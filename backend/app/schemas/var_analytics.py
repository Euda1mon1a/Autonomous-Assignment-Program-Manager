"""
VaR (Value-at-Risk) Analytics Schemas.

Pydantic models for VaR calculation endpoints that support MCP tools.
Mirrors schemas in mcp-server/src/scheduler_mcp/var_risk_tools.py.
"""

from datetime import date, datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


# =============================================================================
# Enums
# =============================================================================


class RiskSeverity(str, Enum):
    """Risk severity classification."""

    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"
    EXTREME = "extreme"


# =============================================================================
# Shared Models
# =============================================================================


class VaRMetric(BaseModel):
    """Single VaR metric at a specific confidence level."""

    confidence_level: float = Field(
        ge=0.0, le=1.0, description="Confidence level (0-1)"
    )
    var_value: float = Field(description="VaR threshold value")
    interpretation: str = Field(
        description="Human-readable interpretation (e.g., 'With 95% confidence, loss <= X')"
    )
    percentile: float = Field(ge=0.0, le=100.0, description="Percentile rank")


# =============================================================================
# Coverage VaR
# =============================================================================


class CoverageVaRRequest(BaseModel):
    """Request for coverage VaR calculation."""

    start_date: date = Field(description="Start date for analysis")
    end_date: date = Field(description="End date for analysis")
    confidence_levels: list[float] = Field(
        default=[0.90, 0.95, 0.99],
        description="Confidence levels for VaR (e.g., [0.90, 0.95, 0.99])",
    )
    rotation_types: list[str] | None = Field(
        default=None,
        description="Specific rotation types to analyze (None = all)",
    )
    historical_days: int = Field(
        default=90, ge=30, le=365, description="Days of historical data to use"
    )


class CoverageVaRResponse(BaseModel):
    """Response from coverage VaR calculation."""

    analyzed_at: datetime = Field(description="Timestamp of analysis")
    period_start: date = Field(description="Analysis period start")
    period_end: date = Field(description="Analysis period end")
    historical_days: int = Field(description="Days of historical data used")
    scenarios_analyzed: int = Field(description="Number of scenarios analyzed")
    var_metrics: list[VaRMetric] = Field(description="VaR at each confidence level")
    baseline_coverage: float = Field(
        ge=0.0, le=1.0, description="Baseline coverage rate (0-1)"
    )
    worst_case_coverage: float = Field(
        ge=0.0, le=1.0, description="Worst historical coverage (0-1)"
    )
    recommendations: list[str] = Field(default_factory=list)
    severity: RiskSeverity = Field(description="Overall risk severity")
    metadata: dict[str, Any] = Field(default_factory=dict)


# =============================================================================
# Workload VaR
# =============================================================================


class WorkloadVaRRequest(BaseModel):
    """Request for workload distribution VaR calculation."""

    start_date: date = Field(description="Start date for analysis")
    end_date: date = Field(description="End date for analysis")
    confidence_levels: list[float] = Field(
        default=[0.90, 0.95, 0.99],
        description="Confidence levels for VaR",
    )
    metric: str = Field(
        default="gini_coefficient",
        description="Workload metric: gini_coefficient, max_hours, variance",
    )


class WorkloadVaRResponse(BaseModel):
    """Response from workload VaR calculation."""

    analyzed_at: datetime = Field(description="Timestamp of analysis")
    period_start: date = Field(description="Analysis period start")
    period_end: date = Field(description="Analysis period end")
    metric: str = Field(description="Workload metric analyzed")
    var_metrics: list[VaRMetric] = Field(description="VaR at each confidence level")
    baseline_value: float = Field(description="Baseline metric value")
    worst_case_value: float = Field(description="Worst historical value")
    recommendations: list[str] = Field(default_factory=list)
    severity: RiskSeverity = Field(description="Overall risk severity")
    metadata: dict[str, Any] = Field(default_factory=dict)


# =============================================================================
# Conditional VaR (Expected Shortfall)
# =============================================================================


class ConditionalVaRRequest(BaseModel):
    """Request for Conditional VaR (Expected Shortfall) calculation."""

    start_date: date = Field(description="Start date for analysis")
    end_date: date = Field(description="End date for analysis")
    confidence_level: float = Field(
        default=0.95, ge=0.5, le=0.999, description="Confidence level for CVaR"
    )
    loss_metric: str = Field(
        default="coverage_drop",
        description="Loss metric: coverage_drop, workload_spike, acgme_violations",
    )


class ConditionalVaRResponse(BaseModel):
    """Response from Conditional VaR (Expected Shortfall) calculation."""

    analyzed_at: datetime = Field(description="Timestamp of analysis")
    period_start: date = Field(description="Analysis period start")
    period_end: date = Field(description="Analysis period end")
    confidence_level: float = Field(description="Confidence level used")
    loss_metric: str = Field(description="Loss metric analyzed")
    var_value: float = Field(description="VaR at specified confidence level")
    cvar_value: float = Field(description="CVaR (expected shortfall) value")
    interpretation: str = Field(description="Human-readable interpretation")
    tail_scenarios_count: int = Field(description="Number of scenarios in tail")
    tail_mean: float = Field(description="Mean loss in tail")
    tail_std: float = Field(description="Standard deviation in tail")
    recommendations: list[str] = Field(default_factory=list)
    severity: RiskSeverity = Field(description="Overall risk severity")
    metadata: dict[str, Any] = Field(default_factory=dict)
