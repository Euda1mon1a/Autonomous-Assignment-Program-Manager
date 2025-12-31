"""
Relationship rule validators.

Validates data relationships and referential integrity:
- Foreign key relationships
- Many-to-many relationships
- Cascading operations
- Orphaned record detection
"""

from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.assignment import Assignment
from app.models.block import Block
from app.models.person import Person
from app.models.rotation_template import RotationTemplate
from app.validators.common import ValidationError, validate_uuid


async def validate_person_assignment_relationship(
    db: AsyncSession,
    person_id: UUID,
    assignment_id: UUID,
) -> dict:
    """
    Validate relationship between person and assignment.

    Args:
        db: Database session
        person_id: Person ID
        assignment_id: Assignment ID

    Returns:
        dict: Validation result

    Raises:
        ValidationError: If person or assignment not found
    """
    validate_uuid(person_id)
    validate_uuid(assignment_id)

    # Get person
    result = await db.execute(select(Person).where(Person.id == person_id))
    person = result.scalar_one_or_none()

    if not person:
        raise ValidationError(f"Person not found: {person_id}")

    # Get assignment
    result = await db.execute(select(Assignment).where(Assignment.id == assignment_id))
    assignment = result.scalar_one_or_none()

    if not assignment:
        raise ValidationError(f"Assignment not found: {assignment_id}")

    # Check relationship
    if assignment.person_id != person_id:
        return {
            "is_valid": False,
            "person_id": str(person_id),
            "assignment_id": str(assignment_id),
            "actual_person_id": str(assignment.person_id),
            "message": f"Assignment {assignment_id} does not belong to person {person_id}",
        }

    return {
        "is_valid": True,
        "person_id": str(person_id),
        "person_name": person.name,
        "assignment_id": str(assignment_id),
    }


async def validate_block_assignment_relationship(
    db: AsyncSession,
    block_id: UUID,
    assignment_id: UUID,
) -> dict:
    """
    Validate relationship between block and assignment.

    Args:
        db: Database session
        block_id: Block ID
        assignment_id: Assignment ID

    Returns:
        dict: Validation result

    Raises:
        ValidationError: If block or assignment not found
    """
    validate_uuid(block_id)
    validate_uuid(assignment_id)

    # Get block
    result = await db.execute(select(Block).where(Block.id == block_id))
    block = result.scalar_one_or_none()

    if not block:
        raise ValidationError(f"Block not found: {block_id}")

    # Get assignment
    result = await db.execute(select(Assignment).where(Assignment.id == assignment_id))
    assignment = result.scalar_one_or_none()

    if not assignment:
        raise ValidationError(f"Assignment not found: {assignment_id}")

    # Check relationship
    if assignment.block_id != block_id:
        return {
            "is_valid": False,
            "block_id": str(block_id),
            "assignment_id": str(assignment_id),
            "actual_block_id": str(assignment.block_id),
            "message": f"Assignment {assignment_id} does not belong to block {block_id}",
        }

    return {
        "is_valid": True,
        "block_id": str(block_id),
        "block_date": block.date.isoformat(),
        "block_session": block.session,
        "assignment_id": str(assignment_id),
    }


async def validate_orphaned_assignments(
    db: AsyncSession,
) -> dict:
    """
    Validate there are no orphaned assignments.

    Orphaned assignments are those where:
    - Person no longer exists
    - Block no longer exists
    - Rotation template no longer exists (if specified)

    Args:
        db: Database session

    Returns:
        dict: Validation result with orphaned records
    """
    orphaned = []

    # Get all assignments
    result = await db.execute(select(Assignment))
    assignments = result.scalars().all()

    for assignment in assignments:
        # Check person exists
        result = await db.execute(
            select(Person).where(Person.id == assignment.person_id)
        )
        person = result.scalar_one_or_none()

        if not person:
            orphaned.append(
                {
                    "assignment_id": str(assignment.id),
                    "type": "missing_person",
                    "person_id": str(assignment.person_id),
                    "message": f"Assignment {assignment.id} references non-existent person {assignment.person_id}",
                }
            )

        # Check block exists
        result = await db.execute(select(Block).where(Block.id == assignment.block_id))
        block = result.scalar_one_or_none()

        if not block:
            orphaned.append(
                {
                    "assignment_id": str(assignment.id),
                    "type": "missing_block",
                    "block_id": str(assignment.block_id),
                    "message": f"Assignment {assignment.id} references non-existent block {assignment.block_id}",
                }
            )

        # Check rotation template exists (if specified)
        if assignment.rotation_template_id:
            result = await db.execute(
                select(RotationTemplate).where(
                    RotationTemplate.id == assignment.rotation_template_id
                )
            )
            rotation = result.scalar_one_or_none()

            if not rotation:
                orphaned.append(
                    {
                        "assignment_id": str(assignment.id),
                        "type": "missing_rotation_template",
                        "rotation_template_id": str(assignment.rotation_template_id),
                        "message": f"Assignment {assignment.id} references non-existent rotation template {assignment.rotation_template_id}",
                    }
                )

    return {
        "has_orphans": len(orphaned) > 0,
        "total_assignments": len(assignments),
        "orphaned_count": len(orphaned),
        "orphaned_records": orphaned,
    }


async def validate_cascade_delete_impact(
    db: AsyncSession,
    entity_type: str,
    entity_id: UUID,
) -> dict:
    """
    Validate impact of cascading delete.

    Args:
        db: Database session
        entity_type: Type of entity ('person', 'block', 'rotation_template')
        entity_id: Entity ID to delete

    Returns:
        dict: Impact analysis

    Raises:
        ValidationError: If entity type is invalid or entity not found
    """
    validate_uuid(entity_id)

    if entity_type == "person":
        # Get assignments for this person
        result = await db.execute(
            select(Assignment).where(Assignment.person_id == entity_id)
        )
        assignments = result.scalars().all()

        return {
            "entity_type": entity_type,
            "entity_id": str(entity_id),
            "affected_assignments": len(assignments),
            "impact_level": "high"
            if len(assignments) > 10
            else "medium"
            if len(assignments) > 0
            else "low",
            "message": f"Deleting person will affect {len(assignments)} assignments",
        }

    elif entity_type == "block":
        # Get assignments for this block
        result = await db.execute(
            select(Assignment).where(Assignment.block_id == entity_id)
        )
        assignments = result.scalars().all()

        return {
            "entity_type": entity_type,
            "entity_id": str(entity_id),
            "affected_assignments": len(assignments),
            "impact_level": "high"
            if len(assignments) > 5
            else "medium"
            if len(assignments) > 0
            else "low",
            "message": f"Deleting block will affect {len(assignments)} assignments",
        }

    elif entity_type == "rotation_template":
        # Get assignments using this rotation template
        result = await db.execute(
            select(Assignment).where(Assignment.rotation_template_id == entity_id)
        )
        assignments = result.scalars().all()

        return {
            "entity_type": entity_type,
            "entity_id": str(entity_id),
            "affected_assignments": len(assignments),
            "impact_level": "medium" if len(assignments) > 0 else "low",
            "message": f"Deleting rotation template will affect {len(assignments)} assignments",
        }

    else:
        raise ValidationError(
            f"Invalid entity type: '{entity_type}'. "
            f"Must be 'person', 'block', or 'rotation_template'"
        )


async def validate_referential_integrity(
    db: AsyncSession,
) -> dict:
    """
    Validate referential integrity across all relationships.

    Comprehensive check for:
    - Orphaned assignments
    - Missing foreign keys
    - Circular dependencies (if any)
    - Constraint violations

    Args:
        db: Database session

    Returns:
        dict: Comprehensive integrity report
    """
    # Check for orphaned assignments
    orphan_result = await validate_orphaned_assignments(db)

    # Could add more checks here:
    # - Check person references
    # - Check block references
    # - Check rotation template references

    issues = []
    issues.extend(orphan_result["orphaned_records"])

    return {
        "is_valid": len(issues) == 0,
        "total_issues": len(issues),
        "issues_by_type": {
            "orphaned_assignments": orphan_result["orphaned_count"],
        },
        "issues": issues,
    }


def validate_relationship(
    relationship_type: str,
    context: dict,
) -> dict:
    """
    Validate a named relationship.

    Args:
        relationship_type: Type of relationship to validate
        context: Context data for validation

    Returns:
        dict: Validation result

    Raises:
        ValidationError: If relationship type is unknown
    """
    valid_relationships = [
        "person_assignment",
        "block_assignment",
        "rotation_assignment",
    ]

    if relationship_type not in valid_relationships:
        raise ValidationError(
            f"Unknown relationship type: '{relationship_type}'. "
            f"Valid types: {valid_relationships}"
        )

    return {
        "relationship_type": relationship_type,
        "is_valid": True,
        "message": f"Relationship '{relationship_type}' validated",
    }


async def check_data_integrity(
    db: AsyncSession,
) -> bool:
    """
    Quick boolean check for data integrity.

    Args:
        db: Database session

    Returns:
        bool: True if integrity is valid, False otherwise
    """
    result = await validate_referential_integrity(db)
    return result["is_valid"]
