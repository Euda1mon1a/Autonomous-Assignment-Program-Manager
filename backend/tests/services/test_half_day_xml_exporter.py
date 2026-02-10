"""Tests for HalfDayXMLExporter filtering."""

from datetime import date
from uuid import uuid4
from xml.etree import ElementTree as ET

from sqlalchemy.orm import Session

from app.models.activity import Activity, ActivityCategory
from app.models.half_day_assignment import HalfDayAssignment
from app.models.person import Person
from app.services.half_day_xml_exporter import HalfDayXMLExporter


def test_export_excludes_faculty_by_default(db: Session) -> None:
    activity = Activity(
        id=uuid4(),
        name="Clinic",
        code="clinic",
        display_abbreviation="C",
        activity_category=ActivityCategory.CLINICAL.value,
    )

    resident = Person(
        id=uuid4(),
        name="Dr. Resident",
        type="resident",
        email="resident@hospital.org",
        pgy_level=2,
    )

    faculty = Person(
        id=uuid4(),
        name="Dr. Faculty",
        type="faculty",
        email="faculty@hospital.org",
    )

    db.add_all([activity, resident, faculty])
    db.commit()

    slot_date = date(2026, 2, 3)

    resident_assignment = HalfDayAssignment(
        id=uuid4(),
        person_id=resident.id,
        date=slot_date,
        time_of_day="AM",
        activity_id=activity.id,
        source="solver",
    )

    faculty_assignment = HalfDayAssignment(
        id=uuid4(),
        person_id=faculty.id,
        date=slot_date,
        time_of_day="AM",
        activity_id=activity.id,
        source="solver",
    )

    db.add_all([resident_assignment, faculty_assignment])
    db.commit()

    exporter = HalfDayXMLExporter(db)
    xml_output = exporter.export(slot_date, slot_date)

    root = ET.fromstring(xml_output)
    resident_names = [node.attrib.get("name") for node in root.findall("resident")]

    assert any("Resident" in name for name in resident_names)
    assert not any("Faculty" in name for name in resident_names)
