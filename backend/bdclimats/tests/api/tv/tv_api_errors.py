from unittest.mock import Mock, patch

import pytest
import requests
from rest_framework import status

from catalog.models import ComputationRule, Dataset, Indicator

pytestmark = pytest.mark.django_db


def _make_indicator(
    rule_params=None,
    operation="avg",
    is_active=True,
    version=1,
    source_url="https://example.com/data.json",
):
    dataset = Dataset.objects.create(code="D1", name="Test", source_url=source_url)
    indicator = Indicator.objects.create(
        code="T2M", name="Temp", unit="C", dataset=dataset
    )
    ComputationRule.objects.create(
        indicator=indicator,
        version=version,
        operation=operation,
        is_active=is_active,
        params=rule_params or {},
    )
    return indicator, dataset


def test_compute_rule_version_not_found(api_client):
    indicator, _ = _make_indicator()
    response = api_client.post(
        f"/api/indicators/{indicator.id}/compute/",
        {
            "rule_version": 99,
            "values": [{"timestamp": "2026-01-27T10:00:00Z", "value": 1.0}],
        },
        format="json",
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_compute_rule_version_found(api_client):
    indicator, _ = _make_indicator(version=2, is_active=False)
    response = api_client.post(
        f"/api/indicators/{indicator.id}/compute/",
        {
            "rule_version": 2,
            "values": [{"timestamp": "2026-01-27T10:00:00Z", "value": 1.0}],
        },
        format="json",
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.data["rule"]["version"] == 2


def test_compute_no_active_rule(api_client):
    indicator, _ = _make_indicator(is_active=False)
    response = api_client.post(
        f"/api/indicators/{indicator.id}/compute/",
        {"values": [{"timestamp": "2026-01-27T10:00:00Z", "value": 1.0}]},
        format="json",
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_compute_no_rule_exists(api_client):
    dataset = Dataset.objects.create(
        code="D1", name="Test", source_url="https://example.com"
    )
    indicator = Indicator.objects.create(
        code="T2M", name="Temp", unit="C", dataset=dataset
    )
    response = api_client.post(
        f"/api/indicators/{indicator.id}/compute/",
        {"values": [{"timestamp": "2026-01-27T10:00:00Z", "value": 1.0}]},
        format="json",
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_compute_dropna_false_rejects_nulls(api_client):
    indicator, _ = _make_indicator(rule_params={"dropna": False})
    response = api_client.post(
        f"/api/indicators/{indicator.id}/compute/",
        {
            "values": [
                {"timestamp": "2026-01-27T10:00:00Z", "value": 1.0},
                {"timestamp": "2026-01-27T11:00:00Z", "value": None},
            ]
        },
        format="json",
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_compute_min_count_enforced(api_client):
    indicator, _ = _make_indicator(rule_params={"min_count": 3})
    response = api_client.post(
        f"/api/indicators/{indicator.id}/compute/",
        {
            "values": [
                {"timestamp": "2026-01-27T10:00:00Z", "value": 1.0},
                {"timestamp": "2026-01-27T11:00:00Z", "value": 2.0},
            ]
        },
        format="json",
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_compute_dropna_false_allows_no_nulls(api_client):
    indicator, _ = _make_indicator(rule_params={"dropna": False})
    response = api_client.post(
        f"/api/indicators/{indicator.id}/compute/",
        {
            "values": [
                {"timestamp": "2026-01-27T10:00:00Z", "value": 1.0},
                {"timestamp": "2026-01-27T11:00:00Z", "value": 2.0},
            ]
        },
        format="json",
    )
    assert response.status_code == status.HTTP_200_OK


def test_compute_unknown_operation(api_client):
    indicator, _ = _make_indicator(operation="median")
    response = api_client.post(
        f"/api/indicators/{indicator.id}/compute/",
        {"values": [{"timestamp": "2026-01-27T10:00:00Z", "value": 1.0}]},
        format="json",
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_use_dataset_missing_source_url(api_client):
    dataset = Dataset.objects.create(
        code="D1", name="Test", source_url="https://example.com"
    )
    Dataset.objects.filter(pk=dataset.id).update(source_url="")
    dataset.refresh_from_db()
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
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_use_dataset_unsupported_scheme(api_client):
    indicator, _ = _make_indicator(source_url="ftp://example.com/data.json")
    response = api_client.post(
        f"/api/indicators/{indicator.id}/compute/",
        {"use_dataset": True},
        format="json",
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST


@patch("api.views.requests.get")
def test_use_dataset_http_non_json_content_type(mock_get, api_client):
    indicator, _ = _make_indicator()
    mock_resp = Mock()
    mock_resp.raise_for_status.return_value = None
    mock_resp.headers = {"Content-Type": "text/html"}
    mock_resp.json.return_value = {}
    mock_get.return_value = mock_resp

    response = api_client.post(
        f"/api/indicators/{indicator.id}/compute/",
        {"use_dataset": True},
        format="json",
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST


@patch("api.views.requests.get")
def test_use_dataset_http_request_error(mock_get, api_client):
    indicator, _ = _make_indicator()
    mock_get.side_effect = requests.RequestException("boom")

    response = api_client.post(
        f"/api/indicators/{indicator.id}/compute/",
        {"use_dataset": True},
        format="json",
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST


@patch("api.views.requests.get")
def test_use_dataset_http_invalid_json(mock_get, api_client):
    indicator, _ = _make_indicator()
    mock_resp = Mock()
    mock_resp.raise_for_status.return_value = None
    mock_resp.headers = {"Content-Type": "application/json"}
    mock_resp.json.side_effect = ValueError("bad json")
    mock_get.return_value = mock_resp

    response = api_client.post(
        f"/api/indicators/{indicator.id}/compute/",
        {"use_dataset": True},
        format="json",
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST


@patch("api.views.requests.get")
def test_use_dataset_http_missing_values(mock_get, api_client):
    indicator, _ = _make_indicator()
    mock_resp = Mock()
    mock_resp.raise_for_status.return_value = None
    mock_resp.headers = {"Content-Type": "application/json"}
    mock_resp.json.return_value = {}
    mock_get.return_value = mock_resp

    response = api_client.post(
        f"/api/indicators/{indicator.id}/compute/",
        {"use_dataset": True},
        format="json",
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST


@patch("api.views.requests.get")
def test_use_dataset_http_invalid_point_shape(mock_get, api_client):
    indicator, _ = _make_indicator()
    mock_resp = Mock()
    mock_resp.raise_for_status.return_value = None
    mock_resp.headers = {"Content-Type": "application/json"}
    mock_resp.json.return_value = {"values": ["oops"]}
    mock_get.return_value = mock_resp

    response = api_client.post(
        f"/api/indicators/{indicator.id}/compute/",
        {"use_dataset": True},
        format="json",
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST


@patch("api.views.requests.get")
def test_use_dataset_http_invalid_timestamp(mock_get, api_client):
    indicator, _ = _make_indicator()
    mock_resp = Mock()
    mock_resp.raise_for_status.return_value = None
    mock_resp.headers = {"Content-Type": "application/json"}
    mock_resp.json.return_value = {
        "values": [{"timestamp": "not-a-date", "value": 1.0}]
    }
    mock_get.return_value = mock_resp

    response = api_client.post(
        f"/api/indicators/{indicator.id}/compute/",
        {"use_dataset": True},
        format="json",
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST


@patch("api.views.requests.get")
def test_use_dataset_http_invalid_value_type(mock_get, api_client):
    indicator, _ = _make_indicator()
    mock_resp = Mock()
    mock_resp.raise_for_status.return_value = None
    mock_resp.headers = {"Content-Type": "application/json"}
    mock_resp.json.return_value = {
        "values": [{"timestamp": "2026-01-27T10:00:00Z", "value": "oops"}]
    }
    mock_get.return_value = mock_resp

    response = api_client.post(
        f"/api/indicators/{indicator.id}/compute/",
        {"use_dataset": True},
        format="json",
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_use_dataset_file_disallowed_in_prod(api_client, settings, tmp_path):
    settings.DEBUG = False
    data_path = tmp_path / "data.json"
    data_path.write_text(
        '{"values":[{"timestamp":"2026-01-27T10:00:00Z","value":1.0}]}',
        encoding="utf-8",
    )
    indicator, _ = _make_indicator(source_url=data_path.absolute().as_uri())
    response = api_client.post(
        f"/api/indicators/{indicator.id}/compute/",
        {"use_dataset": True},
        format="json",
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_use_dataset_file_windows_path_branch(
    api_client, settings, tmp_path, monkeypatch
):
    settings.DEBUG = True
    monkeypatch.chdir(tmp_path)
    win_path = tmp_path / "C:" / "tmp"
    win_path.mkdir(parents=True)
    data_path = win_path / "data.json"
    data_path.write_text(
        '{"values":[{"timestamp":"2026-01-27T10:00:00Z","value":1.0}]}',
        encoding="utf-8",
    )
    indicator, _ = _make_indicator(source_url="file:///C:/tmp/data.json")
    response = api_client.post(
        f"/api/indicators/{indicator.id}/compute/",
        {"use_dataset": True},
        format="json",
    )
    assert response.status_code == status.HTTP_200_OK


def test_use_dataset_file_not_found(api_client, settings, tmp_path):
    settings.DEBUG = True
    missing = tmp_path / "missing.json"
    indicator, _ = _make_indicator(source_url=missing.absolute().as_uri())
    response = api_client.post(
        f"/api/indicators/{indicator.id}/compute/",
        {"use_dataset": True},
        format="json",
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_use_dataset_file_invalid_json(api_client, settings, tmp_path):
    settings.DEBUG = True
    bad_path = tmp_path / "bad.json"
    bad_path.write_text("{bad json", encoding="utf-8")
    indicator, _ = _make_indicator(source_url=bad_path.absolute().as_uri())
    response = api_client.post(
        f"/api/indicators/{indicator.id}/compute/",
        {"use_dataset": True},
        format="json",
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
