"""
Compression encoders for API response compression.

Implements various compression algorithms:
- Gzip compression (standard library)
- Brotli compression (if available)
- Streaming compression support
- Fallback handling
"""
import gzip
import io
import logging
from abc import ABC, abstractmethod
from typing import Optional

logger = logging.getLogger(__name__)


class CompressionEncoder(ABC):
    """
    Abstract base class for compression encoders.

    Defines interface for compression algorithms.
    """

    @property
    @abstractmethod
    def encoding(self) -> str:
        """Get encoding name for Content-Encoding header."""
        pass

    @property
    @abstractmethod
    def available(self) -> bool:
        """Check if encoder is available."""
        pass

    @abstractmethod
    def compress(self, data: bytes) -> bytes:
        """
        Compress data.

        Args:
            data: Raw bytes to compress

        Returns:
            Compressed bytes
        """
        pass

    @abstractmethod
    def compress_stream(self, data: bytes, chunk_size: int = 8192) -> bytes:
        """
        Compress data in streaming fashion.

        Useful for large responses to avoid loading entire response in memory.

        Args:
            data: Raw bytes to compress
            chunk_size: Size of chunks to process

        Returns:
            Compressed bytes
        """
        pass


class GzipEncoder(CompressionEncoder):
    """
    Gzip compression encoder.

    Uses Python's built-in gzip module for compression.
    Always available as it's part of the standard library.
    """

    def __init__(self, level: int = 6):
        """
        Initialize gzip encoder.

        Args:
            level: Compression level (1-9)
                1 = fastest, lowest compression
                9 = slowest, highest compression
                6 = balanced (default)
        """
        if not 1 <= level <= 9:
            raise ValueError(f"Invalid gzip level {level}, must be 1-9")
        self.level = level
        logger.debug(f"GzipEncoder initialized with level {level}")

    @property
    def encoding(self) -> str:
        """Get encoding name for Content-Encoding header."""
        return "gzip"

    @property
    def available(self) -> bool:
        """Gzip is always available (standard library)."""
        return True

    def compress(self, data: bytes) -> bytes:
        """
        Compress data with gzip.

        Args:
            data: Raw bytes to compress

        Returns:
            Gzip-compressed bytes
        """
        return gzip.compress(data, compresslevel=self.level)

    def compress_stream(self, data: bytes, chunk_size: int = 8192) -> bytes:
        """
        Compress data in streaming fashion.

        Args:
            data: Raw bytes to compress
            chunk_size: Size of chunks to process

        Returns:
            Gzip-compressed bytes
        """
        output = io.BytesIO()

        with gzip.GzipFile(fileobj=output, mode="wb", compresslevel=self.level) as gz:
            # Process data in chunks
            offset = 0
            while offset < len(data):
                chunk = data[offset:offset + chunk_size]
                gz.write(chunk)
                offset += chunk_size

        return output.getvalue()


class BrotliEncoder(CompressionEncoder):
    """
    Brotli compression encoder.

    Brotli typically provides better compression ratios than gzip,
    especially for text content. Requires the 'brotli' package.

    Note: Falls back gracefully if brotli is not installed.
    """

    def __init__(self, quality: int = 4):
        """
        Initialize brotli encoder.

        Args:
            quality: Compression quality (0-11)
                0 = fastest, lowest compression
                11 = slowest, highest compression
                4 = balanced (default)
        """
        if not 0 <= quality <= 11:
            raise ValueError(f"Invalid brotli quality {quality}, must be 0-11")
        self.quality = quality

        # Try to import brotli
        try:
            import brotli
            self._brotli = brotli
            self._available = True
            logger.debug(f"BrotliEncoder initialized with quality {quality}")
        except ImportError:
            self._brotli = None
            self._available = False
            logger.warning(
                "Brotli compression not available. "
                "Install with: pip install brotli"
            )

    @property
    def encoding(self) -> str:
        """Get encoding name for Content-Encoding header."""
        return "br"  # 'br' is the standard encoding name for brotli

    @property
    def available(self) -> bool:
        """Check if brotli module is available."""
        return self._available

    def compress(self, data: bytes) -> bytes:
        """
        Compress data with brotli.

        Args:
            data: Raw bytes to compress

        Returns:
            Brotli-compressed bytes

        Raises:
            RuntimeError: If brotli is not available
        """
        if not self.available:
            raise RuntimeError("Brotli compression not available")

        return self._brotli.compress(data, quality=self.quality)

    def compress_stream(self, data: bytes, chunk_size: int = 8192) -> bytes:
        """
        Compress data in streaming fashion.

        Args:
            data: Raw bytes to compress
            chunk_size: Size of chunks to process

        Returns:
            Brotli-compressed bytes

        Raises:
            RuntimeError: If brotli is not available
        """
        if not self.available:
            raise RuntimeError("Brotli compression not available")

        compressor = self._brotli.Compressor(quality=self.quality)

        # Process data in chunks
        output = io.BytesIO()
        offset = 0
        while offset < len(data):
            chunk = data[offset:offset + chunk_size]
            compressed_chunk = compressor.process(chunk)
            if compressed_chunk:
                output.write(compressed_chunk)
            offset += chunk_size

        # Flush any remaining data
        final_chunk = compressor.flush()
        if final_chunk:
            output.write(final_chunk)

        return output.getvalue()


class EncoderFactory:
    """
    Factory for creating compression encoders.

    Handles encoder selection based on client preferences and availability.
    """

    def __init__(self, gzip_level: int = 6, brotli_quality: int = 4):
        """
        Initialize encoder factory.

        Args:
            gzip_level: Default gzip compression level (1-9)
            brotli_quality: Default brotli quality level (0-11)
        """
        self.gzip_level = gzip_level
        self.brotli_quality = brotli_quality

        # Pre-create encoders
        self._gzip_encoder = GzipEncoder(level=gzip_level)
        self._brotli_encoder = BrotliEncoder(quality=brotli_quality)

        logger.info(
            f"EncoderFactory initialized: "
            f"gzip={self._gzip_encoder.available}, "
            f"brotli={self._brotli_encoder.available}"
        )

    def get_encoder(self, accept_encoding: str) -> Optional[CompressionEncoder]:
        """
        Get best encoder based on Accept-Encoding header.

        Negotiates compression based on client preferences and availability.
        Prefers brotli over gzip when both are acceptable.

        Args:
            accept_encoding: Accept-Encoding header value
                Example: "gzip, deflate, br"

        Returns:
            Best available encoder, or None if no match
        """
        if not accept_encoding:
            return None

        # Parse Accept-Encoding header
        # Format: "encoding1;q=0.9, encoding2, encoding3;q=0.5"
        encodings = self._parse_accept_encoding(accept_encoding)

        # Try encoders in order of preference
        # Brotli first (better compression)
        if "br" in encodings and self._brotli_encoder.available:
            logger.debug("Selected brotli encoder")
            return self._brotli_encoder

        # Gzip fallback
        if "gzip" in encodings and self._gzip_encoder.available:
            logger.debug("Selected gzip encoder")
            return self._gzip_encoder

        # No suitable encoder
        logger.debug("No suitable encoder found")
        return None

    def _parse_accept_encoding(self, header: str) -> set:
        """
        Parse Accept-Encoding header.

        Extracts supported encodings, ignoring quality values.

        Args:
            header: Accept-Encoding header value

        Returns:
            Set of supported encoding names
        """
        encodings = set()

        for part in header.lower().split(","):
            # Remove quality value if present (e.g., "gzip;q=0.9" -> "gzip")
            encoding = part.split(";")[0].strip()
            if encoding:
                encodings.add(encoding)

        return encodings

    @property
    def available_encoders(self) -> list[str]:
        """
        Get list of available encoding names.

        Returns:
            List of available encoding names
        """
        encoders = []
        if self._gzip_encoder.available:
            encoders.append(self._gzip_encoder.encoding)
        if self._brotli_encoder.available:
            encoders.append(self._brotli_encoder.encoding)
        return encoders
