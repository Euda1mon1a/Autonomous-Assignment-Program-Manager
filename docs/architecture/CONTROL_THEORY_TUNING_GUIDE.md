***REMOVED*** Control Theory Tuning Guide for Residency Scheduler

> **Purpose:** Comprehensive tuning procedures for PID controllers, Kalman filters, and Model Predictive Control in the residency scheduling system
> **Target Audience:** System engineers, DevOps, researchers
> **Prerequisites:** Basic understanding of control theory concepts
> **Last Updated:** 2025-12-26

---

***REMOVED******REMOVED*** Table of Contents

1. [Introduction](***REMOVED***introduction)
2. [System Overview](***REMOVED***system-overview)
3. [PID Controller Tuning](***REMOVED***pid-controller-tuning)
4. [Kalman Filter Configuration](***REMOVED***kalman-filter-configuration)
5. [Model Predictive Control Tuning](***REMOVED***model-predictive-control-tuning)
6. [System Identification](***REMOVED***system-identification)
7. [Integration Testing](***REMOVED***integration-testing)
8. [Troubleshooting Guide](***REMOVED***troubleshooting-guide)
9. [References](***REMOVED***references)

---

***REMOVED******REMOVED*** Introduction

***REMOVED******REMOVED******REMOVED*** Purpose of This Guide

Control theory provides mathematical rigor for managing complex scheduling dynamics. This guide presents **practical, step-by-step tuning procedures** for three complementary control strategies:

- **PID Controllers:** Fast, local feedback for utilization, workload, and coverage
- **Kalman Filters:** Optimal state estimation from noisy measurements
- **Model Predictive Control:** Optimal multi-week schedule generation with constraints

***REMOVED******REMOVED******REMOVED*** When to Use Each Technique

| Technique | Use Case | Time Horizon | Computational Cost |
|-----------|----------|--------------|-------------------|
| **PID** | Real-time corrections (hours/days) | 1-7 days | Very Low |
| **Kalman Filter** | State estimation from noisy data | Continuous | Low |
| **MPC** | Schedule optimization | 2-8 weeks | Medium-High |

***REMOVED******REMOVED******REMOVED*** Prerequisites

Before tuning, ensure:

1. ✅ Homeostasis system is operational (`backend/app/resilience/homeostasis.py`)
2. ✅ Historical data available (>90 days for system identification)
3. ✅ Metrics collection working (utilization, coverage, workload)
4. ✅ Testing environment set up for safe experimentation

---

***REMOVED******REMOVED*** System Overview

***REMOVED******REMOVED******REMOVED*** Control Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                  CONTROL SYSTEM LAYERS                        │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│  Layer 1: State Estimation (Kalman Filters)                  │
│  ├─ Workload Kalman Filter                                   │
│  ├─ Schedule Health Extended Kalman Filter                   │
│  └─ Outputs: Filtered state estimates                        │
│                                                               │
│  Layer 2: Feedback Control (PID Controllers)                 │
│  ├─ Utilization PID (setpoint: 0.75)                         │
│  ├─ Workload Balance PID (setpoint: 0.15 std_dev)           │
│  ├─ Coverage PID (setpoint: 0.95)                            │
│  └─ Outputs: Corrective actions                              │
│                                                               │
│  Layer 3: Predictive Optimization (MPC)                      │
│  ├─ 4-week prediction horizon                                │
│  ├─ 2-week control horizon                                   │
│  ├─ Constraint enforcement (ACGME, preferences)              │
│  └─ Outputs: Optimized 4-week schedule                       │
│                                                               │
└──────────────────────────────────────────────────────────────┘
```

***REMOVED******REMOVED******REMOVED*** Process Variables and Setpoints

| Variable | Symbol | Setpoint | Tolerance | Unit | Priority |
|----------|--------|----------|-----------|------|----------|
| **Faculty Utilization** | u | 0.75 | ±0.05 | ratio | High |
| **Workload Balance** | σ_w | 0.15 | ±0.03 | std_dev | Medium |
| **Coverage Rate** | c | 0.95 | ±0.02 | ratio | **CRITICAL** |
| **Schedule Stability** | s | 0.95 | ±0.05 | ratio | Medium |
| **ACGME Compliance** | a | 1.00 | ±0.00 | ratio | **CRITICAL** |

---

***REMOVED******REMOVED*** PID Controller Tuning

***REMOVED******REMOVED******REMOVED*** Overview

PID (Proportional-Integral-Derivative) controllers provide **fast, local feedback** to maintain process variables at setpoints. The control law is:

```
u(t) = Kp·e(t) + Ki·∫e(τ)dτ + Kd·de(t)/dt

Where:
  e(t) = setpoint - measured_value  (error)
  Kp = Proportional gain
  Ki = Integral gain
  Kd = Derivative gain
```

***REMOVED******REMOVED******REMOVED*** Method 1: Ziegler-Nichols Ultimate Cycling

**Best for:** Initial tuning when system behavior is unknown

**Procedure:**

***REMOVED******REMOVED******REMOVED******REMOVED*** Step 1: Set Up P-Only Controller

```python
***REMOVED*** File: backend/scripts/tune_pid_ziegler_nichols.py

from app.resilience.pid_control import PIDControllerBank
from app.resilience.homeostasis import HomeostasisMonitor
import matplotlib.pyplot as plt
import numpy as np

***REMOVED*** Initialize controller with only P term
bank = PIDControllerBank()
controller = bank.controllers["utilization"]

***REMOVED*** Disable I and D terms
controller.config.Ki = 0.0
controller.config.Kd = 0.0
controller.config.Kp = 1.0  ***REMOVED*** Start conservative

print("=== Ziegler-Nichols Tuning: Step 1 ===")
print("Set Ki=0, Kd=0, starting with Kp=1.0")
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Step 2: Increase Kp Until Sustained Oscillation

```python
def simulate_system_response(
    controller,
    setpoint: float,
    duration_days: int,
    initial_value: float,
    system_gain: float = 0.1,  ***REMOVED*** System responsiveness
    system_lag: float = 0.8,   ***REMOVED*** System inertia
) -> tuple[list[float], list[float], list[float]]:
    """
    Simulate closed-loop system response.

    Args:
        controller: PID controller instance
        setpoint: Target value
        duration_days: Simulation length
        initial_value: Starting process variable value
        system_gain: How much control signal affects output (0-1)
        system_lag: First-order lag coefficient (0-1, higher = more lag)

    Returns:
        (time, output, control_signal) arrays
    """
    time = []
    output = []
    control_signals = []

    current_output = initial_value

    for day in range(duration_days):
        ***REMOVED*** Measure current state
        error = setpoint - current_output

        ***REMOVED*** Calculate control signal (PID)
        P = controller.config.Kp * error
        I = controller.config.Ki * controller.integral
        D = controller.config.Kd * (error - controller.previous_error)

        control_signal = P + I + D

        ***REMOVED*** Update controller state
        controller.integral += error
        controller.integral = np.clip(
            controller.integral,
            controller.config.integral_limits[0],
            controller.config.integral_limits[1]
        )
        controller.previous_error = error

        ***REMOVED*** Simulate system dynamics (first-order with lag)
        output_change = system_gain * control_signal
        current_output = system_lag * current_output + (1 - system_lag) * (current_output + output_change)

        ***REMOVED*** Add noise
        current_output += np.random.normal(0, 0.01)

        ***REMOVED*** Record
        time.append(day)
        output.append(current_output)
        control_signals.append(control_signal)

    return time, output, control_signals


***REMOVED*** Find ultimate gain (Ku)
Kp_values = np.linspace(1.0, 30.0, 30)
results = {}

for Kp in Kp_values:
    controller.config.Kp = Kp
    controller.reset()

    time, output, control = simulate_system_response(
        controller,
        setpoint=0.75,
        duration_days=60,
        initial_value=0.70
    )

    ***REMOVED*** Detect sustained oscillation
    ***REMOVED*** Use last 20 days to check for steady oscillation
    recent_output = output[-20:]

    ***REMOVED*** Count zero crossings
    mean_output = np.mean(recent_output)
    crossings = sum(
        1 for i in range(1, len(recent_output))
        if (recent_output[i] - mean_output) * (recent_output[i-1] - mean_output) < 0
    )

    ***REMOVED*** Check amplitude consistency (oscillation without divergence)
    amplitude = np.std(recent_output)

    results[Kp] = {
        "crossings": crossings,
        "amplitude": amplitude,
        "output": output,
        "is_oscillating": crossings >= 8 and amplitude > 0.02,  ***REMOVED*** Significant oscillation
    }

    print(f"Kp={Kp:.1f}: crossings={crossings}, amplitude={amplitude:.4f}, oscillating={results[Kp]['is_oscillating']}")

***REMOVED*** Find ultimate gain
oscillating_Kps = [Kp for Kp, r in results.items() if r["is_oscillating"]]

if oscillating_Kps:
    Ku = oscillating_Kps[0]  ***REMOVED*** First Kp that causes oscillation

    ***REMOVED*** Measure ultimate period (Pu)
    oscillating_output = results[Ku]["output"][-20:]

    ***REMOVED*** Find peaks
    peaks = []
    for i in range(1, len(oscillating_output) - 1):
        if oscillating_output[i] > oscillating_output[i-1] and oscillating_output[i] > oscillating_output[i+1]:
            peaks.append(i)

    if len(peaks) >= 2:
        Pu = np.mean([peaks[i+1] - peaks[i] for i in range(len(peaks)-1)])

        print(f"\n=== Ultimate Cycling Found ===")
        print(f"Ultimate Gain (Ku): {Ku:.2f}")
        print(f"Ultimate Period (Pu): {Pu:.2f} days")

        ***REMOVED*** Calculate Ziegler-Nichols gains
        Kp_zn = 0.6 * Ku
        Ki_zn = 1.2 * Ku / Pu
        Kd_zn = 0.075 * Ku * Pu

        print(f"\n=== Ziegler-Nichols PID Gains ===")
        print(f"Kp = {Kp_zn:.2f}")
        print(f"Ki = {Ki_zn:.2f}")
        print(f"Kd = {Kd_zn:.2f}")

        ***REMOVED*** Apply gains
        controller.config.Kp = Kp_zn
        controller.config.Ki = Ki_zn
        controller.config.Kd = Kd_zn

        print("\n✓ Gains applied to controller")
    else:
        print("Error: Could not detect clear oscillation period")
else:
    print("Error: No sustained oscillation found. Increase Kp range or adjust system parameters.")
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Step 3: Validate Tuned Controller

```python
***REMOVED*** Test tuned controller
controller.reset()

time, output, control = simulate_system_response(
    controller,
    setpoint=0.75,
    duration_days=60,
    initial_value=0.70
)

***REMOVED*** Calculate performance metrics
settling_time = None
for i, val in enumerate(output):
    if abs(val - 0.75) < 0.02:  ***REMOVED*** Within 2% of setpoint
        ***REMOVED*** Check if it stays within band
        if all(abs(v - 0.75) < 0.02 for v in output[i:min(i+7, len(output))]):
            settling_time = i
            break

overshoot = max(output) - 0.75 if max(output) > 0.75 else 0
steady_state_error = abs(output[-1] - 0.75)

print(f"\n=== Performance Metrics ===")
print(f"Settling Time: {settling_time} days")
print(f"Overshoot: {overshoot:.4f} ({overshoot/0.75*100:.1f}%)")
print(f"Steady-State Error: {steady_state_error:.4f}")

***REMOVED*** Plot results
plt.figure(figsize=(12, 8))

plt.subplot(2, 1, 1)
plt.plot(time, output, label='System Output', linewidth=2)
plt.axhline(y=0.75, color='r', linestyle='--', label='Setpoint')
plt.axhline(y=0.77, color='g', linestyle=':', alpha=0.5, label='±2% band')
plt.axhline(y=0.73, color='g', linestyle=':', alpha=0.5)
plt.xlabel('Time (days)')
plt.ylabel('Utilization')
plt.title('PID Controller Response (Ziegler-Nichols Tuning)')
plt.legend()
plt.grid(True, alpha=0.3)

plt.subplot(2, 1, 2)
plt.plot(time, control, label='Control Signal', color='orange', linewidth=2)
plt.xlabel('Time (days)')
plt.ylabel('Control Signal')
plt.title('Control Signal Over Time')
plt.legend()
plt.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('backend/data/pid_ziegler_nichols_tuning.png', dpi=150)
print("\n✓ Plot saved to backend/data/pid_ziegler_nichols_tuning.png")
```

**Strengths:**
- ✅ Systematic, proven method
- ✅ No model required
- ✅ Good starting point

**Weaknesses:**
- ❌ Requires inducing oscillations (disruptive)
- ❌ Conservative (may need refinement)
- ❌ Not optimal for all systems

---

***REMOVED******REMOVED******REMOVED*** Method 2: Cohen-Coon Tuning Rules

**Best for:** Systems with significant lag or dead time

**Theory:**

Cohen-Coon method uses **open-loop step response** to identify system characteristics, then calculates PID gains analytically.

**System Model:**
```
G(s) = K·e^(-θs) / (τs + 1)

Where:
  K = Process gain
  θ = Dead time (delay before response)
  τ = Time constant (63.2% response time)
```

**Procedure:**

***REMOVED******REMOVED******REMOVED******REMOVED*** Step 1: Perform Open-Loop Step Test

```python
***REMOVED*** File: backend/scripts/tune_pid_cohen_coon.py

import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit

def perform_step_test(
    initial_utilization: float = 0.70,
    step_magnitude: float = 0.05,  ***REMOVED*** 5% increase in assignments
    duration_days: int = 30,
) -> tuple[list[float], list[float]]:
    """
    Simulate open-loop step response.

    In production: Apply a step change to assignments and measure utilization
    over time WITHOUT feedback control.
    """
    time = []
    output = []

    ***REMOVED*** Simulate first-order system with dead time
    K = 1.0  ***REMOVED*** Process gain (output change / input change)
    tau = 7.0  ***REMOVED*** Time constant (days)
    theta = 1.5  ***REMOVED*** Dead time (days)

    for day in range(duration_days):
        if day < theta:
            ***REMOVED*** Dead time - no response yet
            response = initial_utilization
        else:
            ***REMOVED*** First-order response after dead time
            t_eff = day - theta
            response = initial_utilization + K * step_magnitude * (1 - np.exp(-t_eff / tau))

        ***REMOVED*** Add measurement noise
        response += np.random.normal(0, 0.005)

        time.append(day)
        output.append(response)

    return time, output

***REMOVED*** Run step test
time, output = perform_step_test()

***REMOVED*** Plot step response
plt.figure(figsize=(10, 6))
plt.plot(time, output, 'b-', linewidth=2, label='System Response')
plt.axhline(y=0.70, color='r', linestyle='--', alpha=0.5, label='Initial Value')
plt.axhline(y=0.75, color='g', linestyle='--', alpha=0.5, label='Final Value')
plt.xlabel('Time (days)')
plt.ylabel('Utilization')
plt.title('Open-Loop Step Response')
plt.legend()
plt.grid(True, alpha=0.3)
plt.savefig('backend/data/step_response.png', dpi=150)
print("✓ Step response saved to backend/data/step_response.png")
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Step 2: Identify System Parameters

```python
def first_order_model(t, K, tau, theta):
    """First-order plus dead time (FOPDT) model."""
    return 0.70 + K * 0.05 * np.maximum(0, 1 - np.exp(-(np.maximum(0, t - theta)) / tau))

***REMOVED*** Fit FOPDT model to data
popt, pcov = curve_fit(
    first_order_model,
    time,
    output,
    p0=[1.0, 7.0, 1.5],  ***REMOVED*** Initial guess
    bounds=([0.5, 1.0, 0.0], [2.0, 20.0, 5.0])  ***REMOVED*** Parameter bounds
)

K_identified, tau_identified, theta_identified = popt

print(f"\n=== Identified System Parameters ===")
print(f"Process Gain (K): {K_identified:.3f}")
print(f"Time Constant (τ): {tau_identified:.2f} days")
print(f"Dead Time (θ): {theta_identified:.2f} days")

***REMOVED*** Calculate dimensionless ratios
tau_theta_ratio = tau_identified / theta_identified
print(f"\nτ/θ ratio: {tau_theta_ratio:.2f}")

***REMOVED*** Plot fitted model
fitted_output = [first_order_model(t, *popt) for t in time]
plt.figure(figsize=(10, 6))
plt.plot(time, output, 'b-', linewidth=2, label='Measured')
plt.plot(time, fitted_output, 'r--', linewidth=2, label='Fitted Model')
plt.xlabel('Time (days)')
plt.ylabel('Utilization')
plt.title('FOPDT Model Fit')
plt.legend()
plt.grid(True, alpha=0.3)
plt.savefig('backend/data/model_fit.png', dpi=150)
print("✓ Model fit saved to backend/data/model_fit.png")
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Step 3: Calculate Cohen-Coon PID Gains

```python
def cohen_coon_pid_gains(K: float, tau: float, theta: float) -> tuple[float, float, float]:
    """
    Calculate PID gains using Cohen-Coon tuning rules.

    Args:
        K: Process gain
        tau: Time constant
        theta: Dead time

    Returns:
        (Kp, Ki, Kd) tuple
    """
    ***REMOVED*** Cohen-Coon formulas
    Kp = (1.0 / K) * (tau / theta) * (1.0 + theta / (3 * tau))

    Ti = theta * ((32 + 6 * theta / tau) / (13 + 8 * theta / tau))
    Ki = Kp / Ti

    Td = theta * (4.0 / (11 + 2 * theta / tau))
    Kd = Kp * Td

    return Kp, Ki, Kd

Kp_cc, Ki_cc, Kd_cc = cohen_coon_pid_gains(K_identified, tau_identified, theta_identified)

print(f"\n=== Cohen-Coon PID Gains ===")
print(f"Kp = {Kp_cc:.2f}")
print(f"Ki = {Ki_cc:.2f}")
print(f"Kd = {Kd_cc:.2f}")

***REMOVED*** Compare with Ziegler-Nichols (if available)
print(f"\nComparison:")
print(f"{'Method':<15} {'Kp':>8} {'Ki':>8} {'Kd':>8}")
print(f"{'Cohen-Coon':<15} {Kp_cc:>8.2f} {Ki_cc:>8.2f} {Kd_cc:>8.2f}")
***REMOVED*** print(f"{'Ziegler-Nichols':<15} {Kp_zn:>8.2f} {Ki_zn:>8.2f} {Kd_zn:>8.2f}")

***REMOVED*** Apply gains
from app.resilience.pid_control import PIDControllerBank

bank = PIDControllerBank()
controller = bank.controllers["utilization"]

controller.config.Kp = Kp_cc
controller.config.Ki = Ki_cc
controller.config.Kd = Kd_cc

print("\n✓ Cohen-Coon gains applied to controller")
```

**When to Use Cohen-Coon:**

- ✅ System has noticeable dead time (θ > 0)
- ✅ Can't tolerate sustained oscillations (Ziegler-Nichols not viable)
- ✅ Want aggressive tuning (faster than Ziegler-Nichols)

**Caveats:**

- ⚠️ More aggressive than Ziegler-Nichols (risk of overshoot)
- ⚠️ Less robust to model mismatch
- ⚠️ May need detuning for safety-critical applications

---

***REMOVED******REMOVED******REMOVED*** Method 3: Relay Feedback Auto-Tuning

**Best for:** Automated tuning in production without manual intervention

**Theory:**

Relay feedback induces **limit cycle oscillation** without needing to manually sweep Kp. The system oscillates at its natural frequency, revealing Ku and Pu.

**Algorithm:**

```python
***REMOVED*** File: backend/scripts/tune_pid_relay_feedback.py

import numpy as np
import matplotlib.pyplot as plt

def relay_feedback_test(
    setpoint: float = 0.75,
    relay_amplitude: float = 0.1,  ***REMOVED*** ±10% control signal
    hysteresis: float = 0.01,  ***REMOVED*** Deadband to prevent chattering
    duration_days: int = 60,
    initial_value: float = 0.70,
) -> tuple[list[float], list[float], list[float], float, float]:
    """
    Perform relay feedback test to identify ultimate gain and period.

    Returns:
        (time, output, control, Ku, Pu)
    """
    time = []
    output = []
    control_signals = []

    current_output = initial_value
    relay_state = 1  ***REMOVED*** +1 or -1

    ***REMOVED*** System parameters (first-order)
    system_gain = 0.15
    system_lag = 0.85

    for day in range(duration_days):
        error = setpoint - current_output

        ***REMOVED*** Relay with hysteresis
        if error > hysteresis:
            relay_state = 1
        elif error < -hysteresis:
            relay_state = -1
        ***REMOVED*** else: maintain previous state

        control_signal = relay_state * relay_amplitude

        ***REMOVED*** System response
        output_change = system_gain * control_signal
        current_output = system_lag * current_output + (1 - system_lag) * (current_output + output_change)
        current_output += np.random.normal(0, 0.005)

        time.append(day)
        output.append(current_output)
        control_signals.append(control_signal)

    ***REMOVED*** Analyze last 30 days for steady oscillation
    steady_output = output[-30:]
    steady_time = time[-30:]

    ***REMOVED*** Find peaks and troughs
    peaks = []
    troughs = []

    for i in range(1, len(steady_output) - 1):
        if steady_output[i] > steady_output[i-1] and steady_output[i] > steady_output[i+1]:
            peaks.append((steady_time[i], steady_output[i]))
        if steady_output[i] < steady_output[i-1] and steady_output[i] < steady_output[i+1]:
            troughs.append((steady_time[i], steady_output[i]))

    ***REMOVED*** Calculate ultimate period
    if len(peaks) >= 2:
        peak_times = [t for t, _ in peaks]
        Pu = np.mean([peak_times[i+1] - peak_times[i] for i in range(len(peak_times)-1)])
    else:
        Pu = None

    ***REMOVED*** Calculate ultimate gain using describing function method
    if peaks and troughs:
        a = np.mean([val for _, val in peaks]) - np.mean([val for _, val in troughs])  ***REMOVED*** Oscillation amplitude
        d = relay_amplitude  ***REMOVED*** Relay amplitude

        ***REMOVED*** Describing function for relay
        Ku = (4 * d) / (np.pi * a)
    else:
        Ku = None

    return time, output, control_signals, Ku, Pu

***REMOVED*** Run relay feedback test
time, output, control, Ku, Pu = relay_feedback_test()

print(f"\n=== Relay Feedback Test Results ===")
if Ku and Pu:
    print(f"Ultimate Gain (Ku): {Ku:.2f}")
    print(f"Ultimate Period (Pu): {Pu:.2f} days")

    ***REMOVED*** Calculate PID gains
    Kp_relay = 0.6 * Ku
    Ki_relay = 1.2 * Ku / Pu
    Kd_relay = 0.075 * Ku * Pu

    print(f"\n=== Auto-Tuned PID Gains (Relay Method) ===")
    print(f"Kp = {Kp_relay:.2f}")
    print(f"Ki = {Ki_relay:.2f}")
    print(f"Kd = {Kd_relay:.2f}")
else:
    print("Error: Could not identify oscillation parameters")

***REMOVED*** Plot relay feedback response
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))

ax1.plot(time, output, 'b-', linewidth=2, label='System Output')
ax1.axhline(y=0.75, color='r', linestyle='--', label='Setpoint')
ax1.set_xlabel('Time (days)')
ax1.set_ylabel('Utilization')
ax1.set_title('Relay Feedback Test: Output')
ax1.legend()
ax1.grid(True, alpha=0.3)

ax2.plot(time, control, 'orange', linewidth=2, label='Relay Control')
ax2.set_xlabel('Time (days)')
ax2.set_ylabel('Control Signal')
ax2.set_title('Relay Feedback Test: Control Signal')
ax2.legend()
ax2.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('backend/data/relay_feedback_tuning.png', dpi=150)
print("\n✓ Plot saved to backend/data/relay_feedback_tuning.png")
```

**Advantages:**

- ✅ Fully automated (no manual Kp sweeping)
- ✅ Fast convergence to limit cycle
- ✅ Works well for nonlinear systems
- ✅ Can run in background during normal operations

**Implementation Notes:**

- Use **hysteresis** (deadband) to prevent control chatter
- Run test during **low-stakes periods** (not during crisis)
- Requires 30-60 days for reliable Pu measurement

---

***REMOVED******REMOVED******REMOVED*** Method 4: Simulation-Based Optimization

**Best for:** Offline tuning using historical data

**Theory:**

Use **optimization algorithms** (e.g., gradient descent, genetic algorithms) to minimize a performance cost function:

```
J = ∫[q·e²(t) + r·u²(t)]dt

Where:
  e(t) = tracking error
  u(t) = control effort
  q, r = weighting factors (penalize error vs control aggression)
```

**Procedure:**

```python
***REMOVED*** File: backend/scripts/tune_pid_optimization.py

import numpy as np
from scipy.optimize import minimize, differential_evolution
import matplotlib.pyplot as plt

def cost_function(
    gains: tuple[float, float, float],
    setpoint: float,
    historical_data: list[float],
    disturbances: list[float],
    q: float = 1.0,  ***REMOVED*** Error weight
    r: float = 0.1,  ***REMOVED*** Control effort weight
) -> float:
    """
    Calculate performance cost for given PID gains.

    Cost = q·ISE + r·TVu

    Where:
      ISE = Integral Squared Error
      TVu = Total Variation of control signal (penalizes aggressive control)
    """
    Kp, Ki, Kd = gains

    ***REMOVED*** Simulate closed-loop with these gains
    integral = 0.0
    previous_error = 0.0
    previous_control = 0.0

    errors = []
    controls = []

    current_value = historical_data[0]

    for i, disturbance in enumerate(disturbances):
        error = setpoint - current_value

        ***REMOVED*** PID calculation
        integral += error
        integral = np.clip(integral, -5.0, 5.0)
        derivative = error - previous_error

        control = Kp * error + Ki * integral + Kd * derivative
        control = np.clip(control, -0.2, 0.2)

        ***REMOVED*** Simulate system
        current_value += 0.15 * control + disturbance
        current_value += np.random.normal(0, 0.005)

        errors.append(error)
        controls.append(control)

        previous_error = error
        previous_control = control

    ***REMOVED*** Calculate cost components
    ISE = sum(e**2 for e in errors)  ***REMOVED*** Integral Squared Error
    TVu = sum(abs(controls[i] - controls[i-1]) for i in range(1, len(controls)))  ***REMOVED*** Total Variation

    cost = q * ISE + r * TVu

    return cost

***REMOVED*** Generate synthetic historical data with disturbances
np.random.seed(42)
num_days = 90
historical_utilization = np.random.uniform(0.70, 0.80, num_days)
disturbances = np.random.normal(0, 0.02, num_days)

***REMOVED*** Add some structured disturbances (absences, emergencies)
disturbances[30] = -0.10  ***REMOVED*** Large absence
disturbances[60] = -0.08  ***REMOVED*** Emergency

***REMOVED*** Optimize gains
print("=== Optimization-Based Tuning ===")
print("Searching for optimal PID gains...\n")

***REMOVED*** Method 1: Gradient-based optimization (fast, local optima)
initial_guess = [10.0, 0.5, 2.0]
bounds = [(0, 30), (0, 5), (0, 10)]

result_gradient = minimize(
    fun=lambda x: cost_function(x, 0.75, historical_utilization, disturbances),
    x0=initial_guess,
    bounds=bounds,
    method='L-BFGS-B'
)

Kp_opt_grad, Ki_opt_grad, Kd_opt_grad = result_gradient.x

print(f"Gradient-Based Optimization:")
print(f"  Kp = {Kp_opt_grad:.2f}")
print(f"  Ki = {Ki_opt_grad:.2f}")
print(f"  Kd = {Kd_opt_grad:.2f}")
print(f"  Cost = {result_gradient.fun:.4f}\n")

***REMOVED*** Method 2: Global optimization (slow, better coverage)
result_global = differential_evolution(
    func=lambda x: cost_function(x, 0.75, historical_utilization, disturbances),
    bounds=bounds,
    maxiter=50,
    seed=42,
    workers=-1  ***REMOVED*** Use all CPU cores
)

Kp_opt_glob, Ki_opt_glob, Kd_opt_glob = result_global.x

print(f"Global Optimization (Differential Evolution):")
print(f"  Kp = {Kp_opt_glob:.2f}")
print(f"  Ki = {Ki_opt_glob:.2f}")
print(f"  Kd = {Kd_opt_glob:.2f}")
print(f"  Cost = {result_global.fun:.4f}\n")

***REMOVED*** Validate on test data
print("=== Validation ===")

***REMOVED*** Apply optimized gains to controller
from app.resilience.pid_control import PIDControllerBank

bank = PIDControllerBank()
controller = bank.controllers["utilization"]

controller.config.Kp = Kp_opt_glob
controller.config.Ki = Ki_opt_glob
controller.config.Kd = Kd_opt_glob

print("✓ Optimized gains applied to controller")

***REMOVED*** Simulate performance with optimized gains
controller.reset()
simulated_output = []
simulated_control = []
current_util = 0.70

for dist in disturbances:
    result = controller.update(current_util)
    current_util += 0.15 * result["control_signal"] + dist
    current_util += np.random.normal(0, 0.005)

    simulated_output.append(current_util)
    simulated_control.append(result["control_signal"])

***REMOVED*** Calculate performance metrics
settling_time = None
for i, val in enumerate(simulated_output):
    if abs(val - 0.75) < 0.02:
        if all(abs(v - 0.75) < 0.02 for v in simulated_output[i:min(i+7, len(simulated_output))]):
            settling_time = i
            break

overshoot = max(simulated_output) - 0.75 if max(simulated_output) > 0.75 else 0
steady_state_error = abs(simulated_output[-1] - 0.75)
ise = sum((v - 0.75)**2 for v in simulated_output)

print(f"\nPerformance Metrics:")
print(f"  Settling Time: {settling_time} days")
print(f"  Overshoot: {overshoot:.4f} ({overshoot/0.75*100:.1f}%)")
print(f"  Steady-State Error: {steady_state_error:.4f}")
print(f"  ISE: {ise:.4f}")

***REMOVED*** Plot results
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))

ax1.plot(simulated_output, 'b-', linewidth=2, label='Utilization')
ax1.axhline(y=0.75, color='r', linestyle='--', label='Setpoint')
ax1.axhline(y=0.77, color='g', linestyle=':', alpha=0.5, label='±2% band')
ax1.axhline(y=0.73, color='g', linestyle=':', alpha=0.5)

***REMOVED*** Mark disturbances
ax1.axvline(x=30, color='orange', linestyle=':', alpha=0.7, label='Disturbances')
ax1.axvline(x=60, color='orange', linestyle=':', alpha=0.7)

ax1.set_xlabel('Time (days)')
ax1.set_ylabel('Utilization')
ax1.set_title('PID Response with Optimized Gains')
ax1.legend()
ax1.grid(True, alpha=0.3)

ax2.plot(simulated_control, 'orange', linewidth=2, label='Control Signal')
ax2.set_xlabel('Time (days)')
ax2.set_ylabel('Control Signal')
ax2.set_title('Control Effort')
ax2.legend()
ax2.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('backend/data/pid_optimized_tuning.png', dpi=150)
print("\n✓ Plot saved to backend/data/pid_optimized_tuning.png")
```

**Cost Function Weighting:**

| Application | q (Error Weight) | r (Control Weight) | Behavior |
|-------------|------------------|-------------------|----------|
| **Safety-Critical** | 10.0 | 0.1 | Tight tracking, aggressive |
| **Balanced** | 1.0 | 0.1 | Moderate tracking, smooth |
| **Comfort-Priority** | 0.5 | 0.5 | Loose tracking, gentle |

**Advantages:**

- ✅ Optimal for specific cost function
- ✅ Can incorporate real disturbance patterns
- ✅ Works offline (no production disruption)
- ✅ Global optimization explores entire parameter space

**Limitations:**

- ⚠️ Requires good system model
- ⚠️ Optimized for historical data (may not generalize)
- ⚠️ Computationally expensive for global methods

---

***REMOVED******REMOVED******REMOVED*** Anti-Windup Strategies

**Problem:** Integral term accumulates unbounded error during saturation, causing overshoot.

***REMOVED******REMOVED******REMOVED******REMOVED*** Strategy 1: Integral Clamping (Simple)

```python
***REMOVED*** In PIDState.update() method

***REMOVED*** Integral with clamping
self.integral += error * dt
self.integral = np.clip(
    self.integral,
    self.config.integral_limits[0],  ***REMOVED*** -5.0
    self.config.integral_limits[1]   ***REMOVED*** +5.0
)
I = self.config.Ki * self.integral
```

**Recommended Limits:**

| Controller | integral_max | integral_min | Reasoning |
|------------|--------------|--------------|-----------|
| **Utilization** | 5.0 | -5.0 | ~10 cycles at max error |
| **Workload** | 3.0 | -3.0 | Less critical |
| **Coverage** | 10.0 | -10.0 | May have persistent gaps during crises |

***REMOVED******REMOVED******REMOVED******REMOVED*** Strategy 2: Conditional Integration

```python
***REMOVED*** Only integrate when NOT saturated

P = self.config.Kp * error
D = self.config.Kd * (error - self.previous_error) / dt

***REMOVED*** Tentative control without integral
tentative_control = P + D

***REMOVED*** Only integrate if we're not saturated
if self.config.output_limits[0] < tentative_control < self.config.output_limits[1]:
    self.integral += error * dt
    self.integral = np.clip(self.integral, self.config.integral_limits[0], self.config.integral_limits[1])

I = self.config.Ki * self.integral
control_signal = P + I + D
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Strategy 3: Back-Calculation

```python
***REMOVED*** Feed excess saturation back to reduce integral

***REMOVED*** Calculate raw control
raw_control = P + I + D

***REMOVED*** Apply output limits
control_signal = np.clip(raw_control, self.config.output_limits[0], self.config.output_limits[1])

***REMOVED*** Back-calculation anti-windup
if raw_control != control_signal:
    excess = raw_control - control_signal
    Kt = 1.0 / self.config.Ki  ***REMOVED*** Anti-windup gain
    self.integral -= Kt * excess * dt
```

**When to Use:**

- **Clamping:** Default choice (simple, effective)
- **Conditional Integration:** When saturation is frequent
- **Back-Calculation:** Best performance, more complex

---

***REMOVED******REMOVED******REMOVED*** Gain Scheduling for Defense Levels

Adapt PID gains based on system state (resilience defense level):

```python
***REMOVED*** File: backend/app/resilience/pid_gain_schedule.py

from enum import Enum

class DefenseLevel(str, Enum):
    GREEN = "green"      ***REMOVED*** Normal
    YELLOW = "yellow"    ***REMOVED*** Elevated
    ORANGE = "orange"    ***REMOVED*** High
    RED = "red"          ***REMOVED*** Critical

class PIDGainSchedule:
    """Gain scheduling based on system defense level."""

    GAIN_SCHEDULES = {
        DefenseLevel.GREEN: {
            "utilization": {"Kp": 10.0, "Ki": 0.5, "Kd": 2.0},
            "workload": {"Kp": 5.0, "Ki": 0.3, "Kd": 1.0},
            "coverage": {"Kp": 12.0, "Ki": 0.8, "Kd": 1.5},
        },
        DefenseLevel.YELLOW: {
            "utilization": {"Kp": 15.0, "Ki": 1.0, "Kd": 3.0},  ***REMOVED*** More aggressive
            "workload": {"Kp": 7.0, "Ki": 0.5, "Kd": 1.5},
            "coverage": {"Kp": 15.0, "Ki": 1.2, "Kd": 2.0},
        },
        DefenseLevel.ORANGE: {
            "utilization": {"Kp": 20.0, "Ki": 1.5, "Kd": 4.0},  ***REMOVED*** Very aggressive
            "workload": {"Kp": 3.0, "Ki": 0.1, "Kd": 0.5},       ***REMOVED*** Deprioritize
            "coverage": {"Kp": 20.0, "Ki": 2.0, "Kd": 2.5},      ***REMOVED*** Focus on coverage
        },
        DefenseLevel.RED: {
            "utilization": {"Kp": 25.0, "Ki": 2.0, "Kd": 5.0},  ***REMOVED*** Maximum response
            "workload": {"Kp": 0.0, "Ki": 0.0, "Kd": 0.0},       ***REMOVED*** Disable
            "coverage": {"Kp": 30.0, "Ki": 3.0, "Kd": 3.0},      ***REMOVED*** Critical priority
        },
    }

    @classmethod
    def get_gains(cls, defense_level: DefenseLevel, controller_name: str) -> dict:
        """Get PID gains for current defense level."""
        return cls.GAIN_SCHEDULES[defense_level][controller_name]

    @classmethod
    def apply_gain_schedule(cls, pid_bank, defense_level: DefenseLevel):
        """Apply gain schedule to all controllers."""
        for name, controller in pid_bank.controllers.items():
            if name in cls.GAIN_SCHEDULES[defense_level]:
                gains = cls.GAIN_SCHEDULES[defense_level][name]
                controller.config.Kp = gains["Kp"]
                controller.config.Ki = gains["Ki"]
                controller.config.Kd = gains["Kd"]

        print(f"✓ Gain schedule applied for {defense_level.value} level")
```

---

***REMOVED******REMOVED******REMOVED*** PID Tuning Summary Table

| Method | Effort | Accuracy | Robustness | Best For |
|--------|--------|----------|------------|----------|
| **Ziegler-Nichols** | Medium | Good | Moderate | Initial tuning |
| **Cohen-Coon** | Low | Good | Lower | Systems with delay |
| **Relay Feedback** | Low | Very Good | Good | Automated tuning |
| **Simulation-Based** | High | Excellent | Depends | Historical data available |
| **Manual** | High | Variable | Depends | Expert intuition |

**Recommended Workflow:**

1. **Start:** Cohen-Coon or Relay Feedback (fast, automated)
2. **Refine:** Simulation-based optimization on historical data
3. **Validate:** Test in staging with real schedule dynamics
4. **Deploy:** Gradual rollout with monitoring
5. **Adapt:** Enable gain scheduling for defense levels

---

***REMOVED******REMOVED*** Kalman Filter Configuration

***REMOVED******REMOVED******REMOVED*** Overview

Kalman filters provide **optimal state estimation** from noisy measurements. For scheduling:

- **Workload Kalman Filter (Linear):** Estimate true workload from noisy hour logs
- **Schedule Health Extended Kalman Filter (Nonlinear):** Estimate overall system state from multiple indicators

**Mathematical Foundation:**

```
State Prediction:
  x̂[k|k-1] = F·x̂[k-1|k-1] + B·u[k]
  P[k|k-1] = F·P[k-1|k-1]·Fᵀ + Q

Measurement Update:
  K[k] = P[k|k-1]·Hᵀ·(H·P[k|k-1]·Hᵀ + R)⁻¹
  x̂[k|k] = x̂[k|k-1] + K[k]·(z[k] - H·x̂[k|k-1])
  P[k|k] = (I - K[k]·H)·P[k|k-1]

Where:
  x̂ = state estimate
  P = error covariance
  F = state transition matrix
  Q = process noise covariance
  R = measurement noise covariance
  H = measurement matrix
  K = Kalman gain
  z = measurement
```

---

***REMOVED******REMOVED******REMOVED*** Workload Kalman Filter Tuning

**Problem:** Faculty report hours with noise, errors, and delays. Need true workload estimate.

**State Space Model:**

```
State: x = [workload, workload_rate]ᵀ

State equation:
  x[k] = F·x[k-1] + w[k]

  F = [1  Δt]    (workload integrates rate)
      [0   1]

  w ~ N(0, Q)    (process noise)

Measurement equation:
  z[k] = H·x[k] + v[k]

  H = [1  0]     (we measure workload directly)

  v ~ N(0, R)    (measurement noise)
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Step 1: Estimate Process Noise (Q Matrix)

Process noise represents **unpredictable changes** in the system (absences, emergencies, self-swaps).

```python
***REMOVED*** File: backend/scripts/tune_kalman_workload.py

import numpy as np
import matplotlib.pyplot as plt
from scipy import stats

def estimate_process_noise_from_data(
    workload_time_series: list[float],
    dt: float = 1.0,  ***REMOVED*** Days
) -> np.ndarray:
    """
    Estimate process noise covariance Q from historical data.

    Method: Analyze differences in consecutive measurements to
    infer system variability.
    """
    ***REMOVED*** Calculate first differences (rate of change)
    diffs = np.diff(workload_time_series)

    ***REMOVED*** Estimate workload variance
    workload_var = np.var(workload_time_series)

    ***REMOVED*** Estimate rate variance from differences
    rate_var = np.var(diffs) / dt

    ***REMOVED*** Q matrix (diagonal, assuming independent noise)
    Q = np.array([
        [workload_var * 0.01, 0],              ***REMOVED*** Workload process noise (1% of variance)
        [0, rate_var * 0.05]                    ***REMOVED*** Rate process noise (5% of variance)
    ])

    print(f"Estimated Q matrix:")
    print(Q)
    print(f"\nQ diagonal: [{Q[0,0]:.6f}, {Q[1,1]:.6f}]")

    return Q

***REMOVED*** Load historical workload data
***REMOVED*** In production: Query from database
np.random.seed(42)
num_days = 90
true_workload = 0.75 + 0.05 * np.sin(np.linspace(0, 4*np.pi, num_days))  ***REMOVED*** Sinusoidal variation
noise = np.random.normal(0, 0.10, num_days)  ***REMOVED*** 10% noise
measured_workload = true_workload + noise

***REMOVED*** Estimate Q
Q_estimated = estimate_process_noise_from_data(measured_workload)

***REMOVED*** Plot analysis
plt.figure(figsize=(12, 6))
plt.subplot(1, 2, 1)
plt.plot(true_workload, 'g-', label='True Workload', linewidth=2, alpha=0.7)
plt.plot(measured_workload, 'b.', label='Measured (Noisy)', alpha=0.5)
plt.xlabel('Day')
plt.ylabel('Workload')
plt.title('Workload Time Series')
plt.legend()
plt.grid(True, alpha=0.3)

plt.subplot(1, 2, 2)
plt.hist(np.diff(measured_workload), bins=20, alpha=0.7, edgecolor='black')
plt.xlabel('Workload Change (day-to-day)')
plt.ylabel('Frequency')
plt.title('Distribution of Workload Changes')
plt.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('backend/data/kalman_q_estimation.png', dpi=150)
print("✓ Q estimation plot saved")
```

**Tuning Heuristics for Q:**

| Q Value | Effect | When to Use |
|---------|--------|-------------|
| **Small Q** | Trust model more than measurements | Stable, predictable system |
| **Large Q** | Trust measurements more than model | Volatile, unpredictable system |
| **Q[0,0] >> Q[1,1]** | Workload changes rapidly, rate is stable | Many absences, swaps |
| **Q[1,1] >> Q[0,0]** | Workload stable, rate varies | Seasonal patterns |

**Recommended Starting Values:**

```python
Q_conservative = np.array([
    [0.002, 0.0],    ***REMOVED*** σ_workload² = 0.002 (±4.5% std dev)
    [0.0, 0.0005]    ***REMOVED*** σ_rate² = 0.0005
])

Q_aggressive = np.array([
    [0.01, 0.0],     ***REMOVED*** σ_workload² = 0.01 (±10% std dev)
    [0.0, 0.002]     ***REMOVED*** σ_rate² = 0.002
])
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Step 2: Estimate Measurement Noise (R Matrix)

Measurement noise represents **sensor/reporting errors** (self-report bias, rounding, delays).

```python
def estimate_measurement_noise_from_residuals(
    measured_workload: list[float],
    filtered_workload: list[float],
) -> float:
    """
    Estimate measurement noise R from innovation (residuals).

    Innovation = measurement - prediction

    For a well-tuned filter, innovation should be white noise
    with variance ≈ R.
    """
    residuals = np.array(measured_workload) - np.array(filtered_workload)

    R = np.var(residuals)

    print(f"Estimated R (measurement noise variance): {R:.6f}")
    print(f"Measurement noise std dev: {np.sqrt(R):.4f}")

    ***REMOVED*** Check whiteness (should be uncorrelated)
    autocorr = np.correlate(residuals - np.mean(residuals), residuals - np.mean(residuals), mode='full')
    autocorr = autocorr[len(autocorr)//2:]
    autocorr = autocorr / autocorr[0]

    print(f"Residual autocorrelation at lag 1: {autocorr[1]:.3f} (should be ~0)")

    return R

***REMOVED*** For initial estimate, use empirical measurement variance
def estimate_R_from_repeated_measurements(
    repeated_measurements: list[list[float]],
) -> float:
    """
    If you have multiple measurements of the same quantity,
    use variance across measurements.
    """
    ***REMOVED*** Example: Multiple faculty report same shift hours
    variances = [np.var(measurements) for measurements in repeated_measurements]
    R = np.mean(variances)

    return R

***REMOVED*** Quick estimate from data
R_estimated = np.var(measured_workload - true_workload)
print(f"\nEmpirical R estimate: {R_estimated:.6f}")
```

**Recommended Starting Values:**

```python
***REMOVED*** Low-noise sensors (automated time tracking)
R_low_noise = 0.01  ***REMOVED*** σ_measurement = 0.1 (10% error)

***REMOVED*** Medium-noise sensors (self-reported hours)
R_medium_noise = 0.04  ***REMOVED*** σ_measurement = 0.2 (20% error)

***REMOVED*** High-noise sensors (peer estimates, rough logs)
R_high_noise = 0.10  ***REMOVED*** σ_measurement = 0.32 (32% error)
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Step 3: Implement Workload Kalman Filter

```python
***REMOVED*** File: backend/app/resilience/kalman_filters.py

import numpy as np
from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4

@dataclass
class KalmanFilterState:
    """State of a Kalman filter."""

    id: UUID
    name: str

    ***REMOVED*** State estimate: [workload, workload_rate]
    x: np.ndarray = field(default_factory=lambda: np.array([0.75, 0.0]))

    ***REMOVED*** Error covariance
    P: np.ndarray = field(default_factory=lambda: np.eye(2) * 0.1)

    ***REMOVED*** State transition matrix
    F: np.ndarray = field(default_factory=lambda: np.array([[1.0, 1.0], [0.0, 1.0]]))  ***REMOVED*** dt=1 day

    ***REMOVED*** Measurement matrix
    H: np.ndarray = field(default_factory=lambda: np.array([[1.0, 0.0]]))

    ***REMOVED*** Process noise covariance
    Q: np.ndarray = field(default_factory=lambda: np.array([[0.002, 0.0], [0.0, 0.0005]]))

    ***REMOVED*** Measurement noise covariance
    R: float = 0.04  ***REMOVED*** Scalar for single measurement

    ***REMOVED*** History
    estimate_history: list[tuple[datetime, np.ndarray]] = field(default_factory=list)
    measurement_history: list[tuple[datetime, float]] = field(default_factory=list)
    innovation_history: list[tuple[datetime, float]] = field(default_factory=list)

    def predict(self, dt: float = 1.0):
        """
        Prediction step: Propagate state forward in time.

        Args:
            dt: Time step (days)
        """
        ***REMOVED*** Update F with current dt
        self.F[0, 1] = dt

        ***REMOVED*** State prediction
        self.x = self.F @ self.x

        ***REMOVED*** Covariance prediction
        self.P = self.F @ self.P @ self.F.T + self.Q

    def update(self, measurement: float):
        """
        Update step: Correct state estimate with measurement.

        Args:
            measurement: Observed workload value
        """
        ***REMOVED*** Innovation (residual)
        z = np.array([measurement])
        z_pred = self.H @ self.x
        innovation = z - z_pred

        ***REMOVED*** Innovation covariance
        S = self.H @ self.P @ self.H.T + self.R

        ***REMOVED*** Kalman gain
        K = self.P @ self.H.T / S

        ***REMOVED*** State update
        self.x = self.x + K * innovation

        ***REMOVED*** Covariance update (Joseph form for numerical stability)
        I_KH = np.eye(2) - np.outer(K, self.H)
        self.P = I_KH @ self.P @ I_KH.T + np.outer(K, K) * self.R

        ***REMOVED*** Record history
        now = datetime.now()
        self.estimate_history.append((now, self.x.copy()))
        self.measurement_history.append((now, measurement))
        self.innovation_history.append((now, float(innovation)))

    def filter(self, measurement: float, dt: float = 1.0) -> dict:
        """
        Complete Kalman filter cycle: predict + update.

        Returns:
            Dict with filtered estimate and diagnostics
        """
        self.predict(dt)
        self.update(measurement)

        return {
            "workload_estimate": float(self.x[0]),
            "workload_rate_estimate": float(self.x[1]),
            "uncertainty": float(np.sqrt(self.P[0, 0])),
            "innovation": float(self.innovation_history[-1][1]) if self.innovation_history else 0.0,
            "kalman_gain": float(self.P[0, 0] / (self.P[0, 0] + self.R)),  ***REMOVED*** Effective gain on workload
        }

    def get_diagnostics(self) -> dict:
        """Get filter diagnostics for tuning."""
        if len(self.innovation_history) < 10:
            return {"status": "insufficient_data"}

        recent_innovations = [inn for _, inn in self.innovation_history[-20:]]

        ***REMOVED*** Check innovation statistics (should be zero-mean, white noise)
        innovation_mean = np.mean(recent_innovations)
        innovation_std = np.std(recent_innovations)

        ***REMOVED*** Normalized Innovation Squared (NIS) test
        ***REMOVED*** Should be chi-squared distributed with 1 DOF
        nis = [inn**2 / (self.P[0, 0] + self.R) for inn in recent_innovations]
        nis_mean = np.mean(nis)

        ***REMOVED*** For chi-squared(1), mean should be 1.0
        is_well_tuned = 0.5 < nis_mean < 1.5

        return {
            "innovation_mean": innovation_mean,
            "innovation_std": innovation_std,
            "nis_mean": nis_mean,
            "is_well_tuned": is_well_tuned,
            "tuning_hint": (
                "Q too large (trust measurements more)" if nis_mean < 0.5
                else "Q too small (trust model more)" if nis_mean > 1.5
                else "Tuning looks good"
            ),
        }

class KalmanFilterBank:
    """Bank of Kalman filters for scheduling system."""

    def __init__(self):
        self.filters: dict[str, KalmanFilterState] = {}
        self._initialize_default_filters()

    def _initialize_default_filters(self):
        """Initialize Kalman filters for workload estimation."""
        self.filters["workload"] = KalmanFilterState(
            id=uuid4(),
            name="workload_kalman",
            x=np.array([0.75, 0.0]),  ***REMOVED*** Initial: 75% utilization, zero rate
            P=np.eye(2) * 0.1,
            Q=np.array([[0.002, 0.0], [0.0, 0.0005]]),
            R=0.04,
        )

    def update(self, filter_name: str, measurement: float, dt: float = 1.0) -> dict:
        """Update a Kalman filter with new measurement."""
        kf = self.filters.get(filter_name)
        if not kf:
            raise ValueError(f"Unknown filter: {filter_name}")

        return kf.filter(measurement, dt)
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Step 4: Tune Q and R Iteratively

```python
***REMOVED*** File: backend/scripts/tune_kalman_qr_iteration.py

from app.resilience.kalman_filters import KalmanFilterBank
import numpy as np
import matplotlib.pyplot as plt

***REMOVED*** Load test data
measured_workload = np.load('backend/data/historical_workload.npy')  ***REMOVED*** Example
true_workload = np.load('backend/data/true_workload.npy')  ***REMOVED*** Ground truth (if available)

***REMOVED*** Test multiple Q/R combinations
Q_candidates = [0.001, 0.002, 0.005, 0.01]
R_candidates = [0.02, 0.04, 0.08, 0.10]

results = {}

for Q_val in Q_candidates:
    for R_val in R_candidates:
        ***REMOVED*** Create filter with these params
        kf_bank = KalmanFilterBank()
        kf = kf_bank.filters["workload"]

        kf.Q = np.array([[Q_val, 0.0], [0.0, Q_val * 0.25]])
        kf.R = R_val
        kf.x = np.array([measured_workload[0], 0.0])
        kf.P = np.eye(2) * 0.1

        ***REMOVED*** Run filter
        estimates = []
        innovations = []

        for i, meas in enumerate(measured_workload):
            result = kf.filter(meas, dt=1.0)
            estimates.append(result["workload_estimate"])
            innovations.append(result["innovation"])

        ***REMOVED*** Calculate performance
        mse = np.mean((np.array(estimates) - true_workload)**2)
        innovation_std = np.std(innovations)

        ***REMOVED*** Normalized Innovation Squared test
        nis = np.mean([(inn**2) / (kf.P[0,0] + kf.R) for inn in innovations])

        results[(Q_val, R_val)] = {
            "mse": mse,
            "innovation_std": innovation_std,
            "nis": nis,
            "estimates": estimates,
        }

        print(f"Q={Q_val:.4f}, R={R_val:.2f}: MSE={mse:.6f}, NIS={nis:.3f}")

***REMOVED*** Find best parameters
best_params = min(results.items(), key=lambda x: x[1]["mse"])
Q_best, R_best = best_params[0]
print(f"\n=== Best Parameters ===")
print(f"Q = {Q_best:.4f}")
print(f"R = {R_best:.2f}")
print(f"MSE = {best_params[1]['mse']:.6f}")

***REMOVED*** Plot best result
best_estimates = best_params[1]["estimates"]

plt.figure(figsize=(12, 6))
plt.plot(true_workload, 'g-', label='True Workload', linewidth=2)
plt.plot(measured_workload, 'b.', label='Measured (Noisy)', alpha=0.5)
plt.plot(best_estimates, 'r-', label=f'Kalman Estimate (Q={Q_best}, R={R_best})', linewidth=2)
plt.xlabel('Day')
plt.ylabel('Workload')
plt.title('Kalman Filter Performance')
plt.legend()
plt.grid(True, alpha=0.3)
plt.savefig('backend/data/kalman_best_tuning.png', dpi=150)
print("✓ Best tuning plot saved")
```

**Tuning Guidelines:**

1. **Start conservative:** Q=0.002, R=0.04
2. **Check NIS:** Should be near 1.0
   - If NIS < 0.5: Increase Q (trust measurements more)
   - If NIS > 1.5: Decrease Q (trust model more)
3. **Validate on test data:** Use different time period than tuning data
4. **Monitor innovation:** Should be white noise (uncorrelated)

---

***REMOVED******REMOVED******REMOVED*** Adaptive Kalman Filtering

For time-varying noise characteristics, use **adaptive Kalman filters** that estimate Q and R online.

***REMOVED******REMOVED******REMOVED******REMOVED*** Innovation-Based Adaptive Filter

```python
***REMOVED*** File: backend/app/resilience/adaptive_kalman.py

import numpy as np
from app.resilience.kalman_filters import KalmanFilterState

class AdaptiveKalmanFilter(KalmanFilterState):
    """Kalman filter with online Q/R adaptation."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        ***REMOVED*** Adaptive parameters
        self.adaptation_window = 20  ***REMOVED*** Use last 20 measurements
        self.min_R = 0.01
        self.max_R = 0.20
        self.min_Q = 0.0001
        self.max_Q = 0.05

    def adapt_R(self):
        """
        Adapt measurement noise based on recent innovation.

        Method: Innovation-based adaptive estimation
        R̂ = (1/N)·Σ(innovation²)
        """
        if len(self.innovation_history) < self.adaptation_window:
            return

        recent_innovations = [inn for _, inn in self.innovation_history[-self.adaptation_window:]]

        ***REMOVED*** Estimate R from innovation variance
        R_new = np.var(recent_innovations)

        ***REMOVED*** Smooth update
        alpha = 0.1  ***REMOVED*** Learning rate
        self.R = (1 - alpha) * self.R + alpha * R_new

        ***REMOVED*** Clamp
        self.R = np.clip(self.R, self.min_R, self.max_R)

    def adapt_Q(self):
        """
        Adapt process noise based on prediction error.

        Method: Residual-based adaptive estimation
        """
        if len(self.estimate_history) < self.adaptation_window + 1:
            return

        ***REMOVED*** Get recent state estimates
        recent_states = [x for _, x in self.estimate_history[-self.adaptation_window-1:]]

        ***REMOVED*** Calculate one-step prediction errors
        prediction_errors = []
        for i in range(1, len(recent_states)):
            predicted = self.F @ recent_states[i-1]
            actual = recent_states[i]
            error = actual - predicted
            prediction_errors.append(error)

        ***REMOVED*** Estimate Q from prediction error covariance
        if prediction_errors:
            Q_new = np.cov(np.array(prediction_errors).T)

            ***REMOVED*** Smooth update
            alpha = 0.05
            self.Q = (1 - alpha) * self.Q + alpha * Q_new

            ***REMOVED*** Clamp diagonal elements
            self.Q[0, 0] = np.clip(self.Q[0, 0], self.min_Q, self.max_Q)
            self.Q[1, 1] = np.clip(self.Q[1, 1], self.min_Q * 0.25, self.max_Q * 0.25)

    def filter(self, measurement: float, dt: float = 1.0) -> dict:
        """Filter with adaptation."""
        ***REMOVED*** Standard Kalman update
        result = super().filter(measurement, dt)

        ***REMOVED*** Adapt parameters
        self.adapt_R()
        self.adapt_Q()

        result["R_adapted"] = float(self.R)
        result["Q_adapted"] = self.Q.tolist()

        return result
```

**When to Use Adaptive Kalman:**

- ✅ Noise characteristics change over time (e.g., more errors during busy periods)
- ✅ Unknown noise levels (Q/R hard to estimate a priori)
- ✅ Long-running systems with evolving dynamics

**Caveats:**

- ⚠️ Requires sufficient data for reliable adaptation (>20 samples)
- ⚠️ Can diverge if adaptation rate is too high
- ⚠️ More complex to tune and debug

---

***REMOVED******REMOVED******REMOVED*** Extended Kalman Filter for Nonlinear Systems

For **schedule health estimation** from multiple nonlinear indicators (coverage, utilization, compliance):

```python
***REMOVED*** File: backend/app/resilience/extended_kalman.py

import numpy as np
from dataclasses import dataclass, field
from uuid import UUID, uuid4

@dataclass
class ExtendedKalmanFilterState:
    """Extended Kalman Filter for nonlinear systems."""

    id: UUID
    name: str

    ***REMOVED*** State: [coverage, utilization, workload_balance]
    x: np.ndarray = field(default_factory=lambda: np.array([0.95, 0.75, 0.15]))

    ***REMOVED*** Error covariance
    P: np.ndarray = field(default_factory=lambda: np.eye(3) * 0.01)

    ***REMOVED*** Process noise
    Q: np.ndarray = field(default_factory=lambda: np.diag([0.001, 0.002, 0.001]))

    ***REMOVED*** Measurement noise
    R: np.ndarray = field(default_factory=lambda: np.diag([0.02, 0.04, 0.01]))

    def f(self, x: np.ndarray, dt: float) -> np.ndarray:
        """
        Nonlinear state transition function.

        Model: Coverage and utilization interact (nonlinear coupling)
        """
        coverage, utilization, workload = x

        ***REMOVED*** Coverage decays if utilization too high (burnout)
        coverage_decay = 0.01 * max(0, utilization - 0.80)

        ***REMOVED*** Utilization increases if workload unbalanced (some faculty overloaded)
        util_increase = 0.005 * max(0, workload - 0.20)

        ***REMOVED*** Nonlinear state evolution
        x_new = np.array([
            coverage - coverage_decay * dt,
            utilization + util_increase * dt,
            workload * 0.99,  ***REMOVED*** Workload slowly equilibrates
        ])

        return x_new

    def F_jacobian(self, x: np.ndarray, dt: float) -> np.ndarray:
        """
        Jacobian of state transition function.

        F = ∂f/∂x
        """
        coverage, utilization, workload = x

        ***REMOVED*** Partial derivatives
        F = np.array([
            [1.0, -0.01 * dt if utilization > 0.80 else 0.0, 0.0],
            [0.0, 1.0, 0.005 * dt if workload > 0.20 else 0.0],
            [0.0, 0.0, 0.99],
        ])

        return F

    def h(self, x: np.ndarray) -> np.ndarray:
        """
        Nonlinear measurement function.

        We measure all states directly (linear in this case),
        but could add nonlinear transformations.
        """
        return x  ***REMOVED*** Direct measurement

    def H_jacobian(self, x: np.ndarray) -> np.ndarray:
        """
        Jacobian of measurement function.

        H = ∂h/∂x
        """
        return np.eye(3)  ***REMOVED*** Linear measurement

    def predict(self, dt: float = 1.0):
        """EKF prediction step."""
        ***REMOVED*** Nonlinear state prediction
        self.x = self.f(self.x, dt)

        ***REMOVED*** Linearized covariance prediction
        F = self.F_jacobian(self.x, dt)
        self.P = F @ self.P @ F.T + self.Q

    def update(self, measurement: np.ndarray):
        """EKF update step."""
        ***REMOVED*** Predicted measurement
        z_pred = self.h(self.x)

        ***REMOVED*** Innovation
        innovation = measurement - z_pred

        ***REMOVED*** Linearized measurement
        H = self.H_jacobian(self.x)

        ***REMOVED*** Innovation covariance
        S = H @ self.P @ H.T + self.R

        ***REMOVED*** Kalman gain
        K = self.P @ H.T @ np.linalg.inv(S)

        ***REMOVED*** State update
        self.x = self.x + K @ innovation

        ***REMOVED*** Covariance update
        I_KH = np.eye(3) - K @ H
        self.P = I_KH @ self.P @ I_KH.T + K @ self.R @ K.T

    def filter(self, measurement: np.ndarray, dt: float = 1.0) -> dict:
        """Complete EKF cycle."""
        self.predict(dt)
        self.update(measurement)

        return {
            "coverage_estimate": float(self.x[0]),
            "utilization_estimate": float(self.x[1]),
            "workload_balance_estimate": float(self.x[2]),
            "uncertainty": np.sqrt(np.diag(self.P)).tolist(),
        }
```

**EKF Tuning:**

1. **Start with linear Kalman:** Tune Q/R for linear version first
2. **Add nonlinearity gradually:** Start with weak coupling
3. **Validate Jacobians:** Check derivatives numerically
4. **Monitor linearization error:** EKF assumes weak nonlinearity

---

***REMOVED******REMOVED*** Model Predictive Control Tuning

*(Continued in next part due to length...)*

---

**Word Count:** ~8,500 words (Part 1 of 2)

**To be continued:** MPC Tuning, System Identification, Integration Testing, and Troubleshooting sections will follow.

***REMOVED******REMOVED*** Model Predictive Control Tuning

***REMOVED******REMOVED******REMOVED*** Overview

Model Predictive Control (MPC) generates **optimal multi-week schedules** by solving a constrained optimization problem at each time step.

**Control Law:**

```
min  Σ[t=0 to N-1] { q_c·(coverage[t] - 0.95)² 
                     + q_u·(utilization[t] - 0.75)²
                     + q_w·workload_variance[t]
                     + q_p·preference_mismatch[t] }

subject to:
  • ACGME duty hour limits
  • Faculty availability constraints
  • Supervision ratio requirements
  • Block coverage requirements
  • Continuity constraints

Where:
  N = prediction horizon (e.g., 28 days)
  M = control horizon (e.g., 14 days)
  q_c, q_u, q_w, q_p = objective weights
```

---

***REMOVED******REMOVED******REMOVED*** Tuning Parameter 1: Prediction Horizon (N)

**Definition:** How far ahead MPC plans (in days or blocks).

***REMOVED******REMOVED******REMOVED******REMOVED*** Selection Criteria

```python
***REMOVED*** File: backend/scripts/tune_mpc_horizon.py

def analyze_prediction_horizon_tradeoffs():
    """Analyze computational cost vs performance for different horizons."""

    horizons = [7, 14, 21, 28, 35, 42]  ***REMOVED*** Days
    results = {}

    for N in horizons:
        ***REMOVED*** Measure computational cost
        import time
        start = time.time()

        ***REMOVED*** Simulate MPC solve (placeholder)
        ***REMOVED*** In practice: call actual MPC solver
        num_decision_vars = N * num_faculty * num_rotations
        num_constraints = N * (num_acgme_rules + num_coverage_req)

        ***REMOVED*** Approximate solve time (MILP is NP-hard)
        ***REMOVED*** Empirical formula: time ∝ (decision_vars)^1.5
        solve_time_estimate = 0.1 * (num_decision_vars / 100) ** 1.5

        elapsed = time.time() - start

        ***REMOVED*** Performance metrics
        ***REMOVED*** Longer horizon = better anticipation of future constraints
        anticipation_benefit = min(1.0, N / 28.0)  ***REMOVED*** Saturates at 28 days

        ***REMOVED*** Longer horizon = more uncertainty (forecast degrades)
        forecast_uncertainty = (N / 7) ** 0.5 * 0.05  ***REMOVED*** Grows with sqrt(N)

        results[N] = {
            "solve_time_estimate_sec": solve_time_estimate,
            "anticipation_benefit": anticipation_benefit,
            "forecast_uncertainty": forecast_uncertainty,
            "decision_vars": num_decision_vars,
            "constraints": num_constraints,
        }

        print(f"N={N:2d} days: solve_time~{solve_time_estimate:.2f}s, "
              f"benefit={anticipation_benefit:.2f}, uncertainty={forecast_uncertainty:.3f}")

    ***REMOVED*** Recommend optimal horizon
    ***REMOVED*** Trade-off: maximize benefit / (solve_time * uncertainty)
    scores = {N: r["anticipation_benefit"] / (r["solve_time_estimate_sec"] * (1 + r["forecast_uncertainty"]))
              for N, r in results.items()}

    best_N = max(scores, key=scores.get)

    print(f"\n=== Recommended Prediction Horizon ===")
    print(f"N = {best_N} days")
    print(f"Score: {scores[best_N]:.3f}")

    return best_N

***REMOVED*** Typical values
num_faculty = 30
num_rotations = 10
num_acgme_rules = 5
num_coverage_req = 15

optimal_N = analyze_prediction_horizon_tradeoffs()
```

**Recommended Values:**

| Context | Prediction Horizon (N) | Rationale |
|---------|----------------------|-----------|
| **Daily MPC** | 14 days (2 weeks) | Balance responsiveness vs computation |
| **Weekly MPC** | 28 days (4 weeks) | ACGME 4-week averaging window |
| **Monthly MPC** | 56 days (8 weeks) | Long-term planning (e.g., vacation scheduling) |

**Key Insight:** **Receding horizon** strategy—plan N days ahead, execute M days, then re-plan. Longer N improves anticipation but increases computation and forecast error.

---

***REMOVED******REMOVED******REMOVED*** Tuning Parameter 2: Control Horizon (M)

**Definition:** How many days of the plan are "committed" before re-planning.

***REMOVED******REMOVED******REMOVED******REMOVED*** Selection Criteria

```python
def analyze_control_horizon_tradeoffs():
    """Determine optimal control horizon relative to prediction horizon."""

    N = 28  ***REMOVED*** Prediction horizon (fixed)
    control_horizons = [1, 3, 7, 14, 21, 28]

    for M in control_horizons:
        ***REMOVED*** Metrics
        replanning_frequency = 1.0 / M  ***REMOVED*** How often we re-plan
        commitment_depth = M / N  ***REMOVED*** Fraction of plan executed before revision

        ***REMOVED*** Trade-offs
        adaptability = 1.0 - commitment_depth  ***REMOVED*** Ability to react to changes
        stability = commitment_depth  ***REMOVED*** Schedule consistency

        ***REMOVED*** Computational cost (proportional to replanning frequency)
        annual_solves = 365 / M

        print(f"M={M:2d} days: adaptability={adaptability:.2f}, stability={stability:.2f}, "
              f"annual_solves={annual_solves:.0f}")

    print(f"\n=== Recommendation ===")
    print(f"For N={N}: Use M={N//2} (half of prediction horizon)")
    print(f"This balances adaptability and stability.")

analyze_control_horizon_tradeoffs()
```

**Recommended Ratio:**

```
M = N / 2

Example: If N=28 days, use M=14 days
```

**Rationale:**
- **M too small (<< N):** Excessive re-planning, schedule instability
- **M too large (= N):** No benefit from receding horizon
- **M = N/2:** Sweet spot for most applications

---

***REMOVED******REMOVED******REMOVED*** Tuning Parameter 3: Objective Weights (q_c, q_u, q_w, q_p)

**Problem:** How to balance competing objectives?

```
Objective = q_c·coverage_error + q_u·utilization_error + q_w·workload_variance + q_p·preference_mismatch
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Method: Hierarchical Weighting

```python
***REMOVED*** File: backend/app/scheduling/mpc_weights.py

from dataclasses import dataclass

@dataclass
class MPCWeights:
    """Objective weights for MPC scheduler."""

    ***REMOVED*** Critical constraints (must be satisfied)
    coverage_weight: float = 100.0       ***REMOVED*** HIGHEST priority
    acgme_compliance_weight: float = 100.0

    ***REMOVED*** Important objectives (strong preference)
    utilization_weight: float = 10.0
    supervision_ratio_weight: float = 10.0

    ***REMOVED*** Desirable objectives (nice-to-have)
    workload_balance_weight: float = 1.0
    preference_match_weight: float = 0.5

    ***REMOVED*** Soft constraints (aspirational)
    continuity_weight: float = 0.1
    fairness_weight: float = 0.1

    def scale_by_defense_level(self, level: str) -> "MPCWeights":
        """Adjust weights based on resilience defense level."""
        if level == "GREEN":
            return self  ***REMOVED*** Use defaults

        elif level == "YELLOW":
            ***REMOVED*** Increase coverage priority
            return MPCWeights(
                coverage_weight=150.0,
                acgme_compliance_weight=100.0,
                utilization_weight=15.0,
                supervision_ratio_weight=12.0,
                workload_balance_weight=0.5,  ***REMOVED*** Deprioritize
                preference_match_weight=0.2,
                continuity_weight=0.05,
                fairness_weight=0.05,
            )

        elif level == "ORANGE":
            ***REMOVED*** Focus on coverage and compliance
            return MPCWeights(
                coverage_weight=200.0,
                acgme_compliance_weight=150.0,
                utilization_weight=20.0,
                supervision_ratio_weight=15.0,
                workload_balance_weight=0.1,  ***REMOVED*** Nearly ignore
                preference_match_weight=0.0,  ***REMOVED*** Ignore
                continuity_weight=0.0,
                fairness_weight=0.0,
            )

        elif level == "RED":
            ***REMOVED*** CRITICAL: Coverage only
            return MPCWeights(
                coverage_weight=500.0,
                acgme_compliance_weight=200.0,
                utilization_weight=10.0,
                supervision_ratio_weight=20.0,
                workload_balance_weight=0.0,
                preference_match_weight=0.0,
                continuity_weight=0.0,
                fairness_weight=0.0,
            )

        return self


***REMOVED*** Usage
weights = MPCWeights()
yellow_weights = weights.scale_by_defense_level("YELLOW")
```

**Tuning Process:**

1. **Start with hierarchical ordering** (coverage >> utilization >> preferences)
2. **Scale ratios by importance** (10x between levels)
3. **Validate on test scenarios:**
   - Coverage shortfall: Should prioritize coverage over preferences
   - Overutilization: Should balance workload
   - Normal ops: Should respect preferences
4. **Iterate based on stakeholder feedback**

***REMOVED******REMOVED******REMOVED******REMOVED*** Empirical Weight Optimization

```python
***REMOVED*** File: backend/scripts/tune_mpc_weights.py

from scipy.optimize import minimize
import numpy as np

def cost_function_for_weight_tuning(
    weights: np.ndarray,
    historical_schedules: list,
    stakeholder_preferences: dict,
) -> float:
    """
    Evaluate MPC performance with given weights.

    Args:
        weights: [q_c, q_u, q_w, q_p]
        historical_schedules: Past schedules with known outcomes
        stakeholder_preferences: Desired priorities

    Returns:
        Cost (lower is better)
    """
    q_c, q_u, q_w, q_p = weights

    ***REMOVED*** Simulate MPC with these weights on historical data
    ***REMOVED*** (In practice: re-solve past schedules with new weights)

    total_cost = 0.0

    for schedule in historical_schedules:
        ***REMOVED*** Calculate objective value
        coverage_error = max(0, 0.95 - schedule["coverage"])
        utilization_error = abs(schedule["utilization"] - 0.75)
        workload_variance = schedule["workload_std"]
        preference_mismatch = 1.0 - schedule["preference_match_rate"]

        objective = (q_c * coverage_error**2 +
                     q_u * utilization_error**2 +
                     q_w * workload_variance**2 +
                     q_p * preference_mismatch**2)

        total_cost += objective

        ***REMOVED*** Penalty for violating stakeholder priorities
        ***REMOVED*** Example: Coverage should always be >90%
        if schedule["coverage"] < 0.90:
            total_cost += 1000.0  ***REMOVED*** Large penalty

    ***REMOVED*** Normalize by number of schedules
    total_cost /= len(historical_schedules)

    return total_cost

***REMOVED*** Optimize weights
initial_weights = np.array([100.0, 10.0, 1.0, 0.5])
bounds = [(10, 500), (1, 50), (0.1, 10), (0, 5)]

result = minimize(
    fun=lambda w: cost_function_for_weight_tuning(w, historical_schedules, preferences),
    x0=initial_weights,
    bounds=bounds,
    method='L-BFGS-B'
)

q_c_opt, q_u_opt, q_w_opt, q_p_opt = result.x

print(f"=== Optimized MPC Weights ===")
print(f"Coverage:    {q_c_opt:.1f}")
print(f"Utilization: {q_u_opt:.1f}")
print(f"Workload:    {q_w_opt:.1f}")
print(f"Preference:  {q_p_opt:.1f}")
```

---

***REMOVED******REMOVED******REMOVED*** Tuning Parameter 4: Constraint Softening

**Problem:** Infeasible schedules when hard constraints conflict.

**Solution:** Soft constraints with penalty terms.

```python
***REMOVED*** File: backend/app/scheduling/mpc_soft_constraints.py

from dataclasses import dataclass

@dataclass
class SoftConstraintConfig:
    """Configuration for soft constraint penalties."""

    ***REMOVED*** Slack variable bounds
    max_coverage_slack: float = 0.05      ***REMOVED*** Allow up to 5% coverage shortfall
    max_preference_violation: float = 1.0  ***REMOVED*** Allow full preference override

    ***REMOVED*** Penalty weights (per unit of violation)
    coverage_slack_penalty: float = 1000.0   ***REMOVED*** Very expensive
    preference_violation_penalty: float = 1.0  ***REMOVED*** Cheap

    ***REMOVED*** Constraint types
    HARD_CONSTRAINTS = [
        "acgme_duty_hours",
        "faculty_availability",
        "supervision_ratios",
    ]

    SOFT_CONSTRAINTS = [
        "coverage_target",      ***REMOVED*** Prefer 95%, tolerate 90%
        "preference_match",     ***REMOVED*** Nice to have
        "workload_balance",     ***REMOVED*** Aspirational
    ]


def formulate_mpc_with_soft_constraints(weights: MPCWeights, soft_config: SoftConstraintConfig):
    """
    Formulate MPC optimization with soft constraints.

    Objective:
      min  Σ{ q_c·(coverage - 0.95 + slack_c)² + penalty_c·slack_c² + ... }

    Constraints:
      coverage >= 0.95 - slack_c          (soft)
      0 <= slack_c <= max_coverage_slack  (slack bounds)

      duty_hours <= 80                     (hard, no slack)
    """
    ***REMOVED*** Pseudo-code (actual implementation uses OR-Tools or similar)

    ***REMOVED*** Decision variables
    ***REMOVED*** x[t,f,r] = 1 if faculty f assigned to rotation r at time t

    ***REMOVED*** Slack variables
    ***REMOVED*** slack_coverage[t] >= 0

    ***REMOVED*** Objective
    objective = sum(
        weights.coverage_weight * (coverage[t] - 0.95 + slack_coverage[t])**2 +
        soft_config.coverage_slack_penalty * slack_coverage[t]**2
        for t in range(N)
    )

    ***REMOVED*** Soft coverage constraint
    ***REMOVED*** coverage[t] = sum(x[t,f,r] for f,r) / num_blocks_to_cover[t]
    ***REMOVED*** coverage[t] >= 0.95 - slack_coverage[t]

    ***REMOVED*** Hard ACGME constraint (no slack)
    ***REMOVED*** sum(hours[t-3:t+1]) <= 80  (4-week rolling window)

    ***REMOVED*** Solve
    ***REMOVED*** solution = solver.solve(objective, constraints)

    return solution
```

**Tuning Soft Constraint Penalties:**

| Constraint | Penalty Weight | Slack Bound | Effect |
|------------|----------------|-------------|--------|
| **Coverage** | 1000 | 0.05 (5%) | Can sacrifice up to 5% coverage, but very expensive |
| **Preference** | 1 | 1.0 (100%) | Can fully override preferences if needed |
| **Workload Balance** | 10 | 0.10 (10%) | Tolerate some imbalance |

**Recommended Approach:**

1. **Start with hard constraints only** (may be infeasible)
2. **Identify frequently violated constraints** (from solver logs)
3. **Soften lowest-priority constraints** (preferences first)
4. **Tune penalties** to balance feasibility vs quality

---

***REMOVED******REMOVED******REMOVED*** MPC Solver Selection

**Options:**

| Solver | Type | Speed | Optimality | Best For |
|--------|------|-------|------------|----------|
| **OR-Tools CP-SAT** | Constraint Programming | Fast | Heuristic | Discrete assignments |
| **Gurobi** | MILP | Medium | Optimal* | Mixed-integer problems |
| **CPLEX** | MILP | Medium | Optimal* | Large-scale LP/MILP |
| **PuLP** | MILP | Slow | Optimal* | Prototyping |

**\*Optimal within time limit**

**Recommended:** OR-Tools CP-SAT for scheduling (fast, handles disjunctions well)

---

***REMOVED******REMOVED******REMOVED*** MPC Tuning Summary

| Parameter | Recommended Range | Tuning Method |
|-----------|------------------|---------------|
| **Prediction Horizon (N)** | 14-28 days | Cost-benefit analysis |
| **Control Horizon (M)** | N/2 | Fixed ratio |
| **Coverage Weight** | 100-500 | Hierarchical + empirical |
| **Utilization Weight** | 10-50 | Relative to coverage |
| **Preference Weight** | 0.5-5 | Stakeholder feedback |
| **Soft Constraint Penalty** | 100-1000 | Feasibility testing |

---

***REMOVED******REMOVED*** System Identification

***REMOVED******REMOVED******REMOVED*** Overview

**System identification** estimates dynamic models from input-output data. For scheduling:

```
Input: Assignment changes, absences, emergencies
Output: Utilization, coverage, workload

Model: Utilization[t+1] = f(Utilization[t], Assignments[t], Disturbances[t])
```

---

***REMOVED******REMOVED******REMOVED*** Method 1: ARX Model Estimation

**AutoRegressive with eXogenous inputs**

```
y[t] = a₁·y[t-1] + a₂·y[t-2] + ... + b₁·u[t-1] + b₂·u[t-2] + ... + e[t]

Where:
  y[t] = output (e.g., utilization)
  u[t] = input (e.g., assignments)
  e[t] = noise
  a, b = parameters to estimate
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Implementation

```python
***REMOVED*** File: backend/scripts/system_identification_arx.py

import numpy as np
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression

def estimate_arx_model(
    output_data: np.ndarray,  ***REMOVED*** Utilization time series
    input_data: np.ndarray,   ***REMOVED*** Assignment changes
    order: tuple[int, int] = (2, 2),  ***REMOVED*** (na, nb) - AR and exog orders
) -> dict:
    """
    Estimate ARX model: y[t] = a1*y[t-1] + a2*y[t-2] + b1*u[t-1] + b2*u[t-2]

    Args:
        output_data: Output measurements (length N)
        input_data: Input measurements (length N)
        order: (na, nb) where na=AR order, nb=exogenous order

    Returns:
        Dict with model parameters and diagnostics
    """
    na, nb = order
    max_lag = max(na, nb)

    ***REMOVED*** Build regression matrix
    N = len(output_data)
    X = []
    y = []

    for t in range(max_lag, N):
        ***REMOVED*** Lagged outputs
        y_lags = [output_data[t - i] for i in range(1, na + 1)]

        ***REMOVED*** Lagged inputs
        u_lags = [input_data[t - i] for i in range(1, nb + 1)]

        X.append(y_lags + u_lags)
        y.append(output_data[t])

    X = np.array(X)
    y = np.array(y)

    ***REMOVED*** Fit linear regression
    model = LinearRegression()
    model.fit(X, y)

    ***REMOVED*** Extract parameters
    a_params = model.coef_[:na]
    b_params = model.coef_[na:]

    ***REMOVED*** Predictions
    y_pred = model.predict(X)
    residuals = y - y_pred

    ***REMOVED*** Diagnostics
    R2 = model.score(X, y)
    MSE = np.mean(residuals**2)
    RMSE = np.sqrt(MSE)

    print(f"=== ARX Model (order {na},{nb}) ===")
    print(f"AR coefficients (a): {a_params}")
    print(f"Exogenous coefficients (b): {b_params}")
    print(f"Intercept: {model.intercept_}")
    print(f"\nModel Performance:")
    print(f"  R² = {R2:.4f}")
    print(f"  RMSE = {RMSE:.4f}")

    ***REMOVED*** Plot residuals
    plt.figure(figsize=(12, 6))

    plt.subplot(2, 1, 1)
    plt.plot(y, 'b-', label='Actual', linewidth=2)
    plt.plot(y_pred, 'r--', label='Predicted', linewidth=2)
    plt.xlabel('Time')
    plt.ylabel('Utilization')
    plt.title(f'ARX Model Fit (R²={R2:.3f})')
    plt.legend()
    plt.grid(True, alpha=0.3)

    plt.subplot(2, 1, 2)
    plt.plot(residuals, 'k-', linewidth=1)
    plt.axhline(y=0, color='r', linestyle='--')
    plt.xlabel('Time')
    plt.ylabel('Residual')
    plt.title('Model Residuals')
    plt.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig('backend/data/arx_model_fit.png', dpi=150)
    print("\n✓ ARX model plot saved")

    return {
        "a_params": a_params,
        "b_params": b_params,
        "intercept": model.intercept_,
        "R2": R2,
        "RMSE": RMSE,
        "model": model,
    }

***REMOVED*** Example usage
***REMOVED*** Load historical data
utilization_data = np.load('backend/data/historical_utilization.npy')
assignment_changes = np.load('backend/data/historical_assignments.npy')

arx_model = estimate_arx_model(utilization_data, assignment_changes, order=(2, 2))
```

**Model Order Selection:**

Use **Akaike Information Criterion (AIC)** to choose order:

```python
def select_arx_order(output_data, input_data, max_order: int = 5):
    """Select ARX order using AIC."""
    from scipy.stats import norm

    results = {}

    for na in range(1, max_order + 1):
        for nb in range(1, max_order + 1):
            model_result = estimate_arx_model(output_data, input_data, order=(na, nb))

            ***REMOVED*** Calculate AIC
            N = len(output_data) - max(na, nb)
            k = na + nb + 1  ***REMOVED*** Number of parameters
            RSS = model_result["RMSE"]**2 * N

            AIC = 2 * k + N * np.log(RSS / N)

            results[(na, nb)] = {
                "AIC": AIC,
                "R2": model_result["R2"],
                "RMSE": model_result["RMSE"],
            }

            print(f"Order ({na},{nb}): AIC={AIC:.2f}, R²={model_result['R2']:.4f}")

    ***REMOVED*** Select best (minimum AIC)
    best_order = min(results, key=lambda x: results[x]["AIC"])

    print(f"\n=== Best Order ===")
    print(f"({best_order[0]}, {best_order[1]})")
    print(f"AIC = {results[best_order]['AIC']:.2f}")

    return best_order
```

---

***REMOVED******REMOVED******REMOVED*** Method 2: Step Response Analysis

**Procedure:**

1. Apply step change to input (e.g., add 10 assignments)
2. Measure output response (utilization over time)
3. Fit first-order plus dead time (FOPDT) model

```python
***REMOVED*** File: backend/scripts/system_identification_step_response.py

def analyze_step_response(
    time: np.ndarray,
    output: np.ndarray,
    step_time: int,
    step_magnitude: float,
    initial_value: float,
) -> dict:
    """
    Analyze step response and extract system parameters.

    Fits FOPDT model: G(s) = K·e^(-θs) / (τs + 1)
    """
    from scipy.optimize import curve_fit

    def fopdt_model(t, K, tau, theta):
        """First-order plus dead time model."""
        return initial_value + K * step_magnitude * np.maximum(0, 1 - np.exp(-(np.maximum(0, t - theta)) / tau))

    ***REMOVED*** Fit model
    popt, pcov = curve_fit(
        fopdt_model,
        time,
        output,
        p0=[1.0, 7.0, 1.0],  ***REMOVED*** Initial guess
        bounds=([0.5, 1.0, 0.0], [2.0, 30.0, 10.0])
    )

    K, tau, theta = popt

    print(f"=== Step Response Analysis ===")
    print(f"Process Gain (K): {K:.3f}")
    print(f"Time Constant (τ): {tau:.2f} days")
    print(f"Dead Time (θ): {theta:.2f} days")
    print(f"\nDynamic Characteristics:")
    print(f"  Rise Time (10-90%): {2.2 * tau:.1f} days")
    print(f"  Settling Time (2%): {4 * tau:.1f} days")

    ***REMOVED*** Plot
    fitted_output = fopdt_model(time, K, tau, theta)

    plt.figure(figsize=(10, 6))
    plt.plot(time, output, 'b-', linewidth=2, label='Measured')
    plt.plot(time, fitted_output, 'r--', linewidth=2, label=f'FOPDT Fit (τ={tau:.1f}, θ={theta:.1f})')
    plt.axvline(x=step_time, color='g', linestyle=':', alpha=0.7, label='Step Applied')
    plt.xlabel('Time (days)')
    plt.ylabel('Utilization')
    plt.title('Step Response Analysis')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.savefig('backend/data/step_response_analysis.png', dpi=150)
    print("\n✓ Step response plot saved")

    return {"K": K, "tau": tau, "theta": theta}
```

---

***REMOVED******REMOVED******REMOVED*** Method 3: Frequency Response Analysis

For systems with oscillatory behavior:

```python
***REMOVED*** File: backend/scripts/system_identification_frequency.py

import numpy as np
from scipy import signal
import matplotlib.pyplot as plt

def frequency_response_analysis(
    input_data: np.ndarray,
    output_data: np.ndarray,
    fs: float = 1.0,  ***REMOVED*** Sampling frequency (1/day)
) -> dict:
    """
    Estimate frequency response (Bode plot) from data.

    Uses Welch's method for spectral estimation.
    """
    ***REMOVED*** Compute cross-spectral density
    f, Pxy = signal.csd(input_data, output_data, fs=fs, nperseg=len(input_data)//4)

    ***REMOVED*** Compute auto-spectral density of input
    _, Pxx = signal.welch(input_data, fs=fs, nperseg=len(input_data)//4)

    ***REMOVED*** Frequency response: H(f) = Pxy / Pxx
    H = Pxy / Pxx

    ***REMOVED*** Convert to magnitude and phase
    magnitude = np.abs(H)
    phase = np.angle(H, deg=True)

    ***REMOVED*** Plot Bode diagram
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))

    ax1.semilogx(f, 20 * np.log10(magnitude))
    ax1.set_ylabel('Magnitude (dB)')
    ax1.set_title('Frequency Response (Bode Plot)')
    ax1.grid(True, which='both', alpha=0.3)

    ax2.semilogx(f, phase)
    ax2.set_xlabel('Frequency (cycles/day)')
    ax2.set_ylabel('Phase (degrees)')
    ax2.grid(True, which='both', alpha=0.3)

    plt.tight_layout()
    plt.savefig('backend/data/frequency_response.png', dpi=150)
    print("✓ Frequency response plot saved")

    ***REMOVED*** Find dominant frequency
    dominant_freq_idx = np.argmax(magnitude[1:]) + 1  ***REMOVED*** Ignore DC
    dominant_freq = f[dominant_freq_idx]

    print(f"=== Frequency Response Analysis ===")
    print(f"Dominant Frequency: {dominant_freq:.4f} cycles/day ({1/dominant_freq:.1f} day period)")
    print(f"Magnitude at Dominant Freq: {20*np.log10(magnitude[dominant_freq_idx]):.2f} dB")

    return {
        "frequencies": f,
        "magnitude": magnitude,
        "phase": phase,
        "dominant_frequency": dominant_freq,
    }
```

---

***REMOVED******REMOVED*** Integration Testing

***REMOVED******REMOVED******REMOVED*** Test Scenario 1: PID + Kalman Integration

```python
***REMOVED*** File: backend/tests/integration/test_pid_kalman_integration.py

import pytest
import numpy as np
from app.resilience.pid_control import PIDControllerBank
from app.resilience.kalman_filters import KalmanFilterBank

class TestPIDKalmanIntegration:
    """Test integrated PID and Kalman filter performance."""

    def test_noisy_utilization_control(self):
        """Test PID with Kalman-filtered measurements."""

        ***REMOVED*** Initialize
        pid_bank = PIDControllerBank()
        kf_bank = KalmanFilterBank()

        ***REMOVED*** Simulation parameters
        setpoint = 0.75
        num_days = 90
        true_utilization = setpoint
        measurement_noise_std = 0.10  ***REMOVED*** 10% noise

        ***REMOVED*** History
        time = []
        true_values = []
        measured_values = []
        filtered_values = []
        control_signals = []

        for day in range(num_days):
            ***REMOVED*** Add measurement noise
            measured_util = true_utilization + np.random.normal(0, measurement_noise_std)

            ***REMOVED*** Kalman filter
            kf_result = kf_bank.update("workload", measured_util)
            filtered_util = kf_result["workload_estimate"]

            ***REMOVED*** PID control (using filtered value)
            pid_result = pid_bank.update("utilization", filtered_util)
            control = pid_result["control_signal"]

            ***REMOVED*** System dynamics (simple model)
            true_utilization += 0.15 * control
            true_utilization += np.random.normal(0, 0.01)  ***REMOVED*** Process noise

            ***REMOVED*** Record
            time.append(day)
            true_values.append(true_utilization)
            measured_values.append(measured_util)
            filtered_values.append(filtered_util)
            control_signals.append(control)

        ***REMOVED*** Assertions
        final_error = abs(true_values[-1] - setpoint)
        assert final_error < 0.05, f"Failed to converge: error={final_error}"

        ***REMOVED*** Check filter reduces noise
        measurement_std = np.std(measured_values[-30:])
        filtered_std = np.std(filtered_values[-30:])
        assert filtered_std < measurement_std, "Kalman filter should reduce noise"

        print(f"✓ PID + Kalman integration test passed")
        print(f"  Final error: {final_error:.4f}")
        print(f"  Measurement std: {measurement_std:.4f}")
        print(f"  Filtered std: {filtered_std:.4f}")
```

***REMOVED******REMOVED******REMOVED*** Test Scenario 2: MPC with PID Fallback

```python
***REMOVED*** File: backend/tests/integration/test_mpc_pid_fallback.py

class TestMPCPIDFallback:
    """Test MPC with PID fallback for real-time corrections."""

    def test_mpc_generates_plan_pid_executes(self):
        """MPC generates 4-week plan, PID makes daily adjustments."""

        ***REMOVED*** Initialize
        mpc_horizon = 28  ***REMOVED*** days
        pid_bank = PIDControllerBank()

        ***REMOVED*** MPC generates initial plan (mock)
        mpc_plan = {
            "coverage_trajectory": [0.95] * mpc_horizon,
            "utilization_trajectory": [0.75] * mpc_horizon,
        }

        ***REMOVED*** Execute with PID corrections
        for day in range(mpc_horizon):
            ***REMOVED*** Measure actual state (with disturbances)
            actual_util = mpc_plan["utilization_trajectory"][day] + np.random.normal(0, 0.05)

            ***REMOVED*** PID corrects deviations from MPC plan
            target = mpc_plan["utilization_trajectory"][day]
            pid_bank.controllers["utilization"].config.setpoint = target

            pid_result = pid_bank.update("utilization", actual_util)

            ***REMOVED*** Apply PID correction
            control = pid_result["control_signal"]

            ***REMOVED*** Verify PID brings system back to MPC trajectory
            if abs(actual_util - target) > 0.02:
                assert abs(control) > 0.01, "PID should generate correction"

        print("✓ MPC + PID fallback test passed")
```

---

***REMOVED******REMOVED*** Troubleshooting Guide

***REMOVED******REMOVED******REMOVED*** Common Issues and Solutions

***REMOVED******REMOVED******REMOVED******REMOVED*** Issue 1: PID Oscillation

**Symptoms:**
- Utilization oscillates around setpoint
- Frequent sign changes in control signal
- Overshoot on both sides

**Diagnosis:**
```python
***REMOVED*** Check oscillation count
diagnostics = pid_bank.controllers["utilization"].get_diagnostics()
if diagnostics["oscillation_detected"]:
    print("ISSUE: PID oscillating")
```

**Solutions:**

1. **Reduce Kp** (proportional gain too high)
   ```python
   controller.config.Kp *= 0.8  ***REMOVED*** Reduce by 20%
   ```

2. **Increase Kd** (need more damping)
   ```python
   controller.config.Kd *= 1.5  ***REMOVED*** Increase by 50%
   ```

3. **Add low-pass filter** to derivative term
   ```python
   ***REMOVED*** Filter derivative to reduce noise amplification
   derivative_filtered = 0.7 * derivative_filtered + 0.3 * derivative_raw
   ```

---

***REMOVED******REMOVED******REMOVED******REMOVED*** Issue 2: Integral Windup

**Symptoms:**
- Large overshoot after saturation
- Slow recovery from disturbances
- Integral term at limit

**Diagnosis:**
```python
if pid_result["integral_saturated"]:
    print("WARNING: Integral windup detected")
```

**Solutions:**

1. **Reduce integral limits**
   ```python
   controller.config.integral_limits = (-3.0, 3.0)  ***REMOVED*** Was (-5.0, 5.0)
   ```

2. **Enable conditional integration**
   ```python
   ***REMOVED*** Only integrate when not saturated (see Anti-Windup section)
   ```

3. **Reset integral on large setpoint changes**
   ```python
   if abs(new_setpoint - old_setpoint) > 0.05:
       controller.reset()
   ```

---

***REMOVED******REMOVED******REMOVED******REMOVED*** Issue 3: Kalman Filter Divergence

**Symptoms:**
- Estimate diverges from measurements
- Innovation consistently large
- NIS test fails (nis_mean >> 1.5)

**Diagnosis:**
```python
diagnostics = kf_bank.filters["workload"].get_diagnostics()
if not diagnostics["is_well_tuned"]:
    print(f"ISSUE: {diagnostics['tuning_hint']}")
```

**Solutions:**

1. **Q too small** (trusting model too much)
   ```python
   kf.Q *= 2.0  ***REMOVED*** Increase process noise
   ```

2. **R too large** (distrusting measurements)
   ```python
   kf.R *= 0.5  ***REMOVED*** Decrease measurement noise
   ```

3. **Check for model mismatch**
   ```python
   ***REMOVED*** If system dynamics changed, re-identify model
   ```

---

***REMOVED******REMOVED******REMOVED******REMOVED*** Issue 4: MPC Infeasibility

**Symptoms:**
- Solver returns "INFEASIBLE"
- No solution found within time limit
- Conflicting constraints

**Diagnosis:**
```python
if solution.status == "INFEASIBLE":
    print("ERROR: MPC problem is infeasible")
    ***REMOVED*** Analyze which constraints conflict
```

**Solutions:**

1. **Soften low-priority constraints**
   ```python
   ***REMOVED*** Convert preference constraints to soft (see Constraint Softening section)
   ```

2. **Reduce prediction horizon**
   ```python
   N = 14  ***REMOVED*** Was 28 (less constraining)
   ```

3. **Check for data errors**
   ```python
   ***REMOVED*** Verify faculty availability data is correct
   ```

---

***REMOVED******REMOVED******REMOVED*** Performance Monitoring Checklist

- [ ] **PID Controllers:**
  - [ ] No sustained oscillations (check oscillation_count)
  - [ ] Integral not saturated >50% of time
  - [ ] Settling time < 7 days
  - [ ] Steady-state error < 2%

- [ ] **Kalman Filters:**
  - [ ] Innovation white noise (autocorrelation ~0)
  - [ ] NIS in range [0.5, 1.5]
  - [ ] Uncertainty decreasing over time
  - [ ] Estimate tracks measurements smoothly

- [ ] **MPC:**
  - [ ] Solver finds solution >95% of time
  - [ ] Solve time < 60 seconds
  - [ ] Coverage target met >90% of days
  - [ ] ACGME compliance maintained

---

***REMOVED******REMOVED*** References

***REMOVED******REMOVED******REMOVED*** Control Theory Textbooks

1. **Åström, K. J., & Murray, R. M.** (2008). *Feedback Systems: An Introduction for Scientists and Engineers*. Princeton University Press.
   - Classic reference, excellent for PID and state-space methods

2. **Franklin, G. F., Powell, J. D., & Workman, M. L.** (1997). *Digital Control of Dynamic Systems* (3rd ed.). Addison-Wesley.
   - Digital implementation of control algorithms

3. **Simon, D.** (2006). *Optimal State Estimation: Kalman, H∞, and Nonlinear Approaches*. Wiley-Interscience.
   - Comprehensive Kalman filter reference

4. **Camacho, E. F., & Bordons, C.** (2007). *Model Predictive Control* (2nd ed.). Springer.
   - Authoritative MPC textbook

***REMOVED******REMOVED******REMOVED*** Tuning Methods

5. **Ziegler, J. G., & Nichols, N. B.** (1942). "Optimum Settings for Automatic Controllers." *Transactions of the ASME*, 64, 759-768.
   - Original Ziegler-Nichols paper

6. **Cohen, G. H., & Coon, G. A.** (1953). "Theoretical Consideration of Retarded Control." *Transactions of the ASME*, 75, 827-834.
   - Cohen-Coon tuning rules

7. **Åström, K. J., & Hägglund, T.** (1995). *PID Controllers: Theory, Design, and Tuning* (2nd ed.). Instrument Society of America.
   - Practical PID tuning techniques, including relay feedback

***REMOVED******REMOVED******REMOVED*** Application to Scheduling

8. **Pinedo, M. L.** (2016). *Scheduling: Theory, Algorithms, and Systems* (5th ed.). Springer.
   - Scheduling theory fundamentals

9. **Brucker, P., & Knust, S.** (2012). *Complex Scheduling* (2nd ed.). Springer.
   - Advanced scheduling algorithms

***REMOVED******REMOVED******REMOVED*** System Identification

10. **Ljung, L.** (1999). *System Identification: Theory for the User* (2nd ed.). Prentice Hall.
    - Comprehensive system identification methods (ARX, ARMAX, state-space)

11. **Keesman, K. J.** (2011). *System Identification: An Introduction*. Springer.
    - Practical introduction with examples

***REMOVED******REMOVED******REMOVED*** Online Resources

12. **MATLAB Control System Toolbox Documentation**
    - https://www.mathworks.com/help/control/
    - Excellent tutorials and examples

13. **Python Control Systems Library**
    - https://python-control.readthedocs.io/
    - Open-source control systems library for Python

14. **OR-Tools Documentation** (Google)
    - https://developers.google.com/optimization
    - Constraint programming and MPC solvers

---

***REMOVED******REMOVED*** Appendix: Quick Reference Tables

***REMOVED******REMOVED******REMOVED*** PID Tuning Quick Reference

| Symptom | Likely Cause | Solution |
|---------|--------------|----------|
| Slow response | Kp too low | Increase Kp by 20-50% |
| Oscillation | Kp too high | Decrease Kp by 20-30%, increase Kd |
| Steady-state error | Ki too low | Increase Ki by 50-100% |
| Overshoot | Kd too low | Increase Kd by 30-50% |
| Instability | All gains too high | Reduce all by 50%, start over |

***REMOVED******REMOVED******REMOVED*** Kalman Filter Quick Reference

| Symptom | Likely Cause | Solution |
|---------|--------------|----------|
| Estimate lags measurement | Q too small | Increase Q |
| Estimate too noisy | R too large | Decrease R |
| Innovation not white | Model mismatch | Re-identify system |
| Divergence | Q or R wrong | Reset and re-tune |

***REMOVED******REMOVED******REMOVED*** MPC Quick Reference

| Parameter | Typical Value | Adjust If... |
|-----------|---------------|--------------|
| **Prediction Horizon (N)** | 28 days | Computation too slow: reduce to 14 days |
| **Control Horizon (M)** | N/2 = 14 days | Schedule too reactive: increase to N |
| **Coverage Weight** | 100-200 | Coverage violations: increase |
| **Preference Weight** | 0.5-2.0 | Low satisfaction: increase |

---

**Document Status:** ✅ Complete  
**Version:** 1.0  
**Last Updated:** 2025-12-26  
**Word Count:** ~11,500 words

**Maintenance:** Update this guide when new tuning methods are discovered or system dynamics change significantly.

