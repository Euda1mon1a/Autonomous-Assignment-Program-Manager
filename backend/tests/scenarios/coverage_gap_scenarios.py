"""Coverage gap and understaffing test scenarios."""

from datetime import date, timedelta
from typing import Optional

from sqlalchemy.orm import Session

from tests.factories.leave_factory import LeaveFactory
from tests.factories.person_factory import PersonFactory
from tests.factories.schedule_factory import ScheduleFactory


class CoverageGapScenarios:
    """Pre-built scenarios for coverage gap and understaffing testing."""

    @staticmethod
    def create_understaffed_clinic(db: Session) -> dict:
        """
        Create understaffed clinic scenario.

        Too many residents, not enough supervising faculty.
        """
        return ScheduleFactory.create_understaffed_schedule(
            db, num_residents=12, num_faculty=2, num_days=7
        )

    @staticmethod
    def create_overlapping_absences(
        db: Session, num_absences: int = 4
    ) -> dict:
        """
        Create scenario with multiple overlapping absences.

        Multiple residents absent during same time period.
        """
        # Create residents
        residents = PersonFactory.create_batch_residents(db, count=num_absences + 2)

        # Create schedule
        schedule = ScheduleFactory.create_complete_schedule(
            db, num_residents=len(residents), num_faculty=3, num_days=7
        )

        # Create overlapping absences for first N residents
        start_date = date.today() + timedelta(days=1)
        absences = LeaveFactory.create_overlapping_absences(
            db, persons=residents[:num_absences], start_date=start_date, days=5
        )

        schedule["absences"] = absences
        return schedule

    @staticmethod
    def create_weekend_gap(db: Session) -> dict:
        """
        Create weekend coverage gap scenario.

        Not enough faculty for weekend call coverage.
        """
        # Create minimal faculty (insufficient for 4 weekends)
        return ScheduleFactory.create_weekend_call_schedule(
            db, num_faculty=2, num_weekends=4
        )

    @staticmethod
    def create_deployment_coverage_gap(db: Session) -> dict:
        """
        Create coverage gap from military deployment.

        Key faculty member deployed, leaving coverage gap.
        """
        # Create schedule with faculty
        schedule = ScheduleFactory.create_complete_schedule(
            db, num_residents=8, num_faculty=4, num_days=28
        )

        # Deploy one faculty member
        deployed_faculty = schedule["faculty"][0]
        deployment = LeaveFactory.create_deployment(
            db,
            person=deployed_faculty,
            days=90,
            deployment_location="OCONUS",
        )

        schedule["deployment"] = deployment
        return schedule

    @staticmethod
    def create_flu_season_gap(db: Session) -> dict:
        """
        Create coverage gap from multiple sick residents (flu season).

        Multiple residents out sick simultaneously.
        """
        # Create schedule
        schedule = ScheduleFactory.create_complete_schedule(
            db, num_residents=10, num_faculty=4, num_days=7
        )

        # Create sick leave for 3 residents (same week)
        absences = []
        for resident in schedule["residents"][:3]:
            absence = LeaveFactory.create_medical_leave(
                db, person=resident, days=3  # Short but simultaneous
            )
            absences.append(absence)

        schedule["sick_absences"] = absences
        return schedule

    @staticmethod
    def create_fmit_understaffing(db: Session) -> dict:
        """
        Create FMIT understaffing scenario.

        Not enough faculty for 24/7 inpatient coverage.
        """
        return ScheduleFactory.create_fmit_week_schedule(
            db, num_faculty=4  # Need 7 for daily rotation
        )

    @staticmethod
    def create_specialty_shortage(db: Session) -> dict:
        """
        Create specialty shortage scenario.

        Need Sports Medicine faculty but none available.
        """
        from tests.factories.block_factory import BlockFactory
        from tests.factories.rotation_factory import RotationFactory
        from tests.factories.assignment_factory import AssignmentFactory

        # Create residents and non-SM faculty
        residents = PersonFactory.create_batch_residents(db, count=3)
        faculty = PersonFactory.create_batch_faculty(
            db, count=2, include_leadership=False
        )

        # Create blocks
        blocks = BlockFactory.create_week_blocks(db)

        # Create SM clinic template (requires SM specialty)
        sm_template = RotationFactory.create_sports_medicine_template(db)

        # Try to assign residents without SM faculty
        assignments = []
        for resident in residents:
            assignment = AssignmentFactory.create_primary_assignment(
                db, person=resident, block=blocks[0], rotation_template=sm_template
            )
            assignments.append(assignment)

        return {
            "residents": residents,
            "faculty": faculty,
            "blocks": blocks,
            "template": sm_template,
            "assignments": assignments,
            "gap_type": "specialty_shortage",
        }

    @staticmethod
    def create_holiday_coverage_gap(db: Session) -> dict:
        """
        Create holiday coverage gap scenario.

        Major holiday with insufficient coverage volunteers.
        """
        from tests.factories.block_factory import BlockFactory

        # Create faculty
        faculty = PersonFactory.create_batch_faculty(db, count=3)

        # Create holiday blocks (Christmas week)
        year = date.today().year
        blocks = BlockFactory.create_holiday_blocks(db, year=year)

        # No assignments created = coverage gap
        return {
            "faculty": faculty,
            "blocks": blocks,
            "gap_type": "holiday_coverage",
        }

    @staticmethod
    def create_n_minus_1_failure(db: Session) -> dict:
        """
        Create N-1 resilience failure scenario.

        System cannot handle loss of 1 person.
        """
        # Create minimal staffing (exactly what's needed, no buffer)
        schedule = ScheduleFactory.create_complete_schedule(
            db, num_residents=4, num_faculty=1, num_days=7  # Minimal faculty
        )

        # Remove one resident (emergency absence)
        emergency_resident = schedule["residents"][0]
        emergency = LeaveFactory.create_family_emergency(
            db, person=emergency_resident, return_date_known=False
        )

        schedule["emergency_absence"] = emergency
        schedule["gap_type"] = "n_minus_1_failure"
        return schedule

    @staticmethod
    def create_maternity_leave_gap(db: Session) -> dict:
        """
        Create coverage gap from maternity leave.

        Resident on 12-week maternity leave.
        """
        schedule = ScheduleFactory.create_complete_schedule(
            db, num_residents=6, num_faculty=3, num_days=84  # 12 weeks
        )

        # Create maternity leave for one resident
        maternity_resident = schedule["residents"][0]
        maternity = LeaveFactory.create_maternity_paternity_leave(
            db, person=maternity_resident, days=84
        )

        schedule["maternity_leave"] = maternity
        return schedule
