"""SMTP client wrapper."""

import smtplib
from email.mime.multipart import MIMEMultipart
from typing import Any

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()


class SMTPClient:
    """
    SMTP client for sending emails.

    Handles connection pooling, authentication, and error handling.
    """

    def __init__(self):
        """Initialize SMTP client."""
        self.smtp_host = getattr(settings, "SMTP_HOST", "localhost")
        self.smtp_port = getattr(settings, "SMTP_PORT", 587)
        self.smtp_user = getattr(settings, "SMTP_USER", None)
        self.smtp_password = getattr(settings, "SMTP_PASSWORD", None)
        self.use_tls = getattr(settings, "SMTP_USE_TLS", True)

    async def send(self, msg: MIMEMultipart) -> str:
        """
        Send email via SMTP.

        Args:
            msg: Email message to send

        Returns:
            Message ID

        Raises:
            smtplib.SMTPException: If sending fails
        """
        try:
            # Create SMTP connection
            if self.use_tls:
                server = smtplib.SMTP(self.smtp_host, self.smtp_port)
                server.starttls()
            else:
                server = smtplib.SMTP(self.smtp_host, self.smtp_port)

            # Authenticate if credentials provided
            if self.smtp_user and self.smtp_password:
                server.login(self.smtp_user, self.smtp_password)

            # Send email
            server.send_message(msg)
            server.quit()

            # Extract message ID (or generate one)
            message_id = msg.get("Message-ID", f"<{id(msg)}@scheduler.local>")

            logger.debug("Email sent via SMTP: %s", message_id)

            return message_id

        except smtplib.SMTPException as e:
            logger.error("SMTP error: %s", e, exc_info=True)
            raise

    def test_connection(self) -> bool:
        """
        Test SMTP connection.

        Returns:
            True if connection successful
        """
        try:
            if self.use_tls:
                server = smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=10)
                server.starttls()
            else:
                server = smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=10)

            if self.smtp_user and self.smtp_password:
                server.login(self.smtp_user, self.smtp_password)

            server.quit()
            logger.info("SMTP connection test successful")
            return True

        except Exception as e:
            logger.error("SMTP connection test failed: %s", e)
            return False
