"""
Keystone Species Analysis for Schedule Resilience.

Identifies critical resources (faculty, residents, rotations) whose removal
would cause disproportionate schedule collapse.

Ecology basis: Keystone species have low abundance but high ecosystem impact.
Removing them causes trophic cascades through multiple levels.

Key Concepts:
- Keystoneness = Impact/Abundance ratio (high impact despite low abundance)
- Trophic cascade: Removal triggers chain reactions through dependency network
- Functional redundancy: How many alternatives can fill the same role
- Succession planning: Identifying and training replacements

This differs from hub analysis in important ways:
- Hubs focus on pure connectivity (many connections)
- Keystones focus on disproportionate impact relative to size
- A keystone might have few connections but each is critical
- Example: A specialized proceduralist (low volume, high criticality)

Real-world example from ecology:
Sea otters are keystone species in kelp forests. They're not abundant,
but they control sea urchin populations. Without otters, urchins overgraze
kelp, causing forest collapse and affecting hundreds of species.

In scheduling:
A neonatology specialist might handle few cases (low abundance) but
removing them means no one can cover high-risk deliveries (high impact).
"""

import logging
import statistics
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

logger = logging.getLogger(__name__)

# Try to import NetworkX for graph analysis
try:
    import networkx as nx

    HAS_NETWORKX = True
except ImportError:
    HAS_NETWORKX = False
    logger.warning("NetworkX not installed - keystone analysis will use basic methods")


class EntityType(str, Enum):
    """Type of entity in the scheduling ecosystem."""

    FACULTY = "faculty"
    RESIDENT = "resident"
    ROTATION = "rotation"
    SERVICE = "service"
    SKILL = "skill"


class KeystoneRiskLevel(str, Enum):
    """Risk level if this keystone is lost."""

    LOW = "low"  # Minimal impact, easy replacement
    MODERATE = "moderate"  # Noticeable impact, replacement available
    HIGH = "high"  # Significant disruption, limited replacements
    CRITICAL = "critical"  # Major cascade, difficult to replace
    CATASTROPHIC = "catastrophic"  # System collapse likely


class SuccessionStatus(str, Enum):
    """Status of succession planning for a keystone."""

    NONE = "none"  # No succession plan
    PLANNED = "planned"  # Plan exists but not started
    IN_PROGRESS = "in_progress"  # Actively training backup
    COMPLETED = "completed"  # Backup fully trained
    VERIFIED = "verified"  # Backup proven capable


@dataclass
class KeystoneResource:
    """
    A critical resource whose loss causes disproportionate impact.

    Keystoneness is measured as impact/abundance ratio:
    - High keystoneness: Low abundance but high impact (keystone)
    - Low keystoneness: Impact proportional to abundance (not keystone)
    """

    entity_id: UUID
    entity_name: str
    entity_type: EntityType
    calculated_at: datetime

    # Core metrics
    keystoneness_score: float  # 0.0-1.0, high = disproportionate impact
    abundance: float  # 0.0-1.0, relative presence in system
    impact_if_removed: float  # 0.0-1.0, cascade damage potential
    replacement_difficulty: float  # 0.0-1.0, how hard to find substitute

    # Dependency analysis
    direct_dependents: int  # Entities that directly depend on this
    indirect_dependents: int  # Entities affected via cascade
    cascade_depth: int  # How many levels cascade propagates
    bottleneck_score: float  # How much of a bottleneck (0.0-1.0)

    # Functional redundancy
    functional_redundancy: float  # 0.0-1.0, high = many substitutes
    unique_capabilities: list[str] = field(default_factory=list)
    shared_capabilities: list[str] = field(default_factory=list)

    # Risk assessment
    risk_level: KeystoneRiskLevel = KeystoneRiskLevel.LOW
    risk_factors: list[str] = field(default_factory=list)

    # Succession planning
    succession_status: SuccessionStatus = SuccessionStatus.NONE
    backup_entities: list[UUID] = field(default_factory=list)

    @property
    def is_keystone(self) -> bool:
        """
        Determine if this is truly a keystone resource.

        Keystone criteria:
        1. High impact relative to abundance (keystoneness > 0.6)
        2. Low functional redundancy (< 0.4)
        3. Creates cascade when removed (cascade_depth > 0)
        """
        return (
            self.keystoneness_score > 0.6
            and self.functional_redundancy < 0.4
            and self.cascade_depth > 0
        )

    @property
    def is_single_point_of_failure(self) -> bool:
        """Is this the only entity providing critical capabilities?"""
        return len(self.unique_capabilities) > 0 and self.functional_redundancy < 0.1


@dataclass
class CascadeAnalysis:
    """
    Results of simulating removal cascade.

    Models trophic cascade from ecology: removing keystone triggers
    chain reaction through multiple trophic levels.
    """

    removed_entity_id: UUID
    removed_entity_name: str
    removed_entity_type: EntityType
    simulation_date: datetime

    # Cascade propagation
    cascade_steps: list[dict] = field(default_factory=list)
    affected_entities: dict[EntityType, list[UUID]] = field(default_factory=dict)
    total_affected: int = 0
    cascade_depth: int = 0

    # Impact assessment
    affected_assignments: int = 0  # Assignments that cannot be filled
    coverage_loss: float = 0.0  # Percentage of coverage lost (0.0-1.0)
    recovery_time_days: int = 0  # Estimated days to recover
    is_catastrophic: bool = False  # Coverage loss > 50%

    # Cascade characteristics
    cascade_velocity: float = 0.0  # How quickly cascade spreads
    amplification_factor: float = 1.0  # Initial impact / final impact

    def add_cascade_step(
        self,
        level: int,
        affected_entities: list[UUID],
        affected_types: dict[EntityType, int],
        reason: str,
    ):
        """Record a cascade propagation step."""
        self.cascade_steps.append(
            {
                "level": level,
                "affected_count": len(affected_entities),
                "affected_entities": [str(e) for e in affected_entities],
                "affected_types": {k.value: v for k, v in affected_types.items()},
                "reason": reason,
            }
        )
        self.cascade_depth = max(self.cascade_depth, level)


@dataclass
class SuccessionPlan:
    """
    Succession plan for a keystone resource.

    Identifies backup candidates and training requirements to reduce
    dependency on keystone.
    """

    id: UUID
    keystone_entity_id: UUID
    keystone_entity_name: str
    keystone_entity_type: EntityType
    created_at: datetime

    # Backup candidates (ranked by suitability)
    backup_candidates: list[tuple[UUID, str, float]] = field(
        default_factory=list
    )  # (id, name, suitability_score)

    # Training requirements
    cross_training_needed: list[str] = field(
        default_factory=list
    )  # Skills to train
    estimated_training_hours: int = 0
    training_priority: str = "medium"  # low, medium, high, urgent

    # Implementation
    timeline: dict[str, date] = field(default_factory=dict)  # milestone -> date
    status: SuccessionStatus = SuccessionStatus.PLANNED
    assigned_trainers: list[UUID] = field(default_factory=list)

    # Risk mitigation
    interim_measures: list[str] = field(
        default_factory=list
    )  # Temporary workarounds
    risk_reduction: float = 0.0  # Expected risk reduction (0.0-1.0)

    # Tracking
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    verified_at: Optional[datetime] = None


class KeystoneAnalyzer:
    """
    Analyzes scheduling ecosystem for keystone resources.

    Identifies critical resources whose removal would cause
    disproportionate disruption (trophic cascade), and recommends
    succession planning to reduce dependency.
    """

    def __init__(
        self,
        keystone_threshold: float = 0.6,
        use_networkx: bool = True,
    ):
        """
        Initialize keystone analyzer.

        Args:
            keystone_threshold: Minimum keystoneness score to be considered keystone
            use_networkx: Whether to use NetworkX for graph analysis
        """
        self.keystone_threshold = keystone_threshold
        self.use_networkx = use_networkx and HAS_NETWORKX

        self.keystone_cache: dict[UUID, KeystoneResource] = {}
        self.cascade_simulations: dict[UUID, CascadeAnalysis] = {}
        self.succession_plans: dict[UUID, SuccessionPlan] = {}

        self._dependency_graph: Optional["nx.DiGraph"] = None
        self._last_analysis: Optional[datetime] = None

    def build_dependency_graph(
        self,
        faculty: list,
        residents: list,
        assignments: list,
        services: dict[UUID, list[UUID]],  # service_id -> capable faculty/residents
        rotations: dict[UUID, dict],  # rotation_id -> {name, required_skills, etc}
    ) -> Optional["nx.DiGraph"]:
        """
        Build directed dependency graph for the scheduling ecosystem.

        Nodes represent entities (faculty, residents, services, rotations).
        Edges represent dependencies (A enables B, B requires A).

        Args:
            faculty: List of faculty members
            residents: List of residents
            assignments: Current assignments
            services: Dict mapping service_id to capable providers
            rotations: Dict of rotation metadata

        Returns:
            NetworkX DiGraph or None if NetworkX unavailable
        """
        if not self.use_networkx:
            logger.warning("NetworkX not available - cannot build dependency graph")
            return None

        G = nx.DiGraph()
        self._last_analysis = datetime.now()

        # Add faculty nodes
        for fac in faculty:
            fac_id = fac.id if hasattr(fac, "id") else fac["id"]
            fac_name = getattr(fac, "name", str(fac_id))
            G.add_node(
                str(fac_id),
                type=EntityType.FACULTY.value,
                name=fac_name,
                entity_type=EntityType.FACULTY,
            )

        # Add resident nodes
        for res in residents:
            res_id = res.id if hasattr(res, "id") else res["id"]
            res_name = getattr(res, "name", str(res_id))
            G.add_node(
                str(res_id),
                type=EntityType.RESIDENT.value,
                name=res_name,
                entity_type=EntityType.RESIDENT,
            )

        # Add service nodes
        for service_id in services:
            G.add_node(
                f"service:{service_id}",
                type=EntityType.SERVICE.value,
                name=f"Service {service_id}",
                entity_type=EntityType.SERVICE,
            )

        # Add rotation nodes
        for rot_id, rot_data in rotations.items():
            G.add_node(
                f"rotation:{rot_id}",
                type=EntityType.ROTATION.value,
                name=rot_data.get("name", str(rot_id)),
                entity_type=EntityType.ROTATION,
            )

        # Add dependency edges
        # Faculty/Residents -> Services they enable
        for service_id, capable_ids in services.items():
            for provider_id in capable_ids:
                G.add_edge(
                    str(provider_id),
                    f"service:{service_id}",
                    relationship="enables",
                    weight=1.0 / len(capable_ids),  # Weight by replaceability
                )

        # Services -> Rotations that require them
        for rot_id, rot_data in rotations.items():
            required_services = rot_data.get("required_services", [])
            for service_id in required_services:
                if f"service:{service_id}" in G:
                    G.add_edge(
                        f"service:{service_id}",
                        f"rotation:{rot_id}",
                        relationship="required_for",
                        weight=1.0,
                    )

        # Assignments create dependencies: Rotation -> Person (person is assigned)
        assignment_counts = defaultdict(int)
        for a in assignments:
            person_id = str(getattr(a, "person_id", a.get("person_id")))
            rot_id = getattr(a, "rotation_template_id", a.get("rotation_template_id"))
            if rot_id:
                assignment_counts[(rot_id, person_id)] += 1

        for (rot_id, person_id), count in assignment_counts.items():
            if f"rotation:{rot_id}" in G and str(person_id) in G:
                G.add_edge(
                    f"rotation:{rot_id}",
                    str(person_id),
                    relationship="uses",
                    weight=count,
                )

        logger.info(
            f"Built dependency graph: {G.number_of_nodes()} nodes, "
            f"{G.number_of_edges()} edges"
        )

        self._dependency_graph = G
        return G

    def compute_keystoneness_score(
        self,
        entity_id: str,
        graph: "nx.DiGraph",
    ) -> float:
        """
        Compute keystoneness score for an entity.

        Keystoneness = Impact / Abundance
        - Impact: How much is affected by removal (betweenness, out-degree)
        - Abundance: How much presence in system (assignments, connections)

        High keystoneness = low abundance but high impact (keystone)
        Low keystoneness = impact proportional to abundance (not keystone)

        Args:
            entity_id: Entity to analyze
            graph: Dependency graph

        Returns:
            Keystoneness score (0.0-1.0)
        """
        if not graph or entity_id not in graph:
            return 0.0

        # Calculate impact metrics
        out_degree = graph.out_degree(entity_id)  # What depends on this
        in_degree = graph.in_degree(entity_id)  # What this depends on

        # Betweenness centrality: how often on critical paths
        try:
            betweenness = nx.betweenness_centrality(graph).get(entity_id, 0.0)
        except Exception:
            betweenness = 0.0

        # Abundance: normalized presence
        total_nodes = graph.number_of_nodes()
        total_edges = graph.number_of_edges()

        # Node abundance (how connected)
        node_abundance = (in_degree + out_degree) / (2 * max(total_nodes, 1))

        # Edge weight sum (how utilized)
        edge_weights = sum(
            graph[entity_id][neighbor].get("weight", 1.0)
            for neighbor in graph.successors(entity_id)
        )
        edge_abundance = edge_weights / max(total_edges, 1)

        # Combined abundance (normalized 0-1)
        abundance = (node_abundance + edge_abundance) / 2

        # Impact: combination of betweenness and out-degree
        impact = (betweenness + (out_degree / max(total_nodes, 1))) / 2

        # Keystoneness = impact / abundance (avoid division by zero)
        if abundance < 0.01:
            # Very low abundance - if has any impact, it's a keystone
            keystoneness = min(impact * 10, 1.0)
        else:
            keystoneness = min(impact / abundance, 1.0)

        return keystoneness

    def compute_functional_redundancy(
        self,
        entity_id: str,
        services: dict[UUID, list[UUID]],
    ) -> float:
        """
        Compute functional redundancy - how replaceable is this entity?

        High redundancy (>0.7): Many entities can fill same role
        Low redundancy (<0.3): Few or no substitutes available

        Args:
            entity_id: Entity to analyze
            services: Service capability mapping

        Returns:
            Redundancy score (0.0-1.0)
        """
        # Extract UUID from entity_id (might be prefixed)
        try:
            if ":" in entity_id:
                _, uuid_str = entity_id.split(":", 1)
                entity_uuid = UUID(uuid_str)
            else:
                entity_uuid = UUID(entity_id)
        except (ValueError, AttributeError):
            return 0.0

        # Count services this entity can provide
        my_services = [sid for sid, providers in services.items() if entity_uuid in providers]

        if not my_services:
            return 1.0  # Not providing services, fully redundant

        # For each service, count alternatives
        redundancy_scores = []
        for service_id in my_services:
            providers = services.get(service_id, [])
            num_alternatives = len([p for p in providers if p != entity_uuid])

            # Redundancy for this service
            if num_alternatives == 0:
                service_redundancy = 0.0  # No alternatives
            elif num_alternatives == 1:
                service_redundancy = 0.3  # Minimal backup
            elif num_alternatives == 2:
                service_redundancy = 0.6  # Moderate backup
            else:
                service_redundancy = min(0.9, 0.6 + (num_alternatives - 2) * 0.1)

            redundancy_scores.append(service_redundancy)

        # Average redundancy across services
        return statistics.mean(redundancy_scores)

    def identify_keystone_resources(
        self,
        faculty: list,
        residents: list,
        assignments: list,
        services: dict[UUID, list[UUID]],
        rotations: dict[UUID, dict],
        threshold: Optional[float] = None,
    ) -> list[KeystoneResource]:
        """
        Identify keystone resources in the scheduling ecosystem.

        Args:
            faculty: List of faculty members
            residents: List of residents
            assignments: Current assignments
            services: Service capability mapping
            rotations: Rotation metadata
            threshold: Keystoneness threshold (uses default if None)

        Returns:
            List of KeystoneResource sorted by keystoneness score
        """
        threshold = threshold or self.keystone_threshold

        # Build dependency graph
        graph = self.build_dependency_graph(
            faculty, residents, assignments, services, rotations
        )

        if not graph:
            logger.warning("Cannot identify keystones without dependency graph")
            return []

        keystones = []
        all_entities = list(faculty) + list(residents)

        for entity in all_entities:
            entity_id = entity.id if hasattr(entity, "id") else entity["id"]
            entity_name = getattr(entity, "name", str(entity_id))
            entity_type = (
                EntityType.FACULTY
                if entity in faculty
                else EntityType.RESIDENT
            )

            entity_str = str(entity_id)

            # Calculate metrics
            keystoneness = self.compute_keystoneness_score(entity_str, graph)
            redundancy = self.compute_functional_redundancy(entity_str, services)

            # Skip if below threshold
            if keystoneness < threshold:
                continue

            # Dependency analysis
            out_degree = graph.out_degree(entity_str)
            in_degree = graph.in_degree(entity_str)

            # Simulate removal to get cascade depth
            cascade = self.simulate_removal_cascade(
                entity_id, faculty, residents, assignments, services, rotations
            )

            # Identify unique and shared capabilities
            my_services = [
                sid for sid, providers in services.items() if entity_id in providers
            ]
            unique_caps = [
                str(sid)
                for sid in my_services
                if len(services.get(sid, [])) == 1
            ]
            shared_caps = [
                str(sid)
                for sid in my_services
                if len(services.get(sid, [])) > 1
            ]

            # Calculate metrics
            abundance = (in_degree + out_degree) / (2 * max(graph.number_of_nodes(), 1))
            impact = cascade.coverage_loss
            replacement_difficulty = 1.0 - redundancy

            # Determine risk level
            if cascade.is_catastrophic:
                risk_level = KeystoneRiskLevel.CATASTROPHIC
            elif keystoneness > 0.8 and redundancy < 0.2:
                risk_level = KeystoneRiskLevel.CRITICAL
            elif keystoneness > 0.7 or redundancy < 0.3:
                risk_level = KeystoneRiskLevel.HIGH
            elif keystoneness > 0.6:
                risk_level = KeystoneRiskLevel.MODERATE
            else:
                risk_level = KeystoneRiskLevel.LOW

            # Build risk factors
            risk_factors = []
            if len(unique_caps) > 0:
                risk_factors.append(f"Sole provider for {len(unique_caps)} service(s)")
            if redundancy < 0.3:
                risk_factors.append("Very low functional redundancy")
            if cascade.cascade_depth > 2:
                risk_factors.append(f"Triggers {cascade.cascade_depth}-level cascade")
            if impact > 0.3:
                risk_factors.append(f"Removal causes {impact:.0%} coverage loss")

            # Create keystone resource
            keystone = KeystoneResource(
                entity_id=entity_id,
                entity_name=entity_name,
                entity_type=entity_type,
                calculated_at=datetime.now(),
                keystoneness_score=keystoneness,
                abundance=abundance,
                impact_if_removed=impact,
                replacement_difficulty=replacement_difficulty,
                direct_dependents=out_degree,
                indirect_dependents=cascade.total_affected,
                cascade_depth=cascade.cascade_depth,
                bottleneck_score=min(keystoneness, 1.0),
                functional_redundancy=redundancy,
                unique_capabilities=unique_caps,
                shared_capabilities=shared_caps,
                risk_level=risk_level,
                risk_factors=risk_factors,
                succession_status=SuccessionStatus.NONE,
                backup_entities=[],
            )

            self.keystone_cache[entity_id] = keystone
            keystones.append(keystone)

        # Sort by keystoneness score
        keystones.sort(key=lambda k: -k.keystoneness_score)

        logger.info(f"Identified {len(keystones)} keystone resources")
        return keystones

    def simulate_removal_cascade(
        self,
        entity_id: UUID,
        faculty: list,
        residents: list,
        assignments: list,
        services: dict[UUID, list[UUID]],
        rotations: dict[UUID, dict],
        max_iterations: int = 10,
    ) -> CascadeAnalysis:
        """
        Simulate trophic cascade from removing an entity.

        Models multi-level cascade:
        1. Entity removed
        2. Services it provided become unavailable
        3. Rotations requiring those services cannot run
        4. Assignments to those rotations fail
        5. Workload redistributes, potentially overloading others

        Args:
            entity_id: Entity to remove
            faculty: Faculty list
            residents: Resident list
            assignments: Current assignments
            services: Service capability mapping
            rotations: Rotation metadata
            max_iterations: Maximum cascade steps

        Returns:
            CascadeAnalysis with detailed cascade simulation
        """
        # Find entity
        entity = None
        entity_type = EntityType.FACULTY
        for fac in faculty:
            fac_id = fac.id if hasattr(fac, "id") else fac["id"]
            if fac_id == entity_id:
                entity = fac
                entity_type = EntityType.FACULTY
                break
        if not entity:
            for res in residents:
                res_id = res.id if hasattr(res, "id") else res["id"]
                if res_id == entity_id:
                    entity = res
                    entity_type = EntityType.RESIDENT
                    break

        if not entity:
            logger.warning(f"Entity {entity_id} not found for cascade simulation")
            return CascadeAnalysis(
                removed_entity_id=entity_id,
                removed_entity_name="Unknown",
                removed_entity_type=EntityType.FACULTY,
                simulation_date=datetime.now(),
            )

        entity_name = getattr(entity, "name", str(entity_id))

        cascade = CascadeAnalysis(
            removed_entity_id=entity_id,
            removed_entity_name=entity_name,
            removed_entity_type=entity_type,
            simulation_date=datetime.now(),
        )

        # Level 0: Entity removed
        affected_at_level = {EntityType.FACULTY: [], EntityType.SERVICE: [], EntityType.ROTATION: []}
        affected_at_level[entity_type].append(entity_id)

        # Level 1: Services lost
        lost_services = []
        for service_id, providers in services.items():
            if entity_id in providers:
                remaining = [p for p in providers if p != entity_id]
                if len(remaining) == 0:
                    # Service completely lost
                    lost_services.append(service_id)

        affected_at_level[EntityType.SERVICE].extend(lost_services)

        if lost_services:
            cascade.add_cascade_step(
                level=1,
                affected_entities=lost_services,
                affected_types={EntityType.SERVICE: len(lost_services)},
                reason=f"Services have no remaining providers after {entity_name} removal",
            )

        # Level 2: Rotations affected
        affected_rotations = []
        for rot_id, rot_data in rotations.items():
            required_services = rot_data.get("required_services", [])
            # Check if any required service is lost
            if any(sid in lost_services for sid in required_services):
                affected_rotations.append(rot_id)

        affected_at_level[EntityType.ROTATION].extend(affected_rotations)

        if affected_rotations:
            cascade.add_cascade_step(
                level=2,
                affected_entities=affected_rotations,
                affected_types={EntityType.ROTATION: len(affected_rotations)},
                reason="Rotations cannot run without required services",
            )

        # Level 3: Assignments lost
        affected_assignments = 0
        total_assignments = len(assignments)

        for a in assignments:
            person_id = getattr(a, "person_id", a.get("person_id"))
            rot_id = getattr(a, "rotation_template_id", a.get("rotation_template_id"))

            # Assignment affected if:
            # 1. Assigned to removed entity
            # 2. Rotation is affected
            if person_id == entity_id or rot_id in affected_rotations:
                affected_assignments += 1

        cascade.affected_assignments = affected_assignments
        cascade.coverage_loss = (
            affected_assignments / total_assignments if total_assignments > 0 else 0.0
        )
        cascade.is_catastrophic = cascade.coverage_loss > 0.5

        # Count total affected
        cascade.total_affected = sum(
            len(entities) for entities in affected_at_level.values()
        )
        cascade.affected_entities = affected_at_level

        # Estimate recovery time (heuristic)
        if cascade.is_catastrophic:
            cascade.recovery_time_days = 90  # Major restructure needed
        elif cascade.coverage_loss > 0.3:
            cascade.recovery_time_days = 30  # Significant adjustments
        elif cascade.coverage_loss > 0.1:
            cascade.recovery_time_days = 7  # Minor adjustments
        else:
            cascade.recovery_time_days = 1  # Quick fix

        # Amplification factor
        initial_impact = 1  # One entity removed
        final_impact = cascade.total_affected
        cascade.amplification_factor = final_impact / max(initial_impact, 1)

        # Cache simulation
        self.cascade_simulations[entity_id] = cascade

        logger.debug(
            f"Cascade simulation for {entity_name}: "
            f"{cascade.total_affected} affected, "
            f"{cascade.coverage_loss:.1%} coverage loss"
        )

        return cascade

    def recommend_succession_plan(
        self,
        keystone: KeystoneResource,
        all_entities: list,
        services: dict[UUID, list[UUID]],
    ) -> SuccessionPlan:
        """
        Generate succession plan for a keystone resource.

        Identifies best backup candidates and training requirements
        to reduce dependency on keystone.

        Args:
            keystone: Keystone resource to plan succession for
            all_entities: All available entities (faculty + residents)
            services: Service capability mapping

        Returns:
            SuccessionPlan with ranked backups and training requirements
        """
        # Find what services this keystone provides
        keystone_services = [
            sid
            for sid, providers in services.items()
            if keystone.entity_id in providers
        ]

        # Find potential backup candidates
        backup_candidates = []

        for entity in all_entities:
            entity_id = entity.id if hasattr(entity, "id") else entity["id"]
            entity_name = getattr(entity, "name", str(entity_id))

            # Don't suggest self as backup
            if entity_id == keystone.entity_id:
                continue

            # Calculate suitability score
            # How many of keystone's services can they already do?
            entity_services = [
                sid for sid, providers in services.items() if entity_id in providers
            ]
            overlap = len(set(keystone_services) & set(entity_services))

            if len(keystone_services) > 0:
                suitability = overlap / len(keystone_services)
            else:
                suitability = 0.0

            # Bonus for already providing related services
            if overlap > 0:
                suitability += 0.2

            suitability = min(suitability, 1.0)

            if suitability > 0.0:
                backup_candidates.append((entity_id, entity_name, suitability))

        # Sort by suitability
        backup_candidates.sort(key=lambda x: -x[2])

        # Identify training needs (services keystone provides but candidate doesn't)
        training_needed = []
        if backup_candidates:
            best_candidate_id = backup_candidates[0][0]
            candidate_services = [
                sid
                for sid, providers in services.items()
                if best_candidate_id in providers
            ]
            training_needed = [
                str(sid)
                for sid in keystone_services
                if sid not in candidate_services
            ]

        # Estimate training hours (rough heuristic)
        estimated_hours = len(training_needed) * 40  # 40 hours per skill

        # Determine priority based on risk level
        priority_map = {
            KeystoneRiskLevel.CATASTROPHIC: "urgent",
            KeystoneRiskLevel.CRITICAL: "urgent",
            KeystoneRiskLevel.HIGH: "high",
            KeystoneRiskLevel.MODERATE: "medium",
            KeystoneRiskLevel.LOW: "low",
        }
        priority = priority_map.get(keystone.risk_level, "medium")

        # Create timeline
        timeline = {}
        if priority == "urgent":
            timeline["training_start"] = date.today()
            timeline["training_complete"] = date.today().replace(
                year=date.today().year + (3 if estimated_hours > 80 else 1)
            )
        else:
            # More relaxed timeline for lower priority
            timeline["training_start"] = date.today().replace(
                month=(date.today().month % 12) + 1
            )
            timeline["training_complete"] = date.today().replace(
                year=date.today().year + 1
            )

        # Interim measures
        interim = []
        if len(keystone.unique_capabilities) > 0:
            interim.append("Document procedures for unique capabilities")
        if keystone.functional_redundancy < 0.3:
            interim.append("Increase cross-coverage with related services")
        if keystone.cascade_depth > 1:
            interim.append("Create fallback rotations that don't require this resource")

        # Risk reduction estimate
        if backup_candidates:
            risk_reduction = min(backup_candidates[0][2] * 0.8, 0.9)
        else:
            risk_reduction = 0.0

        plan = SuccessionPlan(
            id=uuid4(),
            keystone_entity_id=keystone.entity_id,
            keystone_entity_name=keystone.entity_name,
            keystone_entity_type=keystone.entity_type,
            created_at=datetime.now(),
            backup_candidates=backup_candidates[:5],  # Top 5
            cross_training_needed=training_needed,
            estimated_training_hours=estimated_hours,
            training_priority=priority,
            timeline=timeline,
            status=SuccessionStatus.PLANNED,
            assigned_trainers=[],
            interim_measures=interim,
            risk_reduction=risk_reduction,
        )

        self.succession_plans[keystone.entity_id] = plan

        logger.info(
            f"Created succession plan for {keystone.entity_name}: "
            f"{len(backup_candidates)} candidates, "
            f"{estimated_hours}h training needed"
        )

        return plan

    def get_keystone_summary(self) -> dict:
        """Get summary of keystone analysis."""
        keystones = list(self.keystone_cache.values())

        return {
            "last_analysis": (
                self._last_analysis.isoformat() if self._last_analysis else None
            ),
            "total_keystones": len(keystones),
            "by_risk_level": {
                "catastrophic": sum(
                    1 for k in keystones if k.risk_level == KeystoneRiskLevel.CATASTROPHIC
                ),
                "critical": sum(
                    1 for k in keystones if k.risk_level == KeystoneRiskLevel.CRITICAL
                ),
                "high": sum(
                    1 for k in keystones if k.risk_level == KeystoneRiskLevel.HIGH
                ),
                "moderate": sum(
                    1 for k in keystones if k.risk_level == KeystoneRiskLevel.MODERATE
                ),
                "low": sum(
                    1 for k in keystones if k.risk_level == KeystoneRiskLevel.LOW
                ),
            },
            "single_points_of_failure": sum(
                1 for k in keystones if k.is_single_point_of_failure
            ),
            "average_keystoneness": (
                statistics.mean([k.keystoneness_score for k in keystones])
                if keystones
                else 0.0
            ),
            "succession_plans": {
                "total": len(self.succession_plans),
                "by_status": {
                    "none": sum(
                        1
                        for p in self.succession_plans.values()
                        if p.status == SuccessionStatus.NONE
                    ),
                    "planned": sum(
                        1
                        for p in self.succession_plans.values()
                        if p.status == SuccessionStatus.PLANNED
                    ),
                    "in_progress": sum(
                        1
                        for p in self.succession_plans.values()
                        if p.status == SuccessionStatus.IN_PROGRESS
                    ),
                    "completed": sum(
                        1
                        for p in self.succession_plans.values()
                        if p.status == SuccessionStatus.COMPLETED
                    ),
                },
            },
        }

    def get_top_keystones(self, n: int = 5) -> list[KeystoneResource]:
        """Get top N most critical keystones."""
        keystones = list(self.keystone_cache.values())
        return sorted(keystones, key=lambda k: -k.keystoneness_score)[:n]
