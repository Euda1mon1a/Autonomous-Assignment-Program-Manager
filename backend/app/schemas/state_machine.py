"""Pydantic schemas for state machine API."""

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class StateMachineStatusSchema(str, Enum):
    """Status of a state machine instance."""

    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED = "failed"
    SUSPENDED = "suspended"


class StateDefinition(BaseModel):
    """Definition of a state in the state machine."""

    name: str = Field(..., description="Unique name of the state")
    is_initial: bool = Field(False, description="Whether this is the initial state")
    is_final: bool = Field(False, description="Whether this is a final state")
    entry_action: str | None = Field(None, description="Action to execute on entry")
    exit_action: str | None = Field(None, description="Action to execute on exit")
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional state metadata"
    )


class TransitionDefinition(BaseModel):
    """Definition of a transition between states."""

    from_state: str = Field(..., description="Source state")
    to_state: str = Field(..., description="Destination state")
    event: str = Field(..., description="Event that triggers this transition")
    guard: str | None = Field(None, description="Guard condition to evaluate")
    action: str | None = Field(None, description="Action to execute during transition")
    priority: int = Field(
        0, description="Priority when multiple transitions match (higher wins)"
    )


class ParallelStateDefinition(BaseModel):
    """Definition of parallel states that can be active simultaneously."""

    name: str = Field(..., description="Name of the parallel region")
    states: list[str] = Field(..., description="List of states in this parallel region")
    initial_state: str = Field(..., description="Initial state for this region")


class StateMachineDefinition(BaseModel):
    """Complete definition of a state machine."""

    name: str = Field(..., description="Unique name of the state machine")
    states: list[StateDefinition] = Field(..., description="All states in the machine")
    transitions: list[TransitionDefinition] = Field(..., description="All transitions")
    parallel_regions: list[ParallelStateDefinition] = Field(
        default_factory=list, description="Parallel state regions"
    )
    initial_context: dict[str, Any] = Field(
        default_factory=dict, description="Initial context data"
    )


class StateMachineCreateRequest(BaseModel):
    """Request to create a new state machine instance."""

    machine_name: str = Field(..., description="Name of the machine definition to use")
    initial_context: dict[str, Any] = Field(
        default_factory=dict, description="Initial context data"
    )
    entity_type: str | None = Field(
        None, description="Type of entity this machine manages"
    )
    entity_id: UUID | None = Field(
        None, description="ID of entity this machine manages"
    )


class TransitionRequest(BaseModel):
    """Request to trigger a state transition."""

    event: str = Field(..., description="Event to trigger")
    context_updates: dict[str, Any] = Field(
        default_factory=dict, description="Updates to merge into context"
    )


class StateMachineInstanceResponse(BaseModel):
    """Response containing state machine instance data."""

    id: UUID
    machine_name: str
    current_state: str
    parallel_states: list[dict[str, str]]
    status: StateMachineStatusSchema
    context: dict[str, Any]
    entity_type: str | None
    entity_id: UUID | None
    owner_id: UUID | None
    error_message: str | None
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None

    class Config:
        from_attributes = True


class StateMachineTransitionResponse(BaseModel):
    """Response containing transition history entry."""

    id: UUID
    instance_id: UUID
    from_state: str
    to_state: str
    event: str
    guard_passed: str | None
    guard_failed: str | None
    entry_action: str | None
    exit_action: str | None
    transition_action: str | None
    context_before: dict[str, Any] | None
    context_after: dict[str, Any] | None
    triggered_by_id: UUID | None
    error_message: str | None
    created_at: datetime

    class Config:
        from_attributes = True


class StateMachineHistoryResponse(BaseModel):
    """Response containing full history of a state machine instance."""

    instance: StateMachineInstanceResponse
    transitions: list[StateMachineTransitionResponse]


class StateMachineVisualization(BaseModel):
    """State machine visualization in DOT format."""

    machine_name: str
    dot_graph: str = Field(..., description="GraphViz DOT format representation")
    states_count: int
    transitions_count: int
    has_parallel_regions: bool
