"""Tests for block import schemas (Field bounds, defaults, nested models)."""

import pytest
from pydantic import ValidationError

from app.schemas.block_import import (
    ResidentRosterItem,
    ParsedFMITWeekSchema,
    ParsedBlockAssignmentSchema,
    BlockParseResponse,
)


class TestResidentRosterItem:
    def test_valid(self):
        r = ResidentRosterItem(
            name="Smith, Jane",
            template="R2",
            role="PGY 2",
            row=10,
        )
        assert r.confidence == 1.0

    def test_custom_confidence(self):
        r = ResidentRosterItem(
            name="Jones, Bob",
            template="R1",
            role="PGY 1",
            row=15,
            confidence=0.85,
        )
        assert r.confidence == 0.85

    # --- confidence ge=0.0, le=1.0 ---

    def test_confidence_boundaries(self):
        r = ResidentRosterItem(
            name="A", template="R1", role="PGY 1", row=1, confidence=0.0
        )
        assert r.confidence == 0.0
        r = ResidentRosterItem(
            name="A", template="R1", role="PGY 1", row=1, confidence=1.0
        )
        assert r.confidence == 1.0

    def test_confidence_negative(self):
        with pytest.raises(ValidationError):
            ResidentRosterItem(
                name="A", template="R1", role="PGY 1", row=1, confidence=-0.1
            )

    def test_confidence_above_one(self):
        with pytest.raises(ValidationError):
            ResidentRosterItem(
                name="A", template="R1", role="PGY 1", row=1, confidence=1.1
            )


class TestParsedFMITWeekSchema:
    def test_valid_minimal(self):
        r = ParsedFMITWeekSchema(block_number=10, week_number=1)
        assert r.start_date is None
        assert r.end_date is None
        assert r.faculty_name == ""
        assert r.is_holiday_call is False

    def test_full(self):
        r = ParsedFMITWeekSchema(
            block_number=10,
            week_number=2,
            start_date="2026-03-12",
            end_date="2026-03-18",
            faculty_name="Dr. Chu",
            is_holiday_call=True,
        )
        assert r.faculty_name == "Dr. Chu"
        assert r.is_holiday_call is True


class TestParsedBlockAssignmentSchema:
    def test_valid_minimal(self):
        r = ParsedBlockAssignmentSchema(
            person_name="Smith, Jane",
            date="2026-03-12",
            template="R2",
            role="PGY 2",
        )
        assert r.slot_am is None
        assert r.slot_pm is None
        assert r.row_idx == 0
        assert r.confidence == 1.0

    def test_full(self):
        r = ParsedBlockAssignmentSchema(
            person_name="Jones, Bob",
            date="2026-03-12",
            template="R1",
            role="PGY 1",
            slot_am="FM Clinic",
            slot_pm="ICU",
            row_idx=15,
            confidence=0.9,
        )
        assert r.slot_am == "FM Clinic"
        assert r.slot_pm == "ICU"
        assert r.row_idx == 15


class TestBlockParseResponse:
    def test_valid_minimal(self):
        r = BlockParseResponse(success=True, block_number=10)
        assert r.start_date is None
        assert r.end_date is None
        assert r.residents == []
        assert r.residents_by_template == {}
        assert r.fmit_schedule == []
        assert r.assignments == []
        assert r.warnings == []
        assert r.errors == []
        assert r.total_residents == 0
        assert r.total_assignments == 0

    def test_with_data(self):
        resident = ResidentRosterItem(
            name="Smith, Jane", template="R2", role="PGY 2", row=10
        )
        fmit = ParsedFMITWeekSchema(block_number=10, week_number=1, faculty_name="Chu")
        assignment = ParsedBlockAssignmentSchema(
            person_name="Smith, Jane",
            date="2026-03-12",
            template="R2",
            role="PGY 2",
            slot_am="FM Clinic",
        )
        r = BlockParseResponse(
            success=True,
            block_number=10,
            start_date="2026-03-12",
            end_date="2026-04-08",
            residents=[resident],
            residents_by_template={"R2": [resident]},
            fmit_schedule=[fmit],
            assignments=[assignment],
            warnings=["Low confidence match"],
            total_residents=1,
            total_assignments=1,
        )
        assert len(r.residents) == 1
        assert "R2" in r.residents_by_template
        assert len(r.fmit_schedule) == 1
        assert len(r.assignments) == 1
        assert len(r.warnings) == 1

    def test_failure(self):
        r = BlockParseResponse(
            success=False,
            block_number=10,
            errors=["Failed to parse header row"],
        )
        assert r.success is False
        assert len(r.errors) == 1
