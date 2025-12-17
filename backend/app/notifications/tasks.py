"""
Celery Tasks for Notification Delivery.

Provides background tasks for sending notifications via various channels.
"""

import logging
from datetime import datetime

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(
    name="app.notifications.tasks.send_email",
    max_retries=3,
    default_retry_delay=60,
)
def send_email(
    to: str,
    subject: str,
    body: str,
    html: str | None = None,
) -> dict:
    """
    Send an email notification.

    In production, integrate with SMTP (smtplib) or a service like SendGrid/SES.
    Currently logs only - actual sending is stubbed.
    """
    logger.info("Sending email to %s: %s", to, subject)

    # NOTE: Implement email sending here. Options:
    # - smtplib for direct SMTP
    # - SendGrid/Mailgun/SES SDK for managed email
    # - See docs/TODO_RESILIENCE.md for production checklist
    return {
        "timestamp": datetime.now().isoformat(),
        "to": to,
        "subject": subject,
        "status": "queued",
    }


@shared_task(
    name="app.notifications.tasks.send_webhook",
    max_retries=3,
    default_retry_delay=30,
)
def send_webhook(
    url: str,
    payload: dict,
) -> dict:
    """
    Send a webhook notification.

    In production, makes HTTP POST to the URL with JSON payload.
    Currently logs only - actual HTTP request is stubbed.
    """
    logger.info("Sending webhook to %s", url)

    # NOTE: Implement HTTP POST here. Recommended: httpx (async-friendly)
    # Example:
    # import httpx
    # async with httpx.AsyncClient() as client:
    #     response = await client.post(url, json=payload, timeout=30)
    #     response.raise_for_status()
    return {
        "timestamp": datetime.now().isoformat(),
        "url": url,
        "status": "queued",
    }
