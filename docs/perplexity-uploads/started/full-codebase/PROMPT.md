# FULL CODEBASE AUDIT: Military Residency Scheduling System (AAPM)
# For: Perplexity Computer (Deep Research + Code Analysis)
# Stack: FastAPI + SQLAlchemy 2.0 (async) + PostgreSQL 15 + OR-Tools CP-SAT 9.8 + Next.js 14
# Scale: ~12 residents, ~8 faculty, 13 blocks/year (~28 days each), ~4,032 binary vars/block

---

## WHAT YOU'RE LOOKING AT

This upload contains the **entire production codebase** of a military family medicine residency scheduling system, minus only the resilience framework (104 files, covered in prior research) and analytics (10 files, signal processing). Everything else is here.

### File Manifest

| File | Size | Contents |
|------|------|----------|
| `backend_source.py` | 15MB | All 1,200+ backend Python files merged (models, schemas, services, scheduling engine, constraints, API routes, auth, middleware, core) |
| `backend_tests.py` | 14MB | All 945 test files merged (unit, integration, service, scheduling tests) |
| `frontend_wiring.ts` | 5.5MB | Frontend API layer: 55 TanStack Query hooks, 6 API modules, axios client, auth, 73K-line auto-generated TypeScript types |
| `architecture_docs.md` | 2.2MB | All 101 architecture decision docs |
| `migrations.py` | 500KB | All 110 Alembic database migrations |
| `prior_research_results.md` | 300KB | Results from 6 completed specialist research sessions (see below) |

**Not included:** Frontend presentational components (React/TSX that renders data from hooks — 222 files, purely UI), node_modules, .venv, .git, resilience/ (covered in exotic research results), analytics/ (signal processing, tangential).

### Prior Research Already Completed (in prior_research_results.md)

Six specialist Perplexity Computer sessions have already completed. Their full results are included. Do NOT re-derive these findings — build on them:

1. **Full-Stack Audit:** CP-SAT weight sweep (2,100 configs), Excel import chaos monkey (65 test files, 3 bugs), ACGME regulatory intelligence (15 findings), constraint research (5 recs), security audit (35 findings: 10 critical), API contract audit (94 routes, 65 mismatches)
2. **Exotic Physics Research:** Betweenness centrality, burstiness analysis, natural connectivity, percolation thresholds, ACO warm-start, CMA-ES bilevel weight optimization — full implementation code provided
3. **OR-Tools 9.8→9.12 Migration:** Changelog, API compatibility (PEP 8 rename), hint system evolution (v9.12 fixes hint preservation), behavioral changes, new features, migration checklist
4. **Section 508 Accessibility:** Landmarks/headings, keyboard nav, ARIA patterns, drag-and-drop, data viz, color contrast, forms/errors, remediation priority
5. **Competitive Intelligence:** Market sizing (13,762 ACGME programs, 167K trainees, $1.3B TAM), vendor deep dives (Amion, QGenda, MedHub, etc.), whitespace analysis
6. **PostgreSQL 15 Tuning:** 76 query patterns cataloged, index gap analysis (24 new indexes recommended), EXPLAIN plan predictions, connection pool tuning, partial/expression indexes, materialized views, monitoring config

---

## YOUR MISSION

You have something no prior session had: **the complete picture**. Each prior session saw 5-10 files in isolation. You see everything. Your job is to find what they missed.

### SECTION 1: Cross-Cutting Architecture Audit

**Goal:** Identify architectural issues that only become visible when you see the entire codebase at once.

1. **Dead code & orphan modules** — Find backend services/models/routes that exist but are never imported or called. The codebase grew fast; there are likely entire features that were started but never wired up.
2. **Circular dependency risks** — Trace import chains across the 1,200+ backend files. Identify any circular imports or tightly-coupled module clusters.
3. **Inconsistent patterns** — The codebase has multiple authors (human + AI). Find places where the same thing is done 3 different ways (e.g., error handling, auth checks, pagination, transaction management).
4. **Schema-code drift** — Compare the SQLAlchemy models in `backend_source.py` against the Alembic migrations in `migrations.py`. Are there model columns that have no migration? Migrations that reference tables not in the models?

### SECTION 2: API Contract Integrity

**Goal:** The prior audit found 65 route mismatches. With the full codebase + frontend wiring, do a complete contract verification.

1. **Route-to-hook mapping** — For every FastAPI route in the backend, find the corresponding frontend hook that calls it. List any routes with NO frontend consumer (backend-only or dead).
2. **Type contract verification** — Compare the Pydantic response schemas in `backend_source.py` against the TypeScript types in `frontend_wiring.ts` (the `api-generated.ts` section). Find any fields that exist on one side but not the other.
3. **Error contract** — How does the backend return errors (HTTPException, custom exceptions, validation errors)? How does the frontend parse them (error handlers in `lib/`)? Are they aligned?
4. **WebSocket contracts** — Find all WebSocket endpoints and their frontend consumers. Verify message format alignment.

### SECTION 3: Test Coverage Gap Analysis

**Goal:** With 945 test files and all source code, identify what's NOT tested.

1. **Untested services** — List every service class in `backend_source.py` and check if it has a corresponding test in `backend_tests.py`. Flag services with 0 tests.
2. **Untested routes** — List every API route and check for route-level tests.
3. **Untested edge cases** — For the scheduling engine and constraint system specifically, identify edge cases that have no test (e.g., block boundary conditions, PGY transitions, leave spanning blocks).
4. **Test quality** — Are tests actually asserting meaningful things, or are there tests that just check `response.status_code == 200` without verifying the response body?

### SECTION 4: The Annual Leap — Implementation Design

**Goal:** With the full codebase visible, design the concrete implementation for transforming from block-scoped to annual-scoped scheduling. Prior sessions identified 5 components:

1. **`person_academic_years` migration** — You can see the existing `PersonAcademicYear` model AND all code that reads `Person.pgy_level`. Write the exact migration SQL, the seed query, and list every file that needs to switch from `Person.pgy_level` to `PersonAcademicYear`.
2. **Faculty call equity YTD** — You can see `call_equity.py` (the current constraint) AND `base.py` (the SchedulingContext) AND `engine.py` (where context is built). Write the exact code changes: where `prior_calls` gets added, where it's hydrated, where it's injected into the solver.
3. **Cross-block leave continuity** — You can see `absence.py` (model), `half_day_import_service.py` (import), and `admin_block_assignments.py` (the TODO placeholder). Design the complete data flow.
4. **Cross-block 1-in-7 boundary** — You can see `acgme_compliance_engine.py` and `longitudinal_validator.py`. Design the sliding window that crosses boundaries.
5. **YTD_SUMMARY sheet** — You can see `canonical_schedule_export_service.py` and the architecture doc. Design the implementation.

For each component: specify exact file paths, function names, line-number-level insertion points, and the code to add/modify.

### SECTION 5: Security Deep Dive

**Goal:** The prior audit found 10 critical and 9 high security issues but only saw 6 files. With the full codebase:

1. **Auth coverage map** — List every route and whether it has auth middleware. The prior audit found 41+ unguarded endpoints — verify and extend that count with the full route set.
2. **Input validation gaps** — Find all places where user input flows into database queries, file operations, or shell commands without validation.
3. **Secret handling** — Trace how secrets (JWT keys, DB credentials, API keys) flow through the codebase. Are they ever logged, returned in responses, or stored in plaintext?
4. **OPSEC risks** — This is a military medical system. Find any code that could leak operational information (duty schedules, deployment data, personnel assignments) through error messages, logs, or API responses.

### SECTION 6: Performance & Scalability

**Goal:** The PG tuning session analyzed 6 service files. With the full codebase:

1. **N+1 query patterns** — Find all places where a loop executes individual DB queries instead of batch queries. The prior session found some; find the rest.
2. **Missing indexes** — The prior session recommended 24 new indexes based on 6 files. With all service/repository code visible, are there additional query patterns that need indexes?
3. **Memory risks** — Find any code that loads unbounded result sets into memory (e.g., `select all` without pagination for tables that could grow large).
4. **Concurrency issues** — Find any shared mutable state, race conditions in async code, or transaction isolation issues.

---

## OUTPUT FORMAT

Produce a single comprehensive report with:

1. **Executive summary** — Top 10 findings across all sections, ranked by impact
2. **Per-section findings** — Each with severity (CRITICAL/HIGH/MEDIUM/LOW), affected files, and recommended fix
3. **Cross-reference table** — Map each finding to related prior research findings (e.g., "this confirms PG tuning finding #7" or "this contradicts exotic research assumption X")
4. **Implementation priority matrix** — All findings ranked by (impact × effort⁻¹), grouped into:
   - **Do now** (high impact, low effort)
   - **Plan next sprint** (high impact, high effort)
   - **Backlog** (low impact)
   - **Won't fix** (not worth the effort at current scale)

Title the report: **"AAPM Full Codebase Audit — Cross-Cutting Analysis"**

The report should be directly actionable by a Claude Code agent. Include file paths, function names, and line numbers where possible.
