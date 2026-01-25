"""Half-Day XML Exporter - Export from half_day_assignments table only.

This exporter reads DESCRIPTIVE TRUTH directly from the database:
- No pattern reconstruction
- No constant duplication
- Activity codes come from activities table via FK

Two Truths Architecture:
    PRESCRIPTIVE: rotation_templates + weekly_patterns → solver → DESCRIPTIVE
    DESCRIPTIVE:  half_day_assignments (what DID happen)
                                      ↓
                  HalfDayJSONExporter → JSON (canonical export)

This XML exporter is kept for validation and legacy ROSETTA compatibility.
"""

from datetime import date
from typing import Any
from uuid import UUID
from xml.dom import minidom
from xml.etree.ElementTree import Element, SubElement, tostring

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.logging import get_logger
from app.models.activity import Activity
from app.models.block_assignment import BlockAssignment
from app.models.call_assignment import CallAssignment
from app.models.half_day_assignment import HalfDayAssignment
from app.models.person import Person

logger = get_logger(__name__)


class HalfDayXMLExporter:
    """Export schedule from half_day_assignments table to XML.

    This exporter reads directly from the database without pattern duplication.
    It exports DESCRIPTIVE truth (what IS scheduled), not PRESCRIPTIVE truth
    (what SHOULD be scheduled).

    XML format matches ROSETTA for validation:
    ```xml
    <schedule block_start="2026-03-12" block_end="2026-04-08" source="half_day_assignments">
      <resident name="Name, First" pgy="1" rotation1="FMC" rotation2="">
        <day date="2026-03-12" weekday="Thu" am="C" pm="C"/>
        ...
      </resident>
      ...
    </schedule>
    ```
    """

    def __init__(self, db: Session):
        """Initialize exporter with database session.

        Args:
            db: SQLAlchemy session for database queries
        """
        self.db = db

    def export(
        self,
        block_start: date,
        block_end: date,
        person_ids: list[UUID] | None = None,
        include_faculty: bool = False,
        include_call: bool = False,
    ) -> str:
        """Export schedule for date range to XML.

        Args:
            block_start: First day of schedule block
            block_end: Last day of schedule block
            person_ids: Optional list of person IDs to export (default: all residents)
            include_faculty: If True, include faculty in export (default: False)
            include_call: If True, include call assignments (default: False)

        Returns:
            XML string in ROSETTA-compatible format
        """
        # Build root element
        root = Element("schedule")
        root.set("block_start", block_start.isoformat())
        root.set("block_end", block_end.isoformat())
        root.set("source", "half_day_assignments")

        # Get all half_day_assignments for date range with activity codes
        assignments = self._fetch_assignments(
            block_start, block_end, person_ids, include_faculty
        )

        # Group by person
        by_person: dict[UUID, list[HalfDayAssignment]] = {}
        for assignment in assignments:
            pid = assignment.person_id
            if pid not in by_person:
                by_person[pid] = []
            by_person[pid].append(assignment)

        # Get person details and block assignments for rotation info
        person_map = self._fetch_people(list(by_person.keys()))
        rotation_map = self._fetch_rotations(
            list(by_person.keys()), block_start, block_end
        )

        # Add each person's schedule
        for pid, person_assignments in sorted(
            by_person.items(),
            key=lambda x: person_map.get(x[0], {}).get("name", ""),
        ):
            person_info = person_map.get(pid, {})
            rotation_info = rotation_map.get(pid, {})
            self._add_person(
                root,
                person_info,
                rotation_info,
                person_assignments,
                block_start,
                block_end,
            )

        if include_call:
            call_assignments = self._fetch_call_assignments(block_start, block_end)
            if call_assignments:
                self._add_call_section(root, call_assignments)

        # Format and return XML
        xml_str = tostring(root, encoding="unicode")
        return minidom.parseString(xml_str).toprettyxml(indent="  ")

    def _fetch_assignments(
        self,
        block_start: date,
        block_end: date,
        person_ids: list[UUID] | None,
        include_faculty: bool = False,
    ) -> list[HalfDayAssignment]:
        """Fetch half_day_assignments with joined activity codes.

        Args:
            block_start: First day of schedule block
            block_end: Last day of schedule block
            person_ids: Optional list of person IDs to filter
            include_faculty: If True, include faculty (default: residents only)

        Note: By default only fetches residents (Person.type == 'resident').
        Set include_faculty=True to also include faculty schedules.
        """
        from sqlalchemy import or_

        # Build person type filter
        if include_faculty:
            type_filter = or_(Person.type == "resident", Person.type == "faculty")
        else:
            type_filter = Person.type == "resident"

        stmt = (
            select(HalfDayAssignment)
            .options(selectinload(HalfDayAssignment.activity))
            .join(Person, HalfDayAssignment.person_id == Person.id)
            .where(
                HalfDayAssignment.date >= block_start,
                HalfDayAssignment.date <= block_end,
                type_filter,
            )
            .order_by(
                HalfDayAssignment.person_id,
                HalfDayAssignment.date,
                HalfDayAssignment.time_of_day,
            )
        )

        if person_ids:
            stmt = stmt.where(HalfDayAssignment.person_id.in_(person_ids))

        result = self.db.execute(stmt)
        return list(result.scalars().all())

    def _fetch_people(self, person_ids: list[UUID]) -> dict[UUID, dict[str, Any]]:
        """Fetch person details by ID."""
        if not person_ids:
            return {}

        stmt = select(Person).where(Person.id.in_(person_ids))
        result = self.db.execute(stmt)
        people = result.scalars().all()

        return {
            p.id: {
                "name": p.name,
                "pgy": p.pgy_level if p.type == "resident" else None,
                "type": p.type,
            }
            for p in people
        }

    def _fetch_rotations(
        self,
        person_ids: list[UUID],
        block_start: date,
        block_end: date,
    ) -> dict[UUID, dict[str, Any]]:
        """Fetch rotation info from block_assignments for the date range.

        Uses denormalized block_number/academic_year fields (always populated)
        rather than the nullable academic_block_id FK for reliability.
        """
        if not person_ids:
            return {}

        from app.utils.academic_blocks import get_block_number_for_date

        # Get block number and academic year for the requested date range
        block_num, acad_year = get_block_number_for_date(block_start)

        # Filter by block_number and academic_year (denormalized, always populated)
        stmt = (
            select(BlockAssignment)
            .options(
                selectinload(BlockAssignment.rotation_template),
                selectinload(BlockAssignment.secondary_rotation_template),
            )
            .where(
                BlockAssignment.resident_id.in_(person_ids),
                BlockAssignment.block_number == block_num,
                BlockAssignment.academic_year == acad_year,
            )
        )

        result = self.db.execute(stmt)
        block_assignments = result.scalars().all()

        rotation_map: dict[UUID, dict[str, Any]] = {}
        for ba in block_assignments:
            rotation1 = ""
            rotation2 = ""

            if ba.rotation_template:
                rotation1 = (
                    ba.rotation_template.display_abbreviation
                    or ba.rotation_template.abbreviation
                    or ""
                )

            if ba.secondary_rotation_template:
                rotation2 = (
                    ba.secondary_rotation_template.display_abbreviation
                    or ba.secondary_rotation_template.abbreviation
                    or ""
                )

            rotation_map[ba.resident_id] = {
                "rotation1": rotation1,
                "rotation2": rotation2,
            }

        return rotation_map

    def _add_person(
        self,
        parent: Element,
        person_info: dict[str, Any],
        rotation_info: dict[str, Any],
        assignments: list[HalfDayAssignment],
        block_start: date,
        block_end: date,
    ) -> None:
        """Add a person element with their daily schedule from DB.

        Uses <resident> for residents and <faculty> for faculty members.
        Faculty don't have rotation info (rotation1/rotation2 will be empty).
        """
        from datetime import timedelta

        person_type = person_info.get("type", "resident")
        element_name = "faculty" if person_type == "faculty" else "resident"

        person_elem = SubElement(parent, element_name)
        person_elem.set("name", person_info.get("name", ""))
        person_elem.set("pgy", str(person_info.get("pgy", "") or ""))
        person_elem.set("rotation1", rotation_info.get("rotation1", ""))
        person_elem.set("rotation2", rotation_info.get("rotation2", "") or "")

        # Index assignments by (date, time_of_day) for O(1) lookup
        assignment_index: dict[tuple[date, str], HalfDayAssignment] = {}
        for a in assignments:
            assignment_index[(a.date, a.time_of_day)] = a

        # Generate day elements for each day in range
        current = block_start
        while current <= block_end:
            am_assignment = assignment_index.get((current, "AM"))
            pm_assignment = assignment_index.get((current, "PM"))

            # Get activity codes from database (descriptive truth)
            am_code = self._get_activity_code(am_assignment)
            pm_code = self._get_activity_code(pm_assignment)

            day_elem = SubElement(person_elem, "day")
            day_elem.set("date", current.isoformat())
            day_elem.set("weekday", current.strftime("%a"))
            day_elem.set("am", am_code)
            day_elem.set("pm", pm_code)

            current = current + timedelta(days=1)

    def _fetch_call_assignments(
        self,
        block_start: date,
        block_end: date,
    ) -> list[dict[str, Any]]:
        """Fetch call assignments for date range."""
        stmt = (
            select(CallAssignment)
            .join(Person, CallAssignment.person_id == Person.id)
            .where(
                CallAssignment.date >= block_start,
                CallAssignment.date <= block_end,
            )
            .options(selectinload(CallAssignment.person))
        )
        result = self.db.execute(stmt)
        calls = result.scalars().all()

        call_rows: list[dict[str, Any]] = []
        for ca in calls:
            name = ca.person.name if ca.person else ""
            # Use last name for call row (matches template convention)
            last_name = name.split(",")[0] if "," in name else name
            call_rows.append(
                {
                    "date": ca.date,
                    "staff": last_name,
                }
            )

        return call_rows

    def _add_call_section(
        self,
        parent: Element,
        call_rows: list[dict[str, Any]],
    ) -> None:
        """Add call section to XML."""
        call_elem = SubElement(parent, "call")
        for row in call_rows:
            night = SubElement(call_elem, "night")
            night.set("date", row.get("date").isoformat())
            night.set("staff", row.get("staff", ""))

    def _get_activity_code(self, assignment: HalfDayAssignment | None) -> str:
        """Get activity code from assignment.

        This reads the actual activity code from the database,
        not from pattern constants. Returns empty string for missing
        slots to maintain ROSETTA XML compatibility.
        """
        if assignment is None:
            return ""  # Missing slot - empty for ROSETTA compatibility

        if assignment.activity is None:
            # NULL activity_id - data integrity issue (EC-4)
            logger.warning(
                f"NULL activity_id in half_day_assignment: "
                f"person_id={assignment.person_id}, "
                f"date={assignment.date}, "
                f"time_of_day={assignment.time_of_day}"
            )
            return ""  # NULL activity - empty for ROSETTA compatibility

        # Use display_abbreviation if available, else code
        activity = assignment.activity
        return activity.display_abbreviation or activity.code or ""


def export_block_schedule(
    db: Session,
    block_number: int,
    academic_year: int,
    include_faculty: bool = False,
    include_call: bool = False,
) -> str:
    """Convenience function to export a block schedule.

    Args:
        db: Database session
        block_number: Block number (1-13)
        academic_year: Academic year start (e.g., 2025 for AY 2025-2026)
        include_faculty: If True, include faculty in export (default: False)

    Returns:
        XML string with schedule data
    """
    from app.utils.academic_blocks import get_block_dates

    block_dates = get_block_dates(block_number, academic_year)

    exporter = HalfDayXMLExporter(db)
    return exporter.export(
        block_dates.start_date,
        block_dates.end_date,
        include_faculty=include_faculty,
        include_call=include_call,
    )
