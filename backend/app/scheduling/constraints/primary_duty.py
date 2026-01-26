"""
Faculty Primary Duty Clinic Constraints.

This module contains constraints that enforce faculty clinic assignment rules
based on Airtable primary duty configuration data.

The primary duty configuration provides more granular control than role-based
defaults, including:
- Per-duty clinic half-day min/max requirements
- Day-of-week availability
- Allowed clinic templates

Classes:
    - PrimaryDutyConfig: Data class for parsing Airtable primary duty records
    - FacultyPrimaryDutyClinicConstraint: Enforce min/max clinic assignments (hard)
    - FacultyDayAvailabilityConstraint: Enforce day-of-week availability (hard)
"""

import json
import logging
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date, timedelta
from pathlib import Path
from typing import Any
from uuid import UUID

from .base import (
    ConstraintPriority,
    ConstraintResult,
    ConstraintType,
    ConstraintViolation,
    HardConstraint,
    SchedulingContext,
    SoftConstraint,
)

logger = logging.getLogger(__name__)


@dataclass
class PrimaryDutyConfig:
    """
    Configuration for a faculty primary duty.

    Parsed from Airtable primary_duties table export.

    Attributes:
        duty_id: Airtable record ID (e.g., "recgREn5x6J5HN5pz")
        duty_name: Human-readable name (e.g., "Faculty Alpha", "Program Director")
        clinic_min_per_week: Minimum clinic half-days per week (0 = no requirement)
        clinic_max_per_week: Maximum clinic half-days per week
        available_days: Set of available weekdays (0=Mon, 1=Tue, ..., 4=Fri)
        allowed_clinic_templates: Set of allowed clinic template Airtable IDs
        faculty_ids: List of faculty Airtable IDs linked to this duty
    """

    duty_id: str
    duty_name: str
    clinic_min_per_week: int = 0
    clinic_max_per_week: int = 10  # Default high max
    available_days: set[int] = field(default_factory=lambda: {0, 1, 2, 3, 4})
    allowed_clinic_templates: set[str] = field(default_factory=set)
    faculty_ids: list[str] = field(default_factory=list)

    # Additional constraints from Airtable (for future use)
    inpatient_weeks_min: int = 0
    inpatient_weeks_max: int = 0
    gme_min_per_week: int = 0
    gme_max_per_week: int = 0
    resident_supervision_min: int = 0
    resident_supervision_max: int = 0

    @classmethod
    def from_airtable_record(cls, record: dict[str, Any]) -> "PrimaryDutyConfig":
        """
        Create PrimaryDutyConfig from an Airtable record.

        Args:
            record: Single record from Airtable primary_duties table

        Returns:
            PrimaryDutyConfig instance
        """
        fields = record.get("fields", {})

        # Parse day availability
        available_days: set[int] = set()
        day_mapping = {
            "availableMonday": 0,
            "availableTuesday": 1,
            "availableWednesday": 2,
            "availableThursday": 3,
            "availableFriday": 4,
        }
        for field_name, day_num in day_mapping.items():
            if fields.get(field_name, False):
                available_days.add(day_num)

        # If no days specified, default to all weekdays
        if not available_days:
            available_days = {0, 1, 2, 3, 4}

        return cls(
            duty_id=record.get("id", ""),
            duty_name=fields.get("primaryDuty", "Unknown"),
            clinic_min_per_week=fields.get("Clinic Minimum Half-Days Per Week", 0),
            clinic_max_per_week=fields.get("Clinic Maximum Half-Days Per Week", 10),
            available_days=available_days,
            allowed_clinic_templates=set(fields.get("attendingClinicTemplates", [])),
            faculty_ids=fields.get("Faculty", []),
            inpatient_weeks_min=fields.get("Inpatient Weeks Minimum", 0),
            inpatient_weeks_max=fields.get("Inpatient Weeks Maximum", 0),
            gme_min_per_week=fields.get(
                "Minimum Graduate Medical Education Half-Day Per Week", 0
            ),
            gme_max_per_week=fields.get(
                "Maximum Graduate Medical Education Half-Days Per Week", 0
            ),
            resident_supervision_min=fields.get(
                "Resident Supervision Minimum Half-Days Per Week", 0
            ),
            resident_supervision_max=fields.get(
                "Resident Supervision Maximum Half-Days Per Week copy", 0
            ),
        )


def load_primary_duties_config(
    json_path: str | Path | None = None,
) -> dict[str, PrimaryDutyConfig]:
    """
    Load primary duty configurations from JSON file.

    Args:
        json_path: Path to sanitized_primary_duties.json. If None, uses default.

    Returns:
        Dict mapping duty_name to PrimaryDutyConfig
    """
    if json_path is None:
        # Default to sanitized file in docs/schedules
        json_path = (
            Path(__file__).parents[4]
            / "docs"
            / "schedules"
            / "sanitized_primary_duties.json"
        )

    try:
        with open(json_path) as f:
            data = json.load(f)

        configs: dict[str, PrimaryDutyConfig] = {}
        for record in data.get("records", []):
            config = PrimaryDutyConfig.from_airtable_record(record)
            configs[config.duty_name] = config
            # Also index by duty_id for lookup
            configs[config.duty_id] = config

        logger.info(f"Loaded {len(data.get('records', []))} primary duty configs")
        return configs

    except FileNotFoundError:
        logger.warning(f"Primary duties config not found at {json_path}")
        return {}
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in primary duties config: {e}")
        return {}


class FacultyPrimaryDutyClinicConstraint(HardConstraint):
    """
    Enforces clinic half-day requirements based on primary duty configuration.

    This constraint uses Airtable primary duty data to enforce:
    - Minimum clinic half-days per week (hard requirement for coverage)
    - Maximum clinic half-days per week (hard limit)

    The min requirement ensures faculty fulfill their clinical duties.
    The max requirement prevents over-scheduling.

    Unlike FacultyRoleClinicConstraint which uses hardcoded limits per role,
    this constraint uses per-faculty duty configurations which can vary.
    """

    def __init__(
        self,
        duty_configs: dict[str, PrimaryDutyConfig] | None = None,
        json_path: str | Path | None = None,
    ) -> None:
        """
        Initialize the constraint.

        Args:
            duty_configs: Pre-loaded duty configurations, or
            json_path: Path to JSON file to load configs from
        """
        super().__init__(
            name="FacultyPrimaryDutyClinic",
            constraint_type=ConstraintType.CAPACITY,
            priority=ConstraintPriority.HIGH,
        )
        self._duty_configs = duty_configs or load_primary_duties_config(json_path)

    def get_faculty_duty_config(self, faculty: Any) -> PrimaryDutyConfig | None:
        """
        Get primary duty config for a faculty member.

        Looks up by primary_duty field on faculty object.
        """
        if not hasattr(faculty, "primary_duty") or not faculty.primary_duty:
            return None
        return self._duty_configs.get(faculty.primary_duty)

    def add_to_cpsat(
        self,
        model: Any,
        variables: dict[str, Any],
        context: SchedulingContext,
    ) -> None:
        """
        Add primary duty clinic constraints to CP-SAT model.

        For each faculty with a primary duty config:
        - Adds min constraint: sum(clinic_vars) >= min_per_week
        - Adds max constraint: sum(clinic_vars) <= max_per_week
        """
        template_vars = variables.get("template_assignments", {})
        if not template_vars:
            logger.debug("No template_assignments variables found")
            return

        # Identify clinic templates
        clinic_template_ids = {
            t.id
            for t in context.templates
            if hasattr(t, "rotation_type") and t.rotation_type == "outpatient"
        }

        if not clinic_template_ids:
            logger.debug("No outpatient templates found")
            return

        constraints_added = 0

        for faculty in context.faculty:
            config = self.get_faculty_duty_config(faculty)
            if not config:
                continue

            f_i = context.faculty_idx.get(faculty.id)
            if f_i is None:
                continue

            # Group blocks by week
            weeks = self._group_blocks_by_week(context.blocks)

            for week_start, week_blocks in weeks.items():
                week_clinic_vars = []

                for block in week_blocks:
                    b_i = context.block_idx[block.id]
                    for template in context.templates:
                        if template.id not in clinic_template_ids:
                            continue
                        t_i = context.template_idx[template.id]
                        if (f_i, b_i, t_i) in template_vars:
                            week_clinic_vars.append(template_vars[f_i, b_i, t_i])

                if not week_clinic_vars:
                    continue

                week_sum = sum(week_clinic_vars)

                # Minimum constraint (coverage requirement)
                if config.clinic_min_per_week > 0:
                    model.Add(week_sum >= config.clinic_min_per_week)
                    constraints_added += 1

                # Maximum constraint
                if config.clinic_max_per_week < 10:  # Only if explicitly limited
                    model.Add(week_sum <= config.clinic_max_per_week)
                    constraints_added += 1

        logger.debug(f"Added {constraints_added} primary duty clinic constraints")

    def add_to_pulp(
        self,
        model: Any,
        variables: dict[str, Any],
        context: SchedulingContext,
    ) -> None:
        """Add primary duty clinic constraints to PuLP model."""
        import pulp

        template_vars = variables.get("template_assignments", {})
        if not template_vars:
            return

        clinic_template_ids = {
            t.id
            for t in context.templates
            if hasattr(t, "rotation_type") and t.rotation_type == "outpatient"
        }

        if not clinic_template_ids:
            return

        constraint_count = 0

        for faculty in context.faculty:
            config = self.get_faculty_duty_config(faculty)
            if not config:
                continue

            f_i = context.faculty_idx.get(faculty.id)
            if f_i is None:
                continue

            weeks = self._group_blocks_by_week(context.blocks)

            for week_start, week_blocks in weeks.items():
                week_clinic_vars = []

                for block in week_blocks:
                    b_i = context.block_idx[block.id]
                    for template in context.templates:
                        if template.id not in clinic_template_ids:
                            continue
                        t_i = context.template_idx[template.id]
                        if (f_i, b_i, t_i) in template_vars:
                            week_clinic_vars.append(template_vars[f_i, b_i, t_i])

                if not week_clinic_vars:
                    continue

                # Minimum constraint
                if config.clinic_min_per_week > 0:
                    model += (
                        pulp.lpSum(week_clinic_vars) >= config.clinic_min_per_week,
                        f"duty_clinic_min_{f_i}_{constraint_count}",
                    )
                    constraint_count += 1

                # Maximum constraint
                if config.clinic_max_per_week < 10:
                    model += (
                        pulp.lpSum(week_clinic_vars) <= config.clinic_max_per_week,
                        f"duty_clinic_max_{f_i}_{constraint_count}",
                    )
                    constraint_count += 1

    def validate(
        self,
        assignments: list[Any],
        context: SchedulingContext,
    ) -> ConstraintResult:
        """
        Validate faculty clinic assignments against primary duty requirements.
        """
        violations: list[ConstraintViolation] = []

        faculty_by_id = {f.id: f for f in context.faculty}
        block_by_id = {b.id: b for b in context.blocks}

        # Identify clinic templates
        clinic_template_ids = {
            t.id
            for t in context.templates
            if hasattr(t, "rotation_type") and t.rotation_type == "outpatient"
        }

        # Count clinic assignments by faculty and week
        faculty_weekly_counts: dict[UUID, dict[date, int]] = defaultdict(
            lambda: defaultdict(int)
        )

        for a in assignments:
            if a.person_id not in faculty_by_id:
                continue
            if a.rotation_template_id not in clinic_template_ids:
                continue

            block = block_by_id.get(a.block_id)
            if not block:
                continue

            week_start = self._get_week_start(block.date)
            faculty_weekly_counts[a.person_id][week_start] += 1

        # Check constraints
        for faculty in context.faculty:
            config = self.get_faculty_duty_config(faculty)
            if not config:
                continue

            weekly_counts = faculty_weekly_counts.get(faculty.id, {})

            # Get all weeks in the scheduling period
            weeks = self._group_blocks_by_week(context.blocks)

            for week_start in weeks:
                count = weekly_counts.get(week_start, 0)

                # Check minimum
                if count < config.clinic_min_per_week:
                    violations.append(
                        ConstraintViolation(
                            constraint_name=self.name,
                            constraint_type=self.constraint_type,
                            severity="HIGH",
                            message=(
                                f"{faculty.name} ({config.duty_name}): "
                                f"{count} clinic half-days in week of {week_start}, "
                                f"requires minimum {config.clinic_min_per_week}"
                            ),
                            person_id=faculty.id,
                            details={
                                "week_start": str(week_start),
                                "count": count,
                                "minimum": config.clinic_min_per_week,
                                "duty": config.duty_name,
                            },
                        )
                    )

                # Check maximum
                if count > config.clinic_max_per_week:
                    violations.append(
                        ConstraintViolation(
                            constraint_name=self.name,
                            constraint_type=self.constraint_type,
                            severity="HIGH",
                            message=(
                                f"{faculty.name} ({config.duty_name}): "
                                f"{count} clinic half-days in week of {week_start}, "
                                f"exceeds maximum {config.clinic_max_per_week}"
                            ),
                            person_id=faculty.id,
                            details={
                                "week_start": str(week_start),
                                "count": count,
                                "maximum": config.clinic_max_per_week,
                                "duty": config.duty_name,
                            },
                        )
                    )

        return ConstraintResult(
            satisfied=len(violations) == 0,
            violations=violations,
        )

    def _group_blocks_by_week(self, blocks: list[Any]) -> dict[date, list[Any]]:
        """Group blocks by week (starting Monday)."""
        weeks: dict[date, list[Any]] = defaultdict(list)
        for block in blocks:
            week_start = self._get_week_start(block.date)
            weeks[week_start].append(block)
        return weeks

    def _get_week_start(self, any_date: date) -> date:
        """Get Monday of the week containing the date."""
        days_since_monday = any_date.weekday()
        return any_date - timedelta(days=days_since_monday)


class FacultyDayAvailabilityConstraint(HardConstraint):
    """
    Enforces day-of-week availability based on primary duty configuration.

    Faculty can only be assigned to clinic sessions on their available days.
    This prevents scheduling conflicts with administrative duties, teaching, etc.
    """

    def __init__(
        self,
        duty_configs: dict[str, PrimaryDutyConfig] | None = None,
        json_path: str | Path | None = None,
    ) -> None:
        """Initialize the constraint."""
        super().__init__(
            name="FacultyDayAvailability",
            constraint_type=ConstraintType.AVAILABILITY,
            priority=ConstraintPriority.CRITICAL,
        )
        self._duty_configs = duty_configs or load_primary_duties_config(json_path)

    def get_faculty_duty_config(self, faculty: Any) -> PrimaryDutyConfig | None:
        """Get primary duty config for a faculty member."""
        if not hasattr(faculty, "primary_duty") or not faculty.primary_duty:
            return None
        return self._duty_configs.get(faculty.primary_duty)

    def add_to_cpsat(
        self,
        model: Any,
        variables: dict[str, Any],
        context: SchedulingContext,
    ) -> None:
        """
        Block clinic assignments on unavailable days in CP-SAT model.
        """
        template_vars = variables.get("template_assignments", {})
        if not template_vars:
            return

        clinic_template_ids = {
            t.id
            for t in context.templates
            if hasattr(t, "rotation_type") and t.rotation_type == "outpatient"
        }

        if not clinic_template_ids:
            return

        blocked_count = 0

        for faculty in context.faculty:
            config = self.get_faculty_duty_config(faculty)
            if not config:
                continue

            f_i = context.faculty_idx.get(faculty.id)
            if f_i is None:
                continue

            for block in context.blocks:
                # Check if block's day is available
                day_of_week = block.date.weekday()
                if day_of_week in config.available_days:
                    continue  # Available, no constraint needed

                # Block assignments on unavailable days
                b_i = context.block_idx[block.id]
                for template in context.templates:
                    if template.id not in clinic_template_ids:
                        continue
                    t_i = context.template_idx[template.id]
                    if (f_i, b_i, t_i) in template_vars:
                        model.Add(template_vars[f_i, b_i, t_i] == 0)
                        blocked_count += 1

        logger.debug(f"Blocked {blocked_count} assignments on unavailable days")

    def add_to_pulp(
        self,
        model: Any,
        variables: dict[str, Any],
        context: SchedulingContext,
    ) -> None:
        """Block clinic assignments on unavailable days in PuLP model."""
        template_vars = variables.get("template_assignments", {})
        if not template_vars:
            return

        clinic_template_ids = {
            t.id
            for t in context.templates
            if hasattr(t, "rotation_type") and t.rotation_type == "outpatient"
        }

        if not clinic_template_ids:
            return

        constraint_count = 0

        for faculty in context.faculty:
            config = self.get_faculty_duty_config(faculty)
            if not config:
                continue

            f_i = context.faculty_idx.get(faculty.id)
            if f_i is None:
                continue

            for block in context.blocks:
                day_of_week = block.date.weekday()
                if day_of_week in config.available_days:
                    continue

                b_i = context.block_idx[block.id]
                for template in context.templates:
                    if template.id not in clinic_template_ids:
                        continue
                    t_i = context.template_idx[template.id]
                    if (f_i, b_i, t_i) in template_vars:
                        model += (
                            template_vars[f_i, b_i, t_i] == 0,
                            f"day_avail_{f_i}_{b_i}_{constraint_count}",
                        )
                        constraint_count += 1

    def validate(
        self,
        assignments: list[Any],
        context: SchedulingContext,
    ) -> ConstraintResult:
        """Validate faculty are not assigned on unavailable days."""
        violations: list[ConstraintViolation] = []

        faculty_by_id = {f.id: f for f in context.faculty}
        block_by_id = {b.id: b for b in context.blocks}

        clinic_template_ids = {
            t.id
            for t in context.templates
            if hasattr(t, "rotation_type") and t.rotation_type == "outpatient"
        }

        day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]

        for a in assignments:
            faculty = faculty_by_id.get(a.person_id)
            if not faculty:
                continue

            if a.rotation_template_id not in clinic_template_ids:
                continue

            config = self.get_faculty_duty_config(faculty)
            if not config:
                continue

            block = block_by_id.get(a.block_id)
            if not block:
                continue

            day_of_week = block.date.weekday()
            if day_of_week not in config.available_days:
                day_name = day_names[day_of_week] if day_of_week < 5 else "Weekend"
                violations.append(
                    ConstraintViolation(
                        constraint_name=self.name,
                        constraint_type=self.constraint_type,
                        severity="CRITICAL",
                        message=(
                            f"{faculty.name} assigned to clinic on {day_name} "
                            f"({block.date}), but not available that day"
                        ),
                        person_id=faculty.id,
                        block_id=block.id,
                        details={
                            "date": str(block.date),
                            "day_of_week": day_of_week,
                            "available_days": list(config.available_days),
                            "duty": config.duty_name,
                        },
                    )
                )

        return ConstraintResult(
            satisfied=len(violations) == 0,
            violations=violations,
        )


class FacultyClinicEquitySoftConstraint(SoftConstraint):
    """
    Soft constraint that optimizes toward target clinic coverage.

    Instead of hard min/max, this provides weighted penalties for deviation
    from target. Use when you want to optimize but not strictly require.
    """

    def __init__(
        self,
        weight: float = 15.0,
        duty_configs: dict[str, PrimaryDutyConfig] | None = None,
        json_path: str | Path | None = None,
    ) -> None:
        """Initialize the constraint."""
        super().__init__(
            name="FacultyClinicEquity",
            constraint_type=ConstraintType.EQUITY,
            weight=weight,
            priority=ConstraintPriority.MEDIUM,
        )
        self._duty_configs = duty_configs or load_primary_duties_config(json_path)

    def get_faculty_duty_config(self, faculty: Any) -> PrimaryDutyConfig | None:
        """Get primary duty config for a faculty member."""
        if not hasattr(faculty, "primary_duty") or not faculty.primary_duty:
            return None
        return self._duty_configs.get(faculty.primary_duty)

    def add_to_cpsat(
        self,
        model: Any,
        variables: dict[str, Any],
        context: SchedulingContext,
    ) -> None:
        """Add clinic equity objective to CP-SAT model."""
        template_vars = variables.get("template_assignments", {})
        if not template_vars:
            return

        clinic_template_ids = {
            t.id
            for t in context.templates
            if hasattr(t, "rotation_type") and t.rotation_type == "outpatient"
        }

        if not clinic_template_ids:
            return

        total_deviation = 0

        for faculty in context.faculty:
            config = self.get_faculty_duty_config(faculty)
            if not config:
                continue

            f_i = context.faculty_idx.get(faculty.id)
            if f_i is None:
                continue

            # Calculate target as midpoint of min/max
            target = (config.clinic_min_per_week + config.clinic_max_per_week) // 2
            if target == 0:
                continue

            weeks = self._group_blocks_by_week(context.blocks)

            for week_start, week_blocks in weeks.items():
                week_clinic_vars = []

                for block in week_blocks:
                    b_i = context.block_idx[block.id]
                    for template in context.templates:
                        if template.id not in clinic_template_ids:
                            continue
                        t_i = context.template_idx[template.id]
                        if (f_i, b_i, t_i) in template_vars:
                            week_clinic_vars.append(template_vars[f_i, b_i, t_i])

                if not week_clinic_vars:
                    continue

                week_sum = sum(week_clinic_vars)

                # Create deviation variable
                deviation = model.NewIntVar(
                    0,
                    len(context.blocks),
                    f"clinic_dev_{f_i}_{week_start}",
                )
                model.Add(deviation >= week_sum - target)
                model.Add(deviation >= target - week_sum)
                total_deviation += deviation

        if total_deviation:
            variables["clinic_equity_penalty"] = total_deviation

    def add_to_pulp(
        self,
        model: Any,
        variables: dict[str, Any],
        context: SchedulingContext,
    ) -> None:
        """Add clinic equity objective to PuLP model."""
        import pulp

        template_vars = variables.get("template_assignments", {})
        if not template_vars:
            return

        clinic_template_ids = {
            t.id
            for t in context.templates
            if hasattr(t, "rotation_type") and t.rotation_type == "outpatient"
        }

        if not clinic_template_ids:
            return

        deviations = []

        for faculty in context.faculty:
            config = self.get_faculty_duty_config(faculty)
            if not config:
                continue

            f_i = context.faculty_idx.get(faculty.id)
            if f_i is None:
                continue

            target = (config.clinic_min_per_week + config.clinic_max_per_week) // 2
            if target == 0:
                continue

            weeks = self._group_blocks_by_week(context.blocks)

            for week_idx, (week_start, week_blocks) in enumerate(weeks.items()):
                week_clinic_vars = []

                for block in week_blocks:
                    b_i = context.block_idx[block.id]
                    for template in context.templates:
                        if template.id not in clinic_template_ids:
                            continue
                        t_i = context.template_idx[template.id]
                        if (f_i, b_i, t_i) in template_vars:
                            week_clinic_vars.append(template_vars[f_i, b_i, t_i])

                if not week_clinic_vars:
                    continue

                week_sum = pulp.lpSum(week_clinic_vars)

                dev_pos = pulp.LpVariable(
                    f"clinic_dev_pos_{f_i}_{week_idx}", lowBound=0, cat="Integer"
                )
                dev_neg = pulp.LpVariable(
                    f"clinic_dev_neg_{f_i}_{week_idx}", lowBound=0, cat="Integer"
                )

                model += (
                    week_sum - target == dev_pos - dev_neg,
                    f"clinic_dev_def_{f_i}_{week_idx}",
                )

                deviations.append(dev_pos + dev_neg)

        if deviations:
            variables["clinic_equity_penalty"] = pulp.lpSum(deviations)

    def validate(
        self,
        assignments: list[Any],
        context: SchedulingContext,
    ) -> ConstraintResult:
        """Calculate equity penalty for clinic assignments."""
        faculty_by_id = {f.id: f for f in context.faculty}
        block_by_id = {b.id: b for b in context.blocks}

        clinic_template_ids = {
            t.id
            for t in context.templates
            if hasattr(t, "rotation_type") and t.rotation_type == "outpatient"
        }

        # Count assignments
        faculty_weekly_counts: dict[UUID, dict[date, int]] = defaultdict(
            lambda: defaultdict(int)
        )

        for a in assignments:
            if a.person_id not in faculty_by_id:
                continue
            if a.rotation_template_id not in clinic_template_ids:
                continue

            block = block_by_id.get(a.block_id)
            if not block:
                continue

            week_start = self._get_week_start(block.date)
            faculty_weekly_counts[a.person_id][week_start] += 1

        # Calculate total deviation
        total_penalty = 0.0

        for faculty in context.faculty:
            config = self.get_faculty_duty_config(faculty)
            if not config:
                continue

            target = (config.clinic_min_per_week + config.clinic_max_per_week) // 2
            if target == 0:
                continue

            weekly_counts = faculty_weekly_counts.get(faculty.id, {})
            weeks = self._group_blocks_by_week(context.blocks)

            for week_start in weeks:
                count = weekly_counts.get(week_start, 0)
                deviation = abs(count - target)
                total_penalty += deviation * self.weight

        return ConstraintResult(
            satisfied=True,  # Soft constraint
            violations=[],
            penalty=total_penalty,
        )

    def _group_blocks_by_week(self, blocks: list[Any]) -> dict[date, list[Any]]:
        """Group blocks by week (starting Monday)."""
        weeks: dict[date, list[Any]] = defaultdict(list)
        for block in blocks:
            week_start = self._get_week_start(block.date)
            weeks[week_start].append(block)
        return weeks

    def _get_week_start(self, any_date: date) -> date:
        """Get Monday of the week containing the date."""
        days_since_monday = any_date.weekday()
        return any_date - timedelta(days=days_since_monday)
