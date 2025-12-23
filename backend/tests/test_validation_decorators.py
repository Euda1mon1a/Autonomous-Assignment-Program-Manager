"""
Tests for request validation decorators.

Validates decorator functionality including query validation, body validation,
cross-field validation, and error handling.
"""

from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from app.validation import (
    email_format,
    enum_values,
    numeric_range,
    person_type_rule,
    pgy_level_rule,
    required,
    string_length,
    validate_body,
    validate_conditional_field,
    validate_pagination,
    validate_query,
    validate_request,
)

# Test FastAPI app
app = FastAPI()


@app.get("/test-query")
@validate_query(
    {
        "page": [required, numeric_range(min_value=1)],
        "limit": [numeric_range(min_value=1, max_value=100)],
    }
)
def test_query_validation(page: int, limit: int = 20):
    """Test endpoint with query validation."""
    return {"page": page, "limit": limit}


@app.post("/test-body")
@validate_body(
    {
        "name": [required, string_length(min_length=1, max_length=100)],
        "email": [required, email_format()],
    }
)
async def test_body_validation(request: Request):
    """Test endpoint with body validation."""
    body = await request.json()
    return body


@app.post("/test-cross-field")
@validate_request(
    body_rules={"start_date": [required], "end_date": [required]},
    cross_field_validator=lambda data, ctx: (
        ctx.add_field_error("end_date", "Must be after start date")
        if data.get("start_date")
        and data.get("end_date")
        and data["start_date"] > data["end_date"]
        else None
    ),
)
async def test_cross_field_validation(request: Request):
    """Test endpoint with cross-field validation."""
    body = await request.json()
    return body


@app.get("/test-pagination")
@validate_pagination(max_limit=50)
def test_pagination_validation(page: int = 1, limit: int = 20):
    """Test endpoint with pagination validation."""
    return {"page": page, "limit": limit}


@app.post("/test-person")
@validate_body(
    {
        "name": [required, string_length(min_length=1)],
        "type": [required, person_type_rule()],
        "pgy_level": [],  # Conditionally required
    }
)
@validate_conditional_field(
    field="pgy_level",
    condition_field="type",
    condition_value="resident",
    rules=[required, pgy_level_rule()],
)
async def test_conditional_validation(request: Request):
    """Test endpoint with conditional field validation."""
    body = await request.json()
    return body


client = TestClient(app)


class TestQueryValidation:
    """Tests for query parameter validation."""

    def test_valid_query_params(self):
        """Test validation passes with valid query parameters."""
        response = client.get("/test-query?page=1&limit=20")
        assert response.status_code == 200
        assert response.json() == {"page": 1, "limit": 20}

    def test_missing_required_param(self):
        """Test validation fails when required param is missing."""
        response = client.get("/test-query")
        assert response.status_code == 422
        data = response.json()
        assert "errors" in data["detail"]
        errors = data["detail"]["errors"]
        assert any(e["field"] == "page" for e in errors)

    def test_param_below_min(self):
        """Test validation fails when param is below minimum."""
        response = client.get("/test-query?page=0")
        assert response.status_code == 422
        data = response.json()
        errors = data["detail"]["errors"]
        assert any(e["field"] == "page" for e in errors)

    def test_param_above_max(self):
        """Test validation fails when param exceeds maximum."""
        response = client.get("/test-query?page=1&limit=200")
        assert response.status_code == 422
        data = response.json()
        errors = data["detail"]["errors"]
        assert any(e["field"] == "limit" for e in errors)

    def test_optional_param_valid(self):
        """Test optional param with default value."""
        response = client.get("/test-query?page=1")
        assert response.status_code == 200
        assert response.json() == {"page": 1, "limit": 20}


class TestBodyValidation:
    """Tests for request body validation."""

    def test_valid_body(self):
        """Test validation passes with valid body."""
        response = client.post(
            "/test-body", json={"name": "John Doe", "email": "john@example.com"}
        )
        assert response.status_code == 200

    def test_missing_required_field(self):
        """Test validation fails when required field is missing."""
        response = client.post("/test-body", json={"name": "John Doe"})
        assert response.status_code == 422
        data = response.json()
        errors = data["detail"]["errors"]
        assert any(e["field"] == "email" for e in errors)

    def test_invalid_email_format(self):
        """Test validation fails with invalid email format."""
        response = client.post(
            "/test-body", json={"name": "John Doe", "email": "invalid-email"}
        )
        assert response.status_code == 422
        data = response.json()
        errors = data["detail"]["errors"]
        assert any(e["field"] == "email" for e in errors)

    def test_string_too_long(self):
        """Test validation fails when string exceeds max length."""
        long_name = "a" * 101
        response = client.post(
            "/test-body", json={"name": long_name, "email": "john@example.com"}
        )
        assert response.status_code == 422
        data = response.json()
        errors = data["detail"]["errors"]
        assert any(e["field"] == "name" for e in errors)

    def test_empty_string_fails_required(self):
        """Test validation fails when required field is empty string."""
        response = client.post(
            "/test-body", json={"name": "", "email": "john@example.com"}
        )
        assert response.status_code == 422
        data = response.json()
        errors = data["detail"]["errors"]
        assert any(e["field"] == "name" for e in errors)


class TestCrossFieldValidation:
    """Tests for cross-field validation."""

    def test_valid_date_range(self):
        """Test validation passes with valid date range."""
        response = client.post(
            "/test-cross-field",
            json={"start_date": "2024-01-01", "end_date": "2024-12-31"},
        )
        assert response.status_code == 200

    def test_invalid_date_range(self):
        """Test validation fails when end date is before start date."""
        response = client.post(
            "/test-cross-field",
            json={"start_date": "2024-12-31", "end_date": "2024-01-01"},
        )
        assert response.status_code == 422
        data = response.json()
        errors = data["detail"]["errors"]
        assert any(e["field"] == "end_date" for e in errors)

    def test_missing_field_for_cross_validation(self):
        """Test cross-field validation when one field is missing."""
        response = client.post("/test-cross-field", json={"start_date": "2024-01-01"})
        assert response.status_code == 422
        # Should fail on required validation, not cross-field


class TestPaginationValidation:
    """Tests for pagination validation."""

    def test_default_pagination(self):
        """Test pagination with default values."""
        response = client.get("/test-pagination")
        assert response.status_code == 200

    def test_custom_pagination(self):
        """Test pagination with custom values."""
        response = client.get("/test-pagination?page=2&limit=30")
        assert response.status_code == 200

    def test_pagination_exceeds_max(self):
        """Test pagination fails when limit exceeds maximum."""
        response = client.get("/test-pagination?page=1&limit=100")
        assert response.status_code == 422

    def test_pagination_invalid_page(self):
        """Test pagination fails with invalid page number."""
        response = client.get("/test-pagination?page=0")
        assert response.status_code == 422


class TestConditionalValidation:
    """Tests for conditional field validation."""

    def test_resident_requires_pgy_level(self):
        """Test that pgy_level is required for residents."""
        response = client.post(
            "/test-person", json={"name": "John Doe", "type": "resident"}
        )
        assert response.status_code == 422
        data = response.json()
        errors = data["detail"]["errors"]
        assert any(e["field"] == "pgy_level" for e in errors)

    def test_resident_with_valid_pgy_level(self):
        """Test resident with valid pgy_level."""
        response = client.post(
            "/test-person",
            json={"name": "John Doe", "type": "resident", "pgy_level": 2},
        )
        assert response.status_code == 200

    def test_resident_with_invalid_pgy_level(self):
        """Test resident with invalid pgy_level."""
        response = client.post(
            "/test-person",
            json={"name": "John Doe", "type": "resident", "pgy_level": 5},
        )
        assert response.status_code == 422

    def test_faculty_does_not_require_pgy_level(self):
        """Test that pgy_level is not required for faculty."""
        response = client.post(
            "/test-person", json={"name": "Dr. Smith", "type": "faculty"}
        )
        assert response.status_code == 200


class TestValidationContext:
    """Tests for validation context."""

    def test_context_accumulates_errors(self):
        """Test that context accumulates multiple errors."""
        from app.validation import validation_scope

        with validation_scope() as ctx:
            ctx.add_field_error("field1", "Error 1")
            ctx.add_field_error("field2", "Error 2")

            assert ctx.has_errors()
            assert len(ctx.get_errors()) == 2

    def test_context_error_dict(self):
        """Test getting errors as dictionary."""
        from app.validation import validation_scope

        with validation_scope() as ctx:
            ctx.add_field_error("email", "Invalid format")
            ctx.add_field_error("email", "Already exists")
            ctx.add_field_error("name", "Required")

            error_dict = ctx.get_error_dict()
            assert "email" in error_dict
            assert "name" in error_dict
            assert len(error_dict["email"]) == 2
            assert len(error_dict["name"]) == 1

    def test_context_data_storage(self):
        """Test storing and retrieving data in context."""
        from app.validation import validation_scope

        with validation_scope() as ctx:
            ctx.set_data("user_id", "123")
            ctx.set_data("role", "admin")

            assert ctx.get_data("user_id") == "123"
            assert ctx.get_data("role") == "admin"
            assert ctx.get_data("missing", "default") == "default"
            assert ctx.has_data("user_id")
            assert not ctx.has_data("missing")


class TestValidationRules:
    """Tests for individual validation rules."""

    def test_string_length_rule(self):
        """Test string length validation rule."""
        from app.validation import validation_scope

        rule = string_length(min_length=3, max_length=10)

        with validation_scope() as ctx:
            assert rule("name", "test", ctx)
            assert not ctx.has_errors()

        with validation_scope() as ctx:
            assert not rule("name", "ab", ctx)
            assert ctx.has_errors()

        with validation_scope() as ctx:
            assert not rule("name", "a" * 11, ctx)
            assert ctx.has_errors()

    def test_numeric_range_rule(self):
        """Test numeric range validation rule."""
        from app.validation import validation_scope

        rule = numeric_range(min_value=1, max_value=100)

        with validation_scope() as ctx:
            assert rule("age", 25, ctx)
            assert not ctx.has_errors()

        with validation_scope() as ctx:
            assert not rule("age", 0, ctx)
            assert ctx.has_errors()

        with validation_scope() as ctx:
            assert not rule("age", 101, ctx)
            assert ctx.has_errors()

    def test_enum_values_rule(self):
        """Test enum values validation rule."""
        from app.validation import validation_scope

        rule = enum_values(["red", "green", "blue"])

        with validation_scope() as ctx:
            assert rule("color", "red", ctx)
            assert not ctx.has_errors()

        with validation_scope() as ctx:
            assert not rule("color", "yellow", ctx)
            assert ctx.has_errors()

    def test_email_format_rule(self):
        """Test email format validation rule."""
        from app.validation import validation_scope

        rule = email_format()

        with validation_scope() as ctx:
            assert rule("email", "test@example.com", ctx)
            assert not ctx.has_errors()

        with validation_scope() as ctx:
            assert not rule("email", "invalid-email", ctx)
            assert ctx.has_errors()

    def test_all_of_combinator(self):
        """Test all_of rule combinator."""
        from app.validation import all_of, validation_scope

        rule = all_of(
            required, string_length(min_length=3), enum_values(["test", "demo"])
        )

        with validation_scope() as ctx:
            assert rule("field", "test", ctx)
            assert not ctx.has_errors()

        with validation_scope() as ctx:
            assert not rule("field", "ab", ctx)  # Too short
            assert ctx.has_errors()

        with validation_scope() as ctx:
            assert not rule("field", "invalid", ctx)  # Not in enum
            assert ctx.has_errors()


class TestErrorMessages:
    """Tests for error message formatting."""

    def test_field_name_formatting(self):
        """Test field name formatting for display."""
        from app.validation import format_field_name

        assert format_field_name("first_name") == "First Name"
        assert format_field_name("pgy_level") == "PGY Level"
        assert format_field_name("email") == "Email"

    def test_localized_messages(self):
        """Test localized error messages."""
        from app.validation import Locale, ValidationMessageType, get_error_message

        # English
        msg = get_error_message(
            ValidationMessageType.REQUIRED, Locale.EN_US, field="Name"
        )
        assert "required" in msg.lower()

        # Spanish
        msg = get_error_message(
            ValidationMessageType.REQUIRED, Locale.ES_ES, field="Nombre"
        )
        assert "requerido" in msg.lower()

    def test_error_message_parameters(self):
        """Test error messages with parameters."""
        from app.validation import Locale, ValidationMessageType, get_error_message

        msg = get_error_message(
            ValidationMessageType.OUT_OF_RANGE,
            Locale.EN_US,
            field="Age",
            min_value=18,
            max_value=65,
        )
        assert "18" in msg
        assert "65" in msg
