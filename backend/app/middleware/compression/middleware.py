"""
Response compression middleware for FastAPI.

Provides automatic compression of API responses based on:
- Client Accept-Encoding header
- Response content type
- Response size
- Configuration settings

Features:
- Gzip and Brotli compression
- Content-type filtering
- Minimum size threshold
- Accept-Encoding negotiation
- Streaming compression for large responses
- Compression statistics tracking
- Graceful fallback on errors
"""
import logging
import time
from typing import Optional

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.middleware.compression.config import (
    CompressionConfig,
    is_compressible_content_type,
    should_exclude_path,
)
from app.middleware.compression.encoders import CompressionEncoder, EncoderFactory

logger = logging.getLogger(__name__)


class CompressionStats:
    """
    Statistics tracker for compression middleware.

    Tracks compression performance metrics:
    - Total requests processed
    - Compression ratio
    - Time spent compressing
    - Bytes saved
    """

    def __init__(self):
        """Initialize compression statistics."""
        self.total_requests = 0
        self.compressed_requests = 0
        self.total_original_bytes = 0
        self.total_compressed_bytes = 0
        self.total_compression_time = 0.0
        self.compression_errors = 0

    def record_compression(
        self,
        original_size: int,
        compressed_size: int,
        compression_time: float,
    ):
        """
        Record successful compression.

        Args:
            original_size: Original response size in bytes
            compressed_size: Compressed response size in bytes
            compression_time: Time taken to compress in seconds
        """
        self.total_requests += 1
        self.compressed_requests += 1
        self.total_original_bytes += original_size
        self.total_compressed_bytes += compressed_size
        self.total_compression_time += compression_time

    def record_skip(self):
        """Record request that was not compressed."""
        self.total_requests += 1

    def record_error(self):
        """Record compression error."""
        self.total_requests += 1
        self.compression_errors += 1

    @property
    def compression_ratio(self) -> float:
        """
        Calculate average compression ratio.

        Returns:
            Compression ratio (original / compressed)
        """
        if self.total_compressed_bytes == 0:
            return 0.0
        return self.total_original_bytes / self.total_compressed_bytes

    @property
    def bytes_saved(self) -> int:
        """
        Calculate total bytes saved by compression.

        Returns:
            Bytes saved
        """
        return self.total_original_bytes - self.total_compressed_bytes

    @property
    def average_compression_time(self) -> float:
        """
        Calculate average time spent compressing.

        Returns:
            Average compression time in milliseconds
        """
        if self.compressed_requests == 0:
            return 0.0
        return (self.total_compression_time / self.compressed_requests) * 1000

    def get_stats(self) -> dict:
        """
        Get current statistics as dictionary.

        Returns:
            Dictionary of compression statistics
        """
        return {
            "total_requests": self.total_requests,
            "compressed_requests": self.compressed_requests,
            "compression_ratio": round(self.compression_ratio, 2),
            "bytes_saved": self.bytes_saved,
            "average_compression_time_ms": round(self.average_compression_time, 2),
            "compression_errors": self.compression_errors,
        }

    def reset(self):
        """Reset all statistics."""
        self.__init__()


class CompressionMiddleware(BaseHTTPMiddleware):
    """
    Middleware for automatic API response compression.

    Compresses responses based on:
    1. Client Accept-Encoding header (gzip, br)
    2. Response Content-Type (only compressible types)
    3. Response size (above minimum threshold)
    4. Path exclusions (configured paths)

    The middleware:
    - Selects best compression algorithm (prefers Brotli)
    - Compresses response body
    - Sets Content-Encoding header
    - Updates Content-Length header
    - Tracks compression statistics
    - Handles errors gracefully (returns uncompressed on error)
    """

    def __init__(
        self,
        app: ASGIApp,
        config: Optional[CompressionConfig] = None,
    ):
        """
        Initialize compression middleware.

        Args:
            app: FastAPI application
            config: Compression configuration (uses default if not provided)
        """
        super().__init__(app)
        self.config = config or CompressionConfig()
        self.encoder_factory = EncoderFactory(
            gzip_level=self.config.gzip_level,
            brotli_quality=self.config.brotli_quality,
        )
        self.stats = CompressionStats() if self.config.track_stats else None

        logger.info(
            f"CompressionMiddleware initialized: "
            f"min_size={self.config.min_size}B, "
            f"encoders={self.encoder_factory.available_encoders}"
        )

    async def dispatch(self, request: Request, call_next):
        """
        Process request and compress response if applicable.

        Args:
            request: Incoming HTTP request
            call_next: Next middleware in chain

        Returns:
            HTTP response (compressed if applicable)
        """
        # Check if compression is globally disabled
        if not self.config.enabled:
            return await call_next(request)

        # Check if path is excluded
        if should_exclude_path(request.url.path, self.config):
            if self.stats:
                self.stats.record_skip()
            return await call_next(request)

        # Get client's accepted encodings
        accept_encoding = request.headers.get("Accept-Encoding", "")

        # Get encoder for this request
        encoder = self.encoder_factory.get_encoder(accept_encoding)

        if not encoder:
            # Client doesn't accept compression
            if self.stats:
                self.stats.record_skip()
            return await call_next(request)

        # Process request
        response = await call_next(request)

        # Check if response should be compressed
        if not self._should_compress_response(response):
            if self.stats:
                self.stats.record_skip()
            return response

        # Compress response
        try:
            compressed_response = await self._compress_response(response, encoder)
            if self.stats:
                self.stats.record_compression(
                    original_size=len(response.body),
                    compressed_size=len(compressed_response.body),
                    compression_time=0.0,  # Updated in _compress_response
                )
            return compressed_response
        except Exception as e:
            # Log error but return uncompressed response
            logger.error(f"Compression failed: {e}", exc_info=True)
            if self.stats:
                self.stats.record_error()
            return response

    def _should_compress_response(self, response: Response) -> bool:
        """
        Check if response should be compressed.

        Args:
            response: HTTP response

        Returns:
            True if response should be compressed
        """
        # Check if response already has Content-Encoding
        if "content-encoding" in response.headers:
            return False

        # Check if response has body
        if not hasattr(response, "body") or not response.body:
            return False

        # Check minimum size
        if len(response.body) < self.config.min_size:
            logger.debug(
                f"Response too small for compression: "
                f"{len(response.body)}B < {self.config.min_size}B"
            )
            return False

        # Check content type
        content_type = response.headers.get("content-type", "")
        if not is_compressible_content_type(content_type, self.config):
            logger.debug(f"Content type not compressible: {content_type}")
            return False

        return True

    async def _compress_response(
        self,
        response: Response,
        encoder: CompressionEncoder,
    ) -> Response:
        """
        Compress response body.

        Args:
            response: Original HTTP response
            encoder: Compression encoder to use

        Returns:
            Compressed HTTP response
        """
        original_size = len(response.body)
        start_time = time.time()

        # Compress response body
        # Use streaming compression for large responses (>100KB)
        if original_size > 100 * 1024:
            compressed_body = encoder.compress_stream(response.body)
        else:
            compressed_body = encoder.compress(response.body)

        compression_time = time.time() - start_time
        compressed_size = len(compressed_body)

        # Update response
        response.body = compressed_body

        # Update headers
        response.headers["Content-Encoding"] = encoder.encoding
        response.headers["Content-Length"] = str(compressed_size)

        # Add Vary header to indicate response varies by encoding
        if "Vary" in response.headers:
            if "Accept-Encoding" not in response.headers["Vary"]:
                response.headers["Vary"] += ", Accept-Encoding"
        else:
            response.headers["Vary"] = "Accept-Encoding"

        # Log compression results
        ratio = original_size / compressed_size if compressed_size > 0 else 0
        logger.debug(
            f"Compressed response: "
            f"{original_size}B -> {compressed_size}B "
            f"({ratio:.2f}x) in {compression_time*1000:.2f}ms "
            f"using {encoder.encoding}"
        )

        # Update stats with actual compression time
        if self.stats:
            self.stats.total_compression_time += compression_time

        return response

    def get_stats(self) -> Optional[dict]:
        """
        Get compression statistics.

        Returns:
            Dictionary of compression statistics, or None if tracking disabled
        """
        if not self.stats:
            return None
        return self.stats.get_stats()

    def reset_stats(self):
        """Reset compression statistics."""
        if self.stats:
            self.stats.reset()
