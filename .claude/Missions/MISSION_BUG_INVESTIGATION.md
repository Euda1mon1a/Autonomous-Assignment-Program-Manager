# Mission Template: Bug Investigation

> **Type:** ASTRONAUT Diagnostic Mission
> **Phase:** Bug Triage (Phase 5)
> **Workflow:** `.claude/workflows/hybrid-frontend-qa.md`

---

## Mission Briefing

**CODENAME:** BUG-[ISSUE_NUMBER]-INVESTIGATION
**CLASSIFICATION:** UNCLASSIFIED
**TIME LIMIT:** 30 minutes

---

## Bug Report

**Issue:** #[number]
**Title:** [Bug title]
**Reported By:** [reporter]
**Date:** [date]

---

## Reported Behavior

**Expected:** [what should happen]
**Actual:** [what happens instead]

---

## Reproduction Steps (from report)

1. [step 1]
2. [step 2]
3. [step 3]

---

## Investigation Checklist

### 1. Reproduction
- [ ] Can reproduce issue as described
- [ ] Identified minimum steps to reproduce
- [ ] Confirmed on [browser/device]

### 2. Console Analysis
- [ ] Captured all console errors
- [ ] Identified relevant error messages
- [ ] Checked network tab for failed requests

### 3. State Inspection
- [ ] Checked application state at failure point
- [ ] Identified triggering condition
- [ ] Tested with different data/users

### 4. Scope Assessment
- [ ] Issue isolated to specific component
- [ ] Issue affects multiple routes
- [ ] Issue is intermittent vs consistent

---

## Deliverables

1. **Reproduction Status:** Confirmed / Cannot Reproduce / Intermittent
2. **Root Cause Hypothesis:** What's likely causing the issue
3. **Affected Components:** List of files/components involved
4. **Suggested Fix:** High-level approach
5. **Regression Test:** What Playwright test should prevent recurrence

---

## Output Format

```markdown
## DEBRIEF: BUG-[ISSUE_NUMBER]-INVESTIGATION

**Status:** REPRODUCED | CANNOT_REPRODUCE | INTERMITTENT
**Duration:** [X] minutes
**Severity:** CRITICAL | HIGH | MEDIUM | LOW

### Reproduction
**Confirmed:** YES/NO/INTERMITTENT
**Steps to Reproduce:**
1. [step]
2. [step]

### Console Errors
\`\`\`
[paste error output]
\`\`\`

### Root Cause Analysis
**Hypothesis:** [what's causing the issue]
**Evidence:** [supporting observations]
**Confidence:** HIGH/MEDIUM/LOW

### Affected Components
- `frontend/src/[path]` - [description]
- `backend/app/[path]` - [if applicable]

### Suggested Fix
[High-level approach to fix the issue]

### Regression Test (for Playwright)
\`\`\`typescript
test('should not [reproduce bug]', async ({ page }) => {
  // Steps that previously caused the bug
  await page.goto('[route]');
  // ...
  // Verify correct behavior
  await expect(page.locator('[selector]')).toBeVisible();
});
\`\`\`

### Screenshots/Evidence
1. [description] - [screenshot reference]

### Recommendations
- [ ] Assign to [agent/team] for fix
- [ ] Priority: [P1/P2/P3]
- [ ] Add regression test after fix
```

---

## Rules of Engagement

1. **INVESTIGATE ONLY** - No code changes during investigation
2. **DOCUMENT EVERYTHING** - Screenshots, console logs, traces
3. **HYPOTHESIS TESTING** - Try variations to confirm root cause
4. **TIME-BOXED** - Escalate if cannot diagnose in 30 minutes

---

## Escalation Triggers

- Cannot reproduce after 3 attempts → Note in debrief, request more info
- Security vulnerability discovered → Immediate escalate to SECURITY_AUDITOR
- Backend issue suspected → Escalate to COORD_PLATFORM
- Database issue suspected → Escalate to DBA
