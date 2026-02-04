from datetime import date, timedelta

from app.services.lock_window_service import LockWindowService
from app.models.settings import ApplicationSettings


def test_lock_window_null_date(db):
    service = LockWindowService(db)
    assert service.get_lock_date() is None
    assert service.is_locked(date.today()) is False


def test_lock_window_inclusive_bounds(db):
    lock_date = date.today() + timedelta(days=2)
    settings = ApplicationSettings(schedule_lock_date=lock_date)
    db.add(settings)
    db.commit()

    service = LockWindowService(db)
    assert service.is_locked(date.today() - timedelta(days=1)) is True
    assert service.is_locked(date.today()) is True
    assert service.is_locked(lock_date) is True
    assert service.is_locked(lock_date + timedelta(days=1)) is False
