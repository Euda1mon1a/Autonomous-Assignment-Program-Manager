"""Lock window service for schedule drafts and publish gating."""

from datetime import date

from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.models.settings import ApplicationSettings

logger = get_logger(__name__)


class LockWindowService:
    """Service for lock-date enforcement.

    Lock date is stored in ApplicationSettings.schedule_lock_date.
    If schedule_lock_date is NULL, no lock window is enforced.
    """

    def __init__(self, db: Session) -> None:
        self.db = db
        self._settings_cache: ApplicationSettings | None = None

    def get_settings(self) -> ApplicationSettings:
        """Get application settings (cached)."""
        if self._settings_cache is None:
            self._settings_cache = self.db.query(ApplicationSettings).first()
            if self._settings_cache is None:
                self._settings_cache = ApplicationSettings()
                self.db.add(self._settings_cache)
                self.db.commit()
        return self._settings_cache

    def clear_settings_cache(self) -> None:
        """Clear settings cache (call when settings are updated)."""
        self._settings_cache = None

    def get_lock_date(self) -> date | None:
        """Return the current lock date (NULL means no lock window)."""
        return self.get_settings().schedule_lock_date

    def is_locked(self, target_date: date) -> bool:
        """Return True if target_date is on or before the lock date."""
        lock_date = self.get_lock_date()
        if lock_date is None:
            return False
        return target_date <= lock_date
