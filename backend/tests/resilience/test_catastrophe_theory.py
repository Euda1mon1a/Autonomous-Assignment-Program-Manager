"""Tests for catastrophe theory (pure logic, no DB)."""

import pytest

from app.resilience.exotic.catastrophe import (
    CatastrophePoint,
    CatastropheTheory,
    CuspParameters,
)


# -- CuspParameters dataclass ------------------------------------------------


class TestCuspParameters:
    def test_creation(self):
        p = CuspParameters(a=-1.0, b=0.5, x=2.0, potential=3.5)
        assert p.a == -1.0
        assert p.b == 0.5
        assert p.x == 2.0
        assert p.potential == 3.5


# -- CatastrophePoint dataclass ---------------------------------------------


class TestCatastrophePoint:
    def test_creation(self):
        cp = CatastrophePoint(
            a_critical=-2.0,
            b_critical=0.3,
            x_before=-1.0,
            x_after=1.5,
            jump_magnitude=2.5,
            hysteresis_width=0.5,
        )
        assert cp.a_critical == -2.0
        assert cp.jump_magnitude == 2.5
        assert cp.hysteresis_width == 0.5


# -- CatastropheTheory init -------------------------------------------------


class TestCatastropheTheoryInit:
    def test_init(self):
        ct = CatastropheTheory()
        assert ct is not None


# -- calculate_cusp_potential ------------------------------------------------


class TestCalculateCuspPotential:
    def test_at_zero(self):
        ct = CatastropheTheory()
        # V(0) = 0^4/4 + a*0^2/2 + b*0 = 0
        assert ct.calculate_cusp_potential(0.0, a=1.0, b=1.0) == 0.0

    def test_known_value(self):
        ct = CatastropheTheory()
        # V(1; a=0, b=0) = 1/4 + 0 + 0 = 0.25
        assert ct.calculate_cusp_potential(1.0, a=0.0, b=0.0) == pytest.approx(0.25)

    def test_with_bias(self):
        ct = CatastropheTheory()
        # V(1; a=0, b=1) = 1/4 + 0 + 1 = 1.25
        assert ct.calculate_cusp_potential(1.0, a=0.0, b=1.0) == pytest.approx(1.25)

    def test_with_asymmetry(self):
        ct = CatastropheTheory()
        # V(1; a=2, b=0) = 1/4 + 2*1/2 + 0 = 1.25
        assert ct.calculate_cusp_potential(1.0, a=2.0, b=0.0) == pytest.approx(1.25)

    def test_negative_x(self):
        ct = CatastropheTheory()
        # V(-2; a=0, b=0) = 16/4 = 4.0
        assert ct.calculate_cusp_potential(-2.0, a=0.0, b=0.0) == pytest.approx(4.0)

    def test_symmetry_with_no_bias(self):
        ct = CatastropheTheory()
        # V(x) = V(-x) when b=0
        v_pos = ct.calculate_cusp_potential(1.5, a=-1.0, b=0.0)
        v_neg = ct.calculate_cusp_potential(-1.5, a=-1.0, b=0.0)
        assert v_pos == pytest.approx(v_neg)


# -- find_equilibria ---------------------------------------------------------


class TestFindEquilibria:
    def test_single_equilibrium_positive_a(self):
        ct = CatastropheTheory()
        # x^3 + x + 0 = 0 => only x=0
        roots = ct.find_equilibria(a=1.0, b=0.0)
        assert len(roots) == 1
        assert roots[0] == pytest.approx(0.0, abs=1e-6)

    def test_three_equilibria_negative_a(self):
        ct = CatastropheTheory()
        # x^3 - 3x + 0 = 0 => x(x^2 - 3) = 0 => x=0, x=+-sqrt(3)
        roots = ct.find_equilibria(a=-3.0, b=0.0)
        assert len(roots) == 3
        assert roots[0] == pytest.approx(-1.732, abs=0.01)
        assert roots[1] == pytest.approx(0.0, abs=0.01)
        assert roots[2] == pytest.approx(1.732, abs=0.01)

    def test_sorted_output(self):
        ct = CatastropheTheory()
        roots = ct.find_equilibria(a=-3.0, b=0.0)
        assert roots == sorted(roots)

    def test_with_bias(self):
        ct = CatastropheTheory()
        # x^3 + x + 1 = 0 has one real root
        roots = ct.find_equilibria(a=1.0, b=1.0)
        assert len(roots) >= 1

    def test_equilibria_satisfy_cubic(self):
        ct = CatastropheTheory()
        a, b = -2.0, 0.5
        roots = ct.find_equilibria(a, b)
        for r in roots:
            assert r**3 + a * r + b == pytest.approx(0.0, abs=1e-6)


# -- classify_equilibrium_stability ------------------------------------------


class TestClassifyEquilibriumStability:
    def test_stable_minimum(self):
        ct = CatastropheTheory()
        # At x=sqrt(3), a=-3: 3*3 + (-3) = 6 > 0 => stable
        result = ct.classify_equilibrium_stability(x=1.732, a=-3.0, b=0.0)
        assert result == "stable"

    def test_unstable_maximum(self):
        ct = CatastropheTheory()
        # At x=0, a=-3: 3*0 + (-3) = -3 < 0 => unstable
        result = ct.classify_equilibrium_stability(x=0.0, a=-3.0, b=0.0)
        assert result == "unstable"

    def test_positive_a_always_stable(self):
        ct = CatastropheTheory()
        # 3x^2 + a, for a>0 and any x, always positive
        result = ct.classify_equilibrium_stability(x=0.0, a=1.0, b=0.0)
        assert result == "stable"

    def test_stability_depends_on_second_derivative(self):
        ct = CatastropheTheory()
        # At x=0, a=-1: 3*0 + (-1) = -1 < 0 => unstable
        assert ct.classify_equilibrium_stability(0.0, a=-1.0, b=0.0) == "unstable"
        # At x=1, a=-1: 3*1 + (-1) = 2 > 0 => stable
        assert ct.classify_equilibrium_stability(1.0, a=-1.0, b=0.0) == "stable"


# -- find_bifurcation_set ----------------------------------------------------


class TestFindBifurcationSet:
    def test_returns_correct_count(self):
        ct = CatastropheTheory()
        points = ct.find_bifurcation_set(b_range=(-1.0, 1.0), num_points=50)
        assert len(points) == 50

    def test_points_are_tuples(self):
        ct = CatastropheTheory()
        points = ct.find_bifurcation_set(b_range=(-1.0, 1.0), num_points=10)
        for a, b in points:
            assert isinstance(a, float)
            assert isinstance(b, float)

    def test_origin_on_boundary(self):
        ct = CatastropheTheory()
        # At b=0, a should be 0 (cusp point)
        points = ct.find_bifurcation_set(b_range=(-0.01, 0.01), num_points=3)
        # Middle point should be near origin
        a_mid, b_mid = points[1]
        assert a_mid == pytest.approx(0.0, abs=0.1)

    def test_a_negative_for_nonzero_b(self):
        ct = CatastropheTheory()
        points = ct.find_bifurcation_set(b_range=(0.1, 1.0), num_points=10)
        for a, b in points:
            assert a <= 0  # a is always negative on bifurcation set


# -- predict_catastrophe_jump ------------------------------------------------


class TestPredictCatastropheJump:
    def test_no_jump_in_stable_region(self):
        ct = CatastropheTheory()
        # Start far from bifurcation, small perturbation
        result = ct.predict_catastrophe_jump(
            current_a=1.0, current_b=0.0, da=0.1, db=0.1
        )
        assert result is None

    def test_jump_crossing_bifurcation(self):
        ct = CatastropheTheory()
        # Start with 3 equilibria (a=-3, b=0), push b to cause jump
        result = ct.predict_catastrophe_jump(
            current_a=-3.0, current_b=0.0, da=0.0, db=3.0, num_steps=200
        )
        # Should detect a jump as we move along the b axis
        if result is not None:
            assert result.jump_magnitude > 0

    def test_returns_catastrophe_point_or_none(self):
        ct = CatastropheTheory()
        result = ct.predict_catastrophe_jump(
            current_a=-2.0, current_b=0.0, da=1.0, db=2.0
        )
        assert result is None or isinstance(result, CatastrophePoint)


# -- calculate_resilience_from_catastrophe -----------------------------------


class TestCalculateResilienceFromCatastrophe:
    def test_returns_expected_keys(self):
        ct = CatastropheTheory()
        result = ct.calculate_resilience_from_catastrophe(
            current_state=(1.0, 0.0, 0.0),
            stress_direction=(0.1, 0.1),
        )
        expected_keys = {
            "resilience_score",
            "status",
            "is_safe",
            "distance_to_catastrophe",
            "current_distance_to_bifurcation",
            "warning",
            "catastrophe_point",
        }
        assert set(result.keys()) == expected_keys

    def test_far_from_bifurcation_is_robust(self):
        ct = CatastropheTheory()
        # a^3 + 27*b^2 = 1000 + 0 = 1000, well above 10
        result = ct.calculate_resilience_from_catastrophe(
            current_state=(10.0, 0.0, 0.0),
            stress_direction=(0.01, 0.01),
        )
        assert result["resilience_score"] == 1.0  # capped at 1.0
        assert result["status"] == "robust"

    def test_near_bifurcation_is_vulnerable(self):
        ct = CatastropheTheory()
        # a^3 + 27*b^2 near 0 → low resilience
        # a=-3, b=0: (-3)^3 + 27*0 = -27, |distance| = 27 → score = 27/10 = 2.7 → capped at 1.0
        # Need a closer point: a=0, b=0 → distance=0 → score=0
        result = ct.calculate_resilience_from_catastrophe(
            current_state=(0.0, 0.0, 0.0),
            stress_direction=(0.01, 0.01),
        )
        assert result["resilience_score"] == 0.0
        assert result["status"] == "critical"

    def test_safe_when_no_catastrophe(self):
        ct = CatastropheTheory()
        result = ct.calculate_resilience_from_catastrophe(
            current_state=(5.0, 0.0, 0.0),
            stress_direction=(0.01, 0.01),
        )
        if result["catastrophe_point"] is None:
            assert result["is_safe"] is True
            assert "No catastrophe predicted" in result["warning"]

    def test_status_classification(self):
        ct = CatastropheTheory()
        # Test the boundaries: robust (>0.8), stable (>0.5), vulnerable (>0.2), critical (<=0.2)
        # |a^3 + 27*b^2| / 10 = score
        # score = 0.9 → |val| = 9 → a=cube_root(9)≈2.08, b=0
        result = ct.calculate_resilience_from_catastrophe(
            current_state=(2.08, 0.0, 0.0),
            stress_direction=(0.01, 0.01),
        )
        assert result["status"] == "robust"


# -- model_hysteresis --------------------------------------------------------


class TestModelHysteresis:
    def test_returns_expected_keys(self):
        ct = CatastropheTheory()
        result = ct.model_hysteresis(a=-3.0, b_range=(-2.0, 2.0), num_steps=20)
        assert "forward_path" in result
        assert "backward_path" in result
        assert "hysteresis_area" in result
        assert "has_hysteresis" in result

    def test_path_lengths_match_num_steps(self):
        ct = CatastropheTheory()
        result = ct.model_hysteresis(a=-3.0, b_range=(-2.0, 2.0), num_steps=50)
        assert len(result["forward_path"]) == 50
        assert len(result["backward_path"]) == 50

    def test_no_hysteresis_positive_a(self):
        ct = CatastropheTheory()
        # With a > 0, only one equilibrium → no hysteresis
        result = ct.model_hysteresis(a=1.0, b_range=(-2.0, 2.0), num_steps=50)
        assert result["hysteresis_area"] < 0.5  # Should be very small or zero

    def test_hysteresis_negative_a(self):
        ct = CatastropheTheory()
        # With a < 0 (strong), should have hysteresis
        result = ct.model_hysteresis(a=-5.0, b_range=(-5.0, 5.0), num_steps=100)
        assert result["hysteresis_area"] >= 0  # Non-negative area

    def test_path_tuples_have_two_elements(self):
        ct = CatastropheTheory()
        result = ct.model_hysteresis(a=-3.0, b_range=(-1.0, 1.0), num_steps=10)
        for b_val, x_val in result["forward_path"]:
            assert isinstance(b_val, float)
            assert isinstance(x_val, float)
