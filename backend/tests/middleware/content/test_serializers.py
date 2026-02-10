"""Tests for content serializers (no DB)."""

from __future__ import annotations

import json

import pytest

from app.middleware.content.serializers import (
    JSONSerializer,
    MessagePackSerializer,
    SerializationError,
    SerializerRegistry,
    XMLSerializer,
    YAMLSerializer,
    get_serializer_registry,
)


# ---------------------------------------------------------------------------
# SerializationError
# ---------------------------------------------------------------------------


class TestSerializationError:
    def test_is_exception(self):
        with pytest.raises(SerializationError):
            raise SerializationError("failed")

    def test_message(self):
        err = SerializationError("serialize failed")
        assert str(err) == "serialize failed"


# ---------------------------------------------------------------------------
# JSONSerializer — properties
# ---------------------------------------------------------------------------


class TestJSONSerializerProperties:
    def test_content_type(self):
        assert JSONSerializer().content_type == "application/json"

    def test_always_available(self):
        assert JSONSerializer().available is True

    def test_default_indent_none(self):
        s = JSONSerializer()
        assert s.indent is None

    def test_default_ensure_ascii_false(self):
        s = JSONSerializer()
        assert s.ensure_ascii is False

    def test_custom_indent(self):
        s = JSONSerializer(indent=2)
        assert s.indent == 2


# ---------------------------------------------------------------------------
# JSONSerializer — serialize
# ---------------------------------------------------------------------------


class TestJSONSerializerSerialize:
    def test_dict(self):
        result = JSONSerializer().serialize({"key": "value"})
        assert isinstance(result, bytes)
        assert json.loads(result) == {"key": "value"}

    def test_list(self):
        result = JSONSerializer().serialize([1, 2, 3])
        assert json.loads(result) == [1, 2, 3]

    def test_string(self):
        result = JSONSerializer().serialize("hello")
        assert json.loads(result) == "hello"

    def test_number(self):
        result = JSONSerializer().serialize(42)
        assert json.loads(result) == 42

    def test_null(self):
        result = JSONSerializer().serialize(None)
        assert json.loads(result) is None

    def test_nested(self):
        data = {"a": {"b": [1, 2]}}
        result = JSONSerializer().serialize(data)
        assert json.loads(result) == data

    def test_compact_no_indent(self):
        result = JSONSerializer().serialize({"a": 1})
        # Compact should not have newlines in simple objects
        text = result.decode("utf-8")
        assert "\n" not in text

    def test_indented(self):
        result = JSONSerializer(indent=2).serialize({"a": 1})
        text = result.decode("utf-8")
        assert "\n" in text

    def test_unicode_preserved(self):
        result = JSONSerializer(ensure_ascii=False).serialize({"name": "José"})
        text = result.decode("utf-8")
        assert "José" in text

    def test_unicode_escaped(self):
        result = JSONSerializer(ensure_ascii=True).serialize({"name": "José"})
        text = result.decode("utf-8")
        assert "\\u" in text

    def test_non_serializable_converted_to_string(self):
        from datetime import datetime

        data = {"time": datetime(2026, 1, 15)}
        result = JSONSerializer().serialize(data)
        parsed = json.loads(result)
        assert isinstance(parsed["time"], str)


# ---------------------------------------------------------------------------
# XMLSerializer — properties
# ---------------------------------------------------------------------------


class TestXMLSerializerProperties:
    def test_content_type(self):
        assert XMLSerializer().content_type == "application/xml"

    def test_always_available(self):
        assert XMLSerializer().available is True

    def test_default_root_tag(self):
        s = XMLSerializer()
        assert s.root_tag == "response"

    def test_custom_root_tag(self):
        s = XMLSerializer(root_tag="data")
        assert s.root_tag == "data"


# ---------------------------------------------------------------------------
# XMLSerializer — serialize
# ---------------------------------------------------------------------------


class TestXMLSerializerSerialize:
    def test_returns_bytes(self):
        result = XMLSerializer().serialize({"key": "value"})
        assert isinstance(result, bytes)

    def test_contains_xml_declaration(self):
        result = XMLSerializer().serialize({"key": "value"})
        text = result.decode("utf-8")
        assert "<?xml" in text

    def test_contains_root_tag(self):
        result = XMLSerializer(root_tag="data").serialize({"key": "value"})
        text = result.decode("utf-8")
        assert "<data>" in text or "<data " in text

    def test_dict_children(self):
        result = XMLSerializer().serialize({"name": "test"})
        text = result.decode("utf-8")
        assert "<name>test</name>" in text

    def test_nested_dict(self):
        result = XMLSerializer().serialize({"person": {"name": "Alice"}})
        text = result.decode("utf-8")
        assert "<person>" in text
        assert "<name>Alice</name>" in text

    def test_list_creates_items(self):
        result = XMLSerializer().serialize({"items": [1, 2]})
        text = result.decode("utf-8")
        assert "<item>1</item>" in text
        assert "<item>2</item>" in text

    def test_none_value(self):
        result = XMLSerializer().serialize({"key": None})
        text = result.decode("utf-8")
        assert "<key" in text  # May be <key></key>, <key/>, or <key />


# ---------------------------------------------------------------------------
# YAMLSerializer — properties
# ---------------------------------------------------------------------------


class TestYAMLSerializerProperties:
    def test_content_type(self):
        assert YAMLSerializer().content_type == "application/yaml"

    def test_available_depends_on_import(self):
        s = YAMLSerializer()
        assert isinstance(s.available, bool)


# ---------------------------------------------------------------------------
# YAMLSerializer — serialize (conditional)
# ---------------------------------------------------------------------------


class TestYAMLSerializerSerialize:
    def test_unavailable_raises_runtime(self):
        s = YAMLSerializer()
        if not s.available:
            with pytest.raises(RuntimeError, match="not available"):
                s.serialize({"key": "value"})

    def test_dict_if_available(self):
        s = YAMLSerializer()
        if s.available:
            result = s.serialize({"name": "test", "value": 42})
            assert isinstance(result, bytes)
            text = result.decode("utf-8")
            assert "name:" in text
            assert "test" in text

    def test_list_if_available(self):
        s = YAMLSerializer()
        if s.available:
            result = s.serialize([1, 2, 3])
            assert isinstance(result, bytes)


# ---------------------------------------------------------------------------
# MessagePackSerializer — properties
# ---------------------------------------------------------------------------


class TestMessagePackSerializerProperties:
    def test_content_type(self):
        assert MessagePackSerializer().content_type == "application/msgpack"

    def test_available_depends_on_import(self):
        s = MessagePackSerializer()
        assert isinstance(s.available, bool)


# ---------------------------------------------------------------------------
# MessagePackSerializer — serialize (conditional)
# ---------------------------------------------------------------------------


class TestMessagePackSerializerSerialize:
    def test_unavailable_raises_runtime(self):
        s = MessagePackSerializer()
        if not s.available:
            with pytest.raises(RuntimeError, match="not available"):
                s.serialize({"key": "value"})

    def test_round_trip_if_available(self):
        s = MessagePackSerializer()
        if s.available:
            import msgpack

            data = {"key": "value", "num": 42}
            result = s.serialize(data)
            assert isinstance(result, bytes)
            assert msgpack.unpackb(result, raw=False) == data


# ---------------------------------------------------------------------------
# SerializerRegistry — initialization
# ---------------------------------------------------------------------------


class TestSerializerRegistryInit:
    def test_has_json(self):
        registry = SerializerRegistry()
        assert registry.is_supported("application/json")

    def test_has_xml(self):
        registry = SerializerRegistry()
        assert registry.is_supported("application/xml")

    def test_at_least_two_serializers(self):
        registry = SerializerRegistry()
        assert len(registry.get_available_types()) >= 2


# ---------------------------------------------------------------------------
# SerializerRegistry — register / unregister
# ---------------------------------------------------------------------------


class TestSerializerRegistryOps:
    def test_register_serializer(self):
        registry = SerializerRegistry()
        registry.register(JSONSerializer())
        assert registry.is_supported("application/json")

    def test_unregister_serializer(self):
        registry = SerializerRegistry()
        registry.unregister("application/json")
        assert not registry.is_supported("application/json")

    def test_unregister_nonexistent_no_error(self):
        registry = SerializerRegistry()
        registry.unregister("application/nonexistent")


# ---------------------------------------------------------------------------
# SerializerRegistry — get_serializer
# ---------------------------------------------------------------------------


class TestSerializerRegistryGetSerializer:
    def test_exact_match(self):
        registry = SerializerRegistry()
        s = registry.get_serializer("application/json")
        assert s is not None
        assert s.content_type == "application/json"

    def test_with_charset(self):
        registry = SerializerRegistry()
        s = registry.get_serializer("application/json; charset=utf-8")
        assert s is not None

    def test_case_insensitive(self):
        registry = SerializerRegistry()
        s = registry.get_serializer("Application/JSON")
        assert s is not None

    def test_unsupported_returns_none(self):
        registry = SerializerRegistry()
        assert registry.get_serializer("text/csv") is None


# ---------------------------------------------------------------------------
# SerializerRegistry — info
# ---------------------------------------------------------------------------


class TestSerializerRegistryInfo:
    def test_get_available_types_returns_list(self):
        registry = SerializerRegistry()
        result = registry.get_available_types()
        assert isinstance(result, list)

    def test_is_supported_true(self):
        registry = SerializerRegistry()
        assert registry.is_supported("application/json") is True

    def test_is_supported_false(self):
        registry = SerializerRegistry()
        assert registry.is_supported("text/csv") is False


# ---------------------------------------------------------------------------
# Global registry
# ---------------------------------------------------------------------------


class TestGlobalSerializerRegistry:
    def test_returns_registry(self):
        reg = get_serializer_registry()
        assert isinstance(reg, SerializerRegistry)

    def test_has_json(self):
        reg = get_serializer_registry()
        assert reg.is_supported("application/json")
