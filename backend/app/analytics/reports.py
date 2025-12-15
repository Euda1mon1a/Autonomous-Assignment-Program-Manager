"""Report generation and export for analytics data."""
import csv
import io
from datetime import date, datetime, timedelta
from enum import Enum
from typing import Optional, Dict, List, Any, Literal

from sqlalchemy.orm import Session

from app.analytics.service import AnalyticsService


class ReportType(str, Enum):
    """Available report types."""
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    CUSTOM = "custom"


class ReportFormat(str, Enum):
    """Available export formats."""
    JSON = "json"
    CSV = "csv"


class ReportGenerator:
    """
    Generate reports for schedule analytics.

    Provides:
    - Report generation (weekly, monthly, quarterly)
    - Export formats (JSON, CSV)
    - Report scheduling
    - Custom date range reports
    """

    def __init__(self, db: Session):
        """Initialize the report generator."""
        self.db = db
        self.analytics = AnalyticsService(db)

    def generate_report(
        self,
        report_type: ReportType,
        reference_date: Optional[date] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> Dict[str, Any]:
        """
        Generate a report of the specified type.

        Args:
            report_type: Type of report to generate
            reference_date: Reference date for relative reports (weekly, monthly, quarterly)
            start_date: Start date for custom reports
            end_date: End date for custom reports

        Returns:
            Dictionary containing report data
        """
        # Determine date range based on report type
        if report_type == ReportType.CUSTOM:
            if not start_date or not end_date:
                raise ValueError("Custom reports require start_date and end_date")
            report_start = start_date
            report_end = end_date
        else:
            if not reference_date:
                reference_date = date.today()
            report_start, report_end = self._get_date_range(report_type, reference_date)

        # Generate report data
        report_data = {
            "report_type": report_type.value,
            "date_range": {
                "start_date": report_start.isoformat(),
                "end_date": report_end.isoformat(),
            },
            "generated_at": datetime.utcnow().isoformat(),
            "sections": {},
        }

        # Collect all analytics data
        report_data["sections"]["overview"] = self.analytics.get_overview_metrics(
            report_start, report_end
        )
        report_data["sections"]["workload"] = self.analytics.get_person_workload(
            report_start, report_end
        )
        report_data["sections"]["absences"] = self.analytics.get_absence_patterns(
            report_start, report_end
        )
        report_data["sections"]["compliance"] = self.analytics.get_compliance_metrics(
            report_start, report_end
        )
        report_data["sections"]["utilization"] = self.analytics.get_utilization_metrics(
            report_start, report_end
        )

        return report_data

    def export_report(
        self,
        report_data: Dict[str, Any],
        format: ReportFormat,
    ) -> str:
        """
        Export report data in the specified format.

        Args:
            report_data: Report data to export
            format: Export format (JSON or CSV)

        Returns:
            Exported report as string
        """
        if format == ReportFormat.JSON:
            return self._export_json(report_data)
        elif format == ReportFormat.CSV:
            return self._export_csv(report_data)
        else:
            raise ValueError(f"Unsupported export format: {format}")

    def generate_weekly_report(
        self,
        reference_date: Optional[date] = None,
    ) -> Dict[str, Any]:
        """
        Generate a weekly report (Monday-Sunday).

        Args:
            reference_date: Date within the week to report on (defaults to today)

        Returns:
            Weekly report data
        """
        return self.generate_report(
            report_type=ReportType.WEEKLY,
            reference_date=reference_date,
        )

    def generate_monthly_report(
        self,
        reference_date: Optional[date] = None,
    ) -> Dict[str, Any]:
        """
        Generate a monthly report.

        Args:
            reference_date: Date within the month to report on (defaults to today)

        Returns:
            Monthly report data
        """
        return self.generate_report(
            report_type=ReportType.MONTHLY,
            reference_date=reference_date,
        )

    def generate_quarterly_report(
        self,
        reference_date: Optional[date] = None,
    ) -> Dict[str, Any]:
        """
        Generate a quarterly report (3 months).

        Args:
            reference_date: Date within the quarter to report on (defaults to today)

        Returns:
            Quarterly report data
        """
        return self.generate_report(
            report_type=ReportType.QUARTERLY,
            reference_date=reference_date,
        )

    def generate_custom_report(
        self,
        start_date: date,
        end_date: date,
    ) -> Dict[str, Any]:
        """
        Generate a custom date range report.

        Args:
            start_date: Report start date
            end_date: Report end date

        Returns:
            Custom report data
        """
        return self.generate_report(
            report_type=ReportType.CUSTOM,
            start_date=start_date,
            end_date=end_date,
        )

    def _get_date_range(
        self,
        report_type: ReportType,
        reference_date: date,
    ) -> tuple[date, date]:
        """
        Calculate date range for a report type.

        Args:
            report_type: Type of report
            reference_date: Reference date

        Returns:
            Tuple of (start_date, end_date)
        """
        if report_type == ReportType.WEEKLY:
            # Get Monday of the reference week
            days_since_monday = reference_date.weekday()
            start_date = reference_date - timedelta(days=days_since_monday)
            end_date = start_date + timedelta(days=6)  # Sunday
            return start_date, end_date

        elif report_type == ReportType.MONTHLY:
            # Get first and last day of the reference month
            start_date = reference_date.replace(day=1)
            # Get last day of month
            if reference_date.month == 12:
                next_month = reference_date.replace(year=reference_date.year + 1, month=1, day=1)
            else:
                next_month = reference_date.replace(month=reference_date.month + 1, day=1)
            end_date = next_month - timedelta(days=1)
            return start_date, end_date

        elif report_type == ReportType.QUARTERLY:
            # Get quarter boundaries
            quarter = (reference_date.month - 1) // 3
            first_month = quarter * 3 + 1
            start_date = reference_date.replace(month=first_month, day=1)

            # Get last day of quarter
            last_month = first_month + 2
            if last_month > 12:
                next_quarter = start_date.replace(
                    year=start_date.year + 1,
                    month=1,
                    day=1
                )
            else:
                if last_month == 12:
                    next_quarter = start_date.replace(
                        year=start_date.year + 1,
                        month=1,
                        day=1
                    )
                else:
                    next_quarter = start_date.replace(month=last_month + 1, day=1)

            end_date = next_quarter - timedelta(days=1)
            return start_date, end_date

        else:
            raise ValueError(f"Unsupported report type: {report_type}")

    def _export_json(self, report_data: Dict[str, Any]) -> str:
        """
        Export report as JSON string.

        Args:
            report_data: Report data to export

        Returns:
            JSON string
        """
        import json
        return json.dumps(report_data, indent=2, default=str)

    def _export_csv(self, report_data: Dict[str, Any]) -> str:
        """
        Export report as CSV string.

        Creates multiple CSV sections for different report parts:
        - Overview metrics
        - Workload by person
        - Absence summary

        Args:
            report_data: Report data to export

        Returns:
            CSV string
        """
        output = io.StringIO()
        writer = csv.writer(output)

        # Header
        writer.writerow(["Analytics Report"])
        writer.writerow([f"Report Type: {report_data['report_type']}"])
        writer.writerow([
            f"Date Range: {report_data['date_range']['start_date']} to {report_data['date_range']['end_date']}"
        ])
        writer.writerow([f"Generated: {report_data['generated_at']}"])
        writer.writerow([])

        sections = report_data.get("sections", {})

        # Overview Section
        if "overview" in sections:
            overview = sections["overview"]
            writer.writerow(["OVERVIEW METRICS"])
            writer.writerow([])

            # Coverage
            coverage = overview.get("coverage", {})
            writer.writerow(["Coverage"])
            writer.writerow(["Total Blocks", coverage.get("total_blocks", 0)])
            writer.writerow(["Total Assignments", coverage.get("total_assignments", 0)])
            writer.writerow(["Coverage Rate (%)", coverage.get("coverage_rate", 0)])
            writer.writerow([])

            # Workload
            workload = overview.get("workload", {})
            writer.writerow(["Workload"])
            writer.writerow(["Total Residents", workload.get("total_residents", 0)])
            writer.writerow(["Avg Blocks/Resident", workload.get("average_blocks_per_resident", 0)])
            writer.writerow([])

            # Compliance
            compliance = overview.get("compliance", {})
            writer.writerow(["Compliance"])
            writer.writerow(["Compliance Rate (%)", compliance.get("compliance_rate", 0)])
            writer.writerow(["Avg Violations", compliance.get("average_violations", 0)])
            writer.writerow(["Success Rate (%)", compliance.get("schedule_success_rate", 0)])
            writer.writerow([])

        # Workload Section
        if "workload" in sections:
            workload_data = sections["workload"]
            writer.writerow(["WORKLOAD BY PERSON"])
            writer.writerow([])
            writer.writerow([
                "Person Name",
                "PGY Level",
                "Total Blocks",
                "Target Blocks",
                "Utilization (%)",
                "Weekend",
                "Holiday",
            ])

            for person in workload_data:
                stats = person.get("statistics", {})
                writer.writerow([
                    person.get("person_name", ""),
                    person.get("pgy_level", ""),
                    stats.get("total_blocks", 0),
                    stats.get("target_blocks", 0),
                    stats.get("utilization_percentage", 0),
                    stats.get("weekend_assignments", 0),
                    stats.get("holiday_assignments", 0),
                ])
            writer.writerow([])

        # Absence Section
        if "absences" in sections:
            absences = sections["absences"]
            summary = absences.get("summary", {})

            writer.writerow(["ABSENCE SUMMARY"])
            writer.writerow([])
            writer.writerow(["Total Absences", summary.get("total_absences", 0)])
            writer.writerow(["Total Days", summary.get("total_days", 0)])
            writer.writerow(["Military Absences", summary.get("military_absences", 0)])
            writer.writerow(["Military Days", summary.get("military_days", 0)])
            writer.writerow(["Blocking Absences", summary.get("blocking_absences", 0)])
            writer.writerow([])

            # Absence by person
            by_person = absences.get("by_person", [])
            if by_person:
                writer.writerow(["ABSENCE BY PERSON"])
                writer.writerow([])
                writer.writerow([
                    "Person Name",
                    "Total Absences",
                    "Total Days",
                ])

                for person in by_person:
                    writer.writerow([
                        person.get("person_name", ""),
                        person.get("total_absences", 0),
                        person.get("total_days", 0),
                    ])
                writer.writerow([])

        # Compliance Section
        if "compliance" in sections:
            compliance_data = sections["compliance"]
            summary = compliance_data.get("summary", {})

            writer.writerow(["COMPLIANCE METRICS"])
            writer.writerow([])
            writer.writerow(["Total Runs", summary.get("total_runs", 0)])
            writer.writerow(["Successful Runs", summary.get("successful_runs", 0)])
            writer.writerow(["Success Rate (%)", summary.get("success_rate", 0)])
            writer.writerow(["Avg Violations", summary.get("average_violations", 0)])
            writer.writerow(["Total Overrides", summary.get("total_overrides", 0)])
            writer.writerow([])

        # Utilization Section
        if "utilization" in sections:
            utilization = sections["utilization"]
            summary = utilization.get("summary", {})

            writer.writerow(["UTILIZATION METRICS"])
            writer.writerow([])
            writer.writerow(["Total Blocks", summary.get("total_blocks", 0)])
            writer.writerow(["Total Assignments", summary.get("total_assignments", 0)])
            writer.writerow(["Overall Utilization (%)", summary.get("overall_utilization", 0)])
            writer.writerow([])

            # By day type
            by_day = utilization.get("by_day_type", {})
            writer.writerow(["UTILIZATION BY DAY TYPE"])
            writer.writerow([])
            writer.writerow(["Day Type", "Blocks", "Assignments", "Utilization (%)"])

            for day_type, data in by_day.items():
                writer.writerow([
                    day_type.title(),
                    data.get("blocks", 0),
                    data.get("assignments", 0),
                    data.get("utilization", 0),
                ])
            writer.writerow([])

        return output.getvalue()

    def schedule_report(
        self,
        report_type: ReportType,
        frequency: Literal["daily", "weekly", "monthly"],
    ) -> Dict[str, Any]:
        """
        Configure a scheduled report.

        Note: This is a placeholder for future implementation of
        scheduled report generation (would require a task queue).

        Args:
            report_type: Type of report to schedule
            frequency: How often to generate the report

        Returns:
            Schedule configuration
        """
        return {
            "report_type": report_type.value,
            "frequency": frequency,
            "status": "scheduled",
            "message": "Report scheduling configured. Implementation requires task queue setup.",
        }
