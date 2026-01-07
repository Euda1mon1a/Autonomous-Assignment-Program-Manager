# Quality Gate Specification for 16 GUI Bug Fixes

## Overview

This directory contains the complete quality gate specification for verifying 16 GUI bugs across the Residency Scheduler frontend.

**Key Facts:**
- 16 bugs organized by severity: 3 P0 (critical), 7 P1 (features), 6 P2 (polish)
- ~10 new automated test files required
- 2-3 hours manual UAT per batch
- 3 bugs flagged as hard-to-verify (require special testing)
- Total effort: ~20-25 hours (dev + QA + design review)

---

## Documents

### 1. **QUALITY_GATE_SPEC.md** (Detailed Reference)
The authoritative specification document. Contains:
- Full acceptance criteria for all 12 bugs
- Automated vs. manual verification strategy
- Test file recommendations (which tests to create/enhance)
- Special flags for hard-to-verify bugs
- Verification checklist template

**Use this when:** Writing code to understand what "done" means
**Reference:** 245 lines, ~10 sections per bug

---

### 2. **QUALITY_GATE_SUMMARY.txt** (Executive Summary)
High-level overview for stakeholders. Contains:
- Bug categorization table
- Acceptance criteria (bulleted, concise)
- Hard-to-verify flags with justification
- Effort estimation
- Quality gates (CI-level + manual)

**Use this when:** Presenting to stakeholders, planning sprints
**Reference:** 112 lines, fits on 1-2 pages

---

### 3. **TEST_CHECKLIST.md** (Test Developer Guide)
Detailed test implementation guide with:
- Copy-paste-ready test checklists for each bug
- Specific test assertions (exact Jest patterns)
- Mock data requirements
- Manual verification steps
- Universal test best practices
- Troubleshooting guide

**Use this when:** Writing Jest tests
**Reference:** 347 lines, ~1 section per bug + universal checklist

---

### 4. **QUICK_REFERENCE.txt** (Cheat Sheet)
Single-page reference for developers. Contains:
- Bug table (ID, severity, component, test type)
- Acceptance criteria (one-liners)
- Test file list (create vs. enhance)
- Common test patterns (copy-paste snippets)
- Verification batches
- Commands (npm test, lint, build)
- Escalation paths

**Use this when:** Need quick answers during development
**Reference:** 230 lines, everything on one document

---

## Quick Start

### For Developers Fixing Bugs

1. **Read:** `QUALITY_GATE_SPEC.md` section for your bug
2. **Write Tests:** Copy test checklist from `TEST_CHECKLIST.md`
3. **Reference:** Use `QUICK_REFERENCE.txt` for common patterns
4. **Verify:** Run `npm test` and check all assertions pass

### For QA / Manual Testers

1. **Read:** `QUALITY_GATE_SUMMARY.txt` for overview
2. **Use:** Verification checklist in `QUALITY_GATE_SPEC.md`
3. **Check:** Each bug's acceptance criteria
4. **Flag:** Hard-to-verify bugs (bugs #8, #9, #10)

### For Stakeholders

1. **Read:** `QUALITY_GATE_SUMMARY.txt` (executive summary)
2. **Check:** Effort estimation and quality gates
3. **Review:** Hard-to-verify flags and special considerations

---

## Bug Categorization

### P0 Critical (Release Blockers)
| Bug | Component | Auto Test | Manual |
|-----|-----------|-----------|--------|
| #1 | Block 0 Dates | Jest | Calendar UI |
| #2 | Conflicts API 404 | Jest | Curl + UI |
| #3 | Swap Permissions | Jest | Cross-resident swap |

### P1 Feature-Critical
| Bug | Component | Auto Test | Manual |
|-----|-----------|-----------|--------|
| #4 | Month/Week Views | Jest | Toggle views |
| #5 | Call Roster | Jest | Check page |
| #6 | Import Table | Jest | Upload CSV |
| #7 | CSV Export | Jest | Download file |

### P2 Polish
| Bug | Component | Auto Test | Manual | Special |
|-----|-----------|-----------|--------|---------|
| #8 | Sticky Header | None | Scroll test | Visual regression |
| #9 | Nav Dropdowns | Jest | Mobile test | Responsive testing |
| #10 | Manifest Redesign | Jest | Visual | Design review |
| #11 | People Card Click | Jest | Navigation | None |
| #12 | PGY Filter | Jest | Filter test | None |

---

## Test Files Overview

### New Test Files to Create (6 files)
```
frontend/__tests__/components/schedule/ScheduleCalendar.test.tsx
frontend/__tests__/components/schedule/MonthView.test.tsx
frontend/__tests__/components/schedule/PersonalScheduleCard.test.tsx
frontend/__tests__/components/MobileNav.test.tsx
frontend/__tests__/features/import-export/ImportPreview.test.tsx
frontend/__tests__/features/daily-manifest/DailyManifest.test.tsx
```

### Existing Test Files to Enhance (4 files)
```
frontend/__tests__/features/conflicts/ConflictsList.test.tsx → Add 404 handling
frontend/__tests__/features/swap-marketplace/SwapRequestForm.test.tsx → Add permission tests
frontend/__tests__/features/call-roster/CallRoster.test.tsx → Add empty state
frontend/__tests__/components/ExcelExportButton.test.tsx → Add export flow
```

---

## Verification Batches

### Batch 1: Critical (P0)
**Duration:** ~4 hours CI
**Scope:** Bugs #1, #2, #3
**Deliverables:** 3 new tests + 2 enhanced tests + manual UAT
**Gate:** All tests pass + P0 acceptance criteria verified

### Batch 2: Features (P1)
**Duration:** ~3 hours CI
**Scope:** Bugs #4, #5, #6, #7
**Deliverables:** 4 new tests + 3 enhanced tests + integration verification
**Gate:** All tests pass + API endpoints verified

### Batch 3: Polish (P2)
**Duration:** ~2-3 hours manual
**Scope:** Bugs #8, #9, #10, #11, #12
**Deliverables:** 3 new tests + visual regression tests + design review
**Gate:** Visual tests pass + design approved + UX verified on mobile

---

## Hard-to-Verify Bugs

These bugs require special testing beyond standard Jest:

### Bug #8: Sticky Header
**Challenge:** CSS behavior can't be fully tested with Jest
**Required Tests:**
- Visual regression testing (Playwright or Chromatic)
- Manual scroll verification on desktop/mobile
**Action Items:**
- Add to Playwright visual test suite
- Capture baseline screenshot in main branch
- Compare against fix branch

### Bug #9: Nav Dropdowns
**Challenge:** Mobile interactions differ from desktop
**Required Tests:**
- Jest tests with mobile viewport mock
- OR device testing on actual mobile
**Action Items:**
- Mock viewport: `{ width: 375, height: 667 }`
- Test touch events if applicable
- Manual verification on iOS/Android

### Bug #10: Manifest Redesign
**Challenge:** Visual design is subjective
**Required Tests:**
- Visual regression testing
- Design review with product owner
**Action Items:**
- Get design mockup approval
- Capture screenshots for Chromatic
- Product owner sign-off in PR comments

---

## Quality Gates

### CI Gates (Automated)
```
npm test           # All Jest tests pass
npm run lint:fix   # No lint errors
npm run build      # Build succeeds
npm run type-check # No TypeScript errors
```

### Visual Gates (Playwright)
```
npm run test:visual            # Screenshots match baseline
npm run test:visual -- --update # Update baseline after approved changes
```

### Manual Gates
```
[ ] P0 bugs verified in UI
[ ] No new accessibility regressions
[ ] Mobile responsiveness verified (3 breakpoints)
[ ] Design changes approved by product owner
```

---

## Testing Patterns

### Mocking Hooks
```typescript
jest.mock('@/lib/hooks', () => ({
  useAssignments: jest.fn(),
  usePeople: jest.fn(),
}))
```

### Date Testing
```typescript
function localDate(year: number, month: number, day: number): Date {
  return new Date(year, month - 1, day) // month is 0-indexed
}
```

### Async Testing
```typescript
await waitFor(() => {
  expect(screen.getByText('Loaded')).toBeInTheDocument()
})
```

See `TEST_CHECKLIST.md` for more patterns.

---

## Commands

```bash
# Run tests
npm test
npm test -- CallRoster              # Pattern match
npm test -- --coverage              # With coverage
npm test -- --watch                 # Watch mode
npm test -- --testNamePattern="404" # Specific test

# Code quality
npm run lint:fix    # Auto-fix lint errors
npm run type-check  # TypeScript validation
npm run build       # Build check

# Visual testing
npm run test:visual              # Take screenshots
npm run test:visual -- --update  # Update baseline
```

---

## Support & Escalation

### If a Test Fails
1. Read the error message carefully
2. Verify mock data matches component expectations
3. Check DOM selectors (data-testid values)
4. Verify async handling (use waitFor)
5. Run test in isolation: `npm test -- --testNamePattern="test name"`
6. Ask for help if stuck >15 minutes

### If a Visual Issue Appears
1. Check CSS is applied (browser DevTools)
2. Compare to design mockup
3. Check responsive breakpoints
4. Flag for design review if subjective

### If an API Issue Occurs
```bash
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/v1/endpoint
docker-compose logs backend  # Check backend logs
```

---

## Effort Estimation

| Phase | Task | Hours | Effort |
|-------|------|-------|--------|
| Dev | Code fixes for 16 bugs | 12 | Low-Medium |
| Dev | 10 new/enhanced tests | 6 | Medium |
| QA | Manual P0 UAT | 2 | Low |
| QA | Manual P1 integration | 1 | Low |
| QA | Manual P2 UX + design | 2 | Medium |
| Design | Manifest redesign review | 1 | Low |
| CI/CD | Visual regression setup | 2 | Medium |
| **Total** | | **~25 hours** | |

---

## Document Index

```
.claude/QA/
├── README.md                      (this file - overview & index)
├── QUALITY_GATE_SPEC.md          (detailed specs, 245 lines)
├── QUALITY_GATE_SUMMARY.txt      (executive summary, 112 lines)
├── TEST_CHECKLIST.md             (test implementation guide, 347 lines)
└── QUICK_REFERENCE.txt           (cheat sheet, 230 lines)

Total: 4 supporting documents, ~934 lines, covers all 16 bugs
```

---

## Next Steps

1. **Developers:** Start with `QUALITY_GATE_SPEC.md` for your bug
2. **Test Writers:** Use `TEST_CHECKLIST.md` as test template
3. **QA:** Reference `QUALITY_GATE_SPEC.md` for manual verification
4. **Stakeholders:** Share `QUALITY_GATE_SUMMARY.txt` for executive overview
5. **All:** Keep `QUICK_REFERENCE.txt` handy for quick lookup

---

## Contact & Questions

For questions about:
- **Test implementation:** See `TEST_CHECKLIST.md` troubleshooting
- **Acceptance criteria:** See `QUALITY_GATE_SPEC.md` for your bug
- **Effort/timeline:** See `QUALITY_GATE_SUMMARY.txt` estimation
- **Quick answers:** See `QUICK_REFERENCE.txt` cheat sheet
