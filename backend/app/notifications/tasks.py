"""
Celery Tasks for Notification Delivery.

Provides background tasks for sending notifications via various channels.
Tasks use proper retry logic with exponential backoff.
"""

import logging
from datetime import datetime
from uuid import UUID

import httpx
from celery import shared_task

from app.services.email_service import EmailService, EmailConfig

logger = logging.getLogger(__name__)

# Lazy-loaded email service instance
_email_service: EmailService | None = None


def get_email_service() -> EmailService:
    """Get or create the email service singleton."""
    global _email_service
    if _email_service is None:
        _email_service = EmailService(EmailConfig.from_env())
    return _email_service


@shared_task(
    bind=True,  # Required for self.retry()
    name="app.notifications.tasks.send_email",
    max_retries=3,
    default_retry_delay=60,
    autoretry_for=(Exception,),
    retry_backoff=True,  # Exponential backoff
    retry_backoff_max=300,  # Max 5 minutes between retries
)
def send_email(
    self,
    to: str,
    subject: str,
    body: str,
    html: str | None = None,
) -> dict:
    """
    Send an email notification via SMTP.

    Uses EmailService for actual delivery. Retries on failure with
    exponential backoff (60s, 120s, 240s).

    Args:
        to: Recipient email address
        subject: Email subject line
        body: Plain text body (used if html is None)
        html: HTML body (preferred if provided)

    Returns:
        Dict with delivery status and metadata
    """
    logger.info("Sending email to %s: %s (attempt %d)", to, subject, self.request.retries + 1)

    try:
        email_service = get_email_service()

        # Use html if provided, otherwise wrap plain text in basic HTML
        if html:
            body_html = html
            body_text = body
        else:
            body_html = f"<html><body><pre>{body}</pre></body></html>"
            body_text = body

        success = email_service.send_email(
            to_email=to,
            subject=subject,
            body_html=body_html,
            body_text=body_text,
        )

        if not success:
            raise RuntimeError(f"EmailService.send_email returned False for {to}")

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "to": to,
            "subject": subject,
            "status": "sent",
            "attempts": self.request.retries + 1,
        }

    except Exception as e:
        logger.warning(
            "Email to %s failed (attempt %d/%d): %s",
            to,
            self.request.retries + 1,
            self.max_retries + 1,
            str(e),
        )
        # Let autoretry_for handle the retry, or raise to trigger it
        raise


@shared_task(
    bind=True,
    name="app.notifications.tasks.send_webhook",
    max_retries=3,
    default_retry_delay=30,
    autoretry_for=(httpx.HTTPError, httpx.TimeoutException),
    retry_backoff=True,
    retry_backoff_max=120,
)
def send_webhook(
    self,
    url: str,
    payload: dict,
) -> dict:
    """
    Send a webhook notification via HTTP POST.

    Makes synchronous HTTP POST request with retry logic.
    Retries on HTTP errors and timeouts with exponential backoff.

    Args:
        url: Webhook endpoint URL
        payload: JSON payload to send

    Returns:
        Dict with delivery status and response info
    """
    logger.info("Sending webhook to %s (attempt %d)", url, self.request.retries + 1)

    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.post(url, json=payload)
            response.raise_for_status()

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "url": url,
            "status": "sent",
            "status_code": response.status_code,
            "attempts": self.request.retries + 1,
        }

    except httpx.HTTPError as e:
        logger.warning(
            "Webhook to %s failed (attempt %d/%d): %s",
            url,
            self.request.retries + 1,
            self.max_retries + 1,
            str(e),
        )
        raise


@shared_task(
    bind=True,
    name="app.notifications.tasks.detect_leave_conflicts",
    max_retries=3,
    default_retry_delay=60,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=300,
)
def detect_leave_conflicts(
    self,
    absence_id: str,
) -> dict:
    """
    Background task to detect conflicts after leave creation/approval.

    This task:
    1. Checks for FMIT schedule conflicts with the leave
    2. Creates conflict alerts for any detected issues
    3. Notifies affected faculty if configured

    Retries on failure with exponential backoff.

    Args:
        absence_id: UUID of the absence record to check

    Returns:
        Dict with conflict detection results
    """
    from app.db.session import task_session_scope
    from app.services.conflict_auto_detector import ConflictAutoDetector

    logger.info(
        "Detecting conflicts for leave %s (attempt %d)",
        absence_id,
        self.request.retries + 1,
    )

    try:
        # Use task_session_scope for proper transaction handling
        with task_session_scope() as db:
            # Initialize conflict detector
            detector = ConflictAutoDetector(db)

            # Detect conflicts for this absence
            conflicts = detector.detect_conflicts_for_absence(UUID(absence_id))

            # Create conflict alerts if any found
            alert_ids = []
            if conflicts:
                alert_ids = detector.create_conflict_alerts(conflicts)
                logger.info(
                    "Created %d conflict alerts for leave %s",
                    len(alert_ids),
                    absence_id,
                )

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "absence_id": absence_id,
            "conflicts_found": len(conflicts),
            "alerts_created": len(alert_ids),
            "status": "completed",
            "attempts": self.request.retries + 1,
        }

    except Exception as e:
        logger.warning(
            "Conflict detection for leave %s failed (attempt %d/%d): %s",
            absence_id,
            self.request.retries + 1,
            self.max_retries + 1,
            str(e),
        )
        raise
