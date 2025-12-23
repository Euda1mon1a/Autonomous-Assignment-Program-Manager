"""Faculty summary report template."""
import logging
from datetime import date, datetime
from typing import Any

from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import PageBreak, Paragraph, Spacer, Table, TableStyle
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session, joinedload

from app.models.assignment import Assignment
from app.models.block import Block
from app.models.person import Person
from app.models.swap import SwapRecord
from app.schemas.reports import FacultySummaryReportRequest
from app.services.reports.pdf_generator import PDFReportGenerator

logger = logging.getLogger(__name__)


class FacultySummaryReportTemplate:
    """
    Template for generating faculty summary reports.

    Generates a comprehensive report for faculty members showing:
    - Individual faculty workload statistics
    - Assignment distribution by rotation
    - Swap history (initiated and received)
    - Weekly workload breakdown
    - Performance indicators

    Example:
        >>> template = FacultySummaryReportTemplate(db)
        >>> pdf_bytes = template.generate(request)
    """

    def __init__(self, db: Session):
        """
        Initialize faculty summary report template.

        Args:
            db: Database session for querying data
        """
        self.db = db
        self.generator = PDFReportGenerator(db)

    def generate(self, request: FacultySummaryReportRequest) -> bytes:
        """
        Generate faculty summary report.

        Args:
            request: Faculty summary report request with parameters

        Returns:
            PDF content as bytes
        """
        logger.info(
            f"Generating faculty summary report from {request.start_date} to {request.end_date}"
        )

        # Build PDF elements
        elements = []

        # Title
        elements.append(
            Paragraph(
                f"Faculty Summary Report<br/>"
                f"<font size=14>{request.start_date} to {request.end_date}</font>",
                self.generator.styles["ReportTitle"],
            )
        )
        elements.append(Spacer(1, 0.3 * inch))

        # If no faculty IDs specified, get all faculty
        faculty_ids = request.faculty_ids
        if not faculty_ids:
            # Get all faculty members
            all_faculty = (
                self.db.query(Person).filter(Person.type == "faculty").all()
            )
            faculty_ids = [f.id for f in all_faculty]

        # Generate report for each faculty member
        for faculty_id in faculty_ids:
            faculty_data = self._get_faculty_data(
                faculty_id, request.start_date, request.end_date
            )

            if not faculty_data:
                continue

            ***REMOVED*** header
            elements.append(
                Paragraph(
                    f"Faculty: {faculty_data['name']}",
                    self.generator.styles["SectionHeader"]
                )
            )
            elements.append(Spacer(1, 0.1 * inch))

            # Summary statistics
            if request.include_workload:
                elements.extend(self._create_workload_section(faculty_data))
                elements.append(Spacer(1, 0.15 * inch))

            # Rotation breakdown
            elements.extend(self._create_rotation_breakdown(faculty_data))
            elements.append(Spacer(1, 0.15 * inch))

            # Swap history
            if request.include_supervision:
                elements.extend(self._create_swap_history(faculty_data))
                elements.append(Spacer(1, 0.15 * inch))

            # Page break between faculty
            if len(faculty_ids) > 1:
                elements.append(PageBreak())

        # Generate PDF
        return self.generator.build(
            elements=elements,
            include_toc=request.include_toc,
            include_logo=request.include_logo,
            include_page_numbers=request.include_page_numbers,
        )

    def _get_faculty_data(
        self, faculty_id: str, start_date: date, end_date: date
    ) -> dict[str, Any] | None:
        """
        Get faculty member data for the report period.

        Args:
            faculty_id: Faculty member ID
            start_date: Report start date
            end_date: Report end date

        Returns:
            Dictionary with faculty data or None if not found
        """
        # Get faculty member
        faculty = self.db.query(Person).filter(Person.id == faculty_id).first()

        if not faculty:
            logger.warning(f"Faculty not found: {faculty_id}")
            return None

        # Get assignments in date range
        assignment_list = (
            self.db.query(Assignment)
            .join(Block)
            .filter(
                Assignment.person_id == faculty_id,
                Block.date >= start_date,
                Block.date <= end_date,
            )
            .options(joinedload(Assignment.block))
            .options(joinedload(Assignment.rotation_template))
            .all()
        )

        # Get swap history
        swap_list = (
            self.db.query(SwapRecord)
            .filter(
                or_(
                    SwapRecord.source_faculty_id == faculty_id,
                    SwapRecord.target_faculty_id == faculty_id,
                ),
                SwapRecord.requested_at >= start_date,
                SwapRecord.requested_at <= end_date,
            )
            .all()
        )

        # Calculate rotation breakdown
        rotation_breakdown = {}
        for assignment in assignment_list:
            rotation = (
                assignment.rotation_template.name
                if assignment.rotation_template
                else assignment.activity_override or "Unassigned"
            )
            rotation_breakdown[rotation] = rotation_breakdown.get(rotation, 0) + 1

        # Calculate total blocks (half-days)
        total_blocks = len(assignment_list)
        total_weeks = total_blocks / 10  # Assuming 10 blocks (5 days) per week

        return {
            "faculty_id": str(faculty_id),
            "name": faculty.name,
            "email": faculty.email,
            "faculty_role": faculty.faculty_role,
            "total_blocks": total_blocks,
            "total_weeks": round(total_weeks, 1),
            "rotation_breakdown": rotation_breakdown,
            "total_swaps": len(swap_list),
            "swaps_initiated": sum(
                1 for s in swap_list if str(s.source_faculty_id) == str(faculty_id)
            ),
            "swaps_received": sum(
                1 for s in swap_list if str(s.target_faculty_id) == str(faculty_id)
            ),
            "assignments": assignment_list,
            "swaps": swap_list,
        }

    def _create_workload_section(self, faculty_data: dict[str, Any]) -> list:
        """Create workload statistics section."""
        elements = []

        elements.append(
            Paragraph("Workload Summary", self.generator.styles["Subsection"])
        )

        # Create summary table
        data = [
            ["Metric", "Value"],
            ["Total Blocks Assigned", str(faculty_data["total_blocks"])],
            ["Estimated Weeks", str(faculty_data["total_weeks"])],
            ["Faculty Role", faculty_data.get("faculty_role", "N/A") or "N/A"],
            ["Total Swaps", str(faculty_data["total_swaps"])],
        ]

        table = Table(data, colWidths=[3 * inch, 2 * inch])
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, 0), 12),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                    ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
                    ("GRID", (0, 0), (-1, -1), 1, colors.black),
                ]
            )
        )
        elements.append(table)

        return elements

    def _create_rotation_breakdown(self, faculty_data: dict[str, Any]) -> list:
        """Create rotation distribution breakdown."""
        elements = []

        elements.append(
            Paragraph("Rotation Distribution", self.generator.styles["Subsection"])
        )

        if not faculty_data["rotation_breakdown"]:
            elements.append(
                Paragraph("No assignments in this period.", self.generator.styles["Normal"])
            )
            return elements

        # Create rotation table
        data = [["Rotation", "Blocks", "Percentage"]]
        total = faculty_data["total_blocks"]

        for rotation, count in sorted(
            faculty_data["rotation_breakdown"].items(), key=lambda x: x[1], reverse=True
        ):
            percentage = (count / total * 100) if total > 0 else 0
            data.append([rotation, str(count), f"{percentage:.1f}%"])

        table = Table(data, colWidths=[3 * inch, 1 * inch, 1 * inch])
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, 0), 11),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                    ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
                    ("GRID", (0, 0), (-1, -1), 1, colors.black),
                ]
            )
        )
        elements.append(table)

        return elements

    def _create_swap_history(self, faculty_data: dict[str, Any]) -> list:
        """Create swap history section."""
        elements = []

        elements.append(
            Paragraph("Swap Activity", self.generator.styles["Subsection"])
        )

        # Create swap summary table
        data = [
            ["Swap Type", "Count"],
            ["Swaps Initiated", str(faculty_data["swaps_initiated"])],
            ["Swaps Received", str(faculty_data["swaps_received"])],
            ["Total Swaps", str(faculty_data["total_swaps"])],
        ]

        table = Table(data, colWidths=[3 * inch, 2 * inch])
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, 0), 11),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                    ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
                    ("GRID", (0, 0), (-1, -1), 1, colors.black),
                ]
            )
        )
        elements.append(table)

        return elements
