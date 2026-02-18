"""Tests for import staging endpoints."""

from fastapi.testclient import TestClient


def test_stage_import_invalid_extension_returns_error_detail(
    client: TestClient, auth_headers
):
    response = client.post(
        "/api/v1/import/stage",
        headers=auth_headers,
        files={"file": ("bad.txt", b"not an excel file", "text/plain")},
    )

    assert response.status_code == 400
    detail = response.json()["detail"]
    assert detail["error_code"] == "INVALID_EXTENSION"
    assert "error" in detail
    assert "success" not in detail


def test_list_batches_invalid_status_returns_string_detail(
    client: TestClient, auth_headers
):
    response = client.get(
        "/api/v1/import/batches",
        headers=auth_headers,
        params={"status": "not-a-status"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid status: not-a-status"
