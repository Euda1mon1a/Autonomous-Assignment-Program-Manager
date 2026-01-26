"""Tests for CPSATActivitySolver - activity assignment with CP-SAT.

These tests use mocking to avoid JSONB/SQLite compatibility issues.
"""

from datetime import date
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from app.scheduling.activity_solver import (
    ADMIN_ACTIVITY_CODES,
    AT_COVERAGE_CODES,
    BLOCK_HALF_DAY,
    CPSATActivitySolver,
    DEFAULT_WEEKLY_C_MAX,
    DEFAULT_WEEKLY_C_MIN,
    DEFAULT_WEEKLY_SPECIALTY_MAX,
    DEFAULT_WEEKLY_SPECIALTY_MIN,
    FACULTY_ADMIN_BONUS,
    FACULTY_CLINIC_SHORTFALL_PENALTY,
    OUTPATIENT_ACTIVITY_TYPES,
    RESIDENT_CLINIC_CODES,
    solve_activities,
)


class TestModuleConstants:
    """Tests verifying module constants are defined correctly."""

    def test_default_weekly_c_min(self):
        """DEFAULT_WEEKLY_C_MIN should be defined."""
        assert DEFAULT_WEEKLY_C_MIN == 2

    def test_default_weekly_c_max(self):
        """DEFAULT_WEEKLY_C_MAX should be defined."""
        assert DEFAULT_WEEKLY_C_MAX == 4

    def test_default_weekly_specialty_min(self):
        """DEFAULT_WEEKLY_SPECIALTY_MIN should be defined."""
        assert DEFAULT_WEEKLY_SPECIALTY_MIN == 3

    def test_default_weekly_specialty_max(self):
        """DEFAULT_WEEKLY_SPECIALTY_MAX should be defined."""
        assert DEFAULT_WEEKLY_SPECIALTY_MAX == 4

    def test_block_half_day(self):
        """BLOCK_HALF_DAY should be 14 (day 15+ uses secondary rotation)."""
        assert BLOCK_HALF_DAY == 14

    def test_outpatient_rotation_types(self):
        """OUTPATIENT_ACTIVITY_TYPES should include clinic and outpatient."""
        assert "clinic" in OUTPATIENT_ACTIVITY_TYPES
        assert "outpatient" in OUTPATIENT_ACTIVITY_TYPES

    def test_resident_clinic_codes(self):
        """RESIDENT_CLINIC_CODES should include FM_CLINIC, C, C-N, CV."""
        assert "FM_CLINIC" in RESIDENT_CLINIC_CODES
        assert "C" in RESIDENT_CLINIC_CODES
        assert "C-N" in RESIDENT_CLINIC_CODES
        assert "CV" in RESIDENT_CLINIC_CODES

    def test_at_coverage_codes(self):
        """AT_COVERAGE_CODES should include AT and PCAT."""
        assert "AT" in AT_COVERAGE_CODES
        assert "PCAT" in AT_COVERAGE_CODES

    def test_admin_activity_codes(self):
        """ADMIN_ACTIVITY_CODES should map GME/DFM/SM to codes."""
        assert "GME" in ADMIN_ACTIVITY_CODES
        assert "DFM" in ADMIN_ACTIVITY_CODES
        assert "SM" in ADMIN_ACTIVITY_CODES
        assert ADMIN_ACTIVITY_CODES["GME"] == "gme"
        assert ADMIN_ACTIVITY_CODES["DFM"] == "dfm"
        assert ADMIN_ACTIVITY_CODES["SM"] == "sm_clinic"

    def test_faculty_clinic_shortfall_penalty(self):
        """FACULTY_CLINIC_SHORTFALL_PENALTY should be defined."""
        assert FACULTY_CLINIC_SHORTFALL_PENALTY == 10

    def test_faculty_admin_bonus(self):
        """FACULTY_ADMIN_BONUS should be defined."""
        assert FACULTY_ADMIN_BONUS == 1


class TestCPSATActivitySolverInit:
    """Tests for CPSATActivitySolver initialization."""

    def test_init_with_defaults(self):
        """Solver initializes with default timeout and workers."""
        mock_session = MagicMock()
        solver = CPSATActivitySolver(mock_session)

        assert solver.session is mock_session
        assert solver.timeout_seconds == 60.0
        assert solver.num_workers == 4

    def test_init_with_custom_timeout(self):
        """Solver accepts custom timeout."""
        mock_session = MagicMock()
        solver = CPSATActivitySolver(mock_session, timeout_seconds=120.0)

        assert solver.timeout_seconds == 120.0

    def test_init_with_custom_workers(self):
        """Solver accepts custom worker count."""
        mock_session = MagicMock()
        solver = CPSATActivitySolver(mock_session, num_workers=8)

        assert solver.num_workers == 8

    def test_activity_cache_initialized_empty(self):
        """Activity cache starts empty."""
        mock_session = MagicMock()
        solver = CPSATActivitySolver(mock_session)

        assert solver._activity_cache == {}

    def test_assignment_rotation_map_initialized_empty(self):
        """Assignment rotation map starts empty."""
        mock_session = MagicMock()
        solver = CPSATActivitySolver(mock_session)

        assert solver._assignment_rotation_map == {}


class TestHelperMethods:
    """Tests for private helper methods."""

    def test_get_activity_by_code_returns_none_if_not_cached(self):
        """_get_activity_by_code returns None if code not in cache."""
        mock_session = MagicMock()
        solver = CPSATActivitySolver(mock_session)

        result = solver._get_activity_by_code("NONEXISTENT")
        assert result is None

    def test_get_activity_by_code_returns_cached_activity(self):
        """_get_activity_by_code returns activity from cache."""
        mock_session = MagicMock()
        solver = CPSATActivitySolver(mock_session)

        mock_activity = MagicMock()
        mock_activity.code = "C"
        solver._activity_cache["C"] = mock_activity

        result = solver._get_activity_by_code("C")
        assert result is mock_activity

    def test_activity_ids_for_codes_empty_codes(self):
        """_activity_ids_for_codes returns empty set for empty codes."""
        mock_session = MagicMock()
        solver = CPSATActivitySolver(mock_session)

        result = solver._activity_ids_for_codes([], set())
        assert result == set()

    def test_activity_ids_for_codes_matches_code(self):
        """_activity_ids_for_codes matches by code."""
        mock_session = MagicMock()
        solver = CPSATActivitySolver(mock_session)

        activity_id = uuid4()
        mock_activity = MagicMock()
        mock_activity.id = activity_id
        mock_activity.code = "C"
        mock_activity.display_abbreviation = None

        result = solver._activity_ids_for_codes([mock_activity], {"C"})
        assert activity_id in result

    def test_activity_ids_for_codes_matches_display_abbreviation(self):
        """_activity_ids_for_codes matches by display_abbreviation."""
        mock_session = MagicMock()
        solver = CPSATActivitySolver(mock_session)

        activity_id = uuid4()
        mock_activity = MagicMock()
        mock_activity.id = activity_id
        mock_activity.code = "fm_clinic"
        mock_activity.display_abbreviation = "C"

        result = solver._activity_ids_for_codes([mock_activity], {"C"})
        assert activity_id in result

    def test_activity_ids_for_codes_case_insensitive(self):
        """_activity_ids_for_codes is case insensitive."""
        mock_session = MagicMock()
        solver = CPSATActivitySolver(mock_session)

        activity_id = uuid4()
        mock_activity = MagicMock()
        mock_activity.id = activity_id
        mock_activity.code = "c"
        mock_activity.display_abbreviation = None

        result = solver._activity_ids_for_codes([mock_activity], {"C"})
        assert activity_id in result

    def test_get_faculty_clinic_caps_with_values(self):
        """_get_faculty_clinic_caps returns min/max from faculty."""
        mock_session = MagicMock()
        solver = CPSATActivitySolver(mock_session)

        mock_faculty = MagicMock()
        mock_faculty.min_clinic_halfdays_per_week = 2
        mock_faculty.max_clinic_halfdays_per_week = 6

        min_c, max_c = solver._get_faculty_clinic_caps(mock_faculty)
        assert min_c == 2
        assert max_c == 6

    def test_get_faculty_clinic_caps_with_none(self):
        """_get_faculty_clinic_caps returns defaults for None values."""
        mock_session = MagicMock()
        solver = CPSATActivitySolver(mock_session)

        mock_faculty = MagicMock()
        mock_faculty.min_clinic_halfdays_per_week = None
        mock_faculty.max_clinic_halfdays_per_week = None

        min_c, max_c = solver._get_faculty_clinic_caps(mock_faculty)
        assert min_c == 0
        assert max_c == 0

    def test_get_faculty_clinic_caps_max_less_than_min(self):
        """_get_faculty_clinic_caps adjusts max if less than min."""
        mock_session = MagicMock()
        solver = CPSATActivitySolver(mock_session)

        mock_faculty = MagicMock()
        mock_faculty.min_clinic_halfdays_per_week = 5
        mock_faculty.max_clinic_halfdays_per_week = 2  # Less than min

        min_c, max_c = solver._get_faculty_clinic_caps(mock_faculty)
        assert min_c == 5
        assert max_c == 5  # Adjusted to equal min

    def test_get_admin_activity_for_faculty_gme(self):
        """_get_admin_activity_for_faculty returns GME activity."""
        mock_session = MagicMock()
        solver = CPSATActivitySolver(mock_session)

        mock_gme_activity = MagicMock()
        activities = {"gme": mock_gme_activity}

        mock_faculty = MagicMock()
        mock_faculty.admin_type = "GME"

        result = solver._get_admin_activity_for_faculty(mock_faculty, activities)
        assert result is mock_gme_activity

    def test_get_admin_activity_for_faculty_dfm(self):
        """_get_admin_activity_for_faculty returns DFM activity."""
        mock_session = MagicMock()
        solver = CPSATActivitySolver(mock_session)

        mock_dfm_activity = MagicMock()
        activities = {"dfm": mock_dfm_activity}

        mock_faculty = MagicMock()
        mock_faculty.admin_type = "DFM"

        result = solver._get_admin_activity_for_faculty(mock_faculty, activities)
        assert result is mock_dfm_activity

    def test_get_admin_activity_for_faculty_default_gme(self):
        """_get_admin_activity_for_faculty defaults to GME if admin_type is None."""
        mock_session = MagicMock()
        solver = CPSATActivitySolver(mock_session)

        mock_gme_activity = MagicMock()
        activities = {"gme": mock_gme_activity}

        mock_faculty = MagicMock()
        mock_faculty.admin_type = None

        result = solver._get_admin_activity_for_faculty(mock_faculty, activities)
        assert result is mock_gme_activity

    def test_is_sports_medicine_faculty_with_flag(self):
        """_is_sports_medicine_faculty returns True if is_sports_medicine=True."""
        mock_session = MagicMock()
        solver = CPSATActivitySolver(mock_session)

        mock_faculty = MagicMock()
        mock_faculty.is_sports_medicine = True

        assert solver._is_sports_medicine_faculty(mock_faculty) is True

    def test_is_sports_medicine_faculty_with_role(self):
        """_is_sports_medicine_faculty returns True if faculty_role=sports_med."""
        mock_session = MagicMock()
        solver = CPSATActivitySolver(mock_session)

        mock_faculty = MagicMock(spec=[])  # No is_sports_medicine attr
        mock_faculty.faculty_role = "sports_med"

        assert solver._is_sports_medicine_faculty(mock_faculty) is True

    def test_is_sports_medicine_faculty_false(self):
        """_is_sports_medicine_faculty returns False for non-SM faculty."""
        mock_session = MagicMock()
        solver = CPSATActivitySolver(mock_session)

        mock_faculty = MagicMock()
        mock_faculty.is_sports_medicine = False

        assert solver._is_sports_medicine_faculty(mock_faculty) is False

    def test_is_sm_template_with_requires_specialty(self):
        """_is_sm_template returns True if requires_specialty is Sports Medicine."""
        mock_session = MagicMock()
        solver = CPSATActivitySolver(mock_session)

        mock_template = MagicMock()
        mock_template.requires_specialty = "Sports Medicine"

        assert solver._is_sm_template(mock_template) is True

    def test_is_sm_template_with_name_match(self):
        """_is_sm_template returns True if name contains SPORTS MEDICINE."""
        mock_session = MagicMock()
        solver = CPSATActivitySolver(mock_session)

        mock_template = MagicMock()
        mock_template.requires_specialty = None
        mock_template.name = "Sports Medicine Rotation"
        mock_template.abbreviation = "SMR"

        assert solver._is_sm_template(mock_template) is True

    def test_is_sm_template_with_abbreviation_sm(self):
        """_is_sm_template returns True if abbreviation is SM."""
        mock_session = MagicMock()
        solver = CPSATActivitySolver(mock_session)

        mock_template = MagicMock()
        mock_template.requires_specialty = None
        mock_template.name = "Something"
        mock_template.abbreviation = "SM"

        assert solver._is_sm_template(mock_template) is True

    def test_is_sm_template_false(self):
        """_is_sm_template returns False for non-SM templates."""
        mock_session = MagicMock()
        solver = CPSATActivitySolver(mock_session)

        mock_template = MagicMock()
        mock_template.requires_specialty = None
        mock_template.name = "Internal Medicine"
        mock_template.abbreviation = "IM"

        assert solver._is_sm_template(mock_template) is False

    def test_get_week_number_first_day(self):
        """_get_week_number returns 1 for first day of block."""
        mock_session = MagicMock()
        solver = CPSATActivitySolver(mock_session)

        block_start = date(2026, 3, 12)
        slot_date = date(2026, 3, 12)

        result = solver._get_week_number(slot_date, block_start)
        assert result == 1

    def test_get_week_number_day_7(self):
        """_get_week_number returns 1 for day 7 (still week 1)."""
        mock_session = MagicMock()
        solver = CPSATActivitySolver(mock_session)

        block_start = date(2026, 3, 12)
        slot_date = date(2026, 3, 18)  # 6 days later

        result = solver._get_week_number(slot_date, block_start)
        assert result == 1

    def test_get_week_number_day_8(self):
        """_get_week_number returns 2 for day 8 (week 2 starts)."""
        mock_session = MagicMock()
        solver = CPSATActivitySolver(mock_session)

        block_start = date(2026, 3, 12)
        slot_date = date(2026, 3, 19)  # 7 days later

        result = solver._get_week_number(slot_date, block_start)
        assert result == 2

    def test_get_week_number_week_4(self):
        """_get_week_number returns 4 for last week."""
        mock_session = MagicMock()
        solver = CPSATActivitySolver(mock_session)

        block_start = date(2026, 3, 12)
        slot_date = date(2026, 4, 8)  # 27 days later (week 4)

        result = solver._get_week_number(slot_date, block_start)
        assert result == 4


class TestSolveReturnFormat:
    """Tests for solve() return value structure."""

    @patch("app.scheduling.activity_solver.get_block_dates")
    @patch.object(CPSATActivitySolver, "_load_candidate_slots")
    def test_solve_no_slots_returns_no_work(self, mock_candidates, mock_dates):
        """solve() with no candidate slots returns no_work status."""
        mock_dates.return_value = MagicMock(
            start_date=date(2026, 3, 12), end_date=date(2026, 4, 8)
        )
        mock_candidates.return_value = []

        solver = CPSATActivitySolver(MagicMock())
        result = solver.solve(10, 2025)

        assert result["success"] is True
        assert result["assignments_updated"] == 0
        assert result["status"] == "no_work"
        assert "message" in result

    @patch("app.scheduling.activity_solver.get_block_dates")
    @patch.object(CPSATActivitySolver, "_load_candidate_slots")
    @patch.object(CPSATActivitySolver, "_filter_outpatient_slots")
    @patch.object(CPSATActivitySolver, "_load_activities")
    @patch.object(CPSATActivitySolver, "_load_assignment_rotation_map")
    def test_solve_no_activities_returns_error(
        self,
        mock_rotation_map,
        mock_activities,
        mock_filter,
        mock_candidates,
        mock_dates,
    ):
        """solve() with no activities returns error status."""
        mock_dates.return_value = MagicMock(
            start_date=date(2026, 3, 12), end_date=date(2026, 4, 8)
        )

        # Create a mock slot with minimal attributes
        mock_slot = MagicMock()
        mock_slot.person_id = uuid4()
        mock_slot.person = MagicMock()
        mock_slot.person.type = "resident"
        mock_slot.date = date(2026, 3, 12)
        mock_slot.time_of_day = "AM"
        mock_slot.block_assignment = None
        mock_candidates.return_value = [mock_slot]
        mock_filter.return_value = [mock_slot]

        mock_activities.return_value = []
        mock_rotation_map.return_value = {}

        solver = CPSATActivitySolver(MagicMock())
        result = solver.solve(10, 2025)

        assert result["success"] is False
        assert result["status"] == "error"
        assert "No activities found" in result.get("message", "")

    def test_solve_returns_dict(self):
        """solve() returns a dictionary."""
        mock_session = MagicMock()
        solver = CPSATActivitySolver(mock_session)

        with (
            patch.object(solver, "_load_candidate_slots", return_value=[]),
            patch("app.scheduling.activity_solver.get_block_dates") as mock_dates,
        ):
            mock_dates.return_value = MagicMock(
                start_date=date(2026, 3, 12), end_date=date(2026, 4, 8)
            )
            result = solver.solve(10, 2025)

        assert isinstance(result, dict)

    def test_solve_result_has_required_keys(self):
        """solve() result contains success, assignments_updated, status keys."""
        mock_session = MagicMock()
        solver = CPSATActivitySolver(mock_session)

        with (
            patch.object(solver, "_load_candidate_slots", return_value=[]),
            patch("app.scheduling.activity_solver.get_block_dates") as mock_dates,
        ):
            mock_dates.return_value = MagicMock(
                start_date=date(2026, 3, 12), end_date=date(2026, 4, 8)
            )
            result = solver.solve(10, 2025)

        assert "success" in result
        assert "assignments_updated" in result
        assert "status" in result


class TestSolveActivitiesConvenience:
    """Tests for solve_activities() convenience function."""

    def test_solve_activities_creates_solver_and_calls_solve(self):
        """solve_activities() creates solver and calls solve()."""
        mock_session = MagicMock()

        with (
            patch(
                "app.scheduling.activity_solver.CPSATActivitySolver"
            ) as mock_solver_class,
        ):
            mock_solver = MagicMock()
            mock_solver.solve.return_value = {"success": True}
            mock_solver_class.return_value = mock_solver

            result = solve_activities(mock_session, 10, 2025)

            mock_solver_class.assert_called_once_with(
                mock_session, timeout_seconds=60.0
            )
            mock_solver.solve.assert_called_once_with(10, 2025)
            assert result == {"success": True}

    def test_solve_activities_passes_timeout(self):
        """solve_activities() passes custom timeout."""
        mock_session = MagicMock()

        with (
            patch(
                "app.scheduling.activity_solver.CPSATActivitySolver"
            ) as mock_solver_class,
        ):
            mock_solver = MagicMock()
            mock_solver.solve.return_value = {"success": True}
            mock_solver_class.return_value = mock_solver

            solve_activities(mock_session, 10, 2025, timeout_seconds=120.0)

            mock_solver_class.assert_called_once_with(
                mock_session, timeout_seconds=120.0
            )
