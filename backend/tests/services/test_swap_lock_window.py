"""Tests for swap lock window checks."""

from datetime import date
from unittest.mock import patch

from sqlalchemy.orm import Session

from app.services.swap.lock_window import check_swap_lock_window


def test_check_swap_lock_window_disabled_when_no_lock_date(db: Session) -> None:
    with patch(
        "app.services.swap.lock_window.LockWindowService.get_lock_date",
        return_value=None,
    ):
        status = check_swap_lock_window(
            db, source_week=date(2025, 2, 3), target_week=None
        )

    assert status.enabled is False
    assert status.lock_date is None
    assert status.within_lock_window is False
    assert status.message is None


def test_check_swap_lock_window_detects_locked_week(db: Session) -> None:
    lock_date = date(2025, 2, 10)
    with patch(
        "app.services.swap.lock_window.LockWindowService.get_lock_date",
        return_value=lock_date,
    ):
        status = check_swap_lock_window(
            db, source_week=date(2025, 2, 3), target_week=date(2025, 3, 3)
        )

    assert status.enabled is True
    assert status.lock_date == lock_date
    assert status.within_lock_window is True
    assert status.message == "Swap touches locked window (lock_date=2025-02-10)"


def test_check_swap_lock_window_allows_after_lock_date(db: Session) -> None:
    lock_date = date(2025, 2, 10)
    with patch(
        "app.services.swap.lock_window.LockWindowService.get_lock_date",
        return_value=lock_date,
    ):
        status = check_swap_lock_window(
            db, source_week=date(2025, 2, 17), target_week=date(2025, 2, 24)
        )

    assert status.enabled is True
    assert status.lock_date == lock_date
    assert status.within_lock_window is False
    assert status.message is None
