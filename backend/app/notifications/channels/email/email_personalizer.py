"""Email personalization."""

from datetime import datetime
from typing import Any
from uuid import UUID

from app.core.logging import get_logger

logger = get_logger(__name__)


class EmailPersonalizer:
    """
    Personalizes email content for recipients.

    Features:
    - Name personalization
    - Timezone-aware timestamps
    - Role-based content
    - Custom merge tags
    """

    def personalize(
        self,
        template: str,
        recipient_data: dict[str, Any],
    ) -> str:
        """
        Personalize email template for recipient.

        Args:
            template: Email template with merge tags
            recipient_data: Recipient-specific data

        Returns:
            Personalized email content
        """
        # Replace merge tags
        personalized = template

        for key, value in recipient_data.items():
            tag = f"{{{{{key}}}}}"  # {{key}} format
            personalized = personalized.replace(tag, str(value))

        # Add default greeting if not present
        if "{{first_name}}" in personalized and "first_name" not in recipient_data:
            personalized = personalized.replace("{{first_name}}", "there")

        logger.debug("Personalized email template")

        return personalized

    def add_greeting(
        self,
        content: str,
        recipient_name: str | None = None,
        time_of_day: str | None = None,
    ) -> str:
        """
        Add personalized greeting.

        Args:
            content: Email content
            recipient_name: Recipient's name
            time_of_day: Time of day (morning/afternoon/evening)

        Returns:
            Content with greeting
        """
        # Determine time of day
        if not time_of_day:
            hour = datetime.utcnow().hour
            if hour < 12:
                time_of_day = "morning"
            elif hour < 18:
                time_of_day = "afternoon"
            else:
                time_of_day = "evening"

        # Build greeting
        greeting = f"Good {time_of_day}"
        if recipient_name:
            greeting += f", {recipient_name}"

        return f"{greeting},\n\n{content}"

    def format_name(
        self,
        first_name: str | None = None,
        last_name: str | None = None,
        title: str | None = None,
    ) -> str:
        """
        Format name with military conventions.

        Args:
            first_name: First name
            last_name: Last name
            title: Military title/rank

        Returns:
            Formatted name
        """
        if title and last_name:
            return f"{title} {last_name}"
        elif first_name and last_name:
            return f"{first_name} {last_name}"
        elif last_name:
            return last_name
        elif first_name:
            return first_name
        else:
            return "User"
