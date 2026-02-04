"""Swap lock window checks based on schedule lock date."""

from dataclasses import dataclass
from datetime import date

from sqlalchemy.orm import Session

from app.services.lock_window_service import LockWindowService


@dataclass(frozen=True)
class SwapLockWindowStatus:
    """Represents whether a swap touches the lock window."""

    enabled: bool
    lock_date: date | None
    within_lock_window: bool
    message: str | None


def check_swap_lock_window(
    db: Session,
    source_week: date,
    target_week: date | None,
) -> SwapLockWindowStatus:
    """Check whether a swap touches the lock window.

    A swap is within the lock window if any affected week begins on or
    before the configured schedule_lock_date. If lock date is NULL,
    no lock window is enforced.
    """
    lock_service = LockWindowService(db)
    lock_date = lock_service.get_lock_date()
    if lock_date is None:
        return SwapLockWindowStatus(
            enabled=False,
            lock_date=None,
            within_lock_window=False,
            message=None,
        )

    within_lock_window = source_week <= lock_date or (
        target_week is not None and target_week <= lock_date
    )
    message = None
    if within_lock_window:
        message = f"Swap touches locked window (lock_date={lock_date.isoformat()})"

    return SwapLockWindowStatus(
        enabled=True,
        lock_date=lock_date,
        within_lock_window=within_lock_window,
        message=message,
    )
