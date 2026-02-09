"""Tests for activity schemas (Pydantic validation, field_validator, Field bounds)."""

from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas.activity import (
    ActivityCategory,
    VALID_ACTIVITY_CATEGORIES,
    ActivityBase,
    ActivityCreate,
    ActivityUpdate,
    ActivityListResponse,
    ActivityRequirementBase,
    ActivityRequirementUpdate,
    ActivityRequirementBulkUpdate,
)


# ===========================================================================
# Enum Tests
# ===========================================================================


class TestActivityCategory:
    def test_values(self):
        assert ActivityCategory.CLINICAL.value == "clinical"
        assert ActivityCategory.EDUCATIONAL.value == "educational"
        assert ActivityCategory.ADMINISTRATIVE.value == "administrative"
        assert ActivityCategory.TIME_OFF.value == "time_off"

    def test_count(self):
        assert len(ActivityCategory) == 4

    def test_valid_categories_tuple(self):
        assert len(VALID_ACTIVITY_CATEGORIES) == 4
        assert "clinical" in VALID_ACTIVITY_CATEGORIES


# ===========================================================================
# ActivityBase Tests
# ===========================================================================


class TestActivityBase:
    def _valid_kwargs(self):
        return {
            "name": "FM Clinic",
            "code": "fm_clinic",
            "activity_category": "clinical",
        }

    def test_valid_minimal(self):
        r = ActivityBase(**self._valid_kwargs())
        assert r.display_abbreviation is None
        assert r.font_color is None
        assert r.background_color is None
        assert r.requires_supervision is True
        assert r.is_protected is False
        assert r.counts_toward_clinical_hours is True
        assert r.display_order == 0

    def test_full(self):
        r = ActivityBase(
            name="Lecture",
            code="lec",
            display_abbreviation="LEC",
            activity_category="educational",
            font_color="text-blue-700",
            background_color="bg-blue-100",
            requires_supervision=False,
            is_protected=True,
            counts_toward_clinical_hours=False,
            display_order=10,
        )
        assert r.is_protected is True

    # --- name field_validator (strip + not empty) ---

    def test_name_empty(self):
        kw = self._valid_kwargs()
        kw["name"] = ""
        with pytest.raises(ValidationError):
            ActivityBase(**kw)

    def test_name_whitespace_only(self):
        kw = self._valid_kwargs()
        kw["name"] = "   "
        with pytest.raises(ValidationError):
            ActivityBase(**kw)

    def test_name_strips_whitespace(self):
        kw = self._valid_kwargs()
        kw["name"] = "  FM Clinic  "
        r = ActivityBase(**kw)
        assert r.name == "FM Clinic"

    # --- code field_validator (strip, lowercase, alphanumeric + _/-) ---

    def test_code_empty(self):
        kw = self._valid_kwargs()
        kw["code"] = ""
        with pytest.raises(ValidationError):
            ActivityBase(**kw)

    def test_code_whitespace_only(self):
        kw = self._valid_kwargs()
        kw["code"] = "   "
        with pytest.raises(ValidationError):
            ActivityBase(**kw)

    def test_code_lowercased(self):
        kw = self._valid_kwargs()
        kw["code"] = "FM_CLINIC"
        r = ActivityBase(**kw)
        assert r.code == "fm_clinic"

    def test_code_with_hyphens(self):
        kw = self._valid_kwargs()
        kw["code"] = "fm-clinic"
        r = ActivityBase(**kw)
        assert r.code == "fm-clinic"

    def test_code_invalid_chars(self):
        kw = self._valid_kwargs()
        kw["code"] = "fm clinic"  # space not allowed
        with pytest.raises(ValidationError):
            ActivityBase(**kw)

    def test_code_invalid_special_chars(self):
        kw = self._valid_kwargs()
        kw["code"] = "fm.clinic"  # dot not allowed
        with pytest.raises(ValidationError):
            ActivityBase(**kw)

    # --- code max_length=50 ---

    def test_code_too_long(self):
        kw = self._valid_kwargs()
        kw["code"] = "a" * 51
        with pytest.raises(ValidationError):
            ActivityBase(**kw)

    # --- display_abbreviation max_length=20 ---

    def test_display_abbreviation_too_long(self):
        kw = self._valid_kwargs()
        kw["display_abbreviation"] = "x" * 21
        with pytest.raises(ValidationError):
            ActivityBase(**kw)

    # --- activity_category field_validator ---

    def test_all_valid_categories(self):
        for cat in VALID_ACTIVITY_CATEGORIES:
            kw = self._valid_kwargs()
            kw["activity_category"] = cat
            r = ActivityBase(**kw)
            assert r.activity_category == cat

    def test_invalid_category(self):
        kw = self._valid_kwargs()
        kw["activity_category"] = "social"
        with pytest.raises(ValidationError):
            ActivityBase(**kw)


# ===========================================================================
# ActivityCreate Tests
# ===========================================================================


class TestActivityCreate:
    def test_inherits_base(self):
        r = ActivityCreate(
            name="Lecture",
            code="lec",
            activity_category="educational",
        )
        assert r.name == "Lecture"


# ===========================================================================
# ActivityUpdate Tests
# ===========================================================================


class TestActivityUpdate:
    def test_all_none(self):
        r = ActivityUpdate()
        assert r.name is None
        assert r.code is None
        assert r.display_abbreviation is None
        assert r.activity_category is None

    # --- code field_validator (None allowed) ---

    def test_code_valid(self):
        r = ActivityUpdate(code="new_code")
        assert r.code == "new_code"

    def test_code_none_allowed(self):
        r = ActivityUpdate(code=None)
        assert r.code is None

    def test_code_invalid_chars(self):
        with pytest.raises(ValidationError):
            ActivityUpdate(code="bad code")

    # --- activity_category field_validator (None allowed) ---

    def test_category_valid(self):
        r = ActivityUpdate(activity_category="educational")
        assert r.activity_category == "educational"

    def test_category_none_allowed(self):
        r = ActivityUpdate(activity_category=None)
        assert r.activity_category is None

    def test_category_invalid(self):
        with pytest.raises(ValidationError):
            ActivityUpdate(activity_category="social")


# ===========================================================================
# ActivityListResponse Tests
# ===========================================================================


class TestActivityListResponse:
    def test_valid(self):
        r = ActivityListResponse(activities=[], total=0)
        assert r.activities == []


# ===========================================================================
# ActivityRequirementBase Tests
# ===========================================================================


class TestActivityRequirementBase:
    def _valid_kwargs(self):
        return {"activity_id": uuid4()}

    def test_valid_minimal(self):
        r = ActivityRequirementBase(**self._valid_kwargs())
        assert r.min_halfdays == 0
        assert r.max_halfdays == 14
        assert r.target_halfdays is None
        assert r.applicable_weeks is None
        assert r.prefer_full_days is True
        assert r.preferred_days is None
        assert r.avoid_days is None
        assert r.priority == 50

    # --- min_halfdays ge=0, le=28 ---

    def test_min_halfdays_boundaries(self):
        kw = self._valid_kwargs()
        kw["min_halfdays"] = 0
        r = ActivityRequirementBase(**kw)
        assert r.min_halfdays == 0

        kw["min_halfdays"] = 28
        r = ActivityRequirementBase(**kw)
        assert r.min_halfdays == 28

    def test_min_halfdays_negative(self):
        kw = self._valid_kwargs()
        kw["min_halfdays"] = -1
        with pytest.raises(ValidationError):
            ActivityRequirementBase(**kw)

    def test_min_halfdays_above_max(self):
        kw = self._valid_kwargs()
        kw["min_halfdays"] = 29
        with pytest.raises(ValidationError):
            ActivityRequirementBase(**kw)

    # --- max_halfdays ge=0, le=28 ---

    def test_max_halfdays_negative(self):
        kw = self._valid_kwargs()
        kw["max_halfdays"] = -1
        with pytest.raises(ValidationError):
            ActivityRequirementBase(**kw)

    def test_max_halfdays_above_max(self):
        kw = self._valid_kwargs()
        kw["max_halfdays"] = 29
        with pytest.raises(ValidationError):
            ActivityRequirementBase(**kw)

    # --- target_halfdays ge=0, le=28 ---

    def test_target_halfdays_negative(self):
        kw = self._valid_kwargs()
        kw["target_halfdays"] = -1
        with pytest.raises(ValidationError):
            ActivityRequirementBase(**kw)

    def test_target_halfdays_above_max(self):
        kw = self._valid_kwargs()
        kw["target_halfdays"] = 29
        with pytest.raises(ValidationError):
            ActivityRequirementBase(**kw)

    # --- priority ge=0, le=100 ---

    def test_priority_boundaries(self):
        kw = self._valid_kwargs()
        kw["priority"] = 0
        r = ActivityRequirementBase(**kw)
        assert r.priority == 0

        kw["priority"] = 100
        r = ActivityRequirementBase(**kw)
        assert r.priority == 100

    def test_priority_negative(self):
        kw = self._valid_kwargs()
        kw["priority"] = -1
        with pytest.raises(ValidationError):
            ActivityRequirementBase(**kw)

    def test_priority_above_max(self):
        kw = self._valid_kwargs()
        kw["priority"] = 101
        with pytest.raises(ValidationError):
            ActivityRequirementBase(**kw)

    # --- applicable_weeks field_validator (1-4, dedup, sort) ---

    def test_applicable_weeks_valid(self):
        kw = self._valid_kwargs()
        kw["applicable_weeks"] = [3, 1, 2]
        r = ActivityRequirementBase(**kw)
        assert r.applicable_weeks == [1, 2, 3]

    def test_applicable_weeks_dedup(self):
        kw = self._valid_kwargs()
        kw["applicable_weeks"] = [2, 2, 1, 1]
        r = ActivityRequirementBase(**kw)
        assert r.applicable_weeks == [1, 2]

    def test_applicable_weeks_zero(self):
        kw = self._valid_kwargs()
        kw["applicable_weeks"] = [0]
        with pytest.raises(ValidationError):
            ActivityRequirementBase(**kw)

    def test_applicable_weeks_five(self):
        kw = self._valid_kwargs()
        kw["applicable_weeks"] = [5]
        with pytest.raises(ValidationError):
            ActivityRequirementBase(**kw)

    # --- preferred_days / avoid_days field_validator (0-6, dedup, sort) ---

    def test_preferred_days_valid(self):
        kw = self._valid_kwargs()
        kw["preferred_days"] = [5, 3, 1]
        r = ActivityRequirementBase(**kw)
        assert r.preferred_days == [1, 3, 5]

    def test_preferred_days_dedup(self):
        kw = self._valid_kwargs()
        kw["preferred_days"] = [1, 1, 3, 3]
        r = ActivityRequirementBase(**kw)
        assert r.preferred_days == [1, 3]

    def test_preferred_days_negative(self):
        kw = self._valid_kwargs()
        kw["preferred_days"] = [-1]
        with pytest.raises(ValidationError):
            ActivityRequirementBase(**kw)

    def test_preferred_days_seven(self):
        kw = self._valid_kwargs()
        kw["preferred_days"] = [7]
        with pytest.raises(ValidationError):
            ActivityRequirementBase(**kw)

    def test_avoid_days_valid(self):
        kw = self._valid_kwargs()
        kw["avoid_days"] = [0, 6]
        r = ActivityRequirementBase(**kw)
        assert r.avoid_days == [0, 6]

    def test_avoid_days_negative(self):
        kw = self._valid_kwargs()
        kw["avoid_days"] = [-1]
        with pytest.raises(ValidationError):
            ActivityRequirementBase(**kw)


# ===========================================================================
# ActivityRequirementUpdate Tests
# ===========================================================================


class TestActivityRequirementUpdate:
    def test_all_none(self):
        r = ActivityRequirementUpdate()
        assert r.min_halfdays is None
        assert r.max_halfdays is None
        assert r.target_halfdays is None
        assert r.priority is None

    # --- min_halfdays ge=0, le=28 ---

    def test_min_halfdays_negative(self):
        with pytest.raises(ValidationError):
            ActivityRequirementUpdate(min_halfdays=-1)

    def test_min_halfdays_above_max(self):
        with pytest.raises(ValidationError):
            ActivityRequirementUpdate(min_halfdays=29)

    # --- priority ge=0, le=100 ---

    def test_priority_negative(self):
        with pytest.raises(ValidationError):
            ActivityRequirementUpdate(priority=-1)

    def test_priority_above_max(self):
        with pytest.raises(ValidationError):
            ActivityRequirementUpdate(priority=101)


# ===========================================================================
# ActivityRequirementBulkUpdate Tests
# ===========================================================================


class TestActivityRequirementBulkUpdate:
    def test_valid(self):
        r = ActivityRequirementBulkUpdate(requirements=[])
        assert r.requirements == []
