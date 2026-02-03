"""Tests for admin dashboard summary endpoint."""

from datetime import date, timedelta
from uuid import uuid4

from fastapi.testclient import TestClient

from app.core.security import get_password_hash
from app.models.absence import Absence
from app.models.conflict_alert import (
    ConflictAlert,
    ConflictAlertStatus,
    ConflictSeverity,
    ConflictType,
)
from app.models.person import Person
from app.models.swap import SwapRecord, SwapStatus, SwapType
from app.models.user import User


def test_admin_dashboard_summary(client: TestClient, auth_headers, db):
    today = date.today()

    resident = Person(
        id=uuid4(),
        name="Resident One",
        type="resident",
        email="resident.one@example.org",
        pgy_level=1,
    )
    faculty = Person(
        id=uuid4(),
        name="Faculty One",
        type="faculty",
        email="faculty.one@example.org",
        faculty_role="core",
    )
    db.add_all([resident, faculty])

    inactive_user = User(
        id=uuid4(),
        username="inactive_user",
        email="inactive@example.org",
        hashed_password=get_password_hash("inactivepass123"),
        role="resident",
        is_active=False,
    )
    db.add(inactive_user)

    db.add(
        Absence(
            id=uuid4(),
            person_id=resident.id,
            start_date=today - timedelta(days=1),
            end_date=today + timedelta(days=1),
            absence_type="vacation",
        )
    )
    db.add(
        Absence(
            id=uuid4(),
            person_id=resident.id,
            start_date=today + timedelta(days=5),
            end_date=today + timedelta(days=7),
            absence_type="vacation",
        )
    )

    db.add(
        SwapRecord(
            id=uuid4(),
            source_faculty_id=faculty.id,
            source_week=today,
            target_faculty_id=faculty.id,
            target_week=today + timedelta(days=7),
            swap_type=SwapType.ONE_TO_ONE,
            status=SwapStatus.PENDING,
        )
    )
    db.add(
        SwapRecord(
            id=uuid4(),
            source_faculty_id=faculty.id,
            source_week=today,
            target_faculty_id=faculty.id,
            target_week=today + timedelta(days=7),
            swap_type=SwapType.ONE_TO_ONE,
            status=SwapStatus.EXECUTED,
        )
    )

    db.add(
        ConflictAlert(
            id=uuid4(),
            faculty_id=faculty.id,
            conflict_type=ConflictType.LEAVE_FMIT_OVERLAP,
            severity=ConflictSeverity.WARNING,
            fmit_week=today,
            status=ConflictAlertStatus.NEW,
            description="Test conflict",
        )
    )
    db.add(
        ConflictAlert(
            id=uuid4(),
            faculty_id=faculty.id,
            conflict_type=ConflictType.LEAVE_FMIT_OVERLAP,
            severity=ConflictSeverity.WARNING,
            fmit_week=today,
            status=ConflictAlertStatus.RESOLVED,
            description="Resolved conflict",
        )
    )

    db.commit()

    response = client.get("/api/v1/admin/dashboard/summary", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()

    assert data["people"]["residents"] == 1
    assert data["people"]["faculty"] == 1
    assert data["absences"]["active"] == 1
    assert data["absences"]["upcoming"] == 1
    assert data["swaps"]["pending"] == 1
    assert data["swaps"]["executed"] == 1
    assert data["conflicts"]["new"] == 1
    assert data["conflicts"]["resolved"] == 1
