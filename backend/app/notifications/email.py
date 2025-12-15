"""
Email sender module for notifications.

Handles SMTP email sending with HTML and plain text support.
Uses async patterns for non-blocking email delivery.
"""
import asyncio
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
from functools import lru_cache

from pydantic_settings import BaseSettings


class EmailSettings(BaseSettings):
    """Email configuration from environment variables."""

    SMTP_HOST: str = "localhost"
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_USE_TLS: bool = True
    SMTP_FROM_EMAIL: str = "noreply@residency-scheduler.com"
    SMTP_FROM_NAME: str = "Residency Scheduler"

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_email_settings() -> EmailSettings:
    """Get cached email settings instance."""
    return EmailSettings()


class EmailSender:
    """SMTP email sender with HTML and plain text support."""

    def __init__(self, settings: Optional[EmailSettings] = None):
        """Initialize email sender with optional settings."""
        self.settings = settings or get_email_settings()

    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        plain_content: Optional[str] = None,
        to_name: Optional[str] = None,
    ) -> bool:
        """
        Send an email asynchronously.

        Args:
            to_email: Recipient email address
            subject: Email subject line
            html_content: HTML version of email body
            plain_content: Plain text version (optional, auto-generated if not provided)
            to_name: Recipient name (optional)

        Returns:
            bool: True if email sent successfully, False otherwise
        """
        try:
            # Run blocking SMTP operation in thread pool
            await asyncio.to_thread(
                self._send_email_sync,
                to_email=to_email,
                subject=subject,
                html_content=html_content,
                plain_content=plain_content,
                to_name=to_name,
            )
            return True
        except Exception as e:
            # Log error but don't crash
            print(f"Failed to send email to {to_email}: {str(e)}")
            return False

    def _send_email_sync(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        plain_content: Optional[str] = None,
        to_name: Optional[str] = None,
    ) -> None:
        """
        Synchronous email sending implementation.

        This is called via asyncio.to_thread for async execution.
        """
        # Create message container
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"{self.settings.SMTP_FROM_NAME} <{self.settings.SMTP_FROM_EMAIL}>"

        if to_name:
            msg["To"] = f"{to_name} <{to_email}>"
        else:
            msg["To"] = to_email

        # Generate plain text version if not provided
        if not plain_content:
            # Simple HTML to plain text conversion
            plain_content = self._html_to_plain(html_content)

        # Attach both plain and HTML versions
        part1 = MIMEText(plain_content, "plain")
        part2 = MIMEText(html_content, "html")
        msg.attach(part1)
        msg.attach(part2)

        # Send email
        with smtplib.SMTP(self.settings.SMTP_HOST, self.settings.SMTP_PORT) as server:
            if self.settings.SMTP_USE_TLS:
                server.starttls()

            if self.settings.SMTP_USER and self.settings.SMTP_PASSWORD:
                server.login(self.settings.SMTP_USER, self.settings.SMTP_PASSWORD)

            server.send_message(msg)

    async def send_batch(
        self,
        emails: list[dict],
        max_concurrent: int = 5,
    ) -> dict[str, bool]:
        """
        Send multiple emails concurrently.

        Args:
            emails: List of email dictionaries with keys: to_email, subject, html_content, etc.
            max_concurrent: Maximum number of concurrent email sends

        Returns:
            dict mapping email addresses to success status
        """
        results = {}

        # Create tasks for all emails
        tasks = []
        for email_data in emails:
            task = self.send_email(
                to_email=email_data["to_email"],
                subject=email_data["subject"],
                html_content=email_data["html_content"],
                plain_content=email_data.get("plain_content"),
                to_name=email_data.get("to_name"),
            )
            tasks.append((email_data["to_email"], task))

        # Execute with concurrency limit
        semaphore = asyncio.Semaphore(max_concurrent)

        async def send_with_limit(email: str, task):
            async with semaphore:
                result = await task
                return email, result

        # Run all tasks
        completed = await asyncio.gather(
            *[send_with_limit(email, task) for email, task in tasks],
            return_exceptions=True
        )

        # Process results
        for item in completed:
            if isinstance(item, tuple):
                email, success = item
                results[email] = success
            else:
                # Exception occurred
                results["unknown"] = False

        return results

    @staticmethod
    def _html_to_plain(html: str) -> str:
        """
        Convert HTML to plain text (simple implementation).

        For production, consider using html2text or beautifulsoup.
        """
        import re

        # Remove HTML tags
        text = re.sub(r"<[^>]+>", "", html)

        # Decode common HTML entities
        text = text.replace("&nbsp;", " ")
        text = text.replace("&amp;", "&")
        text = text.replace("&lt;", "<")
        text = text.replace("&gt;", ">")
        text = text.replace("&quot;", '"')

        # Clean up whitespace
        text = re.sub(r"\n\s*\n", "\n\n", text)
        text = text.strip()

        return text
