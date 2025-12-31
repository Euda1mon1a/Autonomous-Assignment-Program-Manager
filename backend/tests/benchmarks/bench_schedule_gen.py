"""
Schedule Generation Benchmarks

Benchmark the most computationally expensive operations.

Run:
    pytest tests/benchmarks/bench_schedule_gen.py --benchmark-only
    pytest tests/benchmarks/bench_schedule_gen.py --benchmark-compare
"""

import pytest
from datetime import date, timedelta
from sqlalchemy.ext.asyncio import AsyncSession

from app.scheduling.engine import ScheduleGenerator
from app.scheduling.algorithms.greedy import GreedyScheduler
from app.scheduling.algorithms.constraint_programming import ConstraintProgrammingScheduler
from app.models.person import Person
from app.models.rotation import Rotation
from app.models.block import Block


@pytest.mark.benchmark
class TestScheduleGenerationBenchmarks:
    """Benchmark schedule generation performance"""

    @pytest.fixture
    async def schedule_data(self, db: AsyncSession):
        """Create test data for schedule generation"""
        # Create 20 persons
        persons = []
        for i in range(20):
            person = Person(
                first_name=f"Person{i}",
                last_name="Test",
                email=f"person{i}@benchmark.com",
                role="RESIDENT" if i < 15 else "FACULTY",
                pgy_year=(i % 3) + 1 if i < 15 else None,
                is_active=True
            )
            db.add(person)
            persons.append(person)

        # Create 5 rotations
        rotations = []
        rotation_types = ["CLINIC", "INPATIENT", "PROCEDURES", "CALL", "ADMIN"]
        for i, rot_type in enumerate(rotation_types):
            rotation = Rotation(
                name=f"{rot_type} Rotation",
                rotation_type=rot_type,
                is_active=True,
                requires_supervision=rot_type in ["PROCEDURES", "INPATIENT"],
                max_consecutive_days=7 if rot_type == "CALL" else 14
            )
            db.add(rotation)
            rotations.append(rotation)

        # Create blocks for 30 days
        blocks = []
        start_date = date.today()
        for i in range(30):
            current_date = start_date + timedelta(days=i)
            for session_type in ["AM", "PM"]:
                block = Block(
                    date=current_date,
                    session_type=session_type,
                    is_holiday=False,
                    is_weekend=current_date.weekday() >= 5
                )
                db.add(block)
                blocks.append(block)

        await db.commit()

        for person in persons:
            await db.refresh(person)
        for rotation in rotations:
            await db.refresh(rotation)
        for block in blocks:
            await db.refresh(block)

        return {
            "persons": persons,
            "rotations": rotations,
            "blocks": blocks,
            "start_date": start_date,
            "end_date": start_date + timedelta(days=29)
        }

    def test_greedy_scheduler_small(self, benchmark, db: AsyncSession, schedule_data):
        """Benchmark greedy scheduler with small dataset (20 persons, 30 days)"""
        scheduler = GreedyScheduler()

        def run_scheduler():
            # Note: In real benchmarks, you'd need to handle async properly
            # This is a simplified example
            return scheduler.generate_schedule(
                persons=schedule_data["persons"][:10],  # 10 persons
                rotations=schedule_data["rotations"],
                blocks=schedule_data["blocks"][:20],  # 10 days
                start_date=schedule_data["start_date"],
                end_date=schedule_data["start_date"] + timedelta(days=9)
            )

        result = benchmark(run_scheduler)
        assert result is not None

    def test_greedy_scheduler_medium(self, benchmark, schedule_data):
        """Benchmark greedy scheduler with medium dataset (20 persons, 30 days)"""
        scheduler = GreedyScheduler()

        def run_scheduler():
            return scheduler.generate_schedule(
                persons=schedule_data["persons"],
                rotations=schedule_data["rotations"],
                blocks=schedule_data["blocks"],
                start_date=schedule_data["start_date"],
                end_date=schedule_data["end_date"]
            )

        result = benchmark(run_scheduler)
        assert result is not None

    @pytest.mark.slow
    def test_constraint_programming_small(self, benchmark, schedule_data):
        """Benchmark CP solver with small dataset"""
        scheduler = ConstraintProgrammingScheduler()

        def run_scheduler():
            return scheduler.generate_schedule(
                persons=schedule_data["persons"][:10],
                rotations=schedule_data["rotations"],
                blocks=schedule_data["blocks"][:20],
                start_date=schedule_data["start_date"],
                end_date=schedule_data["start_date"] + timedelta(days=9),
                max_runtime_seconds=10
            )

        result = benchmark.pedantic(run_scheduler, rounds=3, iterations=1)
        assert result is not None

    def test_schedule_validation(self, benchmark, schedule_data):
        """Benchmark schedule validation"""
        from app.scheduling.acgme_validator import ACGMEValidator

        validator = ACGMEValidator()

        # Create a simple schedule to validate
        assignments = []
        # ... populate assignments ...

        def run_validation():
            return validator.validate_schedule(assignments)

        result = benchmark(run_validation)
        assert result is not None


@pytest.mark.benchmark
class TestConstraintBenchmarks:
    """Benchmark individual constraint checks"""

    def test_80_hour_rule_check(self, benchmark):
        """Benchmark 80-hour rule validation"""
        from app.scheduling.constraints.acgme import check_80_hour_rule

        # Create test data
        work_hours = [70, 75, 78, 80, 72, 68, 74]  # 7 days of work hours

        result = benchmark(check_80_hour_rule, work_hours)
        assert isinstance(result, bool)

    def test_one_in_seven_rule_check(self, benchmark):
        """Benchmark 1-in-7 rule validation"""
        from app.scheduling.constraints.acgme import check_one_in_seven_rule

        # Create test data - 7 days of work indicators
        work_days = [True, True, True, True, True, True, False]

        result = benchmark(check_one_in_seven_rule, work_days)
        assert isinstance(result, bool)

    def test_supervision_ratio_check(self, benchmark):
        """Benchmark supervision ratio validation"""
        from app.scheduling.constraints.acgme import check_supervision_ratio

        result = benchmark(
            check_supervision_ratio,
            residents_count=10,
            faculty_count=3,
            pgy_level=1
        )
        assert isinstance(result, bool)


@pytest.mark.benchmark
class TestDatabaseBenchmarks:
    """Benchmark database operations"""

    @pytest.mark.asyncio
    async def test_bulk_assignment_create(self, benchmark, db: AsyncSession):
        """Benchmark bulk assignment creation"""
        from app.models.assignment import Assignment

        # Create test assignments
        assignments_data = [
            Assignment(
                person_id=f"person-{i}",
                block_id=f"block-{i}",
                rotation_id=f"rotation-{i % 5}",
                status="SCHEDULED"
            )
            for i in range(100)
        ]

        async def create_assignments():
            db.add_all(assignments_data)
            await db.commit()

        # Note: pytest-benchmark doesn't directly support async
        # You'd need to use a sync wrapper or pytest-benchmark-asyncio
        # This is a simplified example
        result = benchmark.pedantic(
            lambda: create_assignments(),
            rounds=5,
            iterations=1
        )

    @pytest.mark.asyncio
    async def test_complex_query(self, benchmark, db: AsyncSession):
        """Benchmark complex query with joins"""
        from sqlalchemy import select
        from app.models.assignment import Assignment
        from app.models.person import Person
        from app.models.rotation import Rotation

        async def run_query():
            stmt = (
                select(Assignment)
                .join(Person)
                .join(Rotation)
                .where(Person.role == "RESIDENT")
                .where(Rotation.rotation_type == "CLINIC")
                .limit(100)
            )
            result = await db.execute(stmt)
            return result.scalars().all()

        result = benchmark.pedantic(
            lambda: run_query(),
            rounds=10,
            iterations=1
        )


@pytest.mark.benchmark
class TestResilienceBenchmarks:
    """Benchmark resilience calculations"""

    def test_utilization_calculation(self, benchmark):
        """Benchmark utilization calculation"""
        from app.resilience.metrics import calculate_utilization

        # Sample data
        capacity = 100
        demand = 75

        result = benchmark(calculate_utilization, capacity, demand)
        assert 0 <= result <= 1

    def test_n_minus_one_analysis(self, benchmark):
        """Benchmark N-1 contingency analysis"""
        from app.resilience.contingency import analyze_n_minus_one

        # Sample schedule data
        schedule = {
            "assignments": [],  # Populate with test data
            "persons": [],
            "rotations": []
        }

        result = benchmark.pedantic(
            lambda: analyze_n_minus_one(schedule),
            rounds=5,
            iterations=1
        )

    def test_burnout_risk_calculation(self, benchmark):
        """Benchmark burnout risk calculation"""
        from app.resilience.burnout import calculate_burnout_risk

        # Sample work history
        work_hours = [70, 75, 78, 80, 72, 68, 74, 76, 79, 80, 73, 71]

        result = benchmark(calculate_burnout_risk, work_hours)
        assert 0 <= result <= 1


# Benchmark configuration
def pytest_configure(config):
    """Configure pytest-benchmark"""
    config.addinivalue_line(
        "markers",
        "benchmark: mark test as a benchmark"
    )
    config.addinivalue_line(
        "markers",
        "slow: mark test as slow (expensive benchmarks)"
    )
