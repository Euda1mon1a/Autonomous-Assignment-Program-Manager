"""
Pytest configuration and fixtures for backend tests.

Provides test database setup, API client, and common fixtures
for testing the Residency Scheduler API.
"""

from collections.abc import AsyncGenerator, Generator
from datetime import date, timedelta
import os
from typing import Any
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, configure_mappers, sessionmaker
from sqlalchemy.pool import StaticPool
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy_continuum import versioning_manager

from app.core.security import get_password_hash
from app.db.base import Base
from app.db.session import get_async_db, get_db
from app.main import app
from app.models.absence import Absence
from app.models.assignment import Assignment
from app.models.block import Block
from app.models.person import Person
from app.models.rotation_template import RotationTemplate
from app.models.user import User
from app.utils.academic_blocks import get_block_number_for_date

# Configure mappers to ensure SQLAlchemy-Continuum creates version tables
configure_mappers()

# Use TEST_DATABASE_URL if provided, otherwise fall back to DATABASE_URL or SQLite.
TEST_DATABASE_URL = (
    os.getenv("TEST_DATABASE_URL") or os.getenv("DATABASE_URL") or "sqlite:///:memory:"
)
USE_SQLITE = TEST_DATABASE_URL.startswith("sqlite")
TEST_SCHEMA = None


def _is_vector_column(column) -> bool:
    return isinstance(column.type, Vector)


def _is_sqlite_unsupported_column(column) -> bool:
    return isinstance(column.type, (Vector, JSONB))


if USE_SQLITE:
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
else:
    # Isolate tests in a dedicated schema to avoid touching existing data.
    TEST_SCHEMA = f"test_schema_{uuid4().hex}"
    engine = create_engine(
        TEST_DATABASE_URL,
        pool_pre_ping=True,
        connect_args={"options": f"-c search_path={TEST_SCHEMA}"},
    )

    with engine.begin() as conn:
        conn.exec_driver_sql(f'CREATE SCHEMA IF NOT EXISTS "{TEST_SCHEMA}"')

if USE_SQLITE:
    TEST_TABLES = [
        table
        for table in Base.metadata.sorted_tables
        if not any(_is_sqlite_unsupported_column(column) for column in table.columns)
    ]
    VERSIONING_TABLES = [
        table
        for table in versioning_manager.metadata.sorted_tables
        if not any(_is_sqlite_unsupported_column(column) for column in table.columns)
    ]
else:
    TEST_TABLES = [
        table
        for table in Base.metadata.sorted_tables
        if not any(_is_vector_column(column) for column in table.columns)
    ]
    VERSIONING_TABLES = [
        table
        for table in versioning_manager.metadata.sorted_tables
        if not any(_is_vector_column(column) for column in table.columns)
    ]
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class AsyncSessionWrapper:
    """Wraps a sync Session to provide async-compatible interface for tests.

    This allows sync tests using TestClient to work with code that expects
    AsyncSession methods. The wrapper makes sync methods awaitable.
    """

    def __init__(self, sync_session: Session):
        self._session = sync_session

    async def execute(self, statement, *args, **kwargs):
        """Execute statement and return result (makes sync execute awaitable)."""
        return self._session.execute(statement, *args, **kwargs)

    async def commit(self):
        """Commit transaction."""
        self._session.commit()

    async def rollback(self):
        """Rollback transaction."""
        self._session.rollback()

    async def flush(self):
        """Flush session."""
        self._session.flush()

    async def refresh(self, obj, *args, **kwargs):
        """Refresh object from database."""
        self._session.refresh(obj, *args, **kwargs)

    async def delete(self, obj):
        """Delete object."""
        self._session.delete(obj)

    async def get(self, entity, ident, *args, **kwargs):
        """Get entity by primary key (async-compatible wrapper)."""
        return self._session.get(entity, ident, *args, **kwargs)

    def add(self, obj):
        """Add object to session."""
        self._session.add(obj)

    async def close(self):
        """Close session."""
        self._session.close()

    def __getattr__(self, name):
        """Proxy attribute access to underlying session."""
        return getattr(self._session, name)


def override_get_db() -> Generator[Session, None, None]:
    """Override database dependency for tests."""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
async def async_db_session(db: Session) -> AsyncGenerator[AsyncSessionWrapper, None]:
    """Provide async-compatible session wrapper for analytics tests."""
    yield AsyncSessionWrapper(db)


@pytest.fixture(scope="function")
def db() -> Generator[Session, None, None]:
    """
    Create a fresh database for each test.

    Creates all tables, yields a session, then drops all tables.
    """
    if TEST_SCHEMA:
        with engine.begin() as conn:
            conn.exec_driver_sql(f'SET search_path TO "{TEST_SCHEMA}"')
            Base.metadata.create_all(bind=conn, tables=TEST_TABLES)
            versioning_manager.metadata.create_all(bind=conn, tables=VERSIONING_TABLES)
    else:
        Base.metadata.create_all(bind=engine, tables=TEST_TABLES)
        versioning_manager.metadata.create_all(bind=engine, tables=VERSIONING_TABLES)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        if TEST_SCHEMA:
            with engine.begin() as conn:
                conn.exec_driver_sql(f'SET search_path TO "{TEST_SCHEMA}"')
                versioning_manager.metadata.drop_all(
                    bind=conn, tables=VERSIONING_TABLES
                )
                Base.metadata.drop_all(bind=conn, tables=TEST_TABLES)
        else:
            versioning_manager.metadata.drop_all(bind=engine, tables=VERSIONING_TABLES)
            Base.metadata.drop_all(bind=engine, tables=TEST_TABLES)


@pytest.fixture(scope="function")
def client(db: Session) -> Generator[TestClient, None, None]:
    """
    Create a test client with database dependency override.

    Overrides both sync and async database dependencies to use
    the same in-memory SQLite database for tests, wrapped for async
    compatibility.
    """
    # Override sync session
    app.dependency_overrides[get_db] = lambda: db

    # Create async-compatible wrapper
    async_wrapper = AsyncSessionWrapper(db)

    # Override async session with wrapped session
    async def get_async_db_override() -> AsyncGenerator[Any, None]:
        yield async_wrapper

    app.dependency_overrides[get_async_db] = get_async_db_override

    # Disable rate limiting in tests
    from app.api.routes.auth import rate_limit_login, rate_limit_register

    app.dependency_overrides[rate_limit_login] = lambda: None
    app.dependency_overrides[rate_limit_register] = lambda: None

    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def admin_user(db: Session) -> User:
    """Create an admin user for authenticated tests."""
    user = User(
        id=uuid4(),
        username="testadmin",
        email="testadmin@test.org",
        hashed_password=get_password_hash("testpass123"),
        role="admin",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def auth_headers(client: TestClient, admin_user: User) -> dict:
    """Get authentication headers for API requests."""
    response = client.post(
        "/api/v1/auth/login/json",
        json={"username": "testadmin", "password": "testpass123"},
    )
    if response.status_code == 200:
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    return {}


@pytest.fixture
def authed_client(client: TestClient, auth_headers: dict) -> TestClient:
    """Return a client with admin auth headers attached."""
    client.headers.update(auth_headers)
    return client


# ============================================================================
# Sample Data Fixtures
# ============================================================================


@pytest.fixture
def sample_resident(db: Session) -> Person:
    """Create a sample resident."""
    resident = Person(
        id=uuid4(),
        name="Dr. Jane Smith",
        type="resident",
        email="jane.smith@hospital.org",
        pgy_level=2,
    )
    db.add(resident)
    db.commit()
    db.refresh(resident)
    return resident


@pytest.fixture
def sample_faculty(db: Session) -> Person:
    """Create a sample faculty member."""
    faculty = Person(
        id=uuid4(),
        name="Dr. John Doe",
        type="faculty",
        email="john.doe@hospital.org",
        performs_procedures=True,
        specialties=["Sports Medicine", "Primary Care"],
    )
    db.add(faculty)
    db.commit()
    db.refresh(faculty)
    return faculty


@pytest.fixture
def sample_residents(db: Session) -> list[Person]:
    """Create multiple sample residents (one per PGY level)."""
    residents = []
    for pgy in range(1, 4):
        resident = Person(
            id=uuid4(),
            name=f"Dr. Resident PGY{pgy}",
            type="resident",
            email=f"resident{pgy}@hospital.org",
            pgy_level=pgy,
        )
        db.add(resident)
        residents.append(resident)
    db.commit()
    for r in residents:
        db.refresh(r)
    return residents


@pytest.fixture
def sample_faculty_members(db: Session) -> list[Person]:
    """Create multiple sample faculty members."""
    faculty = []
    for i in range(1, 4):
        fac = Person(
            id=uuid4(),
            name=f"Dr. Faculty {i}",
            type="faculty",
            email=f"faculty{i}@hospital.org",
            performs_procedures=(i == 1),
            specialties=["General"],
        )
        db.add(fac)
        faculty.append(fac)
    db.commit()
    for f in faculty:
        db.refresh(f)
    return faculty


@pytest.fixture
def sample_rotation_template(db: Session) -> RotationTemplate:
    """Create a sample rotation template."""
    template = RotationTemplate(
        id=uuid4(),
        name="Sports Medicine Clinic",
        rotation_type="outpatient",
        abbreviation="SM",
        clinic_location="Building A",
        max_residents=4,
        supervision_required=True,
        max_supervision_ratio=4,
    )
    db.add(template)
    db.commit()
    db.refresh(template)
    return template


@pytest.fixture
def sample_block(db: Session) -> Block:
    """Create a sample block for today AM."""
    block = Block(
        id=uuid4(),
        date=date.today(),
        time_of_day="AM",
        block_number=1,
        is_weekend=False,
        is_holiday=False,
    )
    db.add(block)
    db.commit()
    db.refresh(block)
    return block


@pytest.fixture
def sample_blocks(db: Session) -> list[Block]:
    """Create blocks for one week (AM and PM)."""
    blocks = []
    start_date = date.today()

    for i in range(7):
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
            db.add(block)
            blocks.append(block)

    db.commit()
    for b in blocks:
        db.refresh(b)
    return blocks


@pytest.fixture
def sample_absence(db: Session, sample_resident: Person) -> Absence:
    """Create a sample absence for a resident."""
    absence = Absence(
        id=uuid4(),
        person_id=sample_resident.id,
        start_date=date.today() + timedelta(days=7),
        end_date=date.today() + timedelta(days=14),
        absence_type="vacation",
        notes="Annual leave",
    )
    db.add(absence)
    db.commit()
    db.refresh(absence)
    return absence


@pytest.fixture
def sample_assignment(
    db: Session,
    sample_resident: Person,
    sample_block: Block,
    sample_rotation_template: RotationTemplate,
) -> Assignment:
    """Create a sample assignment."""
    assignment = Assignment(
        id=uuid4(),
        block_id=sample_block.id,
        person_id=sample_resident.id,
        rotation_template_id=sample_rotation_template.id,
        role="primary",
    )
    db.add(assignment)
    db.commit()
    db.refresh(assignment)
    return assignment


# ============================================================================
# Helper Functions
# ============================================================================


def create_test_person(
    db: Session,
    name: str = "Test Person",
    person_type: str = "resident",
    pgy_level: int = None,
    email: str = None,
) -> Person:
    """Helper to create a person in tests."""
    person = Person(
        id=uuid4(),
        name=name,
        type=person_type,
        email=email or f"{name.lower().replace(' ', '.')}@test.org",
        pgy_level=pgy_level if person_type == "resident" else None,
    )
    db.add(person)
    db.commit()
    db.refresh(person)
    return person


def create_test_blocks(
    db: Session,
    start_date: date,
    days: int = 7,
) -> list[Block]:
    """Helper to create blocks for a date range.

    Block numbers use Thursday-Wednesday alignment via get_block_number_for_date.
    """
    blocks = []
    for i in range(days):
        current_date = start_date + timedelta(days=i)
        # Use Thursday-Wednesday aligned block number calculation
        block_number, _ = get_block_number_for_date(current_date)
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
    db.commit()
    return blocks
