"""Tests for subharmonic detector - time crystal periodicity analysis (no DB)."""

from dataclasses import dataclass
from datetime import date, timedelta

import numpy as np
import pytest

from app.scheduling.periodicity.subharmonic_detector import (
    PeriodicityReport,
    SubharmonicDetector,
    TimeSeriesData,
    _generate_periodicity_recommendations,
    visualize_autocorrelation,
)


# ---------------------------------------------------------------------------
# Mock objects for assignment-dependent tests
# ---------------------------------------------------------------------------


@dataclass
class MockBlock:
    date: date


@dataclass
class MockAssignment:
    id: str
    person_id: str
    block: MockBlock


def _make_weekly_assignments(
    n_days: int = 56, people_per_day: int = 2
) -> list[MockAssignment]:
    """Create mock assignments with daily pattern for n_days."""
    assignments = []
    start = date(2024, 1, 1)
    for d in range(n_days):
        for p in range(people_per_day):
            assignments.append(
                MockAssignment(
                    id=f"a-{d}-{p}",
                    person_id=f"person-{p}",
                    block=MockBlock(date=start + timedelta(days=d)),
                )
            )
    return assignments


def _make_periodic_assignments(
    n_days: int = 56, period: int = 7
) -> list[MockAssignment]:
    """Create assignments with a clear periodic pattern."""
    assignments = []
    start = date(2024, 1, 1)
    for d in range(n_days):
        # Vary assignments by day of cycle to create periodicity
        n_people = 1 + (d % period)
        for p in range(n_people):
            assignments.append(
                MockAssignment(
                    id=f"a-{d}-{p}",
                    person_id=f"person-{p}",
                    block=MockBlock(date=start + timedelta(days=d)),
                )
            )
    return assignments


# ---------------------------------------------------------------------------
# PeriodicityReport dataclass
# ---------------------------------------------------------------------------


class TestPeriodicityReport:
    def test_construction(self):
        report = PeriodicityReport(
            fundamental_period=7.0,
            subharmonic_periods=[14.0, 28.0],
            periodicity_strength=0.75,
            autocorrelation=np.array([1.0, 0.5, 0.2]),
        )
        assert report.fundamental_period == 7.0
        assert len(report.subharmonic_periods) == 2
        assert report.periodicity_strength == 0.75

    def test_defaults(self):
        report = PeriodicityReport(
            fundamental_period=7.0,
            subharmonic_periods=[],
            periodicity_strength=0.5,
            autocorrelation=np.array([1.0]),
        )
        assert report.detected_patterns == []
        assert report.recommendations == []
        assert report.metadata == {}

    def test_str(self):
        report = PeriodicityReport(
            fundamental_period=7.0,
            subharmonic_periods=[14.0],
            periodicity_strength=0.75,
            autocorrelation=np.array([1.0]),
            detected_patterns=["Weekly pattern"],
        )
        s = str(report)
        assert "7.0" in s
        assert "Weekly pattern" in s
        assert "75" in s  # 0.75 formatted as percentage

    def test_str_no_patterns(self):
        report = PeriodicityReport(
            fundamental_period=7.0,
            subharmonic_periods=[],
            periodicity_strength=0.0,
            autocorrelation=np.array([1.0]),
        )
        s = str(report)
        assert "None" in s


# ---------------------------------------------------------------------------
# TimeSeriesData dataclass
# ---------------------------------------------------------------------------


class TestTimeSeriesData:
    def test_construction(self):
        ts = TimeSeriesData(
            values=np.array([1.0, 2.0, 3.0, 4.0]),
            dates=[date(2024, 1, d) for d in range(1, 5)],
        )
        assert len(ts.values) == 4
        assert ts.sampling_rate == 1.0

    def test_mismatched_lengths_raises(self):
        with pytest.raises(ValueError, match="Values length"):
            TimeSeriesData(
                values=np.array([1.0, 2.0]),
                dates=[date(2024, 1, 1)],
            )

    def test_too_short_raises(self):
        with pytest.raises(ValueError, match="too short"):
            TimeSeriesData(
                values=np.array([1.0, 2.0, 3.0]),
                dates=[date(2024, 1, d) for d in range(1, 4)],
            )

    def test_minimum_length(self):
        ts = TimeSeriesData(
            values=np.array([1.0, 2.0, 3.0, 4.0]),
            dates=[date(2024, 1, d) for d in range(1, 5)],
        )
        assert len(ts.values) == 4

    def test_default_person_ids(self):
        ts = TimeSeriesData(
            values=np.array([1.0, 2.0, 3.0, 4.0]),
            dates=[date(2024, 1, d) for d in range(1, 5)],
        )
        assert ts.person_ids == []


# ---------------------------------------------------------------------------
# _generate_periodicity_recommendations
# ---------------------------------------------------------------------------


class TestGenerateRecommendations:
    def _make_ts(self, n: int = 30) -> TimeSeriesData:
        """Create a simple time series for recommendations."""
        return TimeSeriesData(
            values=np.ones(n),
            dates=[date(2024, 1, 1) + timedelta(days=d) for d in range(n)],
        )

    def test_weak_periodicity(self):
        ts = self._make_ts()
        recs = _generate_periodicity_recommendations([7], 7, 0.2, ts)
        assert any("WEAK" in r for r in recs)

    def test_moderate_periodicity(self):
        ts = self._make_ts()
        recs = _generate_periodicity_recommendations([7], 7, 0.45, ts)
        assert any("MODERATE" in r for r in recs)

    def test_strong_periodicity(self):
        ts = self._make_ts()
        recs = _generate_periodicity_recommendations([7, 14, 28], 7, 0.8, ts)
        assert any("STRONG" in r for r in recs)

    def test_missing_base_period(self):
        ts = self._make_ts()
        recs = _generate_periodicity_recommendations([14], 7, 0.5, ts)
        assert any("Missing 7-day" in r for r in recs)

    def test_missing_28_day(self):
        ts = self._make_ts()
        recs = _generate_periodicity_recommendations([7], 7, 0.5, ts)
        assert any("28-day ACGME" in r for r in recs)

    def test_too_many_cycles(self):
        ts = self._make_ts()
        recs = _generate_periodicity_recommendations(
            [7, 14, 21, 28, 35, 42, 49], 7, 0.5, ts
        )
        assert any("Many cycles" in r for r in recs)

    def test_only_one_cycle(self):
        ts = self._make_ts()
        recs = _generate_periodicity_recommendations([7], 7, 0.5, ts)
        assert any("Only one" in r for r in recs)

    def test_high_variability(self):
        # Create a high-variance time series
        values = np.array([0.0] * 10 + [20.0] * 10 + [0.0] * 10, dtype=np.float64)
        ts = TimeSeriesData(
            values=values,
            dates=[date(2024, 1, 1) + timedelta(days=d) for d in range(30)],
        )
        recs = _generate_periodicity_recommendations([7], 7, 0.5, ts)
        assert any("variability" in r.lower() for r in recs)


# ---------------------------------------------------------------------------
# SubharmonicDetector
# ---------------------------------------------------------------------------


class TestSubharmonicDetector:
    def test_init(self):
        sd = SubharmonicDetector()
        assert sd.base_period == 7
        assert sd.min_significance == 0.3
        assert sd.history == []

    def test_custom_init(self):
        sd = SubharmonicDetector(base_period=14, min_significance=0.5)
        assert sd.base_period == 14
        assert sd.min_significance == 0.5

    def test_analyze_empty(self):
        sd = SubharmonicDetector()
        report = sd.analyze([])
        assert report.periodicity_strength == 0.0
        assert len(sd.history) == 1

    def test_analyze_records_history(self):
        sd = SubharmonicDetector()
        sd.analyze([])
        sd.analyze([])
        assert len(sd.history) == 2

    def test_compare_insufficient_history(self):
        sd = SubharmonicDetector()
        report = PeriodicityReport(
            fundamental_period=7.0,
            subharmonic_periods=[],
            periodicity_strength=0.5,
            autocorrelation=np.array([1.0]),
        )
        sd.history.append(report)
        result = sd.compare_to_previous(report)
        assert result["status"] == "insufficient_history"

    def test_compare_with_history(self):
        sd = SubharmonicDetector()
        r1 = PeriodicityReport(
            fundamental_period=7.0,
            subharmonic_periods=[14.0],
            periodicity_strength=0.5,
            autocorrelation=np.array([1.0]),
        )
        r2 = PeriodicityReport(
            fundamental_period=7.0,
            subharmonic_periods=[14.0, 28.0],
            periodicity_strength=0.7,
            autocorrelation=np.array([1.0]),
        )
        sd.history.extend([r1, r2])
        result = sd.compare_to_previous(r2)
        assert result["status"] == "compared"
        assert result["strength_change"] == pytest.approx(0.2)
        assert 28.0 in result["new_cycles"]

    def test_compare_lost_cycles(self):
        sd = SubharmonicDetector()
        r1 = PeriodicityReport(
            fundamental_period=7.0,
            subharmonic_periods=[14.0, 28.0],
            periodicity_strength=0.6,
            autocorrelation=np.array([1.0]),
        )
        r2 = PeriodicityReport(
            fundamental_period=7.0,
            subharmonic_periods=[14.0],
            periodicity_strength=0.5,
            autocorrelation=np.array([1.0]),
        )
        sd.history.extend([r1, r2])
        result = sd.compare_to_previous(r2)
        assert 28.0 in result["lost_cycles"]

    def test_trend_improving(self):
        sd = SubharmonicDetector()
        for strength in [0.3, 0.5, 0.7]:
            sd.history.append(
                PeriodicityReport(
                    fundamental_period=7.0,
                    subharmonic_periods=[],
                    periodicity_strength=strength,
                    autocorrelation=np.array([1.0]),
                )
            )
        result = sd.compare_to_previous(sd.history[-1])
        assert result["strength_trend"] == "improving"

    def test_trend_declining(self):
        sd = SubharmonicDetector()
        for strength in [0.7, 0.5, 0.3]:
            sd.history.append(
                PeriodicityReport(
                    fundamental_period=7.0,
                    subharmonic_periods=[],
                    periodicity_strength=strength,
                    autocorrelation=np.array([1.0]),
                )
            )
        result = sd.compare_to_previous(sd.history[-1])
        assert result["strength_trend"] == "declining"

    def test_trend_stable(self):
        sd = SubharmonicDetector()
        for strength in [0.5, 0.7, 0.5]:
            sd.history.append(
                PeriodicityReport(
                    fundamental_period=7.0,
                    subharmonic_periods=[],
                    periodicity_strength=strength,
                    autocorrelation=np.array([1.0]),
                )
            )
        result = sd.compare_to_previous(sd.history[-1])
        assert result["strength_trend"] == "stable"


# ---------------------------------------------------------------------------
# SubharmonicDetector — get_stability_score
# ---------------------------------------------------------------------------


class TestGetStabilityScore:
    def test_no_history(self):
        sd = SubharmonicDetector()
        assert sd.get_stability_score() == 0.0

    def test_single_report_high_strength(self):
        sd = SubharmonicDetector()
        sd.history.append(
            PeriodicityReport(
                fundamental_period=7.0,
                subharmonic_periods=[14.0],
                periodicity_strength=1.0,
                autocorrelation=np.array([1.0]),
            )
        )
        score = sd.get_stability_score()
        assert 0.0 < score <= 1.0

    def test_consistent_reports_high_score(self):
        sd = SubharmonicDetector()
        for _ in range(5):
            sd.history.append(
                PeriodicityReport(
                    fundamental_period=7.0,
                    subharmonic_periods=[14.0, 28.0],
                    periodicity_strength=0.8,
                    autocorrelation=np.array([1.0]),
                )
            )
        score = sd.get_stability_score()
        assert score > 0.5

    def test_inconsistent_reports_lower_score(self):
        sd = SubharmonicDetector()
        for n_sub in [0, 5, 0, 5, 0]:
            sd.history.append(
                PeriodicityReport(
                    fundamental_period=7.0,
                    subharmonic_periods=[float(i) for i in range(n_sub)],
                    periodicity_strength=0.3,
                    autocorrelation=np.array([1.0]),
                )
            )
        score_inconsistent = sd.get_stability_score()

        sd2 = SubharmonicDetector()
        for _ in range(5):
            sd2.history.append(
                PeriodicityReport(
                    fundamental_period=7.0,
                    subharmonic_periods=[14.0],
                    periodicity_strength=0.8,
                    autocorrelation=np.array([1.0]),
                )
            )
        score_consistent = sd2.get_stability_score()
        assert score_consistent > score_inconsistent

    def test_bounded_0_1(self):
        sd = SubharmonicDetector()
        sd.history.append(
            PeriodicityReport(
                fundamental_period=7.0,
                subharmonic_periods=[],
                periodicity_strength=0.0,
                autocorrelation=np.array([1.0]),
            )
        )
        score = sd.get_stability_score()
        assert 0.0 <= score <= 1.0


# ---------------------------------------------------------------------------
# visualize_autocorrelation
# ---------------------------------------------------------------------------


class TestVisualizeAutocorrelation:
    def test_returns_string(self):
        autocorr = np.array([1.0, 0.8, 0.5, 0.2, -0.1])
        result = visualize_autocorrelation(autocorr, max_lag=5)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_contains_title(self):
        autocorr = np.array([1.0, 0.5, 0.2, 0.1, 0.0])
        result = visualize_autocorrelation(autocorr, title="Test ACF")
        assert "Test ACF" in result

    def test_weekly_markers(self):
        autocorr = np.ones(14)
        result = visualize_autocorrelation(autocorr, max_lag=14)
        # Lag 0 and 7 should have "*" markers
        assert "*" in result

    def test_negative_values(self):
        autocorr = np.array([1.0, -0.5, 0.2, -0.1, 0.0])
        result = visualize_autocorrelation(autocorr, max_lag=5)
        # Should contain negative values formatted
        assert "-0." in result

    def test_max_lag_capped(self):
        autocorr = np.array([1.0, 0.5, 0.3, 0.1, 0.0])
        result = visualize_autocorrelation(autocorr, max_lag=100)
        # Should only show up to len(autocorr)
        lines = result.strip().split("\n")
        # Title + separator + 5 data lines + separator = 8
        assert len(lines) == 8


# ---------------------------------------------------------------------------
# Integration: analyze with mock assignments
# ---------------------------------------------------------------------------


class TestAnalyzeWithMockAssignments:
    def test_analyze_periodic_assignments(self):
        sd = SubharmonicDetector()
        assignments = _make_periodic_assignments(n_days=56, period=7)
        report = sd.analyze(assignments)
        assert isinstance(report, PeriodicityReport)
        assert report.fundamental_period == 7.0
        assert report.periodicity_strength > 0.0

    def test_analyze_uniform_assignments(self):
        sd = SubharmonicDetector()
        assignments = _make_weekly_assignments(n_days=56, people_per_day=2)
        report = sd.analyze(assignments)
        assert isinstance(report, PeriodicityReport)

    def test_analyze_metadata_populated(self):
        sd = SubharmonicDetector()
        assignments = _make_weekly_assignments(n_days=28)
        report = sd.analyze(assignments)
        assert "n_assignments" in report.metadata
        assert "n_days" in report.metadata
        assert "date_range" in report.metadata
