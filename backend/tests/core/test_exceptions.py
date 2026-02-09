"""Tests for custom exception classes."""

import pytest

from app.core.exceptions import (
    ActivityNotFoundError,
    AppException,
    ConflictError,
    ForbiddenError,
    NotFoundError,
    UnauthorizedError,
    ValidationError,
)


# ==================== AppException ====================


class TestAppException:
    def test_default_status_code(self):
        e = AppException("test")
        assert e.status_code == 400

    def test_custom_status_code(self):
        e = AppException("test", status_code=500)
        assert e.status_code == 500

    def test_message(self):
        e = AppException("Something went wrong")
        assert e.message == "Something went wrong"

    def test_str(self):
        e = AppException("Something went wrong")
        assert str(e) == "Something went wrong"

    def test_is_exception(self):
        e = AppException("test")
        assert isinstance(e, Exception)

    def test_can_be_raised(self):
        with pytest.raises(AppException) as exc_info:
            raise AppException("boom")
        assert exc_info.value.message == "boom"


# ==================== NotFoundError ====================


class TestNotFoundError:
    def test_default_message(self):
        e = NotFoundError()
        assert e.message == "Resource not found"

    def test_custom_message(self):
        e = NotFoundError("User not found")
        assert e.message == "User not found"

    def test_status_code(self):
        e = NotFoundError()
        assert e.status_code == 404

    def test_is_app_exception(self):
        assert issubclass(NotFoundError, AppException)


# ==================== ValidationError ====================


class TestValidationError:
    def test_message(self):
        e = ValidationError("Invalid input")
        assert e.message == "Invalid input"

    def test_status_code(self):
        e = ValidationError("bad")
        assert e.status_code == 422

    def test_is_app_exception(self):
        assert issubclass(ValidationError, AppException)


# ==================== ConflictError ====================


class TestConflictError:
    def test_message(self):
        e = ConflictError("Already exists")
        assert e.message == "Already exists"

    def test_status_code(self):
        e = ConflictError("conflict")
        assert e.status_code == 409

    def test_is_app_exception(self):
        assert issubclass(ConflictError, AppException)


# ==================== UnauthorizedError ====================


class TestUnauthorizedError:
    def test_default_message(self):
        e = UnauthorizedError()
        assert e.message == "Authentication required"

    def test_custom_message(self):
        e = UnauthorizedError("Token expired")
        assert e.message == "Token expired"

    def test_status_code(self):
        e = UnauthorizedError()
        assert e.status_code == 401

    def test_is_app_exception(self):
        assert issubclass(UnauthorizedError, AppException)


# ==================== ForbiddenError ====================


class TestForbiddenError:
    def test_default_message(self):
        e = ForbiddenError()
        assert e.message == "Access forbidden"

    def test_custom_message(self):
        e = ForbiddenError("Admin only")
        assert e.message == "Admin only"

    def test_status_code(self):
        e = ForbiddenError()
        assert e.status_code == 403

    def test_is_app_exception(self):
        assert issubclass(ForbiddenError, AppException)


# ==================== ActivityNotFoundError ====================


class TestActivityNotFoundError:
    def test_code_stored(self):
        e = ActivityNotFoundError("LEC")
        assert e.code == "LEC"

    def test_default_no_context(self):
        e = ActivityNotFoundError("LEC")
        assert e.context == ""

    def test_message_includes_code(self):
        e = ActivityNotFoundError("LEC")
        assert "LEC" in e.message

    def test_message_includes_preflight(self):
        e = ActivityNotFoundError("LEC")
        assert "preflight" in e.message

    def test_context_included(self):
        e = ActivityNotFoundError("FMIT", context="Block 10 generation")
        assert "Block 10 generation" in e.message
        assert e.context == "Block 10 generation"

    def test_status_code(self):
        e = ActivityNotFoundError("C")
        assert e.status_code == 422

    def test_is_app_exception(self):
        assert issubclass(ActivityNotFoundError, AppException)


# ==================== Exception Hierarchy ====================


class TestExceptionHierarchy:
    def test_all_inherit_from_app_exception(self):
        for cls in [
            NotFoundError,
            ValidationError,
            ConflictError,
            UnauthorizedError,
            ForbiddenError,
            ActivityNotFoundError,
        ]:
            assert issubclass(cls, AppException), (
                f"{cls.__name__} must inherit AppException"
            )

    def test_all_inherit_from_exception(self):
        for cls in [
            AppException,
            NotFoundError,
            ValidationError,
            ConflictError,
            UnauthorizedError,
            ForbiddenError,
            ActivityNotFoundError,
        ]:
            assert issubclass(cls, Exception), f"{cls.__name__} must inherit Exception"

    def test_catch_by_base_class(self):
        """All app exceptions catchable via AppException."""
        exceptions = [
            NotFoundError(),
            ValidationError("bad"),
            ConflictError("dup"),
            UnauthorizedError(),
            ForbiddenError(),
            ActivityNotFoundError("X"),
        ]
        for e in exceptions:
            with pytest.raises(AppException):
                raise e
