"""Tests for inpatient constraints (pure logic, no DB required)."""

from datetime import date, timedelta
from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.scheduling.constraints.base import (
    ConstraintPriority,
    ConstraintType,
    SchedulingContext,
)
from app.scheduling.constraints.inpatient import (
    FMITResidentClinicDayConstraint,
    ResidentInpatientHeadcountConstraint,
)


# ==================== Helpers ====================


def _person(pid=None, name="Resident", pgy_level=None):
    """Build a mock person."""
    ns = SimpleNamespace(id=pid or uuid4(), name=name)
    if pgy_level is not None:
        ns.pgy_level = pgy_level
    return ns


def _block(bid=None, block_date=None, time_of_day="AM"):
    """Build a mock block."""
    return SimpleNamespace(
        id=bid or uuid4(),
        date=block_date or date(2025, 3, 3),
        time_of_day=time_of_day,
    )


def _template(
    tid=None,
    name="Template",
    abbreviation=None,
    first_half_component_id=None,
    second_half_component_id=None,
):
    """Build a mock template."""
    ns = SimpleNamespace(id=tid or uuid4(), name=name)
    if abbreviation is not None:
        ns.abbreviation = abbreviation
    if first_half_component_id is not None:
        ns.first_half_component_id = first_half_component_id
    if second_half_component_id is not None:
        ns.second_half_component_id = second_half_component_id
    return ns


def _assignment(person_id, block_id, rotation_template_id=None):
    """Build a mock assignment."""
    return SimpleNamespace(
        person_id=person_id,
        block_id=block_id,
        rotation_template_id=rotation_template_id,
    )


def _context(
    residents=None, blocks=None, faculty=None, templates=None, start_date=None
):
    """Build a SchedulingContext."""
    ctx = SchedulingContext(
        residents=residents or [],
        faculty=faculty or [],
        blocks=blocks or [],
        templates=templates or [],
    )
    if start_date is not None:
        ctx.start_date = start_date
    return ctx


# ==================== ResidentInpatientHeadcountConstraint Init ====================


class TestHeadcountInit:
    """Test initialization."""

    def test_name(self):
        c = ResidentInpatientHeadcountConstraint()
        assert c.name == "ResidentInpatientHeadcount"

    def test_type(self):
        c = ResidentInpatientHeadcountConstraint()
        assert c.constraint_type == ConstraintType.CAPACITY

    def test_priority(self):
        c = ResidentInpatientHeadcountConstraint()
        assert c.priority == ConstraintPriority.CRITICAL

    def test_constants(self):
        assert ResidentInpatientHeadcountConstraint.FMIT_PER_PGY_PER_BLOCK == 1
        assert ResidentInpatientHeadcountConstraint.NF_CONCURRENT_MAX == 1


# ==================== _get_week_number Tests ====================


class TestGetWeekNumber:
    """Test _get_week_number helper."""

    def test_no_start_date(self):
        c = ResidentInpatientHeadcountConstraint()
        assert c._get_week_number(date(2025, 3, 3), None) == 1

    def test_same_day_week_1(self):
        c = ResidentInpatientHeadcountConstraint()
        assert c._get_week_number(date(2025, 3, 3), date(2025, 3, 3)) == 1

    def test_day_6_week_1(self):
        c = ResidentInpatientHeadcountConstraint()
        assert c._get_week_number(date(2025, 3, 9), date(2025, 3, 3)) == 1

    def test_day_7_week_2(self):
        c = ResidentInpatientHeadcountConstraint()
        assert c._get_week_number(date(2025, 3, 10), date(2025, 3, 3)) == 2

    def test_day_21_week_4(self):
        c = ResidentInpatientHeadcountConstraint()
        assert c._get_week_number(date(2025, 3, 24), date(2025, 3, 3)) == 4


# ==================== _get_fmit_template_ids Tests ====================


class TestGetFmitTemplateIds:
    """Test _get_fmit_template_ids helper."""

    def test_finds_fmit_template(self):
        c = ResidentInpatientHeadcountConstraint()
        t = _template(name="FMIT")
        ctx = _context(templates=[t])
        assert t.id in c._get_fmit_template_ids(ctx)

    def test_finds_fmit_case_insensitive(self):
        c = ResidentInpatientHeadcountConstraint()
        t = _template(name="fmit rotation")
        ctx = _context(templates=[t])
        assert t.id in c._get_fmit_template_ids(ctx)

    def test_excludes_night_float_fmit(self):
        c = ResidentInpatientHeadcountConstraint()
        t = _template(name="FMIT Night Float")
        ctx = _context(templates=[t])
        assert len(c._get_fmit_template_ids(ctx)) == 0

    def test_excludes_non_fmit(self):
        c = ResidentInpatientHeadcountConstraint()
        t = _template(name="Clinic")
        ctx = _context(templates=[t])
        assert len(c._get_fmit_template_ids(ctx)) == 0

    def test_empty_templates(self):
        c = ResidentInpatientHeadcountConstraint()
        ctx = _context(templates=[])
        assert len(c._get_fmit_template_ids(ctx)) == 0


# ==================== _is_combo_template / _is_nf_base_template Tests ====================


class TestTemplateClassification:
    """Test combo and NF template classification."""

    def test_is_combo_first_half(self):
        c = ResidentInpatientHeadcountConstraint()
        t = _template(name="Combo", first_half_component_id=uuid4())
        assert c._is_combo_template(t) is True

    def test_is_combo_second_half(self):
        c = ResidentInpatientHeadcountConstraint()
        t = _template(name="Combo", second_half_component_id=uuid4())
        assert c._is_combo_template(t) is True

    def test_not_combo(self):
        c = ResidentInpatientHeadcountConstraint()
        t = _template(name="Regular")
        assert c._is_combo_template(t) is False

    def test_nf_base_by_name(self):
        c = ResidentInpatientHeadcountConstraint()
        t = _template(name="Night Float")
        assert c._is_nf_base_template(t) is True

    def test_nf_base_by_abbreviation(self):
        c = ResidentInpatientHeadcountConstraint()
        t = _template(name="Some NF", abbreviation="NF")
        assert c._is_nf_base_template(t) is True

    def test_nf_abbreviation_prefix(self):
        c = ResidentInpatientHeadcountConstraint()
        t = _template(name="NF Endo", abbreviation="NF-ENDO")
        assert c._is_nf_base_template(t) is True

    def test_combo_not_nf_base(self):
        """Combo template is NOT a standalone NF base template."""
        c = ResidentInpatientHeadcountConstraint()
        t = _template(
            name="Night Float Combo",
            first_half_component_id=uuid4(),
        )
        assert c._is_nf_base_template(t) is False

    def test_clinic_not_nf(self):
        c = ResidentInpatientHeadcountConstraint()
        t = _template(name="Clinic")
        assert c._is_nf_base_template(t) is False


# ==================== _get_nf_template_sets Tests ====================


class TestGetNfTemplateSets:
    """Test _get_nf_template_sets helper."""

    def test_finds_standalone_nf(self):
        c = ResidentInpatientHeadcountConstraint()
        nf = _template(name="Night Float")
        ctx = _context(templates=[nf])
        full_nf_ids, combo_week_map = c._get_nf_template_sets(ctx)
        assert nf.id in full_nf_ids
        assert len(combo_week_map) == 0

    def test_finds_combo_with_nf_first_half(self):
        c = ResidentInpatientHeadcountConstraint()
        nf = _template(name="Night Float")
        combo = _template(
            name="NF+Clinic",
            first_half_component_id=nf.id,
        )
        ctx = _context(templates=[nf, combo])
        full_nf_ids, combo_week_map = c._get_nf_template_sets(ctx)
        assert nf.id in full_nf_ids
        assert combo.id in combo_week_map
        assert combo_week_map[combo.id] == {1, 2}

    def test_finds_combo_with_nf_second_half(self):
        c = ResidentInpatientHeadcountConstraint()
        nf = _template(name="Night Float")
        combo = _template(
            name="Clinic+NF",
            second_half_component_id=nf.id,
        )
        ctx = _context(templates=[nf, combo])
        full_nf_ids, combo_week_map = c._get_nf_template_sets(ctx)
        assert combo.id in combo_week_map
        assert combo_week_map[combo.id] == {3, 4}


# ==================== validate Tests ====================


class TestHeadcountValidate:
    """Test ResidentInpatientHeadcountConstraint.validate method."""

    def test_no_assignments_satisfied(self):
        c = ResidentInpatientHeadcountConstraint()
        ctx = _context()
        result = c.validate([], ctx)
        assert result.satisfied is True

    def test_one_fmit_per_pgy_satisfied(self):
        """1 PGY-1 on FMIT per block -> satisfied."""
        c = ResidentInpatientHeadcountConstraint()
        r1 = _person(name="Intern A", pgy_level=1)
        fmit = _template(name="FMIT")
        b1 = _block()
        ctx = _context(residents=[r1], blocks=[b1], templates=[fmit])

        a = _assignment(r1.id, b1.id, rotation_template_id=fmit.id)
        result = c.validate([a], ctx)
        assert result.satisfied is True

    def test_two_fmit_same_pgy_violation(self):
        """2 PGY-1s on FMIT same block -> violation."""
        c = ResidentInpatientHeadcountConstraint()
        r1 = _person(name="Intern A", pgy_level=1)
        r2 = _person(name="Intern B", pgy_level=1)
        fmit = _template(name="FMIT")
        b1 = _block()
        ctx = _context(residents=[r1, r2], blocks=[b1], templates=[fmit])

        assignments = [
            _assignment(r1.id, b1.id, rotation_template_id=fmit.id),
            _assignment(r2.id, b1.id, rotation_template_id=fmit.id),
        ]
        result = c.validate(assignments, ctx)
        assert result.satisfied is False
        assert len(result.violations) == 1
        assert "PGY-1" in result.violations[0].message
        assert "2 FMIT" in result.violations[0].message

    def test_different_pgy_fmit_satisfied(self):
        """1 PGY-1 and 1 PGY-2 on FMIT same block -> satisfied."""
        c = ResidentInpatientHeadcountConstraint()
        r1 = _person(name="Intern", pgy_level=1)
        r2 = _person(name="Second Year", pgy_level=2)
        fmit = _template(name="FMIT")
        b1 = _block()
        ctx = _context(residents=[r1, r2], blocks=[b1], templates=[fmit])

        assignments = [
            _assignment(r1.id, b1.id, rotation_template_id=fmit.id),
            _assignment(r2.id, b1.id, rotation_template_id=fmit.id),
        ]
        result = c.validate(assignments, ctx)
        assert result.satisfied is True

    def test_one_nf_satisfied(self):
        """1 resident on NF -> satisfied."""
        c = ResidentInpatientHeadcountConstraint()
        r1 = _person(name="NF Resident", pgy_level=2)
        nf = _template(name="Night Float", abbreviation="NF")
        b1 = _block()
        ctx = _context(residents=[r1], blocks=[b1], templates=[nf])

        a = _assignment(r1.id, b1.id, rotation_template_id=nf.id)
        result = c.validate([a], ctx)
        assert result.satisfied is True

    def test_two_nf_same_block_violation(self):
        """2 residents on NF same block -> violation."""
        c = ResidentInpatientHeadcountConstraint()
        r1 = _person(name="NF A", pgy_level=2)
        r2 = _person(name="NF B", pgy_level=3)
        nf = _template(name="Night Float", abbreviation="NF")
        b1 = _block()
        ctx = _context(residents=[r1, r2], blocks=[b1], templates=[nf])

        assignments = [
            _assignment(r1.id, b1.id, rotation_template_id=nf.id),
            _assignment(r2.id, b1.id, rotation_template_id=nf.id),
        ]
        result = c.validate(assignments, ctx)
        assert result.satisfied is False
        assert any("Night Float" in v.message for v in result.violations)

    def test_non_fmit_non_nf_satisfied(self):
        """Clinic assignment -> no headcount check."""
        c = ResidentInpatientHeadcountConstraint()
        r1 = _person(name="Resident", pgy_level=1)
        clinic = _template(name="Clinic")
        b1 = _block()
        ctx = _context(residents=[r1], blocks=[b1], templates=[clinic])

        a = _assignment(r1.id, b1.id, rotation_template_id=clinic.id)
        result = c.validate([a], ctx)
        assert result.satisfied is True

    def test_fmit_violation_details(self):
        """Violation details include pgy_level and count."""
        c = ResidentInpatientHeadcountConstraint()
        r1 = _person(name="A", pgy_level=2)
        r2 = _person(name="B", pgy_level=2)
        fmit = _template(name="FMIT")
        b1 = _block()
        ctx = _context(residents=[r1, r2], blocks=[b1], templates=[fmit])

        assignments = [
            _assignment(r1.id, b1.id, rotation_template_id=fmit.id),
            _assignment(r2.id, b1.id, rotation_template_id=fmit.id),
        ]
        result = c.validate(assignments, ctx)
        assert result.violations[0].details["pgy_level"] == 2
        assert result.violations[0].details["count"] == 2


# ==================== FMITResidentClinicDayConstraint ====================


class TestFMITClinicDayInit:
    """Test FMITResidentClinicDayConstraint initialization."""

    def test_name(self):
        c = FMITResidentClinicDayConstraint()
        assert c.name == "FMITResidentClinicDay"

    def test_type(self):
        c = FMITResidentClinicDayConstraint()
        assert c.constraint_type == ConstraintType.ROTATION

    def test_priority(self):
        c = FMITResidentClinicDayConstraint()
        assert c.priority == ConstraintPriority.HIGH

    def test_clinic_days_constants(self):
        days = FMITResidentClinicDayConstraint.FMIT_CLINIC_DAYS
        assert days[1] == {"weekday": 2, "time_of_day": "AM"}  # PGY-1: Wed AM
        assert days[2] == {"weekday": 1, "time_of_day": "PM"}  # PGY-2: Tue PM
        assert days[3] == {"weekday": 0, "time_of_day": "PM"}  # PGY-3: Mon PM

    def test_validate_stub_satisfied(self):
        """Validate is a stub that always returns satisfied."""
        c = FMITResidentClinicDayConstraint()
        ctx = _context()
        result = c.validate([], ctx)
        assert result.satisfied is True
