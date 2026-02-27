# Section 508 Accessibility Audit — Military Medical Scheduling UI

Upload all files from this folder, then paste the prompt below.

---

## Context

Military Family Medicine residency scheduling application. Frontend: **Next.js 14 (App Router) + React 18 + TypeScript + TailwindCSS**. This is a DoD system that must comply with **Section 508 of the Rehabilitation Act** (aligned with WCAG 2.1 Level AA).

**Current state:** No dedicated accessibility utility library. ARIA patterns are ad-hoc per component. No automated a11y testing in CI.

**Uploaded files:**
- `components/` — Core interactive components (nav, modals, tables, editors, forms, notifications, errors)
- `schedule/` — Main schedule view page + 3D voxel visualization
- `resilience/` — Resilience dashboard + burnout visualization
- `layout.tsx` — Root application layout

**High-risk areas identified:**
- `WeeklyGridEditor.tsx` — Drag-and-drop scheduling grid (keyboard alternative needed)
- `VoxelScheduleView.tsx` — 3D WebGL visualization (text fallback needed)
- `EditableCell.tsx` — Inline cell editing (focus management critical)
- Data tables (`PeopleTable`, `CallAssignmentTable`) — Complex tabular data with bulk actions

---

## Section 1: Document Structure & Landmarks

Review `layout.tsx`, `Navigation.tsx`, `MobileNav.tsx`, and `SchedulePage.tsx`:

1. **HTML5 landmarks** — Are `<nav>`, `<main>`, `<aside>`, `<header>`, `<footer>` used correctly?
2. **Skip navigation link** — Is there a "Skip to main content" link?
3. **Heading hierarchy** — Is there a logical h1→h2→h3 progression without skipping levels?
4. **Page titles** — Does each route have a unique, descriptive `<title>`?
5. **Language attribute** — Is `lang="en"` set on `<html>`?

Deliver: Findings with specific file:line references and fix recommendations.

---

## Section 2: Keyboard Navigation

Review ALL uploaded components for keyboard accessibility:

1. **Tab order** — Is the tab sequence logical? Are there keyboard traps?
2. **Focus indicators** — Are focus outlines visible? Does TailwindCSS `focus:` or `focus-visible:` appear?
3. **Escape key** — Do modals (`Modal.tsx`) and dropdowns close on Escape?
4. **Arrow keys** — Do tables and grids support arrow key navigation?
5. **Enter/Space** — Do interactive elements respond to both?
6. **Custom keyboard shortcuts** — Any shortcuts defined? Are they documented?
7. **Mobile nav** — Can `MobileNav.tsx` be opened/closed via keyboard?

Deliver: Component-by-component keyboard audit matrix.

---

## Section 3: ARIA Patterns

Review each component against WAI-ARIA Authoring Practices 1.2:

1. **Modal.tsx** — Does it implement the Dialog pattern? (`role="dialog"`, `aria-modal="true"`, `aria-labelledby`, focus trap, return focus on close)
2. **Toast.tsx** — Does it use `role="alert"` or `role="status"` with `aria-live`?
3. **PeopleTable.tsx / CallAssignmentTable.tsx** — Do they use proper `<table>` semantics with `<th scope>`? Or are they CSS grid faking a table?
4. **WeeklyGridEditor.tsx** — What ARIA pattern applies? Grid? Treegrid? Listbox?
5. **EditableCell.tsx** — How is the edit state communicated? `aria-expanded`? Role changes?
6. **ErrorBoundary.tsx / ErrorAlert** — Are errors announced to screen readers?
7. **LoginForm.tsx** — Are `<label>` elements properly associated? Are errors linked via `aria-describedby`?

Deliver: Per-component ARIA compliance checklist (PASS/FAIL/MISSING for each required attribute).

---

## Section 4: Drag-and-Drop Accessibility

Deep dive on `WeeklyGridEditor.tsx`:

1. **Current implementation** — How is drag-and-drop implemented? (HTML5 DnD, react-dnd, custom?)
2. **Keyboard alternative** — Is there ANY keyboard-only way to move items?
3. **Screen reader announcements** — Are drag start/move/drop announced?
4. **Recommended pattern** — What's the WAI-ARIA best practice for grid-based drag-and-drop?
5. **Implementation plan** — Concrete code pattern for adding keyboard support (select with Space, move with arrows, drop with Enter, cancel with Escape)

Deliver: Recommended implementation approach with code snippets.

---

## Section 5: Data Visualization Accessibility

Review `VoxelScheduleView.tsx` and `BurnoutDashboard.tsx`:

1. **VoxelScheduleView (3D/WebGL):**
   - Is there a text-based alternative view?
   - Can screen readers access the schedule data?
   - Is there a "switch to table view" option?
   - What's the recommended pattern for 3D visualization accessibility?

2. **BurnoutDashboard:**
   - Are charts/gauges described with `aria-label` or `<desc>` elements?
   - Is the underlying data available in tabular form?
   - Are color-only indicators supplemented with text/pattern?

3. **General data viz:**
   - Are tooltips keyboard-accessible?
   - Do charts have meaningful alt text?

Deliver: Specific recommendations for each visualization with WCAG 2.1 AA compliance path.

---

## Section 6: Color & Contrast

Analyze TailwindCSS classes across ALL uploaded files:

1. **Text contrast** — Identify any `text-gray-*` on `bg-*` combinations that fail WCAG AA (4.5:1 for normal text, 3:1 for large text)
2. **Interactive element contrast** — Do buttons, links, form controls meet 3:1 against adjacent colors?
3. **Focus indicator contrast** — Are focus rings visible on all backgrounds?
4. **Color-only information** — Are there any cases where color is the SOLE differentiator (red=error, green=success) without text/icon backup?
5. **Dark mode** — If present, does it maintain contrast ratios?

Deliver: Table of contrast violations with Tailwind class, computed colors, actual ratio, and fix.

---

## Section 7: Forms & Error Handling

Review `LoginForm.tsx`, `EditableCell.tsx`, and any form patterns in other components:

1. **Label association** — Every `<input>` has a visible `<label>` or `aria-label`?
2. **Required fields** — Indicated both visually AND with `aria-required="true"`?
3. **Error messages** — Connected to inputs via `aria-describedby`? Announced with `aria-live`?
4. **Validation timing** — On blur? On submit? Real-time? (Screen readers need predictable timing)
5. **Success feedback** — Are successful actions announced?
6. **Autocomplete** — Are `autocomplete` attributes set on login fields?

---

## Section 8: Remediation Priority & Testing Plan

Based on Sections 1-7:

1. **CRITICAL findings** (blocks access entirely — must fix before deployment):
   - List each with component, issue, WCAG criterion, fix
2. **HIGH findings** (significantly degrades experience):
   - List each with component, issue, WCAG criterion, fix
3. **MEDIUM findings** (inconvenient but workable):
   - List each
4. **LOW findings** (best practice, not strictly required):
   - List each

5. **Manual testing plan** — 10 specific test scenarios for VoiceOver (macOS) and keyboard-only:
   - Login flow
   - Navigate to schedule
   - Read schedule data
   - Edit an assignment
   - Use drag-and-drop alternative
   - Read a notification
   - Open/close a modal
   - Navigate data table
   - Read resilience dashboard
   - Handle an error state

6. **Automated testing recommendations:**
   - axe-core integration (jest-axe for unit tests)
   - Playwright a11y assertions for E2E
   - Storybook a11y addon for component development

Deliver: Prioritized remediation backlog ready to be converted to tickets.
