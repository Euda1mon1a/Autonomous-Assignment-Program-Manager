"""
Comprehensive unit tests for Hub Vulnerability Analysis module.

Tests cover:
- FacultyCentrality scoring and risk assessment
- HubAnalyzer centrality calculation (basic and NetworkX)
- Hub identification and profiling
- Cross-training recommendations
- Hub protection planning
- Distribution reporting
- Hub status tracking
"""

from datetime import date, datetime, timedelta
from uuid import UUID, uuid4

import pytest

from app.resilience.hub_analysis import (
    HAS_NETWORKX,
    CrossTrainingPriority,
    FacultyCentrality,
    HubAnalyzer,
    HubDistributionReport,
    HubRiskLevel,
)

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def mock_faculty():
    """Create mock faculty members."""

    class MockFaculty:
        def __init__(self, id: UUID, name: str):
            self.id = id
            self.name = name

    return [
        MockFaculty(UUID("00000000-0000-0000-0000-000000000001"), "Alice"),
        MockFaculty(UUID("00000000-0000-0000-0000-000000000002"), "Bob"),
        MockFaculty(UUID("00000000-0000-0000-0000-000000000003"), "Carol"),
        MockFaculty(UUID("00000000-0000-0000-0000-000000000004"), "Dave"),
    ]


@pytest.fixture
def mock_assignments():
    """Create mock assignments."""

    class MockAssignment:
        def __init__(self, faculty_id: UUID, block_id: int):
            self.faculty_id = faculty_id
            self.block_id = block_id

    # Alice has 10 assignments, Bob has 5, Carol has 3, Dave has 0
    assignments = []
    alice_id = UUID("00000000-0000-0000-0000-000000000001")
    bob_id = UUID("00000000-0000-0000-0000-000000000002")
    carol_id = UUID("00000000-0000-0000-0000-000000000003")

    for i in range(10):
        assignments.append(MockAssignment(alice_id, i))
    for i in range(5):
        assignments.append(MockAssignment(bob_id, i + 10))
    for i in range(3):
        assignments.append(MockAssignment(carol_id, i + 15))

    return assignments


@pytest.fixture
def mock_services():
    """
    Create mock service capability mapping.

    Service distribution:
    - service_1: Only Alice (single point of failure)
    - service_2: Alice and Bob (dual coverage)
    - service_3: Alice and Bob (dual coverage)
    - service_4: Alice, Bob, Carol (well covered)
    - service_5: Bob and Carol (dual coverage)
    - service_6: Only Carol (single point of failure)
    """
    alice_id = UUID("00000000-0000-0000-0000-000000000001")
    bob_id = UUID("00000000-0000-0000-0000-000000000002")
    carol_id = UUID("00000000-0000-0000-0000-000000000003")

    return {
        UUID("10000000-0000-0000-0000-000000000001"): [alice_id],
        UUID("10000000-0000-0000-0000-000000000002"): [alice_id, bob_id],
        UUID("10000000-0000-0000-0000-000000000003"): [alice_id, bob_id],
        UUID("10000000-0000-0000-0000-000000000004"): [alice_id, bob_id, carol_id],
        UUID("10000000-0000-0000-0000-000000000005"): [bob_id, carol_id],
        UUID("10000000-0000-0000-0000-000000000006"): [carol_id],
    }


@pytest.fixture
def mock_service_names():
    """Create mock service names."""
    return {
        UUID("10000000-0000-0000-0000-000000000001"): "Critical Surgery",
        UUID("10000000-0000-0000-0000-000000000002"): "Emergency Medicine",
        UUID("10000000-0000-0000-0000-000000000003"): "Cardiology",
        UUID("10000000-0000-0000-0000-000000000004"): "General Practice",
        UUID("10000000-0000-0000-0000-000000000005"): "Pediatrics",
        UUID("10000000-0000-0000-0000-000000000006"): "Oncology",
    }


# ============================================================================
# TestFacultyCentrality
# ============================================================================


class TestFacultyCentrality:
    """Test FacultyCentrality dataclass methods."""

    def test_composite_score_default_weights(self):
        """Test composite score calculation with default weights."""
        centrality = FacultyCentrality(
            faculty_id=uuid4(),
            faculty_name="Test Faculty",
            calculated_at=datetime.now(),
            degree_centrality=0.5,
            betweenness_centrality=0.6,
            eigenvector_centrality=0.4,
            pagerank=0.3,
            replacement_difficulty=0.7,
        )

        centrality.calculate_composite()

        # Default weights: degree=0.2, betweenness=0.3, eigenvector=0.2, pagerank=0.15, replacement=0.15
        expected = (0.5 * 0.2) + (0.6 * 0.3) + (0.4 * 0.2) + (0.3 * 0.15) + (0.7 * 0.15)
        # = 0.1 + 0.18 + 0.08 + 0.045 + 0.105 = 0.51
        assert abs(centrality.composite_score - expected) < 0.001

    def test_composite_score_custom_weights(self):
        """Test composite score calculation with custom weights."""
        centrality = FacultyCentrality(
            faculty_id=uuid4(),
            faculty_name="Test Faculty",
            calculated_at=datetime.now(),
            degree_centrality=0.5,
            betweenness_centrality=0.6,
            eigenvector_centrality=0.4,
            pagerank=0.3,
            replacement_difficulty=0.7,
        )

        custom_weights = {
            "degree": 0.3,
            "betweenness": 0.3,
            "eigenvector": 0.1,
            "pagerank": 0.1,
            "replacement": 0.2,
        }
        centrality.calculate_composite(custom_weights)

        expected = (0.5 * 0.3) + (0.6 * 0.3) + (0.4 * 0.1) + (0.3 * 0.1) + (0.7 * 0.2)
        # = 0.15 + 0.18 + 0.04 + 0.03 + 0.14 = 0.54
        assert abs(centrality.composite_score - expected) < 0.001

    def test_risk_level_low(self):
        """Test risk level classification - LOW."""
        centrality = FacultyCentrality(
            faculty_id=uuid4(),
            faculty_name="Test",
            calculated_at=datetime.now(),
            composite_score=0.1,
            unique_services=0,
        )

        assert centrality.risk_level == HubRiskLevel.LOW

    def test_risk_level_moderate(self):
        """Test risk level classification - MODERATE."""
        centrality = FacultyCentrality(
            faculty_id=uuid4(),
            faculty_name="Test",
            calculated_at=datetime.now(),
            composite_score=0.3,
            unique_services=0,
        )

        assert centrality.risk_level == HubRiskLevel.MODERATE

    def test_risk_level_high(self):
        """Test risk level classification - HIGH."""
        centrality = FacultyCentrality(
            faculty_id=uuid4(),
            faculty_name="Test",
            calculated_at=datetime.now(),
            composite_score=0.5,
            unique_services=0,
        )

        assert centrality.risk_level == HubRiskLevel.HIGH

    def test_risk_level_critical(self):
        """Test risk level classification - CRITICAL."""
        centrality = FacultyCentrality(
            faculty_id=uuid4(),
            faculty_name="Test",
            calculated_at=datetime.now(),
            composite_score=0.65,
            unique_services=0,
        )

        assert centrality.risk_level == HubRiskLevel.CRITICAL

    def test_risk_level_catastrophic_by_score(self):
        """Test risk level classification - CATASTROPHIC by score."""
        centrality = FacultyCentrality(
            faculty_id=uuid4(),
            faculty_name="Test",
            calculated_at=datetime.now(),
            composite_score=0.85,
            unique_services=0,
        )

        assert centrality.risk_level == HubRiskLevel.CATASTROPHIC

    def test_risk_level_catastrophic_by_unique_services(self):
        """Test risk level classification - CATASTROPHIC by unique services."""
        centrality = FacultyCentrality(
            faculty_id=uuid4(),
            faculty_name="Test",
            calculated_at=datetime.now(),
            composite_score=0.1,
            unique_services=3,
        )

        assert centrality.risk_level == HubRiskLevel.CATASTROPHIC

    def test_is_hub_by_score(self):
        """Test hub identification by composite score."""
        centrality = FacultyCentrality(
            faculty_id=uuid4(),
            faculty_name="Test",
            calculated_at=datetime.now(),
            composite_score=0.45,
            unique_services=0,
        )

        assert centrality.is_hub is True

    def test_is_hub_by_unique_services(self):
        """Test hub identification by unique services."""
        centrality = FacultyCentrality(
            faculty_id=uuid4(),
            faculty_name="Test",
            calculated_at=datetime.now(),
            composite_score=0.1,
            unique_services=1,
        )

        assert centrality.is_hub is True

    def test_not_hub_low_metrics(self):
        """Test non-hub with low metrics."""
        centrality = FacultyCentrality(
            faculty_id=uuid4(),
            faculty_name="Test",
            calculated_at=datetime.now(),
            composite_score=0.2,
            unique_services=0,
        )

        assert centrality.is_hub is False


# ============================================================================
# TestHubAnalyzer
# ============================================================================


class TestHubAnalyzer:
    """Test HubAnalyzer class (basic mode without NetworkX)."""

    def test_init_default_thresholds(self):
        """Test initialization with default thresholds."""
        analyzer = HubAnalyzer()

        assert analyzer.hub_threshold == 0.4
        assert analyzer.critical_hub_threshold == 0.6
        assert analyzer.centrality_cache == {}
        assert analyzer.hub_profiles == {}
        assert analyzer.protection_plans == {}

    def test_init_custom_thresholds(self):
        """Test initialization with custom thresholds."""
        analyzer = HubAnalyzer(
            hub_threshold=0.5,
            critical_hub_threshold=0.7,
            use_networkx=False,
        )

        assert analyzer.hub_threshold == 0.5
        assert analyzer.critical_hub_threshold == 0.7
        assert analyzer.use_networkx is False

    def test_calculate_centrality_basic(
        self, mock_faculty, mock_assignments, mock_services
    ):
        """Test centrality calculation using basic method (no NetworkX)."""
        analyzer = HubAnalyzer(use_networkx=False)

        results = analyzer.calculate_centrality(
            faculty=mock_faculty,
            assignments=mock_assignments,
            services=mock_services,
        )

        # Should have 4 faculty members
        assert len(results) == 4

        # Results should be sorted by composite score (descending)
        for i in range(len(results) - 1):
            assert results[i].composite_score >= results[i + 1].composite_score

        # Alice should have the highest score (most assignments, unique service)
        alice_result = next(r for r in results if r.faculty_name == "Alice")
        assert alice_result.unique_services == 1  # service_1 only Alice
        assert alice_result.services_covered == 4  # services 1,2,3,4
        assert alice_result.total_assignments == 10

        # Carol should have a unique service too
        carol_result = next(r for r in results if r.faculty_name == "Carol")
        assert carol_result.unique_services == 1  # service_6 only Carol

    def test_calculate_centrality_single_provider_high_score(
        self, mock_faculty, mock_assignments, mock_services
    ):
        """Test that single providers get high centrality scores."""
        analyzer = HubAnalyzer(use_networkx=False)

        results = analyzer.calculate_centrality(
            faculty=mock_faculty,
            assignments=mock_assignments,
            services=mock_services,
        )

        # Alice and Carol both have unique services
        alice = next(r for r in results if r.faculty_name == "Alice")
        carol = next(r for r in results if r.faculty_name == "Carol")

        # Both should be identified as hubs
        assert alice.is_hub is True
        assert carol.is_hub is True

        # Both should have high risk levels
        assert alice.risk_level in [
            HubRiskLevel.HIGH,
            HubRiskLevel.CRITICAL,
            HubRiskLevel.CATASTROPHIC,
        ]
        assert carol.risk_level in [
            HubRiskLevel.HIGH,
            HubRiskLevel.CRITICAL,
            HubRiskLevel.CATASTROPHIC,
        ]

    def test_calculate_centrality_replacement_difficulty(
        self, mock_faculty, mock_assignments, mock_services
    ):
        """Test replacement difficulty calculation."""
        analyzer = HubAnalyzer(use_networkx=False)

        results = analyzer.calculate_centrality(
            faculty=mock_faculty,
            assignments=mock_assignments,
            services=mock_services,
        )

        alice = next(r for r in results if r.faculty_name == "Alice")

        # Alice covers service_1 (1 provider), service_2 (2 providers),
        # service_3 (2 providers), service_4 (3 providers)
        # Difficulties: 1.0, 0.5, 0.5, 0.33...
        # Average: (1.0 + 0.5 + 0.5 + 0.33) / 4 ≈ 0.58
        assert alice.replacement_difficulty > 0.5
        assert alice.replacement_difficulty < 0.7

    def test_identify_hubs_from_cache(
        self, mock_faculty, mock_assignments, mock_services
    ):
        """Test hub identification from cached centrality scores."""
        analyzer = HubAnalyzer(use_networkx=False)

        # First calculate centrality
        analyzer.calculate_centrality(
            faculty=mock_faculty,
            assignments=mock_assignments,
            services=mock_services,
        )

        # Now identify hubs from cache
        hubs = analyzer.identify_hubs()

        # Should have at least 2 hubs (Alice and Carol have unique services)
        assert len(hubs) >= 2

        # All hubs should have is_hub == True
        for hub in hubs:
            assert hub.is_hub is True

    def test_identify_hubs_empty(self):
        """Test hub identification with empty cache."""
        analyzer = HubAnalyzer()

        hubs = analyzer.identify_hubs()

        assert hubs == []

    def test_get_top_hubs(self, mock_faculty, mock_assignments, mock_services):
        """Test getting top N hubs."""
        analyzer = HubAnalyzer(use_networkx=False)

        analyzer.calculate_centrality(
            faculty=mock_faculty,
            assignments=mock_assignments,
            services=mock_services,
        )

        top_3 = analyzer.get_top_hubs(n=3)

        assert len(top_3) == 3

        # Should be sorted by composite score (descending)
        for i in range(len(top_3) - 1):
            assert top_3[i].composite_score >= top_3[i + 1].composite_score


# ============================================================================
# TestHubAnalyzerWithNetworkX
# ============================================================================


@pytest.mark.skipif(not HAS_NETWORKX, reason="NetworkX not installed")
class TestHubAnalyzerWithNetworkX:
    """Test HubAnalyzer with NetworkX enabled."""

    def test_calculate_centrality_with_networkx(
        self, mock_faculty, mock_assignments, mock_services
    ):
        """Test centrality calculation using NetworkX."""
        analyzer = HubAnalyzer(use_networkx=True)

        results = analyzer.calculate_centrality(
            faculty=mock_faculty,
            assignments=mock_assignments,
            services=mock_services,
        )

        # Should have 4 faculty members
        assert len(results) == 4

        # Results should be sorted by composite score
        for i in range(len(results) - 1):
            assert results[i].composite_score >= results[i + 1].composite_score

        # All centrality metrics should be calculated
        for result in results:
            assert hasattr(result, "degree_centrality")
            assert hasattr(result, "betweenness_centrality")
            assert hasattr(result, "eigenvector_centrality")
            assert hasattr(result, "pagerank")

    def test_centrality_scores_differ_from_basic(
        self, mock_faculty, mock_assignments, mock_services
    ):
        """Test that NetworkX scores differ from basic calculation."""
        analyzer_basic = HubAnalyzer(use_networkx=False)
        analyzer_nx = HubAnalyzer(use_networkx=True)

        results_basic = analyzer_basic.calculate_centrality(
            faculty=mock_faculty,
            assignments=mock_assignments,
            services=mock_services,
        )

        results_nx = analyzer_nx.calculate_centrality(
            faculty=mock_faculty,
            assignments=mock_assignments,
            services=mock_services,
        )

        # Find Alice in both result sets
        alice_basic = next(r for r in results_basic if r.faculty_name == "Alice")
        alice_nx = next(r for r in results_nx if r.faculty_name == "Alice")

        # NetworkX should provide more sophisticated centrality measures
        # The scores should differ (at least for eigenvector centrality)
        assert alice_basic.eigenvector_centrality != alice_nx.eigenvector_centrality


# ============================================================================
# TestCrossTrainingRecommendations
# ============================================================================


class TestCrossTrainingRecommendations:
    """Test cross-training recommendation generation."""

    def test_generate_recommendations_single_provider(self, mock_services):
        """Test recommendations for single-provider services."""
        analyzer = HubAnalyzer()

        all_faculty = [
            UUID("00000000-0000-0000-0000-000000000001"),
            UUID("00000000-0000-0000-0000-000000000002"),
            UUID("00000000-0000-0000-0000-000000000003"),
            UUID("00000000-0000-0000-0000-000000000004"),
        ]

        recommendations = analyzer.generate_cross_training_recommendations(
            services=mock_services,
            all_faculty=all_faculty,
        )

        # Should have recommendations for single-provider services
        # service_1 (Alice only) and service_6 (Carol only)
        single_provider_recs = [
            r for r in recommendations if r.priority == CrossTrainingPriority.HIGH
        ]

        assert len(single_provider_recs) >= 2

        # Check that they have the right reason
        for rec in single_provider_recs:
            assert "Single point of failure" in rec.reason

    def test_generate_recommendations_dual_provider(self, mock_services):
        """Test recommendations for dual-provider services."""
        analyzer = HubAnalyzer()

        all_faculty = [
            UUID("00000000-0000-0000-0000-000000000001"),
            UUID("00000000-0000-0000-0000-000000000002"),
            UUID("00000000-0000-0000-0000-000000000003"),
        ]

        recommendations = analyzer.generate_cross_training_recommendations(
            services=mock_services,
            all_faculty=all_faculty,
        )

        # Should have recommendations for dual coverage
        dual_coverage_recs = [
            r for r in recommendations if r.priority == CrossTrainingPriority.MEDIUM
        ]

        assert len(dual_coverage_recs) >= 1

        # Check they have the right reason
        for rec in dual_coverage_recs:
            assert "Limited coverage" in rec.reason

    def test_generate_recommendations_well_covered(self, mock_services):
        """Test that well-covered services have lower priority or no recommendations."""
        analyzer = HubAnalyzer()

        all_faculty = [
            UUID("00000000-0000-0000-0000-000000000001"),
            UUID("00000000-0000-0000-0000-000000000002"),
            UUID("00000000-0000-0000-0000-000000000003"),
        ]

        recommendations = analyzer.generate_cross_training_recommendations(
            services=mock_services,
            all_faculty=all_faculty,
        )

        # service_4 has 3 providers (well covered)
        # It should not have HIGH or URGENT recommendations
        well_covered_urgent = [
            r
            for r in recommendations
            if r.priority in [CrossTrainingPriority.HIGH, CrossTrainingPriority.URGENT]
            and "10000000-0000-0000-0000-000000000004" in str(r.skill)
        ]

        assert len(well_covered_urgent) == 0

    def test_recommendations_sorted_by_priority(self, mock_services):
        """Test that recommendations are sorted by priority."""
        analyzer = HubAnalyzer()

        all_faculty = [
            UUID("00000000-0000-0000-0000-000000000001"),
            UUID("00000000-0000-0000-0000-000000000002"),
        ]

        recommendations = analyzer.generate_cross_training_recommendations(
            services=mock_services,
            all_faculty=all_faculty,
        )

        # Check that recommendations are sorted by priority
        priority_order = {
            CrossTrainingPriority.URGENT: 0,
            CrossTrainingPriority.HIGH: 1,
            CrossTrainingPriority.MEDIUM: 2,
            CrossTrainingPriority.LOW: 3,
        }

        for i in range(len(recommendations) - 1):
            curr_priority = priority_order[recommendations[i].priority]
            next_priority = priority_order[recommendations[i + 1].priority]
            assert curr_priority <= next_priority

    def test_no_recommendations_for_empty_services(self):
        """Test no recommendations for empty service list."""
        analyzer = HubAnalyzer()

        recommendations = analyzer.generate_cross_training_recommendations(
            services={},
            all_faculty=[uuid4()],
        )

        assert recommendations == []


# ============================================================================
# TestHubProtection
# ============================================================================


class TestHubProtection:
    """Test hub protection planning and profiling."""

    def test_create_hub_profile(
        self, mock_faculty, mock_assignments, mock_services, mock_service_names
    ):
        """Test creating a hub profile."""
        analyzer = HubAnalyzer(use_networkx=False)

        # Calculate centrality first
        analyzer.calculate_centrality(
            faculty=mock_faculty,
            assignments=mock_assignments,
            services=mock_services,
        )

        # Create profile for Alice (has unique service)
        alice_id = UUID("00000000-0000-0000-0000-000000000001")
        profile = analyzer.create_hub_profile(
            faculty_id=alice_id,
            services=mock_services,
            service_names=mock_service_names,
        )

        assert profile is not None
        assert profile.faculty_id == alice_id
        assert profile.faculty_name == "Alice"
        assert isinstance(profile.centrality, FacultyCentrality)

    def test_profile_unique_skills(
        self, mock_faculty, mock_assignments, mock_services, mock_service_names
    ):
        """Test that profile correctly identifies unique skills."""
        analyzer = HubAnalyzer(use_networkx=False)

        analyzer.calculate_centrality(
            faculty=mock_faculty,
            assignments=mock_assignments,
            services=mock_services,
        )

        alice_id = UUID("00000000-0000-0000-0000-000000000001")
        profile = analyzer.create_hub_profile(
            faculty_id=alice_id,
            services=mock_services,
            service_names=mock_service_names,
        )

        # Alice should have 'Critical Surgery' as unique skill
        assert "Critical Surgery" in profile.unique_skills
        assert len(profile.unique_skills) == 1

    def test_profile_risk_factors(
        self, mock_faculty, mock_assignments, mock_services, mock_service_names
    ):
        """Test that profile identifies risk factors."""
        analyzer = HubAnalyzer(use_networkx=False)

        analyzer.calculate_centrality(
            faculty=mock_faculty,
            assignments=mock_assignments,
            services=mock_services,
        )

        alice_id = UUID("00000000-0000-0000-0000-000000000001")
        profile = analyzer.create_hub_profile(
            faculty_id=alice_id,
            services=mock_services,
            service_names=mock_service_names,
        )

        # Alice has 1 unique service, so should have risk factor
        assert len(profile.risk_factors) > 0
        assert any("Single provider" in factor for factor in profile.risk_factors)

    def test_profile_mitigation_actions(
        self, mock_faculty, mock_assignments, mock_services, mock_service_names
    ):
        """Test that profile suggests mitigation actions."""
        analyzer = HubAnalyzer(use_networkx=False)

        analyzer.calculate_centrality(
            faculty=mock_faculty,
            assignments=mock_assignments,
            services=mock_services,
        )

        alice_id = UUID("00000000-0000-0000-0000-000000000001")
        profile = analyzer.create_hub_profile(
            faculty_id=alice_id,
            services=mock_services,
            service_names=mock_service_names,
        )

        # Should have mitigation actions
        assert len(profile.mitigation_actions) > 0
        assert any("Cross-train" in action for action in profile.mitigation_actions)

    def test_create_protection_plan(
        self, mock_faculty, mock_assignments, mock_services
    ):
        """Test creating a hub protection plan."""
        analyzer = HubAnalyzer(use_networkx=False)

        # Calculate centrality and create profile
        analyzer.calculate_centrality(
            faculty=mock_faculty,
            assignments=mock_assignments,
            services=mock_services,
        )

        alice_id = UUID("00000000-0000-0000-0000-000000000001")
        analyzer.create_hub_profile(
            faculty_id=alice_id,
            services=mock_services,
        )

        # Create protection plan
        today = date.today()
        plan = analyzer.create_protection_plan(
            hub_faculty_id=alice_id,
            period_start=today,
            period_end=today + timedelta(days=30),
            reason="High-risk period - flu season",
            workload_reduction=0.3,
            assign_backup=True,
        )

        assert plan is not None
        assert plan.hub_faculty_id == alice_id
        assert plan.workload_reduction == 0.3
        assert plan.backup_assigned is True
        assert plan.status == "planned"

    def test_create_protection_plan_non_hub_rejected(
        self, mock_faculty, mock_assignments, mock_services
    ):
        """Test that protection plan fails for non-hub faculty."""
        analyzer = HubAnalyzer(use_networkx=False)

        # Dave has no assignments or unique services (not a hub)
        dave_id = UUID("00000000-0000-0000-0000-000000000004")

        today = date.today()
        plan = analyzer.create_protection_plan(
            hub_faculty_id=dave_id,
            period_start=today,
            period_end=today + timedelta(days=30),
            reason="Test",
        )

        # Should return None for non-hub
        assert plan is None

    def test_activate_protection_plan(
        self, mock_faculty, mock_assignments, mock_services
    ):
        """Test activating a protection plan."""
        analyzer = HubAnalyzer(use_networkx=False)

        analyzer.calculate_centrality(
            faculty=mock_faculty,
            assignments=mock_assignments,
            services=mock_services,
        )

        alice_id = UUID("00000000-0000-0000-0000-000000000001")
        analyzer.create_hub_profile(
            faculty_id=alice_id,
            services=mock_services,
        )

        today = date.today()
        plan = analyzer.create_protection_plan(
            hub_faculty_id=alice_id,
            period_start=today,
            period_end=today + timedelta(days=30),
            reason="Test",
        )

        # Activate the plan
        analyzer.activate_protection_plan(plan.id)

        assert plan.status == "active"
        assert plan.activated_at is not None

    def test_deactivate_protection_plan(
        self, mock_faculty, mock_assignments, mock_services
    ):
        """Test deactivating a protection plan."""
        analyzer = HubAnalyzer(use_networkx=False)

        analyzer.calculate_centrality(
            faculty=mock_faculty,
            assignments=mock_assignments,
            services=mock_services,
        )

        alice_id = UUID("00000000-0000-0000-0000-000000000001")
        analyzer.create_hub_profile(
            faculty_id=alice_id,
            services=mock_services,
        )

        today = date.today()
        plan = analyzer.create_protection_plan(
            hub_faculty_id=alice_id,
            period_start=today,
            period_end=today + timedelta(days=30),
            reason="Test",
        )

        # Deactivate the plan
        analyzer.deactivate_protection_plan(plan.id)

        assert plan.status == "completed"
        assert plan.deactivated_at is not None


# ============================================================================
# TestHubDistributionReport
# ============================================================================


class TestHubDistributionReport:
    """Test hub distribution reporting."""

    def test_get_distribution_report(
        self, mock_faculty, mock_assignments, mock_services, mock_service_names
    ):
        """Test generating a distribution report."""
        analyzer = HubAnalyzer(use_networkx=False)

        analyzer.calculate_centrality(
            faculty=mock_faculty,
            assignments=mock_assignments,
            services=mock_services,
        )

        report = analyzer.get_distribution_report(
            services=mock_services,
            service_names=mock_service_names,
        )

        assert isinstance(report, HubDistributionReport)
        assert report.total_faculty == 4
        assert report.total_hubs >= 2  # At least Alice and Carol
        assert isinstance(report.hub_concentration, float)

    def test_report_counts_by_risk_level(
        self, mock_faculty, mock_assignments, mock_services, mock_service_names
    ):
        """Test that report correctly counts hubs by risk level."""
        analyzer = HubAnalyzer(use_networkx=False)

        analyzer.calculate_centrality(
            faculty=mock_faculty,
            assignments=mock_assignments,
            services=mock_services,
        )

        report = analyzer.get_distribution_report(
            services=mock_services,
            service_names=mock_service_names,
        )

        # Sum of all risk categories should equal total hubs
        total_by_risk = (
            report.catastrophic_hubs + report.critical_hubs + report.high_risk_hubs
        )

        # Note: total_hubs includes moderate and low risk hubs too
        assert total_by_risk <= report.total_hubs

    def test_report_single_point_of_failure_detection(
        self, mock_faculty, mock_assignments, mock_services, mock_service_names
    ):
        """Test single point of failure detection in report."""
        analyzer = HubAnalyzer(use_networkx=False)

        analyzer.calculate_centrality(
            faculty=mock_faculty,
            assignments=mock_assignments,
            services=mock_services,
        )

        report = analyzer.get_distribution_report(
            services=mock_services,
            service_names=mock_service_names,
        )

        # Should detect 2 single-provider services
        assert len(report.services_with_single_provider) == 2
        assert "Critical Surgery" in report.services_with_single_provider
        assert "Oncology" in report.services_with_single_provider

        # Should have at least 2 single points of failure
        assert report.single_points_of_failure >= 2

    def test_report_recommendations(
        self, mock_faculty, mock_assignments, mock_services, mock_service_names
    ):
        """Test that report includes recommendations."""
        analyzer = HubAnalyzer(use_networkx=False)

        analyzer.calculate_centrality(
            faculty=mock_faculty,
            assignments=mock_assignments,
            services=mock_services,
        )

        report = analyzer.get_distribution_report(
            services=mock_services,
            service_names=mock_service_names,
        )

        # Should have recommendations
        assert len(report.recommendations) > 0

        # Should include cross-training priorities
        assert len(report.cross_training_priorities) > 0

        # Recommendations should mention single points of failure
        assert any("single point" in rec.lower() for rec in report.recommendations)


# ============================================================================
# TestHubStatus
# ============================================================================


class TestHubStatus:
    """Test hub status tracking."""

    def test_get_hub_status(self, mock_faculty, mock_assignments, mock_services):
        """Test getting hub status summary."""
        analyzer = HubAnalyzer(use_networkx=False)

        analyzer.calculate_centrality(
            faculty=mock_faculty,
            assignments=mock_assignments,
            services=mock_services,
        )

        status = analyzer.get_hub_status()

        assert isinstance(status, dict)
        assert "last_analysis" in status
        assert "total_faculty_analyzed" in status
        assert "total_hubs" in status
        assert "hubs_by_risk" in status
        assert "active_protection_plans" in status
        assert "pending_cross_training" in status

    def test_hub_status_structure(self, mock_faculty, mock_assignments, mock_services):
        """Test hub status has correct structure and values."""
        analyzer = HubAnalyzer(use_networkx=False)

        analyzer.calculate_centrality(
            faculty=mock_faculty,
            assignments=mock_assignments,
            services=mock_services,
        )

        status = analyzer.get_hub_status()

        # Check structure
        assert status["total_faculty_analyzed"] == 4
        assert status["total_hubs"] >= 2

        # Check hubs_by_risk structure
        assert "catastrophic" in status["hubs_by_risk"]
        assert "critical" in status["hubs_by_risk"]
        assert "high" in status["hubs_by_risk"]
        assert "moderate" in status["hubs_by_risk"]

        # All risk counts should be non-negative integers
        for count in status["hubs_by_risk"].values():
            assert isinstance(count, int)
            assert count >= 0

        # Last analysis should be a valid ISO timestamp string
        if status["last_analysis"]:
            # Should be parseable as ISO format
            datetime.fromisoformat(status["last_analysis"])
