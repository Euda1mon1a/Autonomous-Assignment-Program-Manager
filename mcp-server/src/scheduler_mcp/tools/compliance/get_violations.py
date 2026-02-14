"""
Get violations tool for retrieving compliance violations.
"""

import inspect
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
            data = await self._fetch_violations_payload(client, request)

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

        except Exception:
            # Return empty result on error
            return GetViolationsResponse(
                start_date=request.start_date,
                end_date=request.end_date,
                total_violations=0,
                critical_count=0,
                warning_count=0,
                violations=[],
            )

    async def _fetch_violations_payload(
        self, client: Any, request: GetViolationsRequest
    ) -> dict[str, Any]:
        """Fetch and normalize violations payload for real and mocked API clients."""
        payload = {
            "start_date": request.start_date,
            "end_date": request.end_date,
            "rule_types": request.rule_types,
            "severity": request.severity,
        }

        get_fn = getattr(client, "get_violations", None)
        if callable(get_fn):
            result = get_fn(**payload)
            if inspect.isawaitable(result):
                result = await result
            result = await self._normalize_response_payload(result)
            if isinstance(result, dict):
                return result

        params: dict[str, Any] = {
            "start_date": request.start_date,
            "end_date": request.end_date,
        }
        if request.rule_types:
            params["rule_types"] = ",".join(request.rule_types)
        if request.severity:
            params["severity"] = request.severity

        headers = await client._ensure_authenticated()
        response = await client.client.get(
            f"{client.config.api_prefix}/compliance/violations",
            headers=headers,
            params=params,
        )
        response.raise_for_status()

        response_data = response.json()
        if inspect.isawaitable(response_data):
            response_data = await response_data
        if not isinstance(response_data, dict):
            raise ValueError("Unexpected violations response payload")
        return response_data

    async def _normalize_response_payload(self, result: Any) -> dict[str, Any] | None:
        """Normalize either a dict payload or a response-like object."""
        if isinstance(result, dict):
            return result
        json_fn = getattr(result, "json", None)
        if not callable(json_fn):
            return None
        payload = json_fn()
        if inspect.isawaitable(payload):
            payload = await payload
        if isinstance(payload, dict):
            return payload
        return None
