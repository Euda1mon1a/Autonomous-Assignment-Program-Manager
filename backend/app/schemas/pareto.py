"""Pareto optimization schemas for multi-objective scheduling."""

from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field, model_validator


class ObjectiveDirection(str, Enum):
    """Direction for objective optimization."""
    MINIMIZE = "minimize"
    MAXIMIZE = "maximize"


class ObjectiveName(str, Enum):
    """Available optimization objectives."""
    FAIRNESS = "fairness"
    COVERAGE = "coverage"
    PREFERENCE_SATISFACTION = "preference_satisfaction"
    WORKLOAD_BALANCE = "workload_balance"
    CONSECUTIVE_DAYS = "consecutive_days"
    SPECIALTY_DISTRIBUTION = "specialty_distribution"


class ParetoObjective(BaseModel):
    """Schema for a single optimization objective."""
    name: ObjectiveName = Field(
        ...,
        description="Name of the objective to optimize"
    )
    weight: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Relative weight of this objective (0.0-1.0)"
    )
    direction: ObjectiveDirection = Field(
        default=ObjectiveDirection.MAXIMIZE,
        description="Whether to minimize or maximize this objective"
    )
    target_value: float | None = Field(
        default=None,
        description="Optional target value for the objective"
    )

    @model_validator(mode='after')
    def validate_weight(self) -> 'ParetoObjective':
        """Ensure weight is between 0 and 1."""
        if not 0.0 <= self.weight <= 1.0:
            raise ValueError(f"Weight must be between 0.0 and 1.0, got {self.weight}")
        return self


class ParetoSolution(BaseModel):
    """Schema for a single solution in the Pareto frontier."""
    solution_id: int = Field(
        ...,
        description="Unique identifier for this solution"
    )
    objective_values: dict[str, float] = Field(
        ...,
        description="Objective values achieved by this solution"
    )
    decision_variables: dict[str, Any] = Field(
        ...,
        description="Assignment decisions made in this solution (person_id -> block_id mappings)"
    )
    is_feasible: bool = Field(
        default=True,
        description="Whether this solution satisfies all constraints"
    )
    constraint_violations: list[str] = Field(
        default=[],
        description="List of constraint violations if infeasible"
    )
    rank: int | None = Field(
        default=None,
        description="Pareto rank (0 = non-dominated, 1 = dominated by rank 0, etc.)"
    )
    crowding_distance: float | None = Field(
        default=None,
        description="Crowding distance for diversity metric"
    )


class ParetoConstraint(BaseModel):
    """Schema for optimization constraints."""
    constraint_type: str = Field(
        ...,
        description="Type of constraint (e.g., 'max_consecutive_days', 'min_rest_hours')"
    )
    parameters: dict[str, Any] = Field(
        default={},
        description="Parameters for the constraint"
    )
    is_hard: bool = Field(
        default=True,
        description="Whether this is a hard constraint (must be satisfied)"
    )


class ParetoResult(BaseModel):
    """Schema for Pareto optimization results."""
    solutions: list[ParetoSolution] = Field(
        ...,
        description="All solutions found during optimization"
    )
    frontier_indices: list[int] = Field(
        ...,
        description="Indices of solutions on the Pareto frontier"
    )
    hypervolume: float | None = Field(
        default=None,
        description="Hypervolume indicator for solution quality"
    )
    total_solutions: int = Field(
        ...,
        description="Total number of solutions evaluated"
    )
    convergence_metric: float | None = Field(
        default=None,
        description="Metric indicating algorithm convergence"
    )
    execution_time_seconds: float = Field(
        ...,
        description="Time taken to complete optimization"
    )
    algorithm: str = Field(
        default="NSGA-II",
        description="Algorithm used for optimization"
    )
    termination_reason: str | None = Field(
        default=None,
        description="Reason why optimization terminated"
    )


class ParetoOptimizeRequest(BaseModel):
    """Request schema for multi-objective Pareto optimization."""
    objectives: list[ParetoObjective] = Field(
        ...,
        min_length=2,
        description="List of objectives to optimize (minimum 2 for multi-objective)"
    )
    constraints: list[ParetoConstraint] = Field(
        default=[],
        description="List of constraints to satisfy"
    )
    population_size: int = Field(
        default=100,
        ge=10,
        le=1000,
        description="Size of the population for genetic algorithm"
    )
    n_generations: int = Field(
        default=100,
        ge=10,
        le=1000,
        description="Number of generations to evolve"
    )
    timeout_seconds: float = Field(
        default=300.0,
        ge=10.0,
        le=3600.0,
        description="Maximum optimization time in seconds"
    )
    seed: int | None = Field(
        default=None,
        description="Random seed for reproducibility"
    )
    person_ids: list[UUID] | None = Field(
        default=None,
        description="Filter to specific persons for assignment"
    )
    block_ids: list[UUID] | None = Field(
        default=None,
        description="Filter to specific blocks for assignment"
    )

    @model_validator(mode='after')
    def validate_objectives(self) -> 'ParetoOptimizeRequest':
        """Ensure at least 2 objectives for multi-objective optimization."""
        if len(self.objectives) < 2:
            raise ValueError(
                "Multi-objective optimization requires at least 2 objectives"
            )
        return self

    @model_validator(mode='after')
    def validate_weights(self) -> 'ParetoOptimizeRequest':
        """Ensure weights sum to a reasonable value."""
        total_weight = sum(obj.weight for obj in self.objectives)
        if total_weight > 0 and (total_weight < 0.1 or total_weight > len(self.objectives)):
            raise ValueError(
                f"Total objective weights ({total_weight}) should be between "
                f"0.1 and {len(self.objectives)}"
            )
        return self


class ParetoOptimizeResponse(BaseModel):
    """Response schema for Pareto optimization."""
    success: bool = Field(
        ...,
        description="Whether optimization completed successfully"
    )
    message: str = Field(
        ...,
        description="Human-readable message about the optimization result"
    )
    result: ParetoResult | None = Field(
        default=None,
        description="Optimization results if successful"
    )
    error: str | None = Field(
        default=None,
        description="Error message if optimization failed"
    )
    recommended_solution_id: int | None = Field(
        default=None,
        description="ID of the recommended solution based on weights"
    )


class SolutionRankRequest(BaseModel):
    """Request schema for ranking solutions."""
    solution_ids: list[int] = Field(
        ...,
        min_length=1,
        description="List of solution IDs to rank"
    )
    weights: dict[str, float] = Field(
        ...,
        description="Weights for each objective used in ranking"
    )
    normalization: str = Field(
        default="minmax",
        description="Normalization method (minmax, zscore, none)"
    )

    @model_validator(mode='after')
    def validate_weights(self) -> 'SolutionRankRequest':
        """Ensure weights are positive."""
        for obj_name, weight in self.weights.items():
            if weight < 0:
                raise ValueError(f"Weight for {obj_name} must be non-negative, got {weight}")
        return self


class RankedSolution(BaseModel):
    """Schema for a ranked solution."""
    solution_id: int
    rank: int  # 1 = best
    score: float
    objective_values: dict[str, float]
    weighted_score_breakdown: dict[str, float]


class SolutionRankResponse(BaseModel):
    """Response schema for ranked solutions."""
    success: bool
    ranked_solutions: list[RankedSolution] = []
    normalization_used: str
    message: str = ""
