"""
Clear half-day assignments tool for pre-generation cleanup.

Clears solver/template half-day assignments for a date range while
preserving preload (FMIT, call, absences) and manual overrides.
"""

from typing import Any

from pydantic import BaseModel, Field

from ..base import BaseTool
from ..validator import validate_date_range


class ClearHalfDayAssignmentsRequest(BaseModel):
    """Request to clear half-day assignments."""

    start_date: str = Field(..., description="Start date in YYYY-MM-DD format")
    end_date: str = Field(..., description="End date in YYYY-MM-DD format")
    sources: str = Field(
        default="solver,template",
        description="Comma-separated sources to clear (solver, template). Preload and manual are always preserved.",
    )


class ClearHalfDayAssignmentsResponse(BaseModel):
    """Response from clearing half-day assignments."""

    success: bool
    message: str
    deleted_count: int = 0
    start_date: str = ""
    end_date: str = ""
    sources: list[str] = Field(default_factory=list)


class ClearHalfDayAssignmentsTool(
    BaseTool[ClearHalfDayAssignmentsRequest, ClearHalfDayAssignmentsResponse]
):
    """
    Tool for clearing solver/template half-day assignments.

    Use before schedule generation to ensure a clean slate for the solver
    without losing preloaded obligations or manual overrides.
    """

    @property
    def name(self) -> str:
        return "clear_half_day_assignments"

    @property
    def description(self) -> str:
        return (
            "Clear solver and template half-day assignments for a date range. "
            "Preserves preload (FMIT, call, absences) and manual overrides. "
            "Use before schedule generation to ensure a clean slate."
        )

    def validate_input(self, **kwargs: Any) -> ClearHalfDayAssignmentsRequest:
        """Validate input parameters."""
        start_date = kwargs.get("start_date", "")
        end_date = kwargs.get("end_date", "")
        validate_date_range(start_date, end_date, max_days=365)

        sources = kwargs.get("sources", "solver,template")
        # Validate source values
        allowed = {"solver", "template"}
        requested = {s.strip() for s in sources.split(",")}
        invalid = requested - allowed
        if invalid:
            raise ValueError(
                f"Cannot clear protected sources: {', '.join(sorted(invalid))}. "
                f"Only solver and template may be cleared."
            )

        return ClearHalfDayAssignmentsRequest(
            start_date=start_date,
            end_date=end_date,
            sources=sources,
        )

    async def execute(
        self, request: ClearHalfDayAssignmentsRequest
    ) -> ClearHalfDayAssignmentsResponse:
        """
        Clear half-day assignments via the backend API.

        Removes solver and/or template half-day assignments for the
        specified date range. Preload and manual assignments are always
        preserved regardless of the sources parameter.

        Args:
            request: Validated request with date range and sources

        Returns:
            ClearHalfDayAssignmentsResponse with deletion count
        """
        client = self._require_api_client()

        try:
            result = await client.clear_half_day_assignments(
                start_date=request.start_date,
                end_date=request.end_date,
                sources=request.sources,
            )

            deleted = result.get("deleted", 0)
            sources = result.get("sources", [])

            return ClearHalfDayAssignmentsResponse(
                success=True,
                message=f"Cleared {deleted} half-day assignments",
                deleted_count=deleted,
                start_date=request.start_date,
                end_date=request.end_date,
                sources=sources,
            )

        except (ConnectionError, TimeoutError) as e:
            return ClearHalfDayAssignmentsResponse(
                success=False,
                message=f"Backend service unavailable: {type(e).__name__}",
            )
        except ValueError as e:
            return ClearHalfDayAssignmentsResponse(
                success=False,
                message=f"Invalid parameters: {str(e)}",
            )
        except Exception as e:
            return ClearHalfDayAssignmentsResponse(
                success=False,
                message=f"Failed to clear half-day assignments: {type(e).__name__}",
            )
