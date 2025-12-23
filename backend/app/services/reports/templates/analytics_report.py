"""Workload analytics report template."""
import logging
import statistics
from collections import Counter, defaultdict
from typing import Any

from reportlab.lib.units import inch
from reportlab.platypus import PageBreak, Paragraph, Spacer, Table
from sqlalchemy import and_, func
from sqlalchemy.orm import Session, joinedload

from app.models.assignment import Assignment
from app.models.block import Block
from app.models.person import Person
from app.schemas.reports import AnalyticsReportRequest
from app.services.reports.pdf_generator import PDFReportGenerator

logger = logging.getLogger(__name__)


class AnalyticsReportTemplate:
    """
    Workload analytics report template.

    Generates comprehensive analytics reports showing:
    - Workload distribution statistics
    - Fairness metrics (Gini coefficient, standard deviation)
    - Rotation distribution analysis
    - Faculty supervision metrics
    - Trending data (if historical data available)

    Example:
        >>> template = AnalyticsReportTemplate(db)
        >>> pdf_bytes = template.generate(request)
    """

    def __init__(self, db: Session):
        """
        Initialize analytics report template.

        Args:
            db: Database session for querying data
        """
        self.db = db
        self.generator = PDFReportGenerator(db)

    def generate(self, request: AnalyticsReportRequest) -> bytes:
        """
        Generate workload analytics report.

        Args:
            request: Analytics report request with parameters

        Returns:
            PDF content as bytes
        """
        logger.info(
            f"Generating analytics report from {request.start_date} to {request.end_date}"
        )

        # Collect analytics data
        workload_data = self._get_workload_data(request)
        fairness_metrics = self._calculate_fairness_metrics(workload_data)
        rotation_data = self._get_rotation_distribution(request)
        faculty_data = self._get_faculty_metrics(request)

        # Build PDF elements
        elements = []

        # Title
        elements.append(
            Paragraph(
                f"Workload Analytics Report<br/>"
                f"<font size=14>{request.start_date} to {request.end_date}</font>",
                self.generator.styles["ReportTitle"],
            )
        )
        elements.append(Spacer(1, 0.3 * inch))

        # Executive summary
        elements.append(
            Paragraph("Executive Summary", self.generator.styles["SectionHeader"])
        )
        elements.extend(
            self._create_summary_section(workload_data, fairness_metrics)
        )
        elements.append(Spacer(1, 0.2 * inch))

        # Workload distribution
        elements.append(
            Paragraph(
                "Workload Distribution", self.generator.styles["SectionHeader"]
            )
        )
        elements.extend(self._create_workload_section(workload_data))
        elements.append(Spacer(1, 0.2 * inch))

        # Fairness metrics
        if request.include_fairness_metrics:
            elements.append(
                Paragraph("Fairness Metrics", self.generator.styles["SectionHeader"])
            )
            elements.extend(self._create_fairness_section(fairness_metrics))
            elements.append(Spacer(1, 0.2 * inch))

        # Rotation distribution
        elements.append(PageBreak())
        elements.append(
            Paragraph(
                "Rotation Distribution", self.generator.styles["SectionHeader"]
            )
        )
        elements.extend(self._create_rotation_section(rotation_data))
        elements.append(Spacer(1, 0.2 * inch))

        # Faculty metrics
        elements.append(
            Paragraph(
                "Faculty Supervision Metrics", self.generator.styles["SectionHeader"]
            )
        )
        elements.extend(self._create_faculty_section(faculty_data))

        # Generate PDF
        return self.generator.generate_pdf(
            elements=elements,
            title="Workload Analytics Report",
            include_logo=request.include_logo,
            include_page_numbers=request.include_page_numbers,
        )

    def _get_workload_data(
        self, request: AnalyticsReportRequest
    ) -> dict[str, dict[str, Any]]:
        """Calculate workload data per person."""
        # Query assignments
        assignments = (
            self.db.query(Assignment)
            .join(Block)
            .options(joinedload(Assignment.person))
            .filter(
                and_(
                    Block.date >= request.start_date,
                    Block.date <= request.end_date,
                )
            )
            .all()
        )

        # Count assignments per person
        workload = defaultdict(lambda: {"assignments": 0, "name": "", "type": ""})

        for assignment in assignments:
            if assignment.person:
                person_id = str(assignment.person.id)
                workload[person_id]["assignments"] += 1
                workload[person_id]["name"] = assignment.person.name
                workload[person_id]["type"] = assignment.person.type

        return dict(workload)

    def _calculate_fairness_metrics(
        self, workload_data: dict[str, dict[str, Any]]
    ) -> dict[str, Any]:
        """Calculate fairness metrics from workload data."""
        if not workload_data:
            return {
                "gini_coefficient": 0.0,
                "std_deviation": 0.0,
                "mean": 0.0,
                "median": 0.0,
                "min": 0,
                "max": 0,
            }

        assignment_counts = [data["assignments"] for data in workload_data.values()]

        # Calculate Gini coefficient
        gini = self._calculate_gini(assignment_counts)

        return {
            "gini_coefficient": gini,
            "std_deviation": statistics.stdev(assignment_counts)
            if len(assignment_counts) > 1
            else 0.0,
            "mean": statistics.mean(assignment_counts),
            "median": statistics.median(assignment_counts),
            "min": min(assignment_counts),
            "max": max(assignment_counts),
        }

    def _calculate_gini(self, values: list[float]) -> float:
        """
        Calculate Gini coefficient for fairness measurement.

        A Gini coefficient of 0 represents perfect equality,
        while 1 represents maximal inequality.
        """
        if not values or len(values) == 1:
            return 0.0

        sorted_values = sorted(values)
        n = len(sorted_values)
        cumsum = 0.0
        for i, value in enumerate(sorted_values):
            cumsum += (i + 1) * value

        return (2 * cumsum) / (n * sum(sorted_values)) - (n + 1) / n

    def _get_rotation_distribution(
        self, request: AnalyticsReportRequest
    ) -> dict[str, int]:
        """Get distribution of assignments across rotations."""
        assignments = (
            self.db.query(Assignment)
            .join(Block)
            .options(joinedload(Assignment.rotation_template))
            .filter(
                and_(
                    Block.date >= request.start_date,
                    Block.date <= request.end_date,
                )
            )
            .all()
        )

        rotation_counts = Counter()
        for assignment in assignments:
            rotation_name = assignment.activity_name
            rotation_counts[rotation_name] += 1

        return dict(rotation_counts)

    def _get_faculty_metrics(self, request: AnalyticsReportRequest) -> dict[str, Any]:
        """Calculate faculty supervision metrics."""
        faculty = self.db.query(Person).filter(Person.type == "faculty").all()
        residents = self.db.query(Person).filter(Person.type == "resident").all()

        faculty_assignments = (
            self.db.query(Assignment)
            .join(Block)
            .join(Person)
            .filter(
                and_(
                    Block.date >= request.start_date,
                    Block.date <= request.end_date,
                    Person.type == "faculty",
                )
            )
            .count()
        )

        resident_assignments = (
            self.db.query(Assignment)
            .join(Block)
            .join(Person)
            .filter(
                and_(
                    Block.date >= request.start_date,
                    Block.date <= request.end_date,
                    Person.type == "resident",
                )
            )
            .count()
        )

        return {
            "total_faculty": len(faculty),
            "total_residents": len(residents),
            "faculty_assignments": faculty_assignments,
            "resident_assignments": resident_assignments,
            "supervision_ratio": resident_assignments / max(faculty_assignments, 1),
        }

    def _create_summary_section(
        self, workload_data: dict[str, dict[str, Any]], fairness_metrics: dict[str, Any]
    ) -> list:
        """Create executive summary section."""
        elements = []

        total_people = len(workload_data)
        total_assignments = sum(data["assignments"] for data in workload_data.values())

        elements.append(
            Paragraph(
                f"This analytics report analyzes workload distribution across "
                f"{total_people} individuals with {total_assignments} total assignments. "
                f"The Gini coefficient of {fairness_metrics['gini_coefficient']:.3f} "
                f"indicates {'good' if fairness_metrics['gini_coefficient'] < 0.2 else 'moderate' if fairness_metrics['gini_coefficient'] < 0.4 else 'concerning'} "
                f"fairness in workload distribution.",
                self.generator.styles["ReportBody"],
            )
        )

        return elements

    def _create_workload_section(self, workload_data: dict[str, dict[str, Any]]) -> list:
        """Create workload distribution section."""
        elements = []

        if not workload_data:
            elements.append(
                Paragraph(
                    "No workload data available for this period.",
                    self.generator.styles["ReportBody"],
                )
            )
            return elements

        # Sort by assignment count (descending)
        sorted_workload = sorted(
            workload_data.items(),
            key=lambda x: x[1]["assignments"],
            reverse=True,
        )

        # Workload table
        workload_table_data = [["Name", "Type", "Assignments"]]

        for person_id, data in sorted_workload:
            workload_table_data.append([
                data["name"],
                data["type"].upper(),
                str(data["assignments"]),
            ])

        workload_table = self.generator._create_table(
            workload_table_data,
            col_widths=[2.5 * inch, 1.5 * inch, 1.5 * inch],
        )
        elements.append(workload_table)

        return elements

    def _create_fairness_section(self, fairness_metrics: dict[str, Any]) -> list:
        """Create fairness metrics section."""
        elements = []

        elements.append(
            Paragraph(
                "Fairness metrics help identify potential inequities in workload "
                "distribution. Lower values indicate more equitable distribution.",
                self.generator.styles["ReportBody"],
            )
        )
        elements.append(Spacer(1, 0.1 * inch))

        # Fairness metrics table
        metrics_data = [
            ["Metric", "Value", "Interpretation"],
            [
                "Gini Coefficient",
                f"{fairness_metrics['gini_coefficient']:.3f}",
                "0=perfect equality, 1=max inequality",
            ],
            [
                "Std Deviation",
                f"{fairness_metrics['std_deviation']:.2f}",
                "Lower is more consistent",
            ],
            ["Mean Assignments", f"{fairness_metrics['mean']:.1f}", "Average workload"],
            [
                "Median Assignments",
                f"{fairness_metrics['median']:.1f}",
                "Middle value",
            ],
            ["Min Assignments", str(fairness_metrics["min"]), "Lowest workload"],
            ["Max Assignments", str(fairness_metrics["max"]), "Highest workload"],
        ]

        metrics_table = self.generator._create_table(
            metrics_data,
            col_widths=[2 * inch, 1.5 * inch, 3 * inch],
        )
        elements.append(metrics_table)

        return elements

    def _create_rotation_section(self, rotation_data: dict[str, int]) -> list:
        """Create rotation distribution section."""
        elements = []

        if not rotation_data:
            elements.append(
                Paragraph(
                    "No rotation data available for this period.",
                    self.generator.styles["ReportBody"],
                )
            )
            return elements

        # Sort by count (descending)
        sorted_rotations = sorted(
            rotation_data.items(), key=lambda x: x[1], reverse=True
        )

        # Rotation table
        rotation_table_data = [["Rotation/Activity", "Assignments", "Percentage"]]

        total_assignments = sum(rotation_data.values())

        for rotation_name, count in sorted_rotations:
            percentage = (count / total_assignments * 100) if total_assignments > 0 else 0
            rotation_table_data.append([
                rotation_name,
                str(count),
                f"{percentage:.1f}%",
            ])

        rotation_table = self.generator._create_table(
            rotation_table_data,
            col_widths=[3 * inch, 1.5 * inch, 1.5 * inch],
        )
        elements.append(rotation_table)

        return elements

    def _create_faculty_section(self, faculty_data: dict[str, Any]) -> list:
        """Create faculty supervision metrics section."""
        elements = []

        elements.append(
            Paragraph(
                "Faculty supervision metrics ensure adequate oversight and mentorship "
                "for resident training.",
                self.generator.styles["ReportBody"],
            )
        )
        elements.append(Spacer(1, 0.1 * inch))

        # Faculty metrics table
        faculty_metrics_data = [
            ["Metric", "Value"],
            ["Total Faculty", str(faculty_data["total_faculty"])],
            ["Total Residents", str(faculty_data["total_residents"])],
            ["Faculty Assignments", str(faculty_data["faculty_assignments"])],
            ["Resident Assignments", str(faculty_data["resident_assignments"])],
            [
                "Supervision Ratio",
                f"{faculty_data['supervision_ratio']:.2f}:1",
            ],
        ]

        faculty_table = self.generator._create_table(
            faculty_metrics_data,
            col_widths=[3 * inch, 2.5 * inch],
        )
        elements.append(faculty_table)

        return elements
