"""Half-Day JSON Exporter - Export from half_day_assignments table only.

This exporter reads DESCRIPTIVE TRUTH directly from the database:
- No pattern reconstruction
- No constant duplication
- Activity codes come from activities table via FK

Two Truths Architecture:
    PRESCRIPTIVE: rotation_templates + weekly_patterns → solver → DESCRIPTIVE
    DESCRIPTIVE:  half_day_assignments (what DID happen)
                                      ↓
                 HalfDayJSONExporter → JSON (canonical export)
"""

from __future__ import annotations

import json
from datetime import date, timedelta
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.services.half_day_xml_exporter import HalfDayXMLExporter

logger = get_logger(__name__)


class HalfDayJSONExporter(HalfDayXMLExporter):
    """Export schedule from half_day_assignments table to JSON dict."""

    def export(
        self,
        block_start: date,
        block_end: date,
        person_ids: list[UUID] | None = None,
        include_faculty: bool = False,
        include_call: bool = False,
        include_overrides: bool = True,
    ) -> dict[str, Any]:
        """Export schedule for date range to JSON-friendly dict.

        Args:
            block_start: First day of schedule block
            block_end: Last day of schedule block
            person_ids: Optional list of person IDs to export (default: all residents)
            include_faculty: If True, include faculty in export (default: False)
            include_call: If True, include call assignments (default: False)

        Returns:
            Dict with schedule data suitable for JSON serialization
        """
        data: dict[str, Any] = {
            "block_start": block_start.isoformat(),
            "block_end": block_end.isoformat(),
            "source": "half_day_assignments",
            "residents": [],
            "faculty": [],
        }

        assignments = self._fetch_assignments(
            block_start,
            block_end,
            person_ids,
            include_faculty,
            include_overrides=include_overrides,
        )

        by_person: dict[UUID, list] = {}
        for assignment in assignments:
            pid = assignment.person_id
            if pid not in by_person:
                by_person[pid] = []
            by_person[pid].append(assignment)

        person_map = self._fetch_people(list(by_person.keys()))
        rotation_map = self._fetch_rotations(
            list(by_person.keys()), block_start, block_end
        )

        for pid, person_assignments in sorted(
            by_person.items(),
            key=lambda x: person_map.get(x[0], {}).get("name", ""),
        ):
            person_info = person_map.get(pid, {})
            rotation_info = rotation_map.get(pid, {})
            person_payload = self._build_person(
                person_info,
                rotation_info,
                person_assignments,
                block_start,
                block_end,
            )

            if person_info.get("type") == "faculty":
                data["faculty"].append(person_payload)
            else:
                data["residents"].append(person_payload)

        if include_call:
            call_assignments = self._fetch_call_assignments(block_start, block_end)
            data["call"] = {
                "nights": [
                    {
                        "date": row.get("date").isoformat()
                        if isinstance(row.get("date"), date)
                        else row.get("date"),
                        "staff": row.get("staff", ""),
                    }
                    for row in call_assignments
                ]
            }

        return data

    def export_json(
        self,
        block_start: date,
        block_end: date,
        person_ids: list[UUID] | None = None,
        include_faculty: bool = False,
        include_call: bool = False,
        include_overrides: bool = True,
        pretty: bool = False,
    ) -> str:
        """Export schedule to JSON string."""
        data = self.export(
            block_start,
            block_end,
            person_ids=person_ids,
            include_faculty=include_faculty,
            include_call=include_call,
            include_overrides=include_overrides,
        )
        return json.dumps(data, indent=2 if pretty else None)

    def _build_person(
        self,
        person_info: dict[str, Any],
        rotation_info: dict[str, Any],
        assignments: list,
        block_start: date,
        block_end: date,
    ) -> dict[str, Any]:
        """Build person payload with daily schedule from DB assignments."""
        person = {
            "name": person_info.get("name", ""),
            "pgy": person_info.get("pgy"),
            "rotation1": rotation_info.get("rotation1", ""),
            "rotation2": rotation_info.get("rotation2", ""),
            "days": [],
        }

        assignment_index: dict[tuple[date, str], Any] = {}
        for a in assignments:
            assignment_index[(a.date, a.time_of_day)] = a

        current = block_start
        while current <= block_end:
            am_assignment = assignment_index.get((current, "AM"))
            pm_assignment = assignment_index.get((current, "PM"))

            am_code = self._get_activity_code(am_assignment)
            pm_code = self._get_activity_code(pm_assignment)

            person["days"].append(
                {
                    "date": current.isoformat(),
                    "weekday": current.strftime("%a"),
                    "am": am_code,
                    "pm": pm_code,
                }
            )

            current = current + timedelta(days=1)

        return person


def export_block_schedule_json(
    db: Session,
    block_number: int,
    academic_year: int,
    include_faculty: bool = False,
    include_call: bool = False,
    include_overrides: bool = True,
) -> dict[str, Any]:
    """Convenience function to export a block schedule as JSON dict."""
    from app.utils.academic_blocks import get_block_dates

    block_dates = get_block_dates(block_number, academic_year)

    exporter = HalfDayJSONExporter(db)
    return exporter.export(
        block_dates.start_date,
        block_dates.end_date,
        include_faculty=include_faculty,
        include_call=include_call,
        include_overrides=include_overrides,
    )
