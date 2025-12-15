"""Analytics service for schedule metrics and reporting."""
from datetime import date, datetime, timedelta
from typing import Optional, Dict, List, Any
from uuid import UUID
from collections import defaultdict

from sqlalchemy import func, and_, or_, case
from sqlalchemy.orm import Session, joinedload

from app.models import (
    Assignment,
    Person,
    Block,
    Absence,
    RotationTemplate,
    ScheduleRun,
)


class AnalyticsService:
    """
    Service for analyzing schedule metrics and generating insights.

    Provides:
    - Schedule utilization metrics
    - Person workload statistics
    - Absence patterns analysis
    - Compliance rate calculations
    - Time-series data aggregation
    """

    def __init__(self, db: Session):
        """Initialize the analytics service."""
        self.db = db

    def get_overview_metrics(
        self,
        start_date: date,
        end_date: date,
    ) -> Dict[str, Any]:
        """
        Get high-level dashboard metrics for a date range.

        Returns:
        - Total assignments
        - Coverage rate
        - ACGME compliance rate
        - Average workload per person
        - Absence statistics
        """
        # Total blocks in range
        total_blocks = (
            self.db.query(func.count(Block.id))
            .filter(Block.date >= start_date, Block.date <= end_date)
            .scalar()
        )

        # Total assignments
        total_assignments = (
            self.db.query(func.count(Assignment.id))
            .join(Block)
            .filter(Block.date >= start_date, Block.date <= end_date)
            .scalar()
        )

        # Coverage rate
        coverage_rate = (total_assignments / total_blocks * 100) if total_blocks > 0 else 0

        # Get resident assignments (for workload calculation)
        resident_assignments = (
            self.db.query(Assignment.person_id, func.count(Assignment.id).label('count'))
            .join(Block)
            .join(Person)
            .filter(
                Block.date >= start_date,
                Block.date <= end_date,
                Person.type == 'resident',
            )
            .group_by(Assignment.person_id)
            .all()
        )

        # Calculate average workload
        if resident_assignments:
            total_resident_blocks = sum(r.count for r in resident_assignments)
            avg_workload = total_resident_blocks / len(resident_assignments)
        else:
            avg_workload = 0

        # Absence statistics
        absences = (
            self.db.query(Absence)
            .filter(
                or_(
                    and_(Absence.start_date >= start_date, Absence.start_date <= end_date),
                    and_(Absence.end_date >= start_date, Absence.end_date <= end_date),
                    and_(Absence.start_date <= start_date, Absence.end_date >= end_date),
                )
            )
            .all()
        )

        absence_stats = {
            "total": len(absences),
            "blocking": sum(1 for a in absences if a.should_block_assignment),
            "by_type": {},
        }

        # Count by type
        for absence in absences:
            absence_stats["by_type"][absence.absence_type] = (
                absence_stats["by_type"].get(absence.absence_type, 0) + 1
            )

        # Get compliance metrics from recent schedule runs
        recent_runs = (
            self.db.query(ScheduleRun)
            .filter(
                ScheduleRun.start_date >= start_date,
                ScheduleRun.end_date <= end_date,
            )
            .order_by(ScheduleRun.created_at.desc())
            .limit(5)
            .all()
        )

        if recent_runs:
            avg_violations = sum(r.acgme_violations or 0 for r in recent_runs) / len(recent_runs)
            compliance_rate = max(0, 100 - (avg_violations / total_blocks * 100)) if total_blocks > 0 else 100
            successful_runs = sum(1 for r in recent_runs if r.is_successful)
            success_rate = (successful_runs / len(recent_runs) * 100) if recent_runs else 0
        else:
            compliance_rate = 100.0
            success_rate = 0.0
            avg_violations = 0

        return {
            "date_range": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
            },
            "coverage": {
                "total_blocks": total_blocks,
                "total_assignments": total_assignments,
                "coverage_rate": round(coverage_rate, 2),
            },
            "workload": {
                "total_residents": len(resident_assignments),
                "average_blocks_per_resident": round(avg_workload, 2),
            },
            "absences": absence_stats,
            "compliance": {
                "compliance_rate": round(compliance_rate, 2),
                "average_violations": round(avg_violations, 2),
                "schedule_success_rate": round(success_rate, 2),
            },
        }

    def get_person_workload(
        self,
        start_date: date,
        end_date: date,
        person_id: Optional[UUID] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get detailed workload statistics per person.

        Returns for each person:
        - Total assignments
        - Breakdown by rotation type
        - Workload compared to target
        - Weekend/holiday assignments
        - Call assignments
        """
        query = (
            self.db.query(Person)
            .options(joinedload(Person.assignments))
            .filter(Person.type == 'resident')
        )

        if person_id:
            query = query.filter(Person.id == person_id)

        people = query.all()
        results = []

        for person in people:
            # Get assignments in date range
            assignments = [
                a for a in person.assignments
                if a.block and start_date <= a.block.date <= end_date
            ]

            # Count by rotation template
            rotation_breakdown = defaultdict(int)
            for assignment in assignments:
                rotation_name = assignment.activity_name
                rotation_breakdown[rotation_name] += 1

            # Count weekend/holiday assignments
            weekend_count = sum(1 for a in assignments if a.block.is_weekend)
            holiday_count = sum(1 for a in assignments if a.block.is_holiday)

            # Count by role
            role_breakdown = defaultdict(int)
            for assignment in assignments:
                role_breakdown[assignment.role] += 1

            # Calculate target vs actual
            total_blocks = len(assignments)
            target_blocks = person.target_clinical_blocks or 0

            # Estimate target for this date range
            total_days = (end_date - start_date).days + 1
            estimated_target = (target_blocks / 365 * total_days * 2) if target_blocks > 0 else 0

            # Calculate utilization percentage
            utilization = (total_blocks / estimated_target * 100) if estimated_target > 0 else 0

            results.append({
                "person_id": str(person.id),
                "person_name": person.name,
                "pgy_level": person.pgy_level,
                "statistics": {
                    "total_blocks": total_blocks,
                    "target_blocks": round(estimated_target, 1),
                    "utilization_percentage": round(utilization, 2),
                    "weekend_assignments": weekend_count,
                    "holiday_assignments": holiday_count,
                },
                "rotation_breakdown": dict(rotation_breakdown),
                "role_breakdown": dict(role_breakdown),
            })

        # Sort by total blocks descending
        results.sort(key=lambda x: x["statistics"]["total_blocks"], reverse=True)

        return results

    def get_absence_patterns(
        self,
        start_date: date,
        end_date: date,
    ) -> Dict[str, Any]:
        """
        Analyze absence patterns and trends.

        Returns:
        - Absence frequency by person
        - Absence types distribution
        - Peak absence periods
        - Military vs non-military absences
        """
        absences = (
            self.db.query(Absence)
            .options(joinedload(Absence.person))
            .filter(
                or_(
                    and_(Absence.start_date >= start_date, Absence.start_date <= end_date),
                    and_(Absence.end_date >= start_date, Absence.end_date <= end_date),
                    and_(Absence.start_date <= start_date, Absence.end_date >= end_date),
                )
            )
            .all()
        )

        # Absence by person
        person_absences = defaultdict(lambda: {"count": 0, "total_days": 0, "types": defaultdict(int)})

        for absence in absences:
            person_id = str(absence.person_id)
            person_absences[person_id]["count"] += 1
            person_absences[person_id]["total_days"] += absence.duration_days
            person_absences[person_id]["types"][absence.absence_type] += 1
            person_absences[person_id]["person_name"] = absence.person.name

        # Convert to list format
        absence_by_person = [
            {
                "person_id": pid,
                "person_name": data["person_name"],
                "total_absences": data["count"],
                "total_days": data["total_days"],
                "types": dict(data["types"]),
            }
            for pid, data in person_absences.items()
        ]

        # Sort by total days descending
        absence_by_person.sort(key=lambda x: x["total_days"], reverse=True)

        # Absence type distribution
        type_distribution = defaultdict(lambda: {"count": 0, "total_days": 0})
        for absence in absences:
            type_distribution[absence.absence_type]["count"] += 1
            type_distribution[absence.absence_type]["total_days"] += absence.duration_days

        # Military vs non-military
        military_count = sum(1 for a in absences if a.is_military)
        military_days = sum(a.duration_days for a in absences if a.is_military)

        # Blocking vs non-blocking
        blocking_count = sum(1 for a in absences if a.should_block_assignment)
        blocking_days = sum(a.duration_days for a in absences if a.should_block_assignment)

        # Time-series analysis (monthly aggregation)
        monthly_absences = defaultdict(lambda: {"count": 0, "days": 0})
        for absence in absences:
            month_key = absence.start_date.strftime("%Y-%m")
            monthly_absences[month_key]["count"] += 1
            monthly_absences[month_key]["days"] += absence.duration_days

        # Convert to sorted list
        monthly_series = [
            {"month": month, "absences": data["count"], "days": data["days"]}
            for month, data in sorted(monthly_absences.items())
        ]

        return {
            "summary": {
                "total_absences": len(absences),
                "total_days": sum(a.duration_days for a in absences),
                "military_absences": military_count,
                "military_days": military_days,
                "blocking_absences": blocking_count,
                "blocking_days": blocking_days,
            },
            "by_person": absence_by_person,
            "by_type": {
                k: {"count": v["count"], "total_days": v["total_days"]}
                for k, v in type_distribution.items()
            },
            "time_series": monthly_series,
        }

    def get_compliance_metrics(
        self,
        start_date: date,
        end_date: date,
    ) -> Dict[str, Any]:
        """
        Calculate ACGME compliance rates and violation trends.

        Returns:
        - Overall compliance rate
        - Violation breakdown by type
        - Trends over time
        - Override statistics
        """
        # Get all schedule runs in date range
        runs = (
            self.db.query(ScheduleRun)
            .filter(
                or_(
                    and_(ScheduleRun.start_date >= start_date, ScheduleRun.start_date <= end_date),
                    and_(ScheduleRun.end_date >= start_date, ScheduleRun.end_date <= end_date),
                )
            )
            .order_by(ScheduleRun.created_at.desc())
            .all()
        )

        if not runs:
            return {
                "summary": {
                    "total_runs": 0,
                    "successful_runs": 0,
                    "success_rate": 0,
                    "average_violations": 0,
                    "total_overrides": 0,
                },
                "by_algorithm": {},
                "time_series": [],
            }

        # Calculate summary statistics
        total_runs = len(runs)
        successful_runs = sum(1 for r in runs if r.is_successful)
        total_violations = sum(r.acgme_violations or 0 for r in runs)
        total_overrides = sum(r.acgme_override_count or 0 for r in runs)

        success_rate = (successful_runs / total_runs * 100) if total_runs > 0 else 0
        avg_violations = total_violations / total_runs if total_runs > 0 else 0

        # Breakdown by algorithm
        algorithm_stats = defaultdict(lambda: {
            "runs": 0,
            "successful": 0,
            "violations": 0,
            "avg_runtime": 0,
        })

        for run in runs:
            alg = run.algorithm
            algorithm_stats[alg]["runs"] += 1
            if run.is_successful:
                algorithm_stats[alg]["successful"] += 1
            algorithm_stats[alg]["violations"] += (run.acgme_violations or 0)
            algorithm_stats[alg]["avg_runtime"] += float(run.runtime_seconds or 0)

        # Calculate averages
        for alg, stats in algorithm_stats.items():
            if stats["runs"] > 0:
                stats["success_rate"] = round(stats["successful"] / stats["runs"] * 100, 2)
                stats["avg_violations"] = round(stats["violations"] / stats["runs"], 2)
                stats["avg_runtime"] = round(stats["avg_runtime"] / stats["runs"], 2)

        # Time-series data (daily aggregation)
        time_series = []
        for run in sorted(runs, key=lambda r: r.created_at):
            time_series.append({
                "date": run.created_at.date().isoformat(),
                "status": run.status,
                "violations": run.acgme_violations or 0,
                "overrides": run.acgme_override_count or 0,
                "algorithm": run.algorithm,
                "runtime_seconds": float(run.runtime_seconds or 0),
            })

        return {
            "summary": {
                "total_runs": total_runs,
                "successful_runs": successful_runs,
                "success_rate": round(success_rate, 2),
                "average_violations": round(avg_violations, 2),
                "total_overrides": total_overrides,
            },
            "by_algorithm": {k: dict(v) for k, v in algorithm_stats.items()},
            "time_series": time_series,
        }

    def get_utilization_metrics(
        self,
        start_date: date,
        end_date: date,
    ) -> Dict[str, Any]:
        """
        Calculate schedule utilization metrics.

        Returns:
        - Overall utilization rate
        - Utilization by rotation type
        - Utilization by time period (weekday vs weekend)
        - Peak and low utilization periods
        """
        # Get all blocks and assignments in range
        blocks = (
            self.db.query(Block)
            .filter(Block.date >= start_date, Block.date <= end_date)
            .all()
        )

        assignments = (
            self.db.query(Assignment)
            .options(joinedload(Assignment.rotation_template))
            .join(Block)
            .filter(Block.date >= start_date, Block.date <= end_date)
            .all()
        )

        total_blocks = len(blocks)
        total_assignments = len(assignments)

        # Overall utilization
        overall_utilization = (total_assignments / total_blocks * 100) if total_blocks > 0 else 0

        # Utilization by rotation
        rotation_utilization = defaultdict(int)
        for assignment in assignments:
            rotation_name = assignment.activity_name
            rotation_utilization[rotation_name] += 1

        # Utilization by day type
        weekday_blocks = sum(1 for b in blocks if not b.is_weekend and not b.is_holiday)
        weekend_blocks = sum(1 for b in blocks if b.is_weekend)
        holiday_blocks = sum(1 for b in blocks if b.is_holiday)

        weekday_assignments = sum(
            1 for a in assignments
            if a.block and not a.block.is_weekend and not a.block.is_holiday
        )
        weekend_assignments = sum(
            1 for a in assignments
            if a.block and a.block.is_weekend
        )
        holiday_assignments = sum(
            1 for a in assignments
            if a.block and a.block.is_holiday
        )

        weekday_util = (weekday_assignments / weekday_blocks * 100) if weekday_blocks > 0 else 0
        weekend_util = (weekend_assignments / weekend_blocks * 100) if weekend_blocks > 0 else 0
        holiday_util = (holiday_assignments / holiday_blocks * 100) if holiday_blocks > 0 else 0

        # Daily utilization for trend analysis
        daily_utilization = defaultdict(lambda: {"blocks": 0, "assignments": 0})
        for block in blocks:
            date_key = block.date.isoformat()
            daily_utilization[date_key]["blocks"] += 1

        for assignment in assignments:
            if assignment.block:
                date_key = assignment.block.date.isoformat()
                daily_utilization[date_key]["assignments"] += 1

        # Convert to time series with utilization percentage
        time_series = []
        for date_key in sorted(daily_utilization.keys()):
            data = daily_utilization[date_key]
            util_pct = (data["assignments"] / data["blocks"] * 100) if data["blocks"] > 0 else 0
            time_series.append({
                "date": date_key,
                "blocks": data["blocks"],
                "assignments": data["assignments"],
                "utilization": round(util_pct, 2),
            })

        return {
            "summary": {
                "total_blocks": total_blocks,
                "total_assignments": total_assignments,
                "overall_utilization": round(overall_utilization, 2),
            },
            "by_day_type": {
                "weekday": {
                    "blocks": weekday_blocks,
                    "assignments": weekday_assignments,
                    "utilization": round(weekday_util, 2),
                },
                "weekend": {
                    "blocks": weekend_blocks,
                    "assignments": weekend_assignments,
                    "utilization": round(weekend_util, 2),
                },
                "holiday": {
                    "blocks": holiday_blocks,
                    "assignments": holiday_assignments,
                    "utilization": round(holiday_util, 2),
                },
            },
            "by_rotation": {
                k: v for k, v in sorted(
                    rotation_utilization.items(),
                    key=lambda x: x[1],
                    reverse=True
                )
            },
            "time_series": time_series,
        }
