"""CatBoost evaluation for neural schedule vision.

CatBoost provides native categorical feature support (no encoding needed),
ordered boosting to prevent target leakage, and built-in feature importance.
Unlike TabPFN, CatBoost can handle the full 116K dataset and exports to Core ML.

Evaluation strategy matches learn_tabpfn.py for fair comparison:
  1. Leave-one-AY-out CV — tests temporal generalization
  2. Leave-one-block-out CV — direct comparison with existing pipeline
  3. Feature ablation — quantify RGB color contribution
  4. Feature importance analysis

Usage:
    python learn_catboost.py --features data/features_universal.json
"""

from __future__ import annotations

import argparse
import json
import time
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd
from catboost import CatBoostClassifier, Pool
from sklearn.metrics import accuracy_score
from sklearn.preprocessing import LabelEncoder

# ── Feature configuration (shared with learn_tabpfn.py) ──────────

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


def load_data(path: str, min_code_count: int = 10) -> pd.DataFrame:
    """Load features and filter rare codes."""
    data = json.loads(Path(path).read_text())
    df = pd.DataFrame(data)
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


def get_cat_indices(feature_cols: list[str]) -> list[int]:
    """Get indices of categorical features for CatBoost."""
    all_cat = set(CATEGORICAL) | set(CONTEXT)
    return [i for i, col in enumerate(feature_cols) if col in all_cat]


def prepare_catboost_data(df: pd.DataFrame, feature_cols: list[str],
                          label_encoder: LabelEncoder | None = None):
    """Prepare data for CatBoost. Returns X, y, label_encoder."""
    X = df[feature_cols].copy()

    # CatBoost needs categoricals as strings
    all_cat = set(CATEGORICAL) | set(CONTEXT)
    for col in feature_cols:
        if col in all_cat:
            X[col] = X[col].astype(str)
        else:
            X[col] = pd.to_numeric(X[col], errors="coerce").fillna(-1)

    if label_encoder is None:
        label_encoder = LabelEncoder()
        y = label_encoder.fit_transform(df[TARGET])
    else:
        y = label_encoder.transform(df[TARGET])

    return X, y, label_encoder


def make_catboost(n_classes: int, iterations: int = 1000) -> CatBoostClassifier:
    """Create a CatBoost classifier with good defaults for this task."""
    return CatBoostClassifier(
        iterations=iterations,
        depth=8,
        learning_rate=0.05,
        auto_class_weights="Balanced",
        random_seed=42,
        verbose=0,  # Suppress training output
        task_type="CPU",
        # Use fast one-hot for low-cardinality categoricals
        one_hot_max_size=10,
    )


def run_catboost_cv(df: pd.DataFrame, feature_cols: list[str],
                    split_col: str, desc: str,
                    iterations: int = 1000) -> dict:
    """Run leave-one-out CV on the specified split column."""
    groups = sorted(df[split_col].unique())
    cat_indices = get_cat_indices(feature_cols)
    print(f"\n  {desc} ({len(groups)} folds)")
    print(f"  {'─' * 50}")

    results = []
    all_y_true = []
    all_y_pred = []
    all_y_true_labels = []
    all_y_pred_labels = []

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

        le = LabelEncoder()
        le.fit(train_df[TARGET])
        test_df = test_df[test_df[TARGET].isin(le.classes_)]
        if len(test_df) == 0:
            continue

        X_train, y_train, _ = prepare_catboost_data(train_df, feature_cols, le)
        X_test, y_test, _ = prepare_catboost_data(test_df, feature_cols, le)

        clf = make_catboost(len(le.classes_), iterations)
        train_pool = Pool(X_train, y_train, cat_features=cat_indices)
        test_pool = Pool(X_test, cat_features=cat_indices)

        t0 = time.time()
        clf.fit(train_pool)
        y_pred = clf.predict(test_pool).flatten().astype(int)
        elapsed = time.time() - t0

        acc = accuracy_score(y_test, y_pred)
        results.append({
            "group": group,
            "accuracy": acc,
            "n_train": len(train_df),
            "n_test": len(test_df),
            "elapsed": elapsed,
        })
        all_y_true.extend(y_test.tolist())
        all_y_pred.extend(y_pred.tolist())
        all_y_true_labels.extend(le.inverse_transform(y_test).tolist())
        all_y_pred_labels.extend(le.inverse_transform(y_pred).tolist())

        print(f"    {split_col}={group}: {acc:.1%} "
              f"({len(test_df)} test, {len(train_df)} train, {elapsed:.1f}s)")

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
        "y_true_labels": all_y_true_labels,
        "y_pred_labels": all_y_pred_labels,
    }


def print_per_code_accuracy(y_true_labels: list[str], y_pred_labels: list[str],
                            top_n: int = 30):
    """Print per-code accuracy for the most common codes."""
    y_true = np.array(y_true_labels)
    y_pred = np.array(y_pred_labels)
    code_counts = Counter(y_true)

    print(f"\n  Per-code accuracy (top {top_n} by frequency):")
    print(f"  {'Code':12s} {'Correct':>8s} {'Total':>6s} {'Acc':>6s}")
    print(f"  {'─' * 36}")

    for code, total in code_counts.most_common(top_n):
        mask = y_true == code
        correct = (y_pred[mask] == code).sum()
        acc = correct / total if total > 0 else 0
        marker = " ★" if acc >= 0.8 else ""
        print(f"  {code:12s} {correct:8d} {total:6d} {acc:6.1%}{marker}")


def run_feature_importance(df: pd.DataFrame, feature_cols: list[str]):
    """Train on full data and report feature importance."""
    cat_indices = get_cat_indices(feature_cols)
    le = LabelEncoder()
    le.fit(df[TARGET])
    X, y, le = prepare_catboost_data(df, feature_cols, le)

    clf = make_catboost(len(le.classes_), iterations=500)
    pool = Pool(X, y, cat_features=cat_indices)
    clf.fit(pool)

    importances = clf.get_feature_importance()
    feat_imp = sorted(zip(feature_cols, importances), key=lambda x: -x[1])

    print(f"\n  Feature importance (CatBoost, full data):")
    print(f"  {'Feature':20s} {'Importance':>12s}")
    print(f"  {'─' * 36}")
    for name, imp in feat_imp[:15]:
        bar = "█" * int(imp / 2)
        visual = " [visual]" if name in VISUAL else ""
        print(f"  {name:20s} {imp:12.1f}  {bar}{visual}")

    return {name: float(imp) for name, imp in feat_imp}


def run_feature_ablation(df: pd.DataFrame, iterations: int = 500) -> dict:
    """Run CatBoost with different feature sets."""
    configs = {
        "all_features": get_feature_cols(include_visual=True, include_context=False),
        "no_visual": get_feature_cols(include_visual=False, include_context=False),
        "with_context": get_feature_cols(include_visual=True, include_context=True),
        "structural_only": [c for c in get_feature_cols(False, False)
                           if c not in ["academic_year"]],
    }

    # Use smallest AY as holdout
    test_ay = df["academic_year"].value_counts().idxmin()
    print(f"\n  Feature ablation (test AY={test_ay})")
    print(f"  {'─' * 60}")

    results = {}
    for name, cols in configs.items():
        cat_indices = get_cat_indices(cols)
        test_mask = df["academic_year"] == test_ay
        train_df = df[~test_mask]
        test_df = df[test_mask]

        train_codes = set(train_df[TARGET])
        test_df = test_df[test_df[TARGET].isin(train_codes)]
        if len(test_df) == 0:
            print(f"    {name}: SKIP")
            continue

        le = LabelEncoder()
        le.fit(train_df[TARGET])
        test_df = test_df[test_df[TARGET].isin(le.classes_)]
        if len(test_df) == 0:
            continue

        X_train, y_train, _ = prepare_catboost_data(train_df, cols, le)
        X_test, y_test, _ = prepare_catboost_data(test_df, cols, le)

        clf = make_catboost(len(le.classes_), iterations)
        train_pool = Pool(X_train, y_train, cat_features=cat_indices)
        test_pool = Pool(X_test, cat_features=cat_indices)

        t0 = time.time()
        clf.fit(train_pool)
        y_pred = clf.predict(test_pool).flatten().astype(int)
        elapsed = time.time() - t0

        acc = accuracy_score(y_test, y_pred)
        results[name] = {"accuracy": acc, "n_features": len(cols), "elapsed": elapsed}
        print(f"    {name:20s}: {acc:.1%} ({len(cols)} features, {elapsed:.1f}s)")

    return results


def main():
    parser = argparse.ArgumentParser(description="CatBoost evaluation for schedule vision")
    parser.add_argument("--features", default="data/features_universal.json",
                        help="Feature JSON from extract_universal.py")
    parser.add_argument("--min-code-count", type=int, default=10,
                        help="Minimum occurrences for a code to be included")
    parser.add_argument("--iterations", type=int, default=1000,
                        help="CatBoost training iterations")
    parser.add_argument("--skip-ablation", action="store_true",
                        help="Skip feature ablation (faster)")
    parser.add_argument("--output", default="data/catboost_results.json",
                        help="Output results JSON")
    args = parser.parse_args()

    print(f"\n{'=' * 60}")
    print(f"  CATBOOST SCHEDULE VISION EVALUATION")
    print(f"{'=' * 60}")

    df = load_data(args.features, args.min_code_count)
    feature_cols = get_feature_cols(include_visual=True, include_context=False)
    cat_indices = get_cat_indices(feature_cols)

    print(f"\n  Features ({len(feature_cols)}):")
    for i, col in enumerate(feature_cols):
        cat_mark = " [cat]" if i in cat_indices else ""
        visual = " [visual]" if col in VISUAL else ""
        print(f"    {col:20s}{cat_mark}{visual}")

    # ── Leave-one-AY-out CV ───────────────────────────────────
    print(f"\n{'─' * 60}")
    print(f"  LEAVE-ONE-AY-OUT CROSS-VALIDATION")
    print(f"{'─' * 60}")

    loayo = run_catboost_cv(df, feature_cols, "academic_year",
                            "Leave-one-AY-out CV", args.iterations)

    # ── Leave-one-block-out CV ────────────────────────────────
    print(f"\n{'─' * 60}")
    print(f"  LEAVE-ONE-BLOCK-OUT CROSS-VALIDATION")
    print(f"{'─' * 60}")

    biggest_ay = df["academic_year"].value_counts().idxmax()
    df_ay = df[df["academic_year"] == biggest_ay].copy()
    print(f"  Using AY {biggest_ay} ({len(df_ay)} cells, "
          f"{df_ay['block_number'].nunique()} blocks)")

    lobo = run_catboost_cv(df_ay, feature_cols, "block_number",
                           "Leave-one-block-out CV", args.iterations)

    # ── Per-code accuracy ─────────────────────────────────────
    if loayo.get("y_true_labels"):
        print(f"\n{'─' * 60}")
        print(f"  PER-CODE ACCURACY (leave-one-AY-out)")
        print(f"{'─' * 60}")
        print_per_code_accuracy(loayo["y_true_labels"], loayo["y_pred_labels"])

    # ── Feature importance ────────────────────────────────────
    print(f"\n{'─' * 60}")
    print(f"  FEATURE IMPORTANCE")
    print(f"{'─' * 60}")
    feat_imp = run_feature_importance(df, feature_cols)

    # ── Feature ablation ──────────────────────────────────────
    ablation = {}
    if not args.skip_ablation:
        print(f"\n{'─' * 60}")
        print(f"  FEATURE ABLATION")
        print(f"{'─' * 60}")
        ablation = run_feature_ablation(df, min(args.iterations, 500))

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
            "per_fold": loayo.get("results", []),
        },
        "leave_one_block_out": {
            "overall_accuracy": lobo.get("overall_accuracy"),
            "mean_fold_accuracy": lobo.get("mean_accuracy"),
            "per_fold": lobo.get("results", []),
        },
        "feature_importance": feat_imp,
        "ablation": ablation,
        "baseline_accuracy": 0.688,
    }
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(results, indent=2, default=str))
    print(f"\n  Results saved to {out}")


if __name__ == "__main__":
    main()
