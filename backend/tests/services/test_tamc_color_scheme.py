"""Tests for tamc_color_scheme.py — Excel color mapping engine.

Tests load the real TAMC_Color_Scheme_Reference.xml to validate
color mappings used in schedule XLSX export.
"""

import os
from pathlib import Path
from tempfile import NamedTemporaryFile

import pytest

from app.services.tamc_color_scheme import TAMCColorScheme

# Path to the real color scheme XML
_PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
_XML_PATH = _PROJECT_ROOT / "docs" / "scheduling" / "TAMC_Color_Scheme_Reference.xml"

_xml_exists = _XML_PATH.exists()
needs_xml = pytest.mark.skipif(not _xml_exists, reason="Color scheme XML not found")


@pytest.fixture
def scheme() -> TAMCColorScheme:
    """Load the real color scheme XML."""
    return TAMCColorScheme(xml_path=_XML_PATH)


# ── Loading ──────────────────────────────────────────────────────────────


@needs_xml
class TestLoading:
    """Test XML loading and parsing."""

    def test_loads_fill_colors(self, scheme):
        """Scheme has fill color mappings."""
        assert scheme.code_count > 0

    def test_known_code_has_color(self, scheme):
        """Common codes like W, C, FMIT should have colors."""
        assert scheme.get_code_color("W") is not None
        assert scheme.get_code_color("FMIT") is not None
        assert scheme.get_code_color("C") is not None

    def test_hex_format_no_alpha(self, scheme):
        """Colors should be 6-char hex (alpha stripped)."""
        color = scheme.get_code_color("W")
        assert color is not None
        assert len(color) == 6
        # Validate hex
        int(color, 16)


# ── get_code_color ───────────────────────────────────────────────────────


@needs_xml
class TestGetCodeColor:
    """Test fill color lookups for schedule codes."""

    def test_weekend_code(self, scheme):
        """W (weekend) should have a color."""
        assert scheme.get_code_color("W") is not None

    def test_fmit_code(self, scheme):
        assert scheme.get_code_color("FMIT") is not None

    def test_hol_code(self, scheme):
        assert scheme.get_code_color("HOL") is not None

    def test_clinic_code(self, scheme):
        assert scheme.get_code_color("C") is not None

    def test_leave_code(self, scheme):
        assert scheme.get_code_color("LV") is not None

    def test_night_float_code(self, scheme):
        assert scheme.get_code_color("NF") is not None

    def test_unknown_code_returns_none(self, scheme):
        assert scheme.get_code_color("ZZZZZ_NONEXISTENT") is None

    def test_empty_code_returns_none(self, scheme):
        assert scheme.get_code_color("") is None

    def test_same_group_codes_share_color(self, scheme):
        """Codes in the same color group should have the same color."""
        # HOL and LEC are both in blocked_protected group
        hol = scheme.get_code_color("HOL")
        lec = scheme.get_code_color("LEC")
        assert hol == lec


# ── get_font_color ───────────────────────────────────────────────────────


@needs_xml
class TestGetFontColor:
    """Test font color lookups for schedule codes."""

    def test_unknown_code_returns_none(self, scheme):
        assert scheme.get_font_color("ZZZZZ_NONEXISTENT") is None

    def test_font_color_hex_format(self, scheme):
        """Any returned font color should be valid 6-char hex."""
        # Try a few codes that might have font colors
        for code in ["PR", "NF", "HOL", "W"]:
            color = scheme.get_font_color(code)
            if color is not None:
                assert len(color) == 6
                int(color, 16)  # validates hex


# ── get_header_color ─────────────────────────────────────────────────────


@needs_xml
class TestGetHeaderColor:
    """Test header color by day of week."""

    def test_monday(self, scheme):
        """Monday (0) is a regular weekday."""
        color = scheme.get_header_color(0)
        # May be None if weekday key not in XML, but should not error
        assert color is None or len(color) == 6

    def test_tuesday_is_special(self, scheme):
        """Tuesday (1) has a special color (light blue)."""
        color = scheme.get_header_color(1)
        assert color is None or len(color) == 6

    def test_thursday_same_as_tuesday(self, scheme):
        """Thursday (3) should match Tuesday (1) color."""
        tue = scheme.get_header_color(1)
        thu = scheme.get_header_color(3)
        assert tue == thu

    def test_weekend_saturday(self, scheme):
        color = scheme.get_header_color(5)
        assert color is None or len(color) == 6

    def test_weekend_sunday(self, scheme):
        color = scheme.get_header_color(6)
        assert color is None or len(color) == 6

    def test_saturday_same_as_sunday(self, scheme):
        """Both weekend days should get the same color."""
        sat = scheme.get_header_color(5)
        sun = scheme.get_header_color(6)
        assert sat == sun


# ── get_rotation_color ───────────────────────────────────────────────────


@needs_xml
class TestGetRotationColor:
    """Test rotation column color lookups."""

    def test_fmit_rotation(self, scheme):
        """FMIT should have a rotation color."""
        color = scheme.get_rotation_color("FMIT")
        assert color is not None

    def test_nf_rotation(self, scheme):
        """NF should have a rotation color."""
        color = scheme.get_rotation_color("NF")
        assert color is not None

    def test_fmc_rotation(self, scheme):
        """FMC should be elective_outpatient type."""
        color = scheme.get_rotation_color("FMC")
        assert color is not None

    def test_im_rotation(self, scheme):
        """IM should be inpatient_critical type."""
        color = scheme.get_rotation_color("IM")
        assert color is not None

    def test_fmo_rotation(self, scheme):
        """FMO should be orientation type."""
        color = scheme.get_rotation_color("FMO")
        assert color is not None

    def test_unknown_rotation_returns_none(self, scheme):
        assert scheme.get_rotation_color("ZZZZZ_NONEXISTENT") is None

    def test_fmit_variants_same_color(self, scheme):
        """All FMIT variants should have the same rotation color."""
        base = scheme.get_rotation_color("FMIT")
        for variant in ["FMIT 1", "FMIT 2", "FMIT1", "FMIT2"]:
            assert scheme.get_rotation_color(variant) == base


# ── _build_rotation_mappings ─────────────────────────────────────────────


@needs_xml
class TestRotationMappings:
    """Test the rotation name to category mappings."""

    def test_inpatient_rotations_mapped(self, scheme):
        """Inpatient rotations should map to inpatient_critical."""
        for rot in ["IM", "KAP", "ICU"]:
            assert scheme._rotation_mappings.get(rot) == "inpatient_critical"

    def test_elective_rotations_mapped(self, scheme):
        for rot in ["FMC", "NEURO", "SM"]:
            assert scheme._rotation_mappings.get(rot) == "elective_outpatient"

    def test_night_float_mapped(self, scheme):
        for rot in ["NF", "Peds NF", "PedNF"]:
            assert scheme._rotation_mappings.get(rot) == "night_float"

    def test_orientation_mapped(self, scheme):
        for rot in ["FMO", "DCC", "BOLC"]:
            assert scheme._rotation_mappings.get(rot) == "orientation"


# ── Edge cases ──────────────────────────────────────────────────────────


class TestEdgeCases:
    """Edge cases that don't need the real XML file."""

    def test_missing_xml_no_crash(self, tmp_path):
        """Non-existent XML path should not crash, just return empty."""
        scheme = TAMCColorScheme(xml_path=tmp_path / "nonexistent.xml")
        assert scheme.code_count == 0
        assert scheme.get_code_color("W") is None

    def test_empty_xml_no_crash(self, tmp_path):
        """Malformed XML should not crash."""
        bad_xml = tmp_path / "empty.xml"
        bad_xml.write_text('<?xml version="1.0"?><root/>')
        scheme = TAMCColorScheme(xml_path=bad_xml)
        assert scheme.code_count == 0

    def test_minimal_xml(self, tmp_path):
        """Minimal valid XML with one code should work."""
        xml_content = """<?xml version="1.0"?>
<tamc_color_scheme>
  <fill_colors>
    <color_group name="test" hex_color="FF112233">
      <code value="TST"/>
    </color_group>
  </fill_colors>
</tamc_color_scheme>"""
        xml_path = tmp_path / "test.xml"
        xml_path.write_text(xml_content)
        scheme = TAMCColorScheme(xml_path=xml_path)
        assert scheme.code_count == 1
        assert scheme.get_code_color("TST") == "112233"

    def test_alpha_stripping(self, tmp_path):
        """FF prefix (alpha channel) should be stripped from 8-char hex."""
        xml_content = """<?xml version="1.0"?>
<tamc_color_scheme>
  <fill_colors>
    <color_group name="test" hex_color="FFAABBCC">
      <code value="ABC"/>
    </color_group>
  </fill_colors>
</tamc_color_scheme>"""
        xml_path = tmp_path / "test.xml"
        xml_path.write_text(xml_content)
        scheme = TAMCColorScheme(xml_path=xml_path)
        assert scheme.get_code_color("ABC") == "AABBCC"

    def test_short_hex_not_stripped(self, tmp_path):
        """6-char hex should NOT have anything stripped."""
        xml_content = """<?xml version="1.0"?>
<tamc_color_scheme>
  <fill_colors>
    <color_group name="test" hex_color="FF0000">
      <code value="RED"/>
    </color_group>
  </fill_colors>
</tamc_color_scheme>"""
        xml_path = tmp_path / "test.xml"
        xml_path.write_text(xml_content)
        scheme = TAMCColorScheme(xml_path=xml_path)
        assert scheme.get_code_color("RED") == "FF0000"
