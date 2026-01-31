# Session: CP-SAT Phase 8 + K2.5 Integration Design

**Date:** 2026-01-30 (continued)
**Branch:** `excel-import-improvements`
**Starting commit:** `e7620746` (main after PR #785 merge)

---

## Completed

### 1. GUI Day-Off Patterns - Full Implementation (PR #784 → merged)

**Problem:** Codex found that PR #783 only *skipped* hardcoded fallbacks but didn't *apply* GUI patterns.

**Fix (commit `fb7e8763` + `f20bbedf`):**
- Added `_get_time_off_codes_for_date()` to actually apply weekly patterns
- Expanded template lookup with PGY-aware matching + aliases
- Added ORDER BY to prefer exact abbreviation matches over display_abbreviation
- Tests: `test_sync_preload_time_off_patterns.py` (2 tests)

**Merged as:** `aaec3390`

### 2. Excel Import Draft Flow (PR #785 → merged)

**New endpoint:** `POST /api/v1/import/half-day/batches/{batch_id}/draft`

**Flow:**
```
Stage → Preview → Draft → Publish
```

**Safety features:**
- Batch status gate (only STAGED/APPROVED)
- MODIFY/DELETE validation (existing_assignment_id required)
- Full-day slot preservation (None→"ALL")
- Orphan draft cleanup (delete if all rows fail)

**Codex fixes:**
- P1: `row.slot or "AM"` → `row.slot` (preserve full-day)
- P2: Delete orphan drafts when all rows fail

**Tests:** `test_half_day_import_service.py` (3 tests)

**Merged as:** `e7620746`

### 3. Time-Off Patterns Extended to All Rotations

**Change:** Removed `is_inpatient or is_offsite` restriction so GUI time-off patterns apply to outpatient rotations too.

**Test:** `test_preload_outpatient_time_off_patterns`

### 4. K2.5 Swarm Integration Design

**Docs created:**
- `docs/planning/K2_SWARM_MCP_INTEGRATION.md` - MCP tool design
- `docs/research/AGENT_ARCHITECTURE_COMPARISON.md` - AAPM vs Moltbot vs K2.5

**MCP Tools designed:**
| Tool | Purpose |
|------|---------|
| `k2_swarm_spawn_task` | Send task to 100-agent swarm |
| `k2_swarm_get_result` | Poll completion, get patches |
| `k2_swarm_apply_patches` | Selective apply with dry-run |

**Architecture:** AAPM orchestrates → K2.5 executes → Drafts for review → Approve before commit

**First use case:** Mypy bulk fix (4,250 errors)

**Added to MASTER_PRIORITY_LIST.md** as HIGH #13

---

## PRs Merged This Session

| PR | Title | Commit |
|----|-------|--------|
| #784 | feat(preload): apply GUI time-off patterns to InpatientPreload | `aaec3390` |
| #785 | feat(import): Excel staging → draft flow + time-off pattern extensions | `e7620746` |

## PRs Closed

| PR | Reason |
|----|--------|
| #782 | Dependabot Next.js bump - deferred to maintenance window |
| #783 | Superseded by #784 with complete implementation |

---

## Key Decisions

1. **K2.5 as managed asset** - Swarm executes, Claude/human reviews before commit
2. **Draft-first workflow** - All bulk changes go through draft/review/apply
3. **Moonshot API direct** - OpenRouter has base model but not Agent Swarm mode

---

## Files Modified

**Backend:**
- `backend/app/services/preload_service.py` - time-off patterns
- `backend/app/services/sync_preload_service.py` - time-off patterns
- `backend/app/services/half_day_import_service.py` - draft flow + fixes
- `backend/app/services/schedule_draft_service.py` - sync draft helper
- `backend/app/api/routes/half_day_imports.py` - draft endpoint
- `backend/app/schemas/half_day_import.py` - draft schemas

**Tests:**
- `backend/tests/services/test_sync_preload_time_off_patterns.py` (new)
- `backend/tests/services/test_half_day_import_service.py` (new)
- `backend/tests/services/test_sync_preload_protected_patterns.py` (extended)

**Docs:**
- `docs/planning/K2_SWARM_MCP_INTEGRATION.md` (new)
- `docs/research/AGENT_ARCHITECTURE_COMPARISON.md` (new)
- `docs/MASTER_PRIORITY_LIST.md` (updated)
- `docs/scratchpad/session-*.md` (5 files)

---

## Next Session

1. **Get Moonshot API account** - Required for K2.5 swarm access
2. **Implement K2.5 MCP tools** - `mcp-server/src/scheduler_mcp/k2_swarm/`
3. **Test with mypy bulk fix** - First real use case
4. **Or continue:** Excel export auth fix (CRITICAL #1), Rate limits (HIGH #10)

---

## Notes

- K2.5 Agent Swarm is Beta, requires Moonshot API (not OpenRouter)
- Swarm mode: up to 100 agents, 1500 tool calls, 2.2-4.5x speedup
- AAPM governance patterns (audit trails, escalation) still valuable even with swarm
- Block 10 validation passed: 100% ACGME compliance, 0 issues

---

## Commits on `excel-import-improvements`

```
dca10d30 docs: add K2.5 swarm integration to priority list
```

(Other work was on `cpsat-phase8` which was merged)
