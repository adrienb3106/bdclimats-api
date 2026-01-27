
from api.compute_serializers import ComputeRequestSerializer


def test_compute_serializer_requires_values_when_not_using_dataset():
    ser = ComputeRequestSerializer(data={"use_dataset": False})
    assert not ser.is_valid()
    assert "values" in ser.errors


def test_compute_serializer_rejects_all_null_values():
    ser = ComputeRequestSerializer(
        data={
            "values": [
                {"timestamp": "2026-01-27T10:00:00Z", "value": None},
                {"timestamp": "2026-01-27T11:00:00Z", "value": None},
            ]
        }
    )
    assert not ser.is_valid()
    assert "values" in ser.errors


def test_compute_serializer_allows_missing_values_with_use_dataset():
    ser = ComputeRequestSerializer(data={"use_dataset": True})
    assert ser.is_valid()
