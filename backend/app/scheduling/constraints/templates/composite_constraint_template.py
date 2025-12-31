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


***REMOVED*** Example Composites
***REMOVED***
***REMOVED*** class CompositeFMITConstraint(CompositeConstraint):
***REMOVED***     '''FMIT program constraints (mandatory call, staffing, continuity).'''
***REMOVED***     def __init__(self):
***REMOVED***         super().__init__(
***REMOVED***             name="FMIT",
***REMOVED***             constraints=[
***REMOVED***                 FMITMandatoryCallConstraint(),
***REMOVED***                 FMITStaffingFloorConstraint(),
***REMOVED***                 FMITContinuityTurfConstraint(),
***REMOVED***                 FMITWeekBlockingConstraint(),
***REMOVED***             ]
***REMOVED***         )
***REMOVED***
***REMOVED*** class CompositeCallConstraint(CompositeConstraint):
***REMOVED***     '''All call-related constraints.'''
***REMOVED***     def __init__(self):
***REMOVED***         super().__init__(
***REMOVED***             name="CallManagement",
***REMOVED***             constraints=[
***REMOVED***                 OvernightCallCoverageConstraint(),
***REMOVED***                 CallSpacingConstraint(),
***REMOVED***                 CallAvailabilityConstraint(),
***REMOVED***                 AdjunctCallExclusionConstraint(),
***REMOVED***             ]
***REMOVED***         )
***REMOVED***
***REMOVED*** class CompositeWednesdayConstraint(CompositeConstraint):
***REMOVED***     '''Wednesday-specific constraints.'''
***REMOVED***     def __init__(self):
***REMOVED***         super().__init__(
***REMOVED***             name="WednesdayManagement",
***REMOVED***             constraints=[
***REMOVED***                 WednesdayAMInternOnlyConstraint(),
***REMOVED***                 WednesdayPMSingleFacultyConstraint(),
***REMOVED***                 InvertedWednesdayConstraint(),
***REMOVED***             ]
***REMOVED***         )
