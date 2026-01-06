"""Tests for academic block date utilities.

Verifies Thursday-Wednesday block alignment across multiple academic years.
"""

from datetime import date, timedelta

import pytest

from app.utils.academic_blocks import (
    BLOCK_DURATION_DAYS,
    THURSDAY,
    WEDNESDAY,
    BlockDates,
    get_all_block_dates,
    get_block_dates,
    get_block_half,
    get_block_number_for_date,
    get_first_thursday,
    validate_block_alignment,
)


class TestGetFirstThursday:
    """Tests for get_first_thursday function."""

    def test_2024_july_1_is_monday(self):
        """2024: July 1 is Monday, first Thursday is July 4."""
        result = get_first_thursday(2024)
        assert result == date(2024, 7, 4)
        assert result.weekday() == THURSDAY

    def test_2025_july_1_is_tuesday(self):
        """2025: July 1 is Tuesday, first Thursday is July 3."""
        result = get_first_thursday(2025)
        assert result == date(2025, 7, 3)
        assert result.weekday() == THURSDAY

    def test_2026_july_1_is_wednesday(self):
        """2026: July 1 is Wednesday, first Thursday is July 2."""
        result = get_first_thursday(2026)
        assert result == date(2026, 7, 2)
        assert result.weekday() == THURSDAY

    def test_2027_july_1_is_thursday(self):
        """2027: July 1 is Thursday, first Thursday is July 1."""
        result = get_first_thursday(2027)
        assert result == date(2027, 7, 1)
        assert result.weekday() == THURSDAY


class TestGetBlockDates:
    """Tests for get_block_dates function."""

    def test_block_0_orientation(self):
        """Block 0 is orientation, July 1 to day before first Thursday."""
        # 2025: July 1 (Tue) to July 2 (Wed)
        block = get_block_dates(0, 2025)
        assert block.block_number == 0
        assert block.academic_year == 2025
        assert block.start_date == date(2025, 7, 1)
        assert block.end_date == date(2025, 7, 2)
        assert block.duration_days == 2
        assert block.is_orientation

    def test_block_0_when_july_1_is_thursday(self):
        """Block 0 has zero days when July 1 is Thursday."""
        # 2027: July 1 is Thursday
        block = get_block_dates(0, 2027)
        assert block.start_date == date(2027, 7, 1)
        assert block.end_date == date(2027, 6, 30)  # Previous day
        assert block.duration_days == 0

    def test_block_1_starts_thursday(self):
        """Block 1 starts on first Thursday."""
        block = get_block_dates(1, 2025)
        assert block.start_date == date(2025, 7, 3)  # First Thursday
        assert block.start_date.weekday() == THURSDAY

    def test_block_1_ends_wednesday(self):
        """Block 1 ends on Wednesday (28 days later)."""
        block = get_block_dates(1, 2025)
        assert block.end_date == date(2025, 7, 30)  # Wednesday
        assert block.end_date.weekday() == WEDNESDAY

    def test_standard_blocks_are_28_days(self):
        """Blocks 1-12 are exactly 28 days."""
        for block_num in range(1, 13):
            block = get_block_dates(block_num, 2025)
            assert block.duration_days == BLOCK_DURATION_DAYS
            assert block.is_standard_block

    def test_standard_blocks_start_thursday_end_wednesday(self):
        """All standard blocks start Thursday and end Wednesday."""
        for block_num in range(1, 13):
            block = get_block_dates(block_num, 2025)
            assert block.start_date.weekday() == THURSDAY
            assert block.end_date.weekday() == WEDNESDAY

    def test_block_13_ends_june_30(self):
        """Block 13 ends on June 30 of next year."""
        block = get_block_dates(13, 2025)
        assert block.end_date == date(2026, 6, 30)
        assert block.is_final_block

    def test_block_13_variable_length(self):
        """Block 13 has variable length (ends June 30)."""
        # Different years have different Block 13 lengths
        b13_2024 = get_block_dates(13, 2024)
        b13_2025 = get_block_dates(13, 2025)
        b13_2026 = get_block_dates(13, 2026)
        b13_2027 = get_block_dates(13, 2027)

        assert b13_2024.duration_days == 26
        assert b13_2025.duration_days == 27
        assert b13_2026.duration_days == 28
        assert b13_2027.duration_days == 30

    def test_blocks_are_contiguous(self):
        """Blocks have no gaps between them."""
        blocks = get_all_block_dates(2025)

        for i in range(len(blocks) - 1):
            if blocks[i].duration_days > 0:
                expected_next = blocks[i].end_date + timedelta(days=1)
                assert blocks[i + 1].start_date == expected_next

    def test_invalid_block_number_raises_error(self):
        """Invalid block numbers raise ValueError."""
        with pytest.raises(ValueError):
            get_block_dates(-1, 2025)

        with pytest.raises(ValueError):
            get_block_dates(14, 2025)

    def test_caching_works(self):
        """Results are cached for performance."""
        # Call twice - should be cached
        block1 = get_block_dates(5, 2025)
        block2 = get_block_dates(5, 2025)
        assert block1 is block2  # Same object from cache


class TestGetBlockNumberForDate:
    """Tests for get_block_number_for_date function."""

    def test_july_1_in_block_0(self):
        """July 1 falls in Block 0 (unless it's Thursday)."""
        block_num, year = get_block_number_for_date(date(2025, 7, 1))
        assert block_num == 0
        assert year == 2025

    def test_first_thursday_in_block_1(self):
        """First Thursday is in Block 1."""
        block_num, year = get_block_number_for_date(date(2025, 7, 3))
        assert block_num == 1
        assert year == 2025

    def test_june_30_in_block_13(self):
        """June 30 of next year is in Block 13."""
        block_num, year = get_block_number_for_date(date(2026, 6, 30))
        assert block_num == 13
        assert year == 2025  # Academic year 2025-2026

    def test_mid_block_date(self):
        """Date in middle of a block returns correct block number."""
        # Block 5 for 2025: starts after 4*28 = 112 days from first Thursday
        # First Thursday 2025 = July 3, +112 = Oct 23
        block_num, year = get_block_number_for_date(date(2025, 10, 25))
        assert block_num == 5
        assert year == 2025

    def test_all_dates_in_year_have_valid_block(self):
        """Every date in academic year maps to a valid block 0-13."""
        start = date(2025, 7, 1)
        end = date(2026, 6, 30)
        current = start

        while current <= end:
            block_num, year = get_block_number_for_date(current)
            assert 0 <= block_num <= 13
            assert year == 2025
            current += timedelta(days=1)


class TestGetBlockHalf:
    """Tests for get_block_half function."""

    def test_first_day_is_first_half(self):
        """First day of block is in first half."""
        # Block 1 starts July 3, 2025
        assert get_block_half(date(2025, 7, 3)) == 1

    def test_day_14_is_first_half(self):
        """Day 14 of block is still first half."""
        # Block 1 day 14 = July 3 + 13 = July 16
        assert get_block_half(date(2025, 7, 16)) == 1

    def test_day_15_is_second_half(self):
        """Day 15 of block is second half."""
        # Block 1 day 15 = July 3 + 14 = July 17
        assert get_block_half(date(2025, 7, 17)) == 2

    def test_last_day_is_second_half(self):
        """Last day of block is in second half."""
        # Block 1 ends July 30
        assert get_block_half(date(2025, 7, 30)) == 2


class TestValidateBlockAlignment:
    """Tests for validate_block_alignment function."""

    def test_2024_valid(self):
        """AY 2024-2025 passes validation."""
        result = validate_block_alignment(2024)
        assert result["valid"] is True
        assert len(result["issues"]) == 0
        assert result["total_days_covered"] == 365

    def test_2025_valid(self):
        """AY 2025-2026 passes validation."""
        result = validate_block_alignment(2025)
        assert result["valid"] is True
        assert len(result["issues"]) == 0
        assert result["total_days_covered"] == 365

    def test_2026_valid(self):
        """AY 2026-2027 passes validation."""
        result = validate_block_alignment(2026)
        assert result["valid"] is True
        assert len(result["issues"]) == 0
        assert result["total_days_covered"] == 365

    def test_2027_valid_leap_year(self):
        """AY 2027-2028 (leap year) passes validation."""
        result = validate_block_alignment(2027)
        assert result["valid"] is True
        assert len(result["issues"]) == 0
        assert result["total_days_covered"] == 366  # Leap year


class TestBlockDatesDataclass:
    """Tests for BlockDates dataclass properties."""

    def test_is_orientation(self):
        """Block 0 is marked as orientation."""
        block = get_block_dates(0, 2025)
        assert block.is_orientation is True
        assert block.is_standard_block is False
        assert block.is_final_block is False

    def test_is_standard_block(self):
        """Blocks 1-12 are marked as standard."""
        for i in range(1, 13):
            block = get_block_dates(i, 2025)
            assert block.is_orientation is False
            assert block.is_standard_block is True
            assert block.is_final_block is False

    def test_is_final_block(self):
        """Block 13 is marked as final."""
        block = get_block_dates(13, 2025)
        assert block.is_orientation is False
        assert block.is_standard_block is False
        assert block.is_final_block is True


class TestEdgeCases:
    """Edge case and boundary tests."""

    def test_transition_between_blocks(self):
        """Block transitions happen correctly at midnight Wednesday->Thursday."""
        # Block 1 ends July 30 (Wed), Block 2 starts July 31 (Thu)
        block1_last_day = date(2025, 7, 30)
        block2_first_day = date(2025, 7, 31)

        b1, _ = get_block_number_for_date(block1_last_day)
        b2, _ = get_block_number_for_date(block2_first_day)

        assert b1 == 1
        assert b2 == 2

    def test_year_transition(self):
        """Block number calculation works across calendar year boundary."""
        # December 31, 2025 -> January 1, 2026 (both in AY 2025-2026)
        dec31, year1 = get_block_number_for_date(date(2025, 12, 31))
        jan1, year2 = get_block_number_for_date(date(2026, 1, 1))

        # Both should be in academic year 2025
        assert year1 == 2025
        assert year2 == 2025

        # Block numbers should be in valid range
        assert 1 <= dec31 <= 13
        assert 1 <= jan1 <= 13

    def test_dates_before_academic_year(self):
        """Dates before July 1 belong to previous academic year's Block 13."""
        # June 29, 2025 is in AY 2024-2025, Block 13
        block_num, year = get_block_number_for_date(date(2025, 6, 29))
        assert block_num == 13
        assert year == 2024

    def test_february_29_leap_year(self):
        """Leap year Feb 29 is handled correctly."""
        # Feb 29, 2028 (AY 2027-2028)
        block_num, year = get_block_number_for_date(date(2028, 2, 29))
        assert 1 <= block_num <= 13
        assert year == 2027
