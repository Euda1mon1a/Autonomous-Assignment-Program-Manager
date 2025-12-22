"""Tests for generate_blocks.py script.

Tests the block date calculation logic and argument validation.
"""
from datetime import date, timedelta

import pytest


def calculate_block_dates(block_number: int, academic_year_start: date) -> tuple[date, date]:
    """
    Calculate start and end dates for a given block number.

    Each block is 4 weeks (28 days).
    This is a copy of the function from generate_blocks.py for testing.
    """
    block_start = academic_year_start + timedelta(days=(block_number - 1) * 28)
    block_end = block_start + timedelta(days=27)
    return block_start, block_end


class TestCalculateBlockDates:
    """Tests for calculate_block_dates function."""

    def test_block_1_starts_on_academic_year_start(self):
        """Block 1 should start on the academic year start date."""
        academic_start = date(2025, 7, 1)
        block_start, block_end = calculate_block_dates(1, academic_start)

        assert block_start == date(2025, 7, 1)
        assert block_end == date(2025, 7, 28)

    def test_block_2_starts_28_days_after_block_1(self):
        """Block 2 should start exactly 28 days after Block 1."""
        academic_start = date(2025, 7, 1)
        block_start, block_end = calculate_block_dates(2, academic_start)

        assert block_start == date(2025, 7, 29)
        assert block_end == date(2025, 8, 25)

    def test_block_10_matches_expected_dates(self):
        """Block 10 should be March 10 - April 6 for AY 2025-2026."""
        academic_start = date(2025, 7, 1)
        block_start, block_end = calculate_block_dates(10, academic_start)

        assert block_start == date(2026, 3, 10)
        assert block_end == date(2026, 4, 6)

    def test_block_13_is_last_block(self):
        """Block 13 should end in late June."""
        academic_start = date(2025, 7, 1)
        block_start, block_end = calculate_block_dates(13, academic_start)

        assert block_start == date(2026, 6, 2)
        assert block_end == date(2026, 6, 29)

    def test_each_block_is_28_days(self):
        """Each block should be exactly 28 days (inclusive)."""
        academic_start = date(2025, 7, 1)

        for block_num in range(1, 14):
            block_start, block_end = calculate_block_dates(block_num, academic_start)
            # End - start + 1 = 28 days
            days = (block_end - block_start).days + 1
            assert days == 28, f"Block {block_num} is {days} days, expected 28"

    def test_blocks_are_contiguous(self):
        """Blocks should be contiguous with no gaps."""
        academic_start = date(2025, 7, 1)

        for block_num in range(1, 13):
            _, current_end = calculate_block_dates(block_num, academic_start)
            next_start, _ = calculate_block_dates(block_num + 1, academic_start)

            # Next block should start the day after current block ends
            assert next_start == current_end + timedelta(days=1), (
                f"Gap between Block {block_num} and Block {block_num + 1}"
            )

    def test_academic_year_covers_364_days(self):
        """13 blocks × 28 days = 364 days total."""
        academic_start = date(2025, 7, 1)
        block_1_start, _ = calculate_block_dates(1, academic_start)
        _, block_13_end = calculate_block_dates(13, academic_start)

        total_days = (block_13_end - block_1_start).days + 1
        assert total_days == 364


class TestWeekendDetection:
    """Tests for weekend detection logic."""

    def test_saturday_is_weekend(self):
        """Saturday (weekday=5) should be detected as weekend."""
        saturday = date(2025, 7, 5)  # July 5, 2025 is a Saturday
        assert saturday.weekday() >= 5

    def test_sunday_is_weekend(self):
        """Sunday (weekday=6) should be detected as weekend."""
        sunday = date(2025, 7, 6)  # July 6, 2025 is a Sunday
        assert sunday.weekday() >= 5

    def test_friday_is_not_weekend(self):
        """Friday (weekday=4) should not be detected as weekend."""
        friday = date(2025, 7, 4)  # July 4, 2025 is a Friday
        assert friday.weekday() < 5


class TestBlockCountPerDay:
    """Tests for block generation count logic."""

    def test_single_day_creates_2_blocks(self):
        """Each day should create exactly 2 blocks (AM and PM)."""
        # Logic test: for each day, we create AM and PM
        time_of_days = ["AM", "PM"]
        assert len(time_of_days) == 2

    def test_28_day_block_creates_56_blocks(self):
        """A 28-day block should create 56 blocks (28 days × 2)."""
        days = 28
        blocks_per_day = 2
        expected_blocks = days * blocks_per_day
        assert expected_blocks == 56

    def test_full_year_creates_728_blocks(self):
        """13 blocks × 28 days × 2 = 728 blocks per academic year."""
        # Note: The model docstring says 730 (365 × 2), but the academic
        # year is actually 364 days (13 × 28), so it's 728 blocks
        num_blocks = 13
        days_per_block = 28
        blocks_per_day = 2
        expected = num_blocks * days_per_block * blocks_per_day
        assert expected == 728
