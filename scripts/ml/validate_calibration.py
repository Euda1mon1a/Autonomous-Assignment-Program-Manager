#!/usr/bin/env python3
"""Leave-one-block-out cross-validation for learned constraints.

For each block B in [2..11], learns constraints from all other blocks,
then checks what % of Block B's actual activity counts fall within the
learned bounds. Pure statistical validation — no DB writes, no solver runs.

Usage:
    cd ~/workspace/aapm
    backend/.venv/bin/python scripts/ml/validate_calibration.py \
        --profiles /tmp/rotation_profiles_v2.json \
        --output /tmp/validation_results.json
"""

import argparse
import json
import os
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
import psycopg2

BACKGROUND_CODES = frozenset({
    "fm_clinic", "lec", "gme", "RETREAT", "PI", "W", "off", "recovery",
    "CC", "SIM", "ADV", "CCC", "HLC", "HR-SUP", "pcat", "do", "dfm",
    "at", "ORIENT", "CODING",
    "LV", "LV-AM", "LV-PM", "HOL",
    "USAFP", "DEP",
})


def parse_args():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--profiles", default="/tmp/rotation_profiles_v2.json")
    p.add_argument("--output", default="/tmp/validation_results.json")
    p.add_argument("--db-url", default=os.getenv(
        "DATABASE_URL",
        "postgresql://scheduler@localhost:5432/residency_scheduler",
    ))
    return p.parse_args()


def confidence_tier(n):
    if n >= 8:
        return "high"
    elif n >= 4:
        return "medium"
    else:
        return "low"


def fetch_template_mappings(cur):
    """Fetch primary + secondary template mappings.

    Primary rows have block_half IS NULL (full block) or block_half = 1 (first half).
    Secondary rows have block_half = 2 (days 15-28).
    """
    cur.execute("""
        SELECT ba.resident_id::text, ba.block_number,
               rt.name AS template_name,
               ba.block_half
        FROM block_assignments ba
        JOIN rotation_templates rt ON ba.rotation_template_id = rt.id
        WHERE ba.academic_year = 2025
    """)
    primary = {}
    secondary = {}
    for row in cur.fetchall():
        key = (row[0], row[1])
        block_half = row[3]
        if block_half == 2:
            secondary[key] = row[2]
        else:
            # block_half IS NULL (full block) or 1 (first half) → primary
            primary[key] = row[2]
    return primary, secondary


def learn_constraints_from_subset(profiles, ba_mapping, secondary_mapping):
    """Learn constraints from a subset of profiles (same logic as learn_constraints.py v2)."""
    by_template = defaultdict(list)

    for p in profiles:
        key = (p["person_id"], p["block_number"])
        primary_template = ba_mapping.get(key) or p.get("assigned_template")
        secondary_template = secondary_mapping.get(key) or p.get("secondary_template")

        if p.get("is_split_block") and secondary_template and primary_template:
            by_template[primary_template].append((p, "weeks_1_2"))
            by_template[secondary_template].append((p, "weeks_3_4"))
        elif primary_template:
            by_template[primary_template].append((p, "all"))

    learned = {}
    for template_name, profile_entries in by_template.items():
        n = len(profile_entries)
        if n < 2:
            continue

        code_observations = defaultdict(list)
        tier = confidence_tier(n)
        padding = 2 if tier == "medium" else 0

        for p, week_filter in profile_entries:
            split_hdas = p.get("split_week_hdas", {})
            if week_filter == "weeks_1_2" and split_hdas:
                counts = split_hdas.get("weeks_1_2", {})
            elif week_filter == "weeks_3_4" and split_hdas:
                counts = split_hdas.get("weeks_3_4", {})
            else:
                counts = p["code_counts"]

            for code, count in counts.items():
                code_observations[code].append(count)

        # Pad to n
        for code in code_observations:
            while len(code_observations[code]) < n:
                code_observations[code].append(0)

        template_learned = {}
        for code, counts_list in code_observations.items():
            arr = np.array(counts_list, dtype=float)
            nonzero = arr[arr > 0]
            presence_rate = len(nonzero) / n
            if presence_rate < 0.25:
                continue

            p5 = np.percentile(arr, 5) if len(arr) > 1 else arr[0]
            p95 = np.percentile(arr, 95) if len(arr) > 1 else arr[0]
            p50 = np.percentile(arr, 50)

            template_learned[code] = {
                "learned_min": max(0, int(round(p5)) - padding),
                "learned_max": min(28, int(round(p95)) + padding),
                "learned_target": int(round(p50)),
                "confidence": tier,
                "is_background": code in BACKGROUND_CODES,
            }

        if template_learned:
            learned[template_name] = template_learned

    return learned


def evaluate_block(held_out_profiles, learned, ba_mapping, secondary_mapping):
    """Evaluate learned constraints against held-out block profiles."""
    results = []

    for p in held_out_profiles:
        key = (p["person_id"], p["block_number"])
        primary_template = ba_mapping.get(key) or p.get("assigned_template")
        secondary_template = secondary_mapping.get(key) or p.get("secondary_template")

        # Determine which template(s) and code_counts to check
        checks = []
        if p.get("is_split_block") and secondary_template and primary_template:
            split_hdas = p.get("split_week_hdas", {})
            checks.append((primary_template, split_hdas.get("weeks_1_2", {})))
            checks.append((secondary_template, split_hdas.get("weeks_3_4", {})))
        elif primary_template:
            checks.append((primary_template, p["code_counts"]))

        for template_name, actual_counts in checks:
            if template_name not in learned:
                continue

            template_constraints = learned[template_name]

            for code, constraint in template_constraints.items():
                actual = actual_counts.get(code, 0)
                l_min = constraint["learned_min"]
                l_max = constraint["learned_max"]
                l_target = constraint["learned_target"]

                contained = l_min <= actual <= l_max
                target_error = abs(actual - l_target)

                results.append({
                    "template_name": template_name,
                    "activity_code": code,
                    "actual": actual,
                    "learned_min": l_min,
                    "learned_max": l_max,
                    "learned_target": l_target,
                    "contained": contained,
                    "target_error": target_error,
                    "is_background": constraint["is_background"],
                    "confidence": constraint["confidence"],
                    "block_number": p["block_number"],
                    "is_split_block": p.get("is_split_block", False),
                    "rotation_category": p.get("rotation_category", "unknown"),
                })

    return results


def main():
    args = parse_args()

    print("Loading profiles...")
    profiles = json.loads(Path(args.profiles).read_text())
    meaningful = [p for p in profiles if p.get("rotation_category") != "background_only"]
    print(f"  {len(meaningful)} meaningful profiles")

    conn = psycopg2.connect(args.db_url)
    cur = conn.cursor()
    ba_mapping, secondary_mapping = fetch_template_mappings(cur)
    conn.close()
    print(f"  {len(ba_mapping)} primary, {len(secondary_mapping)} secondary template mappings")

    # Get unique blocks
    blocks = sorted(set(p["block_number"] for p in meaningful))
    print(f"  Blocks: {blocks}")

    # Leave-one-block-out cross-validation
    all_results = []
    block_summaries = {}

    for held_out_block in blocks:
        if held_out_block < 2:
            # Block 1 often has orientation anomalies, skip
            continue

        train_profiles = [p for p in meaningful if p["block_number"] != held_out_block]
        test_profiles = [p for p in meaningful if p["block_number"] == held_out_block]

        if not test_profiles:
            continue

        print(f"\n  Block {held_out_block}: train={len(train_profiles)}, test={len(test_profiles)}")

        # Learn from training set
        learned = learn_constraints_from_subset(
            train_profiles, ba_mapping, secondary_mapping
        )

        # Evaluate on held-out block
        results = evaluate_block(test_profiles, learned, ba_mapping, secondary_mapping)
        all_results.extend(results)

        # Block-level summary
        if results:
            contained = sum(1 for r in results if r["contained"])
            total = len(results)
            errors = [r["target_error"] for r in results]
            block_summaries[held_out_block] = {
                "n_checks": total,
                "containment_rate": round(contained / total, 3),
                "mean_target_error": round(np.mean(errors), 2),
                "median_target_error": round(np.median(errors), 2),
            }
            print(f"    Containment: {contained}/{total} = {contained/total:.1%}, "
                  f"MAE={np.mean(errors):.1f}")

    # Aggregate metrics
    print(f"\n{'='*60}")
    print(f"  CROSS-VALIDATION SUMMARY")
    print(f"{'='*60}")

    if not all_results:
        print("  No results to report.")
        Path(args.output).write_text(json.dumps({"error": "no results"}, indent=2))
        return

    # Overall containment
    total_contained = sum(1 for r in all_results if r["contained"])
    total_checks = len(all_results)
    overall_rate = total_contained / total_checks
    print(f"  Overall containment: {total_contained}/{total_checks} = {overall_rate:.1%}")

    # By confidence tier
    for tier in ["high", "medium", "low"]:
        subset = [r for r in all_results if r["confidence"] == tier]
        if subset:
            contained = sum(1 for r in subset if r["contained"])
            errors = [r["target_error"] for r in subset]
            print(f"  {tier:8s}: {contained}/{len(subset)} = {contained/len(subset):.1%}, "
                  f"MAE={np.mean(errors):.1f}")

    # By background vs foreground
    for bg_label, bg_val in [("foreground", False), ("background", True)]:
        subset = [r for r in all_results if r["is_background"] == bg_val]
        if subset:
            contained = sum(1 for r in subset if r["contained"])
            errors = [r["target_error"] for r in subset]
            print(f"  {bg_label:12s}: {contained}/{len(subset)} = {contained/len(subset):.1%}, "
                  f"MAE={np.mean(errors):.1f}")

    # By rotation category
    cat_groups = defaultdict(list)
    for r in all_results:
        cat_groups[r["rotation_category"]].append(r)
    for cat, subset in sorted(cat_groups.items()):
        contained = sum(1 for r in subset if r["contained"])
        print(f"  {cat:20s}: {contained}/{len(subset)} = {contained/len(subset):.1%}")

    # By split-block
    for split_label, split_val in [("non-split", False), ("split-block", True)]:
        subset = [r for r in all_results if r["is_split_block"] == split_val]
        if subset:
            contained = sum(1 for r in subset if r["contained"])
            print(f"  {split_label:12s}: {contained}/{len(subset)} = {contained/len(subset):.1%}")

    # Worst templates (lowest containment)
    template_results = defaultdict(list)
    for r in all_results:
        template_results[r["template_name"]].append(r)

    print(f"\n  Per-template containment (worst 10):")
    template_rates = {}
    for tname, results in template_results.items():
        contained = sum(1 for r in results if r["contained"])
        rate = contained / len(results)
        template_rates[tname] = rate

    for tname, rate in sorted(template_rates.items(), key=lambda x: x[1])[:10]:
        n = len(template_results[tname])
        print(f"    {tname:40s} {rate:.1%}  (n={n})")

    # Write output
    output = {
        "n_total_checks": total_checks,
        "overall_containment_rate": round(overall_rate, 4),
        "overall_mean_target_error": round(float(np.mean([r["target_error"] for r in all_results])), 2),
        "block_summaries": block_summaries,
        "template_containment_rates": template_rates,
        "by_confidence": {},
        "by_category": {},
    }

    for tier in ["high", "medium", "low"]:
        subset = [r for r in all_results if r["confidence"] == tier]
        if subset:
            contained = sum(1 for r in subset if r["contained"])
            output["by_confidence"][tier] = {
                "n": len(subset),
                "containment_rate": round(contained / len(subset), 4),
                "mean_target_error": round(float(np.mean([r["target_error"] for r in subset])), 2),
            }

    for cat, subset in cat_groups.items():
        contained = sum(1 for r in subset if r["contained"])
        output["by_category"][cat] = {
            "n": len(subset),
            "containment_rate": round(contained / len(subset), 4),
        }

    out_path = Path(args.output)
    out_path.write_text(json.dumps(output, indent=2, default=str))
    print(f"\n  Output: {out_path} ({out_path.stat().st_size / 1024:.1f} KB)")


if __name__ == "__main__":
    main()
