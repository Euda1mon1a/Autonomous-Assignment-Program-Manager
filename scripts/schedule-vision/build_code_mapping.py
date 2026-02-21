"""Audit and build deterministic display-code mapping from schedule facts.

Classifies all ~60 display codes into:
  - DETERMINISTIC: 1:1 map from (activity_code, rotation, person_type, weekend)
  - CONTEXTUAL: requires rules (NF expansion, weekend collapse, clinic mapping)
  - AMBIGUOUS: requires ML or coordinator review

Outputs:
  - data/code_mapping.json — the deterministic mapping table
  - data/code_audit.json — full classification with stats
  - Console report with coverage analysis

Usage:
    python build_code_mapping.py --features data/features_universal.json
    python build_code_mapping.py --features data/features_universal.json --output data/code_mapping.json
"""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path


# ── All known display codes from compare.py ──────────────────────
# Grouped by semantic category

DISPLAY_CODES = {
    # Clinic variants — all map from "C" activity with context
    "clinic": ["C", "CC", "C40", "C30", "CCC", "C-I", "C-N"],
    # Night float variants — map from NF activity + rotation context
    "night_float": ["NF", "PedsNF", "L&D", "Endo"],
    # Inpatient rotations — 1:1 from rotation template
    "inpatient": ["FMIT", "IMW", "KAP", "PedW", "OB"],
    # Faculty admin — 1:1 from activity code
    "faculty_admin": ["GME", "AT", "DO", "CV", "DFM", "ADV", "PCAT"],
    # Educational — 1:1 from activity code
    "educational": ["LEC", "SIM"],
    # Time off / leave — 1:1 from activity or absence type
    "time_off": ["W", "OFF", "LV", "DEP", "TDY", "USAFP", "SLV", "FLX"],
    # Specialty rotations — 1:1 from rotation template
    "specialty": ["SM", "aSM", "GYN", "NEURO", "ENT", "Ophtho", "URO"],
    # Procedures — 1:1 from activity code
    "procedures": ["PR", "US", "VAS"],
    # Other — 1:1 from activity code
    "other": ["PI", "HC", "HV", "ADM", "PC"],
}


def classify_codes() -> dict[str, dict]:
    """Classify each display code as deterministic, contextual, or ambiguous.

    Returns dict of {code: {category, classification, rule, notes}}.
    """
    classifications = {}

    # ── DETERMINISTIC: 1:1 map from activity/rotation code ──
    deterministic_1to1 = {
        # Inpatient rotations: rotation_template.abbreviation IS the display code
        "FMIT": "rotation_template.abbreviation = 'FMIT'",
        "IMW": "rotation_template.abbreviation = 'IMW' (or CODE_NORM: IM → IMW)",
        "KAP": "rotation_template.abbreviation = 'KAP'",
        "PedW": "rotation_template.abbreviation = 'PedW'",
        "OB": "rotation_template.abbreviation = 'OB'",
        # Faculty admin: activity.display_abbreviation IS the code
        "GME": "activity.display_abbreviation = 'GME'",
        "AT": "activity.display_abbreviation = 'AT'",
        "DO": "activity.display_abbreviation = 'DO'",
        "CV": "activity.display_abbreviation = 'CV'",
        "DFM": "activity.display_abbreviation = 'DFM'",
        "ADV": "activity.display_abbreviation = 'ADV'",
        "PCAT": "activity.display_abbreviation = 'PCAT'",
        # Educational
        "LEC": "activity.display_abbreviation = 'LEC'",
        "SIM": "activity.display_abbreviation = 'SIM'",
        # Time off (simple)
        "OFF": "activity.code = 'off'",
        "LV": "absence_type = 'leave'",
        "DEP": "absence_type = 'deployment'",
        "TDY": "absence_type = 'tdy'",
        "USAFP": "absence_type = 'usafp'",
        "SLV": "absence_type = 'sabbatical_leave'",
        "FLX": "activity.code = 'flex'",
        # Specialty rotations
        "GYN": "rotation contains 'GYN'",
        "NEURO": "rotation contains 'NEURO'",
        "ENT": "rotation contains 'ENT'",
        "Ophtho": "rotation contains 'Ophtho'",
        "URO": "rotation contains 'URO'",
        # Procedures
        "PR": "activity.display_abbreviation = 'PR'",
        "US": "activity.display_abbreviation = 'US'",
        "VAS": "activity.display_abbreviation = 'VAS'",
        # Other
        "PI": "activity.display_abbreviation = 'PI'",
        "HC": "activity.display_abbreviation = 'HC'",
        "HV": "activity.display_abbreviation = 'HV'",
        "ADM": "activity.display_abbreviation = 'ADM'",
        "PC": "activity.display_abbreviation = 'PC'",
    }

    for code, rule in deterministic_1to1.items():
        cat = next(
            (k for k, codes in DISPLAY_CODES.items() if code in codes), "unknown"
        )
        classifications[code] = {
            "category": cat,
            "classification": "deterministic",
            "rule": rule,
            "notes": "1:1 map from canonical fact",
        }

    # ── CONTEXTUAL: requires rules but deterministic given context ──
    contextual_rules = {
        "W": {
            "rule": "is_weekend=True AND (person_type='resident' OR activity in FACULTY_COLLAPSE)",
            "notes": "Weekend day. Faculty admin codes collapse to W on weekends. "
            "Exception: FMIT/IMW/KAP override on weekends.",
        },
        "NF": {
            "rule": "rotation contains NF AND NOT (L&D, Peds, Endo specific)",
            "notes": "Generic night float. Falls through from _nf_display() when "
            "rotation doesn't match specific NF subtypes.",
        },
        "PedsNF": {
            "rule": "rotation contains PEDSNF|PEDNF|PNF|PEDSW",
            "notes": "Pediatrics night float. Multiple abbreviations normalize to PedsNF.",
        },
        "L&D": {
            "rule": "rotation contains LDNF",
            "notes": "Labor & Delivery night float.",
        },
        "Endo": {
            "rule": "rotation contains ENDO (but not NF/ENDO which → NF)",
            "notes": "Endoscopy. Tricky: NF/ENDO → NF, but standalone Endo → Endo.",
        },
        "SM": {
            "rule": "activity='C' AND rotation contains 'SM'",
            "notes": "Sports Medicine clinic. Clinic code C is remapped when on SM rotation.",
        },
        "aSM": {
            "rule": "SM rotation + specific context (attending SM?)",
            "notes": "Attending Sports Medicine. Unclear rule — may need coordinator input.",
        },
    }

    for code, info in contextual_rules.items():
        cat = next(
            (k for k, codes in DISPLAY_CODES.items() if code in codes), "unknown"
        )
        classifications[code] = {
            "category": cat,
            "classification": "contextual",
            **info,
        }

    # ── AMBIGUOUS: requires ML or coordinator judgment ──
    ambiguous_codes = {
        "C": {
            "rule": "activity='C' AND rotation NOT in (SM, GYN) AND day is weekday",
            "notes": "Generic clinic. But coordinator sometimes writes C40, C30, CC, "
            "CCC, C-I, C-N based on sub-clinic assignment not captured in solver.",
        },
        "CC": {
            "rule": "Continuity Clinic — determined by schedule template, not rotation",
            "notes": "Coordinator assigns based on patient panel continuity. "
            "Not derivable from rotation/activity alone.",
        },
        "C40": {
            "rule": "Intern clinic — PGY-1 specific clinic session",
            "notes": "Could be derived from pgy_level=1, but coordinator sometimes "
            "assigns C40 to upper-level residents.",
        },
        "C30": {
            "rule": "Clinic variant — unclear differentiation from C",
            "notes": "Needs coordinator interview to determine rule.",
        },
        "CCC": {
            "rule": "CCC variant — unclear",
            "notes": "Needs coordinator interview.",
        },
        "C-I": {
            "rule": "Clinic Initial — new patient clinic?",
            "notes": "Needs coordinator interview.",
        },
        "C-N": {
            "rule": "Clinic New — new patient clinic?",
            "notes": "Needs coordinator interview.",
        },
    }

    for code, info in ambiguous_codes.items():
        cat = next(
            (k for k, codes in DISPLAY_CODES.items() if code in codes), "unknown"
        )
        classifications[code] = {
            "category": cat,
            "classification": "ambiguous",
            **info,
        }

    return classifications


def analyze_features(features_path: str, classifications: dict) -> dict:
    """Analyze feature data to validate classifications and compute coverage.

    For each display code in the training data, count occurrences and check
    if the classification matches the observed patterns.
    """
    data = json.loads(Path(features_path).read_text())

    # Count display code occurrences
    code_counts = Counter()
    code_by_context = defaultdict(lambda: defaultdict(Counter))

    for cell in data:
        truth = cell.get("truth_code") or cell.get("cell_text")
        if not truth:
            continue
        code_counts[truth] += 1

        # Track context for each code
        rot = cell.get("rotation1") or cell.get("rotation") or "?"
        person_type = cell.get("person_type", "resident")
        is_weekend = cell.get("is_weekend", False)
        half = cell.get("half", "am")

        context_key = f"{rot}|{person_type}|{'wkend' if is_weekend else 'wkday'}|{half}"
        code_by_context[truth][context_key][truth] += 1

    # Build coverage stats
    total_cells = sum(code_counts.values())
    stats = {
        "total_cells": total_cells,
        "unique_codes": len(code_counts),
        "classified_codes": len(classifications),
        "unclassified_codes": [],
    }

    det_count = 0
    ctx_count = 0
    amb_count = 0
    noise_count = 0

    for code, count in code_counts.most_common():
        cls = classifications.get(code, {}).get("classification", "unclassified")
        if cls == "deterministic":
            det_count += count
        elif cls == "contextual":
            ctx_count += count
        elif cls == "ambiguous":
            amb_count += count
        elif cls == "noise":
            noise_count += count
        else:
            stats["unclassified_codes"].append({"code": code, "count": count})

    stats["deterministic"] = {
        "cells": det_count,
        "pct": round(100 * det_count / total_cells, 1) if total_cells else 0,
    }
    stats["contextual"] = {
        "cells": ctx_count,
        "pct": round(100 * ctx_count / total_cells, 1) if total_cells else 0,
    }
    stats["ambiguous"] = {
        "cells": amb_count,
        "pct": round(100 * amb_count / total_cells, 1) if total_cells else 0,
    }
    stats["noise"] = {
        "cells": noise_count,
        "pct": round(100 * noise_count / total_cells, 1) if total_cells else 0,
    }

    # Per-code breakdown
    stats["per_code"] = []
    for code, count in code_counts.most_common():
        cls_info = classifications.get(code, {})
        stats["per_code"].append({
            "code": code,
            "count": count,
            "pct": round(100 * count / total_cells, 1),
            "classification": cls_info.get("classification", "unclassified"),
            "category": cls_info.get("category", "unknown"),
            "unique_contexts": len(code_by_context.get(code, {})),
        })

    return stats


def build_mapping_table(classifications: dict) -> list[dict]:
    """Build the deterministic mapping table for the renderer.

    Each entry maps (activity_code, rotation_type, person_type, is_weekend, half, pgy)
    → display_code.

    Only includes deterministic and contextual codes — ambiguous codes are
    excluded (flagged for ML/coordinator review).
    """
    mappings = []

    for code, info in classifications.items():
        if info["classification"] == "ambiguous":
            continue

        mappings.append({
            "display_code": code,
            "classification": info["classification"],
            "category": info["category"],
            "rule": info["rule"],
        })

    return mappings


def print_report(classifications: dict, stats: dict | None = None):
    """Print a formatted audit report."""
    print(f"\n{'=' * 70}")
    print(f"  DISPLAY CODE AUDIT — CANONICAL FACTS COVERAGE")
    print(f"{'=' * 70}")

    # Classification summary
    det = [c for c, i in classifications.items() if i["classification"] == "deterministic"]
    ctx = [c for c, i in classifications.items() if i["classification"] == "contextual"]
    amb = [c for c, i in classifications.items() if i["classification"] == "ambiguous"]
    noi = [c for c, i in classifications.items() if i["classification"] == "noise"]

    print(f"\n  Total display codes classified: {len(classifications)}")
    print(f"  Deterministic (1:1 map):  {len(det)} codes")
    print(f"  Contextual (rule-based):  {len(ctx)} codes")
    print(f"  Ambiguous (needs ML):     {len(amb)} codes")
    print(f"  Noise (errors/labels):    {len(noi)} codes")

    print(f"\n{'─' * 70}")
    print(f"  DETERMINISTIC CODES ({len(det)})")
    print(f"{'─' * 70}")
    for code in sorted(det):
        info = classifications[code]
        print(f"    {code:8s} [{info['category']:15s}] {info['rule']}")

    print(f"\n{'─' * 70}")
    print(f"  CONTEXTUAL CODES ({len(ctx)})")
    print(f"{'─' * 70}")
    for code in sorted(ctx):
        info = classifications[code]
        print(f"    {code:8s} [{info['category']:15s}] {info['rule']}")

    print(f"\n{'─' * 70}")
    print(f"  AMBIGUOUS CODES ({len(amb)})")
    print(f"{'─' * 70}")
    for code in sorted(amb):
        info = classifications[code]
        print(f"    {code:8s} [{info['category']:15s}] {info['notes']}")

    if stats:
        print(f"\n{'=' * 70}")
        print(f"  COVERAGE ON TRAINING DATA ({stats['total_cells']} cells)")
        print(f"{'=' * 70}")
        d = stats["deterministic"]
        c = stats["contextual"]
        a = stats["ambiguous"]
        n = stats.get("noise", {"cells": 0, "pct": 0})
        print(f"  Deterministic: {d['cells']:>7,} cells ({d['pct']}%)")
        print(f"  Contextual:    {c['cells']:>7,} cells ({c['pct']}%)")
        print(f"  Ambiguous:     {a['cells']:>7,} cells ({a['pct']}%)")
        print(f"  Noise/Error:   {n['cells']:>7,} cells ({n['pct']}%)")

        if stats["unclassified_codes"]:
            total_uncl = sum(u["count"] for u in stats["unclassified_codes"])
            uncl_pct = round(100 * total_uncl / stats["total_cells"], 1)
            print(f"  Unclassified:  {total_uncl:>7,} cells ({uncl_pct}%)")
            print(f"\n  Unclassified codes ({len(stats['unclassified_codes'])}):")
            for u in stats["unclassified_codes"]:
                print(f"    {u['code']:8s} — {u['count']} occurrences")

        print(f"\n{'─' * 70}")
        print(f"  TOP 30 CODES BY FREQUENCY")
        print(f"{'─' * 70}")
        print(f"    {'Code':8s} {'Count':>7s} {'Pct':>6s} {'Class':14s} {'Category'}")
        print(f"    {'────':8s} {'─────':>7s} {'───':>6s} {'─────':14s} {'────────'}")
        for entry in stats["per_code"][:30]:
            print(
                f"    {entry['code']:8s} {entry['count']:>7,} {entry['pct']:>5.1f}% "
                f"{entry['classification']:14s} {entry['category']}"
            )

        # Summary
        resolvable = d["pct"] + c["pct"]
        print(f"\n  ═══════════════════════════════════════════")
        print(f"  DETERMINISTIC + CONTEXTUAL = {resolvable:.1f}% resolvable")
        print(f"  AMBIGUOUS (needs ML/human) = {a['pct']:.1f}%")
        print(f"  NOISE (errors/labels):       {n['pct']:.1f}%")
        if stats["unclassified_codes"]:
            total_uncl = sum(u["count"] for u in stats["unclassified_codes"])
            uncl_pct = round(100 * total_uncl / stats["total_cells"], 1)
            print(f"  UNCLASSIFIED:                {uncl_pct:.1f}%")
        print(f"  ═══════════════════════════════════════════")
        print(f"\n  → The renderer can resolve ~{resolvable:.0f}% of codes deterministically.")
        print(f"  → ML is only needed for ~{a['pct']:.0f}% of cells.")
        print(f"  → {n['pct']:.1f}% is noise (errors, day labels, deprecated codes).")


def load_merged_classifications(path: str = "data/merged_classifications.json") -> dict:
    """Load user-curated classifications from merged JSON file.

    Falls back to hardcoded classify_codes() if file not found.
    """
    merged_path = Path(path)
    if not merged_path.exists():
        print(f"  No merged classifications at {merged_path}, using hardcoded only")
        return classify_codes()

    merged = json.loads(merged_path.read_text())
    # Start with hardcoded as base, overlay merged (user corrections win)
    base = classify_codes()
    base.update(merged)
    return base


def main():
    parser = argparse.ArgumentParser(
        description="Audit display codes and build deterministic mapping"
    )
    parser.add_argument(
        "--features",
        default="data/features_universal.json",
        help="Feature JSON from extract_universal.py",
    )
    parser.add_argument(
        "--output",
        default="data/code_mapping.json",
        help="Output mapping JSON",
    )
    parser.add_argument(
        "--audit-output",
        default="data/code_audit.json",
        help="Output audit JSON with full stats",
    )
    parser.add_argument(
        "--merged",
        default="data/merged_classifications.json",
        help="Merged user-curated classifications JSON",
    )
    args = parser.parse_args()

    # Step 1: Load classifications (merged file + hardcoded base)
    classifications = load_merged_classifications(args.merged)

    # Step 2: Analyze against training data (if available)
    stats = None
    features_path = Path(args.features)
    if features_path.exists():
        print(f"  Analyzing {features_path}...")
        stats = analyze_features(str(features_path), classifications)
    else:
        print(f"  Features file not found: {features_path}")
        print(f"  Running classification-only audit (no coverage stats)")

    # Step 3: Print report
    print_report(classifications, stats)

    # Step 4: Build and save mapping table
    mapping = build_mapping_table(classifications)
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(mapping, indent=2))
    print(f"\n  Mapping saved to {out} ({len(mapping)} entries)")

    # Step 5: Save full audit
    audit = {
        "classifications": classifications,
        "stats": stats,
        "mapping": mapping,
    }
    audit_out = Path(args.audit_output)
    audit_out.write_text(json.dumps(audit, indent=2, default=str))
    print(f"  Full audit saved to {audit_out}")


if __name__ == "__main__":
    main()
