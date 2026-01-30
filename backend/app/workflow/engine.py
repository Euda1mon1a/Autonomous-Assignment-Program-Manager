"""Workflow orchestration engine for multi-step process execution.

This module provides a comprehensive workflow execution engine designed for
complex, multi-step processes like schedule generation, compliance validation,
and notification workflows in the Residency Scheduler application.

Core Concepts
-------------

**Templates**: Versioned workflow definitions stored in the database. Templates
define the steps, their execution order, retry policies, and conditional logic.
New versions are created when definitions change, preserving history.

**Instances**: Runtime executions of a workflow template. Each instance tracks
its own state, input/output data, and step execution history independently.

**Steps**: Individual units of work within a workflow. Steps can:
- Execute sequentially or in parallel based on dependencies
- Be conditionally skipped based on runtime expressions
- Retry automatically with exponential backoff on failure
- Have individual timeouts separate from the workflow timeout

**Handlers**: Async Python functions that implement step logic. Handlers receive
input data and return output data that can be consumed by dependent steps.

Execution Model
---------------

The workflow engine uses a dependency-based execution model:

1. Steps declare dependencies on other steps via `depends_on`
2. The engine builds an execution plan respecting these dependencies
3. Steps with the same set of completed dependencies run in parallel
4. Failed steps trigger retry logic or halt the workflow
5. All state is persisted to allow resumption after failures

Features:
- Sequential and parallel step execution
- Conditional branching with Python expressions
- Error handling with configurable retry policies
- Exponential backoff between retries
- State persistence for resumability
- Step and workflow-level timeouts
- Graceful cancellation with running step cleanup
- Template versioning for workflow evolution

Example Usage
-------------

Creating and executing a workflow::

    from app.workflow.engine import WorkflowEngine

    engine = WorkflowEngine(db)

    # Create a template
    template = engine.create_template(
        name="schedule_generation",
        definition={
            "steps": [
                {
                    "id": "validate",
                    "name": "Validate Input",
                    "handler": "app.handlers.validate_schedule_input",
                    "timeout_seconds": 60,
                },
                {
                    "id": "generate",
                    "name": "Generate Schedule",
                    "handler": "app.handlers.generate_schedule",
                    "depends_on": ["validate"],
                    "retry_policy": {"max_attempts": 3, "backoff_multiplier": 2},
                    "timeout_seconds": 600,
                },
                {
                    "id": "notify",
                    "name": "Send Notifications",
                    "handler": "app.handlers.send_notifications",
                    "depends_on": ["generate"],
                    "condition": "step_outputs['generate']['success'] == True",
                },
            ],
            "default_timeout_seconds": 3600,
        },
    )

    # Create and execute an instance
    instance = engine.create_instance(
        template_id=template.id,
        input_data={"block": 10, "year": 2024},
    )
    result = await engine.execute_workflow(instance.id, async_execution=False)

See Also
--------
- `app.workflow.state_machine`: Event-driven state machine for entity lifecycle
- `app.models.workflow`: Database models for persistence
- `backend/app/workflow/README.md`: Detailed documentation with examples
"""

import asyncio
import importlib
import logging
import traceback
from collections.abc import Callable
from datetime import datetime, timedelta
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session, selectinload

from app.models.workflow import (
    StepStatus,
    WorkflowInstance,
    WorkflowStatus,
    WorkflowStepExecution,
    WorkflowTemplate,
)

logger = logging.getLogger(__name__)


class WorkflowExecutionError(Exception):
    """Base exception for workflow execution errors."""

    pass


class WorkflowTimeoutError(WorkflowExecutionError):
    """Raised when workflow execution times out."""

    pass


class StepTimeoutError(WorkflowExecutionError):
    """Raised when step execution times out."""

    pass


class StepExecutionError(WorkflowExecutionError):
    """Raised when step execution fails."""

    pass


class ConditionEvaluationError(WorkflowExecutionError):
    """Raised when condition evaluation fails."""

    pass


class WorkflowEngine:
    """
    Workflow orchestration engine.

    Provides comprehensive workflow execution capabilities including:
    - Template-based workflow definition
    - Sequential and parallel execution
    - Conditional step execution
    - Automatic retry with exponential backoff
    - Timeout handling at workflow and step levels
    - State persistence for resumability
    - Graceful cancellation
    """

    def __init__(self, db: Session) -> None:
        """
        Initialize workflow engine.

        Args:
            db: Database session for state persistence
        """
        self.db = db
        self._handler_cache: dict[str, Callable] = {}

        # ========================================================================
        # Template Management
        # ========================================================================

    def create_template(
        self,
        name: str,
        definition: dict[str, Any],
        description: str | None = None,
        tags: list[str] | None = None,
        created_by_id: UUID | None = None,
    ) -> WorkflowTemplate:
        """
        Create a new workflow template.

        Args:
            name: Template name
            definition: Workflow definition (steps, error handlers, etc.)
            description: Optional template description
            tags: Optional tags for categorization
            created_by_id: ID of user creating the template

        Returns:
            Created WorkflowTemplate instance

        Raises:
            ValueError: If template definition is invalid
        """
        # Check if template with this name exists
        existing = (
            self.db.query(WorkflowTemplate)
            .filter(WorkflowTemplate.name == name)
            .order_by(WorkflowTemplate.version.desc())
            .first()
        )

        version = 1 if not existing else existing.version + 1

        template = WorkflowTemplate(
            name=name,
            version=version,
            description=description,
            definition=definition,
            tags=tags or [],
            created_by_id=created_by_id,
        )

        self.db.add(template)
        self.db.flush()

        logger.info(f"Created workflow template '{name}' version {version}")
        return template

    def get_template(
        self,
        template_id: UUID | None = None,
        name: str | None = None,
        version: int | None = None,
    ) -> WorkflowTemplate | None:
        """
        Get workflow template by ID or name/version.

        Args:
            template_id: Template UUID
            name: Template name (requires version or gets latest)
            version: Template version (requires name)

        Returns:
            WorkflowTemplate instance or None if not found
        """
        if template_id:
            return (
                self.db.query(WorkflowTemplate)
                .filter(WorkflowTemplate.id == template_id)
                .first()
            )

        if name:
            query = self.db.query(WorkflowTemplate).filter(
                WorkflowTemplate.name == name,
                WorkflowTemplate.is_active == True,  # noqa: E712
            )

            if version:
                query = query.filter(WorkflowTemplate.version == version)
            else:
                query = query.order_by(WorkflowTemplate.version.desc())

            return query.first()

        return None

    def update_template(
        self,
        template_id: UUID,
        definition: dict[str, Any] | None = None,
        description: str | None = None,
        tags: list[str] | None = None,
        is_active: bool | None = None,
    ) -> WorkflowTemplate:
        """
        Update workflow template (creates new version if definition changed).

        Args:
            template_id: Template ID to update
            definition: New workflow definition (creates new version)
            description: Updated description
            tags: Updated tags
            is_active: Set template active/inactive

        Returns:
            Updated or new WorkflowTemplate instance

        Raises:
            ValueError: If template not found
        """
        template = self.get_template(template_id=template_id)
        if not template:
            raise ValueError(f"Template {template_id} not found")

            # If definition changed, create new version
        if definition and definition != template.definition:
            return self.create_template(
                name=template.name,
                definition=definition,
                description=description or template.description,
                tags=tags or template.tags,
            )

            # Otherwise update in place
        if description is not None:
            template.description = description
        if tags is not None:
            template.tags = tags
        if is_active is not None:
            template.is_active = is_active

        template.updated_at = datetime.utcnow()
        self.db.flush()

        return template

        # ========================================================================
        # Workflow Instance Management
        # ========================================================================

    def create_instance(
        self,
        template_id: UUID,
        input_data: dict[str, Any] | None = None,
        name: str | None = None,
        description: str | None = None,
        priority: int = 0,
        timeout_seconds: int | None = None,
        created_by_id: UUID | None = None,
        parent_instance_id: UUID | None = None,
    ) -> WorkflowInstance:
        """
        Create a new workflow instance from a template.

        Args:
            template_id: ID of workflow template
            input_data: Input parameters for workflow
            name: Optional custom instance name
            description: Instance description
            priority: Execution priority (0-100, higher = more important)
            timeout_seconds: Override default workflow timeout
            created_by_id: ID of user creating instance
            parent_instance_id: Parent workflow ID (for sub-workflows)

        Returns:
            Created WorkflowInstance

        Raises:
            ValueError: If template not found or inactive
        """
        template = self.get_template(template_id=template_id)
        if not template:
            raise ValueError(f"Template {template_id} not found")

        if not template.is_active:
            raise ValueError(
                f"Template {template.name} v{template.version} is inactive"
            )

            # Calculate timeout
        default_timeout = template.definition.get("default_timeout_seconds", 3600)
        timeout = timeout_seconds or default_timeout
        timeout_at = datetime.utcnow() + timedelta(seconds=timeout)

        instance = WorkflowInstance(
            template_id=template.id,
            template_version=template.version,
            name=name,
            description=description,
            status=WorkflowStatus.PENDING.value,
            input_data=input_data or {},
            priority=priority,
            timeout_at=timeout_at,
            created_by_id=created_by_id,
            parent_instance_id=parent_instance_id,
            execution_state={
                "completed_steps": [],
                "current_step": None,
                "step_outputs": {},
                "context": {},
            },
        )

        self.db.add(instance)
        self.db.flush()

        logger.info(
            f"Created workflow instance {instance.id} from template "
            f"'{template.name}' v{template.version}"
        )
        return instance

    def get_instance(self, instance_id: UUID) -> WorkflowInstance | None:
        """
        Get workflow instance by ID with step executions.

        Args:
            instance_id: Workflow instance ID

        Returns:
            WorkflowInstance with eager-loaded step executions or None
        """
        return (
            self.db.query(WorkflowInstance)
            .options(selectinload(WorkflowInstance.step_executions))
            .filter(WorkflowInstance.id == instance_id)
            .first()
        )

    def cancel_instance(
        self,
        instance_id: UUID,
        reason: str,
        cancelled_by_id: UUID | None = None,
    ) -> WorkflowInstance:
        """
        Cancel a running workflow instance.

        Args:
            instance_id: Workflow instance ID
            reason: Cancellation reason
            cancelled_by_id: ID of user cancelling workflow

        Returns:
            Cancelled WorkflowInstance

        Raises:
            ValueError: If instance not found or cannot be cancelled
        """
        instance = self.get_instance(instance_id)
        if not instance:
            raise ValueError(f"Workflow instance {instance_id} not found")

        if not instance.can_cancel:
            raise ValueError(f"Cannot cancel workflow in status {instance.status}")

        instance.status = WorkflowStatus.CANCELLED.value
        instance.cancelled_at = datetime.utcnow()
        instance.cancelled_by_id = cancelled_by_id
        instance.cancellation_reason = reason

        # Cancel running steps
        for step_exec in instance.step_executions:
            if step_exec.status == StepStatus.RUNNING.value:
                step_exec.status = StepStatus.CANCELLED.value
                step_exec.completed_at = datetime.utcnow()

        self.db.flush()

        logger.info(f"Cancelled workflow instance {instance_id}: {reason}")
        return instance

        # ========================================================================
        # Workflow Execution
        # ========================================================================

    async def execute_workflow(
        self,
        instance_id: UUID,
        async_execution: bool = True,
    ) -> WorkflowInstance:
        """
        Execute a workflow instance.

        Args:
            instance_id: Workflow instance ID
            async_execution: If True, returns immediately; if False, waits for completion

        Returns:
            WorkflowInstance (in RUNNING state if async, terminal state if sync)

        Raises:
            ValueError: If instance not found or already completed
            WorkflowExecutionError: If workflow execution fails
        """
        instance = self.get_instance(instance_id)
        if not instance:
            raise ValueError(f"Workflow instance {instance_id} not found")

        if instance.is_terminal:
            raise ValueError(
                f"Workflow instance {instance_id} is already in terminal state {instance.status}"
            )

            # Start workflow
        instance.status = WorkflowStatus.RUNNING.value
        instance.started_at = datetime.utcnow()
        self.db.commit()

        logger.info(f"Starting workflow instance {instance_id}")

        if async_execution:
            # Execute in background
            asyncio.create_task(self._execute_workflow_async(instance_id))
            return instance
        else:
            # Execute synchronously
            return await self._execute_workflow_async(instance_id)

    async def _execute_workflow_async(self, instance_id: UUID) -> WorkflowInstance:
        """
        Internal async workflow execution.

        Args:
            instance_id: Workflow instance ID

        Returns:
            Completed WorkflowInstance
        """
        try:
            instance = self.get_instance(instance_id)
            if not instance:
                raise ValueError(f"Workflow instance {instance_id} not found")

            template = instance.template
            steps = template.definition.get("steps", [])

            # Build execution plan
            execution_plan = self._build_execution_plan(steps)

            # Execute steps
            for step_group in execution_plan:
                # Check for cancellation
                self.db.refresh(instance)
                if instance.status == WorkflowStatus.CANCELLED.value:
                    logger.info(f"Workflow {instance_id} was cancelled")
                    return instance

                    # Check for timeout
                if instance.timeout_at and datetime.utcnow() > instance.timeout_at:
                    instance.status = WorkflowStatus.TIMED_OUT.value
                    instance.completed_at = datetime.utcnow()
                    instance.error_message = "Workflow execution timed out"
                    self.db.commit()
                    raise WorkflowTimeoutError("Workflow execution timed out")

                    # Execute step group (parallel or sequential)
                await self._execute_step_group(instance, step_group)

                # Workflow completed successfully
            instance.status = WorkflowStatus.COMPLETED.value
            instance.completed_at = datetime.utcnow()
            self.db.commit()

            logger.info(f"Workflow instance {instance_id} completed successfully")
            return instance

        except Exception as e:
            logger.error(f"Workflow {instance_id} failed: {str(e)}", exc_info=True)

            instance = self.get_instance(instance_id)
            if instance:
                instance.status = WorkflowStatus.FAILED.value
                instance.completed_at = datetime.utcnow()
                instance.error_message = str(e)
                instance.error_details = {
                    "error_type": type(e).__name__,
                    "traceback": traceback.format_exc(),
                }
                self.db.commit()

            raise

    def _build_execution_plan(self, steps: list[dict]) -> list[list[dict]]:
        """
        Build execution plan respecting dependencies.

        Args:
            steps: List of step definitions

        Returns:
            List of step groups (each group can execute in parallel)
        """
        # Build dependency graph
        step_map = {step["id"]: step for step in steps}
        in_degree = {step["id"]: len(step.get("depends_on", [])) for step in steps}

        execution_plan: list[list[dict]] = []
        executed: set[str] = set()

        while len(executed) < len(steps):
            # Find steps with no unmet dependencies
            ready_steps = [
                step
                for step in steps
                if step["id"] not in executed
                and all(dep in executed for dep in step.get("depends_on", []))
            ]

            if not ready_steps:
                raise WorkflowExecutionError(
                    "Circular dependency or missing dependencies detected"
                )

            execution_plan.append(ready_steps)
            executed.update(step["id"] for step in ready_steps)

        return execution_plan

    async def _execute_step_group(
        self,
        instance: WorkflowInstance,
        step_group: list[dict],
    ) -> None:
        """
        Execute a group of steps (potentially in parallel).

        Args:
            instance: Workflow instance
            step_group: List of steps to execute

        Raises:
            StepExecutionError: If any step fails
        """
        tasks = []
        for step_def in step_group:
            tasks.append(self._execute_step(instance, step_def))

            # Execute all steps in group concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Check for failures
        for result in results:
            if isinstance(result, Exception):
                raise result

    async def _execute_step(
        self,
        instance: WorkflowInstance,
        step_def: dict,
    ) -> WorkflowStepExecution:
        """
        Execute a single workflow step with retry logic.

        Args:
            instance: Workflow instance
            step_def: Step definition from template

        Returns:
            Completed WorkflowStepExecution

        Raises:
            StepExecutionError: If step fails after all retries
        """
        step_id = step_def["id"]
        retry_policy = step_def.get("retry_policy", {})
        max_attempts = retry_policy.get("max_attempts", 1)

        # Check if step should be skipped based on condition
        if step_def.get("condition"):
            should_execute = self._evaluate_condition(
                step_def["condition"],
                instance.execution_state,
            )
            if not should_execute:
                return self._skip_step(instance, step_def)

                # Try to execute step with retries
        for attempt in range(1, max_attempts + 1):
            try:
                step_exec = await self._execute_step_attempt(
                    instance,
                    step_def,
                    attempt,
                    max_attempts,
                )

                if step_exec.status == StepStatus.COMPLETED.value:
                    # Update execution state with step output
                    instance.execution_state["completed_steps"].append(step_id)
                    instance.execution_state["step_outputs"][step_id] = (
                        step_exec.output_data
                    )
                    self.db.commit()
                    return step_exec

                    # Step failed, check if we should retry
                if attempt < max_attempts:
                    # Calculate backoff delay
                    backoff_multiplier = retry_policy.get("backoff_multiplier", 2.0)
                    max_backoff = retry_policy.get("max_backoff_seconds", 300)
                    delay = min(backoff_multiplier**attempt, max_backoff)

                    logger.info(
                        f"Step {step_id} failed (attempt {attempt}/{max_attempts}), "
                        f"retrying in {delay}s"
                    )

                    step_exec.status = StepStatus.RETRYING.value
                    step_exec.next_retry_at = datetime.utcnow() + timedelta(
                        seconds=delay
                    )
                    self.db.commit()

                    await asyncio.sleep(delay)

            except Exception as e:
                logger.error(
                    f"Step {step_id} attempt {attempt} failed: {str(e)}", exc_info=True
                )

                if attempt >= max_attempts:
                    raise StepExecutionError(
                        f"Step {step_id} failed after {max_attempts} attempts: {str(e)}"
                    )

        raise StepExecutionError(f"Step {step_id} failed after all retry attempts")

    async def _execute_step_attempt(
        self,
        instance: WorkflowInstance,
        step_def: dict,
        attempt: int,
        max_attempts: int,
    ) -> WorkflowStepExecution:
        """
        Execute a single attempt of a workflow step.

        Args:
            instance: Workflow instance
            step_def: Step definition
            attempt: Current attempt number
            max_attempts: Maximum attempts allowed

        Returns:
            WorkflowStepExecution record

        Raises:
            StepTimeoutError: If step times out
        """
        step_id = step_def["id"]

        # Create or update step execution record
        step_exec = (
            self.db.query(WorkflowStepExecution)
            .filter(
                WorkflowStepExecution.workflow_instance_id == instance.id,
                WorkflowStepExecution.step_id == step_id,
            )
            .first()
        )

        if not step_exec:
            # Calculate timeout
            timeout_seconds = step_def.get("timeout_seconds")
            timeout_at = None
            if timeout_seconds:
                timeout_at = datetime.utcnow() + timedelta(seconds=timeout_seconds)

            step_exec = WorkflowStepExecution(
                workflow_instance_id=instance.id,
                step_id=step_id,
                step_name=step_def["name"],
                step_handler=step_def["handler"],
                status=StepStatus.RUNNING.value,
                attempt_number=attempt,
                max_attempts=max_attempts,
                timeout_at=timeout_at,
                depends_on=step_def.get("depends_on", []),
                condition_expression=step_def.get("condition"),
            )
            self.db.add(step_exec)
        else:
            step_exec.status = StepStatus.RUNNING.value
            step_exec.attempt_number = attempt

        step_exec.started_at = datetime.utcnow()
        self.db.commit()

        # Prepare input data
        input_data = self._prepare_step_input(
            step_def.get("input_mapping", {}),
            instance.input_data,
            instance.execution_state,
        )
        step_exec.input_data = input_data

        try:
            # Load and execute handler
            handler = self._load_handler(step_def["handler"])

            # Execute with timeout
            timeout_seconds = step_def.get("timeout_seconds")
            if timeout_seconds:
                output_data = await asyncio.wait_for(
                    handler(input_data),
                    timeout=timeout_seconds,
                )
            else:
                output_data = await handler(input_data)

                # Step completed successfully
            step_exec.status = StepStatus.COMPLETED.value
            step_exec.output_data = output_data
            step_exec.completed_at = datetime.utcnow()

            if step_exec.started_at:
                duration = (
                    step_exec.completed_at - step_exec.started_at
                ).total_seconds()
                step_exec.duration_seconds = duration

            self.db.commit()

            logger.info(
                f"Step {step_id} completed successfully "
                f"(attempt {attempt}, duration: {step_exec.duration_seconds:.2f}s)"
            )

            return step_exec

        except TimeoutError:
            step_exec.status = StepStatus.TIMED_OUT.value
            step_exec.completed_at = datetime.utcnow()
            step_exec.error_message = f"Step timed out after {timeout_seconds}s"
            self.db.commit()

            raise StepTimeoutError(f"Step {step_id} timed out after {timeout_seconds}s")

        except Exception as e:
            step_exec.status = StepStatus.FAILED.value
            step_exec.completed_at = datetime.utcnow()
            step_exec.error_message = str(e)
            step_exec.error_details = {"error_type": type(e).__name__}
            step_exec.error_traceback = traceback.format_exc()
            self.db.commit()

            raise

    def _skip_step(
        self,
        instance: WorkflowInstance,
        step_def: dict,
    ) -> WorkflowStepExecution:
        """
        Skip a step based on conditional evaluation.

        Args:
            instance: Workflow instance
            step_def: Step definition

        Returns:
            WorkflowStepExecution marked as skipped
        """
        step_exec = WorkflowStepExecution(
            workflow_instance_id=instance.id,
            step_id=step_def["id"],
            step_name=step_def["name"],
            step_handler=step_def["handler"],
            status=StepStatus.SKIPPED.value,
            attempt_number=1,
            max_attempts=1,
            condition_result=False,
            condition_expression=step_def.get("condition"),
            started_at=datetime.utcnow(),
            completed_at=datetime.utcnow(),
            duration_seconds=0.0,
        )

        self.db.add(step_exec)
        self.db.commit()

        logger.info(f"Step {step_def['id']} skipped due to condition")
        return step_exec

        # ========================================================================
        # Helper Methods
        # ========================================================================

    def _evaluate_condition(
        self,
        condition: str,
        execution_state: dict[str, Any],
    ) -> bool:
        """
        Evaluate a conditional expression.

        Args:
            condition: Python expression to evaluate
            execution_state: Current workflow execution state

        Returns:
            Boolean result of condition evaluation

        Raises:
            ConditionEvaluationError: If condition cannot be evaluated
        """
        try:
            # Build safe evaluation context
            context = {
                "step_outputs": execution_state.get("step_outputs", {}),
                "input_data": execution_state.get("input_data", {}),
                "context": execution_state.get("context", {}),
            }

            # Evaluate condition
            result = eval(condition, {"__builtins__": {}}, context)
            return bool(result)

        except Exception as e:
            raise ConditionEvaluationError(
                f"Failed to evaluate condition '{condition}': {str(e)}"
            )

    def _prepare_step_input(
        self,
        input_mapping: dict[str, Any],
        workflow_input: dict[str, Any],
        execution_state: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Prepare input data for step execution using input mapping.

        Args:
            input_mapping: Mapping of input parameter names to values/expressions
            workflow_input: Original workflow input data
            execution_state: Current execution state

        Returns:
            Dictionary of input parameters for step
        """
        input_data = {}

        for param_name, param_value in input_mapping.items():
            # If value is a string starting with "step_outputs.", resolve it
            if isinstance(param_value, str) and param_value.startswith("step_outputs."):
                path = param_value.split(".")
                value = execution_state.get("step_outputs", {})
                for key in path[1:]:
                    value = value.get(key, {})
                input_data[param_name] = value
            else:
                input_data[param_name] = param_value

        return input_data

    def _load_handler(self, handler_path: str) -> Callable:
        """
        Load handler function from module path.

        Args:
            handler_path: Module path to handler (e.g., "app.services.email_service.send_email")

        Returns:
            Handler function

        Raises:
            ImportError: If handler cannot be loaded
        """
        if handler_path in self._handler_cache:
            return self._handler_cache[handler_path]

        try:
            module_path, function_name = handler_path.rsplit(".", 1)
            module = importlib.import_module(module_path)
            handler = getattr(module, function_name)

            self._handler_cache[handler_path] = handler
            return handler

        except Exception as e:
            raise ImportError(f"Failed to load handler '{handler_path}': {str(e)}")

            # ========================================================================
            # Query Methods
            # ========================================================================

    def query_instances(
        self,
        template_id: UUID | None = None,
        status: str | None = None,
        created_after: datetime | None = None,
        created_before: datetime | None = None,
        priority_min: int | None = None,
        priority_max: int | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[list[WorkflowInstance], int]:
        """
        Query workflow instances with filters.

        Args:
            template_id: Filter by template ID
            status: Filter by status
            created_after: Filter by creation date (after)
            created_before: Filter by creation date (before)
            priority_min: Filter by minimum priority
            priority_max: Filter by maximum priority
            limit: Maximum results to return
            offset: Offset for pagination

        Returns:
            Tuple of (list of instances, total count)
        """
        query = self.db.query(WorkflowInstance)

        # Apply filters
        if template_id:
            query = query.filter(WorkflowInstance.template_id == template_id)
        if status:
            query = query.filter(WorkflowInstance.status == status)
        if created_after:
            query = query.filter(WorkflowInstance.created_at >= created_after)
        if created_before:
            query = query.filter(WorkflowInstance.created_at <= created_before)
        if priority_min is not None:
            query = query.filter(WorkflowInstance.priority >= priority_min)
        if priority_max is not None:
            query = query.filter(WorkflowInstance.priority <= priority_max)

            # Get total count
        total = query.count()

        # Apply pagination and ordering
        instances = (
            query.order_by(
                WorkflowInstance.priority.desc(), WorkflowInstance.created_at.desc()
            )
            .limit(limit)
            .offset(offset)
            .all()
        )

        return instances, total

    def get_statistics(self, template_id: UUID | None = None) -> dict[str, Any]:
        """
        Get workflow execution statistics.

        Args:
            template_id: Optional template ID to filter statistics

        Returns:
            Dictionary of statistics
        """
        query = self.db.query(WorkflowInstance)

        if template_id:
            query = query.filter(WorkflowInstance.template_id == template_id)

        total = query.count()
        running = query.filter(
            WorkflowInstance.status == WorkflowStatus.RUNNING.value
        ).count()
        completed = query.filter(
            WorkflowInstance.status == WorkflowStatus.COMPLETED.value
        ).count()
        failed = query.filter(
            WorkflowInstance.status == WorkflowStatus.FAILED.value
        ).count()
        cancelled = query.filter(
            WorkflowInstance.status == WorkflowStatus.CANCELLED.value
        ).count()

        # Calculate success rate
        success_rate = (completed / total * 100) if total > 0 else 0.0

        # Calculate average duration for completed workflows
        avg_duration = None
        completed_instances = query.filter(
            WorkflowInstance.status == WorkflowStatus.COMPLETED.value,
            WorkflowInstance.started_at.isnot(None),
            WorkflowInstance.completed_at.isnot(None),
        ).all()

        if completed_instances:
            durations = [
                (inst.completed_at - inst.started_at).total_seconds()
                for inst in completed_instances
            ]
            avg_duration = sum(durations) / len(durations)

        return {
            "total_instances": total,
            "running_instances": running,
            "completed_instances": completed,
            "failed_instances": failed,
            "cancelled_instances": cancelled,
            "success_rate": success_rate,
            "avg_duration_seconds": avg_duration,
        }
