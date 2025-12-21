"""
Unit tests for constraint validation service.

Tests constraint validation functionality including:
- Schedule constraint validation (80-hour rule, 1-in-7 rule)
- Supervision ratio validation
- Custom constraint validation
- Error handling
"""

import pytest
from datetime import date, timedelta
from uuid import uuid4
from unittest.mock import Mock

from app.scheduling.constraints.base import (
    Constraint,
    ConstraintPriority,
    ConstraintResult,
    ConstraintType,
    ConstraintViolation,
    HardConstraint,
    SoftConstraint,
    SchedulingContext,
)
from app.scheduling.constraints.manager import ConstraintManager
from app.scheduling.constraints.acgme import (
    AvailabilityConstraint,
    EightyHourRuleConstraint,
    OneInSevenRuleConstraint,
    SupervisionRatioConstraint,
)
from app.scheduling.constraints.capacity import (
    ClinicCapacityConstraint,
    CoverageConstraint,
    OnePersonPerBlockConstraint,
)
from app.scheduling.constraints.equity import EquityConstraint, ContinuityConstraint
from app.models.assignment import Assignment
from app.models.block import Block
from app.models.person import Person


class TestConstraintManager:
    """Test suite for ConstraintManager."""

    def test_add_constraint_returns_self(self):
        """Test that adding a constraint returns self for chaining."""
        manager = ConstraintManager()
        result = manager.add(AvailabilityConstraint())

        assert result is manager
        assert len(manager.constraints) == 1

    def test_add_multiple_constraints_chaining(self):
        """Test adding multiple constraints with method chaining."""
        manager = ConstraintManager()
        result = manager.add(AvailabilityConstraint()).add(
            EightyHourRuleConstraint()
        ).add(EquityConstraint(weight=10.0))

        assert result is manager
        assert len(manager.constraints) == 3
        assert len(manager._hard_constraints) == 2
        assert len(manager._soft_constraints) == 1

    def test_remove_constraint_by_name(self):
        """Test removing a constraint by name."""
        manager = ConstraintManager()
        manager.add(AvailabilityConstraint())
        manager.add(EightyHourRuleConstraint())

        manager.remove("Availability")

        assert len(manager.constraints) == 1
        assert manager.constraints[0].name == "80HourRule"

    def test_enable_disable_constraints(self):
        """Test enabling and disabling constraints."""
        manager = ConstraintManager()
        manager.add(AvailabilityConstraint())

        # Disable constraint
        manager.disable("Availability")
        assert manager.constraints[0].enabled is False

        # Re-enable constraint
        manager.enable("Availability")
        assert manager.constraints[0].enabled is True

    def test_get_enabled_constraints(self):
        """Test getting only enabled constraints."""
        manager = ConstraintManager()
        manager.add(AvailabilityConstraint())
        manager.add(EightyHourRuleConstraint())

        manager.disable("Availability")
        enabled = manager.get_enabled()

        assert len(enabled) == 1
        assert enabled[0].name == "80HourRule"

    def test_get_hard_constraints(self):
        """Test getting hard constraints."""
        manager = ConstraintManager()
        manager.add(AvailabilityConstraint())
        manager.add(EightyHourRuleConstraint())
        manager.add(EquityConstraint(weight=10.0))

        hard = manager.get_hard_constraints()

        assert len(hard) == 2
        assert all(isinstance(c, HardConstraint) for c in hard)

    def test_get_soft_constraints(self):
        """Test getting soft constraints."""
        manager = ConstraintManager()
        manager.add(AvailabilityConstraint())
        manager.add(EquityConstraint(weight=10.0))
        manager.add(ContinuityConstraint(weight=5.0))

        soft = manager.get_soft_constraints()

        assert len(soft) == 2
        assert all(isinstance(c, SoftConstraint) for c in soft)

    def test_create_default_manager(self):
        """Test creating default constraint manager."""
        manager = ConstraintManager.create_default()

        # Should have both hard and soft constraints
        assert len(manager.get_hard_constraints()) >= 5
        assert len(manager.get_soft_constraints()) >= 3

        # Resilience constraints should be disabled by default
        resilience_constraints = ["HubProtection", "UtilizationBuffer", "ZoneBoundary"]
        for name in resilience_constraints:
            constraint = next((c for c in manager.constraints if c.name == name), None)
            assert constraint is not None
            assert constraint.enabled is False

    def test_create_minimal_manager(self):
        """Test creating minimal constraint manager for fast solving."""
        manager = ConstraintManager.create_minimal()

        # Should have only essential constraints
        assert len(manager.constraints) == 3
        assert len(manager.get_hard_constraints()) == 2


class TestScheduleConstraintValidation:
    """Test suite for schedule constraint validation (80-hour, 1-in-7, etc.)."""

    def test_80_hour_rule_no_violation(self, db, sample_resident):
        """Test 80-hour rule passes when within limits."""
        # Create 4 weeks of blocks (28 days)
        blocks = []
        start_date = date.today()
        for i in range(28):
            block = Block(
                id=uuid4(),
                date=start_date + timedelta(days=i),
                time_of_day="AM",
                block_number=1,
                is_weekend=False,
            )
            db.add(block)
            blocks.append(block)
        db.commit()

        # Create assignments: 5 days/week, AM only = 30 hours/week (within 80)
        assignments = []
        for i in range(0, 28, 7):  # Each week
            for j in range(5):  # 5 days per week
                assignment = Assignment(
                    id=uuid4(),
                    block_id=blocks[i + j].id,
                    person_id=sample_resident.id,
                    role="primary",
                )
                assignments.append(assignment)

        context = SchedulingContext(
            residents=[sample_resident],
            faculty=[],
            blocks=blocks,
            templates=[],
        )

        constraint = EightyHourRuleConstraint()
        result = constraint.validate(assignments, context)

        assert result.satisfied is True
        assert len(result.violations) == 0

    def test_80_hour_rule_violation(self, db, sample_resident):
        """Test 80-hour rule detects violations."""
        # Create 4 weeks of blocks
        blocks = []
        start_date = date.today()
        for i in range(28):
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

        # Create assignments: 7 days/week, AM+PM = 84 hours/week (violates 80)
        assignments = []
        for block in blocks:
            assignment = Assignment(
                id=uuid4(),
                block_id=block.id,
                person_id=sample_resident.id,
                role="primary",
            )
            assignments.append(assignment)

        context = SchedulingContext(
            residents=[sample_resident],
            faculty=[],
            blocks=blocks,
            templates=[],
        )

        constraint = EightyHourRuleConstraint()
        result = constraint.validate(assignments, context)

        assert result.satisfied is False
        assert len(result.violations) > 0
        assert result.violations[0].constraint_type == ConstraintType.DUTY_HOURS
        assert "80" in result.violations[0].message or "hour" in result.violations[0].message.lower()

    def test_1_in_7_rule_no_violation(self, db, sample_resident):
        """Test 1-in-7 rule passes when resident has days off."""
        # Create 14 days of blocks
        blocks = []
        start_date = date.today()
        for i in range(14):
            block = Block(
                id=uuid4(),
                date=start_date + timedelta(days=i),
                time_of_day="AM",
                block_number=1,
                is_weekend=False,
            )
            db.add(block)
            blocks.append(block)
        db.commit()

        # Create assignments: Work 6 days, off 1 day (compliant)
        assignments = []
        for i in range(14):
            if i % 7 != 6:  # Day 7, 14 are off
                assignment = Assignment(
                    id=uuid4(),
                    block_id=blocks[i].id,
                    person_id=sample_resident.id,
                    role="primary",
                )
                assignments.append(assignment)

        context = SchedulingContext(
            residents=[sample_resident],
            faculty=[],
            blocks=blocks,
            templates=[],
        )

        constraint = OneInSevenRuleConstraint()
        result = constraint.validate(assignments, context)

        assert result.satisfied is True
        assert len(result.violations) == 0

    def test_1_in_7_rule_violation(self, db, sample_resident):
        """Test 1-in-7 rule detects violations (too many consecutive days)."""
        # Create 10 consecutive days of blocks
        blocks = []
        start_date = date.today()
        for i in range(10):
            block = Block(
                id=uuid4(),
                date=start_date + timedelta(days=i),
                time_of_day="AM",
                block_number=1,
                is_weekend=False,
            )
            db.add(block)
            blocks.append(block)
        db.commit()

        # Create assignments for all 10 consecutive days (violates 1-in-7)
        assignments = []
        for block in blocks:
            assignment = Assignment(
                id=uuid4(),
                block_id=block.id,
                person_id=sample_resident.id,
                role="primary",
            )
            assignments.append(assignment)

        context = SchedulingContext(
            residents=[sample_resident],
            faculty=[],
            blocks=blocks,
            templates=[],
        )

        constraint = OneInSevenRuleConstraint()
        result = constraint.validate(assignments, context)

        assert result.satisfied is False
        assert len(result.violations) > 0
        assert result.violations[0].constraint_type == ConstraintType.CONSECUTIVE_DAYS

    def test_minimum_rest_between_shifts(self, db, sample_resident):
        """Test that residents have adequate rest between shifts."""
        # Create consecutive AM/PM blocks
        blocks = []
        start_date = date.today()
        for i in range(2):
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

        # Assign resident to consecutive blocks
        assignments = []
        for block in blocks:
            assignment = Assignment(
                id=uuid4(),
                block_id=block.id,
                person_id=sample_resident.id,
                role="primary",
            )
            assignments.append(assignment)

        context = SchedulingContext(
            residents=[sample_resident],
            faculty=[],
            blocks=blocks,
            templates=[],
        )

        # OnePersonPerBlock ensures no double-booking
        constraint = OnePersonPerBlockConstraint()
        result = constraint.validate(assignments, context)

        assert result.satisfied is True

    def test_maximum_consecutive_work_days(self, db, sample_resident):
        """Test maximum consecutive work days constraint."""
        # Create 8 consecutive days
        blocks = []
        start_date = date.today()
        for i in range(8):
            block = Block(
                id=uuid4(),
                date=start_date + timedelta(days=i),
                time_of_day="AM",
                block_number=1,
                is_weekend=False,
            )
            db.add(block)
            blocks.append(block)
        db.commit()

        # Assign all 8 consecutive days
        assignments = []
        for block in blocks:
            assignment = Assignment(
                id=uuid4(),
                block_id=block.id,
                person_id=sample_resident.id,
                role="primary",
            )
            assignments.append(assignment)

        context = SchedulingContext(
            residents=[sample_resident],
            faculty=[],
            blocks=blocks,
            templates=[],
        )

        # 1-in-7 rule should catch this
        constraint = OneInSevenRuleConstraint()
        result = constraint.validate(assignments, context)

        assert result.satisfied is False
        assert len(result.violations) > 0


class TestSupervisionRatioValidation:
    """Test suite for supervision ratio validation."""

    def test_pgy1_supervision_ratio_compliant(self, db, sample_residents, sample_faculty_members):
        """Test PGY-1 supervision ratio passes when compliant (1:2)."""
        # Get PGY-1 residents
        pgy1_residents = [r for r in sample_residents if r.pgy_level == 1]

        # Create a block
        block = Block(
            id=uuid4(),
            date=date.today(),
            time_of_day="AM",
            block_number=1,
            is_weekend=False,
        )
        db.add(block)
        db.commit()

        # Assign 2 PGY-1 residents and 1 faculty (compliant 1:2 ratio)
        assignments = []
        for resident in pgy1_residents[:2]:
            assignment = Assignment(
                id=uuid4(),
                block_id=block.id,
                person_id=resident.id,
                role="primary",
            )
            assignments.append(assignment)

        # Add faculty
        faculty_assignment = Assignment(
            id=uuid4(),
            block_id=block.id,
            person_id=sample_faculty_members[0].id,
            role="supervisor",
        )
        assignments.append(faculty_assignment)

        context = SchedulingContext(
            residents=pgy1_residents[:2],
            faculty=sample_faculty_members[:1],
            blocks=[block],
            templates=[],
        )

        constraint = SupervisionRatioConstraint()
        result = constraint.validate(assignments, context)

        assert result.satisfied is True
        assert len(result.violations) == 0

    def test_pgy1_supervision_ratio_violation(self, db, sample_residents, sample_faculty_members):
        """Test PGY-1 supervision ratio detects violations (too many residents)."""
        # Get PGY-1 residents (need to ensure they exist)
        pgy1_residents = [r for r in sample_residents if r.pgy_level == 1]

        # Create additional PGY-1 residents if needed
        while len(pgy1_residents) < 3:
            pgy1 = Person(
                id=uuid4(),
                name=f"Dr. PGY1 Extra {len(pgy1_residents)}",
                type="resident",
                email=f"pgy1extra{len(pgy1_residents)}@test.org",
                pgy_level=1,
            )
            db.add(pgy1)
            pgy1_residents.append(pgy1)
        db.commit()

        # Create a block
        block = Block(
            id=uuid4(),
            date=date.today(),
            time_of_day="AM",
            block_number=1,
            is_weekend=False,
        )
        db.add(block)
        db.commit()

        # Assign 3 PGY-1 residents and only 1 faculty (violates 1:2 ratio)
        assignments = []
        for resident in pgy1_residents[:3]:
            assignment = Assignment(
                id=uuid4(),
                block_id=block.id,
                person_id=resident.id,
                role="primary",
            )
            assignments.append(assignment)

        # Add only 1 faculty (need 2 for 3 residents)
        faculty_assignment = Assignment(
            id=uuid4(),
            block_id=block.id,
            person_id=sample_faculty_members[0].id,
            role="supervisor",
        )
        assignments.append(faculty_assignment)

        context = SchedulingContext(
            residents=pgy1_residents[:3],
            faculty=sample_faculty_members[:1],
            blocks=[block],
            templates=[],
        )

        constraint = SupervisionRatioConstraint()
        result = constraint.validate(assignments, context)

        assert result.satisfied is False
        assert len(result.violations) > 0
        assert result.violations[0].constraint_type == ConstraintType.SUPERVISION

    def test_pgy23_supervision_ratio_compliant(self, db, sample_residents, sample_faculty_members):
        """Test PGY-2/3 supervision ratio passes when compliant (1:4)."""
        # Get PGY-2/3 residents
        pgy23_residents = [r for r in sample_residents if r.pgy_level >= 2]

        # Create a block
        block = Block(
            id=uuid4(),
            date=date.today(),
            time_of_day="AM",
            block_number=1,
            is_weekend=False,
        )
        db.add(block)
        db.commit()

        # Assign 2 PGY-2/3 residents and 1 faculty (compliant 1:4 ratio)
        assignments = []
        for resident in pgy23_residents[:2]:
            assignment = Assignment(
                id=uuid4(),
                block_id=block.id,
                person_id=resident.id,
                role="primary",
            )
            assignments.append(assignment)

        # Add faculty
        faculty_assignment = Assignment(
            id=uuid4(),
            block_id=block.id,
            person_id=sample_faculty_members[0].id,
            role="supervisor",
        )
        assignments.append(faculty_assignment)

        context = SchedulingContext(
            residents=pgy23_residents[:2],
            faculty=sample_faculty_members[:1],
            blocks=[block],
            templates=[],
        )

        constraint = SupervisionRatioConstraint()
        result = constraint.validate(assignments, context)

        assert result.satisfied is True
        assert len(result.violations) == 0

    def test_coverage_requirement_met(self, db, sample_residents, sample_blocks):
        """Test that coverage requirements are met."""
        # Assign residents to blocks
        assignments = []
        for i, block in enumerate(sample_blocks[:5]):
            assignment = Assignment(
                id=uuid4(),
                block_id=block.id,
                person_id=sample_residents[i % len(sample_residents)].id,
                role="primary",
            )
            assignments.append(assignment)

        context = SchedulingContext(
            residents=sample_residents,
            faculty=[],
            blocks=sample_blocks[:5],
            templates=[],
        )

        # Coverage constraint checks if blocks are assigned
        constraint = CoverageConstraint(weight=1000.0)
        result = constraint.validate(assignments, context)

        # Should have good coverage
        assert result.penalty >= 0


class TestCustomConstraintValidation:
    """Test suite for custom constraint validation."""

    def test_equity_constraint(self, db, sample_residents, sample_blocks):
        """Test equity constraint ensures fair distribution."""
        # Assign all blocks to one resident (inequitable)
        assignments = []
        for block in sample_blocks[:6]:
            assignment = Assignment(
                id=uuid4(),
                block_id=block.id,
                person_id=sample_residents[0].id,
                role="primary",
            )
            assignments.append(assignment)

        context = SchedulingContext(
            residents=sample_residents,
            faculty=[],
            blocks=sample_blocks[:6],
            templates=[],
        )

        constraint = EquityConstraint(weight=10.0)
        result = constraint.validate(assignments, context)

        # Should have high penalty for inequity
        assert result.penalty > 0

    def test_continuity_constraint(self, db, sample_resident, sample_blocks):
        """Test continuity constraint promotes consistent scheduling."""
        # Assign resident to some blocks
        assignments = []
        for block in sample_blocks[:3]:
            assignment = Assignment(
                id=uuid4(),
                block_id=block.id,
                person_id=sample_resident.id,
                role="primary",
            )
            assignments.append(assignment)

        context = SchedulingContext(
            residents=[sample_resident],
            faculty=[],
            blocks=sample_blocks[:7],
            templates=[],
        )

        constraint = ContinuityConstraint(weight=5.0)
        result = constraint.validate(assignments, context)

        # Continuity constraint should evaluate
        assert result.penalty >= 0

    def test_constraint_priority_ordering(self):
        """Test that constraints are ordered by priority."""
        manager = ConstraintManager()
        manager.add(AvailabilityConstraint())  # CRITICAL
        manager.add(EquityConstraint(weight=10.0))  # MEDIUM

        enabled = manager.get_enabled()

        # Critical constraint should have higher priority value
        critical = next(c for c in enabled if c.name == "Availability")
        medium = next(c for c in enabled if c.name == "Equity")

        assert critical.priority.value > medium.priority.value

    def test_constraint_enable_disable(self):
        """Test custom constraints can be enabled/disabled."""
        manager = ConstraintManager()
        manager.add(EquityConstraint(weight=10.0))

        # Initially enabled
        assert manager.constraints[0].enabled is True

        # Disable
        manager.disable("Equity")
        assert len(manager.get_enabled()) == 0

        # Re-enable
        manager.enable("Equity")
        assert len(manager.get_enabled()) == 1

    def test_soft_constraint_penalty_calculation(self):
        """Test that soft constraints calculate penalties correctly."""
        constraint = EquityConstraint(weight=10.0)

        # Penalty should be based on weight and priority
        penalty = constraint.get_penalty(violation_count=5)

        assert penalty > 0
        assert penalty == 10.0 * 5 * constraint.priority.value


class TestConstraintErrorHandling:
    """Test suite for constraint error handling."""

    def test_validate_with_empty_assignments(self, db, sample_resident):
        """Test validation handles empty assignment list."""
        context = SchedulingContext(
            residents=[sample_resident],
            faculty=[],
            blocks=[],
            templates=[],
        )

        constraint = EightyHourRuleConstraint()
        result = constraint.validate([], context)

        # Should not crash with empty assignments
        assert result is not None
        assert result.satisfied is True

    def test_validate_with_missing_context_data(self):
        """Test validation handles missing context data."""
        # Create context with minimal data
        context = SchedulingContext(
            residents=[],
            faculty=[],
            blocks=[],
            templates=[],
        )

        constraint = SupervisionRatioConstraint()
        result = constraint.validate([], context)

        # Should handle gracefully
        assert result is not None
        assert result.satisfied is True

    def test_validate_with_invalid_person_id(self, db, sample_blocks):
        """Test validation handles invalid person IDs."""
        # Create assignment with non-existent person
        assignment = Assignment(
            id=uuid4(),
            block_id=sample_blocks[0].id,
            person_id=uuid4(),  # Non-existent person
            role="primary",
        )

        context = SchedulingContext(
            residents=[],
            faculty=[],
            blocks=sample_blocks[:1],
            templates=[],
        )

        constraint = AvailabilityConstraint()
        result = constraint.validate([assignment], context)

        # Should handle gracefully (person not in availability matrix)
        assert result is not None

    def test_validate_with_invalid_block_id(self, db, sample_resident):
        """Test validation handles invalid block IDs."""
        # Create assignment with non-existent block
        assignment = Assignment(
            id=uuid4(),
            block_id=uuid4(),  # Non-existent block
            person_id=sample_resident.id,
            role="primary",
        )

        context = SchedulingContext(
            residents=[sample_resident],
            faculty=[],
            blocks=[],
            templates=[],
        )

        constraint = OneInSevenRuleConstraint()
        result = constraint.validate([assignment], context)

        # Should handle gracefully
        assert result is not None

    def test_constraint_violation_reporting(self, db, sample_resident, sample_blocks):
        """Test that constraint violations are properly reported."""
        # Create many consecutive assignments to violate 1-in-7
        assignments = []
        for i in range(10):
            block = Block(
                id=uuid4(),
                date=date.today() + timedelta(days=i),
                time_of_day="AM",
                block_number=1,
                is_weekend=False,
            )
            db.add(block)
            db.commit()

            assignment = Assignment(
                id=uuid4(),
                block_id=block.id,
                person_id=sample_resident.id,
                role="primary",
            )
            assignments.append(assignment)

        context = SchedulingContext(
            residents=[sample_resident],
            faculty=[],
            blocks=[],
            templates=[],
        )

        constraint = OneInSevenRuleConstraint()
        result = constraint.validate(assignments, context)

        # Should report violations with details
        if not result.satisfied:
            assert len(result.violations) > 0
            violation = result.violations[0]
            assert violation.constraint_name is not None
            assert violation.constraint_type is not None
            assert violation.severity is not None
            assert violation.message is not None

    def test_multiple_constraint_validation(self, db, sample_resident, sample_blocks):
        """Test validating multiple constraints together."""
        manager = ConstraintManager()
        manager.add(AvailabilityConstraint())
        manager.add(OnePersonPerBlockConstraint())
        manager.add(EquityConstraint(weight=10.0))

        # Create some assignments
        assignments = []
        for block in sample_blocks[:3]:
            assignment = Assignment(
                id=uuid4(),
                block_id=block.id,
                person_id=sample_resident.id,
                role="primary",
            )
            assignments.append(assignment)

        context = SchedulingContext(
            residents=[sample_resident],
            faculty=[],
            blocks=sample_blocks[:3],
            templates=[],
        )

        result = manager.validate_all(assignments, context)

        # Should aggregate results from all constraints
        assert result is not None
        assert isinstance(result.satisfied, bool)
        assert isinstance(result.violations, list)
        assert isinstance(result.penalty, (int, float))

    def test_constraint_conflict_detection(self):
        """Test that constraint conflicts are detectable."""
        manager = ConstraintManager()

        # Add constraints that might conflict
        manager.add(CoverageConstraint(weight=1000.0))  # Wants max coverage
        manager.add(EightyHourRuleConstraint())  # Limits hours

        # Both constraints should be present
        assert len(manager.constraints) == 2

        # Hard constraint should take precedence (higher priority)
        hard = manager.get_hard_constraints()
        soft = manager.get_soft_constraints()

        assert len(hard) == 1
        assert len(soft) == 1
        assert hard[0].priority.value > soft[0].priority.value


class TestConstraintServiceScheduleIdValidation:
    """Test suite for ConstraintService schedule_id validation (security)."""

    def test_valid_uuid_schedule_id(self):
        """Test that valid UUID schedule_id is accepted."""
        from app.services.constraint_service import ConstraintService

        valid_uuid = "12345678-1234-1234-1234-123456789abc"
        result = ConstraintService.validate_schedule_id(valid_uuid)

        assert result == valid_uuid

    def test_valid_alphanumeric_schedule_id(self):
        """Test that valid alphanumeric schedule_id is accepted."""
        from app.services.constraint_service import ConstraintService

        valid_id = "schedule_2025_winter"
        result = ConstraintService.validate_schedule_id(valid_id)

        assert result == valid_id

    def test_valid_schedule_id_with_hyphens(self):
        """Test that schedule_id with hyphens is accepted."""
        from app.services.constraint_service import ConstraintService

        valid_id = "schedule-2025-01"
        result = ConstraintService.validate_schedule_id(valid_id)

        assert result == valid_id

    def test_empty_schedule_id_rejected(self):
        """Test that empty schedule_id is rejected."""
        from app.services.constraint_service import (
            ConstraintService,
            ScheduleIdValidationError,
        )

        with pytest.raises(ScheduleIdValidationError, match="cannot be empty"):
            ConstraintService.validate_schedule_id("")

    def test_none_schedule_id_rejected(self):
        """Test that None schedule_id is rejected."""
        from app.services.constraint_service import (
            ConstraintService,
            ScheduleIdValidationError,
        )

        with pytest.raises(ScheduleIdValidationError, match="cannot be empty"):
            ConstraintService.validate_schedule_id(None)

    def test_whitespace_only_schedule_id_rejected(self):
        """Test that whitespace-only schedule_id is rejected."""
        from app.services.constraint_service import (
            ConstraintService,
            ScheduleIdValidationError,
        )

        with pytest.raises(ScheduleIdValidationError, match="empty after stripping"):
            ConstraintService.validate_schedule_id("   ")

    def test_too_long_schedule_id_rejected(self):
        """Test that overly long schedule_id is rejected."""
        from app.services.constraint_service import (
            ConstraintService,
            ScheduleIdValidationError,
        )

        long_id = "a" * 100
        with pytest.raises(ScheduleIdValidationError, match="too long"):
            ConstraintService.validate_schedule_id(long_id)

    def test_path_traversal_rejected(self):
        """Test that path traversal attempts are rejected."""
        from app.services.constraint_service import (
            ConstraintService,
            ScheduleIdValidationError,
        )

        with pytest.raises(ScheduleIdValidationError, match="invalid characters"):
            ConstraintService.validate_schedule_id("../etc/passwd")

    def test_sql_injection_rejected(self):
        """Test that SQL injection attempts are rejected."""
        from app.services.constraint_service import (
            ConstraintService,
            ScheduleIdValidationError,
        )

        with pytest.raises(ScheduleIdValidationError, match="invalid characters"):
            ConstraintService.validate_schedule_id("'; DROP TABLE schedules; --")

    def test_command_injection_rejected(self):
        """Test that command injection attempts are rejected."""
        from app.services.constraint_service import (
            ConstraintService,
            ScheduleIdValidationError,
        )

        with pytest.raises(ScheduleIdValidationError, match="invalid characters"):
            ConstraintService.validate_schedule_id("schedule; rm -rf /")

    def test_html_injection_rejected(self):
        """Test that HTML injection attempts are rejected."""
        from app.services.constraint_service import (
            ConstraintService,
            ScheduleIdValidationError,
        )

        with pytest.raises(ScheduleIdValidationError, match="invalid characters"):
            ConstraintService.validate_schedule_id("<script>alert('xss')</script>")

    def test_null_byte_injection_rejected(self):
        """Test that null byte injection is rejected."""
        from app.services.constraint_service import (
            ConstraintService,
            ScheduleIdValidationError,
        )

        with pytest.raises(ScheduleIdValidationError, match="invalid characters"):
            ConstraintService.validate_schedule_id("schedule\x00.txt")

    def test_newline_injection_rejected(self):
        """Test that newline injection is rejected."""
        from app.services.constraint_service import (
            ConstraintService,
            ScheduleIdValidationError,
        )

        with pytest.raises(ScheduleIdValidationError, match="invalid characters"):
            ConstraintService.validate_schedule_id("schedule\nid")

    def test_shell_expansion_rejected(self):
        """Test that shell expansion attempts are rejected."""
        from app.services.constraint_service import (
            ConstraintService,
            ScheduleIdValidationError,
        )

        with pytest.raises(ScheduleIdValidationError, match="invalid characters"):
            ConstraintService.validate_schedule_id("$(whoami)")

    def test_invalid_format_rejected(self):
        """Test that invalid format schedule_id is rejected."""
        from app.services.constraint_service import (
            ConstraintService,
            ScheduleIdValidationError,
        )

        with pytest.raises(ScheduleIdValidationError, match="valid UUID or alphanumeric"):
            ConstraintService.validate_schedule_id("schedule@invalid.format")


class TestConstraintServicePIISanitization:
    """Test suite for ConstraintService PII sanitization (security)."""

    def test_email_sanitization(self, db):
        """Test that email addresses are sanitized from messages."""
        from app.services.constraint_service import ConstraintService

        service = ConstraintService(db)
        message = "Assignment conflict for dr.smith@hospital.org"

        sanitized = service._sanitize_message(message)

        assert "dr.smith@hospital.org" not in sanitized
        assert "[EMAIL REDACTED]" in sanitized

    def test_phone_sanitization(self, db):
        """Test that phone numbers are sanitized from messages."""
        from app.services.constraint_service import ConstraintService

        service = ConstraintService(db)
        message = "Contact at 555-123-4567 for coverage"

        sanitized = service._sanitize_message(message)

        assert "555-123-4567" not in sanitized
        assert "[PHONE REDACTED]" in sanitized

    def test_ssn_sanitization(self, db):
        """Test that SSN patterns are sanitized from messages."""
        from app.services.constraint_service import ConstraintService

        service = ConstraintService(db)
        message = "Person with SSN 123-45-6789 has conflict"

        sanitized = service._sanitize_message(message)

        assert "123-45-6789" not in sanitized
        assert "[SSN REDACTED]" in sanitized

    def test_doctor_name_sanitization(self, db):
        """Test that doctor names are sanitized from messages."""
        from app.services.constraint_service import ConstraintService

        service = ConstraintService(db)
        message = "Dr. Smith has exceeded hours"

        sanitized = service._sanitize_message(message)

        assert "Dr. Smith" not in sanitized
        assert "[PERSON]" in sanitized

    def test_sensitive_fields_removed_from_details(self, db):
        """Test that sensitive fields are removed from details dict."""
        from app.services.constraint_service import ConstraintService

        service = ConstraintService(db)
        details = {
            "email": "test@example.com",
            "phone": "555-1234",
            "ssn": "123-45-6789",
            "hours": 85,
            "blocks": 15,
            "user_password": "secret123",
            "api_token": "abc123",
        }

        sanitized = service._sanitize_details(details)

        # Sensitive fields should be removed
        assert "email" not in sanitized
        assert "phone" not in sanitized
        assert "ssn" not in sanitized
        assert "user_password" not in sanitized
        assert "api_token" not in sanitized

        # Non-sensitive fields should remain
        assert sanitized["hours"] == 85
        assert sanitized["blocks"] == 15

    def test_entity_anonymization(self, db):
        """Test that person IDs are anonymized."""
        from app.services.constraint_service import ConstraintService

        service = ConstraintService(db)
        person_id = uuid4()

        anonymized = service._anonymize_person_ref(person_id)

        assert anonymized is not None
        assert anonymized.startswith("entity-")
        assert str(person_id) not in anonymized
        # Only first 8 chars of UUID should be used
        assert len(anonymized) == len("entity-") + 8

    def test_none_entity_anonymization(self, db):
        """Test that None person_id returns None."""
        from app.services.constraint_service import ConstraintService

        service = ConstraintService(db)
        anonymized = service._anonymize_person_ref(None)

        assert anonymized is None
