"""
JSON export service.

Provides JSON export functionality for schedules, assignments, people,
and analytics data with streaming support for large datasets.
"""

import gzip
import io
import json
from collections.abc import AsyncIterator
from datetime import date, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.assignment import Assignment
from app.models.block import Block
from app.models.person import Person
from app.services.export.formatters import (
    format_assignment,
    format_block,
    format_person,
    format_schedule_row,
)


class JSONEncoder(json.JSONEncoder):
    """Custom JSON encoder for database models."""

    def default(self, obj) -> str:
        """Handle special types."""
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        if isinstance(obj, UUID):
            return str(obj)
        return super().default(obj)


class JSONExporter:
    """JSON export service with streaming and compression support."""

    def __init__(self, db: AsyncSession) -> None:
        """
        Initialize JSON exporter.

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
        pretty: bool = False,
        batch_size: int = 1000,
    ) -> bytes:
        """
        Export assignments to JSON.

        Args:
            start_date: Filter assignments from this date
            end_date: Filter assignments to this date
            fields: List of fields to include (None = all)
            include_relations: Include related objects (block, person, rotation)
            compress: Whether to gzip compress the output
            pretty: Whether to pretty-print JSON
            batch_size: Number of records to fetch per batch

        Returns:
            JSON data as bytes (optionally compressed)
        """
        all_assignments = []
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
            for a in assignments:
                formatted = format_assignment(
                    a, fields=fields, include_relations=include_relations
                )
                all_assignments.append(formatted)

            offset += batch_size

        # Create JSON structure
        output = {
            "data": all_assignments,
            "metadata": {
                "export_type": "assignments",
                "total_count": len(all_assignments),
                "filters": {
                    "start_date": start_date.isoformat() if start_date else None,
                    "end_date": end_date.isoformat() if end_date else None,
                },
                "exported_at": datetime.utcnow().isoformat(),
            },
        }

        # Serialize to JSON
        if pretty:
            json_content = json.dumps(output, cls=JSONEncoder, indent=2)
        else:
            json_content = json.dumps(output, cls=JSONEncoder)

        # Compress if requested
        if compress:
            return self._compress(json_content)

        return json_content.encode("utf-8")

    async def export_schedule(
        self,
        start_date: date | None = None,
        end_date: date | None = None,
        person_ids: list[str] | None = None,
        fields: list[str] | None = None,
        compress: bool = False,
        pretty: bool = False,
        nested: bool = True,
        batch_size: int = 1000,
    ) -> bytes:
        """
        Export schedule to JSON.

        Args:
            start_date: Filter schedule from this date
            end_date: Filter schedule to this date
            person_ids: Filter to specific people
            fields: List of fields to include (None = all)
            compress: Whether to gzip compress the output
            pretty: Whether to pretty-print JSON
            nested: Whether to use nested structure or flat rows
            batch_size: Number of records to fetch per batch

        Returns:
            JSON data as bytes (optionally compressed)
        """
        all_rows = []
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

            # Format rows
            for a in assignments:
                if nested:
                    formatted = format_assignment(
                        a, fields=fields, include_relations=True
                    )
                else:
                    formatted = format_schedule_row(a, flat=True)
                    if fields:
                        formatted = {k: v for k, v in formatted.items() if k in fields}
                all_rows.append(formatted)

            offset += batch_size

        # Create JSON structure
        output = {
            "data": all_rows,
            "metadata": {
                "export_type": "schedule",
                "total_count": len(all_rows),
                "filters": {
                    "start_date": start_date.isoformat() if start_date else None,
                    "end_date": end_date.isoformat() if end_date else None,
                    "person_ids": person_ids,
                },
                "format": "nested" if nested else "flat",
                "exported_at": datetime.utcnow().isoformat(),
            },
        }

        # Serialize to JSON
        if pretty:
            json_content = json.dumps(output, cls=JSONEncoder, indent=2)
        else:
            json_content = json.dumps(output, cls=JSONEncoder)

        # Compress if requested
        if compress:
            return self._compress(json_content)

        return json_content.encode("utf-8")

    async def export_people(
        self,
        person_type: str | None = None,
        fields: list[str] | None = None,
        compress: bool = False,
        pretty: bool = False,
        batch_size: int = 1000,
    ) -> bytes:
        """
        Export people directory to JSON.

        Args:
            person_type: Filter by type ('resident' or 'faculty')
            fields: List of fields to include (None = all)
            compress: Whether to gzip compress the output
            pretty: Whether to pretty-print JSON
            batch_size: Number of records to fetch per batch

        Returns:
            JSON data as bytes (optionally compressed)
        """
        all_people = []
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
            for p in people:
                formatted = format_person(p, fields=fields)
                all_people.append(formatted)

            offset += batch_size

        # Create JSON structure
        output = {
            "data": all_people,
            "metadata": {
                "export_type": "people",
                "total_count": len(all_people),
                "filters": {
                    "person_type": person_type,
                },
                "exported_at": datetime.utcnow().isoformat(),
            },
        }

        # Serialize to JSON
        if pretty:
            json_content = json.dumps(output, cls=JSONEncoder, indent=2)
        else:
            json_content = json.dumps(output, cls=JSONEncoder)

        # Compress if requested
        if compress:
            return self._compress(json_content)

        return json_content.encode("utf-8")

    async def export_blocks(
        self,
        start_date: date | None = None,
        end_date: date | None = None,
        fields: list[str] | None = None,
        compress: bool = False,
        pretty: bool = False,
        batch_size: int = 1000,
    ) -> bytes:
        """
        Export blocks to JSON.

        Args:
            start_date: Filter blocks from this date
            end_date: Filter blocks to this date
            fields: List of fields to include (None = all)
            compress: Whether to gzip compress the output
            pretty: Whether to pretty-print JSON
            batch_size: Number of records to fetch per batch

        Returns:
            JSON data as bytes (optionally compressed)
        """
        all_blocks = []
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
            for b in blocks:
                formatted = format_block(b, fields=fields)
                all_blocks.append(formatted)

            offset += batch_size

        # Create JSON structure
        output = {
            "data": all_blocks,
            "metadata": {
                "export_type": "blocks",
                "total_count": len(all_blocks),
                "filters": {
                    "start_date": start_date.isoformat() if start_date else None,
                    "end_date": end_date.isoformat() if end_date else None,
                },
                "exported_at": datetime.utcnow().isoformat(),
            },
        }

        # Serialize to JSON
        if pretty:
            json_content = json.dumps(output, cls=JSONEncoder, indent=2)
        else:
            json_content = json.dumps(output, cls=JSONEncoder)

        # Compress if requested
        if compress:
            return self._compress(json_content)

        return json_content.encode("utf-8")

    async def export_analytics(
        self,
        metrics_data: list[dict[str, Any]],
        compress: bool = False,
        pretty: bool = False,
    ) -> bytes:
        """
        Export analytics data to JSON.

        Args:
            metrics_data: List of dictionaries containing analytics metrics
            compress: Whether to gzip compress the output
            pretty: Whether to pretty-print JSON

        Returns:
            JSON data as bytes (optionally compressed)
        """
        # Create JSON structure
        output = {
            "data": metrics_data,
            "metadata": {
                "export_type": "analytics",
                "total_count": len(metrics_data),
                "exported_at": datetime.utcnow().isoformat(),
            },
        }

        # Serialize to JSON
        if pretty:
            json_content = json.dumps(output, cls=JSONEncoder, indent=2)
        else:
            json_content = json.dumps(output, cls=JSONEncoder)

        # Compress if requested
        if compress:
            return self._compress(json_content)

        return json_content.encode("utf-8")

    async def stream_export(self, export_type: str, **kwargs) -> AsyncIterator[bytes]:
        """
        Stream export data in chunks (for large datasets).

        Args:
            export_type: Type of export ('assignments', 'schedule', 'people', 'blocks')
            **kwargs: Arguments passed to specific export method

        Yields:
            Chunks of JSON data
        """
        # This is a simplified streaming implementation
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
        Compress JSON content with gzip.

        Args:
            content: JSON content as string

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
        Get appropriate content type for JSON export.

        Args:
            compress: Whether output is compressed

        Returns:
            MIME type string
        """
        if compress:
            return "application/gzip"
        return "application/json"

    @staticmethod
    def get_filename(
        base_name: str, compress: bool = False, timestamp: bool = True
    ) -> str:
        """
        Generate filename for JSON export.

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
            return f"{filename}.json.gz"

        return f"{filename}.json"
