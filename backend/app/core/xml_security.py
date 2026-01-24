"""
Secure XML parsing utilities to prevent XXE attacks.

XML External Entity (XXE) attacks can allow attackers to:
- Read arbitrary files from the server
- Perform SSRF attacks
- Cause denial of service

This module provides secure alternatives using defusedxml or
secure ElementTree configuration.
"""

import logging
from typing import Any, cast
from xml.etree import ElementTree as ET

logger = logging.getLogger(__name__)


def parse_xml_secure(xml_string: str) -> ET.Element:
    """
    Parse XML string securely, preventing XXE attacks.

    Args:
        xml_string: Raw XML string to parse

    Returns:
        Root element of parsed XML

    Raises:
        ValueError: If XML is invalid or contains malicious content

    Example:
        >>> xml_data = '<root><child>value</child></root>'
        >>> root = parse_xml_secure(xml_data)
        >>> root.tag
        'root'

    Security:
        This function blocks common XXE attack patterns including:
        - External entity declarations (<!ENTITY)
        - DOCTYPE declarations
        - SYSTEM references
        - External protocol handlers (file://, http://, https://)

    Note:
        For production use, consider using the defusedxml library instead:
        `from defusedxml.ElementTree import fromstring as parse_xml_secure`

        Install with: pip install defusedxml
    """
    # Check for common XXE patterns
    dangerous_patterns = [
        "<!ENTITY",
        "<!DOCTYPE",
        "SYSTEM",
        "file://",
        "http://",
        "https://",
    ]

    xml_lower = xml_string.lower()
    for pattern in dangerous_patterns:
        if pattern.lower() in xml_lower:
            logger.warning(f"Blocked potential XXE attack: found '{pattern}'")
            raise ValueError(f"XML contains potentially dangerous content: {pattern}")

    try:
        return ET.fromstring(xml_string)
    except ET.ParseError as e:
        logger.error(f"XML parsing error: {e}")
        raise ValueError(f"Invalid XML: {e}") from e


def parse_xml_defused(xml_string: str) -> ET.Element:
    """
    Parse XML using defusedxml library (recommended for production).

    This is a placeholder that will use defusedxml if installed,
    otherwise falls back to pattern-based validation.

    Args:
        xml_string: Raw XML string to parse

    Returns:
        Root element of parsed XML

    Raises:
        ValueError: If XML is invalid or contains malicious content
        ImportError: If defusedxml is not installed (with helpful message)

    Example:
        >>> # In production with defusedxml installed:
        >>> xml_data = '<root><child>value</child></root>'
        >>> root = parse_xml_defused(xml_data)
    """
    try:
        # Try to use defusedxml (preferred)
        from defusedxml.ElementTree import fromstring

        logger.debug("Using defusedxml for secure XML parsing")
        try:
            return cast(ET.Element[str], fromstring(xml_string))
        except Exception as e:
            logger.error(f"XML parsing error (defusedxml): {e}")
            raise ValueError(f"Invalid XML: {e}") from e

    except ImportError:
        logger.warning(
            "defusedxml not installed, falling back to pattern-based validation. "
            "For production, install defusedxml: pip install defusedxml"
        )
        # Fall back to pattern-based validation
        return parse_xml_secure(xml_string)


# Alias for convenience
parse_xml = parse_xml_secure
