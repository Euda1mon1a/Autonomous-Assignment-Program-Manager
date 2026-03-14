"""Pydantic schemas for task history learning system."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


# =============================================================================
# Request Schemas
# =============================================================================


class TaskHistoryCreate(BaseModel):
    """Request to log a completed task."""

    task_description: str = Field(
        ...,
        min_length=1,
        description="Description of the task that was attempted",
    )
    agent_used: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Agent that performed the task",
    )
    model_used: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="Model tier used: haiku, sonnet, opus",
    )
    success: bool = Field(
        ...,
        description="Whether the task completed successfully",
    )
    duration_ms: int | None = Field(
        default=None,
        ge=0,
        description="Task duration in milliseconds",
    )
    session_id: str | None = Field(
        default=None,
        max_length=200,
        description="Session ID for episodic grouping",
    )
    notes: str | None = Field(
        default=None,
        description="Free-text lesson learned",
    )
    failure_reason: str | None = Field(
        default=None,
        max_length=200,
        description="Failure category (schema_error, import_error, etc.)",
    )
    tags: list[str] | None = Field(
        default=None,
        description='Domain tags: ["scheduling", "hda", "constraints"]',
    )
    files_touched: list[str] | None = Field(
        default=None,
        description='Files involved: ["backend/app/scheduling/engine.py"]',
    )


class TaskHistorySearchRequest(BaseModel):
    """Request to search similar past tasks via vector similarity."""

    query: str = Field(
        ...,
        min_length=1,
        description="Search query (will be embedded for similarity search)",
    )
    top_k: int = Field(
        default=5,
        ge=1,
        le=50,
        description="Maximum number of results",
    )
    success_filter: bool | None = Field(
        default=None,
        description="Filter by success/failure (None = both)",
    )
    tags_filter: list[str] | None = Field(
        default=None,
        description="Filter to tasks matching any of these tags",
    )
    min_similarity: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Minimum cosine similarity threshold",
    )


# =============================================================================
# Response Schemas
# =============================================================================


class TaskHistoryResponse(BaseModel):
    """Single task history entry."""

    id: int
    task_description: str
    agent_used: str
    model_used: str
    success: bool
    duration_ms: int | None = None
    session_id: str | None = None
    notes: str | None = None
    failure_reason: str | None = None
    tags: list[str] | None = None
    files_touched: list[str] | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TaskHistorySimilarResult(BaseModel):
    """Task history entry with similarity score."""

    id: int
    task_description: str
    agent_used: str
    model_used: str
    success: bool
    duration_ms: int | None = None
    session_id: str | None = None
    notes: str | None = None
    failure_reason: str | None = None
    tags: list[str] | None = None
    files_touched: list[str] | None = None
    created_at: datetime
    similarity_score: float = Field(ge=0.0, le=1.0)

    model_config = ConfigDict(from_attributes=True)


class TaskHistorySearchResponse(BaseModel):
    """Response from similarity search."""

    query: str
    results: list[TaskHistorySimilarResult]
    total_results: int


class TaskHistorySessionResponse(BaseModel):
    """All tasks from a single session."""

    session_id: str
    tasks: list[TaskHistoryResponse]
    total_tasks: int
