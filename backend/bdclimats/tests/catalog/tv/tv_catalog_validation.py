import pytest
from django.core.exceptions import ValidationError

from catalog.models import ComputationRule, Dataset, Indicator

pytestmark = pytest.mark.django_db


def test_catalog_models_valid_path():
    dataset = Dataset.objects.create(code="D1", name="Test", source_url="https://example.com")
    indicator = Indicator.objects.create(code="T2M", name="Temp", unit="C", dataset=dataset)
    rule = ComputationRule(indicator=indicator, version=1, operation="avg", is_active=True)
    dataset.full_clean()
    indicator.full_clean()
    rule.full_clean()


def test_dataset_clean_rejects_empty_code():
    dataset = Dataset(code="   ", name="Test", source_url="https://example.com")
    with pytest.raises(ValidationError):
        dataset.full_clean()


def test_indicator_clean_rejects_empty_code():
    dataset = Dataset.objects.create(code="D1", name="Test", source_url="https://example.com")
    indicator = Indicator(code="   ", name="Rain", unit="mm", dataset=dataset)
    with pytest.raises(ValidationError):
        indicator.full_clean()


def test_indicator_clean_allows_empty_unit():
    dataset = Dataset.objects.create(code="D1", name="Test", source_url="https://example.com")
    indicator = Indicator(code="T2M", name="Temp", unit="   ", dataset=dataset)
    indicator.full_clean()


def test_computation_rule_clean_rejects_non_positive_version():
    dataset = Dataset.objects.create(code="D1", name="Test", source_url="https://example.com")
    indicator = Indicator.objects.create(code="T2M", name="Temp", unit="C", dataset=dataset)
    rule = ComputationRule(indicator=indicator, version=0)
    with pytest.raises(ValidationError):
        rule.full_clean()
