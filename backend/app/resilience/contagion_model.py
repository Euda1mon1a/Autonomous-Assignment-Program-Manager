"""
Burnout Contagion Modeling (Epidemiological Network Diffusion Pattern).

Burnout spreads like a contagion through social networks. High-stress
individuals amplify stress in their collaborators, creating cascade effects.
Understanding burnout as a network phenomenon allows proactive intervention.

Key Principles (from Epidemiology):
- Burnout "infection" spreads through collaboration networks
- Superspreaders (high-stress + high-centrality) amplify contagion
- Early intervention on network hubs prevents cascades
- Network topology determines outbreak severity

Key Principles (from Social Contagion Research):
- Emotional contagion occurs through social ties
- Repeated exposure increases "infection" probability
- Recovery is possible with reduced stress and social support
- Network interventions (edge removal, buffer insertion) reduce spread

This module implements:
1. SIS (Susceptible-Infected-Susceptible) burnout contagion model
2. Superspreader identification (high burnout + high centrality)
3. Cascade prediction and simulation
4. Network intervention recommendations
5. Burnout propagation visualization and analysis
"""

import logging
import statistics
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

import networkx as nx

logger = logging.getLogger(__name__)

# Try to import ndlib for diffusion modeling
try:
    import ndlib.models.ModelConfig as mc
    import ndlib.models.epidemics as ep
    HAS_NDLIB = True
except ImportError:
    HAS_NDLIB = False
    logger.warning("ndlib not installed - burnout contagion modeling unavailable")


# =============================================================================
# Enums and Constants
# =============================================================================


class BurnoutState(str, Enum):
    """Burnout state for a provider."""
    SUSCEPTIBLE = "susceptible"  # Low burnout, can be infected
    INFECTED = "infected"        # High burnout, can infect others
    RECOVERED = "recovered"      # Was infected but recovered (if using SIR)


class InterventionType(str, Enum):
    """Type of network intervention."""
    EDGE_REMOVAL = "edge_removal"           # Reduce collaboration frequency
    BUFFER_INSERTION = "buffer_insertion"   # Add low-burnout intermediary
    WORKLOAD_REDUCTION = "workload_reduction"  # Reduce superspreader load
    QUARANTINE = "quarantine"               # Temporarily isolate from network
    PEER_SUPPORT = "peer_support"           # Add supportive connections


class ContagionRisk(str, Enum):
    """Overall contagion risk level."""
    LOW = "low"           # <10% of network infected
    MODERATE = "moderate"  # 10-25% infected
    HIGH = "high"         # 25-50% infected
    CRITICAL = "critical"  # >50% infected, cascade likely


# =============================================================================
# Data Classes
# =============================================================================


@dataclass
class BurnoutSnapshot:
    """Snapshot of network burnout state at a point in time."""
    iteration: int
    timestamp: datetime
    susceptible_count: int
    infected_count: int
    infection_rate: float  # % of network infected
    newly_infected: list[str] = field(default_factory=list)
    newly_recovered: list[str] = field(default_factory=list)

    # Network metrics
    mean_burnout_score: float = 0.0
    max_burnout_score: float = 0.0
    burnout_std_dev: float = 0.0


@dataclass
class SuperspreaderProfile:
    """Profile of a potential superspreader."""
    provider_id: str
    provider_name: str

    # Burnout metrics
    burnout_score: float  # 0.0-1.0
    burnout_trend: str    # "increasing", "stable", "decreasing"

    # Network metrics
    degree_centrality: float
    betweenness_centrality: float
    eigenvector_centrality: float
    composite_centrality: float

    # Superspreader risk
    superspreader_score: float  # burnout * centrality
    risk_level: str  # "low", "moderate", "high", "critical"

    # Potential impact
    direct_contacts: int
    estimated_cascade_size: int  # How many could be infected via this node


@dataclass
class NetworkIntervention:
    """Recommended network intervention to reduce contagion."""
    id: UUID
    intervention_type: InterventionType
    priority: int  # 1 = highest
    reason: str

    # Target
    target_providers: list[str]

    # Expected impact
    estimated_infection_reduction: float  # % reduction in final infection rate
    estimated_cost: float  # Hours of schedule disruption

    # Affected edges
    affected_edges: list[tuple[str, str]] = field(default_factory=list)

    # Status
    status: str = "recommended"  # recommended, approved, implemented, rejected
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class ContagionReport:
    """Comprehensive burnout contagion analysis report."""
    generated_at: datetime
    network_size: int

    # Current state
    current_susceptible: int
    current_infected: int
    current_infection_rate: float
    contagion_risk: ContagionRisk

    # Simulation results
    simulation_iterations: int
    final_infection_rate: float
    peak_infection_rate: float
    peak_iteration: int

    # Superspreaders
    superspreaders: list[SuperspreaderProfile]
    total_superspreaders: int

    # Interventions
    recommended_interventions: list[NetworkIntervention]

    # Trajectory
    snapshots: list[BurnoutSnapshot] = field(default_factory=list)

    # Warnings
    warnings: list[str] = field(default_factory=list)


# =============================================================================
# Burnout Contagion Model
# =============================================================================


class BurnoutContagionModel:
    """
    Models burnout spread through provider social networks using SIS epidemiology.

    The Susceptible-Infected-Susceptible (SIS) model captures burnout dynamics:
    - Susceptible: Low burnout, can become infected through contact
    - Infected: High burnout, can infect susceptibles
    - Recovery: Infected can recover (return to susceptible) with interventions

    Unlike SIR models, SIS allows reinfection - appropriate for burnout which
    can recur even after recovery.
    """

    def __init__(self, social_graph: nx.Graph):
        """
        Initialize burnout contagion model.

        Args:
            social_graph: NetworkX graph where nodes are providers and edges
                         represent collaboration/social contact
        """
        if not HAS_NDLIB:
            raise ImportError(
                "ndlib is required for burnout contagion modeling. "
                "Install with: pip install ndlib>=5.1.0"
            )

        self.social_graph = social_graph
        self.model = None
        self.config = None

        # Model parameters
        self.infection_rate = 0.05  # Beta: probability of infection per contact
        self.recovery_rate = 0.01   # Gamma: probability of recovery per iteration

        # Simulation state
        self.snapshots: list[BurnoutSnapshot] = []
        self.current_iteration = 0

        # Burnout scores
        self.burnout_scores: dict[str, float] = {}

        # Cache
        self._centrality_cache: dict[str, dict[str, float]] = {}

    def configure(
        self,
        infection_rate: float = 0.05,
        recovery_rate: float = 0.01,
    ):
        """
        Configure SIS model parameters.

        Args:
            infection_rate: Probability of burnout spreading per contact (beta)
                          Higher = faster spread. Typical range: 0.01-0.15
            recovery_rate: Probability of recovery per iteration (gamma)
                          Higher = faster recovery. Typical range: 0.001-0.05
        """
        if not (0.0 <= infection_rate <= 1.0):
            raise ValueError("infection_rate must be between 0.0 and 1.0")
        if not (0.0 <= recovery_rate <= 1.0):
            raise ValueError("recovery_rate must be between 0.0 and 1.0")

        self.infection_rate = infection_rate
        self.recovery_rate = recovery_rate

        # Create SIS model
        self.model = ep.SISModel(self.social_graph)

        # Configure model
        self.config = mc.Configuration()
        self.config.add_model_parameter('beta', infection_rate)
        self.config.add_model_parameter('lambda', recovery_rate)
        self.model.set_initial_status(self.config)

        logger.info(
            f"Configured SIS model: beta={infection_rate:.3f}, "
            f"lambda={recovery_rate:.3f}"
        )

    def set_initial_burnout(
        self,
        provider_ids: list[str],
        burnout_scores: dict[str, float],
    ):
        """
        Set initial burnout state for providers.

        Args:
            provider_ids: List of provider IDs in the network
            burnout_scores: Dict mapping provider_id -> burnout score (0.0-1.0)
                          Scores >0.5 are considered "infected"
        """
        if self.model is None:
            raise RuntimeError("Must call configure() before set_initial_burnout()")

        self.burnout_scores = burnout_scores.copy()

        # Set initial status based on burnout threshold
        burnout_threshold = 0.5

        # Count infected nodes
        infected_count = sum(
            1 for score in burnout_scores.values()
            if score >= burnout_threshold
        )

        # Set status for all nodes explicitly
        for provider_id in provider_ids:
            burnout = burnout_scores.get(provider_id, 0.0)

            if burnout >= burnout_threshold:
                # High burnout = infected
                self.config.add_node_configuration("status", provider_id, 1)
            else:
                # Low burnout = susceptible
                self.config.add_node_configuration("status", provider_id, 0)

        # If no nodes are infected, seed at least one to enable simulation
        if infected_count == 0 and len(provider_ids) > 0:
            # Find node with highest burnout (even if below threshold)
            max_burnout_id = max(provider_ids, key=lambda pid: burnout_scores.get(pid, 0.0))
            # Override to infected
            self.config.add_node_configuration("status", max_burnout_id, 1)
            logger.info(
                f"No nodes above threshold - seeding {max_burnout_id} as infected"
            )

        self.model.set_initial_status(self.config)

        logger.info(
            f"Initial burnout state: {infected_count}/{len(provider_ids)} infected "
            f"(threshold={burnout_threshold})"
        )

    def simulate(self, iterations: int = 50) -> list[dict]:
        """
        Run burnout contagion simulation.

        Args:
            iterations: Number of simulation steps to run

        Returns:
            List of iteration results, each containing:
            - iteration: iteration number
            - status: dict of node statuses
            - node_count: dict with counts per status
            - status_delta: changes from previous iteration
        """
        if self.model is None:
            raise RuntimeError("Must call configure() before simulate()")

        self.snapshots.clear()
        results = []

        logger.info(f"Starting burnout contagion simulation for {iterations} iterations")

        for i in range(iterations):
            # Execute iteration
            iteration_result = self.model.iteration()
            results.append(iteration_result)

            # Extract state
            node_status = iteration_result['status']
            node_count = iteration_result['node_count']

            susceptible = node_count.get(0, 0)
            infected = node_count.get(1, 0)
            total = susceptible + infected
            infection_rate = infected / total if total > 0 else 0.0

            # Calculate burnout statistics
            if self.burnout_scores:
                burnout_values = list(self.burnout_scores.values())
                mean_burnout = statistics.mean(burnout_values)
                max_burnout = max(burnout_values)
                std_burnout = statistics.stdev(burnout_values) if len(burnout_values) > 1 else 0.0
            else:
                mean_burnout = max_burnout = std_burnout = 0.0

            # Create snapshot
            snapshot = BurnoutSnapshot(
                iteration=i,
                timestamp=datetime.now(),
                susceptible_count=susceptible,
                infected_count=infected,
                infection_rate=infection_rate,
                mean_burnout_score=mean_burnout,
                max_burnout_score=max_burnout,
                burnout_std_dev=std_burnout,
            )

            # Track newly infected/recovered
            if i > 0:
                prev_status = results[i-1]['status']
                for node_id, current in node_status.items():
                    previous = prev_status.get(node_id, 0)
                    if previous == 0 and current == 1:
                        snapshot.newly_infected.append(node_id)
                    elif previous == 1 and current == 0:
                        snapshot.newly_recovered.append(node_id)

            self.snapshots.append(snapshot)
            self.current_iteration = i

        logger.info(
            f"Simulation complete: {iterations} iterations, "
            f"final infection rate: {self.snapshots[-1].infection_rate:.1%}"
        )

        return results

    def identify_superspreaders(
        self,
        centrality_weights: dict[str, float] | None = None,
    ) -> list[str]:
        """
        Identify superspreaders: high-burnout nodes with high network centrality.

        Superspreaders are the most dangerous nodes - they have:
        1. High burnout (likely to be "infected")
        2. High centrality (many connections or strategic position)

        These nodes can trigger burnout cascades. Protecting them prevents outbreaks.

        Args:
            centrality_weights: Weights for combining centrality measures
                              Default: {"degree": 0.3, "betweenness": 0.4, "eigenvector": 0.3}

        Returns:
            List of provider IDs identified as superspreaders
        """
        if not self.burnout_scores:
            logger.warning("No burnout scores set - cannot identify superspreaders")
            return []

        weights = centrality_weights or {
            "degree": 0.3,
            "betweenness": 0.4,
            "eigenvector": 0.3,
        }

        # Calculate centrality if not cached
        if not self._centrality_cache:
            self._calculate_centrality()

        superspreaders = []

        for node_id in self.social_graph.nodes():
            node_id_str = str(node_id)

            # Get burnout score
            burnout = self.burnout_scores.get(node_id_str, 0.0)

            # Get centrality
            centrality = self._centrality_cache.get(node_id_str, {})
            degree_cent = centrality.get("degree", 0.0)
            between_cent = centrality.get("betweenness", 0.0)
            eigen_cent = centrality.get("eigenvector", 0.0)

            # Calculate composite centrality
            composite_cent = (
                degree_cent * weights["degree"] +
                between_cent * weights["betweenness"] +
                eigen_cent * weights["eigenvector"]
            )

            # Superspreader criteria:
            # 1. High burnout (>0.6) OR
            # 2. Moderate burnout (>0.5) AND high centrality (top 20%)
            is_high_burnout = burnout >= 0.6
            is_moderate_burnout_high_centrality = (
                burnout >= 0.5 and composite_cent >= 0.15
            )

            if is_high_burnout or is_moderate_burnout_high_centrality:
                superspreaders.append(node_id_str)

        logger.info(f"Identified {len(superspreaders)} superspreaders")

        return superspreaders

    def get_superspreader_profiles(
        self,
        provider_names: dict[str, str] | None = None,
    ) -> list[SuperspreaderProfile]:
        """
        Get detailed profiles of superspreaders.

        Args:
            provider_names: Optional mapping of provider_id -> name

        Returns:
            List of SuperspreaderProfile objects
        """
        provider_names = provider_names or {}

        if not self._centrality_cache:
            self._calculate_centrality()

        superspreader_ids = self.identify_superspreaders()
        profiles = []

        for provider_id in superspreader_ids:
            burnout = self.burnout_scores.get(provider_id, 0.0)
            centrality = self._centrality_cache.get(provider_id, {})

            degree_cent = centrality.get("degree", 0.0)
            between_cent = centrality.get("betweenness", 0.0)
            eigen_cent = centrality.get("eigenvector", 0.0)
            composite_cent = (degree_cent + between_cent + eigen_cent) / 3

            superspreader_score = burnout * composite_cent

            # Determine risk level
            if superspreader_score >= 0.8:
                risk_level = "critical"
            elif superspreader_score >= 0.7:
                risk_level = "high"
            elif superspreader_score >= 0.6:
                risk_level = "moderate"
            else:
                risk_level = "low"

            # Count direct contacts
            direct_contacts = self.social_graph.degree(provider_id)

            # Estimate cascade size (simplified)
            estimated_cascade = int(direct_contacts * 2.5 * burnout)

            profile = SuperspreaderProfile(
                provider_id=provider_id,
                provider_name=provider_names.get(provider_id, provider_id),
                burnout_score=burnout,
                burnout_trend="stable",  # Would need historical data
                degree_centrality=degree_cent,
                betweenness_centrality=between_cent,
                eigenvector_centrality=eigen_cent,
                composite_centrality=composite_cent,
                superspreader_score=superspreader_score,
                risk_level=risk_level,
                direct_contacts=direct_contacts,
                estimated_cascade_size=estimated_cascade,
            )

            profiles.append(profile)

        # Sort by superspreader score
        profiles.sort(key=lambda p: p.superspreader_score, reverse=True)

        return profiles

    def recommend_interventions(
        self,
        max_interventions: int = 10,
    ) -> list[NetworkIntervention]:
        """
        Recommend network interventions to reduce burnout contagion.

        Interventions include:
        1. Edge removal: Reduce collaboration between high-burnout pairs
        2. Buffer insertion: Add low-burnout intermediaries
        3. Workload reduction: Lower load on superspreaders
        4. Quarantine: Temporarily isolate superspreaders

        Args:
            max_interventions: Maximum number of interventions to recommend

        Returns:
            List of NetworkIntervention objects, sorted by priority
        """
        interventions = []

        # Get superspreaders
        superspreaders = self.identify_superspreaders()

        if not superspreaders:
            logger.info("No superspreaders identified - no interventions needed")
            return interventions

        # Intervention 1: Workload reduction for critical superspreaders
        for provider_id in superspreaders[:3]:  # Top 3 superspreaders
            burnout = self.burnout_scores.get(provider_id, 0.0)

            if burnout >= 0.7:
                intervention = NetworkIntervention(
                    id=uuid4(),
                    intervention_type=InterventionType.WORKLOAD_REDUCTION,
                    priority=1,
                    reason=f"Critical superspreader with burnout={burnout:.2f}",
                    target_providers=[provider_id],
                    estimated_infection_reduction=0.15,
                    estimated_cost=20.0,  # Hours of schedule adjustment
                )
                interventions.append(intervention)

        # Intervention 2: Edge removal for high-burnout pairs
        high_burnout_edges = []
        for edge in self.social_graph.edges():
            source, target = str(edge[0]), str(edge[1])
            source_burnout = self.burnout_scores.get(source, 0.0)
            target_burnout = self.burnout_scores.get(target, 0.0)

            # If both have high burnout, consider removing edge
            if source_burnout >= 0.6 and target_burnout >= 0.6:
                combined_burnout = (source_burnout + target_burnout) / 2
                high_burnout_edges.append((source, target, combined_burnout))

        # Sort by combined burnout
        high_burnout_edges.sort(key=lambda x: x[2], reverse=True)

        for source, target, combined_burnout in high_burnout_edges[:5]:
            intervention = NetworkIntervention(
                id=uuid4(),
                intervention_type=InterventionType.EDGE_REMOVAL,
                priority=2,
                reason=f"High-burnout collaboration (avg={combined_burnout:.2f})",
                target_providers=[source, target],
                affected_edges=[(source, target)],
                estimated_infection_reduction=0.08,
                estimated_cost=10.0,
            )
            interventions.append(intervention)

        # Intervention 3: Quarantine for extreme superspreaders
        for provider_id in superspreaders:
            burnout = self.burnout_scores.get(provider_id, 0.0)

            if burnout >= 0.85:
                degree = self.social_graph.degree(provider_id)
                intervention = NetworkIntervention(
                    id=uuid4(),
                    intervention_type=InterventionType.QUARANTINE,
                    priority=1,
                    reason=f"Extreme burnout ({burnout:.2f}) with {degree} contacts",
                    target_providers=[provider_id],
                    estimated_infection_reduction=0.20,
                    estimated_cost=40.0,  # Significant schedule disruption
                )
                interventions.append(intervention)

        # Sort by priority, then by estimated impact
        interventions.sort(
            key=lambda x: (x.priority, -x.estimated_infection_reduction)
        )

        return interventions[:max_interventions]

    def generate_report(self) -> ContagionReport:
        """
        Generate comprehensive burnout contagion report.

        Returns:
            ContagionReport with full analysis
        """
        if not self.snapshots:
            raise RuntimeError("Must run simulate() before generating report")

        # Get current state
        current_snapshot = self.snapshots[-1]

        # Calculate peak infection
        peak_snapshot = max(self.snapshots, key=lambda s: s.infection_rate)

        # Determine contagion risk
        final_rate = current_snapshot.infection_rate
        if final_rate < 0.10:
            risk = ContagionRisk.LOW
        elif final_rate < 0.25:
            risk = ContagionRisk.MODERATE
        elif final_rate < 0.50:
            risk = ContagionRisk.HIGH
        else:
            risk = ContagionRisk.CRITICAL

        # Get superspreaders
        superspreader_profiles = self.get_superspreader_profiles()

        # Get interventions
        interventions = self.recommend_interventions()

        # Generate warnings
        warnings = []
        if risk in (ContagionRisk.HIGH, ContagionRisk.CRITICAL):
            warnings.append(
                f"ALERT: {risk.value.upper()} contagion risk - "
                f"{final_rate:.1%} of network infected"
            )
        if len(superspreader_profiles) > self.social_graph.number_of_nodes() * 0.15:
            warnings.append(
                f"High superspreader concentration: {len(superspreader_profiles)} identified"
            )
        if peak_snapshot.infection_rate > 0.5:
            warnings.append(
                f"Cascade detected: peak infection rate {peak_snapshot.infection_rate:.1%} "
                f"at iteration {peak_snapshot.iteration}"
            )

        report = ContagionReport(
            generated_at=datetime.now(),
            network_size=self.social_graph.number_of_nodes(),
            current_susceptible=current_snapshot.susceptible_count,
            current_infected=current_snapshot.infected_count,
            current_infection_rate=current_snapshot.infection_rate,
            contagion_risk=risk,
            simulation_iterations=len(self.snapshots),
            final_infection_rate=final_rate,
            peak_infection_rate=peak_snapshot.infection_rate,
            peak_iteration=peak_snapshot.iteration,
            superspreaders=superspreader_profiles,
            total_superspreaders=len(superspreader_profiles),
            recommended_interventions=interventions,
            snapshots=self.snapshots,
            warnings=warnings,
        )

        return report

    def _calculate_centrality(self):
        """Calculate and cache centrality measures for all nodes."""
        logger.info("Calculating network centrality measures...")

        # Calculate different centrality measures
        try:
            degree_cent = nx.degree_centrality(self.social_graph)
        except Exception:
            degree_cent = {}

        try:
            between_cent = nx.betweenness_centrality(self.social_graph)
        except Exception:
            between_cent = {}

        try:
            eigen_cent = nx.eigenvector_centrality(self.social_graph, max_iter=1000)
        except Exception:
            eigen_cent = {}

        # Build cache
        for node_id in self.social_graph.nodes():
            node_id_str = str(node_id)
            self._centrality_cache[node_id_str] = {
                "degree": degree_cent.get(node_id, 0.0),
                "betweenness": between_cent.get(node_id, 0.0),
                "eigenvector": eigen_cent.get(node_id, 0.0),
            }

        logger.info(f"Centrality calculated for {len(self._centrality_cache)} nodes")

    def get_infection_trajectory(self) -> list[tuple[int, float]]:
        """
        Get infection rate trajectory over time.

        Returns:
            List of (iteration, infection_rate) tuples
        """
        return [(s.iteration, s.infection_rate) for s in self.snapshots]

    def get_current_state(self) -> dict[str, Any]:
        """
        Get current simulation state.

        Returns:
            Dict with current state information
        """
        if not self.snapshots:
            return {"error": "No simulation run yet"}

        current = self.snapshots[-1]

        return {
            "iteration": current.iteration,
            "susceptible": current.susceptible_count,
            "infected": current.infected_count,
            "infection_rate": current.infection_rate,
            "mean_burnout": current.mean_burnout_score,
            "max_burnout": current.max_burnout_score,
        }
