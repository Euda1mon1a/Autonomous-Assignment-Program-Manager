"""Tests for mathematical utility functions."""

import pytest

from app.utils.math_utils import (
    clamp,
    moving_average,
    percentage,
    round_to,
    safe_divide,
)


class TestClamp:
    """Tests for clamp."""

    def test_value_within_range(self):
        assert clamp(5, 0, 10) == 5

    def test_value_below_min(self):
        assert clamp(-5, 0, 10) == 0

    def test_value_above_max(self):
        assert clamp(15, 0, 10) == 10

    def test_value_equals_min(self):
        assert clamp(0, 0, 10) == 0

    def test_value_equals_max(self):
        assert clamp(10, 0, 10) == 10

    def test_float_values(self):
        assert clamp(0.5, 0.0, 1.0) == 0.5

    def test_negative_range(self):
        assert clamp(0, -10, -1) == -1


class TestPercentage:
    """Tests for percentage."""

    def test_simple_percentage(self):
        assert percentage(50, 100) == 50.0

    def test_zero_whole(self):
        assert percentage(50, 0) == 0.0

    def test_full_percentage(self):
        assert percentage(100, 100) == 100.0

    def test_over_100_percent(self):
        assert percentage(150, 100) == 150.0

    def test_custom_decimals(self):
        assert percentage(1, 3, decimals=4) == 33.3333

    def test_zero_part(self):
        assert percentage(0, 100) == 0.0

    def test_default_2_decimals(self):
        assert percentage(1, 3) == 33.33


class TestRoundTo:
    """Tests for round_to."""

    def test_round_to_2_decimals(self):
        assert round_to(3.14159) == 3.14

    def test_round_to_0_decimals(self):
        assert round_to(3.7, 0) == 4.0

    def test_round_to_4_decimals(self):
        assert round_to(3.14159, 4) == 3.1416

    def test_no_rounding_needed(self):
        assert round_to(3.14, 2) == 3.14


class TestSafeDivide:
    """Tests for safe_divide."""

    def test_normal_division(self):
        assert safe_divide(10, 2) == 5.0

    def test_divide_by_zero_returns_default(self):
        assert safe_divide(10, 0) == 0.0

    def test_custom_default(self):
        assert safe_divide(10, 0, default=-1) == -1.0

    def test_float_division(self):
        assert safe_divide(1, 3) == pytest.approx(0.3333, abs=0.001)

    def test_zero_numerator(self):
        assert safe_divide(0, 5) == 0.0


class TestMovingAverage:
    """Tests for moving_average."""

    def test_simple_average(self):
        result = moving_average([1, 2, 3, 4, 5], 3)
        assert result == [2.0, 3.0, 4.0]

    def test_window_equals_length(self):
        result = moving_average([1, 2, 3], 3)
        assert result == [2.0]

    def test_window_larger_than_list(self):
        result = moving_average([1, 2], 3)
        assert result == []

    def test_window_of_1(self):
        result = moving_average([1, 2, 3], 1)
        assert result == [1.0, 2.0, 3.0]

    def test_zero_window_raises(self):
        with pytest.raises(ValueError, match="positive"):
            moving_average([1, 2, 3], 0)

    def test_negative_window_raises(self):
        with pytest.raises(ValueError, match="positive"):
            moving_average([1, 2, 3], -1)

    def test_empty_list(self):
        result = moving_average([], 3)
        assert result == []

    def test_float_values(self):
        result = moving_average([1.5, 2.5, 3.5], 2)
        assert result == [2.0, 3.0]
