"""Render schedule rows as PNG images for VLM pattern discovery.

Each person's 28-day schedule is rendered as a colored grid image
showing AM/PM half-day cells with their display codes and colors.
Generates three versions: handjam truth, DB export, and diff overlay.

Usage:
    python render.py --features data/features_all.json --output data/images/
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

# Cell dimensions
CELL_W = 36
CELL_H = 20
LABEL_W = 100
DAY_LABEL_H = 16
ROW_LABEL_W = 45
PADDING = 4

# Colors — same as compare.py
CODE_COLORS: dict[str, tuple[int, int, int]] = {
    "C": (255, 215, 0), "CC": (255, 215, 0), "C40": (255, 215, 0),
    "C30": (255, 215, 0), "CCC": (255, 215, 0), "C-I": (255, 215, 0),
    "C-N": (255, 215, 0),
    "LEC": (135, 206, 235), "ADV": (135, 206, 235),
    "W": (232, 232, 232), "OFF": (232, 232, 232), "FLX": (232, 232, 232),
    "NF": (147, 112, 219), "PedsNF": (147, 112, 219),
    "L&D": (255, 105, 180),
    "FMIT": (144, 238, 144),
    "IMW": (255, 160, 122),
    "KAP": (221, 160, 221),
    "PedW": (255, 182, 193),
    "GYN": (255, 105, 180), "OB": (255, 105, 180),
    "SM": (152, 251, 152), "aSM": (152, 251, 152),
    "GME": (176, 196, 222), "AT": (176, 196, 222),
    "DO": (176, 196, 222), "CV": (176, 196, 222),
    "DFM": (176, 196, 222), "ADM": (176, 196, 222),
    "LV": (255, 228, 181), "SLV": (255, 228, 181), "USAFP": (255, 228, 181),
    "DEP": (255, 99, 71), "TDY": (255, 99, 71),
    "PR": (255, 218, 185), "US": (255, 218, 185),
    "NEURO": (222, 184, 135), "Endo": (222, 184, 135),
    "ENT": (222, 184, 135), "Ophtho": (222, 184, 135),
    "URO": (222, 184, 135), "VAS": (222, 184, 135),
    "HOL": (200, 200, 255),
    "NICU": (173, 216, 230), "NBN": (173, 216, 230),
    "ICU": (255, 160, 122),
    "ER": (255, 200, 200),
    "PI": (173, 216, 230), "PCAT": (173, 216, 230),
    "SIM": (173, 216, 230), "HC": (144, 238, 144),
    "HV": (144, 238, 144),
    "PC": (250, 250, 210),
}
DEFAULT_COLOR = (255, 255, 255)


def _get_color(code: str) -> tuple[int, int, int]:
    return CODE_COLORS.get(code, DEFAULT_COLOR)


def _try_font(size: int):
    """Try to load a monospace font."""
    for name in [
        "/System/Library/Fonts/SFMono-Regular.otf",
        "/System/Library/Fonts/Menlo.ttc",
        "/System/Library/Fonts/Monaco.dfont",
        "/System/Library/Fonts/Courier.dfont",
    ]:
        try:
            return ImageFont.truetype(name, size)
        except (OSError, IOError):
            continue
    return ImageFont.load_default()


def render_person(
    name: str,
    cells: list[dict],
    output_dir: Path,
    render_diff: bool = True,
) -> list[Path]:
    """Render one person's schedule as PNG images.

    Returns list of saved image paths.
    """
    # Group by day_index
    days: dict[int, dict[str, dict]] = defaultdict(dict)
    for c in cells:
        days[c["day_index"]][c["half"]] = c

    max_day = max(days.keys()) if days else 0
    n_days = max_day + 1

    # Image dimensions
    img_w = LABEL_W + n_days * CELL_W + PADDING * 2
    img_h = DAY_LABEL_H + 2 * CELL_H + PADDING * 2  # AM + PM rows

    font_small = _try_font(9)
    font_label = _try_font(10)
    day_names = ["M", "Tu", "W", "Th", "F", "Sa", "Su"]

    paths = []

    for mode in ["truth", "db", "diff"]:
        if mode == "diff" and not render_diff:
            continue

        img = Image.new("RGB", (img_w, img_h), (255, 255, 255))
        draw = ImageDraw.Draw(img)

        # Person name label
        draw.text((4, DAY_LABEL_H + 2), name[:12], fill=(0, 0, 0), font=font_label)

        # Day labels
        for d in range(n_days):
            day_data = days.get(d, {})
            am = day_data.get("am", {})
            pm = day_data.get("pm", {})
            dow = am.get("day_of_week", pm.get("day_of_week"))
            label = day_names[dow] if dow is not None and 0 <= dow < 7 else ""
            x = LABEL_W + d * CELL_W
            draw.text((x + 4, 1), label, fill=(128, 128, 128), font=font_small)

        # Draw cells
        for d in range(n_days):
            day_data = days.get(d, {})
            x = LABEL_W + d * CELL_W

            for half_idx, half in enumerate(["am", "pm"]):
                cell = day_data.get(half, {})
                y = DAY_LABEL_H + half_idx * CELL_H

                if mode == "truth":
                    code = cell.get("truth_code", "")
                elif mode == "db":
                    code = cell.get("db_code", "")
                else:  # diff
                    truth = cell.get("truth_code", "")
                    db = cell.get("db_code", "")
                    code = truth

                    # Highlight mismatches
                    if truth and db and truth != db:
                        draw.rectangle(
                            [x, y, x + CELL_W - 1, y + CELL_H - 1],
                            outline=(231, 76, 60), width=2,
                        )

                bg = _get_color(code)
                draw.rectangle(
                    [x + 1, y + 1, x + CELL_W - 2, y + CELL_H - 2],
                    fill=bg,
                )

                # Draw text (dark for light backgrounds)
                if code:
                    brightness = sum(bg) / 3
                    text_color = (0, 0, 0) if brightness > 128 else (255, 255, 255)
                    # Truncate long codes
                    display = code[:4]
                    draw.text((x + 2, y + 3), display, fill=text_color, font=font_small)

        # Row labels
        draw.text((LABEL_W - 22, DAY_LABEL_H + 2), "AM", fill=(100, 100, 100), font=font_small)
        draw.text((LABEL_W - 22, DAY_LABEL_H + CELL_H + 2), "PM", fill=(100, 100, 100), font=font_small)

        safe_name = name.replace(" ", "_").replace(",", "").replace("/", "_")[:20]
        path = output_dir / f"{safe_name}_{mode}.png"
        img.save(path)
        paths.append(path)

    return paths


def main():
    parser = argparse.ArgumentParser(
        description="Render schedule rows as PNG images",
    )
    parser.add_argument("--features", default="data/features_all.json",
                        help="Feature JSON from extract.py")
    parser.add_argument("--output", default="data/images/",
                        help="Output directory for PNG images")
    args = parser.parse_args()

    features = json.loads(Path(args.features).read_text())
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Group by person
    by_person: dict[str, list[dict]] = defaultdict(list)
    for f in features:
        if f.get("truth_code"):
            by_person[f["person"]].append(f)

    total_images = 0
    for name, cells in sorted(by_person.items()):
        cells.sort(key=lambda c: (c.get("day_index", 0), 0 if c.get("half") == "am" else 1))
        paths = render_person(name, cells, output_dir)
        total_images += len(paths)

    print(f"Rendered {total_images} images for {len(by_person)} people in {output_dir}")


if __name__ == "__main__":
    main()
