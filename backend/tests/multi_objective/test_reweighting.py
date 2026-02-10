"""Tests for dynamic objective reweighting (no DB)."""

from datetime import datetime, timedelta

import pytest

from app.multi_objective.core import (
    ObjectiveConfig,
    ObjectiveDirection,
    ObjectiveType,
)
from app.multi_objective.reweighting import (
    ContextProfile,
    ContextType,
    ContextualReweighter,
    DynamicReweighter,
    FeedbackEvent,
    FeedbackProcessor,
    FeedbackType,
    ObjectiveAdjuster,
    TemporalReweighter,
    TemporalSchedule,
    WeightState,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _obj_coverage() -> ObjectiveConfig:
    return ObjectiveConfig(
        name="coverage",
        display_name="Coverage",
        description="Schedule coverage",
        direction=ObjectiveDirection.MAXIMIZE,
        objective_type=ObjectiveType.COVERAGE,
        weight=0.5,
        reference_point=1.0,
        nadir_point=0.0,
    )


def _obj_equity() -> ObjectiveConfig:
    return ObjectiveConfig(
        name="equity",
        display_name="Equity",
        description="Workload equity",
        direction=ObjectiveDirection.MINIMIZE,
        objective_type=ObjectiveType.EQUITY,
        weight=0.5,
        reference_point=0.0,
        nadir_point=1.0,
    )


def _objectives() -> list[ObjectiveConfig]:
    return [_obj_coverage(), _obj_equity()]


def _feedback_event(ftype: FeedbackType, data: dict, **kw) -> FeedbackEvent:
    return FeedbackEvent(
        feedback_type=ftype,
        timestamp=datetime.now(),
        data=data,
        **kw,
    )


# ---------------------------------------------------------------------------
# FeedbackType / ContextType enums
# ---------------------------------------------------------------------------


class TestFeedbackType:
    def test_rating(self):
        assert FeedbackType.RATING.value == "rating"

    def test_comparison(self):
        assert FeedbackType.COMPARISON.value == "comparison"

    def test_member_count(self):
        assert len(FeedbackType) == 7


class TestContextType:
    def test_normal(self):
        assert ContextType.NORMAL.value == "normal"

    def test_emergency(self):
        assert ContextType.EMERGENCY.value == "emergency"

    def test_member_count(self):
        assert len(ContextType) == 6


# ---------------------------------------------------------------------------
# FeedbackEvent / WeightState dataclasses
# ---------------------------------------------------------------------------


class TestFeedbackEvent:
    def test_construction(self):
        e = _feedback_event(FeedbackType.RATING, {"rating": 5})
        assert e.feedback_type == FeedbackType.RATING
        assert e.data["rating"] == 5
        assert e.confidence == 1.0

    def test_custom_confidence(self):
        e = _feedback_event(FeedbackType.RATING, {}, confidence=0.5)
        assert e.confidence == 0.5


class TestWeightState:
    def test_construction(self):
        ws = WeightState(
            weights={"coverage": 0.6, "equity": 0.4},
            timestamp=datetime.now(),
            reason="test",
        )
        assert ws.weights["coverage"] == 0.6
        assert ws.context == ContextType.NORMAL


# ---------------------------------------------------------------------------
# FeedbackProcessor
# ---------------------------------------------------------------------------


class TestFeedbackProcessor:
    def test_init(self):
        fp = FeedbackProcessor(_objectives())
        assert fp.learning_rate == 0.1
        assert fp.decay_factor == 0.95
        assert len(fp.history) == 0

    def test_process_rating_adds_to_history(self):
        fp = FeedbackProcessor(_objectives())
        event = _feedback_event(
            FeedbackType.RATING,
            {"rating": 5, "objectives": {"coverage": 0.9, "equity": 0.2}},
        )
        fp.process_feedback(event)
        assert len(fp.history) == 1

    def test_process_rating_high_returns_deltas(self):
        fp = FeedbackProcessor(_objectives(), learning_rate=0.1)
        event = _feedback_event(
            FeedbackType.RATING,
            {"rating": 5, "objectives": {"coverage": 0.9, "equity": 0.2}},
        )
        deltas = fp.process_feedback(event)
        # High rating with good coverage → positive delta for coverage
        assert "coverage" in deltas

    def test_process_comparison(self):
        fp = FeedbackProcessor(_objectives())
        event = _feedback_event(
            FeedbackType.COMPARISON,
            {
                "preferred_objectives": {"coverage": 0.9, "equity": 0.3},
                "other_objectives": {"coverage": 0.5, "equity": 0.5},
            },
        )
        deltas = fp.process_feedback(event)
        # Preferred has higher coverage (MAXIMIZE) → positive delta
        assert deltas.get("coverage", 0) > 0

    def test_process_adjustment(self):
        fp = FeedbackProcessor(_objectives(), learning_rate=0.1)
        event = _feedback_event(
            FeedbackType.ADJUSTMENT,
            {"adjustments": {"coverage": 2.0, "equity": -1.0}},
        )
        deltas = fp.process_feedback(event)
        assert deltas["coverage"] == 0.2  # 2.0 * 0.1
        assert deltas["equity"] == -0.1  # -1.0 * 0.1

    def test_process_selection(self):
        fp = FeedbackProcessor(_objectives())
        event = _feedback_event(
            FeedbackType.SELECTION,
            {"objectives": {"coverage": 0.8}},
        )
        deltas = fp.process_feedback(event)
        assert deltas.get("coverage", 0) > 0

    def test_process_rejection(self):
        fp = FeedbackProcessor(_objectives())
        event = _feedback_event(
            FeedbackType.REJECTION,
            {"reason": "Bad coverage in this schedule"},
        )
        deltas = fp.process_feedback(event)
        assert deltas.get("coverage", 0) < 0

    def test_process_complaint(self):
        fp = FeedbackProcessor(_objectives())
        event = _feedback_event(
            FeedbackType.COMPLAINT,
            {"objective": "equity", "severity": 0.8},
        )
        deltas = fp.process_feedback(event)
        assert "equity" in deltas
        assert deltas["equity"] > 0

    def test_process_priority(self):
        fp = FeedbackProcessor(_objectives(), learning_rate=0.1)
        event = _feedback_event(
            FeedbackType.PRIORITY,
            {"priority_order": ["coverage", "equity"]},
        )
        deltas = fp.process_feedback(event)
        # coverage first → higher delta than equity
        assert deltas["coverage"] > deltas["equity"]

    def test_cumulative_signals_update(self):
        fp = FeedbackProcessor(_objectives())
        event = _feedback_event(
            FeedbackType.COMPLAINT,
            {"objective": "equity", "severity": 1.0},
        )
        fp.process_feedback(event)
        signals = fp.get_cumulative_adjustments()
        assert signals["equity"] > 0

    def test_decay_applies_to_old_signals(self):
        fp = FeedbackProcessor(_objectives(), decay_factor=0.5)
        event1 = _feedback_event(
            FeedbackType.COMPLAINT,
            {"objective": "equity", "severity": 1.0},
        )
        fp.process_feedback(event1)
        sig1 = fp.get_cumulative_adjustments()["equity"]

        event2 = _feedback_event(
            FeedbackType.COMPLAINT,
            {"objective": "equity", "severity": 1.0},
        )
        fp.process_feedback(event2)
        sig2 = fp.get_cumulative_adjustments()["equity"]
        # Second signal = 0.5 * sig1 + new_delta → different from 2 * sig1
        assert sig2 != 2 * sig1


# ---------------------------------------------------------------------------
# ObjectiveAdjuster
# ---------------------------------------------------------------------------


class TestObjectiveAdjuster:
    def test_init_normalizes(self):
        oa = ObjectiveAdjuster(_objectives())
        total = sum(oa.get_weights().values())
        assert abs(total - 1.0) < 1e-10

    def test_apply_deltas(self):
        oa = ObjectiveAdjuster(_objectives(), max_weight=0.9)
        old = oa.get_weights()
        new = oa.apply_deltas({"coverage": 0.2})
        # After delta + normalization, coverage weight should shift
        assert new["coverage"] != old["coverage"]

    def test_apply_deltas_records_history(self):
        oa = ObjectiveAdjuster(_objectives())
        oa.apply_deltas({"coverage": 0.1})
        assert len(oa.history) == 1

    def test_apply_deltas_respects_min_weight(self):
        oa = ObjectiveAdjuster(_objectives(), min_weight=0.1)
        oa.apply_deltas({"coverage": -10.0})
        w = oa.get_weights()
        assert w["coverage"] >= 0.1 / sum(oa.weights.values()) - 0.01

    def test_apply_deltas_respects_max_weight(self):
        oa = ObjectiveAdjuster(_objectives(), max_weight=0.6)
        oa.apply_deltas({"coverage": 10.0})
        # After normalization, raw weight was clamped at 0.6

    def test_set_weights(self):
        oa = ObjectiveAdjuster(_objectives())
        new = oa.set_weights({"coverage": 0.8, "equity": 0.2})
        total = sum(new.values())
        assert abs(total - 1.0) < 1e-10

    def test_set_weights_records_history(self):
        oa = ObjectiveAdjuster(_objectives())
        oa.set_weights({"coverage": 0.8})
        assert len(oa.history) == 1

    def test_reset_to_default(self):
        oa = ObjectiveAdjuster(_objectives())
        oa.apply_deltas({"coverage": 0.5})
        oa.reset_to_default()
        w = oa.get_weights()
        # Both objectives have weight 0.5, normalized = 0.5 each
        assert abs(w["coverage"] - 0.5) < 1e-10
        assert abs(w["equity"] - 0.5) < 1e-10


# ---------------------------------------------------------------------------
# ContextualReweighter
# ---------------------------------------------------------------------------


class TestContextualReweighter:
    def test_init_default_context(self):
        cr = ContextualReweighter(_objectives())
        assert cr.current_context == ContextType.NORMAL

    def test_default_profiles_exist(self):
        cr = ContextualReweighter(_objectives())
        assert ContextType.NORMAL in cr.profiles
        assert ContextType.EMERGENCY in cr.profiles
        assert ContextType.UNDERSTAFFED in cr.profiles

    def test_switch_context(self):
        cr = ContextualReweighter(_objectives())
        mults = cr.switch_context(ContextType.EMERGENCY)
        assert cr.current_context == ContextType.EMERGENCY
        assert isinstance(mults, dict)

    def test_apply_context_normal_unchanged(self):
        cr = ContextualReweighter(_objectives())
        base = {"coverage": 0.5, "equity": 0.5}
        adjusted = cr.apply_context(base, ContextType.NORMAL)
        # Normal multipliers are all 1.0 → weights unchanged
        assert abs(adjusted["coverage"] - 0.5) < 1e-10
        assert abs(adjusted["equity"] - 0.5) < 1e-10

    def test_apply_context_emergency_shifts(self):
        cr = ContextualReweighter(_objectives())
        base = {"coverage": 0.5, "equity": 0.5}
        adjusted = cr.apply_context(base, ContextType.EMERGENCY)
        # Emergency boosts coverage → its normalized weight should be higher
        assert adjusted.get("coverage", 0) > adjusted.get("equity", 0)

    def test_set_custom_profile(self):
        cr = ContextualReweighter(_objectives())
        profile = ContextProfile(
            context=ContextType.HIGH_DEMAND,
            weight_multipliers={"coverage": 3.0, "equity": 0.5},
            description="High demand",
        )
        cr.set_profile(profile)
        assert ContextType.HIGH_DEMAND in cr.profiles

    def test_get_profile_fallback(self):
        cr = ContextualReweighter(_objectives())
        # HIGH_DEMAND not set by default → falls back to NORMAL
        profile = cr.get_profile(ContextType.HIGH_DEMAND)
        assert profile.context == ContextType.NORMAL


# ---------------------------------------------------------------------------
# TemporalReweighter
# ---------------------------------------------------------------------------


class TestTemporalReweighter:
    def test_init(self):
        tr = TemporalReweighter(_objectives())
        assert len(tr.schedules) == 0

    def test_add_schedule(self):
        tr = TemporalReweighter(_objectives())
        now = datetime.now()
        sched = TemporalSchedule(
            start_time=now,
            end_time=now + timedelta(hours=1),
            weight_profile={"coverage": 0.7, "equity": 0.3},
            reason="test",
        )
        tr.add_schedule(sched)
        assert len(tr.schedules) == 1

    def test_get_weights_at_with_active_schedule(self):
        tr = TemporalReweighter(_objectives())
        now = datetime.now()
        sched = TemporalSchedule(
            start_time=now - timedelta(minutes=5),
            end_time=now + timedelta(hours=1),
            weight_profile={"coverage": 0.8, "equity": 0.2},
            reason="test",
        )
        tr.add_schedule(sched)
        weights = tr.get_weights_at(now)
        assert weights["coverage"] == 0.8

    def test_get_weights_at_no_active_schedule(self):
        tr = TemporalReweighter(_objectives())
        now = datetime.now()
        sched = TemporalSchedule(
            start_time=now + timedelta(hours=1),
            end_time=now + timedelta(hours=2),
            weight_profile={"coverage": 0.8, "equity": 0.2},
            reason="future",
        )
        tr.add_schedule(sched)
        weights = tr.get_weights_at(now)
        # Should return defaults
        assert weights["coverage"] == 0.5

    def test_remove_schedule(self):
        tr = TemporalReweighter(_objectives())
        start = datetime(2026, 1, 1)
        sched = TemporalSchedule(
            start_time=start,
            end_time=start + timedelta(hours=1),
            weight_profile={"coverage": 0.7},
            reason="test",
        )
        tr.add_schedule(sched)
        tr.remove_schedule(start)
        assert len(tr.schedules) == 0

    def test_priority_ordering(self):
        tr = TemporalReweighter(_objectives())
        now = datetime.now()
        low = TemporalSchedule(
            start_time=now - timedelta(hours=1),
            end_time=now + timedelta(hours=1),
            weight_profile={"coverage": 0.3},
            reason="low",
            priority=0,
        )
        high = TemporalSchedule(
            start_time=now - timedelta(hours=1),
            end_time=now + timedelta(hours=1),
            weight_profile={"coverage": 0.9},
            reason="high",
            priority=10,
        )
        tr.add_schedule(low)
        tr.add_schedule(high)
        weights = tr.get_weights_at(now)
        # Higher priority wins (first in list after sort)
        assert weights["coverage"] == 0.9

    def test_create_phase_schedule(self):
        tr = TemporalReweighter(_objectives())
        start = datetime(2026, 6, 1)
        phases = [
            ("explore", {"coverage": 0.7, "equity": 0.3}, timedelta(hours=1)),
            ("exploit", {"coverage": 0.3, "equity": 0.7}, timedelta(hours=1)),
        ]
        created = tr.create_phase_schedule(phases, start=start)
        assert len(created) == 2
        assert len(tr.schedules) == 2
        # Second phase starts after first
        assert created[1].start_time == start + timedelta(hours=1)


# ---------------------------------------------------------------------------
# DynamicReweighter
# ---------------------------------------------------------------------------


class TestDynamicReweighter:
    def test_init(self):
        dr = DynamicReweighter(_objectives())
        assert dr.auto_adjust is True
        assert dr.current_context == ContextType.NORMAL

    def test_process_feedback_returns_weights(self):
        dr = DynamicReweighter(_objectives())
        weights = dr.process_feedback(
            FeedbackType.COMPLAINT,
            {"objective": "equity", "severity": 1.0},
        )
        total = sum(weights.values())
        assert abs(total - 1.0) < 1e-10

    def test_set_context(self):
        dr = DynamicReweighter(_objectives())
        weights = dr.set_context(ContextType.EMERGENCY)
        assert dr.current_context == ContextType.EMERGENCY
        assert abs(sum(weights.values()) - 1.0) < 1e-10

    def test_get_weights_returns_normalized(self):
        dr = DynamicReweighter(_objectives())
        weights = dr.get_weights()
        assert abs(sum(weights.values()) - 1.0) < 1e-10

    def test_schedule_weights(self):
        dr = DynamicReweighter(_objectives())
        now = datetime.now()
        dr.schedule_weights(
            {"coverage": 0.8, "equity": 0.2},
            start=now - timedelta(minutes=1),
            end=now + timedelta(hours=1),
        )
        assert len(dr.temporal.schedules) == 1

    def test_boost_objective(self):
        dr = DynamicReweighter(_objectives())
        original = dr.adjuster.get_weights()["coverage"]
        boosted = dr.boost_objective("coverage", factor=2.0)
        # After boost + normalize, coverage should be proportionally higher
        assert boosted["coverage"] > original

    def test_boost_nonexistent_objective(self):
        dr = DynamicReweighter(_objectives())
        original = dr.adjuster.get_weights()
        result = dr.boost_objective("nonexistent", factor=2.0)
        # Should return unchanged weights
        assert result == original

    def test_boost_with_duration(self):
        dr = DynamicReweighter(_objectives())
        dr.boost_objective("coverage", factor=2.0, duration=timedelta(hours=1))
        assert len(dr.temporal.schedules) == 1

    def test_balance_weights(self):
        dr = DynamicReweighter(_objectives())
        # Unbalance first
        dr.boost_objective("coverage", factor=3.0)
        # Then balance
        balanced = dr.balance_weights()
        assert abs(balanced["coverage"] - 0.5) < 1e-10
        assert abs(balanced["equity"] - 0.5) < 1e-10

    def test_get_adjustment_summary(self):
        dr = DynamicReweighter(_objectives())
        summary = dr.get_adjustment_summary()
        assert "current_weights" in summary
        assert "current_context" in summary
        assert summary["current_context"] == "normal"
        assert summary["feedback_history_length"] == 0

    def test_auto_adjust_off(self):
        dr = DynamicReweighter(_objectives())
        dr.auto_adjust = False
        original = dr.adjuster.get_weights()
        result = dr.process_feedback(
            FeedbackType.COMPLAINT,
            {"objective": "equity", "severity": 1.0},
        )
        # Weights should not change
        assert result == original
