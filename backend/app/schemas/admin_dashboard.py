"""Schemas for admin dashboard aggregate endpoints."""

from datetime import datetime

from pydantic import BaseModel


class AdminUserCounts(BaseModel):
    total: int
    active: int


class AdminPeopleCounts(BaseModel):
    total: int
    residents: int
    faculty: int


class AdminAbsenceCounts(BaseModel):
    active: int
    upcoming: int


class AdminSwapCounts(BaseModel):
    pending: int
    approved: int
    executed: int
    rejected: int
    cancelled: int
    rolled_back: int


class AdminConflictCounts(BaseModel):
    new: int
    acknowledged: int
    resolved: int
    ignored: int


class AdminDashboardSummary(BaseModel):
    timestamp: datetime
    users: AdminUserCounts
    people: AdminPeopleCounts
    absences: AdminAbsenceCounts
    swaps: AdminSwapCounts
    conflicts: AdminConflictCounts
