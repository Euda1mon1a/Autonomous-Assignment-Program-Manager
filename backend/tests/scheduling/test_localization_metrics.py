"""Tests for localization metrics tracking (pure logic, no DB required)."""

from collections import defaultdict
from datetime import datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.scheduling.anderson_localization import (
    Disruption,
    DisruptionType,
    LocalizationRegion,
)
from app.scheduling.localization_metrics import (
    LocalizationEvent,
    LocalizationMetrics,
    LocalizationMetricsResponse,
    LocalizationMetricsTracker,
    LocalizationQuality,
    LocalizationRegionResponse,
)


# ==================== Helpers ====================


def _make_region(
    size: int = 50,
    localization_length: float = 5.0,
    barrier_strength: float = 0.7,
    escape_probability: float = 0.1,
    region_type: str = "localized",
) -> LocalizationRegion:
    """Build a LocalizationRegion with deterministic UUID sets."""
    assignments = {uuid4() for _ in range(size)}
    epicenter = {uuid4()}
    boundary = {uuid4() for _ in range(3)}
    return LocalizationRegion(
        affected_assignments=assignments,
        epicenter_blocks=epicenter,
        boundary_blocks=boundary,
        localization_length=localization_length,
        barrier_strength=barrier_strength,
        escape_probability=escape_probability,
        region_type=region_type,
    )


def _make_disruption(
    dtype: DisruptionType = DisruptionType.LEAVE_REQUEST,
) -> Disruption:
    """Build a minimal Disruption."""
    return Disruption(
        disruption_type=dtype,
        person_id=uuid4(),
        block_ids=[uuid4()],
    )


# ==================== Enum Tests ====================


class TestLocalizationQuality:
    """Test LocalizationQuality enum."""

    def test_all_values(self):
        expected = {"excellent", "good", "fair", "poor"}
        actual = {q.value for q in LocalizationQuality}
        assert actual == expected

    def test_count(self):
        assert len(LocalizationQuality) == 4

    def test_is_string_enum(self):
        assert LocalizationQuality.EXCELLENT == "excellent"
        assert LocalizationQuality.POOR == "poor"


# ==================== LocalizationEvent Dataclass Tests ====================


class TestLocalizationEvent:
    """Test LocalizationEvent dataclass."""

    def test_basic_construction(self):
        region = _make_region()
        event = LocalizationEvent(
            timestamp=datetime(2025, 6, 1, 12, 0, 0),
            disruption_type=DisruptionType.LEAVE_REQUEST,
            region=region,
            computation_time_ms=125.5,
            quality=LocalizationQuality.EXCELLENT,
        )
        assert event.disruption_type == DisruptionType.LEAVE_REQUEST
        assert event.computation_time_ms == 125.5
        assert event.quality == LocalizationQuality.EXCELLENT

    def test_default_metadata_empty(self):
        region = _make_region()
        event = LocalizationEvent(
            timestamp=datetime.utcnow(),
            disruption_type=DisruptionType.SWAP_REQUEST,
            region=region,
            computation_time_ms=10.0,
            quality=LocalizationQuality.GOOD,
        )
        assert event.metadata == {}

    def test_custom_metadata(self):
        region = _make_region()
        event = LocalizationEvent(
            timestamp=datetime.utcnow(),
            disruption_type=DisruptionType.EMERGENCY,
            region=region,
            computation_time_ms=200.0,
            quality=LocalizationQuality.POOR,
            metadata={"escalated": True},
        )
        assert event.metadata["escalated"] is True


# ==================== LocalizationMetrics Dataclass Tests ====================


class TestLocalizationMetrics:
    """Test LocalizationMetrics dataclass."""

    def test_all_defaults_zero(self):
        m = LocalizationMetrics()
        assert m.total_events == 0
        assert m.localized_count == 0
        assert m.extended_count == 0
        assert m.global_count == 0
        assert m.avg_region_size == 0.0
        assert m.avg_localization_length == 0.0
        assert m.avg_barrier_strength == 0.0
        assert m.avg_escape_probability == 0.0
        assert m.avg_computation_time_ms == 0.0
        assert m.p95_computation_time_ms == 0.0
        assert m.p99_computation_time_ms == 0.0

    def test_quality_distribution_default_empty(self):
        m = LocalizationMetrics()
        assert len(m.quality_distribution) == 0

    def test_metrics_by_type_default_empty(self):
        m = LocalizationMetrics()
        assert len(m.metrics_by_type) == 0

    def test_repr_zero_events(self):
        m = LocalizationMetrics()
        r = repr(m)
        assert "total=0" in r
        assert "localized_rate=0.0%" in r

    def test_repr_with_events(self):
        m = LocalizationMetrics()
        m.total_events = 10
        m.localized_count = 7
        m.avg_region_size = 42.0
        m.avg_localization_length = 5.2
        r = repr(m)
        assert "total=10" in r
        assert "localized_rate=70.0%" in r
        assert "avg_size=42" in r
        assert "avg_length=5.2d" in r


# ==================== Quality Classification Tests ====================


class TestQualityClassification:
    """Test _classify_quality via the tracker."""

    def _classify(self, region: LocalizationRegion) -> LocalizationQuality:
        tracker = LocalizationMetricsTracker()
        return tracker._classify_quality(region)

    def test_excellent_small_scope_strong_barrier(self):
        # < 10% scope (size < 100 of 1000), barrier > 0.6, escape < 0.2
        region = _make_region(
            size=50,
            barrier_strength=0.8,
            escape_probability=0.1,
        )
        assert self._classify(region) == LocalizationQuality.EXCELLENT

    def test_good_moderate_scope(self):
        # 10-20% scope (size 100-200), barrier > 0.4, escape < 0.4
        region = _make_region(
            size=150,
            barrier_strength=0.5,
            escape_probability=0.3,
        )
        assert self._classify(region) == LocalizationQuality.GOOD

    def test_fair_larger_scope(self):
        # 20-40% scope (size 200-400), escape < 0.6
        region = _make_region(
            size=300,
            barrier_strength=0.3,
            escape_probability=0.4,
        )
        assert self._classify(region) == LocalizationQuality.FAIR

    def test_poor_large_scope(self):
        # > 40% scope (size > 400)
        region = _make_region(
            size=500,
            barrier_strength=0.2,
            escape_probability=0.7,
        )
        assert self._classify(region) == LocalizationQuality.POOR

    def test_poor_high_escape_probability(self):
        # Small scope but escape > 0.6
        region = _make_region(
            size=300,
            barrier_strength=0.3,
            escape_probability=0.65,
        )
        assert self._classify(region) == LocalizationQuality.POOR

    def test_excellent_boundary_values(self):
        # Exactly at boundary: size=99 (< 10%), barrier=0.61, escape=0.19
        region = _make_region(
            size=99,
            barrier_strength=0.61,
            escape_probability=0.19,
        )
        assert self._classify(region) == LocalizationQuality.EXCELLENT

    def test_not_excellent_at_boundary_scope(self):
        # size=100 (exactly 10%, NOT < 10%)
        region = _make_region(
            size=100,
            barrier_strength=0.8,
            escape_probability=0.1,
        )
        assert self._classify(region) != LocalizationQuality.EXCELLENT


# ==================== Tracker Tests ====================


class TestLocalizationMetricsTracker:
    """Test LocalizationMetricsTracker."""

    def test_initial_state(self):
        tracker = LocalizationMetricsTracker()
        assert tracker.window_size == 100
        assert tracker.events == []
        assert tracker.metrics.total_events == 0

    def test_custom_window_size(self):
        tracker = LocalizationMetricsTracker(window_size=10)
        assert tracker.window_size == 10

    def test_record_single_event(self):
        tracker = LocalizationMetricsTracker()
        disruption = _make_disruption()
        region = _make_region(size=50, region_type="localized")
        event = tracker.record_event(disruption, region, 100.0)

        assert isinstance(event, LocalizationEvent)
        assert event.disruption_type == DisruptionType.LEAVE_REQUEST
        assert event.computation_time_ms == 100.0
        assert len(tracker.events) == 1
        assert tracker.metrics.total_events == 1

    def test_localized_count(self):
        tracker = LocalizationMetricsTracker()
        for _ in range(3):
            tracker.record_event(
                _make_disruption(),
                _make_region(region_type="localized"),
                50.0,
            )
        assert tracker.metrics.localized_count == 3

    def test_extended_count(self):
        tracker = LocalizationMetricsTracker()
        tracker.record_event(
            _make_disruption(),
            _make_region(region_type="extended"),
            50.0,
        )
        assert tracker.metrics.extended_count == 1

    def test_global_count(self):
        tracker = LocalizationMetricsTracker()
        tracker.record_event(
            _make_disruption(),
            _make_region(region_type="global"),
            50.0,
        )
        assert tracker.metrics.global_count == 1

    def test_window_trimming(self):
        tracker = LocalizationMetricsTracker(window_size=5)
        for _ in range(10):
            tracker.record_event(
                _make_disruption(),
                _make_region(),
                50.0,
            )
        assert len(tracker.events) == 5
        assert tracker.metrics.total_events == 5

    def test_avg_computation_time(self):
        tracker = LocalizationMetricsTracker()
        tracker.record_event(_make_disruption(), _make_region(), 100.0)
        tracker.record_event(_make_disruption(), _make_region(), 200.0)
        assert tracker.metrics.avg_computation_time_ms == pytest.approx(150.0)

    def test_avg_barrier_strength(self):
        tracker = LocalizationMetricsTracker()
        tracker.record_event(
            _make_disruption(),
            _make_region(barrier_strength=0.6),
            50.0,
        )
        tracker.record_event(
            _make_disruption(),
            _make_region(barrier_strength=0.8),
            50.0,
        )
        assert tracker.metrics.avg_barrier_strength == pytest.approx(0.7)

    def test_percentile_computation(self):
        tracker = LocalizationMetricsTracker()
        # Add 20 events with known computation times
        for i in range(20):
            tracker.record_event(
                _make_disruption(),
                _make_region(),
                float(i + 1) * 10.0,  # 10, 20, ..., 200
            )
        # p95 index = int(0.95 * 20) = 19 -> value = 200.0
        assert tracker.metrics.p95_computation_time_ms == 200.0
        # p99 index = int(0.99 * 20) = 19 -> value = 200.0
        assert tracker.metrics.p99_computation_time_ms == 200.0

    def test_quality_distribution_tracked(self):
        tracker = LocalizationMetricsTracker()
        # Excellent quality event
        tracker.record_event(
            _make_disruption(),
            _make_region(size=50, barrier_strength=0.8, escape_probability=0.1),
            50.0,
        )
        dist = tracker.metrics.quality_distribution
        assert dist[LocalizationQuality.EXCELLENT] == 1

    def test_per_disruption_type_metrics(self):
        tracker = LocalizationMetricsTracker()
        for _ in range(3):
            tracker.record_event(
                _make_disruption(DisruptionType.LEAVE_REQUEST),
                _make_region(region_type="localized"),
                100.0,
            )
        tracker.record_event(
            _make_disruption(DisruptionType.EMERGENCY),
            _make_region(region_type="extended"),
            200.0,
        )

        by_type = tracker.metrics.metrics_by_type
        assert DisruptionType.LEAVE_REQUEST in by_type
        assert by_type[DisruptionType.LEAVE_REQUEST]["count"] == 3
        assert by_type[DisruptionType.LEAVE_REQUEST][
            "localization_rate"
        ] == pytest.approx(1.0)
        assert DisruptionType.EMERGENCY in by_type
        assert by_type[DisruptionType.EMERGENCY]["count"] == 1
        assert by_type[DisruptionType.EMERGENCY]["localization_rate"] == pytest.approx(
            0.0
        )

    def test_event_metadata_includes_person_id(self):
        tracker = LocalizationMetricsTracker()
        disruption = _make_disruption()
        event = tracker.record_event(disruption, _make_region(), 50.0)
        assert event.metadata["person_id"] == str(disruption.person_id)

    def test_event_metadata_null_person_id(self):
        tracker = LocalizationMetricsTracker()
        disruption = Disruption(
            disruption_type=DisruptionType.ROTATION_CHANGE,
            person_id=None,
            block_ids=[uuid4()],
        )
        event = tracker.record_event(disruption, _make_region(), 50.0)
        assert event.metadata["person_id"] is None

    def test_event_metadata_block_count(self):
        tracker = LocalizationMetricsTracker()
        block_ids = [uuid4(), uuid4(), uuid4()]
        disruption = Disruption(
            disruption_type=DisruptionType.SWAP_REQUEST,
            block_ids=block_ids,
        )
        event = tracker.record_event(disruption, _make_region(), 50.0)
        assert event.metadata["num_blocks"] == 3


# ==================== Accessor Method Tests ====================


class TestTrackerAccessors:
    """Test get_localization_rate, get_quality_distribution, export_metrics."""

    def test_localization_rate_empty(self):
        tracker = LocalizationMetricsTracker()
        assert tracker.get_localization_rate() == 0.0

    def test_localization_rate_all_localized(self):
        tracker = LocalizationMetricsTracker()
        for _ in range(5):
            tracker.record_event(
                _make_disruption(),
                _make_region(region_type="localized"),
                50.0,
            )
        assert tracker.get_localization_rate() == pytest.approx(1.0)

    def test_localization_rate_mixed(self):
        tracker = LocalizationMetricsTracker()
        for _ in range(3):
            tracker.record_event(
                _make_disruption(),
                _make_region(region_type="localized"),
                50.0,
            )
        for _ in range(2):
            tracker.record_event(
                _make_disruption(),
                _make_region(region_type="extended"),
                50.0,
            )
        assert tracker.get_localization_rate() == pytest.approx(0.6)

    def test_quality_distribution_empty(self):
        tracker = LocalizationMetricsTracker()
        assert tracker.get_quality_distribution() == {}

    def test_quality_distribution_percentages(self):
        tracker = LocalizationMetricsTracker()
        # 2 excellent events
        for _ in range(2):
            tracker.record_event(
                _make_disruption(),
                _make_region(size=50, barrier_strength=0.8, escape_probability=0.1),
                50.0,
            )
        # 2 poor events
        for _ in range(2):
            tracker.record_event(
                _make_disruption(),
                _make_region(size=500, barrier_strength=0.2, escape_probability=0.7),
                50.0,
            )
        dist = tracker.get_quality_distribution()
        assert dist["excellent"] == pytest.approx(50.0)
        assert dist["poor"] == pytest.approx(50.0)

    def test_export_metrics_structure(self):
        tracker = LocalizationMetricsTracker()
        tracker.record_event(
            _make_disruption(),
            _make_region(region_type="localized"),
            100.0,
        )
        export = tracker.export_metrics()
        assert "summary" in export
        assert "region_types" in export
        assert "quality_distribution" in export
        assert "performance" in export
        assert "by_disruption_type" in export

    def test_export_summary_keys(self):
        tracker = LocalizationMetricsTracker()
        tracker.record_event(
            _make_disruption(),
            _make_region(),
            100.0,
        )
        summary = tracker.export_metrics()["summary"]
        assert "total_events" in summary
        assert "localization_rate" in summary
        assert "avg_region_size" in summary
        assert "avg_localization_length" in summary
        assert "avg_barrier_strength" in summary

    def test_export_region_types(self):
        tracker = LocalizationMetricsTracker()
        tracker.record_event(
            _make_disruption(),
            _make_region(region_type="localized"),
            50.0,
        )
        rt = tracker.export_metrics()["region_types"]
        assert rt["localized"] == 1
        assert rt["extended"] == 0
        assert rt["global"] == 0

    def test_export_by_disruption_type_uses_string_keys(self):
        tracker = LocalizationMetricsTracker()
        tracker.record_event(
            _make_disruption(DisruptionType.FACULTY_ABSENCE),
            _make_region(),
            50.0,
        )
        by_type = tracker.export_metrics()["by_disruption_type"]
        assert "faculty_absence" in by_type


# ==================== Pydantic Response Model Tests ====================


class TestLocalizationRegionResponse:
    """Test LocalizationRegionResponse Pydantic model."""

    def test_valid_construction(self):
        r = LocalizationRegionResponse(
            region_size=42,
            epicenter_blocks=["block-1"],
            localization_length=5.2,
            barrier_strength=0.68,
            escape_probability=0.15,
            region_type="localized",
            is_localized=True,
        )
        assert r.region_size == 42
        assert r.barrier_strength == 0.68

    def test_barrier_strength_boundary_zero(self):
        r = LocalizationRegionResponse(
            region_size=1,
            epicenter_blocks=[],
            localization_length=1.0,
            barrier_strength=0.0,
            escape_probability=0.5,
            region_type="extended",
            is_localized=False,
        )
        assert r.barrier_strength == 0.0

    def test_barrier_strength_boundary_one(self):
        r = LocalizationRegionResponse(
            region_size=1,
            epicenter_blocks=[],
            localization_length=1.0,
            barrier_strength=1.0,
            escape_probability=0.5,
            region_type="extended",
            is_localized=False,
        )
        assert r.barrier_strength == 1.0

    def test_barrier_strength_rejects_above_one(self):
        with pytest.raises(ValidationError):
            LocalizationRegionResponse(
                region_size=1,
                epicenter_blocks=[],
                localization_length=1.0,
                barrier_strength=1.1,
                escape_probability=0.5,
                region_type="localized",
                is_localized=True,
            )

    def test_escape_probability_rejects_below_zero(self):
        with pytest.raises(ValidationError):
            LocalizationRegionResponse(
                region_size=1,
                epicenter_blocks=[],
                localization_length=1.0,
                barrier_strength=0.5,
                escape_probability=-0.1,
                region_type="localized",
                is_localized=True,
            )

    def test_default_metadata_empty(self):
        r = LocalizationRegionResponse(
            region_size=10,
            epicenter_blocks=["b1"],
            localization_length=3.0,
            barrier_strength=0.5,
            escape_probability=0.2,
            region_type="localized",
            is_localized=True,
        )
        assert r.metadata == {}


class TestLocalizationMetricsResponse:
    """Test LocalizationMetricsResponse Pydantic model."""

    def test_valid_construction(self):
        r = LocalizationMetricsResponse(
            summary={"total_events": 10, "localization_rate": 0.8},
            region_types={"localized": 8, "extended": 1, "global": 1},
            quality_distribution={"excellent": 50.0, "good": 30.0},
            performance={"avg_computation_time_ms": 100.0},
            by_disruption_type={},
        )
        assert r.summary["total_events"] == 10
        assert r.region_types["localized"] == 8

    def test_serialization_round_trip(self):
        r = LocalizationMetricsResponse(
            summary={"localization_rate": 0.75},
            region_types={"localized": 5},
            quality_distribution={"good": 60.0},
            performance={"p95_computation_time_ms": 350.0},
            by_disruption_type={"leave_request": {"count": 3}},
        )
        d = r.model_dump()
        r2 = LocalizationMetricsResponse(**d)
        assert r2.summary == r.summary
        assert r2.by_disruption_type == r.by_disruption_type
