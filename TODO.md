# TODO — Actionable Items

> **Updated:** 2026-03-04 (Planning Dissolve)
> **Source:** Extracted from MASTER_PRIORITY_LIST.md, TECHNICAL_DEBT.md, GUI_WIRING_GAPS.md, SCHEDULER_HARDENING_TODO.md, TRANSCRIPT_ACTION_ITEMS.md, and 8 other archived planning docs.
> **Companion:** `docs/planning/ROADMAP.md` (macro vision), `docs/planning/TECHNICAL_DEBT.md` (debt tracker)

---

## P0 — Critical / Blocking

- [ ] **PII in git history** — Resident names in deleted files still in repo history. Requires `git filter-repo` + force push. All collaborators must re-clone after.
- [ ] **Python CVEs (DEBT-026)** — `langchain-core` CVE-2026-26013, `langgraph-checkpoint` CVE-2026-27794, `ecdsa` CVE-2024-23342. Run `pip-audit`, upgrade deps.
- [ ] **npm CVEs (DEBT-027)** — `minimatch` (high), `undici` (moderate). Run `cd frontend && npm audit fix`.

## P1 — High / This Sprint

### Scheduling Engine

- [ ] **CP-SAT FMIT Fri/Sat call verification** — Confirm Fri/Sat call appears in `call_assignments` after regeneration. Verify PCAT/DO correctness.
- [ ] **MCP clear_existing doesn't clear HDAs** — MCP client deletes `assignments` only; stale `half_day_assignments` (solver/template) cause INFEASIBLE on repeated runs. Fix MCP client to clear both tables.
- [ ] **C30/C40 PGY booking rule** — Post-processing: auto-translate `C` → `C40` (PGY-1) / `C30` (PGY-2/3). Fix `C30` display_abbreviation (currently `None`). Add background color to TAMC color scheme.
- [ ] **Graduated call spacing** — Replace flat penalty=50 for consecutive-only with exponential decay across 1-4 day gaps (100/50/25/0). Extends `NoConsecutiveCallConstraint`.
- [ ] **NF continuity touchpoint (C-N)** — Preloader or constraint to assign `C-N` code to first Thursday PM of NF blocks.
- [ ] **SM deterministic preload** — DECISION NEEDED: remove SM from solver entirely (Option A) vs. improve solver's SM handling (Option B). Design doc: `docs/architecture/SM_DETERMINISTIC_PRELOAD.md`.

### Infrastructure

- [ ] **Alembic head sync** — DB may be behind head. Run `alembic current` + `alembic heads`, then `alembic upgrade head`.
- [ ] **5 failing tests (DEBT-025)** — Masking regressions: `test_min_limit_enforcement_in_validation`, `test_engine_calls_faculty_expansion_after_resident_expansion`, `test_pcat_do_created_for_each_call`, `test_cpsat_allows_templates_requiring_procedure_credential`, `test_cpsat_respects_locked_blocks`.
- [ ] **mypy 4,194 errors** — 492 files, 43.5% fixed (from 7,426). Bulk patterns: `no-untyped-def` (~2K), `var-annotated` (~1.5K), SQLAlchemy Column (~1K). Use sed/awk for common fixes.

### Frontend

- [ ] **Heavy route bundles (DEBT-028)** — `/absences` 345kB, `/hub/import-export` 332kB, `/admin/import` 318kB, `/admin/labs/optimization` 315kB. Add route-level code splitting.
- [ ] **Playwright port conflict (DEBT-030)** — Two configs both use port 3000. Unify with reserved port strategy.

## P2 — Medium / This Month

### Scheduling Engine

- [ ] **ACGME call duty validation gap** — `call_assignments` excluded from 24+4/rest checks. Pending MEDCOM ruling on ACGME interpretation.
- [ ] **Faculty template gaps** — 4 faculty have no weekly templates; overrides are effectively empty.
- [ ] **Final Wednesday continuity** — Penalize PGY-1/2 reaching final Wednesday without `C` or `C-I` (ACGME continuity tally).
- [ ] **HC & CLC template immunity** — Seed `HC` into activities (`is_protected=True`), verify `CLC` is protected. Solver/import must treat as locked.
- [ ] **Solver checkpointing** — Long runs (15+ min) lose progress on crash. Add `SolverSnapshot` model with periodic checkpointing.
- [ ] **Schedule diff guard** — Enforce 20% max change ratio before activation. Pure Python, no migration.
- [ ] **Closed-loop validation pipeline** — Automated generate → validate → diagnose → fix → regenerate loop.

### Infrastructure

- [ ] **Orphan framework code (~5.8K LOC)** — Evaluate: Saga (1.5K), EventBus (1.3K), gRPC (1.7K), Mesh (1.3K). Integrate or remove.
- [ ] **Budget cron wiring** — Code merged (PR #1177) but not registered: routes not in `main.py`, Celery beat not configured, Redis keys not consumed.
- [ ] **Lock window Phase 3** — Resilience workflows (stage + gated publish), imports (lock-window flag injection).
- [ ] **Field-level change tracking** — Activity log tracks actions but not field diffs. Add to `activity_log_service.py`.
- [ ] **Load-test missing scripts (DEBT-029)** — `.github/workflows/load-tests.yml` references 3 scripts not in repo.

### Frontend

- [ ] **MCP placeholder tools (DEBT-009)** — 11 tools return mock data (Hopfield, immune, VaR, Shapley). Implement backend services.
- [ ] **Frontend a11y gaps (DEBT-008)** — Exotic components (Three.js, voxel, Plotly). Deferred as low-priority.
- [ ] **Frontend hub consolidation** — 14 hubs: 1 complete (Swap), 5 partial, 8 to build. See `FRONTEND_HUB_CONSOLIDATION_ROADMAP.md`.

## P3 — Low / Backlog

- [ ] **OpenTelemetry (DEBT-018)** — `TELEMETRY_ENABLED=false` by default. Enable for production.
- [ ] **"No CLI" execution phases** — 3-phase plan: web-first daily ops → admin UI → never-CLI. Blocked by RED audit status.
- [ ] **Med student scheduling** — 7 learner tracks (M3/M4 rotations, skill logs, longitudinal clinics). Complete spec archived.
- [ ] **Constraint config GUI** — DB table for constraint enable/disable/weight. Currently hardcoded.
- [ ] **Solver sandboxing** — Resource ceilings (memory/CPU) for pathological inputs.
- [ ] **Field-level encryption** — `leave_type`, `accommodation_notes`, `military_status`.
- [ ] **K2.5 swarm integration** — Kimi K2.5 for parallel bulk work (e.g., mypy). Needs Moonshot API access.

---

## Do NOT Auto-Assign

- Scheduling engine changes, ACGME validator, constraint definitions
- Auth/security files (`core/security.py`, `routes/auth.py`)
- Architecture decisions (mobile, multi-program, solver rewrites)

## Human TODO

- [ ] Log into Gemini CLI (`gemini` in terminal)
- [ ] Log into Codex CLI (`codex auth`)
- [ ] SM deterministic preload decision (Option A vs B)
- [ ] MEDCOM ruling on ACGME call duty interpretation

## Laptop Cleanup (2026-02-22)

- [ ] Push `post-restore-setup` branch (10 unpushed commits)
- [ ] Add `rf_enrichment.json` to `scripts/sdr/.gitignore`
- [ ] Add `*.db-shm` and `*.db-wal` to `workspace/ha-ml/.gitignore`
- [ ] Delete stale AAPM copies once verified redundant

## OPSEC Debt (Cannot Fix)

Alembic migrations contain real faculty names in SQL queries. Cannot edit existing migrations per Hard Boundary rules. Future migrations should use UUID lookups.
