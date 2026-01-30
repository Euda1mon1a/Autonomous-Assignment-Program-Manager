"""Block assignment repository for database operations."""

from uuid import UUID

from sqlalchemy.orm import Session, joinedload

from app.models.block_assignment import BlockAssignment
from app.repositories.base import BaseRepository


class BlockAssignmentRepository(BaseRepository[BlockAssignment]):
    """Repository for BlockAssignment entity operations."""

    def __init__(self, db: Session) -> None:
        super().__init__(BlockAssignment, db)

    def get_by_id_with_relations(self, id: UUID) -> BlockAssignment | None:
        """Get block assignment with related resident and rotation template loaded."""
        return (
            self.db.query(BlockAssignment)
            .options(
                joinedload(BlockAssignment.resident),
                joinedload(BlockAssignment.rotation_template),
            )
            .filter(BlockAssignment.id == id)
            .first()
        )

    def list_by_block(
        self,
        block_number: int,
        academic_year: int,
        include_relations: bool = True,
    ) -> list[BlockAssignment]:
        """
        List all assignments for a specific block.

        Args:
            block_number: Academic block number (0-13)
            academic_year: Academic year (e.g., 2025)
            include_relations: If True, eager load resident and rotation template
        """
        query = self.db.query(BlockAssignment)

        if include_relations:
            query = query.options(
                joinedload(BlockAssignment.resident),
                joinedload(BlockAssignment.rotation_template),
            )

        return (
            query.filter(
                BlockAssignment.block_number == block_number,
                BlockAssignment.academic_year == academic_year,
            )
            .order_by(BlockAssignment.created_at)
            .all()
        )

    def list_by_resident(
        self,
        resident_id: UUID,
        academic_year: int | None = None,
    ) -> list[BlockAssignment]:
        """List all assignments for a resident, optionally filtered by year."""
        query = (
            self.db.query(BlockAssignment)
            .options(joinedload(BlockAssignment.rotation_template))
            .filter(BlockAssignment.resident_id == resident_id)
        )

        if academic_year:
            query = query.filter(BlockAssignment.academic_year == academic_year)

        return query.order_by(
            BlockAssignment.academic_year, BlockAssignment.block_number
        ).all()

    def list_by_rotation(
        self,
        rotation_template_id: UUID,
        block_number: int | None = None,
        academic_year: int | None = None,
    ) -> list[BlockAssignment]:
        """List all assignments for a rotation template."""
        query = (
            self.db.query(BlockAssignment)
            .options(joinedload(BlockAssignment.resident))
            .filter(BlockAssignment.rotation_template_id == rotation_template_id)
        )

        if block_number is not None:
            query = query.filter(BlockAssignment.block_number == block_number)
        if academic_year:
            query = query.filter(BlockAssignment.academic_year == academic_year)

        return query.order_by(
            BlockAssignment.academic_year, BlockAssignment.block_number
        ).all()

    def get_residents_with_leave(
        self,
        block_number: int,
        academic_year: int,
    ) -> list[BlockAssignment]:
        """Get all assignments where resident has leave in the block."""
        return (
            self.db.query(BlockAssignment)
            .options(
                joinedload(BlockAssignment.resident),
                joinedload(BlockAssignment.rotation_template),
            )
            .filter(
                BlockAssignment.block_number == block_number,
                BlockAssignment.academic_year == academic_year,
                BlockAssignment.has_leave == True,  # noqa: E712
            )
            .all()
        )

    def get_assignment_for_resident(
        self,
        resident_id: UUID,
        block_number: int,
        academic_year: int,
    ) -> BlockAssignment | None:
        """Get the assignment for a specific resident in a specific block."""
        return (
            self.db.query(BlockAssignment)
            .options(joinedload(BlockAssignment.rotation_template))
            .filter(
                BlockAssignment.resident_id == resident_id,
                BlockAssignment.block_number == block_number,
                BlockAssignment.academic_year == academic_year,
            )
            .first()
        )

    def count_by_rotation(
        self,
        rotation_template_id: UUID,
        block_number: int,
        academic_year: int,
    ) -> int:
        """Count how many residents are assigned to a rotation in a block."""
        return (
            self.db.query(BlockAssignment)
            .filter(
                BlockAssignment.rotation_template_id == rotation_template_id,
                BlockAssignment.block_number == block_number,
                BlockAssignment.academic_year == academic_year,
            )
            .count()
        )

    def delete_block_assignments(
        self,
        block_number: int,
        academic_year: int,
    ) -> int:
        """
        Delete all assignments for a block.

        Returns the number of deleted assignments.
        """
        deleted = (
            self.db.query(BlockAssignment)
            .filter(
                BlockAssignment.block_number == block_number,
                BlockAssignment.academic_year == academic_year,
            )
            .delete(synchronize_session=False)
        )
        return deleted

    def bulk_create(self, assignments: list[dict]) -> list[BlockAssignment]:
        """
        Create multiple assignments in bulk.

        Args:
            assignments: List of assignment dictionaries

        Returns:
            List of created BlockAssignment objects
        """
        created = []
        for assignment_data in assignments:
            db_obj = BlockAssignment(**assignment_data)
            self.db.add(db_obj)
            created.append(db_obj)

        self.db.flush()
        return created
