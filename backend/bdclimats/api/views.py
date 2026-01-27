import json
from pathlib import Path
from urllib.parse import urlparse

import requests
from django.conf import settings
from django.utils.dateparse import parse_datetime
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from api.compute_serializers import ComputeRequestSerializer
from api.serializers import (
    ComputationRuleSerializer,
    DatasetSerializer,
    IndicatorSerializer,
)
from api.services.compute import ComputeError, compute
from catalog.models import ComputationRule, Dataset, Indicator


def _load_payload_from_source(source_url: str, debug: bool):
    parsed = urlparse(source_url)

    # 1) Source locale (file://) autorisée uniquement en DEBUG.
    if parsed.scheme == "file":
        if not debug:
            return None, Response(
                {"detail": "file:// interdit hors DEBUG."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Lecture du fichier JSON local (format: {"values": [...] }).
        file_path = Path(parsed.path)
        if (
            file_path.drive == ""
            and parsed.path.startswith("/")
            and len(parsed.path) >= 3
            and parsed.path[2] == ":"
        ):
            file_path = Path(parsed.path[1:])

        try:
            raw = file_path.read_text(encoding="utf-8")
            return json.loads(raw), None
        except FileNotFoundError:
            return None, Response(
                {"detail": f"Fichier introuvable: {file_path}"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except json.JSONDecodeError:
            return None, Response(
                {"detail": "JSON invalide dans le fichier dataset."},
                status=status.HTTP_400_BAD_REQUEST,
            )

    # 2) Source distante (http/https)
    if parsed.scheme in ("http", "https"):
        try:
            resp = requests.get(source_url, timeout=3)
            resp.raise_for_status()
            content_type = resp.headers.get("Content-Type", "")
            if "application/json" not in content_type:
                return None, Response(
                    {"detail": "source_url doit renvoyer du JSON (application/json)."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            return resp.json(), None
        except requests.RequestException:
            return None, Response(
                {"detail": "Erreur HTTP sur source_url."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except ValueError:
            return None, Response(
                {"detail": "JSON invalide depuis source_url."},
                status=status.HTTP_400_BAD_REQUEST,
            )

    # 3) Schéma non supporté.
    return None, Response(
        {"detail": f"scheme {parsed.scheme} non supporté"},
        status=status.HTTP_400_BAD_REQUEST,
    )


def _extract_values_from_payload(payload):
    # Validation stricte du format attendu: {"values": [...]}
    points = payload.get("values")
    if not isinstance(points, list) or len(points) == 0:
        return None, Response(
            {
                "detail": "Le JSON dataset doit contenir une clé 'values' (liste non vide)."
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    for point in points:
        if not isinstance(point, dict):
            return None, Response(
                {"detail": "Chaque point doit être un objet {timestamp, value}."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        ts = point.get("timestamp")
        if not ts or parse_datetime(str(ts)) is None:
            return None, Response(
                {"detail": "timestamp doit être en ISO 8601."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        value = point.get("value")
        if (value is not None) and (not isinstance(value, (int, float))):
            return None, Response(
                {"detail": "value doit être un nombre (ou null si dropna=true)."},
                status=status.HTTP_400_BAD_REQUEST,
            )

    return [point.get("value") for point in points], None


class IndicatorViewSet(viewsets.ModelViewSet):
    # CRUD complet pour Indicator.
    queryset = Indicator.objects.all().order_by("code")
    serializer_class = IndicatorSerializer

    @action(detail=True, methods=["post"], url_path="compute")
    def compute(self, request, pk=None):
        # 1) Valider le payload d'entrée
        req_ser = ComputeRequestSerializer(data=request.data)
        req_ser.is_valid(raise_exception=True)
        rule_version = req_ser.validated_data.get("rule_version")

        # 2) Récupérer l'indicator
        indicator = self.get_object()

        # use_dataset (payload) : True => lire dataset.source_url, False => utiliser values du body.
        use_dataset = req_ser.validated_data.get("use_dataset", False)
        # Mode dataset: lit les valeurs depuis dataset.source_url (file:// en dev, http/https en prod).
        if use_dataset:
            dataset = indicator.dataset
            if dataset is None or not dataset.source_url:
                return Response(
                    {"detail": "Aucun dataset associé à cet indicateur."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            payload, error = _load_payload_from_source(
                dataset.source_url, settings.DEBUG
            )
            if error:
                return error
            values, error = _extract_values_from_payload(payload)
            if error:
                return error
        else:
            points = req_ser.validated_data["values"]
            values = [point.get("value") for point in points]

        # 3) Choisir la rule
        if rule_version is not None:
            rule = ComputationRule.objects.filter(
                indicator=indicator, version=rule_version
            ).first()
            if rule is None:
                return Response(
                    {
                        "detail": f"Aucune rule version={rule_version} pour cet indicateur."
                    },
                    status=status.HTTP_404_NOT_FOUND,
                )
        else:
            rule = (
                ComputationRule.objects.filter(indicator=indicator, is_active=True)
                .order_by("-version")
                .first()
            )
            if rule is None:
                return Response(
                    {"detail": "Aucune rule active pour cet indicateur."},
                    status=status.HTTP_404_NOT_FOUND,
                )

        # 4) Appliquer params (dropna/min_count)
        params = rule.params or {}
        dropna = bool(params.get("dropna", True))
        min_count = int(params.get("min_count", 1))

        if dropna:
            cleaned = [v for v in values if v is not None]
        else:
            if any(v is None for v in values):
                return Response(
                    {"detail": "Valeurs nulles présentes mais dropna=false."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            cleaned = values

        if len(cleaned) < min_count:
            return Response(
                {
                    "detail": "Pas assez de valeurs pour calculer.",
                    "min_count": min_count,
                    "used_count": len(cleaned),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # 5) Calcul
        try:
            result = compute(rule.operation, cleaned)
        except ComputeError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        # 6) Réponse
        return Response(
            {
                "indicator": {
                    "id": indicator.id,
                    "code": indicator.code,
                    "unit": indicator.unit,
                },
                "rule": {
                    "version": rule.version,
                    "operation": rule.operation,
                    "params": rule.params,
                },
                "input_count": len(values),
                "used_count": len(cleaned),
                "result": result,
            },
            status=status.HTTP_200_OK,
        )


class DatasetViewSet(viewsets.ModelViewSet):
    # CRUD complet pour Dataset.
    queryset = Dataset.objects.all().order_by("code")
    serializer_class = DatasetSerializer


class ComputationRuleViewSet(viewsets.ModelViewSet):
    # CRUD complet pour ComputationRule.
    queryset = ComputationRule.objects.all().order_by("indicator", "version")
    serializer_class = ComputationRuleSerializer
