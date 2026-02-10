"""Tests for compression encoders (no DB)."""

from __future__ import annotations

import gzip

import pytest

from app.middleware.compression.encoders import (
    BrotliEncoder,
    CompressionEncoder,
    EncoderFactory,
    GzipEncoder,
)


# ---------------------------------------------------------------------------
# GzipEncoder — construction
# ---------------------------------------------------------------------------


class TestGzipEncoderInit:
    def test_default_level(self):
        enc = GzipEncoder()
        assert enc.level == 6

    def test_custom_level(self):
        enc = GzipEncoder(level=9)
        assert enc.level == 9

    def test_min_level(self):
        enc = GzipEncoder(level=1)
        assert enc.level == 1

    def test_max_level(self):
        enc = GzipEncoder(level=9)
        assert enc.level == 9

    def test_level_zero_raises(self):
        with pytest.raises(ValueError, match="Invalid gzip level"):
            GzipEncoder(level=0)

    def test_level_ten_raises(self):
        with pytest.raises(ValueError, match="Invalid gzip level"):
            GzipEncoder(level=10)

    def test_negative_level_raises(self):
        with pytest.raises(ValueError):
            GzipEncoder(level=-1)


# ---------------------------------------------------------------------------
# GzipEncoder — properties
# ---------------------------------------------------------------------------


class TestGzipEncoderProperties:
    def test_encoding_name(self):
        assert GzipEncoder().encoding == "gzip"

    def test_always_available(self):
        assert GzipEncoder().available is True


# ---------------------------------------------------------------------------
# GzipEncoder — compress
# ---------------------------------------------------------------------------


class TestGzipCompress:
    def test_compress_returns_bytes(self):
        enc = GzipEncoder()
        result = enc.compress(b"hello world")
        assert isinstance(result, bytes)

    def test_compress_decompressible(self):
        enc = GzipEncoder()
        original = b"hello world this is test data"
        compressed = enc.compress(original)
        assert gzip.decompress(compressed) == original

    def test_compress_reduces_size_large_data(self):
        enc = GzipEncoder()
        data = b"a" * 10000
        compressed = enc.compress(data)
        assert len(compressed) < len(data)

    def test_compress_empty(self):
        enc = GzipEncoder()
        result = enc.compress(b"")
        assert isinstance(result, bytes)
        assert gzip.decompress(result) == b""

    def test_higher_level_better_compression(self):
        data = b"test data " * 1000
        low = GzipEncoder(level=1).compress(data)
        high = GzipEncoder(level=9).compress(data)
        assert len(high) <= len(low)


# ---------------------------------------------------------------------------
# GzipEncoder — compress_stream
# ---------------------------------------------------------------------------


class TestGzipCompressStream:
    def test_stream_returns_bytes(self):
        enc = GzipEncoder()
        result = enc.compress_stream(b"hello world")
        assert isinstance(result, bytes)

    def test_stream_decompressible(self):
        enc = GzipEncoder()
        original = b"hello world this is streaming test data"
        compressed = enc.compress_stream(original)
        assert gzip.decompress(compressed) == original

    def test_stream_small_chunk_size(self):
        enc = GzipEncoder()
        original = b"abcdefghijklmnopqrstuvwxyz"
        compressed = enc.compress_stream(original, chunk_size=4)
        assert gzip.decompress(compressed) == original

    def test_stream_large_data(self):
        enc = GzipEncoder()
        original = b"x" * 50000
        compressed = enc.compress_stream(original, chunk_size=8192)
        assert gzip.decompress(compressed) == original

    def test_stream_empty(self):
        enc = GzipEncoder()
        result = enc.compress_stream(b"")
        assert isinstance(result, bytes)


# ---------------------------------------------------------------------------
# BrotliEncoder — construction
# ---------------------------------------------------------------------------


class TestBrotliEncoderInit:
    def test_default_quality(self):
        enc = BrotliEncoder()
        assert enc.quality == 4

    def test_custom_quality(self):
        enc = BrotliEncoder(quality=11)
        assert enc.quality == 11

    def test_min_quality(self):
        enc = BrotliEncoder(quality=0)
        assert enc.quality == 0

    def test_max_quality(self):
        enc = BrotliEncoder(quality=11)
        assert enc.quality == 11

    def test_quality_negative_raises(self):
        with pytest.raises(ValueError, match="Invalid brotli quality"):
            BrotliEncoder(quality=-1)

    def test_quality_twelve_raises(self):
        with pytest.raises(ValueError, match="Invalid brotli quality"):
            BrotliEncoder(quality=12)


# ---------------------------------------------------------------------------
# BrotliEncoder — properties
# ---------------------------------------------------------------------------


class TestBrotliEncoderProperties:
    def test_encoding_name(self):
        assert BrotliEncoder().encoding == "br"

    def test_available_depends_on_import(self):
        enc = BrotliEncoder()
        # available is True if brotli package installed, False otherwise
        assert isinstance(enc.available, bool)


# ---------------------------------------------------------------------------
# BrotliEncoder — compress (conditional on availability)
# ---------------------------------------------------------------------------


class TestBrotliCompress:
    def test_compress_unavailable_raises(self):
        enc = BrotliEncoder()
        if not enc.available:
            with pytest.raises(RuntimeError, match="not available"):
                enc.compress(b"hello")

    def test_compress_stream_unavailable_raises(self):
        enc = BrotliEncoder()
        if not enc.available:
            with pytest.raises(RuntimeError, match="not available"):
                enc.compress_stream(b"hello")

    def test_compress_if_available(self):
        enc = BrotliEncoder()
        if enc.available:
            result = enc.compress(b"hello world test data")
            assert isinstance(result, bytes)
            assert len(result) > 0

    def test_compress_stream_if_available(self):
        enc = BrotliEncoder()
        if enc.available:
            result = enc.compress_stream(b"hello world test data", chunk_size=4)
            assert isinstance(result, bytes)
            assert len(result) > 0


# ---------------------------------------------------------------------------
# EncoderFactory — construction
# ---------------------------------------------------------------------------


class TestEncoderFactoryInit:
    def test_default_levels(self):
        factory = EncoderFactory()
        assert factory.gzip_level == 6
        assert factory.brotli_quality == 4

    def test_custom_levels(self):
        factory = EncoderFactory(gzip_level=9, brotli_quality=11)
        assert factory.gzip_level == 9
        assert factory.brotli_quality == 11

    def test_gzip_encoder_created(self):
        factory = EncoderFactory()
        assert factory._gzip_encoder is not None
        assert factory._gzip_encoder.available is True

    def test_brotli_encoder_created(self):
        factory = EncoderFactory()
        assert factory._brotli_encoder is not None


# ---------------------------------------------------------------------------
# EncoderFactory._parse_accept_encoding
# ---------------------------------------------------------------------------


class TestParseAcceptEncoding:
    def test_simple(self):
        factory = EncoderFactory()
        result = factory._parse_accept_encoding("gzip")
        assert result == {"gzip"}

    def test_multiple(self):
        factory = EncoderFactory()
        result = factory._parse_accept_encoding("gzip, deflate, br")
        assert result == {"gzip", "deflate", "br"}

    def test_with_quality(self):
        factory = EncoderFactory()
        result = factory._parse_accept_encoding("gzip;q=0.9, br;q=1.0")
        assert "gzip" in result
        assert "br" in result

    def test_case_insensitive(self):
        factory = EncoderFactory()
        result = factory._parse_accept_encoding("GZIP, BR")
        assert "gzip" in result
        assert "br" in result

    def test_extra_whitespace(self):
        factory = EncoderFactory()
        result = factory._parse_accept_encoding("  gzip  ,  br  ")
        assert "gzip" in result
        assert "br" in result

    def test_empty_string(self):
        factory = EncoderFactory()
        result = factory._parse_accept_encoding("")
        assert result == set()

    def test_wildcard(self):
        factory = EncoderFactory()
        result = factory._parse_accept_encoding("*")
        assert "*" in result


# ---------------------------------------------------------------------------
# EncoderFactory.get_encoder
# ---------------------------------------------------------------------------


class TestGetEncoder:
    def test_gzip_selected(self):
        factory = EncoderFactory()
        enc = factory.get_encoder("gzip")
        assert enc is not None
        assert enc.encoding == "gzip"

    def test_empty_returns_none(self):
        factory = EncoderFactory()
        assert factory.get_encoder("") is None

    def test_no_match_returns_none(self):
        factory = EncoderFactory()
        assert factory.get_encoder("deflate") is None

    def test_prefers_brotli_if_available(self):
        factory = EncoderFactory()
        enc = factory.get_encoder("gzip, br")
        if factory._brotli_encoder.available:
            assert enc.encoding == "br"
        else:
            assert enc.encoding == "gzip"

    def test_gzip_fallback_when_brotli_unavailable(self):
        factory = EncoderFactory()
        if not factory._brotli_encoder.available:
            enc = factory.get_encoder("gzip, br")
            assert enc is not None
            assert enc.encoding == "gzip"


# ---------------------------------------------------------------------------
# EncoderFactory.available_encoders
# ---------------------------------------------------------------------------


class TestAvailableEncoders:
    def test_includes_gzip(self):
        factory = EncoderFactory()
        assert "gzip" in factory.available_encoders

    def test_returns_list(self):
        factory = EncoderFactory()
        result = factory.available_encoders
        assert isinstance(result, list)

    def test_brotli_conditional(self):
        factory = EncoderFactory()
        if factory._brotli_encoder.available:
            assert "br" in factory.available_encoders
        else:
            assert "br" not in factory.available_encoders
