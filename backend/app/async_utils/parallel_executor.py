"""Parallel execution utilities for concurrent async operations.

Provides utilities for running multiple async operations in parallel with
proper error handling and resource management.
"""
import asyncio
import logging
from typing import Any, Callable, Sequence, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


class ParallelExecutor:
    """Execute multiple async operations in parallel."""

    def __init__(self, max_concurrent: int = 10):
        """Initialize parallel executor.

        Args:
            max_concurrent: Maximum concurrent operations
        """
        self.max_concurrent = max_concurrent
        self.semaphore = asyncio.Semaphore(max_concurrent)

    async def map(
        self,
        func: Callable[[T], Any],
        items: Sequence[T],
        return_exceptions: bool = False,
    ) -> list[Any]:
        """Execute function on all items in parallel.

        Args:
            func: Async function to execute on each item
            items: Items to process
            return_exceptions: If True, return exceptions instead of raising

        Returns:
            List of results in same order as items
        """
        async def bounded_func(item):
            async with self.semaphore:
                return await func(item)

        tasks = [bounded_func(item) for item in items]
        results = await asyncio.gather(*tasks, return_exceptions=return_exceptions)

        logger.debug(f"Parallel map completed: {len(items)} items")
        return results

    async def map_chunked(
        self,
        func: Callable[[T], Any],
        items: Sequence[T],
        chunk_size: int,
    ) -> list[Any]:
        """Execute function on items in chunks.

        Args:
            func: Async function to execute
            items: Items to process
            chunk_size: Number of items per chunk

        Returns:
            List of all results
        """
        results = []

        for i in range(0, len(items), chunk_size):
            chunk = items[i : i + chunk_size]
            chunk_results = await self.map(func, chunk)
            results.extend(chunk_results)

            logger.debug(f"Processed chunk {i // chunk_size + 1}: {len(chunk)} items")

        return results

    async def run_parallel(
        self,
        *coroutines,
        return_exceptions: bool = False,
    ) -> tuple:
        """Run multiple coroutines in parallel.

        Args:
            *coroutines: Coroutines to execute
            return_exceptions: If True, return exceptions instead of raising

        Returns:
            Tuple of results
        """
        results = await asyncio.gather(*coroutines, return_exceptions=return_exceptions)
        logger.debug(f"Parallel execution completed: {len(coroutines)} coroutines")
        return results

    async def run_with_timeout(
        self,
        coroutine,
        timeout: float,
        default: Any = None,
    ) -> Any:
        """Run coroutine with timeout.

        Args:
            coroutine: Coroutine to execute
            timeout: Timeout in seconds
            default: Default value if timeout occurs

        Returns:
            Result or default on timeout
        """
        try:
            result = await asyncio.wait_for(coroutine, timeout=timeout)
            return result
        except asyncio.TimeoutError:
            logger.warning(f"Operation timed out after {timeout}s")
            return default

    async def run_with_retries(
        self,
        func: Callable,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        exponential_backoff: bool = True,
    ) -> Any:
        """Run function with retry logic.

        Args:
            func: Async function to execute
            max_retries: Maximum retry attempts
            retry_delay: Initial delay between retries
            exponential_backoff: If True, use exponential backoff

        Returns:
            Function result

        Raises:
            Exception from last retry attempt
        """
        last_exception = None

        for attempt in range(max_retries + 1):
            try:
                result = await func()
                return result
            except Exception as e:
                last_exception = e
                logger.warning(f"Attempt {attempt + 1}/{max_retries + 1} failed: {e}")

                if attempt < max_retries:
                    delay = retry_delay * (2 ** attempt) if exponential_backoff else retry_delay
                    await asyncio.sleep(delay)

        raise last_exception


class BatchedParallelExecutor:
    """Execute operations in batches with parallel processing."""

    def __init__(
        self,
        batch_size: int = 100,
        max_concurrent: int = 10,
    ):
        """Initialize batched parallel executor.

        Args:
            batch_size: Number of items per batch
            max_concurrent: Maximum concurrent operations per batch
        """
        self.batch_size = batch_size
        self.executor = ParallelExecutor(max_concurrent=max_concurrent)

    async def execute_batched(
        self,
        func: Callable[[Sequence[T]], Any],
        items: Sequence[T],
    ) -> list[Any]:
        """Execute function on items in batches.

        Args:
            func: Async function that processes a batch
            items: Items to process

        Returns:
            List of batch results
        """
        results = []

        for i in range(0, len(items), self.batch_size):
            batch = items[i : i + self.batch_size]
            result = await func(batch)
            results.append(result)

            logger.debug(
                f"Processed batch {i // self.batch_size + 1}: "
                f"{len(batch)} items"
            )

        return results

    async def execute_batched_parallel(
        self,
        func: Callable[[T], Any],
        items: Sequence[T],
    ) -> list[Any]:
        """Execute function on items with batching and parallelism.

        Args:
            func: Async function to execute on each item
            items: Items to process

        Returns:
            List of all results
        """
        all_results = []

        for i in range(0, len(items), self.batch_size):
            batch = items[i : i + self.batch_size]

            # Process batch in parallel
            batch_results = await self.executor.map(func, batch)
            all_results.extend(batch_results)

            logger.debug(
                f"Processed batch {i // self.batch_size + 1}: "
                f"{len(batch)} items in parallel"
            )

        return all_results


async def gather_with_concurrency(
    *coroutines,
    max_concurrent: int = 10,
    return_exceptions: bool = False,
) -> list[Any]:
    """Gather coroutines with concurrency limit.

    Args:
        *coroutines: Coroutines to execute
        max_concurrent: Maximum concurrent operations
        return_exceptions: If True, return exceptions instead of raising

    Returns:
        List of results
    """
    semaphore = asyncio.Semaphore(max_concurrent)

    async def bounded_coroutine(coro):
        async with semaphore:
            return await coro

    bounded_coroutines = [bounded_coroutine(coro) for coro in coroutines]
    return await asyncio.gather(*bounded_coroutines, return_exceptions=return_exceptions)


async def run_tasks_with_progress(
    tasks: Sequence[Callable],
    progress_callback: Optional[Callable[[int, int], None]] = None,
    max_concurrent: int = 10,
) -> list[Any]:
    """Run tasks with progress tracking.

    Args:
        tasks: List of async callables
        progress_callback: Optional callback(completed, total)
        max_concurrent: Maximum concurrent tasks

    Returns:
        List of results
    """
    total = len(tasks)
    completed = 0
    results = []

    semaphore = asyncio.Semaphore(max_concurrent)

    async def run_task(task):
        nonlocal completed

        async with semaphore:
            result = await task()
            completed += 1

            if progress_callback:
                progress_callback(completed, total)

            return result

    task_coroutines = [run_task(task) for task in tasks]
    results = await asyncio.gather(*task_coroutines)

    return results
