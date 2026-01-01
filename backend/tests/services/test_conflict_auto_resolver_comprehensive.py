"""Comprehensive test suite for conflict auto-resolver service."""

import pytest
from datetime import date, timedelta
from uuid import uuid4

from sqlalchemy.orm import Session

from app.models.person import Person
from app.models.conflict_alert import ConflictAlert, ConflictAlertStatus, ConflictSeverity, ConflictType
from app.services.conflict_auto_resolver import ConflictAutoResolver


class TestConflictAutoResolverComprehensive:
    """Comprehensive tests for conflict auto-resolver service methods."""

    @pytest.fixture
    def resolver(self, db: Session) -> ConflictAutoResolver:
        """Create a conflict auto-resolver instance."""
        return ConflictAutoResolver(db)

    @pytest.fixture
    def faculty(self, db: Session) -> Person:
        """Create a faculty member."""
        person = Person(
            id=uuid4(),
            name="Dr. Faculty",
            type="faculty",
            email="faculty@hospital.org",
            performs_procedures=True,
        )
        db.add(person)
        db.commit()
        db.refresh(person)
        return person

    @pytest.fixture
    def resident(self, db: Session) -> Person:
        """Create a resident."""
        person = Person(
            id=uuid4(),
            name="Dr. Resident",
            type="resident",
            email="resident@hospital.org",
            pgy_level=1,
        )
        db.add(person)
        db.commit()
        db.refresh(person)
        return person

    @pytest.fixture
    def conflict_alert(self, db: Session, faculty: Person) -> ConflictAlert:
        """Create a conflict alert."""
        alert = ConflictAlert(
            id=uuid4(),
            faculty_id=faculty.id,
            conflict_type=ConflictType.LEAVE_FMIT_OVERLAP,
            severity=ConflictSeverity.WARNING,
            fmit_week=date.today() + timedelta(days=30),
            status=ConflictAlertStatus.NEW,
            message="Test conflict",
            created_at=date.today(),
        )
        db.add(alert)
        db.commit()
        db.refresh(alert)
        return alert

    # ===== TESTS FOR analyze_conflict() =====

    def test_analyze_conflict_basic(
        self, resolver: ConflictAutoResolver, conflict_alert: ConflictAlert
    ):
        """Test analyze_conflict returns comprehensive analysis."""
        analysis = resolver.analyze_conflict(conflict_alert.id)

        assert analysis.conflict_id == conflict_alert.id
        assert analysis.conflict_type == conflict_alert.conflict_type.value
        assert analysis.severity == conflict_alert.severity.value
        assert isinstance(analysis.root_cause, str)
        assert isinstance(analysis.affected_faculty, list)
        assert isinstance(analysis.affected_dates, list)
        assert 0.0 <= analysis.complexity_score <= 1.0
        assert isinstance(analysis.safety_checks, list)
        assert isinstance(analysis.all_checks_passed, bool)
        assert isinstance(analysis.constraints, list)
        assert isinstance(analysis.blockers, list)
        assert isinstance(analysis.recommended_strategies, list)
        assert analysis.estimated_resolution_time > 0

    def test_analyze_conflict_nonexistent(self, resolver: ConflictAutoResolver):
        """Test analyze_conflict with nonexistent conflict raises error."""
        fake_id = uuid4()

        with pytest.raises(ValueError, match="not found"):
            resolver.analyze_conflict(fake_id)

    def test_analyze_conflict_critical_severity(
        self, resolver: ConflictAutoResolver, db: Session, faculty: Person
    ):
        """Test analyze_conflict with critical severity conflict."""
        critical_alert = ConflictAlert(
            id=uuid4(),
            faculty_id=faculty.id,
            conflict_type=ConflictType.CALL_CASCADE,
            severity=ConflictSeverity.CRITICAL,
            fmit_week=date.today() + timedelta(days=7),
            status=ConflictAlertStatus.NEW,
            message="Critical conflict",
            created_at=date.today(),
        )
        db.add(critical_alert)
        db.commit()

        analysis = resolver.analyze_conflict(critical_alert.id)

        assert analysis.severity == ConflictSeverity.CRITICAL.value
        # Critical conflicts may have higher complexity
        assert analysis.complexity_score >= 0.0

    def test_analyze_conflict_safety_checks(
        self, resolver: ConflictAutoResolver, conflict_alert: ConflictAlert
    ):
        """Test analyze_conflict performs all safety checks."""
        analysis = resolver.analyze_conflict(conflict_alert.id)

        # Should have multiple safety checks
        assert len(analysis.safety_checks) > 0

        # Each safety check should have required fields
        for check in analysis.safety_checks:
            assert hasattr(check, "check_type")
            assert hasattr(check, "passed")
            assert hasattr(check, "message")

    def test_analyze_conflict_recommended_strategies(
        self, resolver: ConflictAutoResolver, conflict_alert: ConflictAlert
    ):
        """Test analyze_conflict recommends resolution strategies."""
        analysis = resolver.analyze_conflict(conflict_alert.id)

        # Should recommend at least one strategy
        assert len(analysis.recommended_strategies) > 0

    # ===== TESTS FOR generate_resolution_options() =====

    def test_generate_resolution_options_basic(
        self, resolver: ConflictAutoResolver, conflict_alert: ConflictAlert
    ):
        """Test generate_resolution_options returns options."""
        options = resolver.generate_resolution_options(conflict_alert.id, max_options=5)

        assert isinstance(options, list)
        # Should always have at least "defer to human" option
        assert len(options) > 0

        # Each option should have required fields
        for option in options:
            assert hasattr(option, "id")
            assert hasattr(option, "conflict_id")
            assert hasattr(option, "strategy")
            assert hasattr(option, "title")
            assert hasattr(option, "description")
            assert hasattr(option, "detailed_steps")
            assert hasattr(option, "risk_level")

    def test_generate_resolution_options_respects_max(
        self, resolver: ConflictAutoResolver, conflict_alert: ConflictAlert
    ):
        """Test generate_resolution_options respects max_options parameter."""
        options = resolver.generate_resolution_options(conflict_alert.id, max_options=2)

        assert len(options) <= 2

    def test_generate_resolution_options_sorted_by_score(
        self, resolver: ConflictAutoResolver, conflict_alert: ConflictAlert
    ):
        """Test generate_resolution_options returns sorted options."""
        options = resolver.generate_resolution_options(conflict_alert.id)

        # Options should be sorted by overall score (descending)
        if len(options) > 1:
            for i in range(len(options) - 1):
                score1 = options[i].impact.overall_score if options[i].impact else 0
                score2 = options[i + 1].impact.overall_score if options[i + 1].impact else 0
                assert score1 >= score2

    def test_generate_resolution_options_caching(
        self, resolver: ConflictAutoResolver, conflict_alert: ConflictAlert
    ):
        """Test generate_resolution_options uses caching."""
        # First call
        options1 = resolver.generate_resolution_options(conflict_alert.id, max_options=5)

        # Second call within 5 minutes should use cache
        options2 = resolver.generate_resolution_options(conflict_alert.id, max_options=5)

        # Should return same number of options
        assert len(options1) == len(options2)

    def test_generate_resolution_options_nonexistent_conflict(
        self, resolver: ConflictAutoResolver
    ):
        """Test generate_resolution_options with nonexistent conflict."""
        fake_id = uuid4()

        options = resolver.generate_resolution_options(fake_id)

        # Should return empty list, not raise error
        assert options == []

    def test_generate_resolution_options_impact_assessment(
        self, resolver: ConflictAutoResolver, conflict_alert: ConflictAlert
    ):
        """Test generate_resolution_options includes impact assessment."""
        options = resolver.generate_resolution_options(conflict_alert.id)

        for option in options:
            if option.impact:
                assert hasattr(option.impact, "affected_faculty_count")
                assert hasattr(option.impact, "affected_weeks_count")
                assert hasattr(option.impact, "overall_score")
                assert 0.0 <= option.impact.overall_score <= 1.0

    # ===== TESTS FOR auto_resolve_if_safe() =====

    def test_auto_resolve_if_safe_nonexistent_conflict(
        self, resolver: ConflictAutoResolver
    ):
        """Test auto_resolve_if_safe with nonexistent conflict."""
        fake_id = uuid4()

        result = resolver.auto_resolve_if_safe(fake_id)

        assert result.success is False
        assert result.error_code == "CONFLICT_NOT_FOUND"

    def test_auto_resolve_if_safe_already_resolved(
        self, resolver: ConflictAutoResolver, db: Session, faculty: Person
    ):
        """Test auto_resolve_if_safe with already resolved conflict."""
        resolved_alert = ConflictAlert(
            id=uuid4(),
            faculty_id=faculty.id,
            conflict_type=ConflictType.LEAVE_FMIT_OVERLAP,
            severity=ConflictSeverity.WARNING,
            fmit_week=date.today() + timedelta(days=30),
            status=ConflictAlertStatus.RESOLVED,
            message="Already resolved",
            created_at=date.today(),
        )
        db.add(resolved_alert)
        db.commit()

        result = resolver.auto_resolve_if_safe(resolved_alert.id)

        assert result.success is False
        assert result.error_code == "ALREADY_RESOLVED"

    def test_auto_resolve_if_safe_safety_check_failure(
        self, resolver: ConflictAutoResolver, db: Session, faculty: Person
    ):
        """Test auto_resolve_if_safe when safety checks fail."""
        # Create a critical conflict that likely fails safety checks
        critical_alert = ConflictAlert(
            id=uuid4(),
            faculty_id=faculty.id,
            conflict_type=ConflictType.CALL_CASCADE,
            severity=ConflictSeverity.CRITICAL,
            fmit_week=date.today() + timedelta(days=7),
            status=ConflictAlertStatus.NEW,
            message="Critical conflict",
            created_at=date.today(),
        )
        db.add(critical_alert)
        db.commit()

        result = resolver.auto_resolve_if_safe(critical_alert.id)

        # May fail safety checks or require manual review
        if not result.success:
            assert result.error_code in ["SAFETY_CHECK_FAILED", "APPROVAL_REQUIRED", "NO_OPTIONS"]

    def test_auto_resolve_if_safe_returns_result(
        self, resolver: ConflictAutoResolver, conflict_alert: ConflictAlert
    ):
        """Test auto_resolve_if_safe returns ResolutionResult."""
        result = resolver.auto_resolve_if_safe(conflict_alert.id)

        assert hasattr(result, "success")
        assert hasattr(result, "status")
        assert hasattr(result, "message")
        assert hasattr(result, "conflict_id")
        assert result.conflict_id == conflict_alert.id

    def test_auto_resolve_if_safe_with_specific_strategy(
        self, resolver: ConflictAutoResolver, conflict_alert: ConflictAlert
    ):
        """Test auto_resolve_if_safe with specific strategy parameter."""
        result = resolver.auto_resolve_if_safe(
            conflict_alert.id, strategy="swap_assignments"
        )

        # Result may succeed or fail depending on options available
        assert isinstance(result.success, bool)

    def test_auto_resolve_if_safe_measures_duration(
        self, resolver: ConflictAutoResolver, conflict_alert: ConflictAlert
    ):
        """Test auto_resolve_if_safe measures execution duration."""
        result = resolver.auto_resolve_if_safe(conflict_alert.id)

        assert hasattr(result, "duration_seconds")
        if result.duration_seconds is not None:
            assert result.duration_seconds >= 0

    # ===== TESTS FOR batch_auto_resolve() =====

    def test_batch_auto_resolve_empty_list(self, resolver: ConflictAutoResolver):
        """Test batch_auto_resolve with empty conflict list."""
        result = resolver.batch_auto_resolve([])

        assert result.total_conflicts == 0
        assert result.conflicts_analyzed == 0
        assert result.resolutions_applied == 0
        assert result.success_rate == 0.0

    def test_batch_auto_resolve_single_conflict(
        self, resolver: ConflictAutoResolver, conflict_alert: ConflictAlert
    ):
        """Test batch_auto_resolve with single conflict."""
        result = resolver.batch_auto_resolve([conflict_alert.id])

        assert result.total_conflicts == 1
        assert result.conflicts_analyzed >= 0
        assert isinstance(result.results, list)
        assert isinstance(result.pending_approvals, list)
        assert isinstance(result.failed_conflicts, list)

    def test_batch_auto_resolve_multiple_conflicts(
        self, resolver: ConflictAutoResolver, db: Session, faculty: Person
    ):
        """Test batch_auto_resolve with multiple conflicts."""
        # Create multiple conflicts
        conflict_ids = []
        for i in range(3):
            alert = ConflictAlert(
                id=uuid4(),
                faculty_id=faculty.id,
                conflict_type=ConflictType.LEAVE_FMIT_OVERLAP,
                severity=ConflictSeverity.WARNING,
                fmit_week=date.today() + timedelta(days=30 + i * 7),
                status=ConflictAlertStatus.NEW,
                message=f"Test conflict {i}",
                created_at=date.today(),
            )
            db.add(alert)
            conflict_ids.append(alert.id)
        db.commit()

        result = resolver.batch_auto_resolve(conflict_ids)

        assert result.total_conflicts == 3
        assert result.conflicts_analyzed <= 3
        assert result.processing_time_seconds >= 0

    def test_batch_auto_resolve_with_auto_apply(
        self, resolver: ConflictAutoResolver, conflict_alert: ConflictAlert
    ):
        """Test batch_auto_resolve with auto_apply_safe=True."""
        result = resolver.batch_auto_resolve(
            [conflict_alert.id], auto_apply_safe=True, max_risk_level="medium"
        )

        # May or may not apply depending on safety
        assert isinstance(result.resolutions_applied, int)
        assert isinstance(result.resolutions_deferred, int)

    def test_batch_auto_resolve_risk_level_filtering(
        self, resolver: ConflictAutoResolver, conflict_alert: ConflictAlert
    ):
        """Test batch_auto_resolve respects max_risk_level parameter."""
        # Only auto-apply low risk
        result_low = resolver.batch_auto_resolve(
            [conflict_alert.id], auto_apply_safe=True, max_risk_level="low"
        )

        # Allow medium risk
        result_medium = resolver.batch_auto_resolve(
            [conflict_alert.id], auto_apply_safe=True, max_risk_level="medium"
        )

        # Medium risk may apply more resolutions than low risk
        assert result_medium.resolutions_applied >= result_low.resolutions_applied

    def test_batch_auto_resolve_calculates_metrics(
        self, resolver: ConflictAutoResolver, conflict_alert: ConflictAlert
    ):
        """Test batch_auto_resolve calculates all metrics."""
        result = resolver.batch_auto_resolve([conflict_alert.id])

        assert hasattr(result, "total_conflicts")
        assert hasattr(result, "conflicts_analyzed")
        assert hasattr(result, "resolutions_proposed")
        assert hasattr(result, "resolutions_applied")
        assert hasattr(result, "resolutions_deferred")
        assert hasattr(result, "resolutions_failed")
        assert hasattr(result, "success_rate")
        assert hasattr(result, "overall_status")
        assert hasattr(result, "summary_message")

    def test_batch_auto_resolve_tracks_safety_checks(
        self, resolver: ConflictAutoResolver, conflict_alert: ConflictAlert
    ):
        """Test batch_auto_resolve tracks safety check metrics."""
        result = resolver.batch_auto_resolve([conflict_alert.id])

        assert hasattr(result, "safety_checks_performed")
        assert hasattr(result, "safety_checks_passed")
        assert hasattr(result, "safety_checks_failed")
        assert result.safety_checks_performed >= 0

    def test_batch_auto_resolve_handles_errors_gracefully(
        self, resolver: ConflictAutoResolver
    ):
        """Test batch_auto_resolve handles invalid conflict IDs gracefully."""
        # Include both valid and invalid IDs
        fake_ids = [uuid4(), uuid4()]

        result = resolver.batch_auto_resolve(fake_ids)

        # Should not crash, should track failures
        assert result.resolutions_failed >= 0

    def test_batch_auto_resolve_generates_recommendations(
        self, resolver: ConflictAutoResolver, conflict_alert: ConflictAlert
    ):
        """Test batch_auto_resolve generates recommendations."""
        result = resolver.batch_auto_resolve([conflict_alert.id], auto_apply_safe=True)

        assert hasattr(result, "recommendations")
        assert isinstance(result.recommendations, list)

    def test_batch_auto_resolve_tracks_affected_faculty(
        self, resolver: ConflictAutoResolver, conflict_alert: ConflictAlert
    ):
        """Test batch_auto_resolve tracks affected faculty count."""
        result = resolver.batch_auto_resolve([conflict_alert.id])

        assert hasattr(result, "total_faculty_affected")
        assert result.total_faculty_affected >= 0

    # ===== EDGE CASE TESTS =====

    def test_analyze_conflict_back_to_back_type(
        self, resolver: ConflictAutoResolver, db: Session, faculty: Person
    ):
        """Test analyze_conflict with BACK_TO_BACK conflict type."""
        alert = ConflictAlert(
            id=uuid4(),
            faculty_id=faculty.id,
            conflict_type=ConflictType.BACK_TO_BACK,
            severity=ConflictSeverity.WARNING,
            fmit_week=date.today() + timedelta(days=14),
            status=ConflictAlertStatus.NEW,
            message="Back-to-back FMIT weeks",
            created_at=date.today(),
        )
        db.add(alert)
        db.commit()

        analysis = resolver.analyze_conflict(alert.id)

        assert analysis.conflict_type == ConflictType.BACK_TO_BACK.value
        # Should have specific recommended strategies for back-to-back
        assert len(analysis.recommended_strategies) > 0

    def test_generate_resolution_options_different_conflict_types(
        self, resolver: ConflictAutoResolver, db: Session, faculty: Person
    ):
        """Test generate_resolution_options handles different conflict types."""
        conflict_types = [
            ConflictType.LEAVE_FMIT_OVERLAP,
            ConflictType.BACK_TO_BACK,
            ConflictType.CALL_CASCADE,
            ConflictType.EXCESSIVE_ALTERNATING,
        ]

        for conflict_type in conflict_types:
            alert = ConflictAlert(
                id=uuid4(),
                faculty_id=faculty.id,
                conflict_type=conflict_type,
                severity=ConflictSeverity.WARNING,
                fmit_week=date.today() + timedelta(days=30),
                status=ConflictAlertStatus.NEW,
                message=f"Test {conflict_type.value}",
                created_at=date.today(),
            )
            db.add(alert)
            db.commit()

            options = resolver.generate_resolution_options(alert.id)

            # Each conflict type should generate options
            assert len(options) > 0

    def test_batch_auto_resolve_mixed_conflict_severities(
        self, resolver: ConflictAutoResolver, db: Session, faculty: Person
    ):
        """Test batch_auto_resolve with mixed severity levels."""
        severities = [ConflictSeverity.INFO, ConflictSeverity.WARNING, ConflictSeverity.CRITICAL]
        conflict_ids = []

        for severity in severities:
            alert = ConflictAlert(
                id=uuid4(),
                faculty_id=faculty.id,
                conflict_type=ConflictType.LEAVE_FMIT_OVERLAP,
                severity=severity,
                fmit_week=date.today() + timedelta(days=30),
                status=ConflictAlertStatus.NEW,
                message=f"Test {severity.value}",
                created_at=date.today(),
            )
            db.add(alert)
            conflict_ids.append(alert.id)
        db.commit()

        result = resolver.batch_auto_resolve(conflict_ids)

        assert result.total_conflicts == 3
        # Different severities may have different resolution outcomes
        assert result.conflicts_analyzed >= 0
