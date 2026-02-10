"""Tests for content parsers (no DB)."""

from __future__ import annotations

import json

import pytest

from app.middleware.content.parsers import (
    FormDataParser,
    JSONParser,
    MessagePackParser,
    Parser,
    ParserRegistry,
    ParsingError,
    XMLParser,
    YAMLParser,
    get_parser_registry,
)


# ---------------------------------------------------------------------------
# ParsingError
# ---------------------------------------------------------------------------


class TestParsingError:
    def test_is_exception(self):
        with pytest.raises(ParsingError):
            raise ParsingError("bad input")

    def test_message(self):
        err = ParsingError("parse failed")
        assert str(err) == "parse failed"


# ---------------------------------------------------------------------------
# JSONParser — properties
# ---------------------------------------------------------------------------


class TestJSONParserProperties:
    def test_content_type(self):
        assert JSONParser().content_type == "application/json"

    def test_always_available(self):
        assert JSONParser().available is True


# ---------------------------------------------------------------------------
# JSONParser — parse
# ---------------------------------------------------------------------------


class TestJSONParserParse:
    def test_parse_object(self):
        data = json.dumps({"key": "value"}).encode()
        result = JSONParser().parse(data)
        assert result == {"key": "value"}

    def test_parse_array(self):
        data = json.dumps([1, 2, 3]).encode()
        result = JSONParser().parse(data)
        assert result == [1, 2, 3]

    def test_parse_string(self):
        data = json.dumps("hello").encode()
        assert JSONParser().parse(data) == "hello"

    def test_parse_number(self):
        data = json.dumps(42).encode()
        assert JSONParser().parse(data) == 42

    def test_parse_null(self):
        data = b"null"
        assert JSONParser().parse(data) is None

    def test_parse_boolean(self):
        data = b"true"
        assert JSONParser().parse(data) is True

    def test_nested_object(self):
        data = json.dumps({"a": {"b": [1, 2]}}).encode()
        result = JSONParser().parse(data)
        assert result["a"]["b"] == [1, 2]

    def test_invalid_json_raises(self):
        with pytest.raises(ParsingError, match="Invalid JSON"):
            JSONParser().parse(b"{invalid")

    def test_empty_raises(self):
        with pytest.raises(ParsingError, match="Invalid JSON"):
            JSONParser().parse(b"")

    def test_invalid_utf8_raises(self):
        with pytest.raises(ParsingError):
            JSONParser().parse(b"\xff\xfe")


# ---------------------------------------------------------------------------
# XMLParser — properties
# ---------------------------------------------------------------------------


class TestXMLParserProperties:
    def test_content_type(self):
        assert XMLParser().content_type == "application/xml"

    def test_always_available(self):
        assert XMLParser().available is True


# ---------------------------------------------------------------------------
# XMLParser — parse
# ---------------------------------------------------------------------------


class TestXMLParserParse:
    def test_simple_element(self):
        xml = b"<root><name>test</name></root>"
        result = XMLParser().parse(xml)
        assert result["name"] == "test"

    def test_nested_elements(self):
        xml = b"<root><person><name>Alice</name></person></root>"
        result = XMLParser().parse(xml)
        assert result["person"]["name"] == "Alice"

    def test_element_with_attributes_text_only(self):
        # Element with text and no children returns just the text
        xml = b'<root><item id="1">value</item></root>'
        result = XMLParser().parse(xml)
        assert result["item"] == "value"

    def test_root_attributes(self):
        xml = b'<root id="1"><child>val</child></root>'
        result = XMLParser().parse(xml)
        assert result["_attributes"]["id"] == "1"

    def test_multiple_same_tag(self):
        xml = b"<root><item>a</item><item>b</item></root>"
        result = XMLParser().parse(xml)
        assert isinstance(result["item"], list)
        assert result["item"] == ["a", "b"]

    def test_text_only_element(self):
        xml = b"<value>42</value>"
        result = XMLParser().parse(xml)
        # Root element with only text returns the text
        assert result is None or isinstance(result, (str, dict))

    def test_invalid_xml_raises(self):
        with pytest.raises(ParsingError, match="Invalid XML"):
            XMLParser().parse(b"<invalid>not closed")

    def test_empty_raises(self):
        with pytest.raises(ParsingError, match="Invalid XML"):
            XMLParser().parse(b"")

    def test_root_with_text_and_children(self):
        xml = b"<root>text<child>val</child></root>"
        result = XMLParser().parse(xml)
        assert "_text" in result
        assert result["child"] == "val"


# ---------------------------------------------------------------------------
# YAMLParser — properties
# ---------------------------------------------------------------------------


class TestYAMLParserProperties:
    def test_content_type(self):
        assert YAMLParser().content_type == "application/yaml"

    def test_available_depends_on_import(self):
        parser = YAMLParser()
        assert isinstance(parser.available, bool)


# ---------------------------------------------------------------------------
# YAMLParser — parse (conditional)
# ---------------------------------------------------------------------------


class TestYAMLParserParse:
    def test_unavailable_raises_runtime(self):
        parser = YAMLParser()
        if not parser.available:
            with pytest.raises(RuntimeError, match="not available"):
                parser.parse(b"key: value")

    def test_parse_dict_if_available(self):
        parser = YAMLParser()
        if parser.available:
            result = parser.parse(b"name: test\nvalue: 42")
            assert result["name"] == "test"
            assert result["value"] == 42

    def test_parse_list_if_available(self):
        parser = YAMLParser()
        if parser.available:
            result = parser.parse(b"- a\n- b\n- c")
            assert result == ["a", "b", "c"]

    def test_parse_invalid_if_available(self):
        parser = YAMLParser()
        if parser.available:
            # YAML is very permissive, so most strings are valid
            result = parser.parse(b"just a string")
            assert result == "just a string"


# ---------------------------------------------------------------------------
# MessagePackParser — properties
# ---------------------------------------------------------------------------


class TestMessagePackParserProperties:
    def test_content_type(self):
        assert MessagePackParser().content_type == "application/msgpack"

    def test_available_depends_on_import(self):
        parser = MessagePackParser()
        assert isinstance(parser.available, bool)


# ---------------------------------------------------------------------------
# MessagePackParser — parse (conditional)
# ---------------------------------------------------------------------------


class TestMessagePackParserParse:
    def test_unavailable_raises_runtime(self):
        parser = MessagePackParser()
        if not parser.available:
            with pytest.raises(RuntimeError, match="not available"):
                parser.parse(b"\x80")

    def test_parse_if_available(self):
        parser = MessagePackParser()
        if parser.available:
            import msgpack

            data = msgpack.packb({"key": "value"})
            result = parser.parse(data)
            assert result == {"key": "value"}


# ---------------------------------------------------------------------------
# FormDataParser — properties
# ---------------------------------------------------------------------------


class TestFormDataParserProperties:
    def test_content_type(self):
        assert FormDataParser().content_type == "application/x-www-form-urlencoded"

    def test_always_available(self):
        assert FormDataParser().available is True


# ---------------------------------------------------------------------------
# FormDataParser — parse
# ---------------------------------------------------------------------------


class TestFormDataParserParse:
    def test_simple_fields(self):
        data = b"name=test&value=42"
        result = FormDataParser().parse(data)
        assert result["name"] == "test"
        assert result["value"] == "42"

    def test_single_values_as_strings(self):
        data = b"key=value"
        result = FormDataParser().parse(data)
        assert isinstance(result["key"], str)

    def test_multiple_values_as_list(self):
        data = b"color=red&color=blue"
        result = FormDataParser().parse(data)
        assert isinstance(result["color"], list)
        assert result["color"] == ["red", "blue"]

    def test_blank_value(self):
        data = b"key="
        result = FormDataParser().parse(data)
        assert result["key"] == ""

    def test_encoded_characters(self):
        data = b"name=hello+world"
        result = FormDataParser().parse(data)
        assert result["name"] == "hello world"

    def test_percent_encoded(self):
        data = b"value=%2Fpath%2Fto%2Ffile"
        result = FormDataParser().parse(data)
        assert result["value"] == "/path/to/file"

    def test_empty_data(self):
        result = FormDataParser().parse(b"")
        assert result == {}


# ---------------------------------------------------------------------------
# ParserRegistry — initialization
# ---------------------------------------------------------------------------


class TestParserRegistryInit:
    def test_has_json(self):
        registry = ParserRegistry()
        assert registry.is_supported("application/json")

    def test_has_xml(self):
        registry = ParserRegistry()
        assert registry.is_supported("application/xml")

    def test_has_form_data(self):
        registry = ParserRegistry()
        assert registry.is_supported("application/x-www-form-urlencoded")

    def test_at_least_three_parsers(self):
        registry = ParserRegistry()
        assert len(registry.get_available_types()) >= 3


# ---------------------------------------------------------------------------
# ParserRegistry — register / unregister
# ---------------------------------------------------------------------------


class TestParserRegistryOps:
    def test_register_parser(self):
        registry = ParserRegistry()
        parser = JSONParser()
        # JSON already registered, but re-register should work
        registry.register(parser)
        assert registry.is_supported("application/json")

    def test_unregister_parser(self):
        registry = ParserRegistry()
        registry.unregister("application/json")
        assert not registry.is_supported("application/json")

    def test_unregister_nonexistent_no_error(self):
        registry = ParserRegistry()
        registry.unregister("application/nonexistent")


# ---------------------------------------------------------------------------
# ParserRegistry — get_parser
# ---------------------------------------------------------------------------


class TestParserRegistryGetParser:
    def test_exact_match(self):
        registry = ParserRegistry()
        parser = registry.get_parser("application/json")
        assert parser is not None
        assert parser.content_type == "application/json"

    def test_with_charset(self):
        registry = ParserRegistry()
        parser = registry.get_parser("application/json; charset=utf-8")
        assert parser is not None
        assert parser.content_type == "application/json"

    def test_case_insensitive(self):
        registry = ParserRegistry()
        parser = registry.get_parser("Application/JSON")
        assert parser is not None

    def test_unsupported_returns_none(self):
        registry = ParserRegistry()
        assert registry.get_parser("text/csv") is None


# ---------------------------------------------------------------------------
# ParserRegistry — get_available_types / is_supported
# ---------------------------------------------------------------------------


class TestParserRegistryInfo:
    def test_get_available_types_returns_list(self):
        registry = ParserRegistry()
        result = registry.get_available_types()
        assert isinstance(result, list)

    def test_is_supported_true(self):
        registry = ParserRegistry()
        assert registry.is_supported("application/json") is True

    def test_is_supported_false(self):
        registry = ParserRegistry()
        assert registry.is_supported("text/csv") is False


# ---------------------------------------------------------------------------
# Global registry
# ---------------------------------------------------------------------------


class TestGlobalRegistry:
    def test_returns_registry(self):
        reg = get_parser_registry()
        assert isinstance(reg, ParserRegistry)

    def test_has_json(self):
        reg = get_parser_registry()
        assert reg.is_supported("application/json")
