"""
Validate schedule tool for ACGME compliance checking.
"""

from typing import Any

from pydantic import BaseModel, Field

from ..base import BaseTool
from ..validator import validate_date_range


class ValidationIssue(BaseModel):
    """A validation issue."""

    severity: str  # critical, warning, info
    rule_type: str
    message: str
    constraint_name: str
    affected_entity_ref: str | None = None
    date_context: str | None = None


class ValidateScheduleRequest(BaseModel):
    """Request to validate a schedule."""

    start_date: str = Field(..., description="Start date in YYYY-MM-DD format")
    end_date: str = Field(..., description="End date in YYYY-MM-DD format")
    checks: list[str] | None = Field(
        default=None,
        description="Specific checks to run (default: all)",
    )


class ValidateScheduleResponse(BaseModel):
    """Response from validate schedule."""

    is_valid: bool
    compliance_rate: float = Field(ge=0.0, le=1.0)
    total_issues: int
    critical_count: int
    warning_count: int
    info_count: int
    issues: list[ValidationIssue]
    start_date: str
    end_date: str


class ValidateScheduleTool(
    BaseTool[ValidateScheduleRequest, ValidateScheduleResponse]
):
    """
    Tool for validating schedule compliance.

    Checks schedules against ACGME regulations and institutional policies.
    """

    @property
    def name(self) -> str:
        return "validate_schedule"

    @property
    def description(self) -> str:
        return (
            "Validate a schedule for ACGME compliance. "
            "Checks work hours, day-off rules, supervision ratios, and coverage gaps."
        )

    def validate_input(self, **kwargs: Any) -> ValidateScheduleRequest:
        """Validate input parameters."""
        # Validate dates
        start_date = kwargs.get("start_date", "")
        end_date = kwargs.get("end_date", "")
        validate_date_range(start_date, end_date, max_days=365)

        return ValidateScheduleRequest(
            start_date=start_date,
            end_date=end_date,
            checks=kwargs.get("checks"),
        )

    async def execute(
        self, request: ValidateScheduleRequest
    ) -> ValidateScheduleResponse:
        """Execute the tool."""
        client = self._require_api_client()

        try:
            # Validate schedule via API
            result = await client.validate_schedule(
                start_date=request.start_date,
                end_date=request.end_date,
                checks=request.checks,
            )

            # Parse issues
            issues = []
            for item in result.get("issues", []):
                issue = ValidationIssue(
                    severity=item.get("severity", "info"),
                    rule_type=item.get("rule_type", "unknown"),
                    message=item.get("message", ""),
                    constraint_name=item.get("constraint_name", ""),
                    affected_entity_ref=item.get("affected_entity_ref"),
                    date_context=item.get("date_context"),
                )
                issues.append(issue)

            # Count by severity
            critical_count = sum(1 for i in issues if i.severity == "critical")
            warning_count = sum(1 for i in issues if i.severity == "warning")
            info_count = sum(1 for i in issues if i.severity == "info")

            return ValidateScheduleResponse(
                is_valid=result.get("is_valid", False),
                compliance_rate=result.get("compliance_rate", 0.0),
                total_issues=len(issues),
                critical_count=critical_count,
                warning_count=warning_count,
                info_count=info_count,
                issues=issues,
                start_date=request.start_date,
                end_date=request.end_date,
            )

        except Exception as e:
            # Return failure response
            return ValidateScheduleResponse(
                is_valid=False,
                compliance_rate=0.0,
                total_issues=1,
                critical_count=1,
                warning_count=0,
                info_count=0,
                issues=[
                    ValidationIssue(
                        severity="critical",
                        rule_type="system",
                        message=f"Validation failed: {e}",
                        constraint_name="api_error",
                    )
                ],
                start_date=request.start_date,
                end_date=request.end_date,
            )
