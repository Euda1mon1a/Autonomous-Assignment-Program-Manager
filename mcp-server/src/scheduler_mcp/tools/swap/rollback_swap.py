"""
Rollback swap tool for reversing completed swaps.
"""

from typing import Any

from pydantic import BaseModel, Field

from ..base import BaseTool
from ..validator import validate_person_id


class RollbackSwapRequest(BaseModel):
    """Request to rollback a swap."""

    swap_id: str = Field(..., description="Swap ID to rollback")
    reason: str | None = Field(default=None, description="Rollback reason")


class RollbackSwapResponse(BaseModel):
    """Response from rollback swap."""

    success: bool
    message: str
    swap_id: str
    rolled_back_at: str | None = None


class RollbackSwapTool(BaseTool[RollbackSwapRequest, RollbackSwapResponse]):
    """
    Tool for rolling back completed swaps.

    Reverses a swap within the 24-hour rollback window.
    """

    @property
    def name(self) -> str:
        return "rollback_swap"

    @property
    def description(self) -> str:
        return (
            "Rollback a completed swap within the 24-hour window. "
            "Restores original assignments."
        )

    def validate_input(self, **kwargs: Any) -> RollbackSwapRequest:
        """Validate input parameters."""
        # Validate swap_id
        swap_id = validate_person_id(kwargs.get("swap_id", ""), "swap_id")

        return RollbackSwapRequest(
            swap_id=swap_id,
            reason=kwargs.get("reason"),
        )

    async def execute(
        self, request: RollbackSwapRequest
    ) -> RollbackSwapResponse:
        """
        Execute swap rollback.

        Reverses a completed swap within the 24-hour rollback window by restoring
        the original assignments. After rollback:
        - Swap status changes to "rolled_back"
        - Original assignments are restored
        - Rollback timestamp is recorded
        - Notifications sent to affected parties

        Rollback Window:
        - Available for 24 hours after swap execution
        - Automatically expires after deadline
        - Can be performed by swap requester or program coordinator

        Rollback Process:
        1. Verify swap is in "executed" status
        2. Check rollback deadline hasn't passed
        3. Restore original assignments
        4. Update swap status
        5. Log rollback event

        Args:
            request: Validated request with swap_id and optional reason

        Returns:
            RollbackSwapResponse with success status and rollback timestamp

        Raises:
            APIError: Backend API request fails
            NotFoundError: Swap does not exist
            ValidationError: Swap cannot be rolled back (wrong status or expired deadline)
        """
        client = self._require_api_client()

        try:
            # Rollback swap via API
            result = await client.client.post(
                f"{client.config.api_prefix}/swaps/{request.swap_id}/rollback",
                headers=await client._ensure_authenticated(),
                json={
                    "reason": request.reason,
                },
            )
            result.raise_for_status()
            data = result.json()

            return RollbackSwapResponse(
                success=True,
                message="Swap rolled back successfully",
                swap_id=request.swap_id,
                rolled_back_at=data.get("rolled_back_at"),
            )

        except (ConnectionError, TimeoutError) as e:
            return RollbackSwapResponse(
                success=False,
                message=f"Backend service unavailable: {type(e).__name__}",
                swap_id=request.swap_id,
            )
        except KeyError as e:
            return RollbackSwapResponse(
                success=False,
                message=f"Swap not found: {request.swap_id}",
                swap_id=request.swap_id,
            )
        except ValueError as e:
            return RollbackSwapResponse(
                success=False,
                message=f"Cannot rollback swap: {str(e)}",
                swap_id=request.swap_id,
            )
        except Exception as e:
            return RollbackSwapResponse(
                success=False,
                message=f"Failed to rollback swap: {type(e).__name__}",
                swap_id=request.swap_id,
            )
