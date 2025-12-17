"""Schemas for personal dashboard API."""
from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field


class DashboardUserInfo(BaseModel):
    """User information for dashboard."""
    id: UUID
    name: str
    role: str  # 'resident' or 'faculty'
    email: str | None = None
    pgy_level: int | None = None

    class Config:
        from_attributes = True


class DashboardScheduleItem(BaseModel):
    """Schedule item for dashboard."""
    date: date
    time_of_day: str  # 'AM' or 'PM'
    activity: str
    location: str | None = None
    can_trade: bool = True
    role: str | None = None  # 'primary', 'supervising', 'backup'
    assignment_id: UUID | None = None

    class Config:
        from_attributes = True


class DashboardSwapItem(BaseModel):
    """Pending swap item for dashboard."""
    swap_id: UUID
    swap_type: str  # 'one_to_one' or 'absorb'
    status: str  # 'pending', 'approved', etc.
    source_week: date
    target_week: date | None
    other_party_name: str
    requested_at: datetime

    class Config:
        from_attributes = True


class DashboardAbsenceItem(BaseModel):
    """Absence item for dashboard."""
    absence_id: UUID
    start_date: date
    end_date: date
    absence_type: str
    notes: str | None = None

    class Config:
        from_attributes = True


class DashboardSummary(BaseModel):
    """Summary statistics for dashboard."""
    next_assignment: date | None = None
    workload_next_4_weeks: int = 0  # Number of blocks
    pending_swap_count: int = 0
    upcoming_absences_count: int = 0


class MeDashboardResponse(BaseModel):
    """Complete dashboard response."""
    user: DashboardUserInfo
    upcoming_schedule: list[DashboardScheduleItem] = []
    pending_swaps: list[DashboardSwapItem] = []
    absences: list[DashboardAbsenceItem] = []
    calendar_sync_url: str | None = None
    summary: DashboardSummary

    class Config:
        from_attributes = True
