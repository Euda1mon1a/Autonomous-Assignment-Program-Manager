"""Schedule matrix coordinate mapper.

Pure-Python (date, provider) -> (row, col) index for Block Template 2 layout.
Zero external dependencies — works as a bridge between openpyxl and xlwings.

BT2 Layout Constants:
    - Column A(1): Rotation 1
    - Column B(2): Rotation 2
    - Column C(3): Template code
    - Column D(4): Role
    - Column E(5): Provider name
    - Column F(6)+: Schedule data, 2 columns per day (AM/PM)
    - Row 3: Date header row (merged cells, one per day)
    - Rows 9-30: Resident band
    - Rows 31-80: Faculty band
"""

from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any

# Import BT2 layout constants from the converter
BT2_COL_SCHEDULE_START = 6
BT2_COL_NAME = 5
COLS_PER_DAY = 2


class ScheduleMatrixMapper:
    """Library-agnostic (date, provider) -> (row, col) coordinate index.

    Provides the same coordinate system for both openpyxl and xlwings,
    enabling the hybrid architecture where openpyxl builds the workbook
    and xlwings applies finishing touches.
    """

    def __init__(
        self,
        block_start: date,
        block_end: date,
        row_mappings: dict[str, int],
    ) -> None:
        """Initialize with block dates and provider-to-row mappings.

        Args:
            block_start: First day of the block.
            block_end: Last day of the block.
            row_mappings: Dict mapping provider key (UUID or name) to Excel row number.
        """
        self.block_start = block_start
        self.block_end = block_end
        self.row_mappings = dict(row_mappings)
        self._reverse_rows: dict[int, str] = {v: k for k, v in row_mappings.items()}
        self._total_days = (block_end - block_start).days + 1

    def date_to_col(self, target_date: date, time_of_day: str) -> int:
        """Convert a (date, AM/PM) pair to an Excel column number.

        Args:
            target_date: The calendar date.
            time_of_day: "AM" or "PM" (case-insensitive).

        Returns:
            Excel column number (1-indexed).

        Raises:
            ValueError: If date is outside block range or invalid time_of_day.
        """
        day_offset = (target_date - self.block_start).days
        if day_offset < 0 or day_offset >= self._total_days:
            raise ValueError(
                f"Date {target_date} outside block range "
                f"({self.block_start} to {self.block_end})"
            )

        slot = 0 if time_of_day.upper() == "AM" else 1
        if time_of_day.upper() not in ("AM", "PM"):
            raise ValueError(f"time_of_day must be 'AM' or 'PM', got '{time_of_day}'")

        return BT2_COL_SCHEDULE_START + (day_offset * COLS_PER_DAY) + slot

    def provider_to_row(self, provider_key: str) -> int | None:
        """Look up the Excel row for a provider.

        Args:
            provider_key: UUID string or provider name.

        Returns:
            Excel row number, or None if not found.
        """
        return self.row_mappings.get(provider_key)

    def cell_address(
        self,
        provider_key: str,
        target_date: date,
        time_of_day: str,
    ) -> tuple[int, int] | None:
        """Get (row, col) for a specific provider/date/slot combination.

        Returns:
            (row, col) tuple, or None if provider not found.
        """
        row = self.provider_to_row(provider_key)
        if row is None:
            return None
        col = self.date_to_col(target_date, time_of_day)
        return (row, col)

    def col_to_date(self, col: int) -> tuple[date, str] | None:
        """Reverse mapping: Excel column -> (date, time_of_day).

        Args:
            col: Excel column number (1-indexed).

        Returns:
            (date, "AM"|"PM") tuple, or None if column is outside schedule range.
        """
        offset = col - BT2_COL_SCHEDULE_START
        if offset < 0:
            return None

        day_index = offset // COLS_PER_DAY
        if day_index >= self._total_days:
            return None

        slot_index = offset % COLS_PER_DAY
        target_date = self.block_start + timedelta(days=day_index)
        time_of_day = "AM" if slot_index == 0 else "PM"
        return (target_date, time_of_day)

    def row_to_provider(self, row: int) -> str | None:
        """Reverse mapping: Excel row -> provider key.

        Args:
            row: Excel row number (1-indexed).

        Returns:
            Provider key (UUID or name), or None if row not mapped.
        """
        return self._reverse_rows.get(row)

    def all_schedule_cells(self) -> list[tuple[int, int, str, date, str]]:
        """Enumerate every cell in the schedule grid.

        Returns:
            List of (row, col, provider_key, date, time_of_day) tuples.
        """
        cells = []
        for provider_key, row in self.row_mappings.items():
            current = self.block_start
            while current <= self.block_end:
                for tod in ("AM", "PM"):
                    col = self.date_to_col(current, tod)
                    cells.append((row, col, provider_key, current, tod))
                current += timedelta(days=1)
        return cells

    @classmethod
    def from_worksheet(
        cls,
        ws: Any,
        anchor_search_rows: range = range(1, 10),
        name_col: int = BT2_COL_NAME,
    ) -> ScheduleMatrixMapper:
        """Build a mapper by discovering the layout of an existing worksheet.

        Scans the worksheet to find:
        1. The date header row (contains "Date:" label or date objects)
        2. Provider names in the name column

        Works with both openpyxl Worksheet and xlwings Sheet objects
        via duck-typed cell access.

        Args:
            ws: An openpyxl Worksheet or xlwings Sheet.
            anchor_search_rows: Range of rows to search for the date anchor.
            name_col: Column number containing provider names.

        Returns:
            A ScheduleMatrixMapper instance.

        Raises:
            ValueError: If date anchor row cannot be found.
        """
        # Detect whether this is openpyxl or xlwings
        is_openpyxl = hasattr(ws, "cell") and callable(ws.cell)

        def _read_cell(row: int, col: int) -> Any:
            if is_openpyxl:
                return ws.cell(row=row, column=col).value
            else:
                # xlwings: ws.range((row, col)).value
                return ws.range((row, col)).value

        # 1. Find the date anchor row
        date_row = None
        schedule_start_col = None

        for r in anchor_search_rows:
            for c in range(1, 10):
                val = _read_cell(r, c)
                if val is None:
                    continue

                # Look for "Date:" label
                if isinstance(val, str) and val.strip().lower() in ("date:", "date"):
                    date_row = r
                    schedule_start_col = c + 1
                    break

                # Or look for a date value in the expected schedule start area
                if c >= BT2_COL_SCHEDULE_START and isinstance(val, (date, datetime)):
                    date_row = r
                    schedule_start_col = c
                    break
            if date_row is not None:
                break

        if date_row is None:
            raise ValueError(
                "Could not find date anchor row. Expected 'Date:' label or date "
                f"objects in rows {anchor_search_rows.start}-{anchor_search_rows.stop - 1}."
            )

        # 2. Read dates from the header row to determine block range
        dates: list[date] = []
        assert schedule_start_col is not None  # guaranteed by date_row check above
        c = schedule_start_col
        max_col = schedule_start_col + 200  # safety limit
        while c < max_col:
            val = _read_cell(date_row, c)
            if val is None:
                break
            if isinstance(val, datetime):
                dates.append(val.date())
                c += COLS_PER_DAY  # dates are merged across AM/PM
            elif isinstance(val, date):
                dates.append(val)
                c += COLS_PER_DAY
            else:
                c += 1

        if not dates:
            raise ValueError(f"No dates found in row {date_row}.")

        block_start = min(dates)
        block_end = max(dates)

        # 3. Read provider names from the name column
        row_mappings: dict[str, int] = {}
        max_row = date_row + 200  # safety limit
        for r in range(date_row + 1, max_row):
            val = _read_cell(r, name_col)
            if val is None:
                # Allow sparse rows (black dividers, etc.)
                continue
            name = str(val).strip()
            if name and name.lower() not in ("none", ""):
                row_mappings[name] = r

        return cls(
            block_start=block_start,
            block_end=block_end,
            row_mappings=row_mappings,
        )
