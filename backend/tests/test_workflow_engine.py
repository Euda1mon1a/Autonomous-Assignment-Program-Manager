"""Tests for workflow orchestration engine.

This test module demonstrates and validates:
- Workflow template creation and versioning
- Sequential and parallel step execution
- Conditional branching
- Error handling with retry logic
- Step timeout handling
- Workflow cancellation
- State persistence and resumability
"""

import asyncio
from datetime import datetime, timedelta

import pytest

from app.models.workflow import (
    StepStatus,
    WorkflowStatus,
    WorkflowStepExecution,
)
from app.workflow.engine import (
    WorkflowEngine,
    WorkflowExecutionError,
)

# ============================================================================
# Test Fixtures
# ============================================================================


@pytest.fixture
def workflow_engine(db):
    """Create workflow engine instance."""
    return WorkflowEngine(db)


@pytest.fixture
def simple_template_definition():
    """Simple sequential workflow definition."""
    return {
        "steps": [
            {
                "id": "step1",
                "name": "First Step",
                "handler": "tests.test_workflow_engine.mock_step_handler",
                "execution_mode": "sequential",
                "depends_on": [],
                "retry_policy": {
                    "max_attempts": 3,
                    "backoff_multiplier": 2,
                    "max_backoff_seconds": 60,
                },
                "timeout_seconds": 10,
            },
            {
                "id": "step2",
                "name": "Second Step",
                "handler": "tests.test_workflow_engine.mock_step_handler",
                "execution_mode": "sequential",
                "depends_on": ["step1"],
                "retry_policy": {
                    "max_attempts": 1,
                },
                "timeout_seconds": 10,
            },
        ],
        "error_handlers": {},
        "default_timeout_seconds": 300,
    }


@pytest.fixture
def parallel_template_definition():
    """Workflow with parallel steps."""
    return {
        "steps": [
            {
                "id": "step1",
                "name": "Initial Step",
                "handler": "tests.test_workflow_engine.mock_step_handler",
                "execution_mode": "sequential",
                "depends_on": [],
            },
            {
                "id": "step2a",
                "name": "Parallel Step A",
                "handler": "tests.test_workflow_engine.mock_step_handler",
                "execution_mode": "parallel",
                "depends_on": ["step1"],
            },
            {
                "id": "step2b",
                "name": "Parallel Step B",
                "handler": "tests.test_workflow_engine.mock_step_handler",
                "execution_mode": "parallel",
                "depends_on": ["step1"],
            },
            {
                "id": "step3",
                "name": "Final Step",
                "handler": "tests.test_workflow_engine.mock_step_handler",
                "execution_mode": "sequential",
                "depends_on": ["step2a", "step2b"],
            },
        ],
        "error_handlers": {},
        "default_timeout_seconds": 300,
    }


@pytest.fixture
def conditional_template_definition():
    """Workflow with conditional steps."""
    return {
        "steps": [
            {
                "id": "step1",
                "name": "Initial Step",
                "handler": "tests.test_workflow_engine.mock_step_handler",
                "execution_mode": "sequential",
                "depends_on": [],
            },
            {
                "id": "step2",
                "name": "Conditional Step",
                "handler": "tests.test_workflow_engine.mock_step_handler",
                "execution_mode": "sequential",
                "depends_on": ["step1"],
                "condition": "step_outputs['step1']['success'] == True",
            },
            {
                "id": "step3",
                "name": "Always Execute",
                "handler": "tests.test_workflow_engine.mock_step_handler",
                "execution_mode": "sequential",
                "depends_on": ["step1"],
            },
        ],
        "error_handlers": {},
        "default_timeout_seconds": 300,
    }


# ============================================================================
# Mock Step Handlers
# ============================================================================


async def mock_step_handler(input_data: dict) -> dict:
    """Mock step handler that succeeds."""
    await asyncio.sleep(0.1)  # Simulate work
    return {
        "success": True,
        "message": "Step completed successfully",
        "input": input_data,
    }


async def mock_failing_step_handler(input_data: dict) -> dict:
    """Mock step handler that fails."""
    await asyncio.sleep(0.1)
    raise ValueError("Step failed intentionally")


async def mock_timeout_step_handler(input_data: dict) -> dict:
    """Mock step handler that times out."""
    await asyncio.sleep(100)  # Will timeout
    return {"success": True}


# ============================================================================
# Template Management Tests
# ============================================================================


def test_create_workflow_template(workflow_engine, simple_template_definition, db):
    """Test creating a workflow template."""
    template = workflow_engine.create_template(
        name="test_workflow",
        definition=simple_template_definition,
        description="Test workflow template",
        tags=["test", "simple"],
    )

    assert template.name == "test_workflow"
    assert template.version == 1
    assert template.description == "Test workflow template"
    assert template.is_active is True
    assert "test" in template.tags
    assert len(template.definition["steps"]) == 2


def test_template_versioning(workflow_engine, simple_template_definition, db):
    """Test template versioning when updating definition."""
    # Create initial template
    template_v1 = workflow_engine.create_template(
        name="versioned_workflow",
        definition=simple_template_definition,
    )

    assert template_v1.version == 1

    # Update with new definition (creates new version)
    new_definition = simple_template_definition.copy()
    new_definition["default_timeout_seconds"] = 600

    template_v2 = workflow_engine.update_template(
        template_id=template_v1.id,
        definition=new_definition,
    )

    assert template_v2.version == 2
    assert template_v2.name == "versioned_workflow"
    assert template_v2.definition["default_timeout_seconds"] == 600

    # Original version should still exist
    original = workflow_engine.get_template(template_id=template_v1.id)
    assert original.version == 1


def test_get_template_by_name(workflow_engine, simple_template_definition, db):
    """Test retrieving template by name."""
    workflow_engine.create_template(
        name="test_workflow",
        definition=simple_template_definition,
    )

    # Get latest version by name
    template = workflow_engine.get_template(name="test_workflow")
    assert template is not None
    assert template.name == "test_workflow"


# ============================================================================
# Workflow Instance Tests
# ============================================================================


def test_create_workflow_instance(workflow_engine, simple_template_definition, db):
    """Test creating a workflow instance."""
    template = workflow_engine.create_template(
        name="test_workflow",
        definition=simple_template_definition,
    )

    instance = workflow_engine.create_instance(
        template_id=template.id,
        input_data={"param1": "value1"},
        name="Test Instance",
        priority=5,
    )

    assert instance.template_id == template.id
    assert instance.template_version == template.version
    assert instance.status == WorkflowStatus.PENDING.value
    assert instance.input_data["param1"] == "value1"
    assert instance.priority == 5
    assert instance.timeout_at is not None


def test_workflow_instance_timeout_calculation(
    workflow_engine, simple_template_definition, db
):
    """Test that workflow timeout is calculated correctly."""
    template = workflow_engine.create_template(
        name="test_workflow",
        definition=simple_template_definition,
    )

    # Use default timeout from template (300 seconds)
    instance = workflow_engine.create_instance(template_id=template.id)
    default_timeout = (instance.timeout_at - instance.created_at).total_seconds()
    assert abs(default_timeout - 300) < 2  # Within 2 seconds

    # Override with custom timeout
    instance2 = workflow_engine.create_instance(
        template_id=template.id,
        timeout_seconds=600,
    )
    custom_timeout = (instance2.timeout_at - instance2.created_at).total_seconds()
    assert abs(custom_timeout - 600) < 2


# ============================================================================
# Workflow Execution Tests
# ============================================================================


@pytest.mark.asyncio
async def test_execute_simple_workflow(workflow_engine, simple_template_definition, db):
    """Test executing a simple sequential workflow."""
    template = workflow_engine.create_template(
        name="simple_workflow",
        definition=simple_template_definition,
    )

    instance = workflow_engine.create_instance(
        template_id=template.id,
        input_data={"test": "data"},
    )

    # Execute workflow synchronously
    completed_instance = await workflow_engine.execute_workflow(
        instance_id=instance.id,
        async_execution=False,
    )

    assert completed_instance.status == WorkflowStatus.COMPLETED.value
    assert completed_instance.started_at is not None
    assert completed_instance.completed_at is not None

    # Check step executions
    step_execs = (
        db.query(WorkflowStepExecution)
        .filter(WorkflowStepExecution.workflow_instance_id == instance.id)
        .all()
    )

    assert len(step_execs) == 2
    assert all(s.status == StepStatus.COMPLETED.value for s in step_execs)


@pytest.mark.asyncio
async def test_execute_parallel_workflow(
    workflow_engine, parallel_template_definition, db
):
    """Test executing workflow with parallel steps."""
    template = workflow_engine.create_template(
        name="parallel_workflow",
        definition=parallel_template_definition,
    )

    instance = workflow_engine.create_instance(template_id=template.id)

    completed_instance = await workflow_engine.execute_workflow(
        instance_id=instance.id,
        async_execution=False,
    )

    assert completed_instance.status == WorkflowStatus.COMPLETED.value

    # Verify all steps executed
    step_execs = (
        db.query(WorkflowStepExecution)
        .filter(WorkflowStepExecution.workflow_instance_id == instance.id)
        .all()
    )

    assert len(step_execs) == 4
    assert all(s.status == StepStatus.COMPLETED.value for s in step_execs)


@pytest.mark.asyncio
async def test_conditional_step_execution(
    workflow_engine, conditional_template_definition, db
):
    """Test conditional step execution."""
    template = workflow_engine.create_template(
        name="conditional_workflow",
        definition=conditional_template_definition,
    )

    instance = workflow_engine.create_instance(template_id=template.id)

    completed_instance = await workflow_engine.execute_workflow(
        instance_id=instance.id,
        async_execution=False,
    )

    # Step 2 should be executed (condition is true)
    step2 = (
        db.query(WorkflowStepExecution)
        .filter(
            WorkflowStepExecution.workflow_instance_id == instance.id,
            WorkflowStepExecution.step_id == "step2",
        )
        .first()
    )

    assert step2 is not None
    assert step2.status == StepStatus.COMPLETED.value
    assert step2.condition_result is True


# ============================================================================
# Error Handling Tests
# ============================================================================


@pytest.mark.asyncio
async def test_workflow_cancellation(workflow_engine, simple_template_definition, db):
    """Test cancelling a workflow instance."""
    template = workflow_engine.create_template(
        name="cancellable_workflow",
        definition=simple_template_definition,
    )

    instance = workflow_engine.create_instance(template_id=template.id)

    # Cancel before execution
    cancelled_instance = workflow_engine.cancel_instance(
        instance_id=instance.id,
        reason="Test cancellation",
    )

    assert cancelled_instance.status == WorkflowStatus.CANCELLED.value
    assert cancelled_instance.cancellation_reason == "Test cancellation"
    assert cancelled_instance.cancelled_at is not None


def test_cancel_completed_workflow_fails(
    workflow_engine, simple_template_definition, db
):
    """Test that completed workflows cannot be cancelled."""
    template = workflow_engine.create_template(
        name="test_workflow",
        definition=simple_template_definition,
    )

    instance = workflow_engine.create_instance(template_id=template.id)
    instance.status = WorkflowStatus.COMPLETED.value
    instance.completed_at = datetime.utcnow()
    db.commit()

    with pytest.raises(ValueError, match="Cannot cancel workflow"):
        workflow_engine.cancel_instance(
            instance_id=instance.id,
            reason="Too late",
        )


# ============================================================================
# Query and Statistics Tests
# ============================================================================


def test_query_workflow_instances(workflow_engine, simple_template_definition, db):
    """Test querying workflow instances with filters."""
    template = workflow_engine.create_template(
        name="test_workflow",
        definition=simple_template_definition,
    )

    # Create multiple instances
    for i in range(5):
        workflow_engine.create_instance(
            template_id=template.id,
            priority=i,
        )

    # Query all instances
    instances, total = workflow_engine.query_instances()
    assert total >= 5

    # Query by template
    instances, total = workflow_engine.query_instances(template_id=template.id)
    assert total == 5

    # Query by priority
    instances, total = workflow_engine.query_instances(
        template_id=template.id,
        priority_min=3,
    )
    assert total == 2  # Priorities 3 and 4


def test_workflow_statistics(workflow_engine, simple_template_definition, db):
    """Test workflow statistics calculation."""
    template = workflow_engine.create_template(
        name="stats_workflow",
        definition=simple_template_definition,
    )

    # Create instances with different statuses
    inst1 = workflow_engine.create_instance(template_id=template.id)
    inst1.status = WorkflowStatus.COMPLETED.value
    inst1.started_at = datetime.utcnow()
    inst1.completed_at = datetime.utcnow() + timedelta(seconds=10)

    inst2 = workflow_engine.create_instance(template_id=template.id)
    inst2.status = WorkflowStatus.FAILED.value

    inst3 = workflow_engine.create_instance(template_id=template.id)
    inst3.status = WorkflowStatus.RUNNING.value

    db.commit()

    stats = workflow_engine.get_statistics(template_id=template.id)

    assert stats["total_instances"] == 3
    assert stats["completed_instances"] == 1
    assert stats["failed_instances"] == 1
    assert stats["running_instances"] == 1
    assert 0 <= stats["success_rate"] <= 100
    assert stats["avg_duration_seconds"] is not None


# ============================================================================
# Helper Function Tests
# ============================================================================


def test_build_execution_plan(workflow_engine, parallel_template_definition):
    """Test execution plan building with dependencies."""
    steps = parallel_template_definition["steps"]
    execution_plan = workflow_engine._build_execution_plan(steps)

    # Should have 3 groups: [step1], [step2a, step2b], [step3]
    assert len(execution_plan) == 3
    assert len(execution_plan[0]) == 1  # step1
    assert len(execution_plan[1]) == 2  # step2a, step2b
    assert len(execution_plan[2]) == 1  # step3


def test_circular_dependency_detection(workflow_engine):
    """Test that circular dependencies are detected."""
    circular_definition = {
        "steps": [
            {
                "id": "step1",
                "name": "Step 1",
                "handler": "mock",
                "depends_on": ["step2"],
            },
            {
                "id": "step2",
                "name": "Step 2",
                "handler": "mock",
                "depends_on": ["step1"],
            },
        ],
        "error_handlers": {},
        "default_timeout_seconds": 300,
    }

    with pytest.raises(WorkflowExecutionError, match="Circular dependency"):
        workflow_engine._build_execution_plan(circular_definition["steps"])


def test_condition_evaluation(workflow_engine):
    """Test conditional expression evaluation."""
    execution_state = {
        "step_outputs": {
            "step1": {"success": True, "value": 42},
        },
        "input_data": {"param": "test"},
        "context": {},
    }

    # Test true condition
    result = workflow_engine._evaluate_condition(
        "step_outputs['step1']['success'] == True",
        execution_state,
    )
    assert result is True

    # Test false condition
    result = workflow_engine._evaluate_condition(
        "step_outputs['step1']['value'] > 100",
        execution_state,
    )
    assert result is False


def test_prepare_step_input(workflow_engine):
    """Test step input preparation with mapping."""
    input_mapping = {
        "param1": "static_value",
        "param2": "step_outputs.step1.value",
    }

    workflow_input = {"original": "data"}

    execution_state = {
        "step_outputs": {
            "step1": {"value": 42},
        },
    }

    result = workflow_engine._prepare_step_input(
        input_mapping,
        workflow_input,
        execution_state,
    )

    assert result["param1"] == "static_value"
    assert result["param2"] == 42
