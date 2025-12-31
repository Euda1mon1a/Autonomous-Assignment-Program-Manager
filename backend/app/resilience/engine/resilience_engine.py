"""
Resilience Engine - Main Orchestrator.

Coordinates all resilience subsystems:
- Defense level calculation
- Utilization monitoring
- N-1/N-2 contingency analysis
- Burnout epidemiology
- Alert generation
- Recovery planning
"""

from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional

from app.resilience.engine.defense_level_calculator import (
    DefenseLevel,
    DefenseLevelCalculator,
    DefenseLevelResult,
)
from app.resilience.engine.utilization_monitor import UtilizationMonitor, UtilizationSnapshot
from app.resilience.engine.threshold_manager import ThresholdManager, ThresholdViolation


@dataclass
class ResilienceStatus:
    """Overall resilience status."""

    defense_level: DefenseLevelResult
    utilization: UtilizationSnapshot
    threshold_violations: list[ThresholdViolation]
    alerts: list[str]
    timestamp: datetime
    is_healthy: bool
    risk_score: float  # 0.0 (safe) to 1.0 (critical)


class ResilienceEngine:
    """
    Main resilience orchestrator.

    Integrates:
    1. Queuing theory (utilization monitoring)
    2. Power grid contingency (N-1/N-2 analysis)
    3. Cybersecurity (defense in depth)
    4. Epidemiology (burnout spread)
    5. SPC (statistical monitoring)
    """

    def __init__(self):
        """Initialize resilience engine."""
        self.defense_calculator = DefenseLevelCalculator()
        self.utilization_monitor = UtilizationMonitor()
        self.threshold_manager = ThresholdManager()

        # Initialize default thresholds
        self._setup_default_thresholds()

    def _setup_default_thresholds(self):
        """Setup default resilience thresholds."""
        # Utilization thresholds (from queuing theory)
        self.threshold_manager.create_static_threshold(
            name="utilization",
            warning_upper=0.80,
            critical_upper=0.95,
            upper_bound=1.0,
        )

        # N-1 failures
        self.threshold_manager.create_static_threshold(
            name="n1_failures",
            warning_upper=3,
            critical_upper=10,
        )

        # N-2 failures (any N-2 failure is serious)
        self.threshold_manager.create_static_threshold(
            name="n2_failures",
            warning_upper=1,
            critical_upper=5,
        )

        # Coverage gaps
        self.threshold_manager.create_static_threshold(
            name="coverage_gaps",
            warning_upper=2,
            critical_upper=5,
        )

        # Burnout cases
        self.threshold_manager.create_static_threshold(
            name="burnout_cases",
            warning_upper=2,
            critical_upper=5,
        )

        # Cascade risk
        self.threshold_manager.create_static_threshold(
            name="cascade_risk",
            warning_upper=0.25,
            critical_upper=0.50,
            upper_bound=1.0,
        )

    def assess_resilience(
        self,
        period_start: date,
        period_end: date,
        total_capacity: float,
        utilized_capacity: float,
        num_servers: int,
        n1_failures: int = 0,
        n2_failures: int = 0,
        coverage_gaps: int = 0,
        burnout_cases: int = 0,
        cascade_risk: float = 0.0,
        arrival_rate: Optional[float] = None,
        service_rate: Optional[float] = None,
    ) -> ResilienceStatus:
        """
        Assess overall resilience status.

        Args:
            period_start: Assessment period start
            period_end: Assessment period end
            total_capacity: Total available hours
            utilized_capacity: Scheduled hours
            num_servers: Number of residents/faculty
            n1_failures: Number of N-1 failure scenarios
            n2_failures: Number of N-2 failure scenarios
            coverage_gaps: Number of coverage gaps
            burnout_cases: Number of residents in burnout
            cascade_risk: Cascade failure probability (0-1)
            arrival_rate: Request arrival rate (optional)
            service_rate: Service rate per server (optional)

        Returns:
            ResilienceStatus with comprehensive assessment
        """
        # Calculate utilization
        utilization = self.utilization_monitor.calculate_snapshot(
            period_start=period_start,
            period_end=period_end,
            total_capacity=total_capacity,
            utilized_capacity=utilized_capacity,
            num_servers=num_servers,
            arrival_rate=arrival_rate,
            service_rate=service_rate,
        )

        # Calculate defense level
        defense_level = self.defense_calculator.calculate(
            utilization=utilization.utilization_ratio,
            n1_failures=n1_failures,
            n2_failures=n2_failures,
            coverage_gaps=coverage_gaps,
            burnout_cases=burnout_cases,
            cascade_risk=cascade_risk,
        )

        # Check threshold violations
        violations = []

        util_violation = self.threshold_manager.check_threshold(
            "utilization", utilization.utilization_ratio
        )
        if util_violation:
            violations.append(util_violation)

        n1_violation = self.threshold_manager.check_threshold("n1_failures", n1_failures)
        if n1_violation:
            violations.append(n1_violation)

        n2_violation = self.threshold_manager.check_threshold("n2_failures", n2_failures)
        if n2_violation:
            violations.append(n2_violation)

        gap_violation = self.threshold_manager.check_threshold("coverage_gaps", coverage_gaps)
        if gap_violation:
            violations.append(gap_violation)

        burnout_violation = self.threshold_manager.check_threshold("burnout_cases", burnout_cases)
        if burnout_violation:
            violations.append(burnout_violation)

        cascade_violation = self.threshold_manager.check_threshold("cascade_risk", cascade_risk)
        if cascade_violation:
            violations.append(cascade_violation)

        # Generate alerts
        alerts = self._generate_alerts(defense_level, violations)

        # Calculate overall risk score (0-1)
        risk_score = self._calculate_risk_score(defense_level, utilization, violations)

        # System is healthy if defense level is GREEN or YELLOW and no critical violations
        is_healthy = defense_level.level in [
            DefenseLevel.GREEN,
            DefenseLevel.YELLOW,
        ] and not any(v.severity == "critical" for v in violations)

        return ResilienceStatus(
            defense_level=defense_level,
            utilization=utilization,
            threshold_violations=violations,
            alerts=alerts,
            timestamp=datetime.now(),
            is_healthy=is_healthy,
            risk_score=risk_score,
        )

    def _generate_alerts(
        self,
        defense_level: DefenseLevelResult,
        violations: list[ThresholdViolation],
    ) -> list[str]:
        """Generate alert messages."""
        alerts = []

        # Defense level alerts
        if defense_level.level == DefenseLevel.BLACK:
            alerts.append("🚨 EMERGENCY: System in BLACK defense level - immediate action required")
        elif defense_level.level == DefenseLevel.RED:
            alerts.append("🔴 CRITICAL: System in RED defense level - urgent intervention needed")
        elif defense_level.level == DefenseLevel.ORANGE:
            alerts.append("🟠 WARNING: System in ORANGE defense level - degraded operations")
        elif defense_level.level == DefenseLevel.YELLOW:
            alerts.append("🟡 CAUTION: System in YELLOW defense level - early warning")

        # Threshold violation alerts
        for violation in violations:
            if violation.severity == "critical":
                alerts.append(f"🚨 CRITICAL: {violation.message}")
            elif violation.severity == "warning":
                alerts.append(f"⚠️ WARNING: {violation.message}")

        # Add recommendations from defense level
        for rec in defense_level.recommendations:
            alerts.append(f"💡 {rec}")

        return alerts

    def _calculate_risk_score(
        self,
        defense_level: DefenseLevelResult,
        utilization: UtilizationSnapshot,
        violations: list[ThresholdViolation],
    ) -> float:
        """
        Calculate overall risk score (0.0 - 1.0).

        Combines:
        - Defense level severity (0-4)
        - Utilization ratio
        - Number and severity of violations
        """
        # Defense level contribution (0-0.4)
        defense_score = defense_level.level.severity_score / 10.0  # 0-0.4

        # Utilization contribution (0-0.3)
        util_score = min(0.3, utilization.utilization_ratio * 0.3)

        # Violations contribution (0-0.3)
        critical_violations = sum(1 for v in violations if v.severity == "critical")
        warning_violations = sum(1 for v in violations if v.severity == "warning")
        violation_score = min(0.3, (critical_violations * 0.1 + warning_violations * 0.05))

        return min(1.0, defense_score + util_score + violation_score)

    def get_health_summary(self, status: ResilienceStatus) -> dict:
        """
        Get human-readable health summary.

        Returns:
            Dict with summary information
        """
        return {
            "status": "HEALTHY" if status.is_healthy else "DEGRADED",
            "defense_level": status.defense_level.level.value,
            "risk_score": f"{status.risk_score:.2%}",
            "utilization": f"{status.utilization.utilization_ratio:.1%}",
            "alerts_count": len(status.alerts),
            "critical_violations": sum(
                1 for v in status.threshold_violations if v.severity == "critical"
            ),
            "warning_violations": sum(
                1 for v in status.threshold_violations if v.severity == "warning"
            ),
            "timestamp": status.timestamp.isoformat(),
            "recommendations": status.defense_level.recommendations,
        }
