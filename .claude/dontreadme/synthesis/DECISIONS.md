# Architectural Decision Record (ADR)

**Purpose:** Track major architectural decisions, their context, and rationale to prevent revisiting settled debates.

**Format:** Lightweight ADR - Context, Decision, Consequences

**Last Updated:** 2025-12-31 (Session 37)

---

## Active Decisions

### ADR-001: FastAPI + SQLAlchemy 2.0 (Async)

**Date:** 2024-12 (Project inception)

**Context:**
- Medical residency scheduling requires real-time responsiveness
- ACGME compliance checks are computationally expensive
- Multiple users may modify schedules concurrently

**Decision:**
- Use FastAPI with async/await throughout
- Use SQLAlchemy 2.0+ with AsyncSession
- PostgreSQL as primary database

**Consequences:**
- ✅ High concurrency handling
- ✅ Type hints + Pydantic validation
- ✅ OpenAPI docs auto-generated
- ⚠️ All code must be async (no sync DB calls)
- ⚠️ Learning curve for async SQLAlchemy

**Status:** ✅ Adopted

---

### ADR-002: Constraint Programming (OR-Tools) for Scheduling

**Date:** 2024-12 (Project inception)

**Context:**
- Schedule generation is NP-hard
- ACGME rules are hard constraints (must satisfy)
- Preferences are soft constraints (optimize)

**Decision:**
- Use Google OR-Tools CP-SAT solver
- Model ACGME rules as hard constraints
- Model preferences as soft constraints with weighted objectives

**Consequences:**
- ✅ Provably compliant schedules (or proof of infeasibility)
- ✅ Multi-objective optimization (coverage, balance, preferences)
- ⚠️ Solver can timeout on complex schedules
- ⚠️ Constraint encoding is complex

**Status:** ✅ Adopted

**See Also:** `docs/architecture/SOLVER_ALGORITHM.md`

---

### ADR-003: MCP Server for AI Integration

**Date:** 2025-12 (Session 8)

**Context:**
- Need AI agent access to scheduling operations
- Want to avoid direct database manipulation
- Must maintain audit trails for AI actions

**Decision:**
- Build FastMCP server with 29+ scheduling tools
- Run MCP server in Docker container
- AI agents call tools via MCP protocol

**Consequences:**
- ✅ Safe AI interaction (no direct DB access)
- ✅ Audit trails for all AI actions
- ✅ Composable tools (agents orchestrate)
- ⚠️ Additional infrastructure complexity
- ⚠️ MCP server must be deployed alongside app

**Status:** ✅ Adopted

**Implementation:** `mcp-server/`

---

### ADR-004: Resilience Framework - Cross-Disciplinary Approach

**Date:** 2025-12 (Sessions 15-20)

**Context:**
- Burnout is epidemic in medical residencies
- Traditional metrics miss early warning signs
- Need proactive detection, not reactive response

**Decision:**
- Apply cross-industry resilience concepts to scheduling
- 5-tier framework: Core → Strategic → Analytics → Observability → Exotic
- Integrate diverse disciplines: queuing theory, epidemiology, materials science, seismology

**Concepts:**
- **Tier 1:** 80% utilization threshold, N-1/N-2 contingency, defense in depth
- **Tier 3:** SPC monitoring, Erlang coverage, SIR epidemiology, burnout Rt
- **Tier 5:** Metastability detection, spin glass models, circadian PRC

**Consequences:**
- ✅ Early warning system (detect burnout precursors)
- ✅ Evidence-based thresholds (queuing theory)
- ✅ Multi-scale detection (STA/LTA, PRC, fire index)
- ⚠️ Complexity (requires cross-disciplinary expertise)
- ⚠️ Computational cost (run resilience checks every 15 min)

**Status:** ✅ Adopted

**Reference:** `docs/architecture/cross-disciplinary-resilience.md`, `docs/architecture/EXOTIC_FRONTIER_CONCEPTS.md`

---

### ADR-005: Next.js 14 App Router (Frontend)

**Date:** 2024-12 (Project inception)

**Context:**
- Need server-side rendering for SEO
- Want streaming and progressive enhancement
- React Server Components simplify data fetching

**Decision:**
- Use Next.js 14 with App Router
- TanStack Query for client-side state
- TailwindCSS for styling

**Consequences:**
- ✅ Server-side rendering (fast initial load)
- ✅ Type-safe routing
- ✅ Automatic code splitting
- ⚠️ App Router is newer paradigm (less mature ecosystem)
- ⚠️ Server vs client components require careful separation

**Status:** ✅ Adopted

---

### ADR-006: Swap System with Auto-Matching

**Date:** 2025-01 (Session 11)

**Context:**
- Faculty need to exchange shifts
- Manual matching is time-consuming
- Must maintain ACGME compliance after swaps

**Decision:**
- Build swap request + auto-matcher
- Matcher finds compatible candidates (same rotation, similar experience)
- All swaps validated for ACGME compliance before execution

**Consequences:**
- ✅ Reduces coordinator burden
- ✅ Maintains compliance automatically
- ✅ Audit trail for all swaps
- ⚠️ Matcher complexity (constraint satisfaction)
- ⚠️ Edge cases (3-way swaps, absorbs)

**Status:** ✅ Adopted

**Implementation:** `backend/app/services/swap_matcher.py`

---

### ADR-007: Monorepo with Docker Compose

**Date:** 2024-12 (Project inception)

**Context:**
- Backend, frontend, MCP server, database, Redis all required
- Local development should mirror production
- Want reproducible environments

**Decision:**
- Monorepo structure: `backend/`, `frontend/`, `mcp-server/`, `load-tests/`
- Docker Compose for orchestration
- Shared `docker-compose.yml` for all services

**Consequences:**
- ✅ Single clone for full stack
- ✅ Consistent environments (dev = staging = prod)
- ✅ Easy onboarding (docker-compose up)
- ⚠️ Large repo (harder to navigate)
- ⚠️ Docker required for local development

**Status:** ✅ Adopted

---

### ADR-008: Slot-Type Invariants for Credentials

**Date:** 2025-12 (Session 29)

**Context:**
- Admin burden: tracking who has which certifications
- Assignments fail when credentials expire mid-rotation
- Need proactive reminders, not reactive failures

**Decision:**
- Define credential requirements per slot type (invariants)
- Hard constraints (must have): HIPAA, Cyber, N95 fit
- Soft constraints (penalty if missing): Expiring soon
- Dashboard shows "next block failures" and "expiring in X days"

**Consequences:**
- ✅ Prevents invalid assignments at schedule generation
- ✅ Proactive renewal reminders (30/60/90 days)
- ✅ Reduces admin burden (automated checks)
- ⚠️ Requires credential tracking infrastructure
- ⚠️ Initial setup burden (define invariants per slot type)

**Status:** ✅ Adopted

**Reference:** `docs/constraints/SLOT_TYPE_INVARIANTS.md`

---

### ADR-009: Time Crystal Scheduling (Anti-Churn)

**Date:** 2025-12 (Session 20)

**Context:**
- Schedule regeneration causes unnecessary churn
- Residents dislike frequent changes to stable schedules
- Need to minimize edits while maintaining compliance

**Decision:**
- Add anti-churn objective to solver
- Detect subharmonic cycles (7d, 14d, 28d ACGME windows)
- Stroboscopic checkpoints (state advances at discrete boundaries)
- Rigidity scoring (0.0-1.0) measures schedule stability

**Consequences:**
- ✅ Reduces schedule volatility
- ✅ Residents prefer stable schedules (higher satisfaction)
- ✅ Solver can warm-start from previous solution
- ⚠️ May sacrifice optimality for stability
- ⚠️ Requires previous schedule as input

**Status:** ✅ Adopted

**Reference:** `docs/architecture/TIME_CRYSTAL_ANTI_CHURN.md`

---

### ADR-010: Pytest + Jest Testing Strategy

**Date:** 2024-12 (Project inception)

**Context:**
- Need high test coverage for medical safety
- Backend and frontend require different testing approaches

**Decision:**
- Backend: pytest with async fixtures
- Frontend: Jest + React Testing Library
- Integration tests for critical paths
- Target 80% coverage minimum, 90%+ for critical paths

**Consequences:**
- ✅ High confidence in deployments
- ✅ Regression detection
- ✅ Documentation via tests
- ⚠️ Test maintenance burden
- ⚠️ Slow CI (tests take 5+ minutes)

**Status:** ✅ Adopted

---

## Rejected Decisions

### REJ-001: GraphQL Instead of REST

**Date:** 2024-12 (Evaluated, rejected)

**Context:** Considered GraphQL for flexible querying

**Decision:** Rejected in favor of REST

**Rationale:**
- REST + Pydantic schemas simpler
- OpenAPI docs auto-generated with FastAPI
- GraphQL adds complexity without clear benefit for this use case

---

### REJ-002: Celery for Schedule Generation

**Date:** 2025-01 (Evaluated, rejected)

**Context:** Considered offloading schedule generation to Celery

**Decision:** Rejected, use synchronous solver calls

**Rationale:**
- Schedule generation is interactive (user waits for result)
- OR-Tools solver is fast enough (<30 seconds)
- Celery adds complexity for minimal benefit
- **Update:** Celery adopted for resilience checks (periodic background tasks), not schedule generation

---

## Decision Review Process

**When to Create ADR:**
- Major technology choice (framework, database, architecture)
- Significant design pattern adoption
- Rejection of common approach (document why)

**ADR Lifecycle:**
1. **Proposed:** Under discussion
2. **Accepted:** Decision made, implementation started
3. **Adopted:** Fully implemented and in use
4. **Deprecated:** No longer recommended (but may still exist)
5. **Superseded:** Replaced by newer ADR

**Review Cadence:** Quarterly or when revisiting major decisions

---

**See Also:**
- `.claude/dontreadme/synthesis/PATTERNS.md` - Recurring implementation patterns
- `.claude/dontreadme/synthesis/LESSONS_LEARNED.md` - Session insights
- `CLAUDE.md` - Project guidelines
