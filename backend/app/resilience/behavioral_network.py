"""
Behavioral Network Analysis (Counter-Insurgency / Forensic Accounting Patterns).

The official org chart shows formal authority. The "shadow org chart" reveals
who actually holds power - who can get things done, who absorbs the pain,
who games the system.

Key Principles (from COIN doctrine):
- Formal authority != actual influence
- Map the "human terrain" to find warlords and pacifiers
- Protect the stabilizers, isolate the destabilizers
- Network behavior reveals what policy cannot see

Key Principles (from Forensic Accounting):
- Compliance != contribution
- Time-in-seat != burden-carried
- Patterns of evasion emerge over time
- Fairness requires weighting, not just counting

This module implements:
1. Swap Network Analysis - Who trades with whom, who wins/loses
2. Shadow Org Chart - Informal power structures from behavior
3. Burden Equity - Fair distribution of difficult work
4. Martyr Protection - Auto-protect over-givers from themselves
5. Gamer Detection - Flag systematic burden evasion (for visibility, not punishment)
"""

import logging
import statistics
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

logger = logging.getLogger(__name__)


# =============================================================================
# Enums and Constants
# =============================================================================


class BehavioralRole(str, Enum):
    """Informal roles revealed by swap behavior."""

    NEUTRAL = "neutral"  # Normal swap behavior
    POWER_BROKER = "power_broker"  # Swaps always approved, others seek them out
    MARTYR = "martyr"  # Always absorbs bad shifts, rarely swaps away
    EVADER = "evader"  # Systematically avoids difficult shifts
    ISOLATE = "isolate"  # Never participates in swap network
    STABILIZER = "stabilizer"  # Flexible, helps balance the system


class BurdenCategory(str, Enum):
    """Categories of shift burden."""

    MINIMAL = "minimal"  # Admin, easy clinics
    LOW = "low"  # Standard daytime
    MODERATE = "moderate"  # Busy daytime, early AM
    HIGH = "high"  # Evening, weekend day
    SEVERE = "severe"  # Night, weekend night
    EXTREME = "extreme"  # Holiday, on-call, ICU night


class EquityStatus(str, Enum):
    """Status of burden equity for a person."""

    BALANCED = "balanced"  # Within 1 std dev of mean
    LIGHT = "light"  # >1 std dev below mean (carrying less)
    HEAVY = "heavy"  # >1 std dev above mean (carrying more)
    VERY_LIGHT = "very_light"  # >2 std dev below mean (possible evasion)
    CRUSHING = "crushing"  # >2 std dev above mean (burnout risk)


class ProtectionLevel(str, Enum):
    """Protection level for martyrs."""

    NONE = "none"  # No protection needed
    MONITORING = "monitoring"  # Watch for over-volunteering
    SOFT_LIMIT = "soft_limit"  # Warn when taking extra burden
    HARD_LIMIT = "hard_limit"  # Block additional burden absorption

    # =============================================================================
    # Burden Weighting
    # =============================================================================

    # Default burden weights (can be customized per institution)


DEFAULT_BURDEN_WEIGHTS = {
    # Time of day
    "day": 1.0,
    "evening": 1.5,
    "night": 2.5,
    "overnight": 3.0,
    # Day of week
    "weekday": 1.0,
    "friday": 1.2,
    "saturday": 1.8,
    "sunday": 2.0,
    "holiday": 3.0,
    # Shift type
    "clinic": 0.8,
    "inpatient": 1.2,
    "icu": 1.8,
    "or": 1.5,
    "ed": 1.6,
    "on_call": 2.0,
    "admin": 0.3,
    "conference": 0.4,
    "teaching": 0.6,
    # Combiners (multiplicative)
    "weekend_night": 3.5,
    "holiday_night": 4.0,
    "icu_night": 4.0,
}


@dataclass
class ShiftBurden:
    """Burden calculation for a single shift."""

    shift_id: UUID
    faculty_id: UUID
    date: datetime
    shift_type: str
    raw_hours: float
    burden_weight: float
    weighted_burden: float  # raw_hours * burden_weight
    category: BurdenCategory
    factors: list[str] = field(default_factory=list)  # What contributed to weight


@dataclass
class FacultyBurdenProfile:
    """Comprehensive burden profile for a faculty member."""

    faculty_id: UUID
    faculty_name: str
    period_start: datetime
    period_end: datetime
    calculated_at: datetime

    # Raw metrics
    total_hours: float = 0.0
    total_shifts: int = 0
    shift_breakdown: dict[str, int] = field(default_factory=dict)  # type -> count

    # Burden metrics
    total_burden: float = 0.0
    burden_per_hour: float = 0.0  # efficiency of burden carrying
    high_burden_shifts: int = 0  # severe/extreme shifts

    # Equity assessment
    equity_status: EquityStatus = EquityStatus.BALANCED
    std_devs_from_mean: float = 0.0

    # Behavioral flags
    behavioral_role: BehavioralRole = BehavioralRole.NEUTRAL
    protection_level: ProtectionLevel = ProtectionLevel.NONE

    # =============================================================================
    # Swap Network Analysis
    # =============================================================================


@dataclass
class SwapEdge:
    """An edge in the swap network graph."""

    source_id: UUID
    target_id: UUID
    swap_count: int = 0
    source_initiated: int = 0  # Source asked target
    target_initiated: int = 0  # Target asked source
    burden_flow: float = 0.0  # Net burden transferred (+ = source gave to target)
    success_rate: float = 1.0  # What % of attempted swaps succeeded


@dataclass
class SwapNetworkNode:
    """A node in the swap network (faculty member)."""

    faculty_id: UUID
    faculty_name: str

    # Network metrics
    degree: int = 0  # Number of unique swap partners
    in_degree: int = 0  # Times asked to take swaps
    out_degree: int = 0  # Times initiated swap requests
    swap_count: int = 0  # Total swaps involved in

    # Burden flow (positive = net giver, negative = net receiver)
    net_burden_flow: float = 0.0
    burden_absorbed: float = 0.0  # Total burden taken from others
    burden_offloaded: float = 0.0  # Total burden given to others

    # Success metrics
    requests_made: int = 0
    requests_granted: int = 0
    requests_received: int = 0
    requests_accepted: int = 0

    # Derived metrics
    approval_rate: float = 0.0  # How often their requests are granted
    acceptance_rate: float = 0.0  # How often they accept others' requests

    # Behavioral classification
    behavioral_role: BehavioralRole = BehavioralRole.NEUTRAL
    role_confidence: float = 0.0


@dataclass
class SwapNetworkAnalysis:
    """Complete swap network analysis."""

    analyzed_at: datetime
    period_start: datetime
    period_end: datetime
    total_swaps: int
    total_faculty: int

    # Network statistics
    network_density: float = 0.0  # Actual edges / possible edges
    average_degree: float = 0.0
    clustering_coefficient: float = 0.0

    # Role distributions
    power_brokers: list[UUID] = field(default_factory=list)
    martyrs: list[UUID] = field(default_factory=list)
    evaders: list[UUID] = field(default_factory=list)
    isolates: list[UUID] = field(default_factory=list)
    stabilizers: list[UUID] = field(default_factory=list)

    # Risk assessment
    martyr_burnout_risk: list[UUID] = field(default_factory=list)
    equity_concerns: list[str] = field(default_factory=list)

    # =============================================================================
    # Behavioral Network Analyzer
    # =============================================================================


class BehavioralNetworkAnalyzer:
    """
    Analyzes swap behavior and workload patterns to reveal the "shadow org chart."

    This isn't about catching cheaters - it's about understanding actual
    dynamics so the system can protect martyrs, ensure fairness, and
    surface patterns that formal metrics miss.
    """

    def __init__(
        self,
        burden_weights: dict[str, float] | None = None,
        martyr_threshold: float = 1.5,  # std devs above mean burden
        evader_threshold: float = -1.5,  # std devs below mean burden
        min_swaps_for_classification: int = 3,
    ) -> None:
        self.burden_weights = burden_weights or DEFAULT_BURDEN_WEIGHTS
        self.martyr_threshold = martyr_threshold
        self.evader_threshold = evader_threshold
        self.min_swaps = min_swaps_for_classification

        # Network state
        self.nodes: dict[UUID, SwapNetworkNode] = {}
        self.edges: dict[tuple[UUID, UUID], SwapEdge] = {}
        self.burden_profiles: dict[UUID, FacultyBurdenProfile] = {}

        # -------------------------------------------------------------------------
        # Burden Calculation
        # -------------------------------------------------------------------------

    def calculate_shift_burden(
        self,
        shift_id: UUID,
        faculty_id: UUID,
        date: datetime,
        shift_type: str,
        hours: float,
        is_weekend: bool = False,
        is_holiday: bool = False,
        is_night: bool = False,
        custom_factors: list[str] | None = None,
    ) -> ShiftBurden:
        """
        Calculate the weighted burden of a single shift.

        The key insight: 8 hours of Monday clinic != 8 hours of Saturday ICU night.
        Burden weighting makes this visible.
        """
        factors = custom_factors or []
        weight = 1.0

        # Base shift type weight
        if shift_type.lower() in self.burden_weights:
            weight *= self.burden_weights[shift_type.lower()]
            factors.append(f"shift_type:{shift_type}")

            # Time modifiers
        if is_night:
            weight *= self.burden_weights.get("night", 2.5)
            factors.append("night")

        if is_weekend and is_night:
            # Use combined weight if available, else multiplicative
            if "weekend_night" in self.burden_weights:
                weight = self.burden_weights["weekend_night"]
                factors.append("weekend_night")
            else:
                weight *= self.burden_weights.get("saturday", 1.8)
                factors.append("weekend")
        elif is_weekend:
            day_name = date.strftime("%A").lower()
            if day_name in self.burden_weights:
                weight *= self.burden_weights[day_name]
            else:
                weight *= self.burden_weights.get("saturday", 1.8)
            factors.append("weekend")

        if is_holiday:
            if is_night and "holiday_night" in self.burden_weights:
                weight = self.burden_weights["holiday_night"]
                factors.append("holiday_night")
            else:
                weight *= self.burden_weights.get("holiday", 3.0)
                factors.append("holiday")

                # Calculate weighted burden
        weighted = hours * weight

        # Categorize
        if weighted < 5:
            category = BurdenCategory.MINIMAL
        elif weighted < 10:
            category = BurdenCategory.LOW
        elif weighted < 15:
            category = BurdenCategory.MODERATE
        elif weighted < 25:
            category = BurdenCategory.HIGH
        elif weighted < 40:
            category = BurdenCategory.SEVERE
        else:
            category = BurdenCategory.EXTREME

        return ShiftBurden(
            shift_id=shift_id,
            faculty_id=faculty_id,
            date=date,
            shift_type=shift_type,
            raw_hours=hours,
            burden_weight=weight,
            weighted_burden=weighted,
            category=category,
            factors=factors,
        )

    def calculate_faculty_burden_profile(
        self,
        faculty_id: UUID,
        faculty_name: str,
        shifts: list[ShiftBurden],
        period_start: datetime,
        period_end: datetime,
        all_faculty_burdens: list[float] | None = None,
    ) -> FacultyBurdenProfile:
        """
        Calculate comprehensive burden profile for a faculty member.

        If all_faculty_burdens is provided, calculates equity status
        relative to the group.
        """
        profile = FacultyBurdenProfile(
            faculty_id=faculty_id,
            faculty_name=faculty_name,
            period_start=period_start,
            period_end=period_end,
            calculated_at=datetime.now(),
        )

        if not shifts:
            return profile

            # Aggregate shifts
        profile.total_shifts = len(shifts)
        profile.total_hours = sum(s.raw_hours for s in shifts)
        profile.total_burden = sum(s.weighted_burden for s in shifts)

        # Breakdown by type
        for shift in shifts:
            shift_type = shift.shift_type
            profile.shift_breakdown[shift_type] = (
                profile.shift_breakdown.get(shift_type, 0) + 1
            )

            # High burden count
        profile.high_burden_shifts = sum(
            1
            for s in shifts
            if s.category in (BurdenCategory.SEVERE, BurdenCategory.EXTREME)
        )

        # Burden per hour (efficiency metric)
        if profile.total_hours > 0:
            profile.burden_per_hour = profile.total_burden / profile.total_hours

            # Equity assessment (if group data provided)
        if all_faculty_burdens and len(all_faculty_burdens) > 1:
            mean_burden = statistics.mean(all_faculty_burdens)
            std_burden = statistics.stdev(all_faculty_burdens)

            if std_burden > 0:
                profile.std_devs_from_mean = (
                    profile.total_burden - mean_burden
                ) / std_burden

                if profile.std_devs_from_mean > 2:
                    profile.equity_status = EquityStatus.CRUSHING
                elif profile.std_devs_from_mean > 1:
                    profile.equity_status = EquityStatus.HEAVY
                elif profile.std_devs_from_mean < -2:
                    profile.equity_status = EquityStatus.VERY_LIGHT
                elif profile.std_devs_from_mean < -1:
                    profile.equity_status = EquityStatus.LIGHT
                else:
                    profile.equity_status = EquityStatus.BALANCED

        return profile

        # -------------------------------------------------------------------------
        # Swap Network Analysis
        # -------------------------------------------------------------------------

    def record_swap(
        self,
        source_id: UUID,
        source_name: str,
        target_id: UUID,
        target_name: str,
        initiated_by: UUID,
        source_burden: float,
        target_burden: float,
        was_successful: bool,
    ) -> None:
        """
        Record a swap attempt in the network.

        Args:
            source_id: Faculty giving away their shift
            source_name: Name of source faculty
            target_id: Faculty receiving the shift
            target_name: Name of target faculty
            initiated_by: Who requested the swap
            source_burden: Burden weight of source's original shift
            target_burden: Burden weight of what target gave in exchange (0 if absorb)
            was_successful: Whether the swap completed
        """
        # Ensure nodes exist
        if source_id not in self.nodes:
            self.nodes[source_id] = SwapNetworkNode(
                faculty_id=source_id,
                faculty_name=source_name,
            )
        if target_id not in self.nodes:
            self.nodes[target_id] = SwapNetworkNode(
                faculty_id=target_id,
                faculty_name=target_name,
            )

        source_node = self.nodes[source_id]
        target_node = self.nodes[target_id]

        # Ensure edge exists
        edge_key = tuple(sorted([source_id, target_id]))
        if edge_key not in self.edges:
            self.edges[edge_key] = SwapEdge(
                source_id=edge_key[0],
                target_id=edge_key[1],
            )
        edge = self.edges[edge_key]

        # Update edge
        edge.swap_count += 1
        if initiated_by == source_id:
            edge.source_initiated += 1
        else:
            edge.target_initiated += 1

            # Calculate burden flow (positive = source gave more burden to target)
        burden_transferred = source_burden - target_burden
        if source_id == edge_key[0]:
            edge.burden_flow += burden_transferred
        else:
            edge.burden_flow -= burden_transferred

            # Update nodes
        if initiated_by == source_id:
            source_node.requests_made += 1
            target_node.requests_received += 1
            if was_successful:
                source_node.requests_granted += 1
                target_node.requests_accepted += 1
        else:
            target_node.requests_made += 1
            source_node.requests_received += 1
            if was_successful:
                target_node.requests_granted += 1
                source_node.requests_accepted += 1

        if was_successful:
            source_node.swap_count += 1
            target_node.swap_count += 1
            source_node.burden_offloaded += source_burden
            target_node.burden_absorbed += source_burden
            source_node.burden_absorbed += target_burden
            target_node.burden_offloaded += target_burden
            source_node.net_burden_flow -= burden_transferred
            target_node.net_burden_flow += burden_transferred

    def analyze_network(
        self,
        period_start: datetime,
        period_end: datetime,
    ) -> SwapNetworkAnalysis:
        """
        Analyze the swap network to identify behavioral roles.

        Returns comprehensive analysis including:
        - Network statistics
        - Role classifications
        - Risk assessments
        """
        analysis = SwapNetworkAnalysis(
            analyzed_at=datetime.now(),
            period_start=period_start,
            period_end=period_end,
            total_swaps=sum(e.swap_count for e in self.edges.values()),
            total_faculty=len(self.nodes),
        )

        if not self.nodes:
            return analysis

            # Calculate network statistics
        n = len(self.nodes)
        possible_edges = n * (n - 1) / 2
        actual_edges = len(self.edges)
        analysis.network_density = (
            actual_edges / possible_edges if possible_edges > 0 else 0
        )

        # Calculate degrees
        for node in self.nodes.values():
            node.degree = sum(
                1 for edge_key in self.edges if node.faculty_id in edge_key
            )
            node.in_degree = node.requests_received
            node.out_degree = node.requests_made

            # Calculate rates
            if node.requests_made > 0:
                node.approval_rate = node.requests_granted / node.requests_made
            if node.requests_received > 0:
                node.acceptance_rate = node.requests_accepted / node.requests_received

        degrees = [n.degree for n in self.nodes.values()]
        analysis.average_degree = statistics.mean(degrees) if degrees else 0

        # Classify behavioral roles
        self._classify_roles()

        # Populate analysis with classified roles
        for node in self.nodes.values():
            if node.behavioral_role == BehavioralRole.POWER_BROKER:
                analysis.power_brokers.append(node.faculty_id)
            elif node.behavioral_role == BehavioralRole.MARTYR:
                analysis.martyrs.append(node.faculty_id)
            elif node.behavioral_role == BehavioralRole.EVADER:
                analysis.evaders.append(node.faculty_id)
            elif node.behavioral_role == BehavioralRole.ISOLATE:
                analysis.isolates.append(node.faculty_id)
            elif node.behavioral_role == BehavioralRole.STABILIZER:
                analysis.stabilizers.append(node.faculty_id)

                # Identify martyrs at burnout risk (high burden absorption + high swap count)
        for node in self.nodes.values():
            if node.behavioral_role == BehavioralRole.MARTYR:
                if node.burden_absorbed > 0 and node.swap_count >= self.min_swaps * 2:
                    analysis.martyr_burnout_risk.append(node.faculty_id)

                    # Generate equity concerns
        if len(analysis.martyrs) > len(self.nodes) * 0.2:
            analysis.equity_concerns.append(
                f"High martyr concentration: {len(analysis.martyrs)} of {len(self.nodes)} faculty"
            )
        if len(analysis.evaders) > len(self.nodes) * 0.15:
            analysis.equity_concerns.append(
                f"Possible burden evasion pattern: {len(analysis.evaders)} faculty consistently offloading"
            )
        if len(analysis.isolates) > len(self.nodes) * 0.3:
            analysis.equity_concerns.append(
                f"Low swap network participation: {len(analysis.isolates)} faculty not engaging"
            )

        return analysis

    def _classify_roles(self) -> None:
        """Classify each node's behavioral role."""
        if not self.nodes:
            return

            # Calculate burden flow statistics
        burden_flows = [
            n.net_burden_flow for n in self.nodes.values() if n.swap_count > 0
        ]
        if len(burden_flows) < 2:
            return

        mean_flow = statistics.mean(burden_flows)
        std_flow = statistics.stdev(burden_flows) if len(burden_flows) > 1 else 1.0

        for node in self.nodes.values():
            if node.swap_count < self.min_swaps:
                if (
                    node.swap_count == 0
                    and node.requests_made == 0
                    and node.requests_received == 0
                ):
                    node.behavioral_role = BehavioralRole.ISOLATE
                    node.role_confidence = 1.0
                continue

            burden_ratio = (
                (node.burden_absorbed / max(1.0, node.burden_offloaded))
                if node.burden_offloaded or node.burden_absorbed
                else 0
            )

            # Identify martyrs based on heavy burden absorption even in small samples
            if burden_ratio >= 2:
                node.behavioral_role = BehavioralRole.MARTYR
                node.role_confidence = min(1.0, burden_ratio / 5)
                continue

                # Calculate z-score for burden flow
            z_score = (
                (node.net_burden_flow - mean_flow) / std_flow if std_flow > 0 else 0
            )

            # Classify based on burden flow and approval patterns
            if z_score >= self.martyr_threshold:
                # Absorbs significantly more burden than average
                node.behavioral_role = BehavioralRole.MARTYR
                node.role_confidence = min(1.0, z_score / 3)
            elif z_score <= self.evader_threshold:
                # Offloads significantly more burden than average
                node.behavioral_role = BehavioralRole.EVADER
                node.role_confidence = min(1.0, abs(z_score) / 3)
            elif (
                node.approval_rate > 0.9
                and node.requests_received > node.requests_made * 2
            ):
                # High approval rate + others seek them out
                node.behavioral_role = BehavioralRole.POWER_BROKER
                node.role_confidence = node.approval_rate
            elif abs(z_score) < 0.5 and node.acceptance_rate > 0.7:
                # Balanced burden flow + helpful
                node.behavioral_role = BehavioralRole.STABILIZER
                node.role_confidence = 0.7
            else:
                node.behavioral_role = BehavioralRole.NEUTRAL
                node.role_confidence = 0.5

                # -------------------------------------------------------------------------
                # Martyr Protection
                # -------------------------------------------------------------------------

    def get_martyr_protection_level(
        self,
        faculty_id: UUID,
        current_allostatic_load: float = 0.0,
    ) -> tuple[ProtectionLevel, str]:
        """
        Determine what level of protection a faculty member needs.

        Martyrs need protection from themselves - they'll keep absorbing
        burden until they burn out. The system must say "no" for them.

        Args:
            faculty_id: Faculty to check
            current_allostatic_load: Current stress level (0-100)

        Returns:
            Tuple of (protection level, reason)
        """
        if faculty_id not in self.nodes:
            return ProtectionLevel.NONE, "Not in swap network"

        node = self.nodes[faculty_id]

        if node.behavioral_role != BehavioralRole.MARTYR:
            # Even non-martyrs might need protection at high stress
            if current_allostatic_load > 80:
                return ProtectionLevel.SOFT_LIMIT, "High allostatic load"
            return ProtectionLevel.NONE, "Not identified as martyr"

            # Martyr protection levels based on burden absorbed + stress
        if current_allostatic_load > 70:
            return (
                ProtectionLevel.HARD_LIMIT,
                f"Martyr at high stress ({current_allostatic_load:.0f}/100). "
                f"Additional burden absorption blocked.",
            )
        elif node.burden_absorbed > node.burden_offloaded * 3:
            return (
                ProtectionLevel.HARD_LIMIT,
                f"Severe burden imbalance: absorbed {node.burden_absorbed:.0f} vs "
                f"offloaded {node.burden_offloaded:.0f}. Additional absorption blocked.",
            )
        elif node.burden_absorbed > node.burden_offloaded * 2:
            return (
                ProtectionLevel.SOFT_LIMIT,
                "Significant burden imbalance. Recommend declining additional swaps.",
            )
        else:
            return (
                ProtectionLevel.MONITORING,
                "Identified as martyr pattern. Monitoring burden absorption.",
            )

    def should_block_swap(
        self,
        target_id: UUID,
        source_burden: float,
        target_current_load: float = 0.0,
    ) -> tuple[bool, str]:
        """
        Determine if a swap should be blocked to protect the target.

        The Martyr Protection feature: "Corporal, you are too valuable to
        die on this hill. Request denied."

        Args:
            target_id: Faculty who would absorb the burden
            source_burden: Burden weight of the shift being offered
            target_current_load: Target's current allostatic load

        Returns:
            Tuple of (should_block, reason)
        """
        protection_level, reason = self.get_martyr_protection_level(
            target_id, target_current_load
        )

        if protection_level == ProtectionLevel.HARD_LIMIT:
            return True, f"BLOCKED: {reason}"

        if protection_level == ProtectionLevel.SOFT_LIMIT and source_burden > 15:
            return (
                True,
                f"BLOCKED: High-burden shift ({source_burden:.0f}) declined. {reason}",
            )

        return False, ""

        # -------------------------------------------------------------------------
        # Burden Equity Analysis
        # -------------------------------------------------------------------------

    def analyze_burden_equity(
        self,
        burden_profiles: list[FacultyBurdenProfile],
    ) -> dict[str, Any]:
        """
        Analyze burden equity across all faculty.

        Returns comprehensive equity analysis including:
        - Distribution statistics
        - Outliers (both high and low)
        - Equity recommendations
        """
        if not burden_profiles:
            return {"error": "No burden profiles provided"}

        burdens = [p.total_burden for p in burden_profiles]
        hours = [p.total_hours for p in burden_profiles]

        # Basic statistics
        mean_burden = statistics.mean(burdens)
        std_burden = statistics.stdev(burdens) if len(burdens) > 1 else 0
        mean_hours = statistics.mean(hours)
        std_hours = statistics.stdev(hours) if len(hours) > 1 else 0

        # Gini coefficient (inequality measure, 0 = perfect equality, 1 = perfect inequality)
        sorted_burdens = sorted(burdens)
        n = len(sorted_burdens)
        cumulative = sum((2 * i - n - 1) * b for i, b in enumerate(sorted_burdens, 1))
        gini = cumulative / (n * sum(sorted_burdens)) if sum(sorted_burdens) > 0 else 0

        # Categorize faculty
        crushing = [
            p for p in burden_profiles if p.equity_status == EquityStatus.CRUSHING
        ]
        heavy = [p for p in burden_profiles if p.equity_status == EquityStatus.HEAVY]
        balanced = [
            p for p in burden_profiles if p.equity_status == EquityStatus.BALANCED
        ]
        light = [p for p in burden_profiles if p.equity_status == EquityStatus.LIGHT]
        very_light = [
            p for p in burden_profiles if p.equity_status == EquityStatus.VERY_LIGHT
        ]

        # Generate recommendations
        recommendations = []

        if len(crushing) > 0:
            names = [p.faculty_name for p in crushing[:3]]
            recommendations.append(
                f"CRITICAL: {len(crushing)} faculty at crushing burden levels: {', '.join(names)}"
            )

        if len(very_light) > 0 and len(crushing) > 0:
            recommendations.append(
                f"Rebalancing opportunity: {len(very_light)} faculty at very light burden "
                f"could absorb from {len(crushing)} at crushing levels"
            )

        if gini > 0.3:
            recommendations.append(
                f"High burden inequality (Gini={gini:.2f}). Consider workload redistribution."
            )

            # Check for hours vs burden discrepancy (the "forensic accounting" insight)
        for profile in burden_profiles:
            if (
                profile.total_hours > mean_hours
                and profile.total_burden < mean_burden * 0.7
            ):
                recommendations.append(
                    f"Possible burden-light pattern: {profile.faculty_name} has "
                    f"{profile.total_hours:.0f}h but only {profile.total_burden:.0f} burden "
                    f"(mean: {mean_burden:.0f})"
                )

        return {
            "mean_burden": mean_burden,
            "std_burden": std_burden,
            "mean_hours": mean_hours,
            "std_hours": std_hours,
            "gini_coefficient": gini,
            "equity_grade": self._grade_equity(gini),
            "distribution": {
                "crushing": len(crushing),
                "heavy": len(heavy),
                "balanced": len(balanced),
                "light": len(light),
                "very_light": len(very_light),
            },
            "crushing_faculty": [p.faculty_id for p in crushing],
            "very_light_faculty": [p.faculty_id for p in very_light],
            "recommendations": recommendations,
        }

    def _grade_equity(self, gini: float) -> str:
        """Grade equity based on Gini coefficient."""
        if gini < 0.1:
            return "A (Excellent equity)"
        elif gini < 0.2:
            return "B (Good equity)"
        elif gini < 0.3:
            return "C (Acceptable equity)"
        elif gini < 0.4:
            return "D (Poor equity)"
        else:
            return "F (Severe inequity)"

            # =============================================================================
            # Shadow Org Chart Service
            # =============================================================================


class ShadowOrgChartService:
    """
    High-level service for shadow org chart analysis.

    Combines swap network analysis with burden equity to provide
    a complete picture of informal organizational dynamics.
    """

    def __init__(self) -> None:
        self.analyzer = BehavioralNetworkAnalyzer()
        self.network_history: list[SwapNetworkAnalysis] = []

    def build_from_swap_records(
        self,
        swap_records: list[dict],
        burden_calculator: Callable | None = None,
    ) -> None:
        """
        Build network from swap records.

        Args:
            swap_records: List of swap records with source/target info
            burden_calculator: Optional function to calculate shift burden
        """
        for record in swap_records:
            source_burden = record.get("source_burden", 10.0)
            target_burden = record.get("target_burden", 0.0)

            if burden_calculator:
                source_burden = burden_calculator(record.get("source_shift"))
                target_burden = burden_calculator(record.get("target_shift", {}))

            self.analyzer.record_swap(
                source_id=record["source_id"],
                source_name=record.get("source_name", "Unknown"),
                target_id=record["target_id"],
                target_name=record.get("target_name", "Unknown"),
                initiated_by=record["initiated_by"],
                source_burden=source_burden,
                target_burden=target_burden,
                was_successful=record.get("status") in ("approved", "executed"),
            )

    def generate_report(
        self,
        period_start: datetime,
        period_end: datetime,
        burden_profiles: list[FacultyBurdenProfile] | None = None,
    ) -> dict[str, Any]:
        """
        Generate comprehensive shadow org chart report.

        Returns combined analysis of:
        - Swap network dynamics
        - Burden equity
        - Risk assessments
        - Recommendations
        """
        # Network analysis
        network = self.analyzer.analyze_network(period_start, period_end)
        self.network_history.append(network)

        # Burden equity (if profiles provided)
        equity_analysis = None
        if burden_profiles:
            equity_analysis = self.analyzer.analyze_burden_equity(burden_profiles)

            # Compile report
        report = {
            "generated_at": datetime.now().isoformat(),
            "period": {
                "start": period_start.isoformat(),
                "end": period_end.isoformat(),
            },
            "network_summary": {
                "total_faculty": network.total_faculty,
                "total_swaps": network.total_swaps,
                "network_density": network.network_density,
                "average_connections": network.average_degree,
            },
            "behavioral_roles": {
                "power_brokers": len(network.power_brokers),
                "martyrs": len(network.martyrs),
                "evaders": len(network.evaders),
                "stabilizers": len(network.stabilizers),
                "isolates": len(network.isolates),
            },
            "risk_flags": {
                "martyrs_at_burnout_risk": len(network.martyr_burnout_risk),
                "equity_concerns": network.equity_concerns,
            },
            "detailed_roles": {
                "power_brokers": [str(uid) for uid in network.power_brokers],
                "martyrs": [str(uid) for uid in network.martyrs],
                "martyrs_burnout_risk": [
                    str(uid) for uid in network.martyr_burnout_risk
                ],
                "evaders": [str(uid) for uid in network.evaders],
            },
        }

        if equity_analysis:
            report["burden_equity"] = equity_analysis

            # Generate actionable recommendations
        recommendations = []

        if network.martyr_burnout_risk:
            recommendations.append(
                {
                    "priority": "CRITICAL",
                    "action": "Enable martyr protection",
                    "details": f"{len(network.martyr_burnout_risk)} faculty at burnout risk need shift absorption blocked",
                }
            )

        if equity_analysis and equity_analysis.get("gini_coefficient", 0) > 0.3:
            recommendations.append(
                {
                    "priority": "HIGH",
                    "action": "Rebalance workload",
                    "details": f"Gini coefficient {equity_analysis['gini_coefficient']:.2f} indicates significant inequity",
                }
            )

        if len(network.isolates) > network.total_faculty * 0.3:
            recommendations.append(
                {
                    "priority": "MEDIUM",
                    "action": "Increase swap network participation",
                    "details": f"{len(network.isolates)} faculty not participating in swaps",
                }
            )

        report["recommendations"] = recommendations

        return report
