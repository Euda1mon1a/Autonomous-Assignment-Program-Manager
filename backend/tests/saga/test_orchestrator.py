"""Tests for saga orchestrator types and pure logic (no DB)."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from app.saga.orchestrator import (
    SagaCompensationError,
    SagaOrchestrator,
    SagaTimeoutError,
)
from app.saga.types import (
    SagaContext,
    SagaDefinition,
    SagaExecutionResult,
    SagaStatus,
    SagaStepDefinition,
    SagaStepResult,
    StepStatus,
    StepType,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _dummy_action(data: dict[str, Any]) -> dict[str, Any]:
    """Dummy step action for tests."""
    return {"result": "ok"}


async def _dummy_compensation(data: dict[str, Any]) -> None:
    """Dummy compensation for tests."""
    pass


def _step(name: str = "step1", **kwargs) -> SagaStepDefinition:
    """Create a step definition with defaults."""
    defaults: dict[str, Any] = {"name": name, "action": _dummy_action}
    defaults.update(kwargs)
    return SagaStepDefinition(**defaults)


def _definition(
    name: str = "test_saga", steps: list | None = None, **kwargs
) -> SagaDefinition:
    """Create a saga definition with defaults."""
    if steps is None:
        steps = [_step("step1")]
    defaults: dict[str, Any] = {"name": name, "steps": steps}
    defaults.update(kwargs)
    return SagaDefinition(**defaults)


# ---------------------------------------------------------------------------
# SagaStatus enum
# ---------------------------------------------------------------------------


class TestSagaStatus:
    def test_all_values(self):
        assert SagaStatus.PENDING == "pending"
        assert SagaStatus.RUNNING == "running"
        assert SagaStatus.COMPENSATING == "compensating"
        assert SagaStatus.COMPLETED == "completed"
        assert SagaStatus.FAILED == "failed"
        assert SagaStatus.TIMEOUT == "timeout"
        assert SagaStatus.CANCELLED == "cancelled"

    def test_count(self):
        assert len(SagaStatus) == 7

    def test_is_str_enum(self):
        assert isinstance(SagaStatus.PENDING, str)


# ---------------------------------------------------------------------------
# StepStatus enum
# ---------------------------------------------------------------------------


class TestStepStatus:
    def test_all_values(self):
        assert StepStatus.PENDING == "pending"
        assert StepStatus.RUNNING == "running"
        assert StepStatus.COMPLETED == "completed"
        assert StepStatus.FAILED == "failed"
        assert StepStatus.COMPENSATING == "compensating"
        assert StepStatus.COMPENSATED == "compensated"

    def test_count(self):
        assert len(StepStatus) == 6


# ---------------------------------------------------------------------------
# StepType enum
# ---------------------------------------------------------------------------


class TestStepType:
    def test_all_values(self):
        assert StepType.SEQUENTIAL == "sequential"
        assert StepType.PARALLEL == "parallel"

    def test_count(self):
        assert len(StepType) == 2


# ---------------------------------------------------------------------------
# SagaStepDefinition
# ---------------------------------------------------------------------------


class TestSagaStepDefinition:
    def test_defaults(self):
        s = _step("s1")
        assert s.name == "s1"
        assert s.compensation is None
        assert s.timeout_seconds == 300
        assert s.retry_attempts == 0
        assert s.retry_delay_seconds == 5
        assert s.idempotent is True
        assert s.parallel_group is None

    def test_with_compensation(self):
        s = _step("s1", compensation=_dummy_compensation)
        assert s.compensation is not None

    def test_with_parallel_group(self):
        s = _step("s1", parallel_group="group_a")
        assert s.parallel_group == "group_a"

    def test_custom_timeout(self):
        s = _step("s1", timeout_seconds=60)
        assert s.timeout_seconds == 60

    def test_custom_retry(self):
        s = _step("s1", retry_attempts=3, retry_delay_seconds=10)
        assert s.retry_attempts == 3
        assert s.retry_delay_seconds == 10

    def test_not_idempotent(self):
        s = _step("s1", idempotent=False)
        assert s.idempotent is False

    def test_timeout_zero_raises(self):
        with pytest.raises(ValueError, match="timeout_seconds must be positive"):
            _step("s1", timeout_seconds=0)

    def test_timeout_negative_raises(self):
        with pytest.raises(ValueError, match="timeout_seconds must be positive"):
            _step("s1", timeout_seconds=-1)

    def test_retry_negative_raises(self):
        with pytest.raises(ValueError, match="retry_attempts cannot be negative"):
            _step("s1", retry_attempts=-1)

    def test_retry_delay_negative_raises(self):
        with pytest.raises(ValueError, match="retry_delay_seconds cannot be negative"):
            _step("s1", retry_delay_seconds=-1)


# ---------------------------------------------------------------------------
# SagaDefinition
# ---------------------------------------------------------------------------


class TestSagaDefinition:
    def test_defaults(self):
        d = _definition("test")
        assert d.name == "test"
        assert len(d.steps) == 1
        assert d.timeout_seconds == 3600
        assert d.description == ""
        assert d.version == "1.0"

    def test_custom_timeout(self):
        d = _definition("test", timeout_seconds=600)
        assert d.timeout_seconds == 600

    def test_custom_description(self):
        d = _definition("test", description="A test saga")
        assert d.description == "A test saga"

    def test_custom_version(self):
        d = _definition("test", version="2.0")
        assert d.version == "2.0"

    def test_empty_steps_raises(self):
        with pytest.raises(ValueError, match="at least one step"):
            SagaDefinition(name="empty", steps=[])

    def test_timeout_zero_raises(self):
        with pytest.raises(ValueError, match="timeout_seconds must be positive"):
            _definition("test", timeout_seconds=0)

    def test_timeout_negative_raises(self):
        with pytest.raises(ValueError, match="timeout_seconds must be positive"):
            _definition("test", timeout_seconds=-1)

    def test_duplicate_step_names_raises(self):
        steps = [_step("dup"), _step("dup")]
        with pytest.raises(ValueError, match="Step names must be unique"):
            _definition("test", steps=steps)

    def test_multiple_steps(self):
        steps = [_step("s1"), _step("s2"), _step("s3")]
        d = _definition("test", steps=steps)
        assert len(d.steps) == 3

    def test_parallel_group_consecutive_ok(self):
        steps = [
            _step("s1", parallel_group="group_a"),
            _step("s2", parallel_group="group_a"),
            _step("s3"),
        ]
        d = _definition("test", steps=steps)
        assert len(d.steps) == 3

    def test_parallel_group_non_consecutive_raises(self):
        steps = [
            _step("s1", parallel_group="group_a"),
            _step("s2"),  # Sequential step breaks the group
            _step("s3", parallel_group="group_a"),
        ]
        with pytest.raises(ValueError, match="must be consecutive"):
            _definition("test", steps=steps)

    def test_multiple_parallel_groups(self):
        steps = [
            _step("s1", parallel_group="a"),
            _step("s2", parallel_group="a"),
            _step("s3"),
            _step("s4", parallel_group="b"),
            _step("s5", parallel_group="b"),
        ]
        d = _definition("test", steps=steps)
        assert len(d.steps) == 5


# ---------------------------------------------------------------------------
# SagaStepResult
# ---------------------------------------------------------------------------


class TestSagaStepResult:
    def test_creation(self):
        r = SagaStepResult(step_name="s1", status=StepStatus.COMPLETED)
        assert r.step_name == "s1"
        assert r.status == StepStatus.COMPLETED
        assert r.output_data == {}
        assert r.error_message is None
        assert r.started_at is None
        assert r.completed_at is None
        assert r.retry_count == 0

    def test_with_output(self):
        r = SagaStepResult(
            step_name="s1", status=StepStatus.COMPLETED, output_data={"key": "val"}
        )
        assert r.output_data["key"] == "val"

    def test_failed(self):
        r = SagaStepResult(
            step_name="s1", status=StepStatus.FAILED, error_message="timeout"
        )
        assert r.status == StepStatus.FAILED
        assert r.error_message == "timeout"

    def test_with_retry_count(self):
        r = SagaStepResult(step_name="s1", status=StepStatus.COMPLETED, retry_count=3)
        assert r.retry_count == 3


# ---------------------------------------------------------------------------
# SagaExecutionResult
# ---------------------------------------------------------------------------


class TestSagaExecutionResult:
    def test_creation(self):
        sid = uuid4()
        r = SagaExecutionResult(saga_id=sid, status=SagaStatus.COMPLETED)
        assert r.saga_id == sid
        assert r.status == SagaStatus.COMPLETED
        assert r.step_results == []
        assert r.started_at is None
        assert r.completed_at is None
        assert r.compensated_steps == 0
        assert r.error_message is None

    def test_duration_seconds(self):
        now = datetime(2026, 1, 15, 12, 0)
        r = SagaExecutionResult(
            saga_id=uuid4(),
            status=SagaStatus.COMPLETED,
            started_at=now,
            completed_at=now + timedelta(seconds=42),
        )
        assert r.duration_seconds == 42.0

    def test_duration_seconds_none_when_incomplete(self):
        r = SagaExecutionResult(
            saga_id=uuid4(),
            status=SagaStatus.RUNNING,
            started_at=datetime(2026, 1, 15),
        )
        assert r.duration_seconds is None

    def test_duration_seconds_none_when_not_started(self):
        r = SagaExecutionResult(saga_id=uuid4(), status=SagaStatus.PENDING)
        assert r.duration_seconds is None

    def test_is_successful_completed(self):
        r = SagaExecutionResult(saga_id=uuid4(), status=SagaStatus.COMPLETED)
        assert r.is_successful is True

    def test_is_successful_failed(self):
        r = SagaExecutionResult(saga_id=uuid4(), status=SagaStatus.FAILED)
        assert r.is_successful is False

    def test_is_successful_running(self):
        r = SagaExecutionResult(saga_id=uuid4(), status=SagaStatus.RUNNING)
        assert r.is_successful is False

    def test_is_terminal_completed(self):
        r = SagaExecutionResult(saga_id=uuid4(), status=SagaStatus.COMPLETED)
        assert r.is_terminal is True

    def test_is_terminal_failed(self):
        r = SagaExecutionResult(saga_id=uuid4(), status=SagaStatus.FAILED)
        assert r.is_terminal is True

    def test_is_terminal_timeout(self):
        r = SagaExecutionResult(saga_id=uuid4(), status=SagaStatus.TIMEOUT)
        assert r.is_terminal is True

    def test_is_terminal_cancelled(self):
        r = SagaExecutionResult(saga_id=uuid4(), status=SagaStatus.CANCELLED)
        assert r.is_terminal is True

    def test_is_terminal_running(self):
        r = SagaExecutionResult(saga_id=uuid4(), status=SagaStatus.RUNNING)
        assert r.is_terminal is False

    def test_is_terminal_pending(self):
        r = SagaExecutionResult(saga_id=uuid4(), status=SagaStatus.PENDING)
        assert r.is_terminal is False

    def test_is_terminal_compensating(self):
        r = SagaExecutionResult(saga_id=uuid4(), status=SagaStatus.COMPENSATING)
        assert r.is_terminal is False

    def test_with_step_results(self):
        r = SagaExecutionResult(
            saga_id=uuid4(),
            status=SagaStatus.COMPLETED,
            step_results=[
                SagaStepResult(step_name="s1", status=StepStatus.COMPLETED),
                SagaStepResult(step_name="s2", status=StepStatus.COMPLETED),
            ],
        )
        assert len(r.step_results) == 2

    def test_with_compensation(self):
        r = SagaExecutionResult(
            saga_id=uuid4(),
            status=SagaStatus.FAILED,
            compensated_steps=3,
            error_message="Step s2 failed",
        )
        assert r.compensated_steps == 3
        assert r.error_message == "Step s2 failed"


# ---------------------------------------------------------------------------
# SagaContext
# ---------------------------------------------------------------------------


class TestSagaContext:
    def test_creation(self):
        sid = uuid4()
        ctx = SagaContext(saga_id=sid, input_data={"key": "val"})
        assert ctx.saga_id == sid
        assert ctx.input_data == {"key": "val"}
        assert ctx.accumulated_data == {}
        assert ctx.metadata == {}

    def test_merge_step_output(self):
        ctx = SagaContext(saga_id=uuid4(), input_data={})
        ctx.merge_step_output("s1", {"result": "ok"})
        assert ctx.accumulated_data["s1"] == {"result": "ok"}

    def test_merge_multiple_steps(self):
        ctx = SagaContext(saga_id=uuid4(), input_data={})
        ctx.merge_step_output("s1", {"a": 1})
        ctx.merge_step_output("s2", {"b": 2})
        assert ctx.accumulated_data["s1"] == {"a": 1}
        assert ctx.accumulated_data["s2"] == {"b": 2}

    def test_merge_overwrites_existing(self):
        ctx = SagaContext(saga_id=uuid4(), input_data={})
        ctx.merge_step_output("s1", {"v": 1})
        ctx.merge_step_output("s1", {"v": 2})
        assert ctx.accumulated_data["s1"]["v"] == 2

    def test_get_step_output(self):
        ctx = SagaContext(saga_id=uuid4(), input_data={})
        ctx.merge_step_output("s1", {"result": "ok"})
        assert ctx.get_step_output("s1") == {"result": "ok"}

    def test_get_step_output_missing(self):
        ctx = SagaContext(saga_id=uuid4(), input_data={})
        assert ctx.get_step_output("nonexistent") == {}

    def test_to_dict(self):
        sid = uuid4()
        ctx = SagaContext(
            saga_id=sid,
            input_data={"x": 1},
            accumulated_data={"s1": {"y": 2}},
            metadata={"user": "test"},
        )
        d = ctx.to_dict()
        assert d["saga_id"] == str(sid)
        assert d["input_data"] == {"x": 1}
        assert d["accumulated_data"]["s1"] == {"y": 2}
        assert d["metadata"]["user"] == "test"

    def test_with_metadata(self):
        ctx = SagaContext(
            saga_id=uuid4(),
            input_data={},
            metadata={"user_id": "u1", "trace_id": "t1"},
        )
        assert ctx.metadata["user_id"] == "u1"
        assert ctx.metadata["trace_id"] == "t1"


# ---------------------------------------------------------------------------
# SagaTimeoutError / SagaCompensationError
# ---------------------------------------------------------------------------


class TestSagaExceptions:
    def test_timeout_error(self):
        err = SagaTimeoutError("timed out")
        assert str(err) == "timed out"

    def test_timeout_error_raises(self):
        with pytest.raises(SagaTimeoutError):
            raise SagaTimeoutError("timeout")

    def test_compensation_error(self):
        err = SagaCompensationError("comp failed")
        assert str(err) == "comp failed"

    def test_compensation_error_raises(self):
        with pytest.raises(SagaCompensationError):
            raise SagaCompensationError("comp failed")


# ---------------------------------------------------------------------------
# SagaOrchestrator.register_saga / get_saga_definition
# ---------------------------------------------------------------------------


class TestOrchestratorRegistration:
    def setup_method(self):
        self.mock_db = MagicMock()
        self.orch = SagaOrchestrator(self.mock_db)

    def test_register_and_get(self):
        d = _definition("my_saga")
        self.orch.register_saga(d)
        result = self.orch.get_saga_definition("my_saga")
        assert result.name == "my_saga"

    def test_register_duplicate_raises(self):
        d = _definition("my_saga")
        self.orch.register_saga(d)
        with pytest.raises(ValueError, match="already registered"):
            self.orch.register_saga(d)

    def test_get_unregistered_raises(self):
        with pytest.raises(ValueError, match="not registered"):
            self.orch.get_saga_definition("nonexistent")

    def test_register_multiple(self):
        self.orch.register_saga(_definition("saga1"))
        self.orch.register_saga(_definition("saga2"))
        assert self.orch.get_saga_definition("saga1").name == "saga1"
        assert self.orch.get_saga_definition("saga2").name == "saga2"


# ---------------------------------------------------------------------------
# SagaOrchestrator._group_steps_for_execution
# ---------------------------------------------------------------------------


class TestGroupStepsForExecution:
    def setup_method(self):
        self.mock_db = MagicMock()
        self.orch = SagaOrchestrator(self.mock_db)

    def test_single_sequential_step(self):
        steps = [_step("s1")]
        groups = self.orch._group_steps_for_execution(steps)
        assert len(groups) == 1
        assert len(groups[0]) == 1
        assert groups[0][0].name == "s1"

    def test_multiple_sequential_steps(self):
        steps = [_step("s1"), _step("s2"), _step("s3")]
        groups = self.orch._group_steps_for_execution(steps)
        assert len(groups) == 3
        assert all(len(g) == 1 for g in groups)

    def test_parallel_group(self):
        steps = [
            _step("s1", parallel_group="g1"),
            _step("s2", parallel_group="g1"),
        ]
        groups = self.orch._group_steps_for_execution(steps)
        assert len(groups) == 1
        assert len(groups[0]) == 2

    def test_sequential_then_parallel(self):
        steps = [
            _step("s1"),
            _step("s2", parallel_group="g1"),
            _step("s3", parallel_group="g1"),
        ]
        groups = self.orch._group_steps_for_execution(steps)
        assert len(groups) == 2
        assert len(groups[0]) == 1  # s1 alone
        assert len(groups[1]) == 2  # s2, s3 parallel

    def test_parallel_then_sequential(self):
        steps = [
            _step("s1", parallel_group="g1"),
            _step("s2", parallel_group="g1"),
            _step("s3"),
        ]
        groups = self.orch._group_steps_for_execution(steps)
        assert len(groups) == 2
        assert len(groups[0]) == 2  # s1, s2 parallel
        assert len(groups[1]) == 1  # s3 alone

    def test_mixed_groups(self):
        steps = [
            _step("s1"),
            _step("s2", parallel_group="a"),
            _step("s3", parallel_group="a"),
            _step("s4"),
            _step("s5", parallel_group="b"),
            _step("s6", parallel_group="b"),
            _step("s7", parallel_group="b"),
        ]
        groups = self.orch._group_steps_for_execution(steps)
        assert len(groups) == 4
        assert [len(g) for g in groups] == [1, 2, 1, 3]

    def test_empty_steps(self):
        groups = self.orch._group_steps_for_execution([])
        assert groups == []

    def test_single_parallel_step(self):
        """A parallel group with one step still becomes its own group."""
        steps = [_step("s1", parallel_group="g1")]
        groups = self.orch._group_steps_for_execution(steps)
        assert len(groups) == 1
        assert len(groups[0]) == 1

    def test_three_parallel_steps(self):
        steps = [
            _step("s1", parallel_group="g1"),
            _step("s2", parallel_group="g1"),
            _step("s3", parallel_group="g1"),
        ]
        groups = self.orch._group_steps_for_execution(steps)
        assert len(groups) == 1
        assert len(groups[0]) == 3

    def test_two_separate_parallel_groups(self):
        steps = [
            _step("s1", parallel_group="a"),
            _step("s2", parallel_group="a"),
            _step("s3", parallel_group="b"),
            _step("s4", parallel_group="b"),
        ]
        groups = self.orch._group_steps_for_execution(steps)
        assert len(groups) == 2
        assert len(groups[0]) == 2
        assert len(groups[1]) == 2
        assert groups[0][0].name == "s1"
        assert groups[1][0].name == "s3"


# ---------------------------------------------------------------------------
# Integration: definition -> registration -> group extraction
# ---------------------------------------------------------------------------


class TestIntegration:
    def test_full_flow(self):
        """Register a saga and verify step grouping."""
        mock_db = MagicMock()
        orch = SagaOrchestrator(mock_db)

        steps = [
            _step("validate", parallel_group=None),
            _step("reserve_a", parallel_group="reserve"),
            _step("reserve_b", parallel_group="reserve"),
            _step("confirm", parallel_group=None),
        ]
        defn = _definition("booking", steps=steps, description="Book reservations")
        orch.register_saga(defn)

        retrieved = orch.get_saga_definition("booking")
        assert retrieved.description == "Book reservations"

        groups = orch._group_steps_for_execution(retrieved.steps)
        assert len(groups) == 3
        assert groups[0][0].name == "validate"
        assert len(groups[1]) == 2  # reserve_a, reserve_b
        assert groups[2][0].name == "confirm"

    def test_context_accumulation(self):
        """Verify context accumulates step outputs correctly."""
        ctx = SagaContext(saga_id=uuid4(), input_data={"x": 1})
        ctx.merge_step_output("step1", {"y": 2})
        ctx.merge_step_output("step2", {"z": 3})

        d = ctx.to_dict()
        assert d["input_data"]["x"] == 1
        assert d["accumulated_data"]["step1"]["y"] == 2
        assert d["accumulated_data"]["step2"]["z"] == 3

    def test_result_lifecycle(self):
        """Simulate result going through states."""
        now = datetime(2026, 1, 15, 12, 0)
        r = SagaExecutionResult(
            saga_id=uuid4(),
            status=SagaStatus.PENDING,
        )
        assert not r.is_successful
        assert not r.is_terminal
        assert r.duration_seconds is None

        # Start running
        r.status = SagaStatus.RUNNING
        r.started_at = now
        assert not r.is_terminal

        # Complete
        r.status = SagaStatus.COMPLETED
        r.completed_at = now + timedelta(seconds=30)
        assert r.is_successful
        assert r.is_terminal
        assert r.duration_seconds == 30.0
