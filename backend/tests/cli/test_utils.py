"""
Tests for CLI utility functions.
"""

import pytest

from cli.utils.validators import (
    validate_email,
    validate_date,
    validate_uuid,
    validate_pgy_level,
    validate_role,
    validate_block_number,
)
from cli.utils.formatters import (
    format_bool,
    format_percentage,
    format_hours,
    truncate,
)


class TestValidators:
    """Test validation utilities."""

    def test_validate_email_valid(self):
        """Test valid email addresses."""
        assert validate_email("user@example.com")
        assert validate_email("john.doe@hospital.mil")

    def test_validate_email_invalid(self):
        """Test invalid email addresses."""
        assert not validate_email("invalid")
        assert not validate_email("@example.com")
        assert not validate_email("user@")

    def test_validate_date_valid(self):
        """Test valid dates."""
        assert validate_date("2024-01-15")
        assert validate_date("2024-12-31")

    def test_validate_date_invalid(self):
        """Test invalid dates."""
        assert not validate_date("2024-13-01")
        assert not validate_date("invalid")
        assert not validate_date("01/15/2024")

    def test_validate_uuid_valid(self):
        """Test valid UUIDs."""
        assert validate_uuid("123e4567-e89b-12d3-a456-426614174000")

    def test_validate_uuid_invalid(self):
        """Test invalid UUIDs."""
        assert not validate_uuid("invalid-uuid")
        assert not validate_uuid("123")

    def test_validate_pgy_level(self):
        """Test PGY level validation."""
        assert validate_pgy_level("PGY-1")
        assert validate_pgy_level("PGY-2")
        assert validate_pgy_level("PGY-3")
        assert not validate_pgy_level("PGY-4")
        assert not validate_pgy_level("INVALID")

    def test_validate_role(self):
        """Test role validation."""
        assert validate_role("ADMIN")
        assert validate_role("RESIDENT")
        assert validate_role("FACULTY")
        assert not validate_role("INVALID_ROLE")

    def test_validate_block_number(self):
        """Test block number validation."""
        assert validate_block_number(1)
        assert validate_block_number(12)
        assert not validate_block_number(0)
        assert not validate_block_number(13)


class TestFormatters:
    """Test formatting utilities."""

    def test_format_bool(self):
        """Test boolean formatting."""
        assert format_bool(True) == "✓"
        assert format_bool(False) == "✗"

    def test_format_percentage(self):
        """Test percentage formatting."""
        assert format_percentage(95.5) == "95.5%"
        assert format_percentage(100.0) == "100.0%"
        assert format_percentage(None) == "-"

    def test_format_hours(self):
        """Test hours formatting."""
        assert format_hours(40.5) == "40.5h"
        assert format_hours(80.0) == "80.0h"
        assert format_hours(None) == "-"

    def test_truncate(self):
        """Test text truncation."""
        text = "This is a very long string that should be truncated"
        result = truncate(text, max_length=20)

        assert len(result) <= 20
        assert result.endswith("...")

    def test_truncate_short_text(self):
        """Test truncation of short text."""
        text = "Short"
        result = truncate(text, max_length=20)

        assert result == "Short"
