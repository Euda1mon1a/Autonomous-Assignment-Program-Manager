"""
Content parsers for request body parsing.

Implements parsers for multiple formats:
- JSON (standard library)
- XML (if lxml available)
- YAML (if PyYAML available)
- MessagePack (if msgpack available)
- Form data (standard library)
- Custom format registration

Each parser handles conversion from format-specific bytes to Python objects.
"""

import json
import logging
from abc import ABC, abstractmethod
from typing import Any
from urllib.parse import parse_qs

logger = logging.getLogger(__name__)


class Parser(ABC):
    """
    Abstract base class for content parsers.

    Defines interface for parsing request bodies to Python objects.
    """

    @property
    @abstractmethod
    def content_type(self) -> str:
        """Get MIME type this parser handles."""
        pass

    @property
    @abstractmethod
    def available(self) -> bool:
        """Check if parser is available."""
        pass

    @abstractmethod
    def parse(self, data: bytes) -> Any:
        """
        Parse bytes to Python object.

        Args:
            data: Raw bytes to parse

        Returns:
            Parsed Python object

        Raises:
            ParsingError: If parsing fails
        """
        pass


class ParsingError(Exception):
    """Exception raised when parsing fails."""

    pass


class JSONParser(Parser):
    """
    JSON parser using standard library.

    Always available as it uses Python's built-in json module.
    """

    @property
    def content_type(self) -> str:
        """Get MIME type for JSON."""
        return "application/json"

    @property
    def available(self) -> bool:
        """JSON parser is always available."""
        return True

    def parse(self, data: bytes) -> Any:
        """
        Parse JSON bytes to Python object.

        Args:
            data: JSON bytes

        Returns:
            Python object (dict, list, etc.)

        Raises:
            ParsingError: If JSON is invalid
        """
        try:
            return json.loads(data.decode("utf-8"))
        except json.JSONDecodeError as e:
            raise ParsingError(f"Invalid JSON: {e}") from e
        except UnicodeDecodeError as e:
            raise ParsingError(f"Invalid UTF-8 encoding: {e}") from e


class XMLParser(Parser):
    """
    XML parser using lxml or xml.etree.

    Falls back to xml.etree if lxml is not available.
    Converts XML to Python dicts.
    """

    def __init__(self):
        """Initialize XML parser."""
        # Try to use lxml (more powerful)
        try:
            from lxml import etree

            self._etree = etree
            self._lxml_available = True
            logger.debug("XMLParser using lxml")
        except ImportError:
            # Fallback to standard library
            import xml.etree.ElementTree as etree

            self._etree = etree
            self._lxml_available = False
            logger.debug("XMLParser using xml.etree (fallback)")

    @property
    def content_type(self) -> str:
        """Get MIME type for XML."""
        return "application/xml"

    @property
    def available(self) -> bool:
        """XML parser is always available."""
        return True

    def parse(self, data: bytes) -> Any:
        """
        Parse XML bytes to Python object.

        Args:
            data: XML bytes

        Returns:
            Python dict representation of XML

        Raises:
            ParsingError: If XML is invalid
        """
        try:
            # Parse XML
            if self._lxml_available:
                root = self._etree.fromstring(data)
            else:
                root = self._etree.fromstring(data)

            # Convert to dict
            return self._element_to_dict(root)
        except Exception as e:
            raise ParsingError(f"Invalid XML: {e}") from e

    def _element_to_dict(self, element) -> dict:
        """
        Convert XML element to dictionary.

        Args:
            element: XML element

        Returns:
            Dictionary representation
        """
        result = {}

        # Add element text if present
        if element.text and element.text.strip():
            if len(element) > 0:
                # Has children, use special key
                result["_text"] = element.text.strip()
            else:
                # No children, text is the value
                return element.text.strip()

        # Process children
        children = {}
        for child in element:
            child_data = self._element_to_dict(child)
            tag = child.tag

            # Handle multiple children with same tag
            if tag in children:
                # Convert to list if not already
                if not isinstance(children[tag], list):
                    children[tag] = [children[tag]]
                children[tag].append(child_data)
            else:
                children[tag] = child_data

        result.update(children)

        # Add attributes
        if element.attrib:
            result["_attributes"] = dict(element.attrib)

        return result if result else None


class YAMLParser(Parser):
    """
    YAML parser using PyYAML.

    Requires PyYAML package. Falls back gracefully if not available.
    """

    def __init__(self):
        """Initialize YAML parser."""
        # Try to import PyYAML
        try:
            import yaml

            self._yaml = yaml
            self._available = True
            logger.debug("YAMLParser initialized")
        except ImportError:
            self._yaml = None
            self._available = False
            logger.warning(
                "YAML parsing not available. Install with: pip install pyyaml"
            )

    @property
    def content_type(self) -> str:
        """Get MIME type for YAML."""
        return "application/yaml"

    @property
    def available(self) -> bool:
        """Check if PyYAML is available."""
        return self._available

    def parse(self, data: bytes) -> Any:
        """
        Parse YAML bytes to Python object.

        Args:
            data: YAML bytes

        Returns:
            Python object

        Raises:
            ParsingError: If YAML is invalid
            RuntimeError: If YAML is not available
        """
        if not self.available:
            raise RuntimeError("YAML parsing not available")

        try:
            return self._yaml.safe_load(data.decode("utf-8"))
        except Exception as e:
            raise ParsingError(f"Invalid YAML: {e}") from e


class MessagePackParser(Parser):
    """
    MessagePack parser for binary format.

    Requires msgpack package. MessagePack is a binary format
    that's more compact than JSON.
    """

    def __init__(self):
        """Initialize MessagePack parser."""
        # Try to import msgpack
        try:
            import msgpack

            self._msgpack = msgpack
            self._available = True
            logger.debug("MessagePackParser initialized")
        except ImportError:
            self._msgpack = None
            self._available = False
            logger.warning(
                "MessagePack parsing not available. Install with: pip install msgpack"
            )

    @property
    def content_type(self) -> str:
        """Get MIME type for MessagePack."""
        return "application/msgpack"

    @property
    def available(self) -> bool:
        """Check if msgpack is available."""
        return self._available

    def parse(self, data: bytes) -> Any:
        """
        Parse MessagePack bytes to Python object.

        Args:
            data: MessagePack bytes

        Returns:
            Python object

        Raises:
            ParsingError: If MessagePack is invalid
            RuntimeError: If MessagePack is not available
        """
        if not self.available:
            raise RuntimeError("MessagePack parsing not available")

        try:
            return self._msgpack.unpackb(data, raw=False)
        except Exception as e:
            raise ParsingError(f"Invalid MessagePack: {e}") from e


class FormDataParser(Parser):
    """
    URL-encoded form data parser.

    Handles application/x-www-form-urlencoded content.
    Always available as it uses standard library.
    """

    @property
    def content_type(self) -> str:
        """Get MIME type for form data."""
        return "application/x-www-form-urlencoded"

    @property
    def available(self) -> bool:
        """Form parser is always available."""
        return True

    def parse(self, data: bytes) -> dict:
        """
        Parse form data to dictionary.

        Args:
            data: URL-encoded form data bytes

        Returns:
            Dictionary of form fields

        Raises:
            ParsingError: If form data is invalid
        """
        try:
            # Decode and parse query string
            query_string = data.decode("utf-8")
            parsed = parse_qs(query_string, keep_blank_values=True)

            # Convert single-value lists to strings
            result = {}
            for key, value in parsed.items():
                if len(value) == 1:
                    result[key] = value[0]
                else:
                    result[key] = value

            return result
        except Exception as e:
            raise ParsingError(f"Invalid form data: {e}") from e


class ParserRegistry:
    """
    Registry for managing available parsers.

    Allows custom parser registration and provides
    parser lookup by content type.
    """

    def __init__(self):
        """Initialize parser registry with default parsers."""
        self._parsers: dict[str, Parser] = {}
        self._register_default_parsers()

    def _register_default_parsers(self):
        """Register default parsers (JSON, XML, YAML, MessagePack, Form)."""
        # JSON (always available)
        self.register(JSONParser())

        # XML (always available)
        self.register(XMLParser())

        # YAML (if available)
        yaml_parser = YAMLParser()
        if yaml_parser.available:
            self.register(yaml_parser)

        # MessagePack (if available)
        msgpack_parser = MessagePackParser()
        if msgpack_parser.available:
            self.register(msgpack_parser)

        # Form data (always available)
        self.register(FormDataParser())

        logger.info(
            f"ParserRegistry initialized with {len(self._parsers)} parsers: "
            f"{list(self._parsers.keys())}"
        )

    def register(self, parser: Parser):
        """
        Register a parser.

        Args:
            parser: Parser instance to register
        """
        if not parser.available:
            logger.warning(f"Cannot register unavailable parser: {parser.content_type}")
            return

        self._parsers[parser.content_type] = parser
        logger.debug(f"Registered parser: {parser.content_type}")

    def unregister(self, content_type: str):
        """
        Unregister a parser.

        Args:
            content_type: MIME type of parser to remove
        """
        if content_type in self._parsers:
            del self._parsers[content_type]
            logger.debug(f"Unregistered parser: {content_type}")

    def get_parser(self, content_type: str) -> Parser | None:
        """
        Get parser for content type.

        Args:
            content_type: MIME type (e.g., "application/json")

        Returns:
            Parser instance, or None if not found
        """
        # Strip parameters from content type (e.g., "application/json; charset=utf-8")
        base_content_type = content_type.split(";")[0].strip().lower()
        return self._parsers.get(base_content_type)

    def get_available_types(self) -> list[str]:
        """
        Get list of available content types.

        Returns:
            List of MIME types
        """
        return list(self._parsers.keys())

    def is_supported(self, content_type: str) -> bool:
        """
        Check if content type is supported.

        Args:
            content_type: MIME type to check

        Returns:
            True if supported
        """
        return self.get_parser(content_type) is not None


# Global registry instance
_global_registry = ParserRegistry()


def get_parser_registry() -> ParserRegistry:
    """
    Get global parser registry.

    Returns:
        Global ParserRegistry instance
    """
    return _global_registry


def register_parser(parser: Parser):
    """
    Register a custom parser globally.

    Args:
        parser: Parser instance to register
    """
    _global_registry.register(parser)
