"""Tests for json_to_xlsx_converter.py - JSON to XLSX conversion.

These tests use mocking to avoid JSONB/SQLite compatibility issues.
"""

import json
from unittest.mock import MagicMock, patch

import pytest

from app.services.json_to_xlsx_converter import JSONToXlsxConverter


class TestJSONToXlsxConverter:
    """Tests for JSONToXlsxConverter.convert_from_json() method."""

    def test_inherits_from_xml_converter(self):
        """JSONToXlsxConverter should inherit from XMLToXlsxConverter."""
        from app.services.xml_to_xlsx_converter import XMLToXlsxConverter

        assert issubclass(JSONToXlsxConverter, XMLToXlsxConverter)

    @patch.object(JSONToXlsxConverter, "convert_from_data")
    def test_convert_from_json_accepts_dict(self, mock_convert):
        """convert_from_json() should accept dict input."""
        mock_convert.return_value = b"xlsx_bytes"

        converter = JSONToXlsxConverter.__new__(JSONToXlsxConverter)
        converter.template_path = None
        converter.structure_path = None

        data = {"block_start": "2026-03-12", "residents": []}
        result = converter.convert_from_json(data)

        mock_convert.assert_called_once()
        assert result == b"xlsx_bytes"

    @patch.object(JSONToXlsxConverter, "convert_from_data")
    def test_convert_from_json_accepts_string(self, mock_convert):
        """convert_from_json() should accept JSON string input."""
        mock_convert.return_value = b"xlsx_bytes"

        converter = JSONToXlsxConverter.__new__(JSONToXlsxConverter)
        converter.template_path = None
        converter.structure_path = None

        json_string = '{"block_start": "2026-03-12", "residents": []}'
        result = converter.convert_from_json(json_string)

        mock_convert.assert_called_once()
        assert result == b"xlsx_bytes"

    @patch.object(JSONToXlsxConverter, "convert_from_data")
    def test_convert_from_json_accepts_bytes(self, mock_convert):
        """convert_from_json() should accept bytes input."""
        mock_convert.return_value = b"xlsx_bytes"

        converter = JSONToXlsxConverter.__new__(JSONToXlsxConverter)
        converter.template_path = None
        converter.structure_path = None

        json_bytes = b'{"block_start": "2026-03-12", "residents": []}'
        result = converter.convert_from_json(json_bytes)

        mock_convert.assert_called_once()
        assert result == b"xlsx_bytes"

    @patch.object(JSONToXlsxConverter, "convert_from_data")
    def test_convert_returns_bytes(self, mock_convert):
        """convert_from_json() should return bytes."""
        mock_convert.return_value = b"xlsx_content_here"

        converter = JSONToXlsxConverter.__new__(JSONToXlsxConverter)
        converter.template_path = None
        converter.structure_path = None

        result = converter.convert_from_json({"data": "test"})

        assert isinstance(result, bytes)
