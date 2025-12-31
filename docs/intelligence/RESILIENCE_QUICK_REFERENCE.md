# Resilience Components - Quick Reference Card

## Component Summary Table

| Component | Status | Lines | Complexity | Est. Hours | Key APIs |
|-----------|--------|-------|-----------|----------|----------|
| **HealthStatusIndicator** | Stub | 44 | LOW | 2-3 | `GET /resilience/health` |
| **ResilienceHub** | Partial Stub | 37 | MEDIUM | 10-14 | `GET /resilience/report`, `/history/*` |
| **ContingencyAnalysis** | Stub | 25 | MEDIUM-HIGH | 8-10 | `GET /resilience/vulnerability`, `/hubs/top` |
| **HubVisualization** | Stub | 25 | HIGH | 12-16 | `POST /hubs/analyze`, `GET /hubs/distribution` |

## Implementation Order
1. **HealthStatusIndicator** (2-3h) - Atomic, establishes patterns
2. **ResilienceHub** (10-14h) - Container, enables testing
3. **ContingencyAnalysis** (8-10h) - Data display component
4. **HubVisualization** (12-16h) - Advanced visualization

**Total: 32-43 hours (4-5.5 engineering days)**

## Key Backend Endpoints (Priority Order)

### CRITICAL (Tier 1)
```
GET  /resilience/health                    HealthCheckResponse
GET  /resilience/report                    ComprehensiveReportResponse
GET  /resilience/vulnerability             VulnerabilityReportResponse
GET  /resilience/history/health?limit=30   HealthCheckHistoryResponse
GET  /resilience/history/events?limit=30   EventHistoryResponse
```

### HIGH (Tier 3)
```
GET  /resilience/tier3/hubs/top            TopHubsResponse
POST /resilience/tier3/hubs/analyze        HubAnalysisResponse
GET  /resilience/tier3/hubs/distribution   HubDistributionReportResponse
```

## Type Alignments Needed

### Current (Frontend) vs Backend
```
Frontend                    Backend
HealthStatus (5 values)  → OverallStatus (5 enums)
                            GREEN → healthy
                            YELLOW → warning
                            ORANGE → degraded
                            RED → critical
                            BLACK → emergency
```

**Action:** Rename HealthStatus type or create mapping layer

## Essential Hooks to Create

1. **useResilienceHealth()**
   - Endpoint: `GET /resilience/health`
   - Polling: 60s
   - Cache: 30s

2. **useVulnerabilityReport()**
   - Endpoint: `GET /resilience/vulnerability`
   - Polling: 5-10 min
   - Cache: 5 min

3. **useHubAnalysis()**
   - Endpoint: `POST /resilience/tier3/hubs/analyze`
   - Polling: One-time or 10 min
   - Cache: 10 min

4. **useHistoricalHealth()**
   - Endpoint: `GET /resilience/history/health`
   - Polling: None (one-time fetch)
   - Cache: 5 min

## Common Pitfalls ⚠️

1. **Polling Too Frequently** - Max 60s for health (expensive computation)
2. **Type Mismatch** - HealthStatus vs OverallStatus enums (align them)
3. **Missing Admin Role** - All endpoints require admin auth
4. **Graph Size** - HubVisualization dies with >500 nodes (implement clustering)
5. **Empty States** - Handle "no data" and "computing..." states

## Quick Implementation Checklist

**HealthStatusIndicator:**
- [ ] Map OverallStatus enum to colors
- [ ] Create hook: useResilienceHealth()
- [ ] Add loading skeleton
- [ ] Add error fallback
- [ ] Test with mock data

**ResilienceHub:**
- [ ] Add tab state (use Next.js URL params)
- [ ] Create 3 tab content sections
- [ ] Wire refresh button
- [ ] Add loading states
- [ ] Aggregate multiple API calls

**ContingencyAnalysis:**
- [ ] Create VulnerabilityTable component
- [ ] Map N-1 vulnerabilities to rows
- [ ] Map N-2 fatal pairs to section
- [ ] Display critical faculty list
- [ ] Sort/filter by risk level

**HubVisualization:**
- [ ] Choose visualization lib (React-Force-Graph recommended)
- [ ] Create hook: useHubAnalysis()
- [ ] Transform API response to graph nodes/edges
- [ ] Implement zoom/pan
- [ ] Add node detail tooltips
- [ ] Handle large graphs (cluster or filter)

## File Locations

| File | Purpose | Status |
|------|---------|--------|
| `frontend/src/features/resilience/HealthStatusIndicator.tsx` | Status indicator | Stub (44 lines) |
| `frontend/src/features/resilience/ResilienceHub.tsx` | Parent dashboard | Partial (37 lines) |
| `frontend/src/features/resilience/ContingencyAnalysis.tsx` | Contingency tab | Stub (25 lines) |
| `frontend/src/features/resilience/HubVisualization.tsx` | Hub graph | Stub (25 lines) |
| `frontend/src/hooks/useResilience.ts` | Emergency coverage | Exists (96 lines) |

## Authorization Notes

- **All endpoints** require `require_admin` role
- **Make ResilienceHub admin-only** at route level
- **Check user role** before rendering components
- **Handle 401/403** errors with "Admin access required" message

## Performance Targets

| Component | Target Render | API Response | Total Load |
|-----------|--------------|--------------|-----------|
| HealthStatusIndicator | <1ms | 500-1000ms | <1.5s |
| ContingencyAnalysis | <50ms | 2-5s | <5.5s |
| HubVisualization | 100-500ms | 2-5s | <5.5s |
| ResilienceHub | <100ms | 6-15s (parallel) | <15s |

**Optimization Tips:**
- Use React.memo for visualization components
- Implement virtualization for tables >100 rows
- Cache hub analysis (expensive computation)
- Paginate history data (default: 30 records)

## Testing Strategy

1. **Unit Tests** - Components with mock data
2. **Integration Tests** - Hooks with MSW (Mock Service Worker)
3. **E2E Tests** - Full flow with real backend API
4. **Performance Tests** - Large graph rendering, polling intervals

## Next Phase Readiness

**When to Move to Phase 2 (HubVisualization):**
- [ ] Phase 1 components complete and merged
- [ ] Hooks tested and stable
- [ ] Type definitions aligned
- [ ] API integration patterns established
- [ ] Design mockups approved for visualization

---

**Full Details:** See `RESILIENCE_COMPONENT_STUB_ANALYSIS.md`
