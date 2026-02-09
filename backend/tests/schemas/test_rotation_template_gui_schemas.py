"""Tests for rotation_template_gui schemas (Field bounds, Literal types, defaults, model_validators)."""

from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas.rotation_template_gui import (
    WeeklyPatternBase,
    WeeklyPatternUpdate,
    WeeklyGridUpdate,
    RotationPreferenceBase,
    RotationPreferenceUpdate,
    RotationTemplateGUIFields,
    RotationTemplateExtendedCreate,
    HalfDaySummary,
    HalfDayRequirementBase,
    HalfDayRequirementUpdate,
    BatchPatternSlot,
    BatchPatternUpdateRequest,
    BatchPatternUpdateResult,
    BatchPatternUpdateResponse,
    SplitRotationCreate,
    SplitRotationTemplateConfig,
)


# ── WeeklyPatternBase ───────────────────────────────────────────────────


class TestWeeklyPatternBase:
    def test_defaults(self):
        r = WeeklyPatternBase(
            day_of_week=0, time_of_day="AM", activity_type="fm_clinic"
        )
        assert r.activity_id is None
        assert r.week_number is None
        assert r.linked_template_id is None
        assert r.is_protected is False
        assert r.notes is None

    # --- day_of_week (ge=0, le=6) ---

    def test_day_of_week_min(self):
        r = WeeklyPatternBase(day_of_week=0, time_of_day="AM", activity_type="off")
        assert r.day_of_week == 0

    def test_day_of_week_max(self):
        r = WeeklyPatternBase(day_of_week=6, time_of_day="PM", activity_type="off")
        assert r.day_of_week == 6

    def test_day_of_week_below_min(self):
        with pytest.raises(ValidationError):
            WeeklyPatternBase(day_of_week=-1, time_of_day="AM", activity_type="off")

    def test_day_of_week_above_max(self):
        with pytest.raises(ValidationError):
            WeeklyPatternBase(day_of_week=7, time_of_day="AM", activity_type="off")

    # --- time_of_day (Literal["AM", "PM"]) ---

    def test_time_am(self):
        r = WeeklyPatternBase(day_of_week=1, time_of_day="AM", activity_type="off")
        assert r.time_of_day == "AM"

    def test_time_pm(self):
        r = WeeklyPatternBase(day_of_week=1, time_of_day="PM", activity_type="off")
        assert r.time_of_day == "PM"

    def test_time_invalid(self):
        with pytest.raises(ValidationError):
            WeeklyPatternBase(day_of_week=1, time_of_day="NOON", activity_type="off")

    # --- activity_type (max_length=50) ---

    def test_activity_type_too_long(self):
        with pytest.raises(ValidationError):
            WeeklyPatternBase(day_of_week=1, time_of_day="AM", activity_type="x" * 51)

    # --- week_number (ge=1, le=4) ---

    def test_week_number_min(self):
        r = WeeklyPatternBase(
            day_of_week=1, time_of_day="AM", activity_type="off", week_number=1
        )
        assert r.week_number == 1

    def test_week_number_max(self):
        r = WeeklyPatternBase(
            day_of_week=1, time_of_day="AM", activity_type="off", week_number=4
        )
        assert r.week_number == 4

    def test_week_number_below_min(self):
        with pytest.raises(ValidationError):
            WeeklyPatternBase(
                day_of_week=1, time_of_day="AM", activity_type="off", week_number=0
            )

    def test_week_number_above_max(self):
        with pytest.raises(ValidationError):
            WeeklyPatternBase(
                day_of_week=1, time_of_day="AM", activity_type="off", week_number=5
            )

    # --- notes (max_length=200) ---

    def test_notes_too_long(self):
        with pytest.raises(ValidationError):
            WeeklyPatternBase(
                day_of_week=1, time_of_day="AM", activity_type="off", notes="x" * 201
            )

    def test_notes_valid(self):
        r = WeeklyPatternBase(
            day_of_week=1, time_of_day="AM", activity_type="off", notes="Clinic A"
        )
        assert r.notes == "Clinic A"


# ── WeeklyPatternUpdate ─────────────────────────────────────────────────


class TestWeeklyPatternUpdate:
    def test_all_none(self):
        r = WeeklyPatternUpdate()
        assert r.activity_id is None
        assert r.activity_type is None
        assert r.week_number is None
        assert r.linked_template_id is None
        assert r.is_protected is None
        assert r.notes is None

    def test_activity_type_too_long(self):
        with pytest.raises(ValidationError):
            WeeklyPatternUpdate(activity_type="x" * 51)

    def test_week_number_below_min(self):
        with pytest.raises(ValidationError):
            WeeklyPatternUpdate(week_number=0)

    def test_week_number_above_max(self):
        with pytest.raises(ValidationError):
            WeeklyPatternUpdate(week_number=5)

    def test_notes_too_long(self):
        with pytest.raises(ValidationError):
            WeeklyPatternUpdate(notes="x" * 201)


# ── WeeklyGridUpdate ────────────────────────────────────────────────────


class TestWeeklyGridUpdate:
    def _make_pattern(self, **kw):
        defaults = {"day_of_week": 1, "time_of_day": "AM", "activity_type": "off"}
        defaults.update(kw)
        return defaults

    def test_defaults(self):
        r = WeeklyGridUpdate(patterns=[self._make_pattern()])
        assert r.same_pattern_all_weeks is True

    def test_max_56_patterns(self):
        pats = [self._make_pattern(day_of_week=i % 7) for i in range(56)]
        r = WeeklyGridUpdate(patterns=pats)
        assert len(r.patterns) == 56

    def test_too_many_patterns(self):
        pats = [self._make_pattern(day_of_week=i % 7) for i in range(57)]
        with pytest.raises(ValidationError):
            WeeklyGridUpdate(patterns=pats)


# ── RotationPreferenceBase ──────────────────────────────────────────────


class TestRotationPreferenceBase:
    def test_defaults(self):
        r = RotationPreferenceBase(preference_type="full_day_grouping")
        assert r.weight == "medium"
        assert r.config_json == {}
        assert r.is_active is True
        assert r.description is None

    # --- preference_type (max_length=50) ---

    def test_preference_type_too_long(self):
        with pytest.raises(ValidationError):
            RotationPreferenceBase(preference_type="x" * 51)

    # --- weight (Literal) ---

    def test_weight_low(self):
        r = RotationPreferenceBase(preference_type="avoid_friday_pm", weight="low")
        assert r.weight == "low"

    def test_weight_high(self):
        r = RotationPreferenceBase(preference_type="avoid_friday_pm", weight="high")
        assert r.weight == "high"

    def test_weight_required(self):
        r = RotationPreferenceBase(preference_type="avoid_friday_pm", weight="required")
        assert r.weight == "required"

    def test_weight_invalid(self):
        with pytest.raises(ValidationError):
            RotationPreferenceBase(preference_type="test", weight="critical")

    # --- description (max_length=200) ---

    def test_description_too_long(self):
        with pytest.raises(ValidationError):
            RotationPreferenceBase(preference_type="test", description="x" * 201)


# ── RotationPreferenceUpdate ────────────────────────────────────────────


class TestRotationPreferenceUpdate:
    def test_all_none(self):
        r = RotationPreferenceUpdate()
        assert r.weight is None
        assert r.config_json is None
        assert r.is_active is None
        assert r.description is None

    def test_weight_invalid(self):
        with pytest.raises(ValidationError):
            RotationPreferenceUpdate(weight="critical")

    def test_description_too_long(self):
        with pytest.raises(ValidationError):
            RotationPreferenceUpdate(description="x" * 201)


# ── RotationTemplateGUIFields ───────────────────────────────────────────


class TestRotationTemplateGUIFields:
    def test_defaults(self):
        r = RotationTemplateGUIFields()
        assert r.pattern_type == "regular"
        assert r.setting_type == "outpatient"
        assert r.paired_template_id is None
        assert r.split_day is None
        assert r.is_mirror_primary is True

    # --- pattern_type (Literal) ---

    def test_pattern_type_split(self):
        r = RotationTemplateGUIFields(pattern_type="split")
        assert r.pattern_type == "split"

    def test_pattern_type_mirrored(self):
        r = RotationTemplateGUIFields(pattern_type="mirrored")
        assert r.pattern_type == "mirrored"

    def test_pattern_type_alternating(self):
        r = RotationTemplateGUIFields(pattern_type="alternating")
        assert r.pattern_type == "alternating"

    def test_pattern_type_invalid(self):
        with pytest.raises(ValidationError):
            RotationTemplateGUIFields(pattern_type="random")

    # --- setting_type (Literal) ---

    def test_setting_type_inpatient(self):
        r = RotationTemplateGUIFields(setting_type="inpatient")
        assert r.setting_type == "inpatient"

    def test_setting_type_invalid(self):
        with pytest.raises(ValidationError):
            RotationTemplateGUIFields(setting_type="hybrid")

    # --- split_day (ge=1, le=27) ---

    def test_split_day_min(self):
        r = RotationTemplateGUIFields(split_day=1)
        assert r.split_day == 1

    def test_split_day_max(self):
        r = RotationTemplateGUIFields(split_day=27)
        assert r.split_day == 27

    def test_split_day_below_min(self):
        with pytest.raises(ValidationError):
            RotationTemplateGUIFields(split_day=0)

    def test_split_day_above_max(self):
        with pytest.raises(ValidationError):
            RotationTemplateGUIFields(split_day=28)


# ── RotationTemplateExtendedCreate ──────────────────────────────────────


class TestRotationTemplateExtendedCreate:
    def test_defaults(self):
        r = RotationTemplateExtendedCreate(name="FM Clinic", rotation_type="outpatient")
        assert r.abbreviation is None
        assert r.leave_eligible is True
        assert r.supervision_required is True
        assert r.max_supervision_ratio == 4
        assert r.pattern_type == "regular"
        assert r.setting_type == "outpatient"
        assert r.split_day is None
        assert r.is_mirror_primary is True

    def test_split_day_below_min(self):
        with pytest.raises(ValidationError):
            RotationTemplateExtendedCreate(name="T", rotation_type="ip", split_day=0)

    def test_split_day_above_max(self):
        with pytest.raises(ValidationError):
            RotationTemplateExtendedCreate(name="T", rotation_type="ip", split_day=28)


# ── HalfDaySummary ──────────────────────────────────────────────────────


class TestHalfDaySummary:
    def test_defaults(self):
        r = HalfDaySummary()
        assert r.fm_clinic == 0
        assert r.specialty == 0
        assert r.elective == 0
        assert r.conference == 0
        assert r.inpatient == 0
        assert r.call == 0
        assert r.procedure == 0
        assert r.off == 0
        assert r.total == 0


# ── HalfDayRequirementBase ──────────────────────────────────────────────


class TestHalfDayRequirementBase:
    def test_defaults(self):
        r = HalfDayRequirementBase()
        assert r.fm_clinic_halfdays == 4
        assert r.specialty_halfdays == 5
        assert r.specialty_name is None
        assert r.academics_halfdays == 1
        assert r.elective_halfdays == 0
        assert r.min_consecutive_specialty == 1
        assert r.prefer_combined_clinic_days is True

    # --- fm_clinic_halfdays (ge=0, le=14) ---

    def test_fm_clinic_below_min(self):
        with pytest.raises(ValidationError):
            HalfDayRequirementBase(fm_clinic_halfdays=-1)

    def test_fm_clinic_above_max(self):
        with pytest.raises(ValidationError):
            HalfDayRequirementBase(fm_clinic_halfdays=15)

    # --- specialty_halfdays (ge=0, le=14) ---

    def test_specialty_below_min(self):
        with pytest.raises(ValidationError):
            HalfDayRequirementBase(specialty_halfdays=-1)

    def test_specialty_above_max(self):
        with pytest.raises(ValidationError):
            HalfDayRequirementBase(specialty_halfdays=15)

    # --- specialty_name (max_length=255) ---

    def test_specialty_name_too_long(self):
        with pytest.raises(ValidationError):
            HalfDayRequirementBase(specialty_name="x" * 256)

    def test_specialty_name_valid(self):
        r = HalfDayRequirementBase(specialty_name="Neurology")
        assert r.specialty_name == "Neurology"

    # --- academics_halfdays (ge=0, le=14) ---

    def test_academics_below_min(self):
        with pytest.raises(ValidationError):
            HalfDayRequirementBase(academics_halfdays=-1)

    def test_academics_above_max(self):
        with pytest.raises(ValidationError):
            HalfDayRequirementBase(academics_halfdays=15)

    # --- elective_halfdays (ge=0, le=14) ---

    def test_elective_below_min(self):
        with pytest.raises(ValidationError):
            HalfDayRequirementBase(elective_halfdays=-1)

    def test_elective_above_max(self):
        with pytest.raises(ValidationError):
            HalfDayRequirementBase(elective_halfdays=15)

    # --- min_consecutive_specialty (ge=1, le=5) ---

    def test_min_consecutive_below_min(self):
        with pytest.raises(ValidationError):
            HalfDayRequirementBase(min_consecutive_specialty=0)

    def test_min_consecutive_above_max(self):
        with pytest.raises(ValidationError):
            HalfDayRequirementBase(min_consecutive_specialty=6)


# ── HalfDayRequirementUpdate ────────────────────────────────────────────


class TestHalfDayRequirementUpdate:
    def test_all_none(self):
        r = HalfDayRequirementUpdate()
        assert r.fm_clinic_halfdays is None
        assert r.specialty_halfdays is None
        assert r.specialty_name is None
        assert r.academics_halfdays is None
        assert r.elective_halfdays is None
        assert r.min_consecutive_specialty is None
        assert r.prefer_combined_clinic_days is None

    def test_fm_clinic_below_min(self):
        with pytest.raises(ValidationError):
            HalfDayRequirementUpdate(fm_clinic_halfdays=-1)

    def test_fm_clinic_above_max(self):
        with pytest.raises(ValidationError):
            HalfDayRequirementUpdate(fm_clinic_halfdays=15)

    def test_min_consecutive_below_min(self):
        with pytest.raises(ValidationError):
            HalfDayRequirementUpdate(min_consecutive_specialty=0)

    def test_min_consecutive_above_max(self):
        with pytest.raises(ValidationError):
            HalfDayRequirementUpdate(min_consecutive_specialty=6)


# ── BatchPatternSlot ────────────────────────────────────────────────────


class TestBatchPatternSlot:
    def test_defaults(self):
        r = BatchPatternSlot(day_of_week=3, time_of_day="PM")
        assert r.linked_template_id is None
        assert r.activity_type is None
        assert r.is_protected is None
        assert r.notes is None

    def test_day_of_week_below_min(self):
        with pytest.raises(ValidationError):
            BatchPatternSlot(day_of_week=-1, time_of_day="AM")

    def test_day_of_week_above_max(self):
        with pytest.raises(ValidationError):
            BatchPatternSlot(day_of_week=7, time_of_day="AM")

    def test_time_of_day_invalid(self):
        with pytest.raises(ValidationError):
            BatchPatternSlot(day_of_week=1, time_of_day="EVE")

    def test_activity_type_too_long(self):
        with pytest.raises(ValidationError):
            BatchPatternSlot(day_of_week=1, time_of_day="AM", activity_type="x" * 51)

    def test_notes_too_long(self):
        with pytest.raises(ValidationError):
            BatchPatternSlot(day_of_week=1, time_of_day="AM", notes="x" * 201)


# ── BatchPatternUpdateRequest ───────────────────────────────────────────


class TestBatchPatternUpdateRequest:
    def _make_slot(self, **kw):
        defaults = {"day_of_week": 1, "time_of_day": "AM"}
        defaults.update(kw)
        return defaults

    def test_defaults(self):
        r = BatchPatternUpdateRequest(template_ids=[uuid4()], slots=[self._make_slot()])
        assert r.mode == "overlay"
        assert r.week_numbers is None
        assert r.dry_run is False

    def test_mode_replace(self):
        r = BatchPatternUpdateRequest(
            template_ids=[uuid4()], slots=[self._make_slot()], mode="replace"
        )
        assert r.mode == "replace"

    def test_mode_invalid(self):
        with pytest.raises(ValidationError):
            BatchPatternUpdateRequest(
                template_ids=[uuid4()], slots=[self._make_slot()], mode="merge"
            )

    # --- template_ids (min_length=1) ---

    def test_template_ids_empty(self):
        with pytest.raises(ValidationError):
            BatchPatternUpdateRequest(template_ids=[], slots=[self._make_slot()])

    # --- slots (min_length=1, max_length=14) ---

    def test_slots_empty(self):
        with pytest.raises(ValidationError):
            BatchPatternUpdateRequest(template_ids=[uuid4()], slots=[])

    def test_slots_too_many(self):
        slots = [self._make_slot(day_of_week=i % 7) for i in range(15)]
        with pytest.raises(ValidationError):
            BatchPatternUpdateRequest(template_ids=[uuid4()], slots=slots)

    def test_slots_max_ok(self):
        slots = [self._make_slot(day_of_week=i % 7) for i in range(14)]
        r = BatchPatternUpdateRequest(template_ids=[uuid4()], slots=slots)
        assert len(r.slots) == 14

    # --- _normalize_slots model_validator: "patterns" alias ---

    def test_patterns_alias(self):
        data = {
            "template_ids": [str(uuid4())],
            "patterns": [self._make_slot()],
        }
        r = BatchPatternUpdateRequest.model_validate(data)
        assert len(r.slots) == 1


# ── BatchPatternUpdateResult ────────────────────────────────────────────


class TestBatchPatternUpdateResult:
    def test_defaults(self):
        r = BatchPatternUpdateResult(
            template_id=uuid4(), template_name="FM Clinic", success=True
        )
        assert r.slots_modified == 0
        assert r.error is None


# ── BatchPatternUpdateResponse ──────────────────────────────────────────


class TestBatchPatternUpdateResponse:
    def test_defaults(self):
        r = BatchPatternUpdateResponse(
            total_templates=3, successful=2, failed=1, results=[]
        )
        assert r.operation_type == "batch_apply_patterns"
        assert r.total is None
        assert r.succeeded is None
        assert r.dry_run is False


# ── SplitRotationCreate ─────────────────────────────────────────────────


class TestSplitRotationCreate:
    def _make_config(self, **kw):
        defaults = {"name": "Ward A", "rotation_type": "inpatient"}
        defaults.update(kw)
        return SplitRotationTemplateConfig(**defaults)

    def test_defaults(self):
        r = SplitRotationCreate(
            primary_template=self._make_config(),
            secondary_template=self._make_config(name="Ward B"),
            pattern_type="split",
        )
        assert r.split_day == 14
        assert r.create_mirror is False
        assert r.leave_eligible is True
        assert r.supervision_required is True
        assert r.max_supervision_ratio == 4

    def test_pattern_type_mirrored(self):
        r = SplitRotationCreate(
            primary_template=self._make_config(),
            secondary_template=self._make_config(name="Ward B"),
            pattern_type="mirrored",
            create_mirror=True,
        )
        assert r.pattern_type == "mirrored"
        assert r.create_mirror is True

    def test_pattern_type_invalid(self):
        with pytest.raises(ValidationError):
            SplitRotationCreate(
                primary_template=self._make_config(),
                secondary_template=self._make_config(name="Ward B"),
                pattern_type="alternating",
            )

    # --- split_day (ge=1, le=27) ---

    def test_split_day_min(self):
        r = SplitRotationCreate(
            primary_template=self._make_config(),
            secondary_template=self._make_config(name="B"),
            pattern_type="split",
            split_day=1,
        )
        assert r.split_day == 1

    def test_split_day_max(self):
        r = SplitRotationCreate(
            primary_template=self._make_config(),
            secondary_template=self._make_config(name="B"),
            pattern_type="split",
            split_day=27,
        )
        assert r.split_day == 27

    def test_split_day_below_min(self):
        with pytest.raises(ValidationError):
            SplitRotationCreate(
                primary_template=self._make_config(),
                secondary_template=self._make_config(name="B"),
                pattern_type="split",
                split_day=0,
            )

    def test_split_day_above_max(self):
        with pytest.raises(ValidationError):
            SplitRotationCreate(
                primary_template=self._make_config(),
                secondary_template=self._make_config(name="B"),
                pattern_type="split",
                split_day=28,
            )


# ── SplitRotationTemplateConfig ─────────────────────────────────────────


class TestSplitRotationTemplateConfig:
    def test_defaults(self):
        r = SplitRotationTemplateConfig(name="Ward A", rotation_type="inpatient")
        assert r.abbreviation is None
        assert r.font_color is None
        assert r.background_color is None
