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
