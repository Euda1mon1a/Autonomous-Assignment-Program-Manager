"""
Coverage metrics tool for schedule coverage analysis.
"""

from typing import Any

from pydantic import BaseModel, Field

from ..base import BaseTool
from ..validator import validate_date_range


class CoverageMetricsRequest(BaseModel):
    """Request to get coverage metrics."""

    start_date: str = Field(..., description="Start date in YYYY-MM-DD format")
    end_date: str = Field(..., description="End date in YYYY-MM-DD format")
    by_rotation: bool = Field(
        default=True,
        description="Include breakdown by rotation",
    )


class RotationCoverage(BaseModel):
    """Coverage for a rotation."""

    rotation_name: str
    total_blocks: int
    covered_blocks: int
    uncovered_blocks: int
    coverage_rate: float = Field(ge=0.0, le=1.0)


class CoverageMetricsResponse(BaseModel):
    """Response from coverage metrics."""

    start_date: str
    end_date: str
    total_blocks: int
    covered_blocks: int
    uncovered_blocks: int
    overall_coverage_rate: float = Field(ge=0.0, le=1.0)
    rotations: list[RotationCoverage] = Field(default_factory=list)


class CoverageMetricsTool(BaseTool[CoverageMetricsRequest, CoverageMetricsResponse]):
    """
    Tool for analyzing schedule coverage.

    Calculates coverage rates overall and by rotation.
    """

    @property
    def name(self) -> str:
        return "coverage_metrics"

    @property
    def description(self) -> str:
        return (
            "Get schedule coverage metrics. "
            "Shows coverage rates overall and by rotation."
        )

    def validate_input(self, **kwargs: Any) -> CoverageMetricsRequest:
        """Validate input parameters."""
        # Validate dates
        start_date = kwargs.get("start_date", "")
        end_date = kwargs.get("end_date", "")
        validate_date_range(start_date, end_date, max_days=365)

        return CoverageMetricsRequest(
            start_date=start_date,
            end_date=end_date,
            by_rotation=kwargs.get("by_rotation", True),
        )

    async def execute(
        self, request: CoverageMetricsRequest
    ) -> CoverageMetricsResponse:
        """Execute the tool."""
        client = self._require_api_client()

        try:
            # Get coverage metrics via API
            result = await client.client.get(
                f"{client.config.api_prefix}/analytics/coverage",
                headers=await client._ensure_authenticated(),
                params={
                    "start_date": request.start_date,
                    "end_date": request.end_date,
                    "by_rotation": request.by_rotation,
                },
            )
            result.raise_for_status()
            data = result.json()

            # Parse rotations
            rotations = []
            if request.by_rotation:
                for item in data.get("rotations", []):
                    rotation = RotationCoverage(
                        rotation_name=item["rotation_name"],
                        total_blocks=item["total_blocks"],
                        covered_blocks=item["covered_blocks"],
                        uncovered_blocks=item["uncovered_blocks"],
                        coverage_rate=item["coverage_rate"],
                    )
                    rotations.append(rotation)

            return CoverageMetricsResponse(
                start_date=request.start_date,
                end_date=request.end_date,
                total_blocks=data.get("total_blocks", 0),
                covered_blocks=data.get("covered_blocks", 0),
                uncovered_blocks=data.get("uncovered_blocks", 0),
                overall_coverage_rate=data.get("overall_coverage_rate", 0.0),
                rotations=rotations,
            )

        except Exception as e:
            # Return empty metrics
            return CoverageMetricsResponse(
                start_date=request.start_date,
                end_date=request.end_date,
                total_blocks=0,
                covered_blocks=0,
                uncovered_blocks=0,
                overall_coverage_rate=0.0,
                rotations=[],
            )
