"""
Get defense level tool for resilience status.
"""

from typing import Any

from pydantic import BaseModel, Field

from ..base import BaseTool
from ..validator import validate_date_string


class GetDefenseLevelRequest(BaseModel):
    """Request to get defense level."""

    date: str | None = Field(
        default=None,
        description="Optional date (defaults to today)",
    )


class GetDefenseLevelResponse(BaseModel):
    """Response from get defense level."""

    date: str
    defense_level: str  # GREEN, YELLOW, ORANGE, RED, BLACK
    utilization: float = Field(ge=0.0, le=1.0)
    burnout_rt: float = Field(ge=0.0)
    early_warnings: int
    status_message: str
    recommendations: list[str] = Field(default_factory=list)


class GetDefenseLevelTool(
    BaseTool[GetDefenseLevelRequest, GetDefenseLevelResponse]
):
    """
    Tool for getting current defense level.

    Returns the resilience defense level (GREEN → BLACK) based on
    utilization, burnout Rt, and early warning signals.
    """

    @property
    def name(self) -> str:
        return "get_defense_level"

    @property
    def description(self) -> str:
        return (
            "Get current resilience defense level. "
            "Returns status (GREEN/YELLOW/ORANGE/RED/BLACK) with metrics."
        )

    def validate_input(self, **kwargs: Any) -> GetDefenseLevelRequest:
        """Validate input parameters."""
        # Validate date if provided
        date_value = kwargs.get("date")
        if date_value is not None:
            date_value = validate_date_string(date_value)

        return GetDefenseLevelRequest(date=date_value)

    async def execute(
        self, request: GetDefenseLevelRequest
    ) -> GetDefenseLevelResponse:
        """
        Execute defense level calculation.

        Returns current resilience status using Defense in Depth 5-level system
        (borrowed from cybersecurity). Combines utilization, burnout Rt, and early
        warning signals into unified threat level.

        Defense Levels:
        - GREEN: Normal operations (utilization < 70%, Rt < 0.9, no warnings)
        - YELLOW: Elevated watch (utilization 70-80%, Rt 0.9-1.1, minor warnings)
        - ORANGE: Heightened alert (utilization 80-90%, Rt 1.1-1.5, warnings present)
        - RED: Severe risk (utilization 90-95%, Rt > 1.5, critical warnings)
        - BLACK: Critical failure (utilization > 95%, epidemic burnout, system collapse imminent)

        Args:
            request: Validated request with optional date (defaults to today)

        Returns:
            GetDefenseLevelResponse with level, metrics, and recommendations

        Raises:
            APIError: Backend API request fails
            ValidationError: Invalid date format
        """
        client = self._require_api_client()

        try:
            # Build params
            params: dict[str, Any] = {}
            if request.date:
                params["date"] = request.date

            # Get defense level via API
            result = await client.client.get(
                f"{client.config.api_prefix}/resilience/defense-level",
                headers=await client._ensure_authenticated(),
                params=params,
            )
            result.raise_for_status()
            data = result.json()

            return GetDefenseLevelResponse(
                date=data.get("date", request.date or ""),
                defense_level=data.get("defense_level", "UNKNOWN"),
                utilization=data.get("utilization", 0.0),
                burnout_rt=data.get("burnout_rt", 0.0),
                early_warnings=data.get("early_warnings", 0),
                status_message=data.get("status_message", ""),
                recommendations=data.get("recommendations", []),
            )

        except (ConnectionError, TimeoutError) as e:
            # Network connectivity issues
            return GetDefenseLevelResponse(
                date=request.date or "",
                defense_level="UNKNOWN",
                utilization=0.0,
                burnout_rt=0.0,
                early_warnings=0,
                status_message=f"Backend service unavailable: {type(e).__name__}",
                recommendations=[],
            )
        except (KeyError, ValueError) as e:
            # Data parsing errors
            return GetDefenseLevelResponse(
                date=request.date or "",
                defense_level="UNKNOWN",
                utilization=0.0,
                burnout_rt=0.0,
                early_warnings=0,
                status_message=f"Invalid response data: {type(e).__name__}",
                recommendations=[],
            )
        except Exception as e:
            # Unexpected errors
            return GetDefenseLevelResponse(
                date=request.date or "",
                defense_level="UNKNOWN",
                utilization=0.0,
                burnout_rt=0.0,
                early_warnings=0,
                status_message=f"Error: {type(e).__name__}",
                recommendations=[],
            )
