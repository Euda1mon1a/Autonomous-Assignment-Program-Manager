"""Tests for template_filler.py helper functions.

Tests the pure/static helper methods without requiring actual XLSX templates.
"""

from datetime import date

import pytest

from app.services.template_filler import TemplateFiller


# ── _last_name ──────────────────────────────────────────────────────────────


class TestLastName:
    """Test last name extraction from full names."""

    def test_first_last(self):
        assert TemplateFiller._last_name("John Smith") == "smith"

    def test_single_name(self):
        assert TemplateFiller._last_name("Madonna") == "madonna"

    def test_three_parts(self):
        """Last token of multi-part name."""
        assert TemplateFiller._last_name("Mary Jane Watson") == "watson"

    def test_empty_string(self):
        assert TemplateFiller._last_name("") == ""

    def test_already_lowercase(self):
        assert TemplateFiller._last_name("john smith") == "smith"

    def test_mixed_case(self):
        assert TemplateFiller._last_name("McDonald O'Brien") == "o'brien"


# ── _build_absence_lookup ──────────────────────────────────────────────────


class TestBuildAbsenceLookup:
    """Test absence lookup table construction."""

    def test_single_day_absence(self):
        absences = [
            {
                "name": "John Smith",
                "type": "leave",
                "start": "2026-01-05",
                "end": "2026-01-05",
            }
        ]
        lookup = TemplateFiller._build_absence_lookup(absences)
        assert lookup[("smith", date(2026, 1, 5))] == "leave"

    def test_multi_day_absence(self):
        absences = [
            {
                "name": "Jane Doe",
                "type": "TDY",
                "start": "2026-01-10",
                "end": "2026-01-12",
            }
        ]
        lookup = TemplateFiller._build_absence_lookup(absences)
        assert lookup[("doe", date(2026, 1, 10))] == "TDY"
        assert lookup[("doe", date(2026, 1, 11))] == "TDY"
        assert lookup[("doe", date(2026, 1, 12))] == "TDY"
        assert ("doe", date(2026, 1, 13)) not in lookup

    def test_empty_absences(self):
        lookup = TemplateFiller._build_absence_lookup([])
        assert lookup == {}

    def test_missing_date_keys(self):
        """Absence with missing start/end is skipped."""
        absences = [{"name": "John Smith", "type": "leave"}]
        lookup = TemplateFiller._build_absence_lookup(absences)
        assert lookup == {}

    def test_invalid_date_skipped(self):
        absences = [
            {
                "name": "John Smith",
                "type": "leave",
                "start": "bad-date",
                "end": "2026-01-05",
            }
        ]
        lookup = TemplateFiller._build_absence_lookup(absences)
        assert lookup == {}

    def test_missing_type_defaults_empty(self):
        absences = [{"name": "John Smith", "start": "2026-01-05", "end": "2026-01-05"}]
        lookup = TemplateFiller._build_absence_lookup(absences)
        assert lookup[("smith", date(2026, 1, 5))] == ""

    def test_single_name_person(self):
        absences = [
            {
                "name": "Cher",
                "type": "leave",
                "start": "2026-01-05",
                "end": "2026-01-05",
            }
        ]
        lookup = TemplateFiller._build_absence_lookup(absences)
        assert lookup[("cher", date(2026, 1, 5))] == "leave"

    def test_multiple_absences_same_person(self):
        absences = [
            {
                "name": "John Smith",
                "type": "leave",
                "start": "2026-01-05",
                "end": "2026-01-05",
            },
            {
                "name": "John Smith",
                "type": "TDY",
                "start": "2026-01-10",
                "end": "2026-01-10",
            },
        ]
        lookup = TemplateFiller._build_absence_lookup(absences)
        assert lookup[("smith", date(2026, 1, 5))] == "leave"
        assert lookup[("smith", date(2026, 1, 10))] == "TDY"

    def test_overlapping_absences_last_wins(self):
        """When two absences overlap, the last one in the list wins."""
        absences = [
            {
                "name": "John Smith",
                "type": "leave",
                "start": "2026-01-05",
                "end": "2026-01-07",
            },
            {
                "name": "John Smith",
                "type": "TDY",
                "start": "2026-01-06",
                "end": "2026-01-08",
            },
        ]
        lookup = TemplateFiller._build_absence_lookup(absences)
        assert lookup[("smith", date(2026, 1, 5))] == "leave"
        assert lookup[("smith", date(2026, 1, 6))] == "TDY"  # overwritten
        assert lookup[("smith", date(2026, 1, 7))] == "TDY"  # overwritten
        assert lookup[("smith", date(2026, 1, 8))] == "TDY"


# ── _resolve_row ────────────────────────────────────────────────────────────


class TestResolveRow:
    """Test row resolution from name maps."""

    @pytest.fixture
    def filler(self, tmp_path):
        """Create a TemplateFiller with dummy paths (helpers don't use them)."""
        return TemplateFiller(
            template_path=tmp_path / "dummy.xlsx",
            structure_xml_path=tmp_path / "dummy.xml",
        )

    @pytest.fixture
    def name_map(self):
        return {
            "John Smith": 10,
            "Jane Doe": 11,
            "Cameron Williams": 12,
            "Katherine Brown": 13,
        }

    def test_exact_match(self, filler, name_map):
        assert filler._resolve_row("John Smith", name_map) == 10

    def test_last_name_fallback(self, filler, name_map):
        """Nickname resolves via last name match."""
        assert filler._resolve_row("Cam Williams", name_map) == 12

    def test_case_insensitive_last(self, filler, name_map):
        assert filler._resolve_row("JOHN SMITH", name_map) == 10

    def test_unknown_name_returns_none(self, filler, name_map):
        assert filler._resolve_row("Unknown Person", name_map) is None

    def test_empty_name_map(self, filler):
        assert filler._resolve_row("John Smith", {}) is None

    def test_single_name_match(self, filler):
        name_map = {"Madonna": 20}
        assert filler._resolve_row("Madonna", name_map) == 20

    def test_single_name_no_match(self, filler):
        name_map = {"Madonna": 20}
        assert filler._resolve_row("Cher", name_map) is None
