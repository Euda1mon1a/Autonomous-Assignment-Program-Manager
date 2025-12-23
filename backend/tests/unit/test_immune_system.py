"""
Tests for Artificial Immune System (AIS) module.

Tests cover:
- Feature extraction from schedule states
- Detector generation via negative selection
- Anomaly detection
- Antibody registration and selection
- Repair application via clonal selection
"""

import numpy as np
import pytest

from app.resilience.immune_system import (
    AnomalyReport,
    Antibody,
    Detector,
    RepairResult,
    ScheduleImmuneSystem,
)

# Test Fixtures


@pytest.fixture
def valid_schedule_state():
    """A valid, compliant schedule state."""
    return {
        "total_blocks": 100,
        "covered_blocks": 95,
        "faculty_count": 10,
        "resident_count": 20,
        "acgme_violations": [],
        "avg_hours_per_week": 75.0,
        "supervision_ratio": 0.5,  # 1:2 ratio
        "workload_std_dev": 0.1,
        "schedule_changes": 5,
        "total_assignments": 100,
        "coverage_by_type": {
            "clinic": 0.95,
            "inpatient": 0.90,
            "procedure": 0.85,
        },
    }


@pytest.fixture
def invalid_schedule_state():
    """An invalid schedule state with violations."""
    return {
        "total_blocks": 100,
        "covered_blocks": 70,  # Low coverage
        "faculty_count": 5,
        "resident_count": 20,
        "acgme_violations": [
            {"type": "80_HOUR", "severity": "CRITICAL"},
            {"type": "SUPERVISION", "severity": "CRITICAL"},
        ],
        "avg_hours_per_week": 85.0,  # Over limit
        "supervision_ratio": 4.0,  # Poor ratio (1:4)
        "workload_std_dev": 0.5,  # High imbalance
        "schedule_changes": 30,
        "total_assignments": 100,
        "coverage_by_type": {
            "clinic": 0.70,
            "inpatient": 0.65,
            "procedure": 0.60,
        },
    }


@pytest.fixture
def immune_system():
    """Create a basic immune system instance."""
    return ScheduleImmuneSystem(
        feature_dims=12, detector_count=50, detection_radius=0.15
    )


@pytest.fixture
def trained_immune_system(immune_system, valid_schedule_state):
    """Create and train an immune system."""
    # Generate variations of valid schedules for training
    training_schedules = []
    for i in range(10):
        schedule = valid_schedule_state.copy()
        # Small variations
        schedule["covered_blocks"] = 95 + np.random.randint(-2, 3)
        schedule["avg_hours_per_week"] = 75.0 + np.random.uniform(-5, 5)
        schedule["workload_std_dev"] = 0.1 + np.random.uniform(-0.05, 0.05)
        training_schedules.append(schedule)

    immune_system.train(training_schedules)
    return immune_system


# Test Feature Extraction


def test_feature_extraction_dimensions(immune_system, valid_schedule_state):
    """Test that feature extraction produces correct dimensions."""
    features = immune_system.extract_features(valid_schedule_state)

    assert isinstance(features, np.ndarray)
    assert features.shape == (immune_system.feature_dims,)
    assert features.dtype == np.float32


def test_feature_extraction_coverage(immune_system):
    """Test that coverage is correctly extracted."""
    state = {
        "total_blocks": 100,
        "covered_blocks": 90,
        "faculty_count": 10,
        "resident_count": 20,
        "acgme_violations": [],
        "avg_hours_per_week": 75.0,
        "supervision_ratio": 0.5,
        "workload_std_dev": 0.1,
        "schedule_changes": 5,
        "total_assignments": 100,
        "coverage_by_type": {"clinic": 0.9, "inpatient": 0.9, "procedure": 0.9},
    }

    features = immune_system.extract_features(state)

    # First feature should be coverage rate (90/100 = 0.9)
    assert abs(features[0] - 0.9) < 0.01


def test_feature_extraction_violations(immune_system):
    """Test that violations affect features correctly."""
    state_no_violations = {
        "total_blocks": 100,
        "covered_blocks": 95,
        "faculty_count": 10,
        "resident_count": 20,
        "acgme_violations": [],
        "avg_hours_per_week": 75.0,
        "supervision_ratio": 0.5,
        "workload_std_dev": 0.1,
        "schedule_changes": 5,
        "total_assignments": 100,
        "coverage_by_type": {"clinic": 0.95, "inpatient": 0.95, "procedure": 0.95},
    }

    state_with_violations = state_no_violations.copy()
    state_with_violations["acgme_violations"] = [
        {"severity": "CRITICAL"},
        {"severity": "HIGH"},
    ]

    features_clean = immune_system.extract_features(state_no_violations)
    features_violations = immune_system.extract_features(state_with_violations)

    # Features should be different
    assert not np.allclose(features_clean, features_violations)


# Test Detector Class


def test_detector_matches():
    """Test detector matching logic."""
    from datetime import datetime
    from uuid import uuid4

    center = np.array([0.5, 0.5, 0.5], dtype=np.float32)
    detector = Detector(
        id=uuid4(),
        center=center,
        radius=0.2,
        created_at=datetime.now(),
    )

    # Point within radius should match
    point_inside = np.array([0.55, 0.55, 0.55], dtype=np.float32)
    assert detector.matches(point_inside)

    # Point outside radius should not match
    point_outside = np.array([0.9, 0.9, 0.9], dtype=np.float32)
    assert not detector.matches(point_outside)


def test_detector_distance():
    """Test detector distance calculation."""
    from datetime import datetime
    from uuid import uuid4

    center = np.array([0.0, 0.0, 0.0], dtype=np.float32)
    detector = Detector(
        id=uuid4(),
        center=center,
        radius=0.2,
        created_at=datetime.now(),
    )

    point = np.array([3.0, 4.0, 0.0], dtype=np.float32)
    distance = detector.get_distance(point)

    # Distance should be 5.0 (3-4-5 triangle)
    assert abs(distance - 5.0) < 0.01


# Test Training (Negative Selection)


def test_training_generates_detectors(immune_system, valid_schedule_state):
    """Test that training generates detectors."""
    training_schedules = [valid_schedule_state] * 5

    immune_system.train(training_schedules)

    assert immune_system.is_trained
    assert len(immune_system.detectors) > 0
    assert len(immune_system.training_features) == 5


def test_negative_selection_rejects_self_matching(immune_system, valid_schedule_state):
    """Test that negative selection doesn't create detectors that match valid schedules."""
    training_schedules = [valid_schedule_state] * 10

    immune_system.train(training_schedules)

    # Extract features from valid schedule
    valid_features = immune_system.extract_features(valid_schedule_state)

    # Count how many detectors match valid schedule
    matches = sum(1 for d in immune_system.detectors if d.matches(valid_features))

    # Should be zero or very few (negative selection should prevent this)
    assert matches == 0, "Detectors should not match valid 'self' schedules"


def test_training_with_empty_schedules(immune_system):
    """Test training with no valid schedules."""
    immune_system.train([])

    assert not immune_system.is_trained
    assert len(immune_system.detectors) == 0


# Test Anomaly Detection


def test_anomaly_detection_on_valid_schedule(
    trained_immune_system, valid_schedule_state
):
    """Test that valid schedules are not flagged as anomalies."""
    is_anomaly = trained_immune_system.is_anomaly(valid_schedule_state)

    # Valid schedule should not be anomalous
    # (some detectors might trigger due to randomness, but generally should be False)
    assert (
        not is_anomaly
        or trained_immune_system.get_anomaly_score(valid_schedule_state) < 0.5
    )


def test_anomaly_detection_on_invalid_schedule(
    trained_immune_system, invalid_schedule_state
):
    """Test that invalid schedules are flagged as anomalies."""
    is_anomaly = trained_immune_system.is_anomaly(invalid_schedule_state)

    # Invalid schedule should be detected as anomaly
    assert is_anomaly


def test_anomaly_score_invalid_higher_than_valid(
    trained_immune_system, valid_schedule_state, invalid_schedule_state
):
    """Test that invalid schedules have higher anomaly scores."""
    valid_score = trained_immune_system.get_anomaly_score(valid_schedule_state)
    invalid_score = trained_immune_system.get_anomaly_score(invalid_schedule_state)

    # Invalid should have higher anomaly score
    assert invalid_score > valid_score


def test_detect_anomaly_returns_report(trained_immune_system, invalid_schedule_state):
    """Test that detect_anomaly returns a detailed report."""
    report = trained_immune_system.detect_anomaly(invalid_schedule_state)

    if report:  # Only check if anomaly was detected
        assert isinstance(report, AnomalyReport)
        assert report.anomaly_score > 0
        assert len(report.matching_detectors) > 0
        assert report.severity in ["low", "medium", "high", "critical"]
        assert len(report.description) > 0


def test_untrained_immune_system_returns_no_anomaly(
    immune_system, invalid_schedule_state
):
    """Test that untrained system doesn't detect anomalies."""
    is_anomaly = immune_system.is_anomaly(invalid_schedule_state)

    assert not is_anomaly


# Test Antibody Class


def test_antibody_affinity_calculation():
    """Test antibody affinity calculation."""
    from uuid import uuid4

    center = np.array([0.5, 0.5, 0.5], dtype=np.float32)

    def dummy_repair(state):
        return state

    antibody = Antibody(
        id=uuid4(),
        name="test_antibody",
        description="Test",
        repair_function=dummy_repair,
        affinity_center=center,
        affinity_radius=0.3,
    )

    # Point at center should have affinity 1.0
    point_center = np.array([0.5, 0.5, 0.5], dtype=np.float32)
    affinity_center = antibody.get_affinity(point_center)
    assert abs(affinity_center - 1.0) < 0.01

    # Point outside radius should have affinity 0.0
    point_far = np.array([1.0, 1.0, 1.0], dtype=np.float32)
    affinity_far = antibody.get_affinity(point_far)
    assert affinity_far == 0.0

    # Point halfway to edge should have affinity ~0.5
    point_mid = center + 0.15 * np.array([1.0, 0.0, 0.0], dtype=np.float32)
    affinity_mid = antibody.get_affinity(point_mid)
    assert 0.4 < affinity_mid < 0.6


def test_antibody_success_rate():
    """Test antibody success rate calculation."""
    from uuid import uuid4

    def dummy_repair(state):
        return state

    antibody = Antibody(
        id=uuid4(),
        name="test_antibody",
        description="Test",
        repair_function=dummy_repair,
        affinity_center=np.zeros(3, dtype=np.float32),
        affinity_radius=1.0,
        applications_count=10,
        success_count=7,
    )

    assert abs(antibody.success_rate - 0.7) < 0.01


# Test Antibody Registration and Selection


def test_register_antibody(immune_system):
    """Test antibody registration."""

    def repair_coverage(state):
        state = state.copy()
        state["covered_blocks"] = state["total_blocks"]
        return state

    immune_system.register_antibody(
        name="coverage_repair",
        repair_fn=repair_coverage,
        description="Fixes coverage gaps",
    )

    assert "coverage_repair" in immune_system.antibodies
    assert immune_system.antibodies["coverage_repair"].name == "coverage_repair"


def test_select_antibody_highest_affinity(immune_system, invalid_schedule_state):
    """Test that select_antibody chooses highest affinity antibody."""

    def repair1(state):
        return state

    def repair2(state):
        return state

    # Register two antibodies
    immune_system.register_antibody(
        name="antibody1",
        repair_fn=repair1,
        affinity_pattern=invalid_schedule_state,  # High affinity
        affinity_radius=2.0,
    )

    immune_system.register_antibody(
        name="antibody2",
        repair_fn=repair2,
        affinity_radius=0.1,  # Low affinity
    )

    # Select for invalid schedule
    selection = immune_system.select_antibody(invalid_schedule_state)

    assert selection is not None
    name, antibody = selection
    # Should select antibody1 (higher affinity)
    assert name == "antibody1"


def test_select_antibody_no_antibodies(immune_system, invalid_schedule_state):
    """Test select_antibody with no registered antibodies."""
    selection = immune_system.select_antibody(invalid_schedule_state)

    assert selection is None


# Test Repair Application


def test_apply_repair_success(trained_immune_system, invalid_schedule_state):
    """Test successful repair application."""

    def fix_coverage(state):
        """Repair function that improves coverage."""
        state = state.copy()
        state["covered_blocks"] = state["total_blocks"]  # Full coverage
        state["acgme_violations"] = []  # Clear violations
        state["avg_hours_per_week"] = 75.0  # Compliant hours
        state["coverage_by_type"] = {
            "clinic": 1.0,
            "inpatient": 1.0,
            "procedure": 1.0,
        }
        return state

    trained_immune_system.register_antibody(
        name="full_repair",
        repair_fn=fix_coverage,
        affinity_pattern=invalid_schedule_state,
        affinity_radius=3.0,
        description="Comprehensive repair",
    )

    result = trained_immune_system.apply_repair(invalid_schedule_state)

    assert result is not None
    assert isinstance(result, RepairResult)
    assert result.antibody_name == "full_repair"
    assert result.anomaly_after < result.anomaly_before  # Should improve
    assert result.successful


def test_apply_repair_ineffective(trained_immune_system, invalid_schedule_state):
    """Test repair that doesn't improve anomaly score."""

    def bad_repair(state):
        """Repair that doesn't actually help."""
        return state  # No change

    trained_immune_system.register_antibody(
        name="bad_repair",
        repair_fn=bad_repair,
        affinity_pattern=invalid_schedule_state,
        affinity_radius=3.0,
    )

    result = trained_immune_system.apply_repair(invalid_schedule_state)

    assert result is not None
    assert not result.successful  # Should fail
    assert result.anomaly_after == result.anomaly_before


def test_apply_repair_no_antibodies(trained_immune_system, invalid_schedule_state):
    """Test repair with no registered antibodies."""
    result = trained_immune_system.apply_repair(invalid_schedule_state)

    assert result is None


def test_apply_repair_updates_statistics(trained_immune_system, invalid_schedule_state):
    """Test that repair updates antibody statistics."""

    def repair(state):
        state = state.copy()
        state["covered_blocks"] = state["total_blocks"]
        return state

    trained_immune_system.register_antibody(
        name="test_repair",
        repair_fn=repair,
        affinity_pattern=invalid_schedule_state,
        affinity_radius=3.0,
    )

    initial_applications = trained_immune_system.antibodies[
        "test_repair"
    ].applications_count

    trained_immune_system.apply_repair(invalid_schedule_state)

    # Applications count should increase
    assert (
        trained_immune_system.antibodies["test_repair"].applications_count
        == initial_applications + 1
    )


def test_repair_exception_handling(trained_immune_system, invalid_schedule_state):
    """Test that repair handles exceptions gracefully."""

    def failing_repair(state):
        raise ValueError("Intentional failure")

    trained_immune_system.register_antibody(
        name="failing_repair",
        repair_fn=failing_repair,
        affinity_pattern=invalid_schedule_state,
        affinity_radius=3.0,
    )

    result = trained_immune_system.apply_repair(invalid_schedule_state)

    assert result is not None
    assert not result.successful
    assert "failed" in result.message.lower()


# Test Statistics


def test_get_statistics(trained_immune_system):
    """Test statistics retrieval."""
    stats = trained_immune_system.get_statistics()

    assert stats["is_trained"]
    assert stats["detector_count"] > 0
    assert stats["feature_dims"] == 12
    assert "anomalies_detected" in stats
    assert "repairs_applied" in stats
    assert "antibody_performance" in stats


def test_reset_statistics(trained_immune_system, invalid_schedule_state):
    """Test statistics reset."""
    # Detect some anomalies
    trained_immune_system.is_anomaly(invalid_schedule_state)
    trained_immune_system.is_anomaly(invalid_schedule_state)

    assert trained_immune_system.anomalies_detected > 0

    # Reset
    trained_immune_system.reset_statistics()

    assert trained_immune_system.anomalies_detected == 0
    assert trained_immune_system.repairs_applied == 0


# Integration Tests


def test_full_workflow(immune_system, valid_schedule_state, invalid_schedule_state):
    """Test complete workflow: train -> detect -> repair."""
    # 1. Train
    training_schedules = [valid_schedule_state] * 10
    immune_system.train(training_schedules)

    assert immune_system.is_trained

    # 2. Detect anomaly
    is_anomaly = immune_system.is_anomaly(invalid_schedule_state)
    assert is_anomaly

    # 3. Register repair antibody
    def comprehensive_repair(state):
        state = state.copy()
        state["covered_blocks"] = state["total_blocks"]
        state["acgme_violations"] = []
        state["avg_hours_per_week"] = 75.0
        state["supervision_ratio"] = 0.5
        state["workload_std_dev"] = 0.1
        state["coverage_by_type"] = {"clinic": 1.0, "inpatient": 1.0, "procedure": 1.0}
        return state

    immune_system.register_antibody(
        name="comprehensive_repair",
        repair_fn=comprehensive_repair,
        affinity_pattern=invalid_schedule_state,
        affinity_radius=3.0,
    )

    # 4. Apply repair
    result = immune_system.apply_repair(invalid_schedule_state)

    assert result is not None
    assert result.successful
    assert result.anomaly_after < result.anomaly_before

    # 5. Verify repaired state is better
    repaired_anomaly = immune_system.is_anomaly(result.repaired_state)
    original_anomaly = immune_system.is_anomaly(invalid_schedule_state)

    # Repaired should be less anomalous (or not anomalous at all)
    assert (not repaired_anomaly) or (
        immune_system.get_anomaly_score(result.repaired_state)
        < immune_system.get_anomaly_score(invalid_schedule_state)
    )


def test_multiple_repairs_improve_success_rate(
    trained_immune_system, invalid_schedule_state
):
    """Test that antibody success rate updates over multiple applications."""

    def good_repair(state):
        state = state.copy()
        state["covered_blocks"] = state["total_blocks"]
        state["acgme_violations"] = []
        return state

    trained_immune_system.register_antibody(
        name="good_repair",
        repair_fn=good_repair,
        affinity_pattern=invalid_schedule_state,
        affinity_radius=3.0,
    )

    # Apply repair multiple times
    for _ in range(5):
        trained_immune_system.apply_repair(invalid_schedule_state)

    antibody = trained_immune_system.antibodies["good_repair"]
    assert antibody.applications_count == 5
    assert antibody.success_rate > 0.5  # Should have decent success rate


def test_detector_match_counting(trained_immune_system, invalid_schedule_state):
    """Test that detector match counts are updated."""
    initial_total_matches = sum(
        d.matches_count for d in trained_immune_system.detectors
    )

    # Detect anomaly several times
    for _ in range(3):
        trained_immune_system.is_anomaly(invalid_schedule_state)

    final_total_matches = sum(d.matches_count for d in trained_immune_system.detectors)

    # Match count should increase
    assert final_total_matches > initial_total_matches
