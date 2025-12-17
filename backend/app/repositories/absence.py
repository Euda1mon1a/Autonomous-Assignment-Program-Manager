"""Absence repository for database operations."""

from datetime import date
from uuid import UUID

from sqlalchemy.orm import Session, joinedload

from app.models.absence import Absence
from app.repositories.base import BaseRepository


class AbsenceRepository(BaseRepository[Absence]):
    """Repository for Absence entity operations."""

    def __init__(self, db: Session):
        super().__init__(Absence, db)

    def get_by_id_with_person(self, id: UUID) -> Absence | None:
        """Get absence with related person loaded."""
        return (
            self.db.query(Absence)
            .options(joinedload(Absence.person))
            .filter(Absence.id == id)
            .first()
        )

    def list_with_filters(
        self,
        start_date: date | None = None,
        end_date: date | None = None,
        person_id: UUID | None = None,
        absence_type: str | None = None,
    ) -> list[Absence]:
        """List absences with optional filters and eager loading."""
        query = self.db.query(Absence).options(joinedload(Absence.person))

        if start_date:
            query = query.filter(Absence.end_date >= start_date)
        if end_date:
            query = query.filter(Absence.start_date <= end_date)
        if person_id:
            query = query.filter(Absence.person_id == person_id)
        if absence_type:
            query = query.filter(Absence.absence_type == absence_type)

        return query.order_by(Absence.start_date).all()

    def get_person_ids_absent_on_date(self, on_date: date) -> list[UUID]:
        """Get all person IDs who have an absence on a specific date."""
        results = (
            self.db.query(Absence.person_id)
            .filter(
                Absence.start_date <= on_date,
                Absence.end_date >= on_date,
            )
            .all()
        )
        return [r[0] for r in results]

    def get_by_person_and_date_range(
        self, person_id: UUID, start_date: date, end_date: date
    ) -> list[Absence]:
        """Get absences for a person that overlap with a date range."""
        return (
            self.db.query(Absence)
            .filter(
                Absence.person_id == person_id,
                Absence.start_date <= end_date,
                Absence.end_date >= start_date,
            )
            .order_by(Absence.start_date)
            .all()
        )

    def has_absence_on_date(self, person_id: UUID, on_date: date) -> bool:
        """Check if a person has an absence on a specific date."""
        return (
            self.db.query(Absence)
            .filter(
                Absence.person_id == person_id,
                Absence.start_date <= on_date,
                Absence.end_date >= on_date,
            )
            .first()
            is not None
        )
