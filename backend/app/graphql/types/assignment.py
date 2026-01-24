"""GraphQL types for Assignment entity."""

from datetime import datetime
from enum import Enum
from typing import Any

import strawberry
from strawberry.scalars import JSON


@strawberry.enum
class AssignmentRole(str, Enum):
    """Assignment role types."""

    PRIMARY = "primary"
    SUPERVISING = "supervising"
    BACKUP = "backup"


@strawberry.type
class Assignment:
    """Assignment GraphQL type."""

    id: strawberry.ID
    block_id: strawberry.ID
    person_id: strawberry.ID
    rotation_template_id: strawberry.ID | None = None
    role: AssignmentRole
    activity_override: str | None = None
    notes: str | None = None
    override_reason: str | None = None
    override_acknowledged_at: datetime | None = None
    confidence: float | None = None
    score: float | None = None
    explain_json: JSON | None = None
    alternatives_json: JSON | None = None
    audit_hash: str | None = None
    created_by: str | None = None
    created_at: datetime
    updated_at: datetime

    @strawberry.field
    def activity_name(self) -> str:
        """Get the activity name (override or template name)."""
        if self.activity_override:
            return self.activity_override
        return "Unassigned"

    @strawberry.field
    def confidence_level(self) -> str | None:
        """Get confidence level as high/medium/low."""
        if self.confidence is None:
            return None
        if self.confidence >= 0.8:
            return "high"
        elif self.confidence >= 0.5:
            return "medium"
        else:
            return "low"


@strawberry.input
class AssignmentCreateInput:
    """Input type for creating an assignment."""

    block_id: strawberry.ID
    person_id: strawberry.ID
    rotation_template_id: strawberry.ID | None = None
    role: AssignmentRole
    activity_override: str | None = None
    notes: str | None = None
    override_reason: str | None = None


@strawberry.input
class AssignmentUpdateInput:
    """Input type for updating an assignment."""

    rotation_template_id: strawberry.ID | None = None
    role: AssignmentRole | None = None
    activity_override: str | None = None
    notes: str | None = None
    override_reason: str | None = None
    acknowledge_override: bool | None = None


@strawberry.input
class AssignmentFilterInput:
    """Filter input for querying assignments."""

    person_id: strawberry.ID | None = None
    block_id: strawberry.ID | None = None
    rotation_template_id: strawberry.ID | None = None
    role: AssignmentRole | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None


@strawberry.type
class AssignmentConnection:
    """Paginated assignment results."""

    items: list[Assignment]
    total: int
    has_next_page: bool
    has_previous_page: bool


@strawberry.type
class AssignmentWithWarnings:
    """Assignment with ACGME compliance warnings."""

    assignment: Assignment
    acgme_warnings: list[str]
    is_compliant: bool


def assignment_from_db(db_assignment: Any) -> Assignment:
    """Convert database Assignment model to GraphQL type."""
    return Assignment(  # type: ignore[call-arg]
        id=strawberry.ID(str(db_assignment.id)),
        block_id=strawberry.ID(str(db_assignment.block_id)),
        person_id=strawberry.ID(str(db_assignment.person_id)),
        rotation_template_id=(
            strawberry.ID(str(db_assignment.rotation_template_id))
            if db_assignment.rotation_template_id
            else None
        ),
        role=AssignmentRole(db_assignment.role),
        activity_override=db_assignment.activity_override,
        notes=db_assignment.notes,
        override_reason=db_assignment.override_reason,
        override_acknowledged_at=db_assignment.override_acknowledged_at,
        confidence=db_assignment.confidence,
        score=db_assignment.score,
        explain_json=db_assignment.explain_json,
        alternatives_json=db_assignment.alternatives_json,
        audit_hash=db_assignment.audit_hash,
        created_by=db_assignment.created_by,
        created_at=db_assignment.created_at,
        updated_at=db_assignment.updated_at,
    )
