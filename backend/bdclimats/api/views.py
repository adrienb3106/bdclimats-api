from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from catalog.models import Indicator, Dataset, ComputationRule
from api.serializers import IndicatorSerializer, DatasetSerializer, ComputationRuleSerializer
from api.compute_serializers import ComputeRequestSerializer
from api.services.compute import compute, ComputeError

import json
from urllib.parse import urlparse
from pathlib import Path


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

        use_dataset = req_ser.validated_data.get("use_dataset", False)

        if use_dataset:
            dataset = indicator.dataset
            if dataset is None or not dataset.source_url:
                return Response(
                    {"detail": "Aucun dataset associé à cet indicateur."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            parsed = urlparse(dataset.source_url)

            if parsed.scheme != "file":
                return Response(
                    {"detail": "Dataset source_url doit être en file:// pour ce mode."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            file_path = Path(parsed.path)
            if file_path.drive == "" and parsed.path.startswith("/") and len(parsed.path) >= 3 and parsed.path[2] == ":":
                file_path = Path(parsed.path[1:])
            
            try:
                raw = file_path.read_text(encoding="utf-8")
                payload = json.loads(raw)
            except FileNotFoundError:
                return Response({"detail": f"Fichier introuvable: {file_path}"}, status=status.HTTP_400_BAD_REQUEST)
            except json.JSONDecodeError:
                return Response({"detail": "JSON invalide dans le fichier dataset."}, status=status.HTTP_400_BAD_REQUEST)

            values = payload.get("values")
            if not isinstance(values, list) or len(values) == 0:
                return Response({"detail": "Le JSON dataset doit contenir une clé 'values' (liste non vide)."}, status=status.HTTP_400_BAD_REQUEST)
        else:
            values = req_ser.validated_data["values"]
    
        # 3) Choisir la rule
        if rule_version is not None:
            rule = (
                ComputationRule.objects
                .filter(indicator=indicator, version=rule_version)
                .first()
            )
            if rule is None:
                return Response(
                    {"detail": f"Aucune rule version={rule_version} pour cet indicateur."},
                    status=status.HTTP_404_NOT_FOUND,
                )
        else:
            rule = (
                ComputationRule.objects
                .filter(indicator=indicator, is_active=True)
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
