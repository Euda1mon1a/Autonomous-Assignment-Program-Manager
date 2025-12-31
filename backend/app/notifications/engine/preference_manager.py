"""User notification preference management."""

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models.notification import NotificationPreferenceRecord
from app.notifications.notification_types import NotificationType

logger = get_logger(__name__)


class UserPreferences:
    """
    User notification preferences data class.

    Attributes:
        user_id: UUID of user
        enabled_channels: List of enabled channels
        notification_types: Dict of type -> enabled status
        quiet_hours_start: Quiet hours start (0-23)
        quiet_hours_end: Quiet hours end (0-23)
        timezone: User timezone for quiet hours
        digest_enabled: Whether to receive digest emails
        digest_frequency: Digest frequency ('daily', 'weekly')
    """

    def __init__(
        self,
        user_id: UUID,
        enabled_channels: list[str] | None = None,
        notification_types: dict[str, bool] | None = None,
        quiet_hours_start: int | None = None,
        quiet_hours_end: int | None = None,
        timezone: str = "UTC",
        digest_enabled: bool = False,
        digest_frequency: str = "daily",
    ):
        """Initialize user preferences."""
        self.user_id = user_id
        self.enabled_channels = enabled_channels or ["in_app", "email"]
        self.notification_types = notification_types or {}
        self.quiet_hours_start = quiet_hours_start
        self.quiet_hours_end = quiet_hours_end
        self.timezone = timezone
        self.digest_enabled = digest_enabled
        self.digest_frequency = digest_frequency


class PreferenceManager:
    """
    Manages user notification preferences.

    Features:
    - Load and cache preferences
    - Bulk preload for batch operations
    - Channel enablement checks
    - Quiet hours enforcement
    - Notification type opt-in/opt-out
    - Digest preferences
    """

    # Default preferences for new users
    DEFAULT_PREFERENCES = UserPreferences(
        user_id=UUID("00000000-0000-0000-0000-000000000000"),
        enabled_channels=["in_app", "email"],
        notification_types={
            NotificationType.SCHEDULE_PUBLISHED.value: True,
            NotificationType.ASSIGNMENT_CHANGED.value: True,
            NotificationType.SHIFT_REMINDER_24H.value: True,
            NotificationType.SHIFT_REMINDER_1H.value: True,
            NotificationType.ACGME_WARNING.value: True,
            NotificationType.ABSENCE_APPROVED.value: True,
            NotificationType.ABSENCE_REJECTED.value: True,
        },
        quiet_hours_start=None,
        quiet_hours_end=None,
        digest_enabled=False,
        digest_frequency="daily",
    )

    def __init__(self, db: AsyncSession):
        """
        Initialize preference manager.

        Args:
            db: Database session
        """
        self.db = db
        self._cache: dict[UUID, UserPreferences] = {}

    async def get_preferences(self, user_id: UUID) -> UserPreferences:
        """
        Get user preferences.

        Args:
            user_id: UUID of user

        Returns:
            UserPreferences object
        """
        # Check cache first
        if user_id in self._cache:
            return self._cache[user_id]

        # Load from database
        result = await self.db.execute(
            select(NotificationPreferenceRecord).where(
                NotificationPreferenceRecord.user_id == user_id
            )
        )
        record = result.scalar_one_or_none()

        if record:
            preferences = UserPreferences(
                user_id=user_id,
                enabled_channels=record.get_enabled_channels(),
                notification_types=record.notification_types or {},
                quiet_hours_start=record.quiet_hours_start,
                quiet_hours_end=record.quiet_hours_end,
                timezone=getattr(record, "timezone", "UTC"),
                digest_enabled=getattr(record, "digest_enabled", False),
                digest_frequency=getattr(record, "digest_frequency", "daily"),
            )
        else:
            # Return defaults
            preferences = UserPreferences(
                user_id=user_id,
                enabled_channels=self.DEFAULT_PREFERENCES.enabled_channels.copy(),
                notification_types=self.DEFAULT_PREFERENCES.notification_types.copy(),
                quiet_hours_start=self.DEFAULT_PREFERENCES.quiet_hours_start,
                quiet_hours_end=self.DEFAULT_PREFERENCES.quiet_hours_end,
                timezone=self.DEFAULT_PREFERENCES.timezone,
                digest_enabled=self.DEFAULT_PREFERENCES.digest_enabled,
                digest_frequency=self.DEFAULT_PREFERENCES.digest_frequency,
            )

        # Cache and return
        self._cache[user_id] = preferences
        return preferences

    async def preload_preferences(self, user_ids: list[UUID]) -> None:
        """
        Preload preferences for multiple users (optimization for bulk operations).

        Args:
            user_ids: List of user UUIDs
        """
        # Get IDs not in cache
        uncached_ids = [uid for uid in user_ids if uid not in self._cache]

        if not uncached_ids:
            return

        # Bulk load from database
        result = await self.db.execute(
            select(NotificationPreferenceRecord).where(
                NotificationPreferenceRecord.user_id.in_(uncached_ids)
            )
        )
        records = result.scalars().all()

        # Build cache
        records_by_id = {record.user_id: record for record in records}

        for user_id in uncached_ids:
            if user_id in records_by_id:
                record = records_by_id[user_id]
                preferences = UserPreferences(
                    user_id=user_id,
                    enabled_channels=record.get_enabled_channels(),
                    notification_types=record.notification_types or {},
                    quiet_hours_start=record.quiet_hours_start,
                    quiet_hours_end=record.quiet_hours_end,
                    timezone=getattr(record, "timezone", "UTC"),
                    digest_enabled=getattr(record, "digest_enabled", False),
                    digest_frequency=getattr(record, "digest_frequency", "daily"),
                )
            else:
                # Use defaults
                preferences = UserPreferences(
                    user_id=user_id,
                    enabled_channels=self.DEFAULT_PREFERENCES.enabled_channels.copy(),
                    notification_types=self.DEFAULT_PREFERENCES.notification_types.copy(),
                    quiet_hours_start=self.DEFAULT_PREFERENCES.quiet_hours_start,
                    quiet_hours_end=self.DEFAULT_PREFERENCES.quiet_hours_end,
                    timezone=self.DEFAULT_PREFERENCES.timezone,
                    digest_enabled=self.DEFAULT_PREFERENCES.digest_enabled,
                    digest_frequency=self.DEFAULT_PREFERENCES.digest_frequency,
                )

            self._cache[user_id] = preferences

        logger.debug("Preloaded preferences for %d users", len(uncached_ids))

    async def should_send(
        self, preferences: UserPreferences, notification_type: NotificationType
    ) -> bool:
        """
        Check if notification should be sent based on preferences.

        Args:
            preferences: User preferences
            notification_type: Type of notification

        Returns:
            True if should send
        """
        # Check if type is enabled
        if not preferences.notification_types.get(notification_type.value, True):
            logger.debug(
                "Notification type disabled for user %s: %s",
                preferences.user_id,
                notification_type.value,
            )
            return False

        # Check quiet hours
        if await self._is_in_quiet_hours(preferences):
            # Allow critical notifications during quiet hours
            if notification_type == NotificationType.ACGME_WARNING:
                logger.debug("ACGME warning bypassing quiet hours")
                return True

            logger.debug(
                "User %s in quiet hours, suppressing notification",
                preferences.user_id,
            )
            return False

        return True

    async def _is_in_quiet_hours(self, preferences: UserPreferences) -> bool:
        """Check if current time is within quiet hours."""
        if (
            preferences.quiet_hours_start is None
            or preferences.quiet_hours_end is None
        ):
            return False

        # Get current hour in user's timezone
        # NOTE: For simplicity, using UTC. In production, use user's timezone
        current_hour = datetime.utcnow().hour

        start = preferences.quiet_hours_start
        end = preferences.quiet_hours_end

        # Handle overnight quiet hours (e.g., 22:00 - 06:00)
        if start > end:
            return current_hour >= start or current_hour < end
        else:
            return start <= current_hour < end

    async def get_enabled_channels(self, preferences: UserPreferences) -> list[str]:
        """
        Get list of enabled channels for user.

        Args:
            preferences: User preferences

        Returns:
            List of enabled channel names
        """
        return preferences.enabled_channels

    async def update_preferences(
        self,
        user_id: UUID,
        enabled_channels: list[str] | None = None,
        notification_types: dict[str, bool] | None = None,
        quiet_hours_start: int | None = None,
        quiet_hours_end: int | None = None,
        digest_enabled: bool | None = None,
        digest_frequency: str | None = None,
    ) -> UserPreferences:
        """
        Update user preferences.

        Args:
            user_id: UUID of user
            enabled_channels: Channels to enable
            notification_types: Notification type preferences
            quiet_hours_start: Quiet hours start hour
            quiet_hours_end: Quiet hours end hour
            digest_enabled: Enable digest emails
            digest_frequency: Digest frequency

        Returns:
            Updated UserPreferences
        """
        # Load existing or create new
        result = await self.db.execute(
            select(NotificationPreferenceRecord).where(
                NotificationPreferenceRecord.user_id == user_id
            )
        )
        record = result.scalar_one_or_none()

        if record:
            # Update existing
            if enabled_channels is not None:
                record.enabled_channels = ",".join(enabled_channels)
            if notification_types is not None:
                record.notification_types = notification_types
            if quiet_hours_start is not None:
                record.quiet_hours_start = quiet_hours_start
            if quiet_hours_end is not None:
                record.quiet_hours_end = quiet_hours_end
            if digest_enabled is not None:
                setattr(record, "digest_enabled", digest_enabled)
            if digest_frequency is not None:
                setattr(record, "digest_frequency", digest_frequency)

            record.updated_at = datetime.utcnow()
        else:
            # Create new
            record = NotificationPreferenceRecord(
                user_id=user_id,
                enabled_channels=",".join(enabled_channels or ["in_app", "email"]),
                notification_types=notification_types or {},
                quiet_hours_start=quiet_hours_start,
                quiet_hours_end=quiet_hours_end,
            )
            # Set digest fields if they exist on model
            if hasattr(record, "digest_enabled"):
                record.digest_enabled = digest_enabled or False
            if hasattr(record, "digest_frequency"):
                record.digest_frequency = digest_frequency or "daily"

            self.db.add(record)

        await self.db.commit()
        await self.db.refresh(record)

        # Update cache
        preferences = UserPreferences(
            user_id=user_id,
            enabled_channels=record.get_enabled_channels(),
            notification_types=record.notification_types or {},
            quiet_hours_start=record.quiet_hours_start,
            quiet_hours_end=record.quiet_hours_end,
            timezone=getattr(record, "timezone", "UTC"),
            digest_enabled=getattr(record, "digest_enabled", False),
            digest_frequency=getattr(record, "digest_frequency", "daily"),
        )

        self._cache[user_id] = preferences

        logger.info("Updated preferences for user %s", user_id)
        return preferences

    def clear_cache(self, user_id: UUID | None = None) -> None:
        """
        Clear preference cache.

        Args:
            user_id: Specific user to clear, or None for all
        """
        if user_id:
            if user_id in self._cache:
                del self._cache[user_id]
        else:
            self._cache.clear()

    async def get_statistics(self) -> dict[str, Any]:
        """
        Get preference statistics.

        Returns:
            Dictionary of statistics
        """
        # Count users by channel preferences
        result = await self.db.execute(select(NotificationPreferenceRecord))
        records = result.scalars().all()

        channel_stats = {"in_app": 0, "email": 0, "sms": 0, "webhook": 0}
        quiet_hours_enabled = 0
        digest_enabled_count = 0

        for record in records:
            channels = record.get_enabled_channels()
            for channel in channels:
                if channel in channel_stats:
                    channel_stats[channel] += 1

            if record.quiet_hours_start is not None:
                quiet_hours_enabled += 1

            if getattr(record, "digest_enabled", False):
                digest_enabled_count += 1

        return {
            "total_users": len(records),
            "cached_preferences": len(self._cache),
            "channel_enablement": channel_stats,
            "quiet_hours_enabled": quiet_hours_enabled,
            "digest_enabled": digest_enabled_count,
        }
