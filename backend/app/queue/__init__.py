"""
Async Task Queue System.

Provides advanced task queue functionality including:
- Task priority levels (low, normal, high, critical)
- Delayed execution and scheduling
- Task dependencies and chaining
- Enhanced retry policies with exponential backoff
- Dead letter queue for failed tasks
- Task cancellation and revocation
- Progress tracking and monitoring
- Task status management
- Multi-priority queue support
- Job deduplication
- Fair scheduling across priorities
- Comprehensive queue metrics

This module extends Celery with additional features for managing
complex task workflows in the residency scheduler application.
"""

from app.queue.manager import QueueManager
from app.queue.priority_queue import (
    DeadLetterRecord,
    FairSchedulingPolicy,
    JobMetadata,
    JobPriority,
    JobState,
    PriorityQueueManager,
    QueueMetrics,
)
from app.queue.scheduler import TaskScheduler
from app.queue.tasks import (
    BaseQueueTask,
    TaskPriority,
    TaskStatus,
    create_task_chain,
    create_task_group,
)
from app.queue.workers import WorkerManager

__all__ = [
    "QueueManager",
    "TaskScheduler",
    "WorkerManager",
    "BaseQueueTask",
    "TaskPriority",
    "TaskStatus",
    "create_task_chain",
    "create_task_group",
    # Priority Queue
    "PriorityQueueManager",
    "JobPriority",
    "JobState",
    "JobMetadata",
    "QueueMetrics",
    "DeadLetterRecord",
    "FairSchedulingPolicy",
]
