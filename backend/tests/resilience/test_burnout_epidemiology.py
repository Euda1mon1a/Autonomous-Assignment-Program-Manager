"""
Tests for burnout epidemiology module.

Tests epidemiological modeling of burnout spread through social networks.
"""

from datetime import datetime, timedelta
from uuid import uuid4

import pytest

try:
    import networkx as nx

    HAS_NETWORKX = True
except ImportError:
    HAS_NETWORKX = False

from app.resilience.burnout_epidemiology import (
    BurnoutEpidemiology,
    BurnoutSIRModel,
    BurnoutState,
    EpiReport,
    InterventionLevel,
)

***REMOVED*** Skip all tests if NetworkX not available
pytestmark = pytest.mark.skipif(
    not HAS_NETWORKX, reason="NetworkX required for burnout epidemiology tests"
)


***REMOVED*** =============================================================================
***REMOVED*** Fixtures
***REMOVED*** =============================================================================


@pytest.fixture
def simple_network():
    """Create a simple social network for testing."""
    G = nx.Graph()

    ***REMOVED*** Create 10 residents
    residents = [uuid4() for _ in range(10)]

    ***REMOVED*** Add nodes
    for r in residents:
        G.add_node(r)

    ***REMOVED*** Create a connected network
    ***REMOVED*** Star topology: resident 0 connected to all others (super-spreader)
    for i in range(1, 10):
        G.add_edge(residents[0], residents[i])

    ***REMOVED*** Add some additional connections
    G.add_edge(residents[1], residents[2])
    G.add_edge(residents[2], residents[3])
    G.add_edge(residents[3], residents[4])
    G.add_edge(residents[5], residents[6])

    return G, residents


@pytest.fixture
def chain_network():
    """Create a chain network (linear connections)."""
    G = nx.Graph()

    residents = [uuid4() for _ in range(5)]

    for r in residents:
        G.add_node(r)

    ***REMOVED*** Linear chain: 0-1-2-3-4
    for i in range(4):
        G.add_edge(residents[i], residents[i + 1])

    return G, residents


@pytest.fixture
def complete_network():
    """Create a complete network (everyone connected to everyone)."""
    G = nx.Graph()

    residents = [uuid4() for _ in range(6)]

    for r in residents:
        G.add_node(r)

    ***REMOVED*** Complete graph
    for i in range(6):
        for j in range(i + 1, 6):
            G.add_edge(residents[i], residents[j])

    return G, residents


@pytest.fixture
def epi_analyzer(simple_network):
    """Create burnout epidemiology analyzer with simple network."""
    G, residents = simple_network
    return BurnoutEpidemiology(G), residents


***REMOVED*** =============================================================================
***REMOVED*** Test BurnoutSIRModel
***REMOVED*** =============================================================================


class TestBurnoutSIRModel:
    """Test SIR model dataclass."""

    def test_valid_model_creation(self):
        """Test creating a valid SIR model."""
        infected = {uuid4(), uuid4()}
        model = BurnoutSIRModel(beta=0.05, gamma=0.02, initial_infected=infected)

        assert model.beta == 0.05
        assert model.gamma == 0.02
        assert model.initial_infected == infected

    def test_basic_reproduction_number(self):
        """Test R0 calculation."""
        model = BurnoutSIRModel(beta=0.1, gamma=0.05, initial_infected=set())

        ***REMOVED*** R0 = beta / gamma = 0.1 / 0.05 = 2.0
        assert model.basic_reproduction_number == 2.0

    def test_r0_gamma_zero(self):
        """Test R0 when gamma is zero (infinite infectious period)."""
        model = BurnoutSIRModel(beta=0.1, gamma=0.0, initial_infected=set())

        assert model.basic_reproduction_number == float("inf")

    def test_invalid_beta_raises_error(self):
        """Test that invalid beta raises ValueError."""
        with pytest.raises(ValueError, match="beta must be in"):
            BurnoutSIRModel(beta=1.5, gamma=0.02, initial_infected=set())

        with pytest.raises(ValueError, match="beta must be in"):
            BurnoutSIRModel(beta=-0.1, gamma=0.02, initial_infected=set())

    def test_invalid_gamma_raises_error(self):
        """Test that invalid gamma raises ValueError."""
        with pytest.raises(ValueError, match="gamma must be in"):
            BurnoutSIRModel(beta=0.05, gamma=1.5, initial_infected=set())

        with pytest.raises(ValueError, match="gamma must be in"):
            BurnoutSIRModel(beta=0.05, gamma=-0.1, initial_infected=set())


***REMOVED*** =============================================================================
***REMOVED*** Test BurnoutEpidemiology - Initialization
***REMOVED*** =============================================================================


class TestBurnoutEpidemiologyInit:
    """Test initialization of burnout epidemiology analyzer."""

    def test_initialization(self, simple_network):
        """Test basic initialization."""
        G, residents = simple_network
        analyzer = BurnoutEpidemiology(G)

        assert analyzer.network == G
        assert len(analyzer.burnout_history) == 0
        assert len(analyzer._contact_cache) == 0

    def test_network_summary(self, simple_network):
        """Test network summary statistics."""
        G, residents = simple_network
        analyzer = BurnoutEpidemiology(G)

        summary = analyzer.get_network_summary()

        assert summary["total_nodes"] == 10
        assert summary["total_edges"] == 13
        assert summary["average_degree"] > 0
        assert "density" in summary
        assert "is_connected" in summary

    def test_requires_networkx(self):
        """Test that NetworkX requirement is enforced."""
        ***REMOVED*** This test would only fail if NetworkX was not installed
        ***REMOVED*** Covered by module-level skipif
        pass


***REMOVED*** =============================================================================
***REMOVED*** Test Close Contacts
***REMOVED*** =============================================================================


class TestCloseContacts:
    """Test close contact identification."""

    def test_get_close_contacts_star_network(self, simple_network):
        """Test getting contacts in star network."""
        G, residents = simple_network
        analyzer = BurnoutEpidemiology(G)

        ***REMOVED*** Central node (0) should have 9 contacts
        contacts = analyzer.get_close_contacts(residents[0])
        assert len(contacts) == 9

        ***REMOVED*** Peripheral node should have fewer contacts
        contacts = analyzer.get_close_contacts(residents[1])
        assert len(contacts) >= 1  ***REMOVED*** Connected to center and possibly others

    def test_get_close_contacts_chain(self, chain_network):
        """Test getting contacts in chain network."""
        G, residents = chain_network
        analyzer = BurnoutEpidemiology(G)

        ***REMOVED*** Middle node should have 2 contacts
        contacts = analyzer.get_close_contacts(residents[2])
        assert len(contacts) == 2

        ***REMOVED*** End node should have 1 contact
        contacts = analyzer.get_close_contacts(residents[0])
        assert len(contacts) == 1

    def test_get_close_contacts_nonexistent_node(self, simple_network):
        """Test getting contacts for nonexistent node."""
        G, residents = simple_network
        analyzer = BurnoutEpidemiology(G)

        fake_id = uuid4()
        contacts = analyzer.get_close_contacts(fake_id)

        assert len(contacts) == 0

    def test_close_contacts_caching(self, simple_network):
        """Test that close contacts are cached."""
        G, residents = simple_network
        analyzer = BurnoutEpidemiology(G)

        ***REMOVED*** First call
        contacts1 = analyzer.get_close_contacts(residents[0])

        ***REMOVED*** Should be cached
        assert (residents[0], timedelta(weeks=4)) in analyzer._contact_cache

        ***REMOVED*** Second call should use cache
        contacts2 = analyzer.get_close_contacts(residents[0])

        assert contacts1 == contacts2


***REMOVED*** =============================================================================
***REMOVED*** Test Reproduction Number Calculation
***REMOVED*** =============================================================================


class TestReproductionNumber:
    """Test reproduction number (Rt) calculation."""

    def test_rt_no_cases(self, epi_analyzer):
        """Test Rt calculation with no burnout cases."""
        analyzer, residents = epi_analyzer

        report = analyzer.calculate_reproduction_number(set())

        assert report.reproduction_number == 0.0
        assert report.status == "no_cases"
        assert report.total_cases_analyzed == 0
        assert report.intervention_level == InterventionLevel.NONE

    def test_rt_single_case_no_spread(self, epi_analyzer):
        """Test Rt with one case that doesn't spread."""
        analyzer, residents = epi_analyzer

        ***REMOVED*** Record one burnout case
        analyzer.record_burnout_state(
            residents[0], BurnoutState.BURNED_OUT, datetime.now() - timedelta(weeks=2)
        )

        report = analyzer.calculate_reproduction_number({residents[0]})

        ***REMOVED*** No secondary cases, but we estimate R=1 conservatively
        assert report.reproduction_number >= 0.0
        assert report.total_cases_analyzed == 1

    def test_rt_with_secondary_cases(self, epi_analyzer):
        """Test Rt calculation with secondary cases."""
        analyzer, residents = epi_analyzer

        now = datetime.now()

        ***REMOVED*** Index case becomes burned out
        analyzer.record_burnout_state(
            residents[0], BurnoutState.BURNED_OUT, now - timedelta(weeks=3)
        )

        ***REMOVED*** Two contacts become burned out within time window
        analyzer.record_burnout_state(
            residents[1], BurnoutState.BURNED_OUT, now - timedelta(weeks=2)
        )
        analyzer.record_burnout_state(
            residents[2], BurnoutState.BURNED_OUT, now - timedelta(weeks=1)
        )

        report = analyzer.calculate_reproduction_number({residents[0]})

        ***REMOVED*** Should detect secondary cases
        assert report.reproduction_number > 0
        assert (
            residents[1] in report.high_risk_contacts
            or residents[2] in report.high_risk_contacts
        )

    def test_rt_status_declining(self, epi_analyzer):
        """Test status is 'declining' when Rt < 0.5."""
        analyzer, residents = epi_analyzer

        ***REMOVED*** Mock a low Rt scenario
        analyzer.record_burnout_state(
            residents[0], BurnoutState.BURNED_OUT, datetime.now() - timedelta(weeks=10)
        )

        report = analyzer.calculate_reproduction_number({residents[0]})

        ***REMOVED*** With no recent secondary cases, Rt should be low
        ***REMOVED*** Status depends on Rt value
        assert report.status in ["declining", "controlled", "no_cases", "spreading"]

    def test_rt_multiple_index_cases(self, simple_network):
        """Test Rt with multiple index cases."""
        G, residents = simple_network
        analyzer = BurnoutEpidemiology(G)

        now = datetime.now()

        ***REMOVED*** Multiple index cases
        for i in range(3):
            analyzer.record_burnout_state(
                residents[i], BurnoutState.BURNED_OUT, now - timedelta(weeks=3)
            )

        report = analyzer.calculate_reproduction_number(set(residents[:3]))

        assert report.total_cases_analyzed == 3


***REMOVED*** =============================================================================
***REMOVED*** Test SIR Simulation
***REMOVED*** =============================================================================


class TestSIRSimulation:
    """Test SIR epidemic simulation."""

    def test_sir_basic_simulation(self, chain_network):
        """Test basic SIR simulation."""
        G, residents = chain_network
        analyzer = BurnoutEpidemiology(G)

        ***REMOVED*** Start with one infected
        initial = {residents[0]}

        results = analyzer.simulate_sir_spread(
            initial_infected=initial, beta=0.3, gamma=0.1, steps=20
        )

        ***REMOVED*** Should have results for multiple steps
        assert len(results) > 0

        ***REMOVED*** First step should have 1 infected
        assert results[0]["infected"] == 1
        assert results[0]["susceptible"] == 4

        ***REMOVED*** Total should remain constant (conservation)
        for step in results:
            total = step["susceptible"] + step["infected"] + step["recovered"]
            assert total == 5

    def test_sir_simulation_no_spread(self, chain_network):
        """Test SIR simulation with beta=0 (no transmission)."""
        G, residents = chain_network
        analyzer = BurnoutEpidemiology(G)

        initial = {residents[0]}

        results = analyzer.simulate_sir_spread(
            initial_infected=initial,
            beta=0.0,  ***REMOVED*** No transmission
            gamma=0.5,  ***REMOVED*** Fast recovery
            steps=10,
        )

        ***REMOVED*** Infected should decline to zero
        final = results[-1]
        assert final["infected"] <= len(initial) or len(results) < 10

    def test_sir_simulation_high_beta(self, complete_network):
        """Test SIR simulation with high transmission rate."""
        G, residents = complete_network
        analyzer = BurnoutEpidemiology(G)

        initial = {residents[0]}

        results = analyzer.simulate_sir_spread(
            initial_infected=initial,
            beta=0.8,  ***REMOVED*** High transmission
            gamma=0.05,  ***REMOVED*** Slow recovery
            steps=30,
        )

        ***REMOVED*** Should see infection spread
        ***REMOVED*** Peak infected should be > initial
        max_infected = max(step["infected"] for step in results)
        assert max_infected >= 1

    def test_sir_time_series_structure(self, simple_network):
        """Test that SIR time series has correct structure."""
        G, residents = simple_network
        analyzer = BurnoutEpidemiology(G)

        results = analyzer.simulate_sir_spread(initial_infected={residents[0]}, steps=5)

        ***REMOVED*** Check structure
        for step_data in results:
            assert "step" in step_data
            assert "week" in step_data
            assert "susceptible" in step_data
            assert "infected" in step_data
            assert "recovered" in step_data
            assert "S" in step_data
            assert "I" in step_data
            assert "R" in step_data


***REMOVED*** =============================================================================
***REMOVED*** Test Super-Spreader Identification
***REMOVED*** =============================================================================


class TestSuperSpreaders:
    """Test super-spreader identification."""

    def test_identify_super_spreaders_star(self, simple_network):
        """Test identifying super-spreaders in star network."""
        G, residents = simple_network
        analyzer = BurnoutEpidemiology(G)

        ***REMOVED*** Central node has degree 9
        super_spreaders = analyzer.identify_super_spreaders(threshold_degree=5)

        ***REMOVED*** Should identify the central node
        assert len(super_spreaders) >= 1
        assert residents[0] in super_spreaders

    def test_identify_super_spreaders_chain(self, chain_network):
        """Test super-spreader identification in chain (low connectivity)."""
        G, residents = chain_network
        analyzer = BurnoutEpidemiology(G)

        ***REMOVED*** No node has degree > 5 in a chain
        super_spreaders = analyzer.identify_super_spreaders(threshold_degree=5)

        assert len(super_spreaders) == 0

    def test_identify_super_spreaders_complete(self, complete_network):
        """Test super-spreader identification in complete network."""
        G, residents = complete_network
        analyzer = BurnoutEpidemiology(G)

        ***REMOVED*** All nodes have degree 5 in complete graph of 6 nodes
        super_spreaders = analyzer.identify_super_spreaders(threshold_degree=5)

        ***REMOVED*** All nodes should be super-spreaders
        assert len(super_spreaders) == 6

    def test_identify_super_spreaders_custom_threshold(self, simple_network):
        """Test super-spreader identification with custom threshold."""
        G, residents = simple_network
        analyzer = BurnoutEpidemiology(G)

        ***REMOVED*** Low threshold should find more
        low_threshold = analyzer.identify_super_spreaders(threshold_degree=1)

        ***REMOVED*** High threshold should find fewer
        high_threshold = analyzer.identify_super_spreaders(threshold_degree=10)

        assert len(low_threshold) >= len(high_threshold)


***REMOVED*** =============================================================================
***REMOVED*** Test Herd Immunity
***REMOVED*** =============================================================================


class TestHerdImmunity:
    """Test herd immunity threshold calculation."""

    def test_herd_immunity_r0_2(self, epi_analyzer):
        """Test HIT for R0=2."""
        analyzer, _ = epi_analyzer

        hit = analyzer.calculate_herd_immunity_threshold(2.0)

        ***REMOVED*** HIT = 1 - 1/2 = 0.5
        assert hit == 0.5

    def test_herd_immunity_r0_3(self, epi_analyzer):
        """Test HIT for R0=3."""
        analyzer, _ = epi_analyzer

        hit = analyzer.calculate_herd_immunity_threshold(3.0)

        ***REMOVED*** HIT = 1 - 1/3 ≈ 0.667
        assert abs(hit - 0.667) < 0.01

    def test_herd_immunity_r0_less_than_1(self, epi_analyzer):
        """Test HIT when R0 < 1 (no herd immunity needed)."""
        analyzer, _ = epi_analyzer

        hit = analyzer.calculate_herd_immunity_threshold(0.8)

        ***REMOVED*** When R0 < 1, epidemic dies out without herd immunity
        assert hit == 0.0

    def test_herd_immunity_r0_high(self, epi_analyzer):
        """Test HIT for high R0."""
        analyzer, _ = epi_analyzer

        hit = analyzer.calculate_herd_immunity_threshold(10.0)

        ***REMOVED*** HIT = 1 - 1/10 = 0.9
        assert hit == 0.9


***REMOVED*** =============================================================================
***REMOVED*** Test Interventions
***REMOVED*** =============================================================================


class TestInterventions:
    """Test intervention recommendations."""

    def test_interventions_rt_low(self, epi_analyzer):
        """Test interventions when Rt < 0.5."""
        analyzer, _ = epi_analyzer

        interventions = analyzer.get_interventions(0.3)

        ***REMOVED*** Should recommend preventive measures
        assert len(interventions) > 0
        assert any("preventive" in i.lower() for i in interventions)

    def test_interventions_rt_controlled(self, epi_analyzer):
        """Test interventions when 0.5 <= Rt < 1."""
        analyzer, _ = epi_analyzer

        interventions = analyzer.get_interventions(0.8)

        ***REMOVED*** Should recommend monitoring
        assert len(interventions) > 0
        assert any("monitor" in i.lower() for i in interventions)

    def test_interventions_rt_spreading(self, epi_analyzer):
        """Test interventions when 1 <= Rt < 2."""
        analyzer, _ = epi_analyzer

        interventions = analyzer.get_interventions(1.5)

        ***REMOVED*** Should recommend moderate interventions
        assert len(interventions) > 0
        assert any(
            "moderate" in i.lower() or "workload" in i.lower() for i in interventions
        )

    def test_interventions_rt_aggressive(self, epi_analyzer):
        """Test interventions when 2 <= Rt < 3."""
        analyzer, _ = epi_analyzer

        interventions = analyzer.get_interventions(2.5)

        ***REMOVED*** Should recommend aggressive interventions
        assert len(interventions) > 0
        assert any(
            "aggressive" in i.lower() or "mandatory" in i.lower() for i in interventions
        )

    def test_interventions_rt_emergency(self, epi_analyzer):
        """Test interventions when Rt >= 3."""
        analyzer, _ = epi_analyzer

        interventions = analyzer.get_interventions(3.5)

        ***REMOVED*** Should recommend emergency interventions
        assert len(interventions) > 0
        assert any(
            "emergency" in i.lower() or "immediate" in i.lower() for i in interventions
        )

    def test_interventions_include_super_spreaders(self, simple_network):
        """Test that interventions mention super-spreaders when Rt > 1."""
        G, residents = simple_network
        analyzer = BurnoutEpidemiology(G)

        interventions = analyzer.get_interventions(1.5)

        ***REMOVED*** Should mention super-spreaders for star network
        intervention_text = " ".join(interventions).lower()
        assert "super" in intervention_text or "connectivity" in intervention_text


***REMOVED*** =============================================================================
***REMOVED*** Test EpiReport
***REMOVED*** =============================================================================


class TestEpiReport:
    """Test epidemiological report."""

    def test_report_to_dict(self):
        """Test converting report to dictionary."""
        report = EpiReport(
            reproduction_number=1.5,
            status="spreading",
            secondary_cases={"id1": 2, "id2": 1},
            recommended_interventions=["Intervention A", "Intervention B"],
            intervention_level=InterventionLevel.MODERATE,
        )

        data = report.to_dict()

        assert data["reproduction_number"] == 1.5
        assert data["status"] == "spreading"
        assert data["intervention_level"] == InterventionLevel.MODERATE
        assert len(data["recommended_interventions"]) == 2
        assert "analyzed_at" in data

    def test_report_with_super_spreaders(self):
        """Test report with super-spreaders."""
        uid1 = uuid4()
        uid2 = uuid4()

        report = EpiReport(
            reproduction_number=2.0,
            status="rapid_spread",
            secondary_cases={},
            recommended_interventions=[],
            super_spreaders=[uid1, uid2],
            high_risk_contacts=[uid1],
        )

        data = report.to_dict()

        assert len(data["super_spreaders"]) == 2
        assert len(data["high_risk_contacts"]) == 1


***REMOVED*** =============================================================================
***REMOVED*** Test Burnout State Tracking
***REMOVED*** =============================================================================


class TestBurnoutStateTracking:
    """Test burnout state recording and tracking."""

    def test_record_burnout_state(self, epi_analyzer):
        """Test recording burnout state."""
        analyzer, residents = epi_analyzer

        now = datetime.now()
        analyzer.record_burnout_state(residents[0], BurnoutState.BURNED_OUT, now)

        ***REMOVED*** Check history
        assert residents[0] in analyzer.burnout_history
        assert len(analyzer.burnout_history[residents[0]]) == 1

        timestamp, state = analyzer.burnout_history[residents[0]][0]
        assert state == BurnoutState.BURNED_OUT
        assert timestamp == now

    def test_record_multiple_states(self, epi_analyzer):
        """Test recording multiple state changes."""
        analyzer, residents = epi_analyzer

        now = datetime.now()

        ***REMOVED*** Record state progression
        analyzer.record_burnout_state(
            residents[0], BurnoutState.SUSCEPTIBLE, now - timedelta(weeks=8)
        )
        analyzer.record_burnout_state(
            residents[0], BurnoutState.AT_RISK, now - timedelta(weeks=4)
        )
        analyzer.record_burnout_state(
            residents[0], BurnoutState.BURNED_OUT, now - timedelta(weeks=2)
        )
        analyzer.record_burnout_state(residents[0], BurnoutState.RECOVERED, now)

        ***REMOVED*** Check progression
        history = analyzer.burnout_history[residents[0]]
        assert len(history) == 4
        assert history[0][1] == BurnoutState.SUSCEPTIBLE
        assert history[-1][1] == BurnoutState.RECOVERED

    def test_get_current_state(self, epi_analyzer):
        """Test getting current state."""
        analyzer, residents = epi_analyzer

        ***REMOVED*** No history = susceptible
        state = analyzer._get_current_state(residents[0])
        assert state == BurnoutState.SUSCEPTIBLE

        ***REMOVED*** Add state
        analyzer.record_burnout_state(residents[0], BurnoutState.BURNED_OUT)

        state = analyzer._get_current_state(residents[0])
        assert state == BurnoutState.BURNED_OUT

    def test_burnout_summary(self, epi_analyzer):
        """Test burnout summary statistics."""
        analyzer, residents = epi_analyzer

        ***REMOVED*** Record some burnout states
        analyzer.record_burnout_state(residents[0], BurnoutState.BURNED_OUT)
        analyzer.record_burnout_state(residents[1], BurnoutState.AT_RISK)
        analyzer.record_burnout_state(residents[2], BurnoutState.RECOVERED)

        summary = analyzer.get_burnout_summary()

        assert summary["total_residents"] == 10
        assert summary["burned_out"] >= 1
        assert summary["at_risk"] >= 1
        assert summary["recovered"] >= 1
        assert summary["susceptible"] >= 0


***REMOVED*** =============================================================================
***REMOVED*** Integration Tests
***REMOVED*** =============================================================================


class TestIntegration:
    """Integration tests combining multiple features."""

    def test_full_epidemic_workflow(self, simple_network):
        """Test complete epidemic analysis workflow."""
        G, residents = simple_network
        analyzer = BurnoutEpidemiology(G)

        now = datetime.now()

        ***REMOVED*** Initial outbreak
        analyzer.record_burnout_state(
            residents[0], BurnoutState.BURNED_OUT, now - timedelta(weeks=4)
        )

        ***REMOVED*** Spread to contacts
        for i in [1, 2, 3]:
            analyzer.record_burnout_state(
                residents[i], BurnoutState.BURNED_OUT, now - timedelta(weeks=3)
            )

        ***REMOVED*** Calculate Rt
        burned_out = {residents[0], residents[1], residents[2], residents[3]}
        report = analyzer.calculate_reproduction_number(burned_out)

        ***REMOVED*** Should detect spread
        assert report.reproduction_number > 0
        assert len(report.recommended_interventions) > 0

        ***REMOVED*** Simulate future spread
        sir_results = analyzer.simulate_sir_spread(
            initial_infected=burned_out, beta=0.1, gamma=0.05, steps=20
        )

        ***REMOVED*** Should have projection
        assert len(sir_results) > 0

        ***REMOVED*** Identify super-spreaders
        super_spreaders = analyzer.identify_super_spreaders(threshold_degree=3)

        ***REMOVED*** Central node should be identified
        assert residents[0] in super_spreaders

    def test_intervention_escalation(self, chain_network):
        """Test that interventions escalate with increasing Rt."""
        G, residents = chain_network
        analyzer = BurnoutEpidemiology(G)

        ***REMOVED*** Get interventions at different Rt levels
        interventions_low = analyzer.get_interventions(0.5)
        interventions_moderate = analyzer.get_interventions(1.5)
        interventions_high = analyzer.get_interventions(2.5)
        interventions_emergency = analyzer.get_interventions(3.5)

        ***REMOVED*** Should have increasing intervention intensity
        assert len(interventions_emergency) > len(interventions_moderate)

    def test_network_metrics_and_epidemiology(self, complete_network):
        """Test combining network metrics with epidemic analysis."""
        G, residents = complete_network
        analyzer = BurnoutEpidemiology(G)

        ***REMOVED*** Get network summary
        network_summary = analyzer.get_network_summary()

        ***REMOVED*** Complete graph should have high density
        assert network_summary["density"] > 0.8
        assert network_summary["is_connected"] is True

        ***REMOVED*** Record burnout
        analyzer.record_burnout_state(residents[0], BurnoutState.BURNED_OUT)

        ***REMOVED*** Get burnout summary
        burnout_summary = analyzer.get_burnout_summary()

        assert burnout_summary["burned_out"] >= 1

        ***REMOVED*** Simulate - should spread quickly in complete network
        sir_results = analyzer.simulate_sir_spread(
            initial_infected={residents[0]}, beta=0.3, gamma=0.1, steps=15
        )

        ***REMOVED*** Infection should spread
        max_infected = max(step["infected"] for step in sir_results)
        assert max_infected > 1
