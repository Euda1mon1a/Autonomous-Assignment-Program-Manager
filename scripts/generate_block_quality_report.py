#!/usr/bin/env python3
"""
Generate Block Quality Reports.

Usage:
    # Single block
    python scripts/generate_block_quality_report.py --block 10

    # Multiple blocks
    python scripts/generate_block_quality_report.py --blocks 10,11,12,13

    # Range of blocks with summary
    python scripts/generate_block_quality_report.py --blocks 10-13 --summary

    # Custom output directory
    python scripts/generate_block_quality_report.py --block 10 --output /tmp/reports

    # Via Docker
    docker exec scheduler-local-backend python /app/scripts/generate_block_quality_report.py --blocks 10-13 --summary
"""

import argparse
import os
import sys
from datetime import datetime
from pathlib import Path

# Add app to path when running from scripts/
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from app.db.session import SessionLocal
from app.services.block_quality_report_service import BlockQualityReportService


def parse_blocks(blocks_str: str) -> list[int]:
    """Parse block specification string.

    Supports:
    - Single: "10"
    - List: "10,11,12"
    - Range: "10-13"
    - Mixed: "10,12-13"
    """
    blocks = []
    parts = blocks_str.split(",")

    for part in parts:
        part = part.strip()
        if "-" in part:
            # Range
            start, end = part.split("-")
            blocks.extend(range(int(start), int(end) + 1))
        else:
            blocks.append(int(part))

    return sorted(set(blocks))


def main():
    parser = argparse.ArgumentParser(
        description="Generate Block Quality Reports",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    # Block selection (mutually exclusive)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--block",
        type=int,
        help="Single block number",
    )
    group.add_argument(
        "--blocks",
        type=str,
        help="Multiple blocks: 10,11,12 or 10-13",
    )

    parser.add_argument(
        "--year",
        type=int,
        default=None,
        help="Academic year (e.g., 2025 for AY 2025-2026). Auto-detects from current date if not specified.",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="docs/reports",
        help="Output directory (default: docs/reports)",
    )
    parser.add_argument(
        "--summary",
        action="store_true",
        help="Generate cross-block summary (only for multiple blocks)",
    )
    parser.add_argument(
        "--format",
        choices=["markdown", "json"],
        default="markdown",
        help="Output format (default: markdown)",
    )

    args = parser.parse_args()

    # Parse block numbers
    if args.block:
        block_numbers = [args.block]
    else:
        block_numbers = parse_blocks(args.blocks)

    print(f"Generating reports for blocks: {block_numbers}")

    # Create output directory
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Derive academic year from current date if not provided
    if args.year is None:
        today = datetime.now().date()
        args.year = today.year if today.month >= 7 else today.year - 1
        print(f"  Auto-detected academic year: {args.year}")

    # Generate reports
    db = SessionLocal()
    try:
        service = BlockQualityReportService(db)
        date_str = datetime.now().strftime("%Y%m%d")

        for block_num in block_numbers:
            print(f"  Processing Block {block_num}...")

            try:
                report = service.generate_report(block_num, args.year)

                if args.format == "markdown":
                    content = service.to_markdown(report)
                    filename = f"BLOCK_{block_num}_QUALITY_REPORT_{date_str}.md"
                else:
                    content = report.model_dump_json(indent=2)
                    filename = f"BLOCK_{block_num}_QUALITY_REPORT_{date_str}.json"

                filepath = output_dir / filename
                with open(filepath, "w") as f:
                    f.write(content)

                print(f"    -> {filepath}")
                print(f"       Total: {report.executive_summary.total_assignments}")
                print(f"       Status: {report.executive_summary.overall_status}")

            except Exception as e:
                print(f"    ERROR: {e}")
                continue

        # Generate summary if requested and multiple blocks
        if args.summary and len(block_numbers) > 1:
            print(f"  Generating summary for {len(block_numbers)} blocks...")

            summary = service.generate_summary(block_numbers, args.year)

            if args.format == "markdown":
                content = service.summary_to_markdown(summary)
                filename = f"BLOCKS_{min(block_numbers)}-{max(block_numbers)}_SUMMARY_{date_str}.md"
            else:
                content = summary.model_dump_json(indent=2)
                filename = f"BLOCKS_{min(block_numbers)}-{max(block_numbers)}_SUMMARY_{date_str}.json"

            filepath = output_dir / filename
            with open(filepath, "w") as f:
                f.write(content)

            print(f"    -> {filepath}")
            print(f"       Total: {summary.total_assignments}")
            print(f"       Status: {summary.overall_status}")

        print("\nDone!")

    finally:
        db.close()


if __name__ == "__main__":
    main()
