"""String manipulation utility functions."""

import re
import unicodedata


def slugify(text: str) -> str:
    """
    Convert text to a URL-friendly slug.

    - Converts to lowercase
    - Replaces spaces with hyphens
    - Removes non-alphanumeric characters
    - Removes accents/diacritics

    Args:
        text: Text to slugify

    Returns:
        URL-friendly slug string
    """
    # Normalize unicode characters and remove accents
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii")

    # Convert to lowercase
    text = text.lower()

    # Replace spaces and underscores with hyphens
    text = re.sub(r"[\s_]+", "-", text)

    # Remove non-alphanumeric characters (except hyphens)
    text = re.sub(r"[^a-z0-9-]", "", text)

    # Remove multiple consecutive hyphens
    text = re.sub(r"-+", "-", text)

    # Strip leading/trailing hyphens
    text = text.strip("-")

    return text


def truncate(text: str, max_length: int, suffix: str = "...") -> str:
    """
    Truncate text to a maximum length, adding suffix if truncated.

    Args:
        text: Text to truncate
        max_length: Maximum length (including suffix)
        suffix: Suffix to add when truncating (default: "...")

    Returns:
        Truncated text with suffix, or original if short enough
    """
    if len(text) <= max_length:
        return text

    # Account for suffix length
    truncate_at = max_length - len(suffix)
    if truncate_at <= 0:
        return suffix[:max_length]

    return text[:truncate_at] + suffix


def remove_html_tags(text: str) -> str:
    """
    Remove HTML tags from text, leaving only the content.

    Args:
        text: Text potentially containing HTML tags

    Returns:
        Text with HTML tags removed
    """
    # Remove HTML tags
    clean_text = re.sub(r"<[^>]+>", "", text)

    # Decode common HTML entities
    clean_text = clean_text.replace("&nbsp;", " ")
    clean_text = clean_text.replace("&lt;", "<")
    clean_text = clean_text.replace("&gt;", ">")
    clean_text = clean_text.replace("&amp;", "&")
    clean_text = clean_text.replace("&quot;", '"')
    clean_text = clean_text.replace("&#39;", "'")

    return clean_text


def extract_initials(name: str, max_initials: int = 3) -> str:
    """
    Extract initials from a person's name.

    Args:
        name: Full name to extract initials from
        max_initials: Maximum number of initials to return

    Returns:
        Uppercase initials (e.g., "John Doe" -> "JD")
    """
    if not name:
        return ""

    # Split on whitespace and filter empty strings
    parts = [part for part in name.split() if part]

    # Get first letter of each part (up to max_initials)
    initials = "".join(part[0].upper() for part in parts[:max_initials])

    return initials


def normalize_whitespace(text: str) -> str:
    """
    Normalize whitespace in text.

    - Replaces multiple spaces with single space
    - Replaces tabs and newlines with spaces
    - Strips leading/trailing whitespace

    Args:
        text: Text to normalize

    Returns:
        Text with normalized whitespace
    """
    # Replace all whitespace characters with single space
    normalized = re.sub(r"\s+", " ", text)

    # Strip leading/trailing whitespace
    normalized = normalized.strip()

    return normalized
