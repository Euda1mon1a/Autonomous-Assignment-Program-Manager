"""
Create swap tool for requesting schedule swaps.
"""

from typing import Any

from pydantic import BaseModel, Field

from ..base import BaseTool
from ..validator import validate_person_id


class CreateSwapRequest(BaseModel):
    """Request to create a swap."""

    person_id: str = Field(..., description="Person requesting the swap")
    assignment_id: str = Field(..., description="Assignment to swap")
    swap_type: str = Field(
        default="one_to_one",
        description="Swap type (one_to_one or absorb)",
    )
    target_person_id: str | None = Field(
        default=None,
        description="Optional target person for one_to_one swap",
    )
    notes: str | None = Field(default=None, description="Optional notes")


class CreateSwapResponse(BaseModel):
    """Response from create swap."""

    success: bool
    message: str
    swap_id: str | None = None
    status: str | None = None


class CreateSwapTool(BaseTool[CreateSwapRequest, CreateSwapResponse]):
    """
    Tool for creating swap requests.

    Allows faculty to request schedule swaps (one-to-one or absorb).
    """

    @property
    def name(self) -> str:
        return "create_swap"

    @property
    def description(self) -> str:
        return (
            "Create a schedule swap request. "
            "Supports one-to-one swaps and absorb (give away shift) swaps."
        )

    def validate_input(self, **kwargs: Any) -> CreateSwapRequest:
        """Validate input parameters."""
        # Validate person IDs
        person_id = validate_person_id(kwargs.get("person_id", ""))
        assignment_id = validate_person_id(
            kwargs.get("assignment_id", ""), "assignment_id"
        )

        # Validate swap type
        swap_type = kwargs.get("swap_type", "one_to_one")
        valid_types = ["one_to_one", "absorb"]
        if swap_type not in valid_types:
            from ..base import ValidationError

            raise ValidationError(
                f"Invalid swap type: {swap_type}",
                details={"value": swap_type, "valid": valid_types},
            )

        # Validate target person if provided
        target_person_id = kwargs.get("target_person_id")
        if target_person_id is not None:
            target_person_id = validate_person_id(target_person_id)

        return CreateSwapRequest(
            person_id=person_id,
            assignment_id=assignment_id,
            swap_type=swap_type,
            target_person_id=target_person_id,
            notes=kwargs.get("notes"),
        )

    async def execute(self, request: CreateSwapRequest) -> CreateSwapResponse:
        """
        Execute swap request creation.

        Creates a new schedule swap request (one-to-one or absorb type).
        Swap requests start in "pending" status and require approval before
        execution. Faculty can swap shifts with each other (one-to-one) or
        give away a shift without replacement (absorb).

        Args:
            request: Validated swap request with person, assignment, and type

        Returns:
            CreateSwapResponse with swap_id and initial status

        Raises:
            APIError: Backend API request fails
            AuthenticationError: Invalid or expired credentials
            ValidationError: Swap violates ACGME compliance or business rules
        """
        client = self._require_api_client()

        try:
            # Create swap via API
            result = await client.client.post(
                f"{client.config.api_prefix}/swaps",
                headers=await client._ensure_authenticated(),
                json={
                    "person_id": request.person_id,
                    "assignment_id": request.assignment_id,
                    "swap_type": request.swap_type,
                    "target_person_id": request.target_person_id,
                    "notes": request.notes,
                },
            )
            result.raise_for_status()
            data = result.json()

            return CreateSwapResponse(
                success=True,
                message="Swap request created successfully",
                swap_id=data.get("id"),
                status=data.get("status"),
            )

        except (ConnectionError, TimeoutError) as e:
            return CreateSwapResponse(
                success=False,
                message=f"Backend service unavailable: {type(e).__name__}",
            )
        except PermissionError as e:
            return CreateSwapResponse(
                success=False,
                message=f"Insufficient permissions to create swap: {str(e)}",
            )
        except ValueError as e:
            return CreateSwapResponse(
                success=False,
                message=f"Invalid swap request: {str(e)}",
            )
        except Exception as e:
            return CreateSwapResponse(
                success=False,
                message=f"Failed to create swap: {type(e).__name__}",
            )
