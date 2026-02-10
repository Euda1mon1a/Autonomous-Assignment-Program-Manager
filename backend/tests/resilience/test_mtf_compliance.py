"""Tests for MTF Compliance / Iron Dome (pure logic, no DB)."""

import pytest

from app.resilience.mtf_compliance import (
    CircuitBreaker,
    CircuitBreakerCheck,
    CircuitBreakerOverride,
    CircuitBreakerStatus,
    CoverageAnalysis,
    DRRSTranslator,
    IronDomeService,
    IronDomeStatus,
    MFRDocument,
    MFRGenerator,
    MTFComplianceResult,
    MTFViolation,
    RFFDrafter,
    RFFDocument,
    ReadinessAssessment,
    SystemStateDict,
)
from app.resilience.mtf_types import (
    CascadePrediction,
    PositiveFeedbackRisk,
    SystemHealthState,
)
from app.schemas.mtf_compliance import (
    CircuitBreakerState,
    CircuitBreakerTrigger,
    DRRSCategory,
    EquipmentReadinessLevel,
    MFRPriority,
    MFRType,
    MissionCapabilityStatus,
    MissionType,
    OverrideAuthority,
    PersonnelReadinessLevel,
    RiskLevel,
)
from app.schemas.resilience import (
    EquilibriumState,
    LoadSheddingLevel,
)


# -- Helper: standard dict-based system state ---------------------------------


def _healthy_state() -> SystemStateDict:
    return {
        "n1_pass": True,
        "n2_pass": True,
        "coverage_rate": 0.95,
        "average_allostatic_load": 30,
        "load_shedding_level": "NORMAL",
        "equilibrium_state": "stable",
        "phase_transition_risk": "low",
        "compensation_debt": 100,
        "volatility_level": "normal",
    }


def _critical_state() -> SystemStateDict:
    return {
        "n1_pass": False,
        "n2_pass": False,
        "coverage_rate": 0.60,
        "average_allostatic_load": 85,
        "load_shedding_level": "RED",
        "equilibrium_state": "critical",
        "phase_transition_risk": "critical",
        "compensation_debt": 1500,
        "volatility_level": "critical",
    }


# =============================================================================
# DRRSTranslator
# =============================================================================


class TestDRRSTranslatorLoadShedding:
    """translate_load_shedding maps LoadSheddingLevel → (DRRSCategory, str)."""

    def test_normal_maps_to_c1(self):
        t = DRRSTranslator()
        cat, explanation = t.translate_load_shedding(LoadSheddingLevel.NORMAL)
        assert cat == DRRSCategory.C1
        assert "Fully Mission Capable" in explanation

    def test_yellow_maps_to_c2(self):
        cat, _ = DRRSTranslator().translate_load_shedding(LoadSheddingLevel.YELLOW)
        assert cat == DRRSCategory.C2

    def test_orange_maps_to_c3(self):
        cat, _ = DRRSTranslator().translate_load_shedding(LoadSheddingLevel.ORANGE)
        assert cat == DRRSCategory.C3

    def test_red_maps_to_c4(self):
        cat, _ = DRRSTranslator().translate_load_shedding(LoadSheddingLevel.RED)
        assert cat == DRRSCategory.C4

    def test_black_maps_to_c4(self):
        cat, _ = DRRSTranslator().translate_load_shedding(LoadSheddingLevel.BLACK)
        assert cat == DRRSCategory.C4

    def test_critical_maps_to_c5(self):
        cat, explanation = DRRSTranslator().translate_load_shedding(
            LoadSheddingLevel.CRITICAL
        )
        assert cat == DRRSCategory.C5
        assert "Critical" in explanation


class TestDRRSTranslatorPersonnel:
    """translate_personnel_strength maps headcount → (P-rating, pct)."""

    def test_fully_manned_p1(self):
        t = DRRSTranslator()
        rating, pct = t.translate_personnel_strength(20, 20)
        assert rating == PersonnelReadinessLevel.P1
        assert pct >= 100.0

    def test_overmanned_p1(self):
        rating, pct = DRRSTranslator().translate_personnel_strength(25, 20)
        assert rating == PersonnelReadinessLevel.P1
        assert pct > 100.0

    def test_minor_shortage_p2(self):
        rating, pct = DRRSTranslator().translate_personnel_strength(19, 20)
        assert rating == PersonnelReadinessLevel.P2
        assert 90 <= pct < 100

    def test_significant_shortage_p3(self):
        rating, pct = DRRSTranslator().translate_personnel_strength(17, 20)
        assert rating == PersonnelReadinessLevel.P3
        assert 80 <= pct < 90

    def test_critical_shortage_p4(self):
        rating, pct = DRRSTranslator().translate_personnel_strength(14, 20)
        assert rating == PersonnelReadinessLevel.P4
        assert pct < 80

    def test_zero_required_returns_p4(self):
        rating, pct = DRRSTranslator().translate_personnel_strength(10, 0)
        assert rating == PersonnelReadinessLevel.P4
        assert pct == 0.0

    def test_overloaded_degrades_rating(self):
        # 18 available, 20 required → 90% → P2 normally
        # But 4 overloaded → effective = 18 - (4*0.5) = 16 → 80% → P3
        rating, pct = DRRSTranslator().translate_personnel_strength(18, 20, 4)
        assert rating == PersonnelReadinessLevel.P3
        assert pct == pytest.approx(80.0)


class TestDRRSTranslatorCapability:
    """translate_capability maps contingency → (S-rating, deficiencies)."""

    def test_all_pass_s1(self):
        rating, defs = DRRSTranslator().translate_capability(True, True, 0.95)
        assert rating == EquipmentReadinessLevel.S1
        assert defs == []

    def test_n2_fail_only_s2(self):
        # n1 passes, n2 fails, coverage ok → 1 deficiency + n1 pass → S2
        rating, defs = DRRSTranslator().translate_capability(True, False, 0.95)
        assert rating == EquipmentReadinessLevel.S2
        assert len(defs) == 1

    def test_multiple_deficiencies_n1_pass_s3(self):
        # n1 pass, n2 fail, coverage degraded → 2 deficiencies + n1 pass → S3
        rating, defs = DRRSTranslator().translate_capability(True, False, 0.85)
        assert rating == EquipmentReadinessLevel.S3
        assert len(defs) == 2

    def test_n1_fail_s4(self):
        rating, defs = DRRSTranslator().translate_capability(False, False, 0.80)
        assert rating == EquipmentReadinessLevel.S4
        assert any("Single Point of Failure" in d for d in defs)

    def test_coverage_degraded_appears_in_deficiencies(self):
        _, defs = DRRSTranslator().translate_capability(True, True, 0.85)
        assert len(defs) == 1
        assert "Coverage degraded" in defs[0]


class TestDRRSTranslatorSitrep:
    """generate_sitrep_summary produces SITREP text."""

    def test_c1_green(self):
        summary = DRRSTranslator().generate_sitrep_summary(
            DRRSCategory.C1,
            PersonnelReadinessLevel.P1,
            EquipmentReadinessLevel.S1,
            LoadSheddingLevel.NORMAL,
            [],
        )
        assert "GREEN" in summary
        assert "Mission Capable" in summary

    def test_c3_yellow(self):
        summary = DRRSTranslator().generate_sitrep_summary(
            DRRSCategory.C3,
            PersonnelReadinessLevel.P3,
            EquipmentReadinessLevel.S3,
            LoadSheddingLevel.ORANGE,
            ["Test deficiency"],
        )
        assert "YELLOW" in summary
        assert "Marginally Mission Capable" in summary
        assert "Test deficiency" in summary

    def test_c4_red(self):
        summary = DRRSTranslator().generate_sitrep_summary(
            DRRSCategory.C4,
            PersonnelReadinessLevel.P4,
            EquipmentReadinessLevel.S4,
            LoadSheddingLevel.RED,
            ["Critical"],
        )
        assert "RED" in summary
        assert "Non-Mission Capable" in summary

    def test_c5_black(self):
        summary = DRRSTranslator().generate_sitrep_summary(
            DRRSCategory.C5,
            PersonnelReadinessLevel.P4,
            EquipmentReadinessLevel.S4,
            LoadSheddingLevel.CRITICAL,
            ["Severe"],
        )
        assert "BLACK" in summary

    def test_c2_with_watch_items(self):
        summary = DRRSTranslator().generate_sitrep_summary(
            DRRSCategory.C2,
            PersonnelReadinessLevel.P2,
            EquipmentReadinessLevel.S2,
            LoadSheddingLevel.YELLOW,
            ["Minor issue"],
        )
        assert "AMBER" in summary
        assert "WATCH ITEMS" in summary
        assert "Minor issue" in summary


# =============================================================================
# MFRGenerator
# =============================================================================


class TestMFRGeneratorRiskLevel:
    """_assess_risk_level uses weighted scoring."""

    def test_healthy_state_low(self):
        gen = MFRGenerator()
        assert gen._assess_risk_level(_healthy_state()) == RiskLevel.LOW

    def test_n1_fail_moderate(self):
        state = _healthy_state()
        state["n1_pass"] = False
        # n1 fail = +3 → MODERATE (2-3)
        assert MFRGenerator()._assess_risk_level(state) == RiskLevel.MODERATE

    def test_n1_n2_fail_high(self):
        state = _healthy_state()
        state["n1_pass"] = False
        state["n2_pass"] = False
        # +3 + +2 = 5 → HIGH (4-6)
        assert MFRGenerator()._assess_risk_level(state) == RiskLevel.HIGH

    def test_critical_coverage_high(self):
        state = _healthy_state()
        state["coverage_rate"] = 0.65
        # coverage <70 = +4 → HIGH
        assert MFRGenerator()._assess_risk_level(state) == RiskLevel.HIGH

    def test_severe_coverage_moderate(self):
        state = _healthy_state()
        state["coverage_rate"] = 0.75
        # coverage 70-80 = +3 → MODERATE
        assert MFRGenerator()._assess_risk_level(state) == RiskLevel.MODERATE

    def test_allostatic_overload_moderate(self):
        state = _healthy_state()
        state["average_allostatic_load"] = 85
        # allostatic >80 = +3 → MODERATE
        assert MFRGenerator()._assess_risk_level(state) == RiskLevel.MODERATE

    def test_critical_equilibrium_high(self):
        state = _healthy_state()
        state["equilibrium_state"] = "critical"
        # equilibrium critical = +4 → HIGH
        assert MFRGenerator()._assess_risk_level(state) == RiskLevel.HIGH

    def test_catastrophic_combined(self):
        # Everything bad: n1(+3) + n2(+2) + coverage<70(+4) + allostatic>80(+3) + critical(+4) = 16
        assert (
            MFRGenerator()._assess_risk_level(_critical_state())
            == RiskLevel.CATASTROPHIC
        )

    def test_critical_combined(self):
        state = _healthy_state()
        state["n1_pass"] = False  # +3
        state["coverage_rate"] = 0.75  # +3
        state["average_allostatic_load"] = 65  # +2
        # Total: 8 → CRITICAL (7-9)
        assert MFRGenerator()._assess_risk_level(state) == RiskLevel.CRITICAL


class TestMFRGeneratorExtractFindings:
    """_extract_findings checks 7 conditions + additional."""

    def test_healthy_no_findings(self):
        findings = MFRGenerator()._extract_findings(_healthy_state(), None)
        assert findings == []

    def test_n1_fail_finding(self):
        state = _healthy_state()
        state["n1_pass"] = False
        findings = MFRGenerator()._extract_findings(state, None)
        assert any("N-1" in f for f in findings)

    def test_n2_fail_finding(self):
        state = _healthy_state()
        state["n2_pass"] = False
        findings = MFRGenerator()._extract_findings(state, None)
        assert any("N-2" in f for f in findings)

    def test_load_shedding_active_finding(self):
        state = _healthy_state()
        state["load_shedding_level"] = "RED"
        findings = MFRGenerator()._extract_findings(state, None)
        assert any("LOAD SHEDDING" in f for f in findings)

    def test_coverage_degraded_finding(self):
        state = _healthy_state()
        state["coverage_rate"] = 0.85
        findings = MFRGenerator()._extract_findings(state, None)
        assert any("COVERAGE" in f for f in findings)

    def test_allostatic_overload_finding(self):
        state = _healthy_state()
        state["average_allostatic_load"] = 75
        findings = MFRGenerator()._extract_findings(state, None)
        assert any("OVERLOAD" in f for f in findings)

    def test_unsustainable_equilibrium_finding(self):
        state = _healthy_state()
        state["equilibrium_state"] = "unsustainable"
        findings = MFRGenerator()._extract_findings(state, None)
        assert any("UNSUSTAINABLE" in f for f in findings)

    def test_phase_transition_risk_finding(self):
        state = _healthy_state()
        state["phase_transition_risk"] = "critical"
        findings = MFRGenerator()._extract_findings(state, None)
        assert any("PHASE TRANSITION" in f for f in findings)

    def test_additional_findings_appended(self):
        findings = MFRGenerator()._extract_findings(_healthy_state(), ["EXTRA FINDING"])
        assert "EXTRA FINDING" in findings

    def test_critical_state_multiple_findings(self):
        findings = MFRGenerator()._extract_findings(_critical_state(), None)
        assert len(findings) >= 5


class TestMFRGeneratorGenerateMFR:
    """generate_mfr produces MFRDocument."""

    def test_returns_mfr_document(self):
        mfr = MFRGenerator().generate_mfr(
            mfr_type=MFRType.RISK_ACCEPTANCE,
            subject="Test Subject",
            system_state=_healthy_state(),
            scheduler_name="Test Scheduler",
        )
        assert isinstance(mfr, MFRDocument)

    def test_has_sha256_hash(self):
        mfr = MFRGenerator().generate_mfr(
            mfr_type=MFRType.RISK_ACCEPTANCE,
            subject="Hash Test",
            system_state=_healthy_state(),
            scheduler_name="Tester",
        )
        assert len(mfr.document_hash) == 64  # SHA-256 hex digest

    def test_risk_acceptance_requires_signature(self):
        mfr = MFRGenerator().generate_mfr(
            mfr_type=MFRType.RISK_ACCEPTANCE,
            subject="Sig Test",
            system_state=_healthy_state(),
            scheduler_name="Tester",
        )
        assert mfr.requires_commander_signature is True

    def test_resource_request_no_signature(self):
        mfr = MFRGenerator().generate_mfr(
            mfr_type=MFRType.RESOURCE_REQUEST,
            subject="Resource Test",
            system_state=_healthy_state(),
            scheduler_name="Tester",
        )
        assert mfr.requires_commander_signature is False

    def test_distribution_list_populated(self):
        mfr = MFRGenerator().generate_mfr(
            mfr_type=MFRType.SAFETY_CONCERN,
            subject="Distribution Test",
            system_state=_healthy_state(),
            scheduler_name="Tester",
        )
        assert len(mfr.distribution_list) > 0
        assert "Commander" in mfr.distribution_list

    def test_header_contains_subject(self):
        mfr = MFRGenerator().generate_mfr(
            mfr_type=MFRType.COMPLIANCE_VIOLATION,
            subject="ACGME Work Hour Violation",
            system_state=_healthy_state(),
            scheduler_name="Tester",
        )
        assert "ACGME Work Hour Violation" in mfr.header

    def test_priority_in_header(self):
        mfr = MFRGenerator().generate_mfr(
            mfr_type=MFRType.STAND_DOWN,
            subject="Priority Test",
            system_state=_healthy_state(),
            scheduler_name="Tester",
            priority=MFRPriority.IMMEDIATE,
        )
        assert "IMMEDIATE" in mfr.header

    def test_scheduler_objection_in_body(self):
        mfr = MFRGenerator().generate_mfr(
            mfr_type=MFRType.RISK_ACCEPTANCE,
            subject="Objection Test",
            system_state=_healthy_state(),
            scheduler_name="Maj Smith",
            scheduler_objection="This is unsafe",
        )
        assert "This is unsafe" in mfr.body
        assert "Maj Smith" in mfr.body

    def test_system_state_snapshot_stored(self):
        state = _healthy_state()
        mfr = MFRGenerator().generate_mfr(
            mfr_type=MFRType.RISK_ACCEPTANCE,
            subject="Snapshot Test",
            system_state=state,
            scheduler_name="Tester",
        )
        assert mfr.system_state_snapshot["n1_pass"] is True

    def test_critical_state_produces_catastrophic_risk(self):
        mfr = MFRGenerator().generate_mfr(
            mfr_type=MFRType.RISK_ACCEPTANCE,
            subject="Critical Test",
            system_state=_critical_state(),
            scheduler_name="Tester",
        )
        assert mfr.risk_level == RiskLevel.CATASTROPHIC
        assert "CATASTROPHIC" in mfr.risk_assessment


# =============================================================================
# CircuitBreaker (MTF)
# =============================================================================


class TestMTFCircuitBreakerInit:
    """Initial state and constants."""

    def test_initial_state_closed(self):
        cb = CircuitBreaker()
        assert cb.state == CircuitBreakerState.CLOSED

    def test_trip_count_zero(self):
        cb = CircuitBreaker()
        assert cb.trip_count == 0

    def test_locked_operations_defined(self):
        assert CircuitBreakerState.OPEN in CircuitBreaker.LOCKED_OPERATIONS
        assert len(CircuitBreaker.LOCKED_OPERATIONS[CircuitBreakerState.OPEN]) > 0

    def test_always_allowed_includes_emergency(self):
        assert "emergency_coverage" in CircuitBreaker.ALWAYS_ALLOWED


class TestMTFCircuitBreakerCheckAndTrip:
    """check_and_trip implements 7-priority cascade."""

    def _safe_args(self):
        return {
            "n1_pass": True,
            "n2_pass": True,
            "coverage_rate": 0.95,
            "average_allostatic_load": 30,
            "volatility_level": "normal",
            "compensation_debt": 100,
        }

    def test_no_trip_when_healthy(self):
        cb = CircuitBreaker()
        tripped, trigger, details = cb.check_and_trip(**self._safe_args())
        assert tripped is False
        assert trigger is None

    def test_priority1_n1_failure(self):
        cb = CircuitBreaker()
        args = self._safe_args()
        args["n1_pass"] = False
        tripped, trigger, _ = cb.check_and_trip(**args)
        assert tripped is True
        assert trigger == CircuitBreakerTrigger.N1_VIOLATION
        assert cb.state == CircuitBreakerState.OPEN

    def test_priority2_n2_with_degraded_coverage(self):
        cb = CircuitBreaker()
        args = self._safe_args()
        args["n2_pass"] = False
        args["coverage_rate"] = 0.80  # below 0.85 warning
        tripped, trigger, _ = cb.check_and_trip(**args)
        assert tripped is True
        assert trigger == CircuitBreakerTrigger.N2_VIOLATION

    def test_n2_alone_does_not_trip(self):
        cb = CircuitBreaker()
        args = self._safe_args()
        args["n2_pass"] = False
        # coverage still healthy → no trip for n2 alone
        tripped, _, _ = cb.check_and_trip(**args)
        assert tripped is False

    def test_priority3_coverage_collapse(self):
        cb = CircuitBreaker()
        args = self._safe_args()
        args["coverage_rate"] = 0.65
        tripped, trigger, _ = cb.check_and_trip(**args)
        assert tripped is True
        assert trigger == CircuitBreakerTrigger.COVERAGE_COLLAPSE

    def test_priority4_allostatic_overload(self):
        cb = CircuitBreaker()
        args = self._safe_args()
        args["average_allostatic_load"] = 85
        tripped, trigger, _ = cb.check_and_trip(**args)
        assert tripped is True
        assert trigger == CircuitBreakerTrigger.ALLOSTATIC_OVERLOAD

    def test_priority5_volatility_critical(self):
        cb = CircuitBreaker()
        args = self._safe_args()
        args["volatility_level"] = "critical"
        tripped, trigger, _ = cb.check_and_trip(**args)
        assert tripped is True
        assert trigger == CircuitBreakerTrigger.VOLATILITY_CRITICAL

    def test_priority6_compensation_debt(self):
        cb = CircuitBreaker()
        args = self._safe_args()
        args["compensation_debt"] = 1500
        tripped, trigger, _ = cb.check_and_trip(**args)
        assert tripped is True
        assert trigger == CircuitBreakerTrigger.COMPENSATION_DEBT_EXCEEDED

    def test_priority7_positive_feedback(self):
        cb = CircuitBreaker()
        args = self._safe_args()
        args["positive_feedback_risks"] = [
            PositiveFeedbackRisk(
                risk_type="burnout_cascade",
                confidence=0.9,
                description="Detected",
            )
        ]
        tripped, trigger, _ = cb.check_and_trip(**args)
        assert tripped is True
        assert trigger == CircuitBreakerTrigger.POSITIVE_FEEDBACK_CASCADE

    def test_positive_feedback_low_confidence_no_trip(self):
        cb = CircuitBreaker()
        args = self._safe_args()
        args["positive_feedback_risks"] = [
            PositiveFeedbackRisk(risk_type="minor", confidence=0.5, description="Low")
        ]
        tripped, _, _ = cb.check_and_trip(**args)
        assert tripped is False

    def test_positive_feedback_dict_form(self):
        cb = CircuitBreaker()
        args = self._safe_args()
        args["positive_feedback_risks"] = [{"confidence": 0.9}]
        tripped, trigger, _ = cb.check_and_trip(**args)
        assert tripped is True
        assert trigger == CircuitBreakerTrigger.POSITIVE_FEEDBACK_CASCADE

    def test_already_open_returns_early(self):
        cb = CircuitBreaker()
        # Trip it first
        args = self._safe_args()
        args["n1_pass"] = False
        cb.check_and_trip(**args)
        assert cb.state == CircuitBreakerState.OPEN

        # Second check returns False (already tripped)
        tripped, trigger, _ = cb.check_and_trip(**args)
        assert tripped is False
        assert trigger == CircuitBreakerTrigger.N1_VIOLATION  # remembers original

    def test_trip_increments_count(self):
        cb = CircuitBreaker()
        args = self._safe_args()
        args["n1_pass"] = False
        cb.check_and_trip(**args)
        assert cb.trip_count == 1

    def test_half_open_auto_closes_when_safe(self):
        cb = CircuitBreaker()
        cb.half_open()
        assert cb.state == CircuitBreakerState.HALF_OPEN

        # check_and_trip with safe conditions → auto-close
        tripped, _, _ = cb.check_and_trip(**self._safe_args())
        assert tripped is False
        assert cb.state == CircuitBreakerState.CLOSED


class TestMTFCircuitBreakerOperations:
    """is_operation_allowed, override, close, half_open."""

    def test_always_allowed_emergency(self):
        cb = CircuitBreaker()
        cb._trip(CircuitBreakerTrigger.N1_VIOLATION, "test")
        allowed, reason = cb.is_operation_allowed("emergency_coverage")
        assert allowed is True
        assert reason is None

    def test_locked_when_open(self):
        cb = CircuitBreaker()
        cb._trip(CircuitBreakerTrigger.N1_VIOLATION, "test")
        allowed, reason = cb.is_operation_allowed("new_assignments")
        assert allowed is False
        assert "HTTP 451" in reason

    def test_locked_when_half_open(self):
        cb = CircuitBreaker()
        cb.half_open()
        allowed, reason = cb.is_operation_allowed("leave_approval")
        assert allowed is False

    def test_allowed_when_closed(self):
        cb = CircuitBreaker()
        allowed, _ = cb.is_operation_allowed("new_assignments")
        assert allowed is True

    def test_override_allows_locked_ops(self):
        cb = CircuitBreaker()
        cb._trip(CircuitBreakerTrigger.N1_VIOLATION, "test")
        cb.override_breaker(
            OverrideAuthority.COMMANDER,
            "Commander override for urgent needs",
            duration_hours=4,
        )
        allowed, _ = cb.is_operation_allowed("new_assignments")
        assert allowed is True

    def test_override_returns_record(self):
        cb = CircuitBreaker()
        cb._trip(CircuitBreakerTrigger.N1_VIOLATION, "test")
        override = cb.override_breaker(
            OverrideAuthority.PROGRAM_DIRECTOR,
            "PD override",
            duration_hours=2,
        )
        assert isinstance(override, CircuitBreakerOverride)
        assert override.authority == OverrideAuthority.PROGRAM_DIRECTOR

    def test_close_resets_state(self):
        cb = CircuitBreaker()
        cb._trip(CircuitBreakerTrigger.N1_VIOLATION, "test")
        cb.close()
        assert cb.state == CircuitBreakerState.CLOSED
        assert cb.trigger is None
        assert cb.override is None

    def test_half_open_sets_state(self):
        cb = CircuitBreaker()
        cb.half_open()
        assert cb.state == CircuitBreakerState.HALF_OPEN


class TestMTFCircuitBreakerStatus:
    """get_status returns CircuitBreakerStatus."""

    def test_closed_status(self):
        status = CircuitBreaker().get_status()
        assert isinstance(status, CircuitBreakerStatus)
        assert status.state == CircuitBreakerState.CLOSED
        assert status.locked_operations == []

    def test_open_status_has_locked_ops(self):
        cb = CircuitBreaker()
        cb._trip(CircuitBreakerTrigger.COVERAGE_COLLAPSE, "test")
        status = cb.get_status()
        assert status.state == CircuitBreakerState.OPEN
        assert "new_assignments" in status.locked_operations
        assert status.trigger == CircuitBreakerTrigger.COVERAGE_COLLAPSE

    def test_status_includes_allowed_ops(self):
        status = CircuitBreaker().get_status()
        assert "emergency_coverage" in status.allowed_operations


# =============================================================================
# RFFDrafter
# =============================================================================


class TestRFFDrafter:
    """draft_rff produces RFFDocument."""

    def _draft_basic(self):
        return RFFDrafter().draft_rff(
            requesting_unit="Department of Family Medicine",
            mission_affected=[MissionType.OUTPATIENT_PRIMARY],
            mos_required=["60H"],
            personnel_count=2,
            duration_days=90,
            justification="Prevent cascade failure",
            system_state=_healthy_state(),
        )

    def test_returns_rff_document(self):
        rff = self._draft_basic()
        assert isinstance(rff, RFFDocument)

    def test_has_sha256_hash(self):
        rff = self._draft_basic()
        assert len(rff.document_hash) == 64

    def test_header_contains_unit(self):
        rff = self._draft_basic()
        assert "Department of Family Medicine" in rff.header

    def test_header_contains_rff(self):
        rff = self._draft_basic()
        assert "REQUEST FOR FORCES" in rff.header

    def test_header_with_uic(self):
        rff = RFFDrafter().draft_rff(
            requesting_unit="Test Unit",
            mission_affected=[MissionType.EMERGENCY_DEPARTMENT],
            mos_required=["60H"],
            personnel_count=1,
            duration_days=30,
            justification="Test",
            system_state=_healthy_state(),
            uic="W12345",
        )
        assert "W12345" in rff.header

    def test_situation_paragraph(self):
        rff = self._draft_basic()
        assert "SITUATION" in rff.situation

    def test_execution_has_mos(self):
        rff = self._draft_basic()
        assert "60H" in rff.execution

    def test_sustainment_has_duration(self):
        rff = self._draft_basic()
        assert "90 days" in rff.sustainment

    def test_command_paragraph(self):
        rff = self._draft_basic()
        assert "COMMAND AND SIGNAL" in rff.command_and_signal

    def test_supporting_metrics_populated(self):
        rff = self._draft_basic()
        assert rff.supporting_metrics.coverage_rate is not None

    def test_cascade_prediction_in_situation(self):
        rff = RFFDrafter().draft_rff(
            requesting_unit="Test",
            mission_affected=[MissionType.INPATIENT_MEDICINE],
            mos_required=["60H"],
            personnel_count=3,
            duration_days=60,
            justification="Cascade risk",
            system_state=_critical_state(),
            cascade_prediction=CascadePrediction(days_until_exhaustion=10),
        )
        assert "10 days" in rff.situation

    def test_projection_without_support_cascade(self):
        rff = RFFDrafter().draft_rff(
            requesting_unit="Test",
            mission_affected=[MissionType.SURGICAL_SERVICES],
            mos_required=["60H"],
            personnel_count=2,
            duration_days=90,
            justification="Test",
            system_state=_critical_state(),
            cascade_prediction=CascadePrediction(days_until_exhaustion=14),
        )
        assert rff.projected_without_support.mission_failure_likely is True
        assert len(rff.projected_without_support.outcomes) > 0


# =============================================================================
# IronDomeService
# =============================================================================


class TestIronDomeService:
    """Integration tests for the unified IronDomeService."""

    def test_init(self):
        svc = IronDomeService()
        assert isinstance(svc.translator, DRRSTranslator)
        assert isinstance(svc.mfr_generator, MFRGenerator)
        assert isinstance(svc.circuit_breaker, CircuitBreaker)
        assert isinstance(svc.rff_drafter, RFFDrafter)

    def test_assess_readiness_healthy(self):
        svc = IronDomeService()
        assessment = svc.assess_readiness(
            load_shedding_level=LoadSheddingLevel.NORMAL,
            equilibrium_state=EquilibriumState.STABLE,
            n1_pass=True,
            n2_pass=True,
            coverage_rate=0.95,
            available_faculty=20,
            required_faculty=20,
        )
        assert isinstance(assessment, ReadinessAssessment)
        assert assessment.overall_rating == DRRSCategory.C1.value
        assert assessment.overall_capability == MissionCapabilityStatus.FMC.value

    def test_assess_readiness_degraded(self):
        svc = IronDomeService()
        assessment = svc.assess_readiness(
            load_shedding_level=LoadSheddingLevel.ORANGE,
            equilibrium_state=EquilibriumState.STRESSED,
            n1_pass=False,
            n2_pass=False,
            coverage_rate=0.80,
            available_faculty=16,
            required_faculty=20,
            overloaded_faculty_count=4,
        )
        assert assessment.overall_rating == DRRSCategory.C3.value
        assert assessment.overall_capability == MissionCapabilityStatus.PMC.value

    def test_assess_readiness_c4_nmc(self):
        svc = IronDomeService()
        assessment = svc.assess_readiness(
            load_shedding_level=LoadSheddingLevel.RED,
            equilibrium_state=EquilibriumState.UNSUSTAINABLE,
            n1_pass=False,
            n2_pass=False,
            coverage_rate=0.60,
            available_faculty=10,
            required_faculty=20,
        )
        assert assessment.overall_rating == DRRSCategory.C4.value
        assert assessment.overall_capability == MissionCapabilityStatus.NMC.value

    def test_check_circuit_breaker_trips(self):
        svc = IronDomeService()
        check = svc.check_circuit_breaker(
            n1_pass=False,
            n2_pass=False,
            coverage_rate=0.60,
            average_allostatic_load=85,
            volatility_level="critical",
            compensation_debt=1500,
        )
        assert isinstance(check, CircuitBreakerCheck)
        assert check.tripped is True
        assert check.state == CircuitBreakerState.OPEN.value

    def test_check_circuit_breaker_no_trip(self):
        svc = IronDomeService()
        check = svc.check_circuit_breaker(
            n1_pass=True,
            n2_pass=True,
            coverage_rate=0.95,
            average_allostatic_load=30,
            volatility_level="normal",
            compensation_debt=100,
        )
        assert check.tripped is False
        assert check.state == CircuitBreakerState.CLOSED.value

    def test_generate_risk_mfr(self):
        svc = IronDomeService()
        mfr = svc.generate_risk_mfr(
            subject="Critical Staffing Shortage",
            system_state=_critical_state(),
            scheduler_name="Maj Smith",
        )
        assert isinstance(mfr, MFRDocument)
        assert mfr.mfr_type == MFRType.RISK_ACCEPTANCE
        assert len(svc.mfr_history) == 1

    def test_get_status_default(self):
        svc = IronDomeService()
        status = svc.get_status()
        assert isinstance(status, IronDomeStatus)
        assert status.circuit_breaker_state == CircuitBreakerState.CLOSED.value
        assert status.scheduling_locked is False
        assert status.mfrs_generated == 0
        assert status.rffs_generated == 0

    def test_get_status_after_trip(self):
        svc = IronDomeService()
        svc.check_circuit_breaker(
            n1_pass=False,
            n2_pass=False,
            coverage_rate=0.60,
            average_allostatic_load=85,
            volatility_level="critical",
            compensation_debt=1500,
        )
        status = svc.get_status()
        assert status.circuit_breaker_state == CircuitBreakerState.OPEN.value
        assert status.scheduling_locked is True

    def test_draft_resource_request(self):
        svc = IronDomeService()
        rff = svc.draft_resource_request(
            requesting_unit="Family Medicine",
            mission_affected=[
                MissionType.OUTPATIENT_PRIMARY,
                MissionType.GRADUATE_MEDICAL_EDUCATION,
            ],
            mos_required=["60H", "66H"],
            personnel_count=3,
            duration_days=90,
            justification="Cascade failure prevention",
            system_state=_critical_state(),
        )
        assert isinstance(rff, RFFDocument)
        assert len(svc.rff_history) == 1


# =============================================================================
# Data classes
# =============================================================================


class TestDataClasses:
    """Test dataclass construction and to_dict methods."""

    def test_mtf_violation(self):
        v = MTFViolation(
            rule_id="ACGME_80HR",
            severity="critical",
            description="Work hour limit exceeded",
        )
        assert v.rule_id == "ACGME_80HR"
        assert v.affected_items == []

    def test_mtf_compliance_result(self):
        r = MTFComplianceResult(is_compliant=True, score=98.5)
        assert r.violations == []
        assert r.recommendations == []

    def test_coverage_analysis(self):
        c = CoverageAnalysis(total_slots=100, filled_slots=92, coverage_percentage=92.0)
        assert c.gaps == []

    def test_readiness_assessment_to_dict(self):
        ra = ReadinessAssessment(
            overall_rating="C-1",
            overall_capability="FMC",
            personnel_rating="P-1",
            personnel_percentage=100.0,
            capability_rating="S-1",
            deficiencies=[],
            load_shedding_level="NORMAL",
            equilibrium_state="stable",
            executive_summary="All good",
        )
        d = ra.to_dict()
        assert d["overall_rating"] == "C-1"
        assert d["personnel_percentage"] == 100.0

    def test_circuit_breaker_check_to_dict(self):
        cbc = CircuitBreakerCheck(
            tripped=True,
            state="open",
            trigger="n1_violation",
            trigger_details="Test",
            locked_operations=["new_assignments"],
            allowed_operations=["emergency_coverage"],
            override_active=False,
        )
        d = cbc.to_dict()
        assert d["tripped"] is True
        assert d["state"] == "open"

    def test_iron_dome_status_to_dict(self):
        ids = IronDomeStatus(
            circuit_breaker_state="closed",
            scheduling_locked=False,
            override_active=False,
            trigger=None,
            mfrs_generated=0,
            rffs_generated=0,
            locked_operations=[],
        )
        d = ids.to_dict()
        assert d["scheduling_locked"] is False
        assert d["locked_operations"] == []
