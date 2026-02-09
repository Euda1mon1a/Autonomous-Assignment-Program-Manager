"""Tests for structured logging configuration."""

import json
import logging
from unittest.mock import MagicMock, patch

from app.core.logging import (
    InterceptHandler,
    _json_serializer,
    _request_id_ctx,
    get_logger,
    get_request_id,
    set_request_id,
    setup_logging,
)


# ==================== Request ID Context ====================


class TestRequestIdContext:
    def test_default_none(self):
        assert get_request_id() is None

    def test_set_and_get(self):
        set_request_id("test-123")
        assert get_request_id() == "test-123"
        # Clean up
        set_request_id(None)

    def test_overwrite(self):
        set_request_id("first")
        set_request_id("second")
        assert get_request_id() == "second"
        set_request_id(None)


# ==================== InterceptHandler ====================


class TestInterceptHandler:
    def test_is_handler(self):
        handler = InterceptHandler()
        assert isinstance(handler, logging.Handler)

    def test_has_emit(self):
        handler = InterceptHandler()
        assert hasattr(handler, "emit")
        assert callable(handler.emit)


# ==================== _json_serializer ====================


class TestJsonSerializer:
    def _make_record(self, **overrides):
        """Build a minimal loguru-style record dict."""
        level_mock = MagicMock()
        level_mock.name = (
            "INFO"  # MagicMock(name=) sets Mock's internal name, not .name attr
        )
        record = {
            "time": MagicMock(
                strftime=MagicMock(return_value="2025-01-01T00:00:00.000000+0000")
            ),
            "level": level_mock,
            "message": "test message",
            "name": "app.core.test",
            "function": "test_func",
            "line": 42,
            "extra": {},
            "exception": None,
        }
        record.update(overrides)
        return record

    def test_basic_fields(self):
        record = self._make_record()
        result = json.loads(_json_serializer(record))
        assert result["level"] == "INFO"
        assert result["message"] == "test message"
        assert result["module"] == "app.core.test"
        assert result["function"] == "test_func"
        assert result["line"] == 42

    def test_timestamp_present(self):
        record = self._make_record()
        result = json.loads(_json_serializer(record))
        assert "timestamp" in result

    def test_request_id_included(self):
        token = _request_id_ctx.set("req-abc")
        try:
            record = self._make_record()
            result = json.loads(_json_serializer(record))
            assert result["request_id"] == "req-abc"
        finally:
            _request_id_ctx.reset(token)

    def test_request_id_excluded_when_none(self):
        token = _request_id_ctx.set(None)
        try:
            record = self._make_record()
            result = json.loads(_json_serializer(record))
            assert "request_id" not in result
        finally:
            _request_id_ctx.reset(token)

    def test_extra_fields_included(self):
        record = self._make_record(extra={"user_id": 123, "action": "create"})
        result = json.loads(_json_serializer(record))
        assert result["user_id"] == 123
        assert result["action"] == "create"

    def test_exception_info(self):
        exc = MagicMock()
        exc.type = ValueError
        exc.value = ValueError("test error")
        exc.traceback = MagicMock()
        record = self._make_record(exception=exc)
        result = json.loads(_json_serializer(record))
        assert result["exception"]["type"] == "ValueError"
        assert "test error" in result["exception"]["value"]
        assert result["exception"]["traceback"] is True

    def test_exception_none_type(self):
        exc = MagicMock()
        exc.type = None
        exc.value = None
        exc.traceback = None
        record = self._make_record(exception=exc)
        result = json.loads(_json_serializer(record))
        assert result["exception"]["type"] is None
        assert result["exception"]["value"] is None

    def test_output_is_valid_json(self):
        record = self._make_record()
        result = _json_serializer(record)
        # Should not raise
        parsed = json.loads(result)
        assert isinstance(parsed, dict)


# ==================== get_logger ====================


class TestGetLogger:
    def test_returns_logger(self):
        log = get_logger("test.module")
        # loguru logger has bind, should have module in extra
        assert log is not None

    def test_different_names(self):
        log1 = get_logger("module.a")
        log2 = get_logger("module.b")
        # Both should be loguru loggers (they're bound instances)
        assert log1 is not None
        assert log2 is not None


# ==================== setup_logging ====================


class TestSetupLogging:
    def test_text_format(self):
        """setup_logging with text format does not raise."""
        setup_logging(level="WARNING", format_type="text")

    def test_json_format(self):
        """setup_logging with json format does not raise."""
        setup_logging(level="INFO", format_type="json")

    def test_custom_level(self):
        """setup_logging with DEBUG level does not raise."""
        setup_logging(level="DEBUG", format_type="text")

    def test_setup_multiple_times(self):
        """setup_logging can be called multiple times without error."""
        setup_logging(level="INFO", format_type="text")
        setup_logging(level="WARNING", format_type="json")
