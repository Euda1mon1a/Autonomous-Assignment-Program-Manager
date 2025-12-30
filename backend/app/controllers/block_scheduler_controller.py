"""Block scheduler controller - request/response handling."""

from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.schemas.block_assignment import (
    BlockAssignmentCreate,
    BlockAssignmentResponse,
    BlockAssignmentUpdate,
    BlockScheduleRequest,
    BlockScheduleResponse,
    BlockSchedulerDashboard,
    ResidentInfo,
    RotationTemplateInfo,
)
from app.services.block_scheduler_service import BlockSchedulerService


class BlockSchedulerController:
    """Controller for block scheduler operations."""

    def __init__(self, db: Session):
        self.db = db
        self.service = BlockSchedulerService(db)

    def get_dashboard(
        self,
        block_number: int,
        academic_year: int,
    ) -> BlockSchedulerDashboard:
        """Get dashboard view for block scheduler."""
        return self.service.get_dashboard(block_number, academic_year)

    def schedule_block(
        self,
        request: BlockScheduleRequest,
        created_by: str | None = None,
    ) -> BlockScheduleResponse:
        """
        Schedule residents for a block.

        If dry_run=True, returns preview without saving.
        If dry_run=False, saves assignments to database.
        """
        return self.service.schedule_block(
            block_number=request.block_number,
            academic_year=request.academic_year,
            dry_run=request.dry_run,
            include_all_residents=request.include_all_residents,
            created_by=created_by,
        )

    def get_assignment(self, assignment_id: UUID) -> BlockAssignmentResponse:
        """Get a single block assignment by ID."""
        assignment = self.service.get_assignment(assignment_id)
        if not assignment:
            raise HTTPException(status_code=404, detail="Block assignment not found")

        resident_info = None
        rotation_info = None

        if assignment.resident:
            resident_info = ResidentInfo(
                id=assignment.resident.id,
                name=assignment.resident.name,
                pgy_level=assignment.resident.pgy_level,
            )

        if assignment.rotation_template:
            rotation_info = RotationTemplateInfo(
                id=assignment.rotation_template.id,
                name=assignment.rotation_template.name,
                activity_type=assignment.rotation_template.activity_type,
                leave_eligible=assignment.rotation_template.leave_eligible,
            )

        return BlockAssignmentResponse(
            id=assignment.id,
            block_number=assignment.block_number,
            academic_year=assignment.academic_year,
            resident_id=assignment.resident_id,
            rotation_template_id=assignment.rotation_template_id,
            has_leave=assignment.has_leave,
            leave_days=assignment.leave_days,
            assignment_reason=assignment.assignment_reason,
            notes=assignment.notes,
            created_by=assignment.created_by,
            created_at=assignment.created_at,
            updated_at=assignment.updated_at,
            resident=resident_info,
            rotation_template=rotation_info,
        )

    def create_assignment(
        self,
        assignment_in: BlockAssignmentCreate,
    ) -> BlockAssignmentResponse:
        """Create a manual block assignment."""
        try:
            assignment = self.service.create_manual_assignment(
                block_number=assignment_in.block_number,
                academic_year=assignment_in.academic_year,
                resident_id=assignment_in.resident_id,
                rotation_template_id=assignment_in.rotation_template_id,
                created_by=assignment_in.created_by,
                notes=assignment_in.notes,
            )
        except Exception as e:
            if "unique_resident_per_block" in str(e):
                raise HTTPException(
                    status_code=409,
                    detail="Assignment already exists for this resident in this block",
                )
            raise HTTPException(status_code=400, detail=str(e))

        return self.get_assignment(assignment.id)

    def update_assignment(
        self,
        assignment_id: UUID,
        update_in: BlockAssignmentUpdate,
    ) -> BlockAssignmentResponse:
        """Update a block assignment."""
        update_data = update_in.model_dump(exclude_unset=True)

        assignment = self.service.update_assignment(assignment_id, update_data)
        if not assignment:
            raise HTTPException(status_code=404, detail="Block assignment not found")

        return self.get_assignment(assignment.id)

    def delete_assignment(self, assignment_id: UUID) -> None:
        """Delete a block assignment."""
        success = self.service.delete_assignment(assignment_id)
        if not success:
            raise HTTPException(status_code=404, detail="Block assignment not found")
