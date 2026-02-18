"""Activity lookup with 3-tier fallback and instance-level caching."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import ActivityNotFoundError
from app.core.logging import get_logger
from app.models.activity import Activity

logger = get_logger(__name__)


class ActivityCache:
    """Cached activity-ID lookup with 3-tier fallback.

    Lookup order:
    1. Exact ``code`` match
    2. Case-insensitive ``code`` match
    3. ``display_abbreviation`` match
    """

    def __init__(self, session: Session) -> None:
        self.session = session
        self._cache: dict[str, UUID] = {}

    def get(
        self,
        code: str,
        *,
        required: bool = True,
    ) -> UUID | None:
        """Return activity UUID for *code*, or raise/return None."""
        if code in self._cache:
            return self._cache[code]

        # Tier 1: exact code
        stmt = select(Activity).where(Activity.code == code)
        activity = self.session.execute(stmt).scalars().first()

        if not activity:
            # Tier 2: case-insensitive code
            stmt = select(Activity).where(Activity.code.ilike(code))
            activity = self.session.execute(stmt).scalars().first()

        if not activity:
            # Tier 3: display_abbreviation
            stmt = select(Activity).where(Activity.display_abbreviation == code)
            activity = self.session.execute(stmt).scalars().first()

        if activity:
            self._cache[code] = activity.id
            return activity.id

        if required:
            logger.error(f"Unknown activity code during preload: {code}")
            raise ActivityNotFoundError(code, context="preload/activity_cache")

        logger.warning(f"Optional activity not found during preload: {code}")
        return None
