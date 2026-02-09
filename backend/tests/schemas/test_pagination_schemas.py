"""Tests for pagination schemas (Field bounds, field_validators, generics)."""

import pytest
from pydantic import ValidationError

from app.schemas.pagination import (
    PaginationParams,
    OffsetPaginationParams,
    CursorPaginationParams,
    PageInfo,
    PaginatedResponse,
    CursorPageInfo,
    CursorPaginatedResponse,
)


class TestPaginationParams:
    def test_defaults(self):
        r = PaginationParams()
        assert r.page == 1
        assert r.page_size == 50

    # --- page ge=1 ---

    def test_page_min(self):
        r = PaginationParams(page=1)
        assert r.page == 1

    def test_page_below_min(self):
        with pytest.raises(ValidationError):
            PaginationParams(page=0)

    # --- page_size ge=1, le=1000 ---

    def test_page_size_boundaries(self):
        r = PaginationParams(page_size=1)
        assert r.page_size == 1
        r = PaginationParams(page_size=1000)
        assert r.page_size == 1000

    def test_page_size_below_min(self):
        with pytest.raises(ValidationError):
            PaginationParams(page_size=0)

    def test_page_size_above_max(self):
        with pytest.raises(ValidationError):
            PaginationParams(page_size=1001)


class TestOffsetPaginationParams:
    def test_defaults(self):
        r = OffsetPaginationParams()
        assert r.offset == 0
        assert r.limit == 50

    # --- offset ge=0 ---

    def test_offset_zero(self):
        r = OffsetPaginationParams(offset=0)
        assert r.offset == 0

    def test_offset_negative(self):
        with pytest.raises(ValidationError):
            OffsetPaginationParams(offset=-1)

    # --- limit ge=1, le=1000 ---

    def test_limit_boundaries(self):
        r = OffsetPaginationParams(limit=1)
        assert r.limit == 1
        r = OffsetPaginationParams(limit=1000)
        assert r.limit == 1000

    def test_limit_below_min(self):
        with pytest.raises(ValidationError):
            OffsetPaginationParams(limit=0)

    def test_limit_above_max(self):
        with pytest.raises(ValidationError):
            OffsetPaginationParams(limit=1001)


class TestCursorPaginationParams:
    def test_defaults(self):
        r = CursorPaginationParams()
        assert r.cursor is None
        assert r.limit == 50

    def test_with_cursor(self):
        r = CursorPaginationParams(cursor="abc123")
        assert r.cursor == "abc123"

    # --- limit ge=1, le=1000 ---

    def test_limit_below_min(self):
        with pytest.raises(ValidationError):
            CursorPaginationParams(limit=0)

    def test_limit_above_max(self):
        with pytest.raises(ValidationError):
            CursorPaginationParams(limit=1001)


class TestPageInfo:
    def test_valid(self):
        r = PageInfo(
            page=1,
            page_size=50,
            total_items=100,
            total_pages=2,
            has_next=True,
            has_previous=False,
        )
        assert r.total_items == 100
        assert r.has_next is True


class TestPaginatedResponse:
    def test_valid(self):
        page_info = PageInfo(
            page=1,
            page_size=10,
            total_items=25,
            total_pages=3,
            has_next=True,
            has_previous=False,
        )
        r = PaginatedResponse(items=["a", "b"], page_info=page_info)
        assert len(r.items) == 2
        assert r.page_info.total_items == 25

    def test_empty(self):
        page_info = PageInfo(
            page=1,
            page_size=10,
            total_items=0,
            total_pages=0,
            has_next=False,
            has_previous=False,
        )
        r = PaginatedResponse(items=[], page_info=page_info)
        assert r.items == []


class TestCursorPageInfo:
    def test_valid(self):
        r = CursorPageInfo(has_next=True, has_previous=False, count=10)
        assert r.next_cursor is None
        assert r.previous_cursor is None

    def test_with_cursors(self):
        r = CursorPageInfo(
            next_cursor="next123",
            previous_cursor="prev456",
            has_next=True,
            has_previous=True,
            count=50,
        )
        assert r.next_cursor == "next123"


class TestCursorPaginatedResponse:
    def test_valid(self):
        cursor_info = CursorPageInfo(has_next=False, has_previous=False, count=0)
        r = CursorPaginatedResponse(items=[], cursor_info=cursor_info)
        assert r.items == []
