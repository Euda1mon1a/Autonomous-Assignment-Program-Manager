"""Tests for emergency deployment schemas (enums, Field bounds, defaults)."""

from datetime import date, datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas.emergency_deployment import (
    EmergencyStrategy,
    FragilityAssessment,
    RepairOutcome,
    HealthVerification,
    EmergencyDeploymentRequest,
    EmergencyDeploymentResponse,
)


class TestEmergencyStrategy:
    def test_values(self):
        assert EmergencyStrategy.INCREMENTAL.value == "incremental"
        assert EmergencyStrategy.CASCADE.value == "cascade"
        assert EmergencyStrategy.FALLBACK.value == "fallback"

    def test_count(self):
        assert len(EmergencyStrategy) == 3

    def test_is_str(self):
        assert isinstance(EmergencyStrategy.INCREMENTAL, str)


class TestFragilityAssessment:
    def test_valid(self):
        r = FragilityAssessment(
            fragility_score=0.5,
            rd_mean=2.3,
            rd_max=5,
            affected_slots=10,
            recommended_strategy=EmergencyStrategy.CASCADE,
            assessment_time_ms=15.0,
        )
        assert r.fragility_score == 0.5
        assert r.recommended_strategy == EmergencyStrategy.CASCADE

    # --- fragility_score ge=0.0, le=1.0 ---

    def test_fragility_score_boundaries(self):
        r = FragilityAssessment(
            fragility_score=0.0,
            rd_mean=0.0,
            rd_max=0,
            affected_slots=0,
            recommended_strategy=EmergencyStrategy.INCREMENTAL,
            assessment_time_ms=0.0,
        )
        assert r.fragility_score == 0.0

        r = FragilityAssessment(
            fragility_score=1.0,
            rd_mean=0.0,
            rd_max=0,
            affected_slots=0,
            recommended_strategy=EmergencyStrategy.FALLBACK,
            assessment_time_ms=0.0,
        )
        assert r.fragility_score == 1.0

    def test_fragility_score_negative(self):
        with pytest.raises(ValidationError):
            FragilityAssessment(
                fragility_score=-0.1,
                rd_mean=0.0,
                rd_max=0,
                affected_slots=0,
                recommended_strategy=EmergencyStrategy.INCREMENTAL,
                assessment_time_ms=0.0,
            )

    def test_fragility_score_above_one(self):
        with pytest.raises(ValidationError):
            FragilityAssessment(
                fragility_score=1.1,
                rd_mean=0.0,
                rd_max=0,
                affected_slots=0,
                recommended_strategy=EmergencyStrategy.INCREMENTAL,
                assessment_time_ms=0.0,
            )

    # --- rd_mean ge=0.0 ---

    def test_rd_mean_negative(self):
        with pytest.raises(ValidationError):
            FragilityAssessment(
                fragility_score=0.5,
                rd_mean=-1.0,
                rd_max=0,
                affected_slots=0,
                recommended_strategy=EmergencyStrategy.INCREMENTAL,
                assessment_time_ms=0.0,
            )

    # --- rd_max ge=0 ---

    def test_rd_max_negative(self):
        with pytest.raises(ValidationError):
            FragilityAssessment(
                fragility_score=0.5,
                rd_mean=0.0,
                rd_max=-1,
                affected_slots=0,
                recommended_strategy=EmergencyStrategy.INCREMENTAL,
                assessment_time_ms=0.0,
            )

    # --- affected_slots ge=0 ---

    def test_affected_slots_negative(self):
        with pytest.raises(ValidationError):
            FragilityAssessment(
                fragility_score=0.5,
                rd_mean=0.0,
                rd_max=0,
                affected_slots=-1,
                recommended_strategy=EmergencyStrategy.INCREMENTAL,
                assessment_time_ms=0.0,
            )

    # --- assessment_time_ms ge=0 ---

    def test_assessment_time_negative(self):
        with pytest.raises(ValidationError):
            FragilityAssessment(
                fragility_score=0.5,
                rd_mean=0.0,
                rd_max=0,
                affected_slots=0,
                recommended_strategy=EmergencyStrategy.INCREMENTAL,
                assessment_time_ms=-1.0,
            )


class TestRepairOutcome:
    def test_valid_minimal(self):
        r = RepairOutcome(
            success=True,
            strategy_used=EmergencyStrategy.INCREMENTAL,
            execution_time_ms=100.0,
        )
        assert r.slots_repaired == 0
        assert r.slots_remaining == 0
        assert r.cascade_steps == 0
        assert r.fallback_activated is None
        assert r.details == []

    def test_full(self):
        r = RepairOutcome(
            success=False,
            strategy_used=EmergencyStrategy.CASCADE,
            slots_repaired=8,
            slots_remaining=2,
            cascade_steps=3,
            fallback_activated="static_fallback",
            execution_time_ms=250.0,
            details=["Step 1: ...", "Step 2: ..."],
        )
        assert r.slots_remaining == 2
        assert len(r.details) == 2

    # --- execution_time_ms ge=0 ---

    def test_execution_time_negative(self):
        with pytest.raises(ValidationError):
            RepairOutcome(
                success=True,
                strategy_used=EmergencyStrategy.INCREMENTAL,
                execution_time_ms=-1.0,
            )


class TestHealthVerification:
    def test_valid(self):
        r = HealthVerification(
            coverage_rate=0.98,
            is_healthy=True,
        )
        assert r.escalated is False
        assert r.escalation_severity is None

    # --- coverage_rate ge=0.0, le=1.0 ---

    def test_coverage_rate_boundaries(self):
        r = HealthVerification(coverage_rate=0.0, is_healthy=False)
        assert r.coverage_rate == 0.0
        r = HealthVerification(coverage_rate=1.0, is_healthy=True)
        assert r.coverage_rate == 1.0

    def test_coverage_rate_negative(self):
        with pytest.raises(ValidationError):
            HealthVerification(coverage_rate=-0.1, is_healthy=False)

    def test_coverage_rate_above_one(self):
        with pytest.raises(ValidationError):
            HealthVerification(coverage_rate=1.1, is_healthy=True)

    def test_with_escalation(self):
        r = HealthVerification(
            coverage_rate=0.8,
            is_healthy=False,
            escalated=True,
            escalation_severity="critical",
        )
        assert r.escalated is True
        assert r.escalation_severity == "critical"


class TestEmergencyDeploymentRequest:
    def test_defaults(self):
        r = EmergencyDeploymentRequest(
            person_id=uuid4(),
            start_date=date(2026, 3, 1),
            end_date=date(2026, 3, 14),
        )
        assert r.reason == "deployment"
        assert r.notes is None
        assert r.dry_run is True
        assert r.force_strategy is None

    def test_full(self):
        r = EmergencyDeploymentRequest(
            person_id=uuid4(),
            start_date=date(2026, 3, 1),
            end_date=date(2026, 3, 14),
            reason="emergency_leave",
            notes="Family emergency",
            dry_run=False,
            force_strategy=EmergencyStrategy.CASCADE,
        )
        assert r.dry_run is False
        assert r.force_strategy == EmergencyStrategy.CASCADE


class TestEmergencyDeploymentResponse:
    def _make_assessment(self):
        return FragilityAssessment(
            fragility_score=0.3,
            rd_mean=1.5,
            rd_max=3,
            affected_slots=6,
            recommended_strategy=EmergencyStrategy.INCREMENTAL,
            assessment_time_ms=10.0,
        )

    def test_valid_dry_run(self):
        r = EmergencyDeploymentResponse(
            request_id=uuid4(),
            person_id=uuid4(),
            start_date=date(2026, 3, 1),
            end_date=date(2026, 3, 14),
            dry_run=True,
            assessment=self._make_assessment(),
            overall_success=True,
            total_time_ms=50.0,
        )
        assert r.repair_outcome is None
        assert r.health_check is None
        assert r.recommendations == []
        assert r.warnings == []
        assert r.errors == []

    def test_valid_full(self):
        repair = RepairOutcome(
            success=True,
            strategy_used=EmergencyStrategy.INCREMENTAL,
            slots_repaired=6,
            execution_time_ms=200.0,
        )
        health = HealthVerification(coverage_rate=0.98, is_healthy=True)
        r = EmergencyDeploymentResponse(
            request_id=uuid4(),
            person_id=uuid4(),
            start_date=date(2026, 3, 1),
            end_date=date(2026, 3, 14),
            dry_run=False,
            assessment=self._make_assessment(),
            repair_outcome=repair,
            health_check=health,
            overall_success=True,
            total_time_ms=300.0,
            recommendations=["Monitor coverage"],
        )
        assert r.repair_outcome.slots_repaired == 6
        assert r.health_check.is_healthy is True
        assert len(r.recommendations) == 1

    # --- total_time_ms ge=0 ---

    def test_total_time_negative(self):
        with pytest.raises(ValidationError):
            EmergencyDeploymentResponse(
                request_id=uuid4(),
                person_id=uuid4(),
                start_date=date(2026, 3, 1),
                end_date=date(2026, 3, 14),
                dry_run=True,
                assessment=self._make_assessment(),
                overall_success=True,
                total_time_ms=-1.0,
            )
