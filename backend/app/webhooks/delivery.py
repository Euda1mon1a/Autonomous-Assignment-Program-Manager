"""Webhook delivery manager with retry logic and backoff.

Handles the actual HTTP delivery of webhooks with:
- Exponential backoff for retries
- Timeout handling
- Dead letter queue for failed deliveries
- Comprehensive logging
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.webhooks.models import (
    Webhook,
    WebhookDeadLetter,
    WebhookDelivery,
    WebhookDeliveryStatus,
)
from app.webhooks.signatures import WebhookSignatureGenerator

logger = logging.getLogger(__name__)


class WebhookDeliveryManager:
    """
    Manages webhook delivery with retry logic and exponential backoff.

    Implements:
    - Exponential backoff: 2^attempt * base_delay (e.g., 60s, 120s, 240s, 480s, 960s)
    - Timeout handling per webhook configuration
    - Dead letter queue for permanently failed deliveries
    - Response logging for debugging
    """

    def __init__(
        self,
        base_retry_delay_seconds: int = 60,
        max_retry_delay_seconds: int = 3600,
        timestamp_tolerance_seconds: int = 300
    ):
        """
        Initialize the delivery manager.

        Args:
            base_retry_delay_seconds: Base delay for exponential backoff (default: 60s)
            max_retry_delay_seconds: Maximum retry delay cap (default: 3600s = 1 hour)
            timestamp_tolerance_seconds: Timestamp tolerance for signature verification
        """
        self.base_retry_delay = base_retry_delay_seconds
        self.max_retry_delay = max_retry_delay_seconds
        self.signature_generator = WebhookSignatureGenerator(timestamp_tolerance_seconds)

    async def deliver(
        self,
        db: AsyncSession,
        delivery_id: str,
        raise_on_error: bool = False
    ) -> bool:
        """
        Attempt to deliver a webhook.

        Args:
            db: Database session
            delivery_id: Webhook delivery ID
            raise_on_error: If True, raise exceptions instead of catching them

        Returns:
            True if delivery succeeded, False otherwise

        Raises:
            Exception: If raise_on_error=True and delivery fails
        """
        # Load delivery
        result = await db.execute(
            select(WebhookDelivery)
            .where(WebhookDelivery.id == delivery_id)
        )
        delivery = result.scalar_one_or_none()

        if not delivery:
            logger.error(f"Delivery {delivery_id} not found")
            return False

        # Load webhook
        result = await db.execute(
            select(Webhook).where(Webhook.id == delivery.webhook_id)
        )
        webhook = result.scalar_one_or_none()

        if not webhook:
            logger.error(f"Webhook {delivery.webhook_id} not found for delivery {delivery_id}")
            return False

        # Update delivery status
        delivery.status = WebhookDeliveryStatus.PROCESSING.value
        delivery.attempt_count += 1
        delivery.last_attempted_at = datetime.utcnow()

        if delivery.first_attempted_at is None:
            delivery.first_attempted_at = datetime.utcnow()

        await db.commit()

        try:
            # Make HTTP request
            success = await self._send_webhook(
                webhook=webhook,
                delivery=delivery,
                raise_on_error=raise_on_error
            )

            if success:
                # Mark as successful
                delivery.status = WebhookDeliveryStatus.SUCCESS.value
                delivery.completed_at = datetime.utcnow()
                webhook.last_triggered_at = datetime.utcnow()
                logger.info(
                    f"Webhook delivery {delivery_id} succeeded "
                    f"(attempt {delivery.attempt_count})"
                )
            else:
                # Handle failure
                await self._handle_delivery_failure(db, delivery, webhook)

            await db.commit()
            return success

        except Exception as e:
            logger.error(f"Error delivering webhook {delivery_id}: {e}", exc_info=True)
            delivery.error_message = str(e)
            await self._handle_delivery_failure(db, delivery, webhook)
            await db.commit()

            if raise_on_error:
                raise

            return False

    async def _send_webhook(
        self,
        webhook: Webhook,
        delivery: WebhookDelivery,
        raise_on_error: bool = False
    ) -> bool:
        """
        Send the actual HTTP request to the webhook endpoint.

        Args:
            webhook: Webhook configuration
            delivery: Delivery record
            raise_on_error: If True, raise exceptions instead of catching them

        Returns:
            True if request succeeded (2xx response), False otherwise
        """
        # Generate signature and headers
        headers = self.signature_generator.generate_headers(
            payload=delivery.payload,
            secret=webhook.secret,
            event_type=delivery.event_type,
            delivery_id=str(delivery.id)
        )

        # Add custom headers
        if webhook.custom_headers:
            headers.update(webhook.custom_headers)

        # Make request with timeout
        start_time = datetime.utcnow()

        try:
            async with httpx.AsyncClient(timeout=webhook.timeout_seconds) as client:
                response = await client.post(
                    webhook.url,
                    json=delivery.payload,
                    headers=headers
                )

            # Calculate response time
            response_time_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)

            # Update delivery with response details
            delivery.http_status_code = response.status_code
            delivery.response_time_ms = response_time_ms

            # Store response body (truncated if too long)
            response_body = response.text[:10000] if response.text else None
            delivery.response_body = response_body

            # Check if successful (2xx status)
            if 200 <= response.status_code < 300:
                logger.info(
                    f"Webhook delivered successfully to {webhook.url}: "
                    f"status={response.status_code}, time={response_time_ms}ms"
                )
                return True
            else:
                logger.warning(
                    f"Webhook delivery failed to {webhook.url}: "
                    f"status={response.status_code}, time={response_time_ms}ms"
                )
                delivery.error_message = f"HTTP {response.status_code}: {response_body}"
                return False

        except httpx.TimeoutException as e:
            logger.warning(f"Webhook timeout for {webhook.url}: {e}")
            delivery.error_message = f"Request timeout after {webhook.timeout_seconds}s"
            if raise_on_error:
                raise
            return False

        except httpx.RequestError as e:
            logger.warning(f"Webhook request error for {webhook.url}: {e}")
            delivery.error_message = f"Request error: {str(e)}"
            if raise_on_error:
                raise
            return False

        except Exception as e:
            logger.error(f"Unexpected error sending webhook to {webhook.url}: {e}", exc_info=True)
            delivery.error_message = f"Unexpected error: {str(e)}"
            if raise_on_error:
                raise
            return False

    async def _handle_delivery_failure(
        self,
        db: AsyncSession,
        delivery: WebhookDelivery,
        webhook: Webhook
    ) -> None:
        """
        Handle a failed delivery attempt.

        Schedules retry with exponential backoff or moves to dead letter queue
        if max retries exceeded.

        Args:
            db: Database session
            delivery: Failed delivery record
            webhook: Webhook configuration
        """
        # Check if we can retry
        if delivery.can_retry and webhook.retry_enabled:
            # Calculate next retry time with exponential backoff
            retry_delay = self._calculate_retry_delay(delivery.attempt_count)
            delivery.next_retry_at = datetime.utcnow() + timedelta(seconds=retry_delay)
            delivery.status = WebhookDeliveryStatus.FAILED.value

            logger.info(
                f"Webhook delivery {delivery.id} failed, will retry in {retry_delay}s "
                f"(attempt {delivery.attempt_count}/{delivery.max_attempts})"
            )
        else:
            # Max retries exceeded - move to dead letter queue
            delivery.status = WebhookDeliveryStatus.DEAD_LETTER.value
            delivery.completed_at = datetime.utcnow()

            await self._move_to_dead_letter(db, delivery, webhook)

            logger.warning(
                f"Webhook delivery {delivery.id} moved to dead letter queue "
                f"after {delivery.attempt_count} attempts"
            )

    def _calculate_retry_delay(self, attempt_count: int) -> int:
        """
        Calculate retry delay with exponential backoff.

        Formula: min(base_delay * 2^(attempt - 1), max_delay)
        Examples with base_delay=60:
        - Attempt 1: 60s
        - Attempt 2: 120s
        - Attempt 3: 240s
        - Attempt 4: 480s
        - Attempt 5: 960s

        Args:
            attempt_count: Number of attempts made

        Returns:
            Delay in seconds
        """
        delay = self.base_retry_delay * (2 ** (attempt_count - 1))
        return min(delay, self.max_retry_delay)

    async def _move_to_dead_letter(
        self,
        db: AsyncSession,
        delivery: WebhookDelivery,
        webhook: Webhook
    ) -> None:
        """
        Move a failed delivery to the dead letter queue.

        Args:
            db: Database session
            delivery: Failed delivery
            webhook: Webhook configuration
        """
        dead_letter = WebhookDeadLetter(
            delivery_id=delivery.id,
            webhook_id=webhook.id,
            event_type=delivery.event_type,
            payload=delivery.payload,
            total_attempts=delivery.attempt_count,
            last_error_message=delivery.error_message,
            last_http_status=delivery.http_status_code
        )

        db.add(dead_letter)
        logger.info(f"Created dead letter entry for delivery {delivery.id}")

    async def process_pending_deliveries(
        self,
        db: AsyncSession,
        batch_size: int = 10
    ) -> int:
        """
        Process pending webhook deliveries that are ready for retry.

        This should be called periodically by a background task (Celery).

        Args:
            db: Database session
            batch_size: Maximum number of deliveries to process

        Returns:
            Number of deliveries processed
        """
        # Find deliveries ready for retry
        result = await db.execute(
            select(WebhookDelivery)
            .where(
                WebhookDelivery.status.in_([
                    WebhookDeliveryStatus.PENDING.value,
                    WebhookDeliveryStatus.FAILED.value
                ])
            )
            .where(
                (WebhookDelivery.next_retry_at.is_(None)) |
                (WebhookDelivery.next_retry_at <= datetime.utcnow())
            )
            .limit(batch_size)
        )

        deliveries = result.scalars().all()

        processed = 0
        for delivery in deliveries:
            try:
                await self.deliver(db, str(delivery.id))
                processed += 1
            except Exception as e:
                logger.error(f"Error processing delivery {delivery.id}: {e}", exc_info=True)
                continue

        logger.info(f"Processed {processed}/{len(deliveries)} pending webhook deliveries")
        return processed
