"""Async batch processing utilities for efficient data processing.

Provides utilities for processing large datasets in batches with
parallel execution and progress tracking.
"""

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable, Optional, Sequence, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")
R = TypeVar("R")


@dataclass
class BatchResult:
    """Result of batch processing."""

    total_items: int
    processed: int
    failed: int
    results: list[Any]
    errors: list[tuple[int, Exception]]
    duration_seconds: float
    batches_processed: int


class BatchProcessor:
    """Process items in batches with parallel execution."""

    def __init__(
        self,
        batch_size: int = 100,
        max_concurrent_batches: int = 5,
        stop_on_error: bool = False,
    ):
        """Initialize batch processor.

        Args:
            batch_size: Number of items per batch
            max_concurrent_batches: Maximum concurrent batches
            stop_on_error: If True, stop processing on first error
        """
        self.batch_size = batch_size
        self.max_concurrent_batches = max_concurrent_batches
        self.stop_on_error = stop_on_error

    async def process(
        self,
        items: Sequence[T],
        processor: Callable[[T], R],
        progress_callback: Callable[[int, int], None] | None = None,
    ) -> BatchResult:
        """Process items in batches.

        Args:
            items: Items to process
            processor: Async function to process each item
            progress_callback: Optional callback(processed, total)

        Returns:
            BatchResult with processing statistics
        """
        start_time = datetime.utcnow()
        total_items = len(items)
        results: list[Any] = []
        errors: list[tuple[int, Exception]] = []
        processed = 0
        batches_processed = 0

        # Create batches
        batches = [
            items[i : i + self.batch_size]
            for i in range(0, total_items, self.batch_size)
        ]

        # Process batches with concurrency limit
        semaphore = asyncio.Semaphore(self.max_concurrent_batches)

        async def process_batch(batch_idx: int, batch: Sequence[T]):
            nonlocal processed, batches_processed

            async with semaphore:
                batch_results = []
                batch_errors = []

                for item_idx, item in enumerate(batch):
                    global_idx = batch_idx * self.batch_size + item_idx

                    try:
                        result = await processor(item)
                        batch_results.append(result)
                        processed += 1

                        if progress_callback:
                            progress_callback(processed, total_items)

                    except Exception as e:
                        logger.error(f"Error processing item {global_idx}: {e}")
                        batch_errors.append((global_idx, e))

                        if self.stop_on_error:
                            raise

                batches_processed += 1
                return batch_results, batch_errors

        # Process all batches
        batch_tasks = [process_batch(idx, batch) for idx, batch in enumerate(batches)]

        batch_outputs = await asyncio.gather(*batch_tasks, return_exceptions=True)

        # Collect results and errors
        for output in batch_outputs:
            if isinstance(output, Exception):
                logger.error(f"Batch processing error: {output}")
                if self.stop_on_error:
                    break
            else:
                batch_results, batch_errors = output
                results.extend(batch_results)
                errors.extend(batch_errors)

        # Calculate duration
        duration = (datetime.utcnow() - start_time).total_seconds()

        logger.info(
            f"Batch processing complete: {processed}/{total_items} items "
            f"in {batches_processed} batches ({duration:.2f}s)"
        )

        return BatchResult(
            total_items=total_items,
            processed=processed,
            failed=len(errors),
            results=results,
            errors=errors,
            duration_seconds=duration,
            batches_processed=batches_processed,
        )

    async def process_with_retry(
        self,
        items: Sequence[T],
        processor: Callable[[T], R],
        max_retries: int = 3,
        retry_delay: float = 1.0,
    ) -> BatchResult:
        """Process items with automatic retry on failure.

        Args:
            items: Items to process
            processor: Async function to process each item
            max_retries: Maximum retry attempts per item
            retry_delay: Delay between retries in seconds

        Returns:
            BatchResult with processing statistics
        """

        async def processor_with_retry(item: T) -> R:
            last_error = None

            for attempt in range(max_retries + 1):
                try:
                    return await processor(item)
                except Exception as e:
                    last_error = e
                    if attempt < max_retries:
                        await asyncio.sleep(retry_delay * (2**attempt))

            raise last_error

        return await self.process(items, processor_with_retry)


class StreamingBatchProcessor:
    """Process items as they become available (streaming)."""

    def __init__(
        self,
        batch_size: int = 100,
        max_queue_size: int = 1000,
        flush_interval: float = 5.0,
    ):
        """Initialize streaming batch processor.

        Args:
            batch_size: Number of items per batch
            max_queue_size: Maximum queue size
            flush_interval: Flush interval in seconds
        """
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        self.queue: asyncio.Queue = asyncio.Queue(maxsize=max_queue_size)
        self.current_batch: list = []
        self.processor: Callable | None = None
        self._running = False
        self._worker_task: asyncio.Task | None = None

    async def start(self, processor: Callable[[Sequence[T]], Any]):
        """Start the streaming processor.

        Args:
            processor: Async function to process batches
        """
        if self._running:
            logger.warning("Streaming processor already running")
            return

        self.processor = processor
        self._running = True
        self._worker_task = asyncio.create_task(self._worker())

        logger.info("Streaming batch processor started")

    async def stop(self):
        """Stop the streaming processor."""
        self._running = False

        # Flush remaining items
        if self.current_batch:
            await self._flush_batch()

        # Wait for worker to finish
        if self._worker_task:
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass

        logger.info("Streaming batch processor stopped")

    async def add(self, item: T):
        """Add item to processing queue.

        Args:
            item: Item to process
        """
        await self.queue.put(item)

    async def _worker(self):
        """Worker loop to collect and process batches."""
        last_flush = datetime.utcnow()

        while self._running:
            try:
                # Get item with timeout
                try:
                    item = await asyncio.wait_for(
                        self.queue.get(),
                        timeout=1.0,
                    )
                    self.current_batch.append(item)
                except TimeoutError:
                    pass

                # Check if batch is full or flush interval reached
                now = datetime.utcnow()
                batch_full = len(self.current_batch) >= self.batch_size
                time_to_flush = (
                    now - last_flush
                ).total_seconds() >= self.flush_interval

                if batch_full or (time_to_flush and self.current_batch):
                    await self._flush_batch()
                    last_flush = now

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Streaming processor error: {e}", exc_info=True)

    async def _flush_batch(self):
        """Flush current batch."""
        if not self.current_batch or not self.processor:
            return

        batch = self.current_batch
        self.current_batch = []

        try:
            await self.processor(batch)
            logger.debug(f"Flushed batch of {len(batch)} items")
        except Exception as e:
            logger.error(f"Batch processing error: {e}", exc_info=True)


async def process_in_batches(
    items: Sequence[T],
    processor: Callable[[Sequence[T]], Any],
    batch_size: int = 100,
) -> list[Any]:
    """Simple utility to process items in batches.

    Args:
        items: Items to process
        processor: Async function that processes a batch
        batch_size: Number of items per batch

    Returns:
        List of batch results
    """
    results = []

    for i in range(0, len(items), batch_size):
        batch = items[i : i + batch_size]
        result = await processor(batch)
        results.append(result)

    return results
