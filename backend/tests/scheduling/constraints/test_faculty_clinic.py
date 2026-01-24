"""
Tests for Faculty Clinic and AT Constraints.

Session 136: Tests for FacultyClinicCapConstraint and FacultySupervisionConstraint.
"""

from datetime import date
from uuid import uuid4

import pytest

from app.scheduling.constraints.faculty_clinic import (
    FACULTY_CLINIC_CAPS,
    FacultyClinicCapConstraint,
    FacultySupervisionConstraint,
)
from app.scheduling.constraints.base import (
    ConstraintType,
    SchedulingContext,
)


class MockPerson:
    """Mock Person object for testing."""

    def __init__(self, name: str, person_type: str = "faculty", pgy_level: int = 2):
        self.id = uuid4()
        self.name = name
        self.type = person_type
        self.pgy_level = pgy_level


class MockAssignment:
    """Mock assignment for testing."""

    def __init__(
        self,
        person_id,
        assign_date: date,
        time_of_day: str,
        activity_code: str,
        person_type: str = "faculty",
        pgy_level: int = 2,
    ):
        self.person_id = person_id
        self.date = assign_date
        self.time_of_day = time_of_day
        self.activity_code = activity_code
        self.person_type = person_type
        self.pgy_level = pgy_level


class TestFacultyClinicCaps:
    """Tests for FACULTY_CLINIC_CAPS configuration."""

    def test_clinic_caps_defined(self):
        """Verify clinic caps are defined for core faculty."""
        assert "Montgomery" in FACULTY_CLINIC_CAPS
        assert "Kinkennon" in FACULTY_CLINIC_CAPS
        assert "Tagawa" in FACULTY_CLINIC_CAPS

    def test_montgomery_caps(self):
        """Montgomery should have fixed 2 clinic per week."""
        min_c, max_c = FACULTY_CLINIC_CAPS["Montgomery"]
        assert min_c == 2
        assert max_c == 2

    def test_tagawa_no_clinic(self):
        """Tagawa (SM) should have no FM clinic."""
        min_c, max_c = FACULTY_CLINIC_CAPS["Tagawa"]
        assert min_c == 0
        assert max_c == 0

    def test_kinkennon_flexible_caps(self):
        """Kinkennon should have 2-4 clinic per week."""
        min_c, max_c = FACULTY_CLINIC_CAPS["Kinkennon"]
        assert min_c == 2
        assert max_c == 4


class TestFacultyClinicCapConstraint:
    """Tests for FacultyClinicCapConstraint."""

    @pytest.fixture
    def constraint(self):
        """Create constraint instance."""
        return FacultyClinicCapConstraint()

    @pytest.fixture
    def context(self):
        """Create minimal scheduling context."""
        return SchedulingContext(
            residents=[],
            faculty=[MockPerson("Aaron Montgomery")],
            blocks=[],
            templates=[],
            start_date=date(2026, 3, 12),
            end_date=date(2026, 4, 8),
        )

    def test_constraint_type(self, constraint):
        """Constraint should be CAPACITY type."""
        assert constraint.constraint_type == ConstraintType.CAPACITY

    def test_constraint_name(self, constraint):
        """Constraint should have correct name."""
        assert constraint.name == "FacultyClinicCap"

    def test_get_caps_last_name_extraction(self, constraint):
        """Should extract last name and get caps."""
        min_c, max_c = constraint._get_caps("Aaron Montgomery")
        assert min_c == 2
        assert max_c == 2

    def test_get_caps_comma_format(self, constraint):
        """Should handle 'Last, First' format."""
        min_c, max_c = constraint._get_caps("Montgomery, Aaron")
        assert min_c == 2
        assert max_c == 2

    def test_get_caps_unknown_faculty(self, constraint):
        """Unknown faculty should get default caps."""
        min_c, max_c = constraint._get_caps("Unknown Faculty")
        assert min_c == 0
        assert max_c == 4

    def test_validate_no_assignments(self, constraint, context):
        """No violations when no assignments."""
        result = constraint.validate([], context)
        assert result.satisfied

    def test_validate_within_caps(self, constraint, context):
        """No violations when within caps."""
        faculty = context.faculty[0]
        assignments = [
            MockAssignment(faculty.id, date(2026, 3, 12), "AM", "fm_clinic"),
            MockAssignment(faculty.id, date(2026, 3, 12), "PM", "fm_clinic"),
        ]
        result = constraint.validate(assignments, context)
        # Montgomery has max 2, this is exactly 2
        assert result.satisfied

    def test_validate_exceeds_max(self, constraint, context):
        """Violation when exceeding max caps."""
        faculty = context.faculty[0]
        assignments = [
            MockAssignment(faculty.id, date(2026, 3, 12), "AM", "fm_clinic"),
            MockAssignment(faculty.id, date(2026, 3, 12), "PM", "fm_clinic"),
            MockAssignment(faculty.id, date(2026, 3, 13), "AM", "fm_clinic"),
        ]
        result = constraint.validate(assignments, context)
        # Montgomery has max 2, this is 3 = violation
        assert not result.satisfied
        assert len(result.violations) > 0
        assert result.violations[0].severity == "HIGH"


class TestFacultySupervisionConstraint:
    """Tests for FacultySupervisionConstraint (ACGME AT coverage)."""

    @pytest.fixture
    def constraint(self):
        """Create constraint instance."""
        return FacultySupervisionConstraint()

    @pytest.fixture
    def context(self):
        """Create minimal scheduling context."""
        return SchedulingContext(
            residents=[
                MockPerson("Intern 1", "resident", pgy_level=1),
                MockPerson("Intern 2", "resident", pgy_level=1),
            ],
            faculty=[MockPerson("Dr Faculty")],
            blocks=[],
            templates=[],
            start_date=date(2026, 3, 12),
            end_date=date(2026, 4, 8),
        )

    def test_constraint_type(self, constraint):
        """Constraint should be SUPERVISION type."""
        assert constraint.constraint_type == ConstraintType.SUPERVISION

    def test_constraint_priority_critical(self, constraint):
        """ACGME supervision is CRITICAL priority."""
        from app.scheduling.constraints.base import ConstraintPriority

        assert constraint.priority == ConstraintPriority.CRITICAL

    def test_at_demand_pgy1(self, constraint):
        """PGY-1 should have 0.5 demand (2 interns = 1 AT)."""
        assert constraint.AT_DEMAND[1] == 0.5

    def test_at_demand_pgy2(self, constraint):
        """PGY-2/3 should have 0.25 demand (4 = 1 AT)."""
        assert constraint.AT_DEMAND[2] == 0.25
        assert constraint.AT_DEMAND[3] == 0.25

    def test_validate_adequate_coverage(self, constraint, context):
        """No violation when AT coverage is adequate."""
        resident = context.residents[0]
        faculty = context.faculty[0]

        assignments = [
            # 1 PGY-1 in clinic (0.5 demand = 1 AT needed)
            MockAssignment(
                resident.id,
                date(2026, 3, 12),
                "AM",
                "fm_clinic",
                person_type="resident",
                pgy_level=1,
            ),
            # 1 faculty providing AT
            MockAssignment(
                faculty.id, date(2026, 3, 12), "AM", "at", person_type="faculty"
            ),
        ]

        result = constraint.validate(assignments, context)
        assert result.satisfied

    def test_validate_insufficient_coverage(self, constraint, context):
        """Violation when AT coverage is insufficient."""
        # 2 PGY-1 in clinic = 1.0 demand = 1 AT needed
        # But no faculty AT assigned
        assignments = [
            MockAssignment(
                context.residents[0].id,
                date(2026, 3, 12),
                "AM",
                "fm_clinic",
                person_type="resident",
                pgy_level=1,
            ),
            MockAssignment(
                context.residents[1].id,
                date(2026, 3, 12),
                "AM",
                "fm_clinic",
                person_type="resident",
                pgy_level=1,
            ),
        ]

        result = constraint.validate(assignments, context)
        assert not result.satisfied
        assert len(result.violations) > 0
        assert result.violations[0].severity == "CRITICAL"

    def test_pcat_counts_as_at(self, constraint, context):
        """PCAT should count toward AT coverage."""
        resident = context.residents[0]
        faculty = context.faculty[0]

        assignments = [
            MockAssignment(
                resident.id,
                date(2026, 3, 12),
                "AM",
                "fm_clinic",
                person_type="resident",
                pgy_level=1,
            ),
            # PCAT (post-call attending time) counts as AT
            MockAssignment(
                faculty.id, date(2026, 3, 12), "AM", "pcat", person_type="faculty"
            ),
        ]

        result = constraint.validate(assignments, context)
        assert result.satisfied


class TestIntegration:
    """Integration tests for faculty clinic constraints."""

    def test_constraints_importable(self):
        """Constraints should be importable from package."""
        from app.scheduling.constraints import (
            FacultyClinicCapConstraint,
            FacultySupervisionConstraint,
            FACULTY_CLINIC_CAPS,
        )

        assert FacultyClinicCapConstraint is not None
        assert FacultySupervisionConstraint is not None
        assert isinstance(FACULTY_CLINIC_CAPS, dict)
