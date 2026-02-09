"""Tests for conflict type definitions (enums and Pydantic models)."""

from datetime import date, datetime
from uuid import UUID, uuid4

import pytest
from pydantic import ValidationError

from app.scheduling.conflicts.types import (
    ACGMEViolationConflict,
    Conflict,
    ConflictCategory,
    ConflictSeverity,
    ConflictSummary,
    ConflictTimeline,
    ConflictType,
    ResourceContentionConflict,
    SupervisionConflict,
    TimeOverlapConflict,
)


# ==================== Enum Tests ====================


class TestConflictCategory:
    """Test ConflictCategory enum values."""

    def test_all_categories_exist(self):
        expected = {
            "time_overlap",
            "resource_contention",
            "acgme_violation",
            "supervision_issue",
            "availability_conflict",
            "workload_imbalance",
            "pattern_violation",
        }
        actual = {c.value for c in ConflictCategory}
        assert actual == expected

    def test_category_count(self):
        assert len(ConflictCategory) == 7

    def test_is_string_enum(self):
        assert ConflictCategory.TIME_OVERLAP == "time_overlap"


class TestConflictSeverity:
    """Test ConflictSeverity enum values."""

    def test_all_severities_exist(self):
        expected = {"critical", "high", "medium", "low"}
        actual = {s.value for s in ConflictSeverity}
        assert actual == expected

    def test_severity_count(self):
        assert len(ConflictSeverity) == 4


class TestConflictType:
    """Test ConflictType enum values."""

    def test_has_acgme_types(self):
        acgme_types = [
            ConflictType.EIGHTY_HOUR_VIOLATION,
            ConflictType.ONE_IN_SEVEN_VIOLATION,
            ConflictType.CONTINUOUS_DUTY_VIOLATION,
            ConflictType.NIGHT_FLOAT_VIOLATION,
            ConflictType.PGY_SHIFT_LENGTH_VIOLATION,
        ]
        for ct in acgme_types:
            assert ct.value.endswith("_violation")

    def test_has_time_overlap_types(self):
        assert ConflictType.DOUBLE_BOOKING.value == "double_booking"
        assert ConflictType.OVERLAPPING_SHIFTS.value == "overlapping_shifts"

    def test_has_availability_types(self):
        assert ConflictType.ASSIGNED_DURING_ABSENCE.value == "assigned_during_absence"
        assert (
            ConflictType.ASSIGNED_DURING_DEPLOYMENT.value
            == "assigned_during_deployment"
        )
        assert ConflictType.ASSIGNED_DURING_TDY.value == "assigned_during_tdy"

    def test_total_count(self):
        assert len(ConflictType) == 21


# ==================== Base Conflict Model Tests ====================


def _make_conflict(**overrides) -> dict:
    """Build a valid Conflict dict with defaults."""
    base = {
        "conflict_id": "conf_001",
        "category": ConflictCategory.ACGME_VIOLATION,
        "conflict_type": ConflictType.EIGHTY_HOUR_VIOLATION,
        "severity": ConflictSeverity.CRITICAL,
        "title": "Test Conflict",
        "description": "Test description",
        "start_date": "2024-06-01",
        "end_date": "2024-06-07",
        "impact_score": 0.8,
        "urgency_score": 0.9,
        "complexity_score": 0.5,
    }
    base.update(overrides)
    return base


class TestConflict:
    """Test base Conflict model."""

    def test_valid_conflict(self):
        c = Conflict(**_make_conflict())
        assert c.conflict_id == "conf_001"
        assert c.category == ConflictCategory.ACGME_VIOLATION
        assert c.severity == ConflictSeverity.CRITICAL

    def test_default_affected_lists_empty(self):
        c = Conflict(**_make_conflict())
        assert c.affected_people == []
        assert c.affected_blocks == []
        assert c.affected_assignments == []

    def test_default_context_empty(self):
        c = Conflict(**_make_conflict())
        assert c.context == {}

    def test_default_auto_resolvable_false(self):
        c = Conflict(**_make_conflict())
        assert c.is_auto_resolvable is False

    def test_default_resolution_difficulty(self):
        c = Conflict(**_make_conflict())
        assert c.resolution_difficulty == "medium"

    def test_detected_at_auto_set(self):
        before = datetime.utcnow()
        c = Conflict(**_make_conflict())
        after = datetime.utcnow()
        assert before <= c.detected_at <= after

    def test_impact_score_boundary_zero(self):
        c = Conflict(**_make_conflict(impact_score=0.0))
        assert c.impact_score == 0.0

    def test_impact_score_boundary_one(self):
        c = Conflict(**_make_conflict(impact_score=1.0))
        assert c.impact_score == 1.0

    def test_impact_score_rejects_above_one(self):
        with pytest.raises(ValidationError):
            Conflict(**_make_conflict(impact_score=1.01))

    def test_impact_score_rejects_below_zero(self):
        with pytest.raises(ValidationError):
            Conflict(**_make_conflict(impact_score=-0.1))

    def test_urgency_score_rejects_above_one(self):
        with pytest.raises(ValidationError):
            Conflict(**_make_conflict(urgency_score=1.5))

    def test_complexity_score_rejects_below_zero(self):
        with pytest.raises(ValidationError):
            Conflict(**_make_conflict(complexity_score=-0.5))

    def test_affected_people_uuids(self):
        pid = uuid4()
        c = Conflict(**_make_conflict(affected_people=[pid]))
        assert c.affected_people == [pid]

    def test_serialization_round_trip(self):
        c = Conflict(**_make_conflict())
        d = c.model_dump()
        c2 = Conflict(**d)
        assert c2.conflict_id == c.conflict_id
        assert c2.impact_score == c.impact_score


# ==================== Subclass Tests ====================


def _make_conflict_no_category(**overrides) -> dict:
    """Build valid Conflict dict without category (let subclass defaults work)."""
    data = _make_conflict(**overrides)
    data.pop("category", None)
    return data


class TestTimeOverlapConflict:
    """Test TimeOverlapConflict model."""

    def test_category_set_automatically(self):
        c = TimeOverlapConflict(
            **_make_conflict_no_category(
                conflict_type=ConflictType.DOUBLE_BOOKING,
                severity=ConflictSeverity.HIGH,
            )
        )
        assert c.category == ConflictCategory.TIME_OVERLAP

    def test_overlap_duration(self):
        c = TimeOverlapConflict(
            **_make_conflict_no_category(
                conflict_type=ConflictType.DOUBLE_BOOKING,
                severity=ConflictSeverity.HIGH,
                overlap_duration_hours=4.5,
            )
        )
        assert c.overlap_duration_hours == 4.5

    def test_default_overlap_zero(self):
        c = TimeOverlapConflict(
            **_make_conflict_no_category(
                conflict_type=ConflictType.DOUBLE_BOOKING,
                severity=ConflictSeverity.HIGH,
            )
        )
        assert c.overlap_duration_hours == 0.0


class TestResourceContentionConflict:
    """Test ResourceContentionConflict model."""

    def test_resource_fields(self):
        c = ResourceContentionConflict(
            **_make_conflict_no_category(
                conflict_type=ConflictType.SUPERVISION_RATIO_VIOLATION,
                resource_type="faculty",
                required_count=2,
                available_count=1,
                deficit=1,
            )
        )
        assert c.category == ConflictCategory.RESOURCE_CONTENTION
        assert c.resource_type == "faculty"
        assert c.required_count == 2
        assert c.available_count == 1
        assert c.deficit == 1


class TestACGMEViolationConflict:
    """Test ACGMEViolationConflict model."""

    def test_always_critical_severity(self):
        c = ACGMEViolationConflict(
            **_make_conflict(
                conflict_type=ConflictType.EIGHTY_HOUR_VIOLATION,
                acgme_rule="80-hour work week",
                person_id=uuid4(),
                person_name="Test Resident",
                threshold_value=80.0,
                actual_value=86.5,
                excess_amount=6.5,
            )
        )
        assert c.severity == ConflictSeverity.CRITICAL
        assert c.category == ConflictCategory.ACGME_VIOLATION

    def test_violation_details(self):
        c = ACGMEViolationConflict(
            **_make_conflict(
                conflict_type=ConflictType.ONE_IN_SEVEN_VIOLATION,
                acgme_rule="1-in-7 day off",
                person_id=uuid4(),
                person_name="Dr. Smith",
                pgy_level=1,
                threshold_value=7.0,
                actual_value=10.0,
                excess_amount=3.0,
                consecutive_days=10,
            )
        )
        assert c.pgy_level == 1
        assert c.consecutive_days == 10
        assert c.excess_amount == 3.0

    def test_optional_duty_hours(self):
        c = ACGMEViolationConflict(
            **_make_conflict(
                conflict_type=ConflictType.EIGHTY_HOUR_VIOLATION,
                acgme_rule="80-hour",
                person_id=uuid4(),
                person_name="Dr. Jones",
                threshold_value=80.0,
                actual_value=85.0,
                excess_amount=5.0,
                total_hours=85.0,
                average_weekly_hours=85.0,
            )
        )
        assert c.total_hours == 85.0
        assert c.average_weekly_hours == 85.0


class TestSupervisionConflict:
    """Test SupervisionConflict model."""

    def test_supervision_fields(self):
        c = SupervisionConflict(
            **_make_conflict_no_category(
                conflict_type=ConflictType.INADEQUATE_SUPERVISION,
                severity=ConflictSeverity.CRITICAL,
                pgy1_count=2,
                pgy2_3_count=1,
                faculty_count=0,
                required_faculty_count=1,
            )
        )
        assert c.category == ConflictCategory.SUPERVISION_ISSUE
        assert c.pgy1_count == 2
        assert c.faculty_count == 0
        assert c.required_faculty_count == 1


# ==================== Summary & Timeline Tests ====================


class TestConflictSummary:
    """Test ConflictSummary model."""

    def test_all_defaults_zero(self):
        s = ConflictSummary()
        assert s.total_conflicts == 0
        assert s.critical_count == 0
        assert s.high_count == 0
        assert s.medium_count == 0
        assert s.low_count == 0
        assert s.auto_resolvable_count == 0
        assert s.average_impact_score == 0.0

    def test_custom_counts(self):
        s = ConflictSummary(
            total_conflicts=15,
            critical_count=3,
            high_count=5,
            medium_count=4,
            low_count=3,
            affected_people_count=8,
        )
        assert s.total_conflicts == 15
        assert s.affected_people_count == 8

    def test_by_category_dict(self):
        s = ConflictSummary(by_category={"acgme_violation": 5, "time_overlap": 3})
        assert s.by_category["acgme_violation"] == 5

    def test_optional_dates(self):
        s = ConflictSummary(
            earliest_date=date(2024, 1, 1),
            latest_date=date(2024, 6, 30),
        )
        assert s.earliest_date == date(2024, 1, 1)
        assert s.latest_date == date(2024, 6, 30)

    def test_no_dates_by_default(self):
        s = ConflictSummary()
        assert s.earliest_date is None
        assert s.latest_date is None


class TestConflictTimeline:
    """Test ConflictTimeline model."""

    def test_basic_timeline(self):
        t = ConflictTimeline(
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31),
        )
        assert t.start_date == date(2024, 1, 1)
        assert t.end_date == date(2024, 1, 31)

    def test_default_collections_empty(self):
        t = ConflictTimeline(
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31),
        )
        assert t.timeline_entries == []
        assert t.severity_by_date == {}
        assert t.count_by_date == {}
        assert t.conflicts_by_person == {}
        assert t.category_timeline == []

    def test_severity_by_date(self):
        t = ConflictTimeline(
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31),
            severity_by_date={"2024-01-08": 0.85, "2024-01-15": 0.62},
            count_by_date={"2024-01-08": 3, "2024-01-15": 2},
        )
        assert t.severity_by_date["2024-01-08"] == 0.85
        assert t.count_by_date["2024-01-15"] == 2

    def test_serialization(self):
        t = ConflictTimeline(
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31),
            severity_by_date={"2024-01-08": 0.85},
        )
        d = t.model_dump()
        t2 = ConflictTimeline(**d)
        assert t2.severity_by_date == t.severity_by_date
