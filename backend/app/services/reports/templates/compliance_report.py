"""ACGME compliance report template."""

import logging
from collections import defaultdict
from datetime import date, timedelta
from typing import Any

from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import PageBreak, Paragraph, Spacer, Table, TableStyle
from sqlalchemy import and_
from sqlalchemy.orm import Session

from app.models.person import Person
from app.scheduling.validator import ACGMEValidator
from app.schemas.reports import ComplianceReportRequest
from app.services.reports.pdf_generator import PDFReportGenerator

logger = logging.getLogger(__name__)


class ComplianceReportTemplate:
    """
    ACGME compliance report template.

    Generates detailed compliance reports showing:
    - Overall compliance status
    - Violations by resident and type
    - 80-hour rule compliance trends
    - 1-in-7 rule compliance
    - Supervision ratio analysis

    Example:
        >>> template = ComplianceReportTemplate(db)
        >>> pdf_bytes = template.generate(request)
    """

    def __init__(self, db: Session):
        """
        Initialize compliance report template.

        Args:
            db: Database session for querying data
        """
        self.db = db
        self.generator = PDFReportGenerator(db)
        self.validator = ACGMEValidator(db)

    def generate(self, request: ComplianceReportRequest) -> bytes:
        """
        Generate ACGME compliance report.

        Args:
            request: Compliance report request with parameters

        Returns:
            PDF content as bytes
        """
        logger.info(
            f"Generating compliance report from {request.start_date} to {request.end_date}"
        )

        # Run validation
        validation_result = self.validator.validate_all(
            request.start_date, request.end_date
        )

        # Get residents
        residents = self._get_residents(request)

        # Build PDF elements
        elements = []

        # Title
        elements.append(
            Paragraph(
                f"ACGME Compliance Report<br/>"
                f"<font size=14>{request.start_date} to {request.end_date}</font>",
                self.generator.styles["ReportTitle"],
            )
        )
        elements.append(Spacer(1, 0.3 * inch))

        # Compliance status overview
        elements.append(
            Paragraph("Compliance Status", self.generator.styles["SectionHeader"])
        )
        elements.extend(self._create_status_section(validation_result))
        elements.append(Spacer(1, 0.2 * inch))

        # Violations summary
        if validation_result.violations:
            elements.append(
                Paragraph("Violations Summary", self.generator.styles["SectionHeader"])
            )
            elements.extend(
                self._create_violations_summary(validation_result.violations)
            )
            elements.append(Spacer(1, 0.2 * inch))

        # Detailed violations by resident
        if validation_result.violations and not request.include_violations_only:
            elements.append(PageBreak())
            elements.append(
                Paragraph("Detailed Violations", self.generator.styles["SectionHeader"])
            )
            elements.extend(
                self._create_detailed_violations(
                    validation_result.violations, residents
                )
            )
        elif not validation_result.violations:
            elements.append(
                Paragraph(
                    "No ACGME violations found for this period. "
                    "All residents are in compliance.",
                    self.generator.styles["ReportBody"],
                )
            )

        # Generate PDF
        return self.generator.generate_pdf(
            elements=elements,
            title="ACGME Compliance Report",
            include_logo=request.include_logo,
            include_page_numbers=request.include_page_numbers,
        )

    def _get_residents(self, request: ComplianceReportRequest) -> list[Person]:
        """Query residents for the report."""
        query = self.db.query(Person).filter(Person.type == "resident")

        if request.resident_ids:
            query = query.filter(Person.id.in_(request.resident_ids))

        if request.pgy_levels:
            query = query.filter(Person.pgy_level.in_(request.pgy_levels))

        return query.order_by(Person.pgy_level, Person.name).all()

    def _create_status_section(self, validation_result: Any) -> list:
        """Create compliance status overview section."""
        elements = []

        # Status indicator
        if validation_result.valid:
            status_text = '<font color="#28a745" size=12><b>✓ COMPLIANT</b></font>'
            status_desc = "All ACGME requirements are met for this period."
        else:
            status_text = '<font color="#dc3545" size=12><b>✗ NON-COMPLIANT</b></font>'
            status_desc = (
                f"Found {validation_result.total_violations} violation(s) "
                "requiring attention."
            )

        elements.append(Paragraph(status_text, self.generator.styles["ReportBody"]))
        elements.append(Spacer(1, 0.1 * inch))
        elements.append(Paragraph(status_desc, self.generator.styles["ReportBody"]))
        elements.append(Spacer(1, 0.15 * inch))

        # Statistics table
        stats_data = [
            ["Metric", "Value"],
            ["Total Violations", str(validation_result.total_violations)],
            [
                "Coverage Rate",
                f"{validation_result.coverage_rate:.1f}%",
            ],
            ["Compliance Status", "PASS" if validation_result.valid else "FAIL"],
        ]

        stats_table = self.generator._create_table(
            stats_data, col_widths=[3.5 * inch, 2 * inch]
        )
        elements.append(stats_table)

        return elements

    def _create_violations_summary(self, violations: list) -> list:
        """Create violations summary section."""
        elements = []

        # Count violations by type and severity
        by_type = defaultdict(int)
        by_severity = defaultdict(int)

        for violation in violations:
            by_type[violation.type] += 1
            by_severity[violation.severity] += 1

        # Violations by type table
        elements.append(
            Paragraph("Violations by Type", self.generator.styles["SubsectionHeader"])
        )

        type_data = [["Violation Type", "Count"]]
        for vtype, count in sorted(by_type.items(), key=lambda x: -x[1]):
            type_data.append([vtype, str(count)])

        type_table = self.generator._create_table(
            type_data, col_widths=[3.5 * inch, 2 * inch]
        )
        elements.append(type_table)
        elements.append(Spacer(1, 0.15 * inch))

        # Violations by severity table
        elements.append(
            Paragraph(
                "Violations by Severity", self.generator.styles["SubsectionHeader"]
            )
        )

        severity_data = [["Severity Level", "Count"]]
        severity_order = ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
        for severity in severity_order:
            if severity in by_severity:
                severity_data.append([severity, str(by_severity[severity])])

        severity_table = self.generator._create_table(
            severity_data, col_widths=[3.5 * inch, 2 * inch]
        )

        # Color-code severity rows
        severity_colors = {
            "CRITICAL": colors.HexColor("#dc3545"),
            "HIGH": colors.HexColor("#fd7e14"),
            "MEDIUM": colors.HexColor("#ffc107"),
            "LOW": colors.HexColor("#17a2b8"),
        }

        style = severity_table.getStyle()
        for i, row in enumerate(severity_data[1:], start=1):
            severity = row[0]
            if severity in severity_colors:
                style.add("TEXTCOLOR", (0, i), (0, i), severity_colors[severity])
                style.add("FONTNAME", (0, i), (0, i), "Helvetica-Bold")

        elements.append(severity_table)

        return elements

    def _create_detailed_violations(
        self, violations: list, residents: list[Person]
    ) -> list:
        """Create detailed violations listing."""
        elements = []

        # Group violations by person
        violations_by_person = defaultdict(list)
        for violation in violations:
            person_id = violation.person_id
            if person_id:
                violations_by_person[person_id].append(violation)

        # Create section for each resident with violations
        resident_map = {r.id: r for r in residents}

        for person_id, person_violations in violations_by_person.items():
            resident = resident_map.get(person_id)
            if not resident:
                continue

            # Resident header
            elements.append(
                Paragraph(
                    f"{resident.name} (PGY-{resident.pgy_level})",
                    self.generator.styles["SubsectionHeader"],
                )
            )

            # Violations table
            violation_data = [["Type", "Severity", "Message"]]

            for violation in person_violations:
                violation_data.append(
                    [
                        violation.type,
                        violation.severity,
                        violation.message[:80] + "..."
                        if len(violation.message) > 80
                        else violation.message,
                    ]
                )

            violation_table = self.generator._create_table(
                violation_data,
                col_widths=[1.5 * inch, 1 * inch, 4 * inch],
            )
            elements.append(violation_table)
            elements.append(Spacer(1, 0.15 * inch))

        # Handle violations without person_id
        orphan_violations = [v for v in violations if not v.person_id]
        if orphan_violations:
            elements.append(
                Paragraph(
                    "System-Level Violations",
                    self.generator.styles["SubsectionHeader"],
                )
            )

            violation_data = [["Type", "Severity", "Message"]]
            for violation in orphan_violations:
                violation_data.append(
                    [
                        violation.type,
                        violation.severity,
                        violation.message[:80] + "..."
                        if len(violation.message) > 80
                        else violation.message,
                    ]
                )

            violation_table = self.generator._create_table(
                violation_data,
                col_widths=[1.5 * inch, 1 * inch, 4 * inch],
            )
            elements.append(violation_table)

        return elements
