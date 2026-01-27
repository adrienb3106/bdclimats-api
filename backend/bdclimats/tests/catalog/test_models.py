import pytest
from django.core.exceptions import ValidationError

from catalog.models import ComputationRule, Dataset, Indicator

pytestmark = pytest.mark.django_db


def test_code_normalization_applies():
    # GOAL: ensure model-level normalization is applied.
    # TESTED: Dataset.code and Indicator.code are trimmed + uppercased on full_clean().
    # TYPE: unit test (model validation).
    dataset = Dataset.objects.create(code="  d1  ", name="Test", source_url="https://example.com")
    indicator = Indicator(code="  rr_sum ", name="Rain", unit="mm", dataset=dataset)
    indicator.full_clean()
    assert dataset.code == "D1"
    assert indicator.code == "RR_SUM"


def test_dataset_code_unique():
    # GOAL: prevent duplicate dataset codes.
    # TESTED: Dataset.code uniqueness constraint.
    # TYPE: unit test (model/DB constraint).
    Dataset.objects.create(code="D1", name="One", source_url="https://example.com")
    with pytest.raises(Exception):
        Dataset.objects.create(code="D1", name="Two", source_url="https://example.com")


def test_indicator_code_unique_per_dataset():
    # GOAL: prevent duplicate indicator codes within a dataset.
    # TESTED: (dataset, code) uniqueness constraint.
    # TYPE: unit test (model/DB constraint).
    dataset = Dataset.objects.create(code="D1", name="Test", source_url="https://example.com")
    Indicator.objects.create(code="T2M", name="Temp", unit="C", dataset=dataset)
    with pytest.raises(Exception):
        Indicator.objects.create(code="T2M", name="Temp2", unit="C", dataset=dataset)


def test_indicator_unit_required():
    # GOAL: require unit at model level.
    # TESTED: Indicator.unit cannot be blank.
    # TYPE: unit test (model validation).
    dataset = Dataset.objects.create(code="D1", name="Test", source_url="https://example.com")
    indicator = Indicator(code="T2M", name="Temp", unit="   ", dataset=dataset)
    with pytest.raises(ValidationError):
        indicator.full_clean()


def test_computation_rule_version_positive():
    # GOAL: enforce positive version at model level.
    # TESTED: ComputationRule.version > 0.
    # TYPE: unit test (model validation).
    dataset = Dataset.objects.create(code="D1", name="Test", source_url="https://example.com")
    indicator = Indicator.objects.create(code="T2M", name="Temp", unit="C", dataset=dataset)
    rule = ComputationRule(indicator=indicator, version=0)
    with pytest.raises(ValidationError):
        rule.full_clean()


def test_computation_rule_unique_version_per_indicator():
    # GOAL: prevent duplicate rule versions per indicator.
    # TESTED: (indicator, version) uniqueness constraint.
    # TYPE: unit test (model/DB constraint).
    dataset = Dataset.objects.create(code="D1", name="Test", source_url="https://example.com")
    indicator = Indicator.objects.create(code="T2M", name="Temp", unit="C", dataset=dataset)
    ComputationRule.objects.create(indicator=indicator, version=1)
    with pytest.raises(Exception):
        ComputationRule.objects.create(indicator=indicator, version=1)
