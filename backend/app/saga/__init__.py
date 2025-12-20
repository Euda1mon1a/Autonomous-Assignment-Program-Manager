"""Saga orchestration for distributed transactions.

This package provides a complete saga pattern implementation with:

Key Features:
- Saga definition with steps and compensations
- Saga orchestrator for step execution
- Saga state persistence for crash recovery
- Compensation rollback on failure
- Saga and step timeout handling
- Parallel step execution
- Automatic retry with exponential backoff
- Saga execution logging and monitoring

Usage Example:
    ```python
    from app.saga import (
        SagaOrchestrator,
        SagaDefinition,
        SagaStepDefinition,
    )

    # Define saga steps
    async def create_order(data: dict) -> dict:
        # Business logic here
        return {"order_id": "123"}

    async def compensate_order(data: dict) -> None:
        # Rollback logic here
        pass

    async def reserve_inventory(data: dict) -> dict:
        # Business logic here
        return {"reservation_id": "456"}

    async def compensate_inventory(data: dict) -> None:
        # Rollback logic here
        pass

    async def process_payment(data: dict) -> dict:
        # Business logic here
        return {"payment_id": "789"}

    async def compensate_payment(data: dict) -> None:
        # Rollback logic here
        pass

    # Create saga definition
    saga_def = SagaDefinition(
        name="order_processing",
        description="Process customer order with payment",
        steps=[
            SagaStepDefinition(
                name="create_order",
                action=create_order,
                compensation=compensate_order,
                timeout_seconds=30,
                retry_attempts=3,
            ),
            SagaStepDefinition(
                name="reserve_inventory",
                action=reserve_inventory,
                compensation=compensate_inventory,
                timeout_seconds=30,
                retry_attempts=3,
            ),
            SagaStepDefinition(
                name="process_payment",
                action=process_payment,
                compensation=compensate_payment,
                timeout_seconds=60,
                retry_attempts=2,
            ),
        ],
        timeout_seconds=300,  # 5 minutes total
    )

    # Execute saga
    from sqlalchemy.orm import Session

    def execute_order_saga(db: Session, order_data: dict):
        orchestrator = SagaOrchestrator(db)
        orchestrator.register_saga(saga_def)

        result = await orchestrator.execute_saga(
            saga_name="order_processing",
            input_data=order_data,
            metadata={"user_id": "user123", "trace_id": "abc123"},
        )

        if result.is_successful:
            print(f"Order processed successfully: {result.saga_id}")
        else:
            print(f"Order failed: {result.error_message}")
            print(f"Compensated {result.compensated_steps} steps")
    ```

Parallel Execution Example:
    ```python
    # Steps in the same parallel_group execute concurrently
    saga_def = SagaDefinition(
        name="multi_service_update",
        steps=[
            SagaStepDefinition(
                name="update_service_a",
                action=update_service_a,
                compensation=rollback_service_a,
                parallel_group="updates",  # Executes in parallel
            ),
            SagaStepDefinition(
                name="update_service_b",
                action=update_service_b,
                compensation=rollback_service_b,
                parallel_group="updates",  # Executes in parallel
            ),
            SagaStepDefinition(
                name="update_service_c",
                action=update_service_c,
                compensation=rollback_service_c,
                parallel_group="updates",  # Executes in parallel
            ),
            SagaStepDefinition(
                name="notify_completion",
                action=send_notification,
                # Executes after parallel group completes
            ),
        ],
    )
    ```

Recovery After Service Restart:
    ```python
    # On service startup, recover interrupted sagas
    orchestrator = SagaOrchestrator(db)
    recovered_saga_ids = await orchestrator.recover_pending_sagas()
    print(f"Recovered {len(recovered_saga_ids)} interrupted sagas")
    ```

Monitoring Saga Status:
    ```python
    # Check saga status
    result = await orchestrator.get_saga_status(saga_id)
    if result:
        print(f"Status: {result.status}")
        print(f"Duration: {result.duration_seconds}s")
        for step in result.step_results:
            print(f"  Step {step.step_name}: {step.status}")
    ```

Architecture:
-----------
The saga orchestrator follows the orchestration pattern (not choreography),
where a central orchestrator manages the workflow:

1. **Sequential Execution**: Steps execute one after another
2. **Parallel Execution**: Steps in the same parallel_group execute concurrently
3. **Compensation**: On failure, completed steps are compensated in reverse order
4. **State Persistence**: All state is persisted to enable crash recovery
5. **Idempotency**: Steps can be safely retried if marked as idempotent
6. **Timeouts**: Both saga and individual steps have configurable timeouts

Database Models:
---------------
- `SagaExecution`: Persists saga state
- `SagaStepExecution`: Persists individual step state
- `SagaEvent`: Event log for monitoring and debugging

See also:
- docs/ARCHITECTURE.md for system design
- docs/SAGA_PATTERN.md for detailed documentation
"""

from app.saga.models import SagaEvent, SagaExecution, SagaStepExecution
from app.saga.orchestrator import (
    SagaCompensationError,
    SagaOrchestrator,
    SagaTimeoutError,
)
from app.saga.types import (
    SagaContext,
    SagaDefinition,
    SagaExecutionResult,
    SagaStatus,
    SagaStepDefinition,
    SagaStepResult,
    StepStatus,
    StepType,
)

__all__ = [
    # Orchestrator
    "SagaOrchestrator",
    "SagaTimeoutError",
    "SagaCompensationError",
    # Types
    "SagaDefinition",
    "SagaStepDefinition",
    "SagaContext",
    "SagaExecutionResult",
    "SagaStepResult",
    "SagaStatus",
    "StepStatus",
    "StepType",
    # Models
    "SagaExecution",
    "SagaStepExecution",
    "SagaEvent",
]
