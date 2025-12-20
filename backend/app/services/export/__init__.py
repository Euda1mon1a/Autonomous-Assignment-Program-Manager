"""
Export services package.

Provides data export functionality in multiple formats (CSV, JSON, XML)
with support for streaming, compression, and scheduled exports.

Examples:
    Basic usage with factory:

    >>> from app.services.export import ExportFactory, ExportFormat, ExportType
    >>> from app.db.session import AsyncSessionLocal
    >>>
    >>> async with AsyncSessionLocal() as db:
    ...     factory = ExportFactory(db)
    ...     data = await factory.export(
    ...         export_type=ExportType.SCHEDULE,
    ...         format=ExportFormat.CSV,
    ...         start_date=date(2024, 1, 1),
    ...         end_date=date(2024, 12, 31),
    ...         compress=True
    ...     )

    Using specific exporters:

    >>> from app.services.export import CSVExporter
    >>>
    >>> async with AsyncSessionLocal() as db:
    ...     exporter = CSVExporter(db)
    ...     csv_data = await exporter.export_assignments(
    ...         start_date=date(2024, 1, 1),
    ...         compress=False
    ...     )

    Convenience functions:

    >>> from app.services.export import export_schedule_json
    >>>
    >>> async with AsyncSessionLocal() as db:
    ...     json_data = await export_schedule_json(
    ...         db,
    ...         start_date=date(2024, 1, 1),
    ...         pretty=True
    ...     )

Features:
    - Multiple export formats: CSV, JSON, XML
    - Streaming support for large datasets
    - Gzip compression option
    - Custom field selection
    - Date range filtering
    - Person filtering
    - Batch processing for memory efficiency
    - Scheduled export configuration
"""
from app.services.export.csv_exporter import CSVExporter
from app.services.export.export_factory import (
    ExportFactory,
    ExportFormat,
    ExportType,
    ScheduledExportConfig,
    export_assignments_csv,
    export_people_xml,
    export_schedule_json,
)
from app.services.export.json_exporter import JSONExporter
from app.services.export.xml_exporter import XMLExporter

__all__ = [
    # Exporters
    "CSVExporter",
    "JSONExporter",
    "XMLExporter",
    # Factory and enums
    "ExportFactory",
    "ExportFormat",
    "ExportType",
    # Config
    "ScheduledExportConfig",
    # Convenience functions
    "export_assignments_csv",
    "export_schedule_json",
    "export_people_xml",
]
