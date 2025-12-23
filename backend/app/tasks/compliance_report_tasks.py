"""
Celery tasks for scheduled compliance report generation.

Provides automated compliance report generation and distribution:
- Daily compliance summaries
- Weekly detailed reports
- Monthly executive summaries
- On-demand report generation
- Email distribution to stakeholders
"""

import json
import logging
import os
from datetime import date, datetime, timedelta
from typing import Any

from celery import shared_task
from sqlalchemy import select

from app.compliance.reports import ComplianceReportGenerator
from app.db.session import SessionLocal
from app.models.person import FacultyRole, Person
from app.notifications.tasks import send_email

logger = logging.getLogger(__name__)


def save_report_to_file(report_bytes: bytes, filename: str, report_type: str) -> str:
    """
    Save report to file system and return path.

    Args:
        report_bytes: Report content as bytes
        filename: Desired filename
        report_type: Type of report (for subdirectory organization)

    Returns:
        str: Absolute path to saved file

    Raises:
        IOError: If file cannot be written
    """
    try:
        # Get reports directory from environment or use default
        reports_dir = os.getenv("REPORTS_DIR", "/tmp/reports")

        # Create subdirectory for report type
        type_dir = os.path.join(reports_dir, report_type)
        os.makedirs(type_dir, exist_ok=True)

        # Save file
        filepath = os.path.join(type_dir, filename)
        with open(filepath, "wb") as f:
            f.write(report_bytes)

        logger.info(f"Report saved to: {filepath} ({len(report_bytes)} bytes)")
        return filepath

    except Exception as e:
        logger.error(f"Failed to save report {filename}: {e}")
        raise


def save_report_data_to_json(report_data: dict, report_type: str) -> str:
    """
    Save report data dictionary to JSON file.

    Args:
        report_data: Report data as dictionary
        report_type: Type of report (for filename)

    Returns:
        str: Absolute path to saved JSON file

    Raises:
        IOError: If file cannot be written
    """
    try:
        reports_dir = os.getenv("REPORTS_DIR", "/tmp/reports")
        os.makedirs(reports_dir, exist_ok=True)

        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"{report_type}_{timestamp}.json"
        filepath = os.path.join(reports_dir, filename)

        with open(filepath, "w") as f:
            json.dump(report_data, f, indent=2, default=str)

        logger.info(f"Report data saved to: {filepath}")
        return filepath

    except Exception as e:
        logger.error(f"Failed to save report data: {e}")
        raise


def get_program_directors_emails(db) -> list[str]:
    """
    Get email addresses of all program directors.

    Args:
        db: Database session

    Returns:
        list[str]: List of program director email addresses
    """
    try:
        # Query for faculty with Program Director role
        stmt = select(Person).where(
            Person.type == "faculty",
            Person.faculty_role == FacultyRole.PD.value,
            Person.email.isnot(None),
        )
        result = db.execute(stmt)
        program_directors = result.scalars().all()

        emails = [pd.email for pd in program_directors if pd.email]
        logger.info(f"Found {len(emails)} program director email(s)")
        return emails

    except Exception as e:
        logger.error(f"Failed to query program directors: {e}")
        return []


def get_compliance_stakeholder_emails() -> list[str]:
    """
    Get compliance stakeholder email addresses from configuration.

    Returns:
        list[str]: List of stakeholder email addresses
    """
    # Get from environment or use default
    stakeholders = os.getenv(
        "COMPLIANCE_STAKEHOLDER_EMAILS",
        "compliance@hospital.org,program-director@hospital.org",
    )
    return [email.strip() for email in stakeholders.split(",") if email.strip()]


def get_executive_stakeholder_emails() -> list[str]:
    """
    Get executive stakeholder email addresses from configuration.

    Returns:
        list[str]: List of executive email addresses
    """
    # Get from environment or use default
    executives = os.getenv(
        "EXECUTIVE_STAKEHOLDER_EMAILS",
        "chief-medical-officer@hospital.org,program-director@hospital.org",
    )
    return [email.strip() for email in executives.split(",") if email.strip()]


@shared_task(
    name="app.tasks.compliance_report_tasks.generate_daily_compliance_summary",
    bind=True,
    max_retries=3,
    default_retry_delay=300,  # 5 minutes
)
def generate_daily_compliance_summary(self, lookback_days: int = 1) -> dict[str, Any]:
    """
    Generate daily compliance summary report.

    Runs daily to check compliance for the previous day's schedule.
    Intended for quick monitoring of potential violations.

    Args:
        lookback_days: Number of days to look back (default: 1 = yesterday)

    Returns:
        dict: Task result with report summary

    Example Schedule:
        Run daily at 7 AM:
        schedule = crontab(hour=7, minute=0)
    """
    try:
        db = SessionLocal()
        try:
            end_date = date.today() - timedelta(days=1)
            start_date = end_date - timedelta(days=lookback_days - 1)

            logger.info(
                f"Generating daily compliance summary for {start_date} to {end_date}"
            )

            generator = ComplianceReportGenerator(db)
            report_data = generator.generate_compliance_data(
                start_date=start_date,
                end_date=end_date,
                include_violations_only=False,
            )

            # Extract summary metrics
            summary = {
                "start_date": str(start_date),
                "end_date": str(end_date),
                "total_residents": report_data.work_hour_summary.get(
                    "total_residents", 0
                ),
                "total_violations": report_data.work_hour_summary.get(
                    "total_violations", 0
                ),
                "compliance_rate": report_data.work_hour_summary.get(
                    "compliance_rate", 100
                ),
                "coverage_rate": report_data.coverage_metrics.get(
                    "coverage_rate_percent", 0
                ),
            }

            logger.info(f"Daily compliance summary: {summary}")

            # Send email notification if violations found
            if summary["total_violations"] > 0:
                logger.warning(
                    f"Found {summary['total_violations']} violations in daily summary"
                )

                # Get stakeholder emails
                stakeholder_emails = get_compliance_stakeholder_emails()

                # Send email to each stakeholder
                for email in stakeholder_emails:
                    try:
                        send_email.delay(
                            to=email,
                            subject=f"Compliance Alert: {summary['total_violations']} violation(s) detected",
                            body=f"""Daily Compliance Alert - {end_date}

The following compliance violations were detected in the daily compliance check:

Period: {start_date} to {end_date}
Total Violations: {summary["total_violations"]}
Total Residents: {summary["total_residents"]}
Compliance Rate: {summary["compliance_rate"]:.1f}%
Coverage Rate: {summary["coverage_rate"]:.1f}%

Please review the compliance report and take appropriate action.

This is an automated alert from the Residency Scheduler system.
""",
                            html=None,
                        )
                        logger.info(f"Violation alert email queued for {email}")
                    except Exception as e:
                        logger.error(
                            f"Failed to queue violation alert email for {email}: {e}"
                        )

            return {
                "success": True,
                "message": "Daily compliance summary generated",
                "summary": summary,
            }

        finally:
            db.close()

    except Exception as exc:
        logger.error(f"Failed to generate daily compliance summary: {exc}")
        # Retry with exponential backoff
        raise self.retry(exc=exc)


@shared_task(
    name="app.tasks.compliance_report_tasks.generate_weekly_compliance_report",
    bind=True,
    max_retries=3,
    default_retry_delay=300,
)
def generate_weekly_compliance_report(
    self,
    pgy_levels: list[int] | None = None,
    include_violations_only: bool = False,
    format: str = "pdf",
) -> dict[str, Any]:
    """
    Generate weekly comprehensive compliance report.

    Runs weekly (typically Monday morning) to review the previous week's
    compliance metrics. Generates PDF/Excel report for stakeholders.

    Args:
        pgy_levels: Filter by specific PGY levels (None = all)
        include_violations_only: Only include residents with violations
        format: Export format ('pdf' or 'excel')

    Returns:
        dict: Task result with report details

    Example Schedule:
        Run Monday at 8 AM:
        schedule = crontab(hour=8, minute=0, day_of_week=1)
    """
    try:
        db = SessionLocal()
        try:
            # Previous week (Monday to Sunday)
            today = date.today()
            days_since_monday = today.weekday()
            last_monday = today - timedelta(days=days_since_monday + 7)
            last_sunday = last_monday + timedelta(days=6)

            logger.info(
                f"Generating weekly compliance report for {last_monday} to {last_sunday}"
            )

            generator = ComplianceReportGenerator(db)
            report_data = generator.generate_compliance_data(
                start_date=last_monday,
                end_date=last_sunday,
                pgy_levels=pgy_levels,
                include_violations_only=include_violations_only,
            )

            # Generate report file
            if format == "pdf":
                report_bytes = generator.export_to_pdf(
                    report_data, include_charts=True, include_details=True
                )
            else:
                report_bytes = generator.export_to_excel(
                    report_data, include_charts=True
                )

            filename = f"compliance_report_{last_monday}_{last_sunday}.{format}"

            # Save report to file system
            try:
                filepath = save_report_to_file(
                    report_bytes=report_bytes, filename=filename, report_type="weekly"
                )
            except Exception as e:
                logger.error(f"Failed to save weekly report: {e}")
                filepath = None

            # Send email to stakeholders with attachment
            stakeholder_emails = get_compliance_stakeholder_emails()
            for email in stakeholder_emails:
                try:
                    # Note: Celery send_email task doesn't support attachments yet
                    # For now, send link to report location or inline summary
                    send_email.delay(
                        to=email,
                        subject=f"Weekly Compliance Report - {last_monday} to {last_sunday}",
                        body=f"""Weekly Compliance Report

Report Period: {last_monday} to {last_sunday}
Format: {format.upper()}

Summary:
- Total Residents: {report_data.work_hour_summary.get("total_residents", 0)}
- Total Violations: {report_data.work_hour_summary.get("total_violations", 0)}
- Compliance Rate: {report_data.work_hour_summary.get("compliance_rate", 100):.1f}%

Report File: {filepath if filepath else "Failed to save"}

Please review the compliance report for the past week.

This is an automated report from the Residency Scheduler system.
""",
                        html=None,
                    )
                    logger.info(f"Weekly report email queued for {email}")
                except Exception as e:
                    logger.error(
                        f"Failed to queue weekly report email for {email}: {e}"
                    )

            logger.info(
                f"Weekly compliance report generated: {filename} "
                f"({len(report_bytes)} bytes)"
            )

            return {
                "success": True,
                "message": "Weekly compliance report generated",
                "filename": filename,
                "file_size": len(report_bytes),
                "start_date": str(last_monday),
                "end_date": str(last_sunday),
                "summary": {
                    "total_residents": report_data.work_hour_summary.get(
                        "total_residents", 0
                    ),
                    "total_violations": report_data.work_hour_summary.get(
                        "total_violations", 0
                    ),
                    "compliance_rate": report_data.work_hour_summary.get(
                        "compliance_rate", 100
                    ),
                },
            }

        finally:
            db.close()

    except Exception as exc:
        logger.error(f"Failed to generate weekly compliance report: {exc}")
        raise self.retry(exc=exc)


@shared_task(
    name="app.tasks.compliance_report_tasks.generate_monthly_executive_summary",
    bind=True,
    max_retries=3,
    default_retry_delay=300,
)
def generate_monthly_executive_summary(self) -> dict[str, Any]:
    """
    Generate monthly executive compliance summary.

    Runs monthly (first day of month) to review the previous month's
    compliance trends and metrics. Intended for leadership review.

    Returns:
        dict: Task result with executive summary

    Example Schedule:
        Run 1st of month at 9 AM:
        schedule = crontab(hour=9, minute=0, day_of_month=1)
    """
    try:
        db = SessionLocal()
        try:
            # Previous month
            today = date.today()
            first_of_this_month = today.replace(day=1)
            last_of_prev_month = first_of_this_month - timedelta(days=1)
            first_of_prev_month = last_of_prev_month.replace(day=1)

            logger.info(
                f"Generating monthly executive summary for "
                f"{first_of_prev_month} to {last_of_prev_month}"
            )

            generator = ComplianceReportGenerator(db)
            report_data = generator.generate_compliance_data(
                start_date=first_of_prev_month,
                end_date=last_of_prev_month,
                include_violations_only=False,
            )

            # Generate PDF with charts
            pdf_bytes = generator.export_to_pdf(
                report_data, include_charts=True, include_details=False
            )

            # Generate Excel for data analysis
            excel_bytes = generator.export_to_excel(report_data, include_charts=True)

            filename_pdf = (
                f"executive_summary_{first_of_prev_month.strftime('%Y-%m')}.pdf"
            )
            filename_excel = (
                f"compliance_data_{first_of_prev_month.strftime('%Y-%m')}.xlsx"
            )

            # Save reports to file system
            pdf_filepath = None
            excel_filepath = None

            try:
                pdf_filepath = save_report_to_file(
                    report_bytes=pdf_bytes,
                    filename=filename_pdf,
                    report_type="monthly_executive",
                )
            except Exception as e:
                logger.error(f"Failed to save monthly PDF report: {e}")

            try:
                excel_filepath = save_report_to_file(
                    report_bytes=excel_bytes,
                    filename=filename_excel,
                    report_type="monthly_executive",
                )
            except Exception as e:
                logger.error(f"Failed to save monthly Excel report: {e}")

            # Send email to executive stakeholders
            executive_emails = get_executive_stakeholder_emails()
            for email in executive_emails:
                try:
                    send_email.delay(
                        to=email,
                        subject=f"Monthly Executive Compliance Summary - {first_of_prev_month.strftime('%B %Y')}",
                        body=f"""Monthly Executive Compliance Summary

Report Period: {first_of_prev_month.strftime("%B %Y")} ({first_of_prev_month} to {last_of_prev_month})

Executive Summary:
- Total Residents: {report_data.work_hour_summary.get("total_residents", 0)}
- Total Violations: {report_data.work_hour_summary.get("total_violations", 0)}
- Compliance Rate: {report_data.work_hour_summary.get("compliance_rate", 100):.1f}%
- Average Weekly Hours: {report_data.work_hour_summary.get("avg_weekly_hours", 0):.1f}
- Supervision Compliance: {report_data.supervision_summary.get("compliance_rate", 100):.1f}%

Report Files:
- PDF Report: {pdf_filepath if pdf_filepath else "Failed to save"}
- Excel Data: {excel_filepath if excel_filepath else "Failed to save"}

Please review the monthly compliance summary for leadership review.

This is an automated report from the Residency Scheduler system.
""",
                        html=None,
                    )
                    logger.info(f"Monthly executive report email queued for {email}")
                except Exception as e:
                    logger.error(
                        f"Failed to queue monthly executive email for {email}: {e}"
                    )

            logger.info(
                f"Monthly executive summary generated: {filename_pdf} "
                f"({len(pdf_bytes)} bytes PDF, {len(excel_bytes)} bytes Excel)"
            )

            return {
                "success": True,
                "message": "Monthly executive summary generated",
                "files": {
                    "pdf": {"filename": filename_pdf, "size": len(pdf_bytes)},
                    "excel": {"filename": filename_excel, "size": len(excel_bytes)},
                },
                "period": f"{first_of_prev_month} to {last_of_prev_month}",
                "summary": {
                    "total_residents": report_data.work_hour_summary.get(
                        "total_residents", 0
                    ),
                    "total_violations": report_data.work_hour_summary.get(
                        "total_violations", 0
                    ),
                    "compliance_rate": report_data.work_hour_summary.get(
                        "compliance_rate", 100
                    ),
                    "avg_weekly_hours": report_data.work_hour_summary.get(
                        "avg_weekly_hours", 0
                    ),
                    "supervision_compliance": report_data.supervision_summary.get(
                        "compliance_rate", 100
                    ),
                },
            }

        finally:
            db.close()

    except Exception as exc:
        logger.error(f"Failed to generate monthly executive summary: {exc}")
        raise self.retry(exc=exc)


@shared_task(
    name="app.tasks.compliance_report_tasks.generate_custom_compliance_report",
    bind=True,
    max_retries=3,
    default_retry_delay=300,
)
def generate_custom_compliance_report(
    self,
    start_date: str,
    end_date: str,
    resident_ids: list[str] | None = None,
    pgy_levels: list[int] | None = None,
    include_violations_only: bool = False,
    format: str = "pdf",
    include_charts: bool = True,
    include_details: bool = True,
) -> dict[str, Any]:
    """
    Generate custom compliance report with specific parameters.

    This task can be triggered on-demand via API or scheduled with
    custom parameters for specific reporting needs.

    Args:
        start_date: Report start date (ISO format: YYYY-MM-DD)
        end_date: Report end date (ISO format: YYYY-MM-DD)
        resident_ids: List of resident IDs to include (None = all)
        pgy_levels: List of PGY levels to filter (None = all)
        include_violations_only: Only include residents with violations
        format: Export format ('pdf' or 'excel')
        include_charts: Include trend charts in report
        include_details: Include detailed resident summaries

    Returns:
        dict: Task result with report details

    Example:
        >>> from app.tasks.compliance_report_tasks import (
        ...     generate_custom_compliance_report
        ... )
        >>> result = generate_custom_compliance_report.delay(
        ...     start_date="2025-01-01",
        ...     end_date="2025-01-31",
        ...     pgy_levels=[1],
        ...     format="pdf"
        ... )
        >>> result.get()
    """
    try:
        db = SessionLocal()
        try:
            # Parse dates
            start = date.fromisoformat(start_date)
            end = date.fromisoformat(end_date)

            # Convert resident_ids to UUIDs if provided
            from uuid import UUID

            resident_uuids = None
            if resident_ids:
                resident_uuids = [UUID(rid) for rid in resident_ids]

            logger.info(f"Generating custom compliance report for {start} to {end}")

            generator = ComplianceReportGenerator(db)
            report_data = generator.generate_compliance_data(
                start_date=start,
                end_date=end,
                resident_ids=resident_uuids,
                pgy_levels=pgy_levels,
                include_violations_only=include_violations_only,
            )

            # Generate report
            if format == "pdf":
                report_bytes = generator.export_to_pdf(
                    report_data,
                    include_charts=include_charts,
                    include_details=include_details,
                )
            else:
                report_bytes = generator.export_to_excel(
                    report_data, include_charts=include_charts
                )

            filename = f"compliance_report_{start}_{end}.{format}"

            # Save report to file system and return file path for download
            filepath = None
            try:
                filepath = save_report_to_file(
                    report_bytes=report_bytes, filename=filename, report_type="custom"
                )
            except Exception as e:
                logger.error(f"Failed to save custom report: {e}")

            logger.info(
                f"Custom compliance report generated: {filename} "
                f"({len(report_bytes)} bytes)"
            )

            return {
                "success": True,
                "message": "Custom compliance report generated",
                "filename": filename,
                "filepath": filepath,
                "file_size": len(report_bytes),
                "start_date": str(start),
                "end_date": str(end),
                "parameters": {
                    "resident_ids": resident_ids,
                    "pgy_levels": pgy_levels,
                    "include_violations_only": include_violations_only,
                    "format": format,
                },
                "summary": {
                    "total_residents": report_data.work_hour_summary.get(
                        "total_residents", 0
                    ),
                    "total_violations": report_data.work_hour_summary.get(
                        "total_violations", 0
                    ),
                    "compliance_rate": report_data.work_hour_summary.get(
                        "compliance_rate", 100
                    ),
                },
            }

        finally:
            db.close()

    except Exception as exc:
        logger.error(f"Failed to generate custom compliance report: {exc}")
        raise self.retry(exc=exc)


@shared_task(
    name="app.tasks.compliance_report_tasks.check_violation_alerts",
    bind=True,
    max_retries=3,
    default_retry_delay=300,
)
def check_violation_alerts(self, lookback_days: int = 1) -> dict[str, Any]:
    """
    Check for new compliance violations and send alerts.

    Runs frequently (e.g., every 4 hours) to detect new violations
    and alert program directors immediately.

    Args:
        lookback_days: Number of days to check (default: 1)

    Returns:
        dict: Task result with violation count

    Example Schedule:
        Run every 4 hours:
        schedule = crontab(hour="*/4", minute=0)
    """
    try:
        db = SessionLocal()
        try:
            end_date = date.today()
            start_date = end_date - timedelta(days=lookback_days)

            logger.info(
                f"Checking for compliance violations from {start_date} to {end_date}"
            )

            generator = ComplianceReportGenerator(db)
            report_data = generator.generate_compliance_data(
                start_date=start_date,
                end_date=end_date,
                include_violations_only=True,
            )

            violations = report_data.acgme_violations

            if violations:
                # Critical violations need immediate attention
                critical_violations = [
                    v for v in violations if v.get("severity") == "CRITICAL"
                ]

                logger.warning(
                    f"Found {len(violations)} violations "
                    f"({len(critical_violations)} critical)"
                )

                # Send email alerts to program directors
                pd_emails = get_program_directors_emails(db)

                for email in pd_emails:
                    try:
                        # Format violation details for email
                        violation_details = "\n".join(
                            f"- {v.get('type', 'Unknown')}: {v.get('description', 'No description')} "
                            f"(Severity: {v.get('severity', 'UNKNOWN')})"
                            for v in violations[:10]  # Include first 10
                        )

                        if len(violations) > 10:
                            violation_details += (
                                f"\n... and {len(violations) - 10} more violations"
                            )

                        send_email.delay(
                            to=email,
                            subject=f"URGENT: {len(critical_violations)} Critical Compliance Violation(s) Detected",
                            body=f"""Compliance Violation Alert

URGENT: Compliance violations have been detected that require immediate attention.

Period Checked: {start_date} to {end_date}
Total Violations: {len(violations)}
Critical Violations: {len(critical_violations)}

Violation Details:
{violation_details}

Please review these violations and take appropriate corrective action immediately.

This is an automated alert from the Residency Scheduler system.
""",
                            html=None,
                        )
                        logger.info(
                            f"Critical violation alert email queued for {email}"
                        )
                    except Exception as e:
                        logger.error(
                            f"Failed to queue violation alert email for {email}: {e}"
                        )

                # Create in-app notifications for program directors
                from app.models.notification import Notification

                # Query program directors for in-app notifications
                stmt = select(Person).where(
                    Person.type == "faculty",
                    Person.faculty_role == FacultyRole.PD.value,
                )
                result = db.execute(stmt)
                program_directors = result.scalars().all()

                for pd in program_directors:
                    try:
                        # Create notification record
                        notification = Notification(
                            recipient_id=pd.id,
                            notification_type="COMPLIANCE_ALERT",
                            subject="Critical Compliance Issues Detected",
                            body=f"{len(critical_violations)} critical and {len(violations) - len(critical_violations)} "
                            f"total compliance violations detected between {start_date} and {end_date}. "
                            f"Immediate review required.",
                            priority="high",
                            data={
                                "violation_count": len(violations),
                                "critical_count": len(critical_violations),
                                "start_date": str(start_date),
                                "end_date": str(end_date),
                                "violations": violations[
                                    :5
                                ],  # Include first 5 for quick view
                            },
                        )
                        db.add(notification)
                        logger.info(
                            f"Created in-app notification for program director {pd.id}"
                        )
                    except Exception as e:
                        logger.error(
                            f"Failed to create in-app notification for PD {pd.id}: {e}"
                        )

                # Commit all notifications
                try:
                    db.commit()
                    logger.info(
                        f"Created {len(program_directors)} in-app notifications for program directors"
                    )
                except Exception as e:
                    logger.error(f"Failed to commit in-app notifications: {e}")
                    db.rollback()

                return {
                    "success": True,
                    "message": f"Found {len(violations)} violations",
                    "violations_found": len(violations),
                    "critical_violations": len(critical_violations),
                    "violations": violations[:10],  # Include first 10
                }
            else:
                logger.info("No compliance violations found")
                return {
                    "success": True,
                    "message": "No violations found",
                    "violations_found": 0,
                    "critical_violations": 0,
                }

        finally:
            db.close()

    except Exception as exc:
        logger.error(f"Failed to check violation alerts: {exc}")
        raise self.retry(exc=exc)
