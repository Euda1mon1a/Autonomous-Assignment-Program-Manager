"""Pydantic schemas for workflow orchestration."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

# ============================================================================
# Workflow Template Schemas
# ============================================================================


class StepRetryPolicy(BaseModel):
    """Retry policy configuration for a workflow step."""

    max_attempts: int = Field(
        default=1, ge=1, le=10, description="Maximum retry attempts"
    )
    backoff_multiplier: float = Field(
        default=1.0, ge=1.0, description="Exponential backoff multiplier"
    )
    max_backoff_seconds: int = Field(
        default=300, ge=1, description="Maximum backoff time in seconds"
    )
    retry_on_timeout: bool = Field(default=True, description="Retry if step times out")


class StepDefinition(BaseModel):
    """Definition of a single workflow step."""

    id: str = Field(..., description="Unique step identifier within the workflow")
    name: str = Field(..., description="Human-readable step name")
    handler: str = Field(
        ...,
        description="Handler function path (e.g., 'app.services.email_service.send_email')",
    )
    execution_mode: str = Field(
        default="sequential", description="sequential or parallel"
    )
    depends_on: list[str] = Field(
        default_factory=list, description="List of step IDs this step depends on"
    )
    condition: str | None = Field(
        default=None, description="Python expression to evaluate before executing"
    )
    retry_policy: StepRetryPolicy = Field(
        default_factory=StepRetryPolicy, description="Retry configuration"
    )
    timeout_seconds: int | None = Field(
        default=None, ge=1, description="Step timeout in seconds"
    )
    input_mapping: dict[str, Any] = Field(
        default_factory=dict, description="Input parameter mapping"
    )


class WorkflowTemplateDefinition(BaseModel):
    """Complete workflow template definition."""

    steps: list[StepDefinition] = Field(..., description="List of workflow steps")
    error_handlers: dict[str, str] = Field(
        default_factory=dict,
        description="Mapping of step IDs to error handler step IDs",
    )
    default_timeout_seconds: int = Field(
        default=3600, ge=1, description="Default workflow timeout"
    )

    @field_validator("steps")
    @classmethod
    def validate_steps(cls, v: list[StepDefinition]) -> list[StepDefinition]:
        """Validate steps have unique IDs and valid dependencies."""
        if not v:
            raise ValueError("Workflow must have at least one step")

        step_ids = {step.id for step in v}

        # Check for duplicate step IDs
        if len(step_ids) != len(v):
            raise ValueError("Step IDs must be unique within a workflow")

        # Validate dependencies reference existing steps
        for step in v:
            for dep in step.depends_on:
                if dep not in step_ids:
                    raise ValueError(
                        f"Step '{step.id}' depends on non-existent step '{dep}'"
                    )

        # Check for circular dependencies
        cls._check_circular_dependencies(v)

        return v

    @staticmethod
    def _check_circular_dependencies(steps: list[StepDefinition]) -> None:
        """Check for circular dependencies in workflow steps."""

        def has_cycle(step_id: str, visited: set[str], rec_stack: set[str]) -> bool:
            visited.add(step_id)
            rec_stack.add(step_id)

            step = next((s for s in steps if s.id == step_id), None)
            if step:
                for dep in step.depends_on:
                    if dep not in visited:
                        if has_cycle(dep, visited, rec_stack):
                            return True
                    elif dep in rec_stack:
                        return True

            rec_stack.remove(step_id)
            return False

        visited: set[str] = set()
        rec_stack: set[str] = set()

        for step in steps:
            if step.id not in visited:
                if has_cycle(step.id, visited, rec_stack):
                    raise ValueError(
                        f"Circular dependency detected involving step '{step.id}'"
                    )


class WorkflowTemplateCreate(BaseModel):
    """Schema for creating a new workflow template."""

    name: str = Field(..., min_length=1, max_length=255, description="Template name")
    description: str | None = Field(default=None, description="Template description")
    definition: WorkflowTemplateDefinition = Field(
        ..., description="Workflow definition"
    )
    tags: list[str] = Field(
        default_factory=list, description="Template tags for categorization"
    )


class WorkflowTemplateUpdate(BaseModel):
    """Schema for updating a workflow template (creates new version)."""

    description: str | None = None
    definition: WorkflowTemplateDefinition | None = None
    tags: list[str] | None = None
    is_active: bool | None = None


class WorkflowTemplateResponse(BaseModel):
    """Response schema for workflow template."""

    id: UUID
    name: str
    description: str | None
    version: int
    definition: dict[str, Any]
    is_active: bool
    created_at: datetime
    updated_at: datetime
    tags: list[str] | None

    class Config:
        from_attributes = True


# ============================================================================
# Workflow Instance Schemas
# ============================================================================


class WorkflowInstanceCreate(BaseModel):
    """Schema for creating a new workflow instance."""

    template_id: UUID = Field(..., description="ID of the workflow template to execute")
    name: str | None = Field(
        default=None, max_length=255, description="Optional custom instance name"
    )
    description: str | None = Field(default=None, description="Instance description")
    input_data: dict[str, Any] = Field(
        default_factory=dict, description="Input parameters for the workflow"
    )
    priority: int = Field(
        default=0,
        ge=0,
        le=100,
        description="Execution priority (higher = more important)",
    )
    timeout_seconds: int | None = Field(
        default=None, ge=1, description="Override workflow timeout"
    )


class WorkflowInstanceUpdate(BaseModel):
    """Schema for updating a workflow instance."""

    name: str | None = None
    description: str | None = None
    priority: int | None = Field(default=None, ge=0, le=100)


class WorkflowInstanceCancel(BaseModel):
    """Schema for cancelling a workflow instance."""

    reason: str = Field(..., min_length=1, description="Reason for cancellation")


class WorkflowInstanceResponse(BaseModel):
    """Response schema for workflow instance."""

    id: UUID
    template_id: UUID
    template_version: int
    name: str | None
    description: str | None
    status: str
    input_data: dict[str, Any] | None
    output_data: dict[str, Any] | None
    execution_state: dict[str, Any] | None
    error_message: str | None
    started_at: datetime | None
    completed_at: datetime | None
    timeout_at: datetime | None
    created_at: datetime
    priority: int
    parent_instance_id: UUID | None

    class Config:
        from_attributes = True


class WorkflowInstanceDetailResponse(WorkflowInstanceResponse):
    """Detailed response schema for workflow instance with step executions."""

    step_executions: list["WorkflowStepExecutionResponse"]


# ============================================================================
# Workflow Step Execution Schemas
# ============================================================================


class WorkflowStepExecutionResponse(BaseModel):
    """Response schema for workflow step execution."""

    id: UUID
    workflow_instance_id: UUID
    step_id: str
    step_name: str
    step_handler: str
    status: str
    attempt_number: int
    max_attempts: int
    input_data: dict[str, Any] | None
    output_data: dict[str, Any] | None
    error_message: str | None
    started_at: datetime | None
    completed_at: datetime | None
    duration_seconds: float | None
    next_retry_at: datetime | None
    execution_order: int | None
    condition_result: bool | None

    class Config:
        from_attributes = True


# ============================================================================
# Workflow Execution Schemas
# ============================================================================


class WorkflowExecutionStart(BaseModel):
    """Schema for starting workflow execution."""

    async_execution: bool = Field(
        default=True,
        description="Execute asynchronously (returns immediately) or wait for completion",
    )


class WorkflowExecutionPause(BaseModel):
    """Schema for pausing workflow execution."""

    reason: str | None = Field(default=None, description="Reason for pausing")


class WorkflowExecutionResume(BaseModel):
    """Schema for resuming workflow execution."""

    reason: str | None = Field(default=None, description="Reason for resuming")


# ============================================================================
# Workflow Query Schemas
# ============================================================================


class WorkflowInstanceFilter(BaseModel):
    """Filter criteria for querying workflow instances."""

    template_id: UUID | None = None
    status: str | None = None
    created_after: datetime | None = None
    created_before: datetime | None = None
    priority_min: int | None = None
    priority_max: int | None = None


class WorkflowInstanceList(BaseModel):
    """Paginated list of workflow instances."""

    items: list[WorkflowInstanceResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class WorkflowTemplateList(BaseModel):
    """Paginated list of workflow templates."""

    items: list[WorkflowTemplateResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# ============================================================================
# Workflow Statistics Schemas
# ============================================================================


class WorkflowStatistics(BaseModel):
    """Statistics for workflow execution."""

    total_instances: int
    running_instances: int
    completed_instances: int
    failed_instances: int
    cancelled_instances: int
    avg_duration_seconds: float | None
    success_rate: float


class WorkflowTemplateStatistics(BaseModel):
    """Statistics for a specific workflow template."""

    template_id: UUID
    template_name: str
    template_version: int
    total_executions: int
    successful_executions: int
    failed_executions: int
    avg_duration_seconds: float | None
    last_execution_at: datetime | None
