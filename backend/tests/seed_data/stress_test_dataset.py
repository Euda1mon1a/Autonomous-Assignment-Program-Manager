"""Stress test seed dataset for performance and load testing."""

from datetime import date

from sqlalchemy.orm import Session

from tests.factories.credential_factory import CredentialFactory
from tests.factories.leave_factory import LeaveFactory
from tests.factories.person_factory import PersonFactory
from tests.factories.schedule_factory import ScheduleFactory
from tests.factories.swap_factory import SwapFactory


class StressTestDataset:
    """
    Large-scale dataset for stress testing and performance benchmarking.

    Includes:
    - Large numbers of residents, faculty, blocks, and assignments
    - Tests database performance under load
    - Tests scheduler algorithm with realistic constraints
    """

    @staticmethod
    def seed_large_program(db: Session, num_residents: int = 50) -> dict:
        """
        Seed database with large residency program.

        Args:
            db: Database session
            num_residents: Number of residents (default 50)

        Returns:
            dict: Dictionary with all seeded entities
        """
        # Calculate proportional faculty (1 faculty per 10 residents)
        num_faculty = max(5, num_residents // 10)

        # Create people
        residents = PersonFactory.create_batch_residents(db, count=num_residents)
        faculty = PersonFactory.create_batch_faculty(
            db, count=num_faculty, include_leadership=True
        )

        # Create one month of blocks (for performance testing)
        schedule = ScheduleFactory.create_complete_schedule(
            db,
            num_residents=num_residents,
            num_faculty=num_faculty,
            num_days=28,
            include_absences=True,
            include_certifications=True,
        )

        return {
            **schedule,
            "dataset_type": "stress_test_large_program",
            "num_residents": num_residents,
            "num_faculty": num_faculty,
        }

    @staticmethod
    def seed_massive_assignment_load(
        db: Session, num_residents: int = 100, num_days: int = 7
    ) -> dict:
        """
        Seed database with massive assignment load.

        Creates large number of assignments to test database performance.

        Args:
            db: Database session
            num_residents: Number of residents (default 100)
            num_days: Number of days to schedule (default 7 to keep manageable)

        Returns:
            dict: Dictionary with all seeded entities
        """
        from tests.factories.block_factory import BlockFactory
        from tests.factories.rotation_factory import RotationFactory
        from tests.factories.assignment_factory import AssignmentFactory

        # Create large cohort
        residents = PersonFactory.create_batch_residents(db, count=num_residents)
        faculty = PersonFactory.create_batch_faculty(
            db, count=num_residents // 10, include_leadership=False
        )

        # Create blocks
        blocks = BlockFactory.create_block_period(db, days=num_days)

        # Create templates
        templates = RotationFactory.create_standard_template_set(db)
        clinic_template = templates["pgy1_clinic"]

        # Create massive number of assignments
        # Total assignments = num_residents × num_days × 2 (AM/PM)
        assignments = []
        for resident in residents:
            for block in blocks:
                assignment = AssignmentFactory.create_primary_assignment(
                    db, person=resident, block=block, rotation_template=clinic_template
                )
                assignments.append(assignment)

        total_assignments = len(assignments)

        return {
            "residents": residents,
            "faculty": faculty,
            "blocks": blocks,
            "templates": templates,
            "assignments": assignments,
            "dataset_type": "stress_test_massive_assignments",
            "total_assignments": total_assignments,
            "expected_assignments": num_residents * num_days * 2,
        }

    @staticmethod
    def seed_swap_flood(
        db: Session, num_faculty: int = 50, num_swaps: int = 500
    ) -> dict:
        """
        Seed database with large number of swap requests.

        Tests swap processing performance.

        Args:
            db: Database session
            num_faculty: Number of faculty (default 50)
            num_swaps: Number of swap requests (default 500)

        Returns:
            dict: Dictionary with all seeded entities
        """
        # Create faculty
        faculty = PersonFactory.create_batch_faculty(
            db, count=num_faculty, include_leadership=False
        )

        # Create massive number of swaps
        swaps = SwapFactory.create_batch_swaps(
            db, faculty=faculty, num_swaps=num_swaps, swap_type=None
        )

        return {
            "faculty": faculty,
            "swaps": swaps,
            "dataset_type": "stress_test_swap_flood",
            "num_faculty": num_faculty,
            "num_swaps": len(swaps),
        }

    @staticmethod
    def seed_absence_storm(
        db: Session, num_residents: int = 100, absences_per_person: int = 10
    ) -> dict:
        """
        Seed database with large number of absences.

        Tests absence processing and conflict detection performance.

        Args:
            db: Database session
            num_residents: Number of residents (default 100)
            absences_per_person: Absences per person (default 10)

        Returns:
            dict: Dictionary with all seeded entities
        """
        # Create residents
        residents = PersonFactory.create_batch_residents(db, count=num_residents)

        # Create many absences
        absences = LeaveFactory.create_batch_absences(
            db, persons=residents, count_per_person=absences_per_person
        )

        total_absences = len(absences)

        return {
            "residents": residents,
            "absences": absences,
            "dataset_type": "stress_test_absence_storm",
            "num_residents": num_residents,
            "total_absences": total_absences,
            "expected_absences": num_residents * absences_per_person,
        }

    @staticmethod
    def seed_certification_flood(
        db: Session, num_people: int = 200, certs_per_person: int = 6
    ) -> dict:
        """
        Seed database with large number of certifications.

        Tests certification tracking and expiration monitoring performance.

        Args:
            db: Database session
            num_people: Number of people (default 200)
            certs_per_person: Certifications per person (default 6)

        Returns:
            dict: Dictionary with all seeded entities
        """
        # Create mixed population
        residents = PersonFactory.create_batch_residents(db, count=num_people // 2)
        faculty = PersonFactory.create_batch_faculty(
            db, count=num_people // 2, include_leadership=False
        )
        all_people = residents + faculty

        # Create certification types
        cert_types = CredentialFactory.create_standard_certification_types(db)

        # Create many certifications
        all_certifications = []
        for person in all_people:
            for cert_type in list(cert_types.values())[:certs_per_person]:
                cert = CredentialFactory.create_person_certification(
                    db, person=person, certification_type=cert_type
                )
                all_certifications.append(cert)

        return {
            "residents": residents,
            "faculty": faculty,
            "certification_types": cert_types,
            "certifications": all_certifications,
            "dataset_type": "stress_test_certification_flood",
            "total_certifications": len(all_certifications),
            "expected_certifications": num_people * certs_per_person,
        }

    @staticmethod
    def seed_full_stress_test(
        db: Session,
        num_residents: int = 100,
        num_faculty: int = 20,
        num_days: int = 28,
    ) -> dict:
        """
        Seed database with comprehensive stress test data.

        Combines all stress test scenarios into one massive dataset.

        Args:
            db: Database session
            num_residents: Number of residents (default 100)
            num_faculty: Number of faculty (default 20)
            num_days: Number of days (default 28)

        Returns:
            dict: Dictionary with all seeded entities
        """
        # Create comprehensive schedule
        schedule = ScheduleFactory.create_complete_schedule(
            db,
            num_residents=num_residents,
            num_faculty=num_faculty,
            num_days=num_days,
            include_absences=True,
            include_certifications=True,
        )

        # Add extra swaps
        swaps = SwapFactory.create_batch_swaps(
            db, faculty=schedule["faculty"], num_swaps=100
        )

        # Add extra absences
        extra_absences = LeaveFactory.create_batch_absences(
            db, persons=schedule["residents"], count_per_person=5
        )

        return {
            **schedule,
            "extra_swaps": swaps,
            "extra_absences": extra_absences,
            "dataset_type": "stress_test_full",
            "total_swaps": len(swaps),
            "total_absences": len(schedule.get("absences", [])) + len(extra_absences),
            "total_assignments": len(schedule["assignments"]),
        }

    @staticmethod
    def seed_academic_year_full_assignments(
        db: Session, year: int | None = None
    ) -> dict:
        """
        Seed database with full academic year INCLUDING all assignments.

        WARNING: This creates ~730 blocks × 10 residents = 7,300+ assignments.
        Use only for true load testing.

        Args:
            db: Database session
            year: Academic year starting year

        Returns:
            dict: Dictionary with all seeded entities
        """
        from tests.factories.block_factory import BlockFactory
        from tests.factories.rotation_factory import RotationFactory
        from tests.factories.assignment_factory import AssignmentFactory

        if year is None:
            year = date.today().year

        # Create skeleton
        skeleton = ScheduleFactory.create_academic_year_skeleton(
            db, year=year, num_residents=10, num_faculty=5
        )

        # Create assignments for ENTIRE YEAR (heavy load)
        clinic_template = skeleton["templates"]["pgy1_clinic"]
        assignments = []

        print(
            f"Creating {len(skeleton['residents'])} × {len(skeleton['blocks'])} = "
            f"{len(skeleton['residents']) * len(skeleton['blocks'])} assignments..."
        )

        for resident in skeleton["residents"]:
            for block in skeleton["blocks"]:
                assignment = AssignmentFactory.create_primary_assignment(
                    db, person=resident, block=block, rotation_template=clinic_template
                )
                assignments.append(assignment)

        print(f"Created {len(assignments)} assignments")

        return {
            **skeleton,
            "assignments": assignments,
            "dataset_type": "stress_test_full_year_assignments",
            "total_assignments": len(assignments),
        }
