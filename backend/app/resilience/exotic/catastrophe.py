"""
Catastrophe Theory for Schedule Failure Prediction.

From dynamical systems theory (René Thom, 1972): smooth parameter changes
can cause sudden discontinuous transitions (catastrophes).

Application to scheduling:
- Predict sudden system failures from gradual stress accumulation
- Identify bifurcation points (parameter values where behavior changes qualitatively)
- Model tipping points in resident morale

Seven elementary catastrophes:
1. Fold (1 control, 1 behavior)
2. Cusp (2 control, 1 behavior) - most common
3. Swallowtail (3 control, 1 behavior)
4. Butterfly, Hyperbolic umbilic, Elliptic umbilic, Parabolic umbilic (higher dimensions)

We focus on Cusp catastrophe - two control parameters cause sudden jumps
in behavior variable.

Based on:
- Zeeman's work on catastrophe theory applications
- Cusp catastrophe model
- Bifurcation theory
"""

from dataclasses import dataclass
from typing import Optional

import numpy as np
from scipy.optimize import minimize_scalar


@dataclass
class CuspParameters:
    """Cusp catastrophe parameters."""

    a: float  # Asymmetry/splitting factor
    b: float  # Bias/normal factor
    x: float  # Behavior state
    potential: float  # Potential function value V(x)


@dataclass
class CatastrophePoint:
    """Catastrophe point (bifurcation/jump location)."""

    a_critical: float  # Critical asymmetry value
    b_critical: float  # Critical bias value
    x_before: float  # State before jump
    x_after: float  # State after jump
    jump_magnitude: float  # Size of discontinuous jump
    hysteresis_width: float  # Width of hysteresis region


class CatastropheTheory:
    """
    Catastrophe theory for predicting sudden system failures.

    Uses cusp catastrophe model to identify tipping points.

    Cusp potential: V(x; a, b) = x^4/4 + ax^2/2 + bx

    Equilibria satisfy: dV/dx = 0 => x^3 + ax + b = 0

    Control surface: a^3 + 27b^2 = 0 (bifurcation set)
    """

    def __init__(self):
        """Initialize catastrophe theory model."""
        pass

    def calculate_cusp_potential(self, x: float, a: float, b: float) -> float:
        """
        Calculate cusp potential function.

        V(x) = x^4/4 + ax^2/2 + bx

        Args:
            x: Behavior variable (e.g., burnout level, morale)
            a: Asymmetry factor (splitting parameter)
            b: Bias factor (normal parameter)

        Returns:
            Potential value
        """
        V = (x**4) / 4.0 + a * (x**2) / 2.0 + b * x
        return V

    def find_equilibria(self, a: float, b: float) -> list[float]:
        """
        Find equilibrium points for given control parameters.

        Equilibria satisfy: x^3 + ax + b = 0

        Args:
            a: Asymmetry parameter
            b: Bias parameter

        Returns:
            List of equilibrium x values
        """
        # Solve cubic equation: x^3 + ax + b = 0
        # Use Cardano's formula or numerical root finding

        coefficients = [1, 0, a, b]  # x^3 + 0*x^2 + a*x + b
        roots = np.roots(coefficients)

        # Keep only real roots
        real_roots = [float(r.real) for r in roots if abs(r.imag) < 1e-10]

        return sorted(real_roots)

    def classify_equilibrium_stability(self, x: float, a: float, b: float) -> str:
        """
        Classify equilibrium as stable or unstable.

        Stable if d²V/dx² > 0 (potential minimum)
        Unstable if d²V/dx² < 0 (potential maximum)

        d²V/dx² = 3x^2 + a

        Args:
            x: Equilibrium point
            a: Asymmetry parameter
            b: Bias parameter (not used in stability)

        Returns:
            "stable" or "unstable"
        """
        second_derivative = 3 * x**2 + a

        return "stable" if second_derivative > 0 else "unstable"

    def find_bifurcation_set(
        self, b_range: tuple[float, float], num_points: int = 100
    ) -> list[tuple[float, float]]:
        """
        Find bifurcation set (catastrophe boundary).

        For cusp: a^3 + 27b^2 = 0 => a = -3(3b^2)^(1/3)

        Args:
            b_range: Range of b values to plot
            num_points: Number of points

        Returns:
            List of (a, b) points on bifurcation boundary
        """
        b_values = np.linspace(b_range[0], b_range[1], num_points)
        bifurcation_points = []

        for b in b_values:
            # Cusp boundary: a = -(3^(1/3)) * (3|b|)^(2/3) * sign(b)
            if abs(b) > 1e-10:
                a = -np.cbrt(27) * np.cbrt(abs(b) ** 2) * np.sign(b)
            else:
                a = 0.0

            bifurcation_points.append((float(a), float(b)))

        return bifurcation_points

    def predict_catastrophe_jump(
        self,
        current_a: float,
        current_b: float,
        da: float,
        db: float,
        num_steps: int = 100,
    ) -> CatastrophePoint | None:
        """
        Predict if parameter change will cause catastrophic jump.

        Simulates gradual change in (a, b) and detects discontinuity.

        Args:
            current_a: Current asymmetry parameter
            current_b: Current bias parameter
            da: Change in a
            db: Change in b
            num_steps: Number of steps to simulate

        Returns:
            CatastrophePoint if jump occurs, None otherwise
        """
        # Start from current equilibrium
        current_equilibria = self.find_equilibria(current_a, current_b)
        if not current_equilibria:
            return None

        # Start at lowest stable equilibrium
        current_x = min(current_equilibria)

        # Track trajectory
        for step in range(num_steps):
            t = step / num_steps
            a = current_a + t * da
            b = current_b + t * db

            # Find equilibria at this point
            equilibria = self.find_equilibria(a, b)

            # Check if current_x is still an equilibrium
            tolerance = 0.1
            still_valid = any(abs(eq - current_x) < tolerance for eq in equilibria)

            if not still_valid:
                # Jump occurred!
                # Find nearest new stable equilibrium
                stable_equilibria = [
                    eq
                    for eq in equilibria
                    if self.classify_equilibrium_stability(eq, a, b) == "stable"
                ]

                if stable_equilibria:
                    new_x = min(stable_equilibria, key=lambda eq: abs(eq - current_x))

                    return CatastrophePoint(
                        a_critical=a,
                        b_critical=b,
                        x_before=current_x,
                        x_after=new_x,
                        jump_magnitude=abs(new_x - current_x),
                        hysteresis_width=abs(da * t),  # Approximate
                    )

        return None

    def calculate_resilience_from_catastrophe(
        self,
        current_state: tuple[float, float, float],  # (a, b, x)
        stress_direction: tuple[float, float],  # (da, db)
    ) -> dict:
        """
        Calculate resilience based on distance to catastrophe.

        Args:
            current_state: Current (a, b, x) state
            stress_direction: Direction of stress increase (da, db)

        Returns:
            Dict with resilience metrics
        """
        a, b, x = current_state
        da, db = stress_direction

        # Find distance to bifurcation set
        # Bifurcation: a^3 + 27b^2 = 0
        current_distance = abs(a**3 + 27 * b**2)

        # Normalize to resilience score
        # Large distance = high resilience
        resilience_score = min(1.0, current_distance / 10.0)

        # Predict catastrophe
        catastrophe_point = self.predict_catastrophe_jump(a, b, da, db)

        if catastrophe_point:
            is_safe = False
            distance_to_catastrophe = catastrophe_point.hysteresis_width
            warning = f"Catastrophe predicted at a={catastrophe_point.a_critical:.2f}, b={catastrophe_point.b_critical:.2f}"
        else:
            is_safe = True
            distance_to_catastrophe = float("inf")
            warning = "No catastrophe predicted in stress direction"

        # Classification
        if resilience_score > 0.8:
            status = "robust"
        elif resilience_score > 0.5:
            status = "stable"
        elif resilience_score > 0.2:
            status = "vulnerable"
        else:
            status = "critical"

        return {
            "resilience_score": resilience_score,
            "status": status,
            "is_safe": is_safe,
            "distance_to_catastrophe": distance_to_catastrophe,
            "current_distance_to_bifurcation": current_distance,
            "warning": warning,
            "catastrophe_point": catastrophe_point,
        }

    def model_hysteresis(
        self,
        a: float,
        b_range: tuple[float, float],
        num_steps: int = 100,
    ) -> dict:
        """
        Model hysteresis loop (forward and backward paths differ).

        As b increases then decreases, system follows different paths
        (characteristic of catastrophe).

        Args:
            a: Fixed asymmetry parameter
            b_range: Range of bias parameter
            num_steps: Number of steps

        Returns:
            Dict with forward and backward paths
        """
        forward_path = []
        backward_path = []

        # Forward sweep (increasing b)
        b_values_forward = np.linspace(b_range[0], b_range[1], num_steps)
        current_x = None

        for b in b_values_forward:
            equilibria = self.find_equilibria(a, b)
            stable_equilibria = [
                eq
                for eq in equilibria
                if self.classify_equilibrium_stability(eq, a, b) == "stable"
            ]

            if current_x is None:
                # Start at lowest stable equilibrium
                current_x = min(stable_equilibria) if stable_equilibria else 0.0
            else:
                # Follow nearest stable equilibrium
                if stable_equilibria:
                    current_x = min(
                        stable_equilibria, key=lambda eq: abs(eq - current_x)
                    )

            forward_path.append((b, current_x))

        # Backward sweep (decreasing b)
        b_values_backward = np.linspace(b_range[1], b_range[0], num_steps)
        current_x = forward_path[-1][1]  # Start from end of forward path

        for b in b_values_backward:
            equilibria = self.find_equilibria(a, b)
            stable_equilibria = [
                eq
                for eq in equilibria
                if self.classify_equilibrium_stability(eq, a, b) == "stable"
            ]

            if stable_equilibria:
                current_x = min(stable_equilibria, key=lambda eq: abs(eq - current_x))

            backward_path.append((b, current_x))

        # Calculate hysteresis area
        hysteresis_area = self._calculate_hysteresis_area(forward_path, backward_path)

        return {
            "forward_path": forward_path,
            "backward_path": backward_path,
            "hysteresis_area": hysteresis_area,
            "has_hysteresis": hysteresis_area > 0.01,
        }

    def _calculate_hysteresis_area(
        self,
        forward_path: list[tuple[float, float]],
        backward_path: list[tuple[float, float]],
    ) -> float:
        """Calculate area between forward and backward paths."""
        # Numerical integration using trapezoidal rule
        area = 0.0

        # Ensure same b values
        if len(forward_path) != len(backward_path):
            return 0.0

        for i in range(len(forward_path) - 1):
            b1, x_forward1 = forward_path[i]
            b2, x_forward2 = forward_path[i + 1]
            _, x_backward1 = backward_path[-(i + 1)]
            _, x_backward2 = backward_path[-(i + 2)]

            # Trapezoid area
            db = b2 - b1
            avg_height = abs(
                (x_forward1 + x_forward2) / 2 - (x_backward1 + x_backward2) / 2
            )
            area += avg_height * abs(db)

        return area
