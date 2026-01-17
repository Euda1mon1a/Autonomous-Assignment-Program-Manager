"""Block Explorer schemas for pre-launch verification UI.

These schemas match the frontend Block Explorer JSON structure,
enabling full-stack integration with live database data.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


# --- Meta ---


class BlockMeta(BaseModel):
    """Block metadata for header display."""

    block_number: int = Field(..., alias="blockNumber")
    title: str
    date_range: str = Field(..., alias="dateRange")
    start_date: str = Field(..., alias="startDate")
    end_date: str = Field(..., alias="endDate")
    days_in_block: int = Field(..., alias="daysInBlock")
    generated_at: datetime = Field(..., alias="generatedAt")

    model_config = ConfigDict(populate_by_name=True)


# --- Completeness ---


class CompletenessItem(BaseModel):
    """Single completeness metric with status."""

    assigned: int | None = None
    total: int | None = None
    active: int | None = None
    defined: int | None = None
    recorded: int | None = None
    pending: int | None = None
    filled: int | None = None
    gaps: int | None = None
    status: str = Field(..., description="pass | warn | fail")


class CompletenessData(BaseModel):
    """Data completeness for all entity types."""

    residents: CompletenessItem
    faculty: CompletenessItem
    rotations: CompletenessItem
    absences: CompletenessItem
    call_roster: CompletenessItem = Field(..., alias="callRoster")
    coverage: CompletenessItem

    model_config = ConfigDict(populate_by_name=True)


# --- ACGME Compliance ---


class ACGMERule(BaseModel):
    """Single ACGME compliance rule status."""

    id: str
    name: str
    status: str = Field(..., description="pass | warn | fail")
    detail: str
    threshold: str


class ACGMEComplianceData(BaseModel):
    """ACGME compliance summary."""

    overall_status: str = Field(..., alias="overallStatus")
    last_checked: datetime = Field(..., alias="lastChecked")
    rules: list[ACGMERule]

    model_config = ConfigDict(populate_by_name=True)


# --- Health ---


class HealthData(BaseModel):
    """Schedule health metrics."""

    coverage: int = Field(..., description="Coverage percentage 0-100")
    conflicts: int = Field(default=0)
    resident_count: int = Field(..., alias="residentCount")
    total_residents: int = Field(..., alias="totalResidents")
    acgme_compliant: bool = Field(..., alias="acgmeCompliant")
    completeness: int = Field(..., description="Completeness percentage 0-100")
    status: str = Field(..., description="ready | warning | error")

    model_config = ConfigDict(populate_by_name=True)


# --- Calendar ---


class CalendarWeek(BaseModel):
    """Single week in the block calendar."""

    week_num: int = Field(..., alias="weekNum")
    dates: list[str] = Field(..., description="ISO date strings")

    model_config = ConfigDict(populate_by_name=True)


class CalendarData(BaseModel):
    """Calendar structure for the block."""

    weeks: list[CalendarWeek]
    day_labels: list[str] = Field(..., alias="dayLabels")

    model_config = ConfigDict(populate_by_name=True)


# --- Residents ---


class ResidentHalfDay(BaseModel):
    """Single day's AM/PM assignments for a resident."""

    date: str
    am: str
    pm: str
    am_source: str = Field(..., alias="amSource")
    pm_source: str = Field(..., alias="pmSource")

    model_config = ConfigDict(populate_by_name=True)


class ResidentExplorerData(BaseModel):
    """Resident data for Block Explorer list and modal."""

    id: str
    name: str
    pgy_level: int = Field(..., alias="pgyLevel")
    rotation: str
    rotation_id: str = Field(..., alias="rotationId")
    assignment_count: int = Field(..., alias="assignmentCount")
    complete_assignments: int = Field(..., alias="completeAssignments")
    absence_days: int = Field(..., alias="absenceDays")
    source: str = Field(..., description="PRE | GEN | MAN")
    notes: str | None = None
    needs_attention: bool = Field(..., alias="needsAttention")
    attention_reason: str | None = Field(None, alias="attentionReason")
    half_days: list[ResidentHalfDay] = Field(..., alias="halfDays")

    model_config = ConfigDict(populate_by_name=True)


# --- Rotations ---


class RotationExplorerData(BaseModel):
    """Rotation data for Block Explorer sidebar."""

    id: str
    name: str
    abbreviation: str
    category: str
    color: str
    capacity: int | None = None
    assigned_count: int = Field(..., alias="assignedCount")
    residents: list[str] = Field(..., description="List of resident IDs")
    description: str | None = None
    call_eligible: bool = Field(..., alias="callEligible")
    leave_eligible: bool = Field(..., alias="leaveEligible")

    model_config = ConfigDict(populate_by_name=True)


# --- Validation Checks ---


class ValidationCheck(BaseModel):
    """Single validation check result."""

    name: str
    status: str = Field(..., description="pass | fail")
    description: str
    details: str


# --- Sources ---


class SourceInfo(BaseModel):
    """Assignment source metadata."""

    label: str
    color: str
    description: str
    count: int
    percentage: int


# --- Main Response ---


class BlockExplorerResponse(BaseModel):
    """Complete Block Explorer data response."""

    meta: BlockMeta
    completeness: CompletenessData
    acgme_compliance: ACGMEComplianceData = Field(..., alias="acgmeCompliance")
    health: HealthData
    calendar: CalendarData
    residents: list[ResidentExplorerData]
    rotations: list[RotationExplorerData]
    validation_checks: list[ValidationCheck] = Field(..., alias="validationChecks")
    activity_colors: dict[str, str] = Field(..., alias="activityColors")
    sources: dict[str, SourceInfo]

    model_config = ConfigDict(populate_by_name=True)
