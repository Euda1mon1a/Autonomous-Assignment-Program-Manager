"""Tests for advanced constraint handling for multi-objective optimization (no DB)."""

import numpy as np
import pytest

from app.multi_objective.constraints import (
    AdaptivePenaltyMethod,
    ConstraintDominanceMethod,
    ConstraintEvaluation,
    ConstraintHandler,
    ConstraintHandlingMethod,
    ConstraintRelaxer,
    ConstraintViolation,
    DynamicPenaltyMethod,
    FeasibilityPreserver,
    GreedyRepairOperator,
    PenaltyType,
    RandomRepairOperator,
    RelaxationLevel,
    StaticPenaltyMethod,
    create_acgme_constraint_handler,
    create_emergency_constraint_handler,
    create_scheduling_constraint_handler,
)
from app.multi_objective.core import (
    ObjectiveConfig,
    ObjectiveDirection,
    ObjectiveType,
    Solution,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _solution(coverage: float = 0.5, equity: float = 0.3, **kw) -> Solution:
    return Solution(objective_values={"coverage": coverage, "equity": equity}, **kw)


def _hard_violation(magnitude: float = 1.0, name: str = "hours") -> ConstraintViolation:
    return ConstraintViolation(
        constraint_name=name,
        constraint_type="acgme",
        magnitude=magnitude,
        is_hard=True,
    )


def _soft_violation(
    magnitude: float = 0.5, name: str = "equity"
) -> ConstraintViolation:
    return ConstraintViolation(
        constraint_name=name,
        constraint_type="preference",
        magnitude=magnitude,
        is_hard=False,
    )


# ---------------------------------------------------------------------------
# ConstraintHandlingMethod enum
# ---------------------------------------------------------------------------


class TestConstraintHandlingMethod:
    def test_penalty(self):
        assert ConstraintHandlingMethod.PENALTY.value == "penalty"

    def test_repair(self):
        assert ConstraintHandlingMethod.REPAIR.value == "repair"

    def test_feasibility_rules(self):
        assert ConstraintHandlingMethod.FEASIBILITY_RULES.value == "feasibility_rules"

    def test_epsilon_constraint(self):
        assert ConstraintHandlingMethod.EPSILON_CONSTRAINT.value == "epsilon_constraint"

    def test_stochastic_ranking(self):
        assert ConstraintHandlingMethod.STOCHASTIC_RANKING.value == "stochastic_ranking"

    def test_hybrid(self):
        assert ConstraintHandlingMethod.HYBRID.value == "hybrid"

    def test_member_count(self):
        assert len(ConstraintHandlingMethod) == 6


# ---------------------------------------------------------------------------
# PenaltyType enum
# ---------------------------------------------------------------------------


class TestPenaltyType:
    def test_static(self):
        assert PenaltyType.STATIC.value == "static"

    def test_dynamic(self):
        assert PenaltyType.DYNAMIC.value == "dynamic"

    def test_adaptive(self):
        assert PenaltyType.ADAPTIVE.value == "adaptive"

    def test_death(self):
        assert PenaltyType.DEATH.value == "death"

    def test_constraint_dominance(self):
        assert PenaltyType.CONSTRAINT_DOMINANCE.value == "constraint_dominance"

    def test_member_count(self):
        assert len(PenaltyType) == 5


# ---------------------------------------------------------------------------
# ConstraintViolation dataclass
# ---------------------------------------------------------------------------


class TestConstraintViolation:
    def test_construction(self):
        cv = ConstraintViolation(
            constraint_name="hours",
            constraint_type="acgme",
            magnitude=2.5,
        )
        assert cv.constraint_name == "hours"
        assert cv.constraint_type == "acgme"
        assert cv.magnitude == 2.5

    def test_defaults(self):
        cv = ConstraintViolation(
            constraint_name="x", constraint_type="y", magnitude=0.0
        )
        assert cv.is_hard is True
        assert cv.relaxable is False
        assert cv.details == {}
        assert cv.affected_entities == []


# ---------------------------------------------------------------------------
# ConstraintEvaluation dataclass
# ---------------------------------------------------------------------------


class TestConstraintEvaluation:
    def test_construction(self):
        ce = ConstraintEvaluation(is_feasible=True, total_violation=0.0)
        assert ce.is_feasible is True
        assert ce.total_violation == 0.0

    def test_defaults(self):
        ce = ConstraintEvaluation(is_feasible=False, total_violation=1.0)
        assert ce.violations == []
        assert ce.hard_violation_count == 0
        assert ce.soft_violation_count == 0
        assert ce.penalty == 0.0
        assert ce.can_repair is False
        assert ce.repair_cost == 0.0


# ---------------------------------------------------------------------------
# StaticPenaltyMethod
# ---------------------------------------------------------------------------


class TestStaticPenaltyMethod:
    def test_default_coefficients(self):
        sp = StaticPenaltyMethod()
        assert sp.hard_coefficient == 1000.0
        assert sp.soft_coefficient == 10.0

    def test_custom_coefficients(self):
        sp = StaticPenaltyMethod(hard_coefficient=500.0, soft_coefficient=5.0)
        assert sp.hard_coefficient == 500.0
        assert sp.soft_coefficient == 5.0

    def test_no_violations(self):
        sp = StaticPenaltyMethod()
        assert sp.calculate_penalty([], 0, 100) == 0.0

    def test_single_hard_violation(self):
        sp = StaticPenaltyMethod(hard_coefficient=100.0)
        violations = [_hard_violation(2.0)]
        # 100 * 2^2 = 400
        assert abs(sp.calculate_penalty(violations, 0, 100) - 400.0) < 1e-10

    def test_single_soft_violation(self):
        sp = StaticPenaltyMethod(soft_coefficient=10.0)
        violations = [_soft_violation(3.0)]
        # 10 * 3^2 = 90
        assert abs(sp.calculate_penalty(violations, 0, 100) - 90.0) < 1e-10

    def test_mixed_violations(self):
        sp = StaticPenaltyMethod(hard_coefficient=100.0, soft_coefficient=10.0)
        violations = [_hard_violation(1.0), _soft_violation(2.0)]
        # 100*1 + 10*4 = 140
        assert abs(sp.calculate_penalty(violations, 0, 100) - 140.0) < 1e-10

    def test_ignores_generation(self):
        sp = StaticPenaltyMethod(hard_coefficient=100.0)
        violations = [_hard_violation(1.0)]
        p0 = sp.calculate_penalty(violations, 0, 100)
        p50 = sp.calculate_penalty(violations, 50, 100)
        assert abs(p0 - p50) < 1e-10


# ---------------------------------------------------------------------------
# DynamicPenaltyMethod
# ---------------------------------------------------------------------------


class TestDynamicPenaltyMethod:
    def test_defaults(self):
        dp = DynamicPenaltyMethod()
        assert dp.base_coefficient == 100.0
        assert dp.growth_rate == 2.0
        assert dp.violation_power == 2.0

    def test_no_violations(self):
        dp = DynamicPenaltyMethod()
        assert dp.calculate_penalty([], 50, 100) == 0.0

    def test_increases_with_generation(self):
        dp = DynamicPenaltyMethod(base_coefficient=100.0, growth_rate=2.0)
        violations = [_hard_violation(1.0)]
        p_early = dp.calculate_penalty(violations, 0, 100)
        p_late = dp.calculate_penalty(violations, 99, 100)
        assert p_late > p_early

    def test_hard_vs_soft_multiplier(self):
        dp = DynamicPenaltyMethod(base_coefficient=100.0)
        hard = [_hard_violation(1.0)]
        soft = [_soft_violation(1.0)]
        p_hard = dp.calculate_penalty(hard, 50, 100)
        p_soft = dp.calculate_penalty(soft, 50, 100)
        # Hard has 10x multiplier vs soft 1x
        assert abs(p_hard / p_soft - 10.0) < 1e-10

    def test_zero_max_generations(self):
        dp = DynamicPenaltyMethod(base_coefficient=100.0, growth_rate=2.0)
        violations = [_hard_violation(1.0)]
        # progress=1.0 when max_gen=0 → coeff = 100*(1^2)=100
        result = dp.calculate_penalty(violations, 5, 0)
        # 10 * 100 * 1^2 = 1000
        assert abs(result - 1000.0) < 1e-10

    def test_mid_generation(self):
        dp = DynamicPenaltyMethod(
            base_coefficient=100.0, growth_rate=2.0, violation_power=2.0
        )
        violations = [_soft_violation(2.0)]
        # gen=49, max=100 → progress=50/100=0.5
        # coeff = 100 * 0.5^2 = 25
        # penalty = 1 * 25 * 2^2 = 100
        result = dp.calculate_penalty(violations, 49, 100)
        assert abs(result - 100.0) < 1e-10


# ---------------------------------------------------------------------------
# AdaptivePenaltyMethod
# ---------------------------------------------------------------------------


class TestAdaptivePenaltyMethod:
    def test_defaults(self):
        ap = AdaptivePenaltyMethod()
        assert ap.coefficient == 100.0
        assert ap.target_feasibility == 0.5
        assert ap.adaptation_rate == 0.1

    def test_no_violations(self):
        ap = AdaptivePenaltyMethod()
        assert ap.calculate_penalty([], 0, 100) == 0.0

    def test_penalty_uses_coefficient(self):
        ap = AdaptivePenaltyMethod(initial_coefficient=200.0)
        violations = [_soft_violation(1.0)]
        # 1.0 * 200 * 1^2 = 200
        assert abs(ap.calculate_penalty(violations, 0, 100) - 200.0) < 1e-10

    def test_hard_multiplier(self):
        ap = AdaptivePenaltyMethod(initial_coefficient=100.0)
        violations = [_hard_violation(1.0)]
        # 10 * 100 * 1^2 = 1000
        assert abs(ap.calculate_penalty(violations, 0, 100) - 1000.0) < 1e-10

    def test_update_decreases_when_below_target(self):
        ap = AdaptivePenaltyMethod(initial_coefficient=100.0, target_feasibility=0.5)
        ap.update_feasibility(0.2)  # below 0.5
        assert ap.coefficient < 100.0

    def test_update_increases_when_above_target(self):
        ap = AdaptivePenaltyMethod(initial_coefficient=100.0, target_feasibility=0.5)
        ap.update_feasibility(0.7)  # above 0.5
        assert ap.coefficient > 100.0

    def test_coefficient_lower_bound(self):
        ap = AdaptivePenaltyMethod(initial_coefficient=1.1, adaptation_rate=0.99)
        ap.update_feasibility(0.0)  # decrease
        assert ap.coefficient >= 1.0

    def test_coefficient_upper_bound(self):
        ap = AdaptivePenaltyMethod(initial_coefficient=9999.0, adaptation_rate=0.99)
        ap.update_feasibility(0.99)  # increase
        assert ap.coefficient <= 10000.0

    def test_feasibility_history_recorded(self):
        ap = AdaptivePenaltyMethod()
        ap.update_feasibility(0.3)
        ap.update_feasibility(0.6)
        assert len(ap._feasibility_history) == 2
        assert ap._feasibility_history[0] == 0.3
        assert ap._feasibility_history[1] == 0.6


# ---------------------------------------------------------------------------
# ConstraintDominanceMethod
# ---------------------------------------------------------------------------


class TestConstraintDominanceMethod:
    def test_default_weight(self):
        cd = ConstraintDominanceMethod()
        assert cd.feasibility_weight == float("inf")

    def test_no_violations(self):
        cd = ConstraintDominanceMethod()
        assert cd.calculate_penalty([], 0, 100) == 0.0

    def test_soft_only_returns_total(self):
        cd = ConstraintDominanceMethod()
        violations = [_soft_violation(0.5), _soft_violation(0.3)]
        result = cd.calculate_penalty(violations, 0, 100)
        assert abs(result - 0.8) < 1e-10

    def test_hard_violation_adds_inf(self):
        cd = ConstraintDominanceMethod()
        violations = [_hard_violation(0.5)]
        result = cd.calculate_penalty(violations, 0, 100)
        assert result == float("inf")

    def test_hard_with_finite_weight(self):
        cd = ConstraintDominanceMethod(feasibility_weight=1000.0)
        violations = [_hard_violation(0.5)]
        result = cd.calculate_penalty(violations, 0, 100)
        assert abs(result - 1000.5) < 1e-10

    def test_mixed_hard_soft(self):
        cd = ConstraintDominanceMethod(feasibility_weight=100.0)
        violations = [_hard_violation(1.0), _soft_violation(0.5)]
        # has hard → 100 + (1.0+0.5) = 101.5
        result = cd.calculate_penalty(violations, 0, 100)
        assert abs(result - 101.5) < 1e-10


# ---------------------------------------------------------------------------
# GreedyRepairOperator
# ---------------------------------------------------------------------------


class TestGreedyRepairOperator:
    def test_can_repair_no_violations(self):
        gro = GreedyRepairOperator()
        sol = _solution()
        assert gro.can_repair(sol, []) is True

    def test_can_repair_hard_without_function(self):
        gro = GreedyRepairOperator()
        sol = _solution()
        violations = [_hard_violation()]
        # Hard, not relaxable, no repair function for "acgme"
        assert gro.can_repair(sol, violations) is False

    def test_can_repair_hard_with_function(self):
        gro = GreedyRepairOperator(repair_functions={"acgme": lambda s, v, c: True})
        sol = _solution()
        violations = [_hard_violation()]
        assert gro.can_repair(sol, violations) is True

    def test_can_repair_soft_no_functions(self):
        gro = GreedyRepairOperator()
        sol = _solution()
        violations = [_soft_violation()]
        # Soft violations don't trigger the hard check
        assert gro.can_repair(sol, violations) is True

    def test_can_repair_relaxable_hard(self):
        gro = GreedyRepairOperator()
        sol = _solution()
        v = ConstraintViolation(
            constraint_name="hours",
            constraint_type="acgme",
            magnitude=1.0,
            is_hard=True,
            relaxable=True,
        )
        # Hard but relaxable → skips repair function check
        assert gro.can_repair(sol, [v]) is True

    def test_default_max_iterations(self):
        gro = GreedyRepairOperator()
        assert gro.max_iterations == 100


# ---------------------------------------------------------------------------
# RandomRepairOperator
# ---------------------------------------------------------------------------


class TestRandomRepairOperator:
    def test_can_repair_always_true(self):
        rro = RandomRepairOperator()
        sol = _solution()
        assert rro.can_repair(sol, [_hard_violation()]) is True
        assert rro.can_repair(sol, []) is True

    def test_defaults(self):
        rro = RandomRepairOperator()
        assert rro.max_attempts == 10
        assert rro.perturbation_strength == 0.1

    def test_custom_params(self):
        rro = RandomRepairOperator(max_attempts=20, perturbation_strength=0.5)
        assert rro.max_attempts == 20
        assert rro.perturbation_strength == 0.5


# ---------------------------------------------------------------------------
# FeasibilityPreserver
# ---------------------------------------------------------------------------


class TestFeasibilityPreserver:
    def test_returns_feasible_offspring(self):
        def always_feasible(s, c):
            return True

        def crossover(a, b):
            return _solution(0.6, 0.4)

        def mutate(s):
            return s

        fp = FeasibilityPreserver(feasibility_check=always_feasible, max_attempts=5)
        p1 = _solution(0.5, 0.3)
        p2 = _solution(0.7, 0.5)
        result = fp.generate_feasible_offspring(p1, p2, crossover, mutate, None)
        assert result is not None

    def test_returns_none_when_infeasible(self):
        def never_feasible(s, c):
            return False

        def crossover(a, b):
            return _solution(0.6, 0.4)

        def mutate(s):
            return s

        fp = FeasibilityPreserver(feasibility_check=never_feasible, max_attempts=3)
        p1 = _solution(0.5, 0.3)
        p2 = _solution(0.7, 0.5)
        result = fp.generate_feasible_offspring(p1, p2, crossover, mutate, None)
        assert result is None

    def test_fallback_to_parent1(self):
        call_count = [0]

        def check(s, c):
            call_count[0] += 1
            # Fail for offspring (first N calls), pass for parent1
            if call_count[0] <= 3:
                return False
            return s.objective_values.get("coverage") == 0.5

        def crossover(a, b):
            return _solution(0.6, 0.4)

        def mutate(s):
            return s

        fp = FeasibilityPreserver(feasibility_check=check, max_attempts=3)
        p1 = _solution(0.5, 0.3)
        p2 = _solution(0.7, 0.5)
        result = fp.generate_feasible_offspring(p1, p2, crossover, mutate, None)
        assert result is not None


# ---------------------------------------------------------------------------
# RelaxationLevel dataclass
# ---------------------------------------------------------------------------


class TestRelaxationLevel:
    def test_construction(self):
        rl = RelaxationLevel(
            constraint_name="hours",
            original_threshold=80.0,
            current_threshold=80.0,
            relaxation_step=8.0,
            max_relaxation=40.0,
        )
        assert rl.constraint_name == "hours"
        assert rl.original_threshold == 80.0
        assert rl.relaxation_step == 8.0

    def test_default_not_relaxed(self):
        rl = RelaxationLevel(
            constraint_name="x",
            original_threshold=1.0,
            current_threshold=1.0,
            relaxation_step=0.1,
            max_relaxation=0.5,
        )
        assert rl.is_relaxed is False


# ---------------------------------------------------------------------------
# ConstraintRelaxer
# ---------------------------------------------------------------------------


class TestConstraintRelaxer:
    def test_register_constraint(self):
        cr = ConstraintRelaxer()
        cr.register_constraint("hours", 80.0, 8.0, 40.0)
        assert "hours" in cr.relaxations
        assert cr.relaxations["hours"].original_threshold == 80.0

    def test_register_default_step(self):
        cr = ConstraintRelaxer()
        cr.register_constraint("hours", 100.0)
        # Default step = 10% of threshold = 10.0
        assert abs(cr.relaxations["hours"].relaxation_step - 10.0) < 1e-10

    def test_register_default_max(self):
        cr = ConstraintRelaxer()
        cr.register_constraint("hours", 100.0)
        # Default max = 50% of threshold = 50.0
        assert abs(cr.relaxations["hours"].max_relaxation - 50.0) < 1e-10

    def test_get_current_thresholds(self):
        cr = ConstraintRelaxer()
        cr.register_constraint("hours", 80.0)
        cr.register_constraint("equity", 0.3)
        thresholds = cr.get_current_thresholds()
        assert abs(thresholds["hours"] - 80.0) < 1e-10
        assert abs(thresholds["equity"] - 0.3) < 1e-10

    def test_is_any_relaxed_initial(self):
        cr = ConstraintRelaxer()
        cr.register_constraint("hours", 80.0)
        assert cr.is_any_relaxed() is False

    def test_relax_after_infeasible_streak(self):
        cr = ConstraintRelaxer()
        cr.register_constraint("hours", 80.0, 8.0, 40.0)
        # Need 4 infeasible updates to trigger relaxation (>3)
        for _ in range(4):
            cr.update(is_feasible=False, feasibility_ratio=0.0)
        assert cr.is_any_relaxed() is True
        assert cr.relaxations["hours"].current_threshold > 80.0

    def test_no_relax_if_short_streak(self):
        cr = ConstraintRelaxer()
        cr.register_constraint("hours", 80.0, 8.0, 40.0)
        for _ in range(3):
            cr.update(is_feasible=False, feasibility_ratio=0.0)
        assert cr.is_any_relaxed() is False

    def test_restore_after_feasible_streak(self):
        cr = ConstraintRelaxer()
        cr.register_constraint("hours", 80.0, 8.0, 40.0)
        # First relax
        for _ in range(4):
            cr.update(is_feasible=False, feasibility_ratio=0.0)
        relaxed_val = cr.relaxations["hours"].current_threshold
        assert relaxed_val > 80.0
        # Then restore (need >5 feasible)
        for _ in range(6):
            cr.update(is_feasible=True, feasibility_ratio=0.5)
        restored_val = cr.relaxations["hours"].current_threshold
        assert restored_val < relaxed_val

    def test_get_relaxation_report(self):
        cr = ConstraintRelaxer()
        cr.register_constraint("hours", 80.0, 8.0, 40.0)
        report = cr.get_relaxation_report()
        assert len(report) == 1
        assert report[0]["constraint"] == "hours"
        assert report[0]["original"] == 80.0
        assert report[0]["is_relaxed"] is False

    def test_relaxation_report_after_relax(self):
        cr = ConstraintRelaxer()
        cr.register_constraint("hours", 80.0, 8.0, 40.0)
        for _ in range(4):
            cr.update(is_feasible=False, feasibility_ratio=0.0)
        report = cr.get_relaxation_report()
        assert report[0]["is_relaxed"] is True
        assert report[0]["relaxation_pct"] > 0

    def test_max_relaxation_cap(self):
        cr = ConstraintRelaxer()
        cr.register_constraint("hours", 80.0, 8.0, 40.0)
        # Relax many times — should cap at original + max_relaxation = 120
        for _ in range(100):
            cr.update(is_feasible=False, feasibility_ratio=0.0)
        assert cr.relaxations["hours"].current_threshold <= 120.0


# ---------------------------------------------------------------------------
# ConstraintHandler — init and basic
# ---------------------------------------------------------------------------


class TestConstraintHandlerInit:
    def test_defaults(self):
        ch = ConstraintHandler()
        assert ch.method == ConstraintHandlingMethod.PENALTY
        assert isinstance(ch.penalty_method, AdaptivePenaltyMethod)
        assert ch.repair_operator is None
        assert ch.total_evaluations == 0
        assert ch.feasible_count == 0
        assert ch.repaired_count == 0

    def test_custom_method(self):
        ch = ConstraintHandler(method=ConstraintHandlingMethod.REPAIR)
        assert ch.method == ConstraintHandlingMethod.REPAIR

    def test_set_generation_info(self):
        ch = ConstraintHandler()
        ch.set_generation_info(50, 200)
        assert ch.current_generation == 50
        assert ch.max_generations == 200


# ---------------------------------------------------------------------------
# ConstraintHandler — process_solution
# ---------------------------------------------------------------------------


class TestConstraintHandlerProcess:
    def test_no_violations_feasible(self):
        ch = ConstraintHandler()
        sol = _solution()
        result = ch.process_solution(sol, [], None)
        assert result.is_feasible is True
        assert result.total_constraint_violation == 0.0
        assert ch.feasible_count == 1
        assert ch.total_evaluations == 1

    def test_penalty_method_sets_metadata(self):
        sp = StaticPenaltyMethod(hard_coefficient=100.0)
        ch = ConstraintHandler(
            method=ConstraintHandlingMethod.PENALTY,
            penalty_method=sp,
        )
        sol = _solution()
        violations = [_hard_violation(2.0)]
        result = ch.process_solution(sol, violations, None)
        assert "constraint_penalty" in result.metadata
        assert abs(result.metadata["constraint_penalty"] - 400.0) < 1e-10

    def test_records_violation_names(self):
        ch = ConstraintHandler()
        sol = _solution()
        violations = [_hard_violation(1.0, "hours"), _soft_violation(0.5, "equity")]
        result = ch.process_solution(sol, violations, None)
        assert "hours" in result.constraint_violations
        assert "equity" in result.constraint_violations

    def test_total_violation_summed(self):
        ch = ConstraintHandler()
        sol = _solution()
        violations = [_hard_violation(1.0), _soft_violation(0.5)]
        result = ch.process_solution(sol, violations, None)
        assert abs(result.total_constraint_violation - 1.5) < 1e-10

    def test_hard_violation_makes_infeasible(self):
        ch = ConstraintHandler()
        sol = _solution()
        violations = [_hard_violation(1.0)]
        result = ch.process_solution(sol, violations, None)
        assert result.is_feasible is False

    def test_soft_only_is_feasible(self):
        ch = ConstraintHandler()
        sol = _solution()
        violations = [_soft_violation(0.5)]
        result = ch.process_solution(sol, violations, None)
        assert result.is_feasible is True

    def test_repair_method_with_successful_repair(self):
        def repair_fn(sol, v, ctx):
            return True

        gro = GreedyRepairOperator(repair_functions={"acgme": repair_fn})
        ch = ConstraintHandler(
            method=ConstraintHandlingMethod.REPAIR,
            repair_operator=gro,
        )
        sol = _solution()
        violations = [_hard_violation(1.0)]
        result = ch.process_solution(sol, violations, None)
        assert result.is_feasible is True
        assert ch.repaired_count == 1

    def test_repair_fallback_to_penalty(self):
        ch = ConstraintHandler(
            method=ConstraintHandlingMethod.REPAIR,
            penalty_method=StaticPenaltyMethod(hard_coefficient=100.0),
        )
        sol = _solution()
        violations = [_hard_violation(1.0)]
        # No repair operator set → falls back to penalty
        result = ch.process_solution(sol, violations, None)
        assert "constraint_penalty" in result.metadata


# ---------------------------------------------------------------------------
# ConstraintHandler — update_adaptive and get_statistics
# ---------------------------------------------------------------------------


class TestConstraintHandlerAdaptive:
    def test_update_adaptive_empty_population(self):
        ch = ConstraintHandler()
        ch.update_adaptive([])  # should not crash

    def test_update_adaptive_with_population(self):
        ap = AdaptivePenaltyMethod(initial_coefficient=100.0)
        ch = ConstraintHandler(penalty_method=ap)
        pop = [_solution() for _ in range(5)]
        for s in pop[:3]:
            s.is_feasible = True
        for s in pop[3:]:
            s.is_feasible = False
        ch.update_adaptive(pop)
        # 3/5 = 0.6 > target 0.5 → coefficient should increase
        assert ap.coefficient > 100.0

    def test_get_statistics_initial(self):
        ch = ConstraintHandler()
        stats = ch.get_statistics()
        assert stats["total_evaluations"] == 0
        assert stats["feasible_count"] == 0
        assert stats["feasibility_rate"] == 0.0
        assert stats["repaired_count"] == 0
        assert stats["method"] == "penalty"
        assert stats["is_relaxed"] is False

    def test_get_statistics_after_processing(self):
        ch = ConstraintHandler()
        ch.process_solution(_solution(), [], None)
        ch.process_solution(_solution(), [_hard_violation()], None)
        stats = ch.get_statistics()
        assert stats["total_evaluations"] == 2
        assert stats["feasible_count"] == 1
        assert abs(stats["feasibility_rate"] - 0.5) < 1e-10

    def test_update_adaptive_with_relaxer(self):
        relaxer = ConstraintRelaxer()
        relaxer.register_constraint("hours", 80.0, 8.0, 40.0)
        ch = ConstraintHandler(constraint_relaxer=relaxer)
        pop = [_solution() for _ in range(5)]
        for s in pop:
            s.is_feasible = False
        # Feed infeasible population multiple times to trigger relaxation
        for _ in range(4):
            ch.update_adaptive(pop)
        assert relaxer.is_any_relaxed() is True


# ---------------------------------------------------------------------------
# Factory functions
# ---------------------------------------------------------------------------


class TestFactoryFunctions:
    def test_create_acgme_handler(self):
        ch = create_acgme_constraint_handler()
        assert ch.method == ConstraintHandlingMethod.PENALTY
        assert isinstance(ch.penalty_method, ConstraintDominanceMethod)

    def test_create_scheduling_handler(self):
        ch = create_scheduling_constraint_handler()
        assert ch.method == ConstraintHandlingMethod.HYBRID
        assert isinstance(ch.penalty_method, AdaptivePenaltyMethod)
        assert isinstance(ch.repair_operator, GreedyRepairOperator)
        assert ch.constraint_relaxer is not None

    def test_scheduling_handler_has_relaxer(self):
        ch = create_scheduling_constraint_handler()
        thresholds = ch.constraint_relaxer.get_current_thresholds()
        assert "capacity" in thresholds
        assert "equity" in thresholds

    def test_create_emergency_handler(self):
        ch = create_emergency_constraint_handler()
        assert ch.method == ConstraintHandlingMethod.HYBRID
        assert isinstance(ch.penalty_method, DynamicPenaltyMethod)
        assert isinstance(ch.repair_operator, RandomRepairOperator)

    def test_emergency_handler_has_3_constraints(self):
        ch = create_emergency_constraint_handler()
        thresholds = ch.constraint_relaxer.get_current_thresholds()
        assert len(thresholds) == 3
        assert "capacity" in thresholds
        assert "equity" in thresholds
        assert "coverage" in thresholds
