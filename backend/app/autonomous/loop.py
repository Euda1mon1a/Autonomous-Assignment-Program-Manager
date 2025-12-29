"""
Control Loop that Owns Decision-Making.

This is the core automation. It runs until:
    - Hard constraints are satisfied AND soft score is above threshold, OR
    - Max iterations/time budget reached

Loop outline:
    1. Propose params (initial or learned)
    2. Generate candidate schedules
    3. Evaluate each candidate
    4. Update best-so-far
    5. Decide next params/strategy based on failure modes

No LLM required to get this working.
"""

import logging
import time
from dataclasses import dataclass
from datetime import date, datetime
from enum import Enum

from sqlalchemy.orm import Session

from app.autonomous.evaluator import EvaluationResult, ScheduleEvaluator
from app.autonomous.generator import (
    CandidateGenerator,
    GeneratorConfig,
    ScheduleCandidate,
)
from app.autonomous.state import (
    GeneratorParams,
    IterationRecord,
    RunState,
    StateStore,
)
from app.resilience.service import ResilienceConfig

logger = logging.getLogger(__name__)


class StopReason(str, Enum):
    """Reasons the loop might stop."""

    TARGET_REACHED = "target_reached"
    MAX_ITERATIONS = "max_iterations"
    STAGNATION = "stagnation"
    TIME_LIMIT = "time_limit"
    USER_ABORT = "user_abort"
    ERROR = "error"
    RUNNING = "running"


@dataclass
class LoopConfig:
    """
    Configuration for the autonomous loop.

    Attributes:
        max_iterations: Maximum iterations before stopping
        target_score: Score threshold for success (0.0-1.0)
        stagnation_limit: Iterations without improvement before stopping
        time_limit_seconds: Maximum wall-clock time
        candidates_per_iteration: How many candidates to generate each iteration
        log_interval: Log progress every N iterations
        checkpoint_interval: Save state every N iterations
    """

    max_iterations: int = 200
    target_score: float = 0.95
    stagnation_limit: int = 20
    time_limit_seconds: float | None = None
    candidates_per_iteration: int = 1
    log_interval: int = 10
    checkpoint_interval: int = 5


@dataclass
class LoopResult:
    """
    Result of a completed autonomous loop run.

    Attributes:
        success: Whether target was reached
        stop_reason: Why the loop stopped
        final_score: Best score achieved
        final_iteration: Number of iterations completed
        best_candidate: Best schedule candidate found
        best_evaluation: Evaluation of best candidate
        total_time: Total wall-clock time in seconds
        run_id: Run identifier for loading state
    """

    success: bool
    stop_reason: StopReason
    final_score: float
    final_iteration: int
    best_candidate: ScheduleCandidate | None
    best_evaluation: EvaluationResult | None
    total_time: float
    run_id: str


class AutonomousLoop:
    """
    The autonomous scheduling control loop.

    This class owns the decision-making process. Python is authoritative;
    the loop runs to completion without human intervention.

    The loop:
        1. Initializes state (from scratch or resuming)
        2. Generates schedule candidates using the generator
        3. Evaluates candidates using the strict evaluator
        4. Updates best-so-far and adapts parameters
        5. Checks stopping conditions
        6. Persists state for crash recovery

    Example:
        >>> loop = AutonomousLoop.from_config(
        ...     db=db,
        ...     scenario="baseline",
        ...     start_date=date(2025, 1, 1),
        ...     end_date=date(2025, 3, 31),
        ... )
        >>> result = loop.run(max_iterations=200)
        >>> if result.success:
        ...     print(f"Found solution with score {result.final_score}")
        >>> else:
        ...     print(f"Stopped: {result.stop_reason}")
    """

    def __init__(
        self,
        db: Session,
        state: RunState,
        store: StateStore,
        generator: CandidateGenerator,
        evaluator: ScheduleEvaluator,
        config: LoopConfig,
        adapter: "ParameterAdapter | None" = None,
        advisor: "LLMAdvisor | None" = None,
    ):
        """
        Initialize the loop with all components.

        Use AutonomousLoop.from_config() for easier setup.
        """
        self.db = db
        self.state = state
        self.store = store
        self.generator = generator
        self.evaluator = evaluator
        self.config = config
        self.adapter = adapter
        self.advisor = advisor

        self._best_candidate: ScheduleCandidate | None = None
        self._best_evaluation: EvaluationResult | None = None
        self._start_time: float = 0.0
        self._abort_requested: bool = False

    @classmethod
    def from_config(
        cls,
        db: Session,
        scenario: str,
        start_date: date,
        end_date: date,
        config: LoopConfig | None = None,
        generator_config: GeneratorConfig | None = None,
        resilience_config: ResilienceConfig | None = None,
        runs_path: str = "runs",
        resume_run_id: str | None = None,
    ) -> "AutonomousLoop":
        """
        Create a loop from configuration.

        This is the recommended way to create a loop. It handles:
        - Creating or resuming state
        - Initializing all components
        - Setting up the store

        Args:
            db: Database session
            scenario: Scenario identifier
            start_date: Schedule start date
            end_date: Schedule end date
            config: Loop configuration
            generator_config: Generator configuration
            resilience_config: Resilience configuration
            runs_path: Path to store run data
            resume_run_id: Optional run ID to resume

        Returns:
            Configured AutonomousLoop
        """
        config = config or LoopConfig()
        generator_config = generator_config or GeneratorConfig()
        resilience_config = resilience_config or ResilienceConfig()

        # Create store
        store = StateStore(base_path=runs_path)

        # Create or resume state
        if resume_run_id:
            state = store.load_run(resume_run_id)
            if state is None:
                raise ValueError(f"Run {resume_run_id} not found")
            logger.info(
                f"Resuming run {resume_run_id} at iteration {state.current_iteration}"
            )
        else:
            state = store.create_run(
                scenario=scenario,
                start_date=start_date,
                end_date=end_date,
                max_iterations=config.max_iterations,
                target_score=config.target_score,
            )
            logger.info(f"Created new run {state.run_id}")

        # Create generator
        generator = CandidateGenerator(
            db=db,
            start_date=start_date,
            end_date=end_date,
            config=generator_config,
            resilience_config=resilience_config,
        )

        # Create evaluator
        evaluator = ScheduleEvaluator(
            db=db,
            resilience_config=resilience_config,
        )

        # Create adapter (lazy import to avoid circular dependency)
        from app.autonomous.adapter import ParameterAdapter
        from app.autonomous.advisor import LLMAdvisor

        adapter = ParameterAdapter()

        # Create LLM advisor (optional, airgap-compatible)
        # Only create if Ollama is available, otherwise loop runs without advisor
        try:
            advisor = LLMAdvisor(
                llm_router=None,  # Will create default Ollama router
                model="llama3.2",
                airgap_mode=True,  # Local only by default
            )
            logger.info("LLM advisor initialized with local Ollama")
        except Exception as e:
            logger.warning(f"LLM advisor unavailable: {e}")
            advisor = None

        return cls(
            db=db,
            state=state,
            store=store,
            generator=generator,
            evaluator=evaluator,
            config=config,
            adapter=adapter,
            advisor=advisor,  # LLM advisor is optional but enabled by default
        )

    def run(self) -> LoopResult:
        """
        Run the autonomous loop to completion.

        This is the main entry point. The loop runs until a stopping
        condition is met (target reached, max iterations, stagnation,
        time limit, or error).

        Returns:
            LoopResult with final state and best candidate
        """
        self._start_time = time.time()
        self.store.log(
            self.state, f"Starting loop run, target score: {self.config.target_score}"
        )

        stop_reason = StopReason.RUNNING

        try:
            while stop_reason == StopReason.RUNNING:
                # Check stopping conditions
                stop_reason = self._check_stop_conditions()
                if stop_reason != StopReason.RUNNING:
                    break

                # Run one iteration
                self._run_iteration()

                # Checkpoint periodically
                if self.state.current_iteration % self.config.checkpoint_interval == 0:
                    self._checkpoint()

                # Log progress periodically
                if self.state.current_iteration % self.config.log_interval == 0:
                    self._log_progress()

        except Exception as e:
            logger.error(f"Loop error: {e}")
            self.store.log(self.state, f"ERROR: {e}")
            stop_reason = StopReason.ERROR

        # Final save
        self.state.status = (
            "completed" if stop_reason == StopReason.TARGET_REACHED else "exhausted"
        )
        self.store.save_state(self.state)

        if self._best_candidate:
            self.store.save_schedule(
                self.state,
                self._best_candidate.assignment_dicts(),
            )
        if self._best_evaluation:
            self.store.save_report(self.state, self._best_evaluation)

        total_time = time.time() - self._start_time
        self.store.log(
            self.state,
            f"Loop completed: {stop_reason.value}, score={self.state.best_score:.4f}, "
            f"iterations={self.state.current_iteration}, time={total_time:.1f}s",
        )

        return LoopResult(
            success=stop_reason == StopReason.TARGET_REACHED,
            stop_reason=stop_reason,
            final_score=self.state.best_score,
            final_iteration=self.state.current_iteration,
            best_candidate=self._best_candidate,
            best_evaluation=self._best_evaluation,
            total_time=total_time,
            run_id=self.state.run_id,
        )

    def _run_iteration(self) -> None:
        """
        Run a single iteration of the loop.

        Steps:
            1. Get current parameters (from adapter or state)
            2. Generate candidates
            3. Evaluate each candidate
            4. Update best if improved
            5. Adapt parameters based on results
        """
        iteration_start = time.time()

        # 1. Get parameters for this iteration
        params = self._get_current_params()

        # 2. Generate candidates
        candidates = self.generator.generate_candidates(
            params=params,
            k=self.config.candidates_per_iteration,
        )

        if not candidates:
            logger.warning(
                f"Iteration {self.state.current_iteration + 1}: No candidates generated"
            )
            self.state.current_iteration += 1
            return

        # 3. Evaluate each candidate
        best_this_iteration: tuple[ScheduleCandidate, EvaluationResult] | None = None

        for candidate in candidates:
            evaluation = self.evaluator.evaluate(
                assignments=candidate.assignments,
                start_date=self.state.start_date,
                end_date=self.state.end_date,
            )

            # Track best this iteration
            if best_this_iteration is None or evaluation.is_better_than(
                best_this_iteration[1]
            ):
                best_this_iteration = (candidate, evaluation)

        if best_this_iteration is None:
            self.state.current_iteration += 1
            return

        candidate, evaluation = best_this_iteration

        # 4. Update state
        self.state.update_with_result(evaluation, params)

        # 5. Update global best if improved
        if self._best_evaluation is None or evaluation.is_better_than(
            self._best_evaluation
        ):
            self._best_candidate = candidate
            self._best_evaluation = evaluation
            logger.info(
                f"Iteration {self.state.current_iteration}: New best score "
                f"{evaluation.score:.4f} (valid={evaluation.valid})"
            )

        # 6. Record iteration in history
        iteration_time = time.time() - iteration_start
        violation_types = list({v.type for v in evaluation.violations})

        record = IterationRecord(
            iteration=self.state.current_iteration,
            timestamp=datetime.now(),
            params=params,
            score=evaluation.score,
            valid=evaluation.valid,
            critical_violations=evaluation.critical_violations,
            total_violations=evaluation.total_violations,
            violation_types=violation_types,
            duration_seconds=iteration_time,
        )
        self.store.append_iteration(self.state, record)

        # 7. Adapt parameters for next iteration
        if self.adapter:
            next_params = self.adapter.adapt(
                current_params=params,
                evaluation=evaluation,
                history=self.store.load_history(self.state.run_id)[-10:],  # Last 10
            )
            self.state.current_params = next_params

    def _get_current_params(self) -> GeneratorParams:
        """Get parameters for current iteration."""
        return self.state.current_params

    def _check_stop_conditions(self) -> StopReason:
        """Check if any stopping condition is met."""
        # Target reached
        if self.state.best_score >= self.config.target_score:
            return StopReason.TARGET_REACHED

        # Max iterations
        if self.state.current_iteration >= self.config.max_iterations:
            return StopReason.MAX_ITERATIONS

        # Stagnation
        if self.state.iterations_since_improvement >= self.config.stagnation_limit:
            return StopReason.STAGNATION

        # Time limit
        if self.config.time_limit_seconds:
            elapsed = time.time() - self._start_time
            if elapsed >= self.config.time_limit_seconds:
                return StopReason.TIME_LIMIT

        # User abort
        if self._abort_requested:
            return StopReason.USER_ABORT

        return StopReason.RUNNING

    def _checkpoint(self) -> None:
        """Save current state as checkpoint."""
        self.store.save_state(self.state)

    def _log_progress(self) -> None:
        """Log progress summary."""
        elapsed = time.time() - self._start_time
        iters_per_sec = self.state.current_iteration / elapsed if elapsed > 0 else 0

        logger.info(
            f"Progress: iter={self.state.current_iteration}/{self.config.max_iterations}, "
            f"best={self.state.best_score:.4f}, "
            f"since_improvement={self.state.iterations_since_improvement}, "
            f"elapsed={elapsed:.1f}s ({iters_per_sec:.2f} iter/s)"
        )

        self.store.log(
            self.state,
            f"Progress: iter={self.state.current_iteration}, best={self.state.best_score:.4f}",
        )

    def abort(self) -> None:
        """Request loop abort (will stop after current iteration)."""
        self._abort_requested = True


class AutonomousLoopWithAdvisor(AutonomousLoop):
    """
    Extended loop that incorporates LLM advisory suggestions.

    The LLM advisor is optional and advisory only. The Python loop:
    - Validates LLM suggestions against a schema
    - Rejects them if unsafe or nonsensical
    - Can continue without them

    The LLM helps by suggesting:
    - Which failure mode is most important
    - Plausible parameter deltas
    - New neighborhood moves or repair operators
    - Explanations for reports
    """

    async def _run_iteration_async(self) -> None:
        """Run iteration with optional LLM advisory input (async version)."""
        # First, try to get LLM suggestion if advisor is configured
        llm_suggestion = None
        if self.advisor:
            try:
                llm_suggestion = await self.advisor.suggest(
                    state=self.state,
                    last_evaluation=self._best_evaluation,
                    history=self.store.load_history(self.state.run_id)[-5:],
                )
                if llm_suggestion and not self.advisor.validate_suggestion(
                    llm_suggestion
                ):
                    logger.warning("LLM suggestion rejected by validator")
                    llm_suggestion = None
            except Exception as e:
                logger.warning(f"LLM advisor error (continuing without): {e}")
                llm_suggestion = None

        # If LLM suggested parameters, use them
        if llm_suggestion and llm_suggestion.params:
            self.state.current_params = llm_suggestion.params
            logger.info(
                f"Applying LLM suggestion: {llm_suggestion.type.value} "
                f"(confidence={llm_suggestion.confidence:.2f})"
            )
            logger.debug(f"LLM reasoning: {llm_suggestion.reasoning}")

        # Run standard iteration
        super()._run_iteration()

        # Log LLM usage if any
        if llm_suggestion:
            self.store.log(
                self.state,
                f"LLM suggestion applied: {llm_suggestion.type.value} - {llm_suggestion.reasoning}",
            )

    def _run_iteration(self) -> None:
        """
        Run iteration with optional LLM advisory input.

        Note: This wraps the async version for compatibility with the base loop.
        In production, consider making the entire loop async.
        """
        import asyncio

        # Check if we're already in an event loop
        try:
            loop = asyncio.get_running_loop()
            # If we're already in a loop, run the async version directly
            # This requires the caller to use asyncio.run() or similar
            logger.warning(
                "Running async iteration in existing event loop - "
                "consider making the entire loop async"
            )
            # Create a task and wait for it
            task = loop.create_task(self._run_iteration_async())
            # This is a bit hacky but works for now
            loop.run_until_complete(task)
        except RuntimeError:
            # No event loop running, create one
            asyncio.run(self._run_iteration_async())
