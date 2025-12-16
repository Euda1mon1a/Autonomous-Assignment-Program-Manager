# Branch Cleanup Recommendations

Generated: 2025-12-16

## Summary

- **11 remote branches** analyzed
- **7 branches** recommended for deletion
- **2 branches** need consolidation decision
- **1 branch** recommended for merge review

---

## Action Items

### 1. DELETE IMMEDIATELY (7 branches)

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
```

### 2. CONSOLIDATE (Decision Required)

Two branches from parallel work sessions contain different content:

| Branch | Commits Behind | Unique Content |
|--------|----------------|----------------|
| `claude/parallel-terminals-setup-P4F23` | 93 | Analytics, notifications, maintenance, caching, validators (7,602 lines) |
| `claude/parallel-terminals-setup-XOcRI` | 93 | API docs, user guides, e2e tests, integration tests (12,595 lines) |

**Options:**
- **A)** Delete both if functionality was superseded
- **B)** Cherry-pick valuable components into a fresh branch
- **C)** If needed, create issue to track re-implementation

### 3. REVIEW FOR MERGE

`claude/review-scheduling-resiliency-uvPwx` (3 ahead, 5 behind)
- Contains: Tier 2 strategic resilience constraints
- Files: `backend/app/scheduling/constraints.py`, `engine.py`, docs
- 2,041 lines of meaningful scheduling/resilience work

---

## Branch Status Details

| Branch | Ahead | Behind | Recommendation |
|--------|-------|--------|----------------|
| claude/debug-macos-launch-VlAsE | 0 | 24 | DELETE |
| claude/setup-residency-scheduler-* | 0 | 0 | DELETE (merged) |
| claude/review-tasks-feedback-s6oJx | 1 | 96 | DELETE |
| claude/chatgpt-capabilities-review-gbtIG | 1 | 3 | DELETE |
| dependabot/docker/frontend/node-25-alpine | 1 | 22 | DELETE |
| dependabot/github_actions/actions/setup-python-6 | 1 | 22 | DELETE |
| dependabot/github_actions/actions/upload-artifact-6 | 1 | 22 | DELETE |
| claude/parallel-terminals-setup-P4F23 | 4 | 93 | CONSOLIDATE |
| claude/parallel-terminals-setup-XOcRI | 1 | 93 | CONSOLIDATE |
| claude/review-scheduling-resiliency-uvPwx | 3 | 5 | REVIEW/MERGE |
| claude/review-consolidate-prs-2D4Mk | - | - | CURRENT |
