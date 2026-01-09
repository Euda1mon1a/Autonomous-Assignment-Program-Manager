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

# Mission Briefing: PGY_INVESTIGATION_002

**Classification:** INVESTIGATION
**Priority:** HIGH
**Issued By:** ORCHESTRATOR
**Issued At:** 2026-01-09T06:45:00Z
**Time Limit:** 20 minutes

---

## Background

Mission 001 (SCHEDULE_RECON_001) discovered that the schedule page displays "PGY-" without numeric values for residents. For example, it shows "PGY-" instead of "PGY-2" or "PGY-3".

This is a HIGH priority issue because PGY (Post-Graduate Year) level is critical for:
- ACGME compliance (different rules per year)
- Supervision requirements
- Call schedules
- Rotation assignments

---

## Objective

Determine the root cause of missing PGY numbers:
1. Is the data missing from the database?
2. Is the API not returning it?
3. Is the frontend failing to display it?

---

## Target URLs (in order)

1. `http://localhost:3000/login` - Authenticate
2. `http://localhost:3000/people` - View People list
3. Click on any **resident** (not faculty) to view details
4. `http://localhost:3000/schedule` - Correlate findings

---

## Credentials

**Username:** admin
**Password:** admin123

These are LOCAL DEV credentials only.

---

## Investigation Steps

### Step 1: Login
- Navigate to `http://localhost:3000/login`
- Enter credentials: admin / admin123

### Step 2: People List Page
- Navigate to `http://localhost:3000/people`
- Screenshot the people list
- Note which columns are displayed
- Look for any PGY/Year column

### Step 3: Individual Resident Detail (CRITICAL)
- Find a person marked as "Resident" (not Faculty/Attending)
- Click to view their detail page
- Screenshot the detail view
- Look for fields like:
  - `pgy_level`
  - `training_year`
  - `year`
  - `class`
  - `graduation_year`
- Note what data IS present

### Step 4: Network Inspection (CRITICAL)
- Open DevTools (F12 or Cmd+Opt+I)
- Go to Network tab
- Reload the People page
- Find the API request to `/api/v1/people` or similar
- Click on it and view the Response
- **Screenshot the JSON response**
- Look for PGY-related fields in the response data
- Note field names and values

### Step 5: Schedule Page Correlation
- Navigate to `http://localhost:3000/schedule`
- Compare how residents are displayed
- Note if the same "PGY-" issue appears
- Check Network tab for schedule API response

---

## Success Criteria

- [ ] Successfully authenticate
- [ ] Screenshot People list page
- [ ] Screenshot individual resident detail
- [ ] **Screenshot API response JSON** (most important)
- [ ] Screenshot schedule page PGY display
- [ ] Determine root cause: data/API/frontend

---

## Data to Collect

| Item | Priority | Purpose |
|------|----------|---------|
| API response for `/api/v1/people` | HIGH | See if PGY data exists |
| Screenshot of People list | HIGH | See UI display |
| Screenshot of resident detail | HIGH | See individual data |
| Any console errors about undefined | MEDIUM | Catch frontend issues |
| Schedule page PGY display | MEDIUM | Correlate findings |

---

## Expected Findings (Hypothesis)

One of these is likely true:
1. **Field name mismatch** - API returns `training_year` but frontend expects `pgy_level`
2. **Data missing** - Field is null/undefined in database
3. **Frontend bug** - Data present but template not rendering it

---

## ROE Reminders

- **Observe only** - do not modify data
- **Screenshot everything** - evidence for debrief
- **Stay within listed URLs**
- **Abort at 20 minutes** even if incomplete

---

## Abort Conditions

- Authentication fails after 2 attempts
- Cannot find People page
- Cannot access DevTools
- 20 minute time limit exceeded

---

## Debrief Requirements

Your debrief MUST include:
1. API response payload (JSON) showing person data structure
2. Field names present in the data
3. Root cause determination (data missing / API not returning / frontend not displaying)
4. Recommended fix approach

---

## Debrief Location

Write debrief to: `.claude/Missions/DEBRIEF_[YYYYMMDD]_[HHMMSS].md`
Signal completion: Create empty `.claude/Missions/MISSION_COMPLETE`

---

*Mission briefing ends. Execute and report.*
