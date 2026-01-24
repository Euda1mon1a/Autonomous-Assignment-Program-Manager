"""
Unified Critical Faculty Index (Novel Cross-Domain Integration).

This module implements a novel approach to resilience by recognizing that three
separate systems independently identify "critical" individuals:

1. N-1/N-2 Contingency Analysis - Faculty whose loss causes cascade failures
2. Burnout Epidemiology - Super-spreaders with high network connectivity
3. Hub Analysis - High centrality nodes in the assignment graph

These are mathematically the SAME CONCEPT expressed in different domains.
This module unifies them into a single Critical Faculty Index (CFI).

Key Insights:
- A faculty member who is N-1 vulnerable, a super-spreader, AND a hub
  represents the highest concentration of organizational risk
- Cross-validation between domains reveals hidden patterns:
  * High hub score + low epidemiology risk = isolated workaholic (different intervention)
  * High epidemiology + low hub = social connector (burnout spreads but schedule survives)
  * All three high = critical intervention needed immediately
- Single computation of network graph serves all three systems (efficiency)

Novel Contributions:
1. Cross-domain risk aggregation with conflict detection
2. Intervention priority matrix based on which domains signal "critical"
3. Leading indicator synthesis from all three systems
4. Unified dashboard metric for "faculty risk concentration"
"""

import logging
import statistics
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Optional
from uuid import UUID

logger = logging.getLogger(__name__)

# Try to import NetworkX for graph analysis
try:
    import networkx as nx

    HAS_NETWORKX = True
except ImportError:
    HAS_NETWORKX = False
    logger.warning("NetworkX not installed - unified critical index requires NetworkX")


class CriticalityDomain(str, Enum):
    """The three domains that independently identify critical faculty."""

    CONTINGENCY = "contingency"  # N-1/N-2 vulnerability
    EPIDEMIOLOGY = "epidemiology"  # Burnout super-spreader potential
    HUB_ANALYSIS = "hub_analysis"  # Network centrality


class RiskPattern(str, Enum):
    """
    Patterns identified by cross-domain analysis.

    Different combinations of high scores suggest different interventions.
    """

    # All three domains high - maximum risk
    UNIVERSAL_CRITICAL = "universal_critical"

    # Two domains high
    STRUCTURAL_BURNOUT = "structural_burnout"  # Contingency + Epidemiology
    INFLUENTIAL_HUB = "influential_hub"  # Contingency + Hub
    SOCIAL_CONNECTOR = "social_connector"  # Epidemiology + Hub

    # Single domain high
    ISOLATED_WORKHORSE = "isolated_workhorse"  # Contingency only
    BURNOUT_VECTOR = "burnout_vector"  # Epidemiology only
    NETWORK_ANCHOR = "network_anchor"  # Hub only

    # No domains high
    LOW_RISK = "low_risk"


class InterventionType(str, Enum):
    """Recommended intervention types based on risk pattern."""

    IMMEDIATE_PROTECTION = "immediate_protection"  # Universal critical
    CROSS_TRAINING = "cross_training"  # Structural/Hub risks
    WORKLOAD_REDUCTION = "workload_reduction"  # Burnout-related patterns
    NETWORK_DIVERSIFICATION = "network_diversification"  # Hub-related patterns
    MONITORING = "monitoring"  # Low risk, continue observation
    WELLNESS_SUPPORT = "wellness_support"  # Epidemiology-related patterns


@dataclass
class DomainScore:
    """Score from a single domain with metadata."""

    domain: CriticalityDomain
    raw_score: float  # 0.0 to 1.0
    normalized_score: float = 0.0  # After population normalization
    percentile: float = 0.0  # Where this score falls in population
    is_critical: bool = False  # Above critical threshold
    details: dict = field(default_factory=dict)

    @property
    def threshold_exceeded(self) -> bool:
        """Whether this domain considers the faculty critical."""
        return self.normalized_score >= 0.7 or self.is_critical


@dataclass
class UnifiedCriticalIndex:
    """
    The unified critical faculty index combining all three domains.

    This is the primary output of the analysis - a single, comprehensive
    view of faculty criticality that synthesizes multiple perspectives.
    """

    faculty_id: UUID
    faculty_name: str
    calculated_at: datetime

    # Domain-specific scores
    contingency_score: DomainScore
    epidemiology_score: DomainScore
    hub_score: DomainScore

    # Unified metrics
    composite_index: float = 0.0  # 0.0 to 1.0, weighted combination
    risk_pattern: RiskPattern = RiskPattern.LOW_RISK
    confidence: float = 0.0  # 0.0 to 1.0, based on data quality

    # Cross-domain insights
    domain_agreement: float = (
        0.0  # How much domains agree (0 = conflict, 1 = consensus)
    )
    leading_domain: CriticalityDomain | None = None  # Which domain signals first
    conflict_details: list[str] = field(default_factory=list)

    # Actionable outputs
    recommended_interventions: list[InterventionType] = field(default_factory=list)
    priority_rank: int = 0  # 1 = highest priority across population

    def __post_init__(self) -> None:
        """Calculate derived fields."""
        self._calculate_composite()
        self._identify_pattern()
        self._calculate_agreement()
        self._recommend_interventions()

    def _calculate_composite(self) -> None:
        """
        Calculate weighted composite index.

        Weights are calibrated based on intervention urgency:
        - Contingency (0.4): Schedule collapse is immediate operational failure
        - Hub (0.35): Network position affects recovery options
        - Epidemiology (0.25): Burnout spread is slower but insidious
        """
        weights = {
            CriticalityDomain.CONTINGENCY: 0.40,
            CriticalityDomain.HUB_ANALYSIS: 0.35,
            CriticalityDomain.EPIDEMIOLOGY: 0.25,
        }

        self.composite_index = (
            self.contingency_score.normalized_score
            * weights[CriticalityDomain.CONTINGENCY]
            + self.hub_score.normalized_score * weights[CriticalityDomain.HUB_ANALYSIS]
            + self.epidemiology_score.normalized_score
            * weights[CriticalityDomain.EPIDEMIOLOGY]
        )

    def _identify_pattern(self) -> None:
        """Identify the risk pattern based on which domains are critical."""
        critical_domains = []

        if self.contingency_score.threshold_exceeded:
            critical_domains.append(CriticalityDomain.CONTINGENCY)
        if self.epidemiology_score.threshold_exceeded:
            critical_domains.append(CriticalityDomain.EPIDEMIOLOGY)
        if self.hub_score.threshold_exceeded:
            critical_domains.append(CriticalityDomain.HUB_ANALYSIS)

        # Map combination to pattern
        pattern_map = {
            frozenset(): RiskPattern.LOW_RISK,
            frozenset([CriticalityDomain.CONTINGENCY]): RiskPattern.ISOLATED_WORKHORSE,
            frozenset([CriticalityDomain.EPIDEMIOLOGY]): RiskPattern.BURNOUT_VECTOR,
            frozenset([CriticalityDomain.HUB_ANALYSIS]): RiskPattern.NETWORK_ANCHOR,
            frozenset(
                [CriticalityDomain.CONTINGENCY, CriticalityDomain.EPIDEMIOLOGY]
            ): RiskPattern.STRUCTURAL_BURNOUT,
            frozenset(
                [CriticalityDomain.CONTINGENCY, CriticalityDomain.HUB_ANALYSIS]
            ): RiskPattern.INFLUENTIAL_HUB,
            frozenset(
                [CriticalityDomain.EPIDEMIOLOGY, CriticalityDomain.HUB_ANALYSIS]
            ): RiskPattern.SOCIAL_CONNECTOR,
            frozenset(
                [
                    CriticalityDomain.CONTINGENCY,
                    CriticalityDomain.EPIDEMIOLOGY,
                    CriticalityDomain.HUB_ANALYSIS,
                ]
            ): RiskPattern.UNIVERSAL_CRITICAL,
        }

        self.risk_pattern = pattern_map.get(
            frozenset(critical_domains), RiskPattern.LOW_RISK
        )

        # Identify leading domain (highest normalized score)
        scores = [
            (CriticalityDomain.CONTINGENCY, self.contingency_score.normalized_score),
            (CriticalityDomain.EPIDEMIOLOGY, self.epidemiology_score.normalized_score),
            (CriticalityDomain.HUB_ANALYSIS, self.hub_score.normalized_score),
        ]
        self.leading_domain = max(scores, key=lambda x: x[1])[0]

    def _calculate_agreement(self) -> None:
        """
        Calculate how much the three domains agree.

        High agreement = all domains give similar scores (consensus)
        Low agreement = domains disagree (investigate why)
        """
        scores = [
            self.contingency_score.normalized_score,
            self.epidemiology_score.normalized_score,
            self.hub_score.normalized_score,
        ]

        # Agreement = 1 - coefficient of variation
        if len(scores) >= 2 and statistics.mean(scores) > 0:
            cv = statistics.stdev(scores) / statistics.mean(scores)
            self.domain_agreement = max(0.0, 1.0 - cv)
        else:
            self.domain_agreement = 1.0

        # Detect conflicts (disagreement cases worth investigating)
        self.conflict_details = []

        # Case 1: High hub but low epidemiology - isolated workaholic
        if (
            self.hub_score.normalized_score > 0.7
            and self.epidemiology_score.normalized_score < 0.3
        ):
            self.conflict_details.append(
                "High centrality but low social transmission risk - "
                "may be isolated or have strong personal boundaries"
            )

        # Case 2: High epidemiology but low contingency - social but not critical
        if (
            self.epidemiology_score.normalized_score > 0.7
            and self.contingency_score.normalized_score < 0.3
        ):
            self.conflict_details.append(
                "High burnout spread potential but schedule can survive their loss - "
                "focus on wellness rather than coverage"
            )

        # Case 3: All scores similar - true consensus (not a conflict)
        if self.domain_agreement > 0.8:
            self.conflict_details.append(
                "Strong domain consensus - high confidence in assessment"
            )

    def _recommend_interventions(self) -> None:
        """Recommend interventions based on risk pattern."""
        intervention_map = {
            RiskPattern.UNIVERSAL_CRITICAL: [
                InterventionType.IMMEDIATE_PROTECTION,
                InterventionType.CROSS_TRAINING,
                InterventionType.WORKLOAD_REDUCTION,
            ],
            RiskPattern.STRUCTURAL_BURNOUT: [
                InterventionType.WORKLOAD_REDUCTION,
                InterventionType.CROSS_TRAINING,
                InterventionType.WELLNESS_SUPPORT,
            ],
            RiskPattern.INFLUENTIAL_HUB: [
                InterventionType.CROSS_TRAINING,
                InterventionType.NETWORK_DIVERSIFICATION,
            ],
            RiskPattern.SOCIAL_CONNECTOR: [
                InterventionType.WELLNESS_SUPPORT,
                InterventionType.NETWORK_DIVERSIFICATION,
            ],
            RiskPattern.ISOLATED_WORKHORSE: [
                InterventionType.CROSS_TRAINING,
            ],
            RiskPattern.BURNOUT_VECTOR: [
                InterventionType.WELLNESS_SUPPORT,
                InterventionType.WORKLOAD_REDUCTION,
            ],
            RiskPattern.NETWORK_ANCHOR: [
                InterventionType.NETWORK_DIVERSIFICATION,
            ],
            RiskPattern.LOW_RISK: [
                InterventionType.MONITORING,
            ],
        }

        self.recommended_interventions = intervention_map.get(
            self.risk_pattern, [InterventionType.MONITORING]
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "faculty_id": str(self.faculty_id),
            "faculty_name": self.faculty_name,
            "calculated_at": self.calculated_at.isoformat(),
            "composite_index": round(self.composite_index, 4),
            "risk_pattern": self.risk_pattern.value,
            "domain_scores": {
                "contingency": {
                    "raw": round(self.contingency_score.raw_score, 4),
                    "normalized": round(self.contingency_score.normalized_score, 4),
                    "percentile": round(self.contingency_score.percentile, 2),
                    "is_critical": self.contingency_score.is_critical,
                },
                "epidemiology": {
                    "raw": round(self.epidemiology_score.raw_score, 4),
                    "normalized": round(self.epidemiology_score.normalized_score, 4),
                    "percentile": round(self.epidemiology_score.percentile, 2),
                    "is_critical": self.epidemiology_score.is_critical,
                },
                "hub_analysis": {
                    "raw": round(self.hub_score.raw_score, 4),
                    "normalized": round(self.hub_score.normalized_score, 4),
                    "percentile": round(self.hub_score.percentile, 2),
                    "is_critical": self.hub_score.is_critical,
                },
            },
            "domain_agreement": round(self.domain_agreement, 4),
            "leading_domain": self.leading_domain.value
            if self.leading_domain
            else None,
            "conflict_details": self.conflict_details,
            "recommended_interventions": [
                i.value for i in self.recommended_interventions
            ],
            "priority_rank": self.priority_rank,
            "confidence": round(self.confidence, 4),
        }


@dataclass
class PopulationAnalysis:
    """Analysis results for an entire faculty population."""

    analyzed_at: datetime
    total_faculty: int
    indices: list[UnifiedCriticalIndex]

    # Population-level metrics
    risk_concentration: float = 0.0  # Gini coefficient of risk
    critical_count: int = 0
    universal_critical_count: int = 0

    # Distribution by pattern
    pattern_distribution: dict[RiskPattern, int] = field(default_factory=dict)

    # Top risks
    top_priority: list[UUID] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Calculate population-level metrics."""
        self._calculate_concentration()
        self._calculate_distribution()
        self._rank_priorities()

    def _calculate_concentration(self) -> None:
        """
        Calculate risk concentration using Gini coefficient.

        High Gini = risk concentrated in few faculty (dangerous)
        Low Gini = risk distributed evenly (resilient)
        """
        if not self.indices:
            return

        scores = sorted([idx.composite_index for idx in self.indices])
        n = len(scores)

        if n == 0 or sum(scores) == 0:
            self.risk_concentration = 0.0
            return

        # Gini coefficient calculation
        cumulative = 0.0
        for i, score in enumerate(scores):
            cumulative += (2 * (i + 1) - n - 1) * score

        self.risk_concentration = cumulative / (n * sum(scores))

    def _calculate_distribution(self) -> None:
        """Calculate distribution of risk patterns."""
        self.pattern_distribution = {}
        for pattern in RiskPattern:
            self.pattern_distribution[pattern] = 0

        for idx in self.indices:
            self.pattern_distribution[idx.risk_pattern] += 1

        self.critical_count = sum(
            1 for idx in self.indices if idx.risk_pattern != RiskPattern.LOW_RISK
        )
        self.universal_critical_count = self.pattern_distribution.get(
            RiskPattern.UNIVERSAL_CRITICAL, 0
        )

    def _rank_priorities(self) -> None:
        """Rank faculty by intervention priority."""
        # Sort by composite index descending
        sorted_indices = sorted(
            self.indices, key=lambda x: x.composite_index, reverse=True
        )

        for rank, idx in enumerate(sorted_indices, 1):
            idx.priority_rank = rank

        # Top priority = top 20% or universal critical
        threshold = max(1, len(sorted_indices) // 5)
        self.top_priority = [idx.faculty_id for idx in sorted_indices[:threshold]]

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "analyzed_at": self.analyzed_at.isoformat(),
            "total_faculty": self.total_faculty,
            "risk_concentration": round(self.risk_concentration, 4),
            "critical_count": self.critical_count,
            "universal_critical_count": self.universal_critical_count,
            "pattern_distribution": {
                k.value: v for k, v in self.pattern_distribution.items()
            },
            "top_priority": [str(fid) for fid in self.top_priority],
            "indices": [idx.to_dict() for idx in self.indices],
        }


class UnifiedCriticalIndexAnalyzer:
    """
    Analyzer that computes the Unified Critical Faculty Index.

    This is the main entry point for the unified analysis. It:
    1. Builds a shared network graph (efficiency)
    2. Computes domain-specific scores using existing modules
    3. Synthesizes into unified indices
    4. Provides population-level analysis
    """

    def __init__(
        self,
        contingency_weight: float = 0.40,
        hub_weight: float = 0.35,
        epidemiology_weight: float = 0.25,
    ):
        """
        Initialize the unified analyzer.

        Args:
            contingency_weight: Weight for N-1/N-2 vulnerability scores
            hub_weight: Weight for network centrality scores
            epidemiology_weight: Weight for burnout transmission scores
        """
        if not HAS_NETWORKX:
            raise ImportError(
                "NetworkX is required for unified critical index analysis. "
                "Install with: pip install networkx"
            )

        self.weights = {
            CriticalityDomain.CONTINGENCY: contingency_weight,
            CriticalityDomain.HUB_ANALYSIS: hub_weight,
            CriticalityDomain.EPIDEMIOLOGY: epidemiology_weight,
        }

        # Validate weights sum to 1
        if abs(sum(self.weights.values()) - 1.0) > 0.01:
            raise ValueError("Domain weights must sum to 1.0")

        self._network: nx.Graph | None = None
        self._centrality_cache: dict[UUID, dict] = {}

        logger.info(
            f"Initialized unified critical index analyzer with weights: {self.weights}"
        )

    def build_network(
        self,
        faculty: list,
        assignments: list,
        shared_shift_threshold: int = 3,
    ) -> nx.Graph:
        """
        Build a shared network graph for all analyses.

        Nodes are faculty members. Edges represent working relationships
        based on shared assignments (shifts worked together).

        Args:
            faculty: List of faculty members (need id, name attributes)
            assignments: List of assignments (need person_id, block_id)
            shared_shift_threshold: Minimum shared shifts to create an edge

        Returns:
            NetworkX graph representing faculty network
        """
        self._network = nx.Graph()

        # Add all faculty as nodes
        for fac in faculty:
            self._network.add_node(
                fac.id,
                name=getattr(fac, "name", str(fac.id)),
            )

        # Build edge weights from shared assignments
        # Group assignments by block
        blocks_to_faculty: dict[UUID, set[UUID]] = {}
        for assignment in assignments:
            if assignment.block_id not in blocks_to_faculty:
                blocks_to_faculty[assignment.block_id] = set()
            blocks_to_faculty[assignment.block_id].add(assignment.person_id)

        # Count shared shifts between pairs
        shared_shifts: dict[tuple[UUID, UUID], int] = {}
        for block_id, faculty_set in blocks_to_faculty.items():
            faculty_list = list(faculty_set)
            for i, fac1 in enumerate(faculty_list):
                for fac2 in faculty_list[i + 1 :]:
                    pair = tuple(sorted([fac1, fac2]))
                    shared_shifts[pair] = shared_shifts.get(pair, 0) + 1

        # Add edges above threshold
        for (fac1, fac2), count in shared_shifts.items():
            if count >= shared_shift_threshold:
                self._network.add_edge(
                    fac1, fac2, weight=count, relationship="shared_shifts"
                )

        logger.info(
            f"Built network with {self._network.number_of_nodes()} nodes "
            f"and {self._network.number_of_edges()} edges"
        )

        # Pre-compute centrality metrics (expensive, do once)
        self._compute_centrality_metrics()

        return self._network

    def _compute_centrality_metrics(self) -> None:
        """Pre-compute all centrality metrics for the network."""
        if not self._network or self._network.number_of_nodes() == 0:
            return

        self._centrality_cache = {}

        # Compute various centrality measures
        try:
            degree = nx.degree_centrality(self._network)
            betweenness = nx.betweenness_centrality(self._network)
            # Eigenvector may fail for disconnected graphs
            try:
                eigenvector = nx.eigenvector_centrality(
                    self._network, max_iter=1000, tol=1e-06
                )
            except nx.PowerIterationFailedConvergence:
                eigenvector = dict.fromkeys(self._network.nodes(), 0.0)
            pagerank = nx.pagerank(self._network)

            for node in self._network.nodes():
                self._centrality_cache[node] = {
                    "degree": degree.get(node, 0.0),
                    "betweenness": betweenness.get(node, 0.0),
                    "eigenvector": eigenvector.get(node, 0.0),
                    "pagerank": pagerank.get(node, 0.0),
                }

            logger.debug(
                f"Computed centrality metrics for {len(self._centrality_cache)} nodes"
            )

        except Exception as e:
            logger.warning(f"Error computing centrality metrics: {e}")

    def compute_contingency_score(
        self,
        faculty_id: UUID,
        assignments: list,
        coverage_requirements: dict[UUID, int],
    ) -> DomainScore:
        """
        Compute contingency (N-1/N-2) vulnerability score for a faculty member.

        Args:
            faculty_id: Faculty member to analyze
            assignments: All assignments in the period
            coverage_requirements: Block ID -> required coverage count

        Returns:
            DomainScore with contingency vulnerability
        """
        # Get assignments for this faculty member
        faculty_assignments = [a for a in assignments if a.person_id == faculty_id]

        # Count blocks where this faculty is the sole provider
        sole_provider_blocks = 0
        critical_blocks = 0

        # Group assignments by block
        block_faculty: dict[UUID, set[UUID]] = {}
        for assignment in assignments:
            if assignment.block_id not in block_faculty:
                block_faculty[assignment.block_id] = set()
            block_faculty[assignment.block_id].add(assignment.person_id)

        for assignment in faculty_assignments:
            block_id = assignment.block_id
            faculty_on_block = block_faculty.get(block_id, set())
            required = coverage_requirements.get(block_id, 1)

            # Sole provider: only this faculty on the block
            if len(faculty_on_block) == 1:
                sole_provider_blocks += 1

            # Critical: removing this faculty drops below requirement
            if len(faculty_on_block) <= required:
                critical_blocks += 1

        # Calculate raw score
        total_blocks = len(set(a.block_id for a in faculty_assignments))
        if total_blocks == 0:
            raw_score = 0.0
        else:
            # Weight sole provider heavily, critical blocks moderately
            raw_score = min(
                1.0,
                (sole_provider_blocks * 0.3 + critical_blocks * 0.1)
                / max(1, total_blocks),
            )

        is_critical = sole_provider_blocks > 0

        return DomainScore(
            domain=CriticalityDomain.CONTINGENCY,
            raw_score=raw_score,
            normalized_score=raw_score,  # Will be normalized at population level
            is_critical=is_critical,
            details={
                "sole_provider_blocks": sole_provider_blocks,
                "critical_blocks": critical_blocks,
                "total_assigned_blocks": total_blocks,
            },
        )

    def compute_epidemiology_score(
        self,
        faculty_id: UUID,
        burnout_states: dict[UUID, str] | None = None,
    ) -> DomainScore:
        """
        Compute epidemiology (burnout transmission) score for a faculty member.

        Higher score = more likely to spread burnout through the network.

        Args:
            faculty_id: Faculty member to analyze
            burnout_states: Optional dict of faculty_id -> burnout state

        Returns:
            DomainScore with epidemiology risk
        """
        if not self._network or faculty_id not in self._network:
            return DomainScore(
                domain=CriticalityDomain.EPIDEMIOLOGY,
                raw_score=0.0,
                is_critical=False,
            )

        # Factors that increase transmission potential:
        # 1. Degree (number of connections) - more contacts = more transmission
        # 2. Betweenness (bridge between groups) - can spread across clusters
        # 3. Current burnout state (if provided) - already infected

        centrality = self._centrality_cache.get(faculty_id, {})
        degree = centrality.get("degree", 0.0)
        betweenness = centrality.get("betweenness", 0.0)

        # Check current burnout state
        is_burned_out = False
        if burnout_states:
            state = burnout_states.get(faculty_id, "susceptible")
            is_burned_out = state in ["burned_out", "at_risk"]

        # Raw score combines network position with current state
        raw_score = degree * 0.4 + betweenness * 0.4
        if is_burned_out:
            raw_score = min(1.0, raw_score * 1.5)  # Amplify if already burned out

        # Critical if high degree and currently burning out
        is_critical = degree > 0.5 and is_burned_out

        return DomainScore(
            domain=CriticalityDomain.EPIDEMIOLOGY,
            raw_score=raw_score,
            normalized_score=raw_score,  # Will be normalized at population level
            is_critical=is_critical,
            details={
                "degree_centrality": degree,
                "betweenness_centrality": betweenness,
                "is_burned_out": is_burned_out,
            },
        )

    def compute_hub_score(self, faculty_id: UUID) -> DomainScore:
        """
        Compute hub analysis score for a faculty member.

        Higher score = more central/important in the network.

        Args:
            faculty_id: Faculty member to analyze

        Returns:
            DomainScore with hub centrality
        """
        if not self._network or faculty_id not in self._network:
            return DomainScore(
                domain=CriticalityDomain.HUB_ANALYSIS,
                raw_score=0.0,
                is_critical=False,
            )

        centrality = self._centrality_cache.get(faculty_id, {})

        # Composite hub score from multiple centrality measures
        raw_score = (
            centrality.get("degree", 0.0) * 0.25
            + centrality.get("betweenness", 0.0) * 0.35
            + centrality.get("eigenvector", 0.0) * 0.25
            + centrality.get("pagerank", 0.0) * 0.15
        )

        is_critical = raw_score > 0.7

        return DomainScore(
            domain=CriticalityDomain.HUB_ANALYSIS,
            raw_score=raw_score,
            normalized_score=raw_score,  # Will be normalized at population level
            is_critical=is_critical,
            details=centrality,
        )

    def normalize_scores(self, scores: list[DomainScore]) -> list[DomainScore]:
        """
        Normalize scores across population for fair comparison.

        Uses min-max normalization so scores are relative to the population.

        Args:
            scores: List of DomainScores from same domain

        Returns:
            Same list with normalized_score and percentile populated
        """
        if not scores:
            return scores

        raw_values = [s.raw_score for s in scores]
        min_val = min(raw_values)
        max_val = max(raw_values)
        range_val = max_val - min_val

        sorted_values = sorted(raw_values)

        for score in scores:
            # Min-max normalization
            if range_val > 0:
                score.normalized_score = (score.raw_score - min_val) / range_val
            else:
                score.normalized_score = 0.5  # All same, put in middle

            # Percentile
            rank = sorted_values.index(score.raw_score)
            score.percentile = (rank / len(scores)) * 100

        return scores

    def analyze_faculty(
        self,
        faculty_id: UUID,
        faculty_name: str,
        assignments: list,
        coverage_requirements: dict[UUID, int],
        burnout_states: dict[UUID, str] | None = None,
    ) -> UnifiedCriticalIndex:
        """
        Compute unified critical index for a single faculty member.

        Args:
            faculty_id: Faculty member to analyze
            faculty_name: Display name
            assignments: All assignments in the period
            coverage_requirements: Block ID -> required coverage count
            burnout_states: Optional burnout state by faculty ID

        Returns:
            UnifiedCriticalIndex with full analysis
        """
        contingency = self.compute_contingency_score(
            faculty_id, assignments, coverage_requirements
        )
        epidemiology = self.compute_epidemiology_score(faculty_id, burnout_states)
        hub = self.compute_hub_score(faculty_id)

        return UnifiedCriticalIndex(
            faculty_id=faculty_id,
            faculty_name=faculty_name,
            calculated_at=datetime.now(),
            contingency_score=contingency,
            epidemiology_score=epidemiology,
            hub_score=hub,
            confidence=self._calculate_confidence(contingency, epidemiology, hub),
        )

    def _calculate_confidence(
        self,
        contingency: DomainScore,
        epidemiology: DomainScore,
        hub: DomainScore,
    ) -> float:
        """
        Calculate confidence in the unified index.

        Based on data quality and availability.
        """
        confidence = 0.0

        # Contingency: based on number of blocks analyzed
        cont_blocks = contingency.details.get("total_assigned_blocks", 0)
        if cont_blocks > 20:
            confidence += 0.35
        elif cont_blocks > 5:
            confidence += 0.25
        elif cont_blocks > 0:
            confidence += 0.15

        # Hub: based on network connectivity
        if self._network and hub.details:
            confidence += 0.35

        # Epidemiology: based on burnout state data
        if epidemiology.details.get("is_burned_out") is not None:
            confidence += 0.30

        return min(1.0, confidence)

    def analyze_population(
        self,
        faculty: list,
        assignments: list,
        coverage_requirements: dict[UUID, int],
        burnout_states: dict[UUID, str] | None = None,
    ) -> PopulationAnalysis:
        """
        Compute unified critical indices for entire faculty population.

        This is the main entry point for comprehensive analysis.

        Args:
            faculty: List of all faculty members
            assignments: All assignments in the period
            coverage_requirements: Block ID -> required coverage count
            burnout_states: Optional burnout states by faculty ID

        Returns:
            PopulationAnalysis with all indices and population metrics
        """
        # Build network if not already done
        if not self._network:
            self.build_network(faculty, assignments)

        # Compute raw scores for all faculty
        indices = []
        contingency_scores = []
        epidemiology_scores = []
        hub_scores = []

        for fac in faculty:
            idx = self.analyze_faculty(
                faculty_id=fac.id,
                faculty_name=getattr(fac, "name", str(fac.id)),
                assignments=assignments,
                coverage_requirements=coverage_requirements,
                burnout_states=burnout_states,
            )
            indices.append(idx)
            contingency_scores.append(idx.contingency_score)
            epidemiology_scores.append(idx.epidemiology_score)
            hub_scores.append(idx.hub_score)

        # Normalize scores across population
        self.normalize_scores(contingency_scores)
        self.normalize_scores(epidemiology_scores)
        self.normalize_scores(hub_scores)

        # Recalculate derived fields with normalized scores
        for idx in indices:
            idx._calculate_composite()
            idx._identify_pattern()
            idx._calculate_agreement()
            idx._recommend_interventions()

        return PopulationAnalysis(
            analyzed_at=datetime.now(),
            total_faculty=len(faculty),
            indices=indices,
        )


# =============================================================================
# Convenience Functions
# =============================================================================


def quick_analysis(
    faculty: list,
    assignments: list,
    coverage_requirements: dict[UUID, int] | None = None,
) -> PopulationAnalysis:
    """
    Quick analysis with sensible defaults.

    Args:
        faculty: List of faculty members (need id, name attributes)
        assignments: List of assignments (need person_id, block_id)
        coverage_requirements: Optional coverage requirements (default: 1 per block)

    Returns:
        PopulationAnalysis with full unified analysis
    """
    if coverage_requirements is None:
        # Default: 1 person required per block
        block_ids = set(a.block_id for a in assignments)
        coverage_requirements = dict.fromkeys(block_ids, 1)

    analyzer = UnifiedCriticalIndexAnalyzer()
    analyzer.build_network(faculty, assignments)
    return analyzer.analyze_population(faculty, assignments, coverage_requirements)


def get_top_critical(
    analysis: PopulationAnalysis,
    n: int = 5,
) -> list[UnifiedCriticalIndex]:
    """
    Get the top N most critical faculty from a population analysis.

    Args:
        analysis: PopulationAnalysis result
        n: Number of top critical to return

    Returns:
        List of UnifiedCriticalIndex sorted by priority
    """
    sorted_indices = sorted(
        analysis.indices, key=lambda x: x.composite_index, reverse=True
    )
    return sorted_indices[:n]


def get_by_pattern(
    analysis: PopulationAnalysis,
    pattern: RiskPattern,
) -> list[UnifiedCriticalIndex]:
    """
    Get all faculty matching a specific risk pattern.

    Args:
        analysis: PopulationAnalysis result
        pattern: RiskPattern to filter by

    Returns:
        List of UnifiedCriticalIndex matching the pattern
    """
    return [idx for idx in analysis.indices if idx.risk_pattern == pattern]
