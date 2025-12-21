"""Core PDF report generation service using ReportLab."""
import io
import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    PageTemplate,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)
from sqlalchemy.orm import Session

from app.schemas.reports import ReportMetadata, ReportRequest, ReportType

logger = logging.getLogger(__name__)


class PDFReportGenerator:
    """
    Core PDF report generator using ReportLab.

    Provides base functionality for generating professional PDF reports
    including headers, footers, table of contents, and page numbers.

    Features:
        - Professional header/footer with branding
        - Automatic table of contents generation
        - Page numbering with customizable formats
        - Consistent styling and formatting
        - Support for tables, charts, and paragraphs

    Example:
        >>> generator = PDFReportGenerator(db)
        >>> pdf_bytes = generator.generate_schedule_report(
        ...     start_date=date(2025, 1, 1),
        ...     end_date=date(2025, 1, 31)
        ... )
        >>> with open("report.pdf", "wb") as f:
        ...     f.write(pdf_bytes)
    """

    # Page settings
    PAGE_WIDTH, PAGE_HEIGHT = letter
    MARGIN_LEFT = 0.75 * inch
    MARGIN_RIGHT = 0.75 * inch
    MARGIN_TOP = 1.0 * inch
    MARGIN_BOTTOM = 0.75 * inch

    # Color scheme
    PRIMARY_COLOR = colors.HexColor("#1f3a93")  # Navy blue
    SECONDARY_COLOR = colors.HexColor("#2e5090")
    ACCENT_COLOR = colors.HexColor("#4a90e2")  # Light blue
    TEXT_COLOR = colors.HexColor("#333333")
    LIGHT_GRAY = colors.HexColor("#f5f5f5")
    MEDIUM_GRAY = colors.HexColor("#cccccc")

    def __init__(self, db: Session):
        """
        Initialize PDF report generator.

        Args:
            db: Database session for querying data
        """
        self.db = db
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()

    def _setup_custom_styles(self) -> None:
        """Set up custom paragraph styles for reports."""
        # Title style
        self.styles.add(
            ParagraphStyle(
                name="ReportTitle",
                parent=self.styles["Title"],
                fontSize=24,
                textColor=self.PRIMARY_COLOR,
                spaceAfter=30,
                alignment=TA_CENTER,
                fontName="Helvetica-Bold",
            )
        )

        # Section header style
        self.styles.add(
            ParagraphStyle(
                name="SectionHeader",
                parent=self.styles["Heading1"],
                fontSize=16,
                textColor=self.PRIMARY_COLOR,
                spaceAfter=12,
                spaceBefore=12,
                fontName="Helvetica-Bold",
            )
        )

        # Subsection header style
        self.styles.add(
            ParagraphStyle(
                name="SubsectionHeader",
                parent=self.styles["Heading2"],
                fontSize=14,
                textColor=self.SECONDARY_COLOR,
                spaceAfter=10,
                spaceBefore=10,
                fontName="Helvetica-Bold",
            )
        )

        # Body text style
        self.styles.add(
            ParagraphStyle(
                name="ReportBody",
                parent=self.styles["Normal"],
                fontSize=10,
                textColor=self.TEXT_COLOR,
                spaceAfter=6,
                leading=14,
            )
        )

        # Small text style
        self.styles.add(
            ParagraphStyle(
                name="SmallText",
                parent=self.styles["Normal"],
                fontSize=8,
                textColor=colors.gray,
                spaceAfter=4,
            )
        )

        # Footer style
        self.styles.add(
            ParagraphStyle(
                name="Footer",
                parent=self.styles["Normal"],
                fontSize=8,
                textColor=colors.gray,
                alignment=TA_CENTER,
            )
        )

    def _add_header(
        self,
        canvas_obj: canvas.Canvas,
        doc: BaseDocTemplate,
        title: str,
        include_logo: bool = True,
    ) -> None:
        """
        Add header to PDF page.

        Args:
            canvas_obj: ReportLab canvas object
            doc: Document template
            title: Report title to display in header
            include_logo: Whether to include organization logo
        """
        canvas_obj.saveState()

        # Draw header background
        canvas_obj.setFillColor(self.PRIMARY_COLOR)
        canvas_obj.rect(0, self.PAGE_HEIGHT - 0.6 * inch, self.PAGE_WIDTH, 0.6 * inch, fill=1)

        # Add title text
        canvas_obj.setFillColor(colors.white)
        canvas_obj.setFont("Helvetica-Bold", 14)
        canvas_obj.drawString(
            self.MARGIN_LEFT,
            self.PAGE_HEIGHT - 0.4 * inch,
            title,
        )

        # Optionally add logo (placeholder for now)
        if include_logo:
            # Logo would be drawn here
            # For now, just add organization name
            canvas_obj.setFont("Helvetica", 10)
            canvas_obj.drawRightString(
                self.PAGE_WIDTH - self.MARGIN_RIGHT,
                self.PAGE_HEIGHT - 0.4 * inch,
                "Residency Scheduler",
            )

        canvas_obj.restoreState()

    def _add_footer(
        self,
        canvas_obj: canvas.Canvas,
        doc: BaseDocTemplate,
        include_page_numbers: bool = True,
    ) -> None:
        """
        Add footer to PDF page.

        Args:
            canvas_obj: ReportLab canvas object
            doc: Document template
            include_page_numbers: Whether to include page numbers
        """
        canvas_obj.saveState()

        # Draw footer line
        canvas_obj.setStrokeColor(self.MEDIUM_GRAY)
        canvas_obj.setLineWidth(0.5)
        canvas_obj.line(
            self.MARGIN_LEFT,
            self.MARGIN_BOTTOM - 0.2 * inch,
            self.PAGE_WIDTH - self.MARGIN_RIGHT,
            self.MARGIN_BOTTOM - 0.2 * inch,
        )

        # Add page numbers
        if include_page_numbers:
            page_num = canvas_obj.getPageNumber()
            canvas_obj.setFillColor(colors.gray)
            canvas_obj.setFont("Helvetica", 8)
            canvas_obj.drawCentredString(
                self.PAGE_WIDTH / 2,
                self.MARGIN_BOTTOM - 0.4 * inch,
                f"Page {page_num}",
            )

        # Add generation timestamp
        canvas_obj.setFont("Helvetica", 8)
        canvas_obj.drawString(
            self.MARGIN_LEFT,
            self.MARGIN_BOTTOM - 0.4 * inch,
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        )

        canvas_obj.restoreState()

    def _create_table(
        self,
        data: list[list[Any]],
        col_widths: list[float] | None = None,
        header_row: bool = True,
    ) -> Table:
        """
        Create a formatted table.

        Args:
            data: Table data (list of rows)
            col_widths: Column widths in inches
            header_row: Whether first row is a header

        Returns:
            Formatted Table object
        """
        # Create table
        table = Table(data, colWidths=col_widths)

        # Base style
        style = [
            ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("TEXTCOLOR", (0, 0), (-1, -1), self.TEXT_COLOR),
            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("GRID", (0, 0), (-1, -1), 0.5, self.MEDIUM_GRAY),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, self.LIGHT_GRAY]),
        ]

        # Header row style
        if header_row:
            style.extend([
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 10),
                ("BACKGROUND", (0, 0), (-1, 0), self.PRIMARY_COLOR),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
                ("TOPPADDING", (0, 0), (-1, 0), 8),
            ])

        table.setStyle(TableStyle(style))
        return table

    def generate_pdf(
        self,
        elements: list,
        title: str,
        include_logo: bool = True,
        include_page_numbers: bool = True,
    ) -> bytes:
        """
        Generate PDF from list of elements.

        Args:
            elements: List of ReportLab flowables (paragraphs, tables, etc.)
            title: Report title for header
            include_logo: Whether to include logo in header
            include_page_numbers: Whether to include page numbers

        Returns:
            PDF content as bytes
        """
        # Create PDF in memory
        buffer = io.BytesIO()

        # Create document
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            leftMargin=self.MARGIN_LEFT,
            rightMargin=self.MARGIN_RIGHT,
            topMargin=self.MARGIN_TOP,
            bottomMargin=self.MARGIN_BOTTOM,
        )

        # Define page template with header/footer
        def on_page(canvas_obj: canvas.Canvas, doc: BaseDocTemplate) -> None:
            """Callback for drawing header/footer on each page."""
            self._add_header(canvas_obj, doc, title, include_logo)
            self._add_footer(canvas_obj, doc, include_page_numbers)

        # Build PDF
        doc.build(elements, onFirstPage=on_page, onLaterPages=on_page)

        # Get PDF bytes
        pdf_bytes = buffer.getvalue()
        buffer.close()

        return pdf_bytes

    def create_metadata(
        self,
        request: ReportRequest,
        pdf_bytes: bytes,
        generated_by: str,
        page_count: int | None = None,
    ) -> ReportMetadata:
        """
        Create report metadata.

        Args:
            request: Original report request
            pdf_bytes: Generated PDF bytes
            generated_by: User who generated the report
            page_count: Number of pages (estimated if not provided)

        Returns:
            ReportMetadata object
        """
        # Estimate page count if not provided
        if page_count is None:
            # Rough estimate: ~3KB per page
            page_count = max(1, len(pdf_bytes) // 3000)

        return ReportMetadata(
            report_id=uuid.uuid4(),
            report_type=request.report_type,
            generated_at=datetime.now().isoformat(),
            generated_by=generated_by,
            start_date=request.start_date,
            end_date=request.end_date,
            page_count=page_count,
            file_size_bytes=len(pdf_bytes),
        )
