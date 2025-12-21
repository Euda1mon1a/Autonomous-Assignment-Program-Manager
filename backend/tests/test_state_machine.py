"""Tests for state machine engine."""
import pytest
from datetime import datetime
from uuid import uuid4

from app.workflow.state_machine import (
    Action,
    Guard,
    GuardFailedError,
    InvalidTransitionError,
    ParallelState,
    State,
    StateMachine,
    StateMachineContext,
    StateMachineError,
    Transition,
    TransitionEvent,
)
from app.models.state_machine import (
    StateMachineInstance,
    StateMachineStatus,
    StateMachineTransition,
)
from app.models.user import User
from app.core.security import get_password_hash


@pytest.fixture
def test_user(db):
    """Create a test user for state machine tests."""
    user = User(
        id=uuid4(),
        username="testuser",
        email="testuser@test.org",
        hashed_password=get_password_hash("testpass123"),
        role="admin",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def simple_machine():
    """Create a simple state machine for testing."""
    states = [
        State("draft", is_initial=True),
        State("review"),
        State("approved", is_final=True),
        State("rejected", is_final=True),
    ]

    transitions = [
        Transition("draft", "review", "submit"),
        Transition("review", "approved", "approve"),
        Transition("review", "rejected", "reject"),
    ]

    return StateMachine("document_workflow", states, transitions)


@pytest.fixture
def machine_with_guards():
    """Create a state machine with guard conditions."""
    states = [
        State("initial", is_initial=True),
        State("processing"),
        State("completed", is_final=True),
    ]

    transitions = [
        Transition("initial", "processing", "start", guard="has_required_data"),
        Transition("processing", "completed", "finish"),
    ]

    machine = StateMachine("guarded_workflow", states, transitions)

    # Register guard
    def has_required_data(ctx: StateMachineContext) -> bool:
        return ctx.get("required_field") is not None

    machine.register_guard("has_required_data", has_required_data)

    return machine


@pytest.fixture
def machine_with_actions():
    """Create a state machine with entry/exit actions."""
    states = [
        State("idle", is_initial=True, entry_action="on_idle_entry"),
        State("active", entry_action="on_active_entry", exit_action="on_active_exit"),
        State("done", is_final=True),
    ]

    transitions = [
        Transition("idle", "active", "activate", action="on_activate"),
        Transition("active", "done", "complete"),
    ]

    machine = StateMachine("action_workflow", states, transitions)

    # Track action executions
    action_log = []

    def on_idle_entry(ctx: StateMachineContext):
        action_log.append("idle_entry")
        ctx.set("idle_entered", True)

    def on_active_entry(ctx: StateMachineContext):
        action_log.append("active_entry")
        ctx.set("active_entered", True)

    def on_active_exit(ctx: StateMachineContext):
        action_log.append("active_exit")
        ctx.set("active_exited", True)

    def on_activate(ctx: StateMachineContext):
        action_log.append("activate_transition")
        ctx.set("activated", True)

    machine.register_action("on_idle_entry", on_idle_entry)
    machine.register_action("on_active_entry", on_active_entry)
    machine.register_action("on_active_exit", on_active_exit)
    machine.register_action("on_activate", on_activate)

    machine.action_log = action_log

    return machine


@pytest.fixture
def machine_with_parallel_states():
    """Create a state machine with parallel state regions."""
    states = [
        State("initial", is_initial=True),
        State("region1_s1"),
        State("region1_s2"),
        State("region2_s1"),
        State("region2_s2"),
        State("done", is_final=True),
    ]

    transitions = [
        Transition("initial", "region1_s1", "start"),
        Transition("region1_s1", "region1_s2", "advance_r1"),
        Transition("region2_s1", "region2_s2", "advance_r2"),
        Transition("region1_s2", "done", "finish"),
    ]

    parallel_regions = [
        ParallelState("region1", ["region1_s1", "region1_s2"], "region1_s1"),
        ParallelState("region2", ["region2_s1", "region2_s2"], "region2_s1"),
    ]

    return StateMachine(
        "parallel_workflow",
        states,
        transitions,
        parallel_regions=parallel_regions
    )


class TestStateMachineDefinition:
    """Test state machine definition and validation."""

    def test_create_simple_machine(self, simple_machine):
        """Test creating a basic state machine."""
        assert simple_machine.name == "document_workflow"
        assert len(simple_machine.states) == 4
        assert len(simple_machine.transitions) == 3

    def test_get_initial_state(self, simple_machine):
        """Test getting initial state."""
        initial = simple_machine.get_initial_state()
        assert initial.name == "draft"
        assert initial.is_initial is True

    def test_machine_without_initial_state_fails(self):
        """Test that machine without initial state raises error."""
        states = [
            State("state1"),
            State("state2"),
        ]
        transitions = [
            Transition("state1", "state2", "event"),
        ]

        with pytest.raises(ValueError, match="no initial state"):
            StateMachine("invalid", states, transitions)

    def test_machine_with_multiple_initial_states_fails(self):
        """Test that machine with multiple initial states raises error."""
        states = [
            State("state1", is_initial=True),
            State("state2", is_initial=True),
        ]
        transitions = []

        with pytest.raises(ValueError, match="multiple initial states"):
            StateMachine("invalid", states, transitions)

    def test_transition_to_unknown_state_fails(self):
        """Test that transitions to unknown states raise error."""
        states = [
            State("state1", is_initial=True),
        ]
        transitions = [
            Transition("state1", "unknown_state", "event"),
        ]

        with pytest.raises(ValueError, match="unknown state"):
            StateMachine("invalid", states, transitions)


class TestStateMachineInstance:
    """Test state machine instance creation and management."""

    def test_create_instance(self, simple_machine, db):
        """Test creating a state machine instance."""
        instance = simple_machine.create_instance(
            db,
            context={"doc_id": "123"},
            entity_type="document",
            entity_id=uuid4(),
        )

        assert instance.id is not None
        assert instance.machine_name == "document_workflow"
        assert instance.current_state == "draft"
        assert instance.status == StateMachineStatus.ACTIVE.value
        assert instance.context == {"doc_id": "123"}

    def test_create_instance_with_owner(self, simple_machine, db, test_user):
        """Test creating instance with owner."""
        instance = simple_machine.create_instance(
            db,
            owner_id=test_user.id,
        )

        assert instance.owner_id == test_user.id

    def test_get_instance(self, simple_machine, db):
        """Test retrieving a state machine instance."""
        instance = simple_machine.create_instance(db)

        retrieved = simple_machine.get_instance(db, instance.id)

        assert retrieved is not None
        assert retrieved.id == instance.id
        assert retrieved.current_state == instance.current_state

    def test_suspend_instance(self, simple_machine, db):
        """Test suspending a state machine instance."""
        instance = simple_machine.create_instance(db)

        suspended = simple_machine.suspend_instance(db, instance.id)

        assert suspended.status == StateMachineStatus.SUSPENDED.value

    def test_resume_instance(self, simple_machine, db):
        """Test resuming a suspended instance."""
        instance = simple_machine.create_instance(db)
        simple_machine.suspend_instance(db, instance.id)

        resumed = simple_machine.resume_instance(db, instance.id)

        assert resumed.status == StateMachineStatus.ACTIVE.value

    def test_resume_non_suspended_instance_fails(self, simple_machine, db):
        """Test that resuming active instance raises error."""
        instance = simple_machine.create_instance(db)

        with pytest.raises(StateMachineError, match="Cannot resume"):
            simple_machine.resume_instance(db, instance.id)


class TestStateTransitions:
    """Test state transitions."""

    def test_simple_transition(self, simple_machine, db):
        """Test a simple state transition."""
        instance = simple_machine.create_instance(db)

        # Transition from draft to review
        updated = simple_machine.trigger_event(db, instance.id, "submit")

        assert updated.current_state == "review"
        assert updated.status == StateMachineStatus.ACTIVE.value

    def test_transition_to_final_state(self, simple_machine, db):
        """Test transitioning to a final state completes the machine."""
        instance = simple_machine.create_instance(db)

        # draft -> review -> approved
        simple_machine.trigger_event(db, instance.id, "submit")
        updated = simple_machine.trigger_event(db, instance.id, "approve")

        assert updated.current_state == "approved"
        assert updated.status == StateMachineStatus.COMPLETED.value
        assert updated.completed_at is not None

    def test_invalid_transition_fails(self, simple_machine, db):
        """Test that invalid transitions raise error."""
        instance = simple_machine.create_instance(db)

        with pytest.raises(InvalidTransitionError):
            simple_machine.trigger_event(db, instance.id, "approve")

    def test_transition_with_event_object(self, simple_machine, db):
        """Test triggering transition with TransitionEvent object."""
        instance = simple_machine.create_instance(db)

        event = TransitionEvent(
            name="submit",
            data={"reviewer_id": "reviewer_123"},
        )

        updated = simple_machine.trigger_event(db, instance.id, event)

        assert updated.current_state == "review"
        assert updated.context["reviewer_id"] == "reviewer_123"

    def test_transition_with_context_updates(self, simple_machine, db):
        """Test transition with context updates."""
        instance = simple_machine.create_instance(db)

        updated = simple_machine.trigger_event(
            db,
            instance.id,
            "submit",
            context_updates={"submitted_at": "2024-01-01"},
        )

        assert updated.context["submitted_at"] == "2024-01-01"


class TestGuardConditions:
    """Test guard conditions."""

    def test_guard_passes(self, machine_with_guards, db):
        """Test transition with passing guard."""
        instance = machine_with_guards.create_instance(
            db,
            context={"required_field": "value"},
        )

        updated = machine_with_guards.trigger_event(db, instance.id, "start")

        assert updated.current_state == "processing"

    def test_guard_fails(self, machine_with_guards, db):
        """Test transition with failing guard."""
        instance = machine_with_guards.create_instance(db)

        with pytest.raises(GuardFailedError):
            machine_with_guards.trigger_event(db, instance.id, "start")

    def test_transition_priority_with_guards(self, db):
        """Test that higher priority transitions are tried first."""
        states = [
            State("start", is_initial=True),
            State("high_priority_path"),
            State("low_priority_path"),
        ]

        transitions = [
            Transition("start", "low_priority_path", "go", priority=1),
            Transition("start", "high_priority_path", "go", priority=10, guard="always_true"),
        ]

        machine = StateMachine("priority_test", states, transitions)
        machine.register_guard("always_true", lambda ctx: True)

        instance = machine.create_instance(db)
        updated = machine.trigger_event(db, instance.id, "go")

        # Should take high priority path
        assert updated.current_state == "high_priority_path"


class TestActions:
    """Test entry/exit/transition actions."""

    def test_entry_action_on_initial_state(self, machine_with_actions, db):
        """Test that entry action executes on initial state."""
        instance = machine_with_actions.create_instance(db)

        assert "idle_entry" in machine_with_actions.action_log
        assert instance.context["idle_entered"] is True

    def test_entry_and_exit_actions(self, machine_with_actions, db):
        """Test entry and exit actions during transition."""
        instance = machine_with_actions.create_instance(db)
        machine_with_actions.action_log.clear()

        machine_with_actions.trigger_event(db, instance.id, "activate")

        # Should execute: exit (none for idle) -> transition -> entry
        assert "activate_transition" in machine_with_actions.action_log
        assert "active_entry" in machine_with_actions.action_log

    def test_action_execution_order(self, machine_with_actions, db):
        """Test that actions execute in correct order."""
        instance = machine_with_actions.create_instance(db)
        machine_with_actions.action_log.clear()

        # idle -> active
        machine_with_actions.trigger_event(db, instance.id, "activate")

        # Order: exit_action, transition_action, entry_action
        # idle has no exit action, so: transition, entry
        assert machine_with_actions.action_log == ["activate_transition", "active_entry"]

        machine_with_actions.action_log.clear()

        # active -> done
        machine_with_actions.trigger_event(db, instance.id, "complete")

        # active has exit action, done has no entry action
        assert machine_with_actions.action_log == ["active_exit"]

    def test_action_modifies_context(self, machine_with_actions, db):
        """Test that actions can modify context."""
        instance = machine_with_actions.create_instance(db)

        updated = machine_with_actions.trigger_event(db, instance.id, "activate")

        assert updated.context["activated"] is True
        assert updated.context["active_entered"] is True


class TestTransitionHistory:
    """Test transition history logging."""

    def test_transition_recorded_in_history(self, simple_machine, db):
        """Test that transitions are recorded in history."""
        instance = simple_machine.create_instance(db)

        simple_machine.trigger_event(db, instance.id, "submit")

        history = simple_machine.get_history(db, instance.id)

        assert len(history) == 1
        assert history[0].from_state == "draft"
        assert history[0].to_state == "review"
        assert history[0].event == "submit"

    def test_history_tracks_multiple_transitions(self, simple_machine, db):
        """Test history with multiple transitions."""
        instance = simple_machine.create_instance(db)

        simple_machine.trigger_event(db, instance.id, "submit")
        simple_machine.trigger_event(db, instance.id, "approve")

        history = simple_machine.get_history(db, instance.id)

        assert len(history) == 2
        assert history[0].to_state == "review"
        assert history[1].to_state == "approved"

    def test_history_captures_context(self, simple_machine, db):
        """Test that history captures context snapshots."""
        instance = simple_machine.create_instance(
            db,
            context={"initial": "value"},
        )

        simple_machine.trigger_event(
            db,
            instance.id,
            "submit",
            context_updates={"new_field": "new_value"},
        )

        history = simple_machine.get_history(db, instance.id)

        transition = history[0]
        assert transition.context_before["initial"] == "value"
        assert "new_field" not in transition.context_before
        assert transition.context_after["new_field"] == "new_value"

    def test_history_tracks_actions_executed(self, machine_with_actions, db):
        """Test that history records which actions were executed."""
        instance = machine_with_actions.create_instance(db)

        machine_with_actions.trigger_event(db, instance.id, "activate")

        history = machine_with_actions.get_history(db, instance.id)

        transition = history[0]
        assert transition.entry_action == "on_active_entry"
        assert transition.transition_action == "on_activate"


class TestParallelStates:
    """Test parallel state regions."""

    def test_parallel_regions_initialized(self, machine_with_parallel_states, db):
        """Test that parallel regions are initialized correctly."""
        instance = machine_with_parallel_states.create_instance(db)

        assert len(instance.parallel_states) == 2

        regions = {ps["region"]: ps["state"] for ps in instance.parallel_states}
        assert regions["region1"] == "region1_s1"
        assert regions["region2"] == "region2_s1"


class TestVisualization:
    """Test state machine visualization export."""

    def test_export_dot_format(self, simple_machine):
        """Test exporting state machine to DOT format."""
        dot = simple_machine.export_visualization("dot")

        assert "digraph {" in dot
        assert "draft" in dot
        assert "review" in dot
        assert "approved" in dot
        assert "rejected" in dot
        assert "submit" in dot
        assert "approve" in dot
        assert "reject" in dot

    def test_dot_includes_initial_state_marker(self, simple_machine):
        """Test that DOT output includes initial state marker."""
        dot = simple_machine.export_visualization("dot")

        assert "__start__" in dot
        assert "__start__ -> draft" in dot

    def test_dot_marks_final_states(self, simple_machine):
        """Test that final states are marked with double circles."""
        dot = simple_machine.export_visualization("dot")

        # Final states should have doublecircle shape
        assert "approved" in dot
        assert "doublecircle" in dot

    def test_dot_includes_actions(self, machine_with_actions):
        """Test that DOT output includes action names."""
        dot = machine_with_actions.export_visualization("dot")

        assert "on_idle_entry" in dot or "entry:" in dot
        assert "on_active_entry" in dot or "entry:" in dot
        assert "on_active_exit" in dot or "exit:" in dot

    def test_unsupported_format_fails(self, simple_machine):
        """Test that unsupported export format raises error."""
        with pytest.raises(ValueError, match="Unsupported format"):
            simple_machine.export_visualization("invalid")


class TestCallbackRegistration:
    """Test guard and action callback registration."""

    def test_guard_registration(self, db):
        """Test registering guard functions."""
        states = [
            State("start", is_initial=True),
            State("end"),
        ]

        transitions = [
            Transition("start", "end", "go", guard="check_value"),
        ]

        machine = StateMachine("guard_test", states, transitions)

        # Register guard
        def check_value(ctx: StateMachineContext) -> bool:
            return ctx.get("value") == "allowed"

        machine.register_guard("check_value", check_value)

        # Test with failing guard
        instance = machine.create_instance(db, context={"value": "denied"})
        with pytest.raises(GuardFailedError):
            machine.trigger_event(db, instance.id, "go")

        # Test with passing guard
        instance2 = machine.create_instance(db, context={"value": "allowed"})
        updated = machine.trigger_event(db, instance2.id, "go")
        assert updated.current_state == "end"

    def test_action_registration(self, db):
        """Test registering action functions."""
        states = [
            State("start", is_initial=True, entry_action="init_action"),
            State("end"),
        ]

        transitions = [
            Transition("start", "end", "go"),
        ]

        machine = StateMachine("action_test", states, transitions)

        # Register action
        def init_action(ctx: StateMachineContext):
            ctx.set("initialized", True)
            ctx.set("counter", ctx.get("counter", 0) + 1)

        machine.register_action("init_action", init_action)

        instance = machine.create_instance(db, context={"counter": 0})

        assert instance.context.get("initialized") is True
        assert instance.context.get("counter") == 1
