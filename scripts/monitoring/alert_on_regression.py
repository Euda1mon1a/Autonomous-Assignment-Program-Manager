#!/usr/bin/env python3
"""
Performance Regression Alerting

Monitors benchmark results and alerts on performance regressions.
Can be integrated into CI/CD pipelines to fail builds on regressions.

Alert mechanisms:
- Exit code (for CI/CD)
- Console output
- Slack webhook (optional)
- Email (optional)

Usage:
    python alert_on_regression.py --baseline results/baseline.json --current results/current.json
    python alert_on_regression.py --dir benchmark_results/ --threshold 15
    python alert_on_regression.py --ci  # Exit with code 1 on regression
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any


class RegressionDetector:
    """Detect performance regressions."""

    def __init__(self, threshold_percent: float = 10.0):
        """
        Initialize detector.

        Args:
            threshold_percent: Percentage slowdown that constitutes a regression
        """
        self.threshold = threshold_percent
        self.regressions = []
        self.warnings = []

    def check_benchmark(self, baseline: dict[str, Any], current: dict[str, Any]) -> dict[str, Any]:
        """Check a single benchmark for regression."""
        baseline_duration = baseline.get("avg_duration", 0)
        current_duration = current.get("avg_duration", 0)

        if baseline_duration == 0:
            return {"status": "no_baseline"}

        percent_change = ((current_duration - baseline_duration) / baseline_duration) * 100

        result = {
            "benchmark_name": baseline.get("benchmark_name", "unknown"),
            "baseline_duration": baseline_duration,
            "current_duration": current_duration,
            "percent_change": percent_change,
            "status": "ok",
        }

        # Check for regression
        if percent_change > self.threshold:
            result["status"] = "regression"
            result["severity"] = "critical" if percent_change > self.threshold * 2 else "warning"
            self.regressions.append(result)

        # Check memory regression if available
        if baseline.get("memory_mb") and current.get("memory_mb"):
            memory_change = (
                (current["memory_mb"] - baseline["memory_mb"]) / baseline["memory_mb"]
            ) * 100

            if memory_change > self.threshold:
                result["memory_regression"] = True
                result["memory_change_percent"] = memory_change
                self.warnings.append({
                    "type": "memory",
                    "benchmark": result["benchmark_name"],
                    "change": memory_change,
                })

        return result

    def has_regressions(self) -> bool:
        """Check if any regressions were detected."""
        return len(self.regressions) > 0

    def print_report(self):
        """Print regression detection report."""
        print(f"\n{'=' * 80}")
        print("PERFORMANCE REGRESSION REPORT")
        print(f"{'=' * 80}")
        print(f"Threshold: {self.threshold}% slowdown")
        print()

        if not self.regressions and not self.warnings:
            print("✓ No regressions detected")
            return

        if self.regressions:
            print(f"❌ REGRESSIONS DETECTED: {len(self.regressions)}")
            print(f"{'-' * 80}")

            for regression in self.regressions:
                severity_icon = "🔴" if regression["severity"] == "critical" else "⚠️"
                print(f"\n{severity_icon} {regression['benchmark_name']}")
                print(f"   Baseline:  {regression['baseline_duration']:.3f}s")
                print(f"   Current:   {regression['current_duration']:.3f}s")
                print(f"   Change:    {regression['percent_change']:+.1f}%")
                print(f"   Severity:  {regression['severity'].upper()}")

                if regression.get("memory_regression"):
                    print(f"   Memory:    {regression['memory_change_percent']:+.1f}% increase")

        if self.warnings:
            print(f"\n⚠️  WARNINGS: {len(self.warnings)}")
            print(f"{'-' * 80}")

            for warning in self.warnings:
                if warning["type"] == "memory":
                    print(f"   {warning['benchmark']}: Memory increased by {warning['change']:.1f}%")

        print(f"\n{'=' * 80}")


def send_slack_alert(webhook_url: str, detector: RegressionDetector):
    """Send Slack notification about regressions."""
    try:
        import requests

        if not detector.regressions:
            return

        message = {
            "text": f"⚠️ Performance Regression Detected",
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": "🚨 Performance Regression Alert",
                    },
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*{len(detector.regressions)} regression(s) detected*",
                    },
                },
            ],
        }

        for regression in detector.regressions[:5]:  # Limit to 5 for message size
            message["blocks"].append(
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": (
                            f"*{regression['benchmark_name']}*\n"
                            f"• Change: {regression['percent_change']:+.1f}%\n"
                            f"• Duration: {regression['baseline_duration']:.3f}s → "
                            f"{regression['current_duration']:.3f}s"
                        ),
                    },
                }
            )

        response = requests.post(webhook_url, json=message)
        response.raise_for_status()

        print("✓ Slack notification sent")

    except Exception as e:
        print(f"WARNING: Failed to send Slack notification: {e}")


def check_directory(directory: Path, threshold: float) -> RegressionDetector:
    """Check all benchmarks in a directory for regressions."""
    detector = RegressionDetector(threshold_percent=threshold)

    # Find benchmark files
    json_files = sorted(directory.glob("*.json"), key=lambda x: x.stat().st_mtime, reverse=True)

    if len(json_files) < 2:
        print("ERROR: Need at least 2 benchmark files")
        return detector

    # Group by benchmark name
    by_benchmark = {}
    for filepath in json_files:
        try:
            with open(filepath) as f:
                data = json.load(f)
                name = data.get("benchmark_name", "unknown")

                if name not in by_benchmark:
                    by_benchmark[name] = []

                by_benchmark[name].append((filepath, data))
        except Exception:
            continue

    # Check each benchmark (compare latest with previous)
    for benchmark_name, runs in by_benchmark.items():
        if len(runs) < 2:
            continue

        # Sort by modification time
        runs = sorted(runs, key=lambda x: x[0].stat().st_mtime, reverse=True)

        latest = runs[0][1]
        previous = runs[1][1]

        detector.check_benchmark(previous, latest)

    return detector


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Detect performance regressions")

    parser.add_argument(
        "--baseline",
        type=Path,
        help="Baseline benchmark JSON file",
    )

    parser.add_argument(
        "--current",
        type=Path,
        help="Current benchmark JSON file",
    )

    parser.add_argument(
        "--dir",
        type=Path,
        default=Path("benchmark_results"),
        help="Directory containing benchmark results",
    )

    parser.add_argument(
        "--threshold",
        type=float,
        default=10.0,
        help="Regression threshold percentage (default: 10%%)",
    )

    parser.add_argument(
        "--ci",
        action="store_true",
        help="CI mode: Exit with code 1 on regression",
    )

    parser.add_argument(
        "--slack-webhook",
        type=str,
        help="Slack webhook URL for notifications",
    )

    args = parser.parse_args()

    # Detect regressions
    if args.baseline and args.current:
        # Compare two specific files
        detector = RegressionDetector(threshold_percent=args.threshold)

        with open(args.baseline) as f:
            baseline = json.load(f)

        with open(args.current) as f:
            current = json.load(f)

        detector.check_benchmark(baseline, current)
    else:
        # Check directory
        if not args.dir.exists():
            print(f"ERROR: Directory not found: {args.dir}")
            sys.exit(1)

        detector = check_directory(args.dir, args.threshold)

    # Print report
    detector.print_report()

    # Send Slack alert if configured
    if args.slack_webhook and detector.has_regressions():
        send_slack_alert(args.slack_webhook, detector)

    # Exit with appropriate code for CI
    if args.ci and detector.has_regressions():
        print("\n❌ CI FAILURE: Performance regressions detected")
        sys.exit(1)
    elif args.ci:
        print("\n✓ CI SUCCESS: No regressions detected")
        sys.exit(0)


if __name__ == "__main__":
    main()
