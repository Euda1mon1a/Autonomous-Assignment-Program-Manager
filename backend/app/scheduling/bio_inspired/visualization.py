"""
Fitness Landscape Visualization for Bio-Inspired Optimization.

This module provides visualization tools for understanding how evolutionary
algorithms search the solution space. All outputs are JSON, designed for
rendering by the holographic hub 3D visualization system.

Visualization Types
-------------------

**Fitness Landscape**
    A 3D surface showing how fitness varies across the solution space.
    Uses PCA to project high-dimensional chromosomes to 2D coordinates,
    then interpolates fitness values to create a continuous surface.

    Reveals:
    - Local optima (peaks)
    - Global optima (highest peak)
    - Basins of attraction
    - Landscape ruggedness (difficulty)

**Evolution Trajectory**
    Animated path showing how populations move through the landscape
    over generations. Each frame captures:
    - Individual positions (2D projected)
    - Best fitness
    - Population diversity
    - Pareto front (if multi-objective)

**Pareto Front Visualization**
    2D/3D scatter plot of Pareto-optimal solutions showing trade-offs
    between objectives. Includes:
    - Objective values for each solution
    - Hypervolume indicator
    - Extreme solutions

**Convergence Analysis**
    Time-series plots showing:
    - Best fitness over generations
    - Mean fitness over generations
    - Population diversity decay
    - Pareto front size evolution

Usage Examples
--------------

Track evolution during optimization:

.. code-block:: python

    from app.scheduling.bio_inspired.visualization import EvolutionTracker

    # Create tracker (sample every 5 generations)
    tracker = EvolutionTracker(sample_rate=5)

    # During evolution loop
    for gen in range(max_generations):
        # ... evolution code ...
        tracker.record_generation(gen, population, pareto_front)

    # Get animation data for holographic hub
    animation_data = tracker.get_animation_data()

    # Get fitness trajectory
    trajectory = tracker.get_fitness_trajectory()

Generate fitness landscape after optimization:

.. code-block:: python

    from app.scheduling.bio_inspired.visualization import FitnessLandscapeVisualizer

    visualizer = FitnessLandscapeVisualizer(
        resolution=50,      # Grid resolution
        n_samples=500,      # Population samples to include
    )

    # Generate from population history
    landscape = visualizer.generate_landscape(
        population_history,
        n_residents=20,
        n_blocks=200,
    )

    # Landscape includes:
    # - surface: x, y, z grid data
    # - points: individual locations with fitness
    # - peaks: local maxima
    # - statistics: ruggedness, modality

Visualize Pareto front:

.. code-block:: python

    pareto_viz = visualizer.generate_pareto_visualization(
        pareto_front,
        objectives=["coverage", "fairness", "acgme_compliance"],
    )

    # Includes hypervolume and extreme solutions

Generate convergence plot:

.. code-block:: python

    convergence = visualizer.generate_convergence_plot(evolution_history)

    # Returns series for:
    # - best_fitness
    # - mean_fitness
    # - diversity
    # - pareto_size

Data Formats
------------

All visualizations output JSON-serializable dictionaries:

**Fitness Landscape**:

.. code-block:: json

    {
        "type": "fitness_landscape",
        "surface": {
            "x": [0.0, 0.1, ...],
            "y": [0.0, 0.1, ...],
            "z": [[0.5, 0.6, ...], ...]
        },
        "points": [
            {"x": 0.2, "y": 0.3, "fitness": 0.85, "generation": 50}
        ],
        "peaks": [
            {"x": 0.5, "y": 0.5, "fitness": 0.95}
        ],
        "statistics": {
            "ruggedness": 0.15,
            "modality": 3
        }
    }

**Animation Frame**:

.. code-block:: json

    {
        "generation": 50,
        "points": [
            {"x": 0.2, "y": 0.3, "fitness": 0.85, "id": 42}
        ],
        "best_fitness": 0.92,
        "mean_fitness": 0.75,
        "diversity": 0.35,
        "pareto_front": [...]
    }

PCA Projection
--------------

High-dimensional chromosomes are projected to 2D using PCA:

1. Flatten each chromosome to a 1D vector
2. Collect samples from the population
3. Compute principal components via SVD
4. Project to first 2 components

This preserves as much variance as possible in 2D, making similar
chromosomes appear near each other.

The PCA basis is updated periodically as new samples are collected,
adapting to the regions the algorithm explores.

Performance Notes
-----------------

- PCA update: O(n_samples * n_features) - runs occasionally
- Landscape interpolation: O(resolution^2 * n_points) - can be slow
- Animation export: O(n_generations * population_size)

For large populations or many generations, consider:
- Increasing sample_rate (sample fewer generations)
- Reducing resolution (coarser landscape grid)
- Limiting n_samples (fewer points in landscape)
"""

import logging
import math
from dataclasses import dataclass, field
from typing import Callable

import numpy as np

from app.scheduling.bio_inspired.base import (
    Chromosome,
    FitnessVector,
    Individual,
    PopulationStats,
)

logger = logging.getLogger(__name__)


@dataclass
class FitnessLandscapePoint:
    """A point in the fitness landscape."""

    x: float  # First principal component
    y: float  # Second principal component
    fitness: float
    individual_id: int
    generation: int
    is_best: bool = False
    is_pareto: bool = False

    def to_dict(self) -> dict:
        return {
            "x": self.x,
            "y": self.y,
            "fitness": self.fitness,
            "id": self.individual_id,
            "generation": self.generation,
            "is_best": self.is_best,
            "is_pareto": self.is_pareto,
        }


@dataclass
class EvolutionFrame:
    """A frame in the evolution animation."""

    generation: int
    points: list[FitnessLandscapePoint]
    best_fitness: float
    mean_fitness: float
    diversity: float
    pareto_front: list[dict]

    def to_dict(self) -> dict:
        return {
            "generation": self.generation,
            "points": [p.to_dict() for p in self.points],
            "best_fitness": self.best_fitness,
            "mean_fitness": self.mean_fitness,
            "diversity": self.diversity,
            "pareto_front": self.pareto_front,
        }


class EvolutionTracker:
    """
    Tracks evolution progress for visualization.

    Records:
    - Population snapshots at each generation
    - Fitness trajectory
    - Diversity metrics
    - Pareto front evolution
    """

    def __init__(self, sample_rate: int = 5) -> None:
        """
        Initialize evolution tracker.

        Args:
            sample_rate: Record every Nth generation
        """
        self.sample_rate = sample_rate
        self.frames: list[EvolutionFrame] = []
        self.fitness_history: list[float] = []
        self.diversity_history: list[float] = []
        self.pareto_history: list[list[dict]] = []

        # For PCA projection
        self._chromosome_samples: list[np.ndarray] = []
        self._pca_basis: np.ndarray | None = None

    def record_generation(
        self,
        generation: int,
        population: list[Individual],
        pareto_front: list[Individual] | None = None,
    ) -> None:
        """
        Record a generation snapshot.

        Args:
            generation: Current generation number
            population: Population at this generation
            pareto_front: Current Pareto front (if multi-objective)
        """
        if generation % self.sample_rate != 0:
            # Just record fitness
            best = max(
                (ind.fitness.weighted_sum() for ind in population if ind.fitness),
                default=0,
            )
            self.fitness_history.append(best)
            return

        # Full snapshot
        best_ind = max(
            population, key=lambda ind: ind.fitness.weighted_sum() if ind.fitness else 0
        )
        best_fitness = best_ind.fitness.weighted_sum() if best_ind.fitness else 0
        self.fitness_history.append(best_fitness)

        # Compute diversity
        diversity = self._compute_diversity(population)
        self.diversity_history.append(diversity)

        # Collect chromosome samples for PCA
        for ind in population[:20]:  # Sample
            flat = ind.chromosome.genes.flatten().astype(np.float64)
            self._chromosome_samples.append(flat)

        # Update PCA basis periodically
        if len(self._chromosome_samples) >= 50:
            self._update_pca_basis()

        # Create landscape points
        points = []
        pareto_ids = set()
        if pareto_front:
            pareto_ids = {ind.id for ind in pareto_front}

        for ind in population:
            x, y = self._project_to_2d(ind.chromosome)
            point = FitnessLandscapePoint(
                x=x,
                y=y,
                fitness=ind.fitness.weighted_sum() if ind.fitness else 0,
                individual_id=ind.id,
                generation=generation,
                is_best=(ind.id == best_ind.id),
                is_pareto=(ind.id in pareto_ids),
            )
            points.append(point)

        # Pareto front for this generation
        pareto_dicts = []
        if pareto_front:
            for ind in pareto_front:
                if ind.fitness:
                    pareto_dicts.append(
                        {
                            "id": ind.id,
                            "fitness": ind.fitness.to_dict(),
                            "coverage": ind.fitness.coverage,
                            "fairness": ind.fitness.fairness,
                        }
                    )

        self.pareto_history.append(pareto_dicts)

        # Create frame
        mean_fitness = np.mean(
            [ind.fitness.weighted_sum() for ind in population if ind.fitness]
        )

        frame = EvolutionFrame(
            generation=generation,
            points=points,
            best_fitness=best_fitness,
            mean_fitness=mean_fitness,
            diversity=diversity,
            pareto_front=pareto_dicts,
        )
        self.frames.append(frame)

    def _compute_diversity(self, population: list[Individual]) -> float:
        """Compute population diversity using pairwise similarity."""
        if len(population) < 2:
            return 0.0

        # Sample for efficiency
        sample = population[: min(20, len(population))]

        similarities = []
        for i, ind1 in enumerate(sample):
            for ind2 in sample[i + 1 :]:
                sim = ind1.chromosome.similarity(ind2.chromosome)
                similarities.append(sim)

        return 1.0 - np.mean(similarities) if similarities else 0.0

    def _update_pca_basis(self) -> None:
        """Update PCA basis from collected chromosome samples."""
        if len(self._chromosome_samples) < 10:
            return

        # Stack samples
        X = np.array(self._chromosome_samples[-100:])  # Use last 100

        # Center
        mean = np.mean(X, axis=0)
        X_centered = X - mean

        # SVD for PCA
        try:
            U, S, Vt = np.linalg.svd(X_centered, full_matrices=False)
            # Take first 2 components
            self._pca_basis = Vt[:2].T  # Shape: (n_features, 2)
            self._pca_mean = mean
        except Exception:
            self._pca_basis = None

    def _project_to_2d(self, chromosome: Chromosome) -> tuple[float, float]:
        """Project chromosome to 2D for visualization."""
        flat = chromosome.genes.flatten().astype(np.float64)

        if self._pca_basis is not None and len(flat) == len(self._pca_mean):
            centered = flat - self._pca_mean
            projected = centered @ self._pca_basis
            return float(projected[0]), float(projected[1])
        else:
            # Fallback: use first two summary statistics
            return float(np.mean(flat)), float(np.std(flat))

    def get_fitness_trajectory(self) -> list[dict]:
        """Get fitness trajectory over generations."""
        return [
            {"generation": i, "fitness": f} for i, f in enumerate(self.fitness_history)
        ]

    def get_diversity_trajectory(self) -> list[dict]:
        """Get diversity trajectory over generations."""
        return [
            {"generation": i * self.sample_rate, "diversity": d}
            for i, d in enumerate(self.diversity_history)
        ]

    def get_animation_data(self) -> dict:
        """Get data for animated visualization."""
        return {
            "frames": [f.to_dict() for f in self.frames],
            "total_generations": len(self.fitness_history),
            "fitness_trajectory": self.get_fitness_trajectory(),
            "diversity_trajectory": self.get_diversity_trajectory(),
        }


class FitnessLandscapeVisualizer:
    """
    Generates fitness landscape visualizations.

    The fitness landscape shows how fitness varies across the solution space,
    revealing:
    - Local optima (peaks)
    - Global optima (highest peak)
    - Basins of attraction
    - Ruggedness (how variable the landscape is)
    """

    def __init__(
        self,
        resolution: int = 50,
        n_samples: int = 500,
    ) -> None:
        """
        Initialize visualizer.

        Args:
            resolution: Grid resolution for landscape
            n_samples: Number of random samples for exploration
        """
        self.resolution = resolution
        self.n_samples = n_samples

    def generate_landscape(
        self,
        population_history: list[list[Individual]],
        n_residents: int,
        n_blocks: int,
    ) -> dict:
        """
        Generate fitness landscape visualization data.

        Args:
            population_history: Population at each generation
            n_residents: Number of residents
            n_blocks: Number of blocks

        Returns:
            Dictionary with landscape data for visualization
        """
        # Collect all individuals
        all_individuals = []
        for gen, pop in enumerate(population_history):
            for ind in pop:
                all_individuals.append((gen, ind))

        if not all_individuals:
            return {"error": "No population data"}

        # Extract chromosomes and fitness
        chromosomes = []
        fitness_values = []

        for gen, ind in all_individuals:
            flat = ind.chromosome.genes.flatten()
            chromosomes.append(flat)
            fitness_values.append(ind.fitness.weighted_sum() if ind.fitness else 0)

        # Compute 2D projection using PCA
        X = np.array(chromosomes, dtype=np.float64)
        x_2d, y_2d = self._compute_2d_projection(X)

        # Create grid for surface
        x_min, x_max = np.min(x_2d), np.max(x_2d)
        y_min, y_max = np.min(y_2d), np.max(y_2d)

        x_grid = np.linspace(x_min, x_max, self.resolution)
        y_grid = np.linspace(y_min, y_max, self.resolution)

        # Interpolate fitness on grid (using RBF-like smoothing)
        z_grid = self._interpolate_landscape(
            x_2d, y_2d, np.array(fitness_values), x_grid, y_grid
        )

        # Find peaks (local optima)
        peaks = self._find_peaks(x_grid, y_grid, z_grid)

        # Compute landscape statistics
        ruggedness = self._compute_ruggedness(z_grid)
        modality = len(peaks)

        return {
            "type": "fitness_landscape",
            "surface": {
                "x": x_grid.tolist(),
                "y": y_grid.tolist(),
                "z": z_grid.tolist(),
            },
            "points": [
                {
                    "x": float(x_2d[i]),
                    "y": float(y_2d[i]),
                    "fitness": float(fitness_values[i]),
                    "generation": int(all_individuals[i][0]),
                }
                for i in range(min(len(all_individuals), 500))  # Limit points
            ],
            "peaks": peaks,
            "statistics": {
                "ruggedness": ruggedness,
                "modality": modality,
                "fitness_range": {
                    "min": float(np.min(fitness_values)),
                    "max": float(np.max(fitness_values)),
                    "mean": float(np.mean(fitness_values)),
                },
            },
        }

    def _compute_2d_projection(
        self,
        X: np.ndarray,
    ) -> tuple[np.ndarray, np.ndarray]:
        """Compute 2D projection using PCA."""
        if len(X) < 2:
            return np.zeros(len(X)), np.zeros(len(X))

        # Center data
        mean = np.mean(X, axis=0)
        X_centered = X - mean

        # Compute SVD
        try:
            U, S, Vt = np.linalg.svd(X_centered, full_matrices=False)
            # Project onto first 2 components
            x_2d = X_centered @ Vt[0]
            y_2d = X_centered @ Vt[1]
        except Exception:
            # Fallback
            x_2d = np.mean(X, axis=1)
            y_2d = np.std(X, axis=1)

        return x_2d, y_2d

    def _interpolate_landscape(
        self,
        x: np.ndarray,
        y: np.ndarray,
        z: np.ndarray,
        x_grid: np.ndarray,
        y_grid: np.ndarray,
    ) -> list[list[float]]:
        """Interpolate fitness values onto a grid."""
        # Simple inverse distance weighting
        z_grid = np.zeros((len(y_grid), len(x_grid)))

        for i, yi in enumerate(y_grid):
            for j, xj in enumerate(x_grid):
                # Compute distances to all points
                distances = np.sqrt((x - xj) ** 2 + (y - yi) ** 2)
                distances = np.maximum(distances, 0.001)  # Avoid division by zero

                # Inverse distance weighting
                weights = 1.0 / (distances**2)
                z_grid[i, j] = np.sum(weights * z) / np.sum(weights)

        return z_grid.tolist()

    def _find_peaks(
        self,
        x_grid: np.ndarray,
        y_grid: np.ndarray,
        z_grid: list[list[float]],
    ) -> list[dict]:
        """Find local maxima in the landscape."""
        z = np.array(z_grid)
        peaks = []

        for i in range(1, len(y_grid) - 1):
            for j in range(1, len(x_grid) - 1):
                val = z[i, j]
                # Check if local maximum
                neighbors = [
                    z[i - 1, j],
                    z[i + 1, j],
                    z[i, j - 1],
                    z[i, j + 1],
                    z[i - 1, j - 1],
                    z[i - 1, j + 1],
                    z[i + 1, j - 1],
                    z[i + 1, j + 1],
                ]
                if val > max(neighbors):
                    peaks.append(
                        {
                            "x": float(x_grid[j]),
                            "y": float(y_grid[i]),
                            "fitness": float(val),
                        }
                    )

        # Sort by fitness and return top peaks
        peaks.sort(key=lambda p: p["fitness"], reverse=True)
        return peaks[:10]

    def _compute_ruggedness(self, z_grid: list[list[float]]) -> float:
        """
        Compute landscape ruggedness.

        Higher values indicate more variable, harder-to-search landscapes.
        """
        z = np.array(z_grid)
        if z.size < 4:
            return 0.0

        # Gradient-based ruggedness
        grad_x = np.diff(z, axis=1)
        grad_y = np.diff(z, axis=0)

        ruggedness = (np.std(grad_x) + np.std(grad_y)) / 2
        return float(ruggedness)

    def generate_pareto_visualization(
        self,
        pareto_front: list[Individual],
        objectives: list[str] | None = None,
    ) -> dict:
        """
        Generate Pareto front visualization data.

        Args:
            pareto_front: List of Pareto-optimal individuals
            objectives: Which objectives to visualize (default: coverage, fairness)

        Returns:
            Dictionary with Pareto visualization data
        """
        if objectives is None:
            objectives = ["coverage", "fairness"]

        points = []
        for ind in pareto_front:
            if ind.fitness:
                point = {"id": ind.id}
                for obj in objectives:
                    point[obj] = getattr(ind.fitness, obj, 0)
                point["weighted_sum"] = ind.fitness.weighted_sum()
                points.append(point)

        # Sort by first objective for line plot
        points.sort(key=lambda p: p[objectives[0]])

        # Compute Pareto front area/volume
        if len(objectives) == 2 and len(points) > 1:
            # 2D hypervolume
            area = self._compute_2d_hypervolume(points, objectives)
        else:
            area = 0.0

        return {
            "type": "pareto_front",
            "objectives": objectives,
            "points": points,
            "size": len(points),
            "hypervolume": area,
            "extremes": {
                obj: {
                    "max": max((p[obj] for p in points), default=0),
                    "min": min((p[obj] for p in points), default=0),
                }
                for obj in objectives
            },
        }

    def _compute_2d_hypervolume(
        self,
        points: list[dict],
        objectives: list[str],
    ) -> float:
        """Compute 2D hypervolume indicator."""
        if len(points) < 2:
            return 0.0

        obj1, obj2 = objectives[0], objectives[1]

        # Reference point: origin
        ref_x, ref_y = 0.0, 0.0

        # Sort by first objective (descending)
        sorted_points = sorted(points, key=lambda p: p[obj1], reverse=True)

        hypervolume = 0.0
        prev_y = ref_y

        for p in sorted_points:
            x, y = p[obj1], p[obj2]
            if y > prev_y:
                hypervolume += (x - ref_x) * (y - prev_y)
                prev_y = y

        return hypervolume

    def generate_convergence_plot(
        self,
        evolution_history: list[PopulationStats],
    ) -> dict:
        """
        Generate convergence plot data.

        Shows how fitness improves and diversity changes over generations.
        """
        if not evolution_history:
            return {"error": "No evolution history"}

        generations = [s.generation for s in evolution_history]
        best_fitness = [s.best_fitness for s in evolution_history]
        mean_fitness = [s.mean_fitness for s in evolution_history]
        diversity = [s.diversity for s in evolution_history]
        pareto_sizes = [s.pareto_front_size for s in evolution_history]

        return {
            "type": "convergence",
            "generations": generations,
            "series": {
                "best_fitness": best_fitness,
                "mean_fitness": mean_fitness,
                "diversity": diversity,
                "pareto_size": pareto_sizes,
            },
            "statistics": {
                "final_best": best_fitness[-1] if best_fitness else 0,
                "improvement": (
                    (best_fitness[-1] - best_fitness[0]) / best_fitness[0]
                    if best_fitness and best_fitness[0] > 0
                    else 0
                ),
                "generations_to_90_percent": self._find_convergence_point(
                    best_fitness, 0.9
                ),
            },
        }

    def _find_convergence_point(
        self,
        fitness_series: list[float],
        threshold: float,
    ) -> int:
        """Find generation where fitness reaches threshold of final value."""
        if not fitness_series:
            return 0

        final = fitness_series[-1]
        target = fitness_series[0] + threshold * (final - fitness_series[0])

        for i, f in enumerate(fitness_series):
            if f >= target:
                return i

        return len(fitness_series) - 1
