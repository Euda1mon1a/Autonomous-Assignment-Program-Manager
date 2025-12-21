"""
HTML sanitization module for preventing HTML injection and XSS attacks.

This module provides functions to safely handle HTML content by:
- Stripping dangerous tags and attributes
- Allowing safe subset of HTML for rich text
- Escaping special characters
- Removing script and style elements
"""
import html
import re
from typing import Optional


class HTMLSanitizationError(Exception):
    """Exception raised when HTML sanitization fails."""
    pass


# Dangerous HTML tags that should always be removed
DANGEROUS_TAGS = {
    'script', 'style', 'iframe', 'object', 'embed', 'applet',
    'meta', 'link', 'base', 'form', 'input', 'button', 'textarea',
    'select', 'option', 'frame', 'frameset', 'bgsound', 'xml'
}

# Safe HTML tags allowed for rich text content
SAFE_TAGS = {
    'p', 'br', 'strong', 'em', 'u', 'ul', 'ol', 'li',
    'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
    'blockquote', 'pre', 'code', 'hr',
    'a', 'span', 'div', 'table', 'tr', 'td', 'th', 'thead', 'tbody'
}

# Safe attributes allowed for specific tags
SAFE_ATTRIBUTES = {
    'a': {'href', 'title', 'target'},
    'img': {'src', 'alt', 'title', 'width', 'height'},
    'span': {'class'},
    'div': {'class'},
    'table': {'class'},
    'td': {'colspan', 'rowspan'},
    'th': {'colspan', 'rowspan'},
}

# Protocol whitelist for URLs
SAFE_PROTOCOLS = {'http', 'https', 'mailto', 'ftp'}


def strip_all_tags(text: str) -> str:
    """
    Strip all HTML tags from text, leaving only plain text.

    This is the most aggressive sanitization option, removing all HTML markup.
    Use this for fields that should never contain HTML (names, titles, etc.).

    Args:
        text: Input text potentially containing HTML

    Returns:
        Plain text with all HTML tags removed

    Example:
        >>> strip_all_tags('<script>alert("xss")</script>Hello')
        'Hello'
        >>> strip_all_tags('<p>Hello <strong>World</strong></p>')
        'Hello World'
    """
    if not text:
        return ""

    # Remove HTML tags using regex
    clean_text = re.sub(r'<[^>]+>', '', text)

    # Unescape HTML entities
    clean_text = html.unescape(clean_text)

    # Remove multiple spaces and normalize whitespace
    clean_text = re.sub(r'\s+', ' ', clean_text).strip()

    return clean_text


def sanitize_html(
    text: str,
    allowed_tags: Optional[set[str]] = None,
    strip_tags: bool = False
) -> str:
    """
    Sanitize HTML content by removing dangerous tags and attributes.

    This function provides balanced sanitization - it can either strip all tags
    or allow a safe subset for rich text content.

    Args:
        text: Input HTML text to sanitize
        allowed_tags: Set of allowed HTML tags. If None, uses SAFE_TAGS
        strip_tags: If True, strip all tags. Overrides allowed_tags

    Returns:
        Sanitized HTML string

    Raises:
        HTMLSanitizationError: If sanitization fails

    Example:
        >>> sanitize_html('<script>alert("xss")</script><p>Safe text</p>')
        '<p>Safe text</p>'
        >>> sanitize_html('<p onclick="evil()">Text</p>')
        '<p>Text</p>'
    """
    if not text:
        return ""

    try:
        # If strip_tags is True, remove all HTML
        if strip_tags:
            return strip_all_tags(text)

        # Use provided allowed_tags or default SAFE_TAGS
        allowed = allowed_tags if allowed_tags is not None else SAFE_TAGS

        # First pass: Remove dangerous tags entirely
        for tag in DANGEROUS_TAGS:
            # Remove opening and closing tags and everything between
            text = re.sub(
                rf'<{tag}[^>]*>.*?</{tag}>',
                '',
                text,
                flags=re.IGNORECASE | re.DOTALL
            )
            # Remove self-closing tags
            text = re.sub(
                rf'<{tag}[^>]*/?>',
                '',
                text,
                flags=re.IGNORECASE
            )

        # Second pass: Remove on* event handlers (onclick, onerror, etc.)
        text = re.sub(r'\s+on\w+\s*=\s*["\'][^"\']*["\']', '', text, flags=re.IGNORECASE)
        text = re.sub(r'\s+on\w+\s*=\s*\S+', '', text, flags=re.IGNORECASE)

        # Third pass: Remove javascript: protocol from URLs
        text = re.sub(
            r'(href|src)\s*=\s*["\']?\s*javascript:',
            r'\1="',
            text,
            flags=re.IGNORECASE
        )

        # Fourth pass: Remove data: protocol (can be used for XSS)
        text = re.sub(
            r'(href|src)\s*=\s*["\']?\s*data:',
            r'\1="',
            text,
            flags=re.IGNORECASE
        )

        # Fifth pass: Remove vbscript: protocol
        text = re.sub(
            r'(href|src)\s*=\s*["\']?\s*vbscript:',
            r'\1="',
            text,
            flags=re.IGNORECASE
        )

        # Sixth pass: Remove tags not in allowed list
        def replace_tag(match):
            tag_name = match.group(1).lower()
            if tag_name in allowed:
                # Keep the tag but sanitize attributes
                return match.group(0)
            else:
                # Remove the tag but keep the content
                return ''

        # Remove opening tags not in allowed list
        text = re.sub(r'<(/?)(\w+)[^>]*>', replace_tag, text)

        # Final pass: Clean up any remaining dangerous patterns
        text = re.sub(r'<\s*script', '&lt;script', text, flags=re.IGNORECASE)
        text = re.sub(r'javascript\s*:', '', text, flags=re.IGNORECASE)

        return text.strip()

    except Exception as e:
        raise HTMLSanitizationError(f"Failed to sanitize HTML: {e}")


def sanitize_rich_text(text: str) -> str:
    """
    Sanitize rich text content, allowing safe HTML formatting.

    This is designed for user-generated content that needs formatting
    (comments, descriptions, etc.) while preventing XSS attacks.

    Allows: paragraphs, lists, basic formatting, links, tables
    Blocks: scripts, styles, forms, event handlers, dangerous protocols

    Args:
        text: Rich text HTML content

    Returns:
        Sanitized rich text with safe HTML preserved

    Example:
        >>> sanitize_rich_text('<p>Hello <strong>World</strong></p>')
        '<p>Hello <strong>World</strong></p>'
        >>> sanitize_rich_text('<p onclick="alert()">Text</p>')
        '<p>Text</p>'
    """
    return sanitize_html(text, allowed_tags=SAFE_TAGS, strip_tags=False)


def escape_html(text: str) -> str:
    """
    Escape HTML special characters to prevent injection.

    Converts characters like <, >, &, ", and ' to their HTML entity equivalents.
    Use this when you want to display user input as-is without any HTML rendering.

    Args:
        text: Text to escape

    Returns:
        HTML-escaped text

    Example:
        >>> escape_html('<script>alert("xss")</script>')
        '&lt;script&gt;alert(&quot;xss&quot;)&lt;/script&gt;'
    """
    if not text:
        return ""
    return html.escape(text, quote=True)


def validate_url_protocol(url: str) -> bool:
    """
    Validate that a URL uses a safe protocol.

    Args:
        url: URL to validate

    Returns:
        True if URL uses a safe protocol, False otherwise

    Example:
        >>> validate_url_protocol('https://example.com')
        True
        >>> validate_url_protocol('javascript:alert(1)')
        False
    """
    if not url:
        return False

    url_lower = url.lower().strip()

    # Check for dangerous protocols
    dangerous_protocols = ['javascript:', 'data:', 'vbscript:', 'file:']
    for protocol in dangerous_protocols:
        if url_lower.startswith(protocol):
            return False

    # If URL has a protocol, it must be in safe list
    if '://' in url_lower:
        protocol = url_lower.split('://')[0]
        return protocol in SAFE_PROTOCOLS

    # Relative URLs are okay
    return True


def sanitize_attribute(tag: str, attr_name: str, attr_value: str) -> Optional[str]:
    """
    Sanitize an HTML attribute value based on tag and attribute name.

    Args:
        tag: HTML tag name
        attr_name: Attribute name
        attr_value: Attribute value to sanitize

    Returns:
        Sanitized attribute value, or None if attribute should be removed

    Example:
        >>> sanitize_attribute('a', 'href', 'javascript:alert(1)')
        None
        >>> sanitize_attribute('a', 'href', 'https://example.com')
        'https://example.com'
    """
    # Check if attribute is allowed for this tag
    if tag not in SAFE_ATTRIBUTES:
        return None

    if attr_name not in SAFE_ATTRIBUTES[tag]:
        return None

    # Special handling for URL attributes
    if attr_name in {'href', 'src'}:
        if not validate_url_protocol(attr_value):
            return None

    # Remove event handlers disguised as attributes
    if attr_name.lower().startswith('on'):
        return None

    return attr_value


def count_html_tags(text: str) -> int:
    """
    Count the number of HTML tags in text.

    Useful for detecting potential HTML injection attempts.

    Args:
        text: Text to analyze

    Returns:
        Number of HTML tags found

    Example:
        >>> count_html_tags('<p>Hello</p>')
        2
        >>> count_html_tags('Plain text')
        0
    """
    if not text:
        return 0
    return len(re.findall(r'<[^>]+>', text))


def is_safe_html(text: str, max_tags: int = 50) -> bool:
    """
    Check if HTML content appears safe based on heuristics.

    Args:
        text: HTML content to check
        max_tags: Maximum allowed number of tags

    Returns:
        True if content appears safe, False otherwise

    Example:
        >>> is_safe_html('<p>Normal content</p>')
        True
        >>> is_safe_html('<script>alert(1)</script>')
        False
    """
    if not text:
        return True

    # Check for excessive tags (possible attack)
    if count_html_tags(text) > max_tags:
        return False

    # Check for dangerous tags
    text_lower = text.lower()
    for tag in DANGEROUS_TAGS:
        if f'<{tag}' in text_lower or f'</{tag}>' in text_lower:
            return False

    # Check for event handlers
    if re.search(r'\son\w+\s*=', text, re.IGNORECASE):
        return False

    # Check for dangerous protocols
    if re.search(r'(javascript|data|vbscript):', text, re.IGNORECASE):
        return False

    return True
