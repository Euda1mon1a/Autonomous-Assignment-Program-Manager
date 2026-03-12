#!/usr/bin/env python3
"""Mine rotation patterns from historical half-day assignments.

Converts 16,617+ HDAs into structured rotation profiles — one per
person-block combination.  Each profile captures code frequencies,
weekly slot grids, foreground/background separation, and split-block
detection.

Usage:
    cd ~/workspace/aapm
    backend/.venv/bin/python scripts/ml/mine_rotation_patterns.py \
        --output /tmp/rotation_profiles.json
"""

import argparse
import json
import os
import sys
from collections import Counter, defaultdict
from datetime import date, timedelta
from pathlib import Path

import psycopg2
import psycopg2.extras

# Background activities that appear across most rotations (not rotation-defining)
BACKGROUND_CODES = frozenset({
    # Universal admin/conference
    "fm_clinic", "lec", "gme", "RETREAT", "PI", "W", "off", "recovery",
    "CC", "SIM", "ADV", "CCC", "HLC", "HR-SUP", "pcat", "do", "dfm",
    "at", "ORIENT", "CODING",
    # Absences and leave (not rotation-defining)
    "LV", "LV-AM", "LV-PM", "HOL",
    # Institutional events
    "USAFP", "DEP",
})

DAY_NAMES = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]


def parse_args():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--db-url", default=os.getenv(
        "DATABASE_URL",
        "postgresql://scheduler@localhost:5432/residency_scheduler",
    ))
    p.add_argument("--academic-year", type=int, default=2025)
    p.add_argument("--output", default="/tmp/rotation_profiles.json")
    return p.parse_args()


def fetch_blocks(cur, academic_year):
    """Return dict of block_number → {start_date, end_date}."""
    cur.execute("""
        SELECT block_number, start_date, end_date
        FROM academic_blocks
        WHERE academic_year = %s
        ORDER BY block_number
    """, (academic_year,))
    return {row[0]: {"start": row[1], "end": row[2]} for row in cur.fetchall()}


def fetch_hdas(cur, academic_year):
    """Fetch all HDAs for the academic year, joined with people and activities."""
    cur.execute("""
        SELECT
            h.person_id::text,
            p.name,
            p.type AS person_type,
            p.pgy_level,
            h.date,
            h.time_of_day,
            a.code AS activity_code,
            a.activity_category,
            h.source,
            ab.block_number
        FROM half_day_assignments h
        JOIN people p ON h.person_id = p.id
        JOIN activities a ON h.activity_id = a.id
        JOIN academic_blocks ab
            ON h.date >= ab.start_date
            AND h.date <= ab.end_date
            AND ab.academic_year = %s
        WHERE ab.academic_year = %s
        ORDER BY p.name, ab.block_number, h.date, h.time_of_day
    """, (academic_year, academic_year))
    return cur.fetchall()


def fetch_block_assignments(cur, academic_year):
    """Fetch block_assignments → rotation template mappings.

    Split-block residents have two rows: block_half=1 (primary, days 1-14) and
    block_half=2 (secondary, days 15-28). Full-block residents have block_half IS NULL.
    """
    cur.execute("""
        SELECT
            ba.resident_id::text,
            ba.block_number,
            rt.name AS template_name,
            rt.rotation_type,
            rt.template_category,
            ba.block_half
        FROM block_assignments ba
        LEFT JOIN rotation_templates rt ON ba.rotation_template_id = rt.id
        WHERE ba.academic_year = %s
        ORDER BY ba.resident_id, ba.block_number, ba.block_half NULLS FIRST
    """, (academic_year,))
    # Key: (person_id, block_number) → template info
    # Merge block_half=1 and block_half=2 rows into a single entry
    result = {}
    for row in cur.fetchall():
        key = (row[0], row[1])
        block_half = row[5]
        if block_half == 2:
            # Secondary rotation — attach to existing entry
            if key in result:
                result[key]["secondary_template_name"] = row[2]
        else:
            # Primary (block_half IS NULL or 1)
            result[key] = {
                "template_name": row[2],
                "rotation_type": row[3],
                "template_category": row[4],
                "secondary_template_name": None,
            }
    return result


def date_to_week_day(d, block_start):
    """Return (week_number 1-based, day_of_week 0=Mon..6=Sun)."""
    delta = (d - block_start).days
    week = delta // 7 + 1
    dow = d.weekday()  # 0=Mon
    return week, dow


def detect_split_block(foreground_by_week):
    """Detect if the dominant foreground code changes mid-block.

    Returns (is_split, split_week, first_half_code, second_half_code).
    """
    if not foreground_by_week:
        return False, None, None, None

    weeks = sorted(foreground_by_week.keys())
    if len(weeks) < 2:
        return False, None, None, None

    # Get dominant foreground code per week
    week_dominants = {}
    for w in weeks:
        codes = foreground_by_week[w]
        if codes:
            most_common = Counter(codes).most_common(1)[0][0]
            week_dominants[w] = most_common

    if len(set(week_dominants.values())) <= 1:
        return False, None, None, None

    # Find the transition point — the week where dominant code changes
    prev_code = None
    for w in weeks:
        code = week_dominants.get(w)
        if code is None:
            continue
        if prev_code is not None and code != prev_code:
            return True, w, prev_code, code
        prev_code = code

    return False, None, None, None


def build_weekly_grid(hdas_for_profile, block_start):
    """Build a weekly slot grid: list of week dicts with day_am/day_pm slots."""
    grid = defaultdict(lambda: {})
    for _, _, _, _, d, tod, code, *_ in hdas_for_profile:
        week, dow = date_to_week_day(d, block_start)
        slot_key = f"{DAY_NAMES[dow]}_{tod.lower()}"
        grid[week][slot_key] = code

    result = []
    for week_num in sorted(grid.keys()):
        entry = {"week": week_num}
        entry.update(grid[week_num])
        result.append(entry)
    return result


def build_profile(key, hdas, block_info, block_assignments):
    """Build one rotation profile from a list of HDAs for a person-block."""
    person_id, block_number = key
    first = hdas[0]
    person_name = first[1]
    person_type = first[2]
    pgy_level = first[3]

    block_start = block_info[block_number]["start"]

    # Count activity codes
    code_counts = Counter()
    source_counts = Counter()
    foreground_by_week = defaultdict(list)
    all_codes = []

    for row in hdas:
        code = row[6]
        source = row[8]
        d = row[4]
        code_counts[code] += 1
        source_counts[source] += 1
        all_codes.append(code)

        week, _ = date_to_week_day(d, block_start)
        if code not in BACKGROUND_CODES:
            foreground_by_week[week].append(code)

    total_hdas = len(hdas)
    unique_codes = sorted(code_counts.keys())

    # Foreground vs background
    foreground_codes = sorted(set(c for c in all_codes if c not in BACKGROUND_CODES))
    background_codes = sorted(set(c for c in all_codes if c in BACKGROUND_CODES))

    # Dominant code (foreground only)
    fg_counts = {c: n for c, n in code_counts.items() if c not in BACKGROUND_CODES}
    total_fg = sum(fg_counts.values())
    fg_pct = round(total_fg / total_hdas, 3) if total_hdas else 0

    if fg_counts:
        dominant_code = max(fg_counts, key=fg_counts.get)
        dominant_pct = round(fg_counts[dominant_code] / total_hdas, 3)
    else:
        dominant_code = None
        dominant_pct = 0

    # Classify the rotation type
    if fg_pct < 0.05:
        rotation_category = "background_only"  # leave/holiday block
    elif dominant_pct > 0.6:
        rotation_category = "mono_rotation"  # single dominant rotation
    elif len(fg_counts) <= 3:
        rotation_category = "focused"  # 2-3 foreground activities
    else:
        rotation_category = "mixed"  # diverse outpatient-style

    # Split-block detection
    is_split, split_week, first_half, second_half = detect_split_block(foreground_by_week)

    # Weekly grid
    weekly_grid = build_weekly_grid(hdas, block_start)

    # Block assignment template (if exists)
    ba_key = (person_id, block_number)
    template_info = block_assignments.get(ba_key)

    # Split-week HDA counts: separate code_counts for weeks 1-2 vs weeks 3-4
    # Needed by learn_constraints.py for split-block-aware constraint learning
    split_week_hdas = {"weeks_1_2": Counter(), "weeks_3_4": Counter()}
    for row in hdas:
        code = row[6]
        d = row[4]
        week, _ = date_to_week_day(d, block_start)
        if week <= 2:
            split_week_hdas["weeks_1_2"][code] += 1
        else:
            split_week_hdas["weeks_3_4"][code] += 1

    return {
        "person_id": person_id,
        "person_name": person_name,
        "person_type": person_type,
        "pgy_level": pgy_level,
        "block_number": block_number,
        "total_hdas": total_hdas,
        "dominant_code": dominant_code,
        "dominant_pct": dominant_pct,
        "foreground_pct": fg_pct,
        "rotation_category": rotation_category,
        "unique_codes": unique_codes,
        "code_counts": dict(code_counts),
        "foreground_codes": foreground_codes,
        "background_codes": background_codes,
        "is_split_block": is_split,
        "split_point_week": split_week,
        "split_first_half": first_half,
        "split_second_half": second_half,
        "source_breakdown": dict(source_counts),
        "weekly_pattern": weekly_grid,
        "split_week_hdas": {
            "weeks_1_2": dict(split_week_hdas["weeks_1_2"]),
            "weeks_3_4": dict(split_week_hdas["weeks_3_4"]),
        },
        "assigned_template": template_info.get("template_name") if template_info else None,
        "assigned_template_type": template_info.get("rotation_type") if template_info else None,
        "secondary_template": template_info.get("secondary_template_name") if template_info else None,
    }


def main():
    args = parse_args()

    conn = psycopg2.connect(args.db_url)
    cur = conn.cursor()

    print(f"Fetching academic blocks for AY {args.academic_year}...")
    blocks = fetch_blocks(cur, args.academic_year)
    print(f"  Found {len(blocks)} blocks: {sorted(blocks.keys())}")

    print("Fetching block assignments...")
    block_assignments = fetch_block_assignments(cur, args.academic_year)
    print(f"  Found {len(block_assignments)} block assignments")

    print("Fetching half-day assignments...")
    hdas = fetch_hdas(cur, args.academic_year)
    print(f"  Found {len(hdas)} HDAs")

    # Group by (person_id, block_number)
    grouped = defaultdict(list)
    for row in hdas:
        person_id = row[0]
        block_number = row[9]
        grouped[(person_id, block_number)].append(row)

    print(f"  {len(grouped)} unique person-block combinations")

    # Build profiles
    profiles = []
    for key in sorted(grouped.keys(), key=lambda k: (k[1], grouped[k][0][1])):
        profile = build_profile(key, grouped[key], blocks, block_assignments)
        profiles.append(profile)

    # Summary stats
    residents = [p for p in profiles if p["person_type"] == "resident"]
    faculty = [p for p in profiles if p["person_type"] == "faculty"]
    splits = [p for p in profiles if p["is_split_block"]]

    print(f"\n{'='*60}")
    print(f"  ROTATION PROFILE SUMMARY")
    print(f"{'='*60}")
    print(f"  Total profiles:     {len(profiles)}")
    print(f"  Resident profiles:  {len(residents)}")
    print(f"  Faculty profiles:   {len(faculty)}")
    print(f"  Split-block:        {len(splits)}")
    print(f"  Blocks covered:     {sorted(set(p['block_number'] for p in profiles))}")

    # Rotation categories
    cat_counts = Counter(p["rotation_category"] for p in profiles)
    print(f"\n  Rotation categories:")
    for cat, count in cat_counts.most_common():
        print(f"    {cat:20s} {count:3d} profiles")

    # Filter to meaningful profiles for remaining stats
    meaningful = [p for p in profiles if p["rotation_category"] != "background_only"]
    print(f"\n  Meaningful profiles (excl background_only): {len(meaningful)}")

    # Dominant code distribution
    dom_counts = Counter(p["dominant_code"] for p in profiles if p["dominant_code"])
    print(f"\n  Top 15 dominant codes:")
    for code, count in dom_counts.most_common(15):
        print(f"    {code:15s} {count:3d} profiles")

    # PGY breakdown (meaningful profiles only)
    for pgy in [1, 2, 3, None]:
        subset = [p for p in meaningful if p["pgy_level"] == pgy]
        if subset:
            label = f"PGY-{pgy}" if pgy else "Faculty"
            dom = Counter(
                p["dominant_code"] for p in subset if p["dominant_code"]
            ).most_common(5)
            print(f"\n  {label} ({len(subset)} profiles):")
            for code, count in dom:
                print(f"    {code:15s} {count:3d}")

    # Template coverage
    with_template = [p for p in profiles if p["assigned_template"]]
    print(f"\n  Profiles with assigned template: {len(with_template)}/{len(profiles)}")
    if with_template:
        tmpl_counts = Counter(p["assigned_template"] for p in with_template)
        print(f"  Top templates:")
        for tmpl, count in tmpl_counts.most_common(10):
            print(f"    {tmpl:40s} {count:3d}")

    # Write output
    out_path = Path(args.output)
    out_path.write_text(json.dumps(profiles, indent=2, default=str))
    print(f"\n  Output: {out_path} ({out_path.stat().st_size / 1024:.1f} KB)")

    conn.close()


if __name__ == "__main__":
    main()
