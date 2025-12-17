"""FMIT Timeline schemas for Gantt chart visualization.

Provides Pydantic models for faculty timeline data, supporting:
- Academic year timeline views
- Individual faculty assignment timelines
- Weekly workload views
- Gantt chart rendering data
- Fairness and balance metrics
"""
from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field


class WeekAssignment(BaseModel):
    """Represents a single week assignment for a faculty member."""
    week_start: date = Field(..., description="Start date of the week (Monday)")
    week_end: date = Field(..., description="End date of the week (Sunday)")
    status: str = Field(..., description="Status: completed, scheduled, tentative")
    assignment_count: int = Field(0, description="Number of assignments in this week")
    total_blocks: int = Field(0, description="Total blocks assigned in this week")


class WorkloadSummary(BaseModel):
    """Workload metrics for a faculty member."""
    total_weeks: int = Field(0, description="Total weeks assigned")
    target_weeks: float = Field(0.0, description="Target weeks for this faculty member")
    utilization_percent: float = Field(0.0, description="Percentage of target achieved")
    is_balanced: bool = Field(True, description="Whether workload is within acceptable range")
    variance_from_target: float = Field(0.0, description="Weeks above/below target (positive = over)")


class FacultyTimeline(BaseModel):
    """Timeline data for a single faculty member."""
    faculty_id: UUID = Field(..., description="Faculty member UUID")
    faculty_name: str = Field(..., description="Faculty member full name")
    weeks_assigned: list[WeekAssignment] = Field(default_factory=list, description="Weekly assignments")
    workload: WorkloadSummary = Field(..., description="Workload metrics")
    department: str | None = Field(None, description="Faculty department")
    specialty: str | None = Field(None, description="Faculty specialty")


class LoadDistribution(BaseModel):
    """Statistical distribution of workload."""
    mean: float = Field(0.0, description="Mean weeks per faculty")
    median: float = Field(0.0, description="Median weeks per faculty")
    stdev: float = Field(0.0, description="Standard deviation")
    min: float = Field(0.0, description="Minimum weeks assigned")
    max: float = Field(0.0, description="Maximum weeks assigned")


class AggregateMetrics(BaseModel):
    """System-wide fairness and balance metrics."""
    fairness_index: float = Field(0.0, description="Jain's fairness index (0-1, higher is better)")
    load_distribution: LoadDistribution = Field(..., description="Statistical distribution")
    total_faculty: int = Field(0, description="Total faculty members")
    total_weeks_scheduled: int = Field(0, description="Total weeks scheduled across all faculty")
    coverage_percentage: float = Field(0.0, description="Percentage of required coverage achieved")


class TimelineResponse(BaseModel):
    """Response for timeline endpoints."""
    timeline_data: list[FacultyTimeline] = Field(default_factory=list, description="Faculty timelines")
    aggregate_metrics: AggregateMetrics = Field(..., description="System-wide metrics")
    start_date: date = Field(..., description="Timeline start date")
    end_date: date = Field(..., description="Timeline end date")
    generated_at: datetime = Field(..., description="Timestamp when data was generated")


class GanttTask(BaseModel):
    """A single Gantt chart task (assignment period)."""
    id: str = Field(..., description="Unique task identifier")
    name: str = Field(..., description="Task name (faculty name)")
    start: date = Field(..., description="Task start date")
    end: date = Field(..., description="Task end date")
    progress: float = Field(0.0, description="Progress percentage (0-100)")
    dependencies: list[str] = Field(default_factory=list, description="IDs of dependent tasks")
    resource: str = Field(..., description="Resource name (faculty name)")
    type: str = Field("task", description="Task type: task, milestone, project")
    styles: dict = Field(default_factory=dict, description="Custom styling for the task")


class GanttGroup(BaseModel):
    """A Gantt chart group (faculty member grouping)."""
    id: str = Field(..., description="Group identifier")
    name: str = Field(..., description="Group name")
    tasks: list[GanttTask] = Field(default_factory=list, description="Tasks in this group")


class GanttDataResponse(BaseModel):
    """Response for Gantt chart data endpoint."""
    groups: list[GanttGroup] = Field(default_factory=list, description="Task groups (by faculty)")
    all_tasks: list[GanttTask] = Field(default_factory=list, description="All tasks flattened")
    date_range: dict = Field(..., description="Overall date range (start, end)")
    metadata: dict = Field(default_factory=dict, description="Additional metadata")
    generated_at: datetime = Field(..., description="Generation timestamp")


class WeeklyView(BaseModel):
    """Weekly view of assignments."""
    week_start: date = Field(..., description="Week start date (Monday)")
    week_end: date = Field(..., description="Week end date (Sunday)")
    faculty_assignments: list[dict] = Field(default_factory=list, description="Faculty assignments this week")
    total_slots: int = Field(0, description="Total FMIT slots this week")
    filled_slots: int = Field(0, description="Filled slots this week")
    coverage_percentage: float = Field(0.0, description="Coverage percentage")


class WeeklyViewResponse(BaseModel):
    """Response for weekly view endpoint."""
    week_data: WeeklyView = Field(..., description="Week data")
    adjacent_weeks: dict = Field(default_factory=dict, description="Previous and next week summaries")
    generated_at: datetime = Field(..., description="Generation timestamp")
