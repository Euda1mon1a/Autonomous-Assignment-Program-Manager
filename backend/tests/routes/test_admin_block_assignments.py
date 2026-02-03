"""Tests for admin block assignment import/export routes."""

from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient

from app.schemas.block_assignment_import import (
    BlockAssignmentPreviewResponse,
    ImportFormat,
)


def test_preview_requires_content(client: TestClient, auth_headers: dict) -> None:
    response = client.post(
        "/api/v1/admin/block-assignments/preview",
        headers=auth_headers,
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Either csv_content or file must be provided"


def test_preview_accepts_csv_content(client: TestClient, auth_headers: dict) -> None:
    preview_response = BlockAssignmentPreviewResponse(
        preview_id="preview-123",
        academic_year=2025,
        format_detected=ImportFormat.CSV,
        total_rows=1,
        matched_count=1,
    )

    mock_service = MagicMock()
    mock_service.preview_import = AsyncMock(return_value=preview_response)

    with patch(
        "app.api.routes.admin_block_assignments.get_block_assignment_import_service",
        return_value=mock_service,
    ):
        response = client.post(
            "/api/v1/admin/block-assignments/preview",
            headers=auth_headers,
            data={
                "csv_content": "block_number,rotation_abbrev,resident_name\n1,FMIT,Smith"
            },
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["preview_id"] == "preview-123"
    assert payload["total_rows"] == 1


def test_export_block_assignments_streams_file(
    client: TestClient, auth_headers: dict
) -> None:
    mock_service = MagicMock()
    mock_service.export = AsyncMock(
        return_value=(b"export-data", "export.csv", "text/csv")
    )

    with patch(
        "app.api.routes.admin_block_assignments.get_block_assignment_export_service",
        return_value=mock_service,
    ):
        response = client.post(
            "/api/v1/admin/block-assignments/export",
            headers=auth_headers,
            json={"academic_year": 2025, "format": "csv"},
        )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert "export.csv" in response.headers["content-disposition"]
    assert response.content == b"export-data"


def test_parse_block_sheet_rejects_non_excel(
    client: TestClient, auth_headers: dict
) -> None:
    response = client.post(
        "/api/v1/admin/block-assignments/parse-block-sheet",
        headers=auth_headers,
        files={"file": ("bad.txt", b"not-xlsx", "text/plain")},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "File must be an Excel file (.xlsx or .xls)"
