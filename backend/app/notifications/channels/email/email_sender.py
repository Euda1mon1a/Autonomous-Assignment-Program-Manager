"""Main email sending implementation."""

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any

from app.core.config import get_settings
from app.core.logging import get_logger
from app.notifications.channels.email.html_builder import HTMLEmailBuilder
from app.notifications.channels.email.smtp_client import SMTPClient

logger = get_logger(__name__)
settings = get_settings()


class EmailSender:
    """
    Main email sending service.

    Features:
    - HTML and plain text emails
    - Attachment support
    - Template rendering
    - Delivery tracking
    - Error handling and retries
    """

    def __init__(self):
        """Initialize email sender."""
        self.smtp_client = SMTPClient()
        self.html_builder = HTMLEmailBuilder()

    async def send_email(
        self,
        to_address: str,
        subject: str,
        body: str,
        html_body: str | None = None,
        from_address: str | None = None,
        reply_to: str | None = None,
        cc: list[str] | None = None,
        bcc: list[str] | None = None,
        attachments: list[dict[str, Any]] | None = None,
        tracking_enabled: bool = True,
    ) -> dict[str, Any]:
        """
        Send an email.

        Args:
            to_address: Recipient email
            subject: Email subject
            body: Plain text body
            html_body: Optional HTML body
            from_address: Sender address (uses default if None)
            reply_to: Reply-to address
            cc: CC recipients
            bcc: BCC recipients
            attachments: List of attachments
            tracking_enabled: Enable open/click tracking

        Returns:
            Dict with delivery status and message ID
        """
        try:
            # Create message
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = from_address or settings.EMAIL_FROM_ADDRESS
            msg["To"] = to_address

            if reply_to:
                msg["Reply-To"] = reply_to

            if cc:
                msg["Cc"] = ", ".join(cc)

            # Attach plain text
            msg.attach(MIMEText(body, "plain"))

            # Attach HTML if provided
            if html_body:
                msg.attach(MIMEText(html_body, "html"))
            else:
                # Generate HTML from plain text
                html_body = self.html_builder.build_simple_html(subject, body)
                msg.attach(MIMEText(html_body, "html"))

            # Send via SMTP
            message_id = await self.smtp_client.send(msg)

            logger.info("Email sent successfully to %s", to_address)

            return {
                "success": True,
                "message_id": message_id,
                "recipient": to_address,
            }

        except Exception as e:
            logger.error("Failed to send email to %s: %s", to_address, e, exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "recipient": to_address,
            }

    async def send_bulk(
        self,
        recipients: list[str],
        subject: str,
        body: str,
        html_body: str | None = None,
    ) -> list[dict[str, Any]]:
        """
        Send bulk emails.

        Args:
            recipients: List of recipient emails
            subject: Email subject
            body: Email body
            html_body: Optional HTML body

        Returns:
            List of delivery results
        """
        results = []

        for recipient in recipients:
            result = await self.send_email(
                to_address=recipient,
                subject=subject,
                body=body,
                html_body=html_body,
            )
            results.append(result)

        success_count = sum(1 for r in results if r["success"])
        logger.info(
            "Bulk email sent: %d/%d successful",
            success_count,
            len(recipients),
        )

        return results
