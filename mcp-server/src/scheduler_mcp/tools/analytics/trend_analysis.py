"""
Trend analysis tool for identifying scheduling patterns and anomalies.
"""

from typing import Any

from pydantic import BaseModel, Field

from ..base import BaseTool
from ..validator import validate_date_range


class TrendPoint(BaseModel):
    """A trend data point."""

    date: str
    value: float
    is_anomaly: bool = False


class Trend(BaseModel):
    """A trend line."""

    metric: str
    direction: str  # increasing, decreasing, stable
    slope: float
    data_points: list[TrendPoint]


class TrendAnalysisRequest(BaseModel):
    """Request to analyze trends."""

    start_date: str = Field(..., description="Start date in YYYY-MM-DD format")
    end_date: str = Field(..., description="End date in YYYY-MM-DD format")
    metrics: list[str] = Field(
        default_factory=lambda: ["utilization", "coverage", "violations"],
        description="Metrics to analyze",
    )


class TrendAnalysisResponse(BaseModel):
    """Response from trend analysis."""

    start_date: str
    end_date: str
    trends: list[Trend]
    anomalies_detected: int
    insights: list[str] = Field(default_factory=list)


class TrendAnalysisTool(BaseTool[TrendAnalysisRequest, TrendAnalysisResponse]):
    """
    Tool for analyzing scheduling trends.

    Identifies patterns, anomalies, and provides insights.
    """

    @property
    def name(self) -> str:
        return "trend_analysis"

    @property
    def description(self) -> str:
        return (
            "Analyze scheduling trends over time. "
            "Detects patterns, anomalies, and provides insights."
        )

    def validate_input(self, **kwargs: Any) -> TrendAnalysisRequest:
        """Validate input parameters."""
        # Validate dates
        start_date = kwargs.get("start_date", "")
        end_date = kwargs.get("end_date", "")
        validate_date_range(start_date, end_date, max_days=365)

        # Validate metrics
        valid_metrics = ["utilization", "coverage", "violations", "workload"]
        metrics = kwargs.get("metrics", ["utilization", "coverage", "violations"])
        if not isinstance(metrics, list):
            metrics = [metrics]

        for metric in metrics:
            if metric not in valid_metrics:
                from ..base import ValidationError

                raise ValidationError(
                    f"Invalid metric: {metric}",
                    details={"value": metric, "valid": valid_metrics},
                )

        return TrendAnalysisRequest(
            start_date=start_date,
            end_date=end_date,
            metrics=metrics,
        )

    async def execute(
        self, request: TrendAnalysisRequest
    ) -> TrendAnalysisResponse:
        """Execute the tool."""
        client = self._require_api_client()

        try:
            # Get trend analysis via API
            result = await client.client.post(
                f"{client.config.api_prefix}/analytics/trends",
                headers=await client._ensure_authenticated(),
                json={
                    "start_date": request.start_date,
                    "end_date": request.end_date,
                    "metrics": request.metrics,
                },
            )
            result.raise_for_status()
            data = result.json()

            # Parse trends
            trends = []
            total_anomalies = 0
            for item in data.get("trends", []):
                # Parse data points
                data_points = []
                for point in item.get("data_points", []):
                    dp = TrendPoint(
                        date=point["date"],
                        value=point["value"],
                        is_anomaly=point.get("is_anomaly", False),
                    )
                    if dp.is_anomaly:
                        total_anomalies += 1
                    data_points.append(dp)

                trend = Trend(
                    metric=item["metric"],
                    direction=item.get("direction", "stable"),
                    slope=item.get("slope", 0.0),
                    data_points=data_points,
                )
                trends.append(trend)

            return TrendAnalysisResponse(
                start_date=request.start_date,
                end_date=request.end_date,
                trends=trends,
                anomalies_detected=total_anomalies,
                insights=data.get("insights", []),
            )

        except Exception as e:
            # Return empty analysis
            return TrendAnalysisResponse(
                start_date=request.start_date,
                end_date=request.end_date,
                trends=[],
                anomalies_detected=0,
                insights=[f"Error: {e}"],
            )
