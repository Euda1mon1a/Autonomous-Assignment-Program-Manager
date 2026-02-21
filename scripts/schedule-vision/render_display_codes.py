"""Deterministic display-code renderer.

Takes canonical schedule facts (activity_code, rotation, person_type, is_weekend, half)
and renders the display code using:
  1. Merged classifications (from coordinator-curated code_mapping)
  2. Contextual rules (NF expansion, weekend collapse, clinic mapping)
  3. Flags ambiguous codes for ML/coordinator review

This replaces the hierarchical lookup with explicit rules + classifications.
Can be validated against the 116K training cells.

Usage:
    python render_display_codes.py --features data/features_universal.json
    python render_display_codes.py --features data/features_universal.json --output data/render_results.json
"""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path


# ── Contextual rules (from fill_template.py) ─────────────────────

CODE_NORM = {"IM": "IMW", "LDNF": "L&D", "PedNF": "PedsNF"}

# Checked sequentially — first match wins
NF_PATTERNS = [
    ("LDNF", "L&D"),
    ("PEDSNF", "PedsNF"),
    ("PEDNF", "PedsNF"),
    ("PNF", "PedsNF"),
    ("PEDSW", "PedsNF"),
    ("NF/ENDO", "NF"),
    ("NEURO", "NF"),
    ("NF", "NF"),
]

WEEKEND_OVERRIDES = {"FMIT": "FMIT", "IMW": "IMW", "KAP": "KAP"}

FACULTY_COLLAPSE = {"GME", "CV", "DFM", "SM", "LEC", "ADV", "AT", "DO"}

CLINIC_MAP = {"GYN": "GYN", "SM": "SM"}

# Codes that are "Endo" rotation (not NF)
ENDO_PATTERN = "ENDO"


def _nf_display(rotation: str, rotation2: str = "") -> str | None:
    """Determine NF-specific display code from rotation string."""
    combined = f"{rotation} {rotation2}".upper()
    for pattern, display in NF_PATTERNS:
        if pattern.upper() in combined:
            return display
    return None


def _endo_check(rotation: str, rotation2: str = "") -> bool:
    """Check if rotation is Endo (but not NF/ENDO)."""
    combined = f"{rotation} {rotation2}".upper()
    if "NF/ENDO" in combined or "NF" in combined:
        return False
    return ENDO_PATTERN in combined


def render_code(
    db_code: str,
    rotation: str,
    rotation2: str = "",
    is_weekend: bool = False,
    is_faculty: bool = False,
    person_type: str = "resident",
    pgy_level: int = 0,
    half: str = "am",
    classifications: dict | None = None,
) -> tuple[str, str]:
    """Render a display code from canonical schedule facts.

    Returns (display_code, resolution_type) where resolution_type is one of:
      - "deterministic": 1:1 map from classification table
      - "contextual_rule": resolved by contextual rule
      - "ambiguous": needs ML or coordinator
      - "noise": error/label/deprecated
      - "unclassified": not in any classification
      - "passthrough": code returned as-is (no rule changed it)
    """
    if not db_code or not db_code.strip():
        return ("", "empty")

    code = db_code.strip()

    # Step 1: CODE_NORM — normalize known abbreviation variants
    if code in CODE_NORM:
        code = CODE_NORM[code]

    # Step 2: Check classification table first
    if classifications:
        cls_info = classifications.get(code)
        if cls_info:
            cls_type = cls_info.get("classification", "unclassified")
            if cls_type == "noise":
                return (code, "noise")
            if cls_type == "deterministic":
                # Deterministic codes pass through as-is UNLESS
                # contextual rules should override (NF, W, C)
                if code not in ("NF", "W", "C", "OFF"):
                    return (code, "deterministic")
            # contextual and ambiguous fall through to rules

    # Step 3: NF expansion
    if code == "NF":
        nf_display = _nf_display(rotation, rotation2)
        if nf_display:
            return (nf_display, "contextual_rule")
        return ("NF", "contextual_rule")

    # Step 4: OFF on NF rotation → NF-specific code
    if code == "OFF":
        nf_display = _nf_display(rotation, rotation2)
        if nf_display:
            return (nf_display, "contextual_rule")
        # Otherwise OFF stays OFF
        return ("OFF", "deterministic")

    # Step 5: Weekend W expansion
    if is_weekend and code == "W":
        # Try NF expansion first
        nf_display = _nf_display(rotation, rotation2)
        if nf_display:
            return (nf_display, "contextual_rule")
        # Try weekend overrides (inpatient rotations keep their code)
        rot_upper = rotation.upper() if rotation else ""
        for pattern, override_code in WEEKEND_OVERRIDES.items():
            if pattern.upper() in rot_upper:
                return (override_code, "contextual_rule")
        # W stays W
        return ("W", "contextual_rule")

    # Step 6: Faculty weekend collapse
    if is_faculty and is_weekend and code in FACULTY_COLLAPSE:
        return ("W", "contextual_rule")

    # Step 7: Clinic mapping
    if code == "C":
        rot_upper = rotation.upper() if rotation else ""
        for pattern, clinic_code in CLINIC_MAP.items():
            if pattern.upper() in rot_upper:
                return (clinic_code, "contextual_rule")
        # Check for Endo rotation
        if _endo_check(rotation, rotation2):
            return ("Endo", "contextual_rule")
        # Generic C — ambiguous (sub-clinic variant unknown)
        return ("C", "ambiguous")

    # Step 8: Check classification for remaining codes
    if classifications:
        cls_info = classifications.get(code)
        if cls_info:
            cls_type = cls_info.get("classification", "unclassified")
            return (code, cls_type)

    # Step 9: Passthrough — code not in any classification
    return (code, "unclassified")


def infer_db_code(cell_text: str, rotation: str, is_weekend: bool,
                   is_faculty: bool, classifications: dict) -> str:
    """Infer what db_code the solver would have output for this cell.

    Historical data only has the coordinator's display code (cell_text).
    We reverse-engineer the solver's likely output:
      - NF variants (L&D, PedsNF, Endo) → solver would output "NF" or "OFF"
      - Weekend W with inpatient override → solver would output "W"
      - Faculty W on weekend → solver probably output an admin code
      - Clinic variants (CC, C40, C30) → solver would output "C"
      - Everything else → db_code == cell_text (identity)
    """
    code = cell_text.strip()
    if not code:
        return ""

    # NF variants came from "NF" or "OFF" in the solver
    if code in ("L&D", "PedsNF", "Endo"):
        # Could be NF or OFF on an NF rotation
        return "NF"

    # Weekend codes: W on weekend for faculty could have been any admin code
    # But we can't know which one, so just return W
    if code == "W" and is_weekend:
        return "W"

    # Clinic sub-variants all came from "C" in the solver
    if code in ("CC", "C40", "C30", "CCC", "C-I", "C-N", "C10", "C8",
                "C60", "C4", "CP", "COLPO", "COB", "WOMH", "ADHD", "MUC",
                "CL", "GYN", "SM"):
        return "C"

    # Everything else: db_code == display code (identity mapping)
    return code


def validate_against_training(
    features_path: str,
    classifications: dict,
) -> dict:
    """Run renderer on all training cells and compute accuracy.

    Strategy: For each cell, infer what the solver would have output (db_code),
    run the renderer, and compare against the coordinator's actual code (cell_text).
    """
    data = json.loads(Path(features_path).read_text())

    total = 0
    correct = 0
    resolution_counts = Counter()
    correct_by_resolution = Counter()
    errors_by_code = defaultdict(list)
    confusion = defaultdict(Counter)

    for cell in data:
        truth = cell.get("cell_text", "").strip()
        if not truth:
            continue

        rotation = cell.get("rotation", "")
        rotation2 = cell.get("rotation2", "")
        is_weekend = cell.get("is_weekend", False)
        person_type = cell.get("person_type", "resident")
        is_faculty = person_type == "faculty"
        pgy_level = cell.get("pgy_level", 0)
        half = cell.get("half", "am")

        # Infer what the solver would have output
        db_code = infer_db_code(truth, rotation, is_weekend, is_faculty, classifications)

        rendered, resolution = render_code(
            db_code=db_code,
            rotation=rotation,
            rotation2=rotation2,
            is_weekend=is_weekend,
            is_faculty=is_faculty,
            person_type=person_type,
            pgy_level=pgy_level,
            half=half,
            classifications=classifications,
        )

        total += 1
        resolution_counts[resolution] += 1

        if rendered == truth:
            correct += 1
            correct_by_resolution[resolution] += 1
        else:
            if len(errors_by_code[truth]) < 5:
                errors_by_code[truth].append({
                    "truth": truth,
                    "rendered": rendered,
                    "resolution": resolution,
                    "db_code": db_code,
                    "rotation": rotation,
                    "person_type": person_type,
                    "is_weekend": is_weekend,
                    "half": half,
                })
            confusion[truth][rendered] += 1

    accuracy = correct / total if total else 0

    # Build per-resolution accuracy
    resolution_accuracy = {}
    for res, count in resolution_counts.most_common():
        res_correct = correct_by_resolution[res]
        resolution_accuracy[res] = {
            "total": count,
            "correct": res_correct,
            "accuracy": round(100 * res_correct / count, 1) if count else 0,
            "pct_of_total": round(100 * count / total, 1) if total else 0,
        }

    # Top confusion pairs
    top_confusion = []
    for truth_code, rendered_counts in sorted(
        confusion.items(), key=lambda x: sum(x[1].values()), reverse=True
    )[:30]:
        for rendered, count in rendered_counts.most_common(3):
            top_confusion.append({
                "truth": truth_code,
                "rendered": rendered,
                "count": count,
            })

    return {
        "total_cells": total,
        "correct": correct,
        "accuracy": round(100 * accuracy, 2),
        "by_resolution": resolution_accuracy,
        "top_confusion": sorted(top_confusion, key=lambda x: -x["count"])[:30],
        "error_examples": {k: v for k, v in list(errors_by_code.items())[:20]},
    }


def print_validation_report(results: dict):
    """Print a formatted validation report."""
    print(f"\n{'=' * 70}")
    print(f"  DETERMINISTIC RENDERER — VALIDATION REPORT")
    print(f"{'=' * 70}")
    print(f"\n  Total cells:    {results['total_cells']:>7,}")
    print(f"  Correct:        {results['correct']:>7,}")
    print(f"  ACCURACY:       {results['accuracy']:>6.2f}%")
    print(f"  Baseline:        68.80% (hierarchical lookup)")
    improvement = results["accuracy"] - 68.8
    print(f"  Improvement:    {improvement:>+6.2f}pp")

    print(f"\n{'─' * 70}")
    print(f"  ACCURACY BY RESOLUTION TYPE")
    print(f"{'─' * 70}")
    print(f"    {'Resolution':20s} {'Total':>7s} {'Correct':>8s} {'Acc':>7s} {'% Total':>8s}")
    print(f"    {'──────────':20s} {'─────':>7s} {'───────':>8s} {'───':>7s} {'───────':>8s}")
    for res, stats in sorted(
        results["by_resolution"].items(),
        key=lambda x: -x[1]["total"],
    ):
        print(
            f"    {res:20s} {stats['total']:>7,} {stats['correct']:>8,} "
            f"{stats['accuracy']:>6.1f}% {stats['pct_of_total']:>7.1f}%"
        )

    print(f"\n{'─' * 70}")
    print(f"  TOP CONFUSION PAIRS (truth → rendered)")
    print(f"{'─' * 70}")
    print(f"    {'Truth':10s} {'Rendered':10s} {'Count':>7s}")
    print(f"    {'─────':10s} {'────────':10s} {'─────':>7s}")
    for pair in results["top_confusion"][:20]:
        print(f"    {pair['truth']:10s} {pair['rendered']:10s} {pair['count']:>7,}")

    print(f"\n{'=' * 70}")


def main():
    parser = argparse.ArgumentParser(
        description="Deterministic display-code renderer with validation"
    )
    parser.add_argument(
        "--features",
        default="data/features_universal.json",
        help="Feature JSON from extract_universal.py",
    )
    parser.add_argument(
        "--classifications",
        default="data/merged_classifications.json",
        help="Merged classifications JSON",
    )
    parser.add_argument(
        "--output",
        default="data/render_results.json",
        help="Output validation results JSON",
    )
    args = parser.parse_args()

    # Load classifications
    cls_path = Path(args.classifications)
    if cls_path.exists():
        classifications = json.loads(cls_path.read_text())
        print(f"  Loaded {len(classifications)} classifications from {cls_path}")
    else:
        print(f"  No classifications found at {cls_path}")
        classifications = {}

    # Validate against training data
    features_path = Path(args.features)
    if not features_path.exists():
        print(f"  Features file not found: {features_path}")
        return

    print(f"  Validating against {features_path}...")
    results = validate_against_training(str(features_path), classifications)

    # Print report
    print_validation_report(results)

    # Save results
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(results, indent=2, default=str))
    print(f"\n  Results saved to {out}")


if __name__ == "__main__":
    main()
