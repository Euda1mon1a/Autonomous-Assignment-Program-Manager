#!/usr/bin/env python3
"""Generate inpatient time-off overrides from the Templates sheet."""
from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, Tuple

import pandas as pd

# Explicit mapping from Templates sheet row label -> rotation template display_abbreviation
ROW_TO_TEMPLATE_DISPLAY = {
    "Peds Ward (PedW) - Day schedule": "PEDSW",
    "Peds Ward (PedW) - Night Schedule": "PNF",
    # Add more mappings as needed (row label -> rotation_type)
    # "KAP L&D": "KAP",
    # "L&D Pit-Boss Nights*06/16": "LDNF",
}

DAY_MAP = {
    "Su": 0,
    "Sun": 0,
    "Sa": 6,
    "Sat": 6,
    "M": 1,
    "Mon": 1,
    "Tu": 2,
    "Tue": 2,
    "Wed": 3,
    "W": 3,
    "Th": 4,
    "Thu": 4,
    "Fr": 5,
    "Fri": 5,
}

TIME_OFF_CODES = {"OFF", "W"}


def _build_column_map(df: pd.DataFrame) -> Dict[int, Tuple[int, int, str]]:
    """Map column index -> (week_number, day_of_week, time_of_day)."""
    row0 = df.iloc[0].tolist()
    row1 = df.iloc[1].tolist()
    week = 1
    current_day = None
    first = True
    mapping: Dict[int, Tuple[int, int, str]] = {}

    for col in range(1, df.shape[1]):
        day_val = row0[col]
        time_val = row1[col]
        if pd.isna(day_val) and pd.isna(time_val):
            continue
        if pd.notna(day_val):
            current_day = str(day_val).strip()
        if not current_day:
            continue
        time_str = str(time_val).strip().lower() if pd.notna(time_val) else ""
        if current_day == "Th" and time_str == "am" and not first:
            week += 1
        first = False

        dow = DAY_MAP.get(current_day)
        if dow is None:
            continue
        mapping[col] = (week, dow, "AM" if time_str == "am" else "PM")
    return mapping


def _find_row_index(df: pd.DataFrame, label: str) -> int | None:
    labels = df.iloc[:, 0].astype(str).str.strip()
    matches = labels[labels == label]
    if matches.empty:
        return None
    return int(matches.index[0])


def build_overrides(
    df: pd.DataFrame, row_to_template_display: Dict[str, str]
) -> Dict[str, list[dict]]:
    column_map = _build_column_map(df)
    overrides: Dict[str, list[dict]] = {}

    for label, template_display in row_to_template_display.items():
        row_idx = _find_row_index(df, label)
        if row_idx is None:
            print(f"[warn] Row not found: {label}")
            continue
        for col, (week, dow, tod) in column_map.items():
            val = df.iat[row_idx, col]
            if pd.isna(val):
                continue
            code = str(val).strip().upper()
            if code not in TIME_OFF_CODES:
                continue
            overrides.setdefault(template_display, []).append(
                {
                    "week": week,
                    "day_of_week": dow,
                    "time_of_day": tod,
                    "code": code,
                    "row_label": label,
                }
            )

    # Sort entries for determinism
    for rotation, entries in overrides.items():
        entries.sort(key=lambda e: (e["week"], e["day_of_week"], e["time_of_day"]))
    return overrides


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input",
        default="/Users/aaronmontgomery/Desktop/Block 10 cleared of assignments and call v1(AutoRecovered).xlsx",
        help="Path to the Block 10 Excel file",
    )
    parser.add_argument(
        "--sheet",
        default="Templates",
        help="Sheet name with rotation templates",
    )
    parser.add_argument(
        "--output",
        default="data/inpatient_time_off_overrides.json",
        help="Output JSON path",
    )
    args = parser.parse_args()

    input_path = Path(args.input).expanduser()
    if not input_path.exists():
        raise SystemExit(f"Input file not found: {input_path}")

    df = pd.ExcelFile(input_path).parse(args.sheet, header=None)
    overrides = build_overrides(df, ROW_TO_TEMPLATE_DISPLAY)

    payload = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "source": input_path.name,
        "sheet": args.sheet,
        "key_type": "template_display_abbreviation",
        "row_to_template_display": ROW_TO_TEMPLATE_DISPLAY,
        "patterns": overrides,
    }

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2, sort_keys=True))
    print(f"Wrote {output_path} ({len(overrides)} rotations)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
