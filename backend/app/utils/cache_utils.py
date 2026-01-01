"""Cache utility functions for key generation and serialization."""

import hashlib
import json
from typing import Any


def generate_cache_key(*args: Any) -> str:
    """
    Generate a cache key from arbitrary arguments.

    Args:
        *args: Arguments to generate cache key from

    Returns:
        SHA256 hash string suitable as cache key
    """
    # Convert args to string representation
    key_parts = [str(arg) for arg in args]
    key_string = ":".join(key_parts)

    # Hash the key string
    return hashlib.sha256(key_string.encode()).hexdigest()


def hash_dict(d: dict[str, Any]) -> str:
    """
    Generate a consistent hash for a dictionary.

    Args:
        d: Dictionary to hash

    Returns:
        SHA256 hash of the dictionary (sorted keys for consistency)
    """
    # Sort keys to ensure consistent ordering
    sorted_items = sorted(d.items())

    # Convert to JSON string
    json_str = json.dumps(sorted_items, sort_keys=True)

    # Hash the JSON string
    return hashlib.sha256(json_str.encode()).hexdigest()


def serialize_for_cache(obj: Any) -> str:
    """
    Serialize an object to a string for caching.

    Handles common types: dict, list, str, int, float, bool, None

    Args:
        obj: Object to serialize

    Returns:
        JSON string representation

    Raises:
        TypeError: If object is not JSON serializable
    """
    try:
        return json.dumps(obj, sort_keys=True, default=str)
    except TypeError as e:
        raise TypeError(f"Object not serializable for cache: {type(obj)}") from e


def deserialize_from_cache(s: str) -> Any:
    """
    Deserialize a cached string back to an object.

    Args:
        s: JSON string from cache

    Returns:
        Deserialized object

    Raises:
        ValueError: If string is not valid JSON
    """
    try:
        return json.loads(s)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in cache: {s}") from e
