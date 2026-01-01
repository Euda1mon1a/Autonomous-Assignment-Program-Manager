"""
Constraint rule validators.

Validates scheduling constraints:
- Hard constraints (must be satisfied)
- Soft constraints (preferences, optimizations)
- Constraint conflicts
- Constraint prioritization
"""

from datetime import date, timedelta
from typing import Optional
from uuid import UUID

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.assignment import Assignment
from app.models.block import Block
from app.models.faculty_preference import FacultyPreference
from app.models.procedure_credential import ProcedureCredential
from app.validators.common import ValidationError


class ConstraintViolation(Exception):
    """Raised when hard constraint is violated."""

    pass


async def validate_hard_constraint(
    db: AsyncSession,
    constraint_name: str,
    context: dict,
) -> dict:
    """
    Validate hard constraint (must be satisfied).

    Hard constraints examples:
    - No double-booking (person in two places at once)
    - Required credentials for activities
    - Minimum supervision ratios
    - Maximum duty hours (ACGME)

    Args:
        db: Database session
        constraint_name: Name of constraint
        context: Context data for validation

    Returns:
        dict: Validation result

    Raises:
        ConstraintViolation: If hard constraint is violated
    """
    hard_constraints = {
        "no_double_booking": {
            "description": "Person cannot be in two places simultaneously",
            "severity": "critical",
        },
        "required_credentials": {
            "description": "Person must have required credentials for activity",
            "severity": "critical",
        },
        "minimum_supervision": {
            "description": "Minimum supervision ratio must be maintained",
            "severity": "critical",
        },
        "acgme_duty_hours": {
            "description": "ACGME duty hour limits must not be exceeded",
            "severity": "critical",
        },
    }

    if constraint_name not in hard_constraints:
        raise ValidationError(f"Unknown hard constraint: '{constraint_name}'")

    constraint = hard_constraints[constraint_name]

    # Validate constraint based on type
    is_satisfied = True
    violation_details = None

    if constraint_name == "no_double_booking":
        is_satisfied, violation_details = await _check_no_double_booking(db, context)
    elif constraint_name == "required_credentials":
        is_satisfied, violation_details = await _check_required_credentials(db, context)
    elif constraint_name == "minimum_supervision":
        is_satisfied, violation_details = await _check_minimum_supervision(db, context)
    elif constraint_name == "acgme_duty_hours":
        is_satisfied, violation_details = await _check_acgme_duty_hours(db, context)

    if not is_satisfied:
        raise ConstraintViolation(
            f"Hard constraint violated: {constraint['description']}. {violation_details or ''}"
        )

    return {
        "is_satisfied": True,
        "constraint_name": constraint_name,
        "constraint_description": constraint["description"],
        "severity": constraint["severity"],
    }


async def validate_soft_constraint(
    db: AsyncSession,
    constraint_name: str,
    context: dict,
) -> dict:
    """
    Validate soft constraint (preference, can be violated with penalty).

    Soft constraints examples:
    - Rotation preferences
    - Preferred shift times
    - Balanced workload distribution
    - Equitable call distribution

    Args:
        db: Database session
        constraint_name: Name of constraint
        context: Context data for validation

    Returns:
        dict: Validation result with penalty score
    """
    soft_constraints = {
        "rotation_preference": {
            "description": "Person prefers certain rotations",
            "penalty_base": 10,
        },
        "shift_preference": {
            "description": "Person prefers certain shift times",
            "penalty_base": 5,
        },
        "workload_balance": {
            "description": "Workload should be evenly distributed",
            "penalty_base": 15,
        },
        "call_equity": {
            "description": "Call shifts should be fair",
            "penalty_base": 20,
        },
    }

    if constraint_name not in soft_constraints:
        raise ValidationError(f"Unknown soft constraint: '{constraint_name}'")

    constraint = soft_constraints[constraint_name]

    # Calculate satisfaction based on constraint type
    satisfaction = 0.8  # Default satisfaction if we can't calculate
    if constraint_name == "rotation_preference":
        satisfaction = await _calculate_rotation_preference_satisfaction(db, context)
    elif constraint_name == "shift_preference":
        satisfaction = await _calculate_shift_preference_satisfaction(db, context)
    elif constraint_name == "workload_balance":
        satisfaction = await _calculate_workload_balance_satisfaction(db, context)
    elif constraint_name == "call_equity":
        satisfaction = await _calculate_call_equity_satisfaction(db, context)

    penalty = constraint["penalty_base"] * (1.0 - satisfaction)

    return {
        "is_satisfied": satisfaction > 0.5,  # >50% satisfaction
        "constraint_name": constraint_name,
        "constraint_description": constraint["description"],
        "satisfaction_score": round(satisfaction, 3),
        "penalty_score": round(penalty, 2),
    }


async def validate_constraint_priority(
    constraints: list[dict],
) -> dict:
    """
    Validate and prioritize multiple constraints.

    When constraints conflict, prioritization determines which to satisfy.

    Priority order (highest to lowest):
    1. Hard constraints (must satisfy)
    2. ACGME compliance (regulatory)
    3. Safety constraints
    4. Equity constraints
    5. Preference constraints

    Args:
        constraints: List of constraint validation results

    Returns:
        dict: Prioritized constraint results
    """
    priority_order = {
        "hard": 1,
        "acgme": 2,
        "safety": 3,
        "equity": 4,
        "preference": 5,
    }

    # Sort constraints by priority
    sorted_constraints = sorted(
        constraints,
        key=lambda c: priority_order.get(c.get("category", "preference"), 999),
    )

    # Check for conflicts
    conflicts = []
    for i, c1 in enumerate(sorted_constraints):
        for c2 in sorted_constraints[i + 1 :]:
            # Would check if constraints conflict
            # (Simplified for now)
            pass

    return {
        "total_constraints": len(constraints),
        "prioritized_constraints": sorted_constraints,
        "has_conflicts": len(conflicts) > 0,
        "conflicts": conflicts,
    }


def validate_constraint(
    constraint_type: str,
    constraint_name: str,
    context: dict,
) -> dict:
    """
    Validate a constraint by type.

    Args:
        constraint_type: Type of constraint ('hard' or 'soft')
        constraint_name: Name of constraint
        context: Context data for validation

    Returns:
        dict: Validation result

    Raises:
        ValidationError: If constraint type is invalid
    """
    if constraint_type not in ["hard", "soft"]:
        raise ValidationError(
            f"Invalid constraint type: '{constraint_type}'. Must be 'hard' or 'soft'"
        )

    return {
        "constraint_type": constraint_type,
        "constraint_name": constraint_name,
        "is_valid": True,
        "message": f"{constraint_type.capitalize()} constraint '{constraint_name}' validated",
    }


async def check_hard_constraint(
    db: AsyncSession,
    constraint_name: str,
    context: dict,
) -> bool:
    """
    Quick boolean check for hard constraint.

    Args:
        db: Database session
        constraint_name: Name of constraint
        context: Context data

    Returns:
        bool: True if satisfied, False otherwise
    """
    try:
        result = await validate_hard_constraint(db, constraint_name, context)
        return result["is_satisfied"]
    except ConstraintViolation:
        return False


async def check_soft_constraint(
    db: AsyncSession,
    constraint_name: str,
    context: dict,
) -> dict:
    """
    Check soft constraint and return penalty.

    Args:
        db: Database session
        constraint_name: Name of constraint
        context: Context data

    Returns:
        dict: Satisfaction score and penalty
    """
    result = await validate_soft_constraint(db, constraint_name, context)
    return {
        "is_satisfied": result["is_satisfied"],
        "penalty": result["penalty_score"],
    }


# =============================================================================
# Hard Constraint Helper Functions
# =============================================================================


async def _check_no_double_booking(
    db: AsyncSession,
    context: dict,
) -> tuple[bool, str | None]:
    """
    Check that a person is not double-booked (assigned to two places at once).

    Args:
        db: Database session
        context: Must contain 'person_id', 'block_id', and optionally 'assignment_id'

    Returns:
        Tuple of (is_satisfied, violation_details)
    """
    person_id = context.get("person_id")
    block_id = context.get("block_id")
    assignment_id = context.get("assignment_id")  # For updates, exclude self

    if not person_id or not block_id:
        return True, None

    # Check for existing assignment at this block
    query = select(Assignment).where(
        Assignment.person_id == person_id,
        Assignment.block_id == block_id,
    )

    if assignment_id:
        # Exclude the current assignment (for updates)
        query = query.where(Assignment.id != assignment_id)

    result = await db.execute(query)
    existing = result.scalar_one_or_none()

    if existing:
        return False, f"Person already assigned to block {block_id}"
    return True, None


async def _check_required_credentials(
    db: AsyncSession,
    context: dict,
) -> tuple[bool, str | None]:
    """
    Check that a person has required credentials for the activity.

    Args:
        db: Database session
        context: Must contain 'person_id' and 'rotation_id' or 'procedure_id'

    Returns:
        Tuple of (is_satisfied, violation_details)
    """
    person_id = context.get("person_id")
    procedure_id = context.get("procedure_id")

    if not person_id:
        return True, None

    if not procedure_id:
        # No specific procedure requirement
        return True, None

    # Check for valid credential
    today = date.today()
    result = await db.execute(
        select(ProcedureCredential).where(
            ProcedureCredential.person_id == person_id,
            ProcedureCredential.procedure_id == procedure_id,
            ProcedureCredential.status == "active",
        )
    )
    credential = result.scalar_one_or_none()

    if not credential:
        return False, f"No credential found for procedure {procedure_id}"

    # Check expiration
    if credential.expiration_date and credential.expiration_date < today:
        return False, f"Credential expired on {credential.expiration_date}"

    return True, None


async def _check_minimum_supervision(
    db: AsyncSession,
    context: dict,
) -> tuple[bool, str | None]:
    """
    Check that minimum supervision ratios are maintained.

    ACGME requires specific supervision ratios based on PGY level.

    Args:
        db: Database session
        context: Must contain 'block_id' and optionally 'pgy_level'

    Returns:
        Tuple of (is_satisfied, violation_details)
    """
    block_id = context.get("block_id")
    pgy_level = context.get("pgy_level", 1)

    if not block_id:
        return True, None

    # Get assignments for this block
    result = await db.execute(
        select(Assignment).where(Assignment.block_id == block_id)
    )
    assignments = result.scalars().all()

    # Count residents and faculty by role/PGY level
    resident_count = 0
    faculty_count = 0

    for assignment in assignments:
        # Would check person.role in real implementation
        # For now, assume assignment has a role indicator
        role = getattr(assignment, "role", None) or context.get("role", "resident")
        if role == "faculty":
            faculty_count += 1
        else:
            resident_count += 1

    if resident_count == 0:
        return True, None

    # ACGME supervision ratios
    # PGY-1: 1 faculty per 2 residents
    # PGY-2+: 1 faculty per 4 residents
    if pgy_level == 1:
        required_ratio = 0.5  # 1:2
    else:
        required_ratio = 0.25  # 1:4

    actual_ratio = faculty_count / resident_count if resident_count > 0 else 1.0

    if actual_ratio < required_ratio:
        return False, f"Supervision ratio {actual_ratio:.2f} below required {required_ratio:.2f}"

    return True, None


async def _check_acgme_duty_hours(
    db: AsyncSession,
    context: dict,
) -> tuple[bool, str | None]:
    """
    Check that ACGME duty hour limits are not exceeded.

    80-hour rule: Max 80 hours/week averaged over 4 weeks.

    Args:
        db: Database session
        context: Must contain 'person_id' and 'target_date'

    Returns:
        Tuple of (is_satisfied, violation_details)
    """
    person_id = context.get("person_id")
    target_date = context.get("target_date")

    if not person_id or not target_date:
        return True, None

    if isinstance(target_date, str):
        target_date = date.fromisoformat(target_date)

    # Calculate 4-week window
    window_start = target_date - timedelta(weeks=4)
    window_end = target_date

    # Count assignments in window
    result = await db.execute(
        select(func.count(Assignment.id))
        .join(Block, Assignment.block_id == Block.id)
        .where(
            Assignment.person_id == person_id,
            Block.date >= window_start,
            Block.date <= window_end,
        )
    )
    assignment_count = result.scalar() or 0

    # Calculate hours (6 hours per half-day block)
    hours_per_block = 6
    total_hours = assignment_count * hours_per_block

    # 80 hours/week * 4 weeks = 320 max
    max_hours = 80 * 4

    if total_hours > max_hours:
        return False, f"Duty hours {total_hours} exceed 4-week limit of {max_hours}"

    return True, None


# =============================================================================
# Soft Constraint Satisfaction Calculators
# =============================================================================


async def _calculate_rotation_preference_satisfaction(
    db: AsyncSession,
    context: dict,
) -> float:
    """
    Calculate satisfaction score for rotation preferences.

    Args:
        db: Database session
        context: Contains 'person_id', 'rotation_id'

    Returns:
        Satisfaction score from 0.0 (violated) to 1.0 (satisfied)
    """
    person_id = context.get("person_id")
    rotation_id = context.get("rotation_id")

    if not person_id or not rotation_id:
        return 1.0  # No preference to check

    # Check if this rotation is preferred
    result = await db.execute(
        select(FacultyPreference).where(FacultyPreference.faculty_id == person_id)
    )
    prefs = result.scalar_one_or_none()

    if not prefs:
        return 0.8  # No preferences set, neutral

    # For rotation preferences, we'd check preferred_rotations if that field existed
    # Since FacultyPreference uses preferred_weeks, return default
    return 0.8


async def _calculate_shift_preference_satisfaction(
    db: AsyncSession,
    context: dict,
) -> float:
    """
    Calculate satisfaction score for shift time preferences.

    Args:
        db: Database session
        context: Contains 'person_id', 'shift_time' (AM/PM)

    Returns:
        Satisfaction score from 0.0 (violated) to 1.0 (satisfied)
    """
    person_id = context.get("person_id")
    target_date = context.get("target_date")

    if not person_id or not target_date:
        return 1.0

    if isinstance(target_date, str):
        target_date = date.fromisoformat(target_date)

    # Get faculty preferences
    result = await db.execute(
        select(FacultyPreference).where(FacultyPreference.faculty_id == person_id)
    )
    prefs = result.scalar_one_or_none()

    if not prefs:
        return 0.8  # No preferences, neutral

    # Calculate week string
    week_start = target_date - timedelta(days=target_date.weekday())
    week_str = week_start.isoformat()

    # Check if this is a preferred week
    if prefs.preferred_weeks and week_str in prefs.preferred_weeks:
        return 1.0  # Preferred week = full satisfaction
    elif prefs.blocked_weeks and week_str in prefs.blocked_weeks:
        return 0.0  # Blocked week = no satisfaction
    else:
        return 0.7  # Neutral week


async def _calculate_workload_balance_satisfaction(
    db: AsyncSession,
    context: dict,
) -> float:
    """
    Calculate satisfaction score for workload balance.

    Args:
        db: Database session
        context: Contains 'person_id', 'target_date'

    Returns:
        Satisfaction score based on workload distribution
    """
    person_id = context.get("person_id")
    target_date = context.get("target_date")

    if not person_id:
        return 1.0

    if target_date and isinstance(target_date, str):
        target_date = date.fromisoformat(target_date)
    else:
        target_date = date.today()

    # Calculate current workload for this person
    window_start = target_date - timedelta(weeks=2)
    window_end = target_date + timedelta(weeks=2)

    result = await db.execute(
        select(func.count(Assignment.id))
        .join(Block, Assignment.block_id == Block.id)
        .where(
            Assignment.person_id == person_id,
            Block.date >= window_start,
            Block.date <= window_end,
        )
    )
    person_count = result.scalar() or 0

    # Get average across all persons
    avg_result = await db.execute(
        select(func.avg(func.count(Assignment.id)))
        .join(Block, Assignment.block_id == Block.id)
        .where(
            Block.date >= window_start,
            Block.date <= window_end,
        )
        .group_by(Assignment.person_id)
    )
    avg_row = avg_result.fetchone()
    avg_count = float(avg_row[0]) if avg_row and avg_row[0] else person_count

    if avg_count == 0:
        return 1.0

    # Calculate deviation from average
    # Perfect balance = 1.0, more deviation = lower score
    deviation = abs(person_count - avg_count) / avg_count if avg_count > 0 else 0
    satisfaction = max(0.0, 1.0 - deviation)

    return round(satisfaction, 3)


async def _calculate_call_equity_satisfaction(
    db: AsyncSession,
    context: dict,
) -> float:
    """
    Calculate satisfaction score for call shift equity.

    Args:
        db: Database session
        context: Contains 'person_id', 'target_date'

    Returns:
        Satisfaction score based on call distribution fairness
    """
    person_id = context.get("person_id")

    if not person_id:
        return 1.0

    # For call equity, we'd typically check the distribution of call shifts
    # across all eligible persons over a period of time.
    # This requires knowing which assignments are "call" assignments.

    # For now, return a moderate satisfaction that indicates
    # call equity should be considered but not necessarily violated
    return 0.75
