"""Tests for sorting schemas (enums, defaults, field_validator, min/max_length)."""

import pytest
from pydantic import ValidationError

from app.schemas.sorting import (
    SortOrder,
    SortParams,
    MultiSortParams,
    PersonSortField,
    PersonSort,
    AssignmentSortField,
    AssignmentSort,
    BlockSortField,
    BlockSort,
    SwapSortField,
    SwapSort,
)


class TestSortOrder:
    def test_values(self):
        assert SortOrder.ASC.value == "asc"
        assert SortOrder.DESC.value == "desc"

    def test_count(self):
        assert len(SortOrder) == 2

    def test_is_str(self):
        assert isinstance(SortOrder.ASC, str)


class TestSortParams:
    def test_valid(self):
        r = SortParams(sort_by="name")
        assert r.sort_order == SortOrder.ASC

    def test_desc(self):
        r = SortParams(sort_by="created_at", sort_order=SortOrder.DESC)
        assert r.sort_order == SortOrder.DESC


class TestMultiSortParams:
    def test_valid(self):
        sorts = [SortParams(sort_by="name"), SortParams(sort_by="date")]
        r = MultiSortParams(sorts=sorts)
        assert len(r.sorts) == 2

    # --- sorts min_length=1 ---

    def test_empty_sorts(self):
        with pytest.raises(ValidationError):
            MultiSortParams(sorts=[])

    # --- sorts max_length=5 ---

    def test_max_sorts(self):
        sorts = [SortParams(sort_by=f"field_{i}") for i in range(5)]
        r = MultiSortParams(sorts=sorts)
        assert len(r.sorts) == 5

    def test_too_many_sorts(self):
        sorts = [SortParams(sort_by=f"field_{i}") for i in range(6)]
        with pytest.raises(ValidationError):
            MultiSortParams(sorts=sorts)


class TestPersonSortField:
    def test_values(self):
        assert PersonSortField.NAME.value == "name"
        assert PersonSortField.TYPE.value == "type"
        assert PersonSortField.PGY_LEVEL.value == "pgy_level"
        assert PersonSortField.CREATED_AT.value == "created_at"
        assert PersonSortField.UPDATED_AT.value == "updated_at"

    def test_count(self):
        assert len(PersonSortField) == 5


class TestPersonSort:
    def test_defaults(self):
        r = PersonSort()
        assert r.sort_by == PersonSortField.NAME
        assert r.sort_order == SortOrder.ASC


class TestAssignmentSortField:
    def test_values(self):
        assert AssignmentSortField.DATE.value == "date"
        assert AssignmentSortField.PERSON_NAME.value == "person_name"
        assert AssignmentSortField.CREATED_AT.value == "created_at"
        assert AssignmentSortField.UPDATED_AT.value == "updated_at"

    def test_count(self):
        assert len(AssignmentSortField) == 4


class TestAssignmentSort:
    def test_defaults(self):
        r = AssignmentSort()
        assert r.sort_by == AssignmentSortField.DATE
        assert r.sort_order == SortOrder.ASC


class TestBlockSortField:
    def test_values(self):
        assert BlockSortField.DATE.value == "date"
        assert BlockSortField.SESSION.value == "session"
        assert BlockSortField.CREATED_AT.value == "created_at"

    def test_count(self):
        assert len(BlockSortField) == 3


class TestBlockSort:
    def test_defaults(self):
        r = BlockSort()
        assert r.sort_by == BlockSortField.DATE
        assert r.sort_order == SortOrder.ASC


class TestSwapSortField:
    def test_values(self):
        assert SwapSortField.CREATED_AT.value == "created_at"
        assert SwapSortField.EXECUTED_AT.value == "executed_at"
        assert SwapSortField.STATUS.value == "status"

    def test_count(self):
        assert len(SwapSortField) == 3


class TestSwapSort:
    def test_defaults(self):
        r = SwapSort()
        assert r.sort_by == SwapSortField.CREATED_AT
        assert r.sort_order == SortOrder.DESC
