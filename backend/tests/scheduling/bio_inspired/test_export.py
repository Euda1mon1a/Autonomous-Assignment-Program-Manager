"""Tests for export functionality."""
import json
import tempfile
from pathlib import Path

import numpy as np
import pytest

from app.scheduling.bio_inspired.base import (
    Chromosome,
    FitnessVector,
    Individual,
    PopulationStats,
)
from app.scheduling.bio_inspired.export import (
    EvolutionExporter,
    HolographicExporter,
    NumpyEncoder,
    ParetoExporter,
)


class TestNumpyEncoder:
    """Tests for numpy JSON encoder."""

    def test_encode_numpy_int(self):
        """Test encoding numpy integers."""
        data = {"value": np.int64(42)}
        result = json.dumps(data, cls=NumpyEncoder)
        assert '"value": 42' in result

    def test_encode_numpy_float(self):
        """Test encoding numpy floats."""
        data = {"value": np.float64(3.14)}
        result = json.dumps(data, cls=NumpyEncoder)
        parsed = json.loads(result)
        assert parsed["value"] == pytest.approx(3.14)

    def test_encode_numpy_array(self):
        """Test encoding numpy arrays."""
        data = {"arr": np.array([1, 2, 3])}
        result = json.dumps(data, cls=NumpyEncoder)
        parsed = json.loads(result)
        assert parsed["arr"] == [1, 2, 3]

    def test_encode_numpy_bool(self):
        """Test encoding numpy booleans."""
        data = {"flag": np.bool_(True)}
        result = json.dumps(data, cls=NumpyEncoder)
        parsed = json.loads(result)
        assert parsed["flag"] is True


class TestParetoExporter:
    """Tests for Pareto front exporter."""

    def _create_pareto_front(self) -> list[Individual]:
        """Create test Pareto front."""
        return [
            Individual(
                chromosome=Chromosome.create_empty(3, 5),
                fitness=FitnessVector(coverage=0.9, fairness=0.3),
                id=1,
                rank=0,
                crowding_distance=1.5,
            ),
            Individual(
                chromosome=Chromosome.create_empty(3, 5),
                fitness=FitnessVector(coverage=0.6, fairness=0.7),
                id=2,
                rank=0,
                crowding_distance=2.0,
            ),
            Individual(
                chromosome=Chromosome.create_empty(3, 5),
                fitness=FitnessVector(coverage=0.3, fairness=0.9),
                id=3,
                rank=0,
                crowding_distance=1.5,
            ),
        ]

    def test_export_pareto_front(self):
        """Test basic Pareto front export."""
        exporter = ParetoExporter(algorithm_name="test_ga")
        pareto_front = self._create_pareto_front()

        result = exporter.export(pareto_front)

        assert result["type"] == "pareto_front"
        assert result["size"] == 3
        assert len(result["solutions"]) == 3
        assert result["metadata"]["algorithm"] == "test_ga"

    def test_export_with_objectives(self):
        """Test export with specific objectives."""
        exporter = ParetoExporter()
        pareto_front = self._create_pareto_front()

        result = exporter.export(
            pareto_front,
            objectives=["coverage", "fairness"],
        )

        assert "coverage" in result["solutions"][0]["objectives"]
        assert "fairness" in result["solutions"][0]["objectives"]
        # Other objectives should not be present
        assert "preferences" not in result["solutions"][0]["objectives"]

    def test_export_statistics(self):
        """Test statistics computation in export."""
        exporter = ParetoExporter()
        pareto_front = self._create_pareto_front()

        result = exporter.export(pareto_front)

        assert "statistics" in result
        assert "objective_ranges" in result["statistics"]
        assert "coverage" in result["statistics"]["objective_ranges"]
        assert "hypervolume_2d" in result["statistics"]

    def test_export_to_file(self):
        """Test exporting to file."""
        exporter = ParetoExporter()
        pareto_front = self._create_pareto_front()

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "pareto.json"
            exporter.export_to_file(pareto_front, output_path)

            assert output_path.exists()

            with open(output_path) as f:
                data = json.load(f)

            assert data["type"] == "pareto_front"
            assert data["size"] == 3


class TestEvolutionExporter:
    """Tests for evolution history exporter."""

    def _create_evolution_history(self, n_generations: int = 10) -> list[PopulationStats]:
        """Create test evolution history."""
        return [
            PopulationStats(
                generation=i,
                population_size=100,
                best_fitness=0.5 + 0.05 * i,
                worst_fitness=0.2 + 0.02 * i,
                mean_fitness=0.35 + 0.03 * i,
                std_fitness=0.1,
                diversity=0.5 - 0.02 * i,
                pareto_front_size=10 + i,
                hypervolume=0.4 + 0.04 * i,
                convergence=0.3 + 0.05 * i,
            )
            for i in range(n_generations)
        ]

    def test_export_evolution_history(self):
        """Test basic evolution history export."""
        exporter = EvolutionExporter(algorithm_name="test_nsga2")
        history = self._create_evolution_history()

        result = exporter.export(history)

        assert result["type"] == "evolution_history"
        assert result["total_generations"] == 10
        assert len(result["evolution"]) == 10
        assert result["metadata"]["algorithm"] == "test_nsga2"

    def test_export_summary_statistics(self):
        """Test summary statistics in export."""
        exporter = EvolutionExporter()
        history = self._create_evolution_history()

        result = exporter.export(history)

        assert "summary" in result
        assert "fitness" in result["summary"]
        assert "convergence" in result["summary"]
        assert "diversity" in result["summary"]

    def test_export_with_best_individual(self):
        """Test export with best individual."""
        exporter = EvolutionExporter()
        history = self._create_evolution_history(5)
        best = Individual(
            chromosome=Chromosome.create_random(3, 5, 2),
            fitness=FitnessVector(coverage=0.95, fairness=0.90),
            generation=4,
            id=99,
        )

        result = exporter.export(history, best_individual=best)

        assert result["best_individual"] is not None
        assert result["best_individual"]["id"] == 99
        assert result["best_individual"]["generation"] == 4

    def test_export_to_file(self):
        """Test exporting to file."""
        exporter = EvolutionExporter()
        history = self._create_evolution_history(5)

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "evolution.json"
            exporter.export_to_file(history, output_path)

            assert output_path.exists()

            with open(output_path) as f:
                data = json.load(f)

            assert data["type"] == "evolution_history"
            assert data["total_generations"] == 5


class TestHolographicExporter:
    """Tests for holographic hub exporter."""

    def _create_test_data(self):
        """Create test data for holographic export."""
        history = [
            PopulationStats(
                generation=i,
                population_size=50,
                best_fitness=0.5 + 0.05 * i,
                worst_fitness=0.2,
                mean_fitness=0.35,
                std_fitness=0.1,
                diversity=0.4,
                pareto_front_size=5,
                hypervolume=0.5,
                convergence=0.6,
            )
            for i in range(5)
        ]

        pareto = [
            Individual(
                chromosome=Chromosome.create_empty(3, 5),
                fitness=FitnessVector(
                    coverage=0.8,
                    fairness=0.6,
                    acgme_compliance=0.9,
                ),
                id=i,
            )
            for i in range(3)
        ]

        return history, pareto

    def test_holographic_export_complete(self):
        """Test complete holographic export."""
        exporter = HolographicExporter(algorithm_name="test_bio")
        history, pareto = self._create_test_data()

        result = exporter.export_complete(
            evolution_history=history,
            pareto_front=pareto,
        )

        assert result["type"] == "holographic_hub_export"
        assert "pareto_front" in result
        assert "evolution" in result
        assert "holographic" in result

    def test_holographic_nodes(self):
        """Test holographic nodes data."""
        exporter = HolographicExporter()
        history, pareto = self._create_test_data()

        result = exporter.export_complete(
            evolution_history=history,
            pareto_front=pareto,
        )

        nodes = result["holographic"]["nodes"]
        assert len(nodes) == 3  # 3 Pareto solutions

        for node in nodes:
            assert "position" in node
            assert "x" in node["position"]
            assert "y" in node["position"]
            assert "z" in node["position"]
            assert "color" in node

    def test_holographic_axes_config(self):
        """Test holographic axes configuration."""
        exporter = HolographicExporter()
        history, pareto = self._create_test_data()

        result = exporter.export_complete(
            evolution_history=history,
            pareto_front=pareto,
        )

        axes = result["holographic"]["axes"]
        assert "x" in axes
        assert "y" in axes
        assert "z" in axes
        assert axes["x"]["label"] == "Coverage"
        assert axes["y"]["label"] == "Fairness"

    def test_fitness_to_color(self):
        """Test fitness to color conversion."""
        exporter = HolographicExporter()

        # High fitness = green
        color_good = exporter._fitness_to_color(1.0)
        assert color_good.startswith("#")
        assert color_good[3:5] == "ff"  # Green channel high

        # Low fitness = red
        color_bad = exporter._fitness_to_color(0.0)
        assert color_bad[1:3] == "ff"  # Red channel high
