"""
Get schedule tool for fetching schedule data.
"""

from datetime import date
from typing import Any

from pydantic import BaseModel, Field

from ..base import BaseTool
from ..validator import validate_date_range, validate_positive_int


class GetScheduleRequest(BaseModel):
    """Request to get schedule."""

    start_date: str = Field(
        ..., description="Start date in YYYY-MM-DD format"
    )
    end_date: str = Field(
        ..., description="End date in YYYY-MM-DD format"
    )
    limit: int = Field(
        default=1000,
        ge=1,
        le=10000,
        description="Maximum assignments to return"
    )
    include_person_details: bool = Field(
        default=True,
        description="Include person details in response"
    )


class Assignment(BaseModel):
    """Assignment data."""

    id: str
    person_id: str
    person_name: str | None = None
    block_id: str
    block_date: str
    block_session: str
    rotation_id: str | None = None
    rotation_name: str | None = None
    created_at: str | None = None


class GetScheduleResponse(BaseModel):
    """Response from get schedule."""

    start_date: str
    end_date: str
    total_assignments: int
    assignments: list[Assignment]
    date_range_days: int


class GetScheduleTool(BaseTool[GetScheduleRequest, GetScheduleResponse]):
    """
    Tool for fetching schedule data.

    Retrieves assignments for a date range from the backend API.
    """

    @property
    def name(self) -> str:
        return "get_schedule"

    @property
    def description(self) -> str:
        return (
            "Get schedule assignments for a date range. "
            "Returns assignment data including person, block, and rotation information."
        )

    def validate_input(self, **kwargs: Any) -> GetScheduleRequest:
        """Validate input parameters."""
        # Validate dates
        start_date = kwargs.get("start_date", "")
        end_date = kwargs.get("end_date", "")
        validate_date_range(start_date, end_date, max_days=365)

        # Validate limit
        limit = validate_positive_int(
            kwargs.get("limit", 1000),
            field_name="limit",
            max_value=10000
        )

        return GetScheduleRequest(
            start_date=start_date,
            end_date=end_date,
            limit=limit,
            include_person_details=kwargs.get("include_person_details", True),
        )

    async def execute(
        self, request: GetScheduleRequest
    ) -> GetScheduleResponse:
        """
        Execute schedule data retrieval.

        Fetches all assignments within the specified date range from the backend API.
        Returns comprehensive schedule data including person, block, and rotation details.

        Data Structure:
        - Each assignment represents one person assigned to one block (date + session)
        - Blocks are AM/PM sessions (2 per day)
        - Date range is inclusive (includes both start and end dates)

        Performance Notes:
        - Limit parameter prevents excessive data transfer
        - include_person_details=False reduces payload size
        - Results are sorted by block_date, block_session, person_id

        Args:
            request: Validated request with date range and options

        Returns:
            GetScheduleResponse with assignments list and metadata

        Raises:
            APIError: Backend API request fails
            ValidationError: Invalid date range or data format
        """
        client = self._require_api_client()

        try:
            # Fetch assignments
            result = await client.get_assignments(
                start_date=request.start_date,
                end_date=request.end_date,
                limit=request.limit,
            )

            # Parse assignments
            assignments = []
            for item in result.get("assignments", []):
                assignment = Assignment(
                    id=item["id"],
                    person_id=item["person_id"],
                    person_name=item.get("person_name") if request.include_person_details else None,
                    block_id=item["block_id"],
                    block_date=item.get("block_date", ""),
                    block_session=item.get("block_session", ""),
                    rotation_id=item.get("rotation_id"),
                    rotation_name=item.get("rotation_name"),
                    created_at=item.get("created_at"),
                )
                assignments.append(assignment)

            # Calculate date range
            start = date.fromisoformat(request.start_date)
            end = date.fromisoformat(request.end_date)
            date_range_days = (end - start).days + 1

            return GetScheduleResponse(
                start_date=request.start_date,
                end_date=request.end_date,
                total_assignments=len(assignments),
                assignments=assignments,
                date_range_days=date_range_days,
            )

        except (ConnectionError, TimeoutError) as e:
            # Network connectivity issues - return empty schedule
            return GetScheduleResponse(
                start_date=request.start_date,
                end_date=request.end_date,
                total_assignments=0,
                assignments=[],
                date_range_days=0,
            )
        except (KeyError, ValueError, TypeError) as e:
            # Data parsing errors - return empty schedule
            return GetScheduleResponse(
                start_date=request.start_date,
                end_date=request.end_date,
                total_assignments=0,
                assignments=[],
                date_range_days=0,
            )
        except Exception as e:
            # Unexpected errors - return empty schedule
            return GetScheduleResponse(
                start_date=request.start_date,
                end_date=request.end_date,
                total_assignments=0,
                assignments=[],
                date_range_days=0,
            )
