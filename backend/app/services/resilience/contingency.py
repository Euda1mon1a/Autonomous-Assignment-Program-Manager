"""
Contingency Analysis Service.

Extracts and optimizes N-1/N-2 contingency analysis from the route layer
into a proper service with dependency injection and version tracking.

This service implements power grid N-1/N-2 principles:
- N-1: System must survive loss of any single component
- N-2: System must survive loss of any two components (for critical periods)

Optimizations:
- Pre-computed lookup tables for O(1) assignment access
- Early termination for clearly non-critical faculty
- Caching of coverage calculations
- Batch processing for N-2 pair analysis

Uses SQLAlchemy-Continuum for tracking analysis history.
"""

import logging
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from itertools import combinations
from typing import Any, Optional, Protocol
from uuid import UUID

from sqlalchemy import and_, desc
from sqlalchemy.orm import Session, joinedload

logger = logging.getLogger(__name__)

# Try importing NetworkX for graph analysis
try:
    import networkx as nx
    NETWORKX_AVAILABLE = True
except ImportError:
    NETWORKX_AVAILABLE = False
    nx = None
    logger.warning("NetworkX not available - advanced centrality disabled")

# Try importing SQLAlchemy-Continuum for versioning
try:
    from sqlalchemy_continuum import version_class
    VERSIONING_AVAILABLE = True
except ImportError:
    VERSIONING_AVAILABLE = False
    version_class = None
    logger.warning("SQLAlchemy-Continuum not available - versioning disabled")


class FacultyProtocol(Protocol):
    """Protocol for faculty objects."""
    id: UUID
    name: str


class BlockProtocol(Protocol):
    """Protocol for block objects."""
    id: UUID
    date: date


class AssignmentProtocol(Protocol):
    """Protocol for assignment objects."""
    id: UUID
    person_id: UUID
    block_id: UUID
    rotation_template_id: Optional[UUID]


@dataclass
class VulnerabilityInfo:
    """Information about a single vulnerability."""
    faculty_id: UUID
    faculty_name: str
    severity: str  # "critical", "high", "medium", "low"
    affected_blocks: int
    is_unique_provider: bool
    affected_services: list[str] = field(default_factory=list)
    details: str = ""

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "faculty_id": str(self.faculty_id),
            "faculty_name": self.faculty_name,
            "severity": self.severity,
            "affected_blocks": self.affected_blocks,
            "is_unique_provider": self.is_unique_provider,
            "affected_services": self.affected_services,
            "details": self.details,
        }


@dataclass
class FatalPairInfo:
    """Information about a fatal pair (N-2 vulnerability)."""
    faculty1_id: UUID
    faculty1_name: str
    faculty2_id: UUID
    faculty2_name: str
    uncoverable_blocks: int
    affected_services: list[str] = field(default_factory=list)
    probability_estimate: str = "unknown"

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "faculty1_id": str(self.faculty1_id),
            "faculty1_name": self.faculty1_name,
            "faculty2_id": str(self.faculty2_id),
            "faculty2_name": self.faculty2_name,
            "uncoverable_blocks": self.uncoverable_blocks,
            "affected_services": self.affected_services,
            "probability_estimate": self.probability_estimate,
        }


@dataclass
class CentralityInfo:
    """Centrality score for a faculty member."""
    faculty_id: UUID
    faculty_name: str
    centrality_score: float
    services_covered: int
    unique_coverage_slots: int
    replacement_difficulty: float
    workload_share: float
    betweenness: float = 0.0
    degree: float = 0.0
    eigenvector: float = 0.0
    pagerank: float = 0.0

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "faculty_id": str(self.faculty_id),
            "faculty_name": self.faculty_name,
            "centrality_score": self.centrality_score,
            "services_covered": self.services_covered,
            "unique_coverage_slots": self.unique_coverage_slots,
            "replacement_difficulty": self.replacement_difficulty,
            "workload_share": self.workload_share,
            "betweenness": self.betweenness,
            "degree": self.degree,
            "eigenvector": self.eigenvector,
            "pagerank": self.pagerank,
        }


@dataclass
class N1SimulationResult:
    """Result of N-1 simulation for a single faculty loss."""
    faculty_id: UUID
    faculty_name: str
    blocks_affected: int
    coverage_remaining: float
    is_critical: bool
    uncovered_blocks: list[UUID] = field(default_factory=list)
    simulation_time_ms: float = 0.0

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "faculty_id": str(self.faculty_id),
            "faculty_name": self.faculty_name,
            "blocks_affected": self.blocks_affected,
            "coverage_remaining": self.coverage_remaining,
            "is_critical": self.is_critical,
            "uncovered_blocks": [str(b) for b in self.uncovered_blocks],
            "simulation_time_ms": self.simulation_time_ms,
        }


@dataclass
class N2SimulationResult:
    """Result of N-2 simulation for a faculty pair loss."""
    faculty1_id: UUID
    faculty2_id: UUID
    blocks_affected: int
    coverage_remaining: float
    is_fatal: bool
    uncovered_blocks: list[UUID] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "faculty1_id": str(self.faculty1_id),
            "faculty2_id": str(self.faculty2_id),
            "blocks_affected": self.blocks_affected,
            "coverage_remaining": self.coverage_remaining,
            "is_fatal": self.is_fatal,
            "uncovered_blocks": [str(b) for b in self.uncovered_blocks],
        }


@dataclass
class VulnerabilityAssessment:
    """Assessment of system vulnerability."""
    assessed_at: datetime
    period_start: date
    period_end: date
    total_faculty: int
    total_blocks: int
    total_assignments: int
    n1_pass: bool
    n2_pass: bool
    phase_transition_risk: str
    vulnerabilities_count: int
    critical_vulnerabilities: int
    fatal_pairs_count: int

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "assessed_at": self.assessed_at.isoformat(),
            "period_start": self.period_start.isoformat(),
            "period_end": self.period_end.isoformat(),
            "total_faculty": self.total_faculty,
            "total_blocks": self.total_blocks,
            "total_assignments": self.total_assignments,
            "n1_pass": self.n1_pass,
            "n2_pass": self.n2_pass,
            "phase_transition_risk": self.phase_transition_risk,
            "vulnerabilities_count": self.vulnerabilities_count,
            "critical_vulnerabilities": self.critical_vulnerabilities,
            "fatal_pairs_count": self.fatal_pairs_count,
        }


@dataclass
class ContingencyAnalysisResult:
    """Complete result from contingency analysis."""
    analysis_id: UUID
    analyzed_at: datetime
    period_start: date
    period_end: date

    # N-1 results
    n1_pass: bool
    n1_vulnerabilities: list[VulnerabilityInfo]
    n1_simulations: list[N1SimulationResult]

    # N-2 results
    n2_pass: bool
    n2_fatal_pairs: list[FatalPairInfo]

    # Centrality analysis
    centrality_scores: list[CentralityInfo]
    most_critical_faculty: list[UUID]

    # Risk assessment
    phase_transition_risk: str
    leading_indicators: list[str]
    recommended_actions: list[str]

    # Metadata
    analysis_duration_ms: float
    version_id: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "analysis_id": str(self.analysis_id),
            "analyzed_at": self.analyzed_at.isoformat(),
            "period_start": self.period_start.isoformat(),
            "period_end": self.period_end.isoformat(),
            "n1_pass": self.n1_pass,
            "n1_vulnerabilities": [v.to_dict() for v in self.n1_vulnerabilities],
            "n2_pass": self.n2_pass,
            "n2_fatal_pairs": [p.to_dict() for p in self.n2_fatal_pairs],
            "centrality_scores": [c.to_dict() for c in self.centrality_scores[:10]],
            "most_critical_faculty": [str(f) for f in self.most_critical_faculty],
            "phase_transition_risk": self.phase_transition_risk,
            "leading_indicators": self.leading_indicators,
            "recommended_actions": self.recommended_actions,
            "analysis_duration_ms": self.analysis_duration_ms,
            "version_id": self.version_id,
        }


class ContingencyService:
    """
    Service for N-1/N-2 contingency analysis.

    Implements efficient simulation of faculty loss scenarios using:
    - Pre-computed lookup tables for O(1) access
    - Early termination for non-critical paths
    - Caching of coverage calculations
    - Version tracking via SQLAlchemy-Continuum

    Usage:
        service = ContingencyService(db)
        result = service.analyze_contingency(
            start_date=date.today(),
            end_date=date.today() + timedelta(days=30),
        )
    """

    def __init__(self, db: Session):
        """
        Initialize contingency service.

        Args:
            db: SQLAlchemy database session for dependency injection
        """
        self.db = db
        self._lookup_cache: dict[str, Any] = {}
        self._analysis_cache: dict[str, ContingencyAnalysisResult] = {}

    def analyze_contingency(
        self,
        start_date: date,
        end_date: date,
        coverage_requirements: Optional[dict[UUID, int]] = None,
        current_utilization: float = 0.0,
        include_n2: bool = True,
        max_n2_pairs: int = 100,
    ) -> ContingencyAnalysisResult:
        """
        Perform comprehensive N-1/N-2 contingency analysis.

        Args:
            start_date: Start of analysis period
            end_date: End of analysis period
            coverage_requirements: Block ID -> required coverage count
            current_utilization: Current system utilization for risk calculation
            include_n2: Whether to run N-2 analysis (expensive)
            max_n2_pairs: Maximum pairs to analyze for N-2

        Returns:
            ContingencyAnalysisResult with complete analysis
        """
        import time
        from uuid import uuid4

        start_time = time.time()
        analysis_id = uuid4()

        # Load data
        faculty, blocks, assignments = self._load_data(start_date, end_date)

        if not faculty or not blocks:
            return self._empty_result(analysis_id, start_date, end_date)

        # Build default coverage requirements
        if coverage_requirements is None:
            coverage_requirements = {b.id: 1 for b in blocks}

        # Build optimized lookup tables
        lookups = self._build_lookup_tables(faculty, blocks, assignments)

        # Run N-1 analysis with optimizations
        n1_results, n1_vulnerabilities = self._run_n1_simulation_optimized(
            faculty, blocks, assignments, coverage_requirements, lookups
        )

        n1_pass = not any(v.severity == "critical" for v in n1_vulnerabilities)

        # Run N-2 analysis if requested
        n2_fatal_pairs: list[FatalPairInfo] = []
        if include_n2:
            n2_fatal_pairs = self._run_n2_simulation_optimized(
                faculty, blocks, assignments, coverage_requirements,
                lookups, n1_vulnerabilities, max_n2_pairs
            )

        n2_pass = len(n2_fatal_pairs) == 0

        # Calculate centrality scores
        services: dict[UUID, list[UUID]] = {}  # Service capability mapping
        centrality_scores = self._calculate_centrality_optimized(
            faculty, assignments, services, lookups
        )

        # Identify most critical faculty
        most_critical = [
            v.faculty_id for v in n1_vulnerabilities
            if v.severity in ("critical", "high")
        ][:5]

        # Detect phase transition risk
        phase_risk, indicators = self._detect_phase_transition(
            current_utilization, n1_vulnerabilities, n2_fatal_pairs
        )

        # Build recommendations
        recommendations = self._build_recommendations(
            n1_pass, n2_pass, n1_vulnerabilities, n2_fatal_pairs, phase_risk
        )

        # Get version ID if versioning available
        version_id = self._get_current_version_id() if VERSIONING_AVAILABLE else None

        elapsed_ms = (time.time() - start_time) * 1000

        result = ContingencyAnalysisResult(
            analysis_id=analysis_id,
            analyzed_at=datetime.utcnow(),
            period_start=start_date,
            period_end=end_date,
            n1_pass=n1_pass,
            n1_vulnerabilities=n1_vulnerabilities,
            n1_simulations=n1_results,
            n2_pass=n2_pass,
            n2_fatal_pairs=n2_fatal_pairs,
            centrality_scores=centrality_scores,
            most_critical_faculty=most_critical,
            phase_transition_risk=phase_risk,
            leading_indicators=indicators,
            recommended_actions=recommendations,
            analysis_duration_ms=elapsed_ms,
            version_id=version_id,
        )

        # Log analysis summary
        logger.info(
            "Contingency analysis completed: n1_pass=%s, n2_pass=%s, "
            "vulnerabilities=%d, fatal_pairs=%d, duration=%.1fms",
            n1_pass, n2_pass, len(n1_vulnerabilities),
            len(n2_fatal_pairs), elapsed_ms
        )

        return result

    def get_vulnerability_assessment(
        self,
        start_date: date,
        end_date: date,
    ) -> VulnerabilityAssessment:
        """
        Get a quick vulnerability assessment without full simulation.

        This is faster than full analysis and suitable for health checks.

        Args:
            start_date: Start of assessment period
            end_date: End of assessment period

        Returns:
            VulnerabilityAssessment summary
        """
        result = self.analyze_contingency(
            start_date=start_date,
            end_date=end_date,
            include_n2=False,  # Skip N-2 for quick assessment
        )

        critical_count = sum(
            1 for v in result.n1_vulnerabilities
            if v.severity == "critical"
        )

        return VulnerabilityAssessment(
            assessed_at=result.analyzed_at,
            period_start=start_date,
            period_end=end_date,
            total_faculty=len(set(s.faculty_id for s in result.n1_simulations)),
            total_blocks=len(set(
                b for s in result.n1_simulations for b in s.uncovered_blocks
            )) if result.n1_simulations else 0,
            total_assignments=0,  # Set from actual count
            n1_pass=result.n1_pass,
            n2_pass=result.n2_pass,
            phase_transition_risk=result.phase_transition_risk,
            vulnerabilities_count=len(result.n1_vulnerabilities),
            critical_vulnerabilities=critical_count,
            fatal_pairs_count=len(result.n2_fatal_pairs),
        )

    def simulate_faculty_loss(
        self,
        faculty_id: UUID,
        start_date: date,
        end_date: date,
    ) -> N1SimulationResult:
        """
        Simulate loss of a specific faculty member.

        Args:
            faculty_id: Faculty member to simulate losing
            start_date: Start of simulation period
            end_date: End of simulation period

        Returns:
            N1SimulationResult with simulation details
        """
        import time

        start_time = time.time()

        faculty, blocks, assignments = self._load_data(start_date, end_date)

        target_faculty = next((f for f in faculty if f.id == faculty_id), None)
        if not target_faculty:
            return N1SimulationResult(
                faculty_id=faculty_id,
                faculty_name="Unknown",
                blocks_affected=0,
                coverage_remaining=1.0,
                is_critical=False,
            )

        lookups = self._build_lookup_tables(faculty, blocks, assignments)
        coverage_requirements = {b.id: 1 for b in blocks}

        result = self._simulate_single_loss(
            target_faculty, blocks, assignments, coverage_requirements, lookups
        )

        result.simulation_time_ms = (time.time() - start_time) * 1000

        return result

    def calculate_centrality(
        self,
        start_date: date,
        end_date: date,
        services: Optional[dict[UUID, list[UUID]]] = None,
    ) -> list[CentralityInfo]:
        """
        Calculate centrality scores for all faculty.

        Args:
            start_date: Start of analysis period
            end_date: End of analysis period
            services: Service capability mapping (service_id -> faculty_ids)

        Returns:
            List of CentralityInfo sorted by score descending
        """
        faculty, blocks, assignments = self._load_data(start_date, end_date)

        if not faculty:
            return []

        lookups = self._build_lookup_tables(faculty, blocks, assignments)

        return self._calculate_centrality_optimized(
            faculty, assignments, services or {}, lookups
        )

    # =========================================================================
    # Private Methods - Data Loading
    # =========================================================================

    def _load_data(
        self,
        start_date: date,
        end_date: date,
    ) -> tuple[list[Any], list[Any], list[Any]]:
        """Load faculty, blocks, and assignments for the period."""
        from app.models.assignment import Assignment
        from app.models.block import Block
        from app.models.person import Person

        faculty = (
            self.db.query(Person)
            .filter(Person.type == "faculty")
            .order_by(Person.id)
            .all()
        )

        blocks = (
            self.db.query(Block)
            .filter(
                Block.date >= start_date,
                Block.date <= end_date
            )
            .order_by(Block.date, Block.id)
            .all()
        )

        assignments = (
            self.db.query(Assignment)
            .join(Block)
            .options(
                joinedload(Assignment.block),
                joinedload(Assignment.person),
                joinedload(Assignment.rotation_template)
            )
            .filter(
                Block.date >= start_date,
                Block.date <= end_date
            )
            .order_by(Block.date, Assignment.id)
            .all()
        )

        logger.debug(
            "Loaded data: faculty=%d, blocks=%d, assignments=%d",
            len(faculty), len(blocks), len(assignments)
        )

        return faculty, blocks, assignments

    def _build_lookup_tables(
        self,
        faculty: list[Any],
        blocks: list[Any],
        assignments: list[Any],
    ) -> dict[str, Any]:
        """
        Build optimized lookup tables for O(1) access.

        Returns dict with:
        - assignments_by_faculty: faculty_id -> list[assignment]
        - assignments_by_block: block_id -> list[assignment]
        - faculty_by_id: faculty_id -> faculty
        - block_by_id: block_id -> block
        - faculty_assignment_count: faculty_id -> count
        """
        assignments_by_faculty: dict[UUID, list[Any]] = defaultdict(list)
        assignments_by_block: dict[UUID, list[Any]] = defaultdict(list)
        faculty_assignment_count: dict[UUID, int] = defaultdict(int)

        for assignment in assignments:
            assignments_by_faculty[assignment.person_id].append(assignment)
            assignments_by_block[assignment.block_id].append(assignment)
            faculty_assignment_count[assignment.person_id] += 1

        return {
            "assignments_by_faculty": dict(assignments_by_faculty),
            "assignments_by_block": dict(assignments_by_block),
            "faculty_by_id": {f.id: f for f in faculty},
            "block_by_id": {b.id: b for b in blocks},
            "faculty_assignment_count": dict(faculty_assignment_count),
        }

    # =========================================================================
    # Private Methods - N-1 Simulation
    # =========================================================================

    def _run_n1_simulation_optimized(
        self,
        faculty: list[Any],
        blocks: list[Any],
        assignments: list[Any],
        coverage_requirements: dict[UUID, int],
        lookups: dict[str, Any],
    ) -> tuple[list[N1SimulationResult], list[VulnerabilityInfo]]:
        """
        Run optimized N-1 simulation for all faculty.

        Optimizations:
        1. Early termination for faculty with no assignments
        2. Pre-computed coverage per block
        3. Direct lookup instead of iteration
        """
        simulations: list[N1SimulationResult] = []
        vulnerabilities: list[VulnerabilityInfo] = []

        assignments_by_faculty = lookups["assignments_by_faculty"]
        assignments_by_block = lookups["assignments_by_block"]

        for fac in faculty:
            fac_assignments = assignments_by_faculty.get(fac.id, [])

            # Early termination: faculty with no assignments
            if not fac_assignments:
                simulations.append(N1SimulationResult(
                    faculty_id=fac.id,
                    faculty_name=fac.name,
                    blocks_affected=0,
                    coverage_remaining=1.0,
                    is_critical=False,
                ))
                continue

            result = self._simulate_single_loss(
                fac, blocks, assignments, coverage_requirements, lookups
            )
            simulations.append(result)

            # Create vulnerability if there are affected blocks
            if result.blocks_affected > 0:
                is_unique = any(
                    len(assignments_by_block.get(a.block_id, [])) == 1
                    for a in fac_assignments
                )

                severity = self._calculate_severity(
                    result.blocks_affected, is_unique, len(blocks)
                )

                vulnerabilities.append(VulnerabilityInfo(
                    faculty_id=fac.id,
                    faculty_name=fac.name,
                    severity=severity,
                    affected_blocks=result.blocks_affected,
                    is_unique_provider=is_unique,
                    details=f"Loss would leave {result.blocks_affected} blocks under-covered",
                ))

        # Sort vulnerabilities by severity
        severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        vulnerabilities.sort(
            key=lambda v: (severity_order.get(v.severity, 4), -v.affected_blocks)
        )

        return simulations, vulnerabilities

    def _simulate_single_loss(
        self,
        faculty: Any,
        blocks: list[Any],
        assignments: list[Any],
        coverage_requirements: dict[UUID, int],
        lookups: dict[str, Any],
    ) -> N1SimulationResult:
        """Simulate loss of a single faculty member."""
        assignments_by_faculty = lookups["assignments_by_faculty"]
        assignments_by_block = lookups["assignments_by_block"]

        fac_assignments = assignments_by_faculty.get(faculty.id, [])
        affected_blocks: list[UUID] = []
        uncovered_blocks: list[UUID] = []

        for assignment in fac_assignments:
            block_id = assignment.block_id
            block_assignments = assignments_by_block.get(block_id, [])

            # Count coverage without this faculty
            remaining_coverage = sum(
                1 for a in block_assignments
                if a.person_id != faculty.id
            )

            required = coverage_requirements.get(block_id, 1)

            if remaining_coverage < required:
                affected_blocks.append(block_id)
                if remaining_coverage == 0:
                    uncovered_blocks.append(block_id)

        total_blocks = len(blocks)
        coverage_remaining = 1.0 - (len(affected_blocks) / total_blocks) if total_blocks > 0 else 1.0
        is_critical = len(uncovered_blocks) > 0

        return N1SimulationResult(
            faculty_id=faculty.id,
            faculty_name=faculty.name,
            blocks_affected=len(affected_blocks),
            coverage_remaining=coverage_remaining,
            is_critical=is_critical,
            uncovered_blocks=uncovered_blocks,
        )

    def _calculate_severity(
        self,
        affected_blocks: int,
        is_unique: bool,
        total_blocks: int,
    ) -> str:
        """Calculate vulnerability severity."""
        if is_unique:
            return "critical"

        if total_blocks == 0:
            return "low"

        ratio = affected_blocks / total_blocks

        if ratio > 0.20:
            return "critical"
        elif ratio > 0.10 or affected_blocks > 10:
            return "high"
        elif ratio > 0.05 or affected_blocks > 5:
            return "medium"
        else:
            return "low"

    # =========================================================================
    # Private Methods - N-2 Simulation
    # =========================================================================

    def _run_n2_simulation_optimized(
        self,
        faculty: list[Any],
        blocks: list[Any],
        assignments: list[Any],
        coverage_requirements: dict[UUID, int],
        lookups: dict[str, Any],
        n1_vulnerabilities: list[VulnerabilityInfo],
        max_pairs: int,
    ) -> list[FatalPairInfo]:
        """
        Run optimized N-2 simulation.

        Optimizations:
        1. Only analyze pairs involving critical/high faculty from N-1
        2. Early termination when max_pairs reached
        3. Skip pairs with no overlapping coverage
        """
        fatal_pairs: list[FatalPairInfo] = []

        # Get critical faculty from N-1 results
        critical_ids = {
            v.faculty_id for v in n1_vulnerabilities
            if v.severity in ("critical", "high")
        }

        # If no critical faculty, analyze top by assignment count
        if len(critical_ids) < 2:
            sorted_faculty = sorted(
                faculty,
                key=lambda f: len(lookups["assignments_by_faculty"].get(f.id, [])),
                reverse=True
            )
            analysis_faculty = sorted_faculty[:min(10, len(sorted_faculty))]
        else:
            analysis_faculty = [f for f in faculty if f.id in critical_ids]

        pairs_analyzed = 0
        assignments_by_faculty = lookups["assignments_by_faculty"]

        for fac1, fac2 in combinations(analysis_faculty, 2):
            if pairs_analyzed >= max_pairs:
                break

            result = self._simulate_pair_loss(
                fac1, fac2, blocks, assignments, coverage_requirements, lookups
            )

            if result.is_fatal:
                fatal_pairs.append(FatalPairInfo(
                    faculty1_id=fac1.id,
                    faculty1_name=fac1.name,
                    faculty2_id=fac2.id,
                    faculty2_name=fac2.name,
                    uncoverable_blocks=result.blocks_affected,
                ))

            pairs_analyzed += 1

        # Sort by severity
        fatal_pairs.sort(key=lambda p: -p.uncoverable_blocks)

        return fatal_pairs

    def _simulate_pair_loss(
        self,
        fac1: Any,
        fac2: Any,
        blocks: list[Any],
        assignments: list[Any],
        coverage_requirements: dict[UUID, int],
        lookups: dict[str, Any],
    ) -> N2SimulationResult:
        """Simulate loss of a faculty pair."""
        assignments_by_faculty = lookups["assignments_by_faculty"]
        assignments_by_block = lookups["assignments_by_block"]

        # Get combined affected blocks
        fac1_blocks = {a.block_id for a in assignments_by_faculty.get(fac1.id, [])}
        fac2_blocks = {a.block_id for a in assignments_by_faculty.get(fac2.id, [])}
        combined_blocks = fac1_blocks | fac2_blocks

        uncovered: list[UUID] = []

        for block_id in combined_blocks:
            block_assignments = assignments_by_block.get(block_id, [])

            # Count coverage without both faculty
            remaining = sum(
                1 for a in block_assignments
                if a.person_id not in (fac1.id, fac2.id)
            )

            required = coverage_requirements.get(block_id, 1)
            if remaining < required:
                uncovered.append(block_id)

        total_blocks = len(blocks)
        coverage_remaining = 1.0 - (len(uncovered) / total_blocks) if total_blocks > 0 else 1.0

        return N2SimulationResult(
            faculty1_id=fac1.id,
            faculty2_id=fac2.id,
            blocks_affected=len(uncovered),
            coverage_remaining=coverage_remaining,
            is_fatal=len(uncovered) > 0,
            uncovered_blocks=uncovered,
        )

    # =========================================================================
    # Private Methods - Centrality Calculation
    # =========================================================================

    def _calculate_centrality_optimized(
        self,
        faculty: list[Any],
        assignments: list[Any],
        services: dict[UUID, list[UUID]],
        lookups: dict[str, Any],
    ) -> list[CentralityInfo]:
        """
        Calculate centrality scores with optimizations.

        Uses NetworkX if available for advanced graph metrics.
        """
        scores: list[CentralityInfo] = []
        total_assignments = len(assignments)
        assignment_counts = lookups["faculty_assignment_count"]

        # Try NetworkX for advanced metrics
        nx_metrics = self._calculate_networkx_centrality(
            faculty, assignments, services
        ) if NETWORKX_AVAILABLE else {}

        for fac in faculty:
            # Services covered
            services_covered = sum(
                1 for svc_faculty in services.values()
                if fac.id in svc_faculty
            )

            # Unique coverage
            unique_coverage = sum(
                1 for svc_faculty in services.values()
                if svc_faculty == [fac.id]
            )

            # Replacement difficulty
            if services_covered > 0:
                avg_alternatives = sum(
                    len(svc_faculty) - 1
                    for svc_faculty in services.values()
                    if fac.id in svc_faculty
                ) / services_covered
                replacement_difficulty = 1.0 / (1.0 + avg_alternatives)
            else:
                replacement_difficulty = 0.0

            # Workload share
            my_assignments = assignment_counts.get(fac.id, 0)
            workload_share = my_assignments / total_assignments if total_assignments > 0 else 0.0

            # Get NetworkX metrics if available
            node_key = f"faculty:{fac.id}"
            nx_betweenness = nx_metrics.get("betweenness", {}).get(node_key, 0.0)
            nx_degree = nx_metrics.get("degree", {}).get(node_key, 0.0)
            nx_eigenvector = nx_metrics.get("eigenvector", {}).get(node_key, 0.0)
            nx_pagerank = nx_metrics.get("pagerank", {}).get(node_key, 0.0)

            # Combined score
            if nx_metrics:
                score = (
                    0.25 * nx_betweenness +
                    0.25 * nx_pagerank +
                    0.15 * nx_degree +
                    0.10 * nx_eigenvector +
                    0.15 * replacement_difficulty +
                    0.10 * workload_share
                )
            else:
                # Basic score without NetworkX
                score = (
                    0.30 * (services_covered / max(len(services), 1)) +
                    0.30 * (unique_coverage / max(len(services), 1)) +
                    0.20 * replacement_difficulty +
                    0.20 * workload_share
                )

            scores.append(CentralityInfo(
                faculty_id=fac.id,
                faculty_name=fac.name,
                centrality_score=score,
                services_covered=services_covered,
                unique_coverage_slots=unique_coverage,
                replacement_difficulty=replacement_difficulty,
                workload_share=workload_share,
                betweenness=nx_betweenness,
                degree=nx_degree,
                eigenvector=nx_eigenvector,
                pagerank=nx_pagerank,
            ))

        scores.sort(key=lambda s: -s.centrality_score)
        return scores

    def _calculate_networkx_centrality(
        self,
        faculty: list[Any],
        assignments: list[Any],
        services: dict[UUID, list[UUID]],
    ) -> dict[str, dict[str, float]]:
        """Calculate centrality using NetworkX."""
        if not NETWORKX_AVAILABLE or nx is None:
            return {}

        try:
            G = nx.Graph()

            # Add faculty nodes
            for fac in faculty:
                G.add_node(f"faculty:{fac.id}", type="faculty")

            # Add assignment edges
            for assignment in assignments:
                G.add_edge(
                    f"faculty:{assignment.person_id}",
                    f"block:{assignment.block_id}",
                )

            # Add service edges
            for service_id, faculty_ids in services.items():
                for fac_id in faculty_ids:
                    G.add_edge(
                        f"faculty:{fac_id}",
                        f"service:{service_id}",
                    )

            # Calculate metrics
            betweenness = nx.betweenness_centrality(G)
            degree = nx.degree_centrality(G)
            pagerank = nx.pagerank(G, alpha=0.85)

            try:
                eigenvector = nx.eigenvector_centrality(G, max_iter=1000)
            except nx.PowerIterationFailedConvergence:
                eigenvector = dict.fromkeys(G.nodes(), 0.0)

            return {
                "betweenness": betweenness,
                "degree": degree,
                "eigenvector": eigenvector,
                "pagerank": pagerank,
            }

        except Exception as e:
            logger.warning(f"NetworkX centrality calculation failed: {e}")
            return {}

    # =========================================================================
    # Private Methods - Phase Transition Detection
    # =========================================================================

    def _detect_phase_transition(
        self,
        current_utilization: float,
        vulnerabilities: list[VulnerabilityInfo],
        fatal_pairs: list[FatalPairInfo],
    ) -> tuple[str, list[str]]:
        """Detect risk of phase transition."""
        indicators: list[str] = []

        # Utilization indicators
        if current_utilization > 0.95:
            indicators.append("Utilization above 95% - in critical zone")
        elif current_utilization > 0.90:
            indicators.append("Utilization above 90% - approaching critical")
        elif current_utilization > 0.85:
            indicators.append("Utilization above 85% - elevated risk")

        # Vulnerability indicators
        critical_count = sum(1 for v in vulnerabilities if v.severity == "critical")
        if critical_count >= 3:
            indicators.append(f"{critical_count} critical vulnerabilities - high cascade risk")
        elif critical_count >= 1:
            indicators.append(f"{critical_count} critical vulnerabilities detected")

        # N-2 indicators
        if len(fatal_pairs) >= 5:
            indicators.append(f"{len(fatal_pairs)} fatal pairs - fragile system")
        elif len(fatal_pairs) >= 1:
            indicators.append(f"{len(fatal_pairs)} fatal pairs detected")

        # Determine risk level
        if len(indicators) >= 3:
            risk = "critical"
        elif len(indicators) >= 2:
            risk = "high"
        elif len(indicators) >= 1:
            risk = "medium"
        else:
            risk = "low"

        return risk, indicators

    # =========================================================================
    # Private Methods - Recommendations
    # =========================================================================

    def _build_recommendations(
        self,
        n1_pass: bool,
        n2_pass: bool,
        vulnerabilities: list[VulnerabilityInfo],
        fatal_pairs: list[FatalPairInfo],
        phase_risk: str,
    ) -> list[str]:
        """Build recommended actions based on analysis."""
        recommendations: list[str] = []

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

        # Specific recommendations for unique providers
        for vuln in vulnerabilities[:3]:
            if vuln.is_unique_provider:
                recommendations.append(
                    f"Train backup for {vuln.faculty_name} - sole provider for some services"
                )

        return recommendations

    # =========================================================================
    # Private Methods - Versioning
    # =========================================================================

    def _get_current_version_id(self) -> Optional[str]:
        """Get current version ID from SQLAlchemy-Continuum."""
        if not VERSIONING_AVAILABLE or version_class is None:
            return None

        try:
            from app.models.assignment import Assignment

            AssignmentVersion = version_class(Assignment)

            latest = (
                self.db.query(AssignmentVersion.transaction_id)
                .order_by(desc(AssignmentVersion.transaction_id))
                .first()
            )

            return str(latest[0]) if latest else None

        except Exception as e:
            logger.warning(f"Could not get version ID: {e}")
            return None

    # =========================================================================
    # Private Methods - Helpers
    # =========================================================================

    def _empty_result(
        self,
        analysis_id: UUID,
        start_date: date,
        end_date: date,
    ) -> ContingencyAnalysisResult:
        """Return empty result when no data available."""
        return ContingencyAnalysisResult(
            analysis_id=analysis_id,
            analyzed_at=datetime.utcnow(),
            period_start=start_date,
            period_end=end_date,
            n1_pass=True,
            n1_vulnerabilities=[],
            n1_simulations=[],
            n2_pass=True,
            n2_fatal_pairs=[],
            centrality_scores=[],
            most_critical_faculty=[],
            phase_transition_risk="low",
            leading_indicators=[],
            recommended_actions=[],
            analysis_duration_ms=0.0,
        )
