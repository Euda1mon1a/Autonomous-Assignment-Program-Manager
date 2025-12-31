"""Emergency coverage and crisis response test scenarios."""

from datetime import date, timedelta

from sqlalchemy.orm import Session

from tests.factories.leave_factory import LeaveFactory
from tests.factories.person_factory import PersonFactory
from tests.factories.schedule_factory import ScheduleFactory


class EmergencyScenarios:
    """Pre-built scenarios for emergency coverage testing."""

    @staticmethod
    def create_sudden_deployment(db: Session) -> dict:
        """
        Create sudden military deployment emergency.

        Faculty receives deployment orders with 48-hour notice.
        """
        # Create schedule with faculty
        schedule = ScheduleFactory.create_complete_schedule(
            db, num_residents=8, num_faculty=4, num_days=28
        )

        # Sudden deployment (starts in 2 days)
        deployed_faculty = schedule["faculty"][0]
        deployment = LeaveFactory.create_deployment(
            db,
            person=deployed_faculty,
            start_date=date.today() + timedelta(days=2),
            days=180,
            deployment_location="CLASSIFIED",
        )

        schedule["emergency_deployment"] = deployment
        schedule["emergency_type"] = "sudden_deployment"
        return schedule

    @staticmethod
    def create_family_emergency_absence(db: Session) -> dict:
        """
        Create family emergency with unknown return date.

        Resident has family emergency, return date uncertain.
        """
        # Create schedule
        schedule = ScheduleFactory.create_complete_schedule(
            db, num_residents=6, num_faculty=3, num_days=14
        )

        # Family emergency starting today
        emergency_resident = schedule["residents"][0]
        emergency = LeaveFactory.create_family_emergency(
            db,
            person=emergency_resident,
            start_date=date.today(),
            return_date_known=False,
        )

        schedule["family_emergency"] = emergency
        schedule["emergency_type"] = "family_emergency"
        return schedule

    @staticmethod
    def create_medical_emergency(db: Session) -> dict:
        """
        Create medical emergency requiring immediate coverage.

        Faculty has medical emergency mid-shift, needs immediate replacement.
        """
        # Create FMIT schedule (24/7 coverage critical)
        schedule = ScheduleFactory.create_fmit_week_schedule(db, num_faculty=7)

        # Medical emergency for on-duty faculty
        emergency_faculty = schedule["faculty"][0]
        medical_leave = LeaveFactory.create_medical_leave(
            db,
            person=emergency_faculty,
            start_date=date.today(),  # Starts today (emergency)
            days=14,
        )

        schedule["medical_emergency"] = medical_leave
        schedule["emergency_type"] = "medical_emergency"
        return schedule

    @staticmethod
    def create_multiple_simultaneous_emergencies(db: Session) -> dict:
        """
        Create multiple simultaneous emergencies.

        Worst-case scenario: multiple staff unavailable at once.
        """
        # Create schedule
        schedule = ScheduleFactory.create_complete_schedule(
            db, num_residents=10, num_faculty=5, num_days=7
        )

        emergencies = []

        # Emergency 1: Faculty deployment
        deployment = LeaveFactory.create_deployment(
            db,
            person=schedule["faculty"][0],
            start_date=date.today() + timedelta(days=1),
            days=90,
        )
        emergencies.append(("deployment", deployment))

        # Emergency 2: Resident family emergency
        family_emergency = LeaveFactory.create_family_emergency(
            db,
            person=schedule["residents"][0],
            start_date=date.today(),
        )
        emergencies.append(("family_emergency", family_emergency))

        # Emergency 3: Faculty medical emergency
        medical = LeaveFactory.create_medical_leave(
            db,
            person=schedule["faculty"][1],
            start_date=date.today(),
            days=7,
        )
        emergencies.append(("medical", medical))

        schedule["emergencies"] = emergencies
        schedule["emergency_type"] = "multiple_simultaneous"
        return schedule

    @staticmethod
    def create_tdy_overlap_emergency(db: Session) -> dict:
        """
        Create TDY overlap emergency.

        Multiple faculty on TDY simultaneously, leaving coverage gap.
        """
        # Create faculty
        faculty = PersonFactory.create_batch_faculty(
            db, count=5, include_leadership=False
        )

        # Create overlapping TDY assignments
        tdys = []
        start_date = date.today() + timedelta(days=7)

        for i, fac in enumerate(faculty[:3]):
            # Stagger start dates slightly but overlap
            tdy_start = start_date + timedelta(days=i * 3)
            tdy = LeaveFactory.create_tdy(
                db,
                person=fac,
                start_date=tdy_start,
                days=14,
                location=f"Location-{i + 1}",
            )
            tdys.append(tdy)

        return {
            "faculty": faculty,
            "tdys": tdys,
            "emergency_type": "tdy_overlap",
        }

    @staticmethod
    def create_natural_disaster_scenario(db: Session) -> dict:
        """
        Create natural disaster scenario (hurricane, earthquake).

        Facility closes, all staff evacuated.
        """
        # Create full schedule
        schedule = ScheduleFactory.create_complete_schedule(
            db, num_residents=10, num_faculty=5, num_days=7
        )

        # Emergency closure starting tomorrow
        closure_date = date.today() + timedelta(days=1)

        # All staff unavailable during closure
        absences = []
        all_people = schedule["residents"] + schedule["faculty"]

        for person in all_people:
            absence = LeaveFactory.create_absence(
                db,
                person=person,
                start_date=closure_date,
                end_date=closure_date + timedelta(days=3),
                absence_type="emergency_leave",
                is_blocking=True,
                notes="Natural disaster - facility closure",
            )
            absences.append(absence)

        schedule["closure_absences"] = absences
        schedule["emergency_type"] = "natural_disaster"
        return schedule

    @staticmethod
    def create_covid_outbreak_scenario(db: Session) -> dict:
        """
        Create COVID outbreak scenario.

        Multiple residents test positive, need to quarantine.
        """
        # Create schedule
        schedule = ScheduleFactory.create_complete_schedule(
            db, num_residents=12, num_faculty=4, num_days=14
        )

        # 5 residents test positive (need 10-day quarantine)
        quarantine_absences = []
        for resident in schedule["residents"][:5]:
            quarantine = LeaveFactory.create_medical_leave(
                db,
                person=resident,
                start_date=date.today() + timedelta(days=1),
                days=10,
            )
            quarantine_absences.append(quarantine)

        schedule["quarantine_absences"] = quarantine_absences
        schedule["emergency_type"] = "covid_outbreak"
        return schedule

    @staticmethod
    def create_facility_power_outage(db: Session) -> dict:
        """
        Create facility power outage emergency.

        Critical systems down, limited staffing can work.
        """
        # Create weekend call schedule
        schedule = ScheduleFactory.create_weekend_call_schedule(
            db, num_faculty=4, num_weekends=2
        )

        # Power outage affects operations (represented as emergency closure)
        outage_date = date.today() + timedelta(days=1)

        schedule["outage_date"] = outage_date
        schedule["emergency_type"] = "power_outage"
        return schedule

    @staticmethod
    def create_chemical_exposure_incident(db: Session) -> dict:
        """
        Create chemical exposure incident.

        Staff exposed to hazardous material, need decontamination.
        """
        # Create clinic schedule
        schedule = ScheduleFactory.create_clinic_day_schedule(
            db, num_residents=4, num_faculty=2
        )

        # All exposed staff unavailable rest of day
        exposure_absences = []
        exposed_people = schedule["residents"][:2] + schedule["faculty"][:1]

        for person in exposed_people:
            absence = LeaveFactory.create_medical_leave(
                db,
                person=person,
                start_date=date.today(),
                days=1,
            )
            exposure_absences.append(absence)

        schedule["exposure_absences"] = exposure_absences
        schedule["emergency_type"] = "chemical_exposure"
        return schedule

    @staticmethod
    def create_cascading_callout_failure(db: Session) -> dict:
        """
        Create cascading callout failure.

        On-call staff can't be reached, backup fails, emergency coverage needed.
        """
        # Create weekend call schedule
        schedule = ScheduleFactory.create_weekend_call_schedule(
            db, num_faculty=3, num_weekends=1
        )

        # Primary on-call: family emergency (unavailable)
        primary_faculty = schedule["faculty"][0]
        primary_emergency = LeaveFactory.create_family_emergency(
            db,
            person=primary_faculty,
            start_date=date.today(),
        )

        # Backup on-call: medical emergency (also unavailable)
        backup_faculty = schedule["faculty"][1]
        backup_emergency = LeaveFactory.create_medical_leave(
            db,
            person=backup_faculty,
            start_date=date.today(),
            days=3,
        )

        schedule["primary_emergency"] = primary_emergency
        schedule["backup_emergency"] = backup_emergency
        schedule["emergency_type"] = "cascading_callout_failure"
        return schedule
