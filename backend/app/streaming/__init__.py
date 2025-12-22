"""Streaming module for real-time data delivery.

This module provides comprehensive streaming capabilities including:
- Server-Sent Events (SSE) for HTTP-based streaming
- WebSocket streaming wrapper
- Backpressure handling
- Stream buffering and batching
- Stream filtering and transformation
- Reconnection handling
- Stream metrics collection
- Multi-consumer stream support

Example usage:

    # SSE streaming
    from app.streaming import (
        create_sse_stream,
        publish_to_stream,
        get_sse_manager,
        StreamEventType,
    )

    # Create a stream
    stream_id = await create_sse_stream(
        stream_id="schedule-updates",
        buffer_size=1000,
        heartbeat_interval=30.0
    )

    # Publish data to stream
    await publish_to_stream(
        stream_id="schedule-updates",
        data={"schedule_id": "123", "status": "updated"},
        event_type=StreamEventType.DATA
    )

    # Get SSE response for client
    manager = get_sse_manager()
    return await manager.stream_response(
        stream_id="schedule-updates",
        consumer_id="client-123"
    )

    # WebSocket streaming
    from app.streaming import DataStream, WebSocketStreamWrapper

    # Create a stream
    stream = DataStream(
        stream_id="realtime-updates",
        buffer_size=500
    )

    # Wrap WebSocket connection
    async def websocket_endpoint(websocket: WebSocket):
        wrapper = WebSocketStreamWrapper(
            websocket=websocket,
            stream=stream,
            consumer_id="ws-client-123"
        )
        await wrapper.start()

    # Advanced features
    from app.streaming import (
        BackpressureStrategy,
        StreamFormat,
        StreamMetrics,
    )

    # Create stream with custom backpressure
    stream = DataStream(
        backpressure_strategy=BackpressureStrategy.DROP_OLDEST
    )

    # Add filters
    stream.add_filter(lambda msg: msg.get("priority") == "high")

    # Add transformers
    async def enrich_message(msg):
        msg["enriched_at"] = datetime.now()
        return msg

    stream.add_transformer(enrich_message)

    # Get metrics
    metrics = stream.get_metrics()
    print(f"Messages sent: {metrics['messages_sent']}")
    print(f"Consumers: {metrics['consumers_count']}")
"""

from app.streaming.stream import (
    BackpressureStrategy,
    DataStream,
    SSEStreamManager,
    StreamConsumer,
    StreamEvent,
    StreamEventType,
    StreamFormat,
    StreamMetrics,
    WebSocketStreamWrapper,
    create_sse_stream,
    get_sse_manager,
    get_stream_metrics,
    publish_to_stream,
)

__all__ = [
    # Core classes
    "DataStream",
    "StreamConsumer",
    "StreamEvent",
    "SSEStreamManager",
    "WebSocketStreamWrapper",
    # Enums
    "StreamEventType",
    "StreamFormat",
    "BackpressureStrategy",
    # Metrics
    "StreamMetrics",
    # Convenience functions
    "create_sse_stream",
    "publish_to_stream",
    "get_sse_manager",
    "get_stream_metrics",
]
