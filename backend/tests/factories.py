"""FactoryBoy factories for test data generation."""
import factory
from datetime import date, timedelta
from uuid import uuid4

from app.models.person import Person
from app.models.block import Block
from app.models.assignment import Assignment
from app.models.rotation_template import RotationTemplate
from app.models.absence import Absence


class PersonFactory(factory.Factory):
    """Factory for Person model."""

    class Meta:
        model = Person

    id = factory.LazyFunction(uuid4)
    name = factory.Faker('name')
    email = factory.LazyAttribute(lambda o: f"{o.name.lower().replace(' ', '.')}@hospital.org")
    type = "resident"
    pgy_level = factory.Iterator([1, 2, 3])

    class Params:
        faculty = factory.Trait(
            type="faculty",
            pgy_level=None,
            performs_procedures=True,
            specialties=["General"],
        )


class ResidentFactory(PersonFactory):
    """Factory specifically for residents."""
    type = "resident"
    pgy_level = factory.Iterator([1, 2, 3])


class FacultyFactory(PersonFactory):
    """Factory specifically for faculty."""
    type = "faculty"
    pgy_level = None
    performs_procedures = factory.Faker('boolean')
    specialties = factory.LazyFunction(lambda: ["Sports Medicine"])


class BlockFactory(factory.Factory):
    """Factory for Block model."""

    class Meta:
        model = Block

    id = factory.LazyFunction(uuid4)
    date = factory.LazyFunction(date.today)
    time_of_day = factory.Iterator(["AM", "PM"])
    block_number = 1
    is_weekend = factory.LazyAttribute(lambda o: o.date.weekday() >= 5)
    is_holiday = False


class RotationTemplateFactory(factory.Factory):
    """Factory for RotationTemplate model."""

    class Meta:
        model = RotationTemplate

    id = factory.LazyFunction(uuid4)
    name = factory.Iterator(["Sports Medicine", "Primary Care", "Inpatient", "ICU"])
    activity_type = factory.Iterator(["clinic", "inpatient", "call"])
    abbreviation = factory.LazyAttribute(lambda o: o.name[:2].upper())
    leave_eligible = True  # Most rotations allow scheduled leave
    max_residents = 4
    supervision_required = True
    max_supervision_ratio = 4

    class Params:
        # Trait for coverage/inpatient rotations that don't allow leave
        coverage = factory.Trait(
            name="FMIT",
            activity_type="inpatient",
            leave_eligible=False,
        )


class AssignmentFactory(factory.Factory):
    """Factory for Assignment model."""

    class Meta:
        model = Assignment

    id = factory.LazyFunction(uuid4)
    block_id = factory.LazyFunction(uuid4)
    person_id = factory.LazyFunction(uuid4)
    rotation_template_id = factory.LazyFunction(uuid4)
    role = "primary"


class AbsenceFactory(factory.Factory):
    """Factory for Absence model."""

    class Meta:
        model = Absence

    id = factory.LazyFunction(uuid4)
    person_id = factory.LazyFunction(uuid4)
    start_date = factory.LazyFunction(lambda: date.today() + timedelta(days=7))
    end_date = factory.LazyAttribute(lambda o: o.start_date + timedelta(days=7))
    absence_type = factory.Iterator(["vacation", "conference", "sick", "deployment"])
    is_blocking = None  # Auto-determined based on type
    return_date_tentative = False
    created_by_id = None  # Set when admin enters on behalf of someone
    notes = factory.Faker('sentence')

    class Params:
        # Trait for emergency absences (Hawaii default: 10 days, blocking, tentative return)
        emergency = factory.Trait(
            absence_type="emergency_leave",
            end_date=factory.LazyAttribute(lambda o: o.start_date + timedelta(days=10)),
            is_blocking=True,
            return_date_tentative=True,
        )
        # Trait for bereavement (Hawaii default: 10 days for mainland travel)
        bereavement = factory.Trait(
            absence_type="bereavement",
            end_date=factory.LazyAttribute(lambda o: o.start_date + timedelta(days=10)),
            is_blocking=True,
            return_date_tentative=True,
        )


# Helper functions for complex scenarios
def create_week_of_blocks(start_date: date = None) -> list[Block]:
    """Create AM and PM blocks for a full week."""
    start = start_date or date.today()
    blocks = []
    for day_offset in range(7):
        block_date = start + timedelta(days=day_offset)
        for tod in ["AM", "PM"]:
            blocks.append(BlockFactory(
                date=block_date,
                time_of_day=tod,
                is_weekend=block_date.weekday() >= 5,
            ))
    return blocks


def create_residency_cohort(size: int = 10) -> list[Person]:
    """Create a cohort of residents with mixed PGY levels."""
    residents = []
    for i in range(size):
        pgy = (i % 3) + 1  # Distribute across PGY 1-3
        residents.append(ResidentFactory(pgy_level=pgy))
    return residents


def create_faculty_pool(size: int = 5) -> list[Person]:
    """Create a pool of faculty members."""
    return [FacultyFactory() for _ in range(size)]
