"""Tests for admin block assignment import/export routes."""

from datetime import datetime
from types import SimpleNamespace
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.core.security import create_access_token
from app.models.user import User
from app.schemas.block_assignment_import import (
    BlockAssignmentImportResult,
    BlockAssignmentPreviewResponse,
    ImportFormat,
)


@pytest.fixture
def direct_auth_headers(admin_user: User) -> dict[str, str]:
    """Create auth headers without hitting the rate-limited login endpoint."""
    token = create_access_token(
        data={"sub": str(admin_user.id), "username": admin_user.username}
    )
    return {"Authorization": f"Bearer {token}"}


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


def test_execute_import_returns_created_status(
    client: TestClient, direct_auth_headers: dict[str, str]
) -> None:
    result = BlockAssignmentImportResult(
        success=True,
        academic_year=2025,
        total_rows=2,
        imported_count=1,
        updated_count=0,
        skipped_count=1,
        failed_count=0,
        failed_rows=[],
        error_messages=[],
        started_at=datetime(2025, 1, 1, 0, 0, 0),
        completed_at=datetime(2025, 1, 1, 0, 0, 1),
    )

    mock_service = MagicMock()
    mock_service.execute_import = AsyncMock(return_value=result)

    with patch(
        "app.api.routes.admin_block_assignments.get_block_assignment_import_service",
        return_value=mock_service,
    ):
        response = client.post(
            "/api/v1/admin/block-assignments/import",
            headers=direct_auth_headers,
            json={
                "preview_id": "preview-123",
                "academic_year": 2025,
                "skip_duplicates": True,
                "update_duplicates": False,
                "import_unmatched": False,
                "row_overrides": {},
            },
        )

    assert response.status_code == 201
    payload = response.json()
    assert payload["imported_count"] == 1
    assert payload["skipped_count"] == 1


def test_quick_create_template_returns_created_status(
    client: TestClient, direct_auth_headers: dict[str, str]
) -> None:
    template_id = uuid4()
    mock_template = SimpleNamespace(
        id=template_id,
        abbreviation="FMIT",
        name="Family Medicine Inpatient",
        rotation_type="inpatient",
    )

    mock_service = MagicMock()
    mock_service.create_quick_template = AsyncMock(return_value=mock_template)

    with patch(
        "app.api.routes.admin_block_assignments.get_block_assignment_import_service",
        return_value=mock_service,
    ):
        response = client.post(
            "/api/v1/admin/block-assignments/templates/quick-create",
            headers=direct_auth_headers,
            json={
                "abbreviation": "FMIT",
                "name": "Family Medicine Inpatient",
                "rotation_type": "inpatient",
                "leave_eligible": True,
            },
        )

    assert response.status_code == 201
    payload = response.json()
    assert payload["id"] == str(template_id)
    assert payload["abbreviation"] == "FMIT"
    assert payload["rotation_type"] == "inpatient"


def test_import_block_sheet_returns_created_status(
    client: TestClient, direct_auth_headers: dict[str, str]
) -> None:
    preview = SimpleNamespace(preview_id="preview-001", academic_year=2025)
    import_result = SimpleNamespace(
        imported_count=2,
        skipped_count=0,
        failed_count=1,
        error_messages=["Row 3 failed"],
    )

    mock_service = MagicMock()
    mock_service.load_caches = AsyncMock(return_value=None)
    mock_service.preview_import = AsyncMock(return_value=preview)
    mock_service.execute_import = AsyncMock(return_value=import_result)

    with patch(
        "app.api.routes.admin_block_assignments.get_block_assignment_import_service",
        return_value=mock_service,
    ):
        response = client.post(
            "/api/v1/admin/block-assignments/import-block-sheet",
            headers=direct_auth_headers,
            json={
                "assignments": [
                    {
                        "name": "Smith",
                        "rotation": "FMIT",
                    }
                ],
                "blockNumber": 3,
            },
        )

    assert response.status_code == 201
    payload = response.json()
    assert payload["assignmentsCreated"] == 2
    assert payload["failed"] == 1
    assert payload["errors"] == ["Row 3 failed"]
