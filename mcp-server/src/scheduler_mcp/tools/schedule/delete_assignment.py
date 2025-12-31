"""
Delete assignment tool for removing schedule assignments.
"""

from typing import Any

from pydantic import BaseModel, Field

from ..base import BaseTool
from ..validator import validate_person_id


class DeleteAssignmentRequest(BaseModel):
    """Request to delete an assignment."""

    assignment_id: str = Field(..., description="Assignment ID to delete")


class DeleteAssignmentResponse(BaseModel):
    """Response from delete assignment."""

    success: bool
    message: str
    deleted_id: str | None = None


class DeleteAssignmentTool(BaseTool[DeleteAssignmentRequest, DeleteAssignmentResponse]):
    """
    Tool for deleting schedule assignments.

    Removes an assignment from the schedule.
    """

    @property
    def name(self) -> str:
        return "delete_assignment"

    @property
    def description(self) -> str:
        return "Delete a schedule assignment by ID."

    def validate_input(self, **kwargs: Any) -> DeleteAssignmentRequest:
        """Validate input parameters."""
        assignment_id = validate_person_id(
            kwargs.get("assignment_id", ""), "assignment_id"
        )

        return DeleteAssignmentRequest(assignment_id=assignment_id)

    async def execute(
        self, request: DeleteAssignmentRequest
    ) -> DeleteAssignmentResponse:
        """
        Execute assignment deletion.

        Removes an assignment from the schedule database. This operation:
        - Cannot be undone (no soft delete)
        - May trigger re-validation of affected schedules
        - Logs deletion event for audit trail
        - Checks for dependent swaps or holds before deletion

        Use Cases:
        - Correcting scheduling errors
        - Removing obsolete assignments during regeneration
        - Cleaning up test or draft schedules

        Args:
            request: Validated request with assignment_id

        Returns:
            DeleteAssignmentResponse with success status and deleted ID

        Raises:
            APIError: Backend API request fails
            NotFoundError: Assignment does not exist
            ConflictError: Assignment has dependent swaps or cannot be deleted
        """
        client = self._require_api_client()

        try:
            # Delete assignment via API client
            await client.delete_assignment(request.assignment_id)

            return DeleteAssignmentResponse(
                success=True,
                message="Assignment deleted successfully",
                deleted_id=request.assignment_id,
            )

        except (ConnectionError, TimeoutError) as e:
            return DeleteAssignmentResponse(
                success=False,
                message=f"Backend service unavailable: {type(e).__name__}",
            )
        except KeyError as e:
            return DeleteAssignmentResponse(
                success=False,
                message=f"Assignment not found: {request.assignment_id}",
            )
        except ValueError as e:
            return DeleteAssignmentResponse(
                success=False,
                message=f"Cannot delete assignment: {str(e)}",
            )
        except Exception as e:
            return DeleteAssignmentResponse(
                success=False,
                message=f"Failed to delete assignment: {type(e).__name__}",
            )
