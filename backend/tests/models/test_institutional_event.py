"""Tests for InstitutionalEvent model enum handling.

Verifies that SAEnum with native_enum=False correctly round-trips
lowercase PostgreSQL enum values through SQLAlchemy.
"""

import uuid
from datetime import date, datetime

import pytest

from app.models.institutional_event import (
    InstitutionalEvent,
    InstitutionalEventScope,
    InstitutionalEventType,
)


class TestInstitutionalEventEnums:
    """Verify enum deserialization works for all event types."""

    def test_all_event_types_are_valid_python_enums(self):
        """Enum members match lowercase DB values."""
        expected = {"holiday", "conference", "retreat", "training", "closure", "other"}
        actual = {e.value for e in InstitutionalEventType}
        assert actual == expected

    def test_all_scope_types_are_valid_python_enums(self):
        expected = {"all", "faculty", "resident"}
        actual = {e.value for e in InstitutionalEventScope}
        assert actual == expected

    @pytest.mark.parametrize(
        "event_type",
        list(InstitutionalEventType),
        ids=[e.name for e in InstitutionalEventType],
    )
    def test_create_event_with_each_type(self, event_type):
        """Model accepts all enum values without error."""
        event = InstitutionalEvent(
            id=uuid.uuid4(),
            name=f"Test {event_type.value}",
            event_type=event_type,
            applies_to=InstitutionalEventScope.ALL,
            start_date=date(2026, 4, 10),
            end_date=date(2026, 4, 12),
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        assert event.event_type == event_type
        assert event.event_type.value == event_type.value

    @pytest.mark.parametrize(
        "scope",
        list(InstitutionalEventScope),
        ids=[s.name for s in InstitutionalEventScope],
    )
    def test_create_event_with_each_scope(self, scope):
        """Model accepts all scope values without error."""
        event = InstitutionalEvent(
            id=uuid.uuid4(),
            name=f"Test scope {scope.value}",
            event_type=InstitutionalEventType.OTHER,
            applies_to=scope,
            start_date=date(2026, 4, 10),
            end_date=date(2026, 4, 12),
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        assert event.applies_to == scope

    def test_retreat_event_type_matches_db_value(self):
        """Specifically test 'retreat' — the value that triggered the original bug."""
        assert InstitutionalEventType.RETREAT.value == "retreat"
        event = InstitutionalEvent(
            id=uuid.uuid4(),
            name="Block 11 Retreat",
            event_type=InstitutionalEventType.RETREAT,
            applies_to=InstitutionalEventScope.ALL,
            start_date=date(2026, 4, 10),
            end_date=date(2026, 4, 12),
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        assert event.event_type == InstitutionalEventType.RETREAT
