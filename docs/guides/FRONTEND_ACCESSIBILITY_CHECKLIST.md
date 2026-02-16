# Frontend Accessibility Improvements Checklist

**Created:** 2025-12-31
**Source:** SESSION_2_FRONTEND Accessibility Audit
**Target:** WCAG 2.1 Level AA Compliance
**Status:** Actionable Priority List

---

## Executive Summary

**Current Status:** ~75% WCAG AA compliant
**Target:** 100% WCAG 2.1 Level AA by Q1 2026
**Critical Issues:** 3 blocking
**High Priority:** 7 best practices
**Medium Priority:** 5 enhancements

### Key Findings
- 67 aria-label implementations (good foundation)
- 70+ focus:ring implementations (keyboard nav visible)
- 322+ semantic HTML elements (strong)
- **3 role="button" divs** (must fix - breaks semantic HTML)
- **Missing tab keyboard navigation** (WAI-ARIA violation)
- **No focus traps in modals** (UX issue)
- **Color contrast gaps** (4 edge cases)

---

## CRITICAL ISSUES - Fix These First (Week 1)

### Critical Issue #1: Replace role="button" Divs with Native Buttons

**Impact:** HIGH - Blocks WCAG Level A compliance
**Effort:** 1-2 hours
**Files Affected:** 2

#### CellActions.tsx (BLOCKING)

```typescript
// CURRENT (WRONG) ✗
const CellActions = ({ isInteractive, onClick, ...props }) => {
  return (
    <div
      role={isInteractive ? 'button' : undefined}
      tabIndex={isInteractive ? 0 : undefined}
      onClick={onClick}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          onClick?.(e);
        }
      }}
      {...props}
    >
      Actions
    </div>
  );
};

// CORRECT ✓
const CellActions = ({ isInteractive, onClick, ...props }) => {
  if (!isInteractive) {
    return <span {...props}>Actions</span>;
  }

  return (
    <button
      onClick={onClick}
      type="button"
      {...props}
    >
      Actions
    </button>
  );
};
```

#### TimeSlot.tsx (BLOCKING)

```typescript
// CURRENT (WRONG) ✗
role={onClick ? 'button' : undefined}
tabIndex={onClick && !isDisabled ? 0 : undefined}

// CORRECT ✓
{onClick && !isDisabled ? (
  <button type="button" onClick={onClick}>
    Time slot content
  </button>
) : (
  <div>Time slot content</div>
)}
```

**Verification:**
```bash
# Check for remaining role="button" divs
grep -r 'role="button"' frontend/src/components/
grep -r 'role=.*button' frontend/src/components/
```

---

### Critical Issue #2: Add Keyboard Navigation to Tabs Component

**Impact:** HIGH - WAI-ARIA Authoring Practices violation
**Effort:** 30-45 minutes
**File:** `src/components/ui/Tabs.tsx`

**Current Issue:**
- Tabs component implements role="tab" but no arrow key navigation
- Standard: ArrowLeft/Right switches tabs
- Status: Click-based only (incomplete)

**Fix Implementation:**

```typescript
// src/components/ui/Tabs.tsx

interface TabsProps {
  tabs: Tab[];
  activeTabId: string;
  onTabChange: (tabId: string) => void;
}

export function Tabs({ tabs, activeTabId, onTabChange }: TabsProps) {
  const tabsRef = useRef<HTMLDivElement>(null);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLButtonElement>, currentIndex: number) => {
    let nextIndex = currentIndex;

    switch (e.key) {
      case 'ArrowLeft':
      case 'ArrowUp':
        nextIndex = (currentIndex - 1 + tabs.length) % tabs.length;
        e.preventDefault();
        break;
      case 'ArrowRight':
      case 'ArrowDown':
        nextIndex = (currentIndex + 1) % tabs.length;
        e.preventDefault();
        break;
      case 'Home':
        nextIndex = 0;
        e.preventDefault();
        break;
      case 'End':
        nextIndex = tabs.length - 1;
        e.preventDefault();
        break;
      default:
        return;
    }

    // Switch to new tab
    onTabChange(tabs[nextIndex].id);

    // Focus new tab button
    setTimeout(() => {
      const tabButtons = tabsRef.current?.querySelectorAll('[role="tab"]');
      (tabButtons?.[nextIndex] as HTMLElement)?.focus();
    }, 0);
  };

  return (
    <div
      role="tablist"
      aria-orientation="horizontal"
      ref={tabsRef}
      className="border-b border-gray-200"
    >
      {tabs.map((tab, index) => (
        <button
          key={tab.id}
          role="tab"
          aria-selected={tab.id === activeTabId}
          aria-controls={`tabpanel-${tab.id}`}
          tabIndex={tab.id === activeTabId ? 0 : -1}
          onClick={() => onTabChange(tab.id)}
          onKeyDown={(e) => handleKeyDown(e, index)}
          className={`
            px-4 py-2 font-medium border-b-2 transition-colors
            ${tab.id === activeTabId
              ? 'border-blue-500 text-blue-600'
              : 'border-transparent text-gray-700 hover:text-gray-900'}
          `}
        >
          {tab.label}
        </button>
      ))}
    </div>
  );
}
```

**Test:**
```typescript
describe('Tabs Keyboard Navigation', () => {
  it('should navigate to next tab with ArrowRight', async () => {
    const { getByRole } = render(<Tabs {...tabProps} />);
    const tab1 = getByRole('tab', { name: 'Tab 1' });
    const tab2 = getByRole('tab', { name: 'Tab 2' });

    tab1.focus();
    fireEvent.keyDown(tab1, { key: 'ArrowRight' });

    await waitFor(() => {
      expect(tab2).toHaveFocus();
    });
  });
});
```

---

### Critical Issue #3: Fix Color Contrast Issues (4 cases)

**Impact:** MEDIUM-HIGH - Fails WCAG AA for text contrast
**Effort:** 30 minutes
**Files:** Multiple form/button components

#### Issue A: Disabled Button State

**Current (FAIL AA):**
```css
/* bg-gray-opacity-50 / white = 3.2:1 (FAILS) */
.btn:disabled {
  background-color: rgba(107, 114, 128, 0.5);
  color: white;
}
```

**Fixed (PASS AAA):**
```typescript
// src/components/Button.tsx
const disabledStyles = 'bg-gray-400 text-gray-600 cursor-not-allowed opacity-75';

export function Button({ isDisabled, ...props }: ButtonProps) {
  return (
    <button
      disabled={isDisabled}
      className={isDisabled ? disabledStyles : activeStyles}
      {...props}
    />
  );
}
```

#### Issue B: Placeholder Text

**Current (FAIL AA):**
```html
<!-- gray-400 / white = 3.1:1 (FAILS) -->
<input placeholder="Search..." className="placeholder-gray-400" />
```

**Fixed (PASS AA):**
```typescript
// src/components/forms/Input.tsx
<input
  placeholder={placeholder}
  className="placeholder-gray-500"  // Changed from gray-400
  aria-label={label}
/>
```

#### Issue C: Schedule Cell "Off" Rotation

**Current (FAIL AA):**
```typescript
const rotationColors = {
  off: 'bg-white text-gray-400',  // 3:1 (FAILS)
};
```

**Fixed (PASS AA):**
```typescript
const rotationColors = {
  off: 'bg-gray-50 text-gray-700',  // 6.5:1 (PASSES)
};
```

#### Issue D: Gray-400 Icons

**Current (FAIL AA):**
```html
<!-- gray-400 / white = 3.1:1 (FAILS for meaning) -->
<svg className="text-gray-400">
  <use href="#icon-warning" />
</svg>
```

**Fixed (PASS AA):**
```typescript
// Use aria-label + darker color for meaningful icons
<svg
  className="text-gray-600"  // Darker for contrast
  aria-label="Warning: This is required"
  role="img"
>
  <use href="#icon-warning" />
</svg>
```

---

## HIGH PRIORITY - Week 2 (Best Practices)

### High Priority #1: Add Focus Traps in Modals

**Impact:** MEDIUM - Best practice, UX improvement
**Effort:** 1-2 hours
**Files:** ConfirmDialog.tsx, EditAssignmentModal.tsx, and all modals

**Pattern to Implement:**

```typescript
// hooks/useFocusTrap.ts
export function useFocusTrap(containerRef: RefObject<HTMLDivElement>, isActive = true) {
  useEffect(() => {
    if (!isActive) return;

    const container = containerRef.current;
    if (!container) return;

    // Get all focusable elements
    const focusableElements = container.querySelectorAll(
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    );

    const firstElement = focusableElements[0] as HTMLElement;
    const lastElement = focusableElements[focusableElements.length - 1] as HTMLElement;

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key !== 'Tab') return;

      // Trap focus: Shift+Tab on first element → go to last
      if (e.shiftKey && document.activeElement === firstElement) {
        e.preventDefault();
        lastElement.focus();
      }
      // Trap focus: Tab on last element → go to first
      else if (!e.shiftKey && document.activeElement === lastElement) {
        e.preventDefault();
        firstElement.focus();
      }
    };

    container.addEventListener('keydown', handleKeyDown);
    return () => container.removeEventListener('keydown', handleKeyDown);
  }, [containerRef, isActive]);
}

// Usage in Modal
export function Modal({ isOpen, children, ...props }: ModalProps) {
  const modalRef = useRef<HTMLDivElement>(null);
  useFocusTrap(modalRef, isOpen);

  return (
    <div
      ref={modalRef}
      role="alertdialog"
      aria-modal="true"
      className="fixed inset-0 bg-black/50 flex items-center justify-center"
    >
      {children}
    </div>
  );
}
```

**Verification:**
```bash
# Test: Tab in modal should not escape to background
# Tab from last element → should go to first element
```

---

### High Priority #2: Add Focus Restoration

**Impact:** MEDIUM - UX improvement
**Effort:** 30 minutes
**Pattern:**

```typescript
// When modal closes, restore focus to trigger element

export function EditAssignmentModal({
  isOpen,
  onClose,
  triggerRef,  // Ref to button that opened modal
}: EditAssignmentModalProps) {
  const modalRef = useRef<HTMLDivElement>(null);

  const handleClose = useCallback(() => {
    // Restore focus to trigger element
    setTimeout(() => {
      triggerRef?.current?.focus();
    }, 0);

    // Then close modal
    onClose();
  }, [onClose, triggerRef]);

  return (
    <Modal
      isOpen={isOpen}
      onClose={handleClose}
      ref={modalRef}
    >
      {/* Modal content */}
    </Modal>
  );
}

// Usage
const triggerRef = useRef<HTMLButtonElement>(null);

return (
  <>
    <button ref={triggerRef} onClick={() => setShowModal(true)}>
      Edit
    </button>
    <EditAssignmentModal
      isOpen={showModal}
      onClose={() => setShowModal(false)}
      triggerRef={triggerRef}
    />
  </>
);
```

---

### High Priority #3-7: Additional Improvements

#### #3: Add aria-expanded to All Disclosure Toggles

```typescript
// Dropdowns, menus, collapsible sections
<button
  aria-expanded={isOpen}
  aria-controls="dropdown-menu"
  onClick={toggleDropdown}
>
  Menu
</button>
<div id="dropdown-menu" hidden={!isOpen}>
  {/* Menu items */}
</div>
```

#### #4: MultiSelect Keyboard Navigation

Similar to Tabs - implement ArrowUp/Down/Enter/Escape in dropdown lists.

#### #5: Implement Live Region for Dynamic Updates

```typescript
<div aria-live="polite" aria-atomic="true" role="status">
  {scheduleUpdateMessage}
</div>
```

#### #6: Add Screen Reader-Only Content

```typescript
// Expand abbreviations for screen readers
<span aria-label="Postgraduate Year 1">PGY-1</span>

// Add status announcements
<span className="sr-only">
  Loaded {assignments.length} assignments
</span>
```

#### #7: Improve Tooltip Component

```typescript
// Link tooltip to trigger element
<div
  id="tooltip-help"
  role="tooltip"
  aria-describedby="help-button"
>
  Help text here
</div>

<button id="help-button" aria-describedby="tooltip-help">
  ?
</button>
```

---

## MEDIUM PRIORITY - Month 2 (Enhancements)

### Enhancement #1: Dark Mode Contrast Testing

```typescript
// Verify all colors have sufficient contrast in both modes
// Especially: gray-400, gray-500 text

// Test patterns:
// - Light mode: bg-white text-gray-900
// - Dark mode: bg-gray-900 text-white
```

### Enhancement #2: 200% Zoom Testing

Ensure layout doesn't break at 200% zoom (WCAG AA requirement).

### Enhancement #3: Reduced Motion Support

```typescript
// Respect prefers-reduced-motion
@media (prefers-reduced-motion: reduce) {
  * {
    animation: none !important;
    transition: none !important;
  }
}

// React implementation
const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
<motion.div animate={prefersReducedMotion ? {} : animationVariants}>
```

### Enhancement #4: Add Visual Indicators

```typescript
// Beyond color alone, add icons/symbols
<div className="flex items-center gap-2">
  <ErrorIcon aria-hidden="true" />  {/* Visual backup */}
  <span>This field is required</span>
</div>
```

### Enhancement #5: Mobile VoiceOver Testing

Test with iOS Safari screen reader - different behavior than NVDA/JAWS.

---

## ARIA Labels & Attributes Quick Reference

### Form-Related

```typescript
// Input with error
<input
  id="email"
  aria-label="Email address"
  aria-invalid={hasError}
  aria-describedby={hasError ? 'email-error' : undefined}
/>
<span id="email-error" role="alert">{errorMessage}</span>

// Select
<select
  id="country"
  aria-label="Country"
  aria-describedby="country-help"
>
  {/* options */}
</select>
<p id="country-help" className="text-sm text-gray-600">Help text</p>
```

### Interactive Components

```typescript
// Button with icon
<button aria-label="Close menu">
  <CloseIcon aria-hidden="true" />
</button>

// Dropdown
<button aria-expanded={isOpen} aria-controls="menu">
  Menu
</button>
<div id="menu" role="menu" hidden={!isOpen}>
  {/* items */}
</div>

// Tabs
<div role="tablist">
  <button
    role="tab"
    aria-selected={active === 'tab1'}
    aria-controls="tabpanel1"
  >
    Tab 1
  </button>
</div>
<div id="tabpanel1" role="tabpanel" aria-labelledby="tab1">
  Content
</div>
```

### Status & Loading

```typescript
// Loading state
<div aria-busy={isLoading} aria-live="polite">
  {isLoading ? 'Loading...' : content}
</div>

// Success message
<div role="alert" aria-live="assertive">
  ✓ Changes saved
</div>

// Progress
<div role="progressbar" aria-valuenow={50} aria-valuemin={0} aria-valuemax={100} />
```

---

## Accessibility Testing Checklist

### Manual Testing (Before each merge)

```checklist
[ ] Keyboard Navigation
  [ ] Tab through all interactive elements in order
  [ ] Shift+Tab backwards works
  [ ] No focus traps (except in modals)
  [ ] Focus indicator always visible

[ ] Screen Reader (NVDA on Windows, JAWS, or VoiceOver on Mac)
  [ ] Page title announced
  [ ] Headings navigate with H key
  [ ] Form labels associated (announced with field)
  [ ] Images have alt text or aria-hidden
  [ ] Links have descriptive text

[ ] Color Contrast
  [ ] All text meets WCAG AA (4.5:1)
  [ ] Large text meets WCAG AA (3:1)
  [ ] Color not sole differentiator (icons present)

[ ] Mobile Accessibility
  [ ] Tap targets ≥48px × 48px
  [ ] VoiceOver navigation works
  [ ] Pinch zoom not disabled

[ ] Responsive Design
  [ ] Layout works at 200% zoom
  [ ] No horizontal scrolling at 200%
  [ ] Text is readable (not tiny)
```

### Automated Testing

```bash
# Axe DevTools
npm run test:axe

# Lighthouse
npm run test:lighthouse -- http://localhost:3000

# Pa11y CLI
npm run test:pa11y

# ESLint a11y rules
npm run lint -- --plugin a11y

# Playwright accessibility assertions
expect(page).toPass(checkA11y());
```

### Jest Testing for Accessibility

```typescript
it('should have accessible form labels', () => {
  render(<LoginForm />);

  const emailInput = screen.getByLabelText(/email/i);
  const passwordInput = screen.getByLabelText(/password/i);

  expect(emailInput).toHaveAttribute('id');
  expect(passwordInput).toHaveAttribute('id');
});

it('should announce errors to screen readers', () => {
  render(<Form initialErrors={{ email: 'Invalid email' }} />);

  const error = screen.getByRole('alert');
  expect(error).toHaveTextContent('Invalid email');
});

it('should trap focus in modal', async () => {
  const { getByRole } = render(<Modal isOpen />);
  const modal = getByRole('alertdialog');
  const buttons = modal.querySelectorAll('button');

  // Focus first button
  buttons[0].focus();

  // Shift+Tab should go to last button
  fireEvent.keyDown(buttons[0], { key: 'Tab', shiftKey: true });
  expect(buttons[buttons.length - 1]).toHaveFocus();
});
```

---

## Implementation Timeline

### Week 1 (Critical - Do First)
- Replace role="button" divs (2 files)
- Add Tab keyboard navigation
- Fix color contrast (4 cases)
- **Estimated:** 4-5 hours

### Week 2-3 (High Priority)
- Add focus traps to modals
- Add focus restoration
- Add aria-expanded to toggles
- Keyboard nav for MultiSelect
- **Estimated:** 6-8 hours

### Month 2 (Medium Priority)
- Dark mode contrast testing
- 200% zoom testing
- Reduced motion support
- Mobile VoiceOver testing
- **Estimated:** 6-8 hours

### Ongoing (Low Priority)
- Visual regression testing
- Enhanced screen reader content
- Popover API migration
- **Estimated:** 2-3 hours per quarter

---

## Reference Resources

### Documentation
- [WAI-ARIA Authoring Practices](https://www.w3.org/WAI/ARIA/apg/)
- [WCAG 2.1 Guidelines](https://www.w3.org/WAI/WCAG21/quickref/)
- [WebAIM Contrast Checker](https://webaim.org/resources/contrastchecker/)

### Tools
- [Axe DevTools Chrome Extension](https://chrome.google.com/webstore/detail/axe-devtools/lhdoppojpmngadmnkpklempisson)
- [WAVE Browser Extension](https://wave.webaim.org/extension/)
- [Lighthouse](https://developers.google.com/web/tools/lighthouse)
- [Playwright Accessibility Testing](https://playwright.dev/docs/accessibility-testing)

### Testing Libraries
```json
{
  "devDependencies": {
    "axe-core": "^4.7.0",
    "@axe-core/react": "^0.8.0",
    "jest-axe": "^8.0.0",
    "@testing-library/jest-dom": "^6.1.0",
    "pa11y": "^7.0.0"
  }
}
```

---

## Success Criteria

- [ ] 0 Axe violations (critical)
- [ ] All interactive elements keyboard accessible
- [ ] All text meets WCAG AA contrast ratio
- [ ] All form inputs have associated labels
- [ ] Screen reader announces all content correctly
- [ ] Focus indicators visible throughout
- [ ] Modal focus traps working
- [ ] 200% zoom layout intact

---

**Document Version:** 1.0
**Last Updated:** 2025-12-31
**Target Compliance:** WCAG 2.1 Level AA by 2026-03-31
