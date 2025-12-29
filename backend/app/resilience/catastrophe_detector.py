"""
Catastrophe Theory for Schedule Phase Transitions.

Models sudden schedule failures (catastrophes) from gradual parameter changes.
Inspired by René Thom's catastrophe theory (1972), specifically the cusp catastrophe,
which exhibits sudden jumps between stable states as control parameters vary smoothly.

Mathematical Basis:
    The cusp catastrophe has two control parameters (a, b) and one behavior variable (x).
    The potential function is: V(x) = x⁴/4 + ax²/2 + bx

    In scheduling context:
    - Control parameter a: Coverage demand (stress)
    - Control parameter b: Constraint strictness (ACGME compliance pressure)
    - Behavior variable x: Schedule feasibility

    The cusp surface exhibits:
    1. Sudden jumps between stable states (feasible ↔ infeasible)
    2. Hysteresis (path-dependent behavior)
    3. Bifurcation at critical points (small changes cause large effects)
    4. Inaccessible middle region (no stable intermediate states)

Key Principles from Catastrophe Theory:
- Small, smooth changes in parameters can cause sudden, discontinuous state changes
- System exhibits divergence (paths from similar initial conditions separate)
- Hysteresis loop: forward and reverse transitions occur at different thresholds
- Cusp point marks maximum instability

Applications to Medical Residency Scheduling:
- Detect when schedule is approaching catastrophic failure boundary
- Predict "tipping points" where minor changes cause major disruptions
- Identify hysteresis: easier to prevent failure than recover from it
- Map safe operating regions vs. critical zones

References:
- Thom, R. (1972). Structural Stability and Morphogenesis
- Zeeman, E.C. (1976). Catastrophe Theory
- Gilmore, R. (1981). Catastrophe Theory for Scientists and Engineers
"""

import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

import numpy as np
from scipy.optimize import minimize_scalar
from scipy.spatial.distance import euclidean

from app.resilience.defense_in_depth import DefenseLevel

logger = logging.getLogger(__name__)

# Try to import optional dependencies
try:
    from scipy import interpolate

    HAS_SCIPY_INTERPOLATE = True
except ImportError:
    HAS_SCIPY_INTERPOLATE = False
    logger.warning("scipy.interpolate not available - some features limited")


# =============================================================================
# Enums and Constants
# =============================================================================


class CatastropheRegion(str, Enum):
    """Region in parameter space relative to catastrophe boundary."""

    SAFE = "safe"  # Far from cusp, stable
    STABLE = "stable"  # Moderate distance, generally safe
    WARNING = "warning"  # Approaching critical boundary
    CRITICAL = "critical"  # Near cusp, high instability
    CATASTROPHIC = "catastrophic"  # Past cusp, likely failed


class SystemState(str, Enum):
    """Current state of the scheduling system."""

    FEASIBLE = "feasible"  # Schedule can be generated
    STRAINED = "strained"  # Schedule exists but stressed
    MARGINAL = "marginal"  # Schedule barely feasible
    INFEASIBLE = "infeasible"  # No valid schedule exists


# Default parameter ranges for grid search
DEFAULT_DEMAND_RANGE = (0.5, 1.2)  # 50% to 120% of nominal demand
DEFAULT_STRICTNESS_RANGE = (0.0, 1.0)  # 0 = relaxed, 1 = maximum strictness


# =============================================================================
# Data Classes
# =============================================================================


@dataclass
class ParameterState:
    """
    Point in parameter space (demand, strictness).

    Represents a specific configuration of the scheduling system at a moment in time.
    """

    demand: float  # Coverage demand (0.5 = half normal, 1.0 = normal, 1.2 = 120%)
    strictness: float  # Constraint strictness (0.0 = relaxed, 1.0 = maximum)
    timestamp: datetime = field(default_factory=datetime.now)
    feasibility_score: float | None = None  # 0.0 = infeasible, 1.0 = easily feasible
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate parameters."""
        if self.demand < 0:
            raise ValueError(f"demand must be >= 0, got {self.demand}")
        if not 0 <= self.strictness <= 1:
            raise ValueError(f"strictness must be in [0, 1], got {self.strictness}")

    def to_array(self) -> np.ndarray:
        """Convert to numpy array [demand, strictness]."""
        return np.array([self.demand, self.strictness])


@dataclass
class FeasibilitySurface:
    """
    2D grid of feasibility scores across parameter space.

    Maps (demand, strictness) → feasibility_score over a grid of points.
    Used to identify catastrophe boundaries.
    """

    demand_values: np.ndarray  # 1D array of demand values
    strictness_values: np.ndarray  # 1D array of strictness values
    feasibility_grid: np.ndarray  # 2D array: [strictness_idx, demand_idx] → score

    # Metadata
    computed_at: datetime = field(default_factory=datetime.now)
    grid_resolution: tuple[int, int] = field(default=(20, 20))
    computation_time_seconds: float = 0.0

    def __post_init__(self):
        """Validate grid dimensions."""
        expected_shape = (len(self.strictness_values), len(self.demand_values))
        if self.feasibility_grid.shape != expected_shape:
            raise ValueError(
                f"Grid shape mismatch: expected {expected_shape}, "
                f"got {self.feasibility_grid.shape}"
            )

    def get_feasibility(self, demand: float, strictness: float) -> float | None:
        """
        Get feasibility at a specific parameter point (interpolated).

        Args:
            demand: Coverage demand
            strictness: Constraint strictness

        Returns:
            Interpolated feasibility score, or None if out of bounds
        """
        if not HAS_SCIPY_INTERPOLATE:
            # Fallback to nearest neighbor
            d_idx = np.argmin(np.abs(self.demand_values - demand))
            s_idx = np.argmin(np.abs(self.strictness_values - strictness))
            return float(self.feasibility_grid[s_idx, d_idx])

        # Use bilinear interpolation
        interp_func = interpolate.RectBivariateSpline(
            self.strictness_values,
            self.demand_values,
            self.feasibility_grid,
            kx=1,
            ky=1,
        )
        return float(interp_func(strictness, demand)[0, 0])


@dataclass
class CuspAnalysis:
    """
    Results from cusp catastrophe detection.

    Identifies the cusp point, cusp boundary, and hysteresis region.
    """

    cusp_exists: bool  # Whether a cusp catastrophe was detected
    cusp_center: tuple[float, float] | None  # (demand, strictness) at cusp point
    cusp_score: float  # Confidence in cusp detection (0.0 - 1.0)
    hysteresis_gap: float  # Width of hysteresis region

    # Boundary curves
    upper_boundary: list[tuple[float, float]] = field(
        default_factory=list
    )  # Points on upper fold
    lower_boundary: list[tuple[float, float]] = field(
        default_factory=list
    )  # Points on lower fold

    # Regions
    safe_region: CatastropheRegion = CatastropheRegion.SAFE
    critical_threshold_demand: float | None = None  # Demand at which cusp begins
    critical_threshold_strictness: float | None = None

    analyzed_at: datetime = field(default_factory=datetime.now)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "cusp_exists": self.cusp_exists,
            "cusp_center": self.cusp_center,
            "cusp_score": self.cusp_score,
            "hysteresis_gap": self.hysteresis_gap,
            "upper_boundary": self.upper_boundary,
            "lower_boundary": self.lower_boundary,
            "safe_region": self.safe_region.value,
            "critical_threshold_demand": self.critical_threshold_demand,
            "critical_threshold_strictness": self.critical_threshold_strictness,
            "analyzed_at": self.analyzed_at.isoformat(),
            "metadata": self.metadata,
        }


@dataclass
class FailurePrediction:
    """
    Prediction of catastrophic failure based on parameter trajectory.

    Forecasts whether the system is heading toward a catastrophe.
    """

    will_fail: bool  # Whether failure is predicted
    confidence: float  # Prediction confidence (0.0 - 1.0)
    time_to_failure: float | None  # Estimated time steps until failure
    failure_mode: str  # "cusp_crossing", "gradual_degradation", "stable"

    current_state: SystemState
    predicted_state: SystemState

    # Distance metrics
    distance_to_catastrophe: float  # Distance to nearest catastrophe boundary
    trajectory_direction: str  # "toward_cusp", "away_from_cusp", "parallel"

    recommended_actions: list[str] = field(default_factory=list)
    defense_level_needed: DefenseLevel = DefenseLevel.PREVENTION

    analyzed_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "will_fail": self.will_fail,
            "confidence": self.confidence,
            "time_to_failure": self.time_to_failure,
            "failure_mode": self.failure_mode,
            "current_state": self.current_state.value,
            "predicted_state": self.predicted_state.value,
            "distance_to_catastrophe": self.distance_to_catastrophe,
            "trajectory_direction": self.trajectory_direction,
            "recommended_actions": self.recommended_actions,
            "defense_level_needed": self.defense_level_needed.value,
            "analyzed_at": self.analyzed_at.isoformat(),
        }


@dataclass
class CatastropheAlert:
    """
    Early warning alert for approaching catastrophe boundary.

    Triggered when system is approaching critical instability.
    """

    severity: str  # "low", "medium", "high", "critical"
    region: CatastropheRegion
    message: str
    current_params: ParameterState
    distance_to_cusp: float
    recommended_defense_level: DefenseLevel

    # Context
    triggered_at: datetime = field(default_factory=datetime.now)
    metadata: dict[str, Any] = field(default_factory=dict)


# =============================================================================
# Catastrophe Detector
# =============================================================================


class CatastropheDetector:
    """
    Detects catastrophe boundaries and phase transitions in scheduling parameter space.

    Uses catastrophe theory to model sudden transitions from feasible to infeasible
    schedules. Identifies cusp catastrophes, measures distance to critical boundaries,
    and predicts system failures.

    The detector maps a 2D parameter space (demand, strictness) to feasibility scores,
    then analyzes this surface for characteristic catastrophe signatures:
    - Sudden discontinuities (fold catastrophes)
    - S-shaped response curves (cusp catastrophes)
    - Hysteresis loops (path-dependent behavior)
    """

    def __init__(
        self,
        feasibility_function: Callable[[float, float], float] | None = None,
        demand_range: tuple[float, float] = DEFAULT_DEMAND_RANGE,
        strictness_range: tuple[float, float] = DEFAULT_STRICTNESS_RANGE,
    ):
        """
        Initialize catastrophe detector.

        Args:
            feasibility_function: Function (demand, strictness) -> feasibility_score.
                If None, uses a default cusp catastrophe model.
            demand_range: (min, max) for coverage demand parameter
            strictness_range: (min, max) for constraint strictness parameter
        """
        self.feasibility_function = feasibility_function or self._default_cusp_model
        self.demand_range = demand_range
        self.strictness_range = strictness_range

        logger.info("CatastropheDetector initialized with custom feasibility function")

    @staticmethod
    def _default_cusp_model(demand: float, strictness: float) -> float:
        """
        Default cusp catastrophe model for testing.

        This is a mathematical model that exhibits cusp catastrophe behavior.
        Real implementation should use actual schedule feasibility checking.

        The cusp potential: V(x) = x⁴/4 + a*x²/2 + b*x
        where a = (demand - 0.85), b = (strictness - 0.5)

        Feasibility is derived from the equilibrium points.
        """
        # Map parameters to cusp control parameters
        a = (demand - 0.85) * 3  # Center around demand=0.85
        b = (strictness - 0.5) * 2  # Center around strictness=0.5

        # Solve for equilibrium: dV/dx = x³ + ax + b = 0
        # Approximate solution using discriminant
        discriminant = -4 * a**3 - 27 * b**2

        if discriminant > 0:
            # Three real roots - stable region
            feasibility = 1.0
        elif discriminant < -0.5:
            # One real root - unstable, likely infeasible
            feasibility = 0.2
        else:
            # Near boundary - marginal
            feasibility = 0.5 + 0.3 * np.tanh(-discriminant * 2)

        # Add noise for realism
        noise = np.random.normal(0, 0.05)
        return float(np.clip(feasibility + noise, 0.0, 1.0))

    def map_constraint_space(
        self,
        demand_range: tuple[float, float] | None = None,
        strictness_range: tuple[float, float] | None = None,
        resolution: tuple[int, int] = (20, 20),
    ) -> FeasibilitySurface:
        """
        Scan parameter space to create feasibility surface.

        Evaluates feasibility at grid points across (demand, strictness) space.
        This is the foundation for catastrophe detection.

        Args:
            demand_range: Override default demand range
            strictness_range: Override default strictness range
            resolution: (n_demand_points, n_strictness_points)

        Returns:
            FeasibilitySurface containing the computed grid

        Example:
            >>> detector = CatastropheDetector()
            >>> surface = detector.map_constraint_space(resolution=(30, 30))
            >>> print(f"Surface shape: {surface.feasibility_grid.shape}")
        """
        start_time = datetime.now()

        d_range = demand_range or self.demand_range
        s_range = strictness_range or self.strictness_range

        # Create grid
        demand_vals = np.linspace(d_range[0], d_range[1], resolution[0])
        strictness_vals = np.linspace(s_range[0], s_range[1], resolution[1])

        # Evaluate feasibility at each grid point
        grid = np.zeros((resolution[1], resolution[0]))

        for i, strictness in enumerate(strictness_vals):
            for j, demand in enumerate(demand_vals):
                grid[i, j] = self.feasibility_function(demand, strictness)

        computation_time = (datetime.now() - start_time).total_seconds()

        logger.info(
            f"Mapped parameter space: {resolution[0]}x{resolution[1]} grid "
            f"in {computation_time:.2f}s"
        )

        return FeasibilitySurface(
            demand_values=demand_vals,
            strictness_values=strictness_vals,
            feasibility_grid=grid,
            grid_resolution=resolution,
            computation_time_seconds=computation_time,
        )

    def detect_catastrophe_cusp(self, surface: FeasibilitySurface) -> CuspAnalysis:
        """
        Detect cusp catastrophe in feasibility surface.

        Identifies the characteristic S-shaped boundary of a cusp catastrophe
        by looking for:
        1. Rapid transitions (large gradients)
        2. Hysteresis (different thresholds for different paths)
        3. Cusp point (maximum instability)

        Args:
            surface: FeasibilitySurface from map_constraint_space()

        Returns:
            CuspAnalysis containing cusp location and characteristics

        Example:
            >>> surface = detector.map_constraint_space()
            >>> analysis = detector.detect_catastrophe_cusp(surface)
            >>> if analysis.cusp_exists:
            ...     print(f"Cusp detected at {analysis.cusp_center}")
        """
        # Compute gradients to find rapid transitions
        grad_demand = np.gradient(surface.feasibility_grid, axis=1)
        grad_strictness = np.gradient(surface.feasibility_grid, axis=0)
        gradient_magnitude = np.sqrt(grad_demand**2 + grad_strictness**2)

        # Find boundary: where gradient is large and feasibility is near 0.5
        threshold_gradient = np.percentile(gradient_magnitude, 75)
        boundary_mask = (gradient_magnitude > threshold_gradient) & (
            np.abs(surface.feasibility_grid - 0.5) < 0.3
        )

        # Extract boundary points
        boundary_indices = np.argwhere(boundary_mask)

        if len(boundary_indices) < 5:
            # No clear boundary detected
            return CuspAnalysis(
                cusp_exists=False,
                cusp_center=None,
                cusp_score=0.0,
                hysteresis_gap=0.0,
            )

        # Find cusp point: maximum curvature on boundary
        cusp_score = 0.0
        cusp_idx = None
        max_curvature = 0.0

        for idx in boundary_indices:
            s_idx, d_idx = idx
            # Estimate curvature from second derivatives
            if 1 < s_idx < len(surface.strictness_values) - 2:
                curvature = abs(
                    gradient_magnitude[s_idx + 1, d_idx]
                    - 2 * gradient_magnitude[s_idx, d_idx]
                    + gradient_magnitude[s_idx - 1, d_idx]
                )
                if curvature > max_curvature:
                    max_curvature = curvature
                    cusp_idx = idx

        if cusp_idx is not None:
            s_idx, d_idx = cusp_idx
            cusp_demand = surface.demand_values[d_idx]
            cusp_strictness = surface.strictness_values[s_idx]
            cusp_center = (float(cusp_demand), float(cusp_strictness))

            # Score based on gradient strength and boundary clarity
            cusp_score = min(1.0, max_curvature / 10.0)
        else:
            cusp_center = None
            cusp_score = 0.0

        # Measure hysteresis gap
        hysteresis_gap = self._measure_hysteresis(surface, boundary_indices)

        # Extract upper and lower boundaries
        upper_boundary, lower_boundary = self._extract_boundary_curves(
            surface, boundary_indices
        )

        # Determine critical thresholds
        critical_demand = None
        critical_strictness = None
        if cusp_center:
            critical_demand = cusp_center[0] * 0.9  # 90% of cusp demand
            critical_strictness = cusp_center[1] * 0.8

        logger.info(
            f"Cusp analysis: exists={cusp_score > 0.3}, "
            f"center={cusp_center}, score={cusp_score:.2f}, "
            f"hysteresis={hysteresis_gap:.3f}"
        )

        return CuspAnalysis(
            cusp_exists=cusp_score > 0.3,  # Threshold for cusp detection
            cusp_center=cusp_center,
            cusp_score=cusp_score,
            hysteresis_gap=hysteresis_gap,
            upper_boundary=upper_boundary,
            lower_boundary=lower_boundary,
            critical_threshold_demand=critical_demand,
            critical_threshold_strictness=critical_strictness,
        )

    def _measure_hysteresis(
        self, surface: FeasibilitySurface, boundary_indices: np.ndarray
    ) -> float:
        """
        Measure width of hysteresis gap.

        Hysteresis means the transition thresholds differ depending on direction.
        """
        if len(boundary_indices) < 5:
            return 0.0

        # For each strictness level, find min and max demand on boundary
        strictness_levels = {}
        for s_idx, d_idx in boundary_indices:
            strictness = surface.strictness_values[s_idx]
            demand = surface.demand_values[d_idx]

            if strictness not in strictness_levels:
                strictness_levels[strictness] = []
            strictness_levels[strictness].append(demand)

        # Measure average gap
        gaps = []
        for demands in strictness_levels.values():
            if len(demands) > 1:
                gap = max(demands) - min(demands)
                gaps.append(gap)

        return float(np.mean(gaps)) if gaps else 0.0

    def _extract_boundary_curves(
        self, surface: FeasibilitySurface, boundary_indices: np.ndarray
    ) -> tuple[list[tuple[float, float]], list[tuple[float, float]]]:
        """Extract upper and lower fold boundary curves."""
        if len(boundary_indices) < 5:
            return [], []

        # Sort by demand, then by strictness
        points = [
            (surface.demand_values[d_idx], surface.strictness_values[s_idx])
            for s_idx, d_idx in boundary_indices
        ]
        points_sorted = sorted(points)

        # Split into upper and lower based on median strictness
        median_strictness = np.median([p[1] for p in points_sorted])
        upper = [p for p in points_sorted if p[1] >= median_strictness]
        lower = [p for p in points_sorted if p[1] < median_strictness]

        return upper[:50], lower[:50]  # Limit points for efficiency

    def compute_distance_to_catastrophe(
        self, current_params: ParameterState, cusp_analysis: CuspAnalysis
    ) -> float:
        """
        Compute distance from current parameters to catastrophe boundary.

        Args:
            current_params: Current system parameters
            cusp_analysis: Results from detect_catastrophe_cusp()

        Returns:
            Distance to nearest catastrophe boundary (normalized 0-1 scale)

        Example:
            >>> params = ParameterState(demand=0.80, strictness=0.6)
            >>> distance = detector.compute_distance_to_catastrophe(params, analysis)
            >>> if distance < 0.1:
            ...     print("WARNING: Near catastrophe boundary!")
        """
        if not cusp_analysis.cusp_exists or cusp_analysis.cusp_center is None:
            # No cusp detected, assume safe
            return 1.0

        # Distance to cusp center
        cusp_point = np.array(cusp_analysis.cusp_center)
        current_point = current_params.to_array()
        distance_to_cusp = euclidean(current_point, cusp_point)

        # Also check distance to boundaries
        min_boundary_distance = distance_to_cusp

        for boundary in [cusp_analysis.upper_boundary, cusp_analysis.lower_boundary]:
            if boundary:
                distances = [euclidean(current_point, np.array(p)) for p in boundary]
                min_boundary_distance = min(min_boundary_distance, min(distances))

        # Normalize to 0-1 scale (assume max safe distance is 0.3 in parameter space)
        normalized_distance = min(1.0, min_boundary_distance / 0.3)

        return float(normalized_distance)

    def measure_hysteresis_gap(self, boundary_points: list[tuple[float, float]]) -> float:
        """
        Measure hysteresis gap width from boundary points.

        Hysteresis means the system exhibits different behavior when approached
        from different directions. This measures the width of that gap.

        Args:
            boundary_points: List of (demand, strictness) points on catastrophe boundary

        Returns:
            Width of hysteresis region

        Example:
            >>> gap = detector.measure_hysteresis_gap(analysis.upper_boundary)
            >>> print(f"Hysteresis gap: {gap:.3f}")
        """
        if len(boundary_points) < 5:
            return 0.0

        # Group by strictness levels
        strictness_groups = {}
        for demand, strictness in boundary_points:
            # Round strictness to group nearby points
            s_key = round(strictness, 2)
            if s_key not in strictness_groups:
                strictness_groups[s_key] = []
            strictness_groups[s_key].append(demand)

        # Measure gap at each strictness level
        gaps = []
        for demands in strictness_groups.values():
            if len(demands) > 1:
                gap = max(demands) - min(demands)
                gaps.append(gap)

        return float(np.mean(gaps)) if gaps else 0.0

    def predict_system_failure(
        self,
        trajectory: list[ParameterState],
        cusp_analysis: CuspAnalysis,
        horizon: int = 5,
    ) -> FailurePrediction:
        """
        Predict catastrophic failure from parameter trajectory.

        Analyzes recent parameter history to forecast whether the system is
        heading toward a catastrophe boundary.

        Args:
            trajectory: List of recent parameter states (oldest to newest)
            cusp_analysis: Results from detect_catastrophe_cusp()
            horizon: Number of time steps to forecast ahead

        Returns:
            FailurePrediction with failure forecast and recommendations

        Example:
            >>> trajectory = [
            ...     ParameterState(0.70, 0.3),
            ...     ParameterState(0.75, 0.4),
            ...     ParameterState(0.80, 0.5),
            ... ]
            >>> prediction = detector.predict_system_failure(trajectory, analysis)
            >>> if prediction.will_fail:
            ...     print(f"Failure predicted in {prediction.time_to_failure} steps")
        """
        if len(trajectory) < 2:
            # Not enough history
            return FailurePrediction(
                will_fail=False,
                confidence=0.0,
                time_to_failure=None,
                failure_mode="insufficient_data",
                current_state=SystemState.FEASIBLE,
                predicted_state=SystemState.FEASIBLE,
                distance_to_catastrophe=1.0,
                trajectory_direction="unknown",
            )

        current = trajectory[-1]

        # Compute current distance to catastrophe
        distance = self.compute_distance_to_catastrophe(current, cusp_analysis)

        # Estimate velocity (rate of change)
        recent = trajectory[-min(3, len(trajectory)) :]
        demands = np.array([p.demand for p in recent])
        strictness = np.array([p.strictness for p in recent])

        velocity_demand = np.mean(np.diff(demands)) if len(demands) > 1 else 0.0
        velocity_strictness = (
            np.mean(np.diff(strictness)) if len(strictness) > 1 else 0.0
        )

        # Determine trajectory direction
        if cusp_analysis.cusp_exists and cusp_analysis.cusp_center:
            cusp_point = np.array(cusp_analysis.cusp_center)
            current_point = current.to_array()
            velocity_vector = np.array([velocity_demand, velocity_strictness])

            # Dot product: positive = moving toward cusp
            to_cusp = cusp_point - current_point
            dot_product = np.dot(velocity_vector, to_cusp)

            if dot_product > 0.01:
                direction = "toward_cusp"
            elif dot_product < -0.01:
                direction = "away_from_cusp"
            else:
                direction = "parallel"
        else:
            direction = "unknown"

        # Predict failure
        will_fail = False
        time_to_failure = None
        failure_mode = "stable"
        confidence = 0.0

        if direction == "toward_cusp" and distance < 0.3:
            # Heading toward cusp and close
            will_fail = True
            failure_mode = "cusp_crossing"

            # Estimate time to failure
            velocity_magnitude = np.linalg.norm(velocity_vector)
            if velocity_magnitude > 0.001:
                time_to_failure = distance / velocity_magnitude
                confidence = min(0.95, 0.5 + (1 - distance))
            else:
                time_to_failure = float("inf")
                confidence = 0.5

        elif distance < 0.15:
            # Very close to boundary, even if not moving toward it
            will_fail = True
            failure_mode = "proximity_critical"
            confidence = 1.0 - distance / 0.15

        # Determine current and predicted states
        if current.feasibility_score is not None:
            if current.feasibility_score > 0.8:
                current_state = SystemState.FEASIBLE
            elif current.feasibility_score > 0.5:
                current_state = SystemState.STRAINED
            elif current.feasibility_score > 0.3:
                current_state = SystemState.MARGINAL
            else:
                current_state = SystemState.INFEASIBLE
        else:
            current_state = SystemState.FEASIBLE if distance > 0.3 else SystemState.MARGINAL

        predicted_state = SystemState.INFEASIBLE if will_fail else current_state

        # Generate recommendations
        recommendations = self._generate_recommendations(
            distance, direction, current_state, will_fail
        )

        # Determine defense level needed
        defense_level = self._recommend_defense_level(distance, will_fail)

        logger.info(
            f"Failure prediction: will_fail={will_fail}, confidence={confidence:.2f}, "
            f"distance={distance:.3f}, direction={direction}"
        )

        return FailurePrediction(
            will_fail=will_fail,
            confidence=confidence,
            time_to_failure=time_to_failure,
            failure_mode=failure_mode,
            current_state=current_state,
            predicted_state=predicted_state,
            distance_to_catastrophe=distance,
            trajectory_direction=direction,
            recommended_actions=recommendations,
            defense_level_needed=defense_level,
        )

    def find_critical_thresholds(
        self, surface: FeasibilitySurface
    ) -> dict[str, float]:
        """
        Find exact critical thresholds where catastrophes occur.

        Identifies tipping points in parameter space.

        Args:
            surface: FeasibilitySurface from map_constraint_space()

        Returns:
            Dictionary of critical thresholds:
                - max_safe_demand: Maximum demand before failure
                - max_safe_strictness: Maximum strictness before failure
                - cusp_demand: Demand at cusp point
                - cusp_strictness: Strictness at cusp point

        Example:
            >>> thresholds = detector.find_critical_thresholds(surface)
            >>> print(f"Safe demand limit: {thresholds['max_safe_demand']:.2f}")
        """
        # Find maximum demand where feasibility > 0.7 for each strictness level
        max_safe_demand = 0.0
        max_safe_strictness = 0.0

        for i, strictness in enumerate(surface.strictness_values):
            feasible_demands = []
            for j, demand in enumerate(surface.demand_values):
                if surface.feasibility_grid[i, j] > 0.7:
                    feasible_demands.append(demand)

            if feasible_demands:
                safe_demand = max(feasible_demands)
                if safe_demand > max_safe_demand:
                    max_safe_demand = safe_demand
                    max_safe_strictness = strictness

        # Find cusp point (minimum feasibility on boundary)
        min_feasibility = 1.0
        cusp_demand = 0.0
        cusp_strictness = 0.0

        for i, strictness in enumerate(surface.strictness_values):
            for j, demand in enumerate(surface.demand_values):
                feas = surface.feasibility_grid[i, j]
                if 0.3 < feas < 0.7:  # On boundary
                    if feas < min_feasibility:
                        min_feasibility = feas
                        cusp_demand = demand
                        cusp_strictness = strictness

        return {
            "max_safe_demand": float(max_safe_demand),
            "max_safe_strictness": float(max_safe_strictness),
            "cusp_demand": float(cusp_demand),
            "cusp_strictness": float(cusp_strictness),
        }

    def _generate_recommendations(
        self,
        distance: float,
        direction: str,
        current_state: SystemState,
        will_fail: bool,
    ) -> list[str]:
        """Generate context-specific recommendations."""
        recommendations = []

        if will_fail:
            recommendations.append("URGENT: Reduce coverage demand or relax constraints")
            recommendations.append("Activate emergency contingency plans")
            recommendations.append("Consider load shedding non-essential activities")

        if distance < 0.2:
            recommendations.append("System near catastrophe boundary")
            recommendations.append("Increase capacity buffer immediately")

        if direction == "toward_cusp":
            recommendations.append("Parameter trajectory heading toward instability")
            recommendations.append("Reverse trend: decrease demand or increase flexibility")

        if current_state == SystemState.MARGINAL:
            recommendations.append("Schedule currently marginal - add safety margin")

        return recommendations

    def _recommend_defense_level(self, distance: float, will_fail: bool) -> DefenseLevel:
        """Recommend defense in depth level based on catastrophe proximity."""
        if will_fail or distance < 0.1:
            return DefenseLevel.EMERGENCY
        elif distance < 0.2:
            return DefenseLevel.CONTAINMENT
        elif distance < 0.3:
            return DefenseLevel.SAFETY_SYSTEMS
        elif distance < 0.5:
            return DefenseLevel.CONTROL
        else:
            return DefenseLevel.PREVENTION

    def create_alert(
        self,
        current_params: ParameterState,
        cusp_analysis: CuspAnalysis,
        distance: float,
    ) -> CatastropheAlert | None:
        """
        Create catastrophe alert if warranted.

        Args:
            current_params: Current system parameters
            cusp_analysis: Cusp analysis results
            distance: Distance to catastrophe boundary

        Returns:
            CatastropheAlert if alert warranted, None otherwise
        """
        # Determine region and severity
        if distance > 0.5:
            return None  # Too far to alert

        if distance < 0.1:
            region = CatastropheRegion.CATASTROPHIC
            severity = "critical"
            message = "CRITICAL: System at catastrophe boundary - immediate action required"
        elif distance < 0.2:
            region = CatastropheRegion.CRITICAL
            severity = "high"
            message = "System approaching catastrophe boundary - urgent intervention needed"
        elif distance < 0.3:
            region = CatastropheRegion.WARNING
            severity = "medium"
            message = "Warning: System entering unstable region"
        else:
            region = CatastropheRegion.STABLE
            severity = "low"
            message = "Advisory: Monitor system parameters closely"

        defense_level = self._recommend_defense_level(distance, distance < 0.15)

        return CatastropheAlert(
            severity=severity,
            region=region,
            message=message,
            current_params=current_params,
            distance_to_cusp=distance,
            recommended_defense_level=defense_level,
        )
