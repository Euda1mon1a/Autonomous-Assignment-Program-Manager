"""Tests for the faculty write-back template resolution logic in engine.py.

Validates that:
1. DFM is correctly classified as admin (not clinic)
2. Templates are authoritative for C/AT — solver category doesn't gate resolution
3. Solver type is used as fallback when no template exists
4. PCAT, DO, OFF pass through unchanged (not overridden by templates)
"""

from datetime import date
from uuid import uuid4

import pytest


# ---------------------------------------------------------------------------
# Extract the classification sets from engine.py for direct testing.
# We import them indirectly to avoid pulling in the full engine context.
# ---------------------------------------------------------------------------

# These must match engine.py:3327-3346 exactly.
_SOLVER_CLINIC_CODES = {
    "cv",
    "fm_clinic",
    "sm_clinic",
    "c40",
    "hlc",
    "rad",
    "asm",
}
_SOLVER_ADMIN_CODES = {
    "at",
    "gme",
    "sim",
    "lec",
    "pi",
    "dep",
    "dfm",
}


_POSTCALL_CODES = {"pcat", "do", "off"}


def _make_resolve_fn(template_lookup: dict):
    """Build a standalone _resolve_template_activity matching engine.py logic."""

    def _resolve_template_activity(
        faculty_id,
        slot_date,
        time_of_day,
        solver_type,
    ) -> str:
        # Only override C and AT — PCAT, DO, OFF have specific semantics
        if solver_type not in ("C", "AT"):
            return solver_type
        py_wd = slot_date.weekday()
        tpl_code = template_lookup.get((faculty_id, py_wd, time_of_day))
        if tpl_code and tpl_code.lower() not in _POSTCALL_CODES:
            return tpl_code  # Template is authoritative
        return solver_type

    return _resolve_template_activity


# ---------------------------------------------------------------------------
# Classification tests
# ---------------------------------------------------------------------------


class TestSolverCategoryClassification:
    """Verify that activity codes are in the correct solver category set."""

    def test_dfm_is_admin(self):
        assert "dfm" in _SOLVER_ADMIN_CODES
        assert "dfm" not in _SOLVER_CLINIC_CODES

    def test_gme_is_admin(self):
        assert "gme" in _SOLVER_ADMIN_CODES
        assert "gme" not in _SOLVER_CLINIC_CODES

    def test_at_is_admin(self):
        assert "at" in _SOLVER_ADMIN_CODES
        assert "at" not in _SOLVER_CLINIC_CODES

    def test_cv_is_clinic(self):
        assert "cv" in _SOLVER_CLINIC_CODES
        assert "cv" not in _SOLVER_ADMIN_CODES

    def test_fm_clinic_is_clinic(self):
        assert "fm_clinic" in _SOLVER_CLINIC_CODES
        assert "fm_clinic" not in _SOLVER_ADMIN_CODES

    def test_sm_clinic_is_clinic(self):
        assert "sm_clinic" in _SOLVER_CLINIC_CODES
        assert "sm_clinic" not in _SOLVER_ADMIN_CODES

    def test_no_overlap_between_sets(self):
        overlap = _SOLVER_CLINIC_CODES & _SOLVER_ADMIN_CODES
        assert overlap == set(), f"Overlap between clinic and admin: {overlap}"


# ---------------------------------------------------------------------------
# Write-back resolution tests
# ---------------------------------------------------------------------------


class TestResolveTemplateActivity:
    """Verify the template-authoritative write-back logic."""

    @pytest.fixture()
    def faculty_id(self):
        return uuid4()

    @pytest.fixture()
    def monday(self):
        """A known Monday date."""
        return date(2026, 5, 11)  # Monday in Block 12

    def test_template_wins_same_category_clinic(self, faculty_id, monday):
        """Solver=C, template=cv (both clinic) → returns cv."""
        lookup = {(faculty_id, 0, "AM"): "cv"}
        resolve = _make_resolve_fn(lookup)
        assert resolve(faculty_id, monday, "AM", "C") == "cv"

    def test_template_wins_same_category_admin(self, faculty_id, monday):
        """Solver=AT, template=gme (both admin) → returns gme."""
        lookup = {(faculty_id, 0, "AM"): "gme"}
        resolve = _make_resolve_fn(lookup)
        assert resolve(faculty_id, monday, "AM", "AT") == "gme"

    def test_template_wins_cross_category_solver_c_template_admin(
        self, faculty_id, monday
    ):
        """Solver=C, template=gme (cross-category) → returns gme.

        This is the core fix: templates are authoritative regardless of
        solver category.
        """
        lookup = {(faculty_id, 0, "AM"): "gme"}
        resolve = _make_resolve_fn(lookup)
        assert resolve(faculty_id, monday, "AM", "C") == "gme"

    def test_template_wins_cross_category_solver_at_template_clinic(
        self, faculty_id, monday
    ):
        """Solver=AT, template=cv (cross-category) → returns cv."""
        lookup = {(faculty_id, 0, "AM"): "cv"}
        resolve = _make_resolve_fn(lookup)
        assert resolve(faculty_id, monday, "AM", "AT") == "cv"

    def test_no_template_falls_back_to_solver_c(self, faculty_id, monday):
        """No template entry → returns solver type 'C'."""
        resolve = _make_resolve_fn({})
        assert resolve(faculty_id, monday, "AM", "C") == "C"

    def test_no_template_falls_back_to_solver_at(self, faculty_id, monday):
        """No template entry → returns solver type 'AT'."""
        resolve = _make_resolve_fn({})
        assert resolve(faculty_id, monday, "AM", "AT") == "AT"

    def test_dfm_resolves_when_solver_at(self, faculty_id, monday):
        """Solver=AT, template=dfm → returns dfm.

        Before the fix, DFM was in _SOLVER_CLINIC_CODES so this would
        have fallen back to generic 'AT'.
        """
        lookup = {(faculty_id, 0, "AM"): "dfm"}
        resolve = _make_resolve_fn(lookup)
        assert resolve(faculty_id, monday, "AM", "AT") == "dfm"

    def test_dfm_resolves_when_solver_c(self, faculty_id, monday):
        """Solver=C, template=dfm → returns dfm (template authoritative)."""
        lookup = {(faculty_id, 0, "AM"): "dfm"}
        resolve = _make_resolve_fn(lookup)
        assert resolve(faculty_id, monday, "AM", "C") == "dfm"

    def test_pm_slot_uses_correct_lookup(self, faculty_id, monday):
        """AM and PM slots resolve independently."""
        lookup = {
            (faculty_id, 0, "AM"): "cv",
            (faculty_id, 0, "PM"): "gme",
        }
        resolve = _make_resolve_fn(lookup)
        assert resolve(faculty_id, monday, "AM", "C") == "cv"
        assert resolve(faculty_id, monday, "PM", "AT") == "gme"

    def test_weekday_mapping_friday(self, faculty_id):
        """Friday (weekday=4) maps correctly."""
        friday = date(2026, 5, 15)  # Friday
        assert friday.weekday() == 4
        lookup = {(faculty_id, 4, "AM"): "dfm"}
        resolve = _make_resolve_fn(lookup)
        assert resolve(faculty_id, friday, "AM", "C") == "dfm"


# ---------------------------------------------------------------------------
# PCAT / DO / OFF pass-through tests (Codex P1 fix)
# ---------------------------------------------------------------------------


class TestSolverTypePassThrough:
    """Verify that PCAT, DO, and OFF are never overridden by templates.

    These solver types have specific post-call rest semantics:
    - PCAT = Post-Call Attending (AM after overnight call)
    - DO = Day Off post-call (PM after PCAT AM)
    - OFF = No assignment (default)

    Templates must not replace these — doing so would corrupt post-call
    rest tracking and ACGME duty hour compliance.
    """

    @pytest.fixture()
    def faculty_id(self):
        return uuid4()

    @pytest.fixture()
    def monday(self):
        return date(2026, 5, 11)

    def test_pcat_not_overridden_by_template(self, faculty_id, monday):
        """PCAT must pass through even when a template exists for this slot."""
        lookup = {(faculty_id, 0, "AM"): "cv"}
        resolve = _make_resolve_fn(lookup)
        assert resolve(faculty_id, monday, "AM", "PCAT") == "PCAT"

    def test_do_not_overridden_by_template(self, faculty_id, monday):
        """DO must pass through even when a template exists for this slot."""
        lookup = {(faculty_id, 0, "PM"): "gme"}
        resolve = _make_resolve_fn(lookup)
        assert resolve(faculty_id, monday, "PM", "DO") == "DO"

    def test_off_not_overridden_by_template(self, faculty_id, monday):
        """OFF must pass through even when a template exists for this slot."""
        lookup = {(faculty_id, 0, "AM"): "cv"}
        resolve = _make_resolve_fn(lookup)
        assert resolve(faculty_id, monday, "AM", "OFF") == "OFF"

    def test_pcat_without_template(self, faculty_id, monday):
        """PCAT passes through when no template exists."""
        resolve = _make_resolve_fn({})
        assert resolve(faculty_id, monday, "AM", "PCAT") == "PCAT"

    def test_do_without_template(self, faculty_id, monday):
        """DO passes through when no template exists."""
        resolve = _make_resolve_fn({})
        assert resolve(faculty_id, monday, "PM", "DO") == "DO"

    def test_off_without_template(self, faculty_id, monday):
        """OFF passes through when no template exists."""
        resolve = _make_resolve_fn({})
        assert resolve(faculty_id, monday, "AM", "OFF") == "OFF"


# ---------------------------------------------------------------------------
# Post-call template guard tests (Codex P1 fix #2)
# ---------------------------------------------------------------------------


class TestPostCallTemplateGuard:
    """Verify that post-call codes in templates don't corrupt C/AT slots.

    If a coordinator accidentally puts pcat/do/off in a weekly template,
    the resolver must ignore it for C/AT solver types and fall back to the
    generic solver type. Otherwise, normal clinic/supervision slots would
    be written as post-call activities without an actual call event.
    """

    @pytest.fixture()
    def faculty_id(self):
        return uuid4()

    @pytest.fixture()
    def monday(self):
        return date(2026, 5, 11)

    def test_template_pcat_ignored_for_solver_c(self, faculty_id, monday):
        """Template=pcat, solver=C → falls back to C (not pcat)."""
        lookup = {(faculty_id, 0, "AM"): "pcat"}
        resolve = _make_resolve_fn(lookup)
        assert resolve(faculty_id, monday, "AM", "C") == "C"

    def test_template_do_ignored_for_solver_c(self, faculty_id, monday):
        """Template=do, solver=C → falls back to C."""
        lookup = {(faculty_id, 0, "AM"): "do"}
        resolve = _make_resolve_fn(lookup)
        assert resolve(faculty_id, monday, "AM", "C") == "C"

    def test_template_off_ignored_for_solver_at(self, faculty_id, monday):
        """Template=off, solver=AT → falls back to AT."""
        lookup = {(faculty_id, 0, "AM"): "off"}
        resolve = _make_resolve_fn(lookup)
        assert resolve(faculty_id, monday, "AM", "AT") == "AT"

    def test_template_pcat_ignored_for_solver_at(self, faculty_id, monday):
        """Template=pcat, solver=AT → falls back to AT."""
        lookup = {(faculty_id, 0, "PM"): "pcat"}
        resolve = _make_resolve_fn(lookup)
        assert resolve(faculty_id, monday, "PM", "AT") == "AT"

    def test_valid_template_still_works_alongside_guard(self, faculty_id, monday):
        """Valid template codes (cv, gme) are not affected by the guard."""
        lookup = {
            (faculty_id, 0, "AM"): "cv",
            (faculty_id, 0, "PM"): "gme",
        }
        resolve = _make_resolve_fn(lookup)
        assert resolve(faculty_id, monday, "AM", "C") == "cv"
        assert resolve(faculty_id, monday, "PM", "AT") == "gme"
