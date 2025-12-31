"""
Get burnout Rt tool for epidemiological burnout tracking.
"""

from typing import Any

from pydantic import BaseModel, Field

from ..base import BaseTool
from ..validator import validate_date_string


class GetBurnoutRtRequest(BaseModel):
    """Request to get burnout Rt."""

    date: str | None = Field(
        default=None,
        description="Optional date (defaults to today)",
    )


class GetBurnoutRtResponse(BaseModel):
    """Response from get burnout Rt."""

    date: str
    rt_value: float = Field(ge=0.0)
    trend: str  # declining, stable, growing, epidemic
    susceptible: int
    infected: int
    recovered: int
    recommendations: list[str] = Field(default_factory=list)


class GetBurnoutRtTool(BaseTool[GetBurnoutRtRequest, GetBurnoutRtResponse]):
    """
    Tool for getting burnout reproduction number (Rt).

    Uses SIR epidemiological model to track burnout spread.
    """

    @property
    def name(self) -> str:
        return "get_burnout_rt"

    @property
    def description(self) -> str:
        return (
            "Get burnout reproduction number (Rt) using SIR model. "
            "Tracks burnout spread like infectious disease."
        )

    def validate_input(self, **kwargs: Any) -> GetBurnoutRtRequest:
        """Validate input parameters."""
        # Validate date if provided
        date_value = kwargs.get("date")
        if date_value is not None:
            date_value = validate_date_string(date_value)

        return GetBurnoutRtRequest(date=date_value)

    async def execute(
        self, request: GetBurnoutRtRequest
    ) -> GetBurnoutRtResponse:
        """Execute the tool."""
        client = self._require_api_client()

        try:
            # Build params
            params: dict[str, Any] = {}
            if request.date:
                params["date"] = request.date

            # Get burnout Rt via API
            result = await client.client.get(
                f"{client.config.api_prefix}/resilience/burnout-rt",
                headers=await client._ensure_authenticated(),
                params=params,
            )
            result.raise_for_status()
            data = result.json()

            # Determine trend
            rt = data.get("rt_value", 0.0)
            if rt < 0.9:
                trend = "declining"
            elif rt < 1.1:
                trend = "stable"
            elif rt < 1.5:
                trend = "growing"
            else:
                trend = "epidemic"

            return GetBurnoutRtResponse(
                date=data.get("date", request.date or ""),
                rt_value=rt,
                trend=trend,
                susceptible=data.get("susceptible", 0),
                infected=data.get("infected", 0),
                recovered=data.get("recovered", 0),
                recommendations=data.get("recommendations", []),
            )

        except Exception as e:
            # Return safe default
            return GetBurnoutRtResponse(
                date=request.date or "",
                rt_value=0.0,
                trend="unknown",
                susceptible=0,
                infected=0,
                recovered=0,
                recommendations=[f"Error: {e}"],
            )
