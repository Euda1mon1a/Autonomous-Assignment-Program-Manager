"""Diff ground truth (handjam) vs DB export — find every discrepancy.

Matches people by last name, aligns dates by day-of-block index,
and produces a structured diff with pattern analysis.

Usage:
    python scripts/ops/diff_truth_vs_db.py \
        --truth /tmp/ground_truth.json \
        --db-json /tmp/block10_data.json \
        --block "Block 10"
"""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path


def _last_name(name: str) -> str:
    """Extract lowercase last name from either 'First Last' or 'Last, First'."""
    name = name.strip().rstrip("*").strip()
    if "," in name:
        return name.split(",")[0].strip().lower()
    parts = name.split()
    return parts[-1].lower() if parts else name.lower()


def diff_block(truth_block: dict, db_data: dict) -> dict:
    """Compare one block's ground truth against DB export."""

    # Build DB lookup: last_name -> person dict
    db_people = {}
    for person in db_data.get("residents", []) + db_data.get("faculty", []):
        ln = _last_name(person["name"])
        db_people[ln] = person

    results = {
        "block": truth_block["tab_name"],
        "truth_dates": truth_block["dates"],
        "db_dates": [db_data["block_start"], "...", db_data["block_end"]],
        "matches": [],
        "mismatches": [],
        "truth_only": [],
        "db_only": [],
        "unmatched_truth_people": [],
        "unmatched_db_people": [],
    }

    matched_db_names = set()

    for person in truth_block["people"]:
        ln = _last_name(person["name"])
        db_person = db_people.get(ln)

        if not db_person:
            results["unmatched_truth_people"].append({
                "name": person["name"],
                "last_name": ln,
                "type": person["type"],
                "filled_cells": person["filled_cells"],
            })
            # Still record all truth cells as truth_only
            for day in person["days"]:
                for half in ("am", "pm"):
                    code = day.get(half)
                    if code:
                        results["truth_only"].append({
                            "person": person["name"],
                            "day_index": day["day_index"],
                            "date": day["date"],
                            "half": half,
                            "truth_code": code,
                            "rotation": person.get("rotation1"),
                        })
            continue

        matched_db_names.add(ln)

        # Compare day by day using day_index (position in block, 0-27)
        db_days = {i: d for i, d in enumerate(db_person.get("days", []))}

        for day in person["days"]:
            idx = day["day_index"]
            db_day = db_days.get(idx, {})

            for half in ("am", "pm"):
                truth_code = day.get(half)
                db_code = db_day.get(half)

                # Normalize
                truth_norm = truth_code.strip() if truth_code else None
                db_norm = db_code.strip() if db_code else None

                # Skip if both empty
                if not truth_norm and not db_norm:
                    continue

                entry = {
                    "person": person["name"],
                    "db_name": db_person["name"],
                    "day_index": idx,
                    "truth_date": day.get("date"),
                    "db_date": db_day.get("date"),
                    "half": half,
                    "rotation": person.get("rotation1"),
                    "role": person.get("role"),
                }

                if truth_norm == db_norm:
                    entry["code"] = truth_norm
                    results["matches"].append(entry)
                elif truth_norm and db_norm:
                    entry["truth_code"] = truth_norm
                    entry["db_code"] = db_norm
                    results["mismatches"].append(entry)
                elif truth_norm and not db_norm:
                    entry["truth_code"] = truth_norm
                    results["truth_only"].append(entry)
                elif db_norm and not truth_norm:
                    entry["db_code"] = db_norm
                    results["db_only"].append(entry)

        # Rotation comparison
        truth_rot1 = person.get("rotation1")
        db_rot1 = db_person.get("rotation1")
        if truth_rot1 and db_rot1 and truth_rot1 != db_rot1:
            results.setdefault("rotation_mismatches", []).append({
                "person": person["name"],
                "truth_rot1": truth_rot1,
                "db_rot1": db_rot1,
            })

    # Unmatched DB people
    for ln, person in db_people.items():
        if ln not in matched_db_names:
            results["unmatched_db_people"].append({
                "name": person["name"],
                "last_name": ln,
            })

    return results


def analyze_patterns(diff: dict) -> dict:
    """Analyze mismatch patterns to discover transformation rules."""
    patterns = {}

    # 1. Code-to-code mapping frequency
    code_map = Counter()
    for m in diff["mismatches"]:
        code_map[(m["db_code"], m["truth_code"])] += 1

    patterns["code_mappings"] = [
        {"db_code": db, "truth_code": truth, "count": cnt}
        for (db, truth), cnt in code_map.most_common(50)
    ]

    # 2. Group by rotation
    rot_patterns = defaultdict(lambda: Counter())
    for m in diff["mismatches"]:
        rot = m.get("rotation") or "unknown"
        rot_patterns[rot][(m["db_code"], m["truth_code"])] += 1

    patterns["by_rotation"] = {}
    for rot, counter in sorted(rot_patterns.items()):
        patterns["by_rotation"][rot] = [
            {"db": db, "truth": truth, "n": n}
            for (db, truth), n in counter.most_common(10)
        ]

    # 3. Truth-only codes (things in handjam but DB produces nothing)
    truth_only_codes = Counter()
    for t in diff["truth_only"]:
        truth_only_codes[t.get("truth_code", "?")] += 1
    patterns["truth_only_codes"] = [
        {"code": code, "count": cnt}
        for code, cnt in truth_only_codes.most_common(20)
    ]

    # 4. Weekend vs weekday mismatches
    from datetime import date as date_type
    weekend_mismatches = Counter()
    weekday_mismatches = Counter()
    for m in diff["mismatches"]:
        d = m.get("truth_date") or m.get("db_date")
        if d:
            try:
                dt = date_type.fromisoformat(d)
                bucket = weekend_mismatches if dt.weekday() in (5, 6) else weekday_mismatches
            except (ValueError, TypeError):
                bucket = weekday_mismatches
        else:
            bucket = weekday_mismatches
        bucket[(m["db_code"], m["truth_code"])] += 1

    patterns["weekend_mismatches"] = [
        {"db": db, "truth": truth, "n": n}
        for (db, truth), n in weekend_mismatches.most_common(10)
    ]
    patterns["weekday_mismatches"] = [
        {"db": db, "truth": truth, "n": n}
        for (db, truth), n in weekday_mismatches.most_common(10)
    ]

    return patterns


def print_report(diff: dict, patterns: dict):
    """Print human-readable diff report."""
    print(f"\n{'='*70}")
    print(f"  GROUND TRUTH vs DB DIFF — {diff['block']}")
    print(f"{'='*70}")

    print(f"\n  Matched cells:     {len(diff['matches']):5d}")
    print(f"  Mismatched cells:  {len(diff['mismatches']):5d}")
    print(f"  Truth-only cells:  {len(diff['truth_only']):5d}")
    print(f"  DB-only cells:     {len(diff['db_only']):5d}")

    total = len(diff['matches']) + len(diff['mismatches']) + len(diff['truth_only']) + len(diff['db_only'])
    if total:
        pct = len(diff['matches']) / total * 100
        print(f"  Match rate:        {pct:.1f}%")

    if diff.get("unmatched_truth_people"):
        print(f"\n  Unmatched handjam people ({len(diff['unmatched_truth_people'])}):")
        for p in diff["unmatched_truth_people"]:
            print(f"    {p['name']} ({p['type']}, {p['filled_cells']} cells)")

    if diff.get("unmatched_db_people"):
        print(f"\n  Unmatched DB people ({len(diff['unmatched_db_people'])}):")
        for p in diff["unmatched_db_people"]:
            print(f"    {p['name']}")

    if diff.get("rotation_mismatches"):
        print(f"\n  Rotation mismatches:")
        for r in diff["rotation_mismatches"]:
            print(f"    {r['person']:25s}  truth={r['truth_rot1']:20s}  db={r['db_rot1']}")

    # Code mappings — THE KEY OUTPUT
    print(f"\n  {'─'*60}")
    print(f"  TOP CODE MAPPINGS (DB → Handjam)")
    print(f"  {'─'*60}")
    for m in patterns["code_mappings"][:30]:
        arrow = "→" if m["db_code"] != m["truth_code"] else "="
        print(f"    {m['db_code']:15s} {arrow} {m['truth_code']:12s}  (n={m['count']})")

    # By rotation
    print(f"\n  {'─'*60}")
    print(f"  MISMATCHES BY ROTATION")
    print(f"  {'─'*60}")
    for rot, maps in patterns["by_rotation"].items():
        print(f"\n    {rot}:")
        for m in maps[:5]:
            print(f"      {m['db']:15s} → {m['truth']:12s}  (n={m['n']})")

    # Truth-only
    if patterns["truth_only_codes"]:
        print(f"\n  {'─'*60}")
        print(f"  TRUTH-ONLY CODES (handjam has it, DB produces nothing)")
        print(f"  {'─'*60}")
        for t in patterns["truth_only_codes"]:
            print(f"    {t['code']:12s}  (n={t['count']})")


def main():
    parser = argparse.ArgumentParser(description="Diff ground truth vs DB export")
    parser.add_argument("--truth", required=True, help="Ground truth JSON from extract_ground_truth.py")
    parser.add_argument("--db-json", required=True, help="DB export JSON (from HalfDayJSONExporter)")
    parser.add_argument("--block", required=True, help="Block tab name to compare (e.g. 'Block 10')")
    parser.add_argument("--output", default=None, help="Optional: save full diff as JSON")
    args = parser.parse_args()

    truth_data = json.loads(Path(args.truth).read_text())
    db_data = json.loads(Path(args.db_json).read_text())

    # Find the requested block in truth data
    truth_block = None
    for b in truth_data["blocks"]:
        if b["tab_name"] == args.block:
            truth_block = b
            break

    if not truth_block:
        available = [b["tab_name"] for b in truth_data["blocks"]]
        print(f"ERROR: Block '{args.block}' not found. Available: {available}")
        return

    diff = diff_block(truth_block, db_data)
    patterns = analyze_patterns(diff)

    print_report(diff, patterns)

    if args.output:
        out = Path(args.output)
        out.write_text(json.dumps({"diff": diff, "patterns": patterns}, indent=2, default=str))
        print(f"\n  Full diff saved to {out}")


if __name__ == "__main__":
    main()
