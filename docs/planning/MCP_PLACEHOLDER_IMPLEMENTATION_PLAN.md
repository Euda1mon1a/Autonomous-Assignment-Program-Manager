# MCP Placeholder Implementation Plan

> **Created:** 2025-12-24
> **Purpose:** Comprehensive plan to convert MCP placeholder/mock implementations to real backend integrations
> **Status:** Planning Phase

---

## Executive Summary

The MCP (Model Context Protocol) server has **10 placeholder implementations** that return mock data instead of real backend calculations. This document provides a prioritized implementation plan with dependencies, effort estimates, and testing strategies.

### Current State

| Category | Count | Status |
|----------|-------|--------|
| **Fully Integrated** | 4 | `validate_schedule`, `detect_conflicts`, `analyze_swap_candidates`, `generate_schedule` |
| **Tier 1 Core (Placeholder)** | 3 | `get_static_fallbacks`, `execute_sacrifice_hierarchy`, `analyze_homeostasis` |
| **Tier 2 Strategic (Placeholder)** | 3 | `calculate_blast_radius`, `analyze_le_chatelier`, `analyze_hub_centrality` |
| **Tier 3 Advanced (Placeholder)** | 4 | `assess_cognitive_load`, `get_behavioral_patterns`, `analyze_stigmergy`, `check_mtf_compliance` |

---

## Implementation Priority Matrix

### Priority 0: Already Integrated (No Work Needed)

| Tool | File | Backend Endpoint | Status |
|------|------|------------------|--------|
| `validate_schedule` | `tools.py:200` | `POST /api/v1/scheduling/validate` | ✅ Working |
| `detect_conflicts` | `tools.py:471` | `GET /api/v1/scheduling/conflicts` | ✅ Working |
| `analyze_swap_candidates` | `tools.py:772` | `GET /api/v1/swaps/candidates` | ✅ Working (with mock fallback) |
| `generate_schedule` | `tools.py:1011` | `POST /api/v1/scheduling/generate` | ✅ Working |
| `run_contingency_analysis_deep` | `resilience_integration.py:657` | `POST /api/v1/resilience/contingency` | ✅ Working |
| `check_utilization_threshold` | `resilience_integration.py:425` | In-memory calculation | ✅ Working (tries real first) |
| `get_defense_level` | `resilience_integration.py:540` | In-memory calculation | ✅ Working (tries real first) |

### Priority 1: Core Resilience (Critical for Crisis Response)

These tools are essential for crisis situations and burnout detection.

| Tool | File:Line | Current Behavior | Required Backend | Effort |
|------|-----------|------------------|------------------|--------|
| `get_static_fallbacks` | `resilience_integration.py:782` | Returns empty lists | `ResilienceService.get_fallback_schedules()` | Medium |
| `execute_sacrifice_hierarchy` | `resilience_integration.py:813` | Returns mock load shedding | `ResilienceService.execute_sacrifice()` | Medium |
| `analyze_homeostasis` | `resilience_integration.py:893` | Returns mock allostatic load | `HomeostasisService.analyze()` | High |

**Dependencies:**
- Backend services must exist: `ResilienceService`, `HomeostasisService`
- Database tables: `fallback_schedules`, `sacrifice_levels`, `homeostasis_metrics`

### Priority 2: Strategic Analysis (Important for Planning)

These tools support proactive planning and zone management.

| Tool | File:Line | Current Behavior | Required Backend | Effort |
|------|-----------|------------------|------------------|--------|
| `calculate_blast_radius` | `resilience_integration.py:953` | Returns empty zone data | `BlastRadiusService.calculate()` | Medium |
| `analyze_le_chatelier` | `resilience_integration.py:995` | Returns mock equilibrium | `ResilienceService.analyze_equilibrium()` | High |
| `analyze_hub_centrality` | `resilience_integration.py:1040` | Returns empty hub list | `ContingencyService.hub_analysis()` | Medium |

**Dependencies:**
- NetworkX graph construction for hub analysis
- Zone configuration in database
- Stress tracking tables

### Priority 3: Advanced Features (Enhancement)

These tools provide advanced analytics but aren't crisis-critical.

| Tool | File:Line | Current Behavior | Required Backend | Effort |
|------|-----------|------------------|------------------|--------|
| `assess_cognitive_load` | `resilience_integration.py:1074` | Returns "fresh" status | `CognitiveLoadService.assess()` | Low |
| `get_behavioral_patterns` | `resilience_integration.py:1116` | Returns empty patterns | `BehavioralService.get_patterns()` | Medium |
| `analyze_stigmergy` | `resilience_integration.py:1150` | Returns empty suggestions | `StigmergyService.analyze()` | Medium |
| `check_mtf_compliance` | `resilience_integration.py:1192` | Returns "C1/FMC" always | `MTFComplianceService.check()` | Low |

---

## Implementation Pattern

Each placeholder should follow this pattern for graceful degradation:

```python
async def tool_function(request: RequestModel) -> ResponseModel:
    """Tool documentation."""
    logger.info(f"Calling tool with {request}")

    try:
        # 1. Try to call real backend API
        client = await get_api_client()
        result = await client.endpoint_method(...)

        # 2. Transform backend response to MCP format
        return ResponseModel(
            field1=result.get("field1"),
            field2=result.get("field2"),
            source="backend",  # Add source indicator
        )

    except Exception as e:
        # 3. Log warning (not error for graceful degradation)
        logger.warning(f"Backend unavailable, using fallback: {e}")

        # 4. Return fallback/placeholder response
        return _create_fallback_response(request)


def _create_fallback_response(request: RequestModel) -> ResponseModel:
    """Create a sensible fallback response when backend is unavailable."""
    return ResponseModel(
        field1="fallback_value",
        field2=0,
        source="fallback",  # Indicate this is not real data
        message="Backend unavailable - using fallback calculation",
    )
```

### Key Principles

1. **Never fail completely** - Always return a valid response
2. **Indicate data source** - Make it clear when using fallback vs real data
3. **Log appropriately** - `warning` for expected fallbacks, `error` for unexpected failures
4. **Preserve semantics** - Fallback should have reasonable default values

---

## Backend API Endpoints to Create

### Already Existing (Verified)

| Endpoint | Method | Handler |
|----------|--------|---------|
| `/api/v1/scheduling/validate` | POST | `backend/app/api/routes/schedule.py` |
| `/api/v1/scheduling/conflicts` | GET | `backend/app/api/routes/schedule.py` |
| `/api/v1/scheduling/generate` | POST | `backend/app/api/routes/schedule.py` |
| `/api/v1/swaps/candidates` | GET | `backend/app/api/routes/swaps.py` |
| `/api/v1/resilience/contingency` | POST | `backend/app/api/routes/resilience.py` |

### Need to Create

| Endpoint | Method | Service | Model Changes |
|----------|--------|---------|---------------|
| `/api/v1/resilience/fallbacks` | GET | `ResilienceService` | None |
| `/api/v1/resilience/sacrifice` | POST | `ResilienceService` | None |
| `/api/v1/resilience/homeostasis` | POST | `HomeostasisService` | May need metrics table |
| `/api/v1/resilience/blast-radius` | POST | `BlastRadiusService` | Zone config |
| `/api/v1/resilience/equilibrium` | POST | `ResilienceService` | Stress tracking |
| `/api/v1/resilience/hub-analysis` | POST | `ContingencyService` | None (uses NetworkX) |
| `/api/v1/resilience/cognitive-load` | GET | `CognitiveLoadService` | Session tracking |
| `/api/v1/resilience/behavioral` | GET | `BehavioralService` | Preference trails |
| `/api/v1/resilience/stigmergy` | POST | `StigmergyService` | Preference trails |
| `/api/v1/resilience/mtf` | GET | `MTFComplianceService` | None |

---

## Implementation Roadmap

### Phase 1: Foundation (Sprint 1)

**Goal:** Create missing backend services and basic endpoints

1. Create `backend/app/services/resilience/fallback_service.py`
   - `get_fallback_schedules()` method
   - `activate_fallback()` method

2. Create `backend/app/services/resilience/sacrifice_service.py`
   - `execute_sacrifice_hierarchy()` method
   - Activity priority configuration

3. Add endpoints to `backend/app/api/routes/resilience.py`
   - `/fallbacks` endpoint
   - `/sacrifice` endpoint

4. Update MCP integration:
   - `get_static_fallbacks()` → call real endpoint
   - `execute_sacrifice_hierarchy()` → call real endpoint

**Deliverables:**
- 2 new backend services
- 2 new API endpoints
- 2 MCP tools converted from placeholder

### Phase 2: Homeostasis & Equilibrium (Sprint 2)

**Goal:** Implement biological feedback and chemistry-inspired tools

1. Create `backend/app/services/resilience/homeostasis_service.py`
   - `analyze_feedback_loops()` method
   - `calculate_allostatic_load()` method
   - Setpoint monitoring

2. Create `backend/app/services/resilience/equilibrium_service.py`
   - Le Chatelier equilibrium analysis
   - Stress tracking and prediction
   - Compensation debt calculation

3. Add endpoints and update MCP:
   - `/homeostasis` endpoint
   - `/equilibrium` endpoint

**Deliverables:**
- 2 new backend services
- 2 new API endpoints
- 2 MCP tools converted from placeholder

### Phase 3: Network Analysis (Sprint 3)

**Goal:** Implement graph-based analysis tools

1. Enhance `backend/app/services/resilience/contingency_service.py`
   - Add hub centrality analysis using NetworkX
   - Add cascade failure simulation

2. Create `backend/app/services/resilience/blast_radius_service.py`
   - Zone health monitoring
   - Containment level calculation
   - Cross-zone borrowing tracking

3. Add endpoints and update MCP:
   - `/hub-analysis` endpoint
   - `/blast-radius` endpoint

**Deliverables:**
- 1 enhanced service, 1 new service
- 2 new API endpoints
- 2 MCP tools converted from placeholder

### Phase 4: Advanced Features (Sprint 4)

**Goal:** Implement remaining Tier 3 tools

1. Create `backend/app/services/resilience/cognitive_load_service.py`
   - Decision queue tracking
   - Miller's Law implementation
   - Auto-decision capability

2. Create `backend/app/services/resilience/stigmergy_service.py`
   - Preference trail collection
   - Swarm intelligence scoring
   - Pattern emergence detection

3. Create `backend/app/services/resilience/mtf_service.py`
   - DRRS category translation
   - Circuit breaker state machine
   - Iron Dome status

4. Add endpoints and update MCP for remaining tools

**Deliverables:**
- 3 new backend services
- 4 new API endpoints
- 4 MCP tools converted from placeholder

---

## Testing Strategy

### Unit Tests

Each new service should have comprehensive unit tests:

```python
# backend/tests/services/resilience/test_fallback_service.py
class TestFallbackService:
    async def test_get_fallback_schedules(self, db_session):
        """Test retrieval of pre-computed fallback schedules."""
        service = FallbackService(db_session)
        result = await service.get_fallback_schedules()

        assert isinstance(result, list)
        assert all(isinstance(f, FallbackSchedule) for f in result)

    async def test_activate_fallback_success(self, db_session, mock_fallback):
        """Test successful fallback activation."""
        service = FallbackService(db_session)
        result = await service.activate_fallback(mock_fallback.id)

        assert result.is_active
        assert result.activated_at is not None
```

### Integration Tests

Test MCP → Backend integration:

```python
# mcp-server/tests/test_resilience_integration.py
@pytest.mark.asyncio
async def test_get_static_fallbacks_real_backend():
    """Test get_static_fallbacks calls real backend."""
    # Requires backend running at API_BASE_URL
    result = await get_static_fallbacks()

    # Should return real data, not placeholder
    assert result.precomputed_scenarios_count >= 0  # Backend may have none
    # Key: message should not indicate fallback
    assert "fallback" not in result.message.lower() or "ready" in result.message.lower()
```

### Fallback Tests

Test graceful degradation when backend is unavailable:

```python
@pytest.mark.asyncio
async def test_homeostasis_fallback_when_backend_down(mocker):
    """Test that homeostasis returns sensible fallback when backend is unavailable."""
    # Mock API client to fail
    mocker.patch.object(APIClient, 'post', side_effect=ConnectionError)

    result = await analyze_homeostasis({"utilization": 0.75})

    # Should still return valid response
    assert result.overall_state in ("homeostasis", "allostasis", "allostatic_load", "allostatic_overload")
    assert result.severity in ("healthy", "warning", "elevated", "critical")
```

---

## API Client Updates

The `mcp-server/src/scheduler_mcp/api_client.py` needs new methods:

```python
class SchedulerAPIClient:
    # ... existing methods ...

    async def get_fallback_schedules(self) -> dict:
        """Get available fallback schedules."""
        return await self._request("GET", "/api/v1/resilience/fallbacks")

    async def execute_sacrifice(
        self,
        target_level: str,
        simulate_only: bool = True,
    ) -> dict:
        """Execute sacrifice hierarchy."""
        return await self._request(
            "POST",
            "/api/v1/resilience/sacrifice",
            json={"target_level": target_level, "simulate_only": simulate_only},
        )

    async def analyze_homeostasis(self, metrics: dict) -> dict:
        """Analyze homeostasis feedback loops."""
        return await self._request(
            "POST",
            "/api/v1/resilience/homeostasis",
            json={"metrics": metrics},
        )

    # ... additional methods for other tools ...
```

---

## Effort Estimates

| Phase | Tools | New Services | New Endpoints | Estimated Effort |
|-------|-------|--------------|---------------|------------------|
| Phase 1 | 2 | 2 | 2 | 3-4 days |
| Phase 2 | 2 | 2 | 2 | 4-5 days |
| Phase 3 | 2 | 2 | 2 | 3-4 days |
| Phase 4 | 4 | 3 | 4 | 5-6 days |
| **Total** | **10** | **9** | **10** | **15-19 days** |

---

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Backend service complexity | High | Start with simple implementations, iterate |
| Database schema changes | Medium | Use migrations, avoid breaking changes |
| Network latency | Low | Async operations, reasonable timeouts |
| Circular dependencies | Medium | Clear service boundaries, DI |
| Test flakiness | Low | Mock external dependencies in unit tests |

---

## Success Criteria

1. **All 10 tools** call real backend endpoints (with graceful fallback)
2. **Test coverage** ≥ 80% for new services
3. **No breaking changes** to existing MCP tool interfaces
4. **Response time** < 500ms for all tools (P95)
5. **Fallback behavior** works when backend is unavailable

---

## Related Documentation

- [MCP Tools Reference](../mcp-server/docs/MCP_TOOLS_REFERENCE.md) - Tool documentation
- [Resilience Framework](../architecture/cross-disciplinary-resilience.md) - Resilience concepts
- [API Client Summary](../../mcp-server/API_CLIENT_SUMMARY.md) - API client usage

---

*Implementation plan document - December 2025*
