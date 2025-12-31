#!/usr/bin/env python3
"""
Performance Metrics Collector

Collects performance metrics from various sources:
- Benchmark results
- Application logs
- Database performance stats
- System resource usage

Stores metrics in time-series format for trending and analysis.

Usage:
    python collect_metrics.py
    python collect_metrics.py --output metrics.json
    python collect_metrics.py --continuous --interval 300  # Every 5 minutes
"""

import argparse
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import psutil


def collect_system_metrics() -> dict[str, Any]:
    """Collect system resource metrics."""
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage("/")

    return {
        "timestamp": datetime.now().isoformat(),
        "cpu_percent": cpu_percent,
        "cpu_count": psutil.cpu_count(),
        "memory_total_gb": memory.total / (1024**3),
        "memory_available_gb": memory.available / (1024**3),
        "memory_used_gb": memory.used / (1024**3),
        "memory_percent": memory.percent,
        "disk_total_gb": disk.total / (1024**3),
        "disk_used_gb": disk.used / (1024**3),
        "disk_percent": disk.percent,
    }


def collect_database_metrics() -> dict[str, Any]:
    """Collect database performance metrics."""
    try:
        from sqlalchemy import create_engine, text

        # Add backend to path
        import sys

        sys.path.insert(0, str(Path(__file__).parent.parent.parent / "backend"))

        from app.core.config import settings

        engine = create_engine(settings.DATABASE_URL)

        with engine.connect() as conn:
            # Get database size
            size_result = conn.execute(
                text(
                    "SELECT pg_database_size(current_database()) as size"
                )
            ).fetchone()

            # Get connection count
            conn_result = conn.execute(
                text(
                    "SELECT count(*) as count FROM pg_stat_activity "
                    "WHERE datname = current_database()"
                )
            ).fetchone()

            # Get table sizes
            table_result = conn.execute(
                text(
                    """
                    SELECT
                        schemaname,
                        tablename,
                        pg_total_relation_size(schemaname||'.'||tablename) as size
                    FROM pg_tables
                    WHERE schemaname = 'public'
                    ORDER BY size DESC
                    LIMIT 10
                    """
                )
            ).fetchall()

        engine.dispose()

        return {
            "timestamp": datetime.now().isoformat(),
            "database_size_mb": size_result[0] / (1024 * 1024) if size_result else 0,
            "active_connections": conn_result[0] if conn_result else 0,
            "largest_tables": [
                {
                    "schema": row[0],
                    "table": row[1],
                    "size_mb": row[2] / (1024 * 1024),
                }
                for row in table_result
            ],
        }

    except Exception as e:
        return {
            "timestamp": datetime.now().isoformat(),
            "error": str(e),
        }


def collect_benchmark_metrics(benchmark_dir: Path) -> dict[str, Any]:
    """Collect latest benchmark results."""
    if not benchmark_dir.exists():
        return {"error": "Benchmark directory not found"}

    # Find most recent benchmark results
    json_files = list(benchmark_dir.glob("*.json"))

    if not json_files:
        return {"error": "No benchmark results found"}

    # Group by benchmark name and get latest for each
    benchmarks = {}
    for file in json_files:
        try:
            with open(file) as f:
                data = json.load(f)
                name = data.get("benchmark_name", "unknown")

                # Keep only the latest for each benchmark
                if name not in benchmarks or file.stat().st_mtime > benchmarks[name]["mtime"]:
                    benchmarks[name] = {
                        "data": data,
                        "mtime": file.stat().st_mtime,
                    }
        except Exception:
            continue

    return {
        "timestamp": datetime.now().isoformat(),
        "benchmarks": {
            name: info["data"] for name, info in benchmarks.items()
        },
        "total_benchmarks": len(benchmarks),
    }


def collect_all_metrics(benchmark_dir: Path) -> dict[str, Any]:
    """Collect all performance metrics."""
    print("Collecting performance metrics...")

    metrics = {
        "collection_time": datetime.now().isoformat(),
        "system": collect_system_metrics(),
        "database": collect_database_metrics(),
        "benchmarks": collect_benchmark_metrics(benchmark_dir),
    }

    print("✓ Metrics collected successfully")
    return metrics


def save_metrics(metrics: dict[str, Any], output_file: Path):
    """Save metrics to JSON file."""
    output_file.parent.mkdir(parents=True, exist_ok=True)

    # If file exists, append to array
    if output_file.exists():
        with open(output_file) as f:
            existing = json.load(f)
            if isinstance(existing, list):
                existing.append(metrics)
                metrics_to_save = existing
            else:
                metrics_to_save = [existing, metrics]
    else:
        metrics_to_save = [metrics]

    with open(output_file, "w") as f:
        json.dump(metrics_to_save, f, indent=2)

    print(f"✓ Metrics saved to {output_file}")


def continuous_collection(interval: int, output_file: Path, benchmark_dir: Path):
    """Continuously collect metrics at specified interval."""
    print(f"Starting continuous metrics collection (interval: {interval}s)")
    print(f"Output: {output_file}")
    print("Press Ctrl+C to stop")
    print()

    try:
        while True:
            metrics = collect_all_metrics(benchmark_dir)
            save_metrics(metrics, output_file)

            print(f"Next collection in {interval} seconds...")
            time.sleep(interval)

    except KeyboardInterrupt:
        print("\n\nStopped metrics collection")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Collect performance metrics")

    parser.add_argument(
        "--output",
        type=Path,
        default=Path("metrics/performance_metrics.json"),
        help="Output JSON file",
    )

    parser.add_argument(
        "--benchmark-dir",
        type=Path,
        default=Path("benchmark_results"),
        help="Directory containing benchmark results",
    )

    parser.add_argument(
        "--continuous",
        action="store_true",
        help="Continuously collect metrics",
    )

    parser.add_argument(
        "--interval",
        type=int,
        default=300,
        help="Collection interval in seconds (default: 300 = 5 minutes)",
    )

    parser.add_argument(
        "--print",
        action="store_true",
        help="Print metrics to stdout instead of saving",
    )

    args = parser.parse_args()

    if args.continuous:
        continuous_collection(args.interval, args.output, args.benchmark_dir)
    else:
        metrics = collect_all_metrics(args.benchmark_dir)

        if args.print:
            print(json.dumps(metrics, indent=2))
        else:
            save_metrics(metrics, args.output)


if __name__ == "__main__":
    main()
