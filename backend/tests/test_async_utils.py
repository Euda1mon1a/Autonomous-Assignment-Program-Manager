"""Tests for async optimization utilities."""

import asyncio
import pytest
import time

from app.async_utils.batch_processor import BatchProcessor, process_in_batches
from app.async_utils.parallel_executor import ParallelExecutor, gather_with_concurrency
from app.async_utils.semaphore_pool import SemaphorePool, RateLimiter
from app.async_utils.task_queue import TaskQueue, TaskPriority


@pytest.mark.asyncio
async def test_batch_processor():
    """Test batch processing of items."""
    processor = BatchProcessor(batch_size=10, max_concurrent_batches=2)

    processed_items = []

    async def process_item(item: int) -> int:
        await asyncio.sleep(0.01)
        processed_items.append(item)
        return item * 2

    # Process 25 items
    items = list(range(25))
    result = await processor.process(items, process_item)

    assert result.total_items == 25
    assert result.processed == 25
    assert result.failed == 0
    assert len(result.results) == 25
    assert set(processed_items) == set(items)


@pytest.mark.asyncio
async def test_batch_processor_with_errors():
    """Test batch processor error handling."""
    processor = BatchProcessor(batch_size=5, stop_on_error=False)

    async def process_item(item: int) -> int:
        if item % 3 == 0:
            raise ValueError(f"Error processing {item}")
        return item * 2

    items = list(range(10))
    result = await processor.process(items, process_item)

    # Items 0, 3, 6, 9 should fail (4 failures)
    assert result.processed == 6
    assert result.failed == 4
    assert len(result.errors) == 4


@pytest.mark.asyncio
async def test_parallel_executor():
    """Test parallel execution of operations."""
    executor = ParallelExecutor(max_concurrent=5)

    async def slow_operation(n: int) -> int:
        await asyncio.sleep(0.05)
        return n * 2

    items = list(range(20))
    results = await executor.map(slow_operation, items)

    assert len(results) == 20
    assert results == [i * 2 for i in items]


@pytest.mark.asyncio
async def test_parallel_executor_concurrency_limit():
    """Test that parallel executor respects concurrency limit."""
    max_concurrent = 3
    executor = ParallelExecutor(max_concurrent=max_concurrent)

    active_count = 0
    max_active = 0

    async def track_concurrency(n: int) -> int:
        nonlocal active_count, max_active

        active_count += 1
        max_active = max(max_active, active_count)

        await asyncio.sleep(0.05)

        active_count -= 1
        return n

    items = list(range(10))
    await executor.map(track_concurrency, items)

    # Should never exceed max_concurrent
    assert max_active <= max_concurrent


@pytest.mark.asyncio
async def test_semaphore_pool():
    """Test semaphore pool for resource management."""
    pool = SemaphorePool(max_concurrent=3)

    active_count = 0
    max_active = 0

    async def operation():
        nonlocal active_count, max_active

        async with pool.acquire():
            active_count += 1
            max_active = max(max_active, active_count)

            await asyncio.sleep(0.05)

            active_count -= 1

    # Run 10 operations
    await asyncio.gather(*[operation() for _ in range(10)])

    assert max_active <= 3

    # Check stats
    stats = await pool.get_stats()
    assert stats["total_acquisitions"] == 10


@pytest.mark.asyncio
async def test_rate_limiter():
    """Test rate limiter throttles requests."""
    limiter = RateLimiter(rate=5, per=1.0)  # 5 per second

    start_time = time.time()

    # Try to make 10 requests
    for _ in range(10):
        await limiter.acquire()

    elapsed = time.time() - start_time

    # Should take at least 1 second (5 requests in first second, 5 in second)
    assert elapsed >= 1.0

    stats = await limiter.get_stats()
    assert stats["total_requests"] == 10
    assert stats["allowed"] == 10


@pytest.mark.asyncio
async def test_task_queue():
    """Test task queue with priorities."""
    queue = TaskQueue(max_concurrent=2)

    results = []

    async def task(name: str):
        await asyncio.sleep(0.01)
        results.append(name)

    # Start queue
    await queue.start()

    try:
        # Enqueue tasks with different priorities
        await queue.enqueue(task, "low", priority=TaskPriority.LOW)
        await queue.enqueue(task, "high", priority=TaskPriority.HIGH)
        await queue.enqueue(task, "normal", priority=TaskPriority.NORMAL)
        await queue.enqueue(task, "critical", priority=TaskPriority.CRITICAL)

        # Wait for processing
        await asyncio.sleep(0.5)

        # Higher priority tasks should be processed first
        assert "critical" in results
        assert "high" in results

    finally:
        await queue.stop()


@pytest.mark.asyncio
async def test_gather_with_concurrency():
    """Test concurrent gathering with limit."""
    max_concurrent = 3
    active_count = 0
    max_active = 0

    async def operation(n: int) -> int:
        nonlocal active_count, max_active

        active_count += 1
        max_active = max(max_active, active_count)

        await asyncio.sleep(0.05)

        active_count -= 1
        return n * 2

    coroutines = [operation(i) for i in range(10)]
    results = await gather_with_concurrency(
        *coroutines,
        max_concurrent=max_concurrent,
    )

    assert len(results) == 10
    assert max_active <= max_concurrent


@pytest.mark.asyncio
async def test_process_in_batches():
    """Test simple batch processing utility."""
    processed_batches = []

    async def process_batch(batch):
        processed_batches.append(len(batch))
        return sum(batch)

    items = list(range(25))
    results = await process_in_batches(items, process_batch, batch_size=10)

    # Should create 3 batches: 10, 10, 5
    assert len(processed_batches) == 3
    assert processed_batches == [10, 10, 5]
    assert len(results) == 3
