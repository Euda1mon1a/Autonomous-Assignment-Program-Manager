"""GraphQL types for Assignment entity."""
from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID

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
    rotation_template_id: Optional[strawberry.ID] = None
    role: AssignmentRole
    activity_override: Optional[str] = None
    notes: Optional[str] = None
    override_reason: Optional[str] = None
    override_acknowledged_at: Optional[datetime] = None
    confidence: Optional[float] = None
    score: Optional[float] = None
    explain_json: Optional[JSON] = None
    alternatives_json: Optional[JSON] = None
    audit_hash: Optional[str] = None
    created_by: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    @strawberry.field
    def activity_name(self) -> str:
        """Get the activity name (override or template name)."""
        if self.activity_override:
            return self.activity_override
        return "Unassigned"

    @strawberry.field
    def confidence_level(self) -> Optional[str]:
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
    rotation_template_id: Optional[strawberry.ID] = None
    role: AssignmentRole
    activity_override: Optional[str] = None
    notes: Optional[str] = None
    override_reason: Optional[str] = None


@strawberry.input
class AssignmentUpdateInput:
    """Input type for updating an assignment."""
    rotation_template_id: Optional[strawberry.ID] = None
    role: Optional[AssignmentRole] = None
    activity_override: Optional[str] = None
    notes: Optional[str] = None
    override_reason: Optional[str] = None
    acknowledge_override: Optional[bool] = None


@strawberry.input
class AssignmentFilterInput:
    """Filter input for querying assignments."""
    person_id: Optional[strawberry.ID] = None
    block_id: Optional[strawberry.ID] = None
    rotation_template_id: Optional[strawberry.ID] = None
    role: Optional[AssignmentRole] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


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


def assignment_from_db(db_assignment) -> Assignment:
    """Convert database Assignment model to GraphQL type."""
    return Assignment(
        id=strawberry.ID(str(db_assignment.id)),
        block_id=strawberry.ID(str(db_assignment.block_id)),
        person_id=strawberry.ID(str(db_assignment.person_id)),
        rotation_template_id=strawberry.ID(str(db_assignment.rotation_template_id)) if db_assignment.rotation_template_id else None,
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
