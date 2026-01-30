"""
Format serializers for content negotiation.

Implements serializers for multiple formats:
- JSON (standard library)
- XML (if lxml available)
- YAML (if PyYAML available)
- MessagePack (if msgpack available)
- Custom format registration

Each serializer handles conversion from Python objects to format-specific bytes.
"""

import json
import logging
from abc import ABC, abstractmethod
from typing import Any

logger = logging.getLogger(__name__)


class Serializer(ABC):
    """
    Abstract base class for content serializers.

    Defines interface for converting Python objects to specific formats.
    """

    @property
    @abstractmethod
    def content_type(self) -> str:
        """Get MIME type for this serializer."""
        pass

    @property
    @abstractmethod
    def available(self) -> bool:
        """Check if serializer is available."""
        pass

    @abstractmethod
    def serialize(self, data: Any) -> bytes:
        """
        Serialize data to bytes.

        Args:
            data: Python object to serialize

        Returns:
            Serialized bytes

        Raises:
            SerializationError: If serialization fails
        """
        pass


class SerializationError(Exception):
    """Exception raised when serialization fails."""

    pass


class JSONSerializer(Serializer):
    """
    JSON serializer using standard library.

    Always available as it uses Python's built-in json module.
    Supports additional formatting options for development.
    """

    def __init__(self, indent: int | None = None, ensure_ascii: bool = False) -> None:
        """
        Initialize JSON serializer.

        Args:
            indent: Number of spaces for indentation (None for compact)
            ensure_ascii: If True, escape non-ASCII characters
        """
        self.indent = indent
        self.ensure_ascii = ensure_ascii
        logger.debug(
            f"JSONSerializer initialized: indent={indent}, ensure_ascii={ensure_ascii}"
        )

    @property
    def content_type(self) -> str:
        """Get MIME type for JSON."""
        return "application/json"

    @property
    def available(self) -> bool:
        """JSON is always available (standard library)."""
        return True

    def serialize(self, data: Any) -> bytes:
        """
        Serialize data to JSON.

        Args:
            data: Python object to serialize (dict, list, etc.)

        Returns:
            JSON bytes

        Raises:
            SerializationError: If serialization fails
        """
        try:
            json_str = json.dumps(
                data,
                indent=self.indent,
                ensure_ascii=self.ensure_ascii,
                default=str,  # Convert non-serializable to string
            )
            return json_str.encode("utf-8")
        except Exception as e:
            raise SerializationError(f"JSON serialization failed: {e}") from e


class XMLSerializer(Serializer):
    """
    XML serializer using lxml or xml.etree.

    Falls back to xml.etree if lxml is not available.
    Converts Python dicts to XML format.
    """

    def __init__(self, root_tag: str = "response", pretty_print: bool = False) -> None:
        """
        Initialize XML serializer.

        Args:
            root_tag: Root element tag name
            pretty_print: If True, format with indentation
        """
        self.root_tag = root_tag
        self.pretty_print = pretty_print

        # Try to use lxml (more powerful)
        try:
            from lxml import etree

            self._etree = etree
            self._lxml_available = True
            logger.debug("XMLSerializer using lxml")
        except ImportError:
            # Fallback to standard library
            import xml.etree.ElementTree as etree

            self._etree = etree
            self._lxml_available = False
            logger.debug("XMLSerializer using xml.etree (fallback)")

    @property
    def content_type(self) -> str:
        """Get MIME type for XML."""
        return "application/xml"

    @property
    def available(self) -> bool:
        """XML is always available (standard library or lxml)."""
        return True

    def serialize(self, data: Any) -> bytes:
        """
        Serialize data to XML.

        Args:
            data: Python object to serialize (typically dict)

        Returns:
            XML bytes

        Raises:
            SerializationError: If serialization fails
        """
        try:
            # Create root element
            if self._lxml_available:
                root = self._etree.Element(self.root_tag)
            else:
                root = self._etree.Element(self.root_tag)

                # Convert data to XML elements
            self._dict_to_xml(root, data)

            # Convert to bytes
            if self._lxml_available:
                xml_bytes = self._etree.tostring(
                    root,
                    pretty_print=self.pretty_print,
                    xml_declaration=True,
                    encoding="utf-8",
                )
            else:
                tree = self._etree.ElementTree(root)
                import io

                output = io.BytesIO()
                tree.write(output, encoding="utf-8", xml_declaration=True)
                xml_bytes = output.getvalue()

            return xml_bytes
        except Exception as e:
            raise SerializationError(f"XML serialization failed: {e}") from e

    def _dict_to_xml(self, parent, data) -> None:
        """
        Convert dictionary to XML elements.

        Args:
            parent: Parent XML element
            data: Data to convert (dict, list, or primitive)
        """
        if isinstance(data, dict):
            for key, value in data.items():
                # Create child element
                child = self._etree.SubElement(parent, str(key))
                self._dict_to_xml(child, value)
        elif isinstance(data, list):
            for item in data:
                # Create item element
                child = self._etree.SubElement(parent, "item")
                self._dict_to_xml(child, item)
        else:
            # Set text content
            parent.text = str(data) if data is not None else ""


class YAMLSerializer(Serializer):
    """
    YAML serializer using PyYAML.

    Requires PyYAML package. Falls back gracefully if not available.
    """

    def __init__(self, default_flow_style: bool = False) -> None:
        """
        Initialize YAML serializer.

        Args:
            default_flow_style: If True, use flow style (inline)
        """
        self.default_flow_style = default_flow_style

        # Try to import PyYAML
        try:
            import yaml

            self._yaml = yaml
            self._available = True
            logger.debug("YAMLSerializer initialized")
        except ImportError:
            self._yaml = None
            self._available = False
            logger.warning(
                "YAML serialization not available. Install with: pip install pyyaml"
            )

    @property
    def content_type(self) -> str:
        """Get MIME type for YAML."""
        return "application/yaml"

    @property
    def available(self) -> bool:
        """Check if PyYAML is available."""
        return self._available

    def serialize(self, data: Any) -> bytes:
        """
        Serialize data to YAML.

        Args:
            data: Python object to serialize

        Returns:
            YAML bytes

        Raises:
            SerializationError: If serialization fails
            RuntimeError: If YAML is not available
        """
        if not self.available:
            raise RuntimeError("YAML serialization not available")

        try:
            yaml_str = self._yaml.dump(
                data,
                default_flow_style=self.default_flow_style,
                allow_unicode=True,
            )
            return yaml_str.encode("utf-8")
        except Exception as e:
            raise SerializationError(f"YAML serialization failed: {e}") from e


class MessagePackSerializer(Serializer):
    """
    MessagePack serializer for binary format.

    Requires msgpack package. MessagePack is a binary format
    that's more compact than JSON.
    """

    def __init__(self, use_bin_type: bool = True) -> None:
        """
        Initialize MessagePack serializer.

        Args:
            use_bin_type: If True, use binary type for bytes
        """
        self.use_bin_type = use_bin_type

        # Try to import msgpack
        try:
            import msgpack

            self._msgpack = msgpack
            self._available = True
            logger.debug("MessagePackSerializer initialized")
        except ImportError:
            self._msgpack = None
            self._available = False
            logger.warning(
                "MessagePack serialization not available. "
                "Install with: pip install msgpack"
            )

    @property
    def content_type(self) -> str:
        """Get MIME type for MessagePack."""
        return "application/msgpack"

    @property
    def available(self) -> bool:
        """Check if msgpack is available."""
        return self._available

    def serialize(self, data: Any) -> bytes:
        """
        Serialize data to MessagePack.

        Args:
            data: Python object to serialize

        Returns:
            MessagePack bytes

        Raises:
            SerializationError: If serialization fails
            RuntimeError: If MessagePack is not available
        """
        if not self.available:
            raise RuntimeError("MessagePack serialization not available")

        try:
            return self._msgpack.packb(
                data,
                use_bin_type=self.use_bin_type,
                default=str,  # Convert non-serializable to string
            )
        except Exception as e:
            raise SerializationError(f"MessagePack serialization failed: {e}") from e


class SerializerRegistry:
    """
    Registry for managing available serializers.

    Allows custom serializer registration and provides
    serializer lookup by content type.
    """

    def __init__(self) -> None:
        """Initialize serializer registry with default serializers."""
        self._serializers: dict[str, Serializer] = {}
        self._register_default_serializers()

    def _register_default_serializers(self) -> None:
        """Register default serializers (JSON, XML, YAML, MessagePack)."""
        # JSON (always available)
        self.register(JSONSerializer())

        # XML (always available)
        self.register(XMLSerializer())

        # YAML (if available)
        yaml_serializer = YAMLSerializer()
        if yaml_serializer.available:
            self.register(yaml_serializer)

            # MessagePack (if available)
        msgpack_serializer = MessagePackSerializer()
        if msgpack_serializer.available:
            self.register(msgpack_serializer)

        logger.info(
            f"SerializerRegistry initialized with {len(self._serializers)} serializers: "
            f"{list(self._serializers.keys())}"
        )

    def register(self, serializer: Serializer) -> None:
        """
        Register a serializer.

        Args:
            serializer: Serializer instance to register
        """
        if not serializer.available:
            logger.warning(
                f"Cannot register unavailable serializer: {serializer.content_type}"
            )
            return

        self._serializers[serializer.content_type] = serializer
        logger.debug(f"Registered serializer: {serializer.content_type}")

    def unregister(self, content_type: str) -> None:
        """
        Unregister a serializer.

        Args:
            content_type: MIME type of serializer to remove
        """
        if content_type in self._serializers:
            del self._serializers[content_type]
            logger.debug(f"Unregistered serializer: {content_type}")

    def get_serializer(self, content_type: str) -> Serializer | None:
        """
        Get serializer for content type.

        Args:
            content_type: MIME type (e.g., "application/json")

        Returns:
            Serializer instance, or None if not found
        """
        # Strip parameters from content type (e.g., "application/json; charset=utf-8")
        base_content_type = content_type.split(";")[0].strip().lower()
        return self._serializers.get(base_content_type)

    def get_available_types(self) -> list[str]:
        """
        Get list of available content types.

        Returns:
            List of MIME types
        """
        return list(self._serializers.keys())

    def is_supported(self, content_type: str) -> bool:
        """
        Check if content type is supported.

        Args:
            content_type: MIME type to check

        Returns:
            True if supported
        """
        return self.get_serializer(content_type) is not None

        # Global registry instance


_global_registry = SerializerRegistry()


def get_serializer_registry() -> SerializerRegistry:
    """
    Get global serializer registry.

    Returns:
        Global SerializerRegistry instance
    """
    return _global_registry


def register_serializer(serializer: Serializer) -> None:
    """
    Register a custom serializer globally.

    Args:
        serializer: Serializer instance to register
    """
    _global_registry.register(serializer)
