"""Collection utility functions for list and dict operations."""

from typing import Any, Callable, TypeVar

T = TypeVar("T")
K = TypeVar("K")


def chunk_list(lst: list[T], size: int) -> list[list[T]]:
    """
    Split a list into chunks of specified size.

    Args:
        lst: List to chunk
        size: Size of each chunk

    Returns:
        List of chunks, each of max size 'size'
    """
    if size <= 0:
        raise ValueError("Chunk size must be positive")

    chunks = []
    for i in range(0, len(lst), size):
        chunks.append(lst[i : i + size])
    return chunks


def flatten(nested: list[list[T]]) -> list[T]:
    """
    Flatten a nested list one level deep.

    Args:
        nested: List of lists to flatten

    Returns:
        Flattened list
    """
    result = []
    for sublist in nested:
        if isinstance(sublist, list):
            result.extend(sublist)
        else:
            result.append(sublist)
    return result


def group_by(items: list[T], key_func: Callable[[T], K]) -> dict[K, list[T]]:
    """
    Group items by a key function.

    Args:
        items: List of items to group
        key_func: Function that extracts the grouping key from an item

    Returns:
        Dictionary mapping keys to lists of items
    """
    groups: dict[K, list[T]] = {}
    for item in items:
        key = key_func(item)
        if key not in groups:
            groups[key] = []
        groups[key].append(item)
    return groups


def unique_by(items: list[T], key_func: Callable[[T], Any]) -> list[T]:
    """
    Get unique items based on a key function, preserving order.

    Args:
        items: List of items
        key_func: Function that extracts the uniqueness key from an item

    Returns:
        List of unique items (first occurrence kept)
    """
    seen = set()
    result = []
    for item in items:
        key = key_func(item)
        if key not in seen:
            seen.add(key)
            result.append(item)
    return result


def safe_get(d: dict[str, Any], *keys: str, default: Any = None) -> Any:
    """
    Safely get a nested value from a dictionary.

    Args:
        d: Dictionary to get value from
        *keys: Path of keys to traverse
        default: Default value if key path not found

    Returns:
        Value at the key path, or default if not found

    Examples:
        >>> data = {"user": {"profile": {"name": "Alice"}}}
        >>> safe_get(data, "user", "profile", "name")
        'Alice'
        >>> safe_get(data, "user", "settings", "theme", default="dark")
        'dark'
    """
    current = d
    for key in keys:
        if not isinstance(current, dict) or key not in current:
            return default
        current = current[key]
    return current
