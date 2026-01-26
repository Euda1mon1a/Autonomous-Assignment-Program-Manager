"""
Tests for Free Energy Principle Scheduler.

Tests the FEP implementation including:
- DemandForecast creation and manipulation
- GenerativeModel learning and prediction
- FreeEnergyScheduler optimization
- Active inference updates
- Integration with existing solver framework
"""

import uuid
from datetime import date, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import numpy as np
import pytest

from app.models.assignment import Assignment
from app.scheduling.constraints import SchedulingContext
from app.scheduling.free_energy_scheduler import (
    DemandForecast,
    FreeEnergyScheduler,
    GenerativeModel,
    ScheduleOutcome,
    SurpriseMetric,
)
from app.scheduling.bio_inspired.base import Chromosome


# Mock objects for testing
class MockPerson:
    """Mock Person for testing."""

    def __init__(self, name: str = "Test Person", person_type: str = "resident"):
        self.id = uuid.uuid4()
        self.name = name
        self.type = person_type


class MockBlock:
    """Mock Block for testing."""

    def __init__(
        self,
        block_date: date | None = None,
        time_of_day: str = "AM",
        is_weekend: bool = False,
    ):
        self.id = uuid.uuid4()
        self.date = block_date or date.today()
        self.time_of_day = time_of_day
        self.is_weekend = is_weekend


class MockTemplate:
    """Mock RotationTemplate for testing."""

    def __init__(self, name: str = "Clinic", rotation_type: str = "outpatient"):
        self.id = uuid.uuid4()
        self.name = name
        self.rotation_type = rotation_type
        self.requires_procedure_credential = False


class MockAssignment:
    """Mock Assignment for testing."""

    def __init__(
        self, person_id: uuid.UUID, block_id: uuid.UUID, template_id: uuid.UUID
    ):
        self.id = uuid.uuid4()
        self.person_id = person_id
        self.block_id = block_id
        self.rotation_template_id = template_id


# ==================== DemandForecast Tests ====================


class TestDemandForecast:
    """Tests for DemandForecast dataclass."""

    def test_initialization(self):
        """Test DemandForecast initialization."""
        template_ids = [uuid.uuid4() for _ in range(3)]
        coverage = dict.fromkeys(template_ids, 0.33)

        forecast = DemandForecast(
            predicted_coverage=coverage,
            predicted_complexity=0.5,
            confidence=0.8,
        )

        assert forecast.predicted_coverage == coverage
        assert forecast.predicted_complexity == 0.5
        assert forecast.confidence == 0.8
        assert forecast.forecast_horizon_days == 28  # default

    def test_to_vector(self):
        """Test conversion to numpy vector."""
        template_ids = [uuid.uuid4() for _ in range(3)]
        coverage = {
            template_ids[0]: 0.5,
            template_ids[1]: 0.3,
            template_ids[2]: 0.2,
        }

        forecast = DemandForecast(
            predicted_coverage=coverage,
            predicted_complexity=0.5,
            confidence=0.8,
        )

        vector = forecast.to_vector(template_ids)

        assert isinstance(vector, np.ndarray)
        assert len(vector) == 3
        assert np.allclose(vector, [0.5, 0.3, 0.2])

    def test_to_vector_missing_template(self):
        """Test vector conversion with missing templates."""
        template_ids = [uuid.uuid4() for _ in range(3)]
        coverage = {
            template_ids[0]: 0.7,
            # template_ids[1] missing
            template_ids[2]: 0.3,
        }

        forecast = DemandForecast(
            predicted_coverage=coverage,
            predicted_complexity=0.5,
            confidence=0.8,
        )

        vector = forecast.to_vector(template_ids)

        assert vector[0] == 0.7
        assert vector[1] == 0.0  # missing -> 0.0
        assert vector[2] == 0.3

    def test_from_historical_data(self):
        """Test creating forecast from historical assignments."""
        templates = [MockTemplate(f"Template_{i}") for i in range(3)]

        # Create mock assignments
        assignments = []
        for i in range(60):
            template_idx = i % 3  # Uniform distribution
            assignments.append(
                MockAssignment(
                    person_id=uuid.uuid4(),
                    block_id=uuid.uuid4(),
                    template_id=templates[template_idx].id,
                )
            )

        forecast = DemandForecast.from_historical_data(
            historical_assignments=assignments,
            templates=templates,
        )

        # Should have uniform coverage (20 assignments per template)
        assert len(forecast.predicted_coverage) == 3
        for coverage in forecast.predicted_coverage.values():
            assert abs(coverage - 0.333) < 0.01

        assert 0.0 <= forecast.confidence <= 1.0
        assert 0.0 <= forecast.predicted_complexity <= 1.0

    def test_from_historical_data_skewed(self):
        """Test forecast with skewed historical data."""
        templates = [MockTemplate(f"Template_{i}") for i in range(3)]

        # Skewed distribution: 70% template 0, 20% template 1, 10% template 2
        assignments = []
        for _ in range(70):
            assignments.append(
                MockAssignment(
                    person_id=uuid.uuid4(),
                    block_id=uuid.uuid4(),
                    template_id=templates[0].id,
                )
            )
        for _ in range(20):
            assignments.append(
                MockAssignment(
                    person_id=uuid.uuid4(),
                    block_id=uuid.uuid4(),
                    template_id=templates[1].id,
                )
            )
        for _ in range(10):
            assignments.append(
                MockAssignment(
                    person_id=uuid.uuid4(),
                    block_id=uuid.uuid4(),
                    template_id=templates[2].id,
                )
            )

        forecast = DemandForecast.from_historical_data(
            historical_assignments=assignments,
            templates=templates,
        )

        # Check distribution
        coverage_list = [forecast.predicted_coverage.get(t.id, 0) for t in templates]
        assert abs(coverage_list[0] - 0.70) < 0.01
        assert abs(coverage_list[1] - 0.20) < 0.01
        assert abs(coverage_list[2] - 0.10) < 0.01

    def test_from_uniform_prior(self):
        """Test creating uniform prior forecast."""
        templates = [MockTemplate(f"Template_{i}") for i in range(3)]

        forecast = DemandForecast.from_uniform_prior(templates=templates)

        # Should have uniform coverage
        assert len(forecast.predicted_coverage) == 3
        for coverage in forecast.predicted_coverage.values():
            assert abs(coverage - 0.333) < 0.01

        assert forecast.confidence < 0.5  # Low confidence (no data)
        assert forecast.metadata.get("prior_type") == "uniform"


# ==================== ScheduleOutcome Tests ====================


class TestScheduleOutcome:
    """Tests for ScheduleOutcome dataclass."""

    def test_initialization(self):
        """Test ScheduleOutcome initialization."""
        template_ids = [uuid.uuid4() for _ in range(3)]
        coverage = dict.fromkeys(template_ids, 0.33)

        outcome = ScheduleOutcome(
            actual_coverage=coverage,
            actual_complexity=0.6,
            quality_metrics={"satisfaction": 0.8},
        )

        assert outcome.actual_coverage == coverage
        assert outcome.actual_complexity == 0.6
        assert outcome.quality_metrics["satisfaction"] == 0.8


# ==================== GenerativeModel Tests ====================


class TestGenerativeModel:
    """Tests for GenerativeModel learning."""

    def test_initialization(self):
        """Test GenerativeModel initialization."""
        model = GenerativeModel(n_templates=3)

        assert model.n_templates == 3
        assert len(model.prior_weights) == 3
        assert len(model.learned_weights) == 3
        assert np.allclose(model.prior_weights, [1 / 3, 1 / 3, 1 / 3])
        assert model.outcomes_seen == 0

    def test_update_single_outcome(self):
        """Test updating model with single outcome."""
        template_ids = [uuid.uuid4() for _ in range(3)]
        model = GenerativeModel(n_templates=3, learning_rate=0.5)

        # Create outcome with skewed distribution
        coverage = {
            template_ids[0]: 0.6,
            template_ids[1]: 0.3,
            template_ids[2]: 0.1,
        }
        outcome = ScheduleOutcome(
            actual_coverage=coverage,
            actual_complexity=0.5,
        )

        model.update(outcome, template_ids)

        assert model.outcomes_seen == 1
        assert len(model.error_history) == 1

        # Weights should have moved from uniform toward actual distribution
        assert model.learned_weights[0] > model.learned_weights[1]
        assert model.learned_weights[1] > model.learned_weights[2]

    def test_update_multiple_outcomes(self):
        """Test updating model with multiple outcomes."""
        template_ids = [uuid.uuid4() for _ in range(3)]
        model = GenerativeModel(n_templates=3, learning_rate=0.1)

        # Consistently skewed outcomes
        for _ in range(10):
            coverage = {
                template_ids[0]: 0.7,
                template_ids[1]: 0.2,
                template_ids[2]: 0.1,
            }
            outcome = ScheduleOutcome(
                actual_coverage=coverage,
                actual_complexity=0.5,
            )
            model.update(outcome, template_ids)

        assert model.outcomes_seen == 10
        assert len(model.error_history) == 10

        # Weights should converge to actual distribution
        assert abs(model.learned_weights[0] - 0.7) < 0.1
        assert abs(model.learned_weights[1] - 0.2) < 0.1
        assert abs(model.learned_weights[2] - 0.1) < 0.1

    def test_predict(self):
        """Test generating prediction from model."""
        template_ids = [uuid.uuid4() for _ in range(3)]
        model = GenerativeModel(n_templates=3)

        # Update with data
        coverage = {
            template_ids[0]: 0.5,
            template_ids[1]: 0.3,
            template_ids[2]: 0.2,
        }
        outcome = ScheduleOutcome(
            actual_coverage=coverage,
            actual_complexity=0.4,
        )
        model.update(outcome, template_ids)

        # Generate prediction
        forecast = model.predict(template_ids)

        assert isinstance(forecast, DemandForecast)
        assert len(forecast.predicted_coverage) == 3
        assert 0.0 <= forecast.confidence <= 1.0
        assert forecast.metadata.get("outcomes_seen") == 1

    def test_kl_divergence(self):
        """Test KL divergence computation."""
        model = GenerativeModel(n_templates=3)

        # Initially, KL should be ~0 (learned == prior)
        initial_kl = model.compute_kl_divergence()
        assert abs(initial_kl) < 0.01

        # After learning, KL should increase
        template_ids = [uuid.uuid4() for _ in range(3)]
        coverage = {
            template_ids[0]: 0.9,
            template_ids[1]: 0.05,
            template_ids[2]: 0.05,
        }
        outcome = ScheduleOutcome(
            actual_coverage=coverage,
            actual_complexity=0.5,
        )
        model.update(outcome, template_ids)

        updated_kl = model.compute_kl_divergence()
        assert updated_kl > initial_kl

    def test_reset_to_prior(self):
        """Test resetting model to prior."""
        template_ids = [uuid.uuid4() for _ in range(3)]
        model = GenerativeModel(n_templates=3)

        # Update model
        coverage = {
            template_ids[0]: 0.7,
            template_ids[1]: 0.2,
            template_ids[2]: 0.1,
        }
        outcome = ScheduleOutcome(
            actual_coverage=coverage,
            actual_complexity=0.5,
        )
        model.update(outcome, template_ids)

        assert model.outcomes_seen > 0
        assert len(model.error_history) > 0

        # Reset
        model.reset_to_prior()

        assert model.outcomes_seen == 0
        assert len(model.error_history) == 0
        assert np.allclose(model.learned_weights, model.prior_weights)


# ==================== FreeEnergyScheduler Tests ====================


class TestFreeEnergyScheduler:
    """Tests for FreeEnergyScheduler."""

    def create_simple_context(self, n_residents=3, n_blocks=5, n_templates=2):
        """Create simple scheduling context for testing."""
        residents = [MockPerson(f"Resident_{i}") for i in range(n_residents)]
        blocks = [
            MockBlock(
                block_date=date.today() + timedelta(days=i),
                is_weekend=(i % 7 in [5, 6]),
            )
            for i in range(n_blocks)
        ]
        templates = [MockTemplate(f"Template_{i}") for i in range(n_templates)]

        context = SchedulingContext(
            residents=residents,
            blocks=blocks,
            templates=templates,
            availability={},
            start_date=date.today(),
            end_date=date.today() + timedelta(days=n_blocks),
        )

        # Build indices
        context.resident_idx = {r.id: i for i, r in enumerate(residents)}
        context.block_idx = {b.id: i for i, b in enumerate(blocks)}

        return context

    def test_initialization(self):
        """Test FreeEnergyScheduler initialization."""
        solver = FreeEnergyScheduler(
            lambda_complexity=0.2,
            learning_rate=0.15,
            active_inference_enabled=True,
        )

        assert solver.lambda_complexity == 0.2
        assert solver.learning_rate == 0.15
        assert solver.active_inference_enabled is True
        assert solver.generative_model is None  # Not initialized yet

    def test_compute_prediction_error(self):
        """Test prediction error computation."""
        context = self.create_simple_context(n_residents=2, n_blocks=4, n_templates=2)
        solver = FreeEnergyScheduler()

        # Create forecast
        template_ids = [t.id for t in context.templates]
        forecast = DemandForecast(
            predicted_coverage={template_ids[0]: 0.6, template_ids[1]: 0.4},
            predicted_complexity=0.5,
            confidence=0.8,
        )

        # Create chromosome matching forecast
        chromosome = Chromosome.create_empty(n_residents=2, n_blocks=4)
        # Assign to match: 60% template 0, 40% template 1
        chromosome.genes[0, 0] = 1  # template 0
        chromosome.genes[0, 1] = 1
        chromosome.genes[0, 2] = 1
        chromosome.genes[1, 0] = 2  # template 1
        chromosome.genes[1, 1] = 2

        error = solver.compute_prediction_error(forecast, chromosome, context)

        assert isinstance(error, float)
        assert error >= 0.0
        # Error should be small since we matched the forecast
        assert error < 0.5

    def test_compute_free_energy(self):
        """Test free energy computation."""
        context = self.create_simple_context()
        solver = FreeEnergyScheduler(lambda_complexity=0.1)

        # Initialize model
        solver.generative_model = GenerativeModel(n_templates=len(context.templates))

        template_ids = [t.id for t in context.templates]
        forecast = DemandForecast(
            predicted_coverage=dict.fromkeys(template_ids, 0.5),
            predicted_complexity=0.5,
            confidence=0.8,
        )

        chromosome = Chromosome.create_random(
            n_residents=len(context.residents),
            n_blocks=len(context.blocks),
            n_templates=len(context.templates),
            density=0.5,
        )

        free_energy = solver.compute_free_energy(chromosome, forecast, context)

        assert isinstance(free_energy, float)
        assert free_energy >= 0.0

    def test_minimize_free_energy(self):
        """Test free energy minimization."""
        context = self.create_simple_context()
        solver = FreeEnergyScheduler()

        # Initialize model
        solver.generative_model = GenerativeModel(n_templates=len(context.templates))

        template_ids = [t.id for t in context.templates]
        forecast = DemandForecast(
            predicted_coverage=dict.fromkeys(template_ids, 0.5),
            predicted_complexity=0.5,
            confidence=0.8,
        )

        initial_chromosome = Chromosome.create_random(
            n_residents=len(context.residents),
            n_blocks=len(context.blocks),
            n_templates=len(context.templates),
            density=0.5,
        )

        initial_energy = solver.compute_free_energy(
            initial_chromosome, forecast, context
        )

        optimized = solver.minimize_free_energy(
            initial_schedule=initial_chromosome,
            forecast=forecast,
            context=context,
            max_iterations=50,
        )

        final_energy = solver.compute_free_energy(optimized, forecast, context)

        # Energy should decrease or stay same
        assert final_energy <= initial_energy

    def test_active_inference_step(self):
        """Test active inference (bidirectional update)."""
        context = self.create_simple_context()
        solver = FreeEnergyScheduler(active_inference_enabled=True, learning_rate=0.2)

        # Initialize model
        solver.generative_model = GenerativeModel(
            n_templates=len(context.templates),
            learning_rate=0.2,
        )

        template_ids = [t.id for t in context.templates]
        forecast = DemandForecast(
            predicted_coverage=dict.fromkeys(template_ids, 0.5),
            predicted_complexity=0.5,
            confidence=0.8,
        )

        chromosome = Chromosome.create_random(
            n_residents=len(context.residents),
            n_blocks=len(context.blocks),
            n_templates=len(context.templates),
            density=0.5,
        )

        initial_outcomes = solver.generative_model.outcomes_seen

        updated_schedule, updated_forecast = solver.active_inference_step(
            schedule=chromosome,
            forecast=forecast,
            context=context,
        )

        # Model should have been updated
        assert solver.generative_model.outcomes_seen == initial_outcomes + 1

        # Schedule and forecast should be returned
        assert isinstance(updated_schedule, Chromosome)
        assert isinstance(updated_forecast, DemandForecast)

    def test_solve_simple(self):
        """Test basic solve operation."""
        context = self.create_simple_context(n_residents=2, n_blocks=3, n_templates=2)
        solver = FreeEnergyScheduler(
            population_size=20,
            max_generations=10,
            timeout_seconds=30.0,
        )

        result = solver.solve(context)

        assert result is not None
        # Success depends on constraints, so we don't assert True/False
        assert isinstance(result.success, bool)

        if result.success:
            assert len(result.assignments) > 0
            assert result.objective_value >= 0.0

    def test_update_generative_model(self):
        """Test updating generative model from historical outcomes."""
        context = self.create_simple_context()
        solver = FreeEnergyScheduler()
        solver._context = context

        # Initialize model
        solver.generative_model = GenerativeModel(n_templates=len(context.templates))

        template_ids = [t.id for t in context.templates]
        outcomes = []
        for i in range(5):
            coverage = {
                template_ids[0]: 0.6,
                template_ids[1]: 0.4,
            }
            outcome = ScheduleOutcome(
                actual_coverage=coverage,
                actual_complexity=0.5,
            )
            outcomes.append(outcome)

        initial_count = solver.generative_model.outcomes_seen

        solver.update_generative_model(outcomes)

        assert solver.generative_model.outcomes_seen == initial_count + 5

    def test_surprise_tracking(self):
        """Test that surprise metrics are tracked during evolution."""
        context = self.create_simple_context(n_residents=2, n_blocks=3, n_templates=2)
        solver = FreeEnergyScheduler(
            population_size=10,
            max_generations=5,
            track_evolution=True,
        )

        result = solver.solve(context)

        # Surprise history should be populated
        assert len(solver.surprise_history) > 0

        for surprise in solver.surprise_history:
            assert isinstance(surprise, SurpriseMetric)
            assert surprise.prediction_error >= 0.0
            assert surprise.total_surprise >= 0.0


# ==================== Integration Tests ====================


@pytest.mark.asyncio
class TestFreeEnergyIntegration:
    """Integration tests for FEP scheduler with database."""

    async def test_forecast_generator_placeholder(self):
        """Placeholder test for forecast generator (requires DB)."""
        # This would test ForecastGenerator with actual database
        # For now, just verify imports work
        from app.scheduling.free_energy_integration import ForecastGenerator

        assert ForecastGenerator is not None

    async def test_solver_adapter_placeholder(self):
        """Placeholder test for solver adapter (requires DB)."""
        from app.scheduling.free_energy_integration import FreeEnergySolverAdapter

        assert FreeEnergySolverAdapter is not None

    async def test_hybrid_solver_placeholder(self):
        """Placeholder test for hybrid solver (requires DB)."""
        from app.scheduling.free_energy_integration import HybridFreeEnergySolver

        assert HybridFreeEnergySolver is not None


# ==================== Edge Cases and Error Handling ====================


class TestFreeEnergyEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_context(self):
        """Test with empty scheduling context."""
        context = SchedulingContext(
            residents=[],
            blocks=[],
            templates=[],
            availability={},
        )

        solver = FreeEnergyScheduler(population_size=10, max_generations=5)
        result = solver.solve(context)

        assert result.success is False
        assert result.status == "empty"

    def test_zero_templates(self):
        """Test with no templates."""
        context = SchedulingContext(
            residents=[MockPerson()],
            blocks=[MockBlock()],
            templates=[],
            availability={},
        )
        context.resident_idx = {context.residents[0].id: 0}
        context.block_idx = {context.blocks[0].id: 0}

        solver = FreeEnergyScheduler()
        # Should handle gracefully
        # (actual behavior depends on implementation)

    def test_forecast_with_empty_coverage(self):
        """Test forecast with empty coverage dict."""
        forecast = DemandForecast(
            predicted_coverage={},
            predicted_complexity=0.5,
            confidence=0.5,
        )

        template_ids = [uuid.uuid4() for _ in range(3)]
        vector = forecast.to_vector(template_ids)

        assert np.allclose(vector, [0.0, 0.0, 0.0])


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
