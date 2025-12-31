"""
Run N-1 analysis tool for contingency planning.
"""

from typing import Any

from pydantic import BaseModel, Field

from ..base import BaseTool
from ..validator import validate_date_range


class N1Vulnerability(BaseModel):
    """N-1 vulnerability."""

    person_id: str
    person_name: str | None = None
    role: str
    impact_score: float = Field(ge=0.0, le=1.0)
    affected_dates: int
    coverage_gaps: int


class RunN1AnalysisRequest(BaseModel):
    """Request to run N-1 analysis."""

    start_date: str = Field(..., description="Start date in YYYY-MM-DD format")
    end_date: str = Field(..., description="End date in YYYY-MM-DD format")
    scenario: str = Field(
        default="single_absence",
        description="Scenario (single_absence, double_absence, deployment)",
    )


class RunN1AnalysisResponse(BaseModel):
    """Response from run N-1 analysis."""

    start_date: str
    end_date: str
    scenario: str
    total_vulnerabilities: int
    critical_count: int
    vulnerabilities: list[N1Vulnerability]
    resilient: bool
    recommendations: list[str] = Field(default_factory=list)


class RunN1AnalysisTool(BaseTool[RunN1AnalysisRequest, RunN1AnalysisResponse]):
    """
    Tool for running N-1 contingency analysis.

    Tests schedule resilience against single or multiple absences.
    """

    @property
    def name(self) -> str:
        return "run_n1_analysis"

    @property
    def description(self) -> str:
        return (
            "Run N-1 contingency analysis to test schedule resilience. "
            "Identifies critical single points of failure."
        )

    def validate_input(self, **kwargs: Any) -> RunN1AnalysisRequest:
        """Validate input parameters."""
        # Validate dates
        start_date = kwargs.get("start_date", "")
        end_date = kwargs.get("end_date", "")
        validate_date_range(start_date, end_date, max_days=365)

        # Validate scenario
        scenario = kwargs.get("scenario", "single_absence")
        valid_scenarios = ["single_absence", "double_absence", "deployment"]
        if scenario not in valid_scenarios:
            from ..base import ValidationError

            raise ValidationError(
                f"Invalid scenario: {scenario}",
                details={"value": scenario, "valid": valid_scenarios},
            )

        return RunN1AnalysisRequest(
            start_date=start_date,
            end_date=end_date,
            scenario=scenario,
        )

    async def execute(
        self, request: RunN1AnalysisRequest
    ) -> RunN1AnalysisResponse:
        """Execute the tool."""
        client = self._require_api_client()

        try:
            # Run N-1 analysis via API
            result = await client.run_contingency_analysis(
                scenario=request.scenario,
                affected_ids=[],
                start_date=request.start_date,
                end_date=request.end_date,
            )

            # Parse vulnerabilities
            vulnerabilities = []
            for item in result.get("vulnerabilities", []):
                vuln = N1Vulnerability(
                    person_id=item["person_id"],
                    person_name=item.get("person_name"),
                    role=item.get("role", ""),
                    impact_score=item.get("impact_score", 0.0),
                    affected_dates=item.get("affected_dates", 0),
                    coverage_gaps=item.get("coverage_gaps", 0),
                )
                vulnerabilities.append(vuln)

            # Count critical
            critical_count = sum(
                1 for v in vulnerabilities if v.impact_score >= 0.8
            )

            return RunN1AnalysisResponse(
                start_date=request.start_date,
                end_date=request.end_date,
                scenario=request.scenario,
                total_vulnerabilities=len(vulnerabilities),
                critical_count=critical_count,
                vulnerabilities=vulnerabilities,
                resilient=critical_count == 0,
                recommendations=result.get("recommendations", []),
            )

        except Exception as e:
            # Return empty result
            return RunN1AnalysisResponse(
                start_date=request.start_date,
                end_date=request.end_date,
                scenario=request.scenario,
                total_vulnerabilities=0,
                critical_count=0,
                vulnerabilities=[],
                resilient=False,
                recommendations=[f"Error: {e}"],
            )
