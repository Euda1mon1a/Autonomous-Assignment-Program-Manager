"""Academic block date utilities with Thursday-Wednesday alignment.

Military residency programs use 13 academic blocks per year:
- Block 0: Orientation (July 1 through day before first Thursday)
- Blocks 1-12: Standard 28-day blocks (Thursday to Wednesday)
- Block 13: Variable length, ends June 30

All regular blocks (1-12) align to Thursday-Wednesday boundaries for
consistent weekly scheduling patterns.

Example for AY 2025-2026:
- July 1, 2025 is a Tuesday
- Block 0: July 1-2 (2 days, orientation)
- Block 1: July 3 (Thu) - July 30 (Wed), 28 days
- Block 12: June 4-June 3 (Thu-Wed)
- Block 13: June 4 (Thu) - June 30 (Tue), 27 days
"""

from dataclasses import dataclass
from datetime import date, timedelta
from functools import lru_cache


# Thursday = 3 in Python's weekday() (Monday=0)
THURSDAY = 3
WEDNESDAY = 2
BLOCK_DURATION_DAYS = 28


@dataclass(frozen=True)
class BlockDates:
    """Immutable representation of an academic block's date range."""

    block_number: int
    academic_year: int
    start_date: date
    end_date: date

    @property
    def duration_days(self) -> int:
        """Number of days in the block (inclusive)."""
        return (self.end_date - self.start_date).days + 1

    @property
    def is_orientation(self) -> bool:
        """True if this is Block 0 (orientation)."""
        return self.block_number == 0

    @property
    def is_final_block(self) -> bool:
        """True if this is Block 13 (variable length, ends June 30)."""
        return self.block_number == 13

    @property
    def is_standard_block(self) -> bool:
        """True if this is a standard 28-day block (1-12)."""
        return 1 <= self.block_number <= 12


@lru_cache(maxsize=64)
def get_first_thursday(academic_year: int) -> date:
    """
    Get the first Thursday on or after July 1 for an academic year.

    This marks the start of Block 1. If July 1 is a Thursday, Block 1
    starts on July 1 and Block 0 has zero days.

    Args:
        academic_year: Starting year of academic year (e.g., 2025 for AY 2025-2026)

    Returns:
        First Thursday on or after July 1
    """
    july_1 = date(academic_year, 7, 1)
    days_until_thursday = (THURSDAY - july_1.weekday()) % 7
    return july_1 + timedelta(days=days_until_thursday)


@lru_cache(maxsize=64)
def get_academic_year_end(academic_year: int) -> date:
    """
    Get June 30 of the following year (end of academic year).

    Args:
        academic_year: Starting year of academic year

    Returns:
        June 30 of the following year
    """
    return date(academic_year + 1, 6, 30)


@lru_cache(maxsize=1024)
def get_block_dates(block_number: int, academic_year: int) -> BlockDates:
    """
    Calculate the start and end dates for an academic block.

    Block alignment rules:
    - Block 0: July 1 through day before first Thursday (orientation, 0-6 days)
    - Blocks 1-12: 28 days each, Thursday start, Wednesday end
    - Block 13: Thursday start, June 30 end (variable length, 22-30 days)

    Args:
        block_number: Block number (0-13)
        academic_year: Starting year of academic year (e.g., 2025 for AY 2025-2026)

    Returns:
        BlockDates with start_date and end_date

    Raises:
        ValueError: If block_number is not in range 0-13
    """
    if not 0 <= block_number <= 13:
        raise ValueError(f"Block number must be 0-13, got {block_number}")

    july_1 = date(academic_year, 7, 1)
    first_thursday = get_first_thursday(academic_year)
    june_30 = get_academic_year_end(academic_year)

    if block_number == 0:
        # Orientation block: July 1 through day before first Thursday
        if first_thursday == july_1:
            # July 1 is Thursday - Block 0 has zero days
            # Return July 1 with same start/end to indicate empty block
            start_date = july_1
            end_date = july_1 - timedelta(days=1)  # June 30 previous year
        else:
            start_date = july_1
            end_date = first_thursday - timedelta(days=1)
    elif block_number == 13:
        # Final block: starts after Block 12, ends June 30
        block_12_end = first_thursday + timedelta(days=(12 * BLOCK_DURATION_DAYS) - 1)
        start_date = block_12_end + timedelta(days=1)
        end_date = june_30
    else:
        # Standard blocks 1-12: 28 days each, Thursday-Wednesday
        start_date = first_thursday + timedelta(
            days=(block_number - 1) * BLOCK_DURATION_DAYS
        )
        end_date = start_date + timedelta(days=BLOCK_DURATION_DAYS - 1)

    return BlockDates(
        block_number=block_number,
        academic_year=academic_year,
        start_date=start_date,
        end_date=end_date,
    )


def get_block_number_for_date(target_date: date) -> tuple[int, int]:
    """
    Calculate which academic block a date falls within.

    Args:
        target_date: Date to find block number for

    Returns:
        Tuple of (block_number, academic_year)

    Note:
        This handles the edge case where Block 0 may have zero days
        (when July 1 is a Thursday).
    """
    # Determine academic year
    if target_date.month >= 7:
        academic_year = target_date.year
    else:
        academic_year = target_date.year - 1

    july_1 = date(academic_year, 7, 1)
    first_thursday = get_first_thursday(academic_year)

    # Check if in Block 0 (orientation)
    if target_date < first_thursday and target_date >= july_1:
        return 0, academic_year

    # Calculate days since first Thursday
    days_since_block_1 = (target_date - first_thursday).days

    if days_since_block_1 < 0:
        # Before July 1 - belongs to previous academic year's Block 13
        prev_year = academic_year - 1
        return 13, prev_year

    # Calculate block number (1-indexed)
    block_number = (days_since_block_1 // BLOCK_DURATION_DAYS) + 1

    # Cap at Block 13
    if block_number > 13:
        block_number = 13

    return block_number, academic_year


def get_block_half(target_date: date) -> int:
    """
    Determine which half of the block a date falls in.

    Args:
        target_date: Date to check

    Returns:
        1 for days 1-14 (first half)
        2 for days 15+ (second half)
    """
    block_number, academic_year = get_block_number_for_date(target_date)
    block = get_block_dates(block_number, academic_year)

    day_in_block = (target_date - block.start_date).days + 1
    return 1 if day_in_block <= 14 else 2


def get_all_block_dates(academic_year: int) -> list[BlockDates]:
    """
    Get date ranges for all blocks in an academic year.

    Args:
        academic_year: Starting year of academic year

    Returns:
        List of BlockDates for blocks 0-13
    """
    return [get_block_dates(block_num, academic_year) for block_num in range(14)]


def validate_block_alignment(academic_year: int) -> dict:
    """
    Validate that block dates are correctly aligned for an academic year.

    Returns a validation report useful for testing and debugging.

    Args:
        academic_year: Starting year to validate

    Returns:
        Dictionary with validation results and any issues found
    """
    issues = []
    blocks = get_all_block_dates(academic_year)

    july_1 = date(academic_year, 7, 1)
    june_30 = get_academic_year_end(academic_year)

    # Check Block 0 starts on July 1
    if blocks[0].duration_days > 0 and blocks[0].start_date != july_1:
        issues.append(f"Block 0 should start on July 1, got {blocks[0].start_date}")

    # Check Block 13 ends on June 30
    if blocks[13].end_date != june_30:
        issues.append(f"Block 13 should end on June 30, got {blocks[13].end_date}")

    # Check standard blocks are 28 days and aligned Thursday-Wednesday
    for i in range(1, 13):
        block = blocks[i]
        if block.duration_days != 28:
            issues.append(f"Block {i} should be 28 days, got {block.duration_days}")
        if block.start_date.weekday() != THURSDAY:
            issues.append(
                f"Block {i} should start on Thursday, "
                f"got {block.start_date.strftime('%A')}"
            )
        if block.end_date.weekday() != WEDNESDAY:
            issues.append(
                f"Block {i} should end on Wednesday, "
                f"got {block.end_date.strftime('%A')}"
            )

    # Check blocks are contiguous (no gaps)
    for i in range(len(blocks) - 1):
        if blocks[i].duration_days > 0:  # Skip zero-day Block 0
            expected_next_start = blocks[i].end_date + timedelta(days=1)
            if blocks[i + 1].start_date != expected_next_start:
                issues.append(
                    f"Gap between Block {i} and {i + 1}: "
                    f"{blocks[i].end_date} -> {blocks[i + 1].start_date}"
                )

    # Calculate total days
    total_days = sum(max(0, b.duration_days) for b in blocks)
    expected_days = (june_30 - july_1).days + 1  # 365 or 366

    return {
        "academic_year": academic_year,
        "valid": len(issues) == 0,
        "issues": issues,
        "total_days_covered": total_days,
        "expected_days": expected_days,
        "blocks_summary": [
            {
                "block": b.block_number,
                "start": b.start_date.isoformat(),
                "end": b.end_date.isoformat(),
                "days": b.duration_days,
                "start_day": b.start_date.strftime("%A"),
                "end_day": b.end_date.strftime("%A"),
            }
            for b in blocks
        ],
    }
