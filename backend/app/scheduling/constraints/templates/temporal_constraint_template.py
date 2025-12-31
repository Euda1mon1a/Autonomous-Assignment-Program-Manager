"""
Temporal Constraint Template

Temporal constraints regulate assignments based on time patterns
(day of week, time of day, date ranges, sequence).

Examples:
    - Wednesday-only constraints
    - Overnight vs. daytime restrictions
    - Recovery period requirements
    - Rotation sequence constraints
"""

from datetime import date
from typing import Any

from app.scheduling.constraints.base import (
    ConstraintPriority,
    ConstraintResult,
    ConstraintType,
    HardConstraint,
    SchedulingContext,
)


class TemporalConstraintTemplate(HardConstraint):
    """
    Template for temporal constraints.

    Temporal constraints enforce patterns based on:
    - Day of week (Monday, Wednesday, Friday, etc.)
    - Time of block (AM, PM, overnight)
    - Date ranges (specific weeks, months)
    - Sequence (e.g., post-call after call)

    Examples:
        >>> constraint = TemporalConstraintTemplate()
        >>> constraint.allowed_days = ['Monday', 'Wednesday', 'Friday']
        >>> constraint.allowed_times = ['AM']  # Morning only
    """

    def __init__(self) -> None:
        """Initialize temporal constraint."""
        super().__init__(
            name="TemporalConstraint",
            constraint_type=ConstraintType.ROTATION,
            priority=ConstraintPriority.HIGH,
        )
        # Temporal parameters
        self.allowed_days = None  # ['Monday', 'Wednesday', ...]
        self.forbidden_days = None  # ['Sunday', 'Saturday']
        self.allowed_times = None  # ['AM', 'PM']
        self.date_range = None  # (start_date, end_date)
        self.recovery_days = 0  # Days required after event

    def _is_allowed_date(self, date_obj: date) -> bool:
        """Check if date falls in allowed range."""
        if self.date_range is None:
            return True
        start, end = self.date_range
        return start <= date_obj <= end

    def _get_day_name(self, date_obj: date) -> str:
        """Get day name from date."""
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday',
                'Friday', 'Saturday', 'Sunday']
        return days[date_obj.weekday()]

    def _is_allowed_day(self, date_obj: date) -> bool:
        """Check if day of week is allowed."""
        day_name = self._get_day_name(date_obj)

        if self.forbidden_days and day_name in self.forbidden_days:
            return False

        if self.allowed_days and day_name not in self.allowed_days:
            return False

        return True

    def _is_allowed_time(self, block: Any) -> bool:
        """Check if block time is allowed."""
        if self.allowed_times is None:
            return True
        return block.time_period in self.allowed_times

    def add_to_cpsat(
        self,
        model: Any,
        variables: dict[str, Any],
        context: SchedulingContext,
    ) -> None:
        """Add temporal constraint to CP-SAT model."""
        x = variables.get("assignments", {})

        for resident in context.residents:
            r_i = context.resident_idx[resident.id]

            for block in context.blocks:
                b_i = context.block_idx[block.id]

                # Check temporal constraints
                if not self._is_allowed_date(block.date):
                    model.Add(x[r_i, b_i] == 0)

                if not self._is_allowed_day(block.date):
                    model.Add(x[r_i, b_i] == 0)

                if not self._is_allowed_time(block):
                    model.Add(x[r_i, b_i] == 0)

    def add_to_pulp(
        self,
        model: Any,
        variables: dict[str, Any],
        context: SchedulingContext,
    ) -> None:
        """Add temporal constraint to PuLP model."""
        x = variables.get("assignments", {})

        for resident in context.residents:
            r_i = context.resident_idx[resident.id]

            for block in context.blocks:
                b_i = context.block_idx[block.id]

                # Check temporal constraints
                if not self._is_allowed_date(block.date):
                    model += x[r_i, b_i] == 0

                if not self._is_allowed_day(block.date):
                    model += x[r_i, b_i] == 0

                if not self._is_allowed_time(block):
                    model += x[r_i, b_i] == 0

    def validate(
        self,
        assignments: list[Any],
        context: SchedulingContext,
    ) -> ConstraintResult:
        """Validate temporal constraints."""
        violations = []

        for assignment in assignments:
            block = context.blocks[context.block_idx[assignment.block_id]]

            if not self._is_allowed_date(block.date):
                violations.append(
                    type('ConstraintViolation', (), {
                        'constraint_name': self.name,
                        'constraint_type': self.constraint_type,
                        'severity': 'HIGH',
                        'message': f'Assignment outside allowed date range',
                        'person_id': assignment.person_id,
                        'block_id': assignment.block_id,
                    })()
                )

            if not self._is_allowed_day(block.date):
                violations.append(
                    type('ConstraintViolation', (), {
                        'constraint_name': self.name,
                        'constraint_type': self.constraint_type,
                        'severity': 'HIGH',
                        'message': f'Assignment on forbidden day of week',
                        'person_id': assignment.person_id,
                        'block_id': assignment.block_id,
                    })()
                )

        return ConstraintResult(
            satisfied=len(violations) == 0,
            violations=violations,
        )
