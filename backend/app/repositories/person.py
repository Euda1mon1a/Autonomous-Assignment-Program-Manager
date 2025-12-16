"""Person repository for database operations."""

from typing import Optional, List
from uuid import UUID
from sqlalchemy.orm import Session

from app.repositories.base import BaseRepository
from app.models.person import Person


class PersonRepository(BaseRepository[Person]):
    """Repository for Person entity operations."""

    def __init__(self, db: Session):
        super().__init__(Person, db)

    def list_with_filters(
        self,
        type: Optional[str] = None,
        pgy_level: Optional[int] = None,
    ) -> List[Person]:
        """List people with optional filters, ordered by name."""
        query = self.db.query(Person)

        if type:
            query = query.filter(Person.type == type)
        if pgy_level is not None:
            query = query.filter(Person.pgy_level == pgy_level)

        return query.order_by(Person.name).all()

    def list_residents(
        self,
        pgy_level: Optional[int] = None,
    ) -> List[Person]:
        """List all residents, optionally filtered by PGY level."""
        query = self.db.query(Person).filter(Person.type == "resident")

        if pgy_level is not None:
            query = query.filter(Person.pgy_level == pgy_level)

        return query.order_by(Person.pgy_level, Person.name).all()

    def list_faculty(
        self,
        specialty: Optional[str] = None,
    ) -> List[Person]:
        """List all faculty, optionally filtered by specialty."""
        query = self.db.query(Person).filter(Person.type == "faculty")

        if specialty:
            query = query.filter(Person.specialties.contains([specialty]))

        return query.order_by(Person.name).all()

    def get_by_type(self, type: str) -> List[Person]:
        """Get all people of a specific type."""
        return (
            self.db.query(Person)
            .filter(Person.type == type)
            .order_by(Person.name)
            .all()
        )

    def get_available_for_block(
        self,
        exclude_person_id: UUID,
        person_type: str,
        assigned_ids: set[UUID],
        absent_ids: set[UUID],
    ) -> List[Person]:
        """
        Get people available for assignment.

        Excludes:
        - The person being replaced
        - People already assigned to the block
        - People with absences
        """
        query = self.db.query(Person).filter(
            Person.type == person_type,
            Person.id != exclude_person_id,
        )

        # Exclude already assigned
        if assigned_ids:
            query = query.filter(~Person.id.in_(assigned_ids))

        # Exclude absent people
        if absent_ids:
            query = query.filter(~Person.id.in_(absent_ids))

        return query.all()

    def get_by_pgy_level(self, pgy_level: int) -> List[Person]:
        """Get all residents at a specific PGY level."""
        return (
            self.db.query(Person)
            .filter(
                Person.type == "resident",
                Person.pgy_level == pgy_level,
            )
            .order_by(Person.name)
            .all()
        )
