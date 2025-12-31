"""Factory for creating test Assignment instances."""

from typing import Optional
from uuid import UUID, uuid4

from faker import Faker
from sqlalchemy.orm import Session

from app.models.assignment import Assignment
from app.models.block import Block
from app.models.person import Person
from app.models.rotation_template import RotationTemplate

fake = Faker()


class AssignmentFactory:
    """Factory for creating Assignment instances with random data."""

    @staticmethod
    def create_assignment(
        db: Session,
        person: Person | None = None,
        block: Block | None = None,
        rotation_template: RotationTemplate | None = None,
        role: str = "primary",
        activity_override: str | None = None,
        notes: str | None = None,
        created_by: str | None = None,
        confidence: float | None = None,
        score: float | None = None,
    ) -> Assignment:
        """
        Create a single assignment.

        Args:
            db: Database session
            person: Person to assign (required or will error)
            block: Block to assign to (required or will error)
            rotation_template: Rotation template (optional)
            role: Assignment role ("primary", "supervising", "backup")
            activity_override: Override activity name
            notes: Assignment notes
            created_by: Who created this assignment
            confidence: Confidence score 0-1
            score: Objective score for this assignment

        Returns:
            Assignment: Created assignment instance
        """
        if person is None or block is None:
            raise ValueError("person and block are required for assignment creation")

        if confidence is None:
            confidence = fake.random.uniform(0.7, 1.0)

        if score is None:
            score = fake.random.uniform(0.5, 1.0)

        assignment = Assignment(
            id=uuid4(),
            person_id=person.id,
            block_id=block.id,
            rotation_template_id=rotation_template.id if rotation_template else None,
            role=role,
            activity_override=activity_override,
            notes=notes,
            created_by=created_by or "test_system",
            confidence=confidence,
            score=score,
        )
        db.add(assignment)
        db.commit()
        db.refresh(assignment)
        return assignment

    @staticmethod
    def create_primary_assignment(
        db: Session,
        person: Person,
        block: Block,
        rotation_template: RotationTemplate,
    ) -> Assignment:
        """
        Create a primary assignment (main assignment for a resident).

        Args:
            db: Database session
            person: Person to assign
            block: Block to assign to
            rotation_template: Rotation template

        Returns:
            Assignment: Created primary assignment
        """
        return AssignmentFactory.create_assignment(
            db,
            person=person,
            block=block,
            rotation_template=rotation_template,
            role="primary",
        )

    @staticmethod
    def create_supervising_assignment(
        db: Session,
        person: Person,
        block: Block,
        rotation_template: RotationTemplate,
    ) -> Assignment:
        """
        Create a supervising assignment (faculty supervising residents).

        Args:
            db: Database session
            person: Faculty person to assign
            block: Block to assign to
            rotation_template: Rotation template

        Returns:
            Assignment: Created supervising assignment
        """
        if not person.is_faculty:
            raise ValueError("Supervising assignments require faculty person")

        return AssignmentFactory.create_assignment(
            db,
            person=person,
            block=block,
            rotation_template=rotation_template,
            role="supervising",
        )

    @staticmethod
    def create_backup_assignment(
        db: Session,
        person: Person,
        block: Block,
        rotation_template: RotationTemplate,
    ) -> Assignment:
        """
        Create a backup assignment (backup coverage).

        Args:
            db: Database session
            person: Person to assign as backup
            block: Block to assign to
            rotation_template: Rotation template

        Returns:
            Assignment: Created backup assignment
        """
        return AssignmentFactory.create_assignment(
            db,
            person=person,
            block=block,
            rotation_template=rotation_template,
            role="backup",
        )

    @staticmethod
    def create_batch_assignments(
        db: Session,
        persons: list[Person],
        blocks: list[Block],
        rotation_template: RotationTemplate,
        role: str = "primary",
    ) -> list[Assignment]:
        """
        Create multiple assignments for a group of people across blocks.

        Assigns each person to each block with the given rotation template.

        Args:
            db: Database session
            persons: List of persons to assign
            blocks: List of blocks to assign to
            rotation_template: Rotation template for all assignments
            role: Assignment role

        Returns:
            list[Assignment]: List of created assignments
        """
        assignments = []
        for person in persons:
            for block in blocks:
                assignment = AssignmentFactory.create_assignment(
                    db,
                    person=person,
                    block=block,
                    rotation_template=rotation_template,
                    role=role,
                )
                assignments.append(assignment)

        return assignments

    @staticmethod
    def create_week_assignments(
        db: Session,
        person: Person,
        blocks: list[Block],
        rotation_template: RotationTemplate,
        role: str = "primary",
    ) -> list[Assignment]:
        """
        Create assignments for one person across a week of blocks.

        Args:
            db: Database session
            person: Person to assign
            blocks: Week of blocks (typically 14: 7 days × AM/PM)
            rotation_template: Rotation template
            role: Assignment role

        Returns:
            list[Assignment]: List of assignments for the week
        """
        assignments = []
        for block in blocks:
            assignment = AssignmentFactory.create_assignment(
                db,
                person=person,
                block=block,
                rotation_template=rotation_template,
                role=role,
            )
            assignments.append(assignment)

        return assignments

    @staticmethod
    def create_supervised_session(
        db: Session,
        residents: list[Person],
        faculty: Person,
        block: Block,
        rotation_template: RotationTemplate,
    ) -> list[Assignment]:
        """
        Create a supervised clinic session with residents and faculty.

        Args:
            db: Database session
            residents: List of residents to assign
            faculty: Faculty supervisor
            block: Block for the session
            rotation_template: Rotation template (should require supervision)

        Returns:
            list[Assignment]: List of assignments (residents + supervisor)
        """
        assignments = []

        # Assign residents as primary
        for resident in residents:
            assignment = AssignmentFactory.create_primary_assignment(
                db, resident, block, rotation_template
            )
            assignments.append(assignment)

        # Assign faculty as supervising
        supervisor_assignment = AssignmentFactory.create_supervising_assignment(
            db, faculty, block, rotation_template
        )
        assignments.append(supervisor_assignment)

        return assignments

    @staticmethod
    def create_conflicting_assignments(
        db: Session,
        person: Person,
        blocks: list[Block],
        rotation_templates: list[RotationTemplate],
    ) -> list[Assignment]:
        """
        Create conflicting assignments (same person, overlapping blocks, different rotations).

        Useful for testing conflict detection.

        Args:
            db: Database session
            person: Person to create conflicts for
            blocks: Overlapping blocks
            rotation_templates: Different rotation templates (should have >= 2)

        Returns:
            list[Assignment]: List of conflicting assignments
        """
        if len(rotation_templates) < 2:
            raise ValueError("Need at least 2 rotation templates to create conflicts")

        assignments = []
        for i, block in enumerate(blocks):
            # Assign to different rotations on same blocks
            template = rotation_templates[i % len(rotation_templates)]
            assignment = AssignmentFactory.create_assignment(
                db, person=person, block=block, rotation_template=template
            )
            assignments.append(assignment)

        return assignments

    @staticmethod
    def create_double_booked_assignment(
        db: Session,
        person: Person,
        block: Block,
        rotation_templates: list[RotationTemplate],
    ) -> list[Assignment]:
        """
        Create double-booked assignments (same person, same block, multiple rotations).

        This violates the unique constraint and is useful for testing validation.

        Args:
            db: Database session
            person: Person to double-book
            block: Block to double-book
            rotation_templates: Multiple rotation templates

        Returns:
            list[Assignment]: List of double-booked assignments
        """
        assignments = []

        for template in rotation_templates:
            # This will violate unique_person_per_block constraint
            assignment = Assignment(
                id=uuid4(),
                person_id=person.id,
                block_id=block.id,
                rotation_template_id=template.id,
                role="primary",
            )
            db.add(assignment)
            assignments.append(assignment)

        # Don't commit - let test handle the constraint violation
        return assignments

    @staticmethod
    def create_acgme_compliant_week(
        db: Session,
        resident: Person,
        blocks: list[Block],
        clinic_template: RotationTemplate,
        conference_template: RotationTemplate,
    ) -> list[Assignment]:
        """
        Create ACGME-compliant week (standard work hours, proper distribution).

        Creates:
        - 4 clinic half-days (Mon-Thu AM)
        - 1 conference half-day (Fri AM)
        - Weekends off

        Args:
            db: Database session
            resident: Resident to assign
            blocks: Week of blocks (14 blocks: 7 days × AM/PM)
            clinic_template: Clinic rotation template
            conference_template: Conference rotation template

        Returns:
            list[Assignment]: Compliant week assignments
        """
        assignments = []

        # Assumes blocks are sorted by date and time
        # Mon-Thu AM: Clinic
        for i in [0, 2, 4, 6]:  # AM blocks for Mon-Thu
            assignment = AssignmentFactory.create_assignment(
                db, person=resident, block=blocks[i], rotation_template=clinic_template
            )
            assignments.append(assignment)

        # Fri AM: Conference
        assignment = AssignmentFactory.create_assignment(
            db, person=resident, block=blocks[8], rotation_template=conference_template
        )
        assignments.append(assignment)

        # PM and weekend blocks are unassigned (time off)

        return assignments
