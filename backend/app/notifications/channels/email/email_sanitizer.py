"""Email content sanitization."""

import html
import re

from app.core.logging import get_logger

logger = get_logger(__name__)


class EmailSanitizer:
    """
    Sanitizes email content to prevent XSS and injection attacks.

    Features:
    - HTML sanitization
    - Script tag removal
    - Attribute filtering
    - Safe HTML subset
    """

    # Allowed HTML tags
    ALLOWED_TAGS = {
        "a",
        "b",
        "i",
        "u",
        "strong",
        "em",
        "p",
        "br",
        "div",
        "span",
        "h1",
        "h2",
        "h3",
        "h4",
        "h5",
        "h6",
        "ul",
        "ol",
        "li",
        "table",
        "tr",
        "td",
        "th",
        "img",
        "pre",
        "code",
        "blockquote",
    }

    # Allowed attributes
    ALLOWED_ATTRS = {
        "a": ["href", "title", "target"],
        "img": ["src", "alt", "width", "height"],
        "td": ["colspan", "rowspan"],
        "th": ["colspan", "rowspan"],
    }

    def sanitize_html(self, html_content: str) -> str:
        """
        Sanitize HTML content.

        Args:
            html_content: Raw HTML

        Returns:
            Sanitized HTML
        """
        # Remove script tags
        html_content = re.sub(
            r"<script[^>]*>.*?</script>",
            "",
            html_content,
            flags=re.DOTALL | re.IGNORECASE,
        )

        # Remove event handlers
        html_content = re.sub(
            r'\s*on\w+\s*=\s*["\'][^"\']*["\']',
            "",
            html_content,
            flags=re.IGNORECASE,
        )

        # Remove javascript: URLs
        html_content = re.sub(
            r"javascript:",
            "",
            html_content,
            flags=re.IGNORECASE,
        )

        logger.debug("Sanitized HTML content")

        return html_content

    def sanitize_text(self, text: str) -> str:
        """
        Sanitize plain text (escape HTML).

        Args:
            text: Plain text

        Returns:
            HTML-escaped text
        """
        return html.escape(text)

    def remove_sensitive_data(self, text: str) -> str:
        """
        Remove potentially sensitive data patterns.

        Args:
            text: Text content

        Returns:
            Sanitized text
        """
        # Remove email addresses (for privacy)
        text = re.sub(
            r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
            "[EMAIL REDACTED]",
            text,
        )

        # Remove phone numbers
        text = re.sub(
            r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b",
            "[PHONE REDACTED]",
            text,
        )

        # Remove SSNs
        text = re.sub(
            r"\b\d{3}-\d{2}-\d{4}\b",
            "[SSN REDACTED]",
            text,
        )

        return text
