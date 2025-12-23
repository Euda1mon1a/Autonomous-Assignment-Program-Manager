"""
ETag generation utilities for HTTP caching.

Implements RFC 7232 entity tags for cache validation:
- Strong ETags: Exact byte-for-byte equality
- Weak ETags: Semantic equivalence
- ETag comparison and validation
- If-None-Match header handling

ETags are used for:
- Conditional GET requests (304 Not Modified)
- Optimistic concurrency control
- Cache validation without full content transfer
"""

import hashlib
import json
from datetime import datetime
from typing import Any


class ETagGenerator:
    """
    Generate ETags for HTTP responses.

    Supports both strong and weak ETags based on content hashing.
    Strong ETags indicate exact byte-for-byte equality.
    Weak ETags (prefixed with W/) indicate semantic equivalence.

    Example:
        generator = ETagGenerator()

        # Strong ETag from content
        etag = generator.generate(response_body)
        # Returns: "abc123def456"

        # Weak ETag from data
        etag = generator.generate_weak({"data": "value"})
        # Returns: W/"abc123def456"
    """

    def __init__(self, algorithm: str = "sha256"):
        """
        Initialize ETag generator.

        Args:
            algorithm: Hash algorithm (sha256, sha1, md5)
        """
        self.algorithm = algorithm

    def generate(self, content: bytes | str, weak: bool = False) -> str:
        """
        Generate ETag from content.

        Args:
            content: Response content (bytes or string)
            weak: Generate weak ETag (W/ prefix)

        Returns:
            ETag string (with quotes)

        Example:
            etag = generator.generate(b"Hello World")
            # Returns: "a591a6d40bf420404a011733cfb7b190d62c65bf0bcda32b57b277d9ad9f146e"
        """
        if isinstance(content, str):
            content = content.encode("utf-8")

        # Generate hash
        hasher = hashlib.new(self.algorithm)
        hasher.update(content)
        hash_value = hasher.hexdigest()

        # Format as ETag
        if weak:
            return f'W/"{hash_value}"'
        return f'"{hash_value}"'

    def generate_weak(self, data: Any) -> str:
        """
        Generate weak ETag from structured data.

        Useful for JSON responses where minor formatting changes
        shouldn't invalidate the cache.

        Args:
            data: Data to hash (will be JSON serialized)

        Returns:
            Weak ETag string

        Example:
            etag = generator.generate_weak({"user": "john", "id": 123})
            # Returns: W/"hash_of_json"
        """
        # Serialize to JSON (sorted keys for consistency)
        json_str = json.dumps(data, sort_keys=True, separators=(",", ":"))
        return self.generate(json_str, weak=True)

    def generate_from_metadata(
        self,
        last_modified: datetime | None = None,
        content_length: int | None = None,
        version: str | None = None,
    ) -> str:
        """
        Generate ETag from metadata instead of content.

        Faster than hashing full content, but less reliable.
        Useful for large files or database records.

        Args:
            last_modified: Last modification timestamp
            content_length: Content size in bytes
            version: Version string or ID

        Returns:
            ETag string

        Example:
            etag = generator.generate_from_metadata(
                last_modified=datetime(2024, 1, 1),
                content_length=1024,
                version="v1.2.3"
            )
        """
        # Build metadata string
        parts = []

        if last_modified:
            parts.append(str(int(last_modified.timestamp())))

        if content_length is not None:
            parts.append(str(content_length))

        if version:
            parts.append(version)

        metadata_str = "-".join(parts) if parts else "default"
        return self.generate(metadata_str.encode("utf-8"))

    @staticmethod
    def is_weak(etag: str) -> bool:
        """
        Check if ETag is weak.

        Args:
            etag: ETag string

        Returns:
            True if weak ETag (has W/ prefix)

        Example:
            ETagGenerator.is_weak('W/"abc123"')  # True
            ETagGenerator.is_weak('"abc123"')    # False
        """
        return etag.startswith("W/")

    @staticmethod
    def strip_weak_prefix(etag: str) -> str:
        """
        Remove W/ prefix from weak ETag.

        Args:
            etag: ETag string

        Returns:
            ETag without weak prefix

        Example:
            ETagGenerator.strip_weak_prefix('W/"abc123"')  # "abc123"
        """
        if etag.startswith("W/"):
            return etag[2:]
        return etag

    @staticmethod
    def matches(etag1: str, etag2: str, strong_comparison: bool = False) -> bool:
        """
        Compare two ETags for equality.

        Args:
            etag1: First ETag
            etag2: Second ETag
            strong_comparison: Require strong comparison (reject weak ETags)

        Returns:
            True if ETags match

        Example:
            # Weak comparison (default)
            ETagGenerator.matches('W/"abc"', '"abc"')  # True

            # Strong comparison
            ETagGenerator.matches('W/"abc"', '"abc"', strong_comparison=True)  # False
        """
        # Strong comparison requires both to be strong
        if strong_comparison:
            if ETagGenerator.is_weak(etag1) or ETagGenerator.is_weak(etag2):
                return False

        # Strip weak prefixes for comparison
        etag1_stripped = ETagGenerator.strip_weak_prefix(etag1)
        etag2_stripped = ETagGenerator.strip_weak_prefix(etag2)

        return etag1_stripped == etag2_stripped

    @staticmethod
    def parse_if_none_match(header_value: str) -> list[str]:
        """
        Parse If-None-Match header value.

        Args:
            header_value: If-None-Match header value

        Returns:
            List of ETags

        Example:
            etags = ETagGenerator.parse_if_none_match('"abc", W/"def", "ghi"')
            # Returns: ['"abc"', 'W/"def"', '"ghi"']
        """
        # Handle wildcard
        if header_value.strip() == "*":
            return ["*"]

        # Split by comma and strip whitespace
        etags = [etag.strip() for etag in header_value.split(",")]
        return [etag for etag in etags if etag]

    @staticmethod
    def matches_any(etag: str, etag_list: list[str]) -> bool:
        """
        Check if ETag matches any in a list.

        Args:
            etag: ETag to check
            etag_list: List of ETags (from If-None-Match)

        Returns:
            True if etag matches any in the list

        Example:
            matches = ETagGenerator.matches_any(
                '"abc123"',
                ['"abc123"', '"def456"']
            )  # True
        """
        # Wildcard matches everything
        if "*" in etag_list:
            return True

        # Check each ETag
        for candidate in etag_list:
            if ETagGenerator.matches(etag, candidate):
                return True

        return False


def generate_etag(
    content: bytes | str | Any,
    weak: bool = False,
    algorithm: str = "sha256",
) -> str:
    """
    Generate ETag from content (convenience function).

    Args:
        content: Content to hash (bytes, string, or JSON-serializable data)
        weak: Generate weak ETag
        algorithm: Hash algorithm

    Returns:
        ETag string

    Example:
        # Strong ETag from bytes
        etag = generate_etag(b"Hello World")

        # Weak ETag from data
        etag = generate_etag({"user": "john"}, weak=True)
    """
    generator = ETagGenerator(algorithm=algorithm)

    # Handle different content types
    if isinstance(content, (bytes, str)):
        return generator.generate(content, weak=weak)
    else:
        # Assume JSON-serializable
        return generator.generate_weak(content)


def weak_etag(content: bytes | str | Any, algorithm: str = "sha256") -> str:
    """
    Generate weak ETag (convenience function).

    Args:
        content: Content to hash
        algorithm: Hash algorithm

    Returns:
        Weak ETag string

    Example:
        etag = weak_etag({"user": "john"})
        # Returns: W/"hash_value"
    """
    return generate_etag(content, weak=True, algorithm=algorithm)
