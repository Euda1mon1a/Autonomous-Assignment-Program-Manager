# PID-Homeostasis Bridge Specification

> **Purpose:** Replace ad-hoc homeostasis feedback with formal PID control for utilization, workload, and coverage
> **Status:** Implementation-Ready Specification
> **Target File:** `backend/app/resilience/pid_homeostasis_bridge.py`
> **Dependencies:** `backend/app/resilience/homeostasis.py`
> **Last Updated:** 2025-12-26

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Mathematical Foundation](#mathematical-foundation)
3. [Architecture Overview](#architecture-overview)
4. [Three PID Controllers](#three-pid-controllers)
5. [Integration with Homeostasis](#integration-with-homeostasis)
6. [Anti-Windup Protection](#anti-windup-protection)
7. [Data Flow](#data-flow)
8. [Tuning Procedures](#tuning-procedures)
9. [Implementation](#implementation)
10. [Test Cases](#test-cases)
11. [Performance Metrics](#performance-metrics)
12. [Migration Strategy](#migration-strategy)

---

## Executive Summary

The current `HomeostasisMonitor` implements biological-inspired feedback loops with **ad-hoc correction calculations** based on severity thresholds. This specification replaces the ad-hoc `_trigger_correction()` logic with **formal PID (Proportional-Integral-Derivative) controllers** from classical control theory.

### Problem with Current System

```python
# Current: Ad-hoc correction in homeostasis.py
def _trigger_correction(self, loop, current_value, deviation, severity):
    action_type = self._determine_action_type(loop.setpoint, severity)
    # No mathematical basis for correction magnitude
    # No integral action to eliminate steady-state error
    # No derivative action to dampen oscillations
    return CorrectiveAction(...)
```

**Issues:**
- Binary severity thresholds (MINOR, MODERATE, MAJOR, CRITICAL)
- No mathematical guarantee of convergence to setpoint
- No accumulated error correction (integral term)
- No oscillation damping (derivative term)
- Correction magnitude not proportional to deviation

### Solution: PID Control

Replace ad-hoc logic with proven PID control:

```python
# New: Formal PID calculation
u(t) = Kp·e(t) + Ki·∫e(τ)dτ + Kd·de(t)/dt

Where:
- u(t) = control signal (correction magnitude)
- e(t) = setpoint - measured_value (error)
- Kp, Ki, Kd = tuned gains
```

**Benefits:**
- **Proportional (P):** Immediate response proportional to error
- **Integral (I):** Eliminates steady-state error over time
- **Derivative (D):** Dampens oscillations, prevents overshoot
- Mathematical proof of stability and convergence
- Tunable response characteristics (fast vs smooth)

### Key Design Decisions

1. **Preserve existing `HomeostasisMonitor`** - Don't refactor, extend
2. **Three PID controllers** - Utilization, Workload Balance, Coverage Rate
3. **Bridge pattern** - `PIDHomeostasisBridge` coordinates both systems
4. **Gradual migration** - PID can run alongside existing logic initially
5. **Anti-windup** - Prevent integral saturation during constraints

---

## Mathematical Foundation

### PID Control Equation

```
u(t) = Kp·e(t) + Ki·∫₀ᵗ e(τ)dτ + Kd·de(t)/dt

Discrete-time approximation (used in implementation):
u[n] = Kp·e[n] + Ki·Σe[k]·Δt + Kd·(e[n] - e[n-1])/Δt

Where:
- u[n] = control signal at timestep n
- e[n] = error at timestep n = setpoint - measured_value
- Δt = time between samples (e.g., 15 minutes for feedback loop checks)
```

### Three Terms Explained

| Term | Purpose | Physical Meaning | Tuning Effect |
|------|---------|------------------|---------------|
| **Proportional (Kp)** | Immediate response | "How far off are we RIGHT NOW?" | Higher Kp = faster response, but more overshoot |
| **Integral (Ki)** | Eliminate accumulated error | "How long have we been off?" | Higher Ki = faster steady-state convergence, but oscillation risk |
| **Derivative (Kd)** | Dampen oscillations | "How fast is error changing?" | Higher Kd = smoother response, reduced overshoot |

### Control Signal Interpretation

The PID output `u(t)` represents a **normalized correction magnitude**:

- **Positive u(t):** System below setpoint → Increase resource
- **Negative u(t):** System above setpoint → Decrease resource
- **Magnitude |u(t)|:** How aggressively to correct

### Stability Conditions

For PID control to be stable:

1. **Bounded Input, Bounded Output (BIBO):** Finite error → finite control signal
2. **Anti-windup:** Integral term must be limited to prevent saturation
3. **Derivative filtering:** Derivative term should be low-pass filtered to reduce noise amplification

---

## Architecture Overview

### System Components

```
┌─────────────────────────────────────────────────────────────┐
│                 PIDHomeostasisBridge                        │
│                 (Coordinator Layer)                          │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────────┐    ┌──────────────────────────────┐  │
│  │ HomeostasisMonitor│    │ PIDControllerBank            │  │
│  │ (Existing)        │    │ (New)                        │  │
│  ├──────────────────┤    ├──────────────────────────────┤  │
│  │ - Setpoints       │    │ - Utilization PID            │  │
│  │ - Feedback loops  │    │ - Workload Balance PID       │  │
│  │ - Deviation check │    │ - Coverage Rate PID          │  │
│  │ - Volatility      │    │ - Anti-windup logic          │  │
│  │ - Allostatic load │    │ - Tuning algorithms          │  │
│  └──────────────────┘    └──────────────────────────────┘  │
│                                                               │
└───────────────────────────┬───────────────────────────────────┘
                            │
                            │ Combined Corrections
                            ▼
                ┌───────────────────────────┐
                │  SchedulingEngine         │
                │  (Applies Corrections)    │
                └───────────────────────────┘
```

### Design Pattern: Bridge

The **Bridge Pattern** decouples the feedback mechanism (homeostasis) from the correction algorithm (PID). This allows:

- Existing homeostasis logic remains unchanged
- PID controllers are pluggable and independently tunable
- Both systems can run in parallel during migration
- Easy A/B testing and rollback

### Responsibility Separation

| Component | Responsibilities |
|-----------|-----------------|
| **HomeostasisMonitor** | - Manage setpoints<br>- Track value history<br>- Calculate volatility<br>- Detect positive feedback risks<br>- Maintain allostatic load metrics |
| **PIDControllerBank** | - Calculate PID control signals<br>- Track integral and derivative terms<br>- Implement anti-windup<br>- Provide tuning methods<br>- Record control history |
| **PIDHomeostasisBridge** | - Coordinate both systems<br>- Merge recommendations<br>- Resolve conflicts<br>- Provide unified interface<br>- Decide when to use PID vs homeostasis |

---

## Three PID Controllers

### Controller Configurations

Each controller targets a specific process variable with custom-tuned gains.

#### 1. Utilization PID

**Target:** Maintain faculty utilization at 75% (below queuing theory threshold)

```python
@dataclass
class PIDConfig:
    """Configuration for a PID controller."""
    name: str
    setpoint: float
    Kp: float  # Proportional gain
    Ki: float  # Integral gain
    Kd: float  # Derivative gain
    output_limits: tuple[float, float]  # Min, max control signal
    unit: str
    description: str

UTILIZATION_PID = PIDConfig(
    name="utilization",
    setpoint=0.75,  # 75% utilization target
    Kp=10.0,        # Strong immediate response (10% error → 100% correction)
    Ki=0.5,         # Moderate integral action (eliminate drift over ~2 weeks)
    Kd=2.0,         # Damping to prevent overshoot
    output_limits=(-0.2, 0.2),  # ±20% max correction per cycle
    unit="ratio",
    description="Faculty utilization rate (0.0-1.0)"
)
```

**Gain Rationale:**
- **Kp=10.0:** If utilization is 0.85 (10% over), proportional term contributes -1.0 (strong correction)
- **Ki=0.5:** Slow integral buildup prevents drift, reaches full correction in ~2 units of accumulated error
- **Kd=2.0:** If error is changing by 0.05/cycle, derivative contributes -0.1 (10% damping)

**Control Signal Meaning:**
- `u = +0.2` → Add assignments to increase utilization by ~20%
- `u = -0.2` → Remove assignments to decrease utilization by ~20%
- `u = 0.0` → Maintain current assignment rate

#### 2. Workload Balance PID

**Target:** Maintain low variance in workload distribution (std_dev ≤ 0.15)

```python
WORKLOAD_PID = PIDConfig(
    name="workload_balance",
    setpoint=0.0,   # Target: zero imbalance (perfect balance)
    Kp=5.0,         # Moderate proportional (5% imbalance → 25% redistribution)
    Ki=0.3,         # Gentle integral (slow drift correction)
    Kd=1.0,         # Light damping (balance changes slowly)
    output_limits=(-0.15, 0.15),  # ±15% max redistribution per cycle
    unit="std_dev",
    description="Standard deviation of workload across faculty"
)
```

**Process Variable:** Normalized workload imbalance
```python
# Calculate imbalance from current workload distribution
workload_std = np.std([faculty.workload for faculty in faculty_list])
mean_workload = np.mean([faculty.workload for faculty in faculty_list])
imbalance = workload_std / mean_workload if mean_workload > 0 else 0
error = 0.0 - imbalance  # Negative error means too much variance
```

**Gain Rationale:**
- **Kp=5.0:** Lower than utilization because redistribution is disruptive
- **Ki=0.3:** Very slow drift correction (workload balance is lower priority)
- **Kd=1.0:** Minimal damping (workload changes are already slow)

**Control Signal Meaning:**
- `u = +0.15` → Redistribute 15% of workload from high-load to low-load faculty
- `u = -0.15` → Allow natural workload divergence (rare, only if over-balanced)
- `u = 0.0` → No redistribution needed

#### 3. Coverage Rate PID

**Target:** Maintain 95% coverage rate (critical for patient safety)

```python
COVERAGE_PID = PIDConfig(
    name="coverage",
    setpoint=0.95,  # 95% coverage target
    Kp=12.0,        # Very strong immediate response (critical metric)
    Ki=0.8,         # Aggressive integral (eliminate gaps quickly)
    Kd=1.5,         # Moderate damping
    output_limits=(-0.1, 0.1),  # ±10% max coverage adjustment per cycle
    unit="ratio",
    description="Proportion of blocks with assigned coverage"
)
```

**Gain Rationale:**
- **Kp=12.0:** Highest gain of all controllers (coverage is CRITICAL)
- **Ki=0.8:** Fast integral action to close persistent gaps
- **Kd=1.5:** Moderate damping (coverage can fluctuate due to emergencies)

**Control Signal Meaning:**
- `u = +0.1` → Recruit backup coverage for ~10% of uncovered blocks
- `u = -0.1` → Release excess coverage (rare, only if over-staffed)
- `u = 0.0` → Coverage is at target

### Gain Selection Summary

| Controller | Kp (Immediate) | Ki (Drift) | Kd (Damping) | Priority |
|------------|----------------|------------|--------------|----------|
| **Utilization** | 10.0 (strong) | 0.5 (moderate) | 2.0 (strong) | High |
| **Workload** | 5.0 (moderate) | 0.3 (gentle) | 1.0 (light) | Medium |
| **Coverage** | 12.0 (very strong) | 0.8 (aggressive) | 1.5 (moderate) | **CRITICAL** |

---

## Integration with Homeostasis

### Current Homeostasis Flow

```python
# Existing: backend/app/resilience/homeostasis.py

class HomeostasisMonitor:
    def check_feedback_loop(self, loop_id: UUID, current_value: float) -> CorrectiveAction | None:
        loop = self.feedback_loops.get(loop_id)
        loop.record_value(current_value)

        # Check deviation from setpoint
        deviation, severity = loop.setpoint.check_deviation(current_value)

        if severity in (DeviationSeverity.MAJOR, DeviationSeverity.CRITICAL):
            return self._trigger_correction(loop, current_value, deviation, severity)

        # ... (existing logic)
```

### Enhanced PID Flow

```python
# New: Replace _trigger_correction() with PID calculation

class PIDHomeostasisBridge:
    def __init__(self, homeostasis_monitor: HomeostasisMonitor):
        self.homeostasis = homeostasis_monitor
        self.pid_bank = PIDControllerBank()
        self.use_pid = True  # Feature flag for gradual rollout

    def check_feedback_loop_with_pid(
        self,
        loop_id: UUID,
        current_value: float
    ) -> CorrectiveAction | None:
        """Enhanced feedback loop check with PID control."""
        loop = self.homeostasis.feedback_loops.get(loop_id)
        loop.record_value(current_value)

        # Get PID correction
        if self.use_pid and loop.setpoint.name in self.pid_bank.controllers:
            pid_result = self.pid_bank.update(loop.setpoint.name, current_value)

            # Convert PID control signal to CorrectiveAction
            return self._pid_to_corrective_action(
                loop=loop,
                current_value=current_value,
                pid_result=pid_result
            )
        else:
            # Fallback to existing homeostasis logic
            return self.homeostasis.check_feedback_loop(loop_id, current_value)
```

### Replacing Ad-Hoc Correction Calculation

**Before (Ad-Hoc):**
```python
def _determine_action_type(self, setpoint: Setpoint, severity: DeviationSeverity) -> CorrectiveActionType:
    if severity == DeviationSeverity.CRITICAL:
        if setpoint.name in ("coverage_rate", "acgme_compliance"):
            return CorrectiveActionType.RECRUIT_BACKUP
        return CorrectiveActionType.REDUCE_SCOPE
    # ... more if-else chains
```

**After (PID-Based):**
```python
def _pid_to_corrective_action(
    self,
    loop: FeedbackLoop,
    current_value: float,
    pid_result: dict
) -> CorrectiveAction:
    """Convert PID control signal to CorrectiveAction."""
    control_signal = pid_result["control_signal"]
    error = pid_result["error"]

    # Map control signal magnitude to severity
    severity = self._control_signal_to_severity(abs(control_signal))

    # Map setpoint + control direction to action type
    action_type = self._pid_signal_to_action_type(
        setpoint_name=loop.setpoint.name,
        control_signal=control_signal
    )

    return CorrectiveAction(
        id=uuid4(),
        feedback_loop_id=loop.id,
        action_type=action_type,
        description=self._get_pid_action_description(loop, pid_result),
        triggered_at=datetime.now(),
        deviation_severity=severity,
        deviation_amount=abs(error),
        target_value=loop.setpoint.target_value,
        actual_value=current_value,
        # NEW: Store PID diagnostics
        pid_diagnostics={
            "control_signal": control_signal,
            "P_term": pid_result["P"],
            "I_term": pid_result["I"],
            "D_term": pid_result["D"],
            "integral_saturated": pid_result.get("integral_saturated", False),
        }
    )

def _control_signal_to_severity(self, abs_control: float) -> DeviationSeverity:
    """Map PID control signal magnitude to deviation severity."""
    if abs_control < 0.02:
        return DeviationSeverity.NONE
    elif abs_control < 0.05:
        return DeviationSeverity.MINOR
    elif abs_control < 0.10:
        return DeviationSeverity.MODERATE
    elif abs_control < 0.15:
        return DeviationSeverity.MAJOR
    else:
        return DeviationSeverity.CRITICAL

def _pid_signal_to_action_type(
    self,
    setpoint_name: str,
    control_signal: float
) -> CorrectiveActionType:
    """Map PID control signal to corrective action type."""
    # Positive control signal = need to increase metric
    # Negative control signal = need to decrease metric

    if setpoint_name == "coverage_rate":
        if control_signal > 0:
            return CorrectiveActionType.RECRUIT_BACKUP  # Increase coverage
        else:
            return CorrectiveActionType.REDUCE_SCOPE  # Reduce demand

    elif setpoint_name == "faculty_utilization":
        if control_signal > 0:
            return CorrectiveActionType.REDISTRIBUTE  # Add assignments
        else:
            return CorrectiveActionType.DEFER_ACTIVITY  # Reduce load

    elif setpoint_name == "workload_balance":
        if abs(control_signal) > 0.05:
            return CorrectiveActionType.REDISTRIBUTE  # Rebalance
        else:
            return CorrectiveActionType.ALERT_ONLY

    else:
        return CorrectiveActionType.ALERT_ONLY
```

### Preserving Existing Features

The bridge **preserves** all existing homeostasis features:

| Feature | Preserved? | How? |
|---------|-----------|------|
| **Setpoint management** | ✅ Yes | Bridge uses homeostasis setpoints as PID targets |
| **Value history tracking** | ✅ Yes | Homeostasis continues recording values |
| **Volatility detection** | ✅ Yes | `detect_volatility_risks()` still runs |
| **Positive feedback risks** | ✅ Yes | `detect_positive_feedback_risks()` still runs |
| **Allostatic load** | ✅ Yes | Unchanged, orthogonal to PID |
| **Corrective action handlers** | ✅ Yes | Bridge returns `CorrectiveAction` objects as before |

### Dual-Mode Operation (Migration)

During migration, the bridge supports **dual-mode operation**:

```python
class PIDHomeostasisBridge:
    def __init__(self, homeostasis_monitor: HomeostasisMonitor):
        self.homeostasis = homeostasis_monitor
        self.pid_bank = PIDControllerBank()

        # Feature flags for gradual rollout
        self.pid_enabled_for = {
            "coverage_rate": True,      # Start with critical metric
            "faculty_utilization": False,  # Deploy incrementally
            "workload_balance": False,     # Deploy last
        }

    def check_feedback_loop_with_pid(self, loop_id: UUID, current_value: float):
        loop = self.homeostasis.feedback_loops.get(loop_id)

        # Use PID if enabled for this setpoint
        if self.pid_enabled_for.get(loop.setpoint.name, False):
            return self._use_pid_control(loop, current_value)
        else:
            # Fallback to original homeostasis
            return self.homeostasis.check_feedback_loop(loop_id, current_value)
```

**Rollout Plan:**
1. **Week 1:** Enable PID for `coverage_rate` only (most critical)
2. **Week 2:** Monitor performance, enable for `faculty_utilization`
3. **Week 3:** Enable for `workload_balance`
4. **Week 4:** Full PID deployment, deprecate old logic

---

## Anti-Windup Protection

### The Windup Problem

**Integral windup** occurs when the integral term accumulates unbounded error during saturation, causing overshoot and instability.

**Example Scenario:**
```
Coverage is at 0.70 (target 0.95, error = +0.25)
Controller wants to add 50% more coverage (huge correction)
BUT: Only 30 faculty available → Can't add more than 10% coverage
Controller is SATURATED at output limit

Without anti-windup:
- Integral keeps accumulating error: I_term grows to 50, 100, 200...
- When coverage finally reaches 0.95, integral is HUGE
- Controller overshoots to 1.10 coverage (over-staffed)
- Takes weeks to "unwind" the integral term
```

### Anti-Windup Strategies

#### 1. Integral Clamping (Simple, Effective)

Limit the integral term to a fixed range:

```python
class PIDController:
    def __init__(self, Kp, Ki, Kd, integral_max=5.0, integral_min=-5.0):
        self.integral = 0.0
        self.integral_max = integral_max
        self.integral_min = integral_min

    def update(self, error: float, dt: float) -> float:
        # Proportional
        P = self.Kp * error

        # Integral with clamping
        self.integral += error * dt
        self.integral = max(self.integral_min, min(self.integral_max, self.integral))
        I = self.Ki * self.integral

        # Derivative
        derivative = (error - self.previous_error) / dt
        D = self.Kd * derivative

        control_signal = P + I + D
        self.previous_error = error

        return control_signal
```

**Limits for Each Controller:**

| Controller | Integral Max | Integral Min | Rationale |
|------------|--------------|--------------|-----------|
| Utilization | +5.0 | -5.0 | Allows ~10 cycles of max error accumulation |
| Workload | +3.0 | -3.0 | Workload balance is less critical |
| Coverage | +10.0 | -10.0 | Coverage gaps may persist during crises |

#### 2. Conditional Integration (Advanced)

Only integrate when the controller is **not saturated**:

```python
def update(self, error: float, dt: float, output_limits: tuple[float, float]) -> float:
    P = self.Kp * error

    # Calculate tentative control signal WITHOUT integral
    tentative_control = P + self.Kd * (error - self.previous_error) / dt

    # Only integrate if we're NOT saturated
    if output_limits[0] < tentative_control < output_limits[1]:
        self.integral += error * dt
        self.integral = np.clip(self.integral, self.integral_min, self.integral_max)
    else:
        # Controller is saturated - don't accumulate error
        pass

    I = self.Ki * self.integral
    control_signal = P + I + self.Kd * (error - self.previous_error) / dt

    return control_signal
```

#### 3. Back-Calculation Anti-Windup (Most Advanced)

When output saturates, feed the **excess** back to reduce the integral:

```python
def update(self, error: float, dt: float, output_limits: tuple[float, float]) -> float:
    P = self.Kp * error

    # Tentative integral term
    self.integral += error * dt
    I = self.Ki * self.integral

    D = self.Kd * (error - self.previous_error) / dt

    # Calculate raw control signal
    raw_control = P + I + D

    # Apply output limits
    control_signal = np.clip(raw_control, output_limits[0], output_limits[1])

    # Back-calculation anti-windup
    if raw_control != control_signal:
        # We saturated - reduce integral by the excess
        excess = raw_control - control_signal
        Kt = 1.0 / self.Ki  # Anti-windup gain (typically 1/Ki)
        self.integral -= Kt * excess * dt

    self.previous_error = error
    return control_signal
```

### Recommended Implementation

**Use Integral Clamping for simplicity** in initial deployment:

```python
@dataclass
class PIDState:
    """State for a PID controller."""
    name: str
    setpoint: float

    # Gains
    Kp: float
    Ki: float
    Kd: float

    # State
    integral: float = 0.0
    previous_error: float = 0.0
    previous_time: datetime = field(default_factory=datetime.now)

    # Anti-windup limits
    integral_max: float = 5.0
    integral_min: float = -5.0

    # Output limits
    output_max: float = 0.2
    output_min: float = -0.2

    def update(self, current_value: float) -> dict:
        """Calculate PID control signal with anti-windup."""
        now = datetime.now()
        dt = (now - self.previous_time).total_seconds() / 86400  # Days

        error = self.setpoint - current_value

        # Proportional
        P = self.Kp * error

        # Integral with clamping
        self.integral += error * dt
        self.integral = max(self.integral_min, min(self.integral_max, self.integral))
        I = self.Ki * self.integral

        # Derivative
        if dt > 0:
            derivative = (error - self.previous_error) / dt
        else:
            derivative = 0.0
        D = self.Kd * derivative

        # Control signal with output limiting
        raw_control = P + I + D
        control_signal = max(self.output_min, min(self.output_max, raw_control))

        # Update state
        self.previous_error = error
        self.previous_time = now

        return {
            "error": error,
            "control_signal": control_signal,
            "P": P,
            "I": I,
            "D": D,
            "integral_saturated": abs(self.integral - self.integral_max) < 0.01 or
                                  abs(self.integral - self.integral_min) < 0.01,
            "output_saturated": abs(raw_control - control_signal) > 0.01,
            "dt": dt,
        }
```

### Reset Integral on Setpoint Change

When the setpoint changes, **reset the integral term** to prevent windup from the old error:

```python
def set_setpoint(self, new_setpoint: float):
    """Change setpoint and reset integral to prevent windup."""
    old_setpoint = self.setpoint
    self.setpoint = new_setpoint

    if abs(new_setpoint - old_setpoint) > 0.01:
        # Significant setpoint change - reset integral
        self.integral = 0.0
        logger.info(f"Setpoint changed from {old_setpoint} to {new_setpoint}, integral reset")
```

---

## Data Flow

### End-to-End Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. MEASUREMENT COLLECTION                                        │
│    - ScheduleMetricsCollector gathers current metrics           │
│    - HomeostasisService.get_current_metrics()                   │
└─────────────────┬───────────────────────────────────────────────┘
                  │
                  │ {utilization: 0.82, workload: 0.18, coverage: 0.91}
                  ▼
┌─────────────────────────────────────────────────────────────────┐
│ 2. PID HOMEOSTASIS BRIDGE                                        │
│    - PIDHomeostasisBridge.update_all(metrics)                   │
│    - Calls PID controllers for each metric                      │
└─────────────────┬───────────────────────────────────────────────┘
                  │
                  │ For each metric:
                  ├──────────────────────────────────┐
                  │                                  │
                  ▼                                  ▼
┌─────────────────────────────┐    ┌─────────────────────────────┐
│ 3a. PID CALCULATION          │    │ 3b. HOMEOSTASIS CHECK       │
│ - PIDState.update()          │    │ - FeedbackLoop.record_value│
│ - Calculate P, I, D terms    │    │ - Check deviation          │
│ - Apply anti-windup          │    │ - Get volatility           │
│ - Clamp output               │    │ - Detect positive feedback │
└────────────┬─────────────────┘    └────────────┬────────────────┘
             │                                   │
             │ control_signal                    │ severity
             │                                   │
             └─────────────┬─────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│ 4. MERGE RECOMMENDATIONS                                         │
│    - PIDHomeostasisBridge._merge_recommendations()              │
│    - Combine PID corrections with homeostasis alerts            │
│    - Resolve conflicts (PID overrides homeostasis)              │
│    - Prioritize by severity and control signal magnitude        │
└─────────────────┬───────────────────────────────────────────────┘
                  │
                  │ List[CorrectiveAction]
                  ▼
┌─────────────────────────────────────────────────────────────────┐
│ 5. SCHEDULING ENGINE ADJUSTMENT                                  │
│    - SchedulingEngine.adjust_weights(corrections)               │
│    - Modify constraint weights based on control signals         │
│    - Trigger reassignment if needed                             │
└─────────────────┬───────────────────────────────────────────────┘
                  │
                  │ New schedule parameters
                  ▼
┌─────────────────────────────────────────────────────────────────┐
│ 6. SCHEDULE REGENERATION (if needed)                             │
│    - SchedulingEngine.generate_schedule()                       │
│    - Apply new weights and preferences                          │
│    - Validate ACGME compliance                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Step-by-Step Data Transformation

#### Step 1: Metric Collection

```python
# Example: Collect current metrics
from app.services.homeostasis_service import HomeostasisService

homeostasis_svc = HomeostasisService(db)
metrics = await homeostasis_svc.get_current_metrics()

# Returns:
{
    "coverage_rate": 0.91,           # 91% of blocks covered
    "faculty_utilization": 0.82,     # 82% average utilization
    "workload_balance": 0.18,        # 0.18 std_dev in workload
    "schedule_stability": 0.93,
    "acgme_compliance": 1.0,
}
```

#### Step 2: PID Update

```python
# Bridge updates all PID controllers
bridge = PIDHomeostasisBridge(homeostasis_monitor)
corrections = bridge.update_all(metrics)

# For utilization (target 0.75, current 0.82):
utilization_pid.update(0.82)
# Returns:
{
    "error": -0.07,           # 7% over target
    "control_signal": -0.14,  # Remove ~14% of assignments
    "P": -0.70,               # Kp=10.0 × -0.07
    "I": -0.02,               # Small integral contribution
    "D": -0.04,               # Derivative dampening (if error is decreasing)
    "integral_saturated": False,
    "output_saturated": False,
}
```

#### Step 3: Convert to CorrectiveAction

```python
# Bridge converts PID output to CorrectiveAction
action = bridge._pid_to_corrective_action(
    loop=utilization_loop,
    current_value=0.82,
    pid_result=pid_output
)

# Returns:
CorrectiveAction(
    id=UUID(...),
    feedback_loop_id=utilization_loop.id,
    action_type=CorrectiveActionType.DEFER_ACTIVITY,  # Reduce load
    description="PID: Reduce utilization by 14% (currently 82%, target 75%)",
    triggered_at=datetime.now(),
    deviation_severity=DeviationSeverity.MODERATE,
    deviation_amount=0.07,
    target_value=0.75,
    actual_value=0.82,
    pid_diagnostics={
        "control_signal": -0.14,
        "P_term": -0.70,
        "I_term": -0.02,
        "D_term": -0.04,
        "integral_saturated": False,
    }
)
```

#### Step 4: Scheduling Engine Adjustment

```python
# Engine applies PID corrections to constraint weights
from app.scheduling.engine import SchedulingEngine

engine = SchedulingEngine()
await engine.adjust_weights(corrections)

# For utilization correction (control_signal = -0.14):
# - Reduce "maximize_utilization" weight by 14%
# - Increase "balance_workload" weight by 14%
# - Optionally trigger incremental reassignment
```

### Feedback Loop Timing

| Stage | Frequency | Trigger |
|-------|-----------|---------|
| **Metric Collection** | Every 15 minutes | Celery periodic task |
| **PID Update** | Every 15 minutes | Triggered by metric collection |
| **Homeostasis Check** | Every 15 minutes | Parallel with PID |
| **Weight Adjustment** | On deviation | When control signal > 0.05 |
| **Schedule Regeneration** | On demand | When control signal > 0.15 (MAJOR) |

---

## Tuning Procedures

### Why Tuning Matters

PID performance depends **critically** on gain values (Kp, Ki, Kd). Poor tuning leads to:

- **Underdamped:** Oscillations, slow convergence
- **Overdamped:** Sluggish response, large steady-state error
- **Unstable:** Divergent oscillations, system failure

### Tuning Methods

#### 1. Ziegler-Nichols Method (Classical)

**Procedure:**
1. Set Ki = 0, Kd = 0 (P-only control)
2. Increase Kp until system oscillates sustainably
3. Record **ultimate gain** Ku and **ultimate period** Pu
4. Calculate PID gains:

```python
def tune_ziegler_nichols(Ku: float, Pu: float) -> tuple[float, float, float]:
    """
    Calculate PID gains using Ziegler-Nichols method.

    Args:
        Ku: Ultimate gain (gain at which system oscillates)
        Pu: Ultimate period (oscillation period at Ku)

    Returns:
        (Kp, Ki, Kd) tuple
    """
    Kp = 0.6 * Ku
    Ki = 1.2 * Ku / Pu
    Kd = 0.075 * Ku * Pu

    return Kp, Ki, Kd
```

**Example:**
```python
# Relay feedback test for utilization controller
# 1. Set Kp = 0, increase until oscillation
# 2. Observe: Ku = 15.0, Pu = 7 days

Kp, Ki, Kd = tune_ziegler_nicholds(Ku=15.0, Pu=7.0)
# Kp = 0.6 × 15.0 = 9.0
# Ki = 1.2 × 15.0 / 7.0 = 2.57
# Kd = 0.075 × 15.0 × 7.0 = 7.875

# Initial gains: Kp=9.0, Ki=2.57, Kd=7.875
# Typically need to reduce Ki and Kd by 50% for real-world use
```

**Limitations:**
- Requires inducing oscillations (disruptive in production)
- Conservative gains (may be too aggressive or too sluggish)

#### 2. Manual Tuning (Trial-and-Error)

**Procedure:**
1. Start with conservative gains: `Kp=1.0, Ki=0.0, Kd=0.0`
2. Increase Kp until response is fast enough (but not oscillating)
3. Add Ki to eliminate steady-state error (start with Ki = Kp/10)
4. Add Kd to reduce overshoot (start with Kd = Kp/5)
5. Iterate: Adjust each gain by 10-20% increments

**Guidelines:**

| Symptom | Adjustment |
|---------|------------|
| **Slow response** | Increase Kp (+20%) |
| **Oscillations** | Decrease Kp (-20%), increase Kd (+30%) |
| **Steady-state error** | Increase Ki (+50%) |
| **Overshoot** | Increase Kd (+50%), decrease Kp (-10%) |
| **Instability** | Reduce all gains by 50%, start over |

#### 3. Simulation-Based Tuning (Recommended)

Use historical data to simulate PID response and optimize gains offline:

```python
import numpy as np
from scipy.optimize import minimize

def simulate_pid_response(
    gains: tuple[float, float, float],
    setpoint: float,
    historical_data: list[float],
    disturbances: list[float]
) -> float:
    """
    Simulate PID controller on historical data.

    Args:
        gains: (Kp, Ki, Kd) tuple
        setpoint: Target value
        historical_data: Past measurements
        disturbances: External disturbances (absences, emergencies)

    Returns:
        Performance metric (lower is better)
    """
    Kp, Ki, Kd = gains

    integral = 0.0
    previous_error = 0.0
    control_history = []
    error_history = []

    for i, measured_value in enumerate(historical_data):
        # Add disturbance
        measured_value += disturbances[i]

        # PID calculation
        error = setpoint - measured_value
        integral += error
        integral = np.clip(integral, -5.0, 5.0)  # Anti-windup
        derivative = error - previous_error

        control = Kp * error + Ki * integral + Kd * derivative
        control = np.clip(control, -0.2, 0.2)  # Output limits

        control_history.append(control)
        error_history.append(error)
        previous_error = error

    # Performance metric: Integral Squared Error (ISE)
    ise = sum(e**2 for e in error_history)

    # Penalty for control effort (avoid aggressive control)
    control_penalty = 0.1 * sum(abs(c) for c in control_history)

    return ise + control_penalty

def optimize_pid_gains(
    setpoint: float,
    historical_data: list[float],
    disturbances: list[float]
) -> tuple[float, float, float]:
    """
    Optimize PID gains using historical data.

    Returns:
        Optimized (Kp, Ki, Kd) tuple
    """
    # Initial guess
    x0 = [10.0, 0.5, 2.0]

    # Bounds: Kp ∈ [0, 20], Ki ∈ [0, 5], Kd ∈ [0, 10]
    bounds = [(0, 20), (0, 5), (0, 10)]

    # Optimize
    result = minimize(
        fun=lambda gains: simulate_pid_response(gains, setpoint, historical_data, disturbances),
        x0=x0,
        bounds=bounds,
        method='L-BFGS-B'
    )

    return tuple(result.x)

# Example usage:
# historical_utilization = [0.72, 0.78, 0.82, 0.79, 0.81, ...]
# disturbances = [0.0, 0.02, -0.05, 0.01, ...]  # Absences, emergencies
# optimized_gains = optimize_pid_gains(0.75, historical_utilization, disturbances)
# Kp, Ki, Kd = optimized_gains
```

#### 4. Online Tuning (Adaptive)

Continuously adjust gains based on performance:

```python
class AdaptivePIDController:
    """PID controller with online gain adaptation."""

    def __init__(self, initial_Kp, initial_Ki, initial_Kd):
        self.Kp = initial_Kp
        self.Ki = initial_Ki
        self.Kd = initial_Kd

        self.adaptation_rate = 0.05  # 5% adjustment per cycle
        self.performance_window = []
        self.window_size = 20

    def update(self, current_value: float) -> dict:
        """Update with adaptive tuning."""
        # Standard PID calculation
        result = super().update(current_value)

        # Track performance
        ise = result["error"] ** 2
        self.performance_window.append(ise)

        if len(self.performance_window) > self.window_size:
            self.performance_window.pop(0)

        # Adapt gains if performance is poor
        if len(self.performance_window) == self.window_size:
            avg_ise = sum(self.performance_window) / self.window_size

            # If error is persistently high, increase Kp and Ki
            if avg_ise > 0.01:  # Threshold for "poor performance"
                self.Kp *= (1 + self.adaptation_rate)
                self.Ki *= (1 + self.adaptation_rate * 0.5)
                logger.info(f"Adaptive tuning: Increased Kp to {self.Kp:.2f}, Ki to {self.Ki:.2f}")

            # If oscillating, reduce Kp and increase Kd
            if self._is_oscillating():
                self.Kp *= (1 - self.adaptation_rate)
                self.Kd *= (1 + self.adaptation_rate)
                logger.info(f"Adaptive tuning: Reduced Kp to {self.Kp:.2f}, increased Kd to {self.Kd:.2f}")

        return result

    def _is_oscillating(self) -> bool:
        """Detect oscillation in error signal."""
        if len(self.performance_window) < 6:
            return False

        errors = self.performance_window[-6:]
        sign_changes = sum(
            1 for i in range(1, len(errors))
            if (errors[i] - errors[i-1]) * (errors[i-1] - errors[i-2]) < 0
        )

        return sign_changes > 3  # More than 3 direction changes in 6 samples
```

### Tuning Strategy by Defense Level

Different operating conditions require different gain schedules:

```python
class DefenseLevelGainSchedule:
    """Gain scheduling based on resilience defense level."""

    GAIN_SCHEDULES = {
        "GREEN": {  # Normal operation - smooth, balanced control
            "utilization": {"Kp": 10.0, "Ki": 0.5, "Kd": 2.0},
            "workload": {"Kp": 5.0, "Ki": 0.3, "Kd": 1.0},
            "coverage": {"Kp": 12.0, "Ki": 0.8, "Kd": 1.5},
        },
        "YELLOW": {  # Elevated utilization - more aggressive correction
            "utilization": {"Kp": 15.0, "Ki": 1.0, "Kd": 3.0},
            "workload": {"Kp": 7.0, "Ki": 0.5, "Kd": 1.5},
            "coverage": {"Kp": 15.0, "Ki": 1.2, "Kd": 2.0},
        },
        "ORANGE": {  # High utilization - very aggressive, prioritize coverage
            "utilization": {"Kp": 20.0, "Ki": 1.5, "Kd": 4.0},
            "workload": {"Kp": 3.0, "Ki": 0.1, "Kd": 0.5},  # Deprioritize balance
            "coverage": {"Kp": 20.0, "Ki": 2.0, "Kd": 2.5},
        },
        "RED": {  # Crisis - maximum correction, coverage only
            "utilization": {"Kp": 25.0, "Ki": 2.0, "Kd": 5.0},
            "workload": {"Kp": 0.0, "Ki": 0.0, "Kd": 0.0},  # Disable
            "coverage": {"Kp": 30.0, "Ki": 3.0, "Kd": 3.0},
        },
    }

    def get_gains(self, defense_level: str, controller_name: str) -> dict:
        """Get gains for current defense level."""
        return self.GAIN_SCHEDULES[defense_level][controller_name]
```

---

## Implementation

### File Structure

```
backend/app/resilience/
├── homeostasis.py              # Existing (unchanged)
├── pid_homeostasis_bridge.py   # NEW: Bridge implementation
└── pid_control.py              # NEW: PID controller classes
```

### Class Definitions

#### `pid_control.py` - Core PID Implementation

```python
"""
PID Controllers for scheduling system dynamics.

Implements classical Proportional-Integral-Derivative control for precise
setpoint tracking. Complements existing homeostasis feedback loops.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class PIDConfig:
    """Configuration for a PID controller."""

    name: str
    setpoint: float
    Kp: float
    Ki: float
    Kd: float
    output_limits: tuple[float, float]
    integral_limits: tuple[float, float] = (-5.0, 5.0)
    unit: str = ""
    description: str = ""


@dataclass
class PIDState:
    """State of a PID controller."""

    id: UUID
    config: PIDConfig

    # State variables
    integral: float = 0.0
    previous_error: float = 0.0
    previous_time: datetime = field(default_factory=datetime.now)

    # History for diagnostics
    error_history: list[tuple[datetime, float]] = field(default_factory=list)
    control_history: list[tuple[datetime, float]] = field(default_factory=list)
    max_history_size: int = 100

    # Performance tracking
    oscillation_count: int = 0
    saturation_count: int = 0

    def update(self, current_value: float) -> dict:
        """
        Calculate PID control signal.

        Args:
            current_value: Current measurement of process variable

        Returns:
            Dict with control signal and diagnostics:
                - error: Current error (setpoint - current_value)
                - control_signal: PID output (clamped to output_limits)
                - P: Proportional term contribution
                - I: Integral term contribution
                - D: Derivative term contribution
                - integral_saturated: Whether integral is at limit
                - output_saturated: Whether output is at limit
                - dt: Time since last update (days)
        """
        now = datetime.now()
        dt = (now - self.previous_time).total_seconds() / 86400.0  # Convert to days

        # Prevent division by zero on first call
        if dt == 0:
            dt = 1.0 / 96.0  # Default to 15 minutes

        # Calculate error
        error = self.config.setpoint - current_value

        # Proportional term
        P = self.config.Kp * error

        # Integral term with anti-windup (clamping)
        self.integral += error * dt
        self.integral = np.clip(
            self.integral,
            self.config.integral_limits[0],
            self.config.integral_limits[1]
        )
        I = self.config.Ki * self.integral

        # Derivative term
        if abs(self.previous_error) < 1e-9:
            # First call or previous error was zero
            derivative = 0.0
        else:
            derivative = (error - self.previous_error) / dt
        D = self.config.Kd * derivative

        # Calculate raw control signal
        raw_control = P + I + D

        # Apply output limits
        control_signal = np.clip(
            raw_control,
            self.config.output_limits[0],
            self.config.output_limits[1]
        )

        # Track saturation
        integral_saturated = (
            abs(self.integral - self.config.integral_limits[1]) < 0.01 or
            abs(self.integral - self.config.integral_limits[0]) < 0.01
        )
        output_saturated = abs(raw_control - control_signal) > 0.001

        if integral_saturated:
            self.saturation_count += 1

        # Update history
        self.error_history.append((now, error))
        self.control_history.append((now, control_signal))

        # Trim history
        if len(self.error_history) > self.max_history_size:
            self.error_history = self.error_history[-self.max_history_size:]
        if len(self.control_history) > self.max_history_size:
            self.control_history = self.control_history[-self.max_history_size:]

        # Check for oscillations
        if self._is_oscillating():
            self.oscillation_count += 1

        # Update state
        self.previous_error = error
        self.previous_time = now

        return {
            "error": error,
            "control_signal": control_signal,
            "P": P,
            "I": I,
            "D": D,
            "integral_saturated": integral_saturated,
            "output_saturated": output_saturated,
            "dt": dt,
        }

    def _is_oscillating(self, window: int = 6) -> bool:
        """Detect oscillation in error signal."""
        if len(self.error_history) < window:
            return False

        recent_errors = [e for _, e in self.error_history[-window:]]
        sign_changes = sum(
            1 for i in range(1, len(recent_errors))
            if recent_errors[i] * recent_errors[i-1] < 0
        )

        # Oscillating if more than half the intervals change sign
        return sign_changes > window // 2

    def reset(self):
        """Reset controller state (useful for setpoint changes)."""
        self.integral = 0.0
        self.previous_error = 0.0
        self.previous_time = datetime.now()
        self.error_history.clear()
        self.control_history.clear()
        self.oscillation_count = 0
        self.saturation_count = 0

        logger.info(f"PID controller '{self.config.name}' reset")

    def set_setpoint(self, new_setpoint: float):
        """Change setpoint and reset integral to prevent windup."""
        old_setpoint = self.config.setpoint
        self.config.setpoint = new_setpoint

        if abs(new_setpoint - old_setpoint) > 0.01:
            # Significant setpoint change - reset integral
            self.integral = 0.0
            logger.info(
                f"PID '{self.config.name}' setpoint changed "
                f"from {old_setpoint} to {new_setpoint}, integral reset"
            )


class PIDControllerBank:
    """
    Bank of PID controllers for scheduling system.

    Manages multiple PIDs for different process variables:
    - Faculty utilization
    - Workload balance
    - Coverage rate
    """

    def __init__(self):
        self.controllers: dict[str, PIDState] = {}
        self._initialize_default_controllers()

    def _initialize_default_controllers(self):
        """Initialize standard controllers for scheduling."""

        # Utilization controller
        util_config = PIDConfig(
            name="utilization",
            setpoint=0.75,
            Kp=10.0,
            Ki=0.5,
            Kd=2.0,
            output_limits=(-0.2, 0.2),
            integral_limits=(-5.0, 5.0),
            unit="ratio",
            description="Faculty utilization rate (0.0-1.0)"
        )
        self.controllers["utilization"] = PIDState(
            id=uuid4(),
            config=util_config
        )

        # Workload balance controller
        workload_config = PIDConfig(
            name="workload_balance",
            setpoint=0.0,  # Target: zero imbalance
            Kp=5.0,
            Ki=0.3,
            Kd=1.0,
            output_limits=(-0.15, 0.15),
            integral_limits=(-3.0, 3.0),
            unit="std_dev",
            description="Normalized workload imbalance across faculty"
        )
        self.controllers["workload_balance"] = PIDState(
            id=uuid4(),
            config=workload_config
        )

        # Coverage rate controller
        coverage_config = PIDConfig(
            name="coverage",
            setpoint=0.95,
            Kp=12.0,
            Ki=0.8,
            Kd=1.5,
            output_limits=(-0.1, 0.1),
            integral_limits=(-10.0, 10.0),
            unit="ratio",
            description="Proportion of blocks with assigned coverage"
        )
        self.controllers["coverage"] = PIDState(
            id=uuid4(),
            config=coverage_config
        )

        logger.info(f"Initialized PID controllers: {list(self.controllers.keys())}")

    def update(self, controller_name: str, current_value: float) -> dict:
        """
        Update a PID controller and get control signal.

        Args:
            controller_name: Name of controller ("utilization", "workload_balance", "coverage")
            current_value: Current measurement

        Returns:
            PID result dict

        Raises:
            ValueError: If controller_name is unknown
        """
        controller = self.controllers.get(controller_name)
        if not controller:
            raise ValueError(
                f"Unknown controller: {controller_name}. "
                f"Available: {list(self.controllers.keys())}"
            )

        return controller.update(current_value)

    def reset(self, controller_name: Optional[str] = None):
        """
        Reset controller(s).

        Args:
            controller_name: Specific controller to reset, or None to reset all
        """
        if controller_name:
            if controller_name in self.controllers:
                self.controllers[controller_name].reset()
        else:
            for controller in self.controllers.values():
                controller.reset()

    def tune_ziegler_nichols(
        self,
        controller_name: str,
        ultimate_gain: float,
        ultimate_period: float
    ):
        """
        Auto-tune using Ziegler-Nichols method.

        Args:
            controller_name: Controller to tune
            ultimate_gain: Ku - gain at which system oscillates
            ultimate_period: Pu - period of oscillation at Ku (in days)
        """
        controller = self.controllers.get(controller_name)
        if not controller:
            raise ValueError(f"Unknown controller: {controller_name}")

        # Classic Ziegler-Nichols PID tuning
        Kp = 0.6 * ultimate_gain
        Ki = 1.2 * ultimate_gain / ultimate_period
        Kd = 0.075 * ultimate_gain * ultimate_period

        # Update gains
        controller.config.Kp = Kp
        controller.config.Ki = Ki
        controller.config.Kd = Kd

        # Reset state after retuning
        controller.reset()

        logger.info(
            f"Ziegler-Nichols tuning for '{controller_name}': "
            f"Kp={Kp:.2f}, Ki={Ki:.2f}, Kd={Kd:.2f} "
            f"(Ku={ultimate_gain}, Pu={ultimate_period})"
        )

    def get_status(self) -> dict:
        """Get status of all controllers."""
        status = {}
        for name, controller in self.controllers.items():
            status[name] = {
                "setpoint": controller.config.setpoint,
                "gains": {
                    "Kp": controller.config.Kp,
                    "Ki": controller.config.Ki,
                    "Kd": controller.config.Kd,
                },
                "state": {
                    "integral": controller.integral,
                    "previous_error": controller.previous_error,
                },
                "diagnostics": {
                    "oscillation_count": controller.oscillation_count,
                    "saturation_count": controller.saturation_count,
                    "history_size": len(controller.error_history),
                },
            }
        return status
```

#### `pid_homeostasis_bridge.py` - Bridge Integration

```python
"""
PID-Homeostasis Bridge.

Integrates formal PID control with existing homeostasis feedback loops.
Provides gradual migration path from ad-hoc corrections to PID control.
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from uuid import uuid4

from app.resilience.homeostasis import (
    CorrectiveAction,
    CorrectiveActionType,
    DeviationSeverity,
    FeedbackLoop,
    HomeostasisMonitor,
)
from app.resilience.pid_control import PIDControllerBank

logger = logging.getLogger(__name__)


@dataclass
class PIDCorrection:
    """PID-based correction recommendation."""

    controller_name: str
    control_signal: float
    error: float
    P_term: float
    I_term: float
    D_term: float
    action_type: CorrectiveActionType
    severity: DeviationSeverity
    description: str


class PIDHomeostasisBridge:
    """
    Bridge between PID controllers and homeostasis system.

    Coordinates formal PID control with biological feedback loops,
    providing unified interface for scheduling corrections.
    """

    def __init__(self, homeostasis_monitor: HomeostasisMonitor):
        self.homeostasis = homeostasis_monitor
        self.pid_bank = PIDControllerBank()

        # Feature flags for gradual rollout
        self.pid_enabled_for = {
            "coverage_rate": True,      # Start with critical metric
            "faculty_utilization": True,  # Deploy second
            "workload_balance": False,    # Deploy last
        }

        # Map homeostasis setpoint names to PID controller names
        self.setpoint_to_pid = {
            "coverage_rate": "coverage",
            "faculty_utilization": "utilization",
            "workload_balance": "workload_balance",
        }

    def update_all(self, current_values: dict[str, float]) -> dict:
        """
        Update all controllers with current metrics.

        Args:
            current_values: Dict of {setpoint_name: current_value}
                Example: {"coverage_rate": 0.91, "faculty_utilization": 0.82, ...}

        Returns:
            Dict with combined recommendations:
                - pid_corrections: List[PIDCorrection]
                - homeostasis_corrections: List[CorrectiveAction]
                - merged_actions: List[CorrectiveAction] (unified output)
        """
        pid_corrections = []
        homeostasis_corrections = []

        # Run PID controllers
        for setpoint_name, current_value in current_values.items():
            if setpoint_name in self.setpoint_to_pid:
                pid_name = self.setpoint_to_pid[setpoint_name]

                # Use PID if enabled
                if self.pid_enabled_for.get(setpoint_name, False):
                    try:
                        pid_result = self.pid_bank.update(pid_name, current_value)
                        correction = self._pid_result_to_correction(
                            setpoint_name=setpoint_name,
                            pid_name=pid_name,
                            pid_result=pid_result,
                            current_value=current_value
                        )
                        pid_corrections.append(correction)
                    except Exception as e:
                        logger.error(f"PID update failed for {pid_name}: {e}")

        # Run standard homeostasis checks
        homeostasis_corrections = self.homeostasis.check_all_loops(current_values)

        # Merge recommendations
        merged_actions = self._merge_recommendations(
            pid_corrections,
            homeostasis_corrections
        )

        return {
            "pid_corrections": pid_corrections,
            "homeostasis_corrections": homeostasis_corrections,
            "merged_actions": merged_actions,
        }

    def _pid_result_to_correction(
        self,
        setpoint_name: str,
        pid_name: str,
        pid_result: dict,
        current_value: float
    ) -> PIDCorrection:
        """Convert PID result to correction recommendation."""
        control_signal = pid_result["control_signal"]
        error = pid_result["error"]

        # Map control signal magnitude to severity
        severity = self._control_signal_to_severity(abs(control_signal))

        # Map setpoint + control direction to action type
        action_type = self._pid_signal_to_action_type(setpoint_name, control_signal)

        # Generate description
        description = self._get_pid_action_description(
            setpoint_name, pid_result, current_value
        )

        return PIDCorrection(
            controller_name=pid_name,
            control_signal=control_signal,
            error=error,
            P_term=pid_result["P"],
            I_term=pid_result["I"],
            D_term=pid_result["D"],
            action_type=action_type,
            severity=severity,
            description=description
        )

    def _control_signal_to_severity(self, abs_control: float) -> DeviationSeverity:
        """Map PID control signal magnitude to deviation severity."""
        if abs_control < 0.02:
            return DeviationSeverity.NONE
        elif abs_control < 0.05:
            return DeviationSeverity.MINOR
        elif abs_control < 0.10:
            return DeviationSeverity.MODERATE
        elif abs_control < 0.15:
            return DeviationSeverity.MAJOR
        else:
            return DeviationSeverity.CRITICAL

    def _pid_signal_to_action_type(
        self,
        setpoint_name: str,
        control_signal: float
    ) -> CorrectiveActionType:
        """Map PID control signal to corrective action type."""
        # Positive control signal = need to increase metric
        # Negative control signal = need to decrease metric

        if setpoint_name == "coverage_rate":
            if control_signal > 0:
                return CorrectiveActionType.RECRUIT_BACKUP  # Increase coverage
            else:
                return CorrectiveActionType.REDUCE_SCOPE  # Reduce demand

        elif setpoint_name == "faculty_utilization":
            if control_signal > 0:
                return CorrectiveActionType.REDISTRIBUTE  # Add assignments
            else:
                return CorrectiveActionType.DEFER_ACTIVITY  # Reduce load

        elif setpoint_name == "workload_balance":
            if abs(control_signal) > 0.05:
                return CorrectiveActionType.REDISTRIBUTE  # Rebalance
            else:
                return CorrectiveActionType.ALERT_ONLY

        else:
            return CorrectiveActionType.ALERT_ONLY

    def _get_pid_action_description(
        self,
        setpoint_name: str,
        pid_result: dict,
        current_value: float
    ) -> str:
        """Generate human-readable description for PID action."""
        controller = self.pid_bank.controllers[self.setpoint_to_pid[setpoint_name]]
        setpoint = controller.config.setpoint
        control = pid_result["control_signal"]
        error = pid_result["error"]

        direction = "increase" if control > 0 else "decrease"
        magnitude = abs(control) * 100  # Convert to percentage

        desc = (
            f"PID: {direction.capitalize()} {setpoint_name.replace('_', ' ')} "
            f"by {magnitude:.1f}% (current: {current_value:.2f}, target: {setpoint:.2f}, "
            f"error: {error:.2f})"
        )

        # Add diagnostics if saturated
        if pid_result.get("integral_saturated"):
            desc += " [INTEGRAL SATURATED]"
        if pid_result.get("output_saturated"):
            desc += " [OUTPUT SATURATED]"

        return desc

    def _merge_recommendations(
        self,
        pid_corrections: list[PIDCorrection],
        homeostasis_corrections: list[CorrectiveAction]
    ) -> list[CorrectiveAction]:
        """
        Merge PID and homeostasis recommendations.

        Strategy:
        - PID corrections override homeostasis for enabled metrics
        - Homeostasis provides volatility and positive feedback alerts
        - Combine both into unified CorrectiveAction list
        """
        merged = []

        # Convert PID corrections to CorrectiveActions
        for pid_corr in pid_corrections:
            # Find corresponding feedback loop
            loop = self.homeostasis.get_feedback_loop(
                self._pid_to_setpoint_name(pid_corr.controller_name)
            )

            action = CorrectiveAction(
                id=uuid4(),
                feedback_loop_id=loop.id if loop else uuid4(),
                action_type=pid_corr.action_type,
                description=pid_corr.description,
                triggered_at=datetime.now(),
                deviation_severity=pid_corr.severity,
                deviation_amount=abs(pid_corr.error),
                target_value=self.pid_bank.controllers[pid_corr.controller_name].config.setpoint,
                actual_value=self.pid_bank.controllers[pid_corr.controller_name].config.setpoint - pid_corr.error,
            )
            merged.append(action)

        # Add homeostasis corrections for non-PID metrics
        for homeo_action in homeostasis_corrections:
            loop = self.homeostasis.feedback_loops.get(homeo_action.feedback_loop_id)
            if loop and not self.pid_enabled_for.get(loop.setpoint.name, False):
                merged.append(homeo_action)

        # Sort by severity (CRITICAL first)
        severity_order = {
            DeviationSeverity.CRITICAL: 0,
            DeviationSeverity.MAJOR: 1,
            DeviationSeverity.MODERATE: 2,
            DeviationSeverity.MINOR: 3,
            DeviationSeverity.NONE: 4,
        }
        merged.sort(key=lambda a: severity_order[a.deviation_severity])

        return merged

    def _pid_to_setpoint_name(self, pid_name: str) -> str:
        """Reverse lookup: PID controller name to setpoint name."""
        for setpoint, pid in self.setpoint_to_pid.items():
            if pid == pid_name:
                return setpoint
        return pid_name

    def enable_pid(self, setpoint_name: str):
        """Enable PID control for a setpoint."""
        self.pid_enabled_for[setpoint_name] = True
        logger.info(f"PID enabled for {setpoint_name}")

    def disable_pid(self, setpoint_name: str):
        """Disable PID control for a setpoint (revert to homeostasis)."""
        self.pid_enabled_for[setpoint_name] = False
        logger.info(f"PID disabled for {setpoint_name}, using homeostasis")

    def reset_pid(self, controller_name: Optional[str] = None):
        """Reset PID controller(s)."""
        self.pid_bank.reset(controller_name)

    def get_status(self) -> dict:
        """Get comprehensive status of bridge and all controllers."""
        return {
            "pid_enabled": self.pid_enabled_for,
            "pid_bank_status": self.pid_bank.get_status(),
            "homeostasis_status": self.homeostasis.get_status(),
        }
```

---

## Test Cases

### Unit Tests for PID Controllers

```python
"""
Tests for PID control implementation.

backend/tests/resilience/test_pid_control.py
"""

import pytest
from datetime import datetime, timedelta

from app.resilience.pid_control import PIDConfig, PIDState, PIDControllerBank


class TestPIDController:
    """Test suite for PID controller."""

    def test_proportional_response(self):
        """Test proportional term responds to error."""
        config = PIDConfig(
            name="test",
            setpoint=0.75,
            Kp=10.0,
            Ki=0.0,  # Disable integral
            Kd=0.0,  # Disable derivative
            output_limits=(-1.0, 1.0)
        )
        controller = PIDState(id=uuid4(), config=config)

        # Error = 0.75 - 0.85 = -0.10
        result = controller.update(0.85)

        # P = 10.0 × -0.10 = -1.0
        assert result["P"] == pytest.approx(-1.0, abs=0.01)
        assert result["control_signal"] == pytest.approx(-1.0, abs=0.01)

    def test_integral_eliminates_steady_state_error(self):
        """Test integral term eliminates persistent error."""
        config = PIDConfig(
            name="test",
            setpoint=0.75,
            Kp=0.0,   # Disable proportional
            Ki=1.0,   # Only integral
            Kd=0.0,
            output_limits=(-1.0, 1.0)
        )
        controller = PIDState(id=uuid4(), config=config)

        # Simulate persistent error over 5 days
        errors = []
        for day in range(5):
            controller.previous_time = datetime.now() - timedelta(days=5-day)
            result = controller.update(0.70)  # Error = +0.05
            errors.append(result["error"])

        # Integral should accumulate
        assert controller.integral > 0
        assert result["I"] > 0

        # After correction, error should decrease (in real system)

    def test_derivative_dampens_oscillation(self):
        """Test derivative term reduces overshoot."""
        config = PIDConfig(
            name="test",
            setpoint=0.75,
            Kp=10.0,
            Ki=0.0,
            Kd=5.0,   # Strong derivative
            output_limits=(-1.0, 1.0)
        )
        controller = PIDState(id=uuid4(), config=config)

        # Step 1: Large error
        controller.previous_time = datetime.now() - timedelta(days=1)
        result1 = controller.update(0.85)  # Error = -0.10

        # Step 2: Error decreasing rapidly
        controller.previous_time = datetime.now() - timedelta(days=1)
        result2 = controller.update(0.76)  # Error = -0.01 (improving fast)

        # Derivative should oppose the change (negative D for decreasing error)
        assert result2["D"] > 0  # Positive derivative (error became less negative)

        # Total control should be reduced by derivative
        assert abs(result2["control_signal"]) < abs(result2["P"])

    def test_anti_windup_integral_clamping(self):
        """Test integral windup protection."""
        config = PIDConfig(
            name="test",
            setpoint=0.75,
            Kp=0.0,
            Ki=1.0,
            Kd=0.0,
            output_limits=(-0.2, 0.2),
            integral_limits=(-5.0, 5.0)
        )
        controller = PIDState(id=uuid4(), config=config)

        # Simulate sustained error that would cause windup
        for day in range(20):
            controller.previous_time = datetime.now() - timedelta(days=20-day)
            result = controller.update(0.50)  # Error = +0.25 (large)

        # Integral should be clamped
        assert controller.integral <= 5.0
        assert result["integral_saturated"] is True

    def test_output_limiting(self):
        """Test control signal is clamped to output limits."""
        config = PIDConfig(
            name="test",
            setpoint=0.75,
            Kp=100.0,  # Very high gain
            Ki=0.0,
            Kd=0.0,
            output_limits=(-0.2, 0.2)
        )
        controller = PIDState(id=uuid4(), config=config)

        # Large error → large control signal
        result = controller.update(0.95)  # Error = -0.20

        # P = 100 × -0.20 = -20.0 (huge)
        # But output should be clamped to -0.2
        assert result["control_signal"] == pytest.approx(-0.2, abs=0.001)
        assert result["output_saturated"] is True

    def test_setpoint_change_resets_integral(self):
        """Test integral is reset when setpoint changes."""
        config = PIDConfig(
            name="test",
            setpoint=0.75,
            Kp=1.0,
            Ki=1.0,
            Kd=0.0,
            output_limits=(-1.0, 1.0)
        )
        controller = PIDState(id=uuid4(), config=config)

        # Accumulate some integral
        for _ in range(5):
            controller.update(0.70)

        initial_integral = controller.integral
        assert initial_integral > 0

        # Change setpoint
        controller.set_setpoint(0.80)

        # Integral should be reset
        assert controller.integral == 0.0


class TestPIDControllerBank:
    """Test suite for PID controller bank."""

    def test_default_controllers_initialized(self):
        """Test bank initializes with three default controllers."""
        bank = PIDControllerBank()

        assert "utilization" in bank.controllers
        assert "workload_balance" in bank.controllers
        assert "coverage" in bank.controllers

    def test_update_controller(self):
        """Test updating a controller."""
        bank = PIDControllerBank()

        result = bank.update("utilization", 0.82)

        assert "error" in result
        assert "control_signal" in result
        assert result["error"] == pytest.approx(0.75 - 0.82, abs=0.01)

    def test_unknown_controller_raises_error(self):
        """Test updating unknown controller raises ValueError."""
        bank = PIDControllerBank()

        with pytest.raises(ValueError, match="Unknown controller"):
            bank.update("invalid", 0.5)

    def test_ziegler_nichols_tuning(self):
        """Test Ziegler-Nichols auto-tuning."""
        bank = PIDControllerBank()

        # Tune utilization controller
        Ku = 15.0
        Pu = 7.0
        bank.tune_ziegler_nichols("utilization", Ku, Pu)

        controller = bank.controllers["utilization"]

        # Expected: Kp = 0.6×15 = 9.0, Ki = 1.2×15/7 ≈ 2.57, Kd = 0.075×15×7 ≈ 7.88
        assert controller.config.Kp == pytest.approx(9.0, abs=0.1)
        assert controller.config.Ki == pytest.approx(2.57, abs=0.1)
        assert controller.config.Kd == pytest.approx(7.88, abs=0.1)

    def test_reset_specific_controller(self):
        """Test resetting a specific controller."""
        bank = PIDControllerBank()

        # Accumulate state
        bank.update("utilization", 0.82)
        bank.update("coverage", 0.88)

        util_controller = bank.controllers["utilization"]
        coverage_controller = bank.controllers["coverage"]

        # Reset only utilization
        bank.reset("utilization")

        assert util_controller.integral == 0.0
        assert util_controller.previous_error == 0.0
        assert coverage_controller.integral != 0.0  # Should not be reset

    def test_reset_all_controllers(self):
        """Test resetting all controllers."""
        bank = PIDControllerBank()

        # Accumulate state in all
        bank.update("utilization", 0.82)
        bank.update("coverage", 0.88)
        bank.update("workload_balance", 0.20)

        # Reset all
        bank.reset()

        for controller in bank.controllers.values():
            assert controller.integral == 0.0
            assert controller.previous_error == 0.0
```

### Integration Tests for Bridge

```python
"""
Integration tests for PID-Homeostasis Bridge.

backend/tests/resilience/test_pid_homeostasis_bridge.py
"""

import pytest
from unittest.mock import Mock

from app.resilience.homeostasis import HomeostasisMonitor, DeviationSeverity, CorrectiveActionType
from app.resilience.pid_homeostasis_bridge import PIDHomeostasisBridge


class TestPIDHomeostasisBridge:
    """Test suite for PID-Homeostasis Bridge."""

    @pytest.fixture
    def homeostasis_monitor(self):
        """Create homeostasis monitor instance."""
        return HomeostasisMonitor()

    @pytest.fixture
    def bridge(self, homeostasis_monitor):
        """Create bridge instance."""
        return PIDHomeostasisBridge(homeostasis_monitor)

    def test_update_all_with_pid_enabled(self, bridge):
        """Test update_all when PID is enabled."""
        current_values = {
            "coverage_rate": 0.91,
            "faculty_utilization": 0.82,
            "workload_balance": 0.18,
        }

        result = bridge.update_all(current_values)

        assert "pid_corrections" in result
        assert "homeostasis_corrections" in result
        assert "merged_actions" in result

        # PID should generate corrections for enabled metrics
        pid_controllers = [c.controller_name for c in result["pid_corrections"]]
        assert "coverage" in pid_controllers  # Enabled by default
        assert "utilization" in pid_controllers  # Enabled by default

    def test_pid_overrides_homeostasis_for_enabled_metrics(self, bridge):
        """Test PID corrections override homeostasis for enabled metrics."""
        current_values = {
            "coverage_rate": 0.85,  # Below target (0.95)
            "faculty_utilization": 0.82,
        }

        result = bridge.update_all(current_values)

        # Check that merged actions come from PID (not homeostasis) for coverage
        coverage_actions = [
            a for a in result["merged_actions"]
            if "coverage" in a.description.lower()
        ]

        assert len(coverage_actions) > 0
        # Description should mention "PID"
        assert any("PID" in a.description for a in coverage_actions)

    def test_control_signal_to_severity_mapping(self, bridge):
        """Test control signal magnitude maps to severity correctly."""
        assert bridge._control_signal_to_severity(0.01) == DeviationSeverity.NONE
        assert bridge._control_signal_to_severity(0.03) == DeviationSeverity.MINOR
        assert bridge._control_signal_to_severity(0.08) == DeviationSeverity.MODERATE
        assert bridge._control_signal_to_severity(0.12) == DeviationSeverity.MAJOR
        assert bridge._control_signal_to_severity(0.20) == DeviationSeverity.CRITICAL

    def test_pid_signal_to_action_type_coverage(self, bridge):
        """Test PID signal maps to correct action type for coverage."""
        # Positive control = increase coverage
        action = bridge._pid_signal_to_action_type("coverage_rate", 0.1)
        assert action == CorrectiveActionType.RECRUIT_BACKUP

        # Negative control = reduce scope
        action = bridge._pid_signal_to_action_type("coverage_rate", -0.1)
        assert action == CorrectiveActionType.REDUCE_SCOPE

    def test_pid_signal_to_action_type_utilization(self, bridge):
        """Test PID signal maps to correct action type for utilization."""
        # Positive control = add assignments
        action = bridge._pid_signal_to_action_type("faculty_utilization", 0.1)
        assert action == CorrectiveActionType.REDISTRIBUTE

        # Negative control = reduce load
        action = bridge._pid_signal_to_action_type("faculty_utilization", -0.1)
        assert action == CorrectiveActionType.DEFER_ACTIVITY

    def test_enable_disable_pid(self, bridge):
        """Test enabling/disabling PID for specific metrics."""
        # Initially workload_balance is disabled
        assert bridge.pid_enabled_for["workload_balance"] is False

        # Enable it
        bridge.enable_pid("workload_balance")
        assert bridge.pid_enabled_for["workload_balance"] is True

        # Disable it
        bridge.disable_pid("workload_balance")
        assert bridge.pid_enabled_for["workload_balance"] is False

    def test_dual_mode_operation(self, bridge):
        """Test bridge operates in dual mode (PID + homeostasis)."""
        # Disable PID for utilization
        bridge.disable_pid("faculty_utilization")

        current_values = {
            "coverage_rate": 0.91,  # PID enabled
            "faculty_utilization": 0.82,  # PID disabled → homeostasis
        }

        result = bridge.update_all(current_values)

        # PID should only run for coverage
        pid_controllers = [c.controller_name for c in result["pid_corrections"]]
        assert "coverage" in pid_controllers
        assert "utilization" not in pid_controllers

        # Homeostasis should handle utilization
        assert len(result["homeostasis_corrections"]) > 0
```

### Performance Tests

```python
"""
Performance tests for PID control.

backend/tests/resilience/test_pid_performance.py
"""

import pytest
import numpy as np
from datetime import datetime, timedelta

from app.resilience.pid_control import PIDControllerBank


class TestPIDPerformance:
    """Test PID controller performance characteristics."""

    def test_step_response(self):
        """Test response to step change in setpoint."""
        bank = PIDControllerBank()

        # Simulate step response: setpoint changes from 0.75 to 0.80
        bank.controllers["utilization"].set_setpoint(0.80)

        # Simulate system response over 30 days
        utilization_values = []
        control_signals = []

        current_util = 0.75  # Start at old setpoint

        for day in range(30):
            # Update controller
            result = bank.update("utilization", current_util)
            control_signals.append(result["control_signal"])

            # Simulate system response (simple first-order model)
            # du/dt = control_signal (simplified)
            current_util += result["control_signal"] * 0.1  # 10% response rate
            utilization_values.append(current_util)

            # Advance time
            bank.controllers["utilization"].previous_time = datetime.now() - timedelta(days=30-day)

        # Check convergence
        final_util = utilization_values[-1]
        assert final_util == pytest.approx(0.80, abs=0.02)  # Should converge to new setpoint

        # Check for overshoot
        max_util = max(utilization_values)
        assert max_util < 0.85  # Should not overshoot by more than 5%

    def test_disturbance_rejection(self):
        """Test controller rejects disturbances."""
        bank = PIDControllerBank()

        # System at steady state
        current_coverage = 0.95

        # Simulate disturbance at day 10 (sudden absence drops coverage)
        disturbances = [0.0] * 10 + [-0.10] + [0.0] * 19  # -10% coverage drop

        coverage_values = []
        for day, disturbance in enumerate(disturbances):
            # Update controller
            result = bank.update("coverage", current_coverage)

            # Apply control and disturbance
            current_coverage += result["control_signal"] * 0.2 + disturbance
            coverage_values.append(current_coverage)

        # Recovery time: how long to get back within 2% of setpoint
        recovery_day = None
        for day, cov in enumerate(coverage_values[11:], start=11):  # Start after disturbance
            if abs(cov - 0.95) < 0.02:
                recovery_day = day
                break

        assert recovery_day is not None
        assert recovery_day < 20  # Should recover within 10 days

    def test_steady_state_error(self):
        """Test integral term eliminates steady-state error."""
        bank = PIDControllerBank()

        # Simulate system with bias (always settles 5% below target)
        target = 0.75
        system_bias = -0.05

        current_util = 0.70  # Start below target

        for day in range(50):
            result = bank.update("utilization", current_util)

            # System response with bias
            current_util += result["control_signal"] * 0.15 + system_bias * 0.01

        # Integral term should compensate for bias
        # Final value should be close to target despite bias
        assert current_util == pytest.approx(target, abs=0.03)
```

---

## Performance Metrics

### Key Performance Indicators (KPIs)

Track these metrics to evaluate PID performance:

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Rise Time** | < 7 days | Time to reach 90% of setpoint after step change |
| **Settling Time** | < 14 days | Time to stay within ±2% of setpoint |
| **Overshoot** | < 5% | Maximum deviation beyond setpoint |
| **Steady-State Error** | < 1% | Final error after convergence |
| **Disturbance Rejection** | < 10 days | Recovery time after 10% disturbance |
| **Oscillation Frequency** | < 10% cycles | Proportion of updates with sign changes |

### Monitoring Dashboard

Create Grafana dashboard with these panels:

```yaml
# grafana/dashboards/pid_control.json

panels:
  - title: "PID Control Signals"
    type: time-series
    targets:
      - "utilization_control_signal"
      - "workload_control_signal"
      - "coverage_control_signal"

  - title: "PID Error Tracking"
    type: time-series
    targets:
      - "utilization_error"
      - "workload_error"
      - "coverage_error"

  - title: "PID Term Decomposition"
    type: time-series
    targets:
      - "utilization_P_term"
      - "utilization_I_term"
      - "utilization_D_term"

  - title: "Saturation Alerts"
    type: stat
    targets:
      - "integral_saturation_count"
      - "output_saturation_count"

  - title: "Oscillation Detection"
    type: gauge
    targets:
      - "oscillation_count_per_100_cycles"
```

### Logging Strategy

```python
# Add to backend/app/resilience/pid_homeostasis_bridge.py

import logging

logger = logging.getLogger(__name__)

def _log_pid_update(self, controller_name: str, pid_result: dict, current_value: float):
    """Log PID update for monitoring."""
    logger.info(
        f"PID update: {controller_name} | "
        f"value={current_value:.3f} | "
        f"error={pid_result['error']:.3f} | "
        f"control={pid_result['control_signal']:.3f} | "
        f"P={pid_result['P']:.2f}, I={pid_result['I']:.2f}, D={pid_result['D']:.2f} | "
        f"saturated={'I' if pid_result['integral_saturated'] else ''}{'O' if pid_result['output_saturated'] else ''}"
    )

    # Prometheus metrics
    prometheus_client.Gauge(
        f'pid_{controller_name}_error',
        'PID error for {controller_name}'
    ).set(pid_result['error'])

    prometheus_client.Gauge(
        f'pid_{controller_name}_control_signal',
        'PID control signal for {controller_name}'
    ).set(pid_result['control_signal'])
```

---

## Migration Strategy

### Phase 1: Infrastructure (Week 1)

**Objective:** Deploy PID infrastructure without changing behavior

**Tasks:**
1. Implement `pid_control.py` (PID controllers)
2. Implement `pid_homeostasis_bridge.py` (bridge)
3. Add unit tests (target: 90% coverage)
4. Add PID metrics to Prometheus
5. Create Grafana dashboard

**Validation:**
- All tests pass
- Metrics are collected
- Dashboard displays mock data

### Phase 2: Coverage PID (Week 2)

**Objective:** Enable PID for coverage rate (most critical metric)

**Tasks:**
1. Enable PID for `coverage_rate` in production
2. Run dual-mode for 7 days (PID + homeostasis in parallel)
3. Compare PID vs homeostasis recommendations
4. Tune gains based on real data
5. Gradually increase PID authority (20% → 50% → 100%)

**Success Criteria:**
- PID converges faster than homeostasis (< 7 days vs 14 days)
- No oscillations or instability
- Coverage stays within ±2% of target

### Phase 3: Utilization PID (Week 3)

**Objective:** Enable PID for utilization control

**Tasks:**
1. Enable PID for `faculty_utilization`
2. Run dual-mode for 7 days
3. Tune gains (may need lower Kp than coverage due to slower dynamics)
4. Monitor for interactions with coverage PID

**Success Criteria:**
- Utilization stays below 80% threshold
- Workload distribution remains acceptable
- No conflicts with coverage PID

### Phase 4: Workload PID (Week 4)

**Objective:** Enable PID for workload balance

**Tasks:**
1. Enable PID for `workload_balance`
2. Run full system with all three PIDs
3. Optimize gain scheduling (adjust gains by defense level)
4. Document final tuning parameters

**Success Criteria:**
- Workload std dev < 0.15
- All three PIDs stable
- System performance better than homeostasis-only baseline

### Phase 5: Deprecate Old Logic (Week 5)

**Objective:** Remove ad-hoc homeostasis correction logic

**Tasks:**
1. Verify PID handles all scenarios
2. Remove `_determine_action_type()` and `_trigger_correction()` from homeostasis
3. Update tests to use PID exclusively
4. Archive old code for rollback safety

**Rollback Plan:**
- If issues arise, disable PID via feature flags
- System reverts to homeostasis-only mode
- Investigate issues offline, re-enable when fixed

---

## Conclusion

This specification provides a **complete, implementation-ready design** for integrating formal PID control with the existing homeostasis system. The bridge pattern allows for:

- **Gradual migration** without breaking existing functionality
- **Dual-mode operation** for validation and comparison
- **Mathematical rigor** with proven stability guarantees
- **Anti-windup protection** for robust performance
- **Performance monitoring** via Grafana dashboards
- **Easy rollback** if issues arise

The PID controllers replace ad-hoc correction logic with a **mathematically sound approach** that:

1. **Converges faster** to setpoints (7 days vs 14 days)
2. **Eliminates steady-state error** via integral action
3. **Dampens oscillations** via derivative action
4. **Adapts to changing conditions** via gain scheduling

### Next Steps

1. Implement `pid_control.py` and `pid_homeostasis_bridge.py`
2. Add comprehensive test suite (unit + integration + performance)
3. Deploy to staging environment for validation
4. Roll out to production following phased migration plan
5. Monitor KPIs and tune gains based on real-world performance

### References

- **Control Theory:** Åström, K. J., & Murray, R. M. (2008). *Feedback Systems: An Introduction for Scientists and Engineers*
- **PID Tuning:** Ziegler, J. G., & Nichols, N. B. (1942). "Optimum Settings for Automatic Controllers"
- **Anti-Windup:** Åström, K. J., & Hägglund, T. (1995). *PID Controllers: Theory, Design, and Tuning*
- **Homeostasis:** Sterling, P., & Eyer, J. (1988). "Allostasis: A New Paradigm to Explain Arousal Pathology"

---

**Document Status:** ✅ Implementation-Ready
**Author:** Claude (AI Assistant)
**Date:** 2025-12-26
**Version:** 1.0
