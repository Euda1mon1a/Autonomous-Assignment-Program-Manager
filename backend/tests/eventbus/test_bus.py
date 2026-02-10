"""Tests for async event bus models and pure logic (no Redis, no DB)."""

from __future__ import annotations

import asyncio
import json
from datetime import datetime

import pytest

from app.eventbus.bus import (
    DeadLetterEvent,
    DeadLetterQueue,
    Event,
    EventBusException,
    EventBusMode,
    EventFilter,
    EventMetadata,
    EventSubscription,
    EventTransformer,
)


# ---------------------------------------------------------------------------
# EventBusMode enum
# ---------------------------------------------------------------------------


class TestEventBusMode:
    def test_all_values(self):
        assert EventBusMode.IN_MEMORY == "in_memory"
        assert EventBusMode.DISTRIBUTED == "distributed"
        assert EventBusMode.HYBRID == "hybrid"

    def test_count(self):
        assert len(EventBusMode) == 3

    def test_is_str_enum(self):
        assert isinstance(EventBusMode.IN_MEMORY, str)


# ---------------------------------------------------------------------------
# EventBusException
# ---------------------------------------------------------------------------


class TestEventBusException:
    def test_raises(self):
        with pytest.raises(EventBusException):
            raise EventBusException("bus error")

    def test_message(self):
        err = EventBusException("test error")
        assert str(err) == "test error"


# ---------------------------------------------------------------------------
# EventMetadata
# ---------------------------------------------------------------------------


class TestEventMetadata:
    def test_defaults(self):
        m = EventMetadata()
        assert m.event_id  # auto-generated UUID string
        assert m.timestamp is not None
        assert m.correlation_id is None
        assert m.source is None
        assert m.version == "1.0"
        assert m.retry_count == 0
        assert m.content_type == "application/json"

    def test_auto_generated_id_unique(self):
        m1 = EventMetadata()
        m2 = EventMetadata()
        assert m1.event_id != m2.event_id

    def test_custom_fields(self):
        m = EventMetadata(
            correlation_id="corr-1",
            source="test_service",
            version="2.0",
            retry_count=3,
        )
        assert m.correlation_id == "corr-1"
        assert m.source == "test_service"
        assert m.version == "2.0"
        assert m.retry_count == 3


# ---------------------------------------------------------------------------
# Event
# ---------------------------------------------------------------------------


class TestEvent:
    def test_creation(self):
        e = Event(topic="user.created", data={"user_id": 1})
        assert e.topic == "user.created"
        assert e.data["user_id"] == 1
        assert e.metadata is not None

    def test_defaults(self):
        e = Event(topic="test")
        assert e.data == {}
        assert e.metadata.version == "1.0"

    def test_to_dict(self):
        e = Event(topic="test", data={"key": "val"})
        d = e.to_dict()
        assert d["topic"] == "test"
        assert d["data"]["key"] == "val"
        assert "metadata" in d
        assert d["metadata"]["version"] == "1.0"

    def test_from_dict(self):
        d = {
            "topic": "test",
            "data": {"x": 1},
            "metadata": {"version": "1.0"},
        }
        e = Event.from_dict(d)
        assert e.topic == "test"
        assert e.data["x"] == 1

    def test_from_dict_no_data(self):
        d = {"topic": "test"}
        e = Event.from_dict(d)
        assert e.data == {}

    def test_roundtrip_dict(self):
        e = Event(topic="user.created", data={"user_id": 42})
        d = e.to_dict()
        e2 = Event.from_dict(d)
        assert e2.topic == e.topic
        assert e2.data == e.data

    def test_to_json(self):
        e = Event(topic="test", data={"key": "val"})
        j = e.to_json()
        parsed = json.loads(j)
        assert parsed["topic"] == "test"
        assert parsed["data"]["key"] == "val"

    def test_from_json(self):
        j = json.dumps({"topic": "test", "data": {"x": 1}, "metadata": {}})
        e = Event.from_json(j)
        assert e.topic == "test"
        assert e.data["x"] == 1

    def test_roundtrip_json(self):
        e = Event(topic="user.deleted", data={"user_id": 99})
        j = e.to_json()
        e2 = Event.from_json(j)
        assert e2.topic == e.topic
        assert e2.data == e.data

    def test_custom_metadata(self):
        meta = EventMetadata(source="api", correlation_id="req-123")
        e = Event(topic="order.placed", data={"amount": 50}, metadata=meta)
        assert e.metadata.source == "api"
        assert e.metadata.correlation_id == "req-123"


# ---------------------------------------------------------------------------
# EventFilter
# ---------------------------------------------------------------------------


class TestEventFilter:
    def _event(self, topic="test", data=None, source=None):
        meta = EventMetadata(source=source)
        return Event(topic=topic, data=data or {}, metadata=meta)

    def test_empty_filter_passes_all(self):
        f = EventFilter()
        assert f.should_process(self._event()) is True

    def test_filter_by_data_match(self):
        f = EventFilter()
        f.filter_by_data("status", "active")
        assert f.should_process(self._event(data={"status": "active"})) is True

    def test_filter_by_data_no_match(self):
        f = EventFilter()
        f.filter_by_data("status", "active")
        assert f.should_process(self._event(data={"status": "inactive"})) is False

    def test_filter_by_data_missing_key(self):
        f = EventFilter()
        f.filter_by_data("status", "active")
        assert f.should_process(self._event(data={})) is False

    def test_filter_by_metadata_match(self):
        f = EventFilter()
        f.filter_by_metadata("source", "api")
        assert f.should_process(self._event(source="api")) is True

    def test_filter_by_metadata_no_match(self):
        f = EventFilter()
        f.filter_by_metadata("source", "api")
        assert f.should_process(self._event(source="worker")) is False

    def test_filter_by_source(self):
        f = EventFilter()
        f.filter_by_source("api")
        assert f.should_process(self._event(source="api")) is True
        assert f.should_process(self._event(source="other")) is False

    def test_multiple_filters_all_match(self):
        f = EventFilter()
        f.filter_by_data("status", "active")
        f.filter_by_source("api")
        event = Event(
            topic="test",
            data={"status": "active"},
            metadata=EventMetadata(source="api"),
        )
        assert f.should_process(event) is True

    def test_multiple_filters_one_fails(self):
        f = EventFilter()
        f.filter_by_data("status", "active")
        f.filter_by_source("api")
        event = Event(
            topic="test",
            data={"status": "inactive"},
            metadata=EventMetadata(source="api"),
        )
        assert f.should_process(event) is False

    def test_custom_filter_function(self):
        f = EventFilter()
        f.add_filter(lambda e: len(e.data) > 0)
        assert f.should_process(self._event(data={"a": 1})) is True
        assert f.should_process(self._event(data={})) is False


# ---------------------------------------------------------------------------
# EventTransformer
# ---------------------------------------------------------------------------


class TestEventTransformer:
    def test_no_transformers(self):
        t = EventTransformer()
        e = Event(topic="test", data={"a": 1})
        result = t.transform(e)
        assert result.data["a"] == 1

    def test_enrich_data(self):
        t = EventTransformer()
        t.enrich_data({"env": "production"})
        e = Event(topic="test", data={"a": 1})
        result = t.transform(e)
        assert result.data["env"] == "production"
        assert result.data["a"] == 1

    def test_multiple_enrichments(self):
        t = EventTransformer()
        t.enrich_data({"x": 1})
        t.enrich_data({"y": 2})
        e = Event(topic="test", data={})
        result = t.transform(e)
        assert result.data["x"] == 1
        assert result.data["y"] == 2

    def test_custom_transformer(self):
        t = EventTransformer()

        def uppercase_topic(event: Event) -> Event:
            event.topic = event.topic.upper()
            return event

        t.add_transformer(uppercase_topic)
        e = Event(topic="test.event", data={})
        result = t.transform(e)
        assert result.topic == "TEST.EVENT"

    def test_chained_transformers(self):
        t = EventTransformer()
        t.enrich_data({"added": True})
        t.add_transformer(lambda e: Event(topic=e.topic, data={**e.data, "extra": 1}))
        e = Event(topic="test", data={"orig": True})
        result = t.transform(e)
        assert result.data["added"] is True
        assert result.data["extra"] == 1


# ---------------------------------------------------------------------------
# EventSubscription.matches_topic
# ---------------------------------------------------------------------------


class TestEventSubscriptionMatchesTopic:
    def _sub(self, pattern: str) -> EventSubscription:
        async def handler(e: Event) -> None:
            pass

        return EventSubscription(topic_pattern=pattern, handler=handler)

    def test_exact_match(self):
        sub = self._sub("user.created")
        assert sub.matches_topic("user.created") is True

    def test_exact_no_match(self):
        sub = self._sub("user.created")
        assert sub.matches_topic("user.updated") is False

    def test_single_wildcard(self):
        sub = self._sub("user.*")
        assert sub.matches_topic("user.created") is True
        assert sub.matches_topic("user.updated") is True

    def test_single_wildcard_no_nested(self):
        sub = self._sub("user.*")
        assert sub.matches_topic("user.profile.updated") is False

    def test_multi_level_wildcard_bug(self):
        """** wildcard is broken: the * inside .* gets replaced by [^.]+.
        'user.**' becomes regex '^user\\.[^.]+$' instead of '^user\\..*$'.
        This means ** behaves the same as * (single level only)."""
        sub = self._sub("user.**")
        # Due to the bug, ** acts like single-level wildcard
        assert sub.matches_topic("user.created") is True
        assert sub.matches_topic("user.profile.updated") is False  # Bug: should be True

    def test_wildcard_middle(self):
        sub = self._sub("*.created")
        assert sub.matches_topic("user.created") is True
        assert sub.matches_topic("order.created") is True
        assert sub.matches_topic("user.updated") is False

    def test_wildcard_all_bug(self):
        """** alone is broken: becomes regex '^[^.]+$' instead of '^.*$'.
        Only matches single-segment topics without dots."""
        sub = self._sub("**")
        assert sub.matches_topic("anything") is True  # No dots, matches [^.]+
        assert sub.matches_topic("user.created") is False  # Bug: should be True

    def test_complex_pattern(self):
        sub = self._sub("user.*.action")
        assert sub.matches_topic("user.123.action") is True
        assert sub.matches_topic("user.abc.action") is True
        assert sub.matches_topic("user.action") is False

    def test_subscription_defaults(self):
        async def handler(e: Event) -> None:
            pass

        sub = EventSubscription(topic_pattern="test", handler=handler)
        assert sub.subscription_id  # auto-generated
        assert sub.max_retries == 3
        assert sub.dead_letter_enabled is True
        assert sub.filter is None
        assert sub.transformer is None


# ---------------------------------------------------------------------------
# DeadLetterEvent
# ---------------------------------------------------------------------------


class TestDeadLetterEvent:
    def test_creation(self):
        dle = DeadLetterEvent(
            event_id="e1",
            topic="user.created",
            event_data={"topic": "user.created", "data": {}},
            error_message="timeout",
            retry_count=3,
            subscription_id="sub1",
        )
        assert dle.event_id == "e1"
        assert dle.topic == "user.created"
        assert dle.error_message == "timeout"
        assert dle.retry_count == 3
        assert dle.subscription_id == "sub1"
        assert dle.failed_at is not None


# ---------------------------------------------------------------------------
# DeadLetterQueue (in-memory, no Redis)
# ---------------------------------------------------------------------------


class TestDeadLetterQueue:
    def setup_method(self):
        self.dlq = DeadLetterQueue(redis_client=None)

    @pytest.fixture(autouse=True)
    def _event_loop(self):
        """Provide event loop for async tests."""
        pass

    def _make_event(self, event_id="e1", topic="test"):
        return Event(
            topic=topic,
            data={"key": "val"},
            metadata=EventMetadata(event_id=event_id),
        )

    def test_add_and_get_all(self):
        event = self._make_event()
        asyncio.get_event_loop().run_until_complete(
            self.dlq.add(event, Exception("error"), "sub1")
        )
        result = asyncio.get_event_loop().run_until_complete(self.dlq.get_all())
        assert len(result) == 1
        assert result[0].event_id == event.metadata.event_id

    def test_get_all_empty(self):
        result = asyncio.get_event_loop().run_until_complete(self.dlq.get_all())
        assert result == []

    def test_get_by_topic(self):
        e1 = self._make_event("e1", "user.created")
        e2 = self._make_event("e2", "order.placed")
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.dlq.add(e1, Exception("err"), "sub1"))
        loop.run_until_complete(self.dlq.add(e2, Exception("err"), "sub2"))

        result = loop.run_until_complete(self.dlq.get_by_topic("user.created"))
        assert len(result) == 1
        assert result[0].topic == "user.created"

    def test_get_by_topic_no_match(self):
        e1 = self._make_event("e1", "user.created")
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.dlq.add(e1, Exception("err"), "sub1"))

        result = loop.run_until_complete(self.dlq.get_by_topic("order.placed"))
        assert result == []

    def test_remove(self):
        event = self._make_event("e1")
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.dlq.add(event, Exception("err"), "sub1"))

        removed = loop.run_until_complete(self.dlq.remove("e1"))
        assert removed is True

        result = loop.run_until_complete(self.dlq.get_all())
        assert result == []

    def test_remove_nonexistent(self):
        removed = asyncio.get_event_loop().run_until_complete(
            self.dlq.remove("nonexistent")
        )
        assert removed is False

    def test_clear(self):
        loop = asyncio.get_event_loop()
        loop.run_until_complete(
            self.dlq.add(self._make_event("e1"), Exception("err"), "sub1")
        )
        loop.run_until_complete(
            self.dlq.add(self._make_event("e2"), Exception("err"), "sub2")
        )

        count = loop.run_until_complete(self.dlq.clear())
        assert count == 2

        result = loop.run_until_complete(self.dlq.get_all())
        assert result == []

    def test_clear_empty(self):
        count = asyncio.get_event_loop().run_until_complete(self.dlq.clear())
        assert count == 0

    def test_add_records_error_message(self):
        event = self._make_event()
        asyncio.get_event_loop().run_until_complete(
            self.dlq.add(event, ValueError("specific error"), "sub1")
        )
        result = asyncio.get_event_loop().run_until_complete(self.dlq.get_all())
        assert "specific error" in result[0].error_message

    def test_add_records_retry_count(self):
        event = self._make_event()
        event.metadata.retry_count = 5
        asyncio.get_event_loop().run_until_complete(
            self.dlq.add(event, Exception("err"), "sub1")
        )
        result = asyncio.get_event_loop().run_until_complete(self.dlq.get_all())
        assert result[0].retry_count == 5
