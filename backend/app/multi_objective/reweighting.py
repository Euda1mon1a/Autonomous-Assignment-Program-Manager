"""
Dynamic Objective Reweighting for Multi-Objective Optimization.

This module provides mechanisms for dynamically adjusting objective
weights based on user feedback, historical performance, and
contextual factors.

Reweighting Approaches:
    1. Feedback-Based: Adjust based on user preferences
    2. Performance-Based: Boost underperforming objectives
    3. Context-Aware: Adjust based on operational context
    4. Temporal: Time-varying weights for different phases

Multi-Objective Lens - Adaptive Optimization:
    Static weights assume fixed preferences throughout optimization.
    In practice, preferences may:

    - Evolve as decision makers learn about trade-offs
    - Vary based on operational context (normal vs. emergency)
    - Need rebalancing when objectives are under-optimized
    - Change over time (seasonal, project phase)

    Dynamic reweighting enables:
    - Responsive optimization that adapts to feedback
    - Focus shifts between competing objectives
    - Balance correction for lopsided Pareto fronts
    - Interactive steering of the search process

Classes:
    - FeedbackProcessor: Processes user feedback signals
    - ObjectiveAdjuster: Applies weight adjustments
    - ContextualReweighter: Context-aware weight adaptation
    - TemporalReweighter: Time-based weight scheduling
    - DynamicReweighter: Complete reweighting system
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable
from uuid import UUID

import numpy as np

from .core import (
    ObjectiveConfig,
    ObjectiveDirection,
    ParetoFrontier,
    Solution,
)


class FeedbackType(Enum):
    """Types of user feedback."""

    RATING = "rating"  # 1-5 star rating
    COMPARISON = "comparison"  # Pairwise comparison
    ADJUSTMENT = "adjustment"  # Direct weight adjustment
    SELECTION = "selection"  # Solution selection
    REJECTION = "rejection"  # Solution rejection
    COMPLAINT = "complaint"  # Dissatisfaction with objective
    PRIORITY = "priority"  # Explicit priority ordering


class ContextType(Enum):
    """Types of operational contexts."""

    NORMAL = "normal"
    EMERGENCY = "emergency"
    UNDERSTAFFED = "understaffed"
    TRAINING = "training"
    HOLIDAY = "holiday"
    HIGH_DEMAND = "high_demand"


@dataclass
class FeedbackEvent:
    """A single feedback event from the user."""

    feedback_type: FeedbackType
    timestamp: datetime
    data: dict[str, Any]
    affected_objectives: list[str] = field(default_factory=list)
    confidence: float = 1.0  # How confident is this signal


@dataclass
class WeightState:
    """Current state of objective weights."""

    weights: dict[str, float]
    timestamp: datetime
    reason: str
    triggered_by: FeedbackEvent | None = None
    context: ContextType = ContextType.NORMAL


class FeedbackProcessor:
    """
    Processes user feedback to extract weight adjustment signals.

    Converts various feedback types into objective weight deltas.
    """

    def __init__(
        self,
        objectives: list[ObjectiveConfig],
        learning_rate: float = 0.1,
        decay_factor: float = 0.95,
    ):
        """
        Initialize feedback processor.

        Args:
            objectives: List of objective configurations
            learning_rate: How quickly to adjust weights
            decay_factor: Decay for older feedback
        """
        self.objectives = objectives
        self.active_objectives = [o for o in objectives if not o.is_constraint]
        self.learning_rate = learning_rate
        self.decay_factor = decay_factor

        # Feedback history
        self.history: list[FeedbackEvent] = []

        # Cumulative adjustment signals
        self.adjustment_signals: dict[str, float] = {
            o.name: 0.0 for o in self.active_objectives
        }

    def process_feedback(self, event: FeedbackEvent) -> dict[str, float]:
        """
        Process a feedback event and return weight adjustments.

        Args:
            event: Feedback event to process

        Returns:
            Dictionary of objective name to weight delta
        """
        self.history.append(event)

        deltas = {}

        if event.feedback_type == FeedbackType.RATING:
            deltas = self._process_rating(event)

        elif event.feedback_type == FeedbackType.COMPARISON:
            deltas = self._process_comparison(event)

        elif event.feedback_type == FeedbackType.ADJUSTMENT:
            deltas = self._process_adjustment(event)

        elif event.feedback_type == FeedbackType.SELECTION:
            deltas = self._process_selection(event)

        elif event.feedback_type == FeedbackType.REJECTION:
            deltas = self._process_rejection(event)

        elif event.feedback_type == FeedbackType.COMPLAINT:
            deltas = self._process_complaint(event)

        elif event.feedback_type == FeedbackType.PRIORITY:
            deltas = self._process_priority(event)

        # Update cumulative signals
        for obj_name, delta in deltas.items():
            self.adjustment_signals[obj_name] = (
                self.decay_factor * self.adjustment_signals.get(obj_name, 0.0)
                + delta * event.confidence
            )

        return deltas

    def _process_rating(self, event: FeedbackEvent) -> dict[str, float]:
        """Process rating feedback (1-5 scale)."""
        solution_id = event.data.get("solution_id")
        rating = event.data.get("rating", 3)
        solution_objectives = event.data.get("objectives", {})

        deltas = {}
        normalized_rating = (rating - 3) / 2  # Map to [-1, 1]

        # High rating increases weight of objectives where solution excels
        for obj in self.active_objectives:
            if obj.name in solution_objectives:
                val = solution_objectives[obj.name]

                # Determine if this is a "good" value for this objective
                if obj.reference_point is not None and obj.nadir_point is not None:
                    normalized = obj.normalize(val)
                    # If solution is good in this objective and rated highly,
                    # increase its weight (user values it)
                    if obj.direction == ObjectiveDirection.MINIMIZE:
                        quality = 1.0 - normalized
                    else:
                        quality = normalized

                    delta = normalized_rating * quality * self.learning_rate
                    deltas[obj.name] = delta

        return deltas

    def _process_comparison(self, event: FeedbackEvent) -> dict[str, float]:
        """Process pairwise comparison feedback."""
        preferred_objectives = event.data.get("preferred_objectives", {})
        other_objectives = event.data.get("other_objectives", {})

        deltas = {}

        for obj in self.active_objectives:
            if obj.name in preferred_objectives and obj.name in other_objectives:
                pref_val = preferred_objectives[obj.name]
                other_val = other_objectives[obj.name]
                diff = pref_val - other_val

                # If preferred is better in this objective, increase weight
                if obj.direction == ObjectiveDirection.MAXIMIZE:
                    if diff > 0:
                        deltas[obj.name] = self.learning_rate * 0.5
                else:
                    if diff < 0:
                        deltas[obj.name] = self.learning_rate * 0.5

        return deltas

    def _process_adjustment(self, event: FeedbackEvent) -> dict[str, float]:
        """Process direct weight adjustment."""
        adjustments = event.data.get("adjustments", {})
        return {
            k: v * self.learning_rate
            for k, v in adjustments.items()
            if k in [o.name for o in self.active_objectives]
        }

    def _process_selection(self, event: FeedbackEvent) -> dict[str, float]:
        """Process solution selection (implies approval)."""
        solution_objectives = event.data.get("objectives", {})

        deltas = {}
        for obj in self.active_objectives:
            if obj.name in solution_objectives:
                # Increase weight for objectives where selected solution is good
                deltas[obj.name] = self.learning_rate * 0.3

        return deltas

    def _process_rejection(self, event: FeedbackEvent) -> dict[str, float]:
        """Process solution rejection (implies disapproval)."""
        solution_objectives = event.data.get("objectives", {})
        reason = event.data.get("reason", "")

        deltas = {}

        # If reason mentions specific objective, decrease that weight
        for obj in self.active_objectives:
            if obj.name.lower() in reason.lower() or obj.display_name.lower() in reason.lower():
                deltas[obj.name] = -self.learning_rate * 0.5

        return deltas

    def _process_complaint(self, event: FeedbackEvent) -> dict[str, float]:
        """Process complaint about an objective."""
        objective = event.data.get("objective")
        severity = event.data.get("severity", 1.0)  # 0-1

        if objective and objective in [o.name for o in self.active_objectives]:
            return {objective: self.learning_rate * severity}

        return {}

    def _process_priority(self, event: FeedbackEvent) -> dict[str, float]:
        """Process explicit priority ordering."""
        priority_order = event.data.get("priority_order", [])

        deltas = {}
        n = len(priority_order)

        for i, obj_name in enumerate(priority_order):
            if obj_name in [o.name for o in self.active_objectives]:
                # Higher priority = higher weight adjustment
                priority_score = (n - i) / n
                deltas[obj_name] = self.learning_rate * priority_score

        return deltas

    def get_cumulative_adjustments(self) -> dict[str, float]:
        """Get cumulative adjustment signals."""
        return dict(self.adjustment_signals)


class ObjectiveAdjuster:
    """
    Applies weight adjustments to objectives.

    Maintains weight bounds, normalizes weights, and tracks history.
    """

    def __init__(
        self,
        objectives: list[ObjectiveConfig],
        min_weight: float = 0.05,
        max_weight: float = 0.5,
    ):
        """
        Initialize objective adjuster.

        Args:
            objectives: List of objective configurations
            min_weight: Minimum allowed weight
            max_weight: Maximum allowed weight
        """
        self.objectives = objectives
        self.active_objectives = [o for o in objectives if not o.is_constraint]
        self.min_weight = min_weight
        self.max_weight = max_weight

        # Current weights
        self.weights = {o.name: o.weight for o in self.active_objectives}
        self._normalize_weights()

        # History
        self.history: list[WeightState] = []

    def _normalize_weights(self) -> None:
        """Normalize weights to sum to 1."""
        total = sum(self.weights.values())
        if total > 0:
            self.weights = {k: v / total for k, v in self.weights.items()}

    def apply_deltas(
        self,
        deltas: dict[str, float],
        reason: str = "Feedback adjustment",
        event: FeedbackEvent | None = None,
    ) -> dict[str, float]:
        """
        Apply weight deltas and return new weights.

        Args:
            deltas: Weight changes to apply
            reason: Reason for adjustment
            event: Triggering event

        Returns:
            New weight values
        """
        # Apply deltas with bounds
        for obj_name, delta in deltas.items():
            if obj_name in self.weights:
                new_weight = self.weights[obj_name] + delta
                new_weight = max(self.min_weight, min(self.max_weight, new_weight))
                self.weights[obj_name] = new_weight

        # Normalize
        self._normalize_weights()

        # Record state
        state = WeightState(
            weights=dict(self.weights),
            timestamp=datetime.now(),
            reason=reason,
            triggered_by=event,
        )
        self.history.append(state)

        return dict(self.weights)

    def set_weights(
        self,
        weights: dict[str, float],
        reason: str = "Direct assignment",
    ) -> dict[str, float]:
        """
        Set weights directly.

        Args:
            weights: New weight values
            reason: Reason for change

        Returns:
            Applied weights (after normalization)
        """
        for obj_name, weight in weights.items():
            if obj_name in self.weights:
                self.weights[obj_name] = max(
                    self.min_weight, min(self.max_weight, weight)
                )

        self._normalize_weights()

        state = WeightState(
            weights=dict(self.weights),
            timestamp=datetime.now(),
            reason=reason,
        )
        self.history.append(state)

        return dict(self.weights)

    def get_weights(self) -> dict[str, float]:
        """Get current weights."""
        return dict(self.weights)

    def reset_to_default(self) -> dict[str, float]:
        """Reset weights to default values."""
        self.weights = {o.name: o.weight for o in self.active_objectives}
        self._normalize_weights()

        state = WeightState(
            weights=dict(self.weights),
            timestamp=datetime.now(),
            reason="Reset to defaults",
        )
        self.history.append(state)

        return dict(self.weights)


@dataclass
class ContextProfile:
    """Weight profile for a specific context."""

    context: ContextType
    weight_multipliers: dict[str, float]  # Multiply base weights by these
    description: str


class ContextualReweighter:
    """
    Context-aware weight adjustment.

    Maintains profiles for different operational contexts and
    applies appropriate weight modifications.
    """

    def __init__(self, objectives: list[ObjectiveConfig]):
        """
        Initialize contextual reweighter.

        Args:
            objectives: List of objective configurations
        """
        self.objectives = objectives
        self.active_objectives = [o for o in objectives if not o.is_constraint]

        # Default context profiles
        self.profiles: dict[ContextType, ContextProfile] = {
            ContextType.NORMAL: ContextProfile(
                context=ContextType.NORMAL,
                weight_multipliers={o.name: 1.0 for o in self.active_objectives},
                description="Normal operations - balanced weights",
            ),
            ContextType.EMERGENCY: ContextProfile(
                context=ContextType.EMERGENCY,
                weight_multipliers={
                    "coverage": 2.0,
                    "resilience": 1.5,
                    "equity": 0.5,
                    "preference_satisfaction": 0.3,
                },
                description="Emergency - prioritize coverage and resilience",
            ),
            ContextType.UNDERSTAFFED: ContextProfile(
                context=ContextType.UNDERSTAFFED,
                weight_multipliers={
                    "coverage": 1.8,
                    "workload_balance": 1.5,
                    "equity": 0.7,
                },
                description="Understaffed - focus on coverage and balance",
            ),
            ContextType.TRAINING: ContextProfile(
                context=ContextType.TRAINING,
                weight_multipliers={
                    "supervision": 2.0,
                    "coverage": 0.8,
                },
                description="Training period - prioritize supervision",
            ),
            ContextType.HOLIDAY: ContextProfile(
                context=ContextType.HOLIDAY,
                weight_multipliers={
                    "preference_satisfaction": 1.5,
                    "equity": 1.3,
                },
                description="Holiday period - respect preferences",
            ),
        }

        self.current_context = ContextType.NORMAL

    def set_profile(self, profile: ContextProfile) -> None:
        """Set or update a context profile."""
        self.profiles[profile.context] = profile

    def get_profile(self, context: ContextType) -> ContextProfile:
        """Get profile for a context."""
        return self.profiles.get(
            context,
            self.profiles[ContextType.NORMAL],
        )

    def switch_context(self, context: ContextType) -> dict[str, float]:
        """
        Switch to a new context.

        Args:
            context: New context type

        Returns:
            Weight multipliers for the new context
        """
        self.current_context = context
        profile = self.get_profile(context)
        return dict(profile.weight_multipliers)

    def apply_context(
        self,
        base_weights: dict[str, float],
        context: ContextType | None = None,
    ) -> dict[str, float]:
        """
        Apply context-specific adjustments to base weights.

        Args:
            base_weights: Base weight values
            context: Context to apply (or current if None)

        Returns:
            Adjusted weights
        """
        ctx = context or self.current_context
        profile = self.get_profile(ctx)

        adjusted = {}
        for obj_name, weight in base_weights.items():
            multiplier = profile.weight_multipliers.get(obj_name, 1.0)
            adjusted[obj_name] = weight * multiplier

        # Normalize
        total = sum(adjusted.values())
        if total > 0:
            adjusted = {k: v / total for k, v in adjusted.items()}

        return adjusted


@dataclass
class TemporalSchedule:
    """Schedule for time-based weight changes."""

    start_time: datetime
    end_time: datetime
    weight_profile: dict[str, float]
    reason: str
    priority: int = 0  # Higher priority overrides


class TemporalReweighter:
    """
    Time-based weight scheduling.

    Applies different weight profiles based on time, supporting:
    - Scheduled weight changes
    - Recurring patterns (daily, weekly)
    - Phase-based optimization
    """

    def __init__(self, objectives: list[ObjectiveConfig]):
        """
        Initialize temporal reweighter.

        Args:
            objectives: List of objective configurations
        """
        self.objectives = objectives
        self.active_objectives = [o for o in objectives if not o.is_constraint]

        # Scheduled weight changes
        self.schedules: list[TemporalSchedule] = []

        # Default weights
        self.default_weights = {o.name: o.weight for o in self.active_objectives}

    def add_schedule(self, schedule: TemporalSchedule) -> None:
        """Add a scheduled weight change."""
        self.schedules.append(schedule)
        # Sort by priority (higher first)
        self.schedules.sort(key=lambda s: -s.priority)

    def remove_schedule(self, start_time: datetime) -> None:
        """Remove a schedule by start time."""
        self.schedules = [s for s in self.schedules if s.start_time != start_time]

    def get_weights_at(self, time: datetime) -> dict[str, float]:
        """
        Get weights for a specific time.

        Args:
            time: Time to get weights for

        Returns:
            Weight values at that time
        """
        # Find active schedules
        for schedule in self.schedules:
            if schedule.start_time <= time <= schedule.end_time:
                return dict(schedule.weight_profile)

        return dict(self.default_weights)

    def get_current_weights(self) -> dict[str, float]:
        """Get weights for current time."""
        return self.get_weights_at(datetime.now())

    def create_phase_schedule(
        self,
        phases: list[tuple[str, dict[str, float], timedelta]],
        start: datetime | None = None,
    ) -> list[TemporalSchedule]:
        """
        Create a sequence of optimization phases.

        Args:
            phases: List of (name, weights, duration) tuples
            start: Start time (default: now)

        Returns:
            Created schedules
        """
        current_time = start or datetime.now()
        created = []

        for name, weights, duration in phases:
            schedule = TemporalSchedule(
                start_time=current_time,
                end_time=current_time + duration,
                weight_profile=weights,
                reason=f"Phase: {name}",
                priority=1,
            )
            self.add_schedule(schedule)
            created.append(schedule)
            current_time += duration

        return created


class DynamicReweighter:
    """
    Complete dynamic reweighting system.

    Integrates feedback processing, context awareness, and temporal
    scheduling into a unified reweighting mechanism.
    """

    def __init__(
        self,
        objectives: list[ObjectiveConfig],
        learning_rate: float = 0.1,
    ):
        """
        Initialize dynamic reweighter.

        Args:
            objectives: List of objective configurations
            learning_rate: Learning rate for feedback adjustment
        """
        self.objectives = objectives

        # Initialize components
        self.feedback_processor = FeedbackProcessor(objectives, learning_rate)
        self.adjuster = ObjectiveAdjuster(objectives)
        self.contextual = ContextualReweighter(objectives)
        self.temporal = TemporalReweighter(objectives)

        # State
        self.auto_adjust = True  # Whether to auto-apply feedback
        self.current_context = ContextType.NORMAL

    def process_feedback(
        self,
        feedback_type: FeedbackType,
        data: dict[str, Any],
        apply_immediately: bool = True,
    ) -> dict[str, float]:
        """
        Process user feedback.

        Args:
            feedback_type: Type of feedback
            data: Feedback data
            apply_immediately: Whether to apply weight changes

        Returns:
            New weight values
        """
        event = FeedbackEvent(
            feedback_type=feedback_type,
            timestamp=datetime.now(),
            data=data,
        )

        deltas = self.feedback_processor.process_feedback(event)

        if apply_immediately and self.auto_adjust:
            return self.adjuster.apply_deltas(
                deltas, f"Feedback: {feedback_type.value}", event
            )

        return self.adjuster.get_weights()

    def set_context(self, context: ContextType) -> dict[str, float]:
        """
        Set operational context.

        Args:
            context: New context

        Returns:
            Adjusted weights for context
        """
        self.current_context = context
        multipliers = self.contextual.switch_context(context)

        # Apply to current weights
        base_weights = self.adjuster.get_weights()
        adjusted = self.contextual.apply_context(base_weights, context)

        return self.adjuster.set_weights(adjusted, f"Context: {context.value}")

    def get_weights(self) -> dict[str, float]:
        """
        Get current weights.

        Combines temporal schedule with context adjustments.
        """
        # Start with temporal weights
        weights = self.temporal.get_current_weights()

        # Apply context
        weights = self.contextual.apply_context(weights, self.current_context)

        return weights

    def schedule_weights(
        self,
        weights: dict[str, float],
        start: datetime,
        end: datetime,
        reason: str = "Scheduled change",
    ) -> None:
        """
        Schedule a weight change.

        Args:
            weights: Weight values
            start: Start time
            end: End time
            reason: Reason for change
        """
        schedule = TemporalSchedule(
            start_time=start,
            end_time=end,
            weight_profile=weights,
            reason=reason,
        )
        self.temporal.add_schedule(schedule)

    def boost_objective(
        self,
        objective: str,
        factor: float = 1.5,
        duration: timedelta | None = None,
    ) -> dict[str, float]:
        """
        Temporarily boost an objective's weight.

        Boosting multiplies the objective's weight by the factor, then
        renormalizes to maintain sum=1. This ensures the boosted objective
        gets a proportionally higher weight relative to others.

        Args:
            objective: Objective to boost
            factor: Multiplication factor
            duration: How long to boost (None = permanent)

        Returns:
            New weights (normalized to sum to 1)
        """
        current = self.adjuster.get_weights()
        new_weights = dict(current)

        if objective in new_weights:
            # Multiply the target objective's weight
            new_weights[objective] *= factor

            # Normalize to sum to 1 (bypassing bounds for boost)
            total = sum(new_weights.values())
            if total > 0:
                new_weights = {k: v / total for k, v in new_weights.items()}

            if duration:
                # Schedule temporary boost
                self.schedule_weights(
                    new_weights,
                    datetime.now(),
                    datetime.now() + duration,
                    f"Boost {objective}",
                )
                return new_weights
            else:
                # Permanent change - update adjuster directly
                self.adjuster.weights = new_weights
                state = WeightState(
                    weights=dict(new_weights),
                    timestamp=datetime.now(),
                    reason=f"Boost {objective} by {factor}x",
                )
                self.adjuster.history.append(state)
                return dict(new_weights)

        return current

    def balance_weights(self) -> dict[str, float]:
        """Reset to equal weights for all objectives."""
        n = len(self.adjuster.active_objectives)
        equal_weights = {o.name: 1.0 / n for o in self.adjuster.active_objectives}
        return self.adjuster.set_weights(equal_weights, "Balance reset")

    def get_adjustment_summary(self) -> dict[str, Any]:
        """Get summary of all adjustments made."""
        return {
            "current_weights": self.adjuster.get_weights(),
            "current_context": self.current_context.value,
            "feedback_history_length": len(self.feedback_processor.history),
            "cumulative_signals": self.feedback_processor.get_cumulative_adjustments(),
            "adjustment_history_length": len(self.adjuster.history),
            "active_schedules": len(self.temporal.schedules),
        }
