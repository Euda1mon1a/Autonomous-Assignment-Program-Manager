"""Tests for notification template validators."""

import pytest

from app.notifications.templates.validators import (
    TemplateValidator,
    ValidationError,
    validate_template_syntax,
)


class TestTemplateValidator:
    """Test suite for template validator."""

    def test_validate_syntax_valid(self):
        """Test validation of valid template syntax."""
        validator = TemplateValidator()
        template = "Hello {{ name }}!"

        assert validator.validate_template_syntax(template) is True

    def test_validate_syntax_invalid(self):
        """Test validation of invalid template syntax."""
        validator = TemplateValidator()
        template = "Hello {{ name }!"  # Missing closing brace

        with pytest.raises(ValidationError) as exc_info:
            validator.validate_template_syntax(template)

        assert "syntax error" in str(exc_info.value).lower()
        assert exc_info.value.field == "template_syntax"

    def test_validate_subject_template_valid(self):
        """Test validation of valid subject template."""
        validator = TemplateValidator()
        subject = "Meeting Reminder: {{ meeting_name }}"

        assert validator.validate_subject_template(subject) is True

    def test_validate_subject_template_too_long(self):
        """Test validation of subject template exceeding max length."""
        validator = TemplateValidator()
        subject = "A" * (validator.MAX_SUBJECT_LENGTH + 1)

        with pytest.raises(ValidationError) as exc_info:
            validator.validate_subject_template(subject)

        assert "exceeds maximum length" in str(exc_info.value).lower()
        assert exc_info.value.field == "subject_template"

    def test_validate_subject_template_with_newlines(self):
        """Test validation rejects subject templates with newlines."""
        validator = TemplateValidator()
        subject = "Hello {{ name }}\nSecond line"

        with pytest.raises(ValidationError) as exc_info:
            validator.validate_subject_template(subject)

        assert "should not contain newlines" in str(exc_info.value).lower()

    def test_validate_body_template_valid(self):
        """Test validation of valid body template."""
        validator = TemplateValidator()
        body = "<p>Hello {{ name }},</p><p>Welcome to our system!</p>"

        assert validator.validate_body_template(body, template_type="html") is True

    def test_validate_body_template_too_long(self):
        """Test validation of body template exceeding max length."""
        validator = TemplateValidator()
        body = "A" * (validator.MAX_TEMPLATE_LENGTH + 1)

        with pytest.raises(ValidationError) as exc_info:
            validator.validate_body_template(body)

        assert "exceeds maximum length" in str(exc_info.value).lower()

    def test_validate_required_variables_present(self):
        """Test validation when all required variables are present."""
        validator = TemplateValidator()
        template = "Hello {{ name }}, your order {{ order_id }} is ready."
        required_variables = ["name", "order_id"]

        assert (
            validator.validate_required_variables(template, required_variables) is True
        )

    def test_validate_required_variables_missing(self):
        """Test validation when required variables are missing."""
        validator = TemplateValidator()
        template = "Hello {{ name }}!"
        required_variables = ["name", "order_id"]  # order_id is missing

        with pytest.raises(ValidationError) as exc_info:
            validator.validate_required_variables(template, required_variables)

        assert "missing required variables" in str(exc_info.value).lower()
        assert "order_id" in str(exc_info.value)
        assert exc_info.value.field == "required_variables"

    def test_validate_no_forbidden_operations_safe(self):
        """Test validation passes with safe operations."""
        validator = TemplateValidator()
        template = "Hello {{ name|upper }}! {{ count|pluralize('item', 'items') }}"

        assert validator.validate_no_forbidden_operations(template) is True

    def test_validate_no_forbidden_operations_exec_filter(self):
        """Test validation rejects forbidden exec filter."""
        validator = TemplateValidator()
        template = "{{ code|exec }}"

        with pytest.raises(ValidationError) as exc_info:
            validator.validate_no_forbidden_operations(template)

        assert "forbidden filter" in str(exc_info.value).lower()
        assert "exec" in str(exc_info.value)

    def test_validate_no_forbidden_operations_eval_filter(self):
        """Test validation rejects forbidden eval filter."""
        validator = TemplateValidator()
        template = "{{ expression|eval }}"

        with pytest.raises(ValidationError) as exc_info:
            validator.validate_no_forbidden_operations(template)

        assert "forbidden filter" in str(exc_info.value).lower()

    def test_validate_html_safety_safe_html(self):
        """Test validation passes with safe HTML."""
        validator = TemplateValidator()
        html = "<p>Hello {{ name }}!</p><div style='color: blue;'>Content</div>"

        assert validator._validate_html_safety(html) is True

    def test_validate_html_safety_dangerous_attributes(self):
        """Test validation rejects dangerous HTML attributes."""
        validator = TemplateValidator()
        html = "<img src='x' onerror='alert(1)'>"

        with pytest.raises(ValidationError) as exc_info:
            validator._validate_html_safety(html)

        assert "dangerous html attribute" in str(exc_info.value).lower()
        assert "onerror" in str(exc_info.value)

    def test_validate_html_safety_onclick(self):
        """Test validation rejects onclick attribute."""
        validator = TemplateValidator()
        html = "<button onclick='doSomething()'>Click</button>"

        with pytest.raises(ValidationError) as exc_info:
            validator._validate_html_safety(html)

        assert "onclick" in str(exc_info.value)

    def test_validate_complete_template_valid(self):
        """Test complete validation of valid template."""
        validator = TemplateValidator()
        subject = "Welcome {{ user_name }}"
        html = "<p>Hello {{ user_name }}, welcome!</p>"
        text = "Hello {{ user_name }}, welcome!"
        required_vars = ["user_name"]

        assert (
            validator.validate_complete_template(subject, html, text, required_vars)
            is True
        )

    def test_validate_complete_template_invalid_subject(self):
        """Test complete validation fails with invalid subject."""
        validator = TemplateValidator()
        subject = "Subject\nWith\nNewlines"
        html = "<p>Valid HTML</p>"
        text = "Valid text"

        with pytest.raises(ValidationError) as exc_info:
            validator.validate_complete_template(subject, html, text)

        assert "newlines" in str(exc_info.value).lower()

    def test_validate_complete_template_missing_variables(self):
        """Test complete validation fails with missing variables."""
        validator = TemplateValidator()
        subject = "Hello"
        html = "<p>HTML content</p>"
        text = "Text content"
        required_vars = ["user_name", "order_id"]  # Not present in templates

        with pytest.raises(ValidationError) as exc_info:
            validator.validate_complete_template(subject, html, text, required_vars)

        assert "missing required variables" in str(exc_info.value).lower()

    def test_extract_variables(self):
        """Test extracting variables from template."""
        validator = TemplateValidator()
        template = """
        Hello {{ user_name }},

        Your order {{ order_id }} is ready.
        Total: ${{ total_amount }}

        {% if is_member %}
        Member discount applied!
        {% endif %}
        """

        variables = validator.extract_variables(template)

        assert "user_name" in variables
        assert "order_id" in variables
        assert "total_amount" in variables
        assert "is_member" in variables
        # Should be sorted
        assert variables == sorted(variables)

    def test_extract_variables_with_filters(self):
        """Test extracting variables when filters are used."""
        validator = TemplateValidator()
        template = "{{ name|upper }} - {{ count|pluralize('item', 'items') }}"

        variables = validator.extract_variables(template)

        assert "name" in variables
        assert "count" in variables

    def test_extract_variables_invalid_syntax(self):
        """Test extracting variables from template with invalid syntax."""
        validator = TemplateValidator()
        template = "{{ invalid syntax }}"

        variables = validator.extract_variables(template)

        # Should return empty list on error
        assert variables == []

    def test_convenience_function_validate_template_syntax(self):
        """Test convenience function for syntax validation."""
        template = "Hello {{ name }}!"

        assert validate_template_syntax(template) is True

    def test_convenience_function_invalid_syntax(self):
        """Test convenience function with invalid syntax."""
        template = "{{ broken"

        with pytest.raises(ValidationError):
            validate_template_syntax(template)

    def test_validation_error_attributes(self):
        """Test ValidationError includes all expected attributes."""
        error = ValidationError(
            message="Test error", field="test_field", details={"key": "value"}
        )

        assert error.message == "Test error"
        assert error.field == "test_field"
        assert error.details == {"key": "value"}
        assert "Test error" in str(error)

    def test_validation_error_optional_attributes(self):
        """Test ValidationError with optional attributes."""
        error = ValidationError(message="Simple error")

        assert error.message == "Simple error"
        assert error.field is None
        assert error.details == {}
