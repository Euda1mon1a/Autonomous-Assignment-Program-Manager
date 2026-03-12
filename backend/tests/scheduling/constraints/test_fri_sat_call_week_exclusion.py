"""Tests for FMITCallProximityConstraint (and FriSatCallWeekExclusionConstraint alias)."""

import math
import pytest
from datetime import date, timedelta
from uuid import uuid4

from app.scheduling.constraints.base import ConstraintPriority, ConstraintType
from app.scheduling.constraints.overnight_call import (
    FMITCallProximityConstraint,
    FriSatCallWeekExclusionConstraint,
    is_overnight_call_night,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


class MockBlock:
    def __init__(self, block_id, block_date):
        self.id = block_id
        self.date = block_date


class MockTemplate:
    def __init__(
        self,
        template_id,
        name="FMIT",
        rotation_type="inpatient",
        abbreviation="FMIT",
        display_abbreviation="FMIT",
    ):
        self.id = template_id
        self.name = name
        self.rotation_type = rotation_type
        self.abbreviation = abbreviation
        self.display_abbreviation = display_abbreviation


class MockAssignment:
    def __init__(self, person_id, block_id, template_id, block=None):
        self.person_id = person_id
        self.block_id = block_id
        self.rotation_template_id = template_id
        self.rotation_template = None
        self.block = block  # For cross-block fallback


class MockFaculty:
    def __init__(self, faculty_id):
        self.id = faculty_id


class MockCallAssignment:
    """Mock finalized call assignment for validate()."""

    def __init__(self, person_id, call_date, call_type="overnight"):
        self.person_id = person_id
        self.date = call_date
        self.call_type = call_type


def _build_context(
    faculty_ids: list,
    fmit_template_id,
    fmit_assignments: list[tuple],  # (person_id, block_date)
    block_start: date,
    block_end: date,
    *,
    cross_block_fmit: list[tuple]
    | None = None,  # (person_id, block_date) outside range
):
    """Build a MockContext with blocks spanning block_start..block_end.

    cross_block_fmit: FMIT assignments from adjacent blocks (not in blocks list).
    These have an eagerly loaded .block attribute but their block_id won't be
    in blocks_by_id.
    """
    blocks = []
    block_idx = {}
    b_i = 0
    current = block_start
    while current <= block_end:
        bid = uuid4()
        blocks.append(MockBlock(bid, current))
        block_idx[bid] = b_i
        b_i += 1
        current += timedelta(days=1)

    template = MockTemplate(fmit_template_id)
    faculty = [MockFaculty(fid) for fid in faculty_ids]
    call_idx = {f.id: i for i, f in enumerate(faculty)}

    # Build FMIT assignments — find the block matching each date
    blocks_by_date = {b.date: b for b in blocks}
    existing = []
    for pid, adate in fmit_assignments:
        block = blocks_by_date.get(adate)
        if block:
            existing.append(MockAssignment(pid, block.id, fmit_template_id))

    # Cross-block assignments: block is NOT in context.blocks
    if cross_block_fmit:
        for pid, adate in cross_block_fmit:
            fake_block_id = uuid4()
            fake_block = MockBlock(fake_block_id, adate)
            existing.append(
                MockAssignment(pid, fake_block_id, fmit_template_id, block=fake_block)
            )

    class MockContext:
        pass

    ctx = MockContext()
    ctx.blocks = blocks
    ctx.block_idx = block_idx
    ctx.templates = [template]
    ctx.faculty = faculty
    ctx.faculty_idx = call_idx
    ctx.call_eligible_faculty = faculty
    ctx.call_eligible_faculty_idx = call_idx
    ctx.existing_assignments = existing
    ctx.availability = {}
    return ctx


# ---------------------------------------------------------------------------
# Tests — Initialization
# ---------------------------------------------------------------------------


class TestFMITCallProximityInit:
    """Test constraint initialization."""

    def test_defaults(self):
        c = FMITCallProximityConstraint()
        assert c.name == "FMITCallProximity"
        assert c.base_weight == 10_000.0
        assert c.radius_days == 7
        assert c.half_life_days == 1.0
        assert c.weight == 10_000.0  # SoftConstraint.weight = base_weight
        assert c.constraint_type == ConstraintType.CALL
        assert c.priority == ConstraintPriority.HIGH
        assert c.enabled is True

    def test_custom_params(self):
        c = FMITCallProximityConstraint(
            base_weight=5000.0, radius_days=5, half_life_days=2.0
        )
        assert c.base_weight == 5000.0
        assert c.radius_days == 5
        assert c.half_life_days == 2.0

    def test_alias_is_same_class(self):
        """FriSatCallWeekExclusionConstraint is an alias for FMITCallProximityConstraint."""
        assert FriSatCallWeekExclusionConstraint is FMITCallProximityConstraint


# ---------------------------------------------------------------------------
# Tests — Penalty Computation
# ---------------------------------------------------------------------------


class TestPenaltyComputation:
    """Test the exponential decay formula."""

    def test_gap_1(self):
        c = FMITCallProximityConstraint()
        assert c._compute_penalty(1) == 10_000.0

    def test_gap_2(self):
        c = FMITCallProximityConstraint()
        assert c._compute_penalty(2) == 5_000.0

    def test_gap_3(self):
        c = FMITCallProximityConstraint()
        assert c._compute_penalty(3) == 2_500.0

    def test_gap_4(self):
        c = FMITCallProximityConstraint()
        assert c._compute_penalty(4) == 1_250.0

    def test_gap_5(self):
        c = FMITCallProximityConstraint()
        assert c._compute_penalty(5) == 625.0

    def test_gap_6(self):
        c = FMITCallProximityConstraint()
        assert c._compute_penalty(6) == pytest.approx(312.5)

    def test_gap_7(self):
        c = FMITCallProximityConstraint()
        assert c._compute_penalty(7) == pytest.approx(156.25)

    def test_gap_0_returns_zero(self):
        c = FMITCallProximityConstraint()
        assert c._compute_penalty(0) == 0.0

    def test_custom_half_life(self):
        """With half_life=2.0, penalty halves every 2 days."""
        c = FMITCallProximityConstraint(base_weight=10_000.0, half_life_days=2.0)
        assert c._compute_penalty(1) == 10_000.0
        assert c._compute_penalty(3) == 5_000.0  # 2 days after gap=1
        assert c._compute_penalty(5) == 2_500.0


# ---------------------------------------------------------------------------
# Tests — CP-SAT Penalty Terms
# ---------------------------------------------------------------------------


class TestFMITCallProximityCPSAT:
    """Test add_to_cpsat penalty term generation."""

    def test_no_call_vars_returns_early(self):
        """No call_assignments → no penalty terms."""
        c = FMITCallProximityConstraint()
        variables: dict = {}

        class EmptyCtx:
            blocks = []
            block_idx = {}
            templates = []
            faculty = []
            call_eligible_faculty = []
            call_eligible_faculty_idx = {}
            existing_assignments = []
            availability = {}

        c.add_to_cpsat(None, variables, EmptyCtx())
        assert "objective_terms" not in variables

    def test_no_fmit_weeks_returns_early(self):
        """No FMIT assignments → no penalty terms."""
        c = FMITCallProximityConstraint()
        variables = {"call_assignments": {(0, 0, "overnight"): "var"}}

        class NoFmitCtx:
            blocks = []
            block_idx = {}
            templates = []
            faculty = []
            call_eligible_faculty = []
            call_eligible_faculty_idx = {}
            existing_assignments = []
            availability = {}

        c.add_to_cpsat(None, variables, NoFmitCtx())
        assert variables.get("objective_terms", []) == []

    def test_penalty_before_fmit(self):
        """Call nights before FMIT Friday get distance-based penalties."""
        c = FMITCallProximityConstraint()
        fac_id = uuid4()
        tmpl_id = uuid4()

        # FMIT week: Friday Jun 12 - Thursday Jun 18, 2026
        friday = date(2026, 6, 12)
        assert friday.weekday() == 4

        # Build context: Mon Jun 1 - Thu Jun 18 (includes days before FMIT)
        ctx = _build_context(
            faculty_ids=[fac_id],
            fmit_template_id=tmpl_id,
            fmit_assignments=[(fac_id, friday)],
            block_start=date(2026, 6, 1),
            block_end=date(2026, 6, 18),
        )

        # Build call_assignments for all Sun-Thu blocks
        call_vars = {}
        for b in ctx.blocks:
            if is_overnight_call_night(b.date):
                b_i = ctx.block_idx[b.id]
                call_vars[(0, b_i, "overnight")] = f"var_{b.date}"

        variables: dict = {"call_assignments": call_vars, "objective_terms": []}
        c.add_to_cpsat(None, variables, ctx)

        terms = variables["objective_terms"]
        terms_by_date = {var: weight for var, weight in terms}

        # Jun 11 (Thu) = 1 day before Friday → penalty = 10000
        assert terms_by_date.get(f"var_{date(2026, 6, 11)}") == 10000
        # Jun 10 (Wed) = 2 days before → penalty = 5000
        assert terms_by_date.get(f"var_{date(2026, 6, 10)}") == 5000
        # Jun 9 (Tue) = 3 days before → penalty = 2500
        assert terms_by_date.get(f"var_{date(2026, 6, 9)}") == 2500
        # Jun 8 (Mon) = 4 days before → penalty = 1250
        assert terms_by_date.get(f"var_{date(2026, 6, 8)}") == 1250
        # Jun 7 (Sun) = 5 days before → penalty = 625
        assert terms_by_date.get(f"var_{date(2026, 6, 7)}") == 625

    def test_penalty_after_fmit(self):
        """Call nights after FMIT Thursday get distance-based penalties."""
        c = FMITCallProximityConstraint()
        fac_id = uuid4()
        tmpl_id = uuid4()

        # FMIT week: Friday Jun 12 - Thursday Jun 18, 2026
        friday = date(2026, 6, 12)
        thursday_end = date(2026, 6, 18)

        ctx = _build_context(
            faculty_ids=[fac_id],
            fmit_template_id=tmpl_id,
            fmit_assignments=[(fac_id, friday)],
            block_start=friday,
            block_end=date(2026, 6, 28),
        )

        call_vars = {}
        for b in ctx.blocks:
            if is_overnight_call_night(b.date):
                b_i = ctx.block_idx[b.id]
                call_vars[(0, b_i, "overnight")] = f"var_{b.date}"

        variables: dict = {"call_assignments": call_vars, "objective_terms": []}
        c.add_to_cpsat(None, variables, ctx)

        terms = variables["objective_terms"]
        terms_by_date = {var: weight for var, weight in terms}

        # Jun 21 (Sun) = 3 days after Thursday → penalty = 2500
        assert terms_by_date.get(f"var_{date(2026, 6, 21)}") == 2500
        # Jun 22 (Mon) = 4 days after → penalty = 1250
        assert terms_by_date.get(f"var_{date(2026, 6, 22)}") == 1250

    def test_no_penalty_inside_fmit_week(self):
        """Dates inside the FMIT week should NOT be penalized."""
        c = FMITCallProximityConstraint()
        fac_id = uuid4()
        tmpl_id = uuid4()

        friday = date(2026, 6, 12)
        # Only blocks within the FMIT week
        ctx = _build_context(
            faculty_ids=[fac_id],
            fmit_template_id=tmpl_id,
            fmit_assignments=[(fac_id, friday)],
            block_start=friday,
            block_end=date(2026, 6, 18),
        )

        call_vars = {}
        for b in ctx.blocks:
            if is_overnight_call_night(b.date):
                b_i = ctx.block_idx[b.id]
                call_vars[(0, b_i, "overnight")] = f"var_{b.date}"

        variables: dict = {"call_assignments": call_vars, "objective_terms": []}
        c.add_to_cpsat(None, variables, ctx)

        # No terms — all dates are inside the FMIT week (no proximity zone)
        assert len(variables["objective_terms"]) == 0

    def test_multiple_fmit_weeks_stack(self):
        """Faculty with 2 FMIT weeks gets penalties for both proximity zones."""
        c = FMITCallProximityConstraint()
        fac_id = uuid4()
        tmpl_id = uuid4()

        fri1 = date(2026, 6, 12)  # FMIT 1: Jun 12-18
        fri2 = date(2026, 6, 26)  # FMIT 2: Jun 26-Jul 2

        ctx = _build_context(
            faculty_ids=[fac_id],
            fmit_template_id=tmpl_id,
            fmit_assignments=[(fac_id, fri1), (fac_id, fri2)],
            block_start=date(2026, 6, 1),
            block_end=date(2026, 7, 9),
        )

        call_vars = {}
        for b in ctx.blocks:
            if is_overnight_call_night(b.date):
                b_i = ctx.block_idx[b.id]
                call_vars[(0, b_i, "overnight")] = f"var_{b.date}"

        variables: dict = {"call_assignments": call_vars, "objective_terms": []}
        c.add_to_cpsat(None, variables, ctx)

        terms = variables["objective_terms"]
        # Should have penalties from both proximity zones
        assert len(terms) > 0

        # Date between the two FMIT weeks (e.g. Jun 22 = 4 days after first,
        # 4 days before second) should get the max of the two penalties
        dates_with_penalties = [var for var, _ in terms]
        # Jun 22 (Mon) should appear — it's in range of both FMIT weeks
        assert f"var_{date(2026, 6, 22)}" in dates_with_penalties


# ---------------------------------------------------------------------------
# Tests — Cross-Block FMIT Visibility
# ---------------------------------------------------------------------------


class TestCrossBlockFMIT:
    """Test that FMIT from adjacent blocks is visible."""

    def test_cross_block_fmit_via_assignment_block(self):
        """FMIT assignment from adjacent block uses eagerly loaded .block."""
        c = FMITCallProximityConstraint()
        fac_id = uuid4()
        tmpl_id = uuid4()

        # FMIT is on Friday Jun 12, but context blocks only start Jun 8
        # and the FMIT assignment comes from an adjacent block (not in blocks)
        friday = date(2026, 6, 12)

        ctx = _build_context(
            faculty_ids=[fac_id],
            fmit_template_id=tmpl_id,
            fmit_assignments=[],  # No in-range FMIT
            block_start=date(2026, 6, 1),
            block_end=date(2026, 6, 11),  # Ends before FMIT Friday
            cross_block_fmit=[(fac_id, friday)],  # Adjacent block FMIT
        )

        call_vars = {}
        for b in ctx.blocks:
            if is_overnight_call_night(b.date):
                b_i = ctx.block_idx[b.id]
                call_vars[(0, b_i, "overnight")] = f"var_{b.date}"

        variables: dict = {"call_assignments": call_vars, "objective_terms": []}
        c.add_to_cpsat(None, variables, ctx)

        terms = variables["objective_terms"]
        terms_by_date = {var: weight for var, weight in terms}

        # Jun 11 (Thu) = 1 day before FMIT Friday → penalty = 10000
        assert terms_by_date.get(f"var_{date(2026, 6, 11)}") == 10000
        # Jun 10 (Wed) = 2 days before → penalty = 5000
        assert terms_by_date.get(f"var_{date(2026, 6, 10)}") == 5000


# ---------------------------------------------------------------------------
# Tests — Validate
# ---------------------------------------------------------------------------


class TestFMITCallProximityValidate:
    """Test validate() on finalized schedules."""

    def test_no_violations_when_no_fmit(self):
        """No violations when no FMIT weeks exist."""
        c = FMITCallProximityConstraint()

        class MinCtx:
            blocks = []
            block_idx = {}
            templates = []
            faculty = []
            existing_assignments = []

        fac_id = uuid4()
        assignments = [MockCallAssignment(fac_id, date(2026, 6, 9))]
        result = c.validate(assignments, MinCtx())
        assert result.satisfied is True
        assert len(result.violations) == 0

    def test_violation_with_severity_levels(self):
        """Validate reports correct severity based on gap distance."""
        c = FMITCallProximityConstraint()
        fac_id = uuid4()
        tmpl_id = uuid4()

        # FMIT week: Fri Jun 12 - Thu Jun 18
        friday = date(2026, 6, 12)

        ctx = _build_context(
            faculty_ids=[fac_id],
            fmit_template_id=tmpl_id,
            fmit_assignments=[(fac_id, friday)],
            block_start=date(2026, 6, 1),
            block_end=date(2026, 6, 25),
        )

        assignments = [
            MockCallAssignment(fac_id, date(2026, 6, 11)),  # 1 day before → HIGH
            MockCallAssignment(fac_id, date(2026, 6, 9)),  # 3 days before → MEDIUM
            MockCallAssignment(fac_id, date(2026, 6, 24)),  # 6 days after → LOW
        ]

        result = c.validate(assignments, ctx)
        assert result.satisfied is True  # Soft constraint
        assert len(result.violations) == 3

        severities = {v.details["gap_days"]: v.severity for v in result.violations}
        assert severities[1] == "HIGH"
        assert severities[3] == "MEDIUM"
        assert severities[6] == "LOW"

        # Penalty should be sum of all computed penalties
        expected = c._compute_penalty(1) + c._compute_penalty(3) + c._compute_penalty(6)
        assert result.penalty == pytest.approx(expected)

    def test_no_violation_outside_radius(self):
        """Call outside radius_days should not generate violations."""
        c = FMITCallProximityConstraint()
        fac_id = uuid4()
        tmpl_id = uuid4()

        friday = date(2026, 6, 12)
        ctx = _build_context(
            faculty_ids=[fac_id],
            fmit_template_id=tmpl_id,
            fmit_assignments=[(fac_id, friday)],
            block_start=date(2026, 6, 1),
            block_end=date(2026, 6, 30),
        )

        # 10 days before FMIT Friday = outside 7-day radius
        assignments = [MockCallAssignment(fac_id, date(2026, 6, 2))]
        result = c.validate(assignments, ctx)
        assert len(result.violations) == 0

    def test_no_violation_for_other_faculty(self):
        """Faculty without FMIT should not get proximity violations."""
        c = FMITCallProximityConstraint()
        fac_a = uuid4()
        fac_b = uuid4()
        tmpl_id = uuid4()

        friday = date(2026, 6, 12)
        ctx = _build_context(
            faculty_ids=[fac_a, fac_b],
            fmit_template_id=tmpl_id,
            fmit_assignments=[(fac_a, friday)],  # Only fac_a has FMIT
            block_start=date(2026, 6, 1),
            block_end=date(2026, 6, 18),
        )

        # fac_b has call near FMIT but shouldn't be penalized
        assignments = [MockCallAssignment(fac_b, date(2026, 6, 11))]
        result = c.validate(assignments, ctx)
        assert len(result.violations) == 0


# ---------------------------------------------------------------------------
# Tests — Manager Registration
# ---------------------------------------------------------------------------


class TestManagerRegistration:
    """Test constraint is properly registered in ConstraintManager."""

    def test_disabled_in_default_profile(self):
        from app.scheduling.constraints.manager import ConstraintManager

        mgr = ConstraintManager.create_default(profile="resident")
        names = [c.name for c in mgr.get_enabled()]
        assert "FMITCallProximity" not in names

    def test_enabled_in_faculty_profile(self):
        from app.scheduling.constraints.manager import ConstraintManager

        mgr = ConstraintManager.create_default(profile="faculty")
        names = [c.name for c in mgr.get_enabled()]
        assert "FMITCallProximity" in names

    def test_base_weight_is_10000(self):
        from app.scheduling.constraints.manager import ConstraintManager

        mgr = ConstraintManager.create_default(profile="faculty")
        constraint = next(c for c in mgr.constraints if c.name == "FMITCallProximity")
        assert constraint.weight == 10_000.0
