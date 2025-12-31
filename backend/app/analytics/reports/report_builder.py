"""Report Builder - Constructs reports from data."""

from typing import Any, Dict, List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class ReportBuilder:
    """Builds structured reports from analytics data."""

    def build_report(
        self,
        title: str,
        sections: list[dict[str, Any]],
        metadata: dict[str, Any] = None,
    ) -> dict[str, Any]:
        """Build a structured report."""
        return {
            "title": title,
            "generated_at": datetime.utcnow().isoformat(),
            "metadata": metadata or {},
            "sections": sections,
        }

    def add_section(
        self,
        report: dict[str, Any],
        title: str,
        content: Any,
        section_type: str = "data",
    ) -> dict[str, Any]:
        """Add a section to a report."""
        section = {
            "title": title,
            "type": section_type,
            "content": content,
        }
        report["sections"].append(section)
        return report

    def format_table(self, headers: list[str], rows: list[list[Any]]) -> dict[str, Any]:
        """Format data as a table."""
        return {"type": "table", "headers": headers, "rows": rows}

    def format_chart(self, chart_type: str, data: dict[str, Any]) -> dict[str, Any]:
        """Format data for a chart."""
        return {"type": "chart", "chart_type": chart_type, "data": data}
