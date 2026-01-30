"""Schedule overview report template."""

import logging
from collections import defaultdict
from datetime import date
from typing import Any
from uuid import UUID

from reportlab.lib.units import inch
from reportlab.platypus import PageBreak, Paragraph, Spacer, Table
from sqlalchemy import and_
from sqlalchemy.orm import Session, joinedload

from app.models.assignment import Assignment
from app.models.block import Block
from app.models.person import Person
from app.schemas.reports import ScheduleReportRequest
from app.services.reports.pdf_generator import PDFReportGenerator

logger = logging.getLogger(__name__)


class ScheduleReportTemplate:
    """
    Schedule overview report template.

    Generates comprehensive schedule reports showing:
    - Overall schedule statistics
    - Assignment details by person
    - Coverage summary by rotation
    - Daily schedule breakdown (optional)

    Example:
        >>> template = ScheduleReportTemplate(db)
        >>> pdf_bytes = template.generate(request)
    """

    def __init__(self, db: Session) -> None:
        """
        Initialize schedule report template.

        Args:
            db: Database session for querying data
        """
        self.db = db
        self.generator = PDFReportGenerator(db)

    def generate(self, request: ScheduleReportRequest) -> bytes:
        """
        Generate schedule overview report.

        Args:
            request: Schedule report request with parameters

        Returns:
            PDF content as bytes
        """
        logger.info(
            f"Generating schedule report from {request.start_date} to {request.end_date}"
        )

        # Collect data
        assignments_data = self._get_assignments(request)
        people_data = self._get_people(request)
        coverage_data = self._get_coverage_summary(request)

        # Build PDF elements
        elements = []

        # Title
        elements.append(
            Paragraph(
                f"Schedule Overview Report<br/>"
                f"<font size=14>{request.start_date} to {request.end_date}</font>",
                self.generator.styles["ReportTitle"],
            )
        )
        elements.append(Spacer(1, 0.3 * inch))

        # Executive summary
        elements.append(
            Paragraph("Executive Summary", self.generator.styles["SectionHeader"])
        )
        elements.extend(self._create_summary_section(assignments_data, people_data))
        elements.append(Spacer(1, 0.2 * inch))

        # Coverage summary
        elements.append(
            Paragraph("Coverage Summary", self.generator.styles["SectionHeader"])
        )
        elements.extend(self._create_coverage_section(coverage_data))
        elements.append(Spacer(1, 0.2 * inch))

        # Assignment details (if requested)
        if request.include_details:
            elements.append(PageBreak())
            elements.append(
                Paragraph(
                    "Assignment Details by Person",
                    self.generator.styles["SectionHeader"],
                )
            )
            elements.extend(
                self._create_assignment_details(assignments_data, people_data)
            )

            # Generate PDF
        return self.generator.generate_pdf(
            elements=elements,
            title="Schedule Overview Report",
            include_logo=request.include_logo,
            include_page_numbers=request.include_page_numbers,
        )

    def _get_assignments(self, request: ScheduleReportRequest) -> list[Assignment]:
        """Query assignments for the report period."""
        query = (
            self.db.query(Assignment)
            .join(Block)
            .options(
                joinedload(Assignment.person),
                joinedload(Assignment.block),
                joinedload(Assignment.rotation_template),
            )
            .filter(
                and_(
                    Block.date >= request.start_date,
                    Block.date <= request.end_date,
                )
            )
        )

        # Filter by person IDs if specified
        if request.person_ids:
            query = query.filter(Assignment.person_id.in_(request.person_ids))

            # Filter by rotation template IDs if specified
        if request.rotation_template_ids:
            query = query.filter(
                Assignment.rotation_template_id.in_(request.rotation_template_ids)
            )

        return query.order_by(Block.date, Assignment.person_id).all()

    def _get_people(self, request: ScheduleReportRequest) -> list[Person]:
        """Query people included in the report."""
        query = self.db.query(Person)

        if request.person_ids:
            query = query.filter(Person.id.in_(request.person_ids))

        return query.order_by(Person.type, Person.name).all()

    def _get_coverage_summary(
        self, request: ScheduleReportRequest
    ) -> dict[str, dict[str, Any]]:
        """Calculate coverage summary by rotation."""
        assignments = self._get_assignments(request)
        coverage = defaultdict(lambda: {"total": 0, "residents": 0, "faculty": 0})

        for assignment in assignments:
            rotation_name = assignment.activity_name
            coverage[rotation_name]["total"] += 1

            if assignment.person and assignment.person.type == "resident":
                coverage[rotation_name]["residents"] += 1
            elif assignment.person and assignment.person.type == "faculty":
                coverage[rotation_name]["faculty"] += 1

        return dict(coverage)

    def _create_summary_section(
        self, assignments: list[Assignment], people: list[Person]
    ) -> list:
        """Create executive summary section."""
        elements = []

        # Calculate statistics
        total_assignments = len(assignments)
        residents = [p for p in people if p.type == "resident"]
        faculty = [p for p in people if p.type == "faculty"]

        # Summary text
        elements.append(
            Paragraph(
                f"This report covers {total_assignments} total assignments across "
                f"{len(residents)} residents and {len(faculty)} faculty members.",
                self.generator.styles["ReportBody"],
            )
        )
        elements.append(Spacer(1, 0.1 * inch))

        # Statistics table
        stats_data = [
            ["Metric", "Count"],
            ["Total Assignments", str(total_assignments)],
            ["Total Residents", str(len(residents))],
            ["Total Faculty", str(len(faculty))],
            [
                "Avg Assignments/Person",
                f"{total_assignments / max(len(people), 1):.1f}",
            ],
        ]

        stats_table = self.generator._create_table(
            stats_data, col_widths=[3.5 * inch, 2 * inch]
        )
        elements.append(stats_table)

        return elements

    def _create_coverage_section(
        self, coverage_data: dict[str, dict[str, Any]]
    ) -> list:
        """Create coverage summary section."""
        elements = []

        if not coverage_data:
            elements.append(
                Paragraph(
                    "No coverage data available for this period.",
                    self.generator.styles["ReportBody"],
                )
            )
            return elements

            # Coverage table
        coverage_table_data = [
            ["Rotation/Activity", "Total Assignments", "Residents", "Faculty"]
        ]

        for rotation_name, stats in sorted(coverage_data.items()):
            coverage_table_data.append(
                [
                    rotation_name,
                    str(stats["total"]),
                    str(stats["residents"]),
                    str(stats["faculty"]),
                ]
            )

        coverage_table = self.generator._create_table(
            coverage_table_data,
            col_widths=[2.5 * inch, 1.5 * inch, 1.25 * inch, 1.25 * inch],
        )
        elements.append(coverage_table)

        return elements

    def _create_assignment_details(
        self, assignments: list[Assignment], people: list[Person]
    ) -> list:
        """Create detailed assignment listing by person."""
        elements = []

        # Group assignments by person
        assignments_by_person = defaultdict(list)
        for assignment in assignments:
            if assignment.person:
                assignments_by_person[assignment.person.id].append(assignment)

                # Create section for each person
        for person in people:
            person_assignments = assignments_by_person.get(person.id, [])
            if not person_assignments:
                continue

                # Person header
            elements.append(
                Paragraph(
                    f"{person.name} ({person.type.upper()})",
                    self.generator.styles["SubsectionHeader"],
                )
            )

            # Assignment table
            assignment_data = [["Date", "Session", "Activity", "Role"]]

            for assignment in sorted(
                person_assignments, key=lambda a: (a.block.date, a.block.session)
            ):
                assignment_data.append(
                    [
                        str(assignment.block.date),
                        assignment.block.session.upper(),
                        assignment.activity_name,
                        assignment.role,
                    ]
                )

            assignment_table = self.generator._create_table(
                assignment_data,
                col_widths=[1.5 * inch, 1 * inch, 2.5 * inch, 1.5 * inch],
            )
            elements.append(assignment_table)
            elements.append(Spacer(1, 0.15 * inch))

        return elements
