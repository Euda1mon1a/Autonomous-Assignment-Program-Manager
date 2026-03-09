# TODO — Actionable Items

> **Updated:** 2026-03-09 (PR reviews, mypy zero, TS test fixes, backlog audit)
> **Source:** Extracted from architecture docs, planning docs, code TODOs, and Explore agent audit.
> **Companion:** `docs/planning/ROADMAP.md` (macro vision), `docs/planning/TECHNICAL_DEBT.md` (debt tracker)

---

## P0 — Critical / Blocking

- [ ] **PII in git history** — Resident names in deleted files still in repo history. Requires `git filter-repo` + force push. All collaborators must re-clone after. **Human-only.** See `docs/security/PII_AUDIT_LOG.md`.

- [ ] **Track A: PGY Graduation Rollover (July 1 deadline)** — `Person.pgy_level` is not academic-year scoped. Updating it on July 1 corrupts historical ACGME queries. Migration exists (`20260224_person_ay.py`), Alembic heads merged (PR #1196), `_sync_academic_year_call_counts()` implemented (PR #1199). **Remaining:**
  1. Apply migration: `alembic upgrade head` (requires running DB)
  2. Migrate 67+ consumer files from `Person.pgy_level` → `PersonAcademicYear` per-AY reads
  3. Create graduation rollover logic for July 1
  - **Doc:** `docs/architecture/excel-stateful-roundtrip-roadmap.md` (Track A, lines 240-312)

## P1 — High / This Sprint

### Annual Rotation Optimizer (ARO) — Frontend UI

> Backend fully wired (PR #1276): DB models, schemas, service, API, migration. Solver core 48/48 tests.

- [x] **ARO DB models** — `AnnualRotationPlan` + `AnnualRotationAssignment` + migration (PR #1276)
- [x] **ARO Pydantic schemas** — Request/response models for plan CRUD, optimize, publish (PR #1276)
- [x] **ARO service layer** — create_plan → import_leave → optimize → approve → publish (PR #1276)
- [x] **ARO API routes** — REST endpoints under `/api/v1/annual-planner/plans/...` (PR #1276)
- [x] **ARO rotation mapping** — `publish_plan()` resolves rotation_template_id + conflict handling (PR #1276)
- [ ] **ARO Frontend UI** — `/hub/annual-planning` page (blocked on frontend sprint)
- **Doc:** `docs/architecture/ANNUAL_ROTATION_OPTIMIZER.md`

### Excel Pipeline — Stateful Roundtrip

> Phases 1–3 and 4a/4b complete. Phase 4c (provenance comments) deferred.

- [x] **Phase 1: Phantom Database** — `__SYS_META__` veryHidden sheet with metadata JSON (PRs #1262-#1264)
- [x] **Phase 2: UUID Anchoring** — `__ANCHORS__` + `__BASELINE__` sheets with person_id, row_hash (PRs #1262-#1264)
- [x] **Phase 3: Data Validation** — `__REF__` sheet + Named Ranges + DataValidation dropdowns (PRs #1262-#1264)
- [x] **Phase 4a: Dynamic CF** — CellIsRule per activity code (PRs #1262-#1264)
- [x] **Phase 4b: Leave formula** — COUNTIF LV column formula (PRs #1262-#1264)
- [ ] **Phase 4c: Provenance comments** — Override provenance comments on hand-jammed cells. Deferred.
- **Doc:** `docs/architecture/excel-stateful-roundtrip-roadmap.md`

### Scheduling Engine

- [ ] **CP-SAT FMIT Fri/Sat call verification** — Code exists in `overnight_call.py`. Needs manual verification that Fri/Sat call appears in `call_assignments` after regeneration + PCAT/DO correctness check.

### Infrastructure

- [x] **mypy errors** — 3,991→0. PR #1272 (4k→3), PR #1275 (3→0). Zero errors across 1,289 source files.
- [x] **TypeScript compilation errors** — 97→0 across 28 test files. PR #1275.
- [x] **Test suite cleanup** — 552 issues→0. 8,302 tests passing. PR #1273.
- [x] **UX audit round 3** — 12 of 18 findings fixed (2 critical, 6 high, 4 medium). PRs #1272, #1274.

## P2 — Medium / This Month

### Schema Hardening

- [ ] **Track C: Leave Single-Source-of-Truth** — Leave exists in 3 places with no sync (absences table, block_assignments.has_leave/leave_days, HDAs with LV codes). 3-phase fix: computed properties → CRUD propagation → import creates absences → drop stale columns.
  - **Doc:** `docs/architecture/excel-stateful-roundtrip-roadmap.md` (Track C)

### Scheduling Engine

- [ ] **ACGME call duty validation gap** — `call_assignments` excluded from 24+4/rest checks. **Blocked on MEDCOM ruling.**
- [ ] **Faculty template gaps** — 4 faculty have no weekly templates; overrides are effectively empty.
- [ ] **Closed-loop validation pipeline** — Automated generate → validate → diagnose → fix → regenerate loop. Not yet implemented.
- [ ] **DEBT-025: 5 pre-existing failing tests** — `test_min_limit_enforcement`, `test_engine_calls_faculty_expansion`, `test_pcat_do_created_for_each_call`, `test_cpsat_allows_templates_requiring_procedure_credential`, `test_cpsat_respects_locked_blocks`.

### Infrastructure

- [ ] **Lock window Phase 3** — Base lock window works (services, routes, tests). Phase 3 enhancements unbuilt: resilience workflows (stage + gated publish), import lock-window flag injection.
- [ ] **DEBT-026: Python CVEs** — `langchain-core`, `langgraph-checkpoint` need version bumps. `ecdsa` eliminated (PyJWT migration).
- [ ] **DEBT-027: npm CVEs** — `minimatch` (high), `undici` (moderate). Run `npm audit fix`.

### Frontend

- [ ] **Frontend Phase 2: Draft & Publish** — Generate button creates draft instead of direct write. DraftPreviewPanel diff visualization.
- [ ] **Frontend Phase 3: ARO UI Hub** — `/hub/annual-planning` page (backend API ready, PR #1276).
- [ ] **Wire remaining enum hooks** — `useActivityCategories()`, `useRotationTypes()`, `useConstraintCategories()`, `useFreezeScopes()` into dropdowns.
- [ ] **Color scheme parity** — Tailwind classes matching `TAMC_Color_Scheme_Reference.xml` (ADV, C30/C40 distinctions).
- [ ] **MCP placeholder tools (DEBT-009)** — 11 tools return mock data (Hopfield, immune, VaR, Shapley).
- [ ] **Frontend a11y gaps (DEBT-008)** — Exotic components remain (Three.js, voxel, Plotly). Low priority.

## P3 — Low / Backlog

- [ ] **"No CLI" execution phases** — 3-phase plan: web-first daily ops → admin UI → never-CLI. Blocked by RED audit status.
- [ ] **OpenTelemetry (DEBT-018)** — `TELEMETRY_ENABLED=false`. Enable for production monitoring.
- [ ] **Import/Export Phase 4** — Frontend error handling for `BLOCK_MISMATCH` error code.

## Recently Completed (March 2026)

- [x] **ARO backend wiring** — DB models, schemas, service, API, migration (PR #1276)
- [x] **Excel Phases 1–3 + 4a/4b** — Stateful roundtrip pipeline complete (PRs #1262-#1264)
- [x] **Excel checksum determinism** — Sorted rows for stable SHA-256 (PR #1277)
- [x] **ROSETTA archive** — Stale Block 10 reference files archived to `docs/archived/scheduling/`
- [x] **mypy zero** — 3,991→0 errors (PRs #1272, #1275)
- [x] **TypeScript test compilation** — 97→0 errors (PR #1275)
- [x] **Test suite zero-failure** — 8,302 passing from 552 issues (PR #1273)
- [x] **UX audit round 3** — 12 findings fixed (PRs #1272, #1274)
- [x] **Activities CRUD page** — Full CRUD + rotations UX polish (PR #1268)
- [x] **Codex worktree wheat cherry-pick** — 7 cherry-picked, 7 chaff skipped (PR #1271)
- [x] **UX audit round 2** — Cell edit, tab deep links, redirects, nav overflow (PR #1270)

## Previously Completed (February 2026)

- [x] Field-level change tracking (PR branch `feat/field-level-change-tracking`)
- [x] Orphan framework removal ~8.8K LOC (Saga, EventBus, gRPC, Mesh)
- [x] Cache TTL consolidation (DEBT-013)
- [x] Playwright port conflict (DEBT-030)
- [x] Load-test scripts (DEBT-029)
- [x] Route bundle splitting (DEBT-028)
- [x] npm CVE fixes — minimatch, undici (DEBT-027, partial)
- [x] langchain-core CVE pin (DEBT-026, partial)
- [x] useEnums hooks wired (#1260)
- [x] Solver checkpointing (Redis-backed SolverSnapshotManager)
- [x] Schedule diff guard (20% global max change ratio)
- [x] Frontend rewiring steps 1-5 (#1259)
- [x] 217 ESLint `any` warnings → 0 (#1256)
- [x] Section 508 a11y: 22 components, 47 jsx-a11y warnings (#1110, #1251)
- [x] Repo hygiene: 48→25 dirs (#1255-#1258)
- [x] mypy ratchet batches 1-5 (#1243-#1245)
- [x] ecdsa CVE-2024-23342 — python-jose → PyJWT migration
- [x] ARO CP-SAT solver core (48/48 tests, PR #1238)
- [x] Faculty Fix Roadmap — all 3 phases (PRs #1199-#1202, #1219)
- [x] Dead model removal ~27,598 lines (PR #1198)
- [x] Frontend hub consolidation Phase 1 (PRs #694-700)
- [x] Constraint config GUI — DB model, API, frontend admin page
- [x] Med student scheduling — 7 tracks, CRUD, 5 constraints
- [x] Solver sandboxing — MemoryWatchdog, SandboxedCallback
- [x] Field-level encryption — Fernet on sensitive absence/wellness fields

---

## Do NOT Auto-Assign

- **PII history purge (`git filter-repo`)** — Incident #003 corrupted origin. Human-driven only.
- Scheduling engine constraint logic changes
- Auth/security files (`core/security.py`, `routes/auth.py`)
- Architecture decisions (mobile, multi-program, solver rewrites)

## Human TODO

- [ ] SM deterministic preload decision (Option A vs B) — `docs/architecture/SM_DETERMINISTIC_PRELOAD.md`
- [ ] MEDCOM ruling on ACGME call duty interpretation
- [ ] PII history purge coordination

## OPSEC Debt (Cannot Fix)

Alembic migrations contain real faculty names in SQL queries. Cannot edit existing migrations per Hard Boundary rules. Future migrations should use UUID lookups.
