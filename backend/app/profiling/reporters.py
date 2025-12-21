"""
Performance reporters for generating reports and visualizations.

Provides tools for creating flame graphs, performance reports, and summaries.
"""

import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.profiling.analyzers import Bottleneck, PerformanceInsight
from app.profiling.collectors import RequestMetrics, SQLQuery, Trace
from app.profiling.profiler import ProfileResult


@dataclass
class ProfileReport:
    """Comprehensive performance profiling report."""

    report_id: str
    created_at: datetime
    profile_results: List[ProfileResult]
    sql_queries: List[SQLQuery]
    requests: List[RequestMetrics]
    traces: List[Trace]
    bottlenecks: List[Bottleneck]
    insights: List[PerformanceInsight]
    summary: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "report_id": self.report_id,
            "created_at": self.created_at.isoformat(),
            "summary": self.summary,
            "bottlenecks": [b.to_dict() for b in self.bottlenecks],
            "insights": [i.to_dict() for i in self.insights],
            "metadata": self.metadata,
            "counts": {
                "profile_results": len(self.profile_results),
                "sql_queries": len(self.sql_queries),
                "requests": len(self.requests),
                "traces": len(self.traces),
            },
        }


class PerformanceReporter:
    """
    Generates performance reports from profiling data.

    Combines data from various collectors and analyzers to create
    comprehensive reports.
    """

    def __init__(self):
        """Initialize performance reporter."""
        pass

    def generate_report(
        self,
        profile_results: Optional[List[ProfileResult]] = None,
        sql_queries: Optional[List[SQLQuery]] = None,
        requests: Optional[List[RequestMetrics]] = None,
        traces: Optional[List[Trace]] = None,
        bottlenecks: Optional[List[Bottleneck]] = None,
        insights: Optional[List[PerformanceInsight]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ProfileReport:
        """
        Generate a comprehensive performance report.

        Args:
            profile_results: CPU/memory profiling results
            sql_queries: SQL query metrics
            requests: HTTP request metrics
            traces: Distributed traces
            bottlenecks: Detected bottlenecks
            insights: Performance insights
            metadata: Additional metadata

        Returns:
            ProfileReport instance
        """
        from uuid import uuid4

        report_id = str(uuid4())
        created_at = datetime.utcnow()

        # Build summary
        summary = self._build_summary(
            profile_results or [],
            sql_queries or [],
            requests or [],
            traces or [],
        )

        return ProfileReport(
            report_id=report_id,
            created_at=created_at,
            profile_results=profile_results or [],
            sql_queries=sql_queries or [],
            requests=requests or [],
            traces=traces or [],
            bottlenecks=bottlenecks or [],
            insights=insights or [],
            summary=summary,
            metadata=metadata or {},
        )

    def _build_summary(
        self,
        profile_results: List[ProfileResult],
        sql_queries: List[SQLQuery],
        requests: List[RequestMetrics],
        traces: List[Trace],
    ) -> Dict[str, Any]:
        """
        Build summary statistics from profiling data.

        Args:
            profile_results: CPU/memory profiling results
            sql_queries: SQL query metrics
            requests: HTTP request metrics
            traces: Distributed traces

        Returns:
            Summary dictionary
        """
        import statistics

        summary = {}

        # Profile results summary
        if profile_results:
            durations = [r.duration_seconds * 1000 for r in profile_results]
            cpu_percentages = [r.cpu_percent for r in profile_results]
            memory_usage = [r.memory_peak_mb for r in profile_results]

            summary["profiling"] = {
                "total_profiles": len(profile_results),
                "avg_duration_ms": statistics.mean(durations),
                "max_duration_ms": max(durations),
                "avg_cpu_percent": statistics.mean(cpu_percentages),
                "max_cpu_percent": max(cpu_percentages),
                "avg_memory_mb": statistics.mean(memory_usage),
                "max_memory_mb": max(memory_usage),
            }

        # SQL queries summary
        if sql_queries:
            query_durations = [q.duration_ms for q in sql_queries if q.duration_ms]
            failed = [q for q in sql_queries if q.error]

            summary["sql"] = {
                "total_queries": len(sql_queries),
                "avg_duration_ms": (
                    statistics.mean(query_durations) if query_durations else 0
                ),
                "max_duration_ms": max(query_durations) if query_durations else 0,
                "failed_queries": len(failed),
            }

        # Requests summary
        if requests:
            request_durations = [r.duration_ms for r in requests if r.duration_ms]
            failed = [r for r in requests if r.status_code and r.status_code >= 400]

            summary["requests"] = {
                "total_requests": len(requests),
                "avg_duration_ms": (
                    statistics.mean(request_durations) if request_durations else 0
                ),
                "max_duration_ms": max(request_durations) if request_durations else 0,
                "failed_requests": len(failed),
                "error_rate_percent": (
                    len(failed) / len(requests) * 100 if requests else 0
                ),
            }

        # Traces summary
        if traces:
            trace_durations = [t.duration_ms for t in traces if t.duration_ms]

            summary["traces"] = {
                "total_spans": len(traces),
                "avg_duration_ms": (
                    statistics.mean(trace_durations) if trace_durations else 0
                ),
                "max_duration_ms": max(trace_durations) if trace_durations else 0,
            }

        return summary

    def export_to_json(self, report: ProfileReport, pretty: bool = True) -> str:
        """
        Export report to JSON format.

        Args:
            report: Profile report to export
            pretty: Whether to pretty-print JSON

        Returns:
            JSON string
        """
        return json.dumps(report.to_dict(), indent=2 if pretty else None)

    def export_to_html(self, report: ProfileReport) -> str:
        """
        Export report to HTML format.

        Args:
            report: Profile report to export

        Returns:
            HTML string
        """
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Performance Report - {report.report_id}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            line-height: 1.6;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: #f5f5f5;
        }}
        .header {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .section {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        h1 {{ color: #333; margin: 0 0 10px 0; }}
        h2 {{ color: #555; border-bottom: 2px solid #007bff; padding-bottom: 10px; }}
        .metric {{
            display: inline-block;
            margin: 10px 20px 10px 0;
        }}
        .metric-label {{
            font-size: 12px;
            color: #666;
            text-transform: uppercase;
        }}
        .metric-value {{
            font-size: 24px;
            font-weight: bold;
            color: #333;
        }}
        .bottleneck {{
            border-left: 4px solid #dc3545;
            padding: 10px;
            margin: 10px 0;
            background: #fff5f5;
        }}
        .bottleneck.critical {{ border-color: #dc3545; background: #fff5f5; }}
        .bottleneck.high {{ border-color: #fd7e14; background: #fff8f5; }}
        .bottleneck.medium {{ border-color: #ffc107; background: #fffbf0; }}
        .bottleneck.low {{ border-color: #28a745; background: #f0fff4; }}
        .insight {{
            border-left: 4px solid #007bff;
            padding: 10px;
            margin: 10px 0;
            background: #f0f8ff;
        }}
        .recommendation {{
            padding: 5px 10px;
            background: #e9ecef;
            margin: 5px 0;
            border-radius: 4px;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Performance Report</h1>
        <p>Report ID: {report.report_id}</p>
        <p>Generated: {report.created_at.strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
    </div>

    <div class="section">
        <h2>Summary</h2>
        {self._render_summary_html(report.summary)}
    </div>

    {self._render_bottlenecks_html(report.bottlenecks)}

    {self._render_insights_html(report.insights)}

</body>
</html>
"""
        return html

    def _render_summary_html(self, summary: Dict[str, Any]) -> str:
        """Render summary section as HTML."""
        html = ""
        for category, metrics in summary.items():
            html += f"<h3>{category.capitalize()}</h3>"
            for key, value in metrics.items():
                label = key.replace("_", " ").title()
                if isinstance(value, float):
                    formatted_value = f"{value:.2f}"
                else:
                    formatted_value = str(value)
                html += f"""
                <div class="metric">
                    <div class="metric-label">{label}</div>
                    <div class="metric-value">{formatted_value}</div>
                </div>
                """
        return html

    def _render_bottlenecks_html(self, bottlenecks: List[Bottleneck]) -> str:
        """Render bottlenecks section as HTML."""
        if not bottlenecks:
            return ""

        html = '<div class="section"><h2>Bottlenecks</h2>'
        for bottleneck in bottlenecks:
            html += f"""
            <div class="bottleneck {bottleneck.severity}">
                <h3>{bottleneck.description}</h3>
                <p><strong>Type:</strong> {bottleneck.bottleneck_type}</p>
                <p><strong>Severity:</strong> {bottleneck.severity.upper()}</p>
                <p><strong>Affected Items:</strong> {len(bottleneck.affected_items)}</p>
            """
            if bottleneck.recommendations:
                html += "<h4>Recommendations:</h4>"
                for rec in bottleneck.recommendations:
                    html += f'<div class="recommendation">{rec}</div>'
            html += "</div>"
        html += "</div>"
        return html

    def _render_insights_html(self, insights: List[PerformanceInsight]) -> str:
        """Render insights section as HTML."""
        if not insights:
            return ""

        html = '<div class="section"><h2>Performance Insights</h2>'
        for insight in insights:
            html += f"""
            <div class="insight">
                <h3>{insight.title}</h3>
                <p>{insight.description}</p>
                <p><strong>Priority:</strong> {insight.priority}/5</p>
                <p><strong>Impact:</strong> {insight.impact}</p>
                <p><strong>Effort:</strong> {insight.effort}</p>
            </div>
            """
        html += "</div>"
        return html


class FlameGraphGenerator:
    """
    Generates flame graph data from profiling results.

    Creates data structures suitable for flame graph visualization.
    """

    def __init__(self):
        """Initialize flame graph generator."""
        pass

    def generate_from_profile(self, result: ProfileResult) -> Dict[str, Any]:
        """
        Generate flame graph data from profile result.

        Args:
            result: Profile result with stats

        Returns:
            Flame graph data structure
        """
        if not result.stats:
            return {}

        # Extract call stack from pstats
        flame_data = {
            "name": result.function_name,
            "value": result.duration_seconds * 1000,
            "children": [],
        }

        # Note: Full flame graph generation would require parsing pstats
        # This is a simplified version
        return flame_data

    def generate_from_traces(self, traces: List[Trace]) -> Dict[str, Any]:
        """
        Generate flame graph data from distributed traces.

        Args:
            traces: List of trace spans

        Returns:
            Flame graph data structure
        """
        if not traces:
            return {}

        # Group traces by trace_id
        from collections import defaultdict

        trace_groups = defaultdict(list)
        for trace in traces:
            trace_groups[trace.trace_id].append(trace)

        # Build tree structure for the first trace
        first_trace_id = next(iter(trace_groups))
        spans = trace_groups[first_trace_id]

        # Find root span (no parent)
        root_spans = [s for s in spans if not s.parent_span_id]
        if not root_spans:
            return {}

        root = root_spans[0]

        def build_tree(span: Trace) -> Dict[str, Any]:
            """Build tree recursively."""
            children = [s for s in spans if s.parent_span_id == span.span_id]

            return {
                "name": span.operation_name,
                "value": span.duration_ms or 0,
                "children": [build_tree(child) for child in children],
            }

        return build_tree(root)

    def export_to_speedscope(self, result: ProfileResult) -> Dict[str, Any]:
        """
        Export profiling data in Speedscope format.

        Args:
            result: Profile result

        Returns:
            Speedscope-compatible JSON structure
        """
        # Speedscope format: https://www.speedscope.app/
        speedscope_data = {
            "$schema": "https://www.speedscope.app/file-format-schema.json",
            "version": "0.0.1",
            "shared": {"frames": []},
            "profiles": [
                {
                    "type": "evented",
                    "name": result.function_name,
                    "unit": "milliseconds",
                    "startValue": 0,
                    "endValue": result.duration_seconds * 1000,
                    "events": [],
                }
            ],
        }

        return speedscope_data

    def export_to_d3_hierarchy(
        self, flame_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Export flame graph data in D3 hierarchy format.

        Args:
            flame_data: Flame graph data structure

        Returns:
            D3-compatible hierarchy JSON
        """
        # D3 hierarchy format is the same as our internal format
        return flame_data
