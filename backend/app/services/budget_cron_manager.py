"""Budget-aware cron manager for AI cost tracking and gating.

Provides Redis-based tracking of AI API spend with budget enforcement
for cron jobs. Tracks costs using Anthropic's published pricing and
gates task execution based on configurable daily/monthly budgets.
"""

import functools
import json
import logging
from datetime import UTC, datetime, timedelta
from typing import Any, Callable, Optional

import redis

from app.core.config import get_settings

logger = logging.getLogger(__name__)

# Anthropic published pricing (USD per 1K tokens)
OPUS_PRICING = {
    "claude-opus-4-6": {
        "input_per_1k_tokens": 0.015,  # $15 / 1M tokens
        "output_per_1k_tokens": 0.075,  # $75 / 1M tokens
    },
    "claude-sonnet-4-5-20250929": {
        "input_per_1k_tokens": 0.003,  # $3 / 1M tokens
        "output_per_1k_tokens": 0.015,  # $15 / 1M tokens
    },
}

# Default budget configuration
DEFAULT_DAILY_BUDGET_USD = 50.0
DEFAULT_MONTHLY_BUDGET_USD = 1000.0
DEFAULT_WARNING_THRESHOLD = 0.80
DEFAULT_CRITICAL_THRESHOLD = 0.95
DEFAULT_HARD_STOP = True
DEFAULT_PRIORITY_TASKS: list[str] = []


class BudgetCronManager:
    """Redis-based AI budget tracker and cron job gate.

    Tracks per-model token costs against configurable daily and monthly
    budgets.  Priority tasks bypass the gate; non-priority tasks are
    blocked when the budget is exceeded and hard_stop is enabled.
    """

    def __init__(self, redis_client: redis.Redis | None = None) -> None:
        settings = get_settings()

        if redis_client is not None:
            self.redis = redis_client
        else:
            self.redis = redis.from_url(
                settings.redis_url_with_password,
                decode_responses=True,
            )

        # Budget limits (from config.py AI_BUDGET_* settings)
        self.daily_budget = getattr(
            settings, "AI_BUDGET_DAILY_LIMIT_USD", DEFAULT_DAILY_BUDGET_USD
        )
        self.monthly_budget = getattr(
            settings, "AI_BUDGET_MONTHLY_LIMIT_USD", DEFAULT_MONTHLY_BUDGET_USD
        )

        # Thresholds
        self.warning_threshold = getattr(
            settings, "AI_BUDGET_WARNING_THRESHOLD", DEFAULT_WARNING_THRESHOLD
        )
        self.critical_threshold = getattr(
            settings, "AI_BUDGET_CRITICAL_THRESHOLD", DEFAULT_CRITICAL_THRESHOLD
        )

        # Enforcement
        self.hard_stop = getattr(settings, "AI_BUDGET_HARD_STOP", DEFAULT_HARD_STOP)
        self.budget_enabled = getattr(settings, "AI_BUDGET_ENABLED", True)

        # Priority tasks from comma-separated config string
        priority_str = getattr(settings, "AI_BUDGET_PRIORITY_TASKS", "")
        self.priority_tasks: list[str] = (
            [t.strip() for t in priority_str.split(",") if t.strip()]
            if priority_str
            else DEFAULT_PRIORITY_TASKS
        )

    # ------------------------------------------------------------------
    # Redis key helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _daily_key(date: str | None = None) -> str:
        date = date or datetime.now(UTC).strftime("%Y-%m-%d")
        return f"ai_budget:daily:{date}"

    @staticmethod
    def _monthly_key(month: str | None = None) -> str:
        month = month or datetime.now(UTC).strftime("%Y-%m")
        return f"ai_budget:monthly:{month}"

    def _ttl_daily(self) -> int:
        now = datetime.now(UTC)
        end_of_day = now.replace(hour=23, minute=59, second=59, microsecond=0)
        return int((end_of_day - now).total_seconds()) + 3600  # +1 h buffer

    def _ttl_monthly(self) -> int:
        now = datetime.now(UTC)
        if now.month == 12:
            next_month = now.replace(year=now.year + 1, month=1, day=1)
        else:
            next_month = now.replace(month=now.month + 1, day=1)
        end_of_month = next_month - timedelta(seconds=1)
        return int((end_of_month - now).total_seconds()) + 86400  # +1 d buffer

    # ------------------------------------------------------------------
    # Cost calculation
    # ------------------------------------------------------------------

    @staticmethod
    def calculate_cost(model_id: str, input_tokens: int, output_tokens: int) -> float:
        """Return the USD cost for the given token counts.

        Falls back to Opus pricing if *model_id* is not in the pricing
        table.
        """
        pricing = OPUS_PRICING.get(model_id, OPUS_PRICING["claude-opus-4-6"])
        input_cost = (input_tokens / 1000.0) * pricing["input_per_1k_tokens"]
        output_cost = (output_tokens / 1000.0) * pricing["output_per_1k_tokens"]
        return round(input_cost + output_cost, 6)

    # ------------------------------------------------------------------
    # Usage recording
    # ------------------------------------------------------------------

    def record_usage(
        self,
        task_name: str,
        model_id: str,
        input_tokens: int,
        output_tokens: int,
        job_id: str | None = None,
    ) -> dict:
        """Record a completed AI call and return a usage summary.

        Atomically increments Redis daily and monthly spend counters and
        appends an entry to the daily log list for auditing.
        """
        cost = self.calculate_cost(model_id, input_tokens, output_tokens)

        daily_key = self._daily_key()
        monthly_key = self._monthly_key()

        pipe = self.redis.pipeline()
        pipe.incrbyfloat(daily_key, cost)
        pipe.incrbyfloat(monthly_key, cost)
        pipe.expire(daily_key, self._ttl_daily())
        pipe.expire(monthly_key, self._ttl_monthly())
        results = pipe.execute()

        daily_total = float(results[0])
        monthly_total = float(results[1])

        # Append audit entry
        log_entry = {
            "timestamp": datetime.now(UTC).isoformat(),
            "task_name": task_name,
            "model_id": model_id,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "cost_usd": cost,
            "job_id": job_id,
        }
        log_key = f"ai_budget:log:{datetime.now(UTC).strftime('%Y-%m-%d')}"
        self.redis.rpush(log_key, json.dumps(log_entry))
        self.redis.expire(log_key, self._ttl_daily())

        logger.info(
            "Recorded AI usage: task=%s model=%s cost=$%.4f "
            "daily_total=$%.2f monthly_total=$%.2f",
            task_name,
            model_id,
            cost,
            daily_total,
            monthly_total,
        )

        return {
            "task_name": task_name,
            "model_id": model_id,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "cost_usd": cost,
            "daily_total_usd": daily_total,
            "monthly_total_usd": monthly_total,
        }

    # ------------------------------------------------------------------
    # Spend queries
    # ------------------------------------------------------------------

    def get_current_spend(self, period: str = "daily") -> float:
        """Return the current spend for the given period."""
        if period == "monthly":
            key = self._monthly_key()
        else:
            key = self._daily_key()
        value = self.redis.get(key)
        return float(value) if value else 0.0

    def get_budget_status(self) -> dict:
        """Return a full budget status report."""
        daily_spend = self.get_current_spend("daily")
        monthly_spend = self.get_current_spend("monthly")

        daily_util = (
            (daily_spend / self.daily_budget * 100) if self.daily_budget > 0 else 0.0
        )
        monthly_util = (
            (monthly_spend / self.monthly_budget * 100)
            if self.monthly_budget > 0
            else 0.0
        )

        alerts = self.check_alerts()

        return {
            "daily": {
                "spend_usd": round(daily_spend, 4),
                "budget_usd": self.daily_budget,
                "utilization_pct": round(daily_util, 2),
                "remaining_usd": round(max(0, self.daily_budget - daily_spend), 4),
            },
            "monthly": {
                "spend_usd": round(monthly_spend, 4),
                "budget_usd": self.monthly_budget,
                "utilization_pct": round(monthly_util, 2),
                "remaining_usd": round(max(0, self.monthly_budget - monthly_spend), 4),
            },
            "hard_stop": self.hard_stop,
            "alerts": alerts,
        }

    # ------------------------------------------------------------------
    # Budget gate
    # ------------------------------------------------------------------

    def can_execute_task(
        self,
        task_name: str,
        estimated_cost_usd: float | None = None,
    ) -> tuple[bool, str]:
        """Check whether a task is allowed to run within budget.

        Returns:
            (allowed, reason) where *reason* explains the decision.
        """
        # If budget enforcement is disabled, always allow
        if not self.budget_enabled:
            return True, "Budget enforcement is disabled."

        # Priority tasks always proceed
        if task_name in self.priority_tasks:
            return True, f"Task '{task_name}' is a priority task; budget gate bypassed."

        daily_spend = self.get_current_spend("daily")
        monthly_spend = self.get_current_spend("monthly")

        effective_daily = daily_spend + (estimated_cost_usd or 0.0)
        effective_monthly = monthly_spend + (estimated_cost_usd or 0.0)

        # Check daily budget
        if effective_daily > self.daily_budget:
            reason = (
                f"Daily budget exceeded: ${daily_spend:.2f} spent "
                f"(limit ${self.daily_budget:.2f})"
            )
            if self.hard_stop:
                logger.warning("Budget gate BLOCKED task '%s': %s", task_name, reason)
                return False, reason
            logger.warning(
                "Budget gate WARNING for task '%s': %s (hard_stop disabled)",
                task_name,
                reason,
            )

        # Check monthly budget
        if effective_monthly > self.monthly_budget:
            reason = (
                f"Monthly budget exceeded: ${monthly_spend:.2f} spent "
                f"(limit ${self.monthly_budget:.2f})"
            )
            if self.hard_stop:
                logger.warning("Budget gate BLOCKED task '%s': %s", task_name, reason)
                return False, reason
            logger.warning(
                "Budget gate WARNING for task '%s': %s (hard_stop disabled)",
                task_name,
                reason,
            )

        return True, "Within budget."

    # ------------------------------------------------------------------
    # Alerting
    # ------------------------------------------------------------------

    def check_alerts(self) -> list[dict]:
        """Return a list of active budget alerts."""
        alerts: list[dict] = []

        for period, budget in [
            ("daily", self.daily_budget),
            ("monthly", self.monthly_budget),
        ]:
            if budget <= 0:
                continue
            spend = self.get_current_spend(period)
            utilization = spend / budget

            if utilization >= self.critical_threshold:
                alerts.append(
                    {
                        "level": "critical",
                        "period": period,
                        "spend_usd": round(spend, 4),
                        "budget_usd": budget,
                        "utilization_pct": round(utilization * 100, 2),
                        "message": (
                            f"CRITICAL: {period.capitalize()} AI spend at "
                            f"{utilization * 100:.1f}% of budget "
                            f"(${spend:.2f} / ${budget:.2f})"
                        ),
                    }
                )
            elif utilization >= self.warning_threshold:
                alerts.append(
                    {
                        "level": "warning",
                        "period": period,
                        "spend_usd": round(spend, 4),
                        "budget_usd": budget,
                        "utilization_pct": round(utilization * 100, 2),
                        "message": (
                            f"WARNING: {period.capitalize()} AI spend at "
                            f"{utilization * 100:.1f}% of budget "
                            f"(${spend:.2f} / ${budget:.2f})"
                        ),
                    }
                )

        return alerts

    # ------------------------------------------------------------------
    # Decorator
    # ------------------------------------------------------------------

    def budget_aware_task(
        self,
        task_name: str,
        model_id: str = "claude-opus-4-6",
    ) -> Callable:
        """Decorator factory that wraps a Celery task with budget checks.

        Usage::

            manager = BudgetCronManager()

            @manager.budget_aware_task("nightly_summary", model_id="claude-opus-4-6")
            def nightly_summary():
                ...
        """

        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            def wrapper(*args: Any, **kwargs: Any) -> Any:
                allowed, reason = self.can_execute_task(task_name)
                if not allowed:
                    logger.warning("Skipping task '%s': %s", task_name, reason)
                    return {"status": "blocked", "reason": reason}

                logger.info("Executing budget-gated task '%s'", task_name)
                result = func(*args, **kwargs)

                # If the wrapped function returns token counts, record them
                if isinstance(result, dict):
                    input_tokens = result.get("input_tokens", 0)
                    output_tokens = result.get("output_tokens", 0)
                    used_model = result.get("model_id", model_id)
                    job_id = result.get("job_id")
                    if input_tokens or output_tokens:
                        self.record_usage(
                            task_name,
                            used_model,
                            input_tokens,
                            output_tokens,
                            job_id=job_id,
                        )

                return result

            return wrapper

        return decorator
