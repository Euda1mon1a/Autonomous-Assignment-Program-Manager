"""
Hard Constraint Template

This is a template for implementing hard constraints in the scheduling system.
Hard constraints must be satisfied for a schedule to be feasible.

Usage:
    1. Copy this file to a new module in backend/app/scheduling/constraints/
    2. Replace 'MyConstraint' with your constraint name
    3. Implement add_to_cpsat() and add_to_pulp() methods
    4. Implement validate() method
    5. Add unit tests
    6. Register constraint in manager.py imports

Example:
    class CustomRotationConstraint(HardConstraint):
        '''Ensures custom rotation business logic.'''
        ...
"""

from typing import Any

from app.scheduling.constraints.base import (
    ConstraintPriority,
    ConstraintResult,
    ConstraintType,
    ConstraintViolation,
    HardConstraint,
    SchedulingContext,
)


class MyConstraint(HardConstraint):
    """
    Brief description of constraint.

    This constraint ensures [business logic]. It is a hard constraint,
    meaning it must be satisfied for a feasible schedule.

    Algorithm:
        1. [Step 1 of validation logic]
        2. [Step 2 of validation logic]
        3. [Return violations]

    Parameters:
        - param1: Description of parameter 1
        - param2: Description of parameter 2

    Typical Violations:
        - Violation type 1
        - Violation type 2

    Examples:
        >>> constraint = MyConstraint()
        >>> result = constraint.validate(assignments, context)
        >>> if result.satisfied:
        ...     print("Constraint satisfied")
    """

    def __init__(self) -> None:
        """
        Initialize the constraint.

        Sets constraint properties: name, type, priority, and enabled flag.
        Adjust priority based on importance:
        - CRITICAL: ACGME requirements, must satisfy
        - HIGH: Essential operational constraints
        - MEDIUM: Optimization objectives
        - LOW: Nice-to-have preferences
        """
        super().__init__(
            name="MyConstraint",
            constraint_type=ConstraintType.AVAILABILITY,  # Change to appropriate type
            priority=ConstraintPriority.HIGH,  # Adjust priority as needed
        )
        # Add any constraint-specific initialization here
        self.param1 = None
        self.param2 = None

    def add_to_cpsat(
        self,
        model: Any,
        variables: dict[str, Any],
        context: SchedulingContext,
    ) -> None:
        """
        Add constraint to OR-Tools CP-SAT model.

        This method is called during optimization to add constraint expressions
        to the CP-SAT solver model.

        Args:
            model: OR-Tools CP-SAT CpModel instance
            variables: Dict of decision variables indexed by name
            context: SchedulingContext with data needed for constraint

        Implementation:
            1. Extract needed variables from variables dict
            2. Extract needed data from context
            3. Add constraints using model.Add()

        Example:
            >>> x = variables.get("assignments", {})
            >>> for resident in context.residents:
            ...     r_i = context.resident_idx[resident.id]
            ...     for block in context.blocks:
            ...         b_i = context.block_idx[block.id]
            ...         # Add constraint: x[r_i, b_i] <= 1
            ...         model.Add(x[r_i, b_i] <= 1)
        """
        # Get decision variables
        x = variables.get("assignments", {})

        # Iterate over relevant entities
        for resident in context.residents:
            r_i = context.resident_idx[resident.id]

            for block in context.blocks:
                b_i = context.block_idx[block.id]

                # Build constraint logic here
                # Example: model.Add(x[r_i, b_i] == 0)  # Prevent assignment

        # Add model.Add() calls for each constraint expression

    def add_to_pulp(
        self,
        model: Any,
        variables: dict[str, Any],
        context: SchedulingContext,
    ) -> None:
        """
        Add constraint to PuLP model.

        This method is called during optimization to add constraint expressions
        to the PuLP solver model. Similar to add_to_cpsat but uses PuLP syntax.

        Args:
            model: PuLP LpProblem instance
            variables: Dict of decision variables indexed by name
            context: SchedulingContext with data needed for constraint

        Implementation:
            1. Extract needed variables from variables dict
            2. Extract needed data from context
            3. Add constraints using model += (constraint, label)

        Example:
            >>> x = variables.get("assignments", {})
            >>> for resident in context.residents:
            ...     r_i = context.resident_idx[resident.id]
            ...     for block in context.blocks:
            ...         b_i = context.block_idx[block.id]
            ...         model += x[r_i, b_i] <= 1, f"const_{r_i}_{b_i}"
        """
        # Get decision variables
        x = variables.get("assignments", {})

        # Iterate over relevant entities
        for resident in context.residents:
            r_i = context.resident_idx[resident.id]

            for block in context.blocks:
                b_i = context.block_idx[block.id]

                # Build constraint logic here
                # Example: model += x[r_i, b_i] == 0, f"const_{r_i}_{b_i}"

        # Add model += (constraint, label) calls for each constraint

    def validate(
        self,
        assignments: list[Any],
        context: SchedulingContext,
    ) -> ConstraintResult:
        """
        Validate constraint against actual assignments.

        This method checks if a proposed schedule satisfies the constraint
        by examining the actual assignment list.

        Args:
            assignments: List of Assignment objects to validate
            context: SchedulingContext with lookup data

        Returns:
            ConstraintResult:
                - satisfied: True if no violations found
                - violations: List of ConstraintViolation objects
                - penalty: 0.0 for hard constraints (violations make infeasible)

        Implementation:
            1. Iterate over assignments
            2. Check constraint logic
            3. Create ConstraintViolation for each violation
            4. Return ConstraintResult

        Example:
            >>> violations = []
            >>> for assignment in assignments:
            ...     if violates_constraint(assignment):
            ...         violations.append(ConstraintViolation(
            ...             constraint_name=self.name,
            ...             constraint_type=self.constraint_type,
            ...             severity="CRITICAL",
            ...             message="Description of violation",
            ...             person_id=assignment.person_id,
            ...             block_id=assignment.block_id,
            ...         ))
            >>> return ConstraintResult(
            ...     satisfied=len(violations) == 0,
            ...     violations=violations,
            ... )
        """
        violations = []

        # Check constraint logic for each assignment
        for assignment in assignments:
            # Example: Check if person is available
            person_id = assignment.person_id
            block_id = assignment.block_id

            # Validate constraint conditions
            if self._violates_constraint(assignment, context):
                violations.append(
                    ConstraintViolation(
                        constraint_name=self.name,
                        constraint_type=self.constraint_type,
                        severity="CRITICAL",  # or HIGH, MEDIUM, LOW
                        message="Description of what was violated and why",
                        person_id=person_id,
                        block_id=block_id,
                        details={
                            "actual_value": "what was found",
                            "expected_value": "what was expected",
                        },
                    )
                )

        return ConstraintResult(
            satisfied=len(violations) == 0,
            violations=violations,
        )

    def _violates_constraint(
        self,
        assignment: Any,
        context: SchedulingContext,
    ) -> bool:
        """
        Check if a single assignment violates the constraint.

        Helper method to encapsulate constraint logic.

        Args:
            assignment: Assignment object to check
            context: SchedulingContext

        Returns:
            bool: True if assignment violates constraint, False otherwise
        """
        # Implement constraint check logic
        return False


# Alternative constraint types can be created by changing the parent class:
#
# class MyHardConstraint(HardConstraint):
#     """Hard constraint - must be satisfied."""
#     ...
#
# class MySoftConstraint(SoftConstraint):
#     """Soft constraint - optimization objective."""
#     def __init__(self, weight: float = 1.0):
#         super().__init__(
#             name="MySoftConstraint",
#             constraint_type=ConstraintType.PREFERENCE,
#             weight=weight,  # Soft constraints have weight
#         )
