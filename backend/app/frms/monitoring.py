"""
Real-Time Fatigue Monitoring and Alerting System.

This module provides real-time monitoring of resident fatigue levels
with configurable alerting for program directors.

Features:
1. Continuous fatigue score tracking
2. Threshold-based alerting (configurable)
3. Trend detection (rapid degradation warnings)
4. Dashboard metrics aggregation
5. Historical analysis and reporting
6. Integration with notification system

Alert Levels:
- INFO: Fatigue approaching caution threshold
- WARNING: Fatigue below FAA caution threshold (77%)
- CRITICAL: Fatigue below FRA high-risk threshold (70%)
- EMERGENCY: Fatigue at unacceptable levels (<60%)
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any
from uuid import UUID
import json

from app.frms.three_process_model import (
    ThreeProcessModel,
    AlertnessState,
    EffectivenessScore,
)
from app.frms.performance_predictor import PerformancePredictor
from app.frms.constants import (
    THRESHOLD_OPTIMAL,
    THRESHOLD_ACCEPTABLE,
    THRESHOLD_FAA_CAUTION,
    THRESHOLD_FRA_HIGH_RISK,
    THRESHOLD_CRITICAL,
    TREND_WINDOW_HOURS,
    TREND_THRESHOLD_PERCENT,
    EFFECTIVENESS_HISTORY_HOURS,
    EXTENDED_WAKEFULNESS_HOURS,
    LAST_24_HOURS,
    TOP_RISK_RESIDENTS_COUNT,
)

logger = logging.getLogger(__name__)


class AlertSeverity(str, Enum):
    """Alert severity levels for fatigue monitoring."""

    INFO = "info"  # Approaching thresholds
    WARNING = "warning"  # Below FAA caution (77%)
    CRITICAL = "critical"  # Below FRA threshold (70%)
    EMERGENCY = "emergency"  # Below unacceptable (60%)


@dataclass
class FatigueAlert:
    """
    A fatigue-related alert for a resident.

    Represents a notification that should be sent to program directors
    when fatigue levels become concerning.
    """

    alert_id: str
    person_id: UUID
    person_name: str
    severity: AlertSeverity
    created_at: datetime
    effectiveness_score: float
    threshold_violated: float
    message: str
    contributing_factors: dict[str, Any] = field(default_factory=dict)
    recommended_actions: list[str] = field(default_factory=list)
    acknowledged: bool = False
    acknowledged_at: datetime | None = None
    acknowledged_by: str | None = None

    def to_dict(self) -> dict:
        """Serialize to dictionary for API response."""
        return {
            "alert_id": self.alert_id,
            "person_id": str(self.person_id),
            "person_name": self.person_name,
            "severity": self.severity.value,
            "created_at": self.created_at.isoformat(),
            "effectiveness_score": round(self.effectiveness_score, 2),
            "threshold_violated": round(self.threshold_violated, 2),
            "message": self.message,
            "contributing_factors": self.contributing_factors,
            "recommended_actions": self.recommended_actions,
            "acknowledged": self.acknowledged,
            "acknowledged_at": self.acknowledged_at.isoformat()
            if self.acknowledged_at
            else None,
            "acknowledged_by": self.acknowledged_by,
        }


@dataclass
class DashboardMetrics:
    """
    Aggregated metrics for program director dashboard.

    Real-time snapshot of fatigue status across all residents.
    """

    timestamp: datetime
    total_residents: int
    active_alerts: int

    # Distribution by risk level
    at_optimal: int  # ≥95%
    at_acceptable: int  # 85-94%
    at_caution: int  # 77-84%
    at_high_risk: int  # 70-76%
    at_critical: int  # <70%

    # Trend indicators
    improving: int  # Fatigue decreasing
    stable: int  # No significant change
    degrading: int  # Fatigue increasing

    # Top concerns
    highest_risk_residents: list[dict] = field(default_factory=list)
    upcoming_risk_shifts: list[dict] = field(default_factory=list)

    # 24-hour statistics
    alerts_last_24h: int = 0
    avg_effectiveness_24h: float = 85.0
    min_effectiveness_24h: float = 70.0

    def to_dict(self) -> dict:
        """Serialize to dictionary for API response."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "total_residents": self.total_residents,
            "active_alerts": self.active_alerts,
            "distribution": {
                "optimal": self.at_optimal,
                "acceptable": self.at_acceptable,
                "caution": self.at_caution,
                "high_risk": self.at_high_risk,
                "critical": self.at_critical,
            },
            "trends": {
                "improving": self.improving,
                "stable": self.stable,
                "degrading": self.degrading,
            },
            "highest_risk_residents": self.highest_risk_residents,
            "upcoming_risk_shifts": self.upcoming_risk_shifts,
            "last_24h": {
                "alerts": self.alerts_last_24h,
                "avg_effectiveness": round(self.avg_effectiveness_24h, 2),
                "min_effectiveness": round(self.min_effectiveness_24h, 2),
            },
        }


class FatigueMonitor:
    """
    Real-time fatigue monitoring service.

    Tracks fatigue levels for all residents and generates alerts
    when thresholds are exceeded.

    Usage:
        monitor = FatigueMonitor()

        # Update resident state
        monitor.update_resident(resident_id, assignments, datetime.now())

        # Check for alerts
        alerts = monitor.check_alerts()

        # Get dashboard metrics
        dashboard = monitor.get_dashboard_metrics()
    """

    # Alert thresholds (imported from constants)
    THRESHOLD_OPTIMAL = THRESHOLD_OPTIMAL
    THRESHOLD_ACCEPTABLE = THRESHOLD_ACCEPTABLE
    THRESHOLD_FAA_CAUTION = THRESHOLD_FAA_CAUTION
    THRESHOLD_FRA_HIGH_RISK = THRESHOLD_FRA_HIGH_RISK
    THRESHOLD_CRITICAL = THRESHOLD_CRITICAL

    # Trend detection (imported from constants)
    TREND_WINDOW_HOURS = TREND_WINDOW_HOURS
    TREND_THRESHOLD = TREND_THRESHOLD_PERCENT

    def __init__(
        self,
        alert_callback: Any | None = None,
        enable_notifications: bool = True,
    ) -> None:
        """
        Initialize fatigue monitor.

        Args:
            alert_callback: Optional callback function for new alerts
            enable_notifications: Whether to send external notifications
        """
        self.model = ThreeProcessModel()
        self.predictor = PerformancePredictor()

        # State tracking
        self._resident_states: dict[UUID, AlertnessState] = {}
        self._active_alerts: dict[str, FatigueAlert] = {}
        self._alert_history: list[FatigueAlert] = []
        self._effectiveness_history: dict[UUID, list[tuple[datetime, float]]] = {}

        # Configuration
        self.alert_callback = alert_callback
        self.enable_notifications = enable_notifications

        # Deduplication with timestamps
        self._recent_alert_keys: dict[str, datetime] = {}

        logger.info("FatigueMonitor initialized")

    def update_resident(
        self,
        person_id: UUID,
        person_name: str,
        assignments: list[dict],
        current_time: datetime,
        sleep_data: dict | None = None,
    ) -> EffectivenessScore | None:
        """
        Update fatigue state for a resident.

        Args:
            person_id: Resident UUID
            person_name: Resident name
            assignments: Recent assignments
            current_time: Current time
            sleep_data: Optional sleep tracking data

        Returns:
            Current effectiveness score, or None if update failed
        """
        # Get or create state
        state = self._resident_states.get(person_id)
        if state is None:
            state = self.model.create_state(person_id, timestamp=current_time)
            self._resident_states[person_id] = state

            # Calculate time since last update
        time_diff = (current_time - state.timestamp).total_seconds() / 3600.0

        if time_diff > 0:
            # Update for time awake
            state = self.model.update_wakefulness(state, time_diff)
            self._resident_states[person_id] = state

            # Record effectiveness history
        if person_id not in self._effectiveness_history:
            self._effectiveness_history[person_id] = []

        if state.effectiveness:
            self._effectiveness_history[person_id].append(
                (current_time, state.effectiveness.overall)
            )
            # Keep only last 48 hours
            cutoff = current_time - timedelta(hours=EFFECTIVENESS_HISTORY_HOURS)
            self._effectiveness_history[person_id] = [
                (t, e) for t, e in self._effectiveness_history[person_id] if t >= cutoff
            ]

            # Check for alerts
        if state.effectiveness:
            self._check_and_generate_alert(
                person_id, person_name, state.effectiveness, current_time
            )

        return state.effectiveness

    def _check_and_generate_alert(
        self,
        person_id: UUID,
        person_name: str,
        effectiveness: EffectivenessScore,
        current_time: datetime,
    ) -> FatigueAlert | None:
        """Check thresholds and generate alert if needed."""
        score = effectiveness.overall

        # Determine severity
        if score < self.THRESHOLD_CRITICAL:
            severity = AlertSeverity.EMERGENCY
            threshold = self.THRESHOLD_CRITICAL
            message = f"EMERGENCY: {person_name} effectiveness at {score:.1f}% - immediate action required"
        elif score < self.THRESHOLD_FRA_HIGH_RISK:
            severity = AlertSeverity.CRITICAL
            threshold = self.THRESHOLD_FRA_HIGH_RISK
            message = f"CRITICAL: {person_name} effectiveness at {score:.1f}% - high error risk"
        elif score < self.THRESHOLD_FAA_CAUTION:
            severity = AlertSeverity.WARNING
            threshold = self.THRESHOLD_FAA_CAUTION
            message = f"WARNING: {person_name} effectiveness at {score:.1f}% - caution advised"
        elif score < self.THRESHOLD_ACCEPTABLE:
            severity = AlertSeverity.INFO
            threshold = self.THRESHOLD_ACCEPTABLE
            message = f"INFO: {person_name} effectiveness declining to {score:.1f}%"
        else:
            return None  # No alert needed

            # Check for deduplication (don't repeat same alert within 1 hour)
        alert_key = f"{person_id}_{severity.value}"
        now = datetime.utcnow()

        if alert_key in self._recent_alert_keys:
            last_alert_time = self._recent_alert_keys[alert_key]
            if now - last_alert_time < timedelta(hours=1):
                return None

                # Generate alert
        alert = FatigueAlert(
            alert_id=f"alert_{person_id}_{current_time.timestamp():.0f}",
            person_id=person_id,
            person_name=person_name,
            severity=severity,
            created_at=current_time,
            effectiveness_score=score,
            threshold_violated=threshold,
            message=message,
            contributing_factors=effectiveness.factors,
            recommended_actions=self._get_recommendations(severity, effectiveness),
        )

        # Store alert
        self._active_alerts[alert.alert_id] = alert
        self._alert_history.append(alert)
        self._recent_alert_keys[alert_key] = now

        # Clean up old deduplication keys (older than 1 hour)
        self._cleanup_old_alert_keys(now)

        # Trigger callback
        if self.alert_callback and self.enable_notifications:
            try:
                self.alert_callback(alert)
            except Exception as e:
                logger.error(f"Alert callback failed: {e}")

        logger.warning(f"Generated fatigue alert: {alert.message}")

        return alert

    def _get_recommendations(
        self,
        severity: AlertSeverity,
        effectiveness: EffectivenessScore,
    ) -> list[str]:
        """Get recommended actions based on severity."""
        recommendations = []

        if severity == AlertSeverity.EMERGENCY:
            recommendations.extend(
                [
                    "IMMEDIATE: Remove from clinical duties",
                    "Ensure faculty coverage for current patients",
                    "Mandatory rest period before returning",
                    "Consider wellness check-in",
                ]
            )
        elif severity == AlertSeverity.CRITICAL:
            recommendations.extend(
                [
                    "Reduce current workload",
                    "Ensure close faculty supervision",
                    "Schedule rest period within 2 hours",
                    "Avoid high-risk procedures",
                ]
            )
        elif severity == AlertSeverity.WARNING:
            recommendations.extend(
                [
                    "Monitor closely for further degradation",
                    "Consider scheduling break",
                    "Review upcoming assignments for fatigue impact",
                ]
            )
        elif severity == AlertSeverity.INFO:
            recommendations.extend(
                [
                    "Track fatigue trend",
                    "Ensure adequate rest before next shift",
                ]
            )

            # Add factor-specific recommendations
        factors = effectiveness.factors
        if factors.get("in_wocl"):
            recommendations.append(
                "Currently in WOCL (2-6 AM) - heightened vigilance needed"
            )

        if factors.get("hours_awake", 0) > EXTENDED_WAKEFULNESS_HOURS:
            recommendations.append(
                f"Extended wakefulness ({factors.get('hours_awake'):.0f} hours) - prioritize rest"
            )

        return recommendations

    def _cleanup_old_alert_keys(self, current_time: datetime) -> None:
        """
        Remove deduplication keys older than 1 hour.

        This prevents memory growth from accumulating alert keys
        while still maintaining the 1-hour deduplication window.

        Args:
            current_time: Current timestamp for age calculation
        """
        cutoff = current_time - timedelta(hours=1)
        expired_keys = [
            key
            for key, timestamp in self._recent_alert_keys.items()
            if timestamp < cutoff
        ]
        for key in expired_keys:
            del self._recent_alert_keys[key]

    def check_alerts(self) -> list[FatigueAlert]:
        """
        Get all active (unacknowledged) alerts.

        Returns:
            List of active FatigueAlert objects
        """
        return [
            alert for alert in self._active_alerts.values() if not alert.acknowledged
        ]

    def acknowledge_alert(
        self,
        alert_id: str,
        acknowledged_by: str,
    ) -> bool:
        """
        Acknowledge an alert.

        Args:
            alert_id: ID of alert to acknowledge
            acknowledged_by: Who acknowledged the alert

        Returns:
            True if alert was found and acknowledged
        """
        alert = self._active_alerts.get(alert_id)
        if alert:
            alert.acknowledged = True
            alert.acknowledged_at = datetime.now()
            alert.acknowledged_by = acknowledged_by
            logger.info(f"Alert {alert_id} acknowledged by {acknowledged_by}")
            return True
        return False

    def get_dashboard_metrics(self) -> DashboardMetrics:
        """
        Get aggregated metrics for dashboard display.

        Returns:
            DashboardMetrics with current fatigue status
        """
        now = datetime.now()

        # Count by risk level
        at_optimal = 0
        at_acceptable = 0
        at_caution = 0
        at_high_risk = 0
        at_critical = 0

        improving = 0
        stable = 0
        degrading = 0

        highest_risk = []

        for person_id, state in self._resident_states.items():
            if not state.effectiveness:
                continue

            score = state.effectiveness.overall

            # Distribution
            if score >= self.THRESHOLD_OPTIMAL:
                at_optimal += 1
            elif score >= self.THRESHOLD_ACCEPTABLE:
                at_acceptable += 1
            elif score >= self.THRESHOLD_FAA_CAUTION:
                at_caution += 1
            elif score >= self.THRESHOLD_FRA_HIGH_RISK:
                at_high_risk += 1
            else:
                at_critical += 1

                # Trend
            trend = self._calculate_trend(person_id)
            if trend > self.TREND_THRESHOLD:
                improving += 1
            elif trend < -self.TREND_THRESHOLD:
                degrading += 1
            else:
                stable += 1

                # Track highest risk
            if score < self.THRESHOLD_FAA_CAUTION:
                highest_risk.append(
                    {
                        "person_id": str(person_id),
                        "effectiveness": round(score, 2),
                        "risk_level": state.effectiveness.risk_level,
                    }
                )

                # Sort highest risk
        highest_risk.sort(key=lambda x: x["effectiveness"])
        highest_risk = highest_risk[:TOP_RISK_RESIDENTS_COUNT]  # Top N

        # Active alerts
        active_alerts = len(self.check_alerts())

        # 24-hour statistics
        cutoff = now - timedelta(hours=LAST_24_HOURS)
        alerts_24h = len([a for a in self._alert_history if a.created_at >= cutoff])

        # Effectiveness 24h
        all_scores_24h = []
        for person_id, history in self._effectiveness_history.items():
            recent = [e for t, e in history if t >= cutoff]
            all_scores_24h.extend(recent)

        avg_24h = sum(all_scores_24h) / len(all_scores_24h) if all_scores_24h else 85.0
        min_24h = min(all_scores_24h) if all_scores_24h else 70.0

        return DashboardMetrics(
            timestamp=now,
            total_residents=len(self._resident_states),
            active_alerts=active_alerts,
            at_optimal=at_optimal,
            at_acceptable=at_acceptable,
            at_caution=at_caution,
            at_high_risk=at_high_risk,
            at_critical=at_critical,
            improving=improving,
            stable=stable,
            degrading=degrading,
            highest_risk_residents=highest_risk,
            upcoming_risk_shifts=[],  # TODO: Integrate with schedule
            alerts_last_24h=alerts_24h,
            avg_effectiveness_24h=avg_24h,
            min_effectiveness_24h=min_24h,
        )

    def _calculate_trend(self, person_id: UUID) -> float:
        """
        Calculate effectiveness trend for a resident.

        Returns:
            Positive = improving, Negative = degrading
        """
        history = self._effectiveness_history.get(person_id, [])
        if len(history) < 2:
            return 0.0

        cutoff = datetime.now() - timedelta(hours=self.TREND_WINDOW_HOURS)
        recent = [(t, e) for t, e in history if t >= cutoff]

        if len(recent) < 2:
            return 0.0

            # Calculate slope
        first_score = recent[0][1]
        last_score = recent[-1][1]

        return last_score - first_score

    def get_resident_history(
        self,
        person_id: UUID,
        hours: int = 24,
    ) -> list[dict]:
        """
        Get effectiveness history for a resident.

        Args:
            person_id: Resident UUID
            hours: Hours of history to retrieve

        Returns:
            List of {timestamp, effectiveness} dicts
        """
        history = self._effectiveness_history.get(person_id, [])
        cutoff = datetime.now() - timedelta(hours=hours)

        return [
            {"timestamp": t.isoformat(), "effectiveness": round(e, 2)}
            for t, e in history
            if t >= cutoff
        ]

    def export_alert_report(
        self,
        start_date: datetime,
        end_date: datetime,
    ) -> dict:
        """
        Export alert report for a date range.

        Args:
            start_date: Report start date
            end_date: Report end date

        Returns:
            Report dict with alert statistics
        """
        relevant_alerts = [
            a for a in self._alert_history if start_date <= a.created_at <= end_date
        ]

        by_severity = {}
        by_person = {}

        for alert in relevant_alerts:
            # By severity
            sev = alert.severity.value
            by_severity[sev] = by_severity.get(sev, 0) + 1

            # By person
            pid = str(alert.person_id)
            if pid not in by_person:
                by_person[pid] = {
                    "name": alert.person_name,
                    "count": 0,
                    "severities": [],
                }
            by_person[pid]["count"] += 1
            by_person[pid]["severities"].append(sev)

        return {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "total_alerts": len(relevant_alerts),
            "by_severity": by_severity,
            "by_person": by_person,
            "acknowledged_count": len([a for a in relevant_alerts if a.acknowledged]),
            "unacknowledged_count": len(
                [a for a in relevant_alerts if not a.acknowledged]
            ),
        }
