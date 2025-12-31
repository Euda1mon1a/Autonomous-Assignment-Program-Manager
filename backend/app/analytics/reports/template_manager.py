"""Template Manager - Manages report templates."""

from typing import Any, Dict
import logging

logger = logging.getLogger(__name__)


class TemplateManager:
    """Manages report templates."""

    TEMPLATES = {
        "acgme_annual": {
            "title": "ACGME Annual Report",
            "sections": [
                "Executive Summary",
                "Compliance Metrics",
                "Work Hour Analysis",
                "Violations Report",
                "Recommendations",
            ],
        },
        "monthly_summary": {
            "title": "Monthly Summary Report",
            "sections": [
                "Overview",
                "Coverage Analysis",
                "Workload Distribution",
                "Key Metrics",
            ],
        },
        "faculty_workload": {
            "title": "Faculty Workload Report",
            "sections": [
                "Faculty Overview",
                "Assignment Distribution",
                "Call Schedule",
                "Clinic Hours",
            ],
        },
        "resident_hours": {
            "title": "Resident Hours Report",
            "sections": [
                "Resident Overview",
                "Weekly Hours",
                "Compliance Status",
                "Rotation History",
            ],
        },
        "resilience": {
            "title": "Resilience Report",
            "sections": [
                "Utilization Metrics",
                "N-1 Analysis",
                "Risk Assessment",
                "Recommendations",
            ],
        },
    }

    def get_template(self, template_name: str) -> dict[str, Any]:
        """Get a report template."""
        return self.TEMPLATES.get(
            template_name,
            {
                "title": "Custom Report",
                "sections": [],
            },
        )

    def list_templates(self) -> dict[str, str]:
        """List available templates."""
        return {name: template["title"] for name, template in self.TEMPLATES.items()}
