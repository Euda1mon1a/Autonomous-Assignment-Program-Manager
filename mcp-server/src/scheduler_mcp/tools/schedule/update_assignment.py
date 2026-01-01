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
        """
        Execute assignment update.

        Updates an existing assignment's person, rotation, or notes. Partial updates
        are supported (only specified fields are changed). Validates:
        - New person (if changed) is qualified for the rotation
        - New rotation (if changed) exists and is active
        - Update doesn't violate ACGME compliance
        - No conflicts with other assignments

        Update Scenarios:
        - Reassign block to different person (person_id)
        - Change rotation type (rotation_id)
        - Add/modify administrative notes (notes)

        Args:
            request: Validated request with assignment_id and optional field updates

        Returns:
            UpdateAssignmentResponse with success status and updated details

        Raises:
            APIError: Backend API request fails
            NotFoundError: Assignment, person, or rotation not found
            ValidationError: No fields to update or invalid values
            ConflictError: Update would create scheduling conflict
        """
        client = self._require_api_client()

        try:
            # Check if any fields to update
            if (
                request.person_id is None
                and request.rotation_id is None
                and request.notes is None
            ):
                return UpdateAssignmentResponse(
                    success=False,
                    message="No fields to update",
                    details={},
                )

            # Update assignment via API client
            data = await client.update_assignment(
                assignment_id=request.assignment_id,
                person_id=request.person_id,
                rotation_id=request.rotation_id,
                notes=request.notes,
            )

            return UpdateAssignmentResponse(
                success=True,
                message="Assignment updated successfully",
                details=data,
            )

        except (ConnectionError, TimeoutError) as e:
            return UpdateAssignmentResponse(
                success=False,
                message=f"Backend service unavailable: {type(e).__name__}",
                details={"error": "connection_error"},
            )
        except KeyError as e:
            return UpdateAssignmentResponse(
                success=False,
                message=f"Assignment, person, or rotation not found: {str(e)}",
                details={"error": "not_found"},
            )
        except ValueError as e:
            return UpdateAssignmentResponse(
                success=False,
                message=f"Invalid update data: {str(e)}",
                details={"error": "validation_error"},
            )
        except Exception as e:
            return UpdateAssignmentResponse(
                success=False,
                message=f"Failed to update assignment: {type(e).__name__}",
                details={"error": str(e)},
            )
