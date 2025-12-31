"""Tests for report generation."""

import pytest
from datetime import date
from unittest.mock import AsyncMock

from app.analytics.reports.report_builder import ReportBuilder
from app.analytics.reports.pdf_generator import PDFGenerator
from app.analytics.reports.excel_exporter import ExcelExporter
from app.analytics.reports.chart_generator import ChartGenerator
from app.analytics.reports.template_manager import TemplateManager
from app.analytics.reports.acgme_annual import ACGMEAnnualReport


class TestReportBuilder:
    """Test report builder."""

    def test_build_report(self):
        """Test report building."""
        builder = ReportBuilder()

        report = builder.build_report(
            title="Test Report",
            sections=[{"title": "Section 1", "content": "Data"}],
            metadata={"author": "Test"},
        )

        assert report["title"] == "Test Report"
        assert len(report["sections"]) == 1
        assert "generated_at" in report

    def test_add_section(self):
        """Test adding section to report."""
        builder = ReportBuilder()

        report = builder.build_report("Test", [])
        report = builder.add_section(report, "New Section", {"data": 123})

        assert len(report["sections"]) == 1
        assert report["sections"][0]["title"] == "New Section"


class TestPDFGenerator:
    """Test PDF generator."""

    def test_generate_pdf(self):
        """Test PDF generation."""
        generator = PDFGenerator()

        report = {"title": "Test Report", "generated_at": "2024-01-01", "sections": []}
        pdf_bytes = generator.generate_pdf(report)

        assert isinstance(pdf_bytes, bytes)
        assert len(pdf_bytes) > 0


class TestExcelExporter:
    """Test Excel exporter."""

    def test_export_to_excel(self):
        """Test Excel export."""
        exporter = ExcelExporter()

        report = {
            "title": "Test Report",
            "generated_at": "2024-01-01",
            "sections": [
                {"title": "Data", "content": [{"metric": "value", "count": 10}]}
            ],
        }

        excel_bytes = exporter.export_to_excel(report)

        assert isinstance(excel_bytes, bytes)
        assert len(excel_bytes) > 0


class TestChartGenerator:
    """Test chart generator."""

    def test_generate_line_chart(self):
        """Test line chart generation."""
        generator = ChartGenerator()

        data = {"Series 1": [1, 2, 3, 4, 5]}
        chart = generator.generate_line_chart(data, "Test Chart")

        assert isinstance(chart, str)

    def test_generate_bar_chart(self):
        """Test bar chart generation."""
        generator = ChartGenerator()

        categories = ["A", "B", "C"]
        values = [10, 20, 15]
        chart = generator.generate_bar_chart(categories, values, "Test Bar Chart")

        assert isinstance(chart, str)


class TestTemplateManager:
    """Test template manager."""

    def test_get_template(self):
        """Test template retrieval."""
        manager = TemplateManager()

        template = manager.get_template("acgme_annual")

        assert isinstance(template, dict)
        assert "title" in template
        assert "sections" in template

    def test_list_templates(self):
        """Test template listing."""
        manager = TemplateManager()

        templates = manager.list_templates()

        assert isinstance(templates, dict)
        assert len(templates) > 0
        assert "acgme_annual" in templates


@pytest.mark.asyncio
class TestACGMEAnnualReport:
    """Test ACGME annual report."""

    async def test_generate(self, async_db_session):
        """Test annual report generation."""
        report_gen = ACGMEAnnualReport(async_db_session)

        # Mock dependencies
        report_gen.analytics_engine.calculate_all_metrics = AsyncMock(
            return_value={
                "schedule_metrics": {},
                "compliance_metrics": {},
                "resilience_metrics": {},
            }
        )
        report_gen.compliance_score.calculate_score = AsyncMock(
            return_value={
                "compliance_score": 95.0,
                "rating": "excellent",
            }
        )
        report_gen.violation_tracker.track_violations = AsyncMock(
            return_value={
                "total_violations": 2,
            }
        )

        report = await report_gen.generate(2024)

        assert isinstance(report, dict)
        assert "title" in report
        assert "sections" in report
        assert len(report["sections"]) > 0
