"""
Value-at-Risk (VaR) MCP Tools for Schedule Vulnerability Analysis.

Exposes financial risk management concepts as MCP tools for quantifying
worst-case schedule disruption scenarios. Provides probabilistic bounds
on coverage degradation and workload distribution failures.

Tools Provided:
1. calculate_coverage_var - VaR for coverage metrics at various confidence levels
2. calculate_workload_var - VaR for workload distribution inequality
3. simulate_disruption_scenarios - Monte Carlo simulation of random disruptions
4. calculate_conditional_var - Expected shortfall (CVaR) in worst-case scenarios

Scientific Foundations:
- Value-at-Risk (VaR): Quantile-based risk measure from finance
- Conditional VaR (CVaR/ES): Expected loss in tail scenarios
- Monte Carlo Simulation: Stochastic scenario generation
- Bootstrap Resampling: Non-parametric confidence intervals

Complements N-1/N-2 contingency analysis with probabilistic risk quantification.
"""

from __future__ import annotations

import logging
import random
from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


# =============================================================================
# Enums and Constants
# =============================================================================


class ConfidenceLevel(str, Enum):
    """Standard confidence levels for VaR calculation."""

    LEVEL_90 = "90"
    LEVEL_95 = "95"
    LEVEL_99 = "99"
    LEVEL_99_9 = "99.9"


class DisruptionType(str, Enum):
    """Types of disruptions to simulate."""

    RANDOM_ABSENCE = "random_absence"
    MASS_CASUALTY = "mass_casualty"
    DEPLOYMENT = "deployment"
    ILLNESS_CLUSTER = "illness_cluster"
    EQUIPMENT_FAILURE = "equipment_failure"
    WEATHER_EVENT = "weather_event"


class RiskSeverity(str, Enum):
    """Risk severity classification."""

    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"
    EXTREME = "extreme"


# =============================================================================
# Request Models
# =============================================================================


class CoverageVaRRequest(BaseModel):
    """Request for coverage VaR calculation."""

    start_date: str = Field(description="Start date for analysis (YYYY-MM-DD)")
    end_date: str = Field(description="End date for analysis (YYYY-MM-DD)")
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


class WorkloadVaRRequest(BaseModel):
    """Request for workload distribution VaR calculation."""

    start_date: str = Field(description="Start date for analysis (YYYY-MM-DD)")
    end_date: str = Field(description="End date for analysis (YYYY-MM-DD)")
    confidence_levels: list[float] = Field(
        default=[0.90, 0.95, 0.99],
        description="Confidence levels for VaR",
    )
    metric: str = Field(
        default="gini_coefficient",
        description="Workload metric: gini_coefficient, max_hours, variance",
    )


class DisruptionSimulationRequest(BaseModel):
    """Request for Monte Carlo disruption simulation."""

    start_date: str = Field(description="Start date for simulation (YYYY-MM-DD)")
    end_date: str = Field(description="End date for simulation (YYYY-MM-DD)")
    num_simulations: int = Field(
        default=1000, ge=100, le=10000, description="Number of Monte Carlo scenarios"
    )
    disruption_types: list[DisruptionType] = Field(
        default=[DisruptionType.RANDOM_ABSENCE],
        description="Types of disruptions to simulate",
    )
    disruption_probability: float = Field(
        default=0.05,
        ge=0.0,
        le=1.0,
        description="Probability of disruption per person per day",
    )
    seed: int | None = Field(default=None, description="Random seed for reproducibility")


class ConditionalVaRRequest(BaseModel):
    """Request for Conditional VaR (Expected Shortfall) calculation."""

    start_date: str = Field(description="Start date for analysis (YYYY-MM-DD)")
    end_date: str = Field(description="End date for analysis (YYYY-MM-DD)")
    confidence_level: float = Field(
        default=0.95, ge=0.5, le=0.999, description="Confidence level for CVaR"
    )
    loss_metric: str = Field(
        default="coverage_drop",
        description="Loss metric: coverage_drop, workload_spike, acgme_violations",
    )


# =============================================================================
# Response Models
# =============================================================================


class VaRMetric(BaseModel):
    """Single VaR metric at a specific confidence level."""

    confidence_level: float = Field(ge=0.0, le=1.0, description="Confidence level (0-1)")
    var_value: float = Field(description="VaR threshold value")
    interpretation: str = Field(
        description="Human-readable interpretation (e.g., 'With 95% confidence, loss <= X')"
    )
    percentile: float = Field(ge=0.0, le=100.0, description="Percentile rank")


class CoverageVaRResponse(BaseModel):
    """Response from coverage VaR calculation."""

    analyzed_at: str = Field(description="ISO timestamp of analysis")
    period_start: str = Field(description="Analysis period start")
    period_end: str = Field(description="Analysis period end")
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


class WorkloadVaRResponse(BaseModel):
    """Response from workload VaR calculation."""

    analyzed_at: str = Field(description="ISO timestamp of analysis")
    period_start: str = Field(description="Analysis period start")
    period_end: str = Field(description="Analysis period end")
    metric: str = Field(description="Workload metric analyzed")
    var_metrics: list[VaRMetric] = Field(description="VaR at each confidence level")
    baseline_value: float = Field(description="Baseline metric value")
    worst_case_value: float = Field(description="Worst historical value")
    recommendations: list[str] = Field(default_factory=list)
    severity: RiskSeverity = Field(description="Overall risk severity")
    metadata: dict[str, Any] = Field(default_factory=dict)


class DisruptionScenario(BaseModel):
    """Single disruption scenario result."""

    scenario_id: int = Field(description="Scenario number")
    disruptions_count: int = Field(description="Number of disruptions in scenario")
    coverage_impact: float = Field(
        ge=-1.0, le=1.0, description="Coverage change (-1 to 1)"
    )
    acgme_violations: int = Field(ge=0, description="ACGME violations triggered")
    workload_spike: float = Field(ge=0.0, description="Maximum workload increase")
    disrupted_persons: list[str] = Field(
        default_factory=list, description="Anonymized IDs of disrupted persons"
    )


class DisruptionSimulationResponse(BaseModel):
    """Response from Monte Carlo disruption simulation."""

    analyzed_at: str = Field(description="ISO timestamp of analysis")
    period_start: str = Field(description="Simulation period start")
    period_end: str = Field(description="Simulation period end")
    num_simulations: int = Field(description="Number of scenarios simulated")
    disruption_types: list[str] = Field(description="Types of disruptions simulated")
    sample_scenarios: list[DisruptionScenario] = Field(
        description="Sample of scenarios (max 10)"
    )
    var_95_coverage_drop: float = Field(
        description="95% VaR for coverage drop (0-1)"
    )
    var_99_coverage_drop: float = Field(
        description="99% VaR for coverage drop (0-1)"
    )
    mean_coverage_drop: float = Field(description="Average coverage drop across scenarios")
    worst_case_scenario: DisruptionScenario = Field(description="Worst-case scenario")
    recommendations: list[str] = Field(default_factory=list)
    severity: RiskSeverity = Field(description="Overall risk severity")
    metadata: dict[str, Any] = Field(default_factory=dict)


class ConditionalVaRResponse(BaseModel):
    """Response from Conditional VaR (Expected Shortfall) calculation."""

    analyzed_at: str = Field(description="ISO timestamp of analysis")
    period_start: str = Field(description="Analysis period start")
    period_end: str = Field(description="Analysis period end")
    confidence_level: float = Field(description="Confidence level used")
    loss_metric: str = Field(description="Loss metric analyzed")
    var_value: float = Field(description="VaR at specified confidence level")
    cvar_value: float = Field(description="CVaR (expected shortfall) value")
    interpretation: str = Field(
        description=(
            "Human-readable interpretation "
            "(e.g., 'Average loss in worst 5% of cases is X')"
        )
    )
    tail_scenarios_count: int = Field(description="Number of scenarios in tail")
    tail_mean: float = Field(description="Mean loss in tail")
    tail_std: float = Field(description="Standard deviation in tail")
    recommendations: list[str] = Field(default_factory=list)
    severity: RiskSeverity = Field(description="Overall risk severity")
    metadata: dict[str, Any] = Field(default_factory=dict)


# =============================================================================
# Core VaR Calculation Functions
# =============================================================================


def calculate_var(losses: list[float], confidence: float) -> float:
    """
    Calculate Value-at-Risk at specified confidence level.

    VaR is the maximum loss not exceeded with a given probability.
    For example, 95% VaR is the loss threshold such that only 5% of
    scenarios exceed this loss.

    Args:
        losses: List of loss values (higher = worse)
        confidence: Confidence level (e.g., 0.95 for 95%)

    Returns:
        VaR value at the specified confidence level
    """
    if not losses:
        return 0.0

    sorted_losses = sorted(losses)
    index = int((1 - confidence) * len(losses))
    # Ensure index is within bounds
    index = max(0, min(index, len(sorted_losses) - 1))
    return sorted_losses[index]


def calculate_cvar(losses: list[float], confidence: float) -> tuple[float, float]:
    """
    Calculate Conditional VaR (Expected Shortfall).

    CVaR is the expected loss given that the loss exceeds the VaR.
    It provides information about the tail risk beyond VaR.

    Args:
        losses: List of loss values
        confidence: Confidence level (e.g., 0.95 for 95%)

    Returns:
        Tuple of (VaR, CVaR) at the specified confidence level
    """
    if not losses:
        return 0.0, 0.0

    var = calculate_var(losses, confidence)
    tail_losses = [loss for loss in losses if loss >= var]

    if not tail_losses:
        return var, var

    cvar = sum(tail_losses) / len(tail_losses)
    return var, cvar


def classify_risk_severity(
    var_value: float, threshold_moderate: float, threshold_high: float
) -> RiskSeverity:
    """
    Classify risk severity based on VaR value.

    Args:
        var_value: VaR value to classify
        threshold_moderate: Threshold for moderate risk
        threshold_high: Threshold for high risk

    Returns:
        Risk severity classification
    """
    if var_value >= threshold_high * 1.5:
        return RiskSeverity.EXTREME
    elif var_value >= threshold_high:
        return RiskSeverity.CRITICAL
    elif var_value >= threshold_moderate:
        return RiskSeverity.HIGH
    elif var_value >= threshold_moderate * 0.5:
        return RiskSeverity.MODERATE
    else:
        return RiskSeverity.LOW


# =============================================================================
# Tool Implementation Functions
# =============================================================================


async def calculate_coverage_var(request: CoverageVaRRequest) -> CoverageVaRResponse:
    """
    Calculate Value-at-Risk for coverage metrics.

    Analyzes historical coverage data to determine probabilistic bounds
    on coverage degradation. Answers: "With 95% confidence, coverage
    won't drop below X%"

    Args:
        request: Coverage VaR request parameters

    Returns:
        Coverage VaR response with risk metrics
    """
    logger.info(
        "Calculating coverage VaR",
        extra={
            "start_date": request.start_date,
            "end_date": request.end_date,
            "confidence_levels": request.confidence_levels,
        },
    )

    now = datetime.utcnow()

    try:
        # Import API client for backend communication
        from .api_client import get_api_client

        client = get_api_client()

        # Call backend coverage analytics endpoint
        result = await client.post(
            "/api/v1/analytics/coverage-var",
            json={
                "start_date": request.start_date,
                "end_date": request.end_date,
                "confidence_levels": request.confidence_levels,
                "rotation_types": request.rotation_types,
                "historical_days": request.historical_days,
            },
        )

        if result is not None:
            return CoverageVaRResponse(**result)

    except Exception as e:
        logger.warning(
            f"API call failed, using placeholder: {e}",
            extra={"endpoint": "/api/v1/analytics/coverage-var"},
        )

    # Placeholder implementation using Monte Carlo
    return _calculate_coverage_var_placeholder(request)


def _calculate_coverage_var_placeholder(request: CoverageVaRRequest) -> CoverageVaRResponse:
    """
    Placeholder implementation of coverage VaR calculation.

    Generates synthetic coverage drop scenarios for demonstration.
    """
    # Simulate historical coverage drops
    random.seed(42)  # Reproducible for demo
    num_scenarios = request.historical_days

    # Generate synthetic coverage drops (as percentages)
    # Most scenarios have small drops, some have larger drops (heavy tail)
    coverage_drops = []
    for _ in range(num_scenarios):
        # Exponential distribution with mean 5% drop
        drop = random.expovariate(1.0 / 0.05)
        # Cap at 50% maximum drop
        drop = min(drop, 0.50)
        coverage_drops.append(drop)

    # Calculate VaR at each confidence level
    var_metrics = []
    for confidence in request.confidence_levels:
        var_value = calculate_var(coverage_drops, confidence)
        var_metrics.append(
            VaRMetric(
                confidence_level=confidence,
                var_value=var_value,
                interpretation=(
                    f"With {confidence*100:.1f}% confidence, "
                    f"coverage won't drop more than {var_value*100:.1f}%"
                ),
                percentile=(1 - confidence) * 100,
            )
        )

    baseline_coverage = 0.95  # 95% baseline
    worst_case_coverage = baseline_coverage - max(coverage_drops)

    # Determine severity based on 95% VaR
    var_95 = next((m.var_value for m in var_metrics if m.confidence_level == 0.95), 0.0)
    severity = classify_risk_severity(var_95, threshold_moderate=0.10, threshold_high=0.20)

    recommendations = _generate_coverage_recommendations(var_95, severity)

    return CoverageVaRResponse(
        analyzed_at=datetime.utcnow().isoformat(),
        period_start=request.start_date,
        period_end=request.end_date,
        historical_days=request.historical_days,
        scenarios_analyzed=num_scenarios,
        var_metrics=var_metrics,
        baseline_coverage=baseline_coverage,
        worst_case_coverage=worst_case_coverage,
        recommendations=recommendations,
        severity=severity,
        metadata={
            "source": "placeholder",
            "note": "Using synthetic data for demonstration",
        },
    )


async def calculate_workload_var(request: WorkloadVaRRequest) -> WorkloadVaRResponse:
    """
    Calculate Value-at-Risk for workload distribution metrics.

    Analyzes workload inequality (e.g., Gini coefficient) to quantify
    risk of unfair workload distribution.

    Args:
        request: Workload VaR request parameters

    Returns:
        Workload VaR response with risk metrics
    """
    logger.info(
        "Calculating workload VaR",
        extra={
            "start_date": request.start_date,
            "end_date": request.end_date,
            "metric": request.metric,
        },
    )

    try:
        from .api_client import get_api_client

        client = get_api_client()

        result = await client.post(
            "/api/v1/analytics/workload-var",
            json={
                "start_date": request.start_date,
                "end_date": request.end_date,
                "confidence_levels": request.confidence_levels,
                "metric": request.metric,
            },
        )

        if result is not None:
            return WorkloadVaRResponse(**result)

    except Exception as e:
        logger.warning(f"API call failed, using placeholder: {e}")

    return _calculate_workload_var_placeholder(request)


def _calculate_workload_var_placeholder(request: WorkloadVaRRequest) -> WorkloadVaRResponse:
    """Placeholder implementation of workload VaR calculation."""
    random.seed(42)
    num_scenarios = 90  # 90 days of history

    # Generate synthetic workload metric values
    # Gini coefficient: 0 = perfect equality, 1 = maximum inequality
    if request.metric == "gini_coefficient":
        metric_values = [random.betavariate(2, 5) for _ in range(num_scenarios)]
        baseline_value = 0.15
        threshold_moderate = 0.25
        threshold_high = 0.35
    elif request.metric == "max_hours":
        metric_values = [random.normalvariate(65, 10) for _ in range(num_scenarios)]
        baseline_value = 60.0
        threshold_moderate = 70.0
        threshold_high = 75.0
    else:  # variance
        metric_values = [random.gammavariate(2, 50) for _ in range(num_scenarios)]
        baseline_value = 80.0
        threshold_moderate = 120.0
        threshold_high = 150.0

    var_metrics = []
    for confidence in request.confidence_levels:
        var_value = calculate_var(metric_values, confidence)
        var_metrics.append(
            VaRMetric(
                confidence_level=confidence,
                var_value=var_value,
                interpretation=(
                    f"With {confidence*100:.1f}% confidence, "
                    f"{request.metric} won't exceed {var_value:.2f}"
                ),
                percentile=(1 - confidence) * 100,
            )
        )

    var_95 = next((m.var_value for m in var_metrics if m.confidence_level == 0.95), 0.0)
    severity = classify_risk_severity(var_95, threshold_moderate, threshold_high)

    return WorkloadVaRResponse(
        analyzed_at=datetime.utcnow().isoformat(),
        period_start=request.start_date,
        period_end=request.end_date,
        metric=request.metric,
        var_metrics=var_metrics,
        baseline_value=baseline_value,
        worst_case_value=max(metric_values),
        recommendations=_generate_workload_recommendations(var_95, request.metric, severity),
        severity=severity,
        metadata={"source": "placeholder"},
    )


async def simulate_disruption_scenarios(
    request: DisruptionSimulationRequest,
) -> DisruptionSimulationResponse:
    """
    Run Monte Carlo simulation of schedule disruption scenarios.

    Simulates random disruptions (absences, deployments, etc.) to
    quantify their impact on coverage and workload.

    Args:
        request: Simulation request parameters

    Returns:
        Simulation results with VaR metrics
    """
    logger.info(
        "Running disruption simulation",
        extra={
            "num_simulations": request.num_simulations,
            "disruption_types": [dt.value for dt in request.disruption_types],
        },
    )

    if request.seed is not None:
        random.seed(request.seed)

    # Run Monte Carlo simulation
    scenarios = []
    coverage_drops = []

    for scenario_id in range(request.num_simulations):
        scenario = _simulate_single_disruption(
            scenario_id, request.disruption_probability, request.disruption_types
        )
        scenarios.append(scenario)
        coverage_drops.append(scenario.coverage_impact)

    # Calculate VaR
    var_95 = calculate_var(coverage_drops, 0.95)
    var_99 = calculate_var(coverage_drops, 0.99)
    mean_drop = sum(coverage_drops) / len(coverage_drops) if coverage_drops else 0.0

    # Find worst-case scenario
    worst_case = max(scenarios, key=lambda s: s.coverage_impact)

    severity = classify_risk_severity(var_95, threshold_moderate=0.15, threshold_high=0.30)

    return DisruptionSimulationResponse(
        analyzed_at=datetime.utcnow().isoformat(),
        period_start=request.start_date,
        period_end=request.end_date,
        num_simulations=request.num_simulations,
        disruption_types=[dt.value for dt in request.disruption_types],
        sample_scenarios=scenarios[:10],  # First 10 scenarios
        var_95_coverage_drop=var_95,
        var_99_coverage_drop=var_99,
        mean_coverage_drop=mean_drop,
        worst_case_scenario=worst_case,
        recommendations=_generate_simulation_recommendations(var_95, var_99, severity),
        severity=severity,
        metadata={
            "seed": request.seed,
            "source": "monte_carlo_simulation",
        },
    )


def _simulate_single_disruption(
    scenario_id: int, probability: float, disruption_types: list[DisruptionType]
) -> DisruptionScenario:
    """Simulate a single disruption scenario."""
    num_persons = 20  # Simulate 20 persons
    num_disruptions = 0
    disrupted_persons = []

    for person_id in range(num_persons):
        if random.random() < probability:
            num_disruptions += 1
            disrupted_persons.append(f"PERSON-{person_id:03d}")

    # Coverage impact proportional to disruptions
    coverage_impact = min(num_disruptions / num_persons, 1.0)

    # ACGME violations increase with coverage drop
    acgme_violations = int(coverage_impact * 10) if coverage_impact > 0.15 else 0

    # Workload spike on remaining persons
    if num_disruptions > 0:
        workload_spike = num_disruptions / (num_persons - num_disruptions)
    else:
        workload_spike = 0.0

    return DisruptionScenario(
        scenario_id=scenario_id,
        disruptions_count=num_disruptions,
        coverage_impact=coverage_impact,
        acgme_violations=acgme_violations,
        workload_spike=workload_spike,
        disrupted_persons=disrupted_persons,
    )


async def calculate_conditional_var(
    request: ConditionalVaRRequest,
) -> ConditionalVaRResponse:
    """
    Calculate Conditional VaR (Expected Shortfall).

    CVaR measures the average loss in the worst-case scenarios
    (beyond the VaR threshold). Provides insight into tail risk.

    Args:
        request: CVaR request parameters

    Returns:
        CVaR response with tail risk metrics
    """
    logger.info(
        "Calculating CVaR",
        extra={
            "confidence_level": request.confidence_level,
            "loss_metric": request.loss_metric,
        },
    )

    try:
        from .api_client import get_api_client

        client = get_api_client()

        result = await client.post(
            "/api/v1/analytics/conditional-var",
            json={
                "start_date": request.start_date,
                "end_date": request.end_date,
                "confidence_level": request.confidence_level,
                "loss_metric": request.loss_metric,
            },
        )

        if result is not None:
            return ConditionalVaRResponse(**result)

    except Exception as e:
        logger.warning(f"API call failed, using placeholder: {e}")

    return _calculate_conditional_var_placeholder(request)


def _calculate_conditional_var_placeholder(
    request: ConditionalVaRRequest,
) -> ConditionalVaRResponse:
    """Placeholder implementation of CVaR calculation."""
    random.seed(42)
    num_scenarios = 1000

    # Generate loss scenarios based on metric
    if request.loss_metric == "coverage_drop":
        losses = [random.expovariate(1.0 / 0.08) for _ in range(num_scenarios)]
        losses = [min(loss, 0.60) for loss in losses]  # Cap at 60%
    elif request.loss_metric == "workload_spike":
        losses = [random.gammavariate(2, 0.15) for _ in range(num_scenarios)]
    else:  # acgme_violations
        losses = [random.poisson(3) for _ in range(num_scenarios)]

    # Calculate VaR and CVaR
    var_value, cvar_value = calculate_cvar(losses, request.confidence_level)

    # Tail statistics
    tail_losses = [loss for loss in losses if loss >= var_value]
    tail_mean = sum(tail_losses) / len(tail_losses) if tail_losses else 0.0
    tail_std = (
        (sum((x - tail_mean) ** 2 for x in tail_losses) / len(tail_losses)) ** 0.5
        if tail_losses
        else 0.0
    )

    severity = classify_risk_severity(cvar_value, threshold_moderate=0.12, threshold_high=0.25)

    alpha_pct = (1 - request.confidence_level) * 100

    return ConditionalVaRResponse(
        analyzed_at=datetime.utcnow().isoformat(),
        period_start=request.start_date,
        period_end=request.end_date,
        confidence_level=request.confidence_level,
        loss_metric=request.loss_metric,
        var_value=var_value,
        cvar_value=cvar_value,
        interpretation=(
            f"In the worst {alpha_pct:.1f}% of scenarios, "
            f"average {request.loss_metric} is {cvar_value:.2f}"
        ),
        tail_scenarios_count=len(tail_losses),
        tail_mean=tail_mean,
        tail_std=tail_std,
        recommendations=_generate_cvar_recommendations(cvar_value, request.loss_metric, severity),
        severity=severity,
        metadata={"source": "placeholder"},
    )


# =============================================================================
# Recommendation Generators
# =============================================================================


def _generate_coverage_recommendations(var_95: float, severity: RiskSeverity) -> list[str]:
    """Generate coverage VaR recommendations."""
    recommendations = []

    if severity in (RiskSeverity.CRITICAL, RiskSeverity.EXTREME):
        recommendations.append(
            "URGENT: Implement N+1 contingency staffing immediately"
        )
        recommendations.append(
            "Review and update on-call backup rosters"
        )

    if var_95 > 0.15:
        recommendations.append(
            "Consider cross-training faculty to increase coverage flexibility"
        )

    if var_95 > 0.10:
        recommendations.append(
            "Establish formal absence notification protocol with 48h minimum notice"
        )

    recommendations.append(
        "Monitor coverage metrics weekly with automated alerts"
    )

    return recommendations


def _generate_workload_recommendations(
    var_95: float, metric: str, severity: RiskSeverity
) -> list[str]:
    """Generate workload VaR recommendations."""
    recommendations = []

    if metric == "gini_coefficient" and var_95 > 0.30:
        recommendations.append(
            "High workload inequality detected - review assignment algorithm"
        )
        recommendations.append(
            "Consider implementing workload balancing constraints"
        )

    if metric == "max_hours" and var_95 > 75:
        recommendations.append(
            "Individual work hour spikes approaching ACGME limits"
        )
        recommendations.append(
            "Implement proactive workload monitoring and redistribution"
        )

    if severity in (RiskSeverity.HIGH, RiskSeverity.CRITICAL):
        recommendations.append(
            "Review recent schedule changes for workload imbalances"
        )

    return recommendations


def _generate_simulation_recommendations(
    var_95: float, var_99: float, severity: RiskSeverity
) -> list[str]:
    """Generate simulation-based recommendations."""
    recommendations = []

    if var_95 > 0.20:
        recommendations.append(
            "Schedule vulnerable to random disruptions - increase buffer capacity"
        )

    if var_99 > 0.35:
        recommendations.append(
            "Extreme scenarios show catastrophic coverage loss - implement defense in depth"
        )

    if severity in (RiskSeverity.CRITICAL, RiskSeverity.EXTREME):
        recommendations.append(
            "CRITICAL: Schedule lacks resilience to disruptions - major redesign needed"
        )

    recommendations.append(
        "Run disruption drills quarterly to validate contingency plans"
    )

    return recommendations


def _generate_cvar_recommendations(
    cvar_value: float, metric: str, severity: RiskSeverity
) -> list[str]:
    """Generate CVaR-specific recommendations."""
    recommendations = []

    if severity in (RiskSeverity.CRITICAL, RiskSeverity.EXTREME):
        recommendations.append(
            f"CRITICAL: Tail risk ({metric}) exceeds acceptable bounds"
        )
        recommendations.append(
            "Implement tail risk hedging strategies (backup pools, MOUs)"
        )

    recommendations.append(
        "Monitor tail risk metrics monthly to detect regime shifts early"
    )

    return recommendations
