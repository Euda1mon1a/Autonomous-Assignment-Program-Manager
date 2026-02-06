# Mission Template: Post-Fix Validation

> **Type:** ASTRONAUT Verification Mission
> **Phase:** Post-Fix Validation (Phase 6)
> **Workflow:** `.claude/workflows/hybrid-frontend-qa.md`

---

## Mission Briefing

**CODENAME:** FIX-[ISSUE_NUMBER]-VALIDATION
**CLASSIFICATION:** UNCLASSIFIED
**TIME LIMIT:** 15 minutes

---

## Fix Details

**Issue:** #[number]
**Fix PR:** #[pr_number]
**Fixed By:** [author]
**Merged:** [date]

---

## Original Bug

**Title:** [Bug title]
**Root Cause:** [what was wrong]
**Fix Applied:** [what was changed]

---

## Validation Checklist

### 1. Primary Verification
- [ ] Original issue no longer occurs
- [ ] Feature works as expected
- [ ] No console errors

### 2. Regression Check
- [ ] Related features still work
- [ ] No new errors introduced
- [ ] Performance not degraded

### 3. Edge Cases
- [ ] Fix works with edge case data
- [ ] Fix works in different states
- [ ] Fix persists after refresh

---

## Deliverables

1. **Validation Status:** PASS / FAIL / PARTIAL
2. **Evidence:** Screenshots of working behavior
3. **Regression Notes:** Any new issues introduced

---

## Output Format

```markdown
## DEBRIEF: FIX-[ISSUE_NUMBER]-VALIDATION

**Status:** VALIDATED | FAILED | PARTIAL
**Duration:** [X] minutes

### Primary Verification
**Original Issue Fixed:** YES/NO
**Evidence:** [screenshot or description]

### Verification Steps Taken
1. [what you did]
2. [what you observed]

### Regression Check
**New Issues Found:** YES/NO
**Details:** [if any]

### Console Status
- Errors: [count]
- Warnings: [count]

### Final Assessment
**Recommendation:** CLOSE ISSUE | REOPEN | NEEDS FOLLOW-UP

### Screenshots
1. [Working state] - [reference]

### Notes
[Any additional observations]
```

---

## Rules of Engagement

1. **QUICK VERIFICATION** - This is a spot-check, not deep exploration
2. **EVIDENCE REQUIRED** - Screenshot the working state
3. **REGRESSION AWARE** - Watch for new issues
4. **15 MINUTE LIMIT** - Escalate if complex

---

## Outcomes

| Result | Action |
|--------|--------|
| VALIDATED | Close issue, consider Playwright test |
| FAILED | Reopen issue with evidence |
| PARTIAL | Document what works/doesn't, assign for follow-up |
