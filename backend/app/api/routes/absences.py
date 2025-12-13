"""Absence API routes."""
from datetime import date
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload

from app.db.session import get_db
from app.models.absence import Absence
from app.schemas.absence import AbsenceCreate, AbsenceUpdate, AbsenceResponse

router = APIRouter()


@router.get("")
def list_absences(
    start_date: Optional[date] = Query(None, description="Filter absences starting from"),
    end_date: Optional[date] = Query(None, description="Filter absences ending by"),
    person_id: Optional[UUID] = Query(None, description="Filter by person"),
    absence_type: Optional[str] = Query(None, description="Filter by absence type"),
    db: Session = Depends(get_db),
):
    """List absences with optional filters."""
    query = db.query(Absence).options(joinedload(Absence.person))

    if start_date:
        query = query.filter(Absence.end_date >= start_date)
    if end_date:
        query = query.filter(Absence.start_date <= end_date)
    if person_id:
        query = query.filter(Absence.person_id == person_id)
    if absence_type:
        query = query.filter(Absence.absence_type == absence_type)

    absences = query.order_by(Absence.start_date).all()
    return {"items": absences, "total": len(absences)}


@router.get("/{absence_id}", response_model=AbsenceResponse)
def get_absence(absence_id: UUID, db: Session = Depends(get_db)):
    """Get an absence by ID."""
    absence = db.query(Absence).filter(Absence.id == absence_id).first()
    if not absence:
        raise HTTPException(status_code=404, detail="Absence not found")
    return absence


@router.post("", response_model=AbsenceResponse, status_code=201)
def create_absence(absence_in: AbsenceCreate, db: Session = Depends(get_db)):
    """Create a new absence."""
    absence = Absence(**absence_in.model_dump())
    db.add(absence)
    db.commit()
    db.refresh(absence)
    return absence


@router.put("/{absence_id}", response_model=AbsenceResponse)
def update_absence(
    absence_id: UUID,
    absence_in: AbsenceUpdate,
    db: Session = Depends(get_db),
):
    """Update an existing absence."""
    absence = db.query(Absence).filter(Absence.id == absence_id).first()
    if not absence:
        raise HTTPException(status_code=404, detail="Absence not found")

    update_data = absence_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(absence, field, value)

    db.commit()
    db.refresh(absence)
    return absence


@router.delete("/{absence_id}", status_code=204)
def delete_absence(absence_id: UUID, db: Session = Depends(get_db)):
    """Delete an absence."""
    absence = db.query(Absence).filter(Absence.id == absence_id).first()
    if not absence:
        raise HTTPException(status_code=404, detail="Absence not found")

    db.delete(absence)
    db.commit()
