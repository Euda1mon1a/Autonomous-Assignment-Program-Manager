"""
Leave and Absence Compliance Validator.

Implements ACGME leave and absence validation:
- Blocking absence enforcement (no assignments during blocks)
- Sick leave compliance (>3 days blocks, ≤3 days doesn't)
- Educational leave tracking (conferences, professional development)
- Medical leave validation (extended illness/recovery)
- TDY/Deployment handling (military-specific)
- Post-deployment recovery enforcement

This validator ensures residents cannot be assigned during blocking
absences while tracking leave policies for reporting.
"""

import logging
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Optional
from uuid import UUID

logger = logging.getLogger(__name__)


# Leave Type Constants
BLOCKING_LEAVE_TYPES = {
    "deployment",
    "tdy",
    "family_emergency",
    "bereavement",
    "emergency_leave",
    "maternity_paternity",
    "convalescent",
}

CONDITIONAL_BLOCKING_LEAVE_TYPES = {
    "medical": 7,  # Block if > 7 days
    "sick": 3,  # Block if > 3 days
}

NON_BLOCKING_LEAVE_TYPES = {"vacation", "conference"}

# Recovery periods
POST_DEPLOYMENT_RECOVERY_DAYS = 7
POST_CONVALESCENT_RECOVERY_DAYS = 3


@dataclass
class LeaveViolation:
    """Represents a leave compliance violation."""

    person_id: UUID
    violation_type: str  # "assignment_during_block", "expired_return_date"
    severity: str  # "CRITICAL", "HIGH"
    message: str
    absence_id: UUID
    conflict_dates: list[date]


@dataclass
class LeaveWarning:
    """Represents a leave compliance warning."""

    person_id: UUID
    warning_type: str  # "tentative_return", "approaching_end"
    message: str
    absence_id: UUID
    days_until_return: int


class LeaveValidator:
    """
    Validates ACGME leave and absence compliance for residents.

    Rules:
    1. No assignment during blocking absences (hard constraint)
    2. Conditional blocking based on duration (sick >3 days, medical >7 days)
    3. Post-deployment recovery period enforcement
    4. Post-surgical recovery validation
    5. Tentative return date follow-up
    """

    def __init__(self) -> None:
        """Initialize leave validator."""
        self.blocking_types = BLOCKING_LEAVE_TYPES
        self.conditional_types = CONDITIONAL_BLOCKING_LEAVE_TYPES
        self.non_blocking_types = NON_BLOCKING_LEAVE_TYPES

    def should_block_assignment(
        self,
        absence_type: str,
        start_date: date,
        end_date: date,
        is_blocking_override: bool | None = None,
    ) -> bool:
        """
        Determine if absence should block assignments.

        Logic:
        1. Explicit override (is_blocking_override) takes precedence
        2. Always-blocking types (deployment, TDY, etc.)
        3. Duration-based types (medical >7d, sick >3d)
        4. Non-blocking types (vacation, conference)

        Args:
            absence_type: Type of absence
            start_date: Absence start date
            end_date: Absence end date
            is_blocking_override: Explicit block setting (if provided)

        Returns:
            True if should block assignments, False otherwise
        """
        # Explicit override takes precedence
        if is_blocking_override is not None:
            return is_blocking_override

        # Always-blocking types
        if absence_type in self.blocking_types:
            return True

        # Duration-based types
        if absence_type in self.conditional_types:
            duration_days = (end_date - start_date).days + 1
            threshold = self.conditional_types[absence_type]
            return duration_days > threshold

        # Non-blocking types
        if absence_type in self.non_blocking_types:
            return False

        # Default: block unknown types (conservative)
        return True

    def validate_no_assignment_during_block(
        self,
        person_id: UUID,
        absence_id: UUID,
        absence_type: str,
        start_date: date,
        end_date: date,
        assigned_dates: list[date],
        is_blocking: bool | None = None,
    ) -> LeaveViolation | None:
        """
        Validate that resident is not assigned during blocking absence.

        Args:
            person_id: Resident ID
            absence_id: Absence ID
            absence_type: Type of absence
            start_date: Absence start date
            end_date: Absence end date (inclusive)
            assigned_dates: List of dates resident is assigned
            is_blocking: Explicit block setting

        Returns:
            LeaveViolation if assignments found during block, None otherwise
        """
        # Determine if should block
        if not self.should_block_assignment(
            absence_type, start_date, end_date, is_blocking
        ):
            return None  # Non-blocking, no violation possible

        # Check for assignments during absence
        conflict_dates = [d for d in assigned_dates if start_date <= d <= end_date]

        if not conflict_dates:
            return None  # No conflicts

        # Create violation
        message = (
            f"Resident assigned during blocking {absence_type} absence: "
            f"{len(conflict_dates)} dates assigned between "
            f"{start_date} and {end_date}"
        )

        return LeaveViolation(
            person_id=person_id,
            violation_type="assignment_during_block",
            severity="CRITICAL",
            message=message,
            absence_id=absence_id,
            conflict_dates=conflict_dates,
        )

    def validate_sick_leave_compliance(
        self,
        person_id: UUID,
        absence_id: UUID,
        start_date: date,
        end_date: date,
        days_blocked: list[date] | None = None,
    ) -> LeaveViolation | None:
        """
        Validate sick leave compliance (duration-based blocking).

        ACGME allows short sick leave without blocking assignment:
        - ≤3 days: Does not block (minor illness)
        - >3 days: Blocks assignment (extended illness)

        Args:
            person_id: Resident ID
            absence_id: Absence ID
            start_date: Absence start date
            end_date: Absence end date
            days_blocked: Days marked as blocked (if any)

        Returns:
            LeaveViolation if rules violated, None otherwise
        """
        duration = (end_date - start_date).days + 1

        # Short sick leave (<= 3 days) should not block
        if duration <= 3:
            if days_blocked:
                return LeaveViolation(
                    person_id=person_id,
                    violation_type="assignment_during_block",
                    severity="MEDIUM",
                    message=(
                        f"Sick leave ≤3 days ({duration}d) incorrectly marked "
                        f"as blocking"
                    ),
                    absence_id=absence_id,
                    conflict_dates=days_blocked,
                )

        # Extended sick leave (>3 days) should block
        # No violation possible here (blocking is expected)
        return None

    def validate_medical_leave_compliance(
        self,
        person_id: UUID,
        absence_id: UUID,
        start_date: date,
        end_date: date,
        recovery_status: str | None = None,
    ) -> LeaveViolation | None:
        """
        Validate medical leave compliance (surgery/illness recovery).

        Args:
            person_id: Resident ID
            absence_id: Absence ID
            start_date: Leave start date
            end_date: Leave end date
            recovery_status: Status of recovery ('in_progress', 'cleared')

        Returns:
            LeaveViolation if cleared to return before end_date, None otherwise
        """
        # If medically cleared before end_date, should reduce absence duration
        if recovery_status == "cleared":
            return LeaveViolation(
                person_id=person_id,
                violation_type="assignment_during_block",
                severity="HIGH",
                message=(
                    f"Medical clearance received but absence extends to {end_date}. "
                    f"Update leave end_date when cleared to return to duty."
                ),
                absence_id=absence_id,
                conflict_dates=[],
            )

        return None

    def validate_tdy_deployment_compliance(
        self,
        person_id: UUID,
        absence_id: UUID,
        start_date: date,
        end_date: date,
        deployment_orders: bool = False,
        tdy_location: str | None = None,
    ) -> LeaveViolation | None:
        """
        Validate TDY/Deployment absence (military-specific).

        Args:
            person_id: Resident ID
            absence_id: Absence ID
            start_date: Deployment start date
            end_date: Deployment end date
            deployment_orders: Whether backed by deployment orders
            tdy_location: TDY destination (for validation)

        Returns:
            LeaveViolation if missing required info, None otherwise
        """
        # TDY requires destination
        if not tdy_location and "tdy" in str(absence_id):
            return LeaveViolation(
                person_id=person_id,
                violation_type="assignment_during_block",
                severity="MEDIUM",
                message="TDY absence missing destination location",
                absence_id=absence_id,
                conflict_dates=[],
            )

        # Deployment should have orders
        if not deployment_orders and "deployment" in str(absence_id):
            return LeaveViolation(
                person_id=person_id,
                violation_type="assignment_during_block",
                severity="MEDIUM",
                message="Deployment absence missing documented orders",
                absence_id=absence_id,
                conflict_dates=[],
            )

        return None

    def validate_post_deployment_recovery(
        self,
        person_id: UUID,
        deployment_end_date: date,
        assignments_after_return: list[date],
    ) -> LeaveViolation | None:
        """
        Validate post-deployment recovery period.

        After returning from deployment, resident should have recovery
        period before full duty assignments resume.

        Args:
            person_id: Resident ID
            deployment_end_date: Date deployment ends
            assignments_after_return: Assignments after return

        Returns:
            LeaveViolation if recovery period insufficient, None otherwise
        """
        recovery_end_date = deployment_end_date + timedelta(
            days=POST_DEPLOYMENT_RECOVERY_DAYS
        )

        early_assignments = [
            d
            for d in assignments_after_return
            if deployment_end_date < d < recovery_end_date
        ]

        if early_assignments:
            return LeaveViolation(
                person_id=person_id,
                violation_type="assignment_during_block",
                severity="HIGH",
                message=(
                    f"Insufficient post-deployment recovery period: "
                    f"{len(early_assignments)} assignments before "
                    f"recovery end {recovery_end_date}"
                ),
                absence_id=UUID("00000000-0000-0000-0000-000000000000"),
                conflict_dates=early_assignments,
            )

        return None

    def validate_tentative_return_date(
        self,
        person_id: UUID,
        absence_id: UUID,
        return_date_tentative: bool,
        return_date: date,
        today: date,
    ) -> LeaveWarning | None:
        """
        Check tentative return dates and flag for follow-up.

        Args:
            person_id: Resident ID
            absence_id: Absence ID
            return_date_tentative: Whether return date is uncertain
            return_date: Expected return date
            today: Current date

        Returns:
            LeaveWarning if follow-up needed, None otherwise
        """
        if not return_date_tentative:
            return None  # Return date confirmed

        days_until_return = (return_date - today).days

        if days_until_return <= 7:  # Return approaching
            return LeaveWarning(
                person_id=person_id,
                warning_type="approaching_end",
                message=(
                    f"Tentative return date {return_date} approaching. "
                    f"Confirm actual return date with resident."
                ),
                absence_id=absence_id,
                days_until_return=max(0, days_until_return),
            )

        return None

    def validate_convalescent_leave_recovery(
        self,
        person_id: UUID,
        absence_id: UUID,
        start_date: date,
        end_date: date,
        procedure_type: str | None = None,
    ) -> LeaveWarning | None:
        """
        Validate convalescent leave duration matches typical recovery.

        Args:
            person_id: Resident ID
            absence_id: Absence ID
            start_date: Recovery start date
            end_date: Expected return to work date
            procedure_type: Type of procedure (for expected recovery duration)

        Returns:
            LeaveWarning if duration seems short, None otherwise
        """
        duration = (end_date - start_date).days

        # Common minimum recovery times (in days)
        minimum_recovery = {
            "appendectomy": 14,
            "acl_repair": 42,
            "childbirth_vaginal": 42,
            "childbirth_csection": 56,
            "hysterectomy": 42,
        }

        if procedure_type and procedure_type in minimum_recovery:
            min_days = minimum_recovery[procedure_type]
            if duration < min_days:
                return LeaveWarning(
                    person_id=person_id,
                    warning_type="tentative_return",
                    message=(
                        f"Convalescent leave {duration} days may be short for "
                        f"{procedure_type} (typical: {min_days} days). "
                        f"Verify with resident and physician."
                    ),
                    absence_id=absence_id,
                    days_until_return=duration,
                )

        return None

    def get_leave_impact_summary(
        self,
        person_id: UUID,
        leave_records: list[dict],
        schedule_period_days: int,
    ) -> dict:
        """
        Generate summary of leave impact on work hours.

        Args:
            person_id: Resident ID
            leave_records: List of leave dicts with 'start_date', 'end_date',
                          'is_blocking'
            schedule_period_days: Total days in schedule period

        Returns:
            Summary dict with blocking vs non-blocking breakdown
        """
        blocking_days = 0
        non_blocking_days = 0

        for leave in leave_records:
            start = leave.get("start_date")
            end = leave.get("end_date")
            if not start or not end:
                continue

            duration = (end - start).days + 1
            if leave.get("is_blocking", False):
                blocking_days += duration
            else:
                non_blocking_days += duration

        total_leave_days = blocking_days + non_blocking_days
        work_capacity_hours = (schedule_period_days - blocking_days) * 12  # 12h/day
        work_hours_limit = 80 * 4  # 80h/week × 4 weeks

        return {
            "total_leave_days": total_leave_days,
            "blocking_days": blocking_days,
            "non_blocking_days": non_blocking_days,
            "work_days_available": schedule_period_days - blocking_days,
            "work_capacity_hours": work_capacity_hours,
            "hours_limit": work_hours_limit,
            "capacity_utilization": (
                work_hours_limit / work_capacity_hours if work_capacity_hours > 0 else 0
            ),
        }
