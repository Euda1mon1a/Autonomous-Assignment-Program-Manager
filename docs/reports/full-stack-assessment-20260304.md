# Full-Stack Assessment Report

> **Date:** 2026-03-04 | **Branch:** `main` (HEAD: `5a8d437b`) | **Assessor:** Claude Opus 4.6

---

## Executive Summary

| Layer | Health | Key Metric |
|-------|--------|------------|
| **Backend** | Strong | 530K LOC, 66 constraints, 4 solvers, 860 tests |
| **Frontend** | Strong | 920+ TS files, strict mode, 393 tests, schema-driven types |
| **Infrastructure** | Strong | 8/9 Docker services, 26-phase pre-commit, 20 CI workflows |
| **Documentation** | Excellent | 1,028 docs, 67+ RAG-indexed |

**Overall verdict:** Mature, well-engineered system with strong guardrails. Production-quality scheduling engine, schema-driven frontend, layered infrastructure defenses. Main gaps are A11y compliance (Section 508) and remaining placeholder implementations — both addressable without architectural changes.

---

## 1. Backend (Python 3.11 / FastAPI)

### 1.1 Codebase Metrics

| Metric | Value |
|--------|-------|
| Total Python LOC | 530,607 |
| Core files | 659 |
| Test files | 860 (417,486 LOC) |
| Test-to-code ratio | 0.79:1 |
| Coverage threshold | 70% (fail_under) |

### 1.2 Architecture

```
Routes (95 files)        ← Thin, validation only
  ↓
Controllers (11 files)   ← Request handling
  ↓
Services (165 files)     ← Business logic
  ↓
Models (63 ORM models)   ← Data access (SQLAlchemy 2.0 async)
  ↓
PostgreSQL 15 + asyncpg
```

### 1.3 Component Breakdown

| Component | Files | Purpose |
|-----------|-------|---------|
| API Routes | 95 | REST endpoints |
| Services | 165 | Business logic |
| Pydantic Schemas | 103 | Request/response validation |
| SQLAlchemy Models | 63 | ORM layer |
| Scheduling Engine | 118 | Solver + constraints (81K LOC) |
| Resilience Framework | 104 | Cross-domain resilience (52K LOC) |
| Controllers | 11 | Request handling |

### 1.4 Dependencies

**Core Framework:**

| Package | Version | Status |
|---------|---------|--------|
| FastAPI | 0.128.0 | Current |
| SQLAlchemy | 2.0.45 | Current |
| Pydantic | 2.12.5 | Current |
| Alembic | 1.17.2 | Current |
| asyncpg | 0.31.0 | Current |

**Optimization Solvers:**

| Package | Version | Purpose |
|---------|---------|---------|
| OR-Tools | >=9.8, <9.9 | CP-SAT constraint programming |
| PuLP | >=2.7.0 | Linear programming |
| Pyomo | >=6.7.0 | Algebraic modeling |
| pymoo | >=0.6.0 | Multi-objective optimization |

**AI/ML Integration:**

| Package | Purpose |
|---------|---------|
| anthropic >=0.40.0 | Claude API client |
| sentence-transformers | Local embeddings (RAG) |
| pgvector | Vector search in PostgreSQL |
| scikit-learn | ML utilities |

**Cross-Domain Analytics:**

| Package | Purpose |
|---------|---------|
| pyspc | Statistical Process Control |
| pyworkforce | Erlang C queuing theory |
| ndlib + networkx | Burnout contagion modeling |
| ruptures | Change point detection (PELT) |
| ripser | Persistent homology (TDA) |

**Development Tools:**

| Tool | Version | Status |
|------|---------|--------|
| ruff | 0.14.10 | Active |
| black | 25.12.0 | Active |
| isort | 6.0.1 | Active |
| mypy | 1.19.1 | Active (relaxed) |
| pytest | 9.0.2 | Active |
| bandit | >=1.7.0 | Active |

No outdated or known-vulnerable packages. bcrypt pinned <5.0, defusedxml included.

### 1.5 Database & Migrations

| Metric | Value |
|--------|-------|
| ORM Models | 63 |
| Alembic Migrations | 113 |
| Naming Convention | `YYYYMMDD_description` (64-char limit) |
| Chain Status | Merged (PR #1196), single head |

**Key Models:** Person, Block, Assignment, BlockAssignment, CallAssignment, CallOverride, RotationTemplate, Activity, ActivityRequirement, Absence, FacultyWeeklyTemplate, FacultyWeeklyOverride, PersonAcademicYear, ResilienceMetric.

### 1.6 Scheduling Engine

**File:** `backend/app/scheduling/engine.py` — 5,104 lines, 68 methods, synchronous.

**Solver Phase Flow:**
```
Phase 0: Absence Loading → Availability Matrix
Phase 1: Smart Pairing → Greedy Initialization
Phase 2: Resident Association → Constraint-based Assignment
Phase 3: Faculty Assignment → Supervision Ratio Enforcement
Phase 7: Validation → ACGME Compliance Checking
```

**Algorithms:** `greedy`, `cp_sat`, `pulp`, `hybrid`

**Constraint System:**

| Category | Count | Examples |
|----------|-------|---------|
| Hard Constraints | 20+ | EightyHourRule, OneInSevenRule, SupervisionRatio, OvernightCallGeneration, NightFloatPostCall, PostFMITRecovery, AvailabilityConstraint, FMITMandatoryCall |
| Soft Constraints | 40+ | EscalatingCallEquity (MAD-based, 7x tiered), WeekdayCallEquity, SundayCallEquity, ResidentWeeklyClinic, HalfDayRequirement, IntegratedWorkload |
| **Total** | **66** | **47/51 enabled** |

**Constraint Manager:** 645 lines, dynamic enable/disable + weight tuning at runtime.

**Archetype Enforcement:** Pre-commit hook `scripts/archetype-check.py` (Mind Flayer's Probe) performs AST analysis on constraint files, catching 6 known anti-patterns (ARCH-001 through ARCH-006).

### 1.7 API Surface (95 Route Files)

| Domain | Routes | Examples |
|--------|--------|---------|
| Scheduling | 3 | schedule, scheduler, block_scheduler |
| Assignments | 2 | assignments, half_day_assignments |
| Call Management | 2 | call_assignments, call_overrides |
| Resources | 3 | people, blocks, activities |
| Data I/O | 5 | imports, exports, batch, upload, reports |
| Compliance | 3 | constraints, conflicts, conflict_resolution, audit |
| Admin | 4 | admin_dashboard, admin_block_assignments, admin_users, admin_delete_impact, db_admin |
| Resilience | 2 | resilience, exotic_resilience |
| Analytics | 3 | metrics, fairness, wellness, fatigue_risk |
| AI | 2 | rag, claude_chat |
| Integration | 3 | calendar, webhooks, sessions, sso, gateway_auth |

### 1.8 Resilience Framework (52,124 LOC)

| Module | Paradigm | Source Domain |
|--------|----------|---------------|
| circuit_breaker/ | Netflix Hystrix pattern | Software engineering |
| contingency/ | N-1/N-2 contingency analysis | Power grid planning |
| epidemiology/ | SIR contagion modeling | Epidemiology |
| frms/ | Fatigue Risk Management | Aviation (FAA AC 120-103A) |
| queuing/ | Erlang C workforce optimization | Telecom/call centers |
| spc/ | Statistical Process Control | Manufacturing |
| simulation/ | Monte Carlo scenarios | Finance/operations research |
| thermodynamics/ | Entropy + equilibrium | Physics |
| exotic/ | Advanced patterns | Multi-domain |

Includes: defense-in-depth (nuclear safety, 5-level), hub analysis (network centrality), burnout fire index, catastrophe detection (bifurcation), metastability warnings, unified critical index (composite scoring).

### 1.9 Security Posture

| Control | Status |
|---------|--------|
| JWT httpOnly cookies | Implemented |
| Bcrypt password hashing | Implemented (4.0-5.0) |
| Rate limiting (slowapi) | Implemented |
| SQL injection protection | Fixed (24 vectors, PR #1197) |
| Audit logging | Implemented (activity_log table) |
| Input validation (Pydantic) | Implemented |
| Security linting (bandit) | Configured |
| XML safety (defusedxml) | Implemented |
| Dynamic SQL identifiers | `validate_identifier()` + `validate_search_path()` |

### 1.10 Test Configuration

- **pytest markers:** acgme, slow, integration, unit, resilience, performance, e2e, requires_db, requires_redis, requires_celery
- **conftest.py files:** 8 (root + 7 nested for fixture organization)
- **Fixtures:** FastAPI test client, database, async session

### 1.11 Code Quality

| Metric | Value |
|--------|-------|
| TODO/FIXME comments | 16 |
| mypy errors (ratcheting) | ~1,138 (down from ~4,250) |
| Archived dead code | 7 modules (2 service, 5 auth) |
| Dead code removed | 27,598 lines (PR #1198) |

---

## 2. Frontend (Next.js 15 / React 18 / TypeScript)

### 2.1 Codebase Metrics

| Metric | Value |
|--------|-------|
| Framework | Next.js 15.5.12 + React 18.2.0 |
| Total TS/TSX files | 920+ |
| Components (.tsx) | 660 |
| Hooks | 77 |
| Type files | 27 |
| Test files | 393 (184 unit + 158 integration + 44 E2E + 7 legacy) |
| Coverage threshold | 60% |

### 2.2 TypeScript Configuration

| Setting | Value |
|---------|-------|
| `strict` | true |
| `noEmit` | true |
| `isolatedModules` | true |
| `moduleResolution` | bundler |
| `target` | ES2017 |
| Path aliases | `@/*` → `./src/*` |

### 2.3 Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| Next.js | 15.5.12 | App Router framework |
| React | 18.2.0 | UI library |
| TanStack Query | 5.90.14 | Data fetching/caching |
| Axios | 1.13.5 | HTTP client |
| TailwindCSS | 3.4.1 | Utility CSS |
| Zod | 4.3.2 | Schema validation |
| Framer Motion | 12.23.26 | Animations |
| Recharts | 3.6.0 | Charts |
| React-Three-Fiber | 8.18.0 | 3D visualization |
| xlsx | 0.20.2 | Excel I/O |
| date-fns | 4.1.0 | Date utilities |

**Dev:** Jest 29.7.0, Playwright 1.58.2, ESLint 8.57.0, openapi-typescript 7.0.0, MSW 2.12.4

### 2.4 API Type System

| Metric | Value |
|--------|-------|
| Generated types file | `src/types/api-generated.ts` |
| File size | 2.2 MB (73,284 lines) |
| Generator | `openapi-typescript` from backend OpenAPI spec |
| Freshness check | `npm run generate:types:check` |
| Pre-commit enforcement | `modron-march.sh` |

**Conversion boundary:** Axios interceptor in `src/lib/api.ts`:
- Request: camelCase → snake_case (body only)
- Response: snake_case → camelCase (body only)
- URL query params: snake_case (not intercepted)
- Enum values: snake_case (not intercepted)

### 2.5 Component Architecture

**Largest components (LOC):**

| Component | Lines | Domain |
|-----------|-------|--------|
| RotationEditor.tsx | 903 | Rotation editing |
| RotationWeeklyGrid.tsx | 900 | Grid display |
| FacultyWeeklyEditor.tsx | 761 | Faculty templates |
| FacultyMatrixView.tsx | 759 | Faculty assignments |
| BulkWeeklyPatternModal.tsx | 703 | Bulk operations |
| FacultyInpatientWeeksView.tsx | 689 | Inpatient view |
| ResidentAcademicYearView.tsx | 676 | Academic tracking |
| WeeklyRequirementsEditor.tsx | 650 | Requirements |
| WeeklyGridEditor.tsx | 645 | Grid editing |
| BlockAssignmentImportModal.tsx | 639 | Excel import |

**Component domains:** CommandPalette, absence, admin, analytics, common, compliance, dashboard, data-display, form, game-theory, layout, people, rag, resilience, schedule, scheduling.

### 2.6 Custom Hooks

| Hook | Lines | Domain |
|------|-------|--------|
| useProcedures | 1,076 | Procedure credentialing |
| useAbsences | 983 | Leave tracking |
| useSwaps | 867 | Swap management |
| useWebSocket | 840 | Real-time updates |
| useResilience | 813 | Resilience metrics |
| useSchedule | 754 | Schedule generation |
| usePeople | 748 | Resident/faculty data |
| useClaudeChat | 563 | AI chat integration |

**Categories:** Data fetching, real-time, business logic, admin, UI state. 19 hook test files.

### 2.7 ESLint & Code Quality

| Rule | Level | Purpose |
|------|-------|---------|
| `@typescript-eslint/naming-convention` | warn | Enforce camelCase properties |
| `@typescript-eslint/no-unused-vars` | warn | Catch unused variables |
| `@typescript-eslint/no-explicit-any` | warn | Discourage `any` |
| `react-hooks/exhaustive-deps` | warn | Missing useEffect deps |
| `jsx-a11y/interactive-supports-focus` | warn | Keyboard accessibility |
| `jsx-a11y/click-events-have-key-events` | warn | Click needs keyboard |

**ESLint warnings:** ~473 (down 72.9% after ratchet sprint, PRs #1246-#1249)

### 2.8 Test Structure

| Type | Count | Location |
|------|-------|----------|
| Unit tests | 184 | `src/**/*.test.{ts,tsx}` |
| Integration tests | 158 | `__tests__/features/`, `__tests__/contexts/` |
| E2E (Playwright) | 44 | `e2e/tests/**/*.spec.ts` |
| Legacy E2E | 7 | `e2e/*.spec.ts` |
| **Total** | **393** | |

### 2.9 Build Configuration

| Setting | Value |
|---------|-------|
| Output | standalone (Docker-ready) |
| Strict mode | true |
| Compression | gzip enabled |
| API proxy | `/api/:path*` → `BACKEND_URL/api/:path*` |
| ESLint on build | Fail on errors |
| TypeScript on build | Fail on type errors |
| `poweredByHeader` | false (security) |

### 2.10 Tailwind Configuration

- Dark mode: `class` strategy
- Custom medical colors: clinic, inpatient, call, leave, scrub, sterile
- Fonts: Inter (sans), JetBrains Mono (mono)
- Plugins: None (vanilla Tailwind)

---

## 3. Infrastructure

### 3.1 Docker Composition (9 Services)

| Service | Image | Port | Status |
|---------|-------|------|--------|
| PostgreSQL | pgvector:pg15 | 5432 | Active |
| Redis | redis:7.4.2-alpine | 6379 | Active |
| FastAPI (backend) | Custom | 8000 | Active |
| Celery Worker | Custom | — | Active (6 queues) |
| Celery Beat | Custom | — | Active |
| Next.js (frontend) | Custom | 3000 | Active |
| MCP Server | Custom | 8080 | Active |
| n8n (workflow) | n8nio/n8n:1.121.0 | — | **Disabled** (CVE-2026-21858) |

All active services have health checks configured. MCP runs with `no-new-privileges:true`, CPU limit 1, memory limit 2G.

### 3.2 MCP Server

| Metric | Value |
|--------|-------|
| Python files | 80 |
| Tool modules | 42 |
| Armory modules | 8 |
| Placeholder tools | 11 (return synthetic data) |
| Transport | HTTP (Streamable HTTP) |

**Tool domains:** Scheduling validation, swap management, ACGME compliance, analytics, resilience, fatigue risk (FRMS), contingency analysis, circuit breakers, RAG search.

### 3.3 Pre-Commit Hooks (26 Phases)

| Phase | Hook | Purpose |
|-------|------|---------|
| 1-2 | PII scan, gitleaks, ruff | Security + formatting |
| 3 | MyPy | Type checking (non-blocking) |
| 4-7 | File quality, bandit, ESLint | Code quality |
| 8-9 | Migration validation, Lich's Phylactery | DB safety + schema snapshots |
| 10-11 | Conventional commits, YAML lint | Standards |
| 12-23 | Domain-specific | ACGME, resilience, swaps, schedule integrity, docs, constraints |
| 24 | D&D hooks (parallel) | Couatl Killer, Beholder Bane, Gorgon's Gaze |
| 25 | Modron March | OpenAPI type contract enforcement |
| 26 | Githyanki Gatekeeper | Pre-push safety for main |

### 3.4 Scripts (192 Files)

| Category | Count |
|----------|-------|
| Validation hooks | 24 |
| Database management | 12 |
| CI/CD & deployment | 8 |
| Data processing | 6 |
| Development utilities | 8 |
| Linting wrappers | 6 |

### 3.5 CI/CD Workflows (20 GitHub Actions)

| Workflow | Trigger |
|----------|---------|
| `ci.yml` (main pipeline) | Push/PR |
| `ci-lite.yml` (fast subset) | PRs |
| `ci-comprehensive.yml` (full suite) | main branch |
| `security.yml` (SAST, SCA) | Push/PR |
| `quality-gates.yml` | PR |
| `pii-scan.yml` | PR |
| `claude.yml` (Claude Code integration) | Manual |
| `codex-autofix.yml` | On-demand |
| `cd.yml` (deployment) | On-demand |
| `release.yml` | Tag push |
| `load-tests.yml` | Manual |
| `docs.yml` / `docs-link-check.yml` | Push / Daily |
| Others (8) | Various |

### 3.6 Environment

`.env.example` documents 50+ variables across: Database, Security (SECRET_KEY, JWT), Redis, API (CORS, rate limiting), Telemetry (OpenTelemetry), Frontend, MCP. Local dev uses macOS Keychain for secrets.

---

## 4. Documentation (1,028 Files)

| Directory | Files | Purpose |
|-----------|-------|---------|
| archived/ | 179 | Superseded docs, audit logs, triage reports |
| perplexity-uploads/ | 129 | AI analysis sessions (8/8 complete) |
| architecture/ | 111 | System design, ADRs, resilience framework |
| planning/ | 80 | Roadmaps, tech debt, priority lists |
| development/ | 79 | Best practices, agent skills, MCP setup |
| api/ | 58 | OpenAPI specs, endpoint docs |
| research/ | 53 | Cross-disciplinary studies (10+ bridges) |
| guides/ | 40 | Admin manual, user guide, troubleshooting |
| scratchpad/ | 25 | Session notes, analysis drafts |
| rag-knowledge/ | 24 | RAG knowledge base (semantic search) |

**CLAUDE.md:** 670 lines of project instructions covering tech stack, code style, naming conventions (D&D themed), security, AI rules of engagement (Auftragstaktik), MCP tool requirements, permission tiers.

---

## 5. Technical Debt

### 5.1 By Priority

| Priority | Total | Resolved | Open |
|----------|-------|----------|------|
| **P0 Critical** | 2 | 2 | 0 |
| **P1 High** | 7 | 6 | 1 |
| **P2 Medium** | 3 | 0 | 3 |
| **P3 Low** | 1 | 1 | 0 |

### 5.2 Open Items

| ID | Priority | Description | Impact |
|----|----------|-------------|--------|
| A11y warnings | P2 | 47 jsx-a11y violations (44 click-events, 3 focus) | Section 508 non-compliance risk |
| MCP placeholders | P2 | 11 tools return synthetic data | Feature gaps in advanced analytics |
| Failing tests | P2 | 5 pre-existing failures in scheduling/service | CI noise |

### 5.3 Ratchet Progress

| Metric | Before | After | Reduction |
|--------|--------|-------|-----------|
| ESLint warnings | ~1,730 | 473 | 72.9% |
| mypy errors | ~4,250 | 1,138 | 72.9% (coincidentally identical %) |
| TODOs (backend) | — | 16 | Tracked |

---

## 6. Roadmap Status

### 6.1 Current Release: v1.0.0 (Production Ready)

### 6.2 In Progress: v1.0.5 (March 2026)

| Item | Status |
|------|--------|
| 17 constraints re-enabled (47/51 total) | Done |
| Call equity tuning + overnight call generation | Done |
| Integrated workload constraint restored | Done |
| XLSX export TAMC format matching | Done |
| ESLint ratchet (72.9% reduction) | Done |
| mypy ratchet (72.9% reduction) | Done |
| Mind Flayer's Probe (constraint archetype hook) | Done |

### 6.3 Remaining Last-Mile Items

- Call spacing graduated penalty
- C30/C40 PGY booking rule
- Night Float continuity touchpoint
- Final Wednesday continuity loss constraint
- HC/CLC template immunity
- SM deterministic preload

### 6.4 Frontend Rewiring (Post-Backend)

- Phase 0: Triage broken hooks
- Phase 1-5: Fix hooks → draft workflow → ARO UI → import/export → cosmetic

---

## 7. Risk Register

| # | Risk | Severity | Likelihood | Mitigation |
|---|------|----------|------------|------------|
| 1 | **Section 508 / A11y non-compliance** | High | High | 47 jsx-a11y warnings. Government/military apps require Section 508. Schedule bulk fix before production deployment. |
| 2 | **Placeholder frontend hooks** | Medium | Medium | 8 hooks with `// TODO: real API call`. Could fail silently if reached in production flows. Audit and stub or implement. |
| 3 | **Large component complexity** | Medium | Low | 10 components >640 LOC. Increases maintenance burden. Split during frontend rewiring phase. |
| 4 | **mypy strictness gap** | Low | Low | 1,138 errors remain. Ratchet is working (72.9% reduction). Continue gradual tightening. |
| 5 | **Synchronous engine** | Low | Low | Engine runs in threadpool. Acceptable for current load. Monitor if concurrent schedule generation increases. |
| 6 | **n8n disabled (CVE)** | Low | Low | Workflow automation offline pending security patch. No critical dependency on n8n for core scheduling. |

---

## 8. Scorecard

| Category | Grade | Notes |
|----------|-------|-------|
| **Architecture** | A | Clean layered design, constraint manager, pluggable solvers |
| **Code Quality** | A- | Strict TS, ruff/black, pre-commit hooks; mypy still relaxed |
| **Testing** | A- | 1,253 total test files; 5 pre-existing failures |
| **Security** | A | JWT, bcrypt, rate limiting, SQL injection fixed, audit logging, bandit |
| **Documentation** | A | 1,028 files, RAG-indexed, comprehensive CLAUDE.md |
| **Infrastructure** | A- | 8/9 Docker services, 20 CI workflows, 26-phase hooks; n8n down |
| **ACGME Compliance** | A | Hard constraints enforced, validator active, archetype hooks |
| **Accessibility** | C | 47 jsx-a11y warnings, Section 508 risk |
| **Technical Debt** | B+ | P0/P1 resolved, ratchets working, 3 P2 items open |
| **Deployment Readiness** | B+ | Pre-production; CI partially disabled, frontend rewiring pending |

**Overall: B+ / A-** — Production-quality backend with strong guardrails. Frontend needs A11y remediation and hook completion before government deployment.

---

*Generated by Claude Opus 4.6 full-stack assessment. Three parallel agents scanned backend (659 files), frontend (920+ files), and infrastructure (192 scripts, 20 workflows, 1,028 docs).*
