import pytest
from django.core.exceptions import ValidationError

from catalog.models import ComputationRule, Dataset, Indicator

pytestmark = pytest.mark.django_db


def test_dataset_clean_none_code_branch():
    # Unit test: cover "code is not None" branch by calling clean() directly.
    dataset = Dataset(code=None, name="Test", source_url="https://example.com")
    with pytest.raises(ValidationError):
        dataset.clean()


def test_indicator_clean_code_none_fields_branch():
    # Unit test: cover "code is not None" branch by calling clean() directly.
    dataset = Dataset.objects.create(
        code="D1", name="Test", source_url="https://example.com"
    )
    indicator = Indicator(code=None, name="Temp", unit="C", dataset=dataset)
    with pytest.raises(ValidationError):
        indicator.clean()


def test_indicator_clean_unit_none_fields_branch():
    # Unit test: cover "unit is not None" branch by calling clean() directly.
    dataset = Dataset.objects.create(
        code="D1", name="Test", source_url="https://example.com"
    )
    indicator = Indicator(code="T2M", name="Temp", unit=None, dataset=dataset)
    indicator.clean()


def test_indicator_str_branch():
    # Unit test: cover __str__ methods.
    dataset = Dataset.objects.create(
        code="D1", name="Test", source_url="https://example.com"
    )
    indicator = Indicator.objects.create(
        code="T2M", name="Temp", unit="C", dataset=dataset
    )
    rule = ComputationRule.objects.create(indicator=indicator, version=1)
    assert str(dataset) == "Test - D1"
    assert str(indicator) == "Temp - T2M"
    assert str(rule) == "T2M 1"
