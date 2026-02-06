# ASTRONAUT BOOT SEQUENCE

**STOP. Before proceeding, read these files IN ORDER:**

1. **Identity:** `.claude/Missions/ASTRONAUT_SYSTEM_PROMPT.md` - Your role, ROE, constraints
2. **Skill:** `.claude/skills/astronaut/SKILL.md` - Detailed protocols and procedures
3. **Project:** `CLAUDE.md` - Project guidelines (skim for context)
4. **This file:** Continue reading below for your mission

After reading those files, you will understand:
- Who you are (ASTRONAUT - field operative)
- What you can/cannot do (ROE)
- How to report (debrief format)
- Project context (Residency Scheduler)

---

# Mission Briefing: SCHEDULE_RECON_001

**Classification:** RECON
**Priority:** NORMAL
**Issued By:** ORCHESTRATOR
**Issued At:** 2026-01-09T06:15:00Z
**Time Limit:** 15 minutes

---

## Objective

Perform reconnaissance on the schedule page GUI. Log in, navigate to schedule views, and report on:
1. Visual state of the UI
2. Any console errors
3. Network request health
4. Overall user experience issues

---

## Target URLs

1. `http://localhost:3000/login` - Authenticate with test credentials
2. `http://localhost:3000/schedule` - Main schedule view
3. `http://localhost:3000/admin/schedule` - Admin schedule view (if accessible)

---

## Credentials

**Username:** admin
**Password:** admin123

These are LOCAL DEV credentials only. Never use on production.

---

## Success Criteria

- [ ] Successfully authenticate
- [ ] View schedule page loads without crash
- [ ] Document any console errors (React, Next.js, API)
- [ ] Note any failed network requests (4xx, 5xx)
- [ ] Assess overall GUI functionality

---

## Specific Instructions

1. Navigate to `http://localhost:3000/login`
2. Enter credentials: admin / admin123
3. After login, navigate to schedule page
4. Open browser DevTools (F12 or Cmd+Opt+I)
5. Check Console tab for errors
6. Check Network tab for failed requests
7. Interact with schedule UI - try selecting dates, blocks, etc.
8. Note any UI glitches, missing data, or broken features
9. Write comprehensive debrief

---

## Data to Collect

- [ ] Screenshot of login page
- [ ] Screenshot of main schedule view
- [ ] All console errors (copy full text)
- [ ] Any network requests returning 4xx or 5xx
- [ ] List of features that work vs. don't work
- [ ] Any slow-loading elements (>3 seconds)

---

## ROE Reminders

- **Observe only** - no modifications to code or data
- **Stay within listed URLs** - don't explore admin panels beyond schedule
- **Abort if credentials requested** for anything other than localhost
- **Time-boxed** - stop at 15 minutes even if incomplete

---

## Abort Conditions

- Authentication fails after 2 attempts
- Asked for production credentials
- Page requires permissions you don't have
- Browser crashes or hangs
- 15 minute time limit exceeded

---

## Debrief Location

Write debrief to: `.claude/Missions/DEBRIEF_[YYYYMMDD]_[HHMMSS].md`
Signal completion: Create empty `.claude/Missions/MISSION_COMPLETE`

---

*Mission briefing ends. Execute and report.*
