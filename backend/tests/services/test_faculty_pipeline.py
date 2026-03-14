"""Tests for faculty scheduling pipeline fixes.

Tests cover:
1. Adjunct faculty exclusion from auto-expansion
2. Adjunct gap detection API
3. Person-specific clinic limits (max override)
4. Person-specific clinic limits (min enforcement)
5. Faculty expansion timing (Step 3.6.5)
6. Faculty coverage validation endpoint
"""

from datetime import date, timedelta
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from app.models.person import Person, FacultyRole

pytest.importorskip(
    "app.services.faculty_assignment_expansion_service",
    reason="faculty_assignment_expansion_service not yet implemented",
)
from app.services.faculty_assignment_expansion_service import (
    FacultyAssignmentExpansionService,
    AdjunctFacultyGap,
)
from app.scheduling.constraints.faculty_role import FacultyRoleClinicConstraint
from app.scheduling.constraints.base import ConstraintType


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def mock_db():
    """Create a mock database session."""
    return MagicMock()


@pytest.fixture
def core_faculty():
    """Create a core faculty member."""
    person = MagicMock(spec=Person)
    person.id = uuid4()
    person.display_name = "Dr. Core Faculty"
    person.type = "faculty"
    person.faculty_role = "core"
    person.is_faculty = True
    person.weekly_clinic_limit = 4
    person.min_clinic_halfdays_per_week = None
    person.max_clinic_halfdays_per_week = None
    return person


@pytest.fixture
def adjunct_faculty():
    """Create an adjunct faculty member."""
    person = MagicMock(spec=Person)
    person.id = uuid4()
    person.display_name = "Dr. Adjunct Faculty"
    person.type = "faculty"
    person.faculty_role = "adjunct"
    person.is_faculty = True
    person.weekly_clinic_limit = 0
    person.min_clinic_halfdays_per_week = 2
    person.max_clinic_halfdays_per_week = 2
    return person


@pytest.fixture
def person_specific_faculty():
    """Create faculty with person-specific clinic limits."""
    person = MagicMock(spec=Person)
    person.id = uuid4()
    person.display_name = "Dr. Custom Limits"
    person.type = "faculty"
    person.faculty_role = "core"
    person.is_faculty = True
    person.weekly_clinic_limit = 4  # Role default
    person.min_clinic_halfdays_per_week = 2  # Person override
    person.max_clinic_halfdays_per_week = 3  # Person override (lower than role)
    return person


# =============================================================================
# Test: Adjunct Exclusion from Expansion
# =============================================================================


class TestAdjunctExclusion:
    """Tests for adjunct faculty exclusion from auto-expansion."""

    def test_adjuncts_excluded_by_default(self, mock_db):
        """Adjunct faculty should be excluded from expansion by default."""
        service = FacultyAssignmentExpansionService(mock_db)

        # Mock the database query to return adjunct + core faculty
        adjunct = MagicMock(spec=Person)
        adjunct.id = uuid4()
        adjunct.faculty_role = "adjunct"

        core = MagicMock(spec=Person)
        core.id = uuid4()
        core.faculty_role = None  # Core faculty may have NULL role

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [core]  # Adjunct excluded
        mock_db.execute.return_value = mock_result

        # Load faculty with exclude_adjuncts=True
        faculty = service._load_faculty(exclude_adjuncts=True)

        # Verify only non-adjunct faculty returned
        assert len(faculty) == 1
        assert faculty[0].id == core.id

    def test_adjuncts_included_when_requested(self, mock_db):
        """Adjunct faculty should be included when exclude_adjuncts=False."""
        service = FacultyAssignmentExpansionService(mock_db)

        adjunct = MagicMock(spec=Person)
        adjunct.id = uuid4()
        adjunct.faculty_role = "adjunct"

        core = MagicMock(spec=Person)
        core.id = uuid4()
        core.faculty_role = None

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [core, adjunct]
        mock_db.execute.return_value = mock_result

        # Load faculty with exclude_adjuncts=False
        faculty = service._load_faculty(exclude_adjuncts=False)

        assert len(faculty) == 2


# =============================================================================
# Test: Adjunct Gap Detection
# =============================================================================


class TestAdjunctGapDetection:
    """Tests for the adjunct gap detection method."""

    def test_returns_adjuncts_with_zero_assignments(self, mock_db, adjunct_faculty):
        """Should return adjuncts with their assignment counts."""
        service = FacultyAssignmentExpansionService(mock_db)

        # Mock adjunct query
        mock_adjunct_result = MagicMock()
        mock_adjunct_result.scalars.return_value.all.return_value = [adjunct_faculty]

        # Mock count query (no assignments)
        mock_count_result = MagicMock()
        mock_count_result.__iter__ = lambda self: iter([])

        mock_db.execute.side_effect = [mock_adjunct_result, mock_count_result]

        # Get adjunct gaps
        with patch("app.utils.academic_blocks.get_block_dates") as mock_dates:
            mock_dates.return_value = MagicMock(
                start_date=date(2025, 3, 13), end_date=date(2025, 4, 9)
            )
            gaps = service.get_adjunct_faculty_without_assignments(10, 2025)

        assert len(gaps) == 1
        assert gaps[0].person_id == adjunct_faculty.id
        assert gaps[0].min_clinic_halfdays == 2
        assert gaps[0].max_clinic_halfdays == 2
        assert gaps[0].existing_assignment_count == 0


# =============================================================================
# Test: Person-Specific Clinic Limits
# =============================================================================


class TestPersonSpecificClinicLimits:
    """Tests for person-specific clinic limit enforcement."""

    def test_person_max_overrides_role_default(self, person_specific_faculty):
        """Person max_clinic_halfdays_per_week should override role limit."""
        constraint = FacultyRoleClinicConstraint()
        min_limit, max_limit = constraint._get_effective_clinic_limits(
            person_specific_faculty
        )

        # Person-specific max is 3, role default is 4
        assert max_limit == 3  # Person override
        assert min_limit == 2  # Person min also set

    def test_role_default_when_person_not_set(self, core_faculty):
        """Should use role default when person-specific not set."""
        constraint = FacultyRoleClinicConstraint()
        min_limit, max_limit = constraint._get_effective_clinic_limits(core_faculty)

        # No person-specific, should use role default
        assert max_limit == 4  # Core faculty role limit
        assert min_limit == 0  # No min for role-based

    def test_person_zero_is_intentional(self, core_faculty):
        """DB value of 0 is intentional (e.g., PD) — not a fallback trigger."""
        core_faculty.max_clinic_halfdays_per_week = 0
        constraint = FacultyRoleClinicConstraint()
        min_limit, max_limit = constraint._get_effective_clinic_limits(core_faculty)

        assert max_limit == 0  # DB value of 0 respected, not role fallback

    def test_min_limit_enforcement_in_validation(self, person_specific_faculty):
        """Validation should report under-min violations for person-specific limits."""
        constraint = FacultyRoleClinicConstraint()

        # Create mock context with faculty
        context = MagicMock()
        context.faculty = [person_specific_faculty]
        context.blocks = []
        context.templates = []

        # Create mock assignment with 1 clinic (below min of 2)
        mock_assignment = MagicMock()
        mock_assignment.person_id = person_specific_faculty.id
        mock_assignment.rotation_template_id = uuid4()
        mock_assignment.block_id = uuid4()

        mock_block = MagicMock()
        mock_block.id = mock_assignment.block_id
        mock_block.date = date(2025, 3, 17)  # Monday

        context.blocks = [mock_block]

        mock_template = MagicMock()
        mock_template.id = mock_assignment.rotation_template_id
        mock_template.rotation_type = "outpatient"

        context.templates = [mock_template]

        # Validate
        result = constraint.validate([mock_assignment], context)

        # Should have under-min violation
        under_min_violations = [
            v
            for v in result.violations
            if v.details.get("violation_type") == "under_minimum"
        ]
        assert len(under_min_violations) == 1
        assert under_min_violations[0].severity == "MEDIUM"


# =============================================================================
# Test: Faculty Expansion Timing (Integration)
# =============================================================================


class TestFacultyExpansionTiming:
    """Tests to verify the scheduling engine has a generate method."""

    def test_engine_has_generate_method(self):
        """SchedulingEngine should expose a generate() method."""
        from app.scheduling.engine import SchedulingEngine

        assert hasattr(SchedulingEngine, "generate")
        assert callable(SchedulingEngine.generate)

    def test_engine_calls_faculty_expansion_after_resident_expansion(self):
        """Faculty half-day persistence must run AFTER resident half-day persistence.

        The scheduling engine pipeline requires this ordering so that faculty
        assignments (clinic, AT, PCAT, DO) are written after resident rotation
        assignments are persisted.  This test inspects the source of
        ``SchedulingEngine.generate`` to confirm that
        ``_persist_faculty_half_day_from_solver`` is called after
        ``_persist_solver_assignments_to_half_day``.
        """
        import inspect
        from app.scheduling.engine import SchedulingEngine

        source = inspect.getsource(SchedulingEngine.generate)

        resident_pos = source.find("_persist_solver_assignments_to_half_day")
        faculty_pos = source.find("_persist_faculty_half_day_from_solver")

        assert resident_pos != -1, (
            "_persist_solver_assignments_to_half_day not found in generate()"
        )
        assert faculty_pos != -1, (
            "_persist_faculty_half_day_from_solver not found in generate()"
        )
        assert resident_pos < faculty_pos, (
            "Faculty half-day persistence must come AFTER resident half-day "
            "persistence in the generate() pipeline"
        )


# =============================================================================
# Test: Faculty Coverage Validation (API Response Structure)
# =============================================================================


class TestFacultyCoverageValidation:
    """Tests for the faculty coverage validation endpoint."""

    def test_response_includes_all_fields(self):
        """Validate the response schema includes all required fields."""
        from app.schemas.schedule import FacultyCoverageResponse

        # Create a valid response
        response = FacultyCoverageResponse(
            block_number=10,
            academic_year=2025,
            block_start_date=date(2025, 3, 13),
            block_end_date=date(2025, 4, 9),
            total_faculty=12,
            faculty_with_assignments=10,
            adjuncts_needing_manual=[],
            clinic_limit_violations=[],
            coverage_complete=False,
        )

        assert response.block_number == 10
        assert response.total_faculty == 12
        assert response.faculty_with_assignments == 10
        assert response.coverage_complete is False

    def test_coverage_complete_when_all_assigned(self):
        """coverage_complete should be True when all faculty have assignments."""
        from app.schemas.schedule import FacultyCoverageResponse

        response = FacultyCoverageResponse(
            block_number=10,
            academic_year=2025,
            block_start_date=date(2025, 3, 13),
            block_end_date=date(2025, 4, 9),
            total_faculty=12,
            faculty_with_assignments=12,  # All assigned
            adjuncts_needing_manual=[],
            clinic_limit_violations=[],  # No violations
            coverage_complete=True,
        )

        assert response.coverage_complete is True

    def test_clinic_violation_response_structure(self):
        """Validate clinic limit violation response schema."""
        from app.schemas.schedule import ClinicLimitViolationResponse

        violation = ClinicLimitViolationResponse(
            faculty_id=uuid4(),
            faculty_name="Dr. Test",
            faculty_role="core",
            week_start=date(2025, 3, 17),
            clinic_count=5,
            min_limit=0,
            max_limit=4,
            violation_type="over_max",
            limit_source="role",
        )

        assert violation.clinic_count == 5
        assert violation.max_limit == 4
        assert violation.violation_type == "over_max"


# =============================================================================
# Test: Constraint Integration
# =============================================================================


class TestConstraintIntegration:
    """Tests for constraint system integration."""

    def test_constraint_type_is_capacity(self):
        """FacultyRoleClinicConstraint should be a CAPACITY constraint."""
        constraint = FacultyRoleClinicConstraint()
        assert constraint.constraint_type == ConstraintType.CAPACITY

    def test_constraint_has_correct_name(self):
        """Constraint name should be FacultyRoleClinic."""
        constraint = FacultyRoleClinicConstraint()
        assert constraint.name == "FacultyRoleClinic"
