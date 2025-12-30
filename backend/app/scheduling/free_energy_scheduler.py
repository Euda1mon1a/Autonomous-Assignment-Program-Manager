"""
Free Energy Principle Scheduler.

Applies Friston's Free Energy framework to schedule optimization:
- Free Energy = Prediction Error² + λ × Model Complexity
- Minimize surprise between forecasted demand and actual assignments
- Active inference: change schedule OR update demand forecast

Neuroscience basis: Brain continuously minimizes variational free energy
by correcting world models OR making world match predictions.

Key Concepts:
- Prediction Error: Gap between expected coverage and actual assignments
- Model Complexity: KL divergence between learned and prior distributions
- Active Inference: Bidirectional optimization (schedule ↔ forecast)
- Generative Model: Learned patterns from historical outcomes

Reference:
- Friston, K. (2010). The free-energy principle: a unified brain theory?
  Nature Reviews Neuroscience, 11(2), 127-138.
"""

import logging
import time
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any
from uuid import UUID

import numpy as np
from scipy.stats import entropy

from app.models.assignment import Assignment
from app.scheduling.bio_inspired.base import (
    BioInspiredSolver,
    Chromosome,
    FitnessVector,
    Individual,
)
from app.scheduling.constraints import ConstraintManager, SchedulingContext
from app.scheduling.solvers import BaseSolver, SolverResult

logger = logging.getLogger(__name__)


@dataclass
class DemandForecast:
    """
    Predicted demand for schedule coverage.

    Represents the scheduler's "expectations" about what the schedule should
    look like based on historical patterns, institutional requirements, and
    operational needs.

    Attributes:
        predicted_coverage: Expected coverage by rotation type (dict[template_id, float])
        predicted_complexity: Expected schedule complexity (0.0-1.0)
        confidence: Forecast confidence level (0.0-1.0)
        forecast_horizon_days: Time horizon for forecast
        generated_at: Timestamp when forecast was generated
        metadata: Additional forecast information
    """

    predicted_coverage: dict[UUID, float]  # template_id -> expected coverage
    predicted_complexity: float  # Expected schedule complexity (0.0-1.0)
    confidence: float  # Forecast confidence (0.0-1.0)
    forecast_horizon_days: int = 28
    generated_at: datetime = field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_vector(self, template_order: list[UUID]) -> np.ndarray:
        """
        Convert forecast to numpy vector for computation.

        Args:
            template_order: Ordered list of template IDs

        Returns:
            Numpy array of predicted coverage values
        """
        return np.array([self.predicted_coverage.get(tid, 0.0) for tid in template_order])

    @classmethod
    def from_historical_data(
        cls,
        historical_assignments: list[Assignment],
        templates: list,
        forecast_horizon_days: int = 28,
    ) -> "DemandForecast":
        """
        Generate forecast from historical assignment patterns.

        Args:
            historical_assignments: Past assignments to learn from
            templates: Available rotation templates
            forecast_horizon_days: Time horizon for forecast

        Returns:
            DemandForecast based on historical patterns
        """
        # Count historical coverage by template
        template_counts = {}
        for assignment in historical_assignments:
            tid = assignment.rotation_template_id
            template_counts[tid] = template_counts.get(tid, 0) + 1

        # Normalize to probabilities
        total = sum(template_counts.values()) if template_counts else 1
        predicted_coverage = {
            tid: count / total for tid, count in template_counts.items()
        }

        # Estimate complexity from assignment variance
        if len(historical_assignments) > 1:
            person_workloads = {}
            for assignment in historical_assignments:
                pid = assignment.person_id
                person_workloads[pid] = person_workloads.get(pid, 0) + 1

            workloads = list(person_workloads.values())
            cv = np.std(workloads) / np.mean(workloads) if np.mean(workloads) > 0 else 0
            predicted_complexity = min(1.0, cv)
        else:
            predicted_complexity = 0.5

        # Confidence based on sample size
        confidence = min(1.0, len(historical_assignments) / 100)

        return cls(
            predicted_coverage=predicted_coverage,
            predicted_complexity=predicted_complexity,
            confidence=confidence,
            forecast_horizon_days=forecast_horizon_days,
            metadata={"historical_sample_size": len(historical_assignments)},
        )

    @classmethod
    def from_uniform_prior(
        cls,
        templates: list,
        forecast_horizon_days: int = 28,
    ) -> "DemandForecast":
        """
        Create uniform prior forecast (no historical data).

        Args:
            templates: Available rotation templates
            forecast_horizon_days: Time horizon for forecast

        Returns:
            DemandForecast with uniform distribution
        """
        n_templates = len(templates)
        uniform_coverage = 1.0 / n_templates if n_templates > 0 else 0.0

        predicted_coverage = {t.id: uniform_coverage for t in templates}

        return cls(
            predicted_coverage=predicted_coverage,
            predicted_complexity=0.5,  # Neutral complexity
            confidence=0.3,  # Low confidence (no data)
            forecast_horizon_days=forecast_horizon_days,
            metadata={"prior_type": "uniform"},
        )


@dataclass
class ScheduleOutcome:
    """
    Realized outcome of a schedule execution.

    Tracks actual performance metrics for updating the generative model.

    Attributes:
        actual_coverage: Actual coverage achieved by rotation type
        actual_complexity: Actual schedule complexity observed
        quality_metrics: Performance metrics (satisfaction, compliance, etc.)
        timestamp: When outcome was recorded
        schedule_id: Reference to the schedule
    """

    actual_coverage: dict[UUID, float]  # template_id -> actual coverage
    actual_complexity: float
    quality_metrics: dict[str, float] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    schedule_id: str | None = None


@dataclass
class SurpriseMetric:
    """
    Tracks prediction errors over time.

    Measures how much the realized schedule "surprised" the model.
    High surprise indicates model needs updating.

    Attributes:
        prediction_error: Magnitude of prediction error
        complexity_error: Error in complexity prediction
        total_surprise: Combined surprise metric
        timestamp: When surprise was measured
    """

    prediction_error: float
    complexity_error: float
    total_surprise: float
    timestamp: datetime = field(default_factory=datetime.utcnow)


class GenerativeModel:
    """
    Learns schedule patterns from historical outcomes.

    The generative model maintains probability distributions over schedule
    characteristics and updates them based on observed outcomes.

    Uses Bayesian updating to refine predictions over time.

    Attributes:
        prior_weights: Initial parameter distribution
        learned_weights: Current learned parameters
        outcomes_seen: Number of outcomes used for learning
        learning_rate: Adaptation rate for updates
    """

    def __init__(
        self,
        n_templates: int,
        learning_rate: float = 0.1,
        prior_strength: float = 1.0,
    ):
        """
        Initialize generative model.

        Args:
            n_templates: Number of rotation templates
            learning_rate: How fast to adapt to new data (0.0-1.0)
            prior_strength: Weight of prior distribution
        """
        self.n_templates = n_templates
        self.learning_rate = learning_rate
        self.prior_strength = prior_strength

        # Initialize with uniform prior
        self.prior_weights = np.ones(n_templates) / n_templates
        self.learned_weights = self.prior_weights.copy()
        self.outcomes_seen = 0

        # Track prediction errors for meta-learning
        self.error_history: list[float] = []

    def update(self, outcome: ScheduleOutcome, template_order: list[UUID]):
        """
        Update model based on observed outcome (Bayesian learning).

        Args:
            outcome: Realized schedule outcome
            template_order: Ordered list of template IDs for vector alignment
        """
        # Convert outcome to vector
        actual_vector = np.array(
            [outcome.actual_coverage.get(tid, 0.0) for tid in template_order]
        )

        # Normalize to probability distribution
        actual_sum = actual_vector.sum()
        if actual_sum > 0:
            actual_vector = actual_vector / actual_sum

        # Bayesian update with exponential moving average
        self.learned_weights = (
            (1 - self.learning_rate) * self.learned_weights
            + self.learning_rate * actual_vector
        )

        # Renormalize
        weight_sum = self.learned_weights.sum()
        if weight_sum > 0:
            self.learned_weights = self.learned_weights / weight_sum

        self.outcomes_seen += 1

        # Track prediction error
        prediction_error = np.linalg.norm(actual_vector - self.learned_weights)
        self.error_history.append(prediction_error)

        logger.debug(
            f"Model updated: outcomes_seen={self.outcomes_seen}, "
            f"prediction_error={prediction_error:.4f}"
        )

    def predict(self, template_order: list[UUID]) -> DemandForecast:
        """
        Generate forecast from current model.

        Args:
            template_order: Ordered list of template IDs

        Returns:
            DemandForecast based on learned patterns
        """
        # Create forecast from learned weights
        predicted_coverage = {
            tid: float(weight)
            for tid, weight in zip(template_order, self.learned_weights)
        }

        # Estimate complexity from weight distribution entropy
        weight_entropy = entropy(self.learned_weights)
        max_entropy = np.log(self.n_templates)
        predicted_complexity = weight_entropy / max_entropy if max_entropy > 0 else 0.5

        # Confidence increases with sample size
        confidence = min(1.0, self.outcomes_seen / 50)

        return DemandForecast(
            predicted_coverage=predicted_coverage,
            predicted_complexity=predicted_complexity,
            confidence=confidence,
            metadata={
                "outcomes_seen": self.outcomes_seen,
                "model_entropy": weight_entropy,
            },
        )

    def compute_kl_divergence(self) -> float:
        """
        Compute KL divergence between learned and prior distributions.

        This measures model complexity - how far the learned model has
        diverged from the prior (simple) explanation.

        Returns:
            KL divergence (bits)
        """
        # Add small epsilon to avoid log(0)
        epsilon = 1e-10
        learned_safe = np.clip(self.learned_weights, epsilon, 1.0)
        prior_safe = np.clip(self.prior_weights, epsilon, 1.0)

        kl = np.sum(learned_safe * np.log(learned_safe / prior_safe))
        return float(kl)

    def reset_to_prior(self):
        """Reset learned weights to prior (forget learning)."""
        self.learned_weights = self.prior_weights.copy()
        self.outcomes_seen = 0
        self.error_history.clear()
        logger.info("Generative model reset to prior")


class FreeEnergyScheduler(BioInspiredSolver):
    """
    Free Energy Principle-based schedule optimizer.

    Minimizes variational free energy:
        F = E[prediction_error²] + λ × KL(learned || prior)

    Where:
    - Prediction error: Gap between forecast and actual schedule
    - KL divergence: Model complexity penalty

    Implements active inference:
    1. Generate schedule to match forecast (minimize prediction error)
    2. Update forecast to match schedule patterns (minimize complexity)
    """

    def __init__(
        self,
        constraint_manager: ConstraintManager | None = None,
        timeout_seconds: float = 300.0,
        population_size: int = 50,
        max_generations: int = 100,
        lambda_complexity: float = 0.1,
        learning_rate: float = 0.1,
        active_inference_enabled: bool = True,
        seed: int | None = None,
    ):
        """
        Initialize Free Energy scheduler.

        Args:
            constraint_manager: Constraint manager for validation
            timeout_seconds: Maximum solve time
            population_size: Number of candidate schedules
            max_generations: Maximum iterations
            lambda_complexity: Weight for model complexity penalty
            learning_rate: Rate of model adaptation
            active_inference_enabled: Whether to update forecast during optimization
            seed: Random seed
        """
        super().__init__(
            constraint_manager=constraint_manager,
            timeout_seconds=timeout_seconds,
            population_size=population_size,
            max_generations=max_generations,
            seed=seed,
        )

        self.lambda_complexity = lambda_complexity
        self.learning_rate = learning_rate
        self.active_inference_enabled = active_inference_enabled

        # Free energy components
        self.generative_model: GenerativeModel | None = None
        self.current_forecast: DemandForecast | None = None
        self.surprise_history: list[SurpriseMetric] = []

    def compute_prediction_error(
        self,
        forecast: DemandForecast,
        schedule: Chromosome,
        context: SchedulingContext,
    ) -> float:
        """
        Compute prediction error between forecast and schedule.

        Measures "surprise" - how much the schedule deviates from expectations.

        Args:
            forecast: Predicted demand
            schedule: Candidate schedule (chromosome)
            context: Scheduling context

        Returns:
            Prediction error (L2 norm)
        """
        # Get template order for vector alignment
        template_order = [t.id for t in context.templates]

        # Convert forecast to vector
        forecast_vector = forecast.to_vector(template_order)

        # Compute actual coverage from schedule
        template_counts = dict.fromkeys(template_order, 0)
        assignments = schedule.to_assignment_list(context)

        for _, _, template_id in assignments:
            if template_id in template_counts:
                template_counts[template_id] += 1

        # Normalize to distribution
        total = sum(template_counts.values())
        actual_vector = np.array(
            [template_counts[tid] / total if total > 0 else 0 for tid in template_order]
        )

        # L2 distance
        prediction_error = float(np.linalg.norm(actual_vector - forecast_vector))

        return prediction_error

    def compute_model_complexity(
        self,
        learned_weights: dict[str, Any],
        prior_weights: dict[str, Any],
    ) -> float:
        """
        Compute model complexity as KL divergence.

        Args:
            learned_weights: Current learned parameters
            prior_weights: Prior parameter distribution

        Returns:
            KL divergence (model complexity)
        """
        if self.generative_model is None:
            return 0.0

        return self.generative_model.compute_kl_divergence()

    def compute_free_energy(
        self,
        schedule: Chromosome,
        forecast: DemandForecast,
        context: SchedulingContext,
    ) -> float:
        """
        Compute total free energy for a schedule.

        F = prediction_error² + λ × model_complexity

        Args:
            schedule: Candidate schedule
            forecast: Current demand forecast
            context: Scheduling context

        Returns:
            Free energy value (lower is better)
        """
        # Prediction error term
        pred_error = self.compute_prediction_error(forecast, schedule, context)
        prediction_term = pred_error**2

        # Model complexity term (KL divergence)
        complexity_term = self.compute_model_complexity({}, {})

        # Total free energy
        free_energy = prediction_term + self.lambda_complexity * complexity_term

        return free_energy

    def minimize_free_energy(
        self,
        initial_schedule: Chromosome,
        forecast: DemandForecast,
        context: SchedulingContext,
        max_iterations: int = 100,
    ) -> Chromosome:
        """
        Minimize free energy through gradient descent.

        Uses evolutionary optimization to find schedule that minimizes:
        - Prediction error (schedule matches forecast)
        - Model complexity (forecast remains simple)

        Args:
            initial_schedule: Starting schedule
            forecast: Current demand forecast
            context: Scheduling context
            max_iterations: Maximum optimization steps

        Returns:
            Optimized schedule with minimal free energy
        """
        current = initial_schedule.copy()
        best_energy = self.compute_free_energy(current, forecast, context)

        for iteration in range(max_iterations):
            # Try mutation
            candidate = current.copy()

            # Random mutation: swap two assignments
            n_residents, n_blocks = candidate.genes.shape
            if n_residents > 0 and n_blocks > 0:
                r = np.random.randint(0, n_residents)
                b1, b2 = np.random.choice(n_blocks, size=2, replace=False)
                candidate.genes[r, b1], candidate.genes[r, b2] = (
                    candidate.genes[r, b2],
                    candidate.genes[r, b1],
                )

            # Evaluate
            candidate_energy = self.compute_free_energy(candidate, forecast, context)

            # Accept if better
            if candidate_energy < best_energy:
                current = candidate
                best_energy = candidate_energy

            # Early stopping if converged
            if iteration > 10 and best_energy < 0.01:
                break

        logger.debug(
            f"Free energy minimization: {max_iterations} iterations, "
            f"final_energy={best_energy:.4f}"
        )

        return current

    def active_inference_step(
        self,
        schedule: Chromosome,
        forecast: DemandForecast,
        context: SchedulingContext,
    ) -> tuple[Chromosome, DemandForecast]:
        """
        Perform active inference: update both schedule AND forecast.

        This is the key insight from FEP: the brain minimizes surprise by:
        1. Changing actions to match predictions (update schedule)
        2. Changing predictions to match reality (update forecast)

        Args:
            schedule: Current schedule
            forecast: Current forecast
            context: Scheduling context

        Returns:
            Tuple of (updated_schedule, updated_forecast)
        """
        # Step 1: Update schedule to match forecast (action)
        updated_schedule = self.minimize_free_energy(
            initial_schedule=schedule,
            forecast=forecast,
            context=context,
            max_iterations=20,
        )

        # Step 2: Update forecast to match schedule (perception)
        if self.active_inference_enabled and self.generative_model is not None:
            # Create synthetic outcome from current schedule
            template_order = [t.id for t in context.templates]
            assignments = updated_schedule.to_assignment_list(context)

            template_counts = dict.fromkeys(template_order, 0)
            for _, _, template_id in assignments:
                if template_id in template_counts:
                    template_counts[template_id] += 1

            total = sum(template_counts.values())
            actual_coverage = {
                tid: count / total if total > 0 else 0.0
                for tid, count in template_counts.items()
            }

            # Estimate complexity
            coverage_values = list(actual_coverage.values())
            actual_complexity = (
                float(np.std(coverage_values)) if len(coverage_values) > 1 else 0.5
            )

            outcome = ScheduleOutcome(
                actual_coverage=actual_coverage,
                actual_complexity=actual_complexity,
            )

            # Update model
            self.generative_model.update(outcome, template_order)

            # Generate new forecast
            updated_forecast = self.generative_model.predict(template_order)
        else:
            updated_forecast = forecast

        return updated_schedule, updated_forecast

    def update_generative_model(self, historical_outcomes: list[ScheduleOutcome]):
        """
        Update generative model from historical outcomes.

        Args:
            historical_outcomes: Past schedule outcomes to learn from
        """
        if self.generative_model is None:
            logger.warning("Generative model not initialized")
            return

        if not self._context:
            logger.warning("No context available for model update")
            return

        template_order = [t.id for t in self._context.templates]

        for outcome in historical_outcomes:
            self.generative_model.update(outcome, template_order)

        logger.info(
            f"Generative model updated with {len(historical_outcomes)} outcomes. "
            f"Total seen: {self.generative_model.outcomes_seen}"
        )

    def _evolve(self, context: SchedulingContext) -> Individual:
        """
        Run free energy minimization evolution.

        Implements the core FEP optimization loop.

        Args:
            context: Scheduling context

        Returns:
            Best individual found
        """
        start_time = time.time()

        # Initialize generative model
        n_templates = len(context.templates)
        self.generative_model = GenerativeModel(
            n_templates=n_templates,
            learning_rate=self.learning_rate,
        )

        # Generate initial forecast
        if hasattr(context, "historical_assignments") and context.historical_assignments:
            self.current_forecast = DemandForecast.from_historical_data(
                historical_assignments=context.historical_assignments,
                templates=list(context.templates),
            )
        else:
            self.current_forecast = DemandForecast.from_uniform_prior(
                templates=list(context.templates),
            )

        logger.info(
            f"Free Energy Scheduler: Initial forecast confidence={self.current_forecast.confidence:.2f}"
        )

        # Initialize population
        self.population = self.initialize_population(context)

        best_individual = max(
            self.population, key=lambda ind: ind.fitness.weighted_sum() if ind.fitness else 0
        )

        # Evolution loop
        for generation in range(self.max_generations):
            if time.time() - start_time > self.timeout_seconds:
                logger.warning("Free energy optimization timeout")
                break

            # Active inference on best individual
            if self.active_inference_enabled:
                updated_schedule, updated_forecast = self.active_inference_step(
                    schedule=best_individual.chromosome,
                    forecast=self.current_forecast,
                    context=context,
                )

                # Update best individual
                best_individual.chromosome = updated_schedule
                best_individual.fitness = self.evaluate_fitness(updated_schedule, context)

                # Update forecast
                self.current_forecast = updated_forecast

            # Compute free energy for tracking
            free_energy = self.compute_free_energy(
                schedule=best_individual.chromosome,
                forecast=self.current_forecast,
                context=context,
            )

            # Track surprise
            pred_error = self.compute_prediction_error(
                forecast=self.current_forecast,
                schedule=best_individual.chromosome,
                context=context,
            )

            surprise = SurpriseMetric(
                prediction_error=pred_error,
                complexity_error=0.0,  # Placeholder
                total_surprise=free_energy,
            )
            self.surprise_history.append(surprise)

            # Evolve population (standard genetic operations)
            new_population = []

            # Elitism: keep best
            new_population.append(best_individual.copy())

            # Generate offspring
            while len(new_population) < self.population_size:
                # Tournament selection
                tournament = np.random.choice(self.population, size=3, replace=False)
                parent = max(
                    tournament,
                    key=lambda ind: ind.fitness.weighted_sum() if ind.fitness else 0,
                )

                # Mutate
                child_chromosome = parent.chromosome.copy()
                n_residents, n_blocks = child_chromosome.genes.shape

                if n_residents > 0 and n_blocks > 0 and np.random.random() < 0.1:
                    r = np.random.randint(0, n_residents)
                    b = np.random.randint(0, n_blocks)
                    n_templates = len(context.templates)
                    child_chromosome.genes[r, b] = np.random.randint(0, n_templates + 1)

                # Evaluate
                child_fitness = self.evaluate_fitness(child_chromosome, context)
                child = Individual(
                    chromosome=child_chromosome,
                    fitness=child_fitness,
                    generation=generation + 1,
                    parent_ids=[parent.id],
                    id=self._get_next_id(),
                )

                new_population.append(child)

            self.population = new_population

            # Update best
            current_best = max(
                self.population,
                key=lambda ind: ind.fitness.weighted_sum() if ind.fitness else 0,
            )
            if (
                current_best.fitness
                and best_individual.fitness
                and current_best.fitness.weighted_sum() > best_individual.fitness.weighted_sum()
            ):
                best_individual = current_best

            # Track evolution
            if self.track_evolution and generation % 10 == 0:
                stats = self.compute_population_stats(self.population, generation)
                self.evolution_history.append(stats)

                logger.debug(
                    f"Gen {generation}: fitness={stats.best_fitness:.4f}, "
                    f"free_energy={free_energy:.4f}, "
                    f"prediction_error={pred_error:.4f}"
                )

        self.best_individual = best_individual

        runtime = time.time() - start_time
        logger.info(
            f"Free Energy optimization complete: {len(self.evolution_history)} generations, "
            f"runtime={runtime:.2f}s, "
            f"final_free_energy={free_energy:.4f}"
        )

        return best_individual
