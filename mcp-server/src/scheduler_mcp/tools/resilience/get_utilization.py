"""
Get utilization tool for workload metrics.
"""

from typing import Any

from pydantic import BaseModel, Field

from ..base import BaseTool
from ..validator import validate_date_range


class GetUtilizationRequest(BaseModel):
    """Request to get utilization."""

    start_date: str = Field(..., description="Start date in YYYY-MM-DD format")
    end_date: str = Field(..., description="End date in YYYY-MM-DD format")


class UtilizationMetrics(BaseModel):
    """Utilization metrics."""

    average_utilization: float = Field(ge=0.0, le=1.0)
    max_utilization: float = Field(ge=0.0, le=1.0)
    threshold_80_exceeded_days: int
    total_person_days: int
    over_capacity_days: int


class GetUtilizationResponse(BaseModel):
    """Response from get utilization."""

    start_date: str
    end_date: str
    metrics: UtilizationMetrics
    status: str  # safe, warning, critical
    recommendations: list[str] = Field(default_factory=list)


class GetUtilizationTool(BaseTool[GetUtilizationRequest, GetUtilizationResponse]):
    """
    Tool for getting utilization metrics.

    Calculates workload utilization and checks against 80% threshold.
    """

    @property
    def name(self) -> str:
        return "get_utilization"

    @property
    def description(self) -> str:
        return (
            "Get workload utilization metrics. "
            "Checks against 80% threshold from queuing theory."
        )

    def validate_input(self, **kwargs: Any) -> GetUtilizationRequest:
        """Validate input parameters."""
        # Validate dates
        start_date = kwargs.get("start_date", "")
        end_date = kwargs.get("end_date", "")
        validate_date_range(start_date, end_date, max_days=365)

        return GetUtilizationRequest(
            start_date=start_date,
            end_date=end_date,
        )

    async def execute(
        self, request: GetUtilizationRequest
    ) -> GetUtilizationResponse:
        """Execute the tool."""
        client = self._require_api_client()

        try:
            # Get utilization via API
            result = await client.client.get(
                f"{client.config.api_prefix}/resilience/utilization",
                headers=await client._ensure_authenticated(),
                params={
                    "start_date": request.start_date,
                    "end_date": request.end_date,
                },
            )
            result.raise_for_status()
            data = result.json()

            # Parse metrics
            metrics = UtilizationMetrics(
                average_utilization=data.get("average_utilization", 0.0),
                max_utilization=data.get("max_utilization", 0.0),
                threshold_80_exceeded_days=data.get("threshold_80_exceeded_days", 0),
                total_person_days=data.get("total_person_days", 0),
                over_capacity_days=data.get("over_capacity_days", 0),
            )

            # Determine status
            if metrics.average_utilization >= 0.9:
                status = "critical"
            elif metrics.average_utilization >= 0.8:
                status = "warning"
            else:
                status = "safe"

            return GetUtilizationResponse(
                start_date=request.start_date,
                end_date=request.end_date,
                metrics=metrics,
                status=status,
                recommendations=data.get("recommendations", []),
            )

        except Exception as e:
            # Return empty metrics
            return GetUtilizationResponse(
                start_date=request.start_date,
                end_date=request.end_date,
                metrics=UtilizationMetrics(
                    average_utilization=0.0,
                    max_utilization=0.0,
                    threshold_80_exceeded_days=0,
                    total_person_days=0,
                    over_capacity_days=0,
                ),
                status="unknown",
                recommendations=[f"Error: {e}"],
            )
