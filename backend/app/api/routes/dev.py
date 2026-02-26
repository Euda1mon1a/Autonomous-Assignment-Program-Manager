import os
import random
import uuid
from datetime import date, timedelta
from typing import Dict, List, Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.api.deps import get_db
from app.models.person import Person, FacultyRole
from app.models.activity import Activity, ActivityCategory
from app.models.half_day_assignment import HalfDayAssignment, AssignmentSource

router = APIRouter()


class SeedResponse(BaseModel):
    status: str
    scenario: str
    residents_created: int
    faculty_created: int
    activities_created: int
    assignments_created: int


def _generate_deterministic_uuid(rng: random.Random) -> uuid.UUID:
    """Generate a deterministic UUID using a seeded random instance."""
    return uuid.UUID(int=rng.getrandbits(128))


@router.post("/seed", response_model=SeedResponse)
def seed_database(scenario: str = "e2e_baseline", db: Session = Depends(get_db)):
    """
    Seed the database with deterministic test data.
    Only available when ENV=test or ALLOW_DEV_SEED=true.
    """
    env = os.getenv("ENV", "development")
    allow_seed = os.getenv("ALLOW_DEV_SEED", "false").lower() == "true"

    if env != "test" and not allow_seed:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Dev seed endpoint only available in test environment or when ALLOW_DEV_SEED is true",
        )

    if scenario != "e2e_baseline":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown scenario: {scenario}",
        )

    # Use deterministic random generator
    rng = random.Random(42)

    # 1. Clear existing data to ensure clean state
    # We must delete half_day_assignments first, then people and activities
    db.query(HalfDayAssignment).delete()
    # It might be safer to just truncate/delete only the e2e seeded ones, or clear all
    # For a dev seed, clearing all is typically what is expected, but let's just
    # delete the specific synthetic ones if we want to be safe, or just clear all.
    # The roadmap says "Create a protected FastAPI endpoint that deterministically seeds the test database."
    # Let's clear the specific tables to avoid constraint issues.
    db.query(HalfDayAssignment).delete()
    db.query(Activity).filter(
        Activity.code.in_(["C", "NF", "FMIT", "LV", "LEC"])
    ).delete(synchronize_session=False)
    db.query(Person).filter(Person.name.like("CPT Doe-%")).delete(
        synchronize_session=False
    )
    db.query(Person).filter(Person.name.like("Dr. Faculty-%")).delete(
        synchronize_session=False
    )
    db.commit()

    # 2. Seed Activities
    activities = []
    activity_specs = [
        ("Clinic", "C", "C", ActivityCategory.CLINICAL),
        ("Night Float", "NF", "NF", ActivityCategory.CLINICAL),
        ("FMIT", "FMIT", "FMIT", ActivityCategory.CLINICAL),
        ("Leave", "LV", "LV", ActivityCategory.TIME_OFF),
        ("Lecture", "LEC", "LEC", ActivityCategory.EDUCATIONAL),
    ]

    activity_dict = {}
    for name, code, abbrev, category in activity_specs:
        act = (
            db.query(Activity)
            .filter((Activity.code == code) | (Activity.name == name))
            .first()
        )
        if not act:
            act = Activity(
                id=_generate_deterministic_uuid(rng),
                name=name,
                code=code,
                display_abbreviation=abbrev,
                activity_category=category.value,
            )
            db.add(act)
        activities.append(act)
        activity_dict[code] = act

    db.flush()

    # 3. Seed Residents
    residents = []
    for i in range(1, 18):
        pgy = 1 if i <= 6 else (2 if i <= 12 else 3)
        res = Person(
            id=_generate_deterministic_uuid(rng),
            name=f"CPT Doe-{i:02d}",
            type="resident",
            pgy_level=pgy,
            email=f"doe{i:02d}@e2e.test",
        )
        db.add(res)
        residents.append(res)

    # 4. Seed Faculty
    faculty_list = []
    letters = "ABCDEFGHIJKLM"
    roles = [
        FacultyRole.CORE,
        FacultyRole.CORE,
        FacultyRole.APD,
        FacultyRole.PD,
        FacultyRole.DEPT_CHIEF,
    ]
    for i, letter in enumerate(letters):
        role = roles[i % len(roles)]
        fac = Person(
            id=_generate_deterministic_uuid(rng),
            name=f"Dr. Faculty-{letter}",
            type="faculty",
            faculty_role=role.value,
            email=f"faculty_{letter.lower()}@e2e.test",
        )
        db.add(fac)
        faculty_list.append(fac)

    # Flush to get IDs
    db.flush()

    # 5. Seed Block 10 Half-Day Assignments (28 days)
    # Block 10 usually starts in Spring. Let's use a fixed date: 2026-03-02 as start
    start_date = date(2026, 3, 2)
    assignments_created = 0

    all_people = residents + faculty_list
    activity_codes = ["C", "NF", "FMIT", "LV", "LEC"]

    for day_offset in range(28):
        current_date = start_date + timedelta(days=day_offset)
        for person in all_people:
            # Assign AM
            am_act_code = rng.choice(activity_codes)
            am_assignment = HalfDayAssignment(
                id=_generate_deterministic_uuid(rng),
                person_id=person.id,
                date=current_date,
                time_of_day="AM",
                activity_id=activity_dict[am_act_code].id,
                source=AssignmentSource.PRELOAD.value
                if am_act_code == "FMIT"
                else AssignmentSource.SOLVER.value,
            )
            db.add(am_assignment)
            assignments_created += 1

            # Assign PM
            pm_act_code = rng.choice(activity_codes)
            pm_assignment = HalfDayAssignment(
                id=_generate_deterministic_uuid(rng),
                person_id=person.id,
                date=current_date,
                time_of_day="PM",
                activity_id=activity_dict[pm_act_code].id,
                source=AssignmentSource.PRELOAD.value
                if pm_act_code == "FMIT"
                else AssignmentSource.SOLVER.value,
            )
            db.add(pm_assignment)
            assignments_created += 1

    db.commit()

    return SeedResponse(
        status="success",
        scenario=scenario,
        residents_created=len(residents),
        faculty_created=len(faculty_list),
        activities_created=len(activities),
        assignments_created=assignments_created,
    )
