"""Saga orchestrator for managing distributed transactions.

This module provides the core saga orchestration logic including:
- Step execution with retry logic
- Parallel step execution
- Compensation rollback on failure
- Timeout handling
- State persistence for recovery
- Event logging and monitoring
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.exceptions import AppException
from app.saga.models import SagaEvent, SagaExecution, SagaStepExecution
from app.saga.types import (
    SagaContext,
    SagaDefinition,
    SagaExecutionResult,
    SagaStatus,
    SagaStepDefinition,
    SagaStepResult,
    StepStatus,
)

logger = logging.getLogger(__name__)


class SagaTimeoutError(AppException):
    """Raised when saga or step exceeds timeout."""

    def __init__(self, message: str):
        super().__init__(message, status_code=408)


class SagaCompensationError(AppException):
    """Raised when saga compensation fails."""

    def __init__(self, message: str):
        super().__init__(message, status_code=500)


class SagaOrchestrator:
    """Orchestrator for executing sagas with state persistence and recovery.

    The orchestrator handles:
    1. Sequential and parallel step execution
    2. Automatic retry with exponential backoff
    3. Compensation on failure (rollback)
    4. Timeout enforcement at saga and step level
    5. State persistence for crash recovery
    6. Event logging for monitoring
    """

    def __init__(self, db: Session):
        """Initialize saga orchestrator.

        Args:
            db: Database session for state persistence
        """
        self.db = db
        self._registered_sagas: dict[str, SagaDefinition] = {}

    def register_saga(self, definition: SagaDefinition) -> None:
        """Register a saga definition.

        Args:
            definition: Saga definition to register

        Raises:
            ValueError: If saga name already registered
        """
        if definition.name in self._registered_sagas:
            raise ValueError(f"Saga '{definition.name}' already registered")

        logger.info(
            f"Registering saga '{definition.name}' with {len(definition.steps)} steps"
        )
        self._registered_sagas[definition.name] = definition

    def get_saga_definition(self, saga_name: str) -> SagaDefinition:
        """Get registered saga definition.

        Args:
            saga_name: Name of the saga

        Returns:
            Saga definition

        Raises:
            ValueError: If saga not registered
        """
        if saga_name not in self._registered_sagas:
            raise ValueError(f"Saga '{saga_name}' not registered")
        return self._registered_sagas[saga_name]

    async def execute_saga(
        self,
        saga_name: str,
        input_data: dict[str, Any],
        metadata: dict[str, Any] | None = None,
        saga_id: UUID | None = None,
    ) -> SagaExecutionResult:
        """Execute a saga from start to finish.

        Args:
            saga_name: Name of the registered saga to execute
            input_data: Input data for the saga
            metadata: Optional metadata (user_id, trace_id, etc.)
            saga_id: Optional saga ID (for recovery)

        Returns:
            Saga execution result

        Raises:
            ValueError: If saga not registered
            SagaTimeoutError: If saga exceeds timeout
        """
        definition = self.get_saga_definition(saga_name)
        metadata = metadata or {}

        # Create or recover saga execution
        if saga_id:
            saga_exec = await self._recover_saga(saga_id)
            if not saga_exec:
                raise ValueError(f"Saga {saga_id} not found for recovery")
            context = SagaContext(
                saga_id=saga_exec.id,
                input_data=saga_exec.input_data,
                accumulated_data=saga_exec.context_data or {},
                metadata=saga_exec.metadata or {},
            )
        else:
            saga_id = uuid4()
            context = SagaContext(
                saga_id=saga_id,
                input_data=input_data,
                metadata=metadata,
            )
            saga_exec = await self._create_saga_execution(definition, context)

        await self._log_event(
            saga_exec.id,
            "saga_started",
            {"saga_name": saga_name, "input_size": len(str(input_data))},
            f"Started saga '{saga_name}'",
        )

        try:
            # Execute saga with timeout
            result = await asyncio.wait_for(
                self._execute_saga_steps(definition, context, saga_exec),
                timeout=definition.timeout_seconds,
            )

            # Mark saga as completed
            saga_exec.status = result.status.value
            saga_exec.completed_at = datetime.utcnow()
            saga_exec.error_message = result.error_message
            saga_exec.compensated_steps_count = result.compensated_steps
            saga_exec.context_data = context.accumulated_data
            self.db.commit()

            await self._log_event(
                saga_exec.id,
                "saga_completed",
                {"status": result.status.value, "duration": result.duration_seconds},
                f"Saga completed with status: {result.status.value}",
            )

            return result

        except TimeoutError:
            # Handle saga timeout
            logger.error(
                f"Saga {saga_id} timed out after {definition.timeout_seconds}s"
            )
            saga_exec.status = SagaStatus.TIMEOUT.value
            saga_exec.completed_at = datetime.utcnow()
            saga_exec.error_message = (
                f"Saga timed out after {definition.timeout_seconds}s"
            )
            self.db.commit()

            await self._log_event(
                saga_exec.id,
                "saga_timeout",
                {"timeout_seconds": definition.timeout_seconds},
                "Saga timed out",
            )

            # Trigger compensation for completed steps
            await self._compensate_saga(definition, context, saga_exec)

            raise SagaTimeoutError(
                f"Saga '{saga_name}' timed out after {definition.timeout_seconds}s"
            )

        except Exception as e:
            # Handle unexpected errors
            logger.exception(f"Unexpected error in saga {saga_id}")
            saga_exec.status = SagaStatus.FAILED.value
            saga_exec.completed_at = datetime.utcnow()
            saga_exec.error_message = str(e)
            self.db.commit()

            await self._log_event(
                saga_exec.id,
                "saga_error",
                {"error": str(e)},
                f"Saga failed with error: {str(e)}",
            )

            raise

    async def _execute_saga_steps(
        self,
        definition: SagaDefinition,
        context: SagaContext,
        saga_exec: SagaExecution,
    ) -> SagaExecutionResult:
        """Execute all steps in the saga.

        Args:
            definition: Saga definition
            context: Saga execution context
            saga_exec: Persisted saga execution

        Returns:
            Saga execution result
        """
        result = SagaExecutionResult(
            saga_id=context.saga_id,
            status=SagaStatus.RUNNING,
            started_at=datetime.utcnow(),
        )

        # Mark saga as running
        saga_exec.status = SagaStatus.RUNNING.value
        saga_exec.started_at = result.started_at
        self.db.commit()

        # Group steps by parallel execution
        step_groups = self._group_steps_for_execution(definition.steps)

        try:
            for group in step_groups:
                if len(group) == 1:
                    # Sequential execution
                    step_result = await self._execute_step(group[0], context, saga_exec)
                    result.step_results.append(step_result)

                    if step_result.status == StepStatus.FAILED:
                        raise RuntimeError(
                            f"Step '{step_result.step_name}' failed: "
                            f"{step_result.error_message}"
                        )
                else:
                    # Parallel execution
                    step_results = await self._execute_parallel_steps(
                        group, context, saga_exec
                    )
                    result.step_results.extend(step_results)

                    # Check for failures
                    failed_steps = [
                        r for r in step_results if r.status == StepStatus.FAILED
                    ]
                    if failed_steps:
                        failures = ", ".join(s.step_name for s in failed_steps)
                        raise RuntimeError(f"Parallel steps failed: {failures}")

            # All steps completed successfully
            result.status = SagaStatus.COMPLETED
            result.completed_at = datetime.utcnow()
            return result

        except Exception as e:
            # Saga failed, trigger compensation
            logger.error(f"Saga {context.saga_id} failed: {e}")
            result.status = SagaStatus.FAILED
            result.completed_at = datetime.utcnow()
            result.error_message = str(e)

            # Compensate completed steps
            compensated = await self._compensate_saga(definition, context, saga_exec)
            result.compensated_steps = compensated

            return result

    def _group_steps_for_execution(
        self, steps: list[SagaStepDefinition]
    ) -> list[list[SagaStepDefinition]]:
        """Group steps for sequential or parallel execution.

        Args:
            steps: List of step definitions

        Returns:
            List of step groups (each group executes in parallel)
        """
        groups: list[list[SagaStepDefinition]] = []
        current_group: list[SagaStepDefinition] = []
        current_parallel_group: str | None = None

        for step in steps:
            if step.parallel_group:
                if step.parallel_group != current_parallel_group:
                    # Start new parallel group
                    if current_group:
                        groups.append(current_group)
                    current_group = [step]
                    current_parallel_group = step.parallel_group
                else:
                    # Continue current parallel group
                    current_group.append(step)
            else:
                # Sequential step
                if current_group:
                    groups.append(current_group)
                groups.append([step])
                current_group = []
                current_parallel_group = None

        # Add final group if exists
        if current_group:
            groups.append(current_group)

        return groups

    async def _execute_step(
        self,
        step_def: SagaStepDefinition,
        context: SagaContext,
        saga_exec: SagaExecution,
    ) -> SagaStepResult:
        """Execute a single saga step with retry logic.

        Args:
            step_def: Step definition
            context: Saga execution context
            saga_exec: Persisted saga execution

        Returns:
            Step execution result
        """
        # Get or create step execution record
        step_exec = await self._get_or_create_step_execution(
            saga_exec, step_def, context
        )

        result = SagaStepResult(
            step_name=step_def.name,
            status=StepStatus.RUNNING,
            started_at=datetime.utcnow(),
        )

        # Mark step as running
        step_exec.status = StepStatus.RUNNING.value
        step_exec.started_at = result.started_at
        self.db.commit()

        await self._log_event(
            saga_exec.id,
            "step_started",
            {"step_name": step_def.name},
            f"Started step '{step_def.name}'",
            step_id=step_exec.id,
        )

        # Prepare input data (merge context)
        step_input = {
            **context.input_data,
            **context.accumulated_data,
        }

        attempt = step_exec.retry_count
        max_attempts = step_def.retry_attempts + 1

        while attempt < max_attempts:
            try:
                # Execute step with timeout
                output = await asyncio.wait_for(
                    step_def.action(step_input), timeout=step_def.timeout_seconds
                )

                # Step succeeded
                result.status = StepStatus.COMPLETED
                result.output_data = output
                result.completed_at = datetime.utcnow()
                result.retry_count = attempt

                # Update persistence
                step_exec.status = StepStatus.COMPLETED.value
                step_exec.output_data = output
                step_exec.completed_at = result.completed_at
                step_exec.retry_count = attempt
                self.db.commit()

                # Merge output into context
                context.merge_step_output(step_def.name, output)

                await self._log_event(
                    saga_exec.id,
                    "step_completed",
                    {
                        "step_name": step_def.name,
                        "duration": result.completed_at.timestamp()
                        - result.started_at.timestamp(),
                        "retries": attempt,
                    },
                    f"Step '{step_def.name}' completed",
                    step_id=step_exec.id,
                )

                return result

            except TimeoutError:
                error_msg = f"Step timed out after {step_def.timeout_seconds}s"
                logger.error(f"Step {step_def.name} timed out (attempt {attempt + 1})")

                await self._log_event(
                    saga_exec.id,
                    "step_timeout",
                    {"step_name": step_def.name, "attempt": attempt + 1},
                    error_msg,
                    step_id=step_exec.id,
                )

                if attempt < max_attempts - 1:
                    # Retry
                    attempt += 1
                    await asyncio.sleep(step_def.retry_delay_seconds)
                else:
                    # Final failure
                    result.status = StepStatus.FAILED
                    result.error_message = error_msg
                    result.completed_at = datetime.utcnow()
                    result.retry_count = attempt

                    step_exec.status = StepStatus.FAILED.value
                    step_exec.error_message = error_msg
                    step_exec.completed_at = result.completed_at
                    step_exec.retry_count = attempt
                    self.db.commit()

                    return result

            except Exception as e:
                error_msg = str(e)
                logger.error(
                    f"Step {step_def.name} failed (attempt {attempt + 1}): {e}",
                    exc_info=True,
                )

                await self._log_event(
                    saga_exec.id,
                    "step_error",
                    {
                        "step_name": step_def.name,
                        "attempt": attempt + 1,
                        "error": error_msg,
                    },
                    f"Step error: {error_msg}",
                    step_id=step_exec.id,
                )

                if attempt < max_attempts - 1 and step_def.idempotent:
                    # Retry for idempotent steps
                    attempt += 1
                    await asyncio.sleep(step_def.retry_delay_seconds)
                else:
                    # Final failure
                    result.status = StepStatus.FAILED
                    result.error_message = error_msg
                    result.completed_at = datetime.utcnow()
                    result.retry_count = attempt

                    step_exec.status = StepStatus.FAILED.value
                    step_exec.error_message = error_msg
                    step_exec.completed_at = result.completed_at
                    step_exec.retry_count = attempt
                    self.db.commit()

                    return result

        # Should not reach here
        return result

    async def _execute_parallel_steps(
        self,
        steps: list[SagaStepDefinition],
        context: SagaContext,
        saga_exec: SagaExecution,
    ) -> list[SagaStepResult]:
        """Execute multiple steps in parallel.

        Args:
            steps: List of steps to execute concurrently
            context: Saga execution context
            saga_exec: Persisted saga execution

        Returns:
            List of step results
        """
        logger.info(f"Executing {len(steps)} steps in parallel")

        await self._log_event(
            saga_exec.id,
            "parallel_execution_started",
            {"step_count": len(steps), "steps": [s.name for s in steps]},
            f"Starting parallel execution of {len(steps)} steps",
        )

        # Execute all steps concurrently
        tasks = [self._execute_step(step, context, saga_exec) for step in steps]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Convert exceptions to failed results
        final_results: list[SagaStepResult] = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                final_results.append(
                    SagaStepResult(
                        step_name=steps[i].name,
                        status=StepStatus.FAILED,
                        error_message=str(result),
                        completed_at=datetime.utcnow(),
                    )
                )
            else:
                final_results.append(result)

        await self._log_event(
            saga_exec.id,
            "parallel_execution_completed",
            {
                "step_count": len(steps),
                "succeeded": sum(
                    1 for r in final_results if r.status == StepStatus.COMPLETED
                ),
                "failed": sum(
                    1 for r in final_results if r.status == StepStatus.FAILED
                ),
            },
            "Parallel execution completed",
        )

        return final_results

    async def _compensate_saga(
        self,
        definition: SagaDefinition,
        context: SagaContext,
        saga_exec: SagaExecution,
    ) -> int:
        """Compensate (rollback) completed steps in reverse order.

        Args:
            definition: Saga definition
            context: Saga execution context
            saga_exec: Persisted saga execution

        Returns:
            Number of steps compensated
        """
        logger.info(f"Starting compensation for saga {context.saga_id}")

        saga_exec.status = SagaStatus.COMPENSATING.value
        self.db.commit()

        await self._log_event(
            saga_exec.id, "compensation_started", {}, "Starting saga compensation"
        )

        # Get completed steps in reverse order
        completed_steps = [
            s for s in saga_exec.steps if s.status == StepStatus.COMPLETED.value
        ]
        completed_steps.reverse()

        compensated_count = 0
        compensation_errors: list[str] = []

        for step_exec in completed_steps:
            # Find step definition
            step_def = next(
                (s for s in definition.steps if s.name == step_exec.step_name), None
            )

            if not step_def or not step_def.compensation:
                logger.warning(
                    f"No compensation defined for step '{step_exec.step_name}'"
                )
                continue

            try:
                # Mark as compensating
                step_exec.status = StepStatus.COMPENSATING.value
                self.db.commit()

                await self._log_event(
                    saga_exec.id,
                    "step_compensating",
                    {"step_name": step_exec.step_name},
                    f"Compensating step '{step_exec.step_name}'",
                    step_id=step_exec.id,
                )

                # Execute compensation
                compensation_input = {
                    **context.input_data,
                    **context.accumulated_data,
                    "step_output": step_exec.output_data,
                }

                await asyncio.wait_for(
                    step_def.compensation(compensation_input),
                    timeout=step_def.timeout_seconds,
                )

                # Mark as compensated
                step_exec.status = StepStatus.COMPENSATED.value
                step_exec.compensated_at = datetime.utcnow()
                self.db.commit()

                compensated_count += 1

                await self._log_event(
                    saga_exec.id,
                    "step_compensated",
                    {"step_name": step_exec.step_name},
                    f"Step '{step_exec.step_name}' compensated",
                    step_id=step_exec.id,
                )

            except Exception as e:
                error_msg = f"Compensation failed for step '{step_exec.step_name}': {e}"
                logger.error(error_msg, exc_info=True)

                step_exec.compensation_error = str(e)
                self.db.commit()

                compensation_errors.append(error_msg)

                await self._log_event(
                    saga_exec.id,
                    "compensation_error",
                    {"step_name": step_exec.step_name, "error": str(e)},
                    error_msg,
                    step_id=step_exec.id,
                )

        await self._log_event(
            saga_exec.id,
            "compensation_completed",
            {"compensated": compensated_count, "errors": len(compensation_errors)},
            f"Compensation completed: {compensated_count} steps compensated",
        )

        if compensation_errors:
            logger.error(
                f"Saga {context.saga_id} compensation had {len(compensation_errors)} errors"
            )

        return compensated_count

    async def _create_saga_execution(
        self,
        definition: SagaDefinition,
        context: SagaContext,
    ) -> SagaExecution:
        """Create a new saga execution record.

        Args:
            definition: Saga definition
            context: Saga execution context

        Returns:
            Created saga execution
        """
        timeout_at = datetime.utcnow() + timedelta(seconds=definition.timeout_seconds)

        saga_exec = SagaExecution(
            id=context.saga_id,
            saga_name=definition.name,
            saga_version=definition.version,
            status=SagaStatus.PENDING.value,
            input_data=context.input_data,
            metadata=context.metadata,
            timeout_at=timeout_at,
        )

        self.db.add(saga_exec)
        self.db.commit()
        self.db.refresh(saga_exec)

        return saga_exec

    async def _get_or_create_step_execution(
        self,
        saga_exec: SagaExecution,
        step_def: SagaStepDefinition,
        context: SagaContext,
    ) -> SagaStepExecution:
        """Get or create step execution record.

        Args:
            saga_exec: Parent saga execution
            step_def: Step definition
            context: Saga execution context

        Returns:
            Step execution record
        """
        # Check if step already exists (for recovery)
        existing = next(
            (s for s in saga_exec.steps if s.step_name == step_def.name), None
        )

        if existing:
            return existing

        # Create new step execution
        step_order = len(saga_exec.steps)
        timeout_at = datetime.utcnow() + timedelta(seconds=step_def.timeout_seconds)

        step_exec = SagaStepExecution(
            saga_id=saga_exec.id,
            step_name=step_def.name,
            step_order=step_order,
            parallel_group=step_def.parallel_group,
            status=StepStatus.PENDING.value,
            timeout_at=timeout_at,
            max_retries=step_def.retry_attempts,
        )

        self.db.add(step_exec)
        self.db.commit()
        self.db.refresh(step_exec)

        return step_exec

    async def _log_event(
        self,
        saga_id: UUID,
        event_type: str,
        event_data: dict[str, Any] | None = None,
        message: str | None = None,
        step_id: UUID | None = None,
    ) -> None:
        """Log a saga event for monitoring.

        Args:
            saga_id: Saga execution ID
            event_type: Type of event
            event_data: Event data
            message: Human-readable message
            step_id: Optional step ID
        """
        event = SagaEvent(
            saga_id=saga_id,
            step_id=step_id,
            event_type=event_type,
            event_data=event_data or {},
            message=message,
        )

        self.db.add(event)
        self.db.commit()

    async def _recover_saga(self, saga_id: UUID) -> SagaExecution | None:
        """Recover saga execution from database.

        Args:
            saga_id: Saga execution ID

        Returns:
            Saga execution if found, None otherwise
        """
        stmt = (
            select(SagaExecution)
            .where(SagaExecution.id == saga_id)
            .options(selectinload(SagaExecution.steps))
        )
        result = self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_saga_status(self, saga_id: UUID) -> SagaExecutionResult | None:
        """Get current status of a saga execution.

        Args:
            saga_id: Saga execution ID

        Returns:
            Saga execution result if found, None otherwise
        """
        saga_exec = await self._recover_saga(saga_id)
        if not saga_exec:
            return None

        result = SagaExecutionResult(
            saga_id=saga_exec.id,
            status=SagaStatus(saga_exec.status),
            started_at=saga_exec.started_at,
            completed_at=saga_exec.completed_at,
            compensated_steps=saga_exec.compensated_steps_count,
            error_message=saga_exec.error_message,
        )

        # Add step results
        for step_exec in saga_exec.steps:
            step_result = SagaStepResult(
                step_name=step_exec.step_name,
                status=StepStatus(step_exec.status),
                output_data=step_exec.output_data or {},
                error_message=step_exec.error_message,
                started_at=step_exec.started_at,
                completed_at=step_exec.completed_at,
                retry_count=step_exec.retry_count,
            )
            result.step_results.append(step_result)

        return result

    async def recover_pending_sagas(self) -> list[UUID]:
        """Recover sagas that were interrupted (e.g., service restart).

        This method finds sagas in RUNNING or COMPENSATING state and
        attempts to continue their execution.

        Returns:
            List of saga IDs that were recovered
        """
        logger.info("Scanning for pending sagas to recover...")

        stmt = (
            select(SagaExecution)
            .where(
                SagaExecution.status.in_(
                    [SagaStatus.RUNNING.value, SagaStatus.COMPENSATING.value]
                )
            )
            .options(selectinload(SagaExecution.steps))
        )

        result = self.db.execute(stmt)
        pending_sagas = result.scalars().all()

        logger.info(f"Found {len(pending_sagas)} pending sagas to recover")

        recovered_ids: list[UUID] = []

        for saga_exec in pending_sagas:
            try:
                logger.info(
                    f"Recovering saga {saga_exec.id} (status: {saga_exec.status})"
                )

                # Mark as failed for manual review
                # In production, you might want to attempt recovery instead
                saga_exec.status = SagaStatus.FAILED.value
                saga_exec.completed_at = datetime.utcnow()
                saga_exec.error_message = "Saga interrupted by service restart"

                await self._log_event(
                    saga_exec.id,
                    "saga_recovered",
                    {"previous_status": saga_exec.status},
                    "Saga marked as failed after service restart",
                )

                recovered_ids.append(saga_exec.id)

            except Exception as e:
                logger.error(
                    f"Failed to recover saga {saga_exec.id}: {e}", exc_info=True
                )

        self.db.commit()

        return recovered_ids

    async def cleanup_old_sagas(self, days: int = 30, batch_size: int = 100) -> int:
        """Clean up old completed saga executions.

        Args:
            days: Delete sagas older than this many days
            batch_size: Maximum number to delete per call

        Returns:
            Number of sagas deleted
        """
        cutoff = datetime.utcnow() - timedelta(days=days)

        stmt = (
            select(SagaExecution)
            .where(
                SagaExecution.completed_at < cutoff,
                SagaExecution.status.in_(
                    [
                        SagaStatus.COMPLETED.value,
                        SagaStatus.FAILED.value,
                        SagaStatus.TIMEOUT.value,
                        SagaStatus.CANCELLED.value,
                    ]
                ),
            )
            .limit(batch_size)
        )

        result = self.db.execute(stmt)
        old_sagas = result.scalars().all()

        count = 0
        for saga in old_sagas:
            self.db.delete(saga)
            count += 1

        self.db.commit()

        if count > 0:
            logger.info(f"Cleaned up {count} old saga executions")

        return count
