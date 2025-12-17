"""Pydantic schemas for faculty self-service portal."""
from datetime import date, datetime
from enum import Enum
from typing import Optional, List
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
    conflict_description: Optional[str] = None
    can_request_swap: bool = True
    pending_swap_request: bool = False


class MyScheduleResponse(BaseModel):
    """Response for /my/schedule endpoint."""
    faculty_id: UUID
    faculty_name: str
    fmit_weeks: List[FMITWeekInfo]
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
    week_to_give: Optional[date]
    week_to_receive: Optional[date]
    status: SwapRequestStatus
    created_at: datetime
    is_incoming: bool  # True if request is to take a week from me


class MySwapsResponse(BaseModel):
    """Response for /my/swaps endpoint."""
    incoming_requests: List[SwapRequestSummary]
    outgoing_requests: List[SwapRequestSummary]
    recent_swaps: List[SwapRequestSummary]


class SwapRequestCreate(BaseModel):
    """Request to create a swap request."""
    week_to_offload: date
    preferred_target_faculty_id: Optional[UUID] = None
    reason: Optional[str] = Field(None, max_length=500)
    auto_find_candidates: bool = True


class SwapRequestResponse(BaseModel):
    """Response after creating a swap request."""
    success: bool
    request_id: Optional[UUID] = None
    message: str
    candidates_notified: int = 0


class SwapRespondRequest(BaseModel):
    """Request to respond to a swap offer."""
    accept: bool
    counter_offer_week: Optional[date] = None
    notes: Optional[str] = Field(None, max_length=500)


# ============================================================================
# Preferences Schemas
# ============================================================================

class PreferencesUpdate(BaseModel):
    """Request to update faculty preferences."""
    preferred_weeks: Optional[List[date]] = None
    blocked_weeks: Optional[List[date]] = None
    max_weeks_per_month: Optional[int] = Field(None, ge=1, le=4)
    max_consecutive_weeks: Optional[int] = Field(None, ge=1, le=2)
    min_gap_between_weeks: Optional[int] = Field(None, ge=1, le=4)
    notify_swap_requests: Optional[bool] = None
    notify_schedule_changes: Optional[bool] = None
    notify_conflict_alerts: Optional[bool] = None
    notify_reminder_days: Optional[int] = Field(None, ge=1, le=14)
    notes: Optional[str] = Field(None, max_length=1000)


class PreferencesResponse(BaseModel):
    """Response for faculty preferences."""
    faculty_id: UUID
    preferred_weeks: List[date]
    blocked_weeks: List[date]
    max_weeks_per_month: int
    max_consecutive_weeks: int
    min_gap_between_weeks: int
    target_weeks_per_year: int
    notify_swap_requests: bool
    notify_schedule_changes: bool
    notify_conflict_alerts: bool
    notify_reminder_days: int
    notes: Optional[str]
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
    action_url: Optional[str] = None


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
    upcoming_weeks: List[FMITWeekInfo]
    recent_alerts: List[DashboardAlert]
    pending_swap_decisions: List[SwapRequestSummary]


# ============================================================================
# Marketplace Schemas
# ============================================================================

class MarketplaceEntry(BaseModel):
    """An entry in the swap marketplace."""
    request_id: UUID
    requesting_faculty_name: str
    week_available: date
    reason: Optional[str]
    posted_at: datetime
    expires_at: Optional[datetime]
    is_compatible: bool  # Based on viewer's schedule


class MarketplaceResponse(BaseModel):
    """Response for /swaps/marketplace endpoint."""
    entries: List[MarketplaceEntry]
    total: int
    my_postings: int
