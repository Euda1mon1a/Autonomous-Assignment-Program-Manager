"""
XSS (Cross-Site Scripting) prevention and detection module.

This module provides comprehensive XSS protection through:
- Pattern-based XSS detection
- Unicode normalization
- URL sanitization
- Input sanitization with configurable strictness
- Path traversal prevention
"""
import re
import unicodedata
from typing import Optional
from urllib.parse import urlparse, quote, unquote


class XSSDetectionError(Exception):
    """Exception raised when XSS patterns are detected."""
    pass


# XSS attack patterns to detect
XSS_PATTERNS = [
    # Script tags
    r'<\s*script[^>]*>',
    r'<\s*/\s*script\s*>',
    # Event handlers
    r'\bon\w+\s*=',
    r'on(load|error|click|mouse\w+|key\w+|focus|blur|change|submit)\s*=',
    # JavaScript protocol
    r'javascript\s*:',
    r'vbscript\s*:',
    # Data URIs (can contain JavaScript)
    r'data\s*:.*base64',
    r'data\s*:.*text/html',
    # Common XSS payloads
    r'alert\s*\(',
    r'prompt\s*\(',
    r'confirm\s*\(',
    r'eval\s*\(',
    r'expression\s*\(',
    # Document/window manipulation
    r'document\s*\.\s*(write|cookie|location)',
    r'window\s*\.\s*(location|open)',
    # Style-based XSS
    r'<\s*style[^>]*>',
    r'@import',
    r'behavior\s*:',
    # Meta refresh
    r'<\s*meta[^>]*http-equiv[^>]*refresh',
    # Object/embed tags
    r'<\s*(object|embed|applet|iframe)[^>]*>',
    # Form manipulation
    r'<\s*form[^>]*action',
    # Encoded variations
    r'&#x?[0-9a-f]+;',  # HTML entities (can encode scripts)
]

# Dangerous Unicode characters that might be used for obfuscation
DANGEROUS_UNICODE_RANGES = [
    (0x0000, 0x001F),  # Control characters
    (0x007F, 0x009F),  # More control characters
    (0x200B, 0x200F),  # Zero-width characters
    (0x2028, 0x2029),  # Line/paragraph separators
    (0xFFF9, 0xFFFB),  # Interlinear annotation characters
]

# Path traversal patterns
PATH_TRAVERSAL_PATTERNS = [
    r'\.\.',
    r'\.\./',
    r'\.\.',
    r'%2e%2e',
    r'%252e%252e',
    r'\.\.\\',
]


def detect_xss(input_string: str, strict: bool = True) -> bool:
    """
    Detect potential XSS attack patterns in input string.

    Uses pattern matching to identify common XSS techniques including
    script injection, event handlers, and encoded payloads.

    Args:
        input_string: String to check for XSS patterns
        strict: If True, use stricter detection (more false positives)

    Returns:
        True if XSS patterns detected, False otherwise

    Example:
        >>> detect_xss('<script>alert("xss")</script>')
        True
        >>> detect_xss('normal text')
        False
        >>> detect_xss('<img src=x onerror=alert(1)>')
        True
    """
    if not input_string:
        return False

    input_lower = input_string.lower()

    # Check for XSS patterns
    for pattern in XSS_PATTERNS:
        if re.search(pattern, input_lower, re.IGNORECASE):
            return True

    # In strict mode, check for suspicious character combinations
    if strict:
        # Check for HTML-like structures
        if '<' in input_string and '>' in input_string:
            # Count tags
            tag_count = len(re.findall(r'<[^>]+>', input_string))
            if tag_count > 0:
                # Has HTML-like content, check if it looks malicious
                if re.search(r'<\w+[^>]*\w+\s*=', input_string):
                    return True

        # Check for encoded scripts
        if '%3C' in input_string or '%3E' in input_string:
            # URL-encoded < and >
            decoded = unquote(input_string)
            if detect_xss(decoded, strict=False):
                return True

    return False


def sanitize_input(
    input_string: str,
    max_length: Optional[int] = None,
    allow_html: bool = False,
    normalize: bool = True
) -> str:
    """
    Sanitize general user input to prevent XSS attacks.

    This is the primary function for sanitizing user input across the application.

    Args:
        input_string: String to sanitize
        max_length: Maximum allowed length (truncate if exceeded)
        allow_html: If True, allow safe HTML (uses html.sanitize_html)
        normalize: If True, normalize Unicode characters

    Returns:
        Sanitized string

    Raises:
        XSSDetectionError: If dangerous XSS patterns are detected

    Example:
        >>> sanitize_input('<script>alert("xss")</script>')
        Raises XSSDetectionError
        >>> sanitize_input('normal input')
        'normal input'
        >>> sanitize_input('  spaces  ')
        'spaces'
    """
    if not input_string:
        return ""

    # Check for XSS patterns first
    if detect_xss(input_string, strict=True):
        raise XSSDetectionError(
            "Input contains patterns that may indicate XSS attempt"
        )

    # Normalize Unicode if requested
    if normalize:
        input_string = normalize_unicode(input_string)

    # Truncate if max_length specified
    if max_length and len(input_string) > max_length:
        input_string = input_string[:max_length]

    # Remove null bytes
    input_string = input_string.replace('\x00', '')

    # Handle HTML
    if not allow_html:
        # Import here to avoid circular dependency
        from app.sanitization.html import strip_all_tags
        input_string = strip_all_tags(input_string)
    else:
        # Import here to avoid circular dependency
        from app.sanitization.html import sanitize_html
        input_string = sanitize_html(input_string)

    # Remove control characters except newlines and tabs
    input_string = ''.join(
        char for char in input_string
        if char in '\n\r\t' or not unicodedata.category(char).startswith('C')
    )

    return input_string.strip()


def normalize_unicode(text: str, form: str = 'NFKC') -> str:
    """
    Normalize Unicode text to prevent Unicode-based attacks.

    Unicode normalization prevents attacks that use visually similar
    characters or combining characters to bypass filters.

    Args:
        text: Text to normalize
        form: Normalization form (NFC, NFD, NFKC, NFKD). Default: NFKC

    Returns:
        Normalized Unicode string

    Example:
        >>> normalize_unicode('café')  # é as single char
        'café'  # é as e + combining accent
        >>> normalize_unicode('\\u0041\\u0301')  # A + combining acute
        'Á'  # Single character
    """
    if not text:
        return ""

    # Normalize to specified form
    # NFKC is most aggressive - canonical + compatibility decomposition + composition
    normalized = unicodedata.normalize(form, text)

    # Remove dangerous Unicode characters
    cleaned = ''
    for char in normalized:
        code_point = ord(char)
        is_dangerous = any(
            start <= code_point <= end
            for start, end in DANGEROUS_UNICODE_RANGES
        )
        if not is_dangerous:
            cleaned += char

    return cleaned


def sanitize_url(url: str, allowed_schemes: Optional[set[str]] = None) -> str:
    """
    Sanitize URL to prevent XSS through malicious URLs.

    Validates URL scheme, removes dangerous protocols, and normalizes the URL.

    Args:
        url: URL to sanitize
        allowed_schemes: Set of allowed URL schemes. Default: {'http', 'https'}

    Returns:
        Sanitized URL

    Raises:
        XSSDetectionError: If URL contains dangerous patterns

    Example:
        >>> sanitize_url('https://example.com')
        'https://example.com'
        >>> sanitize_url('javascript:alert(1)')
        Raises XSSDetectionError
    """
    if not url:
        return ""

    # Default allowed schemes
    if allowed_schemes is None:
        allowed_schemes = {'http', 'https', 'mailto', 'ftp'}

    url = url.strip()

    # Check for XSS patterns in URL
    if detect_xss(url, strict=True):
        raise XSSDetectionError("URL contains XSS patterns")

    # Parse URL
    try:
        parsed = urlparse(url)
    except Exception:
        raise XSSDetectionError("Invalid URL format")

    # Check scheme
    if parsed.scheme:
        if parsed.scheme.lower() not in allowed_schemes:
            raise XSSDetectionError(
                f"URL scheme '{parsed.scheme}' not allowed. "
                f"Allowed: {', '.join(allowed_schemes)}"
            )

    # Check for dangerous patterns in URL components
    dangerous_patterns = ['javascript:', 'data:', 'vbscript:', 'file:']
    url_lower = url.lower()
    for pattern in dangerous_patterns:
        if pattern in url_lower:
            raise XSSDetectionError(f"Dangerous pattern '{pattern}' in URL")

    return url


def prevent_path_traversal(path: str) -> str:
    """
    Prevent path traversal attacks in file paths.

    Removes ../, ..\, and other path traversal patterns.

    Args:
        path: File path to sanitize

    Returns:
        Sanitized path

    Raises:
        XSSDetectionError: If path contains traversal patterns

    Example:
        >>> prevent_path_traversal('safe/path/file.txt')
        'safe/path/file.txt'
        >>> prevent_path_traversal('../../../etc/passwd')
        Raises XSSDetectionError
    """
    if not path:
        return ""

    path_lower = path.lower()

    # Check for path traversal patterns
    for pattern in PATH_TRAVERSAL_PATTERNS:
        if re.search(pattern, path_lower, re.IGNORECASE):
            raise XSSDetectionError(
                "Path contains traversal patterns"
            )

    # Remove leading slashes (absolute paths)
    while path.startswith(('/', '\\')):
        path = path[1:]

    # Normalize path separators to forward slashes
    path = path.replace('\\', '/')

    # Split path and remove any '..' components
    parts = path.split('/')
    safe_parts = []
    for part in parts:
        if part and part != '..' and part != '.':
            # Remove dangerous characters from filename
            part = re.sub(r'[^\w\-_.]', '_', part)
            safe_parts.append(part)

    return '/'.join(safe_parts)


def sanitize_email(email: str) -> str:
    """
    Sanitize email address input.

    Basic validation and sanitization for email addresses.

    Args:
        email: Email address to sanitize

    Returns:
        Sanitized email address

    Raises:
        XSSDetectionError: If email contains dangerous patterns

    Example:
        >>> sanitize_email('user@example.com')
        'user@example.com'
        >>> sanitize_email('"><script>alert(1)</script>')
        Raises XSSDetectionError
    """
    if not email:
        return ""

    email = email.strip().lower()

    # Check for XSS patterns
    if detect_xss(email, strict=True):
        raise XSSDetectionError("Email contains XSS patterns")

    # Basic email pattern validation
    email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    if not email_pattern.match(email):
        raise XSSDetectionError("Invalid email format")

    # Additional safety checks
    dangerous_chars = ['<', '>', '"', "'", '\\', '/', '(', ')', ';']
    for char in dangerous_chars:
        if char in email:
            raise XSSDetectionError(f"Email contains dangerous character: {char}")

    return email


def sanitize_json_string(json_str: str) -> str:
    """
    Sanitize JSON string to prevent injection through JSON fields.

    Args:
        json_str: JSON string to sanitize

    Returns:
        Sanitized JSON string

    Example:
        >>> sanitize_json_string('{"name": "value"}')
        '{"name": "value"}'
    """
    if not json_str:
        return ""

    # Check for XSS in JSON
    if detect_xss(json_str, strict=True):
        raise XSSDetectionError("JSON contains XSS patterns")

    # Escape special characters
    json_str = json_str.replace('\\', '\\\\')
    json_str = json_str.replace('"', '\\"')

    return json_str


def is_safe_filename(filename: str) -> bool:
    """
    Check if filename is safe (no path traversal, no special characters).

    Args:
        filename: Filename to check

    Returns:
        True if safe, False otherwise

    Example:
        >>> is_safe_filename('document.pdf')
        True
        >>> is_safe_filename('../../../etc/passwd')
        False
        >>> is_safe_filename('file<script>.txt')
        False
    """
    if not filename:
        return False

    # Check for path traversal
    if '..' in filename or '/' in filename or '\\' in filename:
        return False

    # Check for dangerous characters
    dangerous_chars = ['<', '>', '"', "'", '|', '\x00', '\n', '\r']
    for char in dangerous_chars:
        if char in filename:
            return False

    # Check for hidden files
    if filename.startswith('.'):
        return False

    # Check length
    if len(filename) > 255:
        return False

    return True


def encode_for_html_attribute(value: str) -> str:
    """
    Encode value for safe use in HTML attributes.

    Args:
        value: Value to encode

    Returns:
        HTML-attribute-safe encoded value

    Example:
        >>> encode_for_html_attribute('value with "quotes"')
        'value with &quot;quotes&quot;'
    """
    if not value:
        return ""

    # Encode special HTML characters
    value = value.replace('&', '&amp;')
    value = value.replace('<', '&lt;')
    value = value.replace('>', '&gt;')
    value = value.replace('"', '&quot;')
    value = value.replace("'", '&#x27;')
    value = value.replace('/', '&#x2F;')

    return value


def strip_javascript(text: str) -> str:
    """
    Remove JavaScript code from text.

    Args:
        text: Text potentially containing JavaScript

    Returns:
        Text with JavaScript removed

    Example:
        >>> strip_javascript('Hello <script>alert(1)</script> World')
        'Hello  World'
    """
    if not text:
        return ""

    # Remove script tags and content
    text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.IGNORECASE | re.DOTALL)

    # Remove event handlers
    text = re.sub(r'\son\w+\s*=\s*["\'][^"\']*["\']', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\son\w+\s*=\s*\S+', '', text, flags=re.IGNORECASE)

    # Remove javascript: protocol
    text = re.sub(r'javascript\s*:', '', text, flags=re.IGNORECASE)

    return text.strip()
