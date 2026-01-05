"""Call assignment controller for request/response handling."""

from datetime import date
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.call_assignment import (
    BulkCallAssignmentCreate,
    BulkCallAssignmentResponse,
    BulkCallAssignmentUpdateRequest,
    BulkCallAssignmentUpdateResponse,
    CallAssignmentCreate,
    CallAssignmentListResponse,
    CallAssignmentResponse,
    CallAssignmentUpdate,
    CallCoverageReport,
    CallEquityReport,
    EquityPreviewResponse,
    PCATGenerationRequest,
    PCATGenerationResponse,
    SimulatedChange,
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
        return CallAssignmentListResponse(
            items=result["items"],
            total=result["total"],
            skip=skip,
            limit=limit,
        )

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

    async def bulk_create_call_assignments(
        self, bulk_data: BulkCallAssignmentCreate
    ) -> BulkCallAssignmentResponse:
        """Bulk create multiple call assignments."""
        result = await self.service.bulk_create_call_assignments(
            assignments=bulk_data.assignments,
            replace_existing=bulk_data.replace_existing,
        )
        return BulkCallAssignmentResponse(
            created=result["count"],
            errors=result["errors"],
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
        return CallAssignmentListResponse(
            items=assignments,
            total=len(assignments),
        )

    async def get_call_assignments_by_date(
        self, on_date: date
    ) -> CallAssignmentListResponse:
        """Get all call assignments for a specific date."""
        assignments = await self.service.get_call_assignments_by_date_range(
            start_date=on_date,
            end_date=on_date,
        )
        return CallAssignmentListResponse(
            items=assignments,
            total=len(assignments),
        )

    async def get_coverage_report(
        self,
        start_date: date,
        end_date: date,
    ) -> CallCoverageReport:
        """Get call coverage report for a date range."""
        return await self.service.get_coverage_report(start_date, end_date)

    async def get_equity_report(
        self,
        start_date: date,
        end_date: date,
    ) -> CallEquityReport:
        """Get call equity/distribution report for a date range."""
        return await self.service.get_equity_report(start_date, end_date)

    async def bulk_update_call_assignments(
        self,
        request: BulkCallAssignmentUpdateRequest,
    ) -> BulkCallAssignmentUpdateResponse:
        """Bulk update multiple call assignments."""
        result = await self.service.bulk_update_call_assignments(
            assignment_ids=request.assignment_ids,
            updates=request.updates,
        )

        if result["errors"] and result["updated"] == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["errors"][0],
            )

        return BulkCallAssignmentUpdateResponse(
            updated=result["updated"],
            errors=result["errors"],
            assignments=[
                CallAssignmentResponse.model_validate(a)
                for a in result["assignments"]
            ],
        )

    async def generate_pcat(
        self,
        request: PCATGenerationRequest,
    ) -> PCATGenerationResponse:
        """Generate PCAT/DO assignments for selected call assignments."""
        return await self.service.generate_pcat_for_assignments(
            assignment_ids=request.assignment_ids,
        )

    async def get_equity_preview(
        self,
        start_date: date,
        end_date: date,
        simulated_changes: list[SimulatedChange],
    ) -> EquityPreviewResponse:
        """Get equity preview with simulated changes."""
        return await self.service.get_equity_preview(
            start_date=start_date,
            end_date=end_date,
            simulated_changes=simulated_changes,
        )
