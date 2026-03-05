# Roadmap

> **Last Updated:** 2026-03-04 (post-#1260 audit)
> **Companion:** `TODO.md` (actionable items), `docs/planning/TECHNICAL_DEBT.md` (debt tracker)

---

## Current Release: v1.0.5 — Block 12 Schedule Generation & XLSX Last-Mile (March 2026)

> **Status**: Stable. PRs #1214-#1219, #1231-#1236, #1243-#1260 merged.

**Schedule Engine:**
- 47/50 constraints active, call equity tuning, category-gate resolution
- CALL pipeline sync, overnight call generation, MAD formulation, equity weights
- Integrated workload constraint, YTD_SUMMARY faculty union bug fixed
- Category-gate AT/C template resolution Phase 4A/4B/4D
- Final Wednesday faculty inverted schedule + activity code disambiguation
- Mind Flayer's Probe: AST-based pre-commit hook for constraint archetype enforcement
- ARO CP-SAT solver (#1238)
- Solver checkpointing (Redis-backed `SolverSnapshotManager`)
- Schedule diff guard (20% global max change ratio)

**XLSX Export — TAMC Reference Format Match:**
- Color, font, sizing, borders, column widths all matched to reference spreadsheet
- Calculator formulas: Screeners, Providers Virtual, Attendings, V Clinic all implemented

**Frontend:**
- Frontend rewiring steps 1-5 (#1259) — type safety, OpenAPI types, expand_block_assignments toggle
- 217 ESLint `any` warnings eliminated (#1256) — zero-warning frontend
- Section 508 a11y: ARIA across 22 components, 47 jsx-a11y warnings resolved (#1110, #1251)
- useEnums hooks wired into 4 components (#1260)
- Repo hygiene: 48→25 dirs, 55→10 planning docs (#1255-#1258)

**Infrastructure:**
- mypy ratchet batches (#1243-#1245)
- Load-test scripts (k6, locust, CI workflow)
- DEBT-025 failing tests partially addressed (#1123, #1147)

### Upcoming: Last-Mile Coordinator Rules

> **Source**: `docs/archived/planning/TRANSCRIPT_ACTION_ITEMS.md`, `docs/architecture/SM_DETERMINISTIC_PRELOAD.md`

- [ ] Graduated call spacing (exponential decay 1-4 day gaps)
- [ ] C30/C40 PGY booking rule (auto-translate `C` → `C40`/`C30` by PGY level)
- [ ] NF continuity touchpoint (`C-N` code, first Thursday PM of NF blocks)
- [ ] Final Wednesday continuity loss protection (resident side)
- [ ] HC & CLC template immunity (`is_protected=True`)
- [ ] SM deterministic preload (DECISION NEEDED: Option A vs B)

### Upcoming: Frontend Rewiring (Post-Backend Sprint)

> **Doc**: `docs/planning/frontend_rewiring/README.md`

- **Phase 1** — Type Safety: ~~Regenerate OpenAPI types, wire `expand_block_assignments` toggle~~ **DONE** (#1259)
- **Phase 2** — Draft & Publish Lifecycle: Stage/Preview/Publish flow
- **Phase 3** — ARO UI Hub: `/hub/annual-planning` page
- **Phase 4** — Import/Export Last Mile: Annual Workbook (14-sheet) export
- **Phase 5** — Cosmetic & UX Debt: ~~Dynamic enum fetches~~ **DONE** (#1260), color scheme parity

---

## Completed Releases

### v1.0.3 — Reliability & Operations (February 2026)

- `datetime.utcnow()` → `datetime.now(UTC)` migration (10 PRs)
- Mini branch triage Wave 2 (keyboard a11y, admin status, loading states, composite indexes, budget cron, VaR/Shapley tests)
- Stack health audit script, Block 12 preflight, LangGraph Phase 1, Solo pool macOS fix
- Codex feedback fixes (3 P1s, 6 P2s)

### v1.0.2 — Quality & Build Hardening (February 2026)

- Frontend builds with strict checks (`ignoreBuildErrors: false`)
- React key anti-patterns fixed, logout error handling, MAX_FACULTY to Settings
- Test marathon: 11,861 tests across 201 PRs

### v1.0.1 — Personal AI Infrastructure (December 2025)

- 34 Agent Skills, 27 Slash Commands, 4 Operational Modes
- MCP Server: 4 → 97+ tools with backend integration
- Docker security hardening, solver operational controls

---

## v1.1.0 (Target: Q2 2026)

> Q1 was consumed by Realization Sprint, quality hardening, Perplexity research, PII recovery, dead code removal, call equity, SQL injection hardening, and PAI v2.

### Email Notifications
- SMTP integration, certification reminders, schedule/swap notifications
- Celery tasks for async delivery, configurable preferences

### Bulk Import/Export Enhancements
- Batch schedule import from Excel, template-based bulk assignment
- Background Celery tasks for large operations

### FMIT Integration Improvements
- Enhanced FMIT week detection, automated conflict resolution
- FMIT-specific reporting and fairness metrics

---

## v1.2.0+ (Future — Design Docs Archived)

Detailed design documents for future features have been archived to `docs/archived/planning/`. Highlights:

- **Mobile Application** — React Native, push notifications, offline viewing
- **Advanced Analytics** — Predictive scheduling, ML recommendations, custom reports
- **Enterprise Features** — LDAP/SSO, multi-program, cross-institutional scheduling
- **AI/ML Enhancements** — NLP queries, anomaly detection, reinforcement learning
- **Integration Ecosystem** — MyEvaluations, EMR, time tracking, external API

---

## Active Sub-Roadmaps

| File | Scope |
|------|-------|
| `docs/planning/CP_SAT_PIPELINE_ROADMAP.md` | Solver pipeline (preloads, activity solver, export) |
| `docs/planning/E2E_GUI_TESTING_ROADMAP.md` | E2E testing phases (Phase 4 next: auth fixtures) |
| `docs/planning/FRONTEND_HUB_CONSOLIDATION_ROADMAP.md` | 14 hubs: 1 complete, 5 partial, 8 to build |
| `docs/planning/MCP_INTEGRATION_OPPORTUNITIES.md` | MCP Phase 6 (ongoing) |
| `docs/planning/MCP_PLACEHOLDER_IMPLEMENTATION_PLAN.md` | 10 placeholder tools pending backend |
| `docs/planning/MCP_PRIORITY_LIST.md` | Daily P0-P4 MCP priorities |
| `docs/planning/PERFORMANCE_TESTING.md` | Solver benchmarking infrastructure |
| `docs/planning/STRATEGIC_DECISIONS.md` | 7 product direction decisions |
| `docs/planning/TECHNICAL_DEBT.md` | 30 items tracked (21 resolved, 9 open) |
| `docs/architecture/ANNUAL_WORKBOOK_ARCHITECTURE.md` | 14-sheet master workbook pipeline |
