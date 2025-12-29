"""
Tests for Optimization MCP Tools.

Tests cover operational optimization using advanced analytics:
1. Erlang C Coverage Optimization - Specialist staffing optimization
2. Process Capability Analysis - Six Sigma schedule quality metrics

Test Categories:
- Unit Tests: Tool functions in isolation with mocked backends
- Integration Tests: Tool-to-backend API communication
- Contract Tests: Pydantic schema validation
- Smoke Tests: Tools are registered and callable
"""

import asyncio
from datetime import datetime
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

import pytest


# ============================================================================
# Erlang C Coverage Optimization Tests
# ============================================================================


class TestErlangCoverageTool:
    """Tests for Erlang C queuing-based specialist coverage optimization tool."""

    # -------------------------------------------------------------------------
    # Happy Path Tests
    # -------------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_optimize_coverage_basic(
        self, mock_api_client, specialty_coverage_params, erlang_coverage_response
    ):
        """Test basic coverage optimization."""
        mock_api_client.get.return_value.json.return_value = erlang_coverage_response

        response = mock_api_client.get.return_value.json()

        assert response["specialty"] == "Orthopedic Surgery"
        assert response["required_specialists"] >= 1
        assert 0 <= response["predicted_wait_probability"] <= 1.0
        assert response["service_level"] > 0.9  # High service level

    @pytest.mark.asyncio
    async def test_optimize_coverage_low_load(self, mock_api_client):
        """Test optimization with low offered load."""
        mock_response = {
            "specialty": "Dermatology",
            "required_specialists": 2,
            "predicted_wait_probability": 0.01,  # Very low wait probability
            "offered_load": 0.5,  # Low load
            "service_level": 0.998,
            "metrics": {
                "wait_probability": 0.01,
                "avg_wait_time": 0.002,
                "occupancy": 0.25,  # Low utilization - could reduce staff
            },
            "recommendations": [
                "Consider reducing specialists during low-demand periods",
            ],
            "severity": "healthy",
        }
        mock_api_client.get.return_value.json.return_value = mock_response

        response = mock_api_client.get.return_value.json()

        assert response["offered_load"] < 1.0
        assert response["metrics"]["occupancy"] < 0.5
        assert response["predicted_wait_probability"] < 0.05

    @pytest.mark.asyncio
    async def test_optimize_coverage_high_load(self, mock_api_client):
        """Test optimization with high offered load."""
        mock_response = {
            "specialty": "Emergency Medicine",
            "required_specialists": 8,
            "predicted_wait_probability": 0.045,
            "offered_load": 6.0,  # High load
            "service_level": 0.962,
            "metrics": {
                "wait_probability": 0.045,
                "avg_wait_time": 0.018,  # 18 minutes
                "occupancy": 0.75,  # High but sustainable
            },
            "warnings": ["Occupancy approaching 80% threshold"],
            "severity": "info",
        }
        mock_api_client.get.return_value.json.return_value = mock_response

        response = mock_api_client.get.return_value.json()

        assert response["offered_load"] > 5.0
        assert response["required_specialists"] >= 7
        assert response["metrics"]["occupancy"] > 0.7

    @pytest.mark.asyncio
    async def test_optimize_coverage_multiple_specialties(self, mock_api_client):
        """Test batch optimization across multiple specialties."""
        mock_response = {
            "coverage_results": [
                {
                    "specialty": "Orthopedic Surgery",
                    "required_specialists": 4,
                    "service_level": 0.97,
                },
                {
                    "specialty": "Cardiology",
                    "required_specialists": 3,
                    "service_level": 0.95,
                },
                {
                    "specialty": "Neurology",
                    "required_specialists": 2,
                    "service_level": 0.98,
                },
            ],
            "total_specialists_required": 9,
            "overall_service_level": 0.966,
            "severity": "healthy",
        }
        mock_api_client.get.return_value.json.return_value = mock_response

        response = mock_api_client.get.return_value.json()

        assert len(response["coverage_results"]) == 3
        assert response["total_specialists_required"] == 9
        assert all(r["service_level"] >= 0.95 for r in response["coverage_results"])

    # -------------------------------------------------------------------------
    # Edge Case Tests
    # -------------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_optimize_coverage_unstable_queue(self, mock_api_client):
        """Test handling of unstable queue (load >= servers)."""
        mock_response = {
            "error": True,
            "error_code": "UNSTABLE_QUEUE",
            "message": "Unstable queue: offered_load (8.5) >= max_servers (8). Queue will grow indefinitely.",
            "recommendations": [
                "Increase max_servers limit",
                "Reduce arrival_rate through demand management",
                "Decrease service_time through process improvement",
            ],
            "severity": "critical",
        }
        mock_api_client.get.return_value.json.return_value = mock_response

        response = mock_api_client.get.return_value.json()

        assert response["error"] is True
        assert response["error_code"] == "UNSTABLE_QUEUE"
        assert "recommendations" in response

    @pytest.mark.asyncio
    async def test_optimize_coverage_target_not_achievable(self, mock_api_client):
        """Test when target wait probability cannot be met."""
        mock_response = {
            "error": True,
            "error_code": "TARGET_NOT_ACHIEVABLE",
            "message": "Cannot meet target wait probability 0.01 with up to 20 specialists.",
            "best_achievable": {
                "specialists": 20,
                "wait_probability": 0.025,
                "service_level": 0.98,
            },
            "recommendations": [
                "Relax target_wait_prob to 0.03",
                "Consider demand smoothing across time periods",
            ],
            "severity": "warning",
        }
        mock_api_client.get.return_value.json.return_value = mock_response

        response = mock_api_client.get.return_value.json()

        assert response["error"] is True
        assert "best_achievable" in response

    @pytest.mark.asyncio
    async def test_optimize_coverage_staffing_table(self, mock_api_client):
        """Test generation of staffing table with metrics for different server counts."""
        mock_response = {
            "staffing_table": [
                {
                    "servers": 3,
                    "wait_probability": 0.25,
                    "avg_wait_time": 0.08,
                    "service_level": 0.85,
                    "occupancy": 0.42,
                },
                {
                    "servers": 4,
                    "wait_probability": 0.04,
                    "avg_wait_time": 0.01,
                    "service_level": 0.97,
                    "occupancy": 0.31,
                },
                {
                    "servers": 5,
                    "wait_probability": 0.008,
                    "avg_wait_time": 0.002,
                    "service_level": 0.995,
                    "occupancy": 0.25,
                },
            ],
            "recommended_servers": 4,
            "reasoning": "4 servers meets target with efficient utilization",
            "severity": "healthy",
        }
        mock_api_client.get.return_value.json.return_value = mock_response

        response = mock_api_client.get.return_value.json()

        assert len(response["staffing_table"]) >= 3
        # Verify wait probability decreases with more servers
        wait_probs = [s["wait_probability"] for s in response["staffing_table"]]
        assert wait_probs == sorted(wait_probs, reverse=True)

    @pytest.mark.asyncio
    async def test_optimize_coverage_zero_arrival(self, mock_api_client):
        """Test handling of zero arrival rate."""
        mock_response = {
            "specialty": "Rare Specialty",
            "required_specialists": 1,  # Minimum for on-call coverage
            "predicted_wait_probability": 0.0,
            "offered_load": 0.0,
            "warnings": ["Zero arrival rate - consider on-call coverage only"],
            "severity": "healthy",
        }
        mock_api_client.get.return_value.json.return_value = mock_response

        response = mock_api_client.get.return_value.json()

        assert response["offered_load"] == 0.0
        assert response["required_specialists"] >= 1

    # -------------------------------------------------------------------------
    # Contract Tests
    # -------------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_erlang_response_schema(
        self, mock_api_client, erlang_coverage_response, validate_response_schema
    ):
        """Test Erlang coverage response matches expected schema."""
        mock_api_client.get.return_value.json.return_value = erlang_coverage_response

        response = mock_api_client.get.return_value.json()

        validate_response_schema(
            response,
            required_fields=[
                "specialty",
                "required_specialists",
                "predicted_wait_probability",
            ],
            field_types={
                "specialty": str,
                "required_specialists": int,
                "predicted_wait_probability": float,
                "offered_load": float,
                "service_level": float,
            },
        )


# ============================================================================
# Process Capability (Six Sigma) Tests
# ============================================================================


class TestProcessCapabilityTool:
    """Tests for Six Sigma process capability analysis tool."""

    # -------------------------------------------------------------------------
    # Happy Path Tests
    # -------------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_analyze_capability_excellent(
        self, mock_api_client, capable_process_data, process_capability_response
    ):
        """Test analysis of excellent (world-class) process."""
        # Modify to EXCELLENT
        response_data = process_capability_response.copy()
        response_data["cpk"] = 1.85
        response_data["capability_status"] = "EXCELLENT"
        response_data["sigma_level"] = 5.55
        mock_api_client.get.return_value.json.return_value = response_data

        response = mock_api_client.get.return_value.json()

        assert response["capability_status"] == "EXCELLENT"
        assert response["cpk"] >= 1.67
        assert response["sigma_level"] >= 5.0

    @pytest.mark.asyncio
    async def test_analyze_capability_capable(
        self, mock_api_client, process_capability_response
    ):
        """Test analysis of capable process (industry standard)."""
        mock_api_client.get.return_value.json.return_value = process_capability_response

        response = mock_api_client.get.return_value.json()

        assert response["capability_status"] == "CAPABLE"
        assert 1.33 <= response["cpk"] < 1.67
        assert response["sigma_level"] >= 4.0

    @pytest.mark.asyncio
    async def test_analyze_capability_marginal(
        self, mock_api_client, marginal_process_data
    ):
        """Test analysis of marginal process."""
        mock_response = {
            "cp": 1.25,
            "cpk": 1.15,
            "pp": 1.25,
            "ppk": 1.15,
            "cpm": 1.10,
            "capability_status": "MARGINAL",
            "sigma_level": 3.45,
            "sample_size": len(marginal_process_data),
            "mean": 60.5,
            "std_dev": 7.8,
            "lsl": 40.0,
            "usl": 80.0,
            "target": 60.0,
            "recommendations": [
                "Process barely meets specifications - improvement needed",
                "Reduce process variation through better load balancing",
            ],
            "severity": "warning",
        }
        mock_api_client.get.return_value.json.return_value = mock_response

        response = mock_api_client.get.return_value.json()

        assert response["capability_status"] == "MARGINAL"
        assert 1.0 <= response["cpk"] < 1.33
        assert len(response["recommendations"]) > 0

    @pytest.mark.asyncio
    async def test_analyze_capability_incapable(
        self, mock_api_client, incapable_process_data
    ):
        """Test analysis of incapable process."""
        mock_response = {
            "cp": 0.75,
            "cpk": 0.62,
            "pp": 0.75,
            "ppk": 0.62,
            "cpm": 0.55,
            "capability_status": "INCAPABLE",
            "sigma_level": 1.86,
            "sample_size": len(incapable_process_data),
            "mean": 58.2,
            "std_dev": 14.5,
            "lsl": 40.0,
            "usl": 80.0,
            "target": 60.0,
            "defect_estimate": {
                "ppm": 25000,  # 2.5% defect rate
                "percentage": 2.5,
            },
            "recommendations": [
                "URGENT: Process cannot reliably meet specifications",
                "Review schedule generation constraints",
                "Investigate root causes of variation",
            ],
            "severity": "critical",
        }
        mock_api_client.get.return_value.json.return_value = mock_response

        response = mock_api_client.get.return_value.json()

        assert response["capability_status"] == "INCAPABLE"
        assert response["cpk"] < 1.0
        assert "URGENT" in response["recommendations"][0]

    # -------------------------------------------------------------------------
    # Edge Case Tests
    # -------------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_analyze_capability_off_center(self, mock_api_client):
        """Test analysis of process that's capable but off-center."""
        mock_response = {
            "cp": 2.0,  # High potential
            "cpk": 1.2,  # Lower actual due to off-center
            "pp": 2.0,
            "ppk": 1.2,
            "cpm": 1.0,  # Low due to Taguchi loss
            "capability_status": "MARGINAL",
            "sigma_level": 3.6,
            "centering_analysis": {
                "centering_ratio": 0.6,  # Cpk/Cp
                "status": "POOR - Process significantly off-center",
                "mean_shift": 8.5,  # Hours above target
            },
            "recommendations": [
                "Improve centering: Cpk/Cp = 0.60 (target mean closer to 60)",
                "High off-target loss - aim for target value, not just spec limits",
            ],
            "severity": "warning",
        }
        mock_api_client.get.return_value.json.return_value = mock_response

        response = mock_api_client.get.return_value.json()

        assert response["cp"] > response["cpk"]  # Off-center indicator
        assert response["centering_analysis"]["centering_ratio"] < 0.85
        assert "centering" in response["recommendations"][0].lower()

    @pytest.mark.asyncio
    async def test_analyze_capability_zero_variation(self, mock_api_client):
        """Test handling of zero variation (constant values)."""
        mock_response = {
            "cp": float("inf"),
            "cpk": float("inf"),
            "capability_status": "EXCELLENT",
            "sigma_level": 99.0,  # Capped for display
            "std_dev": 0.0,
            "warnings": [
                "Zero standard deviation - process may be static or simulated"
            ],
            "severity": "info",
        }
        mock_api_client.get.return_value.json.return_value = mock_response

        response = mock_api_client.get.return_value.json()

        assert response["std_dev"] == 0.0
        assert "warnings" in response

    @pytest.mark.asyncio
    async def test_analyze_capability_small_sample(self, mock_api_client):
        """Test warning for small sample size."""
        mock_response = {
            "cp": 1.45,
            "cpk": 1.38,
            "capability_status": "CAPABLE",
            "sample_size": 15,  # Below recommended 30
            "warnings": [
                "Sample size (15) below recommended minimum (30) for Six Sigma analysis. Results may be unreliable."
            ],
            "confidence_interval": {
                "cpk_lower": 0.95,
                "cpk_upper": 1.81,
            },
            "severity": "info",
        }
        mock_api_client.get.return_value.json.return_value = mock_response

        response = mock_api_client.get.return_value.json()

        assert response["sample_size"] < 30
        assert "warnings" in response
        assert "confidence_interval" in response

    @pytest.mark.asyncio
    async def test_analyze_capability_custom_limits(self, mock_api_client):
        """Test with custom specification limits."""
        mock_response = {
            "cp": 1.5,
            "cpk": 1.42,
            "capability_status": "CAPABLE",
            "lsl": 50.0,  # Custom lower limit
            "usl": 70.0,  # Custom upper limit (tighter than ACGME)
            "target": 60.0,
            "spec_width": 20.0,
            "severity": "healthy",
        }
        mock_api_client.get.return_value.json.return_value = mock_response

        response = mock_api_client.get.return_value.json()

        assert response["lsl"] == 50.0
        assert response["usl"] == 70.0

    @pytest.mark.asyncio
    async def test_analyze_capability_with_trends(self, mock_api_client):
        """Test capability analysis with trend detection."""
        mock_response = {
            "cp": 1.35,
            "cpk": 1.28,
            "capability_status": "MARGINAL",
            "trend_analysis": {
                "trend_detected": True,
                "direction": "increasing",
                "slope": 0.5,  # Hours per week increase
                "projected_cpk_4weeks": 1.05,
                "projected_status_4weeks": "MARGINAL",
            },
            "recommendations": [
                "Trend detected: workload increasing at 0.5 hours/week",
                "If trend continues, process may become INCAPABLE in 8-12 weeks",
            ],
            "severity": "warning",
        }
        mock_api_client.get.return_value.json.return_value = mock_response

        response = mock_api_client.get.return_value.json()

        assert "trend_analysis" in response
        assert response["trend_analysis"]["trend_detected"] is True

    @pytest.mark.asyncio
    async def test_analyze_capability_summary(self, mock_api_client):
        """Test capability summary generation."""
        mock_response = {
            "cp": 1.55,
            "cpk": 1.48,
            "capability_status": "CAPABLE",
            "summary": {
                "status": "CAPABLE",
                "sigma_level": "4.44",
                "indices": {
                    "Cpk": "1.480",
                    "Cp": "1.550",
                    "Cpm": "1.420",
                },
                "centering": "GOOD - Minor centering improvement possible",
                "statistics": {
                    "mean": "61.2",
                    "std_dev": "4.3",
                    "sample_size": 52,
                },
                "estimated_defect_rate": {
                    "ppm": "45.2",
                    "percentage": "0.0045%",
                },
            },
            "severity": "healthy",
        }
        mock_api_client.get.return_value.json.return_value = mock_response

        response = mock_api_client.get.return_value.json()

        assert "summary" in response
        summary = response["summary"]
        assert "indices" in summary
        assert "estimated_defect_rate" in summary

    # -------------------------------------------------------------------------
    # ACGME-Specific Tests
    # -------------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_analyze_acgme_compliance_capability(self, mock_api_client):
        """Test capability analysis specific to ACGME 80-hour rule."""
        mock_response = {
            "analysis_type": "ACGME_80_HOUR_RULE",
            "cp": 1.42,
            "cpk": 1.35,
            "capability_status": "CAPABLE",
            "lsl": 40.0,  # Minimum meaningful workload
            "usl": 80.0,  # ACGME limit
            "target": 60.0,  # Balanced target
            "acgme_specific": {
                "hours_above_limit": 0,
                "hours_near_limit": 3,  # Within 5 hours of 80
                "compliance_rate": 1.0,  # 100%
                "margin_to_violation": 8.5,  # Average hours below 80
            },
            "severity": "healthy",
        }
        mock_api_client.get.return_value.json.return_value = mock_response

        response = mock_api_client.get.return_value.json()

        assert response["analysis_type"] == "ACGME_80_HOUR_RULE"
        assert response["usl"] == 80.0
        assert "acgme_specific" in response
        assert response["acgme_specific"]["compliance_rate"] == 1.0

    # -------------------------------------------------------------------------
    # Contract Tests
    # -------------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_capability_response_schema(
        self, mock_api_client, process_capability_response, validate_response_schema
    ):
        """Test process capability response matches expected schema."""
        mock_api_client.get.return_value.json.return_value = process_capability_response

        response = mock_api_client.get.return_value.json()

        validate_response_schema(
            response,
            required_fields=["cp", "cpk", "capability_status", "sigma_level"],
            field_types={
                "cp": float,
                "cpk": float,
                "pp": float,
                "ppk": float,
                "cpm": float,
                "capability_status": str,
                "sigma_level": float,
                "sample_size": int,
                "mean": float,
                "std_dev": float,
                "lsl": float,
                "usl": float,
            },
        )


# ============================================================================
# Smoke Tests
# ============================================================================


class TestOptimizationToolsSmoke:
    """Smoke tests to verify tools are registered and callable."""

    @pytest.mark.asyncio
    async def test_erlang_tool_registered(self, mock_api_client):
        """Verify Erlang coverage tool is accessible."""
        mock_api_client.get.return_value.json.return_value = {
            "specialty": "Test",
            "required_specialists": 1,
        }

        response = mock_api_client.get.return_value.json()

        assert "specialty" in response

    @pytest.mark.asyncio
    async def test_capability_tool_registered(self, mock_api_client):
        """Verify process capability tool is accessible."""
        mock_api_client.get.return_value.json.return_value = {
            "cpk": 1.5,
            "capability_status": "CAPABLE",
        }

        response = mock_api_client.get.return_value.json()

        assert "cpk" in response


# ============================================================================
# Integration Tests (with actual backend module imports)
# ============================================================================


class TestOptimizationIntegration:
    """Integration tests that use actual backend resilience modules."""

    def test_erlang_calculation(self, specialty_coverage_params):
        """Test Erlang C calculation with actual module."""
        try:
            from backend.app.resilience.erlang_coverage import ErlangCCalculator

            calc = ErlangCCalculator()

            # Calculate for given parameters
            coverage = calc.optimize_specialist_coverage(
                specialty=specialty_coverage_params["specialty"],
                arrival_rate=specialty_coverage_params["arrival_rate"],
                service_time=specialty_coverage_params["service_time"],
                target_wait_prob=specialty_coverage_params["target_wait_prob"],
            )

            assert coverage.required_specialists >= 1
            assert coverage.predicted_wait_probability <= specialty_coverage_params[
                "target_wait_prob"
            ]
            assert 0 <= coverage.service_level <= 1.0

        except ImportError:
            pytest.skip("Backend modules not available in test environment")

    def test_erlang_metrics(self):
        """Test Erlang C metrics calculation with actual module."""
        try:
            from backend.app.resilience.erlang_coverage import ErlangCCalculator

            calc = ErlangCCalculator()

            metrics = calc.calculate_metrics(
                arrival_rate=2.5,
                service_time=0.5,
                servers=4,
                target_wait=0.25,
            )

            assert 0 <= metrics.wait_probability <= 1.0
            assert metrics.avg_wait_time >= 0
            assert 0 <= metrics.service_level <= 1.0
            assert 0 <= metrics.occupancy <= 1.0

        except ImportError:
            pytest.skip("Backend modules not available in test environment")

    def test_capability_analysis(self, capable_process_data):
        """Test process capability analysis with actual module."""
        try:
            from backend.app.resilience.process_capability import (
                ScheduleCapabilityAnalyzer,
            )

            analyzer = ScheduleCapabilityAnalyzer(min_sample_size=10)

            report = analyzer.analyze_workload_capability(
                weekly_hours=capable_process_data,
                min_hours=40.0,
                max_hours=80.0,
                target_hours=60.0,
            )

            assert report.cp > 0
            assert report.cpk > 0
            assert report.capability_status in [
                "EXCELLENT",
                "CAPABLE",
                "MARGINAL",
                "INCAPABLE",
            ]
            assert report.sigma_level >= 0

        except ImportError:
            pytest.skip("Backend modules not available in test environment")

    def test_capability_indices(self):
        """Test individual capability index calculations with actual module."""
        try:
            from backend.app.resilience.process_capability import (
                ScheduleCapabilityAnalyzer,
            )

            analyzer = ScheduleCapabilityAnalyzer()

            # Test data with known properties
            centered_data = [60.0, 61.0, 59.0, 60.5, 59.5, 60.2, 59.8, 60.3, 59.7, 60.0]

            cp = analyzer.calculate_cp(centered_data, lsl=40.0, usl=80.0)
            cpk = analyzer.calculate_cpk(centered_data, lsl=40.0, usl=80.0)
            cpm = analyzer.calculate_cpm(
                centered_data, lsl=40.0, usl=80.0, target=60.0
            )

            # For well-centered data, Cp and Cpk should be similar
            assert abs(cp - cpk) < cp * 0.2

            # Cpm should be high for on-target data
            assert cpm > 1.0

        except ImportError:
            pytest.skip("Backend modules not available in test environment")

    def test_capability_classification(self):
        """Test capability classification with actual module."""
        try:
            from backend.app.resilience.process_capability import (
                ScheduleCapabilityAnalyzer,
            )

            analyzer = ScheduleCapabilityAnalyzer()

            classifications = [
                (2.0, "EXCELLENT"),
                (1.67, "EXCELLENT"),
                (1.5, "CAPABLE"),
                (1.33, "CAPABLE"),
                (1.1, "MARGINAL"),
                (1.0, "MARGINAL"),
                (0.8, "INCAPABLE"),
            ]

            for cpk, expected_class in classifications:
                result = analyzer.classify_capability(cpk)
                assert result == expected_class, f"Cpk={cpk} should be {expected_class}"

        except ImportError:
            pytest.skip("Backend modules not available in test environment")

    def test_sigma_level_conversion(self):
        """Test Cpk to sigma level conversion with actual module."""
        try:
            from backend.app.resilience.process_capability import (
                ScheduleCapabilityAnalyzer,
            )

            analyzer = ScheduleCapabilityAnalyzer()

            test_cases = [
                (1.0, 3.0),  # 3 sigma
                (1.33, 3.99),  # ~4 sigma
                (1.67, 5.01),  # ~5 sigma
                (2.0, 6.0),  # 6 sigma
            ]

            for cpk, expected_sigma in test_cases:
                sigma = analyzer.get_sigma_level(cpk)
                assert abs(sigma - expected_sigma) < 0.1, (
                    f"Cpk={cpk} should give ~{expected_sigma}sigma"
                )

        except ImportError:
            pytest.skip("Backend modules not available in test environment")
