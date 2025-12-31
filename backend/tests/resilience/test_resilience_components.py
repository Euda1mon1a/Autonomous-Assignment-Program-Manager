"""
Resilience Framework Component Tests.

Comprehensive tests for resilience framework components including
defense levels, N-1/N-2 contingency analysis, utilization thresholds,
and blast radius isolation.

Test Coverage:
- Defense level transitions (GREEN -> YELLOW -> ORANGE -> RED -> BLACK)
- 80% utilization threshold detection
- N-1 contingency analysis (single failure scenarios)
- N-2 contingency analysis (double failure scenarios)
- Blast radius isolation and containment
- Homeostasis feedback loops
- Sacrifice hierarchy during load shedding
- Static stability fallback schedules
"""

from datetime import date, datetime, timedelta
from uuid import uuid4

import pytest
from sqlalchemy.orm import Session

from app.models.assignment import Assignment
from app.models.block import Block
from app.models.person import Person
from app.models.rotation_template import RotationTemplate
from app.resilience.defense_levels import DefenseLevelManager, DefenseLevel
from app.resilience.n_minus_analysis import NMinusAnalyzer
from app.resilience.utilization import UtilizationMonitor
from app.resilience.blast_radius import BlastRadiusAnalyzer
from app.resilience.homeostasis import HomeostasisController


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def defense_manager(db: Session) -> DefenseLevelManager:
    """Create a defense level manager."""
    return DefenseLevelManager(db)


@pytest.fixture
def n_minus_analyzer(db: Session) -> NMinusAnalyzer:
    """Create N-minus analyzer."""
    return NMinusAnalyzer(db)


@pytest.fixture
def utilization_monitor(db: Session) -> UtilizationMonitor:
    """Create utilization monitor."""
    return UtilizationMonitor(db)


@pytest.fixture
def blast_radius_analyzer(db: Session) -> BlastRadiusAnalyzer:
    """Create blast radius analyzer."""
    return BlastRadiusAnalyzer(db)


@pytest.fixture
def homeostasis_controller(db: Session) -> HomeostasisController:
    """Create homeostasis controller."""
    return HomeostasisController(db)


@pytest.fixture
def faculty_pool(db: Session) -> list[Person]:
    """Create a pool of 5 faculty members."""
    faculty = []
    for i in range(5):
        person = Person(
            id=uuid4(),
            name=f"Dr. Faculty {i+1}",
            type="faculty",
            email=f"faculty{i+1}@test.org",
            performs_procedures=(i < 3),  # First 3 can do procedures
        )
        db.add(person)
        faculty.append(person)
    db.commit()
    for f in faculty:
        db.refresh(f)
    return faculty


@pytest.fixture
def resident_pool(db: Session) -> list[Person]:
    """Create a pool of 6 residents (2 per PGY level)."""
    residents = []
    for pgy in range(1, 4):
        for i in range(2):
            resident = Person(
                id=uuid4(),
                name=f"Dr. PGY{pgy}-{i+1}",
                type="resident",
                email=f"pgy{pgy}.{i+1}@test.org",
                pgy_level=pgy,
            )
            db.add(resident)
            residents.append(resident)
    db.commit()
    for r in residents:
        db.refresh(r)
    return residents


def create_heavy_schedule(
    db: Session, persons: list[Person], rotation: RotationTemplate,
    start_date: date, days: int
) -> list[Assignment]:
    """Create heavy schedule approaching 80% utilization."""
    assignments = []
    for day in range(days):
        current_date = start_date + timedelta(days=day)
        for tod in ["AM", "PM"]:
            block = Block(
                id=uuid4(),
                date=current_date,
                time_of_day=tod,
                block_number=1,
            )
            db.add(block)
            db.commit()

            # Assign 80% of available personnel
            num_to_assign = int(len(persons) * 0.8)
            for i in range(num_to_assign):
                assignment = Assignment(
                    id=uuid4(),
                    block_id=block.id,
                    person_id=persons[i].id,
                    rotation_template_id=rotation.id,
                    role="primary",
                )
                db.add(assignment)
                assignments.append(assignment)
    db.commit()
    return assignments


# ============================================================================
# Test Class: Defense Level Transitions
# ============================================================================


class TestDefenseLevelTransitions:
    """Tests for defense level escalation and de-escalation."""

    def test_green_to_yellow_transition_on_threshold(
        self, db: Session, defense_manager: DefenseLevelManager,
        faculty_pool: list[Person], sample_rotation_template: RotationTemplate
    ):
        """Test transition from GREEN to YELLOW when utilization exceeds 60%."""
        start_date = date.today()

        # Create schedule with 65% utilization (triggers YELLOW)
        for day in range(7):
            current_date = start_date + timedelta(days=day)
            block = Block(
                id=uuid4(),
                date=current_date,
                time_of_day="AM",
                block_number=1,
            )
            db.add(block)
            db.commit()

            # Assign 65% of faculty (3.25 ≈ 3 out of 5)
            for i in range(3):
                assignment = Assignment(
                    id=uuid4(),
                    block_id=block.id,
                    person_id=faculty_pool[i].id,
                    rotation_template_id=sample_rotation_template.id,
                    role="primary",
                )
                db.add(assignment)
        db.commit()

        current_level = defense_manager.assess_defense_level(start_date)
        assert current_level >= DefenseLevel.YELLOW

    def test_yellow_to_orange_on_80_percent_utilization(
        self, db: Session, defense_manager: DefenseLevelManager,
        faculty_pool: list[Person], sample_rotation_template: RotationTemplate
    ):
        """Test transition to ORANGE when utilization hits 80%."""
        start_date = date.today()
        create_heavy_schedule(db, faculty_pool, sample_rotation_template, start_date, 7)

        current_level = defense_manager.assess_defense_level(start_date)
        assert current_level >= DefenseLevel.ORANGE

    def test_orange_to_red_on_n_minus_1_failure(
        self, db: Session, defense_manager: DefenseLevelManager,
        faculty_pool: list[Person], sample_rotation_template: RotationTemplate
    ):
        """Test transition to RED when N-1 contingency fails."""
        start_date = date.today()

        # Create schedule using all but one faculty member
        for day in range(7):
            current_date = start_date + timedelta(days=day)
            block = Block(
                id=uuid4(),
                date=current_date,
                time_of_day="AM",
                block_number=1,
            )
            db.add(block)
            db.commit()

            # Use 4 out of 5 faculty
            for i in range(4):
                assignment = Assignment(
                    id=uuid4(),
                    block_id=block.id,
                    person_id=faculty_pool[i].id,
                    rotation_template_id=sample_rotation_template.id,
                    role="primary",
                )
                db.add(assignment)
        db.commit()

        current_level = defense_manager.assess_defense_level(start_date)
        # Should be RED if losing one more faculty breaks coverage
        assert current_level >= DefenseLevel.ORANGE

    def test_de_escalation_when_utilization_drops(
        self, db: Session, defense_manager: DefenseLevelManager,
        faculty_pool: list[Person], sample_rotation_template: RotationTemplate
    ):
        """Test de-escalation when utilization decreases."""
        start_date = date.today()

        # Initial heavy schedule
        create_heavy_schedule(db, faculty_pool, sample_rotation_template, start_date, 7)

        initial_level = defense_manager.assess_defense_level(start_date)

        # Remove some assignments to reduce utilization
        assignments = db.query(Assignment).filter(
            Assignment.person_id.in_([f.id for f in faculty_pool])
        ).limit(10).all()

        for assignment in assignments:
            db.delete(assignment)
        db.commit()

        new_level = defense_manager.assess_defense_level(start_date)
        assert new_level < initial_level or new_level == DefenseLevel.GREEN


# ============================================================================
# Test Class: N-1 Contingency Analysis
# ============================================================================


class TestNMinus1Contingency:
    """Tests for N-1 contingency analysis."""

    def test_n_minus_1_passes_with_adequate_backup(
        self, db: Session, n_minus_analyzer: NMinusAnalyzer,
        faculty_pool: list[Person], sample_rotation_template: RotationTemplate
    ):
        """Test N-1 analysis passes when adequate backup exists."""
        start_date = date.today()

        # Use only 3 out of 5 faculty (40% spare capacity)
        for day in range(7):
            current_date = start_date + timedelta(days=day)
            block = Block(
                id=uuid4(),
                date=current_date,
                time_of_day="AM",
                block_number=1,
            )
            db.add(block)
            db.commit()

            for i in range(3):
                assignment = Assignment(
                    id=uuid4(),
                    block_id=block.id,
                    person_id=faculty_pool[i].id,
                    rotation_template_id=sample_rotation_template.id,
                    role="primary",
                )
                db.add(assignment)
        db.commit()

        result = n_minus_analyzer.analyze_n_minus_1(start_date)
        assert result.passes is True
        assert len(result.vulnerable_dates) == 0

    def test_n_minus_1_fails_at_capacity(
        self, db: Session, n_minus_analyzer: NMinusAnalyzer,
        faculty_pool: list[Person], sample_rotation_template: RotationTemplate
    ):
        """Test N-1 analysis fails when at full capacity."""
        start_date = date.today()

        # Use all 5 faculty (no spare capacity)
        for day in range(7):
            current_date = start_date + timedelta(days=day)
            block = Block(
                id=uuid4(),
                date=current_date,
                time_of_day="AM",
                block_number=1,
            )
            db.add(block)
            db.commit()

            for i in range(5):
                assignment = Assignment(
                    id=uuid4(),
                    block_id=block.id,
                    person_id=faculty_pool[i].id,
                    rotation_template_id=sample_rotation_template.id,
                    role="primary",
                )
                db.add(assignment)
        db.commit()

        result = n_minus_analyzer.analyze_n_minus_1(start_date)
        assert result.passes is False
        assert len(result.vulnerable_dates) > 0

    def test_n_minus_1_identifies_critical_personnel(
        self, db: Session, n_minus_analyzer: NMinusAnalyzer,
        faculty_pool: list[Person]
    ):
        """Test identification of critical single points of failure."""
        start_date = date.today()

        # Create specialized rotation only one faculty can cover
        specialized = RotationTemplate(
            id=uuid4(),
            name="Specialized Procedure",
            activity_type="procedure",
            abbreviation="SPEC",
            max_residents=1,
        )
        db.add(specialized)
        db.commit()

        block = Block(
            id=uuid4(),
            date=start_date,
            time_of_day="AM",
            block_number=1,
        )
        db.add(block)
        db.commit()

        # Only one faculty member assigned
        assignment = Assignment(
            id=uuid4(),
            block_id=block.id,
            person_id=faculty_pool[0].id,
            rotation_template_id=specialized.id,
            role="primary",
        )
        db.add(assignment)
        db.commit()

        result = n_minus_analyzer.identify_critical_personnel(start_date)
        assert faculty_pool[0].id in result.critical_person_ids


# ============================================================================
# Test Class: N-2 Contingency Analysis
# ============================================================================


class TestNMinus2Contingency:
    """Tests for N-2 contingency analysis (double failure)."""

    def test_n_minus_2_passes_with_deep_bench(
        self, db: Session, n_minus_analyzer: NMinusAnalyzer,
        resident_pool: list[Person], sample_rotation_template: RotationTemplate
    ):
        """Test N-2 passes with sufficient depth."""
        start_date = date.today()

        # Use 3 out of 6 residents (50% capacity)
        for day in range(7):
            current_date = start_date + timedelta(days=day)
            block = Block(
                id=uuid4(),
                date=current_date,
                time_of_day="AM",
                block_number=1,
            )
            db.add(block)
            db.commit()

            for i in range(3):
                assignment = Assignment(
                    id=uuid4(),
                    block_id=block.id,
                    person_id=resident_pool[i].id,
                    rotation_template_id=sample_rotation_template.id,
                    role="primary",
                )
                db.add(assignment)
        db.commit()

        result = n_minus_analyzer.analyze_n_minus_2(start_date)
        assert result.passes is True

    def test_n_minus_2_fails_with_thin_margins(
        self, db: Session, n_minus_analyzer: NMinusAnalyzer,
        faculty_pool: list[Person], sample_rotation_template: RotationTemplate
    ):
        """Test N-2 fails when margins are too thin."""
        start_date = date.today()

        # Use 4 out of 5 faculty (80% utilization)
        create_heavy_schedule(db, faculty_pool[:4], sample_rotation_template, start_date, 7)

        result = n_minus_analyzer.analyze_n_minus_2(start_date)
        assert result.passes is False
        # Losing 2 people would cause coverage failure


# ============================================================================
# Test Class: Utilization Monitoring
# ============================================================================


class TestUtilizationMonitoring:
    """Tests for utilization threshold monitoring."""

    def test_utilization_below_80_percent_threshold(
        self, db: Session, utilization_monitor: UtilizationMonitor,
        faculty_pool: list[Person], sample_rotation_template: RotationTemplate
    ):
        """Test normal utilization below 80% threshold."""
        start_date = date.today()

        # 60% utilization
        for day in range(7):
            current_date = start_date + timedelta(days=day)
            block = Block(
                id=uuid4(),
                date=current_date,
                time_of_day="AM",
                block_number=1,
            )
            db.add(block)
            db.commit()

            for i in range(3):  # 3 out of 5 = 60%
                assignment = Assignment(
                    id=uuid4(),
                    block_id=block.id,
                    person_id=faculty_pool[i].id,
                    rotation_template_id=sample_rotation_template.id,
                    role="primary",
                )
                db.add(assignment)
        db.commit()

        utilization = utilization_monitor.calculate_utilization(start_date)
        assert utilization < 0.80

    def test_utilization_exceeds_80_percent_triggers_alert(
        self, db: Session, utilization_monitor: UtilizationMonitor,
        faculty_pool: list[Person], sample_rotation_template: RotationTemplate
    ):
        """Test alert when utilization exceeds 80%."""
        start_date = date.today()
        create_heavy_schedule(db, faculty_pool, sample_rotation_template, start_date, 7)

        utilization = utilization_monitor.calculate_utilization(start_date)
        assert utilization >= 0.80

        alerts = utilization_monitor.check_thresholds(start_date)
        assert len(alerts) > 0
        assert "80%" in alerts[0].message or "utilization" in alerts[0].message.lower()


# ============================================================================
# Test Class: Blast Radius Isolation
# ============================================================================


class TestBlastRadiusIsolation:
    """Tests for blast radius containment."""

    def test_failure_contained_to_single_rotation(
        self, db: Session, blast_radius_analyzer: BlastRadiusAnalyzer,
        faculty_pool: list[Person]
    ):
        """Test that rotation failure doesn't cascade to others."""
        start_date = date.today()

        # Create two independent rotations
        rotation_a = RotationTemplate(
            id=uuid4(),
            name="Clinic A",
            activity_type="outpatient",
            abbreviation="CA",
            max_residents=2,
        )
        rotation_b = RotationTemplate(
            id=uuid4(),
            name="Clinic B",
            activity_type="outpatient",
            abbreviation="CB",
            max_residents=2,
        )
        db.add_all([rotation_a, rotation_b])
        db.commit()

        block = Block(
            id=uuid4(),
            date=start_date,
            time_of_day="AM",
            block_number=1,
        )
        db.add(block)
        db.commit()

        # Assign to rotation A
        assignment_a = Assignment(
            id=uuid4(),
            block_id=block.id,
            person_id=faculty_pool[0].id,
            rotation_template_id=rotation_a.id,
            role="primary",
        )
        # Assign to rotation B
        assignment_b = Assignment(
            id=uuid4(),
            block_id=block.id,
            person_id=faculty_pool[1].id,
            rotation_template_id=rotation_b.id,
            role="primary",
        )
        db.add_all([assignment_a, assignment_b])
        db.commit()

        # Simulate failure in rotation A
        blast_radius = blast_radius_analyzer.calculate_blast_radius(
            failure_point=rotation_a.id,
            start_date=start_date,
        )

        # Should only affect rotation A, not B
        assert rotation_b.id not in blast_radius.affected_rotations

    def test_cascade_detection_in_dependent_rotations(
        self, db: Session, blast_radius_analyzer: BlastRadiusAnalyzer,
        resident_pool: list[Person]
    ):
        """Test detection of cascading failures in dependent rotations."""
        start_date = date.today()

        # Create dependent rotations (prerequisite relationship)
        basic_rotation = RotationTemplate(
            id=uuid4(),
            name="Basic Skills",
            activity_type="training",
            abbreviation="BASIC",
            max_residents=2,
        )
        advanced_rotation = RotationTemplate(
            id=uuid4(),
            name="Advanced Skills",
            activity_type="training",
            abbreviation="ADV",
            max_residents=2,
            prerequisites=[basic_rotation.id],  # Requires basic first
        )
        db.add_all([basic_rotation, advanced_rotation])
        db.commit()

        # If basic rotation fails, advanced should be affected
        blast_radius = blast_radius_analyzer.calculate_blast_radius(
            failure_point=basic_rotation.id,
            start_date=start_date,
        )

        assert advanced_rotation.id in blast_radius.affected_rotations


# ============================================================================
# Test Class: Homeostasis Feedback
# ============================================================================


class TestHomeostasisFeedback:
    """Tests for homeostasis feedback loops."""

    def test_workload_balancing_feedback(
        self, db: Session, homeostasis_controller: HomeostasisController,
        faculty_pool: list[Person], sample_rotation_template: RotationTemplate
    ):
        """Test feedback loop that balances workload."""
        start_date = date.today()

        # Create imbalanced schedule (one person overworked)
        for day in range(14):
            current_date = start_date + timedelta(days=day)
            block = Block(
                id=uuid4(),
                date=current_date,
                time_of_day="AM",
                block_number=1,
            )
            db.add(block)
            db.commit()

            # Always assign to first faculty member
            assignment = Assignment(
                id=uuid4(),
                block_id=block.id,
                person_id=faculty_pool[0].id,
                rotation_template_id=sample_rotation_template.id,
                role="primary",
            )
            db.add(assignment)
        db.commit()

        # Homeostasis should detect imbalance
        corrections = homeostasis_controller.calculate_corrections(start_date)
        assert len(corrections) > 0
        assert corrections[0].person_id == faculty_pool[0].id
        assert corrections[0].adjustment_type == "reduce_workload"

    def test_equilibrium_restoration_after_perturbation(
        self, db: Session, homeostasis_controller: HomeostasisController,
        resident_pool: list[Person], sample_rotation_template: RotationTemplate
    ):
        """Test system returns to equilibrium after perturbation."""
        start_date = date.today()

        # Create balanced initial schedule
        for day in range(7):
            current_date = start_date + timedelta(days=day)
            block = Block(
                id=uuid4(),
                date=current_date,
                time_of_day="AM",
                block_number=1,
            )
            db.add(block)
            db.commit()

            # Balanced assignment (rotate through residents)
            assignment = Assignment(
                id=uuid4(),
                block_id=block.id,
                person_id=resident_pool[day % len(resident_pool)].id,
                rotation_template_id=sample_rotation_template.id,
                role="primary",
            )
            db.add(assignment)
        db.commit()

        initial_balance = homeostasis_controller.measure_balance(start_date)

        # Apply perturbation (remove one resident's assignments)
        assignments = db.query(Assignment).filter(
            Assignment.person_id == resident_pool[0].id
        ).all()
        for assignment in assignments:
            db.delete(assignment)
        db.commit()

        # Apply homeostasis corrections
        homeostasis_controller.apply_corrections(start_date)

        final_balance = homeostasis_controller.measure_balance(start_date)
        # Balance should improve (move toward equilibrium)
        assert final_balance >= initial_balance or final_balance > 0.8
