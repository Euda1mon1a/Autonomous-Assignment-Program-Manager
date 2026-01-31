"""Schemas for half-day schedule Excel staging and diff preview."""

from __future__ import annotations

from datetime import date, datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field


class HalfDayDiffType(str, Enum):
    """Diff classification for a half-day slot."""

    ADDED = "added"
    REMOVED = "removed"
    MODIFIED = "modified"


class HalfDayDiffEntry(BaseModel):
    """Single diff entry between Excel and live schedule."""

    person_id: UUID | None = None
    person_name: str
    assignment_date: date
    time_of_day: str  # AM/PM
    diff_type: HalfDayDiffType
    excel_value: str | None = None
    current_value: str | None = None
    warnings: list[str] = Field(default_factory=list)


class HalfDayDiffMetrics(BaseModel):
    """Summary metrics for Excel vs schedule diff."""

    total_slots: int = 0
    changed_slots: int = 0
    added: int = 0
    removed: int = 0
    modified: int = 0
    percent_changed: float = 0.0
    manual_half_days: int = 0
    manual_hours: float = 0.0
    by_activity: dict[str, int] = Field(default_factory=dict)


class HalfDayImportStageResponse(BaseModel):
    """Response for staging a half-day Excel import."""

    success: bool
    batch_id: UUID | None = None
    created_at: datetime | None = None
    message: str
    warnings: list[str] = Field(default_factory=list)
    diff_metrics: HalfDayDiffMetrics | None = None


class HalfDayImportPreviewResponse(BaseModel):
    """Preview response for half-day staged batch."""

    batch_id: UUID
    metrics: HalfDayDiffMetrics
    diffs: list[HalfDayDiffEntry] = Field(default_factory=list)
    total_diffs: int = 0
    page: int = 1
    page_size: int = 50


class HalfDayImportDraftRequest(BaseModel):
    """Request to create a schedule draft from staged half-day diffs."""

    staged_ids: list[UUID] | None = None
    notes: str | None = Field(default=None, max_length=2000)


class HalfDayImportDraftResponse(BaseModel):
    """Response for creating a draft from staged half-day diffs."""

    success: bool
    batch_id: UUID
    draft_id: UUID | None = None
    message: str
    total_selected: int = 0
    added: int = 0
    modified: int = 0
    removed: int = 0
    skipped: int = 0
    failed: int = 0
