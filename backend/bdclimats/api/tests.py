from rest_framework import status
from rest_framework.test import APITestCase

from catalog.models import Dataset, Indicator


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
