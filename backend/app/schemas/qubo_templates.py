"""Pydantic schemas for QUBO template optimization API."""

from datetime import date
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field, model_validator


class TemplateDesirabilityLevel(str, Enum):
    """Classification of rotation template desirability."""

    HIGHLY_DESIRABLE = "highly_desirable"
    NEUTRAL = "neutral"
    UNDESIRABLE = "undesirable"


class QUBOObjectiveWeight(BaseModel):
    """Weights for QUBO optimization objectives."""

    coverage: float = Field(
        default=1.0,
        ge=0.0,
        le=2.0,
        description="Weight for coverage objective (maximize assignments)",
    )
    fairness: float = Field(
        default=1.0,
        ge=0.0,
        le=2.0,
        description="Weight for fairness objective (equal rotation distribution)",
    )
    preference: float = Field(
        default=0.5,
        ge=0.0,
        le=2.0,
        description="Weight for preference satisfaction",
    )
    learning: float = Field(
        default=0.3,
        ge=0.0,
        le=2.0,
        description="Weight for learning goal objective (rotation variety)",
    )


class QUBOAnnealingConfig(BaseModel):
    """Configuration for simulated annealing."""

    num_reads: int = Field(
        default=100,
        ge=1,
        le=1000,
        description="Number of independent annealing runs",
    )
    num_sweeps: int = Field(
        default=1000,
        ge=100,
        le=10000,
        description="Number of sweeps per run",
    )
    beta_start: float = Field(
        default=0.1,
        ge=0.01,
        le=1.0,
        description="Initial inverse temperature (low = high temperature)",
    )
    beta_end: float = Field(
        default=4.2,
        ge=1.0,
        le=10.0,
        description="Final inverse temperature (high = low temperature)",
    )
    use_adaptive_temperature: bool = Field(
        default=True,
        description="Enable adaptive temperature with automatic reheat",
    )


class QUBOParetoConfig(BaseModel):
    """Configuration for Pareto front exploration."""

    enabled: bool = Field(
        default=True,
        description="Enable Pareto front exploration",
    )
    population_size: int = Field(
        default=50,
        ge=10,
        le=200,
        description="Population size for multi-objective optimization",
    )
    generations: int = Field(
        default=100,
        ge=10,
        le=500,
        description="Number of generations for Pareto exploration",
    )
    objectives: list[str] = Field(
        default=["coverage", "fairness", "preference"],
        description="Objectives to include in Pareto optimization",
    )


class TemplateDesirabilityMapping(BaseModel):
    """Mapping of template names to desirability levels."""

    template_name: str = Field(..., description="Name of the rotation template")
    desirability: TemplateDesirabilityLevel = Field(
        ..., description="Desirability classification"
    )


class QUBOTemplateOptimizeRequest(BaseModel):
    """Request schema for QUBO template optimization."""

    start_date: date = Field(..., description="Start date for schedule optimization")
    end_date: date = Field(..., description="End date for schedule optimization")

    # Filtering
    person_ids: list[UUID] | None = Field(
        default=None,
        description="Filter to specific residents (None = all residents)",
    )
    template_ids: list[UUID] | None = Field(
        default=None,
        description="Filter to specific templates (None = all templates)",
    )

    # Objective weights
    objective_weights: QUBOObjectiveWeight = Field(
        default_factory=QUBOObjectiveWeight,
        description="Weights for optimization objectives",
    )

    # Annealing configuration
    annealing_config: QUBOAnnealingConfig = Field(
        default_factory=QUBOAnnealingConfig,
        description="Simulated annealing parameters",
    )

    # Pareto configuration
    pareto_config: QUBOParetoConfig = Field(
        default_factory=QUBOParetoConfig,
        description="Pareto front exploration parameters",
    )

    # Desirability mappings (override defaults)
    desirability_mappings: list[TemplateDesirabilityMapping] | None = Field(
        default=None,
        description="Custom template desirability classifications",
    )

    # Miscellaneous
    seed: int | None = Field(
        default=None,
        description="Random seed for reproducibility",
    )
    timeout_seconds: float = Field(
        default=120.0,
        ge=10.0,
        le=600.0,
        description="Maximum optimization time in seconds",
    )
    include_energy_landscape: bool = Field(
        default=True,
        description="Include energy landscape data for visualization",
    )
    include_benchmarks: bool = Field(
        default=False,
        description="Run and include benchmark comparisons",
    )

    @model_validator(mode="after")
    def validate_dates(self) -> "QUBOTemplateOptimizeRequest":
        """Ensure end_date is after start_date."""
        if self.end_date <= self.start_date:
            raise ValueError("end_date must be after start_date")
        return self


class ParetoSolutionSchema(BaseModel):
    """Schema for a Pareto frontier solution."""

    solution_id: int = Field(..., description="Unique solution identifier")
    objectives: dict[str, float] = Field(
        ..., description="Objective values for this solution"
    )
    rank: int = Field(
        default=0, description="Pareto rank (0 = non-dominated frontier)"
    )
    crowding_distance: float = Field(
        default=0.0, description="Crowding distance for diversity"
    )
    num_assignments: int = Field(
        ..., description="Number of assignments in this solution"
    )


class EnergyLandscapePointSchema(BaseModel):
    """Schema for an energy landscape point."""

    energy: float = Field(..., description="QUBO energy value")
    is_local_minimum: bool = Field(
        default=False, description="Whether this is a local minimum"
    )
    tunneling_probability: float = Field(
        default=0.0, description="Quantum tunneling probability to global minimum"
    )
    basin_size: int = Field(default=1, description="Estimated basin of attraction size")
    objectives: dict[str, float] = Field(
        default={}, description="Individual objective values"
    )


class EnergyLandscapeSchema(BaseModel):
    """Schema for energy landscape visualization data."""

    num_samples: int = Field(..., description="Number of sampled points")
    num_local_minima: int = Field(..., description="Number of local minima found")
    global_minimum_energy: float = Field(
        ..., description="Energy of the global minimum"
    )
    energy_range: dict[str, float] = Field(
        ..., description="Min/max energy range"
    )
    points: list[EnergyLandscapePointSchema] = Field(
        default=[], description="Sampled landscape points"
    )
    minima: list[EnergyLandscapePointSchema] = Field(
        default=[], description="Local minima points"
    )


class BenchmarkResultSchema(BaseModel):
    """Schema for benchmark comparison results."""

    approach: str = Field(..., description="Optimization approach name")
    success: bool = Field(..., description="Whether optimization succeeded")
    num_assignments: int = Field(..., description="Number of assignments produced")
    runtime_seconds: float = Field(..., description="Execution time")
    objective_value: float | None = Field(
        default=None, description="Final objective value"
    )


class BenchmarkComparisonSchema(BaseModel):
    """Schema for benchmark comparisons."""

    qubo: BenchmarkResultSchema
    greedy: BenchmarkResultSchema
    random: BenchmarkResultSchema
    qubo_vs_greedy_improvement: float = Field(
        ..., description="Percentage improvement of QUBO over greedy"
    )
    qubo_vs_random_improvement: float = Field(
        ..., description="Percentage improvement of QUBO over random"
    )


class AssignmentSchema(BaseModel):
    """Schema for a schedule assignment."""

    person_id: UUID = Field(..., description="Resident ID")
    block_id: UUID = Field(..., description="Block ID")
    template_id: UUID | None = Field(default=None, description="Template ID")


class QUBOStatisticsSchema(BaseModel):
    """Schema for QUBO optimization statistics."""

    num_variables: int = Field(..., description="Number of QUBO binary variables")
    num_qubo_terms: int = Field(..., description="Non-zero terms in QUBO matrix")
    qubo_energy: float = Field(..., description="Initial QUBO energy")
    refined_energy: float = Field(..., description="Energy after classical refinement")
    final_energy: float = Field(..., description="Final energy after constraint repair")
    improvement: float = Field(..., description="Total energy improvement")
    num_assignments: int = Field(..., description="Number of final assignments")
    objectives: dict[str, float] = Field(
        default={}, description="Individual objective values"
    )
    pareto_frontier_size: int = Field(
        default=0, description="Number of Pareto frontier solutions"
    )
    num_local_minima: int = Field(default=0, description="Number of local minima found")


class QUBOTemplateOptimizeResponse(BaseModel):
    """Response schema for QUBO template optimization."""

    success: bool = Field(..., description="Whether optimization succeeded")
    message: str = Field(..., description="Human-readable result message")

    # Core results
    assignments: list[AssignmentSchema] = Field(
        default=[], description="Optimized schedule assignments"
    )
    statistics: QUBOStatisticsSchema | None = Field(
        default=None, description="Optimization statistics"
    )

    # Pareto front
    pareto_frontier: list[ParetoSolutionSchema] = Field(
        default=[], description="Pareto frontier solutions"
    )
    recommended_solution_id: int | None = Field(
        default=None, description="ID of recommended solution from Pareto front"
    )

    # Energy landscape (for visualization)
    energy_landscape: EnergyLandscapeSchema | None = Field(
        default=None, description="Energy landscape data for visualization"
    )

    # Benchmarks
    benchmarks: BenchmarkComparisonSchema | None = Field(
        default=None, description="Benchmark comparison results"
    )

    # Timing
    runtime_seconds: float = Field(..., description="Total optimization time")

    # Quantum advantage analysis
    quantum_advantage_estimate: float | None = Field(
        default=None,
        description="Estimated quantum advantage ratio (>1 means QUBO better)",
    )


class QUBOStatusResponse(BaseModel):
    """Response schema for QUBO template selector status."""

    available: bool = Field(..., description="Whether QUBO solver is available")
    features: dict[str, bool] = Field(..., description="Available features")
    recommended_problem_size: dict[str, int] = Field(
        ..., description="Recommended problem size ranges"
    )
    quantum_libraries: dict[str, bool] = Field(
        ..., description="Status of quantum libraries"
    )


class QuantumAdvantageScenario(BaseModel):
    """Schema for quantum advantage scenario description."""

    scenario_name: str = Field(..., description="Name of the scenario")
    description: str = Field(..., description="Detailed description")
    problem_characteristics: list[str] = Field(
        ..., description="Characteristics that enable advantage"
    )
    expected_speedup: str = Field(
        ..., description="Expected speedup over classical (e.g., '2-10x')"
    )
    conditions: list[str] = Field(
        ..., description="Conditions required for advantage"
    )


class QuantumAdvantageDocResponse(BaseModel):
    """Response schema for quantum advantage documentation."""

    overview: str = Field(..., description="Overview of quantum advantage in scheduling")
    scenarios: list[QuantumAdvantageScenario] = Field(
        ..., description="Scenarios where quantum advantage applies"
    )
    current_limitations: list[str] = Field(
        ..., description="Current limitations of quantum approaches"
    )
    recommendations: list[str] = Field(
        ..., description="Recommendations for when to use QUBO"
    )
