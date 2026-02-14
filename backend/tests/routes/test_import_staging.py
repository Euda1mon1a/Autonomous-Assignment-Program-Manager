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
