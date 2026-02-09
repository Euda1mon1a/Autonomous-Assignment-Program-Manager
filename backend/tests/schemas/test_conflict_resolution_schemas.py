"""Tests for conflict resolution schemas (Field bounds, enums, defaults, default_factory)."""

from datetime import date, datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas.conflict_resolution import (
    ConflictSeverity,
    ConflictType,
    ConflictStatus,
    ConflictResponse,
    ConflictListResponse,
    ResolutionStrategyEnum,
    ResolutionStatusEnum,
    SafetyCheckType,
    SafetyCheckResult,
    ConflictAnalysis,
    ImpactAssessment,
    ResolutionOption,
    ResolutionResult,
    BatchResolutionRequest,
    BatchResolutionReport,
    AutoResolutionConfig,
)


# ── Enums ──────────────────────────────────────────────────────────────


class TestConflictSeverity:
    def test_values(self):
        assert ConflictSeverity.CRITICAL == "critical"
        assert ConflictSeverity.HIGH == "high"
        assert ConflictSeverity.MEDIUM == "medium"
        assert ConflictSeverity.LOW == "low"

    def test_count(self):
        assert len(ConflictSeverity) == 4


class TestConflictType:
    def test_count(self):
        assert len(ConflictType) == 14

    def test_sample_values(self):
        assert ConflictType.SCHEDULING_OVERLAP == "scheduling_overlap"
        assert ConflictType.ACGME_VIOLATION == "acgme_violation"
        assert ConflictType.LEAVE_FMIT_OVERLAP == "leave_fmit_overlap"
        assert ConflictType.EXTERNAL_COMMITMENT == "external_commitment"


class TestConflictStatus:
    def test_values(self):
        assert ConflictStatus.UNRESOLVED == "unresolved"
        assert ConflictStatus.PENDING_REVIEW == "pending_review"
        assert ConflictStatus.RESOLVED == "resolved"
        assert ConflictStatus.IGNORED == "ignored"
        assert ConflictStatus.NEW == "new"
        assert ConflictStatus.ACKNOWLEDGED == "acknowledged"

    def test_count(self):
        assert len(ConflictStatus) == 6


class TestResolutionStrategyEnum:
    def test_count(self):
        assert len(ResolutionStrategyEnum) == 5

    def test_sample(self):
        assert ResolutionStrategyEnum.SWAP_ASSIGNMENTS == "swap_assignments"
        assert ResolutionStrategyEnum.DEFER_TO_HUMAN == "defer_to_human"


class TestResolutionStatusEnum:
    def test_count(self):
        assert len(ResolutionStatusEnum) == 6

    def test_sample(self):
        assert ResolutionStatusEnum.PROPOSED == "proposed"
        assert ResolutionStatusEnum.REJECTED == "rejected"


class TestSafetyCheckType:
    def test_count(self):
        assert len(SafetyCheckType) == 5

    def test_sample(self):
        assert SafetyCheckType.ACGME_COMPLIANCE == "acgme_compliance"
        assert SafetyCheckType.WORKLOAD_BALANCE == "workload_balance"


# ── ConflictResponse ───────────────────────────────────────────────────


class TestConflictResponse:
    def test_defaults(self):
        r = ConflictResponse(
            id=uuid4(),
            type="scheduling_overlap",
            severity="high",
            status="unresolved",
            title="Overlap",
            description="Two assignments on same date",
            conflict_date=date(2026, 1, 15),
            detected_at=datetime(2026, 1, 15),
        )
        assert r.affected_person_ids == []
        assert r.affected_assignment_ids == []
        assert r.affected_block_ids == []
        assert r.detected_by == "system"
        assert r.rule_id is None
        assert r.resolved_at is None
        assert r.resolved_by is None
        assert r.resolution_method is None
        assert r.resolution_notes is None
        assert r.details == {}
        assert r.conflict_session is None


# ── SafetyCheckResult ──────────────────────────────────────────────────


class TestSafetyCheckResult:
    def test_defaults(self):
        r = SafetyCheckResult(
            check_type=SafetyCheckType.ACGME_COMPLIANCE,
            passed=True,
            message="OK",
        )
        assert r.details == {}


# ── ConflictAnalysis ───────────────────────────────────────────────────


class TestConflictAnalysis:
    def test_defaults(self):
        r = ConflictAnalysis(
            conflict_id=uuid4(),
            conflict_type="scheduling_overlap",
            severity="high",
            root_cause="Double booking",
            affected_faculty=[uuid4()],
            affected_dates=["2026-01-15"],
            complexity_score=0.5,
        )
        assert r.safety_checks == []
        assert r.all_checks_passed is True
        assert r.auto_resolution_safe is True
        assert r.constraints == []
        assert r.blockers == []
        assert r.recommended_strategies == []
        assert r.estimated_resolution_time == 0
        assert r.analyzed_at is not None

    # --- complexity_score ge=0.0, le=1.0 ---

    def test_complexity_below_min(self):
        with pytest.raises(ValidationError):
            ConflictAnalysis(
                conflict_id=uuid4(),
                conflict_type="t",
                severity="h",
                root_cause="r",
                affected_faculty=[],
                affected_dates=[],
                complexity_score=-0.1,
            )

    def test_complexity_above_max(self):
        with pytest.raises(ValidationError):
            ConflictAnalysis(
                conflict_id=uuid4(),
                conflict_type="t",
                severity="h",
                root_cause="r",
                affected_faculty=[],
                affected_dates=[],
                complexity_score=1.1,
            )


# ── ImpactAssessment ──────────────────────────────────────────────────


class TestImpactAssessment:
    def test_defaults(self):
        r = ImpactAssessment(
            workload_balance_score=0.8,
            fairness_score=0.7,
            disruption_score=0.2,
            feasibility_score=0.9,
            confidence_level=0.85,
            overall_score=0.75,
            recommendation="Apply swap",
        )
        assert r.affected_faculty_count == 0
        assert r.affected_weeks_count == 0
        assert r.affected_blocks_count == 0
        assert r.new_conflicts_created == 0
        assert r.conflicts_resolved == 1
        assert r.cascading_changes_required == 0

    # --- float bounds ge=0.0, le=1.0 for all 6 float fields ---

    def test_workload_balance_above_max(self):
        with pytest.raises(ValidationError):
            ImpactAssessment(
                workload_balance_score=1.1,
                fairness_score=0.5,
                disruption_score=0.5,
                feasibility_score=0.5,
                confidence_level=0.5,
                overall_score=0.5,
                recommendation="r",
            )

    def test_fairness_below_min(self):
        with pytest.raises(ValidationError):
            ImpactAssessment(
                workload_balance_score=0.5,
                fairness_score=-0.1,
                disruption_score=0.5,
                feasibility_score=0.5,
                confidence_level=0.5,
                overall_score=0.5,
                recommendation="r",
            )

    def test_disruption_above_max(self):
        with pytest.raises(ValidationError):
            ImpactAssessment(
                workload_balance_score=0.5,
                fairness_score=0.5,
                disruption_score=1.1,
                feasibility_score=0.5,
                confidence_level=0.5,
                overall_score=0.5,
                recommendation="r",
            )

    def test_feasibility_below_min(self):
        with pytest.raises(ValidationError):
            ImpactAssessment(
                workload_balance_score=0.5,
                fairness_score=0.5,
                disruption_score=0.5,
                feasibility_score=-0.1,
                confidence_level=0.5,
                overall_score=0.5,
                recommendation="r",
            )

    def test_confidence_above_max(self):
        with pytest.raises(ValidationError):
            ImpactAssessment(
                workload_balance_score=0.5,
                fairness_score=0.5,
                disruption_score=0.5,
                feasibility_score=0.5,
                confidence_level=1.1,
                overall_score=0.5,
                recommendation="r",
            )

    def test_overall_below_min(self):
        with pytest.raises(ValidationError):
            ImpactAssessment(
                workload_balance_score=0.5,
                fairness_score=0.5,
                disruption_score=0.5,
                feasibility_score=0.5,
                confidence_level=0.5,
                overall_score=-0.1,
                recommendation="r",
            )


# ── ResolutionOption ───────────────────────────────────────────────────


class TestResolutionOption:
    def test_defaults(self):
        r = ResolutionOption(
            id="opt-1",
            conflict_id=uuid4(),
            strategy=ResolutionStrategyEnum.SWAP_ASSIGNMENTS,
            title="Swap",
            description="Swap assignments",
        )
        assert r.detailed_steps == []
        assert r.changes == {}
        assert r.prerequisites == []
        assert r.impact is None
        assert r.safety_validated is False
        assert r.safety_issues == []
        assert r.status == ResolutionStatusEnum.PROPOSED
        assert r.can_auto_apply is False
        assert r.requires_approval is True
        assert r.created_at is not None
        assert r.estimated_duration == 0
        assert r.risk_level == "medium"


# ── ResolutionResult ───────────────────────────────────────────────────


class TestResolutionResult:
    def test_defaults(self):
        r = ResolutionResult(
            resolution_option_id="opt-1",
            conflict_id=uuid4(),
            strategy=ResolutionStrategyEnum.SWAP_ASSIGNMENTS,
            success=True,
            status=ResolutionStatusEnum.APPLIED,
            message="Done",
        )
        assert r.changes_applied == []
        assert r.entities_modified == {}
        assert r.conflict_resolved is False
        assert r.new_conflicts_created == []
        assert r.warnings == []
        assert r.applied_at is not None
        assert r.applied_by_id is None
        assert r.duration_seconds is None
        assert r.can_rollback is False
        assert r.rollback_instructions is None
        assert r.error_code is None
        assert r.error_details == {}
        assert r.follow_up_required is False
        assert r.follow_up_actions == []


# ── BatchResolutionRequest ─────────────────────────────────────────────


class TestBatchResolutionRequest:
    def test_defaults(self):
        r = BatchResolutionRequest(conflict_ids=[uuid4()])
        assert r.strategy_preference is None
        assert r.auto_apply_safe is False
        assert r.max_risk_level == "medium"
        assert r.require_approval is True

    # --- conflict_ids min_length=1 ---

    def test_empty_ids(self):
        with pytest.raises(ValidationError):
            BatchResolutionRequest(conflict_ids=[])


# ── BatchResolutionReport ──────────────────────────────────────────────


class TestBatchResolutionReport:
    def test_defaults(self):
        r = BatchResolutionReport(
            total_conflicts=10,
            conflicts_analyzed=8,
            processing_time_seconds=5.5,
            started_at=datetime(2026, 1, 15),
            success_rate=0.8,
            overall_status="completed",
            summary_message="Done",
        )
        assert r.resolutions_proposed == 0
        assert r.resolutions_applied == 0
        assert r.resolutions_failed == 0
        assert r.resolutions_deferred == 0
        assert r.results == []
        assert r.pending_approvals == []
        assert r.failed_conflicts == []
        assert r.total_faculty_affected == 0
        assert r.total_changes_made == 0
        assert r.new_conflicts_created == 0
        assert r.safety_checks_performed == 0
        assert r.safety_checks_passed == 0
        assert r.safety_checks_failed == 0
        assert r.recommendations == []
        assert r.completed_at is not None

    # --- success_rate ge=0.0, le=1.0 ---

    def test_success_rate_below_min(self):
        with pytest.raises(ValidationError):
            BatchResolutionReport(
                total_conflicts=1,
                conflicts_analyzed=1,
                processing_time_seconds=1.0,
                started_at=datetime(2026, 1, 15),
                success_rate=-0.1,
                overall_status="done",
                summary_message="m",
            )

    def test_success_rate_above_max(self):
        with pytest.raises(ValidationError):
            BatchResolutionReport(
                total_conflicts=1,
                conflicts_analyzed=1,
                processing_time_seconds=1.0,
                started_at=datetime(2026, 1, 15),
                success_rate=1.1,
                overall_status="done",
                summary_message="m",
            )


# ── AutoResolutionConfig ──────────────────────────────────────────────


class TestAutoResolutionConfig:
    def test_defaults(self):
        r = AutoResolutionConfig()
        assert r.enabled is True
        assert len(r.preferred_strategies) == 3
        assert r.min_feasibility_score == 0.7
        assert r.max_disruption_score == 0.3
        assert r.min_confidence_level == 0.8
        assert r.max_affected_faculty == 5
        assert r.max_cascading_changes == 3
        assert r.max_batch_size == 20
        assert r.auto_apply_low_risk is True
        assert r.auto_apply_medium_risk is False
        assert r.auto_apply_high_risk is False
        assert r.require_approval_threshold == 0.6

    # --- float thresholds ge=0.0, le=1.0 ---

    def test_min_feasibility_below_min(self):
        with pytest.raises(ValidationError):
            AutoResolutionConfig(min_feasibility_score=-0.1)

    def test_min_feasibility_above_max(self):
        with pytest.raises(ValidationError):
            AutoResolutionConfig(min_feasibility_score=1.1)

    def test_max_disruption_below_min(self):
        with pytest.raises(ValidationError):
            AutoResolutionConfig(max_disruption_score=-0.1)

    def test_min_confidence_above_max(self):
        with pytest.raises(ValidationError):
            AutoResolutionConfig(min_confidence_level=1.1)

    def test_require_approval_threshold_below_min(self):
        with pytest.raises(ValidationError):
            AutoResolutionConfig(require_approval_threshold=-0.1)

    # --- int limits gt=0 ---

    def test_max_affected_faculty_zero(self):
        with pytest.raises(ValidationError):
            AutoResolutionConfig(max_affected_faculty=0)

    def test_max_cascading_changes_zero(self):
        with pytest.raises(ValidationError):
            AutoResolutionConfig(max_cascading_changes=0)

    def test_max_batch_size_zero(self):
        with pytest.raises(ValidationError):
            AutoResolutionConfig(max_batch_size=0)
