"""
Test data factories for generating test data.

Provides factory functions for creating test instances of all models
with random but realistic data using Faker.

Usage:
    from tests.factories import PersonFactory, AssignmentFactory

    # Create a single resident
    resident = PersonFactory.create_resident(db)

    # Create multiple faculty
    faculty = PersonFactory.create_batch_faculty(db, count=5)

    # Create a complete schedule
    schedule = ScheduleFactory.create_complete_schedule(
        db, num_residents=10, num_faculty=5, num_days=28
    )
"""

from tests.factories.assignment_factory import AssignmentFactory
from tests.factories.block_factory import BlockFactory
from tests.factories.compliance_factory import ComplianceFactory
from tests.factories.credential_factory import CredentialFactory
from tests.factories.leave_factory import LeaveFactory
from tests.factories.person_factory import PersonFactory
from tests.factories.rotation_factory import RotationFactory
from tests.factories.schedule_factory import ScheduleFactory
from tests.factories.swap_factory import SwapFactory

__all__ = [
    "PersonFactory",
    "AssignmentFactory",
    "BlockFactory",
    "RotationFactory",
    "SwapFactory",
    "CredentialFactory",
    "LeaveFactory",
    "ScheduleFactory",
    "ComplianceFactory",
]
