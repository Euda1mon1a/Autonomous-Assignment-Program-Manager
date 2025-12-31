"""
Alert Generation System.

Generates prioritized alerts based on resilience metrics.
Implements alert fatigue prevention and intelligent routing.
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional


class AlertSeverity(str, Enum):
    """Alert severity levels."""

    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


class AlertCategory(str, Enum):
    """Alert categories."""

    UTILIZATION = "utilization"
    COVERAGE = "coverage"
    BURNOUT = "burnout"
    CONTINGENCY = "contingency"
    COMPLIANCE = "compliance"
    SYSTEM = "system"


@dataclass
class Alert:
    """Resilience alert."""

    id: str
    timestamp: datetime
    severity: AlertSeverity
    category: AlertCategory
    title: str
    message: str
    metrics: dict
    recommendations: list[str]
    requires_ack: bool = False
    escalation_time_minutes: int | None = None


class AlertGenerator:
    """
    Generate and prioritize resilience alerts.

    Prevents alert fatigue through:
    - Deduplication
    - Rate limiting
    - Priority scoring
    - Smart escalation
    """

    def __init__(self):
        """Initialize alert generator."""
        self.active_alerts: list[Alert] = []
        self.alert_history: list[Alert] = []
        self.suppressed_alerts: set[str] = set()

    def generate_utilization_alert(
        self,
        utilization: float,
        threshold: float = 0.90,
    ) -> Alert | None:
        """
        Generate utilization alert.

        Args:
            utilization: Current utilization ratio
            threshold: Alert threshold

        Returns:
            Alert if threshold exceeded
        """
        if utilization < threshold:
            return None

        # Determine severity
        if utilization >= 0.98:
            severity = AlertSeverity.EMERGENCY
            escalation = 5  # Escalate after 5 minutes
        elif utilization >= 0.95:
            severity = AlertSeverity.CRITICAL
            escalation = 15
        elif utilization >= 0.90:
            severity = AlertSeverity.WARNING
            escalation = 60
        else:
            severity = AlertSeverity.INFO
            escalation = None

        alert = Alert(
            id=f"util_{datetime.now().isoformat()}",
            timestamp=datetime.now(),
            severity=severity,
            category=AlertCategory.UTILIZATION,
            title=f"High Utilization: {utilization:.1%}",
            message=(
                f"System utilization at {utilization:.1%}, exceeding {threshold:.1%} threshold. "
                f"Queue growth accelerating. Immediate capacity adjustment recommended."
            ),
            metrics={"utilization": utilization, "threshold": threshold},
            recommendations=[
                "Reduce non-essential assignments",
                "Activate backup coverage",
                "Defer elective procedures if possible",
            ],
            requires_ack=severity in [AlertSeverity.CRITICAL, AlertSeverity.EMERGENCY],
            escalation_time_minutes=escalation,
        )

        return alert

    def generate_burnout_alert(
        self,
        infected_count: int,
        total_population: int,
        rt: float,
    ) -> Alert | None:
        """
        Generate burnout epidemic alert.

        Args:
            infected_count: Current burnout cases
            total_population: Total residents
            rt: Effective reproduction number

        Returns:
            Alert if epidemic detected
        """
        prevalence = infected_count / total_population if total_population > 0 else 0.0

        if prevalence < 0.05 and rt < 1.0:
            return None  # Under control

        # Determine severity
        if prevalence > 0.15 or rt > 2.0:
            severity = AlertSeverity.EMERGENCY
        elif prevalence > 0.10 or rt > 1.5:
            severity = AlertSeverity.CRITICAL
        elif prevalence > 0.05 or rt > 1.0:
            severity = AlertSeverity.WARNING
        else:
            severity = AlertSeverity.INFO

        alert = Alert(
            id=f"burnout_{datetime.now().isoformat()}",
            timestamp=datetime.now(),
            severity=severity,
            category=AlertCategory.BURNOUT,
            title=f"Burnout Epidemic: {infected_count}/{total_population} residents",
            message=(
                f"Burnout affecting {infected_count} residents ({prevalence:.1%}). "
                f"Reproduction number Rt={rt:.2f}. "
                f"{'Epidemic growing' if rt > 1 else 'Epidemic declining'}."
            ),
            metrics={
                "infected": infected_count,
                "prevalence": prevalence,
                "rt": rt,
            },
            recommendations=[
                "Implement workload reduction interventions",
                "Activate wellness support programs",
                "Schedule mandatory time off for affected residents",
                "Consider temporary schedule restructuring",
            ],
            requires_ack=True,
        )

        return alert

    def generate_n1_alert(
        self,
        spof_count: int,
        critical_scenarios: list,
    ) -> Alert | None:
        """
        Generate N-1 contingency alert.

        Args:
            spof_count: Number of single points of failure
            critical_scenarios: List of critical N-1 scenarios

        Returns:
            Alert if SPOFs detected
        """
        if spof_count == 0:
            return None

        severity = (
            AlertSeverity.CRITICAL
            if spof_count >= 5
            else AlertSeverity.WARNING
            if spof_count >= 3
            else AlertSeverity.INFO
        )

        alert = Alert(
            id=f"n1_{datetime.now().isoformat()}",
            timestamp=datetime.now(),
            severity=severity,
            category=AlertCategory.CONTINGENCY,
            title=f"N-1 Vulnerabilities: {spof_count} SPOFs detected",
            message=(
                f"System has {spof_count} single points of failure. "
                f"Schedule vulnerable to single-resident unavailability."
            ),
            metrics={"spof_count": spof_count},
            recommendations=[
                "Cross-train residents in critical specialties",
                "Establish backup coverage agreements",
                "Reduce dependency on individual specialists",
            ],
            requires_ack=spof_count >= 5,
        )

        return alert

    def deduplicate_alerts(self, new_alert: Alert) -> bool:
        """
        Check if alert is duplicate of recent alert.

        Args:
            new_alert: New alert to check

        Returns:
            True if duplicate (should suppress)
        """
        # Check recent alerts (last hour)
        recent_cutoff = datetime.now().timestamp() - 3600

        for existing in self.active_alerts:
            if existing.timestamp.timestamp() < recent_cutoff:
                continue

            # Same category and similar metrics = duplicate
            if (
                existing.category == new_alert.category
                and existing.severity == new_alert.severity
            ):
                return True

        return False

    def prioritize_alerts(self, alerts: list[Alert]) -> list[Alert]:
        """
        Prioritize alerts by severity and urgency.

        Args:
            alerts: List of alerts to prioritize

        Returns:
            Sorted list (highest priority first)
        """
        severity_order = {
            AlertSeverity.EMERGENCY: 4,
            AlertSeverity.CRITICAL: 3,
            AlertSeverity.WARNING: 2,
            AlertSeverity.INFO: 1,
        }

        return sorted(
            alerts,
            key=lambda a: (severity_order.get(a.severity, 0), a.timestamp),
            reverse=True,
        )

    def should_escalate(self, alert: Alert) -> bool:
        """
        Check if alert should escalate to next level.

        Args:
            alert: Alert to check

        Returns:
            True if should escalate
        """
        if alert.escalation_time_minutes is None:
            return False

        # Check if alert has been active longer than escalation time
        age_minutes = (datetime.now() - alert.timestamp).total_seconds() / 60

        return age_minutes >= alert.escalation_time_minutes
