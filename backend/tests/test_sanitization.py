"""Tests for input sanitization module."""

import pytest

from app.sanitization.html import (
    count_html_tags,
    escape_html,
    is_safe_html,
    sanitize_html,
    sanitize_rich_text,
    strip_all_tags,
    validate_url_protocol,
)
from app.sanitization.sql import (
    SQLInjectionError,
    check_query_complexity,
    detect_sql_injection,
    escape_like_wildcards,
    is_safe_order_by,
    sanitize_numeric_id,
    sanitize_sql_input,
    validate_identifier,
    validate_like_pattern,
    validate_table_name,
)
from app.sanitization.xss import (
    XSSDetectionError,
    detect_xss,
    encode_for_html_attribute,
    is_safe_filename,
    normalize_unicode,
    prevent_path_traversal,
    sanitize_email,
    sanitize_input,
    sanitize_url,
    strip_javascript,
)


class TestHTMLSanitization:
    """Test suite for HTML sanitization functions."""

    def test_strip_all_tags_basic(self):
        """Test basic HTML tag stripping."""
        assert strip_all_tags("<p>Hello World</p>") == "Hello World"
        assert strip_all_tags('<script>alert("xss")</script>') == ""
        assert strip_all_tags("Plain text") == "Plain text"

    def test_strip_all_tags_complex(self):
        """Test stripping complex HTML."""
        html = "<div><p>Hello <strong>World</strong></p><script>evil()</script></div>"
        result = strip_all_tags(html)
        assert result == "Hello World"
        assert "<" not in result
        assert ">" not in result

    def test_strip_all_tags_empty(self):
        """Test stripping with empty input."""
        assert strip_all_tags("") == ""
        assert strip_all_tags(None) == ""

    def test_sanitize_html_removes_dangerous_tags(self):
        """Test that dangerous tags are removed."""
        dangerous = '<script>alert("xss")</script><p>Safe</p>'
        result = sanitize_html(dangerous)
        assert "script" not in result.lower()
        assert "Safe" in result

    def test_sanitize_html_removes_event_handlers(self):
        """Test that event handlers are removed."""
        html = '<p onclick="evil()">Text</p>'
        result = sanitize_html(html)
        assert "onclick" not in result.lower()
        assert "Text" in result

    def test_sanitize_html_removes_javascript_protocol(self):
        """Test that javascript: protocol is removed."""
        html = '<a href="javascript:alert(1)">Link</a>'
        result = sanitize_html(html)
        assert "javascript:" not in result.lower()

    def test_sanitize_html_allows_safe_tags(self):
        """Test that safe tags are preserved."""
        html = "<p>Hello <strong>World</strong></p>"
        result = sanitize_html(html)
        assert "<p>" in result or "Hello" in result
        assert "World" in result

    def test_sanitize_rich_text(self):
        """Test rich text sanitization."""
        html = "<p>Hello <strong>World</strong></p>"
        result = sanitize_rich_text(html)
        assert "Hello" in result
        assert "World" in result

    def test_escape_html(self):
        """Test HTML escaping."""
        assert escape_html("<script>") == "&lt;script&gt;"
        assert escape_html('"quotes"') == "&quot;quotes&quot;"
        assert escape_html("'single'") == "&#x27;single&#x27;"

    def test_validate_url_protocol_safe(self):
        """Test URL protocol validation with safe URLs."""
        assert validate_url_protocol("https://example.com") is True
        assert validate_url_protocol("http://example.com") is True
        assert validate_url_protocol("mailto:user@example.com") is True
        assert validate_url_protocol("/relative/path") is True

    def test_validate_url_protocol_dangerous(self):
        """Test URL protocol validation with dangerous URLs."""
        assert validate_url_protocol("javascript:alert(1)") is False
        assert (
            validate_url_protocol("data:text/html,<script>alert(1)</script>") is False
        )
        assert validate_url_protocol("vbscript:msgbox(1)") is False

    def test_count_html_tags(self):
        """Test HTML tag counting."""
        assert count_html_tags("<p>Text</p>") == 2
        assert count_html_tags("Plain text") == 0
        assert count_html_tags("<div><p>Text</p></div>") == 4

    def test_is_safe_html(self):
        """Test safe HTML detection."""
        assert is_safe_html("<p>Normal content</p>") is True
        assert is_safe_html("Plain text") is True
        assert is_safe_html("<script>alert(1)</script>") is False
        assert is_safe_html('<p onclick="evil()">Text</p>') is False


class TestSQLSanitization:
    """Test suite for SQL injection prevention."""

    def test_detect_sql_injection_basic(self):
        """Test basic SQL injection detection."""
        assert detect_sql_injection("' OR '1'='1") is True
        assert detect_sql_injection("normal text") is False
        assert detect_sql_injection("SELECT * FROM users") is True

    def test_detect_sql_injection_union(self):
        """Test UNION-based injection detection."""
        assert detect_sql_injection("1 UNION SELECT * FROM users") is True
        assert detect_sql_injection("normal union membership") is False

    def test_detect_sql_injection_comment(self):
        """Test comment-based injection detection."""
        assert detect_sql_injection("admin'--") is True
        assert detect_sql_injection("/* comment */ DROP TABLE") is True

    def test_sanitize_sql_input_normal(self):
        """Test sanitizing normal SQL input."""
        assert sanitize_sql_input("normal text") == "normal text"
        assert sanitize_sql_input("  spaces  ") == "spaces"

    def test_sanitize_sql_input_dangerous(self):
        """Test that dangerous SQL input raises error."""
        with pytest.raises(SQLInjectionError):
            sanitize_sql_input("' OR '1'='1")

    def test_sanitize_sql_input_max_length(self):
        """Test SQL input truncation."""
        long_text = "a" * 100
        result = sanitize_sql_input(long_text, max_length=50)
        assert len(result) == 50

    def test_validate_identifier_valid(self):
        """Test validating valid SQL identifiers."""
        assert validate_identifier("users") == "users"
        assert validate_identifier("user_table_123") == "user_table_123"

    def test_validate_identifier_invalid(self):
        """Test validating invalid SQL identifiers."""
        with pytest.raises(SQLInjectionError):
            validate_identifier("'; DROP TABLE users--")

        with pytest.raises(SQLInjectionError):
            validate_identifier("123invalid")  # Can't start with number

        with pytest.raises(SQLInjectionError):
            validate_identifier("")  # Empty

    def test_validate_identifier_reserved(self):
        """Test that reserved words are rejected."""
        with pytest.raises(SQLInjectionError):
            validate_identifier("select")

    def test_validate_like_pattern(self):
        """Test LIKE pattern validation."""
        assert validate_like_pattern("user%") == "user%"
        assert validate_like_pattern("%test_pattern%") == "%test_pattern%"

    def test_validate_like_pattern_dangerous(self):
        """Test that dangerous LIKE patterns are rejected."""
        with pytest.raises(SQLInjectionError):
            validate_like_pattern("user%'; DROP TABLE users--")

    def test_escape_like_wildcards(self):
        """Test escaping LIKE wildcards."""
        assert escape_like_wildcards("50% complete") == "50\\% complete"
        assert escape_like_wildcards("file_name.txt") == "file\\_name.txt"

    def test_is_safe_order_by(self):
        """Test ORDER BY column validation."""
        allowed = {"id", "name", "created_at"}
        assert is_safe_order_by("id", allowed) is True
        assert is_safe_order_by("name", allowed) is True
        assert is_safe_order_by("unknown", allowed) is False
        assert is_safe_order_by("id; DROP TABLE", allowed) is False

    def test_sanitize_numeric_id(self):
        """Test numeric ID sanitization."""
        assert sanitize_numeric_id("123") == 123
        assert sanitize_numeric_id("0") == 0
        assert sanitize_numeric_id("abc") is None
        assert sanitize_numeric_id("123; DROP TABLE") is None
        assert sanitize_numeric_id("-1") is None  # Negative

    def test_validate_table_name(self):
        """Test table name validation."""
        allowed = {"users", "roles", "permissions"}
        assert validate_table_name("users", allowed) == "users"

        with pytest.raises(SQLInjectionError):
            validate_table_name("unknown_table", allowed)

    def test_check_query_complexity(self):
        """Test query complexity checking."""
        assert check_query_complexity("SELECT * FROM users") is True
        assert check_query_complexity("SELECT " + "* " * 1000 + "FROM users") is False


class TestXSSPrevention:
    """Test suite for XSS prevention."""

    def test_detect_xss_script_tags(self):
        """Test XSS detection with script tags."""
        assert detect_xss('<script>alert("xss")</script>') is True
        assert detect_xss("normal text") is False

    def test_detect_xss_event_handlers(self):
        """Test XSS detection with event handlers."""
        assert detect_xss("<img src=x onerror=alert(1)>") is True
        assert detect_xss('<p onclick="evil()">Text</p>') is True

    def test_detect_xss_javascript_protocol(self):
        """Test XSS detection with javascript: protocol."""
        assert detect_xss('<a href="javascript:alert(1)">Link</a>') is True

    def test_detect_xss_encoded(self):
        """Test XSS detection with URL encoding."""
        assert detect_xss("%3Cscript%3Ealert(1)%3C/script%3E") is True

    def test_sanitize_input_normal(self):
        """Test sanitizing normal input."""
        assert sanitize_input("normal text") == "normal text"
        assert sanitize_input("  spaces  ") == "spaces"

    def test_sanitize_input_dangerous(self):
        """Test that dangerous input raises error."""
        with pytest.raises(XSSDetectionError):
            sanitize_input('<script>alert("xss")</script>')

    def test_sanitize_input_max_length(self):
        """Test input truncation."""
        long_text = "a" * 100
        result = sanitize_input(long_text, max_length=50)
        assert len(result) == 50

    def test_normalize_unicode(self):
        """Test Unicode normalization."""
        # Test that it doesn't crash with various Unicode
        result = normalize_unicode("café")
        assert result == "café"

        # Test control character removal
        result = normalize_unicode("text\x00here")
        assert "\x00" not in result

    def test_sanitize_url_safe(self):
        """Test URL sanitization with safe URLs."""
        assert sanitize_url("https://example.com") == "https://example.com"
        assert sanitize_url("http://example.com/path") == "http://example.com/path"

    def test_sanitize_url_dangerous(self):
        """Test URL sanitization with dangerous URLs."""
        with pytest.raises(XSSDetectionError):
            sanitize_url("javascript:alert(1)")

        with pytest.raises(XSSDetectionError):
            sanitize_url("data:text/html,<script>alert(1)</script>")

    def test_prevent_path_traversal(self):
        """Test path traversal prevention."""
        assert prevent_path_traversal("safe/path/file.txt") == "safe/path/file.txt"

        with pytest.raises(XSSDetectionError):
            prevent_path_traversal("../../../etc/passwd")

        with pytest.raises(XSSDetectionError):
            prevent_path_traversal("..\\..\\windows\\system32")

    def test_sanitize_email_valid(self):
        """Test email sanitization with valid emails."""
        assert sanitize_email("user@example.com") == "user@example.com"
        assert sanitize_email("User@Example.COM") == "user@example.com"

    def test_sanitize_email_invalid(self):
        """Test email sanitization with invalid emails."""
        with pytest.raises(XSSDetectionError):
            sanitize_email('"><script>alert(1)</script>')

        with pytest.raises(XSSDetectionError):
            sanitize_email("not-an-email")

    def test_is_safe_filename(self):
        """Test filename safety checking."""
        assert is_safe_filename("document.pdf") is True
        assert is_safe_filename("my_file_123.txt") is True
        assert is_safe_filename("../../../etc/passwd") is False
        assert is_safe_filename("file<script>.txt") is False
        assert is_safe_filename(".hidden") is False

    def test_encode_for_html_attribute(self):
        """Test HTML attribute encoding."""
        assert encode_for_html_attribute("value") == "value"
        result = encode_for_html_attribute('value with "quotes"')
        assert "&quot;" in result
        assert '"' not in result

    def test_strip_javascript(self):
        """Test JavaScript stripping."""
        html = "Hello <script>alert(1)</script> World"
        result = strip_javascript(html)
        assert "Hello" in result
        assert "World" in result
        assert "script" not in result.lower()


class TestSanitizationIntegration:
    """Integration tests for sanitization module."""

    def test_comprehensive_xss_prevention(self):
        """Test comprehensive XSS prevention."""
        payloads = [
            '<script>alert("xss")</script>',
            "<img src=x onerror=alert(1)>",
            "<svg/onload=alert(1)>",
            "javascript:alert(1)",
            '<iframe src="javascript:alert(1)">',
            "<body onload=alert(1)>",
        ]

        for payload in payloads:
            assert detect_xss(payload) is True

    def test_comprehensive_sql_injection_prevention(self):
        """Test comprehensive SQL injection prevention."""
        payloads = [
            "' OR '1'='1",
            "1; DROP TABLE users--",
            "admin'--",
            "1 UNION SELECT * FROM users",
            "'; EXEC xp_cmdshell('dir')--",
        ]

        for payload in payloads:
            assert detect_sql_injection(payload) is True

    def test_sanitization_preserves_safe_content(self):
        """Test that sanitization preserves safe content."""
        safe_inputs = [
            "Normal text",
            "Text with numbers 123",
            "Email: user@example.com",
            "Path: documents/file.txt",
            "List: apples, oranges, bananas",
        ]

        for safe_input in safe_inputs:
            # Should not detect threats
            assert detect_xss(safe_input, strict=False) is False
            assert detect_sql_injection(safe_input, strict=False) is False

    def test_unicode_normalization_prevents_bypass(self):
        """Test that Unicode normalization prevents filter bypass."""
        # Test with various Unicode forms
        text = "café"
        normalized = normalize_unicode(text)
        assert normalized  # Should not be empty
        assert len(normalized) <= len(text)  # May be shorter after normalization

    def test_sanitization_is_idempotent(self):
        """Test that sanitization is idempotent."""
        text = "Normal safe text"
        once = strip_all_tags(text)
        twice = strip_all_tags(once)
        assert once == twice

    def test_empty_and_none_handling(self):
        """Test that empty/None inputs are handled gracefully."""
        assert strip_all_tags("") == ""
        assert strip_all_tags(None) == ""
        assert sanitize_sql_input("") == ""
        assert normalize_unicode("") == ""
        assert escape_html("") == ""


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_very_long_input(self):
        """Test handling of very long inputs."""
        long_text = "a" * 100000
        result = sanitize_input(long_text, max_length=10000)
        assert len(result) <= 10000

    def test_nested_html(self):
        """Test deeply nested HTML."""
        nested = "<div>" * 100 + "content" + "</div>" * 100
        result = strip_all_tags(nested)
        assert "content" in result
        assert "<" not in result

    def test_mixed_encodings(self):
        """Test mixed URL encodings."""
        text = "normal%20text%3Cscript%3E"
        # Should detect encoded script tag
        assert detect_xss(text, strict=True) is True

    def test_case_insensitive_detection(self):
        """Test case-insensitive threat detection."""
        assert detect_xss("<SCRIPT>alert(1)</SCRIPT>") is True
        assert detect_sql_injection("SELECT * FROM users") is True
        assert detect_sql_injection("select * from users") is True

    def test_whitespace_variations(self):
        """Test detection with various whitespace."""
        assert detect_xss("<script\n>alert(1)</script>") is True
        assert detect_xss("<script\t>alert(1)</script>") is True

    def test_null_byte_handling(self):
        """Test null byte removal."""
        text = "text\x00with\x00nulls"
        result = sanitize_input(text, allow_html=False)
        assert "\x00" not in result
