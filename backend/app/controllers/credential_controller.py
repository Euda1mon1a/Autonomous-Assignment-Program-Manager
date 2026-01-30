"""Credential controller for request/response handling."""

from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.error_codes import ErrorCode, get_error_code_from_message
from app.schemas.procedure_credential import (
    CredentialCreate,
    CredentialListResponse,
    CredentialResponse,
    CredentialUpdate,
    FacultyCredentialSummary,
    QualifiedFacultyResponse,
)
from app.services.credential_service import CredentialService


class CredentialController:
    """Controller for credential endpoints."""

    def __init__(self, db: Session) -> None:
        self.service = CredentialService(db)

    def get_credential(self, credential_id: UUID) -> CredentialResponse:
        """Get a single credential by ID."""
        credential = self.service.get_credential(credential_id)
        if not credential:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Credential not found",
            )
        return credential

    def list_credentials_for_person(
        self,
        person_id: UUID,
        status_filter: str | None = None,
        include_expired: bool = False,
    ) -> CredentialListResponse:
        """List all credentials for a person."""
        result = self.service.list_credentials_for_person(
            person_id=person_id,
            status=status_filter,
            include_expired=include_expired,
        )
        return CredentialListResponse(
            items=[CredentialResponse.model_validate(item) for item in result["items"]],
            total=result["total"],
        )

    def list_credentials_for_procedure(
        self,
        procedure_id: UUID,
        status_filter: str | None = None,
        include_expired: bool = False,
    ) -> CredentialListResponse:
        """List all credentials for a procedure."""
        result = self.service.list_credentials_for_procedure(
            procedure_id=procedure_id,
            status=status_filter,
            include_expired=include_expired,
        )
        return CredentialListResponse(
            items=[CredentialResponse.model_validate(item) for item in result["items"]],
            total=result["total"],
        )

    def get_qualified_faculty(self, procedure_id: UUID) -> QualifiedFacultyResponse:
        """Get all faculty qualified to supervise a procedure."""
        result = self.service.list_qualified_faculty_for_procedure(procedure_id)
        if result.get("error"):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=result["error"],
            )
        return QualifiedFacultyResponse(
            procedure_id=result["procedure_id"],
            procedure_name=result["procedure_name"],
            qualified_faculty=result["qualified_faculty"],
            total=result["total"],
        )

    def check_qualification(
        self,
        person_id: UUID,
        procedure_id: UUID,
    ) -> dict:
        """Check if a faculty member is qualified for a procedure."""
        return self.service.is_faculty_qualified(person_id, procedure_id)

    def create_credential(self, credential_in: CredentialCreate) -> CredentialResponse:
        """Create a new credential."""
        result = self.service.create_credential(
            person_id=credential_in.person_id,
            procedure_id=credential_in.procedure_id,
            status=credential_in.status,
            competency_level=credential_in.competency_level,
            issued_date=credential_in.issued_date,
            expiration_date=credential_in.expiration_date,
            last_verified_date=credential_in.last_verified_date,
            max_concurrent_residents=credential_in.max_concurrent_residents,
            max_per_week=credential_in.max_per_week,
            max_per_academic_year=credential_in.max_per_academic_year,
            notes=credential_in.notes,
        )

        if result["error"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["error"],
            )

        return result["credential"]

    def update_credential(
        self,
        credential_id: UUID,
        credential_in: CredentialUpdate,
    ) -> CredentialResponse:
        """Update a credential."""
        update_data = credential_in.model_dump(exclude_unset=True)

        result = self.service.update_credential(
            credential_id=credential_id,
            update_data=update_data,
        )

        if result["error"]:
            # Determine appropriate status code using structured error codes
            error_code = result.get("error_code") or get_error_code_from_message(
                result["error"]
            )

            if error_code == ErrorCode.NOT_FOUND:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=result["error"],
                )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["error"],
            )

        return result["credential"]

    def delete_credential(self, credential_id: UUID) -> None:
        """Delete a credential."""
        result = self.service.delete_credential(credential_id)
        if result["error"]:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=result["error"],
            )

    def suspend_credential(
        self,
        credential_id: UUID,
        notes: str | None = None,
    ) -> CredentialResponse:
        """Suspend a credential."""
        result = self.service.suspend_credential(credential_id, notes)
        if result["error"]:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=result["error"],
            )
        return result["credential"]

    def activate_credential(self, credential_id: UUID) -> CredentialResponse:
        """Activate a credential."""
        result = self.service.activate_credential(credential_id)
        if result["error"]:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=result["error"],
            )
        return result["credential"]

    def verify_credential(self, credential_id: UUID) -> CredentialResponse:
        """Mark a credential as verified."""
        result = self.service.verify_credential(credential_id)
        if result["error"]:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=result["error"],
            )
        return result["credential"]

    def list_expiring_credentials(self, days: int = 30) -> CredentialListResponse:
        """List credentials expiring soon."""
        result = self.service.list_expiring_credentials(days=days)
        return CredentialListResponse(
            items=[CredentialResponse.model_validate(item) for item in result["items"]],
            total=result["total"],
        )

    def get_faculty_summary(self, person_id: UUID) -> FacultyCredentialSummary:
        """Get a summary of a faculty member's credentials."""
        result = self.service.get_faculty_credential_summary(person_id)
        if result.get("error"):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=result["error"],
            )
        return FacultyCredentialSummary(
            person_id=result["person_id"],
            person_name=result["person_name"],
            total_credentials=result["total_credentials"],
            active_credentials=result["active_credentials"],
            expiring_soon=result["expiring_soon"],
            procedures=result["procedures"],
        )
