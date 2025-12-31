"""Factory for creating ACGME compliance test scenarios."""

from datetime import date, timedelta
from typing import Optional

from faker import Faker
from sqlalchemy.orm import Session

from app.models.assignment import Assignment
from app.models.block import Block
from app.models.person import Person
from app.models.rotation_template import RotationTemplate
from tests.factories.assignment_factory import AssignmentFactory
from tests.factories.block_factory import BlockFactory
from tests.factories.person_factory import PersonFactory
from tests.factories.rotation_factory import RotationFactory

fake = Faker()


class ComplianceFactory:
    """Factory for creating ACGME compliance test scenarios."""

    @staticmethod
    def create_80_hour_violation(
        db: Session,
        resident: Optional[Person] = None,
        start_date: Optional[date] = None,
    ) -> dict:
        """
        Create a schedule that violates the 80-hour work week rule.

        Assigns resident to >80 hours in a single week (>40 half-day blocks).

        Args:
            db: Database session
            resident: Resident to over-schedule (created if None)
            start_date: Week start date (today if not provided)

        Returns:
            dict: Violation scenario data
        """
        if resident is None:
            resident = PersonFactory.create_resident(db, pgy_level=2)

        if start_date is None:
            start_date = date.today()

        # Create one week of blocks (14 blocks = 7 days × AM/PM)
        blocks = BlockFactory.create_week_blocks(db, start_date=start_date)

        # Create clinic template (2 hours per half-day = 4 hours per day)
        clinic_template = RotationFactory.create_clinic_template(db)

        # Assign to ALL 14 blocks = 14 half-days = 7 full days × 12 hours/day = 84 hours
        # This violates the 80-hour rule
        assignments = []
        for block in blocks:
            assignment = AssignmentFactory.create_primary_assignment(
                db, person=resident, block=block, rotation_template=clinic_template
            )
            assignments.append(assignment)

        return {
            "resident": resident,
            "blocks": blocks,
            "template": clinic_template,
            "assignments": assignments,
            "violation_type": "80_hour_rule",
            "estimated_hours": 84,  # 14 half-days × 6 hours avg
        }

    @staticmethod
    def create_1_in_7_violation(
        db: Session,
        resident: Optional[Person] = None,
        start_date: Optional[date] = None,
    ) -> dict:
        """
        Create a schedule that violates the 1-in-7 rule (no 24-hour rest period).

        Assigns resident to all 14 days without a day off.

        Args:
            db: Database session
            resident: Resident to schedule (created if None)
            start_date: Period start date

        Returns:
            dict: Violation scenario data
        """
        if resident is None:
            resident = PersonFactory.create_resident(db, pgy_level=1)

        if start_date is None:
            start_date = date.today()

        # Create 14 days of blocks (no breaks)
        blocks = BlockFactory.create_block_period(db, start_date=start_date, days=14)

        # Create clinic template
        clinic_template = RotationFactory.create_clinic_template(db)

        # Assign to every single day (no 24-hour rest period)
        assignments = []
        for block in blocks:
            assignment = AssignmentFactory.create_primary_assignment(
                db, person=resident, block=block, rotation_template=clinic_template
            )
            assignments.append(assignment)

        return {
            "resident": resident,
            "blocks": blocks,
            "template": clinic_template,
            "assignments": assignments,
            "violation_type": "1_in_7_rule",
            "days_without_rest": 14,
        }

    @staticmethod
    def create_supervision_ratio_violation(
        db: Session,
        pgy_level: int = 1,
        num_residents: int = 10,
        num_faculty: int = 1,
    ) -> dict:
        """
        Create a schedule that violates supervision ratios.

        PGY-1: Max 1:2 (1 faculty per 2 residents)
        PGY-2/3: Max 1:4 (1 faculty per 4 residents)

        Args:
            db: Database session
            pgy_level: PGY level (1, 2, or 3)
            num_residents: Number of residents (should exceed ratio)
            num_faculty: Number of faculty (should be insufficient)

        Returns:
            dict: Violation scenario data
        """
        # Create residents of same PGY level
        residents = []
        for _ in range(num_residents):
            resident = PersonFactory.create_resident(db, pgy_level=pgy_level)
            residents.append(resident)

        # Create minimal faculty
        faculty = []
        for _ in range(num_faculty):
            fac = PersonFactory.create_faculty(db)
            faculty.append(fac)

        # Create single clinic session (one block)
        block = BlockFactory.create_block(db)

        # Create clinic template with supervision required
        clinic_template = RotationFactory.create_clinic_template(
            db, max_residents=num_residents
        )

        # Assign all residents to the block
        assignments = []
        for resident in residents:
            assignment = AssignmentFactory.create_primary_assignment(
                db, person=resident, block=block, rotation_template=clinic_template
            )
            assignments.append(assignment)

        # Assign minimal faculty (violates ratio)
        for fac in faculty:
            assignment = AssignmentFactory.create_supervising_assignment(
                db, person=fac, block=block, rotation_template=clinic_template
            )
            assignments.append(assignment)

        max_ratio = 2 if pgy_level == 1 else 4
        actual_ratio = num_residents / num_faculty if num_faculty > 0 else float("inf")

        return {
            "residents": residents,
            "faculty": faculty,
            "block": block,
            "template": clinic_template,
            "assignments": assignments,
            "violation_type": "supervision_ratio",
            "pgy_level": pgy_level,
            "max_ratio": max_ratio,
            "actual_ratio": actual_ratio,
        }

    @staticmethod
    def create_double_booked_violation(
        db: Session,
        resident: Optional[Person] = None,
    ) -> dict:
        """
        Create a double-booking violation (same person, same block, different rotations).

        Args:
            db: Database session
            resident: Resident to double-book (created if None)

        Returns:
            dict: Violation scenario data
        """
        if resident is None:
            resident = PersonFactory.create_resident(db, pgy_level=2)

        # Create single block
        block = BlockFactory.create_block(db)

        # Create two different rotation templates
        clinic_template = RotationFactory.create_clinic_template(db)
        procedure_template = RotationFactory.create_procedure_template(db)

        # Try to create double-booked assignments
        # NOTE: This will violate unique_person_per_block constraint
        assignments = AssignmentFactory.create_double_booked_assignment(
            db, person=resident, block=block, rotation_templates=[clinic_template, procedure_template]
        )

        return {
            "resident": resident,
            "block": block,
            "templates": [clinic_template, procedure_template],
            "assignments": assignments,
            "violation_type": "double_booking",
        }

    @staticmethod
    def create_unsupervised_pgy1_violation(
        db: Session,
    ) -> dict:
        """
        Create scenario where PGY-1 residents are not supervised.

        Args:
            db: Database session

        Returns:
            dict: Violation scenario data
        """
        # Create PGY-1 residents
        residents = PersonFactory.create_batch_residents(
            db, count=3, pgy_distribution={1: 3}
        )

        # Create block
        block = BlockFactory.create_block(db)

        # Create clinic template requiring supervision
        clinic_template = RotationFactory.create_clinic_template(db, pgy_level=1)

        # Assign residents WITHOUT faculty supervisor
        assignments = []
        for resident in residents:
            assignment = AssignmentFactory.create_primary_assignment(
                db, person=resident, block=block, rotation_template=clinic_template
            )
            assignments.append(assignment)

        return {
            "residents": residents,
            "block": block,
            "template": clinic_template,
            "assignments": assignments,
            "violation_type": "unsupervised_pgy1",
        }

    @staticmethod
    def create_capacity_violation(
        db: Session,
        max_residents: int = 4,
        actual_residents: int = 8,
    ) -> dict:
        """
        Create scenario exceeding rotation capacity limit.

        Args:
            db: Database session
            max_residents: Maximum residents allowed
            actual_residents: Actual residents assigned (should exceed max)

        Returns:
            dict: Violation scenario data
        """
        # Create residents
        residents = PersonFactory.create_batch_residents(db, count=actual_residents)

        # Create block
        block = BlockFactory.create_block(db)

        # Create clinic template with capacity limit
        clinic_template = RotationFactory.create_clinic_template(
            db, max_residents=max_residents
        )

        # Assign all residents (exceeds capacity)
        assignments = []
        for resident in residents:
            assignment = AssignmentFactory.create_primary_assignment(
                db, person=resident, block=block, rotation_template=clinic_template
            )
            assignments.append(assignment)

        return {
            "residents": residents,
            "block": block,
            "template": clinic_template,
            "assignments": assignments,
            "violation_type": "capacity_exceeded",
            "max_capacity": max_residents,
            "actual_assigned": actual_residents,
        }

    @staticmethod
    def create_missing_specialty_violation(
        db: Session,
    ) -> dict:
        """
        Create scenario where rotation requires specialty but supervising faculty lacks it.

        Args:
            db: Database session

        Returns:
            dict: Violation scenario data
        """
        # Create resident
        resident = PersonFactory.create_resident(db, pgy_level=2)

        # Create faculty WITHOUT Sports Medicine specialty
        faculty = PersonFactory.create_faculty(
            db, specialties=["Primary Care", "Pediatrics"]
        )

        # Create block
        block = BlockFactory.create_block(db)

        # Create Sports Medicine template (requires specialty)
        sm_template = RotationFactory.create_sports_medicine_template(db)

        # Assign resident and non-SM faculty
        resident_assignment = AssignmentFactory.create_primary_assignment(
            db, person=resident, block=block, rotation_template=sm_template
        )

        faculty_assignment = AssignmentFactory.create_supervising_assignment(
            db, person=faculty, block=block, rotation_template=sm_template
        )

        return {
            "resident": resident,
            "faculty": faculty,
            "block": block,
            "template": sm_template,
            "assignments": [resident_assignment, faculty_assignment],
            "violation_type": "missing_specialty",
            "required_specialty": "Sports Medicine",
            "faculty_specialties": faculty.specialties,
        }

    @staticmethod
    def create_consecutive_weeks_violation(
        db: Session,
        resident: Optional[Person] = None,
        num_weeks: int = 5,
    ) -> dict:
        """
        Create scenario with excessive consecutive work weeks (no breaks).

        ACGME recommends periodic breaks; 5+ consecutive weeks can trigger burnout.

        Args:
            db: Database session
            resident: Resident to schedule (created if None)
            num_weeks: Number of consecutive weeks (default 5)

        Returns:
            dict: Violation scenario data
        """
        if resident is None:
            resident = PersonFactory.create_resident(db, pgy_level=3)

        # Create blocks for consecutive weeks
        blocks = BlockFactory.create_block_period(db, days=num_weeks * 7)

        # Create clinic template
        clinic_template = RotationFactory.create_clinic_template(db)

        # Assign to every weekday (Mon-Fri, skip weekends)
        assignments = []
        for block in blocks:
            if not block.is_weekend:
                assignment = AssignmentFactory.create_primary_assignment(
                    db, person=resident, block=block, rotation_template=clinic_template
                )
                assignments.append(assignment)

        return {
            "resident": resident,
            "blocks": blocks,
            "template": clinic_template,
            "assignments": assignments,
            "violation_type": "consecutive_weeks_no_break",
            "num_weeks": num_weeks,
        }

    @staticmethod
    def create_all_violation_types(db: Session) -> dict:
        """
        Create examples of all ACGME violation types.

        Useful for comprehensive compliance testing.

        Args:
            db: Database session

        Returns:
            dict: Dictionary mapping violation type -> violation scenario
        """
        violations = {}

        violations["80_hour"] = ComplianceFactory.create_80_hour_violation(db)
        violations["1_in_7"] = ComplianceFactory.create_1_in_7_violation(db)
        violations["supervision_ratio_pgy1"] = (
            ComplianceFactory.create_supervision_ratio_violation(
                db, pgy_level=1, num_residents=10, num_faculty=1
            )
        )
        violations["supervision_ratio_pgy2"] = (
            ComplianceFactory.create_supervision_ratio_violation(
                db, pgy_level=2, num_residents=10, num_faculty=1
            )
        )
        violations["unsupervised_pgy1"] = (
            ComplianceFactory.create_unsupervised_pgy1_violation(db)
        )
        violations["capacity"] = ComplianceFactory.create_capacity_violation(db)
        violations["missing_specialty"] = (
            ComplianceFactory.create_missing_specialty_violation(db)
        )
        violations["consecutive_weeks"] = (
            ComplianceFactory.create_consecutive_weeks_violation(db)
        )

        return violations
