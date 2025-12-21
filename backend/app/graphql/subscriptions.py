"""GraphQL subscriptions for real-time updates in the Residency Scheduler.

This module provides WebSocket-based GraphQL subscriptions that integrate with
the existing WebSocket infrastructure and Redis pub/sub for real-time updates.

Features:
- Schedule update subscriptions
- Swap request notifications
- Conflict alert subscriptions
- User presence tracking
- Role-based filtering
- Connection lifecycle management
- Heartbeat/keep-alive handling
- Redis pub/sub integration

Usage:
    The subscriptions are automatically registered in the GraphQL schema
    and can be accessed via GraphQL subscriptions protocol over WebSockets.
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Any, AsyncGenerator, Optional
from uuid import UUID

import redis.asyncio as redis
import strawberry
from strawberry.types import Info

from app.core.config import get_settings
from app.models.conflict_alert import ConflictSeverity, ConflictType
from app.models.swap import SwapStatus, SwapType
from app.websocket.events import (
    AssignmentChangedEvent,
    ConflictDetectedEvent,
    ResilienceAlertEvent,
    ScheduleUpdatedEvent,
    SwapApprovedEvent,
    SwapRequestedEvent,
)

logger = logging.getLogger(__name__)

# Redis pub/sub channels
CHANNEL_SCHEDULE_UPDATES = "graphql:schedule:updates"
CHANNEL_ASSIGNMENT_UPDATES = "graphql:assignment:updates"
CHANNEL_SWAP_REQUESTS = "graphql:swap:requests"
CHANNEL_SWAP_APPROVALS = "graphql:swap:approvals"
CHANNEL_CONFLICT_ALERTS = "graphql:conflict:alerts"
CHANNEL_RESILIENCE_ALERTS = "graphql:resilience:alerts"
CHANNEL_USER_PRESENCE = "graphql:user:presence"
CHANNEL_HEARTBEAT = "graphql:heartbeat"


# GraphQL types for subscription payloads


@strawberry.type
class ScheduleUpdate:
    """Schedule update notification."""

    schedule_id: Optional[strawberry.ID] = None
    academic_year_id: Optional[strawberry.ID] = None
    user_id: Optional[strawberry.ID] = None
    update_type: str
    affected_blocks_count: int
    message: str
    timestamp: datetime


@strawberry.type
class AssignmentUpdate:
    """Assignment change notification."""

    assignment_id: strawberry.ID
    person_id: strawberry.ID
    block_id: strawberry.ID
    rotation_template_id: Optional[strawberry.ID] = None
    change_type: str
    changed_by: Optional[strawberry.ID] = None
    message: str
    timestamp: datetime


@strawberry.type
class SwapNotification:
    """Swap request notification."""

    swap_id: strawberry.ID
    requester_id: strawberry.ID
    target_person_id: Optional[strawberry.ID] = None
    swap_type: str
    status: str
    affected_assignments: list[strawberry.ID]
    message: str
    timestamp: datetime
    approved_by: Optional[strawberry.ID] = None


@strawberry.type
class ConflictNotification:
    """Conflict alert notification."""

    conflict_id: Optional[strawberry.ID] = None
    person_id: strawberry.ID
    conflict_type: str
    severity: str
    affected_blocks: list[strawberry.ID]
    message: str
    timestamp: datetime


@strawberry.type
class ResilienceNotification:
    """Resilience system alert notification."""

    alert_type: str
    severity: str
    current_utilization: Optional[float] = None
    defense_level: Optional[str] = None
    affected_persons: list[strawberry.ID]
    message: str
    recommendations: list[str]
    timestamp: datetime


@strawberry.type
class UserPresenceUpdate:
    """User presence update notification."""

    user_id: strawberry.ID
    status: str  # "online", "offline", "away"
    last_seen: datetime
    active_page: Optional[str] = None


@strawberry.type
class HeartbeatResponse:
    """Heartbeat response for keep-alive."""

    timestamp: datetime
    server_time: datetime
    connection_id: str


# Subscription input filters


@strawberry.input
class SubscriptionFilter:
    """Base filter for subscriptions."""

    user_id: Optional[strawberry.ID] = None
    role: Optional[str] = None


@strawberry.input
class ScheduleSubscriptionFilter:
    """Filter for schedule update subscriptions."""

    schedule_id: Optional[strawberry.ID] = None
    academic_year_id: Optional[strawberry.ID] = None
    person_id: Optional[strawberry.ID] = None
    update_types: Optional[list[str]] = None  # ["generated", "modified", "regenerated"]


@strawberry.input
class SwapSubscriptionFilter:
    """Filter for swap notification subscriptions."""

    person_id: Optional[strawberry.ID] = None
    swap_types: Optional[list[str]] = None  # ["one_to_one", "absorb"]
    statuses: Optional[list[str]] = None  # ["pending", "approved", "executed", "rejected"]


@strawberry.input
class ConflictSubscriptionFilter:
    """Filter for conflict alert subscriptions."""

    person_id: Optional[strawberry.ID] = None
    severities: Optional[list[str]] = None  # ["critical", "warning", "info"]
    conflict_types: Optional[list[str]] = None


# Redis pub/sub manager


class RedisSubscriptionManager:
    """
    Manages Redis pub/sub connections for GraphQL subscriptions.

    Handles:
    - Connection pooling
    - Channel subscription/unsubscription
    - Message broadcasting
    - Connection lifecycle
    """

    def __init__(self):
        """Initialize the subscription manager."""
        self._redis: Optional[redis.Redis] = None
        self._pubsub: Optional[redis.client.PubSub] = None
        self._settings = get_settings()

    async def get_redis(self) -> redis.Redis:
        """
        Get or create async Redis connection.

        Returns:
            Redis client instance

        Raises:
            ConnectionError: If Redis is unavailable
        """
        if self._redis is None:
            redis_url = self._settings.redis_url_with_password
            self._redis = redis.from_url(redis_url, decode_responses=True)

        return self._redis

    async def get_pubsub(self) -> redis.client.PubSub:
        """
        Get or create Redis pub/sub instance.

        Returns:
            Redis pub/sub instance
        """
        if self._pubsub is None:
            redis_client = await self.get_redis()
            self._pubsub = redis_client.pubsub()

        return self._pubsub

    async def subscribe(self, *channels: str) -> AsyncGenerator[dict[str, Any], None]:
        """
        Subscribe to Redis channels and yield messages.

        Args:
            *channels: Channel names to subscribe to

        Yields:
            Message dictionaries from subscribed channels

        Example:
            async for message in manager.subscribe("schedule:updates"):
                print(message)
        """
        pubsub = await self.get_pubsub()

        try:
            await pubsub.subscribe(*channels)
            logger.info(f"Subscribed to channels: {', '.join(channels)}")

            async for message in pubsub.listen():
                if message["type"] == "message":
                    try:
                        # Parse JSON message data
                        data = json.loads(message["data"])
                        yield data
                    except json.JSONDecodeError:
                        logger.warning(f"Failed to decode message: {message['data']}")
                        continue

        except redis.ConnectionError as e:
            logger.error(f"Redis connection error in subscription: {e}")
            raise
        finally:
            try:
                await pubsub.unsubscribe(*channels)
                logger.info(f"Unsubscribed from channels: {', '.join(channels)}")
            except Exception as e:
                logger.error(f"Error unsubscribing from channels: {e}")

    async def publish(self, channel: str, message: dict[str, Any]) -> int:
        """
        Publish a message to a Redis channel.

        Args:
            channel: Channel name
            message: Message dictionary to publish

        Returns:
            Number of subscribers that received the message

        Example:
            await manager.publish("schedule:updates", {
                "schedule_id": "123",
                "update_type": "generated"
            })
        """
        try:
            redis_client = await self.get_redis()
            message_json = json.dumps(message, default=str)
            count = await redis_client.publish(channel, message_json)
            logger.debug(f"Published to {channel}: {count} subscribers")
            return count

        except redis.ConnectionError as e:
            logger.error(f"Redis connection error in publish: {e}")
            return 0
        except Exception as e:
            logger.error(f"Error publishing message: {e}")
            return 0

    async def close(self):
        """Close Redis connections."""
        if self._pubsub is not None:
            await self._pubsub.close()
            self._pubsub = None

        if self._redis is not None:
            await self._redis.close()
            self._redis = None

        logger.info("Redis subscription manager closed")


# Global subscription manager instance
_subscription_manager: Optional[RedisSubscriptionManager] = None


def get_subscription_manager() -> RedisSubscriptionManager:
    """
    Get the global Redis subscription manager instance.

    Returns:
        RedisSubscriptionManager singleton
    """
    global _subscription_manager
    if _subscription_manager is None:
        _subscription_manager = RedisSubscriptionManager()
    return _subscription_manager


# Helper functions for filtering


def should_send_schedule_update(
    update: dict[str, Any],
    filter_input: Optional[ScheduleSubscriptionFilter],
    user_id: str,
) -> bool:
    """
    Check if a schedule update should be sent based on filters.

    Args:
        update: Schedule update data
        filter_input: Subscription filters
        user_id: Current user ID

    Returns:
        True if update matches filters, False otherwise
    """
    if filter_input is None:
        return True

    # Filter by schedule ID
    if filter_input.schedule_id and update.get("schedule_id") != filter_input.schedule_id:
        return False

    # Filter by academic year
    if filter_input.academic_year_id and update.get("academic_year_id") != filter_input.academic_year_id:
        return False

    # Filter by person ID (user watching their own assignments)
    if filter_input.person_id and update.get("person_id") != filter_input.person_id:
        return False

    # Filter by update types
    if filter_input.update_types and update.get("update_type") not in filter_input.update_types:
        return False

    return True


def should_send_swap_notification(
    swap: dict[str, Any],
    filter_input: Optional[SwapSubscriptionFilter],
    user_id: str,
) -> bool:
    """
    Check if a swap notification should be sent based on filters.

    Args:
        swap: Swap notification data
        filter_input: Subscription filters
        user_id: Current user ID

    Returns:
        True if notification matches filters, False otherwise
    """
    if filter_input is None:
        return True

    # Filter by person ID (requester or target)
    if filter_input.person_id:
        person_id_str = str(filter_input.person_id)
        if (swap.get("requester_id") != person_id_str and
            swap.get("target_person_id") != person_id_str):
            return False

    # Filter by swap types
    if filter_input.swap_types and swap.get("swap_type") not in filter_input.swap_types:
        return False

    # Filter by statuses
    if filter_input.statuses and swap.get("status") not in filter_input.statuses:
        return False

    return True


def should_send_conflict_notification(
    conflict: dict[str, Any],
    filter_input: Optional[ConflictSubscriptionFilter],
    user_id: str,
) -> bool:
    """
    Check if a conflict notification should be sent based on filters.

    Args:
        conflict: Conflict notification data
        filter_input: Subscription filters
        user_id: Current user ID

    Returns:
        True if notification matches filters, False otherwise
    """
    if filter_input is None:
        return True

    # Filter by person ID
    if filter_input.person_id and conflict.get("person_id") != str(filter_input.person_id):
        return False

    # Filter by severities
    if filter_input.severities and conflict.get("severity") not in filter_input.severities:
        return False

    # Filter by conflict types
    if filter_input.conflict_types and conflict.get("conflict_type") not in filter_input.conflict_types:
        return False

    return True


# Subscription resolvers


@strawberry.type
class Subscription:
    """
    GraphQL subscription root type.

    Provides real-time subscriptions for:
    - Schedule updates
    - Assignment changes
    - Swap requests and approvals
    - Conflict alerts
    - Resilience alerts
    - User presence
    - Connection heartbeat
    """

    @strawberry.subscription
    async def schedule_updates(
        self,
        info: Info,
        filter: Optional[ScheduleSubscriptionFilter] = None,
    ) -> AsyncGenerator[ScheduleUpdate, None]:
        """
        Subscribe to schedule updates in real-time.

        Args:
            filter: Optional filters for schedule updates

        Yields:
            ScheduleUpdate notifications matching the filters

        Example GraphQL:
            subscription {
                scheduleUpdates(filter: {
                    scheduleId: "123",
                    updateTypes: ["generated", "modified"]
                }) {
                    scheduleId
                    updateType
                    message
                    timestamp
                }
            }
        """
        manager = get_subscription_manager()
        user_id = info.context.get("user", {}).get("user_id", "anonymous")

        logger.info(f"User {user_id} subscribed to schedule updates")

        try:
            async for message in manager.subscribe(CHANNEL_SCHEDULE_UPDATES):
                # Apply filters
                if should_send_schedule_update(message, filter, user_id):
                    yield ScheduleUpdate(
                        schedule_id=strawberry.ID(message.get("schedule_id")) if message.get("schedule_id") else None,
                        academic_year_id=strawberry.ID(message.get("academic_year_id")) if message.get("academic_year_id") else None,
                        user_id=strawberry.ID(message.get("user_id")) if message.get("user_id") else None,
                        update_type=message.get("update_type", ""),
                        affected_blocks_count=message.get("affected_blocks_count", 0),
                        message=message.get("message", ""),
                        timestamp=datetime.fromisoformat(message.get("timestamp", datetime.utcnow().isoformat())),
                    )

        except asyncio.CancelledError:
            logger.info(f"User {user_id} unsubscribed from schedule updates")
            raise
        except Exception as e:
            logger.error(f"Error in schedule updates subscription: {e}", exc_info=True)
            raise

    @strawberry.subscription
    async def assignment_updates(
        self,
        info: Info,
        person_id: Optional[strawberry.ID] = None,
    ) -> AsyncGenerator[AssignmentUpdate, None]:
        """
        Subscribe to assignment changes for a specific person or all assignments.

        Args:
            person_id: Optional person ID to filter updates

        Yields:
            AssignmentUpdate notifications

        Example GraphQL:
            subscription {
                assignmentUpdates(personId: "456") {
                    assignmentId
                    changeType
                    message
                    timestamp
                }
            }
        """
        manager = get_subscription_manager()
        user_id = info.context.get("user", {}).get("user_id", "anonymous")

        logger.info(f"User {user_id} subscribed to assignment updates (person_id={person_id})")

        try:
            async for message in manager.subscribe(CHANNEL_ASSIGNMENT_UPDATES):
                # Filter by person_id if specified
                if person_id and message.get("person_id") != str(person_id):
                    continue

                yield AssignmentUpdate(
                    assignment_id=strawberry.ID(message.get("assignment_id", "")),
                    person_id=strawberry.ID(message.get("person_id", "")),
                    block_id=strawberry.ID(message.get("block_id", "")),
                    rotation_template_id=strawberry.ID(message.get("rotation_template_id")) if message.get("rotation_template_id") else None,
                    change_type=message.get("change_type", ""),
                    changed_by=strawberry.ID(message.get("changed_by")) if message.get("changed_by") else None,
                    message=message.get("message", ""),
                    timestamp=datetime.fromisoformat(message.get("timestamp", datetime.utcnow().isoformat())),
                )

        except asyncio.CancelledError:
            logger.info(f"User {user_id} unsubscribed from assignment updates")
            raise
        except Exception as e:
            logger.error(f"Error in assignment updates subscription: {e}", exc_info=True)
            raise

    @strawberry.subscription
    async def swap_requests(
        self,
        info: Info,
        filter: Optional[SwapSubscriptionFilter] = None,
    ) -> AsyncGenerator[SwapNotification, None]:
        """
        Subscribe to swap request notifications.

        Args:
            filter: Optional filters for swap notifications

        Yields:
            SwapNotification for new swap requests

        Example GraphQL:
            subscription {
                swapRequests(filter: {
                    personId: "789",
                    swapTypes: ["one_to_one"]
                }) {
                    swapId
                    swapType
                    message
                    timestamp
                }
            }
        """
        manager = get_subscription_manager()
        user_id = info.context.get("user", {}).get("user_id", "anonymous")

        logger.info(f"User {user_id} subscribed to swap requests")

        try:
            async for message in manager.subscribe(CHANNEL_SWAP_REQUESTS):
                # Apply filters
                if should_send_swap_notification(message, filter, user_id):
                    yield SwapNotification(
                        swap_id=strawberry.ID(message.get("swap_id", "")),
                        requester_id=strawberry.ID(message.get("requester_id", "")),
                        target_person_id=strawberry.ID(message.get("target_person_id")) if message.get("target_person_id") else None,
                        swap_type=message.get("swap_type", ""),
                        status=message.get("status", "pending"),
                        affected_assignments=[strawberry.ID(aid) for aid in message.get("affected_assignments", [])],
                        message=message.get("message", ""),
                        timestamp=datetime.fromisoformat(message.get("timestamp", datetime.utcnow().isoformat())),
                        approved_by=None,
                    )

        except asyncio.CancelledError:
            logger.info(f"User {user_id} unsubscribed from swap requests")
            raise
        except Exception as e:
            logger.error(f"Error in swap requests subscription: {e}", exc_info=True)
            raise

    @strawberry.subscription
    async def swap_approvals(
        self,
        info: Info,
        filter: Optional[SwapSubscriptionFilter] = None,
    ) -> AsyncGenerator[SwapNotification, None]:
        """
        Subscribe to swap approval notifications.

        Args:
            filter: Optional filters for swap notifications

        Yields:
            SwapNotification for approved swaps

        Example GraphQL:
            subscription {
                swapApprovals(filter: {personId: "789"}) {
                    swapId
                    approvedBy
                    message
                    timestamp
                }
            }
        """
        manager = get_subscription_manager()
        user_id = info.context.get("user", {}).get("user_id", "anonymous")

        logger.info(f"User {user_id} subscribed to swap approvals")

        try:
            async for message in manager.subscribe(CHANNEL_SWAP_APPROVALS):
                # Apply filters
                if should_send_swap_notification(message, filter, user_id):
                    yield SwapNotification(
                        swap_id=strawberry.ID(message.get("swap_id", "")),
                        requester_id=strawberry.ID(message.get("requester_id", "")),
                        target_person_id=strawberry.ID(message.get("target_person_id")) if message.get("target_person_id") else None,
                        swap_type=message.get("swap_type", ""),
                        status="approved",
                        affected_assignments=[strawberry.ID(aid) for aid in message.get("affected_assignments", [])],
                        message=message.get("message", ""),
                        timestamp=datetime.fromisoformat(message.get("timestamp", datetime.utcnow().isoformat())),
                        approved_by=strawberry.ID(message.get("approved_by")) if message.get("approved_by") else None,
                    )

        except asyncio.CancelledError:
            logger.info(f"User {user_id} unsubscribed from swap approvals")
            raise
        except Exception as e:
            logger.error(f"Error in swap approvals subscription: {e}", exc_info=True)
            raise

    @strawberry.subscription
    async def conflict_alerts(
        self,
        info: Info,
        filter: Optional[ConflictSubscriptionFilter] = None,
    ) -> AsyncGenerator[ConflictNotification, None]:
        """
        Subscribe to conflict alert notifications.

        Args:
            filter: Optional filters for conflict alerts

        Yields:
            ConflictNotification for detected conflicts

        Example GraphQL:
            subscription {
                conflictAlerts(filter: {
                    personId: "101",
                    severities: ["critical", "warning"]
                }) {
                    conflictType
                    severity
                    message
                    timestamp
                }
            }
        """
        manager = get_subscription_manager()
        user_id = info.context.get("user", {}).get("user_id", "anonymous")

        logger.info(f"User {user_id} subscribed to conflict alerts")

        try:
            async for message in manager.subscribe(CHANNEL_CONFLICT_ALERTS):
                # Apply filters
                if should_send_conflict_notification(message, filter, user_id):
                    yield ConflictNotification(
                        conflict_id=strawberry.ID(message.get("conflict_id")) if message.get("conflict_id") else None,
                        person_id=strawberry.ID(message.get("person_id", "")),
                        conflict_type=message.get("conflict_type", ""),
                        severity=message.get("severity", ""),
                        affected_blocks=[strawberry.ID(bid) for bid in message.get("affected_blocks", [])],
                        message=message.get("message", ""),
                        timestamp=datetime.fromisoformat(message.get("timestamp", datetime.utcnow().isoformat())),
                    )

        except asyncio.CancelledError:
            logger.info(f"User {user_id} unsubscribed from conflict alerts")
            raise
        except Exception as e:
            logger.error(f"Error in conflict alerts subscription: {e}", exc_info=True)
            raise

    @strawberry.subscription
    async def resilience_alerts(
        self,
        info: Info,
    ) -> AsyncGenerator[ResilienceNotification, None]:
        """
        Subscribe to resilience system alert notifications.

        All authenticated users receive resilience alerts as they are system-wide.

        Yields:
            ResilienceNotification for resilience system alerts

        Example GraphQL:
            subscription {
                resilienceAlerts {
                    alertType
                    severity
                    currentUtilization
                    defenseLevel
                    message
                    recommendations
                    timestamp
                }
            }
        """
        manager = get_subscription_manager()
        user_id = info.context.get("user", {}).get("user_id", "anonymous")

        logger.info(f"User {user_id} subscribed to resilience alerts")

        try:
            async for message in manager.subscribe(CHANNEL_RESILIENCE_ALERTS):
                yield ResilienceNotification(
                    alert_type=message.get("alert_type", ""),
                    severity=message.get("severity", ""),
                    current_utilization=message.get("current_utilization"),
                    defense_level=message.get("defense_level"),
                    affected_persons=[strawberry.ID(pid) for pid in message.get("affected_persons", [])],
                    message=message.get("message", ""),
                    recommendations=message.get("recommendations", []),
                    timestamp=datetime.fromisoformat(message.get("timestamp", datetime.utcnow().isoformat())),
                )

        except asyncio.CancelledError:
            logger.info(f"User {user_id} unsubscribed from resilience alerts")
            raise
        except Exception as e:
            logger.error(f"Error in resilience alerts subscription: {e}", exc_info=True)
            raise

    @strawberry.subscription
    async def user_presence(
        self,
        info: Info,
    ) -> AsyncGenerator[UserPresenceUpdate, None]:
        """
        Subscribe to user presence updates (online/offline/away).

        Yields:
            UserPresenceUpdate for user status changes

        Example GraphQL:
            subscription {
                userPresence {
                    userId
                    status
                    lastSeen
                    activePage
                }
            }
        """
        manager = get_subscription_manager()
        user_id = info.context.get("user", {}).get("user_id", "anonymous")

        logger.info(f"User {user_id} subscribed to user presence updates")

        # Publish own presence as online
        await manager.publish(CHANNEL_USER_PRESENCE, {
            "user_id": user_id,
            "status": "online",
            "last_seen": datetime.utcnow().isoformat(),
            "active_page": None,
        })

        try:
            async for message in manager.subscribe(CHANNEL_USER_PRESENCE):
                yield UserPresenceUpdate(
                    user_id=strawberry.ID(message.get("user_id", "")),
                    status=message.get("status", ""),
                    last_seen=datetime.fromisoformat(message.get("last_seen", datetime.utcnow().isoformat())),
                    active_page=message.get("active_page"),
                )

        except asyncio.CancelledError:
            # Publish own presence as offline on disconnect
            await manager.publish(CHANNEL_USER_PRESENCE, {
                "user_id": user_id,
                "status": "offline",
                "last_seen": datetime.utcnow().isoformat(),
                "active_page": None,
            })
            logger.info(f"User {user_id} unsubscribed from user presence")
            raise
        except Exception as e:
            logger.error(f"Error in user presence subscription: {e}", exc_info=True)
            raise

    @strawberry.subscription
    async def heartbeat(
        self,
        info: Info,
        interval_seconds: int = 30,
    ) -> AsyncGenerator[HeartbeatResponse, None]:
        """
        Heartbeat subscription for connection keep-alive.

        Args:
            interval_seconds: Interval between heartbeats (default: 30s)

        Yields:
            HeartbeatResponse at regular intervals

        Example GraphQL:
            subscription {
                heartbeat(intervalSeconds: 30) {
                    timestamp
                    serverTime
                    connectionId
                }
            }
        """
        import uuid

        user_id = info.context.get("user", {}).get("user_id", "anonymous")
        connection_id = str(uuid.uuid4())

        logger.info(f"User {user_id} started heartbeat subscription (connection_id={connection_id})")

        try:
            while True:
                now = datetime.utcnow()
                yield HeartbeatResponse(
                    timestamp=now,
                    server_time=now,
                    connection_id=connection_id,
                )
                await asyncio.sleep(interval_seconds)

        except asyncio.CancelledError:
            logger.info(f"User {user_id} stopped heartbeat subscription")
            raise
        except Exception as e:
            logger.error(f"Error in heartbeat subscription: {e}", exc_info=True)
            raise


# Broadcasting helper functions


async def broadcast_schedule_update(
    schedule_id: Optional[UUID] = None,
    academic_year_id: Optional[UUID] = None,
    user_id: Optional[UUID] = None,
    update_type: str = "",
    affected_blocks_count: int = 0,
    message: str = "",
):
    """
    Broadcast a schedule update to all subscribers.

    Args:
        schedule_id: Schedule ID
        academic_year_id: Academic year ID
        user_id: User who made the update
        update_type: Type of update ("generated", "modified", "regenerated")
        affected_blocks_count: Number of blocks affected
        message: Descriptive message
    """
    manager = get_subscription_manager()
    await manager.publish(CHANNEL_SCHEDULE_UPDATES, {
        "schedule_id": str(schedule_id) if schedule_id else None,
        "academic_year_id": str(academic_year_id) if academic_year_id else None,
        "user_id": str(user_id) if user_id else None,
        "update_type": update_type,
        "affected_blocks_count": affected_blocks_count,
        "message": message,
        "timestamp": datetime.utcnow().isoformat(),
    })


async def broadcast_assignment_update(
    assignment_id: UUID,
    person_id: UUID,
    block_id: UUID,
    rotation_template_id: Optional[UUID] = None,
    change_type: str = "",
    changed_by: Optional[UUID] = None,
    message: str = "",
):
    """
    Broadcast an assignment update to all subscribers.

    Args:
        assignment_id: Assignment ID
        person_id: Person ID
        block_id: Block ID
        rotation_template_id: Rotation template ID
        change_type: Type of change ("created", "updated", "deleted")
        changed_by: User who made the change
        message: Descriptive message
    """
    manager = get_subscription_manager()
    await manager.publish(CHANNEL_ASSIGNMENT_UPDATES, {
        "assignment_id": str(assignment_id),
        "person_id": str(person_id),
        "block_id": str(block_id),
        "rotation_template_id": str(rotation_template_id) if rotation_template_id else None,
        "change_type": change_type,
        "changed_by": str(changed_by) if changed_by else None,
        "message": message,
        "timestamp": datetime.utcnow().isoformat(),
    })


async def broadcast_swap_request(
    swap_id: UUID,
    requester_id: UUID,
    target_person_id: Optional[UUID] = None,
    swap_type: str = "",
    affected_assignments: Optional[list[UUID]] = None,
    message: str = "",
):
    """
    Broadcast a swap request notification.

    Args:
        swap_id: Swap request ID
        requester_id: Person requesting swap
        target_person_id: Target person
        swap_type: Type of swap ("one_to_one", "absorb")
        affected_assignments: List of affected assignment IDs
        message: Descriptive message
    """
    manager = get_subscription_manager()
    await manager.publish(CHANNEL_SWAP_REQUESTS, {
        "swap_id": str(swap_id),
        "requester_id": str(requester_id),
        "target_person_id": str(target_person_id) if target_person_id else None,
        "swap_type": swap_type,
        "status": "pending",
        "affected_assignments": [str(aid) for aid in (affected_assignments or [])],
        "message": message,
        "timestamp": datetime.utcnow().isoformat(),
    })


async def broadcast_swap_approval(
    swap_id: UUID,
    requester_id: UUID,
    target_person_id: Optional[UUID] = None,
    swap_type: str = "",
    approved_by: Optional[UUID] = None,
    affected_assignments: Optional[list[UUID]] = None,
    message: str = "",
):
    """
    Broadcast a swap approval notification.

    Args:
        swap_id: Swap request ID
        requester_id: Person who requested swap
        target_person_id: Target person
        swap_type: Type of swap
        approved_by: User who approved
        affected_assignments: List of affected assignment IDs
        message: Descriptive message
    """
    manager = get_subscription_manager()
    await manager.publish(CHANNEL_SWAP_APPROVALS, {
        "swap_id": str(swap_id),
        "requester_id": str(requester_id),
        "target_person_id": str(target_person_id) if target_person_id else None,
        "swap_type": swap_type,
        "status": "approved",
        "approved_by": str(approved_by) if approved_by else None,
        "affected_assignments": [str(aid) for aid in (affected_assignments or [])],
        "message": message,
        "timestamp": datetime.utcnow().isoformat(),
    })


async def broadcast_conflict_alert(
    person_id: UUID,
    conflict_type: str,
    severity: str,
    affected_blocks: Optional[list[UUID]] = None,
    conflict_id: Optional[UUID] = None,
    message: str = "",
):
    """
    Broadcast a conflict alert notification.

    Args:
        person_id: Person with conflict
        conflict_type: Type of conflict
        severity: Severity level ("critical", "warning", "info")
        affected_blocks: List of affected block IDs
        conflict_id: Conflict ID
        message: Descriptive message
    """
    manager = get_subscription_manager()
    await manager.publish(CHANNEL_CONFLICT_ALERTS, {
        "conflict_id": str(conflict_id) if conflict_id else None,
        "person_id": str(person_id),
        "conflict_type": conflict_type,
        "severity": severity,
        "affected_blocks": [str(bid) for bid in (affected_blocks or [])],
        "message": message,
        "timestamp": datetime.utcnow().isoformat(),
    })


async def broadcast_resilience_alert(
    alert_type: str,
    severity: str,
    message: str = "",
    current_utilization: Optional[float] = None,
    defense_level: Optional[str] = None,
    affected_persons: Optional[list[UUID]] = None,
    recommendations: Optional[list[str]] = None,
):
    """
    Broadcast a resilience system alert.

    Args:
        alert_type: Type of alert
        severity: Severity level ("green", "yellow", "orange", "red", "black")
        message: Descriptive message
        current_utilization: Current utilization percentage
        defense_level: Defense in depth level
        affected_persons: List of affected person IDs
        recommendations: List of recommended actions
    """
    manager = get_subscription_manager()
    await manager.publish(CHANNEL_RESILIENCE_ALERTS, {
        "alert_type": alert_type,
        "severity": severity,
        "current_utilization": current_utilization,
        "defense_level": defense_level,
        "affected_persons": [str(pid) for pid in (affected_persons or [])],
        "message": message,
        "recommendations": recommendations or [],
        "timestamp": datetime.utcnow().isoformat(),
    })


__all__ = [
    "Subscription",
    "ScheduleUpdate",
    "AssignmentUpdate",
    "SwapNotification",
    "ConflictNotification",
    "ResilienceNotification",
    "UserPresenceUpdate",
    "HeartbeatResponse",
    "ScheduleSubscriptionFilter",
    "SwapSubscriptionFilter",
    "ConflictSubscriptionFilter",
    "RedisSubscriptionManager",
    "get_subscription_manager",
    "broadcast_schedule_update",
    "broadcast_assignment_update",
    "broadcast_swap_request",
    "broadcast_swap_approval",
    "broadcast_conflict_alert",
    "broadcast_resilience_alert",
]
