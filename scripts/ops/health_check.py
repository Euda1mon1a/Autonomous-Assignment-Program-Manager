#!/usr/bin/env python3
"""
System health verification script.

Performs comprehensive health checks:
- Database connectivity and performance
- Redis connectivity
- Celery worker status
- Disk space
- Memory usage
- API endpoint health

Usage:
    python scripts/ops/health_check.py
    python scripts/ops/health_check.py --format json
    python scripts/ops/health_check.py --critical-only
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "backend"))

from app.health.aggregator import HealthAggregator


def check_disk_space() -> Dict[str, Any]:
    """Check available disk space."""
    import shutil

    try:
        usage = shutil.disk_usage("/")
        percent_used = (usage.used / usage.total) * 100

        status = "healthy"
        if percent_used > 90:
            status = "critical"
        elif percent_used > 80:
            status = "warning"

        return {
            "status": status,
            "total_gb": round(usage.total / (1024 ** 3), 2),
            "used_gb": round(usage.used / (1024 ** 3), 2),
            "free_gb": round(usage.free / (1024 ** 3), 2),
            "percent_used": round(percent_used, 2),
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
        }


def check_memory() -> Dict[str, Any]:
    """Check memory usage."""
    try:
        import psutil

        memory = psutil.virtual_memory()

        status = "healthy"
        if memory.percent > 90:
            status = "critical"
        elif memory.percent > 80:
            status = "warning"

        return {
            "status": status,
            "total_gb": round(memory.total / (1024 ** 3), 2),
            "used_gb": round(memory.used / (1024 ** 3), 2),
            "available_gb": round(memory.available / (1024 ** 3), 2),
            "percent_used": memory.percent,
        }
    except ImportError:
        return {
            "status": "warning",
            "message": "psutil not installed - cannot check memory",
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
        }


def run_health_checks(critical_only: bool = False) -> Dict[str, Any]:
    """Run all health checks."""
    results = {
        "timestamp": datetime.now().isoformat(),
        "overall_status": "healthy",
        "checks": {},
    }

    # Application health checks
    aggregator = HealthAggregator()
    app_health = aggregator.check_health()

    results["checks"]["application"] = {
        "status": app_health.status,
        "checks": {
            name: {
                "status": check.status,
                "message": check.message,
                "details": check.details,
            }
            for name, check in app_health.checks.items()
        },
    }

    # System health checks
    if not critical_only:
        results["checks"]["disk"] = check_disk_space()
        results["checks"]["memory"] = check_memory()

    # Determine overall status
    statuses = []

    def collect_statuses(data: Any) -> None:
        if isinstance(data, dict):
            if "status" in data:
                statuses.append(data["status"])
            for value in data.values():
                collect_statuses(value)

    collect_statuses(results["checks"])

    if "critical" in statuses or "error" in statuses:
        results["overall_status"] = "critical"
    elif "warning" in statuses:
        results["overall_status"] = "warning"
    elif "degraded" in statuses:
        results["overall_status"] = "degraded"

    return results


def print_results_table(results: Dict[str, Any]) -> None:
    """Print results in table format."""
    overall = results["overall_status"].upper()
    symbol = "✓" if overall == "HEALTHY" else "✗"

    print("=" * 70)
    print(f"System Health Check - {symbol} {overall}")
    print(f"Timestamp: {results['timestamp']}")
    print("=" * 70)

    def print_check(name: str, data: Dict[str, Any], indent: int = 0) -> None:
        prefix = "  " * indent
        status = data.get("status", "unknown").upper()
        symbol = "✓" if status == "HEALTHY" else "✗"

        print(f"{prefix}{symbol} {name}: {status}")

        if "message" in data and data["message"]:
            print(f"{prefix}  Message: {data['message']}")

        if "details" in data and data["details"]:
            for key, value in data["details"].items():
                print(f"{prefix}  {key}: {value}")

        if "checks" in data:
            for check_name, check_data in data["checks"].items():
                print_check(check_name, check_data, indent + 1)

    for check_name, check_data in results["checks"].items():
        print(f"\n{check_name.upper()}")
        print("-" * 70)
        print_check(check_name, check_data)

    print("\n" + "=" * 70)


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="System health verification script"
    )
    parser.add_argument(
        "--format",
        choices=["table", "json"],
        default="table",
        help="Output format",
    )
    parser.add_argument(
        "--critical-only",
        action="store_true",
        help="Only run critical checks (faster)",
    )
    parser.add_argument(
        "--output",
        type=str,
        help="Save results to file",
    )

    args = parser.parse_args()

    try:
        # Run health checks
        results = run_health_checks(critical_only=args.critical_only)

        # Output results
        if args.format == "json":
            output = json.dumps(results, indent=2)
            print(output)

            if args.output:
                with open(args.output, "w") as f:
                    f.write(output)
        else:
            print_results_table(results)

            if args.output:
                # Save JSON to file even in table mode
                with open(args.output, "w") as f:
                    json.dump(results, f, indent=2)

        # Exit with appropriate code
        if results["overall_status"] in ["critical", "error"]:
            return 1
        elif results["overall_status"] in ["warning", "degraded"]:
            return 2
        else:
            return 0

    except KeyboardInterrupt:
        print("\nAborted by user")
        return 130

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
