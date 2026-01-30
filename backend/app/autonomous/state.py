"""
Run State Store for Iteration Persistence.

You need persistence across iterations so the system can:
    - Remember which parameter sets it tried
    - Remember which fixes worked
    - Resume after crash

Minimal structure: a folder per run with:
    - state.json (iteration, params, best-so-far, RNG seed, timestamps)
    - history.ndjson (one line per attempt: params + score + violations summary)
"""

import json
from dataclasses import asdict, dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

from app.autonomous.evaluator import EvaluationResult


def _json_serializer(obj: Any) -> Any:
    """Custom JSON serializer for special types."""
    if isinstance(obj, UUID):
        return str(obj)
    if isinstance(obj, datetime):
        return obj.isoformat()
    if isinstance(obj, date):
        return obj.isoformat()
    if hasattr(obj, "to_dict"):
        return obj.to_dict()
    if hasattr(obj, "__dict__"):
        return obj.__dict__
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")


@dataclass
class GeneratorParams:
    """
    Parameters that control schedule generation.

    These are the knobs the control loop can turn to improve results.
    """

    algorithm: str = "greedy"
    timeout_seconds: float = 60.0
    random_seed: int | None = None

    # Solver-specific parameters
    solver_params: dict[str, Any] = field(default_factory=dict)

    # Constraint weights (can be adjusted to change priorities)
    constraint_weights: dict[str, float] = field(default_factory=dict)

    # Search parameters
    max_restarts: int = 1
    neighborhood_size: int = 10
    diversification_factor: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "GeneratorParams":
        """Create from dictionary."""
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class IterationRecord:
    """
    Record of a single iteration attempt.

    Stored as one line in history.ndjson for efficient append-only logging.
    """

    iteration: int
    timestamp: datetime
    params: GeneratorParams
    score: float
    valid: bool
    critical_violations: int
    total_violations: int
    violation_types: list[str]
    duration_seconds: float
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "iteration": self.iteration,
            "timestamp": self.timestamp.isoformat(),
            "params": self.params.to_dict(),
            "score": self.score,
            "valid": self.valid,
            "critical_violations": self.critical_violations,
            "total_violations": self.total_violations,
            "violation_types": self.violation_types,
            "duration_seconds": self.duration_seconds,
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "IterationRecord":
        """Create from dictionary."""
        return cls(
            iteration=data["iteration"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            params=GeneratorParams.from_dict(data["params"]),
            score=data["score"],
            valid=data["valid"],
            critical_violations=data["critical_violations"],
            total_violations=data["total_violations"],
            violation_types=data.get("violation_types", []),
            duration_seconds=data["duration_seconds"],
            notes=data.get("notes", ""),
        )

    def to_ndjson_line(self) -> str:
        """Convert to NDJSON line (no trailing newline)."""
        return json.dumps(self.to_dict(), default=_json_serializer)


@dataclass
class RunState:
    """
    Complete state of an autonomous run.

    Persisted as state.json in the run directory.
    Enables resumption after crash.
    """

    run_id: str
    scenario: str
    start_date: date
    end_date: date
    created_at: datetime
    updated_at: datetime

    # Iteration tracking
    current_iteration: int = 0
    max_iterations: int = 200
    status: str = "running"  # running, completed, failed, exhausted

    # Best result tracking
    best_score: float = 0.0
    best_iteration: int = 0
    best_params: GeneratorParams | None = None

    # Stopping conditions
    target_score: float = 0.95
    stagnation_limit: int = 20
    iterations_since_improvement: int = 0

    # RNG state for reproducibility
    rng_seed: int = 42

    # Current parameters
    current_params: GeneratorParams = field(default_factory=GeneratorParams)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "run_id": self.run_id,
            "scenario": self.scenario,
            "start_date": self.start_date.isoformat(),
            "end_date": self.end_date.isoformat(),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "current_iteration": self.current_iteration,
            "max_iterations": self.max_iterations,
            "status": self.status,
            "best_score": self.best_score,
            "best_iteration": self.best_iteration,
            "best_params": self.best_params.to_dict() if self.best_params else None,
            "target_score": self.target_score,
            "stagnation_limit": self.stagnation_limit,
            "iterations_since_improvement": self.iterations_since_improvement,
            "rng_seed": self.rng_seed,
            "current_params": self.current_params.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RunState":
        """Create from dictionary."""
        return cls(
            run_id=data["run_id"],
            scenario=data["scenario"],
            start_date=date.fromisoformat(data["start_date"]),
            end_date=date.fromisoformat(data["end_date"]),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            current_iteration=data["current_iteration"],
            max_iterations=data["max_iterations"],
            status=data["status"],
            best_score=data["best_score"],
            best_iteration=data["best_iteration"],
            best_params=(
                GeneratorParams.from_dict(data["best_params"])
                if data.get("best_params")
                else None
            ),
            target_score=data["target_score"],
            stagnation_limit=data["stagnation_limit"],
            iterations_since_improvement=data["iterations_since_improvement"],
            rng_seed=data["rng_seed"],
            current_params=GeneratorParams.from_dict(data.get("current_params", {})),
        )

    def update_with_result(
        self,
        result: EvaluationResult,
        params: GeneratorParams,
    ) -> None:
        """
        Update state with evaluation result.

        Args:
            result: Evaluation result from this iteration
            params: Parameters used for this iteration
        """
        self.current_iteration += 1
        self.updated_at = datetime.now()
        self.current_params = params

        if result.score > self.best_score:
            self.best_score = result.score
            self.best_iteration = self.current_iteration
            self.best_params = params
            self.iterations_since_improvement = 0
        else:
            self.iterations_since_improvement += 1

    def should_stop(self) -> tuple[bool, str]:
        """
        Check if the loop should stop.

        Returns:
            Tuple of (should_stop, reason)
        """
        if self.best_score >= self.target_score:
            return True, "target_reached"
        if self.current_iteration >= self.max_iterations:
            return True, "max_iterations"
        if self.iterations_since_improvement >= self.stagnation_limit:
            return True, "stagnation"
        return False, ""


class StateStore:
    """
    Persistent state storage for autonomous runs.

    Directory structure:
        runs/
            {run_id}/
                state.json       # Current state
                history.ndjson   # Iteration history (append-only)
                schedule.json    # Best schedule assignments
                report.json      # Best evaluation report
                run.log          # Execution trace
    """

    def __init__(self, base_path: str | Path = "runs") -> None:
        """
        Initialize state store.

        Args:
            base_path: Base directory for storing runs
        """
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    def create_run(
        self,
        scenario: str,
        start_date: date,
        end_date: date,
        max_iterations: int = 200,
        target_score: float = 0.95,
        rng_seed: int = 42,
    ) -> RunState:
        """
        Create a new run and initialize its state.

        Args:
            scenario: Scenario identifier (e.g., "baseline", "n1_test")
            start_date: Schedule start date
            end_date: Schedule end date
            max_iterations: Maximum iterations before stopping
            target_score: Score threshold for success
            rng_seed: Random seed for reproducibility

        Returns:
            Initialized RunState
        """
        run_id = (
            f"{scenario}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid4().hex[:8]}"
        )
        now = datetime.now()

        state = RunState(
            run_id=run_id,
            scenario=scenario,
            start_date=start_date,
            end_date=end_date,
            created_at=now,
            updated_at=now,
            max_iterations=max_iterations,
            target_score=target_score,
            rng_seed=rng_seed,
        )

        # Create run directory
        run_dir = self.base_path / run_id
        run_dir.mkdir(parents=True, exist_ok=True)

        # Save initial state
        self.save_state(state)

        # Initialize empty history file
        history_path = run_dir / "history.ndjson"
        history_path.touch()

        return state

    def load_run(self, run_id: str) -> RunState | None:
        """
        Load an existing run state.

        Args:
            run_id: Run identifier

        Returns:
            RunState if found, None otherwise
        """
        state_path = self.base_path / run_id / "state.json"
        if not state_path.exists():
            return None

        with open(state_path) as f:
            data = json.load(f)

        return RunState.from_dict(data)

    def save_state(self, state: RunState) -> None:
        """
        Save current run state.

        Args:
            state: RunState to save
        """
        run_dir = self.base_path / state.run_id
        run_dir.mkdir(parents=True, exist_ok=True)

        state_path = run_dir / "state.json"
        with open(state_path, "w") as f:
            json.dump(state.to_dict(), f, indent=2, default=_json_serializer)

    def append_iteration(
        self,
        state: RunState,
        record: IterationRecord,
    ) -> None:
        """
        Append iteration record to history.

        Uses NDJSON format for efficient append-only logging.

        Args:
            state: Current run state
            record: Iteration record to append
        """
        history_path = self.base_path / state.run_id / "history.ndjson"
        with open(history_path, "a") as f:
            f.write(record.to_ndjson_line() + "\n")

    def load_history(self, run_id: str) -> list[IterationRecord]:
        """
        Load full iteration history.

        Args:
            run_id: Run identifier

        Returns:
            List of iteration records
        """
        history_path = self.base_path / run_id / "history.ndjson"
        if not history_path.exists():
            return []

        records = []
        with open(history_path) as f:
            for line in f:
                line = line.strip()
                if line:
                    data = json.loads(line)
                    records.append(IterationRecord.from_dict(data))

        return records

    def save_schedule(
        self,
        state: RunState,
        assignments: list[dict[str, Any]],
    ) -> None:
        """
        Save best schedule as JSON.

        Args:
            state: Current run state
            assignments: List of assignment dictionaries
        """
        schedule_path = self.base_path / state.run_id / "schedule.json"
        with open(schedule_path, "w") as f:
            json.dump(assignments, f, indent=2, default=_json_serializer)

    def save_report(
        self,
        state: RunState,
        result: EvaluationResult,
    ) -> None:
        """
        Save evaluation report as JSON.

        Args:
            state: Current run state
            result: Evaluation result to save
        """
        report_path = self.base_path / state.run_id / "report.json"
        with open(report_path, "w") as f:
            json.dump(result.to_dict(), f, indent=2, default=_json_serializer)

    def log(self, state: RunState, message: str) -> None:
        """
        Append to run log.

        Args:
            state: Current run state
            message: Message to log
        """
        log_path = self.base_path / state.run_id / "run.log"
        timestamp = datetime.now().isoformat()
        with open(log_path, "a") as f:
            f.write(f"[{timestamp}] {message}\n")

    def list_runs(self, scenario: str | None = None) -> list[str]:
        """
        List all run IDs, optionally filtered by scenario.

        Args:
            scenario: Optional scenario filter

        Returns:
            List of run IDs
        """
        runs = []
        for run_dir in self.base_path.iterdir():
            if run_dir.is_dir() and (run_dir / "state.json").exists():
                if scenario is None or run_dir.name.startswith(scenario):
                    runs.append(run_dir.name)
        return sorted(runs)

    def get_best_from_history(self, run_id: str) -> IterationRecord | None:
        """
        Get the best iteration from history.

        Args:
            run_id: Run identifier

        Returns:
            Best iteration record or None
        """
        records = self.load_history(run_id)
        if not records:
            return None

            # Sort by score descending, then by valid flag
        valid_records = [r for r in records if r.valid]
        if valid_records:
            return max(valid_records, key=lambda r: r.score)

            # If no valid records, return highest scoring invalid one
        return max(records, key=lambda r: r.score)

    def get_run_summary(self, run_id: str) -> dict[str, Any] | None:
        """
        Get summary of a run for reporting.

        Args:
            run_id: Run identifier

        Returns:
            Summary dictionary or None
        """
        state = self.load_run(run_id)
        if not state:
            return None

        history = self.load_history(run_id)

        return {
            "run_id": run_id,
            "scenario": state.scenario,
            "status": state.status,
            "total_iterations": state.current_iteration,
            "best_score": state.best_score,
            "best_iteration": state.best_iteration,
            "created_at": state.created_at.isoformat(),
            "updated_at": state.updated_at.isoformat(),
            "history_count": len(history),
            "valid_count": sum(1 for r in history if r.valid),
        }
