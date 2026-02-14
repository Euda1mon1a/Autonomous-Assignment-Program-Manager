"""Webhook API routes.

Provides endpoints for:
- Webhook registration and management
- Event triggering
- Delivery monitoring
- Dead letter queue management
"""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.core.security import get_current_active_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.webhook import (
    WebhookCreate,
    WebhookDeadLetterListResponse,
    WebhookDeadLetterResolveRequest,
    WebhookDeadLetterResponse,
    WebhookDeliveryListResponse,
    WebhookDeliveryResponse,
    WebhookDeliveryRetryRequest,
    WebhookEventTrigger,
    WebhookEventTriggerResponse,
    WebhookListResponse,
    WebhookResponse,
    WebhookUpdate,
)
from app.webhooks.models import WebhookDeliveryStatus, WebhookStatus
from app.webhooks.service import WebhookService

router = APIRouter()
logger = logging.getLogger(__name__)


def get_webhook_service() -> WebhookService:
    """Dependency for webhook service."""
    return WebhookService()

    # ============================================================================
    # Webhook Management Endpoints
    # ============================================================================


@router.post("", response_model=WebhookResponse, status_code=status.HTTP_201_CREATED)
async def create_webhook(
    webhook_data: WebhookCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    service: WebhookService = Depends(get_webhook_service),
) -> WebhookResponse:
    """
    Create a new webhook endpoint.

    Registers a webhook that will receive HTTP POST requests
    when subscribed events occur.

    **Required permissions:** Authenticated user
    """
    try:
        webhook = await service.create_webhook(
            db=db,
            url=str(webhook_data.url),
            name=webhook_data.name,
            event_types=webhook_data.event_types,
            description=webhook_data.description,
            secret=webhook_data.secret,
            custom_headers=webhook_data.custom_headers,
            timeout_seconds=webhook_data.timeout_seconds,
            max_retries=webhook_data.max_retries,
            owner_id=current_user.id if hasattr(current_user, "id") else None,
            metadata=webhook_data.metadata,
        )
        return webhook
    except ValueError as e:
        logger.error(f"Validation error creating webhook: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except (TypeError, KeyError) as e:
        logger.error(f"Data error creating webhook: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid webhook data"
        )


@router.get("", response_model=WebhookListResponse)
async def list_webhooks(
    status_filter: WebhookStatus | None = Query(None, alias="status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    service: WebhookService = Depends(get_webhook_service),
) -> WebhookListResponse:
    """
    List all webhooks.

    **Query Parameters:**
    - status: Filter by webhook status (active, paused, disabled)
    - skip: Number of records to skip (pagination)
    - limit: Maximum number of records to return

    **Required permissions:** Authenticated user
    """
    webhooks = await service.list_webhooks(
        db=db, status=status_filter, skip=skip, limit=limit
    )

    return WebhookListResponse(
        webhooks=webhooks,
        total=len(webhooks),  # Note: This is limited by the query
        skip=skip,
        limit=limit,
    )


@router.get("/{webhook_id}", response_model=WebhookResponse)
async def get_webhook(
    webhook_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    service: WebhookService = Depends(get_webhook_service),
) -> WebhookResponse:
    """
    Get webhook details by ID.

    **Required permissions:** Authenticated user
    """
    webhook = await service.get_webhook(db, webhook_id)

    if not webhook:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Webhook {webhook_id} not found",
        )

    return webhook


@router.put("/{webhook_id}", response_model=WebhookResponse)
async def update_webhook(
    webhook_id: UUID,
    webhook_data: WebhookUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    service: WebhookService = Depends(get_webhook_service),
) -> WebhookResponse:
    """
    Update a webhook.

    **Required permissions:** Authenticated user
    """
    # Convert webhook_data to dict, excluding None values
    updates = webhook_data.model_dump(exclude_none=True)

    # Convert URL to string if present
    if "url" in updates:
        updates["url"] = str(updates["url"])

    webhook = await service.update_webhook(db, webhook_id, **updates)

    if not webhook:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Webhook {webhook_id} not found",
        )

    return webhook


@router.delete("/{webhook_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_webhook(
    webhook_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    service: WebhookService = Depends(get_webhook_service),
) -> None:
    """
    Delete a webhook and all associated deliveries.

    **Required permissions:** Authenticated user
    """
    success = await service.delete_webhook(db, webhook_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Webhook {webhook_id} not found",
        )


@router.post("/{webhook_id}/pause", response_model=WebhookResponse)
async def pause_webhook(
    webhook_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    service: WebhookService = Depends(get_webhook_service),
) -> WebhookResponse:
    """
    Pause a webhook.

    Paused webhooks will not receive new events but existing
    deliveries will continue to be retried.

    **Required permissions:** Authenticated user
    """
    webhook = await service.pause_webhook(db, webhook_id)

    if not webhook:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Webhook {webhook_id} not found",
        )

    return webhook


@router.post("/{webhook_id}/resume", response_model=WebhookResponse)
async def resume_webhook(
    webhook_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    service: WebhookService = Depends(get_webhook_service),
) -> WebhookResponse:
    """
    Resume a paused webhook.

    **Required permissions:** Authenticated user
    """
    webhook = await service.resume_webhook(db, webhook_id)

    if not webhook:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Webhook {webhook_id} not found",
        )

    return webhook

    # ============================================================================
    # Event Trigger Endpoints
    # ============================================================================


@router.post("/events/trigger", response_model=WebhookEventTriggerResponse)
async def trigger_event(
    event_data: WebhookEventTrigger,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    service: WebhookService = Depends(get_webhook_service),
) -> WebhookEventTriggerResponse:
    """
    Manually trigger a webhook event.

    This endpoint is typically used for testing or manual event dispatch.

    **Required permissions:** Authenticated user
    """
    count = await service.trigger_event(
        db=db,
        event_type=event_data.event_type,
        payload=event_data.payload,
        event_id=event_data.event_id,
        immediate=event_data.immediate,
    )

    return WebhookEventTriggerResponse(
        event_type=event_data.event_type,
        webhooks_triggered=count,
        message=f"Event '{event_data.event_type}' triggered for {count} webhook(s)",
    )

    # ============================================================================
    # Delivery Monitoring Endpoints
    # ============================================================================


@router.get("/deliveries", response_model=WebhookDeliveryListResponse)
async def list_deliveries(
    webhook_id: UUID | None = Query(None),
    status_filter: WebhookDeliveryStatus | None = Query(None, alias="status"),
    event_type: str | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    service: WebhookService = Depends(get_webhook_service),
) -> WebhookDeliveryListResponse:
    """
    List webhook deliveries with optional filtering.

    **Query Parameters:**
    - webhook_id: Filter by webhook
    - status: Filter by delivery status
    - event_type: Filter by event type
    - skip: Number of records to skip (pagination)
    - limit: Maximum number of records to return

    **Required permissions:** Authenticated user
    """
    deliveries = await service.list_deliveries(
        db=db,
        webhook_id=webhook_id,
        status=status_filter,
        event_type=event_type,
        skip=skip,
        limit=limit,
    )

    return WebhookDeliveryListResponse(
        deliveries=deliveries,
        total=len(deliveries),  # Note: This is limited by the query
        skip=skip,
        limit=limit,
    )


@router.get("/deliveries/{delivery_id}", response_model=WebhookDeliveryResponse)
async def get_delivery(
    delivery_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    service: WebhookService = Depends(get_webhook_service),
) -> WebhookDeliveryResponse:
    """
    Get delivery details by ID.

    **Required permissions:** Authenticated user
    """
    delivery = await service.get_delivery_status(db, delivery_id)

    if not delivery:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Delivery {delivery_id} not found",
        )

    return delivery


@router.post("/deliveries/retry", response_model=WebhookDeliveryResponse)
async def retry_delivery(
    retry_data: WebhookDeliveryRetryRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    service: WebhookService = Depends(get_webhook_service),
) -> WebhookDeliveryResponse:
    """
    Manually retry a failed delivery.

    **Required permissions:** Authenticated user
    """
    success = await service.retry_delivery(db, retry_data.delivery_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unable to retry delivery (not found or in final state)",
        )

        # Return updated delivery status
    delivery = await service.get_delivery_status(db, retry_data.delivery_id)
    return delivery

    # ============================================================================
    # Dead Letter Queue Endpoints
    # ============================================================================


@router.get("/dead-letters", response_model=WebhookDeadLetterListResponse)
async def list_dead_letters(
    webhook_id: UUID | None = Query(None),
    resolved: bool | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    service: WebhookService = Depends(get_webhook_service),
) -> WebhookDeadLetterListResponse:
    """
    List dead letter queue entries.

    Dead letters are webhook deliveries that have exceeded
    maximum retry attempts and require manual intervention.

    **Query Parameters:**
    - webhook_id: Filter by webhook
    - resolved: Filter by resolution status
    - skip: Number of records to skip (pagination)
    - limit: Maximum number of records to return

    **Required permissions:** Authenticated user
    """
    dead_letters = await service.list_dead_letters(
        db=db, webhook_id=webhook_id, resolved=resolved, skip=skip, limit=limit
    )

    return WebhookDeadLetterListResponse(
        dead_letters=dead_letters,
        total=len(dead_letters),  # Note: This is limited by the query
        skip=skip,
        limit=limit,
    )


@router.post(
    "/dead-letters/{dead_letter_id}/resolve", response_model=WebhookDeadLetterResponse
)
async def resolve_dead_letter(
    dead_letter_id: UUID,
    resolve_data: WebhookDeadLetterResolveRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    service: WebhookService = Depends(get_webhook_service),
):
    """
    Resolve a dead letter entry.

    Optionally retry the delivery after resolving.

    **Required permissions:** Authenticated user
    """
    # Get current user ID
    user_id = current_user.id if hasattr(current_user, "id") else None

    success = await service.resolve_dead_letter(
        db=db,
        dead_letter_id=dead_letter_id,
        resolved_by=user_id,
        notes=resolve_data.notes,
        retry=resolve_data.retry,
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dead letter {dead_letter_id} not found",
        )

        # Return updated dead letter
    dead_letters = await service.list_dead_letters(db, skip=0, limit=1)
    if dead_letters:
        return dead_letters[0]

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Dead letter {dead_letter_id} not found after resolution",
    )
