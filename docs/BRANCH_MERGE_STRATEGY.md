# Branch Merge Strategy - Claude Vibe Coding Consolidation

**Generated:** 2025-12-20
**Last Updated:** 2025-12-21
**Total Branches:** 24 Claude branches to evaluate
**Approach:** Triage into tiers, merge in dependency order, validate at each step

---

## Executive Summary

After analyzing all 24 branches, I recommend:
- **✅ COMPLETED (Tier 1):** 8 branches - merged 2025-12-21 via squash and merge
- **Merge with caution (Tier 2):** 6 branches - valuable but need conflict resolution
- **Cherry-pick only (Tier 3):** 5 branches - mixed content, extract useful parts
- **Archive/Skip (Tier 4):** 5 branches - docs-only, duplicates, or superseded

---

## Tier 1: ✅ COMPLETED (2025-12-21)

All 8 Tier 1 branches have been successfully merged into main via squash and merge.

### 1.1 Infrastructure & Quality

| # | Branch | PR | Status |
|---|--------|-----|--------|
| 1 | `add-github-actions-cicd-NXUab` | #308 | ✅ Merged |
| 2 | `add-loguru-logging-aaEGr` | #300 | ✅ Merged (resolved merge conflict) |
| 3 | `fix-pylint-backend-services-MclKI` | #303 | ✅ Merged |

### 1.2 Type Safety

| # | Branch | PR | Status |
|---|--------|-----|--------|
| 4 | `add-python-type-hints-6mDTC` | #310 | ✅ Merged |

### 1.3 Frontend Tests (Isolated)

| # | Branch | PR | Status |
|---|--------|-----|--------|
| 5 | `fmit-week-detection-tests-V311Q` | #307 | ✅ Merged |
| 6 | `test-credentialing-ui-8ufUx` | #297 | ✅ Merged |
| 7 | `test-hub-visualization-olB8U` | #305 | ✅ Merged |
| 8 | `refactor-routes-services-yioFN` | #309 | ✅ Merged |

### Merge Order Used

All branches were merged in the following order using squash and merge:

1. ✅ PR #308: `claude/add-github-actions-cicd-NXUab` (CI/CD)
2. ✅ PR #300: `claude/add-loguru-logging-aaEGr` (Logging - resolved merge conflict)
3. ✅ PR #303: `claude/fix-pylint-backend-services-MclKI` (Pylint)
4. ✅ PR #310: `claude/add-python-type-hints-6mDTC` (Type hints)
5. ✅ PR #307: `claude/fmit-week-detection-tests-V311Q` (Frontend test)
6. ✅ PR #297: `claude/test-credentialing-ui-8ufUx` (Frontend test)
7. ✅ PR #305: `claude/test-hub-visualization-olB8U` (Frontend test)
8. ✅ PR #309: `claude/refactor-routes-services-yioFN` (Frontend test)

---

## Tier 2: Merge with Caution (Medium Risk, High Value)

These branches touch shared code but are well-structured.

### 2.1 Backend Services (Merge in Order)

**CONFLICT ZONE:** `backend/app/api/routes/resilience.py` and `backend/app/services/resilience/__init__.py`

| Branch | Changes | Dependencies |
|--------|---------|--------------|
| `refactor-routes-services-tests-HZBnt` | +2,012 lines | Contingency service - base layer |
| `refactor-routes-services-tests-OFlSX` | +831 lines | Homeostasis service - depends on above |
| `refactor-routes-services-tests-Re4oQ` | +1,154 lines | Blast radius service - depends on above |

**Merge Order:**
```bash
# These MUST be merged sequentially
git merge origin/claude/refactor-routes-services-tests-HZBnt
# Run: pytest backend/tests/services/test_contingency_service.py
git merge origin/claude/refactor-routes-services-tests-OFlSX
# Run: pytest backend/tests/services/test_homeostasis_service.py
git merge origin/claude/refactor-routes-services-tests-Re4oQ
# Run: pytest backend/tests/services/resilience/
```

### 2.2 Security & Caching

| Branch | Changes | Notes |
|--------|---------|-------|
| `add-security-headers-rate-limiting-YpXiO` | +985 lines | Middleware + tests - merge after routes |
| `add-redis-caching-1netr` | +1,623 lines | New cache service - merge after services |

### 2.3 Constraint Refactoring

| Branch | Changes | Notes |
|--------|---------|-------|
| `move-acgme-constraints-fyz8J` | +1,235 lines | Moves ACGME to services layer |
| `refactor-faculty-constraints-e4Onu` | +982 lines | Faculty constraints service |

**Merge Order for Tier 2:**
```bash
# 1. Resilience services (in order - see above)
# 2. Constraint services
git merge origin/claude/move-acgme-constraints-fyz8J
git merge origin/claude/refactor-faculty-constraints-e4Onu
# 3. Security middleware
git merge origin/claude/add-security-headers-rate-limiting-YpXiO
# 4. Redis caching (last - depends on services)
git merge origin/claude/add-redis-caching-1netr
```

---

## Tier 3: Cherry-Pick Only (Mixed Content)

These branches contain useful code mixed with problematic elements.

### 3.1 MCP Server Tools

| Branch | What to Cherry-Pick | What to Skip |
|--------|---------------------|--------------|
| `implement-validate-schedule-ntX3b` | `mcp-server/src/tools/validate_schedule.py` (+578 lines) | Verify MCP server structure matches current |

### 3.2 Frontend + MCP Mix

| Branch | What to Cherry-Pick | What to Skip |
|--------|---------------------|--------------|
| `parallel-high-yield-todos-a5EGB` | `frontend/src/lib/auth.ts`, `validation.ts` improvements | MCP changes may conflict |

### 3.3 Docstring Improvements

| Branch | What to Cherry-Pick | What to Skip |
|--------|---------------------|--------------|
| `add-jsdoc-resilience-Nrt3p` | Docstrings from `backend/app/resilience/*.py` | May conflict with Tier 2 refactors |

### 3.4 Code Review Branch

| Branch | What to Cherry-Pick | What to Skip |
|--------|---------------------|--------------|
| `review-polar-requests-ENIDS` | `docs/CODE_REVIEW_RECOMMENDATIONS.md` | Route changes already superseded |

### 3.5 Parallel Improvements

| Branch | What to Cherry-Pick | What to Skip |
|--------|---------------------|--------------|
| `parallel-high-yield-todos-9AZTo` | +10,844 lines across 44 files - needs manual review | Large, review each file |

**Cherry-Pick Strategy:**
```bash
# Example: Extract specific files
git checkout origin/claude/implement-validate-schedule-ntX3b -- mcp-server/src/tools/validate_schedule.py
git checkout origin/claude/review-polar-requests-ENIDS -- docs/CODE_REVIEW_RECOMMENDATIONS.md
```

---

## Tier 4: Archive or Skip

### 4.1 Superseded/Duplicate

| Branch | Reason to Skip |
|--------|----------------|
| `document-signal-transduction-4z2qX` | Docs only (+880 lines) - merge if docs wanted |

### 4.2 Massive/Risky

| Branch | Reason to Skip |
|--------|----------------|
| `batch-parallel-implementations-BnuSh` | **208,309 lines, 526 files, 3 migrations** - too large to merge safely. Cherry-pick specific features if needed. |

### 4.3 Research Only

| Branch | Reason to Skip |
|--------|----------------|
| `research-resiliency-scheduling-O5FaX` | +29,390 lines of research docs - archive for reference |

### 4.4 Planning Branch (Current)

| Branch | Reason to Skip |
|--------|----------------|
| `plan-branch-merge-strategy-Osewq` | This planning branch - will be deleted after merge |

---

## Conflict Hotspots

These files are touched by multiple branches - resolve carefully:

| File | Branches Touching It |
|------|---------------------|
| `backend/app/api/routes/resilience.py` | HZBnt, OFlSX, Re4oQ, review-polar |
| `backend/app/services/resilience/__init__.py` | HZBnt, OFlSX, Re4oQ |
| `backend/app/resilience/*.py` | jsdoc-resilience, refactor branches |
| `mcp-server/src/scheduler_mcp/tools.py` | implement-validate, parallel-todos |

---

## Migration Handling

Only one branch has migrations:

**`batch-parallel-implementations-BnuSh`** contains 3 new migrations:
- `20251220_add_chaos_experiments_table.py`
- `20251220_add_gateway_auth_tables.py`
- `20251220_add_scheduled_jobs_tables.py`

**Recommendation:** If you need these features, extract the migrations and related model/service code as a focused PR. Do NOT merge the entire branch.

---

## Recommended Merge Script

> **Note:** Tier 1 has been completed (2025-12-21). The script below is for Tier 2 and beyond.

```bash
#!/bin/bash
set -e

# Ensure on main and up to date
git checkout main
git pull origin main

# === TIER 1: COMPLETED (2025-12-21) ===
# All 8 Tier 1 branches have been merged via squash and merge.
# PRs: #308, #300, #303, #310, #307, #297, #305, #309

echo "=== TIER 2: Careful merges ==="

# Resilience services (ORDER MATTERS)
git merge --no-ff -m "Merge: Contingency service" origin/claude/refactor-routes-services-tests-HZBnt
cd backend && pytest tests/services/test_contingency_service.py && cd ..

git merge --no-ff -m "Merge: Homeostasis service" origin/claude/refactor-routes-services-tests-OFlSX
cd backend && pytest tests/services/test_homeostasis_service.py && cd ..

git merge --no-ff -m "Merge: Blast radius service" origin/claude/refactor-routes-services-tests-Re4oQ
cd backend && pytest tests/services/resilience/ && cd ..

# Constraint services
git merge --no-ff -m "Merge: ACGME constraints to service layer" origin/claude/move-acgme-constraints-fyz8J
git merge --no-ff -m "Merge: Faculty constraints service" origin/claude/refactor-faculty-constraints-e4Onu

# Security & caching
git merge --no-ff -m "Merge: Security headers and rate limiting" origin/claude/add-security-headers-rate-limiting-YpXiO
git merge --no-ff -m "Merge: Redis caching service" origin/claude/add-redis-caching-1netr

# Final validation
cd backend && pytest && cd ..
cd frontend && npm test && cd ..

echo "=== COMPLETE ==="
echo "Tier 3 branches require manual cherry-picking"
echo "Tier 4 branches archived - do not merge"
```

---

## Summary

| Tier | Branches | Lines Added | Status |
|------|----------|-------------|--------|
| 1 - Merge | 8 | ~5,200 | ✅ **COMPLETED** (2025-12-21) |
| 2 - Careful | 6 | ~8,800 | ⏳ Pending - Merge in order with tests |
| 3 - Cherry-pick | 5 | ~13,500 | ⏳ Pending - Extract useful parts |
| 4 - Skip | 5 | ~240,000 | 🗄️ Archive for reference |

### Completion Status

- **Tier 1:** ✅ All 8 branches merged on 2025-12-21
  - PRs: #308, #300, #303, #310, #307, #297, #305, #309
  - Method: Squash and merge via GitHub web interface
  - Note: PR #300 (logging) required merge conflict resolution

**Total merged code:** ~5,200 lines from Tier 1
**Total remaining to merge (Tier 2):** ~8,800 lines
**Total to cherry-pick (Tier 3):** ~13,500 lines (review needed)
**Total to archive (Tier 4):** ~240,000 lines (mostly batch-parallel + research docs)
