"""Tests for FRMS constants (no DB)."""

from __future__ import annotations

from app.frms.constants import (
    ALERT_DEDUPLICATION_HOURS,
    BACKGROUND_UPDATE_SECONDS,
    CIRCADIAN_ACROPHASE_HOUR,
    CIRCADIAN_AMPLITUDE,
    CIRCADIAN_PERIOD_HOURS,
    CIRCADIAN_WEIGHT,
    CLOSE_SUPERVISION_THRESHOLD,
    CONCURRENT_UPDATE_LIMIT,
    CRITICAL_ALERT_THRESHOLD,
    CRITICAL_WAKEFULNESS_HOURS,
    DEDUPLICATION_WINDOW_HOURS,
    EFFECTIVENESS_CALCULATION_INTERVAL_MINUTES,
    EFFECTIVENESS_DECIMAL_PLACES,
    EFFECTIVENESS_HISTORY_HOURS,
    EMERGENCY_THRESHOLD,
    EXTENDED_WAKEFULNESS_HOURS,
    HIGH_RISK_PROCEDURE_MIN_EFFECTIVENESS,
    HIGH_RISK_THRESHOLD,
    HOMEOSTATIC_DECREASE_RATE_PER_HOUR,
    HOMEOSTATIC_INCREASE_RATE_PER_HOUR,
    HOMEOSTATIC_MAX_VALUE,
    HOMEOSTATIC_MIN_VALUE,
    HOMEOSTATIC_WEIGHT,
    IMMEDIATE_RELIEF_THRESHOLD,
    INERTIA_WEIGHT,
    INFO_ALERT_THRESHOLD,
    LAST_24_HOURS,
    LAST_30_DAYS,
    LAST_7_DAYS,
    LOW_RISK_THRESHOLD,
    MANDATORY_REST_THRESHOLD,
    MAX_RESIDENTS_PER_BATCH,
    MINIMUM_SLEEP_HOURS,
    MODERATE_RISK_PROCEDURE_MIN_EFFECTIVENESS,
    MODERATE_RISK_THRESHOLD,
    NEGLIGIBLE_RISK_THRESHOLD,
    OPTIMAL_SLEEP_HOURS,
    PERCENTAGE_DECIMAL_PLACES,
    REAL_TIME_UPDATE_SECONDS,
    REST_PERIOD_HOURS,
    STATE_UPDATE_INTERVAL_MINUTES,
    THRESHOLD_ACCEPTABLE,
    THRESHOLD_CRITICAL,
    THRESHOLD_FAA_CAUTION,
    THRESHOLD_FRA_HIGH_RISK,
    THRESHOLD_OPTIMAL,
    TOP_RISK_RESIDENTS_COUNT,
    TOP_UPCOMING_SHIFTS_COUNT,
    TREND_DECIMAL_PLACES,
    TREND_THRESHOLD_PERCENT,
    TREND_WINDOW_HOURS,
    UNSUPERVISED_WORK_MIN_EFFECTIVENESS,
    VERY_HIGH_RISK_THRESHOLD,
    WAKE_INERTIA_DURATION_HOURS,
    WAKE_INERTIA_MAX_IMPAIRMENT,
    WARNING_ALERT_THRESHOLD,
    WOCL_END_HOUR,
    WOCL_START_HOUR,
)


# ---------------------------------------------------------------------------
# Effectiveness thresholds — ordering
# ---------------------------------------------------------------------------


class TestEffectivenessThresholds:
    def test_optimal_highest(self):
        assert THRESHOLD_OPTIMAL > THRESHOLD_ACCEPTABLE

    def test_acceptable_above_faa(self):
        assert THRESHOLD_ACCEPTABLE > THRESHOLD_FAA_CAUTION

    def test_faa_above_fra(self):
        assert THRESHOLD_FAA_CAUTION > THRESHOLD_FRA_HIGH_RISK

    def test_fra_above_critical(self):
        assert THRESHOLD_FRA_HIGH_RISK > THRESHOLD_CRITICAL

    def test_all_positive(self):
        for val in [
            THRESHOLD_OPTIMAL,
            THRESHOLD_ACCEPTABLE,
            THRESHOLD_FAA_CAUTION,
            THRESHOLD_FRA_HIGH_RISK,
            THRESHOLD_CRITICAL,
        ]:
            assert val > 0

    def test_all_under_100(self):
        for val in [
            THRESHOLD_OPTIMAL,
            THRESHOLD_ACCEPTABLE,
            THRESHOLD_FAA_CAUTION,
            THRESHOLD_FRA_HIGH_RISK,
            THRESHOLD_CRITICAL,
        ]:
            assert val <= 100


# ---------------------------------------------------------------------------
# Alert severity mappings
# ---------------------------------------------------------------------------


class TestAlertSeverityMappings:
    def test_emergency_equals_critical(self):
        assert EMERGENCY_THRESHOLD == THRESHOLD_CRITICAL

    def test_critical_alert_equals_fra(self):
        assert CRITICAL_ALERT_THRESHOLD == THRESHOLD_FRA_HIGH_RISK

    def test_warning_equals_faa(self):
        assert WARNING_ALERT_THRESHOLD == THRESHOLD_FAA_CAUTION

    def test_info_equals_acceptable(self):
        assert INFO_ALERT_THRESHOLD == THRESHOLD_ACCEPTABLE

    def test_severity_ordering(self):
        assert EMERGENCY_THRESHOLD < CRITICAL_ALERT_THRESHOLD
        assert CRITICAL_ALERT_THRESHOLD < WARNING_ALERT_THRESHOLD
        assert WARNING_ALERT_THRESHOLD < INFO_ALERT_THRESHOLD


# ---------------------------------------------------------------------------
# Trend detection
# ---------------------------------------------------------------------------


class TestTrendDetection:
    def test_trend_window_positive(self):
        assert TREND_WINDOW_HOURS > 0

    def test_trend_threshold_positive(self):
        assert TREND_THRESHOLD_PERCENT > 0

    def test_history_retention_minimum(self):
        assert EFFECTIVENESS_HISTORY_HOURS >= 24

    def test_dedup_positive(self):
        assert ALERT_DEDUPLICATION_HOURS > 0


# ---------------------------------------------------------------------------
# Physiological constants
# ---------------------------------------------------------------------------


class TestPhysiological:
    def test_extended_before_critical(self):
        assert EXTENDED_WAKEFULNESS_HOURS < CRITICAL_WAKEFULNESS_HOURS

    def test_wocl_start_before_end(self):
        assert WOCL_START_HOUR < WOCL_END_HOUR

    def test_wocl_night_hours(self):
        # WOCL should be in early morning hours
        assert 0 <= WOCL_START_HOUR < 12
        assert 0 < WOCL_END_HOUR <= 12

    def test_min_sleep_below_optimal(self):
        assert MINIMUM_SLEEP_HOURS <= OPTIMAL_SLEEP_HOURS

    def test_rest_period_positive(self):
        assert REST_PERIOD_HOURS > 0


# ---------------------------------------------------------------------------
# Three-process model
# ---------------------------------------------------------------------------


class TestThreeProcessModel:
    def test_homeostatic_increase_positive(self):
        assert HOMEOSTATIC_INCREASE_RATE_PER_HOUR > 0

    def test_homeostatic_decrease_positive(self):
        assert HOMEOSTATIC_DECREASE_RATE_PER_HOUR > 0

    def test_homeostatic_min_less_than_max(self):
        assert HOMEOSTATIC_MIN_VALUE < HOMEOSTATIC_MAX_VALUE

    def test_circadian_period_24h(self):
        assert CIRCADIAN_PERIOD_HOURS == 24.0

    def test_circadian_amplitude_positive(self):
        assert CIRCADIAN_AMPLITUDE > 0

    def test_acrophase_valid_hour(self):
        assert 0 <= CIRCADIAN_ACROPHASE_HOUR < 24

    def test_wake_inertia_duration_positive(self):
        assert WAKE_INERTIA_DURATION_HOURS > 0

    def test_wake_inertia_impairment_positive(self):
        assert WAKE_INERTIA_MAX_IMPAIRMENT > 0


# ---------------------------------------------------------------------------
# Performance prediction weights
# ---------------------------------------------------------------------------


class TestPerformanceWeights:
    def test_weights_sum_to_one(self):
        total = HOMEOSTATIC_WEIGHT + CIRCADIAN_WEIGHT + INERTIA_WEIGHT
        assert abs(total - 1.0) < 1e-9

    def test_all_weights_positive(self):
        assert HOMEOSTATIC_WEIGHT > 0
        assert CIRCADIAN_WEIGHT > 0
        assert INERTIA_WEIGHT > 0

    def test_all_weights_under_one(self):
        assert HOMEOSTATIC_WEIGHT < 1.0
        assert CIRCADIAN_WEIGHT < 1.0
        assert INERTIA_WEIGHT < 1.0


# ---------------------------------------------------------------------------
# Risk level thresholds
# ---------------------------------------------------------------------------


class TestRiskLevelThresholds:
    def test_ordering(self):
        assert NEGLIGIBLE_RISK_THRESHOLD > LOW_RISK_THRESHOLD
        assert LOW_RISK_THRESHOLD > MODERATE_RISK_THRESHOLD
        assert MODERATE_RISK_THRESHOLD > HIGH_RISK_THRESHOLD
        assert HIGH_RISK_THRESHOLD > VERY_HIGH_RISK_THRESHOLD

    def test_negligible_matches_optimal(self):
        assert NEGLIGIBLE_RISK_THRESHOLD == THRESHOLD_OPTIMAL

    def test_low_matches_acceptable(self):
        assert LOW_RISK_THRESHOLD == THRESHOLD_ACCEPTABLE

    def test_moderate_matches_faa(self):
        assert MODERATE_RISK_THRESHOLD == THRESHOLD_FAA_CAUTION

    def test_high_matches_fra(self):
        assert HIGH_RISK_THRESHOLD == THRESHOLD_FRA_HIGH_RISK

    def test_very_high_matches_critical(self):
        assert VERY_HIGH_RISK_THRESHOLD == THRESHOLD_CRITICAL


# ---------------------------------------------------------------------------
# Dashboard constants
# ---------------------------------------------------------------------------


class TestDashboard:
    def test_time_windows(self):
        assert LAST_24_HOURS == 24
        assert LAST_7_DAYS == 7 * 24
        assert LAST_30_DAYS == 30 * 24

    def test_top_n_positive(self):
        assert TOP_RISK_RESIDENTS_COUNT > 0
        assert TOP_UPCOMING_SHIFTS_COUNT > 0

    def test_update_intervals_positive(self):
        assert REAL_TIME_UPDATE_SECONDS > 0
        assert BACKGROUND_UPDATE_SECONDS > 0

    def test_realtime_faster_than_background(self):
        assert REAL_TIME_UPDATE_SECONDS < BACKGROUND_UPDATE_SECONDS


# ---------------------------------------------------------------------------
# Monitoring constants
# ---------------------------------------------------------------------------


class TestMonitoring:
    def test_dedup_window_positive(self):
        assert DEDUPLICATION_WINDOW_HOURS > 0

    def test_batch_limits_positive(self):
        assert MAX_RESIDENTS_PER_BATCH > 0
        assert CONCURRENT_UPDATE_LIMIT > 0

    def test_concurrent_under_batch(self):
        assert CONCURRENT_UPDATE_LIMIT <= MAX_RESIDENTS_PER_BATCH

    def test_calculation_intervals_positive(self):
        assert EFFECTIVENESS_CALCULATION_INTERVAL_MINUTES > 0
        assert STATE_UPDATE_INTERVAL_MINUTES > 0


# ---------------------------------------------------------------------------
# Clinical implications
# ---------------------------------------------------------------------------


class TestClinicalImplications:
    def test_high_risk_above_moderate_risk(self):
        assert (
            HIGH_RISK_PROCEDURE_MIN_EFFECTIVENESS
            > MODERATE_RISK_PROCEDURE_MIN_EFFECTIVENESS
        )

    def test_unsupervised_above_supervision(self):
        assert UNSUPERVISED_WORK_MIN_EFFECTIVENESS > CLOSE_SUPERVISION_THRESHOLD

    def test_mandatory_rest_above_immediate_relief(self):
        assert MANDATORY_REST_THRESHOLD > IMMEDIATE_RELIEF_THRESHOLD

    def test_intervention_thresholds_descending(self):
        assert (
            UNSUPERVISED_WORK_MIN_EFFECTIVENESS
            > CLOSE_SUPERVISION_THRESHOLD
            > MANDATORY_REST_THRESHOLD
            > IMMEDIATE_RELIEF_THRESHOLD
        )


# ---------------------------------------------------------------------------
# Precision constants
# ---------------------------------------------------------------------------


class TestPrecision:
    def test_decimal_places_non_negative(self):
        assert EFFECTIVENESS_DECIMAL_PLACES >= 0
        assert TREND_DECIMAL_PLACES >= 0
        assert PERCENTAGE_DECIMAL_PLACES >= 0

    def test_effectiveness_reasonable(self):
        assert EFFECTIVENESS_DECIMAL_PLACES <= 6

    def test_trend_reasonable(self):
        assert TREND_DECIMAL_PLACES <= 6
