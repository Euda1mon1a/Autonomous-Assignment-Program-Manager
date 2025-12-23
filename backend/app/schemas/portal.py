"""Pydantic schemas for faculty self-service portal."""

from datetime import date, datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field


class SwapRequestStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXECUTED = "executed"
    CANCELLED = "cancelled"


# ============================================================================
# Schedule View Schemas
# ============================================================================


class FMITWeekInfo(BaseModel):
    """Information about an FMIT week."""

    week_start: date
    week_end: date
    is_past: bool = False
    has_conflict: bool = False
    conflict_description: str | None = None
    can_request_swap: bool = True
    pending_swap_request: bool = False


class MyScheduleResponse(BaseModel):
    """Response for /my/schedule endpoint."""

    faculty_id: UUID
    faculty_name: str
    fmit_weeks: list[FMITWeekInfo]
    total_weeks_assigned: int
    target_weeks: int
    weeks_remaining: int


# ============================================================================
# Swap Request Schemas
# ============================================================================


class SwapRequestSummary(BaseModel):
    """Summary of a swap request."""

    id: UUID
    other_faculty_name: str
    week_to_give: date | None
    week_to_receive: date | None
    status: SwapRequestStatus
    created_at: datetime
    is_incoming: bool  # True if request is to take a week from me


class MySwapsResponse(BaseModel):
    """Response for /my/swaps endpoint."""

    incoming_requests: list[SwapRequestSummary]
    outgoing_requests: list[SwapRequestSummary]
    recent_swaps: list[SwapRequestSummary]


class SwapRequestCreate(BaseModel):
    """Request to create a swap request."""

    week_to_offload: date
    preferred_target_faculty_id: UUID | None = None
    reason: str | None = Field(None, max_length=500)
    auto_find_candidates: bool = True


class SwapRequestResponse(BaseModel):
    """Response after creating a swap request."""

    success: bool
    request_id: UUID | None = None
    message: str
    candidates_notified: int = 0


class SwapRespondRequest(BaseModel):
    """Request to respond to a swap offer."""

    accept: bool
    counter_offer_week: date | None = None
    notes: str | None = Field(None, max_length=500)


# ============================================================================
# Preferences Schemas
# ============================================================================


class PreferencesUpdate(BaseModel):
    """Request to update faculty preferences."""

    preferred_weeks: list[date] | None = None
    blocked_weeks: list[date] | None = None
    max_weeks_per_month: int | None = Field(None, ge=1, le=4)
    max_consecutive_weeks: int | None = Field(None, ge=1, le=2)
    min_gap_between_weeks: int | None = Field(None, ge=1, le=4)
    notify_swap_requests: bool | None = None
    notify_schedule_changes: bool | None = None
    notify_conflict_alerts: bool | None = None
    notify_reminder_days: int | None = Field(None, ge=1, le=14)
    notes: str | None = Field(None, max_length=1000)


class PreferencesResponse(BaseModel):
    """Response for faculty preferences."""

    faculty_id: UUID
    preferred_weeks: list[date]
    blocked_weeks: list[date]
    max_weeks_per_month: int
    max_consecutive_weeks: int
    min_gap_between_weeks: int
    target_weeks_per_year: int
    notify_swap_requests: bool
    notify_schedule_changes: bool
    notify_conflict_alerts: bool
    notify_reminder_days: int
    notes: str | None
    updated_at: datetime


# ============================================================================
# Dashboard Schemas
# ============================================================================


class DashboardAlert(BaseModel):
    """An alert for the dashboard."""

    id: UUID
    alert_type: str  # conflict, swap_request, reminder
    severity: str  # critical, warning, info
    message: str
    created_at: datetime
    action_url: str | None = None


class DashboardStats(BaseModel):
    """Statistics for the dashboard."""

    weeks_assigned: int
    weeks_completed: int
    weeks_remaining: int
    target_weeks: int
    pending_swap_requests: int
    unread_alerts: int


class DashboardResponse(BaseModel):
    """Response for /my/dashboard endpoint."""

    faculty_id: UUID
    faculty_name: str
    stats: DashboardStats
    upcoming_weeks: list[FMITWeekInfo]
    recent_alerts: list[DashboardAlert]
    pending_swap_decisions: list[SwapRequestSummary]


# ============================================================================
# Marketplace Schemas
# ============================================================================


class MarketplaceEntry(BaseModel):
    """An entry in the swap marketplace."""

    request_id: UUID
    requesting_faculty_name: str
    week_available: date
    reason: str | None
    posted_at: datetime
    expires_at: datetime | None
    is_compatible: bool  # Based on viewer's schedule


class MarketplaceResponse(BaseModel):
    """Response for /swaps/marketplace endpoint."""

    entries: list[MarketplaceEntry]
    total: int
    my_postings: int
