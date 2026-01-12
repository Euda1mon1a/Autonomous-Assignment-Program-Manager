"""
Shared fixtures for MCP resilience tool tests.

This module provides:
- Mock API client for backend responses
- Common test data fixtures (residents, schedules, metrics)
- Response schema factories for contract testing
- Timeout and error scenario helpers

Fixture Strategy:
1. Mock backend at the httpx client level (not internal functions)
2. Use realistic response schemas matching actual backend endpoints
3. Provide parameterized fixtures for edge cases
4. Support both sync and async test contexts
"""

import asyncio
import os
from datetime import date, datetime, timedelta
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

import pytest

# ============================================================================
# Environment Setup for Tests
# ============================================================================


@pytest.fixture(autouse=True)
def set_test_credentials(monkeypatch):
    """
    Set test credentials for API client tests.

    This fixture runs automatically for all tests and provides mock
    credentials that satisfy the API client's requirement for environment
    variables without exposing real credentials.
    """
    monkeypatch.setenv("API_USERNAME", "test_user")
    monkeypatch.setenv("API_PASSWORD", "test_password_secure_123")
    monkeypatch.setenv("API_BASE_URL", "http://localhost:8000")


# ============================================================================
# UUID Fixtures (Stable for Reproducible Tests)
# ============================================================================


@pytest.fixture
def stable_uuids() -> dict[str, UUID]:
    """
    Provide stable UUIDs for consistent test data.

    Using fixed UUIDs makes test failures easier to debug and
    ensures deterministic test behavior.
    """
    return {
        "resident_1": UUID("11111111-1111-1111-1111-111111111111"),
        "resident_2": UUID("22222222-2222-2222-2222-222222222222"),
        "resident_3": UUID("33333333-3333-3333-3333-333333333333"),
        "resident_4": UUID("44444444-4444-4444-4444-444444444444"),
        "resident_5": UUID("55555555-5555-5555-5555-555555555555"),
        "faculty_1": UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"),
        "faculty_2": UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"),
        "faculty_3": UUID("cccccccc-cccc-cccc-cccc-cccccccccccc"),
        "block_1": UUID("00000001-0001-0001-0001-000000000001"),
        "block_2": UUID("00000002-0002-0002-0002-000000000002"),
        "block_3": UUID("00000003-0003-0003-0003-000000000003"),
    }


# ============================================================================
# Mock API Client Fixtures
# ============================================================================


@pytest.fixture
def mock_api_response_factory():
    """
    Factory for creating mock API responses.

    Returns a function that creates properly structured responses
    for different endpoint types.
    """

    def create_response(
        endpoint: str,
        status: str = "success",
        data: dict[str, Any] | None = None,
        error: str | None = None,
    ) -> dict[str, Any]:
        """Create mock API response matching backend patterns."""
        base_response = {
            "status": status,
            "timestamp": datetime.now().isoformat(),
            "endpoint": endpoint,
        }

        if error:
            base_response["error"] = True
            base_response["message"] = error
            base_response["error_code"] = "API_ERROR"
        else:
            base_response["error"] = False
            base_response["data"] = data or {}

        return base_response

    return create_response


@pytest.fixture
def mock_httpx_client():
    """
    Mock httpx.AsyncClient for testing API calls.

    This fixture mocks at the transport layer, allowing tests to
    control exactly what responses are returned for any API call.
    """
    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.aclose = AsyncMock()
        mock_client_class.return_value = mock_client

        # Setup async context manager
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        yield mock_client


@pytest.fixture
def mock_api_client(mock_httpx_client, mock_api_response_factory):
    """
    Fully configured mock API client with default responses.

    Provides a mock client that returns sensible defaults for
    common endpoints, but can be customized per-test.
    """
    # Default responses for common endpoints
    default_responses = {
        "/health": {"status": "healthy", "version": "1.0.0"},
        "/api/v1/resilience/seismic-detection": {
            "alerts": [],
            "analyzed_residents": 5,
            "time_series_length": 60,
        },
        "/api/v1/resilience/spc-monitoring": {
            "violations": [],
            "residents_analyzed": 5,
            "control_limits": {"ucl": 75.0, "lcl": 45.0, "target": 60.0},
        },
        "/api/v1/resilience/fire-danger-index": {
            "danger_reports": [],
            "residents_analyzed": 5,
            "highest_danger_class": "low",
        },
    }

    async def mock_get(url: str, **kwargs) -> MagicMock:
        response = MagicMock()
        response.status_code = 200

        # Find matching endpoint
        for endpoint, data in default_responses.items():
            if endpoint in url:
                response.json.return_value = data
                return response

        # Default fallback
        response.json.return_value = {"status": "ok"}
        return response

    async def mock_post(url: str, **kwargs) -> MagicMock:
        response = MagicMock()
        response.status_code = 200
        response.json.return_value = {"status": "ok", "result": {}}
        return response

    mock_httpx_client.get = AsyncMock(side_effect=mock_get)
    mock_httpx_client.post = AsyncMock(side_effect=mock_post)

    return mock_httpx_client


# ============================================================================
# Seismic Detection (STA/LTA) Fixtures
# ============================================================================


@pytest.fixture
def normal_swap_request_series() -> list[float]:
    """
    Normal swap request pattern - no anomalies.

    Represents stable behavior over 60 days with minor variation.
    """
    import random

    random.seed(42)  # Reproducible
    return [random.randint(0, 2) for _ in range(60)]


@pytest.fixture
def anomaly_swap_request_series() -> list[float]:
    """
    Swap request pattern with clear anomaly.

    Normal for first 45 days, then sudden increase (burnout precursor).
    """
    normal = [0, 1, 0, 1, 0, 1, 0, 0, 1, 0] * 4 + [0, 1, 0, 1, 0]  # 45 days
    anomaly = [3, 5, 7, 8, 10, 12, 9, 11, 8, 7, 6, 8, 9, 10, 11]  # 15 days spike
    return normal + anomaly


@pytest.fixture
def insufficient_data_series() -> list[float]:
    """
    Too short for STA/LTA analysis (requires minimum window size).
    """
    return [1, 2, 1, 2, 1]  # Only 5 data points


@pytest.fixture
def seismic_alert_response() -> dict[str, Any]:
    """
    Mock response for seismic detection with alerts.
    """
    return {
        "alerts": [
            {
                "signal_type": "swap_requests",
                "sta_lta_ratio": 4.5,
                "trigger_time": datetime.now().isoformat(),
                "severity": "high",
                "predicted_magnitude": 6.2,
                "time_to_event_days": 14,
                "resident_id": "11111111-1111-1111-1111-111111111111",
                "context": {"trigger_start_idx": 45, "trigger_end_idx": 55},
            }
        ],
        "analyzed_residents": 5,
        "time_series_length": 60,
        "severity": "warning",
    }


# ============================================================================
# SPC Monitoring Fixtures
# ============================================================================


@pytest.fixture
def stable_workload_hours() -> list[float]:
    """
    Stable workload pattern - all within control limits.

    Weekly hours centered around 60h with normal variation.
    """
    import random

    random.seed(42)
    return [60 + random.gauss(0, 3) for _ in range(12)]


@pytest.fixture
def workload_with_rule1_violation() -> list[float]:
    """
    Workload pattern that triggers Rule 1 (point beyond 3 sigma).

    One extreme outlier in otherwise normal data.
    """
    return [58, 62, 59, 61, 63, 60, 58, 82, 60, 59, 61, 60]  # 82 is the outlier


@pytest.fixture
def workload_with_rule2_violation() -> list[float]:
    """
    Workload pattern that triggers Rule 2 (2 of 3 beyond 2 sigma).

    Sustained shift upward.
    """
    return [58, 62, 59, 61, 72, 74, 73, 60, 59, 61, 60, 62]  # 72-74 trigger rule 2


@pytest.fixture
def workload_with_rule4_violation() -> list[float]:
    """
    Workload pattern that triggers Rule 4 (8 consecutive above centerline).

    Systematic shift above target.
    """
    return [61, 62, 63, 64, 65, 66, 67, 68, 58, 60, 62, 61]  # First 8 all above 60


@pytest.fixture
def spc_violation_response() -> dict[str, Any]:
    """
    Mock response for SPC monitoring with violations.
    """
    return {
        "violations": [
            {
                "rule": "Rule 1",
                "severity": "CRITICAL",
                "message": "Workload exceeded 3 sigma upper limit: 82.0 hours",
                "resident_id": "11111111-1111-1111-1111-111111111111",
                "data_points": [82.0],
                "control_limits": {"ucl_3sigma": 75.0, "lcl_3sigma": 45.0},
            }
        ],
        "residents_analyzed": 5,
        "control_limits": {"ucl": 75.0, "lcl": 45.0, "target": 60.0},
        "severity": "critical",
    }


# ============================================================================
# Fire Danger Index (Burnout) Fixtures
# ============================================================================


@pytest.fixture
def low_burnout_risk_data() -> dict[str, float]:
    """
    Resident with low burnout risk (all indicators healthy).
    """
    return {
        "recent_hours": 55.0,  # Below target
        "monthly_load": 220.0,  # Below target
        "yearly_satisfaction": 0.85,  # High satisfaction
        "workload_velocity": -2.0,  # Decreasing workload
    }


@pytest.fixture
def high_burnout_risk_data() -> dict[str, float]:
    """
    Resident with high burnout risk (all indicators elevated).
    """
    return {
        "recent_hours": 78.0,  # Near limit
        "monthly_load": 280.0,  # Over target
        "yearly_satisfaction": 0.35,  # Low satisfaction
        "workload_velocity": 8.0,  # Increasing workload
    }


@pytest.fixture
def extreme_burnout_risk_data() -> dict[str, float]:
    """
    Resident with extreme burnout risk (EXTREME danger class).
    """
    return {
        "recent_hours": 85.0,  # Over ACGME limit
        "monthly_load": 320.0,  # Severely over target
        "yearly_satisfaction": 0.15,  # Very low satisfaction
        "workload_velocity": 12.0,  # Rapidly increasing
    }


@pytest.fixture
def fire_danger_response() -> dict[str, Any]:
    """
    Mock response for fire danger index with high risk resident.
    """
    return {
        "danger_reports": [
            {
                "resident_id": "11111111-1111-1111-1111-111111111111",
                "danger_class": "very_high",
                "fwi_score": 72.5,
                "component_scores": {
                    "ffmc": 85.2,
                    "dmc": 68.3,
                    "dc": 55.0,
                    "isi": 45.8,
                    "bui": 61.2,
                    "fwi": 72.5,
                },
                "recommended_restrictions": [
                    "URGENT: Implement immediate workload reduction",
                    "Cap hours at 50/week maximum",
                ],
                "is_safe": False,
                "requires_intervention": True,
            }
        ],
        "residents_analyzed": 5,
        "highest_danger_class": "very_high",
        "severity": "critical",
    }


# ============================================================================
# Epidemiology (Burnout Contagion) Fixtures
# ============================================================================


@pytest.fixture
def small_social_network() -> dict[str, Any]:
    """
    Small social network for epidemiology testing.

    5 residents with connections based on shared shifts.
    """
    nodes = [
        {"id": "11111111-1111-1111-1111-111111111111", "name": "Resident A"},
        {"id": "22222222-2222-2222-2222-222222222222", "name": "Resident B"},
        {"id": "33333333-3333-3333-3333-333333333333", "name": "Resident C"},
        {"id": "44444444-4444-4444-4444-444444444444", "name": "Resident D"},
        {"id": "55555555-5555-5555-5555-555555555555", "name": "Resident E"},
    ]

    # A-B-C chain, D-E separate cluster, B connects to D (bridge)
    edges = [
        {"source": nodes[0]["id"], "target": nodes[1]["id"], "weight": 5},  # A-B
        {"source": nodes[1]["id"], "target": nodes[2]["id"], "weight": 3},  # B-C
        {"source": nodes[1]["id"], "target": nodes[3]["id"], "weight": 2},  # B-D (bridge)
        {"source": nodes[3]["id"], "target": nodes[4]["id"], "weight": 4},  # D-E
    ]

    return {"nodes": nodes, "edges": edges}


@pytest.fixture
def epidemiology_response() -> dict[str, Any]:
    """
    Mock response for epidemiology analysis.
    """
    return {
        "reproduction_number": 1.8,
        "status": "spreading",
        "secondary_cases": {
            "22222222-2222-2222-2222-222222222222": 2,
        },
        "intervention_level": "moderate",
        "super_spreaders": ["22222222-2222-2222-2222-222222222222"],
        "high_risk_contacts": [
            "11111111-1111-1111-1111-111111111111",
            "33333333-3333-3333-3333-333333333333",
        ],
        "recommended_interventions": [
            "MODERATE INTERVENTION REQUIRED",
            "Implement workload reduction for burned out individuals",
            "Break transmission chains",
        ],
        "severity": "warning",
    }


# ============================================================================
# Erlang C Fixtures
# ============================================================================


@pytest.fixture
def specialty_coverage_params() -> dict[str, Any]:
    """
    Parameters for specialty coverage calculation.
    """
    return {
        "specialty": "Orthopedic Surgery",
        "arrival_rate": 2.5,  # 2.5 cases per hour
        "service_time": 0.5,  # 30 minutes per case
        "target_wait_prob": 0.05,  # 5% max wait probability
    }


@pytest.fixture
def erlang_coverage_response() -> dict[str, Any]:
    """
    Mock response for Erlang coverage optimization.
    """
    return {
        "specialty": "Orthopedic Surgery",
        "required_specialists": 4,
        "predicted_wait_probability": 0.038,
        "offered_load": 1.25,
        "service_level": 0.978,
        "metrics": {
            "wait_probability": 0.038,
            "avg_wait_time": 0.012,
            "occupancy": 0.313,
        },
    }


# ============================================================================
# Process Capability Fixtures
# ============================================================================


@pytest.fixture
def capable_process_data() -> list[float]:
    """
    Data representing a capable process (Cpk >= 1.33).
    """
    import random

    random.seed(42)
    # Tight distribution around 60, well within 40-80 limits
    return [60 + random.gauss(0, 4) for _ in range(50)]


@pytest.fixture
def marginal_process_data() -> list[float]:
    """
    Data representing a marginal process (1.0 <= Cpk < 1.33).
    """
    import random

    random.seed(42)
    # Wider distribution, closer to limits
    return [60 + random.gauss(0, 8) for _ in range(50)]


@pytest.fixture
def incapable_process_data() -> list[float]:
    """
    Data representing an incapable process (Cpk < 1.0).
    """
    import random

    random.seed(42)
    # Very wide distribution, exceeds limits
    return [60 + random.gauss(0, 15) for _ in range(50)]


@pytest.fixture
def process_capability_response() -> dict[str, Any]:
    """
    Mock response for process capability analysis.
    """
    return {
        "cp": 1.67,
        "cpk": 1.52,
        "pp": 1.67,
        "ppk": 1.52,
        "cpm": 1.48,
        "capability_status": "CAPABLE",
        "sigma_level": 4.56,
        "sample_size": 50,
        "mean": 60.2,
        "std_dev": 3.98,
        "lsl": 40.0,
        "usl": 80.0,
        "target": 60.0,
    }


# ============================================================================
# Unified Critical Index Fixtures
# ============================================================================


@pytest.fixture
def unified_index_response() -> dict[str, Any]:
    """
    Mock response for unified critical index analysis.
    """
    return {
        "faculty_id": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
        "faculty_name": "Dr. Smith",
        "composite_index": 0.72,
        "risk_pattern": "structural_burnout",
        "domain_scores": {
            "contingency": {"raw": 0.85, "normalized": 0.82, "is_critical": True},
            "epidemiology": {"raw": 0.65, "normalized": 0.71, "is_critical": True},
            "hub_analysis": {"raw": 0.45, "normalized": 0.52, "is_critical": False},
        },
        "domain_agreement": 0.73,
        "recommended_interventions": [
            "workload_reduction",
            "cross_training",
            "wellness_support",
        ],
        "priority_rank": 2,
        "severity": "warning",
    }


# ============================================================================
# Recovery Distance Fixtures
# ============================================================================


@pytest.fixture
def n1_event_faculty_absence(stable_uuids) -> dict[str, Any]:
    """
    N-1 event: faculty absence scenario.
    """
    return {
        "event_type": "faculty_absence",
        "resource_id": str(stable_uuids["faculty_1"]),
        "affected_blocks": [
            str(stable_uuids["block_1"]),
            str(stable_uuids["block_2"]),
        ],
        "metadata": {"name": "Dr. Smith", "reason": "sick_leave"},
    }


@pytest.fixture
def recovery_distance_response() -> dict[str, Any]:
    """
    Mock response for recovery distance calculation.
    """
    return {
        "event": {
            "event_type": "faculty_absence",
            "resource_id": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
        },
        "recovery_distance": 2,
        "feasible": True,
        "witness_edits": [
            {
                "edit_type": "reassign",
                "new_person_id": "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
                "block_id": "00000001-0001-0001-0001-000000000001",
                "justification": "Reassign to available backup",
            },
            {
                "edit_type": "swap",
                "source_assignment_id": "12345678-1234-1234-1234-123456789012",
                "target_assignment_id": "87654321-4321-4321-4321-210987654321",
                "justification": "Swap to balance coverage",
            },
        ],
        "search_depth_reached": 2,
        "computation_time_ms": 125.5,
    }


# ============================================================================
# Error Scenario Fixtures
# ============================================================================


@pytest.fixture
def timeout_error_response():
    """
    Simulate timeout error from backend.
    """
    return {
        "error": True,
        "error_code": "TIMEOUT",
        "message": "Request timed out after 30 seconds",
        "retry_after": 60,
    }


@pytest.fixture
def service_unavailable_response():
    """
    Simulate service unavailable error.
    """
    return {
        "error": True,
        "error_code": "SERVICE_UNAVAILABLE",
        "message": "Backend service temporarily unavailable",
        "retry_after": 120,
    }


@pytest.fixture
def validation_error_response():
    """
    Simulate validation error from backend.
    """
    return {
        "error": True,
        "error_code": "VALIDATION_ERROR",
        "message": "Invalid date range: start_date must be before end_date",
        "details": {"field": "start_date", "constraint": "date_ordering"},
    }


# ============================================================================
# Async Test Helpers
# ============================================================================


@pytest.fixture
def event_loop():
    """
    Create event loop for async tests.

    Using asyncio_mode = "auto" in pytest.ini should handle this,
    but providing explicitly for compatibility.
    """
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def async_timeout():
    """
    Default timeout for async operations in tests.
    """
    return 5.0  # 5 seconds


# ============================================================================
# Schema Validation Helpers
# ============================================================================


@pytest.fixture
def validate_response_schema():
    """
    Helper function to validate response matches expected schema.

    Returns a function that checks:
    - Required fields are present
    - Field types are correct
    - Optional fields have correct types if present
    """

    def validate(response: dict, required_fields: list[str], field_types: dict) -> bool:
        """
        Validate response schema.

        Args:
            response: Response dict to validate
            required_fields: List of field names that must be present
            field_types: Dict mapping field names to expected types

        Returns:
            True if valid, raises AssertionError otherwise
        """
        # Check required fields
        for field in required_fields:
            assert field in response, f"Required field '{field}' missing from response"

        # Check field types
        for field, expected_type in field_types.items():
            if field in response:
                value = response[field]
                assert isinstance(
                    value, expected_type
                ), f"Field '{field}' has type {type(value)}, expected {expected_type}"

        return True

    return validate
