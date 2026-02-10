"""Tests for Western Electric Rules (pure logic, no DB)."""

import pytest

from app.resilience.spc.western_electric import (
    RuleViolation,
    WesternElectricRules,
)


# ── RuleViolation dataclass ────────────────────────────────────────────


class TestRuleViolation:
    def test_creation(self):
        v = RuleViolation(
            rule_number=1,
            rule_name="Beyond 3 Sigma",
            description="Point 5 beyond limits",
            severity="critical",
            points_involved=[5],
        )
        assert v.rule_number == 1
        assert v.severity == "critical"
        assert v.points_involved == [5]


# ── WesternElectricRules init ──────────────────────────────────────────


class TestWesternElectricRulesInit:
    def test_init(self):
        rules = WesternElectricRules(center_line=10.0, sigma=2.0)
        assert rules.center_line == 10.0
        assert rules.sigma == 2.0


# ── Rule 1: One point beyond 3σ ────────────────────────────────────────


class TestRule1:
    def test_no_violation_in_control(self):
        rules = WesternElectricRules(center_line=10.0, sigma=1.0)
        data = [10.0, 11.0, 9.0, 10.5, 9.5]
        violations = rules._rule_1_beyond_3sigma(data)
        assert len(violations) == 0

    def test_above_3sigma(self):
        rules = WesternElectricRules(center_line=10.0, sigma=1.0)
        data = [10.0, 14.0]  # 14 > 13 (10 + 3*1)
        violations = rules._rule_1_beyond_3sigma(data)
        assert len(violations) == 1
        assert violations[0].rule_number == 1
        assert violations[0].severity == "critical"

    def test_below_3sigma(self):
        rules = WesternElectricRules(center_line=10.0, sigma=1.0)
        data = [10.0, 6.0]  # 6 < 7 (10 - 3*1)
        violations = rules._rule_1_beyond_3sigma(data)
        assert len(violations) == 1

    def test_exactly_at_3sigma(self):
        """Point exactly at 3σ is NOT a violation."""
        rules = WesternElectricRules(center_line=10.0, sigma=1.0)
        data = [13.0]  # Exactly at UCL
        violations = rules._rule_1_beyond_3sigma(data)
        assert len(violations) == 0

    def test_multiple_violations(self):
        rules = WesternElectricRules(center_line=10.0, sigma=1.0)
        data = [15.0, 10.0, 5.0]  # Two violations
        violations = rules._rule_1_beyond_3sigma(data)
        assert len(violations) == 2


# ── Rule 2: Two of three beyond 2σ ─────────────────────────────────────


class TestRule2:
    def test_no_violation(self):
        rules = WesternElectricRules(center_line=10.0, sigma=1.0)
        data = [10.0, 11.0, 10.5]
        violations = rules._rule_2_two_of_three_beyond_2sigma(data)
        assert len(violations) == 0

    def test_two_above_2sigma(self):
        rules = WesternElectricRules(center_line=10.0, sigma=1.0)
        # Need 2 of 3 above 12.0 (10 + 2*1)
        data = [12.5, 10.0, 12.5]
        violations = rules._rule_2_two_of_three_beyond_2sigma(data)
        assert len(violations) == 1
        assert violations[0].rule_number == 2

    def test_two_below_2sigma(self):
        rules = WesternElectricRules(center_line=10.0, sigma=1.0)
        data = [7.0, 10.0, 7.0]  # 2 below 8.0
        violations = rules._rule_2_two_of_three_beyond_2sigma(data)
        assert len(violations) == 1

    def test_mixed_sides_no_violation(self):
        """One above and one below don't trigger (must be same side)."""
        rules = WesternElectricRules(center_line=10.0, sigma=1.0)
        data = [12.5, 10.0, 7.0]
        violations = rules._rule_2_two_of_three_beyond_2sigma(data)
        assert len(violations) == 0

    def test_insufficient_data(self):
        rules = WesternElectricRules(center_line=10.0, sigma=1.0)
        violations = rules._rule_2_two_of_three_beyond_2sigma([10.0, 12.5])
        assert len(violations) == 0


# ── Rule 3: Four of five beyond 1σ ─────────────────────────────────────


class TestRule3:
    def test_no_violation(self):
        rules = WesternElectricRules(center_line=10.0, sigma=1.0)
        data = [10.0, 10.5, 11.0, 10.5, 10.0]
        violations = rules._rule_3_four_of_five_beyond_1sigma(data)
        assert len(violations) == 0

    def test_four_above_1sigma(self):
        rules = WesternElectricRules(center_line=10.0, sigma=1.0)
        # 4 of 5 above 11.0 (10 + 1*1)
        data = [11.5, 11.5, 10.0, 11.5, 11.5]
        violations = rules._rule_3_four_of_five_beyond_1sigma(data)
        assert len(violations) == 1
        assert violations[0].rule_number == 3

    def test_four_below_1sigma(self):
        rules = WesternElectricRules(center_line=10.0, sigma=1.0)
        data = [8.5, 8.5, 10.0, 8.5, 8.5]
        violations = rules._rule_3_four_of_five_beyond_1sigma(data)
        assert len(violations) == 1


# ── Rule 4: Eight consecutive same side ────────────────────────────────


class TestRule4:
    def test_no_violation(self):
        rules = WesternElectricRules(center_line=10.0, sigma=1.0)
        data = [11.0, 9.0, 11.0, 9.0, 11.0, 9.0, 11.0, 9.0]
        violations = rules._rule_4_eight_same_side(data)
        assert len(violations) == 0

    def test_eight_above(self):
        rules = WesternElectricRules(center_line=10.0, sigma=1.0)
        data = [10.5, 10.5, 10.5, 10.5, 10.5, 10.5, 10.5, 10.5]
        violations = rules._rule_4_eight_same_side(data)
        assert len(violations) == 1
        assert violations[0].rule_number == 4

    def test_eight_below(self):
        rules = WesternElectricRules(center_line=10.0, sigma=1.0)
        data = [9.5, 9.5, 9.5, 9.5, 9.5, 9.5, 9.5, 9.5]
        violations = rules._rule_4_eight_same_side(data)
        assert len(violations) == 1

    def test_exactly_on_center_no_violation(self):
        """Points exactly on center line don't count (not above or below)."""
        rules = WesternElectricRules(center_line=10.0, sigma=1.0)
        data = [10.0, 10.5, 10.5, 10.5, 10.5, 10.5, 10.5, 10.5]
        violations = rules._rule_4_eight_same_side(data)
        # First point is exactly on center line, breaks the run
        assert len(violations) == 0


# ── Rule 5: Six consecutive trending ───────────────────────────────────


class TestRule5:
    def test_no_trend(self):
        rules = WesternElectricRules(center_line=10.0, sigma=1.0)
        data = [10.0, 10.0, 10.0, 10.0, 10.0, 10.0]
        violations = rules._rule_5_six_trending(data)
        assert len(violations) == 0

    def test_increasing_trend(self):
        rules = WesternElectricRules(center_line=10.0, sigma=1.0)
        data = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0]
        violations = rules._rule_5_six_trending(data)
        assert len(violations) == 1
        assert violations[0].rule_number == 5

    def test_decreasing_trend(self):
        rules = WesternElectricRules(center_line=10.0, sigma=1.0)
        data = [6.0, 5.0, 4.0, 3.0, 2.0, 1.0]
        violations = rules._rule_5_six_trending(data)
        assert len(violations) == 1

    def test_five_not_enough(self):
        rules = WesternElectricRules(center_line=10.0, sigma=1.0)
        data = [1.0, 2.0, 3.0, 4.0, 5.0]
        violations = rules._rule_5_six_trending(data)
        assert len(violations) == 0


# ── Rule 6: Fifteen within 1σ ──────────────────────────────────────────


class TestRule6:
    def test_not_enough_points(self):
        rules = WesternElectricRules(center_line=10.0, sigma=1.0)
        data = [10.0] * 14
        violations = rules._rule_6_fifteen_within_1sigma(data)
        assert len(violations) == 0

    def test_fifteen_within_1sigma(self):
        rules = WesternElectricRules(center_line=10.0, sigma=1.0)
        data = [10.0] * 15  # All at center, well within 1σ
        violations = rules._rule_6_fifteen_within_1sigma(data)
        assert len(violations) == 1
        assert violations[0].rule_number == 6
        assert violations[0].severity == "info"

    def test_one_outlier_breaks_pattern(self):
        rules = WesternElectricRules(center_line=10.0, sigma=1.0)
        data = [10.0] * 14 + [12.0]  # Last point beyond 1σ
        violations = rules._rule_6_fifteen_within_1sigma(data)
        assert len(violations) == 0


# ── Rule 7: Fourteen alternating ───────────────────────────────────────


class TestRule7:
    def test_not_enough_points(self):
        rules = WesternElectricRules(center_line=10.0, sigma=1.0)
        data = [10.0, 11.0] * 6  # 12 points
        violations = rules._rule_7_fourteen_alternating(data)
        assert len(violations) == 0

    def test_alternating_pattern(self):
        rules = WesternElectricRules(center_line=10.0, sigma=1.0)
        # Alternating up/down for 14 points
        data = [
            8.0,
            12.0,
            8.0,
            12.0,
            8.0,
            12.0,
            8.0,
            12.0,
            8.0,
            12.0,
            8.0,
            12.0,
            8.0,
            12.0,
        ]
        violations = rules._rule_7_fourteen_alternating(data)
        assert len(violations) == 1
        assert violations[0].rule_number == 7
        assert violations[0].severity == "info"

    def test_non_alternating(self):
        rules = WesternElectricRules(center_line=10.0, sigma=1.0)
        data = [
            10.0,
            10.0,
            10.0,
            10.0,
            10.0,
            10.0,
            10.0,
            10.0,
            10.0,
            10.0,
            10.0,
            10.0,
            10.0,
            10.0,
        ]
        violations = rules._rule_7_fourteen_alternating(data)
        assert len(violations) == 0


# ── Rule 8: Eight beyond 1σ (both sides) ──────────────────────────────


class TestRule8:
    def test_no_violation(self):
        rules = WesternElectricRules(center_line=10.0, sigma=1.0)
        data = [10.0, 10.0, 10.0, 10.0, 10.0, 10.0, 10.0, 10.0]
        violations = rules._rule_8_eight_beyond_1sigma(data)
        assert len(violations) == 0

    def test_eight_beyond_both_sides(self):
        rules = WesternElectricRules(center_line=10.0, sigma=1.0)
        # All beyond 1σ: some above 11, some below 9
        data = [12.0, 8.0, 12.0, 8.0, 12.0, 8.0, 12.0, 8.0]
        violations = rules._rule_8_eight_beyond_1sigma(data)
        assert len(violations) == 1
        assert violations[0].rule_number == 8

    def test_one_within_breaks_pattern(self):
        rules = WesternElectricRules(center_line=10.0, sigma=1.0)
        data = [12.0, 8.0, 12.0, 10.0, 12.0, 8.0, 12.0, 8.0]
        violations = rules._rule_8_eight_beyond_1sigma(data)
        assert len(violations) == 0


# ── check_all_rules ───────────────────────────────────────────────────


class TestCheckAllRules:
    def test_clean_data_no_violations(self):
        rules = WesternElectricRules(center_line=10.0, sigma=1.0)
        data = [10.0, 10.5, 9.5, 10.2, 9.8]
        violations = rules.check_all_rules(data)
        assert len(violations) == 0

    def test_rule_1_detected(self):
        rules = WesternElectricRules(center_line=10.0, sigma=1.0)
        data = [10.0, 10.0, 10.0, 10.0, 15.0]  # One beyond 3σ
        violations = rules.check_all_rules(data)
        rule_numbers = [v.rule_number for v in violations]
        assert 1 in rule_numbers

    def test_returns_list_of_violations(self):
        rules = WesternElectricRules(center_line=10.0, sigma=1.0)
        data = [15.0]
        violations = rules.check_all_rules(data)
        assert all(isinstance(v, RuleViolation) for v in violations)

    def test_empty_data(self):
        rules = WesternElectricRules(center_line=10.0, sigma=1.0)
        violations = rules.check_all_rules([])
        assert len(violations) == 0


# ── get_rule_summary ──────────────────────────────────────────────────


class TestGetRuleSummary:
    def test_no_violations(self):
        rules = WesternElectricRules(center_line=10.0, sigma=1.0)
        summary = rules.get_rule_summary([])
        assert summary["total_violations"] == 0
        assert summary["status"] == "in_control"
        assert summary["rules_violated"] == []

    def test_critical_violation(self):
        rules = WesternElectricRules(center_line=10.0, sigma=1.0)
        violations = [
            RuleViolation(
                rule_number=1,
                rule_name="Beyond 3 Sigma",
                description="test",
                severity="critical",
                points_involved=[0],
            )
        ]
        summary = rules.get_rule_summary(violations)
        assert summary["critical"] == 1
        assert summary["status"] == "out_of_control"

    def test_warning_status(self):
        rules = WesternElectricRules(center_line=10.0, sigma=1.0)
        violations = [
            RuleViolation(
                rule_number=2,
                rule_name="Test",
                description="test",
                severity="warning",
                points_involved=[0],
            )
        ]
        summary = rules.get_rule_summary(violations)
        assert summary["status"] == "warning"

    def test_info_only_stable(self):
        rules = WesternElectricRules(center_line=10.0, sigma=1.0)
        violations = [
            RuleViolation(
                rule_number=6,
                rule_name="Test",
                description="test",
                severity="info",
                points_involved=[0],
            )
        ]
        summary = rules.get_rule_summary(violations)
        assert summary["status"] == "stable"

    def test_rules_violated_sorted(self):
        rules = WesternElectricRules(center_line=10.0, sigma=1.0)
        violations = [
            RuleViolation(3, "Test", "test", "warning", [0]),
            RuleViolation(1, "Test", "test", "critical", [0]),
        ]
        summary = rules.get_rule_summary(violations)
        assert summary["rules_violated"] == [1, 3]

    def test_most_frequent_rule(self):
        rules = WesternElectricRules(center_line=10.0, sigma=1.0)
        violations = [
            RuleViolation(1, "Test", "test", "critical", [0]),
            RuleViolation(2, "Test", "test", "warning", [0]),
            RuleViolation(2, "Test", "test", "warning", [1]),
        ]
        summary = rules.get_rule_summary(violations)
        assert summary["most_frequent_rule"] == 2

    def test_has_all_keys(self):
        rules = WesternElectricRules(center_line=10.0, sigma=1.0)
        violations = [RuleViolation(1, "Test", "test", "critical", [0])]
        summary = rules.get_rule_summary(violations)
        expected_keys = {
            "total_violations",
            "critical",
            "warning",
            "info",
            "rules_violated",
            "status",
            "most_frequent_rule",
        }
        assert expected_keys == set(summary.keys())
