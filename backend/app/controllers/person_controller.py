"""Person controller for request/response handling."""

from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.schemas.person import (
    PersonCreate,
    PersonListResponse,
    PersonResponse,
    PersonUpdate,
)
from app.services.person_service import PersonService


class PersonController:
    """Controller for person endpoints."""

    def __init__(self, db: Session):
        self.service = PersonService(db)

    def list_people(
        self,
        type: str | None = None,
        pgy_level: int | None = None,
    ) -> PersonListResponse:
        """List people with optional filters."""
        result = self.service.list_people(type=type, pgy_level=pgy_level)
        return PersonListResponse(items=result["items"], total=result["total"])

    def list_residents(
        self,
        pgy_level: int | None = None,
    ) -> PersonListResponse:
        """List all residents with optional PGY filter."""
        result = self.service.list_residents(pgy_level=pgy_level)
        return PersonListResponse(items=result["items"], total=result["total"])

    def list_faculty(
        self,
        specialty: str | None = None,
    ) -> PersonListResponse:
        """List all faculty with optional specialty filter."""
        result = self.service.list_faculty(specialty=specialty)
        return PersonListResponse(items=result["items"], total=result["total"])

    def get_person(self, person_id: UUID) -> PersonResponse:
        """Get a single person by ID."""
        person = self.service.get_person(person_id)
        if not person:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Person not found",
            )
        return person

    def create_person(self, person_in: PersonCreate) -> PersonResponse:
        """Create a new person."""
        result = self.service.create_person(
            name=person_in.name,
            type=person_in.type,
            email=getattr(person_in, "email", None),
            pgy_level=person_in.pgy_level,
            target_clinical_blocks=getattr(person_in, "target_clinical_blocks", None),
            specialties=getattr(person_in, "specialties", None),
            performs_procedures=getattr(person_in, "performs_procedures", False),
        )

        if result["error"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["error"],
            )

        return result["person"]

    def update_person(
        self,
        person_id: UUID,
        person_in: PersonUpdate,
    ) -> PersonResponse:
        """Update a person's information."""
        update_data = person_in.model_dump(exclude_unset=True)

        result = self.service.update_person(
            person_id=person_id,
            update_data=update_data,
        )

        if result["error"]:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=result["error"],
            )

        return result["person"]

    def delete_person(self, person_id: UUID) -> None:
        """Delete a person."""
        result = self.service.delete_person(person_id)
        if result["error"]:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=result["error"],
            )
