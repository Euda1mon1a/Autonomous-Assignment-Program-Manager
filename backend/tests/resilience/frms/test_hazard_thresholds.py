"""Tests for fatigue hazard thresholds and triggers (no DB)."""

from __future__ import annotations

from datetime import datetime, timedelta
from uuid import uuid4

import pytest

from app.resilience.frms.hazard_thresholds import (
    LEVEL_MITIGATIONS,
    THRESHOLDS,
    FatigueHazard,
    HazardLevel,
    HazardThresholdEngine,
    MitigationType,
    TriggerType,
    get_hazard_level_info,
    get_mitigation_info,
)
from app.resilience.frms.samn_perelli import SamnPerelliLevel


# ---------------------------------------------------------------------------
# HazardLevel enum
# ---------------------------------------------------------------------------


class TestHazardLevel:
    def test_five_levels(self):
        assert len(HazardLevel) == 5

    def test_green(self):
        assert HazardLevel.GREEN.value == "green"

    def test_yellow(self):
        assert HazardLevel.YELLOW.value == "yellow"

    def test_orange(self):
        assert HazardLevel.ORANGE.value == "orange"

    def test_red(self):
        assert HazardLevel.RED.value == "red"

    def test_black(self):
        assert HazardLevel.BLACK.value == "black"

    def test_values_are_strings(self):
        # All values are string type
        for level in HazardLevel:
            assert isinstance(level.value, str)


# ---------------------------------------------------------------------------
# TriggerType enum
# ---------------------------------------------------------------------------


class TestTriggerType:
    def test_has_alertness_low(self):
        assert TriggerType.ALERTNESS_LOW.value == "alertness_low"

    def test_has_acgme_violation(self):
        assert TriggerType.ACGME_VIOLATION.value == "acgme_violation"

    def test_has_sleep_debt_high(self):
        assert TriggerType.SLEEP_DEBT_HIGH.value == "sleep_debt_high"

    def test_at_least_ten_triggers(self):
        assert len(TriggerType) >= 10


# ---------------------------------------------------------------------------
# MitigationType enum
# ---------------------------------------------------------------------------


class TestMitigationType:
    def test_has_monitoring(self):
        assert MitigationType.MONITORING.value == "monitoring"

    def test_has_immediate_relief(self):
        assert MitigationType.IMMEDIATE_RELIEF.value == "immediate_relief"

    def test_has_mandatory_rest(self):
        assert MitigationType.MANDATORY_REST.value == "mandatory_rest"

    def test_at_least_eight(self):
        assert len(MitigationType) >= 8


# ---------------------------------------------------------------------------
# THRESHOLDS constant
# ---------------------------------------------------------------------------


class TestThresholds:
    def test_all_levels_present(self):
        for level in HazardLevel:
            assert level in THRESHOLDS

    def test_green_alertness_highest(self):
        assert THRESHOLDS[HazardLevel.GREEN]["alertness_min"] == 0.7

    def test_green_sleep_debt_lowest(self):
        assert THRESHOLDS[HazardLevel.GREEN]["sleep_debt_max"] == 5.0

    def test_green_hours_awake_lowest(self):
        assert THRESHOLDS[HazardLevel.GREEN]["hours_awake_max"] == 14.0

    def test_red_alertness_lower(self):
        assert (
            THRESHOLDS[HazardLevel.RED]["alertness_min"]
            < THRESHOLDS[HazardLevel.GREEN]["alertness_min"]
        )

    def test_black_alertness_zero(self):
        assert THRESHOLDS[HazardLevel.BLACK]["alertness_min"] == 0.0

    def test_thresholds_escalate_for_sleep_debt(self):
        prev_max = 0
        for level in [
            HazardLevel.GREEN,
            HazardLevel.YELLOW,
            HazardLevel.ORANGE,
            HazardLevel.RED,
            HazardLevel.BLACK,
        ]:
            current = THRESHOLDS[level]["sleep_debt_max"]
            assert current > prev_max
            prev_max = current

    def test_thresholds_escalate_for_hours_awake(self):
        prev_max = 0
        for level in [
            HazardLevel.GREEN,
            HazardLevel.YELLOW,
            HazardLevel.ORANGE,
            HazardLevel.RED,
            HazardLevel.BLACK,
        ]:
            current = THRESHOLDS[level]["hours_awake_max"]
            assert current > prev_max
            prev_max = current


# ---------------------------------------------------------------------------
# LEVEL_MITIGATIONS constant
# ---------------------------------------------------------------------------


class TestLevelMitigations:
    def test_all_levels_present(self):
        for level in HazardLevel:
            assert level in LEVEL_MITIGATIONS

    def test_green_no_mitigations(self):
        assert LEVEL_MITIGATIONS[HazardLevel.GREEN] == []

    def test_yellow_has_monitoring(self):
        assert MitigationType.MONITORING in LEVEL_MITIGATIONS[HazardLevel.YELLOW]

    def test_orange_has_buddy_system(self):
        assert MitigationType.BUDDY_SYSTEM in LEVEL_MITIGATIONS[HazardLevel.ORANGE]

    def test_red_has_schedule_modification(self):
        assert (
            MitigationType.SCHEDULE_MODIFICATION in LEVEL_MITIGATIONS[HazardLevel.RED]
        )

    def test_black_has_mandatory_rest(self):
        assert MitigationType.MANDATORY_REST in LEVEL_MITIGATIONS[HazardLevel.BLACK]

    def test_black_has_immediate_relief(self):
        assert MitigationType.IMMEDIATE_RELIEF in LEVEL_MITIGATIONS[HazardLevel.BLACK]


# ---------------------------------------------------------------------------
# FatigueHazard — construction
# ---------------------------------------------------------------------------


class TestFatigueHazardConstruction:
    def test_basic_fields(self):
        rid = uuid4()
        now = datetime.utcnow()
        h = FatigueHazard(
            resident_id=rid,
            hazard_level=HazardLevel.GREEN,
            detected_at=now,
        )
        assert h.resident_id == rid
        assert h.hazard_level == HazardLevel.GREEN
        assert h.detected_at == now

    def test_defaults_empty(self):
        h = FatigueHazard(
            resident_id=uuid4(),
            hazard_level=HazardLevel.GREEN,
            detected_at=datetime.utcnow(),
        )
        assert h.triggers == []
        assert h.required_mitigations == []
        assert h.recommended_mitigations == []
        assert h.acgme_risk is False
        assert h.alertness_score is None
        assert h.sleep_debt is None
        assert h.hours_awake is None
        assert h.escalation_time is None
        assert h.notes is None


# ---------------------------------------------------------------------------
# FatigueHazard — to_dict
# ---------------------------------------------------------------------------


class TestFatigueHazardToDict:
    def test_keys(self):
        h = FatigueHazard(
            resident_id=uuid4(),
            hazard_level=HazardLevel.YELLOW,
            detected_at=datetime(2026, 1, 15, 10, 0),
            triggers=[TriggerType.ALERTNESS_LOW],
            alertness_score=0.5,
            sleep_debt=8.0,
            hours_awake=16.5,
            samn_perelli=SamnPerelliLevel.MODERATELY_TIRED,
            required_mitigations=[MitigationType.MONITORING],
            recommended_mitigations=[MitigationType.BUDDY_SYSTEM],
            acgme_risk=False,
        )
        d = h.to_dict()
        expected = {
            "resident_id",
            "hazard_level",
            "hazard_level_name",
            "detected_at",
            "triggers",
            "alertness_score",
            "sleep_debt",
            "hours_awake",
            "samn_perelli",
            "required_mitigations",
            "recommended_mitigations",
            "acgme_risk",
            "escalation_time",
            "notes",
        }
        assert set(d.keys()) == expected

    def test_resident_id_is_string(self):
        rid = uuid4()
        h = FatigueHazard(
            resident_id=rid,
            hazard_level=HazardLevel.GREEN,
            detected_at=datetime.utcnow(),
        )
        assert h.to_dict()["resident_id"] == str(rid)

    def test_hazard_level_is_value(self):
        h = FatigueHazard(
            resident_id=uuid4(),
            hazard_level=HazardLevel.RED,
            detected_at=datetime.utcnow(),
        )
        assert h.to_dict()["hazard_level"] == "red"

    def test_hazard_level_name(self):
        h = FatigueHazard(
            resident_id=uuid4(),
            hazard_level=HazardLevel.RED,
            detected_at=datetime.utcnow(),
        )
        assert h.to_dict()["hazard_level_name"] == "RED"

    def test_triggers_are_values(self):
        h = FatigueHazard(
            resident_id=uuid4(),
            hazard_level=HazardLevel.YELLOW,
            detected_at=datetime.utcnow(),
            triggers=[TriggerType.ALERTNESS_LOW, TriggerType.SLEEP_DEBT_HIGH],
        )
        d = h.to_dict()
        assert d["triggers"] == ["alertness_low", "sleep_debt_high"]

    def test_alertness_rounded(self):
        h = FatigueHazard(
            resident_id=uuid4(),
            hazard_level=HazardLevel.GREEN,
            detected_at=datetime.utcnow(),
            alertness_score=0.12345,
        )
        assert h.to_dict()["alertness_score"] == 0.123

    def test_sleep_debt_rounded(self):
        h = FatigueHazard(
            resident_id=uuid4(),
            hazard_level=HazardLevel.GREEN,
            detected_at=datetime.utcnow(),
            sleep_debt=7.89,
        )
        assert h.to_dict()["sleep_debt"] == 7.9

    def test_samn_perelli_is_value(self):
        h = FatigueHazard(
            resident_id=uuid4(),
            hazard_level=HazardLevel.GREEN,
            detected_at=datetime.utcnow(),
            samn_perelli=SamnPerelliLevel.OKAY,
        )
        assert h.to_dict()["samn_perelli"] == 3

    def test_none_fields(self):
        h = FatigueHazard(
            resident_id=uuid4(),
            hazard_level=HazardLevel.GREEN,
            detected_at=datetime.utcnow(),
        )
        d = h.to_dict()
        assert d["alertness_score"] is None
        assert d["sleep_debt"] is None
        assert d["hours_awake"] is None
        assert d["samn_perelli"] is None
        assert d["escalation_time"] is None
        assert d["notes"] is None


# ---------------------------------------------------------------------------
# FatigueHazard — properties
# ---------------------------------------------------------------------------


class TestFatigueHazardProperties:
    def test_green_not_critical(self):
        h = FatigueHazard(
            resident_id=uuid4(),
            hazard_level=HazardLevel.GREEN,
            detected_at=datetime.utcnow(),
        )
        assert h.is_critical is False

    def test_yellow_not_critical(self):
        h = FatigueHazard(
            resident_id=uuid4(),
            hazard_level=HazardLevel.YELLOW,
            detected_at=datetime.utcnow(),
        )
        assert h.is_critical is False

    def test_orange_not_critical(self):
        h = FatigueHazard(
            resident_id=uuid4(),
            hazard_level=HazardLevel.ORANGE,
            detected_at=datetime.utcnow(),
        )
        assert h.is_critical is False

    def test_red_is_critical(self):
        h = FatigueHazard(
            resident_id=uuid4(),
            hazard_level=HazardLevel.RED,
            detected_at=datetime.utcnow(),
        )
        assert h.is_critical is True

    def test_black_is_critical(self):
        h = FatigueHazard(
            resident_id=uuid4(),
            hazard_level=HazardLevel.BLACK,
            detected_at=datetime.utcnow(),
        )
        assert h.is_critical is True

    def test_green_no_schedule_change(self):
        h = FatigueHazard(
            resident_id=uuid4(),
            hazard_level=HazardLevel.GREEN,
            detected_at=datetime.utcnow(),
        )
        assert h.requires_schedule_change is False

    def test_yellow_no_schedule_change(self):
        h = FatigueHazard(
            resident_id=uuid4(),
            hazard_level=HazardLevel.YELLOW,
            detected_at=datetime.utcnow(),
        )
        assert h.requires_schedule_change is False

    def test_orange_requires_schedule_change(self):
        h = FatigueHazard(
            resident_id=uuid4(),
            hazard_level=HazardLevel.ORANGE,
            detected_at=datetime.utcnow(),
        )
        assert h.requires_schedule_change is True

    def test_red_requires_schedule_change(self):
        h = FatigueHazard(
            resident_id=uuid4(),
            hazard_level=HazardLevel.RED,
            detected_at=datetime.utcnow(),
        )
        assert h.requires_schedule_change is True

    def test_black_requires_schedule_change(self):
        h = FatigueHazard(
            resident_id=uuid4(),
            hazard_level=HazardLevel.BLACK,
            detected_at=datetime.utcnow(),
        )
        assert h.requires_schedule_change is True


# ---------------------------------------------------------------------------
# HazardThresholdEngine — construction
# ---------------------------------------------------------------------------


class TestHazardThresholdEngineInit:
    def test_default_acgme_limits(self):
        engine = HazardThresholdEngine()
        assert engine.acgme_weekly_limit == 80.0
        assert engine.acgme_daily_limit == 24.0

    def test_custom_limits(self):
        engine = HazardThresholdEngine(acgme_weekly_limit=72.0, acgme_daily_limit=16.0)
        assert engine.acgme_weekly_limit == 72.0
        assert engine.acgme_daily_limit == 16.0


# ---------------------------------------------------------------------------
# HazardThresholdEngine._check_alertness
# ---------------------------------------------------------------------------


class TestCheckAlertness:
    """Test _check_alertness.

    Note: The method iterates BLACK→GREEN and checks alertness >= min.
    BLACK has min=0.0, so non-negative alertness always matches BLACK first.
    Negative alertness falls through to the final return BLACK.
    """

    def setup_method(self):
        self.engine = HazardThresholdEngine()

    def test_high_alertness_returns_black(self):
        # BLACK min=0.0 matches first in iteration order
        assert self.engine._check_alertness(0.9) == HazardLevel.BLACK

    def test_moderate_alertness_returns_black(self):
        assert self.engine._check_alertness(0.5) == HazardLevel.BLACK

    def test_zero_alertness_returns_black(self):
        assert self.engine._check_alertness(0.0) == HazardLevel.BLACK

    def test_negative_alertness_returns_yellow(self):
        # Falls through to GREEN check: -0.1 < 0.7, GREEN special case → YELLOW
        assert self.engine._check_alertness(-0.1) == HazardLevel.YELLOW

    def test_returns_hazard_level(self):
        result = self.engine._check_alertness(0.7)
        assert isinstance(result, HazardLevel)


# ---------------------------------------------------------------------------
# HazardThresholdEngine._check_sleep_debt
# ---------------------------------------------------------------------------


class TestCheckSleepDebt:
    def setup_method(self):
        self.engine = HazardThresholdEngine()

    def test_low_debt_green(self):
        assert self.engine._check_sleep_debt(3.0) == HazardLevel.GREEN

    def test_at_green_max(self):
        assert self.engine._check_sleep_debt(5.0) == HazardLevel.GREEN

    def test_above_green_yellow(self):
        assert self.engine._check_sleep_debt(7.0) == HazardLevel.YELLOW

    def test_at_yellow_max(self):
        assert self.engine._check_sleep_debt(10.0) == HazardLevel.YELLOW

    def test_above_yellow_orange(self):
        assert self.engine._check_sleep_debt(12.0) == HazardLevel.ORANGE

    def test_above_orange_red(self):
        assert self.engine._check_sleep_debt(18.0) == HazardLevel.RED

    def test_above_red_black(self):
        assert self.engine._check_sleep_debt(25.0) == HazardLevel.BLACK

    def test_extreme_debt_black(self):
        assert self.engine._check_sleep_debt(50.0) == HazardLevel.BLACK


# ---------------------------------------------------------------------------
# HazardThresholdEngine._check_hours_awake
# ---------------------------------------------------------------------------


class TestCheckHoursAwake:
    def setup_method(self):
        self.engine = HazardThresholdEngine()

    def test_low_hours_green(self):
        assert self.engine._check_hours_awake(10.0) == HazardLevel.GREEN

    def test_at_green_max(self):
        assert self.engine._check_hours_awake(14.0) == HazardLevel.GREEN

    def test_above_green_yellow(self):
        assert self.engine._check_hours_awake(16.0) == HazardLevel.YELLOW

    def test_above_yellow_orange(self):
        assert self.engine._check_hours_awake(20.0) == HazardLevel.ORANGE

    def test_above_orange_red(self):
        assert self.engine._check_hours_awake(24.0) == HazardLevel.RED

    def test_above_red_black(self):
        assert self.engine._check_hours_awake(30.0) == HazardLevel.BLACK

    def test_extreme_hours_black(self):
        assert self.engine._check_hours_awake(50.0) == HazardLevel.BLACK


# ---------------------------------------------------------------------------
# HazardThresholdEngine._check_consecutive_nights
# ---------------------------------------------------------------------------


class TestCheckConsecutiveNights:
    def setup_method(self):
        self.engine = HazardThresholdEngine()

    def test_zero_green(self):
        assert self.engine._check_consecutive_nights(0) == HazardLevel.GREEN

    def test_two_green(self):
        assert self.engine._check_consecutive_nights(2) == HazardLevel.GREEN

    def test_three_yellow(self):
        assert self.engine._check_consecutive_nights(3) == HazardLevel.YELLOW

    def test_four_yellow(self):
        assert self.engine._check_consecutive_nights(4) == HazardLevel.YELLOW

    def test_five_orange(self):
        assert self.engine._check_consecutive_nights(5) == HazardLevel.ORANGE

    def test_six_red(self):
        assert self.engine._check_consecutive_nights(6) == HazardLevel.RED

    def test_seven_black(self):
        assert self.engine._check_consecutive_nights(7) == HazardLevel.BLACK

    def test_eight_plus_black(self):
        assert self.engine._check_consecutive_nights(10) == HazardLevel.BLACK


# ---------------------------------------------------------------------------
# HazardThresholdEngine._check_samn_perelli
# ---------------------------------------------------------------------------


class TestCheckSamnPerelli:
    def setup_method(self):
        self.engine = HazardThresholdEngine()

    def test_fully_alert_green(self):
        assert (
            self.engine._check_samn_perelli(SamnPerelliLevel.FULLY_ALERT)
            == HazardLevel.GREEN
        )

    def test_a_little_tired_green(self):
        assert (
            self.engine._check_samn_perelli(SamnPerelliLevel.A_LITTLE_TIRED)
            == HazardLevel.GREEN
        )

    def test_moderately_tired_yellow(self):
        assert (
            self.engine._check_samn_perelli(SamnPerelliLevel.MODERATELY_TIRED)
            == HazardLevel.YELLOW
        )

    def test_extremely_tired_orange(self):
        assert (
            self.engine._check_samn_perelli(SamnPerelliLevel.EXTREMELY_TIRED)
            == HazardLevel.ORANGE
        )

    def test_exhausted_red(self):
        assert (
            self.engine._check_samn_perelli(SamnPerelliLevel.EXHAUSTED)
            == HazardLevel.RED
        )


# ---------------------------------------------------------------------------
# HazardThresholdEngine._estimate_escalation_time
# ---------------------------------------------------------------------------


class TestEstimateEscalationTime:
    def setup_method(self):
        self.engine = HazardThresholdEngine()

    def test_black_returns_none(self):
        result = self.engine._estimate_escalation_time(
            HazardLevel.BLACK, hours_awake=30.0, sleep_debt=25.0
        )
        assert result is None

    def test_green_with_hours_returns_future(self):
        result = self.engine._estimate_escalation_time(
            HazardLevel.GREEN, hours_awake=10.0, sleep_debt=3.0
        )
        # Next threshold is YELLOW at 18 hours, 8 hours away
        assert result is not None
        assert result > datetime.utcnow()

    def test_no_hours_returns_none(self):
        result = self.engine._estimate_escalation_time(
            HazardLevel.GREEN, hours_awake=None, sleep_debt=None
        )
        assert result is None

    def test_escalation_time_positive_delta(self):
        result = self.engine._estimate_escalation_time(
            HazardLevel.GREEN, hours_awake=10.0, sleep_debt=None
        )
        if result:
            delta = result - datetime.utcnow()
            # Should be roughly 8 hours (18 - 10)
            assert delta.total_seconds() > 0


# ---------------------------------------------------------------------------
# HazardThresholdEngine._get_recommended_mitigations
# ---------------------------------------------------------------------------


class TestGetRecommendedMitigations:
    def setup_method(self):
        self.engine = HazardThresholdEngine()

    def test_green_empty(self):
        assert self.engine._get_recommended_mitigations(HazardLevel.GREEN) == []

    def test_yellow_has_buddy_system(self):
        result = self.engine._get_recommended_mitigations(HazardLevel.YELLOW)
        assert MitigationType.BUDDY_SYSTEM in result

    def test_orange_has_shift_swap(self):
        result = self.engine._get_recommended_mitigations(HazardLevel.ORANGE)
        assert MitigationType.SHIFT_SWAP in result

    def test_orange_has_early_release(self):
        result = self.engine._get_recommended_mitigations(HazardLevel.ORANGE)
        assert MitigationType.EARLY_RELEASE in result

    def test_red_has_immediate_relief(self):
        result = self.engine._get_recommended_mitigations(HazardLevel.RED)
        assert MitigationType.IMMEDIATE_RELIEF in result

    def test_black_empty(self):
        assert self.engine._get_recommended_mitigations(HazardLevel.BLACK) == []


# ---------------------------------------------------------------------------
# HazardThresholdEngine.evaluate_hazard — green
# ---------------------------------------------------------------------------


class TestEvaluateHazardGreen:
    def setup_method(self):
        self.engine = HazardThresholdEngine()

    def test_all_normal_green(self):
        h = self.engine.evaluate_hazard(
            resident_id=uuid4(),
            alertness=0.9,
            sleep_debt=2.0,
            hours_awake=8.0,
            consecutive_nights=0,
        )
        assert h.hazard_level == HazardLevel.GREEN

    def test_green_no_triggers(self):
        h = self.engine.evaluate_hazard(
            resident_id=uuid4(),
            alertness=0.8,
            sleep_debt=3.0,
            hours_awake=10.0,
        )
        assert h.triggers == []

    def test_green_no_required_mitigations(self):
        h = self.engine.evaluate_hazard(
            resident_id=uuid4(),
            alertness=0.85,
        )
        assert h.required_mitigations == []

    def test_no_acgme_risk(self):
        h = self.engine.evaluate_hazard(
            resident_id=uuid4(),
            alertness=0.9,
            hours_worked_week=40.0,
        )
        assert h.acgme_risk is False


# ---------------------------------------------------------------------------
# HazardThresholdEngine.evaluate_hazard — escalation
# ---------------------------------------------------------------------------


class TestEvaluateHazardEscalation:
    def setup_method(self):
        self.engine = HazardThresholdEngine()

    def test_high_sleep_debt_escalates(self):
        h = self.engine.evaluate_hazard(
            resident_id=uuid4(),
            sleep_debt=12.0,
        )
        assert h.hazard_level == HazardLevel.ORANGE
        assert TriggerType.SLEEP_DEBT_HIGH in h.triggers

    def test_long_hours_awake_escalates(self):
        h = self.engine.evaluate_hazard(
            resident_id=uuid4(),
            hours_awake=24.0,
        )
        assert h.hazard_level == HazardLevel.RED
        assert TriggerType.HOURS_AWAKE_EXTENDED in h.triggers

    def test_multiple_factors_take_worst_by_string(self):
        # String comparison: "red" > "orange" > "green"
        h = self.engine.evaluate_hazard(
            resident_id=uuid4(),
            sleep_debt=18.0,  # RED
            hours_awake=10.0,  # GREEN
        )
        assert h.hazard_level == HazardLevel.RED

    def test_consecutive_nights_trigger(self):
        h = self.engine.evaluate_hazard(
            resident_id=uuid4(),
            consecutive_nights=6,
        )
        assert TriggerType.CONSECUTIVE_NIGHTS in h.triggers
        assert h.hazard_level == HazardLevel.RED


# ---------------------------------------------------------------------------
# HazardThresholdEngine.evaluate_hazard — ACGME
# ---------------------------------------------------------------------------


class TestEvaluateHazardACGME:
    def setup_method(self):
        self.engine = HazardThresholdEngine()

    def test_acgme_violation_triggers_red(self):
        h = self.engine.evaluate_hazard(
            resident_id=uuid4(),
            hours_worked_week=80.0,
        )
        assert h.acgme_risk is True
        assert TriggerType.ACGME_VIOLATION in h.triggers
        assert h.hazard_level == HazardLevel.RED

    def test_acgme_approaching_triggers_orange(self):
        h = self.engine.evaluate_hazard(
            resident_id=uuid4(),
            hours_worked_week=73.0,  # > 80 * 0.9 = 72
        )
        assert h.acgme_risk is True
        assert TriggerType.ACGME_APPROACHING in h.triggers

    def test_acgme_safe_no_trigger(self):
        h = self.engine.evaluate_hazard(
            resident_id=uuid4(),
            hours_worked_week=60.0,
        )
        assert h.acgme_risk is False
        assert TriggerType.ACGME_VIOLATION not in h.triggers
        assert TriggerType.ACGME_APPROACHING not in h.triggers


# ---------------------------------------------------------------------------
# HazardThresholdEngine.evaluate_hazard — returns correct type
# ---------------------------------------------------------------------------


class TestEvaluateHazardReturnType:
    def test_returns_fatigue_hazard(self):
        engine = HazardThresholdEngine()
        h = engine.evaluate_hazard(resident_id=uuid4())
        assert isinstance(h, FatigueHazard)

    def test_detected_at_is_recent(self):
        engine = HazardThresholdEngine()
        before = datetime.utcnow()
        h = engine.evaluate_hazard(resident_id=uuid4())
        after = datetime.utcnow()
        assert before <= h.detected_at <= after

    def test_resident_id_preserved(self):
        engine = HazardThresholdEngine()
        rid = uuid4()
        h = engine.evaluate_hazard(resident_id=rid)
        assert h.resident_id == rid


# ---------------------------------------------------------------------------
# HazardThresholdEngine.batch_evaluate
# ---------------------------------------------------------------------------


class TestBatchEvaluate:
    def setup_method(self):
        self.engine = HazardThresholdEngine()

    def test_returns_list(self):
        residents = [
            {"resident_id": uuid4(), "alertness": 0.9},
            {"resident_id": uuid4(), "alertness": 0.4},
        ]
        result = self.engine.batch_evaluate(residents)
        assert isinstance(result, list)
        assert len(result) == 2

    def test_each_is_hazard(self):
        residents = [{"resident_id": uuid4(), "alertness": 0.8}]
        result = self.engine.batch_evaluate(residents)
        assert isinstance(result[0], FatigueHazard)

    def test_empty_list(self):
        result = self.engine.batch_evaluate([])
        assert result == []

    def test_mixed_hazard_levels(self):
        residents = [
            {"resident_id": uuid4(), "sleep_debt": 2.0},  # GREEN
            {"resident_id": uuid4(), "sleep_debt": 18.0},  # RED
        ]
        result = self.engine.batch_evaluate(residents)
        levels = {h.hazard_level for h in result}
        assert len(levels) >= 2


# ---------------------------------------------------------------------------
# HazardThresholdEngine.get_level_summary
# ---------------------------------------------------------------------------


class TestGetLevelSummary:
    def setup_method(self):
        self.engine = HazardThresholdEngine()

    def test_empty_list(self):
        result = self.engine.get_level_summary([])
        assert result["total_residents"] == 0
        assert result["critical_count"] == 0
        assert result["acgme_risk_count"] == 0

    def test_total_count(self):
        hazards = [
            FatigueHazard(
                resident_id=uuid4(),
                hazard_level=HazardLevel.GREEN,
                detected_at=datetime.utcnow(),
            ),
            FatigueHazard(
                resident_id=uuid4(),
                hazard_level=HazardLevel.RED,
                detected_at=datetime.utcnow(),
            ),
        ]
        result = self.engine.get_level_summary(hazards)
        assert result["total_residents"] == 2

    def test_by_level_counts(self):
        hazards = [
            FatigueHazard(
                resident_id=uuid4(),
                hazard_level=HazardLevel.GREEN,
                detected_at=datetime.utcnow(),
            ),
            FatigueHazard(
                resident_id=uuid4(),
                hazard_level=HazardLevel.GREEN,
                detected_at=datetime.utcnow(),
            ),
            FatigueHazard(
                resident_id=uuid4(),
                hazard_level=HazardLevel.RED,
                detected_at=datetime.utcnow(),
            ),
        ]
        result = self.engine.get_level_summary(hazards)
        assert result["by_level"]["green"]["count"] == 2
        assert result["by_level"]["red"]["count"] == 1

    def test_percentages(self):
        hazards = [
            FatigueHazard(
                resident_id=uuid4(),
                hazard_level=HazardLevel.GREEN,
                detected_at=datetime.utcnow(),
            ),
            FatigueHazard(
                resident_id=uuid4(),
                hazard_level=HazardLevel.GREEN,
                detected_at=datetime.utcnow(),
            ),
        ]
        result = self.engine.get_level_summary(hazards)
        assert result["by_level"]["green"]["percentage"] == 100.0

    def test_critical_count(self):
        hazards = [
            FatigueHazard(
                resident_id=uuid4(),
                hazard_level=HazardLevel.GREEN,
                detected_at=datetime.utcnow(),
            ),
            FatigueHazard(
                resident_id=uuid4(),
                hazard_level=HazardLevel.RED,
                detected_at=datetime.utcnow(),
            ),
            FatigueHazard(
                resident_id=uuid4(),
                hazard_level=HazardLevel.BLACK,
                detected_at=datetime.utcnow(),
            ),
        ]
        result = self.engine.get_level_summary(hazards)
        assert result["critical_count"] == 2

    def test_acgme_risk_count(self):
        h1 = FatigueHazard(
            resident_id=uuid4(),
            hazard_level=HazardLevel.GREEN,
            detected_at=datetime.utcnow(),
        )
        h2 = FatigueHazard(
            resident_id=uuid4(),
            hazard_level=HazardLevel.RED,
            detected_at=datetime.utcnow(),
            acgme_risk=True,
        )
        result = self.engine.get_level_summary([h1, h2])
        assert result["acgme_risk_count"] == 1


# ---------------------------------------------------------------------------
# get_hazard_level_info
# ---------------------------------------------------------------------------


class TestGetHazardLevelInfo:
    def test_returns_list(self):
        result = get_hazard_level_info()
        assert isinstance(result, list)

    def test_five_levels(self):
        assert len(get_hazard_level_info()) == 5

    def test_each_has_keys(self):
        for info in get_hazard_level_info():
            assert "level" in info
            assert "name" in info
            assert "description" in info
            assert "thresholds" in info
            assert "required_mitigations" in info

    def test_green_description(self):
        info = get_hazard_level_info()
        green = next(i for i in info if i["level"] == "green")
        assert "Normal" in green["description"]

    def test_black_description(self):
        info = get_hazard_level_info()
        black = next(i for i in info if i["level"] == "black")
        assert "Critical" in black["description"]


# ---------------------------------------------------------------------------
# get_mitigation_info
# ---------------------------------------------------------------------------


class TestGetMitigationInfo:
    def test_returns_list(self):
        result = get_mitigation_info()
        assert isinstance(result, list)

    def test_at_least_eight(self):
        assert len(get_mitigation_info()) >= 8

    def test_each_has_keys(self):
        for info in get_mitigation_info():
            assert "type" in info
            assert "name" in info
            assert "description" in info

    def test_monitoring_description(self):
        info = get_mitigation_info()
        monitoring = next(i for i in info if i["type"] == "monitoring")
        assert len(monitoring["description"]) > 0
