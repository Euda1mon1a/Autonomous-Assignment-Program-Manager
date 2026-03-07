# Decision Log: Excel Export Formatting & Transformation

## Context
The system-generated CP-SAT Excel schedule export (`Test_Annual_Workbook`) natively produces a highly structured, data-dense layout. However, the administrative staff (the "Muggles") expect a very specific, hand-jammed format (e.g., `Block 11 and 12 AY 25-26 pulled 05 MAR 2026 1512.xlsx`).

To bridge this gap, two distinct technical approaches were evaluated:

1. **Native Engine Overrides**: Injecting hardcoded `openpyxl` formatting rules (colors, merged cells, row heights, summary formulas) directly into the backend `xml_to_xlsx_converter.py`.
2. **Post-Processing Transformers (ML/Heuristics)**: Utilizing external Python scripts (`schedule_transformer_v2.py` and `schedule_transformer_v4.py`) that take the raw DB output and transform it. `v4` notably attempted to use an SLM (Small Language Model) and CatBoost to heuristically predict "human-intended" display codes based on surrounding context.

## Current State & Observations
* We injected `openpyxl` DataValidation relaxations (`showErrorMessage=False`) into the core engine to allow free-text overrides while keeping dropdowns. This was highly successful.
* We injected some macro-formatting (frozen panes at `E8`, column widths) natively into the engine.
* However, applying strict color fills natively began failing on individual cell levels, highlighting a fundamental disconnect between how LLMs/automated systems "see" spreadsheets vs. the reality of human-applied conditional formatting.
* Surprisingly, the `v4` ML Transformer script performed exceptionally well at replicating the macro-structure of the hand-jammed sheet, despite dropping individual cell colorization.

## Decision: PAUSE NATIVE FORMATTING INJECTIONS
Given that the ML-driven transformer script got much closer to the desired macro-format than expected, we are halting further native hardcoding of formatting rules into the `xml_to_xlsx_converter.py` export engine.

## Next Steps / Needs Further Discussion
We need to hold a focused architectural discussion on the final path forward for the "Last Mile" Excel export. The choices are:

1. **The Native Path:** Abandon the transformer script entirely. Painstakingly map every single cell color, border, and merged header into the Python `openpyxl` engine.
2. **The Pipeline Path:** Let the backend generate the ugly, mathematically pure DB export. Build a seamless pipeline where that file is automatically passed to a deterministic, rule-based version of the transformer script (similar to `v2`) before being delivered to the user.
3. **The ML Path:** Continue refining the `v4` SLM/heuristic transformer if contextual disambiguation (e.g., figuring out what "ELEC" means based on resident history) proves to be a hard requirement that deterministic rules cannot solve.

**Status:** Awaiting architectural consensus before modifying the export pipeline further.
