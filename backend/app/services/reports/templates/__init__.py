"""Report templates for different types of PDF reports."""

from app.services.reports.templates.analytics_report import AnalyticsReportTemplate
from app.services.reports.templates.compliance_report import ComplianceReportTemplate
from app.services.reports.templates.schedule_report import ScheduleReportTemplate

__all__ = [
    "ScheduleReportTemplate",
    "ComplianceReportTemplate",
    "AnalyticsReportTemplate",
]
