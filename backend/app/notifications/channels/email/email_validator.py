"""Email address validation."""

import re
from typing import Any

from app.core.logging import get_logger

logger = get_logger(__name__)


class EmailValidator:
    """
    Validates email addresses.

    Features:
    - RFC 5322 compliance
    - Domain validation
    - Disposable email detection
    - Military email pattern validation
    """

    # Email regex pattern (simplified RFC 5322)
    EMAIL_PATTERN = re.compile(
        r"^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$"
    )

    # Military domains
    MILITARY_DOMAINS = [".mil", ".army.mil", ".navy.mil", ".af.mil"]

    # Disposable email domains (partial list)
    DISPOSABLE_DOMAINS = [
        "tempmail.com",
        "10minutemail.com",
        "guerrillamail.com",
        "mailinator.com",
    ]

    def validate(self, email: str) -> tuple[bool, str | None]:
        """
        Validate email address.

        Args:
            email: Email address to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not email:
            return False, "Email address required"

        # Check format
        if not self.EMAIL_PATTERN.match(email):
            return False, "Invalid email format"

        # Check disposable
        if self.is_disposable(email):
            return False, "Disposable email addresses not allowed"

        return True, None

    def is_military(self, email: str) -> bool:
        """Check if email is from military domain."""
        email_lower = email.lower()
        return any(email_lower.endswith(domain) for domain in self.MILITARY_DOMAINS)

    def is_disposable(self, email: str) -> bool:
        """Check if email is from disposable provider."""
        domain = email.split("@")[-1].lower()
        return domain in self.DISPOSABLE_DOMAINS

    def normalize(self, email: str) -> str:
        """Normalize email address (lowercase, trim)."""
        return email.strip().lower()
