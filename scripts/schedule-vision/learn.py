"""Train classifier to predict display codes from visual + contextual features.

Uses Random Forest (robust with few examples, high cardinality) and
Decision Tree (interpretable, prints human-readable rules).

Usage:
    python learn.py --features data/features.json --output data/model.pkl
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

import joblib
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import cross_val_score, StratifiedKFold
from sklearn.preprocessing import LabelEncoder
from sklearn.tree import DecisionTreeClassifier, export_text


# ── Feature configuration ────────────────────────────────────
# Only features available at PREDICTION time (no data leakage).
CAT_FIELDS = [
    "rotation1", "rotation2", "template", "role", "db_code",
    "template_expected", "db_other_half", "fill_rgb", "font_rgb",
    "person_type",
]

NUM_FIELDS = [
    ("pgy_level", 0),           # PGY year (1/2/3), 0 = unknown
    ("block_number", 0),        # Block number (1-13)
    ("day_of_week", -1),        # 0=Mon ... 6=Sun, -1=unknown
    ("is_weekend", 0),          # 1 if Sat/Sun
    ("day_index", 0),           # Day within block (0-27)
    ("is_pm", None),            # 1 if PM half
    ("font_bold", 0),           # 1 if bold font
    ("db_matches_template", 0), # 1 if db_code == template_expected
    ("week_in_block", 0),       # 0-3 which week within the block
]


def _encode_features(
    features: list[dict],
    require_db_code: bool = True,
) -> tuple[np.ndarray, np.ndarray, list[str], dict]:
    """Encode feature dicts into numpy arrays for sklearn.

    Returns (X, y, feature_names, encoders).
    """
    if require_db_code:
        labeled = [f for f in features if f.get("truth_code") and f.get("db_code")]
    else:
        labeled = [f for f in features if f.get("truth_code")]

    encoders: dict[str, LabelEncoder] = {}
    for field in CAT_FIELDS:
        le = LabelEncoder()
        vals = [f.get(field) or "__NONE__" for f in labeled]
        le.fit(vals)
        encoders[field] = le

    rows = []
    for f in labeled:
        row = []
        for field, default in NUM_FIELDS:
            if field == "is_pm":
                row.append(1 if f.get("half") == "pm" else 0)
            elif field == "font_bold":
                row.append(1 if f.get("font_bold") else 0)
            elif field == "is_weekend":
                row.append(1 if f.get("is_weekend") else 0)
            elif field == "db_matches_template":
                row.append(1 if f.get("db_matches_template") else 0)
            else:
                val = f.get(field)
                row.append(val if val is not None else default)
        for field in CAT_FIELDS:
            val = f.get(field) or "__NONE__"
            row.append(encoders[field].transform([val])[0])
        rows.append(row)

    feature_names = [f[0] for f in NUM_FIELDS] + [
        f"enc_{field}" for field in CAT_FIELDS
    ]

    X = np.array(rows, dtype=np.float32)

    y_raw = [f["truth_code"] for f in labeled]
    label_encoder = LabelEncoder()
    y = label_encoder.fit_transform(y_raw)
    encoders["__label__"] = label_encoder

    return X, y, feature_names, encoders


def _rule_baseline(features: list[dict]) -> dict[str, int]:
    """Compute rule-based baseline accuracy."""
    labeled = [f for f in features if f.get("truth_code") and f.get("db_code")]

    NF_MAP = [
        ("LDNF", "L&D"), ("PEDSNF", "PedsNF"), ("PEDNF", "PedsNF"),
        ("PNF", "PedsNF"), ("PEDSW", "PedsNF"), ("NF/ENDO", "NF"), ("NF", "NF"),
    ]
    WEEKEND_OVERRIDES = {"FMIT": "FMIT", "IMW": "IMW", "KAP": "KAP"}
    CLINIC_MAP = {"GYN": "GYN", "SM": "SM"}
    FACULTY_COLLAPSE = {"GME", "CV", "DFM", "SM", "LEC", "ADV", "AT", "DO"}
    CODE_NORM = {"IM": "IMW", "LDNF": "L&D", "PedNF": "PedsNF"}

    def nf_display(rot, rot2):
        combined = f"{rot} {rot2}".upper()
        for key, display in NF_MAP:
            if key in combined:
                return display
        if "NEURO" in combined:
            return "NF"
        return None

    def transform(db_code, rot, rot2, is_weekend, is_faculty):
        code = db_code.strip()
        rot_u = (rot or "").upper()
        rot2_u = (rot2 or "").upper()
        if code in CODE_NORM:
            code = CODE_NORM[code]
        if code == "NF":
            specific = nf_display(rot_u, rot2_u)
            if specific and specific != "NF":
                return specific
        if code == "OFF":
            nf = nf_display(rot_u, rot2_u)
            if nf:
                return nf
        if is_weekend and code == "W":
            nf = nf_display(rot_u, rot2_u)
            if nf:
                return nf
            for rk, disp in WEEKEND_OVERRIDES.items():
                if rk in rot_u:
                    return disp
        if is_faculty and is_weekend and code in FACULTY_COLLAPSE:
            return "W"
        if code == "C":
            for rk, cc in CLINIC_MAP.items():
                if rk.upper() in rot_u or rk.upper() in rot2_u:
                    return cc
        return code

    correct = 0
    total = 0
    for f in labeled:
        is_fac = f.get("person_type") == "faculty"
        transformed = transform(
            f["db_code"], f.get("rotation1", ""), f.get("rotation2", ""),
            f.get("is_weekend", False), is_fac,
        )
        total += 1
        if transformed == f["truth_code"]:
            correct += 1
    return {"correct": correct, "total": total}


def train_and_report(features: list[dict], output_path: str | None = None):
    """Train classifiers and print results."""
    X, y, feature_names, encoders = _encode_features(features, require_db_code=True)
    label_enc = encoders["__label__"]
    labeled = [f for f in features if f.get("truth_code") and f.get("db_code")]

    print(f"\n{'='*60}")
    print(f"  SCHEDULE VISION LEARNER")
    print(f"{'='*60}")
    print(f"\n  Training examples: {len(X)}")
    print(f"  Features: {len(feature_names)}")
    print(f"  Unique display codes: {len(label_enc.classes_)}")

    code_counts = Counter(label_enc.inverse_transform(y))
    print(f"\n  Top 15 codes:")
    for code, cnt in code_counts.most_common(15):
        print(f"    {code:12s} {cnt:5d} ({100*cnt/len(y):.1f}%)")
    rare = sum(1 for _, cnt in code_counts.items() if cnt < 5)
    print(f"\n  Codes with <5 examples: {rare}/{len(code_counts)}")

    # ── Baselines ──────────────────────────────────────────────
    print(f"\n{'─'*60}")
    print(f"  BASELINES")
    print(f"{'─'*60}")

    rb = _rule_baseline(features)
    if rb["total"]:
        print(f"\n  Rule accuracy: {rb['correct']}/{rb['total']} "
              f"({100*rb['correct']/rb['total']:.1f}%)")

    tpl_correct = sum(1 for f in labeled
                      if f.get("template_expected") and f["template_expected"] == f["truth_code"])
    tpl_total = sum(1 for f in labeled if f.get("template_expected"))
    if tpl_total:
        print(f"  Template lookup: {tpl_correct}/{tpl_total} "
              f"({100*tpl_correct/tpl_total:.1f}%) "
              f"[coverage: {tpl_total}/{len(labeled)} = {100*tpl_total/len(labeled):.0f}%]")

    # ── Decision Tree ──────────────────────────────────────────
    print(f"\n{'─'*60}")
    print(f"  DECISION TREE (interpretable)")
    print(f"{'─'*60}")

    dt = DecisionTreeClassifier(
        max_depth=12, min_samples_leaf=3, min_samples_split=5,
        class_weight="balanced",
    )
    min_class = min(code_counts.values())
    n_splits = min(5, max(2, min_class))
    cv = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=42)
    common_mask = np.array([code_counts[label_enc.classes_[yi]] >= n_splits for yi in y])
    X_cv, y_cv = X[common_mask], y[common_mask]
    print(f"\n  CV on {common_mask.sum()}/{len(y)} cells")

    dt_scores = cross_val_score(dt, X_cv, y_cv, cv=cv, scoring="accuracy")
    print(f"  {n_splits}-fold CV accuracy: {dt_scores.mean():.1%} (+/- {dt_scores.std():.1%})")

    dt.fit(X, y)
    importances = sorted(zip(feature_names, dt.feature_importances_), key=lambda x: -x[1])
    print(f"\n  Top feature importances:")
    for name, imp in importances[:8]:
        print(f"    {name:25s} {imp:.3f} {'#' * int(imp * 50)}")

    # ── Random Forest ──────────────────────────────────────────
    print(f"\n{'─'*60}")
    print(f"  RANDOM FOREST")
    print(f"{'─'*60}")

    rf = RandomForestClassifier(
        n_estimators=200, max_depth=15, min_samples_leaf=2,
        class_weight="balanced_subsample", random_state=42, n_jobs=-1,
    )
    rf_scores = cross_val_score(rf, X_cv, y_cv, cv=cv, scoring="accuracy")
    print(f"\n  {n_splits}-fold CV accuracy: {rf_scores.mean():.1%} (+/- {rf_scores.std():.1%})")

    # Leave-one-block-out CV
    blocks = np.array([f.get("block_number", 0) for f in labeled])
    unique_blocks = sorted(set(blocks))
    if len(unique_blocks) > 1:
        print(f"\n  Leave-one-block-out CV:")
        lobo_scores = []
        for test_block in unique_blocks:
            train_mask = blocks != test_block
            test_mask = blocks == test_block
            if test_mask.sum() == 0:
                continue

            # Rotation coverage analysis
            train_rots = set(f.get("rotation1") or "?" for f, m in zip(labeled, train_mask) if m)
            test_rots = set(f.get("rotation1") or "?" for f, m in zip(labeled, test_mask) if m)
            unseen = test_rots - train_rots
            unseen_cells = sum(1 for f, m in zip(labeled, test_mask)
                             if m and (f.get("rotation1") or "?") in unseen)

            rf_temp = RandomForestClassifier(
                n_estimators=200, max_depth=15, min_samples_leaf=2,
                class_weight="balanced_subsample", random_state=42, n_jobs=-1,
            )
            rf_temp.fit(X[train_mask], y[train_mask])
            score = rf_temp.score(X[test_mask], y[test_mask])
            lobo_scores.append((test_block, score, test_mask.sum()))
            print(f"    Block {test_block}: {score:.1%} ({test_mask.sum()} cells, "
                  f"{len(unseen)} unseen rotations = {unseen_cells} cells)")
            if unseen:
                print(f"      Unseen: {sorted(unseen)}")

        if lobo_scores:
            avg = np.mean([s for _, s, _ in lobo_scores])
            print(f"\n  LOBO avg: {avg:.1%}")

    # Fit on all data
    rf.fit(X, y)

    rf_importances = sorted(zip(feature_names, rf.feature_importances_), key=lambda x: -x[1])
    print(f"\n  Top feature importances:")
    for name, imp in rf_importances[:10]:
        print(f"    {name:25s} {imp:.3f} {'#' * int(imp * 50)}")

    # ── Per-code accuracy ──────────────────────────────────────
    print(f"\n{'─'*60}")
    print(f"  PER-CODE ACCURACY (train set)")
    print(f"{'─'*60}")

    y_pred = rf.predict(X)
    for code_idx, code in enumerate(label_enc.classes_):
        mask = y == code_idx
        if mask.sum() < 3:
            continue
        correct = (y_pred[mask] == code_idx).sum()
        total = mask.sum()
        pct = 100 * correct / total
        marker = " ***" if pct >= 80 else ""
        print(f"    {code:12s} {correct:4d}/{total:4d} ({pct:.0f}%){marker}")

    overall_train = (y_pred == y).sum()
    print(f"\n    OVERALL: {overall_train}/{len(y)} ({100*overall_train/len(y):.1f}%)")

    # ── ML vs DB comparison ────────────────────────────────────
    print(f"\n{'─'*60}")
    print(f"  ML vs DB COMPARISON")
    print(f"{'─'*60}")

    ml_correct = db_correct = ml_wins = db_wins = both_right = both_wrong = 0
    total_compared = 0
    for f, pred_idx in zip(labeled, y_pred):
        pred_code = label_enc.inverse_transform([pred_idx])[0]
        db_code = f.get("db_code")
        truth = f["truth_code"]
        if not db_code:
            continue
        total_compared += 1
        ml_right = pred_code == truth
        db_right = db_code == truth
        if ml_right:
            ml_correct += 1
        if db_right:
            db_correct += 1
        if ml_right and db_right:
            both_right += 1
        elif ml_right and not db_right:
            ml_wins += 1
        elif not ml_right and db_right:
            db_wins += 1
        else:
            both_wrong += 1

    if total_compared:
        print(f"\n  ML match:  {100*ml_correct/total_compared:.1f}%")
        print(f"  DB match:  {100*db_correct/total_compared:.1f}%")
        print(f"  ML wins:   {ml_wins:5d} ({100*ml_wins/total_compared:.1f}%)")
        print(f"  DB wins:   {db_wins:5d} ({100*db_wins/total_compared:.1f}%)")
        print(f"  Both wrong:{both_wrong:5d} ({100*both_wrong/total_compared:.1f}%)")

    # ── Transformations learned ────────────────────────────────
    pattern_counts: Counter = Counter()
    for f, pred_idx in zip(labeled, y_pred):
        pred_code = label_enc.inverse_transform([pred_idx])[0]
        db_code = f.get("db_code")
        truth = f["truth_code"]
        if db_code and pred_code == truth and db_code != truth:
            pattern_counts[(db_code, truth)] += 1
    if pattern_counts:
        print(f"\n  Top transformations learned (db → display):")
        for (db, display), cnt in pattern_counts.most_common(15):
            print(f"    {db:8s} → {display:8s}  ({cnt} cells)")

    # Save model
    if output_path:
        model_data = {
            "dt": dt,
            "rf": rf,
            "encoders": encoders,
            "feature_names": feature_names,
        }
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(model_data, out)
        print(f"\n  Saved model to {out}")


def main():
    parser = argparse.ArgumentParser(description="Train schedule display code classifier")
    parser.add_argument("--features", required=True, help="Feature JSON from extract.py")
    parser.add_argument("--output", default="data/model.pkl", help="Output model path")
    args = parser.parse_args()

    features = json.loads(Path(args.features).read_text())
    train_and_report(features, args.output)


if __name__ == "__main__":
    main()
