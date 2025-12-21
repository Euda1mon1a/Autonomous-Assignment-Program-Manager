"""
MCP Tools Package for Residency Scheduler.

This package contains MCP tool implementations that connect to
backend services for schedule operations.

Tools:
    - validate_schedule: Validate schedule against ACGME constraints
"""

from .validate_schedule import (
    ScheduleValidationRequest,
    ScheduleValidationResponse,
    validate_schedule,
)

__all__ = [
    "ScheduleValidationRequest",
    "ScheduleValidationResponse",
    "validate_schedule",
]
