"""
Advanced ACGME Compliance Validator.

Enhanced validation with detailed tracking:
- 24+4 hour rule (duty + handoff)
- Night float limits (max 6 consecutive nights)
- Moonlighting hour tracking
- PGY-specific requirements
- Detailed duty hour breakdowns
"""
from datetime import date, timedelta, datetime
from collections import defaultdict
from typing import Optional, Literal

from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.person import Person
from app.models.block import Block
from app.models.assignment import Assignment
from app.schemas.schedule import ValidationResult, Violation


class AdvancedACGMEValidator:
    """Advanced ACGME compliance checking with enhanced tracking."""

    # Constants
    MAX_DUTY_HOURS = 24
    MAX_HANDOFF_HOURS = 4
    MAX_CONTINUOUS_HOURS = 28  # 24 + 4
    MAX_NIGHT_FLOAT_CONSECUTIVE = 6
    HOURS_PER_HALF_DAY = 6
    MAX_MOONLIGHTING_HOURS_PER_WEEK = 80  # Total including internal + external

    # PGY-specific limits
    PGY1_MAX_SHIFT_LENGTH = 16  # First year limit (without supervision)
    PGY2_PLUS_MAX_SHIFT_LENGTH = 24  # Upper level limit

    def __init__(self, db: Session):
        """Initialize validator with database session."""
        self.db = db

    def validate_24_plus_4_rule(
        self, person_id: str, start_date: date, end_date: date
    ) -> list[Violation]:
        """
        Validate 24+4 hour rule (max 24h duty + 4h handoff).

        Args:
            person_id: Person UUID to validate
            start_date: Start of validation period
            end_date: End of validation period

        Returns:
            List of violations found
        """
        violations = []
        person = self.db.query(Person).filter(Person.id == person_id).first()

        if not person or not person.is_resident:
            return violations

        assignments = (
            self.db.query(Assignment)
            .join(Block)
            .filter(
                and_(
                    Assignment.person_id == person_id,
                    Block.date >= start_date,
                    Block.date <= end_date
                )
            )
            .all()
        )

        # Group assignments by date
        hours_by_date = self._assignments_to_hours(assignments)

        # Check for continuous duty periods exceeding 28 hours
        dates = sorted(hours_by_date.keys())

        i = 0
        while i < len(dates):
            continuous_hours = 0
            start_violation_date = dates[i]

            # Count continuous hours
            j = i
            while j < len(dates) and (j == i or (dates[j] - dates[j-1]).days <= 1):
                continuous_hours += hours_by_date[dates[j]]
                j += 1

            if continuous_hours > self.MAX_CONTINUOUS_HOURS:
                violations.append(
                    Violation(
                        type="24_PLUS_4_VIOLATION",
                        severity="CRITICAL",
                        person_id=person.id,
                        person_name=person.name,
                        message=f"{person.name}: {continuous_hours}h continuous duty (limit: {self.MAX_CONTINUOUS_HOURS}h)",
                        details={
                            "start_date": start_violation_date.isoformat(),
                            "continuous_hours": continuous_hours,
                            "max_allowed": self.MAX_CONTINUOUS_HOURS,
                        },
                    )
                )

            i = j if j > i else i + 1

        return violations

    def validate_night_float_limits(
        self, person_id: str, start_date: date, end_date: date
    ) -> list[Violation]:
        """
        Validate night float limits (max 6 consecutive nights).

        Night shifts are identified as assignments on blocks marked as night coverage.

        Args:
            person_id: Person UUID to validate
            start_date: Start of validation period
            end_date: End of validation period

        Returns:
            List of violations found
        """
        violations = []
        person = self.db.query(Person).filter(Person.id == person_id).first()

        if not person or not person.is_resident:
            return violations

        # Get all assignments for the person
        assignments = (
            self.db.query(Assignment)
            .join(Block)
            .filter(
                and_(
                    Assignment.person_id == person_id,
                    Block.date >= start_date,
                    Block.date <= end_date
                )
            )
            .order_by(Block.date)
            .all()
        )

        # Identify night shifts (PM blocks or explicitly marked)
        night_dates = set()
        for assignment in assignments:
            block = self.db.query(Block).filter(Block.id == assignment.block_id).first()
            # Consider PM blocks as potential night coverage
            if block and block.time_of_day == "PM":
                night_dates.add(block.date)

        if not night_dates:
            return violations

        # Check for consecutive night shifts
        sorted_nights = sorted(night_dates)
        consecutive = 1
        start_sequence = sorted_nights[0]

        for i in range(1, len(sorted_nights)):
            if (sorted_nights[i] - sorted_nights[i-1]).days == 1:
                consecutive += 1
                if consecutive > self.MAX_NIGHT_FLOAT_CONSECUTIVE:
                    violations.append(
                        Violation(
                            type="NIGHT_FLOAT_VIOLATION",
                            severity="HIGH",
                            person_id=person.id,
                            person_name=person.name,
                            message=f"{person.name}: {consecutive} consecutive night shifts (limit: {self.MAX_NIGHT_FLOAT_CONSECUTIVE})",
                            details={
                                "start_date": start_sequence.isoformat(),
                                "end_date": sorted_nights[i].isoformat(),
                                "consecutive_nights": consecutive,
                            },
                        )
                    )
                    break
            else:
                consecutive = 1
                start_sequence = sorted_nights[i]

        return violations

    def validate_moonlighting_hours(
        self, person_id: str, start_date: date, end_date: date, external_hours: float = 0.0
    ) -> list[Violation]:
        """
        Validate moonlighting hours (total internal + external must not exceed limits).

        Args:
            person_id: Person UUID to validate
            start_date: Start of validation period
            end_date: End of validation period
            external_hours: External moonlighting hours to include

        Returns:
            List of violations found
        """
        violations = []
        person = self.db.query(Person).filter(Person.id == person_id).first()

        if not person or not person.is_resident:
            return violations

        # Calculate internal duty hours
        assignments = (
            self.db.query(Assignment)
            .join(Block)
            .filter(
                and_(
                    Assignment.person_id == person_id,
                    Block.date >= start_date,
                    Block.date <= end_date
                )
            )
            .all()
        )

        internal_hours = len(assignments) * self.HOURS_PER_HALF_DAY
        total_hours = internal_hours + external_hours

        # Check weekly average (simplified: total hours / weeks)
        weeks = max(1, (end_date - start_date).days / 7)
        avg_weekly_hours = total_hours / weeks

        if avg_weekly_hours > self.MAX_MOONLIGHTING_HOURS_PER_WEEK:
            violations.append(
                Violation(
                    type="MOONLIGHTING_VIOLATION",
                    severity="CRITICAL",
                    person_id=person.id,
                    person_name=person.name,
                    message=f"{person.name}: {avg_weekly_hours:.1f}h/week total (internal + moonlighting) (limit: {self.MAX_MOONLIGHTING_HOURS_PER_WEEK}h)",
                    details={
                        "internal_hours": internal_hours,
                        "external_hours": external_hours,
                        "total_hours": total_hours,
                        "average_weekly_hours": avg_weekly_hours,
                    },
                )
            )

        return violations

    def validate_pgy_specific_rules(
        self, person_id: str, start_date: date, end_date: date
    ) -> list[Violation]:
        """
        Validate PGY-level specific requirements.

        - PGY-1: Max 16-hour shifts without direct supervision
        - PGY-2+: Max 24-hour shifts
        - Different supervision requirements

        Args:
            person_id: Person UUID to validate
            start_date: Start of validation period
            end_date: End of validation period

        Returns:
            List of violations found
        """
        violations = []
        person = self.db.query(Person).filter(Person.id == person_id).first()

        if not person or not person.is_resident:
            return violations

        assignments = (
            self.db.query(Assignment)
            .join(Block)
            .filter(
                and_(
                    Assignment.person_id == person_id,
                    Block.date >= start_date,
                    Block.date <= end_date
                )
            )
            .all()
        )

        # Check shift lengths based on PGY level
        max_shift_hours = (
            self.PGY1_MAX_SHIFT_LENGTH
            if person.pgy_level == 1
            else self.PGY2_PLUS_MAX_SHIFT_LENGTH
        )

        # Group by consecutive dates to find shifts
        hours_by_date = self._assignments_to_hours(assignments)
        for shift_date, hours in hours_by_date.items():
            if hours > max_shift_hours:
                violations.append(
                    Violation(
                        type="PGY_SHIFT_LENGTH_VIOLATION",
                        severity="HIGH",
                        person_id=person.id,
                        person_name=person.name,
                        message=f"{person.name} (PGY-{person.pgy_level}): {hours}h shift (limit: {max_shift_hours}h)",
                        details={
                            "date": shift_date.isoformat(),
                            "pgy_level": person.pgy_level,
                            "shift_hours": hours,
                            "max_allowed": max_shift_hours,
                        },
                    )
                )

        return violations

    def calculate_duty_hours_breakdown(
        self, person_id: str, start_date: date, end_date: date
    ) -> dict:
        """
        Calculate detailed duty hours breakdown.

        Returns comprehensive report including:
        - Total hours
        - Average hours per week
        - Weekend hours
        - Night hours
        - Days worked

        Args:
            person_id: Person UUID
            start_date: Start of period
            end_date: End of period

        Returns:
            Dict with detailed breakdown
        """
        person = self.db.query(Person).filter(Person.id == person_id).first()

        if not person:
            return {}

        assignments = (
            self.db.query(Assignment)
            .join(Block)
            .filter(
                and_(
                    Assignment.person_id == person_id,
                    Block.date >= start_date,
                    Block.date <= end_date
                )
            )
            .all()
        )

        total_hours = 0
        weekend_hours = 0
        night_hours = 0
        dates_worked = set()

        for assignment in assignments:
            block = self.db.query(Block).filter(Block.id == assignment.block_id).first()
            if block:
                hours = self.HOURS_PER_HALF_DAY
                total_hours += hours
                dates_worked.add(block.date)

                if block.is_weekend:
                    weekend_hours += hours
                if block.time_of_day == "PM":
                    night_hours += hours

        weeks = max(1, (end_date - start_date).days / 7)

        return {
            "person_id": str(person_id),
            "person_name": person.name,
            "pgy_level": person.pgy_level,
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
            },
            "hours": {
                "total": total_hours,
                "average_weekly": round(total_hours / weeks, 1),
                "weekend": weekend_hours,
                "night": night_hours,
                "weekday": total_hours - weekend_hours,
            },
            "days": {
                "worked": len(dates_worked),
                "total_in_period": (end_date - start_date).days + 1,
            },
        }

    def _assignments_to_hours(self, assignments: list[Assignment]) -> dict[date, int]:
        """Convert assignments to hours per date."""
        hours_by_date = defaultdict(int)

        for assignment in assignments:
            block = self.db.query(Block).filter(Block.id == assignment.block_id).first()
            if block:
                hours_by_date[block.date] += self.HOURS_PER_HALF_DAY

        return dict(hours_by_date)
