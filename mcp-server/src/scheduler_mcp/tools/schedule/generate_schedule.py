"""
Generate schedule tool for creating optimized schedules.
"""

from typing import Any

from pydantic import BaseModel, Field

from ..base import BaseTool
from ..validator import validate_algorithm, validate_date_range, validate_float_range


class GenerateScheduleRequest(BaseModel):
    """Request to generate a schedule."""

    start_date: str = Field(..., description="Start date in YYYY-MM-DD format")
    end_date: str = Field(..., description="End date in YYYY-MM-DD format")
    algorithm: str = Field(
        default="greedy",
        description="Scheduling algorithm (greedy, cp_sat, pulp, hybrid)",
    )
    timeout_seconds: float = Field(
        default=60.0,
        ge=5.0,
        le=300.0,
        description="Maximum solver runtime in seconds",
    )
    clear_existing: bool = Field(
        default=True,
        description="Clear existing assignments before generating",
    )


class GenerateScheduleResponse(BaseModel):
    """Response from generate schedule."""

    success: bool
    message: str
    start_date: str
    end_date: str
    algorithm: str
    assignments_created: int
    validation_passed: bool
    solver_time_ms: float | None = None
    details: dict[str, Any] = Field(default_factory=dict)


class GenerateScheduleTool(
    BaseTool[GenerateScheduleRequest, GenerateScheduleResponse]
):
    """
    Tool for generating optimized schedules.

    Uses constraint-based algorithms to generate ACGME-compliant schedules.
    """

    @property
    def name(self) -> str:
        return "generate_schedule"

    @property
    def description(self) -> str:
        return (
            "Generate an optimized schedule for a date range. "
            "Uses constraint programming to ensure ACGME compliance. "
            "Supports multiple algorithms: greedy, cp_sat, pulp, hybrid."
        )

    def validate_input(self, **kwargs: Any) -> GenerateScheduleRequest:
        """Validate input parameters."""
        # Validate dates
        start_date = kwargs.get("start_date", "")
        end_date = kwargs.get("end_date", "")
        validate_date_range(start_date, end_date, max_days=365)

        # Validate algorithm
        algorithm = validate_algorithm(kwargs.get("algorithm", "greedy"))

        # Validate timeout
        timeout_seconds = validate_float_range(
            kwargs.get("timeout_seconds", 60.0),
            field_name="timeout_seconds",
            min_value=5.0,
            max_value=300.0,
        )

        return GenerateScheduleRequest(
            start_date=start_date,
            end_date=end_date,
            algorithm=algorithm,
            timeout_seconds=timeout_seconds,
            clear_existing=kwargs.get("clear_existing", True),
        )

    async def execute(
        self, request: GenerateScheduleRequest
    ) -> GenerateScheduleResponse:
        """Execute the tool."""
        client = self._require_api_client()

        try:
            # Generate schedule via API
            result = await client.generate_schedule(
                start_date=request.start_date,
                end_date=request.end_date,
                algorithm=request.algorithm,
                timeout_seconds=request.timeout_seconds,
                clear_existing=request.clear_existing,
            )

            return GenerateScheduleResponse(
                success=True,
                message="Schedule generated successfully",
                start_date=request.start_date,
                end_date=request.end_date,
                algorithm=request.algorithm,
                assignments_created=result.get("assignments_created", 0),
                validation_passed=result.get("validation_passed", False),
                solver_time_ms=result.get("solver_time_ms"),
                details=result,
            )

        except Exception as e:
            return GenerateScheduleResponse(
                success=False,
                message=f"Failed to generate schedule: {e}",
                start_date=request.start_date,
                end_date=request.end_date,
                algorithm=request.algorithm,
                assignments_created=0,
                validation_passed=False,
                details={"error": str(e)},
            )
