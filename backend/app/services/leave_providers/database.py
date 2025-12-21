"""Database-backed leave provider."""
from datetime import date, timedelta

from sqlalchemy.orm import Session, joinedload

from app.services.leave_providers.base import LeaveProvider, LeaveRecord


class DatabaseLeaveProvider(LeaveProvider):
    """Leave provider that reads from the application database."""

    def __init__(self, db: Session, cache_ttl_seconds: int = 300):
        self.db = db
        self.cache_ttl = cache_ttl_seconds
        self._cache: list[LeaveRecord] | None = None

    def get_conflicts(self, faculty_name: str | None = None, start_date: date | None = None, end_date: date | None = None) -> list[LeaveRecord]:
        records = self.get_all_leave(start_date, end_date)
        if faculty_name:
            records = [r for r in records if r.faculty_name == faculty_name]
        return [r for r in records if r.is_blocking]

    def sync(self) -> int:
        self._cache = None
        return len(self.get_all_leave())

    def get_all_leave(self, start_date: date | None = None, end_date: date | None = None) -> list[LeaveRecord]:
        from app.models.absence import Absence
        from app.models.person import Person

        if start_date is None:
            start_date = date.today()
        if end_date is None:
            end_date = date.today() + timedelta(days=365)

        # OPTIMIZATION: Use joinedload to eagerly load the person relationship
        # This prevents N+1 queries when accessing a.person.name in the list comprehension
        absences = (
            self.db.query(Absence)
            .join(Person)
            .options(joinedload(Absence.person))
            .filter(
                Absence.end_date >= start_date,
                Absence.start_date <= end_date
            )
            .all()
        )

        return [LeaveRecord(
            faculty_name=a.person.name,
            faculty_id=str(a.person_id),
            start_date=a.start_date,
            end_date=a.end_date,
            leave_type=a.absence_type,
            description=a.notes,
            is_blocking=a.should_block_assignment,
        ) for a in absences]
