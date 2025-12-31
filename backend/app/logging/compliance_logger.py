"""
Compliance event logging for ACGME and regulatory compliance monitoring.

Tracks:
- ACGME rule violations (80-hour, 1-in-7, supervision ratios)
- Schedule changes and overrides
- Work hour calculations
- Emergency coverage assignments
- Compliance exceptions and justifications
- Audit trail for regulatory reporting
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from loguru import logger

from app.core.logging.context import bind_context_to_logger


class ComplianceEventType(str, Enum):
    """Compliance event types."""

    # ACGME compliance
    ACGME_VIOLATION = "acgme_violation"
    ACGME_OVERRIDE = "acgme_override"
    WORK_HOUR_EXCEEDED = "work_hour_exceeded"
    REST_PERIOD_VIOLATION = "rest_period_violation"
    SUPERVISION_VIOLATION = "supervision_violation"

    # Schedule changes
    SCHEDULE_CHANGE = "schedule_change"
    SCHEDULE_OVERRIDE = "schedule_override"
    EMERGENCY_ASSIGNMENT = "emergency_assignment"
    SWAP_APPROVED = "swap_approved"
    SWAP_REJECTED = "swap_rejected"

    # Data integrity
    DATA_CORRECTION = "data_correction"
    RETROACTIVE_CHANGE = "retroactive_change"

    # Reporting
    COMPLIANCE_REPORT = "compliance_report"
    AUDIT_EXPORT = "audit_export"


class ComplianceSeverity(str, Enum):
    """Compliance event severity levels."""

    INFO = "info"
    WARNING = "warning"
    VIOLATION = "violation"
    CRITICAL = "critical"


@dataclass
class ComplianceEvent:
    """
    Compliance event data.

    Captures comprehensive information about compliance-related events.
    """

    event_type: ComplianceEventType
    severity: ComplianceSeverity
    timestamp: datetime = field(default_factory=datetime.utcnow)
    user_id: str | None = None
    affected_person: str | None = None
    affected_person_role: str | None = None
    rule: str | None = None
    violation_details: str | None = None
    override_justification: str | None = None
    corrective_action: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for logging."""
        return {
            "event_type": self.event_type.value,
            "severity": self.severity.value,
            "timestamp": self.timestamp.isoformat(),
            "user_id": self.user_id,
            "affected_person": self.affected_person,
            "affected_person_role": self.affected_person_role,
            "rule": self.rule,
            "violation_details": self.violation_details,
            "override_justification": self.override_justification,
            "corrective_action": self.corrective_action,
            **self.metadata,
        }


class ComplianceLogger:
    """
    Compliance logger for tracking regulatory compliance events.

    Features:
    - ACGME rule violation tracking
    - Schedule change audit trail
    - Compliance exception logging
    - Regulatory reporting support
    """

    def __init__(self, enable_alerts: bool = True):
        """
        Initialize compliance logger.

        Args:
            enable_alerts: Enable real-time alerts for violations
        """
        self.enable_alerts = enable_alerts

    def log_event(self, event: ComplianceEvent) -> None:
        """
        Log a compliance event.

        Args:
            event: Compliance event to log
        """
        # Determine log level based on severity
        if event.severity == ComplianceSeverity.CRITICAL:
            log_level = "critical"
        elif event.severity == ComplianceSeverity.VIOLATION:
            log_level = "error"
        elif event.severity == ComplianceSeverity.WARNING:
            log_level = "warning"
        else:
            log_level = "info"

        # Log the event
        bound_logger = logger.bind(**bind_context_to_logger(), compliance=True)
        getattr(bound_logger, log_level)(
            f"Compliance event: {event.event_type.value}",
            **event.to_dict(),
        )

        # Send alert for violations
        if self.enable_alerts and event.severity in (
            ComplianceSeverity.VIOLATION,
            ComplianceSeverity.CRITICAL,
        ):
            self._send_alert(event)

    def log_acgme_violation(
        self,
        rule: str,
        affected_person: str,
        affected_person_role: str,
        violation_details: str,
        user_id: str | None = None,
        severity: ComplianceSeverity = ComplianceSeverity.VIOLATION,
        **metadata,
    ) -> None:
        """
        Log ACGME rule violation.

        Args:
            rule: ACGME rule violated (e.g., "80_hour", "1_in_7")
            affected_person: Person affected by violation
            affected_person_role: Role of affected person (RESIDENT, FACULTY)
            violation_details: Details of the violation
            user_id: User who triggered the violation
            severity: Violation severity
            **metadata: Additional metadata
        """
        event = ComplianceEvent(
            event_type=ComplianceEventType.ACGME_VIOLATION,
            severity=severity,
            user_id=user_id,
            affected_person=affected_person,
            affected_person_role=affected_person_role,
            rule=rule,
            violation_details=violation_details,
            metadata=metadata,
        )
        self.log_event(event)

    def log_acgme_override(
        self,
        rule: str,
        affected_person: str,
        affected_person_role: str,
        justification: str,
        user_id: str,
        approved_by: str | None = None,
        **metadata,
    ) -> None:
        """
        Log ACGME override with justification.

        Args:
            rule: ACGME rule being overridden
            affected_person: Person affected
            affected_person_role: Role of affected person
            justification: Justification for override
            user_id: User requesting override
            approved_by: Approver (if different from requester)
            **metadata: Additional metadata
        """
        event = ComplianceEvent(
            event_type=ComplianceEventType.ACGME_OVERRIDE,
            severity=ComplianceSeverity.WARNING,
            user_id=user_id,
            affected_person=affected_person,
            affected_person_role=affected_person_role,
            rule=rule,
            override_justification=justification,
            metadata={"approved_by": approved_by, **metadata},
        )
        self.log_event(event)

    def log_work_hour_exceeded(
        self,
        affected_person: str,
        hours: float,
        threshold: float,
        period: str,
        user_id: str | None = None,
        **metadata,
    ) -> None:
        """
        Log work hour threshold exceeded.

        Args:
            affected_person: Person affected
            hours: Actual hours worked
            threshold: Threshold exceeded
            period: Time period (week, 4-week average, etc.)
            user_id: User who created the assignment
            **metadata: Additional metadata
        """
        violation_details = (
            f"Worked {hours} hours in {period}, exceeding threshold of {threshold} hours"
        )

        event = ComplianceEvent(
            event_type=ComplianceEventType.WORK_HOUR_EXCEEDED,
            severity=ComplianceSeverity.VIOLATION,
            user_id=user_id,
            affected_person=affected_person,
            affected_person_role="RESIDENT",
            rule="80_hour_rule",
            violation_details=violation_details,
            metadata={
                "hours": hours,
                "threshold": threshold,
                "period": period,
                **metadata,
            },
        )
        self.log_event(event)

    def log_rest_period_violation(
        self,
        affected_person: str,
        violation_type: str,
        user_id: str | None = None,
        **metadata,
    ) -> None:
        """
        Log rest period violation.

        Args:
            affected_person: Person affected
            violation_type: Type of violation (no_1_in_7, insufficient_rest, etc.)
            user_id: User who created the assignment
            **metadata: Additional metadata
        """
        event = ComplianceEvent(
            event_type=ComplianceEventType.REST_PERIOD_VIOLATION,
            severity=ComplianceSeverity.VIOLATION,
            user_id=user_id,
            affected_person=affected_person,
            affected_person_role="RESIDENT",
            rule="1_in_7_rule",
            violation_details=f"Rest period violation: {violation_type}",
            metadata={"violation_type": violation_type, **metadata},
        )
        self.log_event(event)

    def log_supervision_violation(
        self,
        affected_person: str,
        pgy_level: int,
        required_ratio: str,
        actual_ratio: str,
        user_id: str | None = None,
        **metadata,
    ) -> None:
        """
        Log supervision ratio violation.

        Args:
            affected_person: Person affected
            pgy_level: PGY level
            required_ratio: Required supervision ratio
            actual_ratio: Actual supervision ratio
            user_id: User who created the assignment
            **metadata: Additional metadata
        """
        violation_details = (
            f"PGY-{pgy_level} supervision ratio {actual_ratio} "
            f"does not meet required {required_ratio}"
        )

        event = ComplianceEvent(
            event_type=ComplianceEventType.SUPERVISION_VIOLATION,
            severity=ComplianceSeverity.VIOLATION,
            user_id=user_id,
            affected_person=affected_person,
            affected_person_role="RESIDENT",
            rule="supervision_ratio",
            violation_details=violation_details,
            metadata={
                "pgy_level": pgy_level,
                "required_ratio": required_ratio,
                "actual_ratio": actual_ratio,
                **metadata,
            },
        )
        self.log_event(event)

    def log_schedule_change(
        self,
        affected_person: str,
        change_type: str,
        old_value: Any,
        new_value: Any,
        user_id: str,
        reason: str | None = None,
        **metadata,
    ) -> None:
        """
        Log schedule change for audit trail.

        Args:
            affected_person: Person affected by change
            change_type: Type of change (assignment, rotation, block, etc.)
            old_value: Previous value
            new_value: New value
            user_id: User making the change
            reason: Reason for change
            **metadata: Additional metadata
        """
        event = ComplianceEvent(
            event_type=ComplianceEventType.SCHEDULE_CHANGE,
            severity=ComplianceSeverity.INFO,
            user_id=user_id,
            affected_person=affected_person,
            violation_details=f"Changed {change_type}: {old_value} -> {new_value}",
            metadata={
                "change_type": change_type,
                "old_value": str(old_value),
                "new_value": str(new_value),
                "reason": reason,
                **metadata,
            },
        )
        self.log_event(event)

    def log_emergency_assignment(
        self,
        affected_person: str,
        assignment_type: str,
        user_id: str,
        justification: str,
        **metadata,
    ) -> None:
        """
        Log emergency coverage assignment.

        Args:
            affected_person: Person assigned
            assignment_type: Type of assignment (call, clinic, procedure)
            user_id: User creating assignment
            justification: Justification for emergency assignment
            **metadata: Additional metadata
        """
        event = ComplianceEvent(
            event_type=ComplianceEventType.EMERGENCY_ASSIGNMENT,
            severity=ComplianceSeverity.WARNING,
            user_id=user_id,
            affected_person=affected_person,
            violation_details=f"Emergency {assignment_type} assignment",
            override_justification=justification,
            metadata={"assignment_type": assignment_type, **metadata},
        )
        self.log_event(event)

    def log_swap_approved(
        self,
        requestor: str,
        partner: str,
        swap_type: str,
        user_id: str,
        **metadata,
    ) -> None:
        """
        Log approved schedule swap.

        Args:
            requestor: Person requesting swap
            partner: Swap partner
            swap_type: Type of swap (one_to_one, absorb)
            user_id: User approving swap
            **metadata: Additional metadata
        """
        event = ComplianceEvent(
            event_type=ComplianceEventType.SWAP_APPROVED,
            severity=ComplianceSeverity.INFO,
            user_id=user_id,
            affected_person=requestor,
            metadata={
                "partner": partner,
                "swap_type": swap_type,
                **metadata,
            },
        )
        self.log_event(event)

    def log_retroactive_change(
        self,
        affected_person: str,
        change_type: str,
        change_date: datetime,
        user_id: str,
        justification: str,
        **metadata,
    ) -> None:
        """
        Log retroactive schedule change (requires justification).

        Args:
            affected_person: Person affected
            change_type: Type of retroactive change
            change_date: Date being changed
            user_id: User making change
            justification: Justification for retroactive change
            **metadata: Additional metadata
        """
        event = ComplianceEvent(
            event_type=ComplianceEventType.RETROACTIVE_CHANGE,
            severity=ComplianceSeverity.WARNING,
            user_id=user_id,
            affected_person=affected_person,
            violation_details=f"Retroactive {change_type} for {change_date.date()}",
            override_justification=justification,
            metadata={
                "change_type": change_type,
                "change_date": change_date.isoformat(),
                **metadata,
            },
        )
        self.log_event(event)

    def log_compliance_report(
        self,
        report_type: str,
        period_start: datetime,
        period_end: datetime,
        user_id: str,
        **metadata,
    ) -> None:
        """
        Log compliance report generation.

        Args:
            report_type: Type of report
            period_start: Report period start
            period_end: Report period end
            user_id: User generating report
            **metadata: Additional metadata
        """
        event = ComplianceEvent(
            event_type=ComplianceEventType.COMPLIANCE_REPORT,
            severity=ComplianceSeverity.INFO,
            user_id=user_id,
            metadata={
                "report_type": report_type,
                "period_start": period_start.isoformat(),
                "period_end": period_end.isoformat(),
                **metadata,
            },
        )
        self.log_event(event)

    def _send_alert(self, event: ComplianceEvent) -> None:
        """
        Send real-time alert for compliance violations.

        Args:
            event: Compliance event to alert on
        """
        # In production, this would notify:
        # - Program director
        # - Chief resident
        # - Compliance officers

        logger.critical(
            f"COMPLIANCE ALERT: {event.event_type.value}",
            **event.to_dict(),
        )


# Global compliance logger instance
_global_compliance_logger: ComplianceLogger | None = None


def get_compliance_logger() -> ComplianceLogger:
    """Get or create global compliance logger instance."""
    global _global_compliance_logger
    if _global_compliance_logger is None:
        _global_compliance_logger = ComplianceLogger()
    return _global_compliance_logger


def set_compliance_logger(compliance_logger: ComplianceLogger) -> None:
    """Set global compliance logger instance."""
    global _global_compliance_logger
    _global_compliance_logger = compliance_logger


# Convenience functions


def log_acgme_violation(
    rule: str,
    affected_person: str,
    affected_person_role: str,
    violation_details: str,
    user_id: str | None = None,
    **metadata,
) -> None:
    """Log ACGME violation (convenience function)."""
    get_compliance_logger().log_acgme_violation(
        rule, affected_person, affected_person_role, violation_details, user_id, **metadata
    )


def log_acgme_override(
    rule: str,
    affected_person: str,
    affected_person_role: str,
    justification: str,
    user_id: str,
    **metadata,
) -> None:
    """Log ACGME override (convenience function)."""
    get_compliance_logger().log_acgme_override(
        rule, affected_person, affected_person_role, justification, user_id, **metadata
    )


def log_schedule_change(
    affected_person: str,
    change_type: str,
    old_value: Any,
    new_value: Any,
    user_id: str,
    reason: str | None = None,
    **metadata,
) -> None:
    """Log schedule change (convenience function)."""
    get_compliance_logger().log_schedule_change(
        affected_person, change_type, old_value, new_value, user_id, reason, **metadata
    )
