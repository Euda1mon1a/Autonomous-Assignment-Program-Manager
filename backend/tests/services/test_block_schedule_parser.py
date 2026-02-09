"""Tests for block_schedule_parser.py parsing helpers.

Tests the pure parsing methods without requiring actual XLSX files.
"""

import pytest

from app.services.block_schedule_parser import BlockAssignmentRow, BlockScheduleParser


@pytest.fixture
def parser() -> BlockScheduleParser:
    """Create a fresh parser instance."""
    return BlockScheduleParser()


# ── _parse_pgy_level ────────────────────────────────────────────────────────


class TestParsePgyLevel:
    """Test PGY level parsing from various string formats."""

    def test_pgy_with_space(self, parser):
        assert parser._parse_pgy_level("PGY 1") == 1

    def test_pgy_no_space(self, parser):
        assert parser._parse_pgy_level("PGY3") == 3

    def test_pgy_with_dash(self, parser):
        assert parser._parse_pgy_level("PGY-2") == 2

    def test_lowercase(self, parser):
        assert parser._parse_pgy_level("pgy 1") == 1

    def test_mixed_case(self, parser):
        assert parser._parse_pgy_level("Pgy3") == 3

    def test_none_returns_zero(self, parser):
        assert parser._parse_pgy_level(None) == 0

    def test_empty_string_returns_zero(self, parser):
        assert parser._parse_pgy_level("") == 0

    def test_no_match_returns_zero(self, parser):
        assert parser._parse_pgy_level("Faculty") == 0

    def test_just_number_returns_zero(self, parser):
        """Plain number without PGY prefix doesn't match."""
        assert parser._parse_pgy_level("3") == 0

    def test_pgy_with_extra_text(self, parser):
        assert parser._parse_pgy_level("PGY 2 (Resident)") == 2


# ── _normalize_rotation ─────────────────────────────────────────────────────


class TestNormalizeRotation:
    """Test rotation name normalization and mapping."""

    def test_exact_mapping(self, parser):
        assert parser._normalize_rotation("NF") == "NF-PM"

    def test_case_insensitive_mapping(self, parser):
        assert parser._normalize_rotation("nf") == "NF-PM"

    def test_sports_medicine(self, parser):
        assert parser._normalize_rotation("SM") == "SM-AM"

    def test_long_name_mapping(self, parser):
        assert parser._normalize_rotation("Night Float") == "NF-PM"

    def test_fmit_variant(self, parser):
        assert parser._normalize_rotation("FMIT 2") == "FMIT-R"

    def test_ld_night_float(self, parser):
        assert parser._normalize_rotation("L and D night float") == "LDNF"

    def test_surgical_experience(self, parser):
        assert parser._normalize_rotation("Surg Exp") == "SURG"

    def test_unknown_rotation_passthrough(self, parser):
        """Unknown rotations are returned as-is."""
        assert parser._normalize_rotation("CUSTOM-ROT") == "CUSTOM-ROT"

    def test_none_returns_empty(self, parser):
        assert parser._normalize_rotation(None) == ""

    def test_empty_returns_empty(self, parser):
        assert parser._normalize_rotation("") == ""

    def test_whitespace_stripped(self, parser):
        assert parser._normalize_rotation("  NF  ") == "NF-PM"

    def test_hilo_mapping(self, parser):
        assert parser._normalize_rotation("Hilo") == "HILO"

    def test_fmc_passthrough(self, parser):
        assert parser._normalize_rotation("FMC") == "FMC"

    def test_procedures_mapping(self, parser):
        assert parser._normalize_rotation("Procedures") == "PROC-AM"

    def test_peds_ward(self, parser):
        assert parser._normalize_rotation("Peds Ward") == "PEDS-W"

    def test_kapiolani(self, parser):
        assert parser._normalize_rotation("Kapiolani L and D") == "KAPI-LD-PGY1"


# ── _normalize_name ──────────────────────────────────────────────────────────


class TestNormalizeName:
    """Test person name normalization."""

    def test_plain_name(self, parser):
        assert parser._normalize_name("John Smith") == "John Smith"

    def test_strips_asterisk(self, parser):
        """Asterisk marks chief residents and should be removed."""
        assert parser._normalize_name("Jane Doe*") == "Jane Doe"

    def test_multiple_asterisks(self, parser):
        assert parser._normalize_name("Jane* Doe*") == "Jane Doe"

    def test_leading_trailing_whitespace(self, parser):
        assert parser._normalize_name("  John Smith  ") == "John Smith"

    def test_multiple_spaces_collapsed(self, parser):
        assert parser._normalize_name("John   Smith") == "John Smith"

    def test_none_returns_empty(self, parser):
        assert parser._normalize_name(None) == ""

    def test_empty_returns_empty(self, parser):
        assert parser._normalize_name("") == ""

    def test_asterisk_and_whitespace(self, parser):
        assert parser._normalize_name("  Jane Doe*  ") == "Jane Doe"


# ── _get_cell_value ──────────────────────────────────────────────────────────


class TestGetCellValue:
    """Test safe cell value extraction."""

    def test_string_value(self, parser):
        assert parser._get_cell_value(["hello", "world"], 0) == "hello"

    def test_numeric_value(self, parser):
        assert parser._get_cell_value([42, "world"], 0) == "42"

    def test_none_value(self, parser):
        assert parser._get_cell_value([None, "world"], 0) is None

    def test_index_out_of_range(self, parser):
        assert parser._get_cell_value(["hello"], 5) is None

    def test_strips_whitespace(self, parser):
        assert parser._get_cell_value(["  hello  "], 0) == "hello"

    def test_empty_list(self, parser):
        assert parser._get_cell_value([], 0) is None


# ── BlockAssignmentRow ──────────────────────────────────────────────────────


class TestBlockAssignmentRow:
    """Test the dataclass and its to_dict method."""

    def test_to_dict(self):
        row = BlockAssignmentRow(
            rotation_template="NF-PM",
            secondary_rotation="FMC",
            person_name="John Smith",
            pgy_level=2,
            block_number=5,
            role="R2",
        )
        d = row.to_dict()
        assert d == {
            "rotation": "NF-PM",
            "secondary_rotation": "FMC",
            "name": "John Smith",
            "pgy_level": 2,
            "block": 5,
            "role": "R2",
        }

    def test_to_dict_no_secondary(self):
        row = BlockAssignmentRow(
            rotation_template="IM",
            secondary_rotation=None,
            person_name="Jane Doe",
            pgy_level=1,
            block_number=1,
            role="R1",
        )
        d = row.to_dict()
        assert d["secondary_rotation"] is None

    def test_to_dict_has_required_keys(self):
        row = BlockAssignmentRow(
            rotation_template="FMC",
            secondary_rotation=None,
            person_name="Test",
            pgy_level=3,
            block_number=10,
            role="R3",
        )
        d = row.to_dict()
        assert set(d.keys()) == {
            "rotation",
            "secondary_rotation",
            "name",
            "pgy_level",
            "block",
            "role",
        }


# ── ROTATION_MAPPINGS coverage ──────────────────────────────────────────────


class TestRotationMappingsCompleteness:
    """Verify key rotation families have complete mappings."""

    def test_night_float_variants(self, parser):
        """All NF variants should map to NF-PM."""
        for name in ["NF", "Night Float"]:
            assert parser._normalize_rotation(name) == "NF-PM"

    def test_ld_night_float_variants(self, parser):
        """All L&D NF variants should map to LDNF."""
        for name in ["L and D night float", "L and D NF", "L&D Night Float", "L&D NF"]:
            assert parser._normalize_rotation(name) == "LDNF"

    def test_fmit_variants(self, parser):
        """All FMIT variants should map to FMIT-R."""
        for name in ["FMIT 2", "FMIT 1", "FMIT", "FMIT-R"]:
            assert parser._normalize_rotation(name) == "FMIT-R"

    def test_surgical_variants(self, parser):
        for name in ["Surg Exp", "Surgical Experience", "SURG-EXP"]:
            assert parser._normalize_rotation(name) == "SURG"

    def test_gyn_variants(self, parser):
        for name in ["Gyn Clinic", "GYN Clinic", "Gynecology Clinic", "GYN-CLIN"]:
            assert parser._normalize_rotation(name) == "GYN"

    def test_peds_variants(self, parser):
        assert parser._normalize_rotation("Peds Ward") == "PEDS-W"
        assert parser._normalize_rotation("Pediatrics Ward") == "PEDS-W"
        assert parser._normalize_rotation("Peds NF") == "PNF"
        assert parser._normalize_rotation("Pediatrics Night Float") == "PNF"
