"""Factory for creating complete test schedules."""

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


class ScheduleFactory:
    """Factory for creating complete schedules with all related data."""

    @staticmethod
    def create_complete_schedule(
        db: Session,
        num_residents: int = 10,
        num_faculty: int = 5,
        num_days: int = 28,
        start_date: Optional[date] = None,
        include_absences: bool = False,
        include_certifications: bool = False,
    ) -> dict:
        """
        Create a complete schedule with residents, faculty, blocks, rotations, and assignments.

        Args:
            db: Database session
            num_residents: Number of residents to create
            num_faculty: Number of faculty to create
            num_days: Number of days to schedule (default 28 = one block)
            start_date: Schedule start date (today if not provided)
            include_absences: Whether to create absences
            include_certifications: Whether to create certifications

        Returns:
            dict: Dictionary containing all created entities
                {
                    "residents": list[Person],
                    "faculty": list[Person],
                    "blocks": list[Block],
                    "templates": dict[str, RotationTemplate],
                    "assignments": list[Assignment],
                    "absences": list[Absence] (if include_absences),
                    "certifications": list[PersonCertification] (if include_certifications),
                }
        """
        if start_date is None:
            start_date = date.today()

        # Create people
        residents = PersonFactory.create_batch_residents(db, count=num_residents)
        faculty = PersonFactory.create_batch_faculty(
            db, count=num_faculty, include_leadership=True
        )

        # Create blocks
        blocks = BlockFactory.create_block_period(db, start_date=start_date, days=num_days)

        # Create rotation templates
        templates = RotationFactory.create_standard_template_set(db)

        # Create assignments (simple round-robin for testing)
        assignments = []
        clinic_template = templates["pgy1_clinic"]

        for i, resident in enumerate(residents):
            # Assign each resident to a week of clinic blocks
            week_start = i % (num_days // 7)  # Cycle through weeks
            week_blocks = blocks[week_start * 14 : (week_start + 1) * 14]

            week_assignments = AssignmentFactory.create_week_assignments(
                db, person=resident, blocks=week_blocks, rotation_template=clinic_template
            )
            assignments.extend(week_assignments)

        result = {
            "residents": residents,
            "faculty": faculty,
            "blocks": blocks,
            "templates": templates,
            "assignments": assignments,
        }

        # Optionally add absences
        if include_absences:
            from tests.factories.leave_factory import LeaveFactory

            absences = LeaveFactory.create_batch_absences(
                db, persons=residents, count_per_person=1
            )
            result["absences"] = absences

        # Optionally add certifications
        if include_certifications:
            from tests.factories.credential_factory import CredentialFactory

            cert_types = CredentialFactory.create_standard_certification_types(db)
            certifications = []
            for resident in residents:
                certs = CredentialFactory.certify_person_all_standard(
                    db, person=resident, certification_types=cert_types
                )
                certifications.extend(certs)
            result["certifications"] = certifications
            result["certification_types"] = cert_types

        return result

    @staticmethod
    def create_clinic_day_schedule(
        db: Session,
        num_residents: int = 4,
        num_faculty: int = 2,
        clinic_date: Optional[date] = None,
    ) -> dict:
        """
        Create a single clinic day schedule (AM and PM sessions).

        Args:
            db: Database session
            num_residents: Number of residents per session
            num_faculty: Number of supervising faculty per session
            clinic_date: Date for clinic (today if not provided)

        Returns:
            dict: Dictionary containing created entities
        """
        if clinic_date is None:
            clinic_date = date.today()

        # Create people
        residents = PersonFactory.create_batch_residents(db, count=num_residents)
        faculty = PersonFactory.create_batch_faculty(db, count=num_faculty)

        # Create blocks for the day
        am_block, pm_block = BlockFactory.create_day_blocks(db, block_date=clinic_date)

        # Create clinic template
        clinic_template = RotationFactory.create_clinic_template(
            db, max_residents=num_residents
        )

        # Create supervised sessions
        am_assignments = AssignmentFactory.create_supervised_session(
            db,
            residents=residents,
            faculty=faculty[0],
            block=am_block,
            rotation_template=clinic_template,
        )

        pm_assignments = AssignmentFactory.create_supervised_session(
            db,
            residents=residents,
            faculty=faculty[1] if len(faculty) > 1 else faculty[0],
            block=pm_block,
            rotation_template=clinic_template,
        )

        return {
            "residents": residents,
            "faculty": faculty,
            "blocks": [am_block, pm_block],
            "templates": {"clinic": clinic_template},
            "assignments": am_assignments + pm_assignments,
        }

    @staticmethod
    def create_academic_year_skeleton(
        db: Session,
        year: Optional[int] = None,
        num_residents: int = 10,
        num_faculty: int = 5,
    ) -> dict:
        """
        Create skeleton data for a full academic year (blocks, people, templates).

        Does NOT create assignments (too many for typical test setup).
        Use this to create the foundation, then add specific assignments for testing.

        Args:
            db: Database session
            year: Academic year starting year
            num_residents: Number of residents
            num_faculty: Number of faculty

        Returns:
            dict: Dictionary with people, blocks, templates (no assignments)
        """
        if year is None:
            year = date.today().year

        # Create people
        residents = PersonFactory.create_batch_residents(
            db, count=num_residents, pgy_distribution={1: 4, 2: 3, 3: 3}
        )
        faculty = PersonFactory.create_batch_faculty(
            db, count=num_faculty, include_leadership=True
        )

        # Create all blocks for academic year
        blocks = BlockFactory.create_academic_year_blocks(db, year=year)

        # Create rotation templates
        templates = RotationFactory.create_standard_template_set(db)

        return {
            "residents": residents,
            "faculty": faculty,
            "blocks": blocks,
            "templates": templates,
            "year": year,
        }

    @staticmethod
    def create_minimal_schedule(
        db: Session,
    ) -> dict:
        """
        Create minimal viable schedule (1 resident, 1 faculty, 1 week, 1 rotation).

        Useful for focused unit tests.

        Returns:
            dict: Minimal schedule entities
        """
        # Create minimal people
        resident = PersonFactory.create_resident(db, pgy_level=1)
        faculty = PersonFactory.create_faculty(db)

        # Create one week of blocks
        blocks = BlockFactory.create_week_blocks(db)

        # Create clinic template
        clinic_template = RotationFactory.create_clinic_template(db)

        # Create assignments for resident
        assignments = AssignmentFactory.create_week_assignments(
            db, person=resident, blocks=blocks, rotation_template=clinic_template
        )

        return {
            "resident": resident,
            "faculty": faculty,
            "blocks": blocks,
            "template": clinic_template,
            "assignments": assignments,
        }

    @staticmethod
    def create_fmit_week_schedule(
        db: Session,
        num_faculty: int = 7,  # 7 faculty for 7 days
    ) -> dict:
        """
        Create FMIT (inpatient) week schedule with 24/7 coverage.

        Assigns one faculty per day for 7 days.

        Args:
            db: Database session
            num_faculty: Number of faculty (should be >= 7 for daily rotation)

        Returns:
            dict: FMIT week schedule
        """
        # Create faculty
        faculty = PersonFactory.create_batch_faculty(
            db, count=num_faculty, include_leadership=False
        )

        # Create one week of blocks
        blocks = BlockFactory.create_week_blocks(db)

        # Create FMIT template
        fmit_template = RotationFactory.create_fmit_template(db)

        # Assign one faculty per day (both AM and PM)
        assignments = []
        for day_index in range(7):
            faculty_index = day_index % len(faculty)
            day_faculty = faculty[faculty_index]

            # AM and PM blocks for this day
            am_block = blocks[day_index * 2]
            pm_block = blocks[day_index * 2 + 1]

            # Assign faculty to both blocks (24-hour coverage)
            am_assignment = AssignmentFactory.create_supervising_assignment(
                db, person=day_faculty, block=am_block, rotation_template=fmit_template
            )
            pm_assignment = AssignmentFactory.create_supervising_assignment(
                db, person=day_faculty, block=pm_block, rotation_template=fmit_template
            )

            assignments.extend([am_assignment, pm_assignment])

        return {
            "faculty": faculty,
            "blocks": blocks,
            "template": fmit_template,
            "assignments": assignments,
        }

    @staticmethod
    def create_understaffed_schedule(
        db: Session,
        num_residents: int = 8,
        num_faculty: int = 2,  # Deliberately low
        num_days: int = 7,
    ) -> dict:
        """
        Create understaffed schedule (insufficient faculty for supervision ratios).

        Useful for testing coverage gap detection.

        Args:
            db: Database session
            num_residents: Number of residents
            num_faculty: Number of faculty (should be < num_residents / 4)
            num_days: Number of days

        Returns:
            dict: Understaffed schedule
        """
        # Create people
        residents = PersonFactory.create_batch_residents(db, count=num_residents)
        faculty = PersonFactory.create_batch_faculty(
            db, count=num_faculty, include_leadership=False
        )

        # Create blocks
        blocks = BlockFactory.create_block_period(db, days=num_days)

        # Create clinic template
        clinic_template = RotationFactory.create_clinic_template(
            db, max_residents=num_residents
        )

        # Assign all residents to all blocks (oversaturated)
        assignments = []
        for resident in residents:
            for block in blocks:
                assignment = AssignmentFactory.create_primary_assignment(
                    db, person=resident, block=block, rotation_template=clinic_template
                )
                assignments.append(assignment)

        # Minimal faculty supervision (will violate ratios)
        for faculty_member in faculty:
            for block in blocks[:14]:  # Just first week
                assignment = AssignmentFactory.create_supervising_assignment(
                    db,
                    person=faculty_member,
                    block=block,
                    rotation_template=clinic_template,
                )
                assignments.append(assignment)

        return {
            "residents": residents,
            "faculty": faculty,
            "blocks": blocks,
            "template": clinic_template,
            "assignments": assignments,
        }

    @staticmethod
    def create_weekend_call_schedule(
        db: Session,
        num_faculty: int = 4,
        num_weekends: int = 4,
    ) -> dict:
        """
        Create weekend call schedule (Saturday and Sunday coverage).

        Args:
            db: Database session
            num_faculty: Number of faculty for call rotation
            num_weekends: Number of weekends to schedule

        Returns:
            dict: Weekend call schedule
        """
        # Create faculty
        faculty = PersonFactory.create_batch_faculty(
            db, count=num_faculty, include_leadership=False
        )

        # Create weekend blocks
        blocks = BlockFactory.create_weekend_blocks(db, num_weekends=num_weekends)

        # Create call template
        call_template = RotationFactory.create_rotation_template(
            db,
            name="Weekend Call",
            activity_type="inpatient",
            abbreviation="CALL",
            leave_eligible=False,
        )

        # Rotate faculty through weekends
        assignments = []
        for weekend_index in range(num_weekends):
            faculty_index = weekend_index % len(faculty)
            weekend_faculty = faculty[faculty_index]

            # 4 blocks per weekend (Sat AM/PM, Sun AM/PM)
            weekend_blocks = blocks[weekend_index * 4 : (weekend_index + 1) * 4]

            for block in weekend_blocks:
                assignment = AssignmentFactory.create_supervising_assignment(
                    db,
                    person=weekend_faculty,
                    block=block,
                    rotation_template=call_template,
                )
                assignments.append(assignment)

        return {
            "faculty": faculty,
            "blocks": blocks,
            "template": call_template,
            "assignments": assignments,
        }
