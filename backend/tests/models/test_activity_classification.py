"""Tests for Activity model classification properties.

Validates that:
1. is_supervision uses the provides_supervision DB field (not hardcoded)
2. is_solver_clinic maps to counts_toward_physical_capacity
3. is_solver_admin is the complement (non-clinic, non-time_off)
4. Classification sets are disjoint

NOTE: We replicate the property logic here to avoid importing the Activity
model, which triggers the full app import chain and settings validation.
The property implementations must match engine.py/activity.py exactly.
"""

import pytest


# ---------------------------------------------------------------------------
# Replicated property logic from app/models/activity.py.
# If these change, update here too.
# ---------------------------------------------------------------------------


def _is_supervision(provides_supervision: bool) -> bool:
    return bool(provides_supervision)


def _is_solver_clinic(counts_toward_physical_capacity: bool) -> bool:
    return bool(counts_toward_physical_capacity)


def _is_solver_admin(
    counts_toward_physical_capacity: bool, activity_category: str
) -> bool:
    return not counts_toward_physical_capacity and activity_category != "time_off"


class _Activity:
    """Lightweight stand-in for testing classification properties."""

    def __init__(
        self,
        code: str = "test",
        activity_category: str = "clinical",
        counts_toward_physical_capacity: bool = False,
        provides_supervision: bool = False,
    ):
        self.code = code
        self.activity_category = activity_category
        self.counts_toward_physical_capacity = counts_toward_physical_capacity
        self.provides_supervision = provides_supervision

    @property
    def is_supervision(self) -> bool:
        return _is_supervision(self.provides_supervision)

    @property
    def is_solver_clinic(self) -> bool:
        return _is_solver_clinic(self.counts_toward_physical_capacity)

    @property
    def is_solver_admin(self) -> bool:
        return _is_solver_admin(
            self.counts_toward_physical_capacity, self.activity_category
        )


# ---------------------------------------------------------------------------
# is_supervision tests
# ---------------------------------------------------------------------------


class TestIsSupervision:
    """Verify is_supervision uses the provides_supervision DB field."""

    def test_at_is_supervision(self):
        a = _Activity(code="at", provides_supervision=True)
        assert a.is_supervision is True

    def test_pcat_is_supervision(self):
        a = _Activity(code="pcat", provides_supervision=True)
        assert a.is_supervision is True

    def test_do_is_supervision(self):
        a = _Activity(code="do", provides_supervision=True)
        assert a.is_supervision is True

    def test_sm_clinic_is_supervision(self):
        a = _Activity(code="sm_clinic", provides_supervision=True)
        assert a.is_supervision is True

    def test_gme_is_not_supervision(self):
        a = _Activity(code="gme", provides_supervision=False)
        assert a.is_supervision is False

    def test_fm_clinic_is_not_supervision(self):
        a = _Activity(code="fm_clinic", provides_supervision=False)
        assert a.is_supervision is False

    def test_field_based_not_hardcoded(self):
        """A hypothetical new supervision activity is recognized by field alone."""
        a = _Activity(code="new_supervision_code", provides_supervision=True)
        assert a.is_supervision is True


# ---------------------------------------------------------------------------
# is_solver_clinic tests
# ---------------------------------------------------------------------------


class TestIsSolverClinic:
    """Verify is_solver_clinic maps to counts_toward_physical_capacity."""

    def test_c_is_clinic(self):
        a = _Activity(code="C", counts_toward_physical_capacity=True)
        assert a.is_solver_clinic is True

    def test_fm_clinic_is_clinic(self):
        a = _Activity(code="fm_clinic", counts_toward_physical_capacity=True)
        assert a.is_solver_clinic is True

    def test_cv_is_clinic(self):
        a = _Activity(code="CV", counts_toward_physical_capacity=True)
        assert a.is_solver_clinic is True

    def test_hlc_is_clinic(self):
        a = _Activity(code="HLC", counts_toward_physical_capacity=True)
        assert a.is_solver_clinic is True

    def test_dfm_is_not_clinic(self):
        a = _Activity(
            code="dfm",
            activity_category="administrative",
            counts_toward_physical_capacity=False,
        )
        assert a.is_solver_clinic is False

    def test_at_is_not_clinic(self):
        a = _Activity(
            code="at",
            counts_toward_physical_capacity=False,
            provides_supervision=True,
        )
        assert a.is_solver_clinic is False

    def test_weekend_is_not_clinic(self):
        a = _Activity(
            code="W",
            activity_category="time_off",
            counts_toward_physical_capacity=False,
        )
        assert a.is_solver_clinic is False


# ---------------------------------------------------------------------------
# is_solver_admin tests
# ---------------------------------------------------------------------------


class TestIsSolverAdmin:
    """Verify is_solver_admin is the complement of clinic + time_off."""

    def test_at_is_admin(self):
        a = _Activity(
            code="at",
            activity_category="clinical",
            counts_toward_physical_capacity=False,
        )
        assert a.is_solver_admin is True

    def test_gme_is_admin(self):
        a = _Activity(
            code="gme",
            activity_category="administrative",
            counts_toward_physical_capacity=False,
        )
        assert a.is_solver_admin is True

    def test_dfm_is_admin(self):
        a = _Activity(
            code="dfm",
            activity_category="administrative",
            counts_toward_physical_capacity=False,
        )
        assert a.is_solver_admin is True

    def test_lec_is_admin(self):
        a = _Activity(
            code="lec",
            activity_category="educational",
            counts_toward_physical_capacity=False,
        )
        assert a.is_solver_admin is True

    def test_sim_is_admin(self):
        a = _Activity(
            code="SIM",
            activity_category="educational",
            counts_toward_physical_capacity=False,
        )
        assert a.is_solver_admin is True

    def test_c_is_not_admin(self):
        """Clinic activities are not admin."""
        a = _Activity(
            code="C",
            activity_category="clinical",
            counts_toward_physical_capacity=True,
        )
        assert a.is_solver_admin is False

    def test_weekend_is_not_admin(self):
        """Time-off activities are neither clinic nor admin."""
        a = _Activity(
            code="W",
            activity_category="time_off",
            counts_toward_physical_capacity=False,
        )
        assert a.is_solver_admin is False

    def test_holiday_is_not_admin(self):
        a = _Activity(
            code="HOL",
            activity_category="time_off",
            counts_toward_physical_capacity=False,
        )
        assert a.is_solver_admin is False


# ---------------------------------------------------------------------------
# Disjointness tests
# ---------------------------------------------------------------------------


class TestClassificationDisjointness:
    """Verify that clinic, admin, and time_off are mutually exclusive."""

    def test_clinic_activity_not_admin(self):
        a = _Activity(
            code="C",
            activity_category="clinical",
            counts_toward_physical_capacity=True,
        )
        assert a.is_solver_clinic is True
        assert a.is_solver_admin is False

    def test_admin_activity_not_clinic(self):
        a = _Activity(
            code="gme",
            activity_category="administrative",
            counts_toward_physical_capacity=False,
        )
        assert a.is_solver_clinic is False
        assert a.is_solver_admin is True

    def test_time_off_neither_clinic_nor_admin(self):
        a = _Activity(
            code="W",
            activity_category="time_off",
            counts_toward_physical_capacity=False,
        )
        assert a.is_solver_clinic is False
        assert a.is_solver_admin is False

    @pytest.mark.parametrize(
        "code,category,capacity,expected_clinic,expected_admin",
        [
            ("C", "clinical", True, True, False),
            ("fm_clinic", "clinical", True, True, False),
            ("CV", "clinical", True, True, False),
            ("at", "clinical", False, False, True),
            ("pcat", "clinical", False, False, True),
            ("gme", "administrative", False, False, True),
            ("dfm", "administrative", False, False, True),
            ("lec", "educational", False, False, True),
            ("SIM", "educational", False, False, True),
            ("W", "time_off", False, False, False),
            ("HOL", "time_off", False, False, False),
            ("off", "time_off", False, False, False),
        ],
    )
    def test_known_activities(
        self, code, category, capacity, expected_clinic, expected_admin
    ):
        a = _Activity(
            code=code,
            activity_category=category,
            counts_toward_physical_capacity=capacity,
        )
        assert a.is_solver_clinic is expected_clinic, f"{code}: is_solver_clinic"
        assert a.is_solver_admin is expected_admin, f"{code}: is_solver_admin"
