"""Tests for common validation functions (no DB)."""

from __future__ import annotations

import uuid

import pytest

from app.validators.common import (
    ValidationError,
    validate_email_address,
    validate_enum_value,
    validate_float_range,
    validate_integer_range,
    validate_military_id,
    validate_name,
    validate_non_empty_list,
    validate_phone_number,
    validate_string_length,
    validate_uuid,
)


# ---------------------------------------------------------------------------
# ValidationError
# ---------------------------------------------------------------------------


class TestValidationError:
    def test_is_exception(self):
        with pytest.raises(ValidationError):
            raise ValidationError("test")

    def test_message(self):
        err = ValidationError("bad input")
        assert str(err) == "bad input"

    def test_is_base_exception_subclass(self):
        assert issubclass(ValidationError, Exception)


# ---------------------------------------------------------------------------
# validate_email_address
# ---------------------------------------------------------------------------


class TestValidateEmailAddress:
    def test_valid_email(self):
        assert validate_email_address("user@example.com") == "user@example.com"

    def test_uppercase_normalized(self):
        result = validate_email_address("User@EXAMPLE.COM")
        assert result == "user@example.com"

    def test_empty_raises(self):
        with pytest.raises(ValidationError, match="cannot be empty"):
            validate_email_address("")

    def test_invalid_format(self):
        with pytest.raises(ValidationError, match="Invalid email"):
            validate_email_address("not-an-email")

    def test_missing_domain(self):
        with pytest.raises(ValidationError):
            validate_email_address("user@")

    def test_missing_local(self):
        with pytest.raises(ValidationError):
            validate_email_address("@example.com")

    def test_with_plus(self):
        result = validate_email_address("user+tag@example.com")
        assert result == "user+tag@example.com"


# ---------------------------------------------------------------------------
# validate_phone_number
# ---------------------------------------------------------------------------


class TestValidatePhoneNumber:
    def test_us_10_digits(self):
        assert validate_phone_number("5551234567") == "5551234567"

    def test_formatted_us(self):
        assert validate_phone_number("(555) 123-4567") == "5551234567"

    def test_us_with_country_code(self):
        assert validate_phone_number("+1-555-123-4567") == "15551234567"

    def test_dotted_format(self):
        assert validate_phone_number("555.123.4567") == "5551234567"

    def test_empty_raises(self):
        with pytest.raises(ValidationError, match="cannot be empty"):
            validate_phone_number("")

    def test_too_few_digits(self):
        with pytest.raises(ValidationError):
            validate_phone_number("12345")

    def test_letters_raise(self):
        with pytest.raises(ValidationError, match="invalid characters"):
            validate_phone_number("555-abc-1234")

    def test_international_7_digits(self):
        result = validate_phone_number("1234567", allow_international=True)
        assert result == "1234567"

    def test_international_disabled_short(self):
        with pytest.raises(ValidationError):
            validate_phone_number("1234567", allow_international=False)


# ---------------------------------------------------------------------------
# validate_name
# ---------------------------------------------------------------------------


class TestValidateName:
    def test_simple_name(self):
        assert validate_name("John Smith") == "John Smith"

    def test_hyphenated(self):
        assert validate_name("Jean-Pierre") == "Jean-Pierre"

    def test_apostrophe(self):
        assert validate_name("O'Brien") == "O'Brien"

    def test_with_period(self):
        assert validate_name("Dr. Smith") == "Dr. Smith"

    def test_unicode(self):
        assert validate_name("José María") == "José María"

    def test_strips_whitespace(self):
        assert validate_name("  John  ") == "John"

    def test_empty_raises(self):
        with pytest.raises(ValidationError, match="cannot be empty"):
            validate_name("")

    def test_too_short(self):
        with pytest.raises(ValidationError, match="too short"):
            validate_name("A", min_length=2)

    def test_too_long(self):
        with pytest.raises(ValidationError, match="too long"):
            validate_name("A" * 300, max_length=255)

    def test_sql_injection_semicolon(self):
        with pytest.raises(ValidationError, match="invalid characters"):
            validate_name("Robert; DROP TABLE users")

    def test_sql_injection_union(self):
        with pytest.raises(ValidationError, match="suspicious"):
            validate_name("x' union select 1")

    def test_sql_injection_comment(self):
        with pytest.raises(ValidationError, match="suspicious"):
            validate_name("admin'--")

    def test_special_chars_rejected(self):
        with pytest.raises(ValidationError, match="invalid characters"):
            validate_name("John@Smith")


# ---------------------------------------------------------------------------
# validate_uuid
# ---------------------------------------------------------------------------


class TestValidateUuid:
    def test_uuid_object(self):
        u = uuid.uuid4()
        assert validate_uuid(u) == u

    def test_uuid_string(self):
        u = uuid.uuid4()
        result = validate_uuid(str(u))
        assert result == u

    def test_empty_raises(self):
        with pytest.raises(ValidationError, match="cannot be empty"):
            validate_uuid("")

    def test_invalid_format(self):
        with pytest.raises(ValidationError, match="Invalid UUID"):
            validate_uuid("not-a-uuid")

    def test_partial_uuid_raises(self):
        with pytest.raises(ValidationError):
            validate_uuid("12345678-1234")


# ---------------------------------------------------------------------------
# validate_integer_range
# ---------------------------------------------------------------------------


class TestValidateIntegerRange:
    def test_within_range(self):
        assert validate_integer_range(5, min_value=1, max_value=10) == 5

    def test_at_min(self):
        assert validate_integer_range(1, min_value=1) == 1

    def test_at_max(self):
        assert validate_integer_range(10, max_value=10) == 10

    def test_below_min(self):
        with pytest.raises(ValidationError, match="at least"):
            validate_integer_range(0, min_value=1, field_name="Score")

    def test_above_max(self):
        with pytest.raises(ValidationError, match="at most"):
            validate_integer_range(11, max_value=10, field_name="Score")

    def test_no_bounds(self):
        assert validate_integer_range(999) == 999

    def test_non_integer_raises(self):
        with pytest.raises(ValidationError, match="must be an integer"):
            validate_integer_range(3.5, min_value=1)  # type: ignore[arg-type]

    def test_field_name_in_error(self):
        with pytest.raises(ValidationError, match="PGY level"):
            validate_integer_range(0, min_value=1, field_name="PGY level")


# ---------------------------------------------------------------------------
# validate_float_range
# ---------------------------------------------------------------------------


class TestValidateFloatRange:
    def test_within_range(self):
        assert validate_float_range(0.5, min_value=0.0, max_value=1.0) == 0.5

    def test_at_min(self):
        assert validate_float_range(0.0, min_value=0.0) == 0.0

    def test_at_max(self):
        assert validate_float_range(1.0, max_value=1.0) == 1.0

    def test_below_min(self):
        with pytest.raises(ValidationError, match="at least"):
            validate_float_range(-0.1, min_value=0.0)

    def test_above_max(self):
        with pytest.raises(ValidationError, match="at most"):
            validate_float_range(1.1, max_value=1.0)

    def test_int_accepted_as_float(self):
        result = validate_float_range(5, min_value=0.0)
        assert result == 5.0
        assert isinstance(result, float)

    def test_non_number_raises(self):
        with pytest.raises(ValidationError, match="must be a number"):
            validate_float_range("abc", min_value=0.0)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# validate_string_length
# ---------------------------------------------------------------------------


class TestValidateStringLength:
    def test_within_range(self):
        assert validate_string_length("hello", min_length=1, max_length=10) == "hello"

    def test_at_min(self):
        assert validate_string_length("ab", min_length=2) == "ab"

    def test_at_max(self):
        assert validate_string_length("abc", max_length=3) == "abc"

    def test_below_min(self):
        with pytest.raises(ValidationError, match="at least"):
            validate_string_length("a", min_length=2)

    def test_above_max(self):
        with pytest.raises(ValidationError, match="at most"):
            validate_string_length("abcdef", max_length=3)

    def test_non_string_raises(self):
        with pytest.raises(ValidationError, match="must be a string"):
            validate_string_length(123, min_length=1)  # type: ignore[arg-type]

    def test_field_name_in_error(self):
        with pytest.raises(ValidationError, match="Specialty"):
            validate_string_length("x", min_length=2, field_name="Specialty")


# ---------------------------------------------------------------------------
# validate_enum_value
# ---------------------------------------------------------------------------


class TestValidateEnumValue:
    def test_valid_value(self):
        assert validate_enum_value("a", ["a", "b", "c"]) == "a"

    def test_invalid_value(self):
        with pytest.raises(ValidationError, match="must be one of"):
            validate_enum_value("d", ["a", "b", "c"])

    def test_integer_values(self):
        assert validate_enum_value(1, [1, 2, 3]) == 1

    def test_field_name_in_error(self):
        with pytest.raises(ValidationError, match="Status"):
            validate_enum_value("x", ["a"], field_name="Status")


# ---------------------------------------------------------------------------
# validate_military_id
# ---------------------------------------------------------------------------


class TestValidateMilitaryId:
    def test_valid_10_digits(self):
        assert validate_military_id("1234567890") == "1234567890"

    def test_with_spaces(self):
        assert validate_military_id("123 456 7890") == "1234567890"

    def test_with_hyphens(self):
        assert validate_military_id("123-456-7890") == "1234567890"

    def test_empty_raises(self):
        with pytest.raises(ValidationError, match="cannot be empty"):
            validate_military_id("")

    def test_too_few_digits(self):
        with pytest.raises(ValidationError, match="10 digits"):
            validate_military_id("12345")

    def test_too_many_digits(self):
        with pytest.raises(ValidationError, match="10 digits"):
            validate_military_id("12345678901")

    def test_letters_raise(self):
        with pytest.raises(ValidationError, match="10 digits"):
            validate_military_id("123456789a")


# ---------------------------------------------------------------------------
# validate_non_empty_list
# ---------------------------------------------------------------------------


class TestValidateNonEmptyList:
    def test_valid_list(self):
        result = validate_non_empty_list([1, 2, 3])
        assert result == [1, 2, 3]

    def test_single_item(self):
        assert validate_non_empty_list(["a"]) == ["a"]

    def test_empty_raises(self):
        with pytest.raises(ValidationError, match="cannot be empty"):
            validate_non_empty_list([])

    def test_not_a_list_raises(self):
        with pytest.raises(ValidationError, match="must be a list"):
            validate_non_empty_list("not a list")  # type: ignore[arg-type]

    def test_field_name_in_error(self):
        with pytest.raises(ValidationError, match="Residents"):
            validate_non_empty_list([], field_name="Residents")

    def test_tuple_raises(self):
        with pytest.raises(ValidationError, match="must be a list"):
            validate_non_empty_list((1, 2))  # type: ignore[arg-type]
