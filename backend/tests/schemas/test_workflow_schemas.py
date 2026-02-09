"""Tests for workflow schemas (Field bounds, field_validators, nested models, defaults)."""

from datetime import datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas.workflow import (
    StepRetryPolicy,
    StepDefinition,
    WorkflowTemplateDefinition,
    WorkflowTemplateCreate,
    WorkflowTemplateUpdate,
    WorkflowTemplateResponse,
    WorkflowInstanceCreate,
    WorkflowInstanceUpdate,
    WorkflowInstanceCancel,
    WorkflowInstanceResponse,
    WorkflowInstanceDetailResponse,
    WorkflowStepExecutionResponse,
    WorkflowExecutionStart,
    WorkflowExecutionPause,
    WorkflowExecutionResume,
    WorkflowInstanceFilter,
    WorkflowInstanceList,
    WorkflowTemplateList,
    WorkflowStatistics,
    WorkflowTemplateStatistics,
)


# ── StepRetryPolicy ─────────────────────────────────────────────────────


class TestStepRetryPolicy:
    def test_defaults(self):
        r = StepRetryPolicy()
        assert r.max_attempts == 1
        assert r.backoff_multiplier == 1.0
        assert r.max_backoff_seconds == 300
        assert r.retry_on_timeout is True

    # --- max_attempts ge=1, le=10 ---

    def test_max_attempts_below_min(self):
        with pytest.raises(ValidationError):
            StepRetryPolicy(max_attempts=0)

    def test_max_attempts_above_max(self):
        with pytest.raises(ValidationError):
            StepRetryPolicy(max_attempts=11)

    # --- backoff_multiplier ge=1.0 ---

    def test_backoff_multiplier_below_min(self):
        with pytest.raises(ValidationError):
            StepRetryPolicy(backoff_multiplier=0.5)

    # --- max_backoff_seconds ge=1 ---

    def test_max_backoff_below_min(self):
        with pytest.raises(ValidationError):
            StepRetryPolicy(max_backoff_seconds=0)


# ── StepDefinition ──────────────────────────────────────────────────────


class TestStepDefinition:
    def test_defaults(self):
        r = StepDefinition(id="step1", name="Step 1", handler="app.tasks.run")
        assert r.execution_mode == "sequential"
        assert r.depends_on == []
        assert r.condition is None
        assert r.retry_policy is not None
        assert r.timeout_seconds is None
        assert r.input_mapping == {}

    # --- timeout_seconds ge=1 ---

    def test_timeout_below_min(self):
        with pytest.raises(ValidationError):
            StepDefinition(id="step1", name="Step 1", handler="h", timeout_seconds=0)


# ── WorkflowTemplateDefinition ──────────────────────────────────────────


class TestWorkflowTemplateDefinition:
    def test_valid_single_step(self):
        step = StepDefinition(id="s1", name="Step 1", handler="h")
        r = WorkflowTemplateDefinition(steps=[step])
        assert r.default_timeout_seconds == 3600
        assert r.error_handlers == {}

    # --- steps validator: at least one step ---

    def test_empty_steps(self):
        with pytest.raises(ValidationError, match="at least one step"):
            WorkflowTemplateDefinition(steps=[])

    # --- steps validator: unique IDs ---

    def test_duplicate_step_ids(self):
        s1 = StepDefinition(id="s1", name="A", handler="h")
        s2 = StepDefinition(id="s1", name="B", handler="h")
        with pytest.raises(ValidationError, match="unique"):
            WorkflowTemplateDefinition(steps=[s1, s2])

    # --- steps validator: valid dependencies ---

    def test_invalid_dependency(self):
        s1 = StepDefinition(id="s1", name="A", handler="h", depends_on=["s99"])
        with pytest.raises(ValidationError, match="non-existent"):
            WorkflowTemplateDefinition(steps=[s1])

    # --- steps validator: circular dependencies ---

    def test_circular_dependency(self):
        s1 = StepDefinition(id="s1", name="A", handler="h", depends_on=["s2"])
        s2 = StepDefinition(id="s2", name="B", handler="h", depends_on=["s1"])
        with pytest.raises(ValidationError, match="Circular"):
            WorkflowTemplateDefinition(steps=[s1, s2])

    def test_valid_dependencies(self):
        s1 = StepDefinition(id="s1", name="A", handler="h")
        s2 = StepDefinition(id="s2", name="B", handler="h", depends_on=["s1"])
        r = WorkflowTemplateDefinition(steps=[s1, s2])
        assert len(r.steps) == 2

    # --- default_timeout_seconds ge=1 ---

    def test_timeout_below_min(self):
        step = StepDefinition(id="s1", name="A", handler="h")
        with pytest.raises(ValidationError):
            WorkflowTemplateDefinition(steps=[step], default_timeout_seconds=0)


# ── WorkflowTemplateCreate ──────────────────────────────────────────────


class TestWorkflowTemplateCreate:
    def test_defaults(self):
        step = StepDefinition(id="s1", name="A", handler="h")
        defn = WorkflowTemplateDefinition(steps=[step])
        r = WorkflowTemplateCreate(name="My Workflow", definition=defn)
        assert r.description is None
        assert r.tags == []

    # --- name min_length=1, max_length=255 ---

    def test_name_empty(self):
        step = StepDefinition(id="s1", name="A", handler="h")
        defn = WorkflowTemplateDefinition(steps=[step])
        with pytest.raises(ValidationError):
            WorkflowTemplateCreate(name="", definition=defn)


# ── WorkflowTemplateUpdate ──────────────────────────────────────────────


class TestWorkflowTemplateUpdate:
    def test_all_none(self):
        r = WorkflowTemplateUpdate()
        assert r.description is None
        assert r.definition is None
        assert r.tags is None
        assert r.is_active is None


# ── WorkflowTemplateResponse ────────────────────────────────────────────


class TestWorkflowTemplateResponse:
    def test_valid(self):
        r = WorkflowTemplateResponse(
            id=uuid4(),
            name="Workflow",
            description=None,
            version=1,
            definition={"steps": []},
            is_active=True,
            created_at=datetime(2026, 1, 1),
            updated_at=datetime(2026, 1, 1),
            tags=None,
        )
        assert r.version == 1


# ── WorkflowInstanceCreate ──────────────────────────────────────────────


class TestWorkflowInstanceCreate:
    def test_defaults(self):
        r = WorkflowInstanceCreate(template_id=uuid4())
        assert r.name is None
        assert r.description is None
        assert r.input_data == {}
        assert r.priority == 0
        assert r.timeout_seconds is None

    # --- priority ge=0, le=100 ---

    def test_priority_below_min(self):
        with pytest.raises(ValidationError):
            WorkflowInstanceCreate(template_id=uuid4(), priority=-1)

    def test_priority_above_max(self):
        with pytest.raises(ValidationError):
            WorkflowInstanceCreate(template_id=uuid4(), priority=101)

    # --- timeout_seconds ge=1 ---

    def test_timeout_below_min(self):
        with pytest.raises(ValidationError):
            WorkflowInstanceCreate(template_id=uuid4(), timeout_seconds=0)

    # --- name max_length=255 ---

    def test_name_too_long(self):
        with pytest.raises(ValidationError):
            WorkflowInstanceCreate(template_id=uuid4(), name="x" * 256)


# ── WorkflowInstanceUpdate ──────────────────────────────────────────────


class TestWorkflowInstanceUpdate:
    def test_all_none(self):
        r = WorkflowInstanceUpdate()
        assert r.name is None
        assert r.description is None
        assert r.priority is None

    def test_priority_bounds(self):
        with pytest.raises(ValidationError):
            WorkflowInstanceUpdate(priority=-1)

        with pytest.raises(ValidationError):
            WorkflowInstanceUpdate(priority=101)


# ── WorkflowInstanceCancel ──────────────────────────────────────────────


class TestWorkflowInstanceCancel:
    def test_valid(self):
        r = WorkflowInstanceCancel(reason="No longer needed")
        assert r.reason == "No longer needed"

    def test_reason_empty(self):
        with pytest.raises(ValidationError):
            WorkflowInstanceCancel(reason="")


# ── WorkflowInstanceResponse ────────────────────────────────────────────


class TestWorkflowInstanceResponse:
    def test_valid(self):
        r = WorkflowInstanceResponse(
            id=uuid4(),
            template_id=uuid4(),
            template_version=1,
            name=None,
            description=None,
            status="running",
            input_data=None,
            output_data=None,
            execution_state=None,
            error_message=None,
            started_at=None,
            completed_at=None,
            timeout_at=None,
            created_at=datetime(2026, 1, 1),
            priority=0,
            parent_instance_id=None,
        )
        assert r.status == "running"


# ── WorkflowInstanceDetailResponse ──────────────────────────────────────


class TestWorkflowInstanceDetailResponse:
    def test_valid(self):
        r = WorkflowInstanceDetailResponse(
            id=uuid4(),
            template_id=uuid4(),
            template_version=1,
            name=None,
            description=None,
            status="completed",
            input_data=None,
            output_data=None,
            execution_state=None,
            error_message=None,
            started_at=None,
            completed_at=None,
            timeout_at=None,
            created_at=datetime(2026, 1, 1),
            priority=0,
            parent_instance_id=None,
            step_executions=[],
        )
        assert r.step_executions == []


# ── WorkflowStepExecutionResponse ───────────────────────────────────────


class TestWorkflowStepExecutionResponse:
    def test_valid(self):
        r = WorkflowStepExecutionResponse(
            id=uuid4(),
            workflow_instance_id=uuid4(),
            step_id="s1",
            step_name="Step 1",
            step_handler="app.tasks.run",
            status="completed",
            attempt_number=1,
            max_attempts=3,
            input_data=None,
            output_data=None,
            error_message=None,
            started_at=None,
            completed_at=None,
            duration_seconds=None,
            next_retry_at=None,
            execution_order=None,
            condition_result=None,
        )
        assert r.attempt_number == 1


# ── Execution control schemas ───────────────────────────────────────────


class TestWorkflowExecutionStart:
    def test_defaults(self):
        r = WorkflowExecutionStart()
        assert r.async_execution is True


class TestWorkflowExecutionPause:
    def test_defaults(self):
        r = WorkflowExecutionPause()
        assert r.reason is None


class TestWorkflowExecutionResume:
    def test_defaults(self):
        r = WorkflowExecutionResume()
        assert r.reason is None


# ── Query/List schemas ──────────────────────────────────────────────────


class TestWorkflowInstanceFilter:
    def test_defaults(self):
        r = WorkflowInstanceFilter()
        assert r.template_id is None
        assert r.status is None
        assert r.created_after is None
        assert r.created_before is None
        assert r.priority_min is None
        assert r.priority_max is None


class TestWorkflowInstanceList:
    def test_valid(self):
        r = WorkflowInstanceList(items=[], total=0, page=1, page_size=20, total_pages=0)
        assert r.items == []


class TestWorkflowTemplateList:
    def test_valid(self):
        r = WorkflowTemplateList(items=[], total=0, page=1, page_size=20, total_pages=0)
        assert r.items == []


# ── Statistics schemas ──────────────────────────────────────────────────


class TestWorkflowStatistics:
    def test_valid(self):
        r = WorkflowStatistics(
            total_instances=100,
            running_instances=5,
            completed_instances=90,
            failed_instances=3,
            cancelled_instances=2,
            avg_duration_seconds=120.5,
            success_rate=0.9,
        )
        assert r.success_rate == 0.9


class TestWorkflowTemplateStatistics:
    def test_valid(self):
        r = WorkflowTemplateStatistics(
            template_id=uuid4(),
            template_name="Workflow",
            template_version=1,
            total_executions=50,
            successful_executions=45,
            failed_executions=5,
            avg_duration_seconds=None,
            last_execution_at=None,
        )
        assert r.avg_duration_seconds is None
        assert r.last_execution_at is None
