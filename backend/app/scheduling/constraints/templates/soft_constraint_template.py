"""
Soft Constraint Template

This is a template for implementing soft constraints in the scheduling system.
Soft constraints are optimization objectives with associated weights.
Violations add penalties to the objective function rather than making
the schedule infeasible.

Usage:
    1. Copy this file to a new module in backend/app/scheduling/constraints/
    2. Replace 'MyConstraint' with your constraint name
    3. Implement add_to_cpsat() and add_to_pulp() methods (using weights)
    4. Implement validate() method (returning penalties)
    5. Add unit tests
    6. Register constraint in manager.py imports

Example:
    class PreferenceOptimizationConstraint(SoftConstraint):
        '''Optimizes for faculty scheduling preferences.'''
        ...
"""

from typing import Any

from app.scheduling.constraints.base import (
    ConstraintPriority,
    ConstraintResult,
    ConstraintType,
    ConstraintViolation,
    SchedulingContext,
    SoftConstraint,
)


class MyConstraint(SoftConstraint):
    """
    Brief description of constraint.

    This is a soft constraint that optimizes for [business logic].
    Violations add penalties to the objective function rather than
    making the schedule infeasible.

    Penalty Calculation:
        For each violation:
            penalty = weight * priority.value * violation_severity

        Where:
        - weight: Constraint importance (typical 0.5-2.0)
        - priority.value: CRITICAL=100, HIGH=75, MEDIUM=50, LOW=25
        - violation_severity: Typically 1.0 per violation

    Parameters:
        - weight: Constraint weight (default 1.0)
        - priority: CRITICAL/HIGH/MEDIUM/LOW (default MEDIUM)
        - param1: Description of parameter 1
        - param2: Description of parameter 2

    Weight Selection Guide:
        - 0.1-0.5: Very low priority (nice-to-have)
        - 0.5-1.0: Low priority (optimization)
        - 1.0-1.5: Medium priority (important)
        - 1.5-2.5: High priority (very important)
        - 2.5+: Critical (enforce strongly)

    Typical Violations:
        - Violation type 1
        - Violation type 2

    Examples:
        >>> ***REMOVED*** Low weight constraint
        >>> constraint = MyConstraint(weight=0.5)
        >>> result = constraint.validate(assignments, context)
        >>> print(f"Penalty: {result.penalty}")
    """

    def __init__(
        self,
        weight: float = 1.0,
        priority: ConstraintPriority = ConstraintPriority.MEDIUM,
    ) -> None:
        """
        Initialize the soft constraint.

        Args:
            weight: Constraint weight for penalty calculation (default 1.0)
            priority: Constraint priority level (default MEDIUM)

        Weight Selection:
            - Use lower weights for optional preferences (0.1-0.5)
            - Use medium weights for important but not critical (1.0-1.5)
            - Use higher weights for critical soft constraints (1.5+)

        Priority Selection:
            - CRITICAL (100): System-critical optimization (rare for soft)
            - HIGH (75): Important optimization objectives
            - MEDIUM (50): Regular optimization objectives (default)
            - LOW (25): Nice-to-have preferences
        """
        super().__init__(
            name="MyConstraint",
            constraint_type=ConstraintType.PREFERENCE,  ***REMOVED*** Change to appropriate type
            weight=weight,
            priority=priority,
        )
        ***REMOVED*** Add any constraint-specific initialization here
        self.param1 = None
        self.param2 = None

    def add_to_cpsat(
        self,
        model: Any,
        variables: dict[str, Any],
        context: SchedulingContext,
    ) -> None:
        """
        Add constraint to OR-Tools CP-SAT model as optimization objective.

        For soft constraints, add weighted penalty terms to the objective
        function rather than hard constraints.

        Args:
            model: OR-Tools CP-SAT CpModel instance
            variables: Dict of decision variables indexed by name
            context: SchedulingContext with data needed for constraint

        Implementation:
            1. Extract needed variables
            2. Build expressions for penalty calculation
            3. Add to model objective using weights

        Example:
            >>> x = variables.get("assignments", {})
            >>> objective_terms = []
            >>> for resident in context.residents:
            ...     r_i = context.resident_idx[resident.id]
            ...     for block in context.blocks:
            ...         b_i = context.block_idx[block.id]
            ...         ***REMOVED*** Weight penalty by constraint weight
            ...         penalty = self.weight * x[r_i, b_i]
            ...         objective_terms.append(penalty)
            >>> ***REMOVED*** Add to model objective (if using additive model)
        """
        ***REMOVED*** Get decision variables
        x = variables.get("assignments", {})

        ***REMOVED*** Build penalty terms weighted by constraint weight and priority
        penalty_weight = self.weight * self.priority.value

        ***REMOVED*** Iterate over relevant entities to build penalty expressions
        for resident in context.residents:
            r_i = context.resident_idx[resident.id]

            for block in context.blocks:
                b_i = context.block_idx[block.id]

                ***REMOVED*** Build penalty terms
                ***REMOVED*** Example: violation_count = x[r_i, b_i]
                ***REMOVED*** penalty = penalty_weight * violation_count

        ***REMOVED*** Add penalty terms to objective function
        ***REMOVED*** This depends on how the solver is structured (see solver code)

    def add_to_pulp(
        self,
        model: Any,
        variables: dict[str, Any],
        context: SchedulingContext,
    ) -> None:
        """
        Add constraint to PuLP model as objective contribution.

        For soft constraints in PuLP, add weighted expressions to the
        objective function using += operator.

        Args:
            model: PuLP LpProblem instance
            variables: Dict of decision variables indexed by name
            context: SchedulingContext with data needed for constraint

        Implementation:
            1. Extract needed variables
            2. Build expressions for penalty
            3. Add to model objective

        Example:
            >>> x = variables.get("assignments", {})
            >>> for resident in context.residents:
            ...     r_i = context.resident_idx[resident.id]
            ...     for block in context.blocks:
            ...         b_i = context.block_idx[block.id]
            ...         ***REMOVED*** Add to objective with weight
            ...         model += self.weight * x[r_i, b_i]
        """
        ***REMOVED*** Get decision variables
        x = variables.get("assignments", {})

        ***REMOVED*** Calculate penalty weight
        penalty_weight = self.weight * self.priority.value

        ***REMOVED*** Iterate to build penalty expressions
        for resident in context.residents:
            r_i = context.resident_idx[resident.id]

            for block in context.blocks:
                b_i = context.block_idx[block.id]

                ***REMOVED*** Build penalty expression and add to objective
                ***REMOVED*** Example: model += penalty_weight * x[r_i, b_i]

    def validate(
        self,
        assignments: list[Any],
        context: SchedulingContext,
    ) -> ConstraintResult:
        """
        Validate constraint and calculate penalties.

        For soft constraints, this calculates the penalty for violations.
        The schedule is still feasible but has a higher objective value.

        Args:
            assignments: List of Assignment objects to validate
            context: SchedulingContext with lookup data

        Returns:
            ConstraintResult:
                - satisfied: True if no violations (can be ignored for soft)
                - violations: List of violations (for reporting)
                - penalty: Total penalty from all violations

        Penalty Calculation:
            total_penalty = sum(
                weight * priority.value * violation_count
                for each violation
            )

        Implementation:
            1. Count violations or calculate violation severity
            2. Calculate penalty: weight * priority * violation_count
            3. Return ConstraintResult with violations and penalty

        Example:
            >>> violations = []
            >>> violation_count = 0
            >>> for assignment in assignments:
            ...     if not meets_preference(assignment):
            ...         violation_count += 1
            ...         violations.append(ConstraintViolation(...))
            >>> penalty = self.get_penalty(violation_count)
            >>> return ConstraintResult(
            ...     satisfied=(violation_count == 0),
            ...     violations=violations,
            ...     penalty=penalty,
            ... )
        """
        violations = []
        violation_count = 0

        ***REMOVED*** Count violations for each assignment
        for assignment in assignments:
            if self._violates_constraint(assignment, context):
                violation_count += 1
                violations.append(
                    ConstraintViolation(
                        constraint_name=self.name,
                        constraint_type=self.constraint_type,
                        severity="MEDIUM",  ***REMOVED*** Soft constraint severity
                        message="Description of what was violated",
                        person_id=assignment.person_id,
                        block_id=assignment.block_id,
                    )
                )

        ***REMOVED*** Calculate total penalty
        penalty = self.get_penalty(violation_count)

        return ConstraintResult(
            satisfied=(violation_count == 0),
            violations=violations,
            penalty=penalty,
        )

    def _violates_constraint(
        self,
        assignment: Any,
        context: SchedulingContext,
    ) -> bool:
        """
        Check if a single assignment violates the constraint.

        Helper method for constraint logic.

        Args:
            assignment: Assignment object to check
            context: SchedulingContext

        Returns:
            bool: True if assignment violates constraint, False otherwise
        """
        ***REMOVED*** Implement constraint check logic
        return False


***REMOVED*** Weight and Priority Guidelines
***REMOVED***
***REMOVED*** Common Weight Patterns:
***REMOVED*** ┌─────────────────────────────────────────────────────────────────┐
***REMOVED*** │ Constraint Type        │ Weight  │ Priority │ Purpose            │
***REMOVED*** ├─────────────────────────────────────────────────────────────────┤
***REMOVED*** │ Hard preferences       │ 2.0-3.0 │ HIGH     │ Must satisfy       │
***REMOVED*** │ Fair distribution      │ 1.5-2.0 │ MEDIUM   │ Equity objectives  │
***REMOVED*** │ Continuity of care     │ 1.5-2.0 │ MEDIUM   │ Patient continuity │
***REMOVED*** │ Faculty preferences    │ 0.5-1.0 │ MEDIUM   │ Personnel retention│
***REMOVED*** │ Optimization           │ 0.1-0.5 │ LOW      │ Fine-tuning        │
***REMOVED*** └─────────────────────────────────────────────────────────────────┘
***REMOVED***
***REMOVED*** Priority Effects on Penalty:
***REMOVED*** - CRITICAL (100): weight * 100
***REMOVED*** - HIGH (75): weight * 75
***REMOVED*** - MEDIUM (50): weight * 50
***REMOVED*** - LOW (25): weight * 25
***REMOVED***
***REMOVED*** Example: weight=1.5, priority=HIGH => penalty multiplier = 1.5 * 75 = 112.5
