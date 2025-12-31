"""
Composite Constraint Template

A composite constraint combines multiple base constraints into a single unit.
This is useful for related constraints that should be managed together.

Example:
    class CompositeFMITConstraint:
        '''Combines FMIT continuity, staffing, and call constraints.'''
        - FMIT Mandatory Call
        - FMIT Staffing Floor
        - FMIT Continuity Turf
        - FMIT Week Blocking
"""

from typing import Any

from app.scheduling.constraints.base import (
    Constraint,
    ConstraintResult,
    SchedulingContext,
)


class CompositeConstraint:
    """
    Combines multiple constraints into a single composite unit.

    This class manages a group of related constraints that should be
    applied together. It provides convenient enable/disable for the group
    and aggregates validation results.

    Example:
        >>> composite = CompositeCallConstraint()
        >>> composite.enable()
        >>> manager.add(composite)
    """

    def __init__(self, name: str, constraints: list[Constraint]) -> None:
        """
        Initialize composite constraint.

        Args:
            name: Composite constraint name
            constraints: List of base constraints to compose
        """
        self.name = name
        self.constraints = constraints
        self.enabled = True

    def enable(self) -> "CompositeConstraint":
        """Enable all constraints in the composite."""
        for constraint in self.constraints:
            constraint.enabled = True
        self.enabled = True
        return self

    def disable(self) -> "CompositeConstraint":
        """Disable all constraints in the composite."""
        for constraint in self.constraints:
            constraint.enabled = False
        self.enabled = False
        return self

    def validate_all(
        self,
        assignments: list[Any],
        context: SchedulingContext,
    ) -> ConstraintResult:
        """Validate all constraints in the composite."""
        all_violations = []
        total_penalty = 0.0
        all_satisfied = True

        for constraint in self.constraints:
            if constraint.enabled:
                result = constraint.validate(assignments, context)
                all_violations.extend(result.violations)
                total_penalty += result.penalty
                if not result.satisfied:
                    all_satisfied = False

        return ConstraintResult(
            satisfied=all_satisfied,
            violations=all_violations,
            penalty=total_penalty,
        )


# Example Composites
#
# class CompositeFMITConstraint(CompositeConstraint):
#     '''FMIT program constraints (mandatory call, staffing, continuity).'''
#     def __init__(self):
#         super().__init__(
#             name="FMIT",
#             constraints=[
#                 FMITMandatoryCallConstraint(),
#                 FMITStaffingFloorConstraint(),
#                 FMITContinuityTurfConstraint(),
#                 FMITWeekBlockingConstraint(),
#             ]
#         )
#
# class CompositeCallConstraint(CompositeConstraint):
#     '''All call-related constraints.'''
#     def __init__(self):
#         super().__init__(
#             name="CallManagement",
#             constraints=[
#                 OvernightCallCoverageConstraint(),
#                 CallSpacingConstraint(),
#                 CallAvailabilityConstraint(),
#                 AdjunctCallExclusionConstraint(),
#             ]
#         )
#
# class CompositeWednesdayConstraint(CompositeConstraint):
#     '''Wednesday-specific constraints.'''
#     def __init__(self):
#         super().__init__(
#             name="WednesdayManagement",
#             constraints=[
#                 WednesdayAMInternOnlyConstraint(),
#                 WednesdayPMSingleFacultyConstraint(),
#                 InvertedWednesdayConstraint(),
#             ]
#         )
