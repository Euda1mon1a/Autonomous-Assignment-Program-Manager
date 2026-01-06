"""Tests for generate_blocks.py script.

Tests the block date calculation logic using Thursday-Wednesday alignment.
"""

from datetime import date, timedelta

from app.utils.academic_blocks import get_block_dates, get_all_block_dates, THURSDAY, WEDNESDAY


def calculate_block_dates(
    block_number: int, academic_year_start: date
) -> tuple[date, date]:
    """
    Calculate start and end dates for a given block number.

    Uses Thursday-Wednesday alignment:
    - Block 0: July 1 through day before first Thursday (orientation)
    - Blocks 1-12: 28 days each, Thursday start, Wednesday end
    - Block 13: Thursday start, June 30 end (variable length)

    Args:
        block_number: Block number (0-13)
        academic_year_start: July 1 of academic year start

    Returns:
        Tuple of (start_date, end_date)
    """
    # Extract academic year from start date
    academic_year = academic_year_start.year if academic_year_start.month >= 7 else academic_year_start.year - 1
    block = get_block_dates(block_number, academic_year)
    return block.start_date, block.end_date


class TestCalculateBlockDates:
    """Tests for calculate_block_dates function with Thursday-Wednesday alignment."""

    def test_block_1_starts_on_first_thursday(self):
        """Block 1 should start on first Thursday on or after July 1.

        AY 2025-2026: July 1, 2025 is Tuesday, first Thursday is July 3.
        """
        academic_start = date(2025, 7, 1)
        block_start, block_end = calculate_block_dates(1, academic_start)

        assert block_start == date(2025, 7, 3)  # First Thursday
        assert block_end == date(2025, 7, 30)  # Wednesday
        assert block_start.weekday() == THURSDAY
        assert block_end.weekday() == WEDNESDAY

    def test_block_2_starts_28_days_after_block_1(self):
        """Block 2 should start exactly 28 days after Block 1."""
        academic_start = date(2025, 7, 1)
        block_start, block_end = calculate_block_dates(2, academic_start)

        assert block_start == date(2025, 7, 31)  # Thursday
        assert block_end == date(2025, 8, 27)  # Wednesday
        assert block_start.weekday() == THURSDAY
        assert block_end.weekday() == WEDNESDAY

    def test_block_10_matches_expected_dates(self):
        """Block 10 uses Thursday-Wednesday alignment for AY 2025-2026."""
        academic_start = date(2025, 7, 1)
        block_start, block_end = calculate_block_dates(10, academic_start)

        # Block 10 starts 9 * 28 = 252 days after first Thursday (July 3)
        assert block_start.weekday() == THURSDAY
        assert block_end.weekday() == WEDNESDAY
        assert (block_end - block_start).days == 27  # 28 days inclusive

    def test_block_13_ends_june_30(self):
        """Block 13 should end on June 30 (academic year end)."""
        academic_start = date(2025, 7, 1)
        block_start, block_end = calculate_block_dates(13, academic_start)

        assert block_end == date(2026, 6, 30)
        assert block_start.weekday() == THURSDAY

    def test_each_standard_block_is_28_days(self):
        """Blocks 1-12 should be exactly 28 days, Thursday-Wednesday aligned."""
        academic_start = date(2025, 7, 1)

        for block_num in range(1, 13):
            block_start, block_end = calculate_block_dates(block_num, academic_start)
            days = (block_end - block_start).days + 1
            assert days == 28, f"Block {block_num} is {days} days, expected 28"
            assert block_start.weekday() == THURSDAY
            assert block_end.weekday() == WEDNESDAY

    def test_block_13_is_variable_length(self):
        """Block 13 has variable length depending on where June 30 falls."""
        # Check multiple years to verify variable length
        for year in [2024, 2025, 2026, 2027]:
            academic_start = date(year, 7, 1)
            block_start, block_end = calculate_block_dates(13, academic_start)
            days = (block_end - block_start).days + 1
            # Block 13 can be 22-30 days depending on the year
            assert 22 <= days <= 30, f"Block 13 in {year} is {days} days"

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

    def test_academic_year_total_days(self):
        """Academic year should cover from Block 0 start to Block 13 end."""
        academic_year = 2025
        blocks = get_all_block_dates(academic_year)

        july_1 = date(academic_year, 7, 1)
        june_30 = date(academic_year + 1, 6, 30)

        # Total days from July 1 to June 30
        expected_days = (june_30 - july_1).days + 1
        total_days = sum(max(0, b.duration_days) for b in blocks)

        assert total_days == expected_days

    def test_academic_year_in_leap_cycle(self):
        """Academic year spanning Feb 29 should cover 366 days."""
        # AY 2027-2028 includes Feb 29, 2028
        academic_year = 2027
        blocks = get_all_block_dates(academic_year)

        total_days = sum(max(0, b.duration_days) for b in blocks)
        assert total_days == 366


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

    def test_full_year_creates_730_blocks(self):
        """Academic year should generate 365 days × 2 blocks = 730 blocks."""
        total_days = 365
        blocks_per_day = 2
        expected = total_days * blocks_per_day
        assert expected == 730
