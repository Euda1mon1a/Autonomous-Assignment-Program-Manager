"""Tests for schedule schemas (Field bounds, field_validators, model_validators, enums, aliases, defaults)."""

from datetime import date, datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas.schedule import (
    SchedulingAlgorithm,
    ScheduleRequest,
    Violation,
    NFPCAuditViolation,
    NFPCAudit,
    ValidationResult,
    SolverStatistics,
    ScheduleResponse,
    EmergencyRequest,
    EmergencyResponse,
    ConflictItem,
    ScheduleSummary,
    Recommendation,
    ConflictSummary,
    ImportAnalysisResponse,
    FacultyTargetInput,
    ExternalConflictInput,
    SwapFinderRequest,
    SwapCandidateResponse,
    AlternatingPatternInfo,
    SwapFinderResponse,
    SwapCandidateJsonRequest,
    SwapCandidateJsonItem,
    SwapCandidateJsonResponse,
    ScheduleMetrics,
    ScheduleRunRead,
    ScheduleRunsResponse,
    RollbackPoint,
    SyncMetadata,
    ExperimentRunStatus,
    ExperimentRunResult,
    ExperimentRunConfiguration,
    ExperimentRunResponse,
    RunQueueResponse,
    QueueBatchRequest,
    AdjunctFacultyGapResponse,
    AdjunctGapsResponse,
    ClinicLimitViolationResponse,
    FacultyCoverageResponse,
)


# ── SchedulingAlgorithm enum ─────────────────────────────────────────


class TestSchedulingAlgorithm:
    def test_values(self):
        assert SchedulingAlgorithm.GREEDY == "greedy"
        assert SchedulingAlgorithm.CP_SAT == "cp_sat"
        assert SchedulingAlgorithm.PULP == "pulp"
        assert SchedulingAlgorithm.HYBRID == "hybrid"

    def test_count(self):
        assert len(SchedulingAlgorithm) == 4


# ── ExperimentRunStatus enum ─────────────────────────────────────────


class TestExperimentRunStatus:
    def test_values(self):
        assert ExperimentRunStatus.QUEUED == "queued"
        assert ExperimentRunStatus.RUNNING == "running"
        assert ExperimentRunStatus.COMPLETED == "completed"
        assert ExperimentRunStatus.FAILED == "failed"
        assert ExperimentRunStatus.CANCELLED == "cancelled"

    def test_count(self):
        assert len(ExperimentRunStatus) == 5


# ── ScheduleRequest ──────────────────────────────────────────────────


class TestScheduleRequest:
    def test_defaults(self):
        r = ScheduleRequest(
            start_date=date(2026, 1, 1),
            end_date=date(2026, 1, 31),
        )
        assert r.algorithm == SchedulingAlgorithm.CP_SAT
        assert r.timeout_seconds == 60.0
        assert r.pgy_levels is None
        assert r.rotation_template_ids is None
        assert r.expand_block_assignments is False
        assert r.block_number is None
        assert r.academic_year is None

    # --- timeout_seconds (ge=5.0, le=300.0) ---

    def test_timeout_below_min(self):
        with pytest.raises(ValidationError):
            ScheduleRequest(
                start_date=date(2026, 1, 1),
                end_date=date(2026, 1, 31),
                timeout_seconds=4.9,
            )

    def test_timeout_above_max(self):
        with pytest.raises(ValidationError):
            ScheduleRequest(
                start_date=date(2026, 1, 1),
                end_date=date(2026, 1, 31),
                timeout_seconds=301.0,
            )

    def test_timeout_valid_boundary(self):
        r = ScheduleRequest(
            start_date=date(2026, 1, 1),
            end_date=date(2026, 1, 31),
            timeout_seconds=5.0,
        )
        assert r.timeout_seconds == 5.0

    # --- block_number (ge=0, le=13) ---

    def test_block_number_below_min(self):
        with pytest.raises(ValidationError):
            ScheduleRequest(
                start_date=date(2026, 1, 1),
                end_date=date(2026, 1, 31),
                block_number=-1,
            )

    def test_block_number_above_max(self):
        with pytest.raises(ValidationError):
            ScheduleRequest(
                start_date=date(2026, 1, 1),
                end_date=date(2026, 1, 31),
                block_number=14,
            )

    # --- academic_year (ge=2020, le=2100) ---

    def test_academic_year_below_min(self):
        with pytest.raises(ValidationError):
            ScheduleRequest(
                start_date=date(2026, 1, 1),
                end_date=date(2026, 1, 31),
                academic_year=2019,
            )

    def test_academic_year_above_max(self):
        with pytest.raises(ValidationError):
            ScheduleRequest(
                start_date=date(2026, 1, 1),
                end_date=date(2026, 1, 31),
                academic_year=2101,
            )

    # --- model_validator: start_date <= end_date ---

    def test_start_after_end(self):
        with pytest.raises(ValidationError, match="start_date.*must be before"):
            ScheduleRequest(
                start_date=date(2026, 6, 1),
                end_date=date(2026, 1, 1),
            )

    def test_same_dates_ok(self):
        r = ScheduleRequest(
            start_date=date(2026, 3, 1),
            end_date=date(2026, 3, 1),
        )
        assert r.start_date == r.end_date


# ── Violation ────────────────────────────────────────────────────────


class TestViolation:
    def test_defaults(self):
        r = Violation(type="80_HOUR", severity="HIGH", message="Exceeded")
        assert r.person_id is None
        assert r.person_name is None
        assert r.block_id is None
        assert r.details is None


# ── NFPCAuditViolation ───────────────────────────────────────────────


class TestNFPCAuditViolation:
    def test_defaults(self):
        r = NFPCAuditViolation()
        assert r.person_id is None
        assert r.person_name is None
        assert r.nf_date is None
        assert r.pc_required_date is None
        assert r.missing_am_pc is False
        assert r.missing_pm_pc is False


# ── NFPCAudit ────────────────────────────────────────────────────────


class TestNFPCAudit:
    def test_defaults(self):
        r = NFPCAudit(compliant=True, total_nf_transitions=5, violations=[])
        assert r.message is None


# ── ValidationResult ─────────────────────────────────────────────────


class TestValidationResult:
    def test_defaults(self):
        r = ValidationResult(
            valid=True, total_violations=0, violations=[], coverage_rate=95.0
        )
        assert r.statistics is None


# ── SolverStatistics ─────────────────────────────────────────────────


class TestSolverStatistics:
    def test_all_none(self):
        r = SolverStatistics()
        assert r.total_blocks is None
        assert r.total_residents is None
        assert r.coverage_rate is None
        assert r.branches is None
        assert r.conflicts is None


# ── ScheduleResponse ─────────────────────────────────────────────────


class TestScheduleResponse:
    def test_defaults(self):
        validation = ValidationResult(
            valid=True, total_violations=0, violations=[], coverage_rate=100.0
        )
        r = ScheduleResponse(
            status="success",
            message="Done",
            total_assignments=50,
            total_blocks=10,
            validation=validation,
        )
        assert r.run_id is None
        assert r.solver_stats is None
        assert r.nf_pc_audit is None
        assert r.acgme_override_count == 0


# ── EmergencyRequest ─────────────────────────────────────────────────


class TestEmergencyRequest:
    def test_defaults(self):
        r = EmergencyRequest(
            person_id=uuid4(),
            start_date=date(2026, 1, 1),
            end_date=date(2026, 1, 7),
            reason="TDY",
        )
        assert r.is_deployment is False

    def test_start_after_end(self):
        with pytest.raises(ValidationError, match="start_date.*must be before"):
            EmergencyRequest(
                person_id=uuid4(),
                start_date=date(2026, 6, 1),
                end_date=date(2026, 1, 1),
                reason="TDY",
            )


# ── EmergencyResponse ────────────────────────────────────────────────


class TestEmergencyResponse:
    def test_valid(self):
        r = EmergencyResponse(
            status="success",
            replacements_found=3,
            coverage_gaps=0,
            requires_manual_review=False,
            details=[],
        )
        assert r.replacements_found == 3


# ── ConflictItem ─────────────────────────────────────────────────────


class TestConflictItem:
    def test_defaults(self):
        r = ConflictItem(
            provider="Dr. A",
            date="2026-01-15",
            time="AM",
            type="double_book",
            severity="error",
            message="Double booked",
        )
        assert r.fmit_assignment is None
        assert r.clinic_assignment is None


# ── ScheduleSummary ──────────────────────────────────────────────────


class TestScheduleSummary:
    def test_defaults(self):
        r = ScheduleSummary(
            providers=["Dr. A"],
            date_range=["2026-01-01", "2026-01-31"],
            total_slots=20,
        )
        assert r.fmit_slots == 0
        assert r.clinic_slots == 0


# ── Recommendation ───────────────────────────────────────────────────


class TestRecommendation:
    def test_defaults(self):
        r = Recommendation(type="consolidate_fmit", message="Consolidate weeks")
        assert r.providers is None
        assert r.count is None


# ── ImportAnalysisResponse ───────────────────────────────────────────


class TestImportAnalysisResponse:
    def test_defaults(self):
        r = ImportAnalysisResponse(success=True)
        assert r.error is None
        assert r.fmit_schedule is None
        assert r.clinic_schedule is None
        assert r.conflicts == []
        assert r.recommendations == []
        assert r.summary is None


# ── FacultyTargetInput ───────────────────────────────────────────────


class TestFacultyTargetInput:
    def test_defaults(self):
        r = FacultyTargetInput(name="Dr. Smith")
        assert r.target_weeks == 6
        assert r.role == "faculty"
        assert r.current_weeks == 0

    def test_target_weeks_below_min(self):
        with pytest.raises(ValidationError):
            FacultyTargetInput(name="Dr. Smith", target_weeks=-1)

    def test_target_weeks_above_max(self):
        with pytest.raises(ValidationError):
            FacultyTargetInput(name="Dr. Smith", target_weeks=53)

    def test_role_literal(self):
        for role in ("faculty", "chief", "pd", "adjunct"):
            r = FacultyTargetInput(name="X", role=role)
            assert r.role == role

    def test_role_invalid(self):
        with pytest.raises(ValidationError):
            FacultyTargetInput(name="X", role="intern")


# ── ExternalConflictInput ────────────────────────────────────────────


class TestExternalConflictInput:
    def test_defaults(self):
        r = ExternalConflictInput(
            faculty="Dr. A",
            start_date=date(2026, 1, 1),
            end_date=date(2026, 1, 7),
            conflict_type="leave",
        )
        assert r.description == ""

    def test_start_after_end(self):
        with pytest.raises(ValidationError, match="start_date must be before"):
            ExternalConflictInput(
                faculty="Dr. A",
                start_date=date(2026, 6, 1),
                end_date=date(2026, 1, 1),
                conflict_type="leave",
            )

    def test_conflict_type_literal(self):
        for ct in ("leave", "conference", "tdy", "training", "deployment", "medical"):
            r = ExternalConflictInput(
                faculty="X",
                start_date=date(2026, 1, 1),
                end_date=date(2026, 1, 7),
                conflict_type=ct,
            )
            assert r.conflict_type == ct

    def test_conflict_type_invalid(self):
        with pytest.raises(ValidationError):
            ExternalConflictInput(
                faculty="X",
                start_date=date(2026, 1, 1),
                end_date=date(2026, 1, 7),
                conflict_type="vacation",
            )


# ── SwapFinderRequest ────────────────────────────────────────────────


class TestSwapFinderRequest:
    def test_defaults(self):
        r = SwapFinderRequest(
            target_faculty="Dr. A",
            target_week=date(2026, 1, 6),
        )
        assert r.faculty_targets == []
        assert r.external_conflicts == []
        assert r.include_absence_conflicts is True
        assert r.schedule_release_days == 90

    def test_schedule_release_days_below_min(self):
        with pytest.raises(ValidationError):
            SwapFinderRequest(
                target_faculty="Dr. A",
                target_week=date(2026, 1, 6),
                schedule_release_days=-1,
            )

    def test_schedule_release_days_above_max(self):
        with pytest.raises(ValidationError):
            SwapFinderRequest(
                target_faculty="Dr. A",
                target_week=date(2026, 1, 6),
                schedule_release_days=366,
            )


# ── SwapCandidateResponse ────────────────────────────────────────────


class TestSwapCandidateResponse:
    def test_defaults(self):
        r = SwapCandidateResponse(
            faculty="Dr. B",
            can_take_week="2026-01-06",
            back_to_back_ok=True,
            flexibility="easy",
        )
        assert r.gives_week is None
        assert r.external_conflict is None
        assert r.reason == ""
        assert r.rank == 0


# ── SwapFinderResponse ───────────────────────────────────────────────


class TestSwapFinderResponse:
    def test_defaults(self):
        r = SwapFinderResponse(
            success=True,
            target_faculty="Dr. A",
            target_week="2026-01-06",
            candidates=[],
            total_candidates=0,
            viable_candidates=0,
        )
        assert r.alternating_patterns == []
        assert r.message == ""


# ── SwapCandidateJsonRequest ─────────────────────────────────────────


class TestSwapCandidateJsonRequest:
    def test_defaults(self):
        r = SwapCandidateJsonRequest(person_id="abc")
        assert r.assignment_id is None
        assert r.block_id is None
        assert r.max_candidates == 10

    def test_max_candidates_below_min(self):
        with pytest.raises(ValidationError):
            SwapCandidateJsonRequest(person_id="abc", max_candidates=0)

    def test_max_candidates_above_max(self):
        with pytest.raises(ValidationError):
            SwapCandidateJsonRequest(person_id="abc", max_candidates=51)


# ── SwapCandidateJsonItem ────────────────────────────────────────────


class TestSwapCandidateJsonItem:
    def test_defaults(self):
        r = SwapCandidateJsonItem(
            candidate_person_id="p1",
            candidate_name="Dr. B",
            candidate_role="Faculty",
            block_date="2026-01-06",
            block_session="AM",
            match_score=0.85,
        )
        assert r.assignment_id is None
        assert r.rotation_name is None
        assert r.compatibility_factors == {}
        assert r.mutual_benefit is False
        assert r.approval_likelihood == "medium"

    def test_match_score_below_min(self):
        with pytest.raises(ValidationError):
            SwapCandidateJsonItem(
                candidate_person_id="p1",
                candidate_name="Dr. B",
                candidate_role="Faculty",
                block_date="2026-01-06",
                block_session="AM",
                match_score=-0.1,
            )

    def test_match_score_above_max(self):
        with pytest.raises(ValidationError):
            SwapCandidateJsonItem(
                candidate_person_id="p1",
                candidate_name="Dr. B",
                candidate_role="Faculty",
                block_date="2026-01-06",
                block_session="AM",
                match_score=1.1,
            )


# ── SwapCandidateJsonResponse ────────────────────────────────────────


class TestSwapCandidateJsonResponse:
    def test_defaults(self):
        r = SwapCandidateJsonResponse(
            success=True,
            requester_person_id="p1",
            candidates=[],
            total_candidates=0,
        )
        assert r.requester_name is None
        assert r.original_assignment_id is None
        assert r.top_candidate_id is None
        assert r.message == ""


# ── ScheduleMetrics (aliases + populate_by_name) ─────────────────────


class TestScheduleMetrics:
    def test_alias_access(self):
        r = ScheduleMetrics(
            run_id="run-1",
            status="success",
            timestamp=datetime(2026, 1, 15),
        )
        assert r.run_id == "run-1"
        assert r.coverage_percent == 0.0
        assert r.acgme_violations == 0
        assert r.fairness_score == 0.0
        assert r.swap_churn == 0.0
        assert r.runtime_seconds == 0.0
        assert r.stability == 0.0
        assert r.blocks_assigned == 0
        assert r.total_blocks == 0

    def test_populate_by_name(self):
        """Fields can be set by either alias or field name."""
        r = ScheduleMetrics(
            runId="run-1",
            status="success",
            coveragePercent=99.5,
            acgmeViolations=2,
            timestamp=datetime(2026, 1, 15),
        )
        assert r.coverage_percent == 99.5
        assert r.acgme_violations == 2


# ── ScheduleRunRead ──────────────────────────────────────────────────


class TestScheduleRunRead:
    def test_defaults(self):
        r = ScheduleRunRead(
            id=uuid4(),
            algorithm=SchedulingAlgorithm.HYBRID,
            timestamp=datetime(2026, 1, 15),
            status="success",
        )
        assert r.run_id is None
        assert r.start_date is None
        assert r.end_date is None
        assert r.configuration == {}
        assert r.result is None
        assert r.notes is None
        assert r.tags == []


# ── RunQueueResponse ─────────────────────────────────────────────────


class TestRunQueueResponse:
    def test_defaults(self):
        r = RunQueueResponse(runs=[])
        assert r.max_concurrent == 2
        assert r.currently_running == 0


# ── RollbackPoint ────────────────────────────────────────────────────


class TestRollbackPoint:
    def test_defaults(self):
        r = RollbackPoint(
            id=uuid4(),
            created_at=datetime(2026, 1, 15),
            description="Pre-gen backup",
            assignment_count=100,
        )
        assert r.created_by is None
        assert r.run_id is None
        assert r.can_revert is True


# ── SyncMetadata ─────────────────────────────────────────────────────


class TestSyncMetadata:
    def test_defaults(self):
        r = SyncMetadata(sync_status="synced", source_system="AHLTA")
        assert r.last_sync_time is None
        assert r.records_affected == 0


# ── ExperimentRunResult (aliases) ────────────────────────────────────


class TestExperimentRunResult:
    def test_populate_by_name(self):
        r = ExperimentRunResult(
            run_id="r1",
            status="success",
            coverage_percent=95.0,
            acgme_violations=0,
            runtime_seconds=30.5,
            blocks_assigned=100,
            total_blocks=100,
            timestamp=datetime(2026, 1, 15),
        )
        assert r.fairness_score == 0.0
        assert r.swap_churn == 0.0
        assert r.stability == 1.0


# ── ExperimentRunConfiguration (aliases) ─────────────────────────────


class TestExperimentRunConfiguration:
    def test_defaults(self):
        r = ExperimentRunConfiguration(
            algorithm="hybrid",
            academic_year="2025-2026",
            block_range={"start": 1, "end": 13},
            timeout_seconds=60,
        )
        assert r.constraints == []
        assert r.preserve_fmit is True
        assert r.nf_post_call_enabled is True
        assert r.dry_run is False


# ── AdjunctFacultyGapResponse (aliases) ──────────────────────────────


class TestAdjunctFacultyGapResponse:
    def test_populate_by_name(self):
        r = AdjunctFacultyGapResponse(
            person_id=uuid4(),
            display_name="Dr. A",
            faculty_role="adjunct",
            min_clinic_halfdays=2,
            max_clinic_halfdays=4,
            existing_assignment_count=1,
        )
        assert r.faculty_role == "adjunct"

    def test_alias_access(self):
        uid = uuid4()
        r = AdjunctFacultyGapResponse(
            personId=uid,
            displayName="Dr. A",
            facultyRole="adjunct",
            minClinicHalfdays=2,
            maxClinicHalfdays=4,
            existingAssignmentCount=1,
        )
        assert r.person_id == uid


# ── ClinicLimitViolationResponse (aliases) ───────────────────────────


class TestClinicLimitViolationResponse:
    def test_populate_by_name(self):
        r = ClinicLimitViolationResponse(
            faculty_id=uuid4(),
            faculty_name="Dr. B",
            faculty_role="core",
            week_start=date(2026, 1, 6),
            clinic_count=5,
            min_limit=2,
            max_limit=4,
            violation_type="over_max",
            limit_source="role",
        )
        assert r.violation_type == "over_max"
