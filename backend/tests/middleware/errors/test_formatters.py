"""Tests for RFC 7807 error formatters (pure logic, no DB)."""

import pytest
from pydantic import BaseModel, ValidationError as PydanticValidationError

from app.core.error_codes import ErrorCode
from app.middleware.errors.formatters import (
    ErrorFormatter,
    ProblemDetail,
    SimpleErrorFormatter,
    get_formatter,
    set_formatter,
)


# -- ProblemDetail model -----------------------------------------------------


class TestProblemDetailModel:
    def test_required_fields(self):
        pd = ProblemDetail(
            type="https://example.com/errors/test",
            title="Test Error",
            status=400,
            detail="Something went wrong",
            instance="/api/v1/test",
            error_code=ErrorCode.VALIDATION_ERROR,
            error_id="abc-123",
            timestamp="2025-01-01T00:00:00Z",
        )
        assert pd.type == "https://example.com/errors/test"
        assert pd.title == "Test Error"
        assert pd.status == 400
        assert pd.detail == "Something went wrong"
        assert pd.instance == "/api/v1/test"
        assert pd.error_code == ErrorCode.VALIDATION_ERROR
        assert pd.error_id == "abc-123"
        assert pd.timestamp == "2025-01-01T00:00:00Z"

    def test_optional_fields_default_none(self):
        pd = ProblemDetail(
            type="https://example.com/errors/test",
            title="Test",
            status=500,
            detail="error",
            instance="/test",
            error_code=ErrorCode.INTERNAL_ERROR,
            error_id="id-1",
            timestamp="2025-01-01T00:00:00Z",
        )
        assert pd.errors is None
        assert pd.stack_trace is None
        assert pd.request_id is None
        assert pd.fingerprint is None

    def test_optional_fields_populated(self):
        pd = ProblemDetail(
            type="https://example.com/errors/test",
            title="Test",
            status=422,
            detail="validation",
            instance="/test",
            error_code=ErrorCode.VALIDATION_ERROR,
            error_id="id-2",
            timestamp="2025-01-01T00:00:00Z",
            errors=[{"field": "email", "message": "required"}],
            stack_trace=["line 1", "line 2"],
            request_id="req-123",
            fingerprint="fp-abc",
        )
        assert pd.errors == [{"field": "email", "message": "required"}]
        assert pd.stack_trace == ["line 1", "line 2"]
        assert pd.request_id == "req-123"
        assert pd.fingerprint == "fp-abc"

    def test_status_code_min(self):
        pd = ProblemDetail(
            type="t",
            title="t",
            status=100,
            detail="d",
            instance="i",
            error_code=ErrorCode.INTERNAL_ERROR,
            error_id="id",
            timestamp="ts",
        )
        assert pd.status == 100

    def test_status_code_max(self):
        pd = ProblemDetail(
            type="t",
            title="t",
            status=599,
            detail="d",
            instance="i",
            error_code=ErrorCode.INTERNAL_ERROR,
            error_id="id",
            timestamp="ts",
        )
        assert pd.status == 599

    def test_model_dump_excludes_none(self):
        pd = ProblemDetail(
            type="t",
            title="t",
            status=400,
            detail="d",
            instance="i",
            error_code=ErrorCode.VALIDATION_ERROR,
            error_id="id",
            timestamp="ts",
        )
        dumped = pd.model_dump(exclude_none=True)
        assert "errors" not in dumped
        assert "stack_trace" not in dumped
        assert "request_id" not in dumped
        assert "fingerprint" not in dumped


# -- ErrorFormatter ----------------------------------------------------------


class TestErrorFormatterInit:
    def test_default_base_url(self):
        f = ErrorFormatter()
        assert "residency-scheduler" in f.base_url

    def test_custom_base_url(self):
        f = ErrorFormatter(base_url="https://custom.example.com")
        assert f.base_url == "https://custom.example.com"


class TestFormatError:
    def test_basic_error(self):
        f = ErrorFormatter()
        result = f.format_error(
            exc=ValueError("bad value"),
            status_code=400,
            error_code=ErrorCode.VALIDATION_ERROR,
            title="Validation Failed",
            request_path="/api/v1/test",
        )
        assert result["status"] == 400
        assert result["title"] == "Validation Failed"
        assert result["detail"] == "bad value"
        assert result["instance"] == "/api/v1/test"
        assert result["error_code"] == ErrorCode.VALIDATION_ERROR
        assert "error_id" in result
        assert "timestamp" in result
        assert "type" in result

    def test_type_uri_format(self):
        f = ErrorFormatter(base_url="https://api.test.com")
        result = f.format_error(
            exc=RuntimeError("x"),
            status_code=500,
            error_code=ErrorCode.INTERNAL_ERROR,
            title="Error",
            request_path="/test",
        )
        assert result["type"] == "https://api.test.com/errors/internal-error"

    def test_type_uri_underscore_to_hyphen(self):
        f = ErrorFormatter(base_url="https://api.test.com")
        result = f.format_error(
            exc=RuntimeError("x"),
            status_code=400,
            error_code=ErrorCode.VALIDATION_ERROR,
            title="Error",
            request_path="/test",
        )
        assert result["type"] == "https://api.test.com/errors/validation-error"

    def test_unique_error_ids(self):
        f = ErrorFormatter()
        r1 = f.format_error(ValueError("a"), 400, ErrorCode.VALIDATION_ERROR, "V", "/a")
        r2 = f.format_error(ValueError("b"), 400, ErrorCode.VALIDATION_ERROR, "V", "/b")
        assert r1["error_id"] != r2["error_id"]

    def test_timestamp_present(self):
        f = ErrorFormatter()
        result = f.format_error(
            ValueError("x"), 400, ErrorCode.VALIDATION_ERROR, "V", "/test"
        )
        assert result["timestamp"].endswith("Z")

    def test_request_id_included(self):
        f = ErrorFormatter()
        result = f.format_error(
            ValueError("x"),
            400,
            ErrorCode.VALIDATION_ERROR,
            "V",
            "/test",
            request_id="req-abc",
        )
        assert result["request_id"] == "req-abc"

    def test_fingerprint_included(self):
        f = ErrorFormatter()
        result = f.format_error(
            ValueError("x"),
            400,
            ErrorCode.VALIDATION_ERROR,
            "V",
            "/test",
            fingerprint="fp-xyz",
        )
        assert result["fingerprint"] == "fp-xyz"

    def test_include_details_true(self):
        f = ErrorFormatter()
        result = f.format_error(
            ValueError("sensitive info"),
            500,
            ErrorCode.INTERNAL_ERROR,
            "Error",
            "/test",
            include_details=True,
        )
        assert result["detail"] == "sensitive info"

    def test_include_details_false(self):
        f = ErrorFormatter()
        result = f.format_error(
            ValueError("sensitive info"),
            500,
            ErrorCode.INTERNAL_ERROR,
            "Error",
            "/test",
            include_details=False,
        )
        assert "sensitive" not in result["detail"]
        assert "contact support" in result["detail"].lower()

    def test_app_exception_with_message_attr(self):
        class AppException(Exception):
            def __init__(self, message):
                self.message = message
                super().__init__(message)

        f = ErrorFormatter()
        result = f.format_error(
            AppException("safe message"),
            400,
            ErrorCode.VALIDATION_ERROR,
            "Error",
            "/test",
            include_details=False,
        )
        # Should use .message attribute, not generic message
        assert result["detail"] == "safe message"

    def test_empty_exception_message(self):
        f = ErrorFormatter()
        result = f.format_error(
            ValueError(""),
            400,
            ErrorCode.VALIDATION_ERROR,
            "Error",
            "/test",
            include_details=True,
        )
        assert result["detail"] == "An error occurred"

    def test_excludes_none_fields(self):
        f = ErrorFormatter()
        result = f.format_error(
            ValueError("x"), 400, ErrorCode.VALIDATION_ERROR, "V", "/test"
        )
        assert "errors" not in result
        assert "stack_trace" not in result

    def test_stack_trace_included_when_requested(self):
        f = ErrorFormatter()
        try:
            raise ValueError("traceable")
        except ValueError as exc:
            result = f.format_error(
                exc,
                400,
                ErrorCode.VALIDATION_ERROR,
                "V",
                "/test",
                include_stack_trace=True,
            )
        assert "stack_trace" in result
        assert isinstance(result["stack_trace"], list)
        assert len(result["stack_trace"]) > 0

    def test_stack_trace_excluded_by_default(self):
        f = ErrorFormatter()
        try:
            raise ValueError("hidden")
        except ValueError as exc:
            result = f.format_error(
                exc,
                400,
                ErrorCode.VALIDATION_ERROR,
                "V",
                "/test",
            )
        assert "stack_trace" not in result

    def test_no_traceback_returns_empty_list(self):
        f = ErrorFormatter()
        result = f.format_error(
            ValueError("no tb"),
            400,
            ErrorCode.VALIDATION_ERROR,
            "V",
            "/test",
            include_stack_trace=True,
        )
        # ValueError created without raise has no traceback
        assert result.get("stack_trace") is None or result.get("stack_trace") == []


class TestFormatValidationErrors:
    def test_pydantic_validation_errors(self):
        class TestModel(BaseModel):
            name: str
            age: int

        f = ErrorFormatter()
        try:
            TestModel(name=123, age="not_int")  # type: ignore[arg-type]
        except PydanticValidationError as exc:
            result = f.format_error(
                exc,
                422,
                ErrorCode.VALIDATION_ERROR,
                "Validation Failed",
                "/test",
            )

        assert "errors" in result
        assert isinstance(result["errors"], list)
        assert len(result["errors"]) > 0
        # Each error should have field, message, type
        for err in result["errors"]:
            assert "field" in err
            assert "message" in err
            assert "type" in err

    def test_sensitive_field_input_redacted(self):
        class LoginModel(BaseModel):
            username: str
            password: str

        f = ErrorFormatter()
        try:
            LoginModel(username=123, password=456)  # type: ignore[arg-type]
        except PydanticValidationError as exc:
            result = f._format_validation_errors(exc)

        # Password field should NOT have input value
        password_errors = [e for e in result if "password" in e["field"].lower()]
        for err in password_errors:
            assert "input" not in err

    def test_non_sensitive_field_input_included(self):
        class TestModel(BaseModel):
            email: str

        f = ErrorFormatter()
        try:
            TestModel(email=12345)  # type: ignore[arg-type]
        except PydanticValidationError as exc:
            result = f._format_validation_errors(exc)

        email_errors = [e for e in result if "email" in e["field"]]
        # Non-sensitive fields may include input
        assert len(email_errors) > 0

    def test_input_truncated_to_100_chars(self):
        class TestModel(BaseModel):
            name: int

        f = ErrorFormatter()
        long_input = "x" * 200
        try:
            TestModel(name=long_input)  # type: ignore[arg-type]
        except PydanticValidationError as exc:
            result = f._format_validation_errors(exc)

        for err in result:
            if "input" in err:
                assert len(err["input"]) <= 100


# -- SimpleErrorFormatter ----------------------------------------------------


class TestSimpleErrorFormatter:
    def test_basic_error(self):
        result = SimpleErrorFormatter.format_simple_error("Bad request", 400)
        assert result == {"detail": "Bad request", "status_code": 400}

    def test_with_error_code(self):
        result = SimpleErrorFormatter.format_simple_error(
            "Not found", 404, error_code=ErrorCode.NOT_FOUND
        )
        assert result["error_code"] == "NOT_FOUND"

    def test_with_errors_list(self):
        errors = [{"field": "name", "message": "required"}]
        result = SimpleErrorFormatter.format_simple_error(
            "Validation failed", 422, errors=errors
        )
        assert result["errors"] == errors

    def test_no_error_code_omitted(self):
        result = SimpleErrorFormatter.format_simple_error("Error", 500)
        assert "error_code" not in result

    def test_no_errors_omitted(self):
        result = SimpleErrorFormatter.format_simple_error("Error", 500)
        assert "errors" not in result


# -- Global functions --------------------------------------------------------


class TestGlobalFunctions:
    def test_get_formatter_returns_instance(self):
        f = get_formatter()
        assert isinstance(f, ErrorFormatter)

    def test_get_formatter_singleton(self):
        f1 = get_formatter()
        f2 = get_formatter()
        assert f1 is f2

    def test_set_formatter(self):
        original = get_formatter()
        custom = ErrorFormatter(base_url="https://custom.example.com")
        set_formatter(custom)
        assert get_formatter() is custom
        # Restore
        set_formatter(original)

    def test_set_formatter_changes_global(self):
        custom = ErrorFormatter(base_url="https://test.example.com")
        set_formatter(custom)
        f = get_formatter()
        assert f.base_url == "https://test.example.com"
        # Restore default
        set_formatter(ErrorFormatter())
