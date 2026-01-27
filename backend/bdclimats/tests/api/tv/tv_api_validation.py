import json
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from rest_framework import status

from catalog.models import ComputationRule, Dataset, Indicator

pytestmark = pytest.mark.django_db


def test_create_dataset_normalizes_code(api_client):
    response = api_client.post(
        "/api/datasets/",
        {"code": "  t2m  ", "name": "Test", "source_url": "https://example.com"},
        format="json",
    )
    assert response.status_code == status.HTTP_201_CREATED
    assert response.data["code"] == "T2M"


def test_create_dataset_rejects_empty_code(api_client):
    response = api_client.post(
        "/api/datasets/",
        {"code": "   ", "name": "Test", "source_url": "https://example.com"},
        format="json",
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_create_indicator_allows_empty_unit(api_client):
    dataset = Dataset.objects.create(
        code="D1", name="Test", source_url="https://example.com"
    )
    response = api_client.post(
        "/api/indicators/",
        {"dataset": dataset.id, "code": "RR_SUM", "name": "Rain", "unit": ""},
        format="json",
    )
    assert response.status_code == status.HTTP_201_CREATED


def test_create_indicator_rejects_empty_code(api_client):
    dataset = Dataset.objects.create(
        code="D1", name="Test", source_url="https://example.com"
    )
    response = api_client.post(
        "/api/indicators/",
        {"dataset": dataset.id, "code": "  ", "name": "Rain", "unit": "mm"},
        format="json",
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_create_rule_rejects_non_positive_version(api_client):
    dataset = Dataset.objects.create(
        code="D1", name="Test", source_url="https://example.com"
    )
    indicator = Indicator.objects.create(
        code="T2M", name="Temp", unit="C", dataset=dataset
    )
    response = api_client.post(
        "/api/computation-rules/",
        {
            "indicator": indicator.id,
            "version": 0,
            "operation": "avg",
            "is_active": True,
        },
        format="json",
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_compute_use_dataset_file(api_client, settings, tmp_path):
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
    indicator = Indicator.objects.create(
        code="T2M", name="Temp", unit="C", dataset=dataset
    )
    ComputationRule.objects.create(
        indicator=indicator, version=1, operation="avg", is_active=True
    )

    response = api_client.post(
        f"/api/indicators/{indicator.id}/compute/",
        {"use_dataset": True},
        format="json",
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.data["result"] == 15.0


@patch("api.views.requests.get")
def test_compute_use_dataset_http(mock_get, api_client):
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
    indicator = Indicator.objects.create(
        code="T2M", name="Temp", unit="C", dataset=dataset
    )
    ComputationRule.objects.create(
        indicator=indicator, version=1, operation="avg", is_active=True
    )

    response = api_client.post(
        f"/api/indicators/{indicator.id}/compute/",
        {"use_dataset": True},
        format="json",
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.data["result"] == 10.0
