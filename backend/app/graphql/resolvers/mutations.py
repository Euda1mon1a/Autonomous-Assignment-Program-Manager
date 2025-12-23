"""GraphQL mutation resolvers."""

from datetime import datetime
from uuid import UUID

import strawberry
from sqlalchemy.orm import Session

from app.graphql.types import (
    Assignment,
    AssignmentCreateInput,
    AssignmentUpdateInput,
    Person,
    PersonCreateInput,
    PersonUpdateInput,
    assignment_from_db,
    person_from_db,
)
from app.models.assignment import Assignment as DBAssignment
from app.models.person import Person as DBPerson


@strawberry.type
class Mutation:
    """Root mutation type."""

    @strawberry.mutation
    def create_person(self, info, input: PersonCreateInput) -> Person:
        """
        Create a new person (resident or faculty).

        Requires authentication and appropriate permissions.
        """
        db: Session = info.context["db"]
        user = info.context.get("user")

        # Authentication check
        if not user:
            raise Exception("Authentication required")

        # Validate input
        if input.type not in ("resident", "faculty"):
            raise ValueError("type must be 'resident' or 'faculty'")

        if input.pgy_level is not None and (input.pgy_level < 1 or input.pgy_level > 3):
            raise ValueError("pgy_level must be between 1 and 3")

        # Create database model
        db_person = DBPerson(
            name=input.name,
            type=input.type,
            email=input.email,
            pgy_level=input.pgy_level,
            target_clinical_blocks=input.target_clinical_blocks,
            performs_procedures=input.performs_procedures,
            specialties=input.specialties,
            primary_duty=input.primary_duty,
            faculty_role=input.faculty_role.value if input.faculty_role else None,
        )

        db.add(db_person)
        db.commit()
        db.refresh(db_person)

        return person_from_db(db_person)

    @strawberry.mutation
    def update_person(
        self,
        info,
        id: strawberry.ID,
        input: PersonUpdateInput,
    ) -> Person | None:
        """
        Update an existing person.

        Requires authentication and appropriate permissions.
        """
        db: Session = info.context["db"]
        user = info.context.get("user")

        # Authentication check
        if not user:
            raise Exception("Authentication required")

        # Find person
        db_person = db.query(DBPerson).filter(DBPerson.id == UUID(id)).first()
        if not db_person:
            return None

        # Update fields
        if input.name is not None:
            db_person.name = input.name
        if input.email is not None:
            db_person.email = input.email
        if input.pgy_level is not None:
            if input.pgy_level < 1 or input.pgy_level > 3:
                raise ValueError("pgy_level must be between 1 and 3")
            db_person.pgy_level = input.pgy_level
        if input.target_clinical_blocks is not None:
            db_person.target_clinical_blocks = input.target_clinical_blocks
        if input.performs_procedures is not None:
            db_person.performs_procedures = input.performs_procedures
        if input.specialties is not None:
            db_person.specialties = input.specialties
        if input.primary_duty is not None:
            db_person.primary_duty = input.primary_duty
        if input.faculty_role is not None:
            db_person.faculty_role = input.faculty_role.value

        db_person.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(db_person)

        return person_from_db(db_person)

    @strawberry.mutation
    def delete_person(self, info, id: strawberry.ID) -> bool:
        """
        Delete a person.

        Requires authentication and appropriate permissions.
        WARNING: This will cascade delete all related assignments.
        """
        db: Session = info.context["db"]
        user = info.context.get("user")

        # Authentication check
        if not user:
            raise Exception("Authentication required")

        # Find and delete person
        db_person = db.query(DBPerson).filter(DBPerson.id == UUID(id)).first()
        if not db_person:
            return False

        db.delete(db_person)
        db.commit()

        return True

    @strawberry.mutation
    def create_assignment(
        self,
        info,
        input: AssignmentCreateInput,
    ) -> Assignment:
        """
        Create a new assignment.

        Requires authentication and appropriate permissions.
        """
        db: Session = info.context["db"]
        user = info.context.get("user")

        # Authentication check
        if not user:
            raise Exception("Authentication required")

        # Validate role
        if input.role.value not in ("primary", "supervising", "backup"):
            raise ValueError("role must be 'primary', 'supervising', or 'backup'")

        # Create database model
        db_assignment = DBAssignment(
            block_id=UUID(input.block_id),
            person_id=UUID(input.person_id),
            rotation_template_id=UUID(input.rotation_template_id)
            if input.rotation_template_id
            else None,
            role=input.role.value,
            activity_override=input.activity_override,
            notes=input.notes,
            override_reason=input.override_reason,
            created_by=user.get("username", "graphql_api"),
        )

        db.add(db_assignment)
        db.commit()
        db.refresh(db_assignment)

        return assignment_from_db(db_assignment)

    @strawberry.mutation
    def update_assignment(
        self,
        info,
        id: strawberry.ID,
        input: AssignmentUpdateInput,
    ) -> Assignment | None:
        """
        Update an existing assignment.

        Requires authentication and appropriate permissions.
        """
        db: Session = info.context["db"]
        user = info.context.get("user")

        # Authentication check
        if not user:
            raise Exception("Authentication required")

        # Find assignment
        db_assignment = (
            db.query(DBAssignment).filter(DBAssignment.id == UUID(id)).first()
        )
        if not db_assignment:
            return None

        # Update fields
        if input.rotation_template_id is not None:
            db_assignment.rotation_template_id = UUID(input.rotation_template_id)
        if input.role is not None:
            db_assignment.role = input.role.value
        if input.activity_override is not None:
            db_assignment.activity_override = input.activity_override
        if input.notes is not None:
            db_assignment.notes = input.notes
        if input.override_reason is not None:
            db_assignment.override_reason = input.override_reason
        if input.acknowledge_override:
            db_assignment.override_acknowledged_at = datetime.utcnow()

        db_assignment.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(db_assignment)

        return assignment_from_db(db_assignment)

    @strawberry.mutation
    def delete_assignment(self, info, id: strawberry.ID) -> bool:
        """
        Delete an assignment.

        Requires authentication and appropriate permissions.
        """
        db: Session = info.context["db"]
        user = info.context.get("user")

        # Authentication check
        if not user:
            raise Exception("Authentication required")

        # Find and delete assignment
        db_assignment = (
            db.query(DBAssignment).filter(DBAssignment.id == UUID(id)).first()
        )
        if not db_assignment:
            return False

        db.delete(db_assignment)
        db.commit()

        return True

    @strawberry.mutation
    def batch_create_assignments(
        self,
        info,
        inputs: list[AssignmentCreateInput],
    ) -> list[Assignment]:
        """
        Create multiple assignments in a single transaction.

        Useful for bulk schedule operations.
        Requires authentication and appropriate permissions.
        """
        db: Session = info.context["db"]
        user = info.context.get("user")

        # Authentication check
        if not user:
            raise Exception("Authentication required")

        created_assignments = []

        try:
            for input in inputs:
                # Validate role
                if input.role.value not in ("primary", "supervising", "backup"):
                    raise ValueError(f"Invalid role: {input.role.value}")

                # Create database model
                db_assignment = DBAssignment(
                    block_id=UUID(input.block_id),
                    person_id=UUID(input.person_id),
                    rotation_template_id=UUID(input.rotation_template_id)
                    if input.rotation_template_id
                    else None,
                    role=input.role.value,
                    activity_override=input.activity_override,
                    notes=input.notes,
                    override_reason=input.override_reason,
                    created_by=user.get("username", "graphql_api"),
                )

                db.add(db_assignment)
                created_assignments.append(db_assignment)

            # Commit all at once
            db.commit()

            # Refresh all assignments
            for assignment in created_assignments:
                db.refresh(assignment)

            return [assignment_from_db(a) for a in created_assignments]

        except Exception as e:
            db.rollback()
            raise e
