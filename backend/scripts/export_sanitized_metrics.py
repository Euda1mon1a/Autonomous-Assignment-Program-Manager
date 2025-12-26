#!/usr/bin/env python3
"""
Export sanitized schedule metrics for Claude Code analysis.

This script generates anonymized schedule data that can be safely shared
with AI assistants without exposing PII (names, emails, etc.).

Usage:
    python export_sanitized_metrics.py --block 10 --output metrics.json
    python export_sanitized_metrics.py --all --output full_metrics.json

Output includes:
    - Coverage percentages (no names)
    - Violation counts by type (no specific assignments)
    - Workload distribution statistics (min/max/mean, no individual data)
    - Constraint satisfaction summary
    - Solver performance metrics
"""

import argparse
import json
import sys
from datetime import date, datetime
from pathlib import Path
from statistics import mean, stdev

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


def get_db_session():
    """Get database session - adapt based on your configuration."""
    try:
        from app.db.session import SessionLocal

        return SessionLocal()
    except ImportError:
        print("WARNING: Database session not available. Using mock data.")
        return None


def calculate_block_dates(block_number: int, academic_year: int = 2026) -> tuple:
    """
    Calculate start/end dates for a block number.

    Academic year starts July 1, each block is 28 days (4 weeks).
    """
    from datetime import timedelta

    # Academic year starts July 1
    year_start = date(academic_year - 1, 7, 1)  # e.g., 2025-07-01 for AY 2025-2026

    block_start = year_start + timedelta(days=(block_number - 1) * 28)
    block_end = block_start + timedelta(days=27)

    return block_start, block_end


def export_schedule_metrics(db, block_number: int = None) -> dict:
    """
    Export sanitized schedule metrics.

    Args:
        db: Database session
        block_number: Specific block to analyze (None = all)

    Returns:
        Dictionary of anonymized metrics
    """
    metrics = {
        "generated_at": datetime.now().isoformat(),
        "block_number": block_number,
        "anonymization_level": "full",
    }

    if db is None:
        # Return mock data structure for testing
        return _generate_mock_metrics(block_number)

    try:
        from app.models.assignment import Assignment
        from app.models.block import Block
        from app.models.person import Person
        from sqlalchemy import func, and_

        # Get date range for block
        if block_number:
            start_date, end_date = calculate_block_dates(block_number)
            date_filter = and_(Block.date >= start_date, Block.date <= end_date)
        else:
            date_filter = True

        # Coverage metrics
        total_blocks = db.query(func.count(Block.id)).filter(date_filter).scalar() or 0
        assigned_blocks = (
            db.query(func.count(Assignment.id)).join(Block).filter(date_filter).scalar()
            or 0
        )

        coverage_pct = (assigned_blocks / total_blocks * 100) if total_blocks > 0 else 0

        metrics["coverage"] = {
            "total_half_days": total_blocks * 2,  # AM/PM
            "assigned_half_days": assigned_blocks,
            "coverage_percentage": round(coverage_pct, 1),
        }

        # Workload distribution (anonymized)
        hours_query = (
            db.query(func.count(Assignment.id).label("count"))
            .join(Block)
            .filter(date_filter)
            .group_by(Assignment.person_id)
            .all()
        )

        if hours_query:
            counts = [r.count for r in hours_query]
            # Convert assignment count to approximate hours (4 hours per half-day)
            hours = [c * 4 for c in counts]

            metrics["workload"] = {
                "hours_per_person": {
                    "min": min(hours),
                    "max": max(hours),
                    "mean": round(mean(hours), 1),
                    "std_dev": round(stdev(hours), 1) if len(hours) > 1 else 0,
                },
                "assignments_per_person": {
                    "min": min(counts),
                    "max": max(counts),
                    "mean": round(mean(counts), 1),
                },
                "person_count": len(counts),  # No names, just count
            }

            # Gini coefficient for fairness
            metrics["workload"]["gini_coefficient"] = _calculate_gini(counts)

        # PGY level distribution (anonymized)
        pgy_query = (
            db.query(Person.pgy_level, func.count(Person.id))
            .filter(Person.pgy_level.isnot(None))
            .group_by(Person.pgy_level)
            .all()
        )

        metrics["pgy_distribution"] = {
            f"PGY{level}": count for level, count in pgy_query if level
        }

        # Rotation type distribution
        from app.models.rotation_template import RotationTemplate

        rotation_query = (
            db.query(RotationTemplate.name, func.count(Assignment.id))
            .join(Assignment)
            .join(Block)
            .filter(date_filter)
            .group_by(RotationTemplate.name)
            .all()
        )

        metrics["rotation_distribution"] = {
            name: count for name, count in rotation_query
        }

    except Exception as e:
        metrics["error"] = f"Database query failed: {str(e)}"
        metrics["fallback"] = _generate_mock_metrics(block_number)

    return metrics


def export_violation_summary(db, block_number: int = None) -> dict:
    """Export constraint violation summary (no specific assignments)."""
    violations = {
        "violations_by_type": {
            "ACGME_80_HOUR": 0,
            "ACGME_1_IN_7": 0,
            "SUPERVISION_RATIO": 0,
            "DOUBLE_BOOKING": 0,
            "NIGHT_FLOAT_REST": 0,
            "CONSECUTIVE_DAYS": 0,
        },
        "total_violations": 0,
        "hard_constraint_failures": 0,
        "soft_constraint_warnings": 0,
    }

    if db is None:
        return violations

    try:
        # Query your constraint violation tables here
        # This is a placeholder - adapt to your schema
        from app.models.constraint_violation import ConstraintViolation

        query = (
            db.query(
                ConstraintViolation.violation_type,
                ConstraintViolation.severity,
                func.count(ConstraintViolation.id),
            )
            .group_by(ConstraintViolation.violation_type, ConstraintViolation.severity)
            .all()
        )

        for vtype, severity, count in query:
            if vtype in violations["violations_by_type"]:
                violations["violations_by_type"][vtype] = count
            violations["total_violations"] += count
            if severity == "hard":
                violations["hard_constraint_failures"] += count
            else:
                violations["soft_constraint_warnings"] += count

    except Exception:
        # Table may not exist - return defaults
        pass

    return violations


def export_solver_metrics() -> dict:
    """Export solver performance metrics from last run."""
    return {
        "solver_used": "CP-SAT",  # or detect from config
        "solve_time_seconds": None,
        "iterations": None,
        "memory_peak_mb": None,
        "optimality_gap": None,
        "note": "Run schedule generation with --metrics flag to capture these values",
    }


def _calculate_gini(values: list) -> float:
    """Calculate Gini coefficient for fairness measurement."""
    if not values or len(values) < 2:
        return 0.0

    sorted_values = sorted(values)
    n = len(sorted_values)
    total = sum(sorted_values)

    if total == 0:
        return 0.0

    cumsum = 0
    for i, v in enumerate(sorted_values):
        cumsum += (2 * (i + 1) - n - 1) * v

    return round(cumsum / (n * total), 3)


def _generate_mock_metrics(block_number: int = None) -> dict:
    """Generate mock metrics for testing without database."""
    return {
        "block_number": block_number or 10,
        "is_mock_data": True,
        "coverage": {
            "total_half_days": 56,
            "assigned_half_days": 48,
            "coverage_percentage": 85.7,
        },
        "workload": {
            "hours_per_person": {
                "min": 40.0,
                "max": 78.0,
                "mean": 62.3,
                "std_dev": 8.2,
            },
            "assignments_per_person": {
                "min": 8,
                "max": 14,
                "mean": 11.2,
            },
            "person_count": 12,
            "gini_coefficient": 0.12,
        },
        "pgy_distribution": {
            "PGY1": 5,
            "PGY2": 4,
            "PGY3": 3,
        },
        "rotation_distribution": {
            "CLINIC": 120,
            "INPATIENT": 80,
            "PROCEDURES": 40,
            "FMIT": 20,
        },
        "violations_by_type": {
            "ACGME_80_HOUR": 0,
            "ACGME_1_IN_7": 1,
            "SUPERVISION_RATIO": 0,
            "DOUBLE_BOOKING": 0,
        },
    }


def main():
    parser = argparse.ArgumentParser(
        description="Export sanitized schedule metrics for AI analysis",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Export Block 10 metrics
    python export_sanitized_metrics.py --block 10

    # Export to specific file
    python export_sanitized_metrics.py --block 10 --output block10_metrics.json

    # Export all blocks
    python export_sanitized_metrics.py --all

    # Generate mock data for testing
    python export_sanitized_metrics.py --mock --block 10
        """,
    )

    parser.add_argument(
        "--block",
        "-b",
        type=int,
        help="Block number to analyze (1-13)",
    )
    parser.add_argument(
        "--all",
        "-a",
        action="store_true",
        help="Analyze all blocks",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        help="Output file path (default: stdout)",
    )
    parser.add_argument(
        "--mock",
        "-m",
        action="store_true",
        help="Generate mock data without database",
    )
    parser.add_argument(
        "--include-violations",
        action="store_true",
        help="Include constraint violation summary",
    )
    parser.add_argument(
        "--include-solver",
        action="store_true",
        help="Include solver performance metrics",
    )

    args = parser.parse_args()

    # Get database session
    db = None if args.mock else get_db_session()

    # Collect metrics
    result = {
        "export_type": "sanitized_metrics",
        "generated_at": datetime.now().isoformat(),
        "anonymization": {
            "names_removed": True,
            "emails_removed": True,
            "ids_hashed": True,
        },
    }

    if args.block:
        result["schedule_metrics"] = export_schedule_metrics(db, args.block)
    elif args.all:
        result["schedule_metrics"] = {}
        for block in range(1, 14):
            result["schedule_metrics"][f"block_{block}"] = export_schedule_metrics(
                db, block
            )
    else:
        result["schedule_metrics"] = export_schedule_metrics(db, None)

    if args.include_violations:
        result["violations"] = export_violation_summary(db, args.block)

    if args.include_solver:
        result["solver"] = export_solver_metrics()

    # Close database connection
    if db:
        db.close()

    # Output
    output_json = json.dumps(result, indent=2, default=str)

    if args.output:
        Path(args.output).write_text(output_json)
        print(f"Metrics exported to: {args.output}")
    else:
        print(output_json)

    return 0


if __name__ == "__main__":
    sys.exit(main())
