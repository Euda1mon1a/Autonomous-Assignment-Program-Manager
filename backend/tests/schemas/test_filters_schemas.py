"""Tests for filter schemas (field_validators, date range, Field bounds)."""

from datetime import date, datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas.filters import (
    DateRangeFilter,
    DateTimeRangeFilter,
    PersonFilter,
    AssignmentFilter,
    BlockFilter,
    SwapFilter,
    SearchFilter,
    StatusFilter,
    IdListFilter,
    BooleanFilter,
    NumericRangeFilter,
)


class TestDateRangeFilter:
    def test_all_none(self):
        r = DateRangeFilter()
        assert r.start_date is None
        assert r.end_date is None

    def test_valid(self):
        r = DateRangeFilter(start_date=date(2026, 3, 1), end_date=date(2026, 3, 31))
        assert r.start_date == date(2026, 3, 1)

    def test_end_before_start(self):
        with pytest.raises(ValidationError, match="end_date must be after start_date"):
            DateRangeFilter(start_date=date(2026, 3, 31), end_date=date(2026, 3, 1))

    def test_end_without_start(self):
        r = DateRangeFilter(end_date=date(2026, 3, 31))
        assert r.end_date == date(2026, 3, 31)


class TestDateTimeRangeFilter:
    def test_all_none(self):
        r = DateTimeRangeFilter()
        assert r.start_datetime is None
        assert r.end_datetime is None

    def test_valid(self):
        r = DateTimeRangeFilter(
            start_datetime=datetime(2026, 3, 1, 8, 0),
            end_datetime=datetime(2026, 3, 1, 17, 0),
        )
        assert r.start_datetime.hour == 8

    def test_end_before_start(self):
        with pytest.raises(
            ValidationError, match="end_datetime must be after start_datetime"
        ):
            DateTimeRangeFilter(
                start_datetime=datetime(2026, 3, 1, 17, 0),
                end_datetime=datetime(2026, 3, 1, 8, 0),
            )


class TestPersonFilter:
    def test_all_none(self):
        r = PersonFilter()
        assert r.person_type is None
        assert r.pgy_level is None
        assert r.faculty_role is None
        assert r.specialties is None
        assert r.performs_procedures is None

    def test_valid_resident(self):
        r = PersonFilter(person_type="resident", pgy_level=2)
        assert r.person_type == "resident"

    def test_valid_faculty(self):
        r = PersonFilter(person_type="faculty")
        assert r.person_type == "faculty"

    def test_invalid_person_type(self):
        with pytest.raises(
            ValidationError, match="person_type must be 'resident' or 'faculty'"
        ):
            PersonFilter(person_type="nurse")

    # --- pgy_level ge=1, le=3 ---

    def test_pgy_level_below_min(self):
        with pytest.raises(ValidationError):
            PersonFilter(pgy_level=0)

    def test_pgy_level_above_max(self):
        with pytest.raises(ValidationError):
            PersonFilter(pgy_level=4)

    def test_pgy_level_boundaries(self):
        r = PersonFilter(pgy_level=1)
        assert r.pgy_level == 1
        r = PersonFilter(pgy_level=3)
        assert r.pgy_level == 3


class TestAssignmentFilter:
    def test_all_none(self):
        r = AssignmentFilter()
        assert r.person_id is None
        assert r.block_id is None
        assert r.rotation_template_id is None
        assert r.role is None
        assert r.date_range is None

    def test_valid_roles(self):
        for role in ("primary", "supervising", "backup"):
            r = AssignmentFilter(role=role)
            assert r.role == role

    def test_invalid_role(self):
        with pytest.raises(
            ValidationError,
            match="role must be 'primary', 'supervising', or 'backup'",
        ):
            AssignmentFilter(role="observer")

    def test_with_date_range(self):
        dr = DateRangeFilter(start_date=date(2026, 3, 1), end_date=date(2026, 3, 31))
        r = AssignmentFilter(person_id=uuid4(), date_range=dr)
        assert r.date_range is not None


class TestBlockFilter:
    def test_all_none(self):
        r = BlockFilter()
        assert r.date_range is None
        assert r.session is None

    def test_valid_sessions(self):
        r = BlockFilter(session="AM")
        assert r.session == "AM"
        r = BlockFilter(session="PM")
        assert r.session == "PM"

    def test_case_insensitive(self):
        r = BlockFilter(session="am")
        assert r.session == "AM"
        r = BlockFilter(session="pm")
        assert r.session == "PM"

    def test_invalid_session(self):
        with pytest.raises(ValidationError, match="session must be 'AM' or 'PM'"):
            BlockFilter(session="EVENING")


class TestSwapFilter:
    def test_all_none(self):
        r = SwapFilter()
        assert r.requester_id is None
        assert r.target_id is None
        assert r.status is None
        assert r.swap_type is None
        assert r.date_range is None

    def test_valid_statuses(self):
        for status in (
            "pending",
            "approved",
            "executed",
            "rejected",
            "cancelled",
            "rolled_back",
        ):
            r = SwapFilter(status=status)
            assert r.status == status

    def test_invalid_status(self):
        with pytest.raises(ValidationError, match="status must be one of"):
            SwapFilter(status="unknown")

    def test_valid_swap_types(self):
        for stype in ("one_to_one", "absorb", "multi_way"):
            r = SwapFilter(swap_type=stype)
            assert r.swap_type == stype

    def test_invalid_swap_type(self):
        with pytest.raises(ValidationError, match="swap_type must be one of"):
            SwapFilter(swap_type="random")


class TestSearchFilter:
    def test_all_none(self):
        r = SearchFilter()
        assert r.query is None
        assert r.fields is None

    def test_valid(self):
        r = SearchFilter(query="Dr. Smith", fields=["name", "email"])
        assert r.query == "Dr. Smith"

    # --- query min_length=1, max_length=255 ---

    def test_query_empty(self):
        with pytest.raises(ValidationError):
            SearchFilter(query="")

    def test_query_too_long(self):
        with pytest.raises(ValidationError):
            SearchFilter(query="x" * 256)

    def test_query_boundaries(self):
        r = SearchFilter(query="a")
        assert r.query == "a"
        r = SearchFilter(query="x" * 255)
        assert len(r.query) == 255


class TestStatusFilter:
    def test_all_none(self):
        r = StatusFilter()
        assert r.status is None
        assert r.exclude_status is None

    def test_single_status(self):
        r = StatusFilter(status="active")
        assert r.status == "active"

    def test_list_status(self):
        r = StatusFilter(status=["active", "pending"])
        assert len(r.status) == 2

    def test_exclude(self):
        r = StatusFilter(exclude_status="deleted")
        assert r.exclude_status == "deleted"


class TestIdListFilter:
    def test_valid(self):
        ids = [uuid4(), uuid4()]
        r = IdListFilter(ids=ids)
        assert len(r.ids) == 2

    # --- ids min_length=1 ---

    def test_ids_empty(self):
        with pytest.raises(ValidationError):
            IdListFilter(ids=[])


class TestBooleanFilter:
    def test_true(self):
        r = BooleanFilter(value=True)
        assert r.value is True

    def test_false(self):
        r = BooleanFilter(value=False)
        assert r.value is False


class TestNumericRangeFilter:
    def test_all_none(self):
        r = NumericRangeFilter()
        assert r.min_value is None
        assert r.max_value is None

    def test_valid(self):
        r = NumericRangeFilter(min_value=0.0, max_value=100.0)
        assert r.min_value == 0.0

    def test_max_less_than_min(self):
        with pytest.raises(
            ValidationError, match="max_value must be greater than min_value"
        ):
            NumericRangeFilter(min_value=100.0, max_value=50.0)

    def test_max_without_min(self):
        r = NumericRangeFilter(max_value=100.0)
        assert r.max_value == 100.0
