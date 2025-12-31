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
        """Execute the tool."""
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

        except Exception as e:
            return ExecuteSwapResponse(
                success=False,
                message=f"Failed to execute swap: {e}",
                swap_id=request.swap_id,
            )
