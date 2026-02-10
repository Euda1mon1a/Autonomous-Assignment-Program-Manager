"""Tests for PHI sanitization filter."""

import logging

import pytest

from app.core.phi_filter import PHIFilter, phi_patcher, sanitize_text


class TestSanitizeText:
    """Unit tests for the sanitize_text helper."""

    def test_email_redacted(self):
        assert sanitize_text("user john@example.com logged in") == (
            "user [EMAIL_REDACTED] logged in"
        )

    def test_ssn_redacted(self):
        assert sanitize_text("SSN is 123-45-6789") == "SSN is [SSN_REDACTED]"

    def test_phone_redacted_dashes(self):
        assert sanitize_text("Call 555-123-4567") == "Call [PHONE_REDACTED]"

    def test_phone_redacted_dots(self):
        assert sanitize_text("Call 555.123.4567") == "Call [PHONE_REDACTED]"

    def test_phone_redacted_plain(self):
        assert sanitize_text("Call 5551234567") == "Call [PHONE_REDACTED]"

    def test_normal_message_unchanged(self):
        msg = "Schedule generated for block 3"
        assert sanitize_text(msg) == msg

    def test_multiple_patterns(self):
        msg = "User john@example.com SSN 123-45-6789 phone 555-123-4567"
        result = sanitize_text(msg)
        assert "[EMAIL_REDACTED]" in result
        assert "[SSN_REDACTED]" in result
        assert "[PHONE_REDACTED]" in result
        assert "john@example.com" not in result
        assert "123-45-6789" not in result
        assert "555-123-4567" not in result


class TestPHIPatcher:
    """Tests for the loguru patcher function."""

    def test_sanitizes_message(self):
        record = {"message": "Email: test@example.com"}
        phi_patcher(record)
        assert record["message"] == "Email: [EMAIL_REDACTED]"

    def test_non_string_message_ignored(self):
        record = {"message": 42}
        phi_patcher(record)
        assert record["message"] == 42

    def test_missing_message_key(self):
        record = {}
        phi_patcher(record)  # should not raise


class TestPHIFilter:
    """Tests for the stdlib logging.Filter."""

    @pytest.fixture()
    def phi_filter(self):
        return PHIFilter()

    def test_email_in_msg(self, phi_filter):
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="User %s logged in from john@example.com",
            args=("admin",),
            exc_info=None,
        )
        phi_filter.filter(record)
        assert "john@example.com" not in record.msg
        assert "[EMAIL_REDACTED]" in record.msg

    def test_ssn_in_msg(self, phi_filter):
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="SSN 123-45-6789 found",
            args=None,
            exc_info=None,
        )
        phi_filter.filter(record)
        assert "123-45-6789" not in record.msg

    def test_phone_in_msg(self, phi_filter):
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="Phone 555-123-4567",
            args=None,
            exc_info=None,
        )
        phi_filter.filter(record)
        assert "555-123-4567" not in record.msg

    def test_normal_message_passes(self, phi_filter):
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="All systems operational",
            args=None,
            exc_info=None,
        )
        result = phi_filter.filter(record)
        assert result is True
        assert record.msg == "All systems operational"

    def test_tuple_args_sanitized(self, phi_filter):
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="User %s with email %s",
            args=("admin", "admin@example.com"),
            exc_info=None,
        )
        phi_filter.filter(record)
        assert record.args[0] == "admin"
        assert record.args[1] == "[EMAIL_REDACTED]"

    def test_dict_args_sanitized(self, phi_filter):
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="User %(name)s email %(email)s",
            args={"name": "admin", "email": "admin@example.com"},
            exc_info=None,
        )
        phi_filter.filter(record)
        assert record.args["name"] == "admin"
        assert record.args["email"] == "[EMAIL_REDACTED]"

    def test_filter_always_returns_true(self, phi_filter):
        """Filter should sanitize but never suppress records."""
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="SSN 999-88-7777",
            args=None,
            exc_info=None,
        )
        assert phi_filter.filter(record) is True
