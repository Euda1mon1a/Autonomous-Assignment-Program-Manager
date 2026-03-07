# TODO — Actionable Items

> **Updated:** 2026-03-07 (overnight session: change tracking, mypy batch 5, load-test scripts, doc sync)
> **Source:** Extracted from MASTER_PRIORITY_LIST.md, TECHNICAL_DEBT.md, GUI_WIRING_GAPS.md, SCHEDULER_HARDENING_TODO.md, TRANSCRIPT_ACTION_ITEMS.md, and 8 other archived planning docs.
> **Companion:** `docs/planning/ROADMAP.md` (macro vision), `docs/planning/TECHNICAL_DEBT.md` (debt tracker)

---

## P0 — Critical / Blocking

- [ ] **PII in git history** — Resident names in deleted files still in repo history. Requires `git filter-repo` + force push. All collaborators must re-clone after. **Human-only.**
- [x] **ecdsa CVE-2024-23342 (DEBT-026, residual)** — Eliminated by replacing `python-jose` with `PyJWT[crypto]`. 18 source/test files migrated. Key difference: PyJWT auto-validates `aud` claims (added `verify_aud: False` where needed). Caught `ExpiredSignatureError`/`ImmatureSignatureError` for correct error messages. All 31 audience auth tests pass.

## P1 — High / This Sprint

### Scheduling Engine

- [ ] **CP-SAT FMIT Fri/Sat call verification** — Code exists (FMIT weekend exclusions in `overnight_call.py`). Needs manual verification that Fri/Sat call appears in `call_assignments` after regeneration + PCAT/DO correctness check.
- [x] **MCP clear_existing doesn't clear HDAs** — `api_client.py` deletes `assignments` only; stale `half_day_assignments` cause INFEASIBLE on repeated runs. Fix MCP client to clear both tables.
- [x] **C30/C40 PGY booking rule** — Post-processing: auto-translate `C` → `C40` (PGY-1) / `C30` (PGY-2/3). Fix `C30` display_abbreviation (currently `None`). Add background color to TAMC color scheme.
- [x] **Graduated call spacing** — Replace flat `weight=50.0` in `NoConsecutiveCallConstraint` with exponential decay across 1-4 day gaps (100/50/25/0).
- [x] **NF continuity touchpoint (C-N)** — `C-N` code recognized in activity solver but no preloader/constraint assigns it to first Thursday PM of NF blocks.
- [x] **SM deterministic preload** — DECISION NEEDED: remove SM from solver entirely (Option A) vs. improve solver's SM handling (Option B). Design doc: `docs/architecture/SM_DETERMINISTIC_PRELOAD.md`.

### Infrastructure

- [x] **Alembic head sync** — Run `alembic current` + `alembic heads`, then `alembic upgrade head`. Requires running DB.
- [ ] **5 failing tests (DEBT-025)** — Fixes landed (#1123, #1147) but not confirmed all 5 resolved. Requires backend `pytest` run against live DB.
- [ ] **mypy errors** — 3,991 on main. Batches 4-5 on branches bring to ~3,863. Merge pending branches to ratchet down.

### Frontend

- [x] **Heavy route bundles (DEBT-028)** — `/absences` 345kB, `/hub/import-export` 332kB, `/admin/import` 318kB, `/admin/labs/optimization` 315kB. Add route-level code splitting via `next/dynamic`.
- [x] **Playwright port conflict (DEBT-030)** — Unique ports: root 3001, CI 3002, E2E 3003. Branch `fix/playwright-port-conflict` at `be77aeff`.

## P2 — Medium / This Month

### Scheduling Engine

- [ ] **ACGME call duty validation gap** — `call_assignments` excluded from 24+4/rest checks. Blocked on MEDCOM ruling.
- [ ] **Faculty template gaps** — 4 faculty have no weekly templates; overrides are effectively empty.
- [x] **Final Wednesday continuity** — Faculty side done (`WednesdayPMSingleFaculty` in `temporal.py`). Resident side needed: penalize PGY-1/2 reaching final Wednesday without `C` or `C-I`.
- [x] **HC & CLC template immunity** — `is_protected` field exists on activities but HC not seeded as protected. Verify CLC. Solver/import must treat as locked.
- [ ] **Closed-loop validation pipeline** — Automated generate → validate → diagnose → fix → regenerate loop. Not yet implemented.

### Infrastructure

- [x] **Orphan framework code (~8.8K LOC)** — Removed Saga, EventBus, gRPC, Mesh. Branch `cleanup/remove-orphan-frameworks` at `54fcd17d`.
- [x] **Budget cron wiring** — Route exists (`routes/budget.py`) but NOT registered in `__init__.py`. Celery beat function exists but not wired at startup. Code merged (PR #1177) but never activated.
- [ ] **Lock window Phase 3** — Base lock window works (services, routes, tests). Phase 3 enhancements unbuilt: resilience workflows (stage + gated publish), import lock-window flag injection.
- [x] **Field-level change tracking** — Reusable `change_tracker.py` utility wired into swap rollback, break-glass, and publish paths. 27 tests. Branch `feat/field-level-change-tracking` at `36c80eb3`.

### Frontend

- [ ] **MCP placeholder tools (DEBT-009)** — 9/40 tools fully integrated. VaR, Shapley, game theory tools still return mock data.
- [ ] **Frontend a11y gaps (DEBT-008)** — Standard components fixed (#1110, #1251). Exotic components remain (Three.js, voxel, Plotly). Low priority.
- [x] **Frontend hub consolidation** — 14 hubs: 1 complete (Swap), 5 partial, 8 to build. Each hub is its own PR. See `docs/planning/FRONTEND_HUB_CONSOLIDATION_ROADMAP.md`.

## P3 — Low / Backlog

- [x] **OpenTelemetry (DEBT-018)** — Wired `setup_telemetry(app)` in `main.py`, added tracing spans to solver path in `engine.py`.
- [ ] **"No CLI" execution phases** — 3-phase plan: web-first daily ops → admin UI → never-CLI. Blocked by RED audit status.
- [x] **Med student scheduling** — 7 learner tracks, overlay model (LearnerTrack/LearnerToTrack/LearnerAssignment models), CRUD API, 5 scheduling constraints (supervision, ASM Wednesday, FMIT blocking, double-booking, track balance), schedule generator with supervisor matching.
- [x] **Constraint config GUI** — `ConstraintConfiguration` DB model, `PATCH /constraints/{name}` API, `load_from_db()` in config manager, frontend admin page with category filtering + weight editing.
- [x] **Solver sandboxing** — `SolverResourceLimits`, `MemoryWatchdog` thread, `SandboxedCallback` with `StopSearch()`, `clamp_workers()`. Integrated into `solvers.py`.
- [x] **Field-level encryption** — `EncryptedString`/`EncryptedJSON` TypeDecorators using Fernet. Applied to `absence.review_notes`, `absence.tdy_location`, `absence.notes`, `wellness.response_data`, `wellness.notes`.
- [x] **K2.5 swarm integration** — `mcp-server/src/scheduler_mcp/k2_swarm/` with 3 MCP tools: spawn, get_result, apply_patches. Feature-flagged via `K2_SWARM_ENABLED`.

## Recently Completed

- [x] **Field-level change tracking** — `change_tracker.py` utility with `track_changes()`, `track_model_changes()`, `format_changes_for_log()`. Auto-skips sensitive fields. 27 tests. Wired into swap rollback, break-glass approval, schedule publish.
- [x] **Orphan framework removal (~8.8K LOC)** — Saga, EventBus, gRPC, Mesh dead code removed.
- [x] **mypy ratchet batch 4-5** — 144+ errors fixed (numpy wrapping, Optional annotations, Sequence fixes). Baseline: 3,991 → ~3,863.
- [x] **Cache TTL consolidation (DEBT-013)** — All hardcoded TTLs replaced with `CacheTTL` constants.
- [x] **Playwright port conflict (DEBT-030)** — Unique ports 3001/3002/3003 assigned to 3 configs.
- [x] **Load-test missing scripts (DEBT-029)** — 3 CI scripts created (compare-baselines, report-generator, regression-detector).
- [x] **Route bundle splitting (DEBT-028)** — Heavy routes split via `next/dynamic` lazy loading.
- [x] **npm CVEs (DEBT-027)** (#1261) — minimatch ReDoS (high) + undici decompression (moderate) resolved. 4 remaining are low-severity dev-only (`jest-environment-jsdom` chain).
- [x] **langchain-core CVE-2025-68664** (#1261) — Pinned `>=0.3.81`. Original "CVE-2026-26013" cited by GPT-5 was a misattribution (real CVE exists but for a different vulnerability), not a fabricated ID.
- [x] **Wire useEnums hooks** (#1260) — `usePersonTypes`, `usePgyLevels`, `useSchedulingAlgorithms`, `useActivityCategories` wired into 4 components. Backend PGY levels expanded 1-3 → 1-8. EditPersonModal validation fixed.
- [x] **Solver checkpointing** — `SolverSnapshotManager` with Redis-backed storage, hash verification, TTL cleanup (`scheduling/solver_snapshot.py`).
- [x] **Schedule diff guard** — `DiffGuard` with 20% global / 50% per-person / 30% high-churn thresholds (`scheduling/diff_guard.py`). Pure Python, tested.
- [x] **Load-test scripts (DEBT-029)** — k6 scenarios, locust users, analysis scripts, CI workflow, + 3 missing CI scripts (compare-baselines, report-generator, regression-detector). Branch `fix/load-test-missing-scripts` at `3a464d59`.
- [x] **Frontend rewiring steps 1-5** (#1259) — Type safety, OpenAPI regeneration, `expand_block_assignments` toggle.
- [x] **217 ESLint any warnings** (#1256) — Zero-warning frontend.
- [x] **Section 508 a11y** (#1110, #1251) — ARIA attributes across 22 components, 47 jsx-a11y warnings resolved.
- [x] **Repo hygiene** (#1255, #1257, #1258) — 48→25 dirs, 55→10 planning docs.
- [x] **mypy ratchet batches** (#1243-#1245) — Services, tenancy, search, CLI, exports, workflow, analytics, ML, testing.

---

## Do NOT Auto-Assign

- **PII history purge (`git filter-repo`)** — Incident #003 corrupted origin (179K lines mangled). Human-driven only, test on throwaway clone, bundle backup first. See `docs/security/PII_AUDIT_LOG.md`.
- Scheduling engine changes, ACGME validator, constraint definitions
- Auth/security files (`core/security.py`, `routes/auth.py`)
- Architecture decisions (mobile, multi-program, solver rewrites)

## Human TODO

- [ ] SM deterministic preload decision (Option A vs B)
- [ ] MEDCOM ruling on ACGME call duty interpretation

## OPSEC Debt (Cannot Fix)

Alembic migrations contain real faculty names in SQL queries. Cannot edit existing migrations per Hard Boundary rules. Future migrations should use UUID lookups.
