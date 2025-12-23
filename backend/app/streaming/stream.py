"""Data streaming service for real-time data delivery.

This module provides:
- Server-Sent Events (SSE) support for HTTP-based streaming
- WebSocket streaming wrapper for bidirectional communication
- Backpressure handling to prevent memory overflow
- Stream buffering and batching for efficiency
- Stream filtering and transformation
- Reconnection handling and recovery
- Stream metrics collection
- Multi-consumer stream support
"""

import asyncio
import json
import logging
import time
from collections import deque
from collections.abc import AsyncGenerator, Callable, Coroutine
from dataclasses import dataclass, field
from enum import Enum
from typing import (
    Any,
    Generic,
    TypeVar,
)
from uuid import uuid4

from fastapi import WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from starlette.responses import StreamingResponse

logger = logging.getLogger(__name__)

# Type variables for generic stream handling
T = TypeVar("T")
FilterFunc = Callable[[T], bool]
TransformFunc = Callable[[T], T | Coroutine[Any, Any, T]]


class StreamEventType(str, Enum):
    """Types of streaming events."""

    DATA = "data"
    HEARTBEAT = "heartbeat"
    ERROR = "error"
    RECONNECT = "reconnect"
    END = "end"


class StreamFormat(str, Enum):
    """Format for stream serialization."""

    JSON = "json"
    TEXT = "text"
    BINARY = "binary"


class BackpressureStrategy(str, Enum):
    """Strategies for handling backpressure."""

    DROP_OLDEST = "drop_oldest"  # Drop oldest messages when buffer full
    DROP_NEWEST = "drop_newest"  # Drop newest messages when buffer full
    BLOCK = "block"  # Block producer until consumer catches up
    ERROR = "error"  # Raise error when buffer full


@dataclass
class StreamMetrics:
    """Metrics for a stream."""

    stream_id: str
    created_at: float = field(default_factory=time.time)
    messages_sent: int = 0
    messages_dropped: int = 0
    messages_filtered: int = 0
    messages_transformed: int = 0
    bytes_sent: int = 0
    consumers_count: int = 0
    errors_count: int = 0
    last_message_at: float | None = None
    backpressure_events: int = 0

    def to_dict(self) -> dict[str, Any]:
        """
        Convert metrics to dictionary.

        Returns:
            Dictionary representation of metrics
        """
        return {
            "stream_id": self.stream_id,
            "created_at": self.created_at,
            "uptime_seconds": time.time() - self.created_at,
            "messages_sent": self.messages_sent,
            "messages_dropped": self.messages_dropped,
            "messages_filtered": self.messages_filtered,
            "messages_transformed": self.messages_transformed,
            "bytes_sent": self.bytes_sent,
            "consumers_count": self.consumers_count,
            "errors_count": self.errors_count,
            "last_message_at": self.last_message_at,
            "backpressure_events": self.backpressure_events,
            "throughput_msg_per_sec": self._calculate_throughput(),
        }

    def _calculate_throughput(self) -> float:
        """Calculate message throughput in messages per second."""
        uptime = time.time() - self.created_at
        if uptime == 0:
            return 0.0
        return self.messages_sent / uptime


@dataclass
class StreamEvent(Generic[T]):
    """A single streaming event."""

    event_type: StreamEventType
    data: T | None = None
    id: str = field(default_factory=lambda: str(uuid4()))
    retry: int | None = None
    timestamp: float = field(default_factory=time.time)

    def to_sse_format(self, data_format: StreamFormat = StreamFormat.JSON) -> str:
        """
        Convert event to Server-Sent Events format.

        Args:
            data_format: Format for data serialization

        Returns:
            SSE-formatted string
        """
        lines = []

        # Event type
        lines.append(f"event: {self.event_type.value}")

        # Event ID
        lines.append(f"id: {self.id}")

        # Retry interval
        if self.retry is not None:
            lines.append(f"retry: {self.retry}")

        # Data
        if self.data is not None:
            if data_format == StreamFormat.JSON:
                if isinstance(self.data, BaseModel):
                    data_str = self.data.model_dump_json()
                else:
                    data_str = json.dumps(self.data, default=str)
            else:
                data_str = str(self.data)

            # SSE format requires each line of data to be prefixed with "data: "
            for line in data_str.split("\n"):
                lines.append(f"data: {line}")

        # Empty line to signal end of event
        lines.append("")

        return "\n".join(lines) + "\n"


class StreamConsumer(Generic[T]):
    """Consumer for a data stream with buffering and backpressure."""

    def __init__(
        self,
        consumer_id: str,
        buffer_size: int = 1000,
        backpressure_strategy: BackpressureStrategy = BackpressureStrategy.DROP_OLDEST,
    ):
        """
        Initialize stream consumer.

        Args:
            consumer_id: Unique identifier for this consumer
            buffer_size: Maximum number of messages to buffer
            backpressure_strategy: Strategy for handling buffer overflow
        """
        self.consumer_id = consumer_id
        self.buffer_size = buffer_size
        self.backpressure_strategy = backpressure_strategy
        self.buffer: deque[StreamEvent[T]] = deque(maxlen=buffer_size)
        self.event = asyncio.Event()
        self.active = True
        self.created_at = time.time()
        self.last_read_at: float | None = None
        self.messages_received = 0
        self.messages_read = 0

    async def add_message(self, message: StreamEvent[T], block: bool = False) -> bool:
        """
        Add a message to the consumer's buffer.

        Args:
            message: Event to add to buffer
            block: Whether to block if buffer is full (overrides backpressure strategy)

        Returns:
            True if message was added, False if dropped

        Raises:
            asyncio.QueueFull: If buffer is full and strategy is ERROR
        """
        if not self.active:
            return False

        # Handle backpressure
        if len(self.buffer) >= self.buffer_size:
            if self.backpressure_strategy == BackpressureStrategy.DROP_OLDEST:
                self.buffer.popleft()
            elif self.backpressure_strategy == BackpressureStrategy.DROP_NEWEST:
                return False
            elif self.backpressure_strategy == BackpressureStrategy.ERROR:
                raise asyncio.QueueFull(f"Buffer full for consumer {self.consumer_id}")
            elif self.backpressure_strategy == BackpressureStrategy.BLOCK:
                if block:
                    # Wait for buffer to have space
                    while len(self.buffer) >= self.buffer_size and self.active:
                        await asyncio.sleep(0.01)
                else:
                    return False

        self.buffer.append(message)
        self.messages_received += 1
        self.event.set()
        return True

    async def read_message(self, timeout: float | None = None) -> StreamEvent[T] | None:
        """
        Read next message from buffer.

        Args:
            timeout: Maximum time to wait for a message (seconds)

        Returns:
            Next event or None if timeout or consumer closed
        """
        if not self.active:
            return None

        # Wait for message if buffer is empty
        if not self.buffer:
            try:
                await asyncio.wait_for(self.event.wait(), timeout=timeout)
            except TimeoutError:
                return None

        if not self.buffer:
            return None

        message = self.buffer.popleft()
        self.last_read_at = time.time()
        self.messages_read += 1

        # Clear event if buffer is now empty
        if not self.buffer:
            self.event.clear()

        return message

    def close(self):
        """Close the consumer and clear its buffer."""
        self.active = False
        self.buffer.clear()
        self.event.set()  # Wake up any waiting read operations


class DataStream(Generic[T]):
    """
    A multi-consumer data stream with filtering, transformation, and backpressure.
    """

    def __init__(
        self,
        stream_id: str | None = None,
        buffer_size: int = 1000,
        backpressure_strategy: BackpressureStrategy = BackpressureStrategy.DROP_OLDEST,
        heartbeat_interval: float | None = 30.0,
    ):
        """
        Initialize a data stream.

        Args:
            stream_id: Unique identifier for the stream
            buffer_size: Default buffer size for consumers
            backpressure_strategy: Default backpressure strategy
            heartbeat_interval: Interval for heartbeat messages (seconds), None to disable
        """
        self.stream_id = stream_id or str(uuid4())
        self.buffer_size = buffer_size
        self.backpressure_strategy = backpressure_strategy
        self.heartbeat_interval = heartbeat_interval

        self.consumers: dict[str, StreamConsumer[T]] = {}
        self.filters: list[FilterFunc] = []
        self.transformers: list[TransformFunc] = []
        self.metrics = StreamMetrics(stream_id=self.stream_id)

        self._lock = asyncio.Lock()
        self._closed = False
        self._heartbeat_task: asyncio.Task | None = None

        # Start heartbeat if enabled
        if self.heartbeat_interval:
            self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())

    async def add_consumer(
        self,
        consumer_id: str | None = None,
        buffer_size: int | None = None,
        backpressure_strategy: BackpressureStrategy | None = None,
    ) -> str:
        """
        Add a new consumer to the stream.

        Args:
            consumer_id: Unique identifier for consumer, auto-generated if not provided
            buffer_size: Buffer size for this consumer
            backpressure_strategy: Backpressure strategy for this consumer

        Returns:
            Consumer ID
        """
        consumer_id = consumer_id or str(uuid4())
        buffer_size = buffer_size or self.buffer_size
        backpressure_strategy = backpressure_strategy or self.backpressure_strategy

        async with self._lock:
            if consumer_id in self.consumers:
                raise ValueError(f"Consumer {consumer_id} already exists")

            consumer = StreamConsumer[T](
                consumer_id=consumer_id,
                buffer_size=buffer_size,
                backpressure_strategy=backpressure_strategy,
            )
            self.consumers[consumer_id] = consumer
            self.metrics.consumers_count = len(self.consumers)

        logger.info(
            f"Added consumer {consumer_id} to stream {self.stream_id} "
            f"(total: {len(self.consumers)})"
        )

        return consumer_id

    async def remove_consumer(self, consumer_id: str):
        """
        Remove a consumer from the stream.

        Args:
            consumer_id: ID of consumer to remove
        """
        async with self._lock:
            consumer = self.consumers.pop(consumer_id, None)
            if consumer:
                consumer.close()
                self.metrics.consumers_count = len(self.consumers)

        logger.info(
            f"Removed consumer {consumer_id} from stream {self.stream_id} "
            f"(remaining: {len(self.consumers)})"
        )

    def add_filter(self, filter_func: FilterFunc):
        """
        Add a filter function to the stream.

        Messages that don't pass the filter will be dropped.

        Args:
            filter_func: Function that returns True to keep message, False to drop
        """
        self.filters.append(filter_func)

    def add_transformer(self, transform_func: TransformFunc):
        """
        Add a transformation function to the stream.

        Args:
            transform_func: Function to transform messages (can be async)
        """
        self.transformers.append(transform_func)

    async def publish(
        self,
        data: T,
        event_type: StreamEventType = StreamEventType.DATA,
        event_id: str | None = None,
    ) -> int:
        """
        Publish a message to all consumers.

        Args:
            data: Data to publish
            event_type: Type of event
            event_id: Optional event ID

        Returns:
            Number of consumers that received the message
        """
        if self._closed:
            raise RuntimeError("Cannot publish to closed stream")

        # Apply filters
        for filter_func in self.filters:
            try:
                if not filter_func(data):
                    self.metrics.messages_filtered += 1
                    return 0
            except Exception as e:
                logger.error(f"Filter error in stream {self.stream_id}: {e}")
                self.metrics.errors_count += 1

        # Apply transformations
        transformed_data = data
        for transform_func in self.transformers:
            try:
                if asyncio.iscoroutinefunction(transform_func):
                    transformed_data = await transform_func(transformed_data)
                else:
                    transformed_data = transform_func(transformed_data)
                self.metrics.messages_transformed += 1
            except Exception as e:
                logger.error(f"Transform error in stream {self.stream_id}: {e}")
                self.metrics.errors_count += 1
                # Continue with untransformed data
                transformed_data = data

        # Create event
        event = StreamEvent[T](
            event_type=event_type,
            data=transformed_data,
            id=event_id or str(uuid4()),
        )

        # Publish to all consumers
        delivered_count = 0
        async with self._lock:
            consumers_list = list(self.consumers.values())

        for consumer in consumers_list:
            try:
                if await consumer.add_message(event):
                    delivered_count += 1
                else:
                    self.metrics.messages_dropped += 1
                    self.metrics.backpressure_events += 1
            except Exception as e:
                logger.error(
                    f"Error publishing to consumer {consumer.consumer_id}: {e}"
                )
                self.metrics.errors_count += 1

        self.metrics.messages_sent += 1
        self.metrics.last_message_at = time.time()

        return delivered_count

    async def publish_batch(
        self, messages: list[T], event_type: StreamEventType = StreamEventType.DATA
    ) -> int:
        """
        Publish multiple messages in a batch.

        Args:
            messages: List of messages to publish
            event_type: Type of event for all messages

        Returns:
            Total number of message deliveries across all consumers
        """
        total_delivered = 0
        for message in messages:
            delivered = await self.publish(message, event_type=event_type)
            total_delivered += delivered
        return total_delivered

    async def consume(
        self,
        consumer_id: str,
        timeout: float | None = None,
    ) -> AsyncGenerator[StreamEvent[T], None]:
        """
        Consume messages from the stream.

        Args:
            consumer_id: ID of the consumer
            timeout: Timeout for waiting for messages

        Yields:
            Stream events as they become available

        Raises:
            ValueError: If consumer_id doesn't exist
        """
        consumer = self.consumers.get(consumer_id)
        if not consumer:
            raise ValueError(f"Consumer {consumer_id} not found")

        try:
            while consumer.active and not self._closed:
                message = await consumer.read_message(timeout=timeout)
                if message:
                    yield message
                elif timeout:
                    # Timeout occurred, but continue consuming
                    continue
                else:
                    # No message and no timeout, wait a bit
                    await asyncio.sleep(0.1)
        finally:
            await self.remove_consumer(consumer_id)

    async def _heartbeat_loop(self):
        """Send periodic heartbeat messages to all consumers."""
        while not self._closed:
            try:
                await asyncio.sleep(self.heartbeat_interval)
                if not self._closed:
                    await self.publish(
                        data={"timestamp": time.time()},
                        event_type=StreamEventType.HEARTBEAT,
                    )
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Heartbeat error in stream {self.stream_id}: {e}")

    def get_metrics(self) -> dict[str, Any]:
        """
        Get stream metrics.

        Returns:
            Dictionary of stream metrics
        """
        return self.metrics.to_dict()

    async def close(self):
        """Close the stream and all consumers."""
        self._closed = True

        # Cancel heartbeat task
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
            try:
                await self._heartbeat_task
            except asyncio.CancelledError:
                pass

        # Close all consumers
        async with self._lock:
            for consumer in list(self.consumers.values()):
                consumer.close()
            self.consumers.clear()
            self.metrics.consumers_count = 0

        logger.info(f"Stream {self.stream_id} closed")


class SSEStreamManager:
    """Manager for Server-Sent Events streams."""

    def __init__(self):
        """Initialize SSE stream manager."""
        self.streams: dict[str, DataStream] = {}
        self._lock = asyncio.Lock()

    async def create_stream(
        self,
        stream_id: str | None = None,
        buffer_size: int = 1000,
        heartbeat_interval: float | None = 30.0,
    ) -> str:
        """
        Create a new SSE stream.

        Args:
            stream_id: Unique identifier for the stream
            buffer_size: Buffer size for consumers
            heartbeat_interval: Heartbeat interval in seconds

        Returns:
            Stream ID
        """
        stream = DataStream[Any](
            stream_id=stream_id,
            buffer_size=buffer_size,
            heartbeat_interval=heartbeat_interval,
        )

        async with self._lock:
            self.streams[stream.stream_id] = stream

        logger.info(f"Created SSE stream {stream.stream_id}")
        return stream.stream_id

    async def get_stream(self, stream_id: str) -> DataStream | None:
        """
        Get an existing stream.

        Args:
            stream_id: Stream identifier

        Returns:
            DataStream instance or None if not found
        """
        return self.streams.get(stream_id)

    async def delete_stream(self, stream_id: str):
        """
        Delete a stream and close all its consumers.

        Args:
            stream_id: Stream identifier
        """
        async with self._lock:
            stream = self.streams.pop(stream_id, None)
            if stream:
                await stream.close()

        logger.info(f"Deleted SSE stream {stream_id}")

    async def stream_response(
        self,
        stream_id: str,
        consumer_id: str | None = None,
        data_format: StreamFormat = StreamFormat.JSON,
    ) -> StreamingResponse:
        """
        Create a StreamingResponse for SSE.

        Args:
            stream_id: Stream identifier
            consumer_id: Consumer identifier
            data_format: Format for data serialization

        Returns:
            FastAPI StreamingResponse

        Raises:
            ValueError: If stream not found
        """
        stream = self.streams.get(stream_id)
        if not stream:
            raise ValueError(f"Stream {stream_id} not found")

        # Add consumer to stream
        consumer_id = await stream.add_consumer(consumer_id=consumer_id)

        async def event_generator() -> AsyncGenerator[str, None]:
            """Generate SSE events."""
            try:
                async for event in stream.consume(consumer_id, timeout=1.0):
                    sse_data = event.to_sse_format(data_format=data_format)
                    stream.metrics.bytes_sent += len(sse_data.encode())
                    yield sse_data
            except Exception as e:
                logger.error(f"Error in SSE generator for {consumer_id}: {e}")
                error_event = StreamEvent(
                    event_type=StreamEventType.ERROR,
                    data={"error": str(e)},
                )
                yield error_event.to_sse_format(data_format=data_format)

        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "X-Accel-Buffering": "no",  # Disable nginx buffering
                "Connection": "keep-alive",
            },
        )

    def get_all_metrics(self) -> dict[str, dict[str, Any]]:
        """
        Get metrics for all streams.

        Returns:
            Dictionary mapping stream IDs to their metrics
        """
        return {
            stream_id: stream.get_metrics()
            for stream_id, stream in self.streams.items()
        }


class WebSocketStreamWrapper:
    """Wrapper for streaming data over WebSocket connections."""

    def __init__(
        self,
        websocket: WebSocket,
        stream: DataStream,
        consumer_id: str | None = None,
        data_format: StreamFormat = StreamFormat.JSON,
    ):
        """
        Initialize WebSocket stream wrapper.

        Args:
            websocket: FastAPI WebSocket connection
            stream: DataStream to wrap
            consumer_id: Consumer identifier
            data_format: Format for data serialization
        """
        self.websocket = websocket
        self.stream = stream
        self.consumer_id = consumer_id or str(uuid4())
        self.data_format = data_format
        self._active = False

    async def start(self):
        """
        Start streaming data over WebSocket.

        This method will:
        1. Accept the WebSocket connection
        2. Add consumer to the stream
        3. Send events as they arrive
        4. Handle disconnection gracefully
        """
        try:
            # Accept connection
            await self.websocket.accept()
            self._active = True

            # Add consumer to stream
            await self.stream.add_consumer(consumer_id=self.consumer_id)

            # Send events
            async for event in self.stream.consume(self.consumer_id, timeout=1.0):
                if not self._active:
                    break

                # Serialize event
                if self.data_format == StreamFormat.JSON:
                    if isinstance(event.data, BaseModel):
                        data = event.data.model_dump()
                    else:
                        data = event.data

                    await self.websocket.send_json(
                        {
                            "event": event.event_type.value,
                            "id": event.id,
                            "data": data,
                            "timestamp": event.timestamp,
                        }
                    )
                else:
                    await self.websocket.send_text(str(event.data))

        except WebSocketDisconnect:
            logger.info(f"WebSocket consumer {self.consumer_id} disconnected")
        except Exception as e:
            logger.error(f"WebSocket stream error for {self.consumer_id}: {e}")
            # Send error event
            try:
                await self.websocket.send_json(
                    {
                        "event": StreamEventType.ERROR.value,
                        "error": str(e),
                        "timestamp": time.time(),
                    }
                )
            except Exception:
                pass
        finally:
            self._active = False
            await self.stream.remove_consumer(self.consumer_id)
            try:
                await self.websocket.close()
            except Exception:
                pass

    async def stop(self):
        """Stop the WebSocket stream."""
        self._active = False
        await self.stream.remove_consumer(self.consumer_id)


# Global SSE stream manager
_sse_manager: SSEStreamManager | None = None


def get_sse_manager() -> SSEStreamManager:
    """
    Get the global SSE stream manager.

    Returns:
        SSEStreamManager singleton instance
    """
    global _sse_manager
    if _sse_manager is None:
        _sse_manager = SSEStreamManager()
    return _sse_manager


async def create_sse_stream(
    stream_id: str | None = None,
    buffer_size: int = 1000,
    heartbeat_interval: float | None = 30.0,
) -> str:
    """
    Create a new SSE stream.

    Args:
        stream_id: Unique identifier for the stream
        buffer_size: Buffer size for consumers
        heartbeat_interval: Heartbeat interval in seconds

    Returns:
        Stream ID
    """
    manager = get_sse_manager()
    return await manager.create_stream(
        stream_id=stream_id,
        buffer_size=buffer_size,
        heartbeat_interval=heartbeat_interval,
    )


async def publish_to_stream(
    stream_id: str,
    data: Any,
    event_type: StreamEventType = StreamEventType.DATA,
) -> int:
    """
    Publish data to an SSE stream.

    Args:
        stream_id: Stream identifier
        data: Data to publish
        event_type: Type of event

    Returns:
        Number of consumers that received the message

    Raises:
        ValueError: If stream not found
    """
    manager = get_sse_manager()
    stream = await manager.get_stream(stream_id)
    if not stream:
        raise ValueError(f"Stream {stream_id} not found")

    return await stream.publish(data, event_type=event_type)


async def get_stream_metrics(stream_id: str) -> dict[str, Any]:
    """
    Get metrics for a specific stream.

    Args:
        stream_id: Stream identifier

    Returns:
        Dictionary of stream metrics

    Raises:
        ValueError: If stream not found
    """
    manager = get_sse_manager()
    stream = await manager.get_stream(stream_id)
    if not stream:
        raise ValueError(f"Stream {stream_id} not found")

    return stream.get_metrics()
