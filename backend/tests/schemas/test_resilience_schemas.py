"""Tests for Resilience API schemas (Pydantic validation and enum coverage)."""

from datetime import date, datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas.resilience import (
    # Enums - Tier 1
    UtilizationLevel,
    DefenseLevel,
    LoadSheddingLevel,
    OverallStatus,
    FallbackScenario,
    CrisisSeverity,
    # Enums - Tier 2 Homeostasis
    AllostasisState,
    DeviationSeverity,
    CorrectiveActionType,
    # Enums - Tier 2 Zones
    ZoneStatus,
    ZoneType,
    ContainmentLevel,
    BorrowingPriority,
    # Enums - Tier 2 Equilibrium
    EquilibriumState,
    StressType,
    CompensationType,
    # Enums - Tier 3
    DecisionComplexity,
    DecisionCategory,
    CognitiveState,
    DecisionOutcome,
    TrailType,
    TrailStrength,
    SignalType,
    HubRiskLevel,
    HubProtectionStatus,
    CrossTrainingPriority,
    # Enums - SOC / Circuit Breaker
    SOCWarningLevel,
    CircuitBreakerState,
    BreakerSeverity,
    # Request schemas with Field validators
    HealthCheckRequest,
    CrisisActivationRequest,
    CrisisDeactivationRequest,
    FallbackActivationRequest,
    FallbackDeactivationRequest,
    LoadSheddingRequest,
    HomeostasisCheckRequest,
    AllostasisCalculateRequest,
    ZoneCreateRequest,
    BorrowingRequest,
    ZoneIncidentRequest,
    ContainmentSetRequest,
    StressApplyRequest,
    CompensationInitiateRequest,
    StressPredictionRequest,
    DecisionRequest,
    PreferenceTrailRequest,
    HubProtectionPlanRequest,
    DefenseLevelRequest,
    UtilizationThresholdRequest,
    BurnoutRtRequest,
    CriticalSlowingDownRequest,
    # Response schemas
    UtilizationMetrics,
    RedundancyStatus,
    VulnerabilitySummary,
    HealthCheckResponse,
    CrisisResponse,
    FallbackInfo,
    FallbackListResponse,
    FallbackActivationResponse,
    LoadSheddingStatus,
    CentralityScore,
    HealthCheckHistoryItem,
    HealthCheckHistoryResponse,
    EventHistoryItem,
    EventHistoryResponse,
    HomeostasisReport,
    HomeostasisStatusResponse,
    SetpointInfo,
    FeedbackLoopStatus,
    CorrectiveActionInfo,
    AllostasisMetricsResponse,
    PositiveFeedbackRiskInfo,
    ZoneFacultyAssignment,
    ZoneHealthReport,
    ZoneResponse,
    BorrowingResponse,
    ZoneIncidentResponse,
    BlastRadiusReportResponse,
    StressResponse,
    CompensationResponse,
    EquilibriumShiftResponse,
    StressPredictionResponse,
    EquilibriumReportResponse,
    Tier2StatusResponse,
    CognitiveSessionResponse,
    DecisionResponse,
    DecisionQueueResponse,
    CognitiveLoadAnalysis,
    PreferenceTrailResponse,
    CollectivePreferenceResponse,
    StigmergyStatusResponse,
    FacultyCentralityResponse,
    HubProfileResponse,
    HubProtectionPlanResponse,
    CrossTrainingRecommendationResponse,
    HubDistributionResponse,
    Tier3StatusResponse,
    CriticalSlowingDownResponse,
    SOCMetricsHistoryResponse,
    SuccessResponse,
    FallbackDeactivationResponse,
    MTFComplianceResponse,
    DefenseLevelResponse,
    UtilizationThresholdResponse,
    BurnoutRtResponse,
    StateTransitionInfo,
    CircuitBreakerInfo,
    AllBreakersStatusResponse,
    BreakerHealthMetrics,
    BreakerHealthResponse,
    ContainmentSetResponse,
    StressResolveResponse,
    CognitiveSessionStartResponse,
    CognitiveSessionEndResponse,
    CognitiveSessionStatusResponse,
    DecisionCreateResponse,
    DecisionResolveResponse,
    PrioritizedDecisionsResponse,
    ScheduleCognitiveAnalysisResponse,
    PreferenceRecordResponse,
    BehavioralSignalResponse,
    FacultyPreferencesResponse,
    SwapNetworkResponse,
    AssignmentSuggestionsResponse,
    StigmergyPatternsResponse,
    TrailEvaporationResponse,
    HubAnalysisResponse,
    TopHubsResponse,
    HubProfileDetailResponse,
    CrossTrainingRecommendationsResponse,
    HubProtectionPlanCreateResponse,
    HubDistributionReportResponse,
    HubStatusResponse,
    ZoneListResponse,
    ZoneAssignmentResponse,
)


# ===========================================================================
# Enum Tests - Tier 1
# ===========================================================================


class TestUtilizationLevelEnum:
    def test_values(self):
        assert UtilizationLevel.GREEN.value == "GREEN"
        assert UtilizationLevel.YELLOW.value == "YELLOW"
        assert UtilizationLevel.ORANGE.value == "ORANGE"
        assert UtilizationLevel.RED.value == "RED"
        assert UtilizationLevel.BLACK.value == "BLACK"

    def test_count(self):
        assert len(UtilizationLevel) == 5

    def test_is_str_enum(self):
        assert isinstance(UtilizationLevel.GREEN, str)


class TestDefenseLevelEnum:
    def test_values(self):
        assert DefenseLevel.PREVENTION.value == "PREVENTION"
        assert DefenseLevel.CONTROL.value == "CONTROL"
        assert DefenseLevel.SAFETY_SYSTEMS.value == "SAFETY_SYSTEMS"
        assert DefenseLevel.CONTAINMENT.value == "CONTAINMENT"
        assert DefenseLevel.EMERGENCY.value == "EMERGENCY"

    def test_count(self):
        assert len(DefenseLevel) == 5


class TestLoadSheddingLevelEnum:
    def test_values(self):
        assert LoadSheddingLevel.NORMAL.value == "NORMAL"
        assert LoadSheddingLevel.CRITICAL.value == "CRITICAL"

    def test_count(self):
        assert len(LoadSheddingLevel) == 6


class TestOverallStatusEnum:
    def test_values(self):
        assert OverallStatus.HEALTHY.value == "healthy"
        assert OverallStatus.EMERGENCY.value == "emergency"

    def test_count(self):
        assert len(OverallStatus) == 5


class TestFallbackScenarioEnum:
    def test_count(self):
        assert len(FallbackScenario) == 7

    def test_contains_pcs(self):
        assert FallbackScenario.PCS_SEASON_50_PERCENT.value == "pcs_season_50_percent"


class TestCrisisSeverityEnum:
    def test_count(self):
        assert len(CrisisSeverity) == 4

    def test_values(self):
        values = {e.value for e in CrisisSeverity}
        assert values == {"minor", "moderate", "severe", "critical"}


# ===========================================================================
# Enum Tests - Tier 2
# ===========================================================================


class TestTier2Enums:
    def test_allostasis_state_count(self):
        assert len(AllostasisState) == 4

    def test_deviation_severity_count(self):
        assert len(DeviationSeverity) == 5

    def test_corrective_action_type_count(self):
        assert len(CorrectiveActionType) == 6

    def test_zone_status_count(self):
        assert len(ZoneStatus) == 5

    def test_zone_type_count(self):
        assert len(ZoneType) == 6

    def test_containment_level_count(self):
        assert len(ContainmentLevel) == 5

    def test_borrowing_priority_count(self):
        assert len(BorrowingPriority) == 4

    def test_equilibrium_state_count(self):
        assert len(EquilibriumState) == 5

    def test_stress_type_count(self):
        assert len(StressType) == 6

    def test_compensation_type_count(self):
        assert len(CompensationType) == 7


# ===========================================================================
# Enum Tests - Tier 3
# ===========================================================================


class TestTier3Enums:
    def test_decision_complexity_count(self):
        assert len(DecisionComplexity) == 5

    def test_decision_category_count(self):
        assert len(DecisionCategory) == 8

    def test_cognitive_state_count(self):
        assert len(CognitiveState) == 5

    def test_decision_outcome_count(self):
        assert len(DecisionOutcome) == 5

    def test_trail_type_count(self):
        assert len(TrailType) == 5

    def test_trail_strength_count(self):
        assert len(TrailStrength) == 5

    def test_signal_type_count(self):
        assert len(SignalType) == 8

    def test_hub_risk_level_count(self):
        assert len(HubRiskLevel) == 5

    def test_hub_protection_status_count(self):
        assert len(HubProtectionStatus) == 4

    def test_cross_training_priority_count(self):
        assert len(CrossTrainingPriority) == 4


# ===========================================================================
# Enum Tests - SOC / Circuit Breaker
# ===========================================================================


class TestSOCAndBreakerEnums:
    def test_soc_warning_level_count(self):
        assert len(SOCWarningLevel) == 5

    def test_soc_has_unknown(self):
        assert SOCWarningLevel.UNKNOWN.value == "unknown"

    def test_circuit_breaker_state_count(self):
        assert len(CircuitBreakerState) == 3

    def test_circuit_breaker_values(self):
        assert CircuitBreakerState.CLOSED.value == "closed"
        assert CircuitBreakerState.OPEN.value == "open"
        assert CircuitBreakerState.HALF_OPEN.value == "half_open"

    def test_breaker_severity_count(self):
        assert len(BreakerSeverity) == 4


# ===========================================================================
# Request Schema Validation Tests - Tier 1
# ===========================================================================


class TestHealthCheckRequest:
    def test_defaults(self):
        r = HealthCheckRequest()
        assert r.start_date is None
        assert r.end_date is None
        assert r.include_contingency is False

    def test_with_dates(self):
        r = HealthCheckRequest(
            start_date=date(2026, 1, 1),
            end_date=date(2026, 1, 31),
            include_contingency=True,
        )
        assert r.include_contingency is True


class TestCrisisActivationRequest:
    def test_valid(self):
        r = CrisisActivationRequest(
            severity=CrisisSeverity.CRITICAL,
            reason="Faculty shortage exceeding safe thresholds",
        )
        assert r.severity == CrisisSeverity.CRITICAL

    def test_reason_too_short(self):
        with pytest.raises(ValidationError) as exc_info:
            CrisisActivationRequest(severity=CrisisSeverity.MINOR, reason="short")
        assert "reason" in str(exc_info.value).lower() or "min_length" in str(
            exc_info.value
        )

    def test_reason_too_long(self):
        with pytest.raises(ValidationError):
            CrisisActivationRequest(severity=CrisisSeverity.MINOR, reason="x" * 501)

    def test_reason_min_boundary(self):
        r = CrisisActivationRequest(severity=CrisisSeverity.MINOR, reason="x" * 10)
        assert len(r.reason) == 10

    def test_reason_max_boundary(self):
        r = CrisisActivationRequest(severity=CrisisSeverity.MINOR, reason="x" * 500)
        assert len(r.reason) == 500


class TestCrisisDeactivationRequest:
    def test_valid(self):
        r = CrisisDeactivationRequest(reason="Situation resolved, normal ops resume")
        assert len(r.reason) >= 10

    def test_reason_too_short(self):
        with pytest.raises(ValidationError):
            CrisisDeactivationRequest(reason="ok")


class TestFallbackActivationRequest:
    def test_valid(self):
        r = FallbackActivationRequest(
            scenario=FallbackScenario.HOLIDAY_SKELETON,
            reason="Holiday period approaching",
        )
        assert r.scenario == FallbackScenario.HOLIDAY_SKELETON

    def test_reason_too_short(self):
        with pytest.raises(ValidationError):
            FallbackActivationRequest(
                scenario=FallbackScenario.MASS_CASUALTY, reason="bad"
            )


class TestFallbackDeactivationRequest:
    def test_valid(self):
        r = FallbackDeactivationRequest(
            scenario=FallbackScenario.WEATHER_EMERGENCY,
            reason="Weather emergency passed",
        )
        assert r.scenario == FallbackScenario.WEATHER_EMERGENCY


class TestLoadSheddingRequest:
    def test_valid(self):
        r = LoadSheddingRequest(
            level=LoadSheddingLevel.ORANGE,
            reason="Staffing below critical threshold",
        )
        assert r.level == LoadSheddingLevel.ORANGE

    def test_reason_too_short(self):
        with pytest.raises(ValidationError):
            LoadSheddingRequest(level=LoadSheddingLevel.RED, reason="bad")


# ===========================================================================
# Request Schema Validation Tests - Tier 2
# ===========================================================================


class TestAllostasisCalculateRequest:
    def test_defaults(self):
        uid = uuid4()
        r = AllostasisCalculateRequest(entity_id=uid)
        assert r.entity_type == "faculty"
        assert r.consecutive_weekend_calls == 0
        assert r.nights_past_month == 0

    def test_entity_type_faculty(self):
        r = AllostasisCalculateRequest(entity_id=uuid4(), entity_type="faculty")
        assert r.entity_type == "faculty"

    def test_entity_type_system(self):
        r = AllostasisCalculateRequest(entity_id=uuid4(), entity_type="system")
        assert r.entity_type == "system"

    def test_entity_type_invalid(self):
        with pytest.raises(ValidationError):
            AllostasisCalculateRequest(entity_id=uuid4(), entity_type="resident")


class TestZoneCreateRequest:
    def test_valid(self):
        r = ZoneCreateRequest(
            name="ICU",
            zone_type=ZoneType.INPATIENT,
        )
        assert r.name == "ICU"
        assert r.description == ""
        assert r.minimum_coverage == 1
        assert r.optimal_coverage == 2
        assert r.priority == 5

    def test_name_too_long(self):
        with pytest.raises(ValidationError):
            ZoneCreateRequest(name="x" * 101, zone_type=ZoneType.INPATIENT)

    def test_name_empty(self):
        with pytest.raises(ValidationError):
            ZoneCreateRequest(name="", zone_type=ZoneType.INPATIENT)

    def test_description_too_long(self):
        with pytest.raises(ValidationError):
            ZoneCreateRequest(
                name="ICU",
                zone_type=ZoneType.INPATIENT,
                description="x" * 501,
            )

    def test_priority_boundaries(self):
        r_min = ZoneCreateRequest(name="A", zone_type=ZoneType.EDUCATION, priority=1)
        r_max = ZoneCreateRequest(name="B", zone_type=ZoneType.EDUCATION, priority=10)
        assert r_min.priority == 1
        assert r_max.priority == 10

    def test_priority_below_min(self):
        with pytest.raises(ValidationError):
            ZoneCreateRequest(name="A", zone_type=ZoneType.EDUCATION, priority=0)

    def test_priority_above_max(self):
        with pytest.raises(ValidationError):
            ZoneCreateRequest(name="A", zone_type=ZoneType.EDUCATION, priority=11)

    def test_minimum_coverage_negative(self):
        with pytest.raises(ValidationError):
            ZoneCreateRequest(
                name="A", zone_type=ZoneType.INPATIENT, minimum_coverage=-1
            )


class TestBorrowingRequest:
    def _valid_kwargs(self):
        return {
            "requesting_zone_id": uuid4(),
            "lending_zone_id": uuid4(),
            "faculty_id": uuid4(),
            "priority": BorrowingPriority.HIGH,
            "reason": "Need additional coverage for ICU",
        }

    def test_valid(self):
        r = BorrowingRequest(**self._valid_kwargs())
        assert r.duration_hours == 8  # default

    def test_duration_hours_min(self):
        kw = self._valid_kwargs()
        r = BorrowingRequest(**kw, duration_hours=1)
        assert r.duration_hours == 1

    def test_duration_hours_max(self):
        kw = self._valid_kwargs()
        r = BorrowingRequest(**kw, duration_hours=72)
        assert r.duration_hours == 72

    def test_duration_hours_too_high(self):
        kw = self._valid_kwargs()
        with pytest.raises(ValidationError):
            BorrowingRequest(**kw, duration_hours=73)

    def test_duration_hours_zero(self):
        kw = self._valid_kwargs()
        with pytest.raises(ValidationError):
            BorrowingRequest(**kw, duration_hours=0)

    def test_reason_too_short(self):
        kw = self._valid_kwargs()
        kw["reason"] = "short"
        with pytest.raises(ValidationError):
            BorrowingRequest(**kw)


class TestZoneIncidentRequest:
    def _valid_kwargs(self):
        return {
            "zone_id": uuid4(),
            "incident_type": "staffing_gap",
            "description": "Unexpected faculty absence today",
            "severity": "moderate",
        }

    def test_valid(self):
        r = ZoneIncidentRequest(**self._valid_kwargs())
        assert r.severity == "moderate"
        assert r.faculty_affected == []

    def test_severity_pattern_valid(self):
        for sev in ("minor", "moderate", "severe", "critical"):
            kw = self._valid_kwargs()
            kw["severity"] = sev
            r = ZoneIncidentRequest(**kw)
            assert r.severity == sev

    def test_severity_pattern_invalid(self):
        kw = self._valid_kwargs()
        kw["severity"] = "HIGH"
        with pytest.raises(ValidationError):
            ZoneIncidentRequest(**kw)

    def test_incident_type_too_long(self):
        kw = self._valid_kwargs()
        kw["incident_type"] = "x" * 51
        with pytest.raises(ValidationError):
            ZoneIncidentRequest(**kw)

    def test_incident_type_empty(self):
        kw = self._valid_kwargs()
        kw["incident_type"] = ""
        with pytest.raises(ValidationError):
            ZoneIncidentRequest(**kw)

    def test_description_too_short(self):
        kw = self._valid_kwargs()
        kw["description"] = "short"
        with pytest.raises(ValidationError):
            ZoneIncidentRequest(**kw)


class TestContainmentSetRequest:
    def test_valid(self):
        r = ContainmentSetRequest(
            level=ContainmentLevel.STRICT,
            reason="Multiple zone failures detected",
        )
        assert r.level == ContainmentLevel.STRICT

    def test_reason_too_short(self):
        with pytest.raises(ValidationError):
            ContainmentSetRequest(level=ContainmentLevel.NONE, reason="short")


class TestStressApplyRequest:
    def _valid_kwargs(self):
        return {
            "stress_type": StressType.FACULTY_LOSS,
            "description": "Two faculty members on emergency leave",
            "magnitude": 0.5,
            "duration_days": 14,
            "capacity_impact": -0.3,
        }

    def test_valid(self):
        r = StressApplyRequest(**self._valid_kwargs())
        assert r.demand_impact == 0.0  # default
        assert r.is_acute is True
        assert r.is_reversible is True

    def test_magnitude_zero(self):
        kw = self._valid_kwargs()
        kw["magnitude"] = 0.0
        r = StressApplyRequest(**kw)
        assert r.magnitude == 0.0

    def test_magnitude_one(self):
        kw = self._valid_kwargs()
        kw["magnitude"] = 1.0
        r = StressApplyRequest(**kw)
        assert r.magnitude == 1.0

    def test_magnitude_above_one(self):
        kw = self._valid_kwargs()
        kw["magnitude"] = 1.1
        with pytest.raises(ValidationError):
            StressApplyRequest(**kw)

    def test_magnitude_negative(self):
        kw = self._valid_kwargs()
        kw["magnitude"] = -0.1
        with pytest.raises(ValidationError):
            StressApplyRequest(**kw)

    def test_capacity_impact_must_be_negative_or_zero(self):
        kw = self._valid_kwargs()
        kw["capacity_impact"] = 0.1
        with pytest.raises(ValidationError):
            StressApplyRequest(**kw)

    def test_capacity_impact_negative_one(self):
        kw = self._valid_kwargs()
        kw["capacity_impact"] = -1.0
        r = StressApplyRequest(**kw)
        assert r.capacity_impact == -1.0

    def test_demand_impact_positive(self):
        kw = self._valid_kwargs()
        kw["demand_impact"] = 0.5
        r = StressApplyRequest(**kw)
        assert r.demand_impact == 0.5

    def test_demand_impact_negative(self):
        kw = self._valid_kwargs()
        kw["demand_impact"] = -0.1
        with pytest.raises(ValidationError):
            StressApplyRequest(**kw)

    def test_duration_days_min(self):
        kw = self._valid_kwargs()
        kw["duration_days"] = 1
        r = StressApplyRequest(**kw)
        assert r.duration_days == 1

    def test_duration_days_max(self):
        kw = self._valid_kwargs()
        kw["duration_days"] = 365
        r = StressApplyRequest(**kw)
        assert r.duration_days == 365

    def test_duration_days_zero(self):
        kw = self._valid_kwargs()
        kw["duration_days"] = 0
        with pytest.raises(ValidationError):
            StressApplyRequest(**kw)

    def test_duration_days_above_max(self):
        kw = self._valid_kwargs()
        kw["duration_days"] = 366
        with pytest.raises(ValidationError):
            StressApplyRequest(**kw)


class TestCompensationInitiateRequest:
    def _valid_kwargs(self):
        return {
            "stress_id": uuid4(),
            "compensation_type": CompensationType.OVERTIME,
            "description": "Authorizing overtime for remaining staff",
            "magnitude": 0.5,
        }

    def test_valid(self):
        r = CompensationInitiateRequest(**self._valid_kwargs())
        assert r.effectiveness == 0.8  # default
        assert r.sustainability_days == 30  # default
        assert r.immediate_cost == 0.0
        assert r.hidden_cost == 0.0

    def test_effectiveness_boundaries(self):
        kw = self._valid_kwargs()
        kw["effectiveness"] = 0.0
        r = CompensationInitiateRequest(**kw)
        assert r.effectiveness == 0.0

        kw["effectiveness"] = 1.0
        r = CompensationInitiateRequest(**kw)
        assert r.effectiveness == 1.0

    def test_effectiveness_above_one(self):
        kw = self._valid_kwargs()
        kw["effectiveness"] = 1.1
        with pytest.raises(ValidationError):
            CompensationInitiateRequest(**kw)

    def test_sustainability_days_boundaries(self):
        kw = self._valid_kwargs()
        kw["sustainability_days"] = 1
        r = CompensationInitiateRequest(**kw)
        assert r.sustainability_days == 1

        kw["sustainability_days"] = 365
        r = CompensationInitiateRequest(**kw)
        assert r.sustainability_days == 365

    def test_sustainability_days_zero(self):
        kw = self._valid_kwargs()
        kw["sustainability_days"] = 0
        with pytest.raises(ValidationError):
            CompensationInitiateRequest(**kw)

    def test_costs_must_be_non_negative(self):
        kw = self._valid_kwargs()
        kw["immediate_cost"] = -1.0
        with pytest.raises(ValidationError):
            CompensationInitiateRequest(**kw)

        kw = self._valid_kwargs()
        kw["hidden_cost"] = -0.1
        with pytest.raises(ValidationError):
            CompensationInitiateRequest(**kw)


class TestStressPredictionRequest:
    def test_valid(self):
        r = StressPredictionRequest(
            stress_type=StressType.DEMAND_SURGE,
            magnitude=0.7,
            duration_days=30,
            capacity_impact=-0.2,
        )
        assert r.demand_impact == 0.0  # default

    def test_magnitude_boundaries(self):
        r = StressPredictionRequest(
            stress_type=StressType.DEMAND_SURGE,
            magnitude=0.0,
            duration_days=1,
            capacity_impact=0.0,
        )
        assert r.magnitude == 0.0

    def test_invalid_magnitude(self):
        with pytest.raises(ValidationError):
            StressPredictionRequest(
                stress_type=StressType.DEMAND_SURGE,
                magnitude=1.5,
                duration_days=30,
                capacity_impact=-0.2,
            )


# ===========================================================================
# Request Schema Validation Tests - Tier 3
# ===========================================================================


class TestDecisionRequest:
    def test_valid(self):
        r = DecisionRequest(
            category=DecisionCategory.SWAP,
            complexity=DecisionComplexity.MODERATE,
            description="Should we approve the swap between Dr A and Dr B?",
            options=["Approve", "Deny"],
        )
        assert r.is_urgent is False
        assert r.recommended_option is None

    def test_description_too_short(self):
        with pytest.raises(ValidationError):
            DecisionRequest(
                category=DecisionCategory.SWAP,
                complexity=DecisionComplexity.SIMPLE,
                description="Hi",
                options=["A", "B"],
            )

    def test_options_must_have_at_least_two(self):
        with pytest.raises(ValidationError):
            DecisionRequest(
                category=DecisionCategory.SWAP,
                complexity=DecisionComplexity.SIMPLE,
                description="Valid long description here",
                options=["Only one"],
            )


class TestPreferenceTrailRequest:
    def test_valid(self):
        r = PreferenceTrailRequest(
            faculty_id=uuid4(),
            trail_type=TrailType.PREFERENCE,
        )
        assert r.strength == 0.5  # default
        assert r.slot_type is None

    def test_strength_boundaries(self):
        r = PreferenceTrailRequest(
            faculty_id=uuid4(),
            trail_type=TrailType.AVOIDANCE,
            strength=0.0,
        )
        assert r.strength == 0.0

        r = PreferenceTrailRequest(
            faculty_id=uuid4(),
            trail_type=TrailType.AVOIDANCE,
            strength=1.0,
        )
        assert r.strength == 1.0

    def test_strength_above_one(self):
        with pytest.raises(ValidationError):
            PreferenceTrailRequest(
                faculty_id=uuid4(),
                trail_type=TrailType.WORKLOAD,
                strength=1.1,
            )

    def test_strength_negative(self):
        with pytest.raises(ValidationError):
            PreferenceTrailRequest(
                faculty_id=uuid4(),
                trail_type=TrailType.WORKLOAD,
                strength=-0.1,
            )


class TestHubProtectionPlanRequest:
    def test_valid(self):
        r = HubProtectionPlanRequest(
            hub_faculty_id=uuid4(),
            period_start=date(2026, 1, 1),
            period_end=date(2026, 3, 31),
            reason="High centrality faculty needs workload reduction",
        )
        assert r.workload_reduction == 0.3  # default
        assert r.assign_backup is True

    def test_workload_reduction_boundaries(self):
        r = HubProtectionPlanRequest(
            hub_faculty_id=uuid4(),
            period_start=date(2026, 1, 1),
            period_end=date(2026, 1, 31),
            reason="Valid reason with enough characters",
            workload_reduction=0.0,
        )
        assert r.workload_reduction == 0.0

        r = HubProtectionPlanRequest(
            hub_faculty_id=uuid4(),
            period_start=date(2026, 1, 1),
            period_end=date(2026, 1, 31),
            reason="Valid reason with enough characters",
            workload_reduction=1.0,
        )
        assert r.workload_reduction == 1.0

    def test_workload_reduction_above_one(self):
        with pytest.raises(ValidationError):
            HubProtectionPlanRequest(
                hub_faculty_id=uuid4(),
                period_start=date(2026, 1, 1),
                period_end=date(2026, 1, 31),
                reason="Valid reason with enough characters",
                workload_reduction=1.1,
            )


# ===========================================================================
# Request Schema Validation Tests - SOC / Defense / Utilization
# ===========================================================================


class TestDefenseLevelRequest:
    def test_valid(self):
        r = DefenseLevelRequest(coverage_rate=0.85)
        assert r.coverage_rate == 0.85

    def test_boundaries(self):
        r = DefenseLevelRequest(coverage_rate=0.0)
        assert r.coverage_rate == 0.0
        r = DefenseLevelRequest(coverage_rate=1.0)
        assert r.coverage_rate == 1.0

    def test_above_one(self):
        with pytest.raises(ValidationError):
            DefenseLevelRequest(coverage_rate=1.1)

    def test_negative(self):
        with pytest.raises(ValidationError):
            DefenseLevelRequest(coverage_rate=-0.1)


class TestUtilizationThresholdRequest:
    def test_valid(self):
        r = UtilizationThresholdRequest(
            available_faculty=10,
            required_blocks=15,
        )
        assert r.blocks_per_faculty_per_day == 2.0  # default
        assert r.days_in_period == 1  # default

    def test_available_faculty_zero(self):
        r = UtilizationThresholdRequest(available_faculty=0, required_blocks=0)
        assert r.available_faculty == 0

    def test_available_faculty_negative(self):
        with pytest.raises(ValidationError):
            UtilizationThresholdRequest(available_faculty=-1, required_blocks=5)

    def test_blocks_per_faculty_min(self):
        r = UtilizationThresholdRequest(
            available_faculty=5,
            required_blocks=5,
            blocks_per_faculty_per_day=0.1,
        )
        assert r.blocks_per_faculty_per_day == 0.1

    def test_blocks_per_faculty_below_min(self):
        with pytest.raises(ValidationError):
            UtilizationThresholdRequest(
                available_faculty=5,
                required_blocks=5,
                blocks_per_faculty_per_day=0.0,
            )


class TestBurnoutRtRequest:
    def test_defaults(self):
        r = BurnoutRtRequest()
        assert r.burned_out_provider_ids == []
        assert r.time_window_days == 28

    def test_time_window_boundaries(self):
        r = BurnoutRtRequest(time_window_days=7)
        assert r.time_window_days == 7
        r = BurnoutRtRequest(time_window_days=90)
        assert r.time_window_days == 90

    def test_time_window_below_min(self):
        with pytest.raises(ValidationError):
            BurnoutRtRequest(time_window_days=6)

    def test_time_window_above_max(self):
        with pytest.raises(ValidationError):
            BurnoutRtRequest(time_window_days=91)


class TestCriticalSlowingDownRequest:
    def test_valid(self):
        history = [0.7] * 60
        r = CriticalSlowingDownRequest(utilization_history=history)
        assert r.days_lookback == 60  # default

    def test_utilization_history_too_short(self):
        with pytest.raises(ValidationError):
            CriticalSlowingDownRequest(utilization_history=[0.7] * 29)

    def test_days_lookback_min(self):
        r = CriticalSlowingDownRequest(utilization_history=[0.5] * 30, days_lookback=30)
        assert r.days_lookback == 30

    def test_days_lookback_max(self):
        r = CriticalSlowingDownRequest(
            utilization_history=[0.5] * 30, days_lookback=180
        )
        assert r.days_lookback == 180

    def test_days_lookback_below_min(self):
        with pytest.raises(ValidationError):
            CriticalSlowingDownRequest(utilization_history=[0.5] * 30, days_lookback=29)

    def test_days_lookback_above_max(self):
        with pytest.raises(ValidationError):
            CriticalSlowingDownRequest(
                utilization_history=[0.5] * 30, days_lookback=181
            )


class TestHomeostasisCheckRequest:
    def test_valid(self):
        r = HomeostasisCheckRequest(
            metrics={"coverage_rate": 0.92, "faculty_utilization": 0.78}
        )
        assert r.metrics["coverage_rate"] == 0.92


# ===========================================================================
# Response Schema Tests - Tier 1
# ===========================================================================


class TestUtilizationMetricsResponse:
    def test_valid(self):
        m = UtilizationMetrics(
            utilization_rate=0.75,
            level=UtilizationLevel.YELLOW,
            buffer_remaining=0.05,
            wait_time_multiplier=3.0,
            safe_capacity=80,
            current_demand=75,
            theoretical_capacity=100,
        )
        assert m.utilization_rate == 0.75

    def test_utilization_rate_above_one(self):
        with pytest.raises(ValidationError):
            UtilizationMetrics(
                utilization_rate=1.1,
                level=UtilizationLevel.BLACK,
                buffer_remaining=0.0,
                wait_time_multiplier=100.0,
                safe_capacity=80,
                current_demand=110,
                theoretical_capacity=100,
            )

    def test_utilization_rate_negative(self):
        with pytest.raises(ValidationError):
            UtilizationMetrics(
                utilization_rate=-0.1,
                level=UtilizationLevel.GREEN,
                buffer_remaining=0.5,
                wait_time_multiplier=0.0,
                safe_capacity=80,
                current_demand=10,
                theoretical_capacity=100,
            )


class TestHomeostasisReport:
    def test_valid(self):
        r = HomeostasisReport(
            timestamp=datetime.now(),
            overall_state=AllostasisState.HOMEOSTASIS,
            feedback_loops_healthy=4,
            feedback_loops_deviating=1,
            active_corrections=0,
            positive_feedback_risks=0,
            average_allostatic_load=25.0,
        )
        assert r.recommendations == []  # default

    def test_feedback_loops_healthy_negative(self):
        with pytest.raises(ValidationError):
            HomeostasisReport(
                timestamp=datetime.now(),
                overall_state=AllostasisState.HOMEOSTASIS,
                feedback_loops_healthy=-1,
                feedback_loops_deviating=0,
                active_corrections=0,
                positive_feedback_risks=0,
                average_allostatic_load=0.0,
            )

    def test_average_allostatic_load_negative(self):
        with pytest.raises(ValidationError):
            HomeostasisReport(
                timestamp=datetime.now(),
                overall_state=AllostasisState.HOMEOSTASIS,
                feedback_loops_healthy=0,
                feedback_loops_deviating=0,
                active_corrections=0,
                positive_feedback_risks=0,
                average_allostatic_load=-1.0,
            )

    def test_all_ge_zero_fields(self):
        """All ge=0 fields should reject negative values."""
        base = {
            "timestamp": datetime.now(),
            "overall_state": AllostasisState.HOMEOSTASIS,
            "feedback_loops_healthy": 0,
            "feedback_loops_deviating": 0,
            "active_corrections": 0,
            "positive_feedback_risks": 0,
            "average_allostatic_load": 0.0,
        }
        for field in [
            "feedback_loops_healthy",
            "feedback_loops_deviating",
            "active_corrections",
            "positive_feedback_risks",
        ]:
            bad = {**base, field: -1}
            with pytest.raises(ValidationError):
                HomeostasisReport(**bad)


class TestRedundancyStatus:
    def test_valid(self):
        r = RedundancyStatus(
            service="ICU",
            status="N+2",
            available=4,
            minimum_required=2,
            buffer=2,
        )
        assert r.buffer == 2


class TestFallbackInfo:
    def test_valid(self):
        f = FallbackInfo(
            scenario=FallbackScenario.HOLIDAY_SKELETON,
            description="Holiday skeleton crew",
            is_active=False,
            is_precomputed=True,
            assignments_count=10,
            coverage_rate=0.8,
            services_reduced=["education", "research"],
            assumptions=["50% faculty available"],
            activation_count=0,
        )
        assert f.scenario == FallbackScenario.HOLIDAY_SKELETON


class TestCrisisResponse:
    def test_valid(self):
        r = CrisisResponse(
            crisis_mode=True,
            severity=CrisisSeverity.SEVERE,
            actions_taken=["Activated fallback"],
            load_shedding_level=LoadSheddingLevel.RED,
            recovery_plan=["Resume normal ops"],
        )
        assert r.crisis_mode is True

    def test_optional_fields(self):
        r = CrisisResponse(
            crisis_mode=False,
            actions_taken=[],
            load_shedding_level=LoadSheddingLevel.NORMAL,
        )
        assert r.severity is None
        assert r.recovery_plan is None


class TestSuccessResponse:
    def test_default_success(self):
        r = SuccessResponse(message="Operation completed")
        assert r.success is True

    def test_override_success(self):
        r = SuccessResponse(success=False, message="Operation failed")
        assert r.success is False


# ===========================================================================
# Response Schema Tests - Tier 2
# ===========================================================================


class TestSetpointInfo:
    def test_valid(self):
        s = SetpointInfo(
            name="coverage_rate",
            description="Target coverage rate",
            target_value=0.95,
            tolerance=0.05,
            unit="ratio",
            is_critical=True,
        )
        assert s.target_value == 0.95


class TestCentralityScore:
    def test_valid(self):
        c = CentralityScore(
            faculty_id=uuid4(),
            faculty_name="Dr. Test",
            centrality_score=0.85,
            services_covered=5,
            unique_coverage_slots=3,
            replacement_difficulty=0.9,
            risk_level="critical",
        )
        assert c.centrality_score == 0.85


class TestEquilibriumShiftResponse:
    def test_valid(self):
        r = EquilibriumShiftResponse(
            id=uuid4(),
            calculated_at=datetime.now(),
            original_capacity=100.0,
            original_demand=80.0,
            original_coverage_rate=0.95,
            total_capacity_impact=-20.0,
            total_demand_impact=10.0,
            total_compensation=15.0,
            compensation_efficiency=0.75,
            new_capacity=80.0,
            new_demand=90.0,
            new_coverage_rate=0.89,
            sustainable_capacity=85.0,
            compensation_debt=5.0,
            daily_debt_rate=0.5,
            burnout_risk=0.3,
            days_until_exhaustion=60,
            equilibrium_state=EquilibriumState.STRESSED,
            is_sustainable=False,
        )
        assert r.equilibrium_state == EquilibriumState.STRESSED


class TestTier2StatusResponse:
    def test_valid(self):
        r = Tier2StatusResponse(
            generated_at=datetime.now(),
            homeostasis_state=AllostasisState.HOMEOSTASIS,
            feedback_loops_healthy=4,
            feedback_loops_deviating=0,
            average_allostatic_load=20.0,
            positive_feedback_risks=0,
            total_zones=5,
            zones_healthy=4,
            zones_critical=1,
            containment_active=False,
            containment_level=ContainmentLevel.NONE,
            equilibrium_state=EquilibriumState.STABLE,
            current_coverage_rate=0.95,
            compensation_debt=0.0,
            sustainability_score=0.9,
            tier2_status="healthy",
            recommendations=[],
        )
        assert r.tier2_status == "healthy"


# ===========================================================================
# Response Schema Tests - Tier 3
# ===========================================================================


class TestCognitiveSessionResponse:
    def test_valid(self):
        r = CognitiveSessionResponse(
            session_id=uuid4(),
            user_id=uuid4(),
            started_at=datetime.now(),
            ended_at=None,
            max_decisions_before_break=10,
            current_state=CognitiveState.FRESH,
            decisions_count=0,
            total_cognitive_cost=0.0,
            should_take_break=False,
        )
        assert r.current_state == CognitiveState.FRESH


class TestDecisionResponse:
    def test_valid(self):
        r = DecisionResponse(
            decision_id=uuid4(),
            category=DecisionCategory.SWAP,
            complexity=DecisionComplexity.MODERATE,
            description="Approve swap between faculty A and B?",
            options=["Approve", "Deny", "Defer"],
            recommended_option="Approve",
            has_safe_default=True,
            is_urgent=False,
            estimated_cognitive_cost=3.5,
        )
        assert len(r.options) == 3


class TestFacultyCentralityResponse:
    def test_valid(self):
        r = FacultyCentralityResponse(
            faculty_id=uuid4(),
            faculty_name="Dr. Critical",
            composite_score=0.92,
            risk_level=HubRiskLevel.CATASTROPHIC,
            is_hub=True,
            degree_centrality=0.85,
            betweenness_centrality=0.90,
            services_covered=8,
            unique_services=3,
            replacement_difficulty=0.95,
        )
        assert r.risk_level == HubRiskLevel.CATASTROPHIC


class TestHubProfileResponse:
    def test_valid(self):
        r = HubProfileResponse(
            faculty_id=uuid4(),
            faculty_name="Dr. Hub",
            risk_level=HubRiskLevel.CRITICAL,
            unique_skills=["ICU", "OR"],
            high_demand_skills=["ICU"],
            protection_status=HubProtectionStatus.PROTECTED,
            protection_measures=["Backup assigned"],
            backup_faculty=[uuid4()],
            risk_factors=["Single point of failure for OR"],
            mitigation_actions=["Cross-train Dr. B"],
        )
        assert r.protection_status == HubProtectionStatus.PROTECTED


class TestTier3StatusResponse:
    def test_valid(self):
        r = Tier3StatusResponse(
            generated_at=datetime.now(),
            pending_decisions=3,
            urgent_decisions=1,
            estimated_cognitive_cost=8.5,
            can_auto_decide=2,
            total_trails=100,
            active_trails=85,
            average_strength=0.6,
            popular_slots=["Monday AM"],
            unpopular_slots=["Friday PM"],
            total_hubs=5,
            catastrophic_hubs=1,
            critical_hubs=2,
            active_protection_plans=3,
            pending_cross_training=4,
            tier3_status="warning",
            issues=["1 catastrophic hub detected"],
            recommendations=["Activate cross-training"],
        )
        assert r.tier3_status == "warning"


# ===========================================================================
# Response Schema Tests - SOC / Circuit Breaker
# ===========================================================================


class TestCriticalSlowingDownResponse:
    def test_valid(self):
        r = CriticalSlowingDownResponse(
            id=uuid4(),
            calculated_at=datetime.now(),
            days_analyzed=60,
            data_quality="excellent",
            is_critical=True,
            warning_level=SOCWarningLevel.ORANGE,
            confidence=0.85,
            signals_triggered=2,
            avalanche_risk_score=0.72,
        )
        assert r.signals_triggered == 2

    def test_confidence_boundaries(self):
        r = CriticalSlowingDownResponse(
            id=uuid4(),
            calculated_at=datetime.now(),
            days_analyzed=30,
            data_quality="good",
            is_critical=False,
            warning_level=SOCWarningLevel.GREEN,
            confidence=0.0,
            signals_triggered=0,
            avalanche_risk_score=0.0,
        )
        assert r.confidence == 0.0

    def test_confidence_above_one(self):
        with pytest.raises(ValidationError):
            CriticalSlowingDownResponse(
                id=uuid4(),
                calculated_at=datetime.now(),
                days_analyzed=30,
                data_quality="good",
                is_critical=False,
                warning_level=SOCWarningLevel.GREEN,
                confidence=1.1,
                signals_triggered=0,
                avalanche_risk_score=0.0,
            )

    def test_signals_triggered_max(self):
        r = CriticalSlowingDownResponse(
            id=uuid4(),
            calculated_at=datetime.now(),
            days_analyzed=60,
            data_quality="excellent",
            is_critical=True,
            warning_level=SOCWarningLevel.RED,
            confidence=0.95,
            signals_triggered=3,
            avalanche_risk_score=0.95,
        )
        assert r.signals_triggered == 3

    def test_signals_triggered_above_max(self):
        with pytest.raises(ValidationError):
            CriticalSlowingDownResponse(
                id=uuid4(),
                calculated_at=datetime.now(),
                days_analyzed=60,
                data_quality="excellent",
                is_critical=True,
                warning_level=SOCWarningLevel.RED,
                confidence=0.95,
                signals_triggered=4,
                avalanche_risk_score=0.95,
            )

    def test_avalanche_risk_boundaries(self):
        # Min
        r = CriticalSlowingDownResponse(
            id=uuid4(),
            calculated_at=datetime.now(),
            days_analyzed=30,
            data_quality="fair",
            is_critical=False,
            warning_level=SOCWarningLevel.GREEN,
            confidence=0.5,
            signals_triggered=0,
            avalanche_risk_score=0.0,
        )
        assert r.avalanche_risk_score == 0.0

        # Above max
        with pytest.raises(ValidationError):
            CriticalSlowingDownResponse(
                id=uuid4(),
                calculated_at=datetime.now(),
                days_analyzed=30,
                data_quality="fair",
                is_critical=False,
                warning_level=SOCWarningLevel.GREEN,
                confidence=0.5,
                signals_triggered=0,
                avalanche_risk_score=1.1,
            )

    def test_defaults_for_optional_fields(self):
        r = CriticalSlowingDownResponse(
            id=uuid4(),
            calculated_at=datetime.now(),
            days_analyzed=30,
            data_quality="good",
            is_critical=False,
            warning_level=SOCWarningLevel.GREEN,
            confidence=0.5,
            signals_triggered=0,
            avalanche_risk_score=0.1,
        )
        assert r.relaxation_time_hours is None
        assert r.variance_current is None
        assert r.autocorrelation_ac1 is None
        assert r.estimated_days_to_critical is None
        assert r.recommendations == []
        assert r.immediate_actions == []
        assert r.watch_items == []
        assert r.relaxation_time_increasing is False
        assert r.variance_increasing is False
        assert r.autocorrelation_increasing is False


class TestCircuitBreakerInfo:
    def test_valid(self):
        r = CircuitBreakerInfo(
            name="schedule_generator",
            state=CircuitBreakerState.CLOSED,
            failure_rate=0.02,
            success_rate=0.98,
            total_requests=100,
            successful_requests=98,
            failed_requests=2,
            rejected_requests=0,
            consecutive_failures=0,
            consecutive_successes=50,
        )
        assert r.opened_at is None
        assert r.recent_transitions == []


class TestAllBreakersStatusResponse:
    def test_valid(self):
        r = AllBreakersStatusResponse(
            total_breakers=3,
            closed_breakers=2,
            open_breakers=1,
            half_open_breakers=0,
            open_breaker_names=["swap_executor"],
            half_open_breaker_names=[],
            breakers=[],
            overall_health="degraded",
            recommendations=["Investigate swap executor failures"],
            checked_at=datetime.now(),
        )
        assert r.open_breakers == 1


class TestDefenseLevelResponse:
    def test_valid(self):
        r = DefenseLevelResponse(
            level=DefenseLevel.CONTROL,
            level_number=2,
            description="Active monitoring and adjustments",
            recommended_actions=["Monitor trends"],
            escalation_threshold=0.85,
        )
        assert r.level_number == 2

    def test_level_number_boundaries(self):
        r = DefenseLevelResponse(
            level=DefenseLevel.PREVENTION,
            level_number=1,
            description="Prevention",
            recommended_actions=[],
            escalation_threshold=0.9,
        )
        assert r.level_number == 1

        r = DefenseLevelResponse(
            level=DefenseLevel.EMERGENCY,
            level_number=5,
            description="Emergency",
            recommended_actions=[],
            escalation_threshold=0.5,
        )
        assert r.level_number == 5

    def test_level_number_out_of_range(self):
        with pytest.raises(ValidationError):
            DefenseLevelResponse(
                level=DefenseLevel.PREVENTION,
                level_number=0,
                description="Bad",
                recommended_actions=[],
                escalation_threshold=0.9,
            )

        with pytest.raises(ValidationError):
            DefenseLevelResponse(
                level=DefenseLevel.EMERGENCY,
                level_number=6,
                description="Bad",
                recommended_actions=[],
                escalation_threshold=0.5,
            )


class TestMTFComplianceResponse:
    def test_valid(self):
        r = MTFComplianceResponse(
            drrs_category="C1",
            mission_capability="Fully Mission Capable",
            personnel_rating="P1",
            capability_rating="S1",
            executive_summary="All systems nominal",
            iron_dome_status="green",
            severity="healthy",
        )
        assert r.deficiencies == []
        assert r.mfrs_generated == 0
        assert r.circuit_breaker is None


class TestBurnoutRtResponse:
    def test_valid(self):
        r = BurnoutRtResponse(
            rt=0.8,
            status="declining",
            secondary_cases=2,
            time_window_days=28,
            interventions=["Reduce on-call frequency"],
        )
        assert r.confidence_interval is None


class TestStateTransitionInfo:
    def test_valid(self):
        t = StateTransitionInfo(
            from_state="closed",
            to_state="open",
            timestamp=datetime.now(),
            reason="Failure threshold exceeded",
        )
        assert t.from_state == "closed"


# ===========================================================================
# Additional Simple Response Schema Tests
# ===========================================================================


class TestSimpleResponseSchemas:
    """Tests for straightforward response schemas without complex validators."""

    def test_fallback_list_response(self):
        r = FallbackListResponse(fallbacks=[], active_count=0)
        assert r.active_count == 0

    def test_load_shedding_status(self):
        r = LoadSheddingStatus(
            level=LoadSheddingLevel.NORMAL,
            activities_suspended=[],
            activities_protected=["patient_care"],
            capacity_available=100.0,
            capacity_demand=75.0,
        )
        assert r.level == LoadSheddingLevel.NORMAL

    def test_fallback_activation_response(self):
        r = FallbackActivationResponse(
            success=True,
            scenario=FallbackScenario.HOLIDAY_SKELETON,
            assignments_count=10,
            coverage_rate=0.8,
            services_reduced=["education"],
            message="Holiday fallback activated",
        )
        assert r.success is True

    def test_vulnerability_summary(self):
        v = VulnerabilitySummary(
            n1_pass=True,
            n2_pass=False,
            phase_transition_risk="medium",
            critical_faculty_count=3,
            fatal_pair_count=1,
            recommended_actions=["Cross-train faculty"],
        )
        assert v.fatal_pair_count == 1

    def test_event_history_item(self):
        e = EventHistoryItem(
            id=uuid4(),
            timestamp=datetime.now(),
            event_type="crisis_activation",
            severity="critical",
            reason="Mass casualty event",
            triggered_by="admin",
        )
        assert e.event_type == "crisis_activation"

    def test_event_history_response(self):
        r = EventHistoryResponse(items=[], total=0, page=1, page_size=20)
        assert r.page == 1

    def test_health_check_history_item(self):
        h = HealthCheckHistoryItem(
            id=uuid4(),
            timestamp=datetime.now(),
            overall_status=OverallStatus.HEALTHY,
            utilization_rate=0.6,
            utilization_level=UtilizationLevel.GREEN,
            defense_level=DefenseLevel.PREVENTION,
            n1_pass=True,
            n2_pass=True,
            crisis_mode=False,
        )
        assert h.overall_status == OverallStatus.HEALTHY

    def test_health_check_history_response(self):
        r = HealthCheckHistoryResponse(items=[], total=0, page=1, page_size=20)
        assert r.total == 0

    def test_zone_faculty_assignment(self):
        z = ZoneFacultyAssignment(
            faculty_id=uuid4(),
            faculty_name="Dr. Test",
            role="attending",
            is_available=True,
            assigned_at=datetime.now(),
        )
        assert z.is_available is True

    def test_zone_response(self):
        z = ZoneResponse(
            id=uuid4(),
            name="ICU",
            zone_type=ZoneType.INPATIENT,
            description="Intensive Care",
            services=["icu_coverage"],
            minimum_coverage=2,
            optimal_coverage=3,
            priority=1,
            status=ZoneStatus.GREEN,
            containment_level=ContainmentLevel.NONE,
            borrowing_limit=1,
            lending_limit=1,
            is_active=True,
        )
        assert z.zone_type == ZoneType.INPATIENT

    def test_borrowing_response(self):
        r = BorrowingResponse(
            id=uuid4(),
            requesting_zone_id=uuid4(),
            lending_zone_id=uuid4(),
            faculty_id=uuid4(),
            priority=BorrowingPriority.HIGH,
            reason="Critical coverage need",
            status="approved",
            requested_at=datetime.now(),
            approved_at=datetime.now(),
            approved_by="admin",
        )
        assert r.status == "approved"

    def test_zone_incident_response(self):
        r = ZoneIncidentResponse(
            id=uuid4(),
            zone_id=uuid4(),
            incident_type="staffing_gap",
            description="Unexpected absence",
            severity="moderate",
            started_at=datetime.now(),
            faculty_affected=["Dr. A"],
            services_affected=["ICU"],
            capacity_lost=0.2,
            resolved_at=None,
            containment_successful=False,
        )
        assert r.containment_successful is False

    def test_blast_radius_report_response(self):
        r = BlastRadiusReportResponse(
            generated_at=datetime.now(),
            total_zones=5,
            zones_healthy=3,
            zones_degraded=1,
            zones_critical=1,
            containment_active=True,
            containment_level=ContainmentLevel.MODERATE,
            zones_isolated=1,
            active_borrowing_requests=2,
            pending_borrowing_requests=1,
            zone_reports=[],
            recommendations=["Monitor critical zone"],
        )
        assert r.containment_active is True

    def test_stress_response(self):
        r = StressResponse(
            id=uuid4(),
            stress_type=StressType.FACULTY_LOSS,
            description="Faculty on leave",
            magnitude=0.5,
            duration_days=14,
            capacity_impact=-0.2,
            demand_impact=0.0,
            applied_at=datetime.now(),
            is_active=True,
        )
        assert r.is_active is True

    def test_compensation_response(self):
        r = CompensationResponse(
            id=uuid4(),
            stress_id=uuid4(),
            compensation_type=CompensationType.OVERTIME,
            description="Authorized overtime",
            compensation_magnitude=0.5,
            effectiveness=0.8,
            initiated_at=datetime.now(),
            is_active=True,
        )
        assert r.compensation_type == CompensationType.OVERTIME

    def test_collective_preference_response(self):
        r = CollectivePreferenceResponse(
            found=False,
            slot_type=None,
            total_preference_strength=None,
            total_avoidance_strength=None,
            net_preference=None,
            faculty_count=None,
            confidence=None,
            is_popular=None,
            is_unpopular=None,
        )
        assert r.total_preference_strength is None

    def test_stigmergy_status_response(self):
        r = StigmergyStatusResponse(
            timestamp=datetime.now(),
            total_trails=100,
            active_trails=85,
            trails_by_type={"preference": 50, "avoidance": 35},
            average_strength=0.6,
            average_age_days=30.0,
            evaporation_debt_hours=12.0,
            popular_slots=["Monday AM"],
            unpopular_slots=["Friday PM"],
            strong_swap_pairs=10,
            recommendations=[],
        )
        assert r.active_trails == 85

    def test_hub_distribution_response(self):
        r = HubDistributionResponse(
            generated_at=datetime.now(),
            total_faculty=30,
            total_hubs=5,
            catastrophic_hubs=1,
            critical_hubs=2,
            high_risk_hubs=2,
            hub_concentration=0.17,
            single_points_of_failure=1,
            average_hub_score=0.65,
            services_with_single_provider=["OR Night Call"],
            services_with_dual_coverage=["ICU"],
            well_covered_services=["Clinic"],
            recommendations=["Cross-train for OR Night Call"],
        )
        assert r.single_points_of_failure == 1

    def test_soc_metrics_history_response(self):
        r = SOCMetricsHistoryResponse(
            metrics=[],
            total_count=0,
            date_range_start=date(2026, 1, 1),
            date_range_end=date(2026, 1, 31),
        )
        assert r.trend_summary == {}

    def test_breaker_health_metrics(self):
        m = BreakerHealthMetrics(
            total_requests=1000,
            total_failures=20,
            total_rejections=5,
            overall_failure_rate=0.02,
            breakers_above_threshold=1,
            average_failure_rate=0.015,
            max_failure_rate=0.05,
            unhealthiest_breaker="swap_executor",
        )
        assert m.overall_failure_rate == 0.02

    def test_breaker_health_response(self):
        m = BreakerHealthMetrics(
            total_requests=100,
            total_failures=5,
            total_rejections=0,
            overall_failure_rate=0.05,
            breakers_above_threshold=0,
            average_failure_rate=0.05,
            max_failure_rate=0.05,
        )
        r = BreakerHealthResponse(
            total_breakers=3,
            metrics=m,
            breakers_needing_attention=[],
            trend_analysis="Stable",
            severity=BreakerSeverity.HEALTHY,
            recommendations=[],
            analyzed_at=datetime.now(),
        )
        assert r.severity == BreakerSeverity.HEALTHY

    def test_containment_set_response(self):
        r = ContainmentSetResponse(
            success=True,
            containment_level="strict",
            reason="Multiple zone failures",
        )
        assert r.success is True

    def test_stress_resolve_response(self):
        r = StressResolveResponse(
            success=True,
            stress_id=str(uuid4()),
            message="Stress resolved",
        )
        assert r.success is True

    def test_cognitive_session_start_response(self):
        r = CognitiveSessionStartResponse(
            session_id=uuid4(),
            user_id="admin",
            started_at="2026-01-15T10:00:00",
            max_decisions_before_break=10,
            current_state="fresh",
        )
        assert r.current_state == "fresh"

    def test_cognitive_session_end_response(self):
        r = CognitiveSessionEndResponse(
            success=True,
            session_id=str(uuid4()),
            message="Session ended",
        )
        assert r.success is True

    def test_decision_queue_response(self):
        r = DecisionQueueResponse(
            total_pending=5,
            by_complexity={"moderate": 3, "simple": 2},
            by_category={"swap": 3, "assignment": 2},
            urgent_count=1,
            can_auto_decide=2,
            oldest_pending=None,
            estimated_cognitive_cost=8.0,
            recommendations=[],
        )
        assert r.total_pending == 5

    def test_cognitive_load_analysis(self):
        r = CognitiveLoadAnalysis(
            total_score=6.5,
            grade="B",
            grade_description="Good",
            factors={"complexity": 3.0, "volume": 3.5},
            recommendations=["Batch similar decisions"],
        )
        assert r.grade == "B"

    def test_preference_trail_response(self):
        r = PreferenceTrailResponse(
            trail_id=uuid4(),
            faculty_id=uuid4(),
            trail_type=TrailType.PREFERENCE,
            strength=0.7,
            strength_category=TrailStrength.STRONG,
            slot_type="Monday AM",
            reinforcement_count=5,
            age_days=30.0,
        )
        assert r.strength_category == TrailStrength.STRONG

    def test_cross_training_recommendation_response(self):
        r = CrossTrainingRecommendationResponse(
            id=uuid4(),
            skill="ICU Night Call",
            priority=CrossTrainingPriority.URGENT,
            reason="Single point of failure",
            current_holders=[uuid4()],
            recommended_trainees=[uuid4(), uuid4()],
            estimated_training_hours=40,
            risk_reduction=0.6,
            status="pending",
        )
        assert r.priority == CrossTrainingPriority.URGENT

    def test_fallback_deactivation_response(self):
        r = FallbackDeactivationResponse(success=True, message="Fallback deactivated")
        assert r.success is True

    def test_utilization_threshold_response(self):
        r = UtilizationThresholdResponse(
            utilization_rate=0.75,
            level=UtilizationLevel.YELLOW,
            above_threshold=False,
            buffer_remaining=0.05,
            wait_time_multiplier=3.0,
            message="Warning: approaching threshold",
            recommendations=["Monitor closely"],
        )
        assert r.above_threshold is False

    def test_stigmergy_patterns_response(self):
        r = StigmergyPatternsResponse()
        assert r.patterns == []
        assert r.total == 0

    def test_hub_status_response(self):
        r = HubStatusResponse(
            total_hubs=5,
            catastrophic_count=1,
            critical_count=2,
            high_risk_count=2,
            active_protection_plans=3,
            pending_cross_training=4,
        )
        assert r.recommendations == []

    def test_zone_list_response(self):
        r = ZoneListResponse(zones=[], total=0)
        assert r.total == 0

    def test_zone_assignment_response(self):
        r = ZoneAssignmentResponse(success=True, message="Assigned")
        assert r.success is True
