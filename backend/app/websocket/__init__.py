"""WebSocket support for real-time schedule updates."""

from app.websocket.events import (
    AssignmentChangedEvent,
    ConflictDetectedEvent,
    EventType,
    ResilienceAlertEvent,
    ScheduleUpdatedEvent,
    SwapApprovedEvent,
    SwapRequestedEvent,
    WebSocketEvent,
)
from app.websocket.manager import ConnectionManager

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
