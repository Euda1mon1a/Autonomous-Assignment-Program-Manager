"""Assignment API routes."""
from datetime import date
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload

from app.db.session import get_db
from app.models.assignment import Assignment
from app.models.block import Block
from app.schemas.assignment import AssignmentCreate, AssignmentUpdate, AssignmentResponse

router = APIRouter()


@router.get("")
def list_assignments(
    start_date: Optional[date] = Query(None, description="Filter from this date"),
    end_date: Optional[date] = Query(None, description="Filter until this date"),
    person_id: Optional[UUID] = Query(None, description="Filter by person"),
    role: Optional[str] = Query(None, description="Filter by role"),
    db: Session = Depends(get_db),
):
    """List assignments with optional filters."""
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
def get_assignment(assignment_id: UUID, db: Session = Depends(get_db)):
    """Get an assignment by ID."""
    assignment = db.query(Assignment).filter(Assignment.id == assignment_id).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    return assignment


@router.post("", response_model=AssignmentResponse, status_code=201)
def create_assignment(assignment_in: AssignmentCreate, db: Session = Depends(get_db)):
    """Create a new assignment."""
    # Check for duplicate (one person per block)
    existing = db.query(Assignment).filter(
        Assignment.block_id == assignment_in.block_id,
        Assignment.person_id == assignment_in.person_id,
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Person already assigned to this block")

    assignment = Assignment(**assignment_in.model_dump())
    db.add(assignment)
    db.commit()
    db.refresh(assignment)
    return assignment


@router.put("/{assignment_id}", response_model=AssignmentResponse)
def update_assignment(
    assignment_id: UUID,
    assignment_in: AssignmentUpdate,
    db: Session = Depends(get_db),
):
    """Update an existing assignment."""
    assignment = db.query(Assignment).filter(Assignment.id == assignment_id).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")

    update_data = assignment_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(assignment, field, value)

    db.commit()
    db.refresh(assignment)
    return assignment


@router.delete("/{assignment_id}", status_code=204)
def delete_assignment(assignment_id: UUID, db: Session = Depends(get_db)):
    """Delete an assignment."""
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
):
    """Delete all assignments in a date range."""
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
