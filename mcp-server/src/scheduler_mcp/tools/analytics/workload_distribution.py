"""
Workload distribution tool for analyzing work balance.
"""

from typing import Any

from pydantic import BaseModel, Field

from ..base import BaseTool
from ..validator import validate_date_range


class PersonWorkload(BaseModel):
    """Workload for a person."""

    person_id: str
    person_name: str | None = None
    total_assignments: int
    call_shifts: int
    clinic_days: int
    procedure_days: int
    total_hours: float
    workload_score: float = Field(ge=0.0)


class WorkloadDistributionRequest(BaseModel):
    """Request to get workload distribution."""

    start_date: str = Field(..., description="Start date in YYYY-MM-DD format")
    end_date: str = Field(..., description="End date in YYYY-MM-DD format")


class WorkloadDistributionResponse(BaseModel):
    """Response from workload distribution."""

    start_date: str
    end_date: str
    total_people: int
    mean_workload: float
    std_dev_workload: float
    min_workload: float
    max_workload: float
    gini_coefficient: float = Field(ge=0.0, le=1.0)
    people: list[PersonWorkload]


class WorkloadDistributionTool(
    BaseTool[WorkloadDistributionRequest, WorkloadDistributionResponse]
):
    """
    Tool for analyzing workload distribution.

    Calculates workload balance and fairness metrics.
    """

    @property
    def name(self) -> str:
        return "workload_distribution"

    @property
    def description(self) -> str:
        return (
            "Analyze workload distribution across people. "
            "Shows balance metrics and Gini coefficient."
        )

    def validate_input(self, **kwargs: Any) -> WorkloadDistributionRequest:
        """Validate input parameters."""
        # Validate dates
        start_date = kwargs.get("start_date", "")
        end_date = kwargs.get("end_date", "")
        validate_date_range(start_date, end_date, max_days=365)

        return WorkloadDistributionRequest(
            start_date=start_date,
            end_date=end_date,
        )

    async def execute(
        self, request: WorkloadDistributionRequest
    ) -> WorkloadDistributionResponse:
        """Execute the tool."""
        client = self._require_api_client()

        try:
            # Get workload distribution via API
            result = await client.client.get(
                f"{client.config.api_prefix}/analytics/workload",
                headers=await client._ensure_authenticated(),
                params={
                    "start_date": request.start_date,
                    "end_date": request.end_date,
                },
            )
            result.raise_for_status()
            data = result.json()

            # Parse people
            people = []
            for item in data.get("people", []):
                person = PersonWorkload(
                    person_id=item["person_id"],
                    person_name=item.get("person_name"),
                    total_assignments=item.get("total_assignments", 0),
                    call_shifts=item.get("call_shifts", 0),
                    clinic_days=item.get("clinic_days", 0),
                    procedure_days=item.get("procedure_days", 0),
                    total_hours=item.get("total_hours", 0.0),
                    workload_score=item.get("workload_score", 0.0),
                )
                people.append(person)

            return WorkloadDistributionResponse(
                start_date=request.start_date,
                end_date=request.end_date,
                total_people=len(people),
                mean_workload=data.get("mean_workload", 0.0),
                std_dev_workload=data.get("std_dev_workload", 0.0),
                min_workload=data.get("min_workload", 0.0),
                max_workload=data.get("max_workload", 0.0),
                gini_coefficient=data.get("gini_coefficient", 0.0),
                people=people,
            )

        except Exception as e:
            # Return empty metrics
            return WorkloadDistributionResponse(
                start_date=request.start_date,
                end_date=request.end_date,
                total_people=0,
                mean_workload=0.0,
                std_dev_workload=0.0,
                min_workload=0.0,
                max_workload=0.0,
                gini_coefficient=0.0,
                people=[],
            )
