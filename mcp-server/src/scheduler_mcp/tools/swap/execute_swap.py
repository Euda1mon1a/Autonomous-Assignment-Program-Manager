"""
Execute swap tool for completing approved swaps.
"""

from typing import Any

from pydantic import BaseModel, Field

from ..base import BaseTool
from ..validator import validate_person_id


class ExecuteSwapRequest(BaseModel):
    """Request to execute a swap."""

    swap_id: str = Field(..., description="Swap ID to execute")
    approved_by: str | None = Field(
        default=None,
        description="Person approving the swap",
    )


class ExecuteSwapResponse(BaseModel):
    """Response from execute swap."""

    success: bool
    message: str
    swap_id: str
    executed_at: str | None = None
    rollback_deadline: str | None = None


class ExecuteSwapTool(BaseTool[ExecuteSwapRequest, ExecuteSwapResponse]):
    """
    Tool for executing approved swaps.

    Completes the swap and updates assignments with rollback capability.
    """

    @property
    def name(self) -> str:
        return "execute_swap"

    @property
    def description(self) -> str:
        return (
            "Execute an approved swap request. "
            "Updates assignments and enables 24-hour rollback window."
        )

    def validate_input(self, **kwargs: Any) -> ExecuteSwapRequest:
        """Validate input parameters."""
        # Validate swap_id
        swap_id = validate_person_id(kwargs.get("swap_id", ""), "swap_id")

        # Validate approved_by if provided
        approved_by = kwargs.get("approved_by")
        if approved_by is not None:
            approved_by = validate_person_id(approved_by)

        return ExecuteSwapRequest(
            swap_id=swap_id,
            approved_by=approved_by,
        )

    async def execute(self, request: ExecuteSwapRequest) -> ExecuteSwapResponse:
        """
        Execute an approved swap request.

        Completes the swap transaction by updating all affected assignments in the
        database. Enables a 24-hour rollback window for reversing the swap if needed.
        The swap must be in "approved" status before execution.

        Workflow:
        1. Verify swap is in "approved" status
        2. Update person assignments for both parties
        3. Record execution timestamp
        4. Calculate 24-hour rollback deadline
        5. Send notifications to affected parties

        Args:
            request: Validated request with swap_id and optional approver

        Returns:
            ExecuteSwapResponse with execution timestamp and rollback deadline

        Raises:
            APIError: Backend API request fails
            ValidationError: Swap not approved or already executed
            ConflictError: Assignment conflicts detected
        """
        client = self._require_api_client()

        try:
            # Execute swap via API
            result = await client.client.post(
                f"{client.config.api_prefix}/swaps/{request.swap_id}/execute",
                headers=await client._ensure_authenticated(),
                json={
                    "approved_by": request.approved_by,
                },
            )
            result.raise_for_status()
            data = result.json()

            return ExecuteSwapResponse(
                success=True,
                message="Swap executed successfully",
                swap_id=request.swap_id,
                executed_at=data.get("executed_at"),
                rollback_deadline=data.get("rollback_deadline"),
            )

        except (ConnectionError, TimeoutError) as e:
            return ExecuteSwapResponse(
                success=False,
                message=f"Backend service unavailable: {type(e).__name__}",
                swap_id=request.swap_id,
            )
        except PermissionError as e:
            return ExecuteSwapResponse(
                success=False,
                message=f"Insufficient permissions to execute swap: {str(e)}",
                swap_id=request.swap_id,
            )
        except ValueError as e:
            return ExecuteSwapResponse(
                success=False,
                message=f"Invalid swap state or data: {str(e)}",
                swap_id=request.swap_id,
            )
        except Exception as e:
            return ExecuteSwapResponse(
                success=False,
                message=f"Failed to execute swap: {type(e).__name__}",
                swap_id=request.swap_id,
            )
