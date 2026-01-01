"""
CSV export service.

Provides CSV export functionality for schedules, assignments, people,
and analytics data with streaming support for large datasets.
"""

import csv
import gzip
import io
from collections.abc import AsyncIterator
from datetime import date, datetime
from typing import Any, BinaryIO

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.assignment import Assignment
from app.models.block import Block
from app.models.person import Person
from app.services.export.formatters import (
    format_analytics_row,
    format_assignment,
    format_block,
    format_person,
    format_schedule_row,
    get_available_fields,
    sanitize_for_export,
)


class CSVExporter:
    """CSV export service with streaming and compression support."""

    def __init__(self, db: AsyncSession) -> None:
        """
        Initialize CSV exporter.

        Args:
            db: Async database session
        """
        self.db = db

    async def export_assignments(
        self,
        start_date: date | None = None,
        end_date: date | None = None,
        fields: list[str] | None = None,
        include_relations: bool = False,
        compress: bool = False,
        batch_size: int = 1000,
    ) -> bytes:
        """
        Export assignments to CSV.

        Args:
            start_date: Filter assignments from this date
            end_date: Filter assignments to this date
            fields: List of fields to include (None = all)
            include_relations: Include related objects (block, person, rotation)
            compress: Whether to gzip compress the output
            batch_size: Number of records to fetch per batch

        Returns:
            CSV data as bytes (optionally compressed)
        """
        output = io.StringIO()
        writer = None
        offset = 0

        while True:
            # Build query
            query = select(Assignment)

            # Add relations if requested
            if include_relations:
                query = query.options(
                    joinedload(Assignment.block),
                    joinedload(Assignment.person),
                    joinedload(Assignment.rotation_template),
                )

            # Add date filters
            if start_date or end_date:
                query = query.join(Block)
                if start_date:
                    query = query.filter(Block.date >= start_date)
                if end_date:
                    query = query.filter(Block.date <= end_date)

            # Add pagination
            query = query.offset(offset).limit(batch_size)

            # Execute query
            result = await self.db.execute(query)
            assignments = result.unique().scalars().all()

            if not assignments:
                break

            # Format assignments
            rows = [
                format_assignment(a, fields=fields, include_relations=include_relations)
                for a in assignments
            ]

            # Write header on first batch
            if writer is None:
                if rows:
                    fieldnames = list(rows[0].keys())
                    writer = csv.DictWriter(output, fieldnames=fieldnames)
                    writer.writeheader()

            # Write rows
            for row in rows:
                # Sanitize values for CSV
                sanitized = {k: sanitize_for_export(v) for k, v in row.items()}
                writer.writerow(sanitized)

            offset += batch_size

        # Get CSV content
        csv_content = output.getvalue()

        # Compress if requested
        if compress:
            return self._compress(csv_content)

        return csv_content.encode("utf-8")

    async def export_schedule(
        self,
        start_date: date | None = None,
        end_date: date | None = None,
        person_ids: list[str] | None = None,
        fields: list[str] | None = None,
        compress: bool = False,
        batch_size: int = 1000,
    ) -> bytes:
        """
        Export schedule as flat CSV (one row per assignment with all related data).

        Args:
            start_date: Filter schedule from this date
            end_date: Filter schedule to this date
            person_ids: Filter to specific people
            fields: List of fields to include (None = all)
            compress: Whether to gzip compress the output
            batch_size: Number of records to fetch per batch

        Returns:
            CSV data as bytes (optionally compressed)
        """
        output = io.StringIO()
        writer = None
        offset = 0

        while True:
            # Build query with all relations
            query = select(Assignment).options(
                joinedload(Assignment.block),
                joinedload(Assignment.person),
                joinedload(Assignment.rotation_template),
            )

            # Add filters
            if start_date or end_date or person_ids:
                if start_date or end_date:
                    query = query.join(Block)
                    if start_date:
                        query = query.filter(Block.date >= start_date)
                    if end_date:
                        query = query.filter(Block.date <= end_date)

                if person_ids:
                    query = query.filter(Assignment.person_id.in_(person_ids))

            # Add pagination
            query = query.offset(offset).limit(batch_size)

            # Execute query
            result = await self.db.execute(query)
            assignments = result.unique().scalars().all()

            if not assignments:
                break

            # Format as flat rows
            rows = [format_schedule_row(a, flat=True) for a in assignments]

            # Filter fields if specified
            if fields:
                rows = [{k: v for k, v in row.items() if k in fields} for row in rows]

            # Write header on first batch
            if writer is None:
                if rows:
                    fieldnames = list(rows[0].keys())
                    writer = csv.DictWriter(output, fieldnames=fieldnames)
                    writer.writeheader()

            # Write rows
            for row in rows:
                sanitized = {k: sanitize_for_export(v) for k, v in row.items()}
                writer.writerow(sanitized)

            offset += batch_size

        # Get CSV content
        csv_content = output.getvalue()

        # Compress if requested
        if compress:
            return self._compress(csv_content)

        return csv_content.encode("utf-8")

    async def export_people(
        self,
        person_type: str | None = None,
        fields: list[str] | None = None,
        compress: bool = False,
        batch_size: int = 1000,
    ) -> bytes:
        """
        Export people directory to CSV.

        Args:
            person_type: Filter by type ('resident' or 'faculty')
            fields: List of fields to include (None = all)
            compress: Whether to gzip compress the output
            batch_size: Number of records to fetch per batch

        Returns:
            CSV data as bytes (optionally compressed)
        """
        output = io.StringIO()
        writer = None
        offset = 0

        while True:
            # Build query
            query = select(Person)

            # Add filters
            if person_type:
                query = query.filter(Person.type == person_type)

            # Add pagination
            query = query.offset(offset).limit(batch_size)

            # Execute query
            result = await self.db.execute(query)
            people = result.scalars().all()

            if not people:
                break

            # Format people
            rows = [format_person(p, fields=fields) for p in people]

            # Write header on first batch
            if writer is None:
                if rows:
                    fieldnames = list(rows[0].keys())
                    writer = csv.DictWriter(output, fieldnames=fieldnames)
                    writer.writeheader()

            # Write rows
            for row in rows:
                sanitized = {k: sanitize_for_export(v) for k, v in row.items()}
                writer.writerow(sanitized)

            offset += batch_size

        # Get CSV content
        csv_content = output.getvalue()

        # Compress if requested
        if compress:
            return self._compress(csv_content)

        return csv_content.encode("utf-8")

    async def export_blocks(
        self,
        start_date: date | None = None,
        end_date: date | None = None,
        fields: list[str] | None = None,
        compress: bool = False,
        batch_size: int = 1000,
    ) -> bytes:
        """
        Export blocks to CSV.

        Args:
            start_date: Filter blocks from this date
            end_date: Filter blocks to this date
            fields: List of fields to include (None = all)
            compress: Whether to gzip compress the output
            batch_size: Number of records to fetch per batch

        Returns:
            CSV data as bytes (optionally compressed)
        """
        output = io.StringIO()
        writer = None
        offset = 0

        while True:
            # Build query
            query = select(Block)

            # Add filters
            if start_date:
                query = query.filter(Block.date >= start_date)
            if end_date:
                query = query.filter(Block.date <= end_date)

            # Add pagination
            query = query.offset(offset).limit(batch_size)

            # Execute query
            result = await self.db.execute(query)
            blocks = result.scalars().all()

            if not blocks:
                break

            # Format blocks
            rows = [format_block(b, fields=fields) for b in blocks]

            # Write header on first batch
            if writer is None:
                if rows:
                    fieldnames = list(rows[0].keys())
                    writer = csv.DictWriter(output, fieldnames=fieldnames)
                    writer.writeheader()

            # Write rows
            for row in rows:
                sanitized = {k: sanitize_for_export(v) for k, v in row.items()}
                writer.writerow(sanitized)

            offset += batch_size

        # Get CSV content
        csv_content = output.getvalue()

        # Compress if requested
        if compress:
            return self._compress(csv_content)

        return csv_content.encode("utf-8")

    async def export_analytics(
        self,
        metrics_data: list[dict[str, Any]],
        compress: bool = False,
    ) -> bytes:
        """
        Export analytics data to CSV.

        Args:
            metrics_data: List of dictionaries containing analytics metrics
            compress: Whether to gzip compress the output

        Returns:
            CSV data as bytes (optionally compressed)
        """
        if not metrics_data:
            return b""

        output = io.StringIO()

        # Get all unique field names from all metrics
        fieldnames = set()
        for row in metrics_data:
            fieldnames.update(row.keys())

        fieldnames = sorted(fieldnames)

        # Write CSV
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()

        for row in metrics_data:
            sanitized = {k: sanitize_for_export(v) for k, v in row.items()}
            writer.writerow(sanitized)

        # Get CSV content
        csv_content = output.getvalue()

        # Compress if requested
        if compress:
            return self._compress(csv_content)

        return csv_content.encode("utf-8")

    async def stream_export(self, export_type: str, **kwargs) -> AsyncIterator[bytes]:
        """
        Stream export data in chunks (for large datasets).

        Args:
            export_type: Type of export ('assignments', 'schedule', 'people', 'blocks')
            **kwargs: Arguments passed to specific export method

        Yields:
            Chunks of CSV data
        """
        # This is a simplified streaming implementation
        # In production, you might want to yield smaller chunks
        if export_type == "assignments":
            data = await self.export_assignments(**kwargs)
        elif export_type == "schedule":
            data = await self.export_schedule(**kwargs)
        elif export_type == "people":
            data = await self.export_people(**kwargs)
        elif export_type == "blocks":
            data = await self.export_blocks(**kwargs)
        else:
            raise ValueError(f"Unknown export type: {export_type}")

        # Yield in chunks
        chunk_size = 8192  # 8KB chunks
        for i in range(0, len(data), chunk_size):
            yield data[i : i + chunk_size]

    def _compress(self, content: str) -> bytes:
        """
        Compress CSV content with gzip.

        Args:
            content: CSV content as string

        Returns:
            Compressed bytes
        """
        output = io.BytesIO()
        with gzip.GzipFile(fileobj=output, mode="wb") as gz:
            gz.write(content.encode("utf-8"))
        return output.getvalue()

    @staticmethod
    def get_content_type(compress: bool = False) -> str:
        """
        Get appropriate content type for CSV export.

        Args:
            compress: Whether output is compressed

        Returns:
            MIME type string
        """
        if compress:
            return "application/gzip"
        return "text/csv"

    @staticmethod
    def get_filename(
        base_name: str, compress: bool = False, timestamp: bool = True
    ) -> str:
        """
        Generate filename for CSV export.

        Args:
            base_name: Base name for file (e.g., 'schedule', 'people')
            compress: Whether output is compressed
            timestamp: Whether to include timestamp in filename

        Returns:
            Filename string
        """
        filename = base_name

        if timestamp:
            ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            filename = f"{base_name}_{ts}"

        if compress:
            return f"{filename}.csv.gz"

        return f"{filename}.csv"
