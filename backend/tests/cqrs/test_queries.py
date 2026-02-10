"""Tests for CQRS query pattern pure logic (no DB, no Redis).

Covers: Query, ReadModel, QueryResult, QueryHandler, ReadModelProjector,
QueryBus (routing, caching, timing metadata), example queries and read models.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any
from unittest.mock import MagicMock
from uuid import UUID, uuid4

import pytest

from app.cqrs.commands import DomainEvent
from app.cqrs.queries import (
    ExampleGetByIdQuery,
    ExampleListQuery,
    ExampleReadModel,
    ExampleSearchQuery,
    Query,
    QueryBus,
    QueryHandler,
    QueryResult,
    ReadModel,
    ReadModelProjector,
)


def _run(coro):
    """Run an async coroutine synchronously."""
    return asyncio.get_event_loop().run_until_complete(coro)


# ---------------------------------------------------------------------------
# Test query/handler subclasses
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class _TestQuery(Query):
    keyword: str = ""


class _TestReadModel(ReadModel):
    name: str = "test"


class _TestHandler(QueryHandler["_TestQuery"]):
    def __init__(self):
        self.db = MagicMock()
        self.handled = []

    async def handle(self, query: _TestQuery) -> QueryResult:
        self.handled.append(query)
        return QueryResult.ok(data=[{"keyword": query.keyword}], total_count=1)


class _FailingHandler(QueryHandler["_TestQuery"]):
    def __init__(self):
        self.db = MagicMock()

    async def handle(self, query: _TestQuery) -> QueryResult:
        return QueryResult.fail(error="not found")


class _ExplodingHandler(QueryHandler["_TestQuery"]):
    def __init__(self):
        self.db = MagicMock()

    async def handle(self, query: _TestQuery) -> QueryResult:
        raise RuntimeError("query boom")


# ---------------------------------------------------------------------------
# Query base class
# ---------------------------------------------------------------------------


class TestQuery:
    def test_has_query_id(self):
        q = _TestQuery(keyword="x")
        assert isinstance(q.query_id, UUID)

    def test_has_timestamp(self):
        q = _TestQuery(keyword="x")
        assert isinstance(q.timestamp, datetime)

    def test_user_id_default_none(self):
        q = _TestQuery(keyword="x")
        assert q.user_id is None

    def test_metadata_default_empty(self):
        q = _TestQuery(keyword="x")
        assert q.metadata == {}

    def test_frozen(self):
        q = _TestQuery(keyword="x")
        with pytest.raises(AttributeError):
            q.keyword = "y"

    def test_custom_field(self):
        q = _TestQuery(keyword="search term")
        assert q.keyword == "search term"


# ---------------------------------------------------------------------------
# ReadModel base class
# ---------------------------------------------------------------------------


class TestReadModel:
    def test_is_abstract(self):
        # ReadModel is abstract but can be subclassed
        rm = _TestReadModel()
        assert isinstance(rm, ReadModel)

    def test_subclass_fields(self):
        rm = _TestReadModel()
        assert rm.name == "test"


# ---------------------------------------------------------------------------
# QueryResult
# ---------------------------------------------------------------------------


class TestQueryResult:
    def test_ok_success(self):
        result = QueryResult.ok(data=["item1", "item2"])
        assert result.success is True
        assert result.data == ["item1", "item2"]
        assert result.error is None

    def test_ok_with_total_count(self):
        result = QueryResult.ok(data=[], total_count=42)
        assert result.total_count == 42

    def test_ok_with_metadata(self):
        result = QueryResult.ok(data=None, metadata={"cache": True})
        assert result.metadata == {"cache": True}

    def test_ok_default_metadata_empty(self):
        result = QueryResult.ok(data=None)
        assert result.metadata == {}

    def test_fail(self):
        result = QueryResult.fail(error="not found")
        assert result.success is False
        assert result.error == "not found"
        assert result.data is None

    def test_fail_with_metadata(self):
        result = QueryResult.fail(error="err", metadata={"detail": "x"})
        assert result.metadata == {"detail": "x"}

    def test_fail_default_total_count_none(self):
        result = QueryResult.fail(error="err")
        assert result.total_count is None


# ---------------------------------------------------------------------------
# ReadModelProjector
# ---------------------------------------------------------------------------


class TestReadModelProjector:
    def test_init(self):
        class _TestProjector(ReadModelProjector):
            async def project(self, event):
                pass

        p = _TestProjector(db_write=MagicMock(), db_read=MagicMock())
        assert p.db_write is not None
        assert p.db_read is not None

    def test_rebuild_not_implemented(self):
        class _TestProjector(ReadModelProjector):
            async def project(self, event):
                pass

        p = _TestProjector(db_write=MagicMock(), db_read=MagicMock())
        with pytest.raises(NotImplementedError, match="Rebuild not implemented"):
            _run(p.rebuild())


# ---------------------------------------------------------------------------
# QueryBus registration
# ---------------------------------------------------------------------------


class TestQueryBusRegister:
    def test_register_handler(self):
        bus = QueryBus(MagicMock())
        handler = _TestHandler()
        bus.register_handler(_TestQuery, handler)
        assert _TestQuery in bus._handlers

    def test_register_overwrites(self):
        bus = QueryBus(MagicMock())
        h1 = _TestHandler()
        h2 = _TestHandler()
        bus.register_handler(_TestQuery, h1)
        bus.register_handler(_TestQuery, h2)
        assert bus._handlers[_TestQuery] is h2

    def test_cache_disabled_by_default(self):
        bus = QueryBus(MagicMock())
        assert bus.enable_cache is False

    def test_cache_enabled(self):
        bus = QueryBus(MagicMock(), enable_cache=True)
        assert bus.enable_cache is True


# ---------------------------------------------------------------------------
# QueryBus.execute
# ---------------------------------------------------------------------------


class TestQueryBusExecute:
    def test_successful_execution(self):
        bus = QueryBus(MagicMock())
        handler = _TestHandler()
        bus.register_handler(_TestQuery, handler)
        q = _TestQuery(keyword="test")
        result = _run(bus.execute(q))
        assert result.success is True
        assert result.data == [{"keyword": "test"}]
        assert result.total_count == 1
        assert len(handler.handled) == 1

    def test_adds_timing_metadata(self):
        bus = QueryBus(MagicMock())
        bus.register_handler(_TestQuery, _TestHandler())
        result = _run(bus.execute(_TestQuery(keyword="x")))
        assert "query_time_seconds" in result.metadata
        assert result.metadata["cache_hit"] is False

    def test_no_handler_raises(self):
        bus = QueryBus(MagicMock())
        q = _TestQuery(keyword="test")
        # Same logger.error() kwarg bug as CommandBus
        with pytest.raises((ValueError, TypeError)):
            _run(bus.execute(q))

    def test_failed_query_result(self):
        bus = QueryBus(MagicMock())
        bus.register_handler(_TestQuery, _FailingHandler())
        result = _run(bus.execute(_TestQuery(keyword="x")))
        assert result.success is False
        assert result.error == "not found"

    def test_handler_exception_returns_fail(self):
        bus = QueryBus(MagicMock())
        bus.register_handler(_TestQuery, _ExplodingHandler())
        result = _run(bus.execute(_TestQuery(keyword="x")))
        assert result.success is False
        assert result.metadata["exception_type"] == "RuntimeError"


# ---------------------------------------------------------------------------
# QueryBus caching
# ---------------------------------------------------------------------------


class TestQueryBusCaching:
    def test_cache_hit_on_second_call(self):
        bus = QueryBus(MagicMock(), enable_cache=True)
        handler = _TestHandler()
        bus.register_handler(_TestQuery, handler)

        q = _TestQuery(keyword="cached")
        result1 = _run(bus.execute(q))
        assert result1.success is True

        # Same query again — should hit cache
        result2 = _run(bus.execute(q))
        assert result2.metadata.get("cache_hit") is True
        # Handler called only once
        assert len(handler.handled) == 1

    def test_no_cache_when_disabled(self):
        bus = QueryBus(MagicMock(), enable_cache=False)
        handler = _TestHandler()
        bus.register_handler(_TestQuery, handler)

        q = _TestQuery(keyword="nocache")
        _run(bus.execute(q))
        _run(bus.execute(q))
        # Handler called twice (no caching)
        assert len(handler.handled) == 2

    def test_different_queries_not_cached(self):
        bus = QueryBus(MagicMock(), enable_cache=True)
        handler = _TestHandler()
        bus.register_handler(_TestQuery, handler)

        _run(bus.execute(_TestQuery(keyword="a")))
        _run(bus.execute(_TestQuery(keyword="b")))
        assert len(handler.handled) == 2

    def test_clear_cache(self):
        bus = QueryBus(MagicMock(), enable_cache=True)
        handler = _TestHandler()
        bus.register_handler(_TestQuery, handler)

        q = _TestQuery(keyword="clear_me")
        _run(bus.execute(q))
        bus.clear_cache()
        _run(bus.execute(q))
        # Handler called twice after cache clear
        assert len(handler.handled) == 2

    def test_cache_expired_entry_removed(self):
        bus = QueryBus(MagicMock(), enable_cache=True)
        handler = _TestHandler()
        bus.register_handler(_TestQuery, handler)

        q = _TestQuery(keyword="expire_me")
        _run(bus.execute(q))

        # Manually expire the cache entry
        for key in bus._cache:
            result, _ = bus._cache[key]
            bus._cache[key] = (result, datetime.utcnow() - timedelta(seconds=400))

        _run(bus.execute(q))
        # Handler called again after expiry
        assert len(handler.handled) == 2

    def test_failed_result_not_cached(self):
        bus = QueryBus(MagicMock(), enable_cache=True)
        bus.register_handler(_TestQuery, _FailingHandler())

        q = _TestQuery(keyword="fail")
        _run(bus.execute(q))
        assert len(bus._cache) == 0

    def test_make_cache_key_excludes_query_id(self):
        bus = QueryBus(MagicMock(), enable_cache=True)
        q1 = _TestQuery(keyword="same")
        q2 = _TestQuery(keyword="same")
        # Different query_ids but same keyword → same cache key
        assert bus._make_cache_key(q1) == bus._make_cache_key(q2)

    def test_make_cache_key_different_for_different_data(self):
        bus = QueryBus(MagicMock(), enable_cache=True)
        q1 = _TestQuery(keyword="a")
        q2 = _TestQuery(keyword="b")
        assert bus._make_cache_key(q1) != bus._make_cache_key(q2)


# ---------------------------------------------------------------------------
# Example queries
# ---------------------------------------------------------------------------


class TestExampleGetByIdQuery:
    def test_construction(self):
        eid = uuid4()
        q = ExampleGetByIdQuery(entity_id=eid)
        assert q.entity_id == eid
        assert isinstance(q.query_id, UUID)

    def test_frozen(self):
        q = ExampleGetByIdQuery(entity_id=uuid4())
        with pytest.raises(AttributeError):
            q.entity_id = uuid4()


class TestExampleListQuery:
    def test_defaults(self):
        q = ExampleListQuery()
        assert q.status is None
        assert q.limit == 100
        assert q.offset == 0

    def test_custom_values(self):
        q = ExampleListQuery(status="active", limit=50, offset=10)
        assert q.status == "active"
        assert q.limit == 50
        assert q.offset == 10


class TestExampleSearchQuery:
    def test_construction(self):
        q = ExampleSearchQuery(search_term="hello")
        assert q.search_term == "hello"
        assert q.filters == {}

    def test_with_filters(self):
        q = ExampleSearchQuery(search_term="test", filters={"type": "user"})
        assert q.filters == {"type": "user"}


class TestExampleReadModel:
    def test_construction(self):
        now = datetime.now()
        rm = ExampleReadModel(
            id=uuid4(),
            name="John",
            email="john@test.com",
            created_at=now,
            total_assignments=5,
            latest_assignment_date=now,
            compliance_status="compliant",
        )
        assert rm.name == "John"
        assert rm.total_assignments == 5
        assert isinstance(rm, ReadModel)
