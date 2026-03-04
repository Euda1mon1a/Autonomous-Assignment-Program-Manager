# Resilience Hub

> Consolidated system health, compliance, and risk monitoring dashboard.

**Location:** `/admin/resilience-hub`
**Access:** Admin only
**Created:** 2026-01-15

---

## Overview

The Resilience Hub consolidates three previously fragmented admin pages into a single command center:

| Previous Page | New Location | Status |
|---------------|--------------|--------|
| `/admin/health` | Tab 1: Overview | Consolidated |
| `/admin/fairness` | Tab 3: Fairness | Consolidated |
| `/admin/game-theory` | Kept separate | Strategic tool |

---

## Tab Structure

### Tab 1: Overview

System health at a glance with key metrics:

- **Overall Status Badge** - healthy/warning/degraded/critical/emergency
- **Defense Level Widget** - 5-level nuclear safety paradigm (PREVENTION→EMERGENCY)
- **Utilization Gauge** - Queuing theory threshold monitoring (80% critical)
- **Burnout Rt Display** - Epidemiological SIR model for burnout spread
- **N-1 Vulnerability Map** - Single-point failure visualization
- **Immediate Actions** - Recommended interventions

**Data Sources:**
- `useSystemHealth()` - Overall health metrics
- `useVulnerabilityReport()` - N-1/N-2 analysis

### Tab 2: Circuit Breakers

Netflix Hystrix pattern monitoring for service health:

- **Breaker Status Summary** - Total, closed, open, half-open counts
- **Health Metrics** - Failure rates, trend analysis, severity
- **Individual Breaker Cards** - Per-service status with failure rates
- **Recommendations** - System-generated action items

**Circuit Breaker States:**
| State | Meaning | Color |
|-------|---------|-------|
| CLOSED | Normal operation | Green |
| OPEN | Circuit tripped, fail-fast | Red |
| HALF_OPEN | Testing recovery | Amber |

**Data Sources:**
- `useCircuitBreakers()` - All breakers status
- `useBreakerHealth()` - Aggregated health metrics

**Note:** Requires backend REST endpoints (see Backend API Gaps below).

### Tab 3: Fairness

Workload equity analysis with statistical metrics:

- **Jain's Fairness Index** - Circular gauge (0-100%)
  - ≥90%: Excellent (green)
  - ≥80%: Good (emerald)
  - ≥70%: Warning (amber)
  - <70%: Critical (red)
- **Gini Coefficient** - Inequality measure (0 = perfect equality)
- **Category Statistics** - Call, FMIT, Clinic, Admin averages
- **Faculty Workload Table** - Sortable per-faculty breakdown

**Data Sources:**
- `useFairnessAudit()` - Workload distribution analysis

### Tab 4: Compliance

Military compliance and multi-factor risk assessment:

- **MTF Compliance Status**
  - DRRS C-ratings (C1-C5)
  - Personnel P-ratings (P1-P4)
  - Capability S-ratings (S1-S4)
  - Iron Dome status (green/yellow/red)
- **Executive Summary** - Human-readable compliance overview
- **Deficiencies List** - Items requiring attention
- **Unified Critical Index** - Multi-factor risk aggregation
  - Contingency weight: 40%
  - Epidemiology weight: 25%
  - Hub analysis weight: 35%
- **Top Critical Faculty** - Risk-ranked faculty list
- **Recommendations** - Prioritized interventions

**Risk Patterns:**
| Pattern | Description |
|---------|-------------|
| UNIVERSAL_CRITICAL | All domains high - maximum risk |
| STRUCTURAL_BURNOUT | Contingency + Epidemiology high |
| INFLUENTIAL_HUB | Contingency + Hub high |
| SOCIAL_CONNECTOR | Epidemiology + Hub high |
| LOW_RISK | No domains elevated |

**Data Sources:**
- `useMTFCompliance()` - Military compliance metrics
- `useUnifiedCriticalIndex()` - Composite risk scores

---

## New Hooks

### useCircuitBreakers

```typescript
const { data, isLoading, error } = useCircuitBreakers();

// Returns: AllBreakersStatusResponse
// - totalBreakers, closedBreakers, openBreakers, halfOpenBreakers
// - breakers: CircuitBreakerStatusInfo[]
// - overallHealth, recommendations
```

### useBreakerHealth

```typescript
const { data, isLoading, error } = useBreakerHealth();

// Returns: BreakerHealthResponse
// - metrics: { overallFailureRate, averageFailureRate, ... }
// - severity, trendAnalysis, breakersNeedingAttention
```

### useMTFCompliance

```typescript
const { data, isLoading, error } = useMTFCompliance(checkCircuitBreaker);

// Returns: MTFComplianceResponse
// - drrsCategory, personnelRating, capabilityRating
// - ironDomeStatus, executiveSummary, deficiencies
```

### useUnifiedCriticalIndex

```typescript
const { data, isLoading, error } = useUnifiedCriticalIndex(topN);

// Returns: UnifiedCriticalIndexResponse
// - overallIndex, riskLevel, criticalCount
// - topCriticalFaculty: FacultyUnifiedIndex[]
// - recommendations
```

---

## New Types

Located in `frontend/src/types/resilience.ts`:

### Circuit Breaker Types
- `CircuitState` - closed, open, half_open
- `BreakerSeverity` - healthy, warning, critical, emergency
- `StateTransitionInfo` - Breaker state change record
- `CircuitBreakerStatusInfo` - Individual breaker status
- `AllBreakersStatusResponse` - All breakers summary
- `BreakerHealthMetrics` - Aggregated metrics
- `BreakerHealthResponse` - Health assessment

### MTF Compliance Types
- `MTFComplianceResponse` - Military readiness ratings

### Unified Critical Index Types
- `RiskPattern` - Risk pattern classification
- `InterventionType` - Recommended intervention types
- `DomainScoreInfo` - Per-domain risk scores
- `FacultyUnifiedIndex` - Per-faculty risk assessment
- `UnifiedCriticalIndexResponse` - Aggregate response

---

## Backend API Gaps

The following REST endpoints need to be created to expose MCP tools to the frontend:

| Endpoint | MCP Tool | Status |
|----------|----------|--------|
| `GET /resilience/circuit-breakers` | `check_circuit_breakers_tool` | Needed |
| `GET /resilience/circuit-breakers/health` | `get_breaker_health_tool` | Needed |
| `POST /resilience/unified-critical-index` | `get_unified_critical_index_tool` | Needed |

**Existing endpoint:**
- `GET /resilience/mtf-compliance` - Already exists, used by `useMTFCompliance()`

Until these endpoints are created, the Circuit Breakers tab and Unified Critical Index section will show graceful error messages.

---

## Auto-Refresh

All hooks include automatic data refresh:

| Hook | Stale Time | Refetch Interval |
|------|------------|------------------|
| `useCircuitBreakers` | 30s | 30s |
| `useBreakerHealth` | 30s | 30s |
| `useMTFCompliance` | 60s | - |
| `useUnifiedCriticalIndex` | 5min | - |

Manual refresh button available in header.

---

## Crisis Mode

When `health.crisisMode === true`:
- Red banner displays at top of page
- Overall status badge shows "EMERGENCY"
- All metrics update with increased urgency

---

## File Structure

```
frontend/src/
├── app/admin/resilience-hub/
│   └── page.tsx              # Main hub page (~700 lines)
├── components/resilience/
│   ├── DefenseLevel.tsx      # Existing component
│   ├── UtilizationGauge.tsx  # Existing component
│   ├── BurnoutRtDisplay.tsx  # Existing component
│   └── N1ContingencyMap.tsx  # Existing component
├── hooks/
│   ├── useResilience.ts      # New hooks added
│   └── index.ts              # Exports
└── types/
    └── resilience.ts         # New types added
```

---

## Related Documentation

- [ACGME Compliance Rules](../architecture/ACGME_RULES.md)
- [Resilience Framework](../architecture/RESILIENCE_FRAMEWORK.md)
- [MCP Tools Reference](../api/MCP_TOOLS.md)
