"""
Alert rule definitions for monitoring systems.

Provides pre-configured alert rules for:
- Prometheus Alertmanager
- Grafana Alerts
- Datadog Monitors
- Custom alerting systems
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from loguru import logger


class AlertSeverity(str, Enum):
    """Alert severity levels."""

    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class AlertCondition(str, Enum):
    """Alert condition types."""

    THRESHOLD = "threshold"
    ANOMALY = "anomaly"
    RATE_OF_CHANGE = "rate_of_change"
    ABSENCE = "absence"


@dataclass
class AlertRule:
    """Alert rule configuration."""

    name: str
    description: str
    severity: AlertSeverity
    condition: AlertCondition
    query: str
    threshold: float | None = None
    duration: str = "5m"
    labels: dict[str, str] = field(default_factory=dict)
    annotations: dict[str, str] = field(default_factory=dict)
    notification_channels: list[str] = field(default_factory=list)


class AlertRuleBuilder:
    """
    Builder for creating alert rules.

    Creates alert rules for various monitoring systems.
    """

    def __init__(self):
        """Initialize alert rule builder."""
        self.rules: list[AlertRule] = []

    def build_system_alerts(self) -> list[AlertRule]:
        """
        Build system-level alerts.

        Returns:
            list: List of alert rules
        """
        return [
            # High error rate
            AlertRule(
                name="HighErrorRate",
                description="Error rate exceeds 5% of requests",
                severity=AlertSeverity.CRITICAL,
                condition=AlertCondition.THRESHOLD,
                query='rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m]) > 0.05',
                threshold=0.05,
                duration="5m",
                labels={"team": "backend", "severity": "critical"},
                annotations={
                    "summary": "High error rate detected",
                    "description": "Error rate is {{ $value | humanizePercentage }} (threshold: 5%)",
                },
                notification_channels=["pagerduty", "slack"],
            ),
            # Slow response time
            AlertRule(
                name="SlowResponseTime",
                description="95th percentile response time exceeds 2 seconds",
                severity=AlertSeverity.WARNING,
                condition=AlertCondition.THRESHOLD,
                query='histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 2',
                threshold=2.0,
                duration="10m",
                labels={"team": "backend", "severity": "warning"},
                annotations={
                    "summary": "Slow API response time",
                    "description": "P95 response time is {{ $value | humanizeDuration }} (threshold: 2s)",
                },
                notification_channels=["slack"],
            ),
            # High CPU usage
            AlertRule(
                name="HighCPUUsage",
                description="CPU usage exceeds 80%",
                severity=AlertSeverity.WARNING,
                condition=AlertCondition.THRESHOLD,
                query='avg(rate(process_cpu_seconds_total[5m])) * 100 > 80',
                threshold=80.0,
                duration="15m",
                labels={"team": "infrastructure", "severity": "warning"},
                annotations={
                    "summary": "High CPU usage detected",
                    "description": "CPU usage is {{ $value | humanize }}% (threshold: 80%)",
                },
                notification_channels=["email"],
            ),
            # Low memory
            AlertRule(
                name="LowMemory",
                description="Available memory below 10%",
                severity=AlertSeverity.CRITICAL,
                condition=AlertCondition.THRESHOLD,
                query='(node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes) * 100 < 10',
                threshold=10.0,
                duration="5m",
                labels={"team": "infrastructure", "severity": "critical"},
                annotations={
                    "summary": "Low memory available",
                    "description": "Available memory is {{ $value | humanize }}% (threshold: 10%)",
                },
                notification_channels=["pagerduty", "slack"],
            ),
            # Database connection pool exhaustion
            AlertRule(
                name="DatabaseConnectionPoolExhaustion",
                description="Database connection pool usage exceeds 90%",
                severity=AlertSeverity.CRITICAL,
                condition=AlertCondition.THRESHOLD,
                query='(db_connections_active / db_connections_max) * 100 > 90',
                threshold=90.0,
                duration="5m",
                labels={"team": "backend", "severity": "critical"},
                annotations={
                    "summary": "Database connection pool near exhaustion",
                    "description": "Connection pool usage is {{ $value | humanize }}% (threshold: 90%)",
                },
                notification_channels=["pagerduty", "slack"],
            ),
        ]

    def build_compliance_alerts(self) -> list[AlertRule]:
        """
        Build compliance-related alerts.

        Returns:
            list: List of compliance alert rules
        """
        return [
            # ACGME violations
            AlertRule(
                name="ACGMEViolationDetected",
                description="ACGME violation detected",
                severity=AlertSeverity.CRITICAL,
                condition=AlertCondition.THRESHOLD,
                query='increase(acgme_violations_total[1h]) > 0',
                threshold=0.0,
                duration="1m",
                labels={"team": "compliance", "severity": "critical"},
                annotations={
                    "summary": "ACGME violation detected",
                    "description": "{{ $value }} ACGME violations in last hour",
                },
                notification_channels=["pagerduty", "email", "slack"],
            ),
            # Multiple violations for same person
            AlertRule(
                name="RepeatedACGMEViolations",
                description="Multiple ACGME violations for same person",
                severity=AlertSeverity.CRITICAL,
                condition=AlertCondition.THRESHOLD,
                query='count by (person_id) (increase(acgme_violations_total[24h])) > 2',
                threshold=2.0,
                duration="1m",
                labels={"team": "compliance", "severity": "critical"},
                annotations={
                    "summary": "Repeated ACGME violations for person",
                    "description": "Person {{ $labels.person_id }} has {{ $value }} violations in 24h",
                },
                notification_channels=["pagerduty", "email"],
            ),
            # Work hour threshold approaching
            AlertRule(
                name="WorkHourThresholdApproaching",
                description="Resident approaching 80-hour threshold",
                severity=AlertSeverity.WARNING,
                condition=AlertCondition.THRESHOLD,
                query='resident_work_hours_weekly > 75',
                threshold=75.0,
                duration="1h",
                labels={"team": "compliance", "severity": "warning"},
                annotations={
                    "summary": "Resident approaching work hour limit",
                    "description": "Resident {{ $labels.person_id }} has {{ $value }} hours this week (threshold: 75)",
                },
                notification_channels=["slack", "email"],
            ),
        ]

    def build_security_alerts(self) -> list[AlertRule]:
        """
        Build security-related alerts.

        Returns:
            list: List of security alert rules
        """
        return [
            # Failed authentication spike
            AlertRule(
                name="FailedAuthenticationSpike",
                description="Spike in failed authentication attempts",
                severity=AlertSeverity.CRITICAL,
                condition=AlertCondition.RATE_OF_CHANGE,
                query='rate(auth_failures_total[5m]) > 1',
                threshold=1.0,
                duration="5m",
                labels={"team": "security", "severity": "critical"},
                annotations={
                    "summary": "Failed authentication spike detected",
                    "description": "{{ $value | humanize }} failed auth attempts per second",
                },
                notification_channels=["pagerduty", "slack"],
            ),
            # Suspicious activity
            AlertRule(
                name="SuspiciousActivityDetected",
                description="Suspicious activity event logged",
                severity=AlertSeverity.CRITICAL,
                condition=AlertCondition.THRESHOLD,
                query='increase(suspicious_activity_total[5m]) > 0',
                threshold=0.0,
                duration="1m",
                labels={"team": "security", "severity": "critical"},
                annotations={
                    "summary": "Suspicious activity detected",
                    "description": "{{ $value }} suspicious events in last 5 minutes",
                },
                notification_channels=["pagerduty", "email"],
            ),
            # Rate limit violations
            AlertRule(
                name="RateLimitViolations",
                description="High rate of rate limit violations",
                severity=AlertSeverity.WARNING,
                condition=AlertCondition.THRESHOLD,
                query='rate(rate_limit_exceeded_total[5m]) > 0.5',
                threshold=0.5,
                duration="5m",
                labels={"team": "security", "severity": "warning"},
                annotations={
                    "summary": "High rate of rate limit violations",
                    "description": "{{ $value | humanize }} rate limit violations per second",
                },
                notification_channels=["slack"],
            ),
            # Data export volume
            AlertRule(
                name="LargeDataExport",
                description="Large data export detected",
                severity=AlertSeverity.WARNING,
                condition=AlertCondition.THRESHOLD,
                query='data_export_records_total > 1000',
                threshold=1000.0,
                duration="1m",
                labels={"team": "security", "severity": "warning"},
                annotations={
                    "summary": "Large data export detected",
                    "description": "User {{ $labels.user_id }} exported {{ $value }} records",
                },
                notification_channels=["slack", "email"],
            ),
        ]

    def build_performance_alerts(self) -> list[AlertRule]:
        """
        Build performance-related alerts.

        Returns:
            list: List of performance alert rules
        """
        return [
            # Slow database queries
            AlertRule(
                name="SlowDatabaseQueries",
                description="Database queries exceeding 1 second",
                severity=AlertSeverity.WARNING,
                condition=AlertCondition.THRESHOLD,
                query='histogram_quantile(0.95, rate(db_query_duration_seconds_bucket[5m])) > 1',
                threshold=1.0,
                duration="10m",
                labels={"team": "backend", "severity": "warning"},
                annotations={
                    "summary": "Slow database queries detected",
                    "description": "P95 query time is {{ $value | humanizeDuration }}",
                },
                notification_channels=["slack"],
            ),
            # Low cache hit rate
            AlertRule(
                name="LowCacheHitRate",
                description="Cache hit rate below 70%",
                severity=AlertSeverity.WARNING,
                condition=AlertCondition.THRESHOLD,
                query='rate(cache_hits_total[5m]) / (rate(cache_hits_total[5m]) + rate(cache_misses_total[5m])) < 0.7',
                threshold=0.7,
                duration="15m",
                labels={"team": "backend", "severity": "warning"},
                annotations={
                    "summary": "Low cache hit rate",
                    "description": "Cache hit rate is {{ $value | humanizePercentage }} (threshold: 70%)",
                },
                notification_channels=["slack"],
            ),
        ]


def to_prometheus_rules(rules: list[AlertRule]) -> dict[str, Any]:
    """
    Convert alert rules to Prometheus format.

    Args:
        rules: List of alert rules

    Returns:
        dict: Prometheus rules file format
    """
    groups = []
    rules_by_severity = {}

    # Group by severity
    for rule in rules:
        if rule.severity.value not in rules_by_severity:
            rules_by_severity[rule.severity.value] = []
        rules_by_severity[rule.severity.value].append(rule)

    # Create groups
    for severity, severity_rules in rules_by_severity.items():
        group_rules = []

        for rule in severity_rules:
            group_rules.append(
                {
                    "alert": rule.name,
                    "expr": rule.query,
                    "for": rule.duration,
                    "labels": {**rule.labels, "severity": rule.severity.value},
                    "annotations": rule.annotations,
                }
            )

        groups.append({"name": f"{severity}_alerts", "rules": group_rules})

    return {"groups": groups}


def get_all_alert_rules() -> list[AlertRule]:
    """
    Get all pre-configured alert rules.

    Returns:
        list: All alert rules
    """
    builder = AlertRuleBuilder()

    return (
        builder.build_system_alerts()
        + builder.build_compliance_alerts()
        + builder.build_security_alerts()
        + builder.build_performance_alerts()
    )


def export_prometheus_rules(output_file: str) -> None:
    """
    Export alert rules to Prometheus rules file.

    Args:
        output_file: Path to output file
    """
    import yaml

    rules = get_all_alert_rules()
    prometheus_rules = to_prometheus_rules(rules)

    with open(output_file, "w") as f:
        yaml.dump(prometheus_rules, f, default_flow_style=False)

    logger.info(f"Exported {len(rules)} alert rules to {output_file}")
