"""
Western Electric Rules for SPC.

Classic rules from semiconductor manufacturing (AT&T/Western Electric, 1956).
Detect out-of-control conditions in control charts.

Eight rules:
1. One point beyond 3σ
2. Two of three consecutive points beyond 2σ (same side)
3. Four of five consecutive points beyond 1σ (same side)
4. Eight consecutive points on same side of center line
5. Six consecutive points trending up or down
6. Fifteen consecutive points within 1σ (process too good - possible data manipulation)
7. Fourteen consecutive points alternating up/down
8. Eight consecutive points beyond 1σ (both sides)
"""

import logging
from dataclasses import dataclass
from typing import Optional

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class RuleViolation:
    """Western Electric rule violation."""

    rule_number: int
    rule_name: str
    description: str
    severity: str  # "critical", "warning", "info"
    points_involved: list[int]  # Indices of points involved in violation


class WesternElectricRules:
    """
    Western Electric Rules for control chart analysis.

    Detects patterns indicating out-of-control process.
    """

    def __init__(self, center_line: float, sigma: float):
        """
        Initialize rules checker.

        Args:
            center_line: Process mean/target
            sigma: Process standard deviation
        """
        self.center_line = center_line
        self.sigma = sigma

    def check_all_rules(self, data: list[float]) -> list[RuleViolation]:
        """
        Check all Western Electric rules.

        Args:
            data: Time-ordered data points

        Returns:
            List of RuleViolation objects
        """
        logger.info("Checking Western Electric rules for %d data points", len(data))
        violations = []

        # Rule 1: One point beyond 3σ
        v1 = self._rule_1_beyond_3sigma(data)
        if v1:
            logger.warning("Rule 1 violations detected: %d points beyond 3σ", len(v1))
            violations.extend(v1)

        # Rule 2: Two of three consecutive beyond 2σ
        v2 = self._rule_2_two_of_three_beyond_2sigma(data)
        if v2:
            logger.warning("Rule 2 violations detected: %d instances", len(v2))
            violations.extend(v2)

        # Rule 3: Four of five consecutive beyond 1σ
        v3 = self._rule_3_four_of_five_beyond_1sigma(data)
        if v3:
            violations.extend(v3)

        # Rule 4: Eight consecutive on same side
        v4 = self._rule_4_eight_same_side(data)
        if v4:
            violations.extend(v4)

        # Rule 5: Six consecutive trending
        v5 = self._rule_5_six_trending(data)
        if v5:
            violations.extend(v5)

        # Rule 6: Fifteen consecutive within 1σ
        v6 = self._rule_6_fifteen_within_1sigma(data)
        if v6:
            violations.extend(v6)

        # Rule 7: Fourteen alternating
        v7 = self._rule_7_fourteen_alternating(data)
        if v7:
            violations.extend(v7)

        # Rule 8: Eight beyond 1σ both sides
        v8 = self._rule_8_eight_beyond_1sigma(data)
        if v8:
            violations.extend(v8)

        logger.debug("Western Electric check complete: %d total violations found", len(violations))
        return violations

    def _rule_1_beyond_3sigma(self, data: list[float]) -> list[RuleViolation]:
        """Rule 1: One point beyond 3σ."""
        violations = []
        ucl = self.center_line + 3 * self.sigma
        lcl = self.center_line - 3 * self.sigma

        for i, value in enumerate(data):
            if value > ucl or value < lcl:
                violations.append(
                    RuleViolation(
                        rule_number=1,
                        rule_name="Beyond 3 Sigma",
                        description=f"Point {i} ({value:.2f}) beyond control limits [{lcl:.2f}, {ucl:.2f}]",
                        severity="critical",
                        points_involved=[i],
                    )
                )

        return violations

    def _rule_2_two_of_three_beyond_2sigma(
        self, data: list[float]
    ) -> list[RuleViolation]:
        """Rule 2: Two of three consecutive points beyond 2σ (same side)."""
        violations = []
        uwl = self.center_line + 2 * self.sigma
        lwl = self.center_line - 2 * self.sigma

        for i in range(len(data) - 2):
            window = data[i : i + 3]
            above_count = sum(1 for v in window if v > uwl)
            below_count = sum(1 for v in window if v < lwl)

            if above_count >= 2:
                violations.append(
                    RuleViolation(
                        rule_number=2,
                        rule_name="2 of 3 Beyond 2 Sigma",
                        description=f"Points {i}-{i + 2} have 2+ above +2σ ({uwl:.2f})",
                        severity="warning",
                        points_involved=list(range(i, i + 3)),
                    )
                )
            elif below_count >= 2:
                violations.append(
                    RuleViolation(
                        rule_number=2,
                        rule_name="2 of 3 Beyond 2 Sigma",
                        description=f"Points {i}-{i + 2} have 2+ below -2σ ({lwl:.2f})",
                        severity="warning",
                        points_involved=list(range(i, i + 3)),
                    )
                )

        return violations

    def _rule_3_four_of_five_beyond_1sigma(
        self, data: list[float]
    ) -> list[RuleViolation]:
        """Rule 3: Four of five consecutive points beyond 1σ (same side)."""
        violations = []

        for i in range(len(data) - 4):
            window = data[i : i + 5]
            above_count = sum(1 for v in window if v > self.center_line + self.sigma)
            below_count = sum(1 for v in window if v < self.center_line - self.sigma)

            if above_count >= 4:
                violations.append(
                    RuleViolation(
                        rule_number=3,
                        rule_name="4 of 5 Beyond 1 Sigma",
                        description=f"Points {i}-{i + 4} have 4+ above +1σ",
                        severity="warning",
                        points_involved=list(range(i, i + 5)),
                    )
                )
            elif below_count >= 4:
                violations.append(
                    RuleViolation(
                        rule_number=3,
                        rule_name="4 of 5 Beyond 1 Sigma",
                        description=f"Points {i}-{i + 4} have 4+ below -1σ",
                        severity="warning",
                        points_involved=list(range(i, i + 5)),
                    )
                )

        return violations

    def _rule_4_eight_same_side(self, data: list[float]) -> list[RuleViolation]:
        """Rule 4: Eight consecutive points on same side of center line."""
        violations = []

        for i in range(len(data) - 7):
            window = data[i : i + 8]
            all_above = all(v > self.center_line for v in window)
            all_below = all(v < self.center_line for v in window)

            if all_above or all_below:
                side = "above" if all_above else "below"
                violations.append(
                    RuleViolation(
                        rule_number=4,
                        rule_name="8 Consecutive Same Side",
                        description=f"Points {i}-{i + 7} all {side} center line",
                        severity="warning",
                        points_involved=list(range(i, i + 8)),
                    )
                )

        return violations

    def _rule_5_six_trending(self, data: list[float]) -> list[RuleViolation]:
        """Rule 5: Six consecutive points trending up or down."""
        violations = []

        for i in range(len(data) - 5):
            window = data[i : i + 6]
            is_increasing = all(window[j] < window[j + 1] for j in range(5))
            is_decreasing = all(window[j] > window[j + 1] for j in range(5))

            if is_increasing:
                violations.append(
                    RuleViolation(
                        rule_number=5,
                        rule_name="6 Consecutive Trending",
                        description=f"Points {i}-{i + 5} trending upward",
                        severity="warning",
                        points_involved=list(range(i, i + 6)),
                    )
                )
            elif is_decreasing:
                violations.append(
                    RuleViolation(
                        rule_number=5,
                        rule_name="6 Consecutive Trending",
                        description=f"Points {i}-{i + 5} trending downward",
                        severity="warning",
                        points_involved=list(range(i, i + 6)),
                    )
                )

        return violations

    def _rule_6_fifteen_within_1sigma(self, data: list[float]) -> list[RuleViolation]:
        """Rule 6: Fifteen consecutive points within 1σ (process suspiciously stable)."""
        violations = []
        upper = self.center_line + self.sigma
        lower = self.center_line - self.sigma

        for i in range(len(data) - 14):
            window = data[i : i + 15]
            all_within = all(lower <= v <= upper for v in window)

            if all_within:
                violations.append(
                    RuleViolation(
                        rule_number=6,
                        rule_name="15 Within 1 Sigma",
                        description=f"Points {i}-{i + 14} suspiciously stable (all within 1σ)",
                        severity="info",
                        points_involved=list(range(i, i + 15)),
                    )
                )

        return violations

    def _rule_7_fourteen_alternating(self, data: list[float]) -> list[RuleViolation]:
        """Rule 7: Fourteen consecutive points alternating up/down."""
        violations = []

        for i in range(len(data) - 13):
            window = data[i : i + 14]
            is_alternating = all(
                (window[j] < window[j + 1] and window[j + 1] > window[j + 2])
                or (window[j] > window[j + 1] and window[j + 1] < window[j + 2])
                for j in range(0, 12)
            )

            if is_alternating:
                violations.append(
                    RuleViolation(
                        rule_number=7,
                        rule_name="14 Alternating",
                        description=f"Points {i}-{i + 13} alternating up/down (systematic variation)",
                        severity="info",
                        points_involved=list(range(i, i + 14)),
                    )
                )

        return violations

    def _rule_8_eight_beyond_1sigma(self, data: list[float]) -> list[RuleViolation]:
        """Rule 8: Eight consecutive points beyond 1σ (both sides allowed)."""
        violations = []
        upper = self.center_line + self.sigma
        lower = self.center_line - self.sigma

        for i in range(len(data) - 7):
            window = data[i : i + 8]
            all_beyond = all(v > upper or v < lower for v in window)

            if all_beyond:
                violations.append(
                    RuleViolation(
                        rule_number=8,
                        rule_name="8 Beyond 1 Sigma",
                        description=f"Points {i}-{i + 7} all beyond ±1σ (excessive variation)",
                        severity="warning",
                        points_involved=list(range(i, i + 8)),
                    )
                )

        return violations

    def get_rule_summary(self, violations: list[RuleViolation]) -> dict:
        """
        Get summary of rule violations.

        Args:
            violations: List of violations

        Returns:
            Dict with summary statistics
        """
        if not violations:
            return {
                "total_violations": 0,
                "critical": 0,
                "warning": 0,
                "info": 0,
                "rules_violated": [],
                "status": "in_control",
            }

        critical = sum(1 for v in violations if v.severity == "critical")
        warning = sum(1 for v in violations if v.severity == "warning")
        info = sum(1 for v in violations if v.severity == "info")

        rules_violated = sorted(set(v.rule_number for v in violations))

        if critical > 0:
            status = "out_of_control"
        elif warning > 0:
            status = "warning"
        else:
            status = "stable"

        return {
            "total_violations": len(violations),
            "critical": critical,
            "warning": warning,
            "info": info,
            "rules_violated": rules_violated,
            "status": status,
            "most_frequent_rule": (
                max(
                    rules_violated,
                    key=lambda r: sum(1 for v in violations if v.rule_number == r),
                )
                if rules_violated
                else None
            ),
        }
