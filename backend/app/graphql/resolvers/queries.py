"""GraphQL query resolvers."""

from datetime import date
from uuid import UUID

import strawberry
from sqlalchemy import and_, func
from sqlalchemy.orm import Session, selectinload

from app.graphql.types import (
    Assignment,
    AssignmentConnection,
    AssignmentFilterInput,
    Block,
    BlockConnection,
    BlockFilterInput,
    Person,
    PersonConnection,
    PersonFilterInput,
    ScheduleMetrics,
    ScheduleSummary,
    assignment_from_db,
    block_from_db,
    person_from_db,
)
from app.models.assignment import Assignment as DBAssignment
from app.models.block import Block as DBBlock
from app.models.person import Person as DBPerson


@strawberry.type
class Query:
    """Root query type."""

    @strawberry.field
    def person(self, info, id: strawberry.ID) -> Person | None:
        """Get a single person by ID."""
        db: Session = info.context["db"]

        db_person = db.query(DBPerson).filter(DBPerson.id == UUID(id)).first()
        if not db_person:
            return None

        return person_from_db(db_person)

    @strawberry.field
    def people(
        self,
        info,
        filter: PersonFilterInput | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> PersonConnection:
        """Get a paginated list of people with optional filtering."""
        db: Session = info.context["db"]

        query = db.query(DBPerson)

        # Apply filters
        if filter:
            if filter.type:
                query = query.filter(DBPerson.type == filter.type)
            if filter.pgy_level is not None:
                query = query.filter(DBPerson.pgy_level == filter.pgy_level)
            if filter.faculty_role:
                query = query.filter(DBPerson.faculty_role == filter.faculty_role.value)
            if filter.performs_procedures is not None:
                query = query.filter(
                    DBPerson.performs_procedures == filter.performs_procedures
                )

        # Get total count
        total = query.count()

        # Apply pagination
        db_people = query.order_by(DBPerson.name).offset(offset).limit(limit).all()

        # Convert to GraphQL types
        items = [person_from_db(p) for p in db_people]

        return PersonConnection(
            items=items,
            total=total,
            has_next_page=(offset + limit) < total,
            has_previous_page=offset > 0,
        )

    @strawberry.field
    def assignment(self, info, id: strawberry.ID) -> Assignment | None:
        """Get a single assignment by ID."""
        db: Session = info.context["db"]

        db_assignment = (
            db.query(DBAssignment).filter(DBAssignment.id == UUID(id)).first()
        )
        if not db_assignment:
            return None

        return assignment_from_db(db_assignment)

    @strawberry.field
    def assignments(
        self,
        info,
        filter: AssignmentFilterInput | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> AssignmentConnection:
        """Get a paginated list of assignments with optional filtering."""
        db: Session = info.context["db"]

        query = db.query(DBAssignment).options(
            selectinload(DBAssignment.person),
            selectinload(DBAssignment.block),
            selectinload(DBAssignment.rotation_template),
        )

        # Apply filters
        if filter:
            if filter.person_id:
                query = query.filter(DBAssignment.person_id == UUID(filter.person_id))
            if filter.block_id:
                query = query.filter(DBAssignment.block_id == UUID(filter.block_id))
            if filter.rotation_template_id:
                query = query.filter(
                    DBAssignment.rotation_template_id
                    == UUID(filter.rotation_template_id)
                )
            if filter.role:
                query = query.filter(DBAssignment.role == filter.role.value)
            if filter.start_date or filter.end_date:
                # Join with blocks to filter by date
                query = query.join(DBBlock)
                if filter.start_date:
                    query = query.filter(DBBlock.date >= filter.start_date)
                if filter.end_date:
                    query = query.filter(DBBlock.date <= filter.end_date)

        # Get total count
        total = query.count()

        # Apply pagination
        db_assignments = (
            query.order_by(DBAssignment.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

        # Convert to GraphQL types
        items = [assignment_from_db(a) for a in db_assignments]

        return AssignmentConnection(
            items=items,
            total=total,
            has_next_page=(offset + limit) < total,
            has_previous_page=offset > 0,
        )

    @strawberry.field
    def block(self, info, id: strawberry.ID) -> Block | None:
        """Get a single block by ID."""
        db: Session = info.context["db"]

        db_block = db.query(DBBlock).filter(DBBlock.id == UUID(id)).first()
        if not db_block:
            return None

        return block_from_db(db_block)

    @strawberry.field
    def blocks(
        self,
        info,
        filter: BlockFilterInput | None = None,
        offset: int = 0,
        limit: int = 100,
    ) -> BlockConnection:
        """Get a paginated list of blocks with optional filtering."""
        db: Session = info.context["db"]

        query = db.query(DBBlock)

        # Apply filters
        if filter:
            if filter.start_date:
                query = query.filter(DBBlock.date >= filter.start_date)
            if filter.end_date:
                query = query.filter(DBBlock.date <= filter.end_date)
            if filter.time_of_day:
                query = query.filter(DBBlock.time_of_day == filter.time_of_day.value)
            if filter.is_weekend is not None:
                query = query.filter(DBBlock.is_weekend == filter.is_weekend)
            if filter.is_holiday is not None:
                query = query.filter(DBBlock.is_holiday == filter.is_holiday)
            if filter.block_number is not None:
                query = query.filter(DBBlock.block_number == filter.block_number)

        # Get total count
        total = query.count()

        # Apply pagination
        db_blocks = (
            query.order_by(DBBlock.date, DBBlock.time_of_day)
            .offset(offset)
            .limit(limit)
            .all()
        )

        # Convert to GraphQL types
        items = [block_from_db(b) for b in db_blocks]

        return BlockConnection(
            items=items,
            total=total,
            has_next_page=(offset + limit) < total,
            has_previous_page=offset > 0,
        )

    @strawberry.field
    def schedule_summary(
        self,
        info,
        start_date: date,
        end_date: date,
    ) -> ScheduleSummary:
        """Get a summary of the schedule for a date range."""
        db: Session = info.context["db"]

        # Get total people
        total_people = db.query(func.count(DBPerson.id)).scalar()

        # Get total blocks in range
        total_blocks = (
            db.query(func.count(DBBlock.id))
            .filter(
                and_(
                    DBBlock.date >= start_date,
                    DBBlock.date <= end_date,
                )
            )
            .scalar()
        )

        # Get total assignments in range
        total_assignments = (
            db.query(func.count(DBAssignment.id))
            .join(DBBlock)
            .filter(
                and_(
                    DBBlock.date >= start_date,
                    DBBlock.date <= end_date,
                )
            )
            .scalar()
        )

        # Calculate metrics
        coverage_percentage = (
            (total_assignments / total_blocks * 100) if total_blocks > 0 else 0.0
        )

        # Calculate average confidence score as proxy for compliance
        avg_confidence = (
            db.query(func.avg(DBAssignment.confidence))
            .join(DBBlock)
            .filter(
                and_(
                    DBBlock.date >= start_date,
                    DBBlock.date <= end_date,
                    DBAssignment.confidence.isnot(None),
                )
            )
            .scalar()
            or 0.0
        )

        metrics = ScheduleMetrics(
            total_assignments=total_assignments or 0,
            total_blocks=total_blocks or 0,
            coverage_percentage=coverage_percentage,
            acgme_compliance_score=avg_confidence * 100,
            average_utilization=coverage_percentage / 100,
        )

        return ScheduleSummary(
            start_date=start_date,
            end_date=end_date,
            total_people=total_people or 0,
            total_blocks=total_blocks or 0,
            total_assignments=total_assignments or 0,
            metrics=metrics,
        )

    @strawberry.field
    def person_assignments(
        self,
        info,
        person_id: strawberry.ID,
        start_date: date | None = None,
        end_date: date | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> AssignmentConnection:
        """Get assignments for a specific person with date filtering."""
        filter_input = AssignmentFilterInput(
            person_id=person_id,
            start_date=start_date,
            end_date=end_date,
        )
        return self.assignments(info, filter=filter_input, offset=offset, limit=limit)
