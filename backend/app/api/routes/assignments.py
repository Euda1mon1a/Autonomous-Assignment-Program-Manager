"""Assignment API routes."""
from datetime import date
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload

from app.db.session import get_db
from app.models.assignment import Assignment
from app.models.block import Block
from app.models.user import User
from app.schemas.assignment import (
    AssignmentCreate,
    AssignmentUpdate,
    AssignmentResponse,
    AssignmentWithWarnings,
)
from app.core.security import get_current_active_user, get_scheduler_user
from app.scheduling.validator import ACGMEValidator

router = APIRouter()


def validate_assignment_acgme(
    db: Session,
    assignment: Assignment,
    override_reason: Optional[str] = None
) -> dict:
    """
    Validate ACGME compliance for a single assignment.

    Returns a dict with:
    - violations: list of Violation objects
    - warnings: list of warning messages
    - is_compliant: boolean
    """
    # Get the block to determine date range for validation
    block = db.query(Block).filter(Block.id == assignment.block_id).first()
    if not block:
        return {
            "violations": [],
            "warnings": [],
            "is_compliant": True,
        }

    # Validate a window around the assignment date (e.g., +/- 4 weeks)
    from datetime import timedelta
    start_date = block.date - timedelta(weeks=4)
    end_date = block.date + timedelta(weeks=4)

    validator = ACGMEValidator(db)
    result = validator.validate_all(start_date, end_date)

    # Filter violations related to this person
    from app.models.person import Person
    person = db.query(Person).filter(Person.id == assignment.person_id).first()
    relevant_violations = [
        v for v in result.violations
        if v.person_id == assignment.person_id
    ] if person and person.type == "resident" else []

    # Build warnings list
    warnings = []
    if relevant_violations:
        for violation in relevant_violations:
            warnings.append(f"{violation.severity}: {violation.message}")

    # Check if override was provided for violations
    if relevant_violations and override_reason:
        warnings.append(f"Override acknowledged: {override_reason}")

    return {
        "violations": relevant_violations,
        "warnings": warnings,
        "is_compliant": len(relevant_violations) == 0,
    }


@router.get("")
def list_assignments(
    start_date: Optional[date] = Query(None, description="Filter from this date"),
    end_date: Optional[date] = Query(None, description="Filter until this date"),
    person_id: Optional[UUID] = Query(None, description="Filter by person"),
    role: Optional[str] = Query(None, description="Filter by role"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """List assignments with optional filters. Requires authentication."""
    query = db.query(Assignment).options(
        joinedload(Assignment.block),
        joinedload(Assignment.person),
        joinedload(Assignment.rotation_template),
    )

    if start_date or end_date:
        query = query.join(Block)
        if start_date:
            query = query.filter(Block.date >= start_date)
        if end_date:
            query = query.filter(Block.date <= end_date)

    if person_id:
        query = query.filter(Assignment.person_id == person_id)
    if role:
        query = query.filter(Assignment.role == role)

    assignments = query.all()
    return {"items": assignments, "total": len(assignments)}


@router.get("/{assignment_id}", response_model=AssignmentResponse)
def get_assignment(
    assignment_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get an assignment by ID. Requires authentication."""
    assignment = db.query(Assignment).filter(Assignment.id == assignment_id).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    return assignment


@router.post("", response_model=AssignmentWithWarnings, status_code=201)
def create_assignment(
    assignment_in: AssignmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_scheduler_user),
):
    """
    Create a new assignment. Requires scheduler role (admin or coordinator).

    Validates ACGME compliance and returns warnings if violations exist.
    Violations do not block creation but should be acknowledged with override_reason.
    """
    # Check for duplicate (one person per block)
    existing = db.query(Assignment).filter(
        Assignment.block_id == assignment_in.block_id,
        Assignment.person_id == assignment_in.person_id,
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Person already assigned to this block")

    # Create assignment (exclude override_reason from model fields)
    assignment_data = assignment_in.model_dump(exclude={"override_reason"})
    assignment_data["created_by"] = current_user.username
    assignment = Assignment(**assignment_data)
    db.add(assignment)
    db.commit()
    db.refresh(assignment)

    # Validate ACGME compliance
    validation_result = validate_assignment_acgme(
        db, assignment, assignment_in.override_reason
    )

    # Add override to notes if provided
    if assignment_in.override_reason and validation_result["warnings"]:
        existing_notes = assignment.notes or ""
        override_note = f"\nACGME Override: {assignment_in.override_reason}"
        assignment.notes = (existing_notes + override_note).strip()
        db.commit()
        db.refresh(assignment)

    # Build response with warnings
    response = AssignmentWithWarnings(
        **assignment.__dict__,
        acgme_warnings=validation_result["warnings"],
        is_compliant=validation_result["is_compliant"],
    )

    return response


@router.put("/{assignment_id}", response_model=AssignmentWithWarnings)
def update_assignment(
    assignment_id: UUID,
    assignment_in: AssignmentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_scheduler_user),
):
    """
    Update an existing assignment with optimistic locking.
    Requires scheduler role (admin or coordinator).

    Validates ACGME compliance and returns warnings if violations exist.
    Violations do not block update but should be acknowledged with override_reason.
    """
    assignment = db.query(Assignment).filter(Assignment.id == assignment_id).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")

    # Optimistic locking: check if updated_at matches
    if assignment.updated_at != assignment_in.updated_at:
        raise HTTPException(
            status_code=409,
            detail=f"Assignment has been modified by another user. Please refresh and try again. "
                   f"Current version: {assignment.updated_at}, Your version: {assignment_in.updated_at}"
        )

    # Exclude updated_at and override_reason from the update data
    update_data = assignment_in.model_dump(
        exclude_unset=True, exclude={'updated_at', 'override_reason'}
    )
    for field, value in update_data.items():
        setattr(assignment, field, value)

    db.commit()
    db.refresh(assignment)

    # Validate ACGME compliance
    validation_result = validate_assignment_acgme(
        db, assignment, assignment_in.override_reason
    )

    # Add override to notes if provided
    if assignment_in.override_reason and validation_result["warnings"]:
        existing_notes = assignment.notes or ""
        override_note = f"\nACGME Override: {assignment_in.override_reason}"
        assignment.notes = (existing_notes + override_note).strip()
        db.commit()
        db.refresh(assignment)

    # Build response with warnings
    response = AssignmentWithWarnings(
        **assignment.__dict__,
        acgme_warnings=validation_result["warnings"],
        is_compliant=validation_result["is_compliant"],
    )

    return response


@router.delete("/{assignment_id}", status_code=204)
def delete_assignment(
    assignment_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_scheduler_user),
):
    """Delete an assignment. Requires scheduler role (admin or coordinator)."""
    assignment = db.query(Assignment).filter(Assignment.id == assignment_id).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")

    db.delete(assignment)
    db.commit()


@router.delete("")
def delete_assignments_bulk(
    start_date: date = Query(..., description="Delete assignments from this date"),
    end_date: date = Query(..., description="Delete assignments until this date"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_scheduler_user),
):
    """Delete all assignments in a date range. Requires scheduler role (admin or coordinator)."""
    # Get block IDs in range
    block_ids = db.query(Block.id).filter(
        Block.date >= start_date,
        Block.date <= end_date,
    ).all()
    block_ids = [b[0] for b in block_ids]

    deleted = db.query(Assignment).filter(
        Assignment.block_id.in_(block_ids)
    ).delete(synchronize_session=False)

    db.commit()
    return {"deleted": deleted}
