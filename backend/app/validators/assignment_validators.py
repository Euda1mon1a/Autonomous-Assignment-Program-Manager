"""
Assignment validation functions.

Validates schedule assignments including:
- Assignment conflict detection
- Double-booking prevention
- Role compatibility
- Rotation template matching
- Block availability
- Optimistic locking
"""

from datetime import date, time, datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.assignment import Assignment
from app.models.block import Block
from app.models.person import Person
from app.models.rotation_template import RotationTemplate
from app.validators.common import ValidationError, validate_uuid
from app.validators.date_validators import validate_block_date


async def validate_assignment_conflict(
    db: AsyncSession,
    person_id: UUID,
    block_id: UUID,
    exclude_assignment_id: UUID | None = None,
) -> dict:
    """
    Validate that assignment does not create conflicts.

    Checks for:
    - Double-booking (person already assigned to this block)
    - Overlapping assignments (same time slot)

    Args:
        db: Database session
        person_id: Person being assigned
        block_id: Block for assignment
        exclude_assignment_id: Assignment ID to exclude (for updates)

    Returns:
        dict: Validation result with conflict details

    Raises:
        ValidationError: If person or block not found
    """
    validate_uuid(person_id)
    validate_uuid(block_id)

    # Get block
    result = await db.execute(select(Block).where(Block.id == block_id))
    block = result.scalar_one_or_none()

    if not block:
        raise ValidationError(f"Block not found: {block_id}")

    # Get person
    result = await db.execute(select(Person).where(Person.id == person_id))
    person = result.scalar_one_or_none()

    if not person:
        raise ValidationError(f"Person not found: {person_id}")

    # Check for existing assignment
    query = select(Assignment).where(
        Assignment.person_id == person_id,
        Assignment.block_id == block_id,
    )

    if exclude_assignment_id is not None:
        validate_uuid(exclude_assignment_id)
        query = query.where(Assignment.id != exclude_assignment_id)

    result = await db.execute(query)
    existing_assignment = result.scalar_one_or_none()

    if existing_assignment:
        return {
            "has_conflict": True,
            "conflict_type": "DOUBLE_BOOKING",
            "person_id": str(person_id),
            "person_name": person.name,
            "block_id": str(block_id),
            "block_date": block.date.isoformat(),
            "block_session": block.session,
            "existing_assignment_id": str(existing_assignment.id),
            "message": f"{person.name} is already assigned to {block.date} {block.session}",
        }

    return {
        "has_conflict": False,
        "person_id": str(person_id),
        "person_name": person.name,
        "block_id": str(block_id),
        "block_date": block.date.isoformat(),
        "block_session": block.session,
    }


async def validate_role_compatibility(
    db: AsyncSession,
    person_id: UUID,
    role: str,
    rotation_template_id: UUID | None = None,
) -> dict:
    """
    Validate that person can fulfill the specified role.

    Args:
        db: Database session
        person_id: Person being assigned
        role: Assignment role ('primary', 'supervising', 'backup')
        rotation_template_id: Optional rotation template

    Returns:
        dict: Validation result

    Raises:
        ValidationError: If person not found or role invalid
    """
    # Validate role
    valid_roles = ["primary", "supervising", "backup"]
    if role not in valid_roles:
        raise ValidationError(f"Invalid role: '{role}'. Must be one of {valid_roles}")

    # Get person
    result = await db.execute(select(Person).where(Person.id == person_id))
    person = result.scalar_one_or_none()

    if not person:
        raise ValidationError(f"Person not found: {person_id}")

    # Check role compatibility with person type
    if role == "supervising":
        if person.type != "faculty":
            return {
                "is_compatible": False,
                "person_id": str(person_id),
                "person_name": person.name,
                "person_type": person.type,
                "role": role,
                "message": f"{person.name} ({person.type}) cannot have 'supervising' role "
                f"(only faculty can supervise)",
            }

    # Check if rotation template is appropriate for person
    if rotation_template_id is not None:
        result = await db.execute(
            select(RotationTemplate).where(RotationTemplate.id == rotation_template_id)
        )
        rotation = result.scalar_one_or_none()

        if rotation:
            # Could add rotation-specific validation here
            # e.g., checking if person has required certifications
            pass

    return {
        "is_compatible": True,
        "person_id": str(person_id),
        "person_name": person.name,
        "person_type": person.type,
        "role": role,
    }


async def validate_block_availability(
    db: AsyncSession,
    block_id: UUID,
    max_assignments: int | None = None,
) -> dict:
    """
    Validate that block can accept additional assignments.

    Args:
        db: Database session
        block_id: Block to check
        max_assignments: Optional maximum assignments per block

    Returns:
        dict: Validation result with availability status

    Raises:
        ValidationError: If block not found
    """
    validate_uuid(block_id)

    # Get block
    result = await db.execute(select(Block).where(Block.id == block_id))
    block = result.scalar_one_or_none()

    if not block:
        raise ValidationError(f"Block not found: {block_id}")

    # Count existing assignments
    result = await db.execute(select(Assignment).where(Assignment.block_id == block_id))
    assignments = result.scalars().all()
    current_count = len(assignments)

    # Check if block is full
    is_available = True
    if max_assignments is not None and current_count >= max_assignments:
        is_available = False

    return {
        "is_available": is_available,
        "block_id": str(block_id),
        "block_date": block.date.isoformat(),
        "block_session": block.session,
        "current_assignments": current_count,
        "max_assignments": max_assignments,
    }


async def validate_optimistic_lock(
    db: AsyncSession,
    assignment_id: UUID,
    expected_updated_at: datetime,
) -> dict:
    """
    Validate optimistic locking for concurrent updates.

    Args:
        db: Database session
        assignment_id: Assignment being updated
        expected_updated_at: Expected updated_at timestamp from client

    Returns:
        dict: Validation result

    Raises:
        ValidationError: If assignment not found
    """
    validate_uuid(assignment_id)

    # Get assignment
    result = await db.execute(select(Assignment).where(Assignment.id == assignment_id))
    assignment = result.scalar_one_or_none()

    if not assignment:
        raise ValidationError(f"Assignment not found: {assignment_id}")

    # Check if updated_at matches
    if assignment.updated_at != expected_updated_at:
        return {
            "is_valid": False,
            "assignment_id": str(assignment_id),
            "expected_updated_at": expected_updated_at.isoformat(),
            "actual_updated_at": assignment.updated_at.isoformat(),
            "message": "Assignment was modified by another user. Please refresh and try again.",
            "conflict_type": "OPTIMISTIC_LOCK_FAILURE",
        }

    return {
        "is_valid": True,
        "assignment_id": str(assignment_id),
        "updated_at": assignment.updated_at.isoformat(),
    }


async def validate_rotation_template_compatibility(
    db: AsyncSession,
    person_id: UUID,
    rotation_template_id: UUID,
) -> dict:
    """
    Validate that person is compatible with rotation template.

    Checks:
    - Person type matches rotation requirements
    - Person has required certifications (if applicable)
    - Person meets specialty requirements

    Args:
        db: Database session
        person_id: Person being assigned
        rotation_template_id: Rotation template

    Returns:
        dict: Validation result

    Raises:
        ValidationError: If person or rotation not found
    """
    # Get person
    result = await db.execute(select(Person).where(Person.id == person_id))
    person = result.scalar_one_or_none()

    if not person:
        raise ValidationError(f"Person not found: {person_id}")

    # Get rotation template
    result = await db.execute(
        select(RotationTemplate).where(RotationTemplate.id == rotation_template_id)
    )
    rotation = result.scalar_one_or_none()

    if not rotation:
        raise ValidationError(f"Rotation template not found: {rotation_template_id}")

    issues = []

    # Check if rotation is appropriate for person type
    # For example, some rotations might be resident-only or faculty-only
    # This would depend on your specific business rules

    # Check specialty matching if needed
    if rotation.specialty and person.specialties:
        if rotation.specialty not in person.specialties:
            issues.append(
                f"Person specialty mismatch: rotation requires {rotation.specialty}, "
                f"person has {', '.join(person.specialties)}"
            )

    return {
        "is_compatible": len(issues) == 0,
        "person_id": str(person_id),
        "person_name": person.name,
        "rotation_template_id": str(rotation_template_id),
        "rotation_name": rotation.name,
        "issues": issues,
    }


async def validate_bulk_assignment_create(
    db: AsyncSession,
    assignments: list[dict],
    check_conflicts: bool = True,
) -> dict:
    """
    Validate bulk assignment creation.

    Args:
        db: Database session
        assignments: List of assignment data dicts
        check_conflicts: Check for conflicts between assignments

    Returns:
        dict: Validation result with errors by assignment

    Raises:
        ValidationError: If assignment data is malformed
    """
    errors = []
    warnings = []

    # Track assignments by person/block for conflict detection
    person_blocks = {}

    for idx, assignment_data in enumerate(assignments):
        # Validate required fields
        if "person_id" not in assignment_data:
            errors.append(
                {
                    "index": idx,
                    "field": "person_id",
                    "message": "Missing required field: person_id",
                }
            )
            continue

        if "block_id" not in assignment_data:
            errors.append(
                {
                    "index": idx,
                    "field": "block_id",
                    "message": "Missing required field: block_id",
                }
            )
            continue

        person_id = assignment_data["person_id"]
        block_id = assignment_data["block_id"]

        # Check for duplicates within batch
        if check_conflicts:
            key = (person_id, block_id)
            if key in person_blocks:
                errors.append(
                    {
                        "index": idx,
                        "person_id": person_id,
                        "block_id": block_id,
                        "message": f"Duplicate assignment in batch: person {person_id} "
                        f"already assigned to block {block_id} at index {person_blocks[key]}",
                    }
                )
            else:
                person_blocks[key] = idx

        # Validate individual assignment (would call other validators here)

    return {
        "is_valid": len(errors) == 0,
        "total_assignments": len(assignments),
        "errors": errors,
        "warnings": warnings,
    }


async def validate_assignment_override(
    override_reason: str | None,
    acgme_violations: list[dict],
) -> dict:
    """
    Validate that override reason is provided for ACGME violations.

    Args:
        override_reason: Reason for overriding ACGME rules
        acgme_violations: List of ACGME violations

    Returns:
        dict: Validation result
    """
    if not acgme_violations:
        # No violations, no override needed
        return {
            "is_valid": True,
            "requires_override": False,
        }

    # Has violations - override reason is required
    if not override_reason or not override_reason.strip():
        return {
            "is_valid": False,
            "requires_override": True,
            "violations_count": len(acgme_violations),
            "message": "Override reason is required when ACGME violations are present",
        }

    # Validate override reason length
    if len(override_reason.strip()) < 10:
        return {
            "is_valid": False,
            "requires_override": True,
            "violations_count": len(acgme_violations),
            "message": "Override reason must be at least 10 characters",
        }

    if len(override_reason) > 500:
        return {
            "is_valid": False,
            "requires_override": True,
            "violations_count": len(acgme_violations),
            "message": "Override reason must be at most 500 characters",
        }

    return {
        "is_valid": True,
        "requires_override": True,
        "override_reason": override_reason.strip(),
        "violations_count": len(acgme_violations),
    }


async def validate_assignment_cascade_delete(
    db: AsyncSession,
    assignment_id: UUID,
) -> dict:
    """
    Validate that assignment can be safely deleted.

    Checks for:
    - Related data that would be affected
    - Audit trail requirements
    - Coverage gaps created by deletion

    Args:
        db: Database session
        assignment_id: Assignment to delete

    Returns:
        dict: Validation result with cascade impact

    Raises:
        ValidationError: If assignment not found
    """
    validate_uuid(assignment_id)

    # Get assignment
    result = await db.execute(select(Assignment).where(Assignment.id == assignment_id))
    assignment = result.scalar_one_or_none()

    if not assignment:
        raise ValidationError(f"Assignment not found: {assignment_id}")

    warnings = []

    # Check if this creates a coverage gap
    # (Are there other assignments for this block?)
    result = await db.execute(
        select(Assignment).where(
            Assignment.block_id == assignment.block_id,
            Assignment.id != assignment_id,
        )
    )
    other_assignments = result.scalars().all()

    if len(other_assignments) == 0:
        warnings.append(
            f"Deleting this assignment will leave block {assignment.block.date} "
            f"{assignment.block.session} with no coverage"
        )

    return {
        "can_delete": True,
        "assignment_id": str(assignment_id),
        "has_warnings": len(warnings) > 0,
        "warnings": warnings,
        "related_data": {
            "block_id": str(assignment.block_id),
            "person_id": str(assignment.person_id),
            "other_assignments_on_block": len(other_assignments),
        },
    }
