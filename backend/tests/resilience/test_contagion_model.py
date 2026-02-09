"""Tests for Burnout Contagion Model (Epidemiological Network Diffusion)."""

import sys
from datetime import datetime
from unittest.mock import MagicMock, patch
from uuid import uuid4

import networkx as nx
import pytest

# Mock ndlib before importing the module under test
mock_ep = MagicMock()
mock_mc = MagicMock()
sys.modules.setdefault("ndlib", MagicMock())
sys.modules.setdefault("ndlib.models", MagicMock())
sys.modules.setdefault("ndlib.models.epidemics", mock_ep)
sys.modules.setdefault("ndlib.models.ModelConfig", mock_mc)

from app.resilience.contagion_model import (  # noqa: E402
    BurnoutContagionModel,
    BurnoutSnapshot,
    BurnoutState,
    ContagionRisk,
    ContagionReport,
    InterventionType,
    NetworkIntervention,
    SuperspreaderProfile,
)


# ==================== BurnoutState enum ====================


class TestBurnoutState:
    def test_values(self):
        assert BurnoutState.SUSCEPTIBLE == "susceptible"
        assert BurnoutState.INFECTED == "infected"
        assert BurnoutState.RECOVERED == "recovered"

    def test_is_str_enum(self):
        assert isinstance(BurnoutState.SUSCEPTIBLE, str)

    def test_count(self):
        assert len(BurnoutState) == 3


# ==================== InterventionType enum ====================


class TestInterventionType:
    def test_values(self):
        assert InterventionType.EDGE_REMOVAL == "edge_removal"
        assert InterventionType.BUFFER_INSERTION == "buffer_insertion"
        assert InterventionType.WORKLOAD_REDUCTION == "workload_reduction"
        assert InterventionType.QUARANTINE == "quarantine"
        assert InterventionType.PEER_SUPPORT == "peer_support"

    def test_count(self):
        assert len(InterventionType) == 5


# ==================== ContagionRisk enum ====================


class TestContagionRisk:
    def test_values(self):
        assert ContagionRisk.LOW == "low"
        assert ContagionRisk.MODERATE == "moderate"
        assert ContagionRisk.HIGH == "high"
        assert ContagionRisk.CRITICAL == "critical"

    def test_count(self):
        assert len(ContagionRisk) == 4


# ==================== BurnoutSnapshot dataclass ====================


class TestBurnoutSnapshot:
    def test_required_fields(self):
        snap = BurnoutSnapshot(
            iteration=5,
            timestamp=datetime.now(),
            susceptible_count=8,
            infected_count=2,
            infection_rate=0.2,
        )
        assert snap.iteration == 5
        assert snap.susceptible_count == 8
        assert snap.infected_count == 2
        assert snap.infection_rate == 0.2

    def test_defaults(self):
        snap = BurnoutSnapshot(
            iteration=0,
            timestamp=datetime.now(),
            susceptible_count=10,
            infected_count=0,
            infection_rate=0.0,
        )
        assert snap.newly_infected == []
        assert snap.newly_recovered == []
        assert snap.mean_burnout_score == 0.0
        assert snap.max_burnout_score == 0.0
        assert snap.burnout_std_dev == 0.0

    def test_with_burnout_metrics(self):
        snap = BurnoutSnapshot(
            iteration=10,
            timestamp=datetime.now(),
            susceptible_count=5,
            infected_count=5,
            infection_rate=0.5,
            mean_burnout_score=0.55,
            max_burnout_score=0.9,
            burnout_std_dev=0.15,
            newly_infected=["A", "B"],
            newly_recovered=["C"],
        )
        assert snap.mean_burnout_score == 0.55
        assert snap.max_burnout_score == 0.9
        assert len(snap.newly_infected) == 2
        assert len(snap.newly_recovered) == 1


# ==================== SuperspreaderProfile dataclass ====================


class TestSuperspreaderProfile:
    def test_all_fields(self):
        profile = SuperspreaderProfile(
            provider_id="P1",
            provider_name="Dr. Smith",
            burnout_score=0.8,
            burnout_trend="increasing",
            degree_centrality=0.6,
            betweenness_centrality=0.5,
            eigenvector_centrality=0.4,
            composite_centrality=0.5,
            superspreader_score=0.4,
            risk_level="high",
            direct_contacts=5,
            estimated_cascade_size=10,
        )
        assert profile.provider_id == "P1"
        assert profile.burnout_score == 0.8
        assert profile.risk_level == "high"
        assert profile.direct_contacts == 5


# ==================== NetworkIntervention dataclass ====================


class TestNetworkIntervention:
    def test_required_fields(self):
        uid = uuid4()
        intervention = NetworkIntervention(
            id=uid,
            intervention_type=InterventionType.WORKLOAD_REDUCTION,
            priority=1,
            reason="Critical superspreader",
            target_providers=["P1"],
            estimated_infection_reduction=0.15,
            estimated_cost=20.0,
        )
        assert intervention.id == uid
        assert intervention.intervention_type == InterventionType.WORKLOAD_REDUCTION
        assert intervention.priority == 1
        assert len(intervention.target_providers) == 1

    def test_defaults(self):
        intervention = NetworkIntervention(
            id=uuid4(),
            intervention_type=InterventionType.EDGE_REMOVAL,
            priority=2,
            reason="High burnout pair",
            target_providers=["P1", "P2"],
            estimated_infection_reduction=0.08,
            estimated_cost=10.0,
        )
        assert intervention.affected_edges == []
        assert intervention.status == "recommended"
        assert intervention.created_at is not None


# ==================== ContagionReport dataclass ====================


class TestContagionReport:
    def test_required_fields(self):
        report = ContagionReport(
            generated_at=datetime.now(),
            network_size=20,
            current_susceptible=15,
            current_infected=5,
            current_infection_rate=0.25,
            contagion_risk=ContagionRisk.HIGH,
            simulation_iterations=50,
            final_infection_rate=0.3,
            peak_infection_rate=0.4,
            peak_iteration=25,
            superspreaders=[],
            total_superspreaders=0,
            recommended_interventions=[],
        )
        assert report.network_size == 20
        assert report.contagion_risk == ContagionRisk.HIGH
        assert report.final_infection_rate == 0.3

    def test_defaults(self):
        report = ContagionReport(
            generated_at=datetime.now(),
            network_size=10,
            current_susceptible=8,
            current_infected=2,
            current_infection_rate=0.2,
            contagion_risk=ContagionRisk.MODERATE,
            simulation_iterations=50,
            final_infection_rate=0.2,
            peak_infection_rate=0.25,
            peak_iteration=15,
            superspreaders=[],
            total_superspreaders=0,
            recommended_interventions=[],
        )
        assert report.snapshots == []
        assert report.warnings == []


# ==================== BurnoutContagionModel ====================


def _make_graph(n=5):
    """Create a simple test graph with n nodes."""
    g = nx.complete_graph(n)
    # Relabel to string IDs
    mapping = {i: f"P{i}" for i in range(n)}
    return nx.relabel_nodes(g, mapping)


class TestBurnoutContagionModelInit:
    @patch("app.resilience.contagion_model.HAS_NDLIB", True)
    def test_init(self):
        g = _make_graph()
        model = BurnoutContagionModel(g)
        assert model.social_graph is g
        assert model.model is None
        assert model.config is None
        assert model.infection_rate == 0.05
        assert model.recovery_rate == 0.01
        assert model.snapshots == []
        assert model.current_iteration == 0

    @patch("app.resilience.contagion_model.HAS_NDLIB", False)
    def test_init_without_ndlib_raises(self):
        g = _make_graph()
        with pytest.raises(ImportError, match="ndlib is required"):
            BurnoutContagionModel(g)


class TestConfigure:
    @patch("app.resilience.contagion_model.HAS_NDLIB", True)
    def test_configure_sets_rates(self):
        g = _make_graph()
        model = BurnoutContagionModel(g)
        model.configure(infection_rate=0.1, recovery_rate=0.02)
        assert model.infection_rate == 0.1
        assert model.recovery_rate == 0.02
        assert model.model is not None
        assert model.config is not None

    @patch("app.resilience.contagion_model.HAS_NDLIB", True)
    def test_configure_invalid_infection_rate(self):
        g = _make_graph()
        model = BurnoutContagionModel(g)
        with pytest.raises(ValueError, match="infection_rate"):
            model.configure(infection_rate=1.5)

    @patch("app.resilience.contagion_model.HAS_NDLIB", True)
    def test_configure_invalid_recovery_rate(self):
        g = _make_graph()
        model = BurnoutContagionModel(g)
        with pytest.raises(ValueError, match="recovery_rate"):
            model.configure(recovery_rate=-0.1)


class TestSetInitialBurnout:
    @patch("app.resilience.contagion_model.HAS_NDLIB", True)
    def test_requires_configure_first(self):
        g = _make_graph()
        model = BurnoutContagionModel(g)
        with pytest.raises(RuntimeError, match="Must call configure"):
            model.set_initial_burnout(["P0"], {"P0": 0.8})

    @patch("app.resilience.contagion_model.HAS_NDLIB", True)
    def test_sets_burnout_scores(self):
        g = _make_graph()
        model = BurnoutContagionModel(g)
        model.configure()
        scores = {"P0": 0.8, "P1": 0.3, "P2": 0.6}
        model.set_initial_burnout(["P0", "P1", "P2"], scores)
        assert model.burnout_scores == scores

    @patch("app.resilience.contagion_model.HAS_NDLIB", True)
    def test_copies_scores(self):
        g = _make_graph()
        model = BurnoutContagionModel(g)
        model.configure()
        scores = {"P0": 0.8}
        model.set_initial_burnout(["P0"], scores)
        scores["P0"] = 0.1  # Mutate original
        assert model.burnout_scores["P0"] == 0.8  # Model copy unchanged


class TestSimulate:
    @patch("app.resilience.contagion_model.HAS_NDLIB", True)
    def test_requires_configure(self):
        g = _make_graph()
        model = BurnoutContagionModel(g)
        with pytest.raises(RuntimeError, match="Must call configure"):
            model.simulate()

    @patch("app.resilience.contagion_model.HAS_NDLIB", True)
    def test_simulate_returns_results(self):
        g = _make_graph()
        model = BurnoutContagionModel(g)
        model.configure()
        # Mock iteration results
        model.model.iteration = MagicMock(
            return_value={
                "status": {"P0": 0, "P1": 1, "P2": 0, "P3": 0, "P4": 0},
                "node_count": {0: 4, 1: 1},
            }
        )
        results = model.simulate(iterations=3)
        assert len(results) == 3
        assert len(model.snapshots) == 3
        assert model.current_iteration == 2

    @patch("app.resilience.contagion_model.HAS_NDLIB", True)
    def test_simulate_tracks_infection_rate(self):
        g = _make_graph()
        model = BurnoutContagionModel(g)
        model.configure()
        model.model.iteration = MagicMock(
            return_value={
                "status": {"P0": 1, "P1": 1, "P2": 0, "P3": 0, "P4": 0},
                "node_count": {0: 3, 1: 2},
            }
        )
        model.simulate(iterations=5)
        for snap in model.snapshots:
            assert abs(snap.infection_rate - 0.4) < 0.001  # 2/5

    @patch("app.resilience.contagion_model.HAS_NDLIB", True)
    def test_simulate_clears_previous_snapshots(self):
        g = _make_graph()
        model = BurnoutContagionModel(g)
        model.configure()
        model.model.iteration = MagicMock(
            return_value={
                "status": {"P0": 0},
                "node_count": {0: 5, 1: 0},
            }
        )
        model.simulate(iterations=2)
        assert len(model.snapshots) == 2
        model.simulate(iterations=3)
        assert len(model.snapshots) == 3  # Not 5


class TestIdentifySuperspreaders:
    @patch("app.resilience.contagion_model.HAS_NDLIB", True)
    def test_no_scores_returns_empty(self):
        g = _make_graph()
        model = BurnoutContagionModel(g)
        result = model.identify_superspreaders()
        assert result == []

    @patch("app.resilience.contagion_model.HAS_NDLIB", True)
    def test_high_burnout_identified(self):
        g = _make_graph()
        model = BurnoutContagionModel(g)
        # All nodes high burnout
        model.burnout_scores = {f"P{i}": 0.9 for i in range(5)}
        result = model.identify_superspreaders()
        # All should be identified (burnout >= 0.6)
        assert len(result) == 5

    @patch("app.resilience.contagion_model.HAS_NDLIB", True)
    def test_low_burnout_not_identified(self):
        g = _make_graph()
        model = BurnoutContagionModel(g)
        model.burnout_scores = {f"P{i}": 0.1 for i in range(5)}
        result = model.identify_superspreaders()
        assert len(result) == 0

    @patch("app.resilience.contagion_model.HAS_NDLIB", True)
    def test_moderate_burnout_high_centrality(self):
        # Star graph: center has high centrality
        g = nx.star_graph(4)
        mapping = {i: f"P{i}" for i in range(5)}
        g = nx.relabel_nodes(g, mapping)
        model = BurnoutContagionModel(g)
        # P0 is center with moderate burnout, others low
        model.burnout_scores = {"P0": 0.55, "P1": 0.1, "P2": 0.1, "P3": 0.1, "P4": 0.1}
        result = model.identify_superspreaders()
        # P0 has moderate burnout AND high centrality
        assert "P0" in result

    @patch("app.resilience.contagion_model.HAS_NDLIB", True)
    def test_custom_weights(self):
        g = _make_graph()
        model = BurnoutContagionModel(g)
        model.burnout_scores = {f"P{i}": 0.7 for i in range(5)}
        result = model.identify_superspreaders(
            centrality_weights={"degree": 0.5, "betweenness": 0.3, "eigenvector": 0.2}
        )
        assert len(result) == 5  # All high burnout


class TestGetSuperspreaderProfiles:
    @patch("app.resilience.contagion_model.HAS_NDLIB", True)
    def test_returns_profiles(self):
        g = _make_graph(3)
        model = BurnoutContagionModel(g)
        model.burnout_scores = {"P0": 0.9, "P1": 0.8, "P2": 0.1}
        profiles = model.get_superspreader_profiles()
        assert len(profiles) >= 2  # P0 and P1 at least
        assert all(isinstance(p, SuperspreaderProfile) for p in profiles)

    @patch("app.resilience.contagion_model.HAS_NDLIB", True)
    def test_uses_provider_names(self):
        g = _make_graph(3)
        model = BurnoutContagionModel(g)
        model.burnout_scores = {"P0": 0.9, "P1": 0.1, "P2": 0.1}
        names = {"P0": "Dr. Smith"}
        profiles = model.get_superspreader_profiles(provider_names=names)
        assert any(p.provider_name == "Dr. Smith" for p in profiles)

    @patch("app.resilience.contagion_model.HAS_NDLIB", True)
    def test_sorted_by_score(self):
        g = _make_graph(3)
        model = BurnoutContagionModel(g)
        model.burnout_scores = {"P0": 0.7, "P1": 0.9, "P2": 0.8}
        profiles = model.get_superspreader_profiles()
        if len(profiles) >= 2:
            scores = [p.superspreader_score for p in profiles]
            assert scores == sorted(scores, reverse=True)


class TestRecommendInterventions:
    @patch("app.resilience.contagion_model.HAS_NDLIB", True)
    def test_no_superspreaders_returns_empty(self):
        g = _make_graph()
        model = BurnoutContagionModel(g)
        model.burnout_scores = {f"P{i}": 0.1 for i in range(5)}
        result = model.recommend_interventions()
        assert result == []

    @patch("app.resilience.contagion_model.HAS_NDLIB", True)
    def test_workload_reduction_for_critical(self):
        g = _make_graph()
        model = BurnoutContagionModel(g)
        model.burnout_scores = {f"P{i}": 0.8 for i in range(5)}
        result = model.recommend_interventions()
        workload_interventions = [
            i
            for i in result
            if i.intervention_type == InterventionType.WORKLOAD_REDUCTION
        ]
        assert len(workload_interventions) > 0

    @patch("app.resilience.contagion_model.HAS_NDLIB", True)
    def test_quarantine_for_extreme_burnout(self):
        g = _make_graph()
        model = BurnoutContagionModel(g)
        model.burnout_scores = {"P0": 0.9, "P1": 0.1, "P2": 0.1, "P3": 0.1, "P4": 0.1}
        result = model.recommend_interventions()
        quarantine_interventions = [
            i for i in result if i.intervention_type == InterventionType.QUARANTINE
        ]
        assert len(quarantine_interventions) > 0

    @patch("app.resilience.contagion_model.HAS_NDLIB", True)
    def test_edge_removal_for_high_burnout_pairs(self):
        g = _make_graph()
        model = BurnoutContagionModel(g)
        # All high burnout -> many high-burnout edges
        model.burnout_scores = {f"P{i}": 0.75 for i in range(5)}
        result = model.recommend_interventions()
        edge_interventions = [
            i for i in result if i.intervention_type == InterventionType.EDGE_REMOVAL
        ]
        assert len(edge_interventions) > 0

    @patch("app.resilience.contagion_model.HAS_NDLIB", True)
    def test_max_interventions(self):
        g = _make_graph()
        model = BurnoutContagionModel(g)
        model.burnout_scores = {f"P{i}": 0.9 for i in range(5)}
        result = model.recommend_interventions(max_interventions=2)
        assert len(result) <= 2


class TestGenerateReport:
    @patch("app.resilience.contagion_model.HAS_NDLIB", True)
    def test_requires_simulation(self):
        g = _make_graph()
        model = BurnoutContagionModel(g)
        with pytest.raises(RuntimeError, match="Must run simulate"):
            model.generate_report()

    @patch("app.resilience.contagion_model.HAS_NDLIB", True)
    def test_report_structure(self):
        g = _make_graph()
        model = BurnoutContagionModel(g)
        model.burnout_scores = {f"P{i}": 0.3 for i in range(5)}
        # Populate snapshots manually (simulate was mocked)
        model.snapshots = [
            BurnoutSnapshot(
                iteration=i,
                timestamp=datetime.now(),
                susceptible_count=4,
                infected_count=1,
                infection_rate=0.2,
            )
            for i in range(10)
        ]
        report = model.generate_report()
        assert isinstance(report, ContagionReport)
        assert report.network_size == 5
        assert report.simulation_iterations == 10

    @patch("app.resilience.contagion_model.HAS_NDLIB", True)
    def test_risk_classification_low(self):
        g = _make_graph()
        model = BurnoutContagionModel(g)
        model.burnout_scores = {f"P{i}": 0.1 for i in range(5)}
        model.snapshots = [
            BurnoutSnapshot(
                iteration=0,
                timestamp=datetime.now(),
                susceptible_count=9,
                infected_count=1,
                infection_rate=0.05,
            )
        ]
        report = model.generate_report()
        assert report.contagion_risk == ContagionRisk.LOW

    @patch("app.resilience.contagion_model.HAS_NDLIB", True)
    def test_risk_classification_critical(self):
        g = _make_graph()
        model = BurnoutContagionModel(g)
        model.burnout_scores = {f"P{i}": 0.9 for i in range(5)}
        model.snapshots = [
            BurnoutSnapshot(
                iteration=0,
                timestamp=datetime.now(),
                susceptible_count=2,
                infected_count=8,
                infection_rate=0.8,
            )
        ]
        report = model.generate_report()
        assert report.contagion_risk == ContagionRisk.CRITICAL


class TestCalculateCentrality:
    @patch("app.resilience.contagion_model.HAS_NDLIB", True)
    def test_caches_centrality(self):
        g = _make_graph()
        model = BurnoutContagionModel(g)
        model._calculate_centrality()
        assert len(model._centrality_cache) == 5
        for node_id, cent in model._centrality_cache.items():
            assert "degree" in cent
            assert "betweenness" in cent
            assert "eigenvector" in cent

    @patch("app.resilience.contagion_model.HAS_NDLIB", True)
    def test_complete_graph_centrality(self):
        g = _make_graph(4)
        model = BurnoutContagionModel(g)
        model._calculate_centrality()
        # In a complete graph, all nodes have equal centrality
        centralities = list(model._centrality_cache.values())
        for c in centralities:
            assert abs(c["degree"] - centralities[0]["degree"]) < 0.001


class TestGetInfectionTrajectory:
    @patch("app.resilience.contagion_model.HAS_NDLIB", True)
    def test_empty_no_simulation(self):
        g = _make_graph()
        model = BurnoutContagionModel(g)
        assert model.get_infection_trajectory() == []

    @patch("app.resilience.contagion_model.HAS_NDLIB", True)
    def test_returns_tuples(self):
        g = _make_graph()
        model = BurnoutContagionModel(g)
        model.snapshots = [
            BurnoutSnapshot(
                iteration=i,
                timestamp=datetime.now(),
                susceptible_count=5 - i,
                infected_count=i,
                infection_rate=i / 5,
            )
            for i in range(3)
        ]
        trajectory = model.get_infection_trajectory()
        assert len(trajectory) == 3
        assert trajectory[0] == (0, 0.0)
        assert trajectory[1] == (1, 0.2)
        assert trajectory[2] == (2, 0.4)


class TestGetCurrentState:
    @patch("app.resilience.contagion_model.HAS_NDLIB", True)
    def test_no_simulation(self):
        g = _make_graph()
        model = BurnoutContagionModel(g)
        state = model.get_current_state()
        assert "error" in state

    @patch("app.resilience.contagion_model.HAS_NDLIB", True)
    def test_after_simulation(self):
        g = _make_graph()
        model = BurnoutContagionModel(g)
        model.snapshots = [
            BurnoutSnapshot(
                iteration=0,
                timestamp=datetime.now(),
                susceptible_count=4,
                infected_count=1,
                infection_rate=0.2,
                mean_burnout_score=0.3,
                max_burnout_score=0.8,
            )
        ]
        state = model.get_current_state()
        assert state["iteration"] == 0
        assert state["susceptible"] == 4
        assert state["infected"] == 1
        assert state["infection_rate"] == 0.2
        assert state["mean_burnout"] == 0.3
        assert state["max_burnout"] == 0.8
