"""Reports package for analytics report generation."""

import importlib.util
import sys
from pathlib import Path

# Import from reports.py file (shadowed by this package directory)
_reports_file = Path(__file__).parent.parent / "reports.py"
_spec = importlib.util.spec_from_file_location("reports_base", _reports_file)
_reports_base = importlib.util.module_from_spec(_spec)
sys.modules["reports_base"] = _reports_base
_spec.loader.exec_module(_reports_base)

# Re-export ReportGenerator from reports.py
ReportGenerator = _reports_base.ReportGenerator

# Package-level imports
from app.analytics.reports.report_builder import ReportBuilder
from app.analytics.reports.pdf_generator import PDFGenerator
from app.analytics.reports.excel_exporter import ExcelExporter
from app.analytics.reports.chart_generator import ChartGenerator
from app.analytics.reports.template_manager import TemplateManager
from app.analytics.reports.acgme_annual import ACGMEAnnualReport
from app.analytics.reports.monthly_summary import MonthlySummaryReport
from app.analytics.reports.faculty_report import FacultyReport
from app.analytics.reports.resident_report import ResidentReport
from app.analytics.reports.resilience_report import ResilienceReport

__all__ = [
    # From reports.py (base module)
    "ReportGenerator",
    # From package modules
    "ReportBuilder",
    "PDFGenerator",
    "ExcelExporter",
    "ChartGenerator",
    "TemplateManager",
    "ACGMEAnnualReport",
    "MonthlySummaryReport",
    "FacultyReport",
    "ResidentReport",
    "ResilienceReport",
]
