"""Tests for faculty primary duty clinic constraints (no DB)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta
from uuid import UUID, uuid4

import pytest

from app.scheduling.constraints.primary_duty import (
    FacultyClinicEquitySoftConstraint,
    FacultyDayAvailabilityConstraint,
    FacultyPrimaryDutyClinicConstraint,
    PrimaryDutyConfig,
    load_primary_duties_config,
)
from app.scheduling.constraints.base import (
    ConstraintResult,
    SchedulingContext,
)


# ---------------------------------------------------------------------------
# Mocks
# ---------------------------------------------------------------------------


@dataclass
class MockFaculty:
    id: UUID = field(default_factory=uuid4)
    name: str = "Dr. Test"
    primary_duty: str | None = None


@dataclass
class MockBlock:
    id: UUID = field(default_factory=uuid4)
    date: date = field(default_factory=lambda: date(2024, 1, 1))


@dataclass
class MockTemplate:
    id: UUID = field(default_factory=uuid4)
    rotation_type: str = "outpatient"


@dataclass
class MockAssignment:
    person_id: UUID = field(default_factory=uuid4)
    block_id: UUID = field(default_factory=uuid4)
    rotation_template_id: UUID = field(default_factory=uuid4)


def _make_week_blocks(start: date) -> list[MockBlock]:
    """Create blocks for Mon-Fri of a week."""
    # Ensure start is Monday
    days_since_monday = start.weekday()
    monday = start - timedelta(days=days_since_monday)
    return [MockBlock(id=uuid4(), date=monday + timedelta(days=d)) for d in range(5)]


def _make_context(
    faculty: list[MockFaculty],
    blocks: list[MockBlock],
    templates: list[MockTemplate] | None = None,
) -> SchedulingContext:
    """Build a minimal SchedulingContext."""
    if templates is None:
        templates = [MockTemplate()]
    return SchedulingContext(
        residents=[],
        faculty=faculty,
        blocks=blocks,
        templates=templates,
        faculty_idx={f.id: i for i, f in enumerate(faculty)},
        block_idx={b.id: i for i, b in enumerate(blocks)},
        template_idx={t.id: i for i, t in enumerate(templates)},
    )


# ---------------------------------------------------------------------------
# PrimaryDutyConfig dataclass
# ---------------------------------------------------------------------------


class TestPrimaryDutyConfig:
    def test_defaults(self):
        cfg = PrimaryDutyConfig(duty_id="rec1", duty_name="Faculty Alpha")
        assert cfg.clinic_min_per_week == 0
        assert cfg.clinic_max_per_week == 10
        assert cfg.available_days == {0, 1, 2, 3, 4}
        assert cfg.allowed_clinic_templates == set()
        assert cfg.faculty_ids == []

    def test_custom(self):
        cfg = PrimaryDutyConfig(
            duty_id="rec2",
            duty_name="PD",
            clinic_min_per_week=2,
            clinic_max_per_week=4,
            available_days={0, 2, 4},
        )
        assert cfg.clinic_min_per_week == 2
        assert cfg.clinic_max_per_week == 4
        assert cfg.available_days == {0, 2, 4}

    def test_from_airtable_record_basic(self):
        record = {
            "id": "rec123",
            "fields": {
                "primaryDuty": "Faculty Alpha",
                "Clinic Minimum Half-Days Per Week": 3,
                "Clinic Maximum Half-Days Per Week": 5,
                "Faculty": ["fac1", "fac2"],
            },
        }
        cfg = PrimaryDutyConfig.from_airtable_record(record)
        assert cfg.duty_id == "rec123"
        assert cfg.duty_name == "Faculty Alpha"
        assert cfg.clinic_min_per_week == 3
        assert cfg.clinic_max_per_week == 5
        assert cfg.faculty_ids == ["fac1", "fac2"]

    def test_from_airtable_record_day_availability(self):
        record = {
            "id": "rec123",
            "fields": {
                "primaryDuty": "Test",
                "availableMonday": True,
                "availableTuesday": False,
                "availableWednesday": True,
                "availableThursday": False,
                "availableFriday": True,
            },
        }
        cfg = PrimaryDutyConfig.from_airtable_record(record)
        assert cfg.available_days == {0, 2, 4}

    def test_from_airtable_record_no_days_defaults_all(self):
        record = {
            "id": "rec123",
            "fields": {"primaryDuty": "Test"},
        }
        cfg = PrimaryDutyConfig.from_airtable_record(record)
        assert cfg.available_days == {0, 1, 2, 3, 4}

    def test_from_airtable_record_empty(self):
        record = {}
        cfg = PrimaryDutyConfig.from_airtable_record(record)
        assert cfg.duty_id == ""
        assert cfg.duty_name == "Unknown"

    def test_from_airtable_record_templates(self):
        record = {
            "id": "rec123",
            "fields": {
                "primaryDuty": "Test",
                "attendingClinicTemplates": ["tpl1", "tpl2"],
            },
        }
        cfg = PrimaryDutyConfig.from_airtable_record(record)
        assert cfg.allowed_clinic_templates == {"tpl1", "tpl2"}


# ---------------------------------------------------------------------------
# load_primary_duties_config
# ---------------------------------------------------------------------------


class TestLoadPrimaryDutiesConfig:
    def test_missing_session_raises(self):
        """Missing db_session raises ValueError."""
        import pytest

        with pytest.raises(ValueError, match="db_session is required"):
            load_primary_duties_config(db_session=None)

    def test_wrong_type_session_raises(self):
        """Wrong-type db_session raises TypeError."""
        import pytest

        with pytest.raises(TypeError, match="SQLAlchemy Session"):
            load_primary_duties_config(db_session="/some/path.json")

    def test_valid_db_load(self):
        """Mock DB session returns configs correctly."""
        from unittest.mock import MagicMock

        mock_row = MagicMock()
        mock_row.id = "test-uuid"
        mock_row.duty_name = "Faculty Alpha"
        mock_row.clinic_min_per_week = 2
        mock_row.clinic_max_per_week = 4
        mock_row.available_days = [0, 1, 2, 3, 4]

        mock_session = MagicMock()
        mock_session.query.return_value.all.return_value = [mock_row]

        result = load_primary_duties_config(db_session=mock_session)
        assert "Faculty Alpha" in result
        assert result["Faculty Alpha"].clinic_min_per_week == 2


# ---------------------------------------------------------------------------
# FacultyPrimaryDutyClinicConstraint — validate
# ---------------------------------------------------------------------------


class TestPrimaryDutyClinicValidate:
    def _make_constraint(self, configs: dict[str, PrimaryDutyConfig]):
        return FacultyPrimaryDutyClinicConstraint(duty_configs=configs)

    def test_no_violations_within_limits(self):
        cfg = PrimaryDutyConfig(
            duty_id="d1",
            duty_name="Alpha",
            clinic_min_per_week=2,
            clinic_max_per_week=4,
        )
        fac = MockFaculty(primary_duty="Alpha")
        blocks = _make_week_blocks(date(2024, 1, 1))
        tpl = MockTemplate()
        ctx = _make_context([fac], blocks, [tpl])

        # 3 clinic assignments (within 2-4)
        assignments = [
            MockAssignment(
                person_id=fac.id, block_id=blocks[i].id, rotation_template_id=tpl.id
            )
            for i in range(3)
        ]

        constraint = self._make_constraint({"Alpha": cfg})
        result = constraint.validate(assignments, ctx)
        assert result.satisfied is True
        assert len(result.violations) == 0

    def test_below_minimum(self):
        cfg = PrimaryDutyConfig(
            duty_id="d1",
            duty_name="Alpha",
            clinic_min_per_week=3,
            clinic_max_per_week=5,
        )
        fac = MockFaculty(primary_duty="Alpha")
        blocks = _make_week_blocks(date(2024, 1, 1))
        tpl = MockTemplate()
        ctx = _make_context([fac], blocks, [tpl])

        # Only 1 assignment (below min of 3)
        assignments = [
            MockAssignment(
                person_id=fac.id, block_id=blocks[0].id, rotation_template_id=tpl.id
            )
        ]

        constraint = self._make_constraint({"Alpha": cfg})
        result = constraint.validate(assignments, ctx)
        assert result.satisfied is False
        assert any("minimum" in v.message for v in result.violations)

    def test_above_maximum(self):
        cfg = PrimaryDutyConfig(
            duty_id="d1",
            duty_name="Alpha",
            clinic_min_per_week=0,
            clinic_max_per_week=2,
        )
        fac = MockFaculty(primary_duty="Alpha")
        blocks = _make_week_blocks(date(2024, 1, 1))
        tpl = MockTemplate()
        ctx = _make_context([fac], blocks, [tpl])

        # 4 assignments (above max of 2)
        assignments = [
            MockAssignment(
                person_id=fac.id, block_id=blocks[i].id, rotation_template_id=tpl.id
            )
            for i in range(4)
        ]

        constraint = self._make_constraint({"Alpha": cfg})
        result = constraint.validate(assignments, ctx)
        assert result.satisfied is False
        assert any("exceeds maximum" in v.message for v in result.violations)

    def test_faculty_without_duty_config_skipped(self):
        fac = MockFaculty(primary_duty=None)
        blocks = _make_week_blocks(date(2024, 1, 1))
        tpl = MockTemplate()
        ctx = _make_context([fac], blocks, [tpl])
        assignments = [
            MockAssignment(
                person_id=fac.id, block_id=blocks[0].id, rotation_template_id=tpl.id
            )
        ]
        constraint = self._make_constraint({})
        result = constraint.validate(assignments, ctx)
        assert result.satisfied is True

    def test_non_clinic_templates_ignored(self):
        cfg = PrimaryDutyConfig(
            duty_id="d1",
            duty_name="Alpha",
            clinic_min_per_week=5,
            clinic_max_per_week=5,
        )
        fac = MockFaculty(primary_duty="Alpha")
        blocks = _make_week_blocks(date(2024, 1, 1))
        inpatient = MockTemplate(rotation_type="inpatient")
        ctx = _make_context([fac], blocks, [inpatient])

        # Inpatient assignments don't count toward clinic
        assignments = [
            MockAssignment(
                person_id=fac.id,
                block_id=blocks[0].id,
                rotation_template_id=inpatient.id,
            )
        ]

        constraint = self._make_constraint({"Alpha": cfg})
        result = constraint.validate(assignments, ctx)
        # Min=5, but 0 clinic assignments -> violation
        assert result.satisfied is False

    def test_get_week_start(self):
        constraint = FacultyPrimaryDutyClinicConstraint(duty_configs={})
        # Wednesday Jan 3, 2024 -> Monday Jan 1, 2024
        assert constraint._get_week_start(date(2024, 1, 3)) == date(2024, 1, 1)
        # Monday itself
        assert constraint._get_week_start(date(2024, 1, 1)) == date(2024, 1, 1)
        # Friday
        assert constraint._get_week_start(date(2024, 1, 5)) == date(2024, 1, 1)

    def test_group_blocks_by_week(self):
        constraint = FacultyPrimaryDutyClinicConstraint(duty_configs={})
        blocks = _make_week_blocks(date(2024, 1, 1)) + _make_week_blocks(
            date(2024, 1, 8)
        )
        weeks = constraint._group_blocks_by_week(blocks)
        assert len(weeks) == 2
        assert date(2024, 1, 1) in weeks
        assert date(2024, 1, 8) in weeks


# ---------------------------------------------------------------------------
# FacultyDayAvailabilityConstraint — validate
# ---------------------------------------------------------------------------


class TestDayAvailabilityValidate:
    def _make_constraint(self, configs: dict[str, PrimaryDutyConfig]):
        return FacultyDayAvailabilityConstraint(duty_configs=configs)

    def test_no_violations_on_available_days(self):
        cfg = PrimaryDutyConfig(
            duty_id="d1",
            duty_name="Alpha",
            available_days={0, 2, 4},  # Mon, Wed, Fri
        )
        fac = MockFaculty(primary_duty="Alpha")
        blocks = _make_week_blocks(date(2024, 1, 1))
        tpl = MockTemplate()
        ctx = _make_context([fac], blocks, [tpl])

        # Assign only on Mon (idx=0), Wed (idx=2), Fri (idx=4)
        assignments = [
            MockAssignment(
                person_id=fac.id, block_id=blocks[0].id, rotation_template_id=tpl.id
            ),
            MockAssignment(
                person_id=fac.id, block_id=blocks[2].id, rotation_template_id=tpl.id
            ),
            MockAssignment(
                person_id=fac.id, block_id=blocks[4].id, rotation_template_id=tpl.id
            ),
        ]

        constraint = self._make_constraint({"Alpha": cfg})
        result = constraint.validate(assignments, ctx)
        assert result.satisfied is True

    def test_violation_on_unavailable_day(self):
        cfg = PrimaryDutyConfig(
            duty_id="d1",
            duty_name="Alpha",
            available_days={0, 2, 4},  # Mon, Wed, Fri
        )
        fac = MockFaculty(primary_duty="Alpha")
        blocks = _make_week_blocks(date(2024, 1, 1))
        tpl = MockTemplate()
        ctx = _make_context([fac], blocks, [tpl])

        # Assign on Tuesday (idx=1) — unavailable
        assignments = [
            MockAssignment(
                person_id=fac.id, block_id=blocks[1].id, rotation_template_id=tpl.id
            ),
        ]

        constraint = self._make_constraint({"Alpha": cfg})
        result = constraint.validate(assignments, ctx)
        assert result.satisfied is False
        assert len(result.violations) == 1
        assert "Tuesday" in result.violations[0].message

    def test_no_duty_config_skipped(self):
        fac = MockFaculty(primary_duty="Unknown")
        blocks = _make_week_blocks(date(2024, 1, 1))
        tpl = MockTemplate()
        ctx = _make_context([fac], blocks, [tpl])
        assignments = [
            MockAssignment(
                person_id=fac.id, block_id=blocks[0].id, rotation_template_id=tpl.id
            ),
        ]
        constraint = self._make_constraint({})
        result = constraint.validate(assignments, ctx)
        assert result.satisfied is True

    def test_non_clinic_ignored(self):
        cfg = PrimaryDutyConfig(
            duty_id="d1",
            duty_name="Alpha",
            available_days={0},  # Monday only
        )
        fac = MockFaculty(primary_duty="Alpha")
        blocks = _make_week_blocks(date(2024, 1, 1))
        inpatient = MockTemplate(rotation_type="inpatient")
        ctx = _make_context([fac], blocks, [inpatient])

        # Inpatient on Tuesday — should NOT trigger availability violation
        assignments = [
            MockAssignment(
                person_id=fac.id,
                block_id=blocks[1].id,
                rotation_template_id=inpatient.id,
            ),
        ]
        constraint = self._make_constraint({"Alpha": cfg})
        result = constraint.validate(assignments, ctx)
        assert result.satisfied is True


# ---------------------------------------------------------------------------
# FacultyClinicEquitySoftConstraint — validate
# ---------------------------------------------------------------------------


class TestClinicEquityValidate:
    def _make_constraint(
        self, configs: dict[str, PrimaryDutyConfig], weight: float = 15.0
    ):
        return FacultyClinicEquitySoftConstraint(weight=weight, duty_configs=configs)

    def test_at_target_no_penalty(self):
        # Target = (2+4)//2 = 3
        cfg = PrimaryDutyConfig(
            duty_id="d1",
            duty_name="Alpha",
            clinic_min_per_week=2,
            clinic_max_per_week=4,
        )
        fac = MockFaculty(primary_duty="Alpha")
        blocks = _make_week_blocks(date(2024, 1, 1))
        tpl = MockTemplate()
        ctx = _make_context([fac], blocks, [tpl])

        # Exactly 3 assignments
        assignments = [
            MockAssignment(
                person_id=fac.id, block_id=blocks[i].id, rotation_template_id=tpl.id
            )
            for i in range(3)
        ]

        constraint = self._make_constraint({"Alpha": cfg})
        result = constraint.validate(assignments, ctx)
        assert result.satisfied is True  # Soft constraints always satisfied
        assert result.penalty == 0.0

    def test_deviation_produces_penalty(self):
        # Target = (2+4)//2 = 3
        cfg = PrimaryDutyConfig(
            duty_id="d1",
            duty_name="Alpha",
            clinic_min_per_week=2,
            clinic_max_per_week=4,
        )
        fac = MockFaculty(primary_duty="Alpha")
        blocks = _make_week_blocks(date(2024, 1, 1))
        tpl = MockTemplate()
        ctx = _make_context([fac], blocks, [tpl])

        # 1 assignment (deviation = 2)
        assignments = [
            MockAssignment(
                person_id=fac.id, block_id=blocks[0].id, rotation_template_id=tpl.id
            )
        ]

        constraint = self._make_constraint({"Alpha": cfg}, weight=10.0)
        result = constraint.validate(assignments, ctx)
        assert result.penalty == 20.0  # deviation=2, weight=10

    def test_zero_target_skipped(self):
        cfg = PrimaryDutyConfig(
            duty_id="d1",
            duty_name="Alpha",
            clinic_min_per_week=0,
            clinic_max_per_week=0,
        )
        fac = MockFaculty(primary_duty="Alpha")
        blocks = _make_week_blocks(date(2024, 1, 1))
        tpl = MockTemplate()
        ctx = _make_context([fac], blocks, [tpl])
        assignments = []

        constraint = self._make_constraint({"Alpha": cfg})
        result = constraint.validate(assignments, ctx)
        assert result.penalty == 0.0


# ---------------------------------------------------------------------------
# Constraint initialization
# ---------------------------------------------------------------------------


class TestConstraintInit:
    def test_clinic_constraint_name(self):
        c = FacultyPrimaryDutyClinicConstraint(duty_configs={})
        assert c.name == "FacultyPrimaryDutyClinic"

    def test_day_availability_constraint_name(self):
        c = FacultyDayAvailabilityConstraint(duty_configs={})
        assert c.name == "FacultyDayAvailability"

    def test_equity_constraint_name(self):
        c = FacultyClinicEquitySoftConstraint(duty_configs={})
        assert c.name == "FacultyClinicEquity"

    def test_equity_custom_weight(self):
        c = FacultyClinicEquitySoftConstraint(weight=25.0, duty_configs={})
        assert c.weight == 25.0

    def test_get_faculty_duty_config_no_primary_duty(self):
        c = FacultyPrimaryDutyClinicConstraint(
            duty_configs={"Alpha": PrimaryDutyConfig(duty_id="d1", duty_name="Alpha")}
        )
        fac = MockFaculty(primary_duty=None)
        assert c.get_faculty_duty_config(fac) is None

    def test_get_faculty_duty_config_found(self):
        cfg = PrimaryDutyConfig(duty_id="d1", duty_name="Alpha")
        c = FacultyPrimaryDutyClinicConstraint(duty_configs={"Alpha": cfg})
        fac = MockFaculty(primary_duty="Alpha")
        assert c.get_faculty_duty_config(fac) is cfg

    def test_get_faculty_duty_config_not_found(self):
        c = FacultyPrimaryDutyClinicConstraint(duty_configs={})
        fac = MockFaculty(primary_duty="NonExistent")
        assert c.get_faculty_duty_config(fac) is None
