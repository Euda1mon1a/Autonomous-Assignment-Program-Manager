#!/usr/bin/env python3
"""Mine co-occurrence rules from rotation profiles using Apriori.

Models each person-week as a transaction with activity codes as items.
Discovers association rules like: {FMIT} → {CALL}, {PGY-1, fm_clinic} → {PI}.

Usage:
    cd ~/workspace/aapm
    backend/.venv/bin/python scripts/ml/mine_rules.py \
        --profiles /tmp/rotation_profiles.json \
        --output /tmp/association_rules.json
"""

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path

import pandas as pd
from mlxtend.frequent_patterns import fpgrowth, association_rules
from mlxtend.preprocessing import TransactionEncoder


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
    p.add_argument("--output", default="/tmp/association_rules.json")
    p.add_argument("--min-support", type=float, default=0.03)
    p.add_argument("--min-confidence", type=float, default=0.6)
    return p.parse_args()


def profiles_to_transactions(profiles):
    """Convert rotation profiles into transactions (one per person-week).

    Each transaction = set of activity codes active that week +
    context tags like PGY-1, resident, faculty, etc.
    """
    transactions = []

    for p in profiles:
        if p.get("rotation_category") == "background_only":
            continue

        pgy = p["pgy_level"]
        ptype = p["person_type"]

        for week_data in p.get("weekly_pattern", []):
            items = set()

            # Activity codes this week
            for slot_key, code in week_data.items():
                if slot_key == "week":
                    continue
                items.add(code)

            if not items:
                continue

            # Add context tags
            if pgy:
                items.add(f"_PGY{pgy}")
            if ptype == "faculty":
                items.add("_FACULTY")
            else:
                items.add("_RESIDENT")

            # Add foreground/background tags
            fg_in_week = items & (items - BACKGROUND_CODES - {f"_PGY{i}" for i in [1,2,3]} - {"_FACULTY", "_RESIDENT"})
            if fg_in_week:
                for fg in fg_in_week:
                    items.add(f"_FG:{fg}")

            transactions.append(items)

    return transactions


def profiles_to_block_transactions(profiles):
    """Convert to block-level transactions (coarser, better for cross-activity rules)."""
    transactions = []

    for p in profiles:
        if p.get("rotation_category") == "background_only":
            continue

        items = set()
        pgy = p["pgy_level"]
        ptype = p["person_type"]

        # All activity codes in the block
        for code in p.get("unique_codes", []):
            items.add(code)

        if not items:
            continue

        # Context
        if pgy:
            items.add(f"_PGY{pgy}")
        if ptype == "faculty":
            items.add("_FACULTY")
        else:
            items.add("_RESIDENT")

        # Rotation category
        items.add(f"_CAT:{p['rotation_category']}")

        # Split flag
        if p.get("is_split_block"):
            items.add("_SPLIT")

        transactions.append(items)

    return transactions


def run_apriori(transactions, min_support, min_confidence, label=""):
    """Run Apriori and return association rules."""
    te = TransactionEncoder()
    te_arr = te.fit_transform(transactions)
    df = pd.DataFrame(te_arr, columns=te.columns_)

    print(f"\n  {label}: {len(transactions)} transactions, {len(te.columns_)} unique items")

    # Frequent itemsets
    freq = fpgrowth(df, min_support=min_support, use_colnames=True, max_len=3)
    print(f"  Frequent itemsets: {len(freq)}")

    if len(freq) == 0:
        return []

    # Association rules
    rules = association_rules(freq, metric="confidence", min_threshold=min_confidence)
    rules = rules.sort_values("lift", ascending=False)
    print(f"  Rules (conf >= {min_confidence}): {len(rules)}")

    # Convert to serializable format
    result = []
    for _, row in rules.iterrows():
        result.append({
            "antecedent": sorted(row["antecedents"]),
            "consequent": sorted(row["consequents"]),
            "support": round(float(row["support"]), 4),
            "confidence": round(float(row["confidence"]), 4),
            "lift": round(float(row["lift"]), 2),
            "conviction": round(float(row["conviction"]), 2) if row["conviction"] < 100 else 99.0,
        })

    return result


def classify_rules(rules):
    """Classify rules into categories based on content."""
    classified = []

    for r in rules:
        ant = r["antecedent"]
        con = r["consequent"]
        all_items = ant + con

        # Determine type
        has_pgy = any(i.startswith("_PGY") for i in all_items)
        has_faculty = "_FACULTY" in all_items
        has_resident = "_RESIDENT" in all_items
        has_fg = any(i.startswith("_FG:") for i in all_items)
        has_context_only = all(i.startswith("_") for i in all_items)

        # Skip pure context rules
        if has_context_only:
            continue

        # Classify
        if has_pgy and not has_faculty:
            rule_type = "pgy_specific"
        elif has_faculty:
            rule_type = "faculty_specific"
        elif has_resident:
            rule_type = "resident_general"
        else:
            rule_type = "universal"

        # Check if it's a co-occurrence or implication
        ant_codes = [i for i in ant if not i.startswith("_")]
        con_codes = [i for i in con if not i.startswith("_")]

        if ant_codes and con_codes:
            pattern_type = "activity_cooccurrence"
        elif ant_codes and not con_codes:
            pattern_type = "context_implication"
        else:
            pattern_type = "context_driven"

        r["rule_type"] = rule_type
        r["pattern_type"] = pattern_type
        classified.append(r)

    return classified


def main():
    args = parse_args()

    print("Loading profiles...")
    profiles = json.loads(Path(args.profiles).read_text())
    meaningful = [p for p in profiles if p.get("rotation_category") != "background_only"]
    print(f"  {len(meaningful)} meaningful profiles")

    # Weekly transactions
    print("\n" + "="*60)
    print("  WEEKLY TRANSACTION MINING")
    print("="*60)
    weekly_txns = profiles_to_transactions(meaningful)
    weekly_rules = run_apriori(
        weekly_txns, args.min_support, args.min_confidence,
        label="Weekly",
    )

    # Block-level transactions
    print("\n" + "="*60)
    print("  BLOCK-LEVEL TRANSACTION MINING")
    print("="*60)
    block_txns = profiles_to_block_transactions(meaningful)
    block_rules = run_apriori(
        block_txns, args.min_support, args.min_confidence,
        label="Block",
    )

    # Classify all rules
    all_rules = classify_rules(weekly_rules) + classify_rules(block_rules)

    # Summary
    print(f"\n{'='*60}")
    print(f"  RULE SUMMARY")
    print(f"{'='*60}")

    type_counts = Counter(r["rule_type"] for r in all_rules)
    print(f"  Total classified rules: {len(all_rules)}")
    for rtype, count in type_counts.most_common():
        print(f"    {rtype:25s} {count:3d}")

    pattern_counts = Counter(r["pattern_type"] for r in all_rules)
    for ptype, count in pattern_counts.most_common():
        print(f"    {ptype:25s} {count:3d}")

    # Top rules by lift
    print(f"\n  Top 20 rules by lift:")
    sorted_rules = sorted(all_rules, key=lambda r: r["lift"], reverse=True)
    for r in sorted_rules[:20]:
        ant_str = " + ".join(r["antecedent"])
        con_str = " + ".join(r["consequent"])
        print(f"    {ant_str:35s} → {con_str:20s}  "
              f"conf={r['confidence']:.0%}  lift={r['lift']:.1f}  "
              f"[{r['rule_type']}, {r['pattern_type']}]")

    # Write output
    output = {
        "n_weekly_transactions": len(weekly_txns),
        "n_block_transactions": len(block_txns),
        "n_weekly_rules": len(weekly_rules),
        "n_block_rules": len(block_rules),
        "n_classified_rules": len(all_rules),
        "rules": sorted_rules,
    }

    out_path = Path(args.output)
    out_path.write_text(json.dumps(output, indent=2))
    print(f"\n  Output: {out_path} ({out_path.stat().st_size / 1024:.1f} KB)")


if __name__ == "__main__":
    main()
