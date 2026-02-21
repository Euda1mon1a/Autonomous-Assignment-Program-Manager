"""Knowledge distillation for schedule display-code prediction.

Privileged Features Distillation (PFD): train a teacher model WITH visual
features (RGB color from Excel) that won't be available at inference time
for new schedules, then distill the teacher's knowledge into a student
model that uses only structural features.

Method:
  1. Train teacher CatBoost with ALL features (structural + visual RGB)
  2. Generate soft labels (temperature-scaled predict_proba) for all cells
  3. Train student CatBoost on structural features only against:
       α * KL(student, soft_labels) + (1-α) * CE(student, hard_labels)
  4. Compare student vs baseline (68.8% hierarchical lookup)

Usage:
    python distill.py --features data/features_universal.json
    python distill.py --features data/features_universal.json --alpha 0.7 --temperature 3.0
    python distill.py --features data/features_universal.json --teacher-only
    python distill.py --features data/features_universal.json --student-only --soft-labels data/soft_labels.npz
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np
import pandas as pd
from catboost import CatBoostClassifier, Pool
from sklearn.metrics import accuracy_score
from sklearn.preprocessing import LabelEncoder

# ── Reuse feature config from learn_catboost.py ─────────────────

CATEGORICAL = ["rotation", "person_type", "half", "team_or_template", "role_raw"]
NUMERICAL = [
    "pgy_level", "day_of_week", "is_weekend", "day_index", "week_in_block",
    "fill_r", "fill_g", "fill_b", "font_r", "font_g", "font_b",
    "font_bold", "has_fill", "has_font_color", "academic_year",
    "block_number", "row_position",
]
CONTEXT = ["prev_same_half", "next_same_half", "other_half"]
VISUAL = [
    "fill_r", "fill_g", "fill_b", "font_r", "font_g", "font_b",
    "has_fill", "has_font_color",
]
TARGET = "cell_text"


# ── Shared utilities (duplicated from learn_catboost for standalone use) ─

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


def make_catboost(n_classes: int, iterations: int = 1000,
                  loss: str = "MultiClass") -> CatBoostClassifier:
    """Create a CatBoost classifier with good defaults."""
    return CatBoostClassifier(
        iterations=iterations,
        depth=8,
        learning_rate=0.05,
        auto_class_weights="Balanced",
        random_seed=42,
        verbose=0,
        task_type="CPU",
        one_hot_max_size=10,
        loss_function=loss,
    )


# ── Soft label generation ────────────────────────────────────────

def temperature_scale(logits: np.ndarray, T: float) -> np.ndarray:
    """Apply temperature scaling to probability distribution.

    Softens the distribution: T=1 is identity, T>1 spreads mass,
    revealing inter-class relationships the teacher learned.
    """
    if T == 1.0:
        return logits
    # Work in log space to avoid overflow
    log_probs = np.log(logits + 1e-10) / T
    log_probs -= log_probs.max(axis=1, keepdims=True)  # numerical stability
    exp_probs = np.exp(log_probs)
    return exp_probs / exp_probs.sum(axis=1, keepdims=True)


# ── Teacher training ─────────────────────────────────────────────

def train_teacher(df: pd.DataFrame, iterations: int = 1000
                  ) -> tuple[CatBoostClassifier, LabelEncoder, np.ndarray]:
    """Train teacher CatBoost with ALL features including visual RGB.

    Returns: (teacher_model, label_encoder, predict_proba on full data)
    """
    feature_cols = get_feature_cols(include_visual=True, include_context=False)
    cat_indices = get_cat_indices(feature_cols)

    le = LabelEncoder()
    X, y, le = prepare_catboost_data(df, feature_cols, le)
    n_classes = len(le.classes_)

    print(f"\n  Training teacher ({n_classes} classes, {len(feature_cols)} features, "
          f"{iterations} iterations)...")
    print(f"  Visual features included: {[c for c in feature_cols if c in VISUAL]}")

    clf = make_catboost(n_classes, iterations)
    pool = Pool(X, y, cat_features=cat_indices)

    t0 = time.time()
    clf.fit(pool)
    elapsed = time.time() - t0
    print(f"  Teacher trained in {elapsed:.1f}s")

    # In-sample accuracy (sanity check, should be very high)
    y_pred = clf.predict(pool).flatten().astype(int)
    train_acc = accuracy_score(y, y_pred)
    print(f"  Teacher in-sample accuracy: {train_acc:.1%}")

    # Generate probability predictions on full dataset
    proba = clf.predict_proba(pool)
    print(f"  Soft labels shape: {proba.shape}")

    return clf, le, proba


def save_soft_labels(proba: np.ndarray, le: LabelEncoder,
                     temperature: float, output_path: str):
    """Save temperature-scaled soft labels."""
    soft = temperature_scale(proba, temperature)
    np.savez_compressed(
        output_path,
        soft_labels=soft,
        classes=le.classes_,
        temperature=np.array([temperature]),
    )
    print(f"  Soft labels (T={temperature}) saved to {output_path}")
    print(f"  Shape: {soft.shape}, Size: {Path(output_path).stat().st_size / 1e6:.1f}MB")


def load_soft_labels(path: str) -> tuple[np.ndarray, np.ndarray, float]:
    """Load soft labels from file. Returns (soft_labels, classes, temperature)."""
    data = np.load(path)
    return data["soft_labels"], data["classes"], float(data["temperature"][0])


# ── Student training (distillation) ──────────────────────────────

def train_student_fold(
    train_df: pd.DataFrame,
    test_df: pd.DataFrame,
    feature_cols: list[str],
    le: LabelEncoder,
    fold_soft_labels: np.ndarray,
    alpha: float,
    iterations: int,
) -> tuple[float, np.ndarray, np.ndarray]:
    """Train one student fold using distillation.

    CatBoost doesn't natively support soft-label distillation, so we
    approximate with sample weighting:
      - High teacher confidence → high weight (clear signal)
      - Low teacher confidence → low weight (ambiguous, trust hard label less)

    AND we use the teacher's argmax as the label for a fraction of the data
    (the alpha fraction), which transfers the teacher's opinion on ambiguous codes.

    Args:
        fold_soft_labels: Pre-computed soft labels aligned to train_df rows.
            Must be generated from a teacher trained on train_df only (not full data)
            to prevent information leakage during cross-validation.
    """
    cat_indices = get_cat_indices(feature_cols)

    # Prepare structural-only features
    X_train, y_train_hard, _ = prepare_catboost_data(train_df, feature_cols, le)
    X_test, y_test, _ = prepare_catboost_data(test_df, feature_cols, le)

    # Soft labels already aligned to training rows
    soft_train = fold_soft_labels

    # Teacher's prediction (argmax of soft labels)
    y_train_soft = soft_train.argmax(axis=1)

    # Teacher's confidence (max probability) as sample weight
    teacher_confidence = soft_train.max(axis=1)

    # Strategy: blend hard and soft labels
    # For alpha fraction: use teacher's soft argmax label, weighted by confidence
    # For (1-alpha) fraction: use hard ground truth label
    n = len(y_train_hard)
    rng = np.random.RandomState(42)
    soft_mask = rng.random(n) < alpha

    y_blended = y_train_hard.copy()
    y_blended[soft_mask] = y_train_soft[soft_mask]

    # Weight: teacher confidence for soft-label rows, 1.0 for hard-label rows
    weights = np.ones(n, dtype=np.float32)
    weights[soft_mask] = teacher_confidence[soft_mask]

    # Train student
    clf = make_catboost(len(le.classes_), iterations)
    train_pool = Pool(X_train, y_blended, cat_features=cat_indices, weight=weights)
    test_pool = Pool(X_test, cat_features=cat_indices)

    clf.fit(train_pool)
    y_pred = clf.predict(test_pool).flatten().astype(int)

    acc = accuracy_score(y_test, y_pred)
    return acc, y_test, y_pred


def run_distillation_cv(
    df: pd.DataFrame,
    split_col: str,
    alpha: float,
    iterations: int,
    desc: str,
    temperature: float = 3.0,
) -> dict:
    """Run leave-one-out CV for distilled student (structural features only).

    Trains a fold-specific teacher per fold on training data only to prevent
    soft-label leakage into the evaluation. Slower (~N× for N folds) but
    produces unbiased CV estimates.
    """
    feature_cols = get_feature_cols(include_visual=False, include_context=False)
    groups = sorted(df[split_col].unique())

    print(f"\n  {desc} ({len(groups)} folds, alpha={alpha})")
    print(f"  {'─' * 55}")
    print(f"  Features ({len(feature_cols)}): structural only (no RGB)")

    # Need a global label encoder fit on all data
    le = LabelEncoder()
    le.fit(df[TARGET])

    results = []
    all_y_true = []
    all_y_pred = []

    # Track original indices for soft label alignment
    df = df.reset_index(drop=True)

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
        test_df = test_df[test_df[TARGET].isin(le.classes_)]
        if len(test_df) == 0:
            print(f"    {split_col}={group}: SKIP (all codes unseen)")
            continue

        # Train fold-specific teacher on training data only (prevents leakage)
        teacher_cols = get_feature_cols(include_visual=True, include_context=False)
        teacher_cat_idx = get_cat_indices(teacher_cols)
        X_teacher, y_teacher, _ = prepare_catboost_data(train_df, teacher_cols, le)
        fold_teacher = make_catboost(len(le.classes_), iterations)
        teacher_pool = Pool(X_teacher, y_teacher, cat_features=teacher_cat_idx)
        fold_teacher.fit(teacher_pool)
        fold_proba = fold_teacher.predict_proba(teacher_pool)
        fold_soft_labels = temperature_scale(fold_proba, temperature)

        t0 = time.time()
        acc, y_test, y_pred = train_student_fold(
            train_df, test_df, feature_cols, le,
            fold_soft_labels, alpha, iterations,
        )
        elapsed = time.time() - t0

        results.append({
            "group": group,
            "accuracy": acc,
            "n_train": len(train_df),
            "n_test": len(test_df),
            "elapsed": elapsed,
        })
        all_y_true.extend(y_test.tolist())
        all_y_pred.extend(y_pred.tolist())

        print(f"    {split_col}={group}: {acc:.1%} "
              f"({len(test_df)} test, {len(train_df)} train, {elapsed:.1f}s)")

    if not results:
        print("    No valid folds")
        return {"mean_accuracy": 0, "overall_accuracy": 0, "results": []}

    mean_acc = np.mean([r["accuracy"] for r in results])
    overall_acc = accuracy_score(all_y_true, all_y_pred)
    print(f"\n    Mean fold accuracy: {mean_acc:.1%}")
    print(f"    Overall accuracy:   {overall_acc:.1%}")

    return {
        "mean_accuracy": float(mean_acc),
        "overall_accuracy": float(overall_acc),
        "results": results,
    }


# ── Vanilla baseline (no distillation, no visual) ───────────────

def run_vanilla_cv(df: pd.DataFrame, split_col: str,
                   iterations: int, desc: str) -> dict:
    """Run CV with structural features only, no distillation (baseline)."""
    feature_cols = get_feature_cols(include_visual=False, include_context=False)
    cat_indices = get_cat_indices(feature_cols)
    groups = sorted(df[split_col].unique())

    print(f"\n  {desc} ({len(groups)} folds)")
    print(f"  {'─' * 55}")

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

        train_codes = set(train_df[TARGET])
        test_df = test_df[test_df[TARGET].isin(train_codes)]
        if len(test_df) == 0:
            print(f"    {split_col}={group}: SKIP")
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

        print(f"    {split_col}={group}: {acc:.1%} "
              f"({len(test_df)} test, {len(train_df)} train, {elapsed:.1f}s)")

    if not results:
        return {"mean_accuracy": 0, "overall_accuracy": 0, "results": []}

    mean_acc = np.mean([r["accuracy"] for r in results])
    overall_acc = accuracy_score(all_y_true, all_y_pred)
    print(f"\n    Mean fold accuracy: {mean_acc:.1%}")
    print(f"    Overall accuracy:   {overall_acc:.1%}")

    return {
        "mean_accuracy": float(mean_acc),
        "overall_accuracy": float(overall_acc),
        "results": results,
    }


# ── Teacher CV (with visual features) ───────────────────────────

def run_teacher_cv(df: pd.DataFrame, split_col: str,
                   iterations: int, desc: str) -> dict:
    """Run CV with ALL features including visual (teacher upper bound)."""
    feature_cols = get_feature_cols(include_visual=True, include_context=False)
    cat_indices = get_cat_indices(feature_cols)
    groups = sorted(df[split_col].unique())

    print(f"\n  {desc} ({len(groups)} folds)")
    print(f"  {'─' * 55}")

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

        train_codes = set(train_df[TARGET])
        test_df = test_df[test_df[TARGET].isin(train_codes)]
        if len(test_df) == 0:
            print(f"    {split_col}={group}: SKIP")
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

        print(f"    {split_col}={group}: {acc:.1%} "
              f"({len(test_df)} test, {len(train_df)} train, {elapsed:.1f}s)")

    if not results:
        return {"mean_accuracy": 0, "overall_accuracy": 0, "results": []}

    mean_acc = np.mean([r["accuracy"] for r in results])
    overall_acc = accuracy_score(all_y_true, all_y_pred)
    print(f"\n    Mean fold accuracy: {mean_acc:.1%}")
    print(f"    Overall accuracy:   {overall_acc:.1%}")

    return {
        "mean_accuracy": float(mean_acc),
        "overall_accuracy": float(overall_acc),
        "results": results,
    }


# ── Alpha sweep ──────────────────────────────────────────────────

def alpha_sweep(df: pd.DataFrame, soft_labels: np.ndarray,
                iterations: int = 500) -> dict:
    """Quick sweep over alpha values using smallest AY as holdout."""
    test_ay = df["academic_year"].value_counts().idxmin()
    feature_cols = get_feature_cols(include_visual=False, include_context=False)
    cat_indices = get_cat_indices(feature_cols)

    test_mask = df["academic_year"] == test_ay
    train_df = df[~test_mask].reset_index(drop=True)
    test_df_raw = df[test_mask]

    le = LabelEncoder()
    le.fit(df[TARGET])

    train_codes = set(train_df[TARGET])
    test_df = test_df_raw[test_df_raw[TARGET].isin(train_codes)]
    test_df = test_df[test_df[TARGET].isin(le.classes_)]

    # Reindex full df for soft label alignment
    df_reindexed = df.reset_index(drop=True)
    train_indices_in_full = df_reindexed[~test_mask.values].index.values

    print(f"\n  Alpha sweep (test AY={test_ay}, {len(test_df)} test, "
          f"{len(train_df)} train, {iterations} iters)")
    print(f"  {'─' * 55}")

    alphas = [0.0, 0.1, 0.3, 0.5, 0.7, 0.9, 1.0]
    results = {}

    for a in alphas:
        fold_soft = soft_labels[train_indices_in_full[:len(train_df)]]
        acc, _, _ = train_student_fold(
            train_df, test_df, feature_cols, le,
            fold_soft, alpha=a, iterations=iterations,
        )
        results[a] = float(acc)
        print(f"    alpha={a:.1f}: {acc:.1%}")

    best_alpha = max(results, key=results.get)
    print(f"\n    Best alpha: {best_alpha} ({results[best_alpha]:.1%})")
    return results


# ── Main ─────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Knowledge distillation for schedule display-code prediction"
    )
    parser.add_argument(
        "--features", default="data/features_universal.json",
        help="Feature JSON from extract_universal.py",
    )
    parser.add_argument(
        "--min-code-count", type=int, default=10,
        help="Minimum occurrences for a code to be included",
    )
    parser.add_argument(
        "--iterations", type=int, default=1000,
        help="CatBoost training iterations",
    )
    parser.add_argument(
        "--temperature", type=float, default=3.0,
        help="Temperature for soft label generation (higher = softer)",
    )
    parser.add_argument(
        "--alpha", type=float, default=0.5,
        help="Blend ratio: 0=hard labels only, 1=soft labels only",
    )
    parser.add_argument(
        "--teacher-only", action="store_true",
        help="Only train teacher and save soft labels (skip student)",
    )
    parser.add_argument(
        "--student-only", action="store_true",
        help="Only train student (requires --soft-labels)",
    )
    parser.add_argument(
        "--soft-labels", default="data/soft_labels.npz",
        help="Path to soft labels file",
    )
    parser.add_argument(
        "--skip-sweep", action="store_true",
        help="Skip alpha hyperparameter sweep",
    )
    parser.add_argument(
        "--output", default="data/distill_results.json",
        help="Output results JSON",
    )
    args = parser.parse_args()

    print(f"\n{'=' * 65}")
    print(f"  KNOWLEDGE DISTILLATION — PRIVILEGED FEATURES")
    print(f"{'=' * 65}")
    print(f"  Temperature: {args.temperature}")
    print(f"  Alpha:       {args.alpha}")
    print(f"  Iterations:  {args.iterations}")

    df = load_data(args.features, args.min_code_count)
    results = {"baseline_accuracy": 0.688}

    # ── Step 1: Teacher (or load soft labels) ────────────────────

    if args.student_only:
        print(f"\n  Loading soft labels from {args.soft_labels}...")
        soft_labels, classes, temperature = load_soft_labels(args.soft_labels)
        print(f"  Loaded {soft_labels.shape[0]} soft labels, "
              f"{soft_labels.shape[1]} classes, T={temperature}")
        # Validate alignment: soft labels must match current feature count
        if soft_labels.shape[0] != len(df):
            print(
                f"\n  ERROR: Soft labels have {soft_labels.shape[0]} rows but "
                f"features have {len(df)} rows. The .npz file is stale — "
                f"re-run without --student-only to regenerate soft labels."
            )
            sys.exit(1)
    else:
        print(f"\n{'─' * 65}")
        print(f"  STEP 1: TRAIN TEACHER (all features + visual RGB)")
        print(f"{'─' * 65}")

        teacher, le, proba = train_teacher(df, args.iterations)

        # Save soft labels
        soft_path = Path(args.soft_labels)
        soft_path.parent.mkdir(parents=True, exist_ok=True)
        save_soft_labels(proba, le, args.temperature, str(soft_path))
        soft_labels = temperature_scale(proba, args.temperature)

        # Teacher CV (upper bound)
        print(f"\n{'─' * 65}")
        print(f"  TEACHER CROSS-VALIDATION (upper bound)")
        print(f"{'─' * 65}")

        teacher_loayo = run_teacher_cv(
            df, "academic_year", args.iterations,
            "Teacher LOAYO (all features + visual)",
        )
        results["teacher_loayo"] = teacher_loayo

        if args.teacher_only:
            print(f"\n  Teacher-only mode. Soft labels saved. Exiting.")
            out = Path(args.output)
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(json.dumps(results, indent=2, default=str))
            print(f"  Results saved to {out}")
            return

    # ── Step 2: Vanilla baseline (structural only, no distillation) ──

    print(f"\n{'─' * 65}")
    print(f"  STEP 2: VANILLA BASELINE (structural only, no distillation)")
    print(f"{'─' * 65}")

    vanilla_loayo = run_vanilla_cv(
        df, "academic_year", args.iterations,
        "Vanilla LOAYO (structural only, no RGB)",
    )
    results["vanilla_loayo"] = vanilla_loayo

    # ── Step 3: Alpha sweep (quick, find best alpha) ─────────────

    if not args.skip_sweep:
        print(f"\n{'─' * 65}")
        print(f"  STEP 3: ALPHA SWEEP")
        print(f"{'─' * 65}")

        sweep_results = alpha_sweep(df, soft_labels, iterations=500)
        results["alpha_sweep"] = {str(k): v for k, v in sweep_results.items()}

        # Use best alpha for full CV
        best_alpha = max(sweep_results, key=sweep_results.get)
        if best_alpha != args.alpha:
            print(f"\n  Using sweep-optimal alpha={best_alpha} "
                  f"(overriding --alpha={args.alpha})")
            args.alpha = best_alpha

    # ── Step 4: Distilled student CV ─────────────────────────────

    print(f"\n{'─' * 65}")
    print(f"  STEP 4: DISTILLED STUDENT (structural only, soft labels)")
    print(f"{'─' * 65}")

    student_loayo = run_distillation_cv(
        df, "academic_year", args.alpha, args.iterations,
        f"Student LOAYO (alpha={args.alpha}, T={args.temperature})",
        temperature=args.temperature,
    )
    results["student_loayo"] = student_loayo

    # ── Step 5: LOBO on biggest AY ───────────────────────────────

    print(f"\n{'─' * 65}")
    print(f"  STEP 5: LEAVE-ONE-BLOCK-OUT (biggest AY)")
    print(f"{'─' * 65}")

    biggest_ay = df["academic_year"].value_counts().idxmax()
    df_ay = df[df["academic_year"] == biggest_ay].copy()
    print(f"  Using AY {biggest_ay} ({len(df_ay)} cells, "
          f"{df_ay['block_number'].nunique()} blocks)")

    # Vanilla LOBO
    vanilla_lobo = run_vanilla_cv(
        df_ay, "block_number", args.iterations,
        "Vanilla LOBO (structural only)",
    )
    results["vanilla_lobo"] = vanilla_lobo

    # Student LOBO — fold teachers trained per-fold inside run_distillation_cv
    df_ay_for_lobo = df_ay.reset_index(drop=True)
    student_lobo = run_distillation_cv(
        df_ay_for_lobo, "block_number",
        args.alpha, args.iterations,
        f"Student LOBO (alpha={args.alpha})",
        temperature=args.temperature,
    )
    results["student_lobo"] = student_lobo

    # ── Summary ──────────────────────────────────────────────────

    print(f"\n{'=' * 65}")
    print(f"  DISTILLATION SUMMARY")
    print(f"{'=' * 65}")
    print(f"  Baseline (hierarchical lookup):   68.80%")

    if "teacher_loayo" in results:
        t_acc = results["teacher_loayo"].get("overall_accuracy", 0)
        print(f"  Teacher LOAYO (with RGB):         {t_acc:.1%}  [upper bound]")

    v_loayo = vanilla_loayo.get("overall_accuracy", 0)
    s_loayo = student_loayo.get("overall_accuracy", 0)
    print(f"  Vanilla LOAYO (no RGB):           {v_loayo:.1%}")
    print(f"  Student LOAYO (distilled):        {s_loayo:.1%}")
    distill_gain = (s_loayo - v_loayo) * 100
    print(f"  Distillation gain (LOAYO):        {distill_gain:+.1f}pp")

    v_lobo = vanilla_lobo.get("overall_accuracy", 0)
    s_lobo = student_lobo.get("overall_accuracy", 0)
    print(f"\n  Vanilla LOBO (no RGB):            {v_lobo:.1%}")
    print(f"  Student LOBO (distilled):         {s_lobo:.1%}")
    distill_gain_lobo = (s_lobo - v_lobo) * 100
    print(f"  Distillation gain (LOBO):         {distill_gain_lobo:+.1f}pp")

    overall_gain = (s_lobo - 0.688) * 100
    print(f"\n  Improvement over baseline:        {overall_gain:+.1f}pp")

    if s_loayo > v_loayo + 0.005:
        print(f"\n  VERDICT: Distillation WORKS — student recovered signal from RGB")
    elif s_loayo > v_loayo - 0.005:
        print(f"\n  VERDICT: Distillation MARGINAL — minimal transfer from RGB")
    else:
        print(f"\n  VERDICT: Distillation FAILED — soft labels didn't help")
        print(f"  Color signal may be too privileged for distillation at this scale")

    results["distillation_gain_loayo_pp"] = float(distill_gain)
    results["distillation_gain_lobo_pp"] = float(distill_gain_lobo)
    results["improvement_over_baseline_pp"] = float(overall_gain)
    results["alpha_used"] = float(args.alpha)
    results["temperature_used"] = float(args.temperature)

    # Save
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(results, indent=2, default=str))
    print(f"\n  Results saved to {out}")
    print(f"{'=' * 65}")


if __name__ == "__main__":
    main()
