"""Tests for scheduler operations schemas (Pydantic validation and Field coverage)."""

from datetime import datetime

import pytest
from pydantic import ValidationError

from app.schemas.scheduler_ops import (
    FixItMode,
    ApprovalAction,
    TaskStatus,
    TaskMetrics,
    RecentTaskInfo,
    CoverageMetrics,
    SitrepResponse,
    FixItRequest,
    AffectedTask,
    FixItResponse,
    ApprovalRequest,
    ApprovedTaskInfo,
    ApprovalResponse,
    SolverAbortRequest,
    SolverAbortResponse,
    SolverProgressResponse,
    ActiveSolversResponse,
    SchedulerOpsError,
)


# ===========================================================================
# Enum Tests
# ===========================================================================


class TestFixItMode:
    def test_values(self):
        assert FixItMode.GREEDY.value == "greedy"
        assert FixItMode.CONSERVATIVE.value == "conservative"
        assert FixItMode.BALANCED.value == "balanced"

    def test_count(self):
        assert len(FixItMode) == 3

    def test_is_str(self):
        assert isinstance(FixItMode.GREEDY, str)


class TestApprovalAction:
    def test_values(self):
        assert ApprovalAction.APPROVE.value == "approve"
        assert ApprovalAction.DENY.value == "deny"

    def test_count(self):
        assert len(ApprovalAction) == 2


class TestTaskStatus:
    def test_values(self):
        assert TaskStatus.PENDING.value == "pending"
        assert TaskStatus.IN_PROGRESS.value == "in_progress"
        assert TaskStatus.COMPLETED.value == "completed"
        assert TaskStatus.FAILED.value == "failed"
        assert TaskStatus.CANCELLED.value == "cancelled"

    def test_count(self):
        assert len(TaskStatus) == 5


# ===========================================================================
# TaskMetrics Tests
# ===========================================================================


class TestTaskMetrics:
    def _valid_kwargs(self):
        return {
            "total_tasks": 100,
            "active_tasks": 5,
            "completed_tasks": 90,
            "failed_tasks": 3,
            "pending_tasks": 2,
            "success_rate": 0.9,
        }

    def test_valid(self):
        r = TaskMetrics(**self._valid_kwargs())
        assert r.success_rate == 0.9

    # --- ge=0 on count fields ---

    def test_count_fields_zero(self):
        kw = dict.fromkeys(self._valid_kwargs(), 0)
        kw["success_rate"] = 0.0
        r = TaskMetrics(**kw)
        assert r.total_tasks == 0

    def test_count_fields_negative(self):
        for field in [
            "total_tasks",
            "active_tasks",
            "completed_tasks",
            "failed_tasks",
            "pending_tasks",
        ]:
            kw = self._valid_kwargs()
            kw[field] = -1
            with pytest.raises(ValidationError):
                TaskMetrics(**kw)

    # --- success_rate ge=0.0, le=1.0 ---

    def test_success_rate_boundaries(self):
        kw = self._valid_kwargs()
        kw["success_rate"] = 0.0
        r = TaskMetrics(**kw)
        assert r.success_rate == 0.0

        kw["success_rate"] = 1.0
        r = TaskMetrics(**kw)
        assert r.success_rate == 1.0

    def test_success_rate_negative(self):
        kw = self._valid_kwargs()
        kw["success_rate"] = -0.1
        with pytest.raises(ValidationError):
            TaskMetrics(**kw)

    def test_success_rate_above_one(self):
        kw = self._valid_kwargs()
        kw["success_rate"] = 1.1
        with pytest.raises(ValidationError):
            TaskMetrics(**kw)


# ===========================================================================
# RecentTaskInfo Tests
# ===========================================================================


class TestRecentTaskInfo:
    def test_valid_minimal(self):
        r = RecentTaskInfo(
            task_id="task-1",
            name="generate_schedule",
            status=TaskStatus.COMPLETED,
        )
        assert r.description is None
        assert r.started_at is None
        assert r.completed_at is None
        assert r.duration_seconds is None
        assert r.error_message is None

    def test_full(self):
        r = RecentTaskInfo(
            task_id="task-1",
            name="generate_schedule",
            status=TaskStatus.FAILED,
            description="Schedule generation for Block 10",
            started_at=datetime.now(),
            completed_at=datetime.now(),
            duration_seconds=120.5,
            error_message="Timeout exceeded",
        )
        assert r.duration_seconds == 120.5


# ===========================================================================
# CoverageMetrics Tests
# ===========================================================================


class TestCoverageMetrics:
    def _valid_kwargs(self):
        return {
            "coverage_rate": 0.95,
            "blocks_covered": 48,
            "blocks_total": 50,
            "faculty_utilization": 0.85,
        }

    def test_valid(self):
        r = CoverageMetrics(**self._valid_kwargs())
        assert r.critical_gaps == 0

    # --- coverage_rate ge=0.0, le=1.0 ---

    def test_coverage_rate_boundaries(self):
        kw = self._valid_kwargs()
        kw["coverage_rate"] = 0.0
        r = CoverageMetrics(**kw)
        assert r.coverage_rate == 0.0

        kw["coverage_rate"] = 1.0
        r = CoverageMetrics(**kw)
        assert r.coverage_rate == 1.0

    def test_coverage_rate_negative(self):
        kw = self._valid_kwargs()
        kw["coverage_rate"] = -0.1
        with pytest.raises(ValidationError):
            CoverageMetrics(**kw)

    def test_coverage_rate_above_one(self):
        kw = self._valid_kwargs()
        kw["coverage_rate"] = 1.1
        with pytest.raises(ValidationError):
            CoverageMetrics(**kw)

    # --- blocks ge=0 ---

    def test_blocks_zero(self):
        kw = self._valid_kwargs()
        kw["blocks_covered"] = 0
        kw["blocks_total"] = 0
        r = CoverageMetrics(**kw)
        assert r.blocks_total == 0

    def test_blocks_negative(self):
        kw = self._valid_kwargs()
        kw["blocks_covered"] = -1
        with pytest.raises(ValidationError):
            CoverageMetrics(**kw)

    # --- critical_gaps ge=0 ---

    def test_critical_gaps_negative(self):
        kw = self._valid_kwargs()
        kw["critical_gaps"] = -1
        with pytest.raises(ValidationError):
            CoverageMetrics(**kw)

    # --- faculty_utilization ge=0.0, le=1.0 ---

    def test_faculty_utilization_above_one(self):
        kw = self._valid_kwargs()
        kw["faculty_utilization"] = 1.1
        with pytest.raises(ValidationError):
            CoverageMetrics(**kw)


# ===========================================================================
# SitrepResponse Tests
# ===========================================================================


class TestSitrepResponse:
    def _make_metrics(self):
        return TaskMetrics(
            total_tasks=10,
            active_tasks=1,
            completed_tasks=8,
            failed_tasks=1,
            pending_tasks=0,
            success_rate=0.8,
        )

    def test_valid(self):
        r = SitrepResponse(
            task_metrics=self._make_metrics(),
            health_status="healthy",
        )
        assert r.defense_level is None
        assert r.recent_tasks == []
        assert r.coverage_metrics is None
        assert r.immediate_actions == []
        assert r.watch_items == []
        assert r.crisis_mode is False


# ===========================================================================
# FixItRequest Tests
# ===========================================================================


class TestFixItRequest:
    def test_defaults(self):
        r = FixItRequest(initiated_by="admin")
        assert r.mode == FixItMode.BALANCED
        assert r.max_retries == 3
        assert r.auto_approve is False
        assert r.target_task_ids is None
        assert r.dry_run is False

    # --- max_retries ge=1, le=10 ---

    def test_max_retries_boundaries(self):
        r = FixItRequest(initiated_by="admin", max_retries=1)
        assert r.max_retries == 1
        r = FixItRequest(initiated_by="admin", max_retries=10)
        assert r.max_retries == 10

    def test_max_retries_zero(self):
        with pytest.raises(ValidationError):
            FixItRequest(initiated_by="admin", max_retries=0)

    def test_max_retries_above_max(self):
        with pytest.raises(ValidationError):
            FixItRequest(initiated_by="admin", max_retries=11)

    # --- initiated_by min_length=1, max_length=100 ---

    def test_initiated_by_empty(self):
        with pytest.raises(ValidationError):
            FixItRequest(initiated_by="")

    def test_initiated_by_too_long(self):
        with pytest.raises(ValidationError):
            FixItRequest(initiated_by="x" * 101)


# ===========================================================================
# AffectedTask Tests
# ===========================================================================


class TestAffectedTask:
    def test_valid(self):
        r = AffectedTask(
            task_id="task-1",
            task_name="generate_schedule",
            previous_status=TaskStatus.FAILED,
            new_status=TaskStatus.COMPLETED,
            action_taken="retried",
        )
        assert r.retry_count == 0


# ===========================================================================
# FixItResponse Tests
# ===========================================================================


class TestFixItResponse:
    def test_valid_minimal(self):
        r = FixItResponse(
            status="completed",
            execution_id="exec-1",
            mode=FixItMode.BALANCED,
            initiated_by="admin",
            message="Fix-it completed successfully",
        )
        assert r.tasks_fixed == 0
        assert r.tasks_retried == 0
        assert r.tasks_skipped == 0
        assert r.tasks_failed == 0
        assert r.affected_tasks == []
        assert r.estimated_completion is None
        assert r.completed_at is None
        assert r.warnings == []

    # --- ge=0 on count fields ---

    def test_tasks_fixed_negative(self):
        with pytest.raises(ValidationError):
            FixItResponse(
                status="completed",
                execution_id="exec-1",
                mode=FixItMode.BALANCED,
                initiated_by="admin",
                message="Test",
                tasks_fixed=-1,
            )

    def test_tasks_retried_negative(self):
        with pytest.raises(ValidationError):
            FixItResponse(
                status="completed",
                execution_id="exec-1",
                mode=FixItMode.BALANCED,
                initiated_by="admin",
                message="Test",
                tasks_retried=-1,
            )


# ===========================================================================
# ApprovalRequest Tests
# ===========================================================================


class TestApprovalRequest:
    def test_defaults(self):
        r = ApprovalRequest(token="abcd1234", approved_by="admin")
        assert r.action == ApprovalAction.APPROVE
        assert r.task_id is None
        assert r.approved_by_id is None
        assert r.notes is None

    # --- token min_length=8, max_length=200 ---

    def test_token_too_short(self):
        with pytest.raises(ValidationError):
            ApprovalRequest(token="short", approved_by="admin")

    def test_token_too_long(self):
        with pytest.raises(ValidationError):
            ApprovalRequest(token="x" * 201, approved_by="admin")

    def test_token_min_length(self):
        r = ApprovalRequest(token="x" * 8, approved_by="admin")
        assert len(r.token) == 8

    # --- approved_by min_length=1, max_length=100 ---

    def test_approved_by_empty(self):
        with pytest.raises(ValidationError):
            ApprovalRequest(token="abcd1234", approved_by="")

    def test_approved_by_too_long(self):
        with pytest.raises(ValidationError):
            ApprovalRequest(token="abcd1234", approved_by="x" * 101)

    # --- notes max_length=500 ---

    def test_notes_too_long(self):
        with pytest.raises(ValidationError):
            ApprovalRequest(token="abcd1234", approved_by="admin", notes="x" * 501)

    def test_notes_max_length(self):
        r = ApprovalRequest(token="abcd1234", approved_by="admin", notes="x" * 500)
        assert len(r.notes) == 500


# ===========================================================================
# ApprovedTaskInfo Tests
# ===========================================================================


class TestApprovedTaskInfo:
    def test_valid(self):
        r = ApprovedTaskInfo(
            task_id="task-1",
            task_name="generate_schedule",
            task_type="schedule_generation",
            previous_status=TaskStatus.PENDING,
            new_status=TaskStatus.IN_PROGRESS,
            approved_at=datetime.now(),
        )
        assert r.task_type == "schedule_generation"


# ===========================================================================
# ApprovalResponse Tests
# ===========================================================================


class TestApprovalResponse:
    def test_valid(self):
        r = ApprovalResponse(
            status="approved",
            action=ApprovalAction.APPROVE,
            approved_by="admin",
            message="Task approved",
        )
        assert r.task_id is None
        assert r.approved_tasks == 0
        assert r.denied_tasks == 0
        assert r.task_details == []
        assert r.warnings == []

    # --- approved_tasks ge=0, denied_tasks ge=0 ---

    def test_approved_tasks_negative(self):
        with pytest.raises(ValidationError):
            ApprovalResponse(
                status="approved",
                action=ApprovalAction.APPROVE,
                approved_by="admin",
                message="Test",
                approved_tasks=-1,
            )


# ===========================================================================
# SolverAbortRequest Tests
# ===========================================================================


class TestSolverAbortRequest:
    def test_defaults(self):
        r = SolverAbortRequest(requested_by="admin")
        assert r.reason == "operator request"

    # --- reason min_length=1, max_length=500 ---

    def test_reason_empty(self):
        with pytest.raises(ValidationError):
            SolverAbortRequest(reason="", requested_by="admin")

    def test_reason_too_long(self):
        with pytest.raises(ValidationError):
            SolverAbortRequest(reason="x" * 501, requested_by="admin")

    # --- requested_by min_length=1, max_length=100 ---

    def test_requested_by_empty(self):
        with pytest.raises(ValidationError):
            SolverAbortRequest(requested_by="")

    def test_requested_by_too_long(self):
        with pytest.raises(ValidationError):
            SolverAbortRequest(requested_by="x" * 101)


# ===========================================================================
# SolverAbortResponse Tests
# ===========================================================================


class TestSolverAbortResponse:
    def test_valid(self):
        r = SolverAbortResponse(
            status="abort_requested",
            run_id="run-1",
            reason="Taking too long",
            requested_by="admin",
            message="Abort signal sent",
        )
        assert r.status == "abort_requested"


# ===========================================================================
# SolverProgressResponse Tests
# ===========================================================================


class TestSolverProgressResponse:
    def test_valid(self):
        r = SolverProgressResponse(
            run_id="run-1",
            iteration=500,
            best_score=-8.5,
            assignments_count=50,
            violations_count=0,
            status="running",
        )
        assert r.updated_at is None

    # --- iteration ge=0 ---

    def test_iteration_negative(self):
        with pytest.raises(ValidationError):
            SolverProgressResponse(
                run_id="run-1",
                iteration=-1,
                best_score=0.0,
                assignments_count=0,
                violations_count=0,
                status="running",
            )

    # --- assignments_count ge=0 ---

    def test_assignments_count_negative(self):
        with pytest.raises(ValidationError):
            SolverProgressResponse(
                run_id="run-1",
                iteration=0,
                best_score=0.0,
                assignments_count=-1,
                violations_count=0,
                status="running",
            )

    # --- violations_count ge=0 ---

    def test_violations_count_negative(self):
        with pytest.raises(ValidationError):
            SolverProgressResponse(
                run_id="run-1",
                iteration=0,
                best_score=0.0,
                assignments_count=0,
                violations_count=-1,
                status="running",
            )


# ===========================================================================
# ActiveSolversResponse Tests
# ===========================================================================


class TestActiveSolversResponse:
    def test_valid(self):
        r = ActiveSolversResponse(count=0)
        assert r.active_runs == []

    def test_count_negative(self):
        with pytest.raises(ValidationError):
            ActiveSolversResponse(count=-1)


# ===========================================================================
# SchedulerOpsError Tests
# ===========================================================================


class TestSchedulerOpsError:
    def test_valid(self):
        r = SchedulerOpsError(
            error="not_found",
            message="Solver run not found",
        )
        assert r.details is None
