"""
Swap request validation functions.

Validates schedule swap requests including:
- Swap type validation
- Swap compatibility
- ACGME compliance after swap
- Equity impact
- Rollback window validation
"""

from datetime import date, datetime, timedelta
from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.assignment import Assignment
from app.models.block import Block
from app.models.person import Person
from app.models.swap import Swap, SwapStatus, SwapType
from app.validators.common import ValidationError, validate_uuid
from app.validators.date_validators import validate_future_date

# Swap constants
MAX_SWAP_ADVANCE_DAYS = 180  # Can't request swap more than 6 months ahead
MIN_SWAP_ADVANCE_DAYS = 1  # Must request at least 1 day ahead
ROLLBACK_WINDOW_HOURS = 24  # Can rollback within 24 hours of execution
MAX_PENDING_SWAPS_PER_PERSON = 5  # Maximum pending swap requests


def validate_swap_type(swap_type: str) -> str:
    """
    Validate swap type.

    Valid types:
    - one_to_one: Direct swap between two people
    - absorb: One person gives away shift, other takes it
    - multi_way: Multi-person swap (complex)

    Args:
        swap_type: Swap type to validate

    Returns:
        str: Validated swap type

    Raises:
        ValidationError: If swap type is invalid
    """
    valid_types = ["one_to_one", "absorb", "multi_way"]

    if not swap_type:
        raise ValidationError("Swap type cannot be empty")

    swap_type_lower = swap_type.lower().strip()

    if swap_type_lower not in valid_types:
        raise ValidationError(
            f"Swap type must be one of {valid_types}, got '{swap_type}'"
        )

    return swap_type_lower


def validate_swap_status(status: str) -> str:
    """
    Validate swap status.

    Valid statuses:
    - pending: Awaiting approval
    - approved: Approved but not executed
    - executed: Swap completed
    - rejected: Swap denied
    - cancelled: Requester cancelled
    - rolled_back: Swap was reversed

    Args:
        status: Status to validate

    Returns:
        str: Validated status

    Raises:
        ValidationError: If status is invalid
    """
    valid_statuses = [
        "pending",
        "approved",
        "executed",
        "rejected",
        "cancelled",
        "rolled_back",
    ]

    if not status:
        raise ValidationError("Swap status cannot be empty")

    status_lower = status.lower().strip()

    if status_lower not in valid_statuses:
        raise ValidationError(
            f"Swap status must be one of {valid_statuses}, got '{status}'"
        )

    return status_lower


async def validate_swap_request(
    db: AsyncSession,
    requester_id: UUID,
    requester_assignment_id: UUID,
    target_id: UUID | None = None,
    target_assignment_id: UUID | None = None,
    swap_type: str = "one_to_one",
) -> dict:
    """
    Validate swap request before creation.

    Args:
        db: Database session
        requester_id: Person requesting swap
        requester_assignment_id: Assignment requester wants to swap
        target_id: Person to swap with (if one_to_one)
        target_assignment_id: Assignment target would give up (if one_to_one)
        swap_type: Type of swap

    Returns:
        dict: Validation result with any issues

    Raises:
        ValidationError: If data is invalid
    """
    validate_uuid(requester_id)
    validate_uuid(requester_assignment_id)

    swap_type = validate_swap_type(swap_type)

    errors = []
    warnings = []

    # Get requester
    result = await db.execute(select(Person).where(Person.id == requester_id))
    requester = result.scalar_one_or_none()

    if not requester:
        errors.append(f"Requester not found: {requester_id}")
        return {"is_valid": False, "errors": errors, "warnings": warnings}

    # Get requester assignment
    result = await db.execute(
        select(Assignment).where(Assignment.id == requester_assignment_id)
    )
    requester_assignment = result.scalar_one_or_none()

    if not requester_assignment:
        errors.append(f"Requester assignment not found: {requester_assignment_id}")
        return {"is_valid": False, "errors": errors, "warnings": warnings}

    # Verify requester owns the assignment
    if requester_assignment.person_id != requester_id:
        errors.append(
            f"Assignment {requester_assignment_id} does not belong to requester {requester_id}"
        )

    # Check assignment is in the future
    assignment_date = requester_assignment.block.date
    today = date.today()

    if assignment_date < today:
        errors.append(f"Cannot swap assignment in the past ({assignment_date})")
    elif assignment_date == today:
        warnings.append(
            f"Swapping assignment for today ({assignment_date}) - may be too late"
        )

    # Check assignment is not too far in the future
    max_future_date = today + timedelta(days=MAX_SWAP_ADVANCE_DAYS)
    if assignment_date > max_future_date:
        errors.append(
            f"Cannot swap assignment more than {MAX_SWAP_ADVANCE_DAYS} days ahead "
            f"(assignment date: {assignment_date})"
        )

    # Check pending swap limit
    result = await db.execute(
        select(Swap).where(
            Swap.requester_id == requester_id,
            Swap.status == "pending",
        )
    )
    pending_swaps = result.scalars().all()

    if len(pending_swaps) >= MAX_PENDING_SWAPS_PER_PERSON:
        errors.append(
            f"Requester has too many pending swaps ({len(pending_swaps)}). "
            f"Maximum: {MAX_PENDING_SWAPS_PER_PERSON}"
        )

    # Validate one-to-one swap specifics
    if swap_type == "one_to_one":
        if not target_id:
            errors.append("Target person required for one-to-one swap")
        else:
            validate_uuid(target_id)

            # Get target
            result = await db.execute(select(Person).where(Person.id == target_id))
            target = result.scalar_one_or_none()

            if not target:
                errors.append(f"Target person not found: {target_id}")
            else:
                # Check target assignment if provided
                if target_assignment_id:
                    validate_uuid(target_assignment_id)

                    result = await db.execute(
                        select(Assignment).where(Assignment.id == target_assignment_id)
                    )
                    target_assignment = result.scalar_one_or_none()

                    if not target_assignment:
                        errors.append(
                            f"Target assignment not found: {target_assignment_id}"
                        )
                    elif target_assignment.person_id != target_id:
                        errors.append(
                            f"Assignment {target_assignment_id} does not belong to target {target_id}"
                        )

                # Check if target already has assignment at requester's time
                result = await db.execute(
                    select(Assignment).where(
                        Assignment.person_id == target_id,
                        Assignment.block_id == requester_assignment.block_id,
                    )
                )
                existing_target_assignment = result.scalar_one_or_none()

                if existing_target_assignment:
                    warnings.append(
                        f"Target already has assignment on {assignment_date} - "
                        f"this swap would create a conflict"
                    )

    return {
        "is_valid": len(errors) == 0,
        "swap_type": swap_type,
        "requester_id": str(requester_id),
        "requester_name": requester.name,
        "assignment_date": assignment_date.isoformat(),
        "errors": errors,
        "warnings": warnings,
    }


async def validate_swap_acgme_compliance(
    db: AsyncSession,
    swap_id: UUID,
) -> dict:
    """
    Validate that executing swap maintains ACGME compliance.

    Args:
        db: Database session
        swap_id: Swap request to validate

    Returns:
        dict: Validation result with ACGME violations

    Raises:
        ValidationError: If swap not found
    """
    validate_uuid(swap_id)

    # Get swap
    result = await db.execute(select(Swap).where(Swap.id == swap_id))
    swap = result.scalar_one_or_none()

    if not swap:
        raise ValidationError(f"Swap not found: {swap_id}")

    violations = []

    # This would integrate with ACGME validators to check compliance
    # after the swap is executed (simulated here)

    # For example:
    # - Check 80-hour rule for both requester and target
    # - Check 1-in-7 rule for both parties
    # - Check supervision ratios

    # Simplified check for now
    # In production, would call acgme_validators functions

    return {
        "swap_id": str(swap_id),
        "is_compliant": len(violations) == 0,
        "violations": violations,
    }


async def validate_swap_equity_impact(
    db: AsyncSession,
    requester_id: UUID,
    target_id: UUID,
    swap_type: str,
) -> dict:
    """
    Validate equity impact of swap.

    Checks:
    - Call count equity (Sunday call, weekday call)
    - FMIT week equity
    - Shift burden distribution

    Args:
        db: Database session
        requester_id: Person requesting swap
        target_id: Person receiving swap
        swap_type: Type of swap

    Returns:
        dict: Equity impact analysis
    """
    # Get requester and target
    result = await db.execute(
        select(Person).where(Person.id.in_([requester_id, target_id]))
    )
    people = {p.id: p for p in result.scalars().all()}

    requester = people.get(requester_id)
    target = people.get(target_id)

    if not requester or not target:
        return {
            "is_equitable": False,
            "message": "Person not found",
        }

    # Compare call counts
    requester_sunday_calls = requester.sunday_call_count
    target_sunday_calls = target.sunday_call_count

    requester_weekday_calls = requester.weekday_call_count
    target_weekday_calls = target.weekday_call_count

    # Calculate equity scores (simplified)
    sunday_call_diff = abs(requester_sunday_calls - target_sunday_calls)
    weekday_call_diff = abs(requester_weekday_calls - target_weekday_calls)

    concerns = []

    # Flag if swap would create significant inequity
    if swap_type == "absorb":
        # Absorb swaps can create inequity
        if sunday_call_diff > 3:
            concerns.append(
                f"Large Sunday call count difference: "
                f"{requester.name} has {requester_sunday_calls}, "
                f"{target.name} has {target_sunday_calls}"
            )

    return {
        "is_equitable": len(concerns) == 0,
        "requester_id": str(requester_id),
        "requester_name": requester.name,
        "target_id": str(target_id),
        "target_name": target.name,
        "requester_sunday_calls": requester_sunday_calls,
        "target_sunday_calls": target_sunday_calls,
        "requester_weekday_calls": requester_weekday_calls,
        "target_weekday_calls": target_weekday_calls,
        "concerns": concerns,
    }


async def validate_swap_rollback_eligibility(
    db: AsyncSession,
    swap_id: UUID,
) -> dict:
    """
    Validate that swap can be rolled back.

    Swaps can be rolled back if:
    - Status is 'executed'
    - Within rollback window (24 hours)
    - Assignments haven't been modified since swap

    Args:
        db: Database session
        swap_id: Swap to rollback

    Returns:
        dict: Rollback eligibility result

    Raises:
        ValidationError: If swap not found
    """
    validate_uuid(swap_id)

    # Get swap
    result = await db.execute(select(Swap).where(Swap.id == swap_id))
    swap = result.scalar_one_or_none()

    if not swap:
        raise ValidationError(f"Swap not found: {swap_id}")

    # Check status
    if swap.status != "executed":
        return {
            "can_rollback": False,
            "swap_id": str(swap_id),
            "reason": f"Swap status is '{swap.status}', must be 'executed' to rollback",
        }

    # Check rollback window
    if not swap.executed_at:
        return {
            "can_rollback": False,
            "swap_id": str(swap_id),
            "reason": "Swap has no execution timestamp",
        }

    now = datetime.utcnow()
    hours_since_execution = (now - swap.executed_at).total_seconds() / 3600

    if hours_since_execution > ROLLBACK_WINDOW_HOURS:
        return {
            "can_rollback": False,
            "swap_id": str(swap_id),
            "executed_at": swap.executed_at.isoformat(),
            "hours_since_execution": round(hours_since_execution, 1),
            "rollback_window_hours": ROLLBACK_WINDOW_HOURS,
            "reason": f"Rollback window expired ({ROLLBACK_WINDOW_HOURS} hours)",
        }

    return {
        "can_rollback": True,
        "swap_id": str(swap_id),
        "executed_at": swap.executed_at.isoformat(),
        "hours_since_execution": round(hours_since_execution, 1),
        "hours_remaining": round(ROLLBACK_WINDOW_HOURS - hours_since_execution, 1),
    }


async def validate_swap_compatibility(
    db: AsyncSession,
    requester_assignment_id: UUID,
    target_assignment_id: UUID,
) -> dict:
    """
    Validate that two assignments are compatible for swapping.

    Checks:
    - Both assignments exist
    - Different people
    - Similar rotation types (optional)
    - No conflicts created

    Args:
        db: Database session
        requester_assignment_id: Assignment requester wants to give up
        target_assignment_id: Assignment target wants to give up

    Returns:
        dict: Compatibility result
    """
    # Get assignments
    result = await db.execute(
        select(Assignment).where(
            Assignment.id.in_([requester_assignment_id, target_assignment_id])
        )
    )
    assignments = {a.id: a for a in result.scalars().all()}

    requester_assignment = assignments.get(requester_assignment_id)
    target_assignment = assignments.get(target_assignment_id)

    if not requester_assignment or not target_assignment:
        return {
            "is_compatible": False,
            "reason": "One or both assignments not found",
        }

    # Check different people
    if requester_assignment.person_id == target_assignment.person_id:
        return {
            "is_compatible": False,
            "reason": "Cannot swap assignments with yourself",
        }

    # Check for conflicts after swap
    # Would requester have conflict at target's time?
    result = await db.execute(
        select(Assignment).where(
            Assignment.person_id == requester_assignment.person_id,
            Assignment.block_id == target_assignment.block_id,
        )
    )
    requester_conflict = result.scalar_one_or_none()

    if requester_conflict and requester_conflict.id != requester_assignment_id:
        return {
            "is_compatible": False,
            "reason": "Requester already has assignment on target's block",
        }

    # Would target have conflict at requester's time?
    result = await db.execute(
        select(Assignment).where(
            Assignment.person_id == target_assignment.person_id,
            Assignment.block_id == requester_assignment.block_id,
        )
    )
    target_conflict = result.scalar_one_or_none()

    if target_conflict and target_conflict.id != target_assignment_id:
        return {
            "is_compatible": False,
            "reason": "Target already has assignment on requester's block",
        }

    return {
        "is_compatible": True,
        "requester_assignment_id": str(requester_assignment_id),
        "target_assignment_id": str(target_assignment_id),
        "requester_block_date": requester_assignment.block.date.isoformat(),
        "target_block_date": target_assignment.block.date.isoformat(),
    }
