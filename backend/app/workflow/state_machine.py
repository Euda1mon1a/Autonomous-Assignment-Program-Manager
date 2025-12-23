"""State machine engine for workflow management.

This module provides a flexible, event-driven state machine implementation
with support for:
- Guard conditions for transitions
- Entry/exit actions per state
- State persistence to database
- Complete transition history logging
- Event-driven transitions
- Parallel state support
- State machine visualization export

Example:
    from app.workflow.state_machine import StateMachine, State, Transition

    # Define states
    states = [
        State("draft", is_initial=True, entry_action="on_draft_entry"),
        State("pending_review", entry_action="notify_reviewers"),
        State("approved", exit_action="send_approval_email"),
        State("rejected", is_final=True),
    ]

    # Define transitions
    transitions = [
        Transition("draft", "pending_review", "submit", guard="has_content"),
        Transition("pending_review", "approved", "approve"),
        Transition("pending_review", "rejected", "reject"),
    ]

    # Create and use machine
    machine = StateMachine("document_workflow", states, transitions)
    await machine.create_instance(db, context={"doc_id": "123"})
    result = await machine.trigger_event(db, instance_id, "submit")
"""

import copy
import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.state_machine import (
    StateMachineInstance,
    StateMachineStatus,
    StateMachineTransition,
)

logger = logging.getLogger(__name__)


@dataclass
class StateMachineContext:
    """
    Context object passed to guards and actions.

    Contains the current state of the machine and provides access to
    the persistent instance data.
    """

    instance_id: UUID
    current_state: str
    data: dict[str, Any]
    triggered_by_id: UUID | None = None

    def get(self, key: str, default: Any = None) -> Any:
        """Get value from context data."""
        return self.data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set value in context data."""
        self.data[key] = value

    def update(self, updates: dict[str, Any]) -> None:
        """Update multiple values in context data."""
        self.data.update(updates)


@dataclass
class TransitionEvent:
    """Event that triggers a state transition."""

    name: str
    data: dict[str, Any] = field(default_factory=dict)
    triggered_by_id: UUID | None = None


# Type aliases for callbacks
Guard = Callable[[StateMachineContext], bool]
Action = Callable[[StateMachineContext], None]


@dataclass
class State:
    """
    Definition of a state in the state machine.

    Args:
        name: Unique identifier for this state
        is_initial: Whether this is the starting state
        is_final: Whether this is a terminal state
        entry_action: Name of action to execute when entering this state
        exit_action: Name of action to execute when leaving this state
        metadata: Additional metadata for this state
    """

    name: str
    is_initial: bool = False
    is_final: bool = False
    entry_action: str | None = None
    exit_action: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __hash__(self):
        return hash(self.name)


@dataclass
class Transition:
    """
    Definition of a transition between states.

    Args:
        from_state: Source state name
        to_state: Destination state name
        event: Event name that triggers this transition
        guard: Name of guard condition (must return True to allow transition)
        action: Name of action to execute during transition
        priority: Priority when multiple transitions match (higher = higher priority)
    """

    from_state: str
    to_state: str
    event: str
    guard: str | None = None
    action: str | None = None
    priority: int = 0

    def matches(self, current_state: str, event_name: str) -> bool:
        """Check if this transition matches the current state and event."""
        return self.from_state == current_state and self.event == event_name


@dataclass
class ParallelState:
    """
    Definition of a parallel state region.

    Parallel states allow multiple states to be active simultaneously.
    Each region operates independently with its own state transitions.

    Args:
        name: Name of the parallel region
        states: List of state names in this region
        initial_state: Starting state for this region
    """

    name: str
    states: list[str]
    initial_state: str


class StateMachineError(Exception):
    """Base exception for state machine errors."""

    pass


class InvalidTransitionError(StateMachineError):
    """Raised when an invalid transition is attempted."""

    pass


class GuardFailedError(StateMachineError):
    """Raised when a guard condition fails."""

    pass


class StateMachine:
    """
    Event-driven state machine with persistence and history tracking.

    Features:
    - Define states with entry/exit actions
    - Guard conditions for transitions
    - Event-driven transitions
    - Full transition history logging
    - Parallel state support
    - Context data management
    - Visualization export

    Guards and actions are registered by name and can be async functions.
    """

    def __init__(
        self,
        name: str,
        states: list[State],
        transitions: list[Transition],
        parallel_regions: list[ParallelState] | None = None,
    ):
        """
        Initialize state machine definition.

        Args:
            name: Unique name for this state machine
            states: List of state definitions
            transitions: List of transition definitions
            parallel_regions: Optional list of parallel state regions

        Raises:
            ValueError: If state machine definition is invalid
        """
        self.name = name
        self.states = {s.name: s for s in states}
        self.transitions = transitions
        self.parallel_regions = parallel_regions or []

        # Registries for guards and actions
        self._guards: dict[str, Guard] = {}
        self._actions: dict[str, Action] = {}

        # Validate the machine definition
        self._validate_definition()

    def _validate_definition(self) -> None:
        """Validate state machine definition."""
        # Check for exactly one initial state
        initial_states = [s for s in self.states.values() if s.is_initial]
        if len(initial_states) == 0:
            raise ValueError(f"State machine '{self.name}' has no initial state")
        if len(initial_states) > 1:
            raise ValueError(f"State machine '{self.name}' has multiple initial states")

        # Validate transitions reference valid states
        for transition in self.transitions:
            if transition.from_state not in self.states:
                raise ValueError(
                    f"Transition references unknown state: {transition.from_state}"
                )
            if transition.to_state not in self.states:
                raise ValueError(
                    f"Transition references unknown state: {transition.to_state}"
                )

        # Validate parallel regions
        for region in self.parallel_regions:
            if region.initial_state not in region.states:
                raise ValueError(
                    f"Parallel region '{region.name}' initial state not in region states"
                )
            for state_name in region.states:
                if state_name not in self.states:
                    raise ValueError(
                        f"Parallel region '{region.name}' references unknown state: {state_name}"
                    )

    def register_guard(self, name: str, guard_func: Guard) -> None:
        """
        Register a guard condition.

        Args:
            name: Name to register the guard under
            guard_func: Function that takes StateMachineContext and returns bool
        """
        self._guards[name] = guard_func

    def register_action(self, name: str, action_func: Action) -> None:
        """
        Register an action.

        Args:
            name: Name to register the action under
            action_func: Function that takes StateMachineContext and returns None
        """
        self._actions[name] = action_func

    def get_initial_state(self) -> State:
        """Get the initial state of the machine."""
        for state in self.states.values():
            if state.is_initial:
                return state
        raise ValueError("No initial state found")

    def create_instance(
        self,
        db: Session,
        context: dict[str, Any] | None = None,
        entity_type: str | None = None,
        entity_id: UUID | None = None,
        owner_id: UUID | None = None,
    ) -> StateMachineInstance:
        """
        Create a new state machine instance.

        Args:
            db: Database session
            context: Initial context data
            entity_type: Type of entity this machine manages
            entity_id: ID of entity this machine manages
            owner_id: User who owns this instance

        Returns:
            Created StateMachineInstance
        """
        initial_state = self.get_initial_state()
        context_data = context or {}

        # Create instance
        instance = StateMachineInstance(
            machine_name=self.name,
            current_state=initial_state.name,
            parallel_states=[],
            status=StateMachineStatus.ACTIVE.value,
            context=context_data,
            entity_type=entity_type,
            entity_id=entity_id,
            owner_id=owner_id,
        )

        db.add(instance)
        db.flush()

        # Initialize parallel regions if any
        if self.parallel_regions:
            parallel_state_data = [
                {"region": region.name, "state": region.initial_state}
                for region in self.parallel_regions
            ]
            instance.parallel_states = parallel_state_data

        # Execute entry action for initial state
        if initial_state.entry_action:
            ctx = StateMachineContext(
                instance_id=instance.id,
                current_state=initial_state.name,
                data=copy.deepcopy(context_data),
            )
            self._execute_action_sync(initial_state.entry_action, ctx)
            instance.context = ctx.data

        db.commit()
        db.refresh(instance)

        logger.info(
            f"Created state machine instance {instance.id} "
            f"for machine '{self.name}' in state '{initial_state.name}'"
        )

        return instance

    def trigger_event(
        self,
        db: Session,
        instance_id: UUID,
        event: str | TransitionEvent,
        context_updates: dict[str, Any] | None = None,
    ) -> StateMachineInstance:
        """
        Trigger an event on a state machine instance.

        Args:
            db: Database session
            instance_id: ID of the state machine instance
            event: Event name or TransitionEvent object
            context_updates: Optional updates to merge into context

        Returns:
            Updated StateMachineInstance

        Raises:
            InvalidTransitionError: If no valid transition exists
            GuardFailedError: If guard condition fails
        """
        # Load instance with transitions
        instance = (
            db.query(StateMachineInstance)
            .filter(StateMachineInstance.id == instance_id)
            .first()
        )

        if not instance:
            raise ValueError(f"State machine instance {instance_id} not found")

        if instance.status != StateMachineStatus.ACTIVE.value:
            raise StateMachineError(
                f"Cannot trigger event on instance with status {instance.status}"
            )

        # Parse event
        if isinstance(event, str):
            event_obj = TransitionEvent(name=event)
        else:
            event_obj = event

        # Merge context updates
        if context_updates:
            instance.context.update(context_updates)
        if event_obj.data:
            instance.context.update(event_obj.data)

        # Find matching transitions (sorted by priority descending)
        matching_transitions = [
            t
            for t in self.transitions
            if t.matches(instance.current_state, event_obj.name)
        ]
        matching_transitions.sort(key=lambda t: t.priority, reverse=True)

        if not matching_transitions:
            raise InvalidTransitionError(
                f"No transition found from state '{instance.current_state}' "
                f"on event '{event_obj.name}'"
            )

        # Try transitions in priority order until one succeeds
        transition = None
        guard_failed_name = None

        for candidate in matching_transitions:
            # Evaluate guard if present
            if candidate.guard:
                ctx = StateMachineContext(
                    instance_id=instance.id,
                    current_state=instance.current_state,
                    data=copy.deepcopy(instance.context),
                    triggered_by_id=event_obj.triggered_by_id,
                )
                if self._evaluate_guard_sync(candidate.guard, ctx):
                    transition = candidate
                    break
                else:
                    guard_failed_name = candidate.guard
            else:
                transition = candidate
                break

        if not transition:
            raise GuardFailedError(
                f"All transitions from '{instance.current_state}' on event "
                f"'{event_obj.name}' failed guard conditions"
            )

        # Execute the transition
        self._execute_transition_sync(
            db,
            instance,
            transition,
            event_obj.triggered_by_id,
            guard_failed_name,
        )

        db.commit()
        db.refresh(instance)

        logger.info(
            f"Transitioned instance {instance_id} from '{transition.from_state}' "
            f"to '{transition.to_state}' on event '{event_obj.name}'"
        )

        return instance

    def _execute_transition_sync(
        self,
        db: Session,
        instance: StateMachineInstance,
        transition: Transition,
        triggered_by_id: UUID | None,
        guard_failed_name: str | None,
    ) -> None:
        """Execute a state transition with all actions (synchronous version)."""
        from_state_obj = self.states[transition.from_state]
        to_state_obj = self.states[transition.to_state]

        # Snapshot context before transition
        context_before = copy.deepcopy(instance.context)

        # Create context
        ctx = StateMachineContext(
            instance_id=instance.id,
            current_state=instance.current_state,
            data=copy.deepcopy(instance.context),
            triggered_by_id=triggered_by_id,
        )

        # Execute exit action on old state
        exit_action_name = None
        if from_state_obj.exit_action:
            exit_action_name = from_state_obj.exit_action
            self._execute_action_sync(from_state_obj.exit_action, ctx)

        # Execute transition action
        transition_action_name = None
        if transition.action:
            transition_action_name = transition.action
            self._execute_action_sync(transition.action, ctx)

        # Update state
        instance.current_state = transition.to_state
        instance.context = ctx.data
        instance.updated_at = datetime.utcnow()

        # Execute entry action on new state
        entry_action_name = None
        if to_state_obj.entry_action:
            entry_action_name = to_state_obj.entry_action
            self._execute_action_sync(to_state_obj.entry_action, ctx)
            instance.context = ctx.data

        # Check if reached final state
        if to_state_obj.is_final:
            instance.status = StateMachineStatus.COMPLETED.value
            instance.completed_at = datetime.utcnow()

        # Record transition in history
        transition_record = StateMachineTransition(
            instance_id=instance.id,
            from_state=transition.from_state,
            to_state=transition.to_state,
            event=transition.event,
            guard_passed=transition.guard if transition.guard else None,
            guard_failed=guard_failed_name,
            entry_action=entry_action_name,
            exit_action=exit_action_name,
            transition_action=transition_action_name,
            context_before=context_before,
            context_after=instance.context,
            triggered_by_id=triggered_by_id,
        )

        db.add(transition_record)

    def _evaluate_guard_sync(self, guard_name: str, ctx: StateMachineContext) -> bool:
        """Evaluate a guard condition (synchronous version)."""
        if guard_name not in self._guards:
            logger.warning(f"Guard '{guard_name}' not registered, defaulting to True")
            return True

        try:
            guard_func = self._guards[guard_name]
            result = guard_func(ctx)
            return bool(result)
        except Exception as e:
            logger.error(f"Error evaluating guard '{guard_name}': {e}", exc_info=True)
            return False

    def _execute_action_sync(self, action_name: str, ctx: StateMachineContext) -> None:
        """Execute an action (synchronous version)."""
        if action_name not in self._actions:
            logger.warning(f"Action '{action_name}' not registered, skipping")
            return

        try:
            action_func = self._actions[action_name]
            result = action_func(ctx)
            # Note: Synchronous version does not support async actions
        except Exception as e:
            logger.error(f"Error executing action '{action_name}': {e}", exc_info=True)
            raise

    def get_instance(
        self,
        db: Session,
        instance_id: UUID,
    ) -> StateMachineInstance | None:
        """
        Get a state machine instance by ID.

        Args:
            db: Database session
            instance_id: Instance ID

        Returns:
            StateMachineInstance or None if not found
        """
        return (
            db.query(StateMachineInstance)
            .filter(StateMachineInstance.id == instance_id)
            .first()
        )

    def get_history(
        self,
        db: Session,
        instance_id: UUID,
    ) -> list[StateMachineTransition]:
        """
        Get complete transition history for an instance.

        Args:
            db: Database session
            instance_id: Instance ID

        Returns:
            List of transitions ordered by creation time
        """
        return (
            db.query(StateMachineTransition)
            .filter(StateMachineTransition.instance_id == instance_id)
            .order_by(StateMachineTransition.created_at)
            .all()
        )

    def suspend_instance(
        self,
        db: Session,
        instance_id: UUID,
    ) -> StateMachineInstance:
        """
        Suspend a running state machine instance.

        Args:
            db: Database session
            instance_id: Instance ID

        Returns:
            Updated instance
        """
        instance = self.get_instance(db, instance_id)
        if not instance:
            raise ValueError(f"Instance {instance_id} not found")

        instance.status = StateMachineStatus.SUSPENDED.value
        instance.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(instance)

        logger.info(f"Suspended state machine instance {instance_id}")
        return instance

    def resume_instance(
        self,
        db: Session,
        instance_id: UUID,
    ) -> StateMachineInstance:
        """
        Resume a suspended state machine instance.

        Args:
            db: Database session
            instance_id: Instance ID

        Returns:
            Updated instance
        """
        instance = self.get_instance(db, instance_id)
        if not instance:
            raise ValueError(f"Instance {instance_id} not found")

        if instance.status != StateMachineStatus.SUSPENDED.value:
            raise StateMachineError(
                f"Cannot resume instance with status {instance.status}"
            )

        instance.status = StateMachineStatus.ACTIVE.value
        instance.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(instance)

        logger.info(f"Resumed state machine instance {instance_id}")
        return instance

    def export_visualization(self, format: str = "dot") -> str:
        """
        Export state machine as visualization.

        Args:
            format: Export format (currently only 'dot' is supported)

        Returns:
            GraphViz DOT format string

        Example:
            dot_output = machine.export_visualization()
            # Save to file and render:
            # dot -Tpng output.dot -o output.png
        """
        if format != "dot":
            raise ValueError(f"Unsupported format: {format}")

        lines = [
            "digraph {",
            "  rankdir=LR;",
            "  node [shape=circle];",
            "",
        ]

        # Define states
        for state in self.states.values():
            shape = "doublecircle" if state.is_final else "circle"
            label = state.name

            # Add entry/exit actions to label
            actions = []
            if state.entry_action:
                actions.append(f"entry: {state.entry_action}")
            if state.exit_action:
                actions.append(f"exit: {state.exit_action}")

            if actions:
                label += "\\n" + "\\n".join(actions)

            lines.append(f'  {state.name} [label="{label}", shape={shape}];')

        lines.append("")

        # Initial state marker
        initial_state = self.get_initial_state()
        lines.append("  __start__ [shape=point];")
        lines.append(f"  __start__ -> {initial_state.name};")
        lines.append("")

        # Define transitions
        for transition in self.transitions:
            label = transition.event

            # Add guard and action to label
            details = []
            if transition.guard:
                details.append(f"[{transition.guard}]")
            if transition.action:
                details.append(f"/ {transition.action}")

            if details:
                label += "\\n" + " ".join(details)

            lines.append(
                f'  {transition.from_state} -> {transition.to_state} [label="{label}"];'
            )

        lines.append("}")

        return "\n".join(lines)
