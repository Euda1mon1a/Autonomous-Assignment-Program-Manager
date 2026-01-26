"""Assignment controller for request/response handling."""

from datetime import date
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.error_codes import ErrorCode, get_error_code_from_message
from app.models.user import User
from app.schemas.assignment import (
    AssignmentCreate,
    AssignmentListResponse,
    AssignmentResponse,
    AssignmentUpdate,
    AssignmentWithWarnings,
)
from app.services.assignment_service import AssignmentService


class AssignmentController:
    """Controller for assignment endpoints."""

    def __init__(self, db: Session):
        self.service = AssignmentService(db)

    def list_assignments(
        self,
        start_date: date | None = None,
        end_date: date | None = None,
        person_id: UUID | None = None,
        role: str | None = None,
        rotation_type: str | None = None,
        page: int = 1,
        page_size: int = 100,
    ) -> AssignmentListResponse:
        """List assignments with optional filters and database-level pagination.

        Args:
            start_date: Filter assignments starting from this date
            end_date: Filter assignments ending by this date
            person_id: Filter by specific person
            role: Filter by role type
            rotation_type: Filter by rotation type
            page: Page number (1-indexed)
            page_size: Number of items per page

        Returns:
            AssignmentListResponse with items, total count, page, and page_size
        """
        # Calculate offset for database-level pagination
        offset = (page - 1) * page_size

        result = self.service.list_assignments(
            start_date=start_date,
            end_date=end_date,
            person_id=person_id,
            role=role,
            rotation_type=rotation_type,
            offset=offset,
            limit=page_size,
        )

        return AssignmentListResponse(
            items=[AssignmentResponse.model_validate(item) for item in result["items"]],
            total=result["total"],
            page=page,
            page_size=page_size,
        )

    def get_assignment(self, assignment_id: UUID) -> AssignmentResponse:
        """Get a single assignment by ID."""
        assignment = self.service.get_assignment(assignment_id)
        if not assignment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Assignment not found",
            )
        return assignment

    def create_assignment(
        self,
        assignment_in: AssignmentCreate,
        current_user: User,
    ) -> AssignmentWithWarnings:
        """Create a new assignment with ACGME validation."""
        result = self.service.create_assignment(
            block_id=assignment_in.block_id,
            person_id=assignment_in.person_id,
            role=assignment_in.role,
            created_by=current_user.username,
            override_reason=assignment_in.override_reason,
            rotation_template_id=getattr(assignment_in, "rotation_template_id", None),
            notes=getattr(assignment_in, "notes", None),
        )

        if result["error"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["error"],
            )

        return AssignmentWithWarnings(
            **result["assignment"].__dict__,
            acgme_warnings=result["acgme_warnings"],
            is_compliant=result["is_compliant"],
        )

    def update_assignment(
        self,
        assignment_id: UUID,
        assignment_in: AssignmentUpdate,
    ) -> AssignmentWithWarnings:
        """Update an assignment with optimistic locking."""
        update_data = assignment_in.model_dump(
            exclude_unset=True,
            exclude={"updated_at", "override_reason"},
        )

        result = self.service.update_assignment(
            assignment_id=assignment_id,
            update_data=update_data,
            expected_updated_at=assignment_in.updated_at,
            override_reason=assignment_in.override_reason,
        )

        if result["error"]:
            # Determine appropriate status code using structured error codes
            error_code = result.get("error_code") or get_error_code_from_message(
                result["error"]
            )

            if error_code == ErrorCode.NOT_FOUND:
                status_code = status.HTTP_404_NOT_FOUND
            elif error_code in (ErrorCode.CONFLICT, ErrorCode.CONCURRENT_MODIFICATION):
                status_code = status.HTTP_409_CONFLICT
            else:
                status_code = status.HTTP_400_BAD_REQUEST

            raise HTTPException(status_code=status_code, detail=result["error"])

        return AssignmentWithWarnings(
            **result["assignment"].__dict__,
            acgme_warnings=result["acgme_warnings"],
            is_compliant=result["is_compliant"],
        )

    def delete_assignment(self, assignment_id: UUID) -> None:
        """Delete an assignment."""
        result = self.service.delete_assignment(assignment_id)
        if result["error"]:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=result["error"],
            )

    def delete_assignments_bulk(
        self,
        start_date: date,
        end_date: date,
    ) -> dict:
        """Delete all assignments in a date range."""
        return self.service.delete_assignments_bulk(start_date, end_date)
