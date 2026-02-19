"""
Budget-Aware Cron Manager API Routes.

Provides endpoints for monitoring and managing AI API usage budgets.
Admin-only access required.
"""

import json
import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.api.dependencies.role_filter import require_admin
from app.schemas.budget import (
    BudgetAlert,
    BudgetConfigUpdate,
    BudgetStatus,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/budget", tags=["budget"])


class TaskCheckRequest(BaseModel):
    """Request body for checking if a task can execute within budget."""

    task_name: str
    estimated_cost_usd: float | None = None


@router.get("/status", response_model=BudgetStatus)
async def get_budget_status(
    _: None = Depends(require_admin()),
) -> BudgetStatus:
    """Return current budget status with daily/monthly spend, limits, and alerts."""
    from app.services.budget_cron_manager import BudgetCronManager

    try:
        manager = BudgetCronManager()
        status = manager.get_budget_status()

        daily = status.get("daily", {})
        monthly = status.get("monthly", {})
        alerts_raw = status.get("alerts", [])

        daily_exceeded = daily.get("spend_usd", 0) >= daily.get("budget_usd", 0)
        monthly_exceeded = monthly.get("spend_usd", 0) >= monthly.get("budget_usd", 0)

        return BudgetStatus(
            daily_spend_usd=daily.get("spend_usd", 0.0),
            monthly_spend_usd=monthly.get("spend_usd", 0.0),
            daily_limit_usd=daily.get("budget_usd", 0.0),
            monthly_limit_usd=monthly.get("budget_usd", 0.0),
            daily_utilization_pct=daily.get("utilization_pct", 0.0),
            monthly_utilization_pct=monthly.get("utilization_pct", 0.0),
            is_budget_exceeded=daily_exceeded or monthly_exceeded,
            alerts=[
                BudgetAlert(
                    level=a["level"],
                    period=a["period"],
                    current_spend_usd=a["spend_usd"],
                    limit_usd=a["budget_usd"],
                    utilization_pct=a["utilization_pct"],
                    message=a["message"],
                )
                for a in alerts_raw
            ],
            top_consumers=[],
        )
    except Exception:
        logger.exception("Failed to retrieve budget status")
        raise HTTPException(status_code=500, detail="Failed to retrieve budget status")


@router.put("/config", response_model=dict)
async def update_budget_config(
    config: BudgetConfigUpdate,
    _: None = Depends(require_admin()),
) -> dict:
    """Update budget configuration in Redis."""
    from app.services.budget_cron_manager import BudgetCronManager

    try:
        manager = BudgetCronManager()
        updates = config.model_dump(exclude_none=True)

        config_key = "ai_budget:config"
        existing = manager.redis.get(config_key)
        current = json.loads(existing) if existing else {}
        current.update(updates)
        manager.redis.set(config_key, json.dumps(current))

        return {"status": "updated", "config": current}
    except Exception:
        logger.exception("Failed to update budget config")
        raise HTTPException(status_code=500, detail="Failed to update budget config")


@router.post("/check-task", response_model=dict)
async def check_task_budget(
    request: TaskCheckRequest,
    _: None = Depends(require_admin()),
) -> dict:
    """Check if a task can execute within current budget constraints."""
    from app.services.budget_cron_manager import BudgetCronManager

    try:
        manager = BudgetCronManager()
        allowed, reason = manager.can_execute_task(
            task_name=request.task_name,
            estimated_cost_usd=request.estimated_cost_usd,
        )
        return {"allowed": allowed, "reason": reason}
    except Exception:
        logger.exception("Failed to check task budget")
        raise HTTPException(status_code=500, detail="Failed to check task budget")


@router.get("/alerts", response_model=list[BudgetAlert])
async def get_budget_alerts(
    _: None = Depends(require_admin()),
) -> list[BudgetAlert]:
    """Return current budget alerts."""
    from app.services.budget_cron_manager import BudgetCronManager

    try:
        manager = BudgetCronManager()
        alerts_data = manager.check_alerts()
        return [
            BudgetAlert(
                level=a["level"],
                period=a["period"],
                current_spend_usd=a["spend_usd"],
                limit_usd=a["budget_usd"],
                utilization_pct=a["utilization_pct"],
                message=a["message"],
            )
            for a in alerts_data
        ]
    except Exception:
        logger.exception("Failed to retrieve budget alerts")
        raise HTTPException(status_code=500, detail="Failed to retrieve budget alerts")
