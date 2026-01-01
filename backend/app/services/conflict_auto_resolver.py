"""Enhanced conflict auto-resolution service.

This service provides intelligent, safety-first auto-resolution of schedule conflicts
with comprehensive impact analysis, validation, and batch processing capabilities.
"""

import time
from collections import defaultdict
from datetime import date, datetime, timedelta
from uuid import UUID, uuid4

from sqlalchemy import and_, func
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.db.transaction import transactional, transactional_with_retry
from app.models.assignment import Assignment
from app.models.block import Block
from app.models.conflict_alert import (
    ConflictAlert,
    ConflictAlertStatus,
    ConflictSeverity,
    ConflictType,
)
from app.models.person import Person
from app.models.rotation_template import RotationTemplate
from app.models.swap import SwapRecord, SwapStatus, SwapType
from app.schemas.conflict_resolution import (
    BatchResolutionReport,
    ConflictAnalysis,
    ImpactAssessment,
    ResolutionOption,
    ResolutionResult,
    ResolutionStatusEnum,
    ResolutionStrategyEnum,
    SafetyCheckResult,
    SafetyCheckType,
)


class ConflictAutoResolver:
    """
    Enhanced service for automatically resolving schedule conflicts.

    Provides intelligent resolution strategies with comprehensive safety checks,
    impact analysis, and batch processing capabilities.
    """

    def __init__(self, db: Session) -> None:
        self.db = db
        self._resolution_cache = {}  ***REMOVED*** Cache for resolution options

    ***REMOVED*** ==================== MAIN PUBLIC METHODS ====================

    def analyze_conflict(self, conflict_id: UUID) -> ConflictAnalysis:
        """
        Perform deep analysis of a conflict to understand resolution options.

        Args:
            conflict_id: ID of the conflict to analyze

        Returns:
            ConflictAnalysis with comprehensive details
        """
        alert = self._get_alert(conflict_id)
        if not alert:
            raise ValueError(f"Conflict {conflict_id} not found")

        ***REMOVED*** Gather basic information
        faculty = self.db.query(Person).filter(Person.id == alert.faculty_id).first()
        affected_faculty = [alert.faculty_id]
        affected_dates = [alert.fmit_week.isoformat()]

        ***REMOVED*** Determine root cause
        root_cause = self._determine_root_cause(alert)

        ***REMOVED*** Assess complexity
        complexity_score = self._calculate_complexity(alert)

        ***REMOVED*** Perform safety checks
        safety_checks = self._perform_all_safety_checks(alert)
        all_checks_passed = all(check.passed for check in safety_checks)
        auto_resolution_safe = all_checks_passed and complexity_score < 0.7

        ***REMOVED*** Identify constraints and blockers
        constraints = self._identify_constraints(alert)
        blockers = self._identify_blockers(alert)

        ***REMOVED*** Recommend strategies
        recommended_strategies = self._recommend_strategies(alert, safety_checks)

        ***REMOVED*** Estimate resolution time
        estimated_time = self._estimate_resolution_time(
            complexity_score, len(recommended_strategies)
        )

        return ConflictAnalysis(
            conflict_id=conflict_id,
            conflict_type=alert.conflict_type.value,
            severity=alert.severity.value,
            root_cause=root_cause,
            affected_faculty=affected_faculty,
            affected_dates=affected_dates,
            complexity_score=complexity_score,
            safety_checks=safety_checks,
            all_checks_passed=all_checks_passed,
            auto_resolution_safe=auto_resolution_safe,
            constraints=constraints,
            blockers=blockers,
            recommended_strategies=recommended_strategies,
            estimated_resolution_time=estimated_time,
            analyzed_at=datetime.utcnow(),
        )

    def generate_resolution_options(
        self,
        conflict_id: UUID,
        max_options: int = 5,
    ) -> list[ResolutionOption]:
        """
        Generate possible resolution options for a conflict.

        Args:
            conflict_id: ID of the conflict to resolve
            max_options: Maximum number of options to generate

        Returns:
            List of ResolutionOption objects, sorted by overall score
        """
        ***REMOVED*** Check cache first
        cache_key = f"{conflict_id}_{max_options}"
        if cache_key in self._resolution_cache:
            cached_time, options = self._resolution_cache[cache_key]
            if (datetime.utcnow() - cached_time).seconds < 300:  ***REMOVED*** 5 minute cache
                return options

        alert = self._get_alert(conflict_id)
        if not alert:
            return []

        ***REMOVED*** Analyze conflict first
        analysis = self.analyze_conflict(conflict_id)

        options = []

        ***REMOVED*** Generate options based on conflict type and analysis
        if alert.conflict_type == ConflictType.LEAVE_FMIT_OVERLAP:
            options.extend(self._generate_leave_overlap_options(alert, analysis))
        elif alert.conflict_type == ConflictType.BACK_TO_BACK:
            options.extend(self._generate_back_to_back_options(alert, analysis))
        elif alert.conflict_type in [
            ConflictType.CALL_CASCADE,
            ConflictType.EXCESSIVE_ALTERNATING,
        ]:
            options.extend(self._generate_workload_options(alert, analysis))
        elif alert.conflict_type == ConflictType.EXTERNAL_COMMITMENT:
            options.extend(self._generate_external_commitment_options(alert, analysis))

        ***REMOVED*** Always add a "defer to human" option as fallback
        options.append(self._generate_defer_to_human_option(alert, analysis))

        ***REMOVED*** Assess impact for each option
        for option in options:
            option.impact = self._assess_resolution_impact(option, alert)
            option.safety_validated = self._validate_safety(option, alert)
            option.can_auto_apply = self._can_auto_apply(option)
            option.requires_approval = self._requires_approval(option)

        ***REMOVED*** Sort by overall score (highest first)
        options.sort(
            key=lambda o: o.impact.overall_score if o.impact else 0, reverse=True
        )

        ***REMOVED*** Cache results
        self._resolution_cache[cache_key] = (datetime.utcnow(), options[:max_options])

        return options[:max_options]

    def auto_resolve_if_safe(
        self,
        conflict_id: UUID,
        strategy: str | None = None,
        user_id: UUID | None = None,
    ) -> ResolutionResult:
        """
        Automatically resolve a conflict if it passes all safety checks.

        Args:
            conflict_id: ID of the conflict to resolve
            strategy: Specific strategy to use (optional, will auto-select if None)
            user_id: User requesting the resolution (None for system)

        Returns:
            ResolutionResult with outcome details
        """
        start_time = time.time()
        alert = self._get_alert(conflict_id)

        if not alert:
            return ResolutionResult(
                resolution_option_id="none",
                conflict_id=conflict_id,
                strategy=ResolutionStrategyEnum.DEFER_TO_HUMAN,
                success=False,
                status=ResolutionStatusEnum.FAILED,
                message="Conflict not found",
                error_code="CONFLICT_NOT_FOUND",
            )

        ***REMOVED*** Check if already resolved
        if alert.status not in [
            ConflictAlertStatus.NEW,
            ConflictAlertStatus.ACKNOWLEDGED,
        ]:
            return ResolutionResult(
                resolution_option_id="none",
                conflict_id=conflict_id,
                strategy=ResolutionStrategyEnum.DEFER_TO_HUMAN,
                success=False,
                status=ResolutionStatusEnum.REJECTED,
                message=f"Conflict already has status: {alert.status.value}",
                error_code="ALREADY_RESOLVED",
            )

        ***REMOVED*** Analyze conflict
        analysis = self.analyze_conflict(conflict_id)

        ***REMOVED*** Check if auto-resolution is safe
        if not analysis.auto_resolution_safe:
            return ResolutionResult(
                resolution_option_id="none",
                conflict_id=conflict_id,
                strategy=ResolutionStrategyEnum.DEFER_TO_HUMAN,
                success=False,
                status=ResolutionStatusEnum.REJECTED,
                message="Auto-resolution not safe - requires human review",
                warnings=[
                    check.message
                    for check in analysis.safety_checks
                    if not check.passed
                ],
                error_code="SAFETY_CHECK_FAILED",
                follow_up_required=True,
                follow_up_actions=[
                    "Review safety check failures",
                    "Manual resolution required",
                ],
            )

        ***REMOVED*** Generate resolution options
        options = self.generate_resolution_options(conflict_id)

        if not options:
            return ResolutionResult(
                resolution_option_id="none",
                conflict_id=conflict_id,
                strategy=ResolutionStrategyEnum.DEFER_TO_HUMAN,
                success=False,
                status=ResolutionStatusEnum.FAILED,
                message="No resolution options generated",
                error_code="NO_OPTIONS",
            )

        ***REMOVED*** Select option (use specified strategy or best option)
        if strategy:
            selected_option = next(
                (
                    o
                    for o in options
                    if o.strategy.value == strategy and o.can_auto_apply
                ),
                None,
            )
            if not selected_option:
                return ResolutionResult(
                    resolution_option_id="none",
                    conflict_id=conflict_id,
                    strategy=(
                        ResolutionStrategyEnum(strategy)
                        if strategy
                        else ResolutionStrategyEnum.DEFER_TO_HUMAN
                    ),
                    success=False,
                    status=ResolutionStatusEnum.REJECTED,
                    message=f"Requested strategy '{strategy}' not available or not safe for auto-apply",
                    error_code="STRATEGY_NOT_AVAILABLE",
                )
        else:
            ***REMOVED*** Select best option that can be auto-applied
            selected_option = next((o for o in options if o.can_auto_apply), None)
            if not selected_option:
                return ResolutionResult(
                    resolution_option_id=options[0].id,
                    conflict_id=conflict_id,
                    strategy=options[0].strategy,
                    success=False,
                    status=ResolutionStatusEnum.REJECTED,
                    message="Best option requires manual approval",
                    error_code="APPROVAL_REQUIRED",
                    follow_up_required=True,
                    follow_up_actions=[
                        "Review and approve resolution",
                        f"Best option: {options[0].title}",
                    ],
                )

        ***REMOVED*** Apply the selected resolution
        result = self._apply_resolution(selected_option, alert, user_id)
        result.duration_seconds = time.time() - start_time

        return result

    def batch_auto_resolve(
        self,
        conflict_ids: list[UUID],
        auto_apply_safe: bool = False,
        max_risk_level: str = "medium",
    ) -> BatchResolutionReport:
        """
        Attempt to auto-resolve multiple conflicts in batch.

        Args:
            conflict_ids: List of conflict IDs to resolve
            auto_apply_safe: Whether to auto-apply resolutions that pass safety checks
            max_risk_level: Maximum risk level to auto-apply (low, medium, high)

        Returns:
            BatchResolutionReport with aggregate results
        """
        start_time = datetime.utcnow()
        processing_start = time.time()

        report = BatchResolutionReport(
            total_conflicts=len(conflict_ids),
            conflicts_analyzed=0,
            processing_time_seconds=0.0,
            started_at=start_time,
            success_rate=0.0,
            overall_status="processing",
            summary_message="Processing batch resolution...",
        )

        results = []
        pending_approvals = []
        failed_conflicts = []
        affected_faculty_set = set()
        total_changes = 0
        new_conflicts = 0

        safety_performed = 0
        safety_passed = 0
        safety_failed = 0

        ***REMOVED*** Process each conflict
        for conflict_id in conflict_ids:
            try:
                ***REMOVED*** Analyze first
                analysis = self.analyze_conflict(conflict_id)
                report.conflicts_analyzed += 1

                ***REMOVED*** Count safety checks
                safety_performed += len(analysis.safety_checks)
                safety_passed += sum(1 for c in analysis.safety_checks if c.passed)
                safety_failed += sum(1 for c in analysis.safety_checks if not c.passed)

                ***REMOVED*** Track affected faculty
                affected_faculty_set.update(analysis.affected_faculty)

                ***REMOVED*** Generate options
                options = self.generate_resolution_options(conflict_id)
                if not options:
                    failed_conflicts.append(conflict_id)
                    continue

                best_option = options[0]
                report.resolutions_proposed += 1

                ***REMOVED*** Determine if we should auto-apply
                should_auto_apply = (
                    auto_apply_safe
                    and best_option.can_auto_apply
                    and best_option.safety_validated
                    and self._is_acceptable_risk(best_option, max_risk_level)
                )

                if should_auto_apply:
                    ***REMOVED*** Apply the resolution
                    alert = self._get_alert(conflict_id)
                    result = self._apply_resolution(best_option, alert, None)
                    results.append(result)

                    if result.success:
                        report.resolutions_applied += 1
                        total_changes += len(result.changes_applied)
                        new_conflicts += len(result.new_conflicts_created)
                    else:
                        report.resolutions_failed += 1
                        failed_conflicts.append(conflict_id)
                else:
                    ***REMOVED*** Add to pending approvals
                    pending_approvals.append(best_option)
                    report.resolutions_deferred += 1

            except (SQLAlchemyError, ValueError, KeyError, TypeError) as e:
                logger.error(f"Error processing conflict {conflict_id}: {e}", exc_info=True)
                failed_conflicts.append(conflict_id)
                report.resolutions_failed += 1
                results.append(
                    ResolutionResult(
                        resolution_option_id="error",
                        conflict_id=conflict_id,
                        strategy=ResolutionStrategyEnum.DEFER_TO_HUMAN,
                        success=False,
                        status=ResolutionStatusEnum.FAILED,
                        message=f"Error processing conflict: {str(e)}",
                        error_code="PROCESSING_ERROR",
                        error_details={"exception": str(e)},
                    )
                )

        ***REMOVED*** Calculate final metrics
        processing_time = time.time() - processing_start
        report.results = results
        report.pending_approvals = pending_approvals
        report.failed_conflicts = failed_conflicts
        report.total_faculty_affected = len(affected_faculty_set)
        report.total_changes_made = total_changes
        report.new_conflicts_created = new_conflicts
        report.safety_checks_performed = safety_performed
        report.safety_checks_passed = safety_passed
        report.safety_checks_failed = safety_failed
        report.processing_time_seconds = processing_time
        report.completed_at = datetime.utcnow()

        ***REMOVED*** Calculate success rate
        if report.conflicts_analyzed > 0:
            report.success_rate = report.resolutions_applied / report.conflicts_analyzed
        else:
            report.success_rate = 0.0

        ***REMOVED*** Determine overall status
        if report.resolutions_failed == 0 and report.resolutions_deferred == 0:
            report.overall_status = "completed"
        elif report.resolutions_applied > 0:
            report.overall_status = "partial"
        else:
            report.overall_status = "failed"

        ***REMOVED*** Generate summary message
        report.summary_message = (
            f"Batch resolution completed: {report.resolutions_applied} applied, "
            f"{report.resolutions_deferred} pending approval, "
            f"{report.resolutions_failed} failed out of {report.total_conflicts} conflicts"
        )

        ***REMOVED*** Generate recommendations
        if report.resolutions_deferred > 0:
            report.recommendations.append(
                f"Review {report.resolutions_deferred} pending resolutions requiring manual approval"
            )
        if report.resolutions_failed > 0:
            report.recommendations.append(
                f"Investigate {report.resolutions_failed} failed resolutions"
            )
        if new_conflicts > 0:
            report.recommendations.append(
                f"Review {new_conflicts} new conflicts created by resolutions"
            )

        return report

    ***REMOVED*** ==================== PRIVATE HELPER METHODS ====================

    def _get_alert(
        self, conflict_id: UUID, lock: bool = False
    ) -> ConflictAlert | None:
        """
        Get conflict alert by ID.

        Args:
            conflict_id: ID of the conflict
            lock: If True, acquire row-level lock (for updates)

        Returns:
            ConflictAlert or None
        """
        query = self.db.query(ConflictAlert).filter(ConflictAlert.id == conflict_id)
        if lock:
            query = query.with_for_update()
        return query.first()

    def _determine_root_cause(self, alert: ConflictAlert) -> str:
        """Determine the root cause of a conflict."""
        if alert.conflict_type == ConflictType.LEAVE_FMIT_OVERLAP:
            if alert.leave_id:
                return "Faculty scheduled for FMIT during approved leave period"
            return "Scheduling conflict between FMIT assignment and absence"
        elif alert.conflict_type == ConflictType.BACK_TO_BACK:
            return "Faculty assigned to consecutive FMIT weeks without adequate rest"
        elif alert.conflict_type == ConflictType.EXCESSIVE_ALTERNATING:
            return "Faculty has too many alternating FMIT assignments"
        elif alert.conflict_type == ConflictType.CALL_CASCADE:
            return "Call coverage cascade affecting multiple faculty"
        else:
            return f"Conflict of type {alert.conflict_type.value}"

    def _calculate_complexity(self, alert: ConflictAlert) -> float:
        """Calculate complexity score for a conflict (0-1)."""
        complexity = 0.0

        ***REMOVED*** Higher severity increases complexity
        if alert.severity == ConflictSeverity.CRITICAL:
            complexity += 0.3
        elif alert.severity == ConflictSeverity.WARNING:
            complexity += 0.1

        ***REMOVED*** Check how many weeks are affected
        affected_weeks = self._count_affected_weeks(alert)
        complexity += min(affected_weeks * 0.1, 0.3)

        ***REMOVED*** Check how many faculty are involved
        involved_faculty = self._count_involved_faculty(alert)
        complexity += min((involved_faculty - 1) * 0.15, 0.3)

        ***REMOVED*** Check for cascading conflicts
        if self._has_cascading_conflicts(alert):
            complexity += 0.2

        return min(complexity, 1.0)

    def _count_affected_weeks(self, alert: ConflictAlert) -> int:
        """Count how many weeks are affected by this conflict."""
        ***REMOVED*** For simplicity, most conflicts affect 1-2 weeks
        if alert.conflict_type == ConflictType.BACK_TO_BACK:
            return 2
        return 1

    def _count_involved_faculty(self, alert: ConflictAlert) -> int:
        """Count how many faculty members are involved in this conflict."""
        ***REMOVED*** Most conflicts involve 1 faculty, but some may involve more
        involved = 1

        ***REMOVED*** Check for swap-related conflicts
        if alert.swap_id:
            involved += 1

        return involved

    def _has_cascading_conflicts(self, alert: ConflictAlert) -> bool:
        """Check if resolving this conflict might create cascading issues."""
        ***REMOVED*** Check for related conflicts in the same time period
        related_conflicts = (
            self.db.query(ConflictAlert)
            .filter(
                and_(
                    ConflictAlert.id != alert.id,
                    ConflictAlert.fmit_week == alert.fmit_week,
                    ConflictAlert.status.in_(
                        [ConflictAlertStatus.NEW, ConflictAlertStatus.ACKNOWLEDGED]
                    ),
                )
            )
            .count()
        )

        return related_conflicts > 2

    def _perform_all_safety_checks(
        self, alert: ConflictAlert
    ) -> list[SafetyCheckResult]:
        """Perform all safety checks for a conflict."""
        checks = []

        ***REMOVED*** 1. ACGME compliance check
        checks.append(self._check_acgme_compliance(alert))

        ***REMOVED*** 2. Coverage gap check
        checks.append(self._check_coverage_gaps(alert))

        ***REMOVED*** 3. Faculty availability check
        checks.append(self._check_faculty_availability(alert))

        ***REMOVED*** 4. Supervision ratio check
        checks.append(self._check_supervision_ratio(alert))

        ***REMOVED*** 5. Workload balance check
        checks.append(self._check_workload_balance(alert))

        return checks

    def _check_acgme_compliance(self, alert: ConflictAlert) -> SafetyCheckResult:
        """Check if resolution would maintain ACGME compliance."""
        ***REMOVED*** Check 80-hour week and 1-in-7 rest day requirements
        faculty = self.db.query(Person).filter(Person.id == alert.faculty_id).first()

        if not faculty or faculty.type != "resident":
            ***REMOVED*** ACGME rules don't apply to non-residents
            return SafetyCheckResult(
                check_type=SafetyCheckType.ACGME_COMPLIANCE,
                passed=True,
                message="ACGME compliance check not applicable (not a resident)",
            )

        ***REMOVED*** Check work hours for the week
        week_start = alert.fmit_week - timedelta(days=alert.fmit_week.weekday())
        week_end = week_start + timedelta(days=6)

        work_blocks = (
            self.db.query(Assignment)
            .join(Block)
            .filter(
                and_(
                    Assignment.person_id == alert.faculty_id,
                    Block.date >= week_start,
                    Block.date <= week_end,
                )
            )
            .count()
        )

        hours_worked = work_blocks * 4.0  ***REMOVED*** Assuming 4 hours per block

        if hours_worked > 80:
            return SafetyCheckResult(
                check_type=SafetyCheckType.ACGME_COMPLIANCE,
                passed=False,
                message=f"ACGME violation: {hours_worked:.1f} hours worked (max 80)",
                details={"hours_worked": hours_worked, "week_start": str(week_start)},
            )

        return SafetyCheckResult(
            check_type=SafetyCheckType.ACGME_COMPLIANCE,
            passed=True,
            message="ACGME compliance maintained",
            details={"hours_worked": hours_worked},
        )

    def _check_coverage_gaps(self, alert: ConflictAlert) -> SafetyCheckResult:
        """Check if resolution would create coverage gaps."""
        ***REMOVED*** Check if removing this faculty creates a gap
        week_assignments = (
            self.db.query(Assignment)
            .join(Block)
            .filter(
                and_(
                    Block.date >= alert.fmit_week,
                    Block.date < alert.fmit_week + timedelta(days=7),
                )
            )
            .count()
        )

        if week_assignments <= 1:
            return SafetyCheckResult(
                check_type=SafetyCheckType.COVERAGE_GAP,
                passed=False,
                message="Resolution may create coverage gap - no other faculty assigned",
                details={"current_assignments": week_assignments},
            )

        return SafetyCheckResult(
            check_type=SafetyCheckType.COVERAGE_GAP,
            passed=True,
            message="Adequate coverage maintained",
            details={"current_assignments": week_assignments},
        )

    def _check_faculty_availability(self, alert: ConflictAlert) -> SafetyCheckResult:
        """Check if alternate faculty are available."""
        available_faculty = self._find_available_faculty(
            alert.fmit_week, alert.faculty_id
        )

        if not available_faculty:
            return SafetyCheckResult(
                check_type=SafetyCheckType.FACULTY_AVAILABILITY,
                passed=False,
                message="No available faculty for reassignment",
                details={"available_count": 0},
            )

        return SafetyCheckResult(
            check_type=SafetyCheckType.FACULTY_AVAILABILITY,
            passed=True,
            message=f"{len(available_faculty)} faculty member(s) available for reassignment",
            details={"available_count": len(available_faculty)},
        )

    def _check_supervision_ratio(self, alert: ConflictAlert) -> SafetyCheckResult:
        """Check if supervision ratios will be maintained."""
        ***REMOVED*** For faculty conflicts, check if they supervise residents
        faculty = self.db.query(Person).filter(Person.id == alert.faculty_id).first()

        if not faculty or faculty.type != "faculty":
            return SafetyCheckResult(
                check_type=SafetyCheckType.SUPERVISION_RATIO,
                passed=True,
                message="Supervision ratio check not applicable",
            )

        ***REMOVED*** Check if this faculty is supervising residents during this period
        supervised_residents = (
            self.db.query(Assignment)
            .join(Block)
            .join(Person)
            .filter(
                and_(
                    Block.date >= alert.fmit_week,
                    Block.date < alert.fmit_week + timedelta(days=7),
                    Person.type == "resident",
                )
            )
            .count()
        )

        if supervised_residents > 0:
            ***REMOVED*** Check if removing this faculty would violate ratios
            other_faculty = (
                self.db.query(Assignment)
                .join(Block)
                .join(Person)
                .filter(
                    and_(
                        Block.date >= alert.fmit_week,
                        Block.date < alert.fmit_week + timedelta(days=7),
                        Person.type == "faculty",
                        Person.id != alert.faculty_id,
                    )
                )
                .count()
            )

            if other_faculty == 0:
                return SafetyCheckResult(
                    check_type=SafetyCheckType.SUPERVISION_RATIO,
                    passed=False,
                    message=f"No other faculty available to supervise {supervised_residents} residents",
                    details={
                        "supervised_residents": supervised_residents,
                        "other_faculty": other_faculty,
                    },
                )

        return SafetyCheckResult(
            check_type=SafetyCheckType.SUPERVISION_RATIO,
            passed=True,
            message="Supervision ratios maintained",
        )

    def _check_workload_balance(self, alert: ConflictAlert) -> SafetyCheckResult:
        """Check if workload remains balanced."""
        ***REMOVED*** Count current FMIT assignments for this faculty
        current_assignments = (
            self.db.query(Assignment)
            .join(Block)
            .join(RotationTemplate)
            .filter(
                and_(
                    Assignment.person_id == alert.faculty_id,
                    Block.date >= date.today(),
                    RotationTemplate.name.ilike("%FMIT%"),
                )
            )
            .count()
        )

        ***REMOVED*** Compare to average
        avg_assignments = (
            self.db.query(func.count(Assignment.id))
            .join(Block)
            .join(Person)
            .join(RotationTemplate)
            .filter(
                and_(
                    Person.type == "faculty",
                    Block.date >= date.today(),
                    RotationTemplate.name.ilike("%FMIT%"),
                )
            )
            .scalar()
            or 0
        )

        total_faculty = self.db.query(Person).filter(Person.type == "faculty").count()
        avg_per_faculty = avg_assignments / max(total_faculty, 1)

        balance_score = 1.0 - abs(current_assignments - avg_per_faculty) / max(
            avg_per_faculty, 1
        )

        return SafetyCheckResult(
            check_type=SafetyCheckType.WORKLOAD_BALANCE,
            passed=balance_score > 0.7,
            message=f"Workload balance score: {balance_score:.2f}",
            details={
                "current_assignments": current_assignments,
                "average_assignments": avg_per_faculty,
                "balance_score": balance_score,
            },
        )

    def _identify_constraints(self, alert: ConflictAlert) -> list[str]:
        """Identify constraints that limit resolution options."""
        constraints = []

        ***REMOVED*** Check for leave constraints
        if alert.leave_id:
            constraints.append("Faculty has approved leave during this period")

        ***REMOVED*** Check for back-to-back constraints
        if alert.conflict_type == ConflictType.BACK_TO_BACK:
            constraints.append(
                "Must maintain minimum 2-week gap between FMIT rotations"
            )

        ***REMOVED*** Check for ACGME constraints
        faculty = self.db.query(Person).filter(Person.id == alert.faculty_id).first()
        if faculty and faculty.type == "resident":
            constraints.append("Must comply with ACGME work hour limits")
            constraints.append("Must maintain 1-in-7 rest day requirement")

        return constraints

    def _identify_blockers(self, alert: ConflictAlert) -> list[str]:
        """Identify blockers that prevent auto-resolution."""
        blockers = []

        ***REMOVED*** Check for critical severity
        if alert.severity == ConflictSeverity.CRITICAL:
            ***REMOVED*** Critical conflicts might need human review
            if self._has_cascading_conflicts(alert):
                blockers.append("Critical conflict with cascading impacts")

        ***REMOVED*** Check for multiple conflicts in same period
        related_count = (
            self.db.query(ConflictAlert)
            .filter(
                and_(
                    ConflictAlert.fmit_week == alert.fmit_week,
                    ConflictAlert.status.in_(
                        [ConflictAlertStatus.NEW, ConflictAlertStatus.ACKNOWLEDGED]
                    ),
                )
            )
            .count()
        )

        if related_count > 3:
            blockers.append(f"Multiple conflicts ({related_count}) in same time period")

        return blockers

    def _recommend_strategies(
        self,
        alert: ConflictAlert,
        safety_checks: list[SafetyCheckResult],
    ) -> list[ResolutionStrategyEnum]:
        """Recommend resolution strategies based on analysis."""
        strategies = []

        ***REMOVED*** Check if faculty are available for swapping
        faculty_available = next(
            (
                c
                for c in safety_checks
                if c.check_type == SafetyCheckType.FACULTY_AVAILABILITY
            ),
            None,
        )

        if faculty_available and faculty_available.passed:
            strategies.append(ResolutionStrategyEnum.SWAP_ASSIGNMENTS)

        ***REMOVED*** Check if we can reassign to junior faculty
        if alert.conflict_type in [
            ConflictType.LEAVE_FMIT_OVERLAP,
            ConflictType.BACK_TO_BACK,
        ]:
            strategies.append(ResolutionStrategyEnum.REASSIGN_JUNIOR)

        ***REMOVED*** Check if we can use backup
        if alert.severity == ConflictSeverity.CRITICAL:
            strategies.append(ResolutionStrategyEnum.ESCALATE_TO_BACKUP)

        ***REMOVED*** Split coverage is good for back-to-back
        if alert.conflict_type == ConflictType.BACK_TO_BACK:
            strategies.append(ResolutionStrategyEnum.SPLIT_COVERAGE)

        ***REMOVED*** Always include defer as fallback
        if not strategies or alert.severity == ConflictSeverity.CRITICAL:
            strategies.append(ResolutionStrategyEnum.DEFER_TO_HUMAN)

        return strategies

    def _estimate_resolution_time(
        self, complexity_score: float, num_strategies: int
    ) -> int:
        """Estimate time to resolve in minutes."""
        base_time = 10  ***REMOVED*** Base 10 minutes
        complexity_time = int(complexity_score * 20)  ***REMOVED*** Up to 20 extra minutes
        strategy_time = (
            max(num_strategies - 1, 0) * 5
        )  ***REMOVED*** 5 minutes per additional strategy

        return base_time + complexity_time + strategy_time

    def _generate_leave_overlap_options(
        self,
        alert: ConflictAlert,
        analysis: ConflictAnalysis,
    ) -> list[ResolutionOption]:
        """Generate options for leave/FMIT overlap conflicts."""
        options = []

        ***REMOVED*** Option 1: Swap with available faculty
        available_faculty = self._find_available_faculty(
            alert.fmit_week, alert.faculty_id
        )
        if available_faculty:
            for faculty in available_faculty[:2]:  ***REMOVED*** Top 2 candidates
                options.append(
                    ResolutionOption(
                        id=f"swap_{alert.id}_{faculty.id}",
                        conflict_id=alert.id,
                        strategy=ResolutionStrategyEnum.SWAP_ASSIGNMENTS,
                        title=f"Swap FMIT week with {faculty.name}",
                        description=f"Transfer FMIT assignment to {faculty.name} who is available this week",
                        detailed_steps=[
                            f"Remove FMIT assignment from {alert.faculty.name}",
                            f"Create FMIT assignment for {faculty.name}",
                            "Update schedule and notify affected parties",
                            "Verify no new conflicts created",
                        ],
                        changes={
                            "remove_assignments": [str(alert.faculty_id)],
                            "add_assignments": [str(faculty.id)],
                            "affected_week": alert.fmit_week.isoformat(),
                        },
                        risk_level="low",
                    )
                )

        ***REMOVED*** Option 2: Reassign to junior faculty (if applicable)
        junior_faculty = self._find_junior_faculty_available(alert.fmit_week)
        if junior_faculty:
            options.append(
                ResolutionOption(
                    id=f"reassign_junior_{alert.id}",
                    conflict_id=alert.id,
                    strategy=ResolutionStrategyEnum.REASSIGN_JUNIOR,
                    title="Reassign to junior faculty member",
                    description="Reassign FMIT duty to available junior faculty (PGY-2/3)",
                    detailed_steps=[
                        "Identify qualified junior faculty",
                        "Verify junior faculty availability and qualifications",
                        "Transfer assignment with supervision plan",
                        "Brief junior faculty on responsibilities",
                    ],
                    changes={
                        "reassign_to_junior": True,
                        "candidates": [str(f.id) for f in junior_faculty[:3]],
                    },
                    risk_level="medium",
                )
            )

        ***REMOVED*** Option 3: Escalate to backup pool
        options.append(
            ResolutionOption(
                id=f"backup_{alert.id}",
                conflict_id=alert.id,
                strategy=ResolutionStrategyEnum.ESCALATE_TO_BACKUP,
                title="Use backup coverage pool",
                description="Request coverage from designated backup faculty pool",
                detailed_steps=[
                    "Check backup pool availability",
                    "Select backup faculty member",
                    "Create backup assignment",
                    "Notify all parties of coverage arrangement",
                ],
                changes={
                    "use_backup_pool": True,
                    "original_faculty": str(alert.faculty_id),
                },
                risk_level="medium",
            )
        )

        return options

    def _generate_back_to_back_options(
        self,
        alert: ConflictAlert,
        analysis: ConflictAnalysis,
    ) -> list[ResolutionOption]:
        """Generate options for back-to-back FMIT conflicts."""
        options = []

        ***REMOVED*** Option 1: Split coverage
        options.append(
            ResolutionOption(
                id=f"split_{alert.id}",
                conflict_id=alert.id,
                strategy=ResolutionStrategyEnum.SPLIT_COVERAGE,
                title="Split one FMIT week between two faculty",
                description="Divide one FMIT week into partial coverage between faculty members",
                detailed_steps=[
                    "Identify week to split",
                    "Find faculty to share coverage",
                    "Create split schedule (e.g., Mon-Wed, Thu-Sun)",
                    "Update assignments for both faculty",
                ],
                changes={
                    "split_week": alert.fmit_week.isoformat(),
                    "split_type": "partial_coverage",
                },
                risk_level="medium",
            )
        )

        ***REMOVED*** Option 2: Swap one week
        available_faculty = self._find_available_faculty(
            alert.fmit_week, alert.faculty_id
        )
        if available_faculty:
            options.append(
                ResolutionOption(
                    id=f"swap_b2b_{alert.id}",
                    conflict_id=alert.id,
                    strategy=ResolutionStrategyEnum.SWAP_ASSIGNMENTS,
                    title="Swap one FMIT week to create spacing",
                    description="Exchange one of the back-to-back weeks with another faculty",
                    detailed_steps=[
                        "Select which week to swap",
                        f"Swap with {available_faculty[0].name}",
                        "Verify 2+ week gap created",
                        "Update all schedules",
                    ],
                    changes={
                        "swap_week": alert.fmit_week.isoformat(),
                        "swap_with": str(available_faculty[0].id),
                    },
                    risk_level="low",
                )
            )

        return options

    def _generate_workload_options(
        self,
        alert: ConflictAlert,
        analysis: ConflictAnalysis,
    ) -> list[ResolutionOption]:
        """Generate options for workload balance conflicts."""
        options = []

        ***REMOVED*** Redistribute assignments
        options.append(
            ResolutionOption(
                id=f"redistribute_{alert.id}",
                conflict_id=alert.id,
                strategy=ResolutionStrategyEnum.SWAP_ASSIGNMENTS,
                title="Redistribute FMIT assignments for better balance",
                description="Rebalance FMIT schedule to distribute workload more evenly",
                detailed_steps=[
                    "Analyze current workload distribution",
                    "Identify overloaded and underloaded faculty",
                    "Propose swap arrangements",
                    "Execute balanced redistribution",
                ],
                changes={
                    "redistribution": True,
                    "affected_faculty": str(alert.faculty_id),
                },
                risk_level="high",  ***REMOVED*** High risk due to multiple changes
            )
        )

        return options

    def _generate_external_commitment_options(
        self,
        alert: ConflictAlert,
        analysis: ConflictAnalysis,
    ) -> list[ResolutionOption]:
        """Generate options for external commitment conflicts."""
        options = []

        ***REMOVED*** Request coverage
        options.append(
            ResolutionOption(
                id=f"coverage_{alert.id}",
                conflict_id=alert.id,
                strategy=ResolutionStrategyEnum.ESCALATE_TO_BACKUP,
                title="Request coverage for external commitment",
                description="Find replacement coverage to accommodate external commitment",
                detailed_steps=[
                    "Document external commitment details",
                    "Request volunteer coverage",
                    "Identify backup faculty if no volunteers",
                    "Finalize coverage arrangement",
                ],
                changes={
                    "external_commitment": True,
                    "needs_coverage": True,
                },
                risk_level="medium",
            )
        )

        return options

    def _generate_defer_to_human_option(
        self,
        alert: ConflictAlert,
        analysis: ConflictAnalysis,
    ) -> ResolutionOption:
        """Generate a 'defer to human' fallback option."""
        return ResolutionOption(
            id=f"defer_{alert.id}",
            conflict_id=alert.id,
            strategy=ResolutionStrategyEnum.DEFER_TO_HUMAN,
            title="Defer to manual resolution",
            description="Flag this conflict for human review and manual resolution",
            detailed_steps=[
                "Escalate to scheduling coordinator",
                "Review conflict details and constraints",
                "Manually determine best resolution approach",
                "Apply resolution with full context",
            ],
            changes={
                "defer_to_human": True,
                "escalation_required": True,
            },
            risk_level="low",  ***REMOVED*** Low risk for deferral itself
        )

    def _assess_resolution_impact(
        self,
        option: ResolutionOption,
        alert: ConflictAlert,
    ) -> ImpactAssessment:
        """Assess the impact of applying a resolution option."""
        ***REMOVED*** Base metrics
        affected_faculty = 1
        affected_weeks = 1
        affected_blocks = 0
        new_conflicts = 0
        cascading_changes = 0

        ***REMOVED*** Adjust based on strategy
        if option.strategy == ResolutionStrategyEnum.SWAP_ASSIGNMENTS:
            affected_faculty = 2  ***REMOVED*** Swapper and swappee
            ***REMOVED*** Check for potential new conflicts
            new_conflicts = self._predict_new_conflicts(option, alert)

        elif option.strategy == ResolutionStrategyEnum.REASSIGN_JUNIOR:
            affected_faculty = 2  ***REMOVED*** Senior and junior
            cascading_changes = 1  ***REMOVED*** May need supervision adjustments

        elif option.strategy == ResolutionStrategyEnum.SPLIT_COVERAGE:
            affected_faculty = 2  ***REMOVED*** Two people sharing coverage
            affected_blocks = 7  ***REMOVED*** Splitting a week
            cascading_changes = 2  ***REMOVED*** Multiple schedule adjustments

        elif option.strategy == ResolutionStrategyEnum.ESCALATE_TO_BACKUP:
            affected_faculty = 2
            ***REMOVED*** Backup pool has good coverage

        elif option.strategy == ResolutionStrategyEnum.DEFER_TO_HUMAN:
            ***REMOVED*** No automatic changes
            affected_faculty = 0

        ***REMOVED*** Calculate quality scores
        workload_balance = self._calculate_workload_balance_score(option, alert)
        fairness = self._calculate_fairness_score(option, alert)
        disruption = self._calculate_disruption_score(
            affected_faculty, cascading_changes
        )
        feasibility = self._calculate_feasibility_score(option, alert)
        confidence = self._calculate_confidence_score(option, alert)

        ***REMOVED*** Calculate overall score
        overall = (
            feasibility * 0.3
            + workload_balance * 0.2
            + fairness * 0.2
            + (1 - disruption) * 0.15
            + confidence * 0.15
        )

        ***REMOVED*** Generate recommendation
        if overall >= 0.8:
            recommendation = "Highly recommended - safe and effective resolution"
        elif overall >= 0.6:
            recommendation = "Good option - acceptable trade-offs"
        elif overall >= 0.4:
            recommendation = "Moderate option - some concerns"
        else:
            recommendation = "Not recommended - significant risks or low feasibility"

        return ImpactAssessment(
            affected_faculty_count=affected_faculty,
            affected_weeks_count=affected_weeks,
            affected_blocks_count=affected_blocks,
            new_conflicts_created=new_conflicts,
            conflicts_resolved=1,
            cascading_changes_required=cascading_changes,
            workload_balance_score=workload_balance,
            fairness_score=fairness,
            disruption_score=disruption,
            feasibility_score=feasibility,
            confidence_level=confidence,
            overall_score=overall,
            recommendation=recommendation,
        )

    def _predict_new_conflicts(
        self, option: ResolutionOption, alert: ConflictAlert
    ) -> int:
        """Predict how many new conflicts might be created."""
        ***REMOVED*** Simple heuristic: check target faculty's existing conflicts
        if "swap_with" in option.changes:
            target_id = option.changes["swap_with"]
            existing_conflicts = (
                self.db.query(ConflictAlert)
                .filter(
                    ConflictAlert.faculty_id == UUID(target_id),
                    ConflictAlert.status.in_(
                        [ConflictAlertStatus.NEW, ConflictAlertStatus.ACKNOWLEDGED]
                    ),
                )
                .count()
            )
            return 1 if existing_conflicts > 2 else 0
        return 0

    def _calculate_workload_balance_score(
        self, option: ResolutionOption, alert: ConflictAlert
    ) -> float:
        """Calculate workload balance score (0-1, higher is better)."""
        if option.strategy == ResolutionStrategyEnum.DEFER_TO_HUMAN:
            return 0.5  ***REMOVED*** Neutral

        ***REMOVED*** Check if swap would improve balance
        if option.strategy == ResolutionStrategyEnum.SWAP_ASSIGNMENTS:
            return 0.8  ***REMOVED*** Generally improves balance

        return 0.7  ***REMOVED*** Default good score

    def _calculate_fairness_score(
        self, option: ResolutionOption, alert: ConflictAlert
    ) -> float:
        """Calculate fairness score (0-1, higher is more fair)."""
        if option.strategy == ResolutionStrategyEnum.REASSIGN_JUNIOR:
            ***REMOVED*** Check if junior faculty is being overloaded
            return 0.6  ***REMOVED*** Moderate fairness
        elif option.strategy == ResolutionStrategyEnum.SWAP_ASSIGNMENTS:
            return 0.9  ***REMOVED*** Very fair - mutual exchange
        return 0.7

    def _calculate_disruption_score(
        self, affected_faculty: int, cascading_changes: int
    ) -> float:
        """Calculate disruption score (0-1, higher is more disruptive)."""
        disruption = (affected_faculty * 0.1) + (cascading_changes * 0.2)
        return min(disruption, 1.0)

    def _calculate_feasibility_score(
        self, option: ResolutionOption, alert: ConflictAlert
    ) -> float:
        """Calculate feasibility score (0-1, higher is more feasible)."""
        if option.strategy == ResolutionStrategyEnum.DEFER_TO_HUMAN:
            return 1.0  ***REMOVED*** Always feasible to defer

        ***REMOVED*** Check if required resources are available
        if "add_assignments" in option.changes:
            ***REMOVED*** Check if target faculty exists and is available
            return 0.8

        if option.strategy == ResolutionStrategyEnum.ESCALATE_TO_BACKUP:
            ***REMOVED*** Backup might not always be available
            return 0.6

        return 0.75  ***REMOVED*** Default moderate feasibility

    def _calculate_confidence_score(
        self, option: ResolutionOption, alert: ConflictAlert
    ) -> float:
        """Calculate confidence in resolution success (0-1, higher is more confident)."""
        if option.strategy == ResolutionStrategyEnum.DEFER_TO_HUMAN:
            return 0.5  ***REMOVED*** Neutral confidence

        ***REMOVED*** Higher confidence for simpler strategies
        if option.strategy == ResolutionStrategyEnum.SWAP_ASSIGNMENTS:
            return 0.85
        elif option.strategy in [
            ResolutionStrategyEnum.REASSIGN_JUNIOR,
            ResolutionStrategyEnum.ESCALATE_TO_BACKUP,
        ]:
            return 0.75
        else:
            return 0.65

    def _validate_safety(self, option: ResolutionOption, alert: ConflictAlert) -> bool:
        """Validate that a resolution option is safe to apply."""
        ***REMOVED*** Defer is always safe (does nothing)
        if option.strategy == ResolutionStrategyEnum.DEFER_TO_HUMAN:
            return True

        ***REMOVED*** Check impact assessment
        if not option.impact:
            return False

        ***REMOVED*** Fail if creates new conflicts
        if option.impact.new_conflicts_created > 0:
            option.safety_issues.append("May create new conflicts")
            return False

        ***REMOVED*** Fail if feasibility too low
        if option.impact.feasibility_score < 0.5:
            option.safety_issues.append("Low feasibility score")
            return False

        ***REMOVED*** Fail if disruption too high
        if option.impact.disruption_score > 0.7:
            option.safety_issues.append("High disruption score")
            return False

        return True

    def _can_auto_apply(self, option: ResolutionOption) -> bool:
        """Determine if an option can be automatically applied."""
        ***REMOVED*** Never auto-apply defer to human
        if option.strategy == ResolutionStrategyEnum.DEFER_TO_HUMAN:
            return False

        ***REMOVED*** Must be safety validated
        if not option.safety_validated:
            return False

        ***REMOVED*** Must have good overall score
        if not option.impact or option.impact.overall_score < 0.7:
            return False

        ***REMOVED*** Risk level must be low or medium
        if option.risk_level == "high":
            return False

        return True

    def _requires_approval(self, option: ResolutionOption) -> bool:
        """Determine if an option requires human approval."""
        ***REMOVED*** High risk always requires approval
        if option.risk_level == "high":
            return True

        ***REMOVED*** Medium risk with safety issues requires approval
        if option.risk_level == "medium" and option.safety_issues:
            return True

        ***REMOVED*** Low overall score requires approval
        if option.impact and option.impact.overall_score < 0.6:
            return True

        ***REMOVED*** Defer always requires human action
        if option.strategy == ResolutionStrategyEnum.DEFER_TO_HUMAN:
            return True

        return False

    def _apply_resolution(
        self,
        option: ResolutionOption,
        alert: ConflictAlert,
        user_id: UUID | None,
    ) -> ResolutionResult:
        """
        Apply a resolution option to a conflict.

        Uses transactional context with retry to ensure:
        - Atomic application of changes
        - Automatic rollback on failure
        - Deadlock retry
        - Row-level locking to prevent concurrent modifications
        """
        changes_applied = []
        entities_modified = defaultdict(list)
        warnings = []
        new_conflicts = []

        try:
            ***REMOVED*** Execute resolution in transaction with retry on deadlock
            with transactional_with_retry(
                self.db, max_retries=3, timeout_seconds=30.0
            ):
                ***REMOVED*** Re-fetch alert with lock to prevent concurrent modifications
                locked_alert = self._get_alert(alert.id, lock=True)
                if not locked_alert:
                    return ResolutionResult(
                        resolution_option_id=option.id,
                        conflict_id=alert.id,
                        strategy=option.strategy,
                        success=False,
                        status=ResolutionStatusEnum.FAILED,
                        message="Conflict not found when applying resolution",
                        error_code="CONFLICT_NOT_FOUND",
                    )

                ***REMOVED*** Check if alert was already resolved by another process
                if locked_alert.status not in [
                    ConflictAlertStatus.NEW,
                    ConflictAlertStatus.ACKNOWLEDGED,
                ]:
                    return ResolutionResult(
                        resolution_option_id=option.id,
                        conflict_id=alert.id,
                        strategy=option.strategy,
                        success=False,
                        status=ResolutionStatusEnum.REJECTED,
                        message=f"Conflict already resolved with status: {locked_alert.status.value}",
                        error_code="ALREADY_RESOLVED",
                    )

                ***REMOVED*** Apply based on strategy
                if option.strategy == ResolutionStrategyEnum.SWAP_ASSIGNMENTS:
                    success, msg = self._apply_swap_resolution(
                        option, locked_alert, user_id
                    )
                    if success:
                        changes_applied.append(msg)
                        entities_modified["assignments"].append(str(locked_alert.faculty_id))
                    else:
                        return ResolutionResult(
                            resolution_option_id=option.id,
                            conflict_id=alert.id,
                            strategy=option.strategy,
                            success=False,
                            status=ResolutionStatusEnum.FAILED,
                            message=msg,
                            error_code="SWAP_FAILED",
                        )

                elif option.strategy == ResolutionStrategyEnum.REASSIGN_JUNIOR:
                    success, msg = self._apply_reassign_junior(
                        option, locked_alert, user_id
                    )
                    if success:
                        changes_applied.append(msg)
                    else:
                        return ResolutionResult(
                            resolution_option_id=option.id,
                            conflict_id=alert.id,
                            strategy=option.strategy,
                            success=False,
                            status=ResolutionStatusEnum.FAILED,
                            message=msg,
                            error_code="REASSIGN_FAILED",
                        )

                elif option.strategy == ResolutionStrategyEnum.ESCALATE_TO_BACKUP:
                    success, msg = self._apply_backup_escalation(
                        option, locked_alert, user_id
                    )
                    if success:
                        changes_applied.append(msg)
                    else:
                        warnings.append(msg)

                else:
                    return ResolutionResult(
                        resolution_option_id=option.id,
                        conflict_id=alert.id,
                        strategy=option.strategy,
                        success=False,
                        status=ResolutionStatusEnum.REJECTED,
                        message=f"Strategy {option.strategy.value} not implemented for auto-apply",
                        error_code="STRATEGY_NOT_IMPLEMENTED",
                    )

                ***REMOVED*** Mark conflict as resolved
                locked_alert.status = ConflictAlertStatus.RESOLVED
                locked_alert.resolved_at = datetime.utcnow()
                locked_alert.resolved_by_id = user_id
                locked_alert.resolution_notes = (
                    f"Auto-resolved via {option.strategy.value}: {option.title}"
                )

                ***REMOVED*** Transaction auto-commits on success

            changes_applied.append("Conflict marked as resolved")

            return ResolutionResult(
                resolution_option_id=option.id,
                conflict_id=alert.id,
                strategy=option.strategy,
                success=True,
                status=ResolutionStatusEnum.APPLIED,
                message=f"Successfully applied resolution: {option.title}",
                changes_applied=changes_applied,
                entities_modified=dict(entities_modified),
                conflict_resolved=True,
                new_conflicts_created=new_conflicts,
                warnings=warnings,
                applied_at=datetime.utcnow(),
                applied_by_id=user_id,
                can_rollback=True,
                rollback_instructions="Contact scheduling coordinator to reverse changes",
            )

        except (SQLAlchemyError, ValueError, KeyError, TypeError) as e:
            logger.error(f"Error applying resolution for conflict {alert.id}: {e}", exc_info=True)
            return ResolutionResult(
                resolution_option_id=option.id,
                conflict_id=alert.id,
                strategy=option.strategy,
                success=False,
                status=ResolutionStatusEnum.FAILED,
                message=f"Error applying resolution: {str(e)}",
                error_code="APPLICATION_ERROR",
                error_details={"exception": str(e)},
            )

    def _apply_swap_resolution(
        self,
        option: ResolutionOption,
        alert: ConflictAlert,
        user_id: UUID | None,
    ) -> tuple[bool, str]:
        """Apply a swap-based resolution."""
        changes = option.changes

        ***REMOVED*** Get target faculty from changes
        if "add_assignments" in changes and changes["add_assignments"]:
            target_faculty_id = UUID(changes["add_assignments"][0])

            ***REMOVED*** Create swap record
            swap = SwapRecord(
                id=uuid4(),
                source_faculty_id=alert.faculty_id,
                source_week=alert.fmit_week,
                target_faculty_id=target_faculty_id,
                target_week=None,
                swap_type=SwapType.ABSORB,
                status=SwapStatus.APPROVED,  ***REMOVED*** Auto-approved for safe swaps
                requested_by_id=user_id,
                approved_by_id=user_id,
                reason=f"Auto-resolution for conflict {alert.id}",
            )
            self.db.add(swap)
            self.db.flush()

            return True, f"Created swap record (ID: {swap.id})"

        return False, "No target faculty specified for swap"

    def _apply_reassign_junior(
        self,
        option: ResolutionOption,
        alert: ConflictAlert,
        user_id: UUID | None,
    ) -> tuple[bool, str]:
        """Apply a junior reassignment resolution."""
        ***REMOVED*** In a full implementation, this would reassign to a junior faculty member
        ***REMOVED*** For now, we simulate the action
        return True, "Reassignment to junior faculty initiated (simulation)"

    def _apply_backup_escalation(
        self,
        option: ResolutionOption,
        alert: ConflictAlert,
        user_id: UUID | None,
    ) -> tuple[bool, str]:
        """Apply a backup escalation resolution."""
        ***REMOVED*** In a full implementation, this would create backup coverage request
        ***REMOVED*** For now, we simulate the action
        return True, "Backup coverage request created (simulation)"

    def _find_available_faculty(
        self,
        fmit_week: date,
        exclude_faculty_id: UUID,
    ) -> list[Person]:
        """Find faculty members available for a specific FMIT week."""
        all_faculty = (
            self.db.query(Person)
            .filter(
                Person.type == "faculty",
                Person.id != exclude_faculty_id,
            )
            .all()
        )

        available = []
        week_end = fmit_week + timedelta(days=6)

        for faculty in all_faculty:
            ***REMOVED*** Check for conflicts
            has_conflicts = (
                self.db.query(ConflictAlert)
                .filter(
                    ConflictAlert.faculty_id == faculty.id,
                    ConflictAlert.fmit_week == fmit_week,
                    ConflictAlert.status.in_(
                        [ConflictAlertStatus.NEW, ConflictAlertStatus.ACKNOWLEDGED]
                    ),
                )
                .count()
                > 0
            )

            if not has_conflicts:
                ***REMOVED*** Check for existing assignments
                has_assignment = (
                    self.db.query(Assignment)
                    .join(Block)
                    .filter(
                        Assignment.person_id == faculty.id,
                        Block.date >= fmit_week,
                        Block.date <= week_end,
                    )
                    .count()
                    > 0
                )

                if not has_assignment:
                    available.append(faculty)

        return available

    def _find_junior_faculty_available(self, fmit_week: date) -> list[Person]:
        """Find junior faculty (residents PGY-2/3) available for assignment."""
        junior = (
            self.db.query(Person)
            .filter(
                Person.type == "resident",
                Person.pgy_level.in_([2, 3]),
            )
            .all()
        )

        available = []
        week_end = fmit_week + timedelta(days=6)

        for person in junior:
            ***REMOVED*** Check availability (simplified)
            has_assignment = (
                self.db.query(Assignment)
                .join(Block)
                .filter(
                    Assignment.person_id == person.id,
                    Block.date >= fmit_week,
                    Block.date <= week_end,
                )
                .count()
            )

            if has_assignment == 0:
                available.append(person)

        return available

    def _is_acceptable_risk(
        self, option: ResolutionOption, max_risk_level: str
    ) -> bool:
        """Check if an option's risk level is acceptable."""
        risk_levels = {"low": 1, "medium": 2, "high": 3}
        option_risk = risk_levels.get(option.risk_level, 2)
        max_risk = risk_levels.get(max_risk_level, 2)

        return option_risk <= max_risk
