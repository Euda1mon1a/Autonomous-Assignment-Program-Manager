# PEC Operations Design Document

> **Target Audience:** Claude Code CLI
> **Last Updated:** 2026-01-19
> **Status:** Design Sketch — Ready for Implementation

---

## Executive Summary

Program Evaluation Committee (PEC) operations extend this residency scheduler with ACGME-mandated program oversight capabilities. PEC consumes scheduling and evaluation telemetry to enable:

- Block/rotation-level performance aggregation
- Meeting workflow with decision audit trails
- Action item lifecycle management
- Annual program evaluation reporting

This document provides implementation-ready specifications following existing codebase patterns.

---

## 1. Scope Definition

### 1.1 Capability Slices

| Slice | Description | Data Sources |
|-------|-------------|--------------|
| **Performance Views** | Aggregated resident/faculty metrics by rotation, site, block, PGY | Assignments, evaluations, duty hours |
| **Program Outcomes** | Board pass rates, milestone progression, remediation rates | External imports, evaluation aggregates |
| **Meeting Workflow** | Agenda, attendance, decisions, action items | New PEC domain tables |
| **Compliance Reporting** | ACGME annual program evaluation, self-study | All above + compliance engine |

### 1.2 Operational Modes (per CONSTITUTION.md)

```python
class PecOperationMode(str, Enum):
    SAFE_AUDIT = "safe_audit"              # Read-only dashboards
    SUPERVISED_EXECUTION = "supervised"     # AI drafts, human approves
    EXPERIMENTAL_PLANNING = "experimental"  # Simulate curriculum changes
    EMERGENCY_OVERRIDE = "emergency"        # Sentinel event response
```

**Mode → Operation Matrix:**

| Operation | SAFE_AUDIT | SUPERVISED | EXPERIMENTAL | EMERGENCY |
|-----------|------------|------------|--------------|-----------|
| View dashboard | ✓ | ✓ | ✓ | ✓ |
| Create meeting | ✗ | ✓ (approve) | ✗ | ✓ |
| Log decision | ✗ | ✓ (approve) | ✗ | ✓ |
| Close action item | ✗ | ✓ | ✗ | ✓ |
| Generate report | ✓ | ✓ | ✓ | ✓ |
| Simulate changes | ✗ | ✗ | ✓ | ✗ |

---

## 2. Domain Model

### 2.1 Database Tables (SQLAlchemy)

Follow existing patterns from `backend/app/models/`. All models inherit from `Base`, use UUID primary keys, and include audit timestamps.

```python
# backend/app/models/pec.py

from __future__ import annotations
import uuid
from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean, Column, Date, DateTime, Enum, ForeignKey,
    Integer, String, Text, CheckConstraint, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.person import Person
    from app.models.user import User


class PecMeeting(Base):
    """PEC meeting with agenda, attendance, and outcomes."""

    __tablename__ = "pec_meetings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    meeting_date = Column(Date, nullable=False, index=True)
    academic_year = Column(String(10), nullable=False, index=True)  # "AY25-26"
    meeting_type = Column(
        String(30), nullable=False, default="quarterly",
        index=True
    )  # quarterly, annual, special, sentinel
    focus_areas = Column(JSONB, nullable=False, default=list)  # ["PGY-1", "OB Curriculum"]
    status = Column(
        String(20), nullable=False, default="scheduled",
        index=True
    )  # scheduled, in_progress, completed, cancelled
    location = Column(String(255))
    notes = Column(Text)

    # Audit
    created_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    # Relationships
    created_by = relationship("User", foreign_keys=[created_by_id])
    attendance = relationship("PecAttendance", back_populates="meeting", cascade="all, delete-orphan")
    agenda_items = relationship("PecAgendaItem", back_populates="meeting", cascade="all, delete-orphan", order_by="PecAgendaItem.order")
    decisions = relationship("PecDecision", back_populates="meeting", cascade="all, delete-orphan")
    action_items = relationship("PecActionItem", back_populates="meeting", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint(
            "meeting_type IN ('quarterly', 'annual', 'special', 'sentinel')",
            name="check_pec_meeting_type"
        ),
        CheckConstraint(
            "status IN ('scheduled', 'in_progress', 'completed', 'cancelled')",
            name="check_pec_meeting_status"
        ),
    )


class PecAttendance(Base):
    """Meeting attendance record with role."""

    __tablename__ = "pec_attendance"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    meeting_id = Column(UUID(as_uuid=True), ForeignKey("pec_meetings.id", ondelete="CASCADE"), nullable=False)
    person_id = Column(UUID(as_uuid=True), ForeignKey("people.id", ondelete="CASCADE"), nullable=False)
    role = Column(String(30), nullable=False)  # PD, APD, CoreFaculty, ResidentRep, Staff, Guest
    attended = Column(Boolean, nullable=False, default=True)
    notes = Column(String(255))

    # Relationships
    meeting = relationship("PecMeeting", back_populates="attendance")
    person = relationship("Person")

    __table_args__ = (
        UniqueConstraint("meeting_id", "person_id", name="uq_pec_attendance"),
        CheckConstraint(
            "role IN ('PD', 'APD', 'CoreFaculty', 'ResidentRep', 'Staff', 'Guest')",
            name="check_pec_attendance_role"
        ),
    )


class PecAgendaItem(Base):
    """Ordered agenda item with optional data slice reference."""

    __tablename__ = "pec_agenda_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    meeting_id = Column(UUID(as_uuid=True), ForeignKey("pec_meetings.id", ondelete="CASCADE"), nullable=False)
    order = Column(Integer, nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    duration_minutes = Column(Integer, default=15)

    # Data slice reference for analytics linkage
    data_slice_type = Column(String(30))  # RESIDENT_COHORT, ROTATION, SITE, OUTCOME_KPI
    data_slice_key = Column(String(100))  # e.g., rotation_id, site_id

    status = Column(String(20), nullable=False, default="pending")  # pending, discussed, deferred, skipped
    discussion_notes = Column(Text)

    # Relationships
    meeting = relationship("PecMeeting", back_populates="agenda_items")
    decisions = relationship("PecDecision", back_populates="agenda_item")

    __table_args__ = (
        UniqueConstraint("meeting_id", "order", name="uq_pec_agenda_order"),
        CheckConstraint(
            "data_slice_type IS NULL OR data_slice_type IN ('RESIDENT_COHORT', 'ROTATION', 'SITE', 'OUTCOME_KPI', 'FACULTY', 'CURRICULUM')",
            name="check_pec_slice_type"
        ),
    )


class PecDecision(Base):
    """Decision record with evidence linkage and command approval tracking."""

    __tablename__ = "pec_decisions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    meeting_id = Column(UUID(as_uuid=True), ForeignKey("pec_meetings.id", ondelete="CASCADE"), nullable=False)
    agenda_item_id = Column(UUID(as_uuid=True), ForeignKey("pec_agenda_items.id", ondelete="SET NULL"))

    decision_type = Column(String(30), nullable=False)  # ProgramChange, CurriculumChange, PolicyChange, NoChange, Remediation
    summary = Column(String(500), nullable=False)
    rationale = Column(Text, nullable=False)

    # Evidence references (JSONB array of {sourceType, sourceId, hyperlink})
    evidence_refs = Column(JSONB, nullable=False, default=list)

    # Military command approval chain
    requires_command_approval = Column(Boolean, nullable=False, default=False)
    command_disposition = Column(String(20))  # Pending, Approved, Disapproved, Modified
    command_notes = Column(Text)
    command_approved_by = Column(String(100))
    command_approved_at = Column(DateTime)

    # Audit
    created_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    # Relationships
    meeting = relationship("PecMeeting", back_populates="decisions")
    agenda_item = relationship("PecAgendaItem", back_populates="decisions")
    created_by = relationship("User")
    action_items = relationship("PecActionItem", back_populates="decision")

    __table_args__ = (
        CheckConstraint(
            "decision_type IN ('ProgramChange', 'CurriculumChange', 'PolicyChange', 'NoChange', 'Remediation', 'Recognition')",
            name="check_pec_decision_type"
        ),
        CheckConstraint(
            "command_disposition IS NULL OR command_disposition IN ('Pending', 'Approved', 'Disapproved', 'Modified')",
            name="check_pec_command_disposition"
        ),
    )


class PecActionItem(Base):
    """Action item with lifecycle tracking."""

    __tablename__ = "pec_action_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    meeting_id = Column(UUID(as_uuid=True), ForeignKey("pec_meetings.id", ondelete="CASCADE"), nullable=False)
    decision_id = Column(UUID(as_uuid=True), ForeignKey("pec_decisions.id", ondelete="SET NULL"))

    description = Column(String(500), nullable=False)
    owner_person_id = Column(UUID(as_uuid=True), ForeignKey("people.id"), nullable=False)
    due_date = Column(Date)
    priority = Column(String(10), nullable=False, default="medium")  # low, medium, high, critical

    status = Column(String(20), nullable=False, default="open", index=True)  # open, in_progress, completed, deferred, cancelled
    completion_note = Column(Text)
    completed_at = Column(DateTime)

    # Audit
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    # Relationships
    meeting = relationship("PecMeeting", back_populates="action_items")
    decision = relationship("PecDecision", back_populates="action_items")
    owner = relationship("Person")

    __table_args__ = (
        CheckConstraint(
            "priority IN ('low', 'medium', 'high', 'critical')",
            name="check_pec_action_priority"
        ),
        CheckConstraint(
            "status IN ('open', 'in_progress', 'completed', 'deferred', 'cancelled')",
            name="check_pec_action_status"
        ),
    )


class PecEvaluationAggregate(Base):
    """Materialized aggregate for performance analytics."""

    __tablename__ = "pec_evaluation_aggregates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    academic_year = Column(String(10), nullable=False, index=True)
    aggregate_type = Column(String(20), nullable=False)  # resident, rotation, site, cohort
    aggregate_key = Column(UUID(as_uuid=True), nullable=False)  # person_id, rotation_id, etc.

    # Metrics (JSONB for flexibility)
    metrics = Column(JSONB, nullable=False, default=dict)
    # Example: {"meanScore": 3.8, "trajectory": [...], "caseVolume": 120}

    # Flags/concerns
    flags = Column(JSONB, nullable=False, default=list)
    # Example: [{"type": "Remediation", "date": "2026-01-15", "summary": "..."}]

    computed_at = Column(DateTime, nullable=False, server_default=func.now())

    __table_args__ = (
        UniqueConstraint("academic_year", "aggregate_type", "aggregate_key", name="uq_pec_eval_aggregate"),
        CheckConstraint(
            "aggregate_type IN ('resident', 'rotation', 'site', 'cohort', 'faculty')",
            name="check_pec_aggregate_type"
        ),
    )
```

### 2.2 Model Registration

Add to `backend/app/models/__init__.py`:

```python
from app.models.pec import (
    PecMeeting,
    PecAttendance,
    PecAgendaItem,
    PecDecision,
    PecActionItem,
    PecEvaluationAggregate,
)
```

### 2.3 Migration

Create migration: `20260119_add_pec_tables`

```bash
cd backend && alembic revision -m "20260119_add_pec_tables"
```

---

## 3. Pydantic Schemas

Follow existing patterns from `backend/app/schemas/`. Use camelCase aliases for frontend compatibility.

```python
# backend/app/schemas/pec.py

from __future__ import annotations
from datetime import date, datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


# ============ Evidence Reference ============

class EvidenceRef(BaseModel):
    """Reference to supporting evidence for a decision."""
    source_type: Literal[
        "BLOCK_METRICS", "ROTATION_EVALS", "DUTY_HOURS",
        "WELLNESS", "EXAM_SCORES", "INCIDENT_REPORTS", "SCHEDULE"
    ] = Field(..., alias="sourceType")
    source_id: str | None = Field(None, alias="sourceId")
    hyperlink: str | None = None

    model_config = ConfigDict(populate_by_name=True)


# ============ PEC Meeting ============

class PecMeetingBase(BaseModel):
    meeting_date: date = Field(..., alias="meetingDate")
    academic_year: str = Field(..., alias="academicYear", pattern=r"^AY\d{2}-\d{2}$")
    meeting_type: Literal["quarterly", "annual", "special", "sentinel"] = Field(
        "quarterly", alias="meetingType"
    )
    focus_areas: list[str] = Field(default_factory=list, alias="focusAreas")
    location: str | None = None
    notes: str | None = None

    model_config = ConfigDict(populate_by_name=True)


class PecMeetingCreate(PecMeetingBase):
    """Create a new PEC meeting."""
    pass


class PecMeetingUpdate(BaseModel):
    """Update an existing PEC meeting."""
    meeting_date: date | None = Field(None, alias="meetingDate")
    meeting_type: Literal["quarterly", "annual", "special", "sentinel"] | None = Field(
        None, alias="meetingType"
    )
    focus_areas: list[str] | None = Field(None, alias="focusAreas")
    status: Literal["scheduled", "in_progress", "completed", "cancelled"] | None = None
    location: str | None = None
    notes: str | None = None

    model_config = ConfigDict(populate_by_name=True)


class PecMeetingResponse(PecMeetingBase):
    """PEC meeting response with full details."""
    id: UUID
    status: str
    created_by_id: UUID = Field(..., alias="createdById")
    created_at: datetime = Field(..., alias="createdAt")
    updated_at: datetime = Field(..., alias="updatedAt")

    # Counts for list views
    attendance_count: int = Field(0, alias="attendanceCount")
    agenda_item_count: int = Field(0, alias="agendaItemCount")
    decision_count: int = Field(0, alias="decisionCount")
    open_action_count: int = Field(0, alias="openActionCount")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


# ============ Attendance ============

class PecAttendanceCreate(BaseModel):
    person_id: UUID = Field(..., alias="personId")
    role: Literal["PD", "APD", "CoreFaculty", "ResidentRep", "Staff", "Guest"]
    attended: bool = True
    notes: str | None = None

    model_config = ConfigDict(populate_by_name=True)


class PecAttendanceResponse(PecAttendanceCreate):
    id: UUID
    meeting_id: UUID = Field(..., alias="meetingId")
    person_name: str = Field(..., alias="personName")  # Denormalized for display

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


# ============ Agenda Item ============

class DataSliceRef(BaseModel):
    """Reference to a data slice for analytics linkage."""
    type: Literal["RESIDENT_COHORT", "ROTATION", "SITE", "OUTCOME_KPI", "FACULTY", "CURRICULUM"]
    key: str

    model_config = ConfigDict(populate_by_name=True)


class PecAgendaItemCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    duration_minutes: int = Field(15, alias="durationMinutes", ge=5, le=120)
    data_slice: DataSliceRef | None = Field(None, alias="dataSlice")

    model_config = ConfigDict(populate_by_name=True)


class PecAgendaItemUpdate(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    duration_minutes: int | None = Field(None, alias="durationMinutes", ge=5, le=120)
    status: Literal["pending", "discussed", "deferred", "skipped"] | None = None
    discussion_notes: str | None = Field(None, alias="discussionNotes")

    model_config = ConfigDict(populate_by_name=True)


class PecAgendaItemResponse(BaseModel):
    id: UUID
    meeting_id: UUID = Field(..., alias="meetingId")
    order: int
    title: str
    description: str | None
    duration_minutes: int = Field(..., alias="durationMinutes")
    data_slice_type: str | None = Field(None, alias="dataSliceType")
    data_slice_key: str | None = Field(None, alias="dataSliceKey")
    status: str
    discussion_notes: str | None = Field(None, alias="discussionNotes")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


# ============ Decision ============

class PecDecisionCreate(BaseModel):
    agenda_item_id: UUID | None = Field(None, alias="agendaItemId")
    decision_type: Literal[
        "ProgramChange", "CurriculumChange", "PolicyChange",
        "NoChange", "Remediation", "Recognition"
    ] = Field(..., alias="decisionType")
    summary: str = Field(..., min_length=1, max_length=500)
    rationale: str
    evidence_refs: list[EvidenceRef] = Field(default_factory=list, alias="evidenceRefs")
    requires_command_approval: bool = Field(False, alias="requiresCommandApproval")

    model_config = ConfigDict(populate_by_name=True)


class PecDecisionResponse(BaseModel):
    id: UUID
    meeting_id: UUID = Field(..., alias="meetingId")
    agenda_item_id: UUID | None = Field(None, alias="agendaItemId")
    decision_type: str = Field(..., alias="decisionType")
    summary: str
    rationale: str
    evidence_refs: list[EvidenceRef] = Field(..., alias="evidenceRefs")
    requires_command_approval: bool = Field(..., alias="requiresCommandApproval")
    command_disposition: str | None = Field(None, alias="commandDisposition")
    command_notes: str | None = Field(None, alias="commandNotes")
    created_by_id: UUID = Field(..., alias="createdById")
    created_at: datetime = Field(..., alias="createdAt")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


# ============ Action Item ============

class PecActionItemCreate(BaseModel):
    decision_id: UUID | None = Field(None, alias="decisionId")
    description: str = Field(..., min_length=1, max_length=500)
    owner_person_id: UUID = Field(..., alias="ownerPersonId")
    due_date: date | None = Field(None, alias="dueDate")
    priority: Literal["low", "medium", "high", "critical"] = "medium"

    model_config = ConfigDict(populate_by_name=True)


class PecActionItemUpdate(BaseModel):
    description: str | None = Field(None, min_length=1, max_length=500)
    owner_person_id: UUID | None = Field(None, alias="ownerPersonId")
    due_date: date | None = Field(None, alias="dueDate")
    priority: Literal["low", "medium", "high", "critical"] | None = None
    status: Literal["open", "in_progress", "completed", "deferred", "cancelled"] | None = None
    completion_note: str | None = Field(None, alias="completionNote")

    model_config = ConfigDict(populate_by_name=True)


class PecActionItemResponse(BaseModel):
    id: UUID
    meeting_id: UUID = Field(..., alias="meetingId")
    decision_id: UUID | None = Field(None, alias="decisionId")
    description: str
    owner_person_id: UUID = Field(..., alias="ownerPersonId")
    owner_name: str = Field(..., alias="ownerName")  # Denormalized
    due_date: date | None = Field(None, alias="dueDate")
    priority: str
    status: str
    completion_note: str | None = Field(None, alias="completionNote")
    completed_at: datetime | None = Field(None, alias="completedAt")
    created_at: datetime = Field(..., alias="createdAt")
    is_overdue: bool = Field(False, alias="isOverdue")  # Computed

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


# ============ Analytics Slices ============

class MilestoneTrajectory(BaseModel):
    block_id: str = Field(..., alias="blockId")
    level: float

    model_config = ConfigDict(populate_by_name=True)


class ResidentPerformanceSlice(BaseModel):
    """Aggregated resident performance for PEC review."""
    resident_id: UUID = Field(..., alias="residentId")
    resident_name: str = Field(..., alias="residentName")
    pgy_level: int = Field(..., alias="pgyLevel")
    academic_year: str = Field(..., alias="academicYear")
    block_range: dict = Field(..., alias="blockRange")  # {startBlock, endBlock}

    milestones: list[dict] = []  # [{subCompetencyId, meanLevel, trajectory}]
    case_volumes: dict = Field(default_factory=dict, alias="caseVolumes")
    duty_hour_compliance: float = Field(1.0, alias="dutyHourCompliance")

    flags: list[dict] = []  # [{type, date, summary}]
    strengths: list[str] = []
    opportunities: list[str] = []

    model_config = ConfigDict(populate_by_name=True)


class RotationQualitySlice(BaseModel):
    """Rotation-level quality metrics for PEC review."""
    rotation_id: UUID = Field(..., alias="rotationId")
    rotation_name: str = Field(..., alias="rotationName")
    site_id: UUID | None = Field(None, alias="siteId")
    site_name: str | None = Field(None, alias="siteName")
    academic_year: str = Field(..., alias="academicYear")

    resident_eval_mean: float = Field(..., alias="residentEvalMean")
    faculty_eval_mean: float = Field(..., alias="facultyEvalMean")
    case_volume_metrics: dict = Field(default_factory=dict, alias="caseVolumeMetrics")

    narrative_themes: list[str] = Field(default_factory=list, alias="narrativeThemes")
    strengths: list[str] = []
    opportunities: list[str] = []

    model_config = ConfigDict(populate_by_name=True)


# ============ Dashboard ============

class PecDashboardResponse(BaseModel):
    """PEC dashboard aggregate view."""
    academic_year: str = Field(..., alias="academicYear")

    # Summary counts
    total_residents: int = Field(..., alias="totalResidents")
    residents_by_pgy: dict[str, int] = Field(..., alias="residentsByPgy")

    # Key metrics
    board_pass_rate: float | None = Field(None, alias="boardPassRate")
    mean_ite_percentile: float | None = Field(None, alias="meanItePercentile")
    duty_hour_compliance_rate: float = Field(..., alias="dutyHourComplianceRate")

    # Flags
    residents_on_remediation: int = Field(..., alias="residentsOnRemediation")
    wellness_concerns: int = Field(..., alias="wellnessConcerns")
    professionalism_events: int = Field(..., alias="professionalismEvents")

    # Action items
    open_action_items: int = Field(..., alias="openActionItems")
    overdue_action_items: int = Field(..., alias="overdueActionItems")

    # Recent activity
    last_meeting_date: date | None = Field(None, alias="lastMeetingDate")
    next_meeting_date: date | None = Field(None, alias="nextMeetingDate")

    model_config = ConfigDict(populate_by_name=True)
```

---

## 4. Service Layer

Follow existing patterns from `backend/app/services/`. Services orchestrate repositories and contain business logic.

```python
# backend/app/services/pec_service.py

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.pec import (
    PecMeeting, PecAttendance, PecAgendaItem,
    PecDecision, PecActionItem, PecEvaluationAggregate
)
from app.repositories.pec import (
    PecMeetingRepository, PecAttendanceRepository,
    PecAgendaItemRepository, PecDecisionRepository,
    PecActionItemRepository, PecEvaluationAggregateRepository
)
from app.schemas.pec import (
    PecMeetingCreate, PecMeetingUpdate, PecMeetingResponse,
    PecAgendaItemCreate, PecDecisionCreate, PecActionItemCreate,
    PecDashboardResponse, ResidentPerformanceSlice, RotationQualitySlice
)

if TYPE_CHECKING:
    from app.models.user import User


@dataclass
class PecOperationResult:
    """Result wrapper for PEC operations."""
    success: bool
    data: dict | None = None
    message: str = ""
    errors: list[str] = field(default_factory=list)


class PecOperationsService:
    """Orchestrates PEC operations with mode enforcement."""

    def __init__(self, db: Session, current_user: User):
        self.db = db
        self.current_user = current_user

        # Repositories
        self.meeting_repo = PecMeetingRepository(db)
        self.attendance_repo = PecAttendanceRepository(db)
        self.agenda_repo = PecAgendaItemRepository(db)
        self.decision_repo = PecDecisionRepository(db)
        self.action_repo = PecActionItemRepository(db)
        self.aggregate_repo = PecEvaluationAggregateRepository(db)

    # ============ Mode Enforcement ============

    def _check_write_permission(self, operation: str) -> PecOperationResult | None:
        """Check if current mode allows write operations."""
        # TODO: Integrate with CONSTITUTION.md mode system
        # For now, check user role
        allowed_roles = {"admin", "coordinator", "pd", "apd"}
        if self.current_user.role.lower() not in allowed_roles:
            return PecOperationResult(
                success=False,
                message=f"Role '{self.current_user.role}' not authorized for {operation}"
            )
        return None

    # ============ Meeting Operations ============

    def create_meeting(self, data: PecMeetingCreate) -> PecOperationResult:
        """Create a new PEC meeting."""
        if err := self._check_write_permission("create meeting"):
            return err

        meeting = PecMeeting(
            meeting_date=data.meeting_date,
            academic_year=data.academic_year,
            meeting_type=data.meeting_type,
            focus_areas=data.focus_areas,
            location=data.location,
            notes=data.notes,
            created_by_id=self.current_user.id,
        )

        self.meeting_repo.add(meeting)
        self.meeting_repo.commit()
        self.meeting_repo.refresh(meeting)

        return PecOperationResult(
            success=True,
            data={"meeting": meeting},
            message=f"Meeting created for {data.meeting_date}"
        )

    def get_meeting(self, meeting_id: UUID) -> PecMeeting | None:
        """Get meeting with all relationships loaded."""
        return self.meeting_repo.get_with_details(meeting_id)

    def list_meetings(
        self,
        academic_year: str | None = None,
        status: str | None = None,
        limit: int = 50,
        offset: int = 0
    ) -> list[PecMeetingResponse]:
        """List meetings with optional filters."""
        return self.meeting_repo.list_with_filters(
            academic_year=academic_year,
            status=status,
            limit=limit,
            offset=offset
        )

    def update_meeting(
        self, meeting_id: UUID, data: PecMeetingUpdate
    ) -> PecOperationResult:
        """Update meeting details."""
        if err := self._check_write_permission("update meeting"):
            return err

        meeting = self.meeting_repo.get_by_id(meeting_id)
        if not meeting:
            return PecOperationResult(success=False, message="Meeting not found")

        update_data = data.model_dump(exclude_unset=True, by_alias=False)
        for key, value in update_data.items():
            setattr(meeting, key, value)

        self.meeting_repo.commit()
        return PecOperationResult(success=True, data={"meeting": meeting})

    # ============ Agenda Operations ============

    def add_agenda_item(
        self, meeting_id: UUID, data: PecAgendaItemCreate
    ) -> PecOperationResult:
        """Add agenda item to meeting."""
        if err := self._check_write_permission("add agenda item"):
            return err

        # Get next order
        next_order = self.agenda_repo.get_next_order(meeting_id)

        item = PecAgendaItem(
            meeting_id=meeting_id,
            order=next_order,
            title=data.title,
            description=data.description,
            duration_minutes=data.duration_minutes,
            data_slice_type=data.data_slice.type if data.data_slice else None,
            data_slice_key=data.data_slice.key if data.data_slice else None,
        )

        self.agenda_repo.add(item)
        self.agenda_repo.commit()

        return PecOperationResult(success=True, data={"agenda_item": item})

    def reorder_agenda(
        self, meeting_id: UUID, item_ids: list[UUID]
    ) -> PecOperationResult:
        """Reorder agenda items."""
        if err := self._check_write_permission("reorder agenda"):
            return err

        for order, item_id in enumerate(item_ids):
            item = self.agenda_repo.get_by_id(item_id)
            if item and item.meeting_id == meeting_id:
                item.order = order

        self.agenda_repo.commit()
        return PecOperationResult(success=True)

    # ============ Decision Operations ============

    def log_decision(
        self, meeting_id: UUID, data: PecDecisionCreate
    ) -> PecOperationResult:
        """Log a decision from the meeting."""
        if err := self._check_write_permission("log decision"):
            return err

        decision = PecDecision(
            meeting_id=meeting_id,
            agenda_item_id=data.agenda_item_id,
            decision_type=data.decision_type,
            summary=data.summary,
            rationale=data.rationale,
            evidence_refs=[ref.model_dump(by_alias=True) for ref in data.evidence_refs],
            requires_command_approval=data.requires_command_approval,
            command_disposition="Pending" if data.requires_command_approval else None,
            created_by_id=self.current_user.id,
        )

        self.decision_repo.add(decision)
        self.decision_repo.commit()

        return PecOperationResult(success=True, data={"decision": decision})

    # ============ Action Item Operations ============

    def create_action_item(
        self, meeting_id: UUID, data: PecActionItemCreate
    ) -> PecOperationResult:
        """Create an action item."""
        if err := self._check_write_permission("create action item"):
            return err

        action = PecActionItem(
            meeting_id=meeting_id,
            decision_id=data.decision_id,
            description=data.description,
            owner_person_id=data.owner_person_id,
            due_date=data.due_date,
            priority=data.priority,
        )

        self.action_repo.add(action)
        self.action_repo.commit()

        return PecOperationResult(success=True, data={"action_item": action})

    def update_action_status(
        self,
        action_id: UUID,
        status: str,
        completion_note: str | None = None
    ) -> PecOperationResult:
        """Update action item status."""
        if err := self._check_write_permission("update action item"):
            return err

        action = self.action_repo.get_by_id(action_id)
        if not action:
            return PecOperationResult(success=False, message="Action item not found")

        action.status = status
        if status == "completed":
            action.completed_at = datetime.utcnow()
            action.completion_note = completion_note

        self.action_repo.commit()
        return PecOperationResult(success=True, data={"action_item": action})

    def get_open_action_items(
        self,
        owner_person_id: UUID | None = None,
        include_overdue_only: bool = False
    ) -> list[PecActionItem]:
        """Get open action items with optional filters."""
        return self.action_repo.get_open_items(
            owner_person_id=owner_person_id,
            include_overdue_only=include_overdue_only
        )

    # ============ Analytics ============

    def get_dashboard(self, academic_year: str) -> PecDashboardResponse:
        """Get PEC dashboard aggregate data."""
        # Aggregate from multiple sources
        # TODO: Implement aggregation logic
        return PecDashboardResponse(
            academic_year=academic_year,
            total_residents=0,
            residents_by_pgy={},
            duty_hour_compliance_rate=1.0,
            residents_on_remediation=0,
            wellness_concerns=0,
            professionalism_events=0,
            open_action_items=self.action_repo.count_open(),
            overdue_action_items=self.action_repo.count_overdue(),
        )

    def get_resident_slice(
        self, resident_id: UUID, academic_year: str
    ) -> ResidentPerformanceSlice | None:
        """Get aggregated resident performance slice."""
        aggregate = self.aggregate_repo.get_by_key(
            academic_year=academic_year,
            aggregate_type="resident",
            aggregate_key=resident_id
        )
        if not aggregate:
            return None

        # Transform to schema
        return ResidentPerformanceSlice(
            resident_id=resident_id,
            resident_name=aggregate.metrics.get("name", "Unknown"),
            pgy_level=aggregate.metrics.get("pgyLevel", 1),
            academic_year=academic_year,
            block_range=aggregate.metrics.get("blockRange", {}),
            milestones=aggregate.metrics.get("milestones", []),
            case_volumes=aggregate.metrics.get("caseVolumes", {}),
            duty_hour_compliance=aggregate.metrics.get("dutyHourCompliance", 1.0),
            flags=aggregate.flags,
            strengths=aggregate.metrics.get("strengths", []),
            opportunities=aggregate.metrics.get("opportunities", []),
        )

    def get_rotation_slice(
        self, rotation_id: UUID, academic_year: str
    ) -> RotationQualitySlice | None:
        """Get aggregated rotation quality slice."""
        aggregate = self.aggregate_repo.get_by_key(
            academic_year=academic_year,
            aggregate_type="rotation",
            aggregate_key=rotation_id
        )
        if not aggregate:
            return None

        return RotationQualitySlice(
            rotation_id=rotation_id,
            rotation_name=aggregate.metrics.get("name", "Unknown"),
            academic_year=academic_year,
            resident_eval_mean=aggregate.metrics.get("residentEvalMean", 0),
            faculty_eval_mean=aggregate.metrics.get("facultyEvalMean", 0),
            case_volume_metrics=aggregate.metrics.get("caseVolumeMetrics", {}),
            narrative_themes=aggregate.metrics.get("narrativeThemes", []),
            strengths=aggregate.metrics.get("strengths", []),
            opportunities=aggregate.metrics.get("opportunities", []),
        )
```

---

## 5. API Routes

Follow existing patterns from `backend/app/api/routes/`.

```python
# backend/app/api/routes/pec.py

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user, get_db
from app.models.user import User
from app.schemas.pec import (
    PecMeetingCreate, PecMeetingUpdate, PecMeetingResponse,
    PecAgendaItemCreate, PecAgendaItemUpdate, PecAgendaItemResponse,
    PecDecisionCreate, PecDecisionResponse,
    PecActionItemCreate, PecActionItemUpdate, PecActionItemResponse,
    PecDashboardResponse, ResidentPerformanceSlice, RotationQualitySlice,
)
from app.services.pec_service import PecOperationsService

router = APIRouter()


# ============ Dashboard ============

@router.get("/dashboard", response_model=PecDashboardResponse)
async def get_pec_dashboard(
    response: Response,
    academic_year: str = Query(..., alias="academicYear", pattern=r"^AY\d{2}-\d{2}$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> PecDashboardResponse:
    """Get PEC dashboard with aggregate metrics."""
    response.headers["X-Contains-PHI"] = "true"
    service = PecOperationsService(db, current_user)
    return service.get_dashboard(academic_year)


# ============ Meetings ============

@router.get("/meetings", response_model=list[PecMeetingResponse])
async def list_meetings(
    response: Response,
    academic_year: str | None = Query(None, alias="academicYear"),
    status: str | None = None,
    limit: int = Query(50, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> list[PecMeetingResponse]:
    """List PEC meetings with optional filters."""
    response.headers["X-Contains-PHI"] = "true"
    service = PecOperationsService(db, current_user)
    return service.list_meetings(
        academic_year=academic_year,
        status=status,
        limit=limit,
        offset=offset
    )


@router.post("/meetings", response_model=PecMeetingResponse, status_code=201)
async def create_meeting(
    meeting_in: PecMeetingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> PecMeetingResponse:
    """Create a new PEC meeting."""
    service = PecOperationsService(db, current_user)
    result = service.create_meeting(meeting_in)
    if not result.success:
        raise HTTPException(status_code=400, detail=result.message)
    return PecMeetingResponse.model_validate(result.data["meeting"])


@router.get("/meetings/{meeting_id}", response_model=PecMeetingResponse)
async def get_meeting(
    meeting_id: UUID,
    response: Response,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> PecMeetingResponse:
    """Get meeting details with agenda, decisions, and action items."""
    response.headers["X-Contains-PHI"] = "true"
    service = PecOperationsService(db, current_user)
    meeting = service.get_meeting(meeting_id)
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    return PecMeetingResponse.model_validate(meeting)


@router.patch("/meetings/{meeting_id}", response_model=PecMeetingResponse)
async def update_meeting(
    meeting_id: UUID,
    meeting_in: PecMeetingUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> PecMeetingResponse:
    """Update meeting details."""
    service = PecOperationsService(db, current_user)
    result = service.update_meeting(meeting_id, meeting_in)
    if not result.success:
        raise HTTPException(status_code=400, detail=result.message)
    return PecMeetingResponse.model_validate(result.data["meeting"])


# ============ Agenda Items ============

@router.post("/meetings/{meeting_id}/agenda", response_model=PecAgendaItemResponse, status_code=201)
async def add_agenda_item(
    meeting_id: UUID,
    item_in: PecAgendaItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> PecAgendaItemResponse:
    """Add an agenda item to a meeting."""
    service = PecOperationsService(db, current_user)
    result = service.add_agenda_item(meeting_id, item_in)
    if not result.success:
        raise HTTPException(status_code=400, detail=result.message)
    return PecAgendaItemResponse.model_validate(result.data["agenda_item"])


@router.put("/meetings/{meeting_id}/agenda/order")
async def reorder_agenda(
    meeting_id: UUID,
    item_ids: list[UUID],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> dict:
    """Reorder agenda items."""
    service = PecOperationsService(db, current_user)
    result = service.reorder_agenda(meeting_id, item_ids)
    if not result.success:
        raise HTTPException(status_code=400, detail=result.message)
    return {"success": True}


# ============ Decisions ============

@router.post("/meetings/{meeting_id}/decisions", response_model=PecDecisionResponse, status_code=201)
async def log_decision(
    meeting_id: UUID,
    decision_in: PecDecisionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> PecDecisionResponse:
    """Log a decision from the meeting."""
    service = PecOperationsService(db, current_user)
    result = service.log_decision(meeting_id, decision_in)
    if not result.success:
        raise HTTPException(status_code=400, detail=result.message)
    return PecDecisionResponse.model_validate(result.data["decision"])


# ============ Action Items ============

@router.post("/meetings/{meeting_id}/actions", response_model=PecActionItemResponse, status_code=201)
async def create_action_item(
    meeting_id: UUID,
    action_in: PecActionItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> PecActionItemResponse:
    """Create an action item."""
    service = PecOperationsService(db, current_user)
    result = service.create_action_item(meeting_id, action_in)
    if not result.success:
        raise HTTPException(status_code=400, detail=result.message)
    return PecActionItemResponse.model_validate(result.data["action_item"])


@router.get("/actions", response_model=list[PecActionItemResponse])
async def list_action_items(
    response: Response,
    owner_id: UUID | None = Query(None, alias="ownerId"),
    overdue_only: bool = Query(False, alias="overdueOnly"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> list[PecActionItemResponse]:
    """List open action items."""
    response.headers["X-Contains-PHI"] = "true"
    service = PecOperationsService(db, current_user)
    items = service.get_open_action_items(
        owner_person_id=owner_id,
        include_overdue_only=overdue_only
    )
    return [PecActionItemResponse.model_validate(item) for item in items]


@router.patch("/actions/{action_id}/status")
async def update_action_status(
    action_id: UUID,
    status: str = Query(...),
    completion_note: str | None = Query(None, alias="completionNote"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> dict:
    """Update action item status."""
    service = PecOperationsService(db, current_user)
    result = service.update_action_status(action_id, status, completion_note)
    if not result.success:
        raise HTTPException(status_code=400, detail=result.message)
    return {"success": True, "status": status}


# ============ Analytics Slices ============

@router.get("/slices/resident/{resident_id}", response_model=ResidentPerformanceSlice)
async def get_resident_slice(
    resident_id: UUID,
    response: Response,
    academic_year: str = Query(..., alias="academicYear"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> ResidentPerformanceSlice:
    """Get aggregated resident performance slice."""
    response.headers["X-Contains-PHI"] = "true"
    service = PecOperationsService(db, current_user)
    slice_data = service.get_resident_slice(resident_id, academic_year)
    if not slice_data:
        raise HTTPException(status_code=404, detail="Resident slice not found")
    return slice_data


@router.get("/slices/rotation/{rotation_id}", response_model=RotationQualitySlice)
async def get_rotation_slice(
    rotation_id: UUID,
    response: Response,
    academic_year: str = Query(..., alias="academicYear"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> RotationQualitySlice:
    """Get aggregated rotation quality slice."""
    response.headers["X-Contains-PHI"] = "true"
    service = PecOperationsService(db, current_user)
    slice_data = service.get_rotation_slice(rotation_id, academic_year)
    if not slice_data:
        raise HTTPException(status_code=404, detail="Rotation slice not found")
    return slice_data
```

**Route Registration** (add to `backend/app/api/routes/__init__.py`):

```python
from app.api.routes import pec

api_router.include_router(pec.router, prefix="/pec", tags=["pec-operations"])
```

---

## 6. Frontend Implementation

### 6.1 React Query Hooks

```typescript
// frontend/src/hooks/usePec.ts

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { get, post, patch, put } from '@/lib/api';

// ============ Types ============

export interface PecMeeting {
  id: string;
  meetingDate: string;
  academicYear: string;
  meetingType: 'quarterly' | 'annual' | 'special' | 'sentinel';
  focusAreas: string[];
  status: 'scheduled' | 'in_progress' | 'completed' | 'cancelled';
  location?: string;
  notes?: string;
  createdById: string;
  createdAt: string;
  updatedAt: string;
  attendanceCount: number;
  agendaItemCount: number;
  decisionCount: number;
  openActionCount: number;
}

export interface PecAgendaItem {
  id: string;
  meetingId: string;
  order: number;
  title: string;
  description?: string;
  durationMinutes: number;
  dataSliceType?: string;
  dataSliceKey?: string;
  status: 'pending' | 'discussed' | 'deferred' | 'skipped';
  discussionNotes?: string;
}

export interface PecDecision {
  id: string;
  meetingId: string;
  agendaItemId?: string;
  decisionType: string;
  summary: string;
  rationale: string;
  evidenceRefs: EvidenceRef[];
  requiresCommandApproval: boolean;
  commandDisposition?: string;
  commandNotes?: string;
  createdById: string;
  createdAt: string;
}

export interface EvidenceRef {
  sourceType: string;
  sourceId?: string;
  hyperlink?: string;
}

export interface PecActionItem {
  id: string;
  meetingId: string;
  decisionId?: string;
  description: string;
  ownerPersonId: string;
  ownerName: string;
  dueDate?: string;
  priority: 'low' | 'medium' | 'high' | 'critical';
  status: 'open' | 'in_progress' | 'completed' | 'deferred' | 'cancelled';
  completionNote?: string;
  completedAt?: string;
  createdAt: string;
  isOverdue: boolean;
}

export interface PecDashboard {
  academicYear: string;
  totalResidents: number;
  residentsByPgy: Record<string, number>;
  boardPassRate?: number;
  meanItePercentile?: number;
  dutyHourComplianceRate: number;
  residentsOnRemediation: number;
  wellnessConcerns: number;
  professionalismEvents: number;
  openActionItems: number;
  overdueActionItems: number;
  lastMeetingDate?: string;
  nextMeetingDate?: string;
}

export interface ResidentPerformanceSlice {
  residentId: string;
  residentName: string;
  pgyLevel: number;
  academicYear: string;
  blockRange: { startBlock: string; endBlock: string };
  milestones: Array<{
    subCompetencyId: string;
    meanLevel: number;
    trajectory: Array<{ blockId: string; level: number }>;
  }>;
  caseVolumes: Record<string, number>;
  dutyHourCompliance: number;
  flags: Array<{ type: string; date: string; summary: string }>;
  strengths: string[];
  opportunities: string[];
}

// ============ Hooks ============

export function usePecDashboard(academicYear: string) {
  return useQuery({
    queryKey: ['pec', 'dashboard', academicYear],
    queryFn: () => get<PecDashboard>(`/api/v1/pec/dashboard?academicYear=${academicYear}`),
    enabled: !!academicYear,
  });
}

export function usePecMeetings(params?: {
  academicYear?: string;
  status?: string;
}) {
  const searchParams = new URLSearchParams();
  if (params?.academicYear) searchParams.set('academicYear', params.academicYear);
  if (params?.status) searchParams.set('status', params.status);

  return useQuery({
    queryKey: ['pec', 'meetings', params],
    queryFn: () => get<PecMeeting[]>(`/api/v1/pec/meetings?${searchParams}`),
  });
}

export function usePecMeeting(meetingId: string) {
  return useQuery({
    queryKey: ['pec', 'meeting', meetingId],
    queryFn: () => get<PecMeeting>(`/api/v1/pec/meetings/${meetingId}`),
    enabled: !!meetingId,
  });
}

export function useCreatePecMeeting() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: Omit<PecMeeting, 'id' | 'status' | 'createdById' | 'createdAt' | 'updatedAt' | 'attendanceCount' | 'agendaItemCount' | 'decisionCount' | 'openActionCount'>) =>
      post<PecMeeting>('/api/v1/pec/meetings', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['pec', 'meetings'] });
    },
  });
}

export function useUpdatePecMeeting() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, ...data }: { id: string } & Partial<PecMeeting>) =>
      patch<PecMeeting>(`/api/v1/pec/meetings/${id}`, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['pec', 'meetings'] });
      queryClient.invalidateQueries({ queryKey: ['pec', 'meeting', variables.id] });
    },
  });
}

export function usePecActionItems(params?: {
  ownerId?: string;
  overdueOnly?: boolean;
}) {
  const searchParams = new URLSearchParams();
  if (params?.ownerId) searchParams.set('ownerId', params.ownerId);
  if (params?.overdueOnly) searchParams.set('overdueOnly', 'true');

  return useQuery({
    queryKey: ['pec', 'actions', params],
    queryFn: () => get<PecActionItem[]>(`/api/v1/pec/actions?${searchParams}`),
  });
}

export function useUpdateActionStatus() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ actionId, status, completionNote }: {
      actionId: string;
      status: string;
      completionNote?: string;
    }) => {
      const params = new URLSearchParams({ status });
      if (completionNote) params.set('completionNote', completionNote);
      return patch(`/api/v1/pec/actions/${actionId}/status?${params}`, {});
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['pec', 'actions'] });
      queryClient.invalidateQueries({ queryKey: ['pec', 'dashboard'] });
    },
  });
}

export function useResidentSlice(residentId: string, academicYear: string) {
  return useQuery({
    queryKey: ['pec', 'slice', 'resident', residentId, academicYear],
    queryFn: () => get<ResidentPerformanceSlice>(
      `/api/v1/pec/slices/resident/${residentId}?academicYear=${academicYear}`
    ),
    enabled: !!residentId && !!academicYear,
  });
}
```

### 6.2 Dashboard Page

```tsx
// frontend/src/app/admin/pec/page.tsx

'use client';

import { useState, useMemo } from 'react';
import { format, parseISO } from 'date-fns';
import {
  Calendar, Users, AlertTriangle, CheckCircle2,
  Clock, TrendingUp, FileText, Plus
} from 'lucide-react';

import { ProtectedRoute } from '@/components/ProtectedRoute';
import { PageHeader } from '@/components/layout/PageHeader';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';

import { usePecDashboard, usePecMeetings, usePecActionItems } from '@/hooks/usePec';

const ACADEMIC_YEARS = ['AY25-26', 'AY24-25', 'AY23-24'];

export default function PecDashboardPage() {
  const [academicYear, setAcademicYear] = useState('AY25-26');
  const [activeTab, setActiveTab] = useState('overview');

  const { data: dashboard, isLoading: dashboardLoading } = usePecDashboard(academicYear);
  const { data: meetings, isLoading: meetingsLoading } = usePecMeetings({ academicYear });
  const { data: actionItems, isLoading: actionsLoading } = usePecActionItems({ overdueOnly: false });

  const upcomingMeetings = useMemo(() => {
    if (!meetings) return [];
    const today = new Date();
    return meetings
      .filter(m => m.status === 'scheduled' && new Date(m.meetingDate) >= today)
      .sort((a, b) => new Date(a.meetingDate).getTime() - new Date(b.meetingDate).getTime())
      .slice(0, 3);
  }, [meetings]);

  const overdueActions = useMemo(() => {
    return actionItems?.filter(a => a.isOverdue) || [];
  }, [actionItems]);

  return (
    <ProtectedRoute allowedRoles={['admin', 'coordinator', 'pd', 'apd', 'faculty']}>
      <div className="container mx-auto py-6 space-y-6">
        <PageHeader
          title="Program Evaluation Committee"
          description="ACGME-compliant program oversight and continuous improvement"
        >
          <div className="flex items-center gap-4">
            <Select value={academicYear} onValueChange={setAcademicYear}>
              <SelectTrigger className="w-32">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {ACADEMIC_YEARS.map(year => (
                  <SelectItem key={year} value={year}>{year}</SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Button>
              <Plus className="h-4 w-4 mr-2" />
              New Meeting
            </Button>
          </div>
        </PageHeader>

        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList>
            <TabsTrigger value="overview">Overview</TabsTrigger>
            <TabsTrigger value="meetings">Meetings</TabsTrigger>
            <TabsTrigger value="actions">Action Items</TabsTrigger>
            <TabsTrigger value="analytics">Analytics</TabsTrigger>
          </TabsList>

          <TabsContent value="overview" className="space-y-6">
            {/* KPI Cards */}
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
              <Card>
                <CardHeader className="flex flex-row items-center justify-between pb-2">
                  <CardTitle className="text-sm font-medium">Total Residents</CardTitle>
                  <Users className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{dashboard?.totalResidents || 0}</div>
                  <p className="text-xs text-muted-foreground">
                    {Object.entries(dashboard?.residentsByPgy || {})
                      .map(([pgy, count]) => `PGY-${pgy}: ${count}`)
                      .join(' | ')}
                  </p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="flex flex-row items-center justify-between pb-2">
                  <CardTitle className="text-sm font-medium">Duty Hour Compliance</CardTitle>
                  <CheckCircle2 className="h-4 w-4 text-green-500" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">
                    {((dashboard?.dutyHourComplianceRate || 0) * 100).toFixed(1)}%
                  </div>
                  <p className="text-xs text-muted-foreground">80-hour rule adherence</p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="flex flex-row items-center justify-between pb-2">
                  <CardTitle className="text-sm font-medium">Remediation</CardTitle>
                  <AlertTriangle className="h-4 w-4 text-amber-500" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{dashboard?.residentsOnRemediation || 0}</div>
                  <p className="text-xs text-muted-foreground">Active remediation plans</p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="flex flex-row items-center justify-between pb-2">
                  <CardTitle className="text-sm font-medium">Open Actions</CardTitle>
                  <Clock className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{dashboard?.openActionItems || 0}</div>
                  <p className="text-xs text-muted-foreground">
                    {dashboard?.overdueActionItems || 0} overdue
                  </p>
                </CardContent>
              </Card>
            </div>

            {/* Two Column Layout */}
            <div className="grid gap-6 lg:grid-cols-2">
              {/* Upcoming Meetings */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Calendar className="h-5 w-5" />
                    Upcoming Meetings
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  {upcomingMeetings.length === 0 ? (
                    <p className="text-muted-foreground text-sm">No upcoming meetings scheduled</p>
                  ) : (
                    <div className="space-y-4">
                      {upcomingMeetings.map(meeting => (
                        <div key={meeting.id} className="flex items-center justify-between">
                          <div>
                            <p className="font-medium">
                              {format(parseISO(meeting.meetingDate), 'MMM d, yyyy')}
                            </p>
                            <p className="text-sm text-muted-foreground">
                              {meeting.focusAreas.join(', ') || 'General Review'}
                            </p>
                          </div>
                          <Badge variant="outline">{meeting.meetingType}</Badge>
                        </div>
                      ))}
                    </div>
                  )}
                </CardContent>
              </Card>

              {/* Overdue Actions */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <AlertTriangle className="h-5 w-5 text-amber-500" />
                    Overdue Action Items
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  {overdueActions.length === 0 ? (
                    <p className="text-muted-foreground text-sm">No overdue items</p>
                  ) : (
                    <div className="space-y-4">
                      {overdueActions.slice(0, 5).map(action => (
                        <div key={action.id} className="flex items-start justify-between">
                          <div className="space-y-1">
                            <p className="text-sm font-medium leading-none">
                              {action.description}
                            </p>
                            <p className="text-xs text-muted-foreground">
                              Owner: {action.ownerName} | Due: {action.dueDate}
                            </p>
                          </div>
                          <Badge variant="destructive">{action.priority}</Badge>
                        </div>
                      ))}
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          <TabsContent value="meetings">
            {/* Meeting list component */}
            <Card>
              <CardHeader>
                <CardTitle>PEC Meetings</CardTitle>
              </CardHeader>
              <CardContent>
                {/* Implement PecMeetingsList component */}
                <p className="text-muted-foreground">Meeting list implementation pending</p>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="actions">
            {/* Action items list */}
            <Card>
              <CardHeader>
                <CardTitle>Action Items</CardTitle>
              </CardHeader>
              <CardContent>
                {/* Implement PecActionItemsList component */}
                <p className="text-muted-foreground">Action items list implementation pending</p>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="analytics">
            {/* Analytics panels */}
            <Card>
              <CardHeader>
                <CardTitle>Performance Analytics</CardTitle>
              </CardHeader>
              <CardContent>
                {/* Implement analytics visualizations */}
                <p className="text-muted-foreground">Analytics implementation pending</p>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </ProtectedRoute>
  );
}
```

---

## 7. Skill Definition

Create a Claude Code skill for PEC operations.

```yaml
# .claude/skills/PEC_OPERATIONS/SKILL.md
---
name: PEC_OPERATIONS
version: 1.0.0
description: Program Evaluation Committee operations for ACGME compliance
triggers:
  - "pec"
  - "program evaluation"
  - "pec meeting"
  - "action item"
  - "milestone review"
tools_required:
  - mcp__residency-scheduler__rag_search
  - mcp__residency-scheduler__validate_schedule_tool
capabilities:
  - Meeting preparation and agenda generation
  - Decision logging with evidence linkage
  - Action item tracking and follow-up
  - Resident performance slice generation
  - Annual program evaluation drafting
---

# PEC Operations Skill

## Purpose
Manage Program Evaluation Committee workflows including meeting preparation,
decision documentation, action item tracking, and compliance reporting per
ACGME requirements.

## Operational Modes

| Mode | Allowed Operations |
|------|-------------------|
| SAFE_AUDIT | View dashboards, generate read-only reports |
| SUPERVISED_EXECUTION | Draft agendas/decisions (human approves) |
| EXPERIMENTAL_PLANNING | Simulate curriculum changes |
| EMERGENCY_OVERRIDE | Sentinel event response |

## Key Workflows

### 1. Meeting Preparation (`/pec-prep`)
```
Input: academicYear, focusAreas
Steps:
1. Query dashboard metrics via GET /api/v1/pec/dashboard
2. Identify outliers and trends
3. Draft agenda with data slice references
4. Generate pre-meeting packet (PDF)
```

### 2. Decision Logging
```
Input: meetingId, decisionType, summary, rationale, evidenceRefs
Validation:
- Rationale must reference specific evidence
- Command approval flagging for ProgramChange/PolicyChange
```

### 3. Action Item Follow-up
```
Trigger: Weekly cron or manual /pec-actions
Steps:
1. Query open/overdue items
2. Notify owners via existing notification service
3. Escalate overdue > 14 days to PD
```

## Integration Points

- **Scheduling Domain**: Link decisions to schedule changes
- **Resilience Framework**: Assess capacity impact of curriculum changes
- **Compliance Engine**: Validate decisions don't violate ACGME rules
- **RAG**: Query policy documents for decision support

## Evidence Source Types

| Type | Description | Example Link |
|------|-------------|--------------|
| BLOCK_METRICS | Aggregate block performance | `/api/v1/pec/slices/resident/{id}` |
| ROTATION_EVALS | End-of-rotation evaluations | `/api/v1/evaluations?rotation={id}` |
| DUTY_HOURS | Work hour compliance | `/api/v1/compliance/duty-hours` |
| WELLNESS | Wellness survey results | `/api/v1/wellness/summary` |
| EXAM_SCORES | ITE, board prep results | `/api/v1/exams/summary` |
| SCHEDULE | Schedule assignments | `/api/v1/schedule/blocks` |

## Military-Specific Requirements

1. **Command Approval Chain**: Decisions marked `requiresCommandApproval`
   must be routed for disposition before implementation
2. **Dual-Mission Metrics**: Track impact on both GME and MTF coverage
3. **Security**: PHI headers on all responses, role-based access

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/pec/dashboard` | Dashboard metrics |
| GET | `/pec/meetings` | List meetings |
| POST | `/pec/meetings` | Create meeting |
| GET | `/pec/meetings/{id}` | Meeting details |
| POST | `/pec/meetings/{id}/agenda` | Add agenda item |
| POST | `/pec/meetings/{id}/decisions` | Log decision |
| POST | `/pec/meetings/{id}/actions` | Create action |
| GET | `/pec/actions` | List open actions |
| GET | `/pec/slices/resident/{id}` | Resident performance |
| GET | `/pec/slices/rotation/{id}` | Rotation quality |
```

---

## 8. Implementation Checklist

### Phase 1: Backend Core
- [ ] Create models in `backend/app/models/pec.py`
- [ ] Add to `backend/app/models/__init__.py`
- [ ] Create Alembic migration `20260119_add_pec_tables`
- [ ] Create schemas in `backend/app/schemas/pec.py`
- [ ] Create repositories in `backend/app/repositories/pec.py`
- [ ] Create service in `backend/app/services/pec_service.py`
- [ ] Create routes in `backend/app/api/routes/pec.py`
- [ ] Register routes in `backend/app/api/routes/__init__.py`
- [ ] Add tests in `backend/tests/api/test_pec.py`

### Phase 2: Analytics
- [ ] Create `pec_analytics` module for aggregate computation
- [ ] Implement materialized view refresh for `pec_evaluation_aggregates`
- [ ] Add Celery task for periodic aggregate refresh
- [ ] Create slice generation from existing evaluation data

### Phase 3: Frontend
- [ ] Create hooks in `frontend/src/hooks/usePec.ts`
- [ ] Create dashboard page `frontend/src/app/admin/pec/page.tsx`
- [ ] Create meeting detail page `frontend/src/app/admin/pec/meetings/[id]/page.tsx`
- [ ] Add navigation link in sidebar
- [ ] Add frontend tests

### Phase 4: Workflows
- [ ] Create skill definition `.claude/skills/PEC_OPERATIONS/SKILL.md`
- [ ] Implement `/pec-prep` workflow
- [ ] Implement `/pec-summary` for annual reporting
- [ ] Add MCP tool for PEC analytics

---

## 9. References

- **ACGME Program Requirements**: Section VI.A (Program Evaluation)
- **Existing Patterns**:
  - `backend/app/services/swap_request_service.py` (approval workflow)
  - `backend/app/resilience/` (defense level integration)
  - `frontend/src/app/admin/compliance/page.tsx` (dashboard pattern)
- **RAG Queries**:
  - `rag_search('ACGME program evaluation committee')`
  - `rag_search('milestone assessment')`
  - `rag_search('approval workflow patterns')`
