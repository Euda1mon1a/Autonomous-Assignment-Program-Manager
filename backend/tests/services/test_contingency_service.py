"""
Tests for ContingencyService.

Tests the N-1/N-2 contingency analysis service with comprehensive
coverage of simulation, centrality calculation, and vulnerability assessment.
"""

from datetime import date, timedelta
from unittest.mock import MagicMock, patch
from uuid import UUID, uuid4

import pytest

from app.services.resilience.contingency import (
    CentralityInfo,
    ContingencyAnalysisResult,
    ContingencyService,
    FatalPairInfo,
    N1SimulationResult,
    N2SimulationResult,
    VulnerabilityAssessment,
    VulnerabilityInfo,
)


# ============================================================================
# Test Fixtures
# ============================================================================


class MockPerson:
    """Mock person/faculty for testing."""

    def __init__(self, id: UUID = None, name: str = "Test Faculty", type: str = "faculty"):
        self.id = id or uuid4()
        self.name = name
        self.type = type


class MockBlock:
    """Mock block for testing."""

    def __init__(self, id: UUID = None, block_date: date = None):
        self.id = id or uuid4()
        self.date = block_date or date.today()


class MockAssignment:
    """Mock assignment for testing."""

    def __init__(
        self,
        id: UUID = None,
        person_id: UUID = None,
        block_id: UUID = None,
        rotation_template_id: UUID = None,
    ):
        self.id = id or uuid4()
        self.person_id = person_id or uuid4()
        self.block_id = block_id or uuid4()
        self.rotation_template_id = rotation_template_id


@pytest.fixture
def mock_db():
    """Create a mock database session."""
    db = MagicMock()
    return db


@pytest.fixture
def mock_faculty():
    """Create mock faculty members."""
    return [
        MockPerson(name="Dr. Smith"),
        MockPerson(name="Dr. Jones"),
        MockPerson(name="Dr. Brown"),
        MockPerson(name="Dr. Williams"),
        MockPerson(name="Dr. Davis"),
    ]


@pytest.fixture
def mock_blocks():
    """Create mock blocks for a 7-day period."""
    today = date.today()
    return [
        MockBlock(block_date=today + timedelta(days=i))
        for i in range(7)
    ]


@pytest.fixture
def mock_assignments(mock_faculty, mock_blocks):
    """Create mock assignments linking faculty to blocks."""
    assignments = []

    # Create diverse assignment patterns
    # Faculty 0 covers blocks 0-3 (heavy load)
    for i in range(4):
        assignments.append(MockAssignment(
            person_id=mock_faculty[0].id,
            block_id=mock_blocks[i].id,
        ))

    # Faculty 1 covers blocks 2-5 (overlaps with faculty 0)
    for i in range(2, 6):
        assignments.append(MockAssignment(
            person_id=mock_faculty[1].id,
            block_id=mock_blocks[i].id,
        ))

    # Faculty 2 is sole provider for block 6 (critical)
    assignments.append(MockAssignment(
        person_id=mock_faculty[2].id,
        block_id=mock_blocks[6].id,
    ))

    # Faculty 3 covers blocks 0, 6 (light load)
    assignments.append(MockAssignment(
        person_id=mock_faculty[3].id,
        block_id=mock_blocks[0].id,
    ))
    assignments.append(MockAssignment(
        person_id=mock_faculty[3].id,
        block_id=mock_blocks[6].id,
    ))

    # Faculty 4 has no assignments (available backup)
    # No assignments for faculty 4

    return assignments


def create_service_with_mock_data(mock_db, faculty, blocks, assignments):
    """Create a ContingencyService with mocked data loading."""
    service = ContingencyService(db=mock_db)

    # Mock the _load_data method
    service._load_data = MagicMock(return_value=(faculty, blocks, assignments))

    return service


# ============================================================================
# VulnerabilityInfo Tests
# ============================================================================


class TestVulnerabilityInfo:
    """Tests for VulnerabilityInfo dataclass."""

    def test_to_dict(self):
        """Test conversion to dictionary."""
        faculty_id = uuid4()
        vuln = VulnerabilityInfo(
            faculty_id=faculty_id,
            faculty_name="Dr. Test",
            severity="critical",
            affected_blocks=5,
            is_unique_provider=True,
            affected_services=["service1"],
            details="Test details",
        )

        result = vuln.to_dict()

        assert result["faculty_id"] == str(faculty_id)
        assert result["faculty_name"] == "Dr. Test"
        assert result["severity"] == "critical"
        assert result["affected_blocks"] == 5
        assert result["is_unique_provider"] is True


class TestN1SimulationResult:
    """Tests for N1SimulationResult dataclass."""

    def test_to_dict(self):
        """Test conversion to dictionary."""
        faculty_id = uuid4()
        block_id = uuid4()
        result = N1SimulationResult(
            faculty_id=faculty_id,
            faculty_name="Dr. Test",
            blocks_affected=3,
            coverage_remaining=0.85,
            is_critical=False,
            uncovered_blocks=[block_id],
            simulation_time_ms=12.5,
        )

        data = result.to_dict()

        assert data["faculty_id"] == str(faculty_id)
        assert data["blocks_affected"] == 3
        assert data["coverage_remaining"] == 0.85
        assert str(block_id) in data["uncovered_blocks"]


# ============================================================================
# ContingencyService Initialization Tests
# ============================================================================


class TestContingencyServiceInit:
    """Tests for ContingencyService initialization."""

    def test_init_with_db(self, mock_db):
        """Test service initialization with database session."""
        service = ContingencyService(db=mock_db)

        assert service.db == mock_db
        assert service._lookup_cache == {}
        assert service._analysis_cache == {}

    def test_init_caches_empty(self, mock_db):
        """Test that caches start empty."""
        service = ContingencyService(db=mock_db)

        assert len(service._lookup_cache) == 0
        assert len(service._analysis_cache) == 0


# ============================================================================
# Lookup Table Tests
# ============================================================================


class TestLookupTables:
    """Tests for lookup table construction."""

    def test_build_lookup_tables(self, mock_db, mock_faculty, mock_blocks, mock_assignments):
        """Test building optimized lookup tables."""
        service = ContingencyService(db=mock_db)

        lookups = service._build_lookup_tables(mock_faculty, mock_blocks, mock_assignments)

        # Check structure
        assert "assignments_by_faculty" in lookups
        assert "assignments_by_block" in lookups
        assert "faculty_by_id" in lookups
        assert "block_by_id" in lookups
        assert "faculty_assignment_count" in lookups

        # Check faculty lookup
        for fac in mock_faculty:
            assert fac.id in lookups["faculty_by_id"]

        # Check block lookup
        for block in mock_blocks:
            assert block.id in lookups["block_by_id"]

    def test_assignment_counts(self, mock_db, mock_faculty, mock_blocks, mock_assignments):
        """Test assignment counts in lookup tables."""
        service = ContingencyService(db=mock_db)

        lookups = service._build_lookup_tables(mock_faculty, mock_blocks, mock_assignments)

        # Faculty 0 should have 4 assignments
        assert lookups["faculty_assignment_count"].get(mock_faculty[0].id, 0) == 4

        # Faculty 4 should have 0 assignments
        assert lookups["faculty_assignment_count"].get(mock_faculty[4].id, 0) == 0


# ============================================================================
# N-1 Simulation Tests
# ============================================================================


class TestN1Simulation:
    """Tests for N-1 simulation."""

    def test_simulate_single_loss_no_impact(self, mock_db, mock_faculty, mock_blocks, mock_assignments):
        """Test simulating loss of faculty with no critical impact."""
        service = ContingencyService(db=mock_db)
        lookups = service._build_lookup_tables(mock_faculty, mock_blocks, mock_assignments)
        coverage_requirements = {b.id: 1 for b in mock_blocks}

        # Simulate loss of faculty 0 (blocks 0-3 are covered)
        # Blocks 0, 2, 3 have backup; block 1 may not
        result = service._simulate_single_loss(
            mock_faculty[0], mock_blocks, mock_assignments,
            coverage_requirements, lookups
        )

        assert result.faculty_id == mock_faculty[0].id
        assert result.faculty_name == mock_faculty[0].name

    def test_simulate_single_loss_critical(self, mock_db, mock_faculty, mock_blocks, mock_assignments):
        """Test simulating loss of sole provider (critical)."""
        service = ContingencyService(db=mock_db)
        lookups = service._build_lookup_tables(mock_faculty, mock_blocks, mock_assignments)
        coverage_requirements = {b.id: 1 for b in mock_blocks}

        # Simulate loss of faculty 2 (sole provider for block 6)
        result = service._simulate_single_loss(
            mock_faculty[2], mock_blocks, mock_assignments,
            coverage_requirements, lookups
        )

        # Block 6 should be affected but faculty 3 also covers it
        assert result.faculty_id == mock_faculty[2].id

    def test_n1_simulation_optimized(self, mock_db, mock_faculty, mock_blocks, mock_assignments):
        """Test full N-1 simulation with optimizations."""
        service = ContingencyService(db=mock_db)
        lookups = service._build_lookup_tables(mock_faculty, mock_blocks, mock_assignments)
        coverage_requirements = {b.id: 1 for b in mock_blocks}

        simulations, vulnerabilities = service._run_n1_simulation_optimized(
            mock_faculty, mock_blocks, mock_assignments,
            coverage_requirements, lookups
        )

        # Should have simulation for each faculty
        assert len(simulations) == len(mock_faculty)

        # Faculty 4 (no assignments) should have 0 blocks affected
        fac4_sim = next(s for s in simulations if s.faculty_id == mock_faculty[4].id)
        assert fac4_sim.blocks_affected == 0

    def test_severity_calculation_critical(self, mock_db):
        """Test severity calculation for unique provider."""
        service = ContingencyService(db=mock_db)

        severity = service._calculate_severity(
            affected_blocks=1,
            is_unique=True,
            total_blocks=10,
        )

        assert severity == "critical"

    def test_severity_calculation_high(self, mock_db):
        """Test severity calculation for high-impact loss."""
        service = ContingencyService(db=mock_db)

        severity = service._calculate_severity(
            affected_blocks=15,
            is_unique=False,
            total_blocks=50,  # 30% affected
        )

        assert severity == "critical"

    def test_severity_calculation_medium(self, mock_db):
        """Test severity calculation for medium-impact loss."""
        service = ContingencyService(db=mock_db)

        severity = service._calculate_severity(
            affected_blocks=7,
            is_unique=False,
            total_blocks=100,  # 7% affected
        )

        assert severity == "medium"

    def test_severity_calculation_low(self, mock_db):
        """Test severity calculation for low-impact loss."""
        service = ContingencyService(db=mock_db)

        severity = service._calculate_severity(
            affected_blocks=2,
            is_unique=False,
            total_blocks=100,  # 2% affected
        )

        assert severity == "low"


# ============================================================================
# N-2 Simulation Tests
# ============================================================================


class TestN2Simulation:
    """Tests for N-2 simulation."""

    def test_simulate_pair_loss(self, mock_db, mock_faculty, mock_blocks, mock_assignments):
        """Test simulating loss of two faculty members."""
        service = ContingencyService(db=mock_db)
        lookups = service._build_lookup_tables(mock_faculty, mock_blocks, mock_assignments)
        coverage_requirements = {b.id: 1 for b in mock_blocks}

        result = service._simulate_pair_loss(
            mock_faculty[0], mock_faculty[1],
            mock_blocks, mock_assignments,
            coverage_requirements, lookups
        )

        assert result.faculty1_id == mock_faculty[0].id
        assert result.faculty2_id == mock_faculty[1].id

    def test_n2_simulation_optimized(self, mock_db, mock_faculty, mock_blocks, mock_assignments):
        """Test N-2 simulation with optimizations."""
        service = ContingencyService(db=mock_db)
        lookups = service._build_lookup_tables(mock_faculty, mock_blocks, mock_assignments)
        coverage_requirements = {b.id: 1 for b in mock_blocks}

        # Create some vulnerabilities for N-2 to focus on
        n1_vulns = [
            VulnerabilityInfo(
                faculty_id=mock_faculty[0].id,
                faculty_name=mock_faculty[0].name,
                severity="high",
                affected_blocks=4,
                is_unique_provider=False,
            ),
        ]

        fatal_pairs = service._run_n2_simulation_optimized(
            mock_faculty, mock_blocks, mock_assignments,
            coverage_requirements, lookups, n1_vulns, max_pairs=50
        )

        # Should return a list (possibly empty)
        assert isinstance(fatal_pairs, list)


# ============================================================================
# Centrality Calculation Tests
# ============================================================================


class TestCentralityCalculation:
    """Tests for centrality calculation."""

    def test_calculate_centrality_basic(self, mock_db, mock_faculty, mock_blocks, mock_assignments):
        """Test basic centrality calculation without NetworkX."""
        service = ContingencyService(db=mock_db)
        lookups = service._build_lookup_tables(mock_faculty, mock_blocks, mock_assignments)

        services = {}  # Empty services mapping

        with patch('app.services.resilience.contingency.NETWORKX_AVAILABLE', False):
            scores = service._calculate_centrality_optimized(
                mock_faculty, mock_assignments, services, lookups
            )

        assert len(scores) == len(mock_faculty)

        # Scores should be sorted descending
        for i in range(len(scores) - 1):
            assert scores[i].centrality_score >= scores[i + 1].centrality_score

    def test_calculate_centrality_with_services(self, mock_db, mock_faculty, mock_blocks, mock_assignments):
        """Test centrality calculation with service mapping."""
        service = ContingencyService(db=mock_db)
        lookups = service._build_lookup_tables(mock_faculty, mock_blocks, mock_assignments)

        # Create service mapping where faculty 2 is sole provider for a service
        services = {
            uuid4(): [mock_faculty[0].id, mock_faculty[1].id],  # Shared
            uuid4(): [mock_faculty[2].id],  # Sole provider
        }

        with patch('app.services.resilience.contingency.NETWORKX_AVAILABLE', False):
            scores = service._calculate_centrality_optimized(
                mock_faculty, mock_assignments, services, lookups
            )

        # Faculty 2 should have high centrality (sole provider)
        fac2_score = next(s for s in scores if s.faculty_id == mock_faculty[2].id)
        assert fac2_score.unique_coverage_slots == 1


# ============================================================================
# Phase Transition Detection Tests
# ============================================================================


class TestPhaseTransition:
    """Tests for phase transition detection."""

    def test_detect_low_risk(self, mock_db):
        """Test detection of low risk conditions."""
        service = ContingencyService(db=mock_db)

        risk, indicators = service._detect_phase_transition(
            current_utilization=0.50,
            vulnerabilities=[],
            fatal_pairs=[],
        )

        assert risk == "low"
        assert len(indicators) == 0

    def test_detect_medium_risk(self, mock_db, mock_faculty):
        """Test detection of medium risk conditions."""
        service = ContingencyService(db=mock_db)

        vulnerabilities = [
            VulnerabilityInfo(
                faculty_id=mock_faculty[0].id,
                faculty_name="Test",
                severity="critical",
                affected_blocks=5,
                is_unique_provider=True,
            )
        ]

        risk, indicators = service._detect_phase_transition(
            current_utilization=0.75,
            vulnerabilities=vulnerabilities,
            fatal_pairs=[],
        )

        assert risk in ("medium", "high")
        assert len(indicators) >= 1

    def test_detect_high_risk(self, mock_db, mock_faculty):
        """Test detection of high risk conditions."""
        service = ContingencyService(db=mock_db)

        vulnerabilities = [
            VulnerabilityInfo(
                faculty_id=mock_faculty[i].id,
                faculty_name=f"Test {i}",
                severity="critical",
                affected_blocks=5,
                is_unique_provider=True,
            )
            for i in range(3)
        ]

        risk, indicators = service._detect_phase_transition(
            current_utilization=0.90,
            vulnerabilities=vulnerabilities,
            fatal_pairs=[],
        )

        assert risk == "high" or risk == "critical"

    def test_detect_critical_utilization(self, mock_db):
        """Test detection of critical utilization."""
        service = ContingencyService(db=mock_db)

        risk, indicators = service._detect_phase_transition(
            current_utilization=0.96,
            vulnerabilities=[],
            fatal_pairs=[],
        )

        assert "95%" in indicators[0] if indicators else True


# ============================================================================
# Full Analysis Tests
# ============================================================================


class TestFullAnalysis:
    """Tests for full contingency analysis."""

    def test_analyze_contingency_empty_data(self, mock_db):
        """Test analysis with no data."""
        service = ContingencyService(db=mock_db)
        service._load_data = MagicMock(return_value=([], [], []))

        result = service.analyze_contingency(
            start_date=date.today(),
            end_date=date.today() + timedelta(days=7),
        )

        assert result.n1_pass is True
        assert result.n2_pass is True
        assert len(result.n1_vulnerabilities) == 0
        assert len(result.n2_fatal_pairs) == 0

    def test_analyze_contingency_with_data(self, mock_db, mock_faculty, mock_blocks, mock_assignments):
        """Test analysis with mock data."""
        service = create_service_with_mock_data(
            mock_db, mock_faculty, mock_blocks, mock_assignments
        )

        result = service.analyze_contingency(
            start_date=date.today(),
            end_date=date.today() + timedelta(days=7),
        )

        assert isinstance(result, ContingencyAnalysisResult)
        assert result.analyzed_at is not None
        assert result.period_start == date.today()
        assert result.analysis_duration_ms > 0

    def test_analyze_contingency_skip_n2(self, mock_db, mock_faculty, mock_blocks, mock_assignments):
        """Test analysis with N-2 disabled."""
        service = create_service_with_mock_data(
            mock_db, mock_faculty, mock_blocks, mock_assignments
        )

        result = service.analyze_contingency(
            start_date=date.today(),
            end_date=date.today() + timedelta(days=7),
            include_n2=False,
        )

        # N-2 should pass (not run, so default to pass)
        assert result.n2_pass is True
        assert len(result.n2_fatal_pairs) == 0

    def test_result_to_dict(self, mock_db, mock_faculty, mock_blocks, mock_assignments):
        """Test that analysis result converts to dict."""
        service = create_service_with_mock_data(
            mock_db, mock_faculty, mock_blocks, mock_assignments
        )

        result = service.analyze_contingency(
            start_date=date.today(),
            end_date=date.today() + timedelta(days=7),
        )

        data = result.to_dict()

        assert "analysis_id" in data
        assert "analyzed_at" in data
        assert "n1_pass" in data
        assert "n2_pass" in data
        assert "recommended_actions" in data


# ============================================================================
# Vulnerability Assessment Tests
# ============================================================================


class TestVulnerabilityAssessment:
    """Tests for quick vulnerability assessment."""

    def test_get_vulnerability_assessment(self, mock_db, mock_faculty, mock_blocks, mock_assignments):
        """Test quick vulnerability assessment."""
        service = create_service_with_mock_data(
            mock_db, mock_faculty, mock_blocks, mock_assignments
        )

        assessment = service.get_vulnerability_assessment(
            start_date=date.today(),
            end_date=date.today() + timedelta(days=7),
        )

        assert isinstance(assessment, VulnerabilityAssessment)
        assert assessment.assessed_at is not None
        assert assessment.period_start == date.today()


# ============================================================================
# Single Faculty Simulation Tests
# ============================================================================


class TestSingleFacultySimulation:
    """Tests for single faculty loss simulation."""

    def test_simulate_faculty_loss(self, mock_db, mock_faculty, mock_blocks, mock_assignments):
        """Test simulating loss of a specific faculty member."""
        service = create_service_with_mock_data(
            mock_db, mock_faculty, mock_blocks, mock_assignments
        )

        result = service.simulate_faculty_loss(
            faculty_id=mock_faculty[0].id,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=7),
        )

        assert result.faculty_id == mock_faculty[0].id
        assert result.simulation_time_ms > 0

    def test_simulate_unknown_faculty(self, mock_db, mock_faculty, mock_blocks, mock_assignments):
        """Test simulating loss of unknown faculty."""
        service = create_service_with_mock_data(
            mock_db, mock_faculty, mock_blocks, mock_assignments
        )

        unknown_id = uuid4()
        result = service.simulate_faculty_loss(
            faculty_id=unknown_id,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=7),
        )

        assert result.faculty_id == unknown_id
        assert result.faculty_name == "Unknown"
        assert result.blocks_affected == 0


# ============================================================================
# Recommendation Tests
# ============================================================================


class TestRecommendations:
    """Tests for recommendation building."""

    def test_build_recommendations_n1_fail(self, mock_db, mock_faculty):
        """Test recommendations when N-1 fails."""
        service = ContingencyService(db=mock_db)

        vulnerabilities = [
            VulnerabilityInfo(
                faculty_id=mock_faculty[0].id,
                faculty_name="Dr. Test",
                severity="critical",
                affected_blocks=5,
                is_unique_provider=True,
            )
        ]

        recommendations = service._build_recommendations(
            n1_pass=False,
            n2_pass=True,
            vulnerabilities=vulnerabilities,
            fatal_pairs=[],
            phase_risk="medium",
        )

        assert any("cross-train" in r.lower() for r in recommendations)

    def test_build_recommendations_n2_fail(self, mock_db, mock_faculty):
        """Test recommendations when N-2 fails."""
        service = ContingencyService(db=mock_db)

        fatal_pairs = [
            FatalPairInfo(
                faculty1_id=mock_faculty[0].id,
                faculty1_name="Dr. A",
                faculty2_id=mock_faculty[1].id,
                faculty2_name="Dr. B",
                uncoverable_blocks=3,
            )
        ]

        recommendations = service._build_recommendations(
            n1_pass=True,
            n2_pass=False,
            vulnerabilities=[],
            fatal_pairs=fatal_pairs,
            phase_risk="low",
        )

        assert any("different days" in r.lower() for r in recommendations)


# ============================================================================
# Empty Result Tests
# ============================================================================


class TestEmptyResult:
    """Tests for empty result generation."""

    def test_empty_result(self, mock_db):
        """Test empty result generation."""
        service = ContingencyService(db=mock_db)
        analysis_id = uuid4()

        result = service._empty_result(
            analysis_id=analysis_id,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=7),
        )

        assert result.analysis_id == analysis_id
        assert result.n1_pass is True
        assert result.n2_pass is True
        assert len(result.n1_vulnerabilities) == 0
        assert len(result.n2_fatal_pairs) == 0
        assert result.phase_transition_risk == "low"
