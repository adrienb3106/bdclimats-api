from django.core.exceptions import ValidationError
from django.test import TestCase

from catalog.models import ComputationRule, Dataset, Indicator


class CatalogModelTests(TestCase):
    def test_code_normalization_applies(self):
        # GOAL: ensure model-level normalization is applied.
        # TESTED: Dataset.code and Indicator.code are trimmed + uppercased on full_clean().
        # TYPE: unit test (model validation).
        dataset = Dataset.objects.create(code="  d1  ", name="Test", source_url="https://example.com")
        indicator = Indicator(code="  rr_sum ", name="Rain", unit="mm", dataset=dataset)
        indicator.full_clean()
        self.assertEqual(dataset.code, "D1")
        self.assertEqual(indicator.code, "RR_SUM")

    def test_dataset_code_unique(self):
        # GOAL: prevent duplicate dataset codes.
        # TESTED: Dataset.code uniqueness constraint.
        # TYPE: unit test (model/DB constraint).
        Dataset.objects.create(code="D1", name="One", source_url="https://example.com")
        with self.assertRaises(Exception):
            Dataset.objects.create(code="D1", name="Two", source_url="https://example.com")

    def test_indicator_code_unique_per_dataset(self):
        # GOAL: prevent duplicate indicator codes within a dataset.
        # TESTED: (dataset, code) uniqueness constraint.
        # TYPE: unit test (model/DB constraint).
        dataset = Dataset.objects.create(code="D1", name="Test", source_url="https://example.com")
        Indicator.objects.create(code="T2M", name="Temp", unit="C", dataset=dataset)
        with self.assertRaises(Exception):
            Indicator.objects.create(code="T2M", name="Temp2", unit="C", dataset=dataset)

    def test_indicator_unit_required(self):
        # GOAL: require unit at model level.
        # TESTED: Indicator.unit cannot be blank.
        # TYPE: unit test (model validation).
        dataset = Dataset.objects.create(code="D1", name="Test", source_url="https://example.com")
        indicator = Indicator(code="T2M", name="Temp", unit="   ", dataset=dataset)
        with self.assertRaises(ValidationError):
            indicator.full_clean()

    def test_computation_rule_version_positive(self):
        # GOAL: enforce positive version at model level.
        # TESTED: ComputationRule.version > 0.
        # TYPE: unit test (model validation).
        dataset = Dataset.objects.create(code="D1", name="Test", source_url="https://example.com")
        indicator = Indicator.objects.create(code="T2M", name="Temp", unit="C", dataset=dataset)
        rule = ComputationRule(indicator=indicator, version=0)
        with self.assertRaises(ValidationError):
            rule.full_clean()

    def test_computation_rule_unique_version_per_indicator(self):
        # GOAL: prevent duplicate rule versions per indicator.
        # TESTED: (indicator, version) uniqueness constraint.
        # TYPE: unit test (model/DB constraint).
        dataset = Dataset.objects.create(code="D1", name="Test", source_url="https://example.com")
        indicator = Indicator.objects.create(code="T2M", name="Temp", unit="C", dataset=dataset)
        ComputationRule.objects.create(indicator=indicator, version=1)
        with self.assertRaises(Exception):
            ComputationRule.objects.create(indicator=indicator, version=1)
