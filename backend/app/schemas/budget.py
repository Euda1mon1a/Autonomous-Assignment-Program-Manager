"""Schema definitions for Budget-Aware Cron Manager."""

from datetime import datetime

from pydantic import BaseModel, Field


class BudgetAlert(BaseModel):
    """Alert triggered when budget thresholds are approached or exceeded."""

    level: str = Field(..., description="Alert severity level (warning or critical)")
    period: str = Field(..., description="Budget period (daily or monthly)")
    current_spend_usd: float = Field(
        ..., description="Current spend in USD for the period"
    )
    limit_usd: float = Field(..., description="Budget limit in USD for the period")
    utilization_pct: float = Field(
        ..., description="Budget utilization percentage (0-100)"
    )
    message: str = Field(..., description="Human-readable alert message")


class TaskCostSummary(BaseModel):
    """Per-task cost breakdown summary."""

    task_name: str = Field(..., description="Name of the scheduled task")
    call_count: int = Field(..., description="Number of times the task was invoked")
    total_cost_usd: float = Field(..., description="Total cost in USD for this task")
    avg_cost_per_call_usd: float = Field(
        ..., description="Average cost per invocation in USD"
    )


class BudgetStatus(BaseModel):
    """Current budget status and utilization metrics."""

    daily_spend_usd: float = Field(..., description="Total spend in USD for today")
    monthly_spend_usd: float = Field(
        ..., description="Total spend in USD for the current month"
    )
    daily_limit_usd: float = Field(..., description="Daily budget limit in USD")
    monthly_limit_usd: float = Field(..., description="Monthly budget limit in USD")
    daily_utilization_pct: float = Field(
        ..., description="Daily budget utilization percentage (0-100)"
    )
    monthly_utilization_pct: float = Field(
        ..., description="Monthly budget utilization percentage (0-100)"
    )
    is_budget_exceeded: bool = Field(
        ..., description="Whether any budget limit has been exceeded"
    )
    alerts: list[BudgetAlert] = Field(
        default_factory=list, description="Active budget alerts"
    )
    top_consumers: list[TaskCostSummary] = Field(
        default_factory=list, description="Top cost-consuming tasks"
    )


class BudgetConfigUpdate(BaseModel):
    """Request schema for updating budget configuration."""

    daily_limit_usd: float | None = Field(
        None, description="New daily budget limit in USD"
    )
    monthly_limit_usd: float | None = Field(
        None, description="New monthly budget limit in USD"
    )
    warning_threshold_pct: float | None = Field(
        None, description="Percentage threshold for warning alerts (e.g. 80.0)"
    )
    critical_threshold_pct: float | None = Field(
        None, description="Percentage threshold for critical alerts (e.g. 95.0)"
    )
    hard_stop: bool | None = Field(
        None,
        description="Whether to hard-stop task execution when budget is exceeded",
    )
    priority_tasks: list[str] | None = Field(
        None,
        description="Task names that are exempt from budget restrictions",
    )


class UsageLogEntry(BaseModel):
    """Individual LLM usage log entry."""

    id: int = Field(..., description="Unique log entry identifier")
    created_at: datetime = Field(..., description="Timestamp when the usage occurred")
    task_name: str = Field(..., description="Name of the task that made the LLM call")
    model_id: str = Field(..., description="Model identifier used for the call")
    input_tokens: int = Field(..., description="Number of input tokens consumed")
    output_tokens: int = Field(..., description="Number of output tokens generated")
    total_tokens: int = Field(..., description="Total tokens consumed")
    cost_usd: float = Field(..., description="Cost of the call in USD")
    status: str = Field(..., description="Call status (success, error, budget_blocked)")
    job_id: str | None = Field(None, description="Associated cron job identifier")


class UsageLogResponse(BaseModel):
    """Paginated response for usage log queries."""

    entries: list[UsageLogEntry] = Field(..., description="List of usage log entries")
    total_count: int = Field(..., description="Total number of matching entries")
    total_cost_usd: float = Field(..., description="Sum of costs for matching entries")
    period_start: datetime = Field(..., description="Start of the queried period")
    period_end: datetime = Field(..., description="End of the queried period")
