"""Procedure controller for request/response handling."""

from typing import Optional
from uuid import UUID
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.services.procedure_service import ProcedureService
from app.schemas.procedure import (
    ProcedureCreate,
    ProcedureUpdate,
    ProcedureResponse,
    ProcedureListResponse,
)


class ProcedureController:
    """Controller for procedure endpoints."""

    def __init__(self, db: Session):
        self.service = ProcedureService(db)

    def list_procedures(
        self,
        specialty: Optional[str] = None,
        category: Optional[str] = None,
        is_active: Optional[bool] = None,
        complexity_level: Optional[str] = None,
    ) -> ProcedureListResponse:
        """List procedures with optional filters."""
        result = self.service.list_procedures(
            specialty=specialty,
            category=category,
            is_active=is_active,
            complexity_level=complexity_level,
        )
        return ProcedureListResponse(items=result["items"], total=result["total"])

    def get_procedure(self, procedure_id: UUID) -> ProcedureResponse:
        """Get a single procedure by ID."""
        procedure = self.service.get_procedure(procedure_id)
        if not procedure:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Procedure not found",
            )
        return procedure

    def get_procedure_by_name(self, name: str) -> ProcedureResponse:
        """Get a procedure by name."""
        procedure = self.service.get_procedure_by_name(name)
        if not procedure:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Procedure not found",
            )
        return procedure

    def create_procedure(self, procedure_in: ProcedureCreate) -> ProcedureResponse:
        """Create a new procedure."""
        result = self.service.create_procedure(
            name=procedure_in.name,
            description=procedure_in.description,
            category=procedure_in.category,
            specialty=procedure_in.specialty,
            supervision_ratio=procedure_in.supervision_ratio,
            requires_certification=procedure_in.requires_certification,
            complexity_level=procedure_in.complexity_level,
            min_pgy_level=procedure_in.min_pgy_level,
            is_active=procedure_in.is_active,
        )

        if result["error"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["error"],
            )

        return result["procedure"]

    def update_procedure(
        self,
        procedure_id: UUID,
        procedure_in: ProcedureUpdate,
    ) -> ProcedureResponse:
        """Update a procedure."""
        update_data = procedure_in.model_dump(exclude_unset=True)

        result = self.service.update_procedure(
            procedure_id=procedure_id,
            update_data=update_data,
        )

        if result["error"]:
            if "not found" in result["error"].lower():
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=result["error"],
                )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["error"],
            )

        return result["procedure"]

    def delete_procedure(self, procedure_id: UUID) -> None:
        """Delete a procedure."""
        result = self.service.delete_procedure(procedure_id)
        if result["error"]:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=result["error"],
            )

    def get_specialties(self) -> list[str]:
        """Get all unique specialties."""
        return self.service.get_specialties()

    def get_categories(self) -> list[str]:
        """Get all unique categories."""
        return self.service.get_categories()
