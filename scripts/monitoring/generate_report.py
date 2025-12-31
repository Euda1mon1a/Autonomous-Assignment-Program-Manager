#!/usr/bin/env python3
"""
Performance Report Generator

Generates human-readable performance reports from collected metrics and benchmarks.

Output formats:
- Text report
- HTML report
- Markdown report
- JSON summary

Usage:
    python generate_report.py
    python generate_report.py --format html --output report.html
    python generate_report.py --metrics metrics/performance_metrics.json
"""

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any


def generate_text_report(metrics: dict[str, Any]) -> str:
    """Generate text-formatted report."""
    lines = []

    lines.append("=" * 80)
    lines.append("PERFORMANCE REPORT")
    lines.append("=" * 80)
    lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")

    # System metrics
    if "system" in metrics:
        lines.append("SYSTEM METRICS")
        lines.append("-" * 80)
        sys = metrics["system"]
        lines.append(f"CPU Usage:        {sys.get('cpu_percent', 0):.1f}%")
        lines.append(f"CPU Cores:        {sys.get('cpu_count', 0)}")
        lines.append(f"Memory Usage:     {sys.get('memory_percent', 0):.1f}%")
        lines.append(
            f"Memory Used:      {sys.get('memory_used_gb', 0):.2f} GB / "
            f"{sys.get('memory_total_gb', 0):.2f} GB"
        )
        lines.append(f"Disk Usage:       {sys.get('disk_percent', 0):.1f}%")
        lines.append("")

    # Database metrics
    if "database" in metrics and "error" not in metrics["database"]:
        lines.append("DATABASE METRICS")
        lines.append("-" * 80)
        db = metrics["database"]
        lines.append(f"Database Size:    {db.get('database_size_mb', 0):.2f} MB")
        lines.append(f"Active Connections: {db.get('active_connections', 0)}")

        if "largest_tables" in db and db["largest_tables"]:
            lines.append("\nLargest Tables:")
            for table in db["largest_tables"][:5]:
                lines.append(f"  {table['table']:30s} {table['size_mb']:8.2f} MB")
        lines.append("")

    # Benchmark metrics
    if "benchmarks" in metrics and "benchmarks" in metrics["benchmarks"]:
        lines.append("BENCHMARK RESULTS")
        lines.append("-" * 80)

        benchmarks = metrics["benchmarks"]["benchmarks"]

        # Group by category
        by_category = {}
        for name, data in benchmarks.items():
            category = data.get("category", "unknown")
            if category not in by_category:
                by_category[category] = []
            by_category[category].append((name, data))

        for category, items in sorted(by_category.items()):
            lines.append(f"\n{category.upper()}:")
            for name, data in items:
                lines.append(f"  {name[:50]:50s}")
                lines.append(f"    Avg Duration:  {data.get('avg_duration', 0):.3f}s")

                if data.get("throughput"):
                    lines.append(f"    Throughput:    {data.get('throughput', 0):.2f} ops/sec")

                if data.get("memory_mb"):
                    lines.append(f"    Memory:        {data.get('memory_mb', 0):.1f} MB")

        lines.append("")

    lines.append("=" * 80)

    return "\n".join(lines)


def generate_markdown_report(metrics: dict[str, Any]) -> str:
    """Generate Markdown-formatted report."""
    lines = []

    lines.append("# Performance Report")
    lines.append(f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")
    lines.append("")

    # System metrics
    if "system" in metrics:
        lines.append("## System Metrics")
        lines.append("")
        sys = metrics["system"]
        lines.append(f"- **CPU Usage**: {sys.get('cpu_percent', 0):.1f}%")
        lines.append(f"- **Memory Usage**: {sys.get('memory_percent', 0):.1f}%")
        lines.append(f"- **Disk Usage**: {sys.get('disk_percent', 0):.1f}%")
        lines.append("")

    # Database metrics
    if "database" in metrics and "error" not in metrics["database"]:
        lines.append("## Database Metrics")
        lines.append("")
        db = metrics["database"]
        lines.append(f"- **Database Size**: {db.get('database_size_mb', 0):.2f} MB")
        lines.append(f"- **Active Connections**: {db.get('active_connections', 0)}")
        lines.append("")

    # Benchmark results
    if "benchmarks" in metrics and "benchmarks" in metrics["benchmarks"]:
        lines.append("## Benchmark Results")
        lines.append("")

        benchmarks = metrics["benchmarks"]["benchmarks"]

        # Create table
        lines.append("| Benchmark | Avg Duration | Throughput | Memory |")
        lines.append("|-----------|--------------|------------|--------|")

        for name, data in sorted(benchmarks.items()):
            throughput = f"{data.get('throughput', 0):.2f} ops/s" if data.get("throughput") else "N/A"
            memory = f"{data.get('memory_mb', 0):.1f} MB" if data.get("memory_mb") else "N/A"

            lines.append(
                f"| {name[:40]} | {data.get('avg_duration', 0):.3f}s | {throughput} | {memory} |"
            )

        lines.append("")

    return "\n".join(lines)


def generate_html_report(metrics: dict[str, Any]) -> str:
    """Generate HTML-formatted report."""
    html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Performance Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        h1 {{ color: #333; }}
        h2 {{ color: #666; margin-top: 30px; }}
        table {{ border-collapse: collapse; width: 100%; margin-top: 20px; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background-color: #f2f2f2; }}
        .metric {{ margin: 10px 0; }}
        .good {{ color: green; }}
        .warning {{ color: orange; }}
        .bad {{ color: red; }}
    </style>
</head>
<body>
    <h1>Performance Report</h1>
    <p><em>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</em></p>

    <h2>System Metrics</h2>
"""

    if "system" in metrics:
        sys = metrics["system"]
        html += f"""
    <div class="metric">CPU Usage: <strong>{sys.get('cpu_percent', 0):.1f}%</strong></div>
    <div class="metric">Memory Usage: <strong>{sys.get('memory_percent', 0):.1f}%</strong></div>
    <div class="metric">Disk Usage: <strong>{sys.get('disk_percent', 0):.1f}%</strong></div>
"""

    if "benchmarks" in metrics and "benchmarks" in metrics["benchmarks"]:
        html += """
    <h2>Benchmark Results</h2>
    <table>
        <thead>
            <tr>
                <th>Benchmark</th>
                <th>Avg Duration</th>
                <th>Throughput</th>
                <th>Memory</th>
            </tr>
        </thead>
        <tbody>
"""

        benchmarks = metrics["benchmarks"]["benchmarks"]
        for name, data in sorted(benchmarks.items()):
            throughput = f"{data.get('throughput', 0):.2f} ops/s" if data.get("throughput") else "N/A"
            memory = f"{data.get('memory_mb', 0):.1f} MB" if data.get("memory_mb") else "N/A"

            html += f"""
            <tr>
                <td>{name}</td>
                <td>{data.get('avg_duration', 0):.3f}s</td>
                <td>{throughput}</td>
                <td>{memory}</td>
            </tr>
"""

        html += """
        </tbody>
    </table>
"""

    html += """
</body>
</html>
"""

    return html


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Generate performance report")

    parser.add_argument(
        "--metrics",
        type=Path,
        default=Path("metrics/performance_metrics.json"),
        help="Metrics JSON file",
    )

    parser.add_argument(
        "--format",
        type=str,
        default="text",
        choices=["text", "markdown", "html", "json"],
        help="Report format",
    )

    parser.add_argument(
        "--output",
        type=Path,
        help="Output file (default: stdout)",
    )

    args = parser.parse_args()

    # Load metrics
    if not args.metrics.exists():
        print(f"ERROR: Metrics file not found: {args.metrics}")
        return

    with open(args.metrics) as f:
        metrics_data = json.load(f)

    # If metrics is a list, use the latest
    if isinstance(metrics_data, list):
        metrics = metrics_data[-1]
    else:
        metrics = metrics_data

    # Generate report
    if args.format == "text":
        report = generate_text_report(metrics)
    elif args.format == "markdown":
        report = generate_markdown_report(metrics)
    elif args.format == "html":
        report = generate_html_report(metrics)
    else:  # json
        report = json.dumps(metrics, indent=2)

    # Output
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(report)
        print(f"✓ Report saved to {args.output}")
    else:
        print(report)


if __name__ == "__main__":
    main()
