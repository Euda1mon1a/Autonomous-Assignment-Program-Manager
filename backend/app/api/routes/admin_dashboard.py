"""Admin dashboard aggregate endpoints."""

from datetime import date, datetime

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.auth.permissions.decorators import require_role
from app.db.session import get_db
from app.models.absence import Absence
from app.models.conflict_alert import ConflictAlert, ConflictAlertStatus
from app.models.person import Person
from app.models.swap import SwapRecord, SwapStatus
from app.models.user import User
from app.schemas.admin_dashboard import (
    AdminAbsenceCounts,
    AdminConflictCounts,
    AdminDashboardSummary,
    AdminPeopleCounts,
    AdminSwapCounts,
    AdminUserCounts,
)

router = APIRouter(prefix="/admin/dashboard", tags=["admin-dashboard"])


@router.get(
    "/summary",
    response_model=AdminDashboardSummary,
    dependencies=[Depends(require_role(["ADMIN", "COORDINATOR"]))],
)
def get_admin_dashboard_summary(db: Session = Depends(get_db)) -> AdminDashboardSummary:
    """Return aggregate counts for admin dashboard widgets."""
    today = date.today()

    # Users
    users_total = db.query(func.count(User.id)).scalar() or 0
    users_active = (
        db.query(func.count(User.id)).filter(User.is_active.is_(True)).scalar() or 0
    )

    # People
    people_total = db.query(func.count(Person.id)).scalar() or 0
    residents_total = (
        db.query(func.count(Person.id))
        .filter(Person.type == "resident")
        .scalar()
        or 0
    )
    faculty_total = (
        db.query(func.count(Person.id)).filter(Person.type == "faculty").scalar() or 0
    )

    # Absences
    absences_active = (
        db.query(func.count(Absence.id))
        .filter(Absence.start_date <= today, Absence.end_date >= today)
        .scalar()
        or 0
    )
    absences_upcoming = (
        db.query(func.count(Absence.id)).filter(Absence.start_date > today).scalar()
        or 0
    )

    # Swaps by status
    swap_counts = {status.value: 0 for status in SwapStatus}
    for status, count in (
        db.query(SwapRecord.status, func.count(SwapRecord.id))
        .group_by(SwapRecord.status)
        .all()
    ):
        key = status.value if hasattr(status, "value") else str(status)
        swap_counts[key] = count

    # Conflicts by status
    conflict_counts = {status.value: 0 for status in ConflictAlertStatus}
    for status, count in (
        db.query(ConflictAlert.status, func.count(ConflictAlert.id))
        .group_by(ConflictAlert.status)
        .all()
    ):
        key = status.value if hasattr(status, "value") else str(status)
        conflict_counts[key] = count

    return AdminDashboardSummary(
        timestamp=datetime.utcnow(),
        users=AdminUserCounts(total=users_total, active=users_active),
        people=AdminPeopleCounts(
            total=people_total, residents=residents_total, faculty=faculty_total
        ),
        absences=AdminAbsenceCounts(
            active=absences_active, upcoming=absences_upcoming
        ),
        swaps=AdminSwapCounts(
            pending=swap_counts[SwapStatus.PENDING.value],
            approved=swap_counts[SwapStatus.APPROVED.value],
            executed=swap_counts[SwapStatus.EXECUTED.value],
            rejected=swap_counts[SwapStatus.REJECTED.value],
            cancelled=swap_counts[SwapStatus.CANCELLED.value],
            rolled_back=swap_counts[SwapStatus.ROLLED_BACK.value],
        ),
        conflicts=AdminConflictCounts(
            new=conflict_counts[ConflictAlertStatus.NEW.value],
            acknowledged=conflict_counts[ConflictAlertStatus.ACKNOWLEDGED.value],
            resolved=conflict_counts[ConflictAlertStatus.RESOLVED.value],
            ignored=conflict_counts[ConflictAlertStatus.IGNORED.value],
        ),
    )
