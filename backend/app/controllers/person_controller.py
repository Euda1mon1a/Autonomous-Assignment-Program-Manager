"""Person controller for request/response handling."""

from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.schemas.person import (
    BatchPersonResponse,
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
        return PersonListResponse(
            items=[PersonResponse.model_validate(item) for item in result["items"]],
            total=result["total"],
        )

    def list_residents(
        self,
        pgy_level: int | None = None,
    ) -> PersonListResponse:
        """List all residents with optional PGY filter."""
        result = self.service.list_residents(pgy_level=pgy_level)
        return PersonListResponse(
            items=[PersonResponse.model_validate(item) for item in result["items"]],
            total=result["total"],
        )

    def list_faculty(
        self,
        specialty: str | None = None,
    ) -> PersonListResponse:
        """List all faculty with optional specialty filter."""
        result = self.service.list_faculty(specialty=specialty)
        return PersonListResponse(
            items=[PersonResponse.model_validate(item) for item in result["items"]],
            total=result["total"],
        )

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

    # =========================================================================
    # Batch Operations
    # =========================================================================

    def batch_create_people(
        self, people_data: list[dict], dry_run: bool = False
    ) -> BatchPersonResponse:
        """Batch create multiple people atomically."""
        try:
            result = self.service.batch_create(people_data, dry_run)

            if result["failed"] > 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "message": "Batch create operation failed",
                        "failed": result["failed"],
                        "results": result["results"],
                    },
                )

            return BatchPersonResponse(**result)

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e),
            )

    def batch_update_people(
        self, updates: list[dict], dry_run: bool = False
    ) -> BatchPersonResponse:
        """Batch update multiple people atomically."""
        try:
            result = self.service.batch_update(updates, dry_run)

            if result["failed"] > 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "message": "Batch update operation failed",
                        "failed": result["failed"],
                        "results": result["results"],
                    },
                )

            return BatchPersonResponse(**result)

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e),
            )

    def batch_delete_people(
        self, person_ids: list[UUID], dry_run: bool = False
    ) -> BatchPersonResponse:
        """Batch delete multiple people atomically."""
        try:
            result = self.service.batch_delete(person_ids, dry_run)

            if result["failed"] > 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "message": "Batch delete operation failed",
                        "failed": result["failed"],
                        "results": result["results"],
                    },
                )

            return BatchPersonResponse(**result)

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e),
            )
