"""
Hub Vulnerability Analysis (Network Theory Pattern).

Scale-free networks (many connections to few "hub" nodes) are robust to random
failure but extremely vulnerable to targeted hub removal. In scheduling, hubs
are faculty members who cover many unique services or are difficult to replace.

Key Principles:
- Hub nodes have disproportionate network influence
- Random failures rarely hit hubs; targeted attacks always do
- Cross-training reduces hub concentration
- Hub protection during high-risk periods is critical

This module implements:
1. Faculty centrality scoring (betweenness, degree, eigenvector)
2. Hub identification and ranking
3. Hub protection strategies
4. Cross-training recommendations
5. Hub distribution analysis
6. Single-point-of-failure detection
"""

import logging
import statistics
from dataclasses import dataclass
from datetime import date, datetime
from enum import Enum
from uuid import UUID, uuid4

logger = logging.getLogger(__name__)

# Try to import NetworkX for advanced analysis
try:
    import networkx as nx

    HAS_NETWORKX = True
except ImportError:
    HAS_NETWORKX = False
    logger.warning("NetworkX not installed - hub analysis will use basic methods")


class HubRiskLevel(str, Enum):
    """Risk level if this hub is lost."""

    LOW = "low"  # Easy to cover, multiple backups
    MODERATE = "moderate"  # Some impact, backups available
    HIGH = "high"  # Significant impact, limited backups
    CRITICAL = "critical"  # Major disruption, no viable backups
    CATASTROPHIC = "catastrophic"  # System failure possible


class HubProtectionStatus(str, Enum):
    """Current protection status of a hub."""

    UNPROTECTED = "unprotected"  # No special measures
    MONITORED = "monitored"  # Extra attention
    PROTECTED = "protected"  # Active measures in place
    REDUNDANT = "redundant"  # Backup hub trained


class CrossTrainingPriority(str, Enum):
    """Priority for cross-training a skill."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


@dataclass
class FacultyCentrality:
    """
    Centrality metrics for a faculty member.

    Multiple centrality measures capture different aspects of importance:
    - Degree: How many connections (coverage breadth)
    - Betweenness: How often on shortest paths (bottleneck potential)
    - Eigenvector: Connected to other important nodes (influence)
    - PageRank: Probability of being "visited" (overall importance)
    """

    faculty_id: UUID
    faculty_name: str
    calculated_at: datetime

    # Centrality scores (0.0 - 1.0 normalized)
    degree_centrality: float = 0.0
    betweenness_centrality: float = 0.0
    eigenvector_centrality: float = 0.0
    pagerank: float = 0.0

    # Composite score
    composite_score: float = 0.0

    # Coverage metrics
    services_covered: int = 0
    unique_services: int = 0  # Services only this person can cover
    total_assignments: int = 0

    # Replacement difficulty (0.0 easy - 1.0 impossible)
    replacement_difficulty: float = 0.0

    def calculate_composite(self, weights: dict = None):
        """Calculate weighted composite centrality score."""
        weights = weights or {
            "degree": 0.2,
            "betweenness": 0.3,
            "eigenvector": 0.2,
            "pagerank": 0.15,
            "replacement": 0.15,
        }

        self.composite_score = (
            self.degree_centrality * weights.get("degree", 0.2)
            + self.betweenness_centrality * weights.get("betweenness", 0.3)
            + self.eigenvector_centrality * weights.get("eigenvector", 0.2)
            + self.pagerank * weights.get("pagerank", 0.15)
            + self.replacement_difficulty * weights.get("replacement", 0.15)
        )

    @property
    def risk_level(self) -> HubRiskLevel:
        """Determine risk level based on metrics."""
        if self.composite_score >= 0.8 or self.unique_services >= 3:
            return HubRiskLevel.CATASTROPHIC
        elif self.composite_score >= 0.6 or self.unique_services >= 2:
            return HubRiskLevel.CRITICAL
        elif self.composite_score >= 0.4 or self.unique_services >= 1:
            return HubRiskLevel.HIGH
        elif self.composite_score >= 0.2:
            return HubRiskLevel.MODERATE
        else:
            return HubRiskLevel.LOW

    @property
    def is_hub(self) -> bool:
        """Is this faculty member a hub?"""
        return self.composite_score >= 0.4 or self.unique_services > 0


@dataclass
class HubProfile:
    """
    Detailed profile of a hub faculty member.

    Extends centrality with actionable information.
    """

    faculty_id: UUID
    faculty_name: str
    centrality: FacultyCentrality

    # What makes them a hub
    unique_skills: list[str]
    high_demand_skills: list[str]
    bottleneck_periods: list[date]

    # Protection status
    protection_status: HubProtectionStatus
    protection_measures: list[str]
    backup_faculty: list[UUID]

    # Risk assessment
    risk_level: HubRiskLevel
    risk_factors: list[str]
    mitigation_actions: list[str]

    # Cross-training needs
    cross_training_candidates: list[tuple[UUID, str]]  # (faculty_id, skill)


@dataclass
class CrossTrainingRecommendation:
    """
    Recommendation to cross-train faculty on a skill.

    Cross-training reduces hub concentration by distributing capabilities.
    """

    id: UUID
    skill: str
    current_holders: list[UUID]
    recommended_trainees: list[UUID]
    priority: CrossTrainingPriority
    reason: str
    estimated_training_hours: int
    risk_reduction: float  # How much hub risk would decrease

    # Status
    created_at: datetime
    status: str = "pending"  # pending, approved, in_progress, completed
    started_at: datetime | None = None
    completed_at: datetime | None = None


@dataclass
class HubDistributionReport:
    """Report on hub distribution across the system."""

    generated_at: datetime

    # Hub counts
    total_faculty: int
    total_hubs: int
    catastrophic_hubs: int
    critical_hubs: int
    high_risk_hubs: int

    # Distribution metrics
    hub_concentration: float  # 0.0 spread out - 1.0 concentrated
    single_points_of_failure: int
    average_hub_score: float

    # Services
    services_with_single_provider: list[str]
    services_with_dual_coverage: list[str]
    well_covered_services: list[str]

    # Recommendations
    recommendations: list[str]
    cross_training_priorities: list[CrossTrainingRecommendation]


@dataclass
class HubProtectionPlan:
    """Plan to protect critical hubs during high-risk periods."""

    id: UUID
    hub_faculty_id: UUID
    hub_faculty_name: str
    period_start: date
    period_end: date
    reason: str

    # Protection measures
    workload_reduction: float  # 0.0 none - 1.0 complete relief
    backup_assigned: bool
    backup_faculty_ids: list[UUID]
    critical_only: bool  # Limit to critical services

    # Status
    status: str = "planned"  # planned, active, completed
    activated_at: datetime | None = None
    deactivated_at: datetime | None = None


class HubAnalyzer:
    """
    Analyzes hub vulnerability in the scheduling network.

    Identifies critical faculty members whose loss would cause
    disproportionate disruption, and recommends protection strategies.
    """

    def __init__(
        self,
        hub_threshold: float = 0.4,
        critical_hub_threshold: float = 0.6,
        use_networkx: bool = True,
    ):
        self.hub_threshold = hub_threshold
        self.critical_hub_threshold = critical_hub_threshold
        self.use_networkx = use_networkx and HAS_NETWORKX

        self.centrality_cache: dict[UUID, FacultyCentrality] = {}
        self.hub_profiles: dict[UUID, HubProfile] = {}
        self.protection_plans: dict[UUID, HubProtectionPlan] = {}
        self.cross_training_recommendations: list[CrossTrainingRecommendation] = []

        self._last_analysis: datetime | None = None

    def calculate_centrality(
        self,
        faculty: list,
        assignments: list,
        services: dict[UUID, list[UUID]],  # service_id -> faculty_ids who can cover
    ) -> list[FacultyCentrality]:
        """
        Calculate centrality scores for all faculty.

        Args:
            faculty: List of faculty objects (need id, name)
            assignments: List of assignments (need faculty_id, block_id)
            services: Dict mapping service to capable faculty

        Returns:
            List of FacultyCentrality objects sorted by composite score
        """
        self._last_analysis = datetime.now()

        if self.use_networkx:
            return self._calculate_with_networkx(faculty, assignments, services)
        else:
            return self._calculate_basic(faculty, assignments, services)

    def _calculate_with_networkx(
        self,
        faculty: list,
        assignments: list,
        services: dict[UUID, list[UUID]],
    ) -> list[FacultyCentrality]:
        """Calculate centrality using NetworkX graph algorithms."""
        # Build bipartite graph: faculty <-> services
        G = nx.Graph()

        # Add faculty nodes
        for f in faculty:
            G.add_node(
                f"faculty_{f.id}", type="faculty", name=getattr(f, "name", str(f.id))
            )

        # Add service nodes
        for service_id, capable_faculty in services.items():
            G.add_node(f"service_{service_id}", type="service")
            for fac_id in capable_faculty:
                G.add_edge(f"faculty_{fac_id}", f"service_{service_id}")

        # Add assignment edges with weight
        assignment_counts = {}
        for a in assignments:
            key = str(getattr(a, "faculty_id", a.get("faculty_id")))
            assignment_counts[key] = assignment_counts.get(key, 0) + 1

        # Calculate centrality measures
        try:
            degree_cent = nx.degree_centrality(G)
        except Exception:
            degree_cent = {}

        try:
            betweenness_cent = nx.betweenness_centrality(G)
        except Exception:
            betweenness_cent = {}

        try:
            eigenvector_cent = nx.eigenvector_centrality(G, max_iter=1000)
        except Exception:
            eigenvector_cent = {}

        try:
            pagerank_cent = nx.pagerank(G)
        except Exception:
            pagerank_cent = {}

        # Build centrality objects
        results = []

        for f in faculty:
            fac_id = f.id if hasattr(f, "id") else f["id"]
            fac_name = getattr(f, "name", str(fac_id))
            node_key = f"faculty_{fac_id}"

            # Count services this faculty can cover
            covered_services = [sid for sid, facs in services.items() if fac_id in facs]

            # Count unique services (only this person)
            unique_services = [
                sid
                for sid, facs in services.items()
                if len(facs) == 1 and fac_id in facs
            ]

            # Calculate replacement difficulty
            if len(covered_services) == 0:
                replacement_diff = 0.0
            else:
                # Average of 1/num_capable for each service
                difficulties = []
                for sid in covered_services:
                    capable = len(services.get(sid, []))
                    diff = 1.0 / capable if capable > 0 else 1.0
                    difficulties.append(diff)
                replacement_diff = statistics.mean(difficulties)

            centrality = FacultyCentrality(
                faculty_id=fac_id,
                faculty_name=fac_name,
                calculated_at=datetime.now(),
                degree_centrality=degree_cent.get(node_key, 0.0),
                betweenness_centrality=betweenness_cent.get(node_key, 0.0),
                eigenvector_centrality=eigenvector_cent.get(node_key, 0.0),
                pagerank=pagerank_cent.get(node_key, 0.0),
                services_covered=len(covered_services),
                unique_services=len(unique_services),
                total_assignments=assignment_counts.get(str(fac_id), 0),
                replacement_difficulty=replacement_diff,
            )

            centrality.calculate_composite()
            self.centrality_cache[fac_id] = centrality
            results.append(centrality)

        return sorted(results, key=lambda c: -c.composite_score)

    def _calculate_basic(
        self,
        faculty: list,
        assignments: list,
        services: dict[UUID, list[UUID]],
    ) -> list[FacultyCentrality]:
        """Calculate centrality using basic methods (no NetworkX)."""
        results = []

        # Count assignments per faculty
        assignment_counts = {}
        for a in assignments:
            fac_id = str(getattr(a, "faculty_id", a.get("faculty_id")))
            assignment_counts[fac_id] = assignment_counts.get(fac_id, 0) + 1

        max_assignments = max(assignment_counts.values()) if assignment_counts else 1

        for f in faculty:
            fac_id = f.id if hasattr(f, "id") else f["id"]
            fac_name = getattr(f, "name", str(fac_id))

            # Services covered
            covered_services = [sid for sid, facs in services.items() if fac_id in facs]

            unique_services = [
                sid
                for sid, facs in services.items()
                if len(facs) == 1 and fac_id in facs
            ]

            max_services = max(len(services), 1)

            # Basic degree centrality: services / max_services
            degree = len(covered_services) / max_services

            # Basic betweenness: unique services add betweenness
            betweenness = len(unique_services) * 0.3

            # Replacement difficulty
            if len(covered_services) == 0:
                replacement_diff = 0.0
            else:
                difficulties = []
                for sid in covered_services:
                    capable = len(services.get(sid, []))
                    diff = 1.0 / capable if capable > 0 else 1.0
                    difficulties.append(diff)
                replacement_diff = statistics.mean(difficulties)

            # Assignment-based influence
            num_assignments = assignment_counts.get(str(fac_id), 0)
            pagerank = num_assignments / max_assignments if max_assignments > 0 else 0.0

            centrality = FacultyCentrality(
                faculty_id=fac_id,
                faculty_name=fac_name,
                calculated_at=datetime.now(),
                degree_centrality=degree,
                betweenness_centrality=betweenness,
                eigenvector_centrality=degree * 0.5,  # Simplified
                pagerank=pagerank,
                services_covered=len(covered_services),
                unique_services=len(unique_services),
                total_assignments=num_assignments,
                replacement_difficulty=replacement_diff,
            )

            centrality.calculate_composite()
            self.centrality_cache[fac_id] = centrality
            results.append(centrality)

        return sorted(results, key=lambda c: -c.composite_score)

    def identify_hubs(
        self,
        centrality_scores: list[FacultyCentrality] = None,
    ) -> list[FacultyCentrality]:
        """
        Identify hub faculty members from centrality scores.

        Args:
            centrality_scores: Pre-calculated scores (uses cache if None)

        Returns:
            List of hubs sorted by composite score
        """
        scores = centrality_scores or list(self.centrality_cache.values())
        return [c for c in scores if c.is_hub]

    def create_hub_profile(
        self,
        faculty_id: UUID,
        services: dict[UUID, list[UUID]],
        service_names: dict[UUID, str] = None,
    ) -> HubProfile | None:
        """
        Create detailed profile for a hub faculty member.

        Args:
            faculty_id: Faculty to profile
            services: Service capability mapping
            service_names: Human-readable service names

        Returns:
            HubProfile or None
        """
        centrality = self.centrality_cache.get(faculty_id)
        if not centrality:
            return None

        service_names = service_names or {}

        # Find unique skills
        unique_skills = []
        high_demand = []

        for sid, capable in services.items():
            service_name = service_names.get(sid, str(sid))
            if faculty_id in capable:
                if len(capable) == 1:
                    unique_skills.append(service_name)
                elif len(capable) <= 3:
                    high_demand.append(service_name)

        # Identify backup faculty
        backup_faculty = []
        for sid, capable in services.items():
            if faculty_id in capable:
                for backup_id in capable:
                    if backup_id != faculty_id and backup_id not in backup_faculty:
                        backup_faculty.append(backup_id)

        # Build risk factors
        risk_factors = []
        if centrality.unique_services > 0:
            risk_factors.append(
                f"Single provider for {centrality.unique_services} services"
            )
        if centrality.betweenness_centrality > 0.5:
            risk_factors.append("High betweenness - critical path bottleneck")
        if centrality.replacement_difficulty > 0.7:
            risk_factors.append("Very difficult to replace")

        # Mitigation actions
        mitigation = []
        if unique_skills:
            mitigation.append(f"Cross-train backup for: {', '.join(unique_skills)}")
        if centrality.composite_score > self.critical_hub_threshold:
            mitigation.append("Implement workload protection during high-risk periods")
        if not backup_faculty:
            mitigation.append("URGENT: Train at least one backup faculty member")

        # Cross-training candidates
        cross_training = []
        for skill in unique_skills:
            # Find faculty who could learn this skill (simplified)
            for backup_id in backup_faculty[:3]:
                cross_training.append((backup_id, skill))

        profile = HubProfile(
            faculty_id=faculty_id,
            faculty_name=centrality.faculty_name,
            centrality=centrality,
            unique_skills=unique_skills,
            high_demand_skills=high_demand,
            bottleneck_periods=[],  # Would need schedule analysis
            protection_status=HubProtectionStatus.UNPROTECTED,
            protection_measures=[],
            backup_faculty=backup_faculty[:5],
            risk_level=centrality.risk_level,
            risk_factors=risk_factors,
            mitigation_actions=mitigation,
            cross_training_candidates=cross_training[:5],
        )

        self.hub_profiles[faculty_id] = profile
        return profile

    def generate_cross_training_recommendations(
        self,
        services: dict[UUID, list[UUID]],
        service_names: dict[UUID, str] = None,
        all_faculty: list[UUID] = None,
    ) -> list[CrossTrainingRecommendation]:
        """
        Generate recommendations for cross-training to reduce hub concentration.

        Args:
            services: Service capability mapping
            service_names: Human-readable service names
            all_faculty: All available faculty for training

        Returns:
            List of CrossTrainingRecommendation sorted by priority
        """
        service_names = service_names or {}
        all_faculty = all_faculty or []

        recommendations = []

        for sid, capable in services.items():
            service_name = service_names.get(sid, str(sid))

            if len(capable) == 0:
                # No one can cover - urgent
                rec = CrossTrainingRecommendation(
                    id=uuid4(),
                    skill=service_name,
                    current_holders=[],
                    recommended_trainees=all_faculty[:3],
                    priority=CrossTrainingPriority.URGENT,
                    reason="No faculty currently capable of covering this service",
                    estimated_training_hours=40,
                    risk_reduction=1.0,
                    created_at=datetime.now(),
                )
                recommendations.append(rec)

            elif len(capable) == 1:
                # Single point of failure
                other_faculty = [f for f in all_faculty if f not in capable]
                rec = CrossTrainingRecommendation(
                    id=uuid4(),
                    skill=service_name,
                    current_holders=capable.copy(),
                    recommended_trainees=other_faculty[:2],
                    priority=CrossTrainingPriority.HIGH,
                    reason="Single point of failure - only one faculty member capable",
                    estimated_training_hours=20,
                    risk_reduction=0.8,
                    created_at=datetime.now(),
                )
                recommendations.append(rec)

            elif len(capable) == 2:
                # Limited coverage
                other_faculty = [f for f in all_faculty if f not in capable]
                rec = CrossTrainingRecommendation(
                    id=uuid4(),
                    skill=service_name,
                    current_holders=capable.copy(),
                    recommended_trainees=other_faculty[:1],
                    priority=CrossTrainingPriority.MEDIUM,
                    reason="Limited coverage - only two faculty members capable",
                    estimated_training_hours=20,
                    risk_reduction=0.4,
                    created_at=datetime.now(),
                )
                recommendations.append(rec)

        # Sort by priority
        priority_order = {
            CrossTrainingPriority.URGENT: 0,
            CrossTrainingPriority.HIGH: 1,
            CrossTrainingPriority.MEDIUM: 2,
            CrossTrainingPriority.LOW: 3,
        }

        self.cross_training_recommendations = sorted(
            recommendations, key=lambda r: priority_order.get(r.priority, 99)
        )

        return self.cross_training_recommendations

    def create_protection_plan(
        self,
        hub_faculty_id: UUID,
        period_start: date,
        period_end: date,
        reason: str,
        workload_reduction: float = 0.3,
        assign_backup: bool = True,
    ) -> HubProtectionPlan | None:
        """
        Create a protection plan for a hub during a high-risk period.

        Args:
            hub_faculty_id: Hub to protect
            period_start: Protection period start
            period_end: Protection period end
            reason: Why protection is needed
            workload_reduction: How much to reduce workload (0.0-1.0)
            assign_backup: Whether to assign backup faculty

        Returns:
            HubProtectionPlan or None
        """
        profile = self.hub_profiles.get(hub_faculty_id)
        if not profile:
            # Try to get from cache
            centrality = self.centrality_cache.get(hub_faculty_id)
            if not centrality or not centrality.is_hub:
                return None
            faculty_name = centrality.faculty_name
            backup_ids = []
        else:
            faculty_name = profile.faculty_name
            backup_ids = profile.backup_faculty

        plan = HubProtectionPlan(
            id=uuid4(),
            hub_faculty_id=hub_faculty_id,
            hub_faculty_name=faculty_name,
            period_start=period_start,
            period_end=period_end,
            reason=reason,
            workload_reduction=workload_reduction,
            backup_assigned=assign_backup,
            backup_faculty_ids=backup_ids[:2] if assign_backup else [],
            critical_only=workload_reduction > 0.5,
        )

        self.protection_plans[hub_faculty_id] = plan
        logger.info(
            f"Created protection plan for hub {faculty_name} "
            f"({period_start} to {period_end})"
        )

        return plan

    def get_distribution_report(
        self,
        services: dict[UUID, list[UUID]],
        service_names: dict[UUID, str] = None,
    ) -> HubDistributionReport:
        """
        Generate report on hub distribution across the system.

        Args:
            services: Service capability mapping
            service_names: Human-readable service names

        Returns:
            HubDistributionReport
        """
        service_names = service_names or {}

        centrality_list = list(self.centrality_cache.values())

        # Count by risk level
        catastrophic = sum(
            1 for c in centrality_list if c.risk_level == HubRiskLevel.CATASTROPHIC
        )
        critical = sum(
            1 for c in centrality_list if c.risk_level == HubRiskLevel.CRITICAL
        )
        high = sum(1 for c in centrality_list if c.risk_level == HubRiskLevel.HIGH)
        total_hubs = sum(1 for c in centrality_list if c.is_hub)

        # Hub concentration (Gini-like coefficient)
        scores = [c.composite_score for c in centrality_list]
        if scores:
            mean_score = statistics.mean(scores)
            variance = statistics.variance(scores) if len(scores) > 1 else 0
            concentration = min(1.0, variance / mean_score) if mean_score > 0 else 0.0
        else:
            concentration = 0.0

        # Single points of failure
        spof = sum(1 for c in centrality_list if c.unique_services > 0)

        # Service categorization
        single_provider = []
        dual_coverage = []
        well_covered = []

        for sid, capable in services.items():
            name = service_names.get(sid, str(sid))
            if len(capable) == 1:
                single_provider.append(name)
            elif len(capable) == 2:
                dual_coverage.append(name)
            elif len(capable) >= 3:
                well_covered.append(name)

        # Build recommendations
        recommendations = []

        if catastrophic > 0:
            recommendations.append(
                f"CRITICAL: {catastrophic} catastrophic hub(s) - immediate cross-training needed"
            )

        if spof > 0:
            recommendations.append(f"WARNING: {spof} single points of failure detected")

        if concentration > 0.5:
            recommendations.append(
                "High hub concentration - skills not well distributed"
            )

        if len(single_provider) > len(services) * 0.2:
            recommendations.append(
                f"{len(single_provider)} services have single provider - expand capabilities"
            )

        if not recommendations:
            recommendations.append("Hub distribution is healthy - continue monitoring")

        # Generate cross-training priorities
        cross_training = self.generate_cross_training_recommendations(
            services, service_names, [c.faculty_id for c in centrality_list]
        )

        return HubDistributionReport(
            generated_at=datetime.now(),
            total_faculty=len(centrality_list),
            total_hubs=total_hubs,
            catastrophic_hubs=catastrophic,
            critical_hubs=critical,
            high_risk_hubs=high,
            hub_concentration=concentration,
            single_points_of_failure=spof,
            average_hub_score=statistics.mean(scores) if scores else 0.0,
            services_with_single_provider=single_provider,
            services_with_dual_coverage=dual_coverage,
            well_covered_services=well_covered,
            recommendations=recommendations,
            cross_training_priorities=cross_training[:10],
        )

    def get_hub_status(self) -> dict:
        """Get summary status of hub analysis."""
        centrality_list = list(self.centrality_cache.values())
        hubs = [c for c in centrality_list if c.is_hub]

        return {
            "last_analysis": self._last_analysis.isoformat()
            if self._last_analysis
            else None,
            "total_faculty_analyzed": len(centrality_list),
            "total_hubs": len(hubs),
            "hubs_by_risk": {
                "catastrophic": sum(
                    1 for c in hubs if c.risk_level == HubRiskLevel.CATASTROPHIC
                ),
                "critical": sum(
                    1 for c in hubs if c.risk_level == HubRiskLevel.CRITICAL
                ),
                "high": sum(1 for c in hubs if c.risk_level == HubRiskLevel.HIGH),
                "moderate": sum(
                    1 for c in hubs if c.risk_level == HubRiskLevel.MODERATE
                ),
            },
            "active_protection_plans": len(self.protection_plans),
            "pending_cross_training": sum(
                1 for r in self.cross_training_recommendations if r.status == "pending"
            ),
        }

    def get_top_hubs(self, n: int = 5) -> list[FacultyCentrality]:
        """Get top N most critical hubs."""
        centrality_list = list(self.centrality_cache.values())
        return sorted(centrality_list, key=lambda c: -c.composite_score)[:n]

    def activate_protection_plan(self, plan_id: UUID):
        """Activate a protection plan."""
        for _fac_id, plan in self.protection_plans.items():
            if plan.id == plan_id:
                plan.status = "active"
                plan.activated_at = datetime.now()
                logger.info(f"Activated protection plan {plan_id}")
                return

    def deactivate_protection_plan(self, plan_id: UUID):
        """Deactivate a protection plan."""
        for _fac_id, plan in self.protection_plans.items():
            if plan.id == plan_id:
                plan.status = "completed"
                plan.deactivated_at = datetime.now()
                logger.info(f"Deactivated protection plan {plan_id}")
                return
