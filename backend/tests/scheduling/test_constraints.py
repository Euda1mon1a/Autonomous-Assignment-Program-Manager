"""Tests for modular constraint system pure logic (no DB, no Redis).

Covers: ConstraintPriority, ConstraintType, ConstraintViolation,
ConstraintResult, HardConstraint, SoftConstraint, SchedulingContext,
validate() methods for all concrete constraints, and ConstraintManager.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date, timedelta
from types import SimpleNamespace
from uuid import UUID, uuid4

import pytest

from app.scheduling.constraints import (
    AvailabilityConstraint,
    ClinicCapacityConstraint,
    ConstraintManager,
    ConstraintPriority,
    ConstraintResult,
    ConstraintType,
    ConstraintViolation,
    ContinuityConstraint,
    CoverageConstraint,
    EightyHourRuleConstraint,
    EquityConstraint,
    HardConstraint,
    HubProtectionConstraint,
    MaxPhysiciansInClinicConstraint,
    N1VulnerabilityConstraint,
    OneInSevenRuleConstraint,
    OnePersonPerBlockConstraint,
    PreferenceConstraint,
    PreferenceTrailConstraint,
    SchedulingContext,
    SoftConstraint,
    SupervisionRatioConstraint,
    UtilizationBufferConstraint,
    WednesdayAMInternOnlyConstraint,
    ZoneBoundaryConstraint,
)


# ---------------------------------------------------------------------------
# Mock helpers — lightweight objects that constraints access via attributes
# ---------------------------------------------------------------------------


def _person(pid=None, name="Resident", pgy_level=1, target_clinical_blocks=None):
    ns = SimpleNamespace(id=pid or uuid4(), name=name, pgy_level=pgy_level)
    if target_clinical_blocks is not None:
        ns.target_clinical_blocks = target_clinical_blocks
    return ns


def _block(bid=None, d=None, tod="AM", is_weekend=False):
    return SimpleNamespace(
        id=bid or uuid4(),
        date=d or date(2024, 6, 3),  # Monday
        time_of_day=tod,
        is_weekend=is_weekend,
    )


def _template(tid=None, name="Template", max_residents=None, rotation_type=None):
    return SimpleNamespace(
        id=tid or uuid4(),
        name=name,
        max_residents=max_residents,
        rotation_type=rotation_type,
    )


def _assignment(person_id, block_id, role="primary", template_id=None):
    return SimpleNamespace(
        person_id=person_id,
        block_id=block_id,
        role=role,
        rotation_template_id=template_id,
    )


def _context(residents=None, faculty=None, blocks=None, templates=None, **kwargs):
    """Build a minimal SchedulingContext with mock data."""
    return SchedulingContext(
        residents=residents or [],
        faculty=faculty or [],
        blocks=blocks or [],
        templates=templates or [],
        **kwargs,
    )


# ---------------------------------------------------------------------------
# ConstraintPriority enum
# ---------------------------------------------------------------------------


class TestConstraintPriority:
    def test_values(self):
        assert ConstraintPriority.CRITICAL.value == 100
        assert ConstraintPriority.HIGH.value == 75
        assert ConstraintPriority.MEDIUM.value == 50
        assert ConstraintPriority.LOW.value == 25

    def test_count(self):
        assert len(ConstraintPriority) == 4


# ---------------------------------------------------------------------------
# ConstraintType enum
# ---------------------------------------------------------------------------


class TestConstraintType:
    def test_core_types_exist(self):
        assert ConstraintType.AVAILABILITY.value == "availability"
        assert ConstraintType.DUTY_HOURS.value == "duty_hours"
        assert ConstraintType.SUPERVISION.value == "supervision"
        assert ConstraintType.CAPACITY.value == "capacity"

    def test_resilience_types_exist(self):
        assert ConstraintType.RESILIENCE.value == "resilience"
        assert ConstraintType.HUB_PROTECTION.value == "hub_protection"
        assert ConstraintType.UTILIZATION_BUFFER.value == "utilization_buffer"
        assert ConstraintType.ZONE_BOUNDARY.value == "zone_boundary"
        assert ConstraintType.PREFERENCE_TRAIL.value == "preference_trail"
        assert ConstraintType.N1_VULNERABILITY.value == "n1_vulnerability"


# ---------------------------------------------------------------------------
# ConstraintViolation dataclass
# ---------------------------------------------------------------------------


class TestConstraintViolation:
    def test_construction(self):
        v = ConstraintViolation(
            constraint_name="Test",
            constraint_type=ConstraintType.AVAILABILITY,
            severity="CRITICAL",
            message="Test violation",
        )
        assert v.constraint_name == "Test"
        assert v.severity == "CRITICAL"
        assert v.person_id is None
        assert v.block_id is None
        assert v.details == {}

    def test_with_ids(self):
        pid, bid = uuid4(), uuid4()
        v = ConstraintViolation(
            constraint_name="X",
            constraint_type=ConstraintType.CAPACITY,
            severity="HIGH",
            message="msg",
            person_id=pid,
            block_id=bid,
            details={"count": 5},
        )
        assert v.person_id == pid
        assert v.block_id == bid
        assert v.details == {"count": 5}


# ---------------------------------------------------------------------------
# ConstraintResult dataclass
# ---------------------------------------------------------------------------


class TestConstraintResult:
    def test_satisfied(self):
        r = ConstraintResult(satisfied=True)
        assert r.satisfied is True
        assert r.violations == []
        assert r.penalty == 0.0

    def test_with_violations(self):
        v = ConstraintViolation(
            constraint_name="X",
            constraint_type=ConstraintType.DUTY_HOURS,
            severity="HIGH",
            message="msg",
        )
        r = ConstraintResult(satisfied=False, violations=[v], penalty=10.0)
        assert r.satisfied is False
        assert len(r.violations) == 1
        assert r.penalty == 10.0


# ---------------------------------------------------------------------------
# HardConstraint / SoftConstraint base classes
# ---------------------------------------------------------------------------


class TestHardConstraint:
    def test_get_penalty_infinite(self):
        # Need a concrete subclass
        c = AvailabilityConstraint()
        assert c.get_penalty() == float("inf")

    def test_is_hard_constraint(self):
        c = OnePersonPerBlockConstraint()
        assert isinstance(c, HardConstraint)


class TestSoftConstraint:
    def test_get_penalty_calculation(self):
        c = EquityConstraint(weight=10.0)
        # penalty = weight * violation_count * priority.value
        # priority = MEDIUM = 50
        penalty = c.get_penalty(violation_count=2)
        assert penalty == 10.0 * 2 * 50

    def test_weight_stored(self):
        c = CoverageConstraint(weight=1000.0)
        assert c.weight == 1000.0

    def test_is_soft_constraint(self):
        c = EquityConstraint()
        assert isinstance(c, SoftConstraint)


# ---------------------------------------------------------------------------
# SchedulingContext
# ---------------------------------------------------------------------------


class TestSchedulingContext:
    def test_post_init_builds_indices(self):
        r1 = _person()
        b1 = _block()
        t1 = _template()
        ctx = _context(residents=[r1], blocks=[b1], templates=[t1])
        assert ctx.resident_idx[r1.id] == 0
        assert ctx.block_idx[b1.id] == 0
        assert ctx.template_idx[t1.id] == 0

    def test_blocks_by_date(self):
        d = date(2024, 6, 3)
        b1 = _block(d=d, tod="AM")
        b2 = _block(d=d, tod="PM")
        ctx = _context(blocks=[b1, b2])
        assert len(ctx.blocks_by_date[d]) == 2

    def test_has_resilience_data_empty(self):
        ctx = _context()
        assert ctx.has_resilience_data() is False

    def test_has_resilience_data_with_hub_scores(self):
        fid = uuid4()
        ctx = _context(hub_scores={fid: 0.8})
        assert ctx.has_resilience_data() is True

    def test_has_resilience_data_with_utilization(self):
        ctx = _context(current_utilization=0.75)
        assert ctx.has_resilience_data() is True

    def test_get_hub_score_known(self):
        fid = uuid4()
        ctx = _context(hub_scores={fid: 0.65})
        assert ctx.get_hub_score(fid) == 0.65

    def test_get_hub_score_unknown(self):
        ctx = _context()
        assert ctx.get_hub_score(uuid4()) == 0.0

    def test_is_n1_vulnerable(self):
        fid = uuid4()
        ctx = _context(n1_vulnerable_faculty={fid})
        assert ctx.is_n1_vulnerable(fid) is True
        assert ctx.is_n1_vulnerable(uuid4()) is False

    def test_get_preference_strength_known(self):
        fid = uuid4()
        ctx = _context(preference_trails={fid: {"monday_am": 0.9}})
        assert ctx.get_preference_strength(fid, "monday_am") == 0.9

    def test_get_preference_strength_unknown(self):
        ctx = _context()
        assert ctx.get_preference_strength(uuid4(), "monday_am") == 0.5

    def test_defaults(self):
        ctx = _context()
        assert ctx.current_utilization == 0.0
        assert ctx.target_utilization == 0.80
        assert ctx.locked_blocks == set()


# ---------------------------------------------------------------------------
# AvailabilityConstraint.validate
# ---------------------------------------------------------------------------


class TestAvailabilityConstraintValidate:
    def test_no_violations(self):
        r = _person(name="Intern A")
        b = _block()
        ctx = _context(residents=[r], blocks=[b])
        a = _assignment(r.id, b.id)
        result = AvailabilityConstraint().validate([a], ctx)
        assert result.satisfied is True

    def test_violation_when_unavailable(self):
        r = _person(name="Intern B")
        b = _block()
        avail = {r.id: {b.id: {"available": False}}}
        ctx = _context(residents=[r], blocks=[b], availability=avail)
        a = _assignment(r.id, b.id)
        result = AvailabilityConstraint().validate([a], ctx)
        assert result.satisfied is False
        assert len(result.violations) == 1
        assert "absence" in result.violations[0].message

    def test_name_resolved_in_violation(self):
        r = _person(name="Dr. Smith")
        b = _block()
        avail = {r.id: {b.id: {"available": False}}}
        ctx = _context(residents=[r], blocks=[b], availability=avail)
        a = _assignment(r.id, b.id)
        result = AvailabilityConstraint().validate([a], ctx)
        assert "Dr. Smith" in result.violations[0].message


# ---------------------------------------------------------------------------
# OnePersonPerBlockConstraint.validate
# ---------------------------------------------------------------------------


class TestOnePersonPerBlockValidate:
    def test_single_assignment_ok(self):
        r = _person()
        b = _block()
        ctx = _context(residents=[r], blocks=[b])
        a = _assignment(r.id, b.id, role="primary")
        result = OnePersonPerBlockConstraint().validate([a], ctx)
        assert result.satisfied is True

    def test_two_primaries_violated(self):
        r1 = _person()
        r2 = _person()
        b = _block()
        ctx = _context(residents=[r1, r2], blocks=[b])
        a1 = _assignment(r1.id, b.id, role="primary")
        a2 = _assignment(r2.id, b.id, role="primary")
        result = OnePersonPerBlockConstraint().validate([a1, a2], ctx)
        assert result.satisfied is False
        assert result.violations[0].details["count"] == 2

    def test_custom_max_per_block(self):
        r1, r2, r3 = _person(), _person(), _person()
        b = _block()
        ctx = _context(residents=[r1, r2, r3], blocks=[b])
        a1 = _assignment(r1.id, b.id, role="primary")
        a2 = _assignment(r2.id, b.id, role="primary")
        result = OnePersonPerBlockConstraint(max_per_block=2).validate([a1, a2], ctx)
        assert result.satisfied is True


# ---------------------------------------------------------------------------
# EightyHourRuleConstraint
# ---------------------------------------------------------------------------


class TestEightyHourRule:
    def test_constants(self):
        c = EightyHourRuleConstraint()
        assert c.HOURS_PER_BLOCK == 6
        assert c.MAX_WEEKLY_HOURS == 80
        assert c.ROLLING_WEEKS == 4
        # Max blocks per 4-week window = (80 * 4) // 6 = 53
        assert c.max_blocks_per_window == 53

    def test_under_limit_ok(self):
        r = _person(name="Resident")
        # 10 blocks over 28 days = 60 hours / 4 weeks = 15 hours/week
        blocks = [_block(d=date(2024, 6, 3) + timedelta(days=i)) for i in range(10)]
        ctx = _context(residents=[r], blocks=blocks)
        assignments = [_assignment(r.id, b.id) for b in blocks]
        result = EightyHourRuleConstraint().validate(assignments, ctx)
        assert result.satisfied is True

    def test_over_limit_violation(self):
        r = _person(name="Overworked")
        # 54 blocks in 28 days → 324 hours / 4 weeks = 81 hours/week
        blocks = []
        for day in range(28):
            d = date(2024, 6, 3) + timedelta(days=day)
            blocks.append(_block(d=d, tod="AM"))
            blocks.append(_block(d=d, tod="PM"))
        ctx = _context(residents=[r], blocks=blocks)
        assignments = [_assignment(r.id, b.id) for b in blocks]
        result = EightyHourRuleConstraint().validate(assignments, ctx)
        assert result.satisfied is False
        assert "Overworked" in result.violations[0].message


# ---------------------------------------------------------------------------
# OneInSevenRuleConstraint.validate
# ---------------------------------------------------------------------------


class TestOneInSevenRuleValidate:
    def test_six_consecutive_ok(self):
        r = _person(name="R1")
        blocks = [_block(d=date(2024, 6, 3) + timedelta(days=i)) for i in range(6)]
        ctx = _context(residents=[r], blocks=blocks)
        assignments = [_assignment(r.id, b.id) for b in blocks]
        result = OneInSevenRuleConstraint().validate(assignments, ctx)
        assert result.satisfied is True

    def test_seven_consecutive_violated(self):
        r = _person(name="R2")
        blocks = [_block(d=date(2024, 6, 3) + timedelta(days=i)) for i in range(7)]
        ctx = _context(residents=[r], blocks=blocks)
        assignments = [_assignment(r.id, b.id) for b in blocks]
        result = OneInSevenRuleConstraint().validate(assignments, ctx)
        assert result.satisfied is False
        assert result.violations[0].details["consecutive_days"] == 7


# ---------------------------------------------------------------------------
# SupervisionRatioConstraint
# ---------------------------------------------------------------------------


class TestSupervisionRatio:
    def test_calculate_pgy1_only(self):
        c = SupervisionRatioConstraint()
        # 2 PGY-1 needs 1 faculty (ratio 1:2)
        assert c.calculate_required_faculty(2, 0) == 1
        # 3 PGY-1 needs 2 faculty
        assert c.calculate_required_faculty(3, 0) == 2

    def test_calculate_other_only(self):
        c = SupervisionRatioConstraint()
        # 4 PGY-2/3 needs 1 faculty (ratio 1:4)
        assert c.calculate_required_faculty(0, 4) == 1
        # 5 needs 2
        assert c.calculate_required_faculty(0, 5) == 2

    def test_calculate_mixed(self):
        c = SupervisionRatioConstraint()
        # 2 PGY-1 (1 faculty) + 4 PGY-2/3 (1 faculty) = 2 total
        assert c.calculate_required_faculty(2, 4) == 2

    def test_calculate_no_residents(self):
        c = SupervisionRatioConstraint()
        assert c.calculate_required_faculty(0, 0) == 0

    def test_validate_adequate_supervision(self):
        c = SupervisionRatioConstraint()
        r1 = _person(pgy_level=1)
        r2 = _person(pgy_level=1)
        f1 = _person(name="Faculty")
        b = _block()
        ctx = _context(residents=[r1, r2], faculty=[f1], blocks=[b])
        # 2 PGY-1 + 1 faculty = adequate (1:2 ratio)
        a_r1 = _assignment(r1.id, b.id, role="primary")
        a_r2 = _assignment(r2.id, b.id, role="primary")
        a_f = _assignment(f1.id, b.id, role="faculty")
        result = c.validate([a_r1, a_r2, a_f], ctx)
        assert result.satisfied is True

    def test_validate_inadequate_supervision(self):
        c = SupervisionRatioConstraint()
        r1 = _person(pgy_level=1)
        r2 = _person(pgy_level=1)
        r3 = _person(pgy_level=1)
        f1 = _person(name="Faculty")
        b = _block()
        ctx = _context(residents=[r1, r2, r3], faculty=[f1], blocks=[b])
        # 3 PGY-1 needs 2 faculty but only 1 assigned
        a_r1 = _assignment(r1.id, b.id, role="primary")
        a_r2 = _assignment(r2.id, b.id, role="primary")
        a_r3 = _assignment(r3.id, b.id, role="primary")
        a_f = _assignment(f1.id, b.id, role="faculty")
        result = c.validate([a_r1, a_r2, a_r3, a_f], ctx)
        assert result.satisfied is False
        assert result.violations[0].details["required"] == 2


# ---------------------------------------------------------------------------
# ClinicCapacityConstraint.validate
# ---------------------------------------------------------------------------


class TestClinicCapacityValidate:
    def test_under_capacity(self):
        t = _template(max_residents=3)
        b = _block()
        r1, r2 = _person(), _person()
        ctx = _context(residents=[r1, r2], blocks=[b], templates=[t])
        a1 = _assignment(r1.id, b.id, template_id=t.id)
        a2 = _assignment(r2.id, b.id, template_id=t.id)
        result = ClinicCapacityConstraint().validate([a1, a2], ctx)
        assert result.satisfied is True

    def test_over_capacity(self):
        t = _template(name="FMClinic", max_residents=1)
        b = _block()
        r1, r2 = _person(), _person()
        ctx = _context(residents=[r1, r2], blocks=[b], templates=[t])
        a1 = _assignment(r1.id, b.id, template_id=t.id)
        a2 = _assignment(r2.id, b.id, template_id=t.id)
        result = ClinicCapacityConstraint().validate([a1, a2], ctx)
        assert result.satisfied is False
        assert "FMClinic" in result.violations[0].message


# ---------------------------------------------------------------------------
# WednesdayAMInternOnlyConstraint.validate
# ---------------------------------------------------------------------------


class TestWednesdayAMInternOnly:
    def test_is_wednesday_am(self):
        c = WednesdayAMInternOnlyConstraint()
        wed = _block(d=date(2024, 6, 5), tod="AM")  # Wednesday
        assert c._is_wednesday_am(wed) is True

    def test_is_not_wednesday_am(self):
        c = WednesdayAMInternOnlyConstraint()
        tue = _block(d=date(2024, 6, 4), tod="AM")  # Tuesday
        assert c._is_wednesday_am(tue) is False
        wed_pm = _block(d=date(2024, 6, 5), tod="PM")
        assert c._is_wednesday_am(wed_pm) is False

    def test_intern_on_wed_am_ok(self):
        c = WednesdayAMInternOnlyConstraint()
        t = _template(rotation_type="outpatient")
        r = _person(pgy_level=1)
        b = _block(d=date(2024, 6, 5), tod="AM")  # Wednesday
        ctx = _context(residents=[r], blocks=[b], templates=[t])
        a = _assignment(r.id, b.id, template_id=t.id)
        result = c.validate([a], ctx)
        assert result.satisfied is True

    def test_pgy2_on_wed_am_violated(self):
        c = WednesdayAMInternOnlyConstraint()
        t = _template(rotation_type="outpatient")
        r = _person(name="PGY-2 Doc", pgy_level=2)
        b = _block(d=date(2024, 6, 5), tod="AM")  # Wednesday
        ctx = _context(residents=[r], blocks=[b], templates=[t])
        a = _assignment(r.id, b.id, template_id=t.id)
        result = c.validate([a], ctx)
        assert result.satisfied is False
        assert "PGY-2" in result.violations[0].message


# ---------------------------------------------------------------------------
# EquityConstraint.validate
# ---------------------------------------------------------------------------


class TestEquityValidate:
    def test_balanced_no_violations(self):
        r1, r2 = _person(), _person()
        b1 = _block(d=date(2024, 6, 3))
        b2 = _block(d=date(2024, 6, 4))
        ctx = _context(residents=[r1, r2], blocks=[b1, b2])
        # Each resident has 1 assignment
        a1 = _assignment(r1.id, b1.id)
        a2 = _assignment(r2.id, b2.id)
        result = EquityConstraint().validate([a1, a2], ctx)
        assert result.satisfied is True
        assert result.penalty == 0.0

    def test_imbalanced_generates_penalty(self):
        r1, r2 = _person(), _person()
        blocks = [_block(d=date(2024, 6, 3) + timedelta(days=i)) for i in range(10)]
        ctx = _context(residents=[r1, r2], blocks=blocks)
        # r1 gets 8 assignments, r2 gets 2
        assignments = [_assignment(r1.id, b.id) for b in blocks[:8]]
        assignments += [_assignment(r2.id, b.id) for b in blocks[8:]]
        result = EquityConstraint(weight=10.0).validate(assignments, ctx)
        assert result.penalty > 0

    def test_empty_no_penalty(self):
        ctx = _context(residents=[_person()])
        result = EquityConstraint().validate([], ctx)
        assert result.satisfied is True
        assert result.penalty == 0.0


# ---------------------------------------------------------------------------
# CoverageConstraint.validate
# ---------------------------------------------------------------------------


class TestCoverageValidate:
    def test_full_coverage(self):
        b1 = _block(d=date(2024, 6, 3))
        b2 = _block(d=date(2024, 6, 4))
        r = _person()
        ctx = _context(residents=[r], blocks=[b1, b2])
        a1 = _assignment(r.id, b1.id)
        a2 = _assignment(r.id, b2.id)
        result = CoverageConstraint().validate([a1, a2], ctx)
        assert result.satisfied is True

    def test_low_coverage_has_penalty(self):
        blocks = [_block(d=date(2024, 6, 3) + timedelta(days=i)) for i in range(10)]
        r = _person()
        ctx = _context(residents=[r], blocks=blocks)
        # Only cover 5 of 10
        assignments = [_assignment(r.id, b.id) for b in blocks[:5]]
        result = CoverageConstraint(weight=1000.0).validate(assignments, ctx)
        assert result.penalty > 0


# ---------------------------------------------------------------------------
# ContinuityConstraint.validate
# ---------------------------------------------------------------------------


class TestContinuityValidate:
    def test_same_template_no_penalty(self):
        t = _template()
        r = _person()
        b1 = _block(d=date(2024, 6, 3))
        b2 = _block(d=date(2024, 6, 4))
        ctx = _context(residents=[r], blocks=[b1, b2])
        a1 = _assignment(r.id, b1.id, template_id=t.id)
        a2 = _assignment(r.id, b2.id, template_id=t.id)
        result = ContinuityConstraint().validate([a1, a2], ctx)
        assert result.penalty == 0.0

    def test_template_change_has_penalty(self):
        t1, t2 = _template(), _template()
        r = _person()
        b1 = _block(d=date(2024, 6, 3))
        b2 = _block(d=date(2024, 6, 4))
        ctx = _context(residents=[r], blocks=[b1, b2])
        a1 = _assignment(r.id, b1.id, template_id=t1.id)
        a2 = _assignment(r.id, b2.id, template_id=t2.id)
        result = ContinuityConstraint(weight=5.0).validate([a1, a2], ctx)
        assert result.penalty == 5.0


# ---------------------------------------------------------------------------
# PreferenceConstraint.validate
# ---------------------------------------------------------------------------


class TestPreferenceValidate:
    def test_high_preference_low_penalty(self):
        r = _person()
        t = _template()
        b = _block()
        prefs = {r.id: {t.id: 0.9}}
        ctx = _context(residents=[r], blocks=[b])
        a = _assignment(r.id, b.id, template_id=t.id)
        result = PreferenceConstraint(preferences=prefs, weight=2.0).validate([a], ctx)
        # penalty = (1 - 0.9) * 2.0 * 1 = 0.2
        assert result.penalty < 1.0

    def test_no_preference_neutral(self):
        r = _person()
        t = _template()
        b = _block()
        ctx = _context(residents=[r], blocks=[b])
        a = _assignment(r.id, b.id, template_id=t.id)
        result = PreferenceConstraint(weight=2.0).validate([a], ctx)
        # Default 0.5 → penalty = (1 - 0.5) * 2.0 * 1 = 1.0
        assert abs(result.penalty - 1.0) < 0.01


# ---------------------------------------------------------------------------
# HubProtectionConstraint.validate
# ---------------------------------------------------------------------------


class TestHubProtectionValidate:
    def test_no_hub_scores_no_penalty(self):
        ctx = _context()
        result = HubProtectionConstraint().validate([], ctx)
        assert result.penalty == 0.0

    def test_hub_over_assigned_violation(self):
        f1 = _person(name="Hub Faculty")
        f2 = _person(name="Normal Faculty")
        blocks = [_block(d=date(2024, 6, 3) + timedelta(days=i)) for i in range(10)]
        ctx = _context(
            faculty=[f1, f2],
            blocks=blocks,
            hub_scores={f1.id: 0.7, f2.id: 0.1},
        )
        # Hub gets 8 assignments, normal gets 2
        assignments = [_assignment(f1.id, b.id) for b in blocks[:8]]
        assignments += [_assignment(f2.id, b.id) for b in blocks[8:]]
        result = HubProtectionConstraint(weight=15.0).validate(assignments, ctx)
        assert result.penalty > 0
        assert len(result.violations) > 0

    def test_critical_hub_higher_severity(self):
        f1 = _person(name="Critical Hub")
        blocks = [_block(d=date(2024, 6, 3) + timedelta(days=i)) for i in range(5)]
        ctx = _context(
            faculty=[f1],
            blocks=blocks,
            hub_scores={f1.id: 0.8},
        )
        assignments = [_assignment(f1.id, b.id) for b in blocks]
        result = HubProtectionConstraint().validate(assignments, ctx)
        assert result.penalty > 0


# ---------------------------------------------------------------------------
# ZoneBoundaryConstraint.validate
# ---------------------------------------------------------------------------


class TestZoneBoundaryValidate:
    def test_no_zone_data_no_penalty(self):
        ctx = _context()
        result = ZoneBoundaryConstraint().validate([], ctx)
        assert result.penalty == 0.0

    def test_same_zone_no_penalty(self):
        f = _person()
        b = _block()
        zone_id = uuid4()
        ctx = _context(
            faculty=[f],
            blocks=[b],
            zone_assignments={f.id: zone_id},
            block_zones={b.id: zone_id},
        )
        a = _assignment(f.id, b.id)
        result = ZoneBoundaryConstraint().validate([a], ctx)
        assert result.penalty == 0.0

    def test_cross_zone_has_penalty(self):
        f = _person()
        b = _block()
        zone_a, zone_b = uuid4(), uuid4()
        ctx = _context(
            faculty=[f],
            blocks=[b],
            zone_assignments={f.id: zone_a},
            block_zones={b.id: zone_b},
        )
        a = _assignment(f.id, b.id)
        result = ZoneBoundaryConstraint(weight=12.0).validate([a], ctx)
        assert result.penalty == 12.0
        assert len(result.violations) > 0


# ---------------------------------------------------------------------------
# N1VulnerabilityConstraint.validate
# ---------------------------------------------------------------------------


class TestN1VulnerabilityValidate:
    def test_redundant_coverage_no_violation(self):
        f1, f2 = _person(name="F1"), _person(name="F2")
        b = _block()
        ctx = _context(faculty=[f1, f2], blocks=[b])
        a1 = _assignment(f1.id, b.id)
        a2 = _assignment(f2.id, b.id)
        result = N1VulnerabilityConstraint().validate([a1, a2], ctx)
        # 2 providers = no N-1 vulnerability
        n1_blocks = (
            result.violations[0].details.get("n1_vulnerable_blocks", 0)
            if result.violations
            else 0
        )
        assert n1_blocks == 0

    def test_single_coverage_is_vulnerable(self):
        f1 = _person(name="Solo Faculty")
        b = _block()
        ctx = _context(faculty=[f1], blocks=[b])
        a = _assignment(f1.id, b.id)
        result = N1VulnerabilityConstraint().validate([a], ctx)
        assert result.penalty > 0
        assert len(result.violations) >= 1


# ---------------------------------------------------------------------------
# ConstraintManager
# ---------------------------------------------------------------------------


class TestConstraintManagerBasics:
    def test_add_and_get(self):
        mgr = ConstraintManager()
        c = AvailabilityConstraint()
        mgr.add(c)
        assert len(mgr.constraints) == 1
        assert len(mgr.get_hard_constraints()) == 1
        assert len(mgr.get_soft_constraints()) == 0

    def test_add_soft_constraint(self):
        mgr = ConstraintManager()
        mgr.add(EquityConstraint())
        assert len(mgr.get_soft_constraints()) == 1
        assert len(mgr.get_hard_constraints()) == 0

    def test_method_chaining(self):
        mgr = ConstraintManager()
        result = mgr.add(AvailabilityConstraint()).add(EquityConstraint())
        assert result is mgr
        assert len(mgr.constraints) == 2

    def test_remove(self):
        mgr = ConstraintManager()
        mgr.add(AvailabilityConstraint())
        mgr.add(EquityConstraint())
        mgr.remove("Availability")
        assert len(mgr.constraints) == 1
        assert mgr.constraints[0].name == "Equity"

    def test_remove_nonexistent_no_error(self):
        mgr = ConstraintManager()
        mgr.remove("NonExistent")  # Should not raise

    def test_enable_disable(self):
        mgr = ConstraintManager()
        mgr.add(AvailabilityConstraint())
        mgr.disable("Availability")
        assert len(mgr.get_enabled()) == 0
        mgr.enable("Availability")
        assert len(mgr.get_enabled()) == 1

    def test_get_enabled_filters_disabled(self):
        mgr = ConstraintManager()
        mgr.add(AvailabilityConstraint())
        mgr.add(EquityConstraint())
        mgr.disable("Equity")
        enabled = mgr.get_enabled()
        assert len(enabled) == 1
        assert enabled[0].name == "Availability"


class TestConstraintManagerFactories:
    def test_create_default(self):
        mgr = ConstraintManager.create_default()
        # Should have hard + soft constraints
        assert len(mgr.get_hard_constraints()) >= 5
        assert len(mgr.get_soft_constraints()) >= 3
        # Core ACGME constraints should be present and enabled
        enabled_names = {c.name for c in mgr.get_enabled()}
        assert "Availability" in enabled_names
        assert "80HourRule" in enabled_names
        assert "SupervisionRatio" in enabled_names

    def test_create_resilience_aware_tier2(self):
        mgr = ConstraintManager.create_resilience_aware(tier=2)
        enabled_names = {c.name for c in mgr.get_enabled()}
        assert "HubProtection" in enabled_names
        assert "UtilizationBuffer" in enabled_names
        assert "ZoneBoundary" in enabled_names
        assert "N1Vulnerability" in enabled_names

    def test_create_resilience_aware_tier1(self):
        mgr = ConstraintManager.create_resilience_aware(tier=1)
        enabled_names = {c.name for c in mgr.get_enabled()}
        assert "HubProtection" in enabled_names
        assert "UtilizationBuffer" in enabled_names
        # Tier 2 disabled
        assert "ZoneBoundary" not in enabled_names

    def test_create_minimal(self):
        mgr = ConstraintManager.create_minimal()
        names = {c.name for c in mgr.constraints}
        assert "Availability" in names
        assert "Coverage" in names
        # Minimal should have very few constraints
        assert len(mgr.constraints) <= 5

    def test_create_strict(self):
        mgr = ConstraintManager.create_strict()
        # Soft constraint weights should be doubled
        for c in mgr.get_soft_constraints():
            if c.name == "Coverage":
                assert c.weight == 2000.0
            elif c.name == "Equity":
                assert c.weight == 20.0


class TestConstraintManagerValidateAll:
    def test_all_satisfied(self):
        mgr = ConstraintManager()
        mgr.add(AvailabilityConstraint())
        r = _person()
        b = _block()
        ctx = _context(residents=[r], blocks=[b])
        a = _assignment(r.id, b.id)
        result = mgr.validate_all([a], ctx)
        assert result.satisfied is True

    def test_hard_violation_not_satisfied(self):
        mgr = ConstraintManager()
        mgr.add(AvailabilityConstraint())
        r = _person()
        b = _block()
        avail = {r.id: {b.id: {"available": False}}}
        ctx = _context(residents=[r], blocks=[b], availability=avail)
        a = _assignment(r.id, b.id)
        result = mgr.validate_all([a], ctx)
        assert result.satisfied is False
        assert len(result.violations) >= 1

    def test_soft_violation_still_satisfied(self):
        mgr = ConstraintManager()
        mgr.add(EquityConstraint(weight=10.0))
        r1, r2 = _person(), _person()
        blocks = [_block(d=date(2024, 6, 3) + timedelta(days=i)) for i in range(10)]
        ctx = _context(residents=[r1, r2], blocks=blocks)
        # Imbalanced: r1 gets 8, r2 gets 2
        assignments = [_assignment(r1.id, b.id) for b in blocks[:8]]
        assignments += [_assignment(r2.id, b.id) for b in blocks[8:]]
        result = mgr.validate_all(assignments, ctx)
        # Soft constraints are always "satisfied" (penalty only)
        assert result.satisfied is True
        assert result.penalty > 0

    def test_disabled_constraints_skipped(self):
        mgr = ConstraintManager()
        mgr.add(AvailabilityConstraint())
        mgr.disable("Availability")
        r = _person()
        b = _block()
        avail = {r.id: {b.id: {"available": False}}}
        ctx = _context(residents=[r], blocks=[b], availability=avail)
        a = _assignment(r.id, b.id)
        result = mgr.validate_all([a], ctx)
        # Should be satisfied because the constraint is disabled
        assert result.satisfied is True
