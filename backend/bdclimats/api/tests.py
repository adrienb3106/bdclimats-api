from rest_framework import status
from rest_framework.test import APITestCase

from catalog.models import ComputationRule, Dataset, Indicator


class ApiValidationTests(APITestCase):
    def test_create_dataset_normalizes_code(self):
        # GOAL: verify API returns normalized codes.
        # TESTED: Dataset.code is trimmed + uppercased by validation.
        # TYPE: API test (serializer validation).
        response = self.client.post(
            "/api/datasets/",
            {"code": "  t2m  ", "name": "Test", "source_url": "https://example.com"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["code"], "T2M")

    def test_create_indicator_requires_unit(self):
        # GOAL: prevent indicators without a unit.
        # TESTED: Unit empty string is rejected by serializer validation.
        # TYPE: API test (serializer validation).
        dataset = Dataset.objects.create(code="D1", name="Test", source_url="https://example.com")
        response = self.client.post(
            "/api/indicators/",
            {"dataset": dataset.id, "code": "RR_SUM", "name": "Rain", "unit": ""},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_dataset_rejects_empty_code(self):
        # GOAL: reject empty dataset code at API level.
        # TESTED: Dataset.code empty string validation.
        # TYPE: API test (serializer validation).
        response = self.client.post(
            "/api/datasets/",
            {"code": "   ", "name": "Test", "source_url": "https://example.com"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_indicator_rejects_empty_code(self):
        # GOAL: reject empty indicator code at API level.
        # TESTED: Indicator.code empty string validation.
        # TYPE: API test (serializer validation).
        dataset = Dataset.objects.create(code="D1", name="Test", source_url="https://example.com")
        response = self.client.post(
            "/api/indicators/",
            {"dataset": dataset.id, "code": "  ", "name": "Rain", "unit": "mm"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_rule_rejects_non_positive_version(self):
        # GOAL: reject version <= 0 at API level.
        # TESTED: ComputationRule.version validation in serializer.
        # TYPE: API test (serializer validation).
        dataset = Dataset.objects.create(code="D1", name="Test", source_url="https://example.com")
        indicator = Indicator.objects.create(code="T2M", name="Temp", unit="C", dataset=dataset)
        response = self.client.post(
            "/api/computation-rules/",
            {"indicator": indicator.id, "version": 0, "operation": "avg", "is_active": True},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_rules_ordering(self):
        # GOAL: verify ordering of rules in API list.
        # TESTED: order_by indicator then version.
        # TYPE: API test (view/queryset ordering).
        dataset = Dataset.objects.create(code="D1", name="Test", source_url="https://example.com")
        indicator_a = Indicator.objects.create(code="A", name="A", unit="C", dataset=dataset)
        indicator_b = Indicator.objects.create(code="B", name="B", unit="C", dataset=dataset)
        ComputationRule.objects.create(indicator=indicator_b, version=2)
        ComputationRule.objects.create(indicator=indicator_a, version=1)
        ComputationRule.objects.create(indicator=indicator_b, version=1)
        response = self.client.get("/api/computation-rules/", format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = [item["id"] for item in response.data["results"]]
        expected = list(
            ComputationRule.objects.all().order_by("indicator", "version").values_list("id", flat=True)
        )
        self.assertEqual(ids, expected)

    def test_pagination(self):
        # GOAL: ensure pagination is applied.
        # TESTED: API returns paginated structure with results.
        # TYPE: API test (pagination settings).
        for i in range(25):
            Dataset.objects.create(code=f"D{i}", name=f"Test{i}", source_url="https://example.com")
        response = self.client.get("/api/datasets/", format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("results", response.data)
