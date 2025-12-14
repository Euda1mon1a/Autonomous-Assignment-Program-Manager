"""People API routes."""
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.person import Person
from app.models.user import User
from app.schemas.person import PersonCreate, PersonUpdate, PersonResponse, PersonListResponse
from app.core.security import get_current_active_user

router = APIRouter()


@router.get("", response_model=PersonListResponse)
def list_people(
    type: Optional[str] = Query(None, description="Filter by type: 'resident' or 'faculty'"),
    pgy_level: Optional[int] = Query(None, description="Filter residents by PGY level"),
    db: Session = Depends(get_db),
):
    """List all people, optionally filtered by type or PGY level."""
    query = db.query(Person)

    if type:
        query = query.filter(Person.type == type)
    if pgy_level is not None:
        query = query.filter(Person.pgy_level == pgy_level)

    people = query.order_by(Person.name).all()
    return PersonListResponse(items=people, total=len(people))


@router.get("/residents", response_model=PersonListResponse)
def list_residents(
    pgy_level: Optional[int] = Query(None, description="Filter by PGY level (1, 2, or 3)"),
    db: Session = Depends(get_db),
):
    """List all residents, optionally filtered by PGY level."""
    query = db.query(Person).filter(Person.type == "resident")

    if pgy_level is not None:
        query = query.filter(Person.pgy_level == pgy_level)

    residents = query.order_by(Person.pgy_level, Person.name).all()
    return PersonListResponse(items=residents, total=len(residents))


@router.get("/faculty", response_model=PersonListResponse)
def list_faculty(
    specialty: Optional[str] = Query(None, description="Filter by specialty"),
    db: Session = Depends(get_db),
):
    """List all faculty, optionally filtered by specialty."""
    query = db.query(Person).filter(Person.type == "faculty")

    if specialty:
        query = query.filter(Person.specialties.contains([specialty]))

    faculty = query.order_by(Person.name).all()
    return PersonListResponse(items=faculty, total=len(faculty))


@router.get("/{person_id}", response_model=PersonResponse)
def get_person(person_id: UUID, db: Session = Depends(get_db)):
    """Get a person by ID."""
    person = db.query(Person).filter(Person.id == person_id).first()
    if not person:
        raise HTTPException(status_code=404, detail="Person not found")
    return person


@router.post("", response_model=PersonResponse, status_code=201)
def create_person(
    person_in: PersonCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Create a new person (resident or faculty). Requires authentication."""
    # Validate resident fields
    if person_in.type == "resident" and person_in.pgy_level is None:
        raise HTTPException(status_code=400, detail="PGY level required for residents")

    person = Person(**person_in.model_dump())
    db.add(person)
    db.commit()
    db.refresh(person)
    return person


@router.put("/{person_id}", response_model=PersonResponse)
def update_person(
    person_id: UUID,
    person_in: PersonUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Update an existing person. Requires authentication."""
    person = db.query(Person).filter(Person.id == person_id).first()
    if not person:
        raise HTTPException(status_code=404, detail="Person not found")

    update_data = person_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(person, field, value)

    db.commit()
    db.refresh(person)
    return person


@router.delete("/{person_id}", status_code=204)
def delete_person(
    person_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Delete a person. Requires authentication."""
    person = db.query(Person).filter(Person.id == person_id).first()
    if not person:
        raise HTTPException(status_code=404, detail="Person not found")

    db.delete(person)
    db.commit()
