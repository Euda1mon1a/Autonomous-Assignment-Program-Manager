# Mission Template: Feature Exploration

> **Type:** ASTRONAUT Exploratory Mission
> **Phase:** Development (Phase 1)
> **Workflow:** `.claude/workflows/hybrid-frontend-qa.md`

---

## Mission Briefing

**CODENAME:** [FEATURE_NAME]-EXPLORATION
**CLASSIFICATION:** UNCLASSIFIED
**TIME LIMIT:** 30 minutes

---

## Objective

Explore a new or updated feature to discover issues before formal testing.

---

## Target

**URL:** http://localhost:3000/[route]
**Feature:** [Brief description]
**Branch:** [feature-branch-name]

---

## Reconnaissance Checklist

### 1. Initial Load
- [ ] Page loads without crash
- [ ] No console errors on load
- [ ] Layout renders correctly
- [ ] All expected elements visible

### 2. Interactive Elements
- [ ] All buttons clickable
- [ ] Forms accept input
- [ ] Dropdowns/selects work
- [ ] Navigation functions correctly

### 3. User Flows
- [ ] Primary action (happy path) succeeds
- [ ] Error states display correctly
- [ ] Loading states visible during operations
- [ ] Success feedback provided

### 4. Edge Cases
- [ ] Empty state handled
- [ ] Large data sets render
- [ ] Invalid input rejected gracefully
- [ ] Network errors handled

### 5. Visual Quality
- [ ] No layout breaks
- [ ] Responsive at common breakpoints
- [ ] Consistent with design system
- [ ] Accessibility basics (contrast, labels)

---

## Deliverables

1. **Screenshots:** Capture each significant state
2. **Console Log:** Document any errors/warnings
3. **UX Friction:** Note confusing or slow interactions
4. **Happy Path:** Document the successful user journey
5. **Playwright Candidates:** Suggest test cases to encode

---

## Output Format

```markdown
## DEBRIEF: [FEATURE_NAME]-EXPLORATION

**Status:** MISSION_COMPLETE | MISSION_BLOCKED | MISSION_ESCALATE
**Duration:** [X] minutes
**Findings:** [summary]

### Screenshots
1. [description] - [screenshot reference]
2. ...

### Console Errors
- [error 1]
- [error 2]

### UX Friction Points
1. [issue] - Severity: HIGH/MEDIUM/LOW
2. ...

### Happy Path (for Playwright)
1. Navigate to [route]
2. [action 1]
3. [action 2]
4. Verify [expected result]

### Recommended Playwright Tests
1. `test('[test name]', async ({ page }) => { ... })`
2. ...

### Issues Found
| Issue | Severity | Suggested Fix |
|-------|----------|---------------|
| [desc] | HIGH/MED/LOW | [fix] |

### Next Steps
- [ ] Fix issues before stabilization
- [ ] Create Playwright tests for happy path
- [ ] Schedule follow-up validation
```

---

## Rules of Engagement

1. **OBSERVE AND DOCUMENT** - No code changes
2. **STAY IN SCOPE** - Only test the target feature
3. **TIME-BOXED** - Abort at 30 minutes
4. **ABORT if uncertain** - Document ambiguity in debrief

---

## Escalation Triggers

- Feature fundamentally broken → Escalate to COORD_FRONTEND
- Security issue found → Escalate to SECURITY_AUDITOR
- Needs backend investigation → Escalate to COORD_PLATFORM
