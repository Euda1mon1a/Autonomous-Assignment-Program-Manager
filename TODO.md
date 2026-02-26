# AAPM — Autonomous Coding Tasks

> Format: `- [ ] description` | Agent picks next unchecked task, commits to feature branch.
> All branches require manual review — NOT auto-merged.
> **84% of tech debt resolved (21/25).** 0 open issues, 0 open PRs.

---

## Batch 1 — Safe, Mechanical (Next Run)

- [ ] Build admin status dashboard page showing native service health (Postgres, Redis, backend, frontend) — use existing `/api/health/deep` endpoint, standard React page, no security implications
- [ ] Clean up RECENT_ACTIVITY.md dedup — file has massive duplication (same entries 10+ times). Fix the dedup logic in `.codex/sync-claude-activity.sh`
- [ ] Add type hints in `backend/app/services/upload/` — run mypy on this directory only and fix errors (3 files: `processors.py`, `service.py`, `storage.py`)

## Batch 2 — Moderate Complexity

- [ ] Enable OpenTelemetry configuration — `TELEMETRY_ENABLED=false` by default, exporters already in `backend/app/telemetry/tracer.py`, just needs config wiring
- [ ] Add type hints in `backend/app/services/export/` — run mypy on this directory only (3 files: `export_factory.py`, `xml_exporter.py`, and any others)
- [ ] Audit frontend pages for missing loading states — ensure every page that fetches data shows a skeleton/spinner
- [ ] Add error boundary components to top 5 admin pages (dashboard, scheduling, people, compliance, swaps)
- [ ] Review useEffect hooks for missing dependency arrays — run `react-hooks/exhaustive-deps` and fix warnings

## Batch 3 — Requires Human Review (PR Only)

- [ ] Fix DEBT-025 failing tests (5 tests in scheduling engine): `test_min_limit_enforcement_in_validation`, `test_engine_calls_faculty_expansion_after_resident_expansion`, `test_pcat_do_created_for_each_call`, `test_cpsat_allows_templates_requiring_procedure_credential`, `test_cpsat_respects_locked_blocks`
- [ ] Implement VaR and Shapley MCP placeholder tools — currently return mock data (DEBT-009)
- [ ] Create DB migration adding indexes on most-queried columns (check slow query log or EXPLAIN ANALYZE)
- [ ] Add keyboard navigation tests for schedule grid component

## Batch 4 — Service Integration (Deferred)

- [ ] Wire Pareto optimization into scheduling engine as optional multi-solution mode — behind `use_pareto_frontier=False` flag in `engine.py:generate()`. Requires human review (scheduling engine change).
- [ ] Wire Agent Matcher into `claude_chat.py` for automatic model tier selection based on task semantics — low-risk routing enhancement
- [ ] Unquarantine approval chain — implement `require_coordinator_or_above` RBAC dependency (note: route uses non-factory `Depends()` pattern, needs pattern reconciliation with existing `require_admin()` factory)
- [ ] See `docs/reviews/2026-02-26-service-integration-assessment.md` for full analysis

## Completed

- [x] Add integration tests for schedule generation pipeline (claude/2026-02-10)
- [x] Audit API routes for consistent error response format (claude/2026-02-10)
- [x] Add request validation tests for complex JSON bodies (claude/2026-02-10)
- [x] Add retry logic with backoff to RAG embedding ingestion (codex/2026-02-11)
- [x] Add /api/health/deep endpoint (codex/2026-02-11)

## Do NOT Auto-Assign

- Scheduling engine changes, ACGME validator, constraint definitions
- Auth/security files (`core/security.py`, `routes/auth.py`)
- New architecture decisions (mobile app, multi-program support)
- Budget-aware cron manager (human task)

## Human TODO

- [ ] Log into Gemini CLI (`gemini` in terminal — OAuth browser flow)
- [ ] Log into Codex CLI (`codex auth` — OAuth browser flow)
- [ ] Build budget-aware cron manager for Opus-consuming jobs

## Laptop Cleanup (2026-02-22)

- [ ] Push `post-restore-setup` branch (10 unpushed commits, no remote tracking — incident docs, PII fixes, ML pipeline, constraint calibration, MCP watchdog)
- [ ] Add `rf_enrichment.json` to `scripts/sdr/.gitignore` (or commit if intentional)
- [ ] Add `*.db-shm` and `*.db-wal` to `workspace/ha-ml/.gitignore`
- [ ] Delete stale AAPM copies once verified redundant:
  - `Autonomous-Assignment-Program-Manager-1/` (dirty `.vscode/settings.json`)
  - `Autonomous-Assignment-Program-Manager-archived-20251220/` (3 loose Excel files + `1cd/`)
  - `Autonomous-Assignment-Program-Manager.corrupted/` (8 modified hook scripts)
  - `Documents/Autonomous-Assignment-Program-Manager/` (dirty Dockerfile + package-lock.json)

## OPSEC Debt (Cannot Fix — Existing Migrations)

Alembic migrations contain real faculty names in SQL queries (`20260114_faculty_constraints.py`, `20260114_sm_constraints.py`, `20260114_half_day_tables.py`). Cannot edit existing migrations per Hard Boundary rules. Future migrations should use UUID lookups instead of name-based queries.
