"""xlwings bridge for Excel native finishing pass.

Post-processes openpyxl-generated workbooks by opening them in Excel
via xlwings, letting Excel evaluate CF rules and formulas natively.

All xlwings imports are inside function bodies to keep this module
importable without xlwings installed.
"""

from __future__ import annotations

import random
from pathlib import Path
from typing import Any

from app.core.logging import get_logger
from app.services.tamc_color_scheme import TAMCColorScheme

logger = get_logger(__name__)


class XlwingsBridge:
    """Post-processing bridge using xlwings to leverage Excel's native engine.

    Operations:
    1. Open openpyxl-generated .xlsx in Excel (headless)
    2. Recalculate all formulas (Excel evaluates CF, SUMIF, COUNTIF)
    3. Verify CF-rendered colors match TAMC scheme expectations
    4. Apply print layout (area, orientation, headers/footers)
    5. Save and close

    All operations use try/finally to ensure app.quit() — no orphaned
    Excel processes.
    """

    def __init__(
        self,
        color_scheme: TAMCColorScheme,
        visible: bool = False,
        timeout_seconds: int = 120,
    ) -> None:
        self.color_scheme = color_scheme
        self.visible = visible
        self.timeout_seconds = timeout_seconds

    def apply_finishing_pass(
        self,
        xlsx_path: Path,
        sheet_name: str = "Block Template2",
    ) -> Path:
        """Open workbook in Excel, evaluate CF/formulas, apply finishing formatting.

        Args:
            xlsx_path: Path to the openpyxl-generated .xlsx file.
            sheet_name: Name of the main schedule sheet.

        Returns:
            Path to the finished file (same as input — edited in-place).
        """
        import xlwings as xw

        app = None
        try:
            app = xw.App(visible=self.visible)
            app.screen_updating = False
            app.display_alerts = False

            wb = app.books.open(str(xlsx_path))
            ws = wb.sheets[sheet_name]

            # Force Excel to evaluate all formulas and CF rules
            app.calculate()

            # Verify CF colors match TAMC scheme on a sample of cells
            mismatches = self._verify_cf_colors(ws)
            if mismatches:
                logger.warning(
                    "CF color mismatches found: %d cells differ from TAMC scheme",
                    len(mismatches),
                )
                for m in mismatches[:5]:
                    logger.debug(
                        "  Cell (%d,%d): code=%s expected=%s actual=%s",
                        m["row"],
                        m["col"],
                        m["code"],
                        m["expected"],
                        m["actual"],
                    )

            # Apply print layout
            self._apply_print_layout(ws)

            wb.save()
            wb.close()

            logger.info(
                "xlwings finishing pass complete: %s (%d CF mismatches)",
                xlsx_path.name,
                len(mismatches),
            )
            return xlsx_path

        finally:
            if app is not None:
                try:
                    app.screen_updating = True
                    app.display_alerts = True
                    app.quit()
                except Exception:
                    logger.warning("Failed to quit Excel cleanly", exc_info=True)

    def read_rendered_colors(
        self,
        xlsx_path: Path,
        sheet_name: str,
        cells: list[tuple[int, int]],
    ) -> dict[tuple[int, int], tuple[int, int, int] | None]:
        """Read the actual rendered background color of cells after CF evaluation.

        This is the core capability openpyxl cannot provide — it reads CF
        *rules* but cannot evaluate them to determine the displayed color.

        Args:
            xlsx_path: Path to the Excel file.
            sheet_name: Sheet name to read from.
            cells: List of (row, col) tuples to read.

        Returns:
            Dict mapping (row, col) -> (r, g, b) tuple, or None if no fill.
        """
        import xlwings as xw

        app = None
        result: dict[tuple[int, int], tuple[int, int, int] | None] = {}

        try:
            app = xw.App(visible=False)
            app.screen_updating = False
            app.display_alerts = False

            wb = app.books.open(str(xlsx_path))
            ws = wb.sheets[sheet_name]

            # Force recalculation so CF is evaluated
            app.calculate()

            for row, col in cells:
                cell = ws.range((row, col))
                color = cell.color
                if color is not None:
                    result[(row, col)] = (int(color[0]), int(color[1]), int(color[2]))
                else:
                    result[(row, col)] = None

            wb.close()

        finally:
            if app is not None:
                try:
                    app.quit()
                except Exception:
                    pass

        return result

    def surgical_edit(
        self,
        xlsx_path: Path,
        sheet_name: str,
        edits: dict[tuple[int, int], Any],
    ) -> Path:
        """Write only specified cells into an existing workbook.

        Opens the file in Excel and writes cell values surgically.
        Because Excel manages the file, ALL existing formatting, CF rules,
        merged cells, and comments are preserved perfectly.

        Args:
            xlsx_path: Path to the existing Excel file.
            sheet_name: Sheet name to edit.
            edits: Dict mapping (row, col) -> new value.

        Returns:
            Path to the edited file (same as input).
        """
        import xlwings as xw

        app = None
        try:
            app = xw.App(visible=self.visible)
            app.screen_updating = False
            app.display_alerts = False

            wb = app.books.open(str(xlsx_path))
            ws = wb.sheets[sheet_name]

            for (row, col), value in edits.items():
                ws.range((row, col)).value = value

            wb.save()
            wb.close()

            logger.info(
                "Surgical edit complete: %d cells updated in %s [%s]",
                len(edits),
                xlsx_path.name,
                sheet_name,
            )
            return xlsx_path

        finally:
            if app is not None:
                try:
                    app.screen_updating = True
                    app.display_alerts = True
                    app.quit()
                except Exception:
                    logger.warning("Failed to quit Excel cleanly", exc_info=True)

    def _verify_cf_colors(
        self,
        ws: Any,
        sample_size: int = 20,
    ) -> list[dict[str, Any]]:
        """Spot-check rendered cell colors against TAMC scheme.

        Samples cells from the schedule grid that contain known codes,
        reads their actual background color, and compares against the
        expected color from the TAMC scheme.

        Args:
            ws: xlwings Sheet object.
            sample_size: Max number of cells to check.

        Returns:
            List of mismatch dicts with row, col, code, expected, actual.
        """
        mismatches: list[dict[str, Any]] = []

        # Scan schedule grid for cells with known codes
        # Grid: rows 9-69, columns 6-61 (BT2 layout)
        candidates: list[tuple[int, int, str]] = []
        for row in range(9, 45):
            for col in range(6, 62):
                val = ws.range((row, col)).value
                if val is not None:
                    code = str(val).strip()
                    expected_color = self.color_scheme.get_code_color(code)
                    if expected_color:
                        candidates.append((row, col, code))

        # Random sample to avoid checking thousands of cells
        if len(candidates) > sample_size:
            candidates = random.sample(candidates, sample_size)

        for row, col, code in candidates:
            cell = ws.range((row, col))
            actual_rgb = cell.color  # (r, g, b) tuple or None

            expected_hex = self.color_scheme.get_code_color(code)
            if expected_hex is None:
                continue

            # Convert expected hex (ARGB or RGB) to RGB for comparison
            # Strip "FF" alpha prefix if present (openpyxl convention)
            h = expected_hex
            if len(h) == 8 and h[:2].upper() == "FF":
                h = h[2:]
            # Take last 6 chars as RGB
            h = h[-6:] if len(h) >= 6 else h
            try:
                er = int(h[0:2], 16)
                eg = int(h[2:4], 16)
                eb = int(h[4:6], 16)
            except (ValueError, IndexError):
                continue

            if actual_rgb is None:
                mismatches.append(
                    {
                        "row": row,
                        "col": col,
                        "code": code,
                        "expected": f"({er},{eg},{eb})",
                        "actual": "None",
                    }
                )
            else:
                ar, ag, ab = int(actual_rgb[0]), int(actual_rgb[1]), int(actual_rgb[2])
                # Allow tolerance of ±5 for rounding differences
                if abs(ar - er) > 5 or abs(ag - eg) > 5 or abs(ab - eb) > 5:
                    mismatches.append(
                        {
                            "row": row,
                            "col": col,
                            "code": code,
                            "expected": f"({er},{eg},{eb})",
                            "actual": f"({ar},{ag},{ab})",
                        }
                    )

        return mismatches

    def _apply_print_layout(self, ws: Any) -> None:
        """Set print area, orientation, and fit-to-page for the schedule sheet."""
        try:
            # Landscape orientation for wide schedule grid
            ws.api.PageSetup.Orientation = 2  # xlLandscape

            # Fit all columns to one page wide, allow multiple pages tall
            ws.api.PageSetup.FitToPagesWide = 1
            ws.api.PageSetup.FitToPagesTall = False

            # Set print area to cover the schedule grid
            ws.api.PageSetup.PrintArea = "$A$1:$BI$45"

            logger.debug("Print layout applied to %s", ws.name)
        except Exception:
            logger.debug("Could not apply print layout", exc_info=True)
