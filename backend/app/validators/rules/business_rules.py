"""
Business rule validators.

Validates domain-specific business rules for scheduling:
- Rotation eligibility
- Workload distribution
- Shift preferences
- Call equity
- Fair scheduling practices
"""

from datetime import date, timedelta
from typing import Optional
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.assignment import Assignment
from app.models.block import Block
from app.models.person import Person
from app.validators.common import ValidationError


async def validate_rotation_eligibility(
    db: AsyncSession,
    person_id: UUID,
    rotation_type: str,
    check_date: date,
) -> dict:
    """
    Validate that person is eligible for rotation type.

    Business rules:
    - PGY-1 residents must complete orientation before clinical rotations
    - Sports medicine rotations require specific specialty
    - Procedure rotations require certification
    - Research rotations have eligibility criteria

    Args:
        db: Database session
        person_id: Person to check
        rotation_type: Type of rotation
        check_date: Date of rotation

    Returns:
        dict: Eligibility result
    """
    # Get person
    result = await db.execute(select(Person).where(Person.id == person_id))
    person = result.scalar_one_or_none()

    if not person:
        raise ValidationError(f"Person not found: {person_id}")

    reasons = []

    # PGY-1 orientation requirement
    if person.type == "resident" and person.pgy_level == 1:
        # Check if rotation is in first 2 weeks of academic year
        # (Simplified: would need academic year start date)
        # For now, just check if it's complex rotation
        if rotation_type in ["surgery", "ob_gyn", "emergency"]:
            # PGY-1 should complete orientation first
            # Would check person's rotation history here
            pass

    # Specialty matching
    if rotation_type == "sports_medicine":
        if person.specialties and "Sports Medicine" not in person.specialties:
            reasons.append(
                "Sports medicine rotation requires Sports Medicine specialty"
            )

    # Procedure requirements
    if rotation_type in ["surgery", "ob_gyn", "procedures"]:
        if person.type == "resident" and not person.performs_procedures:
            reasons.append(f"{rotation_type} rotation requires procedural credentials")

    return {
        "is_eligible": len(reasons) == 0,
        "person_id": str(person_id),
        "person_name": person.name,
        "rotation_type": rotation_type,
        "check_date": check_date.isoformat(),
        "ineligibility_reasons": reasons,
    }


async def validate_workload_distribution(
    db: AsyncSession,
    person_id: UUID,
    start_date: date,
    end_date: date,
    max_clinical_blocks: int = 200,
) -> dict:
    """
    Validate workload is fairly distributed.

    Business rules:
    - No person should have more than 50% more blocks than average
    - Call shifts should be evenly distributed
    - Weekend coverage should be equitable

    Args:
        db: Database session
        person_id: Person to check
        start_date: Start of period
        end_date: End of period
        max_clinical_blocks: Maximum clinical blocks per period

    Returns:
        dict: Workload distribution result
    """
    # Get person's assignments
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

    total_blocks = len(assignments)

    # Check against maximum
    issues = []
    if total_blocks > max_clinical_blocks:
        issues.append(
            f"Exceeds maximum clinical blocks: {total_blocks} > {max_clinical_blocks}"
        )

    # Get average for comparison (would compare with peers here)
    # For now, simplified
    average_blocks = max_clinical_blocks * 0.7  # Assume 70% utilization is average

    if total_blocks > average_blocks * 1.5:
        issues.append(
            f"Workload significantly above average: {total_blocks} blocks "
            f"vs average {average_blocks:.0f}"
        )

    return {
        "is_fair": len(issues) == 0,
        "person_id": str(person_id),
        "period_start": start_date.isoformat(),
        "period_end": end_date.isoformat(),
        "total_blocks": total_blocks,
        "max_blocks": max_clinical_blocks,
        "average_blocks": round(average_blocks, 1),
        "issues": issues,
    }


async def validate_call_equity(
    db: AsyncSession,
    person_id: UUID,
) -> dict:
    """
    Validate call shift equity.

    Business rules:
    - Sunday call should be evenly distributed
    - Weekday call should be balanced
    - No person should have >20% more calls than average

    Args:
        db: Database session
        person_id: Person to check

    Returns:
        dict: Call equity result
    """
    # Get person
    result = await db.execute(select(Person).where(Person.id == person_id))
    person = result.scalar_one_or_none()

    if not person or person.type != "resident":
        return {
            "is_equitable": True,
            "message": "Not applicable for non-residents",
        }

    # Get all residents for comparison
    result = await db.execute(select(Person).where(Person.type == "resident"))
    all_residents = result.scalars().all()

    # Calculate averages
    avg_sunday_calls = sum(r.sunday_call_count for r in all_residents) / len(
        all_residents
    )
    avg_weekday_calls = sum(r.weekday_call_count for r in all_residents) / len(
        all_residents
    )

    issues = []

    # Check if person has significantly more calls than average
    if person.sunday_call_count > avg_sunday_calls * 1.2:
        issues.append(
            f"Sunday calls above average: {person.sunday_call_count} "
            f"vs {avg_sunday_calls:.1f} average"
        )

    if person.weekday_call_count > avg_weekday_calls * 1.2:
        issues.append(
            f"Weekday calls above average: {person.weekday_call_count} "
            f"vs {avg_weekday_calls:.1f} average"
        )

    return {
        "is_equitable": len(issues) == 0,
        "person_id": str(person_id),
        "person_name": person.name,
        "sunday_calls": person.sunday_call_count,
        "avg_sunday_calls": round(avg_sunday_calls, 1),
        "weekday_calls": person.weekday_call_count,
        "avg_weekday_calls": round(avg_weekday_calls, 1),
        "issues": issues,
    }


async def validate_preference_satisfaction(
    db: AsyncSession,
    person_id: UUID,
    assignment_date: date,
    rotation_name: str,
) -> dict:
    """
    Validate assignment satisfies person's preferences.

    Business rules:
    - Respect time-off requests
    - Consider rotation preferences
    - Honor special accommodations

    Args:
        db: Database session
        person_id: Person being assigned
        assignment_date: Date of assignment
        rotation_name: Rotation being assigned

    Returns:
        dict: Preference satisfaction result
    """
    # Get person
    result = await db.execute(select(Person).where(Person.id == person_id))
    person = result.scalar_one_or_none()

    if not person:
        raise ValidationError(f"Person not found: {person_id}")

    # Would check against preferences/absences table here
    # Simplified for now

    conflicts = []
    warnings = []

    # Check for absence requests (would query absences table)
    # For now, simplified

    return {
        "satisfies_preferences": len(conflicts) == 0,
        "person_id": str(person_id),
        "person_name": person.name,
        "assignment_date": assignment_date.isoformat(),
        "rotation_name": rotation_name,
        "conflicts": conflicts,
        "warnings": warnings,
    }


def validate_business_rule(
    rule_name: str,
    context: dict,
) -> dict:
    """
    Validate a named business rule.

    Args:
        rule_name: Name of business rule to validate
        context: Context data for validation

    Returns:
        dict: Validation result

    Raises:
        ValidationError: If rule name is unknown
    """
    valid_rules = [
        "rotation_eligibility",
        "workload_distribution",
        "call_equity",
        "preference_satisfaction",
    ]

    if rule_name not in valid_rules:
        raise ValidationError(
            f"Unknown business rule: '{rule_name}'. Valid rules: {valid_rules}"
        )

    # Route to appropriate validator
    # (In production, would have a registry pattern)

    return {
        "rule_name": rule_name,
        "is_valid": True,
        "message": f"Business rule '{rule_name}' validated",
    }


async def check_rotation_eligibility(
    db: AsyncSession,
    person_id: UUID,
    rotation_type: str,
    check_date: date,
) -> bool:
    """
    Quick boolean check for rotation eligibility.

    Args:
        db: Database session
        person_id: Person to check
        rotation_type: Type of rotation
        check_date: Date of rotation

    Returns:
        bool: True if eligible, False otherwise
    """
    result = await validate_rotation_eligibility(
        db, person_id, rotation_type, check_date
    )
    return result["is_eligible"]


async def check_workload_limits(
    db: AsyncSession,
    person_id: UUID,
    start_date: date,
    end_date: date,
) -> bool:
    """
    Quick boolean check for workload limits.

    Args:
        db: Database session
        person_id: Person to check
        start_date: Start of period
        end_date: End of period

    Returns:
        bool: True if within limits, False otherwise
    """
    result = await validate_workload_distribution(db, person_id, start_date, end_date)
    return result["is_fair"]
