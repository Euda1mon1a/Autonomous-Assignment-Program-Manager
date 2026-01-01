"""
Spin Glass Model for Schedule Diversity.

From condensed matter physics: spin glass systems exhibit frustrated
interactions and multiple degenerate ground states.

Application to scheduling:
- Generate diverse schedule replicas (different but equally good)
- Explore frustrated constraint systems (conflicting preferences)
- Ensemble averaging for robustness

Key concept: Frustration - cannot simultaneously satisfy all pairwise constraints.

Based on:
- Edwards-Anderson spin glass model
- Replica symmetry breaking (Parisi solution)
- Simulated annealing on rugged energy landscapes
"""

import logging
from dataclasses import dataclass
from typing import Optional

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class SpinConfiguration:
    """Spin glass configuration (schedule variant)."""

    spins: np.ndarray  # Binary assignment vector (+1/-1 or 0/1)
    energy: float  # Schedule quality (lower = better)
    frustration: float  # Degree of constraint conflict (0-1)
    magnetization: float  # Overall bias (should be ~0 for balanced)
    overlap: float  # Overlap with reference configuration (0-1)


@dataclass
class ReplicaEnsemble:
    """Ensemble of spin glass replicas."""

    configurations: list[SpinConfiguration]
    mean_energy: float
    energy_std: float
    mean_overlap: float  # Average pairwise overlap
    diversity_score: float  # 1 - mean_overlap (higher = more diverse)


class SpinGlassModel:
    """
    Spin glass model for generating diverse schedule variants.

    Uses Ising model with random couplings to represent
    frustrated scheduling constraints.
    """

    def __init__(
        self,
        num_spins: int,
        temperature: float = 1.0,
        frustration_level: float = 0.3,
    ):
        """
        Initialize spin glass model.

        Args:
            num_spins: Number of binary variables (assignment slots)
            temperature: System temperature for sampling
            frustration_level: Degree of conflicting constraints (0-1)
        """
        logger.info(
            "Initializing spin glass model: num_spins=%d, temperature=%.2f, frustration=%.2f",
            num_spins,
            temperature,
            frustration_level,
        )
        self.num_spins = num_spins
        self.temperature = temperature
        self.frustration_level = frustration_level

        # Random coupling matrix (interaction strengths)
        self.couplings = self._generate_couplings()
        logger.debug("Generated %dx%d coupling matrix", num_spins, num_spins)

    def _generate_couplings(self) -> np.ndarray:
        """
        Generate random coupling matrix.

        Couplings J_{ij} represent constraint compatibility:
        - J_{ij} > 0: prefer same state (both assigned or both unassigned)
        - J_{ij} < 0: prefer opposite states (frustration)
        """
        J = np.random.randn(self.num_spins, self.num_spins)

        # Make symmetric
        J = (J + J.T) / 2

        # Zero diagonal (no self-interaction)
        np.fill_diagonal(J, 0)

        # Add frustration by randomly flipping signs
        frustration_mask = (
            np.random.rand(self.num_spins, self.num_spins) < self.frustration_level
        )
        J[frustration_mask] *= -1

        return J

    def calculate_energy(self, spins: np.ndarray) -> float:
        """
        Calculate Ising energy: E = -Σ_{ij} J_{ij} s_i s_j

        Args:
            spins: Binary spin configuration (+1/-1)

        Returns:
            Energy (lower = better)
        """
        # Convert to +1/-1 if binary 0/1
        if np.all((spins == 0) | (spins == 1)):
            spins = 2 * spins - 1

        energy = -0.5 * np.sum(self.couplings * np.outer(spins, spins))
        return float(energy)

    def calculate_frustration(self, spins: np.ndarray) -> float:
        """
        Calculate degree of frustration in configuration.

        Frustration = fraction of unsatisfied constraints

        Args:
            spins: Spin configuration

        Returns:
            Frustration ratio (0-1)
        """
        if np.all((spins == 0) | (spins == 1)):
            spins = 2 * spins - 1

        total_pairs = 0
        frustrated_pairs = 0

        for i in range(self.num_spins):
            for j in range(i + 1, self.num_spins):
                if self.couplings[i, j] != 0:
                    total_pairs += 1

                    # Check if constraint satisfied
                    # J > 0: want spins aligned
                    # J < 0: want spins anti-aligned
                    desired_product = np.sign(self.couplings[i, j])
                    actual_product = spins[i] * spins[j]

                    if desired_product * actual_product < 0:
                        frustrated_pairs += 1

        return frustrated_pairs / total_pairs if total_pairs > 0 else 0.0

    def generate_replica(
        self,
        num_iterations: int = 1000,
        initial_spins: np.ndarray | None = None,
    ) -> SpinConfiguration:
        """
        Generate single replica using simulated annealing.

        Args:
            num_iterations: Number of Monte Carlo steps
            initial_spins: Initial configuration (random if None)

        Returns:
            SpinConfiguration replica
        """
        # Initialize
        if initial_spins is None:
            spins = 2 * np.random.randint(0, 2, self.num_spins) - 1  # Random +1/-1
        else:
            spins = initial_spins.copy()

        current_energy = self.calculate_energy(spins)

        # Simulated annealing schedule
        for iteration in range(num_iterations):
            # Temperature annealing
            T = self.temperature * (1.0 - iteration / num_iterations)
            T = max(T, 0.01)  # Don't go to zero

            # Propose spin flip
            flip_idx = np.random.randint(self.num_spins)
            new_spins = spins.copy()
            new_spins[flip_idx] *= -1

            new_energy = self.calculate_energy(new_spins)
            delta_E = new_energy - current_energy

            # Metropolis acceptance
            if delta_E < 0 or np.random.rand() < np.exp(-delta_E / T):
                spins = new_spins
                current_energy = new_energy

        # Calculate final metrics
        frustration = self.calculate_frustration(spins)
        magnetization = float(np.mean(spins))

        return SpinConfiguration(
            spins=spins,
            energy=current_energy,
            frustration=frustration,
            magnetization=magnetization,
            overlap=0.0,  # Will be calculated later
        )

    def generate_replica_ensemble(
        self,
        num_replicas: int = 10,
        num_iterations: int = 1000,
    ) -> ReplicaEnsemble:
        """
        Generate ensemble of diverse schedule replicas.

        Args:
            num_replicas: Number of replicas to generate
            num_iterations: MC iterations per replica

        Returns:
            ReplicaEnsemble with diversity statistics
        """
        replicas = []

        for _ in range(num_replicas):
            replica = self.generate_replica(num_iterations=num_iterations)
            replicas.append(replica)

        # Calculate pairwise overlaps
        overlaps = []
        for i in range(len(replicas)):
            for j in range(i + 1, len(replicas)):
                overlap = self.calculate_overlap(replicas[i].spins, replicas[j].spins)
                overlaps.append(overlap)
                replicas[i].overlap = overlap  # Store last computed overlap

        mean_overlap = float(np.mean(overlaps)) if overlaps else 0.0
        diversity_score = 1.0 - mean_overlap

        energies = [r.energy for r in replicas]
        mean_energy = float(np.mean(energies))
        energy_std = float(np.std(energies))

        return ReplicaEnsemble(
            configurations=replicas,
            mean_energy=mean_energy,
            energy_std=energy_std,
            mean_overlap=mean_overlap,
            diversity_score=diversity_score,
        )

    def calculate_overlap(self, spins1: np.ndarray, spins2: np.ndarray) -> float:
        """
        Calculate overlap between two configurations.

        Overlap q = (1/N) Σ_i s1_i * s2_i

        q = 1: identical
        q = 0: random/orthogonal
        q = -1: opposite

        Args:
            spins1: First configuration
            spins2: Second configuration

        Returns:
            Overlap (-1 to 1)
        """
        # Ensure +1/-1 encoding
        if np.all((spins1 == 0) | (spins1 == 1)):
            spins1 = 2 * spins1 - 1
        if np.all((spins2 == 0) | (spins2 == 1)):
            spins2 = 2 * spins2 - 1

        overlap = float(np.mean(spins1 * spins2))
        return overlap

    def find_ground_state(
        self,
        num_attempts: int = 10,
        num_iterations: int = 5000,
    ) -> SpinConfiguration:
        """
        Find approximate ground state (lowest energy configuration).

        Args:
            num_attempts: Number of independent annealing runs
            num_iterations: MC iterations per run

        Returns:
            Best configuration found
        """
        best_config = None
        best_energy = float("inf")

        for _ in range(num_attempts):
            config = self.generate_replica(num_iterations=num_iterations)

            if config.energy < best_energy:
                best_energy = config.energy
                best_config = config

        return best_config

    def assess_landscape_ruggedness(
        self,
        num_samples: int = 100,
    ) -> dict:
        """
        Assess energy landscape ruggedness.

        Rugged landscape = many local minima (hard optimization problem)

        Args:
            num_samples: Number of random samples

        Returns:
            Dict with ruggedness metrics
        """
        energies = []

        for _ in range(num_samples):
            spins = 2 * np.random.randint(0, 2, self.num_spins) - 1
            energy = self.calculate_energy(spins)
            energies.append(energy)

        energies = np.array(energies)

        # Metrics
        energy_range = float(np.max(energies) - np.min(energies))
        energy_variance = float(np.var(energies))
        num_local_minima_estimate = int(np.sqrt(num_samples))  # Rough estimate

        # Ruggedness score: normalized variance
        ruggedness = min(
            1.0, energy_variance / (energy_range**2) if energy_range > 0 else 0.0
        )

        if ruggedness > 0.7:
            difficulty = "very_hard"
        elif ruggedness > 0.4:
            difficulty = "hard"
        elif ruggedness > 0.2:
            difficulty = "moderate"
        else:
            difficulty = "easy"

        return {
            "energy_range": energy_range,
            "energy_variance": energy_variance,
            "ruggedness_score": ruggedness,
            "difficulty": difficulty,
            "estimated_local_minima": num_local_minima_estimate,
            "mean_energy": float(np.mean(energies)),
            "std_energy": float(np.std(energies)),
        }
