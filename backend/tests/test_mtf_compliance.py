"""
Tests for MTF Compliance module ("The Iron Dome").

Tests cover:
1. DRRS Translation (military readiness language)
2. MFR Generator (liability documentation)
3. Circuit Breaker (safety stand-down)
4. RFF Drafter (request for forces)
5. Iron Dome Service (unified interface)
"""

from datetime import datetime, timedelta
from uuid import uuid4

from app.resilience.mtf_compliance import (
    CircuitBreaker,
    DRRSTranslator,
    IronDomeService,
    MFRGenerator,
    RFFDrafter,
)
from app.schemas.mtf_compliance import (
    CircuitBreakerState,
    CircuitBreakerTrigger,
    DRRSCategory,
    EquipmentReadinessLevel,
    MFRPriority,
    MFRType,
    MissionType,
    OverrideAuthority,
    PersonnelReadinessLevel,
    RiskLevel,
)
from app.schemas.resilience import (
    EquilibriumState,
    LoadSheddingLevel,
)

# =============================================================================
# DRRS Translator Tests
# =============================================================================


class TestDRRSTranslator:
    """Tests for DRRS (Defense Readiness Reporting System) translation."""

    def test_load_shedding_to_drrs_normal(self):
        """Test NORMAL load shedding translates to C-1."""
        translator = DRRSTranslator()
        rating, explanation = translator.translate_load_shedding(
            LoadSheddingLevel.NORMAL
        )

        assert rating == DRRSCategory.C1
        assert "Fully Mission Capable" in explanation

    def test_load_shedding_to_drrs_yellow(self):
        """Test YELLOW load shedding translates to C-2."""
        translator = DRRSTranslator()
        rating, _ = translator.translate_load_shedding(LoadSheddingLevel.YELLOW)

        assert rating == DRRSCategory.C2

    def test_load_shedding_to_drrs_red(self):
        """Test RED load shedding translates to C-4 (NMC)."""
        translator = DRRSTranslator()
        rating, explanation = translator.translate_load_shedding(LoadSheddingLevel.RED)

        assert rating == DRRSCategory.C4
        assert "Not Mission Capable" in explanation

    def test_load_shedding_to_drrs_critical(self):
        """Test CRITICAL load shedding translates to C-5."""
        translator = DRRSTranslator()
        rating, _ = translator.translate_load_shedding(LoadSheddingLevel.CRITICAL)

        assert rating == DRRSCategory.C5

    def test_personnel_strength_full(self):
        """Test full personnel strength returns P-1."""
        translator = DRRSTranslator()
        rating, pct = translator.translate_personnel_strength(
            available_faculty=10,
            required_faculty=10,
            overloaded_count=0,
        )

        assert rating == PersonnelReadinessLevel.P1
        assert pct == 100.0

    def test_personnel_strength_degraded(self):
        """Test degraded personnel strength returns P-3."""
        translator = DRRSTranslator()
        rating, pct = translator.translate_personnel_strength(
            available_faculty=8,
            required_faculty=10,
            overloaded_count=0,
        )

        assert rating == PersonnelReadinessLevel.P3
        assert pct == 80.0

    def test_personnel_strength_with_overloaded(self):
        """Test overloaded faculty reduces effective strength."""
        translator = DRRSTranslator()

        # 10 available, 10 required, but 4 overloaded
        # Effective = 10 - (4 * 0.5) = 8 -> 80% -> P-3
        rating, pct = translator.translate_personnel_strength(
            available_faculty=10,
            required_faculty=10,
            overloaded_count=4,
        )

        assert rating == PersonnelReadinessLevel.P3
        assert pct == 80.0

    def test_personnel_strength_critical(self):
        """Test critical personnel shortage returns P-4."""
        translator = DRRSTranslator()
        rating, pct = translator.translate_personnel_strength(
            available_faculty=7,
            required_faculty=10,
            overloaded_count=0,
        )

        assert rating == PersonnelReadinessLevel.P4
        assert pct < 80.0

    def test_capability_full(self):
        """Test full capability returns S-1."""
        translator = DRRSTranslator()
        rating, deficiencies = translator.translate_capability(
            n1_pass=True,
            n2_pass=True,
            coverage_rate=0.95,
        )

        assert rating == EquipmentReadinessLevel.S1
        assert len(deficiencies) == 0

    def test_capability_n1_failure(self):
        """Test N-1 failure returns S-4 with deficiency."""
        translator = DRRSTranslator()
        rating, deficiencies = translator.translate_capability(
            n1_pass=False,
            n2_pass=False,
            coverage_rate=0.95,
        )

        assert rating == EquipmentReadinessLevel.S4
        assert any("Single Point of Failure" in d for d in deficiencies)

    def test_capability_low_coverage(self):
        """Test low coverage adds deficiency."""
        translator = DRRSTranslator()
        rating, deficiencies = translator.translate_capability(
            n1_pass=True,
            n2_pass=True,
            coverage_rate=0.85,
        )

        assert rating == EquipmentReadinessLevel.S2
        assert any("Coverage degraded" in d for d in deficiencies)

    def test_sitrep_summary_green(self):
        """Test SITREP summary for healthy system."""
        translator = DRRSTranslator()
        summary = translator.generate_sitrep_summary(
            drrs_rating=DRRSCategory.C1,
            p_rating=PersonnelReadinessLevel.P1,
            s_rating=EquipmentReadinessLevel.S1,
            load_shedding_level=LoadSheddingLevel.NORMAL,
            deficiencies=[],
        )

        assert "GREEN" in summary
        assert "C-1" in summary
        assert "Mission Capable" in summary

    def test_sitrep_summary_red(self):
        """Test SITREP summary for degraded system."""
        translator = DRRSTranslator()
        summary = translator.generate_sitrep_summary(
            drrs_rating=DRRSCategory.C4,
            p_rating=PersonnelReadinessLevel.P4,
            s_rating=EquipmentReadinessLevel.S4,
            load_shedding_level=LoadSheddingLevel.RED,
            deficiencies=["Single Point of Failure exists"],
        )

        assert "RED" in summary
        assert "C-4" in summary
        assert "Non-Mission Capable" in summary
        assert "Cross-Leveling" in summary


# =============================================================================
# MFR Generator Tests
# =============================================================================


class TestMFRGenerator:
    """Tests for Memorandum for Record generation."""

    def test_generate_risk_acceptance_mfr(self):
        """Test generating a risk acceptance MFR."""
        generator = MFRGenerator()

        system_state = {
            "n1_pass": False,
            "n2_pass": False,
            "coverage_rate": 0.75,
            "load_shedding_level": "RED",
            "average_allostatic_load": 70,
            "equilibrium_state": "stressed",
        }

        mfr = generator.generate_mfr(
            mfr_type=MFRType.RISK_ACCEPTANCE,
            subject="Schedule Publication Under Degraded Conditions",
            system_state=system_state,
            scheduler_name="SGT Smith",
            scheduler_objection="I advised against this schedule due to staffing gaps",
            priority=MFRPriority.PRIORITY,
        )

        assert mfr.mfr_type == MFRType.RISK_ACCEPTANCE
        assert "Risk Acceptance" in mfr.header
        assert mfr.scheduler_objection is None or "SGT Smith" in mfr.body
        assert len(mfr.findings) > 0
        assert mfr.document_hash is not None
        assert mfr.requires_commander_signature is True

    def test_mfr_extracts_n1_finding(self):
        """Test MFR extracts N-1 vulnerability finding."""
        generator = MFRGenerator()

        system_state = {
            "n1_pass": False,
            "coverage_rate": 0.95,
        }

        mfr = generator.generate_mfr(
            mfr_type=MFRType.SAFETY_CONCERN,
            subject="N-1 Vulnerability",
            system_state=system_state,
            scheduler_name="Test",
        )

        assert any("N-1 VULNERABILITY" in f for f in mfr.findings)

    def test_mfr_extracts_coverage_finding(self):
        """Test MFR extracts low coverage finding."""
        generator = MFRGenerator()

        system_state = {
            "n1_pass": True,
            "coverage_rate": 0.80,
        }

        mfr = generator.generate_mfr(
            mfr_type=MFRType.SAFETY_CONCERN,
            subject="Coverage Degradation",
            system_state=system_state,
            scheduler_name="Test",
        )

        assert any("COVERAGE DEGRADED" in f for f in mfr.findings)

    def test_mfr_risk_assessment_catastrophic(self):
        """Test MFR correctly assesses catastrophic risk."""
        generator = MFRGenerator()

        system_state = {
            "n1_pass": False,
            "n2_pass": False,
            "coverage_rate": 0.65,
            "average_allostatic_load": 85,
            "equilibrium_state": "critical",
        }

        mfr = generator.generate_mfr(
            mfr_type=MFRType.SAFETY_CONCERN,
            subject="Critical Conditions",
            system_state=system_state,
            scheduler_name="Test",
        )

        assert mfr.risk_level == RiskLevel.CATASTROPHIC
        assert "CATASTROPHIC" in mfr.risk_assessment

    def test_mfr_document_hash_unique(self):
        """Test each MFR has unique hash."""
        generator = MFRGenerator()
        system_state = {"n1_pass": True, "coverage_rate": 0.95}

        mfr1 = generator.generate_mfr(
            mfr_type=MFRType.RISK_ACCEPTANCE,
            subject="Test 1",
            system_state=system_state,
            scheduler_name="Test",
        )

        mfr2 = generator.generate_mfr(
            mfr_type=MFRType.RISK_ACCEPTANCE,
            subject="Test 2",
            system_state=system_state,
            scheduler_name="Test",
        )

        assert mfr1.document_hash != mfr2.document_hash

    def test_mfr_distribution_list(self):
        """Test MFR has appropriate distribution list."""
        generator = MFRGenerator()
        system_state = {"n1_pass": True}

        mfr = generator.generate_mfr(
            mfr_type=MFRType.STAND_DOWN,
            subject="Stand Down",
            system_state=system_state,
            scheduler_name="Test",
        )

        assert "Commander" in mfr.distribution_list
        assert "DIO" in mfr.distribution_list


# =============================================================================
# Circuit Breaker Tests
# =============================================================================


class TestCircuitBreaker:
    """Tests for scheduling circuit breaker (safety stand-down)."""

    def test_initial_state_closed(self):
        """Test circuit breaker starts closed."""
        cb = CircuitBreaker()
        assert cb.state == CircuitBreakerState.CLOSED

    def test_trip_on_n1_failure(self):
        """Test circuit breaker trips on N-1 failure."""
        cb = CircuitBreaker()

        tripped, trigger, details = cb.check_and_trip(
            n1_pass=False,
            n2_pass=True,
            coverage_rate=0.95,
            average_allostatic_load=50,
            volatility_level="normal",
            compensation_debt=100,
        )

        assert tripped is True
        assert trigger == CircuitBreakerTrigger.N1_VIOLATION
        assert cb.state == CircuitBreakerState.OPEN

    def test_trip_on_coverage_collapse(self):
        """Test circuit breaker trips on coverage collapse."""
        cb = CircuitBreaker()

        tripped, trigger, details = cb.check_and_trip(
            n1_pass=True,
            n2_pass=True,
            coverage_rate=0.65,  # Below 70% threshold
            average_allostatic_load=50,
            volatility_level="normal",
            compensation_debt=100,
        )

        assert tripped is True
        assert trigger == CircuitBreakerTrigger.COVERAGE_COLLAPSE
        assert "70%" in details

    def test_trip_on_allostatic_overload(self):
        """Test circuit breaker trips on allostatic overload."""
        cb = CircuitBreaker()

        tripped, trigger, details = cb.check_and_trip(
            n1_pass=True,
            n2_pass=True,
            coverage_rate=0.90,
            average_allostatic_load=85,  # Above 80 threshold
            volatility_level="normal",
            compensation_debt=100,
        )

        assert tripped is True
        assert trigger == CircuitBreakerTrigger.ALLOSTATIC_OVERLOAD

    def test_trip_on_critical_volatility(self):
        """Test circuit breaker trips on critical volatility."""
        cb = CircuitBreaker()

        tripped, trigger, details = cb.check_and_trip(
            n1_pass=True,
            n2_pass=True,
            coverage_rate=0.90,
            average_allostatic_load=50,
            volatility_level="critical",
            compensation_debt=100,
        )

        assert tripped is True
        assert trigger == CircuitBreakerTrigger.VOLATILITY_CRITICAL

    def test_no_trip_healthy_system(self):
        """Test circuit breaker does not trip on healthy system."""
        cb = CircuitBreaker()

        tripped, trigger, details = cb.check_and_trip(
            n1_pass=True,
            n2_pass=True,
            coverage_rate=0.95,
            average_allostatic_load=40,
            volatility_level="normal",
            compensation_debt=100,
        )

        assert tripped is False
        assert cb.state == CircuitBreakerState.CLOSED

    def test_locked_operations_when_open(self):
        """Test operations are locked when breaker is open."""
        cb = CircuitBreaker()

        # Trip the breaker
        cb.check_and_trip(
            n1_pass=False,
            n2_pass=True,
            coverage_rate=0.95,
            average_allostatic_load=50,
            volatility_level="normal",
            compensation_debt=100,
        )

        # Check operations
        allowed, reason = cb.is_operation_allowed("new_assignments")
        assert allowed is False
        assert "451" in reason  # HTTP 451 Unavailable For Legal Reasons

        # Patient safety always allowed
        allowed, reason = cb.is_operation_allowed("emergency_coverage")
        assert allowed is True

    def test_override_allows_operations(self):
        """Test override allows locked operations."""
        cb = CircuitBreaker()

        # Trip the breaker
        cb.check_and_trip(
            n1_pass=False,
            n2_pass=True,
            coverage_rate=0.95,
            average_allostatic_load=50,
            volatility_level="normal",
            compensation_debt=100,
        )

        # Override
        override = cb.override_breaker(
            authority=OverrideAuthority.COMMANDER,
            reason="Mission critical requirement",
            duration_hours=4,
        )

        # Now operations should be allowed
        allowed, reason = cb.is_operation_allowed("new_assignments")
        assert allowed is True

        assert override.authority == OverrideAuthority.COMMANDER

    def test_override_expires(self):
        """Test override expires after duration."""
        cb = CircuitBreaker()

        # Trip and override with expired time
        cb._trip(CircuitBreakerTrigger.N1_VIOLATION, "test")

        cb.override = type(
            "obj",
            (object,),
            {
                "id": uuid4(),
                "authority": OverrideAuthority.COMMANDER,
                "reason": "test",
                "activated_at": datetime.now() - timedelta(hours=2),
                "expires_at": datetime.now() - timedelta(hours=1),  # Expired
                "mfr_id": None,
            },
        )()

        # Override should not be active
        assert cb._override_active() is False

        # Operations should be blocked
        allowed, reason = cb.is_operation_allowed("new_assignments")
        assert allowed is False

    def test_close_breaker(self):
        """Test closing the circuit breaker."""
        cb = CircuitBreaker()

        # Trip then close
        cb._trip(CircuitBreakerTrigger.N1_VIOLATION, "test")
        assert cb.state == CircuitBreakerState.OPEN

        cb.close()
        assert cb.state == CircuitBreakerState.CLOSED
        assert cb.trigger is None

    def test_status_report(self):
        """Test getting circuit breaker status."""
        cb = CircuitBreaker()

        cb._trip(CircuitBreakerTrigger.COVERAGE_COLLAPSE, "Test coverage failure")

        status = cb.get_status()

        assert status.state == CircuitBreakerState.OPEN
        assert status.trigger == CircuitBreakerTrigger.COVERAGE_COLLAPSE
        assert "new_assignments" in status.locked_operations
        assert "emergency_coverage" in status.allowed_operations


# =============================================================================
# RFF Drafter Tests
# =============================================================================


class TestRFFDrafter:
    """Tests for Request for Forces document drafting."""

    def test_draft_rff_basic(self):
        """Test basic RFF generation."""
        drafter = RFFDrafter()

        system_state = {
            "coverage_rate": 0.75,
            "n1_pass": False,
            "average_allostatic_load": 65,
            "load_shedding_level": "ORANGE",
            "equilibrium_state": "stressed",
        }

        rff = drafter.draft_rff(
            requesting_unit="Internal Medicine",
            mission_affected=[MissionType.INPATIENT_MEDICINE],
            mos_required=["60H", "60M"],
            personnel_count=2,
            duration_days=30,
            justification="Critical staffing shortage affecting patient care",
            system_state=system_state,
        )

        assert rff.requesting_unit == "Internal Medicine"
        assert rff.personnel_count == 2
        assert len(rff.mos_required) == 2
        assert "60H" in rff.mos_required
        assert "REQUEST FOR FORCES" in rff.header
        assert rff.document_hash is not None

    def test_rff_includes_situation(self):
        """Test RFF includes situation paragraph."""
        drafter = RFFDrafter()

        system_state = {
            "coverage_rate": 0.70,
            "n1_pass": False,
        }

        rff = drafter.draft_rff(
            requesting_unit="Test Unit",
            mission_affected=[MissionType.SURGICAL_SERVICES],
            mos_required=["60H"],
            personnel_count=1,
            duration_days=14,
            justification="Test",
            system_state=system_state,
        )

        assert "SITUATION" in rff.situation
        assert "Coverage Rate: 70%" in rff.situation

    def test_rff_includes_cascade_warning(self):
        """Test RFF includes cascade failure warning."""
        drafter = RFFDrafter()

        system_state = {
            "coverage_rate": 0.75,
            "n1_pass": True,
        }

        cascade_prediction = {
            "days_until_exhaustion": 14,
        }

        rff = drafter.draft_rff(
            requesting_unit="Test Unit",
            mission_affected=[MissionType.EMERGENCY_DEPARTMENT],
            mos_required=["60H"],
            personnel_count=2,
            duration_days=30,
            justification="Test",
            system_state=system_state,
            cascade_prediction=cascade_prediction,
        )

        assert "14 days" in rff.situation
        assert "CRITICAL" in rff.situation

    def test_rff_projected_without_support(self):
        """Test RFF includes projection without support."""
        drafter = RFFDrafter()

        system_state = {
            "coverage_rate": 0.75,
            "n1_pass": False,
            "average_allostatic_load": 65,
        }

        cascade_prediction = {
            "days_until_exhaustion": 10,
        }

        rff = drafter.draft_rff(
            requesting_unit="Test Unit",
            mission_affected=[MissionType.LEVEL_1_TRAUMA],
            mos_required=["60H", "66H"],
            personnel_count=3,
            duration_days=30,
            justification="Test",
            system_state=system_state,
            cascade_prediction=cascade_prediction,
        )

        assert rff.projected_without_support["mission_failure_likely"] is True
        assert len(rff.projected_without_support["outcomes"]) > 0


# =============================================================================
# Iron Dome Service Tests
# =============================================================================


class TestIronDomeService:
    """Tests for unified Iron Dome service."""

    def test_assess_readiness_healthy(self):
        """Test readiness assessment for healthy system."""
        service = IronDomeService()

        result = service.assess_readiness(
            load_shedding_level=LoadSheddingLevel.NORMAL,
            equilibrium_state=EquilibriumState.STABLE,
            n1_pass=True,
            n2_pass=True,
            coverage_rate=0.95,
            available_faculty=10,
            required_faculty=10,
        )

        assert result["overall_rating"] == "C-1"
        assert result["overall_capability"] == "FMC"
        assert result["personnel_rating"] == "P-1"

    def test_assess_readiness_degraded(self):
        """Test readiness assessment for degraded system."""
        service = IronDomeService()

        result = service.assess_readiness(
            load_shedding_level=LoadSheddingLevel.RED,
            equilibrium_state=EquilibriumState.STRESSED,
            n1_pass=False,
            n2_pass=False,
            coverage_rate=0.75,
            available_faculty=7,
            required_faculty=10,
        )

        assert result["overall_rating"] == "C-4"
        assert result["overall_capability"] == "NMC"
        assert "RED" in result["executive_summary"]

    def test_check_circuit_breaker(self):
        """Test circuit breaker check through service."""
        service = IronDomeService()

        result = service.check_circuit_breaker(
            n1_pass=False,
            n2_pass=True,
            coverage_rate=0.90,
            average_allostatic_load=50,
            volatility_level="normal",
            compensation_debt=100,
        )

        assert result["tripped"] is True
        assert result["state"] == "open"
        assert result["trigger"] == "n1_violation"

    def test_generate_risk_mfr(self):
        """Test risk MFR generation through service."""
        service = IronDomeService()

        system_state = {
            "n1_pass": False,
            "coverage_rate": 0.80,
        }

        mfr = service.generate_risk_mfr(
            subject="Test Risk Acceptance",
            system_state=system_state,
            scheduler_name="Test Scheduler",
            scheduler_objection="I object to this schedule",
        )

        assert mfr.mfr_type == MFRType.RISK_ACCEPTANCE
        assert len(service.mfr_history) == 1

    def test_initiate_safety_stand_down(self):
        """Test safety stand-down initiation."""
        service = IronDomeService()

        system_state = {
            "n1_pass": False,
            "n2_pass": False,
            "coverage_rate": 0.65,
        }

        mfr, status = service.initiate_safety_stand_down(
            reason="Critical safety concern",
            initiator="Chief Resident",
            system_state=system_state,
        )

        assert mfr.mfr_type == MFRType.STAND_DOWN
        assert status["stand_down_active"] is True
        assert status["circuit_breaker_state"] == "open"

    def test_draft_resource_request(self):
        """Test RFF drafting through service."""
        service = IronDomeService()

        system_state = {
            "coverage_rate": 0.75,
            "n1_pass": False,
        }

        rff = service.draft_resource_request(
            requesting_unit="Internal Medicine",
            mission_affected=[MissionType.INPATIENT_MEDICINE],
            mos_required=["60H"],
            personnel_count=2,
            duration_days=30,
            justification="Test request",
            system_state=system_state,
        )

        assert rff.requesting_unit == "Internal Medicine"
        assert len(service.rff_history) == 1

    def test_get_status(self):
        """Test getting overall Iron Dome status."""
        service = IronDomeService()

        # Generate some documents
        service.generate_risk_mfr(
            subject="Test",
            system_state={"n1_pass": True},
            scheduler_name="Test",
        )

        status = service.get_status()

        assert status["circuit_breaker_state"] == "closed"
        assert status["mfrs_generated"] == 1
        assert status["rffs_generated"] == 0


# =============================================================================
# Integration Tests
# =============================================================================


class TestIronDomeIntegration:
    """Integration tests for Iron Dome workflow."""

    def test_full_crisis_workflow(self):
        """Test full crisis workflow: assess -> trip -> document -> stand-down."""
        service = IronDomeService()

        # System state indicating crisis
        system_state = {
            "n1_pass": False,
            "n2_pass": False,
            "coverage_rate": 0.68,
            "average_allostatic_load": 82,
            "equilibrium_state": "critical",
            "load_shedding_level": "RED",
            "phase_transition_risk": "high",
        }

        # 1. Assess readiness
        readiness = service.assess_readiness(
            load_shedding_level=LoadSheddingLevel.RED,
            equilibrium_state=EquilibriumState.CRITICAL,
            n1_pass=False,
            n2_pass=False,
            coverage_rate=0.68,
            available_faculty=6,
            required_faculty=10,
            overloaded_faculty_count=3,
        )

        assert readiness["overall_rating"] in ("C-4", "C-5")
        assert readiness["overall_capability"] == "NMC"

        # 2. Check circuit breaker (should trip)
        cb_result = service.check_circuit_breaker(
            n1_pass=False,
            n2_pass=False,
            coverage_rate=0.68,
            average_allostatic_load=82,
            volatility_level="high",
            compensation_debt=500,
        )

        assert cb_result["tripped"] is True

        # 3. Generate risk MFR if trying to publish anyway
        mfr = service.generate_risk_mfr(
            subject="Schedule Publication Under Crisis Conditions",
            system_state=system_state,
            scheduler_name="SGT Smith",
            scheduler_objection="Command has directed schedule publication despite system warnings",
        )

        assert mfr.risk_level in (RiskLevel.CRITICAL, RiskLevel.CATASTROPHIC)
        assert mfr.requires_commander_signature is True

        # 4. Draft RFF for support
        rff = service.draft_resource_request(
            requesting_unit="Internal Medicine Residency",
            mission_affected=[
                MissionType.INPATIENT_MEDICINE,
                MissionType.GRADUATE_MEDICAL_EDUCATION,
            ],
            mos_required=["60H", "60M"],
            personnel_count=3,
            duration_days=45,
            justification="Unit at critical staffing levels with imminent mission failure",
            system_state=system_state,
            cascade_prediction={"days_until_exhaustion": 12},
        )

        assert rff.projected_without_support["mission_failure_likely"] is True

        # 5. Final status
        status = service.get_status()

        assert status["scheduling_locked"] is True
        assert status["mfrs_generated"] == 1
        assert status["rffs_generated"] == 1
