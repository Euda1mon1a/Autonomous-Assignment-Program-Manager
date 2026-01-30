"""
Block Schedule Export Service.

Full pipeline: DB → XML → xlsx

This service connects the database to the ROSETTA-validated export pipeline:
1. Query BlockAssignments from DB for a specific block
2. Convert to schedule_xml_exporter format
3. Generate validated XML
4. Convert XML to xlsx using template

The XML serves as the validation checkpoint - if XML matches ROSETTA patterns,
the xlsx output will be correct.
"""

from datetime import date, timedelta
from io import BytesIO
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.logging import get_logger
from app.models.assignment import Assignment
from app.models.block import Block
from app.models.block_assignment import BlockAssignment
from app.models.call_assignment import CallAssignment
from app.models.person import Person
from app.models.rotation_template import RotationTemplate
from app.services.schedule_xml_exporter import ScheduleXMLExporter
from app.services.call_override_service import CallOverrideService
from app.services.xml_to_xlsx_converter import XMLToXlsxConverter
from app.utils.academic_blocks import get_block_dates
from app.utils.rosetta_xml_validator import compare_xml, get_mismatch_summary

logger = get_logger(__name__)

# Path to ROSETTA XML ground truth (generated from xlsx)
# In container: /app/app/services/... → /app/docs/scheduling/...
ROSETTA_XML_PATH = (
    Path(__file__).parent.parent.parent  # app/services → app (backend root)
    / "docs"
    / "scheduling"
    / "Block10_ROSETTA_CORRECT.xml"
)


class BlockScheduleExportService:
    """
    Full pipeline service: DB → XML → xlsx.

    Uses ROSETTA-validated XML exporter to ensure correct rotation patterns,
    then converts to xlsx format.
    """

    def __init__(
        self,
        session: AsyncSession,
        template_path: Path | str | None = None,
    ) -> None:
        self.session = session
        self.template_path = template_path

    async def export_block(
        self,
        block_number: int,
        academic_year: int,
        output_path: Path | str | None = None,
        return_xml: bool = False,
    ) -> bytes | tuple[bytes, str]:
        """
        Export a block schedule from DB to xlsx.

        Args:
            block_number: Block number (1-13)
            academic_year: Academic year (e.g., 2025 for AY 2025-2026)
            output_path: Optional path to save xlsx
            return_xml: If True, also return XML string

        Returns:
            xlsx bytes, or tuple of (xlsx bytes, xml string) if return_xml=True
        """
        # Get block dates
        block_dates = get_block_dates(block_number, academic_year)
        logger.info(
            f"Exporting Block {block_number} ({academic_year}): "
            f"{block_dates.start_date} to {block_dates.end_date}"
        )

        # Query assignments
        assignments = await self._query_assignments(block_number, academic_year)
        logger.info(f"Found {len(assignments)} block assignments")

        # Convert to XML exporter format
        residents = self._convert_to_resident_list(assignments)
        logger.info(f"Converted to {len(residents)} resident records")

        # Generate XML
        exporter = ScheduleXMLExporter(
            block_start=block_dates.start_date,
            block_end=block_dates.end_date,
        )
        xml_string = exporter.export(residents)
        logger.info("Generated XML schedule")

        # Validate XML against ROSETTA ground truth (Block 10 only)
        if block_number == 10:
            validation_mismatches = self._validate_xml_against_rosetta(xml_string)
            if validation_mismatches:
                summary = get_mismatch_summary(validation_mismatches)
                logger.warning(f"XML validation: {summary['total']} mismatches found")
                for m in summary["sample_mismatches"]:
                    logger.warning(f"  - {m}")
            else:
                logger.info("XML validation: PASSED (matches ROSETTA)")

                # Convert XML to xlsx
        converter = XMLToXlsxConverter(template_path=self.template_path)
        xlsx_bytes = converter.convert_from_string(xml_string, output_path)
        logger.info(f"Generated xlsx ({len(xlsx_bytes)} bytes)")

        if return_xml:
            return xlsx_bytes, xml_string
        return xlsx_bytes

    async def export_block_xml_only(
        self,
        block_number: int,
        academic_year: int,
        output_path: Path | str | None = None,
    ) -> str:
        """
        Export a block schedule to XML only (for validation).

        Args:
            block_number: Block number (1-13)
            academic_year: Academic year
            output_path: Optional path to save XML

        Returns:
            XML string
        """
        block_dates = get_block_dates(block_number, academic_year)
        assignments = await self._query_assignments(block_number, academic_year)
        residents = self._convert_to_resident_list(assignments)

        exporter = ScheduleXMLExporter(
            block_start=block_dates.start_date,
            block_end=block_dates.end_date,
        )
        xml_string = exporter.export(residents)

        if output_path:
            Path(output_path).write_text(xml_string)
            logger.info(f"Saved XML to {output_path}")

        return xml_string

    async def export_block_full(
        self,
        block_number: int,
        academic_year: int,
        output_path: Path | str | None = None,
        return_xml: bool = False,
    ) -> bytes | tuple[bytes, str]:
        """
        Export full block schedule with residents, faculty, and call from DB.

        Args:
            block_number: Block number (1-13)
            academic_year: Academic year
            output_path: Optional path to save xlsx
            return_xml: If True, also return XML string

        Returns:
            xlsx bytes, or tuple of (xlsx bytes, xml string) if return_xml=True
        """
        block_dates = get_block_dates(block_number, academic_year)
        start_date = block_dates.start_date
        end_date = block_dates.end_date

        logger.info(f"Exporting full Block {block_number}: {start_date} to {end_date}")

        # Query all data from DB
        assignments = await self._query_assignments(block_number, academic_year)
        residents = self._convert_to_resident_list(assignments)
        faculty_schedules = await self._query_faculty_assignments(start_date, end_date)
        call_assignments = await self._query_call_assignments(start_date, end_date)

        logger.info(
            f"Residents: {len(residents)}, Faculty: {len(faculty_schedules)}, Calls: {len(call_assignments)}"
        )

        # Pre-export validation (warn only, don't block)
        validation_warnings = self._validate_export_data(
            residents, faculty_schedules, call_assignments, start_date, end_date
        )
        for warning in validation_warnings:
            logger.warning(f"EXPORT VALIDATION: {warning}")

        if validation_warnings:
            logger.warning(
                f"Found {len(validation_warnings)} validation warnings (export continues)"
            )

            # Generate XML with faculty from DB
        xml_string = self._generate_full_xml(
            start_date, end_date, residents, faculty_schedules, call_assignments
        )

        # Convert XML to xlsx
        converter = XMLToXlsxConverter(template_path=self.template_path)
        xlsx_bytes = converter.convert_from_string(xml_string, output_path)
        logger.info(f"Generated xlsx ({len(xlsx_bytes)} bytes)")

        if return_xml:
            return xlsx_bytes, xml_string
        return xlsx_bytes

    def _generate_full_xml(
        self,
        start_date: date,
        end_date: date,
        residents: list[dict[str, Any]],
        faculty_schedules: dict[str, dict[date, dict[str, str]]],
        call_assignments: list[dict[str, Any]],
    ) -> str:
        """Generate XML with residents, faculty (from DB), and call."""
        from xml.etree.ElementTree import Element, SubElement, tostring
        from xml.dom import minidom

        root = Element("schedule")
        root.set("block_start", start_date.isoformat())
        root.set("block_end", end_date.isoformat())

        # Call section
        if call_assignments:
            call_elem = SubElement(root, "call")
            for ca in sorted(call_assignments, key=lambda x: x["date"]):
                night_elem = SubElement(call_elem, "night")
                night_elem.set("date", ca["date"].isoformat())
                night_elem.set("staff", ca.get("staff_name", ""))
                night_elem.set("resident", ca.get("resident_name", ""))

                # Residents section (use exporter for patterns)
        exporter = ScheduleXMLExporter(start_date, end_date)
        residents_elem = SubElement(root, "residents")
        for resident in residents:
            exporter._add_resident(residents_elem, resident)

            # Faculty section (from DB assignments)
        if faculty_schedules:
            faculty_elem = SubElement(root, "faculty")
            for name, schedule in sorted(faculty_schedules.items()):
                person_elem = SubElement(faculty_elem, "person")
                person_elem.set("name", name)

                current = start_date
                while current <= end_date:
                    day_data = schedule.get(current, {"am": "", "pm": ""})
                    day_elem = SubElement(person_elem, "day")
                    day_elem.set("date", current.isoformat())
                    day_elem.set("weekday", current.strftime("%a"))
                    day_elem.set("am", day_data.get("am", ""))
                    day_elem.set("pm", day_data.get("pm", ""))
                    current += timedelta(days=1)

        xml_str = tostring(root, encoding="unicode")
        return minidom.parseString(xml_str).toprettyxml(indent="  ")

    async def _query_assignments(
        self,
        block_number: int,
        academic_year: int,
    ) -> list[BlockAssignment]:
        """Query block assignments with eager loading."""
        stmt = (
            select(BlockAssignment)
            .options(
                selectinload(BlockAssignment.resident),
                selectinload(BlockAssignment.rotation_template),
                selectinload(BlockAssignment.secondary_rotation_template),
            )
            .where(BlockAssignment.block_number == block_number)
            .where(BlockAssignment.academic_year == academic_year)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def _query_faculty_assignments(
        self,
        start_date: date,
        end_date: date,
    ) -> dict[str, dict[date, dict[str, str]]]:
        """
        Query faculty assignments from DB and format for XML export.

        Returns:
            Dict mapping faculty name to {date: {am: code, pm: code}}
        """
        stmt = (
            select(Assignment)
            .join(Block)
            .join(Person)
            .join(RotationTemplate)
            .where(Block.date >= start_date)
            .where(Block.date <= end_date)
            .where(Person.type == "faculty")
            .options(
                selectinload(Assignment.block),
                selectinload(Assignment.person),
                selectinload(Assignment.rotation_template),
            )
        )
        result = await self.session.execute(stmt)
        assignments = result.scalars().all()

        # Build faculty schedule dict
        faculty_schedules: dict[str, dict[date, dict[str, str]]] = {}
        for a in assignments:
            name = self._convert_name_format(a.person.name)
            if name not in faculty_schedules:
                faculty_schedules[name] = {}

            block_date = a.block.date
            if block_date not in faculty_schedules[name]:
                faculty_schedules[name][block_date] = {"am": "", "pm": ""}

                # Use display_abbreviation (clean codes like "C", "GME", "FMIT")
            abbrev = (
                a.rotation_template.display_abbreviation
                or a.rotation_template.abbreviation
                or ""
            )

            time_of_day = a.block.time_of_day.lower()
            faculty_schedules[name][block_date][time_of_day] = abbrev

        logger.info(f"Queried {len(faculty_schedules)} faculty schedules from DB")
        return faculty_schedules

    async def _query_call_assignments(
        self,
        start_date: date,
        end_date: date,
    ) -> list[dict[str, Any]]:
        """
        Query call assignments from DB.

        Returns:
            List of dicts with date, staff_name, resident_name
        """
        stmt = (
            select(CallAssignment)
            .join(Person)
            .where(CallAssignment.date >= start_date)
            .where(CallAssignment.date <= end_date)
            .options(selectinload(CallAssignment.person))
        )
        result = await self.session.execute(stmt)
        call_assignments = list(result.scalars().all())

        override_service = CallOverrideService(self.session)
        call_assignments = await override_service.apply_overrides(call_assignments)

        call_list = []
        for ca in call_assignments:
            # Use last name only for call display (cleaner in template)
            full_name = self._convert_name_format(ca.person.name)
            last_name = full_name.split(",")[0] if "," in full_name else full_name
            call_list.append(
                {
                    "date": ca.date,
                    "staff_name": last_name,
                    "resident_name": "",  # TODO: Add resident call if tracked
                }
            )

        logger.info(f"Queried {len(call_list)} call assignments from DB")
        return call_list

    def _convert_to_resident_list(
        self,
        assignments: list[BlockAssignment],
    ) -> list[dict[str, Any]]:
        """
        Convert BlockAssignments to XML exporter format.

        XML exporter expects:
            - name: "Last, First"
            - pgy: 1, 2, or 3
            - rotation1: Primary rotation code
            - rotation2: Secondary rotation code (optional)
        """
        residents = []
        for assignment in assignments:
            if not assignment.resident:
                continue

                # Get rotation codes
            rotation1 = ""
            rotation2 = None

            if assignment.rotation_template:
                rotation1 = self._get_rotation_code(assignment.rotation_template)

            if assignment.secondary_rotation_template:
                rotation2 = self._get_rotation_code(
                    assignment.secondary_rotation_template
                )

                # Convert name to "Last, First" format
            name = self._convert_name_format(assignment.resident.name)

            residents.append(
                {
                    "name": name,
                    "pgy": assignment.resident.pgy_level or 1,
                    "rotation1": rotation1,
                    "rotation2": rotation2,
                }
            )

        return residents

    def _get_rotation_code(self, rotation_template) -> str:
        """
        Get standardized rotation code for XML exporter.

        Uses display_abbreviation (clean codes like "FMIT", "C", "NF")
        instead of internal abbreviations ("FMIT-R", "C-AM", "NF-PM").
        """
        if not rotation_template:
            return ""

            # Use display_abbreviation first (clean codes)
            # Fall back to abbreviation if display_abbreviation not set
        return (
            rotation_template.display_abbreviation
            or rotation_template.abbreviation
            or ""
        )

    def _convert_name_format(self, name: str) -> str:
        """
        Convert name to "Last, First" format.

        DB may store as "First Last" - convert to template format.
        """
        if not name:
            return ""

        name = name.strip()

        # Already in "Last, First" format
        if ", " in name:
            return name

            # Convert "First Last" to "Last, First"
        parts = name.split()
        if len(parts) >= 2:
            # Assume last word is last name
            first_names = " ".join(parts[:-1])
            last_name = parts[-1]
            return f"{last_name}, {first_names}"

        return name

    def _validate_xml_against_rosetta(self, xml_string: str) -> list[str]:
        """
        Compare generated XML against ROSETTA XML ground truth.

        This is the validation checkpoint in the "central dogma" pipeline.
        Returns list of mismatches (empty = valid).
        """
        if not ROSETTA_XML_PATH.exists():
            logger.warning(
                f"ROSETTA XML not found at {ROSETTA_XML_PATH}, skipping validation. "
                "Generate with: python -c 'from app.utils.rosetta_parser import save_rosetta_xml; save_rosetta_xml()'"
            )
            return []

        return compare_xml(ROSETTA_XML_PATH, xml_string)

    def _validate_export_data(
        self,
        residents: list[dict],
        faculty_schedules: dict[str, dict[date, dict[str, str]]],
        call_assignments: list[dict],
        start_date: date,
        end_date: date,
    ) -> list[str]:
        """
        Pre-export validation - warn only, don't block.

        Checks:
        1. Internal abbreviations (should use display codes)
        2. Call coverage gaps (expect 20 Sun-Thu nights)
        3. Physical clinic cap (≤6 providers per slot)
        """
        warnings = []

        # Check 1: Internal abbreviations
        internal_patterns = ["-R", "-AM", "-PM"]
        for r in residents:
            rot1 = r.get("rotation1", "")
            rot2 = r.get("rotation2", "")
            for rot in [rot1, rot2]:
                if rot and any(rot.endswith(p) for p in internal_patterns):
                    warnings.append(
                        f"Internal code '{rot}' for resident {r.get('name', 'unknown')}"
                    )

                    # Check 2: Call coverage (20 nights expected: Sun-Thu)
        call_dates = {ca["date"] for ca in call_assignments}
        expected_nights = 0
        current = start_date
        while current <= end_date:
            # Mon=0, Tue=1, Wed=2, Thu=3, Fri=4, Sat=5, Sun=6
            # Call on: Sun(6), Mon(0), Tue(1), Wed(2), Thu(3)
            if current.weekday() in {0, 1, 2, 3, 6}:
                expected_nights += 1
                if current not in call_dates:
                    warnings.append(f"Missing call coverage on {current}")
            current += timedelta(days=1)

        if len(call_assignments) != expected_nights:
            warnings.append(
                f"Call coverage: {len(call_assignments)}/{expected_nights} nights"
            )

            # Check 3: Physical clinic cap (≤6 per slot)
            # Clinical codes that count toward cap (NOT AT/PCAT)
        clinical_codes = {"C", "CV", "PR", "VAS", "VASC"}

        # Build per-slot counts from faculty schedules
        current = start_date
        while current <= end_date:
            if current.weekday() < 5:  # Weekdays only
                for slot in ["am", "pm"]:
                    count = 0
                    # Count faculty in clinic
                    for name, schedule in faculty_schedules.items():
                        day_data = schedule.get(current, {})
                        code = day_data.get(slot, "")
                        if code in clinical_codes:
                            count += 1

                            # Count residents in clinic (would need block assignments)
                            # For now, just warn if faculty alone exceeds cap
                    if count > 6:
                        warnings.append(
                            f"Clinic cap exceeded: {current} {slot.upper()} has {count} faculty in clinic (max 6)"
                        )
            current += timedelta(days=1)

        return warnings


async def export_block_schedule(
    session: AsyncSession,
    block_number: int,
    academic_year: int,
    output_path: Path | str | None = None,
    template_path: Path | str | None = None,
) -> bytes:
    """
    Convenience function to export block schedule to xlsx.

    Args:
        session: Database session
        block_number: Block number (1-13)
        academic_year: Academic year
        output_path: Optional path to save xlsx
        template_path: Optional custom template path

    Returns:
        xlsx bytes
    """
    service = BlockScheduleExportService(session, template_path)
    return await service.export_block(block_number, academic_year, output_path)


async def export_block_schedule_with_xml(
    session: AsyncSession,
    block_number: int,
    academic_year: int,
    xlsx_path: Path | str | None = None,
    xml_path: Path | str | None = None,
    template_path: Path | str | None = None,
) -> tuple[bytes, str]:
    """
    Export block schedule to both xlsx and XML.

    Args:
        session: Database session
        block_number: Block number (1-13)
        academic_year: Academic year
        xlsx_path: Optional path to save xlsx
        xml_path: Optional path to save XML
        template_path: Optional custom template path

    Returns:
        Tuple of (xlsx bytes, xml string)
    """
    service = BlockScheduleExportService(session, template_path)
    xlsx_bytes, xml_string = await service.export_block(
        block_number, academic_year, xlsx_path, return_xml=True
    )

    if xml_path:
        Path(xml_path).write_text(xml_string)

    return xlsx_bytes, xml_string
