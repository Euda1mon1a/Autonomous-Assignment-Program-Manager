"""WebSocket event types and schemas for real-time updates."""

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class EventType(str, Enum):
    """WebSocket event types."""

    SCHEDULE_UPDATED = "schedule_updated"
    ASSIGNMENT_CHANGED = "assignment_changed"
    SWAP_REQUESTED = "swap_requested"
    SWAP_APPROVED = "swap_approved"
    CONFLICT_DETECTED = "conflict_detected"
    RESILIENCE_ALERT = "resilience_alert"
    CONNECTION_ACK = "connection_ack"
    PING = "ping"
    PONG = "pong"
    # Real-time solver visualization events
    SOLVER_SOLUTION = "solver_solution"
    SOLVER_COMPLETE = "solver_complete"


class WebSocketEventBase(BaseModel):
    """
    Base class for all WebSocket events.

    Automatically serializes all fields to camelCase for frontend compatibility.
    This ensures WS messages follow the same convention as REST API responses
    (which use axios interceptor for snake_case -> camelCase conversion).
    """

    model_config = ConfigDict(
        # Automatically generate camelCase aliases for all fields
        alias_generator=to_camel,
        # Allow both snake_case and camelCase on input
        populate_by_name=True,
        # Use enum values (not enum names) in serialization
        use_enum_values=True,
    )


class WebSocketEvent(WebSocketEventBase):
    """Generic WebSocket event with data payload."""

    event_type: EventType
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    data: dict[str, Any] = Field(default_factory=dict)


class ScheduleUpdatedEvent(WebSocketEventBase):
    """Event for schedule updates."""

    event_type: EventType = EventType.SCHEDULE_UPDATED
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    schedule_id: UUID | None = None
    academic_year_id: UUID | None = None
    user_id: UUID | None = None
    update_type: str  # "generated", "modified", "regenerated"
    affected_blocks_count: int = 0
    message: str = ""


class AssignmentChangedEvent(WebSocketEventBase):
    """Event for assignment changes."""

    event_type: EventType = EventType.ASSIGNMENT_CHANGED
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    assignment_id: UUID
    person_id: UUID
    block_id: UUID
    rotation_template_id: UUID | None = None
    change_type: str  # "created", "updated", "deleted"
    changed_by: UUID | None = None
    message: str = ""


class SwapRequestedEvent(WebSocketEventBase):
    """Event for swap requests."""

    event_type: EventType = EventType.SWAP_REQUESTED
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    swap_id: UUID
    requester_id: UUID
    target_person_id: UUID | None = None
    swap_type: str  # "one_to_one", "absorb"
    affected_assignments: list[UUID] = Field(default_factory=list)
    message: str = ""


class SwapApprovedEvent(WebSocketEventBase):
    """Event for swap approvals."""

    event_type: EventType = EventType.SWAP_APPROVED
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    swap_id: UUID
    requester_id: UUID
    target_person_id: UUID | None = None
    approved_by: UUID
    affected_assignments: list[UUID] = Field(default_factory=list)
    message: str = ""


class ConflictDetectedEvent(WebSocketEventBase):
    """Event for conflict detection."""

    event_type: EventType = EventType.CONFLICT_DETECTED
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    conflict_id: UUID | None = None
    person_id: UUID
    conflict_type: str  # "double_booking", "acgme_violation", "absence_overlap"
    severity: str  # "low", "medium", "high", "critical"
    affected_blocks: list[UUID] = Field(default_factory=list)
    message: str = ""


class ResilienceAlertEvent(WebSocketEventBase):
    """Event for resilience system alerts."""

    event_type: EventType = EventType.RESILIENCE_ALERT
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    alert_type: (
        str  # "utilization_high", "n1_failure", "n2_failure", "defense_level_change"
    )
    severity: str  # "green", "yellow", "orange", "red", "black"
    current_utilization: float | None = None
    defense_level: str | None = None
    affected_persons: list[UUID] = Field(default_factory=list)
    message: str = ""
    recommendations: list[str] = Field(default_factory=list)


class ConnectionAckEvent(WebSocketEventBase):
    """Event acknowledging successful connection."""

    event_type: EventType = EventType.CONNECTION_ACK
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    user_id: UUID
    message: str = "Connection established"


class PingEvent(WebSocketEventBase):
    """Ping event for keepalive."""

    event_type: EventType = EventType.PING
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class PongEvent(WebSocketEventBase):
    """Pong event response to ping."""

    event_type: EventType = EventType.PONG
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# =============================================================================
# Real-Time Solver Visualization Events
# =============================================================================


class SolverAssignment(WebSocketEventBase):
    """Single assignment from solver."""

    person_id: str
    block_id: str
    template_id: str
    r_idx: int | None = None  # Resident index for position calculation
    b_idx: int | None = None  # Block index for position calculation
    t_idx: int | None = None  # Template index for layer calculation


class SolverDelta(WebSocketEventBase):
    """Delta between consecutive solver solutions."""

    added: list[SolverAssignment] = Field(default_factory=list)
    removed: list[SolverAssignment] = Field(default_factory=list)
    moved: list[dict[str, str]] = Field(
        default_factory=list
    )  # {person_id, block_id, old_template_id, new_template_id}


class SolverSolutionEvent(WebSocketEventBase):
    """
    Event fired when CP-SAT solver finds a new feasible solution.

    This enables real-time visualization of the solver progress,
    showing voxels rearranging as better solutions are discovered.

    For the first solution, `solution_type` is "full" and `assignments`
    contains the complete assignment list.

    For subsequent solutions, `solution_type` is "delta" and `delta`
    contains only the changes from the previous solution.
    """

    event_type: EventType = EventType.SOLVER_SOLUTION
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    # Task identification
    task_id: str
    solution_num: int

    # Solution data
    solution_type: str  # "full" or "delta"
    assignments: list[SolverAssignment] | None = None  # For full solutions
    delta: SolverDelta | None = None  # For delta solutions

    # Metrics
    assignment_count: int
    objective_value: float
    optimality_gap_pct: float
    is_optimal: bool = False
    elapsed_seconds: float


class SolverCompleteEvent(WebSocketEventBase):
    """
    Event fired when solver completes (optimal, timeout, or error).

    Indicates the final state of the schedule generation process.
    """

    event_type: EventType = EventType.SOLVER_COMPLETE
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    # Task identification
    task_id: str

    # Completion status
    status: str  # "optimal", "feasible", "timeout", "infeasible", "error"
    total_solutions: int
    final_assignment_count: int
    total_elapsed_seconds: float
    message: str = ""
