#!/usr/bin/env python3
"""Cluster rotation profiles into archetypes using HDBSCAN.

Reads rotation_profiles.json from Phase 1 and discovers natural rotation
groupings via unsupervised clustering on code-frequency vectors.

Usage:
    cd ~/workspace/aapm
    backend/.venv/bin/python scripts/ml/cluster_rotations.py \
        --profiles /tmp/rotation_profiles.json \
        --output /tmp/rotation_clusters.json
"""

import argparse
import json
import os
import sys
from collections import Counter, defaultdict
from pathlib import Path

import hdbscan
import numpy as np
import psycopg2
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

# Same background codes as mine_rotation_patterns.py
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
    p.add_argument("--output", default="/tmp/rotation_clusters.json")
    p.add_argument("--db-url", default=os.getenv(
        "DATABASE_URL",
        "postgresql://scheduler@localhost:5432/residency_scheduler",
    ))
    p.add_argument("--min-cluster-size", type=int, default=5)
    return p.parse_args()


def load_profiles(path):
    """Load and filter to meaningful profiles (exclude background_only)."""
    data = json.loads(Path(path).read_text())
    meaningful = [p for p in data if p["rotation_category"] != "background_only"]
    return meaningful, data


def build_feature_matrix(profiles):
    """Build feature matrix from rotation profiles.

    Features:
    - Normalized code frequency vector (foreground codes only)
    - Temporal: foreground_pct, is_split_block
    - Context: pgy_level one-hot, person_type
    """
    # Collect all foreground codes across profiles
    all_fg_codes = set()
    for p in profiles:
        for code in p["foreground_codes"]:
            all_fg_codes.add(code)
    fg_code_list = sorted(all_fg_codes)
    code_to_idx = {c: i for i, c in enumerate(fg_code_list)}

    n_codes = len(fg_code_list)
    n_profiles = len(profiles)

    # Build feature vectors
    features = np.zeros((n_profiles, n_codes + 6), dtype=np.float32)
    for i, p in enumerate(profiles):
        total = p["total_hdas"] or 1
        # Code frequencies (normalized by total HDAs)
        for code in p["foreground_codes"]:
            if code in code_to_idx:
                count = p["code_counts"].get(code, 0)
                features[i, code_to_idx[code]] = count / total

        # Temporal features
        features[i, n_codes] = p["foreground_pct"]
        features[i, n_codes + 1] = 1.0 if p["is_split_block"] else 0.0

        # PGY one-hot (3 slots for PGY 1-3, 0 for faculty)
        pgy = p["pgy_level"]
        if pgy and 1 <= pgy <= 3:
            features[i, n_codes + 1 + pgy] = 1.0

        # Faculty flag
        features[i, n_codes + 5] = 1.0 if p["person_type"] == "faculty" else 0.0

    feature_names = fg_code_list + [
        "foreground_pct", "is_split_block",
        "is_pgy1", "is_pgy2", "is_pgy3", "is_faculty",
    ]
    return features, feature_names, fg_code_list


def fetch_rotation_templates(db_url):
    """Fetch rotation template names for comparison."""
    conn = psycopg2.connect(db_url)
    cur = conn.cursor()
    cur.execute("SELECT id::text, name, rotation_type, template_category FROM rotation_templates WHERE NOT is_archived")
    templates = {}
    for row in cur.fetchall():
        templates[row[1]] = {
            "id": row[0],
            "name": row[1],
            "rotation_type": row[2],
            "category": row[3],
        }
    conn.close()
    return templates


def describe_cluster(cluster_profiles, fg_code_list):
    """Generate a human-readable description of a cluster."""
    n = len(cluster_profiles)

    # Dominant codes
    dom_codes = Counter(p["dominant_code"] for p in cluster_profiles if p["dominant_code"])
    top_code = dom_codes.most_common(1)[0] if dom_codes else (None, 0)

    # PGY distribution
    pgy_dist = Counter(p["pgy_level"] for p in cluster_profiles)

    # Rotation categories
    cat_dist = Counter(p["rotation_category"] for p in cluster_profiles)

    # Average foreground codes across members
    code_totals = Counter()
    for p in cluster_profiles:
        for code in p["foreground_codes"]:
            code_totals[code] += p["code_counts"].get(code, 0)

    # Templates assigned
    templates = Counter(
        p["assigned_template"] for p in cluster_profiles
        if p["assigned_template"]
    )

    # Split-block rate
    split_rate = sum(1 for p in cluster_profiles if p["is_split_block"]) / n

    # Generate label
    if top_code[0] and top_code[1] / n > 0.5:
        label = f"{top_code[0]}-dominant"
    elif cat_dist.most_common(1)[0][0] == "mono_rotation":
        label = f"mono-{top_code[0] or 'varied'}"
    elif split_rate > 0.5:
        label = "split-block"
    else:
        top_codes = [c for c, _ in code_totals.most_common(3)]
        label = "+".join(top_codes[:2]) if top_codes else "mixed"

    return {
        "label": label,
        "size": n,
        "dominant_codes": dict(dom_codes.most_common(5)),
        "pgy_distribution": {str(k): v for k, v in sorted(pgy_dist.items(), key=lambda x: str(x[0]))},
        "category_distribution": dict(cat_dist),
        "top_foreground_codes": dict(code_totals.most_common(10)),
        "split_block_rate": round(split_rate, 2),
        "templates_matched": dict(templates.most_common(5)),
        "members": [
            {
                "person_name": p["person_name"],
                "block_number": p["block_number"],
                "dominant_code": p["dominant_code"],
                "pgy_level": p["pgy_level"],
                "person_type": p["person_type"],
                "assigned_template": p["assigned_template"],
            }
            for p in cluster_profiles
        ],
    }


def main():
    args = parse_args()

    print("Loading rotation profiles...")
    meaningful, all_profiles = load_profiles(args.profiles)
    print(f"  {len(meaningful)} meaningful profiles (of {len(all_profiles)} total)")

    print("\nBuilding feature matrix...")
    features, feature_names, fg_code_list = build_feature_matrix(meaningful)
    print(f"  Shape: {features.shape} ({len(fg_code_list)} foreground codes + 6 context features)")

    # Scale features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(features)

    # PCA for dimensionality reduction
    n_components = min(15, features.shape[1], features.shape[0] - 1)
    pca = PCA(n_components=n_components)
    X_pca = pca.fit_transform(X_scaled)
    explained = sum(pca.explained_variance_ratio_)
    print(f"  PCA: {n_components} components, {explained:.1%} variance explained")

    # Top PCA loadings
    print(f"\n  Top PCA feature loadings (PC1):")
    pc1_loadings = sorted(
        zip(feature_names, pca.components_[0]),
        key=lambda x: abs(x[1]), reverse=True,
    )[:10]
    for name, loading in pc1_loadings:
        print(f"    {name:20s} {loading:+.3f}")

    # HDBSCAN clustering
    print(f"\nClustering with HDBSCAN (min_cluster_size={args.min_cluster_size})...")
    clusterer = hdbscan.HDBSCAN(
        min_cluster_size=args.min_cluster_size,
        min_samples=3,
        metric="euclidean",
        cluster_selection_method="eom",
    )
    labels = clusterer.fit_predict(X_pca)

    n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
    n_noise = sum(1 for l in labels if l == -1)
    print(f"  Found {n_clusters} clusters + {n_noise} noise points")

    # Build cluster descriptions
    clusters_by_label = defaultdict(list)
    for i, label in enumerate(labels):
        clusters_by_label[label].append(meaningful[i])

    cluster_output = []
    print(f"\n{'='*60}")
    print(f"  CLUSTER DESCRIPTIONS")
    print(f"{'='*60}")

    for label in sorted(clusters_by_label.keys()):
        if label == -1:
            continue
        cluster_profiles = clusters_by_label[label]
        desc = describe_cluster(cluster_profiles, fg_code_list)
        desc["cluster_id"] = label
        cluster_output.append(desc)

        print(f"\n  Cluster {label}: {desc['label']} (n={desc['size']})")
        print(f"    Dominant codes: {desc['dominant_codes']}")
        print(f"    PGY dist: {desc['pgy_distribution']}")
        print(f"    Categories: {desc['category_distribution']}")
        print(f"    Split rate: {desc['split_block_rate']:.0%}")
        if desc["templates_matched"]:
            print(f"    Templates: {desc['templates_matched']}")

    # Noise points
    if -1 in clusters_by_label:
        noise_profiles = clusters_by_label[-1]
        noise_desc = describe_cluster(noise_profiles, fg_code_list)
        noise_desc["cluster_id"] = -1
        noise_desc["label"] = "noise"
        cluster_output.append(noise_desc)
        print(f"\n  Noise: {noise_desc['size']} profiles")
        print(f"    Dominant codes: {noise_desc['dominant_codes']}")

    # Compare clusters to templates
    print(f"\n{'='*60}")
    print(f"  CLUSTER ↔ TEMPLATE MAPPING")
    print(f"{'='*60}")

    templates = fetch_rotation_templates(args.db_url)
    for desc in cluster_output:
        if desc["cluster_id"] == -1:
            continue
        matched = desc["templates_matched"]
        if matched:
            top_tmpl = max(matched, key=matched.get)
            coverage = matched[top_tmpl] / desc["size"]
            print(f"  Cluster {desc['cluster_id']:2d} ({desc['label']:25s}) → {top_tmpl} ({coverage:.0%} of members)")
        else:
            print(f"  Cluster {desc['cluster_id']:2d} ({desc['label']:25s}) → NO TEMPLATE MATCH")

    # Write output
    output = {
        "n_profiles": len(meaningful),
        "n_clusters": n_clusters,
        "n_noise": n_noise,
        "feature_names": feature_names,
        "pca_variance_explained": round(explained, 3),
        "clusters": cluster_output,
    }

    out_path = Path(args.output)
    out_path.write_text(json.dumps(output, indent=2, default=str))
    print(f"\n  Output: {out_path} ({out_path.stat().st_size / 1024:.1f} KB)")


if __name__ == "__main__":
    main()
