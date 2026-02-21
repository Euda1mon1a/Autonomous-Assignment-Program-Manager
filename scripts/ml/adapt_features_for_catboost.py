#!/usr/bin/env python3
"""Adapt extract.py features to extract_universal.py format for CatBoost.

Maps column names and decomposes hex RGB to float channels.
"""

import argparse
import json
import sys
from pathlib import Path


def hex_to_rgb(hex_str: str | None) -> tuple[float, float, float]:
    """Convert hex color (e.g., 'FF9BC2E6') to (r, g, b) floats 0-1."""
    if not hex_str or hex_str == "None":
        return (0.0, 0.0, 0.0)
    h = hex_str.lstrip("#")
    if len(h) == 8:
        h = h[2:]  # Strip alpha
    if len(h) != 6:
        return (0.0, 0.0, 0.0)
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return (r / 255.0, g / 255.0, b / 255.0)


def main():
    parser = argparse.ArgumentParser(description="Adapt extract.py features for CatBoost")
    parser.add_argument("input", help="Input features JSON")
    parser.add_argument("output", nargs="?", default=None, help="Output path")
    parser.add_argument("--academic-year", type=int, default=None,
                        help="Override academic year (default: read from input data, fallback 2025)")
    args = parser.parse_args()

    inp = Path(args.input)
    out = Path(args.output) if args.output else inp.with_name("features_catboost.json")

    data = json.loads(inp.read_text())
    adapted = []
    for f in data:
        if not f.get("truth_code"):
            continue

        fill_r, fill_g, fill_b = hex_to_rgb(f.get("fill_rgb"))
        font_r, font_g, font_b = hex_to_rgb(f.get("font_rgb"))

        adapted.append({
            "cell_text": f["truth_code"],
            "rotation": f.get("rotation1") or "",
            "person_type": f.get("person_type", "resident"),
            "half": f.get("half", "am"),
            "team_or_template": f.get("template") or "",
            "role_raw": f.get("role") or "",
            "pgy_level": f.get("pgy_level", 0) or 0,
            "day_of_week": f.get("day_of_week", 0),
            "is_weekend": 1 if f.get("is_weekend") else 0,
            "day_index": f.get("day_index", 0),
            "week_in_block": f.get("week_in_block", 0),
            "fill_r": fill_r,
            "fill_g": fill_g,
            "fill_b": fill_b,
            "font_r": font_r,
            "font_g": font_g,
            "font_b": font_b,
            "font_bold": 1 if f.get("font_bold") else 0,
            "has_fill": 1 if f.get("fill_rgb") else 0,
            "has_font_color": 1 if f.get("font_rgb") else 0,
            "academic_year": f.get("academic_year") or args.academic_year or 2025,
            "block_number": f.get("block_number", 0),
            "row_position": f.get("row", 0),
            "prev_same_half": f.get("prev_code") or "",
            "next_same_half": f.get("next_code") or "",
            "other_half": f.get("other_half_code") or "",
        })

    out.write_text(json.dumps(adapted, indent=None))
    print(f"Adapted {len(adapted)} features → {out}")
    print(f"  Unique cell_text: {len(set(f['cell_text'] for f in adapted))}")


if __name__ == "__main__":
    main()
