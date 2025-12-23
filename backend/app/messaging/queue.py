"""Message queue integration service.

Provides abstract message queue interface with implementations for
RabbitMQ and Redis, supporting reliable messaging patterns.
"""

import asyncio
import json
import logging
import time
from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class AckMode(str, Enum):
    """Message acknowledgment modes."""

    AUTO = "auto"  # Automatic acknowledgment
    MANUAL = "manual"  # Manual acknowledgment required
    NONE = "none"  # No acknowledgment (fire and forget)


class DeliveryMode(int, Enum):
    """Message delivery modes."""

    TRANSIENT = 1  # Non-persistent (faster, may be lost on restart)
    PERSISTENT = 2  # Persistent (survives broker restart)


@dataclass
class RetryPolicy:
    """Retry policy for failed messages.

    Attributes:
        max_retries: Maximum number of retry attempts
        initial_delay: Initial delay in seconds before first retry
        max_delay: Maximum delay in seconds between retries
        exponential_base: Base for exponential backoff (e.g., 2 for doubling)
        jitter: Add random jitter to prevent thundering herd (0.0 to 1.0)
    """

    max_retries: int = 3
    initial_delay: float = 1.0
    max_delay: float = 300.0
    exponential_base: float = 2.0
    jitter: float = 0.1

    def get_delay(self, attempt: int) -> float:
        """
        Calculate delay for given retry attempt.

        Args:
            attempt: Retry attempt number (0-indexed)

        Returns:
            Delay in seconds with exponential backoff and jitter
        """
        import random

        # Exponential backoff: initial_delay * (base ^ attempt)
        delay = min(
            self.initial_delay * (self.exponential_base**attempt), self.max_delay
        )

        # Add jitter to prevent thundering herd
        if self.jitter > 0:
            jitter_amount = delay * self.jitter * random.random()
            delay += jitter_amount

        return delay


@dataclass
class QueueConfig:
    """Configuration for message queue connection.

    Attributes:
        backend: Queue backend type ("rabbitmq" or "redis")
        url: Connection URL (e.g., "amqp://user:pass@host:port/vhost")
        exchange: Default exchange name (RabbitMQ only)
        exchange_type: Exchange type (RabbitMQ: "direct", "topic", "fanout", "headers")
        default_queue: Default queue name
        dlx_exchange: Dead letter exchange name
        dlx_queue: Dead letter queue name
        prefetch_count: Number of messages to prefetch (consumer side)
        message_ttl: Message time-to-live in milliseconds (None = no expiration)
        max_priority: Maximum message priority (0-255, None = disabled)
        connection_timeout: Connection timeout in seconds
        reconnect_delay: Delay before reconnection attempt in seconds
    """

    backend: str = "redis"
    url: str = "redis://localhost:6379/0"
    exchange: str = "scheduler.events"
    exchange_type: str = "topic"
    default_queue: str = "scheduler.default"
    dlx_exchange: str = "scheduler.dlx"
    dlx_queue: str = "scheduler.dead_letters"
    prefetch_count: int = 10
    message_ttl: int | None = None
    max_priority: int | None = 10
    connection_timeout: float = 30.0
    reconnect_delay: float = 5.0

    @classmethod
    def from_env(cls) -> "QueueConfig":
        """Load configuration from environment variables."""
        import os

        backend = os.getenv("MESSAGE_QUEUE_BACKEND", "redis")
        url = os.getenv("MESSAGE_QUEUE_URL", "redis://localhost:6379/0")

        return cls(
            backend=backend,
            url=url,
            exchange=os.getenv("MESSAGE_QUEUE_EXCHANGE", "scheduler.events"),
            exchange_type=os.getenv("MESSAGE_QUEUE_EXCHANGE_TYPE", "topic"),
            default_queue=os.getenv("MESSAGE_QUEUE_DEFAULT_QUEUE", "scheduler.default"),
            dlx_exchange=os.getenv("MESSAGE_QUEUE_DLX_EXCHANGE", "scheduler.dlx"),
            dlx_queue=os.getenv("MESSAGE_QUEUE_DLX_QUEUE", "scheduler.dead_letters"),
            prefetch_count=int(os.getenv("MESSAGE_QUEUE_PREFETCH_COUNT", "10")),
            message_ttl=int(os.getenv("MESSAGE_QUEUE_TTL", "0")) or None,
            max_priority=int(os.getenv("MESSAGE_QUEUE_MAX_PRIORITY", "10")) or None,
            connection_timeout=float(os.getenv("MESSAGE_QUEUE_TIMEOUT", "30.0")),
            reconnect_delay=float(os.getenv("MESSAGE_QUEUE_RECONNECT_DELAY", "5.0")),
        )


@dataclass
class Message:
    """Message envelope with metadata.

    Attributes:
        body: Message body (will be JSON serialized)
        routing_key: Routing key for message delivery
        headers: Message headers/metadata
        delivery_mode: Delivery mode (transient or persistent)
        priority: Message priority (0-255, higher = more important)
        correlation_id: Correlation ID for request/reply patterns
        reply_to: Reply queue name for RPC patterns
        expiration: Message expiration time in milliseconds
        message_id: Unique message identifier
        timestamp: Message creation timestamp
        content_type: Content type (default: application/json)
        content_encoding: Content encoding (default: utf-8)
    """

    body: Any
    routing_key: str = ""
    headers: dict[str, Any] = field(default_factory=dict)
    delivery_mode: DeliveryMode = DeliveryMode.PERSISTENT
    priority: int = 5
    correlation_id: str | None = None
    reply_to: str | None = None
    expiration: int | None = None
    message_id: str | None = None
    timestamp: datetime | None = None
    content_type: str = "application/json"
    content_encoding: str = "utf-8"

    def __post_init__(self):
        """Set defaults after initialization."""
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()
        if self.message_id is None:
            import uuid

            self.message_id = str(uuid.uuid4())


class MessageQueueAdapter(ABC):
    """Abstract base class for message queue adapters."""

    def __init__(self, config: QueueConfig):
        """
        Initialize message queue adapter.

        Args:
            config: Queue configuration
        """
        self.config = config
        self._connected = False
        self._closing = False

    @abstractmethod
    async def connect(self) -> None:
        """Establish connection to message queue."""
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """Close connection to message queue."""
        pass

    @abstractmethod
    async def publish(
        self,
        message: Message,
        exchange: str | None = None,
        routing_key: str | None = None,
    ) -> bool:
        """
        Publish message to queue.

        Args:
            message: Message to publish
            exchange: Exchange name (overrides default)
            routing_key: Routing key (overrides message.routing_key)

        Returns:
            True if message was published successfully
        """
        pass

    @abstractmethod
    async def consume(
        self,
        queue: str,
        callback: Callable[[dict[str, Any], dict[str, Any]], Any],
        ack_mode: AckMode = AckMode.MANUAL,
    ) -> None:
        """
        Consume messages from queue.

        Args:
            queue: Queue name to consume from
            callback: Async callback function(body, metadata) -> None
            ack_mode: Acknowledgment mode
        """
        pass

    @abstractmethod
    async def ack(self, delivery_tag: Any) -> None:
        """
        Acknowledge message processing.

        Args:
            delivery_tag: Message delivery tag
        """
        pass

    @abstractmethod
    async def nack(
        self, delivery_tag: Any, requeue: bool = True, multiple: bool = False
    ) -> None:
        """
        Negative acknowledge (reject) message.

        Args:
            delivery_tag: Message delivery tag
            requeue: Whether to requeue the message
            multiple: Whether to nack multiple messages
        """
        pass

    @abstractmethod
    async def declare_queue(
        self,
        queue: str,
        durable: bool = True,
        auto_delete: bool = False,
        arguments: dict[str, Any] | None = None,
    ) -> None:
        """
        Declare a queue.

        Args:
            queue: Queue name
            durable: Queue survives broker restart
            auto_delete: Queue is deleted when last consumer unsubscribes
            arguments: Additional queue arguments
        """
        pass

    @abstractmethod
    async def bind_queue(
        self, queue: str, exchange: str, routing_key: str = ""
    ) -> None:
        """
        Bind queue to exchange with routing key.

        Args:
            queue: Queue name
            exchange: Exchange name
            routing_key: Routing key pattern
        """
        pass

    @abstractmethod
    async def purge_queue(self, queue: str) -> int:
        """
        Purge all messages from queue.

        Args:
            queue: Queue name

        Returns:
            Number of messages purged
        """
        pass

    def serialize_message(self, message: Message) -> bytes:
        """
        Serialize message body to bytes.

        Args:
            message: Message to serialize

        Returns:
            Serialized message body as bytes
        """
        try:
            return json.dumps(message.body, default=str).encode("utf-8")
        except (TypeError, ValueError) as e:
            logger.error(f"Failed to serialize message: {e}")
            raise

    def deserialize_message(self, body: bytes) -> Any:
        """
        Deserialize message body from bytes.

        Args:
            body: Serialized message body

        Returns:
            Deserialized message body
        """
        try:
            return json.loads(body.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            logger.error(f"Failed to deserialize message: {e}")
            raise

    @property
    def is_connected(self) -> bool:
        """Check if adapter is connected."""
        return self._connected


class RabbitMQAdapter(MessageQueueAdapter):
    """RabbitMQ message queue adapter using aio_pika."""

    def __init__(self, config: QueueConfig):
        """
        Initialize RabbitMQ adapter.

        Args:
            config: Queue configuration
        """
        super().__init__(config)
        self._connection = None
        self._channel = None
        self._exchanges = {}
        self._queues = {}
        self._consumers = {}

    async def connect(self) -> None:
        """Establish connection to RabbitMQ."""
        if self._connected:
            logger.warning("Already connected to RabbitMQ")
            return

        try:
            import aio_pika

            self._connection = await aio_pika.connect_robust(
                self.config.url, timeout=self.config.connection_timeout
            )
            self._channel = await self._connection.channel()
            await self._channel.set_qos(prefetch_count=self.config.prefetch_count)

            # Declare default exchange
            self._exchanges[
                self.config.exchange
            ] = await self._channel.declare_exchange(
                self.config.exchange,
                type=self.config.exchange_type,
                durable=True,
            )

            # Declare dead letter exchange and queue
            dlx = await self._channel.declare_exchange(
                self.config.dlx_exchange, type="fanout", durable=True
            )
            self._exchanges[self.config.dlx_exchange] = dlx

            dlq = await self._channel.declare_queue(self.config.dlx_queue, durable=True)
            await dlq.bind(dlx)
            self._queues[self.config.dlx_queue] = dlq

            self._connected = True
            logger.info(f"Connected to RabbitMQ at {self.config.url}")

        except ImportError:
            logger.error("aio_pika not installed. Install with: pip install aio-pika")
            raise
        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ: {e}")
            raise

    async def disconnect(self) -> None:
        """Close connection to RabbitMQ."""
        if not self._connected:
            return

        self._closing = True

        try:
            # Cancel all consumers
            for consumer_tag, consumer in list(self._consumers.items()):
                try:
                    await consumer.cancel()
                except Exception as e:
                    logger.warning(f"Error canceling consumer {consumer_tag}: {e}")

            # Close channel and connection
            if self._channel and not self._channel.is_closed:
                await self._channel.close()

            if self._connection and not self._connection.is_closed:
                await self._connection.close()

            self._connected = False
            logger.info("Disconnected from RabbitMQ")

        except Exception as e:
            logger.error(f"Error disconnecting from RabbitMQ: {e}")
        finally:
            self._closing = False
            self._channel = None
            self._connection = None
            self._exchanges.clear()
            self._queues.clear()
            self._consumers.clear()

    async def publish(
        self,
        message: Message,
        exchange: str | None = None,
        routing_key: str | None = None,
    ) -> bool:
        """
        Publish message to RabbitMQ exchange.

        Args:
            message: Message to publish
            exchange: Exchange name (overrides default)
            routing_key: Routing key (overrides message.routing_key)

        Returns:
            True if message was published successfully
        """
        if not self._connected:
            raise RuntimeError("Not connected to RabbitMQ")

        try:
            import aio_pika

            exchange_name = exchange or self.config.exchange
            routing_key = routing_key or message.routing_key

            # Get or declare exchange
            if exchange_name not in self._exchanges:
                self._exchanges[exchange_name] = await self._channel.declare_exchange(
                    exchange_name, type=self.config.exchange_type, durable=True
                )

            exchange_obj = self._exchanges[exchange_name]

            # Create aio_pika message
            aio_message = aio_pika.Message(
                body=self.serialize_message(message),
                delivery_mode=aio_pika.DeliveryMode(message.delivery_mode.value),
                priority=message.priority,
                correlation_id=message.correlation_id,
                reply_to=message.reply_to,
                expiration=message.expiration,
                message_id=message.message_id,
                timestamp=message.timestamp,
                content_type=message.content_type,
                content_encoding=message.content_encoding,
                headers=message.headers,
            )

            # Publish message
            await exchange_obj.publish(aio_message, routing_key=routing_key)

            logger.debug(
                f"Published message to {exchange_name} with routing key {routing_key}"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to publish message: {e}")
            return False

    async def consume(
        self,
        queue: str,
        callback: Callable[[dict[str, Any], dict[str, Any]], Any],
        ack_mode: AckMode = AckMode.MANUAL,
    ) -> None:
        """
        Consume messages from RabbitMQ queue.

        Args:
            queue: Queue name to consume from
            callback: Async callback function(body, metadata) -> None
            ack_mode: Acknowledgment mode
        """
        if not self._connected:
            raise RuntimeError("Not connected to RabbitMQ")

        try:
            # Get or declare queue
            if queue not in self._queues:
                self._queues[queue] = await self._channel.declare_queue(
                    queue, durable=True
                )

            queue_obj = self._queues[queue]

            # Define message handler
            async def on_message(message):
                async with message.process(ignore_processed=ack_mode == AckMode.NONE):
                    try:
                        # Deserialize message body
                        body = self.deserialize_message(message.body)

                        # Extract metadata
                        metadata = {
                            "delivery_tag": message.delivery_tag,
                            "routing_key": message.routing_key,
                            "exchange": message.exchange,
                            "headers": message.headers or {},
                            "priority": message.priority,
                            "correlation_id": message.correlation_id,
                            "reply_to": message.reply_to,
                            "message_id": message.message_id,
                            "timestamp": message.timestamp,
                            "redelivered": message.redelivered,
                        }

                        # Call user callback
                        await callback(body, metadata)

                        # Auto-ack if enabled
                        if ack_mode == AckMode.AUTO:
                            await message.ack()

                    except Exception as e:
                        logger.error(f"Error processing message: {e}", exc_info=True)
                        # Auto-nack on error if manual ack mode
                        if ack_mode == AckMode.MANUAL:
                            await message.nack(requeue=False)
                        raise

            # Start consuming
            no_ack = ack_mode == AckMode.NONE
            consumer = await queue_obj.consume(on_message, no_ack=no_ack)
            self._consumers[consumer.tag] = consumer

            logger.info(f"Started consuming from queue {queue} (ack_mode={ack_mode})")

        except Exception as e:
            logger.error(f"Failed to start consumer: {e}")
            raise

    async def ack(self, delivery_tag: Any) -> None:
        """
        Acknowledge message processing.

        Args:
            delivery_tag: Message delivery tag
        """
        # In aio_pika, ack is handled via message.ack() in the consumer
        # This method is a no-op for compatibility
        pass

    async def nack(
        self, delivery_tag: Any, requeue: bool = True, multiple: bool = False
    ) -> None:
        """
        Negative acknowledge (reject) message.

        Args:
            delivery_tag: Message delivery tag
            requeue: Whether to requeue the message
            multiple: Whether to nack multiple messages
        """
        # In aio_pika, nack is handled via message.nack() in the consumer
        # This method is a no-op for compatibility
        pass

    async def declare_queue(
        self,
        queue: str,
        durable: bool = True,
        auto_delete: bool = False,
        arguments: dict[str, Any] | None = None,
    ) -> None:
        """
        Declare a RabbitMQ queue.

        Args:
            queue: Queue name
            durable: Queue survives broker restart
            auto_delete: Queue is deleted when last consumer unsubscribes
            arguments: Additional queue arguments (e.g., x-dead-letter-exchange)
        """
        if not self._connected:
            raise RuntimeError("Not connected to RabbitMQ")

        # Add dead letter exchange to arguments if not present
        if arguments is None:
            arguments = {}
        if "x-dead-letter-exchange" not in arguments:
            arguments["x-dead-letter-exchange"] = self.config.dlx_exchange

        # Add message TTL if configured
        if self.config.message_ttl:
            arguments["x-message-ttl"] = self.config.message_ttl

        # Add max priority if configured
        if self.config.max_priority:
            arguments["x-max-priority"] = self.config.max_priority

        self._queues[queue] = await self._channel.declare_queue(
            queue, durable=durable, auto_delete=auto_delete, arguments=arguments
        )

        logger.info(f"Declared queue {queue}")

    async def bind_queue(
        self, queue: str, exchange: str, routing_key: str = ""
    ) -> None:
        """
        Bind queue to exchange with routing key.

        Args:
            queue: Queue name
            exchange: Exchange name
            routing_key: Routing key pattern
        """
        if not self._connected:
            raise RuntimeError("Not connected to RabbitMQ")

        # Ensure queue exists
        if queue not in self._queues:
            await self.declare_queue(queue)

        # Ensure exchange exists
        if exchange not in self._exchanges:
            self._exchanges[exchange] = await self._channel.declare_exchange(
                exchange, type=self.config.exchange_type, durable=True
            )

        # Bind queue to exchange
        queue_obj = self._queues[queue]
        exchange_obj = self._exchanges[exchange]
        await queue_obj.bind(exchange_obj, routing_key=routing_key)

        logger.info(
            f"Bound queue {queue} to exchange {exchange} with key {routing_key}"
        )

    async def purge_queue(self, queue: str) -> int:
        """
        Purge all messages from queue.

        Args:
            queue: Queue name

        Returns:
            Number of messages purged
        """
        if not self._connected:
            raise RuntimeError("Not connected to RabbitMQ")

        if queue not in self._queues:
            await self.declare_queue(queue)

        queue_obj = self._queues[queue]
        result = await queue_obj.purge()

        logger.info(f"Purged {result} messages from queue {queue}")
        return result


class RedisQueueAdapter(MessageQueueAdapter):
    """Redis message queue adapter using redis-py."""

    def __init__(self, config: QueueConfig):
        """
        Initialize Redis adapter.

        Args:
            config: Queue configuration
        """
        super().__init__(config)
        self._redis = None
        self._pubsub = None
        self._consumer_tasks = []

    async def connect(self) -> None:
        """Establish connection to Redis."""
        if self._connected:
            logger.warning("Already connected to Redis")
            return

        try:
            import redis.asyncio as aioredis

            # Parse URL to extract password if present
            self._redis = await aioredis.from_url(
                self.config.url,
                decode_responses=False,  # We handle encoding/decoding
                socket_timeout=self.config.connection_timeout,
            )

            # Test connection
            await self._redis.ping()

            self._connected = True
            logger.info(f"Connected to Redis at {self.config.url}")

        except ImportError:
            logger.error("redis not installed. Install with: pip install redis")
            raise
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise

    async def disconnect(self) -> None:
        """Close connection to Redis."""
        if not self._connected:
            return

        self._closing = True

        try:
            # Cancel all consumer tasks
            for task in self._consumer_tasks:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

            # Close pubsub if active
            if self._pubsub:
                await self._pubsub.close()

            # Close Redis connection
            if self._redis:
                await self._redis.close()

            self._connected = False
            logger.info("Disconnected from Redis")

        except Exception as e:
            logger.error(f"Error disconnecting from Redis: {e}")
        finally:
            self._closing = False
            self._redis = None
            self._pubsub = None
            self._consumer_tasks.clear()

    async def publish(
        self,
        message: Message,
        exchange: str | None = None,
        routing_key: str | None = None,
    ) -> bool:
        """
        Publish message to Redis queue/channel.

        Args:
            message: Message to publish
            exchange: Exchange name (used as prefix for Redis key)
            routing_key: Routing key (queue name)

        Returns:
            True if message was published successfully
        """
        if not self._connected:
            raise RuntimeError("Not connected to Redis")

        try:
            routing_key = (
                routing_key or message.routing_key or self.config.default_queue
            )
            exchange_name = exchange or self.config.exchange

            # Create Redis key (exchange:routing_key)
            redis_key = f"{exchange_name}:{routing_key}"

            # Build message envelope
            envelope = {
                "body": message.body,
                "headers": message.headers,
                "metadata": {
                    "message_id": message.message_id,
                    "timestamp": message.timestamp.isoformat()
                    if message.timestamp
                    else None,
                    "priority": message.priority,
                    "correlation_id": message.correlation_id,
                    "reply_to": message.reply_to,
                    "delivery_mode": message.delivery_mode.value,
                    "routing_key": routing_key,
                    "exchange": exchange_name,
                },
            }

            # Serialize envelope
            serialized = json.dumps(envelope, default=str).encode("utf-8")

            # Push to Redis list (LPUSH for FIFO with RPOP/BRPOP)
            await self._redis.lpush(redis_key, serialized)

            # Set expiration if configured
            if message.expiration:
                await self._redis.expire(redis_key, message.expiration // 1000)

            logger.debug(f"Published message to Redis key {redis_key}")
            return True

        except Exception as e:
            logger.error(f"Failed to publish message to Redis: {e}")
            return False

    async def consume(
        self,
        queue: str,
        callback: Callable[[dict[str, Any], dict[str, Any]], Any],
        ack_mode: AckMode = AckMode.MANUAL,
    ) -> None:
        """
        Consume messages from Redis queue.

        Args:
            queue: Queue name to consume from
            callback: Async callback function(body, metadata) -> None
            ack_mode: Acknowledgment mode (NOTE: Redis doesn't support true acks)
        """
        if not self._connected:
            raise RuntimeError("Not connected to Redis")

        # Create Redis key
        redis_key = f"{self.config.exchange}:{queue}"
        processing_key = f"{redis_key}:processing"
        dlq_key = f"{self.config.dlx_exchange}:{self.config.dlx_queue}"

        async def consumer_loop():
            """Consumer loop for processing messages."""
            retry_policy = RetryPolicy()

            while not self._closing:
                try:
                    # BRPOP with timeout (blocking pop from right side of list)
                    result = await self._redis.brpop(redis_key, timeout=1)

                    if not result:
                        continue

                    _, serialized = result

                    # Move to processing queue
                    await self._redis.lpush(processing_key, serialized)

                    try:
                        # Deserialize envelope
                        envelope = json.loads(serialized.decode("utf-8"))
                        body = envelope.get("body")
                        metadata = envelope.get("metadata", {})

                        # Add delivery tag for compatibility
                        metadata["delivery_tag"] = metadata.get("message_id")

                        # Call user callback
                        await callback(body, metadata)

                        # Remove from processing queue on success
                        await self._redis.lrem(processing_key, 1, serialized)

                    except Exception as e:
                        logger.error(f"Error processing message: {e}", exc_info=True)

                        # Remove from processing queue
                        await self._redis.lrem(processing_key, 1, serialized)

                        # Handle retry logic
                        retry_count = envelope.get("metadata", {}).get("retry_count", 0)

                        if retry_count < retry_policy.max_retries:
                            # Update retry count
                            envelope["metadata"]["retry_count"] = retry_count + 1
                            envelope["metadata"]["last_error"] = str(e)

                            # Calculate delay
                            delay = retry_policy.get_delay(retry_count)

                            # Re-queue with delay (using sorted set for delayed delivery)
                            retry_key = f"{redis_key}:retry"
                            retry_time = time.time() + delay

                            await self._redis.zadd(
                                retry_key,
                                {
                                    json.dumps(envelope, default=str).encode(
                                        "utf-8"
                                    ): retry_time
                                },
                            )

                            logger.info(
                                f"Requeued message for retry {retry_count + 1}/{retry_policy.max_retries} "
                                f"after {delay:.2f}s delay"
                            )
                        else:
                            # Max retries exceeded, send to DLQ
                            envelope["metadata"]["dlq_reason"] = "max_retries_exceeded"
                            envelope["metadata"]["last_error"] = str(e)

                            await self._redis.lpush(
                                dlq_key,
                                json.dumps(envelope, default=str).encode("utf-8"),
                            )

                            logger.warning(
                                f"Message sent to DLQ after {retry_count} failed attempts"
                            )

                except asyncio.CancelledError:
                    logger.info(f"Consumer for {queue} cancelled")
                    break
                except Exception as e:
                    logger.error(f"Error in consumer loop: {e}", exc_info=True)
                    await asyncio.sleep(self.config.reconnect_delay)

        # Start consumer task
        task = asyncio.create_task(consumer_loop())
        self._consumer_tasks.append(task)

        logger.info(f"Started consuming from Redis queue {queue}")

    async def ack(self, delivery_tag: Any) -> None:
        """
        Acknowledge message processing.

        Args:
            delivery_tag: Message delivery tag (message_id)

        Note:
            Redis adapter handles acks automatically in consume loop.
            This is a no-op for compatibility.
        """
        pass

    async def nack(
        self, delivery_tag: Any, requeue: bool = True, multiple: bool = False
    ) -> None:
        """
        Negative acknowledge (reject) message.

        Args:
            delivery_tag: Message delivery tag
            requeue: Whether to requeue the message
            multiple: Whether to nack multiple messages

        Note:
            Redis adapter handles nacks automatically in consume loop.
            This is a no-op for compatibility.
        """
        pass

    async def declare_queue(
        self,
        queue: str,
        durable: bool = True,
        auto_delete: bool = False,
        arguments: dict[str, Any] | None = None,
    ) -> None:
        """
        Declare a queue (no-op for Redis, queues are created on first use).

        Args:
            queue: Queue name
            durable: Ignored (Redis is durable by default)
            auto_delete: Ignored
            arguments: Ignored
        """
        # Redis creates lists on first use, so this is a no-op
        logger.debug(f"Queue {queue} will be created on first use (Redis)")

    async def bind_queue(
        self, queue: str, exchange: str, routing_key: str = ""
    ) -> None:
        """
        Bind queue to exchange (no-op for Redis, uses key prefixes).

        Args:
            queue: Queue name
            exchange: Exchange name (used as prefix)
            routing_key: Routing key pattern (ignored in Redis)
        """
        # Redis uses key prefixes for routing, so this is a no-op
        logger.debug(f"Queue {queue} bound to exchange {exchange} (using key prefix)")

    async def purge_queue(self, queue: str) -> int:
        """
        Purge all messages from queue.

        Args:
            queue: Queue name

        Returns:
            Number of messages purged
        """
        if not self._connected:
            raise RuntimeError("Not connected to Redis")

        redis_key = f"{self.config.exchange}:{queue}"
        processing_key = f"{redis_key}:processing"
        retry_key = f"{redis_key}:retry"

        # Get counts before deletion
        count = await self._redis.llen(redis_key)
        processing_count = await self._redis.llen(processing_key)
        retry_count = await self._redis.zcard(retry_key)

        # Delete all queue-related keys
        await self._redis.delete(redis_key, processing_key, retry_key)

        total = count + processing_count + retry_count
        logger.info(f"Purged {total} messages from Redis queue {queue}")

        return total


def create_queue_adapter(config: QueueConfig | None = None) -> MessageQueueAdapter:
    """
    Factory function to create appropriate queue adapter.

    Args:
        config: Queue configuration (loads from env if not provided)

    Returns:
        MessageQueueAdapter instance for configured backend

    Raises:
        ValueError: If backend type is not supported
    """
    if config is None:
        config = QueueConfig.from_env()

    backend = config.backend.lower()

    if backend == "rabbitmq":
        return RabbitMQAdapter(config)
    elif backend == "redis":
        return RedisQueueAdapter(config)
    else:
        raise ValueError(
            f"Unsupported message queue backend: {backend}. "
            f"Supported backends: rabbitmq, redis"
        )
