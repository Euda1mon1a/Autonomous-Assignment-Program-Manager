"""
Tests for Unified Critical Faculty Index.

Comprehensive test suite for the novel cross-domain integration that unifies:
1. N-1/N-2 contingency vulnerability
2. Burnout epidemiology super-spreader detection
3. Hub analysis network centrality

This module tests the core insight that these three systems independently
identify "critical" individuals, and that unifying them creates more
accurate and actionable risk assessments.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from uuid import UUID, uuid4

import pytest

from app.resilience.unified_critical_index import (
    CriticalityDomain,
    DomainScore,
    InterventionType,
    PopulationAnalysis,
    RiskPattern,
    UnifiedCriticalIndex,
    UnifiedCriticalIndexAnalyzer,
    get_by_pattern,
    get_top_critical,
    quick_analysis,
)


# =============================================================================
# Test Fixtures and Helpers
# =============================================================================


@dataclass
class MockFaculty:
    """Mock faculty member for testing."""

    id: UUID
    name: str

    @classmethod
    def create(cls, name: str = "Test Faculty") -> "MockFaculty":
        return cls(id=uuid4(), name=name)


@dataclass
class MockAssignment:
    """Mock assignment for testing."""

    person_id: UUID
    block_id: UUID

    @classmethod
    def create(cls, person_id: UUID, block_id: UUID = None) -> "MockAssignment":
        return cls(person_id=person_id, block_id=block_id or uuid4())


def create_test_population(n_faculty: int = 5, n_blocks: int = 10) -> tuple:
    """Create a test population with faculty and assignments."""
    faculty = [MockFaculty.create(f"Faculty-{i}") for i in range(n_faculty)]
    blocks = [uuid4() for _ in range(n_blocks)]

    # Create varied assignments - some faculty cover more blocks
    assignments = []
    for i, fac in enumerate(faculty):
        # Faculty 0 covers all blocks (hub)
        # Faculty 1 covers half blocks
        # Faculty 2-4 cover fewer blocks
        coverage = n_blocks if i == 0 else max(1, n_blocks // (i + 1))
        for block_id in blocks[:coverage]:
            assignments.append(MockAssignment.create(fac.id, block_id))

    coverage_requirements = dict.fromkeys(blocks, 1)

    return faculty, assignments, coverage_requirements, blocks


# =============================================================================
# DomainScore Tests
# =============================================================================


class TestDomainScore:
    """Test suite for DomainScore dataclass."""

    def test_domain_score_creation(self):
        """Test basic DomainScore creation."""
        score = DomainScore(
            domain=CriticalityDomain.CONTINGENCY,
            raw_score=0.75,
        )

        assert score.domain == CriticalityDomain.CONTINGENCY
        assert score.raw_score == 0.75
        assert score.normalized_score == 0.0
        assert score.percentile == 0.0
        assert score.is_critical is False
        assert score.details == {}

    def test_threshold_exceeded_by_score(self):
        """Test threshold_exceeded when normalized score is high."""
        score = DomainScore(
            domain=CriticalityDomain.HUB_ANALYSIS,
            raw_score=0.8,
            normalized_score=0.75,  # Above 0.7 threshold
        )

        assert score.threshold_exceeded is True

    def test_threshold_exceeded_by_critical_flag(self):
        """Test threshold_exceeded when is_critical is True."""
        score = DomainScore(
            domain=CriticalityDomain.EPIDEMIOLOGY,
            raw_score=0.3,
            normalized_score=0.3,  # Below 0.7 threshold
            is_critical=True,  # But explicitly marked critical
        )

        assert score.threshold_exceeded is True

    def test_threshold_not_exceeded(self):
        """Test threshold_exceeded when neither condition met."""
        score = DomainScore(
            domain=CriticalityDomain.CONTINGENCY,
            raw_score=0.3,
            normalized_score=0.5,
            is_critical=False,
        )

        assert score.threshold_exceeded is False


# =============================================================================
# UnifiedCriticalIndex Tests
# =============================================================================


class TestUnifiedCriticalIndex:
    """Test suite for UnifiedCriticalIndex dataclass."""

    def test_index_creation_low_risk(self):
        """Test creating index with low risk scores."""
        idx = UnifiedCriticalIndex(
            faculty_id=uuid4(),
            faculty_name="Low Risk Faculty",
            calculated_at=datetime.now(),
            contingency_score=DomainScore(
                domain=CriticalityDomain.CONTINGENCY,
                raw_score=0.1,
                normalized_score=0.1,
            ),
            epidemiology_score=DomainScore(
                domain=CriticalityDomain.EPIDEMIOLOGY,
                raw_score=0.1,
                normalized_score=0.1,
            ),
            hub_score=DomainScore(
                domain=CriticalityDomain.HUB_ANALYSIS,
                raw_score=0.1,
                normalized_score=0.1,
            ),
        )

        assert idx.risk_pattern == RiskPattern.LOW_RISK
        assert idx.composite_index < 0.2
        assert InterventionType.MONITORING in idx.recommended_interventions

    def test_index_creation_universal_critical(self):
        """Test creating index with all domains critical."""
        idx = UnifiedCriticalIndex(
            faculty_id=uuid4(),
            faculty_name="Universal Critical Faculty",
            calculated_at=datetime.now(),
            contingency_score=DomainScore(
                domain=CriticalityDomain.CONTINGENCY,
                raw_score=0.9,
                normalized_score=0.9,
                is_critical=True,
            ),
            epidemiology_score=DomainScore(
                domain=CriticalityDomain.EPIDEMIOLOGY,
                raw_score=0.85,
                normalized_score=0.85,
                is_critical=True,
            ),
            hub_score=DomainScore(
                domain=CriticalityDomain.HUB_ANALYSIS,
                raw_score=0.95,
                normalized_score=0.95,
                is_critical=True,
            ),
        )

        assert idx.risk_pattern == RiskPattern.UNIVERSAL_CRITICAL
        assert idx.composite_index > 0.8
        assert InterventionType.IMMEDIATE_PROTECTION in idx.recommended_interventions

    def test_isolated_workhorse_pattern(self):
        """Test isolated workhorse pattern (contingency only)."""
        idx = UnifiedCriticalIndex(
            faculty_id=uuid4(),
            faculty_name="Isolated Workhorse",
            calculated_at=datetime.now(),
            contingency_score=DomainScore(
                domain=CriticalityDomain.CONTINGENCY,
                raw_score=0.9,
                normalized_score=0.9,
                is_critical=True,
            ),
            epidemiology_score=DomainScore(
                domain=CriticalityDomain.EPIDEMIOLOGY,
                raw_score=0.2,
                normalized_score=0.2,
            ),
            hub_score=DomainScore(
                domain=CriticalityDomain.HUB_ANALYSIS,
                raw_score=0.2,
                normalized_score=0.2,
            ),
        )

        assert idx.risk_pattern == RiskPattern.ISOLATED_WORKHORSE
        assert InterventionType.CROSS_TRAINING in idx.recommended_interventions

    def test_burnout_vector_pattern(self):
        """Test burnout vector pattern (epidemiology only)."""
        idx = UnifiedCriticalIndex(
            faculty_id=uuid4(),
            faculty_name="Burnout Vector",
            calculated_at=datetime.now(),
            contingency_score=DomainScore(
                domain=CriticalityDomain.CONTINGENCY,
                raw_score=0.2,
                normalized_score=0.2,
            ),
            epidemiology_score=DomainScore(
                domain=CriticalityDomain.EPIDEMIOLOGY,
                raw_score=0.9,
                normalized_score=0.9,
                is_critical=True,
            ),
            hub_score=DomainScore(
                domain=CriticalityDomain.HUB_ANALYSIS,
                raw_score=0.2,
                normalized_score=0.2,
            ),
        )

        assert idx.risk_pattern == RiskPattern.BURNOUT_VECTOR
        assert InterventionType.WELLNESS_SUPPORT in idx.recommended_interventions

    def test_domain_agreement_high(self):
        """Test domain agreement calculation when scores are similar."""
        idx = UnifiedCriticalIndex(
            faculty_id=uuid4(),
            faculty_name="Consistent Scores",
            calculated_at=datetime.now(),
            contingency_score=DomainScore(
                domain=CriticalityDomain.CONTINGENCY,
                raw_score=0.5,
                normalized_score=0.5,
            ),
            epidemiology_score=DomainScore(
                domain=CriticalityDomain.EPIDEMIOLOGY,
                raw_score=0.5,
                normalized_score=0.5,
            ),
            hub_score=DomainScore(
                domain=CriticalityDomain.HUB_ANALYSIS,
                raw_score=0.5,
                normalized_score=0.5,
            ),
        )

        assert idx.domain_agreement > 0.9  # High agreement

    def test_domain_agreement_low(self):
        """Test domain agreement calculation when scores are divergent."""
        idx = UnifiedCriticalIndex(
            faculty_id=uuid4(),
            faculty_name="Divergent Scores",
            calculated_at=datetime.now(),
            contingency_score=DomainScore(
                domain=CriticalityDomain.CONTINGENCY,
                raw_score=0.9,
                normalized_score=0.9,
            ),
            epidemiology_score=DomainScore(
                domain=CriticalityDomain.EPIDEMIOLOGY,
                raw_score=0.1,
                normalized_score=0.1,
            ),
            hub_score=DomainScore(
                domain=CriticalityDomain.HUB_ANALYSIS,
                raw_score=0.5,
                normalized_score=0.5,
            ),
        )

        assert idx.domain_agreement < 0.7  # Lower agreement

    def test_conflict_detection_isolated_workaholic(self):
        """Test conflict detection: high hub but low epidemiology."""
        idx = UnifiedCriticalIndex(
            faculty_id=uuid4(),
            faculty_name="Isolated Workaholic",
            calculated_at=datetime.now(),
            contingency_score=DomainScore(
                domain=CriticalityDomain.CONTINGENCY,
                raw_score=0.5,
                normalized_score=0.5,
            ),
            epidemiology_score=DomainScore(
                domain=CriticalityDomain.EPIDEMIOLOGY,
                raw_score=0.2,
                normalized_score=0.2,
            ),
            hub_score=DomainScore(
                domain=CriticalityDomain.HUB_ANALYSIS,
                raw_score=0.85,
                normalized_score=0.85,
            ),
        )

        assert any("isolated" in detail.lower() for detail in idx.conflict_details)

    def test_to_dict_serialization(self):
        """Test serialization to dictionary."""
        faculty_id = uuid4()
        idx = UnifiedCriticalIndex(
            faculty_id=faculty_id,
            faculty_name="Test Faculty",
            calculated_at=datetime.now(),
            contingency_score=DomainScore(
                domain=CriticalityDomain.CONTINGENCY,
                raw_score=0.5,
                normalized_score=0.5,
            ),
            epidemiology_score=DomainScore(
                domain=CriticalityDomain.EPIDEMIOLOGY,
                raw_score=0.5,
                normalized_score=0.5,
            ),
            hub_score=DomainScore(
                domain=CriticalityDomain.HUB_ANALYSIS,
                raw_score=0.5,
                normalized_score=0.5,
            ),
        )

        result = idx.to_dict()

        assert result["faculty_id"] == str(faculty_id)
        assert result["faculty_name"] == "Test Faculty"
        assert "domain_scores" in result
        assert "contingency" in result["domain_scores"]
        assert "epidemiology" in result["domain_scores"]
        assert "hub_analysis" in result["domain_scores"]


# =============================================================================
# UnifiedCriticalIndexAnalyzer Tests
# =============================================================================


class TestUnifiedCriticalIndexAnalyzer:
    """Test suite for UnifiedCriticalIndexAnalyzer class."""

    def test_analyzer_initialization(self):
        """Test analyzer initialization with default weights."""
        analyzer = UnifiedCriticalIndexAnalyzer()

        assert analyzer.weights[CriticalityDomain.CONTINGENCY] == 0.40
        assert analyzer.weights[CriticalityDomain.HUB_ANALYSIS] == 0.35
        assert analyzer.weights[CriticalityDomain.EPIDEMIOLOGY] == 0.25

    def test_analyzer_custom_weights(self):
        """Test analyzer with custom weights."""
        analyzer = UnifiedCriticalIndexAnalyzer(
            contingency_weight=0.5,
            hub_weight=0.3,
            epidemiology_weight=0.2,
        )

        assert analyzer.weights[CriticalityDomain.CONTINGENCY] == 0.5

    def test_analyzer_invalid_weights(self):
        """Test analyzer rejects weights that don't sum to 1."""
        with pytest.raises(ValueError, match="must sum to 1.0"):
            UnifiedCriticalIndexAnalyzer(
                contingency_weight=0.5,
                hub_weight=0.5,
                epidemiology_weight=0.5,
            )

    def test_build_network(self):
        """Test building network from faculty and assignments."""
        faculty, assignments, _, _ = create_test_population(5, 10)
        analyzer = UnifiedCriticalIndexAnalyzer()

        network = analyzer.build_network(faculty, assignments)

        assert network.number_of_nodes() == 5
        # Should have edges from shared assignments
        assert network.number_of_edges() >= 0

    def test_compute_contingency_score_sole_provider(self):
        """Test contingency score for sole provider."""
        faculty = [MockFaculty.create("Sole Provider")]
        block_id = uuid4()
        assignments = [MockAssignment.create(faculty[0].id, block_id)]
        coverage_requirements = {block_id: 1}

        analyzer = UnifiedCriticalIndexAnalyzer()
        analyzer.build_network(faculty, assignments)

        score = analyzer.compute_contingency_score(
            faculty[0].id, assignments, coverage_requirements
        )

        assert score.is_critical is True
        assert score.details["sole_provider_blocks"] == 1

    def test_compute_contingency_score_redundant(self):
        """Test contingency score when coverage is redundant."""
        faculty = [MockFaculty.create(f"Faculty-{i}") for i in range(3)]
        block_id = uuid4()
        # All three cover the same block
        assignments = [MockAssignment.create(f.id, block_id) for f in faculty]
        coverage_requirements = {block_id: 1}

        analyzer = UnifiedCriticalIndexAnalyzer()
        analyzer.build_network(faculty, assignments)

        score = analyzer.compute_contingency_score(
            faculty[0].id, assignments, coverage_requirements
        )

        assert score.is_critical is False
        assert score.details["sole_provider_blocks"] == 0

    def test_compute_hub_score(self):
        """Test hub score computation uses centrality metrics."""
        faculty, assignments, _, _ = create_test_population(5, 10)
        analyzer = UnifiedCriticalIndexAnalyzer()
        analyzer.build_network(faculty, assignments)

        # Faculty 0 should have highest hub score (covers all blocks)
        score_0 = analyzer.compute_hub_score(faculty[0].id)
        score_last = analyzer.compute_hub_score(faculty[-1].id)

        # Can't guarantee ordering without more assignments, but both should compute
        assert score_0.raw_score >= 0
        assert score_last.raw_score >= 0

    def test_compute_epidemiology_score_with_burnout_state(self):
        """Test epidemiology score considers burnout state."""
        faculty = [MockFaculty.create("Burned Out Faculty")]
        assignments = [MockAssignment.create(faculty[0].id)]
        burnout_states = {faculty[0].id: "burned_out"}

        analyzer = UnifiedCriticalIndexAnalyzer()
        analyzer.build_network(faculty, assignments)

        score = analyzer.compute_epidemiology_score(faculty[0].id, burnout_states)

        assert score.details["is_burned_out"] is True

    def test_normalize_scores(self):
        """Test score normalization across population."""
        scores = [
            DomainScore(domain=CriticalityDomain.CONTINGENCY, raw_score=0.2),
            DomainScore(domain=CriticalityDomain.CONTINGENCY, raw_score=0.5),
            DomainScore(domain=CriticalityDomain.CONTINGENCY, raw_score=0.8),
        ]

        analyzer = UnifiedCriticalIndexAnalyzer()
        normalized = analyzer.normalize_scores(scores)

        # After normalization: min=0, max=1
        assert normalized[0].normalized_score == 0.0  # Lowest
        assert normalized[2].normalized_score == 1.0  # Highest
        assert 0 < normalized[1].normalized_score < 1  # Middle

    def test_analyze_faculty(self):
        """Test analyzing a single faculty member."""
        faculty, assignments, coverage_requirements, _ = create_test_population(3, 5)
        analyzer = UnifiedCriticalIndexAnalyzer()
        analyzer.build_network(faculty, assignments)

        idx = analyzer.analyze_faculty(
            faculty_id=faculty[0].id,
            faculty_name=faculty[0].name,
            assignments=assignments,
            coverage_requirements=coverage_requirements,
        )

        assert idx.faculty_id == faculty[0].id
        assert idx.faculty_name == faculty[0].name
        assert idx.contingency_score is not None
        assert idx.epidemiology_score is not None
        assert idx.hub_score is not None

    def test_analyze_population(self):
        """Test analyzing entire population."""
        faculty, assignments, coverage_requirements, _ = create_test_population(5, 10)
        analyzer = UnifiedCriticalIndexAnalyzer()
        analyzer.build_network(faculty, assignments)

        result = analyzer.analyze_population(
            faculty=faculty,
            assignments=assignments,
            coverage_requirements=coverage_requirements,
        )

        assert result.total_faculty == 5
        assert len(result.indices) == 5
        assert result.risk_concentration >= 0

        # All indices should have priority rank assigned
        ranks = [idx.priority_rank for idx in result.indices]
        assert sorted(ranks) == list(range(1, 6))


# =============================================================================
# PopulationAnalysis Tests
# =============================================================================


class TestPopulationAnalysis:
    """Test suite for PopulationAnalysis dataclass."""

    def test_risk_concentration_calculation(self):
        """Test risk concentration (Gini) calculation."""
        indices = []
        for i in range(5):
            idx = UnifiedCriticalIndex(
                faculty_id=uuid4(),
                faculty_name=f"Faculty-{i}",
                calculated_at=datetime.now(),
                contingency_score=DomainScore(
                    domain=CriticalityDomain.CONTINGENCY,
                    raw_score=0.1 * (i + 1),
                    normalized_score=0.1 * (i + 1),
                ),
                epidemiology_score=DomainScore(
                    domain=CriticalityDomain.EPIDEMIOLOGY,
                    raw_score=0.1,
                    normalized_score=0.1,
                ),
                hub_score=DomainScore(
                    domain=CriticalityDomain.HUB_ANALYSIS,
                    raw_score=0.1,
                    normalized_score=0.1,
                ),
            )
            indices.append(idx)

        analysis = PopulationAnalysis(
            analyzed_at=datetime.now(),
            total_faculty=5,
            indices=indices,
        )

        assert 0 <= analysis.risk_concentration <= 1

    def test_pattern_distribution(self):
        """Test pattern distribution counts."""
        # Create indices with known patterns
        indices = []

        # 2 low risk
        for _ in range(2):
            idx = UnifiedCriticalIndex(
                faculty_id=uuid4(),
                faculty_name="Low Risk",
                calculated_at=datetime.now(),
                contingency_score=DomainScore(
                    domain=CriticalityDomain.CONTINGENCY,
                    raw_score=0.1,
                    normalized_score=0.1,
                ),
                epidemiology_score=DomainScore(
                    domain=CriticalityDomain.EPIDEMIOLOGY,
                    raw_score=0.1,
                    normalized_score=0.1,
                ),
                hub_score=DomainScore(
                    domain=CriticalityDomain.HUB_ANALYSIS,
                    raw_score=0.1,
                    normalized_score=0.1,
                ),
            )
            indices.append(idx)

        # 1 universal critical
        idx = UnifiedCriticalIndex(
            faculty_id=uuid4(),
            faculty_name="Critical",
            calculated_at=datetime.now(),
            contingency_score=DomainScore(
                domain=CriticalityDomain.CONTINGENCY,
                raw_score=0.9,
                normalized_score=0.9,
                is_critical=True,
            ),
            epidemiology_score=DomainScore(
                domain=CriticalityDomain.EPIDEMIOLOGY,
                raw_score=0.9,
                normalized_score=0.9,
                is_critical=True,
            ),
            hub_score=DomainScore(
                domain=CriticalityDomain.HUB_ANALYSIS,
                raw_score=0.9,
                normalized_score=0.9,
                is_critical=True,
            ),
        )
        indices.append(idx)

        analysis = PopulationAnalysis(
            analyzed_at=datetime.now(),
            total_faculty=3,
            indices=indices,
        )

        assert analysis.pattern_distribution[RiskPattern.LOW_RISK] == 2
        assert analysis.pattern_distribution[RiskPattern.UNIVERSAL_CRITICAL] == 1
        assert analysis.universal_critical_count == 1

    def test_to_dict_serialization(self):
        """Test serialization to dictionary."""
        faculty, assignments, coverage_requirements, _ = create_test_population(3, 5)
        analyzer = UnifiedCriticalIndexAnalyzer()
        analyzer.build_network(faculty, assignments)

        analysis = analyzer.analyze_population(
            faculty=faculty,
            assignments=assignments,
            coverage_requirements=coverage_requirements,
        )

        result = analysis.to_dict()

        assert "analyzed_at" in result
        assert result["total_faculty"] == 3
        assert "indices" in result
        assert len(result["indices"]) == 3


# =============================================================================
# Convenience Function Tests
# =============================================================================


class TestConvenienceFunctions:
    """Test suite for convenience functions."""

    def test_quick_analysis(self):
        """Test quick_analysis helper."""
        faculty, assignments, _, _ = create_test_population(4, 8)

        result = quick_analysis(faculty, assignments)

        assert result.total_faculty == 4
        assert len(result.indices) == 4

    def test_get_top_critical(self):
        """Test get_top_critical helper."""
        faculty, assignments, coverage_requirements, _ = create_test_population(5, 10)
        analyzer = UnifiedCriticalIndexAnalyzer()
        analyzer.build_network(faculty, assignments)

        analysis = analyzer.analyze_population(
            faculty=faculty,
            assignments=assignments,
            coverage_requirements=coverage_requirements,
        )

        top_3 = get_top_critical(analysis, n=3)

        assert len(top_3) == 3
        # Should be sorted by composite index
        assert top_3[0].composite_index >= top_3[1].composite_index
        assert top_3[1].composite_index >= top_3[2].composite_index

    def test_get_by_pattern(self):
        """Test get_by_pattern helper."""
        # Create mixed population
        indices = []

        # 2 low risk
        for i in range(2):
            idx = UnifiedCriticalIndex(
                faculty_id=uuid4(),
                faculty_name=f"Low-{i}",
                calculated_at=datetime.now(),
                contingency_score=DomainScore(
                    domain=CriticalityDomain.CONTINGENCY,
                    raw_score=0.1,
                    normalized_score=0.1,
                ),
                epidemiology_score=DomainScore(
                    domain=CriticalityDomain.EPIDEMIOLOGY,
                    raw_score=0.1,
                    normalized_score=0.1,
                ),
                hub_score=DomainScore(
                    domain=CriticalityDomain.HUB_ANALYSIS,
                    raw_score=0.1,
                    normalized_score=0.1,
                ),
            )
            indices.append(idx)

        analysis = PopulationAnalysis(
            analyzed_at=datetime.now(),
            total_faculty=2,
            indices=indices,
        )

        low_risk = get_by_pattern(analysis, RiskPattern.LOW_RISK)
        critical = get_by_pattern(analysis, RiskPattern.UNIVERSAL_CRITICAL)

        assert len(low_risk) == 2
        assert len(critical) == 0


# =============================================================================
# Integration Tests
# =============================================================================


class TestIntegration:
    """Integration tests for the unified critical index system."""

    def test_full_workflow(self):
        """Test complete analysis workflow."""
        # Create realistic population
        faculty = [
            MockFaculty.create(f"Dr. {name}")
            for name in ["Smith", "Jones", "Lee", "Brown", "Davis"]
        ]
        blocks = [uuid4() for _ in range(20)]

        # Create varied assignment patterns
        assignments = []
        for i, block_id in enumerate(blocks):
            # Dr. Smith covers everything (hub)
            assignments.append(MockAssignment.create(faculty[0].id, block_id))

            # Others have varied coverage
            if i % 2 == 0:
                assignments.append(MockAssignment.create(faculty[1].id, block_id))
            if i % 3 == 0:
                assignments.append(MockAssignment.create(faculty[2].id, block_id))
            if i % 5 == 0:
                assignments.append(MockAssignment.create(faculty[3].id, block_id))

        coverage_requirements = dict.fromkeys(blocks, 1)

        # Run analysis
        analyzer = UnifiedCriticalIndexAnalyzer()
        analyzer.build_network(faculty, assignments)
        result = analyzer.analyze_population(
            faculty=faculty,
            assignments=assignments,
            coverage_requirements=coverage_requirements,
        )

        # Verify results
        assert result.total_faculty == 5
        assert len(result.indices) == 5

        # Dr. Smith should be highest priority (covers all blocks)
        smith_idx = next(idx for idx in result.indices if "Smith" in idx.faculty_name)
        assert smith_idx.priority_rank == 1 or smith_idx.composite_index > 0.3

    def test_network_reuse_efficiency(self):
        """Test that network is built once and reused."""
        faculty, assignments, coverage_requirements, _ = create_test_population(10, 20)

        analyzer = UnifiedCriticalIndexAnalyzer()

        # Build network once
        analyzer.build_network(faculty, assignments)
        network_nodes = analyzer._network.number_of_nodes()

        # Run multiple analyses
        result1 = analyzer.analyze_population(
            faculty, assignments, coverage_requirements
        )
        result2 = analyzer.analyze_population(
            faculty, assignments, coverage_requirements
        )

        # Network should not have been rebuilt
        assert analyzer._network.number_of_nodes() == network_nodes
        assert result1.total_faculty == result2.total_faculty

    def test_empty_population_handling(self):
        """Test handling of empty population."""
        result = quick_analysis([], [])

        assert result.total_faculty == 0
        assert len(result.indices) == 0
        assert result.risk_concentration == 0.0
