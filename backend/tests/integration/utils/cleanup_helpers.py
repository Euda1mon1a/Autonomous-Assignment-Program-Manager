"""
Cleanup helpers for integration tests.

Provides utilities for cleaning up test data.
"""

from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.absence import Absence
from app.models.assignment import Assignment
from app.models.block import Block
from app.models.person import Person
from app.models.rotation_template import RotationTemplate
from app.models.user import User


def cleanup_assignments(db: Session, assignment_ids: list[str] | None = None) -> None:
    """
    Clean up test assignments.

    Args:
        db: Database session
        assignment_ids: Optional list of specific assignment IDs to delete.
                       If None, deletes all assignments.
    """
    if assignment_ids:
        db.query(Assignment).filter(Assignment.id.in_(assignment_ids)).delete(
            synchronize_session=False
        )
    else:
        db.query(Assignment).delete()
    db.commit()


def cleanup_blocks(db: Session, block_ids: list[str] | None = None) -> None:
    """
    Clean up test blocks.

    Args:
        db: Database session
        block_ids: Optional list of specific block IDs to delete.
                  If None, deletes all blocks.
    """
    if block_ids:
        db.query(Block).filter(Block.id.in_(block_ids)).delete(
            synchronize_session=False
        )
    else:
        db.query(Block).delete()
    db.commit()


def cleanup_people(db: Session, person_ids: list[str] | None = None) -> None:
    """
    Clean up test people.

    Args:
        db: Database session
        person_ids: Optional list of specific person IDs to delete.
                   If None, deletes all people.
    """
    if person_ids:
        db.query(Person).filter(Person.id.in_(person_ids)).delete(
            synchronize_session=False
        )
    else:
        db.query(Person).delete()
    db.commit()


def cleanup_rotation_templates(
    db: Session, template_ids: list[str] | None = None
) -> None:
    """
    Clean up test rotation templates.

    Args:
        db: Database session
        template_ids: Optional list of specific template IDs to delete.
                     If None, deletes all templates.
    """
    if template_ids:
        db.query(RotationTemplate).filter(RotationTemplate.id.in_(template_ids)).delete(
            synchronize_session=False
        )
    else:
        db.query(RotationTemplate).delete()
    db.commit()


def cleanup_absences(db: Session, absence_ids: list[str] | None = None) -> None:
    """
    Clean up test absences.

    Args:
        db: Database session
        absence_ids: Optional list of specific absence IDs to delete.
                    If None, deletes all absences.
    """
    if absence_ids:
        db.query(Absence).filter(Absence.id.in_(absence_ids)).delete(
            synchronize_session=False
        )
    else:
        db.query(Absence).delete()
    db.commit()


def cleanup_users(db: Session, user_ids: list[str] | None = None) -> None:
    """
    Clean up test users.

    Args:
        db: Database session
        user_ids: Optional list of specific user IDs to delete.
                 If None, deletes all users.
    """
    if user_ids:
        db.query(User).filter(User.id.in_(user_ids)).delete(synchronize_session=False)
    else:
        db.query(User).delete()
    db.commit()


def cleanup_all_test_data(db: Session) -> None:
    """
    Clean up all test data from database.

    Deletes in correct order to respect foreign key constraints.

    Args:
        db: Database session
    """
    # Delete in order to respect foreign keys
    cleanup_assignments(db)
    cleanup_absences(db)
    cleanup_blocks(db)
    cleanup_people(db)
    cleanup_rotation_templates(db)
    cleanup_users(db)


class TestDataCleanup:
    """
    Context manager for automatic test data cleanup.

    Usage:
        with TestDataCleanup(db) as cleanup:
            # Create test data
            person = create_test_person(db)
            cleanup.add_person(person.id)

            # Test data automatically cleaned up on exit
    """

    def __init__(self, db: Session):
        """
        Initialize cleanup manager.

        Args:
            db: Database session
        """
        self.db = db
        self.assignment_ids = []
        self.block_ids = []
        self.person_ids = []
        self.template_ids = []
        self.absence_ids = []
        self.user_ids = []

    def add_assignment(self, assignment_id: str) -> None:
        """Track assignment for cleanup."""
        self.assignment_ids.append(assignment_id)

    def add_block(self, block_id: str) -> None:
        """Track block for cleanup."""
        self.block_ids.append(block_id)

    def add_person(self, person_id: str) -> None:
        """Track person for cleanup."""
        self.person_ids.append(person_id)

    def add_template(self, template_id: str) -> None:
        """Track template for cleanup."""
        self.template_ids.append(template_id)

    def add_absence(self, absence_id: str) -> None:
        """Track absence for cleanup."""
        self.absence_ids.append(absence_id)

    def add_user(self, user_id: str) -> None:
        """Track user for cleanup."""
        self.user_ids.append(user_id)

    def cleanup(self) -> None:
        """Perform cleanup of tracked entities."""
        if self.assignment_ids:
            cleanup_assignments(self.db, self.assignment_ids)
        if self.absence_ids:
            cleanup_absences(self.db, self.absence_ids)
        if self.block_ids:
            cleanup_blocks(self.db, self.block_ids)
        if self.person_ids:
            cleanup_people(self.db, self.person_ids)
        if self.template_ids:
            cleanup_rotation_templates(self.db, self.template_ids)
        if self.user_ids:
            cleanup_users(self.db, self.user_ids)

    def __enter__(self):
        """Enter context."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context and cleanup."""
        self.cleanup()
