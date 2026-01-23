from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator
from catalog.models import Indicator, Dataset, ComputationRule


class IndicatorSerializer(serializers.ModelSerializer):
    """
    Serializer CRUD d Indicator.
    - dataset est represente par son ID.
    - id est en lecture seule.
    - code est normalise (strip + upper).
    - unicite (dataset, code) validee cote API.
    """

    class Meta:
        model = Indicator
        fields = ["id", "dataset", "code", "name", "unit"]
        read_only_fields = ["id"]
        validators = [
            UniqueTogetherValidator(
                queryset=Indicator.objects.all(),
                fields=["dataset", "code"],
                message="Ce code existe deja pour ce dataset.",
            )
        ]

    def validate_code(self, value: str) -> str:
        # Normalisation defensive cote API.
        value = value.strip().upper()
        if not value:
            raise serializers.ValidationError("Le code ne peut pas etre vide.")
        return value

    def validate_name(self, value: str) -> str:
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Le nom ne peut pas etre vide.")
        return value

    def validate_unit(self, value: str) -> str:
        if value is None:
            raise serializers.ValidationError("L unite ne peut pas etre vide.")
        value = value.strip()
        if not value:
            raise serializers.ValidationError("L unite ne peut pas etre vide.")
        return value


class DatasetSerializer(serializers.ModelSerializer):
    """
    Serializer CRUD de Dataset.
    - id est en lecture seule.
    - code est normalise (strip + upper).
    """
    class Meta:
        model = Dataset
        fields = ["id", "code", "name", "source_url", "created_at"]
        read_only_fields = ["id", "created_at"]

    def validate_code(self, value: str) -> str:
        # Normalisation defensive cote API.
        value = value.strip().upper()
        if not value:
            raise serializers.ValidationError("Le code ne peut pas etre vide.")
        return value

    def validate_name(self, value: str) -> str:
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Le nom ne peut pas etre vide.")
        return value


class ComputationRuleSerializer(serializers.ModelSerializer):
    """
    Serializer CRUD de ComputationRule.
    - id est en lecture seule.
    - unicite (indicator, version) validee cote API.
    """

    class Meta:
        model = ComputationRule
        fields = ["id", "indicator", "version", "operation", "is_active", "params"]
        read_only_fields = ["id"]
        validators = [
            UniqueTogetherValidator(
                queryset=ComputationRule.objects.all(),
                fields=["indicator", "version"],
                message="Cette version existe deja pour cet indicateur.",
            )
        ]

    def validate_version(self, value: int) -> int:
        if value <= 0:
            raise serializers.ValidationError("La version doit etre un entier strictement positif.")
        return value
    
    def validate_params(self, value):
        if value is None:
            return {}

        if not isinstance(value, dict):
            raise serializers.ValidationError("params doit être un objet JSON (dictionnaire).")

        allowed_keys = {"dropna", "min_count"}
        unknown = set(value.keys()) - allowed_keys
        if unknown:
            raise serializers.ValidationError(
                {"params": f"Clés non supportées: {sorted(unknown)}"}
            )

        if "dropna" in value and not isinstance(value["dropna"], bool):
            raise serializers.ValidationError({"dropna": "doit être un booléen (true/false)."})

        if "min_count" in value:
            mc = value["min_count"]
            if not isinstance(mc, int):
                raise serializers.ValidationError({"min_count": "doit être un entier."})
            if mc < 1:
                raise serializers.ValidationError({"min_count": "doit être >= 1."})

        return value
