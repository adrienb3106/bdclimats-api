from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator
from catalog.models import Indicator, Dataset

class IndicatorSerializer(serializers.ModelSerializer):
    """
    Serializer explicite pour l'API CRUD d'Indicator.
    - dataset est représenté par son ID (clé étrangère).
    - id est read-only.
    - code est normalisé (strip + upper).
    - unicité (dataset, code) validée côté API.
    """
    class Meta:
        model = Indicator
        fields = ["id", "dataset", "code", "name", "unit"]
        read_only_fields = ["id"]
        validators = [
            UniqueTogetherValidator(
                queryset=Indicator.objects.all(),
                fields=["dataset", "code"],
                message="Ce code existe déjà pour ce dataset.",
            )
        ]

    def validate_code(self, value: str) -> str:
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
            return value
        return value.strip()

class DatasetSerializer(serializers.ModelSerializer):
    """
    Serializer explicite pour l'API CRUD de Dataset.
    - dataset est représenté par son ID (clé étrangère).
    - id est read-only.
    - code est normalisé (strip + upper).
    - unicité (dataset, code) validée côté API.
    """
    class Meta:
        model = Dataset
        fields = ["id", "code", "name", "source_url", "created_at"]
        read_only_fields = ["id", "created_at"]
    
    def validate_code(self, value: str) -> str:
        value = value.strip().upper()
        if not value:
            raise serializers.ValidationError("Le code ne peut pas etre vide.")
        return value

    def validate_name(self, value: str) -> str:
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Le nom ne peut pas etre vide.")
        return value