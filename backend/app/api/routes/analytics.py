"""Analytics API routes.

Provides endpoints for schedule analytics, metrics tracking, version comparisons,
what-if analysis, and research data exports.
"""

import logging
import statistics
import uuid
from collections import defaultdict
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, and_
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.analytics.engine import AnalyticsEngine
from app.analytics.metrics import (
    calculate_consecutive_duty_stats,
    calculate_coverage_rate,
    calculate_fairness_index,
)
from app.core.security import get_current_active_user
from app.db.session import get_async_db
from app.models.assignment import Assignment
from app.models.block import Block
from app.models.person import Person
from app.models.schedule_run import ScheduleRun
from app.models.user import User
from app.schemas.analytics import (
    AssignmentChange,
    ComplianceData,
    FairnessTrendDataPoint,
    FairnessTrendReport,
    MetricDataPoint,
    MetricTimeSeries,
    MetricValue,
    ResearchDataExport,
    ResidentWorkloadData,
    RotationCoverageData,
    ScheduleVersionMetrics,
    VersionComparison,
    VersionMetricComparison,
    WhatIfMetricImpact,
    WhatIfResult,
    WhatIfViolation,
)

logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================================================
# Helper Functions
# ============================================================================


def _create_metric_value(
    name: str, metric_dict: dict, unit: str | None = None
) -> MetricValue:
    """Convert metric dict to MetricValue schema."""
    return MetricValue(
        name=name,
        value=metric_dict.get("value", 0.0),
        unit=unit,
        status=metric_dict.get("status", "good"),
        trend=metric_dict.get("trend"),
        benchmark=metric_dict.get("benchmark"),
        description=metric_dict.get("description"),
        details=metric_dict.get("details"),
    )


def _anonymize_id(original_id: str, salt: str = "research") -> str:
    """Anonymize an ID for research export."""
    import hashlib

    return hashlib.sha256(f"{original_id}{salt}".encode()).hexdigest()[:16]


# ============================================================================
# Routes
# ============================================================================


@router.get("/analytics/metrics/current", response_model=ScheduleVersionMetrics)
async def get_current_metrics(
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
) -> ScheduleVersionMetrics:
    """
    Get metrics for current live schedule.

    Returns comprehensive metrics for the most recent active schedule,
    including fairness, coverage, ACGME compliance, and workload distribution.
    """
    try:
        # Get the most recent successful schedule run
        latest_run = (
            db.query(ScheduleRun)
            .filter(ScheduleRun.status == "success")
            .order_by(ScheduleRun.created_at.desc())
            .first()
        )

        if not latest_run:
            raise HTTPException(
                status_code=404, detail="No successful schedule runs found"
            )

        # Use analytics engine to get comprehensive data
        engine = AnalyticsEngine(db)
        analysis = engine.analyze_schedule(
            start_date=latest_run.start_date, end_date=latest_run.end_date
        )

        # Convert to response schema
        return ScheduleVersionMetrics(
            versionId=f"run-{latest_run.id}",
            scheduleRunId=latest_run.id,
            timestamp=datetime.utcnow().isoformat() + "Z",
            period={
                "start_date": latest_run.start_date.isoformat(),
                "end_date": latest_run.end_date.isoformat(),
                "total_days": str(
                    (latest_run.end_date - latest_run.start_date).days + 1
                ),
            },
            fairnessIndex=_create_metric_value(
                "Fairness Index", analysis["metrics"]["fairness"]
            ),
            coverageRate=_create_metric_value(
                "Coverage Rate", analysis["metrics"]["coverage"], unit="%"
            ),
            acgmeCompliance=_create_metric_value(
                "ACGME Compliance", analysis["metrics"]["compliance"], unit="%"
            ),
            preferenceSatisfaction=MetricValue(
                name="Preference Satisfaction",
                value=0.0,  # Placeholder - would calculate from preferences
                unit="%",
                status="good",
                description="Preference satisfaction not yet implemented",
            ),
            totalBlocks=analysis["summary"]["total_blocks"],
            totalAssignments=analysis["summary"]["total_assignments"],
            uniqueResidents=analysis["summary"]["unique_people"],
            violations={
                "total": analysis["violations"]["total"],
                "overrides_acknowledged": analysis["violations"][
                    "overrides_acknowledged"
                ],
                "unacknowledged": analysis["violations"]["unacknowledged"],
            },
            workloadDistribution=analysis["workload"],
        )

    except HTTPException:
        raise
    except SQLAlchemyError as e:
        logger.error(f"Database error getting current metrics: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail="Database error occurred retrieving metrics"
        )
    except (ValueError, TypeError, KeyError, AttributeError) as e:
        logger.error(
            f"Data validation error getting current metrics: {e}", exc_info=True
        )
        raise HTTPException(status_code=500, detail="Data validation error occurred")


@router.get("/analytics/metrics/history", response_model=list[MetricTimeSeries])
async def get_metrics_history(
    metric_name: str = Query(
        ..., description="Metric name (fairness, coverage, compliance, violations)"
    ),
    start_date: datetime = Query(..., description="Start date (ISO format)"),
    end_date: datetime = Query(..., description="End date (ISO format)"),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
) -> list[MetricTimeSeries]:
    """
    Get time series of a metric over date range.

    Tracks how a specific metric has changed over time across multiple
    schedule runs or time periods.
    """
    try:
        # Get all schedule runs in the date range
        runs = (
            db.query(ScheduleRun)
            .filter(
                and_(
                    ScheduleRun.start_date >= start_date.date(),
                    ScheduleRun.end_date <= end_date.date(),
                    ScheduleRun.status == "success",
                )
            )
            .order_by(ScheduleRun.created_at)
            .all()
        )

        if not runs:
            return []

        engine = AnalyticsEngine(db)
        data_points = []

        for run in runs:
            try:
                analysis = engine.analyze_schedule(
                    start_date=run.start_date, end_date=run.end_date
                )

                # Extract the requested metric
                value = None
                if metric_name == "fairness":
                    value = analysis["metrics"]["fairness"]["value"]
                elif metric_name == "coverage":
                    value = analysis["metrics"]["coverage"]["value"]
                elif metric_name == "compliance":
                    value = analysis["metrics"]["compliance"]["value"]
                elif metric_name == "violations":
                    value = float(analysis["violations"]["total"])
                else:
                    continue

                data_points.append(
                    MetricDataPoint(
                        timestamp=run.created_at.isoformat() + "Z",
                        value=value,
                        metadata={
                            "run_id": str(run.id),
                            "start_date": run.start_date.isoformat(),
                            "end_date": run.end_date.isoformat(),
                        },
                    )
                )
            except SQLAlchemyError as e:
                logger.warning(
                    f"Database error analyzing run {run.id}: {e}", exc_info=True
                )
                continue
            except (ValueError, TypeError, KeyError, AttributeError) as e:
                logger.warning(
                    f"Data processing error analyzing run {run.id}: {e}", exc_info=True
                )
                continue

        if not data_points:
            return []

        # Calculate statistics
        values = [dp.value for dp in data_points]
        stats = {
            "mean": round(statistics.mean(values), 2),
            "median": round(statistics.median(values), 2),
            "std_dev": round(statistics.stdev(values), 2) if len(values) > 1 else 0.0,
            "min": round(min(values), 2),
            "max": round(max(values), 2),
        }

        # Determine trend direction
        if len(values) >= 2:
            first_half_avg = statistics.mean(values[: len(values) // 2])
            second_half_avg = statistics.mean(values[len(values) // 2 :])
            if metric_name == "violations":
                # For violations, lower is better
                trend = "improving" if second_half_avg < first_half_avg else "declining"
            else:
                # For other metrics, higher is better
                trend = "improving" if second_half_avg > first_half_avg else "declining"
            if abs(second_half_avg - first_half_avg) < 0.01:
                trend = "stable"
        else:
            trend = "stable"

        return [
            MetricTimeSeries(
                metricName=metric_name,
                startDate=start_date.isoformat(),
                endDate=end_date.isoformat(),
                dataPoints=data_points,
                statistics=stats,
                trendDirection=trend,
            )
        ]

    except SQLAlchemyError as e:
        logger.error(f"Database error getting metrics history: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail="Database error occurred retrieving metrics history"
        )
    except (ValueError, TypeError, KeyError, AttributeError) as e:
        logger.error(
            f"Data processing error getting metrics history: {e}", exc_info=True
        )
        raise HTTPException(status_code=500, detail="Data processing error occurred")


@router.get("/analytics/fairness/trend", response_model=FairnessTrendReport)
async def get_fairness_trend(
    months: int = Query(6, ge=1, le=24, description="Number of months to analyze"),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
) -> FairnessTrendReport:
    """
    Get fairness metrics trend over time.

    Analyzes how workload fairness has evolved over the specified number of months,
    providing insights into distribution equity trends.
    """
    try:
        # Calculate date range
        end_date = datetime.utcnow().date()
        start_date = (datetime.utcnow() - timedelta(days=months * 30)).date()

        # Get schedule runs in the period
        runs = (
            db.query(ScheduleRun)
            .filter(
                and_(
                    ScheduleRun.start_date >= start_date,
                    ScheduleRun.status == "success",
                )
            )
            .order_by(ScheduleRun.created_at)
            .all()
        )

        if not runs:
            raise HTTPException(
                status_code=404,
                detail=f"No schedule runs found in the last {months} months",
            )

        engine = AnalyticsEngine(db)
        data_points = []
        fairness_values = []

        for run in runs:
            try:
                analysis = engine.analyze_schedule(
                    start_date=run.start_date, end_date=run.end_date
                )

                fairness = analysis["metrics"]["fairness"]
                fairness_index = fairness["value"]
                gini = 1 - fairness_index  # Convert back to Gini

                data_points.append(
                    FairnessTrendDataPoint(
                        date=run.start_date.isoformat(),
                        fairnessIndex=fairness_index,
                        giniCoefficient=round(gini, 3),
                        residentsCount=analysis["summary"]["unique_people"],
                    )
                )
                fairness_values.append(fairness_index)

            except SQLAlchemyError as e:
                logger.warning(
                    f"Database error analyzing run {run.id}: {e}", exc_info=True
                )
                continue
            except (ValueError, TypeError, KeyError, AttributeError) as e:
                logger.warning(
                    f"Data processing error analyzing run {run.id}: {e}", exc_info=True
                )
                continue

        if not data_points:
            raise HTTPException(
                status_code=500, detail="Could not analyze any schedule runs"
            )

        # Calculate statistics
        avg_fairness = statistics.mean(fairness_values)

        # Determine trend
        if len(fairness_values) >= 2:
            first_half_avg = statistics.mean(
                fairness_values[: len(fairness_values) // 2]
            )
            second_half_avg = statistics.mean(
                fairness_values[len(fairness_values) // 2 :]
            )
            if second_half_avg > first_half_avg + 0.02:
                trend = "improving"
            elif second_half_avg < first_half_avg - 0.02:
                trend = "declining"
            else:
                trend = "stable"
        else:
            trend = "stable"

        # Find most/least fair periods
        sorted_points = sorted(data_points, key=lambda x: x.fairness_index)
        most_unfair = sorted_points[0].date if sorted_points else None
        most_fair = sorted_points[-1].date if sorted_points else None

        # Generate recommendations
        recommendations = []
        if avg_fairness < 0.85:
            recommendations.append(
                "Overall fairness is below target - review workload distribution policies"
            )
        if trend == "declining":
            recommendations.append(
                "Fairness is declining - investigate recent scheduling changes"
            )
        elif trend == "improving":
            recommendations.append(
                "Fairness is improving - current approach is effective"
            )
        if len({dp.residents_count for dp in data_points}) > 1:
            recommendations.append(
                "Resident count has changed - ensure fairness metrics account for cohort size"
            )

        return FairnessTrendReport(
            periodMonths=months,
            startDate=start_date.isoformat(),
            endDate=end_date.isoformat(),
            dataPoints=data_points,
            averageFairness=round(avg_fairness, 3),
            trend=trend,
            mostUnfairPeriod=most_unfair,
            mostFairPeriod=most_fair,
            recommendations=recommendations,
        )

    except HTTPException:
        raise
    except SQLAlchemyError as e:
        logger.error(f"Database error getting fairness trend: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail="Database error occurred retrieving fairness trend"
        )
    except (ValueError, TypeError, KeyError, AttributeError) as e:
        logger.error(
            f"Data processing error getting fairness trend: {e}", exc_info=True
        )
        raise HTTPException(status_code=500, detail="Data processing error occurred")


@router.get(
    "/analytics/compare/{version_a}/{version_b}", response_model=VersionComparison
)
async def compare_versions(
    version_a: str,
    version_b: str,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
) -> VersionComparison:
    """
    Compare metrics between two schedule versions.

    Provides detailed side-by-side comparison of metrics, violations,
    and overall quality between two schedule versions.
    """
    try:
        engine = AnalyticsEngine(db)

        # For now, treat version as run_id
        # In a more sophisticated system, you might have version management
        run_a = (
            await db.execute(select(ScheduleRun).where(ScheduleRun.id == version_a))
        ).scalar_one_or_none()
        run_b = (
            await db.execute(select(ScheduleRun).where(ScheduleRun.id == version_b))
        ).scalar_one_or_none()

        if not run_a or not run_b:
            raise HTTPException(
                status_code=404, detail="One or both schedule versions not found"
            )

        # Analyze both versions
        analysis_a = engine.analyze_schedule(run_a.start_date, run_a.end_date)
        analysis_b = engine.analyze_schedule(run_b.start_date, run_b.end_date)

        # Compare metrics
        metrics_to_compare = [
            ("fairness", "Fairness Index", True),
            ("coverage", "Coverage Rate", True),
            ("compliance", "ACGME Compliance", True),
        ]

        metric_comparisons = []
        improvement_count = 0

        for metric_key, metric_name, higher_is_better in metrics_to_compare:
            val_a = analysis_a["metrics"][metric_key]["value"]
            val_b = analysis_b["metrics"][metric_key]["value"]
            diff = val_b - val_a
            pct_change = (diff / val_a * 100) if val_a != 0 else 0

            improved = (diff > 0) if higher_is_better else (diff < 0)
            if improved:
                improvement_count += 1

            metric_comparisons.append(
                VersionMetricComparison(
                    metricName=metric_name,
                    versionAValue=round(val_a, 2),
                    versionBValue=round(val_b, 2),
                    difference=round(diff, 2),
                    percentChange=round(pct_change, 2),
                    improvement=improved,
                )
            )

        # Add violations comparison
        violations_a = analysis_a["violations"]["total"]
        violations_b = analysis_b["violations"]["total"]
        violations_diff = violations_b - violations_a

        metric_comparisons.append(
            VersionMetricComparison(
                metricName="Total Violations",
                versionAValue=float(violations_a),
                versionBValue=float(violations_b),
                difference=float(violations_diff),
                percentChange=round(
                    (violations_diff / violations_a * 100) if violations_a != 0 else 0,
                    2,
                ),
                improvement=violations_diff < 0,  # Lower is better
            )
        )

        if violations_diff < 0:
            improvement_count += 1

        # Calculate overall improvement
        overall_improvement = improvement_count > len(metric_comparisons) / 2
        improvement_score = (improvement_count / len(metric_comparisons)) * 100

        # Calculate assignment changes (simplified - would need more complex logic)
        assignments_a = analysis_a["summary"]["total_assignments"]
        assignments_b = analysis_b["summary"]["total_assignments"]
        assignments_changed = abs(assignments_b - assignments_a)

        residents_affected = max(
            analysis_a["summary"]["unique_people"],
            analysis_b["summary"]["unique_people"],
        )

        # Generate summary
        if overall_improvement:
            summary = f"Version B shows improvement in {improvement_count} out of {len(metric_comparisons)} metrics."
        else:
            summary = f"Version B shows regression in {len(metric_comparisons) - improvement_count} metrics."

        # Generate recommendations
        recommendations = []
        for comp in metric_comparisons:
            if not comp.improvement:
                recommendations.append(
                    f"Address decline in {comp.metric_name} ({comp.percent_change:+.1f}%)"
                )

        if not recommendations:
            recommendations.append(
                "Version B is ready for deployment - all metrics improved or stable"
            )

        return VersionComparison(
            versionA=version_a,
            versionB=version_b,
            timestamp=datetime.utcnow().isoformat() + "Z",
            metrics=metric_comparisons,
            overallImprovement=overall_improvement,
            improvementScore=round(improvement_score, 2),
            assignmentsChanged=assignments_changed,
            residentsAffected=residents_affected,
            summary=summary,
            recommendations=recommendations,
        )

    except HTTPException:
        raise
    except SQLAlchemyError as e:
        logger.error(f"Database error comparing versions: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail="Database error occurred comparing versions"
        )
    except (ValueError, TypeError, KeyError, AttributeError) as e:
        logger.error(f"Data processing error comparing versions: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Data processing error occurred")


@router.post("/analytics/what-if", response_model=WhatIfResult)
async def what_if_analysis(
    proposed_changes: list[AssignmentChange],
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
) -> WhatIfResult:
    """
    Predict metric impact of proposed changes.

    Analyzes the potential impact of proposed assignment changes on key metrics
    before actually applying them. Helps validate scheduling decisions.
    """
    try:
        if not proposed_changes:
            raise HTTPException(
                status_code=400, detail="No changes provided for analysis"
            )

        # Get current state
        latest_run = (
            db.query(ScheduleRun)
            .filter(ScheduleRun.status == "success")
            .order_by(ScheduleRun.created_at.desc())
            .first()
        )

        if not latest_run:
            raise HTTPException(
                status_code=404, detail="No baseline schedule found for comparison"
            )

        engine = AnalyticsEngine(db)
        current_analysis = engine.analyze_schedule(
            latest_run.start_date, latest_run.end_date
        )

        # Simulate the changes (simplified - in production would create temp tables)
        # For now, just provide estimated impacts based on change types

        metric_impacts = []
        new_violations = []
        affected_residents = set()
        workload_changes = {}

        # Analyze each change
        for change in proposed_changes:
            person = (
                await db.execute(select(Person).where(Person.id == change.person_id))
            ).scalar_one_or_none()
            if person:
                affected_residents.add(person.name)

                # Get current workload
                current_assignments = (
                    db.query(Assignment)
                    .join(Block)
                    .options(
                        joinedload(Assignment.block), joinedload(Assignment.person)
                    )
                    .filter(
                        and_(
                            Assignment.person_id == change.person_id,
                            Block.date >= latest_run.start_date,
                            Block.date <= latest_run.end_date,
                        )
                    )
                    .count()
                )

                # Estimate workload change
                if change.change_type == "add":
                    new_assignments = current_assignments + 1
                elif change.change_type == "remove":
                    new_assignments = current_assignments - 1
                else:
                    new_assignments = current_assignments

                target = person.target_clinical_blocks or 48
                old_util = (current_assignments / target * 100) if target > 0 else 0
                new_util = (new_assignments / target * 100) if target > 0 else 0

                workload_changes[person.name] = {
                    "old_utilization": round(old_util, 2),
                    "new_utilization": round(new_util, 2),
                    "change": round(new_util - old_util, 2),
                }

                # Check for potential violations
                if new_assignments > target * 1.1:
                    new_violations.append(
                        WhatIfViolation(
                            type="WORKLOAD_EXCESS",
                            severity="warning",
                            personId=change.person_id,
                            personName=person.name,
                            message=f"Would exceed target workload by {new_assignments - target} blocks",
                        )
                    )

        # Estimate fairness impact (simplified)
        fairness_impact = "neutral"
        if len(workload_changes) > 0:
            util_changes = [wc["change"] for wc in workload_changes.values()]
            avg_change = statistics.mean([abs(c) for c in util_changes])
            if avg_change > 5:
                fairness_impact = "negative"
            elif avg_change < 2:
                fairness_impact = "positive"

        metric_impacts.append(
            WhatIfMetricImpact(
                metricName="Fairness Index",
                currentValue=current_analysis["metrics"]["fairness"]["value"],
                predictedValue=current_analysis["metrics"]["fairness"]["value"]
                - (0.02 if fairness_impact == "negative" else 0),
                change=-0.02 if fairness_impact == "negative" else 0,
                impactSeverity=fairness_impact,
                confidence=0.7,
            )
        )

        # Overall assessment
        if new_violations:
            overall_impact = "negative"
            safe_to_apply = False
            recommendation = f"Not recommended - would introduce {len(new_violations)} new violations"
        elif fairness_impact == "negative":
            overall_impact = "mixed"
            safe_to_apply = True
            recommendation = "Proceed with caution - may impact fairness metrics"
        else:
            overall_impact = "positive"
            safe_to_apply = True
            recommendation = "Changes appear safe to apply"

        return WhatIfResult(
            timestamp=datetime.utcnow().isoformat() + "Z",
            changesAnalyzed=len(proposed_changes),
            metricImpacts=metric_impacts,
            newViolations=new_violations,
            resolvedViolations=[],  # Would need to check if changes fix existing violations
            overallImpact=overall_impact,
            recommendation=recommendation,
            safeToApply=safe_to_apply,
            affectedResidents=list(affected_residents),
            workloadChanges=workload_changes,
        )

    except HTTPException:
        raise
    except SQLAlchemyError as e:
        logger.error(f"Database error in what-if analysis: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Database error occurred performing what-if analysis",
        )
    except (ValueError, TypeError, KeyError, AttributeError) as e:
        logger.error(f"Data processing error in what-if analysis: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Data processing error occurred")


@router.get("/analytics/export/research", response_model=ResearchDataExport)
async def export_for_research(
    start_date: datetime = Query(..., description="Start date (ISO format)"),
    end_date: datetime = Query(..., description="End date (ISO format)"),
    anonymize: bool = Query(True, description="Anonymize sensitive data"),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
) -> ResearchDataExport:
    """
    Export anonymized data for research/publication.

    Provides comprehensive, optionally anonymized schedule data suitable for
    research, academic publication, or external analysis.
    """
    try:
        # Get all data in date range
        blocks = (
            db.query(Block)
            .filter(
                and_(Block.date >= start_date.date(), Block.date <= end_date.date())
            )
            .limit(100)
            .all()
        )

        assignments = (
            db.query(Assignment)
            .join(Block)
            .options(
                joinedload(Assignment.block),
                joinedload(Assignment.person),
                joinedload(Assignment.rotation_template),
            )
            .filter(
                and_(Block.date >= start_date.date(), Block.date <= end_date.date())
            )
            .limit(100)
            .all()
        )

        # Get all residents
        resident_ids = {a.person_id for a in assignments}
        residents = (
            db.query(Person).filter(Person.id.in_(resident_ids)).limit(100).all()
        )

        # Build resident workload data
        resident_workload = []
        for resident in residents:
            person_assignments = [a for a in assignments if a.person_id == resident.id]

            # Calculate stats
            assignment_dicts = [
                {
                    "id": str(a.id),
                    "person_id": str(a.person_id),
                    "block_id": str(a.block_id),
                    "block_date": a.block.date,
                }
                for a in person_assignments
            ]

            duty_stats = calculate_consecutive_duty_stats(
                str(resident.id), assignment_dicts
            )

            # Count clinical vs non-clinical (simplified)
            clinical_blocks = len(person_assignments)  # Would need more logic
            non_clinical_blocks = 0

            target = resident.target_clinical_blocks or 48
            utilization = (len(person_assignments) / target * 100) if target > 0 else 0

            resident_id = (
                _anonymize_id(str(resident.id)) if anonymize else str(resident.id)
            )

            resident_workload.append(
                ResidentWorkloadData(
                    residentId=resident_id,
                    pgyLevel=resident.pgy_level or 1,
                    totalBlocks=len(person_assignments),
                    targetBlocks=target,
                    utilizationPercent=round(utilization, 2),
                    clinicalBlocks=clinical_blocks,
                    nonClinicalBlocks=non_clinical_blocks,
                    maxConsecutiveDays=duty_stats["max_consecutive_days"],
                    averageRestDays=duty_stats["average_rest_days"],
                )
            )

        # Build rotation coverage data
        rotation_counts = defaultdict(lambda: {"assignments": 0, "residents": set()})
        for assignment in assignments:
            if assignment.rotation_template:
                key = str(assignment.rotation_template_id)
                rotation_counts[key]["assignments"] += 1
                rotation_counts[key]["residents"].add(assignment.person_id)

        rotation_coverage = []
        for rotation_id, data in rotation_counts.items():
            rotation_id_display = (
                _anonymize_id(rotation_id) if anonymize else rotation_id
            )
            rotation_coverage.append(
                RotationCoverageData(
                    rotationId=rotation_id_display,
                    rotationType="clinical",  # Would need more logic
                    activityType="clinical",
                    totalAssignments=data["assignments"],
                    uniqueResidents=len(data["residents"]),
                    averageDuration=4.0,  # Placeholder
                )
            )

        # Compliance data
        runs = (
            db.query(ScheduleRun)
            .filter(
                and_(
                    ScheduleRun.start_date >= start_date.date(),
                    ScheduleRun.end_date <= end_date.date(),
                )
            )
            .all()
        )

        total_violations = sum(r.acgme_violations or 0 for r in runs)
        total_overrides = sum(r.acgme_override_count or 0 for r in runs)
        total_checks = len(blocks)
        compliance_rate = (
            ((total_checks - total_violations) / total_checks * 100)
            if total_checks > 0
            else 100
        )

        compliance_data = ComplianceData(
            totalChecks=total_checks,
            totalViolations=total_violations,
            complianceRate=round(compliance_rate, 2),
            violationsByType={
                "unspecified": total_violations
            },  # Would need more detail
            violationsBySeverity={"high": total_violations},  # Would need more detail
            overrideCount=total_overrides,
        )

        # Calculate aggregate metrics
        assignment_dicts = [
            {"person_id": str(a.person_id), "block_id": str(a.block_id)}
            for a in assignments
        ]
        block_dicts = [{"id": str(b.id)} for b in blocks]

        fairness = calculate_fairness_index(assignment_dicts)
        coverage = calculate_coverage_rate(block_dicts, assignment_dicts)

        fairness_metrics = {
            "fairness_index": fairness["value"],
            "gini_coefficient": 1 - fairness["value"],
            "min_assignments": fairness["details"]["min_assignments"],
            "max_assignments": fairness["details"]["max_assignments"],
            "mean_assignments": fairness["details"]["mean_assignments"],
        }

        coverage_metrics = {
            "coverage_rate": coverage["value"],
            "total_blocks": coverage["details"]["total_blocks"],
            "covered_blocks": coverage["details"]["covered_blocks"],
            "uncovered_blocks": coverage["details"]["uncovered_blocks"],
        }

        return ResearchDataExport(
            exportId=str(uuid.uuid4()),
            timestamp=datetime.utcnow().isoformat() + "Z",
            anonymized=anonymize,
            startDate=start_date.date().isoformat(),
            endDate=end_date.date().isoformat(),
            totalResidents=len(residents),
            totalBlocks=len(blocks),
            totalAssignments=len(assignments),
            totalRotations=len(rotation_coverage),
            residentWorkload=resident_workload,
            rotationCoverage=rotation_coverage,
            complianceData=compliance_data,
            fairnessMetrics=fairness_metrics,
            coverageMetrics=coverage_metrics,
            institutionType="Military Medical Facility" if not anonymize else None,
            programSize="medium" if len(residents) < 50 else "large",
            speciality="Emergency Medicine" if not anonymize else None,
            notes="Exported for research analysis",
        )

    except HTTPException:
        raise
    except SQLAlchemyError as e:
        logger.error(f"Database error exporting research data: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail="Database error occurred exporting research data"
        )
    except (ValueError, TypeError, KeyError, AttributeError) as e:
        logger.error(
            f"Data processing error exporting research data: {e}", exc_info=True
        )
        raise HTTPException(status_code=500, detail="Data processing error occurred")
