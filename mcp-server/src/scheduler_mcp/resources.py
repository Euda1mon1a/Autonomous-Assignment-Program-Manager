"""
Resource definitions for the Scheduler MCP server.

Resources provide read-only access to scheduling data and system state.
They are automatically refreshed and can be subscribed to for updates.
"""

import logging
import os
from collections import defaultdict
from datetime import date, datetime, timedelta
from typing import Any

from pydantic import BaseModel, Field
from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session, joinedload

logger = logging.getLogger(__name__)


# Response Models


class AssignmentInfo(BaseModel):
    """Information about a single assignment."""

    assignment_id: str
    person_id: str
    person_name: str
    block_name: str
    rotation: str
    start_date: date
    end_date: date
    is_supervising: bool
    pgy_level: int | None = None


class CoverageMetrics(BaseModel):
    """Coverage metrics for a time period."""

    total_days: int
    covered_days: int
    coverage_rate: float = Field(ge=0.0, le=1.0)
    understaffed_days: int
    overstaffed_days: int
    average_faculty_per_day: float
    average_residents_per_day: float


class ScheduleStatusResource(BaseModel):
    """Current schedule status resource."""

    query_timestamp: datetime
    date_range_start: date
    date_range_end: date
    total_assignments: int
    active_conflicts: int
    pending_swaps: int
    coverage_metrics: CoverageMetrics
    assignments: list[AssignmentInfo]
    last_generated: datetime | None = None
    generation_algorithm: str | None = None


class ViolationInfo(BaseModel):
    """Information about a compliance violation."""

    violation_type: str
    severity: str  # "critical", "warning", "info"
    person_id: str
    person_name: str
    date_range: tuple[date, date]
    description: str
    details: dict[str, Any]


class ComplianceMetrics(BaseModel):
    """ACGME compliance metrics."""

    overall_compliance_rate: float = Field(ge=0.0, le=1.0)
    work_hour_violations: int
    consecutive_duty_violations: int
    rest_period_violations: int
    supervision_violations: int
    total_violations: int
    residents_affected: int


class ComplianceSummaryResource(BaseModel):
    """ACGME compliance summary resource."""

    query_timestamp: datetime
    date_range_start: date
    date_range_end: date
    metrics: ComplianceMetrics
    violations: list[ViolationInfo]
    warnings: list[ViolationInfo]
    recommendations: list[str]


# Helper Functions


def _get_db_session() -> Session:
    """
    Get database session for resource queries.

    Returns:
        Database session

    Raises:
        RuntimeError: If DATABASE_URL is not set
    """
    # Import here to avoid circular dependencies
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../backend'))

    from app.db.session import SessionLocal

    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        raise RuntimeError(
            "DATABASE_URL environment variable not set. "
            "MCP server requires database connection for resources."
        )

    return SessionLocal()


# Resource Functions


async def get_schedule_status(
    start_date: date | None = None,
    end_date: date | None = None,
) -> ScheduleStatusResource:
    """
    Get current schedule status including assignments and coverage metrics.

    This resource provides a comprehensive view of the current schedule state,
    including all assignments, coverage statistics, and active issues.

    Args:
        start_date: Start date for schedule query (defaults to today)
        end_date: End date for schedule query (defaults to 30 days from start)

    Returns:
        ScheduleStatusResource containing current schedule state

    Raises:
        ValueError: If date range is invalid
    """
    from datetime import timedelta

    # Set defaults
    if start_date is None:
        start_date = date.today()
    if end_date is None:
        end_date = start_date + timedelta(days=30)

    if end_date < start_date:
        raise ValueError("end_date must be after start_date")

    logger.info(f"Fetching schedule status for {start_date} to {end_date}")

    # Import models
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../backend'))

    from app.models.assignment import Assignment
    from app.models.block import Block
    from app.models.conflict_alert import ConflictAlert, ConflictAlertStatus
    from app.models.person import Person
    from app.models.rotation_template import RotationTemplate
    from app.models.schedule_run import ScheduleRun
    from app.models.swap import SwapRecord, SwapStatus

    db = _get_db_session()
    try:
        # Query assignments in date range with related data
        assignments_query = (
            db.query(Assignment)
            .join(Block, Assignment.block_id == Block.id)
            .join(Person, Assignment.person_id == Person.id)
            .outerjoin(RotationTemplate, Assignment.rotation_template_id == RotationTemplate.id)
            .filter(
                and_(
                    Block.date >= start_date,
                    Block.date <= end_date
                )
            )
            .options(
                joinedload(Assignment.block),
                joinedload(Assignment.person),
                joinedload(Assignment.rotation_template)
            )
            .all()
        )

        # Build assignment list
        assignment_list = []
        assignment_dates = defaultdict(lambda: {"blocks": [], "person_ids": set()})

        for assignment in assignments_query:
            block = assignment.block
            person = assignment.person
            rotation = assignment.rotation_template

            # Track for coverage metrics
            assignment_dates[block.date]["blocks"].append(block)
            assignment_dates[block.date]["person_ids"].add(person.id)

            # Create assignment info
            assignment_list.append(AssignmentInfo(
                assignment_id=str(assignment.id),
                person_id=str(person.id),
                person_name=person.name,
                block_name=block.display_name,
                rotation=rotation.name if rotation else assignment.activity_override or "Unknown",
                start_date=block.date,
                end_date=block.date,  # Half-day blocks
                is_supervising=(assignment.role == "supervising"),
                pgy_level=person.pgy_level if person.is_resident else None,
            ))

        # Calculate coverage metrics
        total_days = (end_date - start_date).days + 1
        dates_with_coverage = set(assignment_dates.keys())
        covered_days = len(dates_with_coverage)

        # Calculate faculty and resident counts per day
        faculty_per_day = []
        residents_per_day = []
        understaffed_days = 0
        overstaffed_days = 0

        # Get all dates in range for checking coverage
        current_date = start_date
        while current_date <= end_date:
            if current_date in assignment_dates:
                # Count faculty and residents
                person_ids = assignment_dates[current_date]["person_ids"]
                people = db.query(Person).filter(Person.id.in_(person_ids)).all()

                faculty_count = sum(1 for p in people if p.is_faculty)
                resident_count = sum(1 for p in people if p.is_resident)

                faculty_per_day.append(faculty_count)
                residents_per_day.append(resident_count)

                # Check staffing levels (simplified - at least 1 faculty per day)
                if faculty_count == 0:
                    understaffed_days += 1
                elif faculty_count > 10:  # Example threshold
                    overstaffed_days += 1
            else:
                # No coverage on this day
                understaffed_days += 1
                faculty_per_day.append(0)
                residents_per_day.append(0)

            current_date += timedelta(days=1)

        avg_faculty = sum(faculty_per_day) / len(faculty_per_day) if faculty_per_day else 0.0
        avg_residents = sum(residents_per_day) / len(residents_per_day) if residents_per_day else 0.0

        coverage_metrics = CoverageMetrics(
            total_days=total_days,
            covered_days=covered_days,
            coverage_rate=covered_days / total_days if total_days > 0 else 0.0,
            understaffed_days=understaffed_days,
            overstaffed_days=overstaffed_days,
            average_faculty_per_day=round(avg_faculty, 1),
            average_residents_per_day=round(avg_residents, 1),
        )

        # Count active conflicts
        active_conflicts = (
            db.query(func.count(ConflictAlert.id))
            .filter(
                and_(
                    ConflictAlert.status == ConflictAlertStatus.NEW,
                    ConflictAlert.fmit_week >= start_date,
                    ConflictAlert.fmit_week <= end_date
                )
            )
            .scalar()
        ) or 0

        # Count pending swaps
        pending_swaps = (
            db.query(func.count(SwapRecord.id))
            .filter(SwapRecord.status == SwapStatus.PENDING)
            .scalar()
        ) or 0

        # Get latest schedule run info
        latest_run = (
            db.query(ScheduleRun)
            .order_by(ScheduleRun.created_at.desc())
            .first()
        )

        last_generated = latest_run.created_at if latest_run else None
        generation_algorithm = latest_run.algorithm if latest_run else None

        return ScheduleStatusResource(
            query_timestamp=datetime.now(),
            date_range_start=start_date,
            date_range_end=end_date,
            total_assignments=len(assignment_list),
            active_conflicts=active_conflicts,
            pending_swaps=pending_swaps,
            coverage_metrics=coverage_metrics,
            assignments=assignment_list,
            last_generated=last_generated,
            generation_algorithm=generation_algorithm,
        )

    finally:
        db.close()


async def get_compliance_summary(
    start_date: date | None = None,
    end_date: date | None = None,
) -> ComplianceSummaryResource:
    """
    Get ACGME compliance summary for a date range.

    This resource analyzes the schedule for ACGME work hour violations,
    supervision requirements, and duty hour restrictions.

    Args:
        start_date: Start date for compliance analysis (defaults to today)
        end_date: End date for compliance analysis (defaults to 30 days from start)

    Returns:
        ComplianceSummaryResource containing compliance metrics and violations

    Raises:
        ValueError: If date range is invalid
    """
    from datetime import timedelta

    # Set defaults
    if start_date is None:
        start_date = date.today()
    if end_date is None:
        end_date = start_date + timedelta(days=30)

    if end_date < start_date:
        raise ValueError("end_date must be after start_date")

    logger.info(f"Fetching compliance summary for {start_date} to {end_date}")

    # Import models and validators
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../backend'))

    from app.models.assignment import Assignment
    from app.models.block import Block
    from app.models.person import Person

    db = _get_db_session()
    try:
        # Query all assignments in date range
        assignments = (
            db.query(Assignment)
            .join(Block, Assignment.block_id == Block.id)
            .join(Person, Assignment.person_id == Person.id)
            .filter(
                and_(
                    Block.date >= start_date,
                    Block.date <= end_date
                )
            )
            .options(
                joinedload(Assignment.block),
                joinedload(Assignment.person)
            )
            .all()
        )

        # Get all residents in the period
        resident_ids = set()
        for assignment in assignments:
            if assignment.person.is_resident:
                resident_ids.add(assignment.person_id)

        residents = db.query(Person).filter(
            and_(
                Person.id.in_(resident_ids),
                Person.type == "resident"
            )
        ).all() if resident_ids else []

        # Track violations
        violations_list = []
        warnings_list = []
        work_hour_violations = 0
        consecutive_duty_violations = 0
        rest_period_violations = 0
        supervision_violations = 0
        residents_affected_set = set()

        # ACGME Validation: 80-hour rule
        HOURS_PER_BLOCK = 6
        MAX_WEEKLY_HOURS = 80
        ROLLING_WEEKS = 4

        for resident in residents:
            # Get resident's assignments
            resident_assignments = [a for a in assignments if a.person_id == resident.id]

            # Group by date
            blocks_by_date = defaultdict(int)
            for assignment in resident_assignments:
                blocks_by_date[assignment.block.date] += 1

            sorted_dates = sorted(blocks_by_date.keys())

            # Check 80-hour rule - rolling 4-week windows
            for i, window_start in enumerate(sorted_dates):
                window_end = window_start + timedelta(days=27)  # 4 weeks - 1 day

                total_blocks = sum(
                    count for dt, count in blocks_by_date.items()
                    if window_start <= dt <= window_end
                )

                total_hours = total_blocks * HOURS_PER_BLOCK
                avg_weekly = total_hours / ROLLING_WEEKS

                if avg_weekly > MAX_WEEKLY_HOURS:
                    work_hour_violations += 1
                    residents_affected_set.add(resident.id)
                    violations_list.append(ViolationInfo(
                        violation_type="work_hour_limit",
                        severity="critical",
                        person_id=str(resident.id),
                        person_name=resident.name,
                        date_range=(window_start, window_end),
                        description=f"Exceeded 80-hour weekly work limit",
                        details={
                            "average_weekly_hours": round(avg_weekly, 1),
                            "limit": MAX_WEEKLY_HOURS,
                            "total_blocks": total_blocks,
                            "window_start": window_start.isoformat(),
                            "window_end": window_end.isoformat(),
                        },
                    ))
                    break  # One violation per resident is enough for summary

            # Check 1-in-7 rule - maximum 6 consecutive days
            MAX_CONSECUTIVE_DAYS = 6
            dates_worked = sorted(blocks_by_date.keys())

            if len(dates_worked) >= MAX_CONSECUTIVE_DAYS + 1:
                consecutive = 1
                max_consecutive = 1
                start_consecutive = dates_worked[0]

                for j in range(1, len(dates_worked)):
                    if (dates_worked[j] - dates_worked[j - 1]).days == 1:
                        consecutive += 1
                        max_consecutive = max(max_consecutive, consecutive)
                    else:
                        consecutive = 1
                        start_consecutive = dates_worked[j]

                if max_consecutive > MAX_CONSECUTIVE_DAYS:
                    consecutive_duty_violations += 1
                    residents_affected_set.add(resident.id)
                    violations_list.append(ViolationInfo(
                        violation_type="consecutive_duty",
                        severity="critical",
                        person_id=str(resident.id),
                        person_name=resident.name,
                        date_range=(start_consecutive, start_consecutive + timedelta(days=max_consecutive - 1)),
                        description=f"Worked {max_consecutive} consecutive days (limit: {MAX_CONSECUTIVE_DAYS})",
                        details={
                            "consecutive_days": max_consecutive,
                            "limit": MAX_CONSECUTIVE_DAYS,
                        },
                    ))

        # Check supervision ratios per block
        PGY1_RATIO = 2  # 1 faculty per 2 PGY-1
        OTHER_RATIO = 4  # 1 faculty per 4 PGY-2/3

        # Group assignments by block
        by_block = defaultdict(lambda: {"residents": [], "faculty": [], "block": None})
        for assignment in assignments:
            block_id = assignment.block_id
            if assignment.person.is_resident:
                by_block[block_id]["residents"].append(assignment.person)
            elif assignment.person.is_faculty:
                by_block[block_id]["faculty"].append(assignment.person)
            by_block[block_id]["block"] = assignment.block

        for block_id, personnel in by_block.items():
            residents_in_block = personnel["residents"]
            faculty_in_block = personnel["faculty"]
            block = personnel["block"]

            if not residents_in_block:
                continue

            # Count PGY-1 vs others
            pgy1_count = sum(1 for r in residents_in_block if r.pgy_level == 1)
            other_count = len(residents_in_block) - pgy1_count

            # Calculate required faculty
            from_pgy1 = (pgy1_count + PGY1_RATIO - 1) // PGY1_RATIO
            from_other = (other_count + OTHER_RATIO - 1) // OTHER_RATIO
            required_faculty = max(1, from_pgy1 + from_other) if (pgy1_count + other_count) > 0 else 0

            if len(faculty_in_block) < required_faculty:
                supervision_violations += 1
                # Add resident IDs to affected set
                for r in residents_in_block:
                    residents_affected_set.add(r.id)

                warnings_list.append(ViolationInfo(
                    violation_type="supervision_ratio",
                    severity="warning",
                    person_id=str(block_id),  # Block ID for supervision issues
                    person_name=f"Block {block.display_name}",
                    date_range=(block.date, block.date),
                    description=f"Inadequate supervision: {len(faculty_in_block)} faculty for {len(residents_in_block)} residents",
                    details={
                        "residents_total": len(residents_in_block),
                        "pgy1_count": pgy1_count,
                        "faculty_count": len(faculty_in_block),
                        "required_faculty": required_faculty,
                        "block_date": block.date.isoformat(),
                    },
                ))

        # Calculate compliance metrics
        total_violations = work_hour_violations + consecutive_duty_violations + rest_period_violations + supervision_violations
        residents_affected = len(residents_affected_set)

        # Calculate overall compliance rate
        total_residents = len(residents)
        compliant_residents = total_residents - residents_affected
        overall_compliance_rate = compliant_residents / total_residents if total_residents > 0 else 1.0

        metrics = ComplianceMetrics(
            overall_compliance_rate=round(overall_compliance_rate, 3),
            work_hour_violations=work_hour_violations,
            consecutive_duty_violations=consecutive_duty_violations,
            rest_period_violations=rest_period_violations,
            supervision_violations=supervision_violations,
            total_violations=total_violations,
            residents_affected=residents_affected,
        )

        # Generate recommendations
        recommendations = []
        if work_hour_violations > 0:
            recommendations.append(
                f"Review workload distribution for {work_hour_violations} resident(s) exceeding 80-hour limit"
            )
        if consecutive_duty_violations > 0:
            recommendations.append(
                f"Ensure mandatory rest days for {consecutive_duty_violations} resident(s) with excessive consecutive duty"
            )
        if supervision_violations > 0:
            recommendations.append(
                f"Increase faculty coverage on {supervision_violations} block(s) with inadequate supervision ratios"
            )
        if total_violations == 0:
            recommendations.append("Schedule is fully ACGME compliant - no violations detected")
        else:
            recommendations.append(
                f"Total of {total_violations} violations affecting {residents_affected} resident(s) - prioritize resolution"
            )

        return ComplianceSummaryResource(
            query_timestamp=datetime.now(),
            date_range_start=start_date,
            date_range_end=end_date,
            metrics=metrics,
            violations=violations_list,
            warnings=warnings_list,
            recommendations=recommendations,
        )

    finally:
        db.close()
