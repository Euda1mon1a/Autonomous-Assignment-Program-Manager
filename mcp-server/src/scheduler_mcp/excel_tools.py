"""
Excel export tools for the Scheduler MCP server.

Provides MCP tools for exporting block and yearly schedules
as Excel (.xlsx) files via the FastAPI backend.
"""

import logging
import os
from pathlib import Path

from pydantic import BaseModel, Field

from .api_client import get_api_client

logger = logging.getLogger(__name__)

# Default export directory (configurable via env var)
EXCEL_EXPORT_DIR = os.environ.get("EXCEL_EXPORT_DIR", "exports")


# =============================================================================
# Response Models
# =============================================================================


class ExcelExportResult(BaseModel):
    """Result of an Excel export operation."""

    success: bool = Field(..., description="Whether export succeeded")
    file_path: str = Field("", description="Path to exported file")
    file_size_bytes: int = Field(0, description="File size in bytes")
    filename: str = Field("", description="Export filename")
    error: str | None = Field(None, description="Error message if failed")


# =============================================================================
# Tool Functions
# =============================================================================


async def export_block_xlsx(
    start_date: str,
    end_date: str,
    block_number: int | None = None,
    include_qa_sheet: bool = True,
    include_overrides: bool = True,
) -> ExcelExportResult:
    """
    Export a block schedule as Excel (.xlsx) file.

    Generates an Excel file using the canonical Block Template2 format,
    filled from half_day_assignments. The file is saved to the exports
    directory (configurable via EXCEL_EXPORT_DIR env var).

    Args:
        start_date: Block start date (YYYY-MM-DD)
        end_date: Block end date (YYYY-MM-DD)
        block_number: Block number for header (auto-calculated if omitted)
        include_qa_sheet: Include QA validation sheet (default True)
        include_overrides: Include override assignments (default True)

    Returns:
        ExcelExportResult with file path and size
    """
    try:
        client = await get_api_client()
        xlsx_bytes = await client.export_block_xlsx(
            start_date=start_date,
            end_date=end_date,
            block_number=block_number,
            include_qa_sheet=include_qa_sheet,
            include_overrides=include_overrides,
        )

        # Save to exports directory
        export_dir = Path(EXCEL_EXPORT_DIR)
        export_dir.mkdir(parents=True, exist_ok=True)

        clean_start = start_date.replace("-", "")
        clean_end = end_date.replace("-", "")
        filename = f"schedule_{clean_start}_{clean_end}.xlsx"
        file_path = export_dir / filename

        file_path.write_bytes(xlsx_bytes)
        file_size = len(xlsx_bytes)

        logger.info(f"Exported block schedule: {file_path} ({file_size} bytes)")

        return ExcelExportResult(
            success=True,
            file_path=str(file_path.resolve()),
            file_size_bytes=file_size,
            filename=filename,
        )

    except Exception as e:
        logger.error(f"Failed to export block schedule: {e}")
        return ExcelExportResult(success=False, error=str(e))


async def export_year_xlsx(
    academic_year: int,
    include_overrides: bool = True,
) -> ExcelExportResult:
    """
    Export all blocks for an academic year as a single Excel (.xlsx) file.

    Generates a multi-sheet Excel workbook with blocks 0-13 in the
    canonical Block Template2 format. The file is saved to the exports
    directory (configurable via EXCEL_EXPORT_DIR env var).

    Args:
        academic_year: Academic year (e.g. 2025 for AY 25-26)
        include_overrides: Include override assignments (default True)

    Returns:
        ExcelExportResult with file path and size
    """
    try:
        client = await get_api_client()
        xlsx_bytes = await client.export_year_xlsx(
            academic_year=academic_year,
            include_overrides=include_overrides,
        )

        # Save to exports directory
        export_dir = Path(EXCEL_EXPORT_DIR)
        export_dir.mkdir(parents=True, exist_ok=True)

        filename = f"schedule_ay{academic_year}_{academic_year + 1}.xlsx"
        file_path = export_dir / filename

        file_path.write_bytes(xlsx_bytes)
        file_size = len(xlsx_bytes)

        logger.info(f"Exported year schedule: {file_path} ({file_size} bytes)")

        return ExcelExportResult(
            success=True,
            file_path=str(file_path.resolve()),
            file_size_bytes=file_size,
            filename=filename,
        )

    except Exception as e:
        logger.error(f"Failed to export year schedule: {e}")
        return ExcelExportResult(success=False, error=str(e))
