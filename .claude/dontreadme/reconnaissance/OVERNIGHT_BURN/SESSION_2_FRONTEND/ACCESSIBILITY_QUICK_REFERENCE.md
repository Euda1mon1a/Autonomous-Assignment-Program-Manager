# Frontend Accessibility Quick Reference Guide

**Document:** `/Users/aaronmontgomery/Autonomous-Assignment-Program-Manager/.claude/Scratchpad/OVERNIGHT_BURN/SESSION_2_FRONTEND/frontend-accessibility-audit.md`

**Status:** 861-line comprehensive audit completed
**Date:** 2025-12-30

---

## Critical Findings Summary

### ARIA Implementation
- **67 instances** of aria-label/aria-labelledby (GOOD)
- **57 instances** of dynamic ARIA (aria-expanded, aria-hidden, aria-live, aria-busy)
- **70+ focus:ring** implementations across components
- **322 semantic HTML** elements (headings, sections, nav, etc.)

### Key Problems Found

| Issue | Severity | Files | Impact |
|-------|----------|-------|--------|
| role="button" on divs | CRITICAL | CellActions.tsx, TimeSlot.tsx | Blocks WCAG Level A |
| Tabs missing arrow keys | HIGH | Tabs.tsx | WCAG violation |
| No modal focus trap | MEDIUM | ConfirmDialog.tsx | Best practice gap |
| Color contrast gaps | MEDIUM | Button.tsx, Input.tsx | AA compliance risk |
| ScheduleCell no keyboard | MEDIUM | ScheduleCell.tsx | Keyboard access failure |

### Compliance Status

```
WCAG 2.1 Level A:   ~90% (role-button fixes needed)
WCAG 2.1 Level AA:  ~75% (color contrast, focus traps)
WCAG 2.1 Level AAA: ~60% (advanced features sparse)
```

---

## Priority Fixes (In Order)

### Priority 1: CRITICAL (Week 1)
1. Replace `role="button"` divs with native `<button>` elements
2. Add ArrowLeft/Right keyboard navigation to Tabs component
3. Fix color contrast (disabled buttons, placeholders, gray-400 icons)

### Priority 2: HIGH (Week 2-3)
4. Add focus trap to modals
5. Add focus restoration after modal closes
6. Enhance ScheduleCell with aria-label + keyboard support
7. Add keyboard navigation to MultiSelect

### Priority 3: MEDIUM (Week 3-4)
8. Add aria-expanded to disclosure toggles
9. Improve Tooltip with aria-describedby
10. Add screen reader-only context (sr-only elements)

---

## Component Accessibility Scores

| Component | Score | Main Issue | Effort |
|-----------|-------|-----------|--------|
| Button.tsx | A | None | N/A |
| Input.tsx | A | Placeholder contrast | 1h |
| Select.tsx | A- | Verify contrast | 0.5h |
| Dropdown.tsx | B+ | Add aria-expanded | 1h |
| Tabs.tsx | B | Add arrow nav | 2h |
| Alert.tsx | A | None | N/A |
| ConfirmDialog.tsx | B+ | Add focus trap | 2h |
| Tooltip.tsx | C+ | Add aria-describedby | 1.5h |
| MultiSelect.tsx | B | Add keyboard nav | 2h |
| ScheduleCell.tsx | C | Add keyboard access | 2h |
| ScheduleGrid.tsx | B- | Add semantic headers | 1h |
| CellActions.tsx | D | **Replace with button** | 2h |
| TimeSlot.tsx | D | **Replace with button** | 2h |

**Total Effort:** ~18 hours to fix all issues

---

## Quick Wins (High ROI)

1. **Fix color contrast** (1h)
   - Disabled buttons: use stronger opacity
   - Placeholders: change gray-400 to gray-500
   - Icons: add darker shade or background

2. **Add focus traps** (2h)
   - Use provided useFocusTrap hook pattern
   - Test with Tab key navigation

3. **Replace role-button divs** (2h)
   - Simple find-replace + test
   - Biggest compliance win

---

## Testing Checklist

Before merging any accessibility changes:

```
[ ] All tests pass: npm test
[ ] Axe DevTools audit: 0 violations
[ ] Keyboard Tab navigation: All interactive elements reachable
[ ] Keyboard Enter/Space: All buttons respond
[ ] Screen reader test: NVDA/JAWS announces key content
[ ] Color contrast: All text meets WCAG AA (4.5:1)
[ ] Focus indicators: Visible on all interactive elements
```

---

## Key ARIA Patterns Used

### 1. Alert Pattern
```tsx
<div role="alert">
  Error message here
</div>
```

### 2. Dialog Pattern
```tsx
<div
  role="alertdialog"
  aria-modal="true"
  aria-labelledby="dialog-title"
  aria-describedby="dialog-description"
>
  <h2 id="dialog-title">Title</h2>
  <p id="dialog-description">Content</p>
</div>
```

### 3. Tab Pattern
```tsx
<div role="tablist">
  <button role="tab" aria-selected={active} aria-controls={`panel-${id}`}>
    Tab Label
  </button>
</div>
<div role="tabpanel" id={`panel-${id}`} aria-labelledby={id}>
  Content
</div>
```

### 4. Form Validation Pattern
```tsx
<input
  aria-invalid={hasError}
  aria-describedby={hasError ? 'error-id' : undefined}
/>
{hasError && <p id="error-id" role="alert">{errorMsg}</p>}
```

---

## Focus Ring Implementation

All interactive elements should have:
```tsx
className="... focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
```

Current coverage: **70+ components** ✓

---

## Color Contrast Standards

| Level | Normal Text | Large Text | Status |
|-------|------------|-----------|--------|
| AA | 4.5:1 | 3:1 | Standard requirement |
| AAA | 7:1 | 4.5:1 | Enhanced requirement |

**Components failing AA:**
- Disabled buttons (current: 3.2:1, need 4.5:1)
- Placeholder text (current: 3.1:1, need 4.5:1)
- Gray-400 icons (current: 3.1:1, need context)

---

## Keyboard Navigation Summary

| Control | Keyboard | Status |
|---------|----------|--------|
| Buttons | Space, Enter | ✓ Native HTML |
| Links | Tab | ✓ Native HTML |
| Dropdowns | Arrow keys, Escape | ✓ Implemented |
| Tabs | Arrow keys | ✗ **MISSING** |
| Modals | Escape, Tab (trap) | Partial (no trap) |
| Form inputs | All standard | ✓ Native HTML |

---

## Screen Reader Coverage

| Feature | NVDA | JAWS | VoiceOver | Notes |
|---------|------|------|-----------|-------|
| Buttons | Good | Good | Good | Native HTML |
| Forms | Good | Good | Good | Proper labels |
| Tabs | Good | Good | Good | ARIA roles work |
| Dropdowns | Good | Good | Fair | Works but limited context |
| Schedule grid | Fair | Fair | Fair | Cell context unclear |
| Custom divs | Poor | Poor | Poor | Need native elements |

---

## Implementation Examples

### Fix Role-Button Anti-Pattern

```typescript
// WRONG
<div role="button" tabIndex={0} onClick={handler}>
  Action
</div>

// CORRECT
<button type="button" onClick={handler}>
  Action
</button>
```

### Add Arrow Key Navigation (Tabs)

```typescript
const handleKeyDown = (e: KeyboardEvent, currentId: string) => {
  const currentIndex = tabs.findIndex(t => t.id === currentId);
  let nextIndex = currentIndex;

  if (e.key === 'ArrowRight') nextIndex = (currentIndex + 1) % tabs.length;
  if (e.key === 'ArrowLeft') nextIndex = (currentIndex - 1 + tabs.length) % tabs.length;

  if (nextIndex !== currentIndex) {
    e.preventDefault();
    handleTabChange(tabs[nextIndex].id);
  }
};
```

### Add Focus Trap to Modal

```typescript
// hooks/useFocusTrap.ts
export function useFocusTrap(containerRef: RefObject<HTMLDivElement>) {
  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const focusableElements = container.querySelectorAll(
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    );

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key !== 'Tab') return;

      const firstElement = focusableElements[0] as HTMLElement;
      const lastElement = focusableElements[focusableElements.length - 1] as HTMLElement;

      if (e.shiftKey && document.activeElement === firstElement) {
        e.preventDefault();
        lastElement.focus();
      } else if (!e.shiftKey && document.activeElement === lastElement) {
        e.preventDefault();
        firstElement.focus();
      }
    };

    container.addEventListener('keydown', handleKeyDown);
    return () => container.removeEventListener('keydown', handleKeyDown);
  }, [containerRef]);
}
```

---

## Resources

| Resource | URL | Purpose |
|----------|-----|---------|
| Full Audit | `/frontend-accessibility-audit.md` | Complete assessment |
| WCAG 2.1 | https://www.w3.org/WAI/WCAG21/quickref/ | Standard reference |
| WAI-ARIA | https://www.w3.org/WAI/ARIA/apg/ | Design patterns |
| WebAIM Tools | https://webaim.org/resources/ | Testing tools |
| Axe DevTools | https://www.deque.com/axe/devtools/ | Browser extension |

---

## Monitoring

### Quarterly Audit Tasks

- [ ] Full WCAG 2.1 Level AA audit
- [ ] Screen reader testing (NVDA, JAWS, VoiceOver)
- [ ] Manual keyboard navigation test
- [ ] Color contrast audit
- [ ] Performance impact check

### Automated Testing

```bash
npm run test:a11y      # Accessibility tests
npm run audit:axe      # Axe audit
npm run audit:lighthouse  # Lighthouse audit
```

---

## Next Steps

1. **Week 1:** Read full audit document
2. **Week 2:** Create tickets for Priority 1 issues
3. **Week 3:** Complete Priority 1 fixes
4. **Week 4:** Complete Priority 2 fixes
5. **Ongoing:** Quarterly audits + code review checklist

**Target Compliance:** WCAG 2.1 Level AA by Q1 2026

---

**Quick Reference Version:** 1.0
**Last Updated:** 2025-12-30
**See Also:** `frontend-accessibility-audit.md` for full details
