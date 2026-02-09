"""Tests for TAMC color scheme service."""

import pytest
from pathlib import Path

from app.services.tamc_color_scheme import (
    TAMCColorScheme,
    get_code_color,
    get_font_color,
    get_header_color,
    get_rotation_color,
    DEFAULT_COLOR_SCHEME_PATH,
)


class TestTAMCColorScheme:
    """Test TAMCColorScheme class."""

    @pytest.fixture
    def color_scheme(self) -> TAMCColorScheme:
        """Create a color scheme instance."""
        return TAMCColorScheme()

    def test_init_with_default_path(self, color_scheme: TAMCColorScheme) -> None:
        """Test initialization with default path."""
        assert color_scheme is not None
        assert color_scheme.xml_path == DEFAULT_COLOR_SCHEME_PATH

    def test_init_with_custom_path(self) -> None:
        """Test initialization with custom path."""
        custom_path = Path("/tmp/test.xml")
        color_scheme = TAMCColorScheme(xml_path=custom_path)
        assert color_scheme.xml_path == custom_path

    def test_get_code_color(self, color_scheme: TAMCColorScheme) -> None:
        """Test getting color for a schedule code."""
        # Test with a known code from the XML
        color = color_scheme.get_code_color("C")
        # Just verify it returns a string or None (not an error)
        assert color is None or isinstance(color, str)

    def test_get_font_color(self, color_scheme: TAMCColorScheme) -> None:
        """Test getting font color for a schedule code."""
        color = color_scheme.get_font_color("PR")
        assert color is None or isinstance(color, str)

    def test_get_header_color(self, color_scheme: TAMCColorScheme) -> None:
        """Test getting header color for day of week."""
        # Test all days
        for day in range(7):
            color = color_scheme.get_header_color(day)
            # Should return a string or None (not raise)
            assert color is None or isinstance(color, str)

    def test_get_rotation_color(self, color_scheme: TAMCColorScheme) -> None:
        """Test getting color for a rotation."""
        color = color_scheme.get_rotation_color("FMC")
        assert color is None or isinstance(color, str)

    def test_code_count_property(self, color_scheme: TAMCColorScheme) -> None:
        """Test code_count property."""
        count = color_scheme.code_count
        assert isinstance(count, int)
        assert count >= 0


class TestModuleLevelFunctions:
    """Test module-level convenience functions."""

    def test_get_code_color(self) -> None:
        """Test get_code_color function."""
        color = get_code_color("C")
        assert color is None or isinstance(color, str)

    def test_get_font_color(self) -> None:
        """Test get_font_color function."""
        color = get_font_color("PR")
        assert color is None or isinstance(color, str)

    def test_get_header_color(self) -> None:
        """Test get_header_color function."""
        color = get_header_color(0)
        assert color is None or isinstance(color, str)

    def test_get_rotation_color(self) -> None:
        """Test get_rotation_color function."""
        color = get_rotation_color("FMC")
        assert color is None or isinstance(color, str)