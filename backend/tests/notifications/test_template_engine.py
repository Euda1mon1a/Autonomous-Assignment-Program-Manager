"""Tests for notification template engine."""
import pytest

from app.notifications.templates.engine import (
    TemplateEngine,
    TemplateRenderError,
    get_template_engine,
)


class TestTemplateEngine:
    """Test suite for template engine."""

    def test_render_simple_string(self):
        """Test rendering a simple template string."""
        engine = TemplateEngine()
        template = "Hello {{ name }}!"
        context = {"name": "World"}

        result = engine.render_string(template, context)
        assert result == "Hello World!"

    def test_render_with_filters(self):
        """Test rendering with custom filters."""
        engine = TemplateEngine()
        template = "Count: {{ count|pluralize('item', 'items') }}"

        # Test singular
        result = engine.render_string(template, {"count": 1})
        assert result == "Count: item"

        # Test plural
        result = engine.render_string(template, {"count": 5})
        assert result == "Count: items"

    def test_render_html_and_text(self):
        """Test rendering both HTML and text versions."""
        engine = TemplateEngine()
        html_template = "<p>Hello <strong>{{ name }}</strong>!</p>"
        text_template = "Hello {{ name }}!"
        context = {"name": "World"}

        result = engine.render_html_and_text(html_template, text_template, context)

        assert "html" in result
        assert "text" in result
        assert result["html"] == "<p>Hello <strong>World</strong>!</p>"
        assert result["text"] == "Hello World!"

    def test_render_with_undefined_variable(self):
        """Test that undefined variables raise error with StrictUndefined."""
        engine = TemplateEngine()
        template = "Hello {{ undefined_var }}!"

        with pytest.raises(TemplateRenderError) as exc_info:
            engine.render_string(template, {})

        assert "Undefined variable" in str(exc_info.value)

    def test_validate_syntax_valid(self):
        """Test syntax validation with valid template."""
        engine = TemplateEngine()
        template = "Hello {{ name }}! {% if admin %}Admin{% endif %}"

        assert engine.validate_syntax(template) is True

    def test_validate_syntax_invalid(self):
        """Test syntax validation with invalid template."""
        engine = TemplateEngine()
        template = "Hello {{ name }! {% if admin %}"  # Missing closing braces and endif

        with pytest.raises(TemplateRenderError) as exc_info:
            engine.validate_syntax(template)

        assert "syntax error" in str(exc_info.value).lower()

    def test_preview_template(self):
        """Test template preview with sample data."""
        engine = TemplateEngine()
        template = "Welcome {{ user_name }}, you have {{ message_count }} messages."
        sample_context = {"user_name": "Alice", "message_count": 5}

        result = engine.preview_template(template, sample_context)
        assert result == "Welcome Alice, you have 5 messages."

    def test_auto_escape_html(self):
        """Test that HTML is auto-escaped in HTML mode."""
        engine = TemplateEngine()
        template = "<p>{{ content }}</p>"
        context = {"content": "<script>alert('xss')</script>"}

        result = engine.render_string(template, context, autoescape=True)
        assert "<script>" not in result
        assert "&lt;script&gt;" in result

    def test_no_auto_escape_text(self):
        """Test that text is not escaped in text mode."""
        engine = TemplateEngine()
        template = "Content: {{ content }}"
        context = {"content": "<script>alert('xss')</script>"}

        result = engine.render_string(template, context, autoescape=False)
        assert "<script>" in result

    def test_sandboxed_environment(self):
        """Test that sandboxed environment is used."""
        engine = TemplateEngine(enable_sandbox=True)
        assert engine.enable_sandbox is True

    def test_locale_in_context(self):
        """Test that locale is added to context."""
        engine = TemplateEngine(locale="es_ES")
        template = "Locale: {{ locale }}"

        result = engine.render_string(template, {})
        assert result == "Locale: es_ES"

    def test_format_date_filter(self):
        """Test custom date formatting filter."""
        from datetime import date

        engine = TemplateEngine()
        template = "Date: {{ my_date|format_date('%Y-%m-%d') }}"
        context = {"my_date": date(2025, 12, 20)}

        result = engine.render_string(template, context)
        assert result == "Date: 2025-12-20"

    def test_format_datetime_filter(self):
        """Test custom datetime formatting filter."""
        from datetime import datetime

        engine = TemplateEngine()
        template = "Time: {{ my_datetime|format_datetime('%Y-%m-%d %H:%M') }}"
        context = {"my_datetime": datetime(2025, 12, 20, 14, 30)}

        result = engine.render_string(template, context)
        assert result == "Time: 2025-12-20 14:30"

    def test_get_template_engine_singleton(self):
        """Test that get_template_engine returns singleton."""
        engine1 = get_template_engine()
        engine2 = get_template_engine()

        assert engine1 is engine2

    def test_render_with_conditional(self):
        """Test rendering with conditional logic."""
        engine = TemplateEngine()
        template = """
        {% if is_admin %}
        Admin Panel
        {% else %}
        User Panel
        {% endif %}
        """

        result_admin = engine.render_string(template, {"is_admin": True})
        assert "Admin Panel" in result_admin

        result_user = engine.render_string(template, {"is_admin": False})
        assert "User Panel" in result_user

    def test_render_with_loop(self):
        """Test rendering with loop."""
        engine = TemplateEngine()
        template = """
        {% for item in items %}
        - {{ item }}
        {% endfor %}
        """
        context = {"items": ["Apple", "Banana", "Cherry"]}

        result = engine.render_string(template, context)
        assert "- Apple" in result
        assert "- Banana" in result
        assert "- Cherry" in result

    def test_error_includes_template_name(self):
        """Test that error includes template name when rendering from file fails."""
        engine = TemplateEngine(template_dirs=["/nonexistent"])

        with pytest.raises(TemplateRenderError) as exc_info:
            engine.render_template("nonexistent.html", {})

        # The error should include information about the template
        assert exc_info.value.template_name == "nonexistent.html"
