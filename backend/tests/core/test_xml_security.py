"""Tests for secure XML parsing (XXE prevention)."""

import pytest

from app.core.xml_security import parse_xml, parse_xml_defused, parse_xml_secure


# ==================== parse_xml_secure ====================


class TestParseXmlSecure:
    def test_valid_xml(self):
        root = parse_xml_secure("<root><child>value</child></root>")
        assert root.tag == "root"
        assert root.find("child").text == "value"

    def test_empty_element(self):
        root = parse_xml_secure("<root/>")
        assert root.tag == "root"

    def test_attributes(self):
        root = parse_xml_secure('<root attr="val"/>')
        assert root.get("attr") == "val"

    def test_nested(self):
        root = parse_xml_secure("<a><b><c>deep</c></b></a>")
        assert root.find(".//c").text == "deep"

    def test_blocks_entity(self):
        with pytest.raises(ValueError, match="ENTITY"):
            parse_xml_secure('<!ENTITY xxe "test"><root/>')

    def test_blocks_doctype(self):
        with pytest.raises(ValueError, match="DOCTYPE"):
            parse_xml_secure("<!DOCTYPE foo><root/>")

    def test_blocks_system_via_doctype(self):
        """SYSTEM keyword in DOCTYPE blocked (DOCTYPE caught first)."""
        with pytest.raises(ValueError, match="DOCTYPE"):
            parse_xml_secure('<!DOCTYPE foo SYSTEM "http://evil.com"><root/>')

    def test_blocks_system_standalone(self):
        """SYSTEM keyword without DOCTYPE prefix."""
        with pytest.raises(ValueError, match="SYSTEM"):
            parse_xml_secure("<root>SYSTEM /etc/passwd</root>")

    def test_blocks_file_protocol(self):
        with pytest.raises(ValueError, match="file://"):
            parse_xml_secure("<root>file:///etc/passwd</root>")

    def test_blocks_http(self):
        with pytest.raises(ValueError, match="http://"):
            parse_xml_secure("<root>http://evil.com</root>")

    def test_blocks_https(self):
        with pytest.raises(ValueError, match="https://"):
            parse_xml_secure("<root>https://evil.com</root>")

    def test_case_insensitive_blocking(self):
        with pytest.raises(ValueError):
            parse_xml_secure("<!doctype foo><root/>")

    def test_invalid_xml(self):
        with pytest.raises(ValueError, match="Invalid XML"):
            parse_xml_secure("<unclosed>")


# ==================== parse_xml_defused ====================


class TestParseXmlDefused:
    def test_valid_xml(self):
        root = parse_xml_defused("<root><child>hello</child></root>")
        assert root.tag == "root"

    def test_invalid_xml(self):
        with pytest.raises(ValueError, match="Invalid XML"):
            parse_xml_defused("<unclosed>")


# ==================== parse_xml alias ====================


class TestParseXmlAlias:
    def test_alias_is_secure(self):
        assert parse_xml is parse_xml_secure

    def test_alias_works(self):
        root = parse_xml("<root>ok</root>")
        assert root.tag == "root"
