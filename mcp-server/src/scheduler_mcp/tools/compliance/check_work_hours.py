"""
Check work hours tool for ACGME 80-hour rule compliance.
"""

from typing import Any

from pydantic import BaseModel, Field

from ..base import BaseTool
from ..validator import validate_date_range, validate_person_id


class WorkHoursCheckRequest(BaseModel):
    """Request to check work hours."""

    person_id: str | None = Field(
        default=None, description="Optional person ID (check all if None)"
    )
    start_date: str = Field(..., description="Start date in YYYY-MM-DD format")
    end_date: str = Field(..., description="End date in YYYY-MM-DD format")
    include_details: bool = Field(
        default=True, description="Include detailed breakdown"
    )


class PersonWorkHours(BaseModel):
    """Work hours for a person."""

    person_id: str
    person_name: str | None = None
    total_hours: float
    weeks_analyzed: int
    average_hours_per_week: float
    max_week_hours: float
    violations: int
    compliant: bool


class WorkHoursCheckResponse(BaseModel):
    """Response from work hours check."""

    start_date: str
    end_date: str
    total_people_checked: int
    compliant_count: int
    violation_count: int
    overall_compliant: bool
    people: list[PersonWorkHours]


class CheckWorkHoursTool(BaseTool[WorkHoursCheckRequest, WorkHoursCheckResponse]):
    """
    Tool for checking ACGME 80-hour rule compliance.

    Validates that residents work no more than 80 hours per week
    averaged over 4-week periods.
    """

    @property
    def name(self) -> str:
        return "check_work_hours"

    @property
    def description(self) -> str:
        return (
            "Check ACGME 80-hour work week compliance. "
            "Validates work hours averaged over rolling 4-week periods."
        )

    def validate_input(self, **kwargs: Any) -> WorkHoursCheckRequest:
        """Validate input parameters."""
        # Validate dates
        start_date = kwargs.get("start_date", "")
        end_date = kwargs.get("end_date", "")
        validate_date_range(start_date, end_date, max_days=365)

        # Validate person_id if provided
        person_id = kwargs.get("person_id")
        if person_id is not None:
            person_id = validate_person_id(person_id)

        return WorkHoursCheckRequest(
            person_id=person_id,
            start_date=start_date,
            end_date=end_date,
            include_details=kwargs.get("include_details", True),
        )

    async def execute(
        self, request: WorkHoursCheckRequest
    ) -> WorkHoursCheckResponse:
        """Execute the tool."""
        client = self._require_api_client()

        try:
            # Check work hours via API
            params: dict[str, Any] = {
                "start_date": request.start_date,
                "end_date": request.end_date,
                "include_details": request.include_details,
            }
            if request.person_id:
                params["person_id"] = request.person_id

            result = await client.client.get(
                f"{client.config.api_prefix}/compliance/work-hours",
                headers=await client._ensure_authenticated(),
                params=params,
            )
            result.raise_for_status()
            data = result.json()

            # Parse people data
            people = []
            for item in data.get("people", []):
                person = PersonWorkHours(
                    person_id=item["person_id"],
                    person_name=item.get("person_name"),
                    total_hours=item.get("total_hours", 0.0),
                    weeks_analyzed=item.get("weeks_analyzed", 0),
                    average_hours_per_week=item.get("average_hours_per_week", 0.0),
                    max_week_hours=item.get("max_week_hours", 0.0),
                    violations=item.get("violations", 0),
                    compliant=item.get("compliant", False),
                )
                people.append(person)

            # Count compliant vs violations
            compliant_count = sum(1 for p in people if p.compliant)
            violation_count = len(people) - compliant_count

            return WorkHoursCheckResponse(
                start_date=request.start_date,
                end_date=request.end_date,
                total_people_checked=len(people),
                compliant_count=compliant_count,
                violation_count=violation_count,
                overall_compliant=violation_count == 0,
                people=people,
            )

        except Exception as e:
            # Return empty result on error
            return WorkHoursCheckResponse(
                start_date=request.start_date,
                end_date=request.end_date,
                total_people_checked=0,
                compliant_count=0,
                violation_count=0,
                overall_compliant=False,
                people=[],
            )
