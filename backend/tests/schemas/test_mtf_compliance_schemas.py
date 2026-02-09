"""Tests for MTF compliance schemas (Field bounds, enums, defaults)."""

from datetime import datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas.mtf_compliance import (
    DRRSCategory,
    PersonnelReadinessLevel,
    EquipmentReadinessLevel,
    MissionType,
    MissionCapabilityStatus,
    MFRType,
    MFRPriority,
    RiskLevel,
    CircuitBreakerState,
    CircuitBreakerTrigger,
    OverrideAuthority,
    DRRSReadinessRequest,
    MissionReadiness,
    DRRSReadinessResponse,
    MFRRequest,
    MFRResponse,
    RFFRequest,
    RFFResponse,
    CircuitBreakerStatusResponse,
    CircuitBreakerOverrideRequest,
    CircuitBreakerOverrideResponse,
    SafetyStandDownRequest,
    SafetyStandDownResponse,
    MFRHistoryItem,
    MFRHistoryResponse,
    CircuitBreakerEventHistoryItem,
    CircuitBreakerHistoryResponse,
    IronDomeStatusResponse,
)


# ── Enums ──────────────────────────────────────────────────────────────


class TestDRRSCategory:
    def test_values(self):
        assert DRRSCategory.C1 == "C-1"
        assert DRRSCategory.C2 == "C-2"
        assert DRRSCategory.C3 == "C-3"
        assert DRRSCategory.C4 == "C-4"
        assert DRRSCategory.C5 == "C-5"

    def test_count(self):
        assert len(DRRSCategory) == 5


class TestPersonnelReadinessLevel:
    def test_values(self):
        assert PersonnelReadinessLevel.P1 == "P-1"
        assert PersonnelReadinessLevel.P2 == "P-2"
        assert PersonnelReadinessLevel.P3 == "P-3"
        assert PersonnelReadinessLevel.P4 == "P-4"

    def test_count(self):
        assert len(PersonnelReadinessLevel) == 4


class TestEquipmentReadinessLevel:
    def test_values(self):
        assert EquipmentReadinessLevel.S1 == "S-1"
        assert EquipmentReadinessLevel.S2 == "S-2"
        assert EquipmentReadinessLevel.S3 == "S-3"
        assert EquipmentReadinessLevel.S4 == "S-4"

    def test_count(self):
        assert len(EquipmentReadinessLevel) == 4


class TestMissionType:
    def test_count(self):
        assert len(MissionType) == 8

    def test_sample(self):
        assert MissionType.LEVEL_1_TRAUMA == "level_1_trauma"
        assert MissionType.EMERGENCY_DEPARTMENT == "emergency_department"
        assert MissionType.GRADUATE_MEDICAL_EDUCATION == "graduate_medical_education"


class TestMissionCapabilityStatus:
    def test_values(self):
        assert MissionCapabilityStatus.FMC == "FMC"
        assert MissionCapabilityStatus.PMC == "PMC"
        assert MissionCapabilityStatus.NMC == "NMC"

    def test_count(self):
        assert len(MissionCapabilityStatus) == 3


class TestMFRType:
    def test_values(self):
        assert MFRType.RISK_ACCEPTANCE == "risk_acceptance"
        assert MFRType.SAFETY_CONCERN == "safety_concern"
        assert MFRType.COMPLIANCE_VIOLATION == "compliance_violation"
        assert MFRType.RESOURCE_REQUEST == "resource_request"
        assert MFRType.STAND_DOWN == "stand_down"

    def test_count(self):
        assert len(MFRType) == 5


class TestMFRPriority:
    def test_values(self):
        assert MFRPriority.ROUTINE == "routine"
        assert MFRPriority.PRIORITY == "priority"
        assert MFRPriority.IMMEDIATE == "immediate"
        assert MFRPriority.FLASH == "flash"

    def test_count(self):
        assert len(MFRPriority) == 4


class TestRiskLevel:
    def test_values(self):
        assert RiskLevel.LOW == "low"
        assert RiskLevel.MODERATE == "moderate"
        assert RiskLevel.HIGH == "high"
        assert RiskLevel.CRITICAL == "critical"
        assert RiskLevel.CATASTROPHIC == "catastrophic"

    def test_count(self):
        assert len(RiskLevel) == 5


class TestCircuitBreakerState:
    def test_values(self):
        assert CircuitBreakerState.CLOSED == "closed"
        assert CircuitBreakerState.HALF_OPEN == "half_open"
        assert CircuitBreakerState.OPEN == "open"

    def test_count(self):
        assert len(CircuitBreakerState) == 3


class TestCircuitBreakerTrigger:
    def test_count(self):
        assert len(CircuitBreakerTrigger) == 8

    def test_sample(self):
        assert CircuitBreakerTrigger.N1_VIOLATION == "n1_violation"
        assert CircuitBreakerTrigger.COVERAGE_COLLAPSE == "coverage_collapse"
        assert CircuitBreakerTrigger.MANUAL_ACTIVATION == "manual_activation"


class TestOverrideAuthority:
    def test_count(self):
        assert len(OverrideAuthority) == 6

    def test_sample(self):
        assert OverrideAuthority.SCHEDULER == "scheduler"
        assert OverrideAuthority.COMMANDER == "commander"
        assert OverrideAuthority.RISK_MANAGEMENT == "risk_management"


# ── DRRSReadinessRequest ─────────────────────────────────────────────


class TestDRRSReadinessRequest:
    def test_defaults(self):
        r = DRRSReadinessRequest()
        assert r.include_all_missions is True
        assert r.specific_missions is None


# ── MissionReadiness ─────────────────────────────────────────────────


class TestMissionReadiness:
    def test_valid(self):
        r = MissionReadiness(
            mission_type=MissionType.LEVEL_1_TRAUMA,
            mission_name="Level 1 Trauma",
            capability_status=MissionCapabilityStatus.FMC,
            personnel_rating=PersonnelReadinessLevel.P1,
            capability_rating=EquipmentReadinessLevel.S1,
            combined_rating=DRRSCategory.C1,
            deficiencies=[],
            degradation_percentage=0.0,
            recovery_actions=[],
        )
        assert r.degradation_percentage == 0.0

    # --- degradation_percentage (ge=0.0, le=100.0) ---

    def test_degradation_below_min(self):
        with pytest.raises(ValidationError):
            MissionReadiness(
                mission_type=MissionType.LEVEL_1_TRAUMA,
                mission_name="T",
                capability_status=MissionCapabilityStatus.FMC,
                personnel_rating=PersonnelReadinessLevel.P1,
                capability_rating=EquipmentReadinessLevel.S1,
                combined_rating=DRRSCategory.C1,
                deficiencies=[],
                degradation_percentage=-1.0,
                recovery_actions=[],
            )

    def test_degradation_above_max(self):
        with pytest.raises(ValidationError):
            MissionReadiness(
                mission_type=MissionType.LEVEL_1_TRAUMA,
                mission_name="T",
                capability_status=MissionCapabilityStatus.FMC,
                personnel_rating=PersonnelReadinessLevel.P1,
                capability_rating=EquipmentReadinessLevel.S1,
                combined_rating=DRRSCategory.C1,
                deficiencies=[],
                degradation_percentage=100.1,
                recovery_actions=[],
            )


# ── MFRRequest ───────────────────────────────────────────────────────


class TestMFRRequest:
    def test_defaults(self):
        r = MFRRequest(
            mfr_type=MFRType.SAFETY_CONCERN,
            subject="Safety concern regarding staffing levels",
            scheduler_name="SGT Smith",
        )
        assert r.priority == MFRPriority.ROUTINE
        assert r.include_system_state is True
        assert r.include_vulnerability_analysis is True
        assert r.include_recommendations is True
        assert r.scheduler_objection is None

    # --- subject (min_length=10, max_length=200) ---

    def test_subject_too_short(self):
        with pytest.raises(ValidationError):
            MFRRequest(
                mfr_type=MFRType.SAFETY_CONCERN,
                subject="Short",
                scheduler_name="SGT Smith",
            )

    def test_subject_too_long(self):
        with pytest.raises(ValidationError):
            MFRRequest(
                mfr_type=MFRType.SAFETY_CONCERN,
                subject="x" * 201,
                scheduler_name="SGT Smith",
            )

    # --- scheduler_name (min_length=2, max_length=100) ---

    def test_scheduler_name_too_short(self):
        with pytest.raises(ValidationError):
            MFRRequest(
                mfr_type=MFRType.SAFETY_CONCERN,
                subject="Safety concern regarding staffing levels",
                scheduler_name="A",
            )

    def test_scheduler_name_too_long(self):
        with pytest.raises(ValidationError):
            MFRRequest(
                mfr_type=MFRType.SAFETY_CONCERN,
                subject="Safety concern regarding staffing levels",
                scheduler_name="x" * 101,
            )


# ── RFFRequest ───────────────────────────────────────────────────────


class TestRFFRequest:
    def _make_valid(self, **kwargs):
        defaults = {
            "requesting_unit": "TAMC GME",
            "mission_affected": [MissionType.INPATIENT_MEDICINE],
            "mos_required": ["60H"],
            "personnel_count": 2,
            "duration_days": 30,
            "justification": "x" * 50,
        }
        defaults.update(kwargs)
        return RFFRequest(**defaults)

    def test_defaults(self):
        r = self._make_valid()
        assert r.uic is None

    # --- requesting_unit (min_length=2, max_length=100) ---

    def test_requesting_unit_too_short(self):
        with pytest.raises(ValidationError):
            self._make_valid(requesting_unit="A")

    def test_requesting_unit_too_long(self):
        with pytest.raises(ValidationError):
            self._make_valid(requesting_unit="x" * 101)

    # --- personnel_count (ge=1) ---

    def test_personnel_count_below_min(self):
        with pytest.raises(ValidationError):
            self._make_valid(personnel_count=0)

    # --- duration_days (ge=1, le=365) ---

    def test_duration_below_min(self):
        with pytest.raises(ValidationError):
            self._make_valid(duration_days=0)

    def test_duration_above_max(self):
        with pytest.raises(ValidationError):
            self._make_valid(duration_days=366)

    # --- justification (min_length=50, max_length=2000) ---

    def test_justification_too_short(self):
        with pytest.raises(ValidationError):
            self._make_valid(justification="Too short")

    def test_justification_too_long(self):
        with pytest.raises(ValidationError):
            self._make_valid(justification="x" * 2001)


# ── CircuitBreakerOverrideRequest ────────────────────────────────────


class TestCircuitBreakerOverrideRequest:
    def test_defaults(self):
        r = CircuitBreakerOverrideRequest(
            authority=OverrideAuthority.PROGRAM_DIRECTOR,
            reason="Critical staffing need requires override of safety checks",
            acknowledge_risks=True,
        )
        assert r.duration_hours == 8
        assert r.generate_mfr is True

    # --- reason (min_length=20, max_length=500) ---

    def test_reason_too_short(self):
        with pytest.raises(ValidationError):
            CircuitBreakerOverrideRequest(
                authority=OverrideAuthority.PROGRAM_DIRECTOR,
                reason="Too short",
                acknowledge_risks=True,
            )

    def test_reason_too_long(self):
        with pytest.raises(ValidationError):
            CircuitBreakerOverrideRequest(
                authority=OverrideAuthority.PROGRAM_DIRECTOR,
                reason="x" * 501,
                acknowledge_risks=True,
            )

    # --- duration_hours (ge=1, le=72) ---

    def test_duration_hours_below_min(self):
        with pytest.raises(ValidationError):
            CircuitBreakerOverrideRequest(
                authority=OverrideAuthority.PROGRAM_DIRECTOR,
                reason="Critical staffing need requires override",
                acknowledge_risks=True,
                duration_hours=0,
            )

    def test_duration_hours_above_max(self):
        with pytest.raises(ValidationError):
            CircuitBreakerOverrideRequest(
                authority=OverrideAuthority.PROGRAM_DIRECTOR,
                reason="Critical staffing need requires override",
                acknowledge_risks=True,
                duration_hours=73,
            )


# ── CircuitBreakerOverrideResponse ───────────────────────────────────


class TestCircuitBreakerOverrideResponse:
    def test_valid(self):
        r = CircuitBreakerOverrideResponse(
            success=True,
            override_id=uuid4(),
            expires_at=datetime(2026, 1, 16),
            mfr_generated=True,
            mfr_id=uuid4(),
            warning_message="Override active",
            risks_acknowledged=["Staffing below N-1"],
        )
        assert r.success is True


# ── SafetyStandDownRequest ───────────────────────────────────────────


class TestSafetyStandDownRequest:
    def test_defaults(self):
        r = SafetyStandDownRequest(
            reason="Multiple coverage gaps across critical rotations",
            initiator="Chief Resident",
        )
        assert r.notify_dio is True
        assert r.notify_risk_management is True
        assert r.notify_commander is False

    # --- reason (min_length=20, max_length=500) ---

    def test_reason_too_short(self):
        with pytest.raises(ValidationError):
            SafetyStandDownRequest(reason="Short", initiator="CR")

    def test_reason_too_long(self):
        with pytest.raises(ValidationError):
            SafetyStandDownRequest(reason="x" * 501, initiator="CR")


# ── MFRHistoryResponse ───────────────────────────────────────────────


class TestMFRHistoryResponse:
    def test_valid(self):
        r = MFRHistoryResponse(items=[], total=0, page=1, page_size=20)
        assert r.items == []


# ── CircuitBreakerHistoryResponse ────────────────────────────────────


class TestCircuitBreakerHistoryResponse:
    def test_valid(self):
        r = CircuitBreakerHistoryResponse(items=[], total=0, page=1, page_size=20)
        assert r.items == []


# ── IronDomeStatusResponse ───────────────────────────────────────────


class TestIronDomeStatusResponse:
    def test_valid(self):
        r = IronDomeStatusResponse(
            timestamp=datetime(2026, 1, 15),
            overall_readiness=DRRSCategory.C2,
            missions_nmc_count=1,
            risk_to_mission=RiskLevel.MODERATE,
            circuit_breaker_state=CircuitBreakerState.CLOSED,
            scheduling_locked=False,
            override_active=False,
            mfrs_generated_today=0,
            mfrs_requiring_signature=0,
            rffs_pending=0,
            active_alerts=[],
            recommended_actions=[],
        )
        assert r.scheduling_locked is False
