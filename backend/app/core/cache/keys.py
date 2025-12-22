"""
Cache key generation utilities.

Provides consistent key generation for cache operations with support for
namespacing, versioning, and parameterized keys.

This module provides:
- CacheKeyGenerator: Base class for key generation
- generate_cache_key(): Helper function for quick key generation
- Key versioning for cache busting
- Automatic serialization of complex parameters
"""
import hashlib
import json
from typing import Any


class CacheKeyGenerator:
    """
    Cache key generator with namespace and version support.

    Generates consistent cache keys from function names, parameters,
    and namespaces. Supports automatic serialization and hashing of
    complex parameters.

    Example:
        generator = CacheKeyGenerator(namespace="schedule", version="v1")
        key = generator.generate("get_assignments", user_id=123, date="2024-01-01")
        # Returns: "cache:schedule:v1:get_assignments:hash"
    """

    def __init__(
        self,
        namespace: str = "cache",
        version: str = "v1",
        prefix: str = "cache",
        separator: str = ":"
    ):
        """
        Initialize cache key generator.

        Args:
            namespace: Namespace for grouping related cache keys
            version: Version identifier for cache invalidation
            prefix: Global prefix for all cache keys
            separator: Character used to separate key components
        """
        self.namespace = namespace
        self.version = version
        self.prefix = prefix
        self.separator = separator

    def generate(
        self,
        function_name: str,
        include_namespace: bool = True,
        include_version: bool = True,
        **kwargs
    ) -> str:
        """
        Generate a cache key from function name and parameters.

        Args:
            function_name: Name of the function being cached
            include_namespace: Include namespace in key
            include_version: Include version in key
            **kwargs: Parameters to include in key generation

        Returns:
            Generated cache key string

        Example:
            key = generator.generate("get_user", user_id=123)
            # Returns: "cache:schedule:v1:get_user:f7c3bc1d45e2"
        """
        components = [self.prefix]

        if include_namespace:
            components.append(self.namespace)

        if include_version:
            components.append(self.version)

        components.append(function_name)

        # Add parameter hash if parameters provided
        if kwargs:
            param_hash = self._hash_params(kwargs)
            components.append(param_hash)

        return self.separator.join(components)

    def generate_tagged(
        self,
        function_name: str,
        tags: list[str],
        **kwargs
    ) -> tuple[str, list[str]]:
        """
        Generate a cache key with associated tags for tag-based invalidation.

        Args:
            function_name: Name of the function being cached
            tags: List of tags for invalidation grouping
            **kwargs: Parameters to include in key generation

        Returns:
            Tuple of (cache_key, tag_keys) for storing in cache

        Example:
            key, tag_keys = generator.generate_tagged(
                "get_schedule",
                tags=["schedule", "user:123"],
                date="2024-01-01"
            )
        """
        cache_key = self.generate(function_name, **kwargs)

        # Generate tag keys
        tag_keys = [
            f"{self.prefix}:tag:{self.namespace}:{tag}"
            for tag in tags
        ]

        return cache_key, tag_keys

    def generate_pattern(
        self,
        function_name: str | None = None,
        include_namespace: bool = True,
        include_version: bool = True
    ) -> str:
        """
        Generate a Redis SCAN pattern for matching multiple keys.

        Args:
            function_name: Optional function name to match
            include_namespace: Include namespace in pattern
            include_version: Include version in pattern

        Returns:
            Redis pattern string with wildcards

        Example:
            pattern = generator.generate_pattern("get_user")
            # Returns: "cache:schedule:v1:get_user:*"
        """
        components = [self.prefix]

        if include_namespace:
            components.append(self.namespace)

        if include_version:
            components.append(self.version)

        if function_name:
            components.append(function_name)

        components.append("*")

        return self.separator.join(components)

    def _hash_params(self, params: dict[str, Any]) -> str:
        """
        Generate a consistent hash from parameters.

        Args:
            params: Dictionary of parameters to hash

        Returns:
            Short hash string (12 characters)

        Note:
            Uses MD5 for speed (not for security). Parameters are
            sorted and JSON-serialized for consistency.
        """
        # Sort parameters for consistency
        sorted_params = dict(sorted(params.items()))

        # Serialize to JSON (handles basic types)
        try:
            param_str = json.dumps(sorted_params, sort_keys=True, default=str)
        except (TypeError, ValueError):
            # Fallback for non-serializable types
            param_str = str(sorted_params)

        # Generate hash (MD5 is fast and sufficient for cache keys)
        hash_obj = hashlib.md5(param_str.encode())
        return hash_obj.hexdigest()[:12]


def generate_cache_key(
    namespace: str,
    function_name: str,
    version: str = "v1",
    **kwargs
) -> str:
    """
    Quick helper function to generate a cache key.

    Args:
        namespace: Cache namespace
        function_name: Function name
        version: Cache version
        **kwargs: Parameters to include in key

    Returns:
        Generated cache key

    Example:
        key = generate_cache_key(
            "schedule",
            "get_assignments",
            user_id=123,
            date="2024-01-01"
        )
    """
    generator = CacheKeyGenerator(namespace=namespace, version=version)
    return generator.generate(function_name, **kwargs)


def generate_tag_key(namespace: str, tag: str, prefix: str = "cache") -> str:
    """
    Generate a key for tag-based invalidation tracking.

    Args:
        namespace: Cache namespace
        tag: Tag name
        prefix: Cache key prefix

    Returns:
        Tag key for storing in Redis set

    Example:
        tag_key = generate_tag_key("schedule", "user:123")
        # Returns: "cache:tag:schedule:user:123"
    """
    return f"{prefix}:tag:{namespace}:{tag}"


def generate_stats_key(namespace: str, prefix: str = "cache") -> str:
    """
    Generate a key for cache statistics.

    Args:
        namespace: Cache namespace
        prefix: Cache key prefix

    Returns:
        Statistics key for storing metrics

    Example:
        stats_key = generate_stats_key("schedule")
        # Returns: "cache:stats:schedule"
    """
    return f"{prefix}:stats:{namespace}"
