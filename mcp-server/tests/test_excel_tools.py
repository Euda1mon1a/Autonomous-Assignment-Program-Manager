"""
Tests for Excel export tools module.

Tests the structure, models, and tool functions with mocked API client.
"""

from unittest.mock import AsyncMock, patch

import pytest

from scheduler_mcp.excel_tools import (
    ExcelExportResult,
    export_block_xlsx,
    export_year_xlsx,
)

# =============================================================================
# Model Tests
# =============================================================================


class TestModels:
    def test_export_result_success(self):
        result = ExcelExportResult(
            success=True,
            file_path="/tmp/schedule.xlsx",
            file_size_bytes=50000,
            filename="schedule.xlsx",
        )
        assert result.success
        assert result.file_size_bytes == 50000

    def test_export_result_error(self):
        result = ExcelExportResult(
            success=False,
            error="Export failed",
        )
        assert not result.success
        assert result.file_path == ""


# =============================================================================
# Tool Function Tests (mocked API client)
# =============================================================================


@pytest.fixture
def mock_api_client():
    client = AsyncMock()
    with patch("scheduler_mcp.excel_tools.get_api_client", return_value=client):
        yield client


class TestExportBlockXlsx:
    @pytest.mark.asyncio
    async def test_success(self, mock_api_client, tmp_path):
        # Mock returns fake xlsx bytes
        fake_xlsx = b"PK\x03\x04fake-xlsx-content-bytes"
        mock_api_client.export_block_xlsx.return_value = fake_xlsx

        with patch("scheduler_mcp.excel_tools.EXCEL_EXPORT_DIR", str(tmp_path)):
            result = await export_block_xlsx(
                start_date="2026-05-07",
                end_date="2026-06-03",
            )

        assert result.success
        assert result.file_size_bytes == len(fake_xlsx)
        assert "20260507_20260603" in result.filename
        assert (tmp_path / result.filename).exists()

    @pytest.mark.asyncio
    async def test_with_block_number(self, mock_api_client, tmp_path):
        mock_api_client.export_block_xlsx.return_value = b"xlsx-bytes"

        with patch("scheduler_mcp.excel_tools.EXCEL_EXPORT_DIR", str(tmp_path)):
            result = await export_block_xlsx(
                start_date="2026-05-07",
                end_date="2026-06-03",
                block_number=12,
            )

        assert result.success
        mock_api_client.export_block_xlsx.assert_called_once_with(
            start_date="2026-05-07",
            end_date="2026-06-03",
            block_number=12,
            include_qa_sheet=True,
            include_overrides=True,
        )

    @pytest.mark.asyncio
    async def test_error(self, mock_api_client):
        mock_api_client.export_block_xlsx.side_effect = Exception(
            "500 Internal Server Error"
        )

        result = await export_block_xlsx(
            start_date="2026-05-07",
            end_date="2026-06-03",
        )

        assert not result.success
        assert "500" in result.error


class TestExportYearXlsx:
    @pytest.mark.asyncio
    async def test_success(self, mock_api_client, tmp_path):
        fake_xlsx = b"PK\x03\x04year-workbook-bytes"
        mock_api_client.export_year_xlsx.return_value = fake_xlsx

        with patch("scheduler_mcp.excel_tools.EXCEL_EXPORT_DIR", str(tmp_path)):
            result = await export_year_xlsx(academic_year=2025)

        assert result.success
        assert result.filename == "schedule_ay2025_2026.xlsx"
        assert result.file_size_bytes == len(fake_xlsx)
        assert (tmp_path / result.filename).exists()

    @pytest.mark.asyncio
    async def test_without_overrides(self, mock_api_client, tmp_path):
        mock_api_client.export_year_xlsx.return_value = b"bytes"

        with patch("scheduler_mcp.excel_tools.EXCEL_EXPORT_DIR", str(tmp_path)):
            result = await export_year_xlsx(
                academic_year=2025, include_overrides=False
            )

        mock_api_client.export_year_xlsx.assert_called_once_with(
            academic_year=2025, include_overrides=False
        )
        assert result.success

    @pytest.mark.asyncio
    async def test_error(self, mock_api_client):
        mock_api_client.export_year_xlsx.side_effect = Exception("Timeout")

        result = await export_year_xlsx(academic_year=2025)

        assert not result.success
        assert "Timeout" in result.error
