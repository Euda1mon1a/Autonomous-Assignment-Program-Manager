"""
Example: Using Async Task Tools

This script demonstrates how to use the MCP async task tools to start
background tasks and poll for their completion.

Prerequisites:
1. Redis must be running
2. Celery worker must be running
3. MCP server dependencies must be installed

Setup:
    # Start Redis
    docker-compose up -d redis

    # Start Celery worker
    cd backend
    ../scripts/start-celery.sh worker

    # Run this example
    cd mcp-server
    python examples/async_task_example.py
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path so we can import Celery app
backend_path = Path(__file__).parent.parent.parent / "backend"
sys.path.insert(0, str(backend_path))

# Import async tools
from scheduler_mcp.async_tools import (
    TaskType,
    start_background_task,
    get_task_status,
    list_active_tasks,
    cancel_task,
)


async def example_1_health_check():
    """Example 1: Start a health check and wait for completion."""
    print("\n" + "=" * 60)
    print("Example 1: Resilience Health Check")
    print("=" * 60)

    # Start health check
    print("\nStarting health check...")
    result = await start_background_task(
        task_type=TaskType.RESILIENCE_HEALTH_CHECK,
        params={}
    )

    task_id = result.task_id
    print(f"✓ Task started: {task_id}")
    print(f"  Estimated duration: {result.estimated_duration}")

    # Poll for completion
    print("\nPolling for completion...")
    max_attempts = 30
    poll_interval = 5

    for attempt in range(max_attempts):
        await asyncio.sleep(poll_interval)

        status = await get_task_status(task_id)
        print(f"  [{attempt + 1}/{max_attempts}] Status: {status.status.value}, Progress: {status.progress}%")

        if status.status.value == "success":
            print("\n✓ Task completed successfully!")
            print(f"\nResult:")
            print(f"  Overall Status: {status.result.get('status', 'N/A')}")
            print(f"  Utilization: {status.result.get('utilization', 'N/A')}")
            print(f"  Defense Level: {status.result.get('defense_level', 'N/A')}")
            print(f"  N-1 Pass: {status.result.get('n1_pass', 'N/A')}")
            print(f"  N-2 Pass: {status.result.get('n2_pass', 'N/A')}")
            return status.result

        elif status.status.value == "failure":
            print(f"\n✗ Task failed: {status.error}")
            return None

    print("\n⚠ Task timed out (still running)")
    return None


async def example_2_contingency_analysis():
    """Example 2: Run contingency analysis with parameters."""
    print("\n" + "=" * 60)
    print("Example 2: Contingency Analysis (90 days ahead)")
    print("=" * 60)

    # Start contingency analysis
    print("\nStarting contingency analysis...")
    result = await start_background_task(
        task_type=TaskType.RESILIENCE_CONTINGENCY,
        params={"days_ahead": 90}
    )

    task_id = result.task_id
    print(f"✓ Task started: {task_id}")

    # Poll for completion
    print("\nPolling for completion...")
    max_attempts = 60  # 5 minutes max
    poll_interval = 5

    for attempt in range(max_attempts):
        await asyncio.sleep(poll_interval)

        status = await get_task_status(task_id)
        print(f"  [{attempt + 1}/{max_attempts}] Status: {status.status.value}, Progress: {status.progress}%")

        if status.status.value == "success":
            print("\n✓ Contingency analysis completed!")
            print(f"\nResults:")
            print(f"  N-1 Pass: {status.result.get('n1_pass', 'N/A')}")
            print(f"  N-1 Vulnerabilities: {status.result.get('n1_vulnerabilities_count', 0)}")
            print(f"  N-2 Pass: {status.result.get('n2_pass', 'N/A')}")
            print(f"  N-2 Fatal Pairs: {status.result.get('n2_fatal_pairs_count', 0)}")
            print(f"  Phase Transition Risk: {status.result.get('phase_transition_risk', 'N/A')}")
            return status.result

        elif status.status.value == "failure":
            print(f"\n✗ Task failed: {status.error}")
            return None

    print("\n⚠ Task timed out (still running)")
    return None


async def example_3_metrics_computation():
    """Example 3: Compute schedule metrics for a date range."""
    print("\n" + "=" * 60)
    print("Example 3: Schedule Metrics Computation")
    print("=" * 60)

    # Start metrics computation
    print("\nStarting metrics computation...")
    result = await start_background_task(
        task_type=TaskType.METRICS_COMPUTATION,
        params={
            "start_date": "2025-01-01",
            "end_date": "2025-03-31"
        }
    )

    task_id = result.task_id
    print(f"✓ Task started: {task_id}")

    # Poll for completion
    print("\nPolling for completion...")
    max_attempts = 60
    poll_interval = 5

    for attempt in range(max_attempts):
        await asyncio.sleep(poll_interval)

        status = await get_task_status(task_id)
        print(f"  [{attempt + 1}/{max_attempts}] Status: {status.status.value}, Progress: {status.progress}%")

        if status.status.value == "success":
            print("\n✓ Metrics computation completed!")

            if status.result:
                schedule_analysis = status.result.get("schedule_analysis", {})
                metrics = schedule_analysis.get("metrics", {})

                print(f"\nMetrics:")
                if "fairness" in metrics:
                    print(f"  Fairness: {metrics['fairness'].get('value', 'N/A')}")
                if "coverage" in metrics:
                    print(f"  Coverage: {metrics['coverage'].get('value', 'N/A')}")
                if "compliance" in metrics:
                    print(f"  Compliance: {metrics['compliance'].get('value', 'N/A')}")

                stability = status.result.get("stability_metrics", {})
                if stability:
                    print(f"\nStability:")
                    print(f"  Grade: {stability.get('stability_grade', 'N/A')}")
                    print(f"  Churn Rate: {stability.get('churn_rate', 'N/A')}")

            return status.result

        elif status.status.value == "failure":
            print(f"\n✗ Task failed: {status.error}")
            return None

    print("\n⚠ Task timed out (still running)")
    return None


async def example_4_list_active_tasks():
    """Example 4: List all active tasks."""
    print("\n" + "=" * 60)
    print("Example 4: List Active Tasks")
    print("=" * 60)

    print("\nQuerying active tasks...")
    result = await list_active_tasks()

    print(f"\nTotal active tasks: {result.total_active}")

    if result.total_active > 0:
        print("\nActive tasks:")
        for task in result.tasks:
            print(f"  - {task.task_id[:8]}... ({task.task_type})")
            print(f"    Status: {task.status}")
            if task.started_at:
                print(f"    Started: {task.started_at}")
    else:
        print("  (No active tasks)")

    return result


async def example_5_cancel_task():
    """Example 5: Start a task and then cancel it."""
    print("\n" + "=" * 60)
    print("Example 5: Cancel a Task")
    print("=" * 60)

    # Start a long-running task
    print("\nStarting fallback precomputation (long-running)...")
    result = await start_background_task(
        task_type=TaskType.RESILIENCE_FALLBACK_PRECOMPUTE,
        params={"days_ahead": 90}
    )

    task_id = result.task_id
    print(f"✓ Task started: {task_id}")

    # Wait a bit
    print("\nWaiting 3 seconds...")
    await asyncio.sleep(3)

    # Cancel the task
    print(f"\nCanceling task {task_id[:8]}...")
    cancel_result = await cancel_task(task_id)

    print(f"✓ {cancel_result.message}")

    # Verify cancellation
    await asyncio.sleep(2)
    status = await get_task_status(task_id)
    print(f"\nVerification - Task status: {status.status.value}")

    return cancel_result


async def main():
    """Run all examples."""
    print("\n" + "=" * 60)
    print("MCP Async Task Tools - Examples")
    print("=" * 60)

    try:
        # Example 1: Health check
        await example_1_health_check()

        # Example 2: Contingency analysis
        await example_2_contingency_analysis()

        # Example 3: Metrics computation
        await example_3_metrics_computation()

        # Example 4: List active tasks
        await example_4_list_active_tasks()

        # Example 5: Cancel task
        await example_5_cancel_task()

        print("\n" + "=" * 60)
        print("All examples completed!")
        print("=" * 60)

    except ImportError as e:
        print(f"\n✗ Import error: {e}")
        print("\nMake sure:")
        print("  1. Backend dependencies are installed")
        print("  2. PYTHONPATH includes the backend directory")
        print(f"\n  export PYTHONPATH={backend_path}:$PYTHONPATH")

    except ConnectionError as e:
        print(f"\n✗ Connection error: {e}")
        print("\nMake sure:")
        print("  1. Redis is running: docker-compose up -d redis")
        print("  2. Celery worker is running: cd backend && ../scripts/start-celery.sh worker")

    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
