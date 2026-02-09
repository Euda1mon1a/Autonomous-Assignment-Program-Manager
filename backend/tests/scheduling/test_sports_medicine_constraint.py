"""Tests for Sports Medicine constraint (pure logic, no DB required)."""

from datetime import date
from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.scheduling.constraints.base import (
    ConstraintPriority,
    ConstraintType,
    SchedulingContext,
)
from app.scheduling.constraints.sports_medicine import (
    SMResidentFacultyAlignmentConstraint,
)


# ==================== Helpers ====================


def _person(pid=None, name="Person", **kwargs):
    """Build a mock person with optional attributes."""
    ns = SimpleNamespace(id=pid or uuid4(), name=name)
    for k, v in kwargs.items():
        setattr(ns, k, v)
    return ns


def _block(bid=None, block_date=None, time_of_day="AM"):
    """Build a mock block."""
    return SimpleNamespace(
        id=bid or uuid4(),
        date=block_date or date(2025, 3, 3),
        time_of_day=time_of_day,
    )


def _template(tid=None, name="Template", **kwargs):
    """Build a mock template with optional attributes."""
    ns = SimpleNamespace(id=tid or uuid4(), name=name)
    for k, v in kwargs.items():
        setattr(ns, k, v)
    return ns


def _assignment(person_id, block_id, rotation_template_id=None):
    """Build a mock assignment."""
    return SimpleNamespace(
        person_id=person_id,
        block_id=block_id,
        rotation_template_id=rotation_template_id,
    )


def _context(
    residents=None,
    blocks=None,
    faculty=None,
    templates=None,
    existing_assignments=None,
):
    """Build a SchedulingContext."""
    ctx = SchedulingContext(
        residents=residents or [],
        faculty=faculty or [],
        blocks=blocks or [],
        templates=templates or [],
    )
    if existing_assignments is not None:
        ctx.existing_assignments = existing_assignments
    return ctx


# ==================== Init Tests ====================


class TestSMAlignmentInit:
    """Test SMResidentFacultyAlignmentConstraint initialization."""

    def test_name(self):
        c = SMResidentFacultyAlignmentConstraint()
        assert c.name == "SMResidentFacultyAlignment"

    def test_type(self):
        c = SMResidentFacultyAlignmentConstraint()
        assert c.constraint_type == ConstraintType.SPECIALTY

    def test_priority(self):
        c = SMResidentFacultyAlignmentConstraint()
        assert c.priority == ConstraintPriority.HIGH


# ==================== _get_sm_template_ids Tests ====================


class TestGetSMTemplateIds:
    """Test _get_sm_template_ids helper."""

    def test_by_requires_specialty(self):
        c = SMResidentFacultyAlignmentConstraint()
        t = _template(name="SM Clinic", requires_specialty="Sports Medicine")
        ctx = _context(templates=[t])
        assert t.id in c._get_sm_template_ids(ctx)

    def test_by_name_sports_medicine(self):
        c = SMResidentFacultyAlignmentConstraint()
        t = _template(name="Sports Medicine")
        ctx = _context(templates=[t])
        assert t.id in c._get_sm_template_ids(ctx)

    def test_by_name_sm(self):
        c = SMResidentFacultyAlignmentConstraint()
        t = _template(name="SM")
        ctx = _context(templates=[t])
        assert t.id in c._get_sm_template_ids(ctx)

    def test_case_insensitive(self):
        c = SMResidentFacultyAlignmentConstraint()
        t = _template(name="sports medicine clinic")
        ctx = _context(templates=[t])
        assert t.id in c._get_sm_template_ids(ctx)

    def test_non_sm_template(self):
        c = SMResidentFacultyAlignmentConstraint()
        t = _template(name="Clinic")
        ctx = _context(templates=[t])
        assert len(c._get_sm_template_ids(ctx)) == 0

    def test_empty_templates(self):
        c = SMResidentFacultyAlignmentConstraint()
        ctx = _context(templates=[])
        assert len(c._get_sm_template_ids(ctx)) == 0


# ==================== _get_sm_faculty Tests ====================


class TestGetSMFaculty:
    """Test _get_sm_faculty helper."""

    def test_by_is_sports_medicine_flag(self):
        c = SMResidentFacultyAlignmentConstraint()
        f = _person(name="Dr. SM", is_sports_medicine=True)
        ctx = _context(faculty=[f])
        result = c._get_sm_faculty(ctx)
        assert len(result) == 1
        assert result[0].id == f.id

    def test_by_faculty_role(self):
        c = SMResidentFacultyAlignmentConstraint()
        f = _person(name="Dr. SM", faculty_role="sports_med")
        ctx = _context(faculty=[f])
        result = c._get_sm_faculty(ctx)
        assert len(result) == 1

    def test_by_specialties(self):
        c = SMResidentFacultyAlignmentConstraint()
        f = _person(name="Dr. SM", specialties=["Sports Medicine", "FM"])
        ctx = _context(faculty=[f])
        result = c._get_sm_faculty(ctx)
        assert len(result) == 1

    def test_non_sm_faculty(self):
        c = SMResidentFacultyAlignmentConstraint()
        f = _person(name="Dr. FM")
        ctx = _context(faculty=[f])
        result = c._get_sm_faculty(ctx)
        assert len(result) == 0

    def test_empty_faculty(self):
        c = SMResidentFacultyAlignmentConstraint()
        ctx = _context(faculty=[])
        result = c._get_sm_faculty(ctx)
        assert len(result) == 0


# ==================== _get_sm_rotation_residents Tests ====================


class TestGetSMRotationResidents:
    """Test _get_sm_rotation_residents helper."""

    def test_finds_residents_with_sm_assignments(self):
        c = SMResidentFacultyAlignmentConstraint()
        res = _person(name="SM Resident")
        sm = _template(name="Sports Medicine")
        existing = _assignment(res.id, uuid4(), rotation_template_id=sm.id)
        ctx = _context(
            residents=[res],
            templates=[sm],
            existing_assignments=[existing],
        )
        result = c._get_sm_rotation_residents(ctx)
        assert len(result) == 1
        assert result[0].id == res.id

    def test_no_sm_templates_empty(self):
        c = SMResidentFacultyAlignmentConstraint()
        ctx = _context(templates=[_template(name="Clinic")])
        result = c._get_sm_rotation_residents(ctx)
        assert len(result) == 0

    def test_no_existing_assignments_empty(self):
        c = SMResidentFacultyAlignmentConstraint()
        sm = _template(name="Sports Medicine")
        res = _person(name="Resident")
        ctx = _context(
            residents=[res],
            templates=[sm],
            existing_assignments=[],
        )
        result = c._get_sm_rotation_residents(ctx)
        assert len(result) == 0


# ==================== validate Tests ====================


class TestSMAlignmentValidate:
    """Test validate method."""

    def test_no_sm_templates_satisfied(self):
        c = SMResidentFacultyAlignmentConstraint()
        ctx = _context(templates=[_template(name="Clinic")])
        result = c.validate([], ctx)
        assert result.satisfied is True

    def test_no_assignments_satisfied(self):
        c = SMResidentFacultyAlignmentConstraint()
        sm = _template(name="Sports Medicine")
        ctx = _context(templates=[sm])
        result = c.validate([], ctx)
        assert result.satisfied is True

    def test_sm_resident_with_faculty_satisfied(self):
        """SM resident + SM faculty on same block -> satisfied."""
        c = SMResidentFacultyAlignmentConstraint()
        res = _person(name="SM Resident")
        fac = _person(name="Dr. SM", is_sports_medicine=True)
        sm = _template(name="Sports Medicine")
        b1 = _block()

        existing = _assignment(res.id, b1.id, rotation_template_id=sm.id)
        ctx = _context(
            residents=[res],
            faculty=[fac],
            blocks=[b1],
            templates=[sm],
            existing_assignments=[existing],
        )

        assignments = [
            _assignment(res.id, b1.id, rotation_template_id=sm.id),
            _assignment(fac.id, b1.id, rotation_template_id=sm.id),
        ]
        result = c.validate(assignments, ctx)
        assert result.satisfied is True

    def test_sm_resident_without_faculty_violation(self):
        """SM resident without SM faculty on same block -> violation."""
        c = SMResidentFacultyAlignmentConstraint()
        res = _person(name="SM Resident")
        fac = _person(name="Dr. SM", is_sports_medicine=True)
        sm = _template(name="Sports Medicine")
        b1 = _block()

        existing = _assignment(res.id, b1.id, rotation_template_id=sm.id)
        ctx = _context(
            residents=[res],
            faculty=[fac],
            blocks=[b1],
            templates=[sm],
            existing_assignments=[existing],
        )

        # Only resident assignment, no faculty
        assignments = [
            _assignment(res.id, b1.id, rotation_template_id=sm.id),
        ]
        result = c.validate(assignments, ctx)
        assert result.satisfied is False
        assert len(result.violations) == 1
        assert "without SM faculty" in result.violations[0].message
        assert result.violations[0].severity == "HIGH"

    def test_non_sm_assignment_not_checked(self):
        """Regular clinic assignment -> no SM check."""
        c = SMResidentFacultyAlignmentConstraint()
        res = _person(name="Resident")
        sm = _template(name="Sports Medicine")
        clinic = _template(name="Clinic")
        b1 = _block()

        ctx = _context(
            residents=[res],
            blocks=[b1],
            templates=[sm, clinic],
        )

        a = _assignment(res.id, b1.id, rotation_template_id=clinic.id)
        result = c.validate([a], ctx)
        assert result.satisfied is True

    def test_violation_details(self):
        """Violation includes template name and date."""
        c = SMResidentFacultyAlignmentConstraint()
        res = _person(name="SM Resident")
        fac = _person(name="Dr. SM", is_sports_medicine=True)
        sm = _template(name="Sports Medicine")
        b1 = _block(block_date=date(2025, 3, 5))

        existing = _assignment(res.id, b1.id, rotation_template_id=sm.id)
        ctx = _context(
            residents=[res],
            faculty=[fac],
            blocks=[b1],
            templates=[sm],
            existing_assignments=[existing],
        )

        assignments = [_assignment(res.id, b1.id, rotation_template_id=sm.id)]
        result = c.validate(assignments, ctx)
        assert result.violations[0].details["template"] == "Sports Medicine"
        assert result.violations[0].details["date"] == "2025-03-05"

    def test_multiple_residents_without_faculty(self):
        """Two SM residents without faculty -> two violations."""
        c = SMResidentFacultyAlignmentConstraint()
        res1 = _person(name="SM Res 1")
        res2 = _person(name="SM Res 2")
        fac = _person(name="Dr. SM", is_sports_medicine=True)
        sm = _template(name="Sports Medicine")
        b1 = _block()

        existing = [
            _assignment(res1.id, b1.id, rotation_template_id=sm.id),
            _assignment(res2.id, b1.id, rotation_template_id=sm.id),
        ]
        ctx = _context(
            residents=[res1, res2],
            faculty=[fac],
            blocks=[b1],
            templates=[sm],
            existing_assignments=existing,
        )

        assignments = [
            _assignment(res1.id, b1.id, rotation_template_id=sm.id),
            _assignment(res2.id, b1.id, rotation_template_id=sm.id),
        ]
        result = c.validate(assignments, ctx)
        assert result.satisfied is False
        assert len(result.violations) == 2
