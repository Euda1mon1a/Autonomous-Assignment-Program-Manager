"""
Export Module for Bio-Inspired Optimization Results.

This module provides JSON export functionality for sharing optimization
results with visualization tools, dashboards, and downstream analysis.

Export Types
------------

**ParetoExporter**
    Export Pareto front solutions with objective values, statistics,
    and hypervolume calculations.

**EvolutionExporter**
    Export evolution history with fitness trajectories, diversity
    metrics, and convergence analysis.

**HolographicExporter**
    Export complete optimization results in holographic hub format
    for 3D visualization with animation support.

Usage Examples
--------------

Export Pareto front to JSON file:

.. code-block:: python

    from app.scheduling.bio_inspired.export import ParetoExporter

    exporter = ParetoExporter(algorithm_name="nsga2")

    # Export to dictionary
    data = exporter.export(
        pareto_front,
        objectives=["coverage", "fairness", "acgme_compliance"],
        include_chromosomes=False,  # Omit large chromosome data
    )

    # Export to file
    exporter.export_to_file(
        pareto_front,
        output_path="results/pareto_front.json",
    )

Export evolution history:

.. code-block:: python

    from app.scheduling.bio_inspired.export import EvolutionExporter

    exporter = EvolutionExporter(algorithm_name="genetic_algorithm")

    data = exporter.export(
        evolution_history,
        pareto_history=pareto_fronts_per_generation,
        best_individual=best_solution,
        include_full_pareto=True,  # Include detailed Pareto data
    )

    exporter.export_to_file(evolution_history, "results/evolution.json")

Export for holographic hub:

.. code-block:: python

    from app.scheduling.bio_inspired.export import HolographicExporter

    exporter = HolographicExporter(algorithm_name="hybrid_ga_qubo")

    data = exporter.export_complete(
        evolution_history=history,
        pareto_front=pareto,
        population_snapshots=snapshots,  # For animation
        best_individual=best,
    )

    exporter.export_to_file("results/holographic_export.json", **data)

Export Data Formats
-------------------

**Pareto Front Export**:

.. code-block:: json

    {
        "type": "pareto_front",
        "metadata": {
            "algorithm": "nsga2",
            "timestamp": "2024-01-15T10:30:00",
            "version": "1.0"
        },
        "objectives": ["coverage", "fairness", "acgme_compliance"],
        "size": 45,
        "solutions": [
            {
                "id": 123,
                "rank": 0,
                "crowding_distance": 1.234,
                "objectives": {
                    "coverage": 0.92,
                    "fairness": 0.85,
                    "acgme_compliance": 0.98
                },
                "weighted_sum": 0.91
            }
        ],
        "statistics": {
            "objective_ranges": {...},
            "ideal_point": {...},
            "nadir_point": {...},
            "hypervolume_2d": 0.823
        }
    }

**Evolution History Export**:

.. code-block:: json

    {
        "type": "evolution_history",
        "total_generations": 200,
        "evolution": [
            {
                "generation": 0,
                "best_fitness": 0.45,
                "mean_fitness": 0.32,
                "diversity": 0.89
            }
        ],
        "summary": {
            "fitness": {
                "initial_best": 0.45,
                "final_best": 0.92,
                "improvement_rate": 1.04
            },
            "convergence": {
                "generation_90_percent": 85,
                "converged": true
            }
        }
    }

**Holographic Hub Export**:

.. code-block:: json

    {
        "type": "holographic_hub_export",
        "pareto_front": {...},
        "evolution": {...},
        "holographic": {
            "nodes": [
                {
                    "id": 123,
                    "position": {"x": 0.8, "y": 0.7, "z": 0.9},
                    "size": 8.5,
                    "color": "#2aff32"
                }
            ],
            "frames": [...],
            "surface": {
                "vertices": [...],
                "faces": [...]
            },
            "camera": {
                "initial_position": {"x": 1.5, "y": 1.5, "z": 1.5}
            },
            "axes": {
                "x": {"label": "Coverage", "range": [0, 1]}
            }
        }
    }

Numpy Handling
--------------

The NumpyEncoder class handles numpy types in JSON serialization:
- np.integer -> int
- np.floating -> float
- np.ndarray -> list
- np.bool_ -> bool
- Objects with to_dict() -> dict

Statistics Computed
-------------------

**Pareto Statistics**:
- Objective ranges (min, max, mean, std)
- Ideal point (best in each objective)
- Nadir point (worst in each objective)
- 2D hypervolume indicator

**Evolution Summary**:
- Initial and final best fitness
- Improvement rate
- Generation at 90% convergence
- Diversity trend (increasing/decreasing/stable)
- Evaluations to reach best
- Average improvement per generation
"""

import json
import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np

from app.scheduling.bio_inspired.base import (
    FitnessVector,
    Individual,
    PopulationStats,
)

logger = logging.getLogger(__name__)


class NumpyEncoder(json.JSONEncoder):
    """JSON encoder that handles numpy types."""

    def default(self, obj) -> Any:
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, (np.bool_, bool)):
            return bool(obj)
        elif hasattr(obj, "to_dict"):
            return obj.to_dict()
        return super().default(obj)


@dataclass
class ExportMetadata:
    """Metadata for exported data."""

    algorithm: str
    timestamp: str
    version: str = "1.0"
    problem_size: dict | None = None
    parameters: dict | None = None

    def to_dict(self) -> dict:
        return {
            "algorithm": self.algorithm,
            "timestamp": self.timestamp,
            "version": self.version,
            "problem_size": self.problem_size or {},
            "parameters": self.parameters or {},
        }


class ParetoExporter:
    """
    Exports Pareto front data for visualization and analysis.

    The Pareto front represents all non-dominated solutions where no
    solution is strictly better than another in all objectives.
    """

    def __init__(self, algorithm_name: str = "bio_inspired") -> None:
        """
        Initialize Pareto exporter.

        Args:
            algorithm_name: Name of the algorithm that generated the front
        """
        self.algorithm_name = algorithm_name

    def export(
        self,
        pareto_front: list[Individual],
        objectives: list[str] | None = None,
        include_chromosomes: bool = False,
    ) -> dict:
        """
        Export Pareto front to dictionary.

        Args:
            pareto_front: List of Pareto-optimal individuals
            objectives: Which objectives to include (default: all)
            include_chromosomes: Whether to include full chromosome data

        Returns:
            Dictionary ready for JSON serialization
        """
        if objectives is None:
            objectives = [
                "coverage",
                "fairness",
                "preferences",
                "learning_goals",
                "acgme_compliance",
                "continuity",
            ]

        metadata = ExportMetadata(
            algorithm=self.algorithm_name,
            timestamp=datetime.now().isoformat(),
        )

        solutions = []
        for ind in pareto_front:
            solution = {
                "id": ind.id,
                "rank": ind.rank,
                "crowding_distance": ind.crowding_distance,
                "generation": ind.generation,
            }

            # Add objectives
            if ind.fitness:
                solution["objectives"] = {
                    obj: getattr(ind.fitness, obj, 0) for obj in objectives
                }
                solution["weighted_sum"] = ind.fitness.weighted_sum()

                # Optionally include chromosome
            if include_chromosomes:
                solution["chromosome"] = {
                    "shape": list(ind.chromosome.genes.shape),
                    "n_assignments": ind.chromosome.count_assignments(),
                    "genes_hash": hash(ind.chromosome.genes.tobytes()),
                }

            solutions.append(solution)

            # Sort by first objective for easier visualization
        solutions.sort(key=lambda s: s.get("objectives", {}).get(objectives[0], 0))

        # Compute front statistics
        stats = self._compute_pareto_stats(pareto_front, objectives)

        return {
            "type": "pareto_front",
            "metadata": metadata.to_dict(),
            "objectives": objectives,
            "size": len(solutions),
            "solutions": solutions,
            "statistics": stats,
        }

    def _compute_pareto_stats(
        self,
        pareto_front: list[Individual],
        objectives: list[str],
    ) -> dict:
        """Compute statistics for the Pareto front."""
        if not pareto_front:
            return {}

        stats = {
            "objective_ranges": {},
            "ideal_point": {},
            "nadir_point": {},
        }

        for obj in objectives:
            values = [
                getattr(ind.fitness, obj, 0) for ind in pareto_front if ind.fitness
            ]
            if values:
                stats["objective_ranges"][obj] = {
                    "min": float(min(values)),
                    "max": float(max(values)),
                    "mean": float(np.mean(values)),
                    "std": float(np.std(values)),
                }
                stats["ideal_point"][obj] = float(max(values))
                stats["nadir_point"][obj] = float(min(values))

                # Hypervolume (2D approximation)
        if len(objectives) >= 2:
            obj1, obj2 = objectives[0], objectives[1]
            points = [
                (getattr(ind.fitness, obj1, 0), getattr(ind.fitness, obj2, 0))
                for ind in pareto_front
                if ind.fitness
            ]
            stats["hypervolume_2d"] = self._compute_hypervolume(points)

        return stats

    def _compute_hypervolume(
        self,
        points: list[tuple[float, float]],
        ref_point: tuple[float, float] = (0.0, 0.0),
    ) -> float:
        """Compute 2D hypervolume indicator."""
        if len(points) < 2:
            return 0.0

            # Sort by first objective (descending)
        sorted_points = sorted(points, key=lambda p: p[0], reverse=True)

        hypervolume = 0.0
        prev_y = ref_point[1]

        for x, y in sorted_points:
            if y > prev_y:
                hypervolume += (x - ref_point[0]) * (y - prev_y)
                prev_y = y

        return hypervolume

    def export_to_file(
        self,
        pareto_front: list[Individual],
        output_path: str | Path,
        **kwargs,
    ) -> None:
        """Export Pareto front to JSON file."""
        data = self.export(pareto_front, **kwargs)

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w") as f:
            json.dump(data, f, cls=NumpyEncoder, indent=2)

        logger.info(f"Pareto front exported to {output_path}")


class EvolutionExporter:
    """
    Exports evolution history and population dynamics.

    Tracks how the population evolves over generations for
    visualization and analysis.
    """

    def __init__(self, algorithm_name: str = "bio_inspired") -> None:
        """Initialize evolution exporter."""
        self.algorithm_name = algorithm_name

    def export(
        self,
        evolution_history: list[PopulationStats],
        pareto_history: list[list[Individual]] | None = None,
        best_individual: Individual | None = None,
        include_full_pareto: bool = False,
    ) -> dict:
        """
        Export evolution history to dictionary.

        Args:
            evolution_history: List of PopulationStats per generation
            pareto_history: Pareto front at each generation
            best_individual: Best individual found
            include_full_pareto: Include all Pareto fronts (can be large)

        Returns:
            Dictionary ready for JSON serialization
        """
        metadata = ExportMetadata(
            algorithm=self.algorithm_name,
            timestamp=datetime.now().isoformat(),
        )

        # Core evolution data
        evolution_data = [stats.to_dict() for stats in evolution_history]

        # Summary statistics
        summary = self._compute_summary(evolution_history)

        # Best individual
        best_data = None
        if best_individual:
            best_data = {
                "id": best_individual.id,
                "generation": best_individual.generation,
                "fitness": best_individual.fitness.to_dict()
                if best_individual.fitness
                else {},
                "n_assignments": best_individual.chromosome.count_assignments(),
            }

            # Pareto front evolution (summarized)
        pareto_data = None
        if pareto_history:
            pareto_data = [
                {
                    "generation": i,
                    "size": len(front),
                    "best_weighted_sum": max(
                        (ind.fitness.weighted_sum() for ind in front if ind.fitness),
                        default=0,
                    ),
                }
                for i, front in enumerate(pareto_history)
            ]

            if include_full_pareto and len(pareto_history) > 0:
                # Include final Pareto front details
                final_front = pareto_history[-1]
                pareto_data.append(
                    {
                        "generation": len(pareto_history) - 1,
                        "is_final": True,
                        "solutions": [
                            {
                                "id": ind.id,
                                "fitness": ind.fitness.to_dict() if ind.fitness else {},
                            }
                            for ind in final_front
                        ],
                    }
                )

        return {
            "type": "evolution_history",
            "metadata": metadata.to_dict(),
            "total_generations": len(evolution_history),
            "evolution": evolution_data,
            "summary": summary,
            "best_individual": best_data,
            "pareto_evolution": pareto_data,
        }

    def _compute_summary(
        self,
        evolution_history: list[PopulationStats],
    ) -> dict:
        """Compute summary statistics for evolution."""
        if not evolution_history:
            return {}

        best_fitness_series = [s.best_fitness for s in evolution_history]
        mean_fitness_series = [s.mean_fitness for s in evolution_history]
        diversity_series = [s.diversity for s in evolution_history]

        # Find convergence point (90% of final improvement)
        convergence_gen = self._find_convergence_generation(best_fitness_series)

        # Compute improvement rate
        if len(best_fitness_series) >= 2:
            early_avg = np.mean(best_fitness_series[: len(best_fitness_series) // 4])
            late_avg = np.mean(best_fitness_series[-len(best_fitness_series) // 4 :])
            improvement_rate = (late_avg - early_avg) / max(early_avg, 0.001)
        else:
            improvement_rate = 0.0

        return {
            "fitness": {
                "initial_best": float(best_fitness_series[0]),
                "final_best": float(best_fitness_series[-1]),
                "improvement": float(best_fitness_series[-1] - best_fitness_series[0]),
                "improvement_rate": float(improvement_rate),
            },
            "convergence": {
                "generation_90_percent": convergence_gen,
                "converged": convergence_gen < len(best_fitness_series) * 0.8,
            },
            "diversity": {
                "initial": float(diversity_series[0]) if diversity_series else 0,
                "final": float(diversity_series[-1]) if diversity_series else 0,
                "trend": "decreasing"
                if diversity_series and diversity_series[-1] < diversity_series[0]
                else "stable",
            },
            "efficiency": {
                "evaluations_to_best": self._find_first_best(best_fitness_series),
                "avg_improvement_per_generation": float(
                    (best_fitness_series[-1] - best_fitness_series[0])
                    / len(best_fitness_series)
                ),
            },
        }

    def _find_convergence_generation(
        self,
        fitness_series: list[float],
        threshold: float = 0.9,
    ) -> int:
        """Find generation where 90% of improvement is achieved."""
        if len(fitness_series) < 2:
            return 0

        initial = fitness_series[0]
        final = fitness_series[-1]
        target = initial + threshold * (final - initial)

        for i, f in enumerate(fitness_series):
            if f >= target:
                return i

        return len(fitness_series) - 1

    def _find_first_best(self, fitness_series: list[float]) -> int:
        """Find generation where best fitness was first achieved."""
        if not fitness_series:
            return 0

        best = max(fitness_series)
        for i, f in enumerate(fitness_series):
            if f >= best * 0.999:  # Within 0.1% of best
                return i

        return len(fitness_series) - 1

    def export_to_file(
        self,
        evolution_history: list[PopulationStats],
        output_path: str | Path,
        **kwargs,
    ) -> None:
        """Export evolution history to JSON file."""
        data = self.export(evolution_history, **kwargs)

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w") as f:
            json.dump(data, f, cls=NumpyEncoder, indent=2)

        logger.info(f"Evolution history exported to {output_path}")


class HolographicExporter:
    """
    Exports data in holographic hub format for 3D visualization.

    The holographic hub uses a specialized format with:
    - Node data (individuals as 3D points)
    - Edge data (parent-child relationships)
    - Animation frames (evolution over time)
    - Surface data (fitness landscape)
    """

    def __init__(self, algorithm_name: str = "bio_inspired") -> None:
        """Initialize holographic exporter."""
        self.algorithm_name = algorithm_name
        self.pareto_exporter = ParetoExporter(algorithm_name)
        self.evolution_exporter = EvolutionExporter(algorithm_name)

    def export_complete(
        self,
        evolution_history: list[PopulationStats],
        pareto_front: list[Individual],
        population_snapshots: list[list[Individual]] | None = None,
        best_individual: Individual | None = None,
    ) -> dict:
        """
        Export complete optimization results for holographic hub.

        Args:
            evolution_history: Evolution statistics
            pareto_front: Final Pareto front
            population_snapshots: Population at selected generations
            best_individual: Best individual found

        Returns:
            Complete export dictionary
        """
        metadata = ExportMetadata(
            algorithm=self.algorithm_name,
            timestamp=datetime.now().isoformat(),
            version="1.0-holographic",
        )

        # Core components
        pareto_data = self.pareto_exporter.export(pareto_front)
        evolution_data = self.evolution_exporter.export(
            evolution_history,
            best_individual=best_individual,
        )

        # Build holographic-specific data
        holographic = self._build_holographic_data(
            evolution_history,
            pareto_front,
            population_snapshots or [],
        )

        return {
            "type": "holographic_hub_export",
            "metadata": metadata.to_dict(),
            "pareto_front": pareto_data,
            "evolution": evolution_data,
            "holographic": holographic,
        }

    def _build_holographic_data(
        self,
        evolution_history: list[PopulationStats],
        pareto_front: list[Individual],
        population_snapshots: list[list[Individual]],
    ) -> dict:
        """Build holographic-specific visualization data."""
        # 3D node positions (coverage, fairness, ACGME as axes)
        nodes = []
        for ind in pareto_front:
            if ind.fitness:
                nodes.append(
                    {
                        "id": ind.id,
                        "position": {
                            "x": ind.fitness.coverage,
                            "y": ind.fitness.fairness,
                            "z": ind.fitness.acgme_compliance,
                        },
                        "size": ind.fitness.weighted_sum() * 10,  # Scale for visibility
                        "color": self._fitness_to_color(ind.fitness.weighted_sum()),
                        "label": f"Solution {ind.id}",
                    }
                )

                # Animation frames from population snapshots
        frames = []
        for gen, pop in enumerate(population_snapshots[:50]):  # Limit frames
            frame_nodes = []
            for ind in pop[:50]:  # Limit nodes per frame
                if ind.fitness:
                    frame_nodes.append(
                        {
                            "id": ind.id,
                            "position": {
                                "x": ind.fitness.coverage,
                                "y": ind.fitness.fairness,
                                "z": ind.fitness.acgme_compliance,
                            },
                            "fitness": ind.fitness.weighted_sum(),
                        }
                    )

            frames.append(
                {
                    "generation": gen,
                    "nodes": frame_nodes,
                    "stats": evolution_history[gen].to_dict()
                    if gen < len(evolution_history)
                    else {},
                }
            )

            # Pareto surface (3D mesh)
        surface = self._build_pareto_surface(pareto_front)

        return {
            "nodes": nodes,
            "edges": [],  # Could add parent-child relationships
            "frames": frames,
            "surface": surface,
            "camera": {
                "initial_position": {"x": 1.5, "y": 1.5, "z": 1.5},
                "target": {"x": 0.5, "y": 0.5, "z": 0.5},
            },
            "axes": {
                "x": {"label": "Coverage", "range": [0, 1]},
                "y": {"label": "Fairness", "range": [0, 1]},
                "z": {"label": "ACGME Compliance", "range": [0, 1]},
            },
        }

    def _fitness_to_color(self, fitness: float) -> str:
        """Convert fitness value to color (green = good, red = poor)."""
        # Normalize fitness to 0-1 range
        normalized = min(1.0, max(0.0, fitness))

        # Green to red gradient
        r = int(255 * (1 - normalized))
        g = int(255 * normalized)
        b = 50

        return f"#{r:02x}{g:02x}{b:02x}"

    def _build_pareto_surface(
        self,
        pareto_front: list[Individual],
    ) -> dict:
        """Build 3D surface for Pareto front visualization."""
        if len(pareto_front) < 3:
            return {"vertices": [], "faces": []}

            # Extract 3D coordinates
        vertices = []
        for ind in pareto_front:
            if ind.fitness:
                vertices.append(
                    [
                        ind.fitness.coverage,
                        ind.fitness.fairness,
                        ind.fitness.acgme_compliance,
                    ]
                )

                # Simple triangulation (would use scipy.spatial.Delaunay for real impl)
        faces = []
        for i in range(len(vertices) - 2):
            faces.append([i, i + 1, i + 2])

        return {
            "vertices": vertices,
            "faces": faces,
            "wireframe": True,
            "opacity": 0.6,
        }

    def export_to_file(
        self,
        output_path: str | Path,
        **kwargs,
    ) -> None:
        """Export to JSON file."""
        data = self.export_complete(**kwargs)

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w") as f:
            json.dump(data, f, cls=NumpyEncoder, indent=2)

        logger.info(f"Holographic export saved to {output_path}")
