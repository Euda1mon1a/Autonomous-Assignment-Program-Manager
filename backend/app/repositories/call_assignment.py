"""Call assignment repository for database operations."""

from datetime import date
from uuid import UUID

from sqlalchemy.orm import Session, joinedload

from app.models.call_assignment import CallAssignment
from app.repositories.base import BaseRepository


class CallAssignmentRepository(BaseRepository[CallAssignment]):
    """Repository for CallAssignment entity operations."""

    def __init__(self, db: Session):
        super().__init__(CallAssignment, db)

    def get_by_id_with_person(self, id: UUID) -> CallAssignment | None:
        """Get call assignment with related person loaded."""
        return (
            self.db.query(CallAssignment)
            .options(joinedload(CallAssignment.person))
            .filter(CallAssignment.id == id)
            .first()
        )

    def list_with_filters(
        self,
        start_date: date | None = None,
        end_date: date | None = None,
        person_id: UUID | None = None,
        call_type: str | None = None,
    ) -> list[CallAssignment]:
        """List call assignments with optional filters and eager loading."""
        query = self.db.query(CallAssignment).options(joinedload(CallAssignment.person))

        if start_date:
            query = query.filter(CallAssignment.date >= start_date)
        if end_date:
            query = query.filter(CallAssignment.date <= end_date)
        if person_id:
            query = query.filter(CallAssignment.person_id == person_id)
        if call_type:
            query = query.filter(CallAssignment.call_type == call_type)

        return query.order_by(CallAssignment.date).all()

    def get_by_person_id(self, person_id: UUID) -> list[CallAssignment]:
        """Get all call assignments for a specific person."""
        return (
            self.db.query(CallAssignment)
            .filter(CallAssignment.person_id == person_id)
            .order_by(CallAssignment.date)
            .all()
        )

    def get_by_date(self, on_date: date) -> list[CallAssignment]:
        """Get all call assignments for a specific date."""
        return (
            self.db.query(CallAssignment)
            .options(joinedload(CallAssignment.person))
            .filter(CallAssignment.date == on_date)
            .all()
        )

    def get_by_person_and_date_range(
        self, person_id: UUID, start_date: date, end_date: date
    ) -> list[CallAssignment]:
        """Get call assignments for a person within a date range."""
        return (
            self.db.query(CallAssignment)
            .filter(
                CallAssignment.person_id == person_id,
                CallAssignment.date >= start_date,
                CallAssignment.date <= end_date,
            )
            .order_by(CallAssignment.date)
            .all()
        )

    def has_call_on_date(
        self, person_id: UUID, on_date: date, call_type: str | None = None
    ) -> bool:
        """Check if a person has a call assignment on a specific date."""
        query = self.db.query(CallAssignment).filter(
            CallAssignment.person_id == person_id,
            CallAssignment.date == on_date,
        )

        if call_type:
            query = query.filter(CallAssignment.call_type == call_type)

        return query.first() is not None
