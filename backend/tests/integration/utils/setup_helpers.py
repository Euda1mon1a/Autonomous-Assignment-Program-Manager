"""
Setup helpers for integration tests.

Provides utilities for setting up test data and scenarios.
"""

from datetime import date, timedelta
from typing import List
from uuid import uuid4

from sqlalchemy.orm import Session

from app.models.assignment import Assignment
from app.models.block import Block
from app.models.person import Person
from app.models.rotation_template import RotationTemplate


def create_test_schedule(
    db: Session,
    residents: List[Person],
    template: RotationTemplate,
    start_date: date,
    days: int = 7,
) -> List[Assignment]:
    """
    Create a test schedule with blocks and assignments.

    Args:
        db: Database session
        residents: List of residents to assign
        template: Rotation template to use
        start_date: Start date for schedule
        days: Number of days to create

    Returns:
        List of created assignments
    """
    blocks = []
    assignments = []

    # Create blocks
    for i in range(days):
        current_date = start_date + timedelta(days=i)
        for time_of_day in ["AM", "PM"]:
            block = Block(
                id=uuid4(),
                date=current_date,
                time_of_day=time_of_day,
                block_number=1,
                is_weekend=(current_date.weekday() >= 5),
            )
            db.add(block)
            blocks.append(block)

    db.commit()

    # Create assignments
    for i, block in enumerate(blocks):
        resident = residents[i % len(residents)]
        assignment = Assignment(
            id=uuid4(),
            block_id=block.id,
            person_id=resident.id,
            rotation_template_id=template.id,
            role="primary",
        )
        db.add(assignment)
        assignments.append(assignment)

    db.commit()
    return assignments


def create_test_residents(db: Session, count: int = 3) -> List[Person]:
    """
    Create test residents.

    Args:
        db: Database session
        count: Number of residents to create

    Returns:
        List of created residents
    """
    residents = []

    for i in range(count):
        resident = Person(
            id=uuid4(),
            name=f"Dr. Test Resident {i+1}",
            type="resident",
            email=f"resident{i+1}@test.org",
            pgy_level=(i % 3) + 1,
        )
        db.add(resident)
        residents.append(resident)

    db.commit()
    return residents


def create_test_faculty(db: Session, count: int = 2) -> List[Person]:
    """
    Create test faculty members.

    Args:
        db: Database session
        count: Number of faculty to create

    Returns:
        List of created faculty
    """
    faculty = []

    for i in range(count):
        fac = Person(
            id=uuid4(),
            name=f"Dr. Test Faculty {i+1}",
            type="faculty",
            email=f"faculty{i+1}@test.org",
            performs_procedures=(i == 0),
            specialties=["General Medicine"],
        )
        db.add(fac)
        faculty.append(fac)

    db.commit()
    return faculty


def create_test_rotation_templates(db: Session) -> List[RotationTemplate]:
    """
    Create standard test rotation templates.

    Args:
        db: Database session

    Returns:
        List of created templates
    """
    templates = [
        RotationTemplate(
            id=uuid4(),
            name="Outpatient Clinic",
            activity_type="outpatient",
            abbreviation="OPC",
            max_residents=4,
        ),
        RotationTemplate(
            id=uuid4(),
            name="Inpatient Ward",
            activity_type="inpatient",
            abbreviation="IPW",
            max_residents=3,
        ),
        RotationTemplate(
            id=uuid4(),
            name="Procedures",
            activity_type="procedures",
            abbreviation="PROC",
            max_residents=2,
            supervision_required=True,
            max_supervision_ratio=2,
        ),
    ]

    for template in templates:
        db.add(template)

    db.commit()
    return templates


def create_academic_year_blocks(
    db: Session, start_date: date, end_date: date
) -> List[Block]:
    """
    Create blocks for an entire academic year.

    Args:
        db: Database session
        start_date: Academic year start date
        end_date: Academic year end date

    Returns:
        List of created blocks
    """
    blocks = []
    current_date = start_date
    block_number = 1

    while current_date <= end_date:
        for time_of_day in ["AM", "PM"]:
            block = Block(
                id=uuid4(),
                date=current_date,
                time_of_day=time_of_day,
                block_number=block_number,
                is_weekend=(current_date.weekday() >= 5),
            )
            db.add(block)
            blocks.append(block)

        current_date += timedelta(days=1)

        # Increment block number every 28 days
        if (current_date - start_date).days % 28 == 0:
            block_number += 1

    db.commit()
    return blocks


def setup_minimal_schedule_scenario(
    db: Session,
) -> dict:
    """
    Set up minimal viable schedule scenario.

    Creates:
    - 3 residents
    - 2 faculty
    - 3 rotation templates
    - 1 week of blocks
    - Basic assignments

    Args:
        db: Database session

    Returns:
        Dictionary with created entities
    """
    residents = create_test_residents(db, count=3)
    faculty = create_test_faculty(db, count=2)
    templates = create_test_rotation_templates(db)

    start_date = date.today()
    assignments = create_test_schedule(
        db=db,
        residents=residents,
        template=templates[0],
        start_date=start_date,
        days=7,
    )

    return {
        "residents": residents,
        "faculty": faculty,
        "templates": templates,
        "assignments": assignments,
        "start_date": start_date,
    }
