from rest_framework import serializers


class PointSerializer(serializers.Serializer):
    timestamp = serializers.DateTimeField()
    value = serializers.FloatField(allow_null=True)


class ComputeRequestSerializer(serializers.Serializer):
    """
    Payload d'entrée pour POST /api/indicators/<id>/compute/

    Exemple:
    {
      "values": [
        {"timestamp": "2026-01-27T10:00:00Z", "value": 12.3},
        {"timestamp": "2026-01-27T11:00:00+01:00", "value": null}
      ],
      "rule_version": 2
    }
    """

    use_dataset = serializers.BooleanField(required=False, default=False)

    values = serializers.ListField(
        child=PointSerializer(),
        allow_empty=False,
        required=False,
        help_text="Liste de points {timestamp, value} (value null autorisé si dropna=true).",
    )

    rule_version = serializers.IntegerField(
        required=False,
        min_value=1,
        help_text="Version de ComputationRule à utiliser (optionnel).",
    )

    def validate(self, attrs):
        # Si on ne calcule pas à partir du dataset, "values" est obligatoire.
        use_dataset = attrs.get("use_dataset", False)
        values = attrs.get("values")
        if not use_dataset:
            if values is None:
                raise serializers.ValidationError({"values": "This field is required."})
            if all(point.get("value") is None for point in values):
                raise serializers.ValidationError(
                    {"values": "Toutes les valeurs sont nulles."}
                )
        return attrs
