"""WebSocket connection manager for real-time updates."""

import asyncio
import logging
from collections import defaultdict
from uuid import UUID

from fastapi import WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from app.websocket.events import (
    AssignmentChangedEvent,
    ConflictDetectedEvent,
    ConnectionAckEvent,
    PongEvent,
    ResilienceAlertEvent,
    ScheduleUpdatedEvent,
    SwapApprovedEvent,
    SwapRequestedEvent,
)

logger = logging.getLogger(__name__)


class Connection:
    """Represents a single WebSocket connection."""

    def __init__(self, websocket: WebSocket, user_id: UUID):
        """
        Initialize a WebSocket connection.

        Args:
            websocket: FastAPI WebSocket instance
            user_id: ID of authenticated user
        """
        self.websocket = websocket
        self.user_id = user_id
        self.connected_at = asyncio.get_event_loop().time()
        self.subscriptions: set[str] = set()

    async def send_json(self, data: dict) -> bool:
        """
        Send JSON data to the client.

        Args:
            data: Dictionary to send as JSON

        Returns:
            True if successful, False if connection closed
        """
        try:
            await self.websocket.send_json(data)
            return True
        except WebSocketDisconnect:
            logger.info(f"WebSocket disconnected for user {self.user_id}")
            return False
        except Exception as e:
            logger.error(f"Error sending message to user {self.user_id}: {e}")
            return False

    async def send_event(self, event: BaseModel) -> bool:
        """
        Send a Pydantic event model to the client.

        Args:
            event: Pydantic event model

        Returns:
            True if successful, False if connection closed
        """
        return await self.send_json(event.model_dump(mode="json"))


class ConnectionManager:
    """
    Manages WebSocket connections for real-time updates.

    Supports:
    - Per-user connection tracking
    - Broadcast to all clients watching a schedule
    - Targeted messages to specific users
    - Graceful connection/disconnection handling
    """

    def __init__(self):
        """Initialize the connection manager."""
        # Map of user_id -> list of connections (supports multiple tabs)
        self._connections: dict[UUID, list[Connection]] = defaultdict(list)

        # Map of schedule_id -> set of user_ids watching
        self._schedule_watchers: dict[UUID, set[UUID]] = defaultdict(set)

        # Map of person_id -> set of user_ids (for person-specific events)
        self._person_watchers: dict[UUID, set[UUID]] = defaultdict(set)

        # Lock for thread-safe operations
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket, user_id: UUID) -> Connection:
        """
        Register a new WebSocket connection.

        Args:
            websocket: FastAPI WebSocket instance
            user_id: ID of authenticated user

        Returns:
            Connection instance
        """
        await websocket.accept()

        connection = Connection(websocket, user_id)

        async with self._lock:
            self._connections[user_id].append(connection)

        logger.info(
            f"WebSocket connected: user_id={user_id}, "
            f"total_connections={len(self._connections[user_id])}"
        )

        # Send connection acknowledgment
        ack_event = ConnectionAckEvent(user_id=user_id)
        await connection.send_event(ack_event)

        return connection

    async def disconnect(self, connection: Connection):
        """
        Remove a WebSocket connection.

        Args:
            connection: Connection instance to remove
        """
        user_id = connection.user_id

        async with self._lock:
            if user_id in self._connections:
                try:
                    self._connections[user_id].remove(connection)
                    if not self._connections[user_id]:
                        # Remove user if no more connections
                        del self._connections[user_id]

                        # Clean up subscriptions
                        for watchers in self._schedule_watchers.values():
                            watchers.discard(user_id)
                        for watchers in self._person_watchers.values():
                            watchers.discard(user_id)
                except ValueError:
                    pass  # Connection already removed

        logger.info(f"WebSocket disconnected: user_id={user_id}")

    async def subscribe_to_schedule(self, user_id: UUID, schedule_id: UUID):
        """
        Subscribe a user to schedule updates.

        Args:
            user_id: User ID to subscribe
            schedule_id: Schedule ID to watch
        """
        async with self._lock:
            self._schedule_watchers[schedule_id].add(user_id)

        logger.debug(f"User {user_id} subscribed to schedule {schedule_id}")

    async def unsubscribe_from_schedule(self, user_id: UUID, schedule_id: UUID):
        """
        Unsubscribe a user from schedule updates.

        Args:
            user_id: User ID to unsubscribe
            schedule_id: Schedule ID to stop watching
        """
        async with self._lock:
            self._schedule_watchers[schedule_id].discard(user_id)

        logger.debug(f"User {user_id} unsubscribed from schedule {schedule_id}")

    async def subscribe_to_person(self, user_id: UUID, person_id: UUID):
        """
        Subscribe a user to person-specific updates.

        Args:
            user_id: User ID to subscribe
            person_id: Person ID to watch
        """
        async with self._lock:
            self._person_watchers[person_id].add(user_id)

        logger.debug(f"User {user_id} subscribed to person {person_id}")

    async def unsubscribe_from_person(self, user_id: UUID, person_id: UUID):
        """
        Unsubscribe a user from person updates.

        Args:
            user_id: User ID to unsubscribe
            person_id: Person ID to stop watching
        """
        async with self._lock:
            self._person_watchers[person_id].discard(user_id)

        logger.debug(f"User {user_id} unsubscribed from person {person_id}")

    async def send_to_user(self, user_id: UUID, event: BaseModel) -> int:
        """
        Send an event to all connections of a specific user.

        Args:
            user_id: Target user ID
            event: Event to send

        Returns:
            Number of connections successfully sent to
        """
        connections = self._connections.get(user_id, [])
        sent_count = 0

        for connection in connections:
            success = await connection.send_event(event)
            if success:
                sent_count += 1

        return sent_count

    async def broadcast_to_schedule(self, schedule_id: UUID, event: BaseModel) -> int:
        """
        Broadcast an event to all users watching a schedule.

        Args:
            schedule_id: Schedule ID
            event: Event to broadcast

        Returns:
            Number of users successfully sent to
        """
        watchers = self._schedule_watchers.get(schedule_id, set()).copy()
        sent_count = 0

        for user_id in watchers:
            count = await self.send_to_user(user_id, event)
            if count > 0:
                sent_count += 1

        logger.debug(
            f"Broadcast schedule event to {sent_count} users "
            f"(schedule_id={schedule_id})"
        )

        return sent_count

    async def broadcast_to_person(self, person_id: UUID, event: BaseModel) -> int:
        """
        Broadcast an event to all users watching a specific person.

        Args:
            person_id: Person ID
            event: Event to broadcast

        Returns:
            Number of users successfully sent to
        """
        watchers = self._person_watchers.get(person_id, set()).copy()
        sent_count = 0

        for user_id in watchers:
            count = await self.send_to_user(user_id, event)
            if count > 0:
                sent_count += 1

        logger.debug(
            f"Broadcast person event to {sent_count} users (person_id={person_id})"
        )

        return sent_count

    async def broadcast_to_all(self, event: BaseModel) -> int:
        """
        Broadcast an event to all connected users.

        Args:
            event: Event to broadcast

        Returns:
            Number of users successfully sent to
        """
        all_user_ids = list(self._connections.keys())
        sent_count = 0

        for user_id in all_user_ids:
            count = await self.send_to_user(user_id, event)
            if count > 0:
                sent_count += 1

        logger.debug(f"Broadcast event to {sent_count} users")

        return sent_count

    async def handle_ping(self, connection: Connection):
        """
        Handle ping message from client.

        Args:
            connection: Connection that sent ping
        """
        pong_event = PongEvent()
        await connection.send_event(pong_event)

    def get_connection_count(self) -> int:
        """
        Get total number of active connections.

        Returns:
            Total connection count
        """
        return sum(len(conns) for conns in self._connections.values())

    def get_user_count(self) -> int:
        """
        Get number of unique users connected.

        Returns:
            Unique user count
        """
        return len(self._connections)

    def get_schedule_watcher_count(self, schedule_id: UUID) -> int:
        """
        Get number of users watching a schedule.

        Args:
            schedule_id: Schedule ID

        Returns:
            Watcher count
        """
        return len(self._schedule_watchers.get(schedule_id, set()))

    def get_stats(self) -> dict:
        """
        Get connection manager statistics.

        Returns:
            Dictionary with connection stats
        """
        return {
            "total_connections": self.get_connection_count(),
            "unique_users": self.get_user_count(),
            "schedules_watched": len(self._schedule_watchers),
            "persons_watched": len(self._person_watchers),
        }


# Global connection manager instance
_manager: ConnectionManager | None = None


def get_connection_manager() -> ConnectionManager:
    """
    Get the global ConnectionManager instance.

    Returns:
        ConnectionManager singleton
    """
    global _manager
    if _manager is None:
        _manager = ConnectionManager()
    return _manager


# Convenience functions for broadcasting events


async def broadcast_schedule_updated(
    schedule_id: UUID | None,
    academic_year_id: UUID | None,
    user_id: UUID | None,
    update_type: str,
    affected_blocks_count: int = 0,
    message: str = "",
):
    """
    Broadcast a schedule updated event.

    Args:
        schedule_id: Schedule ID (optional)
        academic_year_id: Academic year ID (optional)
        user_id: User who made the update
        update_type: Type of update ("generated", "modified", "regenerated")
        affected_blocks_count: Number of blocks affected
        message: Descriptive message
    """
    manager = get_connection_manager()
    event = ScheduleUpdatedEvent(
        schedule_id=schedule_id,
        academic_year_id=academic_year_id,
        user_id=user_id,
        update_type=update_type,
        affected_blocks_count=affected_blocks_count,
        message=message,
    )

    if schedule_id:
        await manager.broadcast_to_schedule(schedule_id, event)
    else:
        await manager.broadcast_to_all(event)


async def broadcast_assignment_changed(
    assignment_id: UUID,
    person_id: UUID,
    block_id: UUID,
    rotation_template_id: UUID | None,
    change_type: str,
    changed_by: UUID | None = None,
    message: str = "",
):
    """
    Broadcast an assignment changed event.

    Args:
        assignment_id: Assignment ID
        person_id: Person ID
        block_id: Block ID
        rotation_template_id: Rotation template ID (optional)
        change_type: Type of change ("created", "updated", "deleted")
        changed_by: User who made the change
        message: Descriptive message
    """
    manager = get_connection_manager()
    event = AssignmentChangedEvent(
        assignment_id=assignment_id,
        person_id=person_id,
        block_id=block_id,
        rotation_template_id=rotation_template_id,
        change_type=change_type,
        changed_by=changed_by,
        message=message,
    )

    await manager.broadcast_to_person(person_id, event)


async def broadcast_swap_requested(
    swap_id: UUID,
    requester_id: UUID,
    target_person_id: UUID | None,
    swap_type: str,
    affected_assignments: list[UUID],
    message: str = "",
):
    """
    Broadcast a swap requested event.

    Args:
        swap_id: Swap request ID
        requester_id: Person requesting swap
        target_person_id: Target person (optional)
        swap_type: Type of swap ("one_to_one", "absorb")
        affected_assignments: List of affected assignment IDs
        message: Descriptive message
    """
    manager = get_connection_manager()
    event = SwapRequestedEvent(
        swap_id=swap_id,
        requester_id=requester_id,
        target_person_id=target_person_id,
        swap_type=swap_type,
        affected_assignments=affected_assignments,
        message=message,
    )

    # Notify requester
    await manager.broadcast_to_person(requester_id, event)

    # Notify target if specified
    if target_person_id:
        await manager.broadcast_to_person(target_person_id, event)


async def broadcast_swap_approved(
    swap_id: UUID,
    requester_id: UUID,
    target_person_id: UUID | None,
    approved_by: UUID,
    affected_assignments: list[UUID],
    message: str = "",
):
    """
    Broadcast a swap approved event.

    Args:
        swap_id: Swap request ID
        requester_id: Person who requested swap
        target_person_id: Target person (optional)
        approved_by: User who approved
        affected_assignments: List of affected assignment IDs
        message: Descriptive message
    """
    manager = get_connection_manager()
    event = SwapApprovedEvent(
        swap_id=swap_id,
        requester_id=requester_id,
        target_person_id=target_person_id,
        approved_by=approved_by,
        affected_assignments=affected_assignments,
        message=message,
    )

    # Notify requester
    await manager.broadcast_to_person(requester_id, event)

    # Notify target if specified
    if target_person_id:
        await manager.broadcast_to_person(target_person_id, event)


async def broadcast_conflict_detected(
    person_id: UUID,
    conflict_type: str,
    severity: str,
    affected_blocks: list[UUID],
    conflict_id: UUID | None = None,
    message: str = "",
):
    """
    Broadcast a conflict detected event.

    Args:
        person_id: Person with conflict
        conflict_type: Type of conflict
        severity: Severity level ("low", "medium", "high", "critical")
        affected_blocks: List of affected block IDs
        conflict_id: Conflict ID (optional)
        message: Descriptive message
    """
    manager = get_connection_manager()
    event = ConflictDetectedEvent(
        conflict_id=conflict_id,
        person_id=person_id,
        conflict_type=conflict_type,
        severity=severity,
        affected_blocks=affected_blocks,
        message=message,
    )

    await manager.broadcast_to_person(person_id, event)


async def broadcast_resilience_alert(
    alert_type: str,
    severity: str,
    message: str = "",
    current_utilization: float | None = None,
    defense_level: str | None = None,
    affected_persons: list[UUID] | None = None,
    recommendations: list[str] | None = None,
):
    """
    Broadcast a resilience alert event.

    Args:
        alert_type: Type of alert
        severity: Severity level ("green", "yellow", "orange", "red", "black")
        message: Descriptive message
        current_utilization: Current utilization percentage
        defense_level: Defense in depth level
        affected_persons: List of affected person IDs
        recommendations: List of recommended actions
    """
    manager = get_connection_manager()
    event = ResilienceAlertEvent(
        alert_type=alert_type,
        severity=severity,
        current_utilization=current_utilization,
        defense_level=defense_level,
        affected_persons=affected_persons or [],
        message=message,
        recommendations=recommendations or [],
    )

    # Broadcast to all users for system-wide alerts
    await manager.broadcast_to_all(event)
