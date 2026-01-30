"""
Cognitive Load Management (Psychology/Human Factors Pattern).

Working memory is severely limited (~4 items). Decision quality degrades rapidly
under cognitive overload. Decision fatigue accumulates through a day/week.

Key Principles:
- Miller's Law: Working memory capacity ~7 items (±2)
- Decision fatigue: Quality degrades after repeated decisions
- Defaults reduce cognitive load
- Binary choices easier than open-ended questions

This module implements:
1. Decision point tracking and limiting
2. Safe defaults for auto-decisions
3. Decision fatigue monitoring
4. Context switching costs
5. Batch similar decisions together
6. Cognitive load scoring for schedules
"""

import logging
import statistics
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4

logger = logging.getLogger(__name__)


class DecisionComplexity(str, Enum):
    """Complexity level of a decision."""

    TRIVIAL = "trivial"  # Yes/no, approve/reject
    SIMPLE = "simple"  # Choose from 2-3 options
    MODERATE = "moderate"  # Choose from 4-7 options, some analysis
    COMPLEX = "complex"  # Multiple factors, tradeoffs
    STRATEGIC = "strategic"  # High stakes, long-term impact


class DecisionCategory(str, Enum):
    """Category of scheduling decision."""

    ASSIGNMENT = "assignment"  # Who covers what
    SWAP = "swap"  # Trade shifts between faculty
    COVERAGE = "coverage"  # Fill gaps
    LEAVE = "leave"  # Approve time off
    CONFLICT = "conflict"  # Resolve scheduling conflicts
    OVERRIDE = "override"  # Override constraints
    POLICY = "policy"  # Policy changes
    EMERGENCY = "emergency"  # Crisis decisions


class CognitiveState(str, Enum):
    """Current cognitive load state."""

    FRESH = "fresh"  # Start of session, full capacity
    ENGAGED = "engaged"  # Working well, some load
    LOADED = "loaded"  # Approaching capacity
    FATIGUED = "fatigued"  # Significantly reduced capacity
    DEPLETED = "depleted"  # Needs rest, quality compromised


class DecisionOutcome(str, Enum):
    """Outcome of a decision request."""

    DECIDED = "decided"  # User made decision
    DEFERRED = "deferred"  # Postponed for later
    AUTO_DEFAULT = "auto_default"  # System used default
    DELEGATED = "delegated"  # Sent to someone else
    CANCELLED = "cancelled"  # No longer needed


@dataclass
class Decision:
    """
    A decision point in the scheduling system.

    Represents a choice that requires cognitive effort from the user.
    """

    id: UUID
    category: DecisionCategory
    complexity: DecisionComplexity
    description: str
    created_at: datetime

    # Options
    options: list[str] = field(default_factory=list)
    recommended_option: str | None = None
    has_safe_default: bool = False
    safe_default: str | None = None

    # Context
    context: dict = field(default_factory=dict)
    related_decisions: list[UUID] = field(default_factory=list)

    # Urgency
    deadline: datetime | None = None
    is_urgent: bool = False
    can_defer: bool = True

    # Resolution
    outcome: DecisionOutcome | None = None
    chosen_option: str | None = None
    decided_at: datetime | None = None
    decided_by: str | None = None

    # Cognitive cost
    estimated_cognitive_cost: float = 1.0  # 1.0 = one "decision unit"
    actual_time_seconds: float | None = None

    def get_cognitive_cost(self) -> float:
        """Calculate cognitive cost based on complexity."""
        complexity_costs = {
            DecisionComplexity.TRIVIAL: 0.25,
            DecisionComplexity.SIMPLE: 0.5,
            DecisionComplexity.MODERATE: 1.0,
            DecisionComplexity.COMPLEX: 2.0,
            DecisionComplexity.STRATEGIC: 3.0,
        }
        base_cost = complexity_costs.get(self.complexity, 1.0)

        # Increase cost for more options
        option_multiplier = (
            1.0 + (len(self.options) - 2) * 0.1 if len(self.options) > 2 else 1.0
        )

        # Decrease cost if there's a recommended option
        recommend_discount = 0.8 if self.recommended_option else 1.0

        return base_cost * option_multiplier * recommend_discount


@dataclass
class CognitiveSession:
    """
    A work session with cognitive load tracking.

    Tracks decisions made and cognitive state throughout a session.
    """

    id: UUID
    user_id: UUID
    started_at: datetime

    # Configuration
    max_decisions_before_break: int = 7  # Miller's Law
    break_duration_minutes: int = 15
    session_duration_minutes: int = 120

    # Tracking
    decisions_made: list[Decision] = field(default_factory=list)
    total_cognitive_cost: float = 0.0
    breaks_taken: int = 0
    last_break_at: datetime | None = None

    # State
    current_state: CognitiveState = CognitiveState.FRESH
    state_changed_at: datetime = field(default_factory=datetime.now)

    # Completion
    ended_at: datetime | None = None

    def add_decision(self, decision: Decision) -> None:
        """Add a decided decision to session."""
        self.decisions_made.append(decision)
        self.total_cognitive_cost += decision.get_cognitive_cost()
        self._update_state()

    def _update_state(self) -> None:
        """Update cognitive state based on load."""
        cost = self.total_cognitive_cost

        if cost < 2:
            new_state = CognitiveState.FRESH
        elif cost < 4:
            new_state = CognitiveState.ENGAGED
        elif cost < 6:
            new_state = CognitiveState.LOADED
        elif cost < 8:
            new_state = CognitiveState.FATIGUED
        else:
            new_state = CognitiveState.DEPLETED

        if new_state != self.current_state:
            self.current_state = new_state
            self.state_changed_at = datetime.now()

    def take_break(self) -> None:
        """Record a break taken."""
        self.breaks_taken += 1
        self.last_break_at = datetime.now()
        # Breaks reduce accumulated load
        self.total_cognitive_cost = max(0, self.total_cognitive_cost - 3)
        self._update_state()

    @property
    def decisions_until_break(self) -> int:
        """How many more decisions until break recommended."""
        return max(0, self.max_decisions_before_break - len(self.decisions_made))

    @property
    def should_take_break(self) -> bool:
        """Whether a break is recommended."""
        if self.current_state in (CognitiveState.FATIGUED, CognitiveState.DEPLETED):
            return True
        return len(self.decisions_made) >= self.max_decisions_before_break


@dataclass
class CognitiveLoadReport:
    """Report on cognitive load status for a user."""

    user_id: UUID
    generated_at: datetime

    # Current session
    session_id: UUID | None
    current_state: CognitiveState
    decisions_this_session: int
    cognitive_cost_this_session: float

    # Capacity
    remaining_capacity: float  # 0.0 - 1.0
    decisions_until_break: int
    should_take_break: bool

    # Historical (today)
    decisions_today: int
    total_sessions_today: int
    average_decision_time: float  # seconds

    # Recommendations
    recommendations: list[str] = field(default_factory=list)


@dataclass
class DecisionQueueStatus:
    """Status of the decision queue."""

    total_pending: int
    by_complexity: dict[str, int]
    by_category: dict[str, int]
    urgent_count: int
    can_auto_decide: int
    oldest_pending: datetime | None
    estimated_cognitive_cost: float
    recommendations: list[str] = field(default_factory=list)


class CognitiveLoadManager:
    """
    Manages cognitive load for scheduling decision-makers.

    Implements cognitive psychology principles to:
    - Limit decision points
    - Provide safe defaults
    - Monitor fatigue
    - Recommend breaks
    - Auto-decide when appropriate
    """

    def __init__(
        self,
        max_decisions_per_session: int = 7,
        auto_decide_when_fatigued: bool = True,
        batch_similar_decisions: bool = True,
    ) -> None:
        self.max_decisions_per_session = max_decisions_per_session
        self.auto_decide_when_fatigued = auto_decide_when_fatigued
        self.batch_similar_decisions = batch_similar_decisions

        self.sessions: dict[UUID, CognitiveSession] = {}
        self.pending_decisions: list[Decision] = []
        self.decision_history: list[Decision] = []

        # Decision handlers
        self._default_handlers: dict[DecisionCategory, Callable] = {}
        self._on_state_change: list[Callable] = []

    def start_session(
        self,
        user_id: UUID,
        max_decisions: int = None,
    ) -> CognitiveSession:
        """
        Start a new cognitive session for a user.

        Args:
            user_id: User starting the session
            max_decisions: Override default max decisions

        Returns:
            New CognitiveSession
        """
        session = CognitiveSession(
            id=uuid4(),
            user_id=user_id,
            started_at=datetime.now(),
            max_decisions_before_break=max_decisions or self.max_decisions_per_session,
        )

        self.sessions[session.id] = session
        logger.info(f"Started cognitive session {session.id} for user {user_id}")

        return session

    def end_session(self, session_id: UUID) -> None:
        """End a cognitive session."""
        session = self.sessions.get(session_id)
        if session:
            session.ended_at = datetime.now()
            logger.info(
                f"Ended session {session_id}: "
                f"{len(session.decisions_made)} decisions, "
                f"cognitive cost: {session.total_cognitive_cost:.1f}"
            )

    def create_decision(
        self,
        category: DecisionCategory,
        complexity: DecisionComplexity,
        description: str,
        options: list[str],
        recommended_option: str = None,
        safe_default: str = None,
        context: dict = None,
        deadline: datetime = None,
        is_urgent: bool = False,
    ) -> Decision:
        """
        Create a new decision request.

        Args:
            category: Type of decision
            complexity: How complex the decision is
            description: Human-readable description
            options: Available choices
            recommended_option: Suggested choice
            safe_default: Safe fallback if auto-deciding
            context: Additional context
            deadline: When decision is needed by
            is_urgent: Requires immediate attention

        Returns:
            Created Decision
        """
        decision = Decision(
            id=uuid4(),
            category=category,
            complexity=complexity,
            description=description,
            created_at=datetime.now(),
            options=options,
            recommended_option=recommended_option,
            has_safe_default=safe_default is not None,
            safe_default=safe_default,
            context=context or {},
            deadline=deadline,
            is_urgent=is_urgent,
            can_defer=not is_urgent,
        )

        self.pending_decisions.append(decision)

        logger.debug(f"Created decision {decision.id}: {description}")

        return decision

    def request_decision(
        self,
        session_id: UUID,
        decision: Decision,
    ) -> tuple[str, DecisionOutcome]:
        """
        Request a decision from the user, respecting cognitive load.

        If the user is fatigued and auto-decide is enabled, may return
        the safe default instead of presenting the decision.

        Args:
            session_id: Current session
            decision: Decision to request

        Returns:
            Tuple of (choice, outcome)
        """
        session = self.sessions.get(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

            # Check if we should auto-decide
        if self.auto_decide_when_fatigued:
            if session.current_state == CognitiveState.DEPLETED:
                if decision.has_safe_default:
                    return self._auto_decide(decision, "depleted")

            if session.should_take_break and decision.can_defer:
                return self._defer_decision(decision, "break_recommended")

                # Check decision limit
        if len(session.decisions_made) >= session.max_decisions_before_break:
            if decision.has_safe_default:
                return self._auto_decide(decision, "limit_reached")
            elif decision.can_defer:
                return self._defer_decision(decision, "limit_reached")

                # Present to user (in actual implementation, this would be async)
                # For now, we return a pending state
        return None, DecisionOutcome.DECIDED

    def record_decision(
        self,
        session_id: UUID,
        decision_id: UUID,
        chosen_option: str,
        decided_by: str,
        actual_time_seconds: float = None,
    ) -> None:
        """
        Record a decision that was made.

        Args:
            session_id: Current session
            decision_id: Decision that was resolved
            chosen_option: The choice made
            decided_by: Who made the decision
            actual_time_seconds: How long it took
        """
        session = self.sessions.get(session_id)
        decision = next(
            (d for d in self.pending_decisions if d.id == decision_id), None
        )

        if decision:
            decision.outcome = DecisionOutcome.DECIDED
            decision.chosen_option = chosen_option
            decision.decided_at = datetime.now()
            decision.decided_by = decided_by
            decision.actual_time_seconds = actual_time_seconds

            self.pending_decisions.remove(decision)
            self.decision_history.append(decision)

            if session:
                session.add_decision(decision)
                self._check_state_change(session)

    def _auto_decide(
        self,
        decision: Decision,
        reason: str,
    ) -> tuple[str, DecisionOutcome]:
        """Apply safe default automatically."""
        decision.outcome = DecisionOutcome.AUTO_DEFAULT
        decision.chosen_option = decision.safe_default
        decision.decided_at = datetime.now()
        decision.decided_by = f"auto:{reason}"

        self.pending_decisions.remove(decision)
        self.decision_history.append(decision)

        logger.info(
            f"Auto-decided {decision.id}: {decision.safe_default} (reason: {reason})"
        )

        return decision.safe_default, DecisionOutcome.AUTO_DEFAULT

    def _defer_decision(
        self,
        decision: Decision,
        reason: str,
    ) -> tuple[None, DecisionOutcome]:
        """Defer decision for later."""
        decision.outcome = DecisionOutcome.DEFERRED

        logger.info(f"Deferred decision {decision.id} (reason: {reason})")

        return None, DecisionOutcome.DEFERRED

    def _check_state_change(self, session: CognitiveSession) -> None:
        """Check for state changes and notify handlers."""
        # Notification handlers would be called here
        for handler in self._on_state_change:
            try:
                handler(session)
            except Exception as e:
                logger.error(f"State change handler error: {e}")

    def get_session_status(self, session_id: UUID) -> CognitiveLoadReport | None:
        """
        Get cognitive load report for a session.

        Args:
            session_id: Session to report on

        Returns:
            CognitiveLoadReport or None
        """
        session = self.sessions.get(session_id)
        if not session:
            return None

            # Calculate remaining capacity
        max_cost = self.max_decisions_per_session * 1.5  # Rough estimate
        remaining = max(0, (max_cost - session.total_cognitive_cost) / max_cost)

        # Calculate average decision time
        times = [
            d.actual_time_seconds
            for d in session.decisions_made
            if d.actual_time_seconds
        ]
        avg_time = statistics.mean(times) if times else 0.0

        # Build recommendations
        recommendations = []

        if session.current_state == CognitiveState.DEPLETED:
            recommendations.append(
                "CRITICAL: Take a break immediately to restore decision quality"
            )
        elif session.current_state == CognitiveState.FATIGUED:
            recommendations.append(
                "Warning: Decision quality may be degraded - consider a short break"
            )

        if session.should_take_break:
            recommendations.append(
                f"Break recommended after {len(session.decisions_made)} decisions"
            )

        if not recommendations:
            recommendations.append("Cognitive state is good - continue working")

        return CognitiveLoadReport(
            user_id=session.user_id,
            generated_at=datetime.now(),
            session_id=session.id,
            current_state=session.current_state,
            decisions_this_session=len(session.decisions_made),
            cognitive_cost_this_session=session.total_cognitive_cost,
            remaining_capacity=remaining,
            decisions_until_break=session.decisions_until_break,
            should_take_break=session.should_take_break,
            decisions_today=len(
                session.decisions_made
            ),  # Would aggregate across sessions
            total_sessions_today=1,  # Would count actual sessions
            average_decision_time=avg_time,
            recommendations=recommendations,
        )

    def get_queue_status(self) -> DecisionQueueStatus:
        """Get status of pending decision queue."""
        by_complexity = {}
        by_category = {}
        urgent_count = 0
        can_auto = 0
        total_cost = 0.0
        oldest = None

        for decision in self.pending_decisions:
            # By complexity
            key = decision.complexity.value
            by_complexity[key] = by_complexity.get(key, 0) + 1

            # By category
            key = decision.category.value
            by_category[key] = by_category.get(key, 0) + 1

            # Urgent
            if decision.is_urgent:
                urgent_count += 1

                # Can auto-decide
            if decision.has_safe_default:
                can_auto += 1

                # Cost
            total_cost += decision.get_cognitive_cost()

            # Oldest
            if oldest is None or decision.created_at < oldest:
                oldest = decision.created_at

                # Build recommendations
        recommendations = []

        if urgent_count > 3:
            recommendations.append(f"ALERT: {urgent_count} urgent decisions pending")

        if can_auto > 0 and total_cost > 6:
            recommendations.append(
                f"Consider auto-deciding {can_auto} low-risk decisions"
            )

        if len(self.pending_decisions) > 10:
            recommendations.append("Large decision backlog - prioritize or batch")

        complex_count = by_complexity.get("complex", 0) + by_complexity.get(
            "strategic", 0
        )
        if complex_count > 2:
            recommendations.append("Multiple complex decisions - schedule focused time")

        return DecisionQueueStatus(
            total_pending=len(self.pending_decisions),
            by_complexity=by_complexity,
            by_category=by_category,
            urgent_count=urgent_count,
            can_auto_decide=can_auto,
            oldest_pending=oldest,
            estimated_cognitive_cost=total_cost,
            recommendations=recommendations,
        )

    def batch_similar_decisions(self) -> dict[DecisionCategory, list[Decision]]:
        """
        Group similar pending decisions for batch processing.

        Batching reduces context switching costs.

        Returns:
            Dict of category -> decisions
        """
        batches = {}
        for decision in self.pending_decisions:
            if decision.category not in batches:
                batches[decision.category] = []
            batches[decision.category].append(decision)

        return batches

    def prioritize_decisions(self) -> list[Decision]:
        """
        Get decisions in recommended processing order.

        Priority order:
        1. Urgent decisions
        2. Past deadline
        3. Approaching deadline
        4. Lower complexity first (quick wins)
        5. Has recommendation

        Returns:
            Sorted list of decisions
        """
        now = datetime.now()

        def priority_score(d: Decision) -> tuple:
            urgent = 0 if d.is_urgent else 1
            past_deadline = 0 if d.deadline and d.deadline < now else 1
            deadline_hours = (
                (d.deadline - now).total_seconds() / 3600 if d.deadline else 999
            )
            complexity = {
                DecisionComplexity.TRIVIAL: 1,
                DecisionComplexity.SIMPLE: 2,
                DecisionComplexity.MODERATE: 3,
                DecisionComplexity.COMPLEX: 4,
                DecisionComplexity.STRATEGIC: 5,
            }.get(d.complexity, 3)
            has_rec = 0 if d.recommended_option else 1

            return (urgent, past_deadline, deadline_hours, complexity, has_rec)

        return sorted(self.pending_decisions, key=priority_score)

    def calculate_schedule_cognitive_load(
        self,
        schedule_changes: list[dict],
    ) -> dict:
        """
        Calculate cognitive load imposed by a schedule on coordinators.

        Schedules with more exceptions, conflicts, and edge cases
        require more cognitive effort to understand and manage.

        Args:
            schedule_changes: List of changes/exceptions

        Returns:
            Dict with load metrics and recommendations
        """
        # Count complexity factors
        exceptions = 0
        conflicts = 0
        overrides = 0
        cross_coverage = 0

        for change in schedule_changes:
            change_type = change.get("type", "")
            if "exception" in change_type.lower():
                exceptions += 1
            elif "conflict" in change_type.lower():
                conflicts += 1
            elif "override" in change_type.lower():
                overrides += 1
            elif "cross" in change_type.lower():
                cross_coverage += 1

                # Calculate load score
        base_score = len(schedule_changes) * 0.5
        complexity_score = (
            exceptions * 1.0 + conflicts * 2.0 + overrides * 1.5 + cross_coverage * 1.0
        )

        total_score = base_score + complexity_score

        # Determine grade
        if total_score < 5:
            grade = "A"
            grade_description = "Low cognitive load - easy to manage"
        elif total_score < 10:
            grade = "B"
            grade_description = "Moderate cognitive load - manageable"
        elif total_score < 20:
            grade = "C"
            grade_description = "High cognitive load - requires attention"
        elif total_score < 30:
            grade = "D"
            grade_description = "Very high cognitive load - simplification recommended"
        else:
            grade = "F"
            grade_description = "Excessive cognitive load - likely errors will occur"

        recommendations = []

        if exceptions > 5:
            recommendations.append("Many exceptions - consider revising base schedule")
        if conflicts > 3:
            recommendations.append("Multiple conflicts - review constraint rules")
        if overrides > 3:
            recommendations.append(
                "Excessive overrides - constraints may be too strict"
            )

        return {
            "total_score": total_score,
            "grade": grade,
            "grade_description": grade_description,
            "factors": {
                "total_changes": len(schedule_changes),
                "exceptions": exceptions,
                "conflicts": conflicts,
                "overrides": overrides,
                "cross_coverage": cross_coverage,
            },
            "recommendations": recommendations,
        }

    def register_default_handler(
        self,
        category: DecisionCategory,
        handler: Callable[[Decision], str],
    ) -> None:
        """Register a handler for auto-deciding a category."""
        self._default_handlers[category] = handler
        logger.info(f"Registered default handler for {category.value}")

    def register_state_handler(
        self,
        handler: Callable[[CognitiveSession], None],
    ) -> None:
        """Register handler for cognitive state changes."""
        self._on_state_change.append(handler)

    def get_decision_templates(self) -> dict[DecisionCategory, dict]:
        """
        Get pre-configured decision templates.

        Templates reduce cognitive load by providing structure.

        Returns:
            Dict of category -> template info
        """
        return {
            DecisionCategory.SWAP: {
                "description": "Approve schedule swap between {faculty1} and {faculty2}",
                "default_complexity": DecisionComplexity.SIMPLE,
                "options": ["approve", "deny"],
                "safe_default": "approve",
                "recommended_option": "approve",
            },
            DecisionCategory.LEAVE: {
                "description": "Approve leave request for {faculty} on {dates}",
                "default_complexity": DecisionComplexity.SIMPLE,
                "options": ["approve", "deny", "defer"],
                "safe_default": "defer",
                "recommended_option": None,  # Depends on coverage
            },
            DecisionCategory.COVERAGE: {
                "description": "Assign coverage for {block} on {date}",
                "default_complexity": DecisionComplexity.MODERATE,
                "options": [],  # Dynamic based on available faculty
                "safe_default": None,  # Must choose
                "recommended_option": None,  # Algorithm recommendation
            },
            DecisionCategory.CONFLICT: {
                "description": "Resolve conflict: {description}",
                "default_complexity": DecisionComplexity.COMPLEX,
                "options": [],  # Dynamic
                "safe_default": None,  # Must decide
                "recommended_option": None,
            },
            DecisionCategory.OVERRIDE: {
                "description": "Override constraint: {constraint}",
                "default_complexity": DecisionComplexity.MODERATE,
                "options": ["approve_once", "approve_permanent", "deny"],
                "safe_default": "deny",  # Conservative default
                "recommended_option": "approve_once",
            },
            DecisionCategory.EMERGENCY: {
                "description": "Emergency: {description}",
                "default_complexity": DecisionComplexity.COMPLEX,
                "options": [],  # Dynamic
                "safe_default": None,  # Cannot auto-decide emergencies
                "recommended_option": None,
            },
        }
