"""Assignment schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class AssignmentBase(BaseModel):
    """Base assignment schema."""

    block_id: UUID
    person_id: UUID
    rotation_template_id: UUID | None = None
    role: str  # 'primary', 'supervising', 'backup'
    activity_override: str | None = None
    notes: str | None = None
    override_reason: str | None = None  # Reason for acknowledging ACGME violations

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str) -> str:
        if v not in ("primary", "supervising", "backup"):
            raise ValueError("role must be 'primary', 'supervising', or 'backup'")
        return v


class AssignmentCreate(AssignmentBase):
    """Schema for creating an assignment."""

    created_by: str | None = None


class AssignmentUpdate(BaseModel):
    """Schema for updating an assignment."""

    rotation_template_id: UUID | None = None
    role: str | None = None
    activity_override: str | None = None
    notes: str | None = None
    override_reason: str | None = None  # Reason for acknowledging ACGME violations
    acknowledge_override: bool | None = (
        None  # Set to True to timestamp override_acknowledged_at
    )
    updated_at: datetime  # Required for optimistic locking

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str | None) -> str | None:
        if v is not None and v not in ("primary", "supervising", "backup"):
            raise ValueError("role must be 'primary', 'supervising', or 'backup'")
        return v


class AssignmentResponse(AssignmentBase):
    """Schema for assignment response."""

    id: UUID
    created_by: str | None = None
    created_at: datetime
    updated_at: datetime
    override_acknowledged_at: datetime | None = (
        None  # When ACGME violation was acknowledged
    )

    # Explainability fields
    confidence: float | None = Field(
        None, description="Confidence score 0-1 for this assignment"
    )
    score: float | None = Field(None, description="Objective score for this assignment")

    class Config:
        from_attributes = True


class AssignmentWithWarnings(AssignmentResponse):
    """Schema for assignment response with ACGME validation warnings."""

    acgme_warnings: list[str] = []
    is_compliant: bool = True


class AssignmentWithExplanation(AssignmentResponse):
    """Schema for assignment response with full decision explanation."""

    explain_json: dict | None = Field(
        None, description="Full decision explanation JSON"
    )
    alternatives_json: list[dict] | None = Field(
        None, description="Top alternatives considered"
    )
    audit_hash: str | None = Field(
        None, description="SHA-256 hash for integrity verification"
    )

    # Computed explanation summary
    confidence_level: str | None = Field(
        None, description="high/medium/low confidence level"
    )
    trade_off_summary: str | None = Field(
        None, description="Plain-English trade-off explanation"
    )

    class Config:
        from_attributes = True

    @classmethod
    def from_assignment(cls, assignment, include_explanation: bool = True):
        """Create from Assignment model with explanation extraction."""
        data = {
            "id": assignment.id,
            "block_id": assignment.block_id,
            "person_id": assignment.person_id,
            "rotation_template_id": assignment.rotation_template_id,
            "role": assignment.role,
            "activity_override": assignment.activity_override,
            "notes": assignment.notes,
            "override_reason": assignment.override_reason,
            "created_by": assignment.created_by,
            "created_at": assignment.created_at,
            "updated_at": assignment.updated_at,
            "override_acknowledged_at": assignment.override_acknowledged_at,
            "confidence": assignment.confidence,
            "score": assignment.score,
        }

        if include_explanation and assignment.explain_json:
            data["explain_json"] = assignment.explain_json
            data["alternatives_json"] = assignment.alternatives_json
            data["audit_hash"] = assignment.audit_hash
            data["confidence_level"] = assignment.explain_json.get("confidence")
            data["trade_off_summary"] = assignment.explain_json.get("trade_off_summary")

        return cls(**data)
