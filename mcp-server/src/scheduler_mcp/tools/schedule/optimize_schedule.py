"""
Optimize schedule tool for improving existing schedules.
"""

from typing import Any

from pydantic import BaseModel, Field

from ..base import BaseTool
from ..validator import validate_date_range, validate_float_range


class OptimizeScheduleRequest(BaseModel):
    """Request to optimize a schedule."""

    start_date: str = Field(..., description="Start date in YYYY-MM-DD format")
    end_date: str = Field(..., description="End date in YYYY-MM-DD format")
    objectives: list[str] = Field(
        default_factory=lambda: ["workload_balance", "preferences"],
        description="Optimization objectives",
    )
    preserve_assignments: bool = Field(
        default=True,
        description="Try to preserve existing assignments",
    )
    max_iterations: int = Field(
        default=100, ge=1, le=1000, description="Maximum optimization iterations"
    )
    timeout_seconds: float = Field(
        default=120.0,
        ge=10.0,
        le=600.0,
        description="Maximum optimization time",
    )


class OptimizeScheduleResponse(BaseModel):
    """Response from optimize schedule."""

    success: bool
    message: str
    start_date: str
    end_date: str
    improvements: dict[str, Any] = Field(default_factory=dict)
    assignments_changed: int
    iterations_run: int
    optimization_time_ms: float | None = None


class OptimizeScheduleTool(
    BaseTool[OptimizeScheduleRequest, OptimizeScheduleResponse]
):
    """
    Tool for optimizing existing schedules.

    Improves workload balance, preference satisfaction, and coverage
    while maintaining ACGME compliance.
    """

    @property
    def name(self) -> str:
        return "optimize_schedule"

    @property
    def description(self) -> str:
        return (
            "Optimize an existing schedule to improve workload balance, "
            "preference satisfaction, and coverage quality. "
            "Maintains ACGME compliance during optimization."
        )

    def validate_input(self, **kwargs: Any) -> OptimizeScheduleRequest:
        """Validate input parameters."""
        # Validate dates
        start_date = kwargs.get("start_date", "")
        end_date = kwargs.get("end_date", "")
        validate_date_range(start_date, end_date, max_days=365)

        # Validate timeout
        timeout_seconds = validate_float_range(
            kwargs.get("timeout_seconds", 120.0),
            field_name="timeout_seconds",
            min_value=10.0,
            max_value=600.0,
        )

        # Validate objectives
        valid_objectives = [
            "workload_balance",
            "preferences",
            "coverage",
            "minimize_changes",
        ]
        objectives = kwargs.get("objectives", ["workload_balance", "preferences"])
        if not isinstance(objectives, list):
            objectives = [objectives]

        for obj in objectives:
            if obj not in valid_objectives:
                from ..base import ValidationError

                raise ValidationError(
                    f"Invalid objective: {obj}",
                    details={"value": obj, "valid": valid_objectives},
                )

        return OptimizeScheduleRequest(
            start_date=start_date,
            end_date=end_date,
            objectives=objectives,
            preserve_assignments=kwargs.get("preserve_assignments", True),
            max_iterations=kwargs.get("max_iterations", 100),
            timeout_seconds=timeout_seconds,
        )

    async def execute(
        self, request: OptimizeScheduleRequest
    ) -> OptimizeScheduleResponse:
        """
        Execute schedule optimization.

        Improves an existing schedule using multi-objective optimization while
        maintaining ACGME compliance. Uses iterative local search to:
        - Balance workload across residents and faculty
        - Maximize preference satisfaction
        - Improve coverage quality
        - Minimize unnecessary changes (if preserve_assignments=True)

        Optimization Objectives:
        - workload_balance: Minimize variance in hours worked
        - preferences: Maximize match to requested rotations/blocks
        - coverage: Optimize coverage quality (supervision ratios, expertise)
        - minimize_changes: Preserve existing assignments when possible

        Args:
            request: Validated request with objectives, date range, and constraints

        Returns:
            OptimizeScheduleResponse with improvement metrics and changes count

        Raises:
            APIError: Backend API request fails
            TimeoutError: Optimization exceeds timeout_seconds limit
            ValidationError: Invalid objectives or constraints
        """
        client = self._require_api_client()

        try:
            # Optimize schedule via API
            result = await client.client.post(
                f"{client.config.api_prefix}/schedule/optimize",
                headers=await client._ensure_authenticated(),
                json={
                    "start_date": request.start_date,
                    "end_date": request.end_date,
                    "objectives": request.objectives,
                    "preserve_assignments": request.preserve_assignments,
                    "max_iterations": request.max_iterations,
                    "timeout_seconds": request.timeout_seconds,
                },
                timeout=max(request.timeout_seconds + 30, client.config.timeout),
            )
            result.raise_for_status()
            data = result.json()

            return OptimizeScheduleResponse(
                success=True,
                message="Schedule optimized successfully",
                start_date=request.start_date,
                end_date=request.end_date,
                improvements=data.get("improvements", {}),
                assignments_changed=data.get("assignments_changed", 0),
                iterations_run=data.get("iterations_run", 0),
                optimization_time_ms=data.get("optimization_time_ms"),
            )

        except TimeoutError as e:
            return OptimizeScheduleResponse(
                success=False,
                message=f"Optimization timed out after {request.timeout_seconds}s",
                start_date=request.start_date,
                end_date=request.end_date,
                assignments_changed=0,
                iterations_run=0,
            )
        except (ConnectionError, OSError) as e:
            return OptimizeScheduleResponse(
                success=False,
                message=f"Backend service unavailable: {type(e).__name__}",
                start_date=request.start_date,
                end_date=request.end_date,
                assignments_changed=0,
                iterations_run=0,
            )
        except ValueError as e:
            return OptimizeScheduleResponse(
                success=False,
                message=f"Invalid optimization parameters: {str(e)}",
                start_date=request.start_date,
                end_date=request.end_date,
                assignments_changed=0,
                iterations_run=0,
            )
        except Exception as e:
            return OptimizeScheduleResponse(
                success=False,
                message=f"Failed to optimize schedule: {type(e).__name__}",
                start_date=request.start_date,
                end_date=request.end_date,
                assignments_changed=0,
                iterations_run=0,
            )
