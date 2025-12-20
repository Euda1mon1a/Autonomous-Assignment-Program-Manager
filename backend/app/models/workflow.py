"""Models for workflow orchestration.

This module provides database models for a comprehensive workflow orchestration
system that supports:
- Versioned workflow templates
- Sequential and parallel step execution
- Conditional branching
- Error handling with retry logic
- State persistence
- Step timeout handling
- Workflow cancellation
"""
import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    Index,
)
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.db.types import GUID, JSONType


class WorkflowStatus(str, Enum):
    """Status of a workflow instance."""
    PENDING = "pending"          # Workflow created, not yet started
    RUNNING = "running"          # Workflow is executing
    PAUSED = "paused"           # Workflow execution paused
    COMPLETED = "completed"      # Workflow completed successfully
    FAILED = "failed"           # Workflow failed
    CANCELLED = "cancelled"      # Workflow was cancelled
    TIMED_OUT = "timed_out"     # Workflow exceeded timeout


class StepStatus(str, Enum):
    """Status of a workflow step execution."""
    PENDING = "pending"          # Step not yet started
    RUNNING = "running"          # Step is executing
    COMPLETED = "completed"      # Step completed successfully
    FAILED = "failed"           # Step failed
    SKIPPED = "skipped"         # Step skipped due to conditions
    RETRYING = "retrying"       # Step is retrying after failure
    TIMED_OUT = "timed_out"     # Step exceeded timeout
    CANCELLED = "cancelled"      # Step was cancelled


class StepExecutionMode(str, Enum):
    """Execution mode for workflow steps."""
    SEQUENTIAL = "sequential"    # Execute steps one after another
    PARALLEL = "parallel"        # Execute steps concurrently


class WorkflowTemplate(Base):
    """
    Versioned workflow template definition.

    Templates define the structure of workflows including steps, execution order,
    retry policies, and conditional logic. Templates are versioned to allow
    evolution while maintaining backward compatibility.
    """
    __tablename__ = "workflow_templates"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)

    # Template identification
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    version = Column(Integer, nullable=False, default=1)

    # Template definition
    # Structure: {
    #   "steps": [
    #     {
    #       "id": "step1",
    #       "name": "Step Name",
    #       "handler": "module.function",
    #       "execution_mode": "sequential|parallel",
    #       "depends_on": ["step0"],  # Dependencies
    #       "condition": "previous_step.output.status == 'success'",
    #       "retry_policy": {
    #         "max_attempts": 3,
    #         "backoff_multiplier": 2,
    #         "max_backoff_seconds": 300
    #       },
    #       "timeout_seconds": 60,
    #       "input_mapping": {"param": "previous_step.output.value"}
    #     }
    #   ],
    #   "error_handlers": {
    #     "step1": "error_handler_step"
    #   },
    #   "default_timeout_seconds": 3600
    # }
    definition = Column(JSONType(), nullable=False)

    # Metadata
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_by_id = Column(GUID(), ForeignKey("users.id"), nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Tags for categorization
    tags = Column(JSONType(), nullable=True)  # ["schedule", "acgme", "critical"]

    # Relationships
    instances = relationship("WorkflowInstance", back_populates="template", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_workflow_template_name_version", "name", "version", unique=True),
        Index("idx_workflow_template_active", "is_active"),
    )

    def __repr__(self):
        return f"<WorkflowTemplate(name='{self.name}', version={self.version})>"


class WorkflowInstance(Base):
    """
    Runtime instance of a workflow.

    Represents a specific execution of a workflow template with its own
    state, inputs, and execution history.
    """
    __tablename__ = "workflow_instances"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)

    # Template reference
    template_id = Column(GUID(), ForeignKey("workflow_templates.id"), nullable=False)
    template_version = Column(Integer, nullable=False)

    # Instance metadata
    name = Column(String(255), nullable=True)  # Optional custom name
    description = Column(Text, nullable=True)

    # Status tracking
    status = Column(String(20), nullable=False, default=WorkflowStatus.PENDING.value, index=True)

    # Execution context
    # Input parameters provided when starting the workflow
    input_data = Column(JSONType(), nullable=True)

    # Output data from completed workflow
    output_data = Column(JSONType(), nullable=True)

    # Current execution state (for resuming)
    # Structure: {
    #   "completed_steps": ["step1", "step2"],
    #   "current_step": "step3",
    #   "step_outputs": {
    #     "step1": {"result": "value"},
    #     "step2": {"result": "value"}
    #   },
    #   "context": {}  # Shared context between steps
    # }
    execution_state = Column(JSONType(), nullable=True)

    # Error tracking
    error_message = Column(Text, nullable=True)
    error_details = Column(JSONType(), nullable=True)

    # Timing
    started_at = Column(DateTime, nullable=True, index=True)
    completed_at = Column(DateTime, nullable=True)
    timeout_at = Column(DateTime, nullable=True)  # When workflow should timeout

    # Ownership and audit
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_by_id = Column(GUID(), ForeignKey("users.id"), nullable=True)
    cancelled_at = Column(DateTime, nullable=True)
    cancelled_by_id = Column(GUID(), ForeignKey("users.id"), nullable=True)
    cancellation_reason = Column(Text, nullable=True)

    # Priority (higher = more important)
    priority = Column(Integer, default=0, nullable=False, index=True)

    # Parent workflow (for sub-workflows)
    parent_instance_id = Column(GUID(), ForeignKey("workflow_instances.id"), nullable=True)

    # Relationships
    template = relationship("WorkflowTemplate", back_populates="instances")
    step_executions = relationship(
        "WorkflowStepExecution",
        back_populates="workflow_instance",
        cascade="all, delete-orphan",
        order_by="WorkflowStepExecution.started_at"
    )
    child_workflows = relationship(
        "WorkflowInstance",
        foreign_keys=[parent_instance_id],
        remote_side=[id]
    )

    __table_args__ = (
        Index("idx_workflow_instance_status_priority", "status", "priority"),
        Index("idx_workflow_instance_template", "template_id"),
        Index("idx_workflow_instance_parent", "parent_instance_id"),
    )

    def __repr__(self):
        return f"<WorkflowInstance(id='{self.id}', status='{self.status}')>"

    @property
    def is_terminal(self) -> bool:
        """Check if workflow is in a terminal state."""
        return self.status in [
            WorkflowStatus.COMPLETED.value,
            WorkflowStatus.FAILED.value,
            WorkflowStatus.CANCELLED.value,
            WorkflowStatus.TIMED_OUT.value,
        ]

    @property
    def is_running(self) -> bool:
        """Check if workflow is currently running."""
        return self.status == WorkflowStatus.RUNNING.value

    @property
    def can_cancel(self) -> bool:
        """Check if workflow can be cancelled."""
        return self.status in [
            WorkflowStatus.PENDING.value,
            WorkflowStatus.RUNNING.value,
            WorkflowStatus.PAUSED.value,
        ]


class WorkflowStepExecution(Base):
    """
    Execution record for a single workflow step.

    Tracks the execution history, retries, and results for each step
    in a workflow instance.
    """
    __tablename__ = "workflow_step_executions"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)

    # Workflow reference
    workflow_instance_id = Column(GUID(), ForeignKey("workflow_instances.id"), nullable=False)

    # Step identification
    step_id = Column(String(255), nullable=False)  # ID from template definition
    step_name = Column(String(255), nullable=False)
    step_handler = Column(String(500), nullable=False)  # e.g., "app.services.email_service.send_email"

    # Execution status
    status = Column(String(20), nullable=False, default=StepStatus.PENDING.value, index=True)

    # Retry tracking
    attempt_number = Column(Integer, default=1, nullable=False)
    max_attempts = Column(Integer, default=1, nullable=False)

    # Input/Output
    input_data = Column(JSONType(), nullable=True)
    output_data = Column(JSONType(), nullable=True)

    # Error tracking
    error_message = Column(Text, nullable=True)
    error_details = Column(JSONType(), nullable=True)
    error_traceback = Column(Text, nullable=True)

    # Timing
    started_at = Column(DateTime, nullable=True, index=True)
    completed_at = Column(DateTime, nullable=True)
    timeout_at = Column(DateTime, nullable=True)
    duration_seconds = Column(Float, nullable=True)

    # Next retry time (for exponential backoff)
    next_retry_at = Column(DateTime, nullable=True, index=True)

    # Step execution order (for parallel vs sequential)
    execution_order = Column(Integer, nullable=True)

    # Dependencies (step IDs this step depends on)
    depends_on = Column(JSONType(), nullable=True)  # ["step1", "step2"]

    # Conditional evaluation result
    condition_result = Column(Boolean, nullable=True)
    condition_expression = Column(Text, nullable=True)

    # Relationships
    workflow_instance = relationship("WorkflowInstance", back_populates="step_executions")

    __table_args__ = (
        Index("idx_step_execution_workflow_step", "workflow_instance_id", "step_id"),
        Index("idx_step_execution_status", "status"),
        Index("idx_step_execution_retry", "next_retry_at"),
    )

    def __repr__(self):
        return f"<WorkflowStepExecution(step_name='{self.step_name}', status='{self.status}', attempt={self.attempt_number})>"

    @property
    def is_terminal(self) -> bool:
        """Check if step execution is in a terminal state."""
        return self.status in [
            StepStatus.COMPLETED.value,
            StepStatus.FAILED.value,
            StepStatus.SKIPPED.value,
            StepStatus.CANCELLED.value,
            StepStatus.TIMED_OUT.value,
        ]

    @property
    def can_retry(self) -> bool:
        """Check if step can be retried."""
        return (
            self.status == StepStatus.FAILED.value
            and self.attempt_number < self.max_attempts
        )
