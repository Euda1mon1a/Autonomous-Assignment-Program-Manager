"""AI usage and budget models for budget-aware cron management.

Tracks Opus API usage costs and enforces budget limits to prevent
runaway spending on AI-powered cron jobs.
"""

from datetime import datetime, UTC

from sqlalchemy import Boolean, Column, DateTime, Float, Index, Integer, String, Text

from app.db.base import Base


class AIUsageLog(Base):
    """
    Logs every Opus API call with token and cost tracking.

    Used for budget enforcement, cost analysis, and usage auditing.
    Each row represents a single API call to an AI model.

    Attributes:
        id: Auto-incrementing primary key.
        created_at: UTC timestamp of the API call.
        task_name: Celery task or function name that made the call.
        model_id: Model identifier (e.g. "claude-opus-4-6").
        input_tokens: Number of input tokens consumed.
        output_tokens: Number of output tokens generated.
        total_tokens: Total tokens (input + output).
        cost_usd: Calculated cost in USD for this call.
        job_id: Celery task ID if triggered from a cron job.
        status: Call outcome - "success", "error", or "budget_blocked".
        metadata_json: Optional JSON string for extra context.
    """

    __tablename__ = "ai_usage_log"

    id = Column(Integer, primary_key=True, autoincrement=True)
    created_at = Column(
        DateTime, default=lambda: datetime.now(UTC), nullable=False, index=True
    )
    task_name = Column(String(255), nullable=False, index=True)
    model_id = Column(String(100), nullable=False)
    input_tokens = Column(Integer, nullable=False)
    output_tokens = Column(Integer, nullable=False)
    total_tokens = Column(Integer, nullable=False)
    cost_usd = Column(Float, nullable=False)
    job_id = Column(String(255), nullable=True)
    status = Column(String(50), nullable=False)
    metadata_json = Column(Text, nullable=True)

    __table_args__ = (Index("ix_ai_usage_log_task_created", "task_name", "created_at"),)

    def __repr__(self):
        return (
            f"<AIUsageLog(id={self.id}, task='{self.task_name}', "
            f"model='{self.model_id}', cost=${self.cost_usd:.4f}, "
            f"status='{self.status}')>"
        )


class AIBudgetConfig(Base):
    """
    Budget configuration for AI API spending limits.

    Controls spending thresholds and hard-stop behavior for
    budget-aware cron job execution.

    Attributes:
        id: Auto-incrementing primary key.
        created_at: UTC timestamp of record creation.
        updated_at: UTC timestamp of last modification.
        budget_period: Period type - "daily" or "monthly".
        budget_limit_usd: Maximum spend in USD for the period.
        warning_threshold_pct: Fraction (0-1) at which to warn (default 0.80).
        critical_threshold_pct: Fraction (0-1) at which to escalate (default 0.95).
        hard_stop: If True, block jobs when budget is exceeded (default True).
        is_active: Whether this budget config is active (default True).
        priority_tasks: JSON list of task names that bypass budget limits.
    """

    __tablename__ = "ai_budget_config"

    id = Column(Integer, primary_key=True, autoincrement=True)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC), nullable=False)
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )
    budget_period = Column(String(50), nullable=False)
    budget_limit_usd = Column(Float, nullable=False)
    warning_threshold_pct = Column(Float, nullable=False, default=0.80)
    critical_threshold_pct = Column(Float, nullable=False, default=0.95)
    hard_stop = Column(Boolean, nullable=False, default=True)
    is_active = Column(Boolean, nullable=False, default=True)
    priority_tasks = Column(Text, nullable=True)

    def __repr__(self):
        return (
            f"<AIBudgetConfig(id={self.id}, period='{self.budget_period}', "
            f"limit=${self.budget_limit_usd:.2f}, active={self.is_active})>"
        )
