"""
Generate compliance report tool for creating compliance summaries.
"""

from typing import Any

from pydantic import BaseModel, Field

from ..base import BaseTool
from ..validator import validate_date_range


class GenerateComplianceReportRequest(BaseModel):
    """Request to generate compliance report."""

    start_date: str = Field(..., description="Start date in YYYY-MM-DD format")
    end_date: str = Field(..., description="End date in YYYY-MM-DD format")
    include_violations: bool = Field(
        default=True,
        description="Include violation details",
    )
    include_recommendations: bool = Field(
        default=True,
        description="Include recommendations",
    )
    format: str = Field(
        default="json",
        description="Report format (json, pdf, html)",
    )


class ComplianceSummary(BaseModel):
    """Compliance summary."""

    rule_type: str
    total_checks: int
    passed: int
    failed: int
    compliance_rate: float


class GenerateComplianceReportResponse(BaseModel):
    """Response from generate compliance report."""

    success: bool
    message: str
    start_date: str
    end_date: str
    overall_compliance_rate: float
    summaries: list[ComplianceSummary]
    total_violations: int
    recommendations: list[str] = Field(default_factory=list)
    report_data: dict[str, Any] | None = None
    download_url: str | None = None


class GenerateComplianceReportTool(
    BaseTool[GenerateComplianceReportRequest, GenerateComplianceReportResponse]
):
    """
    Tool for generating compliance reports.

    Creates comprehensive compliance reports with summaries,
    violations, and recommendations.
    """

    @property
    def name(self) -> str:
        return "generate_compliance_report"

    @property
    def description(self) -> str:
        return (
            "Generate a comprehensive ACGME compliance report. "
            "Includes summaries, violations, and recommendations."
        )

    def validate_input(self, **kwargs: Any) -> GenerateComplianceReportRequest:
        """Validate input parameters."""
        # Validate dates
        start_date = kwargs.get("start_date", "")
        end_date = kwargs.get("end_date", "")
        validate_date_range(start_date, end_date, max_days=365)

        # Validate format
        format_value = kwargs.get("format", "json").lower()
        valid_formats = ["json", "pdf", "html"]
        if format_value not in valid_formats:
            from ..base import ValidationError

            raise ValidationError(
                f"Invalid format: {format_value}",
                details={"value": format_value, "valid": valid_formats},
            )

        return GenerateComplianceReportRequest(
            start_date=start_date,
            end_date=end_date,
            include_violations=kwargs.get("include_violations", True),
            include_recommendations=kwargs.get("include_recommendations", True),
            format=format_value,
        )

    async def execute(
        self, request: GenerateComplianceReportRequest
    ) -> GenerateComplianceReportResponse:
        """Execute the tool."""
        client = self._require_api_client()

        try:
            # Generate report via API
            result = await client.client.post(
                f"{client.config.api_prefix}/compliance/report",
                headers=await client._ensure_authenticated(),
                json={
                    "start_date": request.start_date,
                    "end_date": request.end_date,
                    "include_violations": request.include_violations,
                    "include_recommendations": request.include_recommendations,
                    "format": request.format,
                },
            )
            result.raise_for_status()
            data = result.json()

            # Parse summaries
            summaries = []
            for item in data.get("summaries", []):
                summary = ComplianceSummary(
                    rule_type=item["rule_type"],
                    total_checks=item["total_checks"],
                    passed=item["passed"],
                    failed=item["failed"],
                    compliance_rate=item["compliance_rate"],
                )
                summaries.append(summary)

            return GenerateComplianceReportResponse(
                success=True,
                message="Compliance report generated successfully",
                start_date=request.start_date,
                end_date=request.end_date,
                overall_compliance_rate=data.get("overall_compliance_rate", 0.0),
                summaries=summaries,
                total_violations=data.get("total_violations", 0),
                recommendations=data.get("recommendations", []),
                report_data=data.get("report_data"),
                download_url=data.get("download_url"),
            )

        except Exception as e:
            return GenerateComplianceReportResponse(
                success=False,
                message=f"Failed to generate report: {e}",
                start_date=request.start_date,
                end_date=request.end_date,
                overall_compliance_rate=0.0,
                summaries=[],
                total_violations=0,
            )
