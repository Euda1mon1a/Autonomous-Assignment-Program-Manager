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
        """Execute the tool."""
        client = self._require_api_client()

        try:
            # Delete assignment via API
            result = await client.client.delete(
                f"{client.config.api_prefix}/assignments/{request.assignment_id}",
                headers=await client._ensure_authenticated(),
            )
            result.raise_for_status()

            return DeleteAssignmentResponse(
                success=True,
                message="Assignment deleted successfully",
                deleted_id=request.assignment_id,
            )

        except Exception as e:
            return DeleteAssignmentResponse(
                success=False,
                message=f"Failed to delete assignment: {e}",
            )
