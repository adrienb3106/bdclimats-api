import pytest
from rest_framework import serializers

from api.serializers import ComputationRuleSerializer, DatasetSerializer, IndicatorSerializer
from catalog.models import Dataset, Indicator

pytestmark = pytest.mark.django_db


def test_dataset_serializer_rejects_empty_name():
    ser = DatasetSerializer(data={"code": "D1", "name": "   ", "source_url": "https://example.com"})
    assert not ser.is_valid()
    assert "name" in ser.errors


def test_dataset_serializer_rejects_empty_code():
    ser = DatasetSerializer(data={"code": "   ", "name": "Test", "source_url": "https://example.com"})
    assert not ser.is_valid()
    assert "code" in ser.errors


def test_dataset_validate_code_rejects_empty_string():
    ser = DatasetSerializer()
    with pytest.raises(serializers.ValidationError):
        ser.validate_code("")


def test_dataset_validate_name_rejects_empty_string():
    ser = DatasetSerializer()
    with pytest.raises(serializers.ValidationError):
        ser.validate_name("   ")


def test_indicator_validate_code_rejects_empty_string():
    ser = IndicatorSerializer()
    with pytest.raises(serializers.ValidationError):
        ser.validate_code("")


def test_indicator_validate_name_rejects_empty_string():
    ser = IndicatorSerializer()
    with pytest.raises(serializers.ValidationError):
        ser.validate_name("   ")


def test_computation_rule_params_rejects_unknown_keys():
    dataset = Dataset.objects.create(code="D1", name="Test", source_url="https://example.com")
    indicator = Indicator.objects.create(code="T2M", name="Temp", unit="C", dataset=dataset)
    ser = ComputationRuleSerializer(
        data={"indicator": indicator.id, "version": 1, "operation": "avg", "params": {"foo": 1}}
    )
    assert not ser.is_valid()
    assert "params" in ser.errors


def test_computation_rule_params_rejects_dropna_not_bool():
    dataset = Dataset.objects.create(code="D1", name="Test", source_url="https://example.com")
    indicator = Indicator.objects.create(code="T2M", name="Temp", unit="C", dataset=dataset)
    ser = ComputationRuleSerializer(
        data={"indicator": indicator.id, "version": 1, "operation": "avg", "params": {"dropna": "no"}}
    )
    assert not ser.is_valid()
    assert "params" in ser.errors


def test_computation_rule_params_rejects_min_count_not_int():
    dataset = Dataset.objects.create(code="D1", name="Test", source_url="https://example.com")
    indicator = Indicator.objects.create(code="T2M", name="Temp", unit="C", dataset=dataset)
    ser = ComputationRuleSerializer(
        data={"indicator": indicator.id, "version": 1, "operation": "avg", "params": {"min_count": "2"}}
    )
    assert not ser.is_valid()
    assert "params" in ser.errors


def test_computation_rule_params_rejects_min_count_lt_1():
    dataset = Dataset.objects.create(code="D1", name="Test", source_url="https://example.com")
    indicator = Indicator.objects.create(code="T2M", name="Temp", unit="C", dataset=dataset)
    ser = ComputationRuleSerializer(
        data={"indicator": indicator.id, "version": 1, "operation": "avg", "params": {"min_count": 0}}
    )
    assert not ser.is_valid()
    assert "params" in ser.errors


def test_computation_rule_validate_params_rejects_non_dict():
    ser = ComputationRuleSerializer()
    with pytest.raises(serializers.ValidationError):
        ser.validate_params("oops")


def test_computation_rule_validate_params_allows_none():
    ser = ComputationRuleSerializer()
    assert ser.validate_params(None) == {}


def test_computation_rule_validate_params_allows_dropna_only():
    ser = ComputationRuleSerializer()
    assert ser.validate_params({"dropna": True}) == {"dropna": True}


def test_computation_rule_validate_params_allows_valid_min_count():
    ser = ComputationRuleSerializer()
    assert ser.validate_params({"dropna": True, "min_count": 2}) == {"dropna": True, "min_count": 2}
