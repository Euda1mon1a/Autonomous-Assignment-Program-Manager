"""
Defense Level Calculator.

Defense in Depth - Five-tier safety system from cybersecurity and power grid:
- GREEN: Normal operations (utilization < 80%)
- YELLOW: Early warning (utilization 80-90%, minor degradation)
- ORANGE: Degraded (utilization 90-95%, coverage gaps appearing)
- RED: Critical (utilization > 95%, N-1 failures imminent)
- BLACK: Emergency (cascade failures, emergency protocols active)

Based on power grid NERC standards and cybersecurity defense-in-depth.
"""

import logging
from dataclasses import dataclass
from datetime import date, datetime
from enum import Enum
from typing import Optional

import numpy as np

logger = logging.getLogger(__name__)


class DefenseLevel(str, Enum):
    """Defense level enumeration."""

    GREEN = "GREEN"
    YELLOW = "YELLOW"
    ORANGE = "ORANGE"
    RED = "RED"
    BLACK = "BLACK"

    def __lt__(self, other):
        """Allow comparison of defense levels."""
        if not isinstance(other, DefenseLevel):
            return NotImplemented
        order = [
            DefenseLevel.GREEN,
            DefenseLevel.YELLOW,
            DefenseLevel.ORANGE,
            DefenseLevel.RED,
            DefenseLevel.BLACK,
        ]
        return order.index(self) < order.index(other)

    def __le__(self, other):
        """Allow comparison of defense levels."""
        return self == other or self < other

    @property
    def severity_score(self) -> int:
        """Get numeric severity score (0-4)."""
        return {
            DefenseLevel.GREEN: 0,
            DefenseLevel.YELLOW: 1,
            DefenseLevel.ORANGE: 2,
            DefenseLevel.RED: 3,
            DefenseLevel.BLACK: 4,
        }[self]


@dataclass
class DefenseMetrics:
    """Defense level calculation metrics."""

    utilization: float  # Current utilization ratio (0.0-1.0+)
    n1_failures: int  # Number of N-1 failure scenarios
    n2_failures: int  # Number of N-2 failure scenarios
    coverage_gaps: int  # Number of coverage gaps
    burnout_cases: int  # Number of residents in burnout state
    cascade_risk: float  # Cascade failure risk (0.0-1.0)
    recovery_time: float  # Estimated recovery time (hours)


@dataclass
class DefenseLevelResult:
    """Defense level calculation result."""

    level: DefenseLevel
    metrics: DefenseMetrics
    rationale: str
    timestamp: datetime
    recommendations: list[str]


class DefenseLevelCalculator:
    """
    Calculate defense level based on multiple resilience metrics.

    Uses weighted scoring across:
    - Utilization (queuing theory)
    - N-1/N-2 contingency (power grid)
    - Coverage gaps (operational)
    - Burnout epidemiology (SIR model)
    - Cascade risk (network analysis)
    """

    # Utilization thresholds from queuing theory (M/M/c queue)
    UTILIZATION_GREEN = 0.80  # Below this = green
    UTILIZATION_YELLOW = 0.90  # 80-90% = yellow
    UTILIZATION_ORANGE = 0.95  # 90-95% = orange
    UTILIZATION_RED = 0.98  # 95-98% = red
    # Above 98% = black (queue explosion)

    # N-1/N-2 thresholds
    N1_YELLOW_THRESHOLD = 3  # > 3 N-1 failures = yellow
    N1_ORANGE_THRESHOLD = 10  # > 10 N-1 failures = orange
    N1_RED_THRESHOLD = 25  # > 25 N-1 failures = red

    N2_ORANGE_THRESHOLD = 5  # Any N-2 failures = orange+
    N2_RED_THRESHOLD = 15  # > 15 N-2 failures = red

    # Cascade risk thresholds
    CASCADE_YELLOW = 0.10  # 10% cascade risk
    CASCADE_ORANGE = 0.25  # 25% cascade risk
    CASCADE_RED = 0.50  # 50% cascade risk

    def calculate(
        self,
        utilization: float,
        n1_failures: int = 0,
        n2_failures: int = 0,
        coverage_gaps: int = 0,
        burnout_cases: int = 0,
        cascade_risk: float = 0.0,
        recovery_time: float = 0.0,
    ) -> DefenseLevelResult:
        """
        Calculate defense level from resilience metrics.

        Args:
            utilization: Current utilization ratio (0.0-1.0+)
            n1_failures: Number of N-1 failure scenarios
            n2_failures: Number of N-2 failure scenarios
            coverage_gaps: Number of coverage gaps
            burnout_cases: Number of residents in burnout state
            cascade_risk: Cascade failure probability (0.0-1.0)
            recovery_time: Estimated recovery time in hours

        Returns:
            DefenseLevelResult with level, metrics, and recommendations
        """
        logger.info(
            "Calculating defense level: utilization=%.2f, n1=%d, n2=%d, cascade=%.2f",
            utilization,
            n1_failures,
            n2_failures,
            cascade_risk,
        )
        metrics = DefenseMetrics(
            utilization=utilization,
            n1_failures=n1_failures,
            n2_failures=n2_failures,
            coverage_gaps=coverage_gaps,
            burnout_cases=burnout_cases,
            cascade_risk=cascade_risk,
            recovery_time=recovery_time,
        )

        # Calculate scores for each dimension
        util_score = self._score_utilization(utilization)
        n1_score = self._score_n1_failures(n1_failures)
        n2_score = self._score_n2_failures(n2_failures)
        cascade_score = self._score_cascade_risk(cascade_risk)
        gap_score = self._score_coverage_gaps(coverage_gaps)
        burnout_score = self._score_burnout(burnout_cases)

        # Weighted combination (utilization and N-2 are most critical)
        weights = {
            "utilization": 0.30,
            "n1": 0.15,
            "n2": 0.25,
            "cascade": 0.15,
            "gaps": 0.10,
            "burnout": 0.05,
        }

        combined_score = (
            util_score * weights["utilization"]
            + n1_score * weights["n1"]
            + n2_score * weights["n2"]
            + cascade_score * weights["cascade"]
            + gap_score * weights["gaps"]
            + burnout_score * weights["burnout"]
        )

        # Map combined score to defense level
        level = self._score_to_level(combined_score)

        logger.debug("Defense level determined: %s (score=%.2f)", level, combined_score)
        if level in (DefenseLevel.RED, DefenseLevel.BLACK):
            logger.error(
                "CRITICAL: Defense level %s - immediate action required", level
            )
        elif level == DefenseLevel.ORANGE:
            logger.warning("Defense level ORANGE - degraded state detected")

        # Generate rationale and recommendations
        rationale = self._generate_rationale(
            level,
            util_score,
            n1_score,
            n2_score,
            cascade_score,
            gap_score,
            burnout_score,
        )
        recommendations = self._generate_recommendations(level, metrics)

        return DefenseLevelResult(
            level=level,
            metrics=metrics,
            rationale=rationale,
            timestamp=datetime.now(),
            recommendations=recommendations,
        )

    def _score_utilization(self, utilization: float) -> float:
        """Score utilization (0.0-4.0 scale)."""
        if utilization < self.UTILIZATION_GREEN:
            return 0.0
        elif utilization < self.UTILIZATION_YELLOW:
            # Linear interpolation GREEN -> YELLOW
            return (
                1.0
                * (utilization - self.UTILIZATION_GREEN)
                / (self.UTILIZATION_YELLOW - self.UTILIZATION_GREEN)
            )
        elif utilization < self.UTILIZATION_ORANGE:
            return 1.0 + 1.0 * (utilization - self.UTILIZATION_YELLOW) / (
                self.UTILIZATION_ORANGE - self.UTILIZATION_YELLOW
            )
        elif utilization < self.UTILIZATION_RED:
            return 2.0 + 1.0 * (utilization - self.UTILIZATION_ORANGE) / (
                self.UTILIZATION_RED - self.UTILIZATION_ORANGE
            )
        else:
            # Exponential growth beyond RED threshold
            excess = utilization - self.UTILIZATION_RED
            return 3.0 + min(1.0, excess / 0.10)  # Cap at 4.0

    def _score_n1_failures(self, n1_failures: int) -> float:
        """Score N-1 failures (0.0-4.0 scale)."""
        if n1_failures == 0:
            return 0.0
        elif n1_failures <= self.N1_YELLOW_THRESHOLD:
            return 1.0 * n1_failures / self.N1_YELLOW_THRESHOLD
        elif n1_failures <= self.N1_ORANGE_THRESHOLD:
            return 1.0 + 1.0 * (n1_failures - self.N1_YELLOW_THRESHOLD) / (
                self.N1_ORANGE_THRESHOLD - self.N1_YELLOW_THRESHOLD
            )
        elif n1_failures <= self.N1_RED_THRESHOLD:
            return 2.0 + 1.0 * (n1_failures - self.N1_ORANGE_THRESHOLD) / (
                self.N1_RED_THRESHOLD - self.N1_ORANGE_THRESHOLD
            )
        else:
            return min(4.0, 3.0 + (n1_failures - self.N1_RED_THRESHOLD) / 25.0)

    def _score_n2_failures(self, n2_failures: int) -> float:
        """Score N-2 failures (0.0-4.0 scale)."""
        if n2_failures == 0:
            return 0.0
        elif n2_failures < self.N2_ORANGE_THRESHOLD:
            # Any N-2 failure is at least YELLOW
            return 1.0 + 1.0 * n2_failures / self.N2_ORANGE_THRESHOLD
        elif n2_failures <= self.N2_RED_THRESHOLD:
            return 2.0 + 1.0 * (n2_failures - self.N2_ORANGE_THRESHOLD) / (
                self.N2_RED_THRESHOLD - self.N2_ORANGE_THRESHOLD
            )
        else:
            return min(4.0, 3.0 + (n2_failures - self.N2_RED_THRESHOLD) / 15.0)

    def _score_cascade_risk(self, cascade_risk: float) -> float:
        """Score cascade failure risk (0.0-4.0 scale)."""
        if cascade_risk < self.CASCADE_YELLOW:
            return 1.0 * cascade_risk / self.CASCADE_YELLOW
        elif cascade_risk < self.CASCADE_ORANGE:
            return 1.0 + 1.0 * (cascade_risk - self.CASCADE_YELLOW) / (
                self.CASCADE_ORANGE - self.CASCADE_YELLOW
            )
        elif cascade_risk < self.CASCADE_RED:
            return 2.0 + 1.0 * (cascade_risk - self.CASCADE_ORANGE) / (
                self.CASCADE_RED - self.CASCADE_ORANGE
            )
        else:
            return min(4.0, 3.0 + (cascade_risk - self.CASCADE_RED) / 0.50)

    def _score_coverage_gaps(self, gaps: int) -> float:
        """Score coverage gaps (0.0-4.0 scale)."""
        # Coverage gaps are critical
        if gaps == 0:
            return 0.0
        elif gaps <= 2:
            return 1.0 + 0.5 * gaps  # 1-2 gaps = YELLOW
        elif gaps <= 5:
            return 2.0 + 0.33 * (gaps - 2)  # 3-5 gaps = ORANGE
        elif gaps <= 10:
            return 3.0 + 0.20 * (gaps - 5)  # 6-10 gaps = RED
        else:
            return 4.0  # > 10 gaps = BLACK

    def _score_burnout(self, burnout_cases: int) -> float:
        """Score burnout cases (0.0-4.0 scale)."""
        if burnout_cases == 0:
            return 0.0
        elif burnout_cases <= 2:
            return 1.0 * burnout_cases / 2  # 1-2 cases = GREEN-YELLOW
        elif burnout_cases <= 5:
            return 1.0 + 1.0 * (burnout_cases - 2) / 3  # 3-5 = YELLOW-ORANGE
        elif burnout_cases <= 10:
            return 2.0 + 1.0 * (burnout_cases - 5) / 5  # 6-10 = ORANGE-RED
        else:
            return min(4.0, 3.0 + (burnout_cases - 10) / 10.0)

    def _score_to_level(self, score: float) -> DefenseLevel:
        """Map combined score to defense level."""
        if score < 1.0:
            return DefenseLevel.GREEN
        elif score < 2.0:
            return DefenseLevel.YELLOW
        elif score < 3.0:
            return DefenseLevel.ORANGE
        elif score < 3.5:
            return DefenseLevel.RED
        else:
            return DefenseLevel.BLACK

    def _generate_rationale(
        self,
        level: DefenseLevel,
        util_score: float,
        n1_score: float,
        n2_score: float,
        cascade_score: float,
        gap_score: float,
        burnout_score: float,
    ) -> str:
        """Generate human-readable rationale for defense level."""
        contributors = []

        if util_score >= 2.0:
            contributors.append(f"high utilization (score: {util_score:.1f})")
        if n1_score >= 2.0:
            contributors.append(f"N-1 vulnerabilities (score: {n1_score:.1f})")
        if n2_score >= 2.0:
            contributors.append(f"N-2 contingency failures (score: {n2_score:.1f})")
        if cascade_score >= 2.0:
            contributors.append(f"cascade risk (score: {cascade_score:.1f})")
        if gap_score >= 2.0:
            contributors.append(f"coverage gaps (score: {gap_score:.1f})")
        if burnout_score >= 2.0:
            contributors.append(f"burnout cases (score: {burnout_score:.1f})")

        if contributors:
            reason = f"Defense level {level.value} due to: " + ", ".join(contributors)
        else:
            reason = f"Defense level {level.value} - system operating normally"

        return reason

    def _generate_recommendations(
        self, level: DefenseLevel, metrics: DefenseMetrics
    ) -> list[str]:
        """Generate actionable recommendations based on defense level."""
        recs = []

        if level == DefenseLevel.GREEN:
            recs.append("System operating normally - maintain current state")
            if metrics.utilization > 0.70:
                recs.append("Monitor utilization - approaching 80% threshold")

        elif level == DefenseLevel.YELLOW:
            recs.append("Early warning - increase monitoring frequency")
            if metrics.utilization > self.UTILIZATION_GREEN:
                recs.append("Reduce non-essential assignments to lower utilization")
            if metrics.n1_failures > 0:
                recs.append(f"Address {metrics.n1_failures} N-1 vulnerabilities")
            recs.append("Prepare contingency plans")

        elif level == DefenseLevel.ORANGE:
            recs.append("System degraded - activate contingency protocols")
            if metrics.utilization > self.UTILIZATION_YELLOW:
                recs.append("URGENT: Reduce utilization below 90%")
            if metrics.coverage_gaps > 0:
                recs.append(f"Fill {metrics.coverage_gaps} coverage gaps immediately")
            if metrics.n2_failures > 0:
                recs.append(
                    f"Critical: {metrics.n2_failures} N-2 failure scenarios detected"
                )
            recs.append("Consider activating backup residents")

        elif level == DefenseLevel.RED:
            recs.append("CRITICAL - Implement emergency protocols")
            recs.append("Activate all backup coverage immediately")
            if metrics.cascade_risk > self.CASCADE_ORANGE:
                recs.append("High cascade risk - implement blast radius isolation")
            recs.append("Initiate sacrifice hierarchy (shed non-critical assignments)")
            recs.append("Notify program leadership and ACGME if needed")

        elif level == DefenseLevel.BLACK:
            recs.append("EMERGENCY - System failure imminent or in progress")
            recs.append("Execute emergency response plan")
            recs.append("Activate static stability fallbacks")
            recs.append("Request external assistance (GME office, other programs)")
            recs.append("Document all actions for ACGME compliance review")

        return recs
