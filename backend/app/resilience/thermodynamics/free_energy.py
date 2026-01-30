"""
Free Energy and Energy Landscape Analysis.

This module implements thermodynamic concepts for schedule optimization:
- Free energy calculations using Helmholtz formulation
- Energy landscape analysis for understanding schedule stability
- Adaptive temperature scheduling for simulated annealing

Based on statistical mechanics principles applied to scheduling constraints.
"""

import math
from collections import Counter
from dataclasses import dataclass, field
from typing import Any

import numpy as np


@dataclass
class FreeEnergyMetrics:
    """
    Free energy metrics for schedule stability analysis.

    The Helmholtz free energy F = U - TS relates:
    - U (internal energy): Cost of constraint violations
    - T (temperature): Exploration vs exploitation parameter
    - S (entropy): Configuration diversity

    Lower free energy indicates more stable schedule configurations.
    """

    free_energy: float = 0.0
    internal_energy: float = 0.0
    entropy_term: float = 0.0
    temperature: float = 1.0
    constraint_violations: int = 0
    configuration_entropy: float = 0.0


@dataclass
class LandscapeFeatures:
    """Features of an energy landscape."""

    num_local_minima: int = 0
    basin_depths: list[float] = field(default_factory=list)
    ruggedness: float = 0.0
    barrier_heights: list[float] = field(default_factory=list)
    gradient_norms: list[float] = field(default_factory=list)


def _calculate_internal_energy(assignments: list[Any]) -> float:
    """
    Calculate internal energy (U) from constraint violations.

    Internal energy represents the "cost" of the current configuration
    based on constraint violations and preference mismatches.

    Args:
        assignments: List of assignment objects

    Returns:
        Internal energy value (higher = more violations)
    """
    if not assignments:
        return 0.0

    energy = 0.0

    # Count assignments per person (penalize overload)
    person_counts: Counter = Counter()
    for assignment in assignments:
        person_id = getattr(assignment, "person_id", None)
        if person_id:
            person_counts[person_id] += 1

            # Energy contribution from workload imbalance
    if person_counts:
        counts = list(person_counts.values())
        mean_count = sum(counts) / len(counts)
        variance = sum((c - mean_count) ** 2 for c in counts) / len(counts)
        energy += variance * 0.1  # Workload imbalance penalty

        # Energy contribution from constraint violations
    for assignment in assignments:
        # Check for score field (lower score = higher energy)
        score = getattr(assignment, "score", None)
        if score is not None:
            energy += (1.0 - score) * 0.5  # Preference mismatch penalty

            # Check for violation flags
        has_violation = getattr(assignment, "has_violation", False)
        if has_violation:
            energy += 1.0  # Hard constraint violation

    return energy


def _calculate_configuration_entropy(assignments: list[Any]) -> float:
    """
    Calculate configuration entropy (S) from assignment diversity.

    Entropy measures the diversity of the schedule configuration.
    Higher entropy = more diverse assignment distribution.

    Args:
        assignments: List of assignment objects

    Returns:
        Entropy value (in natural units)
    """
    if not assignments:
        return 0.0

        # Count unique configurations (person-rotation pairs)
    configs: Counter = Counter()
    for assignment in assignments:
        person_id = str(getattr(assignment, "person_id", "unknown"))
        rotation_id = str(getattr(assignment, "rotation_template_id", "unknown"))
        configs[(person_id, rotation_id)] += 1

    if not configs:
        return 0.0

        # Calculate Shannon entropy
    total = sum(configs.values())
    entropy = 0.0
    for count in configs.values():
        if count > 0:
            p = count / total
            entropy -= p * math.log(p)

    return entropy


def calculate_free_energy(
    assignments: list[Any], temperature: float = 1.0
) -> FreeEnergyMetrics:
    """
    Calculate Helmholtz free energy of a schedule.

    F = U - TS where:
    - F: Free energy (minimized at equilibrium)
    - U: Internal energy (constraint violations)
    - T: Temperature (exploration parameter)
    - S: Entropy (configuration diversity)

    Lower free energy indicates more stable schedule configurations.
    At high temperatures, entropy dominates (exploration).
    At low temperatures, internal energy dominates (exploitation).

    Args:
        assignments: Schedule assignments to analyze
        temperature: System temperature (T > 0)

    Returns:
        FreeEnergyMetrics with calculated values
    """
    if temperature <= 0:
        temperature = 0.001  # Avoid division by zero

        # Calculate components
    internal_energy = _calculate_internal_energy(assignments)
    entropy = _calculate_configuration_entropy(assignments)
    entropy_term = temperature * entropy

    # Helmholtz free energy
    free_energy = internal_energy - entropy_term

    # Count violations for reporting
    violations = sum(1 for a in assignments if getattr(a, "has_violation", False))

    return FreeEnergyMetrics(
        free_energy=free_energy,
        internal_energy=internal_energy,
        entropy_term=entropy_term,
        temperature=temperature,
        constraint_violations=violations,
        configuration_entropy=entropy,
    )


class EnergyLandscapeAnalyzer:
    """
    Analyze energy landscape of schedule space.

    The energy landscape metaphor helps understand:
    - Local minima: Stable schedule configurations
    - Basins: Regions that flow to same minimum
    - Barriers: Energy required to escape a basin
    - Ruggedness: Complexity of the landscape

    This is useful for:
    - Choosing optimization strategies
    - Understanding schedule stability
    - Identifying robust configurations
    """

    def __init__(self, sample_size: int = 100) -> None:
        """
        Initialize analyzer.

        Args:
            sample_size: Number of perturbations to sample
        """
        self.sample_size = sample_size
        self._rng = np.random.default_rng(42)

    def analyze_landscape(
        self, assignments: list[Any], temperature: float = 1.0
    ) -> dict[str, Any]:
        """
        Analyze energy landscape around current configuration.

        Performs local sampling to estimate landscape features:
        - Local minima detection via gradient analysis
        - Basin depth estimation
        - Ruggedness calculation

        Args:
            assignments: Current schedule configuration
            temperature: Temperature for energy calculation

        Returns:
            Dictionary with landscape analysis results
        """
        if not assignments:
            return {
                "features": LandscapeFeatures(),
                "current_energy": 0.0,
                "is_local_minimum": True,
                "estimated_basin_size": 0,
            }

            # Calculate current energy
        current_metrics = calculate_free_energy(assignments, temperature)
        current_energy = current_metrics.free_energy

        # Sample nearby configurations to estimate landscape
        energies = [current_energy]
        gradients = []

        for _ in range(min(self.sample_size, len(assignments))):
            # Create perturbed configuration
            perturbed = self._perturb_assignments(assignments)
            perturbed_metrics = calculate_free_energy(perturbed, temperature)
            perturbed_energy = perturbed_metrics.free_energy

            energies.append(perturbed_energy)
            gradients.append(perturbed_energy - current_energy)

            # Analyze results
        energy_array = np.array(energies)
        gradient_array = np.array(gradients)

        # Check if current is local minimum (all gradients >= 0)
        is_local_minimum = all(g >= -0.01 for g in gradients)

        # Estimate ruggedness (standard deviation of energies)
        ruggedness = float(np.std(energy_array)) if len(energy_array) > 1 else 0.0

        # Find barrier heights (energy increases from current)
        barriers = [g for g in gradients if g > 0]

        # Estimate basin depth (max energy decrease possible)
        basin_depths = [-g for g in gradients if g < 0] or [0.0]

        features = LandscapeFeatures(
            num_local_minima=1 if is_local_minimum else 0,
            basin_depths=basin_depths,
            ruggedness=ruggedness,
            barrier_heights=barriers,
            gradient_norms=[abs(g) for g in gradients],
        )

        return {
            "features": features,
            "current_energy": current_energy,
            "is_local_minimum": is_local_minimum,
            "estimated_basin_size": len([g for g in gradients if g >= 0]),
            "mean_barrier_height": np.mean(barriers) if barriers else 0.0,
            "mean_gradient": float(np.mean(np.abs(gradient_array)))
            if len(gradient_array) > 0
            else 0.0,
            "landscape_ruggedness": ruggedness,
        }

    def _perturb_assignments(self, assignments: list[Any]) -> list[Any]:
        """
        Create a perturbed copy of assignments.

        This is a simple perturbation that shuffles some assignments.
        In a full implementation, this would swap assignments between
        compatible persons/blocks.

        Args:
            assignments: Original assignments

        Returns:
            Perturbed assignment list
        """
        if len(assignments) <= 1:
            return assignments

            # Create a shallow copy and randomly swap a few elements
        perturbed = list(assignments)
        num_swaps = max(1, len(perturbed) // 10)

        for _ in range(num_swaps):
            i = self._rng.integers(0, len(perturbed))
            j = self._rng.integers(0, len(perturbed))
            perturbed[i], perturbed[j] = perturbed[j], perturbed[i]

        return perturbed

    def find_local_minima(
        self, assignments: list[Any], max_iterations: int = 100
    ) -> list[dict[str, Any]]:
        """
        Search for local minima in the energy landscape.

        Uses gradient descent with random restarts to find
        multiple local minima.

        Args:
            assignments: Starting configuration
            max_iterations: Maximum descent iterations

        Returns:
            List of local minimum configurations found
        """
        minima = []
        current = assignments
        current_energy = calculate_free_energy(current).free_energy

        for _ in range(max_iterations):
            # Try a perturbation
            candidate = self._perturb_assignments(current)
            candidate_energy = calculate_free_energy(candidate).free_energy

            # Accept if lower energy
            if candidate_energy < current_energy:
                current = candidate
                current_energy = candidate_energy

                # Record the found minimum
        minima.append(
            {
                "energy": current_energy,
                "is_minimum": True,
            }
        )

        return minima


def adaptive_temperature(
    iteration: int,
    initial_temp: float = 10.0,
    cooling_rate: float = 0.95,
    schedule: str = "exponential",
    min_temp: float = 0.01,
) -> float:
    """
    Calculate adaptive temperature for simulated annealing.

    Supports multiple cooling schedules:
    - exponential: T(t) = T0 * rate^t (fast cooling)
    - linear: T(t) = T0 - rate * t (constant cooling)
    - logarithmic: T(t) = T0 / log(t + 2) (slow cooling, proven optimal)
    - adaptive: Adjusts based on acceptance rate

    Args:
        iteration: Current iteration (t >= 0)
        initial_temp: Initial temperature (T0)
        cooling_rate: Rate parameter (interpretation depends on schedule)
        schedule: Cooling schedule type
        min_temp: Minimum temperature floor

    Returns:
        Temperature at current iteration
    """
    if iteration < 0:
        iteration = 0

    if schedule == "exponential":
        # Geometric cooling: T(t) = T0 * rate^t
        temp = initial_temp * (cooling_rate**iteration)

    elif schedule == "linear":
        # Linear cooling: T(t) = max(T0 - rate * t, min_temp)
        temp = initial_temp - cooling_rate * iteration

    elif schedule == "logarithmic":
        # Logarithmic cooling: T(t) = T0 / log(t + 2)
        # This is proven to be asymptotically optimal for SA
        temp = initial_temp / math.log(iteration + 2)

    elif schedule == "cauchy":
        # Cauchy cooling: T(t) = T0 / (1 + t)
        # Faster than logarithmic, still good convergence
        temp = initial_temp / (1 + iteration)

    elif schedule == "boltzmann":
        # Boltzmann cooling: T(t) = T0 / (1 + log(1 + t))
        # Compromise between logarithmic and cauchy
        temp = initial_temp / (1 + math.log(1 + iteration))

    else:
        # Default to exponential
        temp = initial_temp * (cooling_rate**iteration)

    return max(temp, min_temp)


def boltzmann_probability(energy_delta: float, temperature: float) -> float:
    """
    Calculate Boltzmann acceptance probability.

    P(accept) = exp(-ΔE / T) when ΔE > 0
    P(accept) = 1 when ΔE <= 0

    This is the Metropolis criterion for simulated annealing.

    Args:
        energy_delta: Change in energy (new - old)
        temperature: Current temperature (T > 0)

    Returns:
        Probability of accepting the transition [0, 1]
    """
    if energy_delta <= 0:
        return 1.0  # Always accept improvements

    if temperature <= 0:
        return 0.0  # Never accept worsening at T=0

        # Boltzmann factor
    exponent = -energy_delta / temperature
    if exponent < -700:  # Avoid underflow
        return 0.0

    return math.exp(exponent)
