"""Message Queue Integration Service.

Provides an abstraction layer for message queue systems supporting
both RabbitMQ and Redis backends.

Features:
- Abstract message queue interface
- Publisher with delivery guarantees
- Consumer with acknowledgment patterns
- Dead letter queue handling
- Message serialization/deserialization
- Retry policies for failed messages
- Topic-based message routing

This module enables reliable asynchronous messaging for the
Residency Scheduler application.
"""

from app.messaging.queue import (
    AckMode,
    DeliveryMode,
    MessageQueueAdapter,
    QueueConfig,
    RabbitMQAdapter,
    RedisQueueAdapter,
    RetryPolicy,
    create_queue_adapter,
)

__all__ = [
    "MessageQueueAdapter",
    "RabbitMQAdapter",
    "RedisQueueAdapter",
    "QueueConfig",
    "RetryPolicy",
    "AckMode",
    "DeliveryMode",
    "create_queue_adapter",
]
