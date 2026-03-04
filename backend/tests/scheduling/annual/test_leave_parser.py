"""Tests for leave request date parsing and block mapping."""

from __future__ import annotations

from datetime import date

import pytest

from app.scheduling.annual.context import map_leave_to_blocks
from app.scheduling.annual.leave_parser import parse_dates_from_text
from app.utils.academic_blocks import get_all_block_dates


# ── parse_dates_from_text ─────────────────────────────────────────────────────


class TestParseDatesFromText:
    """Free-text date extraction from leave request cells."""

    def test_same_month_range(self):
        start, end = parse_dates_from_text("July 14-20 PNW, Flights booked")
        assert start == date(2026, 7, 14)
        assert end == date(2026, 7, 20)

    def test_cross_month_range(self):
        start, end = parse_dates_from_text("Dec 28-Jan 3")
        assert start == date(2026, 12, 28)
        assert end == date(2027, 1, 3)

    def test_cross_month_with_year(self):
        start, end = parse_dates_from_text("August 29-Sep 4, 2026")
        assert start == date(2026, 8, 29)
        assert end == date(2026, 9, 4)

    def test_single_date(self):
        start, end = parse_dates_from_text("Aug 12th 1st day skool")
        assert start == date(2026, 8, 12)
        assert end == date(2026, 8, 12)

    def test_ordinal_suffixes(self):
        start, end = parse_dates_from_text("Oct 3rd-5th wedding")
        assert start == date(2026, 10, 3)
        assert end == date(2026, 10, 5)

    def test_no_dates_returns_none(self):
        start, end = parse_dates_from_text("TBD")
        assert start is None
        assert end is None

    def test_sept_abbreviation(self):
        start, end = parse_dates_from_text("Sept 15-20")
        assert start == date(2026, 9, 15)
        assert end == date(2026, 9, 20)

    def test_en_dash(self):
        start, end = parse_dates_from_text("Nov 22\u201328 Thanksgiving")
        assert start == date(2026, 11, 22)
        assert end == date(2026, 11, 28)

    def test_spring_months_default_to_2027(self):
        """Months < 7 default to 2027 (spring of AY 2026-27)."""
        start, end = parse_dates_from_text("March 10-15")
        assert start == date(2027, 3, 10)
        assert end == date(2027, 3, 15)

    def test_fall_months_default_to_2026(self):
        """Months >= 7 default to 2026 (fall of AY 2026-27)."""
        start, end = parse_dates_from_text("October 1-7")
        assert start == date(2026, 10, 1)
        assert end == date(2026, 10, 7)

    def test_explicit_year_overrides_default(self):
        start, end = parse_dates_from_text("Jan 5-10, 2027")
        assert start == date(2027, 1, 5)
        assert end == date(2027, 1, 10)

    def test_cross_year_with_explicit_year(self):
        """Dec 28-Jan 3, 2026 → end year rolls to 2027."""
        start, end = parse_dates_from_text("Dec 28-Jan 3, 2026")
        assert start == date(2026, 12, 28)
        assert end == date(2027, 1, 3)

    def test_full_month_name(self):
        start, end = parse_dates_from_text("February 14-21")
        assert start == date(2027, 2, 14)
        assert end == date(2027, 2, 21)

    def test_empty_string(self):
        start, end = parse_dates_from_text("")
        assert start is None
        assert end is None

    def test_no_recognizable_month(self):
        start, end = parse_dates_from_text("14-20 vacation")
        assert start is None
        assert end is None


# ── map_leave_to_blocks ───────────────────────────────────────────────────────


class TestMapLeaveToBlocks:
    """Date range → block number mapping using AY 2026-27 calendar."""

    @pytest.fixture
    def blocks_2026(self):
        """AY 2026-27 blocks (excluding Block 0)."""
        return [b for b in get_all_block_dates(2026) if b.block_number > 0]

    def test_single_day_in_block(self, blocks_2026):
        block1 = next(b for b in blocks_2026 if b.block_number == 1)
        result = map_leave_to_blocks(block1.start_date, block1.start_date, blocks_2026)
        assert result == [1]

    def test_entire_block(self, blocks_2026):
        block3 = next(b for b in blocks_2026 if b.block_number == 3)
        result = map_leave_to_blocks(block3.start_date, block3.end_date, blocks_2026)
        assert result == [3]

    def test_cross_block_boundary(self, blocks_2026):
        block4 = next(b for b in blocks_2026 if b.block_number == 4)
        block5 = next(b for b in blocks_2026 if b.block_number == 5)
        result = map_leave_to_blocks(block4.end_date, block5.start_date, blocks_2026)
        assert 4 in result
        assert 5 in result
        assert len(result) == 2

    def test_spanning_three_blocks(self, blocks_2026):
        block6 = next(b for b in blocks_2026 if b.block_number == 6)
        block8 = next(b for b in blocks_2026 if b.block_number == 8)
        result = map_leave_to_blocks(block6.start_date, block8.end_date, blocks_2026)
        assert set(result) == {6, 7, 8}

    def test_no_overlap(self, blocks_2026):
        result = map_leave_to_blocks(date(2020, 1, 1), date(2020, 1, 5), blocks_2026)
        assert result == []

    def test_last_day_of_block(self, blocks_2026):
        block2 = next(b for b in blocks_2026 if b.block_number == 2)
        result = map_leave_to_blocks(block2.end_date, block2.end_date, blocks_2026)
        assert result == [2]

    def test_block_13(self, blocks_2026):
        block13 = next(b for b in blocks_2026 if b.block_number == 13)
        result = map_leave_to_blocks(
            block13.start_date, block13.start_date, blocks_2026
        )
        assert result == [13]
