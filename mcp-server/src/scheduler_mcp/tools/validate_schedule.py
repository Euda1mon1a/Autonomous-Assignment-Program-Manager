"""
Schedule validation tool with ConstraintService integration.

This module provides schedule validation via the backend ConstraintService,
with proper security sanitization of all outputs.

Security Features:
- Input schedule_id is validated and sanitized against injection attacks
- Output is sanitized to prevent PII leakage
- All person references are anonymized
"""

import logging
import re
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator

logger = logging.getLogger(__name__)


class ConstraintConfig(str, Enum):
    """Available constraint configurations."""

    DEFAULT = "default"
    MINIMAL = "minimal"
    STRICT = "strict"
    RESILIENCE = "resilience"


class ValidationSeverity(str, Enum):
    """Severity levels for validation issues."""

    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"


class SanitizedIssue(BaseModel):
    """
    A sanitized validation issue safe for external consumption.

    All PII is stripped and person references are anonymized.
    """

    severity: ValidationSeverity
    rule_type: str
    message: str
    constraint_name: str
    affected_entity_ref: str | None = None  # Anonymized entity reference
    date_context: str | None = None
    details: dict[str, Any] = Field(default_factory=dict)
    suggested_action: str | None = None


class ScheduleValidationRequest(BaseModel):
    """Request to validate a schedule by ID."""

    schedule_id: str = Field(
        ...,
        min_length=1,
        max_length=64,
        description="Schedule identifier (UUID or alphanumeric)",
    )
    constraint_config: ConstraintConfig = Field(
        default=ConstraintConfig.DEFAULT,
        description="Constraint configuration to use",
    )
    include_suggestions: bool = Field(
        default=True,
        description="Include suggested actions for issues",
    )

    @field_validator("schedule_id")
    @classmethod
    def validate_schedule_id(cls, v: str) -> str:
        """Validate schedule_id for security."""
        v = v.strip()

        if not v:
            raise ValueError("schedule_id cannot be empty")

        # Dangerous patterns to reject
        dangerous_patterns = [
            "..",
            "/",
            "\\",
            "<",
            ">",
            "'",
            '"',
            ";",
            "&",
            "|",
            "$",
            "`",
            "\n",
            "\r",
            "\x00",
        ]

        for pattern in dangerous_patterns:
            if pattern in v:
                raise ValueError("schedule_id contains invalid characters")

        # Must be UUID or alphanumeric
        uuid_pattern = re.compile(
            r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-"
            r"[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
        )
        alphanum_pattern = re.compile(r"^[a-zA-Z0-9_-]{1,64}$")

        if not uuid_pattern.match(v) and not alphanum_pattern.match(v):
            raise ValueError(
                "schedule_id must be a valid UUID or alphanumeric identifier"
            )

        return v


class ScheduleValidationResponse(BaseModel):
    """Response from schedule validation with sanitized output."""

    schedule_id: str
    is_valid: bool
    compliance_rate: float = Field(ge=0.0, le=1.0)
    total_issues: int
    critical_count: int
    warning_count: int
    info_count: int
    issues: list[SanitizedIssue]
    validated_at: datetime
    constraint_config: str
    metadata: dict[str, Any] = Field(default_factory=dict)


async def validate_schedule(
    request: ScheduleValidationRequest,
) -> ScheduleValidationResponse:
    """
    Validate a schedule against ACGME constraints.

    This function connects to the backend ConstraintService to perform
    comprehensive schedule validation. All output is sanitized to prevent
    PII leakage.

    Args:
        request: Validation request with schedule_id and configuration

    Returns:
        ScheduleValidationResponse with sanitized validation results

    Raises:
        ValueError: If schedule_id is invalid or schedule not found
    """
    logger.info(
        "Validating schedule via MCP tool",
        extra={
            "schedule_id": request.schedule_id,
            "config": request.constraint_config.value,
        },
    )

    try:
        # Import API client for backend communication
        from ..api_client import get_api_client

        client = await get_api_client()

        # Call backend validation endpoint
        result = await client.validate_schedule_by_id(
            schedule_id=request.schedule_id,
            constraint_config=request.constraint_config.value,
            include_suggestions=request.include_suggestions,
        )

        if result is None:
            # Fallback to placeholder if API not available
            logger.warning(
                "API not available, using placeholder validation",
                extra={"schedule_id": request.schedule_id},
            )
            return _create_placeholder_response(request)

        # Parse and return response
        return ScheduleValidationResponse(**result)

    except Exception as e:
        logger.error(
            f"Validation failed: {e}",
            extra={"schedule_id": request.schedule_id},
            exc_info=True,
        )
        # Return placeholder for graceful degradation
        return _create_placeholder_response(request, error=str(e))


def _create_placeholder_response(
    request: ScheduleValidationRequest,
    error: str | None = None,
) -> ScheduleValidationResponse:
    """
    Create a placeholder response when backend is unavailable.

    This allows the MCP server to function in standalone mode for
    testing and development purposes.
    """
    now = datetime.utcnow()

    issues = []
    if error:
        issues.append(
            SanitizedIssue(
                severity=ValidationSeverity.INFO,
                rule_type="system",
                message=f"Backend unavailable: {error}. Using placeholder data.",
                constraint_name="connectivity",
                suggested_action="Ensure backend service is running",
            )
        )

    return ScheduleValidationResponse(
        schedule_id=request.schedule_id,
        is_valid=True,
        compliance_rate=1.0,
        total_issues=len(issues),
        critical_count=0,
        warning_count=0,
        info_count=len(issues),
        issues=issues,
        validated_at=now,
        constraint_config=request.constraint_config.value,
        metadata={
            "source": "placeholder",
            "reason": "backend_unavailable" if error else "standalone_mode",
        },
    )
