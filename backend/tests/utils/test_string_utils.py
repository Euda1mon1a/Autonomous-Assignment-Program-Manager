"""Tests for string utility functions."""

import pytest

from app.utils.string_utils import (
    extract_initials,
    normalize_whitespace,
    remove_html_tags,
    slugify,
    truncate,
)


class TestSlugify:
    """Tests for slugify."""

    def test_simple_text(self):
        assert slugify("Hello World") == "hello-world"

    def test_special_characters_removed(self):
        assert slugify("Hello! World?") == "hello-world"

    def test_underscores_become_hyphens(self):
        assert slugify("hello_world") == "hello-world"

    def test_multiple_spaces_collapsed(self):
        assert slugify("hello   world") == "hello-world"

    def test_accents_removed(self):
        assert slugify("café résumé") == "cafe-resume"

    def test_leading_trailing_hyphens_stripped(self):
        assert slugify("--hello--") == "hello"

    def test_multiple_hyphens_collapsed(self):
        assert slugify("hello---world") == "hello-world"

    def test_empty_string(self):
        assert slugify("") == ""

    def test_uppercase_lowered(self):
        assert slugify("HELLO WORLD") == "hello-world"

    def test_mixed_input(self):
        assert slugify("Block 10 - Schedule (2025)") == "block-10-schedule-2025"


class TestTruncate:
    """Tests for truncate."""

    def test_short_text_unchanged(self):
        assert truncate("hello", 10) == "hello"

    def test_exact_length_unchanged(self):
        assert truncate("hello", 5) == "hello"

    def test_truncates_with_suffix(self):
        assert truncate("hello world", 8) == "hello..."

    def test_custom_suffix(self):
        assert truncate("hello world", 8, suffix="~") == "hello w~"

    def test_very_short_max_length(self):
        assert truncate("hello world", 3) == "..."

    def test_max_length_shorter_than_suffix(self):
        assert truncate("hello world", 2) == ".."

    def test_empty_suffix(self):
        assert truncate("hello world", 5, suffix="") == "hello"


class TestRemoveHtmlTags:
    """Tests for remove_html_tags."""

    def test_simple_tags(self):
        assert remove_html_tags("<p>Hello</p>") == "Hello"

    def test_nested_tags(self):
        assert remove_html_tags("<div><span>Hello</span></div>") == "Hello"

    def test_no_tags(self):
        assert remove_html_tags("Hello World") == "Hello World"

    def test_html_entities_decoded(self):
        assert remove_html_tags("&lt;script&gt;") == "<script>"

    def test_nbsp_decoded(self):
        assert remove_html_tags("Hello&nbsp;World") == "Hello World"

    def test_amp_decoded(self):
        assert remove_html_tags("Tom &amp; Jerry") == "Tom & Jerry"

    def test_quot_decoded(self):
        assert remove_html_tags("&quot;Hello&quot;") == '"Hello"'

    def test_apos_decoded(self):
        assert remove_html_tags("it&#39;s") == "it's"


class TestExtractInitials:
    """Tests for extract_initials."""

    def test_two_word_name(self):
        assert extract_initials("John Doe") == "JD"

    def test_three_word_name(self):
        assert extract_initials("John Michael Doe") == "JMD"

    def test_single_name(self):
        assert extract_initials("John") == "J"

    def test_empty_string(self):
        assert extract_initials("") == ""

    def test_max_initials_limit(self):
        assert extract_initials("A B C D E", max_initials=2) == "AB"

    def test_lowercase_input(self):
        assert extract_initials("john doe") == "JD"

    def test_extra_whitespace(self):
        assert extract_initials("  John   Doe  ") == "JD"


class TestNormalizeWhitespace:
    """Tests for normalize_whitespace."""

    def test_multiple_spaces(self):
        assert normalize_whitespace("hello   world") == "hello world"

    def test_tabs_replaced(self):
        assert normalize_whitespace("hello\tworld") == "hello world"

    def test_newlines_replaced(self):
        assert normalize_whitespace("hello\nworld") == "hello world"

    def test_mixed_whitespace(self):
        assert normalize_whitespace("  hello \t world \n ") == "hello world"

    def test_already_normalized(self):
        assert normalize_whitespace("hello world") == "hello world"

    def test_leading_trailing_stripped(self):
        assert normalize_whitespace("  hello  ") == "hello"
