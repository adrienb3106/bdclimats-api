from django.test import TestCase

from catalog.models import Dataset, Indicator


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
