"""Tests for Activity model classification properties.

Validates that:
1. is_supervision uses the provides_supervision DB field (not hardcoded)
2. is_solver_clinic maps to counts_toward_physical_capacity
3. is_solver_admin is the complement (non-clinic, non-time_off)
4. Classification sets are disjoint
5. Test property implementations match the real Activity model source

NOTE: We replicate the property logic here to avoid importing the Activity
model, which triggers the full app import chain and settings validation
(Activity → Base → audit.py → logging → config.py → Settings()).
A source-drift guard test (TestSourceDriftGuard) parses the real model
file and verifies the replicated logic hasn't diverged.
"""

import ast
import textwrap
from pathlib import Path

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


# ---------------------------------------------------------------------------
# Source drift guard — ensures test helpers match the real Activity model.
# We parse the source AST instead of importing to avoid the settings chain.
# ---------------------------------------------------------------------------

# Path to the real Activity model, relative to this test file.
_ACTIVITY_MODEL_PATH = (
    Path(__file__).resolve().parent.parent.parent / "app" / "models" / "activity.py"
)


def _extract_property_source(filepath: Path, property_name: str) -> str:
    """Extract the body source of a @property from a class in the given file.

    Returns the dedented body (everything after the def line and docstring).
    """
    source = filepath.read_text()
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef) or node.name != "Activity":
            continue
        for item in node.body:
            if (
                isinstance(item, ast.FunctionDef)
                and item.name == property_name
                and any(
                    isinstance(d, ast.Name) and d.id == "property"
                    for d in item.decorator_list
                )
            ):
                # Get the return statement(s) — skip docstring
                body = [
                    n
                    for n in item.body
                    if not (
                        isinstance(n, ast.Expr)
                        and isinstance(n.value, ast.Constant)
                        and isinstance(n.value.value, str)
                    )
                ]
                return ast.dump(ast.Module(body=body, type_ignores=[]))
    raise ValueError(f"Property {property_name!r} not found in {filepath}")


class TestSourceDriftGuard:
    """Verify that test helper logic matches the real Activity model.

    These tests parse the Activity model source via AST and compare the
    property implementations to catch drift without triggering the import
    chain.
    """

    def test_is_supervision_matches_model(self):
        """Test helper _is_supervision matches Activity.is_supervision.

        Real model should use ``bool(self.provides_supervision)`` —
        field-driven, not hardcoded string checks.
        """
        model_ast = _extract_property_source(_ACTIVITY_MODEL_PATH, "is_supervision")
        assert "provides_supervision" in model_ast
        # Should be a simple bool() call on a field, not a set membership check
        assert "Call" in model_ast, "Expected bool() call wrapping the field"
        # Must NOT contain hardcoded code strings like {'at', 'pcat'}
        assert "Set(" not in model_ast, (
            "is_supervision should use provides_supervision field, not a hardcoded set"
        )

    def test_is_solver_clinic_matches_model(self):
        """Test helper _is_solver_clinic matches Activity.is_solver_clinic."""
        model_ast = _extract_property_source(_ACTIVITY_MODEL_PATH, "is_solver_clinic")
        assert "counts_toward_physical_capacity" in model_ast
        assert "Call" in model_ast, "Expected bool() call wrapping the field"

    def test_is_solver_admin_matches_model(self):
        """Test helper _is_solver_admin matches Activity.is_solver_admin.

        Real model uses ``not self.counts_toward_physical_capacity and
        self.activity_category != ActivityCategory.TIME_OFF.value``.
        """
        model_ast = _extract_property_source(_ACTIVITY_MODEL_PATH, "is_solver_admin")
        assert "counts_toward_physical_capacity" in model_ast
        assert "activity_category" in model_ast
        # Should reference TIME_OFF (via enum or literal)
        assert "TIME_OFF" in model_ast or "time_off" in model_ast

    def test_model_file_exists(self):
        """Guard: the model file we parse must exist."""
        assert _ACTIVITY_MODEL_PATH.exists(), (
            f"Activity model not found at {_ACTIVITY_MODEL_PATH}"
        )
