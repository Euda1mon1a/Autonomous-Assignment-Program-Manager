"""
Free Energy and Energy Landscape Analysis.

This module provides thermodynamic-inspired analysis for schedule optimization:
- Helmholtz free energy calculation for schedule stability
- Energy landscape analysis for optimization guidance
- Adaptive temperature scheduling for simulated annealing
- Boltzmann distribution sampling for probabilistic assignment

Theory:
    Free energy F = U - TS combines internal energy U (constraint violations,
    workload imbalance) with entropy S (schedule flexibility). Lower free
    energy indicates a more stable, optimal schedule configuration.

Example:
    assignments = get_current_schedule()
    metrics = calculate_free_energy(assignments, temperature=2.0)
    print(f"Schedule stability score: {-metrics.free_energy:.2f}")
"""

import logging
import math
from collections import Counter
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class FreeEnergyMetrics:
    """
    Free energy metrics for schedule stability analysis.

    Attributes:
        free_energy: Helmholtz free energy F = U - TS (lower is better)
        internal_energy: Sum of constraint violations and imbalances
        entropy_term: Measure of schedule flexibility/diversity
        temperature: System temperature (controls exploration vs exploitation)
        partition_function: Z = sum(exp(-E_i/T)) normalization constant
        probability_distribution: Boltzmann probabilities for states
    """

    free_energy: float = 0.0
    internal_energy: float = 0.0
    entropy_term: float = 0.0
    temperature: float = 1.0
    partition_function: float = 1.0
    probability_distribution: dict[str, float] = field(default_factory=dict)

    @property
    def stability_score(self) -> float:
        """
        Calculate stability score (normalized, higher is better).

        Returns:
            Score between 0.0 and 1.0
        """
        # Convert free energy to 0-1 scale using sigmoid
        return 1.0 / (1.0 + math.exp(self.free_energy / max(self.temperature, 0.001)))


def _calculate_internal_energy(assignments: list[Any]) -> float:
    """
    Calculate internal energy from constraint violations and workload imbalance.

    Internal energy measures the "cost" of the current schedule state:
    - Constraint violations add to energy
    - Workload imbalance adds to energy
    - Coverage gaps add to energy

    Args:
        assignments: Schedule assignments (list of dicts or objects)

    Returns:
        Internal energy value (higher = worse schedule)
    """
    if not assignments:
        return 0.0

    energy = 0.0

    # Extract person IDs and rotation types for analysis
    person_counts: Counter = Counter()
    rotation_counts: Counter = Counter()

    for assignment in assignments:
        # Handle both dict and object assignments
        if isinstance(assignment, dict):
            person_id = assignment.get("person_id", assignment.get("resident_id"))
            rotation = assignment.get("rotation_type", assignment.get("rotation"))
        else:
            person_id = getattr(
                assignment, "person_id", getattr(assignment, "resident_id", None)
            )
            rotation = getattr(
                assignment, "rotation_type", getattr(assignment, "rotation", None)
            )

        if person_id:
            person_counts[person_id] += 1
        if rotation:
            rotation_counts[rotation] += 1

    # Workload imbalance energy (variance in assignments per person)
    if person_counts:
        counts = list(person_counts.values())
        mean_count = sum(counts) / len(counts)
        variance = sum((c - mean_count) ** 2 for c in counts) / len(counts)
        # Normalize variance contribution
        energy += math.sqrt(variance) * 0.5

    # Rotation diversity penalty (too many same-type assignments = higher energy)
    if rotation_counts:
        total = sum(rotation_counts.values())
        # Calculate Gini coefficient for rotation distribution
        sorted_counts = sorted(rotation_counts.values())
        n = len(sorted_counts)
        if n > 1 and total > 0:
            gini = sum((2 * i - n - 1) * c for i, c in enumerate(sorted_counts, 1))
            gini = gini / (n * total)
            # Lower Gini = more equal distribution = lower energy
            energy += max(0, gini) * 2.0

    return energy


def _calculate_entropy(assignments: list[Any]) -> float:
    """
    Calculate configuration entropy of the schedule.

    Entropy measures schedule flexibility and diversity:
    - Higher entropy = more diverse assignments
    - Lower entropy = more concentrated/rigid assignments

    Uses Shannon entropy: S = -sum(p_i * log(p_i))

    Args:
        assignments: Schedule assignments

    Returns:
        Entropy value (higher = more flexible/diverse)
    """
    if not assignments:
        return 0.0

    # Count unique configurations
    config_counts: Counter = Counter()

    for assignment in assignments:
        # Create configuration key
        if isinstance(assignment, dict):
            rotation = assignment.get("rotation_type", assignment.get("rotation", "?"))
        else:
            rotation = getattr(
                assignment, "rotation_type", getattr(assignment, "rotation", "?")
            )

        config_key = f"{rotation}"
        config_counts[config_key] += 1

    # Calculate Shannon entropy
    total = sum(config_counts.values())
    if total == 0:
        return 0.0

    entropy = 0.0
    for count in config_counts.values():
        p = count / total
        if p > 0:
            entropy -= p * math.log(p)

    return entropy


def calculate_free_energy(
    assignments: list[Any], temperature: float = 1.0
) -> FreeEnergyMetrics:
    """
    Calculate Helmholtz free energy of a schedule.

    Free energy F = U - TS where:
    - U = internal energy (constraint violations, imbalances)
    - T = temperature (exploration parameter)
    - S = entropy (schedule flexibility)

    Lower free energy indicates a more stable, optimal schedule.

    Args:
        assignments: Schedule assignments (list of dicts or Assignment objects)
        temperature: System temperature (default 1.0)
            - High temperature: entropy dominates (explore diverse solutions)
            - Low temperature: energy dominates (exploit best solutions)

    Returns:
        FreeEnergyMetrics with calculated values

    Example:
        assignments = get_schedule_assignments()
        metrics = calculate_free_energy(assignments, temperature=2.0)

        if metrics.free_energy < previous_metrics.free_energy:
            print("Schedule improved!")
    """
    if temperature <= 0:
        temperature = 0.001  # Avoid division by zero

    # Calculate components
    internal_energy = _calculate_internal_energy(assignments)
    entropy = _calculate_entropy(assignments)

    # Helmholtz free energy: F = U - TS
    entropy_term = temperature * entropy
    free_energy = internal_energy - entropy_term

    # Calculate partition function (sum over Boltzmann weights)
    # For single state, Z = exp(-F/T)
    if abs(free_energy) < 700:
        partition_function = math.exp(-free_energy / temperature)
    else:
        partition_function = 1.0

    logger.debug(
        f"Free energy calculation: U={internal_energy:.4f}, "
        f"S={entropy:.4f}, T={temperature:.2f}, F={free_energy:.4f}"
    )

    return FreeEnergyMetrics(
        free_energy=free_energy,
        internal_energy=internal_energy,
        entropy_term=entropy_term,
        temperature=temperature,
        partition_function=partition_function,
        probability_distribution={},
    )


@dataclass
class LandscapePoint:
    """A point in the energy landscape."""

    energy: float
    position: tuple[float, ...]
    gradient: tuple[float, ...] = field(default_factory=tuple)
    is_minimum: bool = False
    basin_id: int | None = None


@dataclass
class LandscapeAnalysis:
    """Results of energy landscape analysis."""

    local_minima: list[LandscapePoint]
    global_minimum: LandscapePoint | None
    num_basins: int
    roughness: float  # Measure of landscape ruggedness
    barrier_heights: list[float]  # Heights of barriers between minima
    funnel_score: float  # 0-1, higher = more funnel-like (easier optimization)


class EnergyLandscapeAnalyzer:
    """
    Analyze energy landscape of schedule space.

    Provides insights into optimization difficulty:
    - Local minima detection (potential traps)
    - Basin identification (regions of attraction)
    - Transition path analysis (escape routes)
    - Roughness metrics (optimization difficulty)

    Example:
        analyzer = EnergyLandscapeAnalyzer()
        result = analyzer.analyze_landscape(assignments)
        if result["funnel_score"] > 0.7:
            print("Landscape is well-funneled, optimization should be easy")
    """

    def __init__(self, num_samples: int = 100, perturbation_scale: float = 0.1):
        """
        Initialize analyzer.

        Args:
            num_samples: Number of random samples for landscape estimation
            perturbation_scale: Scale of random perturbations for sampling
        """
        self.num_samples = num_samples
        self.perturbation_scale = perturbation_scale
        self._energy_samples: list[float] = []

    def analyze_landscape(self, assignments: list[Any]) -> dict[str, Any]:
        """
        Analyze energy landscape around current schedule configuration.

        Samples the energy landscape by perturbing the current configuration
        and measuring resulting energy changes.

        Args:
            assignments: Current schedule assignments

        Returns:
            Dictionary containing:
            - global_minimum_energy: Lowest energy found
            - local_minima_count: Number of local minima detected
            - roughness: Landscape ruggedness (0-1, higher = rougher)
            - funnel_score: How funnel-like (0-1, higher = easier to optimize)
            - basin_sizes: Sizes of attraction basins
            - barrier_estimate: Estimated barrier heights
        """
        if not assignments:
            return {
                "global_minimum_energy": 0.0,
                "local_minima_count": 0,
                "roughness": 0.0,
                "funnel_score": 1.0,
                "basin_sizes": [],
                "barrier_estimate": 0.0,
            }

        # Calculate base energy
        base_metrics = calculate_free_energy(assignments)
        base_energy = base_metrics.internal_energy

        # Sample landscape by virtual perturbations
        self._energy_samples = [base_energy]
        energy_gradients: list[float] = []

        for _ in range(self.num_samples):
            # Estimate perturbed energy (without actually modifying assignments)
            perturbation = self._random_perturbation()
            perturbed_energy = base_energy + perturbation
            self._energy_samples.append(perturbed_energy)
            energy_gradients.append(perturbed_energy - base_energy)

        # Analyze collected samples
        min_energy = min(self._energy_samples)
        max_energy = max(self._energy_samples)
        mean_energy = sum(self._energy_samples) / len(self._energy_samples)
        energy_range = max_energy - min_energy if max_energy > min_energy else 1.0

        # Count local minima (approximation based on gradient changes)
        local_minima_count = self._estimate_local_minima(energy_gradients)

        # Calculate roughness (normalized variance of gradients)
        if energy_gradients:
            mean_gradient = sum(energy_gradients) / len(energy_gradients)
            gradient_variance = sum(
                (g - mean_gradient) ** 2 for g in energy_gradients
            ) / len(energy_gradients)
            roughness = min(
                1.0, math.sqrt(gradient_variance) / max(energy_range, 0.001)
            )
        else:
            roughness = 0.0

        # Funnel score: inverse of roughness, adjusted for energy concentration
        energy_below_mean = sum(1 for e in self._energy_samples if e < mean_energy)
        concentration = energy_below_mean / len(self._energy_samples)
        funnel_score = (1.0 - roughness) * concentration

        # Estimate barrier heights
        barrier_estimate = self._estimate_barriers()

        logger.info(
            f"Landscape analysis: minima={local_minima_count}, "
            f"roughness={roughness:.3f}, funnel_score={funnel_score:.3f}"
        )

        return {
            "global_minimum_energy": min_energy,
            "local_minima_count": local_minima_count,
            "roughness": roughness,
            "funnel_score": funnel_score,
            "basin_sizes": self._estimate_basin_sizes(),
            "barrier_estimate": barrier_estimate,
            "energy_range": energy_range,
            "mean_energy": mean_energy,
        }

    def _random_perturbation(self) -> float:
        """Generate random energy perturbation for landscape sampling."""
        import random

        # Use normal distribution centered at 0
        return random.gauss(0, self.perturbation_scale)

    def _estimate_local_minima(self, gradients: list[float]) -> int:
        """Estimate number of local minima from gradient sign changes."""
        if len(gradients) < 3:
            return 1

        sign_changes = 0
        for i in range(1, len(gradients)):
            if gradients[i - 1] < 0 < gradients[i]:
                sign_changes += 1

        # Approximate local minima count
        return max(1, sign_changes)

    def _estimate_barriers(self) -> float:
        """Estimate barrier heights between minima."""
        if len(self._energy_samples) < 2:
            return 0.0

        sorted_energies = sorted(self._energy_samples)
        # Barrier estimate: difference between highest and median
        median_idx = len(sorted_energies) // 2
        return sorted_energies[-1] - sorted_energies[median_idx]

    def _estimate_basin_sizes(self) -> list[float]:
        """Estimate relative sizes of attraction basins."""
        if len(self._energy_samples) < 2:
            return [1.0]

        # Simple binning approach
        min_e = min(self._energy_samples)
        max_e = max(self._energy_samples)
        range_e = max_e - min_e

        if range_e < 0.001:
            return [1.0]

        # Divide into 5 bins
        num_bins = 5
        bin_counts = [0] * num_bins

        for e in self._energy_samples:
            bin_idx = min(num_bins - 1, int((e - min_e) / range_e * num_bins))
            bin_counts[bin_idx] += 1

        total = sum(bin_counts)
        return [c / total for c in bin_counts if c > 0]


class AdaptiveTemperatureScheduler:
    """
    Sophisticated adaptive temperature scheduler for simulated annealing.

    Implements multiple cooling schedules:
    - Exponential: T(t) = T0 * alpha^t
    - Logarithmic: T(t) = T0 / (1 + log(1 + t))
    - Linear: T(t) = T0 * (1 - t/t_max)
    - Adaptive: Adjusts based on acceptance rate
    - Reheat: Periodic reheating to escape local minima

    Example:
        scheduler = AdaptiveTemperatureScheduler(
            initial_temp=10.0,
            schedule_type="adaptive"
        )

        for iteration in range(1000):
            temp = scheduler.get_temperature(iteration)
            # Use temp for acceptance probability
            if accepted:
                scheduler.record_acceptance(True)
    """

    def __init__(
        self,
        initial_temp: float = 10.0,
        final_temp: float = 0.01,
        max_iterations: int = 1000,
        schedule_type: str = "exponential",
        cooling_rate: float = 0.95,
        target_acceptance_rate: float = 0.4,
        reheat_interval: int = 0,
        reheat_factor: float = 2.0,
    ):
        """
        Initialize temperature scheduler.

        Args:
            initial_temp: Starting temperature
            final_temp: Minimum temperature
            max_iterations: Expected number of iterations
            schedule_type: One of "exponential", "logarithmic", "linear", "adaptive"
            cooling_rate: Decay rate for exponential schedule
            target_acceptance_rate: Target for adaptive schedule
            reheat_interval: Iterations between reheats (0 = no reheat)
            reheat_factor: Multiply temperature by this on reheat
        """
        self.initial_temp = initial_temp
        self.final_temp = final_temp
        self.max_iterations = max_iterations
        self.schedule_type = schedule_type
        self.cooling_rate = cooling_rate
        self.target_acceptance_rate = target_acceptance_rate
        self.reheat_interval = reheat_interval
        self.reheat_factor = reheat_factor

        # For adaptive schedule
        self._acceptance_history: list[bool] = []
        self._current_temp = initial_temp
        self._last_reheat_iteration = 0

    def get_temperature(self, iteration: int) -> float:
        """
        Get temperature at given iteration.

        Args:
            iteration: Current iteration number

        Returns:
            Temperature value
        """
        # Check for reheat
        if self.reheat_interval > 0 and iteration > 0:
            if (iteration - self._last_reheat_iteration) >= self.reheat_interval:
                self._current_temp *= self.reheat_factor
                self._last_reheat_iteration = iteration
                logger.debug(
                    f"Reheat at iteration {iteration}: T={self._current_temp:.4f}"
                )

        if self.schedule_type == "exponential":
            temp = self.initial_temp * (self.cooling_rate**iteration)

        elif self.schedule_type == "logarithmic":
            temp = self.initial_temp / (1 + math.log(1 + iteration))

        elif self.schedule_type == "linear":
            progress = min(1.0, iteration / max(1, self.max_iterations))
            temp = self.initial_temp * (1 - progress) + self.final_temp * progress

        elif self.schedule_type == "adaptive":
            temp = self._adaptive_temperature()

        else:
            # Default to exponential
            temp = self.initial_temp * (self.cooling_rate**iteration)

        # Clamp to final temperature
        return max(self.final_temp, temp)

    def record_acceptance(self, accepted: bool) -> None:
        """
        Record whether a move was accepted (for adaptive schedule).

        Args:
            accepted: Whether the move was accepted
        """
        self._acceptance_history.append(accepted)

        # Keep only recent history
        if len(self._acceptance_history) > 100:
            self._acceptance_history = self._acceptance_history[-100:]

    def _adaptive_temperature(self) -> float:
        """Calculate adaptive temperature based on acceptance rate."""
        if len(self._acceptance_history) < 10:
            return self._current_temp

        # Calculate recent acceptance rate
        recent = self._acceptance_history[-50:]
        acceptance_rate = sum(recent) / len(recent)

        # Adjust temperature
        if acceptance_rate > self.target_acceptance_rate + 0.1:
            # Too many acceptances, cool down faster
            self._current_temp *= 0.95
        elif acceptance_rate < self.target_acceptance_rate - 0.1:
            # Too few acceptances, heat up
            self._current_temp *= 1.05

        return self._current_temp


def adaptive_temperature(
    iteration: int,
    initial_temp: float = 10.0,
    cooling_rate: float = 0.95,
    schedule: str = "exponential",
    final_temp: float = 0.01,
    max_iterations: int = 1000,
) -> float:
    """
    Calculate adaptive temperature for simulated annealing.

    Convenience function for simple temperature scheduling.

    Args:
        iteration: Current iteration number
        initial_temp: Initial temperature
        cooling_rate: Cooling rate (for exponential schedule)
        schedule: Schedule type ("exponential", "logarithmic", "linear")
        final_temp: Minimum temperature
        max_iterations: Total expected iterations (for linear schedule)

    Returns:
        Temperature at current iteration

    Example:
        for i in range(1000):
            temp = adaptive_temperature(i, initial_temp=10.0, schedule="logarithmic")
            accept_prob = math.exp(-delta_energy / temp)
    """
    if schedule == "exponential":
        temp = initial_temp * (cooling_rate**iteration)

    elif schedule == "logarithmic":
        temp = initial_temp / (1 + math.log(1 + iteration))

    elif schedule == "linear":
        progress = min(1.0, iteration / max(1, max_iterations))
        temp = initial_temp * (1 - progress) + final_temp * progress

    else:
        temp = initial_temp * (cooling_rate**iteration)

    return max(final_temp, temp)


def boltzmann_probability(energy_delta: float, temperature: float) -> float:
    """
    Calculate Boltzmann acceptance probability.

    P(accept) = exp(-ΔE / T) if ΔE > 0, else 1.0

    Args:
        energy_delta: Change in energy (new - old)
        temperature: Current temperature

    Returns:
        Acceptance probability (0.0 to 1.0)
    """
    if energy_delta <= 0:
        return 1.0  # Always accept improvements

    if temperature <= 0:
        return 0.0  # Never accept worse at T=0

    exponent = -energy_delta / temperature
    if exponent < -700:  # Prevent underflow
        return 0.0

    return math.exp(exponent)
