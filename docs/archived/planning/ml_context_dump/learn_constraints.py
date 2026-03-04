#!/usr/bin/env python3
"""Learn constraint parameters from historical HDA data (v2).

Split-block-aware constraint learning with confidence tiers and anomaly detection.
For each rotation template that has block_assignments, computes the actual
min/max/target halfdays per activity code from observed data, then compares
to existing rotation_activity_requirements.

v2 changes (council recommendations):
- Split-block awareness: learns from weeks 1-2 for primary, weeks 3-4 for secondary
- Confidence tiers: high (n>=8), medium (n=4-7, +/-2 padding), low (n=2-3, flag only)
- Anomaly detection: z-score > 2 flagged as outliers
- Applicable weeks output for split-block constraints

Usage:
    cd ~/workspace/aapm
    backend/.venv/bin/python scripts/ml/learn_constraints.py \
        --profiles /tmp/rotation_profiles_v2.json \
        --output /tmp/learned_constraints_v2.json \
        --diff-report /tmp/constraint_diff_v2.md
"""

import argparse
import json
import os
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
import psycopg2
import psycopg2.extras

BACKGROUND_CODES = frozenset({
    "fm_clinic", "lec", "gme", "RETREAT", "PI", "W", "off", "recovery",
    "CC", "SIM", "ADV", "CCC", "HLC", "HR-SUP", "pcat", "do", "dfm",
    "at", "ORIENT", "CODING",
    "LV", "LV-AM", "LV-PM", "HOL",
    "USAFP", "DEP",
})


def parse_args():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--profiles", default="/tmp/rotation_profiles.json")
    p.add_argument("--output", default="/tmp/learned_constraints.json")
    p.add_argument("--diff-report", default="/tmp/constraint_diff.md")
    p.add_argument("--db-url", default=os.getenv(
        "DATABASE_URL",
        "postgresql://scheduler@localhost:5432/residency_scheduler",
    ))
    return p.parse_args()


def confidence_tier(n):
    """Return confidence tier based on sample size."""
    if n >= 8:
        return "high"
    elif n >= 4:
        return "medium"
    else:
        return "low"


def fetch_existing_requirements(cur):
    """Fetch existing rotation_activity_requirements with template/activity names."""
    cur.execute("""
        SELECT
            rt.name AS template_name,
            a.code AS activity_code,
            rar.min_halfdays,
            rar.max_halfdays,
            rar.target_halfdays,
            rar.prefer_full_days,
            rar.priority,
            rar.applicable_weeks
        FROM rotation_activity_requirements rar
        JOIN rotation_templates rt ON rar.rotation_template_id = rt.id
        JOIN activities a ON rar.activity_id = a.id
        ORDER BY rt.name, a.code
    """)
    reqs = {}
    for row in cur.fetchall():
        key = (row[0], row[1])
        reqs[key] = {
            "template_name": row[0],
            "activity_code": row[1],
            "min_halfdays": row[2],
            "max_halfdays": row[3],
            "target_halfdays": row[4],
            "prefer_full_days": row[5],
            "priority": row[6],
            "applicable_weeks": row[7],
        }
    return reqs


def fetch_block_assignment_mapping(cur):
    """Fetch primary block_assignment → template mapping."""
    cur.execute("""
        SELECT
            ba.resident_id::text,
            ba.block_number,
            rt.name AS template_name
        FROM block_assignments ba
        JOIN rotation_templates rt ON ba.rotation_template_id = rt.id
        WHERE ba.academic_year = 2025
    """)
    mapping = {}
    for row in cur.fetchall():
        key = (row[0], row[1])
        mapping[key] = row[2]
    return mapping


def fetch_secondary_template_mapping(cur):
    """Fetch secondary (split-block) template mapping."""
    cur.execute("""
        SELECT
            ba.resident_id::text,
            ba.block_number,
            rt.name AS template_name
        FROM block_assignments ba
        JOIN rotation_templates rt ON ba.secondary_rotation_template_id = rt.id
        WHERE ba.academic_year = 2025
            AND ba.secondary_rotation_template_id IS NOT NULL
    """)
    mapping = {}
    for row in cur.fetchall():
        key = (row[0], row[1])
        mapping[key] = row[2]
    return mapping


def learn_activity_stats(code_observations, n, code_day_tod, code_full_day_count,
                         code_half_day_only):
    """Compute learned constraint stats for a set of code observations."""
    tier = confidence_tier(n)
    padding = 2 if tier == "medium" else 0

    template_learned = {}
    anomalies = []

    for code, counts in sorted(code_observations.items()):
        arr = np.array(counts, dtype=float)
        nonzero = arr[arr > 0]

        presence_rate = len(nonzero) / n
        if presence_rate < 0.25:
            continue

        p5 = np.percentile(arr, 5) if len(arr) > 1 else arr[0]
        p50 = np.percentile(arr, 50)
        p95 = np.percentile(arr, 95) if len(arr) > 1 else arr[0]

        # Apply padding for medium confidence
        learned_min = max(0, int(round(p5)) - padding)
        learned_max = min(28, int(round(p95)) + padding)
        learned_target = min(learned_max, max(learned_min, int(round(p50))))

        # Anomaly detection: z-score > 2
        if len(arr) >= 3:
            mean = arr.mean()
            std = arr.std()
            if std > 0:
                for i, val in enumerate(arr):
                    z = abs(val - mean) / std
                    if z > 2.0:
                        anomalies.append({
                            "activity_code": code,
                            "instance_index": i,
                            "value": int(val),
                            "mean": round(float(mean), 1),
                            "std": round(float(std), 1),
                            "z_score": round(float(z), 2),
                        })

        # Prefer full days
        full = code_full_day_count.get(code, 0)
        half = code_half_day_only.get(code, 0)
        prefer_full = full > half if (full + half) > 0 else True

        # Day preferences
        day_counts = defaultdict(int)
        for (day_name, tod), cnt in code_day_tod.get(code, {}).items():
            day_counts[day_name] += cnt
        total_day_counts = sum(day_counts.values())

        preferred_days = []
        avoid_days = []
        if total_day_counts > 0:
            day_names_ordered = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
            for d in day_names_ordered:
                rate = day_counts.get(d, 0) / total_day_counts * 7
                if rate > 1.5:
                    preferred_days.append(d)
                elif rate < 0.2 and n >= 3:
                    avoid_days.append(d)

        template_learned[code] = {
            "activity_code": code,
            "is_background": code in BACKGROUND_CODES,
            "instances": n,
            "confidence": tier,
            "presence_rate": round(presence_rate, 2),
            "mean_count": round(float(arr.mean()), 1),
            "learned_min": learned_min,
            "learned_target": learned_target,
            "learned_max": learned_max,
            "padding_applied": padding,
            "prefer_full_days": prefer_full,
            "preferred_days": preferred_days or None,
            "avoid_days": avoid_days or None,
        }

    return template_learned, anomalies


def learn_from_profiles(profiles, ba_mapping, secondary_mapping):
    """Group profiles by assigned template, compute stats per activity code.

    Split-block-aware: for split-block profiles, learns separately for
    weeks 1-2 (primary template) and weeks 3-4 (secondary template).
    """
    # Group profiles by template
    # For split blocks, create two entries: one for primary (weeks 1-2), one for secondary (weeks 3-4)
    by_template = defaultdict(list)  # template_name → list of (profile, week_filter)
    split_block_count = 0

    for p in profiles:
        key = (p["person_id"], p["block_number"])
        primary_template = ba_mapping.get(key) or p.get("assigned_template")
        secondary_template = secondary_mapping.get(key) or p.get("secondary_template")

        if p.get("is_split_block") and secondary_template and primary_template:
            # Split-block: learn from week halves separately
            split_block_count += 1
            by_template[primary_template].append((p, "weeks_1_2"))
            by_template[secondary_template].append((p, "weeks_3_4"))
        elif primary_template:
            # Non-split: learn from whole block
            by_template[primary_template].append((p, "all"))

    print(f"  Split-block profiles separated: {split_block_count}")

    learned = {}
    all_anomalies = {}

    for template_name, profile_entries in sorted(by_template.items()):
        n = len(profile_entries)
        if n < 2:
            continue

        code_observations = defaultdict(list)
        total_hdas_list = []
        code_day_tod = defaultdict(lambda: defaultdict(int))
        code_full_day_count = defaultdict(int)
        code_half_day_only = defaultdict(int)

        # Track which week filter is used (for applicable_weeks output)
        week_filters = set(wf for _, wf in profile_entries)
        applicable_weeks = None
        if week_filters == {"weeks_1_2"}:
            applicable_weeks = [1, 2]
        elif week_filters == {"weeks_3_4"}:
            applicable_weeks = [3, 4]

        for p, week_filter in profile_entries:
            split_hdas = p.get("split_week_hdas", {})

            if week_filter == "weeks_1_2" and split_hdas:
                counts = split_hdas.get("weeks_1_2", {})
                total = sum(counts.values())
            elif week_filter == "weeks_3_4" and split_hdas:
                counts = split_hdas.get("weeks_3_4", {})
                total = sum(counts.values())
            else:
                counts = p["code_counts"]
                total = p["total_hdas"]

            total_hdas_list.append(total)
            for code, count in counts.items():
                code_observations[code].append(count)

            # Weekly pattern analysis (use full pattern for day prefs)
            for week_data in p.get("weekly_pattern", []):
                week_num = week_data.get("week", 0)
                # Filter by applicable weeks
                if week_filter == "weeks_1_2" and week_num > 2:
                    continue
                if week_filter == "weeks_3_4" and week_num <= 2:
                    continue

                for slot_key, code in week_data.items():
                    if slot_key == "week":
                        continue
                    parts = slot_key.split("_")
                    if len(parts) == 2:
                        day_name, tod = parts
                        code_day_tod[code][(day_name, tod)] += 1

                for day_name in ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]:
                    am = week_data.get(f"{day_name}_am")
                    pm = week_data.get(f"{day_name}_pm")
                    if am and pm and am == pm:
                        code_full_day_count[am] += 1
                    elif am:
                        code_half_day_only[am] += 1
                    elif pm:
                        code_half_day_only[pm] += 1

        # Pad observations
        for code in code_observations:
            while len(code_observations[code]) < n:
                code_observations[code].append(0)

        template_learned, anomalies = learn_activity_stats(
            code_observations, n, code_day_tod, code_full_day_count,
            code_half_day_only,
        )

        if template_learned:
            # Tag all constraints with applicable_weeks if this is a split-block half
            if applicable_weeks:
                for lc in template_learned.values():
                    lc["applicable_weeks"] = applicable_weeks

            learned[template_name] = {
                "template_name": template_name,
                "n_instances": n,
                "confidence": confidence_tier(n),
                "avg_total_hdas": round(np.mean(total_hdas_list), 1),
                "applicable_weeks": applicable_weeks,
                "activities": template_learned,
            }
            if anomalies:
                all_anomalies[template_name] = anomalies

    return learned, all_anomalies


def generate_diff_report(learned, existing_reqs, anomalies):
    """Generate markdown diff between learned and existing constraints."""
    lines = ["# Constraint Diff Report (v2 — split-block aware)", ""]
    lines.append("Comparing **learned** constraints (from historical HDAs) to **existing** rotation_activity_requirements.\n")

    stats = {"matched": 0, "tighter": 0, "wider": 0, "missing_existing": 0,
             "missing_learned": 0, "high_confidence": 0, "medium_confidence": 0,
             "low_confidence": 0}

    for template_name, tdata in sorted(learned.items()):
        template_lines = []
        has_diff = False

        for code, lc in sorted(tdata["activities"].items()):
            key = (template_name, code)
            existing = existing_reqs.get(key)
            tier = lc.get("confidence", "low")
            tier_tag = f" [{tier}]"
            stats[f"{tier}_confidence"] += 1

            if existing:
                e_min = existing["min_halfdays"]
                e_max = existing["max_halfdays"]
                e_tgt = existing["target_halfdays"]
                l_min = lc["learned_min"]
                l_max = lc["learned_max"]
                l_tgt = lc["learned_target"]

                diffs = []
                if l_min != e_min:
                    diffs.append(f"min: {e_min}→{l_min}")
                if l_max != e_max:
                    diffs.append(f"max: {e_max}→{l_max}")
                if e_tgt is not None and l_tgt != e_tgt:
                    diffs.append(f"target: {e_tgt}→{l_tgt}")

                if diffs:
                    has_diff = True
                    range_change = "tighter" if (l_max - l_min) < (e_max - e_min) else "wider"
                    stats[range_change] += 1
                    weeks_tag = f" weeks={lc.get('applicable_weeks')}" if lc.get("applicable_weeks") else ""
                    template_lines.append(
                        f"  - `{code}`: {', '.join(diffs)} ({range_change}, "
                        f"{lc['presence_rate']:.0%} presence, n={lc['instances']}{tier_tag}{weeks_tag})"
                    )
                else:
                    stats["matched"] += 1
            else:
                if not lc["is_background"] and lc["presence_rate"] >= 0.5:
                    has_diff = True
                    stats["missing_existing"] += 1
                    weeks_tag = f", weeks={lc.get('applicable_weeks')}" if lc.get("applicable_weeks") else ""
                    template_lines.append(
                        f"  - `{code}`: **NEW** — min={lc['learned_min']}, "
                        f"max={lc['learned_max']}, target={lc['learned_target']} "
                        f"({lc['presence_rate']:.0%} presence, n={lc['instances']}{tier_tag}{weeks_tag})"
                    )

        if has_diff and template_lines:
            weeks_label = f" [weeks {tdata.get('applicable_weeks')}]" if tdata.get("applicable_weeks") else ""
            lines.append(f"\n### {template_name} (n={tdata['n_instances']}, {tdata['confidence']}){weeks_label}")
            lines.extend(template_lines)

    # Orphaned requirements
    learned_keys = set()
    for tname, tdata in learned.items():
        for code in tdata["activities"]:
            learned_keys.add((tname, code))

    orphan_lines = []
    for key, req in sorted(existing_reqs.items()):
        tname, code = key
        if tname in learned and key not in learned_keys:
            stats["missing_learned"] += 1
            orphan_lines.append(
                f"  - `{tname}` → `{code}`: exists in DB but never observed in data"
            )

    if orphan_lines:
        lines.append("\n### Orphaned Requirements (in DB, not in data)")
        lines.extend(orphan_lines[:30])
        if len(orphan_lines) > 30:
            lines.append(f"  ... and {len(orphan_lines) - 30} more")

    # Anomalies section
    if anomalies:
        lines.append("\n---\n### Anomaly Detection (z-score > 2.0)")
        for tname, anom_list in sorted(anomalies.items()):
            lines.append(f"\n**{tname}:**")
            for a in anom_list[:5]:
                lines.append(
                    f"  - `{a['activity_code']}`: instance #{a['instance_index']} "
                    f"value={a['value']} (mean={a['mean']}, std={a['std']}, z={a['z_score']})"
                )

    # Summary
    summary = (
        f"**Summary:** {stats['matched']} matched, {stats['tighter']} tighter, "
        f"{stats['wider']} wider, {stats['missing_existing']} new (missing from DB), "
        f"{stats['missing_learned']} orphaned (in DB, not observed)\n\n"
        f"**Confidence tiers:** {stats['high_confidence']} high, "
        f"{stats['medium_confidence']} medium, {stats['low_confidence']} low\n"
    )
    lines.insert(2, summary)

    return "\n".join(lines), stats


def main():
    args = parse_args()

    print("Loading profiles...")
    profiles = json.loads(Path(args.profiles).read_text())
    meaningful = [p for p in profiles if p.get("rotation_category") != "background_only"]
    print(f"  {len(meaningful)} meaningful profiles")

    conn = psycopg2.connect(args.db_url)
    cur = conn.cursor()

    print("Fetching existing requirements...")
    existing_reqs = fetch_existing_requirements(cur)
    print(f"  {len(existing_reqs)} existing rotation_activity_requirements")

    print("Fetching primary block assignment mapping...")
    ba_mapping = fetch_block_assignment_mapping(cur)
    print(f"  {len(ba_mapping)} primary block assignments")

    print("Fetching secondary (split-block) template mapping...")
    secondary_mapping = fetch_secondary_template_mapping(cur)
    print(f"  {len(secondary_mapping)} secondary template assignments")

    conn.close()

    print("\nLearning constraints from historical data (split-block aware)...")
    learned, anomalies = learn_from_profiles(meaningful, ba_mapping, secondary_mapping)
    print(f"  Learned constraints for {len(learned)} templates")

    for tname, tdata in sorted(learned.items()):
        fg = {c: d for c, d in tdata["activities"].items() if not d["is_background"]}
        bg = {c: d for c, d in tdata["activities"].items() if d["is_background"]}
        weeks = f" weeks={tdata['applicable_weeks']}" if tdata.get("applicable_weeks") else ""
        print(f"    {tname:45s} n={tdata['n_instances']:2d}  "
              f"[{tdata['confidence']}] fg={len(fg)}, bg={len(bg)}{weeks}")

    if anomalies:
        total_anomalies = sum(len(v) for v in anomalies.values())
        print(f"\n  Anomalies detected: {total_anomalies} across {len(anomalies)} templates")

    print("\nGenerating diff report...")
    diff_md, stats = generate_diff_report(learned, existing_reqs, anomalies)

    print(f"\n{'='*60}")
    print(f"  CONSTRAINT DIFF SUMMARY (v2)")
    print(f"{'='*60}")
    print(f"  Matched:            {stats['matched']}")
    print(f"  Tighter:            {stats['tighter']}")
    print(f"  Wider:              {stats['wider']}")
    print(f"  New (add to DB):    {stats['missing_existing']}")
    print(f"  Orphaned:           {stats['missing_learned']}")
    print(f"  High confidence:    {stats['high_confidence']}")
    print(f"  Medium confidence:  {stats['medium_confidence']}")
    print(f"  Low confidence:     {stats['low_confidence']}")

    out_path = Path(args.output)
    out_path.write_text(json.dumps(learned, indent=2, default=str))
    print(f"\n  Learned constraints: {out_path} ({out_path.stat().st_size / 1024:.1f} KB)")

    diff_path = Path(args.diff_report)
    diff_path.write_text(diff_md)
    print(f"  Diff report: {diff_path}")


if __name__ == "__main__":
    main()
