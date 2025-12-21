"""
Distributed locking service using Redis.

This module provides distributed lock implementations for coordinating
concurrent operations across multiple processes and servers.

Key Features:
- Redis-based distributed locks with automatic expiration
- Reentrant lock support with token-based ownership
- Lock renewal/extension for long-running operations
- Automatic lock release via async context managers
- Fair locking with FIFO queue support
- Deadlock detection and monitoring
- Comprehensive metrics and observability

Example:
    from app.distributed import DistributedLock

    # Basic lock usage
    async with DistributedLock("my-resource", timeout=10) as lock:
        # Critical section - only one process can execute this
        await perform_critical_operation()

    # Reentrant lock usage
    lock = ReentrantLock("user:123:update", owner_id="worker-1")
    async with lock:
        # Can acquire same lock multiple times from same owner
        async with lock:
            await nested_operation()

    # Fair lock usage (FIFO queue)
    async with FairLock("schedule-generation", timeout=30) as lock:
        # Locks acquired in order they were requested
        await generate_schedule()
"""

from app.distributed.locks import (
    DeadlockDetector,
    DistributedLock,
    FairLock,
    LockAcquisitionError,
    LockError,
    LockMetrics,
    LockRenewalError,
    LockTimeoutError,
    ReentrantLock,
    get_lock_metrics,
)

__all__ = [
    "DistributedLock",
    "ReentrantLock",
    "FairLock",
    "LockError",
    "LockAcquisitionError",
    "LockTimeoutError",
    "LockRenewalError",
    "LockMetrics",
    "DeadlockDetector",
    "get_lock_metrics",
]
