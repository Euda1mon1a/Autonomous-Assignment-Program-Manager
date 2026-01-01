"""Shared fixtures and utilities for service tests."""

import pytest
import pytest_asyncio
from datetime import date, timedelta
from uuid import uuid4

from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.core.security import get_password_hash
from app.db.base import Base
from app.models.assignment import Assignment
from app.models.absence import Absence
from app.models.block import Block
from app.models.call_assignment import CallAssignment
from app.models.person import Person
from app.models.rotation_template import RotationTemplate
from app.models.user import User


# ============================================================================
# Async Database Fixtures (for async service tests)
# ============================================================================

# Use in-memory SQLite with async support
ASYNC_TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

# Create async engine for tests
async_test_engine = create_async_engine(
    ASYNC_TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
    echo=False,
)

# Create async session factory
AsyncTestingSessionLocal = async_sessionmaker(
    async_test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


@pytest_asyncio.fixture
async def async_db() -> AsyncSession:
    """
    Create a fresh async database for each test.

    Creates all tables, yields an async session, then drops all tables.
    """
    # Create all tables
    async with async_test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Create session
    async with AsyncTestingSessionLocal() as session:
        yield session

    # Drop all tables
    async with async_test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


# ============================================================================
# Fixture Factories
# ============================================================================


class PersonFactory:
    """Factory for creating Person instances for testing."""

    @staticmethod
    def create_resident(
        db: Session,
        name: str = "Dr. Resident",
        pgy_level: int = 1,
        email: str = None,
    ) -> Person:
        """Create a resident person."""
        person = Person(
            id=uuid4(),
            name=name,
            type="resident",
            email=email or f"{name.lower().replace(' ', '.')}@hospital.org",
            pgy_level=pgy_level,
        )
        db.add(person)
        db.commit()
        db.refresh(person)
        return person

    @staticmethod
    def create_faculty(
        db: Session,
        name: str = "Dr. Faculty",
        email: str = None,
        performs_procedures: bool = True,
    ) -> Person:
        """Create a faculty person."""
        person = Person(
            id=uuid4(),
            name=name,
            type="faculty",
            email=email or f"{name.lower().replace(' ', '.')}@hospital.org",
            performs_procedures=performs_procedures,
        )
        db.add(person)
        db.commit()
        db.refresh(person)
        return person

    @staticmethod
    def create_multiple_residents(db: Session, count: int = 3) -> list[Person]:
        """Create multiple residents."""
        residents = []
        for i in range(count):
            resident = PersonFactory.create_resident(
                db,
                name=f"Dr. Resident {i + 1}",
                pgy_level=(i % 3) + 1,
            )
            residents.append(resident)
        return residents

    @staticmethod
    def create_multiple_faculty(db: Session, count: int = 3) -> list[Person]:
        """Create multiple faculty members."""
        faculty = []
        for i in range(count):
            fac = PersonFactory.create_faculty(
                db,
                name=f"Dr. Faculty {i + 1}",
                performs_procedures=(i == 0),
            )
            faculty.append(fac)
        return faculty


class BlockFactory:
    """Factory for creating Block instances for testing."""

    @staticmethod
    def create_block(
        db: Session,
        test_date: date = None,
        time_of_day: str = "AM",
        is_weekend: bool = False,
    ) -> Block:
        """Create a single block."""
        if test_date is None:
            test_date = date.today()

        block = Block(
            id=uuid4(),
            date=test_date,
            time_of_day=time_of_day,
            block_number=1,
            is_weekend=is_weekend,
            is_holiday=False,
        )
        db.add(block)
        db.commit()
        db.refresh(block)
        return block

    @staticmethod
    def create_blocks_for_week(db: Session, start_date: date = None) -> list[Block]:
        """Create blocks for one week (AM and PM each day)."""
        if start_date is None:
            start_date = date.today()

        blocks = []
        for i in range(7):
            current_date = start_date + timedelta(days=i)
            is_weekend = current_date.weekday() >= 5

            for time_of_day in ["AM", "PM"]:
                block = Block(
                    id=uuid4(),
                    date=current_date,
                    time_of_day=time_of_day,
                    block_number=1,
                    is_weekend=is_weekend,
                    is_holiday=False,
                )
                db.add(block)
                blocks.append(block)

        db.commit()
        return blocks

    @staticmethod
    def create_blocks_for_month(db: Session, start_date: date = None) -> list[Block]:
        """Create blocks for one month (AM and PM each day)."""
        if start_date is None:
            start_date = date.today()

        blocks = []
        for i in range(30):
            current_date = start_date + timedelta(days=i)
            is_weekend = current_date.weekday() >= 5

            for time_of_day in ["AM", "PM"]:
                block = Block(
                    id=uuid4(),
                    date=current_date,
                    time_of_day=time_of_day,
                    block_number=1,
                    is_weekend=is_weekend,
                    is_holiday=False,
                )
                db.add(block)
                blocks.append(block)

        db.commit()
        return blocks


class RotationTemplateFactory:
    """Factory for creating RotationTemplate instances for testing."""

    @staticmethod
    def create_template(
        db: Session,
        name: str = "Test Rotation",
        activity_type: str = "outpatient",
        abbreviation: str = "TR",
    ) -> RotationTemplate:
        """Create a rotation template."""
        template = RotationTemplate(
            id=uuid4(),
            name=name,
            activity_type=activity_type,
            abbreviation=abbreviation,
            max_residents=4,
            supervision_required=True,
        )
        db.add(template)
        db.commit()
        db.refresh(template)
        return template

    @staticmethod
    def create_multiple_templates(
        db: Session, count: int = 3
    ) -> list[RotationTemplate]:
        """Create multiple rotation templates."""
        templates = []
        activity_types = ["outpatient", "inpatient", "call", "procedure"]

        for i in range(count):
            template = RotationTemplate(
                id=uuid4(),
                name=f"Rotation {i + 1}",
                activity_type=activity_types[i % len(activity_types)],
                abbreviation=f"ROT{i + 1}",
                max_residents=4,
                supervision_required=True,
            )
            db.add(template)
            templates.append(template)

        db.commit()
        return templates


class AssignmentFactory:
    """Factory for creating Assignment instances for testing."""

    @staticmethod
    def create_assignment(
        db: Session,
        person: Person,
        block: Block,
        rotation_template: RotationTemplate,
        role: str = "primary",
    ) -> Assignment:
        """Create a single assignment."""
        assignment = Assignment(
            id=uuid4(),
            person_id=person.id,
            block_id=block.id,
            rotation_template_id=rotation_template.id,
            role=role,
        )
        db.add(assignment)
        db.commit()
        db.refresh(assignment)
        return assignment

    @staticmethod
    def create_bulk_assignments(
        db: Session,
        people: list[Person],
        blocks: list[Block],
        rotation_template: RotationTemplate,
    ) -> list[Assignment]:
        """Create multiple assignments."""
        assignments = []
        for i, person in enumerate(people):
            for j, block in enumerate(blocks[:7]):  # Assign to first week
                assignment = Assignment(
                    id=uuid4(),
                    person_id=person.id,
                    block_id=block.id,
                    rotation_template_id=rotation_template.id,
                    role="primary",
                )
                db.add(assignment)
                assignments.append(assignment)

        db.commit()
        return assignments


class CallAssignmentFactory:
    """Factory for creating CallAssignment instances for testing (async)."""

    @staticmethod
    async def create_call_assignment(
        db: AsyncSession,
        person: Person,
        call_date: date = None,
        call_type: str = "overnight",
        is_weekend: bool = False,
        is_holiday: bool = False,
    ) -> CallAssignment:
        """Create a call assignment."""
        if call_date is None:
            call_date = date.today()

        call_assignment = CallAssignment(
            id=uuid4(),
            date=call_date,
            person_id=person.id,
            call_type=call_type,
            is_weekend=is_weekend,
            is_holiday=is_holiday,
        )
        db.add(call_assignment)
        await db.flush()
        await db.commit()
        await db.refresh(call_assignment)
        return call_assignment


class AbsenceFactory:
    """Factory for creating Absence instances for testing."""

    @staticmethod
    def create_absence(
        db: Session,
        person: Person,
        absence_type: str = "vacation",
        start_offset: int = 7,
        duration: int = 7,
    ) -> Absence:
        """Create an absence."""
        start_date = date.today() + timedelta(days=start_offset)
        end_date = start_date + timedelta(days=duration)

        absence = Absence(
            id=uuid4(),
            person_id=person.id,
            start_date=start_date,
            end_date=end_date,
            absence_type=absence_type,
            notes=f"Test {absence_type}",
        )
        db.add(absence)
        db.commit()
        db.refresh(absence)
        return absence


class UserFactory:
    """Factory for creating User instances for testing."""

    @staticmethod
    def create_user(
        db: Session,
        username: str = "testuser",
        email: str = "test@test.org",
        password: str = "Test@Pass123",
        role: str = "coordinator",
        is_admin: bool = False,
    ) -> User:
        """Create a user."""
        user = User(
            id=uuid4(),
            username=username,
            email=email,
            hashed_password=get_password_hash(password),
            role=role,
            is_active=True,
            is_admin=is_admin,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def create_admin_user(db: Session) -> User:
        """Create an admin user."""
        return UserFactory.create_user(
            db,
            username="admin",
            email="admin@test.org",
            is_admin=True,
        )


# ============================================================================
# Pytest Fixtures
# ============================================================================


@pytest.fixture
def person_factory():
    """Provide PersonFactory."""
    return PersonFactory()


@pytest.fixture
def block_factory():
    """Provide BlockFactory."""
    return BlockFactory()


@pytest.fixture
def rotation_template_factory():
    """Provide RotationTemplateFactory."""
    return RotationTemplateFactory()


@pytest.fixture
def assignment_factory():
    """Provide AssignmentFactory."""
    return AssignmentFactory()


@pytest.fixture
def absence_factory():
    """Provide AbsenceFactory."""
    return AbsenceFactory()


@pytest.fixture
def call_assignment_factory():
    """Provide CallAssignmentFactory."""
    return CallAssignmentFactory()


@pytest.fixture
def user_factory():
    """Provide UserFactory."""
    return UserFactory()


# ============================================================================
# Convenience Fixtures (pre-created test data)
# ============================================================================


@pytest.fixture
def residents_list(db: Session) -> list[Person]:
    """Create a list of residents for testing."""
    return PersonFactory.create_multiple_residents(db, count=5)


@pytest.fixture
def faculty_list(db: Session) -> list[Person]:
    """Create a list of faculty for testing."""
    return PersonFactory.create_multiple_faculty(db, count=5)


@pytest.fixture
def blocks_for_month(db: Session) -> list[Block]:
    """Create blocks for a full month."""
    return BlockFactory.create_blocks_for_month(db)


@pytest.fixture
def templates_list(db: Session) -> list[RotationTemplate]:
    """Create multiple rotation templates."""
    return RotationTemplateFactory.create_multiple_templates(db, count=4)


@pytest.fixture
def test_admin_user(db: Session) -> User:
    """Create test admin user."""
    return UserFactory.create_admin_user(db)


# ============================================================================
# Test Data Helpers
# ============================================================================


def create_populated_schedule(
    db: Session,
    num_residents: int = 3,
    num_days: int = 7,
) -> dict:
    """
    Create a complete test schedule with residents, blocks, templates, and assignments.

    Returns a dict with all created objects for convenient access in tests.
    """
    residents = PersonFactory.create_multiple_residents(db, count=num_residents)
    start_date = date.today() + timedelta(days=30)

    # Create blocks
    blocks = []
    for i in range(num_days):
        for time_of_day in ["AM", "PM"]:
            block = Block(
                id=uuid4(),
                date=start_date + timedelta(days=i),
                time_of_day=time_of_day,
                block_number=1,
                is_weekend=False,
            )
            db.add(block)
            blocks.append(block)
    db.commit()

    # Create rotation templates
    templates = RotationTemplateFactory.create_multiple_templates(db, count=2)

    # Create assignments
    assignments = AssignmentFactory.create_bulk_assignments(
        db, residents, blocks, templates[0]
    )

    return {
        "residents": residents,
        "blocks": blocks,
        "templates": templates,
        "assignments": assignments,
    }


@pytest.fixture
def populated_schedule(db: Session):
    """Fixture providing a complete test schedule."""
    return create_populated_schedule(db)
