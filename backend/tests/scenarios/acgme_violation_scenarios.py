"""ACGME compliance violation test scenarios."""

from sqlalchemy.orm import Session

from tests.factories.compliance_factory import ComplianceFactory


class ACGMEViolationScenarios:
    """Pre-built scenarios for ACGME compliance violation testing."""

    @staticmethod
    def create_80_hour_violation(db: Session) -> dict:
        """
        Create scenario violating 80-hour work week rule.

        Resident works >80 hours in a single week.
        """
        return ComplianceFactory.create_80_hour_violation(db)

    @staticmethod
    def create_1_in_7_violation(db: Session) -> dict:
        """
        Create scenario violating 1-in-7 rest rule.

        Resident works 14+ consecutive days without 24-hour rest period.
        """
        return ComplianceFactory.create_1_in_7_violation(db)

    @staticmethod
    def create_pgy1_supervision_violation(db: Session) -> dict:
        """
        Create scenario violating PGY-1 supervision ratios (1:2).

        More than 2 PGY-1 residents per 1 faculty supervisor.
        """
        return ComplianceFactory.create_supervision_ratio_violation(
            db, pgy_level=1, num_residents=6, num_faculty=1
        )

    @staticmethod
    def create_pgy2_supervision_violation(db: Session) -> dict:
        """
        Create scenario violating PGY-2/3 supervision ratios (1:4).

        More than 4 PGY-2/3 residents per 1 faculty supervisor.
        """
        return ComplianceFactory.create_supervision_ratio_violation(
            db, pgy_level=2, num_residents=10, num_faculty=1
        )

    @staticmethod
    def create_unsupervised_pgy1_violation(db: Session) -> dict:
        """
        Create scenario with unsupervised PGY-1 residents.

        PGY-1 residents assigned without any faculty supervision.
        """
        return ComplianceFactory.create_unsupervised_pgy1_violation(db)

    @staticmethod
    def create_capacity_violation(db: Session) -> dict:
        """
        Create scenario exceeding rotation capacity limits.

        More residents assigned than physical space allows.
        """
        return ComplianceFactory.create_capacity_violation(
            db, max_residents=4, actual_residents=8
        )

    @staticmethod
    def create_specialty_mismatch_violation(db: Session) -> dict:
        """
        Create scenario with specialty requirement violation.

        Rotation requires specialty but supervising faculty lacks it.
        """
        return ComplianceFactory.create_missing_specialty_violation(db)

    @staticmethod
    def create_burnout_risk_violation(db: Session) -> dict:
        """
        Create scenario with excessive consecutive weeks (burnout risk).

        Resident works 5+ consecutive weeks without break.
        """
        return ComplianceFactory.create_consecutive_weeks_violation(db, num_weeks=5)

    @staticmethod
    def create_all_violations(db: Session) -> dict:
        """
        Create comprehensive set of all ACGME violation types.

        Returns:
            dict: Map of violation_type -> scenario data
        """
        return ComplianceFactory.create_all_violation_types(db)

    @staticmethod
    def create_double_booking_violation(db: Session) -> dict:
        """
        Create scenario with double-booked resident.

        Same resident assigned to multiple rotations at same time.
        """
        return ComplianceFactory.create_double_booked_violation(db)
