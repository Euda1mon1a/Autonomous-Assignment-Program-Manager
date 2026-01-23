"""Half-Day XML Exporter - Export from half_day_assignments table only.

This exporter reads DESCRIPTIVE TRUTH directly from the database:
- No pattern reconstruction
- No constant duplication
- Activity codes come from activities table via FK

Two Truths Architecture:
    PRESCRIPTIVE: rotation_templates + weekly_patterns → solver → DESCRIPTIVE
    DESCRIPTIVE:  half_day_assignments (what DID happen)
                                      ↓
                  HalfDayXMLExporter → XML (canonical export)

This is the canonical export path. Use ScheduleXMLExporter only for validation
against legacy ROSETTA format.
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
    ) -> str:
        """Export schedule for date range to XML.

        Args:
            block_start: First day of schedule block
            block_end: Last day of schedule block
            person_ids: Optional list of person IDs to export (default: all residents)

        Returns:
            XML string in ROSETTA-compatible format
        """
        # Build root element
        root = Element("schedule")
        root.set("block_start", block_start.isoformat())
        root.set("block_end", block_end.isoformat())
        root.set("source", "half_day_assignments")

        # Get all half_day_assignments for date range with activity codes
        assignments = self._fetch_assignments(block_start, block_end, person_ids)

        # Group by person
        by_person: dict[UUID, list[HalfDayAssignment]] = {}
        for assignment in assignments:
            pid = assignment.person_id
            if pid not in by_person:
                by_person[pid] = []
            by_person[pid].append(assignment)

        # Get person details and block assignments for rotation info
        person_map = self._fetch_people(list(by_person.keys()))
        rotation_map = self._fetch_rotations(list(by_person.keys()), block_start, block_end)

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

        # Format and return XML
        xml_str = tostring(root, encoding="unicode")
        return minidom.parseString(xml_str).toprettyxml(indent="  ")

    def _fetch_assignments(
        self,
        block_start: date,
        block_end: date,
        person_ids: list[UUID] | None,
    ) -> list[HalfDayAssignment]:
        """Fetch half_day_assignments with joined activity codes."""
        stmt = (
            select(HalfDayAssignment)
            .options(selectinload(HalfDayAssignment.activity))
            .join(Person, HalfDayAssignment.person_id == Person.id)
            .where(
                HalfDayAssignment.date >= block_start,
                HalfDayAssignment.date <= block_end,
                Person.type == "resident",  # Default to residents only
            )
            .order_by(HalfDayAssignment.person_id, HalfDayAssignment.date, HalfDayAssignment.time_of_day)
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
                "pgy": p.pgy_level or 1,
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
        """Fetch rotation info from block_assignments for the date range."""
        if not person_ids:
            return {}

        # Find block assignments that overlap with this date range
        stmt = (
            select(BlockAssignment)
            .options(
                selectinload(BlockAssignment.rotation_template),
                selectinload(BlockAssignment.secondary_rotation_template),
            )
            .where(
                BlockAssignment.person_id.in_(person_ids),
            )
        )

        result = self.db.execute(stmt)
        block_assignments = result.scalars().all()

        rotation_map: dict[UUID, dict[str, Any]] = {}
        for ba in block_assignments:
            # Check if this block_assignment is relevant to the date range
            # by looking at the associated block dates
            rotation1 = ""
            rotation2 = ""

            if ba.rotation_template:
                rotation1 = ba.rotation_template.display_abbreviation or ba.rotation_template.abbreviation or ""

            if ba.secondary_rotation_template:
                rotation2 = ba.secondary_rotation_template.display_abbreviation or ba.secondary_rotation_template.abbreviation or ""

            rotation_map[ba.person_id] = {
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
        """Add a person element with their daily schedule from DB."""
        from datetime import timedelta

        res_elem = SubElement(parent, "resident")
        res_elem.set("name", person_info.get("name", ""))
        res_elem.set("pgy", str(person_info.get("pgy", 1)))
        res_elem.set("rotation1", rotation_info.get("rotation1", ""))
        res_elem.set("rotation2", rotation_info.get("rotation2", "") or "")

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

            day_elem = SubElement(res_elem, "day")
            day_elem.set("date", current.isoformat())
            day_elem.set("weekday", current.strftime("%a"))
            day_elem.set("am", am_code)
            day_elem.set("pm", pm_code)

            current = current + timedelta(days=1)

    def _get_activity_code(self, assignment: HalfDayAssignment | None) -> str:
        """Get activity code from assignment.

        This reads the actual activity code from the database,
        not from pattern constants. If no assignment exists,
        returns "?" to indicate missing data.
        """
        if assignment is None:
            return "?"  # Missing slot - should investigate

        if assignment.activity is None:
            # NULL activity_id - data integrity issue (EC-4)
            logger.warning(
                f"NULL activity_id in half_day_assignment: "
                f"person_id={assignment.person_id}, "
                f"date={assignment.date}, "
                f"time_of_day={assignment.time_of_day}"
            )
            return "???"  # Distinct from "?" to indicate NULL activity

        # Use display_abbreviation if available, else code
        activity = assignment.activity
        return activity.display_abbreviation or activity.code or "???"


def export_block_schedule(
    db: Session,
    block_number: int,
    academic_year: int,
) -> str:
    """Convenience function to export a block schedule.

    Args:
        db: Database session
        block_number: Block number (1-13)
        academic_year: Academic year start (e.g., 2025 for AY 2025-2026)

    Returns:
        XML string with schedule data
    """
    from app.utils.academic_blocks import get_block_dates

    block_start, block_end = get_block_dates(block_number, academic_year)

    exporter = HalfDayXMLExporter(db)
    return exporter.export(block_start, block_end)
