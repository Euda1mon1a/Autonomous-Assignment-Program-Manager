# 100-Task Parallel Execution Plan

> **Purpose:** Deploy 10 parallel CCW terminals on 100 tasks to build operational confidence
> **Status:** Ready for execution
> **Security:** Repository is CLEAN - safe to share with CCW instances

---

## Executive Summary

Based on exploration of MCP tools (81 total), backend tests, frontend tests, and security audit:

| Stream | Terminal | Tasks | Focus |
|--------|----------|-------|-------|
| A | 1-3 | 30 | MCP Tool Completion |
| B | 4-6 | 25 | Backend Service Tests |
| C | 7-8 | 15 | Frontend Component Tests |
| D | 9 | 10 | Integration/E2E Scenarios |
| E | 10 | 8 | Security Sweep |
| F | Overflow | 12 | Constraints + DB + Docs |

---

## Context Files for CCW Instances

### Files to Share (All Safe)

**Core Understanding:**
```
CLAUDE.md                                    # Project guidelines
docs/architecture/SOLVER_ALGORITHM.md        # Scheduling engine
docs/architecture/cross-disciplinary-resilience.md  # Resilience framework
```

**For MCP Work (Stream A):**
```
mcp-server/src/scheduler_mcp/server.py       # 81 tools, 4411 lines
mcp-server/src/scheduler_mcp/api_client.py   # API client pattern
mcp-server/src/scheduler_mcp/tools/          # Tool modules
backend/app/api/routes/                      # Backend endpoints to call
```

**For Backend Tests (Stream B):**
```
backend/app/services/                        # 47 services (21% tested)
backend/app/scheduling/constraints/          # 18 constraints (61% tested)
backend/app/resilience/                      # 44 modules (39% tested)
backend/tests/conftest.py                    # Test fixtures
```

**For Frontend Tests (Stream C):**
```
frontend/src/components/                     # 80 components
frontend/src/lib/                            # Utilities (auth.ts, validation.ts)
frontend/__tests__/                          # Existing test patterns
```

**For Security (Stream E):**
```
docs/security/DATA_SECURITY_POLICY.md        # OPSEC/PERSEC policy
docs/security/SECURITY_PATTERN_AUDIT.md      # Security architecture
backend/app/api/routes/auth.py               # Auth endpoints
backend/app/core/security.py                 # Security utilities
```

### Files to NEVER Share

```
.env                                         # Real credentials
docs/data/*.json                             # Real schedule data (gitignored)
.sanitize/                                   # PII mapping files
```

### RAG Knowledge Base (Requires Sanitization)

**Location:** `docs/rag-knowledge/` (10 documents, ~150KB total)

**Before sharing with CCW, run sanitization:**
```bash
# Follow the SOP in docs/security/PII_SANITIZATION_SOP.md
python scripts/sanitize_pii.py --input docs/rag-knowledge/ --output /tmp/rag-sanitized/

# Or manually review each file for:
# - Real names → Replace with PGY1-01, FAC-PD format
# - Real dates → Replace with YYYY-MM-DD placeholders
# - Internal URLs → Remove or replace with example.com
```

**RAG Documents to Review:**
| Document | Content | Sanitization Needed |
|----------|---------|---------------------|
| acgme-rules.md | Regulatory rules | None - generic |
| scheduling-policies.md | Program policies | Review for specifics |
| swap-system.md | Swap workflows | None - generic |
| military-specific.md | Military context | Review for OPSEC |
| resilience-concepts.md | Framework docs | None - generic |
| user-guide-faq.md | User help | Review for examples |
| session-learnings.md | AI learnings | Review for specifics |
| session-protocols.md | Session patterns | None - generic |
| delegation-patterns.md | Agent patterns | None - generic |
| exotic-concepts.md | Frontier concepts | None - generic |

---

## Database & Container Context for CCW

### Database Schema (42 SQLAlchemy Models)

**Core Entities:**
```
Person (residents/faculty) ──── Assignment ──── Block (AM/PM scheduling)
   │                               │
   ├── Absence                     └── RotationTemplate
   ├── CallAssignment
   ├── Certification
   └── FacultyPreference

ScheduleRun (audit trail) ──── Assignment (tracks generation)
User (auth) ──── SwapRecord ──── SwapApproval
```

**Key Models for CCW Context:**
- `Person`: id, name, type, pgy_level, faculty_role, specialties
- `Block`: id, date, time_of_day (AM/PM), block_number (1-13)
- `Assignment`: person_id, block_id, role, confidence, schedule_run_id
- `RotationTemplate`: name, activity_type, max_residents, supervision_required
- `RagDocument`: content, embedding (384-dim), doc_type, metadata

**Files to share for DB context:**
```
backend/app/models/                          # All 42 models
backend/app/db/session.py                    # Connection pooling
backend/alembic/versions/                    # 40 migrations
```

### Container Architecture

```
┌─ Docker Network: "app-network" ─────────────────────────────┐
│                                                              │
│  db (PostgreSQL 15 + pgvector)     Port: 5432              │
│  redis (Redis 7.4.2)               Port: 6379              │
│  backend (FastAPI)                 Port: 8000              │
│  frontend (Next.js 14)             Port: 3000              │
│  mcp-server (FastMCP)              Port: 8080              │
│  celery-worker (Celery)            Background tasks        │
│  celery-beat (Scheduler)           Periodic jobs           │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

**Files to share for container context:**
```
docker-compose.yml                           # All service definitions
docker-compose.dev.yml                       # Dev overrides
.env.example                                 # Required env vars (no secrets)
```

---

## Vector DB / RAG Status

### Current State: OPERATIONAL

| Component | Status | Technology |
|-----------|--------|------------|
| Vector Store | ✓ Operational | pgvector 0.8.1 on PostgreSQL 15 |
| Embeddings | ✓ Operational | sentence-transformers (all-MiniLM-L6-v2) |
| RAG Service | ✓ Operational | 384-dim vectors, cosine distance |
| API Routes | ✓ Operational | /api/rag/* (6 endpoints) |
| Knowledge Base | ⚠ 9/10 docs | exotic-concepts.md needs embedding |

### Key RAG Files for CCW Context
```
backend/app/services/rag_service.py          # RAG operations (700+ lines)
backend/app/services/embedding_service.py    # Embedding generation
backend/app/models/rag_document.py           # Vector storage model
backend/app/api/routes/rag.py                # API endpoints
scripts/init_rag_embeddings.py               # CLI for embedding docs
```

### RAG Capabilities
- Semantic search with top-K retrieval
- Document type filtering (acgme_rules, scheduling_policy, etc.)
- Context building for LLM injection
- Batch embedding with chunking

---

## Celery Background Task Context for CCW

### Task Queues (6 dedicated + 1 default)

| Queue | Purpose | Key Tasks |
|-------|---------|-----------|
| `default` | Unmapped tasks | General processing |
| `resilience` | Health checks, N-1/N-2 analysis | periodic_health_check (15 min), run_contingency_analysis (daily) |
| `notifications` | Email, webhooks, conflict detection | send_email, send_webhook, detect_leave_conflicts |
| `metrics` | Schedule metrics, snapshots | compute_schedule_metrics, snapshot_metrics (hourly) |
| `exports` | Export job execution | run_scheduled_exports (5 min), execute_export_job |
| `security` | Secret rotation | check_scheduled_rotations (daily), rotate_secret |
| `cleanup` | Database maintenance | cleanup_idempotency_requests (hourly), cleanup_token_blacklist |

### Periodic Tasks (Celery Beat)

**High-Frequency (Critical for Operations):**
- `periodic_health_check` - Every 15 min (resilience monitoring)
- `run_scheduled_exports` - Every 5 min (export queue processing)
- `timeout_stale_pending_requests` - Every 5 min (cleanup stuck requests)

**Daily:**
- `run_contingency_analysis` - 2 AM (N-1/N-2 analysis)
- `compute_schedule_metrics` - 5 AM (full metrics recompute)
- `generate_utilization_forecast` - 6 AM (utilization trending)
- `check_scheduled_rotations` - 1 AM (secret rotation check)

**Weekly:**
- `precompute_fallback_schedules` - Sunday 3 AM (static stability)
- `generate_fairness_trend_report` - Monday 7 AM (12-week fairness analysis)

### Task Modules (50+ tasks across 11 modules)

```
backend/app/tasks/
├── schedule_metrics_tasks.py    # Fairness, coverage, compliance
├── cleanup_tasks.py             # Idempotency, token cleanup
├── audit_tasks.py               # Audit log archival
├── backup_tasks.py              # Database backups
├── compliance_report_tasks.py   # ACGME compliance reports
├── ml_tasks.py                  # ML model training
├── rag_tasks.py                 # RAG embedding refresh
└── periodic_tasks.py            # Beat schedule configuration

backend/app/resilience/tasks.py   # Health checks, contingency
backend/app/notifications/tasks.py # Email, webhooks
backend/app/security/rotation_tasks.py # Secret rotation
backend/app/exports/jobs.py       # Export execution
```

### Worker Configuration
- **Concurrency:** 4 workers
- **Task Timeout:** 10 min hard / 9 min soft
- **Result Retention:** 1 hour (24 hours for metrics)
- **Broker:** Redis (redis://localhost:6379/0)

### Files to share for Celery context
```
backend/app/core/celery_app.py               # Main configuration
backend/app/tasks/periodic_tasks.py          # Beat schedule
backend/app/tasks/                           # All task modules
backend/app/resilience/tasks.py              # Resilience tasks
```

---

## Stream A: MCP Tool Completion (30 Tasks)

**Terminals 1-3 | Goal: Get all 81 MCP tools from placeholder to operational**

### Current State
- 50+ tools OPERATIONAL (real backend calls)
- 15+ tools PARTIAL (mock fallbacks)
- 16+ tools PLACEHOLDER (need backend endpoints)

### Task Breakdown

**Terminal 1: Core Scheduling Tools (10 tasks)**
| # | Task | File | Status → Target |
|---|------|------|-----------------|
| 1 | Implement schedule generation tool | server.py:generate_schedule_tool | Partial → Full |
| 2 | Add assignment CRUD tools | server.py | Missing → New |
| 3 | Implement swap execution tool | server.py:execute_swap_tool | Partial → Full |
| 4 | Add rotation template tools | server.py | Missing → New |
| 5 | Implement block management tools | server.py | Missing → New |
| 6 | Add absence management tools | server.py | Missing → New |
| 7 | Implement person lookup tools | server.py | Missing → New |
| 8 | Add call roster tools | server.py | Missing → New |
| 9 | Implement credential check tools | server.py | Missing → New |
| 10 | Add faculty preference tools | server.py | Missing → New |

**Terminal 2: Exotic Frontier Tools (10 tasks)**
| # | Task | Backend Endpoint Needed |
|---|------|------------------------|
| 11 | Hopfield energy calculation | POST /api/v1/resilience/hopfield/energy |
| 12 | Attractor detection | GET /api/v1/resilience/hopfield/attractors |
| 13 | Phase transition detection | POST /api/v1/resilience/thermodynamics/phase |
| 14 | Entropy calculation (real) | GET /api/v1/resilience/entropy |
| 15 | Free energy optimization | POST /api/v1/resilience/free-energy |
| 16 | Game theory Nash equilibrium | POST /api/v1/resilience/game-theory/nash |
| 17 | Lotka-Volterra dynamics | POST /api/v1/resilience/ecological |
| 18 | Kalman filter prediction | POST /api/v1/resilience/kalman |
| 19 | Fourier periodicity (real) | GET /api/v1/resilience/periodicity |
| 20 | Catastrophe detection | POST /api/v1/resilience/catastrophe |

**Terminal 3: Backend Endpoints for MCP (10 tasks)**
| # | Task | Route File |
|---|------|-----------|
| 21 | Create /resilience/hopfield/* routes | routes/resilience.py |
| 22 | Create /resilience/thermodynamics/* | routes/resilience.py |
| 23 | Create /resilience/game-theory/* | routes/game_theory.py |
| 24 | Create /resilience/ecological/* | routes/resilience.py |
| 25 | Create /resilience/kalman/* | routes/resilience.py |
| 26 | Create /schedule/assignments CRUD | routes/schedule.py |
| 27 | Create /people/lookup endpoints | routes/people.py |
| 28 | Create /credentials/check endpoint | routes/credentials.py |
| 29 | Create /call-roster/* endpoints | routes/call_roster.py |
| 30 | Create /preferences/* endpoints | routes/preferences.py |

---

## Stream B: Backend Service Tests (25 Tasks)

**Terminals 4-6 | Goal: Test 37 untested services**

### Current State
- 10/47 services tested (21%)
- 37 services WITHOUT tests

### Task Breakdown

**Terminal 4: Critical Domain Services (10 tasks)**
| # | Service | Test File to Create |
|---|---------|-------------------|
| 31 | person_service.py | test_person_service.py |
| 32 | workflow_service.py | test_workflow_service.py |
| 33 | constraint_service.py | test_constraint_service.py |
| 34 | block_service.py | test_block_service.py |
| 35 | academic_block_service.py | test_academic_block_service.py |
| 36 | credential_service.py | test_credential_service.py |
| 37 | certification_service.py | test_certification_service.py |
| 38 | heatmap_service.py | test_heatmap_service.py |
| 39 | calendar_service.py | test_calendar_service.py |
| 40 | role_view_service.py | test_role_view_service.py |

**Terminal 5: Integration Services (8 tasks)**
| # | Service | Test File to Create |
|---|---------|-------------------|
| 41 | xlsx_import.py | test_xlsx_import.py |
| 42 | xlsx_export.py | test_xlsx_export.py |
| 43 | email_service.py | test_email_service.py |
| 44 | rag_service.py | test_rag_service.py |
| 45 | embedding_service.py | test_embedding_service.py |
| 46 | llm_router.py | test_llm_router.py |
| 47 | claude_service.py | test_claude_service.py |
| 48 | idempotency_service.py | test_idempotency_service.py |

**Terminal 6: Resilience & Constraint Tests (7 tasks)**
| # | Module | Test File to Create |
|---|--------|-------------------|
| 49 | circuit_breaker/*.py (5 files) | test_circuit_breaker_unit.py |
| 50 | retry/*.py (5 files) | test_retry_strategies.py |
| 51 | constraints/call_coverage.py | test_call_coverage_constraint.py |
| 52 | constraints/capacity.py | test_capacity_constraint.py |
| 53 | constraints/inpatient.py | test_inpatient_constraint.py |
| 54 | constraints/temporal.py | test_temporal_constraint.py |
| 55 | thermodynamics/*.py | test_thermodynamics.py |

---

## Stream C: Frontend Component Tests (15 Tasks)

**Terminals 7-8 | Goal: Cover 40 untested components**

### Current State
- 80 components total
- ~60% tested
- Templates feature: 0% coverage
- Auth utilities: 0% coverage

### Task Breakdown

**Terminal 7: Critical Features (8 tasks)**
| # | Component/Feature | Test File to Create |
|---|------------------|-------------------|
| 56 | auth.ts (18,173 lines) | auth.test.ts |
| 57 | validation.ts (8,544 lines) | validation.test.ts |
| 58 | useAuth hook | useAuth.test.ts |
| 59 | useWebSocket hook | useWebSocket.test.ts |
| 60 | AuthContext | AuthContext.test.tsx |
| 61 | ToastContext | ToastContext.test.tsx |
| 62 | Login page | login.test.tsx |
| 63 | ProtectedRoute (enhanced) | ProtectedRoute.test.tsx |

**Terminal 8: Feature Components (7 tasks)**
| # | Component/Feature | Test File to Create |
|---|------------------|-------------------|
| 64 | Templates feature (9 components) | templates/*.test.tsx |
| 65 | Conflicts feature (5 components) | conflicts/*.test.tsx |
| 66 | Import/Export components | import-export/*.test.tsx |
| 67 | Call Roster (2 missing) | call-roster/*.test.tsx |
| 68 | Admin pages (5 pages) | admin/*.test.tsx |
| 69 | useAdminScheduling hook | useAdminScheduling.test.ts |
| 70 | useAdminUsers hook | useAdminUsers.test.ts |

---

## Stream D: Integration/E2E Scenarios (10 Tasks)

**Terminal 9 | Goal: End-to-end user journey tests**

### Task Breakdown

| # | Scenario | Type |
|---|----------|------|
| 71 | Generate schedule → Validate ACGME → Export | E2E |
| 72 | Create swap request → Auto-match → Execute → Rollback | E2E |
| 73 | Import XLSX → Validate → Seed database | E2E |
| 74 | Faculty absence → Conflict detection → Resolution | E2E |
| 75 | Login → View schedule → Request swap → Logout | E2E |
| 76 | Admin: Create user → Assign role → Verify access | E2E |
| 77 | Resilience: Trigger N-1 → Detect → Recover | Integration |
| 78 | MCP: Call 10 tools in sequence (scheduling workflow) | Integration |
| 79 | Celery: Queue job → Monitor → Complete | Integration |
| 80 | WebSocket: Connect → Subscribe → Receive updates | Integration |

---

## Stream E: Security Sweep (8 Tasks)

**Terminal 10 | Goal: OWASP + HIPAA + OPSEC audit**

### Task Breakdown

| # | Audit Area | Files to Review |
|---|-----------|----------------|
| 81 | SQL Injection review | All routes with db queries |
| 82 | XSS prevention audit | Frontend form handling |
| 83 | Auth bypass testing | routes/auth.py, oauth2.py |
| 84 | RBAC enforcement | All protected endpoints |
| 85 | Rate limiting verification | core/rate_limit.py |
| 86 | PHI exposure scan | All API responses |
| 87 | OPSEC compliance | Logging, error messages |
| 88 | Secret management | .env handling, config.py |

---

## Stream F: Overflow Tasks (12 Tasks)

**Distributed across available capacity**

### Constraint Registration (5 tasks)
| # | Task |
|---|------|
| 89 | Verify all constraints in constraints/ are registered in manager.py |
| 90 | Add missing constraint registrations |
| 91 | Create constraint validation test suite |
| 92 | Document constraint interaction matrix |
| 93 | Add constraint preflight checks |

### Database Optimization (3 tasks)
| # | Task |
|---|------|
| 94 | Identify missing indexes (from HUMAN_TODO) |
| 95 | Create index migration |
| 96 | Benchmark query performance |

### Documentation Sync (4 tasks)
| # | Task |
|---|------|
| 97 | Sync OpenAPI spec with actual endpoints |
| 98 | Update API documentation |
| 99 | Create MCP tool usage guide |
| 100 | Update CHANGELOG with all changes |

---

## Execution Protocol

### Pre-Execution Checklist

1. **Verify repo is clean:**
   ```bash
   git status --ignored | grep -E "\.env|data.*\.json"
   # Should show only gitignored files
   ```

2. **Create context bundles for each stream:**
   ```
   Stream A: CLAUDE.md + mcp-server/ + backend/app/api/routes/
   Stream B: CLAUDE.md + backend/app/services/ + backend/tests/conftest.py
   Stream C: CLAUDE.md + frontend/src/ + frontend/__tests__/
   Stream D: CLAUDE.md + all relevant integration points
   Stream E: CLAUDE.md + docs/security/ + backend/app/core/
   ```

3. **Provide each CCW with:**
   - This plan file
   - Relevant context files
   - Task assignment (10 tasks per terminal)
   - Test patterns from existing tests

### Parallel Execution Pattern

```
Phase 1 (Terminals 1-10 in parallel):
├── Terminal 1: MCP Core Scheduling (tasks 1-10)
├── Terminal 2: MCP Exotic Frontier (tasks 11-20)
├── Terminal 3: Backend Endpoints (tasks 21-30)
├── Terminal 4: Service Tests Critical (tasks 31-40)
├── Terminal 5: Service Tests Integration (tasks 41-48)
├── Terminal 6: Resilience Tests (tasks 49-55)
├── Terminal 7: Frontend Critical (tasks 56-63)
├── Terminal 8: Frontend Features (tasks 64-70)
├── Terminal 9: E2E Scenarios (tasks 71-80)
└── Terminal 10: Security Sweep (tasks 81-88)

Phase 2 (Overflow - any available terminal):
├── Constraint Registration (tasks 89-93)
├── Database Optimization (tasks 94-96)
└── Documentation Sync (tasks 97-100)
```

### Synthesis Protocol

After all terminals complete:
1. Collect all test files → Run full test suite
2. Collect all MCP tools → Test with integration harness
3. Collect security findings → Create remediation PR
4. Update CHANGELOG with all 100 tasks

---

## Success Criteria

| Metric | Current | Target |
|--------|---------|--------|
| MCP Tools Operational | 50/81 (62%) | 81/81 (100%) |
| Backend Service Tests | 10/47 (21%) | 47/47 (100%) |
| Frontend Component Tests | ~60% | 90%+ |
| Constraint Tests | 11/18 (61%) | 18/18 (100%) |
| Resilience Module Tests | 17/44 (39%) | 35/44 (80%) |
| E2E Scenarios | 0 | 10 |
| Security Audit | Ad-hoc | Complete |

---

## Files Modified by This Plan

### Stream A (MCP)
- `mcp-server/src/scheduler_mcp/server.py`
- `mcp-server/src/scheduler_mcp/tools/*.py`
- `backend/app/api/routes/resilience.py`
- `backend/app/api/routes/schedule.py`
- NEW: `backend/app/api/routes/game_theory.py`

### Stream B (Backend Tests)
- NEW: `backend/tests/services/test_*.py` (25 files)
- NEW: `backend/tests/constraints/test_*.py` (7 files)
- NEW: `backend/tests/resilience/test_*.py` (3 files)

### Stream C (Frontend Tests)
- NEW: `frontend/__tests__/lib/auth.test.ts`
- NEW: `frontend/__tests__/lib/validation.test.ts`
- NEW: `frontend/__tests__/hooks/*.test.ts` (4 files)
- NEW: `frontend/__tests__/features/templates/*.test.tsx` (9 files)

### Stream D (E2E)
- NEW: `backend/tests/e2e/test_*.py` (10 files)

### Stream E (Security)
- Updates to routes with security fixes
- NEW: `docs/security/OWASP_AUDIT_RESULTS.md`

---

*Plan created by ORCHESTRATOR | Ready for 10-terminal parallel execution*
