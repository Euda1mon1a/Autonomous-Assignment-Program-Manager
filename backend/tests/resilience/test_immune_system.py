"""Tests for Artificial Immune System (AIS) schedule anomaly detection."""

from uuid import uuid4

import numpy as np

from app.resilience.immune_system import (
    Antibody,
    AnomalyReport,
    Detector,
    RepairResult,
    ScheduleImmuneSystem,
)
from datetime import datetime


# ==================== Detector ====================


class TestDetector:
    def test_matches_inside_radius(self):
        d = Detector(
            id=uuid4(),
            center=np.array([0.0, 0.0, 0.0]),
            radius=1.0,
            created_at=datetime.now(),
        )
        assert d.matches(np.array([0.1, 0.1, 0.1]))

    def test_no_match_outside_radius(self):
        d = Detector(
            id=uuid4(),
            center=np.array([0.0, 0.0, 0.0]),
            radius=0.5,
            created_at=datetime.now(),
        )
        assert not d.matches(np.array([1.0, 1.0, 1.0]))

    def test_get_distance(self):
        d = Detector(
            id=uuid4(),
            center=np.array([0.0, 0.0]),
            radius=1.0,
            created_at=datetime.now(),
        )
        dist = d.get_distance(np.array([3.0, 4.0]))
        assert abs(dist - 5.0) < 0.001

    def test_matches_count_default(self):
        d = Detector(
            id=uuid4(),
            center=np.array([0.0]),
            radius=1.0,
            created_at=datetime.now(),
        )
        assert d.matches_count == 0


# ==================== Antibody ====================


class TestAntibody:
    def _make_antibody(self, center=None, radius=1.0):
        return Antibody(
            id=uuid4(),
            name="test_antibody",
            description="Test",
            repair_function=lambda state: state,
            affinity_center=center if center is not None else np.array([0.0, 0.0]),
            affinity_radius=radius,
        )

    def test_affinity_at_center(self):
        ab = self._make_antibody(center=np.array([0.5, 0.5]))
        affinity = ab.get_affinity(np.array([0.5, 0.5]))
        assert affinity == 1.0

    def test_affinity_outside_radius(self):
        ab = self._make_antibody(center=np.array([0.0, 0.0]), radius=0.5)
        affinity = ab.get_affinity(np.array([10.0, 10.0]))
        assert affinity == 0.0

    def test_affinity_between(self):
        ab = self._make_antibody(center=np.array([0.0, 0.0]), radius=2.0)
        affinity = ab.get_affinity(np.array([1.0, 0.0]))
        # distance=1.0, radius=2.0 → affinity = 1.0 - 1/2 = 0.5
        assert abs(affinity - 0.5) < 0.001

    def test_success_rate_zero_applications(self):
        ab = self._make_antibody()
        assert ab.success_rate == 0.0

    def test_success_rate(self):
        ab = self._make_antibody()
        ab.applications_count = 10
        ab.success_count = 7
        assert abs(ab.success_rate - 0.7) < 0.001


# ==================== AnomalyReport ====================


class TestAnomalyReport:
    def test_post_init_critical(self):
        report = AnomalyReport(
            id=uuid4(),
            detected_at=datetime.now(),
            feature_vector=np.array([0.0]),
            anomaly_score=2.5,
            matching_detectors=[uuid4()],
            severity="",
            description="Test",
        )
        assert report.severity == "critical"

    def test_post_init_high(self):
        report = AnomalyReport(
            id=uuid4(),
            detected_at=datetime.now(),
            feature_vector=np.array([0.0]),
            anomaly_score=1.5,
            matching_detectors=[],
            severity="",
            description="Test",
        )
        assert report.severity == "high"

    def test_post_init_medium(self):
        report = AnomalyReport(
            id=uuid4(),
            detected_at=datetime.now(),
            feature_vector=np.array([0.0]),
            anomaly_score=0.7,
            matching_detectors=[],
            severity="",
            description="Test",
        )
        assert report.severity == "medium"

    def test_post_init_low(self):
        report = AnomalyReport(
            id=uuid4(),
            detected_at=datetime.now(),
            feature_vector=np.array([0.0]),
            anomaly_score=0.3,
            matching_detectors=[],
            severity="",
            description="Test",
        )
        assert report.severity == "low"


# ==================== ScheduleImmuneSystem ====================


class TestScheduleImmuneSystemInit:
    def test_defaults(self):
        sis = ScheduleImmuneSystem(feature_dims=10)
        assert sis.feature_dims == 10
        assert sis.detector_count == 100
        assert sis.detection_radius == 0.1
        assert sis.detectors == []
        assert sis.antibodies == {}
        assert sis.is_trained is False
        assert sis.anomalies_detected == 0

    def test_custom(self):
        sis = ScheduleImmuneSystem(
            feature_dims=5, detector_count=50, detection_radius=0.5
        )
        assert sis.feature_dims == 5
        assert sis.detector_count == 50
        assert sis.detection_radius == 0.5


class TestExtractFeatures:
    def test_returns_correct_dims(self):
        sis = ScheduleImmuneSystem(feature_dims=12)
        features = sis.extract_features({"total_blocks": 10, "covered_blocks": 9})
        assert len(features) == 12

    def test_pads_if_short(self):
        sis = ScheduleImmuneSystem(feature_dims=20)
        features = sis.extract_features({})
        assert len(features) == 20

    def test_truncates_if_long(self):
        sis = ScheduleImmuneSystem(feature_dims=3)
        features = sis.extract_features(
            {
                "total_blocks": 10,
                "covered_blocks": 9,
                "coverage_by_type": {"clinic": 0.8},
            }
        )
        assert len(features) == 3

    def test_coverage_rate(self):
        sis = ScheduleImmuneSystem(feature_dims=12)
        features = sis.extract_features({"total_blocks": 100, "covered_blocks": 90})
        assert abs(features[0] - 0.9) < 0.01

    def test_hours_compliance(self):
        sis = ScheduleImmuneSystem(feature_dims=12)
        # At 80 hours → compliance = 1.0
        features = sis.extract_features({"avg_hours_per_week": 80})
        assert features[6] == 1.0  # hours_compliance index

    def test_default_values(self):
        sis = ScheduleImmuneSystem(feature_dims=12)
        features = sis.extract_features({})
        # Should not error with empty state
        assert len(features) == 12


class TestTrain:
    def test_trains_with_valid_schedules(self):
        sis = ScheduleImmuneSystem(
            feature_dims=12, detector_count=10, detection_radius=0.5
        )
        valid = [
            {"total_blocks": 100, "covered_blocks": 95},
            {"total_blocks": 100, "covered_blocks": 98},
            {"total_blocks": 100, "covered_blocks": 92},
        ]
        sis.train(valid, max_attempts=200)
        assert sis.is_trained is True
        assert len(sis.training_features) == 3

    def test_empty_training(self):
        sis = ScheduleImmuneSystem(feature_dims=12)
        sis.train([])
        assert sis.is_trained is False

    def test_detectors_dont_match_self(self):
        sis = ScheduleImmuneSystem(
            feature_dims=12, detector_count=5, detection_radius=0.05
        )
        valid = [
            {"total_blocks": 100, "covered_blocks": 95, "avg_hours_per_week": 60},
        ]
        sis.train(valid, max_attempts=500)
        features = sis.extract_features(valid[0])
        for detector in sis.detectors:
            # Detectors should NOT match the training data
            assert not detector.matches(features)


class TestIsAnomaly:
    def test_not_trained_returns_false(self):
        sis = ScheduleImmuneSystem(feature_dims=12)
        assert sis.is_anomaly({"total_blocks": 10}) is False


class TestGetAnomalyScore:
    def test_not_trained(self):
        sis = ScheduleImmuneSystem(feature_dims=12)
        assert sis.get_anomaly_score({}) == 0.0


class TestRegisterAntibody:
    def test_registers(self):
        sis = ScheduleImmuneSystem(feature_dims=12)

        def repair_fn(state):
            return state

        sis.register_antibody(
            name="coverage_repair",
            repair_fn=repair_fn,
            description="Fix coverage gaps",
        )
        assert "coverage_repair" in sis.antibodies
        assert sis.antibodies["coverage_repair"].description == "Fix coverage gaps"

    def test_with_affinity_pattern(self):
        sis = ScheduleImmuneSystem(feature_dims=12)

        def repair_fn(state):
            return state

        sis.register_antibody(
            name="test",
            repair_fn=repair_fn,
            affinity_pattern={"total_blocks": 100, "covered_blocks": 50},
            affinity_radius=2.0,
        )
        ab = sis.antibodies["test"]
        assert len(ab.affinity_center) == 12
        assert ab.affinity_radius == 2.0


class TestSelectAntibody:
    def test_no_antibodies(self):
        sis = ScheduleImmuneSystem(feature_dims=12)
        assert sis.select_antibody({}) is None

    def test_selects_best_match(self):
        sis = ScheduleImmuneSystem(feature_dims=12)
        state = {"total_blocks": 100, "covered_blocks": 50}

        def repair_fn(s):
            return s

        sis.register_antibody(
            "close_match",
            repair_fn,
            affinity_pattern=state,
            affinity_radius=5.0,
        )
        sis.register_antibody(
            "far_match",
            repair_fn,
            affinity_pattern={"total_blocks": 100, "covered_blocks": 100},
            affinity_radius=5.0,
        )
        result = sis.select_antibody(state)
        assert result is not None
        name, antibody = result
        assert name == "close_match"


class TestApplyRepair:
    def test_no_antibodies(self):
        sis = ScheduleImmuneSystem(feature_dims=12)
        result = sis.apply_repair({})
        assert result is None

    def test_repair_applied(self):
        sis = ScheduleImmuneSystem(
            feature_dims=12, detector_count=5, detection_radius=0.5
        )

        def repair_fn(state):
            return {**state, "covered_blocks": state.get("total_blocks", 100)}

        sis.register_antibody(
            "fix_coverage",
            repair_fn,
            affinity_pattern={"total_blocks": 100, "covered_blocks": 50},
            affinity_radius=5.0,
        )

        state = {"total_blocks": 100, "covered_blocks": 50}
        result = sis.apply_repair(state)
        assert isinstance(result, RepairResult)
        assert result.antibody_name == "fix_coverage"
        assert sis.repairs_applied == 1

    def test_repair_exception_handled(self):
        sis = ScheduleImmuneSystem(feature_dims=12)

        def bad_repair(state):
            raise RuntimeError("repair failed")

        sis.register_antibody(
            "bad",
            bad_repair,
            affinity_pattern={"total_blocks": 10},
            affinity_radius=10.0,
        )
        result = sis.apply_repair({"total_blocks": 10})
        assert result is not None
        assert result.successful is False
        assert "failed" in result.message


class TestGetStatistics:
    def test_initial_stats(self):
        sis = ScheduleImmuneSystem(feature_dims=10)
        stats = sis.get_statistics()
        assert stats["is_trained"] is False
        assert stats["feature_dims"] == 10
        assert stats["detector_count"] == 0
        assert stats["anomalies_detected"] == 0
        assert stats["repairs_applied"] == 0
        assert stats["repair_success_rate"] == 0.0


class TestResetStatistics:
    def test_resets(self):
        sis = ScheduleImmuneSystem(feature_dims=10)
        sis.anomalies_detected = 5
        sis.repairs_applied = 3
        sis.successful_repairs = 2
        sis.reset_statistics()
        assert sis.anomalies_detected == 0
        assert sis.repairs_applied == 0
        assert sis.successful_repairs == 0
