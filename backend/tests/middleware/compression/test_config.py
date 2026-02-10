"""Tests for compression configuration (no DB)."""

from __future__ import annotations

from app.middleware.compression.config import (
    DEFAULT_CONFIG,
    DEVELOPMENT_CONFIG,
    PRODUCTION_CONFIG,
    CompressionConfig,
    get_compression_config,
    is_compressible_content_type,
    should_exclude_path,
)


# ---------------------------------------------------------------------------
# CompressionConfig dataclass defaults
# ---------------------------------------------------------------------------


class TestCompressionConfigDefaults:
    def test_enabled(self):
        cfg = CompressionConfig()
        assert cfg.enabled is True

    def test_min_size(self):
        cfg = CompressionConfig()
        assert cfg.min_size == 1024

    def test_gzip_defaults(self):
        cfg = CompressionConfig()
        assert cfg.gzip_enabled is True
        assert 1 <= cfg.gzip_level <= 9

    def test_brotli_defaults(self):
        cfg = CompressionConfig()
        assert cfg.brotli_enabled is True
        assert 0 <= cfg.brotli_quality <= 11

    def test_compressible_types_includes_json(self):
        cfg = CompressionConfig()
        assert "application/json" in cfg.compressible_types

    def test_compressible_types_includes_html(self):
        cfg = CompressionConfig()
        assert "text/html" in cfg.compressible_types

    def test_compressible_types_includes_svg(self):
        cfg = CompressionConfig()
        assert "image/svg+xml" in cfg.compressible_types

    def test_exclude_paths_includes_health(self):
        cfg = CompressionConfig()
        assert "/health" in cfg.exclude_paths

    def test_exclude_paths_includes_metrics(self):
        cfg = CompressionConfig()
        assert "/metrics" in cfg.exclude_paths

    def test_track_stats_default(self):
        cfg = CompressionConfig()
        assert cfg.track_stats is True


# ---------------------------------------------------------------------------
# Custom construction
# ---------------------------------------------------------------------------


class TestCompressionConfigCustom:
    def test_disabled(self):
        cfg = CompressionConfig(enabled=False)
        assert cfg.enabled is False

    def test_custom_min_size(self):
        cfg = CompressionConfig(min_size=512)
        assert cfg.min_size == 512

    def test_custom_gzip_level(self):
        cfg = CompressionConfig(gzip_level=9)
        assert cfg.gzip_level == 9

    def test_custom_types(self):
        cfg = CompressionConfig(compressible_types={"text/plain"})
        assert cfg.compressible_types == {"text/plain"}


# ---------------------------------------------------------------------------
# Pre-built configurations
# ---------------------------------------------------------------------------


class TestPrebuiltConfigs:
    def test_default_enabled(self):
        assert DEFAULT_CONFIG.enabled is True

    def test_production_high_gzip(self):
        assert PRODUCTION_CONFIG.gzip_level == 9

    def test_production_high_brotli(self):
        assert PRODUCTION_CONFIG.brotli_quality == 11

    def test_production_smaller_min_size(self):
        assert PRODUCTION_CONFIG.min_size < DEFAULT_CONFIG.min_size

    def test_development_low_gzip(self):
        assert DEVELOPMENT_CONFIG.gzip_level == 1

    def test_development_low_brotli(self):
        assert DEVELOPMENT_CONFIG.brotli_quality == 1

    def test_development_larger_min_size(self):
        assert DEVELOPMENT_CONFIG.min_size > DEFAULT_CONFIG.min_size


# ---------------------------------------------------------------------------
# get_compression_config
# ---------------------------------------------------------------------------


class TestGetCompressionConfig:
    def test_default(self):
        cfg = get_compression_config("default")
        assert cfg is DEFAULT_CONFIG

    def test_production(self):
        cfg = get_compression_config("production")
        assert cfg is PRODUCTION_CONFIG

    def test_development(self):
        cfg = get_compression_config("development")
        assert cfg is DEVELOPMENT_CONFIG

    def test_unknown_returns_default(self):
        cfg = get_compression_config("staging")
        assert cfg is DEFAULT_CONFIG

    def test_case_insensitive(self):
        cfg = get_compression_config("PRODUCTION")
        assert cfg is PRODUCTION_CONFIG

    def test_no_arg_returns_default(self):
        cfg = get_compression_config()
        assert cfg is DEFAULT_CONFIG


# ---------------------------------------------------------------------------
# is_compressible_content_type
# ---------------------------------------------------------------------------


class TestIsCompressibleContentType:
    def test_json(self):
        assert is_compressible_content_type("application/json", DEFAULT_CONFIG) is True

    def test_html(self):
        assert is_compressible_content_type("text/html", DEFAULT_CONFIG) is True

    def test_json_with_charset(self):
        assert (
            is_compressible_content_type(
                "application/json; charset=utf-8", DEFAULT_CONFIG
            )
            is True
        )

    def test_css(self):
        assert is_compressible_content_type("text/css", DEFAULT_CONFIG) is True

    def test_svg(self):
        assert is_compressible_content_type("image/svg+xml", DEFAULT_CONFIG) is True

    def test_png_not_compressible(self):
        assert is_compressible_content_type("image/png", DEFAULT_CONFIG) is False

    def test_jpeg_not_compressible(self):
        assert is_compressible_content_type("image/jpeg", DEFAULT_CONFIG) is False

    def test_octet_stream_not_compressible(self):
        assert (
            is_compressible_content_type("application/octet-stream", DEFAULT_CONFIG)
            is False
        )

    def test_empty_string(self):
        assert is_compressible_content_type("", DEFAULT_CONFIG) is False

    def test_uppercase_normalized(self):
        assert is_compressible_content_type("Application/JSON", DEFAULT_CONFIG) is True


# ---------------------------------------------------------------------------
# should_exclude_path
# ---------------------------------------------------------------------------


class TestShouldExcludePath:
    def test_health_excluded(self):
        assert should_exclude_path("/health", DEFAULT_CONFIG) is True

    def test_metrics_excluded(self):
        assert should_exclude_path("/metrics", DEFAULT_CONFIG) is True

    def test_docs_excluded(self):
        assert should_exclude_path("/docs", DEFAULT_CONFIG) is True

    def test_openapi_excluded(self):
        assert should_exclude_path("/openapi.json", DEFAULT_CONFIG) is True

    def test_api_not_excluded(self):
        assert should_exclude_path("/api/v1/persons", DEFAULT_CONFIG) is False

    def test_random_path_not_excluded(self):
        assert should_exclude_path("/foo/bar", DEFAULT_CONFIG) is False
