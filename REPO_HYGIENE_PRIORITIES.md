# Repository Hygiene and Priorities Report

> **Generated:** 2025-12-28
> **Status:** Action items for consolidation, archival, and next steps

---

## Table of Contents

1. [Repository Health Summary](#repository-health-summary)
2. [Immediate Cleanup Actions](#immediate-cleanup-actions)
3. [Documentation Consolidation](#documentation-consolidation)
4. [Priority Tasks from HUMAN_TODO](#priority-tasks-from-human_todo)
5. [Scheduler Hardening Priorities](#scheduler-hardening-priorities)
6. [Recommended Next Steps](#recommended-next-steps)

---

## Repository Health Summary

### Documentation Overview

| Category | Count | Status |
|----------|-------|--------|
| Root markdown files | 26+ | Active - needs consolidation |
| Architecture docs | 49 | Active |
| Development docs | 45 | Active - some duplicates |
| Planning docs | 35 | Active |
| Research docs | 37 | Reference |
| Archived files | 50+ | Historical |
| **Total** | **370+** | **Healthy but complex** |

### Key Findings

1. **Duplicated files**: 3 documentation files exist in multiple locations
2. **Outdated changelog**: `docs/changelog.md` superseded by root `CHANGELOG.md`
3. **Scattered patch reviews**: 5 CLAUDE_REVIEW_PATCHES files need consolidation
4. **Active TODO tracking**: HUMAN_TODO.md is well-maintained and current
5. **Session archives**: Sessions 7-14 documented, recent work well-tracked

---

## Immediate Cleanup Actions

### High Priority - Delete Duplicates

| File to Delete | Reason | Keep Instead |
|----------------|--------|--------------|
| `docs/changelog.md` | Outdated duplicate | `CHANGELOG.md` (root) |
| `docs/CLAUDE_CHAT_INTEGRATION.md` | Smaller version | `docs/development/CLAUDE_CHAT_INTEGRATION.md` |
| `docs/DEPLOYMENT_TROUBLESHOOTING.md` | Smaller version | `docs/development/DEPLOYMENT_TROUBLESHOOTING.md` |

### Medium Priority - Consolidate

| Files | Action |
|-------|--------|
| `CLAUDE_REVIEW_PATCHES*.md` (5 files) | Consolidate into versioned single doc |
| Docker setup guides (3 files) | Merge into unified guide |

---

## Documentation Consolidation

### Completed in This Cleanup

1. ✅ Deleted `docs/changelog.md` (duplicate of root CHANGELOG.md)
2. ✅ Deleted `docs/CLAUDE_CHAT_INTEGRATION.md` (kept development version)
3. ✅ Deleted `docs/DEPLOYMENT_TROUBLESHOOTING.md` (kept development version)

### Deferred (Requires Manual Review)

1. **CLAUDE_REVIEW_PATCHES consolidation**
   - Files: 1, 2, 3, 4, 7 (gaps at 5, 6)
   - Action: Create consolidated document with historical sections
   - Effort: Low

2. **Docker documentation consolidation**
   - `docs/operations/DOCKER_LOCAL_SETUP.md`
   - `docs/operations/DOCKER_LOCAL_CHEATSHEET.md`
   - `docs/CLAUDE_DOCKER_DESKTOP_DEPLOYMENT_NOTES.md`
   - Action: Merge into single comprehensive guide
   - Effort: Medium

---

## Priority Tasks from HUMAN_TODO

### ✅ Completed (Recent)

| Task | Status | Date |
|------|--------|------|
| Block 10 Schedule Generation | ✅ Done | 2025-12-25 |
| MCP Wiring (5/5 tools) | ✅ Done | 2025-12-24 |
| PuLP Solver Template Balance | ✅ Done | 2025-12-24 |
| Solver Template Distribution | ✅ Fixed | 2025-12-24 |
| NF Half-Block Documentation | ✅ Verified | 2025-12-24 |

### 🔴 High Priority - User-Facing

| Task | Description | Owner |
|------|-------------|-------|
| Schedule Grid Frozen Headers | Header/column disappears on scroll | Frontend |
| Heatmap Block Navigation | Match Schedule page UX pattern | Frontend |
| Daily Manifest Empty State | Better error message for no data | Frontend |

### 🟡 Medium Priority - Backend

| Task | Description | Owner |
|------|-------------|-------|
| Heatmap group_by Validation | Backend rejects "Daily"/"Weekly" | Backend |
| Faculty Assignments rotation_template_id | Faculty Year View shows zeros | Backend |
| `solver_managed` Flag | Cleaner than filtering by activity_type | Backend |
| Resident Call Types (NF/LND) | Awaiting resident input | Stakeholder |

### 🟢 Low Priority - Infrastructure

| Task | Description | Owner |
|------|-------------|-------|
| Slack Integration | Webhook, App, Channels | DevOps |
| Broken README Links | 3 links to non-existent files | Docs |
| Linting CI Enforcement | Add ruff to pre-commit/CI | DevOps |

---

## Scheduler Hardening Priorities

> Source: `docs/planning/SCHEDULER_HARDENING_TODO.md`

### ✅ Completed (P0-P1)

- **Kill-Switch for Runaway Solvers** - Redis-backed abort signaling
- **Constraint-Level Violation Metrics** - Prometheus instrumentation

### 🟡 P2: Near-Term (Next Month)

| Task | Effort | Impact |
|------|--------|--------|
| **Deterministic Solver Checkpointing** | Medium | High - resume from crash |
| **Schedule Diff Guard** | Low | High - prevent excessive churn |
| **Write-Ahead Publish Staging** | Medium | Medium - atomic publishes |
| **Schedule Correctness SLO** | Low | Medium - visibility |

### 🔵 P3: Longer-Term

| Task | Effort | Impact |
|------|--------|--------|
| Solver Sandboxing | Medium | Security |
| Field-Level Encryption | High | Security/HIPAA |
| One-Time Publish Tokens | Low-Medium | Security |

---

## Recommended Next Steps

### Immediate (This Session)

1. ✅ **Delete duplicate files** - See actions above
2. ✅ **Create this priority report** - Done

### Short-Term (Next Sprint)

1. **Fix Schedule Grid UX** (High impact, visible to users)
   - Implement sticky headers/columns
   - Test across browsers

2. **Add Heatmap Block Navigation** (Consistency improvement)
   - Match Schedule page pattern
   - One-click block selection

3. **Complete P2 Hardening**
   - Schedule Diff Guard (low effort, high impact)
   - Correctness SLO metrics

### Medium-Term (Next Month)

1. **Solver Checkpointing**
   - Enable resume from long solver crashes
   - Database migration required

2. **MCP Tool Wiring**
   - `abort_solver` tool
   - `get_solver_progress` tool
   - `list_active_solvers` tool

3. **Documentation Consolidation**
   - Docker guides consolidation
   - Review patches consolidation

### Backlog (When Capacity Allows)

1. Slack integration setup
2. Field-level encryption (HIPAA)
3. Session naming convention consolidation (7-9 vs 10+)
4. Broken README link fixes

---

## Files Modified in This Cleanup

| Action | File |
|--------|------|
| Deleted | `docs/changelog.md` |
| Deleted | `docs/CLAUDE_CHAT_INTEGRATION.md` |
| Deleted | `docs/DEPLOYMENT_TROUBLESHOOTING.md` |
| Created | `REPO_HYGIENE_PRIORITIES.md` (this file) |

---

## Summary

The repository is in good health with active development and comprehensive documentation. Key areas for improvement:

1. **UX Priorities**: Schedule grid and heatmap navigation are high-visibility user-facing issues
2. **Hardening**: P2 scheduler hardening items provide safety improvements with reasonable effort
3. **Consolidation**: Duplicate files cleaned up; patch reviews and Docker docs remain for later

The HUMAN_TODO.md file is well-maintained and serves as the primary task tracker. This report supplements it with repo-wide hygiene observations.

---

*Last updated: 2025-12-28*
