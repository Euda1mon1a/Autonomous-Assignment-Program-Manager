"""Tests for input sanitizers (pure logic, security-critical, no DB)."""

import pytest

from app.validators.sanitizers import (
    SanitizationError,
    sanitize_html,
    sanitize_sql_like_pattern,
    sanitize_path,
    sanitize_filename,
    normalize_unicode,
    sanitize_email_input,
    sanitize_search_query,
    strip_dangerous_characters,
    sanitize_json_input,
    validate_no_script_tags,
    sanitize_identifier,
)


# ── sanitize_html ────────────────────────────────────────────────────────


class TestSanitizeHtml:
    def test_escapes_script_tag(self):
        result = sanitize_html("<script>alert('xss')</script>")
        assert "<script>" not in result
        assert "&lt;script&gt;" in result

    def test_escapes_angle_brackets(self):
        result = sanitize_html("<div>test</div>")
        assert "<div>" not in result

    def test_safe_tags_allowed(self):
        result = sanitize_html("Hello <b>World</b>", allow_safe_tags=True)
        assert "<b>World</b>" in result

    def test_safe_tags_em(self):
        result = sanitize_html("<em>text</em>", allow_safe_tags=True)
        assert "<em>text</em>" in result

    def test_safe_tags_strong(self):
        result = sanitize_html("<strong>text</strong>", allow_safe_tags=True)
        assert "<strong>text</strong>" in result

    def test_unsafe_tag_still_escaped_with_safe_mode(self):
        result = sanitize_html("<script>bad</script>", allow_safe_tags=True)
        assert "<script>" not in result

    def test_empty_string(self):
        assert sanitize_html("") == ""

    def test_none_like_empty(self):
        assert sanitize_html("") == ""

    def test_plain_text_unchanged(self):
        assert sanitize_html("Hello World") == "Hello World"

    def test_ampersand_escaped(self):
        result = sanitize_html("A & B")
        assert "&amp;" in result


# ── sanitize_sql_like_pattern ────────────────────────────────────────────


class TestSanitizeSqlLikePattern:
    def test_escapes_percent(self):
        assert "\\%" in sanitize_sql_like_pattern("test%data")

    def test_escapes_underscore(self):
        assert "\\_" in sanitize_sql_like_pattern("test_data")

    def test_escapes_brackets(self):
        result = sanitize_sql_like_pattern("[abc]")
        assert "\\[" in result
        assert "\\]" in result

    def test_escapes_backslash(self):
        result = sanitize_sql_like_pattern("test\\data")
        assert "\\\\" in result

    def test_empty_string(self):
        assert sanitize_sql_like_pattern("") == ""

    def test_plain_text_unchanged(self):
        assert sanitize_sql_like_pattern("hello") == "hello"


# ── sanitize_path ────────────────────────────────────────────────────────


class TestSanitizePath:
    def test_simple_path(self):
        result = sanitize_path("data/file.txt")
        assert result == "data/file.txt"

    def test_traversal_rejected(self):
        with pytest.raises(SanitizationError, match="traversal"):
            sanitize_path("../../etc/passwd")

    def test_absolute_rejected(self):
        with pytest.raises(SanitizationError, match="Absolute"):
            sanitize_path("/etc/passwd")

    def test_absolute_allowed(self):
        result = sanitize_path("/etc/config", allow_absolute=True)
        assert result == "/etc/config"

    def test_null_bytes_removed(self):
        result = sanitize_path("data\x00/file.txt")
        assert "\x00" not in result

    def test_empty(self):
        with pytest.raises(SanitizationError, match="empty"):
            sanitize_path("")


# ── sanitize_filename ────────────────────────────────────────────────────


class TestSanitizeFilename:
    def test_simple_filename(self):
        result = sanitize_filename("report.pdf")
        assert result == "report.pdf"

    def test_strips_path(self):
        result = sanitize_filename("/tmp/secret/report.pdf")
        assert "/" not in result
        assert "report.pdf" in result

    def test_removes_traversal(self):
        result = sanitize_filename("../../../etc/passwd")
        # After removing .., the name should not contain path components
        assert ".." not in result

    def test_removes_null_bytes(self):
        result = sanitize_filename("report\x00.pdf")
        assert "\x00" not in result

    def test_removes_leading_dots(self):
        result = sanitize_filename(".hidden_file")
        assert not result.startswith(".")

    def test_empty(self):
        with pytest.raises(SanitizationError, match="empty"):
            sanitize_filename("")

    def test_long_filename_truncated(self):
        name = "a" * 300 + ".txt"
        result = sanitize_filename(name)
        assert len(result) <= 255

    def test_special_chars_replaced(self):
        result = sanitize_filename("file<>|.txt")
        assert "<" not in result
        assert ">" not in result


# ── normalize_unicode ────────────────────────────────────────────────────


class TestNormalizeUnicode:
    def test_nfkc_default(self):
        result = normalize_unicode("café")
        assert isinstance(result, str)
        assert "caf" in result

    def test_empty(self):
        assert normalize_unicode("") == ""

    def test_nfc_form(self):
        result = normalize_unicode("test", form="NFC")
        assert result == "test"

    def test_nfd_form(self):
        result = normalize_unicode("test", form="NFD")
        assert result == "test"


# ── sanitize_email_input ────────────────────────────────────────────────


class TestSanitizeEmailInput:
    def test_lowercases(self):
        assert sanitize_email_input("User@Example.COM") == "user@example.com"

    def test_trims_whitespace(self):
        assert sanitize_email_input("  user@example.com  ") == "user@example.com"

    def test_removes_null_bytes(self):
        result = sanitize_email_input("user\x00@example.com")
        assert "\x00" not in result

    def test_empty(self):
        with pytest.raises(SanitizationError, match="empty"):
            sanitize_email_input("")


# ── sanitize_search_query ───────────────────────────────────────────────


class TestSanitizeSearchQuery:
    def test_plain_query(self):
        assert sanitize_search_query("John Smith") == "John Smith"

    def test_empty(self):
        assert sanitize_search_query("") == ""

    def test_trims_whitespace(self):
        assert sanitize_search_query("  test  ") == "test"

    def test_truncates_long_query(self):
        result = sanitize_search_query("x" * 300)
        assert len(result) == 200

    def test_custom_max_length(self):
        result = sanitize_search_query("x" * 50, max_length=20)
        assert len(result) == 20

    def test_sql_union_select(self):
        with pytest.raises(SanitizationError, match="SQL"):
            sanitize_search_query("test UNION SELECT * FROM users")

    def test_sql_drop_table(self):
        with pytest.raises(SanitizationError, match="SQL"):
            sanitize_search_query("test; DROP TABLE users")

    def test_command_injection_semicolon(self):
        with pytest.raises(SanitizationError, match="command"):
            sanitize_search_query("test; rm -rf /")

    def test_command_injection_pipe(self):
        with pytest.raises(SanitizationError, match="command"):
            sanitize_search_query("test | cat /etc/passwd")

    def test_command_injection_backtick(self):
        with pytest.raises(SanitizationError, match="command"):
            sanitize_search_query("test `whoami`")

    def test_removes_null_bytes(self):
        result = sanitize_search_query("test\x00query")
        assert "\x00" not in result


# ── strip_dangerous_characters ──────────────────────────────────────────


class TestStripDangerousCharacters:
    def test_plain_text_unchanged(self):
        assert strip_dangerous_characters("Hello World") == "Hello World"

    def test_removes_null_bytes(self):
        result = strip_dangerous_characters("test\x00data")
        assert "\x00" not in result

    def test_keeps_tabs_newlines(self):
        result = strip_dangerous_characters("line1\nline2\ttab")
        assert "\n" in result
        assert "\t" in result

    def test_removes_zero_width_space(self):
        result = strip_dangerous_characters("test\u200bdata")
        assert "\u200b" not in result

    def test_removes_zero_width_joiner(self):
        result = strip_dangerous_characters("test\u200ddata")
        assert "\u200d" not in result

    def test_removes_bom(self):
        result = strip_dangerous_characters("\ufefftest")
        assert "\ufeff" not in result

    def test_removes_rtl_override(self):
        result = strip_dangerous_characters("test\u202edata")
        assert "\u202e" not in result

    def test_empty(self):
        assert strip_dangerous_characters("") == ""


# ── sanitize_json_input ─────────────────────────────────────────────────


class TestSanitizeJsonInput:
    def test_string_sanitized(self):
        result = sanitize_json_input("test\x00data")
        assert "\x00" not in result

    def test_dict_recursed(self):
        result = sanitize_json_input({"key\x00": "val\x00"})
        for k, v in result.items():
            assert "\x00" not in k
            assert "\x00" not in v

    def test_list_recursed(self):
        result = sanitize_json_input(["test\x00", "data\x00"])
        for item in result:
            assert "\x00" not in item

    def test_nested_structure(self):
        data = {"users": [{"name": "test\x00"}]}
        result = sanitize_json_input(data)
        assert "\x00" not in result["users"][0]["name"]

    def test_non_string_passthrough(self):
        assert sanitize_json_input(42) == 42
        assert sanitize_json_input(True) is True
        assert sanitize_json_input(None) is None


# ── validate_no_script_tags ─────────────────────────────────────────────


class TestValidateNoScriptTags:
    def test_plain_text_ok(self):
        assert validate_no_script_tags("Hello World") == "Hello World"

    def test_script_tag_rejected(self):
        with pytest.raises(SanitizationError, match="Script tags"):
            validate_no_script_tags("<script>alert('xss')</script>")

    def test_onclick_rejected(self):
        with pytest.raises(SanitizationError, match="onclick"):
            validate_no_script_tags('<div onclick="bad()">click</div>')

    def test_onload_rejected(self):
        with pytest.raises(SanitizationError, match="onload"):
            validate_no_script_tags('<img onload="bad()" />')

    def test_onerror_rejected(self):
        with pytest.raises(SanitizationError, match="onerror"):
            validate_no_script_tags('<img onerror="bad()" />')

    def test_javascript_protocol_rejected(self):
        with pytest.raises(SanitizationError, match="JavaScript protocol"):
            validate_no_script_tags('javascript:alert("xss")')

    def test_empty(self):
        assert validate_no_script_tags("") == ""

    def test_html_without_script_ok(self):
        assert validate_no_script_tags("<p>Hello</p>") == "<p>Hello</p>"


# ── sanitize_identifier ─────────────────────────────────────────────────


class TestSanitizeIdentifier:
    def test_valid(self):
        assert sanitize_identifier("my_var") == "my_var"

    def test_underscore_start(self):
        assert sanitize_identifier("_private") == "_private"

    def test_alphanumeric(self):
        assert sanitize_identifier("var123") == "var123"

    def test_empty(self):
        with pytest.raises(SanitizationError, match="empty"):
            sanitize_identifier("")

    def test_starts_with_number(self):
        with pytest.raises(SanitizationError, match="start with letter"):
            sanitize_identifier("123abc")

    def test_special_characters(self):
        with pytest.raises(SanitizationError, match="letters, numbers"):
            sanitize_identifier("my-var")

    def test_too_long(self):
        with pytest.raises(SanitizationError, match="too long"):
            sanitize_identifier("x" * 65)

    def test_custom_max_length(self):
        with pytest.raises(SanitizationError, match="too long"):
            sanitize_identifier("x" * 11, max_length=10)

    def test_trims_whitespace(self):
        assert sanitize_identifier("  my_var  ") == "my_var"
