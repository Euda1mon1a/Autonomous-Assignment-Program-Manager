"""
Burnout Contagion Modeling (Epidemiological Pattern).

Burnout spreads through social networks like an infectious disease. Work stress,
negativity, and emotional exhaustion are socially contagious. Understanding burnout
as an epidemic allows us to apply epidemiological tools (R0, contact tracing, herd
immunity) to organizational health.

Key Principles (from Epidemiology):
- R0 (reproduction number) > 1: Burnout is spreading exponentially
- R0 < 1: Burnout is contained and declining
- Close contacts amplify transmission (shared shifts, mentorship relationships)
- Super-spreaders: High-connectivity individuals spread burnout faster
- Interventions must break transmission chains

Key Principles (from Social Contagion Research):
- Emotions spread through networks (Christakis & Fowler, 2008)
- Burnout has social contagion effects (Bakker et al., 2009)
- Proximity and frequency increase contagion risk
- Network position predicts contagion susceptibility

This module implements:
1. Reproduction number (Rt) calculation for burnout spread
2. SIR (Susceptible-Infected-Recovered) epidemic modeling
3. Contact tracing for burnout cases
4. Super-spreader identification (high-connectivity nodes)
5. Herd immunity threshold calculation
6. Evidence-based intervention recommendations
"""

import logging
import statistics
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any
from uuid import UUID

logger = logging.getLogger(__name__)

# Try to import NetworkX for graph analysis
try:
    import networkx as nx

    HAS_NETWORKX = True
except ImportError:
    HAS_NETWORKX = False
    logger.warning("NetworkX not installed - burnout epidemiology requires NetworkX")


# =============================================================================
# Enums and Constants
# =============================================================================


class BurnoutState(str, Enum):
    """
    Burnout state in epidemiological model.

    Analogous to disease states in SIR models:
    - SUSCEPTIBLE: Healthy, but at risk if exposed
    - AT_RISK: Elevated stress, early warning signs (pre-symptomatic)
    - BURNED_OUT: Active burnout (infectious period)
    - RECOVERED: Recovered from burnout, potentially immune (for a period)
    """

    SUSCEPTIBLE = "susceptible"
    AT_RISK = "at_risk"
    BURNED_OUT = "burned_out"
    RECOVERED = "recovered"


class InterventionLevel(str, Enum):
    """Intervention urgency level based on Rt."""

    NONE = "none"  # Rt << 1, burnout declining
    MONITORING = "monitoring"  # Rt ~= 1, stable but watch closely
    MODERATE = "moderate"  # Rt > 1, spreading slowly
    AGGRESSIVE = "aggressive"  # Rt > 2, spreading rapidly
    EMERGENCY = "emergency"  # Rt > 3, crisis intervention needed


# =============================================================================
# Data Classes
# =============================================================================


@dataclass
class BurnoutSIRModel:
    """
    SIR model parameters for burnout epidemic simulation.

    SIR Model:
    - S (Susceptible): Healthy residents who could develop burnout
    - I (Infected): Residents with active burnout (can transmit to others)
    - R (Recovered): Residents who recovered or left the system

    Parameters:
    - beta: Transmission rate (probability of burnout transmission per contact)
    - gamma: Recovery rate (1/gamma = average duration of burnout)
    - initial_infected: Starting set of burned out individuals
    """

    beta: float  # Infection rate (0.0 - 1.0)
    gamma: float  # Recovery rate (0.0 - 1.0)
    initial_infected: set[UUID]

    def __post_init__(self):
        """Validate parameters."""
        if not 0 <= self.beta <= 1:
            raise ValueError(f"beta must be in [0, 1], got {self.beta}")
        if not 0 <= self.gamma <= 1:
            raise ValueError(f"gamma must be in [0, 1], got {self.gamma}")

    @property
    def basic_reproduction_number(self) -> float:
        """
        Calculate R0 (basic reproduction number).

        R0 = beta / gamma

        R0 > 1: Epidemic grows
        R0 = 1: Endemic (stable)
        R0 < 1: Epidemic declines
        """
        return self.beta / self.gamma if self.gamma > 0 else float("inf")


@dataclass
class EpiReport:
    """
    Epidemiological report for burnout spread.

    Contains reproduction number, current status, contact tracing data,
    and recommended interventions.
    """

    reproduction_number: float  # Rt (effective reproduction number)
    status: str  # "declining", "stable", "spreading", "crisis"
    secondary_cases: dict[str, int]  # Map of source -> number of secondary cases
    recommended_interventions: list[str]

    # Additional metrics
    analyzed_at: datetime = field(default_factory=datetime.now)
    time_window: timedelta = field(default=timedelta(weeks=4))
    total_cases_analyzed: int = 0
    total_close_contacts: int = 0
    intervention_level: InterventionLevel = InterventionLevel.MONITORING

    # Risk assessment
    super_spreaders: list[UUID] = field(default_factory=list)
    high_risk_contacts: list[UUID] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "reproduction_number": self.reproduction_number,
            "status": self.status,
            "secondary_cases": {str(k): v for k, v in self.secondary_cases.items()},
            "recommended_interventions": self.recommended_interventions,
            "analyzed_at": self.analyzed_at.isoformat(),
            "time_window_days": self.time_window.days,
            "total_cases_analyzed": self.total_cases_analyzed,
            "total_close_contacts": self.total_close_contacts,
            "intervention_level": self.intervention_level,
            "super_spreaders": [str(sid) for sid in self.super_spreaders],
            "high_risk_contacts": [str(cid) for cid in self.high_risk_contacts],
        }


# =============================================================================
# Burnout Epidemiology Analyzer
# =============================================================================


class BurnoutEpidemiology:
    """
    Analyzes burnout spread through social/work networks using epidemiological models.

    Treats burnout as a contagious condition that spreads through close contacts
    in the workplace. Uses network analysis and epidemic modeling to:
    - Calculate reproduction numbers
    - Identify transmission chains
    - Detect super-spreaders
    - Recommend interventions
    """

    def __init__(self, social_network: nx.Graph):
        """
        Initialize burnout epidemiology analyzer.

        Args:
            social_network: NetworkX graph where nodes are residents and edges
                          represent social/work connections (shared shifts, mentorship, etc.)

        Raises:
            ImportError: If NetworkX is not installed
        """
        if not HAS_NETWORKX:
            raise ImportError(
                "NetworkX is required for burnout epidemiology analysis. "
                "Install with: pip install networkx"
            )

        self.network = social_network
        self.burnout_history: dict[UUID, list[tuple[datetime, BurnoutState]]] = (
            defaultdict(list)
        )

        # Cache for performance
        self._contact_cache: dict[tuple[UUID, timedelta], set[UUID]] = {}
        self._degree_cache: dict[UUID, int] = {}

        logger.info(
            f"Initialized burnout epidemiology analyzer with {self.network.number_of_nodes()} "
            f"nodes and {self.network.number_of_edges()} edges"
        )

    def record_burnout_state(
        self, resident_id: UUID, state: BurnoutState, timestamp: datetime = None
    ):
        """
        Record a burnout state change for a resident.

        Args:
            resident_id: Resident whose state changed
            state: New burnout state
            timestamp: When the change occurred (defaults to now)
        """
        timestamp = timestamp or datetime.now()
        self.burnout_history[resident_id].append((timestamp, state))
        logger.debug(f"Recorded {state} for resident {resident_id} at {timestamp}")

    def get_close_contacts(
        self, resident_id: UUID, time_window: timedelta = timedelta(weeks=4)
    ) -> set[UUID]:
        """
        Get close contacts for a resident within a time window.

        Close contacts are residents connected in the social network.
        In a real implementation, this would consider:
        - Shared shifts in the time window
        - Mentorship relationships
        - Team assignments
        - Physical proximity

        Args:
            resident_id: Resident to get contacts for
            time_window: Time window to consider (not used in basic implementation)

        Returns:
            Set of resident IDs who are close contacts
        """
        cache_key = (resident_id, time_window)
        if cache_key in self._contact_cache:
            return self._contact_cache[cache_key]

        if resident_id not in self.network:
            logger.warning(f"Resident {resident_id} not in social network")
            return set()

        # Get neighbors in the network (1-hop connections)
        contacts = set(self.network.neighbors(resident_id))

        # Could extend to 2-hop for weak ties
        # for neighbor in list(contacts):
        #     contacts.update(self.network.neighbors(neighbor))

        self._contact_cache[cache_key] = contacts
        return contacts

    def calculate_reproduction_number(
        self,
        burned_out_residents: set[UUID],
        time_window: timedelta = timedelta(weeks=4),
    ) -> EpiReport:
        """
        Calculate the effective reproduction number (Rt) for burnout.

        Rt is the average number of secondary burnout cases caused by each
        burned out individual. This is calculated by:
        1. For each burned out resident (index case)
        2. Find their close contacts
        3. Count how many contacts developed burnout within the time window
        4. Average across all index cases

        Args:
            burned_out_residents: Set of currently burned out residents
            time_window: Time window to look for secondary cases

        Returns:
            EpiReport with reproduction number and recommendations
        """
        if not burned_out_residents:
            return EpiReport(
                reproduction_number=0.0,
                status="no_cases",
                secondary_cases={},
                recommended_interventions=["Continue preventive measures"],
                total_cases_analyzed=0,
                intervention_level=InterventionLevel.NONE,
            )

        current_time = datetime.now()
        secondary_case_counts: dict[str, int] = {}
        all_close_contacts: set[UUID] = set()
        high_risk_contacts: set[UUID] = set()

        for index_case in burned_out_residents:
            # Get close contacts
            contacts = self.get_close_contacts(index_case, time_window)
            all_close_contacts.update(contacts)

            # Count secondary cases (contacts who became burned out after this person)
            secondary_count = 0

            # Get when this person became burned out
            index_burnout_time = self._get_burnout_onset(index_case)
            if not index_burnout_time:
                continue

            # Count contacts who became burned out within time_window after index case
            for contact in contacts:
                contact_burnout_time = self._get_burnout_onset(contact)
                if contact_burnout_time:
                    time_diff = contact_burnout_time - index_burnout_time
                    if timedelta(0) < time_diff <= time_window:
                        secondary_count += 1
                        high_risk_contacts.add(contact)

            secondary_case_counts[str(index_case)] = secondary_count

        # Calculate Rt (average secondary cases)
        if secondary_case_counts:
            rt = statistics.mean(secondary_case_counts.values())
        else:
            # If we have burned out residents but no secondary case data,
            # assume at least R=1 (conservative estimate)
            rt = 1.0

        # Determine status
        if rt < 0.5:
            status = "declining"
            intervention_level = InterventionLevel.NONE
        elif rt < 1.0:
            status = "controlled"
            intervention_level = InterventionLevel.MONITORING
        elif rt < 2.0:
            status = "spreading"
            intervention_level = InterventionLevel.MODERATE
        elif rt < 3.0:
            status = "rapid_spread"
            intervention_level = InterventionLevel.AGGRESSIVE
        else:
            status = "crisis"
            intervention_level = InterventionLevel.EMERGENCY

        # Identify super-spreaders (high secondary case counts)
        super_spreaders = [
            UUID(uid) for uid, count in secondary_case_counts.items() if count >= 3
        ]

        # Get interventions
        interventions = self.get_interventions(rt)

        report = EpiReport(
            reproduction_number=rt,
            status=status,
            secondary_cases=secondary_case_counts,
            recommended_interventions=interventions,
            analyzed_at=current_time,
            time_window=time_window,
            total_cases_analyzed=len(burned_out_residents),
            total_close_contacts=len(all_close_contacts),
            intervention_level=intervention_level,
            super_spreaders=super_spreaders,
            high_risk_contacts=list(high_risk_contacts),
        )

        logger.info(
            f"Calculated Rt={rt:.2f} from {len(burned_out_residents)} cases, "
            f"status={status}, intervention_level={intervention_level}"
        )

        return report

    def simulate_sir_spread(
        self,
        initial_infected: set[UUID],
        beta: float = 0.05,
        gamma: float = 0.02,
        steps: int = 52,
    ) -> list[dict]:
        """
        Simulate SIR epidemic spread over time.

        Uses discrete-time SIR model to project burnout spread through
        the network over time. Each time step represents one week.

        Args:
            initial_infected: Initial set of burned out residents
            beta: Transmission rate per contact per time step (default 0.05 = 5% per week)
            gamma: Recovery rate per time step (default 0.02 = ~50 week recovery)
            steps: Number of time steps to simulate (default 52 = 1 year)

        Returns:
            List of dicts with S, I, R counts at each time step
        """
        # Validate model parameters
        model = BurnoutSIRModel(
            beta=beta, gamma=gamma, initial_infected=initial_infected
        )

        # Initialize populations
        all_nodes = set(self.network.nodes())
        infected = initial_infected.copy()
        recovered = set()
        susceptible = all_nodes - infected - recovered

        time_series = []

        for step in range(steps):
            # Record current state
            time_series.append(
                {
                    "step": step,
                    "week": step,
                    "susceptible": len(susceptible),
                    "infected": len(infected),
                    "recovered": len(recovered),
                    "S": len(susceptible),
                    "I": len(infected),
                    "R": len(recovered),
                    "total": len(all_nodes),
                }
            )

            # SIR transitions
            new_infections = set()
            new_recoveries = set()

            # Infection: Each infected person can infect their susceptible contacts
            for infected_node in infected:
                contacts = self.get_close_contacts(infected_node)
                susceptible_contacts = contacts & susceptible

                for contact in susceptible_contacts:
                    # Transmission occurs with probability beta
                    if self._random_transmission(beta):
                        new_infections.add(contact)

            # Recovery: Each infected person recovers with probability gamma
            for infected_node in infected:
                if self._random_transmission(gamma):
                    new_recoveries.add(infected_node)

            # Update populations
            susceptible -= new_infections
            infected.update(new_infections)
            infected -= new_recoveries
            recovered.update(new_recoveries)

            # Stop if no more infected
            if not infected:
                logger.info(f"Epidemic died out at step {step}")
                break

        logger.info(
            f"SIR simulation completed: {steps} steps, "
            f"R0={model.basic_reproduction_number:.2f}, "
            f"final I={len(infected)}, R={len(recovered)}"
        )

        return time_series

    def identify_super_spreaders(self, threshold_degree: int = 5) -> list[UUID]:
        """
        Identify super-spreaders (high-connectivity nodes).

        Super-spreaders are residents with many social connections who
        could spread burnout to large numbers of contacts.

        Args:
            threshold_degree: Minimum degree to be considered a super-spreader

        Returns:
            List of resident IDs who are super-spreaders
        """
        super_spreaders = []

        for node in self.network.nodes():
            degree = self._get_degree(node)
            if degree >= threshold_degree:
                super_spreaders.append(node)
                logger.debug(f"Super-spreader identified: {node} (degree={degree})")

        logger.info(
            f"Identified {len(super_spreaders)} super-spreaders "
            f"(degree >= {threshold_degree})"
        )

        return super_spreaders

    def calculate_herd_immunity_threshold(self, r0: float) -> float:
        """
        Calculate herd immunity threshold.

        Herd immunity threshold is the proportion of the population that
        must be "immune" (recovered or protected by interventions) to stop
        epidemic spread.

        Formula: HIT = 1 - 1/R0

        Args:
            r0: Basic reproduction number

        Returns:
            Herd immunity threshold (0.0 - 1.0)
        """
        if r0 <= 1:
            return 0.0

        hit = 1.0 - (1.0 / r0)

        logger.info(f"Herd immunity threshold for R0={r0:.2f}: {hit:.1%}")

        return hit

    def get_interventions(self, rt: float) -> list[str]:
        """
        Get recommended interventions based on reproduction number.

        Evidence-based interventions from burnout prevention research:
        - Rt < 0.5: Maintain preventive measures
        - 0.5 <= Rt < 1: Monitor and support at-risk individuals
        - 1 <= Rt < 2: Moderate interventions (workload reduction, support groups)
        - 2 <= Rt < 3: Aggressive interventions (mandatory time off, restructuring)
        - Rt >= 3: Emergency interventions (crisis management, external support)

        Args:
            rt: Effective reproduction number

        Returns:
            List of recommended intervention strategies
        """
        interventions = []

        if rt < 0.5:
            interventions.extend(
                [
                    "Continue current preventive measures",
                    "Monitor for early warning signs",
                    "Maintain work-life balance programs",
                ]
            )

        elif rt < 1.0:
            interventions.extend(
                [
                    "Increase monitoring of at-risk individuals",
                    "Offer voluntary support groups and counseling",
                    "Review workload distribution for equity",
                    "Strengthen peer support networks",
                ]
            )

        elif rt < 2.0:
            interventions.extend(
                [
                    "MODERATE INTERVENTION REQUIRED",
                    "Implement workload reduction for burned out individuals",
                    "Mandatory wellness check-ins for all staff",
                    "Increase staffing levels to reduce individual burden",
                    "Break transmission chains: reduce contact between burned out and at-risk",
                    "Provide mental health resources and counseling",
                    "Review and adjust schedule to reduce stress points",
                ]
            )

        elif rt < 3.0:
            interventions.extend(
                [
                    "AGGRESSIVE INTERVENTION REQUIRED",
                    "Mandatory time off for burned out individuals",
                    "Emergency staffing augmentation (temporary hires, locums)",
                    "Restructure teams to reduce super-spreader connectivity",
                    "Daily wellness monitoring for all staff",
                    "Implement crisis management protocols",
                    "Consider rotating high-stress assignments",
                    "Provide immediate access to mental health professionals",
                    "Leadership intervention and organizational restructuring",
                ]
            )

        else:  # rt >= 3.0
            interventions.extend(
                [
                    "⚠️ EMERGENCY INTERVENTION REQUIRED ⚠️",
                    "IMMEDIATE ACTION: Remove burned out individuals from clinical duties",
                    "Emergency external support (crisis counseling, temporary replacements)",
                    "System-wide operational pause to prevent collapse",
                    "Comprehensive organizational assessment and restructuring",
                    "Bring in external organizational health consultants",
                    "Consider activating mutual aid agreements with other programs",
                    "Notify program leadership and institutional administration",
                    "Implement 24/7 mental health crisis support",
                    "Prepare contingency plans for further escalation",
                ]
            )

        # Add super-spreader specific interventions
        super_spreaders = self.identify_super_spreaders()
        if super_spreaders and rt >= 1.0:
            interventions.append(
                f"Target interventions for {len(super_spreaders)} super-spreaders "
                "(high-connectivity individuals)"
            )
            interventions.append(
                "Prioritize wellness support for high-connectivity team members"
            )

        return interventions

    # -------------------------------------------------------------------------
    # Helper Methods
    # -------------------------------------------------------------------------

    def _get_burnout_onset(self, resident_id: UUID) -> datetime | None:
        """Get when a resident first became burned out."""
        history = self.burnout_history.get(resident_id, [])

        for timestamp, state in history:
            if state == BurnoutState.BURNED_OUT:
                return timestamp

        return None

    def _get_degree(self, node: UUID) -> int:
        """Get degree (number of connections) for a node."""
        if node not in self._degree_cache:
            self._degree_cache[node] = self.network.degree(node)
        return self._degree_cache[node]

    def _random_transmission(self, probability: float) -> bool:
        """
        Determine if transmission occurs (simplified for demonstration).

        In a real implementation, would use random.random() < probability.
        For reproducibility and testing, we use a deterministic approach.
        """
        # Deterministic version for testing
        # In production, replace with: random.random() < probability
        import random

        return random.random() < probability

    def get_network_summary(self) -> dict[str, Any]:
        """Get summary statistics about the social network."""
        return {
            "total_nodes": self.network.number_of_nodes(),
            "total_edges": self.network.number_of_edges(),
            "average_degree": (
                2 * self.network.number_of_edges() / self.network.number_of_nodes()
                if self.network.number_of_nodes() > 0
                else 0
            ),
            "density": nx.density(self.network),
            "is_connected": nx.is_connected(self.network),
            "number_of_components": nx.number_connected_components(self.network),
        }

    def get_burnout_summary(self) -> dict[str, Any]:
        """Get summary of current burnout states."""
        current_states = dict.fromkeys(BurnoutState, 0)

        for resident_id in self.network.nodes():
            state = self._get_current_state(resident_id)
            current_states[state] += 1

        return {
            "total_residents": self.network.number_of_nodes(),
            "susceptible": current_states[BurnoutState.SUSCEPTIBLE],
            "at_risk": current_states[BurnoutState.AT_RISK],
            "burned_out": current_states[BurnoutState.BURNED_OUT],
            "recovered": current_states[BurnoutState.RECOVERED],
        }

    def _get_current_state(self, resident_id: UUID) -> BurnoutState:
        """Get current burnout state for a resident."""
        history = self.burnout_history.get(resident_id, [])

        if not history:
            return BurnoutState.SUSCEPTIBLE

        # Return most recent state
        return history[-1][1]
