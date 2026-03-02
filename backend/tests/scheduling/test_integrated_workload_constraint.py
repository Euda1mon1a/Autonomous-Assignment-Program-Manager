"""Tests for integrated workload constraint (pure logic, no DB required)."""

from datetime import date
from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.scheduling.constraints.base import (
    ConstraintPriority,
    ConstraintType,
    SchedulingContext,
)
from app.scheduling.constraints.integrated_workload import (
    ADMIN_WEIGHT,
    ACADEMIC_WEIGHT,
    CALL_WEIGHT,
    CLINIC_WEIGHT,
    FMIT_WEIGHT,
    FacultyWorkload,
    IntegratedWorkloadConstraint,
    calculate_workload_report,
)


# ==================== Helpers ====================


def _person(pid=None, name="Faculty", **kwargs):
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


def _assignment(person_id, block_id, rotation_template_id=None, **kwargs):
    """Build a mock assignment."""
    ns = SimpleNamespace(
        person_id=person_id,
        block_id=block_id,
        rotation_template_id=rotation_template_id,
    )
    for k, v in kwargs.items():
        setattr(ns, k, v)
    return ns


def _context(residents=None, blocks=None, faculty=None, templates=None):
    """Build a SchedulingContext."""
    return SchedulingContext(
        residents=residents or [],
        faculty=faculty or [],
        blocks=blocks or [],
        templates=templates or [],
    )


# ==================== Constants Tests ====================


class TestWorkloadConstants:
    """Test module-level weight constants."""

    def test_call_weight(self):
        assert CALL_WEIGHT == 1.0

    def test_fmit_weight(self):
        assert FMIT_WEIGHT == 3.0

    def test_clinic_weight(self):
        assert CLINIC_WEIGHT == 0.5

    def test_admin_weight(self):
        assert ADMIN_WEIGHT == 0.25

    def test_academic_weight(self):
        assert ACADEMIC_WEIGHT == 0.25


# ==================== FacultyWorkload Tests ====================


class TestFacultyWorkload:
    """Test FacultyWorkload dataclass."""

    def test_default_values(self):
        w = FacultyWorkload(person_id="abc", person_name="Dr. Test")
        assert w.call_count == 0
        assert w.fmit_weeks == 0
        assert w.clinic_halfdays == 0
        assert w.admin_halfdays == 0
        assert w.academic_halfdays == 0

    def test_total_score_all_zero(self):
        w = FacultyWorkload(person_id="abc", person_name="Dr. Test")
        assert w.total_score == 0.0

    def test_total_score_calculation(self):
        w = FacultyWorkload(
            person_id="abc",
            person_name="Dr. Test",
            call_count=2,
            fmit_weeks=1,
            clinic_halfdays=4,
            admin_halfdays=2,
            academic_halfdays=2,
        )
        expected = (
            2 * CALL_WEIGHT
            + 1 * FMIT_WEIGHT
            + 4 * CLINIC_WEIGHT
            + 2 * ADMIN_WEIGHT
            + 2 * ACADEMIC_WEIGHT
        )
        assert w.total_score == expected

    def test_to_dict(self):
        w = FacultyWorkload(
            person_id="abc",
            person_name="Dr. Test",
            call_count=1,
        )
        d = w.to_dict()
        assert d["person_id"] == "abc"
        assert d["person_name"] == "Dr. Test"
        assert d["call_count"] == 1
        assert d["total_score"] == 1.0


# ==================== IntegratedWorkloadConstraint Init ====================


class TestWorkloadInit:
    """Test IntegratedWorkloadConstraint initialization."""

    def test_name(self):
        c = IntegratedWorkloadConstraint()
        assert c.name == "IntegratedWorkload"

    def test_type(self):
        c = IntegratedWorkloadConstraint()
        assert c.constraint_type == ConstraintType.EQUITY

    def test_priority(self):
        c = IntegratedWorkloadConstraint()
        assert c.priority == ConstraintPriority.MEDIUM

    def test_default_weight(self):
        c = IntegratedWorkloadConstraint()
        assert c.weight == 15.0

    def test_custom_weights(self):
        c = IntegratedWorkloadConstraint(
            call_weight=2.0, fmit_weight=5.0, clinic_weight=1.0
        )
        assert c.call_weight == 2.0
        assert c.fmit_weight == 5.0
        assert c.clinic_weight == 1.0

    def test_include_titled_default_false(self):
        c = IntegratedWorkloadConstraint()
        assert c.include_titled_faculty is False


# ==================== _is_eligible_faculty Tests ====================


class TestIsEligibleFaculty:
    """Test _is_eligible_faculty helper."""

    def test_core_faculty_eligible(self):
        c = IntegratedWorkloadConstraint()
        f = _person(name="Dr. Core", faculty_role="core")
        assert c._is_eligible_faculty(f) is True

    def test_pd_excluded(self):
        c = IntegratedWorkloadConstraint()
        f = _person(name="Dr. PD", faculty_role="pd")
        assert c._is_eligible_faculty(f) is False

    def test_apd_excluded(self):
        c = IntegratedWorkloadConstraint()
        f = _person(name="Dr. APD", faculty_role="apd")
        assert c._is_eligible_faculty(f) is False

    def test_oic_excluded(self):
        c = IntegratedWorkloadConstraint()
        f = _person(name="Dr. OIC", faculty_role="oic")
        assert c._is_eligible_faculty(f) is False

    def test_dept_chief_excluded(self):
        c = IntegratedWorkloadConstraint()
        f = _person(name="Dr. Chief", faculty_role="dept_chief")
        assert c._is_eligible_faculty(f) is False

    def test_include_titled_overrides(self):
        c = IntegratedWorkloadConstraint(include_titled_faculty=True)
        f = _person(name="Dr. PD", faculty_role="pd")
        assert c._is_eligible_faculty(f) is True

    def test_no_role_eligible(self):
        c = IntegratedWorkloadConstraint()
        f = _person(name="Dr. NoRole")
        assert c._is_eligible_faculty(f) is True

    def test_title_based_exclusion(self):
        c = IntegratedWorkloadConstraint()
        f = _person(name="Dr. Chief", title="Dept Chief")
        assert c._is_eligible_faculty(f) is False


# ==================== Assignment Classification Tests ====================


class TestAssignmentClassification:
    """Test assignment type classification helpers."""

    def test_is_call_assignment(self):
        c = IntegratedWorkloadConstraint()
        a = _assignment(uuid4(), uuid4(), call_type="overnight")
        assert c._is_call_assignment(a) is True

    def test_is_not_call_assignment(self):
        c = IntegratedWorkloadConstraint()
        a = _assignment(uuid4(), uuid4())
        assert c._is_call_assignment(a) is False

    def test_is_fmit_assignment(self):
        c = IntegratedWorkloadConstraint()
        fmit = _template(name="FMIT")
        ctx = _context(templates=[fmit])
        a = _assignment(uuid4(), uuid4(), rotation_template_id=fmit.id)
        assert c._is_fmit_assignment(a, ctx) is True

    def test_is_not_fmit_assignment(self):
        c = IntegratedWorkloadConstraint()
        clinic = _template(name="Clinic")
        ctx = _context(templates=[clinic])
        a = _assignment(uuid4(), uuid4(), rotation_template_id=clinic.id)
        assert c._is_fmit_assignment(a, ctx) is False

    def test_is_clinic_assignment(self):
        c = IntegratedWorkloadConstraint()
        clinic = _template(name="Clinic", rotation_type="outpatient")
        ctx = _context(templates=[clinic])
        a = _assignment(uuid4(), uuid4(), rotation_template_id=clinic.id)
        assert c._is_clinic_assignment(a, ctx) is True

    def test_is_not_clinic_assignment(self):
        c = IntegratedWorkloadConstraint()
        fmit = _template(name="FMIT", rotation_type="inpatient")
        ctx = _context(templates=[fmit])
        a = _assignment(uuid4(), uuid4(), rotation_template_id=fmit.id)
        assert c._is_clinic_assignment(a, ctx) is False

    def test_is_admin_assignment_gme(self):
        c = IntegratedWorkloadConstraint()
        gme = _template(name="GME Admin")
        ctx = _context(templates=[gme])
        a = _assignment(uuid4(), uuid4(), rotation_template_id=gme.id)
        assert c._is_admin_assignment(a, ctx) is True

    def test_is_admin_assignment_dfm(self):
        c = IntegratedWorkloadConstraint()
        dfm = _template(name="DFM Meeting")
        ctx = _context(templates=[dfm])
        a = _assignment(uuid4(), uuid4(), rotation_template_id=dfm.id)
        assert c._is_admin_assignment(a, ctx) is True

    def test_is_admin_by_rotation_type(self):
        c = IntegratedWorkloadConstraint()
        admin = _template(name="Admin", rotation_type="admin")
        ctx = _context(templates=[admin])
        a = _assignment(uuid4(), uuid4(), rotation_template_id=admin.id)
        assert c._is_admin_assignment(a, ctx) is True

    def test_is_academic_assignment_lec(self):
        c = IntegratedWorkloadConstraint()
        lec = _template(name="LEC")
        ctx = _context(templates=[lec])
        a = _assignment(uuid4(), uuid4(), rotation_template_id=lec.id)
        assert c._is_academic_assignment(a, ctx) is True

    def test_is_academic_by_rotation_type(self):
        c = IntegratedWorkloadConstraint()
        t = _template(name="Education", rotation_type="lecture")
        ctx = _context(templates=[t])
        a = _assignment(uuid4(), uuid4(), rotation_template_id=t.id)
        assert c._is_academic_assignment(a, ctx) is True

    def test_is_academic_by_category(self):
        c = IntegratedWorkloadConstraint()
        t = _template(name="Advise", template_category="educational")
        ctx = _context(templates=[t])
        a = _assignment(uuid4(), uuid4(), rotation_template_id=t.id)
        assert c._is_academic_assignment(a, ctx) is True

    def test_no_rotation_template_id(self):
        """Assignment without rotation_template_id -> False for all types."""
        c = IntegratedWorkloadConstraint()
        ctx = _context()
        a = SimpleNamespace(person_id=uuid4(), block_id=uuid4())
        assert c._is_fmit_assignment(a, ctx) is False
        assert c._is_clinic_assignment(a, ctx) is False
        assert c._is_admin_assignment(a, ctx) is False
        assert c._is_academic_assignment(a, ctx) is False


# ==================== validate Tests ====================


class TestWorkloadValidate:
    """Test IntegratedWorkloadConstraint.validate method."""

    def test_no_eligible_faculty_satisfied(self):
        c = IntegratedWorkloadConstraint()
        ctx = _context()
        result = c.validate([], ctx)
        assert result.satisfied is True
        assert result.penalty == 0.0

    def test_validate_with_eligible_faculty_raises_type_error(self):
        """Bug: ConstraintResult doesn't accept 'details' kwarg.

        validate() passes details= to ConstraintResult on line 521, but
        ConstraintResult.__init__ doesn't support that parameter. This
        causes TypeError whenever eligible_ids is non-empty.
        """
        c = IntegratedWorkloadConstraint()
        fac = _person(name="Dr. A", faculty_role="core")
        ctx = _context(faculty=[fac])
        with pytest.raises(TypeError, match="details"):
            c.validate([], ctx)


# ==================== calculate_workload_report Tests ====================


class TestCalculateWorkloadReport:
    """Test convenience function.

    Note: calculate_workload_report calls validate which hits the
    ConstraintResult 'details' bug when eligible faculty exist.
    """

    def test_no_faculty_raises_attribute_error(self):
        """Bug: calculate_workload_report accesses result.details which
        doesn't exist on ConstraintResult, even on the no-faculty path."""
        ctx = _context()
        with pytest.raises(AttributeError, match="details"):
            calculate_workload_report([], ctx)

    def test_with_eligible_faculty_raises_type_error(self):
        """Bug propagates from validate."""
        fac = _person(name="Dr. A", faculty_role="core")
        ctx = _context(faculty=[fac])
        with pytest.raises(TypeError, match="details"):
            calculate_workload_report([], ctx)


# ==================== add_to_cpsat Solver Variable Tests ====================


class TestAddToCpsat:
    """Test that add_to_cpsat uses correct index dicts after ARCH-001 fix.

    Before the fix, add_to_cpsat used context.resident_idx for faculty lookups,
    which always returned None (faculty UUIDs never appear in resident_idx),
    making the entire method inert dead code.
    """

    def test_creates_workload_vars_with_correct_indices(self):
        """With call_eligible_faculty_idx populated, workload vars are created."""
        from ortools.sat.python import cp_model

        model = cp_model.CpModel()

        fac_a = _person(name="Dr. A", faculty_role="core")
        fac_b = _person(name="Dr. B", faculty_role="core")
        block = _block()

        ctx = _context(faculty=[fac_a, fac_b], blocks=[block])
        # Context builds faculty_idx and block_idx automatically
        assert fac_a.id in ctx.faculty_idx
        assert fac_b.id in ctx.faculty_idx

        # Populate call_eligible_faculty_idx (mimics engine.py)
        ctx.call_eligible_faculty = [fac_a, fac_b]
        ctx.call_eligible_faculty_idx = {fac_a.id: 0, fac_b.id: 1}

        b_i = ctx.block_idx[block.id]

        # Create call variables matching solver's keying scheme
        call_a = model.NewBoolVar("call_0_0")
        call_b = model.NewBoolVar("call_1_0")
        call_vars = {
            (0, b_i, "overnight"): call_a,
            (1, b_i, "overnight"): call_b,
        }

        variables = {"call_assignments": call_vars, "objective_terms": []}

        constraint = IntegratedWorkloadConstraint()
        constraint.add_to_cpsat(model, variables, ctx)

        # Verify objective terms were added (constraint is active)
        assert len(variables["objective_terms"]) == 1, (
            "Expected 1 objective term (max_workload) but got "
            f"{len(variables['objective_terms'])}. Constraint may be inert."
        )

    def test_no_faculty_is_noop(self):
        """No faculty -> no objective terms added."""
        from ortools.sat.python import cp_model

        model = cp_model.CpModel()
        ctx = _context()
        variables = {"call_assignments": {}, "objective_terms": []}

        constraint = IntegratedWorkloadConstraint()
        constraint.add_to_cpsat(model, variables, ctx)

        assert len(variables["objective_terms"]) == 0

    def test_titled_faculty_excluded_by_default(self):
        """PD/APD faculty are excluded from workload balancing by default."""
        from ortools.sat.python import cp_model

        model = cp_model.CpModel()

        fac_pd = _person(name="Dr. PD", faculty_role="pd")
        block = _block()

        ctx = _context(faculty=[fac_pd], blocks=[block])
        ctx.call_eligible_faculty = [fac_pd]
        ctx.call_eligible_faculty_idx = {fac_pd.id: 0}

        variables = {"call_assignments": {}, "objective_terms": []}

        constraint = IntegratedWorkloadConstraint()
        constraint.add_to_cpsat(model, variables, ctx)

        # PD is excluded, so no workload vars created
        assert len(variables["objective_terms"]) == 0

    def test_uses_faculty_assignments_not_resident_assignments(self):
        """Constraint reads faculty_assignments, not assignments (resident vars)."""
        from ortools.sat.python import cp_model

        model = cp_model.CpModel()

        fac = _person(name="Dr. A", faculty_role="core")
        block = _block()

        ctx = _context(faculty=[fac], blocks=[block])
        ctx.call_eligible_faculty = [fac]
        ctx.call_eligible_faculty_idx = {fac.id: 0}

        b_i = ctx.block_idx[block.id]
        fa_i = ctx.faculty_idx[fac.id]

        # Create a faculty_assignment var (keyed by faculty_idx)
        fac_assign = model.NewBoolVar("fac_assign_0_0")

        variables = {
            "call_assignments": {},
            "faculty_assignments": {(fa_i, b_i): fac_assign},
            "assignments": {},  # resident vars (should NOT be read)
            "objective_terms": [],
        }

        constraint = IntegratedWorkloadConstraint()
        constraint.add_to_cpsat(model, variables, ctx)

        # Constraint should be active because faculty_assignments has data
        assert len(variables["objective_terms"]) == 1
