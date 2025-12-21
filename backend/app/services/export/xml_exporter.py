"""
XML export service.

Provides XML export functionality for schedules, assignments, people,
and analytics data with streaming support for large datasets.
"""
import gzip
import io
import xml.etree.ElementTree as ET
from datetime import date, datetime
from typing import Any, AsyncIterator
from xml.dom import minidom

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
    sanitize_for_export,
)


class XMLExporter:
    """XML export service with streaming and compression support."""

    def __init__(self, db: AsyncSession):
        """
        Initialize XML exporter.

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
        Export assignments to XML.

        Args:
            start_date: Filter assignments from this date
            end_date: Filter assignments to this date
            fields: List of fields to include (None = all)
            include_relations: Include related objects (block, person, rotation)
            compress: Whether to gzip compress the output
            pretty: Whether to pretty-print XML
            batch_size: Number of records to fetch per batch

        Returns:
            XML data as bytes (optionally compressed)
        """
        # Create root element
        root = ET.Element("export")
        metadata = ET.SubElement(root, "metadata")
        ET.SubElement(metadata, "export_type").text = "assignments"
        ET.SubElement(metadata, "exported_at").text = datetime.utcnow().isoformat()

        if start_date:
            ET.SubElement(metadata, "start_date").text = start_date.isoformat()
        if end_date:
            ET.SubElement(metadata, "end_date").text = end_date.isoformat()

        # Create data container
        data_elem = ET.SubElement(root, "data")
        count = 0
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
                formatted = format_assignment(a, fields=fields, include_relations=include_relations)
                assignment_elem = self._dict_to_xml(formatted, "assignment")
                data_elem.append(assignment_elem)
                count += 1

            offset += batch_size

        # Add count to metadata
        ET.SubElement(metadata, "total_count").text = str(count)

        # Convert to string
        xml_content = self._to_string(root, pretty=pretty)

        # Compress if requested
        if compress:
            return self._compress(xml_content)

        return xml_content.encode('utf-8')

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
        Export schedule to XML.

        Args:
            start_date: Filter schedule from this date
            end_date: Filter schedule to this date
            person_ids: Filter to specific people
            fields: List of fields to include (None = all)
            compress: Whether to gzip compress the output
            pretty: Whether to pretty-print XML
            nested: Whether to use nested structure or flat rows
            batch_size: Number of records to fetch per batch

        Returns:
            XML data as bytes (optionally compressed)
        """
        # Create root element
        root = ET.Element("export")
        metadata = ET.SubElement(root, "metadata")
        ET.SubElement(metadata, "export_type").text = "schedule"
        ET.SubElement(metadata, "exported_at").text = datetime.utcnow().isoformat()
        ET.SubElement(metadata, "format").text = "nested" if nested else "flat"

        if start_date:
            ET.SubElement(metadata, "start_date").text = start_date.isoformat()
        if end_date:
            ET.SubElement(metadata, "end_date").text = end_date.isoformat()

        # Create data container
        data_elem = ET.SubElement(root, "data")
        count = 0
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
                    formatted = format_assignment(a, fields=fields, include_relations=True)
                    row_elem = self._dict_to_xml(formatted, "assignment")
                else:
                    formatted = format_schedule_row(a, flat=True)
                    if fields:
                        formatted = {k: v for k, v in formatted.items() if k in fields}
                    row_elem = self._dict_to_xml(formatted, "row")

                data_elem.append(row_elem)
                count += 1

            offset += batch_size

        # Add count to metadata
        ET.SubElement(metadata, "total_count").text = str(count)

        # Convert to string
        xml_content = self._to_string(root, pretty=pretty)

        # Compress if requested
        if compress:
            return self._compress(xml_content)

        return xml_content.encode('utf-8')

    async def export_people(
        self,
        person_type: str | None = None,
        fields: list[str] | None = None,
        compress: bool = False,
        pretty: bool = False,
        batch_size: int = 1000,
    ) -> bytes:
        """
        Export people directory to XML.

        Args:
            person_type: Filter by type ('resident' or 'faculty')
            fields: List of fields to include (None = all)
            compress: Whether to gzip compress the output
            pretty: Whether to pretty-print XML
            batch_size: Number of records to fetch per batch

        Returns:
            XML data as bytes (optionally compressed)
        """
        # Create root element
        root = ET.Element("export")
        metadata = ET.SubElement(root, "metadata")
        ET.SubElement(metadata, "export_type").text = "people"
        ET.SubElement(metadata, "exported_at").text = datetime.utcnow().isoformat()

        if person_type:
            ET.SubElement(metadata, "person_type").text = person_type

        # Create data container
        data_elem = ET.SubElement(root, "data")
        count = 0
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
                person_elem = self._dict_to_xml(formatted, "person")
                data_elem.append(person_elem)
                count += 1

            offset += batch_size

        # Add count to metadata
        ET.SubElement(metadata, "total_count").text = str(count)

        # Convert to string
        xml_content = self._to_string(root, pretty=pretty)

        # Compress if requested
        if compress:
            return self._compress(xml_content)

        return xml_content.encode('utf-8')

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
        Export blocks to XML.

        Args:
            start_date: Filter blocks from this date
            end_date: Filter blocks to this date
            fields: List of fields to include (None = all)
            compress: Whether to gzip compress the output
            pretty: Whether to pretty-print XML
            batch_size: Number of records to fetch per batch

        Returns:
            XML data as bytes (optionally compressed)
        """
        # Create root element
        root = ET.Element("export")
        metadata = ET.SubElement(root, "metadata")
        ET.SubElement(metadata, "export_type").text = "blocks"
        ET.SubElement(metadata, "exported_at").text = datetime.utcnow().isoformat()

        if start_date:
            ET.SubElement(metadata, "start_date").text = start_date.isoformat()
        if end_date:
            ET.SubElement(metadata, "end_date").text = end_date.isoformat()

        # Create data container
        data_elem = ET.SubElement(root, "data")
        count = 0
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
                block_elem = self._dict_to_xml(formatted, "block")
                data_elem.append(block_elem)
                count += 1

            offset += batch_size

        # Add count to metadata
        ET.SubElement(metadata, "total_count").text = str(count)

        # Convert to string
        xml_content = self._to_string(root, pretty=pretty)

        # Compress if requested
        if compress:
            return self._compress(xml_content)

        return xml_content.encode('utf-8')

    async def export_analytics(
        self,
        metrics_data: list[dict[str, Any]],
        compress: bool = False,
        pretty: bool = False,
    ) -> bytes:
        """
        Export analytics data to XML.

        Args:
            metrics_data: List of dictionaries containing analytics metrics
            compress: Whether to gzip compress the output
            pretty: Whether to pretty-print XML

        Returns:
            XML data as bytes (optionally compressed)
        """
        # Create root element
        root = ET.Element("export")
        metadata = ET.SubElement(root, "metadata")
        ET.SubElement(metadata, "export_type").text = "analytics"
        ET.SubElement(metadata, "total_count").text = str(len(metrics_data))
        ET.SubElement(metadata, "exported_at").text = datetime.utcnow().isoformat()

        # Create data container
        data_elem = ET.SubElement(root, "data")

        for row in metrics_data:
            metric_elem = self._dict_to_xml(row, "metric")
            data_elem.append(metric_elem)

        # Convert to string
        xml_content = self._to_string(root, pretty=pretty)

        # Compress if requested
        if compress:
            return self._compress(xml_content)

        return xml_content.encode('utf-8')

    async def stream_export(
        self,
        export_type: str,
        **kwargs
    ) -> AsyncIterator[bytes]:
        """
        Stream export data in chunks (for large datasets).

        Args:
            export_type: Type of export ('assignments', 'schedule', 'people', 'blocks')
            **kwargs: Arguments passed to specific export method

        Yields:
            Chunks of XML data
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
            yield data[i:i + chunk_size]

    def _dict_to_xml(self, data: dict[str, Any], root_name: str) -> ET.Element:
        """
        Convert dictionary to XML element.

        Args:
            data: Dictionary to convert
            root_name: Name for root element

        Returns:
            XML element
        """
        root = ET.Element(root_name)

        for key, value in data.items():
            # Sanitize key to be valid XML element name
            safe_key = key.replace(" ", "_").replace("-", "_")

            elem = ET.SubElement(root, safe_key)

            if value is None:
                elem.set("null", "true")
            elif isinstance(value, dict):
                # Nested dict - recursively convert
                for k, v in value.items():
                    safe_k = k.replace(" ", "_").replace("-", "_")
                    sub_elem = ET.SubElement(elem, safe_k)
                    sub_elem.text = str(sanitize_for_export(v))
            elif isinstance(value, list):
                # List - create child elements
                for item in value:
                    item_elem = ET.SubElement(elem, "item")
                    if isinstance(item, dict):
                        # Nested dict in list
                        for k, v in item.items():
                            safe_k = k.replace(" ", "_").replace("-", "_")
                            sub_elem = ET.SubElement(item_elem, safe_k)
                            sub_elem.text = str(sanitize_for_export(v))
                    else:
                        item_elem.text = str(sanitize_for_export(item))
            else:
                elem.text = str(sanitize_for_export(value))

        return root

    def _to_string(self, root: ET.Element, pretty: bool = False) -> str:
        """
        Convert XML element to string.

        Args:
            root: Root XML element
            pretty: Whether to pretty-print

        Returns:
            XML string
        """
        if pretty:
            # Pretty print using minidom
            xml_str = ET.tostring(root, encoding='unicode')
            dom = minidom.parseString(xml_str)
            return dom.toprettyxml(indent="  ")
        else:
            return ET.tostring(root, encoding='unicode')

    def _compress(self, content: str) -> bytes:
        """
        Compress XML content with gzip.

        Args:
            content: XML content as string

        Returns:
            Compressed bytes
        """
        output = io.BytesIO()
        with gzip.GzipFile(fileobj=output, mode='wb') as gz:
            gz.write(content.encode('utf-8'))
        return output.getvalue()

    @staticmethod
    def get_content_type(compress: bool = False) -> str:
        """
        Get appropriate content type for XML export.

        Args:
            compress: Whether output is compressed

        Returns:
            MIME type string
        """
        if compress:
            return "application/gzip"
        return "application/xml"

    @staticmethod
    def get_filename(
        base_name: str,
        compress: bool = False,
        timestamp: bool = True
    ) -> str:
        """
        Generate filename for XML export.

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
            return f"{filename}.xml.gz"

        return f"{filename}.xml"
