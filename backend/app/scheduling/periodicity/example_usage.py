"""
Example Usage: Stroboscopic Schedule Manager

Demonstrates how to use the time crystal-inspired stroboscopic state manager
for managing schedule state with discrete checkpoint transitions.

This example shows:
1. Initializing the manager
2. Proposing draft changes
3. Advancing checkpoints atomically
4. Observing stable authoritative state
5. Handling concurrent access patterns
"""

import asyncio
from datetime import datetime

import redis.asyncio as redis

from app.events.event_bus import get_event_bus
from app.scheduling.periodicity import (
    CheckpointBoundary,
    ScheduleState,
    StroboscopicScheduleManager,
    create_stroboscopic_manager,
)


async def example_basic_usage():
    """
    Example 1: Basic stroboscopic state management.

    Shows the core workflow: propose draft → advance checkpoint → observe state
    """
    print("\n" + "=" * 80)
    print("Example 1: Basic Stroboscopic State Management")
    print("=" * 80)

    # Setup (in real usage, these come from FastAPI dependencies)
    event_bus = get_event_bus()
    redis_client = redis.from_url("redis://localhost:6379", decode_responses=True)

    # Note: db would be AsyncSession in real usage
    db = None  # Placeholder for this example

    # Create manager
    manager = await create_stroboscopic_manager(
        db=db,
        event_bus=event_bus,
        redis_client=redis_client,
        schedule_id="schedule-2024-q1",
        initialize_empty=True,
    )

    # Initial state (empty)
    print("\n1. Initial State:")
    current = await manager.get_observable_state()
    print(f"   State ID: {current.state_id}")
    print(f"   Assignments: {len(current.assignments)}")
    print(f"   Status: {current.status}")

    # Propose draft changes
    print("\n2. Proposing Draft Changes:")
    draft = await manager.propose_draft(
        assignments=[
            {
                "person_id": "person-001",
                "block_id": "block-001",
                "rotation_id": "clinic-am",
                "role": "primary",
            },
            {
                "person_id": "person-002",
                "block_id": "block-001",
                "rotation_id": "inpatient-am",
                "role": "primary",
            },
        ],
        metadata={"reason": "Initial schedule setup"},
        created_by="admin@example.com",
    )
    print(f"   Draft State ID: {draft.state_id}")
    print(f"   Draft Assignments: {len(draft.assignments)}")
    print(f"   Draft Status: {draft.status}")

    # Observer sees UNCHANGED state (stroboscopic!)
    print("\n3. Observable State (Still Old):")
    current = await manager.get_observable_state()
    print(f"   State ID: {current.state_id}")
    print(f"   Assignments: {len(current.assignments)}")
    print("   ✓ Draft does NOT affect observers")

    # Advance checkpoint - atomic transition
    print("\n4. Advancing Checkpoint (Atomic Transition):")
    success = await manager.advance_checkpoint(
        boundary=CheckpointBoundary.WEEK_START,
        triggered_by="example_script",
    )
    print(f"   Checkpoint Advanced: {success}")

    # Observer NOW sees new state
    print("\n5. Observable State (After Checkpoint):")
    current = await manager.get_observable_state()
    print(f"   State ID: {current.state_id}")
    print(f"   Assignments: {len(current.assignments)}")
    print(f"   Status: {current.status}")
    print("   ✓ State atomically transitioned at checkpoint")

    # Cleanup
    await redis_client.close()


async def example_concurrent_draft_and_observe():
    """
    Example 2: Concurrent draft proposals and observations.

    Shows how multiple processes can propose drafts and observe stable state
    without race conditions.
    """
    print("\n" + "=" * 80)
    print("Example 2: Concurrent Operations (No Race Conditions)")
    print("=" * 80)

    event_bus = get_event_bus()
    redis_client = redis.from_url("redis://localhost:6379", decode_responses=True)
    db = None

    manager = await create_stroboscopic_manager(
        db=db,
        event_bus=event_bus,
        redis_client=redis_client,
        schedule_id="schedule-2024-q2",
        initialize_empty=True,
    )

    async def observer_task():
        """Simulates an observer reading state."""
        for i in range(5):
            state = await manager.get_observable_state()
            print(
                f"   [Observer] Read state {state.state_id[:8]}... "
                f"({len(state.assignments)} assignments)"
            )
            await asyncio.sleep(0.1)

    async def draft_proposer_task():
        """Simulates a process proposing draft changes."""
        for i in range(3):
            await asyncio.sleep(0.15)
            draft = await manager.propose_draft(
                assignments=[{"person_id": f"person-{i:03d}", "block_id": "block-001"}],
                metadata={"iteration": i},
            )
            print(
                f"   [Proposer] Created draft {draft.state_id[:8]}... "
                f"({len(draft.assignments)} assignments)"
            )

    # Run observer and proposer concurrently
    print("\n1. Running concurrent observer and draft proposer:")
    await asyncio.gather(observer_task(), draft_proposer_task())

    print("\n   ✓ Observer always saw stable state, never saw in-progress drafts")

    await redis_client.close()


async def example_checkpoint_history():
    """
    Example 3: Checkpoint history and time-travel debugging.

    Shows how checkpoint history enables forensic analysis and debugging.
    """
    print("\n" + "=" * 80)
    print("Example 3: Checkpoint History (Time-Travel Debugging)")
    print("=" * 80)

    event_bus = get_event_bus()
    redis_client = redis.from_url("redis://localhost:6379", decode_responses=True)
    db = None

    manager = await create_stroboscopic_manager(
        db=db,
        event_bus=event_bus,
        redis_client=redis_client,
        schedule_id="schedule-2024-q3",
        initialize_empty=True,
    )

    # Create several checkpoints
    print("\n1. Creating Multiple Checkpoints:")
    for i in range(5):
        await manager.propose_draft(
            assignments=[
                {
                    "person_id": f"person-{j:03d}",
                    "block_id": f"block-{i:03d}",
                }
                for j in range(i + 1)
            ],
            metadata={"checkpoint_number": i},
        )

        await manager.advance_checkpoint(
            boundary=CheckpointBoundary.MANUAL,
            triggered_by=f"checkpoint_{i}",
        )
        print(f"   Checkpoint {i + 1}: {i + 1} assignments")

    # Review history
    print("\n2. Checkpoint History:")
    history = await manager.get_checkpoint_history(limit=10)
    for idx, state in enumerate(history):
        print(
            f"   [{idx}] State {state.state_id[:8]}... - "
            f"{len(state.assignments)} assignments - "
            f"{state.checkpoint_time.strftime('%H:%M:%S')}"
        )

    print("\n   ✓ Complete audit trail of all state transitions")

    await redis_client.close()


async def example_metrics_monitoring():
    """
    Example 4: Monitoring and observability.

    Shows how to get metrics for monitoring checkpoint health.
    """
    print("\n" + "=" * 80)
    print("Example 4: Metrics and Monitoring")
    print("=" * 80)

    event_bus = get_event_bus()
    redis_client = redis.from_url("redis://localhost:6379", decode_responses=True)
    db = None

    manager = await create_stroboscopic_manager(
        db=db,
        event_bus=event_bus,
        redis_client=redis_client,
        schedule_id="schedule-2024-q4",
        initialize_empty=True,
    )

    # Create some activity
    await manager.propose_draft(assignments=[{"person_id": "p1", "block_id": "b1"}])
    await manager.advance_checkpoint()

    await manager.propose_draft(assignments=[{"person_id": "p2", "block_id": "b2"}])
    await manager.advance_checkpoint()

    # Get metrics
    print("\n1. Manager Metrics:")
    metrics = await manager.get_metrics()
    for key, value in metrics.items():
        print(f"   {key}: {value}")

    print("\n   ✓ Full observability into checkpoint state")

    await redis_client.close()


async def run_all_examples():
    """Run all examples sequentially."""
    print("\n" + "=" * 80)
    print("STROBOSCOPIC SCHEDULE MANAGER - USAGE EXAMPLES")
    print("Time Crystal-Inspired State Management for Scheduling")
    print("=" * 80)

    try:
        await example_basic_usage()
        await example_concurrent_draft_and_observe()
        await example_checkpoint_history()
        await example_metrics_monitoring()

        print("\n" + "=" * 80)
        print("ALL EXAMPLES COMPLETED SUCCESSFULLY")
        print("=" * 80)
        print(
            """
Key Takeaways:
1. Draft changes don't affect observers (stroboscopic observation)
2. Checkpoints are atomic transitions with distributed locking
3. Complete history enables time-travel debugging
4. Thread-safe across multiple processes/servers
5. Full observability through metrics

Next Steps:
- Integrate with actual Schedule/Assignment models
- Add ACGME validation hooks
- Set up automatic checkpoint scheduling (Celery beat)
- Add checkpoint event handlers for notifications
        """
        )

    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    # Run examples
    asyncio.run(run_all_examples())
