"""Pydantic models for K2.5 swarm integration."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class K2SwarmSpawnRequest(BaseModel):
    """Request to spawn a K2.5 swarm task."""

    task: str = Field(..., description="Task description for swarm")
    mode: Literal["agent", "agent_swarm"] = Field(
        default="agent_swarm",
        description="K2.5 mode (agent=single, agent_swarm=100 agents)",
    )
    context_files: list[str] = Field(
        default_factory=list,
        description="File paths to include as context",
    )
    max_tokens: int = Field(
        default=32000,
        description="Max output tokens",
    )
    output_format: Literal["patches", "files", "analysis"] = Field(
        default="patches",
        description="How to return results",
    )


class FilePatch(BaseModel):
    """A file modification as a unified diff."""

    filepath: str
    diff: str
    description: str = ""


class K2SwarmOutput(BaseModel):
    """Output from a completed swarm task."""

    patches: list[FilePatch] | None = None
    files: dict[str, str] | None = None
    analysis: str | None = None
    tool_calls: int = 0
    agents_used: int = 0
    execution_time_seconds: float = 0.0


class K2SwarmSpawnResponse(BaseModel):
    """Response from spawning a swarm task."""

    success: bool
    task_id: str
    message: str
    estimated_completion: datetime | None = None


class K2SwarmResultResponse(BaseModel):
    """Response from polling a swarm task."""

    success: bool
    status: Literal["pending", "running", "completed", "failed"]
    progress: float = 0.0
    result: K2SwarmOutput | None = None
    error: str | None = None


class K2SwarmApplyRequest(BaseModel):
    """Request to apply patches from a swarm result."""

    task_id: str
    patch_indices: list[int] | None = Field(
        default=None,
        description="Specific patches to apply (None=all)",
    )
    dry_run: bool = Field(
        default=True,
        description="Preview changes without applying",
    )
