"""
Create assignment tool for adding new schedule assignments.
"""

from typing import Any

from pydantic import BaseModel, Field

from ..base import BaseTool
from ..validator import validate_date_string, validate_person_id


class CreateAssignmentRequest(BaseModel):
    """Request to create an assignment."""

    person_id: str = Field(..., description="Person ID to assign")
    block_date: str = Field(..., description="Block date in YYYY-MM-DD format")
    block_session: str = Field(..., description="Block session (AM or PM)")
    rotation_id: str | None = Field(
        default=None, description="Optional rotation ID"
    )
    notes: str | None = Field(default=None, description="Optional notes")


class CreateAssignmentResponse(BaseModel):
    """Response from create assignment."""

    success: bool
    assignment_id: str | None = None
    message: str
    details: dict[str, Any] = Field(default_factory=dict)


class CreateAssignmentTool(BaseTool[CreateAssignmentRequest, CreateAssignmentResponse]):
    """
    Tool for creating schedule assignments.

    Creates a new assignment for a person on a specific block.
    """

    @property
    def name(self) -> str:
        return "create_assignment"

    @property
    def description(self) -> str:
        return (
            "Create a new schedule assignment. "
            "Assigns a person to a specific block (date + session)."
        )

    def validate_input(self, **kwargs: Any) -> CreateAssignmentRequest:
        """Validate input parameters."""
        # Validate person_id
        person_id = validate_person_id(kwargs.get("person_id", ""))

        # Validate date
        block_date = validate_date_string(
            kwargs.get("block_date", ""), "block_date"
        )

        # Validate session
        block_session = kwargs.get("block_session", "").upper()
        if block_session not in ["AM", "PM"]:
            from ..base import ValidationError

            raise ValidationError(
                "block_session must be AM or PM",
                details={"value": block_session},
            )

        return CreateAssignmentRequest(
            person_id=person_id,
            block_date=block_date,
            block_session=block_session,
            rotation_id=kwargs.get("rotation_id"),
            notes=kwargs.get("notes"),
        )

    async def execute(
        self, request: CreateAssignmentRequest
    ) -> CreateAssignmentResponse:
        """Execute the tool."""
        client = self._require_api_client()

        try:
            # Create assignment via API
            result = await client.client.post(
                f"{client.config.api_prefix}/assignments",
                headers=await client._ensure_authenticated(),
                json={
                    "person_id": request.person_id,
                    "block_date": request.block_date,
                    "block_session": request.block_session,
                    "rotation_id": request.rotation_id,
                    "notes": request.notes,
                },
            )
            result.raise_for_status()
            data = result.json()

            return CreateAssignmentResponse(
                success=True,
                assignment_id=data.get("id"),
                message="Assignment created successfully",
                details=data,
            )

        except Exception as e:
            return CreateAssignmentResponse(
                success=False,
                message=f"Failed to create assignment: {e}",
                details={"error": str(e)},
            )
