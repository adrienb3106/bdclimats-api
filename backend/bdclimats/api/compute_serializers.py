from rest_framework import serializers


class ComputeRequestSerializer(serializers.Serializer):
    """
    Payload d'entrée pour POST /api/indicators/<id>/compute/

    Exemple:
    {
      "values": [12.3, 11.8, null, 13.0],
      "rule_version": 2
    }
    """
    use_dataset = serializers.BooleanField(required=False, default=False)
    
    values = serializers.ListField(
        child=serializers.FloatField(allow_null=True),
        allow_empty=False,
        required=False,
        help_text="Liste de valeurs numériques (null autorisé si dropna=true).",
    )

    rule_version = serializers.IntegerField(
        required=False,
        min_value=1,
        help_text="Version de ComputationRule à utiliser (optionnel).",
    )

    def validate(self, attrs):
        # Si on ne calcule pas ? partir du dataset, "values" est obligatoire.
        use_dataset = attrs.get("use_dataset", False)
        values = attrs.get("values")
        if not use_dataset:
            if values is None:
                raise serializers.ValidationError({"values": "This field is required."})
            if all(v is None for v in values):
                raise serializers.ValidationError({"values": "Toutes les valeurs sont nulles."})
        return attrs
