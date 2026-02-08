"""Generate HTML visual diff report comparing ML predictions vs ground truth.

Shows each person's schedule as a colored grid, highlighting cells where
ML predictions differ from the handjam truth and from the DB export.

Usage:
    python compare.py --features data/features.json --model data/model.pkl
    open data/report.html
"""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path

import joblib
import numpy as np

# TAMC color scheme — map display codes to background colors
CODE_COLORS: dict[str, str] = {
    "C": "#FFD700",      # Gold — FM Clinic
    "CC": "#FFD700",     # Gold — Continuity Clinic
    "C40": "#FFD700",    # Gold — Intern Clinic
    "C30": "#FFD700",    # Gold — Clinic variant
    "CCC": "#FFD700",    # Gold — CCC
    "C-I": "#FFD700",    # Gold — Clinic Initial
    "C-N": "#FFD700",    # Gold — Clinic New
    "LEC": "#87CEEB",    # Light blue — Lecture
    "ADV": "#87CEEB",    # Light blue — Advising
    "W": "#E8E8E8",      # Light gray — Weekend
    "OFF": "#E8E8E8",    # Light gray — Off
    "NF": "#9370DB",     # Medium purple — Night Float
    "PedsNF": "#9370DB", # Medium purple
    "L&D": "#FF69B4",    # Hot pink — L&D NF
    "FMIT": "#90EE90",   # Light green — FM Inpatient
    "IMW": "#FFA07A",    # Light salmon — Internal Med
    "KAP": "#DDA0DD",    # Plum — Kapiolani
    "PedW": "#FFB6C1",   # Light pink — Peds Ward
    "GYN": "#FF69B4",    # Hot pink — GYN
    "SM": "#98FB98",     # Pale green — Sports Med
    "aSM": "#98FB98",    # Pale green
    "GME": "#B0C4DE",    # Light steel blue
    "AT": "#B0C4DE",     # Light steel blue
    "DO": "#B0C4DE",     # Light steel blue
    "CV": "#B0C4DE",     # Light steel blue
    "DFM": "#B0C4DE",    # Light steel blue
    "LV": "#FFE4B5",     # Moccasin — Leave
    "DEP": "#FF6347",    # Tomato — Deployment
    "TDY": "#FF6347",    # Tomato — TDY
    "USAFP": "#FFE4B5",  # Moccasin
    "SLV": "#FFE4B5",    # Moccasin — Sabbatical Leave
    "PR": "#FFDAB9",     # Peach — Procedures
    "US": "#FFDAB9",     # Peach — Ultrasound
    "NEURO": "#DEB887",  # Burlywood — Neuro
    "Endo": "#DEB887",   # Burlywood — Endo
    "ENT": "#DEB887",    # Burlywood
    "Ophtho": "#DEB887", # Burlywood
    "URO": "#DEB887",    # Burlywood
    "OB": "#FF69B4",     # Hot pink — OB
    "PI": "#ADD8E6",     # Light blue
    "PCAT": "#ADD8E6",   # Light blue
    "SIM": "#ADD8E6",    # Light blue
    "HC": "#90EE90",     # Light green
    "HV": "#90EE90",     # Light green
    "ADM": "#B0C4DE",    # Light steel blue
    "FLX": "#E8E8E8",    # Light gray
    "VAS": "#DEB887",    # Burlywood
    "PC": "#FAFAD2",     # Light goldenrod
}

DEFAULT_COLOR = "#FFFFFF"


def _get_color(code: str) -> str:
    return CODE_COLORS.get(code, DEFAULT_COLOR)


def _encode_for_prediction(
    features: list[dict],
    encoders: dict,
    feature_names: list[str],
    cat_fields: list[str],
) -> np.ndarray:
    """Re-encode features for model prediction."""
    rows = []
    num_fields = [
        ("pgy_level", 0), ("block_number", 0), ("day_of_week", -1),
        ("is_weekend", 0), ("day_index", 0), ("is_pm", None), ("font_bold", 0),
        ("db_matches_template", 0), ("week_in_block", 0),
    ]

    for f in features:
        row = []
        for field, default in num_fields:
            if field == "is_pm":
                row.append(1 if f.get("half") == "pm" else 0)
            elif field == "font_bold":
                row.append(1 if f.get("font_bold") else 0)
            elif field == "is_weekend":
                row.append(1 if f.get("is_weekend") else 0)
            elif field == "db_matches_template":
                row.append(1 if f.get("db_matches_template") else 0)
            else:
                val = f.get(field)
                row.append(val if val is not None else default)

        for field in cat_fields:
            val = f.get(field) or "__NONE__"
            enc = encoders[field]
            if val in enc.classes_:
                row.append(enc.transform([val])[0])
            else:
                row.append(len(enc.classes_))  # Unknown category
        rows.append(row)

    return np.array(rows, dtype=np.float32)


def generate_report(
    features: list[dict],
    model_path: str,
    output_path: str,
) -> None:
    """Generate HTML comparison report."""
    model_data = joblib.load(model_path)
    rf = model_data["rf"]
    encoders = model_data["encoders"]
    feature_names = model_data["feature_names"]
    label_enc = encoders["__label__"]

    cat_fields = [
        "rotation1", "rotation2", "template", "role", "db_code",
        "template_expected", "db_other_half", "fill_rgb", "font_rgb",
        "person_type",
    ]

    labeled = [f for f in features if f.get("truth_code")]

    X = _encode_for_prediction(labeled, encoders, feature_names, cat_fields)
    y_pred_idx = rf.predict(X)
    y_pred = label_enc.inverse_transform(y_pred_idx)

    # Attach predictions to features
    for f, pred in zip(labeled, y_pred):
        f["ml_code"] = pred

    # Group by person
    by_person: dict[str, list[dict]] = defaultdict(list)
    for f in labeled:
        by_person[f["person"]].append(f)

    # Sort cells within each person by day_index and half
    for cells in by_person.values():
        cells.sort(key=lambda c: (c.get("day_index", 0), 0 if c.get("half") == "am" else 1))

    # Compute overall stats
    total = len(labeled)
    ml_correct = sum(1 for f in labeled if f["ml_code"] == f["truth_code"])
    db_total = sum(1 for f in labeled if f.get("db_code"))
    db_correct = sum(1 for f in labeled
                     if f.get("db_code") and f["db_code"] == f["truth_code"])

    # Per-person stats
    person_stats: list[tuple[str, float, float, int, dict]] = []
    for name, cells in sorted(by_person.items()):
        n = len(cells)
        ml_ok = sum(1 for c in cells if c["ml_code"] == c["truth_code"])
        db_n = sum(1 for c in cells if c.get("db_code"))
        db_ok = sum(1 for c in cells
                    if c.get("db_code") and c["db_code"] == c["truth_code"])
        ml_pct = 100 * ml_ok / n if n else 0
        db_pct = 100 * db_ok / db_n if db_n else 0
        rot = cells[0].get("rotation1", "") if cells else ""
        pgy = cells[0].get("pgy_level", "") if cells else ""
        person_stats.append((name, ml_pct, db_pct, n, {
            "rotation": rot, "pgy": pgy, "cells": cells,
        }))

    # Sort by ML accuracy (worst first — most interesting)
    person_stats.sort(key=lambda x: x[1])

    # Build HTML
    html_parts = [_html_header(ml_correct, total, db_correct, db_total)]

    for name, ml_pct, db_pct, n, info in person_stats:
        html_parts.append(_html_person(name, ml_pct, db_pct, n, info))

    # Summary table: transformations learned
    pattern_counts: Counter = Counter()
    for f in labeled:
        db = f.get("db_code")
        truth = f["truth_code"]
        ml = f["ml_code"]
        if db and ml == truth and db != truth:
            pattern_counts[(db, truth)] += 1

    html_parts.append(_html_patterns(pattern_counts))
    html_parts.append("</body></html>")

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(html_parts))
    print(f"Wrote report to {out}")
    print(f"  ML accuracy: {ml_correct}/{total} ({100*ml_correct/total:.1f}%)")
    if db_total:
        print(f"  DB accuracy: {db_correct}/{db_total} ({100*db_correct/db_total:.1f}%)")


def _html_header(ml_ok: int, total: int, db_ok: int, db_total: int) -> str:
    ml_pct = 100 * ml_ok / total if total else 0
    db_pct = 100 * db_ok / db_total if db_total else 0
    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8">
<title>Schedule Vision — ML vs Ground Truth</title>
<style>
body {{ font-family: -apple-system, BlinkMacSystemFont, sans-serif;
       margin: 20px; background: #f5f5f5; }}
h1 {{ color: #333; }}
.summary {{ background: white; padding: 20px; border-radius: 8px;
            margin-bottom: 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
.metric {{ display: inline-block; margin-right: 30px; }}
.metric .value {{ font-size: 2em; font-weight: bold; }}
.metric .label {{ color: #666; }}
.ml-good {{ color: #2ecc71; }}
.db-ok {{ color: #3498db; }}
.person {{ background: white; padding: 15px; border-radius: 8px;
           margin-bottom: 10px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
.person-header {{ display: flex; justify-content: space-between;
                  align-items: center; margin-bottom: 8px; }}
.person-name {{ font-weight: bold; font-size: 1.1em; }}
.person-meta {{ color: #666; font-size: 0.9em; }}
.grid {{ display: flex; gap: 1px; flex-wrap: wrap; }}
.day {{ display: flex; flex-direction: column; }}
.day-label {{ font-size: 0.65em; color: #999; text-align: center; width: 32px; }}
.cell {{ width: 32px; height: 18px; font-size: 0.6em; text-align: center;
         line-height: 18px; border: 1px solid #ddd; overflow: hidden; }}
.cell.mismatch {{ border: 2px solid #e74c3c; }}
.cell.ml-win {{ border: 2px solid #2ecc71; }}
.row-label {{ width: 40px; font-size: 0.7em; color: #666;
              line-height: 18px; text-align: right; padding-right: 4px; }}
.schedule-row {{ display: flex; align-items: center; }}
.pct {{ font-weight: bold; }}
.pct-good {{ color: #2ecc71; }}
.pct-mid {{ color: #f39c12; }}
.pct-bad {{ color: #e74c3c; }}
.patterns {{ background: white; padding: 20px; border-radius: 8px;
             box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
.patterns table {{ border-collapse: collapse; width: 100%; }}
.patterns th, .patterns td {{ padding: 6px 12px; text-align: left;
                               border-bottom: 1px solid #eee; }}
.patterns th {{ background: #f8f8f8; }}
</style></head><body>
<h1>Schedule Vision — ML vs Ground Truth</h1>
<div class="summary">
  <div class="metric">
    <div class="value ml-good">{ml_pct:.1f}%</div>
    <div class="label">ML Match Rate ({ml_ok}/{total})</div>
  </div>
  <div class="metric">
    <div class="value db-ok">{db_pct:.1f}%</div>
    <div class="label">DB Match Rate ({db_ok}/{db_total})</div>
  </div>
  <div class="metric">
    <div class="value">{ml_pct - db_pct:+.1f}%</div>
    <div class="label">ML Improvement</div>
  </div>
</div>
"""


def _pct_class(pct: float) -> str:
    if pct >= 80:
        return "pct-good"
    if pct >= 50:
        return "pct-mid"
    return "pct-bad"


def _html_person(
    name: str, ml_pct: float, db_pct: float, n: int, info: dict,
) -> str:
    cells = info["cells"]
    rot = info["rotation"]
    pgy = info["pgy"]

    # Group cells by day_index
    days: dict[int, dict[str, dict]] = defaultdict(dict)
    for c in cells:
        days[c["day_index"]][c["half"]] = c

    max_day = max(days.keys()) if days else 0

    # Build grid rows (Truth, ML, DB)
    truth_cells = []
    ml_cells = []
    db_cells = []
    day_labels = []

    for d in range(max_day + 1):
        day_data = days.get(d, {})
        am = day_data.get("am", {})
        pm = day_data.get("pm", {})

        # Day label
        dow = am.get("day_of_week", pm.get("day_of_week"))
        day_names = ["M", "Tu", "W", "Th", "F", "Sa", "Su"]
        label = day_names[dow] if dow is not None and 0 <= dow < 7 else str(d)
        day_labels.append(label)

        for half_data in [am, pm]:
            if not half_data:
                truth_cells.append(("", DEFAULT_COLOR, ""))
                ml_cells.append(("", DEFAULT_COLOR, ""))
                db_cells.append(("", DEFAULT_COLOR, ""))
                continue

            truth = half_data.get("truth_code", "")
            ml = half_data.get("ml_code", "")
            db = half_data.get("db_code", "")

            # Determine cell class
            ml_class = ""
            if ml != truth:
                ml_class = "mismatch"
            elif db and db != truth:
                ml_class = "ml-win"

            db_class = "mismatch" if db and db != truth else ""

            truth_cells.append((truth, _get_color(truth), ""))
            ml_cells.append((ml, _get_color(ml), ml_class))
            db_cells.append((db, _get_color(db), db_class))

    # Render
    lines = [f'<div class="person">']
    lines.append(f'<div class="person-header">')
    lines.append(f'  <span class="person-name">{name}</span>')
    lines.append(f'  <span class="person-meta">'
                 f'rot={rot} pgy={pgy} '
                 f'ML=<span class="pct {_pct_class(ml_pct)}">{ml_pct:.0f}%</span> '
                 f'DB=<span class="pct {_pct_class(db_pct)}">{db_pct:.0f}%</span>'
                 f'</span>')
    lines.append(f'</div>')

    # Day labels row
    lines.append('<div class="schedule-row">')
    lines.append('<div class="row-label"></div>')
    lines.append('<div class="grid">')
    for i, label in enumerate(day_labels):
        lines.append(f'<div class="day"><div class="day-label">{label}</div></div>')
    lines.append('</div></div>')

    # Truth row
    lines.append(_grid_row("Truth", truth_cells))
    lines.append(_grid_row("ML", ml_cells))
    lines.append(_grid_row("DB", db_cells))

    lines.append('</div>')
    return "\n".join(lines)


def _grid_row(label: str, cells: list[tuple[str, str, str]]) -> str:
    parts = [f'<div class="schedule-row">']
    parts.append(f'<div class="row-label">{label}</div>')
    parts.append('<div class="grid">')
    for text, color, cls in cells:
        cls_attr = f' class="cell {cls}"' if cls else ' class="cell"'
        parts.append(
            f'<div{cls_attr} style="background:{color}" '
            f'title="{text}">{text}</div>'
        )
    parts.append('</div></div>')
    return "\n".join(parts)


def _html_patterns(pattern_counts: Counter) -> str:
    if not pattern_counts:
        return ""

    lines = ['<div class="patterns">', '<h2>Learned Transformations (ML correct, DB wrong)</h2>']
    lines.append('<table><tr><th>DB Code</th><th>→</th>'
                 '<th>Display Code</th><th>Count</th></tr>')
    for (db, display), cnt in pattern_counts.most_common(30):
        lines.append(
            f'<tr><td style="background:{_get_color(db)}">{db}</td>'
            f'<td>→</td>'
            f'<td style="background:{_get_color(display)}">{display}</td>'
            f'<td>{cnt}</td></tr>'
        )
    lines.append('</table></div>')
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Generate visual diff report",
    )
    parser.add_argument("--features", default="data/features.json",
                        help="Feature JSON from extract.py")
    parser.add_argument("--model", default="data/model.pkl",
                        help="Trained model from learn.py")
    parser.add_argument("--output", default="data/report.html",
                        help="Output HTML report")
    args = parser.parse_args()

    features = json.loads(Path(args.features).read_text())
    generate_report(features, args.model, args.output)


if __name__ == "__main__":
    main()
