import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

from rest_framework import status
from rest_framework.test import APITestCase
from django.test import override_settings

from catalog.models import ComputationRule, Dataset, Indicator


class ApiValidationTests(APITestCase):
    @override_settings(DEBUG=True)
    def test_compute_use_dataset_file(self):
        # GOAL: compute using dataset file:// in DEBUG mode.
        # TESTED: file:// source_url is read and used when use_dataset=true.
        # TYPE: API test (compute endpoint, file dataset).
        with tempfile.TemporaryDirectory() as tmpdir:
            data_path = Path(tmpdir) / "sample-values.json"
            payload = {
                "values": [
                    {"timestamp": "2026-01-27T10:00:00Z", "value": 10.0},
                    {"timestamp": "2026-01-27T11:00:00Z", "value": 20.0},
                ]
            }
            data_path.write_text(json.dumps(payload), encoding="utf-8")
            dataset = Dataset.objects.create(
                code="D1",
                name="Test",
                source_url=data_path.absolute().as_uri(),
            )
            indicator = Indicator.objects.create(code="T2M", name="Temp", unit="C", dataset=dataset)
            ComputationRule.objects.create(indicator=indicator, version=1, operation="avg", is_active=True)

            response = self.client.post(
                f"/api/indicators/{indicator.id}/compute/",
                {"use_dataset": True},
                format="json",
            )
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response.data["result"], 15.0)
            self.assertEqual(response.data["input_count"], 2)
            self.assertEqual(response.data["used_count"], 2)

    @patch("api.views.requests.get")
    def test_compute_use_dataset_http(self, mock_get):
        # GOAL: compute using dataset http(s) source.
        # TESTED: http(s) source_url is read and used when use_dataset=true.
        # TYPE: API test (compute endpoint, http dataset).
        mock_resp = Mock()
        mock_resp.raise_for_status.return_value = None
        mock_resp.headers = {"Content-Type": "application/json"}
        mock_resp.json.return_value = {
            "values": [
                {"timestamp": "2026-01-27T10:00:00Z", "value": 5.0},
                {"timestamp": "2026-01-27T11:00:00Z", "value": 15.0},
            ]
        }
        mock_get.return_value = mock_resp

        dataset = Dataset.objects.create(
            code="D1",
            name="Test",
            source_url="https://example.com/data.json",
        )
        indicator = Indicator.objects.create(code="T2M", name="Temp", unit="C", dataset=dataset)
        ComputationRule.objects.create(indicator=indicator, version=1, operation="avg", is_active=True)

        response = self.client.post(
            f"/api/indicators/{indicator.id}/compute/",
            {"use_dataset": True},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["result"], 10.0)
        self.assertEqual(response.data["input_count"], 2)
        self.assertEqual(response.data["used_count"], 2)

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
