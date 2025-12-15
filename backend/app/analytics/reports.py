"""Report generation for schedule analytics."""
from typing import Dict, List, Any, Optional
from datetime import datetime, date, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from collections import defaultdict

from app.models.assignment import Assignment
from app.models.block import Block
from app.models.person import Person
from app.models.schedule_run import ScheduleRun
from app.models.rotation_template import RotationTemplate
from app.analytics.metrics import (
    calculate_fairness_index,
    calculate_coverage_rate,
    calculate_acgme_compliance_rate,
    calculate_consecutive_duty_stats
)


class ReportGenerator:
    """Generate various types of schedule reports."""

    def __init__(self, db: Session):
        """
        Initialize report generator.

        Args:
            db: SQLAlchemy database session
        """
        self.db = db

    def generate_monthly_report(
        self,
        year: int,
        month: int
    ) -> Dict[str, Any]:
        """
        Generate monthly summary report.

        Args:
            year: Year (e.g., 2025)
            month: Month (1-12)

        Returns:
            Dict with monthly report data
        """
        # Calculate date range
        start_date = date(year, month, 1)
        if month == 12:
            end_date = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = date(year, month + 1, 1) - timedelta(days=1)

        # Get blocks and assignments
        blocks = self.db.query(Block).filter(
            and_(
                Block.date >= start_date,
                Block.date <= end_date
            )
        ).all()

        assignments = self.db.query(Assignment).join(Block).filter(
            and_(
                Block.date >= start_date,
                Block.date <= end_date
            )
        ).all()

        # Get schedule runs
        schedule_runs = self.db.query(ScheduleRun).filter(
            and_(
                ScheduleRun.start_date >= start_date,
                ScheduleRun.end_date <= end_date
            )
        ).all()

        # Calculate metrics
        block_dicts = [{"id": str(b.id)} for b in blocks]
        assignment_dicts = [
            {
                "person_id": str(a.person_id),
                "block_id": str(a.block_id)
            }
            for a in assignments
        ]

        fairness = calculate_fairness_index(assignment_dicts)
        coverage = calculate_coverage_rate(block_dicts, assignment_dicts)

        total_violations = sum(sr.acgme_violations or 0 for sr in schedule_runs)
        compliance = calculate_acgme_compliance_rate(
            violations=total_violations,
            total_checks=len(blocks) if blocks else 1
        )

        # Get top rotations
        rotation_counts = defaultdict(int)
        for assignment in assignments:
            if assignment.rotation_template:
                rotation_counts[assignment.rotation_template.name] += 1

        top_rotations = sorted(
            rotation_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]

        # Recommendations
        recommendations = []
        if fairness["status"] != "good":
            recommendations.append("Review workload distribution to improve fairness")
        if coverage["value"] < 95.0:
            recommendations.append(f"Increase coverage - currently at {coverage['value']}%")
        if total_violations > 0:
            recommendations.append(f"Address {total_violations} ACGME violations")

        return {
            "report_type": "monthly",
            "period": {
                "year": year,
                "month": month,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            },
            "summary": {
                "total_blocks": len(blocks),
                "total_assignments": len(assignments),
                "unique_residents": len(set(a.person_id for a in assignments)),
                "schedule_runs": len(schedule_runs),
                "acgme_violations": total_violations
            },
            "metrics": {
                "fairness": fairness,
                "coverage": coverage,
                "compliance": compliance
            },
            "charts": {
                "top_rotations": [
                    {"name": name, "count": count}
                    for name, count in top_rotations
                ],
                "daily_coverage": self._get_daily_coverage_chart(blocks, assignments)
            },
            "recommendations": recommendations,
            "generated_at": datetime.utcnow().isoformat()
        }

    def generate_resident_report(
        self,
        person_id: str,
        start_date: date,
        end_date: date
    ) -> Dict[str, Any]:
        """
        Generate individual resident statistics report.

        Args:
            person_id: Person ID
            start_date: Start date
            end_date: End date

        Returns:
            Dict with resident report data
        """
        # Get person
        person = self.db.query(Person).filter(Person.id == person_id).first()
        if not person:
            return {"error": "Person not found"}

        # Get assignments
        assignments = self.db.query(Assignment).join(Block).filter(
            and_(
                Assignment.person_id == person_id,
                Block.date >= start_date,
                Block.date <= end_date
            )
        ).all()

        # Build assignment dicts with dates
        assignment_dicts = [
            {
                "id": str(a.id),
                "person_id": str(a.person_id),
                "block_id": str(a.block_id),
                "block_date": a.block.date,
                "rotation": a.activity_name
            }
            for a in assignments
        ]

        # Calculate consecutive duty stats
        duty_stats = calculate_consecutive_duty_stats(person_id, assignment_dicts)

        # Count by rotation
        rotation_counts = defaultdict(int)
        for assignment in assignments:
            rotation_counts[assignment.activity_name] += 1

        # Calculate workload
        target_blocks = person.target_clinical_blocks or 48
        actual_blocks = len(assignments)
        utilization = (actual_blocks / target_blocks * 100) if target_blocks > 0 else 0

        # Recommendations
        recommendations = []
        if duty_stats["max_consecutive_days"] > 6:
            recommendations.append(
                f"Review consecutive duty schedule - max {duty_stats['max_consecutive_days']} days"
            )
        if utilization < 80:
            recommendations.append(f"Underutilized - only {utilization:.1f}% of target")
        elif utilization > 120:
            recommendations.append(f"Overutilized - at {utilization:.1f}% of target")

        return {
            "report_type": "resident",
            "person": {
                "id": str(person.id),
                "name": person.name,
                "pgy_level": person.pgy_level,
                "target_blocks": target_blocks
            },
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            },
            "summary": {
                "total_assignments": len(assignments),
                "unique_rotations": len(rotation_counts),
                "utilization_percent": round(utilization, 2)
            },
            "duty_patterns": duty_stats,
            "rotations": [
                {"name": name, "count": count}
                for name, count in sorted(
                    rotation_counts.items(),
                    key=lambda x: x[1],
                    reverse=True
                )
            ],
            "charts": {
                "rotation_distribution": [
                    {"rotation": name, "blocks": count}
                    for name, count in rotation_counts.items()
                ]
            },
            "recommendations": recommendations,
            "generated_at": datetime.utcnow().isoformat()
        }

    def generate_compliance_report(
        self,
        start_date: date,
        end_date: date
    ) -> Dict[str, Any]:
        """
        Generate ACGME compliance summary report.

        Args:
            start_date: Start date
            end_date: End date

        Returns:
            Dict with compliance report data
        """
        # Get schedule runs in period
        schedule_runs = self.db.query(ScheduleRun).filter(
            and_(
                ScheduleRun.start_date >= start_date,
                ScheduleRun.end_date <= end_date
            )
        ).all()

        # Calculate compliance metrics
        total_violations = sum(sr.acgme_violations or 0 for sr in schedule_runs)
        total_overrides = sum(sr.acgme_override_count or 0 for sr in schedule_runs)
        total_runs = len(schedule_runs)
        successful_runs = sum(1 for sr in schedule_runs if sr.status == "success")

        # Get blocks for compliance rate calculation
        blocks = self.db.query(Block).filter(
            and_(
                Block.date >= start_date,
                Block.date <= end_date
            )
        ).all()

        compliance = calculate_acgme_compliance_rate(
            violations=total_violations,
            total_checks=len(blocks) if blocks else 1
        )

        # Get all assignments to check supervision
        assignments = self.db.query(Assignment).join(Block).join(Person).filter(
            and_(
                Block.date >= start_date,
                Block.date <= end_date
            )
        ).all()

        # Check supervision ratios
        supervision_issues = []
        blocks_checked = set()

        for assignment in assignments:
            if assignment.block_id in blocks_checked:
                continue

            block_assignments = [a for a in assignments if a.block_id == assignment.block_id]
            residents = [a for a in block_assignments if a.person.is_resident]
            faculty = [a for a in block_assignments if a.person.is_faculty]

            if residents and not faculty:
                supervision_issues.append({
                    "block_id": str(assignment.block_id),
                    "date": assignment.block.date.isoformat(),
                    "issue": "No faculty supervision",
                    "residents": len(residents)
                })

            blocks_checked.add(assignment.block_id)

        # Recommendations
        recommendations = []
        if total_violations > 0:
            recommendations.append(f"Address {total_violations} ACGME violations")
        if total_overrides > 0:
            recommendations.append(
                f"Review {total_overrides} acknowledged overrides for ongoing necessity"
            )
        if len(supervision_issues) > 0:
            recommendations.append(
                f"Fix {len(supervision_issues)} blocks with supervision issues"
            )

        return {
            "report_type": "compliance",
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            },
            "summary": {
                "total_violations": total_violations,
                "acknowledged_overrides": total_overrides,
                "unacknowledged_violations": total_violations - total_overrides,
                "compliance_rate": compliance["value"],
                "total_schedule_runs": total_runs,
                "successful_runs": successful_runs
            },
            "details": {
                "compliance_metric": compliance,
                "supervision_issues": supervision_issues[:10]  # Top 10
            },
            "charts": {
                "violations_by_run": [
                    {
                        "run_id": str(sr.id),
                        "date": sr.created_at.isoformat(),
                        "violations": sr.acgme_violations or 0
                    }
                    for sr in schedule_runs
                ]
            },
            "recommendations": recommendations,
            "generated_at": datetime.utcnow().isoformat()
        }

    def generate_workload_report(
        self,
        start_date: date,
        end_date: date
    ) -> Dict[str, Any]:
        """
        Generate workload distribution report.

        Args:
            start_date: Start date
            end_date: End date

        Returns:
            Dict with workload report data
        """
        # Get all residents
        residents = self.db.query(Person).filter(Person.type == "resident").all()

        workload_data = []

        for resident in residents:
            # Get assignments
            assignments = self.db.query(Assignment).join(Block).filter(
                and_(
                    Assignment.person_id == resident.id,
                    Block.date >= start_date,
                    Block.date <= end_date
                )
            ).all()

            target_blocks = resident.target_clinical_blocks or 48
            actual_blocks = len(assignments)
            utilization = (actual_blocks / target_blocks * 100) if target_blocks > 0 else 0

            workload_data.append({
                "person_id": str(resident.id),
                "name": resident.name,
                "pgy_level": resident.pgy_level,
                "target_blocks": target_blocks,
                "actual_blocks": actual_blocks,
                "utilization_percent": round(utilization, 2),
                "variance": actual_blocks - target_blocks
            })

        # Calculate fairness
        assignment_dicts = [
            {"person_id": item["person_id"]}
            for item in workload_data
            for _ in range(item["actual_blocks"])
        ]
        fairness = calculate_fairness_index(assignment_dicts)

        # Sort by utilization
        workload_data.sort(key=lambda x: x["utilization_percent"], reverse=True)

        # Identify outliers
        over_utilized = [w for w in workload_data if w["utilization_percent"] > 110]
        under_utilized = [w for w in workload_data if w["utilization_percent"] < 90]

        # Recommendations
        recommendations = []
        if fairness["status"] != "good":
            recommendations.append("Improve workload distribution fairness")
        if over_utilized:
            recommendations.append(
                f"{len(over_utilized)} residents over-utilized (>110% of target)"
            )
        if under_utilized:
            recommendations.append(
                f"{len(under_utilized)} residents under-utilized (<90% of target)"
            )

        return {
            "report_type": "workload",
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            },
            "summary": {
                "total_residents": len(residents),
                "fairness_index": fairness["value"],
                "over_utilized_count": len(over_utilized),
                "under_utilized_count": len(under_utilized)
            },
            "details": {
                "fairness_metric": fairness,
                "workload_by_resident": workload_data
            },
            "charts": {
                "utilization_distribution": [
                    {"name": w["name"], "utilization": w["utilization_percent"]}
                    for w in workload_data
                ],
                "pgy_level_distribution": self._get_pgy_level_distribution(workload_data)
            },
            "recommendations": recommendations,
            "generated_at": datetime.utcnow().isoformat()
        }

    def _get_daily_coverage_chart(
        self,
        blocks: List[Any],
        assignments: List[Any]
    ) -> List[Dict[str, Any]]:
        """Generate daily coverage chart data."""
        coverage_by_date = defaultdict(lambda: {"total": 0, "covered": 0})

        for block in blocks:
            coverage_by_date[block.date]["total"] += 1

        for assignment in assignments:
            coverage_by_date[assignment.block.date]["covered"] += 1

        chart_data = []
        for date in sorted(coverage_by_date.keys()):
            data = coverage_by_date[date]
            coverage_pct = (data["covered"] / data["total"] * 100) if data["total"] > 0 else 0
            chart_data.append({
                "date": date.isoformat(),
                "coverage_percent": round(coverage_pct, 2)
            })

        return chart_data

    def _get_pgy_level_distribution(
        self,
        workload_data: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Generate PGY level distribution chart data."""
        pgy_stats = defaultdict(lambda: {"count": 0, "total_blocks": 0})

        for item in workload_data:
            pgy = item["pgy_level"] or 0
            pgy_stats[pgy]["count"] += 1
            pgy_stats[pgy]["total_blocks"] += item["actual_blocks"]

        chart_data = []
        for pgy_level in sorted(pgy_stats.keys()):
            stats = pgy_stats[pgy_level]
            avg_blocks = stats["total_blocks"] / stats["count"] if stats["count"] > 0 else 0
            chart_data.append({
                "pgy_level": pgy_level,
                "resident_count": stats["count"],
                "average_blocks": round(avg_blocks, 2)
            })

        return chart_data
