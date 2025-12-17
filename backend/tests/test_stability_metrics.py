"""
Comprehensive unit tests for StabilityMetrics module.

Tests cover:
- StabilityMetrics dataclass properties and methods
- StabilityMetricsComputer with mock assignments
- Churn rate calculation
- Ripple factor analysis
- N-1 vulnerability scoring
- Stability grading
- Empty/edge cases
"""

import pytest
from datetime import date, datetime
from uuid import UUID, uuid4

from app.analytics.stability_metrics import (
    StabilityMetrics,
    StabilityMetricsComputer,
    compute_stability_metrics,
    HAS_NETWORKX,
)


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def mock_db_session():
    """Create a mock database session."""
    class MockQuery:
        def __init__(self, items):
            self.items = items
            self._filters = []

        def filter(self, *args):
            return self

        def join(self, *args):
            return self

        def all(self):
            return self.items

    class MockSession:
        def __init__(self):
            self._assignments = []

        def query(self, model):
            return MockQuery(self._assignments)

        def set_assignments(self, assignments):
            self._assignments = assignments

    return MockSession()


@pytest.fixture
def mock_assignments():
    """Create mock assignments for testing."""
    class MockAssignment:
        def __init__(self, id, person_id, block_id, rotation_template_id=None, role="primary"):
            self.id = id
            self.person_id = person_id
            self.block_id = block_id
            self.rotation_template_id = rotation_template_id
            self.role = role
            self.activity_override = None

    person1 = UUID('00000000-0000-0000-0000-000000000001')
    person2 = UUID('00000000-0000-0000-0000-000000000002')
    person3 = UUID('00000000-0000-0000-0000-000000000003')

    rotation1 = UUID('10000000-0000-0000-0000-000000000001')
    rotation2 = UUID('10000000-0000-0000-0000-000000000002')

    assignments = [
        MockAssignment(uuid4(), person1, uuid4(), rotation1, "primary"),
        MockAssignment(uuid4(), person1, uuid4(), rotation1, "primary"),
        MockAssignment(uuid4(), person2, uuid4(), rotation2, "primary"),
        MockAssignment(uuid4(), person2, uuid4(), rotation2, "primary"),
        MockAssignment(uuid4(), person3, uuid4(), rotation1, "backup"),
    ]

    return assignments


# ============================================================================
# Test StabilityMetrics Dataclass
# ============================================================================

def test_stability_metrics_creation():
    """Test basic StabilityMetrics creation."""
    metrics = StabilityMetrics(
        assignments_changed=10,
        churn_rate=0.15,
        ripple_factor=1.5,
        n1_vulnerability_score=0.3,
        new_violations=0,
        days_since_major_change=30,
        total_assignments=100,
    )

    assert metrics.assignments_changed == 10
    assert metrics.churn_rate == 0.15
    assert metrics.ripple_factor == 1.5
    assert metrics.n1_vulnerability_score == 0.3
    assert metrics.new_violations == 0
    assert metrics.days_since_major_change == 30


def test_stability_metrics_is_stable():
    """Test is_stable property."""
    # Stable schedule
    stable = StabilityMetrics(
        assignments_changed=5,
        churn_rate=0.05,
        ripple_factor=1.0,
        n1_vulnerability_score=0.2,
        new_violations=0,
        days_since_major_change=30,
    )
    assert stable.is_stable is True

    # Unstable due to high churn
    high_churn = StabilityMetrics(
        assignments_changed=50,
        churn_rate=0.50,
        ripple_factor=1.0,
        n1_vulnerability_score=0.2,
        new_violations=0,
        days_since_major_change=30,
    )
    assert high_churn.is_stable is False

    # Unstable due to violations
    has_violations = StabilityMetrics(
        assignments_changed=5,
        churn_rate=0.05,
        ripple_factor=1.0,
        n1_vulnerability_score=0.2,
        new_violations=3,
        days_since_major_change=30,
    )
    assert has_violations.is_stable is False


def test_stability_metrics_grading():
    """Test stability_grade property."""
    # Grade A - excellent stability
    grade_a = StabilityMetrics(
        assignments_changed=2,
        churn_rate=0.02,
        ripple_factor=0.5,
        n1_vulnerability_score=0.1,
        new_violations=0,
        days_since_major_change=30,
    )
    assert grade_a.stability_grade == "A"

    # Grade F - has violations
    grade_f = StabilityMetrics(
        assignments_changed=10,
        churn_rate=0.10,
        ripple_factor=1.0,
        n1_vulnerability_score=0.3,
        new_violations=5,
        days_since_major_change=30,
    )
    assert grade_f.stability_grade == "F"

    # Grade C - moderate stability
    grade_c = StabilityMetrics(
        assignments_changed=25,
        churn_rate=0.25,
        ripple_factor=2.5,
        n1_vulnerability_score=0.4,
        new_violations=0,
        days_since_major_change=30,
    )
    assert grade_c.stability_grade in ["C", "D"]


def test_stability_metrics_to_dict():
    """Test conversion to dictionary."""
    metrics = StabilityMetrics(
        assignments_changed=10,
        churn_rate=0.15,
        ripple_factor=1.5,
        n1_vulnerability_score=0.3,
        new_violations=0,
        days_since_major_change=30,
        total_assignments=100,
        computed_at=datetime(2025, 1, 1, 12, 0, 0),
    )

    result = metrics.to_dict()

    assert result["assignments_changed"] == 10
    assert result["churn_rate"] == 0.15
    assert result["ripple_factor"] == 1.5
    assert result["n1_vulnerability_score"] == 0.3
    assert result["new_violations"] == 0
    assert result["days_since_major_change"] == 30
    assert result["total_assignments"] == 100
    assert "2025-01-01" in result["computed_at"]


# ============================================================================
# Test StabilityMetricsComputer
# ============================================================================

def test_computer_initialization(mock_db_session):
    """Test StabilityMetricsComputer initialization."""
    computer = StabilityMetricsComputer(mock_db_session)
    assert computer.db is mock_db_session


def test_compute_with_no_assignments(mock_db_session):
    """Test computing metrics with no assignments."""
    computer = StabilityMetricsComputer(mock_db_session)
    metrics = computer.compute_stability_metrics()

    assert metrics.assignments_changed == 0
    assert metrics.churn_rate == 0.0
    assert metrics.ripple_factor == 0.0
    assert metrics.n1_vulnerability_score == 0.0
    assert metrics.total_assignments == 0


def test_compute_with_assignments(mock_db_session, mock_assignments):
    """Test computing metrics with actual assignments."""
    mock_db_session.set_assignments(mock_assignments)
    computer = StabilityMetricsComputer(mock_db_session)
    metrics = computer.compute_stability_metrics()

    assert metrics.total_assignments == len(mock_assignments)
    assert metrics.computed_at is not None
    assert isinstance(metrics.n1_vulnerability_score, float)
    assert 0.0 <= metrics.n1_vulnerability_score <= 1.0


def test_calculate_churn_rate_first_version(mock_assignments):
    """Test churn rate calculation for first version (no previous)."""
    computer = StabilityMetricsComputer(None)
    result = computer._calculate_churn_rate([], mock_assignments)

    assert result["changed_count"] == 0
    assert result["churn_rate"] == 0.0
    assert len(result["added"]) == len(mock_assignments)
    assert len(result["removed"]) == 0
    assert len(result["modified"]) == 0


def test_calculate_churn_rate_with_changes(mock_assignments):
    """Test churn rate calculation with actual changes."""
    computer = StabilityMetricsComputer(None)

    # Create modified version - remove one, add one new
    new_assignments = mock_assignments[1:].copy()  # Remove first

    class MockAssignment:
        def __init__(self, id, person_id, block_id, rotation_template_id=None, role="primary"):
            self.id = id
            self.person_id = person_id
            self.block_id = block_id
            self.rotation_template_id = rotation_template_id
            self.role = role
            self.activity_override = None

    new_person = UUID('00000000-0000-0000-0000-000000000009')
    new_assignments.append(MockAssignment(uuid4(), new_person, uuid4(), None, "primary"))

    result = computer._calculate_churn_rate(mock_assignments, new_assignments)

    assert result["changed_count"] == 2  # 1 removed + 1 added
    assert result["churn_rate"] == 2 / len(mock_assignments)
    assert len(result["removed"]) == 1
    assert len(result["added"]) == 1


def test_calculate_n1_vulnerability(mock_assignments):
    """Test N-1 vulnerability calculation."""
    computer = StabilityMetricsComputer(None)
    vulnerability = computer._calculate_n1_vulnerability(mock_assignments)

    assert isinstance(vulnerability, float)
    assert 0.0 <= vulnerability <= 1.0
    # Should be non-zero since we have assignments


def test_calculate_n1_vulnerability_single_point_of_failure():
    """Test N-1 vulnerability with clear single point of failure."""
    class MockAssignment:
        def __init__(self, person_id, block_id, rotation_template_id):
            self.person_id = person_id
            self.block_id = block_id
            self.rotation_template_id = rotation_template_id
            self.activity_override = None

    # One person covers a unique rotation
    person1 = UUID('00000000-0000-0000-0000-000000000001')
    person2 = UUID('00000000-0000-0000-0000-000000000002')
    rotation1 = UUID('10000000-0000-0000-0000-000000000001')  # Unique to person1
    rotation2 = UUID('10000000-0000-0000-0000-000000000002')  # Shared

    assignments = [
        MockAssignment(person1, uuid4(), rotation1),  # Unique coverage
        MockAssignment(person1, uuid4(), rotation1),
        MockAssignment(person1, uuid4(), rotation1),
        MockAssignment(person1, uuid4(), rotation2),  # Shared
        MockAssignment(person2, uuid4(), rotation2),  # Shared
    ]

    computer = StabilityMetricsComputer(None)
    vulnerability = computer._calculate_n1_vulnerability(assignments)

    # Should be high due to person1 covering unique rotation
    assert vulnerability > 0.3


def test_calculate_n1_vulnerability_empty():
    """Test N-1 vulnerability with no assignments."""
    computer = StabilityMetricsComputer(None)
    vulnerability = computer._calculate_n1_vulnerability([])

    assert vulnerability == 0.0


def test_ripple_factor_no_changes():
    """Test ripple factor with no changes."""
    computer = StabilityMetricsComputer(None)
    ripple = computer._calculate_ripple_factor([], [])

    assert ripple == 0.0


def test_ripple_factor_with_changes(mock_assignments):
    """Test ripple factor calculation with changes."""
    computer = StabilityMetricsComputer(None)
    changes = [
        ("added", mock_assignments[0].person_id, mock_assignments[0].block_id),
        ("modified", mock_assignments[1].person_id, mock_assignments[1].block_id),
    ]

    ripple = computer._calculate_ripple_factor(changes, mock_assignments)

    assert isinstance(ripple, float)
    assert ripple >= 0.0


def test_build_dependency_graph(mock_assignments):
    """Test dependency graph construction."""
    computer = StabilityMetricsComputer(None)
    graph = computer._build_dependency_graph(mock_assignments)

    # Graph should be created (or mock if NetworkX not available)
    if HAS_NETWORKX:
        import networkx as nx
        assert isinstance(graph, nx.DiGraph)
    # If no NetworkX, mock graph is returned


def test_assignment_differs():
    """Test assignment difference detection."""
    class MockAssignment:
        def __init__(self, rotation_id, role, override):
            self.rotation_template_id = rotation_id
            self.role = role
            self.activity_override = override

    computer = StabilityMetricsComputer(None)

    rotation1 = UUID('10000000-0000-0000-0000-000000000001')
    rotation2 = UUID('10000000-0000-0000-0000-000000000002')

    # Same assignments
    a1 = MockAssignment(rotation1, "primary", None)
    a2 = MockAssignment(rotation1, "primary", None)
    assert computer._assignment_differs(a1, a2) is False

    # Different rotation
    a3 = MockAssignment(rotation2, "primary", None)
    assert computer._assignment_differs(a1, a3) is True

    # Different role
    a4 = MockAssignment(rotation1, "backup", None)
    assert computer._assignment_differs(a1, a4) is True

    # Different override
    a5 = MockAssignment(rotation1, "primary", "Custom activity")
    assert computer._assignment_differs(a1, a5) is True


# ============================================================================
# Test Convenience Function
# ============================================================================

def test_compute_stability_metrics_function(mock_db_session, mock_assignments):
    """Test the convenience compute_stability_metrics function."""
    mock_db_session.set_assignments(mock_assignments)
    result = compute_stability_metrics(mock_db_session)

    assert isinstance(result, dict)
    assert "assignments_changed" in result
    assert "churn_rate" in result
    assert "ripple_factor" in result
    assert "n1_vulnerability_score" in result
    assert "new_violations" in result
    assert "days_since_major_change" in result
    assert "is_stable" in result
    assert "stability_grade" in result
    assert isinstance(result["is_stable"], bool)
    assert result["stability_grade"] in ["A", "B", "C", "D", "F"]


# ============================================================================
# Integration/Edge Cases
# ============================================================================

def test_date_range_filtering(mock_db_session, mock_assignments):
    """Test computing metrics with date range."""
    mock_db_session.set_assignments(mock_assignments)
    computer = StabilityMetricsComputer(mock_db_session)

    start = date(2025, 1, 1)
    end = date(2025, 12, 31)

    metrics = computer.compute_stability_metrics(start_date=start, end_date=end)

    # Should complete without error
    assert metrics is not None
    assert metrics.total_assignments == len(mock_assignments)


def test_metrics_with_version_id(mock_db_session, mock_assignments):
    """Test computing metrics with version ID."""
    mock_db_session.set_assignments(mock_assignments)
    computer = StabilityMetricsComputer(mock_db_session)

    version_id = "test-version-123"
    metrics = computer.compute_stability_metrics(version_id=version_id)

    assert metrics.version_id == version_id
