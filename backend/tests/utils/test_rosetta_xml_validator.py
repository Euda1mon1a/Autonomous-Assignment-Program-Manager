"""Tests for ROSETTA XML validator."""

import tempfile
from pathlib import Path

import pytest

from app.utils.rosetta_xml_validator import (
    compare_xml,
    get_mismatch_summary,
    validate_xml_structure,
)


# ============================================================================
# validate_xml_structure
# ============================================================================


class TestValidateXmlStructure:
    """Tests for validate_xml_structure."""

    def test_valid_xml(self):
        xml = """<?xml version="1.0"?>
        <schedule block_start="2025-07-07" block_end="2025-08-03">
            <resident name="Smith, John" pgy="2" rotation1="NF">
                <day date="2025-07-07" weekday="Mon" am="NF" pm="NF"/>
            </resident>
        </schedule>"""
        issues = validate_xml_structure(xml)
        assert issues == []

    def test_invalid_xml(self):
        issues = validate_xml_structure("<not valid xml")
        assert len(issues) == 1
        assert "XML parse error" in issues[0]

    def test_wrong_root_element(self):
        xml = '<blocks><resident name="A" pgy="1"><day date="2025-01-01"/></resident></blocks>'
        issues = validate_xml_structure(xml)
        assert any("Root element should be 'schedule'" in i for i in issues)

    def test_missing_block_start(self):
        xml = """<schedule block_end="2025-08-03">
            <resident name="A" pgy="1"><day date="2025-01-01"/></resident>
        </schedule>"""
        issues = validate_xml_structure(xml)
        assert any("Missing block_start" in i for i in issues)

    def test_missing_block_end(self):
        xml = """<schedule block_start="2025-07-07">
            <resident name="A" pgy="1"><day date="2025-01-01"/></resident>
        </schedule>"""
        issues = validate_xml_structure(xml)
        assert any("Missing block_end" in i for i in issues)

    def test_no_residents(self):
        xml = '<schedule block_start="2025-07-07" block_end="2025-08-03"></schedule>'
        issues = validate_xml_structure(xml)
        assert any("No resident elements" in i for i in issues)

    def test_resident_missing_name(self):
        xml = """<schedule block_start="2025-07-07" block_end="2025-08-03">
            <resident pgy="1"><day date="2025-01-01"/></resident>
        </schedule>"""
        issues = validate_xml_structure(xml)
        assert any("missing name" in i for i in issues)

    def test_resident_missing_pgy(self):
        xml = """<schedule block_start="2025-07-07" block_end="2025-08-03">
            <resident name="Smith"><day date="2025-01-01"/></resident>
        </schedule>"""
        issues = validate_xml_structure(xml)
        assert any("missing pgy" in i for i in issues)

    def test_resident_no_days(self):
        xml = """<schedule block_start="2025-07-07" block_end="2025-08-03">
            <resident name="Smith" pgy="1"></resident>
        </schedule>"""
        issues = validate_xml_structure(xml)
        assert any("no day elements" in i for i in issues)

    def test_day_missing_date(self):
        xml = """<schedule block_start="2025-07-07" block_end="2025-08-03">
            <resident name="Smith" pgy="1"><day weekday="Mon"/></resident>
        </schedule>"""
        issues = validate_xml_structure(xml)
        assert any("without date" in i for i in issues)

    def test_multiple_residents(self):
        xml = """<schedule block_start="2025-07-07" block_end="2025-08-03">
            <resident name="Smith" pgy="1"><day date="2025-07-07"/></resident>
            <resident name="Jones" pgy="2"><day date="2025-07-07"/></resident>
        </schedule>"""
        issues = validate_xml_structure(xml)
        assert issues == []


# ============================================================================
# get_mismatch_summary
# ============================================================================


class TestGetMismatchSummary:
    """Tests for get_mismatch_summary."""

    def test_empty_list(self):
        result = get_mismatch_summary([])
        assert result["total"] == 0
        assert result["by_resident"] == {}
        assert result["by_time"] == {"AM": 0, "PM": 0}
        assert result["sample_mismatches"] == []

    def test_single_mismatch(self):
        mismatches = ["Smith 2025-07-07 AM: expected NF, got C"]
        result = get_mismatch_summary(mismatches)
        assert result["total"] == 1
        assert result["by_resident"]["Smith"] == 1
        assert result["by_time"]["AM"] == 1
        assert result["by_time"]["PM"] == 0

    def test_multiple_mismatches_same_resident(self):
        mismatches = [
            "Smith 2025-07-07 AM: expected NF, got C",
            "Smith 2025-07-07 PM: expected NF, got OFF",
        ]
        result = get_mismatch_summary(mismatches)
        assert result["total"] == 2
        assert result["by_resident"]["Smith"] == 2
        assert result["by_time"]["AM"] == 1
        assert result["by_time"]["PM"] == 1

    def test_multiple_residents(self):
        mismatches = [
            "Smith 2025-07-07 AM: expected NF, got C",
            "Jones 2025-07-08 PM: expected C, got NF",
        ]
        result = get_mismatch_summary(mismatches)
        assert result["by_resident"]["Smith"] == 1
        assert result["by_resident"]["Jones"] == 1

    def test_comma_name_format(self):
        mismatches = ["Smith, John 2025-07-07 AM: expected NF, got C"]
        result = get_mismatch_summary(mismatches)
        # "Smith," has comma so name="Smith, John", time from parts[3]
        assert result["total"] == 1
        assert result["by_time"]["AM"] == 1

    def test_sample_limited_to_5(self):
        mismatches = [f"R{i} 2025-01-01 AM: expected A, got B" for i in range(10)]
        result = get_mismatch_summary(mismatches)
        assert result["total"] == 10
        assert len(result["sample_mismatches"]) == 5

    def test_missing_resident_mismatch(self):
        mismatches = ["Missing resident in generated: Smith"]
        result = get_mismatch_summary(mismatches)
        assert result["total"] == 1
        # These don't have AM/PM so time counters stay 0
        assert result["by_time"]["AM"] == 0
        assert result["by_time"]["PM"] == 0


# ============================================================================
# compare_xml
# ============================================================================


class TestCompareXml:
    """Tests for compare_xml using temp files."""

    def _write_xml(self, content: str) -> Path:
        """Write XML to a temp file and return its path."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".xml", delete=False
        ) as temp_file:
            temp_file.write(content)
            return Path(temp_file.name)

    def _rosetta_xml(self, residents_xml: str) -> str:
        return f"""<?xml version="1.0"?>
        <schedule block_start="2025-07-07" block_end="2025-08-03">
            {residents_xml}
        </schedule>"""

    def test_identical_xml(self):
        xml = self._rosetta_xml(
            '<resident name="Smith" pgy="1">'
            '<day date="2025-07-07" am="NF" pm="NF"/>'
            "</resident>"
        )
        rosetta_path = self._write_xml(xml)
        mismatches = compare_xml(rosetta_path, xml)
        assert mismatches == []

    def test_mismatch_am(self):
        rosetta = self._rosetta_xml(
            '<resident name="Smith" pgy="1">'
            '<day date="2025-07-07" am="NF" pm="NF"/>'
            "</resident>"
        )
        generated = self._rosetta_xml(
            '<resident name="Smith" pgy="1">'
            '<day date="2025-07-07" am="C" pm="NF"/>'
            "</resident>"
        )
        rosetta_path = self._write_xml(rosetta)
        mismatches = compare_xml(rosetta_path, generated)
        assert len(mismatches) == 1
        assert "AM" in mismatches[0]
        assert "expected NF" in mismatches[0]
        assert "got C" in mismatches[0]

    def test_mismatch_pm(self):
        rosetta = self._rosetta_xml(
            '<resident name="Smith" pgy="1">'
            '<day date="2025-07-07" am="NF" pm="NF"/>'
            "</resident>"
        )
        generated = self._rosetta_xml(
            '<resident name="Smith" pgy="1">'
            '<day date="2025-07-07" am="NF" pm="OFF"/>'
            "</resident>"
        )
        rosetta_path = self._write_xml(rosetta)
        mismatches = compare_xml(rosetta_path, generated)
        assert len(mismatches) == 1
        assert "PM" in mismatches[0]

    def test_missing_resident_in_generated(self):
        rosetta = self._rosetta_xml(
            '<resident name="Smith" pgy="1">'
            '<day date="2025-07-07" am="NF" pm="NF"/>'
            "</resident>"
            '<resident name="Jones" pgy="2">'
            '<day date="2025-07-07" am="C" pm="C"/>'
            "</resident>"
        )
        generated = self._rosetta_xml(
            '<resident name="Smith" pgy="1">'
            '<day date="2025-07-07" am="NF" pm="NF"/>'
            "</resident>"
        )
        rosetta_path = self._write_xml(rosetta)
        mismatches = compare_xml(rosetta_path, generated)
        assert any("Missing resident" in m for m in mismatches)
        assert any("Jones" in m for m in mismatches)

    def test_extra_resident_in_generated(self):
        rosetta = self._rosetta_xml(
            '<resident name="Smith" pgy="1">'
            '<day date="2025-07-07" am="NF" pm="NF"/>'
            "</resident>"
        )
        generated = self._rosetta_xml(
            '<resident name="Smith" pgy="1">'
            '<day date="2025-07-07" am="NF" pm="NF"/>'
            "</resident>"
            '<resident name="Extra" pgy="1">'
            '<day date="2025-07-07" am="C" pm="C"/>'
            "</resident>"
        )
        rosetta_path = self._write_xml(rosetta)
        mismatches = compare_xml(rosetta_path, generated)
        assert any("Extra resident" in m for m in mismatches)

    def test_generated_has_extra_value(self):
        rosetta = self._rosetta_xml(
            '<resident name="Smith" pgy="1">'
            '<day date="2025-07-07" am="" pm=""/>'
            "</resident>"
        )
        generated = self._rosetta_xml(
            '<resident name="Smith" pgy="1">'
            '<day date="2025-07-07" am="C" pm=""/>'
            "</resident>"
        )
        rosetta_path = self._write_xml(rosetta)
        mismatches = compare_xml(rosetta_path, generated)
        assert any("expected (empty)" in m for m in mismatches)

    def test_rosetta_file_not_found(self):
        mismatches = compare_xml("/nonexistent/file.xml", "<schedule/>")
        assert len(mismatches) == 1
        assert "not found" in mismatches[0]

    def test_generated_as_path(self):
        xml = self._rosetta_xml(
            '<resident name="Smith" pgy="1">'
            '<day date="2025-07-07" am="NF" pm="NF"/>'
            "</resident>"
        )
        rosetta_path = self._write_xml(xml)
        generated_path = self._write_xml(xml)
        mismatches = compare_xml(rosetta_path, generated_path)
        assert mismatches == []

    def test_perfect_match_multiple_residents(self):
        xml = self._rosetta_xml(
            '<resident name="Smith" pgy="1">'
            '<day date="2025-07-07" am="NF" pm="NF"/>'
            '<day date="2025-07-08" am="C" pm="C"/>'
            "</resident>"
            '<resident name="Jones" pgy="2">'
            '<day date="2025-07-07" am="OFF" pm="OFF"/>'
            "</resident>"
        )
        rosetta_path = self._write_xml(xml)
        mismatches = compare_xml(rosetta_path, xml)
        assert mismatches == []
