import json
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from rest_framework import status
from rest_framework.test import APIClient

from catalog.models import ComputationRule, Dataset, Indicator

pytestmark = pytest.mark.django_db


@pytest.fixture
def api_client():
    return APIClient()


def test_compute_use_dataset_file(api_client, settings, tmp_path):
    # GOAL: compute using dataset file:// in DEBUG mode.
    # TESTED: file:// source_url is read and used when use_dataset=true.
    # TYPE: API test (compute endpoint, file dataset).
    settings.DEBUG = True
    data_path = Path(tmp_path) / "sample-values.json"
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

    response = api_client.post(
        f"/api/indicators/{indicator.id}/compute/",
        {"use_dataset": True},
        format="json",
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.data["result"] == 15.0
    assert response.data["input_count"] == 2
    assert response.data["used_count"] == 2


@patch("api.views.requests.get")
def test_compute_use_dataset_http(mock_get, api_client):
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

    response = api_client.post(
        f"/api/indicators/{indicator.id}/compute/",
        {"use_dataset": True},
        format="json",
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.data["result"] == 10.0
    assert response.data["input_count"] == 2
    assert response.data["used_count"] == 2


def test_create_dataset_normalizes_code(api_client):
    # GOAL: verify API returns normalized codes.
    # TESTED: Dataset.code is trimmed + uppercased by validation.
    # TYPE: API test (serializer validation).
    response = api_client.post(
        "/api/datasets/",
        {"code": "  t2m  ", "name": "Test", "source_url": "https://example.com"},
        format="json",
    )
    assert response.status_code == status.HTTP_201_CREATED
    assert response.data["code"] == "T2M"


def test_create_indicator_requires_unit(api_client):
    # GOAL: prevent indicators without a unit.
    # TESTED: Unit empty string is rejected by serializer validation.
    # TYPE: API test (serializer validation).
    dataset = Dataset.objects.create(code="D1", name="Test", source_url="https://example.com")
    response = api_client.post(
        "/api/indicators/",
        {"dataset": dataset.id, "code": "RR_SUM", "name": "Rain", "unit": ""},
        format="json",
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_create_dataset_rejects_empty_code(api_client):
    # GOAL: reject empty dataset code at API level.
    # TESTED: Dataset.code empty string validation.
    # TYPE: API test (serializer validation).
    response = api_client.post(
        "/api/datasets/",
        {"code": "   ", "name": "Test", "source_url": "https://example.com"},
        format="json",
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_create_indicator_rejects_empty_code(api_client):
    # GOAL: reject empty indicator code at API level.
    # TESTED: Indicator.code empty string validation.
    # TYPE: API test (serializer validation).
    dataset = Dataset.objects.create(code="D1", name="Test", source_url="https://example.com")
    response = api_client.post(
        "/api/indicators/",
        {"dataset": dataset.id, "code": "  ", "name": "Rain", "unit": "mm"},
        format="json",
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_create_rule_rejects_non_positive_version(api_client):
    # GOAL: reject version <= 0 at API level.
    # TESTED: ComputationRule.version validation in serializer.
    # TYPE: API test (serializer validation).
    dataset = Dataset.objects.create(code="D1", name="Test", source_url="https://example.com")
    indicator = Indicator.objects.create(code="T2M", name="Temp", unit="C", dataset=dataset)
    response = api_client.post(
        "/api/computation-rules/",
        {"indicator": indicator.id, "version": 0, "operation": "avg", "is_active": True},
        format="json",
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_rules_ordering(api_client):
    # GOAL: verify ordering of rules in API list.
    # TESTED: order_by indicator then version.
    # TYPE: API test (view/queryset ordering).
    dataset = Dataset.objects.create(code="D1", name="Test", source_url="https://example.com")
    indicator_a = Indicator.objects.create(code="A", name="A", unit="C", dataset=dataset)
    indicator_b = Indicator.objects.create(code="B", name="B", unit="C", dataset=dataset)
    ComputationRule.objects.create(indicator=indicator_b, version=2)
    ComputationRule.objects.create(indicator=indicator_a, version=1)
    ComputationRule.objects.create(indicator=indicator_b, version=1)
    response = api_client.get("/api/computation-rules/", format="json")
    assert response.status_code == status.HTTP_200_OK
    ids = [item["id"] for item in response.data["results"]]
    expected = list(
        ComputationRule.objects.all().order_by("indicator", "version").values_list("id", flat=True)
    )
    assert ids == expected


def test_pagination(api_client):
    # GOAL: ensure pagination is applied.
    # TESTED: API returns paginated structure with results.
    # TYPE: API test (pagination settings).
    for i in range(25):
        Dataset.objects.create(code=f"D{i}", name=f"Test{i}", source_url="https://example.com")
    response = api_client.get("/api/datasets/", format="json")
    assert response.status_code == status.HTTP_200_OK
    assert "results" in response.data
