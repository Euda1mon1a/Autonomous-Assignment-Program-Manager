"""WebSocket support for real-time schedule updates."""

from app.websocket.manager import ConnectionManager
from app.websocket.events import (
    EventType,
    WebSocketEvent,
    ScheduleUpdatedEvent,
    AssignmentChangedEvent,
    SwapRequestedEvent,
    SwapApprovedEvent,
    ConflictDetectedEvent,
    ResilienceAlertEvent,
)

__all__ = [
    "ConnectionManager",
    "EventType",
    "WebSocketEvent",
    "ScheduleUpdatedEvent",
    "AssignmentChangedEvent",
    "SwapRequestedEvent",
    "SwapApprovedEvent",
    "ConflictDetectedEvent",
    "ResilienceAlertEvent",
]
