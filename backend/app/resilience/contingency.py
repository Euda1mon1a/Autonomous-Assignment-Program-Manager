"""
Contingency Analysis (Power Grid N-1/N-2 Planning).

Implements N-1 and N-2 contingency analysis from electrical grid operations:

N-1: System must survive the loss of any single component
N-2: System must survive the loss of any two components (for critical periods)

Cascade failure anatomy:
1. Initial failure increases load on remaining components
2. Overloaded components fail faster
3. Each failure increases load on survivors
4. System experiences rapid, accelerating collapse

This module identifies vulnerabilities before they cause cascades.

Uses NetworkX for advanced graph-based centrality analysis:
- Betweenness centrality: How often a faculty member is on the shortest path
- Degree centrality: How connected a faculty member is
- Eigenvector centrality: Importance based on connections to important nodes
- PageRank: Google's algorithm adapted for faculty importance
"""

import functools
import logging
from dataclasses import dataclass, field
from datetime import date, timedelta
from itertools import combinations
from uuid import UUID

try:
    import networkx as nx

    NETWORKX_AVAILABLE = True
except ImportError:
    NETWORKX_AVAILABLE = False
    nx = None

logger = logging.getLogger(__name__)


@dataclass
class Vulnerability:
    """A specific vulnerability identified by contingency analysis."""

    faculty_id: UUID
    faculty_name: str
    severity: str  # "critical", "high", "medium", "low"
    affected_blocks: int
    affected_services: list[str] = field(default_factory=list)
    is_unique_provider: bool = False  # Only person who can cover something
    details: str = ""


@dataclass
class FatalPair:
    """A pair of faculty whose simultaneous loss causes system failure."""

    faculty_1_id: UUID
    faculty_1_name: str
    faculty_2_id: UUID
    faculty_2_name: str
    uncoverable_blocks: int
    affected_services: list[str] = field(default_factory=list)
    probability_estimate: str = "unknown"  # Could be "low", "medium", "high"


@dataclass
class VulnerabilityReport:
    """Complete vulnerability report from contingency analysis."""

    analysis_date: date
    period_start: date
    period_end: date

    # N-1 Analysis
    n1_vulnerabilities: list[Vulnerability] = field(default_factory=list)
    n1_pass: bool = True  # True if system survives any single loss

    # N-2 Analysis
    n2_fatal_pairs: list[FatalPair] = field(default_factory=list)
    n2_pass: bool = True  # True if system survives any pair loss

    # Summary
    most_critical_faculty: list[UUID] = field(default_factory=list)
    recommended_actions: list[str] = field(default_factory=list)

    # Phase transition indicators
    phase_transition_risk: str = "low"  # "low", "medium", "high", "critical"
    leading_indicators: list[str] = field(default_factory=list)


@dataclass
class CentralityScore:
    """Measures how critical a faculty member is to the schedule."""

    faculty_id: UUID
    faculty_name: str
    score: float  # 0.0 to 1.0, higher = more critical

    # Component scores
    services_covered: int  # Unique services they can cover
    unique_coverage_slots: int  # Slots only they can fill
    replacement_difficulty: float  # 0.0 to 1.0, higher = harder to replace
    workload_share: float  # What fraction of total work they do

    # NetworkX-based centrality metrics (optional, set when using graph analysis)
    betweenness: float = 0.0  # How often on shortest paths
    degree: float = 0.0  # Number of connections
    eigenvector: float = 0.0  # Importance from important connections
    pagerank: float = 0.0  # PageRank score


@dataclass
class CascadeSimulation:
    """Results of simulating a cascade failure."""

    initial_failures: list[UUID]  # Faculty who initially failed
    cascade_steps: list[dict]  # Each step: {step, failed_faculty, reason, remaining}
    total_failures: int
    final_coverage: float
    cascade_length: int  # How many steps before stabilization
    is_catastrophic: bool  # Did system collapse completely?


class ContingencyAnalyzer:
    """
    Analyzes schedule for N-1 and N-2 contingency compliance.

    Inspired by NERC reliability standards for electrical grids,
    this identifies faculty members whose loss would cause:
    - Coverage gaps (uncovered blocks)
    - ACGME violations
    - Cascade failures (overload leading to more failures)
    """

    def __init__(self):
        self._cache = {}

    def analyze_n1(
        self,
        faculty: list,
        blocks: list,
        current_assignments: list,
        coverage_requirements: dict[UUID, int],
    ) -> list[Vulnerability]:
        """
        Perform N-1 analysis: simulate loss of each faculty member.

        N-1 analysis ensures the system can survive the loss of any single
        component. This method tests each faculty member's removal to identify
        critical dependencies and single points of failure.

        Args:
            faculty: List of faculty members (Person objects with id, name attributes).
            blocks: List of Block objects representing the scheduling period.
            current_assignments: List of Assignment objects linking faculty to blocks.
            coverage_requirements: Dict mapping block_id (UUID) to required
                coverage count. Example: {block_uuid: 2} means 2 faculty required.

        Returns:
            list[Vulnerability]: Vulnerabilities sorted by severity (critical first),
                then by affected_blocks count. Each vulnerability includes:
                - faculty_id: UUID of the vulnerable dependency
                - severity: "critical", "high", "medium", or "low"
                - affected_blocks: Number of blocks impacted
                - is_unique_provider: True if sole provider for any service

        Example:
            >>> analyzer = ContingencyAnalyzer()
            >>> vulns = analyzer.analyze_n1(faculty, blocks, assignments, {b.id: 1 for b in blocks})
            >>> critical = [v for v in vulns if v.severity == "critical"]
            >>> if critical:
            ...     print(f"WARNING: {len(critical)} single points of failure detected")
        """
        vulnerabilities = []

        # Build assignment lookup
        assignments_by_faculty = {}
        assignments_by_block = {}

        for assignment in current_assignments:
            # By faculty
            if assignment.person_id not in assignments_by_faculty:
                assignments_by_faculty[assignment.person_id] = []
            assignments_by_faculty[assignment.person_id].append(assignment)

            # By block
            if assignment.block_id not in assignments_by_block:
                assignments_by_block[assignment.block_id] = []
            assignments_by_block[assignment.block_id].append(assignment)

        # For each faculty, simulate their absence
        for fac in faculty:
            fac_assignments = assignments_by_faculty.get(fac.id, [])
            if not fac_assignments:
                continue

            affected_blocks = []
            is_unique = False

            for assignment in fac_assignments:
                block_assignments = assignments_by_block.get(assignment.block_id, [])
                # Check if this faculty is the only one covering this block
                other_coverage = [a for a in block_assignments if a.person_id != fac.id]

                required = coverage_requirements.get(assignment.block_id, 1)
                if len(other_coverage) < required:
                    affected_blocks.append(assignment.block_id)
                    if len(other_coverage) == 0:
                        is_unique = True

            if affected_blocks:
                severity = (
                    "critical"
                    if is_unique
                    else ("high" if len(affected_blocks) > 5 else "medium")
                )

                vulnerabilities.append(
                    Vulnerability(
                        faculty_id=fac.id,
                        faculty_name=fac.name,
                        severity=severity,
                        affected_blocks=len(affected_blocks),
                        is_unique_provider=is_unique,
                        details=f"Loss would leave {len(affected_blocks)} blocks under-covered",
                    )
                )

        # Sort by severity and affected blocks
        severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        vulnerabilities.sort(
            key=lambda v: (severity_order[v.severity], -v.affected_blocks)
        )

        return vulnerabilities

    def analyze_n2(
        self,
        faculty: list,
        blocks: list,
        current_assignments: list,
        coverage_requirements: dict[UUID, int],
        critical_faculty_only: bool = True,
    ) -> list[FatalPair]:
        """
        Perform N-2 analysis: simulate loss of each pair of faculty.

        N-2 analysis tests system resilience against simultaneous loss of
        two components. This is critical for identifying dangerous faculty
        combinations where joint absence would cause system failure.

        For large faculty lists, this can be expensive (O(n^2)), so by default
        only analyzes pairs involving critical faculty (from N-1 analysis).

        Args:
            faculty: List of faculty members (Person objects with id, name).
            blocks: List of Block objects in the scheduling period.
            current_assignments: List of Assignment objects.
            coverage_requirements: Dict mapping block_id to required coverage.
            critical_faculty_only: If True, only analyze pairs involving
                faculty identified as critical/high in N-1 analysis.
                Set False for exhaustive analysis. Defaults to True.

        Returns:
            list[FatalPair]: Fatal pairs sorted by uncoverable_blocks (worst first).
                Each pair includes:
                - faculty_1_id, faculty_2_id: UUIDs of the pair
                - uncoverable_blocks: Blocks that cannot be covered
                - affected_services: List of impacted services

        Example:
            >>> analyzer = ContingencyAnalyzer()
            >>> pairs = analyzer.analyze_n2(faculty, blocks, assignments, coverage_reqs)
            >>> if pairs:
            ...     worst = pairs[0]
            ...     print(f"DANGER: {worst.faculty_1_name} + {worst.faculty_2_name} absence "
            ...           f"leaves {worst.uncoverable_blocks} blocks uncovered")
        """
        fatal_pairs = []

        # Build assignment lookups
        assignments_by_faculty = {}
        for assignment in current_assignments:
            if assignment.person_id not in assignments_by_faculty:
                assignments_by_faculty[assignment.person_id] = []
            assignments_by_faculty[assignment.person_id].append(assignment)

        # Determine which faculty to analyze
        if critical_faculty_only:
            # First run N-1 to find critical faculty
            n1_vulns = self.analyze_n1(
                faculty, blocks, current_assignments, coverage_requirements
            )
            critical_ids = {
                v.faculty_id for v in n1_vulns if v.severity in ("critical", "high")
            }
            analysis_faculty = [f for f in faculty if f.id in critical_ids]

            # If no critical faculty, analyze top 5 by assignment count
            if len(analysis_faculty) < 2:
                sorted_fac = sorted(
                    faculty,
                    key=lambda f: len(assignments_by_faculty.get(f.id, [])),
                    reverse=True,
                )
                analysis_faculty = sorted_fac[: min(5, len(sorted_fac))]
        else:
            analysis_faculty = faculty

        # Check all pairs
        for fac1, fac2 in combinations(analysis_faculty, 2):
            # Calculate combined absence impact
            combined_assignments = set()
            for a in assignments_by_faculty.get(fac1.id, []):
                combined_assignments.add(a.block_id)
            for a in assignments_by_faculty.get(fac2.id, []):
                combined_assignments.add(a.block_id)

            # Count uncoverable blocks
            uncoverable = 0
            for block_id in combined_assignments:
                block_assignments = [
                    a
                    for a in current_assignments
                    if a.block_id == block_id and a.person_id not in (fac1.id, fac2.id)
                ]
                required = coverage_requirements.get(block_id, 1)
                if len(block_assignments) < required:
                    uncoverable += 1

            if uncoverable > 0:
                fatal_pairs.append(
                    FatalPair(
                        faculty_1_id=fac1.id,
                        faculty_1_name=fac1.name,
                        faculty_2_id=fac2.id,
                        faculty_2_name=fac2.name,
                        uncoverable_blocks=uncoverable,
                    )
                )

        # Sort by severity
        fatal_pairs.sort(key=lambda p: -p.uncoverable_blocks)

        return fatal_pairs

    def calculate_centrality(
        self,
        faculty: list,
        assignments: list,
        services: dict[UUID, list[UUID]],  # service_id -> list of credentialed faculty
    ) -> list[CentralityScore]:
        """
        Calculate centrality scores for each faculty member.

        Higher centrality = removal causes more disruption. This identifies
        "hub" faculty whose loss would disproportionately impact operations.
        Based on network theory hub vulnerability analysis.

        The score combines:
        - Services covered (30%): Breadth of capabilities
        - Unique coverage (30%): Sole provider for services
        - Replacement difficulty (20%): How hard to find substitutes
        - Workload share (20%): Current assignment volume

        Args:
            faculty: List of faculty members (Person objects with id, name).
            assignments: List of current Assignment objects.
            services: Dict mapping service_id (UUID) to list of faculty UUIDs
                who are credentialed to provide that service.

        Returns:
            list[CentralityScore]: Scores sorted by centrality (highest first).
                Each score includes:
                - score: Composite centrality (0.0 to 1.0)
                - services_covered: Count of services faculty can provide
                - unique_coverage_slots: Services where they're sole provider
                - replacement_difficulty: How hard to replace (0.0 to 1.0)
                - workload_share: Fraction of total assignments

        Example:
            >>> analyzer = ContingencyAnalyzer()
            >>> services = {svc_uuid: [fac1.id, fac2.id]}  # Both can do this service
            >>> scores = analyzer.calculate_centrality(faculty, assignments, services)
            >>> hubs = [s for s in scores if s.score > 0.7]
            >>> print(f"Identified {len(hubs)} high-centrality faculty")
        """
        scores = []
        total_assignments = len(assignments)

        # Build assignment count by faculty
        assignment_counts = {}
        for a in assignments:
            assignment_counts[a.person_id] = assignment_counts.get(a.person_id, 0) + 1

        for fac in faculty:
            # Services covered
            services_covered = sum(
                1 for svc_faculty in services.values() if fac.id in svc_faculty
            )

            # Unique coverage (services where they're the only option)
            unique_coverage = sum(
                1 for svc_faculty in services.values() if svc_faculty == [fac.id]
            )

            # Replacement difficulty (inverse of how many others can do their services)
            if services_covered > 0:
                avg_alternatives = (
                    sum(
                        len(svc_faculty) - 1
                        for svc_faculty in services.values()
                        if fac.id in svc_faculty
                    )
                    / services_covered
                )
                replacement_difficulty = 1.0 / (1.0 + avg_alternatives)
            else:
                replacement_difficulty = 0.0

            # Workload share
            my_assignments = assignment_counts.get(fac.id, 0)
            workload_share = (
                my_assignments / total_assignments if total_assignments > 0 else 0.0
            )

            # Combined score (weighted)
            score = (
                0.30 * (services_covered / max(len(services), 1))
                + 0.30 * (unique_coverage / max(len(services), 1))
                + 0.20 * replacement_difficulty
                + 0.20 * workload_share
            )

            scores.append(
                CentralityScore(
                    faculty_id=fac.id,
                    faculty_name=fac.name,
                    score=score,
                    services_covered=services_covered,
                    unique_coverage_slots=unique_coverage,
                    replacement_difficulty=replacement_difficulty,
                    workload_share=workload_share,
                )
            )

        scores.sort(key=lambda s: -s.score)
        return scores

    def build_scheduling_graph(
        self,
        faculty: list,
        blocks: list,
        assignments: list,
        services: dict[UUID, list[UUID]],
    ) -> "nx.Graph":
        """
        Build a NetworkX graph representing the scheduling network.

        Graph structure:
        - Faculty nodes (type='faculty')
        - Block nodes (type='block')
        - Service nodes (type='service')
        - Edges: faculty-block (assignment), faculty-service (credential)

        This enables advanced network analysis like centrality and
        cascade failure simulation.

        Args:
            faculty: List of faculty members
            blocks: List of blocks
            assignments: List of current assignments
            services: Dict of service_id -> list of credentialed faculty

        Returns:
            NetworkX Graph (or None if NetworkX not available)
        """
        if not NETWORKX_AVAILABLE:
            logger.warning("NetworkX not available - graph analysis disabled")
            return None

        G = nx.Graph()

        # Add faculty nodes
        for fac in faculty:
            G.add_node(
                f"faculty:{fac.id}",
                type="faculty",
                faculty_id=fac.id,
                name=fac.name,
            )

        # Add block nodes
        for block in blocks:
            G.add_node(
                f"block:{block.id}",
                type="block",
                block_id=block.id,
                date=str(block.date),
            )

        # Add service nodes
        for service_id in services:
            G.add_node(
                f"service:{service_id}",
                type="service",
                service_id=service_id,
            )

        # Add assignment edges (faculty -> block)
        for assignment in assignments:
            G.add_edge(
                f"faculty:{assignment.person_id}",
                f"block:{assignment.block_id}",
                type="assignment",
            )

        # Add credential edges (faculty -> service)
        for service_id, faculty_ids in services.items():
            for fac_id in faculty_ids:
                G.add_edge(
                    f"faculty:{fac_id}",
                    f"service:{service_id}",
                    type="credential",
                )

        logger.debug(
            f"Built scheduling graph: {G.number_of_nodes()} nodes, "
            f"{G.number_of_edges()} edges"
        )

        return G

    def calculate_centrality_networkx(
        self,
        faculty: list,
        blocks: list,
        assignments: list,
        services: dict[UUID, list[UUID]],
    ) -> list[CentralityScore]:
        """
        Calculate centrality using NetworkX graph algorithms.

        Provides more sophisticated centrality measures:
        - Betweenness: How often faculty is on shortest path between others
        - Degree: Raw connection count
        - Eigenvector: Importance based on connection importance
        - PageRank: Google's algorithm for importance

        Falls back to basic calculation if NetworkX unavailable.

        Args:
            faculty: List of faculty members
            blocks: List of blocks
            assignments: List of current assignments
            services: Dict of service_id -> list of credentialed faculty

        Returns:
            List of CentralityScore with NetworkX metrics
        """
        if not NETWORKX_AVAILABLE:
            logger.warning("NetworkX not available - using basic centrality")
            return self.calculate_centrality(faculty, assignments, services)

        # Build graph
        G = self.build_scheduling_graph(faculty, blocks, assignments, services)
        if G is None:
            return self.calculate_centrality(faculty, assignments, services)

        # Calculate NetworkX centrality metrics
        try:
            betweenness = nx.betweenness_centrality(G)
            degree = nx.degree_centrality(G)
            pagerank = nx.pagerank(G, alpha=0.85)

            # Eigenvector can fail on disconnected graphs
            try:
                eigenvector = nx.eigenvector_centrality(G, max_iter=1000)
            except nx.PowerIterationFailedConvergence:
                eigenvector = dict.fromkeys(G.nodes(), 0.0)
        except Exception as e:
            logger.error(f"NetworkX centrality calculation failed: {e}")
            return self.calculate_centrality(faculty, assignments, services)

        # Build scores
        scores = []
        total_assignments = len(assignments)
        assignment_counts = {}
        for a in assignments:
            assignment_counts[a.person_id] = assignment_counts.get(a.person_id, 0) + 1

        for fac in faculty:
            node_key = f"faculty:{fac.id}"

            # Get NetworkX metrics
            nx_betweenness = betweenness.get(node_key, 0.0)
            nx_degree = degree.get(node_key, 0.0)
            nx_eigenvector = eigenvector.get(node_key, 0.0)
            nx_pagerank = pagerank.get(node_key, 0.0)

            # Calculate basic metrics
            services_covered = sum(
                1 for svc_faculty in services.values() if fac.id in svc_faculty
            )
            unique_coverage = sum(
                1 for svc_faculty in services.values() if svc_faculty == [fac.id]
            )

            if services_covered > 0:
                avg_alternatives = (
                    sum(
                        len(svc_faculty) - 1
                        for svc_faculty in services.values()
                        if fac.id in svc_faculty
                    )
                    / services_covered
                )
                replacement_difficulty = 1.0 / (1.0 + avg_alternatives)
            else:
                replacement_difficulty = 0.0

            my_assignments = assignment_counts.get(fac.id, 0)
            workload_share = (
                my_assignments / total_assignments if total_assignments > 0 else 0.0
            )

            # Combined score using NetworkX metrics
            # Weight betweenness and pagerank heavily - they capture "hub" importance
            score = (
                0.25 * nx_betweenness
                + 0.25 * nx_pagerank
                + 0.15 * nx_degree
                + 0.10 * nx_eigenvector
                + 0.15 * replacement_difficulty
                + 0.10 * workload_share
            )

            scores.append(
                CentralityScore(
                    faculty_id=fac.id,
                    faculty_name=fac.name,
                    score=score,
                    services_covered=services_covered,
                    unique_coverage_slots=unique_coverage,
                    replacement_difficulty=replacement_difficulty,
                    workload_share=workload_share,
                    betweenness=nx_betweenness,
                    degree=nx_degree,
                    eigenvector=nx_eigenvector,
                    pagerank=nx_pagerank,
                )
            )

        scores.sort(key=lambda s: -s.score)
        return scores

    def simulate_cascade_failure(
        self,
        faculty: list,
        blocks: list,
        assignments: list,
        initial_failures: list[UUID],
        max_utilization: float = 0.80,
        overload_threshold: float = 1.2,
    ) -> CascadeSimulation:
        """
        Simulate cascade failure from initial faculty losses.

        Models how initial failures propagate through the system, similar to
        electrical grid cascade failures. Key insight: each failure increases
        load on survivors, potentially triggering additional failures.

        Simulation steps:
        1. Initial failures remove their capacity
        2. Load redistributes to remaining faculty
        3. Faculty exceeding overload_threshold "fail" (burnout/departure)
        4. Steps 2-3 repeat until stable or catastrophic collapse

        Args:
            faculty: List of faculty members (Person objects).
            blocks: List of Block objects in the period.
            assignments: List of current Assignment objects.
            initial_failures: List of faculty UUIDs who initially become
                unavailable (illness, departure, etc.).
            max_utilization: Normal maximum utilization threshold (default 0.80).
            overload_threshold: Utilization multiplier that triggers cascade
                failure. 1.2 means 120% of normal capacity. Default 1.2.

        Returns:
            CascadeSimulation: Detailed simulation results including:
                - cascade_steps: List of failure propagation steps
                - total_failures: Final count of failed faculty
                - final_coverage: Coverage rate after cascade stabilizes
                - cascade_length: Number of propagation steps
                - is_catastrophic: True if final coverage < 50%

        Example:
            >>> analyzer = ContingencyAnalyzer()
            >>> # Simulate what happens if Dr. Smith becomes unavailable
            >>> cascade = analyzer.simulate_cascade_failure(
            ...     faculty, blocks, assignments,
            ...     initial_failures=[dr_smith.id]
            ... )
            >>> if cascade.is_catastrophic:
            ...     print(f"CRITICAL: Cascade would collapse to {cascade.final_coverage:.0%} coverage")
        """
        # Build faculty workload map
        assignment_counts = {}
        for a in assignments:
            assignment_counts[a.person_id] = assignment_counts.get(a.person_id, 0) + 1

        # Track state
        active_faculty = {fac.id: fac for fac in faculty}
        failed_ids = set(initial_failures)
        cascade_steps = []

        # Remove initial failures
        for fid in initial_failures:
            if fid in active_faculty:
                del active_faculty[fid]

        # Calculate initial load redistribution
        total_load = sum(assignment_counts.get(fid, 0) for fid in failed_ids)
        remaining_capacity = len(active_faculty)

        step = 0
        while remaining_capacity > 0:
            step += 1

            # Calculate load per remaining faculty
            total_load / remaining_capacity if remaining_capacity > 0 else float("inf")

            # Find faculty who would be overloaded
            new_failures = []
            for fac_id in list(active_faculty.keys()):
                base_load = assignment_counts.get(fac_id, 0)
                # Rough model: each faculty takes equal share of redistributed load
                effective_load = base_load + (total_load / remaining_capacity)

                # Normal capacity is their current load / max_utilization
                normal_capacity = base_load / max_utilization if base_load > 0 else 1

                if effective_load > normal_capacity * overload_threshold:
                    new_failures.append(fac_id)

            if not new_failures:
                break  # Stable

            # Record cascade step
            cascade_steps.append(
                {
                    "step": step,
                    "failed_faculty": [str(fid) for fid in new_failures],
                    "reason": f"Overloaded (>{overload_threshold * 100:.0f}% capacity)",
                    "remaining": len(active_faculty) - len(new_failures),
                }
            )

            # Remove newly failed
            for fid in new_failures:
                failed_ids.add(fid)
                total_load += assignment_counts.get(fid, 0)
                if fid in active_faculty:
                    del active_faculty[fid]

            remaining_capacity = len(active_faculty)

            # Safety limit
            if step > len(faculty):
                break

        # Calculate final state
        total_assignments = len(assignments)
        covered = sum(1 for a in assignments if a.person_id in active_faculty)
        final_coverage = covered / total_assignments if total_assignments > 0 else 0.0

        return CascadeSimulation(
            initial_failures=initial_failures,
            cascade_steps=cascade_steps,
            total_failures=len(failed_ids),
            final_coverage=final_coverage,
            cascade_length=step,
            is_catastrophic=final_coverage < 0.5,
        )

    def find_critical_failure_points(
        self,
        faculty: list,
        blocks: list,
        assignments: list,
        services: dict[UUID, list[UUID]],
    ) -> list[dict]:
        """
        Find faculty whose removal causes cascade failures.

        Combines N-1 analysis with cascade simulation to identify
        true critical failure points.

        Args:
            faculty: List of faculty members
            blocks: List of blocks
            assignments: List of current assignments
            services: Dict of service_id -> list of credentialed faculty

        Returns:
            List of critical points with cascade impact
        """
        critical_points = []

        # Get centrality scores
        if NETWORKX_AVAILABLE:
            centrality = self.calculate_centrality_networkx(
                faculty, blocks, assignments, services
            )
        else:
            centrality = self.calculate_centrality(faculty, assignments, services)

        # For top centrality faculty, simulate cascade
        for score in centrality[:10]:  # Top 10
            cascade = self.simulate_cascade_failure(
                faculty,
                blocks,
                assignments,
                initial_failures=[score.faculty_id],
            )

            if cascade.cascade_length > 0 or cascade.is_catastrophic:
                critical_points.append(
                    {
                        "faculty_id": str(score.faculty_id),
                        "faculty_name": score.faculty_name,
                        "centrality_score": score.score,
                        "betweenness": score.betweenness,
                        "pagerank": score.pagerank,
                        "cascade_length": cascade.cascade_length,
                        "total_failures": cascade.total_failures,
                        "final_coverage": cascade.final_coverage,
                        "is_catastrophic": cascade.is_catastrophic,
                        "risk_level": (
                            "critical"
                            if cascade.is_catastrophic
                            else "high"
                            if cascade.cascade_length > 1
                            else "medium"
                        ),
                    }
                )

        # Sort by risk
        risk_order = {"critical": 0, "high": 1, "medium": 2}
        critical_points.sort(
            key=lambda x: (risk_order.get(x["risk_level"], 3), -x["centrality_score"])
        )

        return critical_points

    def detect_phase_transition_risk(
        self,
        recent_changes: list[dict],
        current_utilization: float,
    ) -> tuple[str, list[str]]:
        """
        Detect risk of phase transition (sudden shift from stable to chaotic).

        Like power grids, scheduling systems exhibit phase transitions where
        small additional stress causes disproportionate impact.

        Leading indicators:
        - Increasing frequency of last-minute changes
        - Growing backlog of unfilled slots
        - Rising complaint/burnout metrics
        - Decreasing time-to-failure for backup plans

        Args:
            recent_changes: List of recent schedule changes with timestamps
            current_utilization: Current system utilization (0.0 to 1.0)

        Returns:
            Tuple of (risk_level, list of indicators)
        """
        indicators = []

        # Check utilization
        if current_utilization > 0.95:
            indicators.append("Utilization above 95% - in critical zone")
        elif current_utilization > 0.90:
            indicators.append("Utilization above 90% - approaching critical")
        elif current_utilization > 0.85:
            indicators.append("Utilization above 85% - elevated risk")

        # Check change frequency
        if recent_changes:
            # Count changes in last 7 days
            week_ago = date.today() - timedelta(days=7)
            recent_count = sum(
                1 for c in recent_changes if c.get("date", date.today()) >= week_ago
            )

            if recent_count > 20:
                indicators.append(
                    f"{recent_count} schedule changes in past week - highly volatile"
                )
            elif recent_count > 10:
                indicators.append(
                    f"{recent_count} schedule changes in past week - elevated volatility"
                )

        # Check for patterns (simplified)
        if len(indicators) >= 3:
            risk = "critical"
        elif len(indicators) >= 2:
            risk = "high"
        elif len(indicators) >= 1:
            risk = "medium"
        else:
            risk = "low"

        return risk, indicators

    def generate_report(
        self,
        faculty: list,
        blocks: list,
        assignments: list,
        coverage_requirements: dict[UUID, int],
        current_utilization: float = 0.0,
        recent_changes: list[dict] = None,
    ) -> VulnerabilityReport:
        """
        Generate comprehensive vulnerability report.

        Args:
            faculty: List of faculty members
            blocks: List of blocks in period
            assignments: List of current assignments
            coverage_requirements: Dict of block_id -> required coverage
            current_utilization: Current utilization rate
            recent_changes: Recent schedule changes for phase transition detection

        Returns:
            Complete VulnerabilityReport
        """
        # Run analyses
        n1_vulns = self.analyze_n1(faculty, blocks, assignments, coverage_requirements)
        n2_pairs = self.analyze_n2(
            faculty,
            blocks,
            assignments,
            coverage_requirements,
            critical_faculty_only=True,
        )

        # Determine pass/fail
        n1_pass = not any(v.severity == "critical" for v in n1_vulns)
        n2_pass = len(n2_pairs) == 0

        # Identify most critical faculty
        critical_ids = [
            v.faculty_id for v in n1_vulns if v.severity in ("critical", "high")
        ][:5]

        # Detect phase transition risk
        phase_risk, indicators = self.detect_phase_transition_risk(
            recent_changes or [],
            current_utilization,
        )

        # Build recommendations
        recommendations = []
        if not n1_pass:
            recommendations.append("URGENT: Cross-train backup for critical faculty")
        if not n2_pass:
            recommendations.append(
                "Schedule high-centrality faculty on different days when possible"
            )
        if phase_risk in ("high", "critical"):
            recommendations.append(
                "System approaching phase transition - reduce load immediately"
            )

        for vuln in n1_vulns[:3]:
            if vuln.is_unique_provider:
                recommendations.append(
                    f"Train backup for {vuln.faculty_name} - sole provider for some services"
                )

        if not blocks:
            period_start = date.today()
            period_end = date.today()
        else:
            period_start = min(b.date for b in blocks)
            period_end = max(b.date for b in blocks)

        return VulnerabilityReport(
            analysis_date=date.today(),
            period_start=period_start,
            period_end=period_end,
            n1_vulnerabilities=n1_vulns,
            n1_pass=n1_pass,
            n2_fatal_pairs=n2_pairs,
            n2_pass=n2_pass,
            most_critical_faculty=critical_ids,
            recommended_actions=recommendations,
            phase_transition_risk=phase_risk,
            leading_indicators=indicators,
        )
