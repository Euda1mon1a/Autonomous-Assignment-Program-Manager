"""Tests for XMLToXlsxConverter pure/helper methods.

Tests the pure functions that don't require database access, template files,
or complex XML parsing. The converter is instantiated with apply_colors=False
to avoid requiring the TAMC color scheme XML.
"""

from collections import Counter
from datetime import date, datetime

import pytest

from app.services.xml_to_xlsx_converter import XMLToXlsxConverter


@pytest.fixture
def converter():
    """Create a minimal converter without template or color scheme."""
    return XMLToXlsxConverter(
        apply_colors=False,
        use_block_template2=False,
        include_qa_sheet=False,
    )


# ============================================================================
# _normalize_code
# ============================================================================


class TestNormalizeCode:
    """Tests for schedule code normalization."""

    def test_normal_string(self, converter):
        assert converter._normalize_code("fmit") == "FMIT"

    def test_uppercase_passthrough(self, converter):
        assert converter._normalize_code("NF") == "NF"

    def test_strips_whitespace(self, converter):
        assert converter._normalize_code("  C  ") == "C"

    def test_none_returns_empty(self, converter):
        assert converter._normalize_code(None) == ""

    def test_integer_coerced(self, converter):
        assert converter._normalize_code(42) == "42"

    def test_empty_string(self, converter):
        assert converter._normalize_code("") == ""

    def test_mixed_case(self, converter):
        assert converter._normalize_code("PedsNF") == "PEDSNF"


# ============================================================================
# _coerce_date
# ============================================================================


class TestCoerceDate:
    """Tests for date coercion from various input types."""

    def test_date_passthrough(self, converter):
        d = date(2024, 3, 15)
        assert converter._coerce_date(d) == d

    def test_datetime_to_date(self, converter):
        dt = datetime(2024, 3, 15, 10, 30, 0)
        assert converter._coerce_date(dt) == date(2024, 3, 15)

    def test_iso_string(self, converter):
        assert converter._coerce_date("2024-03-15") == date(2024, 3, 15)

    def test_none_returns_none(self, converter):
        assert converter._coerce_date(None) is None

    def test_empty_string_returns_none(self, converter):
        assert converter._coerce_date("") is None

    def test_invalid_string_raises(self, converter):
        with pytest.raises(ValueError):
            converter._coerce_date("not-a-date")


# ============================================================================
# _to_last_first
# ============================================================================


class TestToLastFirst:
    """Tests for name format conversion: 'First Last' -> 'Last, First'."""

    def test_two_part_name(self, converter):
        assert converter._to_last_first("John Smith") == "Smith, John"

    def test_three_part_name(self, converter):
        assert converter._to_last_first("John David Smith") == "Smith, John David"

    def test_already_last_first(self, converter):
        """Names with comma are returned as-is."""
        assert converter._to_last_first("Smith, John") == "Smith, John"

    def test_single_name(self, converter):
        assert converter._to_last_first("Madonna") == "Madonna"

    def test_empty_string(self, converter):
        assert converter._to_last_first("") == ""

    def test_whitespace_trimmed(self, converter):
        assert converter._to_last_first("  John  Smith  ") == "Smith, John"


# ============================================================================
# _get_role
# ============================================================================


class TestGetRole:
    """Tests for role string generation."""

    def test_faculty(self, converter):
        assert converter._get_role("3", is_faculty=True) == "FAC"

    def test_pgy_1(self, converter):
        assert converter._get_role("1", is_faculty=False) == "PGY 1"

    def test_pgy_2(self, converter):
        assert converter._get_role("2", is_faculty=False) == "PGY 2"

    def test_pgy_3(self, converter):
        assert converter._get_role("3", is_faculty=False) == "PGY 3"

    def test_no_pgy_no_faculty(self, converter):
        assert converter._get_role("", is_faculty=False) == ""

    def test_faculty_overrides_pgy(self, converter):
        """Faculty flag takes priority over PGY level."""
        assert converter._get_role("1", is_faculty=True) == "FAC"


# ============================================================================
# _call_last_name_token
# ============================================================================


class TestCallLastNameToken:
    """Tests for extracting last name from various name formats."""

    def test_first_last(self, converter):
        assert converter._call_last_name_token("John Smith") == "SMITH"

    def test_last_comma_first(self, converter):
        assert converter._call_last_name_token("Smith, John") == "SMITH"

    def test_with_asterisk(self, converter):
        """Asterisks (marking special status) are stripped."""
        assert converter._call_last_name_token("John Smith*") == "SMITH"

    def test_none_returns_empty(self, converter):
        assert converter._call_last_name_token(None) == ""

    def test_empty_returns_empty(self, converter):
        assert converter._call_last_name_token("") == ""

    def test_single_name(self, converter):
        assert converter._call_last_name_token("Madonna") == "MADONNA"

    def test_whitespace_only(self, converter):
        assert converter._call_last_name_token("   ") == ""

    def test_asterisk_only(self, converter):
        assert converter._call_last_name_token("*") == ""

    def test_three_part_name(self, converter):
        assert converter._call_last_name_token("John David Smith") == "SMITH"

    def test_multi_word_last_name_comma_format(self, converter):
        """'De La Cruz, Maria' -> 'DE LA CRUZ'."""
        assert converter._call_last_name_token("De La Cruz, Maria") == "DE LA CRUZ"


# ============================================================================
# _collect_people_code_counts
# ============================================================================


class TestCollectPeopleCodeCounts:
    """Tests for aggregating activity codes per person."""

    def test_single_person_single_day(self, converter):
        people = [
            {
                "name": "John Smith",
                "days": [{"am": "C", "pm": "LEC"}],
            }
        ]
        result = converter._collect_people_code_counts(people)
        assert len(result) == 1
        assert result[0][0] == "John Smith"
        assert result[0][1] == Counter({"C": 1, "LEC": 1})

    def test_multiple_days(self, converter):
        people = [
            {
                "name": "Jane Doe",
                "days": [
                    {"am": "C", "pm": "C"},
                    {"am": "NF", "pm": "OFF"},
                ],
            }
        ]
        result = converter._collect_people_code_counts(people)
        assert result[0][1] == Counter({"C": 2, "NF": 1, "OFF": 1})

    def test_codes_uppercased(self, converter):
        people = [
            {
                "name": "Test",
                "days": [{"am": "fmit", "pm": "nf"}],
            }
        ]
        result = converter._collect_people_code_counts(people)
        assert result[0][1] == Counter({"FMIT": 1, "NF": 1})

    def test_empty_codes_skipped(self, converter):
        people = [
            {
                "name": "Test",
                "days": [{"am": "", "pm": None}],
            }
        ]
        result = converter._collect_people_code_counts(people)
        assert result[0][1] == Counter()

    def test_sorted_by_name(self, converter):
        people = [
            {"name": "Charlie", "days": []},
            {"name": "Alice", "days": []},
            {"name": "Bob", "days": []},
        ]
        result = converter._collect_people_code_counts(people)
        names = [r[0] for r in result]
        assert names == ["Alice", "Bob", "Charlie"]

    def test_empty_name_skipped(self, converter):
        people = [
            {"name": "", "days": [{"am": "C", "pm": "C"}]},
            {"name": "Valid", "days": []},
        ]
        result = converter._collect_people_code_counts(people)
        assert len(result) == 1
        assert result[0][0] == "Valid"

    def test_none_name_skipped(self, converter):
        people = [{"name": None, "days": []}]
        result = converter._collect_people_code_counts(people)
        assert len(result) == 0

    def test_empty_people_list(self, converter):
        result = converter._collect_people_code_counts([])
        assert result == []

    def test_missing_days_key(self, converter):
        people = [{"name": "Test"}]
        result = converter._collect_people_code_counts(people)
        assert result[0][1] == Counter()

    def test_none_days(self, converter):
        people = [{"name": "Test", "days": None}]
        result = converter._collect_people_code_counts(people)
        assert result[0][1] == Counter()


# ============================================================================
# Constants
# ============================================================================


class TestConstants:
    """Verify module constants are consistent."""

    def test_cols_per_day(self):
        from app.services.xml_to_xlsx_converter import COLS_PER_DAY

        assert COLS_PER_DAY == 2

    def test_total_days(self):
        from app.services.xml_to_xlsx_converter import TOTAL_DAYS

        assert TOTAL_DAYS == 28

    def test_schedule_end_column(self):
        from app.services.xml_to_xlsx_converter import (
            COL_SCHEDULE_END,
            COL_SCHEDULE_START,
            COLS_PER_DAY,
            TOTAL_DAYS,
        )

        expected = COL_SCHEDULE_START + (TOTAL_DAYS * COLS_PER_DAY) - 1
        assert expected == COL_SCHEDULE_END

    def test_rosetta_columns_sequential(self):
        from app.services.xml_to_xlsx_converter import (
            ROSETTA_COL_NAME,
            ROSETTA_COL_NOTES,
            ROSETTA_COL_PGY,
            ROSETTA_COL_ROTATION1,
            ROSETTA_COL_ROTATION2,
            ROSETTA_COL_SCHEDULE_START,
        )

        assert ROSETTA_COL_NAME == 1
        assert ROSETTA_COL_PGY == 2
        assert ROSETTA_COL_ROTATION1 == 3
        assert ROSETTA_COL_ROTATION2 == 4
        assert ROSETTA_COL_NOTES == 5
        assert ROSETTA_COL_SCHEDULE_START == 6

    def test_bt2_columns_sequential(self):
        from app.services.xml_to_xlsx_converter import (
            BT2_COL_NAME,
            BT2_COL_ROLE,
            BT2_COL_ROTATION1,
            BT2_COL_ROTATION2,
            BT2_COL_SCHEDULE_START,
            BT2_COL_TEMPLATE,
        )

        assert BT2_COL_ROTATION1 == 1
        assert BT2_COL_ROTATION2 == 2
        assert BT2_COL_TEMPLATE == 3
        assert BT2_COL_ROLE == 4
        assert BT2_COL_NAME == 5
        assert BT2_COL_SCHEDULE_START == 6
