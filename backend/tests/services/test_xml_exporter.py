"""Tests for XMLExporter service."""

import gzip
import pytest
import xml.etree.ElementTree as ET
from datetime import date, datetime

from app.services.export.xml_exporter import XMLExporter


class TestXMLExporter:
    """Test suite for XMLExporter."""

    # ========================================================================
    # Export Analytics Tests
    # ========================================================================

    @pytest.mark.asyncio
    async def test_export_analytics_basic(self):
        """Test basic analytics export to XML."""
        exporter = XMLExporter(db=None)

        metrics_data = [
            {"metric": "utilization", "value": 0.75, "timestamp": "2025-01-01"},
            {"metric": "coverage", "value": 0.95, "timestamp": "2025-01-01"},
        ]

        result = await exporter.export_analytics(
            metrics_data=metrics_data,
            compress=False,
            pretty=False,
        )

        # Parse XML
        xml_str = result.decode("utf-8")
        root = ET.fromstring(xml_str)

        assert root.tag == "export"
        assert root.find("metadata/export_type").text == "analytics"
        assert root.find("metadata/total_count").text == "2"

        data_elem = root.find("data")
        metrics = data_elem.findall("metric")
        assert len(metrics) == 2

    @pytest.mark.asyncio
    async def test_export_analytics_pretty(self):
        """Test analytics export with pretty printing."""
        exporter = XMLExporter(db=None)

        metrics_data = [{"metric": "test", "value": 1}]

        result = await exporter.export_analytics(
            metrics_data=metrics_data,
            compress=False,
            pretty=True,
        )

        xml_str = result.decode("utf-8")
        # Pretty printed XML should have newlines and indentation
        assert "\n" in xml_str
        assert "  " in xml_str

    @pytest.mark.asyncio
    async def test_export_analytics_compressed(self):
        """Test analytics export with compression."""
        exporter = XMLExporter(db=None)

        metrics_data = [{"metric": "test", "value": 1}]

        result = await exporter.export_analytics(
            metrics_data=metrics_data,
            compress=True,
            pretty=False,
        )

        # Decompress and verify
        decompressed = gzip.decompress(result).decode("utf-8")
        root = ET.fromstring(decompressed)
        assert root.find("metadata/export_type").text == "analytics"

    @pytest.mark.asyncio
    async def test_export_analytics_empty(self):
        """Test exporting empty analytics data."""
        exporter = XMLExporter(db=None)

        result = await exporter.export_analytics(
            metrics_data=[],
            compress=False,
        )

        xml_str = result.decode("utf-8")
        root = ET.fromstring(xml_str)
        assert root.find("metadata/total_count").text == "0"

    # ========================================================================
    # Dict to XML Conversion Tests
    # ========================================================================

    def test_dict_to_xml_simple(self):
        """Test converting simple dict to XML."""
        exporter = XMLExporter(db=None)

        data = {"name": "John", "age": 30, "active": True}
        elem = exporter._dict_to_xml(data, "person")

        assert elem.tag == "person"
        assert elem.find("name").text == "John"
        assert elem.find("age").text == "30"
        assert elem.find("active").text == "True"

    def test_dict_to_xml_with_none(self):
        """Test converting dict with None values to XML."""
        exporter = XMLExporter(db=None)

        data = {"name": "John", "middle_name": None}
        elem = exporter._dict_to_xml(data, "person")

        middle_elem = elem.find("middle_name")
        assert middle_elem is not None
        assert middle_elem.get("null") == "true"

    def test_dict_to_xml_nested(self):
        """Test converting nested dict to XML."""
        exporter = XMLExporter(db=None)

        data = {
            "person": "John",
            "address": {
                "street": "123 Main St",
                "city": "Springfield",
            }
        }
        elem = exporter._dict_to_xml(data, "record")

        assert elem.find("address/street").text == "123 Main St"
        assert elem.find("address/city").text == "Springfield"

    def test_dict_to_xml_with_list(self):
        """Test converting dict with list to XML."""
        exporter = XMLExporter(db=None)

        data = {
            "name": "John",
            "hobbies": ["reading", "hiking", "coding"]
        }
        elem = exporter._dict_to_xml(data, "person")

        hobbies_elem = elem.find("hobbies")
        items = hobbies_elem.findall("item")
        assert len(items) == 3
        assert items[0].text == "reading"

    # ========================================================================
    # Utility Tests
    # ========================================================================

    def test_get_content_type_xml(self):
        """Test getting content type for XML."""
        content_type = XMLExporter.get_content_type(compress=False)
        assert content_type == "application/xml"

    def test_get_content_type_compressed(self):
        """Test getting content type for compressed XML."""
        content_type = XMLExporter.get_content_type(compress=True)
        assert content_type == "application/gzip"

    def test_get_filename_basic(self):
        """Test generating basic XML filename."""
        filename = XMLExporter.get_filename("test", compress=False, timestamp=False)
        assert filename == "test.xml"

    def test_get_filename_compressed(self):
        """Test generating compressed XML filename."""
        filename = XMLExporter.get_filename("test", compress=True, timestamp=False)
        assert filename == "test.xml.gz"

    def test_get_filename_with_timestamp(self):
        """Test generating filename with timestamp."""
        filename = XMLExporter.get_filename("test", compress=False, timestamp=True)
        assert filename.startswith("test_")
        assert filename.endswith(".xml")

    # ========================================================================
    # Compression Tests
    # ========================================================================

    def test_compress_xml(self):
        """Test XML compression."""
        exporter = XMLExporter(db=None)

        test_xml = "<root><data>test</data></root>"
        compressed = exporter._compress(test_xml)

        assert isinstance(compressed, bytes)
        assert len(compressed) > 0

        # Verify decompression
        decompressed = gzip.decompress(compressed).decode("utf-8")
        assert decompressed == test_xml

    # ========================================================================
    # Placeholder Tests for Database Operations
    # ========================================================================

    @pytest.mark.asyncio
    async def test_export_assignments_structure(self):
        """Test XML structure for assignment exports."""
        # Placeholder - would need async DB
        pass

    @pytest.mark.asyncio
    async def test_export_schedule_nested_format(self):
        """Test nested schedule export format."""
        # Placeholder - would need async DB
        pass

    @pytest.mark.asyncio
    async def test_export_people_with_type_filter(self):
        """Test exporting people with type filters."""
        # Placeholder - would need async DB
        pass

    @pytest.mark.asyncio
    async def test_export_blocks_metadata(self):
        """Test blocks export metadata."""
        # Placeholder - would need async DB
        pass
