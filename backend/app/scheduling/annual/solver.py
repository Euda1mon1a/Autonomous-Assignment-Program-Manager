"""Annual Rotation Optimizer — CP-SAT solver.

Assigns rotations to blocks for all residents across an academic year,
maximizing leave preference satisfaction while respecting PGY-level constraints.

Model: ~2,200 BoolVars (18 residents x 13 blocks x ~12 rotations with domain reduction).
Solves in <5 seconds on commodity hardware.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from uuid import UUID

from ortools.sat.python import cp_model

from app.scheduling.annual.context import AnnualContext, LeaveRequest, ResidentInfo
from app.scheduling.annual.pgy_config import (
    FIXED_ASSIGNMENTS,
    SEQUENCING_RULES,
    Rotation,
    canonical_capacity_name,
    get_capacity,
    get_eligible_blocks,
)

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RotationAssignment:
    """A single solver result: resident R does rotation T in block B."""

    resident_idx: int
    resident_name: str
    person_id: UUID
    pgy: int
    block_number: int
    rotation_name: str
    rotation_idx: int
    is_fixed: bool
    leave_eligible: bool
    leave_satisfied: (
        bool  # True if a leave request exists and the rotation is leave-eligible
    )


@dataclass
class SolverResult:
    """Complete output from the annual rotation solver."""

    status: str  # "OPTIMAL", "FEASIBLE", "INFEASIBLE", "MODEL_INVALID"
    assignments: list[RotationAssignment] = field(default_factory=list)
    leave_satisfied_count: int = 0
    leave_total_count: int = 0
    objective_value: float = 0.0
    solver_runtime_seconds: float = 0.0
    solver_wall_time_seconds: float = 0.0


def solve(
    context: AnnualContext,
    timeout_seconds: float = 30.0,
    respect_pending_leave: bool = True,
) -> SolverResult:
    """Run the CP-SAT annual rotation optimizer.

    Args:
        context: Populated AnnualContext with residents, rotations, and leave requests.
        timeout_seconds: Solver time limit.
        respect_pending_leave: If True (draft mode), honor all leave requests.
            If False (strict mode), only approved absences would be used
            (filtering happens upstream in the caller).

    Returns:
        SolverResult with assignments and leave satisfaction metrics.
    """
    start_time = time.monotonic()
    model = cp_model.CpModel()

    # ── Build rotation indices per PGY ───────────────────────────────────────

    # For each PGY, create a list of (rotation_idx, Rotation) pairs
    pgy_rot_indices: dict[int, list[tuple[int, Rotation]]] = {}
    all_rotation_names: list[str] = []
    rotation_name_to_global_idx: dict[str, list[int]] = {}  # name -> [global indices]
    # Canonical capacity groups: aliases share one pool
    capacity_group_to_global_idx: dict[str, list[int]] = {}

    global_rot_idx = 0
    for pgy in sorted(context.rotations_by_pgy.keys()):
        pgy_rot_indices[pgy] = []
        for rot in context.rotations_by_pgy[pgy]:
            pgy_rot_indices[pgy].append((global_rot_idx, rot))
            all_rotation_names.append(rot.name)
            rotation_name_to_global_idx.setdefault(rot.name, []).append(global_rot_idx)
            cap_name = canonical_capacity_name(rot.name)
            capacity_group_to_global_idx.setdefault(cap_name, []).append(global_rot_idx)
            global_rot_idx += 1

    num_rotations = global_rot_idx
    block_numbers = context.block_numbers

    logger.info(
        "ARO: %d residents, %d blocks, %d total rotation slots",
        len(context.all_residents),
        len(block_numbers),
        num_rotations,
    )

    # ── Create decision variables ────────────────────────────────────────────
    # x[r, b, t] = 1 iff resident r is assigned rotation t in block b

    x: dict[tuple[int, int, int], cp_model.IntVar] = {}

    for r_idx, resident in enumerate(context.all_residents):
        pgy = resident.pgy
        rot_list = pgy_rot_indices.get(pgy, [])

        for block in block_numbers:
            # Check if this block has a fixed assignment for this PGY
            fixed = FIXED_ASSIGNMENTS.get(pgy, {})
            if block in fixed:
                # Fixed assignment — only create one variable, forced to 1
                for t_idx, rot in rot_list:
                    if rot.name == fixed[block]:
                        var = model.NewBoolVar(f"aro_{r_idx}_{block}_{t_idx}")
                        model.Add(var == 1)
                        x[r_idx, block, t_idx] = var
                        break
                continue

            # Create variables only for eligible rotations in eligible blocks
            for t_idx, rot in rot_list:
                eligible = get_eligible_blocks(rot, pgy)
                if block in eligible:
                    x[r_idx, block, t_idx] = model.NewBoolVar(
                        f"aro_{r_idx}_{block}_{t_idx}"
                    )

    logger.info("ARO: created %d decision variables", len(x))

    # ── H1: Exactly one rotation per resident per block ──────────────────────

    for r_idx, resident in enumerate(context.all_residents):
        pgy = resident.pgy
        for block in block_numbers:
            vars_for_block = [
                x[r_idx, block, t_idx]
                for t_idx, _ in pgy_rot_indices.get(pgy, [])
                if (r_idx, block, t_idx) in x
            ]
            if vars_for_block:
                model.AddExactlyOne(vars_for_block)

    # ── H3: Each required rotation exactly once per resident ─────────────────

    for r_idx, resident in enumerate(context.all_residents):
        pgy = resident.pgy
        for t_idx, rot in pgy_rot_indices.get(pgy, []):
            # Skip fixed assignment rotations — they're already forced
            fixed = FIXED_ASSIGNMENTS.get(pgy, {})
            if rot.name in fixed.values():
                # Fixed rotation: already constrained to exactly 1 via the forced var
                continue

            vars_for_rot = [
                x[r_idx, block, t_idx]
                for block in block_numbers
                if (r_idx, block, t_idx) in x
            ]
            if vars_for_rot:
                model.Add(sum(vars_for_rot) == 1)

    # ── H4: Capacity per block (cross-PGY, alias-aware) ─────────────────────

    # Group by canonical capacity name so aliases share one pool
    for cap_group, global_indices in capacity_group_to_global_idx.items():
        cap = get_capacity(cap_group)
        for block in block_numbers:
            vars_in_block = []
            for g_idx in global_indices:
                for r_idx in range(len(context.all_residents)):
                    if (r_idx, block, g_idx) in x:
                        vars_in_block.append(x[r_idx, block, g_idx])
            if len(vars_in_block) > cap:
                model.Add(sum(vars_in_block) <= cap)

    # ── H6: Sequencing (Kap L+D after TAMC L+D for PGY-1) ──────────────────

    for pgy, rules in SEQUENCING_RULES.items():
        residents_in_pgy = [
            r_idx for r_idx, r in enumerate(context.all_residents) if r.pgy == pgy
        ]
        rot_list = pgy_rot_indices.get(pgy, [])

        for pred_name, succ_name in rules:
            pred_idx = next(
                (t_idx for t_idx, rot in rot_list if rot.name == pred_name), None
            )
            succ_idx = next(
                (t_idx for t_idx, rot in rot_list if rot.name == succ_name), None
            )
            if pred_idx is None or succ_idx is None:
                logger.warning(
                    "ARO: sequencing rule %s->%s: rotation not found",
                    pred_name,
                    succ_name,
                )
                continue

            for r_idx in residents_in_pgy:
                # Auxiliary: done_pred[b] = 1 iff resident has done predecessor
                # in block b or earlier
                done_pred: dict[int, cp_model.IntVar] = {}
                sorted_blocks = sorted(
                    b for b in block_numbers if (r_idx, b, pred_idx) in x
                )

                for i, block in enumerate(sorted_blocks):
                    done_var = model.NewBoolVar(f"done_{pred_name}_{r_idx}_{block}")

                    if i == 0:
                        # First eligible block: done = assigned here
                        if (r_idx, block, pred_idx) in x:
                            model.Add(done_var == x[r_idx, block, pred_idx])
                        else:
                            model.Add(done_var == 0)
                    else:
                        # done[b] = max(done[b-1], x[r, b, pred])
                        prev_block = sorted_blocks[i - 1]
                        if (r_idx, block, pred_idx) in x:
                            model.AddMaxEquality(
                                done_var,
                                [done_pred[prev_block], x[r_idx, block, pred_idx]],
                            )
                        else:
                            model.Add(done_var == done_pred[prev_block])
                    done_pred[block] = done_var

                # Successor in block b requires predecessor done before block b
                for block in block_numbers:
                    if (r_idx, block, succ_idx) not in x:
                        continue
                    # Find the latest block before this one that has done_pred
                    earlier_blocks = [b for b in sorted_blocks if b < block]
                    if earlier_blocks:
                        latest_before = earlier_blocks[-1]
                        # succ can only be 1 if done_pred[latest_before] == 1
                        model.Add(x[r_idx, block, succ_idx] <= done_pred[latest_before])
                    else:
                        # No earlier block possible — can't assign successor here
                        model.Add(x[r_idx, block, succ_idx] == 0)

    # ── S1: Leave satisfaction (primary objective, weight 1000) ──────────────

    sat_vars: list[cp_model.IntVar] = []
    leave_detail: list[tuple[LeaveRequest, cp_model.IntVar]] = []

    for i, lr in enumerate(context.leave_requests):
        r_idx = context.resident_idx.get(lr.person_id)  # type: ignore[assignment]
        if r_idx is None:
            continue

        resident = context.all_residents[r_idx]
        pgy = resident.pgy
        rot_list = pgy_rot_indices.get(pgy, [])
        touched_blocks = [b for b in lr.blocks if b in block_numbers]

        if not touched_blocks:
            continue

        if len(touched_blocks) == 1:
            # Single block — sat = 1 iff on leave-eligible rotation
            b = touched_blocks[0]
            le_vars = [
                x[r_idx, b, t_idx]
                for t_idx, rot in rot_list
                if rot.leave_eligible and (r_idx, b, t_idx) in x
            ]
            if not le_vars:
                continue

            sat = model.NewBoolVar(f"lsat_{r_idx}_{b}_{i}")
            model.Add(sum(le_vars) >= 1).OnlyEnforceIf(sat)
            model.Add(sum(le_vars) == 0).OnlyEnforceIf(sat.Not())
            sat_vars.append(sat)
            leave_detail.append((lr, sat))
        else:
            # Cross-block: ALL touched blocks must be leave-eligible
            block_sats: list[cp_model.IntVar] = []
            for b in touched_blocks:
                le_vars = [
                    x[r_idx, b, t_idx]
                    for t_idx, rot in rot_list
                    if rot.leave_eligible and (r_idx, b, t_idx) in x
                ]
                if not le_vars:
                    # No leave-eligible rotations possible — whole request unsatisfiable
                    block_sats = []
                    break

                b_sat = model.NewBoolVar(f"bsat_{r_idx}_{b}_{i}")
                model.Add(sum(le_vars) >= 1).OnlyEnforceIf(b_sat)
                model.Add(sum(le_vars) == 0).OnlyEnforceIf(b_sat.Not())
                block_sats.append(b_sat)

            if not block_sats:
                continue

            sat = model.NewBoolVar(f"lsat_{r_idx}_multi_{i}")
            # Satisfied only if ALL touched blocks are leave-eligible
            model.AddMinEquality(sat, block_sats)
            sat_vars.append(sat)
            leave_detail.append((lr, sat))

    # ── S2: Rotation spread penalty (weight 10) ─────────────────────────────
    # Penalize same rotation in consecutive blocks (except FMC/electives)

    spread_penalties: list[cp_model.IntVar] = []
    no_spread_rotations = {"FMC", "ELE1", "ELE2", "Elective"}

    for r_idx, resident in enumerate(context.all_residents):
        pgy = resident.pgy
        rot_list = pgy_rot_indices.get(pgy, [])
        sorted_blocks = sorted(block_numbers)

        for t_idx, rot in rot_list:
            if rot.name in no_spread_rotations:
                continue
            for j in range(len(sorted_blocks) - 1):
                b1, b2 = sorted_blocks[j], sorted_blocks[j + 1]
                if (r_idx, b1, t_idx) in x and (r_idx, b2, t_idx) in x:
                    both = model.NewBoolVar(f"consec_{r_idx}_{b1}_{t_idx}")
                    model.AddBoolAnd(
                        [x[r_idx, b1, t_idx], x[r_idx, b2, t_idx]]
                    ).OnlyEnforceIf(both)
                    model.AddBoolOr(
                        [x[r_idx, b1, t_idx].Not(), x[r_idx, b2, t_idx].Not()]
                    ).OnlyEnforceIf(both.Not())
                    spread_penalties.append(both)

    # ── Objective ────────────────────────────────────────────────────────────

    objective_terms = []
    for sat in sat_vars:
        objective_terms.append(1000 * sat)
    for penalty in spread_penalties:
        objective_terms.append(-10 * penalty)

    if objective_terms:
        model.Maximize(sum(objective_terms))

    # ── Solve ────────────────────────────────────────────────────────────────

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = timeout_seconds
    solver.parameters.num_workers = 4
    solver.parameters.log_search_progress = False

    status_code = solver.Solve(model)
    elapsed = time.monotonic() - start_time

    status_names = {
        cp_model.OPTIMAL: "OPTIMAL",
        cp_model.FEASIBLE: "FEASIBLE",
        cp_model.INFEASIBLE: "INFEASIBLE",
        cp_model.MODEL_INVALID: "MODEL_INVALID",
        cp_model.UNKNOWN: "UNKNOWN",
    }
    status_str = status_names.get(status_code, f"UNKNOWN_{status_code}")

    logger.info("ARO: solver status=%s, time=%.2fs", status_str, elapsed)

    if status_code not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        return SolverResult(
            status=status_str,
            solver_runtime_seconds=elapsed,
            solver_wall_time_seconds=solver.WallTime(),
            leave_total_count=len(context.leave_requests),
        )

    # ── Extract solution ─────────────────────────────────────────────────────

    assignments: list[RotationAssignment] = []

    # Build set of satisfied leave requests
    satisfied_leaves: set[int] = set()
    for idx, (lr, sat) in enumerate(leave_detail):
        if solver.Value(sat) == 1:
            satisfied_leaves.add(idx)

    # Build leave lookup for annotation
    leave_satisfied_by_rb: dict[tuple[int, int], bool] = {}
    for idx, (lr, sat) in enumerate(leave_detail):
        r_idx = context.resident_idx[lr.person_id]
        is_sat = idx in satisfied_leaves
        for b in lr.blocks:
            key = (r_idx, b)
            # If any leave request for this (resident, block) is satisfied, mark it
            if is_sat:
                leave_satisfied_by_rb[key] = True
            elif key not in leave_satisfied_by_rb:
                leave_satisfied_by_rb[key] = False

    for r_idx, resident in enumerate(context.all_residents):
        pgy = resident.pgy
        rot_list = pgy_rot_indices.get(pgy, [])

        for block in block_numbers:
            for t_idx, rot in rot_list:
                if (r_idx, block, t_idx) in x and solver.Value(
                    x[r_idx, block, t_idx]
                ) == 1:
                    fixed = FIXED_ASSIGNMENTS.get(pgy, {})
                    has_leave = (r_idx, block) in leave_satisfied_by_rb
                    is_leave_sat = leave_satisfied_by_rb.get((r_idx, block), False)

                    assignments.append(
                        RotationAssignment(
                            resident_idx=r_idx,
                            resident_name=resident.name,
                            person_id=resident.person_id,
                            pgy=pgy,
                            block_number=block,
                            rotation_name=rot.name,
                            rotation_idx=t_idx,
                            is_fixed=block in fixed,
                            leave_eligible=rot.leave_eligible,
                            leave_satisfied=is_leave_sat,
                        )
                    )
                    break  # One rotation per block

    leave_sat_count = len(satisfied_leaves)
    # Count all leave requests with matched residents, not just those modeled
    leave_total = sum(
        1 for lr in context.leave_requests if lr.person_id in context.resident_idx
    )

    logger.info(
        "ARO: leave satisfaction %d/%d (%.1f%%)",
        leave_sat_count,
        leave_total,
        (leave_sat_count / leave_total * 100) if leave_total else 0,
    )

    return SolverResult(
        status=status_str,
        assignments=assignments,
        leave_satisfied_count=leave_sat_count,
        leave_total_count=leave_total,
        objective_value=solver.ObjectiveValue(),
        solver_runtime_seconds=elapsed,
        solver_wall_time_seconds=solver.WallTime(),
    )


def print_solution_grid(result: SolverResult, context: AnnualContext) -> str:
    """Format the solver result as a text grid for console output."""
    if not result.assignments:
        return f"No solution found (status: {result.status})"

    lines: list[str] = []
    header = f"{'':>16}" + "".join(
        f"{'Blk' + str(b):>8}" for b in context.block_numbers
    )
    lines.append(header)
    lines.append("-" * len(header))

    # Group assignments by resident
    by_resident: dict[int, dict[int, RotationAssignment]] = {}
    for a in result.assignments:
        by_resident.setdefault(a.resident_idx, {})[a.block_number] = a

    current_pgy = None
    for r_idx, resident in enumerate(context.all_residents):
        if resident.pgy != current_pgy:
            current_pgy = resident.pgy
            lines.append(f"PGY-{current_pgy}:")

        row = f"{resident.name:>14}  "
        for block in context.block_numbers:
            a = by_resident.get(r_idx, {}).get(block)  # type: ignore[assignment]
            if a:
                # Abbreviate rotation names
                abbr = a.rotation_name[:6]
                if a.leave_satisfied:
                    abbr += "*"
                row += f"{abbr:>8}"
            else:
                row += f"{'???':>8}"
        lines.append(row)

    lines.append("")
    lines.append(
        f"Leave satisfied: {result.leave_satisfied_count}/{result.leave_total_count} "
        f"({result.leave_satisfied_count / result.leave_total_count * 100:.1f}%)"
        if result.leave_total_count
        else "No leave requests"
    )
    lines.append(f"Solver: {result.status}, {result.solver_runtime_seconds:.2f}s")

    return "\n".join(lines)
