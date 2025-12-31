"""
Security event logging for monitoring security-related events.

Tracks:
- Authentication attempts (success/failure)
- Authorization failures
- Suspicious activity
- Data access patterns
- Security policy violations
- Rate limit violations
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from loguru import logger

from app.core.logging.context import bind_context_to_logger


class SecurityEventType(str, Enum):
    """Security event types."""

    AUTH_SUCCESS = "auth_success"
    AUTH_FAILURE = "auth_failure"
    AUTH_LOCKED = "auth_locked"
    AUTHZ_FAILURE = "authz_failure"
    TOKEN_ISSUED = "token_issued"
    TOKEN_REVOKED = "token_revoked"
    TOKEN_EXPIRED = "token_expired"
    PASSWORD_CHANGE = "password_change"
    PASSWORD_RESET = "password_reset"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    DATA_ACCESS = "data_access"
    DATA_EXPORT = "data_export"
    DATA_DELETION = "data_deletion"
    PRIVILEGE_ESCALATION = "privilege_escalation"
    POLICY_VIOLATION = "policy_violation"
    SESSION_CREATED = "session_created"
    SESSION_DESTROYED = "session_destroyed"
    MFA_ENABLED = "mfa_enabled"
    MFA_DISABLED = "mfa_disabled"


class SecuritySeverity(str, Enum):
    """Security event severity levels."""

    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class SecurityEvent:
    """
    Security event data.

    Captures comprehensive information about security-related events.
    """

    event_type: SecurityEventType
    severity: SecuritySeverity
    timestamp: datetime = field(default_factory=datetime.utcnow)
    user_id: str | None = None
    username: str | None = None
    ip_address: str | None = None
    user_agent: str | None = None
    resource: str | None = None
    action: str | None = None
    success: bool = True
    reason: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for logging."""
        return {
            "event_type": self.event_type.value,
            "severity": self.severity.value,
            "timestamp": self.timestamp.isoformat(),
            "user_id": self.user_id,
            "username": self.username,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "resource": self.resource,
            "action": self.action,
            "success": self.success,
            "reason": self.reason,
            **self.metadata,
        }


class SecurityLogger:
    """
    Security logger for tracking security-related events.

    Features:
    - Authentication/authorization event logging
    - Suspicious activity detection
    - Security policy violation tracking
    - Compliance audit trail
    """

    def __init__(self, enable_alerts: bool = True):
        """
        Initialize security logger.

        Args:
            enable_alerts: Enable real-time alerts for critical events
        """
        self.enable_alerts = enable_alerts

    def log_event(self, event: SecurityEvent) -> None:
        """
        Log a security event.

        Args:
            event: Security event to log
        """
        # Determine log level based on severity
        if event.severity == SecuritySeverity.CRITICAL:
            log_level = "critical"
        elif event.severity == SecuritySeverity.HIGH:
            log_level = "error"
        elif event.severity == SecuritySeverity.MEDIUM:
            log_level = "warning"
        else:
            log_level = "info"

        # Log the event
        bound_logger = logger.bind(**bind_context_to_logger(), security=True)
        getattr(bound_logger, log_level)(
            f"Security event: {event.event_type.value}",
            **event.to_dict(),
        )

        # Send alert for critical events
        if self.enable_alerts and event.severity in (
            SecuritySeverity.HIGH,
            SecuritySeverity.CRITICAL,
        ):
            self._send_alert(event)

    def log_auth_success(
        self,
        user_id: str,
        username: str,
        ip_address: str | None = None,
        **metadata,
    ) -> None:
        """
        Log successful authentication.

        Args:
            user_id: User identifier
            username: Username
            ip_address: IP address
            **metadata: Additional metadata
        """
        event = SecurityEvent(
            event_type=SecurityEventType.AUTH_SUCCESS,
            severity=SecuritySeverity.INFO,
            user_id=user_id,
            username=username,
            ip_address=ip_address,
            success=True,
            metadata=metadata,
        )
        self.log_event(event)

    def log_auth_failure(
        self,
        username: str,
        reason: str,
        ip_address: str | None = None,
        **metadata,
    ) -> None:
        """
        Log failed authentication attempt.

        Args:
            username: Attempted username
            reason: Failure reason
            ip_address: IP address
            **metadata: Additional metadata
        """
        event = SecurityEvent(
            event_type=SecurityEventType.AUTH_FAILURE,
            severity=SecuritySeverity.MEDIUM,
            username=username,
            ip_address=ip_address,
            success=False,
            reason=reason,
            metadata=metadata,
        )
        self.log_event(event)

    def log_authz_failure(
        self,
        user_id: str,
        resource: str,
        action: str,
        reason: str,
        **metadata,
    ) -> None:
        """
        Log authorization failure.

        Args:
            user_id: User identifier
            resource: Resource accessed
            action: Action attempted
            reason: Failure reason
            **metadata: Additional metadata
        """
        event = SecurityEvent(
            event_type=SecurityEventType.AUTHZ_FAILURE,
            severity=SecuritySeverity.HIGH,
            user_id=user_id,
            resource=resource,
            action=action,
            success=False,
            reason=reason,
            metadata=metadata,
        )
        self.log_event(event)

    def log_rate_limit_exceeded(
        self,
        user_id: str | None,
        ip_address: str,
        endpoint: str,
        limit: int,
        **metadata,
    ) -> None:
        """
        Log rate limit violation.

        Args:
            user_id: User identifier (if authenticated)
            ip_address: IP address
            endpoint: Endpoint accessed
            limit: Rate limit threshold
            **metadata: Additional metadata
        """
        event = SecurityEvent(
            event_type=SecurityEventType.RATE_LIMIT_EXCEEDED,
            severity=SecuritySeverity.MEDIUM,
            user_id=user_id,
            ip_address=ip_address,
            resource=endpoint,
            success=False,
            metadata={"limit": limit, **metadata},
        )
        self.log_event(event)

    def log_suspicious_activity(
        self,
        user_id: str | None,
        activity: str,
        severity: SecuritySeverity,
        ip_address: str | None = None,
        **metadata,
    ) -> None:
        """
        Log suspicious activity.

        Args:
            user_id: User identifier
            activity: Description of suspicious activity
            severity: Activity severity
            ip_address: IP address
            **metadata: Additional metadata
        """
        event = SecurityEvent(
            event_type=SecurityEventType.SUSPICIOUS_ACTIVITY,
            severity=severity,
            user_id=user_id,
            ip_address=ip_address,
            reason=activity,
            success=False,
            metadata=metadata,
        )
        self.log_event(event)

    def log_data_access(
        self,
        user_id: str,
        resource: str,
        action: str,
        sensitive: bool = False,
        **metadata,
    ) -> None:
        """
        Log data access event.

        Args:
            user_id: User identifier
            resource: Resource accessed
            action: Action performed
            sensitive: Whether resource contains sensitive data
            **metadata: Additional metadata
        """
        severity = SecuritySeverity.HIGH if sensitive else SecuritySeverity.INFO

        event = SecurityEvent(
            event_type=SecurityEventType.DATA_ACCESS,
            severity=severity,
            user_id=user_id,
            resource=resource,
            action=action,
            success=True,
            metadata={"sensitive": sensitive, **metadata},
        )
        self.log_event(event)

    def log_data_export(
        self,
        user_id: str,
        resource: str,
        record_count: int,
        export_format: str,
        **metadata,
    ) -> None:
        """
        Log data export event.

        Args:
            user_id: User identifier
            resource: Resource exported
            record_count: Number of records exported
            export_format: Export format (CSV, JSON, etc.)
            **metadata: Additional metadata
        """
        event = SecurityEvent(
            event_type=SecurityEventType.DATA_EXPORT,
            severity=SecuritySeverity.HIGH,
            user_id=user_id,
            resource=resource,
            action="export",
            success=True,
            metadata={
                "record_count": record_count,
                "format": export_format,
                **metadata,
            },
        )
        self.log_event(event)

    def log_data_deletion(
        self,
        user_id: str,
        resource: str,
        record_count: int,
        **metadata,
    ) -> None:
        """
        Log data deletion event.

        Args:
            user_id: User identifier
            resource: Resource deleted
            record_count: Number of records deleted
            **metadata: Additional metadata
        """
        event = SecurityEvent(
            event_type=SecurityEventType.DATA_DELETION,
            severity=SecuritySeverity.CRITICAL,
            user_id=user_id,
            resource=resource,
            action="delete",
            success=True,
            metadata={"record_count": record_count, **metadata},
        )
        self.log_event(event)

    def log_password_change(
        self,
        user_id: str,
        success: bool,
        reason: str | None = None,
        **metadata,
    ) -> None:
        """
        Log password change event.

        Args:
            user_id: User identifier
            success: Whether change succeeded
            reason: Failure reason (if failed)
            **metadata: Additional metadata
        """
        event = SecurityEvent(
            event_type=SecurityEventType.PASSWORD_CHANGE,
            severity=SecuritySeverity.MEDIUM,
            user_id=user_id,
            success=success,
            reason=reason,
            metadata=metadata,
        )
        self.log_event(event)

    def log_session_created(
        self,
        user_id: str,
        session_id: str,
        ip_address: str | None = None,
        **metadata,
    ) -> None:
        """
        Log session creation.

        Args:
            user_id: User identifier
            session_id: Session identifier
            ip_address: IP address
            **metadata: Additional metadata
        """
        event = SecurityEvent(
            event_type=SecurityEventType.SESSION_CREATED,
            severity=SecuritySeverity.INFO,
            user_id=user_id,
            ip_address=ip_address,
            metadata={"session_id": session_id, **metadata},
        )
        self.log_event(event)

    def _send_alert(self, event: SecurityEvent) -> None:
        """
        Send real-time alert for critical security events.

        Args:
            event: Security event to alert on
        """
        # In production, this would integrate with:
        # - Email notifications
        # - Slack/Teams webhooks
        # - PagerDuty/Opsgenie
        # - SIEM systems

        logger.critical(
            f"SECURITY ALERT: {event.event_type.value}",
            **event.to_dict(),
        )


# Global security logger instance
_global_security_logger: SecurityLogger | None = None


def get_security_logger() -> SecurityLogger:
    """Get or create global security logger instance."""
    global _global_security_logger
    if _global_security_logger is None:
        _global_security_logger = SecurityLogger()
    return _global_security_logger


def set_security_logger(security_logger: SecurityLogger) -> None:
    """Set global security logger instance."""
    global _global_security_logger
    _global_security_logger = security_logger


# Convenience functions


def log_auth_success(
    user_id: str,
    username: str,
    ip_address: str | None = None,
    **metadata,
) -> None:
    """Log successful authentication (convenience function)."""
    get_security_logger().log_auth_success(user_id, username, ip_address, **metadata)


def log_auth_failure(
    username: str,
    reason: str,
    ip_address: str | None = None,
    **metadata,
) -> None:
    """Log failed authentication (convenience function)."""
    get_security_logger().log_auth_failure(username, reason, ip_address, **metadata)


def log_authz_failure(
    user_id: str,
    resource: str,
    action: str,
    reason: str,
    **metadata,
) -> None:
    """Log authorization failure (convenience function)."""
    get_security_logger().log_authz_failure(user_id, resource, action, reason, **metadata)


def log_data_access(
    user_id: str,
    resource: str,
    action: str,
    sensitive: bool = False,
    **metadata,
) -> None:
    """Log data access (convenience function)."""
    get_security_logger().log_data_access(user_id, resource, action, sensitive, **metadata)


def log_suspicious_activity(
    user_id: str | None,
    activity: str,
    severity: SecuritySeverity = SecuritySeverity.MEDIUM,
    ip_address: str | None = None,
    **metadata,
) -> None:
    """Log suspicious activity (convenience function)."""
    get_security_logger().log_suspicious_activity(
        user_id, activity, severity, ip_address, **metadata
    )
