"""Type definitions for saga orchestration."""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Awaitable, Callable
from uuid import UUID


class SagaStatus(str, Enum):
    """Status of a saga execution."""
    PENDING = "pending"  # Saga created but not started
    RUNNING = "running"  # Saga currently executing
    COMPENSATING = "compensating"  # Rolling back completed steps
    COMPLETED = "completed"  # All steps completed successfully
    FAILED = "failed"  # Saga failed and compensations completed
    TIMEOUT = "timeout"  # Saga timed out
    CANCELLED = "cancelled"  # Saga manually cancelled


class StepStatus(str, Enum):
    """Status of a saga step execution."""
    PENDING = "pending"  # Step not yet started
    RUNNING = "running"  # Step currently executing
    COMPLETED = "completed"  # Step completed successfully
    FAILED = "failed"  # Step failed
    COMPENSATING = "compensating"  # Compensation in progress
    COMPENSATED = "compensated"  # Compensation completed


class StepType(str, Enum):
    """Type of saga step execution."""
    SEQUENTIAL = "sequential"  # Execute one at a time
    PARALLEL = "parallel"  # Execute concurrently


# Type aliases for step functions
StepFunction = Callable[[dict[str, Any]], Awaitable[dict[str, Any]]]
CompensationFunction = Callable[[dict[str, Any]], Awaitable[None]]


@dataclass
class SagaStepDefinition:
    """Definition of a step in a saga.

    Attributes:
        name: Unique name for the step
        action: Async function to execute for this step
        compensation: Async function to compensate/rollback this step
        timeout_seconds: Maximum time allowed for step execution
        retry_attempts: Number of retry attempts on failure (0 = no retry)
        retry_delay_seconds: Delay between retry attempts
        idempotent: Whether the step can be safely retried
        parallel_group: Group name for parallel execution (None = sequential)
    """
    name: str
    action: StepFunction
    compensation: CompensationFunction | None = None
    timeout_seconds: int = 300  # 5 minutes default
    retry_attempts: int = 0
    retry_delay_seconds: int = 5
    idempotent: bool = True
    parallel_group: str | None = None

    def __post_init__(self):
        """Validate step definition."""
        if self.timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
        if self.retry_attempts < 0:
            raise ValueError("retry_attempts cannot be negative")
        if self.retry_delay_seconds < 0:
            raise ValueError("retry_delay_seconds cannot be negative")


@dataclass
class SagaDefinition:
    """Complete definition of a saga.

    Attributes:
        name: Unique name for the saga type
        steps: Ordered list of steps to execute
        timeout_seconds: Maximum time allowed for entire saga
        description: Human-readable description
        version: Saga definition version (for compatibility)
    """
    name: str
    steps: list[SagaStepDefinition]
    timeout_seconds: int = 3600  # 1 hour default
    description: str = ""
    version: str = "1.0"

    def __post_init__(self):
        """Validate saga definition."""
        if not self.steps:
            raise ValueError("Saga must have at least one step")
        if self.timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")

        # Check for duplicate step names
        step_names = [step.name for step in self.steps]
        if len(step_names) != len(set(step_names)):
            raise ValueError("Step names must be unique")

        # Validate parallel groups
        parallel_groups: dict[str, list[SagaStepDefinition]] = {}
        for step in self.steps:
            if step.parallel_group:
                if step.parallel_group not in parallel_groups:
                    parallel_groups[step.parallel_group] = []
                parallel_groups[step.parallel_group].append(step)

        # All steps in a parallel group should be consecutive
        for group_name, group_steps in parallel_groups.items():
            indices = [self.steps.index(step) for step in group_steps]
            if indices != list(range(min(indices), max(indices) + 1)):
                raise ValueError(
                    f"Parallel group '{group_name}' steps must be consecutive"
                )


@dataclass
class SagaStepResult:
    """Result of executing a saga step.

    Attributes:
        step_name: Name of the executed step
        status: Final status of the step
        output_data: Data returned by the step action
        error_message: Error message if step failed
        started_at: When step execution started
        completed_at: When step execution completed
        retry_count: Number of times step was retried
    """
    step_name: str
    status: StepStatus
    output_data: dict[str, Any] = field(default_factory=dict)
    error_message: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    retry_count: int = 0


@dataclass
class SagaExecutionResult:
    """Result of executing a complete saga.

    Attributes:
        saga_id: UUID of the saga execution
        status: Final status of the saga
        step_results: Results from each step execution
        started_at: When saga execution started
        completed_at: When saga execution completed
        compensated_steps: Number of steps that were compensated
        error_message: Error message if saga failed
    """
    saga_id: UUID
    status: SagaStatus
    step_results: list[SagaStepResult] = field(default_factory=list)
    started_at: datetime | None = None
    completed_at: datetime | None = None
    compensated_steps: int = 0
    error_message: str | None = None

    @property
    def duration_seconds(self) -> float | None:
        """Calculate total execution duration."""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None

    @property
    def is_successful(self) -> bool:
        """Check if saga completed successfully."""
        return self.status == SagaStatus.COMPLETED

    @property
    def is_terminal(self) -> bool:
        """Check if saga is in a terminal state."""
        return self.status in (
            SagaStatus.COMPLETED,
            SagaStatus.FAILED,
            SagaStatus.TIMEOUT,
            SagaStatus.CANCELLED
        )


@dataclass
class SagaContext:
    """Runtime context for saga execution.

    This context is passed between steps and accumulates data.

    Attributes:
        saga_id: UUID of the saga execution
        input_data: Initial input data for the saga
        accumulated_data: Data accumulated from step outputs
        metadata: Additional metadata (user_id, trace_id, etc.)
    """
    saga_id: UUID
    input_data: dict[str, Any]
    accumulated_data: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def merge_step_output(self, step_name: str, output: dict[str, Any]) -> None:
        """Merge step output into accumulated data.

        Args:
            step_name: Name of the step that produced the output
            output: Output data from the step
        """
        self.accumulated_data[step_name] = output

    def get_step_output(self, step_name: str) -> dict[str, Any]:
        """Get output from a previous step.

        Args:
            step_name: Name of the step

        Returns:
            Output data from the step, or empty dict if not found
        """
        return self.accumulated_data.get(step_name, {})

    def to_dict(self) -> dict[str, Any]:
        """Convert context to dictionary for persistence."""
        return {
            "saga_id": str(self.saga_id),
            "input_data": self.input_data,
            "accumulated_data": self.accumulated_data,
            "metadata": self.metadata,
        }
