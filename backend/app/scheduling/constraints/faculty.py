"""
Faculty and Preference Constraints.

This module contains constraints related to faculty preferences and
scheduling preferences.

Classes:
    - PreferenceConstraint: Optimize based on resident/faculty preferences (soft)
"""
import logging
from uuid import UUID

from .base import (
    ConstraintPriority,
    ConstraintResult,
    ConstraintType,
    SchedulingContext,
    SoftConstraint,
)

logger = logging.getLogger(__name__)


class PreferenceConstraint(SoftConstraint):
    """
    Handles resident preferences for specific rotations, times, or blocks.
    Preferences are stored as a dictionary: {person_id: {rotation_id: preference_score}}
    """

    def __init__(
        self,
        preferences: dict[UUID, dict[UUID, float]] = None,
        weight: float = 2.0,
    ):
        super().__init__(
            name="Preferences",
            constraint_type=ConstraintType.PREFERENCE,
            weight=weight,
            priority=ConstraintPriority.LOW,
        )
        self.preferences = preferences or {}

    def add_to_cpsat(self, model, variables: dict, context: SchedulingContext):
        """Add preference bonus to objective."""
        # Would require template-specific assignment variables
        pass

    def add_to_pulp(self, model, variables: dict, context: SchedulingContext):
        """Add preference bonus to objective."""
        pass

    def validate(self, assignments: list, context: SchedulingContext) -> ConstraintResult:
        """Calculate preference satisfaction."""
        total_preference = 0.0
        max_preference = 0.0

        for a in assignments:
            person_prefs = self.preferences.get(a.person_id, {})
            if a.rotation_template_id:
                pref_score = person_prefs.get(a.rotation_template_id, 0.5)  # Neutral default
                total_preference += pref_score
                max_preference += 1.0

        if max_preference == 0:
            return ConstraintResult(satisfied=True, penalty=0.0)

        satisfaction = total_preference / max_preference
        penalty = (1 - satisfaction) * self.weight * len(assignments)

        return ConstraintResult(
            satisfied=True,
            violations=[],
            penalty=penalty,
        )
