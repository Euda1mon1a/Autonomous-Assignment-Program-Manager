"""
Candidate Generator API.

Even if internally you have OR-Tools, CP-SAT, Pyomo, custom heuristics, etc.,
expose one interface:

    generate_candidates(inputs, params, k) -> [candidate]

This lets the control loop swap strategies without rewriting the orchestrator.
"""

from dataclasses import dataclass, field
from datetime import date
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.assignment import Assignment
from app.models.block import Block
from app.models.person import Person
from app.models.rotation_template import RotationTemplate
from app.scheduling.engine import SchedulingEngine
from app.scheduling.constraints import ConstraintManager
from app.resilience.service import ResilienceConfig

from app.autonomous.state import GeneratorParams


@dataclass
class GeneratorConfig:
    """
    Configuration for the candidate generator.

    Attributes:
        algorithms: List of algorithms to use (in order of preference)
        default_timeout: Default solver timeout in seconds
        allow_fallback: Whether to fall back to greedy on failure
        check_resilience: Whether to run resilience checks
    """

    algorithms: list[str] = field(
        default_factory=lambda: ["greedy", "cp_sat", "pulp", "hybrid"]
    )
    default_timeout: float = 60.0
    allow_fallback: bool = True
    check_resilience: bool = True


@dataclass
class ScheduleCandidate:
    """
    A single schedule candidate produced by the generator.

    Attributes:
        assignments: List of assignments in this candidate
        algorithm: Algorithm used to generate this candidate
        params: Parameters used for generation
        solver_stats: Statistics from the solver
        generation_time: Time taken to generate in seconds
        feasible: Whether the solver found a feasible solution
        objective_value: Objective value from solver (if applicable)
    """

    assignments: list[Assignment]
    algorithm: str
    params: GeneratorParams
    solver_stats: dict[str, Any] = field(default_factory=dict)
    generation_time: float = 0.0
    feasible: bool = True
    objective_value: float | None = None

    def assignment_dicts(self) -> list[dict[str, Any]]:
        """Convert assignments to dictionaries for serialization."""
        return [
            {
                "block_id": str(a.block_id),
                "person_id": str(a.person_id),
                "rotation_template_id": str(a.rotation_template_id) if a.rotation_template_id else None,
                "role": a.role,
            }
            for a in self.assignments
        ]


class CandidateGenerator:
    """
    Unified interface to the solver stack.

    This class wraps the existing SchedulingEngine and provides a clean API
    for the control loop to generate schedule candidates.

    The generator can:
    - Generate single candidates with specific parameters
    - Generate multiple candidates with different algorithms/parameters
    - Handle solver failures with fallback to simpler algorithms

    Example:
        >>> generator = CandidateGenerator(db, start_date, end_date)
        >>> candidates = generator.generate_candidates(
        ...     params=GeneratorParams(algorithm="cp_sat"),
        ...     k=3,
        ... )
        >>> for candidate in candidates:
        ...     print(f"{candidate.algorithm}: {len(candidate.assignments)} assignments")
    """

    def __init__(
        self,
        db: Session,
        start_date: date,
        end_date: date,
        config: GeneratorConfig | None = None,
        constraint_manager: ConstraintManager | None = None,
        resilience_config: ResilienceConfig | None = None,
    ):
        """
        Initialize the candidate generator.

        Args:
            db: Database session
            start_date: Schedule start date
            end_date: Schedule end date
            config: Generator configuration
            constraint_manager: Optional constraint manager
            resilience_config: Optional resilience configuration
        """
        self.db = db
        self.start_date = start_date
        self.end_date = end_date
        self.config = config or GeneratorConfig()
        self.constraint_manager = constraint_manager or ConstraintManager.create_default()
        self.resilience_config = resilience_config or ResilienceConfig()

        # Cache loaded data
        self._residents: list[Person] | None = None
        self._faculty: list[Person] | None = None
        self._blocks: list[Block] | None = None
        self._templates: list[RotationTemplate] | None = None

    def generate_candidates(
        self,
        params: GeneratorParams | None = None,
        k: int = 1,
    ) -> list[ScheduleCandidate]:
        """
        Generate k schedule candidates.

        Args:
            params: Generation parameters (uses defaults if None)
            k: Number of candidates to generate

        Returns:
            List of ScheduleCandidate objects
        """
        params = params or GeneratorParams()
        candidates: list[ScheduleCandidate] = []

        if k == 1:
            # Single candidate with specified algorithm
            candidate = self._generate_single(params)
            if candidate:
                candidates.append(candidate)
        else:
            # Multiple candidates with different algorithms
            algorithms = self._select_algorithms(k)
            for algo in algorithms:
                algo_params = GeneratorParams(
                    algorithm=algo,
                    timeout_seconds=params.timeout_seconds,
                    random_seed=params.random_seed,
                    solver_params=params.solver_params,
                    constraint_weights=params.constraint_weights,
                )
                candidate = self._generate_single(algo_params)
                if candidate:
                    candidates.append(candidate)

        return candidates

    def generate_single(
        self,
        params: GeneratorParams | None = None,
    ) -> ScheduleCandidate | None:
        """
        Generate a single schedule candidate.

        Args:
            params: Generation parameters

        Returns:
            ScheduleCandidate or None if generation failed
        """
        return self._generate_single(params or GeneratorParams())

    def _generate_single(
        self,
        params: GeneratorParams,
    ) -> ScheduleCandidate | None:
        """
        Internal method to generate a single candidate.

        This wraps the SchedulingEngine.generate() method and extracts
        the assignments without persisting them to the database.
        """
        import time

        # Create engine
        engine = SchedulingEngine(
            db=self.db,
            start_date=self.start_date,
            end_date=self.end_date,
            constraint_manager=self.constraint_manager,
            resilience_config=self.resilience_config,
        )

        start_time = time.time()

        try:
            # Note: SchedulingEngine.generate() commits to database
            # For candidate generation, we need a different approach
            # We'll use the engine to generate but track the assignments before commit

            # First, ensure blocks exist
            blocks = engine._ensure_blocks_exist(commit=False)

            # Build availability matrix
            engine._build_availability_matrix()

            # Get data
            residents = self._get_residents()
            faculty = self._get_faculty()
            templates = self._get_templates()

            if not residents:
                return None

            # Build context
            context = engine._build_context(
                residents=residents,
                faculty=faculty,
                blocks=blocks,
                templates=templates,
                include_resilience=self.config.check_resilience,
            )

            # Run solver
            solver_result = engine._run_solver(
                algorithm=params.algorithm,
                context=context,
                timeout_seconds=params.timeout_seconds,
            )

            generation_time = time.time() - start_time

            if not solver_result.success:
                if self.config.allow_fallback and params.algorithm != "greedy":
                    # Fallback to greedy
                    solver_result = engine._run_solver(
                        algorithm="greedy",
                        context=context,
                        timeout_seconds=params.timeout_seconds,
                    )
                    generation_time = time.time() - start_time

                if not solver_result.success:
                    return None

            # Convert solver results to assignments (without saving)
            assignments: list[Assignment] = []
            for person_id, block_id, template_id in solver_result.assignments:
                assignment = Assignment(
                    block_id=block_id,
                    person_id=person_id,
                    rotation_template_id=template_id,
                    role="primary",
                )
                assignments.append(assignment)

            # Add faculty assignments
            engine.assignments = assignments
            engine._assign_faculty(faculty, blocks)
            assignments = engine.assignments

            # Rollback any database changes (we don't want to persist yet)
            self.db.rollback()

            return ScheduleCandidate(
                assignments=assignments,
                algorithm=params.algorithm,
                params=params,
                solver_stats=solver_result.statistics,
                generation_time=generation_time,
                feasible=solver_result.success,
                objective_value=solver_result.objective_value,
            )

        except Exception as e:
            self.db.rollback()
            # Log error but don't crash - return None to indicate failure
            import logging
            logging.getLogger(__name__).warning(
                f"Candidate generation failed: {e}"
            )
            return None

    def _select_algorithms(self, k: int) -> list[str]:
        """
        Select k algorithms to use for multi-candidate generation.

        Prioritizes algorithms in config order.
        """
        available = self.config.algorithms
        if k >= len(available):
            return available
        return available[:k]

    def _get_residents(self) -> list[Person]:
        """Get cached residents list."""
        if self._residents is None:
            self._residents = (
                self.db.query(Person)
                .filter(Person.type == "resident")
                .order_by(Person.pgy_level, Person.name)
                .all()
            )
        return self._residents

    def _get_faculty(self) -> list[Person]:
        """Get cached faculty list."""
        if self._faculty is None:
            self._faculty = (
                self.db.query(Person)
                .filter(Person.type == "faculty")
                .all()
            )
        return self._faculty

    def _get_blocks(self) -> list[Block]:
        """Get cached blocks list."""
        if self._blocks is None:
            self._blocks = (
                self.db.query(Block)
                .filter(
                    Block.date >= self.start_date,
                    Block.date <= self.end_date,
                )
                .all()
            )
        return self._blocks

    def _get_templates(self) -> list[RotationTemplate]:
        """Get cached templates list."""
        if self._templates is None:
            self._templates = self.db.query(RotationTemplate).all()
        return self._templates

    def clear_cache(self) -> None:
        """Clear cached data."""
        self._residents = None
        self._faculty = None
        self._blocks = None
        self._templates = None


class GeneratorWithVariation(CandidateGenerator):
    """
    Extended generator that introduces controlled variation.

    Used when the control loop needs to explore the solution space
    through diversification (random restarts, perturbations).
    """

    def generate_with_restart(
        self,
        base_params: GeneratorParams,
        num_restarts: int = 3,
    ) -> list[ScheduleCandidate]:
        """
        Generate candidates with random restarts.

        Each restart uses a different random seed, producing
        potentially different solutions for stochastic solvers.

        Args:
            base_params: Base parameters to use
            num_restarts: Number of restarts to try

        Returns:
            List of candidates from all restarts
        """
        import random

        candidates: list[ScheduleCandidate] = []
        base_seed = base_params.random_seed or random.randint(0, 2**32)

        for i in range(num_restarts):
            params = GeneratorParams(
                algorithm=base_params.algorithm,
                timeout_seconds=base_params.timeout_seconds / num_restarts,
                random_seed=base_seed + i,
                solver_params=base_params.solver_params,
                constraint_weights=base_params.constraint_weights,
            )
            candidate = self._generate_single(params)
            if candidate:
                candidates.append(candidate)

        return candidates

    def generate_with_perturbation(
        self,
        base_candidate: ScheduleCandidate,
        perturbation_rate: float = 0.1,
    ) -> ScheduleCandidate | None:
        """
        Generate a new candidate by perturbing an existing one.

        Randomly swaps some assignments to explore nearby solutions.
        This is useful when close to a good solution but stuck.

        Args:
            base_candidate: Candidate to perturb
            perturbation_rate: Fraction of assignments to modify

        Returns:
            Perturbed candidate or None if failed
        """
        import random

        assignments = base_candidate.assignments.copy()
        num_to_perturb = max(1, int(len(assignments) * perturbation_rate))

        # Get available persons and blocks
        residents = self._get_residents()
        blocks = self._get_blocks()

        if not residents or not blocks:
            return None

        # Randomly modify some assignments
        for _ in range(num_to_perturb):
            if not assignments:
                break

            # Pick random assignment to modify
            idx = random.randint(0, len(assignments) - 1)
            old_assignment = assignments[idx]

            # Swap person or block
            if random.random() < 0.5 and residents:
                # Swap person
                new_person = random.choice(residents)
                assignments[idx] = Assignment(
                    block_id=old_assignment.block_id,
                    person_id=new_person.id,
                    rotation_template_id=old_assignment.rotation_template_id,
                    role=old_assignment.role,
                )
            elif blocks:
                # Swap block
                new_block = random.choice(blocks)
                assignments[idx] = Assignment(
                    block_id=new_block.id,
                    person_id=old_assignment.person_id,
                    rotation_template_id=old_assignment.rotation_template_id,
                    role=old_assignment.role,
                )

        return ScheduleCandidate(
            assignments=assignments,
            algorithm=f"{base_candidate.algorithm}_perturbed",
            params=base_candidate.params,
            solver_stats={"perturbation_rate": perturbation_rate},
            generation_time=0.0,  # Perturbation is fast
            feasible=True,  # May not actually be feasible
            objective_value=None,
        )
