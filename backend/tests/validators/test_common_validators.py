"""Tests for common validators (pure logic, no DB)."""

import uuid

import pytest

from app.validators.common import (
    ValidationError,
    validate_email_address,
    validate_phone_number,
    validate_name,
    validate_uuid,
    validate_integer_range,
    validate_float_range,
    validate_string_length,
    validate_enum_value,
    validate_military_id,
    validate_non_empty_list,
)


# ── validate_email_address ───────────────────────────────────────────────


class TestValidateEmailAddress:
    def test_valid_email(self):
        assert validate_email_address("user@example.com") == "user@example.com"

    def test_normalises_to_lowercase(self):
        result = validate_email_address("User@Example.COM")
        assert result == "user@example.com"

    def test_empty_string(self):
        with pytest.raises(ValidationError, match="empty"):
            validate_email_address("")

    def test_invalid_format(self):
        with pytest.raises(ValidationError, match="Invalid email"):
            validate_email_address("not-an-email")

    def test_missing_domain(self):
        with pytest.raises(ValidationError, match="Invalid email"):
            validate_email_address("user@")

    def test_missing_local(self):
        with pytest.raises(ValidationError, match="Invalid email"):
            validate_email_address("@example.com")


# ── validate_phone_number ────────────────────────────────────────────────


class TestValidatePhoneNumber:
    def test_us_10_digit(self):
        assert validate_phone_number("5551234567") == "5551234567"

    def test_us_formatted(self):
        assert validate_phone_number("(555) 123-4567") == "5551234567"

    def test_us_with_country_code(self):
        assert validate_phone_number("+1-555-123-4567") == "15551234567"

    def test_us_dotted(self):
        assert validate_phone_number("555.123.4567") == "5551234567"

    def test_international_7_digits(self):
        assert validate_phone_number("1234567") == "1234567"

    def test_international_15_digits(self):
        result = validate_phone_number("123456789012345")
        assert result == "123456789012345"

    def test_international_disabled(self):
        with pytest.raises(ValidationError, match="length"):
            validate_phone_number("1234567", allow_international=False)

    def test_empty(self):
        with pytest.raises(ValidationError, match="empty"):
            validate_phone_number("")

    def test_invalid_characters(self):
        with pytest.raises(ValidationError, match="invalid characters"):
            validate_phone_number("555-ABC-1234")

    def test_too_short_us(self):
        with pytest.raises(ValidationError, match="length"):
            validate_phone_number("12345", allow_international=False)


# ── validate_name ────────────────────────────────────────────────────────


class TestValidateName:
    def test_simple_name(self):
        assert validate_name("John Smith") == "John Smith"

    def test_hyphenated(self):
        assert validate_name("Jean-Pierre") == "Jean-Pierre"

    def test_apostrophe(self):
        assert validate_name("O'Brien") == "O'Brien"

    def test_with_period(self):
        assert validate_name("Dr. Smith") == "Dr. Smith"

    def test_trims_whitespace(self):
        assert validate_name("  John  ") == "John"

    def test_empty(self):
        with pytest.raises(ValidationError, match="empty"):
            validate_name("")

    def test_too_short(self):
        with pytest.raises(ValidationError, match="too short"):
            validate_name("A", min_length=2)

    def test_too_long(self):
        with pytest.raises(ValidationError, match="too long"):
            validate_name("x" * 256, max_length=255)

    def test_invalid_characters(self):
        with pytest.raises(ValidationError, match="invalid characters"):
            validate_name("John<script>")

    def test_sql_injection_select(self):
        with pytest.raises(ValidationError):
            validate_name("'; select * from users --")

    def test_sql_injection_union(self):
        with pytest.raises(ValidationError):
            validate_name("test; union select")

    def test_sql_injection_comment(self):
        with pytest.raises(ValidationError):
            validate_name("test; -- comment")


# ── validate_uuid ────────────────────────────────────────────────────────


class TestValidateUUID:
    def test_valid_string(self):
        uid = "550e8400-e29b-41d4-a716-446655440000"
        result = validate_uuid(uid)
        assert isinstance(result, uuid.UUID)
        assert str(result) == uid

    def test_uuid_object(self):
        uid = uuid.uuid4()
        assert validate_uuid(uid) is uid

    def test_empty(self):
        with pytest.raises(ValidationError, match="empty"):
            validate_uuid("")

    def test_invalid_format(self):
        with pytest.raises(ValidationError, match="Invalid UUID"):
            validate_uuid("not-a-uuid")


# ── validate_integer_range ───────────────────────────────────────────────


class TestValidateIntegerRange:
    def test_in_range(self):
        assert validate_integer_range(5, min_value=1, max_value=10) == 5

    def test_at_min(self):
        assert validate_integer_range(1, min_value=1) == 1

    def test_at_max(self):
        assert validate_integer_range(10, max_value=10) == 10

    def test_below_min(self):
        with pytest.raises(ValidationError, match="at least"):
            validate_integer_range(0, min_value=1)

    def test_above_max(self):
        with pytest.raises(ValidationError, match="at most"):
            validate_integer_range(11, max_value=10)

    def test_not_integer(self):
        with pytest.raises(ValidationError, match="integer"):
            validate_integer_range("5")

    def test_no_bounds(self):
        assert validate_integer_range(999) == 999

    def test_custom_field_name(self):
        with pytest.raises(ValidationError, match="Age"):
            validate_integer_range(0, min_value=1, field_name="Age")


# ── validate_float_range ────────────────────────────────────────────────


class TestValidateFloatRange:
    def test_in_range(self):
        assert validate_float_range(5.5, min_value=0.0, max_value=10.0) == 5.5

    def test_at_min(self):
        assert validate_float_range(0.0, min_value=0.0) == 0.0

    def test_at_max(self):
        assert validate_float_range(10.0, max_value=10.0) == 10.0

    def test_below_min(self):
        with pytest.raises(ValidationError, match="at least"):
            validate_float_range(-0.1, min_value=0.0)

    def test_above_max(self):
        with pytest.raises(ValidationError, match="at most"):
            validate_float_range(10.1, max_value=10.0)

    def test_int_coerced_to_float(self):
        result = validate_float_range(5)
        assert result == 5.0
        assert isinstance(result, float)

    def test_not_numeric(self):
        with pytest.raises(ValidationError, match="number"):
            validate_float_range("5.0")


# ── validate_string_length ──────────────────────────────────────────────


class TestValidateStringLength:
    def test_in_range(self):
        assert validate_string_length("hello", min_length=1, max_length=10) == "hello"

    def test_too_short(self):
        with pytest.raises(ValidationError, match="at least"):
            validate_string_length("", min_length=1)

    def test_too_long(self):
        with pytest.raises(ValidationError, match="at most"):
            validate_string_length("x" * 11, max_length=10)

    def test_not_string(self):
        with pytest.raises(ValidationError, match="string"):
            validate_string_length(123)

    def test_no_bounds(self):
        assert validate_string_length("anything") == "anything"


# ── validate_enum_value ─────────────────────────────────────────────────


class TestValidateEnumValue:
    def test_valid(self):
        assert validate_enum_value("red", ["red", "green", "blue"]) == "red"

    def test_invalid(self):
        with pytest.raises(ValidationError, match="one of"):
            validate_enum_value("yellow", ["red", "green", "blue"])

    def test_integer_enum(self):
        assert validate_enum_value(1, [1, 2, 3]) == 1


# ── validate_military_id ────────────────────────────────────────────────


class TestValidateMilitaryId:
    def test_valid_10_digits(self):
        assert validate_military_id("1234567890") == "1234567890"

    def test_with_spaces(self):
        assert validate_military_id("123 456 7890") == "1234567890"

    def test_with_hyphens(self):
        assert validate_military_id("123-456-7890") == "1234567890"

    def test_empty(self):
        with pytest.raises(ValidationError, match="empty"):
            validate_military_id("")

    def test_wrong_length(self):
        with pytest.raises(ValidationError, match="10 digits"):
            validate_military_id("12345")

    def test_non_numeric(self):
        with pytest.raises(ValidationError, match="10 digits"):
            validate_military_id("12345ABCDE")


# ── validate_non_empty_list ─────────────────────────────────────────────


class TestValidateNonEmptyList:
    def test_non_empty(self):
        assert validate_non_empty_list([1, 2, 3]) == [1, 2, 3]

    def test_empty(self):
        with pytest.raises(ValidationError, match="empty"):
            validate_non_empty_list([])

    def test_not_list(self):
        with pytest.raises(ValidationError, match="list"):
            validate_non_empty_list("not a list")

    def test_single_item(self):
        assert validate_non_empty_list(["a"]) == ["a"]
