"""Pydantic schemas for the Annual Rotation Optimizer."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


# ── Request Schemas ──────────────────────────────────────────────────────────


class AnnualRotationPlanCreate(BaseModel):
    """Request to create a new annual rotation plan."""

    academic_year: int = Field(
        ge=2020, le=2100, description="Academic year (e.g. 2026)"
    )
    name: str = Field(max_length=200, description="Plan name")
    solver_time_limit: float = Field(
        default=30.0,
        ge=1.0,
        le=300.0,
        description="Solver time limit in seconds",
    )


class OptimizeRequest(BaseModel):
    """Request to run the optimizer on an existing plan."""

    solver_time_limit: float | None = Field(
        default=None,
        ge=1.0,
        le=300.0,
        description="Override solver time limit (seconds)",
    )


# ── Response Schemas ─────────────────────────────────────────────────────────


class AnnualRotationAssignmentResponse(BaseModel):
    """A single rotation assignment in a plan."""

    id: UUID
    person_id: UUID
    block_number: int
    rotation_name: str
    is_fixed: bool

    model_config = ConfigDict(from_attributes=True)


class AnnualRotationPlanResponse(BaseModel):
    """Full plan response with assignments."""

    id: UUID
    academic_year: int
    name: str
    status: str
    solver_time_limit: float | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    created_by: UUID | None = None
    objective_value: int | None = None
    solver_status: str | None = None
    solve_duration_ms: int | None = None
    assignments: list[AnnualRotationAssignmentResponse] = []

    model_config = ConfigDict(from_attributes=True)


class AnnualRotationPlanSummary(BaseModel):
    """Lightweight plan summary for list endpoints."""

    id: UUID
    academic_year: int
    name: str
    status: str
    solver_status: str | None = None
    objective_value: int | None = None
    solve_duration_ms: int | None = None
    created_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class OptimizeResponse(BaseModel):
    """Response from the optimize endpoint."""

    status: str
    solver_status: str
    objective_value: int | None = None
    solve_duration_ms: int | None = None
    leave_satisfied: int = 0
    leave_total: int = 0
    total_assignments: int = 0
    plan: AnnualRotationPlanResponse
