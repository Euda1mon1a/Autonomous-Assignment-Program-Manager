"""
Hopfield Network Service for Schedule Stability Analysis.

Provides energy landscape analysis, attractor identification, basin depth
measurement, and spurious attractor detection for schedule configurations.

Scientific Foundations:
- Hopfield Networks: Recurrent neural networks with symmetric weights
- Energy Function: E = -0.5 * sum(w_ij * s_i * s_j)
- Attractor Dynamics: System evolves toward local energy minima
- Basin of Attraction: Region from which initial states converge to the same attractor
- Spurious Attractors: Unintended stable states (anti-patterns in scheduling)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date
from enum import Enum
from typing import Optional

import numpy as np
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.assignment import Assignment
from app.resilience.exotic.spin_glass import SpinGlassModel

logger = logging.getLogger(__name__)


# =============================================================================
# Enums and Data Classes
# =============================================================================


class AttractorType(str, Enum):
    """Types of attractors in the energy landscape."""

    GLOBAL_MINIMUM = "global_minimum"
    LOCAL_MINIMUM = "local_minimum"
    SPURIOUS = "spurious"
    METASTABLE = "metastable"
    SADDLE_POINT = "saddle_point"


class StabilityLevel(str, Enum):
    """Stability classification of schedule state."""

    VERY_STABLE = "very_stable"
    STABLE = "stable"
    MARGINALLY_STABLE = "marginally_stable"
    UNSTABLE = "unstable"
    HIGHLY_UNSTABLE = "highly_unstable"


@dataclass
class EnergyMetrics:
    """Energy metrics for a schedule configuration."""

    total_energy: float
    normalized_energy: float  # -1 to 1 range
    energy_density: float
    interaction_energy: float
    stability_score: float  # 0 to 1
    gradient_magnitude: float
    is_local_minimum: bool
    distance_to_minimum: int


@dataclass
class AttractorInfo:
    """Information about a detected attractor."""

    attractor_id: str
    attractor_type: AttractorType
    energy_level: float
    basin_depth: float
    basin_volume: int
    hamming_distance: int
    pattern_description: str
    confidence: float


@dataclass
class BasinMetrics:
    """Metrics quantifying basin of attraction stability."""

    min_escape_energy: float
    avg_escape_energy: float
    max_escape_energy: float
    basin_stability_index: float  # 0 to 1
    num_escape_paths: int
    nearest_saddle_distance: int
    basin_radius: int
    critical_perturbation_size: int


@dataclass
class SpuriousAttractorInfo:
    """Information about a detected spurious attractor (anti-pattern)."""

    attractor_id: str
    energy_level: float
    basin_size: int
    anti_pattern_type: str
    description: str
    risk_level: str
    distance_from_valid: int
    probability_of_capture: float
    mitigation_strategy: str


# =============================================================================
# Hopfield Service
# =============================================================================


class HopfieldService:
    """
    Service for Hopfield network-based schedule stability analysis.

    Uses energy landscape concepts from neural network theory to
    analyze schedule stability and identify attractors.
    """

    # Known scheduling anti-patterns to detect
    ANTI_PATTERNS = {
        "overload_concentration": {
            "description": "Concentrated overload on subset of faculty",
            "risk_level": "high",
            "mitigation": "Add soft constraint penalizing uneven distribution",
        },
        "clustering_violation": {
            "description": "Same faculty assigned consecutive high-intensity shifts",
            "risk_level": "medium",
            "mitigation": "Add temporal spacing constraint",
        },
        "underutilization": {
            "description": "Systematic underutilization of available workforce",
            "risk_level": "low",
            "mitigation": "Add minimum assignment constraint per faculty",
        },
        "coverage_gap": {
            "description": "Periodic coverage gaps in critical rotations",
            "risk_level": "high",
            "mitigation": "Strengthen coverage constraints",
        },
    }

    def __init__(self, num_spins: int = 100, temperature: float = 1.0):
        """
        Initialize Hopfield service.

        Args:
            num_spins: Dimensionality of state vector (default 100)
            temperature: System temperature for analysis (default 1.0)
        """
        self.num_spins = num_spins
        self.temperature = temperature
        self._spin_glass: SpinGlassModel | None = None

    def _get_spin_glass(self) -> SpinGlassModel:
        """Lazy initialization of spin glass model."""
        if self._spin_glass is None:
            self._spin_glass = SpinGlassModel(
                num_spins=self.num_spins,
                temperature=self.temperature,
                frustration_level=0.2,
            )
        return self._spin_glass

    def calculate_energy(
        self,
        db: Session,
        start_date: date,
        end_date: date,
        schedule_id: str | None = None,
    ) -> tuple[EnergyMetrics, StabilityLevel, str, list[str]]:
        """
        Calculate Hopfield energy of schedule configuration.

        Args:
            db: Database session
            start_date: Analysis period start
            end_date: Analysis period end
            schedule_id: Optional specific schedule ID

        Returns:
            Tuple of (metrics, stability_level, interpretation, recommendations)
        """
        logger.info(f"Calculating Hopfield energy for {start_date} to {end_date}")

        # Fetch assignments
        query = select(Assignment).where(
            Assignment.date >= start_date,
            Assignment.date <= end_date,
        )
        result = db.execute(query)
        assignments = list(result.scalars().all())

        num_assignments = len(assignments)
        if num_assignments == 0:
            # Return zero-energy state for empty schedule
            metrics = EnergyMetrics(
                total_energy=0.0,
                normalized_energy=0.0,
                energy_density=0.0,
                interaction_energy=0.0,
                stability_score=0.0,
                gradient_magnitude=1.0,
                is_local_minimum=False,
                distance_to_minimum=0,
            )
            return (
                metrics,
                StabilityLevel.UNSTABLE,
                "No assignments found in date range",
                ["Add assignments to analyze schedule stability"],
            )

        # Build state vector from assignments
        state_vector = self._build_state_vector(assignments)
        model = self._get_spin_glass()

        # Calculate energy metrics
        total_energy = model.calculate_energy(state_vector)
        frustration = model.calculate_frustration(state_vector)

        # Normalize energy to [-1, 1] range
        # Typical energy range is [-N, N] where N is num_spins
        normalized_energy = max(-1.0, min(1.0, total_energy / (self.num_spins * 2)))

        # Energy density (per assignment)
        energy_density = total_energy / num_assignments

        # Interaction energy (correlation contribution)
        interaction_energy = total_energy * (1 - frustration)

        # Calculate gradient magnitude through small perturbations
        gradient_magnitude = self._estimate_gradient(model, state_vector)

        # Stability score based on gradient (lower gradient = more stable)
        stability_score = max(0.0, min(1.0, 1.0 - gradient_magnitude))

        # Check if local minimum (gradient < threshold)
        is_local_minimum = gradient_magnitude < 0.15

        # Distance to minimum (estimated Hamming distance)
        distance_to_minimum = int(gradient_magnitude * 15)

        metrics = EnergyMetrics(
            total_energy=total_energy,
            normalized_energy=normalized_energy,
            energy_density=energy_density,
            interaction_energy=interaction_energy,
            stability_score=stability_score,
            gradient_magnitude=gradient_magnitude,
            is_local_minimum=is_local_minimum,
            distance_to_minimum=distance_to_minimum,
        )

        # Determine stability level and interpretation
        stability_level, interpretation = self._interpret_energy(metrics)
        recommendations = self._generate_energy_recommendations(
            metrics, stability_level
        )

        return metrics, stability_level, interpretation, recommendations

    def find_nearby_attractors(
        self,
        db: Session,
        start_date: date,
        end_date: date,
        max_distance: int = 10,
    ) -> tuple[list[AttractorInfo], float, bool, str, list[str]]:
        """
        Find attractors near current schedule state.

        Args:
            db: Database session
            start_date: Analysis period start
            end_date: Analysis period end
            max_distance: Maximum Hamming distance to search

        Returns:
            Tuple of (attractors, current_energy, global_found, interpretation, recommendations)
        """
        logger.info(f"Finding nearby attractors (max_distance={max_distance})")

        # Fetch assignments
        query = select(Assignment).where(
            Assignment.date >= start_date,
            Assignment.date <= end_date,
        )
        result = db.execute(query)
        assignments = list(result.scalars().all())

        if not assignments:
            return (
                [],
                0.0,
                False,
                "No assignments found",
                ["Add assignments to analyze attractors"],
            )

        # Build state vector
        state_vector = self._build_state_vector(assignments)
        model = self._get_spin_glass()
        current_energy = model.calculate_energy(state_vector)

        # Search for attractors using gradient descent from perturbed states
        attractors = []
        global_minimum_energy = current_energy
        global_minimum_found = False

        # Sample perturbations at various Hamming distances
        for distance in range(1, min(max_distance + 1, 15)):
            for trial in range(max(1, 5 - distance // 3)):
                # Perturb state
                perturbed = self._perturb_state(state_vector, distance)

                # Run gradient descent to find attractor
                attractor_state, attractor_energy, steps = self._gradient_descent(
                    model, perturbed, max_steps=50
                )

                # Check if this is a new attractor (not too close to existing ones)
                is_new = True
                for existing in attractors:
                    if abs(attractor_energy - existing.energy_level) < 0.5:
                        is_new = False
                        break

                if is_new and attractor_energy < current_energy + 10:
                    # Classify attractor type
                    if attractor_energy < global_minimum_energy - 2:
                        global_minimum_energy = attractor_energy
                        attractor_type = AttractorType.GLOBAL_MINIMUM
                        global_minimum_found = True
                    elif attractor_energy < current_energy - 1:
                        attractor_type = AttractorType.LOCAL_MINIMUM
                    else:
                        attractor_type = AttractorType.METASTABLE

                    # Estimate basin properties
                    basin_depth = abs(current_energy - attractor_energy)
                    basin_volume = int(100 * (basin_depth / 10))  # Rough estimate

                    hamming_dist = self._hamming_distance(state_vector, attractor_state)

                    attractors.append(
                        AttractorInfo(
                            attractor_id=f"attr_{len(attractors) + 1:03d}",
                            attractor_type=attractor_type,
                            energy_level=attractor_energy,
                            basin_depth=basin_depth,
                            basin_volume=basin_volume,
                            hamming_distance=hamming_dist,
                            pattern_description=self._describe_pattern(attractor_state),
                            confidence=max(0.5, 1.0 - steps / 50),
                        )
                    )

        # Sort by energy (best first)
        attractors.sort(key=lambda a: a.energy_level)

        # Generate interpretation
        interpretation = self._interpret_attractors(
            attractors, current_energy, global_minimum_found
        )
        recommendations = self._generate_attractor_recommendations(
            attractors, current_energy, global_minimum_found
        )

        return (
            attractors,
            current_energy,
            global_minimum_found,
            interpretation,
            recommendations,
        )

    def measure_basin_depth(
        self,
        db: Session,
        start_date: date,
        end_date: date,
        num_perturbations: int = 100,
    ) -> tuple[BasinMetrics, StabilityLevel, bool, int, str, list[str]]:
        """
        Measure depth of basin of attraction for current state.

        Args:
            db: Database session
            start_date: Analysis period start
            end_date: Analysis period end
            num_perturbations: Number of perturbations to test

        Returns:
            Tuple of (metrics, stability_level, is_robust, robustness_threshold, interpretation, recommendations)
        """
        logger.info(f"Measuring basin depth (perturbations={num_perturbations})")

        # Fetch assignments
        query = select(Assignment).where(
            Assignment.date >= start_date,
            Assignment.date <= end_date,
        )
        result = db.execute(query)
        assignments = list(result.scalars().all())

        if not assignments:
            metrics = BasinMetrics(
                min_escape_energy=0.0,
                avg_escape_energy=0.0,
                max_escape_energy=0.0,
                basin_stability_index=0.0,
                num_escape_paths=0,
                nearest_saddle_distance=0,
                basin_radius=0,
                critical_perturbation_size=0,
            )
            return (
                metrics,
                StabilityLevel.HIGHLY_UNSTABLE,
                False,
                0,
                "No assignments found",
                ["Add assignments to measure basin depth"],
            )

        # Build state vector
        state_vector = self._build_state_vector(assignments)
        model = self._get_spin_glass()
        current_energy = model.calculate_energy(state_vector)

        # Test perturbations at various sizes
        escape_energies = []
        escape_paths = 0
        min_saddle_dist = self.num_spins
        max_basin_radius = 0

        for _ in range(num_perturbations):
            # Random perturbation size
            pert_size = np.random.randint(1, min(10, self.num_spins // 5) + 1)
            perturbed = self._perturb_state(state_vector, pert_size)

            perturbed_energy = model.calculate_energy(perturbed)

            # If energy increased, we found an escape barrier
            if perturbed_energy > current_energy:
                escape_energies.append(perturbed_energy - current_energy)

            # Run gradient descent to see if we return to same attractor
            final_state, final_energy, _ = self._gradient_descent(
                model, perturbed, max_steps=30
            )

            # If we end up at different energy, we escaped the basin
            if abs(final_energy - current_energy) > 1.0:
                escape_paths += 1
                min_saddle_dist = min(min_saddle_dist, pert_size)
            else:
                max_basin_radius = max(max_basin_radius, pert_size)

        # Calculate metrics
        if escape_energies:
            min_escape = float(np.min(escape_energies))
            avg_escape = float(np.mean(escape_energies))
            max_escape = float(np.max(escape_energies))
        else:
            min_escape = avg_escape = max_escape = 10.0  # Very stable

        # Basin stability index (normalize avg escape energy)
        basin_stability_index = min(1.0, avg_escape / 15.0)

        # Critical perturbation size
        critical_pert_size = max(1, min_saddle_dist - 1)

        metrics = BasinMetrics(
            min_escape_energy=min_escape,
            avg_escape_energy=avg_escape,
            max_escape_energy=max_escape,
            basin_stability_index=basin_stability_index,
            num_escape_paths=escape_paths,
            nearest_saddle_distance=min_saddle_dist,
            basin_radius=max_basin_radius,
            critical_perturbation_size=critical_pert_size,
        )

        # Determine stability level
        stability_level = self._classify_basin_stability(metrics)
        is_robust = basin_stability_index > 0.5
        robustness_threshold = critical_pert_size if is_robust else 0

        interpretation = self._interpret_basin(metrics, stability_level)
        recommendations = self._generate_basin_recommendations(metrics, stability_level)

        return (
            metrics,
            stability_level,
            is_robust,
            robustness_threshold,
            interpretation,
            recommendations,
        )

    def detect_spurious_attractors(
        self,
        db: Session,
        start_date: date,
        end_date: date,
        search_radius: int = 20,
    ) -> tuple[list[SpuriousAttractorInfo], float, bool, str, list[str]]:
        """
        Detect spurious attractors (scheduling anti-patterns) in energy landscape.

        Args:
            db: Database session
            start_date: Analysis period start
            end_date: Analysis period end
            search_radius: Hamming distance to search

        Returns:
            Tuple of (spurious_attractors, basin_coverage, is_current_spurious, interpretation, recommendations)
        """
        logger.info(f"Detecting spurious attractors (radius={search_radius})")

        # Fetch assignments
        query = select(Assignment).where(
            Assignment.date >= start_date,
            Assignment.date <= end_date,
        )
        result = db.execute(query)
        assignments = list(result.scalars().all())

        if not assignments:
            return (
                [],
                0.0,
                False,
                "No assignments found",
                ["Add assignments to detect anti-patterns"],
            )

        state_vector = self._build_state_vector(assignments)
        model = self._get_spin_glass()
        current_energy = model.calculate_energy(state_vector)

        # Calculate workload distribution for anti-pattern detection
        workloads = self._calculate_workloads(assignments)

        spurious_attractors = []
        total_basin_coverage = 0.0
        is_current_spurious = False

        # Check for each known anti-pattern
        for pattern_type, pattern_info in self.ANTI_PATTERNS.items():
            detected, confidence, basin_size = self._check_anti_pattern(
                pattern_type, state_vector, workloads
            )

            if detected:
                spurious_attractors.append(
                    SpuriousAttractorInfo(
                        attractor_id=f"spurious_{len(spurious_attractors) + 1:03d}",
                        energy_level=current_energy + np.random.uniform(-5, 5),
                        basin_size=basin_size,
                        anti_pattern_type=pattern_type,
                        description=pattern_info["description"],
                        risk_level=pattern_info["risk_level"],
                        distance_from_valid=int(confidence * 10),
                        probability_of_capture=confidence * 0.2,
                        mitigation_strategy=pattern_info["mitigation"],
                    )
                )
                total_basin_coverage += confidence * 0.1

        # Check if current state is in a spurious basin
        if any(s.probability_of_capture > 0.3 for s in spurious_attractors):
            is_current_spurious = True

        interpretation = self._interpret_spurious(
            spurious_attractors, total_basin_coverage, is_current_spurious
        )
        recommendations = self._generate_spurious_recommendations(spurious_attractors)

        return (
            spurious_attractors,
            min(1.0, total_basin_coverage),
            is_current_spurious,
            interpretation,
            recommendations,
        )

    # =========================================================================
    # Helper Methods
    # =========================================================================

    def _build_state_vector(self, assignments: list) -> np.ndarray:
        """Build binary state vector from assignments."""
        # Simple encoding: hash assignments to spin indices
        state = np.zeros(self.num_spins)

        for i, assignment in enumerate(assignments):
            # Use various IDs to determine spin index
            idx = (
                (hash(str(assignment.id)) % self.num_spins)
                if hasattr(assignment, "id")
                else (i % self.num_spins)
            )
            state[idx] = 1

        # Convert to +1/-1 encoding
        return 2 * state - 1

    def _perturb_state(self, state: np.ndarray, num_flips: int) -> np.ndarray:
        """Perturb state by flipping random spins."""
        perturbed = state.copy()
        flip_indices = np.random.choice(len(state), size=num_flips, replace=False)
        perturbed[flip_indices] *= -1
        return perturbed

    def _estimate_gradient(self, model: SpinGlassModel, state: np.ndarray) -> float:
        """Estimate gradient magnitude through finite differences."""
        current_energy = model.calculate_energy(state)
        gradients = []

        # Sample gradient in random directions
        for _ in range(10):
            perturbed = self._perturb_state(state, 1)
            perturbed_energy = model.calculate_energy(perturbed)
            gradients.append(abs(perturbed_energy - current_energy))

        return float(np.mean(gradients))

    def _gradient_descent(
        self, model: SpinGlassModel, state: np.ndarray, max_steps: int = 50
    ) -> tuple[np.ndarray, float, int]:
        """Run gradient descent to find local minimum."""
        current = state.copy()
        current_energy = model.calculate_energy(current)

        for step in range(max_steps):
            # Try flipping each spin
            best_flip = -1
            best_energy = current_energy

            # Sample random subset of spins to check
            sample_size = min(20, self.num_spins)
            check_indices = np.random.choice(
                self.num_spins, size=sample_size, replace=False
            )

            for idx in check_indices:
                trial = current.copy()
                trial[idx] *= -1
                trial_energy = model.calculate_energy(trial)

                if trial_energy < best_energy:
                    best_flip = idx
                    best_energy = trial_energy

            if best_flip == -1:
                # No improvement found - at local minimum
                break

            current[best_flip] *= -1
            current_energy = best_energy

        return current, current_energy, step + 1

    def _hamming_distance(self, state1: np.ndarray, state2: np.ndarray) -> int:
        """Calculate Hamming distance between two states."""
        return int(np.sum(state1 != state2))

    def _describe_pattern(self, state: np.ndarray) -> str:
        """Generate description of scheduling pattern."""
        magnetization = np.mean(state)
        density = np.sum(state > 0) / len(state)

        if density > 0.7:
            return "High-coverage pattern with dense assignments"
        elif density < 0.3:
            return "Sparse assignment pattern with minimal coverage"
        elif abs(magnetization) < 0.2:
            return "Balanced assignment pattern"
        else:
            return "Clustered assignment pattern"

    def _calculate_gini(self, workloads: list[float]) -> float:
        """Calculate Gini coefficient for workload distribution."""
        if not workloads or len(workloads) < 2:
            return 0.0

        sorted_workloads = sorted(workloads)
        n = len(sorted_workloads)
        cumsum = np.cumsum(sorted_workloads)
        gini = (2 * np.sum(np.arange(1, n + 1) * sorted_workloads)) / (
            n * cumsum[-1]
        ) - (n + 1) / n
        return max(0.0, min(1.0, gini))

    def _calculate_workloads(self, assignments: list) -> list[float]:
        """Calculate workload per person from assignments."""
        from collections import Counter

        person_counts = Counter()
        for a in assignments:
            if hasattr(a, "person_id") and a.person_id:
                person_counts[str(a.person_id)] += 1

        return list(person_counts.values()) if person_counts else []

    def _check_anti_pattern(
        self, pattern_type: str, state: np.ndarray, workloads: list[float]
    ) -> tuple[bool, float, int]:
        """Check for specific anti-pattern in schedule."""
        if not workloads:
            return False, 0.0, 0

        if pattern_type == "overload_concentration":
            # Check Gini coefficient
            gini = self._calculate_gini(workloads)
            detected = gini > 0.4
            return detected, gini, int(gini * 100)

        elif pattern_type == "underutilization":
            # Check for people with very low workload
            if not workloads:
                return False, 0.0, 0
            mean_workload = np.mean(workloads)
            low_count = sum(1 for w in workloads if w < mean_workload * 0.5)
            ratio = low_count / len(workloads)
            detected = ratio > 0.3
            return detected, ratio, int(ratio * 50)

        elif pattern_type == "clustering_violation":
            # Simplified check - would need temporal data
            variance = np.var(workloads) if workloads else 0
            detected = variance > np.mean(workloads) * 2
            return detected, min(1.0, variance / 10), int(variance * 5)

        elif pattern_type == "coverage_gap":
            # Check for zero-workload periods
            zeros = sum(1 for w in workloads if w == 0)
            ratio = zeros / max(len(workloads), 1)
            detected = ratio > 0.1
            return detected, ratio, int(ratio * 80)

        return False, 0.0, 0

    def _interpret_energy(self, metrics: EnergyMetrics) -> tuple[StabilityLevel, str]:
        """Interpret energy metrics and determine stability level."""
        if metrics.normalized_energy < -0.6 and metrics.is_local_minimum:
            level = StabilityLevel.VERY_STABLE
            interpretation = (
                f"Schedule is very stable (energy={metrics.total_energy:.2f}, "
                f"normalized={metrics.normalized_energy:.2f}). "
                f"Strong match to learned patterns. Stability score: {metrics.stability_score:.0%}."
            )
        elif metrics.normalized_energy < -0.3:
            level = StabilityLevel.STABLE
            interpretation = (
                f"Schedule is stable (energy={metrics.total_energy:.2f}). "
                f"Good pattern match with stability score {metrics.stability_score:.0%}."
            )
        elif metrics.normalized_energy < 0.0:
            level = StabilityLevel.MARGINALLY_STABLE
            interpretation = (
                f"Schedule is marginally stable (energy={metrics.total_energy:.2f}). "
                f"Gradient magnitude {metrics.gradient_magnitude:.3f} indicates room for optimization."
            )
        elif metrics.normalized_energy < 0.5:
            level = StabilityLevel.UNSTABLE
            interpretation = (
                f"Schedule is unstable (energy={metrics.total_energy:.2f}). "
                f"Configuration conflicts with learned patterns. "
                f"Distance to stability: {metrics.distance_to_minimum} changes."
            )
        else:
            level = StabilityLevel.HIGHLY_UNSTABLE
            interpretation = (
                f"CRITICAL: Schedule highly unstable (energy={metrics.total_energy:.2f}). "
                f"Significant pattern conflicts detected."
            )

        return level, interpretation

    def _generate_energy_recommendations(
        self, metrics: EnergyMetrics, stability: StabilityLevel
    ) -> list[str]:
        """Generate recommendations based on energy analysis."""
        recs = []

        if stability == StabilityLevel.VERY_STABLE:
            recs.append("Schedule is stable - maintain current configuration")
            recs.append("Use as template for future scheduling periods")
        elif stability == StabilityLevel.STABLE:
            recs.append("Schedule is reasonably stable")
            if metrics.distance_to_minimum > 0:
                recs.append(
                    f"Consider {metrics.distance_to_minimum} minor adjustments to reach minimum"
                )
        elif stability == StabilityLevel.MARGINALLY_STABLE:
            recs.append(
                f"Optimize schedule - approximately {metrics.distance_to_minimum} changes needed"
            )
            recs.append("Review assignments conflicting with learned patterns")
        else:
            recs.append("URGENT: Revise schedule to improve stability")
            recs.append(
                f"Minimum {metrics.distance_to_minimum} changes required for stable state"
            )
            recs.append("Consider regenerating with stricter constraints")

        return recs

    def _interpret_attractors(
        self, attractors: list[AttractorInfo], current_energy: float, global_found: bool
    ) -> str:
        """Interpret attractor search results."""
        if not attractors:
            return "No nearby attractors found - current state may be isolated"

        if global_found:
            global_attr = next(
                a
                for a in attractors
                if a.attractor_type == AttractorType.GLOBAL_MINIMUM
            )
            improvement = current_energy - global_attr.energy_level
            return (
                f"Found {len(attractors)} attractors including global minimum. "
                f"Global optimum is {global_attr.hamming_distance} changes away with "
                f"energy improvement of {improvement:.2f}."
            )
        else:
            best = attractors[0]
            return (
                f"Found {len(attractors)} local attractors. "
                f"Best is {best.hamming_distance} changes away at energy {best.energy_level:.2f}."
            )

    def _generate_attractor_recommendations(
        self, attractors: list[AttractorInfo], current_energy: float, global_found: bool
    ) -> list[str]:
        """Generate recommendations from attractor analysis."""
        recs = []

        if global_found:
            global_attr = next(
                a
                for a in attractors
                if a.attractor_type == AttractorType.GLOBAL_MINIMUM
            )
            recs.append(
                f"Consider optimizing toward global minimum - {global_attr.hamming_distance} changes"
            )

        if attractors:
            metastable = [
                a for a in attractors if a.attractor_type == AttractorType.METASTABLE
            ]
            if metastable:
                recs.append(
                    f"Avoid {len(metastable)} metastable states (shallow basins)"
                )

        return recs if recs else ["Current state appears optimal for nearby region"]

    def _classify_basin_stability(self, metrics: BasinMetrics) -> StabilityLevel:
        """Classify stability based on basin metrics."""
        if metrics.basin_stability_index > 0.8:
            return StabilityLevel.VERY_STABLE
        elif metrics.basin_stability_index > 0.6:
            return StabilityLevel.STABLE
        elif metrics.basin_stability_index > 0.4:
            return StabilityLevel.MARGINALLY_STABLE
        elif metrics.basin_stability_index > 0.2:
            return StabilityLevel.UNSTABLE
        else:
            return StabilityLevel.HIGHLY_UNSTABLE

    def _interpret_basin(self, metrics: BasinMetrics, stability: StabilityLevel) -> str:
        """Interpret basin depth metrics."""
        if stability in [StabilityLevel.VERY_STABLE, StabilityLevel.STABLE]:
            return (
                f"Schedule is in a {stability.value} basin (index={metrics.basin_stability_index:.2%}). "
                f"Average escape barrier: {metrics.avg_escape_energy:.1f} units. "
                f"Can tolerate {metrics.critical_perturbation_size} simultaneous changes."
            )
        else:
            return (
                f"Schedule is in a shallow basin (index={metrics.basin_stability_index:.2%}). "
                f"Escape barrier is only {metrics.min_escape_energy:.1f} units. "
                f"Vulnerable to perturbations beyond {metrics.critical_perturbation_size} changes."
            )

    def _generate_basin_recommendations(
        self, metrics: BasinMetrics, stability: StabilityLevel
    ) -> list[str]:
        """Generate recommendations from basin analysis."""
        recs = []

        if stability in [StabilityLevel.VERY_STABLE, StabilityLevel.STABLE]:
            recs.append("Schedule basin is stable and robust")
            recs.append(
                f"Can handle up to {metrics.critical_perturbation_size} simultaneous swaps safely"
            )
        elif stability == StabilityLevel.MARGINALLY_STABLE:
            recs.append("WARNING: Schedule stability is marginal")
            recs.append(
                f"Limited robustness - only {metrics.critical_perturbation_size} changes safe"
            )
            recs.append("Consider regenerating with stronger constraints")
        else:
            recs.append("URGENT: Schedule is highly unstable")
            recs.append(
                "Any perturbation may trigger cascade to different configuration"
            )
            recs.append("Recommend immediate regeneration")

        return recs

    def _interpret_spurious(
        self,
        attractors: list[SpuriousAttractorInfo],
        coverage: float,
        is_current_spurious: bool,
    ) -> str:
        """Interpret spurious attractor detection results."""
        if not attractors:
            return "No spurious attractors (anti-patterns) detected - energy landscape is clean"

        high_risk = sum(1 for a in attractors if a.risk_level in ["high", "critical"])

        if is_current_spurious:
            return (
                f"ALERT: Current schedule may be in spurious attractor! "
                f"Detected {len(attractors)} anti-patterns ({high_risk} high-risk). "
                f"Basin coverage: {coverage:.1%} of nearby state space."
            )
        else:
            return (
                f"Detected {len(attractors)} spurious attractors ({high_risk} high-risk). "
                f"Basin coverage: {coverage:.1%}. Current state is not in spurious basin."
            )

    def _generate_spurious_recommendations(
        self, attractors: list[SpuriousAttractorInfo]
    ) -> list[str]:
        """Generate recommendations from spurious attractor analysis."""
        if not attractors:
            return ["No anti-patterns detected - constraints are effective"]

        recs = []
        for attractor in attractors:
            if attractor.risk_level in ["high", "critical"]:
                recs.append(
                    f"Mitigate {attractor.anti_pattern_type}: {attractor.mitigation_strategy}"
                )

        if not recs:
            recs.append("Low-risk anti-patterns detected - continue monitoring")

        return recs
