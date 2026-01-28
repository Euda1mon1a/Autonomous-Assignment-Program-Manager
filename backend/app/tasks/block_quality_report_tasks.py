"""
Celery tasks for block quality report generation.

Provides automated and on-demand block quality report generation:
- Single block reports
- Multi-block reports with summary
- Scheduled generation at block transitions
"""

import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any

from celery import shared_task

from app.db.session import SessionLocal
from app.services.block_quality_report_service import BlockQualityReportService

logger = logging.getLogger(__name__)


def get_reports_directory() -> Path:
    """Get the reports output directory."""
    reports_dir = os.getenv("REPORTS_DIR", "/tmp/reports/block_quality")
    path = Path(reports_dir)
    path.mkdir(parents=True, exist_ok=True)
    return path


@shared_task(
    name="app.tasks.block_quality_report_tasks.generate_block_quality_report",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
)
def generate_block_quality_report(
    self,
    block_number: int,
    academic_year: int | None = None,
    output_format: str = "markdown",
    save_to_file: bool = True,
) -> dict[str, Any]:
    """
    Generate quality report for a single block.

    Args:
        block_number: Block number (1-13)
        academic_year: Academic year (auto-detects if not provided)
        output_format: Output format ('markdown', 'json', or 'summary')
        save_to_file: Whether to save report to file system

    Returns:
        dict: Task result with report summary and file path (if saved)

    Example:
        # Async call
        result = generate_block_quality_report.delay(block_number=10)

        # Check result
        if result.ready():
            print(result.get())
    """
    try:
        if academic_year is None:
            today = datetime.now().date()
            academic_year = today.year if today.month >= 7 else today.year - 1
        logger.info(
            f"Generating quality report for Block {block_number}, AY {academic_year}"
        )

        db = SessionLocal()
        try:
            service = BlockQualityReportService(db)
            report = service.generate_report(block_number, academic_year)

            # Prepare output
            result = {
                "success": True,
                "block_number": block_number,
                "academic_year": academic_year,
                "total_assignments": report.executive_summary.total_assignments,
                "resident_assignments": report.executive_summary.resident_assignments,
                "faculty_assignments": report.executive_summary.faculty_assignments,
                "status": report.executive_summary.overall_status,
                "acgme_compliance": report.executive_summary.acgme_compliance_rate,
                "nf_one_in_seven": report.executive_summary.nf_one_in_seven,
                "post_call_pcat_do": report.executive_summary.post_call_pcat_do,
            }

            # Save to file if requested
            if save_to_file:
                reports_dir = get_reports_directory()
                date_str = datetime.now().strftime("%Y%m%d")

                if output_format == "markdown":
                    content = service.to_markdown(report)
                    filename = f"BLOCK_{block_number}_QUALITY_REPORT_{date_str}.md"
                elif output_format == "json":
                    content = report.model_dump_json(indent=2)
                    filename = f"BLOCK_{block_number}_QUALITY_REPORT_{date_str}.json"
                else:
                    # Summary format - just return the dict
                    result["file_path"] = None
                    return result

                filepath = reports_dir / filename
                with open(filepath, "w") as f:
                    f.write(content)

                result["file_path"] = str(filepath)
                logger.info(f"Report saved to {filepath}")

            return result

        finally:
            db.close()

    except Exception as exc:
        logger.error(f"Failed to generate block quality report: {exc}")
        raise self.retry(exc=exc)


@shared_task(
    name="app.tasks.block_quality_report_tasks.generate_multi_block_report",
    bind=True,
    max_retries=3,
    default_retry_delay=120,
)
def generate_multi_block_report(
    self,
    block_numbers: list[int],
    academic_year: int | None = None,
    include_summary: bool = True,
    output_format: str = "markdown",
    save_to_file: bool = True,
) -> dict[str, Any]:
    """
    Generate quality reports for multiple blocks with optional summary.

    Args:
        block_numbers: List of block numbers
        academic_year: Academic year (auto-detects if not provided)
        include_summary: Whether to generate cross-block summary
        output_format: Output format ('markdown' or 'json')
        save_to_file: Whether to save reports to file system

    Returns:
        dict: Task result with individual and summary report info

    Example:
        result = generate_multi_block_report.delay(
            block_numbers=[10, 11, 12, 13],
            include_summary=True
        )
    """
    try:
        if academic_year is None:
            today = datetime.now().date()
            academic_year = today.year if today.month >= 7 else today.year - 1
        logger.info(
            f"Generating quality reports for blocks {block_numbers}, AY {academic_year}"
        )

        db = SessionLocal()
        try:
            service = BlockQualityReportService(db)
            reports_dir = get_reports_directory()
            date_str = datetime.now().strftime("%Y%m%d")

            block_results = []
            total_assignments = 0

            # Generate individual reports
            for block_num in block_numbers:
                logger.info(f"  Processing Block {block_num}...")

                try:
                    report = service.generate_report(block_num, academic_year)

                    block_result = {
                        "block_number": block_num,
                        "total": report.executive_summary.total_assignments,
                        "status": report.executive_summary.overall_status,
                        "success": True,
                    }

                    total_assignments += report.executive_summary.total_assignments

                    # Save individual report
                    if save_to_file:
                        if output_format == "markdown":
                            content = service.to_markdown(report)
                            filename = f"BLOCK_{block_num}_QUALITY_REPORT_{date_str}.md"
                        else:
                            content = report.model_dump_json(indent=2)
                            filename = (
                                f"BLOCK_{block_num}_QUALITY_REPORT_{date_str}.json"
                            )

                        filepath = reports_dir / filename
                        with open(filepath, "w") as f:
                            f.write(content)
                        block_result["file_path"] = str(filepath)

                    block_results.append(block_result)

                except Exception as e:
                    logger.error(f"Failed to process Block {block_num}: {e}")
                    block_results.append(
                        {
                            "block_number": block_num,
                            "success": False,
                            "error": str(e),
                        }
                    )

            result = {
                "success": True,
                "blocks": block_results,
                "total_assignments": total_assignments,
                "blocks_processed": len([b for b in block_results if b.get("success")]),
                "blocks_failed": len(
                    [b for b in block_results if not b.get("success")]
                ),
            }

            # Generate summary if requested
            if include_summary and len(block_numbers) > 1:
                logger.info("Generating cross-block summary...")

                try:
                    summary = service.generate_summary(block_numbers, academic_year)

                    if save_to_file:
                        if output_format == "markdown":
                            content = service.summary_to_markdown(summary)
                            filename = f"BLOCKS_{min(block_numbers)}-{max(block_numbers)}_SUMMARY_{date_str}.md"
                        else:
                            content = summary.model_dump_json(indent=2)
                            filename = f"BLOCKS_{min(block_numbers)}-{max(block_numbers)}_SUMMARY_{date_str}.json"

                        filepath = reports_dir / filename
                        with open(filepath, "w") as f:
                            f.write(content)

                        result["summary_file_path"] = str(filepath)

                    result["summary_status"] = summary.overall_status
                    result["gaps_identified"] = summary.gaps_identified

                except Exception as e:
                    logger.error(f"Failed to generate summary: {e}")
                    result["summary_error"] = str(e)

            return result

        finally:
            db.close()

    except Exception as exc:
        logger.error(f"Failed to generate multi-block report: {exc}")
        raise self.retry(exc=exc)


@shared_task(name="app.tasks.block_quality_report_tasks.check_block_schedule_quality")
def check_block_schedule_quality(
    block_number: int,
    academic_year: int | None = None,
) -> dict[str, Any]:
    """
    Quick quality check for a block (no file output).

    Intended for health monitoring and alerts.

    Args:
        block_number: Block number to check
        academic_year: Academic year (auto-detects if not provided)

    Returns:
        dict: Quality check result with pass/fail status
    """
    try:
        if academic_year is None:
            today = datetime.now().date()
            academic_year = today.year if today.month >= 7 else today.year - 1
        db = SessionLocal()
        try:
            service = BlockQualityReportService(db)
            report = service.generate_report(block_number, academic_year)

            # Determine overall quality
            issues = []
            if report.executive_summary.post_call_pcat_do == "GAP":
                issues.append("Post-call PCAT/DO gap")
            if "FAIL" in report.executive_summary.nf_one_in_seven:
                issues.append("NF 1-in-7 failure")
            if report.executive_summary.double_bookings > 0:
                issues.append(
                    f"{report.executive_summary.double_bookings} double-bookings"
                )

            return {
                "block_number": block_number,
                "passed": len(issues) == 0,
                "total_assignments": report.executive_summary.total_assignments,
                "acgme_compliance": report.executive_summary.acgme_compliance_rate,
                "issues": issues,
                "status": report.executive_summary.overall_status,
            }

        finally:
            db.close()

    except Exception as e:
        logger.error(f"Block quality check failed: {e}")
        return {
            "block_number": block_number,
            "passed": False,
            "error": str(e),
        }
