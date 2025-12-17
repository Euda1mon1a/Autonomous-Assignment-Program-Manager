"""
Conflict auto-detection service.

Detects conflicts between leave records and FMIT schedule assignments,
creating alerts when overlaps are found.
"""
from dataclasses import dataclass
from datetime import date, timedelta
from typing import List, Optional, TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy.orm import Session

if TYPE_CHECKING:
    from app.models.absence import Absence
    from app.models.person import Person


@dataclass
class ConflictInfo:
    """Information about a detected conflict."""
    faculty_id: UUID
    faculty_name: str
    conflict_type: str  # leave_fmit_overlap, back_to_back, excessive_alternating
    fmit_week: date
    leave_id: Optional[UUID] = None
    severity: str = "warning"  # critical, warning, info
    description: str = ""


class ConflictAutoDetector:
    """
    Service for automatically detecting schedule conflicts.

    Monitors leave changes and detects when they overlap with
    FMIT assignments or create scheduling problems.
    """

    def __init__(self, db: Session):
        self.db = db

    def detect_conflicts_for_absence(
        self,
        absence_id: UUID,
    ) -> List[ConflictInfo]:
        """
        Detect conflicts for a specific absence record.

        Args:
            absence_id: ID of the absence to check

        Returns:
            List of ConflictInfo for any detected conflicts
        """
        from app.models.absence import Absence

        absence = self.db.query(Absence).filter(Absence.id == absence_id).first()
        if not absence:
            return []

        conflicts = []

        # Check for FMIT overlap if absence is blocking
        if absence.is_blocking or absence.absence_type == "deployment":
            fmit_conflicts = self._find_fmit_overlaps(
                absence.person_id,
                absence.start_date,
                absence.end_date,
            )
            for fmit_week in fmit_conflicts:
                conflicts.append(ConflictInfo(
                    faculty_id=absence.person_id,
                    faculty_name=absence.person.name if absence.person else "Unknown",
                    conflict_type="leave_fmit_overlap",
                    fmit_week=fmit_week,
                    leave_id=absence_id,
                    severity="critical",
                    description=f"{absence.absence_type} conflicts with FMIT week {fmit_week}",
                ))

        return conflicts

    def detect_all_conflicts(
        self,
        faculty_id: Optional[UUID] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> List[ConflictInfo]:
        """
        Scan for all conflicts in a date range.

        Args:
            faculty_id: Optional filter by faculty
            start_date: Start of scan range (default: today)
            end_date: End of scan range (default: 90 days out)

        Returns:
            List of all detected conflicts
        """
        from app.models.absence import Absence
        from app.models.person import Person

        if start_date is None:
            start_date = date.today()
        if end_date is None:
            end_date = date.today() + timedelta(days=90)

        query = self.db.query(Absence).filter(
            Absence.end_date >= start_date,
            Absence.start_date <= end_date,
        )

        if faculty_id:
            query = query.filter(Absence.person_id == faculty_id)

        conflicts = []
        for absence in query.all():
            conflicts.extend(self.detect_conflicts_for_absence(absence.id))

        return conflicts

    def create_conflict_alerts(
        self,
        conflicts: List[ConflictInfo],
        created_by_id: Optional[UUID] = None,
    ) -> List[UUID]:
        """
        Create ConflictAlert records for detected conflicts.

        Args:
            conflicts: List of conflicts to create alerts for
            created_by_id: User who triggered the scan

        Returns:
            List of created alert IDs
        """
        # TODO: Implement when ConflictAlert model is wired to __init__.py
        # This will create database records for each conflict
        alert_ids = []

        for conflict in conflicts:
            # Placeholder - actual implementation creates ConflictAlert records
            alert_id = uuid4()
            alert_ids.append(alert_id)

        return alert_ids

    def _find_fmit_overlaps(
        self,
        faculty_id: UUID,
        start_date: date,
        end_date: date,
    ) -> List[date]:
        """
        Find FMIT weeks that overlap with a date range.

        Args:
            faculty_id: Faculty to check
            start_date: Start of date range
            end_date: End of date range

        Returns:
            List of FMIT week start dates that overlap
        """
        # This would query the schedule/assignment data to find FMIT weeks
        # For now, return empty list - actual implementation needs schedule source
        # TODO: Query Assignment records where rotation is FMIT type
        return []

    def _check_back_to_back(
        self,
        faculty_id: UUID,
        fmit_weeks: List[date],
    ) -> List[ConflictInfo]:
        """Check for back-to-back FMIT conflicts."""
        from app.services.xlsx_import import has_back_to_back_conflict

        if has_back_to_back_conflict(sorted(fmit_weeks)):
            # Find which weeks are back-to-back
            conflicts = []
            sorted_weeks = sorted(fmit_weeks)
            for i in range(len(sorted_weeks) - 1):
                gap = (sorted_weeks[i+1] - sorted_weeks[i]).days
                if gap <= 14:  # Less than 2 week gap
                    conflicts.append(ConflictInfo(
                        faculty_id=faculty_id,
                        faculty_name="",  # Would be populated from query
                        conflict_type="back_to_back",
                        fmit_week=sorted_weeks[i],
                        severity="warning",
                        description=f"Back-to-back FMIT: {sorted_weeks[i]} and {sorted_weeks[i+1]}",
                    ))
            return conflicts
        return []
