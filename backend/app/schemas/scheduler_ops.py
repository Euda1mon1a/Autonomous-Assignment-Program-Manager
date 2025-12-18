"""Scheduler operations schemas for n8n workflow integration.

Provides schemas for:
- Situation reports (sitrep)
- Fix-it mode operations
- Task approval operations
"""
from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field


# Enums

class FixItMode(str, Enum):
    """Fix-it execution modes."""
    GREEDY = "greedy"           # Aggressive fixes, may impact quality
    CONSERVATIVE = "conservative"  # Careful fixes, prioritize stability
    BALANCED = "balanced"       # Balance between speed and quality


class ApprovalAction(str, Enum):
    """Task approval actions."""
    APPROVE = "approve"
    DENY = "deny"


class TaskStatus(str, Enum):
    """Task execution status."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


# Situation Report Schemas

class TaskMetrics(BaseModel):
    """Task execution metrics."""
    total_tasks: int = Field(..., ge=0, description="Total number of tasks")
    active_tasks: int = Field(..., ge=0, description="Currently running tasks")
    completed_tasks: int = Field(..., ge=0, description="Successfully completed tasks")
    failed_tasks: int = Field(..., ge=0, description="Failed tasks")
    pending_tasks: int = Field(..., ge=0, description="Tasks waiting to execute")
    success_rate: float = Field(..., ge=0.0, le=1.0, description="Success rate (0.0-1.0)")


class RecentTaskInfo(BaseModel):
    """Information about a recent task."""
    task_id: str = Field(..., description="Task identifier")
    name: str = Field(..., description="Task name")
    status: TaskStatus
    description: str | None = Field(None, description="Task description")
    started_at: datetime | None = Field(None, description="Task start time")
    completed_at: datetime | None = Field(None, description="Task completion time")
    duration_seconds: float | None = Field(None, description="Task duration in seconds")
    error_message: str | None = Field(None, description="Error message if failed")


class CoverageMetrics(BaseModel):
    """Schedule coverage metrics."""
    coverage_rate: float = Field(..., ge=0.0, le=1.0, description="Overall coverage rate")
    blocks_covered: int = Field(..., ge=0, description="Number of blocks with assignments")
    blocks_total: int = Field(..., ge=0, description="Total number of blocks")
    critical_gaps: int = Field(default=0, ge=0, description="Number of critical coverage gaps")
    faculty_utilization: float = Field(..., ge=0.0, le=1.0, description="Faculty utilization rate")


class SitrepResponse(BaseModel):
    """Situation report response."""
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Report timestamp")

    # Task metrics
    task_metrics: TaskMetrics

    # Health status
    health_status: str = Field(..., description="Overall health: healthy, degraded, critical")
    defense_level: str | None = Field(None, description="Current defense level")

    # Recent activity
    recent_tasks: list[RecentTaskInfo] = Field(default_factory=list, description="Recent tasks")

    # Coverage metrics
    coverage_metrics: CoverageMetrics | None = Field(None, description="Schedule coverage metrics")

    # Alerts and recommendations
    immediate_actions: list[str] = Field(default_factory=list, description="Required immediate actions")
    watch_items: list[str] = Field(default_factory=list, description="Items to monitor")

    # System metadata
    last_update: datetime = Field(default_factory=datetime.utcnow, description="Last system update")
    crisis_mode: bool = Field(default=False, description="Whether system is in crisis mode")


# Fix-It Mode Schemas

class FixItRequest(BaseModel):
    """Request to initiate fix-it mode."""
    mode: FixItMode = Field(default=FixItMode.BALANCED, description="Fix-it execution mode")
    max_retries: int = Field(default=3, ge=1, le=10, description="Maximum retry attempts per task")
    auto_approve: bool = Field(default=False, description="Automatically approve changes")
    initiated_by: str = Field(..., min_length=1, max_length=100, description="User who initiated fix-it")
    target_task_ids: list[str] | None = Field(None, description="Specific tasks to fix (None = all failed)")
    dry_run: bool = Field(default=False, description="Preview changes without executing")


class AffectedTask(BaseModel):
    """Information about a task affected by fix-it."""
    task_id: str
    task_name: str
    previous_status: TaskStatus
    new_status: TaskStatus
    action_taken: str
    retry_count: int = 0


class FixItResponse(BaseModel):
    """Response from fix-it mode execution."""
    status: str = Field(..., description="Execution status: initiated, running, completed, failed")
    execution_id: str = Field(..., description="Unique execution identifier")
    mode: FixItMode

    # Metrics
    tasks_fixed: int = Field(default=0, ge=0, description="Number of tasks successfully fixed")
    tasks_retried: int = Field(default=0, ge=0, description="Number of tasks retried")
    tasks_skipped: int = Field(default=0, ge=0, description="Number of tasks skipped")
    tasks_failed: int = Field(default=0, ge=0, description="Number of tasks that failed to fix")

    # Details
    affected_tasks: list[AffectedTask] = Field(default_factory=list, description="Tasks affected by fix-it")
    estimated_completion: datetime | None = Field(None, description="Estimated completion time")

    # Metadata
    initiated_by: str
    initiated_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: datetime | None = None

    # Messages
    message: str = Field(..., description="Human-readable status message")
    warnings: list[str] = Field(default_factory=list, description="Warnings generated during execution")


# Approval Schemas

class ApprovalRequest(BaseModel):
    """Request to approve or deny a task."""
    token: str = Field(..., min_length=8, max_length=200, description="Approval token")
    task_id: str | None = Field(None, description="Specific task ID (None = all pending for token)")
    action: ApprovalAction = Field(default=ApprovalAction.APPROVE, description="Approve or deny")
    approved_by: str = Field(..., min_length=1, max_length=100, description="User who approved/denied")
    approved_by_id: str | None = Field(None, description="User ID who approved/denied")
    notes: str | None = Field(None, max_length=500, description="Optional approval notes")


class ApprovedTaskInfo(BaseModel):
    """Information about an approved/denied task."""
    task_id: str
    task_name: str
    task_type: str
    previous_status: TaskStatus
    new_status: TaskStatus
    approved_at: datetime


class ApprovalResponse(BaseModel):
    """Response from approval operation."""
    status: str = Field(..., description="Status: approved, denied, invalid_token, not_found")
    action: ApprovalAction

    # Task information
    task_id: str | None = Field(None, description="Task ID (or 'multiple' if batch approval)")

    # Metrics
    approved_tasks: int = Field(default=0, ge=0, description="Number of tasks approved")
    denied_tasks: int = Field(default=0, ge=0, description="Number of tasks denied")

    # Details
    task_details: list[ApprovedTaskInfo] = Field(default_factory=list, description="Details of approved/denied tasks")

    # Metadata
    approved_by: str
    approved_at: datetime = Field(default_factory=datetime.utcnow)

    # Messages
    message: str = Field(..., description="Human-readable result message")
    warnings: list[str] = Field(default_factory=list, description="Warnings if any")


# Error Response Schema

class SchedulerOpsError(BaseModel):
    """Error response for scheduler operations."""
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Human-readable error message")
    details: dict | None = Field(None, description="Additional error details")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
