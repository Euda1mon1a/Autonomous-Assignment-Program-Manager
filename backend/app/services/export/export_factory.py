"""
Export factory for format selection.

Provides a unified interface for creating exporters based on format type
and managing export operations with consistent configuration.
"""
from datetime import date
from enum import Enum
from typing import Any, AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.export.csv_exporter import CSVExporter
from app.services.export.json_exporter import JSONExporter
from app.services.export.xml_exporter import XMLExporter


class ExportFormat(str, Enum):
    """Supported export formats."""

    CSV = "csv"
    JSON = "json"
    XML = "xml"


class ExportType(str, Enum):
    """Types of data that can be exported."""

    ASSIGNMENTS = "assignments"
    SCHEDULE = "schedule"
    PEOPLE = "people"
    BLOCKS = "blocks"
    ANALYTICS = "analytics"


class ExportFactory:
    """
    Factory for creating and managing data exporters.

    Provides a unified interface for exporting data in different formats
    with consistent configuration and options.
    """

    def __init__(self, db: AsyncSession):
        """
        Initialize export factory.

        Args:
            db: Async database session
        """
        self.db = db
        self._exporters = {
            ExportFormat.CSV: CSVExporter(db),
            ExportFormat.JSON: JSONExporter(db),
            ExportFormat.XML: XMLExporter(db),
        }

    def get_exporter(self, format: ExportFormat | str):
        """
        Get exporter for specified format.

        Args:
            format: Export format (csv, json, xml)

        Returns:
            Exporter instance

        Raises:
            ValueError: If format is not supported
        """
        if isinstance(format, str):
            try:
                format = ExportFormat(format.lower())
            except ValueError:
                raise ValueError(
                    f"Unsupported export format: {format}. "
                    f"Supported formats: {', '.join([f.value for f in ExportFormat])}"
                )

        return self._exporters[format]

    async def export(
        self,
        export_type: ExportType | str,
        format: ExportFormat | str,
        **kwargs
    ) -> bytes:
        """
        Export data in specified format.

        Args:
            export_type: Type of data to export
            format: Export format
            **kwargs: Additional arguments passed to exporter

        Returns:
            Exported data as bytes

        Raises:
            ValueError: If export_type or format is not supported
        """
        # Validate and convert export type
        if isinstance(export_type, str):
            try:
                export_type = ExportType(export_type.lower())
            except ValueError:
                raise ValueError(
                    f"Unsupported export type: {export_type}. "
                    f"Supported types: {', '.join([t.value for t in ExportType])}"
                )

        # Get appropriate exporter
        exporter = self.get_exporter(format)

        # Call appropriate export method
        if export_type == ExportType.ASSIGNMENTS:
            return await exporter.export_assignments(**kwargs)
        elif export_type == ExportType.SCHEDULE:
            return await exporter.export_schedule(**kwargs)
        elif export_type == ExportType.PEOPLE:
            return await exporter.export_people(**kwargs)
        elif export_type == ExportType.BLOCKS:
            return await exporter.export_blocks(**kwargs)
        elif export_type == ExportType.ANALYTICS:
            return await exporter.export_analytics(**kwargs)
        else:
            raise ValueError(f"Unknown export type: {export_type}")

    async def stream_export(
        self,
        export_type: ExportType | str,
        format: ExportFormat | str,
        **kwargs
    ) -> AsyncIterator[bytes]:
        """
        Stream export data in chunks.

        Args:
            export_type: Type of data to export
            format: Export format
            **kwargs: Additional arguments passed to exporter

        Yields:
            Chunks of exported data

        Raises:
            ValueError: If export_type or format is not supported
        """
        # Validate and convert export type
        if isinstance(export_type, str):
            try:
                export_type = ExportType(export_type.lower())
            except ValueError:
                raise ValueError(
                    f"Unsupported export type: {export_type}. "
                    f"Supported types: {', '.join([t.value for t in ExportType])}"
                )

        # Get appropriate exporter
        exporter = self.get_exporter(format)

        # Stream export
        async for chunk in exporter.stream_export(export_type.value, **kwargs):
            yield chunk

    def get_content_type(self, format: ExportFormat | str, compress: bool = False) -> str:
        """
        Get content type for export format.

        Args:
            format: Export format
            compress: Whether output is compressed

        Returns:
            MIME type string
        """
        exporter = self.get_exporter(format)
        return exporter.get_content_type(compress=compress)

    def get_filename(
        self,
        export_type: ExportType | str,
        format: ExportFormat | str,
        compress: bool = False,
        timestamp: bool = True
    ) -> str:
        """
        Generate filename for export.

        Args:
            export_type: Type of data being exported
            format: Export format
            compress: Whether output is compressed
            timestamp: Whether to include timestamp

        Returns:
            Filename string
        """
        # Validate and convert export type
        if isinstance(export_type, str):
            try:
                export_type = ExportType(export_type.lower())
            except ValueError:
                raise ValueError(f"Unsupported export type: {export_type}")

        exporter = self.get_exporter(format)
        return exporter.get_filename(
            base_name=export_type.value,
            compress=compress,
            timestamp=timestamp
        )

    @staticmethod
    def get_supported_formats() -> list[str]:
        """
        Get list of supported export formats.

        Returns:
            List of format names
        """
        return [f.value for f in ExportFormat]

    @staticmethod
    def get_supported_types() -> list[str]:
        """
        Get list of supported export types.

        Returns:
            List of export type names
        """
        return [t.value for t in ExportType]


class ScheduledExportConfig:
    """
    Configuration for scheduled exports.

    This can be used with Celery tasks to schedule regular exports.
    """

    def __init__(
        self,
        export_type: ExportType | str,
        format: ExportFormat | str,
        destination: str,
        schedule: str,
        compress: bool = True,
        **export_kwargs
    ):
        """
        Initialize scheduled export configuration.

        Args:
            export_type: Type of data to export
            format: Export format
            destination: Where to save exports (file path, S3 bucket, etc.)
            schedule: Cron schedule string (e.g., "0 0 * * *" for daily at midnight)
            compress: Whether to compress exports
            **export_kwargs: Additional arguments for export (filters, fields, etc.)
        """
        self.export_type = export_type
        self.format = format
        self.destination = destination
        self.schedule = schedule
        self.compress = compress
        self.export_kwargs = export_kwargs

    def to_dict(self) -> dict[str, Any]:
        """Convert config to dictionary."""
        return {
            "export_type": self.export_type,
            "format": self.format,
            "destination": self.destination,
            "schedule": self.schedule,
            "compress": self.compress,
            "export_kwargs": self.export_kwargs,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ScheduledExportConfig":
        """Create config from dictionary."""
        export_kwargs = data.pop("export_kwargs", {})
        return cls(**data, **export_kwargs)


async def export_assignments_csv(
    db: AsyncSession,
    start_date: date | None = None,
    end_date: date | None = None,
    compress: bool = False,
) -> bytes:
    """
    Convenience function to export assignments as CSV.

    Args:
        db: Database session
        start_date: Filter from this date
        end_date: Filter to this date
        compress: Whether to compress output

    Returns:
        CSV data as bytes
    """
    factory = ExportFactory(db)
    return await factory.export(
        ExportType.ASSIGNMENTS,
        ExportFormat.CSV,
        start_date=start_date,
        end_date=end_date,
        compress=compress,
    )


async def export_schedule_json(
    db: AsyncSession,
    start_date: date | None = None,
    end_date: date | None = None,
    compress: bool = False,
    pretty: bool = True,
) -> bytes:
    """
    Convenience function to export schedule as JSON.

    Args:
        db: Database session
        start_date: Filter from this date
        end_date: Filter to this date
        compress: Whether to compress output
        pretty: Whether to pretty-print JSON

    Returns:
        JSON data as bytes
    """
    factory = ExportFactory(db)
    return await factory.export(
        ExportType.SCHEDULE,
        ExportFormat.JSON,
        start_date=start_date,
        end_date=end_date,
        compress=compress,
        pretty=pretty,
    )


async def export_people_xml(
    db: AsyncSession,
    person_type: str | None = None,
    compress: bool = False,
    pretty: bool = True,
) -> bytes:
    """
    Convenience function to export people directory as XML.

    Args:
        db: Database session
        person_type: Filter by type ('resident' or 'faculty')
        compress: Whether to compress output
        pretty: Whether to pretty-print XML

    Returns:
        XML data as bytes
    """
    factory = ExportFactory(db)
    return await factory.export(
        ExportType.PEOPLE,
        ExportFormat.XML,
        person_type=person_type,
        compress=compress,
        pretty=pretty,
    )
