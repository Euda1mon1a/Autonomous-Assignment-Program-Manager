"""Resilience framework stress test scenarios."""

from datetime import date, timedelta

from sqlalchemy.orm import Session

from tests.factories.leave_factory import LeaveFactory
from tests.factories.person_factory import PersonFactory
from tests.factories.schedule_factory import ScheduleFactory


class ResilienceScenarios:
    """Pre-built scenarios for resilience framework testing."""

    @staticmethod
    def create_n_minus_1_test(db: Session) -> dict:
        """
        Create N-1 resilience test.

        Can system handle loss of 1 person? (Single point of failure test)
        """
        # Create minimal viable schedule
        schedule = ScheduleFactory.create_complete_schedule(
            db, num_residents=4, num_faculty=2, num_days=7
        )

        # Remove one resident (emergency)
        lost_resident = schedule["residents"][0]
        emergency = LeaveFactory.create_family_emergency(
            db, person=lost_resident, return_date_known=False
        )

        schedule["lost_person"] = lost_resident
        schedule["emergency"] = emergency
        schedule["resilience_test"] = "n_minus_1"
        return schedule

    @staticmethod
    def create_n_minus_2_test(db: Session) -> dict:
        """
        Create N-2 resilience test.

        Can system handle loss of 2 people simultaneously?
        """
        # Create schedule with some buffer
        schedule = ScheduleFactory.create_complete_schedule(
            db, num_residents=8, num_faculty=4, num_days=7
        )

        # Remove two people (different emergencies)
        emergencies = []

        # Loss 1: Resident family emergency
        emergency1 = LeaveFactory.create_family_emergency(
            db, person=schedule["residents"][0]
        )
        emergencies.append(emergency1)

        # Loss 2: Faculty deployment
        emergency2 = LeaveFactory.create_deployment(
            db, person=schedule["faculty"][0], days=90
        )
        emergencies.append(emergency2)

        schedule["emergencies"] = emergencies
        schedule["resilience_test"] = "n_minus_2"
        return schedule

    @staticmethod
    def create_80_percent_utilization_test(db: Session) -> dict:
        """
        Create 80% utilization threshold test.

        Test queuing theory: >80% utilization leads to cascade failures.
        """
        # Create schedule at exactly 80% capacity
        num_residents = 10
        num_faculty = 4

        # 80% utilization = 8 residents working, 2 buffer
        schedule = ScheduleFactory.create_complete_schedule(
            db, num_residents=num_residents, num_faculty=num_faculty, num_days=28
        )

        # Now push to 90% by adding leave for 1 resident (reduces buffer)
        leave = LeaveFactory.create_vacation(
            db, person=schedule["residents"][-1], days=7
        )

        schedule["leave"] = leave
        schedule["utilization_before"] = 0.80
        schedule["utilization_after"] = 0.90
        schedule["resilience_test"] = "80_percent_threshold"
        return schedule

    @staticmethod
    def create_cascade_failure_test(db: Session) -> dict:
        """
        Create cascade failure test.

        One failure triggers multiple downstream failures.
        """
        # Create tightly-coupled schedule
        schedule = ScheduleFactory.create_fmit_week_schedule(db, num_faculty=7)

        # Faculty A can't work -> Faculty B must cover double
        # Faculty B overworked -> ACGME violation -> Faculty C forced in
        # Faculty C cancels planned leave -> morale impact

        # Trigger: Faculty A deployment
        trigger_faculty = schedule["faculty"][0]
        deployment = LeaveFactory.create_deployment(
            db,
            person=trigger_faculty,
            start_date=date.today() + timedelta(days=1),
            days=30,
        )

        # Downstream: Faculty C had planned leave (now conflicted)
        downstream_faculty = schedule["faculty"][2]
        planned_leave = LeaveFactory.create_vacation(
            db,
            person=downstream_faculty,
            start_date=date.today() + timedelta(days=7),
            days=7,
        )

        schedule["trigger_event"] = deployment
        schedule["downstream_conflict"] = planned_leave
        schedule["resilience_test"] = "cascade_failure"
        return schedule

    @staticmethod
    def create_defense_in_depth_test(db: Session) -> dict:
        """
        Create defense in depth test.

        Test all 5 defense levels: GREEN -> YELLOW -> ORANGE -> RED -> BLACK
        """
        # Create schedule with progressively reducing staff
        schedule = ScheduleFactory.create_complete_schedule(
            db, num_residents=12, num_faculty=5, num_days=28
        )

        # Level GREEN: Full staffing (baseline)
        # Level YELLOW: 1 person out (10% reduction)
        yellow_absence = LeaveFactory.create_vacation(
            db, person=schedule["residents"][0], days=7
        )

        # Level ORANGE: 2 people out (20% reduction)
        orange_absence = LeaveFactory.create_medical_leave(
            db, person=schedule["residents"][1], days=7
        )

        # Level RED: 3 people out (30% reduction)
        red_absence = LeaveFactory.create_family_emergency(
            db, person=schedule["faculty"][0]
        )

        # Level BLACK: 4 people out (40% reduction - critical)
        black_absence = LeaveFactory.create_deployment(
            db, person=schedule["faculty"][1], days=60
        )

        schedule["defense_levels"] = {
            "green": None,  # Baseline
            "yellow": yellow_absence,
            "orange": orange_absence,
            "red": red_absence,
            "black": black_absence,
        }
        schedule["resilience_test"] = "defense_in_depth"
        return schedule

    @staticmethod
    def create_burnout_propagation_test(db: Session) -> dict:
        """
        Create burnout propagation test (SIR epidemiology model).

        Overworked residents "infect" others through increased workload.
        """
        # Create schedule with some residents overworked
        schedule = ScheduleFactory.create_complete_schedule(
            db, num_residents=10, num_faculty=3, num_days=28  # Understaffed
        )

        # Simulate burnout by creating consecutive weeks without breaks
        from tests.factories.compliance_factory import ComplianceFactory

        burnout_scenario = ComplianceFactory.create_consecutive_weeks_violation(
            db, resident=schedule["residents"][0], num_weeks=6
        )

        schedule["burnout_resident"] = burnout_scenario["resident"]
        schedule["burnout_assignments"] = burnout_scenario["assignments"]
        schedule["resilience_test"] = "burnout_propagation"
        return schedule

    @staticmethod
    def create_static_stability_test(db: Session) -> dict:
        """
        Create static stability test.

        Pre-computed fallback schedules for emergency use.
        """
        # Create primary schedule
        primary = ScheduleFactory.create_complete_schedule(
            db, num_residents=10, num_faculty=4, num_days=28
        )

        # Create fallback schedule (reduced scope)
        fallback = ScheduleFactory.create_complete_schedule(
            db, num_residents=6, num_faculty=3, num_days=7
        )

        return {
            "primary_schedule": primary,
            "fallback_schedule": fallback,
            "resilience_test": "static_stability",
        }

    @staticmethod
    def create_blast_radius_test(db: Session) -> dict:
        """
        Create blast radius isolation test.

        Failure in one zone shouldn't affect other zones.
        """
        # Create two independent clinic zones
        zone_a = ScheduleFactory.create_clinic_day_schedule(
            db, num_residents=4, num_faculty=2, clinic_date=date.today()
        )

        zone_b = ScheduleFactory.create_clinic_day_schedule(
            db, num_residents=4, num_faculty=2, clinic_date=date.today() + timedelta(days=1)
        )

        # Failure in zone A
        zone_a_failure = LeaveFactory.create_family_emergency(
            db, person=zone_a["faculty"][0]
        )

        # Zone B should be unaffected
        return {
            "zone_a": zone_a,
            "zone_b": zone_b,
            "zone_a_failure": zone_a_failure,
            "resilience_test": "blast_radius_isolation",
        }

    @staticmethod
    def create_erlang_coverage_test(db: Session) -> dict:
        """
        Create Erlang C queuing test.

        Test optimal staffing for arrival rate and service time.
        """
        # Create clinic schedule with specific coverage requirements
        # Assume 10 patients/hour arrival rate, 15 min service time

        # Optimal staffing from Erlang C would be ~3 residents
        # Test with 2 (understaffed) vs 3 (optimal) vs 4 (overstaffed)

        understaffed = ScheduleFactory.create_clinic_day_schedule(
            db, num_residents=2, num_faculty=1
        )

        optimal = ScheduleFactory.create_clinic_day_schedule(
            db, num_residents=3, num_faculty=1
        )

        overstaffed = ScheduleFactory.create_clinic_day_schedule(
            db, num_residents=4, num_faculty=1
        )

        return {
            "understaffed": understaffed,
            "optimal": optimal,
            "overstaffed": overstaffed,
            "arrival_rate": 10,  # patients/hour
            "service_time": 15,  # minutes
            "resilience_test": "erlang_coverage",
        }

    @staticmethod
    def create_time_crystal_test(db: Session) -> dict:
        """
        Create time crystal anti-churn test.

        Minimize schedule changes during regeneration.
        """
        # Create initial schedule
        initial = ScheduleFactory.create_complete_schedule(
            db, num_residents=8, num_faculty=4, num_days=28
        )

        # Simulate regeneration with minimal changes
        # (In practice, solver would try to preserve existing assignments)

        return {
            "initial_schedule": initial,
            "resilience_test": "time_crystal_anti_churn",
        }

    @staticmethod
    def create_recovery_distance_test(db: Session) -> dict:
        """
        Create recovery distance test.

        Minimum edits needed to recover from N-1 failure.
        """
        # Create stable schedule
        stable = ScheduleFactory.create_complete_schedule(
            db, num_residents=8, num_faculty=4, num_days=7
        )

        # Remove one person
        lost_person = stable["residents"][0]
        emergency = LeaveFactory.create_family_emergency(db, person=lost_person)

        # Recovery = reassign lost_person's assignments to others
        # Count minimum swaps needed

        return {
            "stable_schedule": stable,
            "lost_person": lost_person,
            "emergency": emergency,
            "resilience_test": "recovery_distance",
        }
