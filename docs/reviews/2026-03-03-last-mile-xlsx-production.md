# The Last Mile: XLSX Production & The Offline User

**Date:** March 3, 2026
**Auditor:** Gemini CLI
**Focus:** Bridging the gap between the CP-SAT engine's output and the final XLSX artifact required by government coordinators who operate exclusively in Excel.

## 1. The Current Pipeline State

The current architecture is highly advanced on the backend but bottlenecked at the serialization layer.

**The Pipeline:**
`CP-SAT Engine (DB)` → `HalfDayJSONExporter` → `JSONToXlsxConverter` (via `XMLToXlsxConverter` base) → `CanonicalScheduleExportService` → **`.xlsx` file**

### What works incredibly well:
1. **The DB/Solver Accuracy:** We have mathematically proven (via the 47-constraint stress test) that the database contains a highly accurate, equitable schedule.
2. **Hidden Metadata Tracking:** The `__SYS_META__` and `__BASELINE__` sheets (implemented in PR #1190 / `e937e7fa`) are a massive win. They fingerprint the system-generated state so that when the coordinator re-imports the file, we can perfectly diff their "hand-jammed" edits.
3. **The Annual Workbook:** Exporting 14 sheets with a `YTD_SUMMARY` (PR #1219) solves the "invisible cross-block FMIT" problem.
4. **Data Validation Dropdowns:** Phase 3 of the Stateful Excel Roadmap was implemented. Cells now enforce valid code entry natively in Excel.

## 2. The "Last Mile" Problem

The "Last Mile" problem is not about the data being wrong; it's about the data *looking* wrong or being structured in a way that breaks coordinator trust immediately upon opening the file.

If a government employee opens the XLSX and sees raw data instead of the polished artifact they are used to, they will reject the system, regardless of the CP-SAT engine's brilliance.

### Current Failures in the Export (Based on `verify_block12_export.py` runs)

1. **Headcount Mismatch (The Filter Blind Spot):**
   - The verification script expects 10 faculty based on DB data, but the `schedule_grid` view shows 23, and the exported XLSX only shows 10.
   - **Why?** The export service (`canonical_schedule_export_service.py`) aggressively filters out `Dr. Faculty-*` placeholders, but the DB view does not. The coordinator opens the sheet and sees a different number of rows than what a DB report would show.
2. **Cell-by-Cell Mismatches (The Transformation Blind Spot):**
   - The test script reported **381 mismatches** out of 1456 cells.
   - **Why?** The export pipeline applies `display_abbrev` transformations (e.g., `fm_clinic` becomes `C`, `LV-AM` becomes `LV`). The raw DB holds the semantic code, but Excel holds the visual code. This isn't a "bug" in the schedule, but it breaks automated round-trip validation and makes the system look broken.
3. **The Call Row Rendering (The UX Blind Spot):**
   - The system puts overnight call assignments into the DB properly. But `xml_to_xlsx_converter.py` explicitly writes call staff names to the *AM column only*, adding a comment: `"User can manually merge AM/PM cells in Excel if desired."`
   - **Reality Check:** A coordinator will not manually merge 30 cells every month. If it doesn't look like their old template, they will reject it.

## 3. Our Blind Spots & Recommendations

We have been treating the Excel file as a "dumb rendering layer." We need to treat it as a **First-Class UI**.

### Blind Spot 1: We haven't finished Phase 2 of the Office.js Roadmap
We documented the incredible `OFFICEJS_AI_ROADMAP.md` (Medium #33) to build an AI sidebar inside Excel for them. But we skipped a critical prerequisite.
*   **The Gap:** `_write_anchor_sheet` exists in the code to map `person_id` to Excel rows, but we never wired the `__ANCHORS__` sheet into the `canonical_schedule_export_service.py` to be saved.
*   **The Fix:** Inject the `__ANCHORS__` sheet during the export loop. This makes the Excel file truly stateful and paves the way for the Office.js add-in.

### Blind Spot 2: Over-Reliance on "Display Abbreviations"
Translating `fm_clinic` to `C` on export means that when the file is re-imported, the system has to translate `C` back to `fm_clinic`.
*   **The Fix:** We should map the `__REF__` sheet's Data Validation dropdowns to use the semantic DB codes, OR we need a robust, bi-directional `display_abbrev` dictionary loaded into the import service. Currently, the import service relies on fuzzy matching, which will break when `C` maps to 4 different clinic types.

### Blind Spot 3: The Call Row formatting
*   **The Fix:** Update `_fill_call_row()` in `xml_to_xlsx_converter.py`. Instead of writing just to the AM cell, programmatically merge the AM and PM cells for that day via `sheet.merge_cells(start_row=r, start_column=c, end_row=r, end_column=c+1)`. It takes 3 lines of Python and saves the coordinator 10 minutes of manual formatting.

### Blind Spot 4: Leave Data Overlay
We successfully compute leave formulas (adding the `LV Days` column), but we rely on a brittle string match `=COUNTIF(..., "LV")`. If the system exports `LV-AM`, the formula fails.
*   **The Fix:** Ensure the dynamic Conditional Formatting (`_add_dynamic_cf`) and the `COUNTIF` formulas accurately account for the display transformations applied during JSON export.

## Summary of Actionable Next Steps

1. **Auto-Merge Call Cells:** Fix `xml_to_xlsx_converter.py` to merge AM/PM columns on rows 4 and 5 so the coordinator doesn't have to.
2. **Wire the `__ANCHORS__` sheet:** Enable Phase 2 of the stateful roadmap so deterministic round-trips work without fuzzy matching.
3. **Fix the View:** Update the SQL for `schedule_grid` to explicitly filter out `LIKE 'Dr. Faculty-%'` so DB validation tests match the Excel export output.
