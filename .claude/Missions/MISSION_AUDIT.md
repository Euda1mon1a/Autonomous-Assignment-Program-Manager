# Mission Template: Full GUI Audit

> **Type:** ASTRONAUT Comprehensive Sweep
> **Phase:** Periodic Audit (Phase 4)
> **Workflow:** `.claude/workflows/hybrid-frontend-qa.md`

---

## Mission Briefing

**CODENAME:** GUI-AUDIT-[YYYYMMDD]
**CLASSIFICATION:** UNCLASSIFIED
**TIME LIMIT:** 60 minutes

---

## Objective

Comprehensive sweep of all frontend routes to identify:
- Visual regressions
- Console errors
- UX degradation
- Broken functionality
- Accessibility issues

---

## Audit Scope

### Core Routes

| Route | Priority | Last Audit |
|-------|----------|------------|
| / | HIGH | [date] |
| /login | HIGH | [date] |
| /dashboard | HIGH | [date] |
| /schedule | HIGH | [date] |
| /my-schedule | HIGH | [date] |

### Admin Routes

| Route | Priority | Last Audit |
|-------|----------|------------|
| /admin/users | HIGH | [date] |
| /admin/people | HIGH | [date] |
| /admin/templates | MEDIUM | [date] |
| /admin/scheduling | HIGH | [date] |
| /admin/health | MEDIUM | [date] |
| /admin/procedures | MEDIUM | [date] |
| /admin/compliance | HIGH | [date] |
| /admin/rotations | MEDIUM | [date] |
| /admin/audit | MEDIUM | [date] |

### Feature Routes

| Route | Priority | Last Audit |
|-------|----------|------------|
| /swaps | HIGH | [date] |
| /conflicts | HIGH | [date] |
| /compliance | HIGH | [date] |
| /resilience | MEDIUM | [date] |
| /heatmap | LOW | [date] |
| /call-roster | MEDIUM | [date] |
| /daily-manifest | MEDIUM | [date] |
| /import-export | MEDIUM | [date] |

---

## Per-Route Checklist

For each route:

1. **Load Test**
   - [ ] Page loads without crash
   - [ ] Load time acceptable (<3s)
   - [ ] No console errors

2. **Visual Check**
   - [ ] Layout correct
   - [ ] No broken images
   - [ ] Text readable
   - [ ] Responsive (resize to mobile)

3. **Functional Test**
   - [ ] Primary action works
   - [ ] Navigation works
   - [ ] Data displays correctly

4. **UX Rating**
   - Rate 1-5 (5 = excellent)
   - Note any friction points

5. **Screenshot**
   - Capture final state

---

## Output Format

```markdown
## DEBRIEF: GUI-AUDIT-[YYYYMMDD]

**Status:** MISSION_COMPLETE
**Duration:** [X] minutes
**Routes Audited:** [count]
**Issues Found:** [count]

### Executive Summary
[2-3 sentence overview of findings]

### Route Status

| Route | Load | Visual | Functional | UX | Issues |
|-------|:----:|:------:|:----------:|:--:|--------|
| / | OK | OK | OK | 5 | None |
| /login | OK | OK | OK | 4 | Minor label alignment |
| /dashboard | OK | WARN | OK | 4 | Console warning |
| ... | ... | ... | ... | ... | ... |

### Issues Found

| # | Route | Type | Severity | Description |
|---|-------|------|----------|-------------|
| 1 | /schedule | Visual | MEDIUM | Grid overflow on mobile |
| 2 | /admin/users | Console | LOW | Deprecation warning |
| ... | ... | ... | ... | ... |

### Console Errors (Aggregate)
- `/schedule`: 2 errors (TypeError, NetworkError)
- `/admin/health`: 1 warning (React key)

### UX Friction Points
1. [Route] - [Issue] - Severity: HIGH/MEDIUM/LOW
2. ...

### Regressions Detected
- [ ] [Description of regression from previous audit]

### Recommendations
1. **HIGH Priority:** [action items]
2. **MEDIUM Priority:** [action items]
3. **LOW Priority:** [action items]

### Playwright Test Gaps
Routes needing test coverage:
- `/[route]` - [what to test]
- ...

### Screenshots
[Reference to screenshot collection]

### Next Audit
Scheduled: [date]
Focus Areas: [based on findings]
```

---

## Rules of Engagement

1. **SYSTEMATIC** - Follow the route list, don't skip
2. **DOCUMENT EVERYTHING** - Screenshot each route
3. **COMPARE** - Note regressions from previous audits
4. **TIME-AWARE** - Prioritize HIGH routes if time short
5. **60 MINUTE LIMIT** - Complete what you can, note what's pending

---

## Escalation Triggers

- Critical issue blocking users → Immediate escalate
- Security vulnerability → Escalate to SECURITY_AUDITOR
- Multiple routes broken → Escalate to COORD_FRONTEND
- Backend issues suspected → Escalate to COORD_PLATFORM

---

## Cadence

| Schedule | Scope |
|----------|-------|
| Weekly | HIGH priority routes |
| Pre-release | All routes |
| Post-deploy | Smoke test (core routes) |
| Quarterly | Full audit + Playwright review |
