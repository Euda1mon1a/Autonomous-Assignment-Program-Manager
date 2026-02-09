"""Tests for state machine schemas (enums, defaults, nested models)."""

from datetime import datetime
from uuid import uuid4

from app.schemas.state_machine import (
    StateMachineStatusSchema,
    StateDefinition,
    TransitionDefinition,
    ParallelStateDefinition,
    StateMachineDefinition,
    StateMachineCreateRequest,
    TransitionRequest,
    StateMachineInstanceResponse,
    StateMachineTransitionResponse,
    StateMachineHistoryResponse,
    StateMachineVisualization,
)


class TestStateMachineStatusSchema:
    def test_values(self):
        assert StateMachineStatusSchema.ACTIVE.value == "active"
        assert StateMachineStatusSchema.COMPLETED.value == "completed"
        assert StateMachineStatusSchema.FAILED.value == "failed"
        assert StateMachineStatusSchema.SUSPENDED.value == "suspended"

    def test_count(self):
        assert len(StateMachineStatusSchema) == 4

    def test_is_str(self):
        assert isinstance(StateMachineStatusSchema.ACTIVE, str)


class TestStateDefinition:
    def test_valid_minimal(self):
        r = StateDefinition(name="idle")
        assert r.is_initial is False
        assert r.is_final is False
        assert r.entry_action is None
        assert r.exit_action is None
        assert r.metadata == {}

    def test_full(self):
        r = StateDefinition(
            name="processing",
            is_initial=True,
            is_final=False,
            entry_action="start_engine",
            exit_action="cleanup",
            metadata={"timeout": 30},
        )
        assert r.is_initial is True
        assert r.metadata["timeout"] == 30


class TestTransitionDefinition:
    def test_valid_minimal(self):
        r = TransitionDefinition(from_state="idle", to_state="active", event="start")
        assert r.guard is None
        assert r.action is None
        assert r.priority == 0

    def test_full(self):
        r = TransitionDefinition(
            from_state="idle",
            to_state="active",
            event="start",
            guard="is_ready",
            action="activate",
            priority=10,
        )
        assert r.priority == 10
        assert r.guard == "is_ready"


class TestParallelStateDefinition:
    def test_valid(self):
        r = ParallelStateDefinition(
            name="region_a", states=["s1", "s2"], initial_state="s1"
        )
        assert len(r.states) == 2
        assert r.initial_state == "s1"


class TestStateMachineDefinition:
    def test_valid_minimal(self):
        state = StateDefinition(name="idle")
        transition = TransitionDefinition(
            from_state="idle", to_state="done", event="finish"
        )
        r = StateMachineDefinition(
            name="my_machine", states=[state], transitions=[transition]
        )
        assert r.parallel_regions == []
        assert r.initial_context == {}

    def test_with_parallel(self):
        state = StateDefinition(name="idle")
        transition = TransitionDefinition(
            from_state="idle", to_state="done", event="finish"
        )
        parallel = ParallelStateDefinition(
            name="region_a", states=["s1", "s2"], initial_state="s1"
        )
        r = StateMachineDefinition(
            name="complex",
            states=[state],
            transitions=[transition],
            parallel_regions=[parallel],
            initial_context={"key": "val"},
        )
        assert len(r.parallel_regions) == 1
        assert r.initial_context["key"] == "val"


class TestStateMachineCreateRequest:
    def test_valid_minimal(self):
        r = StateMachineCreateRequest(machine_name="swap_machine")
        assert r.initial_context == {}
        assert r.entity_type is None
        assert r.entity_id is None

    def test_full(self):
        uid = uuid4()
        r = StateMachineCreateRequest(
            machine_name="swap_machine",
            initial_context={"swap_id": "123"},
            entity_type="swap",
            entity_id=uid,
        )
        assert r.entity_id == uid


class TestTransitionRequest:
    def test_valid_minimal(self):
        r = TransitionRequest(event="approve")
        assert r.context_updates == {}

    def test_with_updates(self):
        r = TransitionRequest(event="approve", context_updates={"approved_by": "admin"})
        assert r.context_updates["approved_by"] == "admin"


class TestStateMachineInstanceResponse:
    def _make_instance(self, **overrides):
        defaults = {
            "id": uuid4(),
            "machine_name": "swap_machine",
            "current_state": "pending",
            "parallel_states": [],
            "status": StateMachineStatusSchema.ACTIVE,
            "context": {},
            "entity_type": None,
            "entity_id": None,
            "owner_id": None,
            "error_message": None,
            "created_at": datetime(2026, 3, 1),
            "updated_at": datetime(2026, 3, 1),
            "completed_at": None,
        }
        defaults.update(overrides)
        return StateMachineInstanceResponse(**defaults)

    def test_valid(self):
        r = self._make_instance()
        assert r.current_state == "pending"
        assert r.completed_at is None

    def test_completed(self):
        r = self._make_instance(
            status=StateMachineStatusSchema.COMPLETED,
            completed_at=datetime(2026, 3, 2),
        )
        assert r.completed_at is not None


class TestStateMachineTransitionResponse:
    def test_valid(self):
        r = StateMachineTransitionResponse(
            id=uuid4(),
            instance_id=uuid4(),
            from_state="pending",
            to_state="approved",
            event="approve",
            guard_passed=None,
            guard_failed=None,
            entry_action=None,
            exit_action=None,
            transition_action=None,
            context_before=None,
            context_after=None,
            triggered_by_id=None,
            error_message=None,
            created_at=datetime(2026, 3, 1),
        )
        assert r.from_state == "pending"
        assert r.to_state == "approved"


class TestStateMachineHistoryResponse:
    def test_valid(self):
        instance = StateMachineInstanceResponse(
            id=uuid4(),
            machine_name="m",
            current_state="done",
            parallel_states=[],
            status=StateMachineStatusSchema.COMPLETED,
            context={},
            entity_type=None,
            entity_id=None,
            owner_id=None,
            error_message=None,
            created_at=datetime(2026, 3, 1),
            updated_at=datetime(2026, 3, 1),
            completed_at=datetime(2026, 3, 2),
        )
        r = StateMachineHistoryResponse(instance=instance, transitions=[])
        assert r.transitions == []


class TestStateMachineVisualization:
    def test_valid(self):
        r = StateMachineVisualization(
            machine_name="swap_machine",
            dot_graph="digraph { idle -> active }",
            states_count=2,
            transitions_count=1,
            has_parallel_regions=False,
        )
        assert r.states_count == 2
        assert r.has_parallel_regions is False
