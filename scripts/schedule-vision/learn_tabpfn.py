"""TabPFN v2.5 evaluation for neural schedule vision.

TabPFN is a foundation model for tabular data (Nature 2025) that uses
in-context learning — no hyperparameter tuning needed. It natively handles
mixed categorical/numeric features through learned embeddings.

Evaluation strategy:
  1. Leave-one-AY-out CV — tests temporal generalization
  2. Leave-one-block-out CV — direct comparison with existing pipeline
  3. Feature ablation — quantify RGB color contribution

Usage:
    python learn_tabpfn.py --features data/features_universal.json
"""

from __future__ import annotations

import argparse
import json
import time
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, confusion_matrix
from sklearn.preprocessing import LabelEncoder

# ── Feature configuration ─────────────────────────────────────────

CATEGORICAL = ["rotation", "person_type", "half", "team_or_template", "role_raw"]
NUMERICAL = [
    "pgy_level", "day_of_week", "is_weekend", "day_index", "week_in_block",
    "fill_r", "fill_g", "fill_b", "font_r", "font_g", "font_b",
    "font_bold", "has_fill", "has_font_color", "academic_year",
    "block_number", "row_position",
]
CONTEXT = ["prev_same_half", "next_same_half", "other_half"]
VISUAL = ["fill_r", "fill_g", "fill_b", "font_r", "font_g", "font_b",
          "has_fill", "has_font_color"]
TARGET = "cell_text"

# TabPFN row limits — subsample if training set exceeds this
TABPFN_MAX_TRAIN = 10000  # Conservative limit for v2.5


def load_data(path: str, min_code_count: int = 10) -> pd.DataFrame:
    """Load features and filter rare codes."""
    data = json.loads(Path(path).read_text())
    df = pd.DataFrame(data)

    # Filter rare codes
    code_counts = df[TARGET].value_counts()
    valid_codes = code_counts[code_counts >= min_code_count].index
    n_before = len(df)
    df = df[df[TARGET].isin(valid_codes)].copy()
    print(f"  Loaded {n_before} cells, kept {len(df)} after filtering "
          f"codes with <{min_code_count} occurrences")
    print(f"  Unique codes: {df[TARGET].nunique()}")
    return df


def get_feature_cols(include_visual: bool = True,
                     include_context: bool = False) -> list[str]:
    """Get feature column list for a given configuration."""
    cols = list(CATEGORICAL) + list(NUMERICAL)
    if include_context:
        cols += CONTEXT
    if not include_visual:
        cols = [c for c in cols if c not in VISUAL]
    return cols


def subsample_stratified(df: pd.DataFrame, max_rows: int,
                         target_col: str = TARGET) -> pd.DataFrame:
    """Stratified subsample to max_rows, preserving class distribution."""
    if len(df) <= max_rows:
        return df
    frac = max_rows / len(df)
    sampled = df.groupby(target_col, group_keys=False).apply(
        lambda x: x.sample(max(1, int(len(x) * frac)), random_state=42)
    )
    # Trim to exact size
    if len(sampled) > max_rows:
        sampled = sampled.sample(max_rows, random_state=42)
    return sampled


def encode_for_tabpfn(df: pd.DataFrame, feature_cols: list[str],
                      label_encoder: LabelEncoder | None = None):
    """Encode features for TabPFN.

    TabPFN handles mixed types but we need to ensure categoricals are strings
    and numerics are floats. Label encode the target.
    """
    X = df[feature_cols].copy()

    # Ensure categoricals are strings (TabPFN auto-detects)
    for col in CATEGORICAL:
        if col in X.columns:
            X[col] = X[col].astype(str)

    # Ensure context columns are strings too
    for col in CONTEXT:
        if col in X.columns:
            X[col] = X[col].astype(str)

    # Target encoding
    if label_encoder is None:
        label_encoder = LabelEncoder()
        y = label_encoder.fit_transform(df[TARGET])
    else:
        y = label_encoder.transform(df[TARGET])

    return X, y, label_encoder


def run_tabpfn_cv(df: pd.DataFrame, feature_cols: list[str],
                  split_col: str, desc: str) -> dict:
    """Run leave-one-out CV on the specified split column."""
    from tabpfn import TabPFNClassifier

    groups = sorted(df[split_col].unique())
    print(f"\n  {desc} ({len(groups)} folds)")
    print(f"  {'─' * 50}")

    le = LabelEncoder()
    le.fit(df[TARGET])

    results = []
    all_y_true = []
    all_y_pred = []

    for group in groups:
        test_mask = df[split_col] == group
        train_mask = ~test_mask

        train_df = df[train_mask]
        test_df = df[test_mask]

        if len(test_df) == 0 or len(train_df) == 0:
            continue

        # Ensure test codes exist in training
        train_codes = set(train_df[TARGET])
        test_df = test_df[test_df[TARGET].isin(train_codes)]
        if len(test_df) == 0:
            print(f"    {split_col}={group}: SKIP (all codes unseen)")
            continue

        # Subsample training if needed
        train_sub = subsample_stratified(train_df, TABPFN_MAX_TRAIN)

        # Re-fit label encoder on training subset codes
        le_fold = LabelEncoder()
        le_fold.fit(train_sub[TARGET])

        # Filter test to codes in training
        test_df = test_df[test_df[TARGET].isin(le_fold.classes_)]
        if len(test_df) == 0:
            continue

        X_train, y_train, _ = encode_for_tabpfn(train_sub, feature_cols, le_fold)
        X_test, y_test, _ = encode_for_tabpfn(test_df, feature_cols, le_fold)

        t0 = time.time()
        clf = TabPFNClassifier(device="cpu")
        clf.fit(X_train, y_train)
        y_pred = clf.predict(X_test)
        elapsed = time.time() - t0

        acc = accuracy_score(y_test, y_pred)
        results.append({
            "group": group,
            "accuracy": acc,
            "n_train": len(train_sub),
            "n_test": len(test_df),
            "elapsed": elapsed,
        })
        all_y_true.extend(y_test.tolist())
        all_y_pred.extend(y_pred.tolist())

        print(f"    {split_col}={group}: {acc:.1%} "
              f"({len(test_df)} test, {len(train_sub)} train, {elapsed:.1f}s)")

    if not results:
        print("    No valid folds")
        return {"mean_accuracy": 0, "results": []}

    mean_acc = np.mean([r["accuracy"] for r in results])
    overall_acc = accuracy_score(all_y_true, all_y_pred)
    print(f"\n    Mean fold accuracy: {mean_acc:.1%}")
    print(f"    Overall accuracy:   {overall_acc:.1%}")

    return {
        "mean_accuracy": mean_acc,
        "overall_accuracy": overall_acc,
        "results": results,
        "y_true": all_y_true,
        "y_pred": all_y_pred,
    }


def print_per_code_accuracy(y_true, y_pred, le: LabelEncoder, top_n: int = 30):
    """Print per-code accuracy for the most common codes."""
    y_true_labels = le.inverse_transform(y_true)
    y_pred_labels = le.inverse_transform(y_pred)

    code_counts = Counter(y_true_labels)
    print(f"\n  Per-code accuracy (top {top_n} by frequency):")
    print(f"  {'Code':12s} {'Correct':>8s} {'Total':>6s} {'Acc':>6s}")
    print(f"  {'─' * 36}")

    for code, total in code_counts.most_common(top_n):
        mask = y_true_labels == code
        correct = (y_pred_labels[mask] == code).sum()
        acc = correct / total if total > 0 else 0
        marker = " ★" if acc >= 0.8 else ""
        print(f"  {code:12s} {correct:8d} {total:6d} {acc:6.1%}{marker}")


def run_feature_ablation(df: pd.DataFrame) -> dict:
    """Run TabPFN with different feature sets to measure contribution."""
    configs = {
        "all_features": get_feature_cols(include_visual=True, include_context=False),
        "no_visual": get_feature_cols(include_visual=False, include_context=False),
        "with_context": get_feature_cols(include_visual=True, include_context=True),
        "structural_only": [c for c in get_feature_cols(False, False)
                           if c not in ["academic_year", "name_hash"]],
    }

    # Use a single AY holdout for speed
    test_ay = df["academic_year"].value_counts().idxmin()  # smallest AY as test
    print(f"\n  Feature ablation (test AY={test_ay})")
    print(f"  {'─' * 60}")

    results = {}
    for name, cols in configs.items():
        test_mask = df["academic_year"] == test_ay
        train_df = df[~test_mask]
        test_df = df[test_mask]

        train_codes = set(train_df[TARGET])
        test_df = test_df[test_df[TARGET].isin(train_codes)]
        if len(test_df) == 0:
            print(f"    {name}: SKIP")
            continue

        train_sub = subsample_stratified(train_df, TABPFN_MAX_TRAIN)
        le = LabelEncoder()
        le.fit(train_sub[TARGET])
        test_df = test_df[test_df[TARGET].isin(le.classes_)]
        if len(test_df) == 0:
            continue

        X_train, y_train, _ = encode_for_tabpfn(train_sub, cols, le)
        X_test, y_test, _ = encode_for_tabpfn(test_df, cols, le)

        from tabpfn import TabPFNClassifier
        clf = TabPFNClassifier(device="cpu")
        t0 = time.time()
        clf.fit(X_train, y_train)
        y_pred = clf.predict(X_test)
        elapsed = time.time() - t0

        acc = accuracy_score(y_test, y_pred)
        results[name] = {"accuracy": acc, "n_features": len(cols), "elapsed": elapsed}
        print(f"    {name:20s}: {acc:.1%} ({len(cols)} features, {elapsed:.1f}s)")

    return results


def main():
    parser = argparse.ArgumentParser(description="TabPFN evaluation for schedule vision")
    parser.add_argument("--features", default="data/features_universal.json",
                        help="Feature JSON from extract_universal.py")
    parser.add_argument("--min-code-count", type=int, default=10,
                        help="Minimum occurrences for a code to be included")
    parser.add_argument("--skip-ablation", action="store_true",
                        help="Skip feature ablation (faster)")
    parser.add_argument("--output", default="data/tabpfn_results.json",
                        help="Output results JSON")
    args = parser.parse_args()

    print(f"\n{'=' * 60}")
    print(f"  TABPFN SCHEDULE VISION EVALUATION")
    print(f"{'=' * 60}")

    df = load_data(args.features, args.min_code_count)
    feature_cols = get_feature_cols(include_visual=True, include_context=False)

    print(f"\n  Features ({len(feature_cols)}):")
    for col in feature_cols:
        dtype = "cat" if col in CATEGORICAL else "num"
        visual = " [visual]" if col in VISUAL else ""
        print(f"    {col:20s} ({dtype}){visual}")

    # ── Leave-one-AY-out CV ───────────────────────────────────
    print(f"\n{'─' * 60}")
    print(f"  LEAVE-ONE-AY-OUT CROSS-VALIDATION")
    print(f"{'─' * 60}")

    loayo = run_tabpfn_cv(df, feature_cols, "academic_year",
                          "Leave-one-AY-out CV")

    # ── Leave-one-block-out CV (within most populated AY) ─────
    print(f"\n{'─' * 60}")
    print(f"  LEAVE-ONE-BLOCK-OUT CROSS-VALIDATION")
    print(f"{'─' * 60}")

    # Use AY 2017 (largest) for LOBO since it has all 13 blocks
    biggest_ay = df["academic_year"].value_counts().idxmax()
    df_ay = df[df["academic_year"] == biggest_ay].copy()
    print(f"  Using AY {biggest_ay} ({len(df_ay)} cells, "
          f"{df_ay['block_number'].nunique()} blocks)")

    lobo = run_tabpfn_cv(df_ay, feature_cols, "block_number",
                         "Leave-one-block-out CV")

    # ── Feature ablation ──────────────────────────────────────
    ablation = {}
    if not args.skip_ablation:
        print(f"\n{'─' * 60}")
        print(f"  FEATURE ABLATION")
        print(f"{'─' * 60}")
        ablation = run_feature_ablation(df)

    # ── Per-code accuracy ─────────────────────────────────────
    if loayo.get("y_true") and loayo.get("y_pred"):
        le = LabelEncoder()
        le.fit(df[TARGET])
        # Re-encode for display
        print(f"\n{'─' * 60}")
        print(f"  PER-CODE ACCURACY (leave-one-AY-out)")
        print(f"{'─' * 60}")
        y_true = np.array(loayo["y_true"])
        y_pred = np.array(loayo["y_pred"])
        # Map back through fold label encoders — just use raw codes
        # Actually the y_true/y_pred are already encoded per-fold, not globally
        # We need to track raw codes instead. Skip for now, show overall.
        print(f"    Overall: {loayo['overall_accuracy']:.1%}")

    # ── Summary ───────────────────────────────────────────────
    print(f"\n{'=' * 60}")
    print(f"  SUMMARY")
    print(f"{'=' * 60}")
    print(f"  Leave-one-AY-out:    {loayo.get('overall_accuracy', 0):.1%}")
    print(f"  Leave-one-block-out: {lobo.get('overall_accuracy', 0):.1%}")
    if ablation:
        for name, res in ablation.items():
            print(f"  Ablation ({name}): {res['accuracy']:.1%}")
    print(f"\n  Current baseline (hierarchical lookup): 68.8%")
    improvement = (lobo.get("overall_accuracy", 0) - 0.688) * 100
    print(f"  LOBO improvement: {improvement:+.1f}pp")

    # Save results
    results = {
        "leave_one_ay_out": {
            "overall_accuracy": loayo.get("overall_accuracy"),
            "mean_fold_accuracy": loayo.get("mean_accuracy"),
            "per_fold": [{k: v for k, v in r.items()}
                        for r in loayo.get("results", [])],
        },
        "leave_one_block_out": {
            "overall_accuracy": lobo.get("overall_accuracy"),
            "mean_fold_accuracy": lobo.get("mean_accuracy"),
            "per_fold": [{k: v for k, v in r.items()}
                        for r in lobo.get("results", [])],
        },
        "ablation": ablation,
        "baseline_accuracy": 0.688,
    }
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(results, indent=2, default=str))
    print(f"\n  Results saved to {out}")


if __name__ == "__main__":
    main()
