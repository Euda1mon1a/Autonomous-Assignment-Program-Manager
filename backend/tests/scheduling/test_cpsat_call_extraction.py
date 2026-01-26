from datetime import date
from uuid import uuid4

from app.scheduling.constraints import ConstraintManager, SchedulingContext
from app.scheduling.constraints.call_coverage import OvernightCallCoverageConstraint
from app.scheduling.solvers import CPSATSolver


class MockPerson:
    def __init__(
        self, id=None, name="Test Person", person_type="resident", pgy_level=1
    ):
        self.id = id or uuid4()
        self.name = name
        self.type = person_type
        self.pgy_level = pgy_level


class MockBlock:
    def __init__(self, id=None, block_date=None, time_of_day="AM", is_weekend=False):
        self.id = id or uuid4()
        self.date = block_date or date.today()
        self.time_of_day = time_of_day
        self.is_weekend = is_weekend


class MockTemplate:
    def __init__(
        self,
        id=None,
        name="Test Rotation",
        max_residents=None,
        requires_procedure_credential=False,
    ):
        self.id = id or uuid4()
        self.name = name
        self.max_residents = max_residents
        self.requires_procedure_credential = requires_procedure_credential


def test_cpsat_call_extraction_includes_weekend_block() -> None:
    sunday = date(2024, 1, 7)  # Sunday
    monday = date(2024, 1, 8)  # Monday

    weekend_block = MockBlock(block_date=sunday, is_weekend=True)
    workday_block = MockBlock(block_date=monday, is_weekend=False)

    resident = MockPerson(name="Resident", person_type="resident", pgy_level=1)
    faculty = MockPerson(name="Faculty", person_type="faculty", pgy_level=None)
    template = MockTemplate(name="Clinic")

    context = SchedulingContext(
        residents=[resident],
        faculty=[faculty],
        blocks=[weekend_block, workday_block],
        templates=[template],
        start_date=sunday,
        end_date=monday,
    )

    for person in [resident, faculty]:
        context.availability[person.id] = {
            weekend_block.id: {"available": True, "replacement": None},
            workday_block.id: {"available": True, "replacement": None},
        }

    context.call_eligible_faculty = [faculty]
    context.call_eligible_faculty_idx = {faculty.id: 0}

    manager = ConstraintManager().add(OvernightCallCoverageConstraint())
    solver = CPSATSolver(constraint_manager=manager, timeout_seconds=5, num_workers=1)

    result = solver.solve(context)

    assert result.success is True
    call_blocks = {block_id for _, block_id, _ in result.call_assignments}
    assert weekend_block.id in call_blocks
