"""Core analytics engine for schedule analysis."""

from collections import defaultdict
from datetime import date, datetime

from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from app.analytics.metrics import (
    calculate_acgme_compliance_rate,
    calculate_coverage_rate,
    calculate_fairness_index,
)
from app.analytics.types import (
    AnalysisResult,
    RotationCoverageStats,
    ScheduleComparison,
    TrendAnalysis,
    WorkloadDistribution,
)
from app.models.assignment import Assignment
from app.models.block import Block
from app.models.person import Person
from app.models.rotation_template import RotationTemplate
from app.models.schedule_run import ScheduleRun


class AnalyticsEngine:
    """Core analytics engine for schedule analysis and reporting."""

    def __init__(self, db: Session) -> None:
        """
        Initialize analytics engine.

        Args:
            db: SQLAlchemy database session
        """
        self.db = db

    def analyze_schedule(self, start_date: date, end_date: date) -> AnalysisResult:
        """
        Comprehensive schedule analysis for a date range.

        Args:
            start_date: Start date for analysis
            end_date: End date for analysis

        Returns:
            Dict with comprehensive analytics including fairness, coverage, violations
        """
        # Fetch blocks in date range
        blocks = (
            self.db.query(Block)
            .filter(and_(Block.date >= start_date, Block.date <= end_date))
            .all()
        )

        # Fetch assignments in date range
        assignments = (
            self.db.query(Assignment)
            .join(Block)
            .filter(and_(Block.date >= start_date, Block.date <= end_date))
            .all()
        )

        # Convert to dicts for metric calculations
        block_dicts = [{"id": str(b.id), "date": b.date} for b in blocks]
        assignment_dicts = [
            {
                "id": str(a.id),
                "person_id": str(a.person_id),
                "block_id": str(a.block_id),
                "rotation_template_id": (
                    str(a.rotation_template_id) if a.rotation_template_id else None
                ),
                "block_date": a.block.date,
            }
            for a in assignments
        ]

        # Get schedule run stats
        schedule_runs = (
            self.db.query(ScheduleRun)
            .filter(
                and_(
                    ScheduleRun.start_date >= start_date,
                    ScheduleRun.end_date <= end_date,
                )
            )
            .all()
        )

        total_violations = sum(sr.acgme_violations or 0 for sr in schedule_runs)
        total_overrides = sum(sr.acgme_override_count or 0 for sr in schedule_runs)

        # Calculate metrics
        fairness = calculate_fairness_index(assignment_dicts)
        coverage = calculate_coverage_rate(block_dicts, assignment_dicts)
        compliance = calculate_acgme_compliance_rate(
            violations=total_violations, total_checks=len(blocks) if blocks else 1
        )

        # Get workload distribution
        workload_dist = self.get_resident_workload_distribution(start_date, end_date)

        return {
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "total_days": (end_date - start_date).days + 1,
            },
            "summary": {
                "total_blocks": len(blocks),
                "total_assignments": len(assignments),
                "unique_people": len({a.person_id for a in assignments}),
                "schedule_runs": len(schedule_runs),
            },
            "metrics": {
                "fairness": fairness,
                "coverage": coverage,
                "compliance": compliance,
            },
            "workload": workload_dist,
            "violations": {
                "total": total_violations,
                "overrides_acknowledged": total_overrides,
                "unacknowledged": total_violations - total_overrides,
            },
            "generated_at": datetime.utcnow().isoformat(),
        }

    def get_resident_workload_distribution(
        self, start_date: date | None = None, end_date: date | None = None
    ) -> WorkloadDistribution:
        """
        Get workload fairness metrics across all residents.

        Args:
            start_date: Optional start date filter
            end_date: Optional end date filter

        Returns:
            Dict with workload distribution statistics
        """
        query = (
            self.db.query(
                Person.id,
                Person.name,
                Person.pgy_level,
                Person.target_clinical_blocks,
                func.count(Assignment.id).label("assignment_count"),
            )
            .join(Assignment)
            .join(Block)
        )

        # Apply date filters if provided
        if start_date:
            query = query.filter(Block.date >= start_date)
        if end_date:
            query = query.filter(Block.date <= end_date)

            # Only residents
        query = query.filter(Person.type == "resident")

        # Group by person
        results = query.group_by(
            Person.id, Person.name, Person.pgy_level, Person.target_clinical_blocks
        ).all()

        workload_data = []
        for person_id, name, pgy_level, target, count in results:
            target_blocks = target or 48  # Default if not set
            utilization = (count / target_blocks * 100) if target_blocks > 0 else 0

            workload_data.append(
                {
                    "person_id": str(person_id),
                    "name": name,
                    "pgy_level": pgy_level,
                    "assignments": count,
                    "target": target_blocks,
                    "utilization_percent": round(utilization, 2),
                    "variance": count - target_blocks,
                }
            )

            # Calculate statistics
        if workload_data:
            assignments = [w["assignments"] for w in workload_data]
            avg_assignments = sum(assignments) / len(assignments)
            variance = sum((a - avg_assignments) ** 2 for a in assignments) / len(
                assignments
            )
            std_dev = variance**0.5
        else:
            avg_assignments = 0
            std_dev = 0

        return {
            "residents": workload_data,
            "statistics": {
                "total_residents": len(workload_data),
                "average_assignments": round(avg_assignments, 2),
                "std_deviation": round(std_dev, 2),
                "min_assignments": min(assignments) if assignments else 0,
                "max_assignments": max(assignments) if assignments else 0,
            },
        }

    def get_rotation_coverage_stats(
        self, start_date: date | None = None, end_date: date | None = None
    ) -> RotationCoverageStats:
        """
        Get coverage statistics by rotation type.

        Args:
            start_date: Optional start date filter
            end_date: Optional end date filter

        Returns:
            Dict with rotation coverage statistics
        """
        query = (
            self.db.query(
                RotationTemplate.id,
                RotationTemplate.name,
                RotationTemplate.rotation_type,
                func.count(Assignment.id).label("assignment_count"),
            )
            .join(Assignment)
            .join(Block)
        )

        # Apply date filters
        if start_date:
            query = query.filter(Block.date >= start_date)
        if end_date:
            query = query.filter(Block.date <= end_date)

        results = query.group_by(
            RotationTemplate.id, RotationTemplate.name, RotationTemplate.rotation_type
        ).all()

        coverage_data = []
        for rotation_id, name, rotation_type, count in results:
            coverage_data.append(
                {
                    "rotation_id": str(rotation_id),
                    "name": name,
                    "rotation_type": rotation_type,
                    "total_assignments": count,
                }
            )

            # Group by rotation type
        by_rotation_type = defaultdict(int)
        for item in coverage_data:
            by_rotation_type[item["rotation_type"]] += item["total_assignments"]

        return {
            "rotations": coverage_data,
            "by_rotation_type": dict(by_rotation_type),
            "total_rotations": len(coverage_data),
        }

    def get_trend_analysis(self, metric: str, period: str = "monthly") -> TrendAnalysis:
        """
        Get historical trends for a specific metric.

        Args:
            metric: Metric to analyze ('violations', 'coverage', 'fairness')
            period: Time period ('daily', 'weekly', 'monthly')

        Returns:
            Dict with trend data points
        """
        # Get all schedule runs
        runs = self.db.query(ScheduleRun).order_by(ScheduleRun.created_at).all()

        trend_data = []

        for run in runs:
            data_point = {
                "date": run.start_date.isoformat(),
                "run_id": str(run.id),
                "status": run.status,
            }

            if metric == "violations":
                data_point["value"] = run.acgme_violations or 0
            elif metric == "coverage":
                coverage_pct = (
                    (run.total_blocks_assigned / 730 * 100)
                    if run.total_blocks_assigned
                    else 0
                )
                data_point["value"] = round(coverage_pct, 2)
            elif metric == "runtime":
                data_point["value"] = float(run.runtime_seconds or 0)

            trend_data.append(data_point)

        return {
            "metric": metric,
            "period": period,
            "data_points": trend_data,
            "total_runs": len(runs),
        }

    def compare_schedules(
        self, run_id_1: str, run_id_2: str
    ) -> ScheduleComparison | dict[str, str]:
        """
        Compare two schedule versions.

        Args:
            run_id_1: First schedule run ID
            run_id_2: Second schedule run ID

        Returns:
            Dict with comparison results
        """
        # Get schedule runs
        run1 = self.db.query(ScheduleRun).filter(ScheduleRun.id == run_id_1).first()
        run2 = self.db.query(ScheduleRun).filter(ScheduleRun.id == run_id_2).first()

        if not run1 or not run2:
            return {"error": "One or both schedule runs not found"}

            # Get assignments for each run's date range
        assignments1 = (
            self.db.query(Assignment)
            .join(Block)
            .filter(and_(Block.date >= run1.start_date, Block.date <= run1.end_date))
            .all()
        )

        assignments2 = (
            self.db.query(Assignment)
            .join(Block)
            .filter(and_(Block.date >= run2.start_date, Block.date <= run2.end_date))
            .all()
        )

        # Build comparison
        comparison = {
            "run_1": {
                "id": str(run1.id),
                "date_range": f"{run1.start_date} to {run1.end_date}",
                "status": run1.status,
                "violations": run1.acgme_violations or 0,
                "blocks_assigned": run1.total_blocks_assigned or 0,
                "runtime_seconds": float(run1.runtime_seconds or 0),
            },
            "run_2": {
                "id": str(run2.id),
                "date_range": f"{run2.start_date} to {run2.end_date}",
                "status": run2.status,
                "violations": run2.acgme_violations or 0,
                "blocks_assigned": run2.total_blocks_assigned or 0,
                "runtime_seconds": float(run2.runtime_seconds or 0),
            },
            "differences": {
                "violations_delta": (run2.acgme_violations or 0)
                - (run1.acgme_violations or 0),
                "blocks_delta": (run2.total_blocks_assigned or 0)
                - (run1.total_blocks_assigned or 0),
                "runtime_delta": float(
                    (run2.runtime_seconds or 0) - (run1.runtime_seconds or 0)
                ),
            },
        }

        return comparison
