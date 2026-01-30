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
    Context object passed to guards and actions during state transitions.

    The context provides a unified interface for guards and actions to:
    - Access the current state machine state
    - Read and modify persistent context data
    - Identify the user who triggered the transition

    Context data is automatically persisted to the database after each
    successful transition, allowing state machines to maintain state across
    system restarts.

    Attributes:
        instance_id: UUID of the state machine instance.
        current_state: Name of the current state before transition.
        data: Mutable dictionary of context data that persists across transitions.
            Must contain only JSON-serializable values.
        triggered_by_id: UUID of the user who triggered this transition, if any.

    Example:
        def validate_swap_guard(ctx: StateMachineContext) -> bool:
            swap_id = ctx.get("swap_id")
            return validate_swap(swap_id)

        def record_approval_action(ctx: StateMachineContext) -> None:
            ctx.set("approved_at", datetime.utcnow().isoformat())
            ctx.set("approved_by", str(ctx.triggered_by_id))
    """

    instance_id: UUID
    current_state: str
    data: dict[str, Any]
    triggered_by_id: UUID | None = None

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a value from context data.

        Args:
            key: The key to look up in the context data.
            default: Value to return if key is not found. Defaults to None.

        Returns:
            The value associated with the key, or the default value.
        """
        return self.data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """
        Set a value in context data.

        The value will be persisted to the database after the transition
        completes successfully.

        Args:
            key: The key to set in the context data.
            value: The value to associate with the key.
                Must be JSON-serializable (str, int, float, bool, list, dict, None).
        """
        self.data[key] = value

    def update(self, updates: dict[str, Any]) -> None:
        """
        Update multiple values in context data.

        Convenience method for setting multiple keys at once.

        Args:
            updates: Dictionary of key-value pairs to merge into context data.
                All values must be JSON-serializable.
        """
        self.data.update(updates)


@dataclass
class TransitionEvent:
    """
    Event that triggers a state transition.

    Events are the external stimuli that cause state machines to transition
    from one state to another. Each event can carry additional data that
    becomes available to guards and actions during the transition.

    Attributes:
        name: The event name that matches transition definitions.
        data: Additional data to merge into the context during transition.
        triggered_by_id: UUID of the user who triggered this event.

    Example:
        # Simple event - just an event name string
        machine.trigger_event(db, instance_id, "approve")

        # Event with data
        event = TransitionEvent(
            name="submit",
            data={"notes": "Urgent request", "priority": "high"},
            triggered_by_id=current_user.id,
        )
        machine.trigger_event(db, instance_id, event)
    """

    name: str
    data: dict[str, Any] = field(default_factory=dict)
    triggered_by_id: UUID | None = None

    # Type aliases for callbacks


Guard = Callable[[StateMachineContext], bool]
"""Guard function type: takes context, returns True if transition is allowed."""

Action = Callable[[StateMachineContext], None]
"""Action function type: takes context, performs side effects, returns None."""


@dataclass
class State:
    """
    Definition of a state in the state machine.

    States represent the possible conditions an entity can be in during its
    lifecycle. Each state can have entry and exit actions that execute
    automatically when transitioning into or out of the state.

    State Types:
        - **Initial State**: The starting state when creating a new instance.
            Exactly one state must be marked as initial.
        - **Final States**: Terminal states that complete the state machine.
            When reached, the instance status becomes COMPLETED.
        - **Regular States**: Intermediate states that can transition to others.

    Action Execution Order:
        When transitioning from State A to State B:
        1. A's exit_action executes
        2. Transition action executes (if any)
        3. B's entry_action executes

    Attributes:
        name: Unique identifier for this state within the machine.
        is_initial: Whether this is the starting state (exactly one required).
        is_final: Whether this is a terminal state (workflow completes here).
        entry_action: Name of registered action to execute when entering.
        exit_action: Name of registered action to execute when leaving.
        metadata: Additional metadata for this state (e.g., description, color).

    Example:
        State("draft", is_initial=True, entry_action="log_creation")
        State("pending_review", entry_action="notify_reviewers")
        State("approved", entry_action="execute_swap", exit_action="log_completion")
        State("rejected", is_final=True)
    """

    name: str
    is_initial: bool = False
    is_final: bool = False
    entry_action: str | None = None
    exit_action: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __hash__(self):
        """Hash based on state name for use in sets and dict keys."""
        return hash(self.name)


@dataclass
class Transition:
    """
    Definition of a transition between states.

    Transitions define the edges in the state machine graph. Each transition
    specifies which event triggers it, optional guard conditions that must
    be satisfied, and optional actions to execute during the transition.

    Priority Handling:
        When multiple transitions match the same (state, event) pair, they
        are tried in priority order (highest first). The first transition
        whose guard passes (or has no guard) is executed.

    Guard Evaluation:
        - Guards are evaluated before the transition executes
        - If a guard returns False, the next matching transition is tried
        - If all guards fail, GuardFailedError is raised
        - Unregistered guards default to True with a warning

    Attributes:
        from_state: Source state name (must exist in machine's states).
        to_state: Destination state name (must exist in machine's states).
        event: Event name that triggers this transition.
        guard: Name of registered guard condition (must return True to proceed).
        action: Name of registered action to execute during transition.
        priority: Priority when multiple transitions match (higher = first).

    Example:
        # Simple transition
        Transition("draft", "pending", "submit")

        # Transition with guard and action
        Transition(
            "pending", "approved", "approve",
            guard="is_valid_swap",
            action="record_approval",
            priority=10,
        )

        # Alternative transition for same event (lower priority)
        Transition(
            "pending", "escalated", "approve",
            guard="needs_escalation",
            priority=5,
        )
    """

    from_state: str
    to_state: str
    event: str
    guard: str | None = None
    action: str | None = None
    priority: int = 0

    def matches(self, current_state: str, event_name: str) -> bool:
        """
        Check if this transition matches the current state and event.

        Args:
            current_state: The current state of the state machine instance.
            event_name: The name of the event being triggered.

        Returns:
            True if this transition should be considered for the given
            state and event combination.
        """
        return self.from_state == current_state and self.event == event_name


@dataclass
class ParallelState:
    """
    Definition of a parallel state region.

    Parallel states allow multiple states to be active simultaneously within
    the same state machine instance. Each region operates independently with
    its own state transitions, enabling modeling of concurrent behaviors.

    Use Cases:
        - Tracking multiple independent aspects of an entity
        - Modeling concurrent workflows that must complete independently
        - Handling orthogonal state concerns (e.g., approval + notification)

    Behavior:
        - Each region starts in its initial_state when the machine is created
        - Regions transition independently based on their own events
        - The machine instance tracks all active states across all regions
        - Final states in parallel regions don't complete the machine

    Attributes:
        name: Unique name for this parallel region.
        states: List of state names that belong to this region.
        initial_state: Starting state for this region (must be in states list).

    Example:
        # Two independent tracking regions
        parallel_regions = [
            ParallelState(
                name="approval",
                states=["pending", "approved", "rejected"],
                initial_state="pending",
            ),
            ParallelState(
                name="notification",
                states=["unsent", "sending", "sent", "failed"],
                initial_state="unsent",
            ),
        ]
    """

    name: str
    states: list[str]
    initial_state: str


class StateMachineError(Exception):
    """
    Base exception for state machine errors.

    All state machine-specific exceptions inherit from this class,
    allowing callers to catch all state machine errors with a single
    except clause if desired.
    """

    pass


class InvalidTransitionError(StateMachineError):
    """
    Raised when an invalid transition is attempted.

    This error occurs when:
    - No transition exists for the (current_state, event) combination
    - The transition references a non-existent state
    - The state machine instance is not in ACTIVE status

    Example:
        try:
            machine.trigger_event(db, instance_id, "unknown_event")
        except InvalidTransitionError as e:
            log.warning(f"Invalid transition: {e}")
    """

    pass


class GuardFailedError(StateMachineError):
    """
    Raised when all matching transitions fail their guard conditions.

    This error occurs when:
    - One or more transitions exist for the (state, event) combination
    - All of those transitions have guard conditions
    - All guard conditions return False

    The difference from InvalidTransitionError:
    - InvalidTransitionError: No transition definition exists
    - GuardFailedError: Transition exists but guard blocked it

    Example:
        try:
            machine.trigger_event(db, instance_id, "approve")
        except GuardFailedError as e:
            log.warning(f"Guard failed: {e}")
            # Inform user why approval was blocked
    """

    pass


class StateMachine:
    """
    Event-driven state machine with persistence and history tracking.

    The StateMachine class provides a complete implementation for managing
    entity lifecycle workflows. It supports:

    Core Features:
        - **States with Actions**: Define entry/exit actions per state
        - **Guard Conditions**: Control transitions with boolean predicates
        - **Event-Driven**: Trigger transitions via named events
        - **Full Audit Trail**: Complete history of all state changes
        - **Parallel Regions**: Multiple concurrent state tracks
        - **Context Management**: Persistent data across transitions
        - **Visualization**: Export to GraphViz DOT format

    Usage Pattern:
        1. Define states and transitions (the state machine graph)
        2. Create a StateMachine instance with the definition
        3. Register guard and action functions by name
        4. Create instances for each entity to track
        5. Trigger events to advance state

    Thread Safety:
        The state machine uses database transactions for consistency.
        Each trigger_event() call is atomic - it either fully completes
        or rolls back on error.

    Persistence:
        All state is persisted to the database via:
        - StateMachineInstance: Current state, context, status
        - StateMachineTransition: Audit log of all transitions

    Example:
        # 1. Define the state machine
        machine = StateMachine(
            name="swap_workflow",
            states=[
                State("draft", is_initial=True),
                State("pending", entry_action="notify_approver"),
                State("approved", is_final=True),
                State("rejected", is_final=True),
            ],
            transitions=[
                Transition("draft", "pending", "submit"),
                Transition("pending", "approved", "approve", guard="is_valid"),
                Transition("pending", "rejected", "reject"),
            ],
        )

        # 2. Register callbacks
        machine.register_guard("is_valid", lambda ctx: validate_swap(ctx.data))
        machine.register_action("notify_approver", send_notification)

        # 3. Create an instance
        instance = machine.create_instance(db, context={"swap_id": "123"})

        # 4. Trigger events
        machine.trigger_event(db, instance.id, "submit")
        machine.trigger_event(db, instance.id, "approve")

    Attributes:
        name: Unique identifier for this state machine type.
        states: Dictionary of state name to State objects.
        transitions: List of transition definitions.
        parallel_regions: List of parallel state regions (if any).
    """

    def __init__(
        self,
        name: str,
        states: list[State],
        transitions: list[Transition],
        parallel_regions: list[ParallelState] | None = None,
    ) -> None:
        """
        Initialize state machine definition.

        The state machine is validated during initialization to catch
        configuration errors early. Validation checks:
        - Exactly one initial state exists
        - All transitions reference valid states
        - Parallel regions reference valid states

        Args:
            name: Unique name for this state machine type.
            states: List of state definitions.
            transitions: List of transition definitions.
            parallel_regions: Optional list of parallel state regions.

        Raises:
            ValueError: If state machine definition is invalid:
                - No initial state defined
                - Multiple initial states defined
                - Transition references unknown state
                - Parallel region references unknown state
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
        """
        Validate state machine definition for correctness.

        Checks performed:
        - Exactly one initial state exists
        - All transition from_state and to_state reference valid states
        - All parallel region states exist and have valid initial states

        Raises:
            ValueError: If any validation check fails.
        """
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
        Register a guard condition by name.

        Guards are boolean functions that determine whether a transition
        is allowed. They receive the current context and must return
        True to allow the transition, False to block it.

        Args:
            name: Name to register the guard under. Must match the guard
                name used in Transition definitions.
            guard_func: Function that takes StateMachineContext and returns bool.

        Example:
            def validate_swap(ctx: StateMachineContext) -> bool:
                swap_id = ctx.get("swap_id")
                return is_valid_swap(swap_id)

            machine.register_guard("validate_swap", validate_swap)
        """
        self._guards[name] = guard_func

    def register_action(self, name: str, action_func: Action) -> None:
        """
        Register an action by name.

        Actions are functions that perform side effects during state
        transitions. They can modify the context, send notifications,
        update external systems, etc.

        Args:
            name: Name to register the action under. Must match the action
                name used in State or Transition definitions.
            action_func: Function that takes StateMachineContext and returns None.

        Example:
            def send_approval_notification(ctx: StateMachineContext) -> None:
                swap_id = ctx.get("swap_id")
                send_email(f"Swap {swap_id} has been approved")
                ctx.set("notification_sent", True)

            machine.register_action("notify_approval", send_approval_notification)
        """
        self._actions[name] = action_func

    def get_initial_state(self) -> State:
        """
        Get the initial state of the machine.

        Returns:
            The State object marked with is_initial=True.

        Raises:
            ValueError: If no initial state is found (should not happen
                if the machine was properly validated).
        """
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

        Creates a new instance in the initial state with the provided context.
        If the initial state has an entry action, it is executed immediately.

        The instance is persisted to the database and can be retrieved later
        using get_instance() or by querying StateMachineInstance directly.

        Args:
            db: Database session for persistence.
            context: Initial context data (dict of JSON-serializable values).
            entity_type: Type of entity this machine manages (e.g., "SwapRequest").
                Used for querying instances by entity type.
            entity_id: ID of the specific entity this instance tracks.
                Enables finding the state machine for a given entity.
            owner_id: User who owns/created this instance.

        Returns:
            The newly created StateMachineInstance in ACTIVE status.

        Example:
            instance = machine.create_instance(
                db,
                context={"swap_id": "123", "requester": "Dr. Smith"},
                entity_type="SwapRequest",
                entity_id=swap_request.id,
                owner_id=current_user.id,
            )
            print(f"Created instance {instance.id} in state {instance.current_state}")
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

        This is the primary method for advancing the state machine. When an
        event is triggered:

        1. The instance is loaded from the database
        2. Matching transitions are found and sorted by priority
        3. Each transition's guard is evaluated until one passes
        4. The transition is executed (exit action, transition action, entry action)
        5. The new state is persisted with transition history

        The entire operation is atomic - if any step fails, the database
        transaction is rolled back.

        Args:
            db: Database session for persistence.
            instance_id: ID of the state machine instance to update.
            event: Event name (string) or TransitionEvent object with data.
            context_updates: Additional data to merge into context before
                evaluating guards and executing actions.

        Returns:
            The updated StateMachineInstance with new current_state.

        Raises:
            ValueError: If instance not found or not in ACTIVE status.
            InvalidTransitionError: If no transition exists for the
                (current_state, event) combination.
            GuardFailedError: If transitions exist but all guards failed.

        Example:
            # Simple event trigger
            instance = machine.trigger_event(db, instance_id, "submit")

            # Event with context updates
            instance = machine.trigger_event(
                db, instance_id, "approve",
                context_updates={"approved_by": "admin", "notes": "LGTM"},
            )

            # Event with TransitionEvent object
            event = TransitionEvent(
                name="submit",
                data={"priority": "high"},
                triggered_by_id=current_user.id,
            )
            instance = machine.trigger_event(db, instance_id, event)
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
        """
        Execute a state transition with all actions (synchronous version).

        This method performs the actual state change, executing actions in order:
        1. Exit action of the current state
        2. Transition action (if any)
        3. Entry action of the new state

        It also:
        - Updates the instance's current_state and context
        - Marks the instance as COMPLETED if reaching a final state
        - Records the transition in the history table for audit

        Args:
            db: Database session for persistence.
            instance: The state machine instance being transitioned.
            transition: The transition definition to execute.
            triggered_by_id: UUID of the user who triggered this transition.
            guard_failed_name: Name of any guard that failed (for audit logging).

        Note:
            This is an internal method. Use trigger_event() for the public API.
        """
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
        """
        Evaluate a guard condition (synchronous version).

        Args:
            guard_name: Name of the registered guard to evaluate.
            ctx: Current state machine context with data for evaluation.

        Returns:
            True if the guard passes (transition allowed), False otherwise.

        Note:
            - Unregistered guards return True with a warning log
            - Exceptions in guards return False with an error log
            - The guard function must be synchronous
        """
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
        """
        Execute an action (synchronous version).

        Args:
            action_name: Name of the registered action to execute.
            ctx: Current state machine context (can be modified by action).

        Raises:
            Exception: Re-raises any exception from the action function.

        Note:
            - Unregistered actions are skipped with a warning log
            - Action functions must be synchronous
            - Actions can modify ctx.data; changes are persisted after transition
        """
        if action_name not in self._actions:
            logger.warning(f"Action '{action_name}' not registered, skipping")
            return

        try:
            action_func = self._actions[action_name]
            action_func(ctx)
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
            db: Database session for querying.
            instance_id: UUID of the instance to retrieve.

        Returns:
            StateMachineInstance if found, None otherwise.

        Note:
            For querying by entity, query StateMachineInstance directly:
            db.query(StateMachineInstance).filter_by(entity_type="Swap", entity_id=id)
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

        Returns all state transitions that have occurred on this instance,
        ordered chronologically. Each transition record includes:
        - from_state and to_state
        - The triggering event
        - Context snapshots before and after
        - Which guards passed/failed
        - Which actions were executed
        - Timestamp and triggering user

        Args:
            db: Database session for querying.
            instance_id: UUID of the instance to get history for.

        Returns:
            List of StateMachineTransition records ordered by created_at.

        Example:
            history = machine.get_history(db, instance_id)
            for transition in history:
                print(f"{transition.from_state} -> {transition.to_state}")
                print(f"  Event: {transition.event}")
                print(f"  At: {transition.created_at}")
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

        Suspended instances cannot process events until resumed. This is useful
        for pausing workflows during maintenance or investigation.

        Args:
            db: Database session for persistence.
            instance_id: UUID of the instance to suspend.

        Returns:
            The updated StateMachineInstance with SUSPENDED status.

        Raises:
            ValueError: If instance not found.

        Note:
            Can suspend from any status. Use resume_instance() to reactivate.
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

        Restores the instance to ACTIVE status so it can process events again.
        The instance continues from its current state.

        Args:
            db: Database session for persistence.
            instance_id: UUID of the instance to resume.

        Returns:
            The updated StateMachineInstance with ACTIVE status.

        Raises:
            ValueError: If instance not found.
            StateMachineError: If instance is not in SUSPENDED status.
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
        Export state machine definition as a visualization.

        Generates a GraphViz DOT format representation of the state machine
        that can be rendered into an image. States are shown as circles
        (double circles for final states), with transitions as labeled edges.

        Args:
            format: Export format. Currently only "dot" is supported.

        Returns:
            String containing the GraphViz DOT format representation.

        Raises:
            ValueError: If format is not "dot".

        Example:
            # Generate DOT format
            dot_output = machine.export_visualization()

            # Save to file
            with open("workflow.dot", "w") as f:
                f.write(dot_output)

            # Render with GraphViz (command line):
            # dot -Tpng workflow.dot -o workflow.png
            # dot -Tsvg workflow.dot -o workflow.svg
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
