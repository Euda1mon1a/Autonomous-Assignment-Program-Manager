"""
Tests for PDF report generator service.

Comprehensive test suite for PDFReportGenerator class,
covering PDF generation, styling, tables, headers, and footers.
"""

import io
import pytest
from datetime import date, datetime
from unittest.mock import MagicMock, patch
from uuid import uuid4

from reportlab.lib import colors
from reportlab.platypus import Paragraph, Table, Spacer

from app.services.reports.pdf_generator import PDFReportGenerator
from app.schemas.reports import ReportRequest, ReportType


@pytest.fixture
def mock_db():
    """Create mock database session."""
    return MagicMock()


@pytest.fixture
def pdf_generator(mock_db):
    """Create PDFReportGenerator instance."""
    return PDFReportGenerator(db=mock_db)


class TestPDFReportGenerator:
    """Test suite for PDFReportGenerator class."""

    def test_initialization_sets_up_styles(self, pdf_generator):
        """Test generator initializes with custom styles."""
        # Assert
        assert pdf_generator.db is not None
        assert pdf_generator.styles is not None
        assert "ReportTitle" in pdf_generator.styles
        assert "SectionHeader" in pdf_generator.styles
        assert "SubsectionHeader" in pdf_generator.styles
        assert "ReportBody" in pdf_generator.styles
        assert "SmallText" in pdf_generator.styles
        assert "Footer" in pdf_generator.styles

    def test_custom_styles_have_correct_properties(self, pdf_generator):
        """Test custom styles have correct color and font properties."""
        # Assert
        title_style = pdf_generator.styles["ReportTitle"]
        assert title_style.fontSize == 24
        assert title_style.textColor == pdf_generator.PRIMARY_COLOR

        section_style = pdf_generator.styles["SectionHeader"]
        assert section_style.fontSize == 16
        assert section_style.textColor == pdf_generator.PRIMARY_COLOR

        body_style = pdf_generator.styles["ReportBody"]
        assert body_style.fontSize == 10
        assert body_style.textColor == pdf_generator.TEXT_COLOR

    def test_create_table_with_header_row(self, pdf_generator):
        """Test creating table with header row styling."""
        # Arrange
        data = [
            ["Name", "Role", "PGY Level"],
            ["Dr. Smith", "Resident", "PGY-2"],
            ["Dr. Jones", "Resident", "PGY-3"],
        ]

        # Act
        table = pdf_generator._create_table(data, header_row=True)

        # Assert
        assert isinstance(table, Table)
        assert table._cellvalues == data
        # Verify table has style applied
        assert table._cellstyles is not None

    def test_create_table_without_header_row(self, pdf_generator):
        """Test creating table without header row styling."""
        # Arrange
        data = [
            ["Item 1", "Value 1"],
            ["Item 2", "Value 2"],
        ]

        # Act
        table = pdf_generator._create_table(data, header_row=False)

        # Assert
        assert isinstance(table, Table)
        assert table._cellvalues == data

    def test_create_table_with_custom_column_widths(self, pdf_generator):
        """Test creating table with custom column widths."""
        # Arrange
        data = [["Col1", "Col2", "Col3"], ["A", "B", "C"]]
        col_widths = [1.5, 2.0, 1.0]  # In inches

        # Act
        table = pdf_generator._create_table(
            data, col_widths=col_widths, header_row=True
        )

        # Assert
        assert isinstance(table, Table)
        assert table._colWidths == col_widths

    def test_generate_pdf_returns_bytes(self, pdf_generator):
        """Test generating PDF returns bytes object."""
        # Arrange
        elements = [
            Paragraph("Test Report", pdf_generator.styles["ReportTitle"]),
            Spacer(1, 12),
            Paragraph("This is a test report.", pdf_generator.styles["ReportBody"]),
        ]

        # Act
        pdf_bytes = pdf_generator.generate_pdf(
            elements=elements,
            title="Test Report",
        )

        # Assert
        assert isinstance(pdf_bytes, bytes)
        assert len(pdf_bytes) > 0
        # PDF files start with %PDF
        assert pdf_bytes[:4] == b"%PDF"

    def test_generate_pdf_with_logo_disabled(self, pdf_generator):
        """Test generating PDF without logo."""
        # Arrange
        elements = [
            Paragraph("Report Without Logo", pdf_generator.styles["ReportTitle"]),
        ]

        # Act
        pdf_bytes = pdf_generator.generate_pdf(
            elements=elements,
            title="Report Without Logo",
            include_logo=False,
        )

        # Assert
        assert isinstance(pdf_bytes, bytes)
        assert len(pdf_bytes) > 0

    def test_generate_pdf_with_page_numbers_disabled(self, pdf_generator):
        """Test generating PDF without page numbers."""
        # Arrange
        elements = [
            Paragraph(
                "Report Without Page Numbers", pdf_generator.styles["ReportTitle"]
            ),
        ]

        # Act
        pdf_bytes = pdf_generator.generate_pdf(
            elements=elements,
            title="Report Without Page Numbers",
            include_page_numbers=False,
        )

        # Assert
        assert isinstance(pdf_bytes, bytes)
        assert len(pdf_bytes) > 0

    def test_generate_pdf_with_table(self, pdf_generator):
        """Test generating PDF with table element."""
        # Arrange
        table_data = [
            ["Name", "Hours", "Status"],
            ["Dr. Smith", "80", "Compliant"],
            ["Dr. Jones", "75", "Compliant"],
            ["Dr. Brown", "82", "Warning"],
        ]

        elements = [
            Paragraph("Weekly Hours Report", pdf_generator.styles["ReportTitle"]),
            Spacer(1, 20),
            pdf_generator._create_table(table_data, header_row=True),
        ]

        # Act
        pdf_bytes = pdf_generator.generate_pdf(
            elements=elements,
            title="Weekly Hours Report",
        )

        # Assert
        assert isinstance(pdf_bytes, bytes)
        assert len(pdf_bytes) > 1000  # Should have substantial content

    def test_create_metadata_from_report_request(self, pdf_generator):
        """Test creating report metadata from report request."""
        # Arrange
        request = ReportRequest(
            report_type=ReportType.SCHEDULE,
            start_date=date(2025, 1, 1),
            end_date=date(2025, 1, 31),
            filters={},
        )
        pdf_bytes = b"fake pdf content" * 100
        generated_by = "test_user"

        # Act
        metadata = pdf_generator.create_metadata(
            request=request,
            pdf_bytes=pdf_bytes,
            generated_by=generated_by,
            page_count=5,
        )

        # Assert
        assert metadata.report_type == ReportType.SCHEDULE
        assert metadata.start_date == date(2025, 1, 1)
        assert metadata.end_date == date(2025, 1, 31)
        assert metadata.generated_by == "test_user"
        assert metadata.page_count == 5
        assert metadata.file_size_bytes == len(pdf_bytes)
        assert metadata.report_id is not None

    def test_create_metadata_estimates_page_count(self, pdf_generator):
        """Test metadata estimates page count when not provided."""
        # Arrange
        request = ReportRequest(
            report_type=ReportType.COMPLIANCE,
            start_date=date(2025, 1, 1),
            end_date=date(2025, 12, 31),
            filters={},
        )
        # Roughly 3KB = 1 page, so 9KB should estimate 3 pages
        pdf_bytes = b"x" * 9000

        # Act
        metadata = pdf_generator.create_metadata(
            request=request,
            pdf_bytes=pdf_bytes,
            generated_by="system",
        )

        # Assert
        assert metadata.page_count >= 1
        assert metadata.page_count == max(1, len(pdf_bytes) // 3000)

    def test_page_dimensions_are_letter_size(self, pdf_generator):
        """Test page dimensions are US letter size."""
        # Assert
        # Letter size is 8.5 x 11 inches = 612 x 792 points
        assert pdf_generator.PAGE_WIDTH == 612
        assert pdf_generator.PAGE_HEIGHT == 792

    def test_color_scheme_is_defined(self, pdf_generator):
        """Test color scheme constants are defined."""
        # Assert
        assert pdf_generator.PRIMARY_COLOR is not None
        assert pdf_generator.SECONDARY_COLOR is not None
        assert pdf_generator.ACCENT_COLOR is not None
        assert pdf_generator.TEXT_COLOR is not None
        assert pdf_generator.LIGHT_GRAY is not None
        assert pdf_generator.MEDIUM_GRAY is not None

    def test_generate_complex_multi_section_report(self, pdf_generator):
        """Test generating complex report with multiple sections."""
        # Arrange
        elements = [
            Paragraph("Residency Schedule Report", pdf_generator.styles["ReportTitle"]),
            Spacer(1, 30),
            Paragraph("Executive Summary", pdf_generator.styles["SectionHeader"]),
            Paragraph(
                "This report summarizes scheduling data for January 2025.",
                pdf_generator.styles["ReportBody"],
            ),
            Spacer(1, 20),
            Paragraph("Resident Assignments", pdf_generator.styles["SectionHeader"]),
            pdf_generator._create_table(
                [
                    ["Resident", "Rotation", "Dates"],
                    ["PGY1-01", "Inpatient", "Jan 1-15"],
                    ["PGY1-02", "Clinic", "Jan 1-15"],
                ],
                header_row=True,
            ),
            Spacer(1, 20),
            Paragraph("ACGME Compliance", pdf_generator.styles["SubsectionHeader"]),
            Paragraph(
                "All residents are compliant with work hour limits.",
                pdf_generator.styles["ReportBody"],
            ),
        ]

        # Act
        pdf_bytes = pdf_generator.generate_pdf(
            elements=elements,
            title="Schedule Report - January 2025",
        )

        # Assert
        assert isinstance(pdf_bytes, bytes)
        assert len(pdf_bytes) > 2000  # Multi-section report should be substantial
        assert pdf_bytes[:4] == b"%PDF"
