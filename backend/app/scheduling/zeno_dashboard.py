"""
Quantum Zeno Effect Dashboard Metrics.

Provides visualization and reporting for Zeno effect monitoring.
"""

from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from typing import Any

from app.scheduling.zeno_governor import (
    InterventionPolicy,
    OptimizationFreedomWindow,
    ZenoGovernor,
    ZenoMetrics,
    ZenoRisk,
)


@dataclass
class ZenoDashboardSummary:
    """Summary metrics for Zeno effect dashboard."""

    # Current state
    current_risk: ZenoRisk
    current_frozen_ratio: float
    current_measurement_frequency: float
    local_optima_risk: float

    # 24-hour trends
    interventions_24h: int
    frozen_assignments: int
    solver_attempts_blocked: int
    evolution_prevented: int

    # 7-day trends
    interventions_7d: int
    avg_interventions_per_day: float
    trend_direction: str  # "improving", "stable", "degrading"

    # Policy recommendations
    recommended_policy: dict[str, Any]
    is_in_freedom_window: bool
    active_freedom_windows: int

    # Alerts
    critical_alerts: list[str]
    warnings: list[str]
    recommendations: list[str]

    # Historical
    last_successful_evolution: datetime | None
    hours_since_evolution: float | None


class ZenoDashboard:
    """
    Dashboard for Zeno effect monitoring and visualization.

    Provides high-level summaries and trends for program coordinators.
    """

    def __init__(self, governor: ZenoGovernor) -> None:
        """
        Initialize dashboard with governor instance.

        Args:
            governor: ZenoGovernor instance to monitor
        """
        self.governor = governor

    async def get_summary(self) -> ZenoDashboardSummary:
        """
        Get dashboard summary with current state and trends.

        Returns:
            ZenoDashboardSummary with all metrics

        Example:
            dashboard = ZenoDashboard(governor)
            summary = await dashboard.get_summary()
            print(f"Risk: {summary.current_risk}")
        """
        metrics = self.governor.get_current_metrics()

        # Calculate trends
        trend_direction = self._analyze_trend(metrics)

        # Get policy as dict
        policy_dict = asdict(metrics.recommended_policy)

        # Calculate time since last evolution
        hours_since_evolution = None
        if metrics.last_successful_evolution:
            hours_since_evolution = (
                datetime.now() - metrics.last_successful_evolution
            ).total_seconds() / 3600

        # Generate alerts
        critical_alerts = self._generate_critical_alerts(metrics)
        warnings = self._generate_warnings(metrics)
        recommendations = metrics.immediate_actions

        return ZenoDashboardSummary(
            current_risk=metrics.risk_level,
            current_frozen_ratio=metrics.frozen_ratio,
            current_measurement_frequency=metrics.measurement_frequency,
            local_optima_risk=metrics.local_optima_risk,
            interventions_24h=metrics.interventions_24h,
            frozen_assignments=metrics.frozen_assignments,
            solver_attempts_blocked=metrics.solver_attempts_blocked,
            evolution_prevented=metrics.evolution_prevented,
            interventions_7d=metrics.interventions_7d,
            avg_interventions_per_day=metrics.interventions_7d / 7.0,
            trend_direction=trend_direction,
            recommended_policy=policy_dict,
            is_in_freedom_window=self.governor.is_in_freedom_window(),
            active_freedom_windows=len(
                [w for w in self.governor.freedom_windows if w.is_active]
            ),
            critical_alerts=critical_alerts,
            warnings=warnings,
            recommendations=recommendations,
            last_successful_evolution=metrics.last_successful_evolution,
            hours_since_evolution=hours_since_evolution,
        )

    def _analyze_trend(self, metrics: ZenoMetrics) -> str:
        """
        Analyze trend direction.

        Args:
            metrics: Current ZenoMetrics

        Returns:
            "improving", "stable", or "degrading"
        """
        # Simple heuristic: compare 24h vs 7d average
        if metrics.interventions_7d == 0:
            return "stable"

        daily_avg = metrics.interventions_7d / 7.0
        current_rate = metrics.interventions_24h

        if current_rate < daily_avg * 0.8:
            return "improving"
        elif current_rate > daily_avg * 1.2:
            return "degrading"
        else:
            return "stable"

    def _generate_critical_alerts(self, metrics: ZenoMetrics) -> list[str]:
        """Generate critical alerts requiring immediate attention."""
        alerts = []

        if metrics.risk_level == ZenoRisk.CRITICAL:
            alerts.append(
                f"🚨 CRITICAL: Zeno effect freezing optimization "
                f"({metrics.frozen_ratio:.0%} frozen, "
                f"{metrics.measurement_frequency * 24:.1f} checks/day)"
            )

        if metrics.frozen_ratio > 0.7:
            alerts.append(f"🚨 {metrics.frozen_ratio:.0%} of assignments are locked")

        if metrics.evolution_prevented > 10:
            alerts.append(
                f"🚨 {metrics.evolution_prevented} solver improvements blocked"
            )

        if metrics.last_successful_evolution:
            hours_since = (
                datetime.now() - metrics.last_successful_evolution
            ).total_seconds() / 3600
            if hours_since > 48:
                alerts.append(
                    f"🚨 No solver progress in {hours_since:.1f} hours "
                    "(likely trapped in local optimum)"
                )

        return alerts

    def _generate_warnings(self, metrics: ZenoMetrics) -> list[str]:
        """Generate warnings for potential issues."""
        warnings = []

        if metrics.risk_level == ZenoRisk.HIGH:
            warnings.append(
                f"⚠️ HIGH Zeno risk: {metrics.measurement_frequency * 24:.1f} interventions/day"
            )

        if metrics.risk_level == ZenoRisk.MODERATE:
            warnings.append(
                f"📊 MODERATE Zeno risk: {metrics.frozen_ratio:.0%} assignments frozen"
            )

        if metrics.local_optima_risk > 0.7:
            warnings.append(
                f"⚠️ Local optima trap risk: {metrics.local_optima_risk:.0%}"
            )

        if metrics.solver_attempts_blocked > 5:
            warnings.append(
                f"⚠️ {metrics.solver_attempts_blocked} solver attempts blocked in 24h"
            )

        # Check for specific users locking too many assignments
        if metrics.frozen_by_user:
            for user_id, count in metrics.frozen_by_user.items():
                if count > metrics.total_assignments * 0.3:
                    warnings.append(
                        f"⚠️ User {user_id} has locked {count} assignments "
                        f"({count / metrics.total_assignments:.0%})"
                    )

        return warnings

    async def get_intervention_history(self, hours: int = 24) -> list[dict[str, Any]]:
        """
        Get intervention history for specified time window.

        Args:
            hours: Hours of history to retrieve

        Returns:
            List of intervention records
        """
        cutoff = datetime.now() - timedelta(hours=hours)
        recent = [i for i in self.governor.interventions if i.timestamp >= cutoff]

        return [
            {
                "intervention_id": str(i.intervention_id),
                "timestamp": i.timestamp.isoformat(),
                "user_id": i.user_id,
                "type": i.intervention_type,
                "assignments_reviewed": len(i.assignments_reviewed),
                "assignments_locked": len(i.assignments_locked),
                "assignments_modified": len(i.assignments_modified),
                "reason": i.reason,
            }
            for i in sorted(recent, key=lambda x: x.timestamp, reverse=True)
        ]

    async def get_freedom_window_status(self) -> dict[str, Any]:
        """
        Get status of optimization freedom windows.

        Returns:
            Dictionary with freedom window information
        """
        active_windows = [w for w in self.governor.freedom_windows if w.is_active]

        return {
            "is_in_freedom_window": self.governor.is_in_freedom_window(),
            "active_windows": len(active_windows),
            "total_windows": len(self.governor.freedom_windows),
            "windows": [
                {
                    "window_id": str(w.window_id),
                    "start_time": w.start_time.isoformat(),
                    "end_time": w.end_time.isoformat(),
                    "duration_hours": (w.end_time - w.start_time).total_seconds()
                    / 3600,
                    "is_active": w.is_active,
                    "reason": w.reason,
                    "interventions_blocked": w.interventions_blocked,
                    "solver_improvements": w.solver_improvements,
                    "score_improvement": w.final_score_improvement,
                }
                for w in self.governor.freedom_windows
            ],
        }

    async def get_solver_performance_summary(self) -> dict[str, Any]:
        """
        Get summary of solver performance under Zeno constraints.

        Returns:
            Dictionary with solver performance metrics
        """
        if not self.governor.solver_attempts:
            return {
                "total_attempts": 0,
                "successful_attempts": 0,
                "blocked_attempts": 0,
                "success_rate": 0.0,
                "block_rate": 0.0,
            }

        total = len(self.governor.solver_attempts)
        successful = sum(
            1 for a in self.governor.solver_attempts if a.get("successful", False)
        )
        blocked = sum(
            1 for a in self.governor.solver_attempts if a.get("blocked", False)
        )

        return {
            "total_attempts": total,
            "successful_attempts": successful,
            "blocked_attempts": blocked,
            "success_rate": successful / total if total > 0 else 0.0,
            "block_rate": blocked / total if total > 0 else 0.0,
            "evolution_prevented": self.governor.compute_evolution_prevented(),
            "last_successful_evolution": (
                (
                    timestamp.isoformat()
                    if (timestamp := self.governor.solver_attempts[-1].get("timestamp"))
                    is not None
                    else None
                )
                if self.governor.solver_attempts
                and self.governor.solver_attempts[-1].get("successful")
                else None
            ),
        }

    async def export_metrics_for_monitoring(self) -> dict[str, Any]:
        """
        Export metrics in format suitable for Prometheus/Grafana.

        Returns:
            Dictionary with metrics in monitoring format
        """
        metrics = self.governor.get_current_metrics()

        return {
            "zeno_risk_level": {
                "value": {
                    ZenoRisk.LOW: 0,
                    ZenoRisk.MODERATE: 1,
                    ZenoRisk.HIGH: 2,
                    ZenoRisk.CRITICAL: 3,
                }[metrics.risk_level],
                "labels": {"risk": metrics.risk_level.value},
            },
            "zeno_frozen_ratio": {
                "value": metrics.frozen_ratio,
                "type": "gauge",
            },
            "zeno_measurement_frequency": {
                "value": metrics.measurement_frequency,
                "type": "gauge",
                "unit": "interventions_per_hour",
            },
            "zeno_local_optima_risk": {
                "value": metrics.local_optima_risk,
                "type": "gauge",
            },
            "zeno_interventions_24h": {
                "value": metrics.interventions_24h,
                "type": "counter",
            },
            "zeno_evolution_prevented": {
                "value": metrics.evolution_prevented,
                "type": "counter",
            },
            "zeno_solver_attempts_blocked": {
                "value": metrics.solver_attempts_blocked,
                "type": "counter",
            },
            "zeno_in_freedom_window": {
                "value": 1 if self.governor.is_in_freedom_window() else 0,
                "type": "gauge",
            },
        }


def format_policy_for_display(policy: InterventionPolicy) -> str:
    """
    Format intervention policy as readable text.

    Args:
        policy: InterventionPolicy to format

    Returns:
        Formatted string for display

    Example:
        text = format_policy_for_display(policy)
        print(text)
    """
    lines = [
        "📋 Recommended Intervention Policy",
        "=" * 40,
        f"Max checks per day: {policy.max_checks_per_day}",
        f"Min interval: {policy.min_interval_hours} hours",
        "",
        "Recommended review windows:",
    ]

    for window in policy.recommended_windows:
        lines.append(f"  • {window}")

    if policy.hands_off_periods:
        lines.append("")
        lines.append("Hands-off periods (no interventions):")
        for period in policy.hands_off_periods:
            lines.append(
                f"  • {period['start']}-{period['end']} "
                f"({period['duration_hours']}h): {period['reason']}"
            )

    lines.append("")
    lines.append(f"Auto-lock threshold: {policy.auto_lock_threshold:.0%} confidence")
    lines.append("")
    lines.append("Rationale:")
    lines.append(f"  {policy.explanation}")

    return "\n".join(lines)


def generate_zeno_report(metrics: ZenoMetrics) -> str:
    """
    Generate comprehensive text report of Zeno effect status.

    Args:
        metrics: ZenoMetrics to report

    Returns:
        Formatted report string

    Example:
        report = generate_zeno_report(metrics)
        with open("zeno_report.txt", "w") as f:
            f.write(report)
    """
    risk_emoji = {
        ZenoRisk.LOW: "✅",
        ZenoRisk.MODERATE: "📊",
        ZenoRisk.HIGH: "⚠️",
        ZenoRisk.CRITICAL: "🚨",
    }

    lines = [
        "=" * 60,
        "QUANTUM ZENO EFFECT MONITORING REPORT",
        "=" * 60,
        f"Generated: {metrics.timestamp.strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        f"OVERALL STATUS: {risk_emoji[metrics.risk_level]} {metrics.risk_level.value.upper()}",
        "",
        "CURRENT STATE",
        "-" * 60,
        f"Measurement Frequency: {metrics.measurement_frequency:.3f}/hour "
        f"({metrics.measurement_frequency * 24:.1f}/day)",
        f"Frozen Assignments: {metrics.frozen_assignments} / {metrics.total_assignments} "
        f"({metrics.frozen_ratio:.1%})",
        f"Local Optima Risk: {metrics.local_optima_risk:.1%}",
        f"Evolution Prevented: {metrics.evolution_prevented} improvements blocked",
        "",
        "24-HOUR ACTIVITY",
        "-" * 60,
        f"Interventions: {metrics.interventions_24h}",
        f"Avg Interval: {metrics.avg_interval_hours:.1f} hours",
        f"Solver Attempts Blocked: {metrics.solver_attempts_blocked}",
    ]

    if metrics.last_successful_evolution:
        hours_ago = (
            datetime.now() - metrics.last_successful_evolution
        ).total_seconds() / 3600
        lines.append(f"Last Successful Evolution: {hours_ago:.1f} hours ago")
    else:
        lines.append("Last Successful Evolution: Never")

    lines.extend(
        [
            "",
            "7-DAY TRENDS",
            "-" * 60,
            f"Total Interventions: {metrics.interventions_7d}",
            f"Avg Per Day: {metrics.interventions_7d / 7:.1f}",
            "",
        ]
    )

    if metrics.frozen_by_user:
        lines.append("FROZEN ASSIGNMENTS BY USER")
        lines.append("-" * 60)
        for user_id, count in sorted(
            metrics.frozen_by_user.items(), key=lambda x: x[1], reverse=True
        ):
            pct = (
                (count / metrics.total_assignments * 100)
                if metrics.total_assignments > 0
                else 0
            )
            lines.append(f"{user_id}: {count} ({pct:.1f}%)")
        lines.append("")

    if metrics.immediate_actions:
        lines.append("IMMEDIATE ACTIONS REQUIRED")
        lines.append("-" * 60)
        for action in metrics.immediate_actions:
            lines.append(f"• {action}")
        lines.append("")

    if metrics.watch_items:
        lines.append("WATCH ITEMS")
        lines.append("-" * 60)
        for item in metrics.watch_items:
            lines.append(f"• {item}")
        lines.append("")

    lines.append("RECOMMENDED POLICY")
    lines.append("-" * 60)
    lines.append(format_policy_for_display(metrics.recommended_policy))
    lines.append("")
    lines.append("=" * 60)

    return "\n".join(lines)
