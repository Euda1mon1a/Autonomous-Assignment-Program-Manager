"""Alert management system with routing and escalation."""

import json
import logging
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional
from uuid import uuid4


# ============================================================================
# ALERT ENUMS AND TYPES (Task 24-27)
# ============================================================================


class AlertSeverity(str, Enum):
    """Alert severity levels."""

    CRITICAL = "critical"  # Immediate action required
    WARNING = "warning"  # Action required soon
    INFO = "info"  # Informational


class AlertStatus(str, Enum):
    """Alert status."""

    OPEN = "open"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"


class AlertCategory(str, Enum):
    """Alert categories."""

    SYSTEM = "system"
    DATABASE = "database"
    SCHEDULER = "scheduler"
    COMPLIANCE = "compliance"
    RESILIENCE = "resilience"
    SECURITY = "security"
    PERFORMANCE = "performance"
    SWAP = "swap"


# ============================================================================
# ALERT DEFINITION FRAMEWORK (Task 24)
# ============================================================================


class AlertDefinition:
    """Define an alert rule."""

    def __init__(
        self,
        name: str,
        description: str,
        category: AlertCategory,
        severity: AlertSeverity,
        condition: Callable[[dict[str, Any]], bool],
        threshold: float | None = None,
        window_minutes: int = 5,
    ):
        """
        Initialize alert definition.

        Args:
            name: Alert name
            description: Alert description
            category: Alert category
            severity: Alert severity
            condition: Function to evaluate condition
            threshold: Threshold value for condition
            window_minutes: Time window for evaluation
        """
        self.id = str(uuid4())
        self.name = name
        self.description = description
        self.category = category
        self.severity = severity
        self.condition = condition
        self.threshold = threshold
        self.window_minutes = window_minutes
        self.enabled = True
        self.created_at = datetime.utcnow()

    def evaluate(self, metrics: dict[str, Any]) -> bool:
        """
        Evaluate alert condition.

        Args:
            metrics: Metrics to evaluate

        Returns:
            True if condition is met
        """
        if not self.enabled:
            return False

        try:
            return self.condition(metrics)
        except Exception as e:
            logging.error(f"Error evaluating alert {self.name}: {e}")
            return False

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "category": self.category.value,
            "severity": self.severity.value,
            "threshold": self.threshold,
            "window_minutes": self.window_minutes,
            "enabled": self.enabled,
            "created_at": self.created_at.isoformat(),
        }


class Alert:
    """Alert instance."""

    def __init__(
        self,
        definition: AlertDefinition,
        triggered_at: datetime | None = None,
        details: dict[str, Any] | None = None,
    ):
        """
        Initialize alert.

        Args:
            definition: Alert definition
            triggered_at: When alert was triggered
            details: Additional details
        """
        self.id = str(uuid4())
        self.definition = definition
        self.triggered_at = triggered_at or datetime.utcnow()
        self.status = AlertStatus.OPEN
        self.details = details or {}
        self.acknowledged_at: datetime | None = None
        self.acknowledged_by: str | None = None
        self.resolved_at: datetime | None = None
        self.resolved_by: str | None = None
        self.escalation_level = 0
        self.notification_count = 0

    def acknowledge(self, user_id: str) -> None:
        """
        Acknowledge alert.

        Args:
            user_id: ID of user acknowledging alert
        """
        self.status = AlertStatus.ACKNOWLEDGED
        self.acknowledged_at = datetime.utcnow()
        self.acknowledged_by = user_id

    def resolve(self, user_id: str) -> None:
        """
        Resolve alert.

        Args:
            user_id: ID of user resolving alert
        """
        self.status = AlertStatus.RESOLVED
        self.resolved_at = datetime.utcnow()
        self.resolved_by = user_id

    def escalate(self) -> None:
        """Escalate alert."""
        self.escalation_level += 1

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "definition": self.definition.to_dict(),
            "triggered_at": self.triggered_at.isoformat(),
            "status": self.status.value,
            "details": self.details,
            "acknowledged_at": self.acknowledged_at.isoformat()
            if self.acknowledged_at
            else None,
            "acknowledged_by": self.acknowledged_by,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "resolved_by": self.resolved_by,
            "escalation_level": self.escalation_level,
            "notification_count": self.notification_count,
        }


# ============================================================================
# ALERT DEFINITIONS (Task 25-27)
# ============================================================================

CRITICAL_ALERTS = {
    "database_unavailable": AlertDefinition(
        name="Database Unavailable",
        description="Database connection failed",
        category=AlertCategory.DATABASE,
        severity=AlertSeverity.CRITICAL,
        condition=lambda m: m.get("db_available", True) is False,
    ),
    "scheduler_failure": AlertDefinition(
        name="Schedule Generation Failed",
        description="Schedule generation encountered critical error",
        category=AlertCategory.SCHEDULER,
        severity=AlertSeverity.CRITICAL,
        condition=lambda m: m.get("scheduler_failure", False) is True,
    ),
    "compliance_violation_critical": AlertDefinition(
        name="Critical Compliance Violation",
        description="ACGME compliance violation detected",
        category=AlertCategory.COMPLIANCE,
        severity=AlertSeverity.CRITICAL,
        condition=lambda m: m.get("critical_violations", 0) > 0,
    ),
    "system_overload": AlertDefinition(
        name="System Overload",
        description="System utilization exceeds safe threshold",
        category=AlertCategory.SYSTEM,
        severity=AlertSeverity.CRITICAL,
        condition=lambda m: m.get("utilization_rate", 0) > 95,
        threshold=95.0,
    ),
    "cascade_failure_risk": AlertDefinition(
        name="Cascade Failure Risk",
        description="Risk of cascade failure detected",
        category=AlertCategory.RESILIENCE,
        severity=AlertSeverity.CRITICAL,
        condition=lambda m: m.get("cascade_risk", 0) > 80,
        threshold=80.0,
    ),
    "security_breach_attempt": AlertDefinition(
        name="Security Breach Attempt",
        description="Multiple failed authentication attempts detected",
        category=AlertCategory.SECURITY,
        severity=AlertSeverity.CRITICAL,
        condition=lambda m: m.get("failed_auth_attempts", 0) > 10,
        threshold=10.0,
    ),
}

WARNING_ALERTS = {
    "high_error_rate": AlertDefinition(
        name="High Error Rate",
        description="Error rate exceeds threshold",
        category=AlertCategory.SYSTEM,
        severity=AlertSeverity.WARNING,
        condition=lambda m: m.get("error_rate", 0) > 5,
        threshold=5.0,
    ),
    "slow_database_queries": AlertDefinition(
        name="Slow Database Queries",
        description="Database query latency is elevated",
        category=AlertCategory.DATABASE,
        severity=AlertSeverity.WARNING,
        condition=lambda m: m.get("avg_query_latency_ms", 0) > 500,
        threshold=500.0,
    ),
    "high_memory_usage": AlertDefinition(
        name="High Memory Usage",
        description="Memory usage exceeds threshold",
        category=AlertCategory.SYSTEM,
        severity=AlertSeverity.WARNING,
        condition=lambda m: m.get("memory_usage_percent", 0) > 80,
        threshold=80.0,
    ),
    "compliance_warning": AlertDefinition(
        name="Compliance Warning",
        description="ACGME compliance approaching violation",
        category=AlertCategory.COMPLIANCE,
        severity=AlertSeverity.WARNING,
        condition=lambda m: m.get("compliance_rate", 100) < 95,
        threshold=95.0,
    ),
    "swap_queue_backlog": AlertDefinition(
        name="Swap Queue Backlog",
        description="Swap requests backing up in queue",
        category=AlertCategory.SWAP,
        severity=AlertSeverity.WARNING,
        condition=lambda m: m.get("swap_queue_depth", 0) > 50,
        threshold=50.0,
    ),
    "cache_miss_rate_high": AlertDefinition(
        name="High Cache Miss Rate",
        description="Cache miss rate exceeds threshold",
        category=AlertCategory.SYSTEM,
        severity=AlertSeverity.WARNING,
        condition=lambda m: m.get("cache_miss_rate", 0) > 30,
        threshold=30.0,
    ),
    "low_resilience_score": AlertDefinition(
        name="Low Resilience Score",
        description="System resilience score below safe level",
        category=AlertCategory.RESILIENCE,
        severity=AlertSeverity.WARNING,
        condition=lambda m: m.get("resilience_score", 100) < 70,
        threshold=70.0,
    ),
}

INFO_ALERTS = {
    "schedule_generated": AlertDefinition(
        name="Schedule Generated",
        description="Schedule generation completed successfully",
        category=AlertCategory.SCHEDULER,
        severity=AlertSeverity.INFO,
        condition=lambda m: m.get("schedule_generated", False) is True,
    ),
    "daily_health_check": AlertDefinition(
        name="Daily Health Check",
        description="Daily system health check completed",
        category=AlertCategory.SYSTEM,
        severity=AlertSeverity.INFO,
        condition=lambda m: m.get("health_check_completed", False) is True,
    ),
    "backup_completed": AlertDefinition(
        name="Backup Completed",
        description="Database backup completed successfully",
        category=AlertCategory.DATABASE,
        severity=AlertSeverity.INFO,
        condition=lambda m: m.get("backup_completed", False) is True,
    ),
}


# ============================================================================
# ALERT ROUTING AND ESCALATION (Task 28-29)
# ============================================================================


class AlertRouter:
    """Route alerts to appropriate channels."""

    def __init__(self):
        """Initialize router."""
        self.routes: dict[AlertSeverity, list[str]] = {
            AlertSeverity.CRITICAL: ["email", "sms", "slack", "pagerduty"],
            AlertSeverity.WARNING: ["email", "slack"],
            AlertSeverity.INFO: ["slack"],
        }
        self.handlers: dict[str, Callable] = {}

    def register_handler(self, channel: str, handler: Callable[[Alert], None]) -> None:
        """
        Register notification handler.

        Args:
            channel: Channel name
            handler: Handler function
        """
        self.handlers[channel] = handler

    def route_alert(self, alert: Alert) -> None:
        """
        Route alert to configured channels.

        Args:
            alert: Alert to route
        """
        channels = self.routes.get(alert.definition.severity, [])

        for channel in channels:
            if channel in self.handlers:
                try:
                    self.handlers[channel](alert)
                except Exception as e:
                    logging.error(f"Error routing alert {alert.id} to {channel}: {e}")

    def set_routes(self, severity: AlertSeverity, channels: list[str]) -> None:
        """
        Set routing for severity level.

        Args:
            severity: Alert severity
            channels: List of channels to route to
        """
        self.routes[severity] = channels


class EscalationPolicy:
    """Define alert escalation policy."""

    def __init__(self):
        """Initialize escalation policy."""
        self.policies: dict[str, list[dict[str, Any]]] = {}

    def define_policy(
        self, alert_name: str, escalation_steps: list[dict[str, Any]]
    ) -> None:
        """
        Define escalation policy for alert.

        Args:
            alert_name: Name of alert
            escalation_steps: List of escalation steps
                Each step should have:
                - level (int)
                - after_minutes (int)
                - action (str or Callable)
        """
        self.policies[alert_name] = escalation_steps

    def should_escalate(self, alert: Alert) -> bool:
        """
        Check if alert should be escalated.

        Args:
            alert: Alert to check

        Returns:
            True if alert should be escalated
        """
        if alert.definition.name not in self.policies:
            return False

        steps = self.policies[alert.definition.name]

        for step in steps:
            if alert.escalation_level == step.get("level", 0):
                minutes_elapsed = (
                    datetime.utcnow() - alert.triggered_at
                ).total_seconds() / 60

                if minutes_elapsed >= step.get("after_minutes", 0):
                    return True

        return False

    def get_escalation_action(self, alert: Alert) -> dict[str, Any] | None:
        """
        Get escalation action for alert.

        Args:
            alert: Alert to check

        Returns:
            Escalation action or None
        """
        if alert.definition.name not in self.policies:
            return None

        steps = self.policies[alert.definition.name]

        for step in steps:
            if alert.escalation_level == step.get("level", 0):
                return step

        return None


# ============================================================================
# ALERT MANAGER (Task 23, 30-31)
# ============================================================================


class AlertManager:
    """Manage alert definitions, instances, and history."""

    def __init__(self):
        """Initialize alert manager."""
        self.definitions: dict[str, AlertDefinition] = {}
        self.active_alerts: dict[str, Alert] = {}
        self.alert_history: list[Alert] = []
        self.router = AlertRouter()
        self.escalation_policy = EscalationPolicy()
        self.logger = logging.getLogger("app.alerts")

        # Register built-in definitions
        self._register_builtin_definitions()

    def _register_builtin_definitions(self) -> None:
        """Register built-in alert definitions."""
        for name, definition in CRITICAL_ALERTS.items():
            self.register_definition(definition)

        for name, definition in WARNING_ALERTS.items():
            self.register_definition(definition)

        for name, definition in INFO_ALERTS.items():
            self.register_definition(definition)

    def register_definition(self, definition: AlertDefinition) -> None:
        """
        Register alert definition.

        Args:
            definition: Alert definition to register
        """
        self.definitions[definition.id] = definition
        self.logger.info(f"Registered alert definition: {definition.name}")

    def create_alert(
        self, definition: AlertDefinition, details: dict[str, Any] | None = None
    ) -> Alert:
        """
        Create and store alert.

        Args:
            definition: Alert definition
            details: Additional details

        Returns:
            Created alert
        """
        alert = Alert(definition, details=details)
        self.active_alerts[alert.id] = alert

        # Route alert
        self.router.route_alert(alert)

        # Store in history
        self._store_alert_history(alert)

        self.logger.info(
            f"Alert created: {definition.name} (severity={definition.severity.value})"
        )

        return alert

    def evaluate_all(self, metrics: dict[str, Any]) -> list[Alert]:
        """
        Evaluate all alert definitions against metrics.

        Args:
            metrics: Metrics to evaluate

        Returns:
            List of triggered alerts
        """
        triggered_alerts = []

        for definition in self.definitions.values():
            if definition.evaluate(metrics):
                # Check if alert already exists
                existing = self._find_existing_alert(definition)

                if not existing:
                    alert = self.create_alert(definition, details=metrics)
                    triggered_alerts.append(alert)
                else:
                    # Alert already active, check for escalation
                    if self.escalation_policy.should_escalate(existing):
                        existing.escalate()
                        self.router.route_alert(existing)

        return triggered_alerts

    def _find_existing_alert(self, definition: AlertDefinition) -> Alert | None:
        """
        Find existing alert for definition.

        Args:
            definition: Alert definition

        Returns:
            Existing alert or None
        """
        for alert in self.active_alerts.values():
            if (
                alert.definition.name == definition.name
                and alert.status == AlertStatus.OPEN
            ):
                return alert

        return None

    def acknowledge_alert(self, alert_id: str, user_id: str) -> Alert | None:
        """
        Acknowledge alert.

        Args:
            alert_id: Alert ID
            user_id: User ID

        Returns:
            Acknowledged alert or None
        """
        alert = self.active_alerts.get(alert_id)

        if alert:
            alert.acknowledge(user_id)
            self.logger.info(f"Alert acknowledged: {alert_id} by {user_id}")

        return alert

    def resolve_alert(self, alert_id: str, user_id: str) -> Alert | None:
        """
        Resolve alert.

        Args:
            alert_id: Alert ID
            user_id: User ID

        Returns:
            Resolved alert or None
        """
        alert = self.active_alerts.get(alert_id)

        if alert:
            alert.resolve(user_id)
            # Move to history
            self._store_alert_history(alert)
            del self.active_alerts[alert_id]
            self.logger.info(f"Alert resolved: {alert_id} by {user_id}")

        return alert

    def get_active_alerts(
        self,
        severity: AlertSeverity | None = None,
        category: AlertCategory | None = None,
    ) -> list[Alert]:
        """
        Get active alerts.

        Args:
            severity: Filter by severity
            category: Filter by category

        Returns:
            List of active alerts
        """
        alerts = list(self.active_alerts.values())

        if severity:
            alerts = [a for a in alerts if a.definition.severity == severity]

        if category:
            alerts = [a for a in alerts if a.definition.category == category]

        return alerts

    def get_alert_history(self, limit: int = 100, hours: int = 24) -> list[Alert]:
        """
        Get alert history.

        Args:
            limit: Maximum number of alerts to return
            hours: Look back hours

        Returns:
            List of alerts from history
        """
        cutoff = datetime.utcnow() - timedelta(hours=hours)

        history = [a for a in self.alert_history if a.triggered_at >= cutoff]

        return history[-limit:]

    def _store_alert_history(self, alert: Alert) -> None:
        """
        Store alert in history.

        Args:
            alert: Alert to store
        """
        self.alert_history.append(alert)

        # Limit history size
        max_history = 10000
        if len(self.alert_history) > max_history:
            self.alert_history = self.alert_history[-max_history:]

    def get_stats(self) -> dict[str, Any]:
        """
        Get alert statistics.

        Returns:
            Alert statistics
        """
        active_by_severity = {}
        for severity in AlertSeverity:
            count = len(self.get_active_alerts(severity=severity))
            active_by_severity[severity.value] = count

        total_alerts = len(self.alert_history)

        return {
            "total_definitions": len(self.definitions),
            "active_alerts": len(self.active_alerts),
            "active_by_severity": active_by_severity,
            "total_alerts_history": total_alerts,
            "history_age_hours": 24,
        }


# ============================================================================
# GLOBAL ALERT MANAGER INSTANCE
# ============================================================================

alert_manager = AlertManager()
