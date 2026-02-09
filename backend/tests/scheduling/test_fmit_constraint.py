"""Tests for FMIT constraints (pure logic, no DB required)."""

from datetime import date, timedelta
from types import SimpleNamespace
from uuid import uuid4

from app.scheduling.constraints.base import (
    ConstraintPriority,
    ConstraintType,
    SchedulingContext,
)
from app.scheduling.constraints.fmit import (
    FMITContinuityTurfConstraint,
    FMITMandatoryCallConstraint,
    FMITStaffingFloorConstraint,
    FMITWeekBlockingConstraint,
    PostFMITRecoveryConstraint,
    PostFMITSundayBlockingConstraint,
    _get_assignment_template,
    _identify_fmit_weeks_from_context,
    _is_fmit_template,
    get_fmit_week_dates,
    is_sun_thurs,
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


def _template(tid=None, name="Template", **kwargs):
    ns = SimpleNamespace(id=tid or uuid4(), name=name)
    for k, v in kwargs.items():
        setattr(ns, k, v)
    return ns


def _assignment(person_id, block_id, rotation_template_id=None, **kwargs):
    ns = SimpleNamespace(
        person_id=person_id,
        block_id=block_id,
        rotation_template_id=rotation_template_id,
    )
    for k, v in kwargs.items():
        setattr(ns, k, v)
    return ns


def _fmit_template(tid=None, name="FMIT"):
    """Build an FMIT rotation template."""
    return _template(tid=tid, name=name, rotation_type="inpatient")


def _context(faculty=None, blocks=None, templates=None, **kwargs):
    ctx = SchedulingContext(
        residents=[],
        faculty=faculty or [],
        blocks=blocks or [],
        templates=templates or [],
    )
    for k, v in kwargs.items():
        setattr(ctx, k, v)
    return ctx


# ==================== get_fmit_week_dates Tests ====================


class TestGetFmitWeekDates:
    """Test get_fmit_week_dates helper function."""

    def test_friday_returns_same_friday(self):
        """Friday is the start of FMIT week."""
        fri = date(2025, 3, 7)  # Friday
        start, end = get_fmit_week_dates(fri)
        assert start == date(2025, 3, 7)
        assert end == date(2025, 3, 13)

    def test_saturday_returns_prev_friday(self):
        sat = date(2025, 3, 8)
        start, end = get_fmit_week_dates(sat)
        assert start == date(2025, 3, 7)
        assert end == date(2025, 3, 13)

    def test_sunday_returns_prev_friday(self):
        sun = date(2025, 3, 9)
        start, end = get_fmit_week_dates(sun)
        assert start == date(2025, 3, 7)
        assert end == date(2025, 3, 13)

    def test_monday_returns_prev_friday(self):
        mon = date(2025, 3, 10)
        start, end = get_fmit_week_dates(mon)
        assert start == date(2025, 3, 7)
        assert end == date(2025, 3, 13)

    def test_thursday_returns_prev_friday(self):
        thu = date(2025, 3, 13)
        start, end = get_fmit_week_dates(thu)
        assert start == date(2025, 3, 7)
        assert end == date(2025, 3, 13)

    def test_wednesday_returns_prev_friday(self):
        wed = date(2025, 3, 12)
        start, end = get_fmit_week_dates(wed)
        assert start == date(2025, 3, 7)
        assert end == date(2025, 3, 13)

    def test_end_is_always_thursday(self):
        """End date is always Thursday (start + 6 days)."""
        for d in range(7):
            test_date = date(2025, 3, 7) + timedelta(days=d)
            _, end = get_fmit_week_dates(test_date)
            assert end.weekday() == 3  # Thursday


# ==================== is_sun_thurs Tests ====================


class TestIsSunThurs:
    """Test is_sun_thurs helper."""

    def test_sunday_true(self):
        assert is_sun_thurs(date(2025, 3, 9)) is True  # Sunday

    def test_monday_true(self):
        assert is_sun_thurs(date(2025, 3, 3)) is True

    def test_tuesday_true(self):
        assert is_sun_thurs(date(2025, 3, 4)) is True

    def test_wednesday_true(self):
        assert is_sun_thurs(date(2025, 3, 5)) is True

    def test_thursday_true(self):
        assert is_sun_thurs(date(2025, 3, 6)) is True

    def test_friday_false(self):
        assert is_sun_thurs(date(2025, 3, 7)) is False

    def test_saturday_false(self):
        assert is_sun_thurs(date(2025, 3, 8)) is False


# ==================== _is_fmit_template Tests ====================


class TestIsFmitTemplate:
    """Test _is_fmit_template helper."""

    def test_fmit_inpatient_true(self):
        t = _fmit_template()
        assert _is_fmit_template(t) is True

    def test_non_inpatient_false(self):
        t = _template(name="FMIT", rotation_type="outpatient")
        assert _is_fmit_template(t) is False

    def test_inpatient_non_fmit_name_false(self):
        t = _template(name="Ward", rotation_type="inpatient")
        assert _is_fmit_template(t) is False

    def test_none_false(self):
        assert _is_fmit_template(None) is False

    def test_abbreviation_match(self):
        t = _template(name="Inpatient", rotation_type="inpatient", abbreviation="FMIT")
        assert _is_fmit_template(t) is True

    def test_display_abbreviation_match(self):
        t = _template(
            name="Teaching",
            rotation_type="inpatient",
            display_abbreviation="FMIT-A",
        )
        assert _is_fmit_template(t) is True

    def test_case_insensitive(self):
        t = _template(name="fmit week", rotation_type="inpatient")
        assert _is_fmit_template(t) is True

    def test_no_rotation_type_false(self):
        t = _template(name="FMIT")  # No rotation_type
        assert _is_fmit_template(t) is False


# ==================== _get_assignment_template Tests ====================


class TestGetAssignmentTemplate:
    """Test _get_assignment_template helper."""

    def test_from_rotation_template_attr(self):
        tmpl = _fmit_template()
        a = SimpleNamespace(
            rotation_template=tmpl,
            rotation_template_id=tmpl.id,
        )
        ctx = _context()
        result = _get_assignment_template(a, ctx)
        assert result is tmpl

    def test_from_context_templates(self):
        tmpl = _fmit_template()
        a = SimpleNamespace(rotation_template_id=tmpl.id)
        ctx = _context(templates=[tmpl])
        result = _get_assignment_template(a, ctx)
        assert result is tmpl

    def test_not_found_returns_none(self):
        a = SimpleNamespace(rotation_template_id=uuid4())
        ctx = _context()
        result = _get_assignment_template(a, ctx)
        assert result is None


# ==================== _identify_fmit_weeks_from_context Tests ====================


class TestIdentifyFmitWeeksFromContext:
    """Test _identify_fmit_weeks_from_context helper."""

    def test_no_existing_assignments(self):
        ctx = _context()
        result = _identify_fmit_weeks_from_context(ctx)
        assert result == {}

    def test_with_fmit_assignment(self):
        fac = _person(name="Dr. A")
        tmpl = _fmit_template()
        # Block on Monday 2025-03-10 -> FMIT week Fri 3/7 to Thu 3/13
        b = _block(block_date=date(2025, 3, 10))
        a = _assignment(fac.id, b.id, rotation_template_id=tmpl.id)
        ctx = _context(faculty=[fac], blocks=[b], templates=[tmpl])
        ctx.existing_assignments = [a]

        result = _identify_fmit_weeks_from_context(ctx)
        assert fac.id in result
        assert (date(2025, 3, 7), date(2025, 3, 13)) in result[fac.id]

    def test_non_fmit_assignment_ignored(self):
        fac = _person(name="Dr. A")
        clinic = _template(name="Clinic", rotation_type="outpatient")
        b = _block(block_date=date(2025, 3, 10))
        a = _assignment(fac.id, b.id, rotation_template_id=clinic.id)
        ctx = _context(faculty=[fac], blocks=[b], templates=[clinic])
        ctx.existing_assignments = [a]

        result = _identify_fmit_weeks_from_context(ctx)
        assert result == {}

    def test_unknown_block_skipped(self):
        fac = _person(name="Dr. A")
        tmpl = _fmit_template()
        a = _assignment(fac.id, uuid4(), rotation_template_id=tmpl.id)
        ctx = _context(faculty=[fac], templates=[tmpl])
        ctx.existing_assignments = [a]

        result = _identify_fmit_weeks_from_context(ctx)
        assert result == {}


# ==================== FMITWeekBlockingConstraint Tests ====================


class TestFMITWeekBlockingInit:
    def test_name(self):
        c = FMITWeekBlockingConstraint()
        assert c.name == "FMITWeekBlocking"

    def test_type(self):
        c = FMITWeekBlockingConstraint()
        assert c.constraint_type == ConstraintType.AVAILABILITY

    def test_priority(self):
        c = FMITWeekBlockingConstraint()
        assert c.priority == ConstraintPriority.CRITICAL


class TestFMITWeekBlockingValidate:
    def test_no_fmit_weeks_satisfied(self):
        c = FMITWeekBlockingConstraint()
        ctx = _context()
        result = c.validate([], ctx)
        assert result.satisfied is True

    def test_clinic_during_fmit_violation(self):
        """Clinic assignment during FMIT week -> CRITICAL violation."""
        c = FMITWeekBlockingConstraint()
        fac = _person(name="Dr. A")
        fmit_tmpl = _fmit_template()
        clinic_tmpl = _template(name="Clinic", rotation_type="outpatient")

        # Block on Monday -> FMIT week Fri 3/7 to Thu 3/13
        fmit_block = _block(block_date=date(2025, 3, 10))
        clinic_block = _block(block_date=date(2025, 3, 11))  # Tuesday in FMIT week

        fmit_assign = _assignment(
            fac.id, fmit_block.id, rotation_template_id=fmit_tmpl.id
        )
        clinic_assign = _assignment(
            fac.id, clinic_block.id, rotation_template_id=clinic_tmpl.id
        )

        ctx = _context(
            faculty=[fac],
            blocks=[fmit_block, clinic_block],
            templates=[fmit_tmpl, clinic_tmpl],
        )
        ctx.existing_assignments = [fmit_assign]

        result = c.validate([clinic_assign], ctx)
        assert result.satisfied is False
        assert len(result.violations) == 1
        assert result.violations[0].severity == "CRITICAL"
        assert "clinic" in result.violations[0].message.lower()

    def test_non_clinic_during_fmit_ok(self):
        """Non-outpatient assignment during FMIT week -> no violation."""
        c = FMITWeekBlockingConstraint()
        fac = _person(name="Dr. A")
        fmit_tmpl = _fmit_template()
        admin_tmpl = _template(name="Admin", rotation_type="admin")

        fmit_block = _block(block_date=date(2025, 3, 10))
        admin_block = _block(block_date=date(2025, 3, 11))

        fmit_assign = _assignment(
            fac.id, fmit_block.id, rotation_template_id=fmit_tmpl.id
        )
        admin_assign = _assignment(
            fac.id, admin_block.id, rotation_template_id=admin_tmpl.id
        )

        ctx = _context(
            faculty=[fac],
            blocks=[fmit_block, admin_block],
            templates=[fmit_tmpl, admin_tmpl],
        )
        ctx.existing_assignments = [fmit_assign]

        result = c.validate([admin_assign], ctx)
        assert result.satisfied is True

    def test_clinic_outside_fmit_week_ok(self):
        """Clinic assignment outside FMIT week -> no violation."""
        c = FMITWeekBlockingConstraint()
        fac = _person(name="Dr. A")
        fmit_tmpl = _fmit_template()
        clinic_tmpl = _template(name="Clinic", rotation_type="outpatient")

        fmit_block = _block(block_date=date(2025, 3, 10))  # FMIT week 3/7-3/13
        clinic_block = _block(block_date=date(2025, 3, 17))  # Next week Monday

        fmit_assign = _assignment(
            fac.id, fmit_block.id, rotation_template_id=fmit_tmpl.id
        )
        clinic_assign = _assignment(
            fac.id, clinic_block.id, rotation_template_id=clinic_tmpl.id
        )

        ctx = _context(
            faculty=[fac],
            blocks=[fmit_block, clinic_block],
            templates=[fmit_tmpl, clinic_tmpl],
        )
        ctx.existing_assignments = [fmit_assign]

        result = c.validate([clinic_assign], ctx)
        assert result.satisfied is True

    def test_unknown_faculty_skipped(self):
        """Assignment for unknown faculty -> skipped."""
        c = FMITWeekBlockingConstraint()
        fac = _person(name="Dr. A")
        fmit_tmpl = _fmit_template()
        clinic_tmpl = _template(name="Clinic", rotation_type="outpatient")

        fmit_block = _block(block_date=date(2025, 3, 10))
        clinic_block = _block(block_date=date(2025, 3, 11))

        fmit_assign = _assignment(
            fac.id, fmit_block.id, rotation_template_id=fmit_tmpl.id
        )
        # Assignment for different (unknown) person
        clinic_assign = _assignment(
            uuid4(), clinic_block.id, rotation_template_id=clinic_tmpl.id
        )

        ctx = _context(
            faculty=[fac],
            blocks=[fmit_block, clinic_block],
            templates=[fmit_tmpl, clinic_tmpl],
        )
        ctx.existing_assignments = [fmit_assign]

        result = c.validate([clinic_assign], ctx)
        assert result.satisfied is True


# ==================== FMITMandatoryCallConstraint Tests ====================


class TestFMITMandatoryCallInit:
    def test_name(self):
        c = FMITMandatoryCallConstraint()
        assert c.name == "FMITMandatoryCall"

    def test_type(self):
        c = FMITMandatoryCallConstraint()
        assert c.constraint_type == ConstraintType.CALL

    def test_priority(self):
        c = FMITMandatoryCallConstraint()
        assert c.priority == ConstraintPriority.CRITICAL


class TestFMITMandatoryCallValidate:
    def test_no_fmit_satisfied(self):
        c = FMITMandatoryCallConstraint()
        ctx = _context()
        result = c.validate([], ctx)
        assert result.satisfied is True

    def test_placeholder_always_satisfied(self):
        """Current implementation is a placeholder that always returns satisfied."""
        c = FMITMandatoryCallConstraint()
        fac = _person(name="Dr. A")
        fmit_tmpl = _fmit_template()
        b = _block(block_date=date(2025, 3, 10))
        fmit_assign = _assignment(fac.id, b.id, rotation_template_id=fmit_tmpl.id)
        ctx = _context(faculty=[fac], blocks=[b], templates=[fmit_tmpl])
        ctx.existing_assignments = [fmit_assign]

        result = c.validate([], ctx)
        assert result.satisfied is True


# ==================== PostFMITRecoveryConstraint Tests ====================


class TestPostFMITRecoveryInit:
    def test_name(self):
        c = PostFMITRecoveryConstraint()
        assert c.name == "PostFMITRecovery"

    def test_type(self):
        c = PostFMITRecoveryConstraint()
        assert c.constraint_type == ConstraintType.AVAILABILITY

    def test_priority(self):
        c = PostFMITRecoveryConstraint()
        assert c.priority == ConstraintPriority.HIGH


class TestPostFMITRecoveryValidate:
    def test_no_fmit_satisfied(self):
        c = PostFMITRecoveryConstraint()
        ctx = _context()
        result = c.validate([], ctx)
        assert result.satisfied is True

    def test_assignment_on_recovery_friday_violation(self):
        """Assignment on the Friday after FMIT -> HIGH violation."""
        c = PostFMITRecoveryConstraint()
        fac = _person(name="Dr. A")
        fmit_tmpl = _fmit_template()

        # FMIT week: Fri 3/7 - Thu 3/13 -> recovery Friday is 3/14
        fmit_block = _block(block_date=date(2025, 3, 10))
        recovery_block = _block(block_date=date(2025, 3, 14))  # Recovery Friday

        fmit_assign = _assignment(
            fac.id, fmit_block.id, rotation_template_id=fmit_tmpl.id
        )
        recovery_assign = _assignment(fac.id, recovery_block.id)

        ctx = _context(
            faculty=[fac],
            blocks=[fmit_block, recovery_block],
            templates=[fmit_tmpl],
        )
        ctx.existing_assignments = [fmit_assign]

        result = c.validate([recovery_assign], ctx)
        assert result.satisfied is False
        assert len(result.violations) == 1
        assert result.violations[0].severity == "HIGH"
        assert "recovery" in result.violations[0].message.lower()

    def test_assignment_day_after_recovery_ok(self):
        """Assignment on Saturday after recovery Friday -> no violation."""
        c = PostFMITRecoveryConstraint()
        fac = _person(name="Dr. A")
        fmit_tmpl = _fmit_template()

        fmit_block = _block(block_date=date(2025, 3, 10))
        sat_block = _block(block_date=date(2025, 3, 15))  # Saturday after recovery

        fmit_assign = _assignment(
            fac.id, fmit_block.id, rotation_template_id=fmit_tmpl.id
        )
        sat_assign = _assignment(fac.id, sat_block.id)

        ctx = _context(
            faculty=[fac],
            blocks=[fmit_block, sat_block],
            templates=[fmit_tmpl],
        )
        ctx.existing_assignments = [fmit_assign]

        result = c.validate([sat_assign], ctx)
        assert result.satisfied is True

    def test_different_faculty_no_violation(self):
        """Recovery Friday assignment for different faculty -> no violation."""
        c = PostFMITRecoveryConstraint()
        fac1 = _person(name="Dr. A")
        fac2 = _person(name="Dr. B")
        fmit_tmpl = _fmit_template()

        fmit_block = _block(block_date=date(2025, 3, 10))
        recovery_block = _block(block_date=date(2025, 3, 14))

        fmit_assign = _assignment(
            fac1.id, fmit_block.id, rotation_template_id=fmit_tmpl.id
        )
        # fac2 assigned on fac1's recovery Friday
        other_assign = _assignment(fac2.id, recovery_block.id)

        ctx = _context(
            faculty=[fac1, fac2],
            blocks=[fmit_block, recovery_block],
            templates=[fmit_tmpl],
        )
        ctx.existing_assignments = [fmit_assign]

        result = c.validate([other_assign], ctx)
        assert result.satisfied is True

    def test_violation_details(self):
        c = PostFMITRecoveryConstraint()
        fac = _person(name="Dr. Smith")
        fmit_tmpl = _fmit_template()

        fmit_block = _block(block_date=date(2025, 3, 10))
        recovery_block = _block(block_date=date(2025, 3, 14))

        fmit_assign = _assignment(
            fac.id, fmit_block.id, rotation_template_id=fmit_tmpl.id
        )
        recovery_assign = _assignment(fac.id, recovery_block.id)

        ctx = _context(
            faculty=[fac],
            blocks=[fmit_block, recovery_block],
            templates=[fmit_tmpl],
        )
        ctx.existing_assignments = [fmit_assign]

        result = c.validate([recovery_assign], ctx)
        v = result.violations[0]
        assert v.details["recovery_date"] == "2025-03-14"
        assert v.person_id == fac.id
        assert v.block_id == recovery_block.id


# ==================== PostFMITSundayBlockingConstraint Tests ====================


class TestPostFMITSundayBlockingInit:
    def test_name(self):
        c = PostFMITSundayBlockingConstraint()
        assert c.name == "PostFMITSundayBlocking"

    def test_type(self):
        c = PostFMITSundayBlockingConstraint()
        assert c.constraint_type == ConstraintType.CALL

    def test_priority(self):
        c = PostFMITSundayBlockingConstraint()
        assert c.priority == ConstraintPriority.HIGH


class TestPostFMITSundayBlockingValidate:
    def test_no_fmit_satisfied(self):
        c = PostFMITSundayBlockingConstraint()
        ctx = _context()
        result = c.validate([], ctx)
        assert result.satisfied is True

    def test_sunday_call_after_fmit_violation(self):
        """Overnight call on Sunday after FMIT -> HIGH violation."""
        c = PostFMITSundayBlockingConstraint()
        fac = _person(name="Dr. A")
        fmit_tmpl = _fmit_template()

        # FMIT week 3/7-3/13, blocked Sunday = 3/13 + 3 = 3/16
        fmit_block = _block(block_date=date(2025, 3, 10))
        sun_block = _block(block_date=date(2025, 3, 16))  # Sunday after FMIT

        fmit_assign = _assignment(
            fac.id, fmit_block.id, rotation_template_id=fmit_tmpl.id
        )
        sun_assign = _assignment(fac.id, sun_block.id, call_type="overnight")

        ctx = _context(
            faculty=[fac],
            blocks=[fmit_block, sun_block],
            templates=[fmit_tmpl],
        )
        ctx.existing_assignments = [fmit_assign]

        result = c.validate([sun_assign], ctx)
        assert result.satisfied is False
        assert len(result.violations) == 1
        assert result.violations[0].severity == "HIGH"
        assert "sunday" in result.violations[0].message.lower()

    def test_non_overnight_on_blocked_sunday_ok(self):
        """Non-overnight call on blocked Sunday -> no violation."""
        c = PostFMITSundayBlockingConstraint()
        fac = _person(name="Dr. A")
        fmit_tmpl = _fmit_template()

        fmit_block = _block(block_date=date(2025, 3, 10))
        sun_block = _block(block_date=date(2025, 3, 16))

        fmit_assign = _assignment(
            fac.id, fmit_block.id, rotation_template_id=fmit_tmpl.id
        )
        sun_assign = _assignment(fac.id, sun_block.id, call_type="backup")

        ctx = _context(
            faculty=[fac],
            blocks=[fmit_block, sun_block],
            templates=[fmit_tmpl],
        )
        ctx.existing_assignments = [fmit_assign]

        result = c.validate([sun_assign], ctx)
        assert result.satisfied is True

    def test_no_call_type_skipped(self):
        """Assignment without call_type -> skipped."""
        c = PostFMITSundayBlockingConstraint()
        fac = _person(name="Dr. A")
        fmit_tmpl = _fmit_template()

        fmit_block = _block(block_date=date(2025, 3, 10))
        sun_block = _block(block_date=date(2025, 3, 16))

        fmit_assign = _assignment(
            fac.id, fmit_block.id, rotation_template_id=fmit_tmpl.id
        )
        sun_assign = SimpleNamespace(
            person_id=fac.id, block_id=sun_block.id
        )  # No call_type

        ctx = _context(
            faculty=[fac],
            blocks=[fmit_block, sun_block],
            templates=[fmit_tmpl],
        )
        ctx.existing_assignments = [fmit_assign]

        result = c.validate([sun_assign], ctx)
        assert result.satisfied is True

    def test_different_sunday_no_violation(self):
        """Overnight call on a different Sunday -> no violation."""
        c = PostFMITSundayBlockingConstraint()
        fac = _person(name="Dr. A")
        fmit_tmpl = _fmit_template()

        fmit_block = _block(block_date=date(2025, 3, 10))
        # FMIT week 3/7-3/13, blocked Sunday = 3/16
        # Use a different Sunday (3/23)
        other_sun = _block(block_date=date(2025, 3, 23))

        fmit_assign = _assignment(
            fac.id, fmit_block.id, rotation_template_id=fmit_tmpl.id
        )
        sun_assign = _assignment(fac.id, other_sun.id, call_type="overnight")

        ctx = _context(
            faculty=[fac],
            blocks=[fmit_block, other_sun],
            templates=[fmit_tmpl],
        )
        ctx.existing_assignments = [fmit_assign]

        result = c.validate([sun_assign], ctx)
        assert result.satisfied is True


# ==================== FMITContinuityTurfConstraint Tests ====================


class TestFMITContinuityTurfInit:
    def test_name(self):
        c = FMITContinuityTurfConstraint()
        assert c.name == "FMITContinuityTurf"

    def test_type(self):
        c = FMITContinuityTurfConstraint()
        assert c.constraint_type == ConstraintType.AVAILABILITY

    def test_priority(self):
        c = FMITContinuityTurfConstraint()
        assert c.priority == ConstraintPriority.HIGH


class TestFMITContinuityTurfValidate:
    def test_normal_satisfied(self):
        """Load level 0 (NORMAL) -> satisfied, no violations."""
        c = FMITContinuityTurfConstraint()
        ctx = _context()
        ctx.load_shedding_level = 0
        result = c.validate([], ctx)
        assert result.satisfied is True
        assert len(result.violations) == 0

    def test_yellow_satisfied(self):
        """Load level 1 (YELLOW) -> satisfied, no violations."""
        c = FMITContinuityTurfConstraint()
        ctx = _context()
        ctx.load_shedding_level = 1
        result = c.validate([], ctx)
        assert result.satisfied is True
        assert len(result.violations) == 0

    def test_orange_warning(self):
        """Load level 2 (ORANGE) -> satisfied with warning violation."""
        c = FMITContinuityTurfConstraint()
        ctx = _context()
        ctx.load_shedding_level = 2
        result = c.validate([], ctx)
        assert result.satisfied is True
        assert len(result.violations) == 1
        assert result.violations[0].severity == "warning"

    def test_red_info(self):
        """Load level 3 (RED) -> satisfied with info violation."""
        c = FMITContinuityTurfConstraint()
        ctx = _context()
        ctx.load_shedding_level = 3
        result = c.validate([], ctx)
        assert result.satisfied is True
        assert len(result.violations) == 1
        assert result.violations[0].severity == "info"

    def test_black_info(self):
        """Load level 4 (BLACK) -> satisfied with info, all continuity to OB."""
        c = FMITContinuityTurfConstraint()
        ctx = _context()
        ctx.load_shedding_level = 4
        result = c.validate([], ctx)
        assert result.satisfied is True
        assert "All continuity to OB" in result.violations[0].message

    def test_default_no_level(self):
        """No load_shedding_level on context -> default to 0 (NORMAL)."""
        c = FMITContinuityTurfConstraint()
        ctx = _context()
        result = c.validate([], ctx)
        assert result.satisfied is True
        assert len(result.violations) == 0


class TestGetTurfPolicy:
    def test_level_0(self):
        c = FMITContinuityTurfConstraint()
        assert "all continuity" in c._get_turf_policy(0).lower()

    def test_level_1(self):
        c = FMITContinuityTurfConstraint()
        assert "yellow" in c._get_turf_policy(1).lower()

    def test_level_2(self):
        c = FMITContinuityTurfConstraint()
        assert "OB acceptable" in c._get_turf_policy(2)

    def test_level_3(self):
        c = FMITContinuityTurfConstraint()
        assert "OB covers" in c._get_turf_policy(3)

    def test_level_4(self):
        c = FMITContinuityTurfConstraint()
        assert "essential" in c._get_turf_policy(4).lower()


# ==================== FMITStaffingFloorConstraint Tests ====================


class TestFMITStaffingFloorInit:
    def test_name(self):
        c = FMITStaffingFloorConstraint()
        assert c.name == "FMITStaffingFloor"

    def test_type(self):
        c = FMITStaffingFloorConstraint()
        assert c.constraint_type == ConstraintType.CAPACITY

    def test_priority(self):
        c = FMITStaffingFloorConstraint()
        assert c.priority == ConstraintPriority.CRITICAL

    def test_minimum_faculty(self):
        assert FMITStaffingFloorConstraint.MINIMUM_FACULTY_FOR_FMIT == 5

    def test_utilization_cap(self):
        assert FMITStaffingFloorConstraint.FMIT_UTILIZATION_CAP == 0.20


class TestFMITStaffingFloorValidate:
    def test_no_fmit_assignments_satisfied(self):
        c = FMITStaffingFloorConstraint()
        faculty = [_person(name=f"Dr. {i}") for i in range(5)]
        clinic = _template(name="Clinic", rotation_type="outpatient")
        b = _block()
        ctx = _context(faculty=faculty, blocks=[b], templates=[clinic])
        a = _assignment(faculty[0].id, b.id, rotation_template_id=clinic.id)
        result = c.validate([a], ctx)
        assert result.satisfied is True

    def test_below_minimum_faculty_violation(self):
        """Fewer than 5 faculty with FMIT assignment -> CRITICAL violation."""
        c = FMITStaffingFloorConstraint()
        faculty = [_person(name=f"Dr. {i}") for i in range(4)]
        fmit_tmpl = _fmit_template()
        b = _block()
        ctx = _context(faculty=faculty, blocks=[b], templates=[fmit_tmpl])
        a = _assignment(faculty[0].id, b.id, rotation_template_id=fmit_tmpl.id)
        result = c.validate([a], ctx)
        assert result.satisfied is False
        assert len(result.violations) == 1
        assert result.violations[0].severity == "CRITICAL"
        assert "minimum" in result.violations[0].message.lower()

    def test_at_minimum_faculty_ok(self):
        """Exactly 5 faculty with 1 FMIT -> OK (cap = max(1, 5*0.2) = 1)."""
        c = FMITStaffingFloorConstraint()
        faculty = [_person(name=f"Dr. {i}") for i in range(5)]
        fmit_tmpl = _fmit_template()
        b = _block(block_date=date(2025, 3, 10))  # Monday
        ctx = _context(faculty=faculty, blocks=[b], templates=[fmit_tmpl])
        a = _assignment(faculty[0].id, b.id, rotation_template_id=fmit_tmpl.id)
        result = c.validate([a], ctx)
        assert result.satisfied is True

    def test_utilization_cap_violation(self):
        """Too many concurrent FMIT -> CRITICAL violation."""
        c = FMITStaffingFloorConstraint()
        faculty = [_person(name=f"Dr. {i}") for i in range(5)]
        fmit_tmpl = _fmit_template()
        # Same week blocks for 2 faculty, but cap = max(1, 5*0.2)=1
        b1 = _block(block_date=date(2025, 3, 10))
        b2 = _block(block_date=date(2025, 3, 11))
        ctx = _context(faculty=faculty, blocks=[b1, b2], templates=[fmit_tmpl])
        assignments = [
            _assignment(faculty[0].id, b1.id, rotation_template_id=fmit_tmpl.id),
            _assignment(faculty[1].id, b2.id, rotation_template_id=fmit_tmpl.id),
        ]
        result = c.validate(assignments, ctx)
        assert result.satisfied is False
        assert any("concurrent" in v.message.lower() for v in result.violations)

    def test_ten_faculty_allows_two_fmit(self):
        """10 faculty -> cap = max(1, 10*0.2)=2, 2 concurrent FMIT is OK."""
        c = FMITStaffingFloorConstraint()
        faculty = [_person(name=f"Dr. {i}") for i in range(10)]
        fmit_tmpl = _fmit_template()
        b1 = _block(block_date=date(2025, 3, 10))
        b2 = _block(block_date=date(2025, 3, 11))
        ctx = _context(faculty=faculty, blocks=[b1, b2], templates=[fmit_tmpl])
        assignments = [
            _assignment(faculty[0].id, b1.id, rotation_template_id=fmit_tmpl.id),
            _assignment(faculty[1].id, b2.id, rotation_template_id=fmit_tmpl.id),
        ]
        result = c.validate(assignments, ctx)
        assert result.satisfied is True


class TestIsFacultyActive:
    def test_always_true(self):
        """Current implementation always returns True."""
        c = FMITStaffingFloorConstraint()
        fac = _person(name="Dr. A")
        assert c._is_faculty_active(fac) is True


class TestGroupFmitByWeek:
    def test_groups_by_fmit_week(self):
        c = FMITStaffingFloorConstraint()
        fac = _person(name="Dr. A")
        fmit_tmpl = _fmit_template()
        # Monday 3/10 -> FMIT week starts Fri 3/7
        b1 = _block(block_date=date(2025, 3, 10))
        # Monday 3/17 -> FMIT week starts Fri 3/14
        b2 = _block(block_date=date(2025, 3, 17))
        ctx = _context(blocks=[b1, b2], templates=[fmit_tmpl])
        assignments = [
            _assignment(fac.id, b1.id, rotation_template_id=fmit_tmpl.id),
            _assignment(fac.id, b2.id, rotation_template_id=fmit_tmpl.id),
        ]
        result = c._group_fmit_by_week(assignments, ctx)
        assert date(2025, 3, 7) in result
        assert date(2025, 3, 14) in result
        assert len(result[date(2025, 3, 7)]) == 1
        assert len(result[date(2025, 3, 14)]) == 1

    def test_unknown_block_skipped(self):
        c = FMITStaffingFloorConstraint()
        fac = _person(name="Dr. A")
        a = _assignment(fac.id, uuid4())
        ctx = _context()
        result = c._group_fmit_by_week([a], ctx)
        assert len(result) == 0
