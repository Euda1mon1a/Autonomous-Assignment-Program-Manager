"""Tests for half_day_json_exporter.py - JSON export from half_day_assignments.

These tests use mocking to avoid JSONB/SQLite compatibility issues.
"""

import json
from datetime import date
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from app.services.half_day_json_exporter import (
    HalfDayJSONExporter,
    export_block_schedule_json,
)


def create_mock_assignment(
    person_id: str,
    assign_date: date,
    time_of_day: str,
    activity_code: str = "C",
) -> MagicMock:
    """Create a mock HalfDayAssignment."""
    assignment = MagicMock()
    assignment.person_id = person_id
    assignment.date = assign_date
    assignment.time_of_day = time_of_day
    assignment.activity = MagicMock()
    assignment.activity.display_abbreviation = activity_code
    assignment.activity.code = activity_code
    return assignment


class TestHalfDayJSONExporterExport:
    """Tests for HalfDayJSONExporter.export() method."""

    def test_export_returns_dict(self):
        """export() should return a dict."""
        mock_db = MagicMock()
        exporter = HalfDayJSONExporter(mock_db)

        # Mock the internal methods
        exporter._fetch_assignments = MagicMock(return_value=[])
        exporter._fetch_people = MagicMock(return_value={})
        exporter._fetch_rotations = MagicMock(return_value={})

        result = exporter.export(
            block_start=date(2026, 3, 12),
            block_end=date(2026, 4, 8),
        )
        assert isinstance(result, dict)

    def test_export_has_required_keys(self):
        """export() should return dict with required keys."""
        mock_db = MagicMock()
        exporter = HalfDayJSONExporter(mock_db)

        exporter._fetch_assignments = MagicMock(return_value=[])
        exporter._fetch_people = MagicMock(return_value={})
        exporter._fetch_rotations = MagicMock(return_value={})

        result = exporter.export(
            block_start=date(2026, 3, 12),
            block_end=date(2026, 4, 8),
        )

        assert "block_start" in result
        assert "block_end" in result
        assert "source" in result
        assert "residents" in result
        assert "faculty" in result

    def test_export_dates_iso_format(self):
        """Dates should be in ISO format."""
        mock_db = MagicMock()
        exporter = HalfDayJSONExporter(mock_db)

        exporter._fetch_assignments = MagicMock(return_value=[])
        exporter._fetch_people = MagicMock(return_value={})
        exporter._fetch_rotations = MagicMock(return_value={})

        result = exporter.export(
            block_start=date(2026, 3, 12),
            block_end=date(2026, 4, 8),
        )

        assert result["block_start"] == "2026-03-12"
        assert result["block_end"] == "2026-04-08"

    def test_export_source_is_half_day_assignments(self):
        """Source should be 'half_day_assignments'."""
        mock_db = MagicMock()
        exporter = HalfDayJSONExporter(mock_db)

        exporter._fetch_assignments = MagicMock(return_value=[])
        exporter._fetch_people = MagicMock(return_value={})
        exporter._fetch_rotations = MagicMock(return_value={})

        result = exporter.export(
            block_start=date(2026, 3, 12),
            block_end=date(2026, 4, 8),
        )

        assert result["source"] == "half_day_assignments"

    def test_export_empty_when_no_assignments(self):
        """Empty residents/faculty lists when no data."""
        mock_db = MagicMock()
        exporter = HalfDayJSONExporter(mock_db)

        exporter._fetch_assignments = MagicMock(return_value=[])
        exporter._fetch_people = MagicMock(return_value={})
        exporter._fetch_rotations = MagicMock(return_value={})

        result = exporter.export(
            block_start=date(2026, 3, 12),
            block_end=date(2026, 4, 8),
        )

        assert result["residents"] == []
        assert result["faculty"] == []

    def test_export_includes_resident(self):
        """Resident with assignment appears in residents list."""
        mock_db = MagicMock()
        exporter = HalfDayJSONExporter(mock_db)

        person_id = uuid4()
        assignment = create_mock_assignment(
            person_id=person_id,
            assign_date=date(2026, 3, 12),
            time_of_day="AM",
            activity_code="C",
        )

        exporter._fetch_assignments = MagicMock(return_value=[assignment])
        exporter._fetch_people = MagicMock(
            return_value={
                person_id: {"name": "Test Resident", "type": "resident", "pgy": 2}
            }
        )
        exporter._fetch_rotations = MagicMock(
            return_value={person_id: {"rotation1": "FMIT", "rotation2": ""}}
        )
        exporter._get_activity_code = MagicMock(return_value="C")

        result = exporter.export(
            block_start=date(2026, 3, 12),
            block_end=date(2026, 3, 12),
        )

        assert len(result["residents"]) == 1
        assert result["residents"][0]["name"] == "Test Resident"

    def test_export_faculty_excluded_by_default(self):
        """Faculty not included when include_faculty=False (default)."""
        mock_db = MagicMock()
        exporter = HalfDayJSONExporter(mock_db)

        # _fetch_assignments is called with include_faculty=False, which should
        # not return faculty assignments
        exporter._fetch_assignments = MagicMock(return_value=[])
        exporter._fetch_people = MagicMock(return_value={})
        exporter._fetch_rotations = MagicMock(return_value={})

        result = exporter.export(
            block_start=date(2026, 3, 12),
            block_end=date(2026, 3, 12),
            include_faculty=False,
        )

        assert result["faculty"] == []

    def test_export_faculty_in_faculty_list(self):
        """Faculty appears in faculty list, not residents list."""
        mock_db = MagicMock()
        exporter = HalfDayJSONExporter(mock_db)

        person_id = uuid4()
        assignment = create_mock_assignment(
            person_id=person_id,
            assign_date=date(2026, 3, 12),
            time_of_day="AM",
            activity_code="AT",
        )

        exporter._fetch_assignments = MagicMock(return_value=[assignment])
        exporter._fetch_people = MagicMock(
            return_value={
                person_id: {"name": "Test Faculty", "type": "faculty", "pgy": None}
            }
        )
        exporter._fetch_rotations = MagicMock(
            return_value={person_id: {"rotation1": "", "rotation2": ""}}
        )
        exporter._get_activity_code = MagicMock(return_value="AT")

        result = exporter.export(
            block_start=date(2026, 3, 12),
            block_end=date(2026, 3, 12),
            include_faculty=True,
        )

        assert len(result["faculty"]) == 1
        assert result["faculty"][0]["name"] == "Test Faculty"
        assert result["residents"] == []

    def test_export_no_call_by_default(self):
        """Call data not included by default."""
        mock_db = MagicMock()
        exporter = HalfDayJSONExporter(mock_db)

        exporter._fetch_assignments = MagicMock(return_value=[])
        exporter._fetch_people = MagicMock(return_value={})
        exporter._fetch_rotations = MagicMock(return_value={})

        result = exporter.export(
            block_start=date(2026, 3, 12),
            block_end=date(2026, 4, 8),
        )

        assert "call" not in result

    def test_export_call_when_flag_set(self):
        """Call data included when include_call=True."""
        mock_db = MagicMock()
        exporter = HalfDayJSONExporter(mock_db)

        exporter._fetch_assignments = MagicMock(return_value=[])
        exporter._fetch_people = MagicMock(return_value={})
        exporter._fetch_rotations = MagicMock(return_value={})
        exporter._fetch_call_assignments = MagicMock(
            return_value=[{"date": date(2026, 3, 12), "staff": "Smith"}]
        )

        result = exporter.export(
            block_start=date(2026, 3, 12),
            block_end=date(2026, 4, 8),
            include_call=True,
        )

        assert "call" in result
        assert "nights" in result["call"]
        assert len(result["call"]["nights"]) == 1


class TestHalfDayJSONExporterExportJson:
    """Tests for HalfDayJSONExporter.export_json() method."""

    def test_export_json_returns_string(self):
        """export_json() should return a string."""
        mock_db = MagicMock()
        exporter = HalfDayJSONExporter(mock_db)

        exporter._fetch_assignments = MagicMock(return_value=[])
        exporter._fetch_people = MagicMock(return_value={})
        exporter._fetch_rotations = MagicMock(return_value={})

        result = exporter.export_json(
            block_start=date(2026, 3, 12),
            block_end=date(2026, 4, 8),
        )
        assert isinstance(result, str)

    def test_export_json_is_valid_json(self):
        """export_json() should return valid JSON."""
        mock_db = MagicMock()
        exporter = HalfDayJSONExporter(mock_db)

        exporter._fetch_assignments = MagicMock(return_value=[])
        exporter._fetch_people = MagicMock(return_value={})
        exporter._fetch_rotations = MagicMock(return_value={})

        result = exporter.export_json(
            block_start=date(2026, 3, 12),
            block_end=date(2026, 4, 8),
        )

        # Should not raise
        parsed = json.loads(result)
        assert isinstance(parsed, dict)

    def test_export_json_pretty_format(self):
        """export_json(pretty=True) should have indentation."""
        mock_db = MagicMock()
        exporter = HalfDayJSONExporter(mock_db)

        exporter._fetch_assignments = MagicMock(return_value=[])
        exporter._fetch_people = MagicMock(return_value={})
        exporter._fetch_rotations = MagicMock(return_value={})

        result = exporter.export_json(
            block_start=date(2026, 3, 12),
            block_end=date(2026, 4, 8),
            pretty=True,
        )

        # Pretty JSON has newlines and indentation
        assert "\n" in result
        assert "  " in result  # 2-space indentation

    def test_export_json_compact_format(self):
        """export_json(pretty=False) should be compact."""
        mock_db = MagicMock()
        exporter = HalfDayJSONExporter(mock_db)

        exporter._fetch_assignments = MagicMock(return_value=[])
        exporter._fetch_people = MagicMock(return_value={})
        exporter._fetch_rotations = MagicMock(return_value={})

        result = exporter.export_json(
            block_start=date(2026, 3, 12),
            block_end=date(2026, 4, 8),
            pretty=False,
        )

        # Compact JSON has no newlines
        lines = [l for l in result.split("\n") if l.strip()]
        assert len(lines) == 1


class TestExportBlockScheduleJson:
    """Tests for export_block_schedule_json convenience function."""

    @patch("app.utils.academic_blocks.get_block_dates")
    def test_returns_dict(self, mock_get_block_dates):
        """Should return a dict."""
        mock_db = MagicMock()

        # Mock block dates
        mock_block_dates = MagicMock()
        mock_block_dates.start_date = date(2026, 3, 12)
        mock_block_dates.end_date = date(2026, 4, 8)
        mock_get_block_dates.return_value = mock_block_dates

        # Mock exporter's internal methods via patching
        with (
            patch.object(HalfDayJSONExporter, "_fetch_assignments", return_value=[]),
            patch.object(HalfDayJSONExporter, "_fetch_people", return_value={}),
            patch.object(HalfDayJSONExporter, "_fetch_rotations", return_value={}),
        ):
            result = export_block_schedule_json(
                db=mock_db,
                block_number=10,
                academic_year=2025,
            )

        assert isinstance(result, dict)
        mock_get_block_dates.assert_called_once_with(10, 2025)

    @patch("app.utils.academic_blocks.get_block_dates")
    def test_passes_flags_to_exporter(self, mock_get_block_dates):
        """Should pass include_faculty and include_call to exporter."""
        mock_db = MagicMock()

        mock_block_dates = MagicMock()
        mock_block_dates.start_date = date(2026, 3, 12)
        mock_block_dates.end_date = date(2026, 4, 8)
        mock_get_block_dates.return_value = mock_block_dates

        # Use a spy to verify the export call
        with (
            patch.object(HalfDayJSONExporter, "_fetch_assignments", return_value=[]),
            patch.object(HalfDayJSONExporter, "_fetch_people", return_value={}),
            patch.object(HalfDayJSONExporter, "_fetch_rotations", return_value={}),
            patch.object(
                HalfDayJSONExporter, "_fetch_call_assignments", return_value=[]
            ),
        ):
            result = export_block_schedule_json(
                db=mock_db,
                block_number=10,
                academic_year=2025,
                include_faculty=True,
                include_call=True,
            )

        # Verify call data is present (meaning include_call was passed)
        assert "call" in result


class TestBuildPerson:
    """Tests for _build_person internal method."""

    def test_person_has_required_keys(self):
        """Person payload should have required keys."""
        mock_db = MagicMock()
        exporter = HalfDayJSONExporter(mock_db)

        # Mock _get_activity_code
        exporter._get_activity_code = MagicMock(return_value="C")

        person_info = {"name": "Test Resident", "pgy": 2}
        rotation_info = {"rotation1": "FMIT", "rotation2": ""}
        assignments = []

        result = exporter._build_person(
            person_info,
            rotation_info,
            assignments,
            block_start=date(2026, 3, 12),
            block_end=date(2026, 3, 12),
        )

        assert "name" in result
        assert "pgy" in result
        assert "rotation1" in result
        assert "rotation2" in result
        assert "days" in result

    def test_day_has_required_keys(self):
        """Day payload should have required keys."""
        mock_db = MagicMock()
        exporter = HalfDayJSONExporter(mock_db)

        exporter._get_activity_code = MagicMock(return_value="C")

        person_info = {"name": "Test Resident", "pgy": 2}
        rotation_info = {"rotation1": "FMIT", "rotation2": ""}
        assignments = []

        result = exporter._build_person(
            person_info,
            rotation_info,
            assignments,
            block_start=date(2026, 3, 12),
            block_end=date(2026, 3, 12),
        )

        assert len(result["days"]) == 1
        day = result["days"][0]
        assert "date" in day
        assert "weekday" in day
        assert "am" in day
        assert "pm" in day

    def test_day_date_is_iso_format(self):
        """Day date should be ISO format."""
        mock_db = MagicMock()
        exporter = HalfDayJSONExporter(mock_db)

        exporter._get_activity_code = MagicMock(return_value="C")

        person_info = {"name": "Test Resident", "pgy": 2}
        rotation_info = {"rotation1": "FMIT", "rotation2": ""}
        assignments = []

        result = exporter._build_person(
            person_info,
            rotation_info,
            assignments,
            block_start=date(2026, 3, 12),
            block_end=date(2026, 3, 12),
        )

        assert result["days"][0]["date"] == "2026-03-12"

    def test_days_cover_full_range(self):
        """Days should cover all dates from start to end."""
        mock_db = MagicMock()
        exporter = HalfDayJSONExporter(mock_db)

        exporter._get_activity_code = MagicMock(return_value="C")

        person_info = {"name": "Test Resident", "pgy": 2}
        rotation_info = {"rotation1": "FMIT", "rotation2": ""}
        assignments = []

        result = exporter._build_person(
            person_info,
            rotation_info,
            assignments,
            block_start=date(2026, 3, 12),
            block_end=date(2026, 3, 14),  # 3 days
        )

        assert len(result["days"]) == 3
        assert result["days"][0]["date"] == "2026-03-12"
        assert result["days"][1]["date"] == "2026-03-13"
        assert result["days"][2]["date"] == "2026-03-14"
