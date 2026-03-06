"""Tests for ScheduleMatrixMapper — pure Python, no external deps."""

from datetime import date, timedelta
from unittest.mock import MagicMock

import pytest

from app.services.schedule_matrix_mapper import (
    BT2_COL_SCHEDULE_START,
    COLS_PER_DAY,
    ScheduleMatrixMapper,
)


@pytest.fixture
def block_dates():
    """Standard 28-day block (Block 12: May 7 – Jun 3, 2026)."""
    return date(2026, 5, 7), date(2026, 6, 3)


@pytest.fixture
def row_mappings():
    return {
        "uuid-resident-1": 9,
        "uuid-resident-2": 10,
        "uuid-faculty-1": 31,
        "Hernandez, Christian": 11,
    }


@pytest.fixture
def mapper(block_dates, row_mappings):
    start, end = block_dates
    return ScheduleMatrixMapper(start, end, row_mappings)


class TestDateToCol:
    def test_first_day_am(self, mapper, block_dates):
        start, _ = block_dates
        col = mapper.date_to_col(start, "AM")
        assert col == BT2_COL_SCHEDULE_START  # Column 6

    def test_first_day_pm(self, mapper, block_dates):
        start, _ = block_dates
        col = mapper.date_to_col(start, "PM")
        assert col == BT2_COL_SCHEDULE_START + 1  # Column 7

    def test_second_day_am(self, mapper, block_dates):
        start, _ = block_dates
        col = mapper.date_to_col(start + timedelta(days=1), "AM")
        assert col == BT2_COL_SCHEDULE_START + COLS_PER_DAY  # Column 8

    def test_last_day_pm(self, mapper, block_dates):
        _, end = block_dates
        col = mapper.date_to_col(end, "PM")
        total_days = (end - block_dates[0]).days
        expected = BT2_COL_SCHEDULE_START + (total_days * COLS_PER_DAY) + 1
        assert col == expected

    def test_case_insensitive(self, mapper, block_dates):
        start, _ = block_dates
        assert mapper.date_to_col(start, "am") == mapper.date_to_col(start, "AM")
        assert mapper.date_to_col(start, "pm") == mapper.date_to_col(start, "PM")

    def test_date_before_block_raises(self, mapper, block_dates):
        start, _ = block_dates
        with pytest.raises(ValueError, match="outside block range"):
            mapper.date_to_col(start - timedelta(days=1), "AM")

    def test_date_after_block_raises(self, mapper, block_dates):
        _, end = block_dates
        with pytest.raises(ValueError, match="outside block range"):
            mapper.date_to_col(end + timedelta(days=1), "AM")

    def test_invalid_time_of_day_raises(self, mapper, block_dates):
        start, _ = block_dates
        with pytest.raises(ValueError, match="must be 'AM' or 'PM'"):
            mapper.date_to_col(start, "NOON")


class TestProviderToRow:
    def test_uuid_lookup(self, mapper):
        assert mapper.provider_to_row("uuid-resident-1") == 9

    def test_name_lookup(self, mapper):
        assert mapper.provider_to_row("Hernandez, Christian") == 11

    def test_missing_returns_none(self, mapper):
        assert mapper.provider_to_row("nonexistent") is None


class TestCellAddress:
    def test_valid_address(self, mapper, block_dates):
        start, _ = block_dates
        result = mapper.cell_address("uuid-resident-1", start, "AM")
        assert result == (9, BT2_COL_SCHEDULE_START)

    def test_missing_provider_returns_none(self, mapper, block_dates):
        start, _ = block_dates
        result = mapper.cell_address("nonexistent", start, "AM")
        assert result is None


class TestColToDate:
    def test_round_trip_all_days(self, mapper, block_dates):
        start, end = block_dates
        current = start
        while current <= end:
            for tod in ("AM", "PM"):
                col = mapper.date_to_col(current, tod)
                result = mapper.col_to_date(col)
                assert result is not None
                assert result[0] == current
                assert result[1] == tod
            current += timedelta(days=1)

    def test_column_before_schedule_returns_none(self, mapper):
        assert mapper.col_to_date(1) is None
        assert mapper.col_to_date(5) is None

    def test_column_after_schedule_returns_none(self, mapper):
        assert mapper.col_to_date(500) is None


class TestRowToProvider:
    def test_round_trip(self, mapper):
        for key, row in mapper.row_mappings.items():
            assert mapper.row_to_provider(row) == key

    def test_unmapped_row_returns_none(self, mapper):
        assert mapper.row_to_provider(999) is None


class TestAllScheduleCells:
    def test_count(self, mapper, block_dates):
        start, end = block_dates
        total_days = (end - start).days + 1
        num_providers = len(mapper.row_mappings)
        expected = num_providers * total_days * 2  # AM + PM
        cells = mapper.all_schedule_cells()
        assert len(cells) == expected

    def test_cell_structure(self, mapper):
        cells = mapper.all_schedule_cells()
        row, col, key, d, tod = cells[0]
        assert isinstance(row, int)
        assert isinstance(col, int)
        assert isinstance(key, str)
        assert isinstance(d, date)
        assert tod in ("AM", "PM")


class TestFromWorksheet:
    def _make_mock_ws(self):
        """Create a mock openpyxl worksheet with BT2-like layout."""
        cells = {}

        # Date anchor: row 3, column 5 = "Date:"
        cells[(3, 5)] = "Date:"
        # Dates start at column 6, merged across AM/PM
        block_start = date(2026, 5, 7)
        for day in range(28):
            d = block_start + timedelta(days=day)
            col = 6 + (day * 2)
            cells[(3, col)] = d

        # Provider names in column 5
        cells[(9, 5)] = "Sawyer, Tessa"
        cells[(10, 5)] = "Sloss, Meleighe"
        cells[(11, 5)] = "Hernandez, Christian"
        # Row 12 = black divider (None)
        cells[(13, 5)] = "Faculty, Test"

        ws = MagicMock()
        ws.cell = MagicMock(
            side_effect=lambda row, column: MagicMock(value=cells.get((row, column)))
        )

        return ws

    def test_discovers_dates(self):
        ws = self._make_mock_ws()
        mapper = ScheduleMatrixMapper.from_worksheet(ws)
        assert mapper.block_start == date(2026, 5, 7)
        assert mapper.block_end == date(2026, 6, 3)

    def test_discovers_providers(self):
        ws = self._make_mock_ws()
        mapper = ScheduleMatrixMapper.from_worksheet(ws)
        assert "Sawyer, Tessa" in mapper.row_mappings
        assert "Hernandez, Christian" in mapper.row_mappings
        assert mapper.row_mappings["Sawyer, Tessa"] == 9
        assert mapper.row_mappings["Faculty, Test"] == 13

    def test_skips_none_rows(self):
        ws = self._make_mock_ws()
        mapper = ScheduleMatrixMapper.from_worksheet(ws)
        # Row 12 had None — should not be in mappings
        assert 12 not in mapper._reverse_rows

    def test_no_date_anchor_raises(self):
        ws = MagicMock()
        ws.cell = MagicMock(return_value=MagicMock(value=None))
        with pytest.raises(ValueError, match="Could not find date anchor"):
            ScheduleMatrixMapper.from_worksheet(ws)
