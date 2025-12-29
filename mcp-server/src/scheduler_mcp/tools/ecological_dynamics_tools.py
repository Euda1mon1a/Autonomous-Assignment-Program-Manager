"""
Ecological Dynamics Tools - Lotka-Volterra Predator-Prey Modeling for Schedule Supply/Demand.

This module applies ecological predator-prey dynamics to model oscillations between
resource supply (available residents) and demand (workload). Predicts boom/bust cycles
in coverage and complements homeostasis feedback loops.

Theoretical Foundation:
-----------------------
The Lotka-Volterra equations model population dynamics of predator-prey systems.
Applied to scheduling:

- x(t) = "prey" = available capacity/slack (idle resident-hours, unfilled slots)
- y(t) = "predator" = workload demand (clinic volume, patient census, procedures)

System Dynamics:
dx/dt = αx - βxy    (capacity grows naturally, consumed by demand)
dy/dt = δxy - γy    (demand grows when capacity exists, decays naturally)

Where:
- α = capacity growth rate (hiring, training, rotation expansion)
- β = consumption rate (how demand consumes capacity)
- δ = demand amplification (demand breeding from available capacity)
- γ = demand decay rate (procedures completed, patients discharged)

Equilibrium Point:
x* = γ/δ  (stable capacity level)
y* = α/β  (stable demand level)

Ecological Interpretation:
- Oscillations indicate unstable supply/demand balance
- Period of oscillation = 2π/√(αγ) (time between coverage crises)
- Amplitude indicates severity of boom/bust cycles
- Phase portrait reveals system stability

Medical Scheduling Context:
- Capacity shocks: Deployment, TDY, medical leave
- Demand shocks: Flu season, COVID surge, mass casualty event
- Natural oscillations: Academic year cycles, seasonal variations
- Intervention modeling: Moonlighting, locums, schedule compression

Related Concepts:
- Homeostasis (PID control) - actively maintains equilibrium
- Lotka-Volterra - models natural oscillations when equilibrium is disturbed
- Together: proactive control + reactive modeling

Security & Privacy:
- All person IDs are anonymized using SHA-256 hashing
- No PII in model parameters or predictions
- Sanitized output suitable for external consumption
"""

import hashlib
import logging
from datetime import date, datetime, timedelta
from enum import Enum
from typing import Any

import numpy as np
from pydantic import BaseModel, Field
from scipy.integrate import odeint
from scipy.optimize import curve_fit, least_squares

logger = logging.getLogger(__name__)


def _anonymize_id(identifier: str | None, prefix: str = "Entity") -> str:
    """
    Create consistent anonymized reference from ID.

    Uses SHA-256 hash for consistent mapping without exposing PII.
    Complies with OPSEC/PERSEC requirements for military medical data.
    """
    if not identifier:
        return f"{prefix}-unknown"
    hash_suffix = hashlib.sha256(identifier.encode()).hexdigest()[:6]
    return f"{prefix}-{hash_suffix}"


# =============================================================================
# Enums and Constants
# =============================================================================


class SystemStabilityEnum(str, Enum):
    """System stability classification based on oscillation characteristics."""

    STABLE = "stable"  # Damped oscillations, converging to equilibrium
    MARGINALLY_STABLE = "marginally_stable"  # Persistent oscillations
    UNSTABLE = "unstable"  # Growing oscillations, diverging from equilibrium
    CHAOTIC = "chaotic"  # Irregular, unpredictable behavior


class InterventionTypeEnum(str, Enum):
    """Types of interventions that can be simulated."""

    ADD_CAPACITY = "add_capacity"  # Hire residents, expand rotations
    REDUCE_DEMAND = "reduce_demand"  # Cancel elective procedures, defer clinics
    INCREASE_EFFICIENCY = "increase_efficiency"  # Reduce β (demand consumption rate)
    MOONLIGHTING = "moonlighting"  # Temporary capacity injection
    LOCUMS = "locums"  # External capacity temporary injection
    SCHEDULE_COMPRESSION = "schedule_compression"  # Increase utilization
    DEMAND_SMOOTHING = "demand_smoothing"  # Spread workload over time


class RiskLevelEnum(str, Enum):
    """Risk level based on predicted capacity crunch timing."""

    LOW = "low"  # >90 days until crunch
    MODERATE = "moderate"  # 60-90 days
    ELEVATED = "elevated"  # 30-60 days
    HIGH = "high"  # 14-30 days
    CRITICAL = "critical"  # <14 days
    IMMINENT = "imminent"  # <7 days


# =============================================================================
# Core Lotka-Volterra Functions
# =============================================================================


def lotka_volterra(y: list[float], t: float, alpha: float, beta: float, delta: float, gamma: float) -> list[float]:
    """
    Lotka-Volterra differential equations.

    Args:
        y: State vector [x, y] where x=capacity, y=demand
        t: Time parameter (not used, but required by odeint)
        alpha: Capacity growth rate
        beta: Consumption rate (demand consuming capacity)
        delta: Demand amplification rate
        gamma: Demand decay rate

    Returns:
        Derivative vector [dx/dt, dy/dt]
    """
    x, y_val = y
    dxdt = alpha * x - beta * x * y_val
    dydt = delta * x * y_val - gamma * y_val
    return [dxdt, dydt]


def calculate_equilibrium(alpha: float, beta: float, delta: float, gamma: float) -> tuple[float, float]:
    """
    Calculate equilibrium point of Lotka-Volterra system.

    Args:
        alpha: Capacity growth rate
        beta: Consumption rate
        delta: Demand amplification rate
        gamma: Demand decay rate

    Returns:
        Tuple of (x_equilibrium, y_equilibrium)
    """
    x_eq = gamma / delta if delta != 0 else 0.0
    y_eq = alpha / beta if beta != 0 else 0.0
    return x_eq, y_eq


def estimate_oscillation_period(alpha: float, gamma: float) -> float:
    """
    Estimate period of oscillation for Lotka-Volterra system.

    For systems near equilibrium, period ≈ 2π/√(αγ)

    Args:
        alpha: Capacity growth rate
        gamma: Demand decay rate

    Returns:
        Estimated period in days
    """
    if alpha <= 0 or gamma <= 0:
        return 0.0
    return 2 * np.pi / np.sqrt(alpha * gamma)


def fit_lotka_volterra_parameters(
    time_series: list[float],
    capacity_series: list[float],
    demand_series: list[float],
    initial_guess: tuple[float, float, float, float] | None = None,
) -> tuple[float, float, float, float, float]:
    """
    Fit Lotka-Volterra parameters to historical data using least squares.

    Args:
        time_series: Time points (days)
        capacity_series: Observed capacity values
        demand_series: Observed demand values
        initial_guess: Initial parameter guess (alpha, beta, delta, gamma)

    Returns:
        Tuple of (alpha, beta, delta, gamma, r_squared)
    """
    if initial_guess is None:
        # Reasonable defaults for medical scheduling
        initial_guess = (0.1, 0.01, 0.01, 0.1)

    def residuals(params: np.ndarray) -> np.ndarray:
        """Calculate residuals between model and data."""
        alpha, beta, delta, gamma = params

        # Ensure positive parameters
        if any(p <= 0 for p in params):
            return np.ones(len(time_series) * 2) * 1e10

        y0 = [capacity_series[0], demand_series[0]]
        solution = odeint(lotka_volterra, y0, time_series, args=(alpha, beta, delta, gamma))

        capacity_pred = solution[:, 0]
        demand_pred = solution[:, 1]

        # Combined residuals for both capacity and demand
        capacity_residuals = capacity_series - capacity_pred
        demand_residuals = demand_series - demand_pred

        return np.concatenate([capacity_residuals, demand_residuals])

    # Bounds: all parameters must be positive
    bounds = ([1e-6, 1e-6, 1e-6, 1e-6], [10.0, 10.0, 10.0, 10.0])

    result = least_squares(residuals, initial_guess, bounds=bounds, max_nfev=1000)

    alpha, beta, delta, gamma = result.x

    # Calculate R² for goodness of fit
    residual_sum_squares = np.sum(result.fun ** 2)
    total_sum_squares = np.sum((capacity_series - np.mean(capacity_series)) ** 2) + \
                        np.sum((demand_series - np.mean(demand_series)) ** 2)
    r_squared = 1 - (residual_sum_squares / total_sum_squares) if total_sum_squares > 0 else 0.0

    return alpha, beta, delta, gamma, r_squared


def simulate_trajectory(
    alpha: float,
    beta: float,
    delta: float,
    gamma: float,
    initial_capacity: float,
    initial_demand: float,
    days: int,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Simulate Lotka-Volterra trajectory forward in time.

    Args:
        alpha: Capacity growth rate
        beta: Consumption rate
        delta: Demand amplification rate
        gamma: Demand decay rate
        initial_capacity: Starting capacity level
        initial_demand: Starting demand level
        days: Number of days to simulate

    Returns:
        Tuple of (time_array, capacity_trajectory, demand_trajectory)
    """
    t = np.linspace(0, days, days * 10)  # 10 points per day for smooth curves
    y0 = [initial_capacity, initial_demand]
    solution = odeint(lotka_volterra, y0, t, args=(alpha, beta, delta, gamma))

    return t, solution[:, 0], solution[:, 1]


def classify_stability(
    alpha: float,
    beta: float,
    delta: float,
    gamma: float,
    capacity_trajectory: np.ndarray,
) -> SystemStabilityEnum:
    """
    Classify system stability based on trajectory behavior.

    Args:
        alpha: Capacity growth rate
        beta: Consumption rate
        delta: Demand amplification rate
        gamma: Demand decay rate
        capacity_trajectory: Simulated capacity over time

    Returns:
        SystemStabilityEnum classification
    """
    # Check for divergence (instability)
    if np.max(capacity_trajectory[-100:]) > np.max(capacity_trajectory[:100]) * 2:
        return SystemStabilityEnum.UNSTABLE

    # Check for convergence (stability)
    recent_variance = np.var(capacity_trajectory[-100:])
    early_variance = np.var(capacity_trajectory[:100])

    if recent_variance < early_variance * 0.5:
        return SystemStabilityEnum.STABLE

    # Check for chaotic behavior (high irregularity)
    # Use coefficient of variation as irregularity metric
    cv = np.std(capacity_trajectory) / np.mean(capacity_trajectory) if np.mean(capacity_trajectory) > 0 else 0
    if cv > 1.5:
        return SystemStabilityEnum.CHAOTIC

    # Default to marginally stable (persistent oscillations)
    return SystemStabilityEnum.MARGINALLY_STABLE


# =============================================================================
# Pydantic Models for Request/Response
# =============================================================================


class HistoricalDataPoint(BaseModel):
    """Single data point in historical time series."""

    date: date = Field(description="Date of observation")
    capacity: float = Field(ge=0.0, description="Available capacity (idle resident-hours)")
    demand: float = Field(ge=0.0, description="Workload demand (procedures, visits, etc.)")


class SupplyDemandCyclesRequest(BaseModel):
    """Request to analyze supply/demand cycles from historical data."""

    historical_data: list[HistoricalDataPoint] = Field(
        min_length=10,
        description="Historical capacity and demand data (minimum 10 points)",
    )
    prediction_days: int = Field(
        default=90,
        ge=1,
        le=365,
        description="Days to predict forward",
    )


class SupplyDemandCyclesResponse(BaseModel):
    """Response from supply/demand cycle analysis."""

    analyzed_at: str = Field(description="ISO timestamp of analysis")
    data_points: int = Field(ge=0, description="Number of historical data points used")
    fitted_parameters: dict[str, float] = Field(
        description="Fitted Lotka-Volterra parameters: alpha, beta, delta, gamma"
    )
    r_squared: float = Field(ge=0.0, le=1.0, description="Goodness of fit (1.0 = perfect)")
    equilibrium_capacity: float = Field(ge=0.0, description="Equilibrium capacity level")
    equilibrium_demand: float = Field(ge=0.0, description="Equilibrium demand level")
    oscillation_period_days: float = Field(ge=0.0, description="Estimated period of oscillation")
    system_stability: SystemStabilityEnum = Field(description="System stability classification")
    current_capacity: float = Field(ge=0.0, description="Current capacity level")
    current_demand: float = Field(ge=0.0, description="Current demand level")
    predicted_trajectory: list[dict[str, float]] = Field(
        description="Predicted capacity/demand trajectory"
    )
    ecological_interpretation: str = Field(description="Plain English interpretation")
    confidence: float = Field(ge=0.0, le=1.0, description="Prediction confidence")


class CapacityCrunchRequest(BaseModel):
    """Request to predict capacity crunch timing."""

    current_capacity: float = Field(ge=0.0, description="Current available capacity")
    current_demand: float = Field(ge=0.0, description="Current workload demand")
    alpha: float = Field(gt=0.0, description="Capacity growth rate")
    beta: float = Field(gt=0.0, description="Consumption rate")
    delta: float = Field(gt=0.0, description="Demand amplification rate")
    gamma: float = Field(gt=0.0, description="Demand decay rate")
    crunch_threshold: float = Field(
        default=0.1,
        gt=0.0,
        description="Capacity threshold below which crunch is declared",
    )
    prediction_days: int = Field(default=180, ge=1, le=365, description="Prediction horizon")


class CapacityCrunchResponse(BaseModel):
    """Response from capacity crunch prediction."""

    analyzed_at: str = Field(description="ISO timestamp of analysis")
    current_capacity: float = Field(ge=0.0, description="Current capacity level")
    current_demand: float = Field(ge=0.0, description="Current demand level")
    equilibrium_capacity: float = Field(ge=0.0, description="Equilibrium capacity")
    capacity_deficit: float = Field(description="Current - equilibrium (negative = overutilized)")
    crunch_threshold: float = Field(ge=0.0, description="Threshold for capacity crunch")
    days_until_crunch: int | None = Field(description="Days until capacity falls below threshold")
    crunch_date: date | None = Field(description="Predicted date of capacity crunch")
    risk_level: RiskLevelEnum = Field(description="Risk classification")
    minimum_capacity: float = Field(ge=0.0, description="Minimum capacity in prediction window")
    minimum_capacity_date: date | None = Field(description="Date of minimum capacity")
    will_recover: bool = Field(description="Whether capacity recovers after crunch")
    recovery_date: date | None = Field(description="Date capacity recovers above threshold")
    mitigation_urgency: str = Field(description="Recommended urgency of intervention")
    predicted_trajectory: list[dict[str, float]] = Field(description="Predicted trajectory")


class EquilibriumRequest(BaseModel):
    """Request to calculate equilibrium point."""

    alpha: float = Field(gt=0.0, description="Capacity growth rate")
    beta: float = Field(gt=0.0, description="Consumption rate")
    delta: float = Field(gt=0.0, description="Demand amplification rate")
    gamma: float = Field(gt=0.0, description="Demand decay rate")


class EquilibriumResponse(BaseModel):
    """Response from equilibrium calculation."""

    analyzed_at: str = Field(description="ISO timestamp of analysis")
    equilibrium_capacity: float = Field(ge=0.0, description="x* = γ/δ")
    equilibrium_demand: float = Field(ge=0.0, description="y* = α/β")
    oscillation_period_days: float = Field(ge=0.0, description="Period of oscillation near equilibrium")
    is_stable: bool = Field(description="Whether equilibrium is stable")
    ecological_interpretation: str = Field(description="Interpretation of equilibrium")
    parameter_sensitivity: dict[str, str] = Field(
        description="How changes in parameters affect equilibrium"
    )


class InterventionRequest(BaseModel):
    """Request to simulate intervention effect."""

    current_capacity: float = Field(ge=0.0, description="Current capacity level")
    current_demand: float = Field(ge=0.0, description="Current demand level")
    alpha: float = Field(gt=0.0, description="Baseline capacity growth rate")
    beta: float = Field(gt=0.0, description="Baseline consumption rate")
    delta: float = Field(gt=0.0, description="Baseline demand amplification rate")
    gamma: float = Field(gt=0.0, description="Baseline demand decay rate")
    intervention_type: InterventionTypeEnum = Field(description="Type of intervention")
    intervention_magnitude: float = Field(
        ge=0.0,
        description="Magnitude of intervention (e.g., 0.2 = 20% increase/decrease)",
    )
    intervention_start_day: int = Field(
        default=0,
        ge=0,
        description="Day intervention begins (0 = immediately)",
    )
    intervention_duration_days: int = Field(
        default=30,
        ge=1,
        description="Duration of intervention in days",
    )
    simulation_days: int = Field(default=180, ge=1, le=365, description="Total simulation duration")


class InterventionResponse(BaseModel):
    """Response from intervention simulation."""

    analyzed_at: str = Field(description="ISO timestamp of analysis")
    intervention_type: InterventionTypeEnum = Field(description="Type of intervention")
    intervention_magnitude: float = Field(description="Magnitude of intervention")
    baseline_trajectory: list[dict[str, float]] = Field(description="Trajectory without intervention")
    intervention_trajectory: list[dict[str, float]] = Field(description="Trajectory with intervention")
    baseline_min_capacity: float = Field(ge=0.0, description="Minimum capacity without intervention")
    intervention_min_capacity: float = Field(ge=0.0, description="Minimum capacity with intervention")
    capacity_improvement: float = Field(description="Improvement in minimum capacity")
    baseline_oscillation_amplitude: float = Field(
        ge=0.0, description="Amplitude of oscillations without intervention"
    )
    intervention_oscillation_amplitude: float = Field(
        ge=0.0, description="Amplitude with intervention"
    )
    amplitude_reduction: float = Field(description="Reduction in oscillation amplitude")
    intervention_effectiveness: float = Field(
        ge=0.0, le=1.0, description="Overall effectiveness score (0-1)"
    )
    recommendation: str = Field(description="Recommendation based on simulation")
    parameter_changes: dict[str, dict[str, float]] = Field(
        description="How intervention changes Lotka-Volterra parameters"
    )


# =============================================================================
# MCP Tool Functions
# =============================================================================


async def analyze_supply_demand_cycles(
    request: SupplyDemandCyclesRequest,
) -> SupplyDemandCyclesResponse:
    """
    Fit Lotka-Volterra model to historical data and predict oscillation period.

    This tool analyzes historical supply/demand data to identify natural
    boom/bust cycles in coverage. Uses ecological predator-prey dynamics
    to model resource oscillations.

    Args:
        request: Historical data and prediction parameters

    Returns:
        Fitted parameters, equilibrium point, and predicted trajectory
    """
    logger.info(
        "Analyzing supply/demand cycles",
        extra={"data_points": len(request.historical_data), "prediction_days": request.prediction_days},
    )

    # Extract time series
    dates = [dp.date for dp in request.historical_data]
    capacity_series = [dp.capacity for dp in request.historical_data]
    demand_series = [dp.demand for dp in request.historical_data]

    # Convert dates to days from start
    start_date = min(dates)
    time_series = [(d - start_date).days for d in dates]

    # Fit parameters
    alpha, beta, delta, gamma, r_squared = fit_lotka_volterra_parameters(
        time_series, capacity_series, demand_series
    )

    # Calculate equilibrium
    x_eq, y_eq = calculate_equilibrium(alpha, beta, delta, gamma)

    # Estimate oscillation period
    period = estimate_oscillation_period(alpha, gamma)

    # Simulate trajectory
    current_capacity = capacity_series[-1]
    current_demand = demand_series[-1]
    t, capacity_traj, demand_traj = simulate_trajectory(
        alpha, beta, delta, gamma, current_capacity, current_demand, request.prediction_days
    )

    # Classify stability
    stability = classify_stability(alpha, beta, delta, gamma, capacity_traj)

    # Build predicted trajectory
    predicted_trajectory = [
        {"day": int(day), "capacity": float(cap), "demand": float(dem)}
        for day, cap, dem in zip(t[::10], capacity_traj[::10], demand_traj[::10])  # Subsample for readability
    ]

    # Ecological interpretation
    if stability == SystemStabilityEnum.STABLE:
        interpretation = (
            f"System is converging to stable equilibrium at capacity={x_eq:.1f}, demand={y_eq:.1f}. "
            f"Oscillations are damping with period ~{period:.1f} days."
        )
    elif stability == SystemStabilityEnum.MARGINALLY_STABLE:
        interpretation = (
            f"System exhibits persistent oscillations with period ~{period:.1f} days. "
            f"Equilibrium at capacity={x_eq:.1f}, demand={y_eq:.1f}, but not converging. "
            "Consider interventions to dampen cycles."
        )
    elif stability == SystemStabilityEnum.UNSTABLE:
        interpretation = (
            f"WARNING: System is unstable and diverging from equilibrium. "
            f"Oscillations are growing, indicating structural imbalance. "
            "Immediate intervention required."
        )
    else:  # CHAOTIC
        interpretation = (
            "System exhibits chaotic behavior with irregular oscillations. "
            "Predictability is limited. Consider fundamental restructuring."
        )

    return SupplyDemandCyclesResponse(
        analyzed_at=datetime.utcnow().isoformat(),
        data_points=len(request.historical_data),
        fitted_parameters={"alpha": alpha, "beta": beta, "delta": delta, "gamma": gamma},
        r_squared=r_squared,
        equilibrium_capacity=x_eq,
        equilibrium_demand=y_eq,
        oscillation_period_days=period,
        system_stability=stability,
        current_capacity=current_capacity,
        current_demand=current_demand,
        predicted_trajectory=predicted_trajectory,
        ecological_interpretation=interpretation,
        confidence=r_squared,  # Use R² as confidence measure
    )


async def predict_capacity_crunch(
    request: CapacityCrunchRequest,
) -> CapacityCrunchResponse:
    """
    Use Lotka-Volterra model to forecast when demand will exceed supply.

    Predicts timing of capacity crunch (when available capacity falls below
    threshold) and provides risk classification.

    Args:
        request: Current state and LV parameters

    Returns:
        Crunch timing, risk level, and mitigation urgency
    """
    logger.info(
        "Predicting capacity crunch",
        extra={
            "current_capacity": request.current_capacity,
            "current_demand": request.current_demand,
            "threshold": request.crunch_threshold,
        },
    )

    # Calculate equilibrium
    x_eq, y_eq = calculate_equilibrium(request.alpha, request.beta, request.delta, request.gamma)
    capacity_deficit = request.current_capacity - x_eq

    # Simulate trajectory
    t, capacity_traj, demand_traj = simulate_trajectory(
        request.alpha,
        request.beta,
        request.delta,
        request.gamma,
        request.current_capacity,
        request.current_demand,
        request.prediction_days,
    )

    # Find when capacity drops below threshold
    below_threshold = capacity_traj < request.crunch_threshold
    if np.any(below_threshold):
        crunch_idx = np.argmax(below_threshold)
        days_until_crunch = int(t[crunch_idx])
        crunch_date = date.today() + timedelta(days=days_until_crunch)

        # Check if it recovers
        after_crunch = capacity_traj[crunch_idx:]
        above_threshold_after = after_crunch > request.crunch_threshold
        if np.any(above_threshold_after):
            recovery_idx = crunch_idx + np.argmax(above_threshold_after)
            recovery_date = date.today() + timedelta(days=int(t[recovery_idx]))
            will_recover = True
        else:
            recovery_date = None
            will_recover = False
    else:
        days_until_crunch = None
        crunch_date = None
        will_recover = False
        recovery_date = None

    # Find minimum capacity
    min_capacity_idx = np.argmin(capacity_traj)
    minimum_capacity = float(capacity_traj[min_capacity_idx])
    minimum_capacity_date = date.today() + timedelta(days=int(t[min_capacity_idx]))

    # Classify risk
    if days_until_crunch is None:
        risk_level = RiskLevelEnum.LOW
        mitigation_urgency = "Monitoring recommended. No immediate action required."
    elif days_until_crunch < 7:
        risk_level = RiskLevelEnum.IMMINENT
        mitigation_urgency = "IMMEDIATE action required. Activate contingency plans now."
    elif days_until_crunch < 14:
        risk_level = RiskLevelEnum.CRITICAL
        mitigation_urgency = "Urgent intervention required within 24-48 hours."
    elif days_until_crunch < 30:
        risk_level = RiskLevelEnum.HIGH
        mitigation_urgency = "High priority. Begin mitigation planning this week."
    elif days_until_crunch < 60:
        risk_level = RiskLevelEnum.ELEVATED
        mitigation_urgency = "Elevated risk. Prepare intervention strategies."
    else:
        risk_level = RiskLevelEnum.MODERATE
        mitigation_urgency = "Moderate risk. Monitor closely and plan proactively."

    # Build trajectory
    predicted_trajectory = [
        {"day": int(day), "capacity": float(cap), "demand": float(dem)}
        for day, cap, dem in zip(t[::10], capacity_traj[::10], demand_traj[::10])
    ]

    return CapacityCrunchResponse(
        analyzed_at=datetime.utcnow().isoformat(),
        current_capacity=request.current_capacity,
        current_demand=request.current_demand,
        equilibrium_capacity=x_eq,
        capacity_deficit=capacity_deficit,
        crunch_threshold=request.crunch_threshold,
        days_until_crunch=days_until_crunch,
        crunch_date=crunch_date,
        risk_level=risk_level,
        minimum_capacity=minimum_capacity,
        minimum_capacity_date=minimum_capacity_date,
        will_recover=will_recover,
        recovery_date=recovery_date,
        mitigation_urgency=mitigation_urgency,
        predicted_trajectory=predicted_trajectory,
    )


async def find_equilibrium_point(
    request: EquilibriumRequest,
) -> EquilibriumResponse:
    """
    Calculate stable equilibrium point (x*, y*) for given parameters.

    The equilibrium point represents the stable state where supply and
    demand balance. Deviations from equilibrium drive oscillations.

    Args:
        request: Lotka-Volterra parameters

    Returns:
        Equilibrium point and ecological interpretation
    """
    logger.info(
        "Calculating equilibrium point",
        extra={
            "alpha": request.alpha,
            "beta": request.beta,
            "delta": request.delta,
            "gamma": request.gamma,
        },
    )

    # Calculate equilibrium
    x_eq, y_eq = calculate_equilibrium(request.alpha, request.beta, request.delta, request.gamma)

    # Calculate oscillation period
    period = estimate_oscillation_period(request.alpha, request.gamma)

    # Check stability (for LV, equilibrium is always marginally stable - center point)
    is_stable = True  # LV equilibrium is a center (neutral stability)

    # Ecological interpretation
    interpretation = (
        f"Equilibrium capacity: {x_eq:.2f} (available idle capacity). "
        f"Equilibrium demand: {y_eq:.2f} (workload level). "
        f"At this point, capacity growth balances consumption. "
        f"Natural oscillations have period ~{period:.1f} days. "
        "Disturbances from equilibrium will cause cyclic boom/bust patterns."
    )

    # Parameter sensitivity
    sensitivity = {
        "alpha": f"Increasing α (capacity growth) raises equilibrium demand (y*=α/β)",
        "beta": f"Increasing β (consumption) lowers equilibrium demand (y*=α/β)",
        "delta": f"Increasing δ (demand amplification) lowers equilibrium capacity (x*=γ/δ)",
        "gamma": f"Increasing γ (demand decay) raises equilibrium capacity (x*=γ/δ)",
    }

    return EquilibriumResponse(
        analyzed_at=datetime.utcnow().isoformat(),
        equilibrium_capacity=x_eq,
        equilibrium_demand=y_eq,
        oscillation_period_days=period,
        is_stable=is_stable,
        ecological_interpretation=interpretation,
        parameter_sensitivity=sensitivity,
    )


async def simulate_intervention(
    request: InterventionRequest,
) -> InterventionResponse:
    """
    Model effect of adding capacity or reducing demand.

    Simulates how different interventions affect supply/demand dynamics
    and predicts their effectiveness in stabilizing oscillations.

    Args:
        request: Current state, parameters, and intervention details

    Returns:
        Comparison of baseline vs intervention trajectories
    """
    logger.info(
        "Simulating intervention",
        extra={
            "intervention_type": request.intervention_type,
            "magnitude": request.intervention_magnitude,
        },
    )

    # Baseline simulation
    t_baseline, cap_baseline, dem_baseline = simulate_trajectory(
        request.alpha,
        request.beta,
        request.delta,
        request.gamma,
        request.current_capacity,
        request.current_demand,
        request.simulation_days,
    )

    # Apply intervention by modifying parameters
    alpha_int = request.alpha
    beta_int = request.beta
    delta_int = request.delta
    gamma_int = request.gamma

    parameter_changes: dict[str, dict[str, float]] = {}

    if request.intervention_type == InterventionTypeEnum.ADD_CAPACITY:
        # Increase alpha (capacity growth rate)
        alpha_int = request.alpha * (1 + request.intervention_magnitude)
        parameter_changes["alpha"] = {"before": request.alpha, "after": alpha_int}

    elif request.intervention_type == InterventionTypeEnum.REDUCE_DEMAND:
        # Increase gamma (demand decay rate)
        gamma_int = request.gamma * (1 + request.intervention_magnitude)
        parameter_changes["gamma"] = {"before": request.gamma, "after": gamma_int}

    elif request.intervention_type == InterventionTypeEnum.INCREASE_EFFICIENCY:
        # Decrease beta (consumption rate)
        beta_int = request.beta * (1 - request.intervention_magnitude)
        parameter_changes["beta"] = {"before": request.beta, "after": beta_int}

    elif request.intervention_type == InterventionTypeEnum.MOONLIGHTING:
        # Temporary capacity boost - increase initial capacity
        capacity_boost = request.current_capacity * request.intervention_magnitude
        # Will model as one-time capacity injection
        parameter_changes["initial_capacity"] = {
            "before": request.current_capacity,
            "after": request.current_capacity + capacity_boost,
        }

    elif request.intervention_type == InterventionTypeEnum.SCHEDULE_COMPRESSION:
        # Increase beta (more efficient consumption) and increase gamma (faster processing)
        beta_int = request.beta * (1 + request.intervention_magnitude)
        gamma_int = request.gamma * (1 + request.intervention_magnitude)
        parameter_changes["beta"] = {"before": request.beta, "after": beta_int}
        parameter_changes["gamma"] = {"before": request.gamma, "after": gamma_int}

    elif request.intervention_type == InterventionTypeEnum.DEMAND_SMOOTHING:
        # Reduce delta (demand amplification) and increase gamma (decay)
        delta_int = request.delta * (1 - request.intervention_magnitude * 0.5)
        gamma_int = request.gamma * (1 + request.intervention_magnitude * 0.5)
        parameter_changes["delta"] = {"before": request.delta, "after": delta_int}
        parameter_changes["gamma"] = {"before": request.gamma, "after": gamma_int}

    # Intervention simulation
    initial_capacity_int = request.current_capacity
    if request.intervention_type == InterventionTypeEnum.MOONLIGHTING:
        initial_capacity_int += request.current_capacity * request.intervention_magnitude

    t_int, cap_int, dem_int = simulate_trajectory(
        alpha_int,
        beta_int,
        delta_int,
        gamma_int,
        initial_capacity_int,
        request.current_demand,
        request.simulation_days,
    )

    # Calculate metrics
    baseline_min = float(np.min(cap_baseline))
    intervention_min = float(np.min(cap_int))
    capacity_improvement = intervention_min - baseline_min

    baseline_amplitude = float(np.max(cap_baseline) - np.min(cap_baseline))
    intervention_amplitude = float(np.max(cap_int) - np.min(cap_int))
    amplitude_reduction = baseline_amplitude - intervention_amplitude

    # Calculate effectiveness score
    # Combine capacity improvement and amplitude reduction
    capacity_score = min(capacity_improvement / baseline_min, 1.0) if baseline_min > 0 else 0.0
    amplitude_score = min(amplitude_reduction / baseline_amplitude, 1.0) if baseline_amplitude > 0 else 0.0
    effectiveness = (capacity_score * 0.6 + amplitude_score * 0.4)  # Weight capacity more
    effectiveness = max(0.0, min(1.0, effectiveness))  # Clamp to [0, 1]

    # Generate recommendation
    if effectiveness > 0.7:
        recommendation = (
            f"HIGHLY EFFECTIVE: {request.intervention_type.value} shows strong positive impact. "
            f"Minimum capacity improves by {capacity_improvement:.1f} and oscillations dampen by {amplitude_reduction:.1f}. "
            "Strongly recommend implementation."
        )
    elif effectiveness > 0.4:
        recommendation = (
            f"MODERATELY EFFECTIVE: {request.intervention_type.value} provides measurable benefit. "
            f"Consider implementation alongside other strategies."
        )
    elif effectiveness > 0.1:
        recommendation = (
            f"LIMITED EFFECTIVENESS: {request.intervention_type.value} shows minimal impact. "
            "Consider alternative interventions or increase magnitude."
        )
    else:
        recommendation = (
            f"INEFFECTIVE: {request.intervention_type.value} does not significantly improve outcomes. "
            "Not recommended. Explore alternative strategies."
        )

    # Build trajectories
    baseline_trajectory = [
        {"day": int(day), "capacity": float(cap), "demand": float(dem)}
        for day, cap, dem in zip(t_baseline[::10], cap_baseline[::10], dem_baseline[::10])
    ]

    intervention_trajectory = [
        {"day": int(day), "capacity": float(cap), "demand": float(dem)}
        for day, cap, dem in zip(t_int[::10], cap_int[::10], dem_int[::10])
    ]

    return InterventionResponse(
        analyzed_at=datetime.utcnow().isoformat(),
        intervention_type=request.intervention_type,
        intervention_magnitude=request.intervention_magnitude,
        baseline_trajectory=baseline_trajectory,
        intervention_trajectory=intervention_trajectory,
        baseline_min_capacity=baseline_min,
        intervention_min_capacity=intervention_min,
        capacity_improvement=capacity_improvement,
        baseline_oscillation_amplitude=baseline_amplitude,
        intervention_oscillation_amplitude=intervention_amplitude,
        amplitude_reduction=amplitude_reduction,
        intervention_effectiveness=effectiveness,
        recommendation=recommendation,
        parameter_changes=parameter_changes,
    )
