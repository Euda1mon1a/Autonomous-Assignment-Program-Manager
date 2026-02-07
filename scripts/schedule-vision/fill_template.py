"""Fill BlockTemplate2 with ML-predicted display codes.

Standalone script that:
  1. Loads Block 10 DB export JSON
  2. Runs ML predictions (or loads pre-computed)
  3. Fills the official BlockTemplate2_Official.xlsx template
  4. Updates dates, rotations, call row, and schedule cells
  5. Outputs a formatted Excel file

Usage:
    python fill_template.py \
        --db-json /tmp/block10_data.json \
        --model data/model_all.pkl \
        --template ~/Autonomous-Assignment-Program-Manager/backend/data/BlockTemplate2_Official.xlsx \
        --structure ~/Autonomous-Assignment-Program-Manager/backend/data/BlockTemplate2_Structure.xml \
        --output data/Block10_ML.xlsx
"""

from __future__ import annotations

import argparse
import json
from datetime import date, datetime, timedelta
from pathlib import Path
from xml.etree import ElementTree

import joblib
import numpy as np
from openpyxl import load_workbook
from openpyxl.cell.cell import MergedCell

# Template layout constants
COL_ROTATION1 = 1
COL_ROTATION2 = 2
COL_TEMPLATE = 3
COL_ROLE = 4
COL_NAME = 5
COL_SCHEDULE_START = 6
COLS_PER_DAY = 2
MAX_DAYS = 28
ROW_DATES = 3
ROW_STAFF_CALL = 4
ROW_RES_CALL = 5


# ── Name matching ──────────────────────────────────────────

def _last_name(name: str) -> str:
    """Extract last name from either 'First Last' or 'Last, First'."""
    name = name.strip()
    if "," in name:
        return name.split(",")[0].strip().lower()
    parts = name.split()
    return parts[-1].lower() if parts else name.lower()


def load_name_map(structure_path: str) -> dict[str, int]:
    """Parse BlockTemplate2_Structure.xml -> {db_name: row}."""
    tree = ElementTree.parse(structure_path)
    root = tree.getroot()
    mapping = {}
    for tag in ("resident", "person"):
        for elem in root.iter(tag):
            name = elem.get("name", "")
            row = elem.get("row")
            if name and row and name not in ("Unassigned", "Unassigned-NF"):
                mapping[name] = int(row)
    return mapping


def resolve_row(db_name: str, name_map: dict[str, int]) -> int | None:
    """Match DB name to template row. Exact first, then last-name fallback."""
    if db_name in name_map:
        return name_map[db_name]
    db_last = _last_name(db_name)
    for xml_name, row in name_map.items():
        xml_last = _last_name(xml_name)
        if db_last == xml_last:
            return row
    return None


# ── ML prediction ──────────────────────────────────────────

def _encode_single(feat: dict, encoders: dict, cat_fields: list[str]) -> np.ndarray:
    """Encode a single feature dict for RF prediction."""
    row = []
    # Numeric features (must match learn.py NUM_FIELDS order)
    row.append(feat.get("pgy_level") or 0)
    row.append(feat.get("block_number") or 0)
    val = feat.get("day_of_week")
    row.append(val if val is not None else -1)
    row.append(1 if feat.get("is_weekend") else 0)
    row.append(feat.get("day_index") or 0)
    row.append(1 if feat.get("half") == "pm" else 0)
    row.append(1 if feat.get("font_bold") else 0)
    row.append(1 if feat.get("db_matches_template") else 0)
    row.append(feat.get("week_in_block") or 0)
    # Categorical features
    for field in cat_fields:
        val = feat.get(field) or "__NONE__"
        enc = encoders[field]
        if val in enc.classes_:
            row.append(enc.transform([val])[0])
        else:
            row.append(len(enc.classes_))
    return np.array(row, dtype=np.float32)


def predict_cell(
    rf, encoders, label_enc, cat_fields,
    db_code: str, person_type: str,
    rot1: str, rot2: str, pgy: int,
    block_number: int, day_index: int,
    day_date: date, half: str,
    other_half_code: str,
) -> str:
    """Predict display code for a single cell."""
    if not db_code:
        return ""

    feat = {
        "pgy_level": pgy,
        "block_number": block_number,
        "day_of_week": day_date.weekday(),
        "is_weekend": day_date.weekday() in (5, 6),
        "day_index": day_index,
        "half": half,
        "font_bold": False,
        "db_matches_template": False,
        "week_in_block": day_index // 7,
        "rotation1": rot1,
        "rotation2": rot2,
        "template": "",
        "role": "",
        "db_code": db_code,
        "template_expected": "",
        "db_other_half": other_half_code,
        "fill_rgb": "",
        "font_rgb": "",
        "person_type": person_type,
    }

    row = _encode_single(feat, encoders, cat_fields)
    pred_idx = rf.predict([row])[0]
    return label_enc.inverse_transform([pred_idx])[0]


# ── Template filling ──────────────────────────────────────

def _write_cell(ws, row, col, value):
    """Write a value to a cell, skipping merged cells."""
    cell = ws.cell(row=row, column=col)
    if not isinstance(cell, MergedCell):
        cell.value = value


def fill_template(
    db_json_path: str,
    model_path: str,
    template_path: str,
    structure_path: str,
    output_path: str,
    block_number: int = 10,
    preserve_identity: bool = True,
):
    """Fill the template with ML-predicted display codes."""
    # Load data
    data = json.loads(Path(db_json_path).read_text())
    block_start = date.fromisoformat(data["block_start"])
    block_end = date.fromisoformat(data["block_end"])

    # Load model
    model_data = joblib.load(model_path)
    rf = model_data["rf"]
    encoders = model_data["encoders"]
    label_enc = encoders["__label__"]
    cat_fields = [
        "rotation1", "rotation2", "template", "role", "db_code",
        "template_expected", "db_other_half", "fill_rgb", "font_rgb",
        "person_type",
    ]

    # Load template
    wb = load_workbook(template_path)
    ws = wb.active

    # Load name mapping
    name_map = load_name_map(structure_path)

    print(f"  Block {block_number}: {block_start} to {block_end}")
    print(f"  Template: {template_path}")
    print(f"  Model: {model_path}")
    print(f"  Name map: {len(name_map)} entries")

    # ── 1. Update dates in row 3 ──
    for day_idx in range(MAX_DAYS):
        day_date = block_start + timedelta(days=day_idx)
        col = COL_SCHEDULE_START + day_idx * COLS_PER_DAY
        cell = ws.cell(row=ROW_DATES, column=col)
        if not isinstance(cell, MergedCell):
            cell.value = datetime(day_date.year, day_date.month, day_date.day)

    # Update block number (row 1, col C)
    _write_cell(ws, 1, 3, str(block_number))

    # Update date range string (row 4, col C)
    range_str = (
        f"{block_start.strftime('%d%b').lstrip('0')}-"
        f"{block_end.strftime('%d%b').lstrip('0')}"
    )
    _write_cell(ws, ROW_STAFF_CALL, 3, range_str)

    print(f"  Updated dates: {block_start} to {block_end}")

    # ── 2. Fill schedule data per person ──
    matched = 0
    skipped = 0
    total_cells = 0
    total_changed = 0

    faculty_names = {p["name"] for p in data.get("faculty", [])}

    for person in data.get("residents", []) + data.get("faculty", []):
        name = person["name"]
        row = resolve_row(name, name_map)
        if row is None:
            print(f"  SKIP: No row for '{name}'")
            skipped += 1
            continue

        matched += 1
        is_faculty = name in faculty_names
        person_type = "faculty" if is_faculty else "resident"
        rot1 = person.get("rotation1") or ""
        rot2 = person.get("rotation2") or ""
        pgy = person.get("pgy") or 0

        # Write rotation columns (A, B) unless preserving template identity
        if not preserve_identity:
            _write_cell(ws, row, COL_ROTATION1, rot1 or None)
            _write_cell(ws, row, COL_ROTATION2, rot2 or None)

        # Fill daily schedule codes
        for i, day in enumerate(person.get("days", [])):
            if i >= MAX_DAYS:
                break

            day_date = date.fromisoformat(day["date"])
            raw_am = day.get("am") or ""
            raw_pm = day.get("pm") or ""

            # Predict AM
            am_pred = predict_cell(
                rf, encoders, label_enc, cat_fields,
                raw_am, person_type, rot1, rot2, pgy,
                block_number, i, day_date, "am", raw_pm,
            )
            # Predict PM
            pm_pred = predict_cell(
                rf, encoders, label_enc, cat_fields,
                raw_pm, person_type, rot1, rot2, pgy,
                block_number, i, day_date, "pm", raw_am,
            )

            # Weekend empty cells → "W" if no DB code
            is_weekend = day_date.weekday() in (5, 6)
            if is_weekend and not raw_am and not am_pred:
                am_pred = "W"
            if is_weekend and not raw_pm and not pm_pred:
                pm_pred = "W"

            am_col = COL_SCHEDULE_START + i * COLS_PER_DAY
            _write_cell(ws, row, am_col, am_pred or None)
            _write_cell(ws, row, am_col + 1, pm_pred or None)

            for code, raw in [(am_pred, raw_am), (pm_pred, raw_pm)]:
                if code or raw:
                    total_cells += 1
                    if code != raw:
                        total_changed += 1

    # ── 3. Fill call row (row 4) ──
    call_written = 0
    for night in data.get("call", {}).get("nights", []):
        night_date = date.fromisoformat(night["date"])
        offset = (night_date - block_start).days
        if 0 <= offset < MAX_DAYS:
            staff = night.get("staff", "")
            if staff:
                last = staff.split()[-1] if " " in staff else staff
                col = COL_SCHEDULE_START + offset * COLS_PER_DAY
                _write_cell(ws, ROW_STAFF_CALL, col, last)
                call_written += 1

    # ── 4. Save ──
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    wb.save(out)
    wb.close()

    print(f"\n  Results:")
    print(f"    Matched: {matched} people ({skipped} skipped)")
    print(f"    Cells filled: {total_cells}")
    print(f"    ML changed: {total_changed} ({100*total_changed/total_cells:.1f}%)")
    print(f"    Call nights: {call_written}")
    print(f"    Output: {out}")


def main():
    parser = argparse.ArgumentParser(
        description="Fill BlockTemplate2 with ML-predicted display codes",
    )
    parser.add_argument(
        "--db-json", default="/tmp/block10_data.json",
        help="DB export JSON",
    )
    parser.add_argument(
        "--model", default="data/model_all.pkl",
        help="Trained model from learn.py",
    )
    parser.add_argument(
        "--template",
        default=str(
            Path.home()
            / "Autonomous-Assignment-Program-Manager"
            / "backend/data/BlockTemplate2_Official.xlsx"
        ),
        help="BlockTemplate2 template XLSX",
    )
    parser.add_argument(
        "--structure",
        default=str(
            Path.home()
            / "Autonomous-Assignment-Program-Manager"
            / "backend/data/BlockTemplate2_Structure.xml"
        ),
        help="BlockTemplate2_Structure.xml",
    )
    parser.add_argument(
        "--output", default="data/Block10_ML.xlsx",
        help="Output XLSX path",
    )
    parser.add_argument(
        "--block", type=int, default=10,
        help="Block number",
    )
    parser.add_argument(
        "--overwrite-identity", action="store_true",
        help="Overwrite template rotation/name columns (default: preserve)",
    )
    args = parser.parse_args()

    fill_template(
        args.db_json, args.model, args.template,
        args.structure, args.output, args.block,
        preserve_identity=not args.overwrite_identity,
    )


if __name__ == "__main__":
    main()
