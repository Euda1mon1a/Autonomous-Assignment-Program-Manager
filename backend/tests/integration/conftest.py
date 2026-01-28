"""
Integration test fixtures.

Provides fixtures specifically for integration testing that exercise
the full API stack with realistic data scenarios.
"""

from collections.abc import Generator
from datetime import date, timedelta
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models.block import Block
from app.models.person import Person
from app.models.rotation_template import RotationTemplate
from app.models.user import User
from tests.conftest import TestingSessionLocal, engine


@pytest.fixture(scope="function")
def integration_db() -> Generator[Session, None, None]:
    """
    Create a fresh database for integration tests.
    """
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def integration_client(integration_db: Session) -> Generator[TestClient, None, None]:
    """
    Create an authenticated test client for integration tests.
    """
    app.dependency_overrides[get_db] = lambda: integration_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def admin_user(integration_db: Session) -> User:
    """Create an admin user for authenticated tests."""
    user = User(
        id=uuid4(),
        username="admin",
        email="admin@test.org",
        hashed_password=get_password_hash("admin123"),
        role="admin",
        is_active=True,
    )
    integration_db.add(user)
    integration_db.commit()
    integration_db.refresh(user)
    return user


@pytest.fixture
def auth_headers(integration_client: TestClient, admin_user: User) -> dict:
    """Get authentication headers for API requests."""
    response = integration_client.post(
        "/api/auth/login/json",
        json={"username": "admin", "password": "admin123"},
    )
    if response.status_code == 200:
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    return {}


@pytest.fixture
def full_program_setup(integration_db: Session) -> dict:
    """
    Create a complete program setup for integration testing.

    Includes:
    - 3 residents (PGY 1, 2, 3)
    - 3 faculty members
    - 2 rotation templates
    - 28 days of blocks (56 half-day blocks)
    """
    # Create residents
    residents = []
    for pgy in range(1, 4):
        resident = Person(
            id=uuid4(),
            name=f"Dr. Resident PGY{pgy}",
            type="resident",
            email=f"resident{pgy}@hospital.org",
            pgy_level=pgy,
        )
        integration_db.add(resident)
        residents.append(resident)

    # Create faculty
    faculty = []
    specialties = [["Sports Medicine"], ["Primary Care"], ["Musculoskeletal"]]
    for i, specs in enumerate(specialties, 1):
        fac = Person(
            id=uuid4(),
            name=f"Dr. Faculty {i}",
            type="faculty",
            email=f"faculty{i}@hospital.org",
            performs_procedures=(i == 1),
            specialties=specs,
        )
        integration_db.add(fac)
        faculty.append(fac)

    # Create rotation templates
    templates = []
    template_configs = [
        ("Sports Medicine Clinic", "clinic", "SMC", True),
        ("Inpatient Service", "inpatient", "INP", True),
    ]
    for name, rotation_type, abbrev, supervision in template_configs:
        template = RotationTemplate(
            id=uuid4(),
            name=name,
            rotation_type=rotation_type,
            abbreviation=abbrev,
            supervision_required=supervision,
            max_supervision_ratio=4,
        )
        integration_db.add(template)
        templates.append(template)

    # Create blocks for 28 days
    blocks = []
    start_date = date.today()
    for i in range(28):
        current_date = start_date + timedelta(days=i)
        for time_of_day in ["AM", "PM"]:
            block = Block(
                id=uuid4(),
                date=current_date,
                time_of_day=time_of_day,
                block_number=1,
                is_weekend=(current_date.weekday() >= 5),
                is_holiday=False,
            )
            integration_db.add(block)
            blocks.append(block)

    integration_db.commit()

    # Refresh all objects
    for r in residents:
        integration_db.refresh(r)
    for f in faculty:
        integration_db.refresh(f)
    for t in templates:
        integration_db.refresh(t)
    for b in blocks:
        integration_db.refresh(b)

    return {
        "residents": residents,
        "faculty": faculty,
        "templates": templates,
        "blocks": blocks,
        "start_date": start_date,
        "end_date": start_date + timedelta(days=27),
    }
