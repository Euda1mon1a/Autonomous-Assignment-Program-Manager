# Branch Cleanup Recommendations

Generated: 2025-12-16

## Summary

- **11 remote branches** analyzed
- **9 branches** recommended for deletion (including 2 parallel-terminals)
- **1 branch** merged into this PR

---

## Completed Actions

### Merged Successfully

`claude/review-scheduling-resiliency-uvPwx` has been merged:
- Added Tier 2 strategic resilience constraints
- Zone boundary, preference trail, and N-1 vulnerability constraints
- Updated `backend/app/scheduling/constraints.py` and `engine.py`
- Updated `docs/RESILIENCE_SCHEDULING_INTEGRATION.md`

---

## Action Items

### 1. DELETE (9 branches)

```bash
# Stale/merged branches - no unique value
git push origin --delete claude/debug-macos-launch-VlAsE
git push origin --delete claude/setup-residency-scheduler-014icKoCdvbUXwm7nJrcHHUb
git push origin --delete claude/review-tasks-feedback-s6oJx
git push origin --delete claude/chatgpt-capabilities-review-gbtIG

# Stale dependabot - let it recreate fresh PRs
git push origin --delete dependabot/docker/frontend/node-25-alpine
git push origin --delete dependabot/github_actions/actions/setup-python-6
git push origin --delete dependabot/github_actions/actions/upload-artifact-6

# Superseded parallel-terminals branches (analysis below)
git push origin --delete claude/parallel-terminals-setup-P4F23
git push origin --delete claude/parallel-terminals-setup-XOcRI
```

---

## Parallel-Terminals Branch Analysis

### P4F23 Analysis (93 commits behind)

**Content (7,602 lines):**
- `backend/app/analytics/` - Reports, service
- `backend/app/notifications/` - Email, service, templates
- `backend/app/scheduling/cache.py` - Caching layer
- `backend/app/scheduling/optimizer.py` - Performance optimizer
- `backend/app/validators/` - ACGME validators, duty hours
- Tests for validators and optimizer

**Current Codebase Comparison:**
| Feature | In P4F23 | Already in HEAD |
|---------|----------|-----------------|
| Analytics | reports.py, service.py | metrics.py, engine.py, reports.py |
| Notifications | email.py, service.py, templates.py | service.py, templates.py, channels.py, tasks.py |
| Validators | advanced_acgme.py, duty_hours.py | advanced_acgme.py, fatigue_tracker.py |
| Optimizer | optimizer.py | optimizer.py |
| **Cache** | cache.py (555 lines) | **NOT PRESENT** |

**Verdict:** Most features superseded. Only `cache.py` is unique but too stale to cherry-pick.

### XOcRI Analysis (93 commits behind)

**Content (12,595 lines):**
- `docs/api/` - README, authentication.md, endpoints.md, schemas.md
- `docs/user-guide/` - absences.md, scheduling.md, getting-started.md
- `e2e/` - Playwright schedule tests (1,022 lines + 528 lines fixtures)
- `tests/integration/` - Integration test framework
- `tests/components/modals/` - Modal component tests

**Current Codebase Comparison:**
| Feature | In XOcRI | Already in HEAD |
|---------|----------|-----------------|
| API Docs | auth, endpoints, schemas | auth, endpoints, schemas (different structure) |
| User Guide | absences, scheduling | **NOT PRESENT** |
| **E2E Tests** | schedule.spec.ts, fixtures | **NOT PRESENT** |
| **Integration Tests** | Full framework | **NOT PRESENT** |
| Component Tests | Modal tests | **NOT PRESENT** |

**Verdict:** Tests are unique but 93 commits behind - would require complete rewrite.

### Recommendation: DELETE BOTH + Create Issues

Both branches are too stale for cherry-picking. Instead:

1. **Delete both branches** to clean up repository
2. **Create issues** for missing functionality:
   - "Add scheduling cache layer" (from P4F23's cache.py)
   - "Add E2E tests for schedule feature" (from XOcRI's e2e/)
   - "Add user guide documentation" (from XOcRI's docs/user-guide/)
   - "Add integration test framework" (from XOcRI's tests/integration/)

---

## Final Branch Status

| Branch | Ahead | Behind | Status |
|--------|-------|--------|--------|
| claude/debug-macos-launch-VlAsE | 0 | 24 | DELETE |
| claude/setup-residency-scheduler-* | 0 | 0 | DELETE |
| claude/review-tasks-feedback-s6oJx | 1 | 96 | DELETE |
| claude/chatgpt-capabilities-review-gbtIG | 1 | 3 | DELETE |
| dependabot/docker/frontend/node-25-alpine | 1 | 22 | DELETE |
| dependabot/github_actions/actions/setup-python-6 | 1 | 22 | DELETE |
| dependabot/github_actions/actions/upload-artifact-6 | 1 | 22 | DELETE |
| claude/parallel-terminals-setup-P4F23 | 4 | 93 | DELETE (superseded) |
| claude/parallel-terminals-setup-XOcRI | 1 | 93 | DELETE (superseded) |
| claude/review-scheduling-resiliency-uvPwx | 3 | 5 | **MERGED** |
| claude/review-consolidate-prs-2D4Mk | - | - | CURRENT |
