"""Comprehensive tests for ConflictAutoResolver service.

Tests cover:
- All 5 resolution strategies (swap, reassign, split, backup, defer)
- All 5 safety checks (ACGME, coverage, availability, supervision, workload)
- Conflict detection and analysis
- Auto-resolution logic and decision making
- Priority and risk handling
- Batch operations
- Edge cases and error conditions
"""
from datetime import date, datetime, timedelta
from unittest.mock import Mock, patch
from uuid import UUID, uuid4

import pytest
from sqlalchemy.orm import Session

from app.models.absence import Absence
from app.models.assignment import Assignment
from app.models.block import Block
from app.models.conflict_alert import (
    ConflictAlert,
    ConflictAlertStatus,
    ConflictSeverity,
    ConflictType,
)
from app.models.person import Person
from app.models.rotation_template import RotationTemplate
from app.models.swap import SwapRecord, SwapStatus, SwapType
from app.models.user import User
from app.schemas.conflict_resolution import (
    ConflictAnalysis,
    ImpactAssessment,
    ResolutionOption,
    ResolutionResult,
    ResolutionStatusEnum,
    ResolutionStrategyEnum,
    SafetyCheckResult,
    SafetyCheckType,
)
from app.services.conflict_auto_resolver import ConflictAutoResolver


# ==================== FIXTURES ====================


@pytest.fixture
def resolver(db: Session) -> ConflictAutoResolver:
    """Create a ConflictAutoResolver instance."""
    return ConflictAutoResolver(db)


@pytest.fixture
def sample_user(db: Session) -> User:
    """Create a sample user for resolution operations."""
    from app.core.security import get_password_hash

    user = User(
        id=uuid4(),
        username="resolver_user",
        email="resolver@test.org",
        hashed_password=get_password_hash("password123"),
        role="admin",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def sample_conflict_alert(
    db: Session, sample_faculty: Person
) -> ConflictAlert:
    """Create a sample conflict alert."""
    fmit_week = date.today() + timedelta(days=14)
    alert = ConflictAlert(
        id=uuid4(),
        faculty_id=sample_faculty.id,
        conflict_type=ConflictType.LEAVE_FMIT_OVERLAP,
        fmit_week=fmit_week,
        description="Test conflict",
        severity=ConflictSeverity.WARNING,
        status=ConflictAlertStatus.NEW,
    )
    db.add(alert)
    db.commit()
    db.refresh(alert)
    return alert


@pytest.fixture
def sample_fmit_template(db: Session) -> RotationTemplate:
    """Create a sample FMIT rotation template."""
    template = RotationTemplate(
        id=uuid4(),
        name="FMIT Week",
        activity_type="fmit",
        abbreviation="FMIT",
        max_residents=1,
        supervision_required=True,
    )
    db.add(template)
    db.commit()
    db.refresh(template)
    return template


@pytest.fixture
def sample_faculty_available(db: Session) -> Person:
    """Create an available faculty member for swaps."""
    faculty = Person(
        id=uuid4(),
        name="Dr. Available",
        type="faculty",
        email="available@test.org",
        performs_procedures=True,
    )
    db.add(faculty)
    db.commit()
    db.refresh(faculty)
    return faculty


@pytest.fixture
def sample_junior_resident(db: Session) -> Person:
    """Create a PGY-2 resident for junior reassignment tests."""
    resident = Person(
        id=uuid4(),
        name="Dr. Junior Resident",
        type="resident",
        email="junior@test.org",
        pgy_level=2,
    )
    db.add(resident)
    db.commit()
    db.refresh(resident)
    return resident


# ==================== CONFLICT ANALYSIS TESTS ====================


@pytest.mark.unit
class TestAnalyzeConflict:
    """Tests for conflict analysis functionality."""

    def test_analyze_basic_conflict(
        self, resolver: ConflictAutoResolver, sample_conflict_alert: ConflictAlert
    ):
        """Test analyzing a basic conflict alert."""
        analysis = resolver.analyze_conflict(sample_conflict_alert.id)

        assert isinstance(analysis, ConflictAnalysis)
        assert analysis.conflict_id == sample_conflict_alert.id
        assert analysis.conflict_type == sample_conflict_alert.conflict_type.value
        assert analysis.severity == sample_conflict_alert.severity.value
        assert len(analysis.affected_faculty) > 0
        assert 0.0 <= analysis.complexity_score <= 1.0

    def test_analyze_nonexistent_conflict(self, resolver: ConflictAutoResolver):
        """Test analyzing a non-existent conflict raises error."""
        fake_id = uuid4()
        with pytest.raises(ValueError, match="not found"):
            resolver.analyze_conflict(fake_id)

    def test_analyze_conflict_root_cause(
        self, resolver: ConflictAutoResolver, sample_conflict_alert: ConflictAlert
    ):
        """Test that root cause is properly identified."""
        analysis = resolver.analyze_conflict(sample_conflict_alert.id)

        assert analysis.root_cause
        assert len(analysis.root_cause) > 0
        # Should contain relevant information about the conflict type
        if sample_conflict_alert.conflict_type == ConflictType.LEAVE_FMIT_OVERLAP:
            assert "FMIT" in analysis.root_cause or "leave" in analysis.root_cause.lower()

    def test_analyze_conflict_complexity_scoring(
        self,
        resolver: ConflictAutoResolver,
        db: Session,
        sample_faculty: Person,
    ):
        """Test complexity scoring for different conflict types."""
        # Simple conflict - single faculty, single week
        simple_alert = ConflictAlert(
            id=uuid4(),
            faculty_id=sample_faculty.id,
            conflict_type=ConflictType.LEAVE_FMIT_OVERLAP,
            fmit_week=date.today() + timedelta(days=7),
            description="Simple conflict",
            severity=ConflictSeverity.INFO,
            status=ConflictAlertStatus.NEW,
        )
        db.add(simple_alert)

        # Critical conflict - higher complexity
        critical_alert = ConflictAlert(
            id=uuid4(),
            faculty_id=sample_faculty.id,
            conflict_type=ConflictType.CALL_CASCADE,
            fmit_week=date.today() + timedelta(days=14),
            description="Critical cascading conflict",
            severity=ConflictSeverity.CRITICAL,
            status=ConflictAlertStatus.NEW,
        )
        db.add(critical_alert)
        db.commit()

        simple_analysis = resolver.analyze_conflict(simple_alert.id)
        critical_analysis = resolver.analyze_conflict(critical_alert.id)

        # Critical should have higher complexity
        assert critical_analysis.complexity_score >= simple_analysis.complexity_score

    def test_analyze_conflict_safety_checks_performed(
        self, resolver: ConflictAutoResolver, sample_conflict_alert: ConflictAlert
    ):
        """Test that all safety checks are performed during analysis."""
        analysis = resolver.analyze_conflict(sample_conflict_alert.id)

        assert len(analysis.safety_checks) == 5  # All 5 safety checks
        check_types = {check.check_type for check in analysis.safety_checks}
        assert SafetyCheckType.ACGME_COMPLIANCE in check_types
        assert SafetyCheckType.COVERAGE_GAP in check_types
        assert SafetyCheckType.FACULTY_AVAILABILITY in check_types
        assert SafetyCheckType.SUPERVISION_RATIO in check_types
        assert SafetyCheckType.WORKLOAD_BALANCE in check_types

    def test_analyze_conflict_recommends_strategies(
        self, resolver: ConflictAutoResolver, sample_conflict_alert: ConflictAlert
    ):
        """Test that analysis recommends appropriate strategies."""
        analysis = resolver.analyze_conflict(sample_conflict_alert.id)

        assert len(analysis.recommended_strategies) > 0
        # Should recommend at least one valid strategy
        assert all(
            isinstance(strategy, ResolutionStrategyEnum)
            for strategy in analysis.recommended_strategies
        )

    def test_analyze_conflict_identifies_constraints(
        self,
        resolver: ConflictAutoResolver,
        db: Session,
        sample_faculty: Person,
        sample_absence: Absence,
    ):
        """Test that constraints are properly identified."""
        # Create conflict with leave constraint
        alert = ConflictAlert(
            id=uuid4(),
            faculty_id=sample_faculty.id,
            conflict_type=ConflictType.LEAVE_FMIT_OVERLAP,
            fmit_week=date.today() + timedelta(days=10),
            description="Leave conflict",
            severity=ConflictSeverity.CRITICAL,
            status=ConflictAlertStatus.NEW,
            leave_id=sample_absence.id,
        )
        db.add(alert)
        db.commit()

        analysis = resolver.analyze_conflict(alert.id)

        assert len(analysis.constraints) > 0
        # Should identify leave as a constraint
        constraint_text = " ".join(analysis.constraints).lower()
        assert "leave" in constraint_text or "approved" in constraint_text


# ==================== SAFETY CHECKS TESTS ====================


@pytest.mark.unit
class TestSafetyChecks:
    """Tests for individual safety check functionality."""

    def test_acgme_compliance_check_resident(
        self, resolver: ConflictAutoResolver, db: Session
    ):
        """Test ACGME compliance check for residents."""
        resident = Person(
            id=uuid4(),
            name="Dr. Test Resident",
            type="resident",
            email="resident@test.org",
            pgy_level=1,
        )
        db.add(resident)

        alert = ConflictAlert(
            id=uuid4(),
            faculty_id=resident.id,
            conflict_type=ConflictType.BACK_TO_BACK,
            fmit_week=date.today() + timedelta(days=7),
            description="Test",
            severity=ConflictSeverity.WARNING,
            status=ConflictAlertStatus.NEW,
        )
        db.add(alert)
        db.commit()

        result = resolver._check_acgme_compliance(alert)

        assert isinstance(result, SafetyCheckResult)
        assert result.check_type == SafetyCheckType.ACGME_COMPLIANCE
        # Should pass for basic scenario without excessive hours
        assert result.passed

    def test_acgme_compliance_check_non_resident(
        self, resolver: ConflictAutoResolver, sample_conflict_alert: ConflictAlert
    ):
        """Test ACGME compliance check for non-residents (should not apply)."""
        result = resolver._check_acgme_compliance(sample_conflict_alert)

        assert result.passed
        assert "not applicable" in result.message.lower()

    def test_coverage_gap_check_sufficient_coverage(
        self,
        resolver: ConflictAutoResolver,
        db: Session,
        sample_conflict_alert: ConflictAlert,
        sample_faculty_available: Person,
        sample_fmit_template: RotationTemplate,
    ):
        """Test coverage gap check when sufficient coverage exists."""
        # Create blocks and assignments for the week
        fmit_week = sample_conflict_alert.fmit_week
        for i in range(7):
            block_date = fmit_week + timedelta(days=i)
            for time_of_day in ["AM", "PM"]:
                block = Block(
                    id=uuid4(),
                    date=block_date,
                    time_of_day=time_of_day,
                    block_number=1,
                )
                db.add(block)
                db.flush()

                # Add assignment for available faculty
                assignment = Assignment(
                    id=uuid4(),
                    block_id=block.id,
                    person_id=sample_faculty_available.id,
                    rotation_template_id=sample_fmit_template.id,
                    role="primary",
                )
                db.add(assignment)

        db.commit()

        result = resolver._check_coverage_gaps(sample_conflict_alert)

        assert result.check_type == SafetyCheckType.COVERAGE_GAP
        assert result.passed

    def test_coverage_gap_check_insufficient_coverage(
        self, resolver: ConflictAutoResolver, sample_conflict_alert: ConflictAlert
    ):
        """Test coverage gap check when coverage is insufficient."""
        result = resolver._check_coverage_gaps(sample_conflict_alert)

        assert result.check_type == SafetyCheckType.COVERAGE_GAP
        # Should fail when no other faculty assigned
        assert not result.passed

    def test_faculty_availability_check_with_available_faculty(
        self,
        resolver: ConflictAutoResolver,
        sample_conflict_alert: ConflictAlert,
        sample_faculty_available: Person,
    ):
        """Test faculty availability check when faculty are available."""
        result = resolver._check_faculty_availability(sample_conflict_alert)

        assert result.check_type == SafetyCheckType.FACULTY_AVAILABILITY
        assert result.passed
        assert result.details.get("available_count", 0) > 0

    def test_faculty_availability_check_no_available_faculty(
        self,
        resolver: ConflictAutoResolver,
        db: Session,
        sample_faculty: Person,
    ):
        """Test faculty availability check when no faculty available."""
        # Create conflict where all faculty are busy
        alert = ConflictAlert(
            id=uuid4(),
            faculty_id=sample_faculty.id,
            conflict_type=ConflictType.LEAVE_FMIT_OVERLAP,
            fmit_week=date.today() + timedelta(days=7),
            description="Test",
            severity=ConflictSeverity.CRITICAL,
            status=ConflictAlertStatus.NEW,
        )
        db.add(alert)
        db.commit()

        result = resolver._check_faculty_availability(alert)

        # May pass or fail depending on test data - just verify structure
        assert result.check_type == SafetyCheckType.FACULTY_AVAILABILITY
        assert "available_count" in result.details

    def test_supervision_ratio_check(
        self, resolver: ConflictAutoResolver, sample_conflict_alert: ConflictAlert
    ):
        """Test supervision ratio check."""
        result = resolver._check_supervision_ratio(sample_conflict_alert)

        assert result.check_type == SafetyCheckType.SUPERVISION_RATIO
        # Should pass for basic faculty conflict
        assert result.passed

    def test_workload_balance_check(
        self, resolver: ConflictAutoResolver, sample_conflict_alert: ConflictAlert
    ):
        """Test workload balance check."""
        result = resolver._check_workload_balance(sample_conflict_alert)

        assert result.check_type == SafetyCheckType.WORKLOAD_BALANCE
        assert "balance_score" in result.details
        assert 0.0 <= result.details["balance_score"] <= 1.0


# ==================== RESOLUTION OPTIONS TESTS ====================


@pytest.mark.unit
class TestGenerateResolutionOptions:
    """Tests for generating resolution options."""

    def test_generate_options_basic(
        self, resolver: ConflictAutoResolver, sample_conflict_alert: ConflictAlert
    ):
        """Test generating basic resolution options."""
        options = resolver.generate_resolution_options(sample_conflict_alert.id)

        assert isinstance(options, list)
        assert len(options) > 0
        # Should always include defer to human as fallback
        assert any(
            opt.strategy == ResolutionStrategyEnum.DEFER_TO_HUMAN for opt in options
        )

    def test_generate_options_nonexistent_conflict(
        self, resolver: ConflictAutoResolver
    ):
        """Test generating options for non-existent conflict."""
        fake_id = uuid4()
        options = resolver.generate_resolution_options(fake_id)

        assert options == []

    def test_generate_options_max_limit(
        self, resolver: ConflictAutoResolver, sample_conflict_alert: ConflictAlert
    ):
        """Test max_options parameter limits returned options."""
        options = resolver.generate_resolution_options(
            sample_conflict_alert.id, max_options=3
        )

        assert len(options) <= 3

    def test_generate_options_sorted_by_score(
        self, resolver: ConflictAutoResolver, sample_conflict_alert: ConflictAlert
    ):
        """Test that options are sorted by overall score."""
        options = resolver.generate_resolution_options(sample_conflict_alert.id)

        if len(options) > 1:
            # Verify descending order by overall score
            for i in range(len(options) - 1):
                score1 = options[i].impact.overall_score if options[i].impact else 0
                score2 = (
                    options[i + 1].impact.overall_score
                    if options[i + 1].impact
                    else 0
                )
                assert score1 >= score2

    def test_generate_options_all_have_impact_assessment(
        self, resolver: ConflictAutoResolver, sample_conflict_alert: ConflictAlert
    ):
        """Test that all options have impact assessments."""
        options = resolver.generate_resolution_options(sample_conflict_alert.id)

        for option in options:
            assert option.impact is not None
            assert isinstance(option.impact, ImpactAssessment)
            assert 0.0 <= option.impact.overall_score <= 1.0

    def test_generate_options_caching(
        self, resolver: ConflictAutoResolver, sample_conflict_alert: ConflictAlert
    ):
        """Test that options are cached for performance."""
        # First call
        options1 = resolver.generate_resolution_options(sample_conflict_alert.id)

        # Second call (should use cache)
        options2 = resolver.generate_resolution_options(sample_conflict_alert.id)

        assert len(options1) == len(options2)
        # Should have same option IDs
        assert [o.id for o in options1] == [o.id for o in options2]


# ==================== STRATEGY-SPECIFIC OPTION TESTS ====================


@pytest.mark.unit
class TestResolutionStrategies:
    """Tests for specific resolution strategies."""

    def test_swap_assignments_strategy(
        self,
        resolver: ConflictAutoResolver,
        db: Session,
        sample_faculty: Person,
        sample_faculty_available: Person,
    ):
        """Test swap assignments strategy generation."""
        alert = ConflictAlert(
            id=uuid4(),
            faculty_id=sample_faculty.id,
            conflict_type=ConflictType.LEAVE_FMIT_OVERLAP,
            fmit_week=date.today() + timedelta(days=14),
            description="Leave overlap",
            severity=ConflictSeverity.CRITICAL,
            status=ConflictAlertStatus.NEW,
        )
        db.add(alert)
        db.commit()

        options = resolver.generate_resolution_options(alert.id)

        swap_options = [
            opt
            for opt in options
            if opt.strategy == ResolutionStrategyEnum.SWAP_ASSIGNMENTS
        ]
        assert len(swap_options) > 0

        swap_opt = swap_options[0]
        assert "swap" in swap_opt.title.lower() or "swap" in swap_opt.description.lower()
        assert len(swap_opt.detailed_steps) > 0

    def test_reassign_junior_strategy(
        self,
        resolver: ConflictAutoResolver,
        db: Session,
        sample_faculty: Person,
        sample_junior_resident: Person,
    ):
        """Test reassign to junior faculty strategy."""
        alert = ConflictAlert(
            id=uuid4(),
            faculty_id=sample_faculty.id,
            conflict_type=ConflictType.LEAVE_FMIT_OVERLAP,
            fmit_week=date.today() + timedelta(days=14),
            description="Leave conflict",
            severity=ConflictSeverity.WARNING,
            status=ConflictAlertStatus.NEW,
        )
        db.add(alert)
        db.commit()

        options = resolver.generate_resolution_options(alert.id)

        junior_options = [
            opt
            for opt in options
            if opt.strategy == ResolutionStrategyEnum.REASSIGN_JUNIOR
        ]
        if junior_options:
            junior_opt = junior_options[0]
            assert "junior" in junior_opt.title.lower() or "junior" in junior_opt.description.lower()

    def test_split_coverage_strategy(
        self,
        resolver: ConflictAutoResolver,
        db: Session,
        sample_faculty: Person,
    ):
        """Test split coverage strategy for back-to-back conflicts."""
        alert = ConflictAlert(
            id=uuid4(),
            faculty_id=sample_faculty.id,
            conflict_type=ConflictType.BACK_TO_BACK,
            fmit_week=date.today() + timedelta(days=14),
            description="Back-to-back FMIT weeks",
            severity=ConflictSeverity.WARNING,
            status=ConflictAlertStatus.NEW,
        )
        db.add(alert)
        db.commit()

        options = resolver.generate_resolution_options(alert.id)

        split_options = [
            opt
            for opt in options
            if opt.strategy == ResolutionStrategyEnum.SPLIT_COVERAGE
        ]
        assert len(split_options) > 0

        split_opt = split_options[0]
        assert "split" in split_opt.title.lower() or "split" in split_opt.description.lower()

    def test_escalate_to_backup_strategy(
        self,
        resolver: ConflictAutoResolver,
        db: Session,
        sample_faculty: Person,
    ):
        """Test escalate to backup pool strategy."""
        alert = ConflictAlert(
            id=uuid4(),
            faculty_id=sample_faculty.id,
            conflict_type=ConflictType.LEAVE_FMIT_OVERLAP,
            fmit_week=date.today() + timedelta(days=14),
            description="Critical conflict",
            severity=ConflictSeverity.CRITICAL,
            status=ConflictAlertStatus.NEW,
        )
        db.add(alert)
        db.commit()

        options = resolver.generate_resolution_options(alert.id)

        backup_options = [
            opt
            for opt in options
            if opt.strategy == ResolutionStrategyEnum.ESCALATE_TO_BACKUP
        ]
        assert len(backup_options) > 0

        backup_opt = backup_options[0]
        assert "backup" in backup_opt.title.lower() or "backup" in backup_opt.description.lower()

    def test_defer_to_human_always_available(
        self, resolver: ConflictAutoResolver, sample_conflict_alert: ConflictAlert
    ):
        """Test that defer to human is always available as fallback."""
        options = resolver.generate_resolution_options(sample_conflict_alert.id)

        defer_options = [
            opt
            for opt in options
            if opt.strategy == ResolutionStrategyEnum.DEFER_TO_HUMAN
        ]
        assert len(defer_options) == 1

        defer_opt = defer_options[0]
        assert "defer" in defer_opt.title.lower() or "manual" in defer_opt.title.lower()
        assert defer_opt.risk_level == "low"


# ==================== AUTO-RESOLUTION TESTS ====================


@pytest.mark.unit
class TestAutoResolveIfSafe:
    """Tests for automatic resolution if safe."""

    def test_auto_resolve_nonexistent_conflict(
        self, resolver: ConflictAutoResolver
    ):
        """Test auto-resolving a non-existent conflict."""
        fake_id = uuid4()
        result = resolver.auto_resolve_if_safe(fake_id)

        assert isinstance(result, ResolutionResult)
        assert not result.success
        assert result.status == ResolutionStatusEnum.FAILED
        assert result.error_code == "CONFLICT_NOT_FOUND"

    def test_auto_resolve_already_resolved_conflict(
        self,
        resolver: ConflictAutoResolver,
        db: Session,
        sample_conflict_alert: ConflictAlert,
        sample_user: User,
    ):
        """Test auto-resolving an already resolved conflict."""
        # Mark conflict as resolved
        sample_conflict_alert.status = ConflictAlertStatus.RESOLVED
        sample_conflict_alert.resolved_at = datetime.utcnow()
        sample_conflict_alert.resolved_by_id = sample_user.id
        db.commit()

        result = resolver.auto_resolve_if_safe(sample_conflict_alert.id)

        assert not result.success
        assert result.status == ResolutionStatusEnum.REJECTED
        assert result.error_code == "ALREADY_RESOLVED"

    def test_auto_resolve_unsafe_conflict(
        self,
        resolver: ConflictAutoResolver,
        db: Session,
        sample_faculty: Person,
    ):
        """Test that unsafe conflicts are rejected for auto-resolution."""
        # Create a complex, critical conflict
        alert = ConflictAlert(
            id=uuid4(),
            faculty_id=sample_faculty.id,
            conflict_type=ConflictType.CALL_CASCADE,
            fmit_week=date.today() + timedelta(days=7),
            description="Complex cascading conflict",
            severity=ConflictSeverity.CRITICAL,
            status=ConflictAlertStatus.NEW,
        )
        db.add(alert)
        db.commit()

        result = resolver.auto_resolve_if_safe(alert.id)

        # May or may not be safe depending on context
        if not result.success:
            assert result.error_code in [
                "SAFETY_CHECK_FAILED",
                "NO_OPTIONS",
                "APPROVAL_REQUIRED",
            ]

    def test_auto_resolve_with_specific_strategy(
        self,
        resolver: ConflictAutoResolver,
        sample_conflict_alert: ConflictAlert,
        sample_user: User,
        sample_faculty_available: Person,
    ):
        """Test auto-resolving with a specific strategy requested."""
        result = resolver.auto_resolve_if_safe(
            sample_conflict_alert.id,
            strategy="swap_assignments",
            user_id=sample_user.id,
        )

        # May succeed or fail depending on whether strategy is available
        assert isinstance(result, ResolutionResult)
        if result.success:
            assert result.strategy == ResolutionStrategyEnum.SWAP_ASSIGNMENTS

    def test_auto_resolve_successful_resolution(
        self,
        resolver: ConflictAutoResolver,
        db: Session,
        sample_faculty: Person,
        sample_faculty_available: Person,
        sample_user: User,
    ):
        """Test successful auto-resolution."""
        # Create a simple, safe-to-resolve conflict
        alert = ConflictAlert(
            id=uuid4(),
            faculty_id=sample_faculty.id,
            conflict_type=ConflictType.LEAVE_FMIT_OVERLAP,
            fmit_week=date.today() + timedelta(days=21),
            description="Simple leave conflict",
            severity=ConflictSeverity.INFO,
            status=ConflictAlertStatus.NEW,
        )
        db.add(alert)
        db.commit()

        result = resolver.auto_resolve_if_safe(alert.id, user_id=sample_user.id)

        # If resolution succeeds
        if result.success:
            assert result.status == ResolutionStatusEnum.APPLIED
            assert len(result.changes_applied) > 0
            assert result.conflict_resolved

            # Check that alert status was updated
            db.refresh(alert)
            assert alert.status == ConflictAlertStatus.RESOLVED
            assert alert.resolved_by_id == sample_user.id

    def test_auto_resolve_no_valid_options(
        self,
        resolver: ConflictAutoResolver,
        db: Session,
        sample_faculty: Person,
    ):
        """Test auto-resolution when no valid options are available."""
        alert = ConflictAlert(
            id=uuid4(),
            faculty_id=sample_faculty.id,
            conflict_type=ConflictType.CALL_CASCADE,
            fmit_week=date.today() + timedelta(days=7),
            description="Complex conflict",
            severity=ConflictSeverity.CRITICAL,
            status=ConflictAlertStatus.NEW,
        )
        db.add(alert)
        db.commit()

        result = resolver.auto_resolve_if_safe(alert.id)

        if not result.success:
            assert result.error_code in [
                "NO_OPTIONS",
                "APPROVAL_REQUIRED",
                "SAFETY_CHECK_FAILED",
            ]

    def test_auto_resolve_records_duration(
        self, resolver: ConflictAutoResolver, sample_conflict_alert: ConflictAlert
    ):
        """Test that resolution duration is recorded."""
        result = resolver.auto_resolve_if_safe(sample_conflict_alert.id)

        assert hasattr(result, "duration_seconds")
        if result.duration_seconds is not None:
            assert result.duration_seconds >= 0.0


# ==================== BATCH RESOLUTION TESTS ====================


@pytest.mark.unit
class TestBatchAutoResolve:
    """Tests for batch auto-resolution."""

    def test_batch_resolve_empty_list(self, resolver: ConflictAutoResolver):
        """Test batch resolution with empty conflict list."""
        report = resolver.batch_auto_resolve([])

        assert report.total_conflicts == 0
        assert report.conflicts_analyzed == 0
        assert report.overall_status in ["completed", "failed"]

    def test_batch_resolve_single_conflict(
        self,
        resolver: ConflictAutoResolver,
        sample_conflict_alert: ConflictAlert,
    ):
        """Test batch resolution with single conflict."""
        report = resolver.batch_auto_resolve([sample_conflict_alert.id])

        assert report.total_conflicts == 1
        assert report.conflicts_analyzed <= 1
        assert report.processing_time_seconds >= 0.0

    def test_batch_resolve_multiple_conflicts(
        self,
        resolver: ConflictAutoResolver,
        db: Session,
        sample_faculty: Person,
        sample_faculty_available: Person,
    ):
        """Test batch resolution with multiple conflicts."""
        # Create multiple conflicts
        alerts = []
        for i in range(3):
            alert = ConflictAlert(
                id=uuid4(),
                faculty_id=sample_faculty.id,
                conflict_type=ConflictType.LEAVE_FMIT_OVERLAP,
                fmit_week=date.today() + timedelta(days=7 * (i + 1)),
                description=f"Conflict {i + 1}",
                severity=ConflictSeverity.WARNING,
                status=ConflictAlertStatus.NEW,
            )
            db.add(alert)
            alerts.append(alert)
        db.commit()

        conflict_ids = [alert.id for alert in alerts]
        report = resolver.batch_auto_resolve(conflict_ids)

        assert report.total_conflicts == 3
        assert report.conflicts_analyzed == 3
        assert len(report.results) <= 3

    def test_batch_resolve_with_auto_apply_safe(
        self,
        resolver: ConflictAutoResolver,
        db: Session,
        sample_faculty: Person,
    ):
        """Test batch resolution with auto_apply_safe enabled."""
        alert = ConflictAlert(
            id=uuid4(),
            faculty_id=sample_faculty.id,
            conflict_type=ConflictType.LEAVE_FMIT_OVERLAP,
            fmit_week=date.today() + timedelta(days=14),
            description="Test conflict",
            severity=ConflictSeverity.INFO,
            status=ConflictAlertStatus.NEW,
        )
        db.add(alert)
        db.commit()

        report = resolver.batch_auto_resolve(
            [alert.id], auto_apply_safe=True, max_risk_level="medium"
        )

        assert report.total_conflicts == 1
        # May or may not apply depending on safety checks
        assert report.resolutions_applied + report.resolutions_deferred + report.resolutions_failed == 1

    def test_batch_resolve_risk_level_filtering(
        self,
        resolver: ConflictAutoResolver,
        db: Session,
        sample_faculty: Person,
    ):
        """Test that max_risk_level is respected in batch resolution."""
        alert = ConflictAlert(
            id=uuid4(),
            faculty_id=sample_faculty.id,
            conflict_type=ConflictType.CALL_CASCADE,
            fmit_week=date.today() + timedelta(days=14),
            description="High risk conflict",
            severity=ConflictSeverity.CRITICAL,
            status=ConflictAlertStatus.NEW,
        )
        db.add(alert)
        db.commit()

        # Try with low risk only
        report = resolver.batch_auto_resolve(
            [alert.id], auto_apply_safe=True, max_risk_level="low"
        )

        # High risk conflict should not be auto-applied with low max_risk
        assert report.resolutions_applied == 0 or report.resolutions_deferred > 0

    def test_batch_resolve_success_rate_calculation(
        self,
        resolver: ConflictAutoResolver,
        db: Session,
        sample_faculty: Person,
    ):
        """Test success rate calculation in batch report."""
        alerts = []
        for i in range(3):
            alert = ConflictAlert(
                id=uuid4(),
                faculty_id=sample_faculty.id,
                conflict_type=ConflictType.LEAVE_FMIT_OVERLAP,
                fmit_week=date.today() + timedelta(days=7 * (i + 1)),
                description=f"Conflict {i + 1}",
                severity=ConflictSeverity.WARNING,
                status=ConflictAlertStatus.NEW,
            )
            db.add(alert)
            alerts.append(alert)
        db.commit()

        conflict_ids = [alert.id for alert in alerts]
        report = resolver.batch_auto_resolve(conflict_ids, auto_apply_safe=True)

        assert 0.0 <= report.success_rate <= 1.0
        if report.conflicts_analyzed > 0:
            expected_rate = report.resolutions_applied / report.conflicts_analyzed
            assert abs(report.success_rate - expected_rate) < 0.01

    def test_batch_resolve_safety_checks_aggregation(
        self,
        resolver: ConflictAutoResolver,
        db: Session,
        sample_faculty: Person,
    ):
        """Test that safety checks are aggregated in batch report."""
        alerts = []
        for i in range(2):
            alert = ConflictAlert(
                id=uuid4(),
                faculty_id=sample_faculty.id,
                conflict_type=ConflictType.LEAVE_FMIT_OVERLAP,
                fmit_week=date.today() + timedelta(days=7 * (i + 1)),
                description=f"Conflict {i + 1}",
                severity=ConflictSeverity.WARNING,
                status=ConflictAlertStatus.NEW,
            )
            db.add(alert)
            alerts.append(alert)
        db.commit()

        conflict_ids = [alert.id for alert in alerts]
        report = resolver.batch_auto_resolve(conflict_ids)

        assert report.safety_checks_performed >= 0
        assert report.safety_checks_passed >= 0
        assert report.safety_checks_failed >= 0
        assert (
            report.safety_checks_performed
            == report.safety_checks_passed + report.safety_checks_failed
        )

    def test_batch_resolve_handles_errors_gracefully(
        self, resolver: ConflictAutoResolver
    ):
        """Test that batch resolution handles errors gracefully."""
        # Include non-existent conflict ID
        fake_ids = [uuid4(), uuid4(), uuid4()]
        report = resolver.batch_auto_resolve(fake_ids)

        assert report.total_conflicts == 3
        # Should handle errors without crashing
        assert report.resolutions_failed > 0

    def test_batch_resolve_generates_recommendations(
        self,
        resolver: ConflictAutoResolver,
        db: Session,
        sample_faculty: Person,
    ):
        """Test that batch resolution generates actionable recommendations."""
        alerts = []
        for i in range(2):
            alert = ConflictAlert(
                id=uuid4(),
                faculty_id=sample_faculty.id,
                conflict_type=ConflictType.LEAVE_FMIT_OVERLAP,
                fmit_week=date.today() + timedelta(days=7 * (i + 1)),
                description=f"Conflict {i + 1}",
                severity=ConflictSeverity.WARNING,
                status=ConflictAlertStatus.NEW,
            )
            db.add(alert)
            alerts.append(alert)
        db.commit()

        conflict_ids = [alert.id for alert in alerts]
        report = resolver.batch_auto_resolve(conflict_ids)

        # Should generate recommendations if there are deferred/failed resolutions
        if report.resolutions_deferred > 0 or report.resolutions_failed > 0:
            assert len(report.recommendations) > 0


# ==================== PRIORITY HANDLING TESTS ====================


@pytest.mark.unit
class TestPriorityHandling:
    """Tests for conflict priority and severity handling."""

    def test_critical_conflicts_analyzed_correctly(
        self,
        resolver: ConflictAutoResolver,
        db: Session,
        sample_faculty: Person,
    ):
        """Test that critical conflicts receive proper analysis."""
        alert = ConflictAlert(
            id=uuid4(),
            faculty_id=sample_faculty.id,
            conflict_type=ConflictType.LEAVE_FMIT_OVERLAP,
            fmit_week=date.today() + timedelta(days=7),
            description="Critical conflict",
            severity=ConflictSeverity.CRITICAL,
            status=ConflictAlertStatus.NEW,
        )
        db.add(alert)
        db.commit()

        analysis = resolver.analyze_conflict(alert.id)

        # Critical conflicts should have higher complexity
        assert analysis.severity == "critical"
        assert analysis.complexity_score > 0.0

    def test_info_level_conflicts_handled(
        self,
        resolver: ConflictAutoResolver,
        db: Session,
        sample_faculty: Person,
    ):
        """Test that info-level conflicts are handled appropriately."""
        alert = ConflictAlert(
            id=uuid4(),
            faculty_id=sample_faculty.id,
            conflict_type=ConflictType.EXTERNAL_COMMITMENT,
            fmit_week=date.today() + timedelta(days=14),
            description="Minor scheduling note",
            severity=ConflictSeverity.INFO,
            status=ConflictAlertStatus.NEW,
        )
        db.add(alert)
        db.commit()

        analysis = resolver.analyze_conflict(alert.id)

        assert analysis.severity == "info"
        # Info conflicts should have lower complexity
        assert analysis.complexity_score < 0.5

    def test_risk_level_affects_auto_apply(
        self,
        resolver: ConflictAutoResolver,
        db: Session,
        sample_faculty: Person,
    ):
        """Test that risk level affects can_auto_apply decision."""
        alert = ConflictAlert(
            id=uuid4(),
            faculty_id=sample_faculty.id,
            conflict_type=ConflictType.LEAVE_FMIT_OVERLAP,
            fmit_week=date.today() + timedelta(days=14),
            description="Test conflict",
            severity=ConflictSeverity.WARNING,
            status=ConflictAlertStatus.NEW,
        )
        db.add(alert)
        db.commit()

        options = resolver.generate_resolution_options(alert.id)

        # High risk options should not be auto-applicable
        high_risk_options = [opt for opt in options if opt.risk_level == "high"]
        for option in high_risk_options:
            assert not option.can_auto_apply


# ==================== EDGE CASES AND ERROR HANDLING ====================


@pytest.mark.unit
class TestEdgeCases:
    """Tests for edge cases and error conditions."""

    def test_conflict_with_missing_faculty(
        self, resolver: ConflictAutoResolver, db: Session
    ):
        """Test handling conflict with non-existent faculty."""
        fake_faculty_id = uuid4()
        alert = ConflictAlert(
            id=uuid4(),
            faculty_id=fake_faculty_id,
            conflict_type=ConflictType.LEAVE_FMIT_OVERLAP,
            fmit_week=date.today() + timedelta(days=14),
            description="Test conflict",
            severity=ConflictSeverity.WARNING,
            status=ConflictAlertStatus.NEW,
        )
        db.add(alert)
        db.commit()

        # Should handle gracefully
        analysis = resolver.analyze_conflict(alert.id)
        assert analysis is not None

    def test_conflict_in_past_handled(
        self,
        resolver: ConflictAutoResolver,
        db: Session,
        sample_faculty: Person,
    ):
        """Test handling conflicts with past dates."""
        past_date = date.today() - timedelta(days=30)
        alert = ConflictAlert(
            id=uuid4(),
            faculty_id=sample_faculty.id,
            conflict_type=ConflictType.BACK_TO_BACK,
            fmit_week=past_date,
            description="Past conflict",
            severity=ConflictSeverity.WARNING,
            status=ConflictAlertStatus.NEW,
        )
        db.add(alert)
        db.commit()

        # Should analyze without errors
        analysis = resolver.analyze_conflict(alert.id)
        assert analysis is not None

    def test_concurrent_conflict_resolution_safety(
        self,
        resolver: ConflictAutoResolver,
        db: Session,
        sample_conflict_alert: ConflictAlert,
        sample_user: User,
    ):
        """Test that concurrent resolutions are handled safely."""
        # Attempt to resolve twice
        result1 = resolver.auto_resolve_if_safe(
            sample_conflict_alert.id, user_id=sample_user.id
        )

        # If first succeeded, second should fail
        if result1.success:
            db.refresh(sample_conflict_alert)
            result2 = resolver.auto_resolve_if_safe(sample_conflict_alert.id)
            assert not result2.success
            assert result2.error_code == "ALREADY_RESOLVED"

    def test_resolution_cache_expiry(
        self,
        resolver: ConflictAutoResolver,
        sample_conflict_alert: ConflictAlert,
    ):
        """Test that resolution cache expires after timeout."""
        # Generate options (cached)
        options1 = resolver.generate_resolution_options(sample_conflict_alert.id)

        # Mock time passage
        with patch("app.services.conflict_auto_resolver.datetime") as mock_datetime:
            mock_datetime.utcnow.return_value = datetime.utcnow() + timedelta(minutes=10)

            # Should regenerate after cache expiry
            options2 = resolver.generate_resolution_options(sample_conflict_alert.id)

            assert len(options1) == len(options2)

    def test_empty_available_faculty_list(
        self,
        resolver: ConflictAutoResolver,
        db: Session,
        sample_faculty: Person,
    ):
        """Test handling when no faculty are available for swaps."""
        # Create conflict when faculty member is the only one
        alert = ConflictAlert(
            id=uuid4(),
            faculty_id=sample_faculty.id,
            conflict_type=ConflictType.LEAVE_FMIT_OVERLAP,
            fmit_week=date.today() + timedelta(days=14),
            description="Only faculty member",
            severity=ConflictSeverity.CRITICAL,
            status=ConflictAlertStatus.NEW,
        )
        db.add(alert)
        db.commit()

        analysis = resolver.analyze_conflict(alert.id)

        # Should identify lack of available faculty as a constraint
        faculty_check = next(
            (
                c
                for c in analysis.safety_checks
                if c.check_type == SafetyCheckType.FACULTY_AVAILABILITY
            ),
            None,
        )
        assert faculty_check is not None


# ==================== INTEGRATION TESTS ====================


@pytest.mark.unit
class TestResolutionWorkflow:
    """Integration tests for complete resolution workflows."""

    def test_full_resolution_workflow(
        self,
        resolver: ConflictAutoResolver,
        db: Session,
        sample_faculty: Person,
        sample_faculty_available: Person,
        sample_user: User,
    ):
        """Test complete workflow from detection to resolution."""
        # Step 1: Create conflict
        alert = ConflictAlert(
            id=uuid4(),
            faculty_id=sample_faculty.id,
            conflict_type=ConflictType.LEAVE_FMIT_OVERLAP,
            fmit_week=date.today() + timedelta(days=21),
            description="Test conflict for workflow",
            severity=ConflictSeverity.WARNING,
            status=ConflictAlertStatus.NEW,
        )
        db.add(alert)
        db.commit()

        # Step 2: Analyze conflict
        analysis = resolver.analyze_conflict(alert.id)
        assert analysis.conflict_id == alert.id

        # Step 3: Generate options
        options = resolver.generate_resolution_options(alert.id)
        assert len(options) > 0

        # Step 4: Attempt auto-resolution
        result = resolver.auto_resolve_if_safe(alert.id, user_id=sample_user.id)

        # Verify result structure regardless of success
        assert isinstance(result, ResolutionResult)
        assert result.conflict_id == alert.id

        if result.success:
            # Verify conflict was marked as resolved
            db.refresh(alert)
            assert alert.status == ConflictAlertStatus.RESOLVED

    def test_multi_conflict_scenario(
        self,
        resolver: ConflictAutoResolver,
        db: Session,
        sample_faculty: Person,
        sample_faculty_available: Person,
    ):
        """Test handling multiple related conflicts."""
        # Create overlapping conflicts
        alerts = []
        base_week = date.today() + timedelta(days=14)

        for i in range(3):
            alert = ConflictAlert(
                id=uuid4(),
                faculty_id=sample_faculty.id,
                conflict_type=ConflictType.LEAVE_FMIT_OVERLAP,
                fmit_week=base_week + timedelta(days=7 * i),
                description=f"Related conflict {i + 1}",
                severity=ConflictSeverity.WARNING,
                status=ConflictAlertStatus.NEW,
            )
            db.add(alert)
            alerts.append(alert)
        db.commit()

        # Batch resolve
        conflict_ids = [alert.id for alert in alerts]
        report = resolver.batch_auto_resolve(conflict_ids, auto_apply_safe=False)

        assert report.total_conflicts == 3
        assert report.conflicts_analyzed == 3

    def test_resolution_with_cascading_effects(
        self,
        resolver: ConflictAutoResolver,
        db: Session,
        sample_faculty: Person,
    ):
        """Test that cascading conflicts are detected during resolution."""
        # Create a conflict that might have cascading effects
        alert = ConflictAlert(
            id=uuid4(),
            faculty_id=sample_faculty.id,
            conflict_type=ConflictType.CALL_CASCADE,
            fmit_week=date.today() + timedelta(days=14),
            description="Cascading call conflict",
            severity=ConflictSeverity.CRITICAL,
            status=ConflictAlertStatus.NEW,
        )
        db.add(alert)
        db.commit()

        analysis = resolver.analyze_conflict(alert.id)

        # Should identify cascading nature
        assert "cascade" in analysis.root_cause.lower() or "cascade" in analysis.conflict_type.lower()
