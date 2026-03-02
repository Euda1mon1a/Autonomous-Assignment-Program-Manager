"""
ARCHETYPE: Call-Related Scheduling Constraint
==============================================
Reference implementation for LLMs generating constraint code that operates
on overnight call variables. Read ALL # INVARIANT: comments before writing
any call-related constraint.

This archetype demonstrates correct patterns for:
- Faculty index lookups (call_eligible_faculty_idx, NOT resident_idx)
- Reading solver variables (never initializing them)
- Constraint count logging (0 constraints = dead code)

Anti-patterns this prevents (from real bugs):
- ARCH-001: resident_idx.get(faculty_uuid) always returns None for faculty
- ARCH-002: Initializing variables["call_assignments"] = {} overwrites solver vars
- ARCH-003: context.faculty includes adjuncts who shouldn't take solver call
- ARCH-004: Silent add_to_cpsat() hides dead code

Enforcement: scripts/archetype-check.py (pre-commit hook)
Suppression: # @archetype-ok comment on flagged line
"""

import logging
from typing import Any

from .base import (
    ConstraintPriority,
    ConstraintResult,
    ConstraintType,
    ConstraintViolation,
    HardConstraint,
    SchedulingContext,
)

logger = logging.getLogger(__name__)


class ArchetypeCallConstraint(HardConstraint):
    """
    Example call constraint — blocks ineligible faculty from overnight call.

    # INVARIANT: Call constraints iterate call_eligible_faculty, NEVER context.faculty
    #   context.faculty includes adjuncts. call_eligible_faculty excludes them.
    #   Adjuncts are manually scheduled for call, not solver-scheduled.
    #
    # INVARIANT: Faculty index from call_eligible_faculty_idx, NEVER resident_idx
    #   resident_idx maps RESIDENT UUIDs → int. Faculty UUIDs are not in it.
    #   Using resident_idx.get(faculty.id) always returns None → dead code.
    #
    # INVARIANT: READ variables.get("call_assignments", {}), NEVER initialize
    #   The solver (solvers.py:935-966) creates call BoolVars for all eligible
    #   faculty on all Sun-Thu nights. Constraints constrain these existing vars.
    #   Initializing variables["call_assignments"] = {} would erase solver vars.
    #
    # INVARIANT: Log constraint count at end of add_to_cpsat()
    #   If count is 0, the constraint is likely dead code. Logging makes this
    #   visible during schedule generation.
    #
    # INVARIANT: Call variable keys are (f_i, b_i, "overnight")
    #   f_i from call_eligible_faculty_idx, b_i from block_idx
    """

    def __init__(self) -> None:
        super().__init__(
            name="ArchetypeCall",
            constraint_type=ConstraintType.CALL,
            priority=ConstraintPriority.HIGH,
        )

    def add_to_cpsat(
        self,
        model: Any,
        variables: dict[str, Any],
        context: SchedulingContext,
    ) -> None:
        # INVARIANT: READ existing solver variables. Never create/initialize.
        call_vars = variables.get("call_assignments", {})
        if not call_vars:
            return  # No solver-created variables to constrain

        # INVARIANT: Use call_eligible_faculty for call constraints.
        # Fallback to context.faculty only if call_eligible_faculty is empty
        # (backwards compat with tests that don't populate it).
        call_eligible = context.call_eligible_faculty or context.faculty
        if not call_eligible:
            return

        # INVARIANT: Use call_eligible_faculty_idx, NEVER resident_idx.
        call_idx = context.call_eligible_faculty_idx or {
            fac.id: i for i, fac in enumerate(call_eligible)
        }

        constraint_count = 0

        for faculty in call_eligible:
            # INVARIANT: call_eligible_faculty_idx for f_i lookup
            f_i = call_idx.get(faculty.id)
            if f_i is None:
                continue

            for block in context.blocks:
                b_i = context.block_idx.get(block.id)
                if b_i is None:
                    continue

                key = (f_i, b_i, "overnight")
                if key not in call_vars:
                    continue

                # --- Your constraint logic here ---
                # Example: block call if faculty is ineligible this night
                # model.Add(call_vars[key] == 0)
                constraint_count += 1

        # INVARIANT: Always log constraint count
        if constraint_count:
            logger.info(f"ArchetypeCall: added {constraint_count} constraints")
        else:
            logger.warning("ArchetypeCall: 0 constraints added — possible dead code")

    def add_to_pulp(
        self,
        model: Any,
        variables: dict[str, Any],
        context: SchedulingContext,
    ) -> None:
        """Mirror CP-SAT logic with PuLP syntax. Same invariants apply."""
        call_vars = variables.get("call_assignments", {})
        if not call_vars:
            return

        call_eligible = context.call_eligible_faculty or context.faculty
        if not call_eligible:
            return

        call_idx = context.call_eligible_faculty_idx or {
            fac.id: i for i, fac in enumerate(call_eligible)
        }

        constraint_count = 0

        for faculty in call_eligible:
            f_i = call_idx.get(faculty.id)
            if f_i is None:
                continue

            for block in context.blocks:
                b_i = context.block_idx.get(block.id)
                if b_i is None:
                    continue

                key = (f_i, b_i, "overnight")
                if key not in call_vars:
                    continue

                # model += (call_vars[key] == 0, f"block_{f_i}_{b_i}")
                constraint_count += 1

        if constraint_count:
            logger.info(f"ArchetypeCall: added {constraint_count} PuLP constraints")

    def validate(
        self,
        assignments: list[Any],
        context: SchedulingContext,
    ) -> ConstraintResult:
        """Validate constraint satisfaction against realized assignments."""
        violations: list[ConstraintViolation] = []
        # --- Your validation logic here ---
        return ConstraintResult(
            satisfied=len(violations) == 0,
            violations=violations,
        )
