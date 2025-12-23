"""Pareto optimization service for multi-objective scheduling using pymoo."""

import time
from typing import Any
from uuid import UUID

import numpy as np
from pymoo.algorithms.moo.nsga2 import NSGA2
from pymoo.core.problem import Problem
from pymoo.indicators.hv import HV
from pymoo.operators.crossover.sbx import SBX
from pymoo.operators.mutation.pm import PM
from pymoo.operators.sampling.rnd import FloatRandomSampling
from pymoo.optimize import minimize
from pymoo.termination import get_termination
from sqlalchemy.orm import Session

from app.models.block import Block
from app.models.person import Person
from app.repositories.assignment import AssignmentRepository
from app.repositories.block import BlockRepository
from app.repositories.person import PersonRepository
from app.schemas.pareto import (
    ObjectiveDirection,
    ParetoConstraint,
    ParetoObjective,
    ParetoResult,
    ParetoSolution,
    RankedSolution,
)


class SchedulingProblem(Problem):
    """
    Multi-objective scheduling problem for pymoo.

    This class defines the optimization problem for medical staff scheduling
    with multiple competing objectives.
    """

    def __init__(
        self,
        n_persons: int,
        n_blocks: int,
        objectives: list[ParetoObjective],
        constraints: list[ParetoConstraint],
        person_data: list[dict],
        block_data: list[dict],
    ):
        """
        Initialize the scheduling problem.

        Args:
            n_persons: Number of persons to assign
            n_blocks: Number of blocks to fill
            objectives: List of optimization objectives
            constraints: List of constraints to satisfy
            person_data: List of person dictionaries with relevant data
            block_data: List of block dictionaries with relevant data
        """
        self.n_persons = n_persons
        self.n_blocks = n_blocks
        self.objectives_config = objectives
        self.constraints_config = constraints
        self.person_data = person_data
        self.block_data = block_data

        # Decision variables: assignment matrix (n_blocks x n_persons)
        # Each variable is binary (0 or 1) indicating assignment
        n_vars = n_persons * n_blocks

        # Number of objectives
        n_obj = len(objectives)

        # Number of constraints
        n_ieq_constr = len([c for c in constraints if c.is_hard])

        super().__init__(
            n_var=n_vars,
            n_obj=n_obj,
            n_ieq_constr=n_ieq_constr,
            xl=0.0,  # Lower bound
            xu=1.0,  # Upper bound
        )

    def _decode_solution(self, x: np.ndarray) -> np.ndarray:
        """
        Decode decision variables into assignment matrix.

        Args:
            x: Decision variables array

        Returns:
            Assignment matrix (n_blocks x n_persons)
        """
        # Reshape into assignment matrix
        assignment_matrix = x.reshape(self.n_blocks, self.n_persons)

        # Apply threshold to create binary assignments
        assignment_matrix = (assignment_matrix > 0.5).astype(int)

        return assignment_matrix

    def _calculate_fairness(self, assignment_matrix: np.ndarray) -> float:
        """
        Calculate fairness objective (minimize variance in assignments).

        Args:
            assignment_matrix: Binary assignment matrix

        Returns:
            Fairness score (lower is better)
        """
        # Count assignments per person
        assignments_per_person = assignment_matrix.sum(axis=0)

        # Calculate coefficient of variation
        if len(assignments_per_person) > 0:
            mean_assignments = assignments_per_person.mean()
            if mean_assignments > 0:
                std_assignments = assignments_per_person.std()
                return std_assignments / mean_assignments
        return 0.0

    def _calculate_coverage(self, assignment_matrix: np.ndarray) -> float:
        """
        Calculate coverage objective (maximize blocks covered).

        Args:
            assignment_matrix: Binary assignment matrix

        Returns:
            Coverage score (higher is better, negated for minimization)
        """
        # Count blocks that have at least one assignment
        covered_blocks = (assignment_matrix.sum(axis=1) > 0).sum()
        coverage_rate = covered_blocks / self.n_blocks if self.n_blocks > 0 else 0.0

        # Return negative for minimization in pymoo
        return -coverage_rate

    def _calculate_preference_satisfaction(
        self, assignment_matrix: np.ndarray
    ) -> float:
        """
        Calculate preference satisfaction (maximize assignments to preferred blocks).

        Args:
            assignment_matrix: Binary assignment matrix

        Returns:
            Preference score (higher is better, negated for minimization)
        """
        satisfaction_score = 0.0
        total_assignments = 0

        for block_idx in range(self.n_blocks):
            for person_idx in range(self.n_persons):
                if assignment_matrix[block_idx, person_idx] == 1:
                    total_assignments += 1
                    # Check if this person has preference for this block type
                    # (simplified - would use actual preference data)
                    person = self.person_data[person_idx]
                    block = self.block_data[block_idx]

                    # Example preference matching logic
                    if person.get("preferred_activity_types") and block.get(
                        "activity_type"
                    ):
                        if block["activity_type"] in person["preferred_activity_types"]:
                            satisfaction_score += 1.0

        # Normalize by total assignments
        if total_assignments > 0:
            satisfaction_score /= total_assignments

        # Return negative for minimization
        return -satisfaction_score

    def _calculate_workload_balance(self, assignment_matrix: np.ndarray) -> float:
        """
        Calculate workload balance (minimize max workload difference).

        Args:
            assignment_matrix: Binary assignment matrix

        Returns:
            Workload balance score (lower is better)
        """
        assignments_per_person = assignment_matrix.sum(axis=0)

        if len(assignments_per_person) > 0:
            max_assignments = assignments_per_person.max()
            min_assignments = assignments_per_person.min()
            return float(max_assignments - min_assignments)

        return 0.0

    def _calculate_consecutive_days(self, assignment_matrix: np.ndarray) -> float:
        """
        Calculate consecutive days penalty (minimize consecutive assignments).

        Args:
            assignment_matrix: Binary assignment matrix

        Returns:
            Consecutive days penalty (lower is better)
        """
        penalty = 0.0

        # Check each person's assignments chronologically
        for person_idx in range(self.n_persons):
            person_assignments = assignment_matrix[:, person_idx]
            consecutive_count = 0

            for block_idx in range(self.n_blocks):
                if person_assignments[block_idx] == 1:
                    consecutive_count += 1
                    if consecutive_count > 5:  # Penalize more than 5 consecutive
                        penalty += (consecutive_count - 5) ** 2
                else:
                    consecutive_count = 0

        return penalty

    def _calculate_specialty_distribution(self, assignment_matrix: np.ndarray) -> float:
        """
        Calculate specialty distribution (balance assignments across specialties).

        Args:
            assignment_matrix: Binary assignment matrix

        Returns:
            Distribution score (lower is better)
        """
        specialty_counts: dict[str, int] = {}

        for block_idx in range(self.n_blocks):
            for person_idx in range(self.n_persons):
                if assignment_matrix[block_idx, person_idx] == 1:
                    block = self.block_data[block_idx]
                    specialty = block.get("specialty", "unknown")
                    specialty_counts[specialty] = specialty_counts.get(specialty, 0) + 1

        if specialty_counts:
            counts = list(specialty_counts.values())
            return float(np.std(counts))

        return 0.0

    def _evaluate(self, x: np.ndarray, out: dict, *args, **kwargs):
        """
        Evaluate objectives and constraints for the given solution.

        Args:
            x: Decision variables (flattened assignment matrix)
            out: Output dictionary for objectives and constraints
        """
        # Decode solution
        assignment_matrix = self._decode_solution(x)

        # Calculate objectives
        objectives = []
        for obj in self.objectives_config:
            if obj.name.value == "fairness":
                value = self._calculate_fairness(assignment_matrix)
            elif obj.name.value == "coverage":
                value = self._calculate_coverage(assignment_matrix)
            elif obj.name.value == "preference_satisfaction":
                value = self._calculate_preference_satisfaction(assignment_matrix)
            elif obj.name.value == "workload_balance":
                value = self._calculate_workload_balance(assignment_matrix)
            elif obj.name.value == "consecutive_days":
                value = self._calculate_consecutive_days(assignment_matrix)
            elif obj.name.value == "specialty_distribution":
                value = self._calculate_specialty_distribution(assignment_matrix)
            else:
                value = 0.0

            # Apply direction (pymoo minimizes by default)
            if obj.direction == ObjectiveDirection.MAXIMIZE:
                value = -value

            objectives.append(value)

        out["F"] = np.array(objectives)

        # Calculate constraint violations
        if self.constraints_config:
            constraints = []

            for constraint in self.constraints_config:
                if not constraint.is_hard:
                    continue

                violation = 0.0

                if constraint.constraint_type == "max_consecutive_days":
                    max_days = constraint.parameters.get("max_days", 5)
                    for person_idx in range(self.n_persons):
                        consecutive = 0
                        for block_idx in range(self.n_blocks):
                            if assignment_matrix[block_idx, person_idx] == 1:
                                consecutive += 1
                                if consecutive > max_days:
                                    violation += consecutive - max_days
                            else:
                                consecutive = 0

                elif constraint.constraint_type == "min_coverage":
                    min_coverage = constraint.parameters.get("min_rate", 0.8)
                    covered = (assignment_matrix.sum(axis=1) > 0).sum()
                    coverage_rate = (
                        covered / self.n_blocks if self.n_blocks > 0 else 0.0
                    )
                    if coverage_rate < min_coverage:
                        violation = min_coverage - coverage_rate

                elif constraint.constraint_type == "max_assignments_per_person":
                    max_assignments = constraint.parameters.get("max_count", 10)
                    assignments = assignment_matrix.sum(axis=0)
                    violation = max(0, (assignments - max_assignments).max())

                constraints.append(violation)

            if constraints:
                out["G"] = np.array(constraints)


class ParetoOptimizationService:
    """Service for multi-objective Pareto optimization of schedules."""

    def __init__(self, db: Session):
        """
        Initialize the Pareto optimization service.

        Args:
            db: Database session
        """
        self.db = db
        self.assignment_repo = AssignmentRepository(db)
        self.block_repo = BlockRepository(db)
        self.person_repo = PersonRepository(db)

    def optimize_schedule_pareto(
        self,
        objectives: list[ParetoObjective],
        constraints: list[ParetoConstraint],
        person_ids: list[UUID] | None = None,
        block_ids: list[UUID] | None = None,
        population_size: int = 100,
        n_generations: int = 100,
        timeout_seconds: float = 300.0,
        seed: int | None = None,
    ) -> ParetoResult:
        """
        Optimize schedule using multi-objective Pareto optimization.

        Args:
            objectives: List of objectives to optimize
            constraints: List of constraints to satisfy
            person_ids: Optional filter for specific persons
            block_ids: Optional filter for specific blocks
            population_size: Size of the population for NSGA-II
            n_generations: Number of generations to evolve
            timeout_seconds: Maximum optimization time
            seed: Random seed for reproducibility

        Returns:
            ParetoResult with all solutions and Pareto frontier
        """
        start_time = time.time()

        # Fetch persons and blocks
        persons = self._get_persons(person_ids)
        blocks = self._get_blocks(block_ids)

        if not persons or not blocks:
            return ParetoResult(
                solutions=[],
                frontier_indices=[],
                hypervolume=None,
                total_solutions=0,
                execution_time_seconds=time.time() - start_time,
                termination_reason="No persons or blocks available",
            )

        # Prepare data
        person_data = [self._person_to_dict(p) for p in persons]
        block_data = [self._block_to_dict(b) for b in blocks]

        # Create optimization problem
        problem = SchedulingProblem(
            n_persons=len(persons),
            n_blocks=len(blocks),
            objectives=objectives,
            constraints=constraints,
            person_data=person_data,
            block_data=block_data,
        )

        # Configure NSGA-II algorithm
        algorithm = NSGA2(
            pop_size=population_size,
            sampling=FloatRandomSampling(),
            crossover=SBX(prob=0.9, eta=15),
            mutation=PM(eta=20),
            eliminate_duplicates=True,
        )

        # Set up termination criteria
        termination = get_termination("n_gen", n_generations)

        # Run optimization
        res = minimize(
            problem,
            algorithm,
            termination,
            seed=seed,
            verbose=False,
        )

        execution_time = time.time() - start_time

        # Extract solutions
        solutions = self._extract_solutions(
            res,
            persons,
            blocks,
            objectives,
        )

        # Find Pareto frontier indices
        frontier_indices = self._find_pareto_frontier(solutions)

        # Calculate hypervolume
        hypervolume = self._calculate_hypervolume(solutions, frontier_indices)

        return ParetoResult(
            solutions=solutions,
            frontier_indices=frontier_indices,
            hypervolume=hypervolume,
            total_solutions=len(solutions),
            convergence_metric=res.algorithm.n_gen / n_generations
            if hasattr(res.algorithm, "n_gen")
            else None,
            execution_time_seconds=execution_time,
            algorithm="NSGA-II",
            termination_reason="Max generations reached"
            if execution_time < timeout_seconds
            else "Timeout",
        )

    def get_pareto_frontier(
        self, solutions: list[ParetoSolution]
    ) -> list[ParetoSolution]:
        """
        Extract solutions on the Pareto frontier.

        Args:
            solutions: List of all solutions

        Returns:
            List of solutions on the Pareto frontier (non-dominated solutions)
        """
        frontier_indices = self._find_pareto_frontier(solutions)
        return [solutions[idx] for idx in frontier_indices]

    def rank_solutions(
        self,
        solutions: list[ParetoSolution],
        weights: dict[str, float],
        normalization: str = "minmax",
    ) -> list[RankedSolution]:
        """
        Rank solutions based on weighted objective values.

        Args:
            solutions: List of solutions to rank
            weights: Dictionary of objective weights
            normalization: Normalization method (minmax, zscore, none)

        Returns:
            List of ranked solutions ordered by score
        """
        if not solutions:
            return []

        # Extract objective values
        objective_names = list(solutions[0].objective_values.keys())
        n_solutions = len(solutions)

        # Create matrix of objective values
        obj_matrix = np.zeros((n_solutions, len(objective_names)))
        for i, sol in enumerate(solutions):
            for j, obj_name in enumerate(objective_names):
                obj_matrix[i, j] = sol.objective_values.get(obj_name, 0.0)

        # Normalize
        if normalization == "minmax":
            obj_min = obj_matrix.min(axis=0)
            obj_max = obj_matrix.max(axis=0)
            obj_range = obj_max - obj_min
            obj_range[obj_range == 0] = 1.0  # Avoid division by zero
            obj_matrix_norm = (obj_matrix - obj_min) / obj_range
        elif normalization == "zscore":
            obj_mean = obj_matrix.mean(axis=0)
            obj_std = obj_matrix.std(axis=0)
            obj_std[obj_std == 0] = 1.0  # Avoid division by zero
            obj_matrix_norm = (obj_matrix - obj_mean) / obj_std
        else:
            obj_matrix_norm = obj_matrix

        # Calculate weighted scores
        ranked_solutions = []
        for i, sol in enumerate(solutions):
            weighted_breakdown = {}
            total_score = 0.0

            for j, obj_name in enumerate(objective_names):
                weight = weights.get(obj_name, 0.0)
                weighted_value = obj_matrix_norm[i, j] * weight
                weighted_breakdown[obj_name] = weighted_value
                total_score += weighted_value

            ranked_solutions.append(
                RankedSolution(
                    solution_id=sol.solution_id,
                    rank=0,  # Will be set after sorting
                    score=total_score,
                    objective_values=sol.objective_values.copy(),
                    weighted_score_breakdown=weighted_breakdown,
                )
            )

        # Sort by score (descending)
        ranked_solutions.sort(key=lambda x: x.score, reverse=True)

        # Assign ranks
        for rank, sol in enumerate(ranked_solutions, start=1):
            sol.rank = rank

        return ranked_solutions

    def _get_persons(self, person_ids: list[UUID] | None) -> list[Person]:
        """Fetch persons from database."""
        if person_ids:
            return [
                self.person_repo.get_by_id(pid)
                for pid in person_ids
                if self.person_repo.get_by_id(pid)
            ]
        return self.person_repo.list_all()[:50]  # Limit for performance

    def _get_blocks(self, block_ids: list[UUID] | None) -> list[Block]:
        """Fetch blocks from database."""
        if block_ids:
            return [
                self.block_repo.get_by_id(bid)
                for bid in block_ids
                if self.block_repo.get_by_id(bid)
            ]
        return self.block_repo.list_all()[:100]  # Limit for performance

    def _person_to_dict(self, person: Person) -> dict:
        """Convert person model to dictionary."""
        return {
            "id": str(person.id),
            "name": person.name,
            "pgy_level": person.pgy_level,
            "preferred_activity_types": getattr(person, "preferred_activity_types", []),
        }

    def _block_to_dict(self, block: Block) -> dict:
        """Convert block model to dictionary."""
        return {
            "id": str(block.id),
            "name": block.name,
            "activity_type": block.activity_type,
            "specialty": getattr(block, "specialty", "general"),
            "start_date": str(block.start_date),
            "end_date": str(block.end_date),
        }

    def _extract_solutions(
        self,
        result: Any,
        persons: list[Person],
        blocks: list[Block],
        objectives: list[ParetoObjective],
    ) -> list[ParetoSolution]:
        """Extract solutions from pymoo result."""
        solutions = []

        if result.X is None or result.F is None:
            return solutions

        # Handle both single and multiple solutions
        X = result.X if result.X.ndim == 2 else result.X.reshape(1, -1)
        F = result.F if result.F.ndim == 2 else result.F.reshape(1, -1)

        for sol_idx in range(len(X)):
            x = X[sol_idx]
            f = F[sol_idx]

            # Decode assignment matrix
            assignment_matrix = (x.reshape(len(blocks), len(persons)) > 0.5).astype(int)

            # Create decision variables dict
            decision_vars = {}
            for block_idx, block in enumerate(blocks):
                for person_idx, person in enumerate(persons):
                    if assignment_matrix[block_idx, person_idx] == 1:
                        key = f"block_{block.id}_person_{person.id}"
                        decision_vars[key] = {
                            "block_id": str(block.id),
                            "person_id": str(person.id),
                            "block_name": block.name,
                            "person_name": person.name,
                        }

            # Create objective values dict
            objective_values = {}
            for obj_idx, obj in enumerate(objectives):
                value = f[obj_idx]
                # Reverse negation for maximization objectives
                if obj.direction == ObjectiveDirection.MAXIMIZE:
                    value = -value
                objective_values[obj.name.value] = float(value)

            solutions.append(
                ParetoSolution(
                    solution_id=sol_idx,
                    objective_values=objective_values,
                    decision_variables=decision_vars,
                    is_feasible=True,
                    constraint_violations=[],
                )
            )

        return solutions

    def _find_pareto_frontier(self, solutions: list[ParetoSolution]) -> list[int]:
        """
        Find indices of solutions on the Pareto frontier.

        A solution is on the frontier if no other solution dominates it.
        """
        if not solutions:
            return []

        n_solutions = len(solutions)
        is_dominated = [False] * n_solutions

        # Extract objective values
        objective_names = list(solutions[0].objective_values.keys())
        obj_matrix = np.zeros((n_solutions, len(objective_names)))

        for i, sol in enumerate(solutions):
            for j, obj_name in enumerate(objective_names):
                obj_matrix[i, j] = sol.objective_values[obj_name]

        # Check dominance
        for i in range(n_solutions):
            for j in range(n_solutions):
                if i == j:
                    continue

                # Check if j dominates i (all objectives better or equal, at least one strictly better)
                dominates = True
                strictly_better = False

                for k in range(len(objective_names)):
                    if obj_matrix[j, k] < obj_matrix[i, k]:  # Assuming minimization
                        strictly_better = True
                    elif obj_matrix[j, k] > obj_matrix[i, k]:
                        dominates = False
                        break

                if dominates and strictly_better:
                    is_dominated[i] = True
                    break

        # Return non-dominated indices
        return [i for i in range(n_solutions) if not is_dominated[i]]

    def _calculate_hypervolume(
        self, solutions: list[ParetoSolution], frontier_indices: list[int]
    ) -> float | None:
        """Calculate hypervolume indicator for Pareto frontier."""
        if not frontier_indices or not solutions:
            return None

        try:
            # Extract frontier solutions
            objective_names = list(solutions[0].objective_values.keys())
            frontier_points = []

            for idx in frontier_indices:
                point = [
                    solutions[idx].objective_values[obj] for obj in objective_names
                ]
                frontier_points.append(point)

            # Calculate hypervolume with reference point
            F = np.array(frontier_points)
            ref_point = (
                np.max(F, axis=0) + 1.0
            )  # Reference point slightly worse than worst

            hv = HV(ref_point=ref_point)
            return float(hv(F))

        except Exception:
            return None
