"""
Get Natural Swaps tool for Foam Topology Scheduler.
"""

from typing import Any

from pydantic import BaseModel, Field

from ..base import BaseTool


class FoamSwapRecommendation(BaseModel):
    resident_a: str
    resident_b: str
    block_a: str
    block_b: str
    energy_improvement: float
    constraint_margin: float
    natural_score: float


class GetNaturalSwapsRequest(BaseModel):
    """Request to get natural swaps."""

    schedule_id: str = Field(..., description="ID of the schedule to analyze")
    n: int = Field(default=5, description="Number of swap recommendations to return")


class GetNaturalSwapsResponse(BaseModel):
    """Response from get natural swaps."""

    analyzed_at: str
    schedule_id: str
    recommendations: list[FoamSwapRecommendation]


class GetNaturalSwapsTool(BaseTool[GetNaturalSwapsRequest, GetNaturalSwapsResponse]):
    """
    Tool for getting natural schedule swaps using Foam Topology.
    """

    @property
    def name(self) -> str:
        return "get_natural_swaps"

    @property
    def description(self) -> str:
        return (
            "Get natural swap opportunities using Foam Topology dynamics. "
            "Returns topologically sound schedule trades."
        )

    def validate_input(self, **kwargs: Any) -> GetNaturalSwapsRequest:
        """Validate input parameters."""
        if "schedule_id" not in kwargs:
            raise ValueError("schedule_id is required")
        return GetNaturalSwapsRequest(**kwargs)

    async def execute(self, request: GetNaturalSwapsRequest) -> GetNaturalSwapsResponse:
        client = self._require_api_client()

        try:
            result = await client.client.get(
                f"{client.config.api_prefix}/foam-topology/{request.schedule_id}/natural-swaps?n={request.n}",
                headers=await client._ensure_authenticated(),
            )
            result.raise_for_status()
            data = result.json()

            return GetNaturalSwapsResponse(**data)

        except Exception:
            # Fallback for errors
            return GetNaturalSwapsResponse(
                analyzed_at="",
                schedule_id=request.schedule_id,
                recommendations=[],
            )
