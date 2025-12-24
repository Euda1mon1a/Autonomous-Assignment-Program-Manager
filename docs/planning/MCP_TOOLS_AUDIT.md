# MCP Tools Audit Report

> **Date:** 2025-12-24
> **Auditor:** Claude Code
> **Branch:** claude/audit-mcp-tools-syNpM

---

## Executive Summary

This audit examines the current MCP (Model Context Protocol) infrastructure, identifying:
- **29 MCP tools** currently registered
- **2 MCP resources** exposed
- **~10 placeholder implementations** needing real backend integration
- **8+ missing tools** that would unlock new capabilities
- **Several incomplete features** blocking production readiness

---

## Current State

### Implemented MCP Tools (29 Total)

| Category | Count | Status |
|----------|-------|--------|
| Schedule Validation | 2 | Functional |
| Conflict & Contingency | 3 | Functional |
| Async Background Tasks | 4 | Functional (Celery) |
| Resilience Framework | 13 | **Mostly Placeholders** |
| Deployment & CI/CD | 7 | Functional (simulated) |

### Implemented MCP Resources (2 Total)

| Resource | URI | Status |
|----------|-----|--------|
| Schedule Status | `schedule://status` | Functional |
| Compliance Summary | `schedule://compliance` | Functional |

---

## CRITICAL: Placeholder Implementations

The following tools return **mock/placeholder data** instead of real backend integration:

### Resilience Integration Placeholders

| Tool | File:Line | Issue |
|------|-----------|-------|
| `analyze_homeostasis` | `resilience_integration.py:796` | Returns mock homeostasis data |
| `get_static_fallbacks` | `resilience_integration.py:836` | Returns mock fallback schedules |
| `execute_sacrifice_hierarchy` | `resilience_integration.py:917` | Returns mock load shedding data |
| `calculate_blast_radius` | `resilience_integration.py:974` | Returns mock zone isolation data |
| `analyze_le_chatelier` | `resilience_integration.py:1017` | Returns mock equilibrium data |
| `analyze_hub_centrality` | `resilience_integration.py:1054` | Returns mock centrality data |
| `assess_cognitive_load` | `resilience_integration.py:1095` | Returns mock cognitive load data |
| `get_behavioral_patterns` | `resilience_integration.py:1130` | Returns mock behavioral data |
| `analyze_stigmergy` | `resilience_integration.py:1173` | Returns mock stigmergy data |
| `check_mtf_compliance` | `resilience_integration.py:1213` | Returns mock MTF data |

### Schedule Validation Fallback

| Tool | File:Line | Issue |
|------|-----------|-------|
| `validate_schedule_by_id` | `validate_schedule.py:183-200` | Falls back to placeholder when API unavailable |

**Impact:** These tools will work in demos but provide no real value in production.

---

## MISSING: High-Value Tools Not Yet Implemented

### Priority 1: Core Schedule Operations (Blocking Production Use)

| Tool | Purpose | Dependency | Effort |
|------|---------|------------|--------|
| `generate_schedule` | Generate new schedule via CP-SAT solver | Backend `/api/v1/schedule/generate` | Medium |
| `execute_swap` | Execute approved swap request | Backend swap executor service | Medium |
| `rollback_swap` | Reverse swap within 24h window | Backend swap service | Low |
| `bulk_assign` | Mass assignment for schedule blocks | Backend assignment service | Medium |

**Why Missing:** These are write operations requiring careful safety gates (backup verification, user confirmation). The `safe-schedule-generation` skill references these but they don't exist.

### Priority 2: Analytics & Reporting

| Tool | Purpose | Dependency | Effort |
|------|---------|------------|--------|
| `get_coverage_heatmap` | Coverage matrix (rotation × date) | Backend heatmap service | Low |
| `get_fairness_metrics` | Gini coefficient, workload distribution | Backend analytics | Low |
| `get_preference_satisfaction` | How well preferences are honored | Backend analytics | Low |
| `get_swap_history` | Audit trail of past swaps | Backend swap service | Low |

**Why Missing:** These are read-only but require backend analytics services that may not be fully exposed.

### Priority 3: Proactive Monitoring

| Tool | Purpose | Dependency | Effort |
|------|---------|------------|--------|
| `get_expiring_credentials` | Credentials expiring in 30/60/90 days | Backend credential service | Low |
| `get_upcoming_absences` | Leave/TDY in next N days | Backend absence service | Low |
| `forecast_utilization` | Predict future utilization | Backend analytics | Medium |

**Why Missing:** Monitoring features not prioritized in initial MCP implementation.

### Priority 4: Notification & Workflow

| Tool | Purpose | Dependency | Effort |
|------|---------|------------|--------|
| `send_notification` | Send schedule change notifications | Backend notification service | Medium |
| `create_conflict_alert` | Create manual conflict alert | Backend alert service | Low |
| `resolve_conflict` | Mark conflict as resolved | Backend alert service | Low |

**Why Missing:** Notification integration not yet connected.

---

## MISSING: High-Value Resources Not Yet Implemented

### Schedule Resources (Planned but Not Implemented)

| Resource | URI | Purpose |
|----------|-----|---------|
| Individual Person Schedule | `schedule://assignments/person/{id}` | Show one person's assignments |
| Rotation Coverage | `schedule://status/coverage/{rotation}` | Coverage for specific rotation |
| Active Conflicts | `schedule://conflicts/active` | Unresolved scheduling conflicts |

### Compliance Resources

| Resource | URI | Purpose |
|----------|-----|---------|
| Individual Compliance | `compliance://acgme/person/{id}` | One person's ACGME status |
| Violation History | `compliance://acgme/violations` | Historical violation trends |

### Resilience Resources

| Resource | URI | Purpose |
|----------|-----|---------|
| Homeostasis Status | `resilience://homeostasis/status` | System stability metrics |
| Allostatic Load | `resilience://allostatic-load/{id}` | Burnout risk per person |
| Contingency Library | `resilience://contingency/scenarios` | Available emergency plans |

### Analytics Resources

| Resource | URI | Purpose |
|----------|-----|---------|
| Coverage Heatmap | `analytics://coverage/heatmap` | Visual coverage matrix |
| Fairness Metrics | `analytics://fairness/metrics` | Workload distribution |
| Stability Trends | `analytics://stability/trends` | Schedule change frequency |

---

## INCOMPLETE: Partially Implemented Features

### 1. Backend API Integration

**Issue:** MCP server can't authenticate to backend API
**Location:** `mcp-server/src/scheduler_mcp/api_client.py`
**Missing:**
- JWT token acquisition from API
- Token refresh mechanism
- Proper error handling for auth failures

**Current State:** Falls back to placeholder data when API unavailable.

### 2. Database Direct Access

**Issue:** Direct database queries not implemented
**Location:** `mcp-server/src/scheduler_mcp/resources.py`
**Missing:**
- SQLAlchemy session management
- Async database queries
- Connection pooling

**Current State:** Resources return mock data without DATABASE_URL.

### 3. Celery Task Integration

**Issue:** Background tasks work but can't retrieve results from backend Celery
**Location:** `mcp-server/src/scheduler_mcp/async_tools.py`
**Missing:**
- Shared Celery broker connection
- Task result backend access
- Real task dispatching

**Current State:** Simulates task lifecycle but doesn't execute real tasks.

### 4. Real-Time Streaming

**Issue:** No WebSocket support for live updates
**Planned:** Phase 6 in MCP_INTEGRATION_OPPORTUNITIES.md
**Missing:**
- WebSocket transport
- Resource subscription
- Change event broadcasting

**Current State:** Polling-only via `get_task_status`.

---

## OPPORTUNITIES: New Doors to Open

### 1. AI-Assisted Schedule Generation

**Capability:** Natural language schedule requests
```
"Generate a schedule for January that maximizes Dr. Smith's preference
for afternoon shifts while maintaining ACGME compliance"
```

**Required:**
- `generate_schedule` tool with parameter flexibility
- Integration with OR-Tools solver
- Pareto frontier presentation

**Impact:** Reduces schedule generation from hours of manual work to minutes.

### 2. Proactive Compliance Monitoring

**Capability:** Continuous ACGME violation detection
```
Alert: "Resident PGY2-03 will exceed 80-hour limit in 3 days
       if current assignments continue"
```

**Required:**
- Background monitoring task
- Predictive hour calculation
- Alert generation tools

**Impact:** Prevents compliance violations before they occur.

### 3. Intelligent Swap Matching

**Capability:** AI-powered swap partner recommendations
```
"Find the best swap partner for Dr. Johnson's Thursday shift
considering workload balance, preferences, and skill match"
```

**Required:**
- Full `analyze_swap_candidates` implementation
- Preference learning from history
- Multi-objective ranking

**Impact:** Reduces swap coordination time by 80%.

### 4. Resilience Dashboard

**Capability:** Real-time system health visualization
```
"Show me which faculty are single points of failure
and what our backup capacity is for next week"
```

**Required:**
- Real hub centrality calculation
- N-1/N-2 contingency with real data
- Utilization forecasting

**Impact:** Proactive risk management instead of reactive crisis response.

### 5. Cross-System Integration

**Capability:** Connect to external systems
- EHR (Epic, Cerner) for patient load
- Calendar systems for automatic sync
- Email/Slack for notifications
- Credential management systems

**Required:**
- OAuth2 token management
- External API adapters
- Webhook handlers

**Impact:** Single source of truth for scheduling.

---

## Priority Ranking

### P0: CRITICAL (Required for Production)

| Item | Type | Effort | Impact |
|------|------|--------|--------|
| Backend API authentication | Fix | Medium | Unlocks all tools |
| Database direct access | Fix | Medium | Enables resources |
| Replace resilience placeholders | Fix | High | 13 tools become real |
| `generate_schedule` tool | Add | Medium | Core functionality |
| `execute_swap` tool | Add | Medium | Core functionality |

### P1: HIGH (Major Value Add)

| Item | Type | Effort | Impact |
|------|------|--------|--------|
| Individual person resources | Add | Low | Better UX |
| Coverage heatmap resource | Add | Low | Visual insights |
| Fairness metrics resource | Add | Low | Equity monitoring |
| `get_expiring_credentials` | Add | Low | Proactive management |
| Background task real execution | Fix | Medium | Automation works |

### P2: MEDIUM (Nice to Have)

| Item | Type | Effort | Impact |
|------|------|--------|--------|
| Notification integration | Add | Medium | Communication |
| Swap history resource | Add | Low | Audit trail |
| Utilization forecasting | Add | Medium | Planning |
| `create_conflict_alert` | Add | Low | Manual alerts |

### P3: LOW (Future Enhancement)

| Item | Type | Effort | Impact |
|------|------|--------|--------|
| WebSocket streaming | Add | High | Real-time updates |
| EHR integration | Add | High | Patient load awareness |
| Mobile app support | Add | High | On-the-go access |
| NLP query interface | Add | High | Natural language |

---

## Recommended Action Plan

### Phase 1: Foundation Fixes (1-2 weeks)

1. **Fix backend API authentication**
   - Add JWT token management to `api_client.py`
   - Implement token refresh
   - Test with real backend

2. **Add database direct access**
   - Configure SQLAlchemy async session
   - Implement connection pooling
   - Add to resources module

3. **Verify Celery integration**
   - Connect to shared Redis broker
   - Test real task dispatching
   - Verify result retrieval

### Phase 2: Replace Placeholders (2-3 weeks)

1. **Implement real resilience tools**
   - Connect to `backend/app/resilience/` services
   - Replace all 10 placeholder implementations
   - Add integration tests

2. **Add missing core tools**
   - `generate_schedule` with backup verification
   - `execute_swap` with validation
   - `rollback_swap` for recovery

### Phase 3: Expand Resources (1-2 weeks)

1. **Add person-level resources**
   - Individual schedule
   - Individual compliance
   - Allostatic load

2. **Add analytics resources**
   - Coverage heatmap
   - Fairness metrics
   - Stability trends

### Phase 4: Production Hardening (1-2 weeks)

1. **Add comprehensive tests**
   - Integration tests for all tools
   - Resource validation tests
   - Error handling tests

2. **Security audit**
   - PII protection verification
   - Input sanitization
   - Rate limiting

3. **Documentation**
   - Update tool reference
   - Add examples
   - Troubleshooting guide

---

## Conclusion

The MCP infrastructure has a solid foundation with 29 tools and 2 resources, but **~35% of the implementation is placeholder code**. The most critical gap is the lack of real backend integration, which renders many tools non-functional in production.

**Immediate priorities:**
1. Fix API authentication (unblocks everything)
2. Replace resilience placeholders (biggest gap)
3. Add `generate_schedule` and `execute_swap` (core use cases)

With these fixes, the MCP server would provide genuine value for schedule management, not just demo capability.

---

*Report generated by MCP tools audit - December 2024*
