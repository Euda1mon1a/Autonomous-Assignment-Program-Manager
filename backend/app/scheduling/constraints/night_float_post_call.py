"""
Night Float Post-Call Constraint.

This module enforces mandatory Post-Call (PC) days after Night Float rotations.

See docs/architecture/FACULTY_SCHEDULING_SPECIFICATION.md for full details.

Post-Call Rules for Night Float:
    - When NF ends (block-half transition or block boundary):
        - Next day AM: PC (Post-Call Recovery)
        - Next day PM: PC (Post-Call Recovery)
    - PC is a FULL DAY (both AM and PM blocked)
    - PC trumps any other rotation assignment

Block-half transitions:
    - NF in block-half 1 (Days 1-14) → Day 15 = PC (start of block-half 2)
    - NF in block-half 2 (Days 15-28) → Day 1 of next block = PC

Classes:
    - NightFloatPostCallConstraint: Force PC day after NF ends
"""
import logging
from collections import defaultdict
from datetime import date, timedelta
from typing import Any, Optional

from .base import (
    ConstraintPriority,
    ConstraintResult,
    ConstraintType,
    ConstraintViolation,
    HardConstraint,
    SchedulingContext,
)

logger = logging.getLogger(__name__)


class NightFloatPostCallConstraint(HardConstraint):
    """
    Enforces PC (Post-Call) full day after Night Float ends.

    When a resident finishes their Night Float rotation (either mid-block
    or at block boundary), the next day MUST be Post-Call for both AM and PM.

    This constraint:
    1. Detects NF assignments that end at block-half or block boundaries
    2. Forces PC assignment for the following day (AM + PM)
    3. Blocks any other rotation from being assigned on PC day
    4. Validates existing schedules for compliance

    Implementation:
    - For NF in block-half 1: Day 15 (first day of half 2) = PC
    - For NF in block-half 2: Day 1 of next block = PC
    - PC trumps whatever the next rotation would have scheduled
    """

    # Activity type identifiers
    NF_ABBREVIATION = "NF"  # Night Float abbreviation
    PC_ABBREVIATION = "PC"  # Post-Call abbreviation

    def __init__(self) -> None:
        """Initialize Night Float post-call constraint."""
        super().__init__(
            name="NightFloatPostCall",
            constraint_type=ConstraintType.ROTATION,
            priority=ConstraintPriority.CRITICAL,
        )

    def add_to_cpsat(
        self,
        model: Any,
        variables: dict[str, Any],
        context: SchedulingContext,
    ) -> None:
        """
        Add Night Float post-call constraints to CP-SAT model.

        For each resident with NF assignment ending at block-half boundary:
        - Force PC for next day AM and PM blocks
        """
        template_vars = variables.get("template_assignments", {})

        if not template_vars:
            return

        # Find NF and PC template IDs
        nf_template_id = self._find_template_id(context, self.NF_ABBREVIATION)
        pc_template_id = self._find_template_id(context, self.PC_ABBREVIATION)

        if not nf_template_id or not pc_template_id:
            logger.warning(
                "NF or PC templates not found - Night Float post-call constraint inactive"
            )
            return

        nf_t_i = context.template_idx.get(nf_template_id)
        pc_t_i = context.template_idx.get(pc_template_id)

        if nf_t_i is None or pc_t_i is None:
            return

        # Group blocks by date and time
        blocks_by_date_time = self._group_blocks_by_date_time(context)

        # Get block-half transition days
        transition_days = self._get_block_half_transition_days(context)

        # For each resident
        for resident in context.residents:
            r_i = context.resident_idx.get(resident.id)
            if r_i is None:
                continue

            # For each block-half transition day
            for transition_date, prev_half_blocks in transition_days.items():
                # Check if any NF assignment exists on the last day of previous half
                nf_on_last_day = False
                for block in prev_half_blocks:
                    b_i = context.block_idx.get(block.id)
                    if b_i is None:
                        continue

                    if (r_i, b_i, nf_t_i) in template_vars:
                        nf_var = template_vars[r_i, b_i, nf_t_i]
                        # Find PC day blocks (transition_date is the PC day)
                        am_blocks = blocks_by_date_time.get((transition_date, "AM"), [])
                        pm_blocks = blocks_by_date_time.get((transition_date, "PM"), [])

                        # If NF on last day => PC on transition day (both AM and PM)
                        for am_block in am_blocks:
                            am_b_i = context.block_idx.get(am_block.id)
                            if am_b_i is not None and (r_i, am_b_i, pc_t_i) in template_vars:
                                # nf_var == 1 => pc_am_var == 1
                                model.AddImplication(nf_var, template_vars[r_i, am_b_i, pc_t_i])

                        for pm_block in pm_blocks:
                            pm_b_i = context.block_idx.get(pm_block.id)
                            if pm_b_i is not None and (r_i, pm_b_i, pc_t_i) in template_vars:
                                # nf_var == 1 => pc_pm_var == 1
                                model.AddImplication(nf_var, template_vars[r_i, pm_b_i, pc_t_i])

    def add_to_pulp(
        self,
        model: Any,
        variables: dict[str, Any],
        context: SchedulingContext,
    ) -> None:
        """Add Night Float post-call constraints to PuLP model."""
        template_vars = variables.get("template_assignments", {})

        if not template_vars:
            return

        nf_template_id = self._find_template_id(context, self.NF_ABBREVIATION)
        pc_template_id = self._find_template_id(context, self.PC_ABBREVIATION)

        if not nf_template_id or not pc_template_id:
            return

        nf_t_i = context.template_idx.get(nf_template_id)
        pc_t_i = context.template_idx.get(pc_template_id)

        if nf_t_i is None or pc_t_i is None:
            return

        blocks_by_date_time = self._group_blocks_by_date_time(context)
        transition_days = self._get_block_half_transition_days(context)
        constraint_count = 0

        for resident in context.residents:
            r_i = context.resident_idx.get(resident.id)
            if r_i is None:
                continue

            for transition_date, prev_half_blocks in transition_days.items():
                for block in prev_half_blocks:
                    b_i = context.block_idx.get(block.id)
                    if b_i is None:
                        continue

                    if (r_i, b_i, nf_t_i) not in template_vars:
                        continue

                    nf_var = template_vars[r_i, b_i, nf_t_i]
                    am_blocks = blocks_by_date_time.get((transition_date, "AM"), [])
                    pm_blocks = blocks_by_date_time.get((transition_date, "PM"), [])

                    # Implication as linear constraint: pc >= nf
                    for am_block in am_blocks:
                        am_b_i = context.block_idx.get(am_block.id)
                        if am_b_i is not None and (r_i, am_b_i, pc_t_i) in template_vars:
                            model += (
                                template_vars[r_i, am_b_i, pc_t_i] >= nf_var,
                                f"nf_post_call_am_{r_i}_{b_i}_{constraint_count}"
                            )
                            constraint_count += 1

                    for pm_block in pm_blocks:
                        pm_b_i = context.block_idx.get(pm_block.id)
                        if pm_b_i is not None and (r_i, pm_b_i, pc_t_i) in template_vars:
                            model += (
                                template_vars[r_i, pm_b_i, pc_t_i] >= nf_var,
                                f"nf_post_call_pm_{r_i}_{b_i}_{constraint_count}"
                            )
                            constraint_count += 1

    def validate(
        self,
        assignments: list[Any],
        context: SchedulingContext,
    ) -> ConstraintResult:
        """
        Validate Night Float post-call assignments.

        Checks that residents with NF assignments ending at block-half boundary
        have PC assigned for both AM and PM of the following day.
        """
        violations: list[ConstraintViolation] = []

        # Find NF and PC template IDs
        nf_template_id = self._find_template_id(context, self.NF_ABBREVIATION)
        pc_template_id = self._find_template_id(context, self.PC_ABBREVIATION)

        if not nf_template_id or not pc_template_id:
            # No templates, can't validate
            return ConstraintResult(satisfied=True, violations=[])

        # Build lookups
        resident_by_id = {r.id: r for r in context.residents}
        block_by_id = {b.id: b for b in context.blocks}

        # Group assignments by person, date, time_of_day
        assignments_by_person_date_time = defaultdict(list)
        for a in assignments:
            block = block_by_id.get(a.block_id)
            if block and hasattr(block, 'time_of_day'):
                key = (a.person_id, block.date, block.time_of_day)
                assignments_by_person_date_time[key].append(a)

        # Find NF assignments on last day of each block-half
        transition_days = self._get_block_half_transition_days(context)

        for a in assignments:
            if a.rotation_template_id != nf_template_id:
                continue

            block = block_by_id.get(a.block_id)
            resident = resident_by_id.get(a.person_id)

            if not block or not resident:
                continue

            # Check if this block is on the last day of a block-half
            for transition_date, prev_half_blocks in transition_days.items():
                if any(b.id == block.id for b in prev_half_blocks):
                    # This NF assignment is on last day before transition
                    # Check for PC on transition_date

                    # Check AM PC
                    am_assignments = assignments_by_person_date_time.get(
                        (a.person_id, transition_date, "AM"), []
                    )
                    has_pc_am = any(
                        ass.rotation_template_id == pc_template_id
                        for ass in am_assignments
                    )

                    # Check PM PC
                    pm_assignments = assignments_by_person_date_time.get(
                        (a.person_id, transition_date, "PM"), []
                    )
                    has_pc_pm = any(
                        ass.rotation_template_id == pc_template_id
                        for ass in pm_assignments
                    )

                    if not has_pc_am:
                        violations.append(ConstraintViolation(
                            constraint_name=self.name,
                            constraint_type=self.constraint_type,
                            severity="CRITICAL",
                            message=(
                                f"{resident.name} on NF {block.date} missing "
                                f"Post-Call for {transition_date} AM"
                            ),
                            person_id=resident.id,
                            block_id=block.id,
                            details={
                                "nf_end_date": str(block.date),
                                "expected_pc_date": str(transition_date),
                                "time_of_day": "AM",
                            },
                        ))

                    if not has_pc_pm:
                        violations.append(ConstraintViolation(
                            constraint_name=self.name,
                            constraint_type=self.constraint_type,
                            severity="CRITICAL",
                            message=(
                                f"{resident.name} on NF {block.date} missing "
                                f"Post-Call for {transition_date} PM"
                            ),
                            person_id=resident.id,
                            block_id=block.id,
                            details={
                                "nf_end_date": str(block.date),
                                "expected_pc_date": str(transition_date),
                                "time_of_day": "PM",
                            },
                        ))

        return ConstraintResult(
            satisfied=len(violations) == 0,
            violations=violations,
        )

    def _find_template_id(
        self, context: SchedulingContext, abbreviation: str
    ) -> Optional[Any]:
        """Find template ID by abbreviation."""
        for t in context.templates:
            if hasattr(t, 'abbreviation') and t.abbreviation:
                if t.abbreviation.upper() == abbreviation.upper():
                    return t.id
            # Fallback: check name
            if hasattr(t, 'name') and t.name.upper() == abbreviation.upper():
                return t.id
        return None

    def _group_blocks_by_date_time(
        self, context: SchedulingContext
    ) -> dict[tuple[date, str], list[Any]]:
        """Group blocks by (date, time_of_day) for quick lookup."""
        result: dict[tuple[date, str], list[Any]] = defaultdict(list)
        for block in context.blocks:
            if hasattr(block, 'time_of_day'):
                key = (block.date, block.time_of_day)
                result[key].append(block)
        return result

    def _get_block_half_transition_days(
        self, context: SchedulingContext
    ) -> dict[date, list[Any]]:
        """
        Get block-half transition days with their preceding blocks.

        Returns a dict mapping transition_date (PC day) to list of blocks
        on the last day of the previous block-half.

        Block-half transitions occur:
        - Day 14 → Day 15 (mid-block)
        - Day 28 → Day 1 (block boundary)
        """
        result: dict[date, list[Any]] = defaultdict(list)

        # Group blocks by block_number and block_half
        blocks_by_number_half: dict[tuple[int, int], list[Any]] = defaultdict(list)
        for block in context.blocks:
            if hasattr(block, 'block_number') and hasattr(block, 'block_half'):
                key = (block.block_number, block.block_half)
                blocks_by_number_half[key].append(block)

        # Find last day of each block-half
        for (block_num, block_half), blocks in blocks_by_number_half.items():
            if not blocks:
                continue

            # Sort by date to find last day
            sorted_blocks = sorted(blocks, key=lambda b: b.date)
            last_day = sorted_blocks[-1].date
            transition_day = last_day + timedelta(days=1)

            # Get all blocks on last_day (AM and PM)
            last_day_blocks = [b for b in blocks if b.date == last_day]
            result[transition_day].extend(last_day_blocks)

        return result
