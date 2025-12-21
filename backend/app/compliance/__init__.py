"""
Compliance module for ACGME compliance reporting and analysis.

This module provides comprehensive compliance reporting capabilities including:
- ACGME compliance reports (80-hour rule, 1-in-7 rule, supervision ratios)
- Work hour violation summaries
- Leave utilization analysis
- Schedule coverage metrics
- Trend analysis over time
- Export to PDF and Excel formats
"""

from app.compliance.reports import ComplianceReportGenerator

__all__ = ["ComplianceReportGenerator"]
