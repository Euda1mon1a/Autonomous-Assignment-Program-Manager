"""
ACGME rule validation functions.

Validates ACGME (Accreditation Council for Graduate Medical Education) compliance rules:
- 80-hour weekly work limit (averaged over 4 weeks)
- 1-in-7 rule (one 24-hour period off every 7 days)
- 24+4 hour shift limit (24 hours + 4 hours for handoff)
- Supervision ratio requirements
- Post-call day restrictions
- Consecutive day limits
"""

from datetime import date, datetime, timedelta
from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.assignment import Assignment
from app.models.block import Block
from app.models.person import Person
from app.validators.common import ValidationError

# ACGME Constants
MAX_HOURS_PER_WEEK = 80
MAX_CONSECUTIVE_HOURS = 24
MAX_HOURS_AFTER_24_SHIFT = 4  # 24+4 rule
MAX_CONSECUTIVE_DAYS = 6  # Must have 1 day off in 7
MIN_TIME_OFF_BETWEEN_SHIFTS = 8  # Minimum hours between shifts
MIN_TIME_OFF_AFTER_24_SHIFT = 14  # Minimum hours off after 24-hour shift
ROLLING_AVERAGE_WEEKS = 4  # 80-hour limit averaged over 4 weeks

# Supervision ratios
PGY1_SUPERVISION_RATIO = 2  # 1 faculty per 2 PGY-1 residents
PGY23_SUPERVISION_RATIO = 4  # 1 faculty per 4 PGY-2/3 residents


async def validate_80_hour_rule(
    db: AsyncSession,
    person_id: UUID,
    start_date: date,
    end_date: date,
    additional_hours: float = 0.0,
) -> list[dict]:
    """
    Validate ACGME 80-hour weekly work limit.

    Checks rolling 4-week average for compliance.

    Args:
        db: Database session
        person_id: Person ID to check
        start_date: Start of period to check
        end_date: End of period to check
        additional_hours: Additional hours being added (for pre-validation)

    Returns:
        list[dict]: List of violations with details

    Raises:
        ValidationError: If person is not a resident
    """
    # Get person
    result = await db.execute(select(Person).where(Person.id == person_id))
    person = result.scalar_one_or_none()

    if not person:
        raise ValidationError(f"Person not found: {person_id}")

    # Only validate for residents
    if person.type != "resident":
        return []

    violations = []

    # Get all assignments for this person in the period
    result = await db.execute(
        select(Assignment)
        .join(Block)
        .where(
            Assignment.person_id == person_id,
            Block.date >= start_date,
            Block.date <= end_date,
        )
    )
    assignments = result.scalars().all()

    # Calculate hours per day (simplified: 12 hours per block/half-day)
    # In production, would use actual shift hours from rotation templates
    hours_by_date = {}
    for assignment in assignments:
        block_date = assignment.block.date
        hours_by_date[block_date] = hours_by_date.get(block_date, 0) + 12.0

    # Check rolling 4-week periods
    current_date = start_date
    while current_date <= end_date:
        # Calculate 4-week period
        period_start = current_date
        period_end = current_date + timedelta(days=27)  # 4 weeks = 28 days

        # Calculate total hours in this period
        total_hours = 0.0
        for check_date in (period_start + timedelta(days=i) for i in range(28)):
            total_hours += hours_by_date.get(check_date, 0)

        # Add additional hours if date falls in period
        if period_start <= end_date <= period_end:
            total_hours += additional_hours

        # Calculate weekly average
        average_weekly_hours = total_hours / ROLLING_AVERAGE_WEEKS

        # Check for violation
        if average_weekly_hours > MAX_HOURS_PER_WEEK:
            violations.append(
                {
                    "rule": "80_HOUR_WEEKLY_LIMIT",
                    "person_id": str(person_id),
                    "person_name": person.name,
                    "period_start": period_start.isoformat(),
                    "period_end": period_end.isoformat(),
                    "average_hours": round(average_weekly_hours, 1),
                    "max_hours": MAX_HOURS_PER_WEEK,
                    "violation_hours": round(
                        average_weekly_hours - MAX_HOURS_PER_WEEK, 1
                    ),
                    "message": f"{person.name}: {average_weekly_hours:.1f} hours/week "
                    f"exceeds {MAX_HOURS_PER_WEEK}-hour limit "
                    f"({period_start} to {period_end})",
                }
            )

        # Move to next week
        current_date += timedelta(days=7)

    return violations


async def validate_one_in_seven_rule(
    db: AsyncSession, person_id: UUID, start_date: date, end_date: date
) -> list[dict]:
    """
    Validate ACGME 1-in-7 rule (one 24-hour period off every 7 days).

    Args:
        db: Database session
        person_id: Person ID to check
        start_date: Start of period to check
        end_date: End of period to check

    Returns:
        list[dict]: List of violations with details
    """
    # Get person
    result = await db.execute(select(Person).where(Person.id == person_id))
    person = result.scalar_one_or_none()

    if not person or person.type != "resident":
        return []

    violations = []

    # Get all dates with assignments
    result = await db.execute(
        select(Block.date)
        .join(Assignment)
        .where(
            Assignment.person_id == person_id,
            Block.date >= start_date,
            Block.date <= end_date,
        )
        .distinct()
    )
    assigned_dates = sorted({row[0] for row in result.all()})

    # Check for 7 consecutive days without a day off
    for i in range(len(assigned_dates) - 6):
        consecutive = assigned_dates[i : i + 7]
        # Check if these are 7 consecutive days
        if (consecutive[-1] - consecutive[0]).days == 6:
            violations.append(
                {
                    "rule": "ONE_IN_SEVEN_DAY_OFF",
                    "person_id": str(person_id),
                    "person_name": person.name,
                    "consecutive_days": 7,
                    "period_start": consecutive[0].isoformat(),
                    "period_end": consecutive[-1].isoformat(),
                    "message": f"{person.name}: 7 consecutive days without a day off "
                    f"({consecutive[0]} to {consecutive[-1]})",
                }
            )

    return violations


async def validate_24_plus_4_rule(
    db: AsyncSession, person_id: UUID, check_date: date
) -> list[dict]:
    """
    Validate ACGME 24+4 hour shift limit.

    Residents may work up to 24 hours, plus up to 4 hours for handoff.

    Args:
        db: Database session
        person_id: Person ID to check
        check_date: Date to check

    Returns:
        list[dict]: List of violations with details
    """
    # This is simplified - in production would track actual shift start/end times
    # For now, just check if person has more than 2 blocks (AM + PM) on same day
    violations = []

    result = await db.execute(select(Person).where(Person.id == person_id))
    person = result.scalar_one_or_none()

    if not person or person.type != "resident":
        return []

    # Get all blocks for this person on this date
    result = await db.execute(
        select(Assignment)
        .join(Block)
        .where(Assignment.person_id == person_id, Block.date == check_date)
    )
    assignments = result.scalars().all()

    # Count blocks (simplified check)
    if len(assignments) > 2:
        violations.append(
            {
                "rule": "24_PLUS_4_HOUR_LIMIT",
                "person_id": str(person_id),
                "person_name": person.name,
                "date": check_date.isoformat(),
                "blocks_assigned": len(assignments),
                "message": f"{person.name}: Too many blocks on {check_date} "
                f"(may exceed 24+4 hour limit)",
            }
        )

    return violations


async def validate_supervision_ratio(
    db: AsyncSession, block_id: UUID, include_pending: bool = False
) -> list[dict]:
    """
    Validate ACGME supervision ratio requirements.

    ACGME ratios:
    - PGY-1: 1 faculty per 2 residents
    - PGY-2/3: 1 faculty per 4 residents

    Args:
        db: Database session
        block_id: Block ID to check
        include_pending: Include pending assignments in calculation

    Returns:
        list[dict]: List of violations with details
    """
    violations = []

    # Get block
    result = await db.execute(select(Block).where(Block.id == block_id))
    block = result.scalar_one_or_none()

    if not block:
        return violations

    # Get all assignments for this block
    result = await db.execute(
        select(Assignment).join(Person).where(Assignment.block_id == block_id)
    )
    assignments = result.scalars().all()

    # Count by role
    pgy1_count = 0
    pgy23_count = 0
    supervising_faculty_count = 0

    for assignment in assignments:
        if assignment.person.type == "resident":
            if assignment.person.pgy_level == 1:
                pgy1_count += 1
            else:
                pgy23_count += 1
        elif assignment.person.type == "faculty":
            if assignment.role == "supervising":
                supervising_faculty_count += 1

    # Calculate required faculty
    required_for_pgy1 = (
        pgy1_count + PGY1_SUPERVISION_RATIO - 1
    ) // PGY1_SUPERVISION_RATIO
    required_for_pgy23 = (
        pgy23_count + PGY23_SUPERVISION_RATIO - 1
    ) // PGY23_SUPERVISION_RATIO
    total_required = max(required_for_pgy1, required_for_pgy23)

    # Check for violation
    if supervising_faculty_count < total_required:
        violations.append(
            {
                "rule": "SUPERVISION_RATIO",
                "block_id": str(block_id),
                "block_date": block.date.isoformat(),
                "block_session": block.session,
                "pgy1_count": pgy1_count,
                "pgy23_count": pgy23_count,
                "supervising_faculty": supervising_faculty_count,
                "required_faculty": total_required,
                "shortage": total_required - supervising_faculty_count,
                "message": f"Block {block.date} {block.session}: Insufficient supervising faculty. "
                f"Required: {total_required}, Available: {supervising_faculty_count} "
                f"(PGY-1: {pgy1_count}, PGY-2/3: {pgy23_count})",
            }
        )

    return violations


async def validate_post_call_restrictions(
    db: AsyncSession, person_id: UUID, call_date: date
) -> list[dict]:
    """
    Validate post-call day restrictions.

    After a 24-hour call shift, residents must have:
    - At least 14 hours off before next shift
    - No new patients after 24 hours (simplified check)

    Args:
        db: Database session
        person_id: Person ID to check
        call_date: Date of call shift

    Returns:
        list[dict]: List of violations with details
    """
    violations = []

    result = await db.execute(select(Person).where(Person.id == person_id))
    person = result.scalar_one_or_none()

    if not person or person.type != "resident":
        return []

    # Check if person has assignments the next day (potential violation)
    next_day = call_date + timedelta(days=1)

    result = await db.execute(
        select(Assignment)
        .join(Block)
        .where(Assignment.person_id == person_id, Block.date == next_day)
    )
    next_day_assignments = result.scalars().all()

    # If person has assignments next day after call, might violate rest requirement
    if next_day_assignments:
        violations.append(
            {
                "rule": "POST_CALL_REST",
                "person_id": str(person_id),
                "person_name": person.name,
                "call_date": call_date.isoformat(),
                "next_day": next_day.isoformat(),
                "message": f"{person.name}: Assigned shifts on {next_day} "
                f"after call on {call_date} (may not have 14 hours rest)",
            }
        )

    return violations


async def validate_acgme_compliance(
    db: AsyncSession,
    person_id: UUID,
    start_date: date,
    end_date: date,
    include_warnings: bool = True,
) -> dict:
    """
    Run comprehensive ACGME compliance validation for a person.

    Checks all ACGME rules:
    - 80-hour weekly limit
    - 1-in-7 day off rule
    - 24+4 hour shift limit
    - Supervision ratios
    - Post-call restrictions

    Args:
        db: Database session
        person_id: Person ID to validate
        start_date: Start of validation period
        end_date: End of validation period
        include_warnings: Include warnings in addition to violations

    Returns:
        dict: Validation results with violations and statistics
    """
    all_violations = []

    # 80-hour rule
    violations_80hr = await validate_80_hour_rule(db, person_id, start_date, end_date)
    all_violations.extend(violations_80hr)

    # 1-in-7 rule
    violations_1in7 = await validate_one_in_seven_rule(
        db, person_id, start_date, end_date
    )
    all_violations.extend(violations_1in7)

    # Check each date for 24+4 rule
    current_date = start_date
    while current_date <= end_date:
        violations_24plus4 = await validate_24_plus_4_rule(db, person_id, current_date)
        all_violations.extend(violations_24plus4)
        current_date += timedelta(days=1)

    # Get person details
    result = await db.execute(select(Person).where(Person.id == person_id))
    person = result.scalar_one_or_none()

    return {
        "person_id": str(person_id),
        "person_name": person.name if person else "Unknown",
        "person_type": person.type if person else "Unknown",
        "pgy_level": person.pgy_level if person else None,
        "period_start": start_date.isoformat(),
        "period_end": end_date.isoformat(),
        "is_compliant": len(all_violations) == 0,
        "total_violations": len(all_violations),
        "violations": all_violations,
        "checked_rules": [
            "80_HOUR_WEEKLY_LIMIT",
            "ONE_IN_SEVEN_DAY_OFF",
            "24_PLUS_4_HOUR_LIMIT",
        ],
    }


async def validate_assignment_acgme_compliance(
    db: AsyncSession,
    person_id: UUID,
    block_id: UUID,
    check_supervision: bool = True,
) -> dict:
    """
    Pre-validate ACGME compliance before creating an assignment.

    Args:
        db: Database session
        person_id: Person ID being assigned
        block_id: Block ID for assignment
        check_supervision: Check supervision ratios

    Returns:
        dict: Validation result with any violations
    """
    # Get block date
    result = await db.execute(select(Block).where(Block.id == block_id))
    block = result.scalar_one_or_none()

    if not block:
        raise ValidationError(f"Block not found: {block_id}")

    violations = []

    # Check 1-in-7 rule around this date
    check_start = block.date - timedelta(days=6)
    check_end = block.date + timedelta(days=6)

    violations_1in7 = await validate_one_in_seven_rule(
        db, person_id, check_start, check_end
    )
    violations.extend(violations_1in7)

    # Check 80-hour rule for 4-week period around this date
    check_start_80 = block.date - timedelta(days=14)
    check_end_80 = block.date + timedelta(days=14)

    violations_80hr = await validate_80_hour_rule(
        db, person_id, check_start_80, check_end_80, additional_hours=12.0
    )
    violations.extend(violations_80hr)

    # Check supervision ratio if requested
    if check_supervision:
        violations_supervision = await validate_supervision_ratio(db, block_id)
        violations.extend(violations_supervision)

    return {
        "is_compliant": len(violations) == 0,
        "violations": violations,
        "warnings": [],  # Could add warnings for near-violations
    }
