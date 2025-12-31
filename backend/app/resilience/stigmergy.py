"""
Stigmergy and Swarm Intelligence (Biology/AI Pattern).

Individual agents following simple rules can collectively solve complex problems
through indirect coordination. Ants find shortest paths without central planning
by depositing and following pheromone trails.

Key Principles:
- Indirect coordination through environment modification
- Positive feedback: successful paths get stronger
- Negative feedback: trails evaporate over time (recency matters)
- Emergent optimization: global patterns from local rules
- No central coordinator bottleneck

This module implements:
1. Preference trails - faculty preferences recorded as "pheromones"
2. Trail evaporation - old preferences fade
3. Collective preference aggregation
4. Trail reinforcement - satisfaction strengthens trails
5. Conflict resolution through trail strength
6. Emergent schedule patterns
"""

import logging
import math
import statistics
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

logger = logging.getLogger(__name__)


class TrailType(str, Enum):
    """Types of preference trails."""

    PREFERENCE = "preference"  # Faculty prefers this slot
    AVOIDANCE = "avoidance"  # Faculty avoids this slot
    SWAP_AFFINITY = "swap_affinity"  # Willing to swap with specific person
    WORKLOAD = "workload"  # Preferred workload pattern
    SEQUENCE = "sequence"  # Preferred assignment sequences


class TrailStrength(str, Enum):
    """Categorical strength of a trail."""

    VERY_WEAK = "very_weak"  # 0.0 - 0.2
    WEAK = "weak"  # 0.2 - 0.4
    MODERATE = "moderate"  # 0.4 - 0.6
    STRONG = "strong"  # 0.6 - 0.8
    VERY_STRONG = "very_strong"  # 0.8 - 1.0


class SignalType(str, Enum):
    """Types of behavioral signals that update trails."""

    EXPLICIT_PREFERENCE = "explicit_preference"  # User explicitly stated
    ACCEPTED_ASSIGNMENT = "accepted_assignment"  # Accepted without complaint
    REQUESTED_SWAP = "requested_swap"  # Tried to swap away
    COMPLETED_SWAP = "completed_swap"  # Successful swap
    DECLINED_OFFER = "declined_offer"  # Rejected an offer
    HIGH_SATISFACTION = "high_satisfaction"  # Reported satisfaction
    LOW_SATISFACTION = "low_satisfaction"  # Reported dissatisfaction
    PATTERN_DETECTED = "pattern_detected"  # System detected pattern


@dataclass
class PreferenceTrail:
    """
    A pheromone-like trail representing a preference pattern.

    Trails accumulate strength through repeated signals and
    decay over time through evaporation.
    """

    id: UUID
    faculty_id: UUID
    trail_type: TrailType

    # What the trail is about
    slot_id: UUID | None = None  # Specific slot
    slot_type: str | None = None  # Type of slot (e.g., "monday_am")
    block_type: str | None = None  # Type of block
    service_type: str | None = None  # Type of service
    target_faculty_id: UUID | None = None  # For swap affinity

    # Trail strength (0.0 - 1.0)
    strength: float = 0.5
    peak_strength: float = 0.5
    created_at: datetime = field(default_factory=datetime.now)
    last_reinforced: datetime = field(default_factory=datetime.now)
    last_evaporated: datetime = field(default_factory=datetime.now)

    # Evaporation parameters
    evaporation_rate: float = 0.1  # Per day
    min_strength: float = 0.01  # Trails never fully disappear
    max_strength: float = 1.0

    # Statistics
    reinforcement_count: int = 0
    signal_history: list[tuple[datetime, SignalType, float]] = field(
        default_factory=list
    )

    def reinforce(self, signal_type: SignalType, amount: float = 0.1) -> None:
        """
        Reinforce the trail (deposit pheromone).

        Args:
            signal_type: What triggered the reinforcement
            amount: How much to strengthen (0.0 - 1.0)
        """
        old_strength = self.strength
        self.strength = min(self.max_strength, self.strength + amount)
        self.peak_strength = max(self.peak_strength, self.strength)
        self.last_reinforced = datetime.now()
        self.reinforcement_count += 1
        self.signal_history.append((datetime.now(), signal_type, amount))

        # Keep history manageable
        if len(self.signal_history) > 100:
            self.signal_history = self.signal_history[-100:]

        logger.debug(
            f"Trail {self.id} reinforced: {old_strength:.3f} -> {self.strength:.3f}"
        )

    def weaken(self, signal_type: SignalType, amount: float = 0.1) -> None:
        """
        Weaken the trail (negative signal).

        Args:
            signal_type: What triggered the weakening
            amount: How much to weaken
        """
        old_strength = self.strength
        self.strength = max(self.min_strength, self.strength - amount)
        self.signal_history.append((datetime.now(), signal_type, -amount))

        logger.debug(
            f"Trail {self.id} weakened: {old_strength:.3f} -> {self.strength:.3f}"
        )

    def evaporate(self, days_elapsed: float = 1.0) -> None:
        """
        Apply evaporation (time decay).

        Trails naturally weaken over time, ensuring recency matters.

        Args:
            days_elapsed: Days since last evaporation
        """
        if days_elapsed <= 0:
            return

        # Exponential decay
        decay_factor = math.exp(-self.evaporation_rate * days_elapsed)
        old_strength = self.strength
        self.strength = max(self.min_strength, self.strength * decay_factor)
        self.last_evaporated = datetime.now()

        if old_strength - self.strength > 0.01:
            logger.debug(
                f"Trail {self.id} evaporated: {old_strength:.3f} -> {self.strength:.3f}"
            )

    @property
    def strength_category(self) -> TrailStrength:
        """Get categorical strength level."""
        if self.strength < 0.2:
            return TrailStrength.VERY_WEAK
        elif self.strength < 0.4:
            return TrailStrength.WEAK
        elif self.strength < 0.6:
            return TrailStrength.MODERATE
        elif self.strength < 0.8:
            return TrailStrength.STRONG
        else:
            return TrailStrength.VERY_STRONG

    @property
    def age_days(self) -> float:
        """How old is this trail in days."""
        return (datetime.now() - self.created_at).total_seconds() / 86400

    @property
    def days_since_reinforced(self) -> float:
        """Days since last reinforcement."""
        return (datetime.now() - self.last_reinforced).total_seconds() / 86400


@dataclass
class CollectivePreference:
    """
    Aggregated preference pattern from multiple faculty trails.

    Represents emergent consensus about a slot or pattern.
    """

    slot_type: str
    total_preference_strength: float
    total_avoidance_strength: float
    net_preference: float  # preference - avoidance
    faculty_count: int
    confidence: float  # Based on signal density
    trails: list[PreferenceTrail]

    @property
    def is_popular(self) -> bool:
        """Is this collectively preferred?"""
        return self.net_preference > 0.3

    @property
    def is_unpopular(self) -> bool:
        """Is this collectively avoided?"""
        return self.net_preference < -0.3


@dataclass
class SwapNetwork:
    """
    Network of swap affinities between faculty.

    Built from swap trails to identify natural swap partners.
    """

    edges: dict[tuple[UUID, UUID], float]  # (faculty1, faculty2) -> affinity
    successful_swaps: dict[tuple[UUID, UUID], int]
    failed_swaps: dict[tuple[UUID, UUID], int]

    def get_best_partners(
        self, faculty_id: UUID, top_n: int = 3
    ) -> list[tuple[UUID, float]]:
        """Get best swap partners for a faculty member."""
        partners = []
        for (f1, f2), affinity in self.edges.items():
            if f1 == faculty_id:
                partners.append((f2, affinity))
            elif f2 == faculty_id:
                partners.append((f1, affinity))

        return sorted(partners, key=lambda x: -x[1])[:top_n]


@dataclass
class StigmergyStatus:
    """Overall status of the stigmergy system."""

    timestamp: datetime
    total_trails: int
    active_trails: int  # Strength > 0.1
    trails_by_type: dict[str, int]

    # Trail health
    average_strength: float
    average_age_days: float
    evaporation_debt_hours: float  # How long since last full evaporation

    # Patterns detected
    popular_slots: list[str]
    unpopular_slots: list[str]
    strong_swap_pairs: int

    # Recommendations
    recommendations: list[str]


class StigmergicScheduler:
    """
    Implements stigmergy-based preference tracking and optimization.

    Faculty preferences are recorded as "pheromone trails" that:
    - Strengthen with repeated positive signals
    - Weaken over time (evaporation)
    - Guide scheduling decisions collectively
    - Emerge optimal patterns without central planning
    """

    def __init__(
        self,
        evaporation_rate: float = 0.1,
        reinforcement_amount: float = 0.1,
        evaporation_interval_hours: float = 24.0,
    ):
        self.evaporation_rate = evaporation_rate
        self.reinforcement_amount = reinforcement_amount
        self.evaporation_interval_hours = evaporation_interval_hours

        self.trails: dict[UUID, PreferenceTrail] = {}
        self.last_evaporation: datetime = datetime.now()

        # Indexes for fast lookup
        self._trails_by_faculty: dict[UUID, list[UUID]] = {}
        self._trails_by_slot: dict[UUID, list[UUID]] = {}
        self._trails_by_type: dict[TrailType, list[UUID]] = {}

    def record_preference(
        self,
        faculty_id: UUID,
        trail_type: TrailType,
        slot_id: UUID = None,
        slot_type: str = None,
        block_type: str = None,
        service_type: str = None,
        target_faculty_id: UUID = None,
        strength: float = 0.5,
    ) -> PreferenceTrail:
        """
        Record a new preference trail or reinforce existing one.

        Args:
            faculty_id: Faculty member
            trail_type: Type of preference
            slot_id: Specific slot (optional)
            slot_type: Type of slot pattern (optional)
            block_type: Type of block (optional)
            service_type: Type of service (optional)
            target_faculty_id: For swap affinity (optional)
            strength: Initial strength

        Returns:
            The created or updated PreferenceTrail
        """
        # Check for existing trail
        existing = self._find_trail(
            faculty_id,
            trail_type,
            slot_id,
            slot_type,
            block_type,
            service_type,
            target_faculty_id,
        )

        if existing:
            existing.reinforce(
                SignalType.EXPLICIT_PREFERENCE, self.reinforcement_amount
            )
            return existing

        # Create new trail
        trail = PreferenceTrail(
            id=uuid4(),
            faculty_id=faculty_id,
            trail_type=trail_type,
            slot_id=slot_id,
            slot_type=slot_type,
            block_type=block_type,
            service_type=service_type,
            target_faculty_id=target_faculty_id,
            strength=strength,
            evaporation_rate=self.evaporation_rate,
        )

        self.trails[trail.id] = trail
        self._index_trail(trail)

        logger.info(f"Created preference trail: {faculty_id} -> {trail_type.value}")

        return trail

    def record_signal(
        self,
        faculty_id: UUID,
        signal_type: SignalType,
        slot_id: UUID = None,
        slot_type: str = None,
        target_faculty_id: UUID = None,
        strength_change: float = None,
    ):
        """
        Record a behavioral signal that updates trails.

        Args:
            faculty_id: Faculty member
            signal_type: Type of signal
            slot_id: Affected slot
            slot_type: Affected slot type
            target_faculty_id: For swap signals
            strength_change: Override default change amount
        """
        amount = strength_change or self.reinforcement_amount

        # Determine trail type and whether to strengthen or weaken
        if signal_type in (
            SignalType.EXPLICIT_PREFERENCE,
            SignalType.ACCEPTED_ASSIGNMENT,
            SignalType.HIGH_SATISFACTION,
        ):
            trail_type = TrailType.PREFERENCE
            strengthen = True

        elif (
            signal_type
            in (
                SignalType.REQUESTED_SWAP,
                SignalType.LOW_SATISFACTION,
            )
            or signal_type == SignalType.DECLINED_OFFER
        ):
            trail_type = TrailType.AVOIDANCE
            strengthen = True

        elif signal_type == SignalType.COMPLETED_SWAP:
            trail_type = TrailType.SWAP_AFFINITY
            strengthen = True

        else:
            trail_type = TrailType.PREFERENCE
            strengthen = True

        # Find or create trail
        trail = self._find_trail(
            faculty_id,
            trail_type,
            slot_id,
            slot_type,
            target_faculty_id=target_faculty_id,
        )

        if not trail:
            trail = self.record_preference(
                faculty_id=faculty_id,
                trail_type=trail_type,
                slot_id=slot_id,
                slot_type=slot_type,
                target_faculty_id=target_faculty_id,
                strength=0.3,  # Start weaker for implicit signals
            )

        if strengthen:
            trail.reinforce(signal_type, amount)
        else:
            trail.weaken(signal_type, amount)

    def evaporate_trails(self, force: bool = False):
        """
        Apply evaporation to all trails.

        Called periodically to ensure recency of preferences matters.

        Args:
            force: Force evaporation even if not due
        """
        now = datetime.now()
        hours_since = (now - self.last_evaporation).total_seconds() / 3600

        if not force and hours_since < self.evaporation_interval_hours:
            return

        days_elapsed = hours_since / 24

        evaporated_count = 0
        for trail in self.trails.values():
            old_strength = trail.strength
            trail.evaporate(days_elapsed)
            if trail.strength < old_strength - 0.01:
                evaporated_count += 1

        self.last_evaporation = now

        logger.info(f"Evaporated {evaporated_count} trails ({days_elapsed:.1f} days)")

    def get_collective_preference(
        self,
        slot_type: str = None,
        slot_id: UUID = None,
    ) -> CollectivePreference | None:
        """
        Get aggregated preference for a slot or slot type.

        Combines all faculty trails to find collective preference.

        Args:
            slot_type: Type of slot to analyze
            slot_id: Specific slot to analyze

        Returns:
            CollectivePreference or None
        """
        # Apply pending evaporation
        self.evaporate_trails()

        relevant_trails = []

        for trail in self.trails.values():
            if (
                slot_id
                and trail.slot_id == slot_id
                or slot_type
                and trail.slot_type == slot_type
            ):
                relevant_trails.append(trail)

        if not relevant_trails:
            return None

        # Aggregate
        preference_strength = 0.0
        avoidance_strength = 0.0
        faculty_ids = set()

        for trail in relevant_trails:
            faculty_ids.add(trail.faculty_id)
            if trail.trail_type == TrailType.PREFERENCE:
                preference_strength += trail.strength
            elif trail.trail_type == TrailType.AVOIDANCE:
                avoidance_strength += trail.strength

        # Normalize
        faculty_count = len(faculty_ids)
        if faculty_count > 0:
            preference_strength /= faculty_count
            avoidance_strength /= faculty_count

        net = preference_strength - avoidance_strength

        # Confidence based on signal density
        avg_reinforcements = (
            statistics.mean([t.reinforcement_count for t in relevant_trails])
            if relevant_trails
            else 0
        )

        confidence = min(
            1.0, avg_reinforcements / 10
        )  # Max confidence at 10 reinforcements

        return CollectivePreference(
            slot_type=slot_type or str(slot_id),
            total_preference_strength=preference_strength,
            total_avoidance_strength=avoidance_strength,
            net_preference=net,
            faculty_count=faculty_count,
            confidence=confidence,
            trails=relevant_trails,
        )

    def get_faculty_preferences(
        self,
        faculty_id: UUID,
        trail_type: TrailType = None,
        min_strength: float = 0.1,
    ) -> list[PreferenceTrail]:
        """
        Get all preference trails for a faculty member.

        Args:
            faculty_id: Faculty to query
            trail_type: Filter by type
            min_strength: Minimum trail strength

        Returns:
            List of PreferenceTrails
        """
        trail_ids = self._trails_by_faculty.get(faculty_id, [])
        trails = []

        for tid in trail_ids:
            trail = self.trails.get(tid)
            if not trail:
                continue
            if trail.strength < min_strength:
                continue
            if trail_type and trail.trail_type != trail_type:
                continue
            trails.append(trail)

        return sorted(trails, key=lambda t: -t.strength)

    def get_swap_network(self) -> SwapNetwork:
        """
        Build swap affinity network from trails.

        Returns:
            SwapNetwork with faculty pair affinities
        """
        edges = {}
        successful = {}
        failed = {}

        for trail in self.trails.values():
            if trail.trail_type != TrailType.SWAP_AFFINITY:
                continue
            if not trail.target_faculty_id:
                continue

            tuple(sorted([str(trail.faculty_id), str(trail.target_faculty_id)]))
            pair_uuids = (trail.faculty_id, trail.target_faculty_id)

            if pair_uuids not in edges:
                edges[pair_uuids] = 0.0
                successful[pair_uuids] = 0
                failed[pair_uuids] = 0

            edges[pair_uuids] = max(edges[pair_uuids], trail.strength)

            # Count signals
            for _, signal, _ in trail.signal_history:
                if signal == SignalType.COMPLETED_SWAP:
                    successful[pair_uuids] += 1

        return SwapNetwork(
            edges=edges,
            successful_swaps=successful,
            failed_swaps=failed,
        )

    def suggest_assignments(
        self,
        slot_id: UUID,
        slot_type: str,
        available_faculty: list[UUID],
    ) -> list[tuple[UUID, float, str]]:
        """
        Suggest faculty for a slot based on preference trails.

        Args:
            slot_id: Slot to fill
            slot_type: Type of slot
            available_faculty: Faculty who could be assigned

        Returns:
            List of (faculty_id, score, reason) sorted by preference
        """
        suggestions = []

        for faculty_id in available_faculty:
            score = 0.5  # Base score
            reasons = []

            # Check preference trails
            pref_trails = [
                t
                for t in self.get_faculty_preferences(faculty_id, TrailType.PREFERENCE)
                if t.slot_id == slot_id or t.slot_type == slot_type
            ]
            if pref_trails:
                max_pref = max(t.strength for t in pref_trails)
                score += max_pref * 0.3
                reasons.append(f"preference trail strength: {max_pref:.2f}")

            # Check avoidance trails
            avoid_trails = [
                t
                for t in self.get_faculty_preferences(faculty_id, TrailType.AVOIDANCE)
                if t.slot_id == slot_id or t.slot_type == slot_type
            ]
            if avoid_trails:
                max_avoid = max(t.strength for t in avoid_trails)
                score -= max_avoid * 0.4  # Avoidance counts more
                reasons.append(f"avoidance trail strength: {max_avoid:.2f}")

            # Clamp score
            score = max(0.0, min(1.0, score))

            reason = "; ".join(reasons) if reasons else "no preference signals"
            suggestions.append((faculty_id, score, reason))

        return sorted(suggestions, key=lambda x: -x[1])

    def detect_patterns(self) -> dict[str, Any]:
        """
        Detect emergent patterns from collective trails.

        Returns:
            Dict with detected patterns
        """
        self.evaporate_trails()

        # Find popular/unpopular slot types
        slot_preferences = {}
        for trail in self.trails.values():
            if not trail.slot_type:
                continue
            if trail.slot_type not in slot_preferences:
                slot_preferences[trail.slot_type] = {
                    "prefer": 0.0,
                    "avoid": 0.0,
                    "count": 0,
                }

            if trail.trail_type == TrailType.PREFERENCE:
                slot_preferences[trail.slot_type]["prefer"] += trail.strength
            elif trail.trail_type == TrailType.AVOIDANCE:
                slot_preferences[trail.slot_type]["avoid"] += trail.strength
            slot_preferences[trail.slot_type]["count"] += 1

        # Normalize and categorize
        popular = []
        unpopular = []
        neutral = []

        for slot_type, data in slot_preferences.items():
            if data["count"] == 0:
                continue
            net = (data["prefer"] - data["avoid"]) / data["count"]
            if net > 0.3:
                popular.append((slot_type, net))
            elif net < -0.3:
                unpopular.append((slot_type, net))
            else:
                neutral.append((slot_type, net))

        # Find swap cliques
        swap_network = self.get_swap_network()
        strong_pairs = [
            (f1, f2, s) for (f1, f2), s in swap_network.edges.items() if s > 0.6
        ]

        return {
            "popular_slots": sorted(popular, key=lambda x: -x[1]),
            "unpopular_slots": sorted(unpopular, key=lambda x: x[1]),
            "neutral_slots": neutral,
            "strong_swap_pairs": strong_pairs,
            "total_patterns": len(popular) + len(unpopular) + len(strong_pairs),
        }

    def get_status(self) -> StigmergyStatus:
        """Get overall status of the stigmergy system."""
        self.evaporate_trails()

        # Count trails
        trails_by_type = {}
        active_count = 0
        strengths = []
        ages = []

        for trail in self.trails.values():
            # By type
            key = trail.trail_type.value
            trails_by_type[key] = trails_by_type.get(key, 0) + 1

            # Active
            if trail.strength > 0.1:
                active_count += 1

            strengths.append(trail.strength)
            ages.append(trail.age_days)

        avg_strength = statistics.mean(strengths) if strengths else 0.0
        avg_age = statistics.mean(ages) if ages else 0.0

        # Evaporation debt
        hours_since = (datetime.now() - self.last_evaporation).total_seconds() / 3600

        # Detect patterns
        patterns = self.detect_patterns()

        # Build recommendations
        recommendations = []

        if avg_strength < 0.3:
            recommendations.append(
                "Low average trail strength - encourage more preference input"
            )

        if hours_since > self.evaporation_interval_hours * 2:
            recommendations.append(
                f"Evaporation overdue by {hours_since - self.evaporation_interval_hours:.0f} hours"
            )

        if len(patterns["unpopular_slots"]) > 3:
            recommendations.append(
                "Multiple unpopular slots detected - review scheduling constraints"
            )

        if active_count < len(self.trails) * 0.5:
            recommendations.append(
                "Many weak trails - consider pruning or encouraging engagement"
            )

        if not recommendations:
            recommendations.append(
                "Stigmergy system healthy - collective preferences emerging normally"
            )

        return StigmergyStatus(
            timestamp=datetime.now(),
            total_trails=len(self.trails),
            active_trails=active_count,
            trails_by_type=trails_by_type,
            average_strength=avg_strength,
            average_age_days=avg_age,
            evaporation_debt_hours=max(
                0, hours_since - self.evaporation_interval_hours
            ),
            popular_slots=[s[0] for s in patterns["popular_slots"][:5]],
            unpopular_slots=[s[0] for s in patterns["unpopular_slots"][:5]],
            strong_swap_pairs=len(patterns["strong_swap_pairs"]),
            recommendations=recommendations,
        )

    def _find_trail(
        self,
        faculty_id: UUID,
        trail_type: TrailType,
        slot_id: UUID = None,
        slot_type: str = None,
        block_type: str = None,
        service_type: str = None,
        target_faculty_id: UUID = None,
    ) -> PreferenceTrail | None:
        """Find an existing trail matching the criteria."""
        trail_ids = self._trails_by_faculty.get(faculty_id, [])

        for tid in trail_ids:
            trail = self.trails.get(tid)
            if not trail:
                continue
            if trail.trail_type != trail_type:
                continue

            # Match criteria
            if slot_id and trail.slot_id != slot_id:
                continue
            if slot_type and trail.slot_type != slot_type:
                continue
            if block_type and trail.block_type != block_type:
                continue
            if service_type and trail.service_type != service_type:
                continue
            if target_faculty_id and trail.target_faculty_id != target_faculty_id:
                continue

            # For swap affinity, need exact slot_type match or both None
            if trail_type == TrailType.SWAP_AFFINITY:
                if slot_type != trail.slot_type:
                    continue

            return trail

        return None

    def _index_trail(self, trail: PreferenceTrail):
        """Add trail to indexes."""
        # By faculty
        if trail.faculty_id not in self._trails_by_faculty:
            self._trails_by_faculty[trail.faculty_id] = []
        self._trails_by_faculty[trail.faculty_id].append(trail.id)

        # By slot
        if trail.slot_id:
            if trail.slot_id not in self._trails_by_slot:
                self._trails_by_slot[trail.slot_id] = []
            self._trails_by_slot[trail.slot_id].append(trail.id)

        # By type
        if trail.trail_type not in self._trails_by_type:
            self._trails_by_type[trail.trail_type] = []
        self._trails_by_type[trail.trail_type].append(trail.id)

    def prune_weak_trails(self, threshold: float = 0.05) -> int:
        """
        Remove trails below strength threshold.

        Args:
            threshold: Minimum strength to keep

        Returns:
            Number of trails pruned
        """
        to_remove = [
            tid for tid, trail in self.trails.items() if trail.strength < threshold
        ]

        for tid in to_remove:
            trail = self.trails[tid]
            del self.trails[tid]

            # Remove from indexes
            if trail.faculty_id in self._trails_by_faculty:
                self._trails_by_faculty[trail.faculty_id] = [
                    t for t in self._trails_by_faculty[trail.faculty_id] if t != tid
                ]
            if trail.slot_id in self._trails_by_slot:
                self._trails_by_slot[trail.slot_id] = [
                    t for t in self._trails_by_slot[trail.slot_id] if t != tid
                ]

        logger.info(f"Pruned {len(to_remove)} weak trails")
        return len(to_remove)
