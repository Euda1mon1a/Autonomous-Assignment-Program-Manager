# Documentation Map

> Quick navigation for humans and AI agents. For AI-specific instructions, see root `CLAUDE.md`.
> Updated: 2026-03-04

## For Continuous Autonomous Work (Agent Essentials)

| Priority | Document | Purpose |
|----------|----------|---------|
| MUST | `CLAUDE.md` (root) | Project guidelines, code style, boundaries — auto-loaded |
| MUST | `docs/planning/ROADMAP.md` | Current work, phase status, what's next |
| MUST | `docs/archived/planning/MASTER_PRIORITY_LIST.md` | Strategic prioritization |
| MUST | `docs/planning/TECHNICAL_DEBT.md` | Open debt items |
| SHOULD | `docs/development/BEST_PRACTICES_AND_GOTCHAS.md` | Common bugs, debugging flowcharts |
| SHOULD | `docs/architecture/DOW_CONVENTION_BUG.md` | Critical: Python weekday vs PG DOW |
| SHOULD | `docs/planning/frontend_rewiring/README.md` | Frontend phase status |
| REF | `.claude/dontreadme/INDEX.md` | AI agent deep context |

## Active Directories

| Directory | Contents | Files |
|-----------|----------|-------|
| `architecture/` | System design, constraints, resilience, specs, ADRs, feature designs | ~130 |
| `development/` | Dev setup, testing, DB utilities, implementation guides, examples | ~90 |
| `operations/` | Ops runbooks, deployment, monitoring, CI/CD, health checks | ~30 |
| `planning/` | Roadmaps, priorities, strategic plans, MCP planning | ~50 |
| `scheduling/` | Solver models, block specs, domain knowledge, abbreviations | ~20 |
| `security/` | PII audit, security scanning, production checklists | ~18 |
| `guides/` | How-to guides, runbooks, tool usage | ~40 |
| `user-guide/` | End-user feature guides | ~19 |
| `admin-manual/` | Admin setup, config, people management | ~11 |
| `playbooks/` | Ops playbooks (incident response, compliance, onboarding) | ~7 |
| `getting-started/` | Onboarding docs | ~6 |
| `reviews/` | Recent assessments (Mar 2026) | ~7 |
| `prompts/` | Automation prompt templates | ~8 |
| `rag-knowledge/` | RAG system knowledge base | ~24 |
| `tools/` | Codex, Kimi tool docs | ~3 |

## By Domain

### Scheduling Engine
- `docs/architecture/ENGINE_ASSIGNMENT_FLOW.md` — How solver routes assignments
- `docs/architecture/CALL_CONSTRAINTS.md` — Call generation rules
- `docs/architecture/CONSTRAINT_CATALOG.md` — Full constraint catalog
- `docs/architecture/DISABLED_CONSTRAINTS_AUDIT.md` — 47 enabled / 4 disabled
- `docs/architecture/FACULTY_FIX_ROADMAP.md` — Faculty scheduling (all phases complete)
- `docs/scheduling/` — Solver models, block specs, domain knowledge

### Excel Import/Export
- `docs/architecture/excel-stateful-roundtrip-roadmap.md` — Phases 1-4
- `docs/archived/planning/BLOCK_12_ANNUAL_WORKBOOK_ROADMAP.md` — Annual workbook pipeline
- `docs/architecture/annual-workbook-architecture.md` — 14-sheet workbook spec

### Security & Compliance
- `docs/architecture/SQL_IDENTIFIER_SECURITY.md` — validate_identifier() patterns
- `docs/security/PII_AUDIT_LOG.md` — 3 PII incidents
- `docs/architecture/DOW_CONVENTION_BUG.md` — Weekday convention

### Operations & Deployment
- `docs/guides/SCHEDULE_GENERATION_RUNBOOK.md` — Step-by-step generation
- `docs/operations/` — Ops runbooks, deployment, monitoring, CI/CD (~30 files)
- `docs/admin-manual/` — Setup, config, people management
- `docs/playbooks/` — Incident response, compliance, onboarding

### Development
- `docs/development/` — Dev setup, testing guides, DB utilities, examples (~90 files)

### Reviews & Assessments
- `docs/reviews/` — Recent assessments (Mar 2026)

### Research (Read-Only — Do Not Modify)
- `docs/research/README.md` — Implementation status for each concept

## Archived Docs

All archived content lives in `docs/archived/`. Preserved for context, no longer active:
- `docs/archived/planning/` — Completed planning docs
- `docs/archived/reports/` — Historical reports and automation output
- `docs/archived/reviews/` — Jan-Feb 2026 review snapshots
- `docs/archived/scratchpad/` — Session notes (Jan-Feb 2026)
- `docs/archived/superseded/` — Superseded docs
- `docs/archived/issues/`, `sessions/`, `tasks/`, `troubleshooting/`, `data/` — Miscellaneous archived items
