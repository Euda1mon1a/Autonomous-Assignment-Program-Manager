"""
Constraint Service for Schedule Validation.

This module provides a service layer for schedule validation using the
constraint management system. It wraps the ConstraintManager and provides
a clean API for validating schedules by ID.

Features:
    - Validate schedules against ACGME compliance rules
    - Support for custom constraint configurations
    - Secure output that prevents PII leakage
    - Integration with the resilience framework

Security:
    - All person identifiers are anonymized in output
    - No sensitive data (SSN, DOB, etc.) is returned
    - Input validation prevents injection attacks
"""

import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.assignment import Assignment
from app.models.block import Block
from app.models.person import Person
from app.scheduling.constraints.base import (
    ConstraintResult,
    ConstraintType,
    ConstraintViolation,
    SchedulingContext,
)
from app.scheduling.constraints.manager import ConstraintManager

logger = logging.getLogger(__name__)


class ValidationSeverity(str, Enum):
    """Severity levels for validation issues."""

    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"


@dataclass
class ScheduleValidationIssue:
    """
    A sanitized validation issue safe for external consumption.

    This class strips PII and provides only necessary information
    for understanding the validation result.
    """

    severity: ValidationSeverity
    rule_type: str
    message: str
    constraint_name: str
    # Anonymized identifiers - never include actual names/PII
    affected_entity_ref: str | None = None
    date_context: str | None = None
    details: dict[str, Any] = field(default_factory=dict)
    suggested_action: str | None = None


@dataclass
class ScheduleValidationResult:
    """
    Result of schedule validation with sanitized output.

    All output is designed to be safe for external consumption
    without risk of PII leakage.
    """

    schedule_id: str
    is_valid: bool
    compliance_rate: float
    total_issues: int
    critical_count: int
    warning_count: int
    info_count: int
    issues: list[ScheduleValidationIssue]
    validated_at: datetime
    constraint_config: str  # Name of constraint configuration used
    metadata: dict[str, Any] = field(default_factory=dict)


class ScheduleIdValidationError(Exception):
    """Raised when schedule_id validation fails."""

    pass


class ScheduleNotFoundError(Exception):
    """Raised when schedule is not found."""

    pass


class ConstraintService:
    """
    Service for validating schedules against constraints.

    This service provides a secure interface for schedule validation,
    ensuring that:
    - Input schedule_id is properly sanitized
    - Output does not contain PII
    - ACGME compliance rules are properly validated

    Attributes:
        db: Database session
        constraint_manager: Configured constraint manager
    """

    # UUID pattern for schedule_id validation
    UUID_PATTERN = re.compile(
        r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
    )

    # Simple alphanumeric pattern for non-UUID identifiers
    ALPHANUM_PATTERN = re.compile(r"^[a-zA-Z0-9_-]{1,64}$")

    # Dangerous patterns to reject
    DANGEROUS_PATTERNS = [
        "..",  # Path traversal
        "/",  # Path separator
        "\\",  # Windows path separator
        "<",  # HTML/XML injection
        ">",
        "'",  # SQL injection
        '"',
        ";",  # Command injection
        "&",
        "|",
        "$",  # Shell expansion
        "`",  # Command substitution
        "\n",  # Newline injection
        "\r",
        "\x00",  # Null byte injection
    ]

    def __init__(
        self,
        db: Session,
        constraint_manager: ConstraintManager | None = None,
    ) -> None:
        """
        Initialize ConstraintService.

        Args:
            db: Database session for querying assignments
            constraint_manager: Optional custom constraint manager.
                              Uses default ACGME constraints if not provided.
        """
        self.db = db
        self.constraint_manager = (
            constraint_manager or ConstraintManager.create_default()
        )

    @classmethod
    def validate_schedule_id(cls, schedule_id: str) -> str:
        """
        Validate and sanitize schedule_id input.

        This method prevents injection attacks by validating the
        schedule_id format. Accepts either UUID format or simple
        alphanumeric identifiers.

        Args:
            schedule_id: The schedule identifier to validate

        Returns:
            str: The validated schedule_id

        Raises:
            ScheduleIdValidationError: If schedule_id is invalid

        Security:
            - Rejects empty or None values
            - Rejects overly long identifiers
            - Rejects path traversal patterns
            - Rejects SQL/command injection patterns
            - Only accepts UUID or alphanumeric formats
        """
        if not schedule_id:
            raise ScheduleIdValidationError("schedule_id cannot be empty")

        if not isinstance(schedule_id, str):
            raise ScheduleIdValidationError("schedule_id must be a string")

            # Strip whitespace
        schedule_id = schedule_id.strip()

        if len(schedule_id) == 0:
            raise ScheduleIdValidationError(
                "schedule_id cannot be empty after stripping"
            )

        if len(schedule_id) > 64:
            raise ScheduleIdValidationError(
                f"schedule_id too long: {len(schedule_id)} chars (max 64)"
            )

            # Check for dangerous patterns
        for pattern in cls.DANGEROUS_PATTERNS:
            if pattern in schedule_id:
                logger.warning(
                    f"Rejected schedule_id with dangerous pattern: {pattern!r}",
                    extra={"schedule_id_length": len(schedule_id)},
                )
                raise ScheduleIdValidationError(
                    "schedule_id contains invalid characters"
                )

                # Validate format: must be either UUID or alphanumeric
        if not cls.UUID_PATTERN.match(schedule_id) and not cls.ALPHANUM_PATTERN.match(
            schedule_id
        ):
            raise ScheduleIdValidationError(
                "schedule_id must be a valid UUID or alphanumeric identifier"
            )

        return schedule_id

    def _anonymize_person_ref(self, person_id: UUID | None) -> str | None:
        """
        Create an anonymized reference for a person.

        Instead of returning actual names or sensitive IDs,
        returns a hash-based reference.

        Args:
            person_id: The person's UUID

        Returns:
            Anonymized reference string or None
        """
        if person_id is None:
            return None

            # Use first 8 chars of UUID as anonymous reference
            # This allows correlation without exposing PII
        return f"entity-{str(person_id)[:8]}"

    def _severity_from_constraint(
        self, violation: ConstraintViolation
    ) -> ValidationSeverity:
        """
        Map constraint violation severity to ValidationSeverity.

        Args:
            violation: The constraint violation

        Returns:
            ValidationSeverity enum value
        """
        severity_map = {
            "CRITICAL": ValidationSeverity.CRITICAL,
            "HIGH": ValidationSeverity.CRITICAL,
            "MEDIUM": ValidationSeverity.WARNING,
            "LOW": ValidationSeverity.INFO,
        }
        return severity_map.get(violation.severity.upper(), ValidationSeverity.WARNING)

    def _sanitize_violation(
        self, violation: ConstraintViolation
    ) -> ScheduleValidationIssue:
        """
        Convert a ConstraintViolation to a sanitized ScheduleValidationIssue.

        Removes any PII and sensitive information from the violation.

        Args:
            violation: Raw constraint violation

        Returns:
            Sanitized validation issue safe for external consumption
        """
        # Strip any PII from the message
        sanitized_message = self._sanitize_message(violation.message)

        # Remove sensitive fields from details
        sanitized_details = self._sanitize_details(violation.details)

        return ScheduleValidationIssue(
            severity=self._severity_from_constraint(violation),
            rule_type=violation.constraint_type.value,
            message=sanitized_message,
            constraint_name=violation.constraint_name,
            affected_entity_ref=self._anonymize_person_ref(violation.person_id),
            date_context=self._format_date_context(violation.block_id),
            details=sanitized_details,
            suggested_action=self._get_suggested_action(violation.constraint_type),
        )

    def _sanitize_message(self, message: str) -> str:
        """
        Remove potential PII from error messages.

        Args:
            message: Original message

        Returns:
            Sanitized message with PII removed
        """
        # List of PII patterns to redact
        pii_patterns = [
            # Email addresses
            (r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", "[EMAIL REDACTED]"),
            # Phone numbers
            (r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b", "[PHONE REDACTED]"),
            # SSN patterns
            (r"\b\d{3}-\d{2}-\d{4}\b", "[SSN REDACTED]"),
            # Names (Dr. prefix pattern)
            (r"\bDr\.\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?", "[PERSON]"),
        ]

        result = message
        for pattern, replacement in pii_patterns:
            result = re.sub(pattern, replacement, result)

        return result

    def _sanitize_details(self, details: dict) -> dict[str, Any]:
        """
        Remove sensitive fields from details dictionary.

        Args:
            details: Original details dict

        Returns:
            Sanitized details with PII removed
        """
        # Fields that should never be included in output
        sensitive_fields = {
            "email",
            "phone",
            "ssn",
            "social_security",
            "dob",
            "date_of_birth",
            "address",
            "name",
            "full_name",
            "first_name",
            "last_name",
            "password",
            "token",
            "secret",
            "credential",
        }

        return {
            k: v
            for k, v in details.items()
            if k.lower() not in sensitive_fields
            and not any(s in k.lower() for s in sensitive_fields)
        }

    def _format_date_context(self, block_id: UUID | None) -> str | None:
        """
        Format date context without exposing block details.

        Args:
            block_id: Block UUID

        Returns:
            Date context string or None
        """
        if block_id is None:
            return None

            # Query block for date information only
        block = self.db.query(Block).filter(Block.id == block_id).first()
        if block:
            return f"{block.date.isoformat()}-{block.session.value}"
        return None

    def _get_suggested_action(self, constraint_type: ConstraintType) -> str:
        """
        Get a suggested action for a constraint violation type.

        Args:
            constraint_type: The type of constraint violated

        Returns:
            Suggested action string
        """
        suggestions = {
            ConstraintType.DUTY_HOURS: "Reduce assigned hours to comply with ACGME limits",
            ConstraintType.CONSECUTIVE_DAYS: "Ensure at least one day off per 7-day period",
            ConstraintType.SUPERVISION: "Assign additional supervising faculty",
            ConstraintType.AVAILABILITY: "Reassign block or update availability",
            ConstraintType.CAPACITY: "Reduce clinic assignments or expand capacity",
            ConstraintType.EQUITY: "Redistribute workload for fairness",
            ConstraintType.CONTINUITY: "Maintain consistent rotation assignments",
            ConstraintType.HUB_PROTECTION: "Distribute load away from hub faculty",
            ConstraintType.UTILIZATION_BUFFER: "Reduce overall system utilization",
            ConstraintType.N1_VULNERABILITY: "Add backup coverage for critical positions",
        }
        return suggestions.get(constraint_type, "Review and adjust schedule")

    def _build_scheduling_context(
        self,
        assignments: list[Assignment],
    ) -> SchedulingContext:
        """
        Build a SchedulingContext from assignments.

        Args:
            assignments: List of assignments to validate

        Returns:
            SchedulingContext for constraint validation
        """
        # Extract unique persons and blocks
        person_ids = {a.person_id for a in assignments if a.person_id}
        block_ids = {a.block_id for a in assignments if a.block_id}

        # Query related entities
        persons = self.db.query(Person).filter(Person.id.in_(person_ids)).all()
        blocks = self.db.query(Block).filter(Block.id.in_(block_ids)).all()

        # Separate residents and faculty
        residents = [p for p in persons if hasattr(p, "role") and p.role == "RESIDENT"]
        faculty = [p for p in persons if hasattr(p, "role") and p.role != "RESIDENT"]

        # Get date range
        dates = [b.date for b in blocks if b.date]
        start_date = min(dates) if dates else None
        end_date = max(dates) if dates else None

        return SchedulingContext(
            residents=residents,
            faculty=faculty,
            blocks=blocks,
            templates=[],
            existing_assignments=assignments,
            start_date=start_date,
            end_date=end_date,
        )

    async def validate_schedule(
        self,
        schedule_id: str,
        constraint_config: str = "default",
    ) -> ScheduleValidationResult:
        """
        Validate a schedule against constraints.

        This is the main entry point for schedule validation. It:
        1. Validates and sanitizes the schedule_id
        2. Retrieves assignments for the schedule
        3. Runs constraint validation
        4. Returns a sanitized result

        Args:
            schedule_id: The schedule identifier (must be valid UUID or alphanumeric)
            constraint_config: Constraint configuration to use
                             ("default", "minimal", "strict", "resilience")

        Returns:
            ScheduleValidationResult with sanitized validation issues

        Raises:
            ScheduleIdValidationError: If schedule_id is invalid
            ScheduleNotFoundError: If schedule doesn't exist or has no assignments

        Security:
            - Input schedule_id is validated and sanitized
            - Output contains no PII
            - All person references are anonymized
        """
        # Step 1: Validate and sanitize schedule_id
        validated_id = self.validate_schedule_id(schedule_id)

        logger.info(
            "Validating schedule",
            extra={"schedule_id": validated_id, "config": constraint_config},
        )

        # Step 2: Get constraint manager for specified configuration
        self.constraint_manager = self._get_constraint_manager(constraint_config)

        # Step 3: Query assignments for this schedule
        # In a real implementation, this would query based on schedule structure
        # For now, we query by schedule_id as a version identifier
        try:
            uuid_id = UUID(validated_id)
            assignments = (
                self.db.query(Assignment)
                .filter(Assignment.schedule_version_id == uuid_id)
                .all()
            )
        except ValueError:
            # Not a UUID, try as string identifier
            assignments = (
                self.db.query(Assignment)
                .filter(Assignment.schedule_label == validated_id)
                .all()
            )

            # FIX: Raise ScheduleNotFoundError when no assignments are found
            # This prevents returning a false "valid" result for non-existent schedules
        if not assignments:
            raise ScheduleNotFoundError(
                f"Schedule '{validated_id}' not found or has no assignments"
            )

            # Step 4: Build scheduling context
        context = self._build_scheduling_context(assignments)

        # Step 5: Run validation
        result = self.constraint_manager.validate_all(assignments, context)

        # Step 6: Sanitize and transform results
        issues = [self._sanitize_violation(v) for v in result.violations]

        critical_count = sum(
            1 for i in issues if i.severity == ValidationSeverity.CRITICAL
        )
        warning_count = sum(
            1 for i in issues if i.severity == ValidationSeverity.WARNING
        )
        info_count = sum(1 for i in issues if i.severity == ValidationSeverity.INFO)

        # Calculate compliance rate
        total_issues = len(issues)
        # Weight critical issues more heavily
        weighted_issues = critical_count * 3 + warning_count * 1 + info_count * 0.25
        max_expected_issues = len(assignments) * 0.1  # Expect up to 10% issues
        compliance_rate = max(
            0.0, min(1.0, 1.0 - (weighted_issues / max(max_expected_issues, 1)))
        )

        return ScheduleValidationResult(
            schedule_id=validated_id,
            is_valid=result.satisfied and critical_count == 0,
            compliance_rate=compliance_rate,
            total_issues=total_issues,
            critical_count=critical_count,
            warning_count=warning_count,
            info_count=info_count,
            issues=issues,
            validated_at=datetime.utcnow(),
            constraint_config=constraint_config,
            metadata={
                "assignment_count": len(assignments),
                "constraint_penalty": result.penalty,
            },
        )

    def _get_constraint_manager(self, config: str) -> ConstraintManager:
        """
        Get constraint manager for specified configuration.

        Args:
            config: Configuration name

        Returns:
            Configured ConstraintManager
        """
        config_map = {
            "default": ConstraintManager.create_default,
            "minimal": ConstraintManager.create_minimal,
            "strict": ConstraintManager.create_strict,
            "resilience": lambda: ConstraintManager.create_resilience_aware(tier=2),
        }

        factory = config_map.get(config, ConstraintManager.create_default)
        return factory()
