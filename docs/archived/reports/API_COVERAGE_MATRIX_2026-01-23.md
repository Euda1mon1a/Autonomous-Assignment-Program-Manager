# API Coverage Matrix Report

> **Generated:** 2026-01-23 | **Session:** 136
> **Scope:** 84 routes, 93 schemas, 752+ endpoints

---

## Executive Summary

| Layer | Total | Covered | Gap |
|-------|-------|---------|-----|
| **Backend Routes** | 84 files | 45 tested (53%) | 39 untested |
| **Endpoints** | 752+ | ~386 tested | ~366 untested |
| **Schemas** | 93 files | 71 exported | 22 orphaned |
| **Frontend Types** | 69K lines generated | 25+ used | ~3 stale |

**Overall Health: 67%** - Strong schemas, weak test coverage on resilience/advanced features.

---

## Route → Schema → Test Matrix

### Tier 1: Full Coverage (Route + Schema + Tests + Frontend)

| Route | Endpoints | Schema | Test | Frontend |
|-------|-----------|--------|------|----------|
| **auth** | 8 | TokenWithRefresh, UserResponse | ✓ | ✓ |
| **people** | 13 | PersonCreate/Update/Response | ✓ | ✓ |
| **blocks** | 5 | BlockCreate/Response | ✓ | ✓ |
| **absences** | 9+ | AbsenceCreate/Update/Response | ✓ | ✓ |
| **assignments** | 6 | AssignmentCreate/Update/Response | ✓ | ✓ |
| **credentials** | 12 | CredentialCreate/Update/Response | ✓ | ✓ |
| **procedures** | 10 | ProcedureCreate/Update/Response | ✓ | ✓ |
| **certifications** | 13 | PersonCertification* | ✓ | ✓ |
| **rotation_templates** | 30+ | RotationTemplate* | ✓ | ✓ |
| **health** | 10 | HealthCheckResponse | ✓ | ✓ |

### Tier 2: Partial Coverage (Missing Tests OR Frontend)

| Route | Endpoints | Schema | Test | Frontend | Gap |
|-------|-----------|--------|------|----------|-----|
| **schedule** | 22 | ScheduleRequest/Response | Partial (55%) | ✓ | Need ~20 more tests |
| **swap** | 5 | SwapExecute*, SwapRecord* | ✗ | ✓ | No test file |
| **analytics** | 7 | VaR*, Metrics* | ✓ | Partial | Some hooks use inline types |
| **calendar** | 7 | CalendarEntry* | ✓ | Partial | Missing subscription types |

### Tier 3: Backend Only (No Tests)

| Route | Endpoints | Schema | Priority |
|-------|-----------|--------|----------|
| **resilience** | 59 | 50+ response types | **P0 CRITICAL** |
| **exotic_resilience** | 22 | Physics/Bio schemas | P2 |
| **fatigue_risk** | 16 | FRMS*, Fatigue* | **P1 SAFETY** |
| **call_assignments** | 13 | CallAssignment*, PCAT* | **P1** |
| **webhooks** | 13 | Webhook*, Delivery* | P1 |
| **wellness** | 15 | Wellness* | P1 |
| **game_theory** | 17 | Strategy*, Tournament* | P2 |
| **constraints** | 8 | ConstraintStatus* | P1 |
| **activities** | 6 | Activity* | P2 |
| **fmit_assignments** | 6 | FMITAssignment* | P1 |

### Tier 4: Orphaned Schemas (No Route Usage)

| Schema File | Classes | Status |
|-------------|---------|--------|
| behavioral_network.py | 17 | Research/experimental |
| chat.py | 8+ | Claude Chat (in progress) |
| mtf_compliance.py | 10+ | Military compliance (planned) |
| pareto.py | 6 | Optimization research |
| qubo_templates.py | 5 | Quantum optimization |
| gateway_auth.py | 4 | Auth gateway (unused) |
| workflow.py | 8+ | Workflow engine (partial) |

---

## Frontend Type Gaps

### Types Generated But Unused
- `BlockCreate`, `BlockUpdate` (blocks are immutable in UI)
- `SolverStatistics` (hooks use inline types)
- `ScheduleConfig` (frontend uses inline config objects)

### Endpoints Called Without Generated Types

| Domain | Endpoints | Status |
|--------|-----------|--------|
| `/game-theory/*` | 17 | Experimental, not in OpenAPI |
| `/fairness/*` | 3 | Missing from OpenAPI spec |
| `/resilience/*` | 59 | Missing from OpenAPI spec |

### Hook Files Using Inline Types (Should Import)
- `useSwaps.ts` - defines `SwapRequest`, `SwapType` locally
- `useGameTheory.ts` - defines all types locally
- `useResilience.ts` - defines response types locally

---

## Test Coverage Details

### Routes With 0% Test Coverage (39 routes, ~366 endpoints)

**Safety-Critical (P0):**
1. `resilience.py` - 59 endpoints (crisis management, fallbacks)
2. `fatigue_risk.py` - 16 endpoints (resident fatigue assessment)
3. `call_assignments.py` - 13 endpoints (PCAT equity)

**Business-Critical (P1):**
4. `webhooks.py` - 13 endpoints (event delivery)
5. `wellness.py` - 15 endpoints (resident health)
6. `constraints.py` - 8 endpoints (schedule constraints)
7. `swap.py` - 5 endpoints (FMIT swaps)
8. `fmit_assignments.py` - 6 endpoints

**Lower Priority (P2):**
- `exotic_resilience.py` (22), `game_theory.py` (17), `visualization.py` (9), etc.

---

## Schema Completeness

### CRUD Pattern Adherence

| Pattern | Files | Coverage |
|---------|-------|----------|
| `*Base` | 93/93 | 100% ✓ |
| `*Create` | 44/93 | 47% (appropriate) |
| `*Update` | 37/93 | 40% (immutable entities excluded) |
| `*Response` | 85/93 | 91% ✓ |
| `*ListResponse` | 40/93 | 43% ✓ |

**All 20+ core entities have complete CRUD schemas.**

---

## Recommendations

### P0: Immediate (Safety/Core)

1. **Add resilience.py tests** (59 endpoints) - core framework, crisis management
2. **Add fatigue_risk.py tests** (16 endpoints) - medical safety compliance
3. **Regenerate frontend types** - `npm run generate:types` to sync

### P1: Short-term

4. **Add call_assignments.py tests** - PCAT equity calculations
5. **Add webhooks.py tests** - event delivery reliability
6. **Increase schedule.py coverage** - add ~20 tests (currently 55%)
7. **Add swap.py tests** - FMIT swap execution
8. **Consolidate hook types** - move inline types to api.ts

### P2: Medium-term

9. **Add game_theory.py to OpenAPI** - enable type generation
10. **Add resilience/* to OpenAPI** - 59 endpoints missing
11. **Document orphaned schemas** - mark experimental vs planned
12. **Remove unused frontend types** - BlockCreate, SolverStatistics

---

## Coverage Heat Map

```
                    SCHEMA    ROUTE    TEST    FRONTEND
                    ─────────────────────────────────────
auth                  ██████   ██████   ██████   ██████
people                ██████   ██████   ██████   ██████
blocks                ██████   ██████   ██████   ██████
absences              ██████   ██████   ██████   ██████
assignments           ██████   ██████   ██████   ██████
schedule              ██████   ██████   ███░░░   ██████
resilience            ██████   ██████   ░░░░░░   ░░░░░░  ← CRITICAL GAP
swap                  ██████   ██████   ░░░░░░   ██████
fatigue_risk          ██████   ██████   ░░░░░░   ░░░░░░  ← SAFETY GAP
call_assignments      ██████   ██████   ░░░░░░   ███░░░
game_theory           ██████   ██████   ░░░░░░   ░░░░░░
exotic_resilience     ██████   ██████   ░░░░░░   ░░░░░░

Legend: ██████ = Complete  ███░░░ = Partial  ░░░░░░ = Missing
```

---

## Cross-Reference: Related Reports

- [Skills Audit](./SKILLS_AUDIT_2026-01-23.md) - 92 skills evaluated
- [MCP Tools Audit](./MCP_TOOLS_AUDIT_2026-01-23.md) - 137 tools evaluated
- [Skills-Tools Rationalization](./SKILLS_TOOLS_RATIONALIZATION_2026-01-23.md) - consolidation plan

---

*Analysis based on 84 routes, 93 schemas, 752+ endpoints, 76+ frontend hooks.*
