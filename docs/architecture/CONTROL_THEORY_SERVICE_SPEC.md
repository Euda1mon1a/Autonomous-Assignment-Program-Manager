# Control Theory Integration Service Specification

> **Purpose:** Production-ready specification for implementing three-layer control system
> **Status:** Implementation Ready
> **Created:** 2025-12-26
> **Version:** 1.0

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Service Architecture](#service-architecture)
3. [API Endpoints](#api-endpoints)
4. [Pydantic Schemas](#pydantic-schemas)
5. [Service Layer](#service-layer)
6. [Celery Tasks](#celery-tasks)
7. [Integration Points](#integration-points)
8. [Database Schema](#database-schema)
9. [Configuration & Tuning](#configuration--tuning)
10. [Testing Strategy](#testing-strategy)
11. [Performance Metrics](#performance-metrics)
12. [Migration & Deployment](#migration--deployment)

---

## Executive Summary

### Problem Statement

The current scheduling system lacks **formal control mechanisms** for:
- Real-time feedback correction of utilization/coverage deviations
- Optimal state estimation under measurement noise
- Predictive optimization with future uncertainty

### Solution: Three-Layer Control Architecture

Integrate control theory techniques into the residency scheduler:

| Layer | Technique | Purpose | Time Horizon |
|-------|-----------|---------|--------------|
| **Layer 1** | **Kalman Filters** | State estimation from noisy measurements | Continuous |
| **Layer 2** | **PID Controllers** | Fast feedback for utilization/coverage | 1-7 days |
| **Layer 3** | **MPC** | Predictive schedule optimization | 2-8 weeks |

### Key Benefits

1. **Mathematical Rigor:** Replace ad-hoc corrections with proven control algorithms
2. **Faster Convergence:** PID reduces settling time from 14 days → 7 days
3. **Noise Rejection:** Kalman filtering provides ±95% confidence intervals
4. **Adaptive Scheduling:** MPC adjusts weights based on predicted system state
5. **Unified Framework:** Three layers work together seamlessly

### Integration Strategy

- **Non-Breaking:** Control layers augment existing `HomeostasisMonitor` and `SchedulingEngine`
- **Gradual Rollout:** Enable layer-by-layer (Kalman → PID → MPC)
- **Feature Flags:** Can disable/revert to legacy behavior anytime

---

## Service Architecture

### Component Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                     ControlTheoryService                             │
│                    (Orchestration Layer)                             │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  Layer 1: State Estimation (Kalman Filters)                  │  │
│  │                                                               │  │
│  │  ┌─────────────────────┐    ┌──────────────────────────┐    │  │
│  │  │ WorkloadKalmanFilter│    │ ScheduleHealthEKF        │    │  │
│  │  │                     │    │ (Extended Kalman)        │    │  │
│  │  │ • State: [hours,    │    │ • State: [util, coverage,│    │  │
│  │  │   trend, seasonal]  │    │   stability, burnout]    │    │  │
│  │  │ • Measurements:     │    │ • Measurements:          │    │  │
│  │  │   - Scheduled hours │    │   - Metric calculations  │    │  │
│  │  │   - Self-reports    │    │   - SPC monitoring       │    │  │
│  │  │   - Call volume     │    │   - Resilience scores    │    │  │
│  │  └─────────────────────┘    └──────────────────────────┘    │  │
│  │                                                               │  │
│  │  Output: Filtered state estimates with confidence intervals  │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                 │                                    │
│                                 ▼                                    │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  Layer 2: Feedback Control (PID Controllers)                 │  │
│  │                                                               │  │
│  │  ┌────────────────┐  ┌────────────────┐  ┌──────────────┐   │  │
│  │  │ Utilization PID│  │ Workload PID   │  │ Coverage PID │   │  │
│  │  │ (setpoint=0.75)│  │ (setpoint=0.15)│  │ (setpoint=0.95)│ │
│  │  │                │  │                │  │              │   │  │
│  │  │ Kp=10.0        │  │ Kp=5.0         │  │ Kp=12.0      │   │  │
│  │  │ Ki=0.5         │  │ Ki=0.3         │  │ Ki=0.8       │   │  │
│  │  │ Kd=2.0         │  │ Kd=1.0         │  │ Kd=1.5       │   │  │
│  │  └────────────────┘  └────────────────┘  └──────────────┘   │  │
│  │                                                               │  │
│  │  Output: CorrectiveAction recommendations                    │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                 │                                    │
│                                 ▼                                    │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  Layer 3: Predictive Optimization (MPC)                      │  │
│  │                                                               │  │
│  │  ┌──────────────────────────────────────────────────────┐   │  │
│  │  │  MPCSchedulerBridge                                   │   │  │
│  │  │                                                        │   │  │
│  │  │  • Prediction Horizon: 4 weeks                        │   │  │
│  │  │  • Control Horizon: 2 weeks                           │   │  │
│  │  │  • Recalculation: Every 1 week                        │   │  │
│  │  │                                                        │   │  │
│  │  │  Inputs: Kalman state estimates + Forecasts           │   │  │
│  │  │  Outputs: Dynamic constraint weights                  │   │  │
│  │  └──────────────────────────────────────────────────────┘   │  │
│  │                                                               │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                 │                                    │
└─────────────────────────────────┼────────────────────────────────────┘
                                  │
                                  ▼
                  ┌───────────────────────────────┐
                  │   SchedulingEngine            │
                  │   • CP-SAT Solver             │
                  │   • Dynamic Weights (from MPC)│
                  │   • ACGME Validation          │
                  └───────────────────────────────┘
```

### Module Layout

```
backend/app/services/control/
├── __init__.py                    # Service exports
├── orchestrator.py                # ControlTheoryService (main)
│
├── kalman/                        # Layer 1: State Estimation
│   ├── __init__.py
│   ├── workload_filter.py        # WorkloadKalmanFilter
│   ├── schedule_health_ekf.py    # Extended Kalman for system health
│   └── base.py                    # Base Kalman filter class
│
├── pid/                           # Layer 2: Feedback Control
│   ├── __init__.py
│   ├── controllers.py             # PIDState, PIDControllerBank
│   ├── bridge.py                  # PIDHomeostasisBridge
│   └── tuning.py                  # Auto-tuning algorithms
│
├── mpc/                           # Layer 3: Predictive Control
│   ├── __init__.py
│   ├── bridge.py                  # MPCSchedulerBridge
│   ├── state_estimator.py        # System state estimation
│   ├── weight_optimizer.py       # Dynamic weight calculation
│   └── observer.py                # Result observation
│
└── schemas.py                     # Pydantic schemas for all layers
```

### Control Flow Sequence

```
┌──────────────────────────────────────────────────────────────┐
│ 1. MEASUREMENT COLLECTION (Every 15 minutes)                  │
│    • ScheduleMetricsCollector.get_current_metrics()          │
│    • ResilienceService.get_forecast(weeks=4)                 │
└──────────────────┬───────────────────────────────────────────┘
                   │
                   ▼
┌──────────────────────────────────────────────────────────────┐
│ 2. STATE ESTIMATION (Layer 1 - Kalman)                       │
│    • WorkloadKalmanFilter.update(measurements)               │
│    • ScheduleHealthEKF.update(metrics)                       │
│    Output: Filtered estimates with uncertainty               │
└──────────────────┬───────────────────────────────────────────┘
                   │
                   ▼
┌──────────────────────────────────────────────────────────────┐
│ 3. FEEDBACK CONTROL (Layer 2 - PID)                          │
│    • PIDControllerBank.update("utilization", estimate)       │
│    • PIDControllerBank.update("coverage", estimate)          │
│    • PIDHomeostasisBridge.merge_recommendations()            │
│    Output: CorrectiveActions with PID diagnostics            │
└──────────────────┬───────────────────────────────────────────┘
                   │
                   ▼
┌──────────────────────────────────────────────────────────────┐
│ 4. PREDICTIVE OPTIMIZATION (Layer 3 - MPC, Weekly)           │
│    • MPCSchedulerBridge.optimize_weights(forecast)           │
│    • Dynamic weight adjustment based on predicted state      │
│    Output: Optimal constraint weights for CP-SAT             │
└──────────────────┬───────────────────────────────────────────┘
                   │
                   ▼
┌──────────────────────────────────────────────────────────────┐
│ 5. SCHEDULE GENERATION                                        │
│    • SchedulingEngine.generate(dynamic_weights=weights)      │
│    • CP-SAT solves with adapted weights                      │
│    • ACGMEValidator ensures compliance                       │
└──────────────────┬───────────────────────────────────────────┘
                   │
                   ▼
┌──────────────────────────────────────────────────────────────┐
│ 6. OBSERVATION & MODEL UPDATE                                │
│    • ControlTheoryService.observe_result(actual_metrics)     │
│    • Update Kalman filters with actual observations          │
│    • Calculate prediction errors for MPC learning            │
│    • Log performance metrics to Prometheus                   │
└──────────────────────────────────────────────────────────────┘
```

### Separation of Concerns

| Component | Responsibilities | Does NOT Handle |
|-----------|-----------------|-----------------|
| **ControlTheoryService** | - Orchestrate all three layers<br>- Coordinate timing<br>- Feature flag management<br>- Unified API | Scheduling logic, ACGME validation |
| **KalmanFilters** | - State estimation<br>- Uncertainty quantification<br>- Noise filtering | Corrective actions, optimization |
| **PIDControllers** | - Feedback calculation<br>- Anti-windup protection<br>- Gain scheduling | State estimation, schedule generation |
| **MPCBridge** | - Multi-week optimization<br>- Dynamic weight calculation<br>- Constraint adaptation | Solving CP-SAT, ACGME rules |
| **HomeostasisMonitor** | - Setpoint management<br>- Volatility detection<br>- Allostatic load | Control algorithms (delegated to PID) |
| **SchedulingEngine** | - Schedule generation<br>- Constraint enforcement<br>- ACGME compliance | Weight optimization (receives from MPC) |

---

## API Endpoints

### Layer 1: Kalman Filter Endpoints

#### `GET /api/v1/control/kalman/workload/{person_id}`

Get Kalman-filtered workload estimate for a person.

**Response:**
```json
{
  "person_id": "uuid",
  "timestamp": "2025-12-26T10:00:00Z",
  "estimated_hours": 67.2,
  "trend": 0.5,
  "seasonal_component": 2.1,
  "uncertainty_std": 1.2,
  "confidence_95_lower": 64.8,
  "confidence_95_upper": 69.6,
  "utilization": 0.896,
  "estimate_reliable": true,
  "measurements_used": ["scheduled_hours", "self_reported"]
}
```

#### `POST /api/v1/control/kalman/workload/{person_id}/update`

Update Kalman filter with new measurements.

**Request Body:**
```json
{
  "scheduled_hours": 65.0,
  "self_reported": 68.0,
  "call_volume": 45.5
}
```

**Response:**
```json
{
  "updated": true,
  "estimate": { /* WorkloadEstimate as above */ }
}
```

#### `GET /api/v1/control/kalman/system-health`

Get system-wide health estimate from Extended Kalman Filter.

**Response:**
```json
{
  "timestamp": "2025-12-26T10:00:00Z",
  "utilization": {
    "estimate": 0.78,
    "uncertainty": 0.03,
    "confidence_95": [0.72, 0.84]
  },
  "coverage": {
    "estimate": 0.94,
    "uncertainty": 0.02,
    "confidence_95": [0.90, 0.98]
  },
  "burnout_risk": {
    "estimate": 0.12,
    "uncertainty": 0.05,
    "confidence_95": [0.02, 0.22]
  },
  "estimate_quality": "high"
}
```

### Layer 2: PID Controller Endpoints

#### `GET /api/v1/control/pid/status`

Get status of all PID controllers.

**Response:**
```json
{
  "utilization": {
    "setpoint": 0.75,
    "current_value": 0.82,
    "error": -0.07,
    "control_signal": -0.14,
    "gains": {
      "Kp": 10.0,
      "Ki": 0.5,
      "Kd": 2.0
    },
    "state": {
      "integral": 0.35,
      "previous_error": -0.06
    },
    "diagnostics": {
      "oscillation_count": 2,
      "saturation_count": 0,
      "integral_saturated": false,
      "output_saturated": false
    }
  },
  "workload_balance": { /* similar structure */ },
  "coverage": { /* similar structure */ }
}
```

#### `POST /api/v1/control/pid/tune`

Auto-tune PID parameters using Ziegler-Nichols or optimization.

**Request Body:**
```json
{
  "controller": "utilization",
  "method": "ziegler_nichols",
  "parameters": {
    "ultimate_gain": 15.0,
    "ultimate_period": 7.0
  }
}
```

**Response:**
```json
{
  "controller": "utilization",
  "method": "ziegler_nichols",
  "tuned_gains": {
    "Kp": 9.0,
    "Ki": 2.57,
    "Kd": 7.88
  },
  "applied": true,
  "timestamp": "2025-12-26T10:00:00Z"
}
```

#### `POST /api/v1/control/pid/reset`

Reset PID controller state (integral, previous_error).

**Request Body:**
```json
{
  "controller": "utilization"  // or null for all
}
```

**Response:**
```json
{
  "reset": ["utilization"],
  "timestamp": "2025-12-26T10:00:00Z"
}
```

### Layer 3: MPC Endpoints

#### `GET /api/v1/control/mpc/forecast`

Get 4-week forecast from MPC prediction horizon.

**Response:**
```json
{
  "prediction_horizon_weeks": 4,
  "start_date": "2025-12-26",
  "end_date": "2026-01-23",
  "utilization_trajectory": [0.78, 0.80, 0.82, 0.84],
  "coverage_trajectory": [0.95, 0.94, 0.93, 0.92],
  "burnout_risk_trajectory": [0.10, 0.12, 0.15, 0.18],
  "system_states": ["GREEN", "YELLOW", "ORANGE", "ORANGE"],
  "recommended_actions": [
    {
      "week": 3,
      "action": "Increase coverage weight",
      "reason": "Predicted coverage drop to 0.93"
    }
  ]
}
```

#### `POST /api/v1/control/mpc/optimize`

Run MPC optimization to calculate optimal constraint weights.

**Request Body:**
```json
{
  "start_date": "2025-12-26",
  "prediction_horizon_weeks": 4,
  "control_horizon_weeks": 2,
  "current_state": {
    "utilization": 0.78,
    "coverage": 0.95,
    "workload_variance": 0.12
  }
}
```

**Response:**
```json
{
  "optimal_weights": {
    "coverage": 1200.0,
    "utilization_buffer": 30.0,
    "equity": 8.0,
    "preference": 6.0,
    "hub_protection": 15.0,
    "n1_vulnerability": 25.0
  },
  "system_state": "YELLOW",
  "predicted_peak_utilization": 0.82,
  "predicted_min_coverage": 0.94,
  "weight_adjustments_applied": [
    "Coverage weight increased 20% (crisis prevention)",
    "Utilization buffer increased 50% (approaching threshold)",
    "Preference weight decreased 25% (deprioritize during stress)"
  ],
  "timestamp": "2025-12-26T10:00:00Z"
}
```

#### `POST /api/v1/control/mpc/generate-schedule`

Generate schedule using MPC rolling-horizon optimization.

**Request Body:**
```json
{
  "start_date": "2025-07-01",
  "end_date": "2026-06-30",
  "config": {
    "prediction_horizon_weeks": 4,
    "control_horizon_weeks": 2,
    "recalculation_frequency_days": 7
  }
}
```

**Response:**
```json
{
  "status": "completed",
  "assignments_count": 14600,
  "iterations": 26,
  "total_time_seconds": 780.5,
  "performance_metrics": {
    "final_coverage_rate": 0.96,
    "final_utilization_rate": 0.78,
    "acgme_compliant": true,
    "mean_prediction_error_utilization": 0.03,
    "mean_prediction_error_coverage": 0.02,
    "crisis_iterations": 3
  },
  "schedule_id": "uuid"
}
```

### Unified Control Endpoints

#### `GET /api/v1/control/state`

Get current control system state across all layers.

**Response:**
```json
{
  "timestamp": "2025-12-26T10:00:00Z",
  "layer1_kalman": {
    "workload_filters_active": 12,
    "system_health_estimate": {
      "utilization": 0.78,
      "coverage": 0.94,
      "confidence": "high"
    }
  },
  "layer2_pid": {
    "controllers_enabled": ["utilization", "coverage"],
    "corrections_active": 2,
    "current_errors": {
      "utilization": -0.03,
      "coverage": 0.01
    }
  },
  "layer3_mpc": {
    "enabled": true,
    "current_iteration": 5,
    "prediction_horizon_weeks": 4,
    "control_horizon_weeks": 2,
    "system_state": "YELLOW"
  },
  "overall_health": "nominal"
}
```

#### `POST /api/v1/control/enable`

Enable/disable control layers via feature flags.

**Request Body:**
```json
{
  "kalman_workload": true,
  "kalman_system_health": true,
  "pid_utilization": true,
  "pid_coverage": true,
  "pid_workload": false,
  "mpc": true
}
```

**Response:**
```json
{
  "updated": true,
  "active_layers": {
    "kalman": ["workload", "system_health"],
    "pid": ["utilization", "coverage"],
    "mpc": ["enabled"]
  },
  "timestamp": "2025-12-26T10:00:00Z"
}
```

---

## Pydantic Schemas

### Layer 1: Kalman Filter Schemas

```python
"""
Pydantic schemas for Kalman filter state estimation.

File: backend/app/services/control/schemas.py
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

import numpy as np
from pydantic import BaseModel, Field, validator


class WorkloadEstimate(BaseModel):
    """Output of Kalman filter workload estimation."""

    timestamp: datetime
    person_id: UUID

    # Point estimates
    estimated_hours: float = Field(..., ge=0, le=168, description="Estimated weekly hours")
    trend: float = Field(..., description="Weekly change rate (hours/week)")
    seasonal_component: float = Field(..., description="Seasonal variation (hours)")

    # Uncertainty quantification
    uncertainty_std: float = Field(..., ge=0, description="Standard deviation of estimate")
    confidence_95_lower: float = Field(..., description="95% CI lower bound")
    confidence_95_upper: float = Field(..., description="95% CI upper bound")

    # Diagnostics
    measurement_residual: Optional[float] = Field(None, description="Innovation (measurement error)")
    kalman_gain: Optional[list[float]] = Field(None, description="Kalman gain coefficients")
    measurements_used: list[str] = Field(default_factory=list, description="Available measurements")

    class Config:
        json_encoders = {
            np.ndarray: lambda x: x.tolist(),
        }


class SystemHealthEstimate(BaseModel):
    """Extended Kalman Filter estimate of system-wide health."""

    timestamp: datetime

    # State estimates
    utilization: dict = Field(
        ...,
        description="Utilization estimate with uncertainty",
        example={"estimate": 0.78, "uncertainty": 0.03, "confidence_95": [0.72, 0.84]}
    )
    coverage: dict = Field(
        ...,
        description="Coverage estimate with uncertainty",
        example={"estimate": 0.94, "uncertainty": 0.02, "confidence_95": [0.90, 0.98]}
    )
    stability: dict = Field(
        ...,
        description="Schedule stability estimate",
        example={"estimate": 0.92, "uncertainty": 0.04, "confidence_95": [0.84, 1.00]}
    )
    burnout_risk: dict = Field(
        ...,
        description="Burnout risk estimate",
        example={"estimate": 0.12, "uncertainty": 0.05, "confidence_95": [0.02, 0.22]}
    )

    # Overall quality
    estimate_quality: str = Field(
        ...,
        description="Estimate reliability: high/medium/low",
        pattern="^(high|medium|low)$"
    )


class KalmanFilterConfig(BaseModel):
    """Configuration for Kalman filter."""

    person_id: UUID
    initial_hours: float = Field(default=60.0, ge=0, le=168)

    # Noise parameters
    process_noise: float = Field(default=0.02, ge=0, le=1.0, description="Process noise variance (Q)")
    measurement_noise_scheduled: float = Field(default=0.05, ge=0, le=1.0, description="Scheduled hours noise (R)")
    measurement_noise_self_report: float = Field(default=0.15, ge=0, le=1.0, description="Self-report noise (R)")
    measurement_noise_call_volume: float = Field(default=0.10, ge=0, le=1.0, description="Call volume noise (R)")


class KalmanMeasurement(BaseModel):
    """Measurements for Kalman filter update."""

    person_id: UUID
    timestamp: datetime

    scheduled_hours: Optional[float] = Field(None, ge=0, le=168)
    self_reported: Optional[float] = Field(None, ge=0, le=168)
    call_volume: Optional[float] = Field(None, ge=0, le=168)

    @validator('self_reported', 'call_volume')
    def validate_optional_measurements(cls, v):
        """Ensure measurements are positive if provided."""
        if v is not None and v < 0:
            raise ValueError("Measurement cannot be negative")
        return v
```

### Layer 2: PID Controller Schemas

```python
class PIDConfig(BaseModel):
    """Configuration for a PID controller."""

    name: str = Field(..., pattern="^(utilization|workload_balance|coverage)$")
    setpoint: float = Field(..., ge=0, le=1.0, description="Target value")

    # Gains
    Kp: float = Field(..., ge=0, le=50.0, description="Proportional gain")
    Ki: float = Field(..., ge=0, le=10.0, description="Integral gain")
    Kd: float = Field(..., ge=0, le=20.0, description="Derivative gain")

    # Limits
    output_limits: tuple[float, float] = Field(default=(-0.2, 0.2), description="Control signal limits")
    integral_limits: tuple[float, float] = Field(default=(-5.0, 5.0), description="Anti-windup limits")

    # Metadata
    unit: str = Field(default="", description="Unit of measurement")
    description: str = Field(default="", description="Controller purpose")


class PIDState(BaseModel):
    """Current state of a PID controller."""

    controller_id: UUID
    name: str
    timestamp: datetime

    # Current values
    current_value: float = Field(..., description="Current process variable")
    setpoint: float = Field(..., description="Target value")
    error: float = Field(..., description="Setpoint - current_value")
    control_signal: float = Field(..., description="PID output")

    # Term breakdown
    P_term: float = Field(..., description="Proportional contribution")
    I_term: float = Field(..., description="Integral contribution")
    D_term: float = Field(..., description="Derivative contribution")

    # State variables
    integral: float = Field(..., description="Accumulated error")
    previous_error: float = Field(..., description="Error from last cycle")

    # Diagnostics
    integral_saturated: bool = Field(default=False, description="Integral at limit")
    output_saturated: bool = Field(default=False, description="Output at limit")
    dt: float = Field(..., ge=0, description="Time since last update (days)")


class PIDTuningRequest(BaseModel):
    """Request to auto-tune PID controller."""

    controller: str = Field(..., pattern="^(utilization|workload_balance|coverage)$")
    method: str = Field(..., pattern="^(ziegler_nichols|cohen_coon|relay_feedback|optimization)$")

    # Method-specific parameters
    parameters: dict = Field(
        default_factory=dict,
        description="Method-specific tuning parameters",
        example={
            "ultimate_gain": 15.0,
            "ultimate_period": 7.0
        }
    )


class PIDTuningResult(BaseModel):
    """Result of PID auto-tuning."""

    controller: str
    method: str
    timestamp: datetime

    tuned_gains: dict = Field(
        ...,
        description="Calculated PID gains",
        example={"Kp": 9.0, "Ki": 2.57, "Kd": 7.88}
    )

    performance_metrics: Optional[dict] = Field(
        None,
        description="Predicted performance",
        example={
            "settling_time_days": 7,
            "overshoot_percent": 5.0,
            "steady_state_error": 0.01
        }
    )

    applied: bool = Field(default=False, description="Whether gains were applied")
```

### Layer 3: MPC Schemas

```python
class MPCConfig(BaseModel):
    """Configuration for MPC scheduler."""

    prediction_horizon_weeks: int = Field(default=4, ge=1, le=8, description="Forecast horizon")
    control_horizon_weeks: int = Field(default=2, ge=1, le=4, description="Execution horizon")
    recalculation_frequency_days: int = Field(default=7, ge=1, le=14, description="Re-solve frequency")

    # Base weights
    base_weights: dict[str, float] = Field(
        default_factory=lambda: {
            "coverage": 1000.0,
            "utilization_buffer": 20.0,
            "equity": 10.0,
            "continuity": 5.0,
            "preference": 8.0,
            "hub_protection": 15.0,
            "n1_vulnerability": 25.0,
        },
        description="Baseline constraint weights"
    )

    # Weight adjustment parameters
    crisis_multiplier: float = Field(default=2.0, ge=1.0, le=5.0, description="Crisis weight multiplier")
    smoothing_alpha: float = Field(default=0.3, ge=0.0, le=1.0, description="EMA smoothing factor")


class MPCForecast(BaseModel):
    """MPC prediction horizon forecast."""

    prediction_horizon_weeks: int
    start_date: str  # ISO format
    end_date: str

    # Trajectories
    utilization_trajectory: list[float] = Field(..., min_items=1, max_items=8)
    coverage_trajectory: list[float] = Field(..., min_items=1, max_items=8)
    burnout_risk_trajectory: list[float] = Field(..., min_items=1, max_items=8)

    # System states
    system_states: list[str] = Field(..., description="Predicted states: GREEN, YELLOW, ORANGE, RED, BLACK")

    # Recommendations
    recommended_actions: list[dict] = Field(
        default_factory=list,
        description="Proactive actions based on forecast"
    )


class MPCOptimizationRequest(BaseModel):
    """Request for MPC weight optimization."""

    start_date: str  # ISO format
    prediction_horizon_weeks: int = Field(default=4, ge=1, le=8)
    control_horizon_weeks: int = Field(default=2, ge=1, le=4)

    current_state: dict = Field(
        ...,
        description="Current system state",
        example={
            "utilization": 0.78,
            "coverage": 0.95,
            "workload_variance": 0.12
        }
    )


class MPCOptimizationResult(BaseModel):
    """Result of MPC optimization."""

    timestamp: datetime
    optimal_weights: dict[str, float] = Field(..., description="Calculated constraint weights")

    # Predicted state
    system_state: str = Field(..., pattern="^(GREEN|YELLOW|ORANGE|RED|BLACK)$")
    predicted_peak_utilization: float = Field(..., ge=0, le=1.0)
    predicted_min_coverage: float = Field(..., ge=0, le=1.0)

    # Weight adjustments applied
    weight_adjustments_applied: list[str] = Field(
        default_factory=list,
        description="Human-readable adjustment descriptions"
    )


class MPCPerformanceMetrics(BaseModel):
    """MPC performance tracking."""

    total_iterations: int = Field(..., ge=0)
    mean_utilization_error: float = Field(..., description="Mean prediction error")
    mean_coverage_error: float = Field(..., description="Mean prediction error")

    weight_adjustments: int = Field(..., ge=0, description="Times weights were adjusted")
    crisis_iterations: int = Field(..., ge=0, description="Iterations in RED/BLACK state")

    final_coverage_rate: float = Field(..., ge=0, le=1.0)
    final_utilization_rate: float = Field(..., ge=0, le=1.0)
    acgme_compliant: bool
```

---

## Service Layer

### Core Service Class

```python
"""
Control Theory Integration Service - Orchestration Layer

File: backend/app/services/control/orchestrator.py
"""

import logging
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any, Optional
from uuid import UUID

from app.db.session import AsyncSession
from app.resilience.service import ResilienceService
from app.services.control.kalman.workload_filter import WorkloadKalmanFilter
from app.services.control.kalman.schedule_health_ekf import ScheduleHealthEKF
from app.services.control.pid.bridge import PIDHomeostasisBridge
from app.services.control.pid.controllers import PIDControllerBank
from app.services.control.mpc.bridge import MPCSchedulerBridge
from app.services.control.schemas import (
    WorkloadEstimate,
    SystemHealthEstimate,
    PIDState,
    MPCOptimizationResult,
)

logger = logging.getLogger(__name__)


@dataclass
class ControlSystemConfig:
    """Configuration for control system layers."""

    # Feature flags
    enable_kalman_workload: bool = True
    enable_kalman_system_health: bool = True
    enable_pid_utilization: bool = True
    enable_pid_coverage: bool = True
    enable_pid_workload: bool = False  # Start disabled
    enable_mpc: bool = True

    # Update frequencies
    kalman_update_minutes: int = 15
    pid_update_minutes: int = 15
    mpc_recalculation_days: int = 7


class ControlTheoryService:
    """
    Unified control theory service integrating three layers.

    Orchestrates:
    - Layer 1: Kalman filtering for state estimation
    - Layer 2: PID control for feedback corrections
    - Layer 3: MPC for predictive scheduling

    Usage:
        service = ControlTheoryService(db, resilience_service)
        await service.update_all()  # Run all layers
        state = await service.get_control_state()
    """

    def __init__(
        self,
        db: AsyncSession,
        resilience_service: ResilienceService,
        config: Optional[ControlSystemConfig] = None,
    ):
        self.db = db
        self.resilience = resilience_service
        self.config = config or ControlSystemConfig()

        # Layer 1: Kalman Filters
        self.workload_filters: dict[UUID, WorkloadKalmanFilter] = {}
        self.system_health_ekf: Optional[ScheduleHealthEKF] = None

        # Layer 2: PID Controllers
        self.pid_bank = PIDControllerBank()
        self.pid_bridge: Optional[PIDHomeostasisBridge] = None

        # Layer 3: MPC
        self.mpc_bridge: Optional[MPCSchedulerBridge] = None

        # State tracking
        self.last_kalman_update: Optional[datetime] = None
        self.last_pid_update: Optional[datetime] = None
        self.last_mpc_update: Optional[datetime] = None

        logger.info("ControlTheoryService initialized with config: %s", self.config)

    async def initialize(self):
        """Initialize all control layers."""
        logger.info("Initializing control layers...")

        # Layer 1: Initialize system health EKF
        if self.config.enable_kalman_system_health:
            from app.services.control.kalman.schedule_health_ekf import ScheduleHealthEKF
            self.system_health_ekf = ScheduleHealthEKF(initial_state=[0.75, 0.95, 0.95, 0.10])
            logger.info("✓ System health EKF initialized")

        # Layer 2: Initialize PID bridge
        if any([
            self.config.enable_pid_utilization,
            self.config.enable_pid_coverage,
            self.config.enable_pid_workload
        ]):
            from app.resilience.homeostasis import HomeostasisMonitor
            homeostasis = HomeostasisMonitor()
            self.pid_bridge = PIDHomeostasisBridge(homeostasis)

            # Configure enabled controllers
            self.pid_bridge.pid_enabled_for = {
                "faculty_utilization": self.config.enable_pid_utilization,
                "coverage_rate": self.config.enable_pid_coverage,
                "workload_balance": self.config.enable_pid_workload,
            }
            logger.info("✓ PID bridge initialized with controllers: %s", self.pid_bridge.pid_enabled_for)

        # Layer 3: Initialize MPC
        if self.config.enable_mpc:
            from app.scheduling.constraints import ConstraintManager
            from app.services.control.mpc.bridge import MPCSchedulerBridge
            constraint_manager = ConstraintManager.create_default()
            self.mpc_bridge = MPCSchedulerBridge(
                resilience_service=self.resilience,
                constraint_manager=constraint_manager,
            )
            logger.info("✓ MPC bridge initialized")

        logger.info("Control system initialization complete")

    # ========================================================================
    # LAYER 1: KALMAN FILTER METHODS
    # ========================================================================

    async def register_faculty_workload_filter(
        self,
        person_id: UUID,
        initial_hours: float = 60.0
    ) -> WorkloadKalmanFilter:
        """Register a Kalman filter for faculty workload tracking."""
        if person_id not in self.workload_filters:
            kf = WorkloadKalmanFilter(person_id=person_id, initial_hours=initial_hours)
            self.workload_filters[person_id] = kf
            logger.info(f"Registered workload filter for {person_id}")
        return self.workload_filters[person_id]

    async def update_workload_estimate(
        self,
        person_id: UUID,
        scheduled_hours: Optional[float] = None,
        self_reported: Optional[float] = None,
        call_volume: Optional[float] = None,
    ) -> WorkloadEstimate:
        """Update workload estimate with new measurements."""
        if person_id not in self.workload_filters:
            await self.register_faculty_workload_filter(person_id)

        kf = self.workload_filters[person_id]

        measurements = {}
        if scheduled_hours is not None:
            measurements["scheduled_hours"] = scheduled_hours
        if self_reported is not None:
            measurements["self_reported"] = self_reported
        if call_volume is not None:
            measurements["call_volume"] = call_volume

        estimate = kf.update(measurements)
        logger.debug(f"Updated workload for {person_id}: {estimate.estimated_hours:.1f}h ± {estimate.uncertainty_std:.1f}h")

        return estimate

    async def update_system_health_estimate(
        self,
        metrics: dict
    ) -> SystemHealthEstimate:
        """Update system-wide health estimate using Extended Kalman Filter."""
        if not self.system_health_ekf:
            raise RuntimeError("System health EKF not initialized")

        # Convert metrics to measurement vector
        measurement = [
            metrics.get("utilization", 0.75),
            metrics.get("coverage", 0.95),
            metrics.get("stability", 0.95),
            metrics.get("burnout_risk", 0.10),
        ]

        state_estimate = self.system_health_ekf.update(measurement)

        # Package as SystemHealthEstimate
        estimate = SystemHealthEstimate(
            timestamp=datetime.now(),
            utilization={
                "estimate": state_estimate[0],
                "uncertainty": self.system_health_ekf.get_uncertainty(0),
                "confidence_95": self.system_health_ekf.get_confidence_interval(0, 0.95),
            },
            coverage={
                "estimate": state_estimate[1],
                "uncertainty": self.system_health_ekf.get_uncertainty(1),
                "confidence_95": self.system_health_ekf.get_confidence_interval(1, 0.95),
            },
            stability={
                "estimate": state_estimate[2],
                "uncertainty": self.system_health_ekf.get_uncertainty(2),
                "confidence_95": self.system_health_ekf.get_confidence_interval(2, 0.95),
            },
            burnout_risk={
                "estimate": state_estimate[3],
                "uncertainty": self.system_health_ekf.get_uncertainty(3),
                "confidence_95": self.system_health_ekf.get_confidence_interval(3, 0.95),
            },
            estimate_quality=self._assess_estimate_quality(self.system_health_ekf),
        )

        logger.debug(f"System health updated: util={estimate.utilization['estimate']:.2f}, quality={estimate.estimate_quality}")

        return estimate

    def _assess_estimate_quality(self, ekf) -> str:
        """Assess quality of EKF estimate based on uncertainty."""
        max_uncertainty = max(ekf.get_uncertainty(i) for i in range(4))

        if max_uncertainty < 0.05:
            return "high"
        elif max_uncertainty < 0.10:
            return "medium"
        else:
            return "low"

    # ========================================================================
    # LAYER 2: PID CONTROLLER METHODS
    # ========================================================================

    async def update_pid_controllers(
        self,
        current_values: dict[str, float]
    ) -> dict:
        """Update all PID controllers with current metrics."""
        if not self.pid_bridge:
            logger.warning("PID bridge not initialized, skipping update")
            return {}

        result = self.pid_bridge.update_all(current_values)

        logger.info(
            f"PID update: {len(result['pid_corrections'])} corrections, "
            f"{len(result['merged_actions'])} total actions"
        )

        self.last_pid_update = datetime.now()

        return result

    async def tune_pid_controller(
        self,
        controller_name: str,
        method: str,
        parameters: dict
    ) -> dict:
        """Auto-tune PID controller using specified method."""
        if not self.pid_bridge:
            raise RuntimeError("PID bridge not initialized")

        if method == "ziegler_nichols":
            Ku = parameters.get("ultimate_gain")
            Pu = parameters.get("ultimate_period")
            if not Ku or not Pu:
                raise ValueError("ziegler_nichols requires ultimate_gain and ultimate_period")

            self.pid_bank.tune_ziegler_nichols(controller_name, Ku, Pu)

        else:
            raise ValueError(f"Unknown tuning method: {method}")

        # Get updated gains
        controller = self.pid_bank.controllers[controller_name]
        return {
            "Kp": controller.config.Kp,
            "Ki": controller.config.Ki,
            "Kd": controller.config.Kd,
        }

    # ========================================================================
    # LAYER 3: MPC METHODS
    # ========================================================================

    async def optimize_mpc_weights(
        self,
        start_date: date,
        current_state: dict
    ) -> MPCOptimizationResult:
        """Run MPC optimization to calculate optimal constraint weights."""
        if not self.mpc_bridge:
            raise RuntimeError("MPC bridge not initialized")

        # Get forecast from resilience service
        predicted_metrics = await self.resilience.get_forecast(
            start_date=start_date,
            weeks=self.mpc_bridge.config.prediction_horizon_weeks,
        )

        # Optimize weights
        optimal_weights = self.mpc_bridge.optimize_weights(
            predicted_metrics=predicted_metrics,
            current_state=None,  # Will use internal state
        )

        # Determine system state
        util_peak = max(predicted_metrics.get("utilization_trajectory", [0.75]))
        system_state = self._determine_system_state(util_peak)

        result = MPCOptimizationResult(
            timestamp=datetime.now(),
            optimal_weights=optimal_weights,
            system_state=system_state,
            predicted_peak_utilization=util_peak,
            predicted_min_coverage=min(predicted_metrics.get("coverage_trajectory", [0.95])),
            weight_adjustments_applied=self._get_weight_adjustment_descriptions(optimal_weights),
        )

        self.last_mpc_update = datetime.now()

        return result

    def _determine_system_state(self, utilization: float) -> str:
        """Determine system state from utilization."""
        if utilization > 0.90:
            return "BLACK"
        elif utilization > 0.85:
            return "RED"
        elif utilization > 0.80:
            return "ORANGE"
        elif utilization > 0.75:
            return "YELLOW"
        else:
            return "GREEN"

    def _get_weight_adjustment_descriptions(self, weights: dict) -> list[str]:
        """Generate human-readable descriptions of weight adjustments."""
        descriptions = []

        base_weights = self.mpc_bridge.config.base_weights if self.mpc_bridge else {}

        for key, value in weights.items():
            if key in base_weights:
                base_value = base_weights[key]
                if value > base_value * 1.2:
                    pct = ((value / base_value) - 1) * 100
                    descriptions.append(f"{key} increased {pct:.0f}%")
                elif value < base_value * 0.8:
                    pct = (1 - (value / base_value)) * 100
                    descriptions.append(f"{key} decreased {pct:.0f}%")

        return descriptions

    # ========================================================================
    # UNIFIED METHODS
    # ========================================================================

    async def update_all(self) -> dict:
        """
        Update all control layers in sequence.

        Returns dict with results from all layers.
        """
        results = {}

        # Layer 1: Kalman updates
        if self.config.enable_kalman_system_health:
            metrics = await self._collect_current_metrics()
            system_health = await self.update_system_health_estimate(metrics)
            results["kalman_system_health"] = system_health

        # Layer 2: PID updates
        if any([
            self.config.enable_pid_utilization,
            self.config.enable_pid_coverage,
            self.config.enable_pid_workload
        ]):
            current_values = await self._get_current_pid_values()
            pid_result = await self.update_pid_controllers(current_values)
            results["pid"] = pid_result

        # Layer 3: MPC (less frequent, check if due)
        if self.config.enable_mpc and self._is_mpc_update_due():
            current_state = await self._get_current_state_dict()
            mpc_result = await self.optimize_mpc_weights(
                start_date=date.today(),
                current_state=current_state
            )
            results["mpc"] = mpc_result

        logger.info(f"Control system update complete: {list(results.keys())}")

        return results

    async def get_control_state(self) -> dict:
        """Get unified control system state."""
        state = {
            "timestamp": datetime.now(),
            "layer1_kalman": {},
            "layer2_pid": {},
            "layer3_mpc": {},
        }

        # Layer 1 state
        if self.workload_filters:
            state["layer1_kalman"]["workload_filters_active"] = len(self.workload_filters)

        if self.system_health_ekf:
            state["layer1_kalman"]["system_health_estimate"] = {
                "utilization": self.system_health_ekf.x[0],
                "coverage": self.system_health_ekf.x[1],
                "confidence": self._assess_estimate_quality(self.system_health_ekf),
            }

        # Layer 2 state
        if self.pid_bridge:
            enabled_controllers = [
                name for name, enabled in self.pid_bridge.pid_enabled_for.items()
                if enabled
            ]
            state["layer2_pid"]["controllers_enabled"] = enabled_controllers

            # Get current errors
            current_errors = {}
            for name in enabled_controllers:
                pid_name = self.pid_bridge.setpoint_to_pid.get(name)
                if pid_name and pid_name in self.pid_bank.controllers:
                    controller = self.pid_bank.controllers[pid_name]
                    current_errors[name] = controller.previous_error
            state["layer2_pid"]["current_errors"] = current_errors

        # Layer 3 state
        if self.mpc_bridge:
            state["layer3_mpc"]["enabled"] = True
            state["layer3_mpc"]["prediction_horizon_weeks"] = self.mpc_bridge.config.prediction_horizon_weeks
            state["layer3_mpc"]["control_horizon_weeks"] = self.mpc_bridge.config.control_horizon_weeks

        return state

    # ========================================================================
    # HELPER METHODS
    # ========================================================================

    async def _collect_current_metrics(self) -> dict:
        """Collect current system metrics."""
        # TODO: Implement actual metric collection from database
        return {
            "utilization": 0.78,
            "coverage": 0.94,
            "stability": 0.92,
            "burnout_risk": 0.12,
        }

    async def _get_current_pid_values(self) -> dict:
        """Get current values for PID controllers."""
        metrics = await self._collect_current_metrics()
        return {
            "faculty_utilization": metrics["utilization"],
            "coverage_rate": metrics["coverage"],
            "workload_balance": 0.15,  # TODO: Calculate from actual data
        }

    async def _get_current_state_dict(self) -> dict:
        """Get current state for MPC."""
        metrics = await self._collect_current_metrics()
        return {
            "utilization": metrics["utilization"],
            "coverage": metrics["coverage"],
            "workload_variance": 0.12,  # TODO: Calculate
        }

    def _is_mpc_update_due(self) -> bool:
        """Check if MPC update is due based on recalculation frequency."""
        if self.last_mpc_update is None:
            return True

        days_since_update = (datetime.now() - self.last_mpc_update).days
        return days_since_update >= self.config.mpc_recalculation_days
```

---

*Due to length constraints, I'll continue with the remaining sections in the next part. The document will include:*

- Celery Tasks
- Integration Points
- Database Schema
- Configuration & Tuning
- Testing Strategy
- Performance Metrics
- Migration & Deployment

Would you like me to continue with the complete specification?

---

## Celery Tasks

### Periodic Control Updates

```python
"""
Celery tasks for periodic control system updates.

File: backend/app/celery/tasks/control_theory.py
"""

from celery import shared_task
from datetime import datetime
import logging

from app.db.session import get_db
from app.resilience.service import ResilienceService
from app.services.control.orchestrator import ControlTheoryService

logger = logging.getLogger(__name__)


@shared_task(name="control.update_kalman_filters")
def update_all_kalman_filters():
    """
    Update all Kalman filters (every 15 minutes).

    - Workload filters for all faculty
    - System health Extended Kalman Filter
    """
    logger.info("Starting Kalman filter updates")

    db = next(get_db())
    resilience = ResilienceService(db=db)
    control_service = ControlTheoryService(db=db, resilience_service=resilience)

    # Initialize if needed
    control_service.initialize()

    # Update system health EKF
    metrics = control_service._collect_current_metrics()
    system_health = control_service.update_system_health_estimate(metrics)

    logger.info(
        f"System health updated: util={system_health.utilization['estimate']:.2f}, "
        f"coverage={system_health.coverage['estimate']:.2f}"
    )

    # Update workload filters for all faculty
    faculty_ids = _get_all_faculty_ids(db)
    for person_id in faculty_ids:
        # Get measurements
        scheduled = _get_scheduled_hours(db, person_id)
        self_report = _get_self_reported_hours(db, person_id)  # May be None

        estimate = control_service.update_workload_estimate(
            person_id=person_id,
            scheduled_hours=scheduled,
            self_reported=self_report,
        )

        logger.debug(f"Faculty {person_id}: {estimate.estimated_hours:.1f}h ± {estimate.uncertainty_std:.1f}h")

    logger.info(f"Kalman filter updates complete: {len(faculty_ids)} faculty")


@shared_task(name="control.update_pid_controllers")
def update_all_pid_controllers():
    """
    Update all PID controllers (every 15 minutes).

    - Utilization PID
    - Coverage PID
    - Workload Balance PID
    """
    logger.info("Starting PID controller updates")

    db = next(get_db())
    resilience = ResilienceService(db=db)
    control_service = ControlTheoryService(db=db, resilience_service=resilience)

    control_service.initialize()

    # Get current values
    current_values = control_service._get_current_pid_values()

    # Update controllers
    result = control_service.update_pid_controllers(current_values)

    # Log corrections
    for correction in result.get("pid_corrections", []):
        logger.info(
            f"PID correction [{correction.controller_name}]: "
            f"signal={correction.control_signal:.3f}, "
            f"action={correction.action_type}"
        )

    # Apply corrective actions if needed
    for action in result.get("merged_actions", []):
        _apply_corrective_action(db, action)

    logger.info(f"PID updates complete: {len(result.get('merged_actions', []))} actions")


@shared_task(name="control.run_mpc_optimization")
def run_mpc_optimization():
    """
    Run MPC optimization (weekly).

    - Forecast 4-week horizon
    - Calculate optimal constraint weights
    - Store for next schedule generation
    """
    logger.info("Starting MPC optimization")

    db = next(get_db())
    resilience = ResilienceService(db=db)
    control_service = ControlTheoryService(db=db, resilience_service=resilience)

    control_service.initialize()

    # Run optimization
    from datetime import date
    current_state = control_service._get_current_state_dict()
    mpc_result = control_service.optimize_mpc_weights(
        start_date=date.today(),
        current_state=current_state
    )

    # Store weights for use by scheduling engine
    _store_mpc_weights(db, mpc_result.optimal_weights)

    logger.info(
        f"MPC optimization complete: state={mpc_result.system_state}, "
        f"weights={mpc_result.optimal_weights}"
    )

    # Alert if crisis predicted
    if mpc_result.system_state in ["RED", "BLACK"]:
        _send_crisis_alert(db, mpc_result)


@shared_task(name="control.auto_tune_pid")
def auto_tune_all_pid_controllers():
    """
    Auto-tune PID controllers using historical data (monthly).

    Uses simulation-based optimization on last 90 days of data.
    """
    logger.info("Starting PID auto-tuning")

    db = next(get_db())
    resilience = ResilienceService(db=db)
    control_service = ControlTheoryService(db=db, resilience_service=resilience)

    control_service.initialize()

    # Get historical data
    historical_data = _get_historical_metrics(db, days=90)

    for controller_name in ["utilization", "coverage", "workload_balance"]:
        # Simulate with different gains
        # Use optimization to find best gains
        # Apply if improvement > 10%
        logger.info(f"Tuning {controller_name}...")

        # TODO: Implement optimization-based tuning
        # See CONTROL_THEORY_TUNING_GUIDE.md for algorithms

    logger.info("PID auto-tuning complete")


# ========================================================================
# HELPER FUNCTIONS
# ========================================================================

def _get_all_faculty_ids(db):
    """Get all active faculty IDs."""
    # TODO: Implement database query
    return []


def _get_scheduled_hours(db, person_id):
    """Get scheduled hours for person from assignments."""
    # TODO: Implement database query
    return 60.0


def _get_self_reported_hours(db, person_id):
    """Get self-reported hours from surveys."""
    # TODO: Implement database query
    return None


def _apply_corrective_action(db, action):
    """Apply a corrective action to the schedule."""
    # TODO: Implement action execution
    pass


def _store_mpc_weights(db, weights: dict):
    """Store MPC weights for scheduling engine."""
    # TODO: Implement database storage
    pass


def _send_crisis_alert(db, mpc_result):
    """Send alert when crisis is predicted."""
    # TODO: Implement alerting
    pass


def _get_historical_metrics(db, days: int):
    """Get historical metrics for tuning."""
    # TODO: Implement database query
    return []
```

### Celery Beat Schedule

```python
"""
Celery beat schedule for control theory tasks.

File: backend/app/celery/beat_schedule.py (add to existing)
"""

from celery.schedules import crontab

CELERYBEAT_SCHEDULE = {
    # ... existing tasks ...

    # Control Theory Tasks
    "control-update-kalman-filters": {
        "task": "control.update_kalman_filters",
        "schedule": 900.0,  # Every 15 minutes
    },
    "control-update-pid-controllers": {
        "task": "control.update_pid_controllers",
        "schedule": 900.0,  # Every 15 minutes
    },
    "control-run-mpc-optimization": {
        "task": "control.run_mpc_optimization",
        "schedule": crontab(hour=8, minute=0, day_of_week=1),  # Monday 8am
    },
    "control-auto-tune-pid": {
        "task": "control.auto_tune_pid",
        "schedule": crontab(hour=2, minute=0, day_of_month=1),  # 1st of month, 2am
    },
}
```

---

## Integration Points

### Connection to Resilience Framework

```python
"""
Integration with existing resilience framework.

The control theory service complements (not replaces) resilience monitoring.
"""

# 1. FORECASTING
# Control service uses ResilienceService.get_forecast() for MPC predictions

from app.resilience.service import ResilienceService

resilience = ResilienceService(db=db)
forecast = await resilience.get_forecast(
    start_date=date.today(),
    weeks=4,
)
# Returns: {
#   'utilization_trajectory': [0.78, 0.80, 0.82, 0.84],
#   'coverage_trajectory': [0.95, 0.94, 0.93, 0.92],
#   'burnout_risk_trajectory': [0.10, 0.12, 0.15, 0.18],
# }

# 2. DEFENSE LEVEL INTEGRATION
# PID gains adjust based on defense level

from app.resilience.defense_in_depth import get_current_defense_level

defense_level = get_current_defense_level(db)

if defense_level == "RED":
    # Increase PID gains for aggressive correction
    utilization_pid.config.Kp *= 2.0
    utilization_pid.config.Ki *= 1.5

# 3. SPC MONITORING
# Kalman filter innovations feed into SPC charts

from app.resilience.spc_monitoring import SPCMonitor

spc_monitor = SPCMonitor()

for estimate in kalman_filter.history:
    if estimate.measurement_residual is not None:
        spc_monitor.add_point(
            metric="kalman_innovation_utilization",
            value=estimate.measurement_residual
        )

# Check for out-of-control conditions
if spc_monitor.is_out_of_control("kalman_innovation_utilization"):
    logger.warning("Kalman filter may need retuning - innovation out of control")
```

### Connection to Scheduler Engine

```python
"""
Integration with scheduling engine for MPC dynamic weights.
"""

# MODIFIED: backend/app/scheduling/engine.py

class SchedulingEngine:
    def generate(
        self,
        start_date: date,
        end_date: date,
        algorithm: str = "cp_sat",
        dynamic_weights: Optional[dict[str, float]] = None,  # NEW
        **kwargs
    ) -> dict:
        """
        Generate schedule with optional MPC-provided weights.

        Args:
            dynamic_weights: Optional constraint weights from MPC optimization.
                           If provided, overrides ConstraintManager defaults.
        """

        # Get weights (MPC takes precedence)
        if dynamic_weights:
            logger.info(f"Using MPC-provided weights: {dynamic_weights}")
            weights = dynamic_weights
        else:
            # Use default weights from constraint manager
            weights = self.constraint_manager.get_weights()

        # Pass to solver
        result = self.solver.solve(
            context=context,
            weights=weights,  # Dynamic or default
            **kwargs
        )

        return result


# USAGE: Scheduling with MPC
from app.services.control.orchestrator import ControlTheoryService

control_service = ControlTheoryService(db, resilience)
mpc_result = await control_service.optimize_mpc_weights(
    start_date=date.today(),
    current_state={"utilization": 0.78, "coverage": 0.95}
)

# Generate schedule with optimized weights
engine = SchedulingEngine(db, start_date, end_date)
schedule = engine.generate(
    algorithm="cp_sat",
    dynamic_weights=mpc_result.optimal_weights  # Use MPC weights
)
```

### Connection to Homeostasis

```python
"""
Integration with homeostasis feedback loops.

PID controllers enhance (not replace) homeostasis logic.
"""

# BEFORE: Ad-hoc homeostasis correction
from app.resilience.homeostasis import HomeostasisMonitor

homeostasis = HomeostasisMonitor()
action = homeostasis.check_feedback_loop(
    loop_id=utilization_loop.id,
    current_value=0.82  # Raw measurement
)

# AFTER: PID-enhanced homeostasis
from app.services.control.pid.bridge import PIDHomeostasisBridge

pid_bridge = PIDHomeostasisBridge(homeostasis)
action = pid_bridge.check_feedback_loop_with_pid(
    loop_id=utilization_loop.id,
    current_value=0.82  # Kalman-filtered estimate
)

# Action now includes PID diagnostics
print(action.pid_diagnostics)
# {
#   'control_signal': -0.14,
#   'P_term': -0.70,
#   'I_term': -0.02,
#   'D_term': -0.04,
#   'integral_saturated': False
# }
```

---

## Database Schema

### Kalman Filter State Table

```sql
-- File: backend/alembic/versions/{timestamp}_add_control_theory_tables.py
-- Note: Actual filename will be generated by Alembic when running:
-- alembic revision --autogenerate -m "Add control theory tables"

CREATE TABLE kalman_filter_states (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    person_id UUID NOT NULL REFERENCES persons(id) ON DELETE CASCADE,
    timestamp TIMESTAMP NOT NULL DEFAULT NOW(),

    -- State estimate
    estimated_hours FLOAT NOT NULL,
    trend FLOAT NOT NULL,
    seasonal_component FLOAT NOT NULL,

    -- Uncertainty
    uncertainty_std FLOAT NOT NULL,
    confidence_95_lower FLOAT NOT NULL,
    confidence_95_upper FLOAT NOT NULL,

    -- Diagnostics
    measurement_residual FLOAT,
    measurements_used TEXT[],

    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),

    INDEX idx_kalman_person_timestamp (person_id, timestamp DESC)
);
```

### PID Controller State Table

```sql
CREATE TABLE pid_controller_states (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    controller_name VARCHAR(50) NOT NULL,
    timestamp TIMESTAMP NOT NULL DEFAULT NOW(),

    -- Current values
    current_value FLOAT NOT NULL,
    setpoint FLOAT NOT NULL,
    error FLOAT NOT NULL,
    control_signal FLOAT NOT NULL,

    -- Term breakdown
    p_term FLOAT NOT NULL,
    i_term FLOAT NOT NULL,
    d_term FLOAT NOT NULL,

    -- State variables
    integral FLOAT NOT NULL,
    previous_error FLOAT NOT NULL,

    -- Gains (for history tracking)
    kp FLOAT NOT NULL,
    ki FLOAT NOT NULL,
    kd FLOAT NOT NULL,

    -- Diagnostics
    integral_saturated BOOLEAN DEFAULT FALSE,
    output_saturated BOOLEAN DEFAULT FALSE,
    dt FLOAT NOT NULL,

    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),

    INDEX idx_pid_controller_timestamp (controller_name, timestamp DESC)
);
```

### MPC Optimization History Table

```sql
CREATE TABLE mpc_optimization_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    timestamp TIMESTAMP NOT NULL DEFAULT NOW(),

    -- Optimization parameters
    start_date DATE NOT NULL,
    prediction_horizon_weeks INT NOT NULL,
    control_horizon_weeks INT NOT NULL,

    -- Optimal weights (JSONB for flexibility)
    optimal_weights JSONB NOT NULL,

    -- Predicted state
    system_state VARCHAR(10) NOT NULL,
    predicted_peak_utilization FLOAT NOT NULL,
    predicted_min_coverage FLOAT NOT NULL,

    -- Weight adjustments
    weight_adjustments_applied TEXT[],

    -- Performance tracking
    iteration_count INT,
    solve_time_seconds FLOAT,

    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),

    INDEX idx_mpc_timestamp (timestamp DESC),
    INDEX idx_mpc_system_state (system_state, timestamp DESC)
);
```

### Control System Config Table

```sql
CREATE TABLE control_system_config (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    version INT NOT NULL DEFAULT 1,

    -- Feature flags
    enable_kalman_workload BOOLEAN DEFAULT TRUE,
    enable_kalman_system_health BOOLEAN DEFAULT TRUE,
    enable_pid_utilization BOOLEAN DEFAULT TRUE,
    enable_pid_coverage BOOLEAN DEFAULT TRUE,
    enable_pid_workload BOOLEAN DEFAULT FALSE,
    enable_mpc BOOLEAN DEFAULT TRUE,

    -- Update frequencies
    kalman_update_minutes INT DEFAULT 15,
    pid_update_minutes INT DEFAULT 15,
    mpc_recalculation_days INT DEFAULT 7,

    -- Metadata
    applied_at TIMESTAMP,
    applied_by UUID REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW(),

    INDEX idx_config_version (version DESC)
);
```

---

## Configuration & Tuning

### Default Configuration

```python
"""
Default control system configuration.

File: backend/app/services/control/config.py
"""

from dataclasses import dataclass


@dataclass
class KalmanFilterDefaults:
    """Default parameters for Kalman filters."""

    # Process noise (Q matrix diagonal)
    process_noise_workload: float = 0.02
    process_noise_trend: float = 0.01
    process_noise_seasonal: float = 0.015

    # Measurement noise (R matrix diagonal)
    measurement_noise_scheduled: float = 0.05
    measurement_noise_self_report: float = 0.15
    measurement_noise_call_volume: float = 0.10

    # System health EKF
    process_noise_system_health: float = 0.01
    measurement_noise_system_health: float = 0.03


@dataclass
class PIDDefaults:
    """Default PID controller parameters."""

    # Utilization PID
    utilization_Kp: float = 10.0
    utilization_Ki: float = 0.5
    utilization_Kd: float = 2.0
    utilization_setpoint: float = 0.75
    utilization_output_limits: tuple = (-0.2, 0.2)
    utilization_integral_limits: tuple = (-5.0, 5.0)

    # Workload Balance PID
    workload_Kp: float = 5.0
    workload_Ki: float = 0.3
    workload_Kd: float = 1.0
    workload_setpoint: float = 0.0  # Zero imbalance
    workload_output_limits: tuple = (-0.15, 0.15)
    workload_integral_limits: tuple = (-3.0, 3.0)

    # Coverage PID
    coverage_Kp: float = 12.0
    coverage_Ki: float = 0.8
    coverage_Kd: float = 1.5
    coverage_setpoint: float = 0.95
    coverage_output_limits: tuple = (-0.1, 0.1)
    coverage_integral_limits: tuple = (-10.0, 10.0)


@dataclass
class MPCDefaults:
    """Default MPC parameters."""

    prediction_horizon_weeks: int = 4
    control_horizon_weeks: int = 2
    recalculation_frequency_days: int = 7

    # Base weights
    base_coverage_weight: float = 1000.0
    base_utilization_buffer_weight: float = 20.0
    base_equity_weight: float = 10.0
    base_continuity_weight: float = 5.0
    base_preference_weight: float = 8.0
    base_hub_protection_weight: float = 15.0
    base_n1_vulnerability_weight: float = 25.0

    # Weight adjustment parameters
    crisis_multiplier: float = 2.0
    smoothing_alpha: float = 0.3
```

### Environment Variables

```bash
# File: .env (add to existing)

# ========================================================================
# CONTROL THEORY CONFIGURATION
# ========================================================================

# Feature Flags
CONTROL_ENABLE_KALMAN_WORKLOAD=true
CONTROL_ENABLE_KALMAN_SYSTEM_HEALTH=true
CONTROL_ENABLE_PID_UTILIZATION=true
CONTROL_ENABLE_PID_COVERAGE=true
CONTROL_ENABLE_PID_WORKLOAD=false
CONTROL_ENABLE_MPC=true

# Update Frequencies
CONTROL_KALMAN_UPDATE_MINUTES=15
CONTROL_PID_UPDATE_MINUTES=15
CONTROL_MPC_RECALCULATION_DAYS=7

# Kalman Filter Tuning
KALMAN_PROCESS_NOISE_WORKLOAD=0.02
KALMAN_MEASUREMENT_NOISE_SCHEDULED=0.05
KALMAN_MEASUREMENT_NOISE_SELF_REPORT=0.15

# PID Tuning - Utilization
PID_UTILIZATION_KP=10.0
PID_UTILIZATION_KI=0.5
PID_UTILIZATION_KD=2.0
PID_UTILIZATION_SETPOINT=0.75

# PID Tuning - Coverage
PID_COVERAGE_KP=12.0
PID_COVERAGE_KI=0.8
PID_COVERAGE_KD=1.5
PID_COVERAGE_SETPOINT=0.95

# MPC Configuration
MPC_PREDICTION_HORIZON_WEEKS=4
MPC_CONTROL_HORIZON_WEEKS=2
MPC_BASE_COVERAGE_WEIGHT=1000.0
MPC_BASE_UTILIZATION_BUFFER_WEIGHT=20.0
MPC_CRISIS_MULTIPLIER=2.0
```

### Tuning Procedures

See `/home/user/Autonomous-Assignment-Program-Manager/docs/architecture/CONTROL_THEORY_TUNING_GUIDE.md` for complete tuning procedures:

- **Kalman Filters:** Noise covariance calibration (Section 5)
- **PID Controllers:** Ziegler-Nichols, Cohen-Coon, Relay Feedback (Section 3)
- **MPC:** Weight sensitivity analysis (Appendix A)

---

*Specification continues with Testing Strategy, Performance Metrics, and Migration sections...*


## Testing Strategy

### Unit Tests

#### Layer 1: Kalman Filter Tests

```python
"""
Unit tests for Kalman filters.

File: backend/tests/services/control/test_kalman_filters.py
"""

import pytest
import numpy as np
from datetime import datetime
from uuid import uuid4

from app.services.control.kalman.workload_filter import WorkloadKalmanFilter
from app.services.control.kalman.schedule_health_ekf import ScheduleHealthEKF


class TestWorkloadKalmanFilter:
    """Test suite for workload estimation Kalman filter."""

    def test_initialization(self):
        """Test filter initializes with correct state."""
        person_id = uuid4()
        kf = WorkloadKalmanFilter(person_id=person_id, initial_hours=60.0)

        assert kf.x[0] == 60.0  # Initial hours
        assert kf.x[1] == 0.0   # Initial trend
        assert kf.x[2] == 0.0   # Initial seasonal
        assert kf.person_id == person_id

    def test_prediction_step(self):
        """Test prediction without measurement."""
        kf = WorkloadKalmanFilter(person_id=uuid4(), initial_hours=60.0)

        # Predict forward
        kf.predict()

        # State should evolve (hours + trend)
        assert kf.x[0] > 60.0 or kf.x[0] < 60.0 or kf.x[0] == 60.0
        # Uncertainty should increase
        assert np.trace(kf.P) > np.trace(kf._initial_P)

    def test_update_with_single_measurement(self):
        """Test Kalman update with scheduled hours only."""
        kf = WorkloadKalmanFilter(person_id=uuid4(), initial_hours=60.0)

        estimate = kf.update({"scheduled_hours": 65.0})

        # Estimate should move toward measurement
        assert 60.0 < estimate.estimated_hours < 65.0
        # Uncertainty should decrease
        assert estimate.uncertainty_std < 10.0

    def test_update_with_multiple_measurements(self):
        """Test sensor fusion with multiple measurements."""
        kf = WorkloadKalmanFilter(person_id=uuid4(), initial_hours=60.0)

        estimate = kf.update({
            "scheduled_hours": 65.0,
            "self_reported": 70.0,  # Faculty reports more
            "call_volume": 62.0,
        })

        # Should be weighted average of measurements
        assert 62.0 < estimate.estimated_hours < 68.0
        # Uncertainty should be lower than single measurement
        assert estimate.uncertainty_std < 5.0

    def test_confidence_intervals(self):
        """Test 95% confidence interval calculation."""
        kf = WorkloadKalmanFilter(person_id=uuid4(), initial_hours=60.0)
        estimate = kf.update({"scheduled_hours": 65.0})

        # CI should contain estimate
        assert estimate.confidence_95_lower < estimate.estimated_hours < estimate.confidence_95_upper

        # CI width should be ~2*1.96*std
        width = estimate.confidence_95_upper - estimate.confidence_95_lower
        expected_width = 2 * 1.96 * estimate.uncertainty_std
        assert abs(width - expected_width) < 0.1

    def test_measurement_residual(self):
        """Test innovation (measurement error) calculation."""
        kf = WorkloadKalmanFilter(person_id=uuid4(), initial_hours=60.0)

        # First update
        estimate1 = kf.update({"scheduled_hours": 65.0})

        # Second update with different measurement
        estimate2 = kf.update({"scheduled_hours": 62.0})

        # Residual should reflect difference from prediction
        assert estimate2.measurement_residual is not None
        assert abs(estimate2.measurement_residual) < 5.0


class TestScheduleHealthEKF:
    """Test suite for Extended Kalman Filter."""

    def test_initialization(self):
        """Test EKF initializes with correct state."""
        ekf = ScheduleHealthEKF(initial_state=[0.75, 0.95, 0.95, 0.10])

        assert ekf.x[0] == 0.75  # Utilization
        assert ekf.x[1] == 0.95  # Coverage
        assert ekf.x[2] == 0.95  # Stability
        assert ekf.x[3] == 0.10  # Burnout risk

    def test_nonlinear_measurement_function(self):
        """Test nonlinear measurement mapping."""
        ekf = ScheduleHealthEKF(initial_state=[0.75, 0.95, 0.95, 0.10])

        # Simulate measurement
        z = np.array([0.78, 0.94, 0.93, 0.12])
        ekf.update(z)

        # State should move toward measurement
        assert 0.75 < ekf.x[0] < 0.78
        assert 0.94 < ekf.x[1] < 0.95

    def test_uncertainty_quantification(self):
        """Test uncertainty estimation."""
        ekf = ScheduleHealthEKF(initial_state=[0.75, 0.95, 0.95, 0.10])

        # Before update
        initial_uncertainty = ekf.get_uncertainty(0)

        # Update with measurement
        ekf.update([0.78, 0.94, 0.93, 0.12])

        # Uncertainty should decrease
        updated_uncertainty = ekf.get_uncertainty(0)
        assert updated_uncertainty < initial_uncertainty

    def test_confidence_interval(self):
        """Test confidence interval calculation."""
        ekf = ScheduleHealthEKF(initial_state=[0.75, 0.95, 0.95, 0.10])
        ekf.update([0.78, 0.94, 0.93, 0.12])

        ci = ekf.get_confidence_interval(index=0, confidence=0.95)

        assert len(ci) == 2
        assert ci[0] < ekf.x[0] < ci[1]
```

#### Layer 2: PID Controller Tests

```python
"""
Unit tests for PID controllers.

File: backend/tests/services/control/test_pid_controllers.py
"""

import pytest
from app.services.control.pid.controllers import PIDState, PIDConfig, PIDControllerBank


class TestPIDState:
    """Test suite for PID state and control logic."""

    def test_proportional_only(self):
        """Test P-only controller."""
        config = PIDConfig(
            name="test",
            setpoint=0.75,
            Kp=10.0,
            Ki=0.0,
            Kd=0.0
        )

        pid = PIDState(config)

        # Error = -0.10 (current > setpoint)
        result = pid.update(current_value=0.85)

        # Control signal should be proportional to error
        assert result["control_signal"] == pytest.approx(-1.0, abs=0.01)  # 10.0 * -0.10
        assert result["P_term"] == pytest.approx(-1.0, abs=0.01)
        assert result["I_term"] == 0.0
        assert result["D_term"] == 0.0

    def test_integral_accumulation(self):
        """Test integral term accumulates error."""
        config = PIDConfig(
            name="test",
            setpoint=0.75,
            Kp=0.0,
            Ki=0.5,
            Kd=0.0
        )

        pid = PIDState(config)

        # Step 1: error = -0.10
        result1 = pid.update(current_value=0.85)
        assert pid.integral == pytest.approx(-0.10, abs=0.01)

        # Step 2: error = -0.10 again
        result2 = pid.update(current_value=0.85)
        assert pid.integral == pytest.approx(-0.20, abs=0.01)

        # Control signal should reflect accumulated integral
        assert result2["I_term"] == pytest.approx(-0.10, abs=0.01)  # 0.5 * -0.20

    def test_derivative_term(self):
        """Test derivative term responds to error rate."""
        config = PIDConfig(
            name="test",
            setpoint=0.75,
            Kp=0.0,
            Ki=0.0,
            Kd=2.0
        )

        pid = PIDState(config)

        # Step 1: error = -0.05
        result1 = pid.update(current_value=0.80)

        # Step 2: error = -0.10 (changing rapidly)
        result2 = pid.update(current_value=0.85)

        # Derivative should be negative (error increasing)
        assert result2["D_term"] < 0

    def test_anti_windup_integral_clamping(self):
        """Test integral clamping prevents windup."""
        config = PIDConfig(
            name="test",
            setpoint=0.75,
            Kp=0.0,
            Ki=1.0,
            Kd=0.0,
            integral_limits=(-2.0, 2.0)
        )

        pid = PIDState(config)

        # Accumulate large error
        for _ in range(50):
            pid.update(current_value=0.90)  # Persistent error

        # Integral should be clamped
        assert pid.integral == pytest.approx(-2.0, abs=0.01)

    def test_output_saturation(self):
        """Test output limits are respected."""
        config = PIDConfig(
            name="test",
            setpoint=0.75,
            Kp=100.0,  # Very high gain
            Ki=0.0,
            Kd=0.0,
            output_limits=(-0.2, 0.2)
        )

        pid = PIDState(config)

        result = pid.update(current_value=0.50)  # Large error

        # Output should be saturated
        assert result["control_signal"] == 0.2
        assert result["output_saturated"] is True


class TestPIDControllerBank:
    """Test suite for PID controller bank."""

    def test_create_default_controllers(self):
        """Test default controller creation."""
        bank = PIDControllerBank()

        assert "utilization" in bank.controllers
        assert "coverage" in bank.controllers
        assert "workload_balance" in bank.controllers

    def test_update_all_controllers(self):
        """Test batch update of all controllers."""
        bank = PIDControllerBank()

        results = bank.update_all({
            "utilization": 0.82,
            "coverage": 0.93,
            "workload_balance": 0.18
        })

        assert len(results) == 3
        assert "utilization" in results
        assert results["utilization"]["control_signal"] < 0  # Reduce utilization

    def test_ziegler_nichols_tuning(self):
        """Test Ziegler-Nichols auto-tuning."""
        bank = PIDControllerBank()

        Ku = 15.0  # Ultimate gain
        Pu = 7.0   # Ultimate period (days)

        bank.tune_ziegler_nichols("utilization", Ku, Pu)

        controller = bank.controllers["utilization"]

        # Check gains were calculated
        assert controller.config.Kp == pytest.approx(9.0, abs=0.1)  # 0.6 * Ku
        assert controller.config.Ki == pytest.approx(2.57, abs=0.1)  # 1.2 * Ku / Pu
        assert controller.config.Kd == pytest.approx(7.88, abs=0.1)  # 0.075 * Ku * Pu
```

#### Layer 3: MPC Tests

```python
"""
Unit tests for MPC optimizer.

File: backend/tests/services/control/test_mpc_bridge.py
"""

import pytest
from datetime import date, timedelta
from app.services.control.mpc.bridge import MPCSchedulerBridge, MPCConfig, StateVector


class TestMPCSchedulerBridge:
    """Test suite for MPC scheduler bridge."""

    def test_weight_adjustment_crisis_mode(self):
        """Test weight adjustment during predicted crisis."""
        config = MPCConfig(
            prediction_horizon_weeks=4,
            control_horizon_weeks=2
        )

        bridge = MPCSchedulerBridge(
            resilience_service=Mock(),
            constraint_manager=Mock(),
            config=config
        )

        # Simulate predicted crisis
        predicted_metrics = {
            'utilization_trajectory': [0.82, 0.85, 0.88, 0.91],
            'coverage_trajectory': [0.95, 0.94, 0.93, 0.92],
        }

        weights = bridge.optimize_weights(
            predicted_metrics=predicted_metrics,
            current_state=None
        )

        # Coverage weight should increase
        assert weights['coverage'] > config.base_weights['coverage']

        # Utilization buffer should increase significantly
        assert weights['utilization_buffer'] > config.base_weights['utilization_buffer'] * 2.0

        # Preference should decrease
        assert weights['preference'] < config.base_weights['preference']

    def test_weight_adjustment_recovery_mode(self):
        """Test weight adjustment during recovery (healthy state)."""
        config = MPCConfig()
        bridge = MPCSchedulerBridge(
            resilience_service=Mock(),
            constraint_manager=Mock(),
            config=config
        )

        # Simulate healthy state
        predicted_metrics = {
            'utilization_trajectory': [0.70, 0.71, 0.72, 0.73],
            'coverage_trajectory': [0.95, 0.95, 0.96, 0.96],
        }

        weights = bridge.optimize_weights(
            predicted_metrics=predicted_metrics,
            current_state=None
        )

        # Equity should be prioritized during recovery
        assert weights['equity'] >= config.base_weights['equity']

        # Preference should be full weight
        assert weights['preference'] >= config.base_weights['preference'] * 0.9

    def test_ema_smoothing(self):
        """Test exponential moving average smoothing."""
        config = MPCConfig(smoothing_alpha=0.3)
        bridge = MPCSchedulerBridge(
            resilience_service=Mock(),
            constraint_manager=Mock(),
            config=config
        )

        # First optimization
        weights1 = bridge.optimize_weights(
            predicted_metrics={'utilization_trajectory': [0.75], 'coverage_trajectory': [0.95]},
            current_state=None
        )

        # Second optimization (sudden spike)
        weights2 = bridge.optimize_weights(
            predicted_metrics={'utilization_trajectory': [0.90], 'coverage_trajectory': [0.95]},
            current_state=None
        )

        # Change should be moderated by EMA
        delta = abs(weights2['utilization_buffer'] - weights1['utilization_buffer'])
        assert delta < 50.0  # Smoothing limits drastic changes

    def test_system_state_determination(self):
        """Test system state classification from utilization."""
        bridge = MPCSchedulerBridge(
            resilience_service=Mock(),
            constraint_manager=Mock()
        )

        assert bridge._determine_system_state(0.70) == "GREEN"
        assert bridge._determine_system_state(0.78) == "YELLOW"
        assert bridge._determine_system_state(0.83) == "ORANGE"
        assert bridge._determine_system_state(0.88) == "RED"
        assert bridge._determine_system_state(0.92) == "BLACK"
```

### Integration Tests

```python
"""
Integration tests for control theory service.

File: backend/tests/services/control/test_integration.py
"""

import pytest
from datetime import date, timedelta

from app.db.session import get_db
from app.resilience.service import ResilienceService
from app.services.control.orchestrator import ControlTheoryService


@pytest.mark.integration
class TestControlTheoryIntegration:
    """Integration tests for full control system."""

    async def test_full_control_loop(self, db_session):
        """Test complete control loop: Kalman → PID → MPC."""
        resilience = ResilienceService(db=db_session)
        control_service = ControlTheoryService(
            db=db_session,
            resilience_service=resilience
        )

        await control_service.initialize()

        # Update all layers
        results = await control_service.update_all()

        # Verify all layers executed
        assert "kalman_system_health" in results
        assert "pid" in results
        # MPC may not run (weekly schedule)

        # Verify state consistency
        state = await control_service.get_control_state()
        assert state["layer1_kalman"]["workload_filters_active"] >= 0
        assert len(state["layer2_pid"]["controllers_enabled"]) > 0

    async def test_mpc_schedule_generation(self, db_session):
        """Test MPC-driven schedule generation."""
        resilience = ResilienceService(db=db_session)
        control_service = ControlTheoryService(
            db=db_session,
            resilience_service=resilience
        )

        await control_service.initialize()

        # Run MPC optimization
        mpc_result = await control_service.optimize_mpc_weights(
            start_date=date.today(),
            current_state={
                "utilization": 0.78,
                "coverage": 0.95,
                "workload_variance": 0.12
            }
        )

        # Use weights for scheduling
        from app.scheduling.engine import SchedulingEngine

        engine = SchedulingEngine(
            db=db_session,
            start_date=date.today(),
            end_date=date.today() + timedelta(weeks=2)
        )

        schedule = engine.generate(
            algorithm="cp_sat",
            dynamic_weights=mpc_result.optimal_weights
        )

        # Verify schedule generated
        assert len(schedule["assignments"]) > 0

    async def test_celery_task_integration(self, celery_worker):
        """Test Celery tasks execute correctly."""
        from app.celery.tasks.control_theory import (
            update_all_kalman_filters,
            update_all_pid_controllers
        )

        # Run tasks
        result1 = update_all_kalman_filters.apply()
        result2 = update_all_pid_controllers.apply()

        # Verify tasks completed
        assert result1.successful()
        assert result2.successful()
```

---

## Performance Metrics

### Service Metrics

```python
"""
Performance metrics for control theory service.

File: backend/app/services/control/metrics.py
"""

from prometheus_client import Counter, Gauge, Histogram

# Kalman Filter Metrics
kalman_update_duration = Histogram(
    "kalman_filter_update_duration_seconds",
    "Time to update Kalman filter",
    ["filter_type"]
)

kalman_innovation_magnitude = Gauge(
    "kalman_filter_innovation_magnitude",
    "Magnitude of Kalman innovation (measurement error)",
    ["person_id"]
)

kalman_uncertainty = Gauge(
    "kalman_filter_uncertainty_std",
    "Kalman filter uncertainty (std dev)",
    ["filter_type"]
)

# PID Controller Metrics
pid_control_signal = Gauge(
    "pid_controller_control_signal",
    "PID controller output",
    ["controller_name"]
)

pid_error = Gauge(
    "pid_controller_error",
    "PID controller error (setpoint - current)",
    ["controller_name"]
)

pid_integral_term = Gauge(
    "pid_controller_integral_term",
    "PID integral component",
    ["controller_name"]
)

pid_saturation_events = Counter(
    "pid_controller_saturation_events_total",
    "Number of times PID output saturated",
    ["controller_name", "saturation_type"]
)

# MPC Optimizer Metrics
mpc_optimization_duration = Histogram(
    "mpc_optimization_duration_seconds",
    "Time to run MPC optimization"
)

mpc_weight_delta = Gauge(
    "mpc_weight_delta",
    "Change in constraint weights from baseline",
    ["weight_name"]
)

mpc_system_state = Gauge(
    "mpc_system_state_numeric",
    "MPC system state (0=GREEN, 1=YELLOW, 2=ORANGE, 3=RED, 4=BLACK)"
)

mpc_prediction_error = Gauge(
    "mpc_prediction_error",
    "MPC prediction vs actual error",
    ["metric_name"]
)

# Overall Control System Metrics
control_loop_cycles_total = Counter(
    "control_loop_cycles_total",
    "Total number of control loop executions",
    ["layer"]
)
```

### Performance Benchmarks

| Metric | Target | Acceptable | Critical |
|--------|--------|------------|----------|
| **Kalman Update Time** | <10ms | <50ms | >100ms |
| **PID Update Time** | <5ms | <20ms | >50ms |
| **MPC Optimization Time** | <30s | <60s | >120s |
| **Kalman Innovation RMSE** | <0.05 | <0.10 | >0.20 |
| **PID Settling Time** | <7 days | <14 days | >21 days |
| **MPC Prediction Error** | <5% | <10% | >15% |

### Monitoring Dashboard (Grafana)

```yaml
# File: monitoring/grafana/dashboards/control_theory.json

{
  "dashboard": {
    "title": "Control Theory Service",
    "panels": [
      {
        "title": "Kalman Filter Uncertainty",
        "targets": [
          {
            "expr": "kalman_filter_uncertainty_std{filter_type=\"workload\"}"
          }
        ]
      },
      {
        "title": "PID Control Signals",
        "targets": [
          {
            "expr": "pid_controller_control_signal"
          }
        ]
      },
      {
        "title": "MPC System State",
        "targets": [
          {
            "expr": "mpc_system_state_numeric"
          }
        ]
      },
      {
        "title": "PID Saturation Events",
        "targets": [
          {
            "expr": "rate(pid_controller_saturation_events_total[5m])"
          }
        ]
      }
    ]
  }
}
```

---

## Migration & Deployment

### Phase 1: Kalman Filters (Week 1-2)

**Objective:** Deploy state estimation layer

```bash
# Step 1: Database migration
cd backend
alembic revision --autogenerate -m "Add Kalman filter state tables"
alembic upgrade head

# Step 2: Deploy Kalman filter code
git checkout -b feature/control-theory-kalman
# Copy kalman/ module to backend/app/services/control/
pytest tests/services/control/test_kalman_filters.py
git commit -m "feat: Add Kalman filter state estimation"

# Step 3: Enable Kalman filters (feature flag)
# In .env:
CONTROL_ENABLE_KALMAN_WORKLOAD=true
CONTROL_ENABLE_KALMAN_SYSTEM_HEALTH=true

# Step 4: Start Celery task
# backend/app/celery/beat_schedule.py already configured
docker-compose restart celery-beat

# Step 5: Monitor for 1 week
# Check Grafana dashboard for Kalman metrics
# Verify uncertainty converges
```

### Phase 2: PID Controllers (Week 3-4)

**Objective:** Deploy feedback control layer

```bash
# Step 1: Database migration
alembic revision --autogenerate -m "Add PID controller state tables"
alembic upgrade head

# Step 2: Deploy PID code
git checkout -b feature/control-theory-pid
# Copy pid/ module
pytest tests/services/control/test_pid_controllers.py
git commit -m "feat: Add PID feedback controllers"

# Step 3: Enable PID controllers
CONTROL_ENABLE_PID_UTILIZATION=true
CONTROL_ENABLE_PID_COVERAGE=true
# Leave workload PID disabled initially

# Step 4: Auto-tune gains (optional)
python backend/scripts/tune_pid_ziegler_nichols.py

# Step 5: Monitor for 2 weeks
# Watch for oscillation or instability
# Tune gains if needed
```

### Phase 3: MPC (Week 5-6)

**Objective:** Deploy predictive optimization layer

```bash
# Step 1: Database migration
alembic revision --autogenerate -m "Add MPC optimization history table"
alembic upgrade head

# Step 2: Deploy MPC code
git checkout -b feature/control-theory-mpc
# Copy mpc/ module
pytest tests/services/control/test_mpc_bridge.py
git commit -m "feat: Add MPC predictive optimization"

# Step 3: Enable MPC
CONTROL_ENABLE_MPC=true

# Step 4: Integration with scheduling engine
# Modify backend/app/scheduling/engine.py to accept dynamic_weights

# Step 5: Monitor weekly MPC runs
# Check weight adjustments
# Verify predictions vs actuals
```

### Rollback Procedures

```bash
# Disable any layer via feature flag
CONTROL_ENABLE_KALMAN_WORKLOAD=false
CONTROL_ENABLE_PID_UTILIZATION=false
CONTROL_ENABLE_MPC=false

# Or revert database migration
alembic downgrade -1

# Or revert code changes
git revert <commit-hash>
```

### Production Checklist

- [ ] All unit tests pass
- [ ] All integration tests pass
- [ ] Performance benchmarks met
- [ ] Grafana dashboards configured
- [ ] Prometheus alerts configured
- [ ] Database migrations tested in staging
- [ ] Celery tasks scheduled and verified
- [ ] Documentation updated
- [ ] Runbook created for operations team
- [ ] Rollback procedures tested

---

## References

### Bridge Specifications

- `/home/user/Autonomous-Assignment-Program-Manager/docs/architecture/bridges/PID_HOMEOSTASIS_BRIDGE.md`
- `/home/user/Autonomous-Assignment-Program-Manager/docs/architecture/bridges/KALMAN_WORKLOAD_BRIDGE.md`
- `/home/user/Autonomous-Assignment-Program-Manager/docs/architecture/bridges/MPC_SCHEDULER_BRIDGE.md`

### Tuning Guide

- `/home/user/Autonomous-Assignment-Program-Manager/docs/architecture/CONTROL_THEORY_TUNING_GUIDE.md`

### Related Documentation

- **Resilience Framework:** `/home/user/Autonomous-Assignment-Program-Manager/docs/architecture/cross-disciplinary-resilience.md`
- **Homeostasis:** `/home/user/Autonomous-Assignment-Program-Manager/backend/app/resilience/homeostasis.py`
- **Scheduling Engine:** `/home/user/Autonomous-Assignment-Program-Manager/backend/app/scheduling/engine.py`
- **CP-SAT Solver:** `/home/user/Autonomous-Assignment-Program-Manager/backend/app/scheduling/solvers.py`

### External References

- **Kalman Filtering:** Welch & Bishop, "An Introduction to the Kalman Filter" (UNC-Chapel Hill)
- **PID Control:** Åström & Hägglund, "PID Controllers: Theory, Design, and Tuning" (2nd Ed)
- **Model Predictive Control:** Camacho & Bordons, "Model Predictive Control" (2nd Ed)
- **Google OR-Tools:** https://developers.google.com/optimization

---

## Appendix A: Success Criteria

### Kalman Filter Success

- ✅ Uncertainty converges within 7 days
- ✅ Innovation magnitude < 0.10 (95% of time)
- ✅ Confidence intervals contain actual values 95% of time
- ✅ Update time < 50ms per filter

### PID Controller Success

- ✅ Settling time < 7 days for step disturbance
- ✅ Overshoot < 10% of setpoint
- ✅ Steady-state error < 2%
- ✅ No sustained oscillations
- ✅ Integral saturation < 5% of updates

### MPC Success

- ✅ Optimization completes in < 60 seconds
- ✅ Prediction error < 10% on 4-week horizon
- ✅ Weight adjustments correlate with system state
- ✅ Generates ACGME-compliant schedules
- ✅ Coverage rate ≥ 95%

---

**End of Specification**

This document provides a production-ready specification for implementing the Control Theory Integration Service with three layers: Kalman filtering, PID control, and Model Predictive Control.

**Next Steps:**

1. Review specification with team
2. Begin Phase 1 (Kalman filters)
3. Monitor metrics and tune parameters
4. Proceed to Phase 2 and Phase 3 sequentially

**Questions or Issues:**

- Create GitHub issue with label `control-theory`
- Reference this spec document
- Tag relevant bridge spec for layer-specific questions
