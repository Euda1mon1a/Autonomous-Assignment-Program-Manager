"""Tests for leave and absence compliance validator (pure logic, no DB required)."""

from datetime import date, timedelta
from uuid import UUID, uuid4

import pytest

from app.scheduling.validators.leave_validator import (
    BLOCKING_LEAVE_TYPES,
    CONDITIONAL_BLOCKING_LEAVE_TYPES,
    NON_BLOCKING_LEAVE_TYPES,
    POST_CONVALESCENT_RECOVERY_DAYS,
    POST_DEPLOYMENT_RECOVERY_DAYS,
    LeaveValidator,
    LeaveViolation,
    LeaveWarning,
)


# ==================== Helpers ====================

PERSON = uuid4()
ABSENCE_ID = uuid4()
BASE_DATE = date(2025, 3, 3)


# ==================== Constants Tests ====================


class TestConstants:
    """Verify leave constants are correct."""

    def test_blocking_leave_types(self):
        expected = {
            "deployment",
            "tdy",
            "family_emergency",
            "bereavement",
            "emergency_leave",
            "maternity_paternity",
            "convalescent",
        }
        assert expected == BLOCKING_LEAVE_TYPES

    def test_conditional_blocking_types(self):
        assert CONDITIONAL_BLOCKING_LEAVE_TYPES == {"medical": 7, "sick": 3}

    def test_non_blocking_types(self):
        assert {"vacation", "conference"} == NON_BLOCKING_LEAVE_TYPES

    def test_post_deployment_recovery(self):
        assert POST_DEPLOYMENT_RECOVERY_DAYS == 7

    def test_post_convalescent_recovery(self):
        assert POST_CONVALESCENT_RECOVERY_DAYS == 3


# ==================== Dataclass Tests ====================


class TestLeaveViolation:
    """Test LeaveViolation dataclass."""

    def test_construction(self):
        v = LeaveViolation(
            person_id=PERSON,
            violation_type="assignment_during_block",
            severity="CRITICAL",
            message="Assigned during deployment",
            absence_id=ABSENCE_ID,
            conflict_dates=[BASE_DATE],
        )
        assert v.person_id == PERSON
        assert v.violation_type == "assignment_during_block"
        assert len(v.conflict_dates) == 1


class TestLeaveWarning:
    """Test LeaveWarning dataclass."""

    def test_construction(self):
        w = LeaveWarning(
            person_id=PERSON,
            warning_type="tentative_return",
            message="Check return date",
            absence_id=ABSENCE_ID,
            days_until_return=5,
        )
        assert w.days_until_return == 5


# ==================== LeaveValidator Init ====================


class TestLeaveValidatorInit:
    """Test LeaveValidator initialization."""

    def test_default_values(self):
        v = LeaveValidator()
        assert v.blocking_types == BLOCKING_LEAVE_TYPES
        assert v.conditional_types == CONDITIONAL_BLOCKING_LEAVE_TYPES
        assert v.non_blocking_types == NON_BLOCKING_LEAVE_TYPES


# ==================== should_block_assignment Tests ====================


class TestShouldBlockAssignment:
    """Test should_block_assignment method."""

    def test_explicit_override_true(self):
        v = LeaveValidator()
        assert v.should_block_assignment("vacation", BASE_DATE, BASE_DATE, True) is True

    def test_explicit_override_false(self):
        v = LeaveValidator()
        assert (
            v.should_block_assignment("deployment", BASE_DATE, BASE_DATE, False)
            is False
        )

    def test_deployment_always_blocks(self):
        v = LeaveValidator()
        assert v.should_block_assignment("deployment", BASE_DATE, BASE_DATE) is True

    def test_tdy_always_blocks(self):
        v = LeaveValidator()
        assert v.should_block_assignment("tdy", BASE_DATE, BASE_DATE) is True

    def test_family_emergency_always_blocks(self):
        v = LeaveValidator()
        assert (
            v.should_block_assignment("family_emergency", BASE_DATE, BASE_DATE) is True
        )

    def test_bereavement_always_blocks(self):
        v = LeaveValidator()
        assert v.should_block_assignment("bereavement", BASE_DATE, BASE_DATE) is True

    def test_maternity_paternity_blocks(self):
        v = LeaveValidator()
        assert (
            v.should_block_assignment("maternity_paternity", BASE_DATE, BASE_DATE)
            is True
        )

    def test_convalescent_blocks(self):
        v = LeaveValidator()
        assert v.should_block_assignment("convalescent", BASE_DATE, BASE_DATE) is True

    def test_sick_3_days_no_block(self):
        """Sick leave 3 days (not > 3) -> does not block."""
        v = LeaveValidator()
        end = BASE_DATE + timedelta(days=2)  # 3 days inclusive
        assert v.should_block_assignment("sick", BASE_DATE, end) is False

    def test_sick_4_days_blocks(self):
        """Sick leave 4 days (> 3) -> blocks."""
        v = LeaveValidator()
        end = BASE_DATE + timedelta(days=3)  # 4 days inclusive
        assert v.should_block_assignment("sick", BASE_DATE, end) is True

    def test_medical_7_days_no_block(self):
        """Medical leave 7 days (not > 7) -> does not block."""
        v = LeaveValidator()
        end = BASE_DATE + timedelta(days=6)  # 7 days inclusive
        assert v.should_block_assignment("medical", BASE_DATE, end) is False

    def test_medical_8_days_blocks(self):
        """Medical leave 8 days (> 7) -> blocks."""
        v = LeaveValidator()
        end = BASE_DATE + timedelta(days=7)  # 8 days inclusive
        assert v.should_block_assignment("medical", BASE_DATE, end) is True

    def test_vacation_no_block(self):
        v = LeaveValidator()
        end = BASE_DATE + timedelta(days=14)
        assert v.should_block_assignment("vacation", BASE_DATE, end) is False

    def test_conference_no_block(self):
        v = LeaveValidator()
        end = BASE_DATE + timedelta(days=3)
        assert v.should_block_assignment("conference", BASE_DATE, end) is False

    def test_unknown_type_blocks_conservatively(self):
        """Unknown absence types default to blocking."""
        v = LeaveValidator()
        assert (
            v.should_block_assignment("alien_abduction", BASE_DATE, BASE_DATE) is True
        )


# ==================== validate_no_assignment_during_block Tests ====================


class TestValidateNoAssignmentDuringBlock:
    """Test validate_no_assignment_during_block method."""

    def test_no_assignment_no_violation(self):
        v = LeaveValidator()
        result = v.validate_no_assignment_during_block(
            PERSON,
            ABSENCE_ID,
            "deployment",
            BASE_DATE,
            BASE_DATE + timedelta(days=7),
            [],
        )
        assert result is None

    def test_assignment_during_deployment_violation(self):
        v = LeaveValidator()
        conflict = BASE_DATE + timedelta(days=3)
        result = v.validate_no_assignment_during_block(
            PERSON,
            ABSENCE_ID,
            "deployment",
            BASE_DATE,
            BASE_DATE + timedelta(days=7),
            [conflict],
        )
        assert result is not None
        assert result.violation_type == "assignment_during_block"
        assert result.severity == "CRITICAL"
        assert conflict in result.conflict_dates

    def test_assignment_outside_block_no_violation(self):
        v = LeaveValidator()
        outside = BASE_DATE + timedelta(days=20)
        result = v.validate_no_assignment_during_block(
            PERSON,
            ABSENCE_ID,
            "deployment",
            BASE_DATE,
            BASE_DATE + timedelta(days=7),
            [outside],
        )
        assert result is None

    def test_non_blocking_type_no_violation(self):
        """Vacation is non-blocking, so assignments during it are OK."""
        v = LeaveValidator()
        conflict = BASE_DATE + timedelta(days=1)
        result = v.validate_no_assignment_during_block(
            PERSON,
            ABSENCE_ID,
            "vacation",
            BASE_DATE,
            BASE_DATE + timedelta(days=7),
            [conflict],
        )
        assert result is None

    def test_explicit_non_blocking_override(self):
        """Explicit is_blocking=False overrides blocking type."""
        v = LeaveValidator()
        conflict = BASE_DATE + timedelta(days=1)
        result = v.validate_no_assignment_during_block(
            PERSON,
            ABSENCE_ID,
            "deployment",
            BASE_DATE,
            BASE_DATE + timedelta(days=7),
            [conflict],
            is_blocking=False,
        )
        assert result is None

    def test_multiple_conflict_dates(self):
        v = LeaveValidator()
        conflicts = [BASE_DATE + timedelta(days=i) for i in range(3)]
        result = v.validate_no_assignment_during_block(
            PERSON,
            ABSENCE_ID,
            "tdy",
            BASE_DATE,
            BASE_DATE + timedelta(days=7),
            conflicts,
        )
        assert result is not None
        assert len(result.conflict_dates) == 3

    def test_short_sick_leave_no_block(self):
        """Sick leave ≤3 days -> non-blocking -> no violation even with assignments."""
        v = LeaveValidator()
        end = BASE_DATE + timedelta(days=2)  # 3 days
        result = v.validate_no_assignment_during_block(
            PERSON,
            ABSENCE_ID,
            "sick",
            BASE_DATE,
            end,
            [BASE_DATE + timedelta(days=1)],
        )
        assert result is None


# ==================== validate_sick_leave_compliance Tests ====================


class TestValidateSickLeaveCompliance:
    """Test validate_sick_leave_compliance method."""

    def test_short_sick_no_blocking_ok(self):
        """≤3 days sick, no blocks marked -> no violation."""
        v = LeaveValidator()
        end = BASE_DATE + timedelta(days=2)
        result = v.validate_sick_leave_compliance(PERSON, ABSENCE_ID, BASE_DATE, end)
        assert result is None

    def test_short_sick_incorrectly_blocked(self):
        """≤3 days sick but marked as blocking -> MEDIUM violation."""
        v = LeaveValidator()
        end = BASE_DATE + timedelta(days=2)
        blocked = [BASE_DATE, BASE_DATE + timedelta(days=1)]
        result = v.validate_sick_leave_compliance(
            PERSON, ABSENCE_ID, BASE_DATE, end, blocked
        )
        assert result is not None
        assert result.severity == "MEDIUM"
        assert "incorrectly marked" in result.message

    def test_long_sick_no_violation(self):
        """>3 days sick -> blocking is expected, no violation."""
        v = LeaveValidator()
        end = BASE_DATE + timedelta(days=5)  # 6 days
        result = v.validate_sick_leave_compliance(PERSON, ABSENCE_ID, BASE_DATE, end)
        assert result is None

    def test_exactly_3_days_not_blocked(self):
        """Exactly 3 days (same as threshold) -> no violation."""
        v = LeaveValidator()
        end = BASE_DATE + timedelta(days=2)
        result = v.validate_sick_leave_compliance(PERSON, ABSENCE_ID, BASE_DATE, end)
        assert result is None

    def test_single_day_sick(self):
        """1 day sick -> no violation."""
        v = LeaveValidator()
        result = v.validate_sick_leave_compliance(
            PERSON, ABSENCE_ID, BASE_DATE, BASE_DATE
        )
        assert result is None


# ==================== validate_medical_leave_compliance Tests ====================


class TestValidateMedicalLeaveCompliance:
    """Test validate_medical_leave_compliance method."""

    def test_in_progress_no_violation(self):
        v = LeaveValidator()
        end = BASE_DATE + timedelta(days=14)
        result = v.validate_medical_leave_compliance(
            PERSON, ABSENCE_ID, BASE_DATE, end, "in_progress"
        )
        assert result is None

    def test_cleared_violation(self):
        """Medically cleared but leave still extends -> HIGH violation."""
        v = LeaveValidator()
        end = BASE_DATE + timedelta(days=14)
        result = v.validate_medical_leave_compliance(
            PERSON, ABSENCE_ID, BASE_DATE, end, "cleared"
        )
        assert result is not None
        assert result.severity == "HIGH"
        assert "clearance received" in result.message.lower()

    def test_no_status_no_violation(self):
        v = LeaveValidator()
        end = BASE_DATE + timedelta(days=14)
        result = v.validate_medical_leave_compliance(PERSON, ABSENCE_ID, BASE_DATE, end)
        assert result is None


# ==================== validate_tdy_deployment_compliance Tests ====================


class TestValidateTdyDeploymentCompliance:
    """Test validate_tdy_deployment_compliance method."""

    def test_tdy_with_location_ok(self):
        v = LeaveValidator()
        result = v.validate_tdy_deployment_compliance(
            PERSON,
            ABSENCE_ID,
            BASE_DATE,
            BASE_DATE + timedelta(days=7),
            tdy_location="Fort Bragg",
        )
        assert result is None

    def test_deployment_with_orders_ok(self):
        v = LeaveValidator()
        result = v.validate_tdy_deployment_compliance(
            PERSON,
            ABSENCE_ID,
            BASE_DATE,
            BASE_DATE + timedelta(days=30),
            deployment_orders=True,
        )
        assert result is None

    def test_no_special_checks_for_generic_id(self):
        """Generic UUID doesn't trigger TDY/deployment string checks."""
        v = LeaveValidator()
        result = v.validate_tdy_deployment_compliance(
            PERSON,
            ABSENCE_ID,
            BASE_DATE,
            BASE_DATE + timedelta(days=7),
        )
        # Generic UUID doesn't contain "tdy" or "deployment" in str
        assert result is None


# ==================== validate_post_deployment_recovery Tests ====================


class TestValidatePostDeploymentRecovery:
    """Test validate_post_deployment_recovery method."""

    def test_no_early_assignments_ok(self):
        v = LeaveValidator()
        deploy_end = date(2025, 3, 14)
        # Assignment after recovery period (7 days)
        assignments = [date(2025, 3, 25)]
        result = v.validate_post_deployment_recovery(PERSON, deploy_end, assignments)
        assert result is None

    def test_early_assignment_violation(self):
        """Assignment during recovery period -> HIGH violation."""
        v = LeaveValidator()
        deploy_end = date(2025, 3, 14)
        early = date(2025, 3, 17)  # 3 days after, < 7 day recovery
        result = v.validate_post_deployment_recovery(PERSON, deploy_end, [early])
        assert result is not None
        assert result.severity == "HIGH"
        assert early in result.conflict_dates

    def test_assignment_on_recovery_end_ok(self):
        """Assignment on recovery end date (exclusive) -> no violation."""
        v = LeaveValidator()
        deploy_end = date(2025, 3, 14)
        recovery_end = deploy_end + timedelta(days=POST_DEPLOYMENT_RECOVERY_DAYS)
        # recovery_end is exclusive (< not <=), so assignment on that date is OK
        result = v.validate_post_deployment_recovery(PERSON, deploy_end, [recovery_end])
        assert result is None

    def test_assignment_on_deploy_end_excluded(self):
        """Assignment on deployment end date itself is not early (> not >=)."""
        v = LeaveValidator()
        deploy_end = date(2025, 3, 14)
        result = v.validate_post_deployment_recovery(PERSON, deploy_end, [deploy_end])
        assert result is None

    def test_multiple_early_assignments(self):
        v = LeaveValidator()
        deploy_end = date(2025, 3, 14)
        early = [date(2025, 3, 16), date(2025, 3, 18)]
        result = v.validate_post_deployment_recovery(PERSON, deploy_end, early)
        assert result is not None
        assert len(result.conflict_dates) == 2

    def test_empty_assignments_ok(self):
        v = LeaveValidator()
        deploy_end = date(2025, 3, 14)
        result = v.validate_post_deployment_recovery(PERSON, deploy_end, [])
        assert result is None


# ==================== validate_tentative_return_date Tests ====================


class TestValidateTentativeReturnDate:
    """Test validate_tentative_return_date method."""

    def test_confirmed_return_no_warning(self):
        """Return date confirmed -> no warning."""
        v = LeaveValidator()
        result = v.validate_tentative_return_date(
            PERSON, ABSENCE_ID, False, date(2025, 3, 10), date(2025, 3, 5)
        )
        assert result is None

    def test_tentative_approaching_warning(self):
        """Tentative return within 7 days -> warning."""
        v = LeaveValidator()
        today = date(2025, 3, 5)
        return_date = date(2025, 3, 10)  # 5 days away
        result = v.validate_tentative_return_date(
            PERSON, ABSENCE_ID, True, return_date, today
        )
        assert result is not None
        assert result.warning_type == "approaching_end"
        assert result.days_until_return == 5

    def test_tentative_far_away_no_warning(self):
        """Tentative return > 7 days away -> no warning."""
        v = LeaveValidator()
        today = date(2025, 3, 1)
        return_date = date(2025, 3, 20)  # 19 days away
        result = v.validate_tentative_return_date(
            PERSON, ABSENCE_ID, True, return_date, today
        )
        assert result is None

    def test_tentative_today_warning(self):
        """Tentative return date is today (0 days) -> warning."""
        v = LeaveValidator()
        today = date(2025, 3, 5)
        result = v.validate_tentative_return_date(
            PERSON, ABSENCE_ID, True, today, today
        )
        assert result is not None
        assert result.days_until_return == 0

    def test_tentative_past_date_warning(self):
        """Tentative return already passed -> warning with 0 days."""
        v = LeaveValidator()
        today = date(2025, 3, 10)
        return_date = date(2025, 3, 5)  # 5 days ago
        result = v.validate_tentative_return_date(
            PERSON, ABSENCE_ID, True, return_date, today
        )
        assert result is not None
        assert result.days_until_return == 0  # max(0, -5)


# ==================== validate_convalescent_leave_recovery Tests ====================


class TestValidateConvalescentLeaveRecovery:
    """Test validate_convalescent_leave_recovery method."""

    def test_no_procedure_no_warning(self):
        v = LeaveValidator()
        result = v.validate_convalescent_leave_recovery(
            PERSON, ABSENCE_ID, BASE_DATE, BASE_DATE + timedelta(days=10)
        )
        assert result is None

    def test_unknown_procedure_no_warning(self):
        v = LeaveValidator()
        result = v.validate_convalescent_leave_recovery(
            PERSON,
            ABSENCE_ID,
            BASE_DATE,
            BASE_DATE + timedelta(days=10),
            procedure_type="unknown_procedure",
        )
        assert result is None

    def test_appendectomy_adequate_no_warning(self):
        """14+ days for appendectomy -> no warning."""
        v = LeaveValidator()
        result = v.validate_convalescent_leave_recovery(
            PERSON,
            ABSENCE_ID,
            BASE_DATE,
            BASE_DATE + timedelta(days=14),
            procedure_type="appendectomy",
        )
        assert result is None

    def test_appendectomy_short_warning(self):
        """7 days for appendectomy (< 14 min) -> warning."""
        v = LeaveValidator()
        result = v.validate_convalescent_leave_recovery(
            PERSON,
            ABSENCE_ID,
            BASE_DATE,
            BASE_DATE + timedelta(days=7),
            procedure_type="appendectomy",
        )
        assert result is not None
        assert result.warning_type == "tentative_return"
        assert "appendectomy" in result.message
        assert "14" in result.message

    def test_acl_repair_short_warning(self):
        """21 days for ACL repair (< 42 min) -> warning."""
        v = LeaveValidator()
        result = v.validate_convalescent_leave_recovery(
            PERSON,
            ABSENCE_ID,
            BASE_DATE,
            BASE_DATE + timedelta(days=21),
            procedure_type="acl_repair",
        )
        assert result is not None
        assert "42" in result.message

    def test_csection_adequate_no_warning(self):
        """56+ days for C-section -> no warning."""
        v = LeaveValidator()
        result = v.validate_convalescent_leave_recovery(
            PERSON,
            ABSENCE_ID,
            BASE_DATE,
            BASE_DATE + timedelta(days=56),
            procedure_type="childbirth_csection",
        )
        assert result is None

    def test_vaginal_birth_short_warning(self):
        """30 days for vaginal delivery (< 42) -> warning."""
        v = LeaveValidator()
        result = v.validate_convalescent_leave_recovery(
            PERSON,
            ABSENCE_ID,
            BASE_DATE,
            BASE_DATE + timedelta(days=30),
            procedure_type="childbirth_vaginal",
        )
        assert result is not None


# ==================== get_leave_impact_summary Tests ====================


class TestGetLeaveImpactSummary:
    """Test get_leave_impact_summary method."""

    def test_no_leave_records(self):
        v = LeaveValidator()
        result = v.get_leave_impact_summary(PERSON, [], 28)
        assert result["total_leave_days"] == 0
        assert result["blocking_days"] == 0
        assert result["non_blocking_days"] == 0
        assert result["work_days_available"] == 28

    def test_blocking_leave_reduces_capacity(self):
        v = LeaveValidator()
        records = [
            {
                "start_date": BASE_DATE,
                "end_date": BASE_DATE + timedelta(days=6),
                "is_blocking": True,
            }
        ]
        result = v.get_leave_impact_summary(PERSON, records, 28)
        assert result["blocking_days"] == 7
        assert result["work_days_available"] == 21
        assert result["work_capacity_hours"] == 21 * 12

    def test_non_blocking_leave_no_capacity_reduction(self):
        v = LeaveValidator()
        records = [
            {
                "start_date": BASE_DATE,
                "end_date": BASE_DATE + timedelta(days=4),
                "is_blocking": False,
            }
        ]
        result = v.get_leave_impact_summary(PERSON, records, 28)
        assert result["non_blocking_days"] == 5
        assert result["blocking_days"] == 0
        assert result["work_days_available"] == 28

    def test_mixed_leave_records(self):
        v = LeaveValidator()
        records = [
            {
                "start_date": BASE_DATE,
                "end_date": BASE_DATE + timedelta(days=6),
                "is_blocking": True,
            },
            {
                "start_date": BASE_DATE + timedelta(days=10),
                "end_date": BASE_DATE + timedelta(days=12),
                "is_blocking": False,
            },
        ]
        result = v.get_leave_impact_summary(PERSON, records, 28)
        assert result["blocking_days"] == 7
        assert result["non_blocking_days"] == 3
        assert result["total_leave_days"] == 10

    def test_missing_dates_skipped(self):
        v = LeaveValidator()
        records = [
            {"is_blocking": True},  # Missing dates
            {
                "start_date": BASE_DATE,
                "end_date": BASE_DATE + timedelta(days=2),
                "is_blocking": True,
            },
        ]
        result = v.get_leave_impact_summary(PERSON, records, 28)
        assert result["blocking_days"] == 3

    def test_capacity_utilization(self):
        v = LeaveValidator()
        result = v.get_leave_impact_summary(PERSON, [], 28)
        # work_capacity_hours = 28 * 12 = 336
        # hours_limit = 80 * 4 = 320
        # utilization = 320 / 336 = 0.952...
        assert result["hours_limit"] == 320
        assert result["capacity_utilization"] == pytest.approx(320 / 336, rel=0.01)

    def test_all_days_blocked_zero_capacity(self):
        """All days blocked -> 0 work capacity, 0 utilization."""
        v = LeaveValidator()
        records = [
            {
                "start_date": BASE_DATE,
                "end_date": BASE_DATE + timedelta(days=27),
                "is_blocking": True,
            }
        ]
        result = v.get_leave_impact_summary(PERSON, records, 28)
        assert result["work_days_available"] == 0
        assert result["work_capacity_hours"] == 0
        assert result["capacity_utilization"] == 0
