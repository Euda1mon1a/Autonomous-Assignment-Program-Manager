"""Cascade override schemas for deployment-style coverage changes."""

from datetime import date
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


class CascadeOverrideRequest(BaseModel):
    """Request a cascade plan for a deployed person."""

    person_id: UUID = Field(..., description="Deployed person ID")
    start_date: date = Field(..., description="Start date (inclusive)")
    end_date: date = Field(..., description="End date (inclusive)")
    reason: str | None = Field(
        None, description="Reason for override (deployment, sick)"
    )
    notes: str | None = Field(None, description="Optional notes")
    apply: bool = Field(False, description="Apply overrides if true; otherwise dry-run")
    max_depth: int = Field(2, ge=1, le=2, description="Cascade depth (max 2)")


class CascadeOverrideStep(BaseModel):
    """Single step in a cascade plan."""

    target_type: Literal["half_day", "call"]
    assignment_id: UUID
    override_type: Literal["coverage", "cancellation", "gap"]
    replacement_person_id: UUID | None = None
    reason: str | None = None
    notes: str | None = None
    score: float | None = None
    warnings: list[str] = []
    created_override_id: UUID | None = None


class CascadeOverridePlanResponse(BaseModel):
    """Response for a cascade plan."""

    person_id: UUID
    start_date: date
    end_date: date
    applied: bool
    steps: list[CascadeOverrideStep]
    warnings: list[str] = []
    errors: list[str] = []
