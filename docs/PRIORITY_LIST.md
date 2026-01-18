# Repository Priority List

> **Generated:** 2025-12-19
> **Purpose:** Consolidated, verified priority list for repository improvements
> **Supersedes:** Outdated sections of ARCHITECTURAL_DISCONNECTS.md

---

## Executive Summary

After comprehensive analysis, this document identifies **active priorities** vs. **already-resolved issues**. Many items documented in ARCHITECTURAL_DISCONNECTS.md have been completed but the document was not updated.

---

## Status of Previously Documented Issues

### RESOLVED ISSUES (No Action Needed)

| Issue | Original Description | Status |
|-------|---------------------|--------|
| #6 | Unauthenticated Routes | **FIXED** - All 4 routes now have `get_current_active_user` |
| #4 | SwapExecutor Facade | **FIXED** - `_update_schedule_assignments()` now has real implementation |
| #2 | Resilience Disabled by Default | **PARTIALLY FIXED** - Tier 1 constraints (HubProtection, UtilizationBuffer) now enabled by default |

### REMAINING ISSUES (Action Required)

| Priority | Issue | Severity | Effort | Description |
|----------|-------|----------|--------|-------------|
| **DONE** | #14 API Session No Rollback | HIGH | LOW | ~~`get_db()` doesn't rollback on exception~~ **FIXED 2025-12-19** |
| **DONE** | #1 Email Disconnect | HIGH | MEDIUM | ~~Notification tasks stubbed~~ **FIXED 2025-12-19** - EmailService now wired in |
| **DONE** | #10 Celery Retry Broken | MEDIUM | LOW | ~~No retry calls~~ **FIXED 2025-12-19** - Tasks now use `autoretry_for` + `bind=True` |
| **DONE** | #11 Timezone Inconsistency | LOW | TRIVIAL | ~~`datetime.now()` used~~ **FIXED 2025-12-19** |
| **DONE** | Documentation Sprawl | LOW | LOW | ~~wiki duplicates docs/~~ **FIXED 2025-12-19** - wiki deleted, backed up to docs/archived/wiki-backup |

---

## HIGHEST-YIELD PRIORITY

### P0: Fix API Session Rollback (#14)

**Why this is highest-yield:**
- **Impact**: Protects EVERY API endpoint from data corruption
- **Effort**: ~10 lines of code
- **Risk**: Currently, exceptions after DB writes can leave dirty session state
- **Foundational**: This is infrastructure that all other code depends on

**Current Code** (`backend/app/db/session.py`):
```python
def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()  # ONLY CLOSES - NO ROLLBACK!
```

**Required Fix**:
```python
def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
        db.commit()  # Commit on success
    except Exception:
        db.rollback()  # Rollback on error
        raise
    finally:
        db.close()
```

---

## DOCUMENTATION CONSOLIDATION PRIORITIES

### Root-Level Files (15 files - reduce to ~5)

**Keep as-is:**
- `README.md` - Project entry point
- `CLAUDE.md` - AI guidance
- `CONTRIBUTING.md` - Contributor guide
- `CHANGELOG.md` - Version history
- `.env.example` - Config template

**Move to docs/:**
| File | Destination | Rationale |
|------|-------------|-----------|
| `ROADMAP.md` | `docs/planning/ROADMAP.md` | Planning document |
| `ARCHITECTURE.md` | `docs/architecture/ARCHITECTURE.md` | Already duplicated in docs/ |
| `USER_GUIDE.md` | `docs/user-guide/USER_GUIDE.md` | User documentation |
| `AGENTS.md` | `docs/development/AGENTS.md` | Development docs |
| `MACOS.md` | `docs/getting-started/macos-deploy.md` | Deployment docs |
| `DOCKER_LOCAL_*.md` (2) | `docs/getting-started/` | Setup docs |
| `SCHEDULER_OPS_QUICK_START.md` | `docs/guides/` | Guide |
| `STRATEGIC_DECISIONS.md` | `docs/planning/` | Planning |
| `NOTEBOOKLM_STATE_DOCUMENT.md` | `docs/archived/` | Session artifact |

**Remove/Archive:**
- `HUMAN_TODO.md` - Only 3 items, merge into ROADMAP

### Wiki Directory (11 files - deprecate)

The `wiki/` directory duplicates content in `docs/`. Recommend:
1. Verify no unique content exists in wiki/
2. Delete wiki/ directory
3. Use docs/ as single source of truth

### Research Documents (consolidate)

Currently scattered:
- `docs/research/` (3 files)
- `docs/planning/research/` (6 files)

Consolidate all to `docs/research/` or archive completed research.

---

## TECHNICAL DEBT PRIORITY LIST

### High Priority (Should Fix Soon)

1. **API Session Rollback** - Data integrity risk
2. **Email Service Wiring** - Notifications don't actually send
3. **Celery Task Retry Logic** - Failed tasks don't retry

### Medium Priority (Plan for Next Sprint)

4. **Test Coverage for 15 Untested Routes** - Many API routes lack test files
5. **Frontend Hook Split** - hooks.ts is ~1200 lines
6. **TypeScript `any` Cleanup** - Type safety bypassed

### Low Priority (Backlog)

7. **Timezone Standardization** - Minor consistency issue
8. **Documentation Consolidation** - Reduce maintenance burden
9. **OWNERSHIP.md Consolidation** - 8 scattered ownership files
10. **LecturePro AI Integration (External)** - AI-powered presentation tool for educational content
    - Location: `~/Downloads/lecturepro-ai` (local reference)
    - Features: Gemini-based slide generation, presenter mode, PDF/PPTX export
    - Use case: Training presentations, orientation materials

---

## CODE QUALITY QUICK WINS

These can be done in parallel with any work:

1. **Replace `datetime.now()` with `datetime.utcnow()`** (3 occurrences in notifications/tasks.py)
2. **Add JSDoc to undocumented frontend hooks**
3. **Remove empty catch blocks in frontend** (14+ locations)

---

## NEXT STEPS

1. Implement P0: API Session Rollback fix
2. Update ARCHITECTURAL_DISCONNECTS.md to reflect resolved issues
3. Begin documentation consolidation (move root files to docs/)
4. Wire EmailService into notification tasks (P1)
5. Add Celery retry logic (P1)

---

*This document should be kept current as issues are resolved.*
*Last verified: 2025-12-19*
