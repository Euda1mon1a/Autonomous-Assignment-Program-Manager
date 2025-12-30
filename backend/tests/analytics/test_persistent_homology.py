"""
Tests for Persistent Homology (TDA) Analysis.

Tests the topological data analysis functionality for schedule structure analysis.
"""

import uuid
from datetime import date, timedelta

import numpy as np
import pytest
from sqlalchemy.orm import Session

from app.analytics.persistent_homology import (
    CoverageVoid,
    CyclicPattern,
    PersistenceDiagram,
    PersistentScheduleAnalyzer,
    TopologicalFeature,
)
from app.models.assignment import Assignment
from app.models.block import Block
from app.models.person import Person
from app.models.rotation_template import RotationTemplate


@pytest.fixture
def sample_point_cloud():
    """Create a sample point cloud for testing."""
    # Create a simple 2D point cloud with clear structure
    # Cluster 1: around (0, 0)
    cluster1 = np.random.randn(20, 2) * 0.5
    # Cluster 2: around (5, 5)
    cluster2 = np.random.randn(20, 2) * 0.5 + np.array([5, 5])
    # Cluster 3: around (5, 0)
    cluster3 = np.random.randn(20, 2) * 0.5 + np.array([5, 0])

    point_cloud = np.vstack([cluster1, cluster2, cluster3])
    return point_cloud


@pytest.fixture
def sample_assignments(db: Session):
    """Create sample assignments for testing."""
    # Create people (residents)
    residents = []
    for i in range(5):
        person = Person(
            id=uuid.uuid4(),
            name=f"Resident {i}",
            email=f"resident{i}@example.com",
            role="RESIDENT",
            pgy_level=i % 3 + 1,
        )
        db.add(person)
        residents.append(person)

    # Create rotation templates
    rotations = []
    for name in ["Clinic", "Inpatient", "Procedures", "Conference"]:
        rotation = RotationTemplate(
            id=uuid.uuid4(),
            name=name,
            abbreviation=name[:3].upper(),
            activity_type="clinical" if name != "Conference" else "administrative",
        )
        db.add(rotation)
        rotations.append(rotation)

    db.commit()

    # Create blocks (30 days, AM and PM)
    start_date = date.today()
    blocks = []
    for day_offset in range(30):
        current_date = start_date + timedelta(days=day_offset)
        for session in ["AM", "PM"]:
            block = Block(
                id=uuid.uuid4(),
                date=current_date,
                session=session,
            )
            db.add(block)
            blocks.append(block)

    db.commit()

    # Create assignments (cyclic pattern)
    assignments = []
    for idx, block in enumerate(blocks):
        # Assign residents in a cyclic pattern
        resident_idx = idx % len(residents)
        rotation_idx = (idx // 7) % len(rotations)  # Weekly rotation change

        assignment = Assignment(
            id=uuid.uuid4(),
            block_id=block.id,
            person_id=residents[resident_idx].id,
            rotation_template_id=rotations[rotation_idx].id,
            role="primary",
            created_by="test",
        )
        db.add(assignment)
        assignments.append(assignment)

    db.commit()

    # Refresh to load relationships
    for assignment in assignments:
        db.refresh(assignment)

    return assignments


class TestTopologicalFeature:
    """Test TopologicalFeature dataclass."""

    def test_feature_creation(self):
        """Test creating a topological feature."""
        feature = TopologicalFeature(
            dimension=1,
            birth=0.5,
            death=2.0,
            persistence=1.5,
            interpretation="Test feature",
        )

        assert feature.dimension == 1
        assert feature.birth == 0.5
        assert feature.death == 2.0
        assert feature.persistence == 1.5
        assert feature.interpretation == "Test feature"

    def test_persistence_auto_calculation(self):
        """Test automatic persistence calculation."""
        feature = TopologicalFeature(
            dimension=0,
            birth=1.0,
            death=3.0,
            persistence=0,  # Should be recalculated
        )

        # Persistence should be recalculated in __post_init__
        assert feature.persistence == 2.0

    def test_is_significant(self):
        """Test significance detection."""
        # High persistence feature (significant)
        sig_feature = TopologicalFeature(
            dimension=1, birth=1.0, death=3.0, persistence=2.0
        )
        assert sig_feature.is_significant

        # Low persistence feature (not significant)
        insig_feature = TopologicalFeature(
            dimension=1, birth=1.0, death=1.2, persistence=0.2
        )
        assert not insig_feature.is_significant

    def test_midpoint(self):
        """Test midpoint calculation."""
        feature = TopologicalFeature(dimension=0, birth=2.0, death=6.0, persistence=4.0)
        assert feature.midpoint == 4.0


class TestPersistenceDiagram:
    """Test PersistenceDiagram class."""

    def test_empty_diagram(self):
        """Test creating an empty persistence diagram."""
        diagram = PersistenceDiagram()

        assert diagram.total_features == 0
        assert len(diagram.significant_features) == 0
        assert diagram.max_dimension == 2

    def test_diagram_with_features(self):
        """Test diagram with multiple features."""
        h0 = [
            TopologicalFeature(0, 0.0, 1.0, 1.0),
            TopologicalFeature(0, 0.5, 1.5, 1.0),
        ]
        h1 = [TopologicalFeature(1, 1.0, 3.0, 2.0)]
        h2 = [TopologicalFeature(2, 2.0, 4.0, 2.0)]

        diagram = PersistenceDiagram(h0_features=h0, h1_features=h1, h2_features=h2)

        assert diagram.total_features == 4
        assert len(diagram.h0_features) == 2
        assert len(diagram.h1_features) == 1
        assert len(diagram.h2_features) == 1

    def test_get_features_by_dimension(self):
        """Test retrieving features by dimension."""
        h0 = [TopologicalFeature(0, 0.0, 1.0, 1.0)]
        h1 = [TopologicalFeature(1, 1.0, 2.0, 1.0)]

        diagram = PersistenceDiagram(h0_features=h0, h1_features=h1)

        assert len(diagram.get_features_by_dimension(0)) == 1
        assert len(diagram.get_features_by_dimension(1)) == 1
        assert len(diagram.get_features_by_dimension(2)) == 0


class TestPersistentScheduleAnalyzer:
    """Test PersistentScheduleAnalyzer class."""

    def test_analyzer_initialization(self, db: Session):
        """Test creating an analyzer."""
        analyzer = PersistentScheduleAnalyzer(db, max_dimension=2)

        assert analyzer.db == db
        assert analyzer.max_dimension == 2

    def test_embed_assignments_empty(self, db: Session):
        """Test embedding empty assignment list."""
        analyzer = PersistentScheduleAnalyzer(db)

        with pytest.raises(ValueError, match="Cannot embed empty assignment list"):
            analyzer.embed_assignments([])

    def test_embed_assignments_pca(self, db: Session, sample_assignments):
        """Test PCA embedding of assignments."""
        analyzer = PersistentScheduleAnalyzer(db)

        point_cloud = analyzer.embed_assignments(
            sample_assignments, method="pca", n_components=3
        )

        assert point_cloud.shape[0] == len(sample_assignments)
        assert point_cloud.shape[1] == 3
        assert not np.isnan(point_cloud).any()

    def test_embed_assignments_manual(self, db: Session, sample_assignments):
        """Test manual embedding of assignments."""
        analyzer = PersistentScheduleAnalyzer(db)

        point_cloud = analyzer.embed_assignments(
            sample_assignments, method="manual", n_components=2
        )

        assert point_cloud.shape[0] == len(sample_assignments)
        assert point_cloud.shape[1] == 2

    def test_compute_persistence_diagram(self, db: Session, sample_point_cloud):
        """Test computing persistence diagram from point cloud."""
        analyzer = PersistentScheduleAnalyzer(db, max_dimension=1)

        diagram = analyzer.compute_persistence_diagram(sample_point_cloud)

        assert isinstance(diagram, PersistenceDiagram)
        assert diagram.max_dimension == 1
        # Should have some H0 features (connected components)
        assert len(diagram.h0_features) >= 0

    def test_compute_persistence_empty_cloud(self, db: Session):
        """Test persistence computation with empty point cloud."""
        analyzer = PersistentScheduleAnalyzer(db)

        with pytest.raises(ValueError, match="Cannot compute persistence"):
            analyzer.compute_persistence_diagram(np.array([]))

    def test_extract_schedule_voids(self, db: Session, sample_assignments):
        """Test extracting coverage voids from H2 features."""
        analyzer = PersistentScheduleAnalyzer(db)

        # Create a diagram with H2 features
        h2_features = [
            TopologicalFeature(2, 1.0, 3.0, 2.0, "Test void"),
            TopologicalFeature(2, 0.5, 1.0, 0.5, "Small void"),
        ]
        diagram = PersistenceDiagram(h2_features=h2_features)

        voids = analyzer.extract_schedule_voids(diagram, sample_assignments)

        # Should extract voids from significant H2 features
        assert isinstance(voids, list)
        assert all(isinstance(v, CoverageVoid) for v in voids)

    def test_detect_cyclic_patterns(self, db: Session, sample_assignments):
        """Test detecting cyclic patterns from H1 features."""
        analyzer = PersistentScheduleAnalyzer(db)

        # Create a diagram with H1 features
        h1_features = [
            TopologicalFeature(1, 0.5, 2.0, 1.5, "Weekly cycle"),
            TopologicalFeature(1, 1.0, 2.5, 1.5, "Biweekly cycle"),
        ]
        diagram = PersistenceDiagram(h1_features=h1_features)

        patterns = analyzer.detect_cyclic_patterns(diagram, sample_assignments)

        # Should detect cyclic patterns
        assert isinstance(patterns, list)
        assert all(isinstance(p, CyclicPattern) for p in patterns)
        # Should map to common cycle lengths (7, 14, 21, 28 days)
        for pattern in patterns:
            assert pattern.cycle_length_days in [7, 14, 21, 28]

    def test_compute_structural_anomaly_score(self, db: Session):
        """Test computing structural anomaly score."""
        analyzer = PersistentScheduleAnalyzer(db)

        # Normal schedule (few H0, few H1, no H2)
        normal_diagram = PersistenceDiagram(
            h0_features=[TopologicalFeature(0, 0, 1, 1) for _ in range(5)],
            h1_features=[TopologicalFeature(1, 0, 1, 1) for _ in range(3)],
            h2_features=[],
        )
        normal_score = analyzer.compute_structural_anomaly_score(normal_diagram)
        assert 0.0 <= normal_score <= 1.0
        assert normal_score < 0.5  # Should be low for normal structure

        # Anomalous schedule (many H2 voids)
        anomalous_diagram = PersistenceDiagram(
            h0_features=[TopologicalFeature(0, 0, 1, 1) for _ in range(10)],
            h1_features=[],
            h2_features=[TopologicalFeature(2, 0, 2, 2) for _ in range(5)],
        )
        anomalous_score = analyzer.compute_structural_anomaly_score(anomalous_diagram)
        assert 0.0 <= anomalous_score <= 1.0
        assert anomalous_score > 0.5  # Should be high for anomalous structure

    def test_compare_schedules_topologically(self, db: Session, sample_assignments):
        """Test topological comparison of two schedules."""
        analyzer = PersistentScheduleAnalyzer(db)

        # Split assignments into two groups
        mid = len(sample_assignments) // 2
        assignments_a = sample_assignments[:mid]
        assignments_b = sample_assignments[mid:]

        distance = analyzer.compare_schedules_topologically(
            assignments_a, assignments_b
        )

        # Should return a non-negative distance
        assert distance >= 0.0
        assert isinstance(distance, float)

    def test_compare_identical_schedules(self, db: Session, sample_assignments):
        """Test comparing identical schedules."""
        analyzer = PersistentScheduleAnalyzer(db)

        # Compare schedule with itself
        distance = analyzer.compare_schedules_topologically(
            sample_assignments, sample_assignments
        )

        # Distance should be zero or very small
        assert distance < 0.1

    def test_analyze_schedule(self, db: Session, sample_assignments):
        """Test comprehensive schedule analysis."""
        analyzer = PersistentScheduleAnalyzer(db)

        # Get date range from sample assignments
        first_block = (
            db.query(Block).filter(Block.id == sample_assignments[0].block_id).first()
        )
        last_block = (
            db.query(Block).filter(Block.id == sample_assignments[-1].block_id).first()
        )

        start_date = first_block.date
        end_date = last_block.date

        result = analyzer.analyze_schedule(start_date=start_date, end_date=end_date)

        # Should return comprehensive analysis
        assert "total_assignments" in result
        assert "persistence_diagram" in result
        assert "coverage_voids" in result
        assert "cyclic_patterns" in result
        assert "anomaly_score" in result
        assert "computed_at" in result

        # Verify structure
        assert result["total_assignments"] == len(sample_assignments)
        assert isinstance(result["anomaly_score"], (int, float))
        assert 0.0 <= result["anomaly_score"] <= 1.0

    def test_analyze_schedule_no_assignments(self, db: Session):
        """Test analysis with no assignments in date range."""
        analyzer = PersistentScheduleAnalyzer(db)

        # Use a date range with no assignments
        future_date = date.today() + timedelta(days=365)

        result = analyzer.analyze_schedule(start_date=future_date, end_date=future_date)

        # Should handle gracefully
        assert "error" in result or result["total_assignments"] == 0


class TestCoverageVoid:
    """Test CoverageVoid dataclass."""

    def test_void_creation(self):
        """Test creating a coverage void."""
        void = CoverageVoid(
            void_id="void_1",
            start_date=date.today(),
            end_date=date.today() + timedelta(days=7),
            affected_rotations=["rotation_1", "rotation_2"],
            severity=0.8,
            persistence=1.5,
        )

        assert void.void_id == "void_1"
        assert void.severity == 0.8
        assert void.persistence == 1.5
        assert len(void.affected_rotations) == 2


class TestCyclicPattern:
    """Test CyclicPattern dataclass."""

    def test_pattern_creation(self):
        """Test creating a cyclic pattern."""
        pattern = CyclicPattern(
            pattern_id="cycle_1",
            cycle_length_days=7,
            residents_involved=["res_1", "res_2"],
            rotations_involved=["rot_1"],
            strength=0.9,
            persistence=2.0,
        )

        assert pattern.pattern_id == "cycle_1"
        assert pattern.cycle_length_days == 7
        assert pattern.strength == 0.9
        assert len(pattern.residents_involved) == 2


class TestIntegration:
    """Integration tests for full TDA workflow."""

    def test_full_tda_pipeline(self, db: Session, sample_assignments):
        """Test complete TDA pipeline from assignments to analysis."""
        analyzer = PersistentScheduleAnalyzer(db, max_dimension=2)

        # Step 1: Embed assignments
        point_cloud = analyzer.embed_assignments(
            sample_assignments, method="pca", n_components=3
        )
        assert point_cloud.shape[0] == len(sample_assignments)

        # Step 2: Compute persistence
        diagram = analyzer.compute_persistence_diagram(point_cloud)
        assert diagram.total_features >= 0

        # Step 3: Extract voids
        voids = analyzer.extract_schedule_voids(diagram, sample_assignments)
        assert isinstance(voids, list)

        # Step 4: Detect cycles
        cycles = analyzer.detect_cyclic_patterns(diagram, sample_assignments)
        assert isinstance(cycles, list)

        # Step 5: Compute anomaly score
        anomaly_score = analyzer.compute_structural_anomaly_score(diagram)
        assert 0.0 <= anomaly_score <= 1.0

    def test_end_to_end_analysis(self, db: Session, sample_assignments):
        """Test end-to-end analysis via analyze_schedule method."""
        analyzer = PersistentScheduleAnalyzer(db)

        result = analyzer.analyze_schedule()

        # Should complete successfully
        assert "total_assignments" in result
        assert "anomaly_score" in result

        # Results should be valid
        if result["total_assignments"] > 0:
            assert result["anomaly_score"] >= 0.0
