"""
Update assignment tool for modifying existing assignments.
"""

from typing import Any

from pydantic import BaseModel, Field

from ..base import BaseTool
from ..validator import validate_person_id


class UpdateAssignmentRequest(BaseModel):
    """Request to update an assignment."""

    assignment_id: str = Field(..., description="Assignment ID to update")
    person_id: str | None = Field(default=None, description="New person ID")
    rotation_id: str | None = Field(default=None, description="New rotation ID")
    notes: str | None = Field(default=None, description="Updated notes")


class UpdateAssignmentResponse(BaseModel):
    """Response from update assignment."""

    success: bool
    message: str
    details: dict[str, Any] = Field(default_factory=dict)


class UpdateAssignmentTool(BaseTool[UpdateAssignmentRequest, UpdateAssignmentResponse]):
    """
    Tool for updating schedule assignments.

    Modifies an existing assignment's person, rotation, or notes.
    """

    @property
    def name(self) -> str:
        return "update_assignment"

    @property
    def description(self) -> str:
        return (
            "Update an existing schedule assignment. "
            "Can change the assigned person, rotation, or notes."
        )

    def validate_input(self, **kwargs: Any) -> UpdateAssignmentRequest:
        """Validate input parameters."""
        assignment_id = validate_person_id(
            kwargs.get("assignment_id", ""), "assignment_id"
        )

        person_id = kwargs.get("person_id")
        if person_id is not None:
            person_id = validate_person_id(person_id)

        return UpdateAssignmentRequest(
            assignment_id=assignment_id,
            person_id=person_id,
            rotation_id=kwargs.get("rotation_id"),
            notes=kwargs.get("notes"),
        )

    async def execute(
        self, request: UpdateAssignmentRequest
    ) -> UpdateAssignmentResponse:
        """Execute the tool."""
        client = self._require_api_client()

        try:
            # Build update payload
            payload = {}
            if request.person_id is not None:
                payload["person_id"] = request.person_id
            if request.rotation_id is not None:
                payload["rotation_id"] = request.rotation_id
            if request.notes is not None:
                payload["notes"] = request.notes

            if not payload:
                return UpdateAssignmentResponse(
                    success=False,
                    message="No fields to update",
                    details={},
                )

            # Update assignment via API
            result = await client.client.patch(
                f"{client.config.api_prefix}/assignments/{request.assignment_id}",
                headers=await client._ensure_authenticated(),
                json=payload,
            )
            result.raise_for_status()
            data = result.json()

            return UpdateAssignmentResponse(
                success=True,
                message="Assignment updated successfully",
                details=data,
            )

        except Exception as e:
            return UpdateAssignmentResponse(
                success=False,
                message=f"Failed to update assignment: {e}",
                details={"error": str(e)},
            )
