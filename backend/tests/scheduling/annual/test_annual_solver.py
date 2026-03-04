"""Tests for the Annual Rotation Optimizer CP-SAT solver.

Pure logic tests — no database required. Uses synthetic residents
with the actual PGY rotation config from pgy_config.py.
"""

from __future__ import annotations

from collections import Counter
from uuid import uuid4

import pytest

from app.scheduling.annual.context import (
    AnnualContext,
    LeaveRequest,
    ResidentInfo,
)
from app.scheduling.annual.pgy_config import (
    FIXED_ASSIGNMENTS,
    PGY_ROTATIONS,
    get_capacity,
    get_eligible_blocks,
)
from app.scheduling.annual.solver import (
    SolverResult,
    print_solution_grid,
    solve,
)


# ── Helpers ───────────────────────────────────────────────────────────────────


def _make_context(
    n_per_pgy: int = 2,
    leave_requests: list[LeaveRequest] | None = None,
    academic_year: int = 2026,
) -> AnnualContext:
    """Build a fully populated AnnualContext with synthetic residents."""
    ctx = AnnualContext(academic_year=academic_year)

    for pgy in (1, 2, 3):
        ctx.residents_by_pgy[pgy] = [
            ResidentInfo(person_id=uuid4(), name=f"PGY{pgy}_{i}", pgy=pgy)
            for i in range(n_per_pgy)
        ]

    if leave_requests:
        ctx.leave_requests = leave_requests
    ctx.build_indices()
    return ctx


def _get_pgy_solver_blocks(pgy: int) -> set[int]:
    """Return the set of blocks a PGY level is optimized over (excluding fixed)."""
    if pgy == 1:
        return set(range(2, 14))  # Block 1 = FMO (not in solver)
    elif pgy == 2:
        return set(range(1, 14))
    elif pgy == 3:
        return set(range(1, 13))  # Block 13 = Military (not in solver)
    return set()


# ── Feasibility ───────────────────────────────────────────────────────────────


class TestSolverFeasibility:
    def test_full_roster_no_leave(self):
        """18 residents (6 per PGY), no leave requests → OPTIMAL."""
        ctx = _make_context(n_per_pgy=6)
        result = solve(ctx, timeout_seconds=30.0)
        assert result.status in ("OPTIMAL", "FEASIBLE")

    def test_small_roster_feasible(self):
        """1 resident per PGY → feasible."""
        ctx = _make_context(n_per_pgy=1)
        result = solve(ctx, timeout_seconds=30.0)
        assert result.status in ("OPTIMAL", "FEASIBLE")

    def test_solver_runtime_under_10s(self):
        """Full 18-resident model should solve quickly."""
        ctx = _make_context(n_per_pgy=6)
        result = solve(ctx, timeout_seconds=30.0)
        assert result.solver_runtime_seconds < 10.0
        assert result.status in ("OPTIMAL", "FEASIBLE")


# ── Fixed Assignments ─────────────────────────────────────────────────────────


class TestFixedAssignments:
    """FMO (PGY-1 Block 1) and Military (PGY-3 Block 13) are not in
    the PGY rotation lists, so the solver produces no assignment for them.
    The caller fills them in post-solve."""

    def test_pgy1_block1_not_in_assignments(self):
        ctx = _make_context(n_per_pgy=2)
        result = solve(ctx)
        pgy1_b1 = [a for a in result.assignments if a.pgy == 1 and a.block_number == 1]
        assert len(pgy1_b1) == 0

    def test_pgy3_block13_not_in_assignments(self):
        ctx = _make_context(n_per_pgy=2)
        result = solve(ctx)
        pgy3_b13 = [
            a for a in result.assignments if a.pgy == 3 and a.block_number == 13
        ]
        assert len(pgy3_b13) == 0

    @pytest.mark.parametrize("pgy", [1, 2, 3])
    def test_solver_blocks_per_pgy(self, pgy: int):
        """Each PGY level has the expected number of solver-assigned blocks."""
        ctx = _make_context(n_per_pgy=2)
        result = solve(ctx)
        expected_blocks = _get_pgy_solver_blocks(pgy)

        for r_idx, resident in enumerate(ctx.all_residents):
            if resident.pgy != pgy:
                continue
            assigned = {
                a.block_number for a in result.assignments if a.resident_idx == r_idx
            }
            assert assigned == expected_blocks, (
                f"{resident.name}: expected blocks {sorted(expected_blocks)}, "
                f"got {sorted(assigned)}"
            )


# ── H1: Exactly one rotation per block ───────────────────────────────────────


class TestExactlyOnePerBlock:
    def test_no_duplicate_block_assignments(self):
        ctx = _make_context(n_per_pgy=6)
        result = solve(ctx)
        assert result.status in ("OPTIMAL", "FEASIBLE")

        counts = Counter((a.resident_idx, a.block_number) for a in result.assignments)
        for (r, b), count in counts.items():
            assert count == 1, f"Resident {r} has {count} assignments in block {b}"


# ── H3: Each rotation exactly once ───────────────────────────────────────────


class TestEachRotationOnce:
    def test_all_rotations_assigned_once(self):
        ctx = _make_context(n_per_pgy=6)
        result = solve(ctx)
        assert result.status in ("OPTIMAL", "FEASIBLE")

        for r_idx, resident in enumerate(ctx.all_residents):
            rot_counts = Counter(
                a.rotation_name for a in result.assignments if a.resident_idx == r_idx
            )
            for name, count in rot_counts.items():
                assert count == 1, f"{resident.name}: '{name}' assigned {count}x"

    def test_rotation_count_matches_pgy(self):
        """Number of assigned rotations = number of solver blocks for PGY."""
        ctx = _make_context(n_per_pgy=2)
        result = solve(ctx)

        for r_idx, resident in enumerate(ctx.all_residents):
            n_assigned = sum(1 for a in result.assignments if a.resident_idx == r_idx)
            expected = len(_get_pgy_solver_blocks(resident.pgy))
            assert n_assigned == expected, (
                f"{resident.name}: {n_assigned} assignments, expected {expected}"
            )


# ── H4: Capacity ─────────────────────────────────────────────────────────────


class TestCapacity:
    def test_capacity_not_exceeded(self):
        ctx = _make_context(n_per_pgy=6)
        result = solve(ctx)
        assert result.status in ("OPTIMAL", "FEASIBLE")

        counts: Counter[tuple[str, int]] = Counter(
            (a.rotation_name, a.block_number) for a in result.assignments
        )
        for (rot_name, block), count in counts.items():
            cap = get_capacity(rot_name)
            assert count <= cap, (
                f"'{rot_name}' block {block}: {count} residents > cap {cap}"
            )


# ── H6: Sequencing ───────────────────────────────────────────────────────────


class TestSequencing:
    def test_kap_after_tamc_for_pgy1(self):
        ctx = _make_context(n_per_pgy=6)
        result = solve(ctx)
        assert result.status in ("OPTIMAL", "FEASIBLE")

        for r_idx, resident in enumerate(ctx.all_residents):
            if resident.pgy != 1:
                continue
            by_rot = {
                a.rotation_name: a.block_number
                for a in result.assignments
                if a.resident_idx == r_idx
            }
            tamc = by_rot.get("TAMC L+D")
            kap = by_rot.get("Kap L+D")
            if tamc is not None and kap is not None:
                assert kap > tamc, (
                    f"{resident.name}: Kap L+D block {kap} <= TAMC L+D block {tamc}"
                )


# ── Block Eligibility ────────────────────────────────────────────────────────


class TestBlockEligibility:
    def test_tamc_ld_not_in_blocked_blocks(self):
        ctx = _make_context(n_per_pgy=6)
        result = solve(ctx)
        for a in result.assignments:
            if a.rotation_name == "TAMC L+D":
                assert a.block_number not in {1, 2}, (
                    f"TAMC L+D in blocked block {a.block_number}"
                )

    def test_peds_nf_ward_only_in_allowed_blocks(self):
        ctx = _make_context(n_per_pgy=6)
        result = solve(ctx)
        allowed = {7, 9, 10, 11, 12, 13}
        for a in result.assignments:
            if a.rotation_name == "[Peds NF + Peds Ward]":
                assert a.block_number in allowed, (
                    f"[Peds NF + Peds Ward] in block {a.block_number}"
                )

    def test_gyn_clinic_not_in_blocks_1_2(self):
        ctx = _make_context(n_per_pgy=6)
        result = solve(ctx)
        for a in result.assignments:
            if a.rotation_name == "Gyn Clinic":
                assert a.block_number not in {1, 2}

    def test_psych_nf_only_in_blocks_4_through_12(self):
        ctx = _make_context(n_per_pgy=6)
        result = solve(ctx)
        allowed = set(range(4, 13))
        for a in result.assignments:
            if a.rotation_name == "[PSYCH + NF]":
                assert a.block_number in allowed

    def test_ld_nf_not_in_blocks_1_2(self):
        ctx = _make_context(n_per_pgy=6)
        result = solve(ctx)
        for a in result.assignments:
            if a.rotation_name == "L+D NF":
                assert a.block_number not in {1, 2}


# ── S1: Leave Satisfaction ────────────────────────────────────────────────────


class TestLeaveSatisfaction:
    def test_single_block_leave_satisfied(self):
        ctx = _make_context(n_per_pgy=2)
        resident = ctx.residents_by_pgy[2][0]
        block5 = next(b for b in ctx.blocks if b.block_number == 5)

        ctx.leave_requests = [
            LeaveRequest(
                person_id=resident.person_id,
                resident_name=resident.name,
                pgy=2,
                start_date=block5.start_date,
                end_date=block5.start_date,
                blocks=[5],
                raw_text="vacation",
            )
        ]
        ctx.build_indices()

        result = solve(ctx)
        assert result.status in ("OPTIMAL", "FEASIBLE")
        assert result.leave_satisfied_count >= 1
        assert result.leave_total_count == 1

        # Verify the assigned rotation is leave-eligible
        a = next(
            (
                a
                for a in result.assignments
                if a.person_id == resident.person_id and a.block_number == 5
            ),
            None,
        )
        assert a is not None
        assert a.leave_eligible is True

    def test_cross_block_leave_both_blocks_eligible(self):
        """Leave spanning blocks 4-5 → both must have leave-eligible rotations."""
        ctx = _make_context(n_per_pgy=2)
        resident = ctx.residents_by_pgy[2][0]
        block4 = next(b for b in ctx.blocks if b.block_number == 4)
        block5 = next(b for b in ctx.blocks if b.block_number == 5)

        ctx.leave_requests = [
            LeaveRequest(
                person_id=resident.person_id,
                resident_name=resident.name,
                pgy=2,
                start_date=block4.end_date,
                end_date=block5.start_date,
                blocks=[4, 5],
                raw_text="spanning leave",
            )
        ]
        ctx.build_indices()

        result = solve(ctx)
        assert result.status in ("OPTIMAL", "FEASIBLE")

        if result.leave_satisfied_count > 0:
            for b in [4, 5]:
                a = next(
                    (
                        a
                        for a in result.assignments
                        if a.person_id == resident.person_id and a.block_number == b
                    ),
                    None,
                )
                assert a is not None
                assert a.leave_eligible is True, (
                    f"Block {b} should be leave-eligible for cross-block leave"
                )

    def test_multiple_residents_leave_maximized(self):
        """Each of 2 residents requesting leave in different blocks → both satisfied."""
        ctx = _make_context(n_per_pgy=2)
        residents = ctx.residents_by_pgy[2]

        ctx.leave_requests = [
            LeaveRequest(
                person_id=residents[0].person_id,
                resident_name=residents[0].name,
                pgy=2,
                start_date=next(
                    b for b in ctx.blocks if b.block_number == 4
                ).start_date,
                end_date=next(b for b in ctx.blocks if b.block_number == 4).start_date,
                blocks=[4],
                raw_text="leave 1",
            ),
            LeaveRequest(
                person_id=residents[1].person_id,
                resident_name=residents[1].name,
                pgy=2,
                start_date=next(
                    b for b in ctx.blocks if b.block_number == 6
                ).start_date,
                end_date=next(b for b in ctx.blocks if b.block_number == 6).start_date,
                blocks=[6],
                raw_text="leave 2",
            ),
        ]
        ctx.build_indices()

        result = solve(ctx)
        assert result.status in ("OPTIMAL", "FEASIBLE")
        assert result.leave_satisfied_count == 2
        assert result.leave_total_count == 2

    def test_no_leave_yields_zero_counts(self):
        ctx = _make_context(n_per_pgy=2)
        result = solve(ctx)
        assert result.leave_satisfied_count == 0
        assert result.leave_total_count == 0


# ── SolverResult ──────────────────────────────────────────────────────────────


class TestSolverResult:
    def test_result_fields(self):
        ctx = _make_context(n_per_pgy=1)
        result = solve(ctx)
        assert isinstance(result.status, str)
        assert isinstance(result.assignments, list)
        assert isinstance(result.objective_value, float)
        assert result.solver_runtime_seconds > 0

    def test_assignment_fields(self):
        ctx = _make_context(n_per_pgy=1)
        result = solve(ctx)
        assert len(result.assignments) > 0
        a = result.assignments[0]
        assert isinstance(a.resident_idx, int)
        assert isinstance(a.resident_name, str)
        assert isinstance(a.pgy, int)
        assert isinstance(a.block_number, int)
        assert isinstance(a.rotation_name, str)
        assert isinstance(a.leave_eligible, bool)
        assert isinstance(a.leave_satisfied, bool)


# ── print_solution_grid ───────────────────────────────────────────────────────


class TestPrintSolutionGrid:
    def test_contains_pgy_headers(self):
        ctx = _make_context(n_per_pgy=1)
        result = solve(ctx)
        grid = print_solution_grid(result, ctx)
        assert "PGY-1:" in grid
        assert "PGY-2:" in grid
        assert "PGY-3:" in grid

    def test_contains_solver_status(self):
        ctx = _make_context(n_per_pgy=1)
        result = solve(ctx)
        grid = print_solution_grid(result, ctx)
        assert "Solver:" in grid

    def test_no_solution_message(self):
        result = SolverResult(status="INFEASIBLE")
        ctx = _make_context(n_per_pgy=1)
        grid = print_solution_grid(result, ctx)
        assert "No solution found" in grid
