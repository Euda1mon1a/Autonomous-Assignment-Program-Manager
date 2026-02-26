"""Agent matcher API routes.

Provides endpoints for ML-powered agent selection using
semantic similarity matching of task descriptions to agent capabilities.
"""

import dataclasses
import logging

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field

from app.core.security import get_current_active_user
from app.models.user import User
from app.services.agent_matcher import get_agent_matcher

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agent-matcher", tags=["agent-matcher"])


# ---------- Request / Response Schemas ----------


class TaskMatchRequest(BaseModel):
    """Request for matching a task to agents."""

    task: str = Field(..., min_length=3, description="Task description to match")
    top_k: int = Field(
        default=3, ge=1, le=10, description="Number of matches to return"
    )


class AgentMatchResponse(BaseModel):
    """Single agent match result."""

    agent_name: str
    similarity_score: float
    archetype: str
    capabilities: str
    recommended_model: str


class TaskMatchResponse(BaseModel):
    """Response for task matching."""

    task: str
    matches: list[AgentMatchResponse]
    recommendation: str | None = None


class AgentInfo(BaseModel):
    """Basic agent information."""

    name: str
    archetype: str
    capabilities: str


# ---------- Endpoints ----------


@router.post(
    "/match",
    response_model=TaskMatchResponse,
    summary="Match a task to the best agents",
    description=(
        "Use semantic similarity to find the most appropriate agents "
        "for a given task description."
    ),
)
def match_task(
    request: TaskMatchRequest,
    current_user: User = Depends(get_current_active_user),
) -> TaskMatchResponse:
    """Match a task description to the best agents."""
    matcher = get_agent_matcher()
    matches = matcher.match_task(request.task, top_k=request.top_k)

    return TaskMatchResponse(
        task=request.task,
        matches=[AgentMatchResponse(**dataclasses.asdict(m)) for m in matches],
        recommendation=matches[0].agent_name if matches else None,
    )


@router.post(
    "/explain",
    summary="Explain agent matching for a task",
    description=(
        "Get detailed explanation of why agents were matched, "
        "including similarity scores and confidence level."
    ),
)
def explain_match(
    request: TaskMatchRequest,
    current_user: User = Depends(get_current_active_user),
) -> dict:
    """Explain why agents were matched to a task."""
    matcher = get_agent_matcher()
    return matcher.explain_match(request.task)


@router.get(
    "/agents",
    response_model=list[AgentInfo],
    summary="List available agents",
    description="List all loaded agent specifications with their archetypes.",
)
def list_agents(
    current_user: User = Depends(get_current_active_user),
) -> list[AgentInfo]:
    """List all available agents."""
    matcher = get_agent_matcher()
    matcher.load_agents()

    return [
        AgentInfo(
            name=agent.name,
            archetype=agent.archetype,
            capabilities=agent.capabilities[:200]
            if len(agent.capabilities) > 200
            else agent.capabilities,
        )
        for agent in matcher._agents
    ]
