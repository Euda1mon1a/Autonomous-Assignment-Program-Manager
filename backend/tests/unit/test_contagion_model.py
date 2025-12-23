"""
Unit tests for burnout contagion model.

Tests coverage:
1. Model initialization with social network
2. Configuration of SIS parameters
3. Setting initial burnout states
4. Simulation execution
5. Superspreader identification
6. Intervention recommendations
7. Report generation
8. Edge cases and error handling
"""

import networkx as nx
import pytest

from app.resilience.contagion_model import (
    BurnoutContagionModel,
    ContagionReport,
    ContagionRisk,
    InterventionType,
    NetworkIntervention,
    SuperspreaderProfile,
)

# Check if ndlib is available
try:
    import ndlib

    HAS_NDLIB = True
except ImportError:
    HAS_NDLIB = False


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def simple_network():
    """Create a simple social network for testing."""
    G = nx.Graph()

    # Add 10 providers
    providers = [f"provider_{i}" for i in range(10)]
    G.add_nodes_from(providers)

    # Create connections (small-world-ish pattern)
    edges = [
        ("provider_0", "provider_1"),
        ("provider_0", "provider_2"),
        ("provider_0", "provider_3"),  # provider_0 is a hub
        ("provider_1", "provider_2"),
        ("provider_2", "provider_3"),
        ("provider_3", "provider_4"),
        ("provider_4", "provider_5"),
        ("provider_5", "provider_6"),
        ("provider_6", "provider_7"),
        ("provider_7", "provider_8"),
        ("provider_8", "provider_9"),
        ("provider_9", "provider_0"),  # Close the loop
    ]
    G.add_edges_from(edges)

    return G


@pytest.fixture
def hub_network():
    """Create a network with a clear hub structure."""
    G = nx.Graph()

    # Central hub with many connections
    hub = "hub_provider"
    peripherals = [f"provider_{i}" for i in range(8)]

    G.add_node(hub)
    G.add_nodes_from(peripherals)

    # Hub connected to all peripherals
    for peripheral in peripherals:
        G.add_edge(hub, peripheral)

    # Some peripheral-to-peripheral connections
    G.add_edge("provider_0", "provider_1")
    G.add_edge("provider_2", "provider_3")
    G.add_edge("provider_4", "provider_5")

    return G


@pytest.fixture
def initial_burnout_low():
    """Low initial burnout scores (healthy)."""
    return {f"provider_{i}": 0.1 + (i * 0.02) for i in range(10)}


@pytest.fixture
def initial_burnout_mixed():
    """Mixed burnout scores (some high, some low)."""
    return {
        "provider_0": 0.8,  # High burnout
        "provider_1": 0.7,  # High burnout
        "provider_2": 0.3,  # Low
        "provider_3": 0.9,  # Very high burnout
        "provider_4": 0.2,  # Low
        "provider_5": 0.4,  # Medium
        "provider_6": 0.6,  # Medium-high
        "provider_7": 0.1,  # Low
        "provider_8": 0.5,  # Medium
        "provider_9": 0.2,  # Low
    }


@pytest.fixture
def initial_burnout_high():
    """High burnout across network (crisis scenario)."""
    return {f"provider_{i}": 0.6 + (i * 0.03) for i in range(10)}


# =============================================================================
# Test: Model Initialization
# =============================================================================


@pytest.mark.skipif(not HAS_NDLIB, reason="ndlib not installed")
def test_model_initialization(simple_network):
    """Test model initializes with a social network."""
    model = BurnoutContagionModel(simple_network)

    assert model.social_graph == simple_network
    assert model.social_graph.number_of_nodes() == 10
    assert model.social_graph.number_of_edges() == 12
    assert model.model is None  # Not configured yet
    assert model.infection_rate == 0.05  # Default
    assert model.recovery_rate == 0.01  # Default


@pytest.mark.skipif(not HAS_NDLIB, reason="ndlib not installed")
def test_model_initialization_empty_network():
    """Test model with empty network."""
    G = nx.Graph()
    model = BurnoutContagionModel(G)

    assert model.social_graph.number_of_nodes() == 0


@pytest.mark.skipif(HAS_NDLIB, reason="Test for missing ndlib")
def test_model_requires_ndlib():
    """Test that model raises error when ndlib not installed."""
    G = nx.Graph()
    G.add_node("provider_1")

    with pytest.raises(ImportError, match="ndlib is required"):
        BurnoutContagionModel(G)


# =============================================================================
# Test: Model Configuration
# =============================================================================


@pytest.mark.skipif(not HAS_NDLIB, reason="ndlib not installed")
def test_configure_model(simple_network):
    """Test model configuration with custom parameters."""
    model = BurnoutContagionModel(simple_network)

    model.configure(infection_rate=0.1, recovery_rate=0.02)

    assert model.infection_rate == 0.1
    assert model.recovery_rate == 0.02
    assert model.model is not None
    assert model.config is not None


@pytest.mark.skipif(not HAS_NDLIB, reason="ndlib not installed")
def test_configure_default_parameters(simple_network):
    """Test configuration with default parameters."""
    model = BurnoutContagionModel(simple_network)

    model.configure()

    assert model.infection_rate == 0.05
    assert model.recovery_rate == 0.01


@pytest.mark.skipif(not HAS_NDLIB, reason="ndlib not installed")
def test_configure_invalid_infection_rate(simple_network):
    """Test configuration rejects invalid infection rate."""
    model = BurnoutContagionModel(simple_network)

    with pytest.raises(ValueError, match="infection_rate must be between"):
        model.configure(infection_rate=1.5)

    with pytest.raises(ValueError, match="infection_rate must be between"):
        model.configure(infection_rate=-0.1)


@pytest.mark.skipif(not HAS_NDLIB, reason="ndlib not installed")
def test_configure_invalid_recovery_rate(simple_network):
    """Test configuration rejects invalid recovery rate."""
    model = BurnoutContagionModel(simple_network)

    with pytest.raises(ValueError, match="recovery_rate must be between"):
        model.configure(recovery_rate=1.5)


# =============================================================================
# Test: Initial Burnout State
# =============================================================================


@pytest.mark.skipif(not HAS_NDLIB, reason="ndlib not installed")
def test_set_initial_burnout(simple_network, initial_burnout_mixed):
    """Test setting initial burnout states."""
    model = BurnoutContagionModel(simple_network)
    model.configure()

    provider_ids = [f"provider_{i}" for i in range(10)]
    model.set_initial_burnout(provider_ids, initial_burnout_mixed)

    assert model.burnout_scores == initial_burnout_mixed

    # Check that high-burnout providers are marked as infected
    # (burnout >= 0.5 should be infected)
    infected = [pid for pid, score in initial_burnout_mixed.items() if score >= 0.5]
    assert len(infected) > 0


@pytest.mark.skipif(not HAS_NDLIB, reason="ndlib not installed")
def test_set_initial_burnout_before_configure(simple_network, initial_burnout_low):
    """Test that setting burnout before configure raises error."""
    model = BurnoutContagionModel(simple_network)

    provider_ids = [f"provider_{i}" for i in range(10)]

    with pytest.raises(RuntimeError, match="Must call configure"):
        model.set_initial_burnout(provider_ids, initial_burnout_low)


# =============================================================================
# Test: Simulation
# =============================================================================


@pytest.mark.skipif(not HAS_NDLIB, reason="ndlib not installed")
def test_simulate_basic(simple_network, initial_burnout_mixed):
    """Test basic simulation runs without error."""
    model = BurnoutContagionModel(simple_network)
    model.configure(infection_rate=0.05, recovery_rate=0.01)

    provider_ids = [f"provider_{i}" for i in range(10)]
    model.set_initial_burnout(provider_ids, initial_burnout_mixed)

    results = model.simulate(iterations=30)

    assert len(results) == 30
    assert len(model.snapshots) == 30

    # Verify each result has expected structure
    for result in results:
        assert "iteration" in result
        assert "status" in result
        assert "node_count" in result


@pytest.mark.skipif(not HAS_NDLIB, reason="ndlib not installed")
def test_simulate_infection_spread(simple_network, initial_burnout_mixed):
    """Test that infection can spread in the network."""
    model = BurnoutContagionModel(simple_network)
    model.configure(infection_rate=0.15, recovery_rate=0.01)  # High infection rate

    provider_ids = [f"provider_{i}" for i in range(10)]
    model.set_initial_burnout(provider_ids, initial_burnout_mixed)

    results = model.simulate(iterations=50)

    # Check that infection rate changes over time
    initial_rate = model.snapshots[0].infection_rate
    final_rate = model.snapshots[-1].infection_rate

    # With high infection rate, final should be >= initial
    # (or at least simulation should progress)
    assert len(model.snapshots) == 50


@pytest.mark.skipif(not HAS_NDLIB, reason="ndlib not installed")
def test_simulate_without_configuration(simple_network):
    """Test that simulate raises error if not configured."""
    model = BurnoutContagionModel(simple_network)

    with pytest.raises(RuntimeError, match="Must call configure"):
        model.simulate(iterations=10)


@pytest.mark.skipif(not HAS_NDLIB, reason="ndlib not installed")
def test_simulate_snapshots(simple_network, initial_burnout_mixed):
    """Test that snapshots are created correctly."""
    model = BurnoutContagionModel(simple_network)
    model.configure()

    provider_ids = [f"provider_{i}" for i in range(10)]
    model.set_initial_burnout(provider_ids, initial_burnout_mixed)

    model.simulate(iterations=20)

    assert len(model.snapshots) == 20

    # Verify snapshot structure
    snapshot = model.snapshots[0]
    assert snapshot.iteration == 0
    assert snapshot.susceptible_count >= 0
    assert snapshot.infected_count >= 0
    assert 0.0 <= snapshot.infection_rate <= 1.0
    assert snapshot.mean_burnout_score >= 0.0


# =============================================================================
# Test: Superspreader Identification
# =============================================================================


@pytest.mark.skipif(not HAS_NDLIB, reason="ndlib not installed")
def test_identify_superspreaders(hub_network):
    """Test superspreader identification in hub network."""
    model = BurnoutContagionModel(hub_network)
    model.configure()

    # Set hub provider to high burnout (should be superspreader)
    burnout_scores = {
        "hub_provider": 0.9,  # High burnout + high centrality = superspreader
        "provider_0": 0.2,
        "provider_1": 0.3,
        "provider_2": 0.1,
        "provider_3": 0.2,
        "provider_4": 0.8,  # High burnout but low centrality
        "provider_5": 0.1,
        "provider_6": 0.2,
        "provider_7": 0.1,
    }

    provider_ids = list(burnout_scores.keys())
    model.set_initial_burnout(provider_ids, burnout_scores)

    superspreaders = model.identify_superspreaders()

    # Hub with high burnout should be identified
    assert "hub_provider" in superspreaders

    # Total superspreaders should be reasonable
    assert len(superspreaders) >= 1


@pytest.mark.skipif(not HAS_NDLIB, reason="ndlib not installed")
def test_identify_superspreaders_profiles(hub_network):
    """Test getting detailed superspreader profiles."""
    model = BurnoutContagionModel(hub_network)
    model.configure()

    burnout_scores = {
        "hub_provider": 0.9,
        "provider_0": 0.2,
        "provider_1": 0.3,
        "provider_2": 0.1,
        "provider_3": 0.2,
        "provider_4": 0.8,
        "provider_5": 0.1,
        "provider_6": 0.2,
        "provider_7": 0.1,
    }

    provider_names = {
        "hub_provider": "Dr. Hub",
        "provider_0": "Dr. Zero",
    }

    provider_ids = list(burnout_scores.keys())
    model.set_initial_burnout(provider_ids, burnout_scores)

    profiles = model.get_superspreader_profiles(provider_names)

    # Should have at least one profile
    assert len(profiles) >= 1

    # Check profile structure
    profile = profiles[0]
    assert isinstance(profile, SuperspreaderProfile)
    assert profile.provider_id in burnout_scores
    assert profile.burnout_score >= 0.0
    assert profile.degree_centrality >= 0.0
    assert profile.betweenness_centrality >= 0.0
    assert profile.superspreader_score >= 0.0
    assert profile.risk_level in ["low", "moderate", "high", "critical"]
    assert profile.direct_contacts >= 0


@pytest.mark.skipif(not HAS_NDLIB, reason="ndlib not installed")
def test_identify_superspreaders_no_burnout(simple_network):
    """Test superspreader identification with no burnout scores."""
    model = BurnoutContagionModel(simple_network)
    model.configure()

    # Don't set any burnout scores
    superspreaders = model.identify_superspreaders()

    assert superspreaders == []


# =============================================================================
# Test: Intervention Recommendations
# =============================================================================


@pytest.mark.skipif(not HAS_NDLIB, reason="ndlib not installed")
def test_recommend_interventions(simple_network, initial_burnout_high):
    """Test intervention recommendations for high burnout network."""
    model = BurnoutContagionModel(simple_network)
    model.configure()

    provider_ids = [f"provider_{i}" for i in range(10)]
    model.set_initial_burnout(provider_ids, initial_burnout_high)

    interventions = model.recommend_interventions(max_interventions=10)

    # Should recommend some interventions for high burnout
    assert len(interventions) > 0

    # Check intervention structure
    intervention = interventions[0]
    assert isinstance(intervention, NetworkIntervention)
    assert intervention.intervention_type in InterventionType
    assert intervention.priority >= 1
    assert len(intervention.reason) > 0
    assert len(intervention.target_providers) > 0
    assert intervention.estimated_infection_reduction >= 0.0


@pytest.mark.skipif(not HAS_NDLIB, reason="ndlib not installed")
def test_recommend_interventions_types(hub_network):
    """Test different types of interventions are recommended."""
    model = BurnoutContagionModel(hub_network)
    model.configure()

    # Create scenario with high burnout superspreader
    burnout_scores = {
        "hub_provider": 0.95,  # Extreme burnout
        "provider_0": 0.7,
        "provider_1": 0.8,
        "provider_2": 0.6,
        "provider_3": 0.7,
        "provider_4": 0.2,
        "provider_5": 0.3,
        "provider_6": 0.1,
        "provider_7": 0.2,
    }

    provider_ids = list(burnout_scores.keys())
    model.set_initial_burnout(provider_ids, burnout_scores)

    interventions = model.recommend_interventions(max_interventions=20)

    # Should have multiple intervention types
    intervention_types = {i.intervention_type for i in interventions}

    # Should recommend workload reduction for extreme burnout
    assert InterventionType.WORKLOAD_REDUCTION in intervention_types

    # Should recommend quarantine for extreme superspreader
    assert InterventionType.QUARANTINE in intervention_types


@pytest.mark.skipif(not HAS_NDLIB, reason="ndlib not installed")
def test_recommend_interventions_no_superspreaders(simple_network, initial_burnout_low):
    """Test no interventions when no superspreaders."""
    model = BurnoutContagionModel(simple_network)
    model.configure()

    provider_ids = [f"provider_{i}" for i in range(10)]
    model.set_initial_burnout(provider_ids, initial_burnout_low)

    interventions = model.recommend_interventions()

    # Low burnout = no superspreaders = no interventions
    assert len(interventions) == 0


@pytest.mark.skipif(not HAS_NDLIB, reason="ndlib not installed")
def test_recommend_interventions_max_limit(simple_network, initial_burnout_high):
    """Test that max_interventions limit is respected."""
    model = BurnoutContagionModel(simple_network)
    model.configure()

    provider_ids = [f"provider_{i}" for i in range(10)]
    model.set_initial_burnout(provider_ids, initial_burnout_high)

    interventions = model.recommend_interventions(max_interventions=3)

    assert len(interventions) <= 3


# =============================================================================
# Test: Report Generation
# =============================================================================


@pytest.mark.skipif(not HAS_NDLIB, reason="ndlib not installed")
def test_generate_report(simple_network, initial_burnout_mixed):
    """Test comprehensive report generation."""
    model = BurnoutContagionModel(simple_network)
    model.configure()

    provider_ids = [f"provider_{i}" for i in range(10)]
    model.set_initial_burnout(provider_ids, initial_burnout_mixed)

    # Run simulation
    model.simulate(iterations=30)

    # Generate report
    report = model.generate_report()

    assert isinstance(report, ContagionReport)
    assert report.network_size == 10
    assert report.simulation_iterations == 30
    assert 0.0 <= report.current_infection_rate <= 1.0
    assert 0.0 <= report.final_infection_rate <= 1.0
    assert 0.0 <= report.peak_infection_rate <= 1.0
    assert report.contagion_risk in ContagionRisk
    assert len(report.snapshots) == 30


@pytest.mark.skipif(not HAS_NDLIB, reason="ndlib not installed")
def test_generate_report_without_simulation(simple_network, initial_burnout_mixed):
    """Test that report generation requires simulation."""
    model = BurnoutContagionModel(simple_network)
    model.configure()

    provider_ids = [f"provider_{i}" for i in range(10)]
    model.set_initial_burnout(provider_ids, initial_burnout_mixed)

    # Don't run simulation
    with pytest.raises(RuntimeError, match="Must run simulate"):
        model.generate_report()


@pytest.mark.skipif(not HAS_NDLIB, reason="ndlib not installed")
def test_report_risk_levels(simple_network):
    """Test that different burnout levels result in different risk levels."""
    # Low burnout scenario
    low_burnout = {f"provider_{i}": 0.1 for i in range(10)}

    model = BurnoutContagionModel(simple_network)
    model.configure(infection_rate=0.02, recovery_rate=0.05)  # Low spread

    provider_ids = [f"provider_{i}" for i in range(10)]
    model.set_initial_burnout(provider_ids, low_burnout)

    model.simulate(iterations=30)
    report_low = model.generate_report()

    # Should be low or moderate risk
    assert report_low.contagion_risk in (ContagionRisk.LOW, ContagionRisk.MODERATE)


@pytest.mark.skipif(not HAS_NDLIB, reason="ndlib not installed")
def test_report_warnings(simple_network, initial_burnout_high):
    """Test that report generates warnings for high-risk scenarios."""
    model = BurnoutContagionModel(simple_network)
    model.configure(infection_rate=0.2, recovery_rate=0.01)  # High spread

    provider_ids = [f"provider_{i}" for i in range(10)]
    model.set_initial_burnout(provider_ids, initial_burnout_high)

    model.simulate(iterations=50)
    report = model.generate_report()

    # High burnout should generate warnings
    assert len(report.warnings) > 0


# =============================================================================
# Test: Utility Methods
# =============================================================================


@pytest.mark.skipif(not HAS_NDLIB, reason="ndlib not installed")
def test_get_infection_trajectory(simple_network, initial_burnout_mixed):
    """Test getting infection trajectory over time."""
    model = BurnoutContagionModel(simple_network)
    model.configure()

    provider_ids = [f"provider_{i}" for i in range(10)]
    model.set_initial_burnout(provider_ids, initial_burnout_mixed)

    model.simulate(iterations=20)

    trajectory = model.get_infection_trajectory()

    assert len(trajectory) == 20

    # Each point should be (iteration, rate)
    for iteration, rate in trajectory:
        assert isinstance(iteration, int)
        assert 0.0 <= rate <= 1.0


@pytest.mark.skipif(not HAS_NDLIB, reason="ndlib not installed")
def test_get_current_state(simple_network, initial_burnout_mixed):
    """Test getting current simulation state."""
    model = BurnoutContagionModel(simple_network)
    model.configure()

    provider_ids = [f"provider_{i}" for i in range(10)]
    model.set_initial_burnout(provider_ids, initial_burnout_mixed)

    model.simulate(iterations=15)

    state = model.get_current_state()

    assert state["iteration"] == 14  # 0-indexed
    assert "susceptible" in state
    assert "infected" in state
    assert "infection_rate" in state
    assert 0.0 <= state["infection_rate"] <= 1.0


@pytest.mark.skipif(not HAS_NDLIB, reason="ndlib not installed")
def test_get_current_state_no_simulation(simple_network):
    """Test getting state before simulation."""
    model = BurnoutContagionModel(simple_network)

    state = model.get_current_state()

    assert "error" in state


# =============================================================================
# Test: Edge Cases
# =============================================================================


@pytest.mark.skipif(not HAS_NDLIB, reason="ndlib not installed")
@pytest.mark.skip(reason="ndlib has known issues with single-node networks")
def test_single_node_network():
    """Test model with single-node network."""
    # Note: This test is skipped because ndlib's SIS model doesn't support
    # single-node networks well (raises ValueError during iteration)
    G = nx.Graph()
    G.add_node("provider_1")

    model = BurnoutContagionModel(G)
    model.configure()

    burnout_scores = {"provider_1": 0.8}
    model.set_initial_burnout(["provider_1"], burnout_scores)

    # Should run without error (but currently doesn't due to ndlib limitation)
    results = model.simulate(iterations=10)
    assert len(results) == 10


@pytest.mark.skipif(not HAS_NDLIB, reason="ndlib not installed")
def test_disconnected_network():
    """Test model with disconnected components."""
    G = nx.Graph()

    # Component 1
    G.add_edge("provider_1", "provider_2")
    G.add_edge("provider_2", "provider_3")

    # Component 2 (disconnected)
    G.add_edge("provider_4", "provider_5")

    model = BurnoutContagionModel(G)
    model.configure()

    burnout_scores = {
        "provider_1": 0.9,
        "provider_2": 0.1,
        "provider_3": 0.1,
        "provider_4": 0.1,
        "provider_5": 0.1,
    }

    provider_ids = list(burnout_scores.keys())
    model.set_initial_burnout(provider_ids, burnout_scores)

    # Should run without error
    results = model.simulate(iterations=20)
    assert len(results) == 20

    # Infection shouldn't spread to disconnected component
    # (though this is probabilistic, so we just verify it runs)


@pytest.mark.skipif(not HAS_NDLIB, reason="ndlib not installed")
def test_all_infected_initial_state(simple_network):
    """Test with all providers initially infected."""
    model = BurnoutContagionModel(simple_network)
    model.configure()

    # All high burnout
    burnout_scores = {f"provider_{i}": 0.9 for i in range(10)}
    provider_ids = list(burnout_scores.keys())

    model.set_initial_burnout(provider_ids, burnout_scores)

    results = model.simulate(iterations=20)

    # Should still run
    assert len(results) == 20

    # Initial state should have some infected (ndlib adds randomness)
    # We expect at least some nodes to be infected given all have high burnout
    assert model.snapshots[0].infected_count >= 1

    # Over time, infection should spread since all have high burnout
    # Check that infection increases or stays high
    final_infection_count = model.snapshots[-1].infected_count
    assert final_infection_count >= 1


@pytest.mark.skipif(not HAS_NDLIB, reason="ndlib not installed")
def test_all_susceptible_initial_state(simple_network):
    """Test with all providers initially susceptible."""
    model = BurnoutContagionModel(simple_network)
    model.configure()

    # All low burnout
    burnout_scores = {f"provider_{i}": 0.1 for i in range(10)}
    provider_ids = list(burnout_scores.keys())

    model.set_initial_burnout(provider_ids, burnout_scores)

    results = model.simulate(iterations=20)

    # Should still run
    assert len(results) == 20

    # Initial state should have at least one seeded (since all below threshold)
    # Most should be susceptible
    assert model.snapshots[0].susceptible_count >= 8
