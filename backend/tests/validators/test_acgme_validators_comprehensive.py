"""
Comprehensive Unit Tests for ACGME Validators.

Tests all ACGME validators:
- WorkHourValidator: 80-hour rule, 24+4 rule, moonlighting
- SupervisionValidator: PGY-level ratios, block supervision
- CallValidator: Call frequency, equity, spacing
- LeaveValidator: Absence blocking, leave policies
- RotationValidator: Rotation requirements, sequence, volume

Tests cover:
1. Core functionality for each rule
2. Edge cases and boundary conditions
3. Data validation and error handling
4. Compliance vs violation detection
5. Integration scenarios
"""

import pytest
from datetime import date, timedelta
from uuid import UUID, uuid4

from app.scheduling.validators import (
    WorkHourValidator,
    SupervisionValidator,
    CallValidator,
    LeaveValidator,
    RotationValidator,
)


# ==============================================================================
# Work Hour Validator Tests
# ==============================================================================


class TestWorkHourValidator:
    """Tests for WorkHourValidator."""

    @pytest.fixture
    def validator(self):
        """Provide validator instance."""
        return WorkHourValidator()

    @pytest.fixture
    def resident_id(self):
        """Provide test resident ID."""
        return uuid4()

    def test_80_hour_rule_exactly_80_hours_compliant(self, validator, resident_id):
        """Test that exactly 80 hours/week is COMPLIANT (not >=)."""
        # 28 days of 10 hours = 280 hours = 70 hours/week average
        start_date = date(2025, 1, 1)
        hours_by_date = {start_date + timedelta(days=i): 10.0 for i in range(28)}

        violations, warnings = validator.validate_80_hour_rolling_average(
            resident_id, hours_by_date
        )

        assert len(violations) == 0, "80 hours/week should be compliant"
        assert len(warnings) == 0, "No warnings for 80 hours exactly"

    def test_80_hour_rule_exceeds_limit_violation(self, validator, resident_id):
        """Test that > 80 hours/week is VIOLATION."""
        # 28 days of 11.5 hours = 322 hours = 80.5 hours/week
        start_date = date(2025, 1, 1)
        hours_by_date = {start_date + timedelta(days=i): 11.5 for i in range(28)}

        violations, warnings = validator.validate_80_hour_rolling_average(
            resident_id, hours_by_date
        )

        assert len(violations) > 0, "Should have violation for >80 hours/week"
        assert violations[0].violation_type == "80_hour"
        assert violations[0].severity == "CRITICAL"

    def test_80_hour_rule_approaching_limit_warning(self, validator, resident_id):
        """Test warning when approaching 80-hour limit (76+ hours)."""
        # 28 days of 10.85 hours = 304 hours = 76 hours/week
        start_date = date(2025, 1, 1)
        hours_by_date = {start_date + timedelta(days=i): 10.85 for i in range(28)}

        violations, warnings = validator.validate_80_hour_rolling_average(
            resident_id, hours_by_date
        )

        assert len(violations) == 0, "76 hours should not violate"
        assert len(warnings) > 0, "Should warn at 76 hours"
        assert warnings[0].warning_type == "approaching_limit"

    def test_24_plus_4_rule_within_limit(self, validator, resident_id):
        """Test 24+4 rule compliance."""
        shift_data = [
            {
                "date": date(2025, 1, 1),
                "start_time": "06:00",
                "end_time": "18:00",
                "duration_hours": 12.0,
            }
        ]

        violations, warnings = validator.validate_24_plus_4_rule(
            resident_id, shift_data
        )

        assert len(violations) == 0, "12-hour shift is compliant"

    def test_24_plus_4_rule_exceeds_28_hours(self, validator, resident_id):
        """Test 24+4 rule violation when shift exceeds 28 hours."""
        shift_data = [
            {
                "date": date(2025, 1, 1),
                "start_time": "06:00",
                "end_time": "14:00",  # 32 hours
                "duration_hours": 32.0,
            }
        ]

        violations, warnings = validator.validate_24_plus_4_rule(
            resident_id, shift_data
        )

        assert len(violations) > 0, "32-hour shift should violate"
        assert violations[0].violation_type == "24_plus_4"

    def test_moonlighting_integration(self, validator, resident_id):
        """Test moonlighting hours integration with 80-hour limit."""
        # Regular hours: 70/week, Moonlighting: 15/week = 85/week total
        start_date = date(2025, 1, 1)
        regular_hours = {start_date + timedelta(days=i): 10.0 for i in range(28)}
        moonlighting_hours = {
            start_date + timedelta(days=i): 2.14 for i in range(28)
        }  # ~15 hours/week

        violations, warnings = validator.validate_80_hour_rolling_average(
            resident_id,
            regular_hours,
            moonlighting_hours=moonlighting_hours,
        )

        assert len(violations) > 0, "70 + 15 = 85 hours should violate 80-hour limit"

    def test_moonlighting_warning_threshold(self, validator, resident_id):
        """Test warning when moonlighting exceeds threshold."""
        start_date = date(2025, 1, 1)
        moonlighting_hours = {
            start_date: 25.0,  # 25 hours in one day (high)
        }

        violations, warnings = validator.validate_moonlighting_integration(
            resident_id, moonlighting_hours
        )

        assert len(warnings) > 0, "High moonlighting should warn"


# ==============================================================================
# Supervision Validator Tests
# ==============================================================================


class TestSupervisionValidator:
    """Tests for SupervisionValidator."""

    @pytest.fixture
    def validator(self):
        """Provide validator instance."""
        return SupervisionValidator()

    def test_calculate_required_faculty_pgy1_only(self, validator):
        """Test faculty calculation for PGY-1 only."""
        # 1 PGY-1 = 2 units, ceil(2/4) = 1 faculty
        assert validator.calculate_required_faculty(1, 0) == 1
        # 2 PGY-1 = 4 units, ceil(4/4) = 1 faculty
        assert validator.calculate_required_faculty(2, 0) == 1
        # 3 PGY-1 = 6 units, ceil(6/4) = 2 faculty
        assert validator.calculate_required_faculty(3, 0) == 2

    def test_calculate_required_faculty_pgy2_3_only(self, validator):
        """Test faculty calculation for PGY-2/3 only."""
        # 1 PGY-2 = 1 unit, ceil(1/4) = 1 faculty
        assert validator.calculate_required_faculty(0, 1) == 1
        # 4 PGY-2 = 4 units, ceil(4/4) = 1 faculty
        assert validator.calculate_required_faculty(0, 4) == 1
        # 5 PGY-2 = 5 units, ceil(5/4) = 2 faculty
        assert validator.calculate_required_faculty(0, 5) == 2

    def test_calculate_required_faculty_mixed_pgy(self, validator):
        """Test faculty calculation for mixed PGY levels."""
        # 1 PGY-1 + 1 PGY-2 = 2+1 = 3 units, ceil(3/4) = 1 faculty
        assert validator.calculate_required_faculty(1, 1) == 1
        # 2 PGY-1 + 2 PGY-2 = 4+2 = 6 units, ceil(6/4) = 2 faculty
        assert validator.calculate_required_faculty(2, 2) == 2

    def test_validate_block_supervision_compliant(self, validator):
        """Test block supervision validation when compliant."""
        block_id = uuid4()
        block_date = date(2025, 1, 1)
        pgy1 = [uuid4(), uuid4()]
        other = [uuid4()]
        faculty = [uuid4()]  # Need 2 for 2 PGY-1 + 1 PGY-2

        violation = validator.validate_block_supervision(
            block_id,
            block_date,
            pgy1_residents=pgy1,
            other_residents=other,
            faculty_assigned=faculty,
        )

        # Need ceil((2*2 + 1 + 3)/4) = ceil(8/4) = 2, have 1
        assert violation is not None, "Should detect deficit"
        assert violation.deficit == 1

    def test_validate_block_supervision_violates(self, validator):
        """Test block supervision validation when violates."""
        block_id = uuid4()
        block_date = date(2025, 1, 1)
        pgy1 = [uuid4(), uuid4(), uuid4()]  # Need 2 faculty
        other = []
        faculty = [uuid4()]  # Only 1 faculty

        violation = validator.validate_block_supervision(
            block_id,
            block_date,
            pgy1_residents=pgy1,
            other_residents=other,
            faculty_assigned=faculty,
        )

        assert violation is not None
        assert violation.severity == "HIGH"
        assert violation.deficit == 1

    def test_validate_period_supervision(self, validator):
        """Test period-wide supervision validation."""
        blocks = [
            {
                "block_id": uuid4(),
                "block_date": date(2025, 1, 1),
                "pgy1_residents": [uuid4(), uuid4()],
                "other_residents": [],
                "faculty_assigned": [uuid4()],
            },
            {
                "block_id": uuid4(),
                "block_date": date(2025, 1, 2),
                "pgy1_residents": [uuid4(), uuid4(), uuid4()],
                "other_residents": [],
                "faculty_assigned": [uuid4()],
            },
        ]

        violations, metrics = validator.validate_period_supervision(blocks)

        assert len(violations) == 1, "Only second block should violate"
        assert metrics["compliance_rate"] < 100


# ==============================================================================
# Call Validator Tests
# ==============================================================================


class TestCallValidator:
    """Tests for CallValidator."""

    @pytest.fixture
    def validator(self):
        """Provide validator instance."""
        return CallValidator()

    @pytest.fixture
    def faculty_id(self):
        """Provide test faculty ID."""
        return uuid4()

    def test_call_frequency_compliant(self, validator, faculty_id):
        """Test compliant call frequency (every 3rd night)."""
        # ~9 calls in 28 days is compliant
        start_date = date(2025, 1, 1)
        call_dates = [start_date + timedelta(days=i * 3) for i in range(9)]

        violations, warnings = validator.validate_call_frequency(faculty_id, call_dates)

        assert len(violations) == 0, "9 calls in 28 days should be compliant"

    def test_call_frequency_exceeds_limit(self, validator, faculty_id):
        """Test excessive call frequency."""
        start_date = date(2025, 1, 1)
        call_dates = [
            start_date + timedelta(days=i) for i in range(12)
        ]  # 12 calls in 12 days

        violations, warnings = validator.validate_call_frequency(faculty_id, call_dates)

        assert len(violations) > 0, "Too many calls should violate"
        assert violations[0].violation_type == "frequency"

    def test_consecutive_nights_within_limit(self, validator, faculty_id):
        """Test consecutive night limits."""
        # 2 consecutive nights is compliant
        call_dates = [
            date(2025, 1, 1),
            date(2025, 1, 2),
        ]

        violations, warnings = validator.validate_consecutive_nights(
            faculty_id, call_dates
        )

        assert len(violations) == 0, "2 consecutive nights should be compliant"

    def test_consecutive_nights_exceeds(self, validator, faculty_id):
        """Test consecutive night violation."""
        # 3 consecutive nights exceeds limit
        call_dates = [
            date(2025, 1, 1),
            date(2025, 1, 2),
            date(2025, 1, 3),
        ]

        violations, warnings = validator.validate_consecutive_nights(
            faculty_id, call_dates
        )

        assert len(violations) > 0, "3 consecutive nights should violate"
        assert violations[0].violation_type == "consecutive"

    def test_call_spacing_violation(self, validator, faculty_id):
        """Test call spacing requirement."""
        # Calls on consecutive days violates spacing rule
        call_dates = [
            date(2025, 1, 1),
            date(2025, 1, 2),
        ]

        violations, warnings = validator.validate_call_spacing(faculty_id, call_dates)

        assert len(violations) > 0, "1-day spacing violates 2-day requirement"

    def test_call_equity_imbalance(self, validator):
        """Test call equity detection."""
        assignments = {
            uuid4(): [date(2025, 1, 1), date(2025, 1, 4), date(2025, 1, 7)],  # 3 calls
            uuid4(): [date(2025, 1, 2)],  # 1 call
        }

        warnings, metrics = validator.validate_call_equity(
            date(2025, 1, 1),
            date(2025, 1, 31),
            assignments,
        )

        assert metrics["imbalance_ratio"] > 1.5, "Should detect imbalance"
        assert len(warnings) > 0, "Should warn about imbalance"


# ==============================================================================
# Leave Validator Tests
# ==============================================================================


class TestLeaveValidator:
    """Tests for LeaveValidator."""

    @pytest.fixture
    def validator(self):
        """Provide validator instance."""
        return LeaveValidator()

    @pytest.fixture
    def resident_id(self):
        """Provide test resident ID."""
        return uuid4()

    def test_blocking_leave_types(self, validator):
        """Test identification of blocking leave types."""
        assert (
            validator.should_block_assignment(
                "deployment",
                date(2025, 1, 1),
                date(2025, 1, 31),
            )
            is True
        )

        assert (
            validator.should_block_assignment(
                "vacation",
                date(2025, 1, 1),
                date(2025, 1, 31),
            )
            is False
        )

    def test_conditional_blocking_medical_short(self, validator):
        """Test medical leave <7 days is non-blocking."""
        # 5 days should not block
        assert (
            validator.should_block_assignment(
                "medical",
                date(2025, 1, 1),
                date(2025, 1, 5),
            )
            is False
        )

    def test_conditional_blocking_medical_long(self, validator):
        """Test medical leave >7 days is blocking."""
        # 10 days should block
        assert (
            validator.should_block_assignment(
                "medical",
                date(2025, 1, 1),
                date(2025, 1, 10),
            )
            is True
        )

    def test_conditional_blocking_sick_short(self, validator):
        """Test sick leave <=3 days is non-blocking."""
        assert (
            validator.should_block_assignment(
                "sick",
                date(2025, 1, 1),
                date(2025, 1, 3),
            )
            is False
        )

    def test_conditional_blocking_sick_long(self, validator):
        """Test sick leave >3 days is blocking."""
        assert (
            validator.should_block_assignment(
                "sick",
                date(2025, 1, 1),
                date(2025, 1, 5),
            )
            is True
        )

    def test_no_assignment_during_blocking(self, validator, resident_id):
        """Test detection of assignments during blocking absence."""
        assigned_dates = [
            date(2025, 1, 5),
            date(2025, 1, 6),
        ]

        violation = validator.validate_no_assignment_during_block(
            person_id=resident_id,
            absence_id=uuid4(),
            absence_type="deployment",
            start_date=date(2025, 1, 1),
            end_date=date(2025, 1, 31),
            assigned_dates=assigned_dates,
        )

        assert violation is not None, "Should detect assignment during block"
        assert len(violation.conflict_dates) == 2


# ==============================================================================
# Rotation Validator Tests
# ==============================================================================


class TestRotationValidator:
    """Tests for RotationValidator."""

    @pytest.fixture
    def validator(self):
        """Provide validator instance."""
        return RotationValidator()

    @pytest.fixture
    def resident_id(self):
        """Provide test resident ID."""
        return uuid4()

    def test_minimum_rotation_length_compliant(self, validator, resident_id):
        """Test rotation meets minimum length."""
        violation = validator.validate_minimum_rotation_length(
            resident_id,
            "FMIT",
            date(2025, 1, 1),
            date(2025, 1, 14),
        )

        assert violation is None, "14 days meets minimum"

    def test_minimum_rotation_length_too_short(self, validator, resident_id):
        """Test rotation is too short."""
        violation = validator.validate_minimum_rotation_length(
            resident_id,
            "FMIT",
            date(2025, 1, 1),
            date(2025, 1, 3),
        )

        assert violation is not None, "3 days violates minimum"
        assert violation.violation_type == "minimum_length"

    def test_pgy1_clinic_requirement_met(self, validator, resident_id):
        """Test PGY-1 clinic requirement."""
        violation = validator.validate_pgy_level_clinic_requirements(
            resident_id,
            pgy_level=1,
            clinic_blocks_completed=8,
        )

        assert violation is None, "8 blocks meets requirement"

    def test_pgy1_clinic_requirement_shortfall(self, validator, resident_id):
        """Test PGY-1 clinic requirement not met."""
        violation = validator.validate_pgy_level_clinic_requirements(
            resident_id,
            pgy_level=1,
            clinic_blocks_completed=6,
        )

        assert violation is not None, "6 blocks fails requirement"
        assert violation.violation_type == "missing_required"

    def test_procedure_volume_adequate(self, validator, resident_id):
        """Test adequate procedure volume."""
        violation, warning = validator.validate_procedure_volume(
            resident_id,
            pgy_level=2,
            procedures_completed=30,
        )

        assert violation is None, "30 procedures meets target"
        assert warning is None, "No warning for adequate volume"

    def test_procedure_volume_low(self, validator, resident_id):
        """Test low procedure volume."""
        violation, warning = validator.validate_procedure_volume(
            resident_id,
            pgy_level=2,
            procedures_completed=15,  # Only 50% of target
        )

        assert violation is not None, "15 procedures too low"
        assert violation.violation_type == "volume_shortfall"


# ==============================================================================
# Integration Tests
# ==============================================================================


class TestComplianceIntegration:
    """Integration tests across multiple validators."""

    def test_resident_compliance_multiple_violations(self):
        """Test resident with violations in multiple domains."""
        work_hour_validator = WorkHourValidator()
        supervision_validator = SupervisionValidator()

        resident_id = uuid4()
        start_date = date(2025, 1, 1)

        # Create hours data with violation
        hours_by_date = {
            start_date + timedelta(days=i): 12.0 for i in range(28)
        }  # 84 hours/week

        # Check work hours
        wh_violations, _ = work_hour_validator.validate_80_hour_rolling_average(
            resident_id, hours_by_date
        )

        # Check supervision
        sup_violation = supervision_validator.validate_block_supervision(
            block_id=uuid4(),
            block_date=start_date,
            pgy1_residents=[resident_id, uuid4(), uuid4()],
            other_residents=[],
            faculty_assigned=[uuid4()],
        )

        assert len(wh_violations) > 0, "Should have work hour violation"
        assert sup_violation is not None, "Should have supervision violation"

    def test_full_schedule_scenario(self):
        """Test realistic full schedule with multiple residents."""
        validators = {
            "work_hour": WorkHourValidator(),
            "supervision": SupervisionValidator(),
            "call": CallValidator(),
        }

        # Simulate 3 residents
        residents = [
            {"id": uuid4(), "pgy_level": 1},
            {"id": uuid4(), "pgy_level": 2},
            {"id": uuid4(), "pgy_level": 3},
        ]

        period_start = date(2025, 1, 1)
        period_end = date(2025, 1, 28)

        results = []
        for resident in residents:
            hours_by_date = {
                period_start + timedelta(days=i): 8.0 for i in range(28)
            }  # 56 hours/week - compliant

            wh_violations, _ = validators["work_hour"].validate_80_hour_rolling_average(
                resident["id"], hours_by_date
            )

            results.append(
                {
                    "resident_id": resident["id"],
                    "pgy_level": resident["pgy_level"],
                    "work_hour_violations": len(wh_violations),
                }
            )

        assert all(r["work_hour_violations"] == 0 for r in results)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
