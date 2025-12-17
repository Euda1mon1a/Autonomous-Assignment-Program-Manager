"""
Resident Fatigue Monitoring System.

Tracks and predicts resident fatigue based on:
- Consecutive duty days
- Night shift frequency
- Weekend coverage burden
- Time since last day off
- Overall workload intensity
"""
from datetime import date, timedelta

from sqlalchemy import and_
from sqlalchemy.orm import Session

from app.models.assignment import Assignment
from app.models.block import Block
from app.models.person import Person


class FatigueTracker:
    """Monitor and predict resident fatigue levels."""

    # Fatigue scoring weights
    WEIGHT_CONSECUTIVE_DAYS = 10  # Points per consecutive day
    WEIGHT_NIGHT_SHIFT = 15  # Extra points per night shift
    WEIGHT_WEEKEND = 12  # Extra points per weekend day
    WEIGHT_NO_DAY_OFF = 8  # Points per day without a day off
    WEIGHT_HOURLY_LOAD = 1.5  # Points per hour worked

    # Thresholds
    FATIGUE_THRESHOLD_HIGH = 70  # High risk threshold
    FATIGUE_THRESHOLD_MODERATE = 50  # Moderate risk threshold
    HOURS_PER_HALF_DAY = 6

    # Recovery constants
    BASE_RECOVERY_HOURS = 24  # Base recovery time
    RECOVERY_PER_FATIGUE_POINT = 0.5  # Additional hours per fatigue point

    def __init__(self, db: Session):
        """Initialize tracker with database session."""
        self.db = db

    def calculate_fatigue_score(self, person_id: str, target_date: date) -> dict:
        """
        Calculate fatigue score (0-100+) for a resident on a specific date.

        Higher scores indicate greater fatigue. Factors:
        - Consecutive duty days (without rest)
        - Night shift frequency
        - Weekend work burden
        - Time since last day off
        - Total hours worked

        Args:
            person_id: Person UUID
            target_date: Date to calculate fatigue for

        Returns:
            Dict with fatigue score and contributing factors
        """
        person = self.db.query(Person).filter(Person.id == person_id).first()

        if not person or not person.is_resident:
            return {
                "person_id": str(person_id),
                "fatigue_score": 0,
                "risk_level": "NONE",
                "error": "Person not found or not a resident",
            }

        # Look back 14 days to calculate fatigue
        lookback_start = target_date - timedelta(days=14)

        assignments = (
            self.db.query(Assignment)
            .join(Block)
            .filter(
                and_(
                    Assignment.person_id == person_id,
                    Block.date >= lookback_start,
                    Block.date <= target_date
                )
            )
            .order_by(Block.date)
            .all()
        )

        # Calculate factors
        consecutive_days = self._calculate_consecutive_days(assignments, target_date)
        night_shifts = self._count_night_shifts(assignments)
        weekend_days = self._count_weekend_days(assignments)
        days_since_off = self._days_since_last_off(assignments, target_date)
        total_hours = len(assignments) * self.HOURS_PER_HALF_DAY

        # Calculate fatigue score
        fatigue_score = (
            consecutive_days * self.WEIGHT_CONSECUTIVE_DAYS +
            night_shifts * self.WEIGHT_NIGHT_SHIFT +
            weekend_days * self.WEIGHT_WEEKEND +
            days_since_off * self.WEIGHT_NO_DAY_OFF +
            total_hours * self.WEIGHT_HOURLY_LOAD
        )

        # Determine risk level
        if fatigue_score >= self.FATIGUE_THRESHOLD_HIGH:
            risk_level = "HIGH"
        elif fatigue_score >= self.FATIGUE_THRESHOLD_MODERATE:
            risk_level = "MODERATE"
        else:
            risk_level = "LOW"

        return {
            "person_id": str(person_id),
            "person_name": person.name,
            "pgy_level": person.pgy_level,
            "date": target_date.isoformat(),
            "fatigue_score": round(fatigue_score, 1),
            "risk_level": risk_level,
            "factors": {
                "consecutive_days": consecutive_days,
                "night_shifts": night_shifts,
                "weekend_days": weekend_days,
                "days_since_off": days_since_off,
                "total_hours_14d": total_hours,
            },
        }

    def get_recovery_time_needed(self, person_id: str, target_date: date) -> dict:
        """
        Calculate recommended recovery time (hours of rest needed).

        Based on current fatigue score and intensity of recent work.

        Args:
            person_id: Person UUID
            target_date: Date to calculate recovery needs for

        Returns:
            Dict with recovery recommendations
        """
        fatigue_data = self.calculate_fatigue_score(person_id, target_date)
        fatigue_score = fatigue_data.get("fatigue_score", 0)

        # Calculate recovery time
        recovery_hours = self.BASE_RECOVERY_HOURS + (
            fatigue_score * self.RECOVERY_PER_FATIGUE_POINT
        )

        # Recommend consecutive days off
        days_off_needed = max(1, int(recovery_hours / 24))

        return {
            "person_id": str(person_id),
            "person_name": fatigue_data.get("person_name"),
            "current_fatigue_score": fatigue_score,
            "recovery_hours_needed": round(recovery_hours, 1),
            "recommended_days_off": days_off_needed,
            "risk_level": fatigue_data.get("risk_level"),
        }

    def predict_fatigue_trend(
        self, person_id: str, start_date: date, days_ahead: int = 7
    ) -> dict:
        """
        Predict fatigue levels for the next N days.

        Projects fatigue based on current schedule and trends.

        Args:
            person_id: Person UUID
            start_date: Date to start prediction from
            days_ahead: Number of days to forecast

        Returns:
            Dict with daily fatigue projections
        """
        person = self.db.query(Person).filter(Person.id == person_id).first()

        if not person or not person.is_resident:
            return {
                "person_id": str(person_id),
                "error": "Person not found or not a resident",
            }

        predictions = []
        current_fatigue = self.calculate_fatigue_score(person_id, start_date)

        for day_offset in range(days_ahead):
            forecast_date = start_date + timedelta(days=day_offset)

            # Get fatigue score for this date
            day_fatigue = self.calculate_fatigue_score(person_id, forecast_date)

            predictions.append({
                "date": forecast_date.isoformat(),
                "fatigue_score": day_fatigue.get("fatigue_score", 0),
                "risk_level": day_fatigue.get("risk_level", "LOW"),
            })

        # Calculate trend
        if len(predictions) >= 2:
            trend_direction = (
                "INCREASING" if predictions[-1]["fatigue_score"] > predictions[0]["fatigue_score"]
                else "DECREASING" if predictions[-1]["fatigue_score"] < predictions[0]["fatigue_score"]
                else "STABLE"
            )
        else:
            trend_direction = "STABLE"

        return {
            "person_id": str(person_id),
            "person_name": person.name,
            "start_date": start_date.isoformat(),
            "days_ahead": days_ahead,
            "current_fatigue": current_fatigue.get("fatigue_score", 0),
            "trend": trend_direction,
            "predictions": predictions,
        }

    def get_high_risk_residents(self, target_date: date, threshold: float = None) -> list[dict]:
        """
        Get list of residents approaching or exceeding fatigue limits.

        Args:
            target_date: Date to check
            threshold: Custom fatigue threshold (default: FATIGUE_THRESHOLD_HIGH)

        Returns:
            List of high-risk residents with their fatigue data
        """
        if threshold is None:
            threshold = self.FATIGUE_THRESHOLD_HIGH

        # Get all residents
        residents = self.db.query(Person).filter(Person.type == "resident").all()

        high_risk = []

        for resident in residents:
            fatigue_data = self.calculate_fatigue_score(resident.id, target_date)

            if fatigue_data.get("fatigue_score", 0) >= threshold:
                recovery = self.get_recovery_time_needed(resident.id, target_date)

                high_risk.append({
                    "person_id": str(resident.id),
                    "person_name": resident.name,
                    "pgy_level": resident.pgy_level,
                    "fatigue_score": fatigue_data.get("fatigue_score"),
                    "risk_level": fatigue_data.get("risk_level"),
                    "recovery_hours_needed": recovery.get("recovery_hours_needed"),
                    "recommended_days_off": recovery.get("recommended_days_off"),
                    "factors": fatigue_data.get("factors"),
                })

        # Sort by fatigue score (highest first)
        high_risk.sort(key=lambda x: x["fatigue_score"], reverse=True)

        return high_risk

    def _calculate_consecutive_days(
        self, assignments: list[Assignment], target_date: date
    ) -> int:
        """Calculate consecutive duty days leading up to target date."""
        if not assignments:
            return 0

        # Get dates with assignments
        dates_worked = set()
        for assignment in assignments:
            block = self.db.query(Block).filter(Block.id == assignment.block_id).first()
            if block:
                dates_worked.add(block.date)

        # Count backwards from target date
        consecutive = 0
        check_date = target_date

        while check_date in dates_worked:
            consecutive += 1
            check_date -= timedelta(days=1)

        return consecutive

    def _count_night_shifts(self, assignments: list[Assignment]) -> int:
        """Count night shifts in assignment list."""
        night_count = 0

        for assignment in assignments:
            block = self.db.query(Block).filter(Block.id == assignment.block_id).first()
            if block and block.time_of_day == "PM":
                night_count += 1

        return night_count

    def _count_weekend_days(self, assignments: list[Assignment]) -> int:
        """Count weekend days worked."""
        weekend_dates = set()

        for assignment in assignments:
            block = self.db.query(Block).filter(Block.id == assignment.block_id).first()
            if block and block.is_weekend:
                weekend_dates.add(block.date)

        return len(weekend_dates)

    def _days_since_last_off(
        self, assignments: list[Assignment], target_date: date
    ) -> int:
        """Calculate days since last day off."""
        if not assignments:
            return 0

        # Get all dates with assignments
        dates_worked = set()
        for assignment in assignments:
            block = self.db.query(Block).filter(Block.id == assignment.block_id).first()
            if block:
                dates_worked.add(block.date)

        # Check backwards from target date to find last day off
        days_since_off = 0
        check_date = target_date

        while check_date in dates_worked and days_since_off < 14:
            days_since_off += 1
            check_date -= timedelta(days=1)

        return days_since_off
