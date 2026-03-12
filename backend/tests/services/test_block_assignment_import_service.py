"""Tests for BlockAssignmentImportService pure functions.

Tests the CSV parsing, name anonymization, rotation matching, synonym
normalization, combined rotation lookup, resident matching, academic year
calculation, and rotation suggestion logic -- all without database access.
"""

import uuid
from datetime import datetime
from unittest.mock import patch

import pytest

from app.services.block_assignment_import_service import (
    ROTATION_SYNONYMS,
    BlockAssignmentImportService,
)


@pytest.fixture
def service():
    """Create service with None session (only testing pure methods)."""
    svc = BlockAssignmentImportService.__new__(BlockAssignmentImportService)
    svc.session = None
    svc._rotation_cache = {}
    svc._resident_cache = {}
    svc._resident_pgy_cache = {}
    svc._preview_cache = {}
    return svc


# ============================================================================
# _anonymize_name
# ============================================================================


class TestAnonymizeName:
    """Tests for PERSEC-compliant name anonymization."""

    def test_last_comma_first_format(self, service):
        result = service._anonymize_name("Smith, John")
        assert result == "S****, J***"

    def test_single_name(self, service):
        result = service._anonymize_name("Montgomery")
        assert result == "M*********"

    def test_two_word_name(self, service):
        result = service._anonymize_name("John Smith")
        assert result == "J*** S****"

    def test_empty_string(self, service):
        assert service._anonymize_name("") == "****"

    def test_none_returns_stars(self, service):
        # Method signature accepts str, but let's test empty-like behavior
        assert service._anonymize_name("") == "****"

    def test_single_char_last_first(self, service):
        result = service._anonymize_name("A, B")
        assert result == "A, B"

    def test_preserves_comma_format(self, service):
        result = service._anonymize_name("Washington, George")
        assert ", " in result

    def test_first_char_visible(self, service):
        """First character of each part should be visible."""
        result = service._anonymize_name("Doe, Jane")
        assert result.startswith("D")
        assert "J" in result


# ============================================================================
# _match_rotation
# ============================================================================


class TestMatchRotation:
    """Tests for rotation template matching."""

    def test_direct_match(self, service):
        rot_id = uuid.uuid4()
        service._rotation_cache["CARDIO"] = (rot_id, "Cardiology")
        rid, name, conf = service._match_rotation("CARDIO")
        assert rid == rot_id
        assert name == "Cardiology"
        assert conf == 1.0

    def test_case_insensitive(self, service):
        rot_id = uuid.uuid4()
        service._rotation_cache["DERM"] = (rot_id, "Dermatology")
        rid, name, conf = service._match_rotation("derm")
        assert rid == rot_id
        assert conf == 1.0

    def test_strips_whitespace(self, service):
        rot_id = uuid.uuid4()
        service._rotation_cache["EM"] = (rot_id, "Emergency Medicine")
        rid, name, conf = service._match_rotation("  EM  ")
        assert rid == rot_id

    def test_no_match_returns_none(self, service):
        rid, name, conf = service._match_rotation("NONEXISTENT")
        assert rid is None
        assert name is None
        assert conf == 0.0

    def test_variation_space_to_dash(self, service):
        rot_id = uuid.uuid4()
        service._rotation_cache["NF-PM"] = (rot_id, "Night Float PM")
        rid, name, conf = service._match_rotation("NF PM")
        assert rid == rot_id
        assert conf == 0.9

    def test_variation_dash_to_space(self, service):
        rot_id = uuid.uuid4()
        service._rotation_cache["NF PM"] = (rot_id, "Night Float PM")
        rid, name, conf = service._match_rotation("NF-PM")
        assert rid == rot_id
        assert conf == 0.9

    def test_variation_slash_to_dash(self, service):
        rot_id = uuid.uuid4()
        service._rotation_cache["KAPI-LD"] = (rot_id, "Kapiolani L&D")
        rid, name, conf = service._match_rotation("KAPI/LD")
        assert rid == rot_id
        assert conf == 0.9

    def test_variation_underscore_to_dash(self, service):
        rot_id = uuid.uuid4()
        service._rotation_cache["FM-CLINIC"] = (rot_id, "FM Clinic")
        rid, name, conf = service._match_rotation("FM_CLINIC")
        assert rid == rot_id
        assert conf == 0.9


# ============================================================================
# _normalize_rotation_input
# ============================================================================


class TestNormalizeRotationInput:
    """Tests for rotation input normalization."""

    def test_synonym_mapping(self, service):
        assert service._normalize_rotation_input("SURG-EXP", None) == "SURG"
        assert service._normalize_rotation_input("GYN-CLIN", None) == "GYN"
        assert service._normalize_rotation_input("IM-INT", None) == "IM"

    def test_case_insensitive(self, service):
        assert service._normalize_rotation_input("surg-exp", None) == "SURG"

    def test_strips_whitespace(self, service):
        assert service._normalize_rotation_input("  SURG-EXP  ", None) == "SURG"

    def test_passthrough_unknown(self, service):
        assert service._normalize_rotation_input("CARDIO", None) == "CARDIO"

    def test_fmit_with_explicit_pgy(self, service):
        assert service._normalize_rotation_input("FMIT1", None) == "FMIT-PGY1"
        assert service._normalize_rotation_input("FMIT2", None) == "FMIT-PGY2"
        assert service._normalize_rotation_input("FMIT3", None) == "FMIT-PGY3"

    def test_fmit_with_pgy_from_cache(self, service):
        resident_id = uuid.uuid4()
        service._resident_pgy_cache[resident_id] = 2
        assert service._normalize_rotation_input("FMIT", resident_id) == "FMIT-PGY2"

    def test_fmit_defaults_to_pgy1(self, service):
        """When no PGY info available, defaults to FMIT-PGY1."""
        assert service._normalize_rotation_input("FMIT", None) == "FMIT-PGY1"


# ============================================================================
# _match_combined_rotation
# ============================================================================


class TestMatchCombinedRotation:
    """Tests for combined rotation pair matching."""

    def test_combined_match(self, service):
        rot_id = uuid.uuid4()
        service._rotation_cache["NF-ENDO"] = (rot_id, "Night Float + Endo")
        rid, name, conf = service._match_combined_rotation(
            "NIGHT FLOAT", "ENDOCRINOLOGY"
        )
        assert rid == rot_id
        assert conf == 1.0

    def test_reverse_order_different_template(self, service):
        """Some combined rotations have different templates based on order."""
        nf_plus = uuid.uuid4()
        c_plus_n = uuid.uuid4()
        service._rotation_cache["NF+"] = (nf_plus, "NF+Cardio")
        service._rotation_cache["C+N"] = (c_plus_n, "Cardio+NF")
        rid1, _, _ = service._match_combined_rotation("NIGHT FLOAT", "CARDIOLOGY")
        rid2, _, _ = service._match_combined_rotation("CARDIOLOGY", "NIGHT FLOAT")
        assert rid1 == nf_plus
        assert rid2 == c_plus_n

    def test_empty_primary_returns_none(self, service):
        rid, name, conf = service._match_combined_rotation("", "ENDOCRINOLOGY")
        assert rid is None
        assert conf == 0.0

    def test_empty_secondary_returns_none(self, service):
        rid, name, conf = service._match_combined_rotation("NIGHT FLOAT", "")
        assert rid is None
        assert conf == 0.0

    def test_no_match_returns_none(self, service):
        rid, name, conf = service._match_combined_rotation("UNKNOWN", "ALSO UNKNOWN")
        assert rid is None
        assert conf == 0.0

    def test_abbreviation_match(self, service):
        rot_id = uuid.uuid4()
        service._rotation_cache["NF-ENDO"] = (rot_id, "NF-Endo")
        rid, name, conf = service._match_combined_rotation("NF-PM", "ENDO")
        assert rid == rot_id
        assert conf == 1.0


# ============================================================================
# _match_resident
# ============================================================================


class TestMatchResident:
    """Tests for resident name matching."""

    def test_last_name_match(self, service):
        res_id = uuid.uuid4()
        service._resident_cache["SMITH"] = (res_id, "Smith, John")
        rid, name, conf = service._match_resident("Smith")
        assert rid == res_id
        assert conf == 1.0

    def test_first_name_match(self, service):
        res_id = uuid.uuid4()
        service._resident_cache["JANE"] = (res_id, "Doe, Jane")
        rid, name, conf = service._match_resident("Jane")
        assert rid == res_id

    def test_comma_separated_name(self, service):
        res_id = uuid.uuid4()
        service._resident_cache["DOE"] = (res_id, "Doe, John")
        rid, name, conf = service._match_resident("Doe, John")
        assert rid == res_id

    def test_no_match(self, service):
        rid, name, conf = service._match_resident("Nobody")
        assert rid is None
        assert conf == 0.0

    def test_case_insensitive(self, service):
        res_id = uuid.uuid4()
        service._resident_cache["JONES"] = (res_id, "Jones, Alice")
        rid, name, conf = service._match_resident("jones")
        assert rid == res_id

    def test_strips_whitespace(self, service):
        res_id = uuid.uuid4()
        service._resident_cache["WILSON"] = (res_id, "Wilson, Bob")
        rid, name, conf = service._match_resident("  Wilson  ")
        assert rid == res_id


# ============================================================================
# _calculate_academic_year
# ============================================================================


class TestCalculateAcademicYear:
    """Tests for academic year calculation."""

    @patch("app.services.block_assignment_import_service.datetime")
    def test_july_is_current_year(self, mock_dt, service):
        mock_dt.now.return_value = datetime(2025, 7, 1)
        assert service._calculate_academic_year() == 2025

    @patch("app.services.block_assignment_import_service.datetime")
    def test_december_is_current_year(self, mock_dt, service):
        mock_dt.now.return_value = datetime(2025, 12, 31)
        assert service._calculate_academic_year() == 2025

    @patch("app.services.block_assignment_import_service.datetime")
    def test_january_is_previous_year(self, mock_dt, service):
        mock_dt.now.return_value = datetime(2026, 1, 15)
        assert service._calculate_academic_year() == 2025

    @patch("app.services.block_assignment_import_service.datetime")
    def test_june_is_previous_year(self, mock_dt, service):
        mock_dt.now.return_value = datetime(2026, 6, 30)
        assert service._calculate_academic_year() == 2025


# ============================================================================
# _parse_csv_content
# ============================================================================


class TestParseCsvContent:
    """Tests for CSV content parsing."""

    def test_basic_csv(self, service):
        csv_content = (
            "block_number,rotation_abbrev,resident_name\n1,CARDIO,Smith\n2,DERM,Jones\n"
        )
        rows = service._parse_csv_content(csv_content)
        assert len(rows) == 2
        assert rows[0]["block_number"] == "1"
        assert rows[0]["rotation_abbrev"] == "CARDIO"
        assert rows[0]["resident_name"] == "Smith"

    def test_alternate_headers(self, service):
        csv_content = "block,rotation,name\n3,EM,Wilson\n"
        rows = service._parse_csv_content(csv_content)
        assert len(rows) == 1
        assert rows[0]["block_number"] == "3"
        assert rows[0]["rotation_abbrev"] == "EM"
        assert rows[0]["resident_name"] == "Wilson"

    def test_blk_rot_shorthand(self, service):
        csv_content = "blk,rot,name\n5,PSYCH,Brown\n"
        rows = service._parse_csv_content(csv_content)
        assert len(rows) == 1
        assert rows[0]["block_number"] == "5"
        assert rows[0]["rotation_abbrev"] == "PSYCH"

    def test_comment_lines_ignored(self, service):
        csv_content = (
            "# This is a comment\n"
            "block_number,rotation_abbrev,resident_name\n"
            "# Another comment\n"
            "1,CARDIO,Smith\n"
        )
        rows = service._parse_csv_content(csv_content)
        assert len(rows) == 1

    def test_empty_content(self, service):
        rows = service._parse_csv_content("")
        assert len(rows) == 0

    def test_header_only(self, service):
        rows = service._parse_csv_content(
            "block_number,rotation_abbrev,resident_name\n"
        )
        assert len(rows) == 0

    def test_row_numbers_start_at_two(self, service):
        csv_content = (
            "block_number,rotation_abbrev,resident_name\n1,CARDIO,Smith\n2,DERM,Jones\n"
        )
        rows = service._parse_csv_content(csv_content)
        assert rows[0]["row_number"] == 2
        assert rows[1]["row_number"] == 3

    def test_whitespace_normalized(self, service):
        csv_content = (
            "  block_number , rotation_abbrev , resident_name  \n1,CARDIO,Smith\n"
        )
        rows = service._parse_csv_content(csv_content)
        assert len(rows) == 1
        # Headers are lowercased and stripped
        assert rows[0]["block_number"] == "1"


# ============================================================================
# _suggest_rotation_name
# ============================================================================


class TestSuggestRotationName:
    """Tests for rotation name suggestions."""

    def test_known_abbreviation(self, service):
        assert service._suggest_rotation_name("CARDIO") == "Cardiology"
        assert service._suggest_rotation_name("EM") == "Emergency Medicine"
        assert service._suggest_rotation_name("PSYCH") == "Psychiatry"

    def test_case_insensitive(self, service):
        assert service._suggest_rotation_name("cardio") == "Cardiology"
        assert service._suggest_rotation_name("Derm") == "Dermatology"

    def test_unknown_returns_none(self, service):
        assert service._suggest_rotation_name("XYZZY") is None

    def test_all_known_suggestions(self, service):
        known = [
            "CARDIO",
            "DERM",
            "ELEC",
            "EM",
            "FAC-DEV",
            "GERI",
            "IM",
            "MSK",
            "PEDS",
            "PROC",
            "PSYCH",
        ]
        for abbrev in known:
            assert service._suggest_rotation_name(abbrev) is not None


# ============================================================================
# Constants validation
# ============================================================================


class TestRotationSynonyms:
    """Tests for ROTATION_SYNONYMS constant."""

    def test_not_empty(self):
        assert len(ROTATION_SYNONYMS) > 0

    def test_keys_are_uppercase(self):
        for key in ROTATION_SYNONYMS:
            assert key == key.upper(), f"Synonym key not uppercase: {key}"

    def test_surgical_experience_maps_to_surg(self):
        assert ROTATION_SYNONYMS["SURG-EXP"] == "SURG"
        assert ROTATION_SYNONYMS["SURG EXP"] == "SURG"
        assert ROTATION_SYNONYMS["SURGICAL EXPERIENCE"] == "SURG"

    def test_gyn_synonyms(self):
        assert ROTATION_SYNONYMS["GYN-CLIN"] == "GYN"
        assert ROTATION_SYNONYMS["GYN CLINIC"] == "GYN"
        assert ROTATION_SYNONYMS["GYNECOLOGY CLINIC"] == "GYN"

    def test_kapiolani_synonyms(self):
        for key in ("KAPI-LD", "KAPI L&D", "KAPIOLANI L AND D", "KAPIOLANI L&D"):
            assert ROTATION_SYNONYMS[key] == "KAPI-LD-PGY1"

    def test_internal_medicine_synonyms(self):
        assert ROTATION_SYNONYMS["IM-INT"] == "IM"
        assert ROTATION_SYNONYMS["INTERNAL MEDICINE"] == "IM"
