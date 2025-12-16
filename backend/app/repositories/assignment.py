"""Assignment repository for database operations."""

from datetime import date
from typing import Optional, List
from uuid import UUID
from sqlalchemy.orm import Session, joinedload

from app.repositories.base import BaseRepository
from app.models.assignment import Assignment
from app.models.block import Block


class AssignmentRepository(BaseRepository[Assignment]):
    """Repository for Assignment entity operations."""

    def __init__(self, db: Session):
        super().__init__(Assignment, db)

    def get_by_id_with_relations(self, id: UUID) -> Optional[Assignment]:
        """Get assignment with related entities loaded."""
        return (
            self.db.query(Assignment)
            .options(
                joinedload(Assignment.block),
                joinedload(Assignment.person),
                joinedload(Assignment.rotation_template),
            )
            .filter(Assignment.id == id)
            .first()
        )

    def get_by_block_and_person(
        self, block_id: UUID, person_id: UUID
    ) -> Optional[Assignment]:
        """Check if a person is already assigned to a block."""
        return (
            self.db.query(Assignment)
            .filter(
                Assignment.block_id == block_id,
                Assignment.person_id == person_id,
            )
            .first()
        )

    def list_with_filters(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        person_id: Optional[UUID] = None,
        role: Optional[str] = None,
    ) -> List[Assignment]:
        """List assignments with optional filters and eager loading."""
        query = self.db.query(Assignment).options(
            joinedload(Assignment.block),
            joinedload(Assignment.person),
            joinedload(Assignment.rotation_template),
        )

        if start_date or end_date:
            query = query.join(Block)
            if start_date:
                query = query.filter(Block.date >= start_date)
            if end_date:
                query = query.filter(Block.date <= end_date)

        if person_id:
            query = query.filter(Assignment.person_id == person_id)
        if role:
            query = query.filter(Assignment.role == role)

        return query.all()

    def get_by_person_and_date_range(
        self, person_id: UUID, start_date: date, end_date: date
    ) -> List[Assignment]:
        """Get all assignments for a person in a date range."""
        return (
            self.db.query(Assignment)
            .join(Block)
            .filter(
                Assignment.person_id == person_id,
                Block.date >= start_date,
                Block.date <= end_date,
            )
            .all()
        )

    def get_by_block_ids(self, block_ids: List[UUID]) -> List[Assignment]:
        """Get assignments for a list of block IDs."""
        return (
            self.db.query(Assignment)
            .filter(Assignment.block_id.in_(block_ids))
            .all()
        )

    def delete_by_block_ids(self, block_ids: List[UUID]) -> int:
        """Delete all assignments in the given blocks. Returns count deleted."""
        deleted = (
            self.db.query(Assignment)
            .filter(Assignment.block_id.in_(block_ids))
            .delete(synchronize_session=False)
        )
        return deleted

    def get_person_ids_assigned_to_block(self, block_id: UUID) -> List[UUID]:
        """Get all person IDs assigned to a specific block."""
        results = (
            self.db.query(Assignment.person_id)
            .filter(Assignment.block_id == block_id)
            .all()
        )
        return [r[0] for r in results]
