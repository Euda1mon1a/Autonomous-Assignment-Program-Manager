# Session 14: IDE Deployment & Multi-AI Review Setup

**Date:** 2025-12-20 (UTC-10, HST)
**Duration:** ~3 hours
**Environment:** Antigravity IDE (macOS) with Claude + Codex integration

---

## Summary

First deployment session from the new Antigravity IDE environment. Established a three-AI workflow for code development and review, fixed local Docker deployment issues, and created infrastructure for ongoing development.

---

## Accomplishments

### 1. Developer Tooling Setup
- ✅ Installed GitHub CLI (`gh`) for PR management from terminal
- ✅ Installed OpenAI Codex CLI for independent code review
- ✅ Configured multi-AI workflow: Claude (implementation) → Codex (review) → iterate

### 2. Workflow Documentation
- ✅ Created `.agent/workflows/deploy-and-test.md`
- ✅ 4 rounds of Codex review with fixes applied
- ✅ Merged as PR #337

### 3. Local Docker Deployment Fixes
- ✅ Fixed `scipy` compilation (pinned to 1.15.3 for ARM64 wheel support)
- ✅ Fixed `pyqubo` numpy 2.x incompatibility (commented out)
- ✅ Added build dependencies to `Dockerfile.local` (gfortran, libopenblas-dev)
- ✅ Fixed Alembic migration chain (duplicate revision ID 018 → 019_fmit)
- ✅ All 7 Docker services running (healthchecks passing where defined)

### 4. Test Data Seeding
- ✅ Created admin user (credentials stored locally, not in repo)
- ✅ Created 10 faculty members with role assignments
- ✅ Created `scripts/seed_people.py` for future use

### 5. Security Verification
- ✅ Confirmed token security fixes are in place (PRs #327, #328)
- ✅ Refresh token privilege escalation: FIXED
- ✅ Refresh token reuse after rotation: FIXED

---

## Known Issues

### Resident Creation 500 Error
**Location:** Backend logger in exception handler
**Symptom:** Creating residents returns 500 Internal Server Error
**Root Cause:** KeyError on `'id'` in logging format string when handling exceptions
**Impact:** Cannot seed resident data via API
**Workaround:** Faculty creation works; direct database seeding possible

### Backend Crash Loop (Resolved)
**Symptom:** Backend container restarts endlessly.
**Root Cause:** `numpy==2.3.5` incompatible with legacy `pyspc` and `manufacturing` libraries.
**Fix:** Downgraded to `numpy==1.26.4` in `backend/requirements.txt`.

### PII Scrub Side Effects (Session 14b - Claude)
**Symptom:** After running `git-filter-repo` to remove PII from branch history, backend fails with `SyntaxError: invalid syntax`.
**Root Cause:** The PII replacement file had entries like `literal:Tagawa==>FAC-PD` which inadvertently replaced `# Faculty` comments with `***REMOVED***` throughout the codebase (~30+ files).
**Affected Areas:**
- `backend/app/models/__init__.py` - Broken `__all__` list
- `backend/alembic/versions/*.py` - Broken column comments
- `backend/app/scheduling/*.py` - Broken code comments
- `backend/app/resilience/*.py` - Broken code comments
- `backend/tests/*.py` - Broken test comments
**Fix:** Run `find backend -name "*.py" -exec sed -i '' 's/\*\*\*REMOVED\*\*\*/# Faculty/g' {} \;`
**Prevention:** Use more specific replacement patterns (e.g., full names only, not last names in isolation).

### Docker Desktop File Sync Issue (Session 14b - Claude)
**Symptom:** Backend container sees old/stale Python files despite local edits.
**Evidence:** Local file has 255 lines, container sees 157 lines (MD5 mismatch).
**Root Cause:** Docker Desktop macOS file sync (VirtioFS/gRPC FUSE) can cache stale files.
**Fix:** Restart Docker Desktop to force file system refresh.
**Workaround:** Use `docker-compose up -d --build` to rebuild image instead of relying on volume mounts.

### Missing Function Exports (Session 14b - Claude)
**Symptom:** `ImportError: cannot import name 'X' from 'app.Y'`
**Examples Found:**
- `invalidate_schedule_cache` not exported from `app.core.cache`
- `validate_academic_year_date` missing from `app.validators.date_validators`
- `require_role` missing from `app.core.security`
**Root Cause:** Code references functions that either don't exist or aren't exported in `__init__.py`.
**Fix:** Add missing exports or create stub implementations.

---

## Files Changed

| File | Change |
|------|--------|
| `backend/Dockerfile.local` | Added gfortran, libopenblas-dev for scipy |
| `backend/requirements.txt` | Pinned scipy, commented pyqubo/dwave |
| `backend/alembic/versions/20241217_*.py` | Fixed revision ID 018 → 019_fmit |
| `backend/alembic/versions/20251219_*.py` | Fixed down_revision chain |
| `.agent/workflows/deploy-and-test.md` | New workflow file |
| `scripts/seed_people.py` | New seeding script |

---

## Multi-AI Workflow Established

```
┌─────────────────────────────────────────────────────────┐
│                    USER (Direction)                      │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│               CLAUDE (Implementation)                    │
│         Antigravity IDE - file/terminal access          │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│            CODEX (Independent Review)                    │
│          Terminal TUI - `codex` command                  │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
                    Iterate/Merge
```

---

## Local Development URLs

| Service | URL | Status |
|---------|-----|--------|
| Frontend | http://localhost:3000 | ✅ Running |
| Backend API | http://localhost:8000 | ✅ Healthy |
| API Docs | http://localhost:8000/docs | ✅ Available |
| n8n Workflows | http://localhost:5679 | ✅ Running |

---

## Next Session Priorities

1. [ ] Fix backend logger KeyError bug for resident creation
2. [ ] Seed remaining test data (18 residents)
3. [ ] Test schedule generation end-to-end
4. [ ] Document any additional deployment gotchas

---

## Commands Reference

```bash
# Deploy locally
docker compose -f docker-compose.local.yml up -d

# View logs
docker compose -f docker-compose.local.yml logs -f backend

# Seed data
python3 scripts/seed_people.py

# Codex review
codex "Review <file> for bugs and security issues"

# Create PR
gh pr create --fill
```
