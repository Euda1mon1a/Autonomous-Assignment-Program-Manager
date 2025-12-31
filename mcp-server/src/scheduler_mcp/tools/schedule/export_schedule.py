"""
Export schedule tool for generating schedule reports.
"""

from typing import Any

from pydantic import BaseModel, Field

from ..base import BaseTool
from ..validator import validate_date_range


class ExportScheduleRequest(BaseModel):
    """Request to export a schedule."""

    start_date: str = Field(..., description="Start date in YYYY-MM-DD format")
    end_date: str = Field(..., description="End date in YYYY-MM-DD format")
    format: str = Field(
        default="json",
        description="Export format (json, csv, xlsx, pdf)",
    )
    include_metadata: bool = Field(
        default=True,
        description="Include schedule metadata",
    )
    anonymize: bool = Field(
        default=False,
        description="Anonymize person information",
    )


class ExportScheduleResponse(BaseModel):
    """Response from export schedule."""

    success: bool
    message: str
    format: str
    data: str | dict[str, Any] | None = None
    download_url: str | None = None
    file_size_bytes: int | None = None


class ExportScheduleTool(BaseTool[ExportScheduleRequest, ExportScheduleResponse]):
    """
    Tool for exporting schedules.

    Generates schedule exports in various formats (JSON, CSV, Excel, PDF).
    """

    @property
    def name(self) -> str:
        return "export_schedule"

    @property
    def description(self) -> str:
        return (
            "Export a schedule in various formats (JSON, CSV, Excel, PDF). "
            "Supports metadata inclusion and anonymization."
        )

    def validate_input(self, **kwargs: Any) -> ExportScheduleRequest:
        """Validate input parameters."""
        # Validate dates
        start_date = kwargs.get("start_date", "")
        end_date = kwargs.get("end_date", "")
        validate_date_range(start_date, end_date, max_days=365)

        # Validate format
        format_value = kwargs.get("format", "json").lower()
        valid_formats = ["json", "csv", "xlsx", "pdf"]
        if format_value not in valid_formats:
            from ..base import ValidationError

            raise ValidationError(
                f"Invalid format: {format_value}",
                details={"value": format_value, "valid": valid_formats},
            )

        return ExportScheduleRequest(
            start_date=start_date,
            end_date=end_date,
            format=format_value,
            include_metadata=kwargs.get("include_metadata", True),
            anonymize=kwargs.get("anonymize", False),
        )

    async def execute(
        self, request: ExportScheduleRequest
    ) -> ExportScheduleResponse:
        """Execute the tool."""
        client = self._require_api_client()

        try:
            # Export schedule via API
            result = await client.client.post(
                f"{client.config.api_prefix}/schedule/export",
                headers=await client._ensure_authenticated(),
                json={
                    "start_date": request.start_date,
                    "end_date": request.end_date,
                    "format": request.format,
                    "include_metadata": request.include_metadata,
                    "anonymize": request.anonymize,
                },
            )
            result.raise_for_status()
            data = result.json()

            # Handle different response types
            if request.format == "json":
                export_data = data.get("data")
            else:
                export_data = None

            return ExportScheduleResponse(
                success=True,
                message="Schedule exported successfully",
                format=request.format,
                data=export_data,
                download_url=data.get("download_url"),
                file_size_bytes=data.get("file_size_bytes"),
            )

        except Exception as e:
            return ExportScheduleResponse(
                success=False,
                message=f"Failed to export schedule: {e}",
                format=request.format,
            )
