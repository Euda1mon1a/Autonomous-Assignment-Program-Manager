"""
Integration tests for PID-Homeostasis Bridge.

Tests the formal PID control implementation for utilization, workload, and coverage
based on the PID_HOMEOSTASIS_BRIDGE.md specification.

Test Coverage:
1. test_proportional_response - P term only
2. test_integral_accumulation - I term accumulates error
3. test_derivative_anticipation - D term dampens overshoot
4. test_anti_windup - Integral saturation limits
5. test_step_response - Full PID step response
6. test_disturbance_rejection - Recovery from perturbation

PID Formula: u(t) = Kp×e + Ki×∫e + Kd×de/dt
where:
  - u(t) = control signal (correction magnitude)
  - e(t) = setpoint - measured_value (error)
  - Kp, Ki, Kd = tuned gains
"""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4

import numpy as np


# Mock PID implementation until backend/app/resilience/pid_control.py is created
# This will be replaced by actual imports once implementation exists
from dataclasses import dataclass, field


@dataclass
class PIDConfig:
    """Configuration for a PID controller."""

    name: str
    setpoint: float
    Kp: float  # Proportional gain
    Ki: float  # Integral gain
    Kd: float  # Derivative gain
    output_limits: tuple[float, float]  # Min, max control signal
    integral_limits: tuple[float, float] = (-5.0, 5.0)
    unit: str = ""
    description: str = ""


@dataclass
class PIDState:
    """State of a PID controller."""

    id: uuid4
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
            Dict with control signal and diagnostics
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
            self.config.integral_limits[1],
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
            raw_control, self.config.output_limits[0], self.config.output_limits[1]
        )

        # Track saturation
        integral_saturated = (
            abs(self.integral - self.config.integral_limits[1]) < 0.01
            or abs(self.integral - self.config.integral_limits[0]) < 0.01
        )
        output_saturated = abs(raw_control - control_signal) > 0.001

        if integral_saturated:
            self.saturation_count += 1

        # Update history
        self.error_history.append((now, error))
        self.control_history.append((now, control_signal))

        # Trim history
        if len(self.error_history) > self.max_history_size:
            self.error_history = self.error_history[-self.max_history_size :]
        if len(self.control_history) > self.max_history_size:
            self.control_history = self.control_history[-self.max_history_size :]

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
            1
            for i in range(1, len(recent_errors))
            if recent_errors[i] * recent_errors[i - 1] < 0
        )

        # Oscillating if more than half the intervals change sign
        return sign_changes > window // 2

    def reset(self):
        """Reset controller state."""
        self.integral = 0.0
        self.previous_error = 0.0
        self.previous_time = datetime.now()
        self.error_history.clear()
        self.control_history.clear()
        self.oscillation_count = 0
        self.saturation_count = 0

    def set_setpoint(self, new_setpoint: float):
        """Change setpoint and reset integral to prevent windup."""
        old_setpoint = self.config.setpoint
        self.config.setpoint = new_setpoint

        if abs(new_setpoint - old_setpoint) > 0.01:
            # Significant setpoint change - reset integral
            self.integral = 0.0


class TestPIDController:
    """Test suite for PID controller mathematical correctness."""

    def test_proportional_response(self):
        """
        Test proportional term responds to error.

        P-only control (Ki=0, Kd=0) should produce immediate response
        proportional to error magnitude.

        Formula: u(t) = Kp × e(t)
        Expected: For error = -0.10 and Kp = 10.0, P = -1.0
        """
        config = PIDConfig(
            name="test_proportional",
            setpoint=0.75,
            Kp=10.0,
            Ki=0.0,  # Disable integral
            Kd=0.0,  # Disable derivative
            output_limits=(-1.0, 1.0),
        )
        controller = PIDState(id=uuid4(), config=config)

        # Error = setpoint - current = 0.75 - 0.85 = -0.10
        result = controller.update(0.85)

        # P = Kp × error = 10.0 × (-0.10) = -1.0
        assert result["P"] == pytest.approx(-1.0, abs=0.01), (
            f"Expected P=-1.0, got {result['P']}"
        )
        assert result["I"] == pytest.approx(0.0, abs=0.01), (
            "Integral term should be zero when Ki=0"
        )
        assert result["D"] == pytest.approx(0.0, abs=0.01), (
            "Derivative term should be zero when Kd=0"
        )
        assert result["control_signal"] == pytest.approx(-1.0, abs=0.01), (
            "Control signal should equal P term when I and D are disabled"
        )

        # Test proportional scaling with different error
        result2 = controller.update(0.80)  # Error = 0.75 - 0.80 = -0.05

        # P = 10.0 × (-0.05) = -0.5
        assert result2["P"] == pytest.approx(-0.5, abs=0.01), (
            f"Expected P=-0.5, got {result2['P']}"
        )
        assert result2["control_signal"] == pytest.approx(-0.5, abs=0.01)

    def test_integral_accumulation(self):
        """
        Test integral term accumulates error over time.

        I-only control (Kp=0, Kd=0) should eliminate steady-state error
        by accumulating error integral over time.

        Formula: u(t) = Ki × ∫e(τ)dτ
        Expected: Persistent error causes integral to grow
        """
        config = PIDConfig(
            name="test_integral",
            setpoint=0.75,
            Kp=0.0,  # Disable proportional
            Ki=1.0,  # Only integral
            Kd=0.0,  # Disable derivative
            output_limits=(-1.0, 1.0),
            integral_limits=(-10.0, 10.0),
        )
        controller = PIDState(id=uuid4(), config=config)

        # Simulate persistent error over 5 time steps
        errors_observed = []
        integrals_observed = []
        control_signals = []

        for step in range(5):
            # Set time to simulate 1-day intervals
            controller.previous_time = datetime.now() - timedelta(days=5 - step)
            result = controller.update(0.70)  # Error = 0.75 - 0.70 = +0.05

            errors_observed.append(result["error"])
            integrals_observed.append(controller.integral)
            control_signals.append(result["control_signal"])

        # Integral should accumulate positive error
        assert controller.integral > 0, (
            f"Integral should accumulate for persistent positive error, got {controller.integral}"
        )

        # Integral should increase over time
        assert integrals_observed[-1] > integrals_observed[0], (
            "Integral should grow with persistent error"
        )

        # Control signal should be positive (I term only)
        assert result["I"] > 0, (
            f"I term should be positive for accumulated positive error, got {result['I']}"
        )
        assert result["control_signal"] > 0, (
            "Control signal should be positive to correct persistent positive error"
        )

        # Integral eliminates steady-state error
        # After 5 days of error=0.05, integral ≈ 0.05 × 5 = 0.25
        # I = Ki × integral = 1.0 × 0.25 = 0.25
        assert result["I"] == pytest.approx(controller.integral * 1.0, abs=0.01)

        # Verify integral grows monotonically for persistent same-sign error
        for i in range(1, len(integrals_observed)):
            assert integrals_observed[i] >= integrals_observed[i - 1], (
                f"Integral should grow monotonically, but decreased at step {i}"
            )

    def test_derivative_anticipation(self):
        """
        Test derivative term dampens oscillations and reduces overshoot.

        D term opposes rate of change, providing damping when error
        is changing rapidly.

        Formula: u(t) = Kd × de(t)/dt
        Expected: Positive D when error decreases (opposes correction)
        """
        config = PIDConfig(
            name="test_derivative",
            setpoint=0.75,
            Kp=10.0,
            Ki=0.0,
            Kd=5.0,  # Strong derivative
            output_limits=(-1.0, 1.0),
        )
        controller = PIDState(id=uuid4(), config=config)

        # Step 1: Large negative error
        controller.previous_time = datetime.now() - timedelta(days=1)
        result1 = controller.update(0.85)  # Error = 0.75 - 0.85 = -0.10

        # P should be negative (below setpoint)
        assert result1["P"] < 0, "P term should be negative for negative error"

        # Step 2: Error decreasing rapidly (system responding)
        controller.previous_time = datetime.now() - timedelta(hours=12)
        result2 = controller.update(0.76)  # Error = 0.75 - 0.76 = -0.01 (improving)

        # Error changed from -0.10 to -0.01, derivative = (-0.01 - (-0.10)) / dt = +0.09 / dt
        # For dt = 0.5 days, derivative ≈ 0.18 per day
        # D = Kd × derivative = 5.0 × 0.18 = 0.9 (positive, opposes correction)
        assert result2["D"] > 0, (
            f"D term should be positive when error is decreasing, got {result2['D']}"
        )

        # Derivative should reduce total control signal magnitude
        # When error decreases rapidly, D opposes P to prevent overshoot
        assert abs(result2["control_signal"]) < abs(result2["P"]), (
            "Derivative should reduce control signal magnitude to dampen response"
        )

        # Step 3: Verify derivative is zero for constant error
        controller.previous_time = datetime.now() - timedelta(days=1)
        result3 = controller.update(0.76)  # Same error as before
        result4 = controller.update(0.76)  # Same error again

        # Derivative should be near zero for constant error
        assert abs(result4["D"]) < 0.1, (
            f"D term should be near zero for constant error, got {result4['D']}"
        )

    def test_anti_windup(self):
        """
        Test integral windup protection prevents saturation.

        When control output saturates, integral should be clamped
        to prevent unbounded accumulation.

        Scenario: Sustained large error that exceeds output limits
        Expected: Integral clamped to integral_limits
        """
        config = PIDConfig(
            name="test_anti_windup",
            setpoint=0.75,
            Kp=0.0,
            Ki=1.0,
            Kd=0.0,
            output_limits=(-0.2, 0.2),
            integral_limits=(-5.0, 5.0),
        )
        controller = PIDState(id=uuid4(), config=config)

        # Simulate sustained large error over many time steps
        for day in range(20):
            controller.previous_time = datetime.now() - timedelta(days=20 - day)
            result = controller.update(0.50)  # Error = 0.75 - 0.50 = +0.25 (large)

        # Integral should be clamped to upper limit
        assert controller.integral <= 5.0, (
            f"Integral should be clamped to 5.0, got {controller.integral}"
        )
        assert controller.integral == pytest.approx(5.0, abs=0.1), (
            "Integral should saturate at upper limit for persistent large error"
        )

        # Saturation flag should be set
        assert result["integral_saturated"] is True, (
            "integral_saturated flag should be True when clamped"
        )

        # Saturation count should be incremented
        assert controller.saturation_count > 0, (
            "Saturation count should track number of saturated updates"
        )

        # Test lower limit saturation
        controller.reset()
        for day in range(20):
            controller.previous_time = datetime.now() - timedelta(days=20 - day)
            result = controller.update(
                0.95
            )  # Error = 0.75 - 0.95 = -0.20 (large negative)

        # Integral should be clamped to lower limit
        assert controller.integral >= -5.0, (
            f"Integral should be clamped to -5.0, got {controller.integral}"
        )
        assert controller.integral == pytest.approx(-5.0, abs=0.1), (
            "Integral should saturate at lower limit for persistent large negative error"
        )

    def test_step_response(self):
        """
        Test full PID response to step change in setpoint.

        Simulates realistic closed-loop system response to setpoint change.
        System should converge to new setpoint without excessive overshoot.

        Performance metrics:
        - Rise time: Time to reach 90% of setpoint
        - Settling time: Time to stay within ±2% of setpoint
        - Overshoot: Maximum deviation beyond setpoint
        - Steady-state error: Final error after convergence
        """
        # Create PID with balanced tuning
        config = PIDConfig(
            name="test_step",
            setpoint=0.75,
            Kp=10.0,
            Ki=0.5,
            Kd=2.0,
            output_limits=(-0.2, 0.2),
            integral_limits=(-5.0, 5.0),
        )
        controller = PIDState(id=uuid4(), config=config)

        # Step change: setpoint changes from 0.75 to 0.80
        controller.set_setpoint(0.80)

        # Simulate system response over 30 days
        utilization_values = []
        control_signals = []
        errors = []

        current_util = 0.75  # Start at old setpoint

        for day in range(30):
            # Update controller
            result = controller.update(current_util)
            control_signals.append(result["control_signal"])
            errors.append(result["error"])

            # Simulate system response (first-order model)
            # du/dt = control_signal (simplified dynamics)
            current_util += result["control_signal"] * 0.1  # 10% response rate
            current_util = np.clip(current_util, 0.0, 1.0)  # Physical limits
            utilization_values.append(current_util)

            # Advance time
            controller.previous_time = datetime.now() - timedelta(days=30 - day)

        # Check convergence to setpoint
        final_util = utilization_values[-1]
        assert final_util == pytest.approx(0.80, abs=0.02), (
            f"System should converge to setpoint 0.80, got {final_util}"
        )

        # Check for acceptable overshoot (< 10%)
        max_util = max(utilization_values)
        overshoot = max_util - 0.80
        assert overshoot < 0.08, f"Overshoot should be < 8%, got {overshoot * 100:.1f}%"

        # Check steady-state error (< 2%)
        steady_state_error = abs(final_util - 0.80)
        assert steady_state_error < 0.02, (
            f"Steady-state error should be < 2%, got {steady_state_error * 100:.1f}%"
        )

        # Check rise time (time to reach 90% of step)
        target_90_percent = 0.75 + 0.9 * (0.80 - 0.75)  # 0.795
        rise_time = None
        for day, util in enumerate(utilization_values):
            if util >= target_90_percent:
                rise_time = day
                break

        assert rise_time is not None, "System should reach 90% of setpoint"
        assert rise_time < 15, f"Rise time should be < 15 days, got {rise_time} days"

    def test_disturbance_rejection(self):
        """
        Test controller rejects external disturbances.

        Scenario: System at steady state, sudden disturbance occurs,
        PID should recover and return to setpoint.

        Metrics:
        - Recovery time: Time to return within 2% of setpoint after disturbance
        - Maximum deviation: Peak error during disturbance
        """
        config = PIDConfig(
            name="test_disturbance",
            setpoint=0.95,
            Kp=12.0,  # Coverage PID (high priority)
            Ki=0.8,
            Kd=1.5,
            output_limits=(-0.1, 0.1),
            integral_limits=(-10.0, 10.0),
        )
        controller = PIDState(id=uuid4(), config=config)

        # System at steady state
        current_coverage = 0.95

        # Simulate disturbance at day 10 (sudden faculty absence drops coverage)
        disturbances = [0.0] * 10 + [-0.10] + [0.0] * 19  # -10% coverage drop

        coverage_values = []
        errors = []

        for day, disturbance in enumerate(disturbances):
            # Update controller
            controller.previous_time = datetime.now() - timedelta(
                days=len(disturbances) - day
            )
            result = controller.update(current_coverage)
            errors.append(result["error"])

            # Apply control and disturbance
            # System response: du/dt = control_signal + disturbance
            current_coverage += result["control_signal"] * 0.2 + disturbance
            current_coverage = np.clip(current_coverage, 0.0, 1.0)
            coverage_values.append(current_coverage)

        # Find maximum deviation during disturbance
        max_deviation = max(abs(0.95 - cov) for cov in coverage_values)
        assert max_deviation > 0.05, "Disturbance should cause noticeable deviation"

        # Find recovery time: time to get back within 2% of setpoint
        recovery_day = None
        for day, cov in enumerate(
            coverage_values[11:], start=11
        ):  # Start after disturbance
            if abs(cov - 0.95) < 0.02:
                recovery_day = day
                break

        assert recovery_day is not None, "System should recover from disturbance"
        assert recovery_day < 20, (
            f"Recovery time should be < 10 days, got {recovery_day - 10} days"
        )

        # Verify final convergence
        final_coverage = coverage_values[-1]
        assert final_coverage == pytest.approx(0.95, abs=0.02), (
            f"System should return to setpoint after disturbance, got {final_coverage}"
        )

        # Verify no sustained oscillation after disturbance
        # Check last 10 values for sign changes (oscillation indicator)
        late_errors = [0.95 - cov for cov in coverage_values[-10:]]
        sign_changes = sum(
            1
            for i in range(1, len(late_errors))
            if late_errors[i] * late_errors[i - 1] < 0
        )
        assert sign_changes < 5, (
            f"System should not oscillate after recovery, got {sign_changes} sign changes"
        )


class TestPIDIntegration:
    """Integration tests for PID in realistic scheduling scenarios."""

    def test_utilization_control(self):
        """Test PID controls faculty utilization around 75% target."""
        config = PIDConfig(
            name="utilization",
            setpoint=0.75,
            Kp=10.0,
            Ki=0.5,
            Kd=2.0,
            output_limits=(-0.2, 0.2),
            integral_limits=(-5.0, 5.0),
        )
        controller = PIDState(id=uuid4(), config=config)

        # Scenario: Utilization drifts to 0.82 (above target)
        result = controller.update(0.82)

        # Error = 0.75 - 0.82 = -0.07 (negative, above target)
        assert result["error"] == pytest.approx(-0.07, abs=0.001)

        # Control signal should be negative (reduce utilization)
        assert result["control_signal"] < 0, (
            "Should signal to reduce utilization when above target"
        )

        # P term dominates for immediate response
        assert abs(result["P"]) > abs(result["I"]), (
            "P term should dominate for immediate correction"
        )

    def test_coverage_emergency_response(self):
        """Test PID responds aggressively to coverage gaps."""
        config = PIDConfig(
            name="coverage",
            setpoint=0.95,
            Kp=12.0,  # High gain for critical metric
            Ki=0.8,
            Kd=1.5,
            output_limits=(-0.1, 0.1),
        )
        controller = PIDState(id=uuid4(), config=config)

        # Scenario: Coverage drops to 0.85 (critical gap)
        result = controller.update(0.85)

        # Error = 0.95 - 0.85 = +0.10 (positive, below target)
        assert result["error"] == pytest.approx(0.10, abs=0.001)

        # Control signal should be positive and near maximum (recruit backup)
        assert result["control_signal"] > 0, (
            "Should signal to increase coverage when below target"
        )
        assert result["control_signal"] == pytest.approx(0.1, abs=0.01), (
            "Should saturate at output limit for large coverage gap"
        )

        # Output should be saturated for such a large error
        assert result["output_saturated"] is True

    def test_workload_balance(self):
        """Test PID maintains workload balance (low variance)."""
        config = PIDConfig(
            name="workload_balance",
            setpoint=0.0,  # Target: zero imbalance
            Kp=5.0,
            Ki=0.3,
            Kd=1.0,
            output_limits=(-0.15, 0.15),
        )
        controller = PIDState(id=uuid4(), config=config)

        # Scenario: Workload imbalance at 0.18 std_dev (high variance)
        result = controller.update(0.18)

        # Error = 0.0 - 0.18 = -0.18 (negative, need to reduce variance)
        assert result["error"] == pytest.approx(-0.18, abs=0.001)

        # Control signal should trigger redistribution
        assert abs(result["control_signal"]) > 0.05, (
            "Should signal workload redistribution for high imbalance"
        )
