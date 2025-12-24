# MCP Placeholder Implementations

> **Purpose:** Track placeholder code that needs real backend integration
> **Status:** 10 tools return mock data instead of real calculations

---

## Resilience Integration Placeholders

**File:** `mcp-server/src/scheduler_mcp/resilience_integration.py`

| Tool | Line | Current Behavior | Needed Integration |
|------|------|------------------|-------------------|
| `analyze_homeostasis` | 796 | Returns mock homeostasis data | `ResilienceService.check_homeostasis()` |
| `get_static_fallbacks` | 836 | Returns mock fallback schedules | `ResilienceService.get_fallback_schedules()` |
| `execute_sacrifice_hierarchy` | 917 | Returns mock load shedding | `ResilienceService.execute_sacrifice()` |
| `calculate_blast_radius` | 974 | Returns mock zone isolation | `BlastRadiusService.calculate()` |
| `analyze_le_chatelier` | 1017 | Returns mock equilibrium data | `ResilienceService.analyze_equilibrium()` |
| `analyze_hub_centrality` | 1054 | Returns mock centrality scores | `ContingencyService.hub_analysis()` |
| `assess_cognitive_load` | 1095 | Returns mock cognitive load | `HomeostasisService.cognitive_load()` |
| `get_behavioral_patterns` | 1130 | Returns mock behavioral data | `BehavioralNetworkService.patterns()` |
| `analyze_stigmergy` | 1173 | Returns mock stigmergy signals | `StigmergyService.analyze()` |
| `check_mtf_compliance` | 1213 | Returns mock MTF data | `MTFComplianceService.check()` |

---

## Pattern for Fixing

Each placeholder follows this pattern:

```python
# Current (placeholder):
async def some_tool(...):
    # ... validation ...

    # Placeholder for actual integration
    return SomeResult(
        mock_field="placeholder value",
        ...
    )

# Fixed (with real integration):
async def some_tool(...):
    # ... validation ...

    try:
        client = get_api_client()
        response = await client.post("/api/v1/resilience/some-endpoint", json={...})

        if response.status_code == 200:
            data = response.json()
            return SomeResult(**data)
        else:
            # Fallback to placeholder with warning
            logger.warning(f"API unavailable: {response.status_code}")
            return _create_placeholder_result()
    except Exception as e:
        logger.error(f"Error calling API: {e}")
        return _create_placeholder_result()
```

---

## Backend Services to Connect

| MCP Tool | Backend Service | Endpoint |
|----------|-----------------|----------|
| `analyze_homeostasis` | `HomeostasisService` | `POST /api/v1/resilience/homeostasis` |
| `get_static_fallbacks` | `ResilienceService` | `GET /api/v1/resilience/fallbacks` |
| `execute_sacrifice_hierarchy` | `ResilienceService` | `POST /api/v1/resilience/sacrifice` |
| `calculate_blast_radius` | `BlastRadiusService` | `POST /api/v1/resilience/blast-radius` |
| `analyze_le_chatelier` | `ResilienceService` | `POST /api/v1/resilience/equilibrium` |
| `analyze_hub_centrality` | `ContingencyService` | `POST /api/v1/resilience/hub-analysis` |
| `assess_cognitive_load` | `HomeostasisService` | `GET /api/v1/resilience/cognitive-load` |
| `get_behavioral_patterns` | `BehavioralService` | `GET /api/v1/resilience/behavioral` |
| `analyze_stigmergy` | `StigmergyService` | `POST /api/v1/resilience/stigmergy` |
| `check_mtf_compliance` | `MTFComplianceService` | `GET /api/v1/resilience/mtf` |

---

## Validation Placeholders

**File:** `mcp-server/src/scheduler_mcp/tools/validate_schedule.py`

| Function | Line | Behavior |
|----------|------|----------|
| `validate_schedule_by_id` | 183-200 | Falls back to placeholder when API unavailable |
| `_create_placeholder_response` | 203-239 | Creates mock validation response |

**Note:** This fallback is intentional for graceful degradation but should log warnings.

---

## Priority for Fixing

### P0: Core Functionality
- `analyze_homeostasis` - Used for burnout detection
- `get_static_fallbacks` - Used for crisis response
- `execute_sacrifice_hierarchy` - Used for load shedding

### P1: Analysis Tools
- `calculate_blast_radius` - Zone containment
- `analyze_hub_centrality` - Single point of failure

### P2: Advanced Features
- `analyze_le_chatelier` - Equilibrium prediction
- `assess_cognitive_load` - Coordinator burnout
- `get_behavioral_patterns` - Pattern detection

### P3: Specialized
- `analyze_stigmergy` - Swarm intelligence
- `check_mtf_compliance` - Military compliance

---

## Testing Strategy

1. **Mock the API client** in tests to simulate backend responses
2. **Test fallback behavior** when API is unavailable
3. **Integration test** with real backend running

```python
# Example test
@pytest.mark.asyncio
async def test_homeostasis_with_real_backend():
    # Requires backend running at API_BASE_URL
    result = await analyze_homeostasis_tool(person_ids=["test-1"])

    # Should return real data, not placeholder
    assert result.source != "placeholder"
    assert result.allostatic_load is not None
```

---

## How to Identify Placeholders in Code

Search pattern:
```bash
grep -n "Placeholder for actual integration" mcp-server/src/scheduler_mcp/*.py
```

Or:
```bash
grep -n "placeholder" mcp-server/src/scheduler_mcp/*.py
```

---

*Placeholder tracking document - December 2024*
