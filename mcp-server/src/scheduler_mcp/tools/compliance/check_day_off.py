"""
Check day-off tool for ACGME 1-in-7 rule compliance.
"""

from typing import Any

from pydantic import BaseModel, Field

from ..base import BaseTool
from ..validator import validate_date_range, validate_person_id


class DayOffCheckRequest(BaseModel):
    """Request to check day-off compliance."""

    person_id: str | None = Field(
        default=None, description="Optional person ID (check all if None)"
    )
    start_date: str = Field(..., description="Start date in YYYY-MM-DD format")
    end_date: str = Field(..., description="End date in YYYY-MM-DD format")


class PersonDayOff(BaseModel):
    """Day-off compliance for a person."""

    person_id: str
    person_name: str | None = None
    days_analyzed: int
    days_off: int
    longest_stretch_days: int
    violations: int
    compliant: bool


class DayOffCheckResponse(BaseModel):
    """Response from day-off check."""

    start_date: str
    end_date: str
    total_people_checked: int
    compliant_count: int
    violation_count: int
    overall_compliant: bool
    people: list[PersonDayOff]


class CheckDayOffTool(BaseTool[DayOffCheckRequest, DayOffCheckResponse]):
    """
    Tool for checking ACGME 1-in-7 day-off rule compliance.

    Validates that residents get at least one 24-hour period off
    every 7 days.
    """

    @property
    def name(self) -> str:
        return "check_day_off"

    @property
    def description(self) -> str:
        return (
            "Check ACGME 1-in-7 day-off rule compliance. "
            "Validates that residents get at least one day off every 7 days."
        )

    def validate_input(self, **kwargs: Any) -> DayOffCheckRequest:
        """Validate input parameters."""
        # Validate dates
        start_date = kwargs.get("start_date", "")
        end_date = kwargs.get("end_date", "")
        validate_date_range(start_date, end_date, max_days=365)

        # Validate person_id if provided
        person_id = kwargs.get("person_id")
        if person_id is not None:
            person_id = validate_person_id(person_id)

        return DayOffCheckRequest(
            person_id=person_id,
            start_date=start_date,
            end_date=end_date,
        )

    async def execute(self, request: DayOffCheckRequest) -> DayOffCheckResponse:
        """Execute the tool."""
        client = self._require_api_client()

        try:
            # Check day-off via API
            params: dict[str, Any] = {
                "start_date": request.start_date,
                "end_date": request.end_date,
            }
            if request.person_id:
                params["person_id"] = request.person_id

            result = await client.client.get(
                f"{client.config.api_prefix}/compliance/day-off",
                headers=await client._ensure_authenticated(),
                params=params,
            )
            result.raise_for_status()
            data = result.json()

            # Parse people data
            people = []
            for item in data.get("people", []):
                person = PersonDayOff(
                    person_id=item["person_id"],
                    person_name=item.get("person_name"),
                    days_analyzed=item.get("days_analyzed", 0),
                    days_off=item.get("days_off", 0),
                    longest_stretch_days=item.get("longest_stretch_days", 0),
                    violations=item.get("violations", 0),
                    compliant=item.get("compliant", False),
                )
                people.append(person)

            # Count compliant vs violations
            compliant_count = sum(1 for p in people if p.compliant)
            violation_count = len(people) - compliant_count

            return DayOffCheckResponse(
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
            return DayOffCheckResponse(
                start_date=request.start_date,
                end_date=request.end_date,
                total_people_checked=0,
                compliant_count=0,
                violation_count=0,
                overall_compliant=False,
                people=[],
            )
