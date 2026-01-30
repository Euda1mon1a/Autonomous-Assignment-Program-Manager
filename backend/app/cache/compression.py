"""Cache value compression for large objects.

Reduces cache memory usage by compressing large values.
"""

import gzip
import json
import logging
import zlib
from enum import Enum
from typing import Any, Optional

logger = logging.getLogger(__name__)


class CompressionAlgorithm(str, Enum):
    """Compression algorithm options."""

    GZIP = "gzip"
    ZLIB = "zlib"
    NONE = "none"


class CacheCompression:
    """Handles compression/decompression for cache values."""

    def __init__(
        self,
        algorithm: CompressionAlgorithm = CompressionAlgorithm.GZIP,
        compression_level: int = 6,
        min_size_bytes: int = 1024,  # Only compress if > 1KB
    ) -> None:
        """Initialize cache compression.

        Args:
            algorithm: Compression algorithm to use
            compression_level: Compression level (1-9, higher = better compression)
            min_size_bytes: Minimum size to compress
        """
        self.algorithm = algorithm
        self.compression_level = compression_level
        self.min_size_bytes = min_size_bytes

    def compress(self, data: Any) -> tuple[bytes, bool]:
        """Compress data for caching.

        Args:
            data: Data to compress (will be JSON serialized first)

        Returns:
            Tuple of (compressed_data, was_compressed)
        """
        # Serialize to JSON
        if isinstance(data, (str, bytes)):
            json_data = data.encode() if isinstance(data, str) else data
        else:
            json_data = json.dumps(data).encode()

            # Check if compression is worthwhile
        if (
            len(json_data) < self.min_size_bytes
            or self.algorithm == CompressionAlgorithm.NONE
        ):
            return json_data, False

            # Compress based on algorithm
        try:
            if self.algorithm == CompressionAlgorithm.GZIP:
                compressed = gzip.compress(
                    json_data, compresslevel=self.compression_level
                )
            elif self.algorithm == CompressionAlgorithm.ZLIB:
                compressed = zlib.compress(json_data, level=self.compression_level)
            else:
                compressed = json_data

                # Only use compression if it actually reduces size
            if len(compressed) < len(json_data):
                logger.debug(
                    f"Compressed {len(json_data)} -> {len(compressed)} bytes "
                    f"({len(compressed) / len(json_data) * 100:.1f}%)"
                )
                return compressed, True
            else:
                return json_data, False

        except Exception as e:
            logger.error(f"Compression error: {e}")
            return json_data, False

    def decompress(self, data: bytes, was_compressed: bool) -> Any:
        """Decompress cached data.

        Args:
            data: Compressed data
            was_compressed: Whether data was compressed

        Returns:
            Decompressed data
        """
        if not was_compressed:
            # Try to parse as JSON
            try:
                return json.loads(data)
            except (json.JSONDecodeError, TypeError):
                return data.decode() if isinstance(data, bytes) else data

                # Decompress based on algorithm
        try:
            if self.algorithm == CompressionAlgorithm.GZIP:
                decompressed = gzip.decompress(data)
            elif self.algorithm == CompressionAlgorithm.ZLIB:
                decompressed = zlib.decompress(data)
            else:
                decompressed = data

                # Try to parse as JSON
            try:
                return json.loads(decompressed)
            except json.JSONDecodeError:
                return decompressed.decode()

        except Exception as e:
            logger.error(f"Decompression error: {e}")
            return None

    def get_compression_stats(
        self,
        original_size: int,
        compressed_size: int,
    ) -> dict:
        """Calculate compression statistics.

        Args:
            original_size: Original data size in bytes
            compressed_size: Compressed data size in bytes

        Returns:
            Compression statistics
        """
        ratio = compressed_size / original_size if original_size > 0 else 1.0
        saved = original_size - compressed_size
        saved_pct = (saved / original_size * 100) if original_size > 0 else 0.0

        return {
            "original_size": original_size,
            "compressed_size": compressed_size,
            "compression_ratio": round(ratio, 3),
            "space_saved": saved,
            "space_saved_pct": round(saved_pct, 2),
        }


class CompressedCacheWrapper:
    """Wrapper that adds automatic compression to cache operations."""

    def __init__(
        self,
        cache,
        compressor: CacheCompression | None = None,
    ) -> None:
        """Initialize compressed cache wrapper.

        Args:
            cache: Base cache instance (e.g., CacheManager)
            compressor: CacheCompression instance
        """
        self.cache = cache
        self.compressor = compressor or CacheCompression()
        self.stats = {
            "total_original_bytes": 0,
            "total_compressed_bytes": 0,
            "compression_count": 0,
        }

    async def set(
        self,
        key: str,
        value: Any,
        ttl: int | None = None,
    ) -> bool:
        """Set value with automatic compression.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds

        Returns:
            True if successful
        """
        # Get original size
        if isinstance(value, str):
            original_size = len(value.encode())
        elif isinstance(value, bytes):
            original_size = len(value)
        else:
            original_size = len(json.dumps(value).encode())

            # Compress
        compressed_data, was_compressed = self.compressor.compress(value)
        compressed_size = len(compressed_data)

        # Store with compression flag
        cache_value = {
            "data": compressed_data.hex(),  # Store as hex string
            "compressed": was_compressed,
            "algorithm": self.compressor.algorithm.value,
        }

        # Update stats
        self.stats["total_original_bytes"] += original_size
        self.stats["total_compressed_bytes"] += compressed_size
        if was_compressed:
            self.stats["compression_count"] += 1

        return await self.cache.set(key, json.dumps(cache_value), ttl)

    async def get(self, key: str) -> Any | None:
        """Get value with automatic decompression.

        Args:
            key: Cache key

        Returns:
            Decompressed value or None
        """
        cached = await self.cache.get(key)
        if cached is None:
            return None

        try:
            cache_value = json.loads(cached)
            data_bytes = bytes.fromhex(cache_value["data"])
            was_compressed = cache_value.get("compressed", False)

            return self.compressor.decompress(data_bytes, was_compressed)

        except Exception as e:
            logger.error(f"Decompression error for key {key}: {e}")
            return None

    async def get_compression_stats(self) -> dict:
        """Get compression statistics.

        Returns:
            Compression statistics
        """
        total_original = self.stats["total_original_bytes"]
        total_compressed = self.stats["total_compressed_bytes"]

        overall_ratio = total_compressed / total_original if total_original > 0 else 1.0
        space_saved = total_original - total_compressed
        space_saved_pct = (
            space_saved / total_original * 100 if total_original > 0 else 0.0
        )

        return {
            "total_original_bytes": total_original,
            "total_compressed_bytes": total_compressed,
            "overall_compression_ratio": round(overall_ratio, 3),
            "total_space_saved": space_saved,
            "space_saved_pct": round(space_saved_pct, 2),
            "compression_count": self.stats["compression_count"],
        }

        # Global compressed cache


_compressed_cache: CompressedCacheWrapper | None = None


def get_compressed_cache() -> CompressedCacheWrapper:
    """Get global compressed cache instance.

    Returns:
        CompressedCacheWrapper singleton
    """
    global _compressed_cache
    if _compressed_cache is None:
        from app.cache.cache_manager import get_cache_manager

        _compressed_cache = CompressedCacheWrapper(get_cache_manager())
    return _compressed_cache
