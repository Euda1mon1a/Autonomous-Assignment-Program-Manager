"""Tests for calendar export schemas (field_validator, Field bounds, defaults)."""

from datetime import date, datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas.calendar import (
    CalendarExportRequest,
    CalendarSubscriptionToken,
    CalendarSubscriptionCreate,
    CalendarSubscriptionResponse,
    CalendarSubscriptionListResponse,
    CalendarSubscriptionRevokeResponse,
)


class TestCalendarExportRequest:
    def test_valid(self):
        r = CalendarExportRequest(
            person_id=uuid4(),
            start_date=date(2026, 1, 1),
            end_date=date(2026, 3, 31),
        )
        assert r.include_types is None

    def test_with_include_types(self):
        r = CalendarExportRequest(
            person_id=uuid4(),
            start_date=date(2026, 1, 1),
            end_date=date(2026, 3, 31),
            include_types=["outpatient", "inpatient"],
        )
        assert len(r.include_types) == 2

    # --- field_validator: end_date >= start_date ---

    def test_end_before_start(self):
        with pytest.raises(ValidationError, match="end_date must be after start_date"):
            CalendarExportRequest(
                person_id=uuid4(),
                start_date=date(2026, 3, 31),
                end_date=date(2026, 1, 1),
            )

    def test_same_start_end(self):
        # Same date should not raise (not strictly "before")
        r = CalendarExportRequest(
            person_id=uuid4(),
            start_date=date(2026, 1, 1),
            end_date=date(2026, 1, 1),
        )
        assert r.start_date == r.end_date


class TestCalendarSubscriptionToken:
    def test_valid(self):
        r = CalendarSubscriptionToken(
            token="abc123",
            person_id=uuid4(),
            created_at=datetime(2026, 1, 1),
        )
        assert r.expires_at is None

    def test_with_expiry(self):
        r = CalendarSubscriptionToken(
            token="abc123",
            person_id=uuid4(),
            created_at=datetime(2026, 1, 1),
            expires_at=datetime(2026, 4, 1),
        )
        assert r.expires_at is not None


class TestCalendarSubscriptionCreate:
    def test_valid_minimal(self):
        r = CalendarSubscriptionCreate(person_id=uuid4())
        assert r.label is None
        assert r.expires_days is None

    # --- label max_length=255 ---

    def test_label_too_long(self):
        with pytest.raises(ValidationError):
            CalendarSubscriptionCreate(person_id=uuid4(), label="x" * 256)

    def test_label_max_length(self):
        r = CalendarSubscriptionCreate(person_id=uuid4(), label="x" * 255)
        assert len(r.label) == 255

    # --- expires_days ge=1, le=365 ---

    def test_expires_days_boundaries(self):
        r = CalendarSubscriptionCreate(person_id=uuid4(), expires_days=1)
        assert r.expires_days == 1
        r = CalendarSubscriptionCreate(person_id=uuid4(), expires_days=365)
        assert r.expires_days == 365

    def test_expires_days_below_min(self):
        with pytest.raises(ValidationError):
            CalendarSubscriptionCreate(person_id=uuid4(), expires_days=0)

    def test_expires_days_above_max(self):
        with pytest.raises(ValidationError):
            CalendarSubscriptionCreate(person_id=uuid4(), expires_days=366)


class TestCalendarSubscriptionResponse:
    def test_valid_minimal(self):
        r = CalendarSubscriptionResponse(
            token="abc",
            subscription_url="https://example.com/cal/abc",
            webcal_url="webcal://example.com/cal/abc",
            person_id=uuid4(),
        )
        assert r.label is None
        assert r.created_at is None
        assert r.expires_at is None
        assert r.last_accessed_at is None
        assert r.is_active is True


class TestCalendarSubscriptionListResponse:
    def test_valid(self):
        r = CalendarSubscriptionListResponse(subscriptions=[], total=0)
        assert r.subscriptions == []
        assert r.total == 0


class TestCalendarSubscriptionRevokeResponse:
    def test_valid(self):
        r = CalendarSubscriptionRevokeResponse(success=True, message="Revoked")
        assert r.success is True
        assert r.message == "Revoked"
