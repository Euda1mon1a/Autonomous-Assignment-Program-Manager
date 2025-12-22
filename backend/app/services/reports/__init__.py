"""PDF Report Generation Services.

This package provides services for generating PDF reports for the
Residency Scheduler application, including:
- Schedule overview reports
- ACGME compliance reports
- Workload analytics reports
- Faculty summary reports

All reports support customizable branding, table of contents, and page numbers.
"""

from app.services.reports.pdf_generator import PDFReportGenerator

__all__ = ["PDFReportGenerator"]
