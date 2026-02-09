"""Tests for block schemas (Field bounds, pattern, field_validators, date validator)."""

from datetime import date, timedelta
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas.block import BlockBase, BlockCreate, BlockResponse, BlockListResponse

# validate_academic_year_date raises app.validators.common.ValidationError
from app.validators.common import ValidationError as AppValidationError


class TestBlockBase:
    def _valid_kwargs(self):
        return {
            "date": date.today(),
            "time_of_day": "AM",
            "block_number": 5,
        }

    def test_valid_minimal(self):
        r = BlockBase(**self._valid_kwargs())
        assert r.is_weekend is False
        assert r.is_holiday is False
        assert r.holiday_name is None

    def test_full(self):
        kw = self._valid_kwargs()
        kw.update(is_weekend=True, is_holiday=True, holiday_name="Christmas")
        r = BlockBase(**kw)
        assert r.is_weekend is True
        assert r.is_holiday is True
        assert r.holiday_name == "Christmas"

    # --- time_of_day pattern ^(AM|PM)$ ---

    def test_time_of_day_am(self):
        kw = self._valid_kwargs()
        kw["time_of_day"] = "AM"
        r = BlockBase(**kw)
        assert r.time_of_day == "AM"

    def test_time_of_day_pm(self):
        kw = self._valid_kwargs()
        kw["time_of_day"] = "PM"
        r = BlockBase(**kw)
        assert r.time_of_day == "PM"

    def test_time_of_day_invalid(self):
        kw = self._valid_kwargs()
        kw["time_of_day"] = "NOON"
        with pytest.raises(ValidationError):
            BlockBase(**kw)

    def test_time_of_day_lowercase(self):
        kw = self._valid_kwargs()
        kw["time_of_day"] = "am"
        with pytest.raises(ValidationError):
            BlockBase(**kw)

    # --- block_number ge=0, le=14 ---

    def test_block_number_boundaries(self):
        kw = self._valid_kwargs()
        kw["block_number"] = 0
        r = BlockBase(**kw)
        assert r.block_number == 0

        kw["block_number"] = 14
        r = BlockBase(**kw)
        assert r.block_number == 14

    def test_block_number_negative(self):
        kw = self._valid_kwargs()
        kw["block_number"] = -1
        with pytest.raises(ValidationError):
            BlockBase(**kw)

    def test_block_number_above_max(self):
        kw = self._valid_kwargs()
        kw["block_number"] = 15
        with pytest.raises(ValidationError):
            BlockBase(**kw)

    # --- holiday_name min_length=1, max_length=100 ---

    def test_holiday_name_empty(self):
        kw = self._valid_kwargs()
        kw["holiday_name"] = ""
        with pytest.raises(ValidationError):
            BlockBase(**kw)

    def test_holiday_name_too_long(self):
        kw = self._valid_kwargs()
        kw["holiday_name"] = "x" * 101
        with pytest.raises(ValidationError):
            BlockBase(**kw)

    def test_holiday_name_max_length(self):
        kw = self._valid_kwargs()
        kw["holiday_name"] = "x" * 100
        r = BlockBase(**kw)
        assert len(r.holiday_name) == 100

    # --- date field_validator (academic year bounds) ---

    def test_date_far_past(self):
        kw = self._valid_kwargs()
        kw["date"] = date.today() - timedelta(days=365 * 6)
        with pytest.raises((ValidationError, AppValidationError)):
            BlockBase(**kw)

    def test_date_far_future(self):
        kw = self._valid_kwargs()
        kw["date"] = date.today() + timedelta(days=365 * 6)
        with pytest.raises((ValidationError, AppValidationError)):
            BlockBase(**kw)


class TestBlockCreate:
    def test_inherits_base(self):
        r = BlockCreate(date=date.today(), time_of_day="AM", block_number=3)
        assert r.block_number == 3


class TestBlockResponse:
    def test_valid(self):
        r = BlockResponse(
            id=uuid4(),
            date=date.today(),
            time_of_day="PM",
            block_number=10,
        )
        assert r.id is not None


class TestBlockListResponse:
    def test_valid(self):
        resp = BlockResponse(
            id=uuid4(), date=date.today(), time_of_day="AM", block_number=1
        )
        r = BlockListResponse(items=[resp], total=1)
        assert len(r.items) == 1
        assert r.total == 1

    def test_empty(self):
        r = BlockListResponse(items=[], total=0)
        assert r.items == []

    # --- total ge=0 ---

    def test_total_negative(self):
        with pytest.raises(ValidationError):
            BlockListResponse(items=[], total=-1)
