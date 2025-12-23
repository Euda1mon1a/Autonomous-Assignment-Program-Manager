# Exotic Control Theory for Residency Scheduling and Resilience Systems

**Research Report**
**Date:** 2025-12-20
**Purpose:** Explore advanced control theory concepts complementary to existing homeostasis, Le Chatelier, and stigmergy implementations

---

## Executive Summary

This report analyzes six exotic control theory concepts and their application to medical residency scheduling and workforce resilience. Each concept offers unique capabilities that complement the existing feedback loops, equilibrium analysis, and preference-tracking systems.

**Key Finding:** Control theory provides a unified mathematical framework for managing system dynamics that naturally integrates with constraint-based optimization.

**Recommended Priority:**
1. **PID Controllers** - Immediate value for workload balancing
2. **Model Predictive Control** - Natural fit for schedule optimization
3. **Kalman Filters** - Enhanced state estimation under uncertainty
4. **Adaptive Control** - Long-term system learning
5. **Smith Predictor** - Managing delayed feedback effects
6. **Sliding Mode Control** - Crisis robustness (advanced)

---

## 1. PID Controllers (Proportional-Integral-Derivative Control)

### Core Principle

PID controllers maintain a process variable at a setpoint by continuously calculating an error value and applying corrections based on proportional, integral, and derivative terms.

**Mathematical Foundation:**

```
u(t) = Kp·e(t) + Ki·∫e(τ)dτ + Kd·de(t)/dt

Where:
- u(t) = control signal (corrective action)
- e(t) = error (setpoint - current_value)
- Kp = proportional gain (immediate response)
- Ki = integral gain (accumulated error correction)
- Kd = derivative gain (rate of change damping)
```

**Control Law Interpretation:**
- **Proportional (P):** React proportionally to current deviation ("How far off are we?")
- **Integral (I):** Eliminate accumulated error over time ("How long have we been off?")
- **Derivative (D):** Dampen oscillations by anticipating trends ("How fast are we changing?")

### Application to Residency Scheduling

#### Use Case 1: Faculty Utilization Control

**Problem:** Faculty utilization tends to drift from target (75%), causing either burnout (>80%) or underutilization (<60%).

**PID Solution:**

```python
class UtilizationPIDController:
    """
    PID controller for maintaining faculty utilization at setpoint.

    Setpoint: 0.75 (75% utilization, below queuing theory threshold)
    Process Variable: Current faculty utilization rate
    Control Signal: Number of assignments to add/remove
    """

    def __init__(
        self,
        setpoint: float = 0.75,
        Kp: float = 10.0,    # Strong immediate response
        Ki: float = 0.5,     # Slow integral windup
        Kd: float = 2.0,     # Moderate damping
        dt: float = 1.0,     # Daily sampling
    ):
        self.setpoint = setpoint
        self.Kp = Kp
        self.Ki = Ki
        self.Kd = Kd
        self.dt = dt

        # State variables
        self.integral = 0.0
        self.previous_error = 0.0

        # Anti-windup limits
        self.integral_max = 5.0
        self.integral_min = -5.0

        # History for analysis
        self.error_history: list[float] = []
        self.control_history: list[float] = []

    def update(self, current_utilization: float) -> dict:
        """
        Calculate PID control signal.

        Args:
            current_utilization: Current faculty utilization (0.0-1.0)

        Returns:
            Dict with control signal and diagnostics
        """
        # Calculate error
        error = self.setpoint - current_utilization

        # Proportional term
        P = self.Kp * error

        # Integral term (with anti-windup)
        self.integral += error * self.dt
        self.integral = max(self.integral_min, min(self.integral_max, self.integral))
        I = self.Ki * self.integral

        # Derivative term
        derivative = (error - self.previous_error) / self.dt if self.dt > 0 else 0.0
        D = self.Kd * derivative

        # Combined control signal
        control_signal = P + I + D

        # Update state
        self.previous_error = error
        self.error_history.append(error)
        self.control_history.append(control_signal)

        # Interpret control signal
        action = self._interpret_control_signal(control_signal, current_utilization)

        return {
            "error": error,
            "control_signal": control_signal,
            "P_contribution": P,
            "I_contribution": I,
            "D_contribution": D,
            "action": action,
            "diagnostics": self._get_diagnostics(),
        }

    def _interpret_control_signal(self, signal: float, current_util: float) -> dict:
        """
        Convert abstract control signal to scheduling actions.

        Positive signal = need to reduce utilization (remove assignments)
        Negative signal = can increase utilization (add assignments)
        """
        # Scale signal to assignment changes
        # Assume each assignment changes utilization by ~0.02
        assignments_to_change = int(signal / 0.02)

        if abs(signal) < 0.1:
            return {
                "type": "maintain",
                "description": f"Utilization at {current_util:.1%}, within tolerance",
                "assignments_delta": 0,
            }
        elif signal > 0:
            # Overutilized - remove assignments
            return {
                "type": "reduce_load",
                "description": f"Reduce by ~{assignments_to_change} assignments",
                "assignments_delta": -assignments_to_change,
                "priority": "high" if current_util > 0.80 else "medium",
            }
        else:
            # Underutilized - can add more
            return {
                "type": "increase_load",
                "description": f"Can safely add ~{abs(assignments_to_change)} assignments",
                "assignments_delta": abs(assignments_to_change),
                "priority": "low",
            }

    def _get_diagnostics(self) -> dict:
        """Diagnostic information for tuning."""
        return {
            "integral_state": self.integral,
            "is_integral_saturated": (
                abs(self.integral - self.integral_max) < 0.1 or
                abs(self.integral - self.integral_min) < 0.1
            ),
            "recent_errors": self.error_history[-10:] if self.error_history else [],
            "oscillation_detected": self._detect_oscillation(),
        }

    def _detect_oscillation(self, window: int = 6) -> bool:
        """Detect oscillation by counting sign changes."""
        if len(self.error_history) < window:
            return False

        recent = self.error_history[-window:]
        sign_changes = sum(
            1 for i in range(1, len(recent))
            if recent[i] * recent[i-1] < 0
        )

        # Oscillating if >50% sign changes
        return sign_changes > window // 2

    def reset(self):
        """Reset controller state."""
        self.integral = 0.0
        self.previous_error = 0.0
        self.error_history.clear()
        self.control_history.clear()

    def tune_ziegler_nichols(self, ultimate_gain: float, ultimate_period: float):
        """
        Auto-tune using Ziegler-Nichols method.

        Args:
            ultimate_gain: Ku - gain at which system oscillates
            ultimate_period: Pu - period of oscillation at Ku
        """
        # Classic Ziegler-Nichols PID tuning
        self.Kp = 0.6 * ultimate_gain
        self.Ki = 1.2 * ultimate_gain / ultimate_period
        self.Kd = 0.075 * ultimate_gain * ultimate_period
```

#### Use Case 2: Workload Balance Control

**Problem:** Workload variance across faculty causes inequality and resentment.

**PID Solution:**

```python
class WorkloadBalancePIDController:
    """
    Maintains low variance in workload distribution across faculty.

    Setpoint: 0.15 (target standard deviation of workload)
    Process Variable: Current workload standard deviation
    Control Signal: Workload redistribution magnitude
    """

    def __init__(self, setpoint: float = 0.15, Kp: float = 5.0, Ki: float = 0.3, Kd: float = 1.0):
        self.setpoint = setpoint
        self.Kp = Kp
        self.Ki = Ki
        self.Kd = Kd
        self.integral = 0.0
        self.previous_error = 0.0

    def calculate_redistribution(
        self,
        faculty_workloads: dict[UUID, float]
    ) -> list[tuple[UUID, UUID, float]]:
        """
        Calculate workload transfers to balance load.

        Returns:
            List of (from_faculty, to_faculty, amount) tuples
        """
        current_std = statistics.stdev(faculty_workloads.values())
        error = self.setpoint - current_std

        # PID calculation
        P = self.Kp * error
        self.integral += error
        I = self.Ki * self.integral
        D = self.Kd * (error - self.previous_error)

        control_signal = P + I + D
        self.previous_error = error

        # Convert to transfers
        # Negative control = need more balance (higher variance than setpoint)
        if control_signal < -0.1:
            magnitude = abs(control_signal)
            return self._generate_transfers(faculty_workloads, magnitude)

        return []

    def _generate_transfers(
        self,
        workloads: dict[UUID, float],
        magnitude: float
    ) -> list[tuple[UUID, UUID, float]]:
        """Generate actual workload transfer recommendations."""
        mean_workload = statistics.mean(workloads.values())

        # Identify overloaded and underloaded
        overloaded = [(fid, load) for fid, load in workloads.items() if load > mean_workload]
        underloaded = [(fid, load) for fid, load in workloads.items() if load < mean_workload]

        overloaded.sort(key=lambda x: -x[1])  # Highest first
        underloaded.sort(key=lambda x: x[1])   # Lowest first

        transfers = []
        remaining_magnitude = magnitude

        for from_fid, from_load in overloaded:
            for to_fid, to_load in underloaded:
                if remaining_magnitude <= 0:
                    break

                # Calculate optimal transfer
                excess = from_load - mean_workload
                deficit = mean_workload - to_load
                transfer = min(excess, deficit, remaining_magnitude * 0.5)

                if transfer > 0.05:  # Minimum meaningful transfer
                    transfers.append((from_fid, to_fid, transfer))
                    remaining_magnitude -= transfer

        return transfers
```

#### Use Case 3: Coverage Rate PID Control

**Problem:** Coverage rate fluctuates due to absences, emergencies, and scheduling gaps.

**PID Integration with Existing Homeostasis:**

```python
class CoveragePIDIntegration:
    """
    Integrate PID control with existing homeostasis feedback loops.

    This enhances the existing setpoint-based system with PID dynamics.
    """

    def __init__(self, homeostasis_monitor: HomeostasisMonitor):
        self.homeostasis = homeostasis_monitor

        # Create PID controllers for each setpoint
        self.pid_controllers: dict[str, UtilizationPIDController] = {}

        # Initialize PIDs for critical setpoints
        for setpoint in self.homeostasis.setpoints.values():
            if setpoint.is_critical:
                self.pid_controllers[setpoint.name] = UtilizationPIDController(
                    setpoint=setpoint.target_value,
                    Kp=self._get_proportional_gain(setpoint),
                    Ki=self._get_integral_gain(setpoint),
                    Kd=self._get_derivative_gain(setpoint),
                )

    def update_with_pid(self, current_values: dict[str, float]) -> dict:
        """
        Run PID controllers alongside homeostasis feedback loops.

        Args:
            current_values: Current values for all setpoints

        Returns:
            Combined recommendations from both systems
        """
        # Run standard homeostasis check
        corrections = self.homeostasis.check_all_loops(current_values)

        # Run PID controllers
        pid_actions = {}
        for setpoint_name, current_value in current_values.items():
            if setpoint_name in self.pid_controllers:
                pid = self.pid_controllers[setpoint_name]
                result = pid.update(current_value)
                pid_actions[setpoint_name] = result

        # Combine recommendations
        return {
            "homeostasis_corrections": corrections,
            "pid_actions": pid_actions,
            "combined_recommendations": self._merge_recommendations(corrections, pid_actions),
        }

    def _get_proportional_gain(self, setpoint: Setpoint) -> float:
        """Calculate appropriate Kp based on setpoint characteristics."""
        # Critical setpoints need stronger immediate response
        if setpoint.is_critical:
            return 15.0
        # Tolerance determines sensitivity
        return 1.0 / setpoint.tolerance

    def _get_integral_gain(self, setpoint: Setpoint) -> float:
        """Calculate appropriate Ki based on setpoint characteristics."""
        # Critical setpoints accumulate error faster
        if setpoint.is_critical:
            return 1.0
        return 0.3

    def _get_derivative_gain(self, setpoint: Setpoint) -> float:
        """Calculate appropriate Kd based on setpoint characteristics."""
        # More damping for volatile metrics
        if setpoint.name in ("schedule_stability", "workload_balance"):
            return 3.0
        return 1.0

    def _merge_recommendations(self, corrections, pid_actions) -> list[str]:
        """Merge homeostasis corrections with PID actions into coherent plan."""
        recommendations = []

        # Prioritize by urgency
        for correction in corrections:
            if correction.deviation_severity in (DeviationSeverity.CRITICAL, DeviationSeverity.MAJOR):
                recommendations.append({
                    "source": "homeostasis",
                    "priority": "critical",
                    "action": correction.action_type.value,
                    "description": correction.description,
                })

        for setpoint_name, pid_result in pid_actions.items():
            action = pid_result["action"]
            if action["type"] != "maintain":
                # Add PID-based fine-tuning
                recommendations.append({
                    "source": "pid",
                    "priority": action.get("priority", "medium"),
                    "setpoint": setpoint_name,
                    "description": action["description"],
                    "delta": action["assignments_delta"],
                    "diagnostics": pid_result["diagnostics"],
                })

        return recommendations
```

### Key Parameters for Tuning

| Parameter | Typical Range | Effect | Tuning Guidance |
|-----------|---------------|--------|-----------------|
| **Kp** (Proportional) | 1.0 - 20.0 | Immediate response strength | Higher = faster response, risk of overshoot |
| **Ki** (Integral) | 0.1 - 2.0 | Accumulated error correction | Higher = eliminates steady-state error, risk of windup |
| **Kd** (Derivative) | 0.5 - 5.0 | Oscillation damping | Higher = smoother response, sensitive to noise |
| **dt** (Sampling) | 1.0 - 7.0 days | Update frequency | Match to system dynamics (daily for utilization) |

**Tuning Methods:**

1. **Manual Tuning (Start Conservative):**
   - Start: Kp=1.0, Ki=0.0, Kd=0.0 (P-only)
   - Increase Kp until response is fast but not oscillating
   - Add Ki slowly to eliminate offset
   - Add Kd to reduce overshoot

2. **Ziegler-Nichols Method:**
   - Find ultimate gain (Ku) where system oscillates sustainably
   - Measure oscillation period (Pu)
   - Calculate: Kp=0.6·Ku, Ki=2·Kp/Pu, Kd=Kp·Pu/8

3. **Software-Defined Auto-Tuning:**
   - Run relay feedback test
   - Observe system response to step changes
   - Use optimization to minimize integral squared error (ISE)

### Implementation Strategy

```python
# File: backend/app/resilience/pid_control.py

"""
PID Controllers for scheduling system dynamics.

Complements existing homeostasis feedback loops with classical
control theory for precise setpoint tracking.
"""

from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4
import statistics


@dataclass
class PIDState:
    """State of a PID controller."""
    id: UUID
    name: str
    setpoint: float

    # Gains
    Kp: float
    Ki: float
    Kd: float

    # State variables
    integral: float = 0.0
    previous_error: float = 0.0
    previous_time: datetime = field(default_factory=datetime.now)

    # Anti-windup
    integral_max: float = 10.0
    integral_min: float = -10.0

    # History
    error_history: list[tuple[datetime, float]] = field(default_factory=list)
    control_history: list[tuple[datetime, float]] = field(default_factory=list)

    # Diagnostics
    oscillation_count: int = 0
    saturation_count: int = 0


class PIDControllerBank:
    """
    Bank of PID controllers for scheduling system.

    Manages multiple PIDs for different process variables:
    - Faculty utilization
    - Workload balance
    - Coverage rate
    - Schedule stability
    """

    def __init__(self):
        self.controllers: dict[str, PIDState] = {}
        self._initialize_default_controllers()

    def _initialize_default_controllers(self):
        """Initialize standard controllers for scheduling."""
        # Utilization controller
        self.controllers["utilization"] = PIDState(
            id=uuid4(),
            name="Faculty Utilization PID",
            setpoint=0.75,
            Kp=10.0,
            Ki=0.5,
            Kd=2.0,
        )

        # Workload balance controller
        self.controllers["workload_balance"] = PIDState(
            id=uuid4(),
            name="Workload Balance PID",
            setpoint=0.15,  # Target std dev
            Kp=5.0,
            Ki=0.3,
            Kd=1.0,
        )

        # Coverage rate controller
        self.controllers["coverage"] = PIDState(
            id=uuid4(),
            name="Coverage Rate PID",
            setpoint=0.95,
            Kp=12.0,
            Ki=0.8,
            Kd=2.5,
        )

    def update(self, process_variable: str, current_value: float) -> dict:
        """Update PID controller and get control signal."""
        controller = self.controllers.get(process_variable)
        if not controller:
            raise ValueError(f"Unknown process variable: {process_variable}")

        now = datetime.now()
        dt = (now - controller.previous_time).total_seconds() / 86400  # Days

        # Calculate error
        error = controller.setpoint - current_value

        # P term
        P = controller.Kp * error

        # I term with anti-windup
        controller.integral += error * dt
        controller.integral = max(
            controller.integral_min,
            min(controller.integral_max, controller.integral)
        )
        I = controller.Ki * controller.integral

        # D term
        derivative = (error - controller.previous_error) / dt if dt > 0 else 0.0
        D = controller.Kd * derivative

        # Control signal
        control_signal = P + I + D

        # Update state
        controller.previous_error = error
        controller.previous_time = now
        controller.error_history.append((now, error))
        controller.control_history.append((now, control_signal))

        # Trim history
        if len(controller.error_history) > 100:
            controller.error_history = controller.error_history[-100:]
        if len(controller.control_history) > 100:
            controller.control_history = controller.control_history[-100:]

        # Check for issues
        if abs(controller.integral - controller.integral_max) < 0.1:
            controller.saturation_count += 1

        if self._is_oscillating(controller):
            controller.oscillation_count += 1

        return {
            "error": error,
            "control_signal": control_signal,
            "P": P,
            "I": I,
            "D": D,
            "integral_saturated": abs(controller.integral - controller.integral_max) < 0.1,
            "oscillating": controller.oscillation_count > 3,
        }

    def _is_oscillating(self, controller: PIDState, window: int = 6) -> bool:
        """Detect oscillation in error signal."""
        if len(controller.error_history) < window:
            return False

        recent_errors = [e for _, e in controller.error_history[-window:]]
        sign_changes = sum(
            1 for i in range(1, len(recent_errors))
            if recent_errors[i] * recent_errors[i-1] < 0
        )

        return sign_changes > window // 2

    def tune(self, process_variable: str, method: str = "ziegler_nichols", **kwargs):
        """Auto-tune PID controller."""
        controller = self.controllers.get(process_variable)
        if not controller:
            raise ValueError(f"Unknown process variable: {process_variable}")

        if method == "ziegler_nichols":
            Ku = kwargs.get("ultimate_gain")
            Pu = kwargs.get("ultimate_period")
            if not Ku or not Pu:
                raise ValueError("Ziegler-Nichols requires ultimate_gain and ultimate_period")

            controller.Kp = 0.6 * Ku
            controller.Ki = 1.2 * Ku / Pu
            controller.Kd = 0.075 * Ku * Pu

    def reset(self, process_variable: str):
        """Reset controller to initial state."""
        controller = self.controllers.get(process_variable)
        if controller:
            controller.integral = 0.0
            controller.previous_error = 0.0
            controller.error_history.clear()
            controller.control_history.clear()
```

---

## 2. Kalman Filters (Optimal State Estimation Under Uncertainty)

### Core Principle

Kalman filters optimally estimate the true state of a system from noisy, uncertain measurements by combining predictions with observations weighted by their uncertainty.

**Mathematical Foundation:**

```
State Update:
x̂(k|k) = x̂(k|k-1) + K(k)[z(k) - H·x̂(k|k-1)]

Where:
- x̂(k|k) = estimated state at time k
- x̂(k|k-1) = predicted state from previous time
- z(k) = measurement at time k
- K(k) = Kalman gain (optimal weighting)
- H = measurement matrix

Kalman Gain:
K(k) = P(k|k-1)·H^T / [H·P(k|k-1)·H^T + R]

Where:
- P = state covariance (uncertainty in estimate)
- R = measurement noise covariance
```

**Key Insight:** The Kalman filter automatically weights predictions vs measurements based on their respective uncertainties. If measurements are noisy, it trusts the model more. If the model is uncertain, it trusts measurements more.

### Application to Residency Scheduling

#### Use Case 1: True Workload Estimation

**Problem:** Reported workload hours are noisy (self-reported, rounding, missing data), but we need accurate estimates for ACGME compliance and resilience monitoring.

**Kalman Solution:**

```python
class WorkloadKalmanFilter:
    """
    Estimate true faculty workload from noisy measurements.

    State Vector:
    x = [actual_hours, weekly_trend, seasonal_component]

    Measurements:
    z = [self_reported_hours, system_logged_hours, peer_estimates]
    """

    def __init__(self, initial_hours: float = 60.0):
        # State: [hours, trend, seasonal]
        self.x = np.array([initial_hours, 0.0, 0.0])

        # State covariance (uncertainty in estimate)
        self.P = np.array([
            [25.0, 0.0, 0.0],   # High initial uncertainty in hours
            [0.0, 1.0, 0.0],    # Moderate uncertainty in trend
            [0.0, 0.0, 4.0],    # Moderate uncertainty in seasonal
        ])

        # State transition matrix (how state evolves)
        self.F = np.array([
            [1.0, 1.0, 1.0],   # hours += trend + seasonal
            [0.0, 0.95, 0.0],  # trend decays 5% per week
            [0.0, 0.0, 0.98],  # seasonal decays 2% per week
        ])

        # Process noise (model uncertainty)
        self.Q = np.array([
            [4.0, 0.0, 0.0],   # Hours vary randomly
            [0.0, 0.5, 0.0],   # Trend changes
            [0.0, 0.0, 1.0],   # Seasonal component varies
        ])

        # Measurement matrix (what we observe)
        self.H = np.array([
            [1.0, 0.0, 0.0],   # Self-report measures hours directly
            [1.0, 0.0, 0.0],   # System logs measure hours
            [1.0, 0.0, 0.0],   # Peer estimate measures hours
        ])

        # Measurement noise (sensor uncertainty)
        self.R = np.array([
            [16.0, 0.0, 0.0],   # Self-report: ±4 hours std dev
            [9.0, 0.0, 0.0],    # System logs: ±3 hours (more accurate)
            [25.0, 0.0, 0.0],   # Peer estimate: ±5 hours (less reliable)
        ])

        # History
        self.history: list[dict] = []

    def predict(self) -> np.ndarray:
        """
        Prediction step: Estimate state at next time step.

        Returns:
            Predicted state vector
        """
        # Predict state
        x_pred = self.F @ self.x

        # Predict covariance
        P_pred = self.F @ self.P @ self.F.T + self.Q

        return x_pred, P_pred

    def update(self, measurements: dict) -> dict:
        """
        Update step: Correct prediction with measurements.

        Args:
            measurements: Dict with keys 'self_report', 'system_log', 'peer_estimate'
                         Values can be None if measurement unavailable

        Returns:
            Dict with estimated state and diagnostics
        """
        # Prediction step
        x_pred, P_pred = self.predict()

        # Build measurement vector and observation matrix
        z_list = []
        H_list = []
        R_list = []

        if measurements.get('self_report') is not None:
            z_list.append(measurements['self_report'])
            H_list.append(self.H[0])
            R_list.append(self.R[0,0])

        if measurements.get('system_log') is not None:
            z_list.append(measurements['system_log'])
            H_list.append(self.H[1])
            R_list.append(self.R[1,1])

        if measurements.get('peer_estimate') is not None:
            z_list.append(measurements['peer_estimate'])
            H_list.append(self.H[2])
            R_list.append(self.R[2,2])

        if not z_list:
            # No measurements - just use prediction
            self.x = x_pred
            self.P = P_pred
            innovation = None
            kalman_gain = None
        else:
            # Have measurements - update
            z = np.array(z_list)
            H_obs = np.array(H_list)
            R_obs = np.diag(R_list)

            # Innovation (measurement residual)
            innovation = z - (H_obs @ x_pred)

            # Innovation covariance
            S = H_obs @ P_pred @ H_obs.T + R_obs

            # Kalman gain
            kalman_gain = P_pred @ H_obs.T @ np.linalg.inv(S)

            # Update state
            self.x = x_pred + kalman_gain @ innovation

            # Update covariance
            I = np.eye(len(self.x))
            self.P = (I - kalman_gain @ H_obs) @ P_pred

        # Record history
        result = {
            "timestamp": datetime.now(),
            "estimated_hours": self.x[0],
            "trend": self.x[1],
            "seasonal": self.x[2],
            "uncertainty": np.sqrt(self.P[0,0]),  # Standard deviation
            "measurements": measurements,
            "innovation": innovation.tolist() if innovation is not None else None,
            "kalman_gain": kalman_gain.tolist() if kalman_gain is not None else None,
        }
        self.history.append(result)

        return result

    def get_confidence_interval(self, confidence: float = 0.95) -> tuple[float, float]:
        """
        Get confidence interval for current estimate.

        Args:
            confidence: Confidence level (e.g., 0.95 for 95%)

        Returns:
            (lower_bound, upper_bound)
        """
        from scipy.stats import norm

        z_score = norm.ppf((1 + confidence) / 2)
        std_dev = np.sqrt(self.P[0,0])

        return (
            self.x[0] - z_score * std_dev,
            self.x[0] + z_score * std_dev
        )

    def is_estimate_reliable(self, threshold_std: float = 3.0) -> bool:
        """Check if estimate is reliable (low uncertainty)."""
        return np.sqrt(self.P[0,0]) < threshold_std
```

#### Use Case 2: Schedule Health State Estimation

**Problem:** Schedule health depends on multiple noisy indicators (utilization, coverage, satisfaction). We need a unified state estimate.

**Extended Kalman Filter for Schedule Health:**

```python
class ScheduleHealthEKF:
    """
    Extended Kalman Filter for overall schedule health estimation.

    State Vector:
    x = [
        overall_health,      # Latent health score (0-1)
        coverage_quality,    # True coverage quality
        workload_stress,     # Underlying stress level
<<<<<<< HEAD
        morale,              # Faculty morale
=======
        morale,              ***REMOVED*** morale
>>>>>>> origin/docs/session-14-summary
    ]

    Measurements:
    z = [
        coverage_rate,       # Observed coverage
        reported_stress,     # Self-reported stress
        satisfaction_score,  # Survey results
        swap_request_rate,   # Behavioral indicator
    ]
    """

    def __init__(self):
        # Initial state estimate (assume healthy start)
        self.x = np.array([0.8, 0.9, 0.3, 0.7])

        # Initial uncertainty
        self.P = np.eye(4) * 0.1

        # Process noise
        self.Q = np.diag([0.01, 0.02, 0.05, 0.03])

        # Measurement noise
        self.R = np.diag([0.05, 0.10, 0.15, 0.08])

    def predict(self, dt: float = 1.0) -> tuple:
        """
        Predict next state using nonlinear dynamics.

        Health dynamics:
        - Health tends toward coverage and inverse of stress
        - Coverage quality slowly degrades without intervention
        - Stress accumulates with overwork
        - Morale follows health with lag
        """
        # Nonlinear state transition
        health = self.x[0]
        coverage = self.x[1]
        stress = self.x[2]
        morale = self.x[3]

        # Dynamics (simplified nonlinear model)
        health_next = 0.7 * health + 0.2 * coverage - 0.1 * stress
        coverage_next = 0.95 * coverage  # Slow degradation
        stress_next = 0.9 * stress + 0.1 * (1.0 - coverage)  # Accumulates from gaps
        morale_next = 0.8 * morale + 0.2 * health  # Follows health with lag

        x_pred = np.array([health_next, coverage_next, stress_next, morale_next])

        # Jacobian for linearization (EKF)
        F = np.array([
            [0.7, 0.2, -0.1, 0.0],
            [0.0, 0.95, 0.0, 0.0],
            [0.0, -0.1, 0.9, 0.0],
            [0.2, 0.0, 0.0, 0.8],
        ])

        # Predict covariance
        P_pred = F @ self.P @ F.T + self.Q

        return x_pred, P_pred

    def update(self, measurements: dict) -> dict:
        """
        Update with measurements.

        Args:
            measurements: {
                'coverage_rate': float or None,
                'reported_stress': float or None,
                'satisfaction_score': float or None,
                'swap_request_rate': float or None,
            }
        """
        x_pred, P_pred = self.predict()

        # Measurement function (nonlinear mapping from state to observations)
        def h(x):
            """Map state to expected measurements."""
            health, coverage, stress, morale = x
            return np.array([
                coverage,              # Coverage observed directly
                stress,                # Stress reported (with bias)
                morale * 0.8 + 0.2,    # Satisfaction correlates with morale
                stress * 1.5,          # Swap requests increase with stress
            ])

        # Measurement Jacobian
        H = np.array([
            [0.0, 1.0, 0.0, 0.0],      # coverage
            [0.0, 0.0, 1.0, 0.0],      # stress
            [0.0, 0.0, 0.0, 0.8],      # satisfaction
            [0.0, 0.0, 1.5, 0.0],      # swap rate
        ])

        # Build measurement vector (handle missing data)
        z_list = []
        H_rows = []
        R_diag = []

        for i, key in enumerate(['coverage_rate', 'reported_stress', 'satisfaction_score', 'swap_request_rate']):
            if measurements.get(key) is not None:
                z_list.append(measurements[key])
                H_rows.append(H[i])
                R_diag.append(self.R[i,i])

        if not z_list:
            # No measurements
            self.x = x_pred
            self.P = P_pred
            return {"estimated_health": self.x[0], "uncertainty": np.sqrt(self.P[0,0])}

        z = np.array(z_list)
        H_obs = np.array(H_rows)
        R_obs = np.diag(R_diag)

        # Innovation
        y = z - (H_obs @ x_pred)

        # Innovation covariance
        S = H_obs @ P_pred @ H_obs.T + R_obs

        # Kalman gain
        K = P_pred @ H_obs.T @ np.linalg.inv(S)

        # Update
        self.x = x_pred + K @ y
        self.P = (np.eye(4) - K @ H_obs) @ P_pred

        return {
            "estimated_health": self.x[0],
            "estimated_coverage_quality": self.x[1],
            "estimated_stress": self.x[2],
            "estimated_morale": self.x[3],
            "uncertainty_health": np.sqrt(self.P[0,0]),
            "innovation": y.tolist(),
            "measurements_used": len(z_list),
        }
```

### Key Parameters for Tuning

| Parameter | Typical Range | Effect | Tuning Guidance |
|-----------|---------------|--------|-----------------|
| **Q** (Process Noise) | 0.01 - 0.1 | Model uncertainty | Higher = trust model less, react to measurements more |
| **R** (Measurement Noise) | 0.05 - 0.5 | Sensor uncertainty | Higher = trust measurements less, rely on model more |
| **P0** (Initial Covariance) | 0.1 - 10.0 | Initial uncertainty | Higher = filter takes longer to converge |
| **F** (State Transition) | N/A | System dynamics | Must match actual system behavior |

**Tuning Strategy:**

1. **Estimate Measurement Noise (R):**
   - Collect repeated measurements under same conditions
   - Calculate sample variance
   - R = variance matrix

2. **Estimate Process Noise (Q):**
   - Run filter with Q=0
   - Observe innovation (measurement - prediction)
   - Q should make innovation white noise (uncorrelated)

3. **Validate with Historical Data:**
   - Run filter on past data
   - Check that 95% of measurements fall within 95% confidence interval
   - Adjust Q and R to achieve this

---

## 3. Model Predictive Control (MPC) / Receding Horizon Optimization

### Core Principle

MPC solves an optimization problem at each time step to find the best sequence of control actions over a finite horizon, executes the first action, then re-solves at the next step.

**Mathematical Foundation:**

```
min  Σ[k=0 to N] [ ||x(k) - x_ref||²_Q + ||u(k)||²_R ]
u

subject to:
    x(k+1) = f(x(k), u(k))           # System dynamics
    x_min ≤ x(k) ≤ x_max             # State constraints
    u_min ≤ u(k) ≤ u_max             # Control constraints
    g(x(k), u(k)) ≤ 0                # General constraints

Where:
- N = prediction horizon
- x(k) = state at time k
- u(k) = control input at time k
- Q, R = weighting matrices
- f() = system dynamics model
```

**Key Insight:** MPC explicitly handles constraints (ACGME rules, capacity limits) and can optimize over future time, making it ideal for scheduling.

### Application to Residency Scheduling

#### Use Case 1: Schedule Generation as MPC

**Problem:** Traditional scheduling solves one big optimization problem. MPC can incrementally build schedules while adapting to changing conditions.

**MPC Scheduling Framework:**

```python
class MPCScheduler:
    """
    Model Predictive Control for adaptive schedule generation.

    Instead of solving entire year at once, solve 4-week windows
    with receding horizon. This enables:
    - Faster solve times (smaller problems)
    - Adaptation to new information (absences, preferences)
    - Explicit handling of future uncertainty
    """

    def __init__(
        self,
        horizon_weeks: int = 4,
        control_horizon_weeks: int = 2,
        objective_weights: dict = None,
    ):
        self.horizon_weeks = horizon_weeks  # How far ahead to predict
        self.control_horizon_weeks = control_horizon_weeks  # How many weeks to optimize

        # Objective function weights
        self.weights = objective_weights or {
            'coverage': 100.0,          # Must maintain coverage
            'utilization': 50.0,        # Keep utilization near target
            'workload_balance': 30.0,   # Balance workload
            'preference': 20.0,         # Honor preferences
            'continuity': 15.0,         # Maintain continuity
            'setup_cost': 10.0,         # Minimize changes
        }

        # Model of system dynamics
        self.state_model = ScheduleStateModel()

    def generate_schedule(
        self,
        start_date: date,
        end_date: date,
        initial_state: dict,
        constraints: ConstraintManager,
    ) -> list[Assignment]:
        """
        Generate schedule using receding horizon MPC.

        Args:
            start_date: Start of schedule period
            end_date: End of schedule period
            initial_state: Initial system state (current assignments, utilization, etc.)
            constraints: Constraint manager

        Returns:
            List of assignments for entire period
        """
        assignments = []
        current_date = start_date
        current_state = initial_state

        while current_date < end_date:
            # Define current horizon
            horizon_end = min(
                current_date + timedelta(weeks=self.horizon_weeks),
                end_date
            )

            # Solve MPC problem for this horizon
            horizon_assignments, next_state = self._solve_mpc_step(
                current_date=current_date,
                horizon_end=horizon_end,
                current_state=current_state,
                constraints=constraints,
            )

            # Extract assignments for control horizon only (rest is discarded)
            control_end = current_date + timedelta(weeks=self.control_horizon_weeks)
            executed_assignments = [
                a for a in horizon_assignments
                if current_date <= a.block.date < control_end
            ]

            assignments.extend(executed_assignments)

            # Update state with executed assignments
            current_state = self.state_model.update(current_state, executed_assignments)

            # Move horizon forward
            current_date = control_end

            logger.info(
                f"MPC step completed: {current_date} to {control_end}, "
                f"{len(executed_assignments)} assignments"
            )

        return assignments

    def _solve_mpc_step(
        self,
        current_date: date,
        horizon_end: date,
        current_state: dict,
        constraints: ConstraintManager,
    ) -> tuple[list, dict]:
        """
        Solve single MPC optimization step.

        This is the core MPC optimization:
        1. Predict future states over horizon
        2. Optimize control actions (assignments)
        3. Return best action sequence
        """
        from ortools.sat.python import cp_model

        model = cp_model.CpModel()

        # Get data for horizon
        blocks = self._get_blocks_for_horizon(current_date, horizon_end)
        residents = self._get_available_residents(current_date, horizon_end)
        templates = self._get_rotation_templates()

        # Create decision variables
        variables = {}
        for resident in residents:
            for block in blocks:
                for template in templates:
                    var_name = f"assign_{resident.id}_{block.id}_{template.id}"
                    variables[(resident.id, block.id, template.id)] = model.NewBoolVar(var_name)

        # Add constraints
        for constraint in constraints.get_hard_constraints():
            constraint.add_to_cpsat(model, variables, current_state)

        # Build multi-objective function
        objective_terms = []

        # 1. Coverage objective
        coverage_penalties = self._create_coverage_objective(model, variables, blocks)
        objective_terms.append(self.weights['coverage'] * coverage_penalties)

        # 2. Utilization objective (keep near target over horizon)
        utilization_penalties = self._create_utilization_objective(
            model, variables, residents, blocks, current_state
        )
        objective_terms.append(self.weights['utilization'] * utilization_penalties)

        # 3. Workload balance objective
        balance_penalties = self._create_balance_objective(model, variables, residents)
        objective_terms.append(self.weights['workload_balance'] * balance_penalties)

        # 4. Preference objective (integrate stigmergy trails)
        preference_bonus = self._create_preference_objective(
            model, variables, residents, blocks, templates
        )
        objective_terms.append(self.weights['preference'] * preference_bonus)

        # 5. Continuity objective (prefer stable assignments)
        continuity_bonus = self._create_continuity_objective(
            model, variables, current_state
        )
        objective_terms.append(self.weights['continuity'] * continuity_bonus)

        # Set objective
        model.Maximize(sum(objective_terms))

        # Solve
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = 30.0  # Fast solve for real-time MPC
        status = solver.Solve(model)

        if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            # Extract assignments
            assignments = self._extract_assignments(solver, variables, residents, blocks, templates)

            # Predict end state
            end_state = self.state_model.predict(current_state, assignments, horizon_end)

            return assignments, end_state
        else:
            logger.warning(f"MPC solve failed with status {status}")
            # Return empty or fallback
            return [], current_state

    def _create_utilization_objective(self, model, variables, residents, blocks, current_state):
        """
        Create objective terms for maintaining target utilization.

        This predicts utilization over the horizon and penalizes deviation
        from the 75% target.
        """
        # Predict utilization at each week in horizon
        weeks = self._group_blocks_by_week(blocks)
        penalty_vars = []

        for week_blocks in weeks:
            # Total assignments in this week
            week_assignments = [
                variables[(r.id, b.id, t.id)]
                for r in residents
                for b in week_blocks
                for t in self._get_rotation_templates()
                if (r.id, b.id, t.id) in variables
            ]

            total_assigned = sum(week_assignments)

            # Available capacity (residents * blocks per week)
            capacity = len(residents) * len(week_blocks)

            # Target utilization (0.75)
            target_assignments = int(capacity * 0.75)

            # Deviation from target
            deviation = model.NewIntVar(-capacity, capacity, f"util_dev_week")
            model.Add(deviation == total_assigned - target_assignments)

            # Absolute deviation (for penalty)
            abs_dev = model.NewIntVar(0, capacity, f"util_abs_dev_week")
            model.AddAbsEquality(abs_dev, deviation)

            penalty_vars.append(abs_dev)

        # Total penalty across horizon
        return sum(penalty_vars)

    def _create_preference_objective(self, model, variables, residents, blocks, templates):
        """
        Create objective terms from stigmergy preference trails.

        Integrates with existing stigmergy system for preference-aware MPC.
        """
        from app.resilience.stigmergy import TrailType

        # Get stigmergy preference data
        stigmergy = self.state_model.get_stigmergy_scheduler()

        bonus_vars = []

        for resident in residents:
            # Get preference trails for this resident
            pref_trails = stigmergy.get_faculty_preferences(
                resident.id,
                trail_type=TrailType.PREFERENCE,
                min_strength=0.2
            )

            avoid_trails = stigmergy.get_faculty_preferences(
                resident.id,
                trail_type=TrailType.AVOIDANCE,
                min_strength=0.2
            )

            # Create preference variables
            for block in blocks:
                for template in templates:
                    if (resident.id, block.id, template.id) not in variables:
                        continue

                    var = variables[(resident.id, block.id, template.id)]

                    # Check if this assignment matches preferences
                    pref_strength = 0.0
                    for trail in pref_trails:
                        if self._trail_matches(trail, block, template):
                            pref_strength += trail.strength

                    avoid_strength = 0.0
                    for trail in avoid_trails:
                        if self._trail_matches(trail, block, template):
                            avoid_strength += trail.strength

                    # Net preference (positive = preferred, negative = avoided)
                    net_pref = pref_strength - avoid_strength

                    # Convert to integer for CP-SAT
                    pref_score = int(net_pref * 100)

                    # Preference bonus
                    pref_bonus = model.NewIntVar(-100, 100, f"pref_{resident.id}_{block.id}")
                    model.Add(pref_bonus == var * pref_score)

                    bonus_vars.append(pref_bonus)

        return sum(bonus_vars)


class ScheduleStateModel:
    """
    Model of schedule system dynamics for MPC prediction.

    Predicts how state evolves based on assignments:
    - Utilization changes
    - Workload distribution
    - Coverage gaps
    - Faculty stress accumulation
    """

    def update(self, current_state: dict, assignments: list) -> dict:
        """Update state based on executed assignments."""
        new_state = current_state.copy()

        # Update utilization
        for faculty_id, workload in self._calculate_workloads(assignments).items():
            new_state.setdefault('utilization', {})[faculty_id] = workload

        # Update coverage
        new_state['coverage_rate'] = self._calculate_coverage(assignments)

        # Update stress (cumulative)
        new_state['stress'] = self._calculate_stress(current_state, assignments)

        return new_state

    def predict(self, current_state: dict, planned_assignments: list, end_date: date) -> dict:
        """Predict future state at end of horizon."""
        # Start from current
        predicted_state = current_state.copy()

        # Apply assignments
        predicted_state = self.update(predicted_state, planned_assignments)

        # Model natural dynamics (stress decay, etc.)
        days_ahead = (end_date - datetime.now().date()).days
        stress_decay = 0.95 ** (days_ahead / 7)  # Decay per week

        if 'stress' in predicted_state:
            predicted_state['stress'] *= stress_decay

        return predicted_state
```

#### Use Case 2: Real-Time Schedule Adjustment

**Problem:** When emergencies occur (faculty absence, illness), need to quickly reoptimize remaining schedule.

**MPC Replanning:**

```python
class EmergencyMPCReplanner:
    """
    Use MPC to replan schedule after disruptions.

    When a faculty member calls in sick or deploys, reoptimize
    the next 2-4 weeks while minimizing changes to existing schedule.
    """

    def __init__(self, mpc_scheduler: MPCScheduler):
        self.mpc = mpc_scheduler

    def replan_after_absence(
        self,
        absent_faculty_id: UUID,
        absence_start: date,
        absence_end: date,
        current_schedule: list[Assignment],
    ) -> dict:
        """
        Replan schedule after unexpected absence.

        Args:
            absent_faculty_id: Faculty who is absent
            absence_start: Start of absence
            absence_end: End of absence
            current_schedule: Current assignments

        Returns:
            Dict with new_assignments, removed_assignments, change_summary
        """
        # Filter out assignments for absent faculty
        valid_assignments = [
            a for a in current_schedule
            if a.person_id != absent_faculty_id or a.block.date < absence_start
        ]

        affected_assignments = [
            a for a in current_schedule
            if a.person_id == absent_faculty_id and absence_start <= a.block.date <= absence_end
        ]

        # Current state
        current_state = {
            'existing_assignments': valid_assignments,
            'disrupted_blocks': [a.block for a in affected_assignments],
        }

        # Run MPC to fill gaps
        # Add penalty for changing existing assignments (stability)
        self.mpc.weights['setup_cost'] = 100.0  # High penalty for changes

        new_assignments = self.mpc.generate_schedule(
            start_date=absence_start,
            end_date=absence_end + timedelta(days=7),  # Extra week buffer
            initial_state=current_state,
            constraints=self._get_emergency_constraints(),
        )

        return {
            'new_assignments': new_assignments,
            'removed_assignments': affected_assignments,
            'change_count': len(new_assignments),
            'affected_blocks': len(affected_assignments),
            'replanning_cost': self._calculate_disruption_cost(affected_assignments, new_assignments),
        }
```

### Key Parameters for Tuning

| Parameter | Typical Range | Effect | Tuning Guidance |
|-----------|---------------|--------|-----------------|
| **Prediction Horizon (N)** | 2-8 weeks | How far ahead to look | Longer = better decisions but slower solve |
| **Control Horizon** | 1-4 weeks | How many weeks to commit | Shorter = more adaptive but more frequent solves |
| **Objective Weights** | 1-100 | Relative importance | Coverage should be highest, preferences lower |
| **Solve Time Limit** | 10-60 sec | Max optimization time | Real-time MPC needs fast solves (≤30s) |

---

## 4. Adaptive Control (Self-Tuning Systems)

### Core Principle

Adaptive control systems automatically adjust their parameters based on system performance, enabling them to handle changing dynamics and unknown parameters.

**Types:**
1. **Model Reference Adaptive Control (MRAC):** System tracks a reference model
2. **Self-Tuning Regulators:** Parameters updated using recursive estimation
3. **Gain Scheduling:** Switch parameters based on operating point

**Mathematical Foundation (MRAC):**

```
e(t) = y(t) - y_m(t)    # Error between actual and reference model

θ̇ = -Γ·e·φ             # Parameter update law (gradient descent)

Where:
- y(t) = system output
- y_m(t) = reference model output
- θ = adaptive parameters
- Γ = adaptation gain
- φ = regressor vector
```

### Application to Residency Scheduling

#### Use Case 1: Self-Tuning Constraint Weights

**Problem:** Optimal constraint weights depend on current system state (crisis vs normal). Hand-tuning is tedious.

**Adaptive Constraint Weighting:**

```python
class AdaptiveConstraintWeights:
    """
    Automatically adjust constraint weights based on schedule performance.

    Learns optimal weights through:
    1. Measure schedule quality after generation
    2. Compare to reference (ideal schedule metrics)
    3. Adjust weights using gradient descent
    """

    def __init__(
        self,
        initial_weights: dict,
        reference_metrics: dict,
        learning_rate: float = 0.1,
    ):
        self.weights = initial_weights.copy()
        self.reference = reference_metrics  # Ideal target metrics
        self.learning_rate = learning_rate

        # History for learning
        self.weight_history: list[dict] = []
        self.performance_history: list[dict] = []

        # Adaptation gains (different for each constraint type)
        self.gains = {
            'coverage': 0.5,        # Adapt quickly - critical
            'utilization': 0.3,     # Moderate adaptation
            'preferences': 0.1,     # Adapt slowly - less critical
            'workload_balance': 0.2,
        }

    def adapt_weights(self, schedule_metrics: dict) -> dict:
        """
        Adapt constraint weights based on schedule performance.

        Args:
            schedule_metrics: Actual metrics from generated schedule
                {
                    'coverage_rate': 0.92,
                    'utilization_rate': 0.78,
                    'workload_std': 0.18,
                    'preference_satisfaction': 0.65,
                }

        Returns:
            Updated weights dict
        """
        # Calculate errors from reference
        errors = {}
        for metric, target in self.reference.items():
            actual = schedule_metrics.get(metric, 0.0)
            errors[metric] = target - actual

        # Update weights using gradient descent
        for constraint_name, weight in self.weights.items():
            # Map constraint to metric
            metric = self._constraint_to_metric(constraint_name)
            if metric not in errors:
                continue

            error = errors[metric]
            gain = self.gains.get(metric, 0.1)

            # Gradient: if error is positive (underperforming), increase weight
            # If error is negative (overperforming), decrease weight
            delta = self.learning_rate * gain * error

            # Update with bounds
            new_weight = max(1.0, min(100.0, weight + delta))
            self.weights[constraint_name] = new_weight

            logger.info(
                f"Adapted {constraint_name}: {weight:.1f} -> {new_weight:.1f} "
                f"(error: {error:+.3f})"
            )

        # Record history
        self.weight_history.append(self.weights.copy())
        self.performance_history.append(schedule_metrics.copy())

        return self.weights.copy()

    def _constraint_to_metric(self, constraint_name: str) -> str:
        """Map constraint names to metrics."""
        mapping = {
            'coverage': 'coverage_rate',
            'utilization': 'utilization_rate',
            'workload_balance': 'workload_std',
            'preference': 'preference_satisfaction',
        }
        return mapping.get(constraint_name, constraint_name)

    def get_weight_trajectory(self) -> dict:
        """Get history of weight evolution for analysis."""
        return {
            'iterations': len(self.weight_history),
            'current_weights': self.weights,
            'initial_weights': self.weight_history[0] if self.weight_history else {},
            'convergence': self._check_convergence(),
        }

    def _check_convergence(self, window: int = 5, threshold: float = 0.05) -> bool:
        """Check if weights have converged."""
        if len(self.weight_history) < window:
            return False

        recent = self.weight_history[-window:]

        # Check variance of each weight
        for constraint_name in self.weights.keys():
            values = [h[constraint_name] for h in recent]
            if len(values) < 2:
                continue

            variance = statistics.variance(values)
            mean = statistics.mean(values)

            # Coefficient of variation
            cv = variance / mean if mean > 0 else 0

            if cv > threshold:
                return False  # Still changing significantly

        return True  # All weights stable
```

#### Use Case 2: Adaptive PID Tuning

**Problem:** PID gains that work in normal conditions may be suboptimal during crisis.

**Gain Scheduling + Self-Tuning:**

```python
class AdaptivePIDController:
    """
    PID controller with adaptive gains based on operating conditions.

    Combines:
    1. Gain scheduling (switch gains based on system state)
    2. Self-tuning (automatically adjust gains from performance)
    """

    def __init__(self, setpoint: float):
        self.setpoint = setpoint

        # Operating regimes with pre-tuned gains
        self.gain_schedules = {
            'normal': {'Kp': 10.0, 'Ki': 0.5, 'Kd': 2.0},
            'stressed': {'Kp': 15.0, 'Ki': 1.0, 'Kd': 3.0},  # More aggressive
            'crisis': {'Kp': 20.0, 'Ki': 2.0, 'Kd': 1.0},     # Fast response, less damping
            'recovery': {'Kp': 5.0, 'Ki': 0.3, 'Kd': 4.0},    # Gentle, avoid overshoot
        }

        # Current gains (start with normal)
        self.gains = self.gain_schedules['normal'].copy()
        self.current_regime = 'normal'

        # Self-tuning parameters
        self.adaptation_enabled = True
        self.adaptation_rate = 0.05

        # PID state
        self.integral = 0.0
        self.previous_error = 0.0

        # Performance tracking
        self.ise = 0.0  # Integral squared error
        self.performance_window: list[float] = []

    def update(self, current_value: float, system_state: dict) -> dict:
        """
        Update control with adaptive gains.

        Args:
            current_value: Current process variable
            system_state: Current system state (for regime detection)

        Returns:
            Control result with adaptive gain info
        """
        # 1. Determine operating regime (gain scheduling)
        new_regime = self._detect_regime(system_state)
        if new_regime != self.current_regime:
            logger.info(f"Switching regime: {self.current_regime} -> {new_regime}")
            self.current_regime = new_regime
            # Load scheduled gains for this regime
            self.gains = self.gain_schedules[new_regime].copy()

        # 2. Calculate PID control
        error = self.setpoint - current_value

        P = self.gains['Kp'] * error

        self.integral += error
        I = self.gains['Ki'] * self.integral

        derivative = error - self.previous_error
        D = self.gains['Kd'] * derivative

        control_signal = P + I + D

        # 3. Track performance
        self.ise += error ** 2
        self.performance_window.append(abs(error))
        if len(self.performance_window) > 20:
            self.performance_window.pop(0)

        # 4. Self-tune gains if enabled
        if self.adaptation_enabled and len(self.performance_window) >= 10:
            self._self_tune_gains(error, derivative)

        self.previous_error = error

        return {
            'control_signal': control_signal,
            'regime': self.current_regime,
            'gains': self.gains.copy(),
            'performance_ise': self.ise,
            'error': error,
        }

    def _detect_regime(self, system_state: dict) -> str:
        """
        Detect current operating regime from system state.

        Args:
            system_state: {
                'utilization': float,
                'coverage_rate': float,
                'active_stresses': int,
                'days_since_crisis': int,
            }
        """
        utilization = system_state.get('utilization', 0.75)
        coverage = system_state.get('coverage_rate', 0.95)
        stresses = system_state.get('active_stresses', 0)
        days_since_crisis = system_state.get('days_since_crisis', 999)

        # Crisis: high utilization, low coverage, or active stresses
        if utilization > 0.85 or coverage < 0.80 or stresses > 2:
            return 'crisis'

        # Recovery: recently exited crisis
        if days_since_crisis < 14:
            return 'recovery'

        # Stressed: approaching limits
        if utilization > 0.75 or coverage < 0.90:
            return 'stressed'

        # Normal: healthy operation
        return 'normal'

    def _self_tune_gains(self, error: float, derivative: float):
        """
        Self-tune gains using MIT rule (Model Reference Adaptive Control).

        Adjusts gains to minimize error while maintaining stability.
        """
        # Calculate recent performance
        recent_error_mean = statistics.mean(self.performance_window)

        # MIT rule: adjust proportional gain based on error magnitude
        if abs(error) > 0.1:  # Only adapt if error is significant
            # If error is large and positive, need stronger response
            kp_adjustment = self.adaptation_rate * error * error
            self.gains['Kp'] = max(1.0, min(30.0, self.gains['Kp'] + kp_adjustment))

        # Adjust integral gain based on steady-state error
        if len(self.performance_window) >= 20:
            steady_state_error = statistics.mean(self.performance_window[-5:])
            if abs(steady_state_error) > 0.05:
                ki_adjustment = self.adaptation_rate * steady_state_error
                self.gains['Ki'] = max(0.1, min(5.0, self.gains['Ki'] + ki_adjustment))

        # Adjust derivative gain based on oscillation
        oscillation = self._detect_oscillation_magnitude()
        if oscillation > 0.3:  # High oscillation
            # Increase damping
            self.gains['Kd'] *= 1.1
        elif oscillation < 0.1:  # Very stable
            # Can reduce damping for faster response
            self.gains['Kd'] *= 0.95

        # Clamp all gains to safe ranges
        self.gains['Kd'] = max(0.5, min(10.0, self.gains['Kd']))

    def _detect_oscillation_magnitude(self) -> float:
        """Calculate oscillation magnitude in recent errors."""
        if len(self.performance_window) < 6:
            return 0.0

        recent = self.performance_window[-6:]

        # Count zero crossings
        crossings = sum(
            1 for i in range(1, len(recent))
            if recent[i] * recent[i-1] < 0
        )

        # Normalize to 0-1
        return crossings / (len(recent) - 1)
```

### Key Parameters for Tuning

| Parameter | Typical Range | Effect | Tuning Guidance |
|-----------|---------------|--------|-----------------|
| **Learning Rate (γ)** | 0.01 - 0.5 | Speed of adaptation | Lower = stable but slow, Higher = fast but unstable |
| **Regime Thresholds** | Context-dependent | When to switch gains | Based on system characteristics |
| **Adaptation Window** | 10-50 samples | How much history for learning | Longer = smoother adaptation |
| **Bounds on Parameters** | Context-dependent | Prevent runaway adaptation | Critical for stability |

---

## 5. Sliding Mode Control (Robust Control Under Uncertainty)

### Core Principle

Sliding mode control (SMC) forces the system onto a "sliding surface" where desired dynamics hold, then maintains the system on that surface using discontinuous control. It's robust to uncertainties and disturbances.

**Mathematical Foundation:**

```
Sliding Surface:
s(x) = λ·e + ė = 0

Control Law:
u = u_eq + u_sw

u_eq = equivalent control (maintains sliding)
u_sw = -K·sign(s)   (switching control, drives to surface)

Where:
- s = sliding variable
- e = tracking error
- λ = sliding surface slope
- K = switching gain (must be large enough to overcome disturbances)
```

**Key Insight:** SMC is "chattering" control - it rapidly switches between states to maintain a desired manifold. The system becomes insensitive to matched disturbances once on the sliding surface.

### Application to Residency Scheduling

#### Use Case 1: Robust Coverage Maintenance

**Problem:** Coverage must be maintained despite uncertainties (call-ins, emergencies, delays). PID control can be slow to react.

**Sliding Mode Coverage Controller:**

```python
class SlidingModeCoverageController:
    """
    Sliding mode control for robust coverage maintenance.

    Maintains coverage on sliding surface: λ·e + ė = 0
    where e = target_coverage - actual_coverage

    Advantages over PID:
    - Finite-time convergence (reaches target faster)
    - Robust to disturbances (faculty absences)
    - Guaranteed stability

    Disadvantage:
    - "Chattering" (rapid switching of assignments)
    """

    def __init__(
        self,
        target_coverage: float = 0.95,
        lambda_param: float = 2.0,    # Sliding surface slope
        switching_gain: float = 5.0,   # Must overcome max disturbance
        boundary_layer: float = 0.02,  # Smooth chattering
    ):
        self.target = target_coverage
        self.lambda_param = lambda_param
        self.K = switching_gain
        self.phi = boundary_layer  # Boundary layer thickness

        # State
        self.previous_error = 0.0
        self.previous_time = datetime.now()

        # Chattering detection
        self.control_switches = 0

    def update(self, current_coverage: float, dt: float = 1.0) -> dict:
        """
        Calculate sliding mode control signal.

        Args:
            current_coverage: Current coverage rate (0-1)
            dt: Time step (days)

        Returns:
            Control result with sliding mode diagnostics
        """
        # Tracking error
        error = self.target - current_coverage

        # Error derivative (finite difference)
        error_dot = (error - self.previous_error) / dt if dt > 0 else 0.0

        # Sliding surface
        s = self.lambda_param * error + error_dot

        # Equivalent control (linear part, maintains sliding)
        # For simple first-order system: u_eq = -λ·e
        u_eq = -self.lambda_param * error

        # Switching control (nonlinear part, drives to surface)
        # Use smooth sat() function instead of sign() to reduce chattering
        u_sw = -self.K * self._smooth_sat(s, self.phi)

        # Total control
        control_signal = u_eq + u_sw

        # Interpret control (how many assignments to add/remove)
        action = self._interpret_control(control_signal, current_coverage)

        # Detect chattering
        if abs(s) < self.phi:
            chattering = False
        else:
            chattering = True
            if np.sign(s) != np.sign(self.previous_error):
                self.control_switches += 1

        self.previous_error = error

        return {
            'error': error,
            'error_dot': error_dot,
            'sliding_variable': s,
            'on_sliding_surface': abs(s) < self.phi,
            'u_equivalent': u_eq,
            'u_switching': u_sw,
            'control_signal': control_signal,
            'action': action,
            'chattering_detected': chattering,
            'switch_count': self.control_switches,
        }

    def _smooth_sat(self, s: float, phi: float) -> float:
        """
        Smooth saturation function to reduce chattering.

        sat(s, φ) = {
            s/φ      if |s| ≤ φ   (inside boundary layer)
            sign(s)  if |s| > φ   (outside boundary layer)
        }
        """
        if abs(s) <= phi:
            return s / phi
        else:
            return np.sign(s)

    def _interpret_control(self, signal: float, current_coverage: float) -> dict:
        """
        Convert SMC control signal to scheduling actions.

        Positive signal = need more coverage (add assignments)
        Negative signal = too much coverage (can remove some)
        """
        # Scale signal to assignments (each assignment ≈ 0.01 coverage)
        assignments_delta = int(signal / 0.01)

        if abs(signal) < 0.05:
            return {
                'type': 'maintain',
                'description': 'On sliding surface - maintain current coverage',
                'delta': 0,
                'urgency': 'low',
            }
        elif signal > 0:
            # Need more coverage
            return {
                'type': 'add_coverage',
                'description': f'Add ~{assignments_delta} assignments to increase coverage',
                'delta': assignments_delta,
                'urgency': 'high' if signal > 0.2 else 'medium',
            }
        else:
            # Excess coverage
            return {
                'type': 'reduce_coverage',
                'description': f'Can remove ~{abs(assignments_delta)} assignments',
                'delta': assignments_delta,
                'urgency': 'low',
            }

    def design_switching_gain(self, max_disturbance: float, safety_factor: float = 1.5):
        """
        Design switching gain to overcome worst-case disturbance.

        Args:
            max_disturbance: Maximum coverage loss rate (e.g., 0.1 = 10% per day)
            safety_factor: Multiplier for robustness

        Rule: K > max_disturbance for guaranteed reaching
        """
        self.K = max_disturbance * safety_factor
        logger.info(f"Switching gain set to {self.K:.2f} (max disturbance: {max_disturbance:.2f})")
```

#### Use Case 2: Crisis Mode Sliding Surface

**Problem:** During crisis, system must quickly reach safe operating point and stay there.

**Multi-Surface Sliding Mode:**

```python
class CrisisModeSlidingController:
    """
    Multi-surface sliding mode control for crisis management.

    Uses multiple sliding surfaces for different objectives:
    1. Primary surface: coverage ≥ minimum
    2. Secondary surface: utilization ≤ maximum
    3. Tertiary surface: workload balance

    Prioritized sliding - higher priority surfaces take precedence.
    """

    def __init__(self):
        # Primary surface (CRITICAL): Minimum coverage
        self.s1_controller = SlidingModeCoverageController(
            target_coverage=0.85,  # Lower target for crisis
            lambda_param=3.0,      # Fast convergence
            switching_gain=10.0,   # Strong control
        )

        # Secondary surface (HIGH): Maximum utilization
        self.s2_controller = SlidingModeUtilizationController(
            target_utilization=0.80,  # Hard limit
            lambda_param=2.0,
            switching_gain=7.0,
        )

        # Tertiary surface (MEDIUM): Workload balance
        self.s3_controller = SlidingModeBalanceController(
            target_std=0.20,  # Relaxed during crisis
            lambda_param=1.0,
            switching_gain=3.0,
        )

    def crisis_update(
        self,
        coverage: float,
        utilization: float,
        workload_std: float,
    ) -> dict:
        """
        Multi-objective sliding mode control for crisis.

        Prioritizes surfaces: coverage > utilization > balance
        """
        # Primary: Coverage (must satisfy first)
        s1_result = self.s1_controller.update(coverage)

        # Check if on primary surface
        if not s1_result['on_sliding_surface']:
            # Not on primary surface - focus only on that
            return {
                'priority': 'CRITICAL',
                'focus': 'coverage',
                'action': s1_result['action'],
                's1': s1_result,
                's2': None,
                's3': None,
            }

        # On primary surface - check secondary
        s2_result = self.s2_controller.update(utilization)

        if not s2_result['on_sliding_surface']:
            # On coverage, not on utilization
            return {
                'priority': 'HIGH',
                'focus': 'utilization',
                'action': s2_result['action'],
                's1': s1_result,
                's2': s2_result,
                's3': None,
            }

        # On both primary and secondary - optimize tertiary
        s3_result = self.s3_controller.update(workload_std)

        return {
            'priority': 'MEDIUM',
            'focus': 'balance',
            'action': s3_result['action'],
            's1': s1_result,
            's2': s2_result,
            's3': s3_result,
        }
```

### Key Parameters for Tuning

| Parameter | Typical Range | Effect | Tuning Guidance |
|-----------|---------------|--------|-----------------|
| **λ (Slope)** | 0.5 - 5.0 | Convergence speed on surface | Higher = faster reaching, may overshoot |
| **K (Switching Gain)** | Max disturbance × 1.5-3.0 | Robustness | Must be larger than disturbances |
| **φ (Boundary Layer)** | 0.01 - 0.1 | Chattering reduction | Larger = smoother but less precise |

**Chattering Mitigation:**
1. Use boundary layer (smooth saturation)
2. Higher-order sliding modes
3. Observer-based disturbance estimation

---

## 6. Smith Predictor (Handling Time Delays in Feedback)

### Core Principle

Smith Predictor compensates for time delays in feedback loops by using a model to predict what the output will be, allowing the controller to act on predicted rather than delayed measurements.

**Mathematical Foundation:**

```
Standard feedback with delay:
y(t) = G(s)·u(t - τ)     # Output delayed by τ

Smith Predictor structure:
Controller sees: y_pred(t) = ŷ(t) + [y(t-τ) - ŷ(t-τ)]
                              ↑         ↑
                        prediction  correction

Where:
- ŷ(t) = model prediction (no delay)
- y(t-τ) = actual delayed measurement
- ŷ(t-τ) = what model predicted τ time ago
"""

**Key Insight:** By predicting the current state from an internal model and correcting with delayed measurements, the controller can act as if there's no delay.

### Application to Residency Scheduling

#### Use Case 1: Schedule Quality Feedback Delay

**Problem:** The true quality of a schedule (workload balance, burnout prevention) only becomes apparent weeks after implementation. By the time you measure problems, it's too late.

**Smith Predictor for Schedule Quality:**

```python
class ScheduleQualitySmithPredictor:
    """
    Smith Predictor for schedule quality with feedback delay.

    Problem: Schedule quality metrics (burnout, satisfaction) have
    2-4 week delay before they're measurable. By the time we see
    the problem, we've already scheduled 2 more weeks badly.

    Solution: Use model to predict quality immediately, then correct
    with delayed measurements when they arrive.
    """

    def __init__(
        self,
        delay_weeks: int = 3,    # How long until quality is measurable
        prediction_model: callable = None,
    ):
        self.delay_weeks = delay_weeks
        self.prediction_model = prediction_model or self._default_quality_model

        # Delayed measurement buffer
        self.delayed_measurements: deque = deque(maxlen=delay_weeks)
        self.delayed_predictions: deque = deque(maxlen=delay_weeks)

        # State
        self.current_prediction = 0.7  # Initial quality estimate
        self.prediction_history: list[tuple[date, float]] = []

        # Controller (operates on predicted quality)
        self.controller = UtilizationPIDController(
            setpoint=0.8,  # Target schedule quality
            Kp=10.0,
            Ki=0.5,
            Kd=2.0,
        )

    def update(
        self,
        schedule_params: dict,
        delayed_measurement: float = None,
        measurement_date: date = None,
    ) -> dict:
        """
        Update Smith Predictor with new schedule and delayed measurement.

        Args:
            schedule_params: Current schedule parameters for prediction
                {
                    'utilization': float,
                    'workload_variance': float,
                    'preference_match': float,
                    'continuous_days': float,
                }
            delayed_measurement: Actual quality measured delay_weeks ago
            measurement_date: Date of the delayed measurement

        Returns:
            Control action based on predicted quality
        """
        today = datetime.now().date()

        # 1. Make prediction for current schedule
        current_prediction = self.prediction_model(schedule_params)

        # 2. Store prediction (for later correction)
        self.delayed_predictions.append((today, current_prediction))

        # 3. If we have a delayed measurement, compute correction
        correction = 0.0
        if delayed_measurement is not None and measurement_date is not None:
            # Find what we predicted for that date
            predicted_then = self._get_prediction_for_date(measurement_date)

            if predicted_then is not None:
                # Correction = actual - predicted (model error)
                correction = delayed_measurement - predicted_then

                logger.info(
                    f"Smith Predictor correction: "
                    f"predicted={predicted_then:.3f}, actual={delayed_measurement:.3f}, "
                    f"error={correction:+.3f}"
                )

        # 4. Corrected estimate (Smith Predictor formula)
        # y_corrected = y_predicted + [y_delayed - y_predicted_delayed]
        corrected_quality = current_prediction + correction

        # 5. Use corrected estimate for control
        control_result = self.controller.update(corrected_quality)

        # 6. Store history
        self.prediction_history.append((today, current_prediction))
        if delayed_measurement is not None:
            self.delayed_measurements.append((measurement_date, delayed_measurement))

        return {
            'predicted_quality': current_prediction,
            'correction': correction,
            'corrected_quality': corrected_quality,
            'control_action': control_result['action'],
            'control_signal': control_result['control_signal'],
            'model_accuracy': self._calculate_model_accuracy(),
        }

    def _default_quality_model(self, params: dict) -> float:
        """
        Default prediction model for schedule quality.

        Simple weighted model:
        - High utilization reduces quality
        - High workload variance reduces quality
        - Good preference matching improves quality
        - Too many continuous days reduces quality
        """
        quality = 0.5  # Base

        util = params.get('utilization', 0.75)
        variance = params.get('workload_variance', 0.15)
        preference = params.get('preference_match', 0.6)
        continuous = params.get('continuous_days', 5.0)

        # Utilization impact (optimal at 0.75)
        util_penalty = abs(util - 0.75) * 2.0
        quality -= util_penalty

        # Variance impact (lower is better)
        variance_penalty = variance * 1.5
        quality -= variance_penalty

        # Preference bonus
        preference_bonus = preference * 0.3
        quality += preference_bonus

        # Continuous days penalty (>5 days is tiring)
        if continuous > 5:
            continuous_penalty = (continuous - 5) * 0.05
            quality -= continuous_penalty

        # Clamp to [0, 1]
        return max(0.0, min(1.0, quality))

    def _get_prediction_for_date(self, target_date: date) -> float | None:
        """Retrieve prediction made for a specific date."""
        for pred_date, pred_value in self.delayed_predictions:
            if pred_date == target_date:
                return pred_value
        return None

    def _calculate_model_accuracy(self) -> dict:
        """Calculate how accurate our prediction model is."""
        if len(self.delayed_measurements) < 3:
            return {'ready': False}

        errors = []
        for meas_date, actual in self.delayed_measurements:
            predicted = self._get_prediction_for_date(meas_date)
            if predicted is not None:
                errors.append(actual - predicted)

        if not errors:
            return {'ready': False}

        mae = statistics.mean([abs(e) for e in errors])
        bias = statistics.mean(errors)
        rmse = math.sqrt(statistics.mean([e**2 for e in errors]))

        return {
            'ready': True,
            'mean_absolute_error': mae,
            'bias': bias,  # Systematic over/under prediction
            'rmse': rmse,
            'sample_size': len(errors),
        }

    def improve_model(self):
        """
        Use accumulated measurements to improve prediction model.

        This learns from prediction errors to make better future predictions.
        (Could use machine learning here)
        """
        if len(self.delayed_measurements) < 10:
            logger.info("Not enough data to improve model yet")
            return

        # Analyze systematic errors
        accuracy = self._calculate_model_accuracy()

        if accuracy['bias'] > 0.1:
            logger.info(f"Model is under-predicting by {accuracy['bias']:.3f} on average")
            # Could adjust model parameters here
        elif accuracy['bias'] < -0.1:
            logger.info(f"Model is over-predicting by {abs(accuracy['bias']):.3f} on average")
```

#### Use Case 2: Delayed ACGME Violations

**Problem:** ACGME violations (80-hour rule, 1-in-7 rule) are measured over 4-week rolling windows. By the time you detect a violation, it's already happened.

**Predictive ACGME Compliance:**

```python
class ACGMESmithPredictor:
    """
    Predict ACGME compliance before the measurement window closes.

    80-Hour Rule: Measured over rolling 4-week periods
    Delay: Up to 4 weeks before violation is confirmed

    Smith Predictor: Forecast hours in current window,
    take action before violation occurs.
    """

    def __init__(self):
        self.delay_weeks = 4  # ACGME measurement window

        # Model of how hours accumulate
        self.hours_model = HoursAccumulationModel()

        # Delayed compliance measurements
        self.delayed_compliance: deque = deque(maxlen=10)

        # Predictor state
        self.predicted_windows: deque = deque(maxlen=delay_weeks)

    def predict_compliance(
        self,
        faculty_id: UUID,
        current_assignments: list,
        planned_assignments: list,
    ) -> dict:
        """
        Predict if faculty will violate 80-hour rule in current window.

        Args:
            faculty_id: Faculty to check
            current_assignments: Completed assignments in current 4-week window
            planned_assignments: Planned assignments for rest of window

        Returns:
            Prediction with preemptive warning
        """
        # Calculate hours so far
        hours_completed = sum(a.hours for a in current_assignments)

        # Predict hours for planned assignments
        hours_predicted = self.hours_model.predict_hours(planned_assignments)

        # Total predicted hours for window
        total_predicted = hours_completed + hours_predicted

        # Average per week
        weeks_in_window = 4
        avg_hours_per_week = total_predicted / weeks_in_window

        # Check compliance
        will_violate = avg_hours_per_week > 80.0
        margin = 80.0 - avg_hours_per_week

        # If we predict violation, recommend action NOW
        if will_violate:
            action = {
                'type': 'preemptive_reduction',
                'description': f'Reduce hours by {abs(margin):.1f}/week to avoid violation',
                'urgency': 'immediate',
                'weeks_remaining': self._weeks_remaining_in_window(current_assignments),
            }
        else:
            action = {
                'type': 'maintain',
                'description': f'Projected {margin:.1f} hours/week buffer remaining',
                'urgency': 'low',
            }

        # Store prediction for later validation
        self.predicted_windows.append({
            'faculty_id': faculty_id,
            'prediction_date': datetime.now().date(),
            'predicted_hours': total_predicted,
            'predicted_violation': will_violate,
        })

        return {
            'predicted_avg_hours': avg_hours_per_week,
            'will_violate_80h': will_violate,
            'margin': margin,
            'confidence': self.hours_model.get_confidence(),
            'action': action,
        }

    def validate_prediction(
        self,
        faculty_id: UUID,
        window_end_date: date,
        actual_hours: float,
    ):
        """
        When window closes, validate our prediction and improve model.

        This is the delayed measurement that improves future predictions.
        """
        # Find prediction for this window
        for pred in self.predicted_windows:
            if (pred['faculty_id'] == faculty_id and
                self._is_same_window(pred['prediction_date'], window_end_date)):

                error = actual_hours - pred['predicted_hours']

                logger.info(
                    f"ACGME prediction validation: "
                    f"predicted={pred['predicted_hours']:.1f}, "
                    f"actual={actual_hours:.1f}, "
                    f"error={error:+.1f} hours"
                )

                # Update model with this error
                self.hours_model.learn_from_error(error)

                # Record for statistics
                self.delayed_compliance.append({
                    'faculty_id': faculty_id,
                    'date': window_end_date,
                    'actual_hours': actual_hours,
                    'predicted_hours': pred['predicted_hours'],
                    'error': error,
                })

                break


class HoursAccumulationModel:
    """
    Model for predicting hours from planned assignments.

    Learns from historical data how long different assignment types
    actually take (including variance).
    """

    def __init__(self):
        # Historical average hours by rotation type
        self.rotation_hours = {
            'clinic': 8.0,
            'inpatient': 12.0,
            'procedure': 10.0,
            'call': 16.0,
        }

        # Variance (for uncertainty quantification)
        self.rotation_std = {
            'clinic': 1.0,
            'inpatient': 2.5,
            'procedure': 2.0,
            'call': 3.0,
        }

        # Model confidence (improves with more data)
        self.prediction_count = 0
        self.error_history: list[float] = []

    def predict_hours(self, assignments: list) -> float:
        """Predict total hours for list of assignments."""
        total = 0.0
        for assignment in assignments:
            rotation_type = getattr(assignment, 'rotation_type', 'clinic')
            base_hours = self.rotation_hours.get(rotation_type, 8.0)
            total += base_hours

        return total

    def get_confidence(self) -> float:
        """Get prediction confidence (0-1)."""
        if self.prediction_count < 5:
            return 0.5  # Low confidence initially

        # Confidence based on recent errors
        if len(self.error_history) < 3:
            return 0.7

        recent_mae = statistics.mean([abs(e) for e in self.error_history[-10:]])

        # Good predictions (MAE < 5 hours) = high confidence
        if recent_mae < 5.0:
            return 0.9
        elif recent_mae < 10.0:
            return 0.7
        else:
            return 0.5

    def learn_from_error(self, error: float):
        """Update model from prediction error."""
        self.error_history.append(error)
        self.prediction_count += 1

        # Could do more sophisticated learning here
        # (e.g., adjust rotation_hours based on systematic bias)
```

### Key Parameters for Tuning

| Parameter | Typical Range | Effect | Tuning Guidance |
|-----------|---------------|--------|-----------------|
| **Model Accuracy** | N/A | Prediction quality | Smith Predictor requires good model |
| **Delay Estimate (τ)** | Actual delay ± 20% | Compensation accuracy | Measure actual system delay carefully |
| **Model Update Rate** | Weekly - Monthly | Learning speed | Update as new data arrives |

**Critical Success Factor:** Smith Predictor REQUIRES an accurate model. If the model is poor, performance will be worse than standard feedback.

---

## Integration Strategy and Implementation Roadmap

### Phase 1: Foundation (Weeks 1-2)

1. **Implement PID Controllers**
   - Add `pid_control.py` to `/backend/app/resilience/`
   - Create `PIDControllerBank` class
   - Integrate with existing `HomeostasisMonitor`
   - Add PID dashboard to monitoring UI

2. **Kalman Filter for Workload Estimation**
   - Add `kalman_filters.py`
   - Implement `WorkloadKalmanFilter`
   - Integrate with existing metrics collection

### Phase 2: Advanced Control (Weeks 3-4)

3. **Model Predictive Control**
   - Add `mpc_scheduler.py`
   - Integrate with existing constraint system
   - Add receding horizon option to schedule generation

4. **Adaptive Weights**
   - Add `adaptive_control.py`
   - Implement `AdaptiveConstraintWeights`
   - Connect to constraint manager

### Phase 3: Robustness (Weeks 5-6)

5. **Sliding Mode Control**
   - Add `sliding_mode.py`
   - Implement crisis mode controllers
   - Integrate with defense-in-depth system

6. **Smith Predictor**
   - Add `smith_predictor.py`
   - Implement ACGME compliance predictor
   - Add delayed feedback handling

### Database Schema Additions

```python
# Add to backend/app/models/control_theory.py

class PIDControllerState(Base):
    """Track PID controller state over time."""
    __tablename__ = "pid_controller_states"

    id = Column(UUID, primary_key=True)
    controller_name = Column(String, index=True)
    timestamp = Column(DateTime, index=True)

    # State
    setpoint = Column(Float)
    process_variable = Column(Float)
    error = Column(Float)
    integral = Column(Float)
    derivative = Column(Float)

    # Gains
    Kp = Column(Float)
    Ki = Column(Float)
    Kd = Column(Float)

    # Output
    control_signal = Column(Float)
    saturated = Column(Boolean)


class KalmanFilterState(Base):
    """Track Kalman filter estimates."""
    __tablename__ = "kalman_filter_states"

    id = Column(UUID, primary_key=True)
    filter_name = Column(String, index=True)
<<<<<<< HEAD
    entity_id = Column(UUID)  # Faculty or system
=======
    entity_id = Column(UUID)  ***REMOVED*** or system
>>>>>>> origin/docs/session-14-summary
    timestamp = Column(DateTime, index=True)

    # Estimate
    estimated_value = Column(Float)
    uncertainty = Column(Float)  # sqrt(P[0,0])

    # Measurements
    measurement_value = Column(Float, nullable=True)
    innovation = Column(Float, nullable=True)

    # Diagnostics
    kalman_gain = Column(Float, nullable=True)


class AdaptiveWeightHistory(Base):
    """Track evolution of adaptive constraint weights."""
    __tablename__ = "adaptive_weight_history"

    id = Column(UUID, primary_key=True)
    timestamp = Column(DateTime, index=True)
    schedule_run_id = Column(UUID, ForeignKey("schedule_runs.id"))

    # Weights
    coverage_weight = Column(Float)
    utilization_weight = Column(Float)
    preference_weight = Column(Float)
    balance_weight = Column(Float)

    # Performance that led to these weights
    coverage_achieved = Column(Float)
    utilization_achieved = Column(Float)
    preference_satisfaction = Column(Float)
    workload_std = Column(Float)

    # Learning metrics
    learning_rate = Column(Float)
    converged = Column(Boolean)
```

---

## Comparative Analysis: When to Use Each Technique

| Technique | Best For | Complexity | Computational Cost | Robustness | Complementary To |
|-----------|----------|------------|-------------------|------------|------------------|
| **PID** | Setpoint tracking, real-time control | Low | Very Low | Medium | Homeostasis (enhances feedback loops) |
| **Kalman** | Noisy measurements, state estimation | Medium | Low | High | All (improves data quality) |
| **MPC** | Multi-objective optimization, constraints | High | High | Medium | Existing scheduler (receding horizon) |
| **Adaptive** | Changing dynamics, unknown parameters | Medium | Medium | High | PID, MPC (parameter tuning) |
| **Sliding Mode** | Crisis situations, robustness | Medium | Low | Very High | Defense-in-depth (crisis control) |
| **Smith Predictor** | Delayed feedback, prediction | High | Medium | Medium | ACGME validation (early warning) |

### Decision Tree for Selecting Control Method

```
Need real-time tracking of metrics?
├─ Yes: Start with PID
│  ├─ Noisy measurements? → Add Kalman Filter
│  ├─ Changing conditions? → Add Adaptive gains
│  └─ Crisis robustness? → Add Sliding Mode
└─ No: Planning/optimization problem
   ├─ Multiple conflicting objectives? → MPC
   ├─ Future uncertainty important? → MPC with robust constraints
   └─ Feedback delayed? → Smith Predictor

```

---

## Testing and Validation Plan

### Unit Tests

```python
# backend/tests/resilience/test_pid_control.py

def test_pid_reaches_setpoint():
    """Verify PID drives error to zero."""
    pid = UtilizationPIDController(setpoint=0.75)

    # Simulate system response
    utilization = 0.50  # Start low

    for _ in range(50):
        result = pid.update(utilization)
        # Simple plant model: utilization changes proportionally to control
        utilization += result['control_signal'] * 0.01

    # Should be close to setpoint
    assert abs(utilization - 0.75) < 0.05


def test_kalman_reduces_noise():
    """Verify Kalman filter smooths noisy measurements."""
    kf = WorkloadKalmanFilter(initial_hours=60.0)

    true_hours = 65.0
    noise_std = 5.0

    measurements = []
    estimates = []

    for i in range(20):
        # Noisy measurement
        measurement = true_hours + np.random.normal(0, noise_std)
        measurements.append(measurement)

        # Update filter
        result = kf.update({
            'self_report': measurement,
            'system_log': measurement + np.random.normal(0, 3.0),
        })

        estimates.append(result['estimated_hours'])

    # Estimate should be smoother (lower variance) than measurements
    meas_var = np.var(measurements)
    est_var = np.var(estimates[-10:])  # Last 10 after convergence

    assert est_var < meas_var * 0.5  # At least 50% noise reduction
```

### Integration Tests

```python
def test_pid_kalman_integration():
    """Test PID controller with Kalman-filtered measurements."""
    pid = UtilizationPIDController(setpoint=0.75)
    kf = WorkloadKalmanFilter()

    # Simulate system with noisy measurements
    true_utilization = 0.60

    for _ in range(30):
        # Noisy measurement
        measured = true_utilization + np.random.normal(0, 0.05)

        # Filter measurement
        filtered_result = kf.update({'self_report': measured})
        filtered_value = filtered_result['estimated_hours'] / 80.0  # Convert to utilization

        # Control on filtered value
        control = pid.update(filtered_value)

        # Update system
        true_utilization += control['control_signal'] * 0.01

    # Should converge despite noise
    assert abs(true_utilization - 0.75) < 0.10
```

---

## Conclusion

These six exotic control theory concepts provide complementary capabilities that enhance the existing homeostasis, Le Chatelier, and stigmergy systems:

1. **PID Controllers** add precise, tunable feedback control to setpoint tracking
2. **Kalman Filters** provide optimal state estimation from noisy, uncertain data
3. **Model Predictive Control** enables multi-objective optimization over future horizons
4. **Adaptive Control** allows self-tuning as system dynamics change
5. **Sliding Mode Control** provides robust crisis management with guaranteed performance
6. **Smith Predictor** handles delayed feedback for early intervention

**Recommended Implementation Order:**
1. PID (easy, immediate value)
2. Kalman (improves all measurements)
3. MPC (powerful scheduling enhancement)
4. Adaptive (long-term improvement)
5. Smith Predictor (specialized use cases)
6. Sliding Mode (advanced crisis control)

The integration creates a comprehensive control architecture that combines:
- **Biological inspiration** (homeostasis, Le Chatelier)
- **Swarm intelligence** (stigmergy)
- **Classical control** (PID, Kalman)
- **Modern control** (MPC, Adaptive, SMC)

This multi-paradigm approach provides resilience at multiple timescales and operational regimes, from normal operations through crisis response.
