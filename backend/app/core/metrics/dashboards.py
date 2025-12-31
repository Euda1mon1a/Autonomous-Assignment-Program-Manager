"""
Dashboard configurations for monitoring systems.

Provides pre-built dashboard definitions for:
- Grafana
- Datadog
- CloudWatch
- Custom visualization tools
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class DashboardType(str, Enum):
    """Dashboard types."""

    OVERVIEW = "overview"
    PERFORMANCE = "performance"
    SECURITY = "security"
    COMPLIANCE = "compliance"
    INFRASTRUCTURE = "infrastructure"


class VisualizationType(str, Enum):
    """Visualization types."""

    GRAPH = "graph"
    GAUGE = "gauge"
    TABLE = "table"
    HEATMAP = "heatmap"
    STAT = "stat"
    BAR_CHART = "bar_chart"


@dataclass
class Panel:
    """Dashboard panel configuration."""

    title: str
    visualization_type: VisualizationType
    query: str
    description: str | None = None
    unit: str = "short"
    thresholds: list[float] = field(default_factory=list)
    grid_pos: dict[str, int] = field(default_factory=dict)
    options: dict[str, Any] = field(default_factory=dict)


@dataclass
class Dashboard:
    """Dashboard configuration."""

    title: str
    type: DashboardType
    description: str
    panels: list[Panel]
    refresh_interval: str = "30s"
    time_range: str = "1h"
    tags: list[str] = field(default_factory=list)
    variables: list[dict[str, Any]] = field(default_factory=list)


class GrafanaDashboardBuilder:
    """
    Builder for Grafana dashboard JSON.

    Creates dashboard configurations compatible with Grafana API.
    """

    def __init__(self):
        """Initialize Grafana dashboard builder."""
        self.dashboards: list[Dashboard] = []

    def build_overview_dashboard(self) -> dict[str, Any]:
        """
        Build overview dashboard showing key metrics.

        Returns:
            dict: Grafana dashboard JSON
        """
        panels = [
            # Request rate
            Panel(
                title="Request Rate",
                visualization_type=VisualizationType.GRAPH,
                query='rate(http_requests_total{job="residency_scheduler"}[5m])',
                description="HTTP requests per second",
                grid_pos={"h": 8, "w": 12, "x": 0, "y": 0},
            ),
            # Response time
            Panel(
                title="Response Time (p95)",
                visualization_type=VisualizationType.GRAPH,
                query='histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))',
                description="95th percentile response time",
                unit="s",
                thresholds=[0.5, 1.0, 2.0],
                grid_pos={"h": 8, "w": 12, "x": 12, "y": 0},
            ),
            # Error rate
            Panel(
                title="Error Rate",
                visualization_type=VisualizationType.STAT,
                query='rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m])',
                description="Percentage of 5xx errors",
                unit="percentunit",
                thresholds=[0.01, 0.05],
                grid_pos={"h": 4, "w": 6, "x": 0, "y": 8},
            ),
            # Active users
            Panel(
                title="Active Users",
                visualization_type=VisualizationType.STAT,
                query='count(count by (user_id) (rate(http_requests_total[5m])))',
                description="Number of active users in last 5 minutes",
                grid_pos={"h": 4, "w": 6, "x": 6, "y": 8},
            ),
            # Database connections
            Panel(
                title="Database Connections",
                visualization_type=VisualizationType.GAUGE,
                query='db_connections_active',
                description="Active database connections",
                thresholds=[50, 80, 100],
                grid_pos={"h": 4, "w": 6, "x": 12, "y": 8},
            ),
            # Cache hit rate
            Panel(
                title="Cache Hit Rate",
                visualization_type=VisualizationType.STAT,
                query='rate(cache_hits_total[5m]) / (rate(cache_hits_total[5m]) + rate(cache_misses_total[5m]))',
                description="Percentage of cache hits",
                unit="percentunit",
                thresholds=[0.7, 0.9],
                grid_pos={"h": 4, "w": 6, "x": 18, "y": 8},
            ),
        ]

        dashboard = Dashboard(
            title="Residency Scheduler - Overview",
            type=DashboardType.OVERVIEW,
            description="High-level overview of system health and performance",
            panels=panels,
            tags=["overview", "health"],
        )

        return self._to_grafana_json(dashboard)

    def build_compliance_dashboard(self) -> dict[str, Any]:
        """
        Build compliance dashboard for ACGME monitoring.

        Returns:
            dict: Grafana dashboard JSON
        """
        panels = [
            # ACGME violations
            Panel(
                title="ACGME Violations (24h)",
                visualization_type=VisualizationType.STAT,
                query='increase(acgme_violations_total[24h])',
                description="Number of ACGME violations in last 24 hours",
                thresholds=[1, 5, 10],
                grid_pos={"h": 6, "w": 6, "x": 0, "y": 0},
            ),
            # Work hour violations
            Panel(
                title="Work Hour Violations by Type",
                visualization_type=VisualizationType.BAR_CHART,
                query='sum by (rule) (increase(acgme_violations_total[7d]))',
                description="Breakdown of violations by rule type",
                grid_pos={"h": 8, "w": 12, "x": 6, "y": 0},
            ),
            # Schedule overrides
            Panel(
                title="ACGME Overrides (7d)",
                visualization_type=VisualizationType.TABLE,
                query='acgme_override_events',
                description="Recent ACGME overrides with justifications",
                grid_pos={"h": 8, "w": 12, "x": 0, "y": 6},
            ),
            # Compliance score
            Panel(
                title="Compliance Score",
                visualization_type=VisualizationType.GAUGE,
                query='(1 - (increase(acgme_violations_total[7d]) / schedule_assignments_total)) * 100',
                description="Overall compliance score (% of assignments without violations)",
                unit="percent",
                thresholds=[90, 95, 98],
                grid_pos={"h": 6, "w": 6, "x": 18, "y": 0},
            ),
        ]

        dashboard = Dashboard(
            title="ACGME Compliance Monitoring",
            type=DashboardType.COMPLIANCE,
            description="ACGME compliance violations and overrides",
            panels=panels,
            tags=["compliance", "acgme"],
        )

        return self._to_grafana_json(dashboard)

    def build_security_dashboard(self) -> dict[str, Any]:
        """
        Build security dashboard for monitoring security events.

        Returns:
            dict: Grafana dashboard JSON
        """
        panels = [
            # Failed auth attempts
            Panel(
                title="Failed Authentication Attempts",
                visualization_type=VisualizationType.GRAPH,
                query='rate(auth_failures_total[5m])',
                description="Failed authentication attempts per second",
                thresholds=[0.1, 0.5],
                grid_pos={"h": 8, "w": 12, "x": 0, "y": 0},
            ),
            # Rate limit hits
            Panel(
                title="Rate Limit Violations",
                visualization_type=VisualizationType.GRAPH,
                query='rate(rate_limit_exceeded_total[5m])',
                description="Rate limit violations per second",
                grid_pos={"h": 8, "w": 12, "x": 12, "y": 0},
            ),
            # Suspicious activity
            Panel(
                title="Suspicious Activity Events",
                visualization_type=VisualizationType.TABLE,
                query='suspicious_activity_events',
                description="Recent suspicious activity detections",
                grid_pos={"h": 10, "w": 24, "x": 0, "y": 8},
            ),
        ]

        dashboard = Dashboard(
            title="Security Monitoring",
            type=DashboardType.SECURITY,
            description="Security events and threats",
            panels=panels,
            tags=["security", "auth"],
        )

        return self._to_grafana_json(dashboard)

    def _to_grafana_json(self, dashboard: Dashboard) -> dict[str, Any]:
        """
        Convert dashboard to Grafana JSON format.

        Args:
            dashboard: Dashboard configuration

        Returns:
            dict: Grafana-compatible dashboard JSON
        """
        panels_json = []

        for idx, panel in enumerate(dashboard.panels):
            panel_json = {
                "id": idx + 1,
                "title": panel.title,
                "type": self._map_visualization_type(panel.visualization_type),
                "targets": [
                    {
                        "expr": panel.query,
                        "refId": "A",
                    }
                ],
                "gridPos": panel.grid_pos,
                "options": panel.options,
            }

            if panel.description:
                panel_json["description"] = panel.description

            if panel.thresholds:
                panel_json["fieldConfig"] = {
                    "defaults": {
                        "thresholds": {
                            "mode": "absolute",
                            "steps": [
                                {"color": "green", "value": None},
                                *[
                                    {"color": self._get_threshold_color(i), "value": threshold}
                                    for i, threshold in enumerate(panel.thresholds)
                                ],
                            ],
                        },
                        "unit": panel.unit,
                    }
                }

            panels_json.append(panel_json)

        return {
            "dashboard": {
                "title": dashboard.title,
                "description": dashboard.description,
                "tags": dashboard.tags,
                "panels": panels_json,
                "refresh": dashboard.refresh_interval,
                "time": {
                    "from": f"now-{dashboard.time_range}",
                    "to": "now",
                },
                "templating": {"list": dashboard.variables},
            },
            "overwrite": True,
        }

    def _map_visualization_type(self, viz_type: VisualizationType) -> str:
        """Map visualization type to Grafana panel type."""
        mapping = {
            VisualizationType.GRAPH: "timeseries",
            VisualizationType.GAUGE: "gauge",
            VisualizationType.TABLE: "table",
            VisualizationType.HEATMAP: "heatmap",
            VisualizationType.STAT: "stat",
            VisualizationType.BAR_CHART: "barchart",
        }
        return mapping.get(viz_type, "timeseries")

    def _get_threshold_color(self, index: int) -> str:
        """Get color for threshold based on index."""
        colors = ["yellow", "orange", "red"]
        return colors[min(index, len(colors) - 1)]


# Pre-built dashboard configurations


def get_overview_dashboard() -> dict[str, Any]:
    """Get overview dashboard configuration."""
    builder = GrafanaDashboardBuilder()
    return builder.build_overview_dashboard()


def get_compliance_dashboard() -> dict[str, Any]:
    """Get compliance dashboard configuration."""
    builder = GrafanaDashboardBuilder()
    return builder.build_compliance_dashboard()


def get_security_dashboard() -> dict[str, Any]:
    """Get security dashboard configuration."""
    builder = GrafanaDashboardBuilder()
    return builder.build_security_dashboard()


# Dashboard management


async def create_dashboards_in_grafana(
    grafana_url: str,
    api_key: str,
) -> dict[str, Any]:
    """
    Create all dashboards in Grafana.

    Args:
        grafana_url: Grafana URL
        api_key: Grafana API key

    Returns:
        dict: Creation results
    """
    import httpx

    dashboards = [
        ("overview", get_overview_dashboard()),
        ("compliance", get_compliance_dashboard()),
        ("security", get_security_dashboard()),
    ]

    results = {}

    async with httpx.AsyncClient() as client:
        for name, dashboard in dashboards:
            try:
                response = await client.post(
                    f"{grafana_url}/api/dashboards/db",
                    json=dashboard,
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json",
                    },
                )
                response.raise_for_status()
                results[name] = "success"
            except Exception as e:
                results[name] = f"failed: {e}"

    return results
