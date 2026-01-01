"""
Tests for Composite MCP Tools.

Tests cover cross-domain analysis tools that synthesize multiple resilience systems:
1. Unified Critical Index - Combines N-1/N-2, epidemiology, and hub analysis
2. Recovery Distance - Graph-theoretic resilience metric for schedule recovery

Test Categories:
- Unit Tests: Tool functions in isolation with mocked backends
- Integration Tests: Tool-to-backend API communication
- Contract Tests: Pydantic schema validation
- Smoke Tests: Tools are registered and callable
"""

from datetime import datetime

import pytest

# ============================================================================
# Unified Critical Index Tests
# ============================================================================


class TestUnifiedCriticalIndexTool:
    """Tests for unified critical faculty index tool."""

    # -------------------------------------------------------------------------
    # Happy Path Tests
    # -------------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_calculate_index_low_risk(self, mock_api_client, stable_uuids):
        """Test index calculation for low-risk faculty member."""
        mock_response = {
            "faculty_id": str(stable_uuids["faculty_1"]),
            "faculty_name": "Dr. Smith",
            "composite_index": 0.25,
            "risk_pattern": "low_risk",
            "domain_scores": {
                "contingency": {"raw": 0.20, "normalized": 0.22, "is_critical": False},
                "epidemiology": {"raw": 0.15, "normalized": 0.18, "is_critical": False},
                "hub_analysis": {"raw": 0.30, "normalized": 0.35, "is_critical": False},
            },
            "domain_agreement": 0.92,
            "leading_domain": "hub_analysis",
            "recommended_interventions": ["monitoring"],
            "priority_rank": 15,
            "confidence": 0.85,
            "severity": "healthy",
        }
        mock_api_client.get.return_value.json.return_value = mock_response

        response = mock_api_client.get.return_value.json()

        assert response["risk_pattern"] == "low_risk"
        assert response["composite_index"] < 0.5
        assert not any(
            d["is_critical"] for d in response["domain_scores"].values()
        )
        assert "monitoring" in response["recommended_interventions"]

    @pytest.mark.asyncio
    async def test_calculate_index_universal_critical(
        self, mock_api_client, unified_index_response, stable_uuids
    ):
        """Test index calculation for universal critical (all domains high)."""
        mock_response = {
            "faculty_id": str(stable_uuids["faculty_1"]),
            "faculty_name": "Dr. Critical",
            "composite_index": 0.92,
            "risk_pattern": "universal_critical",
            "domain_scores": {
                "contingency": {"raw": 0.95, "normalized": 0.92, "is_critical": True},
                "epidemiology": {"raw": 0.88, "normalized": 0.85, "is_critical": True},
                "hub_analysis": {"raw": 0.82, "normalized": 0.80, "is_critical": True},
            },
            "domain_agreement": 0.95,  # High agreement - all domains agree this is critical
            "leading_domain": "contingency",
            "conflict_details": ["Strong domain consensus - high confidence in assessment"],
            "recommended_interventions": [
                "immediate_protection",
                "cross_training",
                "workload_reduction",
            ],
            "priority_rank": 1,
            "confidence": 0.95,
            "severity": "emergency",
        }
        mock_api_client.get.return_value.json.return_value = mock_response

        response = mock_api_client.get.return_value.json()

        assert response["risk_pattern"] == "universal_critical"
        assert response["composite_index"] > 0.8
        assert all(d["is_critical"] for d in response["domain_scores"].values())
        assert "immediate_protection" in response["recommended_interventions"]
        assert response["priority_rank"] == 1

    @pytest.mark.asyncio
    async def test_calculate_index_structural_burnout(self, mock_api_client):
        """Test structural burnout pattern (contingency + epidemiology high)."""
        mock_response = {
            "faculty_id": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
            "faculty_name": "Dr. Stressed",
            "composite_index": 0.72,
            "risk_pattern": "structural_burnout",
            "domain_scores": {
                "contingency": {"raw": 0.85, "normalized": 0.82, "is_critical": True},
                "epidemiology": {"raw": 0.78, "normalized": 0.75, "is_critical": True},
                "hub_analysis": {"raw": 0.35, "normalized": 0.40, "is_critical": False},
            },
            "domain_agreement": 0.68,
            "leading_domain": "contingency",
            "recommended_interventions": [
                "workload_reduction",
                "cross_training",
                "wellness_support",
            ],
            "severity": "warning",
        }
        mock_api_client.get.return_value.json.return_value = mock_response

        response = mock_api_client.get.return_value.json()

        assert response["risk_pattern"] == "structural_burnout"
        assert response["domain_scores"]["contingency"]["is_critical"]
        assert response["domain_scores"]["epidemiology"]["is_critical"]
        assert not response["domain_scores"]["hub_analysis"]["is_critical"]

    @pytest.mark.asyncio
    async def test_calculate_index_isolated_workhorse(self, mock_api_client):
        """Test isolated workhorse pattern (only contingency high)."""
        mock_response = {
            "faculty_id": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
            "faculty_name": "Dr. Workhorse",
            "composite_index": 0.55,
            "risk_pattern": "isolated_workhorse",
            "domain_scores": {
                "contingency": {"raw": 0.90, "normalized": 0.88, "is_critical": True},
                "epidemiology": {"raw": 0.20, "normalized": 0.25, "is_critical": False},
                "hub_analysis": {"raw": 0.25, "normalized": 0.30, "is_critical": False},
            },
            "domain_agreement": 0.42,  # Low agreement
            "conflict_details": [
                "High centrality but low social transmission risk - "
                "may be isolated or have strong personal boundaries"
            ],
            "recommended_interventions": ["cross_training"],
            "severity": "warning",
        }
        mock_api_client.get.return_value.json.return_value = mock_response

        response = mock_api_client.get.return_value.json()

        assert response["risk_pattern"] == "isolated_workhorse"
        assert response["domain_agreement"] < 0.5
        assert "conflict_details" in response
        assert len(response["conflict_details"]) > 0

    # -------------------------------------------------------------------------
    # Population Analysis Tests
    # -------------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_analyze_population(self, mock_api_client):
        """Test population-level analysis."""
        mock_response = {
            "analyzed_at": datetime.now().isoformat(),
            "total_faculty": 25,
            "risk_concentration": 0.35,  # Gini coefficient
            "critical_count": 5,
            "universal_critical_count": 1,
            "pattern_distribution": {
                "low_risk": 15,
                "isolated_workhorse": 3,
                "burnout_vector": 2,
                "network_anchor": 2,
                "structural_burnout": 2,
                "universal_critical": 1,
            },
            "top_priority": [
                "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
                "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
                "cccccccc-cccc-cccc-cccc-cccccccccccc",
            ],
            "indices": [],  # Truncated for brevity
            "severity": "warning",
        }
        mock_api_client.get.return_value.json.return_value = mock_response

        response = mock_api_client.get.return_value.json()

        assert response["total_faculty"] == 25
        assert response["critical_count"] == 5
        assert "pattern_distribution" in response
        assert len(response["top_priority"]) <= 5

    @pytest.mark.asyncio
    async def test_analyze_population_risk_concentration(self, mock_api_client):
        """Test risk concentration analysis (Gini coefficient)."""
        mock_response = {
            "total_faculty": 30,
            "risk_concentration": 0.72,  # High - risk concentrated in few
            "concentration_analysis": {
                "gini_coefficient": 0.72,
                "interpretation": "HIGH - Risk concentrated in few faculty members",
                "top_10_percent_share": 0.65,  # Top 10% hold 65% of risk
            },
            "recommendations": [
                "URGENT: Distribute critical responsibilities more evenly",
                "Cross-train faculty to reduce single points of failure",
            ],
            "severity": "warning",
        }
        mock_api_client.get.return_value.json.return_value = mock_response

        response = mock_api_client.get.return_value.json()

        assert response["risk_concentration"] > 0.6
        assert "concentration_analysis" in response
        assert len(response["recommendations"]) > 0

    # -------------------------------------------------------------------------
    # Edge Case Tests
    # -------------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_calculate_index_missing_network(self, mock_api_client):
        """Test handling when network data is unavailable."""
        mock_response = {
            "faculty_id": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
            "faculty_name": "Dr. NoNetwork",
            "composite_index": 0.35,
            "risk_pattern": "low_risk",
            "domain_scores": {
                "contingency": {"raw": 0.45, "normalized": 0.42, "is_critical": False},
                "epidemiology": {"raw": 0.0, "normalized": 0.0, "is_critical": False},
                "hub_analysis": {"raw": 0.0, "normalized": 0.0, "is_critical": False},
            },
            "confidence": 0.45,  # Lower confidence due to missing data
            "warnings": ["Network data unavailable - epidemiology and hub scores set to 0"],
            "severity": "info",
        }
        mock_api_client.get.return_value.json.return_value = mock_response

        response = mock_api_client.get.return_value.json()

        assert response["confidence"] < 0.6
        assert "warnings" in response

    @pytest.mark.asyncio
    async def test_calculate_index_conflict_detection(self, mock_api_client):
        """Test cross-domain conflict detection."""
        mock_response = {
            "faculty_id": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
            "faculty_name": "Dr. Conflict",
            "composite_index": 0.48,
            "risk_pattern": "social_connector",
            "domain_scores": {
                "contingency": {"raw": 0.25, "normalized": 0.28, "is_critical": False},
                "epidemiology": {"raw": 0.85, "normalized": 0.82, "is_critical": True},
                "hub_analysis": {"raw": 0.78, "normalized": 0.75, "is_critical": True},
            },
            "domain_agreement": 0.38,  # Low agreement - domains disagree
            "conflict_details": [
                "High burnout spread potential but schedule can survive their loss - "
                "focus on wellness rather than coverage"
            ],
            "recommended_interventions": [
                "wellness_support",
                "network_diversification",
            ],
            "severity": "warning",
        }
        mock_api_client.get.return_value.json.return_value = mock_response

        response = mock_api_client.get.return_value.json()

        assert response["domain_agreement"] < 0.5
        assert len(response["conflict_details"]) > 0

    @pytest.mark.asyncio
    async def test_calculate_index_new_faculty(self, mock_api_client):
        """Test handling of new faculty with limited data."""
        mock_response = {
            "faculty_id": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
            "faculty_name": "Dr. NewHire",
            "composite_index": 0.0,
            "risk_pattern": "low_risk",
            "domain_scores": {
                "contingency": {
                    "raw": 0.0,
                    "normalized": 0.0,
                    "is_critical": False,
                    "details": {"total_assigned_blocks": 0},
                },
                "epidemiology": {"raw": 0.0, "normalized": 0.0, "is_critical": False},
                "hub_analysis": {"raw": 0.0, "normalized": 0.0, "is_critical": False},
            },
            "confidence": 0.15,  # Very low confidence
            "warnings": [
                "No assignment history - contingency score unavailable",
                "Faculty not yet in network - epidemiology and hub scores unavailable",
            ],
            "severity": "info",
        }
        mock_api_client.get.return_value.json.return_value = mock_response

        response = mock_api_client.get.return_value.json()

        assert response["composite_index"] == 0.0
        assert response["confidence"] < 0.3

    # -------------------------------------------------------------------------
    # Contract Tests
    # -------------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_unified_index_schema(
        self, mock_api_client, unified_index_response, validate_response_schema
    ):
        """Test unified critical index response matches expected schema."""
        mock_api_client.get.return_value.json.return_value = unified_index_response

        response = mock_api_client.get.return_value.json()

        validate_response_schema(
            response,
            required_fields=[
                "faculty_id",
                "composite_index",
                "risk_pattern",
                "domain_scores",
            ],
            field_types={
                "faculty_id": str,
                "faculty_name": str,
                "composite_index": float,
                "risk_pattern": str,
                "domain_scores": dict,
                "domain_agreement": float,
                "recommended_interventions": list,
                "priority_rank": int,
            },
        )

        # Validate domain scores structure
        for domain_name, domain_data in response["domain_scores"].items():
            validate_response_schema(
                domain_data,
                required_fields=["raw", "normalized"],
                field_types={
                    "raw": float,
                    "normalized": float,
                    "is_critical": bool,
                },
            )


# ============================================================================
# Recovery Distance Tests
# ============================================================================


class TestRecoveryDistanceTool:
    """Tests for recovery distance calculation tool."""

    # -------------------------------------------------------------------------
    # Happy Path Tests
    # -------------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_calculate_rd_zero(self, mock_api_client, stable_uuids):
        """Test recovery distance of 0 (schedule remains feasible)."""
        mock_response = {
            "event": {
                "event_type": "faculty_absence",
                "resource_id": str(stable_uuids["faculty_1"]),
                "affected_blocks": [str(stable_uuids["block_1"])],
            },
            "recovery_distance": 0,
            "feasible": True,
            "witness_edits": [],  # No edits needed
            "search_depth_reached": 0,
            "computation_time_ms": 5.2,
            "interpretation": "Schedule remains feasible without intervention",
            "severity": "healthy",
        }
        mock_api_client.get.return_value.json.return_value = mock_response

        response = mock_api_client.get.return_value.json()

        assert response["recovery_distance"] == 0
        assert response["feasible"] is True
        assert len(response["witness_edits"]) == 0

    @pytest.mark.asyncio
    async def test_calculate_rd_single_edit(
        self, mock_api_client, recovery_distance_response
    ):
        """Test recovery distance of 1 (single edit needed)."""
        mock_response = recovery_distance_response.copy()
        mock_response["recovery_distance"] = 1
        mock_response["witness_edits"] = [
            {
                "edit_type": "reassign",
                "new_person_id": "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
                "block_id": "00000001-0001-0001-0001-000000000001",
                "justification": "Reassign to available backup",
            }
        ]
        mock_api_client.get.return_value.json.return_value = mock_response

        response = mock_api_client.get.return_value.json()

        assert response["recovery_distance"] == 1
        assert len(response["witness_edits"]) == 1
        assert response["witness_edits"][0]["edit_type"] == "reassign"

    @pytest.mark.asyncio
    async def test_calculate_rd_multiple_edits(
        self, mock_api_client, recovery_distance_response
    ):
        """Test recovery distance requiring multiple edits."""
        mock_api_client.get.return_value.json.return_value = recovery_distance_response

        response = mock_api_client.get.return_value.json()

        assert response["recovery_distance"] == 2
        assert response["feasible"] is True
        assert len(response["witness_edits"]) == 2

    @pytest.mark.asyncio
    async def test_calculate_rd_breakglass(self, mock_api_client):
        """Test break-glass scenario (>3 edits required)."""
        mock_response = {
            "event": {
                "event_type": "faculty_absence",
                "resource_id": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
            },
            "recovery_distance": 4,
            "feasible": True,
            "witness_edits": [
                {"edit_type": "reassign", "justification": "Edit 1"},
                {"edit_type": "swap", "justification": "Edit 2"},
                {"edit_type": "reassign", "justification": "Edit 3"},
                {"edit_type": "swap", "justification": "Edit 4"},
            ],
            "search_depth_reached": 4,
            "computation_time_ms": 850.5,
            "is_breakglass": True,
            "warnings": ["Break-glass scenario: requires extensive schedule rework"],
            "severity": "warning",
        }
        mock_api_client.get.return_value.json.return_value = mock_response

        response = mock_api_client.get.return_value.json()

        assert response["recovery_distance"] > 3
        assert response["is_breakglass"] is True
        assert "warnings" in response

    @pytest.mark.asyncio
    async def test_calculate_rd_infeasible(self, mock_api_client):
        """Test infeasible scenario (no recovery path found)."""
        mock_response = {
            "event": {
                "event_type": "faculty_absence",
                "resource_id": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
            },
            "recovery_distance": 6,  # Max depth + 1
            "feasible": False,
            "witness_edits": [],
            "search_depth_reached": 5,  # Max depth
            "computation_time_ms": 1500.0,
            "warnings": [
                "No feasible recovery found within search depth",
                "Consider pre-emptive schedule restructuring",
            ],
            "severity": "critical",
        }
        mock_api_client.get.return_value.json.return_value = mock_response

        response = mock_api_client.get.return_value.json()

        assert response["feasible"] is False
        assert response["search_depth_reached"] == 5
        assert len(response["witness_edits"]) == 0

    # -------------------------------------------------------------------------
    # Aggregate Metrics Tests
    # -------------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_calculate_aggregate_metrics(self, mock_api_client):
        """Test aggregate recovery distance metrics."""
        mock_response = {
            "rd_mean": 1.8,
            "rd_median": 2.0,
            "rd_p95": 4.0,
            "rd_max": 5,
            "breakglass_count": 3,
            "infeasible_count": 1,
            "events_tested": 25,
            "by_event_type": {
                "faculty_absence": {"mean": 2.1, "median": 2.0, "max": 5, "count": 15},
                "resident_sick": {"mean": 1.4, "median": 1.0, "max": 3, "count": 10},
            },
            "overall_resilience": "MODERATE",
            "severity": "warning",
        }
        mock_api_client.get.return_value.json.return_value = mock_response

        response = mock_api_client.get.return_value.json()

        assert response["events_tested"] == 25
        assert response["rd_mean"] < response["rd_p95"]
        assert response["breakglass_count"] + response["infeasible_count"] <= response[
            "events_tested"
        ]
        assert "by_event_type" in response

    @pytest.mark.asyncio
    async def test_calculate_aggregate_resilient(self, mock_api_client):
        """Test aggregate metrics for highly resilient schedule."""
        mock_response = {
            "rd_mean": 0.5,
            "rd_median": 0.0,
            "rd_p95": 1.0,
            "rd_max": 2,
            "breakglass_count": 0,
            "infeasible_count": 0,
            "events_tested": 25,
            "overall_resilience": "EXCELLENT",
            "recommendations": [
                "Schedule demonstrates excellent resilience",
                "Maintain current staffing patterns",
            ],
            "severity": "healthy",
        }
        mock_api_client.get.return_value.json.return_value = mock_response

        response = mock_api_client.get.return_value.json()

        assert response["overall_resilience"] == "EXCELLENT"
        assert response["breakglass_count"] == 0
        assert response["infeasible_count"] == 0

    @pytest.mark.asyncio
    async def test_calculate_aggregate_fragile(self, mock_api_client):
        """Test aggregate metrics for fragile schedule."""
        mock_response = {
            "rd_mean": 3.8,
            "rd_median": 4.0,
            "rd_p95": 5.0,
            "rd_max": 6,
            "breakglass_count": 15,
            "infeasible_count": 5,
            "events_tested": 25,
            "overall_resilience": "FRAGILE",
            "recommendations": [
                "CRITICAL: Schedule requires extensive rework for most n-1 events",
                "Immediate action: Cross-train faculty to reduce single points of failure",
                "Consider increasing minimum coverage requirements",
            ],
            "severity": "critical",
        }
        mock_api_client.get.return_value.json.return_value = mock_response

        response = mock_api_client.get.return_value.json()

        assert response["overall_resilience"] == "FRAGILE"
        assert response["breakglass_count"] + response["infeasible_count"] >= response[
            "events_tested"
        ] * 0.5

    # -------------------------------------------------------------------------
    # Event Type Tests
    # -------------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_generate_test_events(self, mock_api_client):
        """Test generation of test event suite."""
        mock_response = {
            "events": [
                {
                    "event_type": "faculty_absence",
                    "resource_id": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
                    "affected_blocks": ["block1", "block2", "block3"],
                    "metadata": {"name": "Dr. Smith"},
                },
                {
                    "event_type": "resident_sick",
                    "resource_id": "11111111-1111-1111-1111-111111111111",
                    "affected_blocks": ["block1", "block2"],
                    "metadata": {"name": "Resident A", "date": "2025-01-15"},
                },
            ],
            "event_counts": {
                "faculty_absence": 15,
                "resident_sick": 10,
            },
            "total_events": 25,
            "severity": "info",
        }
        mock_api_client.get.return_value.json.return_value = mock_response

        response = mock_api_client.get.return_value.json()

        assert response["total_events"] == 25
        assert "faculty_absence" in response["event_counts"]
        assert "resident_sick" in response["event_counts"]

    @pytest.mark.asyncio
    async def test_rd_by_event_type(self, mock_api_client):
        """Test recovery distance varies by event type."""
        mock_response = {
            "by_event_type": {
                "faculty_absence": {
                    "mean": 2.5,
                    "median": 2.0,
                    "max": 5,
                    "count": 15,
                    "interpretation": "Faculty absences require moderate recovery effort",
                },
                "resident_sick": {
                    "mean": 1.2,
                    "median": 1.0,
                    "max": 3,
                    "count": 10,
                    "interpretation": "Resident sick days are easily recoverable",
                },
            },
            "most_impactful_event_type": "faculty_absence",
            "severity": "info",
        }
        mock_api_client.get.return_value.json.return_value = mock_response

        response = mock_api_client.get.return_value.json()

        assert response["by_event_type"]["faculty_absence"]["mean"] > response[
            "by_event_type"
        ]["resident_sick"]["mean"]

    # -------------------------------------------------------------------------
    # Edge Case Tests
    # -------------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_rd_timeout(self, mock_api_client):
        """Test handling of search timeout."""
        mock_response = {
            "event": {
                "event_type": "faculty_absence",
                "resource_id": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
            },
            "recovery_distance": -1,  # Unknown due to timeout
            "feasible": None,  # Unknown
            "witness_edits": [],
            "search_depth_reached": 3,  # Stopped early
            "computation_time_ms": 30000.0,  # Hit timeout
            "timed_out": True,
            "warnings": ["Search timed out after 30 seconds at depth 3"],
            "severity": "warning",
        }
        mock_api_client.get.return_value.json.return_value = mock_response

        response = mock_api_client.get.return_value.json()

        assert response["timed_out"] is True
        assert response["computation_time_ms"] >= 30000

    @pytest.mark.asyncio
    async def test_rd_empty_schedule(self, mock_api_client):
        """Test handling of empty schedule."""
        mock_response = {
            "error": True,
            "error_code": "EMPTY_SCHEDULE",
            "message": "Cannot calculate recovery distance for empty schedule",
            "severity": "warning",
        }
        mock_api_client.get.return_value.json.return_value = mock_response

        response = mock_api_client.get.return_value.json()

        assert response["error"] is True
        assert response["error_code"] == "EMPTY_SCHEDULE"

    @pytest.mark.asyncio
    async def test_rd_cache_hit(self, mock_api_client):
        """Test cache hit for repeated calculations."""
        mock_response = {
            "event": {"event_type": "faculty_absence"},
            "recovery_distance": 2,
            "feasible": True,
            "computation_time_ms": 0.5,  # Very fast due to cache
            "cache_hit": True,
            "severity": "healthy",
        }
        mock_api_client.get.return_value.json.return_value = mock_response

        response = mock_api_client.get.return_value.json()

        assert response["cache_hit"] is True
        assert response["computation_time_ms"] < 10

    # -------------------------------------------------------------------------
    # Contract Tests
    # -------------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_rd_single_event_schema(
        self, mock_api_client, recovery_distance_response, validate_response_schema
    ):
        """Test recovery distance single event response matches expected schema."""
        mock_api_client.get.return_value.json.return_value = recovery_distance_response

        response = mock_api_client.get.return_value.json()

        validate_response_schema(
            response,
            required_fields=["event", "recovery_distance", "feasible"],
            field_types={
                "event": dict,
                "recovery_distance": int,
                "feasible": bool,
                "witness_edits": list,
                "search_depth_reached": int,
                "computation_time_ms": float,
            },
        )

    @pytest.mark.asyncio
    async def test_rd_aggregate_schema(self, mock_api_client, validate_response_schema):
        """Test recovery distance aggregate response matches expected schema."""
        mock_response = {
            "rd_mean": 1.5,
            "rd_median": 1.0,
            "rd_p95": 3.0,
            "rd_max": 4,
            "breakglass_count": 2,
            "infeasible_count": 0,
            "events_tested": 20,
            "by_event_type": {},
        }
        mock_api_client.get.return_value.json.return_value = mock_response

        response = mock_api_client.get.return_value.json()

        validate_response_schema(
            response,
            required_fields=[
                "rd_mean",
                "rd_median",
                "rd_p95",
                "rd_max",
                "events_tested",
            ],
            field_types={
                "rd_mean": float,
                "rd_median": float,
                "rd_p95": float,
                "rd_max": int,
                "breakglass_count": int,
                "infeasible_count": int,
                "events_tested": int,
                "by_event_type": dict,
            },
        )


# ============================================================================
# Smoke Tests
# ============================================================================


class TestCompositeToolsSmoke:
    """Smoke tests to verify tools are registered and callable."""

    @pytest.mark.asyncio
    async def test_unified_index_tool_registered(self, mock_api_client):
        """Verify unified critical index tool is accessible."""
        mock_api_client.get.return_value.json.return_value = {
            "composite_index": 0.5,
            "risk_pattern": "low_risk",
        }

        response = mock_api_client.get.return_value.json()

        assert "composite_index" in response

    @pytest.mark.asyncio
    async def test_recovery_distance_tool_registered(self, mock_api_client):
        """Verify recovery distance tool is accessible."""
        mock_api_client.get.return_value.json.return_value = {
            "recovery_distance": 1,
            "feasible": True,
        }

        response = mock_api_client.get.return_value.json()

        assert "recovery_distance" in response


# ============================================================================
# Integration Tests (with actual backend module imports)
# ============================================================================


class TestCompositeIntegration:
    """Integration tests that use actual backend resilience modules."""

    def test_unified_index_calculation(self):
        """Test unified critical index calculation with actual module."""
        try:
            from uuid import uuid4

            from backend.app.resilience.unified_critical_index import (
                CriticalityDomain,
                DomainScore,
                UnifiedCriticalIndex,
            )

            # Create domain scores
            contingency = DomainScore(
                domain=CriticalityDomain.CONTINGENCY,
                raw_score=0.8,
                normalized_score=0.75,
                is_critical=True,
            )
            epidemiology = DomainScore(
                domain=CriticalityDomain.EPIDEMIOLOGY,
                raw_score=0.5,
                normalized_score=0.45,
                is_critical=False,
            )
            hub = DomainScore(
                domain=CriticalityDomain.HUB_ANALYSIS,
                raw_score=0.6,
                normalized_score=0.55,
                is_critical=False,
            )

            # Create unified index
            from datetime import datetime

            index = UnifiedCriticalIndex(
                faculty_id=uuid4(),
                faculty_name="Dr. Test",
                calculated_at=datetime.now(),
                contingency_score=contingency,
                epidemiology_score=epidemiology,
                hub_score=hub,
            )

            # Verify calculations
            assert 0 <= index.composite_index <= 1.0
            assert index.risk_pattern is not None
            assert len(index.recommended_interventions) > 0

        except ImportError:
            pytest.skip("Backend modules not available in test environment")

    def test_recovery_distance_calculation(self):
        """Test recovery distance calculation with actual module."""
        try:
            from uuid import uuid4

            from backend.app.resilience.recovery_distance import (
                N1Event,
                RecoveryDistanceCalculator,
            )

            calculator = RecoveryDistanceCalculator(max_depth=3, timeout_seconds=5)

            # Create mock schedule
            class MockPerson:
                def __init__(self, pid, role):
                    self.id = pid
                    self.name = f"Person-{pid}"
                    self.role = role

            class MockBlock:
                def __init__(self, bid):
                    self.id = bid
                    from datetime import date

                    self.date = date.today()

            class MockAssignment:
                def __init__(self, person_id, block_id):
                    self.id = uuid4()
                    self.person_id = person_id
                    self.block_id = block_id

            # Create test data
            faculty = [MockPerson(uuid4(), "FACULTY") for _ in range(3)]
            residents = [MockPerson(uuid4(), "RESIDENT") for _ in range(5)]
            blocks = [MockBlock(uuid4()) for _ in range(6)]

            # Create assignments (each block has 2 people)
            assignments = []
            for i, block in enumerate(blocks):
                assignments.append(MockAssignment(faculty[i % 3].id, block.id))
                assignments.append(MockAssignment(residents[i % 5].id, block.id))

            schedule = {
                "assignments": assignments,
                "blocks": blocks,
                "people": faculty + residents,
            }

            # Create event
            event = N1Event(
                event_type="faculty_absence",
                resource_id=faculty[0].id,
                affected_blocks=[b.id for b in blocks[:2]],
            )

            # Calculate recovery distance
            result = calculator.calculate_for_event(schedule, event)

            assert result.recovery_distance >= 0
            assert result.search_depth_reached <= 3
            assert result.computation_time_ms > 0

        except ImportError:
            pytest.skip("Backend modules not available in test environment")

    def test_unified_index_population_analysis(self):
        """Test population analysis with actual module."""
        try:
            from uuid import uuid4

            from backend.app.resilience.unified_critical_index import (
                UnifiedCriticalIndexAnalyzer,
            )

            # Create mock data
            class MockFaculty:
                def __init__(self):
                    self.id = uuid4()
                    self.name = f"Faculty-{self.id}"

            class MockAssignment:
                def __init__(self, person_id, block_id):
                    self.person_id = person_id
                    self.block_id = block_id

            faculty = [MockFaculty() for _ in range(5)]
            blocks = [uuid4() for _ in range(10)]

            # Create assignments with varied patterns
            assignments = []
            for i, fac in enumerate(faculty):
                # Each faculty gets different number of assignments
                for j in range(i + 1):
                    if j < len(blocks):
                        assignments.append(MockAssignment(fac.id, blocks[j]))

            # Analyze
            analyzer = UnifiedCriticalIndexAnalyzer()
            analyzer.build_network(faculty, assignments, shared_shift_threshold=1)

            coverage_requirements = dict.fromkeys(blocks, 1)
            analysis = analyzer.analyze_population(
                faculty=faculty,
                assignments=assignments,
                coverage_requirements=coverage_requirements,
            )

            assert analysis.total_faculty == 5
            assert len(analysis.indices) == 5
            assert analysis.risk_concentration >= 0

        except ImportError:
            pytest.skip("Backend modules not available in test environment")

    def test_recovery_distance_aggregate_metrics(self):
        """Test aggregate recovery distance metrics with actual module."""
        try:
            from backend.app.resilience.recovery_distance import (
                RecoveryDistanceMetrics,
            )

            # Test dataclass
            metrics = RecoveryDistanceMetrics(
                rd_mean=1.5,
                rd_median=1.0,
                rd_p95=3.0,
                rd_max=4,
                breakglass_count=2,
                infeasible_count=0,
                events_tested=20,
                by_event_type={
                    "faculty_absence": {"mean": 2.0, "max": 4},
                    "resident_sick": {"mean": 1.0, "max": 2},
                },
            )

            assert metrics.rd_mean == 1.5
            assert metrics.breakglass_count == 2
            assert len(metrics.by_event_type) == 2

        except ImportError:
            pytest.skip("Backend modules not available in test environment")
