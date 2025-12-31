"""
Get violations tool for retrieving compliance violations.
"""

from typing import Any

from pydantic import BaseModel, Field

from ..base import BaseTool
from ..validator import validate_date_range


class Violation(BaseModel):
    """A compliance violation."""

    id: str
    rule_type: str  # work_hours, day_off, supervision
    severity: str  # critical, warning
    person_id: str | None = None
    person_name: str | None = None
    date: str
    message: str
    details: dict[str, Any] = Field(default_factory=dict)


class GetViolationsRequest(BaseModel):
    """Request to get violations."""

    start_date: str = Field(..., description="Start date in YYYY-MM-DD format")
    end_date: str = Field(..., description="End date in YYYY-MM-DD format")
    rule_types: list[str] | None = Field(
        default=None,
        description="Filter by rule types (work_hours, day_off, supervision)",
    )
    severity: str | None = Field(
        default=None,
        description="Filter by severity (critical, warning)",
    )


class GetViolationsResponse(BaseModel):
    """Response from get violations."""

    start_date: str
    end_date: str
    total_violations: int
    critical_count: int
    warning_count: int
    violations: list[Violation]


class GetViolationsTool(BaseTool[GetViolationsRequest, GetViolationsResponse]):
    """
    Tool for retrieving compliance violations.

    Fetches all violations for a date range, optionally filtered
    by rule type and severity.
    """

    @property
    def name(self) -> str:
        return "get_violations"

    @property
    def description(self) -> str:
        return (
            "Get ACGME compliance violations for a date range. "
            "Can filter by rule type and severity."
        )

    def validate_input(self, **kwargs: Any) -> GetViolationsRequest:
        """Validate input parameters."""
        # Validate dates
        start_date = kwargs.get("start_date", "")
        end_date = kwargs.get("end_date", "")
        validate_date_range(start_date, end_date, max_days=365)

        # Validate rule types
        rule_types = kwargs.get("rule_types")
        if rule_types is not None:
            valid_types = ["work_hours", "day_off", "supervision"]
            if not isinstance(rule_types, list):
                rule_types = [rule_types]
            for rt in rule_types:
                if rt not in valid_types:
                    from ..base import ValidationError

                    raise ValidationError(
                        f"Invalid rule type: {rt}",
                        details={"value": rt, "valid": valid_types},
                    )

        # Validate severity
        severity = kwargs.get("severity")
        if severity is not None:
            valid_severities = ["critical", "warning"]
            if severity not in valid_severities:
                from ..base import ValidationError

                raise ValidationError(
                    f"Invalid severity: {severity}",
                    details={"value": severity, "valid": valid_severities},
                )

        return GetViolationsRequest(
            start_date=start_date,
            end_date=end_date,
            rule_types=rule_types,
            severity=severity,
        )

    async def execute(
        self, request: GetViolationsRequest
    ) -> GetViolationsResponse:
        """Execute the tool."""
        client = self._require_api_client()

        try:
            # Get violations via API client
            data = await client.get_violations(
                start_date=request.start_date,
                end_date=request.end_date,
                rule_types=request.rule_types,
                severity=request.severity,
            )

            # Parse violations
            violations = []
            for item in data.get("violations", []):
                violation = Violation(
                    id=item["id"],
                    rule_type=item["rule_type"],
                    severity=item["severity"],
                    person_id=item.get("person_id"),
                    person_name=item.get("person_name"),
                    date=item["date"],
                    message=item["message"],
                    details=item.get("details", {}),
                )
                violations.append(violation)

            # Count by severity
            critical_count = sum(1 for v in violations if v.severity == "critical")
            warning_count = len(violations) - critical_count

            return GetViolationsResponse(
                start_date=request.start_date,
                end_date=request.end_date,
                total_violations=len(violations),
                critical_count=critical_count,
                warning_count=warning_count,
                violations=violations,
            )

        except Exception as e:
            # Return empty result on error
            return GetViolationsResponse(
                start_date=request.start_date,
                end_date=request.end_date,
                total_violations=0,
                critical_count=0,
                warning_count=0,
                violations=[],
            )
