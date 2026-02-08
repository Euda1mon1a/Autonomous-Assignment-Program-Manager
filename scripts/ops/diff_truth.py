"""Diff handjam ground truth vs DB truth for Block 10.

Produces:
  1. Cell-level match/mismatch report
  2. Transformation rules (what the DB should produce to match handjam)
  3. Codes only in handjam (missing from DB)
  4. Codes only in DB (missing from handjam)
"""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path


def normalize_name(handjam_name: str) -> str:
    """Convert 'Last, First*' -> last name for matching."""
    name = handjam_name.replace("*", "").strip()
    if "," in name:
        last = name.split(",")[0].strip()
    else:
        last = name.split()[-1].strip()
    return last.lower()


def db_name_to_last(db_name: str) -> str:
    """Convert 'First Last' -> last name for matching."""
    return db_name.split()[-1].strip().lower()


def main():
    gt = json.loads(Path("/tmp/handjam_ground_truth.json").read_text())
    db = json.loads(Path("/tmp/db_truth.json").read_text())

    # Build DB lookup: (last_name, date, half) -> {db_code, db_display}
    db_lookup = {}
    for c in db["cells"]:
        key = (db_name_to_last(c["person"]), c["date"], c["half"])
        db_lookup[key] = c

    # Filter handjam to Block 10 only
    b10_cells = [c for c in gt["cells"] if c["block"] == "Block 10"]

    matched = []
    handjam_only = []
    db_only_keys = set(db_lookup.keys())

    for cell in b10_cells:
        last = normalize_name(cell["person"])
        # Handjam dates are 2026 (we fixed the year in extraction)
        key = (last, cell["date"], cell["half"])

        if key in db_lookup:
            db_cell = db_lookup[key]
            db_only_keys.discard(key)
            matched.append({
                "person": cell["person"],
                "date": cell["date"],
                "half": cell["half"],
                "handjam": cell["code"],
                "db_code": db_cell["db_code"],
                "db_display": db_cell["db_display"],
                "rotation1": cell["rotation1"],
                "rotation2": cell["rotation2"],
                "match_display": cell["code"] == db_cell["db_display"],
                "match_code": cell["code"] == db_cell["db_code"],
            })
        else:
            handjam_only.append(cell)

    db_only = [db_lookup[k] for k in sorted(db_only_keys)]

    # === Analysis ===
    print(f"=== BLOCK 10 DIFF ===")
    print(f"Handjam cells:    {len(b10_cells)}")
    print(f"DB cells:         {len(db['cells'])}")
    print(f"Matched (joined): {len(matched)}")
    print(f"Handjam only:     {len(handjam_only)}")
    print(f"DB only:          {len(db_only)}")

    exact_display = sum(1 for m in matched if m["match_display"])
    exact_code = sum(1 for m in matched if m["match_code"])
    differs = [m for m in matched if not m["match_display"]]

    print(f"\nOf {len(matched)} matched cells:")
    print(f"  Exact match (display_abbrev): {exact_display} ({100*exact_display/len(matched):.1f}%)")
    print(f"  Exact match (raw code):       {exact_code} ({100*exact_code/len(matched):.1f}%)")
    print(f"  Differs:                      {len(differs)}")

    # What transformations are needed?
    print(f"\n=== TRANSFORMATION RULES (db_display -> handjam) ===")
    transforms = Counter()
    for m in differs:
        transforms[(m["db_display"], m["handjam"])] += 1

    for (db_disp, hj), cnt in transforms.most_common(40):
        print(f"  {db_disp:12s} -> {hj:12s}  ({cnt}x)")

    # Group by category
    print(f"\n=== PATTERNS IN DIFFS ===")

    # LV -> something else
    lv_transforms = [(m["handjam"], m["rotation1"]) for m in differs if m["db_display"] == "LV"]
    if lv_transforms:
        print(f"\n  LV overrides ({len(lv_transforms)} cells):")
        lv_by_target = Counter(t[0] for t in lv_transforms)
        for target, cnt in lv_by_target.most_common():
            rots = set(t[1] for t in lv_transforms if t[0] == target)
            print(f"    LV -> {target:8s} ({cnt}x)  rotations: {rots}")

    # OFF -> something else
    off_transforms = [(m["handjam"], m["rotation1"]) for m in differs if m["db_display"] == "OFF"]
    if off_transforms:
        print(f"\n  OFF overrides ({len(off_transforms)} cells):")
        off_by_target = Counter(t[0] for t in off_transforms)
        for target, cnt in off_by_target.most_common():
            rots = set(t[1] for t in off_transforms if t[0] == target)
            print(f"    OFF -> {target:8s} ({cnt}x)  rotations: {rots}")

    # W -> something else
    w_transforms = [(m["handjam"], m["rotation1"]) for m in differs if m["db_display"] == "W"]
    if w_transforms:
        print(f"\n  W overrides ({len(w_transforms)} cells):")
        w_by_target = Counter(t[0] for t in w_transforms)
        for target, cnt in w_by_target.most_common():
            rots = set(t[1] for t in w_transforms if t[0] == target)
            print(f"    W -> {target:8s} ({cnt}x)  rotations: {rots}")

    # IM -> something else
    im_transforms = [(m["handjam"], m["rotation1"]) for m in differs if m["db_display"] == "IM"]
    if im_transforms:
        print(f"\n  IM overrides ({len(im_transforms)} cells):")
        im_by_target = Counter(t[0] for t in im_transforms)
        for target, cnt in im_by_target.most_common():
            rots = set(t[1] for t in im_transforms if t[0] == target)
            print(f"    IM -> {target:8s} ({cnt}x)  rotations: {rots}")

    # What codes appear in handjam but never in DB?
    print(f"\n=== CODES ONLY IN HANDJAM (Block 10) ===")
    hj_codes = set(c["code"] for c in b10_cells)
    db_codes = set(c["db_code"] for c in db["cells"])
    db_displays = set(c["db_display"] for c in db["cells"])
    all_db = db_codes | db_displays

    for code in sorted(hj_codes - all_db):
        cnt = sum(1 for c in b10_cells if c["code"] == code)
        # Who has this code?
        who = set(c["person"] for c in b10_cells if c["code"] == code)
        print(f"  {code:12s} ({cnt}x)  {who}")

    # What does the DB produce that never appears in handjam?
    print(f"\n=== CODES ONLY IN DB (Block 10) ===")
    for code in sorted(db_displays - hj_codes):
        cnt = sum(1 for c in db["cells"] if c["db_display"] == code)
        print(f"  {code:12s} ({cnt}x)")

    # Write full diff to JSON for Claude analysis
    output = {
        "summary": {
            "handjam_cells": len(b10_cells),
            "db_cells": len(db["cells"]),
            "matched": len(matched),
            "exact_match": exact_display,
            "differs": len(differs),
            "handjam_only": len(handjam_only),
            "db_only": len(db_only),
        },
        "transformations": [
            {"db_display": k[0], "handjam": k[1], "count": v}
            for k, v in transforms.most_common()
        ],
        "differs_detail": differs,
        "handjam_only": handjam_only,
        "db_only": db_only,
    }
    Path("/tmp/block10_diff.json").write_text(json.dumps(output, indent=2))
    print(f"\nFull diff written to /tmp/block10_diff.json")


if __name__ == "__main__":
    main()
