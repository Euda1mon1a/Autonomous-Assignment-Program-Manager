"""Tests for schedule draft routes."""

from datetime import date, datetime
from uuid import uuid4
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.models.schedule_draft import (
    DraftSourceType,
    ScheduleDraft,
    ScheduleDraftStatus,
)
from app.models.user import User
from app.services.schedule_draft_service import PublishResult


def _login(client: TestClient, username: str, password: str) -> dict:
    response = client.post(
        "/api/auth/login/json",
        json={"username": username, "password": password},
    )
    if response.status_code != 200:
        pytest.skip("Login endpoint not available")
    token = response.json().get("access_token")
    return {"Authorization": f"Bearer {token}"}


def test_create_draft_requires_scheduler_role(client: TestClient, db: Session) -> None:
    user = User(
        id=uuid4(),
        username="faculty_user",
        email="faculty@test.org",
        hashed_password=get_password_hash("testpass123"),
        role="faculty",
        is_active=True,
    )
    db.add(user)
    db.commit()

    headers = _login(client, "faculty_user", "testpass123")

    payload = {
        "source_type": DraftSourceType.MANUAL.value,
        "target_start_date": date.today().isoformat(),
        "target_end_date": date.today().isoformat(),
    }

    response = client.post(
        "/api/v1/schedules/drafts",
        json=payload,
        headers=headers,
    )

    assert response.status_code == 403
    assert "Schedule management access required" in response.json()["detail"]


@patch("app.api.routes.schedule_drafts.ScheduleDraftService")
def test_publish_passes_break_glass_reason(
    mock_service: MagicMock,
    client: TestClient,
    auth_headers: dict,
) -> None:
    draft_id = uuid4()
    mock_service.return_value.publish_draft.return_value = PublishResult(
        success=True,
        draft_id=draft_id,
        status=ScheduleDraftStatus.PUBLISHED,
        published_count=1,
        error_count=0,
        message="ok",
    )

    response = client.post(
        f"/api/v1/schedules/drafts/{draft_id}/publish",
        json={
            "break_glass_reason": "Emergency coverage",
            "validate_acgme": False,
        },
        headers=auth_headers,
    )

    assert response.status_code == 200
    mock_service.return_value.publish_draft.assert_called_once()
    _, kwargs = mock_service.return_value.publish_draft.call_args
    assert kwargs["break_glass_reason"] == "Emergency coverage"
    assert kwargs["validate_acgme"] is False


def test_get_draft_includes_approval_fields(
    client: TestClient,
    auth_headers: dict,
    db: Session,
    admin_user: User,
) -> None:
    approval_date = date(2026, 2, 1)
    approved_at = datetime(2026, 2, 2, 8, 30, 0)

    draft = ScheduleDraft(
        id=uuid4(),
        created_at=datetime.utcnow(),
        created_by_id=admin_user.id,
        target_start_date=date(2026, 2, 1),
        target_end_date=date(2026, 2, 7),
        status=ScheduleDraftStatus.DRAFT,
        source_type=DraftSourceType.MANUAL,
        approved_at=approved_at,
        approved_by_id=admin_user.id,
        approval_reason="Approved for emergency",
        lock_date_at_approval=approval_date,
        flags_total=0,
        flags_acknowledged=0,
    )
    db.add(draft)
    db.commit()

    response = client.get(
        f"/api/v1/schedules/drafts/{draft.id}",
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["approved_by_id"] == str(admin_user.id)
    assert data["approval_reason"] == "Approved for emergency"
    assert data["lock_date_at_approval"] == approval_date.isoformat()
    assert data["approved_at"] is not None


# ---------------------------------------------------------------------------
# Request-validation tests (422 on malformed bodies)
# ---------------------------------------------------------------------------

DUMMY_DRAFT_ID = "00000000-0000-0000-0000-000000000001"
VALID_PERSON_ID = "00000000-0000-0000-0000-000000000001"


# --- POST /api/v1/schedules/drafts (ScheduleDraftCreate) ------------------


@pytest.mark.unit
def test_create_draft_empty_body_returns_422(client: TestClient, auth_headers):
    response = client.post(
        "/api/v1/schedules/drafts",
        json={},
        headers=auth_headers,
    )
    assert response.status_code == 422


@pytest.mark.unit
def test_create_draft_missing_dates_returns_422(client: TestClient, auth_headers):
    response = client.post(
        "/api/v1/schedules/drafts",
        json={"source_type": "manual"},
        headers=auth_headers,
    )
    assert response.status_code == 422


@pytest.mark.unit
def test_create_draft_invalid_source_type_returns_422(client: TestClient, auth_headers):
    response = client.post(
        "/api/v1/schedules/drafts",
        json={
            "source_type": "BOGUS",
            "target_start_date": "2025-01-01",
            "target_end_date": "2025-01-07",
        },
        headers=auth_headers,
    )
    assert response.status_code == 422


@pytest.mark.unit
def test_create_draft_end_before_start_returns_422(client: TestClient, auth_headers):
    response = client.post(
        "/api/v1/schedules/drafts",
        json={
            "source_type": "manual",
            "target_start_date": "2025-01-07",
            "target_end_date": "2025-01-01",
        },
        headers=auth_headers,
    )
    assert response.status_code == 422


@pytest.mark.unit
def test_create_draft_invalid_date_format_returns_422(client: TestClient, auth_headers):
    response = client.post(
        "/api/v1/schedules/drafts",
        json={
            "source_type": "manual",
            "target_start_date": "not-a-date",
            "target_end_date": "2025-01-07",
        },
        headers=auth_headers,
    )
    assert response.status_code == 422


@pytest.mark.unit
def test_create_draft_target_block_out_of_range_returns_422(
    client: TestClient, auth_headers
):
    response = client.post(
        "/api/v1/schedules/drafts",
        json={
            "source_type": "manual",
            "target_start_date": "2025-01-01",
            "target_end_date": "2025-01-07",
            "target_block": 0,
        },
        headers=auth_headers,
    )
    assert response.status_code == 422


@pytest.mark.unit
def test_create_draft_notes_too_long_returns_422(client: TestClient, auth_headers):
    response = client.post(
        "/api/v1/schedules/drafts",
        json={
            "source_type": "manual",
            "target_start_date": "2025-01-01",
            "target_end_date": "2025-01-07",
            "notes": "x" * 2001,
        },
        headers=auth_headers,
    )
    assert response.status_code == 422


# --- POST /api/v1/schedules/drafts/{draft_id}/assignments (DraftAssignmentCreate) ---


@pytest.mark.unit
def test_add_assignment_empty_body_returns_422(client: TestClient, auth_headers):
    response = client.post(
        f"/api/v1/schedules/drafts/{DUMMY_DRAFT_ID}/assignments",
        json={},
        headers=auth_headers,
    )
    assert response.status_code == 422


@pytest.mark.unit
def test_add_assignment_invalid_person_id_returns_422(client: TestClient, auth_headers):
    response = client.post(
        f"/api/v1/schedules/drafts/{DUMMY_DRAFT_ID}/assignments",
        json={"person_id": "not-uuid", "assignment_date": "2025-01-01"},
        headers=auth_headers,
    )
    assert response.status_code == 422


@pytest.mark.unit
def test_add_assignment_missing_date_returns_422(client: TestClient, auth_headers):
    response = client.post(
        f"/api/v1/schedules/drafts/{DUMMY_DRAFT_ID}/assignments",
        json={"person_id": VALID_PERSON_ID},
        headers=auth_headers,
    )
    assert response.status_code == 422


@pytest.mark.unit
def test_add_assignment_invalid_time_of_day_returns_422(
    client: TestClient, auth_headers
):
    response = client.post(
        f"/api/v1/schedules/drafts/{DUMMY_DRAFT_ID}/assignments",
        json={
            "person_id": VALID_PERSON_ID,
            "assignment_date": "2025-01-01",
            "time_of_day": "EVENING",
        },
        headers=auth_headers,
    )
    assert response.status_code == 422


@pytest.mark.unit
def test_add_assignment_invalid_change_type_returns_422(
    client: TestClient, auth_headers
):
    response = client.post(
        f"/api/v1/schedules/drafts/{DUMMY_DRAFT_ID}/assignments",
        json={
            "person_id": VALID_PERSON_ID,
            "assignment_date": "2025-01-01",
            "change_type": "INVALID",
        },
        headers=auth_headers,
    )
    assert response.status_code == 422


# --- POST /api/v1/schedules/drafts/{draft_id}/flags/acknowledge (DraftFlagBulkAcknowledge) ---


@pytest.mark.unit
def test_bulk_acknowledge_empty_body_returns_422(client: TestClient, auth_headers):
    response = client.post(
        f"/api/v1/schedules/drafts/{DUMMY_DRAFT_ID}/flags/acknowledge",
        json={},
        headers=auth_headers,
    )
    assert response.status_code == 422


@pytest.mark.unit
def test_bulk_acknowledge_empty_flag_ids_returns_422(client: TestClient, auth_headers):
    response = client.post(
        f"/api/v1/schedules/drafts/{DUMMY_DRAFT_ID}/flags/acknowledge",
        json={"flag_ids": []},
        headers=auth_headers,
    )
    assert response.status_code == 422


@pytest.mark.unit
def test_bulk_acknowledge_invalid_uuid_in_list_returns_422(
    client: TestClient, auth_headers
):
    response = client.post(
        f"/api/v1/schedules/drafts/{DUMMY_DRAFT_ID}/flags/acknowledge",
        json={"flag_ids": ["not-a-uuid"]},
        headers=auth_headers,
    )
    assert response.status_code == 422


@pytest.mark.unit
def test_bulk_acknowledge_too_many_flags_returns_422(client: TestClient, auth_headers):
    response = client.post(
        f"/api/v1/schedules/drafts/{DUMMY_DRAFT_ID}/flags/acknowledge",
        json={"flag_ids": [str(uuid4()) for _ in range(101)]},
        headers=auth_headers,
    )
    assert response.status_code == 422


@pytest.mark.unit
def test_bulk_acknowledge_resolution_note_too_long_returns_422(
    client: TestClient, auth_headers
):
    response = client.post(
        f"/api/v1/schedules/drafts/{DUMMY_DRAFT_ID}/flags/acknowledge",
        json={
            "flag_ids": [str(uuid4())],
            "resolution_note": "x" * 501,
        },
        headers=auth_headers,
    )
    assert response.status_code == 422


# --- POST /api/v1/schedules/drafts/{draft_id}/publish (PublishRequest) -----


@pytest.mark.unit
def test_publish_override_comment_too_long_returns_422(
    client: TestClient, auth_headers
):
    response = client.post(
        f"/api/v1/schedules/drafts/{DUMMY_DRAFT_ID}/publish",
        json={"override_comment": "x" * 501},
        headers=auth_headers,
    )
    assert response.status_code == 422


@pytest.mark.unit
def test_publish_break_glass_reason_too_long_returns_422(
    client: TestClient, auth_headers
):
    response = client.post(
        f"/api/v1/schedules/drafts/{DUMMY_DRAFT_ID}/publish",
        json={"break_glass_reason": "x" * 501},
        headers=auth_headers,
    )
    assert response.status_code == 422


# --- POST /api/v1/schedules/drafts/{draft_id}/rollback (RollbackRequest) ---


@pytest.mark.unit
def test_rollback_reason_too_long_returns_422(client: TestClient, auth_headers):
    response = client.post(
        f"/api/v1/schedules/drafts/{DUMMY_DRAFT_ID}/rollback",
        json={"reason": "x" * 501},
        headers=auth_headers,
    )
    assert response.status_code == 422
