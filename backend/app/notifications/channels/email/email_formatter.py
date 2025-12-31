"""Email content formatting."""

import html
import re
from typing import Any

from app.core.logging import get_logger

logger = get_logger(__name__)


class EmailFormatter:
    """
    Formats email content for optimal display.

    Features:
    - Plain text to HTML conversion
    - Line wrapping
    - Link detection and conversion
    - Emoji handling
    """

    def format_plain_text(self, text: str, max_line_length: int = 78) -> str:
        """
        Format plain text with line wrapping.

        Args:
            text: Plain text content
            max_line_length: Maximum line length

        Returns:
            Formatted plain text
        """
        lines = []

        for paragraph in text.split("\n\n"):
            words = paragraph.split()
            current_line = []
            current_length = 0

            for word in words:
                word_length = len(word) + 1  # +1 for space

                if current_length + word_length > max_line_length:
                    lines.append(" ".join(current_line))
                    current_line = [word]
                    current_length = word_length
                else:
                    current_line.append(word)
                    current_length += word_length

            if current_line:
                lines.append(" ".join(current_line))

            lines.append("")  # Paragraph break

        return "\n".join(lines)

    def plain_to_html(self, text: str) -> str:
        """
        Convert plain text to HTML.

        Args:
            text: Plain text

        Returns:
            HTML formatted text
        """
        # Escape HTML
        text = html.escape(text)

        # Convert newlines to <br>
        text = text.replace("\n\n", "</p><p>")
        text = text.replace("\n", "<br>")

        # Wrap in paragraphs
        text = f"<p>{text}</p>"

        # Convert URLs to links
        text = self._linkify(text)

        return text

    def _linkify(self, text: str) -> str:
        """Convert URLs to clickable links."""
        url_pattern = re.compile(
            r'(https?://[^\s<>"\']+|www\.[^\s<>"\']+)'
        )

        def replace_url(match):
            url = match.group(0)
            if not url.startswith("http"):
                url = f"https://{url}"
            return f'<a href="{url}">{match.group(0)}</a>'

        return url_pattern.sub(replace_url, text)

    def add_signature(self, body: str, signature: str) -> str:
        """Add signature to email body."""
        return f"{body}\n\n--\n{signature}"
