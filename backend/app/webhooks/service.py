"""Webhook service for managing webhooks and triggering events.

Provides high-level service methods for:
- Webhook registration and management
- Event triggering and dispatching
- Delivery status monitoring
- Dead letter queue management
"""
import logging
import secrets
from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.webhooks.delivery import WebhookDeliveryManager
from app.webhooks.models import (
    Webhook,
    WebhookDeadLetter,
    WebhookDelivery,
    WebhookDeliveryStatus,
    WebhookEventType,
    WebhookStatus,
)

logger = logging.getLogger(__name__)


class WebhookService:
    """
    High-level service for webhook management and event triggering.

    Handles webhook CRUD operations, event dispatching, and monitoring.
    """

    def __init__(self, delivery_manager: WebhookDeliveryManager | None = None):
        """
        Initialize the webhook service.

        Args:
            delivery_manager: Webhook delivery manager instance
        """
        self.delivery_manager = delivery_manager or WebhookDeliveryManager()

    # =========================================================================
    # Webhook Management
    # =========================================================================

    async def create_webhook(
        self,
        db: AsyncSession,
        url: str,
        name: str,
        event_types: list[str],
        description: str | None = None,
        secret: str | None = None,
        custom_headers: dict[str, str] | None = None,
        timeout_seconds: int = 30,
        max_retries: int = 5,
        owner_id: UUID | None = None,
        metadata: dict[str, Any] | None = None
    ) -> Webhook:
        """
        Create a new webhook endpoint.

        Args:
            db: Database session
            url: Webhook endpoint URL
            name: Descriptive name for the webhook
            event_types: List of event types to subscribe to
            description: Optional description
            secret: Shared secret for signing (auto-generated if not provided)
            custom_headers: Custom headers to include in requests
            timeout_seconds: Request timeout in seconds
            max_retries: Maximum retry attempts
            owner_id: Optional owner person ID
            metadata: Optional metadata

        Returns:
            Created webhook

        Raises:
            ValueError: If event types are invalid
        """
        # Validate event types
        valid_event_types = {e.value for e in WebhookEventType}
        invalid_events = set(event_types) - valid_event_types

        if invalid_events:
            raise ValueError(
                f"Invalid event types: {invalid_events}. "
                f"Valid types: {valid_event_types}"
            )

        # Generate secret if not provided
        if not secret:
            secret = secrets.token_urlsafe(32)

        webhook = Webhook(
            url=url,
            name=name,
            description=description,
            event_types=event_types,
            secret=secret,
            custom_headers=custom_headers or {},
            timeout_seconds=timeout_seconds,
            max_retries=max_retries,
            owner_id=owner_id,
            metadata=metadata or {},
            status=WebhookStatus.ACTIVE.value
        )

        db.add(webhook)
        await db.commit()
        await db.refresh(webhook)

        logger.info(
            f"Created webhook '{name}' ({webhook.id}) "
            f"for events: {', '.join(event_types)}"
        )

        return webhook

    async def get_webhook(
        self,
        db: AsyncSession,
        webhook_id: UUID
    ) -> Webhook | None:
        """Get a webhook by ID."""
        result = await db.execute(
            select(Webhook).where(Webhook.id == webhook_id)
        )
        return result.scalar_one_or_none()

    async def list_webhooks(
        self,
        db: AsyncSession,
        status: WebhookStatus | None = None,
        event_type: str | None = None,
        owner_id: UUID | None = None,
        skip: int = 0,
        limit: int = 100
    ) -> list[Webhook]:
        """
        List webhooks with optional filtering.

        Args:
            db: Database session
            status: Filter by status
            event_type: Filter by subscribed event type
            owner_id: Filter by owner
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of webhooks
        """
        query = select(Webhook)

        if status:
            query = query.where(Webhook.status == status.value)

        if owner_id:
            query = query.where(Webhook.owner_id == owner_id)

        # Note: event_type filtering requires array contains check
        # This is PostgreSQL-specific and would need adjustment for other DBs

        query = query.offset(skip).limit(limit).order_by(Webhook.created_at.desc())

        result = await db.execute(query)
        return list(result.scalars().all())

    async def update_webhook(
        self,
        db: AsyncSession,
        webhook_id: UUID,
        **updates
    ) -> Webhook | None:
        """
        Update a webhook.

        Args:
            db: Database session
            webhook_id: Webhook ID
            **updates: Fields to update

        Returns:
            Updated webhook or None if not found
        """
        webhook = await self.get_webhook(db, webhook_id)
        if not webhook:
            return None

        # Apply updates
        for key, value in updates.items():
            if hasattr(webhook, key) and value is not None:
                setattr(webhook, key, value)

        webhook.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(webhook)

        logger.info(f"Updated webhook {webhook_id}")
        return webhook

    async def delete_webhook(
        self,
        db: AsyncSession,
        webhook_id: UUID
    ) -> bool:
        """
        Delete a webhook and all associated deliveries.

        Args:
            db: Database session
            webhook_id: Webhook ID

        Returns:
            True if deleted, False if not found
        """
        result = await db.execute(
            delete(Webhook).where(Webhook.id == webhook_id)
        )

        if result.rowcount > 0:
            await db.commit()
            logger.info(f"Deleted webhook {webhook_id}")
            return True

        return False

    async def pause_webhook(
        self,
        db: AsyncSession,
        webhook_id: UUID
    ) -> Webhook | None:
        """Pause a webhook (stops delivery without deleting)."""
        return await self.update_webhook(
            db,
            webhook_id,
            status=WebhookStatus.PAUSED.value
        )

    async def resume_webhook(
        self,
        db: AsyncSession,
        webhook_id: UUID
    ) -> Webhook | None:
        """Resume a paused webhook."""
        return await self.update_webhook(
            db,
            webhook_id,
            status=WebhookStatus.ACTIVE.value
        )

    # =========================================================================
    # Event Triggering
    # =========================================================================

    async def trigger_event(
        self,
        db: AsyncSession,
        event_type: str,
        payload: dict[str, Any],
        event_id: str | None = None,
        immediate: bool = False
    ) -> int:
        """
        Trigger a webhook event.

        Finds all active webhooks subscribed to the event type and
        creates delivery records for each.

        Args:
            db: Database session
            event_type: Event type (e.g., "schedule.created")
            payload: Event payload data
            event_id: Optional event identifier for tracking
            immediate: If True, attempt immediate delivery instead of queuing

        Returns:
            Number of webhooks triggered

        Example:
            >>> service = WebhookService()
            >>> count = await service.trigger_event(
            ...     db,
            ...     "schedule.created",
            ...     {"schedule_id": "123", "created_by": "user-456"}
            ... )
        """
        # Find active webhooks subscribed to this event
        result = await db.execute(
            select(Webhook)
            .where(Webhook.status == WebhookStatus.ACTIVE.value)
        )
        webhooks = result.scalars().all()

        # Filter webhooks subscribed to this event type
        subscribed_webhooks = [
            webhook for webhook in webhooks
            if webhook.is_subscribed_to(event_type)
        ]

        if not subscribed_webhooks:
            logger.debug(f"No active webhooks subscribed to event '{event_type}'")
            return 0

        # Create delivery records for each webhook
        deliveries_created = 0

        for webhook in subscribed_webhooks:
            delivery = WebhookDelivery(
                webhook_id=webhook.id,
                event_type=event_type,
                event_id=event_id,
                payload=payload,
                max_attempts=webhook.max_retries,
                status=WebhookDeliveryStatus.PENDING.value
            )

            db.add(delivery)
            deliveries_created += 1

        await db.commit()

        logger.info(
            f"Triggered event '{event_type}' for {deliveries_created} webhooks"
        )

        # If immediate delivery requested, process now
        if immediate:
            for webhook in subscribed_webhooks:
                # Get the delivery we just created
                result = await db.execute(
                    select(WebhookDelivery)
                    .where(WebhookDelivery.webhook_id == webhook.id)
                    .where(WebhookDelivery.event_type == event_type)
                    .where(WebhookDelivery.status == WebhookDeliveryStatus.PENDING.value)
                    .order_by(WebhookDelivery.created_at.desc())
                    .limit(1)
                )
                delivery = result.scalar_one_or_none()

                if delivery:
                    await self.delivery_manager.deliver(db, str(delivery.id))

        return deliveries_created

    # =========================================================================
    # Delivery Monitoring
    # =========================================================================

    async def get_delivery_status(
        self,
        db: AsyncSession,
        delivery_id: UUID
    ) -> WebhookDelivery | None:
        """Get delivery status by ID."""
        result = await db.execute(
            select(WebhookDelivery).where(WebhookDelivery.id == delivery_id)
        )
        return result.scalar_one_or_none()

    async def list_deliveries(
        self,
        db: AsyncSession,
        webhook_id: UUID | None = None,
        status: WebhookDeliveryStatus | None = None,
        event_type: str | None = None,
        skip: int = 0,
        limit: int = 100
    ) -> list[WebhookDelivery]:
        """
        List webhook deliveries with filtering.

        Args:
            db: Database session
            webhook_id: Filter by webhook
            status: Filter by status
            event_type: Filter by event type
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of deliveries
        """
        query = select(WebhookDelivery)

        if webhook_id:
            query = query.where(WebhookDelivery.webhook_id == webhook_id)

        if status:
            query = query.where(WebhookDelivery.status == status.value)

        if event_type:
            query = query.where(WebhookDelivery.event_type == event_type)

        query = query.offset(skip).limit(limit).order_by(WebhookDelivery.created_at.desc())

        result = await db.execute(query)
        return list(result.scalars().all())

    async def retry_delivery(
        self,
        db: AsyncSession,
        delivery_id: UUID
    ) -> bool:
        """
        Manually retry a failed delivery.

        Args:
            db: Database session
            delivery_id: Delivery ID

        Returns:
            True if retry succeeded
        """
        delivery = await self.get_delivery_status(db, delivery_id)

        if not delivery:
            logger.warning(f"Delivery {delivery_id} not found")
            return False

        if delivery.is_final:
            logger.warning(f"Delivery {delivery_id} is in final state: {delivery.status}")
            return False

        return await self.delivery_manager.deliver(db, str(delivery_id))

    # =========================================================================
    # Dead Letter Queue Management
    # =========================================================================

    async def list_dead_letters(
        self,
        db: AsyncSession,
        webhook_id: UUID | None = None,
        resolved: bool | None = None,
        skip: int = 0,
        limit: int = 100
    ) -> list[WebhookDeadLetter]:
        """
        List dead letter queue entries.

        Args:
            db: Database session
            webhook_id: Filter by webhook
            resolved: Filter by resolution status
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of dead letter entries
        """
        query = select(WebhookDeadLetter)

        if webhook_id:
            query = query.where(WebhookDeadLetter.webhook_id == webhook_id)

        if resolved is not None:
            query = query.where(WebhookDeadLetter.resolved == resolved)

        query = query.offset(skip).limit(limit).order_by(WebhookDeadLetter.created_at.desc())

        result = await db.execute(query)
        return list(result.scalars().all())

    async def resolve_dead_letter(
        self,
        db: AsyncSession,
        dead_letter_id: UUID,
        resolved_by: UUID,
        notes: str | None = None,
        retry: bool = False
    ) -> bool:
        """
        Resolve a dead letter entry.

        Args:
            db: Database session
            dead_letter_id: Dead letter ID
            resolved_by: User ID resolving the entry
            notes: Resolution notes
            retry: If True, retry the delivery

        Returns:
            True if resolution succeeded
        """
        result = await db.execute(
            select(WebhookDeadLetter).where(WebhookDeadLetter.id == dead_letter_id)
        )
        dead_letter = result.scalar_one_or_none()

        if not dead_letter:
            return False

        # Mark as resolved
        dead_letter.resolved = True
        dead_letter.resolved_at = datetime.utcnow()
        dead_letter.resolved_by = resolved_by
        dead_letter.resolution_notes = notes

        await db.commit()

        logger.info(f"Resolved dead letter {dead_letter_id}")

        # Optionally retry the delivery
        if retry:
            # Create new delivery attempt
            delivery = WebhookDelivery(
                webhook_id=dead_letter.webhook_id,
                event_type=dead_letter.event_type,
                payload=dead_letter.payload,
                status=WebhookDeliveryStatus.PENDING.value
            )
            db.add(delivery)
            await db.commit()
            await db.refresh(delivery)

            logger.info(f"Created retry delivery {delivery.id} for dead letter {dead_letter_id}")
            return await self.delivery_manager.deliver(db, str(delivery.id))

        return True
