"""Tests for recovery planner (pure logic, no DB)."""

import pytest

from app.resilience.engine.defense_level_calculator import DefenseLevel
from app.resilience.engine.recovery_planner import (
    RecoveryAction,
    RecoveryPlan,
    RecoveryPlanner,
    RecoveryStep,
)


# -- RecoveryAction enum ------------------------------------------------------


class TestRecoveryAction:
    def test_values(self):
        assert RecoveryAction.REDUCE_LOAD == "reduce_load"
        assert RecoveryAction.ADD_CAPACITY == "add_capacity"
        assert RecoveryAction.ACTIVATE_BACKUP == "activate_backup"
        assert RecoveryAction.REDISTRIBUTE_WORK == "redistribute_work"
        assert RecoveryAction.IMPLEMENT_RESTRICTIONS == "implement_restrictions"
        assert RecoveryAction.EMERGENCY_PROTOCOL == "emergency_protocol"

    def test_member_count(self):
        assert len(RecoveryAction) == 6

    def test_is_string_enum(self):
        assert isinstance(RecoveryAction.REDUCE_LOAD, str)


# -- RecoveryStep dataclass ---------------------------------------------------


class TestRecoveryStep:
    def test_creation(self):
        step = RecoveryStep(
            action=RecoveryAction.REDUCE_LOAD,
            priority=2,
            description="Reduce workload",
            estimated_time_hours=4.0,
            expected_impact="Lower utilization",
            prerequisites=["Backup active"],
            success_criteria="Utilization < 85%",
        )
        assert step.action == RecoveryAction.REDUCE_LOAD
        assert step.priority == 2
        assert step.estimated_time_hours == 4.0
        assert step.prerequisites == ["Backup active"]


# -- RecoveryPlan dataclass ---------------------------------------------------


class TestRecoveryPlan:
    def test_creation(self):
        plan = RecoveryPlan(
            current_defense_level=DefenseLevel.RED,
            target_defense_level=DefenseLevel.GREEN,
            steps=[],
            estimated_total_time=0.0,
            success_probability=0.5,
            contingency_actions=["Escalate"],
        )
        assert plan.current_defense_level == DefenseLevel.RED
        assert plan.target_defense_level == DefenseLevel.GREEN
        assert plan.success_probability == 0.5


# -- RecoveryPlanner.plan_recovery (GREEN) ------------------------------------


class TestPlanRecoveryGreen:
    def test_green_no_issues(self):
        planner = RecoveryPlanner()
        plan = planner.plan_recovery(
            DefenseLevel.GREEN,
            0.70,
            n1_failures=0,
            n2_failures=0,
            coverage_gaps=0,
            burnout_cases=0,
        )
        assert plan.current_defense_level == DefenseLevel.GREEN
        assert plan.target_defense_level == DefenseLevel.GREEN
        assert plan.steps == []
        assert plan.estimated_total_time == 0.0


# -- RecoveryPlanner.plan_recovery (YELLOW) -----------------------------------


class TestPlanRecoveryYellow:
    def test_yellow_level_steps(self):
        planner = RecoveryPlanner()
        plan = planner.plan_recovery(
            DefenseLevel.YELLOW,
            0.80,
            n1_failures=0,
            n2_failures=0,
            coverage_gaps=0,
            burnout_cases=0,
        )
        assert len(plan.steps) >= 1
        actions = [s.action for s in plan.steps]
        assert RecoveryAction.REDISTRIBUTE_WORK in actions


# -- RecoveryPlanner.plan_recovery (ORANGE) -----------------------------------


class TestPlanRecoveryOrange:
    def test_orange_level_steps(self):
        planner = RecoveryPlanner()
        plan = planner.plan_recovery(
            DefenseLevel.ORANGE,
            0.85,
            n1_failures=0,
            n2_failures=0,
            coverage_gaps=0,
            burnout_cases=0,
        )
        assert len(plan.steps) >= 2
        actions = [s.action for s in plan.steps]
        assert RecoveryAction.REDISTRIBUTE_WORK in actions
        assert RecoveryAction.REDUCE_LOAD in actions


# -- RecoveryPlanner.plan_recovery (RED) --------------------------------------


class TestPlanRecoveryRed:
    def test_red_level_steps(self):
        planner = RecoveryPlanner()
        plan = planner.plan_recovery(
            DefenseLevel.RED,
            0.92,
            n1_failures=2,
            n2_failures=0,
            coverage_gaps=0,
            burnout_cases=0,
        )
        assert len(plan.steps) >= 2
        actions = [s.action for s in plan.steps]
        assert RecoveryAction.ACTIVATE_BACKUP in actions
        assert RecoveryAction.REDUCE_LOAD in actions


# -- RecoveryPlanner.plan_recovery (BLACK) ------------------------------------


class TestPlanRecoveryBlack:
    def test_black_level_steps(self):
        planner = RecoveryPlanner()
        plan = planner.plan_recovery(
            DefenseLevel.BLACK,
            0.98,
            n1_failures=5,
            n2_failures=3,
            coverage_gaps=4,
            burnout_cases=2,
        )
        assert len(plan.steps) >= 3
        actions = [s.action for s in plan.steps]
        assert RecoveryAction.EMERGENCY_PROTOCOL in actions
        assert RecoveryAction.ACTIVATE_BACKUP in actions
        assert RecoveryAction.IMPLEMENT_RESTRICTIONS in actions

    def test_black_has_highest_priority_steps(self):
        planner = RecoveryPlanner()
        plan = planner.plan_recovery(
            DefenseLevel.BLACK,
            0.99,
            n1_failures=5,
            n2_failures=3,
            coverage_gaps=2,
            burnout_cases=3,
        )
        black_steps = [
            s
            for s in plan.steps
            if s.action
            in {
                RecoveryAction.EMERGENCY_PROTOCOL,
                RecoveryAction.IMPLEMENT_RESTRICTIONS,
            }
        ]
        for step in black_steps:
            assert step.priority == 1


# -- Problem-specific recovery steps -----------------------------------------


class TestProblemSpecificSteps:
    def test_high_utilization_adds_capacity(self):
        planner = RecoveryPlanner()
        plan = planner.plan_recovery(
            DefenseLevel.GREEN,
            0.96,
            n1_failures=0,
            n2_failures=0,
            coverage_gaps=0,
            burnout_cases=0,
        )
        actions = [s.action for s in plan.steps]
        assert RecoveryAction.ADD_CAPACITY in actions

    def test_utilization_91_no_extra_capacity_step(self):
        """Utilization 0.91 triggers no extra utilization step (threshold is >0.95)."""
        planner = RecoveryPlanner()
        plan = planner.plan_recovery(
            DefenseLevel.GREEN,
            0.91,
            n1_failures=0,
            n2_failures=0,
            coverage_gaps=0,
            burnout_cases=0,
        )
        actions = [s.action for s in plan.steps]
        assert RecoveryAction.ADD_CAPACITY not in actions

    def test_coverage_gaps_activate_backup(self):
        planner = RecoveryPlanner()
        plan = planner.plan_recovery(
            DefenseLevel.GREEN,
            0.70,
            n1_failures=0,
            n2_failures=0,
            coverage_gaps=3,
            burnout_cases=0,
        )
        actions = [s.action for s in plan.steps]
        assert RecoveryAction.ACTIVATE_BACKUP in actions
        coverage_steps = [s for s in plan.steps if "coverage" in s.description.lower()]
        assert len(coverage_steps) == 1
        assert coverage_steps[0].estimated_time_hours == 3 * 0.5

    def test_burnout_reduces_load(self):
        planner = RecoveryPlanner()
        plan = planner.plan_recovery(
            DefenseLevel.GREEN,
            0.70,
            n1_failures=0,
            n2_failures=0,
            coverage_gaps=0,
            burnout_cases=5,
        )
        actions = [s.action for s in plan.steps]
        assert RecoveryAction.REDUCE_LOAD in actions

    def test_n2_failures_add_capacity(self):
        planner = RecoveryPlanner()
        plan = planner.plan_recovery(
            DefenseLevel.GREEN,
            0.70,
            n1_failures=0,
            n2_failures=4,
            coverage_gaps=0,
            burnout_cases=0,
        )
        actions = [s.action for s in plan.steps]
        assert RecoveryAction.ADD_CAPACITY in actions


# -- Steps sorted by priority -------------------------------------------------


class TestStepSorting:
    def test_steps_sorted_by_priority(self):
        planner = RecoveryPlanner()
        plan = planner.plan_recovery(
            DefenseLevel.BLACK,
            0.98,
            n1_failures=3,
            n2_failures=2,
            coverage_gaps=3,
            burnout_cases=2,
        )
        priorities = [s.priority for s in plan.steps]
        assert priorities == sorted(priorities)


# -- Total time calculation ---------------------------------------------------


class TestTotalTime:
    def test_total_time_is_sum(self):
        planner = RecoveryPlanner()
        plan = planner.plan_recovery(
            DefenseLevel.RED,
            0.92,
            n1_failures=0,
            n2_failures=0,
            coverage_gaps=2,
            burnout_cases=1,
        )
        expected = sum(s.estimated_time_hours for s in plan.steps)
        assert plan.estimated_total_time == pytest.approx(expected)

    def test_zero_steps_zero_time(self):
        planner = RecoveryPlanner()
        plan = planner.plan_recovery(
            DefenseLevel.GREEN,
            0.70,
            n1_failures=0,
            n2_failures=0,
            coverage_gaps=0,
            burnout_cases=0,
        )
        assert plan.estimated_total_time == 0.0


# -- Success probability ------------------------------------------------------


class TestSuccessProbability:
    def test_green_is_highest(self):
        planner = RecoveryPlanner()
        plan = planner.plan_recovery(
            DefenseLevel.GREEN,
            0.70,
            n1_failures=0,
            n2_failures=0,
            coverage_gaps=0,
            burnout_cases=0,
        )
        # base_prob=1.0, num_steps=0 → 1.0 - 0.05*(0-1) = 1.05
        assert plan.success_probability >= 1.0

    def test_black_is_lowest(self):
        planner = RecoveryPlanner()
        plan = planner.plan_recovery(
            DefenseLevel.BLACK,
            0.99,
            n1_failures=5,
            n2_failures=3,
            coverage_gaps=4,
            burnout_cases=5,
        )
        assert plan.success_probability < 0.5

    def test_more_steps_reduce_probability(self):
        planner = RecoveryPlanner()
        simple = planner.plan_recovery(
            DefenseLevel.YELLOW,
            0.80,
            n1_failures=0,
            n2_failures=0,
            coverage_gaps=0,
            burnout_cases=0,
        )
        complex_ = planner.plan_recovery(
            DefenseLevel.YELLOW,
            0.80,
            n1_failures=0,
            n2_failures=5,
            coverage_gaps=3,
            burnout_cases=2,
        )
        assert complex_.success_probability < simple.success_probability

    def test_minimum_probability(self):
        planner = RecoveryPlanner()
        plan = planner.plan_recovery(
            DefenseLevel.BLACK,
            0.99,
            n1_failures=10,
            n2_failures=10,
            coverage_gaps=10,
            burnout_cases=10,
        )
        assert plan.success_probability >= 0.1

    def test_probability_decreases_with_severity(self):
        planner = RecoveryPlanner()
        levels = [
            DefenseLevel.GREEN,
            DefenseLevel.YELLOW,
            DefenseLevel.ORANGE,
            DefenseLevel.RED,
            DefenseLevel.BLACK,
        ]
        probs = []
        for level in levels:
            plan = planner.plan_recovery(
                level,
                0.70,
                n1_failures=0,
                n2_failures=0,
                coverage_gaps=0,
                burnout_cases=0,
            )
            probs.append(plan.success_probability)
        for i in range(len(probs) - 1):
            assert probs[i] >= probs[i + 1]


# -- Contingency actions ------------------------------------------------------


class TestContingencyActions:
    def test_black_has_most_contingencies(self):
        planner = RecoveryPlanner()
        plan = planner.plan_recovery(
            DefenseLevel.BLACK,
            0.99,
            n1_failures=5,
            n2_failures=3,
            coverage_gaps=4,
            burnout_cases=5,
        )
        assert len(plan.contingency_actions) >= 4

    def test_red_has_contingencies(self):
        planner = RecoveryPlanner()
        plan = planner.plan_recovery(
            DefenseLevel.RED,
            0.92,
            n1_failures=2,
            n2_failures=0,
            coverage_gaps=0,
            burnout_cases=0,
        )
        assert len(plan.contingency_actions) >= 3

    def test_yellow_has_basic_contingencies(self):
        planner = RecoveryPlanner()
        plan = planner.plan_recovery(
            DefenseLevel.YELLOW,
            0.80,
            n1_failures=0,
            n2_failures=0,
            coverage_gaps=0,
            burnout_cases=0,
        )
        assert len(plan.contingency_actions) >= 2

    def test_green_has_basic_contingencies(self):
        planner = RecoveryPlanner()
        plan = planner.plan_recovery(
            DefenseLevel.GREEN,
            0.70,
            n1_failures=0,
            n2_failures=0,
            coverage_gaps=0,
            burnout_cases=0,
        )
        assert len(plan.contingency_actions) >= 2

    def test_black_mentions_acgme(self):
        planner = RecoveryPlanner()
        plan = planner.plan_recovery(
            DefenseLevel.BLACK,
            0.99,
            n1_failures=5,
            n2_failures=3,
            coverage_gaps=4,
            burnout_cases=5,
        )
        acgme_mentioned = any("ACGME" in c for c in plan.contingency_actions)
        assert acgme_mentioned
