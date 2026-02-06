# ASTRONAUT BOOT SEQUENCE

**STOP. Before proceeding, read these files IN ORDER:**

1. **Identity:** `.claude/Missions/ASTRONAUT_SYSTEM_PROMPT.md` - Your role, ROE, constraints
2. **Skill:** `.claude/skills/astronaut/SKILL.md` - Detailed protocols and procedures
3. **Project:** `CLAUDE.md` - Project guidelines (skim for context)
4. **This file:** Continue reading below for your mission

---

# Mission Briefing: VALIDATE-FIX-20260110

**Classification:** VALIDATION
**Priority:** HIGH
**Issued By:** ORCHESTRATOR
**Issued At:** 2026-01-10
**Time Limit:** 10 minutes

---

## Context

Previous audit (GUI-AUDIT-20260110) found:
- HIGH-002: `/api/v1/portal/marketplace` returning 500 error
- Root cause: Missing `select` import in portal.py
- Fix applied: Added `from sqlalchemy import select` to portal.py

**Note:** The auth 401 errors were Chrome-specific in Antigravity. Use Comet browser for this validation.

---

## Objective

Verify the portal.py import fix resolved the 500 error on the marketplace API.

---

## Credentials

**Username:** admin
**Password:** admin123
**URL:** http://localhost:3000

---

## Steps

1. **Login** as admin/admin123
2. **Open DevTools** (F12) → Network tab
3. **Navigate to** `/swaps` (this triggers the marketplace API)
4. **Filter Network** for "marketplace"
5. **Check** `/api/v1/portal/marketplace`:
   - **If 200:** Fix confirmed, MISSION_COMPLETE
   - **If 500:** Document the error response, escalate
   - **If 401:** Likely browser issue, try Comet instead of Chrome

---

## Deliverables

1. Screenshot of Network tab showing marketplace response
2. Status code confirmation (200 = success)
3. Brief status in debrief

---

## Debrief Format

```markdown
# DEBRIEF: VALIDATE-FIX-20260110

**Status:** MISSION_COMPLETE | ESCALATE
**Duration:** [X] minutes

## Result

- Marketplace API: [200 | 500 | 401]
- Fix Status: [CONFIRMED | FAILED]

## Evidence

[Screenshot or error details]

## Next Steps

[If failed, what to investigate]
```

---

## Debrief Location

Write debrief to: `.claude/Missions/DEBRIEF_VALIDATE_20260110.md`

---

*Quick validation mission. 10 minutes max. Confirm the fix, move on.*
