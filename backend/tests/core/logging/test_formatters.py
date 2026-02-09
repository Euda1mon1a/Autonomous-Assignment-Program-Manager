"""Tests for custom log formatters (JSON, GELF, Logfmt, CloudWatch, ColoredText)."""

import json
from datetime import datetime
from unittest.mock import MagicMock

from app.core.logging.formatters import (
    CloudWatchFormatter,
    ColoredTextFormatter,
    GELFFormatter,
    JSONFormatter,
    LogfmtFormatter,
    create_cloudwatch_formatter,
    create_colored_text_formatter,
    create_gelf_formatter,
    create_json_formatter,
    create_logfmt_formatter,
)


def _make_record(**overrides):
    """Build a minimal loguru-style record dict."""
    level_mock = MagicMock()
    level_mock.name = "INFO"
    level_mock.no = 20

    process_mock = MagicMock()
    process_mock.id = 1234
    process_mock.name = "MainProcess"

    thread_mock = MagicMock()
    thread_mock.id = 5678
    thread_mock.name = "MainThread"

    record = {
        "time": datetime(2025, 1, 15, 10, 30, 0),
        "level": level_mock,
        "message": "Test log message",
        "name": "app.test",
        "module": "test_module",
        "function": "test_func",
        "line": 42,
        "extra": {},
        "exception": None,
        "process": process_mock,
        "thread": thread_mock,
    }
    record.update(overrides)
    return record


# ==================== JSONFormatter ====================


class TestJSONFormatter:
    def test_init_defaults(self):
        f = JSONFormatter()
        assert f.indent is None
        assert f.include_extra is True
        assert f.timestamp_format == "iso"

    def test_init_custom(self):
        f = JSONFormatter(indent=2, include_extra=False, timestamp_format="unix")
        assert f.indent == 2
        assert f.include_extra is False
        assert f.timestamp_format == "unix"

    def test_format_basic(self):
        f = JSONFormatter()
        result = json.loads(f.format(_make_record()))
        assert result["level"] == "INFO"
        assert result["message"] == "Test log message"
        assert result["logger"] == "app.test"
        assert result["module"] == "test_module"
        assert result["function"] == "test_func"
        assert result["line"] == 42

    def test_format_iso_timestamp(self):
        f = JSONFormatter(timestamp_format="iso")
        result = json.loads(f.format(_make_record()))
        assert "2025-01-15" in result["timestamp"]

    def test_format_unix_timestamp(self):
        f = JSONFormatter(timestamp_format="unix")
        result = json.loads(f.format(_make_record()))
        assert isinstance(result["timestamp"], int)

    def test_format_unix_ms_timestamp(self):
        f = JSONFormatter(timestamp_format="unix_ms")
        result = json.loads(f.format(_make_record()))
        assert isinstance(result["timestamp"], int)
        assert result["timestamp"] > 1_000_000_000_000  # ms

    def test_format_with_extra(self):
        f = JSONFormatter()
        record = _make_record(extra={"user_id": 123, "action": "login"})
        result = json.loads(f.format(record))
        assert result["user_id"] == 123
        assert result["action"] == "login"

    def test_format_extra_excluded(self):
        f = JSONFormatter(include_extra=False)
        record = _make_record(extra={"user_id": 123})
        result = json.loads(f.format(record))
        assert "user_id" not in result

    def test_format_with_exception(self):
        exc = MagicMock()
        exc.type = ValueError
        exc.value = ValueError("test error")
        exc.traceback = MagicMock()
        f = JSONFormatter()
        result = json.loads(f.format(_make_record(exception=exc)))
        assert result["exception"]["type"] == "ValueError"
        assert "test error" in result["exception"]["value"]
        assert result["exception"]["traceback"] is True

    def test_format_includes_process_thread(self):
        f = JSONFormatter()
        result = json.loads(f.format(_make_record()))
        assert result["process"]["id"] == 1234
        assert result["thread"]["id"] == 5678

    def test_format_valid_json(self):
        f = JSONFormatter()
        output = f.format(_make_record())
        parsed = json.loads(output)
        assert isinstance(parsed, dict)

    def test_format_with_indent(self):
        f = JSONFormatter(indent=2)
        output = f.format(_make_record())
        assert "\n" in output  # Indented JSON has newlines


# ==================== GELFFormatter ====================


class TestGELFFormatter:
    def test_init_defaults(self):
        f = GELFFormatter()
        assert f.facility == "app"
        assert f.include_extra is True
        assert f.hostname  # Should be a string

    def test_format_basic(self):
        f = GELFFormatter()
        result = json.loads(f.format(_make_record()))
        assert result["version"] == "1.1"
        assert result["short_message"] == "Test log message"
        assert result["facility"] == "app"
        assert "_logger" in result
        assert "_module" in result

    def test_format_level_mapping_debug(self):
        f = GELFFormatter()
        level = MagicMock()
        level.name = "DEBUG"
        level.no = 10
        result = json.loads(f.format(_make_record(level=level)))
        assert result["level"] == 7  # DEBUG -> 7

    def test_format_level_mapping_info(self):
        f = GELFFormatter()
        result = json.loads(f.format(_make_record()))
        assert result["level"] == 6  # INFO (20) -> 6

    def test_format_level_mapping_warning(self):
        f = GELFFormatter()
        level = MagicMock()
        level.name = "WARNING"
        level.no = 30
        result = json.loads(f.format(_make_record(level=level)))
        assert result["level"] == 4  # WARNING -> 4

    def test_format_level_mapping_error(self):
        f = GELFFormatter()
        level = MagicMock()
        level.name = "ERROR"
        level.no = 40
        result = json.loads(f.format(_make_record(level=level)))
        assert result["level"] == 3  # ERROR -> 3

    def test_format_level_mapping_critical(self):
        f = GELFFormatter()
        level = MagicMock()
        level.name = "CRITICAL"
        level.no = 50
        result = json.loads(f.format(_make_record(level=level)))
        assert result["level"] == 2  # CRITICAL -> 2

    def test_format_extra_prefixed(self):
        f = GELFFormatter()
        record = _make_record(extra={"user_id": 123})
        result = json.loads(f.format(record))
        assert result["_user_id"] == 123

    def test_format_with_exception(self):
        exc = MagicMock()
        exc.type = RuntimeError
        exc.value = RuntimeError("boom")
        f = GELFFormatter()
        result = json.loads(f.format(_make_record(exception=exc)))
        assert result["_exception_type"] == "RuntimeError"
        assert "boom" in result["_exception_value"]


# ==================== LogfmtFormatter ====================


class TestLogfmtFormatter:
    def test_init_default(self):
        f = LogfmtFormatter()
        assert f.include_extra is True

    def test_format_basic(self):
        f = LogfmtFormatter()
        output = f.format(_make_record())
        assert "level=INFO" in output
        assert "module=test_module" in output
        assert "function=test_func" in output
        assert "line=42" in output

    def test_format_message_quoted(self):
        f = LogfmtFormatter()
        record = _make_record(message="message with spaces")
        output = f.format(record)
        assert '"message with spaces"' in output

    def test_format_extra(self):
        f = LogfmtFormatter()
        record = _make_record(extra={"user_id": 123})
        output = f.format(record)
        assert "user_id=123" in output

    def test_format_exception(self):
        exc = MagicMock()
        exc.type = ValueError
        exc.value = ValueError("oops")
        f = LogfmtFormatter()
        output = f.format(_make_record(exception=exc))
        assert "exception_type=ValueError" in output

    def test_quote_with_spaces(self):
        f = LogfmtFormatter()
        assert f._quote("hello world") == '"hello world"'

    def test_quote_with_equals(self):
        f = LogfmtFormatter()
        assert f._quote("key=val") == '"key=val"'

    def test_quote_without_special(self):
        f = LogfmtFormatter()
        assert f._quote("simple") == "simple"

    def test_quote_with_quotes(self):
        f = LogfmtFormatter()
        result = f._quote('say "hello"')
        assert '\\"hello\\"' in result


# ==================== CloudWatchFormatter ====================


class TestCloudWatchFormatter:
    def test_init_default(self):
        f = CloudWatchFormatter()
        assert f.include_extra is True

    def test_format_basic(self):
        f = CloudWatchFormatter()
        result = json.loads(f.format(_make_record()))
        assert result["@level"] == "INFO"
        assert result["@message"] == "Test log message"
        assert result["@module"] == "test_module"
        assert "@timestamp" in result

    def test_format_extra(self):
        f = CloudWatchFormatter()
        record = _make_record(extra={"user_id": 123})
        result = json.loads(f.format(record))
        assert result["user_id"] == 123  # No prefix for CloudWatch extras

    def test_format_exception(self):
        exc = MagicMock()
        exc.type = RuntimeError
        exc.value = RuntimeError("fail")
        f = CloudWatchFormatter()
        result = json.loads(f.format(_make_record(exception=exc)))
        assert result["@exception"]["type"] == "RuntimeError"

    def test_format_valid_json(self):
        f = CloudWatchFormatter()
        output = f.format(_make_record())
        parsed = json.loads(output)
        assert isinstance(parsed, dict)


# ==================== ColoredTextFormatter ====================


class TestColoredTextFormatter:
    def test_init_defaults(self):
        f = ColoredTextFormatter()
        assert f.include_colors is True
        assert f.include_extra is True

    def test_colors_dict(self):
        assert "DEBUG" in ColoredTextFormatter.COLORS
        assert "INFO" in ColoredTextFormatter.COLORS
        assert "ERROR" in ColoredTextFormatter.COLORS
        assert "CRITICAL" in ColoredTextFormatter.COLORS
        assert "RESET" in ColoredTextFormatter.COLORS

    def test_format_with_colors(self):
        f = ColoredTextFormatter(include_colors=True)
        output = f.format(_make_record())
        assert "\033[" in output  # ANSI codes present
        assert "Test log message" in output

    def test_format_without_colors(self):
        f = ColoredTextFormatter(include_colors=False)
        output = f.format(_make_record())
        assert "\033[" not in output
        assert "Test log message" in output

    def test_format_includes_location(self):
        f = ColoredTextFormatter(include_colors=False)
        output = f.format(_make_record())
        assert "test_module:test_func:42" in output

    def test_format_with_extra(self):
        f = ColoredTextFormatter(include_colors=False)
        record = _make_record(extra={"user_id": 123})
        output = f.format(record)
        assert "user_id=123" in output


# ==================== Factory functions ====================


class TestFactoryFunctions:
    def test_create_json_formatter(self):
        f = create_json_formatter()
        assert isinstance(f, JSONFormatter)

    def test_create_json_formatter_custom(self):
        f = create_json_formatter(indent=2, timestamp_format="unix")
        assert f.indent == 2
        assert f.timestamp_format == "unix"

    def test_create_gelf_formatter(self):
        f = create_gelf_formatter()
        assert isinstance(f, GELFFormatter)

    def test_create_gelf_formatter_custom(self):
        f = create_gelf_formatter(facility="myapp")
        assert f.facility == "myapp"

    def test_create_logfmt_formatter(self):
        f = create_logfmt_formatter()
        assert isinstance(f, LogfmtFormatter)

    def test_create_cloudwatch_formatter(self):
        f = create_cloudwatch_formatter()
        assert isinstance(f, CloudWatchFormatter)

    def test_create_colored_text_formatter(self):
        f = create_colored_text_formatter()
        assert isinstance(f, ColoredTextFormatter)

    def test_create_colored_text_formatter_no_colors(self):
        f = create_colored_text_formatter(include_colors=False)
        assert f.include_colors is False
