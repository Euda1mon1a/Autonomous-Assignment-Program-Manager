"""VLM-powered pattern discovery from schedule images.

Uses a local vision-language model (MLX LLaVA or similar) to analyze
schedule images and discover transformation patterns that the ML
classifier can then learn from.

For each person with mismatches, shows the VLM the truth vs DB images
and asks it to explain the differences and identify rules.

Usage:
    python discover.py --images data/images/ --output data/patterns.json

Prerequisites:
    pip install mlx-vlm
    # First run downloads model weights (~4GB)
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def discover_patterns(
    images_dir: str,
    features_path: str | None = None,
    output_path: str = "data/patterns.json",
    model_name: str = "mlx-community/llava-v1.6-mistral-7b-4bit",
    max_persons: int = 10,
) -> list[dict]:
    """Analyze schedule images with VLM to discover patterns.

    Args:
        images_dir: Directory containing rendered PNG images.
        features_path: Optional features JSON for context.
        output_path: Where to write discovered patterns.
        model_name: MLX VLM model to use.
        max_persons: Max number of people to analyze.

    Returns:
        List of discovered pattern dicts.
    """
    img_dir = Path(images_dir)

    # Find people with both truth and diff images
    people = set()
    for f in img_dir.glob("*_truth.png"):
        name = f.stem.replace("_truth", "")
        diff = img_dir / f"{name}_diff.png"
        if diff.exists():
            people.add(name)

    # Load feature context if available
    context: dict[str, dict] = {}
    if features_path:
        features = json.loads(Path(features_path).read_text())
        from collections import defaultdict
        by_person: dict[str, list] = defaultdict(list)
        for f in features:
            safe = f["person"].replace(" ", "_").replace(",", "").replace("/", "_")[:20]
            by_person[safe].append(f)

        for name, cells in by_person.items():
            mismatches = [
                c for c in cells
                if c.get("truth_code") and c.get("db_code")
                and c["truth_code"] != c["db_code"]
            ]
            if mismatches:
                context[name] = {
                    "rotation": cells[0].get("rotation1", ""),
                    "pgy": cells[0].get("pgy_level"),
                    "person_type": cells[0].get("person_type", ""),
                    "mismatch_count": len(mismatches),
                    "total_cells": len(cells),
                    "sample_mismatches": [
                        {"db": m["db_code"], "truth": m["truth_code"],
                         "day": m.get("day_index"), "half": m.get("half")}
                        for m in mismatches[:5]
                    ],
                }

    # Sort by mismatch count (most interesting first)
    sorted_people = sorted(
        [(p, context.get(p, {}).get("mismatch_count", 0)) for p in people],
        key=lambda x: -x[1],
    )

    # Try to load VLM
    try:
        from mlx_vlm import load, generate
        print(f"Loading VLM: {model_name}...")
        model, processor = load(model_name)
        has_vlm = True
    except ImportError:
        print("  mlx-vlm not installed. Running in context-only mode.")
        print("  Install with: pip install mlx-vlm")
        has_vlm = False
    except Exception as e:
        print(f"  VLM load failed: {e}")
        print("  Running in context-only mode.")
        has_vlm = False

    patterns: list[dict] = []
    analyzed = 0

    for name, mismatch_count in sorted_people:
        if analyzed >= max_persons:
            break
        if mismatch_count == 0:
            continue

        truth_img = img_dir / f"{name}_truth.png"
        diff_img = img_dir / f"{name}_diff.png"
        ctx = context.get(name, {})

        print(f"\n  Analyzing {name} ({mismatch_count} mismatches)...")

        if has_vlm:
            prompt = _build_prompt(name, ctx)
            try:
                # Try with image first, fall back to text-only
                try:
                    gen_result = generate(
                        model, processor,
                        prompt,
                        image=str(diff_img),
                        max_tokens=500,
                    )
                except Exception:
                    # Image dimension issues — run text-only
                    gen_result = generate(
                        model, processor,
                        prompt,
                        max_tokens=500,
                    )
                result_text = gen_result.text if hasattr(gen_result, 'text') else str(gen_result)
                patterns.append({
                    "person": name,
                    "context": ctx,
                    "vlm_analysis": result_text,
                    "images": {
                        "truth": str(truth_img),
                        "diff": str(diff_img),
                    },
                })
                print(f"    VLM: {result_text[:200]}...")
            except Exception as e:
                print(f"    VLM error: {e}")
                patterns.append({
                    "person": name,
                    "context": ctx,
                    "vlm_analysis": None,
                    "error": str(e),
                })
        else:
            # Context-only analysis
            if ctx.get("sample_mismatches"):
                print(f"    Rotation: {ctx.get('rotation', '?')}, "
                      f"PGY: {ctx.get('pgy', '?')}")
                for m in ctx["sample_mismatches"]:
                    print(f"    Day {m['day']} {m['half']}: "
                          f"DB={m['db']} → Truth={m['truth']}")

            patterns.append({
                "person": name,
                "context": ctx,
                "vlm_analysis": None,
            })

        analyzed += 1

    # Write patterns
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(patterns, indent=2))
    print(f"\n  Analyzed {analyzed} people, wrote patterns to {out}")

    return patterns


def _build_prompt(name: str, ctx: dict) -> str:
    """Build VLM prompt for pattern discovery."""
    rotation = ctx.get("rotation", "unknown")
    pgy = ctx.get("pgy", "unknown")
    person_type = ctx.get("person_type", "unknown")
    mismatches = ctx.get("sample_mismatches", [])

    mismatch_text = ""
    if mismatches:
        mismatch_text = "\nKnown mismatches:\n" + "\n".join(
            f"  Day {m['day']} {m['half']}: DB shows '{m['db']}', "
            f"should be '{m['truth']}'"
            for m in mismatches
        )

    return f"""You are analyzing a medical residency schedule image.

This shows the schedule for {name}, a {person_type} (PGY-{pgy}) on {rotation} rotation.

The image shows a 28-day grid with AM (top) and PM (bottom) rows.
Red-bordered cells indicate where the database code differs from the
coordinator's hand-entered truth.

{mismatch_text}

Please analyze the visual patterns:
1. What colors distinguish different activity types?
2. What patterns explain the mismatches (red-bordered cells)?
3. State any rules you can identify as:
   IF [rotation/PGY/day/color conditions] THEN [db_code] should be [display_code]

Focus on patterns that could be generalized to other people on similar rotations."""


def main():
    parser = argparse.ArgumentParser(
        description="VLM pattern discovery from schedule images",
    )
    parser.add_argument("--images", default="data/images/",
                        help="Directory with rendered PNG images")
    parser.add_argument("--features", default="data/features_all.json",
                        help="Feature JSON for context")
    parser.add_argument("--output", default="data/patterns.json",
                        help="Output patterns JSON")
    parser.add_argument("--model", default="mlx-community/llava-v1.6-mistral-7b-4bit",
                        help="MLX VLM model name")
    parser.add_argument("--max-persons", type=int, default=10,
                        help="Max people to analyze")
    args = parser.parse_args()

    discover_patterns(
        args.images, args.features, args.output,
        model_name=args.model, max_persons=args.max_persons,
    )


if __name__ == "__main__":
    main()
