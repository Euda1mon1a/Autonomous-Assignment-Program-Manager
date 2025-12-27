"""Call assignment controller for request/response handling."""

from datetime import date
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.call_assignment import (
    CallAssignmentCreate,
    CallAssignmentListResponse,
    CallAssignmentResponse,
    CallAssignmentUpdate,
)
from app.services.call_assignment_service import CallAssignmentService


class CallAssignmentController:
    """Controller for call assignment endpoints."""

    def __init__(self, db: AsyncSession):
        self.service = CallAssignmentService(db)

    async def list_call_assignments(
        self,
        start_date: date | None = None,
        end_date: date | None = None,
        person_id: UUID | None = None,
        call_type: str | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> CallAssignmentListResponse:
        """List call assignments with optional filters."""
        result = await self.service.get_call_assignments(
            skip=skip,
            limit=limit,
            start_date=start_date,
            end_date=end_date,
            person_id=person_id,
            call_type=call_type,
        )
        return CallAssignmentListResponse(**result)

    async def get_call_assignment(self, call_id: UUID) -> CallAssignmentResponse:
        """Get a single call assignment by ID."""
        call_assignment = await self.service.get_call_assignment(call_id)
        if not call_assignment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Call assignment not found",
            )
        return CallAssignmentResponse.model_validate(call_assignment)

    async def create_call_assignment(
        self, assignment_in: CallAssignmentCreate
    ) -> CallAssignmentResponse:
        """Create a new call assignment."""
        result = await self.service.create_call_assignment(assignment_in)

        if result["error"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["error"],
            )

        return CallAssignmentResponse.model_validate(result["call_assignment"])

    async def update_call_assignment(
        self,
        call_id: UUID,
        assignment_in: CallAssignmentUpdate,
    ) -> CallAssignmentResponse:
        """Update a call assignment."""
        result = await self.service.update_call_assignment(call_id, assignment_in)

        if result["error"]:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=result["error"],
            )

        return CallAssignmentResponse.model_validate(result["call_assignment"])

    async def delete_call_assignment(self, call_id: UUID) -> None:
        """Delete a call assignment."""
        result = await self.service.delete_call_assignment(call_id)
        if result["error"]:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=result["error"],
            )

    async def get_call_assignments_by_person(
        self,
        person_id: UUID,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> CallAssignmentListResponse:
        """Get all call assignments for a specific person."""
        assignments = await self.service.get_call_assignments_by_person(
            person_id=person_id,
            start_date=start_date,
            end_date=end_date,
        )
        return CallAssignmentListResponse(items=assignments, total=len(assignments))

    async def get_call_assignments_by_date(
        self, on_date: date
    ) -> CallAssignmentListResponse:
        """Get all call assignments for a specific date."""
        assignments = await self.service.get_call_assignments_by_date_range(
            start_date=on_date,
            end_date=on_date,
        )
        return CallAssignmentListResponse(items=assignments, total=len(assignments))
