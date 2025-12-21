"""
Async Event Bus System

Provides comprehensive event-driven architecture with:
- In-memory event bus for local events
- Distributed event bus with Redis pub/sub
- Wildcard topic matching
- Event replay capability
- Dead letter handling
- Event persistence
- Event filtering and transformation

Components:
- EventBus: Main event bus implementation
- Event: Base event class
- EventFilter: Event filtering system
- EventTransformer: Event transformation system
- DeadLetterQueue: Failed event handling

Usage:
    from app.eventbus import EventBus, Event

    # Create event bus
    bus = EventBus(mode="distributed")

    # Subscribe to events
    async def handler(event: Event):
        print(f"Received: {event.topic}")

    await bus.subscribe("user.created", handler)
    await bus.subscribe("user.*", handler)  # Wildcard matching

    # Publish events
    event = Event(topic="user.created", data={"user_id": 123})
    await bus.publish(event)

    # Replay events
    events = await bus.replay(topic="user.created", from_timestamp=timestamp)
"""

from app.eventbus.bus import (
    DeadLetterQueue,
    Event,
    EventBus,
    EventBusMode,
    EventFilter,
    EventMetadata,
    EventSubscription,
    EventTransformer,
    get_event_bus,
)

__all__ = [
    "Event",
    "EventBus",
    "EventBusMode",
    "EventMetadata",
    "EventSubscription",
    "EventFilter",
    "EventTransformer",
    "DeadLetterQueue",
    "get_event_bus",
]
