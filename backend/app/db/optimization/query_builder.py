"""Optimized query builders for common database operations.

Provides pre-optimized query patterns for common operations to ensure
consistent performance and avoid N+1 queries.
"""

import logging
from datetime import date, datetime
from typing import Any, Optional

from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.models.absence import Absence
from app.models.assignment import Assignment
from app.models.block import Block
from app.models.person import Person
from app.models.rotation_template import RotationTemplate
from app.models.swap import SwapRecord

logger = logging.getLogger(__name__)


class OptimizedQueryBuilder:
    """
    Builder for optimized database queries.

    Provides pre-configured queries with proper eager loading and indexing
    hints to avoid common performance pitfalls.

    Usage:
        builder = OptimizedQueryBuilder(db)
        assignments = builder.get_assignments_with_relations(
            start_date=date(2024, 1, 1),
            end_date=date(2024, 12, 31)
        )
    """

    def __init__(self, db: Session):
        """
        Initialize query builder.

        Args:
            db: Database session
        """
        self.db = db

    def get_assignments_with_relations(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        person_id: Optional[str] = None,
        rotation_id: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> list[Assignment]:
        """
        Get assignments with all related data eagerly loaded.

        Optimized to prevent N+1 queries by using selectinload.

        Args:
            start_date: Filter by start date
            end_date: Filter by end date
            person_id: Filter by person ID
            rotation_id: Filter by rotation template ID
            limit: Maximum number of results

        Returns:
            List of Assignment objects with relations loaded
        """
        query = (
            select(Assignment)
            .options(
                selectinload(Assignment.person),
                selectinload(Assignment.block),
                selectinload(Assignment.rotation_template),
            )
            .join(Block)
        )

        # Apply filters
        filters = []
        if start_date:
            filters.append(Block.date >= start_date)
        if end_date:
            filters.append(Block.date <= end_date)
        if person_id:
            filters.append(Assignment.person_id == person_id)
        if rotation_id:
            filters.append(Assignment.rotation_template_id == rotation_id)

        if filters:
            query = query.where(and_(*filters))

        # Order by date
        query = query.order_by(Block.date, Block.session)

        if limit:
            query = query.limit(limit)

        result = self.db.execute(query)
        return list(result.scalars().all())

    def get_persons_with_assignments(
        self,
        role: Optional[str] = None,
        include_assignments: bool = True,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> list[Person]:
        """
        Get persons with their assignments eagerly loaded.

        Args:
            role: Filter by role
            include_assignments: Whether to load assignments
            start_date: Filter assignments by start date
            end_date: Filter assignments by end date

        Returns:
            List of Person objects with assignments loaded
        """
        query = select(Person)

        if include_assignments:
            # Use selectinload to avoid N+1
            query = query.options(
                selectinload(Person.assignments).selectinload(Assignment.block),
                selectinload(Person.assignments).selectinload(
                    Assignment.rotation_template
                ),
            )

        if role:
            query = query.where(Person.role == role)

        query = query.order_by(Person.name)

        result = self.db.execute(query)
        persons = list(result.scalars().all())

        # Filter assignments by date if needed
        if include_assignments and (start_date or end_date):
            for person in persons:
                filtered_assignments = []
                for assignment in person.assignments:
                    if assignment.block:
                        block_date = assignment.block.date
                        if start_date and block_date < start_date:
                            continue
                        if end_date and block_date > end_date:
                            continue
                        filtered_assignments.append(assignment)
                person.assignments = filtered_assignments

        return persons

    def get_blocks_with_assignments(
        self,
        start_date: date,
        end_date: date,
        session: Optional[str] = None,
    ) -> list[Block]:
        """
        Get blocks with assignments eagerly loaded.

        Args:
            start_date: Start date
            end_date: End date
            session: Filter by session (AM/PM)

        Returns:
            List of Block objects with assignments loaded
        """
        query = (
            select(Block)
            .options(
                selectinload(Block.assignments).selectinload(Assignment.person),
                selectinload(Block.assignments).selectinload(
                    Assignment.rotation_template
                ),
            )
            .where(and_(Block.date >= start_date, Block.date <= end_date))
        )

        if session:
            query = query.where(Block.session == session)

        query = query.order_by(Block.date, Block.session)

        result = self.db.execute(query)
        return list(result.scalars().all())

    def get_active_swap_records(
        self, person_id: Optional[str] = None, include_relations: bool = True
    ) -> list[SwapRecord]:
        """
        Get active swap records with relations loaded.

        Args:
            person_id: Filter by source or target faculty ID
            include_relations: Whether to load related objects

        Returns:
            List of active SwapRecord objects
        """
        query = select(SwapRecord).where(
            SwapRecord.status.in_(["pending", "approved"])
        )

        if include_relations:
            query = query.options(
                selectinload(SwapRecord.source_faculty),
                selectinload(SwapRecord.target_faculty),
            )

        if person_id:
            query = query.where(
                or_(
                    SwapRecord.source_faculty_id == person_id,
                    SwapRecord.target_faculty_id == person_id,
                )
            )

        query = query.order_by(SwapRecord.requested_at.desc())

        result = self.db.execute(query)
        return list(result.scalars().all())

    def get_absences_in_range(
        self,
        start_date: date,
        end_date: date,
        person_id: Optional[str] = None,
        absence_type: Optional[str] = None,
    ) -> list[Absence]:
        """
        Get absences that overlap with date range.

        Optimized query for finding absence conflicts.

        Args:
            start_date: Range start date
            end_date: Range end date
            person_id: Filter by person ID
            absence_type: Filter by absence type

        Returns:
            List of Absence objects
        """
        # Overlap condition: absence.start <= range.end AND absence.end >= range.start
        query = (
            select(Absence)
            .options(selectinload(Absence.person))
            .where(
                and_(
                    Absence.start_date <= end_date,
                    Absence.end_date >= start_date,
                )
            )
        )

        if person_id:
            query = query.where(Absence.person_id == person_id)

        if absence_type:
            query = query.where(Absence.absence_type == absence_type)

        query = query.order_by(Absence.start_date)

        result = self.db.execute(query)
        return list(result.scalars().all())

    def bulk_get_assignments_by_ids(
        self, assignment_ids: list[str], include_relations: bool = True
    ) -> dict[str, Assignment]:
        """
        Bulk fetch assignments by IDs.

        More efficient than fetching one at a time.

        Args:
            assignment_ids: List of assignment IDs
            include_relations: Whether to load related objects

        Returns:
            Dictionary mapping assignment ID to Assignment object
        """
        if not assignment_ids:
            return {}

        query = select(Assignment).where(Assignment.id.in_(assignment_ids))

        if include_relations:
            query = query.options(
                selectinload(Assignment.person),
                selectinload(Assignment.block),
                selectinload(Assignment.rotation_template),
            )

        result = self.db.execute(query)
        assignments = result.scalars().all()

        return {str(a.id): a for a in assignments}

    def bulk_get_persons_by_ids(
        self, person_ids: list[str], include_assignments: bool = False
    ) -> dict[str, Person]:
        """
        Bulk fetch persons by IDs.

        Args:
            person_ids: List of person IDs
            include_assignments: Whether to load assignments

        Returns:
            Dictionary mapping person ID to Person object
        """
        if not person_ids:
            return {}

        query = select(Person).where(Person.id.in_(person_ids))

        if include_assignments:
            query = query.options(
                selectinload(Person.assignments).selectinload(Assignment.block)
            )

        result = self.db.execute(query)
        persons = result.scalars().all()

        return {str(p.id): p for p in persons}

    def get_assignment_counts_by_person(
        self,
        start_date: date,
        end_date: date,
        role: Optional[str] = None,
    ) -> dict[str, dict[str, Any]]:
        """
        Get assignment counts grouped by person.

        Optimized aggregation query.

        Args:
            start_date: Start date
            end_date: End date
            role: Filter by person role

        Returns:
            Dictionary with person stats
        """
        query = (
            select(
                Person.id,
                Person.name,
                Person.role,
                func.count(Assignment.id).label("assignment_count"),
            )
            .join(Assignment, Assignment.person_id == Person.id)
            .join(Block, Block.id == Assignment.block_id)
            .where(and_(Block.date >= start_date, Block.date <= end_date))
            .group_by(Person.id, Person.name, Person.role)
        )

        if role:
            query = query.where(Person.role == role)

        result = self.db.execute(query)

        stats = {}
        for row in result:
            person_id = str(row[0])
            stats[person_id] = {
                "person_id": person_id,
                "name": row[1],
                "role": row[2],
                "assignment_count": row[3],
            }

        return stats

    def get_coverage_stats_by_rotation(
        self, start_date: date, end_date: date
    ) -> dict[str, dict[str, Any]]:
        """
        Get coverage statistics grouped by rotation.

        Args:
            start_date: Start date
            end_date: End date

        Returns:
            Dictionary with rotation coverage stats
        """
        query = (
            select(
                RotationTemplate.id,
                RotationTemplate.name,
                func.count(Assignment.id).label("assignment_count"),
                func.count(func.distinct(Assignment.person_id)).label(
                    "unique_persons"
                ),
            )
            .join(Assignment, Assignment.rotation_template_id == RotationTemplate.id)
            .join(Block, Block.id == Assignment.block_id)
            .where(and_(Block.date >= start_date, Block.date <= end_date))
            .group_by(RotationTemplate.id, RotationTemplate.name)
        )

        result = self.db.execute(query)

        stats = {}
        for row in result:
            rotation_id = str(row[0])
            stats[rotation_id] = {
                "rotation_id": rotation_id,
                "name": row[1],
                "assignment_count": row[2],
                "unique_persons": row[3],
            }

        return stats

    def get_uncovered_blocks(
        self, start_date: date, end_date: date, limit: Optional[int] = 100
    ) -> list[Block]:
        """
        Get blocks without assignments.

        Optimized LEFT JOIN to find gaps in coverage.

        Args:
            start_date: Start date
            end_date: End date
            limit: Maximum results

        Returns:
            List of uncovered Block objects
        """
        # Using LEFT JOIN to find blocks with no assignments
        query = (
            select(Block)
            .outerjoin(Assignment, Assignment.block_id == Block.id)
            .where(
                and_(
                    Block.date >= start_date,
                    Block.date <= end_date,
                    Assignment.id.is_(None),
                )
            )
            .order_by(Block.date, Block.session)
        )

        if limit:
            query = query.limit(limit)

        result = self.db.execute(query)
        return list(result.scalars().all())

    def batch_create_assignments(
        self, assignments_data: list[dict[str, Any]]
    ) -> list[Assignment]:
        """
        Bulk create assignments efficiently.

        Uses bulk insert for better performance.

        Args:
            assignments_data: List of assignment dictionaries

        Returns:
            List of created Assignment objects
        """
        if not assignments_data:
            return []

        try:
            # Use bulk_insert_mappings for better performance
            self.db.bulk_insert_mappings(Assignment, assignments_data)
            self.db.commit()

            # Fetch the created assignments
            assignment_ids = [a.get("id") for a in assignments_data if a.get("id")]
            if assignment_ids:
                return list(
                    self.db.execute(
                        select(Assignment).where(Assignment.id.in_(assignment_ids))
                    )
                    .scalars()
                    .all()
                )

            return []

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error batch creating assignments: {e}")
            raise

    def batch_update_assignments(
        self, updates: list[dict[str, Any]]
    ) -> None:
        """
        Bulk update assignments efficiently.

        Args:
            updates: List of update dictionaries with 'id' and fields to update
        """
        if not updates:
            return

        try:
            # Use bulk_update_mappings for better performance
            self.db.bulk_update_mappings(Assignment, updates)
            self.db.commit()

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error batch updating assignments: {e}")
            raise

    def batch_delete_assignments(self, assignment_ids: list[str]) -> int:
        """
        Bulk delete assignments efficiently.

        Args:
            assignment_ids: List of assignment IDs to delete

        Returns:
            Number of deleted assignments
        """
        if not assignment_ids:
            return 0

        try:
            # Use bulk delete for better performance
            count = (
                self.db.query(Assignment)
                .filter(Assignment.id.in_(assignment_ids))
                .delete(synchronize_session=False)
            )
            self.db.commit()
            return count

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error batch deleting assignments: {e}")
            raise


def get_optimized_query_builder(db: Session) -> OptimizedQueryBuilder:
    """
    Get an optimized query builder instance.

    Args:
        db: Database session

    Returns:
        OptimizedQueryBuilder instance
    """
    return OptimizedQueryBuilder(db)
