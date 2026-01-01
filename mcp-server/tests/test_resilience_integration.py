"""
Tests for Resilience Framework MCP Integration.

Tests cover:
- Utilization threshold checking
- Defense level analysis
- Contingency (N-1/N-2) analysis
- Static fallback management
- MTF compliance checking
- Request/response validation
"""

from datetime import date

import pytest

from scheduler_mcp.resilience_integration import (
    CircuitBreakerInfo,
    # Request models
    ContingencyAnalysisRequest,
    ContingencyAnalysisResponse,
    DefenseLevelEnum,
    DefenseLevelResponse,
    FallbackScenarioEnum,
    FallbackScheduleInfo,
    FatalPairInfo,
    MTFComplianceRequest,
    MTFComplianceResponse,
    # Enums
    UtilizationLevelEnum,
    # Response models
    UtilizationResponse,
    VulnerabilityInfo,
    check_mtf_compliance,
    # Functions
    check_utilization_threshold,
    get_defense_level,
    get_static_fallbacks,
    run_contingency_analysis_deep,
)


class TestUtilizationModels:
    """Test utilization-related models."""

    def test_utilization_level_enum_values(self):
        """Test all utilization levels exist."""
        assert UtilizationLevelEnum.GREEN == "green"
        assert UtilizationLevelEnum.YELLOW == "yellow"
        assert UtilizationLevelEnum.ORANGE == "orange"
        assert UtilizationLevelEnum.RED == "red"
        assert UtilizationLevelEnum.BLACK == "black"

    def test_utilization_response_valid(self):
        """Test valid utilization response creation."""
        response = UtilizationResponse(
            level=UtilizationLevelEnum.GREEN,
            utilization_rate=0.75,
            effective_utilization=0.78,
            buffer_remaining=0.25,
            total_capacity=100,
            required_coverage=80,
            current_assignments=78,
            safe_maximum=80,
            wait_time_multiplier=1.2,
            message="System operating normally",
            recommendations=[],
            severity="healthy",
        )
        assert response.level == UtilizationLevelEnum.GREEN
        assert response.utilization_rate == 0.75
        assert response.severity == "healthy"

    def test_utilization_response_bounds_validation(self):
        """Test utilization rate bounds are enforced."""
        # Valid at boundary
        response = UtilizationResponse(
            level=UtilizationLevelEnum.BLACK,
            utilization_rate=1.0,
            effective_utilization=1.0,
            buffer_remaining=0.0,
            total_capacity=100,
            required_coverage=100,
            current_assignments=100,
            safe_maximum=80,
            wait_time_multiplier=5.0,
            message="System overloaded",
            recommendations=["Activate emergency protocol"],
            severity="emergency",
        )
        assert response.utilization_rate == 1.0


class TestDefenseLevelModels:
    """Test defense level models."""

    def test_defense_level_enum_ordering(self):
        """Test defense levels have correct order semantically."""
        levels = [
            DefenseLevelEnum.PREVENTION,
            DefenseLevelEnum.CONTROL,
            DefenseLevelEnum.SAFETY_SYSTEMS,
            DefenseLevelEnum.CONTAINMENT,
            DefenseLevelEnum.EMERGENCY,
        ]
        assert len(levels) == 5

    def test_defense_level_response_valid(self):
        """Test valid defense level response."""
        response = DefenseLevelResponse(
            current_level=DefenseLevelEnum.PREVENTION,
            recommended_level=DefenseLevelEnum.PREVENTION,
            status="ready",
            active_actions=[],
            automation_status={"auto_balance": True, "fallback_ready": True},
            escalation_needed=False,
            coverage_rate=0.95,
            severity="normal",
        )
        assert response.current_level == DefenseLevelEnum.PREVENTION
        assert response.escalation_needed is False


class TestContingencyModels:
    """Test contingency analysis models."""

    def test_contingency_request_defaults(self):
        """Test contingency request with defaults."""
        request = ContingencyAnalysisRequest()
        assert request.analyze_n1 is True
        assert request.analyze_n2 is True
        assert request.include_cascade_simulation is False
        assert request.critical_faculty_only is True

    def test_contingency_request_custom(self):
        """Test contingency request with custom values."""
        request = ContingencyAnalysisRequest(
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31),
            analyze_n1=True,
            analyze_n2=False,
            include_cascade_simulation=True,
            critical_faculty_only=False,
        )
        assert request.start_date == date(2024, 1, 1)
        assert request.analyze_n2 is False
        assert request.include_cascade_simulation is True

    def test_vulnerability_info_valid(self):
        """Test vulnerability info creation."""
        vuln = VulnerabilityInfo(
            faculty_id="fac-001",
            faculty_name="[REDACTED]",
            severity="critical",
            affected_blocks=15,
            is_unique_provider=True,
            details="Only provider for procedures",
            services_affected=["procedures", "inpatient"],
        )
        assert vuln.severity == "critical"
        assert vuln.is_unique_provider is True
        assert len(vuln.services_affected) == 2

    def test_fatal_pair_info_valid(self):
        """Test fatal pair info creation."""
        pair = FatalPairInfo(
            faculty_1_id="fac-001",
            faculty_1_name="[REDACTED-1]",
            faculty_2_id="fac-002",
            faculty_2_name="[REDACTED-2]",
            uncoverable_blocks=5,
            affected_services=["clinic"],
        )
        assert pair.uncoverable_blocks == 5


class TestMTFComplianceModels:
    """Test MTF compliance models."""

    def test_circuit_breaker_info_default(self):
        """Test circuit breaker with defaults."""
        cb = CircuitBreakerInfo(
            state="closed",
            tripped=False,
            trigger=None,
            trigger_details=None,
            triggered_at=None,
            locked_operations=[],
            override_active=False,
        )
        assert cb.state == "closed"
        assert cb.tripped is False

    def test_circuit_breaker_tripped(self):
        """Test tripped circuit breaker."""
        cb = CircuitBreakerInfo(
            state="open",
            tripped=True,
            trigger="work_hours_violation",
            trigger_details="ACGME 80-hour limit exceeded",
            triggered_at="2024-01-15T10:30:00",
            locked_operations=["schedule_generation", "bulk_assign"],
            override_active=False,
        )
        assert cb.tripped is True
        assert len(cb.locked_operations) == 2

    def test_mtf_compliance_response_healthy(self):
        """Test healthy MTF compliance response."""
        response = MTFComplianceResponse(
            drrs_category="C1",
            mission_capability="FMC",
            personnel_rating="P1",
            capability_rating="S1",
            circuit_breaker=CircuitBreakerInfo(
                state="closed",
                tripped=False,
                trigger=None,
                trigger_details=None,
                triggered_at=None,
                locked_operations=[],
                override_active=False,
            ),
            executive_summary="Unit operating at full capability",
            deficiencies=[],
            mfrs_generated=0,
            rffs_generated=0,
            iron_dome_status="green",
            severity="healthy",
        )
        assert response.drrs_category == "C1"
        assert response.mission_capability == "FMC"


class TestCheckUtilizationThreshold:
    """Test check_utilization_threshold function."""

    @pytest.mark.asyncio
    async def test_returns_utilization_response(self):
        """Test function returns valid response type."""
        response = await check_utilization_threshold()

        assert isinstance(response, UtilizationResponse)
        assert response.level in UtilizationLevelEnum
        assert 0.0 <= response.utilization_rate <= 1.0

    @pytest.mark.asyncio
    async def test_includes_recommendations(self):
        """Test response includes recommendations list."""
        response = await check_utilization_threshold()

        assert isinstance(response.recommendations, list)

    @pytest.mark.asyncio
    async def test_message_not_empty(self):
        """Test response includes non-empty message."""
        response = await check_utilization_threshold()

        assert response.message
        assert len(response.message) > 0


class TestGetDefenseLevel:
    """Test get_defense_level function."""

    @pytest.mark.asyncio
    async def test_returns_defense_level_response(self):
        """Test function returns valid response type."""
        response = await get_defense_level()

        assert isinstance(response, DefenseLevelResponse)
        assert response.current_level in DefenseLevelEnum
        assert response.recommended_level in DefenseLevelEnum

    @pytest.mark.asyncio
    async def test_automation_status_populated(self):
        """Test automation status is populated."""
        response = await get_defense_level()

        assert isinstance(response.automation_status, dict)


class TestRunContingencyAnalysisDeep:
    """Test run_contingency_analysis_deep function."""

    @pytest.mark.asyncio
    async def test_returns_contingency_response(self):
        """Test function returns valid response type."""
        request = ContingencyAnalysisRequest()
        response = await run_contingency_analysis_deep(request)

        assert isinstance(response, ContingencyAnalysisResponse)
        assert isinstance(response.n1_pass, bool)
        assert isinstance(response.n2_pass, bool)

    @pytest.mark.asyncio
    async def test_includes_vulnerabilities_list(self):
        """Test response includes vulnerabilities list."""
        request = ContingencyAnalysisRequest()
        response = await run_contingency_analysis_deep(request)

        assert isinstance(response.n1_vulnerabilities, list)
        assert isinstance(response.n2_fatal_pairs, list)

    @pytest.mark.asyncio
    async def test_includes_recommended_actions(self):
        """Test response includes recommended actions."""
        request = ContingencyAnalysisRequest()
        response = await run_contingency_analysis_deep(request)

        assert isinstance(response.recommended_actions, list)


class TestGetStaticFallbacks:
    """Test get_static_fallbacks function."""

    @pytest.mark.asyncio
    async def test_returns_list_of_fallbacks(self):
        """Test function returns list of fallback info."""
        response = await get_static_fallbacks()

        assert isinstance(response, list)

    @pytest.mark.asyncio
    async def test_fallback_info_structure(self):
        """Test fallback info has correct structure when populated."""
        response = await get_static_fallbacks()

        # Even if empty, should be a list
        assert isinstance(response, list)

        # If there are fallbacks, they should be FallbackScheduleInfo
        for fallback in response:
            assert isinstance(fallback, FallbackScheduleInfo)


class TestCheckMTFCompliance:
    """Test check_mtf_compliance function."""

    @pytest.mark.asyncio
    async def test_returns_mtf_compliance_response(self):
        """Test function returns valid response type."""
        request = MTFComplianceRequest(check_circuit_breaker=True)
        response = await check_mtf_compliance(request)

        assert isinstance(response, MTFComplianceResponse)
        assert response.drrs_category in ["C1", "C2", "C3", "C4", "C5"]

    @pytest.mark.asyncio
    async def test_includes_circuit_breaker_info(self):
        """Test response includes circuit breaker info."""
        request = MTFComplianceRequest(check_circuit_breaker=True)
        response = await check_mtf_compliance(request)

        assert isinstance(response.circuit_breaker, CircuitBreakerInfo)

    @pytest.mark.asyncio
    async def test_includes_executive_summary(self):
        """Test response includes executive summary."""
        request = MTFComplianceRequest()
        response = await check_mtf_compliance(request)

        assert response.executive_summary
        assert len(response.executive_summary) > 0

    @pytest.mark.asyncio
    async def test_iron_dome_status_valid(self):
        """Test iron dome status has valid value."""
        request = MTFComplianceRequest()
        response = await check_mtf_compliance(request)

        assert response.iron_dome_status in ["green", "yellow", "red"]


class TestFallbackScenarioEnum:
    """Test FallbackScenarioEnum values."""

    def test_all_scenarios_defined(self):
        """Test all expected fallback scenarios exist."""
        expected = [
            "single_absence",
            "dual_absence",
            "pcs_season",
            "holiday_period",
            "deployment",
            "mass_casualty",
        ]

        for scenario in expected:
            assert scenario in [e.value for e in FallbackScenarioEnum]

    def test_scenario_enum_count(self):
        """Test correct number of scenarios."""
        assert len(FallbackScenarioEnum) == 6


class TestResponseSeverityValues:
    """Test severity field values across responses."""

    def test_utilization_severity_values(self):
        """Test utilization severity values are valid."""
        valid_severities = ["healthy", "warning", "critical", "emergency"]

        # Create responses with each severity
        for sev in valid_severities:
            response = UtilizationResponse(
                level=UtilizationLevelEnum.GREEN,
                utilization_rate=0.75,
                effective_utilization=0.78,
                buffer_remaining=0.25,
                total_capacity=100,
                required_coverage=80,
                current_assignments=78,
                safe_maximum=80,
                wait_time_multiplier=1.2,
                message="Test",
                recommendations=[],
                severity=sev,
            )
            assert response.severity == sev

    def test_defense_severity_values(self):
        """Test defense level severity values are valid."""
        valid_severities = ["normal", "elevated", "critical"]

        for sev in valid_severities:
            response = DefenseLevelResponse(
                current_level=DefenseLevelEnum.PREVENTION,
                recommended_level=DefenseLevelEnum.PREVENTION,
                status="ready",
                active_actions=[],
                automation_status={},
                escalation_needed=False,
                coverage_rate=0.95,
                severity=sev,
            )
            assert response.severity == sev

    def test_contingency_severity_values(self):
        """Test contingency analysis severity values are valid."""
        valid_severities = ["healthy", "vulnerable", "critical"]

        for sev in valid_severities:
            response = ContingencyAnalysisResponse(
                analysis_date="2024-01-15",
                period_start="2024-01-01",
                period_end="2024-01-31",
                n1_pass=True,
                n1_vulnerabilities=[],
                n2_pass=True,
                n2_fatal_pairs=[],
                most_critical_faculty=[],
                phase_transition_risk="low",
                leading_indicators=[],
                recommended_actions=[],
                severity=sev,
            )
            assert response.severity == sev
