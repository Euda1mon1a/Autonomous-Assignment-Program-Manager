"""Tests for holographic visualization data export (no DB)."""

from __future__ import annotations

from datetime import datetime, date, timedelta
from uuid import uuid4

import pytest

from app.frms.holographic_export import (
    FatigueTimeSeries,
    HolographicExporter,
    SpatialFatigueMap,
    TemporalDynamicsData,
)


# ---------------------------------------------------------------------------
# FatigueTimeSeries — construction & to_dict
# ---------------------------------------------------------------------------


class TestFatigueTimeSeriesConstruction:
    def test_defaults(self):
        ts = FatigueTimeSeries(person_id="p1", person_name="Alice")
        assert ts.person_id == "p1"
        assert ts.person_name == "Alice"
        assert ts.pgy_level is None
        assert ts.data_points == []
        assert ts.sample_interval_minutes == 30
        assert ts.min_effectiveness == 100.0
        assert ts.max_effectiveness == 100.0

    def test_with_pgy_level(self):
        ts = FatigueTimeSeries(person_id="p1", person_name="Bob", pgy_level=3)
        assert ts.pgy_level == 3

    def test_with_data_points(self):
        pts = [{"timestamp": "2026-01-01T00:00:00", "effectiveness": 85.0}]
        ts = FatigueTimeSeries(person_id="p1", person_name="C", data_points=pts)
        assert len(ts.data_points) == 1


class TestFatigueTimeSeriesToDict:
    def test_returns_dict(self):
        ts = FatigueTimeSeries(person_id="p1", person_name="Alice")
        result = ts.to_dict()
        assert isinstance(result, dict)

    def test_contains_person_info(self):
        ts = FatigueTimeSeries(person_id="p1", person_name="Alice", pgy_level=2)
        d = ts.to_dict()
        assert d["person_id"] == "p1"
        assert d["person_name"] == "Alice"
        assert d["pgy_level"] == 2

    def test_time_range_with_datetimes(self):
        start = datetime(2026, 1, 1, 8, 0)
        end = datetime(2026, 1, 1, 20, 0)
        ts = FatigueTimeSeries(
            person_id="p1",
            person_name="A",
            start_time=start,
            end_time=end,
        )
        d = ts.to_dict()
        assert d["time_range"]["start"] == start.isoformat()
        assert d["time_range"]["end"] == end.isoformat()

    def test_time_range_none(self):
        ts = FatigueTimeSeries(person_id="p1", person_name="A")
        d = ts.to_dict()
        assert d["time_range"]["start"] is None
        assert d["time_range"]["end"] is None

    def test_statistics_section(self):
        ts = FatigueTimeSeries(
            person_id="p1",
            person_name="A",
            min_effectiveness=65.3,
            max_effectiveness=98.7,
            data_points=[{}, {}, {}],
        )
        d = ts.to_dict()
        assert d["statistics"]["min_effectiveness"] == 65.3
        assert d["statistics"]["max_effectiveness"] == 98.7
        assert d["statistics"]["data_points_count"] == 3

    def test_color_gradient_included(self):
        ts = FatigueTimeSeries(
            person_id="p1",
            person_name="A",
            color_gradient=["#ff0000", "#00ff00"],
        )
        d = ts.to_dict()
        assert d["color_gradient"] == ["#ff0000", "#00ff00"]


# ---------------------------------------------------------------------------
# TemporalDynamicsData — construction & to_dict
# ---------------------------------------------------------------------------


class TestTemporalDynamicsDataConstruction:
    def test_defaults(self):
        now = datetime.now()
        td = TemporalDynamicsData(export_time=now, analysis_period_days=14)
        assert td.export_time == now
        assert td.analysis_period_days == 14
        assert td.circadian_pattern == []
        assert td.weekly_pattern == []
        assert td.heatmap_data == []


class TestTemporalDynamicsDataToDict:
    def test_returns_dict(self):
        now = datetime.now()
        td = TemporalDynamicsData(export_time=now, analysis_period_days=7)
        result = td.to_dict()
        assert isinstance(result, dict)

    def test_export_time_serialized(self):
        now = datetime(2026, 1, 15, 10, 30)
        td = TemporalDynamicsData(export_time=now, analysis_period_days=7)
        d = td.to_dict()
        assert d["export_time"] == now.isoformat()

    def test_patterns_section(self):
        now = datetime.now()
        td = TemporalDynamicsData(
            export_time=now,
            analysis_period_days=14,
            circadian_pattern=[{"hour": 0, "avg_effectiveness": 75.0}],
            weekly_pattern=[{"day_of_week": 0, "avg_effectiveness": 85.0}],
            resonance_patterns=[{"type": "wocl_fatigue"}],
        )
        d = td.to_dict()
        assert len(d["patterns"]["circadian"]) == 1
        assert len(d["patterns"]["weekly"]) == 1
        assert len(d["patterns"]["resonance"]) == 1

    def test_heatmap_labels(self):
        now = datetime.now()
        td = TemporalDynamicsData(export_time=now, analysis_period_days=7)
        d = td.to_dict()
        assert len(d["heatmap"]["x_labels"]) == 24
        assert d["heatmap"]["x_labels"][0] == "00:00"
        assert d["heatmap"]["x_labels"][23] == "23:00"
        assert len(d["heatmap"]["y_labels"]) == 7
        assert d["heatmap"]["y_labels"][0] == "Mon"


# ---------------------------------------------------------------------------
# SpatialFatigueMap — construction & to_dict
# ---------------------------------------------------------------------------


class TestSpatialFatigueMapConstruction:
    def test_defaults(self):
        now = datetime.now()
        sfm = SpatialFatigueMap(export_time=now)
        assert sfm.export_time == now
        assert sfm.voxels == []
        assert sfm.x_labels == []


class TestSpatialFatigueMapToDict:
    def test_returns_dict(self):
        now = datetime.now()
        sfm = SpatialFatigueMap(export_time=now)
        result = sfm.to_dict()
        assert isinstance(result, dict)

    def test_grid_dimensions(self):
        now = datetime.now()
        sfm = SpatialFatigueMap(
            export_time=now,
            grid_dimensions={"x": 5, "y": 3, "z": 2},
        )
        d = sfm.to_dict()
        assert d["grid_dimensions"]["x"] == 5

    def test_voxel_count(self):
        now = datetime.now()
        sfm = SpatialFatigueMap(
            export_time=now,
            voxels=[{"position": {"x": 0, "y": 0, "z": 0}}] * 10,
        )
        d = sfm.to_dict()
        assert d["voxel_count"] == 10

    def test_axis_labels(self):
        now = datetime.now()
        sfm = SpatialFatigueMap(
            export_time=now,
            x_labels=["2026-01-01", "2026-01-02"],
            y_labels=["Alice", "Bob"],
            z_labels=["Clinic", "Inpatient"],
        )
        d = sfm.to_dict()
        assert d["axes"]["x_labels"] == ["2026-01-01", "2026-01-02"]
        assert d["axes"]["y_labels"] == ["Alice", "Bob"]
        assert d["axes"]["z_labels"] == ["Clinic", "Inpatient"]


# ---------------------------------------------------------------------------
# HolographicExporter — construction & class constants
# ---------------------------------------------------------------------------


class TestHolographicExporterInit:
    def test_creates_instance(self):
        exporter = HolographicExporter()
        assert exporter is not None

    def test_has_model(self):
        exporter = HolographicExporter()
        assert exporter.model is not None

    def test_has_predictor(self):
        exporter = HolographicExporter()
        assert exporter.predictor is not None

    def test_effectiveness_colors_has_five_levels(self):
        assert len(HolographicExporter.EFFECTIVENESS_COLORS) == 5

    def test_effectiveness_colors_keys(self):
        expected = {"optimal", "acceptable", "caution", "high_risk", "critical"}
        assert set(HolographicExporter.EFFECTIVENESS_COLORS.keys()) == expected

    def test_all_colors_are_hex(self):
        for color in HolographicExporter.EFFECTIVENESS_COLORS.values():
            assert color.startswith("#")
            assert len(color) == 7


# ---------------------------------------------------------------------------
# HolographicExporter._effectiveness_to_color
# ---------------------------------------------------------------------------


class TestEffectivenessToColor:
    def setup_method(self):
        self.exporter = HolographicExporter()
        self.colors = HolographicExporter.EFFECTIVENESS_COLORS

    def test_optimal_100(self):
        assert self.exporter._effectiveness_to_color(100) == self.colors["optimal"]

    def test_optimal_95(self):
        assert self.exporter._effectiveness_to_color(95) == self.colors["optimal"]

    def test_acceptable_94(self):
        assert self.exporter._effectiveness_to_color(94) == self.colors["acceptable"]

    def test_acceptable_85(self):
        assert self.exporter._effectiveness_to_color(85) == self.colors["acceptable"]

    def test_caution_84(self):
        assert self.exporter._effectiveness_to_color(84) == self.colors["caution"]

    def test_caution_77(self):
        assert self.exporter._effectiveness_to_color(77) == self.colors["caution"]

    def test_high_risk_76(self):
        assert self.exporter._effectiveness_to_color(76) == self.colors["high_risk"]

    def test_high_risk_70(self):
        assert self.exporter._effectiveness_to_color(70) == self.colors["high_risk"]

    def test_critical_69(self):
        assert self.exporter._effectiveness_to_color(69) == self.colors["critical"]

    def test_critical_0(self):
        assert self.exporter._effectiveness_to_color(0) == self.colors["critical"]


# ---------------------------------------------------------------------------
# HolographicExporter._std_dev
# ---------------------------------------------------------------------------


class TestStdDev:
    def setup_method(self):
        self.exporter = HolographicExporter()

    def test_single_value(self):
        assert self.exporter._std_dev([42.0]) == 0.0

    def test_empty_list(self):
        assert self.exporter._std_dev([]) == 0.0

    def test_identical_values(self):
        assert self.exporter._std_dev([10.0, 10.0, 10.0]) == 0.0

    def test_known_std_dev(self):
        # [2, 4, 4, 4, 5, 5, 7, 9] → mean=5, pop σ=2.0
        result = self.exporter._std_dev([2, 4, 4, 4, 5, 5, 7, 9])
        assert abs(result - 2.0) < 0.01

    def test_two_values(self):
        # [0, 10] → mean=5, σ=5.0
        result = self.exporter._std_dev([0, 10])
        assert abs(result - 5.0) < 0.01

    def test_returns_float(self):
        result = self.exporter._std_dev([1.0, 2.0, 3.0])
        assert isinstance(result, float)


# ---------------------------------------------------------------------------
# HolographicExporter._detect_resonance_patterns
# ---------------------------------------------------------------------------


class TestDetectResonancePatterns:
    def setup_method(self):
        self.exporter = HolographicExporter()

    def test_no_patterns_when_empty(self):
        result = self.exporter._detect_resonance_patterns([])
        assert result == []

    def test_no_wocl_when_high_effectiveness(self):
        # WOCL hours (2-5) with high effectiveness → no pattern
        circadian = [{"hour": h, "avg_effectiveness": 90.0} for h in range(24)]
        result = self.exporter._detect_resonance_patterns(circadian)
        wocl = [p for p in result if p["type"] == "wocl_fatigue"]
        assert len(wocl) == 0

    def test_wocl_fatigue_detected(self):
        # Low effectiveness during WOCL hours (2-5)
        circadian = []
        for h in range(24):
            eff = 60.0 if 2 <= h < 6 else 90.0
            circadian.append({"hour": h, "avg_effectiveness": eff})
        result = self.exporter._detect_resonance_patterns(circadian)
        wocl = [p for p in result if p["type"] == "wocl_fatigue"]
        assert len(wocl) == 1
        assert wocl[0]["severity"] == "high"  # < 70

    def test_wocl_moderate_severity(self):
        circadian = []
        for h in range(24):
            eff = 72.0 if 2 <= h < 6 else 90.0
            circadian.append({"hour": h, "avg_effectiveness": eff})
        result = self.exporter._detect_resonance_patterns(circadian)
        wocl = [p for p in result if p["type"] == "wocl_fatigue"]
        assert len(wocl) == 1
        assert wocl[0]["severity"] == "moderate"

    def test_post_lunch_dip_detected(self):
        # Morning peak high, afternoon dip low (>5 points difference)
        circadian = []
        for h in range(24):
            if 9 <= h < 12:
                eff = 92.0  # morning
            elif 13 <= h < 16:
                eff = 80.0  # afternoon (>5 below morning)
            else:
                eff = 85.0
            circadian.append({"hour": h, "avg_effectiveness": eff})
        result = self.exporter._detect_resonance_patterns(circadian)
        dip = [p for p in result if p["type"] == "post_lunch_dip"]
        assert len(dip) == 1

    def test_no_post_lunch_dip_when_small_difference(self):
        # Morning and afternoon nearly equal → no dip detected
        circadian = []
        for h in range(24):
            if 9 <= h < 12:
                eff = 90.0
            elif 13 <= h < 16:
                eff = 88.0  # Only 2 below, <5 threshold
            else:
                eff = 85.0
            circadian.append({"hour": h, "avg_effectiveness": eff})
        result = self.exporter._detect_resonance_patterns(circadian)
        dip = [p for p in result if p["type"] == "post_lunch_dip"]
        assert len(dip) == 0


# ---------------------------------------------------------------------------
# HolographicExporter._identify_risk_periods
# ---------------------------------------------------------------------------


class TestIdentifyRiskPeriods:
    def setup_method(self):
        self.exporter = HolographicExporter()

    def test_no_risk_when_all_above_threshold(self):
        predictions = [
            {"timestamp": f"2026-01-01T{h:02d}:00:00", "effectiveness": 85.0}
            for h in range(24)
        ]
        result = self.exporter._identify_risk_periods(predictions)
        assert result == []

    def test_single_risk_period(self):
        predictions = [
            {"timestamp": "2026-01-01T00:00:00", "effectiveness": 80.0},
            {"timestamp": "2026-01-01T01:00:00", "effectiveness": 70.0},
            {"timestamp": "2026-01-01T02:00:00", "effectiveness": 65.0},
            {"timestamp": "2026-01-01T03:00:00", "effectiveness": 80.0},
        ]
        result = self.exporter._identify_risk_periods(predictions)
        assert len(result) == 1
        assert result[0]["start"] == "2026-01-01T01:00:00"
        assert result[0]["end"] == "2026-01-01T03:00:00"

    def test_risk_period_min_effectiveness(self):
        predictions = [
            {"timestamp": "T00", "effectiveness": 80.0},
            {"timestamp": "T01", "effectiveness": 70.0},
            {"timestamp": "T02", "effectiveness": 60.0},
            {"timestamp": "T03", "effectiveness": 80.0},
        ]
        result = self.exporter._identify_risk_periods(predictions)
        assert result[0]["min_effectiveness"] == 60.0

    def test_unclosed_risk_period(self):
        # Risk starts and never ends
        predictions = [
            {"timestamp": "T00", "effectiveness": 80.0},
            {"timestamp": "T01", "effectiveness": 70.0},
            {"timestamp": "T02", "effectiveness": 65.0},
        ]
        result = self.exporter._identify_risk_periods(predictions)
        assert len(result) == 1
        assert result[0]["end"] == "T02"

    def test_multiple_risk_periods(self):
        predictions = [
            {"timestamp": "T00", "effectiveness": 80.0},
            {"timestamp": "T01", "effectiveness": 70.0},  # risk 1 start
            {"timestamp": "T02", "effectiveness": 80.0},  # risk 1 end
            {"timestamp": "T03", "effectiveness": 90.0},
            {"timestamp": "T04", "effectiveness": 65.0},  # risk 2 start
            {"timestamp": "T05", "effectiveness": 80.0},  # risk 2 end
        ]
        result = self.exporter._identify_risk_periods(predictions)
        assert len(result) == 2

    def test_empty_predictions(self):
        result = self.exporter._identify_risk_periods([])
        assert result == []

    def test_exactly_at_threshold_is_not_risk(self):
        # 77 is the threshold — >= 77 is NOT risk
        predictions = [
            {"timestamp": "T00", "effectiveness": 77.0},
            {"timestamp": "T01", "effectiveness": 77.0},
        ]
        result = self.exporter._identify_risk_periods(predictions)
        assert result == []

    def test_just_below_threshold_is_risk(self):
        predictions = [
            {"timestamp": "T00", "effectiveness": 76.9},
            {"timestamp": "T01", "effectiveness": 80.0},
        ]
        result = self.exporter._identify_risk_periods(predictions)
        assert len(result) == 1


# ---------------------------------------------------------------------------
# HolographicExporter.export_temporal_dynamics
# ---------------------------------------------------------------------------


class TestExportTemporalDynamics:
    def setup_method(self):
        self.exporter = HolographicExporter()

    def test_returns_temporal_dynamics_data(self):
        result = self.exporter.export_temporal_dynamics({}, analysis_days=7)
        assert isinstance(result, TemporalDynamicsData)

    def test_empty_data(self):
        result = self.exporter.export_temporal_dynamics({})
        assert result.circadian_pattern == []
        assert result.weekly_pattern == []

    def test_circadian_pattern_populated(self):
        now = datetime.now()
        pid = uuid4()
        # One data point per hour for 24 hours
        data = {pid: [(now - timedelta(hours=h), 80.0 + h * 0.5) for h in range(24)]}
        result = self.exporter.export_temporal_dynamics(data, analysis_days=1)
        assert len(result.circadian_pattern) > 0

    def test_weekly_pattern_populated(self):
        now = datetime.now()
        pid = uuid4()
        # Data over 7 days
        data = {pid: [(now - timedelta(days=d, hours=12), 85.0) for d in range(7)]}
        result = self.exporter.export_temporal_dynamics(data, analysis_days=14)
        assert len(result.weekly_pattern) > 0

    def test_heatmap_is_7_rows(self):
        now = datetime.now()
        pid = uuid4()
        data = {
            pid: [
                (now - timedelta(days=d, hours=h), 85.0)
                for d in range(7)
                for h in range(0, 24, 6)
            ]
        }
        result = self.exporter.export_temporal_dynamics(data, analysis_days=14)
        assert len(result.heatmap_data) == 7

    def test_heatmap_rows_have_24_columns(self):
        now = datetime.now()
        pid = uuid4()
        data = {
            pid: [
                (now - timedelta(days=d, hours=h), 85.0)
                for d in range(7)
                for h in range(24)
            ]
        }
        result = self.exporter.export_temporal_dynamics(data, analysis_days=14)
        for row in result.heatmap_data:
            assert len(row) == 24

    def test_old_data_excluded(self):
        now = datetime.now()
        pid = uuid4()
        # All data older than analysis window
        data = {
            pid: [
                (now - timedelta(days=30), 85.0),
            ]
        }
        result = self.exporter.export_temporal_dynamics(data, analysis_days=7)
        assert result.circadian_pattern == []

    def test_circadian_has_avg_effectiveness(self):
        now = datetime.now()
        pid = uuid4()
        data = {
            pid: [
                (now.replace(hour=10, minute=0), 90.0),
                (now.replace(hour=10, minute=30), 80.0),
            ]
        }
        result = self.exporter.export_temporal_dynamics(data, analysis_days=1)
        h10 = [p for p in result.circadian_pattern if p["hour"] == 10]
        if h10:
            assert h10[0]["avg_effectiveness"] == 85.0  # (90+80)/2


# ---------------------------------------------------------------------------
# HolographicExporter.export_spatial_map
# ---------------------------------------------------------------------------


class TestExportSpatialMap:
    def setup_method(self):
        self.exporter = HolographicExporter()

    def test_returns_spatial_fatigue_map(self):
        result = self.exporter.export_spatial_map([], [], [])
        assert isinstance(result, SpatialFatigueMap)

    def test_empty_inputs(self):
        result = self.exporter.export_spatial_map([], [], [])
        assert result.voxels == []
        assert result.grid_dimensions == {"x": 0, "y": 0, "z": 0}

    def test_basic_voxel_generation(self):
        pid = str(uuid4())
        bid = str(uuid4())
        persons = [{"id": pid, "name": "Alice", "pgy_level": 1}]
        blocks = [{"id": bid, "date": date(2026, 1, 1)}]
        assignments = [{"person_id": pid, "block_id": bid, "rotation_type": "clinic"}]
        result = self.exporter.export_spatial_map(assignments, persons, blocks)
        assert len(result.voxels) == 1

    def test_voxel_position(self):
        pid = str(uuid4())
        bid = str(uuid4())
        persons = [{"id": pid, "name": "Alice", "pgy_level": 1}]
        blocks = [{"id": bid, "date": date(2026, 1, 1)}]
        assignments = [{"person_id": pid, "block_id": bid, "rotation_type": "clinic"}]
        result = self.exporter.export_spatial_map(assignments, persons, blocks)
        voxel = result.voxels[0]
        assert voxel["position"]["x"] == 0
        assert voxel["position"]["y"] == 0
        assert voxel["position"]["z"] == 0

    def test_default_effectiveness(self):
        pid = str(uuid4())
        bid = str(uuid4())
        persons = [{"id": pid, "name": "Alice", "pgy_level": 1}]
        blocks = [{"id": bid, "date": date(2026, 1, 1)}]
        assignments = [
            {
                "id": "a1",
                "person_id": pid,
                "block_id": bid,
                "rotation_type": "clinic",
            }
        ]
        result = self.exporter.export_spatial_map(assignments, persons, blocks)
        assert result.voxels[0]["effectiveness"] == 85.0

    def test_custom_effectiveness_data(self):
        pid = str(uuid4())
        bid = str(uuid4())
        persons = [{"id": pid, "name": "Alice", "pgy_level": 1}]
        blocks = [{"id": bid, "date": date(2026, 1, 1)}]
        assignments = [
            {
                "id": "a1",
                "person_id": pid,
                "block_id": bid,
                "rotation_type": "clinic",
            }
        ]
        eff_data = {"a1": 72.5}
        result = self.exporter.export_spatial_map(
            assignments, persons, blocks, effectiveness_data=eff_data
        )
        assert result.voxels[0]["effectiveness"] == 72.5

    def test_critical_flag(self):
        pid = str(uuid4())
        bid = str(uuid4())
        persons = [{"id": pid, "name": "A", "pgy_level": 1}]
        blocks = [{"id": bid, "date": date(2026, 1, 1)}]
        assignments = [
            {"id": "a1", "person_id": pid, "block_id": bid, "rotation_type": "c"}
        ]
        eff_data = {"a1": 65.0}
        result = self.exporter.export_spatial_map(
            assignments, persons, blocks, effectiveness_data=eff_data
        )
        assert result.voxels[0]["is_critical"] is True
        assert result.voxels[0]["is_warning"] is False

    def test_warning_flag(self):
        pid = str(uuid4())
        bid = str(uuid4())
        persons = [{"id": pid, "name": "A", "pgy_level": 1}]
        blocks = [{"id": bid, "date": date(2026, 1, 1)}]
        assignments = [
            {"id": "a1", "person_id": pid, "block_id": bid, "rotation_type": "c"}
        ]
        eff_data = {"a1": 73.0}
        result = self.exporter.export_spatial_map(
            assignments, persons, blocks, effectiveness_data=eff_data
        )
        assert result.voxels[0]["is_critical"] is False
        assert result.voxels[0]["is_warning"] is True

    def test_missing_person_skips_voxel(self):
        bid = str(uuid4())
        blocks = [{"id": bid, "date": date(2026, 1, 1)}]
        assignments = [{"person_id": "unknown", "block_id": bid, "rotation_type": "c"}]
        result = self.exporter.export_spatial_map(assignments, [], blocks)
        assert result.voxels == []

    def test_missing_block_skips_voxel(self):
        pid = str(uuid4())
        persons = [{"id": pid, "name": "A", "pgy_level": 1}]
        assignments = [{"person_id": pid, "block_id": "unknown", "rotation_type": "c"}]
        result = self.exporter.export_spatial_map(assignments, persons, [])
        assert result.voxels == []

    def test_blocks_sorted_by_date(self):
        pid = str(uuid4())
        b1 = str(uuid4())
        b2 = str(uuid4())
        persons = [{"id": pid, "name": "A", "pgy_level": 1}]
        blocks = [
            {"id": b2, "date": date(2026, 1, 5)},
            {"id": b1, "date": date(2026, 1, 1)},
        ]
        assignments = [
            {"person_id": pid, "block_id": b1, "rotation_type": "c"},
            {"person_id": pid, "block_id": b2, "rotation_type": "c"},
        ]
        result = self.exporter.export_spatial_map(assignments, persons, blocks)
        # b1 (Jan 1) should be x=0, b2 (Jan 5) should be x=1
        xs = [v["position"]["x"] for v in result.voxels]
        assert 0 in xs
        assert 1 in xs

    def test_blocks_sorted_when_dates_mix_date_and_datetime(self):
        pid = str(uuid4())
        b1 = str(uuid4())
        b2 = str(uuid4())
        persons = [{"id": pid, "name": "A", "pgy_level": 1}]
        blocks = [
            {"id": b2, "date": datetime(2026, 1, 2, 8, 0)},
            {"id": b1, "date": date(2026, 1, 1)},
        ]
        assignments = [
            {"person_id": pid, "block_id": b1, "rotation_type": "c"},
            {"person_id": pid, "block_id": b2, "rotation_type": "c"},
        ]

        result = self.exporter.export_spatial_map(assignments, persons, blocks)
        voxel_by_block = {v["block_id"]: v for v in result.voxels}

        assert voxel_by_block[b1]["position"]["x"] == 0
        assert voxel_by_block[b2]["position"]["x"] == 1

    def test_persons_sorted_by_pgy_level(self):
        p1 = str(uuid4())
        p2 = str(uuid4())
        bid = str(uuid4())
        persons = [
            {"id": p2, "name": "Senior", "pgy_level": 3},
            {"id": p1, "name": "Junior", "pgy_level": 1},
        ]
        blocks = [{"id": bid, "date": date(2026, 1, 1)}]
        assignments = [
            {"person_id": p1, "block_id": bid, "rotation_type": "c"},
            {"person_id": p2, "block_id": bid, "rotation_type": "c"},
        ]
        result = self.exporter.export_spatial_map(assignments, persons, blocks)
        # Junior (PGY 1) should be y=0, Senior (PGY 3) should be y=1
        voxel_p1 = [v for v in result.voxels if v["person_id"] == p1][0]
        voxel_p2 = [v for v in result.voxels if v["person_id"] == p2][0]
        assert voxel_p1["position"]["y"] < voxel_p2["position"]["y"]

    def test_grid_dimensions(self):
        pid = str(uuid4())
        bid = str(uuid4())
        persons = [{"id": pid, "name": "A", "pgy_level": 1}]
        blocks = [{"id": bid, "date": date(2026, 1, 1)}]
        assignments = [{"person_id": pid, "block_id": bid, "rotation_type": "clinic"}]
        result = self.exporter.export_spatial_map(assignments, persons, blocks)
        assert result.grid_dimensions["x"] == 1
        assert result.grid_dimensions["y"] == 1
        assert result.grid_dimensions["z"] == 1

    def test_opacity_matches_effectiveness(self):
        pid = str(uuid4())
        bid = str(uuid4())
        persons = [{"id": pid, "name": "A", "pgy_level": 1}]
        blocks = [{"id": bid, "date": date(2026, 1, 1)}]
        assignments = [
            {"id": "a1", "person_id": pid, "block_id": bid, "rotation_type": "c"}
        ]
        eff_data = {"a1": 80.0}
        result = self.exporter.export_spatial_map(
            assignments, persons, blocks, effectiveness_data=eff_data
        )
        assert result.voxels[0]["opacity"] == 0.8


# ---------------------------------------------------------------------------
# HolographicExporter.export_time_series (integration with ThreeProcessModel)
# ---------------------------------------------------------------------------


class TestExportTimeSeries:
    def test_returns_fatigue_time_series(self):
        exporter = HolographicExporter()
        result = exporter.export_time_series(
            person_id=uuid4(),
            person_name="Test",
            assignments=[],
            hours=2,
            sample_interval_minutes=60,
        )
        assert isinstance(result, FatigueTimeSeries)

    def test_has_data_points(self):
        exporter = HolographicExporter()
        result = exporter.export_time_series(
            person_id=uuid4(),
            person_name="Test",
            assignments=[],
            hours=2,
            sample_interval_minutes=60,
        )
        assert len(result.data_points) > 0

    def test_data_point_has_required_fields(self):
        exporter = HolographicExporter()
        result = exporter.export_time_series(
            person_id=uuid4(),
            person_name="Test",
            assignments=[],
            hours=1,
            sample_interval_minutes=60,
        )
        dp = result.data_points[0]
        assert "timestamp" in dp
        assert "effectiveness" in dp
        assert "color" in dp
        assert "position" in dp

    def test_person_info_set(self):
        pid = uuid4()
        exporter = HolographicExporter()
        result = exporter.export_time_series(
            person_id=pid,
            person_name="Alice",
            assignments=[],
            hours=1,
            pgy_level=2,
        )
        assert result.person_id == str(pid)
        assert result.person_name == "Alice"
        assert result.pgy_level == 2

    def test_color_gradient_populated(self):
        exporter = HolographicExporter()
        result = exporter.export_time_series(
            person_id=uuid4(),
            person_name="Test",
            assignments=[],
            hours=1,
        )
        assert len(result.color_gradient) == 5
