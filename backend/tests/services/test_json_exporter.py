"""Tests for JSONExporter service."""

import gzip
import json
import pytest
from datetime import date, datetime
from uuid import UUID, uuid4

from app.services.export.json_exporter import JSONExporter, JSONEncoder


class TestJSONEncoder:
    """Test suite for JSONEncoder."""

    def test_encode_datetime(self):
        """Test encoding datetime objects."""
        encoder = JSONEncoder()
        dt = datetime(2025, 1, 1, 12, 0, 0)
        result = json.dumps({"date": dt}, cls=JSONEncoder)
        assert "2025-01-01T12:00:00" in result

    def test_encode_date(self):
        """Test encoding date objects."""
        encoder = JSONEncoder()
        d = date(2025, 1, 1)
        result = json.dumps({"date": d}, cls=JSONEncoder)
        assert "2025-01-01" in result

    def test_encode_uuid(self):
        """Test encoding UUID objects."""
        encoder = JSONEncoder()
        test_uuid = uuid4()
        result = json.dumps({"id": test_uuid}, cls=JSONEncoder)
        assert str(test_uuid) in result


class TestJSONExporter:
    """Test suite for JSONExporter."""

    # ========================================================================
    # Export Analytics Tests
    # ========================================================================

    @pytest.mark.asyncio
    async def test_export_analytics_basic(self):
        """Test basic analytics export to JSON."""
        exporter = JSONExporter(db=None)

        metrics_data = [
            {"metric": "utilization", "value": 0.75, "timestamp": "2025-01-01"},
            {"metric": "coverage", "value": 0.95, "timestamp": "2025-01-01"},
        ]

        result = await exporter.export_analytics(
            metrics_data=metrics_data,
            compress=False,
            pretty=False,
        )

        # Parse JSON
        data = json.loads(result.decode("utf-8"))

        assert "data" in data
        assert "metadata" in data
        assert len(data["data"]) == 2
        assert data["metadata"]["export_type"] == "analytics"
        assert data["metadata"]["total_count"] == 2

    @pytest.mark.asyncio
    async def test_export_analytics_pretty(self):
        """Test analytics export with pretty printing."""
        exporter = JSONExporter(db=None)

        metrics_data = [{"metric": "test", "value": 1}]

        result = await exporter.export_analytics(
            metrics_data=metrics_data,
            compress=False,
            pretty=True,
        )

        json_str = result.decode("utf-8")
        # Pretty printed JSON should have newlines and indentation
        assert "\n" in json_str
        assert "  " in json_str

    @pytest.mark.asyncio
    async def test_export_analytics_compressed(self):
        """Test analytics export with compression."""
        exporter = JSONExporter(db=None)

        metrics_data = [{"metric": "test", "value": 1}]

        result = await exporter.export_analytics(
            metrics_data=metrics_data,
            compress=True,
            pretty=False,
        )

        # Result should be compressed bytes
        assert isinstance(result, bytes)

        # Decompress and verify
        decompressed = gzip.decompress(result).decode("utf-8")
        data = json.loads(decompressed)
        assert data["metadata"]["export_type"] == "analytics"

    @pytest.mark.asyncio
    async def test_export_analytics_empty(self):
        """Test exporting empty analytics data."""
        exporter = JSONExporter(db=None)

        result = await exporter.export_analytics(
            metrics_data=[],
            compress=False,
        )

        data = json.loads(result.decode("utf-8"))
        assert data["metadata"]["total_count"] == 0
        assert len(data["data"]) == 0

    # ========================================================================
    # Utility Tests
    # ========================================================================

    def test_get_content_type_json(self):
        """Test getting content type for JSON."""
        content_type = JSONExporter.get_content_type(compress=False)
        assert content_type == "application/json"

    def test_get_content_type_compressed(self):
        """Test getting content type for compressed JSON."""
        content_type = JSONExporter.get_content_type(compress=True)
        assert content_type == "application/gzip"

    def test_get_filename_basic(self):
        """Test generating basic JSON filename."""
        filename = JSONExporter.get_filename("test", compress=False, timestamp=False)
        assert filename == "test.json"

    def test_get_filename_compressed(self):
        """Test generating compressed JSON filename."""
        filename = JSONExporter.get_filename("test", compress=True, timestamp=False)
        assert filename == "test.json.gz"

    def test_get_filename_with_timestamp(self):
        """Test generating filename with timestamp."""
        filename = JSONExporter.get_filename("test", compress=False, timestamp=True)
        assert filename.startswith("test_")
        assert filename.endswith(".json")
        assert "_" in filename

    # ========================================================================
    # Compression Tests
    # ========================================================================

    def test_compress_json(self):
        """Test JSON compression."""
        exporter = JSONExporter(db=None)

        test_data = {"test": "data", "value": 123}
        json_str = json.dumps(test_data)

        compressed = exporter._compress(json_str)

        # Verify compression
        assert isinstance(compressed, bytes)
        assert len(compressed) > 0

        # Verify decompression
        decompressed = gzip.decompress(compressed).decode("utf-8")
        assert json.loads(decompressed) == test_data

    # ========================================================================
    # Placeholder Tests for Database Operations
    # ========================================================================

    @pytest.mark.asyncio
    async def test_export_assignments_metadata_structure(self):
        """Test that exported assignments have correct metadata structure."""
        # Placeholder - would need async DB
        pass

    @pytest.mark.asyncio
    async def test_export_schedule_nested_vs_flat(self):
        """Test difference between nested and flat schedule exports."""
        # Placeholder - would need async DB
        pass

    @pytest.mark.asyncio
    async def test_export_people_with_filters(self):
        """Test exporting people with type filters."""
        # Placeholder - would need async DB
        pass

    @pytest.mark.asyncio
    async def test_export_blocks_date_range(self):
        """Test exporting blocks with date range filters."""
        # Placeholder - would need async DB
        pass
