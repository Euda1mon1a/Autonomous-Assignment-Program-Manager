"""Minimal seed dataset for fast unit testing."""

from datetime import date, timedelta

from sqlalchemy.orm import Session

from tests.factories.credential_factory import CredentialFactory
from tests.factories.schedule_factory import ScheduleFactory


class MinimalDataset:
    """
    Minimal viable dataset for unit tests.

    Includes:
    - 1 resident (PGY-1)
    - 1 faculty
    - 1 week of blocks (14 blocks)
    - 1 rotation template (clinic)
    - Assignments for the resident
    - Standard certifications
    """

    @staticmethod
    def seed(db: Session) -> dict:
        """
        Seed database with minimal dataset.

        Args:
            db: Database session

        Returns:
            dict: Dictionary with all seeded entities
        """
        # Create minimal schedule
        schedule = ScheduleFactory.create_minimal_schedule(db)

        # Add certifications
        cert_types = CredentialFactory.create_standard_certification_types(db)
        certifications = CredentialFactory.certify_person_all_standard(
            db, person=schedule["resident"], certification_types=cert_types
        )

        return {
            "resident": schedule["resident"],
            "faculty": schedule["faculty"],
            "blocks": schedule["blocks"],
            "template": schedule["template"],
            "assignments": schedule["assignments"],
            "certification_types": cert_types,
            "certifications": certifications,
            "dataset_type": "minimal",
        }

    @staticmethod
    def seed_multiple_residents(db: Session, num_residents: int = 3) -> dict:
        """
        Seed database with minimal dataset but multiple residents.

        Args:
            db: Database session
            num_residents: Number of residents to create

        Returns:
            dict: Dictionary with all seeded entities
        """
        from tests.factories.person_factory import PersonFactory
        from tests.factories.block_factory import BlockFactory
        from tests.factories.rotation_factory import RotationFactory
        from tests.factories.assignment_factory import AssignmentFactory

        # Create people
        residents = PersonFactory.create_batch_residents(db, count=num_residents)
        faculty = PersonFactory.create_faculty(db)

        # Create one week of blocks
        blocks = BlockFactory.create_week_blocks(db)

        # Create clinic template
        clinic_template = RotationFactory.create_clinic_template(db)

        # Create assignments for each resident
        assignments = []
        for resident in residents:
            resident_assignments = AssignmentFactory.create_week_assignments(
                db, person=resident, blocks=blocks, rotation_template=clinic_template
            )
            assignments.extend(resident_assignments)

        # Add certifications for all residents
        cert_types = CredentialFactory.create_standard_certification_types(db)
        all_certifications = []
        for resident in residents:
            certs = CredentialFactory.certify_person_all_standard(
                db, person=resident, certification_types=cert_types
            )
            all_certifications.extend(certs)

        return {
            "residents": residents,
            "faculty": faculty,
            "blocks": blocks,
            "template": clinic_template,
            "assignments": assignments,
            "certification_types": cert_types,
            "certifications": all_certifications,
            "dataset_type": "minimal_multiple_residents",
        }

    @staticmethod
    def seed_with_absences(db: Session) -> dict:
        """
        Seed minimal dataset with absences included.

        Args:
            db: Database session

        Returns:
            dict: Dictionary with all seeded entities including absences
        """
        from tests.factories.leave_factory import LeaveFactory

        # Create minimal schedule
        data = MinimalDataset.seed(db)

        # Add vacation absence for resident
        absence = LeaveFactory.create_vacation(
            db,
            person=data["resident"],
            start_date=date.today() + timedelta(days=14),
            days=7,
        )

        data["absences"] = [absence]
        return data

    @staticmethod
    def seed_with_swaps(db: Session) -> dict:
        """
        Seed minimal dataset with swap data included.

        Args:
            db: Database session

        Returns:
            dict: Dictionary with all seeded entities including swaps
        """
        from tests.factories.person_factory import PersonFactory
        from tests.factories.swap_factory import SwapFactory

        # Create minimal schedule
        data = MinimalDataset.seed(db)

        # Add more faculty for swaps
        faculty2 = PersonFactory.create_faculty(db)

        # Create swap request
        swap = SwapFactory.create_one_to_one_swap(
            db,
            source_faculty=data["faculty"],
            target_faculty=faculty2,
        )

        data["swaps"] = [swap]
        data["additional_faculty"] = [faculty2]
        return data
