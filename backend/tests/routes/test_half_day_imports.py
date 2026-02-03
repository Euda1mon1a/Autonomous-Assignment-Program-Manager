"""Tests for half-day import routes."""

from datetime import datetime
from types import SimpleNamespace
from uuid import uuid4
from unittest.mock import patch

from fastapi.testclient import TestClient


def test_stage_half_day_import_rejects_non_excel(
    client: TestClient, auth_headers: dict
):
    files = {"file": ("schedule.txt", b"not excel", "text/plain")}
    data = {"block_number": "1", "academic_year": "2025"}

    response = client.post(
        "/api/v1/import/half-day/stage",
        files=files,
        data=data,
        headers=auth_headers,
    )

    assert response.status_code == 400


def test_stage_half_day_import_success(client: TestClient, auth_headers: dict):
    batch_id = uuid4()
    batch = SimpleNamespace(id=batch_id, created_at=datetime.utcnow())
    metrics = {"total_slots": 10, "changed_slots": 2, "added": 1, "removed": 1}
    warnings = ["Person not found in database"]

    with patch(
        "app.api.routes.half_day_imports.validate_excel_upload"
    ) as mock_validate:
        with patch(
            "app.api.routes.half_day_imports.HalfDayImportService"
        ) as mock_service:
            mock_validate.return_value = None
            instance = mock_service.return_value
            instance.stage_block_template2.return_value = (batch, metrics, warnings)

            files = {"file": ("schedule.xlsx", b"xlsx", "application/vnd.ms-excel")}
            data = {"block_number": "1", "academic_year": "2025"}

            response = client.post(
                "/api/v1/import/half-day/stage",
                files=files,
                data=data,
                headers=auth_headers,
            )

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["batch_id"] == str(batch_id)
    assert payload["diff_metrics"]["changed_slots"] == 2
    assert payload["warnings"] == warnings


def test_create_half_day_import_draft_failure(client: TestClient, auth_headers: dict):
    batch_id = uuid4()
    failed_ids = [uuid4()]
    result = SimpleNamespace(
        success=False,
        batch_id=batch_id,
        draft_id=None,
        message="Draft creation failed",
        error_code="invalid_diffs",
        total_selected=1,
        added=0,
        modified=0,
        removed=0,
        skipped=0,
        failed=1,
        failed_ids=failed_ids,
    )

    with patch("app.api.routes.half_day_imports.HalfDayImportService") as mock_service:
        instance = mock_service.return_value
        instance.create_draft_from_batch.return_value = result

        response = client.post(
            f"/api/v1/import/half-day/batches/{batch_id}/draft",
            json={"staged_ids": [str(failed_ids[0])]},
            headers=auth_headers,
        )

    assert response.status_code == 400
    detail = response.json()["detail"]
    assert detail["error_code"] == "invalid_diffs"
    assert detail["failed_ids"] == [str(failed_ids[0])]
