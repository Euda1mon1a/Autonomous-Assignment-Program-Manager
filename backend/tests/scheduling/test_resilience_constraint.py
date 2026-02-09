"""Tests for resilience constraints (pure logic, no DB required)."""

from datetime import date
from types import SimpleNamespace
from uuid import uuid4

from app.scheduling.constraints.base import (
    ConstraintPriority,
    ConstraintType,
    SchedulingContext,
)
from app.scheduling.constraints.resilience import (
    HubProtectionConstraint,
    N1VulnerabilityConstraint,
    PreferenceTrailConstraint,
    UtilizationBufferConstraint,
    ZoneBoundaryConstraint,
)


# ==================== Helpers ====================


def _person(pid=None, name="Faculty", **kwargs):
    ns = SimpleNamespace(id=pid or uuid4(), name=name)
    for k, v in kwargs.items():
        setattr(ns, k, v)
    return ns


def _block(bid=None, block_date=None, time_of_day="AM", **kwargs):
    ns = SimpleNamespace(
        id=bid or uuid4(),
        date=block_date or date(2025, 3, 3),
        time_of_day=time_of_day,
    )
    for k, v in kwargs.items():
        setattr(ns, k, v)
    return ns


def _assignment(person_id, block_id, **kwargs):
    ns = SimpleNamespace(person_id=person_id, block_id=block_id)
    for k, v in kwargs.items():
        setattr(ns, k, v)
    return ns


def _context(faculty=None, blocks=None, **kwargs):
    ctx = SchedulingContext(
        residents=[],
        faculty=faculty or [],
        blocks=blocks or [],
        templates=[],
    )
    for k, v in kwargs.items():
        setattr(ctx, k, v)
    return ctx


# ==================== HubProtectionConstraint Tests ====================


class TestHubProtectionInit:
    def test_name(self):
        c = HubProtectionConstraint()
        assert c.name == "HubProtection"

    def test_type(self):
        c = HubProtectionConstraint()
        assert c.constraint_type == ConstraintType.HUB_PROTECTION

    def test_priority(self):
        c = HubProtectionConstraint()
        assert c.priority == ConstraintPriority.MEDIUM

    def test_default_weight(self):
        c = HubProtectionConstraint()
        assert c.weight == 15.0

    def test_custom_weight(self):
        c = HubProtectionConstraint(weight=30.0)
        assert c.weight == 30.0

    def test_thresholds(self):
        assert HubProtectionConstraint.HIGH_HUB_THRESHOLD == 0.4
        assert HubProtectionConstraint.CRITICAL_HUB_THRESHOLD == 0.6


class TestHubProtectionValidate:
    def test_no_hub_scores_satisfied(self):
        """No hub_scores -> satisfied, zero penalty."""
        c = HubProtectionConstraint()
        ctx = _context()
        result = c.validate([], ctx)
        assert result.satisfied is True
        assert result.penalty == 0.0

    def test_hub_below_threshold_no_penalty(self):
        """Hub score below 0.4 -> no penalty."""
        c = HubProtectionConstraint()
        fac = _person(name="Dr. A")
        b = _block()
        ctx = _context(faculty=[fac], blocks=[b])
        ctx.hub_scores = {fac.id: 0.3}

        a = _assignment(fac.id, b.id)
        result = c.validate([a], ctx)
        assert result.penalty == 0.0

    def test_high_hub_with_assignments_penalty(self):
        """Hub score >= 0.4 with assignments -> penalty."""
        c = HubProtectionConstraint(weight=15.0)
        fac1 = _person(name="Dr. Hub")
        fac2 = _person(name="Dr. Normal")
        b = _block()
        ctx = _context(faculty=[fac1, fac2], blocks=[b])
        ctx.hub_scores = {fac1.id: 0.5, fac2.id: 0.1}

        # fac1 (hub) gets the assignment
        a = _assignment(fac1.id, b.id)
        result = c.validate([a], ctx)
        # penalty = count(1) * hub_score(0.5) * multiplier(1.0) * weight(15.0) = 7.5
        assert result.penalty == 7.5

    def test_critical_hub_double_multiplier(self):
        """Hub score >= 0.6 -> 2x multiplier."""
        c = HubProtectionConstraint(weight=15.0)
        fac = _person(name="Dr. Critical")
        b = _block()
        ctx = _context(faculty=[fac], blocks=[b])
        ctx.hub_scores = {fac.id: 0.7}

        a = _assignment(fac.id, b.id)
        result = c.validate([a], ctx)
        # penalty = 1 * 0.7 * 2.0 * 15.0 = 21.0
        assert result.penalty == 21.0

    def test_hub_over_average_violation(self):
        """Hub assigned > 1.2x average -> violation."""
        c = HubProtectionConstraint()
        fac1 = _person(name="Dr. Hub")
        fac2 = _person(name="Dr. Normal")
        blocks = [_block() for _ in range(5)]
        ctx = _context(faculty=[fac1, fac2], blocks=blocks)
        ctx.hub_scores = {fac1.id: 0.5, fac2.id: 0.1}

        # fac1 gets 4 assignments, fac2 gets 1 -> avg = 2.5, 4 > 2.5*1.2=3.0
        assignments = [_assignment(fac1.id, b.id) for b in blocks[:4]] + [
            _assignment(fac2.id, blocks[4].id)
        ]
        result = c.validate(assignments, ctx)
        assert len(result.violations) >= 1
        assert result.violations[0].severity == "MEDIUM"

    def test_critical_hub_over_average_high_severity(self):
        """Critical hub (>= 0.6) over average -> HIGH severity."""
        c = HubProtectionConstraint()
        fac1 = _person(name="Dr. Critical")
        fac2 = _person(name="Dr. Normal")
        blocks = [_block() for _ in range(5)]
        ctx = _context(faculty=[fac1, fac2], blocks=blocks)
        ctx.hub_scores = {fac1.id: 0.7, fac2.id: 0.1}

        assignments = [_assignment(fac1.id, b.id) for b in blocks[:4]] + [
            _assignment(fac2.id, blocks[4].id)
        ]
        result = c.validate(assignments, ctx)
        assert any(v.severity == "HIGH" for v in result.violations)


# ==================== UtilizationBufferConstraint Tests ====================


class TestUtilizationBufferInit:
    def test_name(self):
        c = UtilizationBufferConstraint()
        assert c.name == "UtilizationBuffer"

    def test_type(self):
        c = UtilizationBufferConstraint()
        assert c.constraint_type == ConstraintType.UTILIZATION_BUFFER

    def test_priority(self):
        c = UtilizationBufferConstraint()
        assert c.priority == ConstraintPriority.HIGH

    def test_default_weight(self):
        c = UtilizationBufferConstraint()
        assert c.weight == 20.0

    def test_default_target_utilization(self):
        c = UtilizationBufferConstraint()
        assert c.target_utilization == 0.80

    def test_custom_target_utilization(self):
        c = UtilizationBufferConstraint(target_utilization=0.75)
        assert c.target_utilization == 0.75


# Note: UtilizationBufferConstraint.validate uses assignment.role and block.is_weekend
# which require specific mock attributes. The validate logic is complex and
# tightly coupled to context.availability. Init tests cover the public API.


# ==================== ZoneBoundaryConstraint Tests ====================


class TestZoneBoundaryInit:
    def test_name(self):
        c = ZoneBoundaryConstraint()
        assert c.name == "ZoneBoundary"

    def test_type(self):
        c = ZoneBoundaryConstraint()
        assert c.constraint_type == ConstraintType.ZONE_BOUNDARY

    def test_priority(self):
        c = ZoneBoundaryConstraint()
        assert c.priority == ConstraintPriority.MEDIUM

    def test_default_weight(self):
        c = ZoneBoundaryConstraint()
        assert c.weight == 12.0

    def test_zone_priority_map(self):
        assert ZoneBoundaryConstraint.ZONE_PRIORITY["inpatient"] == 2.0
        assert ZoneBoundaryConstraint.ZONE_PRIORITY["admin"] == 0.5


class TestZoneBoundaryValidate:
    def test_no_zone_data_satisfied(self):
        """No zone_assignments or block_zones -> satisfied."""
        c = ZoneBoundaryConstraint()
        ctx = _context()
        result = c.validate([], ctx)
        assert result.satisfied is True
        assert result.penalty == 0.0

    def test_same_zone_no_penalty(self):
        """Faculty in same zone as block -> no penalty."""
        c = ZoneBoundaryConstraint()
        fac = _person(name="Dr. A")
        zone_id = uuid4()
        b = _block()
        ctx = _context(faculty=[fac], blocks=[b])
        ctx.zone_assignments = {fac.id: zone_id}
        ctx.block_zones = {b.id: zone_id}

        a = _assignment(fac.id, b.id)
        result = c.validate([a], ctx)
        assert result.penalty == 0.0

    def test_cross_zone_penalty(self):
        """Faculty in different zone from block -> penalty."""
        c = ZoneBoundaryConstraint(weight=12.0)
        fac = _person(name="Dr. A")
        zone_a = uuid4()
        zone_b = uuid4()
        b = _block()
        ctx = _context(faculty=[fac], blocks=[b])
        ctx.zone_assignments = {fac.id: zone_a}
        ctx.block_zones = {b.id: zone_b}

        a = _assignment(fac.id, b.id)
        result = c.validate([a], ctx)
        assert result.penalty == 12.0  # 1 cross-zone * weight

    def test_cross_zone_violation_severity_low(self):
        """< 10% cross-zone -> LOW severity."""
        c = ZoneBoundaryConstraint()
        fac = _person(name="Dr. A")
        zone_a = uuid4()
        zone_b = uuid4()
        blocks = [_block() for _ in range(20)]
        ctx = _context(faculty=[fac], blocks=blocks)
        ctx.zone_assignments = {fac.id: zone_a}
        ctx.block_zones = {blocks[0].id: zone_b}
        # Only 1 block in different zone
        for b in blocks[1:]:
            ctx.block_zones[b.id] = zone_a

        assignments = [_assignment(fac.id, b.id) for b in blocks]
        result = c.validate(assignments, ctx)
        assert len(result.violations) == 1
        assert result.violations[0].severity == "LOW"

    def test_cross_zone_violation_severity_high(self):
        """>= 20% cross-zone -> HIGH severity."""
        c = ZoneBoundaryConstraint()
        fac = _person(name="Dr. A")
        zone_a = uuid4()
        zone_b = uuid4()
        blocks = [_block() for _ in range(5)]
        ctx = _context(faculty=[fac], blocks=blocks)
        ctx.zone_assignments = {fac.id: zone_a}
        # All blocks in different zone
        for b in blocks:
            ctx.block_zones[b.id] = zone_b

        assignments = [_assignment(fac.id, b.id) for b in blocks]
        result = c.validate(assignments, ctx)
        assert result.violations[0].severity == "HIGH"

    def test_no_zone_assignment_skipped(self):
        """Faculty without zone assignment -> not counted."""
        c = ZoneBoundaryConstraint()
        fac = _person(name="Dr. A")
        b = _block()
        ctx = _context(faculty=[fac], blocks=[b])
        ctx.zone_assignments = {}  # Empty
        ctx.block_zones = {b.id: uuid4()}

        a = _assignment(fac.id, b.id)
        result = c.validate([a], ctx)
        assert result.penalty == 0.0


# ==================== PreferenceTrailConstraint Tests ====================


class TestPreferenceTrailInit:
    def test_name(self):
        c = PreferenceTrailConstraint()
        assert c.name == "PreferenceTrail"

    def test_type(self):
        c = PreferenceTrailConstraint()
        assert c.constraint_type == ConstraintType.PREFERENCE_TRAIL

    def test_priority(self):
        c = PreferenceTrailConstraint()
        assert c.priority == ConstraintPriority.LOW

    def test_default_weight(self):
        c = PreferenceTrailConstraint()
        assert c.weight == 8.0

    def test_thresholds(self):
        assert PreferenceTrailConstraint.STRONG_TRAIL_THRESHOLD == 0.6
        assert PreferenceTrailConstraint.WEAK_TRAIL_THRESHOLD == 0.3


class TestPreferenceTrailValidate:
    def test_no_preference_trails_satisfied(self):
        """No preference_trails -> satisfied, zero penalty."""
        c = PreferenceTrailConstraint()
        ctx = _context()
        result = c.validate([], ctx)
        assert result.satisfied is True
        assert result.penalty == 0.0

    def test_aligned_assignment_no_penalty(self):
        """Assignment matching strong trail -> no penalty."""
        c = PreferenceTrailConstraint()
        fac = _person(name="Dr. A")
        # Monday AM -> "monday_am"
        b = _block(block_date=date(2025, 3, 3), time_of_day="AM")
        ctx = _context(faculty=[fac], blocks=[b])
        ctx.preference_trails = {fac.id: {"monday_am": 0.8}}

        a = _assignment(fac.id, b.id)
        result = c.validate([a], ctx)
        assert result.penalty == 0.0

    def test_misaligned_assignment_penalty(self):
        """Assignment against strong avoidance trail -> penalty."""
        c = PreferenceTrailConstraint(weight=8.0)
        fac = _person(name="Dr. A")
        b = _block(block_date=date(2025, 3, 3), time_of_day="AM")
        ctx = _context(faculty=[fac], blocks=[b])
        # Low trail strength = avoidance (< 0.4 = 1.0 - 0.6)
        ctx.preference_trails = {fac.id: {"monday_am": 0.2}}

        a = _assignment(fac.id, b.id)
        result = c.validate([a], ctx)
        # penalty = (0.5 - 0.2) * 8.0 = 2.4
        assert result.penalty > 0

    def test_neutral_trail_no_penalty(self):
        """Trail strength ~0.5 (neutral) -> no penalty."""
        c = PreferenceTrailConstraint()
        fac = _person(name="Dr. A")
        b = _block(block_date=date(2025, 3, 3), time_of_day="AM")
        ctx = _context(faculty=[fac], blocks=[b])
        ctx.preference_trails = {fac.id: {"monday_am": 0.5}}

        a = _assignment(fac.id, b.id)
        result = c.validate([a], ctx)
        assert result.penalty == 0.0

    def test_no_faculty_prefs_skipped(self):
        """Faculty without preference trails -> skipped."""
        c = PreferenceTrailConstraint()
        fac = _person(name="Dr. A")
        b = _block(block_date=date(2025, 3, 3), time_of_day="AM")
        ctx = _context(faculty=[fac], blocks=[b])
        ctx.preference_trails = {}

        a = _assignment(fac.id, b.id)
        result = c.validate([a], ctx)
        assert result.penalty == 0.0

    def test_misalignment_violation_above_threshold(self):
        """>=10% misaligned -> violation."""
        c = PreferenceTrailConstraint()
        fac = _person(name="Dr. A")
        blocks = [
            _block(block_date=date(2025, 3, 3), time_of_day="AM"),
            _block(block_date=date(2025, 3, 4), time_of_day="AM"),
        ]
        ctx = _context(faculty=[fac], blocks=blocks)
        # Both slots have low trail (avoidance)
        ctx.preference_trails = {fac.id: {"monday_am": 0.2, "tuesday_am": 0.2}}

        assignments = [_assignment(fac.id, b.id) for b in blocks]
        result = c.validate(assignments, ctx)
        assert len(result.violations) == 1
        assert "preference trails" in result.violations[0].message


# ==================== N1VulnerabilityConstraint Tests ====================


class TestN1VulnerabilityInit:
    def test_name(self):
        c = N1VulnerabilityConstraint()
        assert c.name == "N1Vulnerability"

    def test_type(self):
        c = N1VulnerabilityConstraint()
        assert c.constraint_type == ConstraintType.N1_VULNERABILITY

    def test_priority(self):
        c = N1VulnerabilityConstraint()
        assert c.priority == ConstraintPriority.HIGH

    def test_default_weight(self):
        c = N1VulnerabilityConstraint()
        assert c.weight == 25.0


class TestN1VulnerabilityValidate:
    def test_no_assignments_satisfied(self):
        c = N1VulnerabilityConstraint()
        ctx = _context()
        result = c.validate([], ctx)
        assert result.satisfied is True
        assert result.penalty == 0.0

    def test_redundant_coverage_no_violation(self):
        """Block covered by 2+ faculty -> no N-1 violation."""
        c = N1VulnerabilityConstraint()
        fac1 = _person(name="Dr. A")
        fac2 = _person(name="Dr. B")
        b = _block()
        ctx = _context(faculty=[fac1, fac2], blocks=[b])

        assignments = [
            _assignment(fac1.id, b.id),
            _assignment(fac2.id, b.id),
        ]
        result = c.validate(assignments, ctx)
        assert result.penalty == 0.0
        assert len(result.violations) == 0

    def test_single_coverage_penalty(self):
        """Block covered by only 1 faculty -> penalty."""
        c = N1VulnerabilityConstraint(weight=25.0)
        fac = _person(name="Dr. A")
        b = _block()
        ctx = _context(faculty=[fac], blocks=[b])

        a = _assignment(fac.id, b.id)
        result = c.validate([a], ctx)
        assert result.penalty == 25.0

    def test_multiple_single_coverage_blocks(self):
        """Multiple blocks with single coverage -> penalty per block."""
        c = N1VulnerabilityConstraint(weight=25.0)
        fac = _person(name="Dr. A")
        blocks = [_block() for _ in range(3)]
        ctx = _context(faculty=[fac], blocks=blocks)

        assignments = [_assignment(fac.id, b.id) for b in blocks]
        result = c.validate(assignments, ctx)
        assert result.penalty == 75.0  # 3 * 25.0

    def test_n1_vulnerable_faculty_extra_penalty(self):
        """Faculty in n1_vulnerable_faculty set -> extra penalty."""
        c = N1VulnerabilityConstraint(weight=25.0)
        fac1 = _person(name="Dr. A")
        fac2 = _person(name="Dr. B")
        b1 = _block()
        b2 = _block()
        ctx = _context(faculty=[fac1, fac2], blocks=[b1, b2])
        ctx.n1_vulnerable_faculty = {fac2.id}

        # fac1 single covers b1 (counted in sole_providers)
        # fac2 covers b2 (both cover b2) - but fac2 is in n1_vulnerable_faculty
        assignments = [
            _assignment(fac1.id, b1.id),
            _assignment(fac1.id, b2.id),
            _assignment(fac2.id, b2.id),
        ]
        result = c.validate(assignments, ctx)
        # b1 has single coverage (fac1) -> 25.0
        # fac2 is n1_vulnerable and has 1 assignment -> 1 * 25.0 * 0.5 = 12.5
        assert result.penalty == 37.5

    def test_vulnerability_rate_severity(self):
        """Severity based on vulnerability rate."""
        c = N1VulnerabilityConstraint()
        fac = _person(name="Dr. A")
        blocks = [_block() for _ in range(5)]
        ctx = _context(faculty=[fac], blocks=blocks)

        # All 5 blocks single-covered: 5/5 = 100% -> CRITICAL
        assignments = [_assignment(fac.id, b.id) for b in blocks]
        result = c.validate(assignments, ctx)
        assert result.violations[0].severity == "CRITICAL"

    def test_sole_provider_report(self):
        """Faculty who is sole provider for 3+ blocks -> separate violation."""
        c = N1VulnerabilityConstraint()
        fac = _person(name="Dr. Sole")
        blocks = [_block() for _ in range(4)]
        ctx = _context(faculty=[fac], blocks=blocks)

        assignments = [_assignment(fac.id, b.id) for b in blocks]
        result = c.validate(assignments, ctx)
        # Should have both the N-1 vulnerability violation AND sole provider violation
        assert len(result.violations) >= 2
        sole_violation = [
            v for v in result.violations if "sole provider" in v.message.lower()
        ]
        assert len(sole_violation) == 1
        assert "Dr. Sole" in sole_violation[0].message

    def test_sole_provider_high_severity(self):
        """Sole provider for 5+ blocks -> HIGH severity."""
        c = N1VulnerabilityConstraint()
        fac = _person(name="Dr. Overloaded")
        blocks = [_block() for _ in range(6)]
        ctx = _context(faculty=[fac], blocks=blocks)

        assignments = [_assignment(fac.id, b.id) for b in blocks]
        result = c.validate(assignments, ctx)
        sole_violations = [
            v for v in result.violations if "sole provider" in v.message.lower()
        ]
        assert sole_violations[0].severity == "HIGH"

    def test_no_blocks_no_crash(self):
        """Empty blocks list -> no crash."""
        c = N1VulnerabilityConstraint()
        fac = _person(name="Dr. A")
        ctx = _context(faculty=[fac])

        a = _assignment(fac.id, uuid4())
        result = c.validate([a], ctx)
        # Single coverage on unknown block - penalty still accumulates
        assert result.satisfied is True
