# Section 508 Accessibility Audit — Residency Scheduler

> **Standard:** Section 508 / WCAG 2.1 Level AA
> **Stack:** Next.js 14 App Router + React 18 + TypeScript + TailwindCSS
> **Audit date:** 2026-02-26
> **Files audited:** layout.tsx, Navigation.tsx, Modal.tsx, Toast.tsx, EditableCell.tsx, ErrorBoundary.tsx, WeeklyGridEditor.tsx, CallAssignmentTable.tsx, PeopleTable.tsx, ResilienceHub.tsx, BurnoutDashboard.tsx
> **Files NOT uploaded (audit separately):** MobileNav.tsx, LoginForm.tsx, VoxelScheduleView.tsx, SchedulePage.tsx, CommandPalette.tsx, KeyboardShortcutHelp.tsx, UserMenu.tsx, ImpersonationBanner.tsx, UtilizationChart.tsx, ResilienceMetrics.tsx, N1Analysis.tsx, NaturalSwapsPanel.tsx

---

## Summary

| Severity | Count | Definition |
|----------|-------|------------|
| CRITICAL | 8 | Blocks access entirely — must fix before deployment |
| HIGH | 9 | Significantly degrades AT experience |
| MEDIUM | 7 | Inconvenient but workable |
| LOW | 5 | Best practice |

---

## CRITICAL Findings

### C1 — WeeklyGridEditor: No keyboard grid navigation

- **File:** `WeeklyGridEditor.tsx`
- **WCAG:** 2.1.1 (Keyboard)
- **Problem:** SlotCell has `tabIndex={0}` and Enter/Space handlers (line 147-155), but every cell is in the tab order and there are no arrow key handlers. Users cannot navigate the 7×2 grid efficiently. No roving tabindex pattern.
- **Fix:** Implement WAI-ARIA Grid pattern. Add a `useGridNavigation` hook with roving tabindex. Only the focused cell gets `tabIndex={0}`; all others get `tabIndex={-1}`. Arrow keys move focus. Tab exits the grid entirely.

```tsx
// NEW FILE: hooks/useGridNavigation.ts
import { useState, useCallback, useRef } from 'react';

type GridPosition = { row: number; col: number };

export function useGridNavigation(rows: number, cols: number) {
  const [focusPos, setFocusPos] = useState<GridPosition>({ row: 0, col: 0 });
  const gridRef = useRef<(HTMLElement | null)[][]>(
    Array.from({ length: rows }, () => Array(cols).fill(null))
  );

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      const { row, col } = focusPos;
      let newRow = row,
        newCol = col;
      switch (e.key) {
        case 'ArrowUp':
          newRow = Math.max(0, row - 1);
          break;
        case 'ArrowDown':
          newRow = Math.min(rows - 1, row + 1);
          break;
        case 'ArrowLeft':
          newCol = Math.max(0, col - 1);
          break;
        case 'ArrowRight':
          newCol = Math.min(cols - 1, col + 1);
          break;
        case 'Home':
          newCol = 0;
          break;
        case 'End':
          newCol = cols - 1;
          break;
        case 'Escape':
          // Deselect — handle in parent
          return;
        case 'Delete':
          // Clear slot — handle in parent
          return;
        default:
          return;
      }
      e.preventDefault();
      setFocusPos({ row: newRow, col: newCol });
      gridRef.current[newRow]?.[newCol]?.focus();
    },
    [focusPos, rows, cols]
  );

  const getCellProps = useCallback(
    (row: number, col: number) => ({
      tabIndex: focusPos.row === row && focusPos.col === col ? 0 : -1,
      ref: (el: HTMLElement | null) => {
        gridRef.current[row][col] = el;
      },
      onKeyDown: handleKeyDown,
      'aria-selected': focusPos.row === row && focusPos.col === col,
    }),
    [focusPos, handleKeyDown]
  );

  return { focusPos, setFocusPos, getCellProps };
}
```

Apply to the grid table in `WeeklyGridEditor.tsx`:

```tsx
// WeeklyGridEditor.tsx — add to the <table>
<table className="w-full border-collapse" role="grid" aria-label="Weekly rotation pattern editor">

// Each <tr> needs:
<tr key={time} role="row">

// Each SlotCell wrapper <td> — pass getCellProps(rowIndex, colIndex) spread to the SlotCell div
// Replace SlotCell's own tabIndex/onKeyDown with the hook's values
```

Also add an aria-live announcement region:

```tsx
// WeeklyGridEditor.tsx — add inside the component, before the return
const [announcement, setAnnouncement] = useState('');

// In handleSlotClick, after onChange:
setAnnouncement(`Applied ${template?.name ?? 'clear'} to ${DAY_NAMES[day]} ${time}`);

// In JSX, before closing </div>:
<div aria-live="polite" className="sr-only">{announcement}</div>
```

---

### C2 — PeopleTable + CallAssignmentTable: Rows not keyboard-accessible

- **File:** `PeopleTable.tsx:240`, `CallAssignmentTable.tsx:310-312`
- **WCAG:** 2.1.1 (Keyboard)
- **Problem:** `<tr>` elements use `onClick` for row selection but have no `tabIndex`, no `onKeyDown`, and no `role`. Keyboard users cannot select rows.
- **Fix for PeopleTable.tsx:234:**

```tsx
<tr
  key={person.id}
  className={`transition-colors cursor-pointer ${isSelected ? 'bg-cyan-500/10' : 'hover:bg-slate-700/30'}`}
  onClick={() => handleSelectRow(person.id)}
  onKeyDown={(e) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      handleSelectRow(person.id);
    }
  }}
  tabIndex={0}
  role="row"
  aria-selected={isSelected}
>
```

- **Fix for CallAssignmentTable.tsx:310:**

```tsx
<tr
  key={assignment.id}
  onClick={(e) => handleRowClick(assignment, e)}
  onKeyDown={(e) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      handleSelectRow(assignment.id);
    }
  }}
  tabIndex={0}
  role="row"
  aria-selected={isSelected}
  className={`border-b border-slate-700/50 transition-colors cursor-pointer ${isSelected ? 'bg-violet-500/10' : 'hover:bg-slate-800/50'}`}
>
```

---

### C3 — Missing visible focus indicators on multiple components

- **WCAG:** 2.4.7 (Focus Visible)
- **Problem:** Several interactive elements lack `focus-visible:` ring styles.
- **Locations and fixes:**

**WeeklyGridEditor.tsx SlotCell (line 132-139):** Add focus ring.

```tsx
// SlotCell div — add to className:
focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-1 outline-none
```

**CallAssignmentTable.tsx SortHeader button (line 67):** Add focus ring.

```tsx
// Change line 68 className to:
className="flex items-center gap-1 text-left font-medium hover:text-white transition-colors focus-visible:ring-2 focus-visible:ring-violet-400 focus-visible:outline-none rounded px-1"
```

**PeopleTable.tsx SortHeader button (line 55):** Same fix as above but with `focus-visible:ring-cyan-400`.

**ResilienceHub.tsx refresh button (line 65-73):** Add focus ring.

```tsx
// Line 68 className — add:
focus-visible:ring-2 focus-visible:ring-blue-400 focus-visible:outline-none
```

**ResilienceHub.tsx emergency toggle button (line 76):** Add focus ring.

```tsx
// Line 77 className — add:
focus-visible:ring-2 focus-visible:ring-red-400 focus-visible:outline-none
```

**Navigation.tsx links (line 116, 172):** Add focus-visible styles.

```tsx
// Line 116 and 172 — add to className:
focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:outline-none
```

**EditableCell.tsx display-state div (line 246):** Add focus ring.

```tsx
// Line 246 className — add:
focus-visible:ring-2 focus-visible:ring-violet-500 focus-visible:outline-none
```

---

### C4 — ErrorBoundary: Error not announced to screen readers

- **File:** `ErrorBoundary.tsx:348`
- **WCAG:** 4.1.3 (Status Messages)
- **Problem:** Error container `<div>` at line 348 has no `role="alert"`. Focus is not moved to the error UI when it renders. Screen reader users will not know an error occurred.
- **Fix at line 348:**

```tsx
<div
  className="min-h-screen flex items-center justify-center bg-gray-50 p-4"
  role="alert"
  aria-live="assertive"
>
```

Also add a ref and focus the error heading on mount:

```tsx
// Add ref at class level:
private errorHeadingRef = React.createRef<HTMLHeadingElement>();

// In componentDidUpdate or after state change to hasError:
componentDidUpdate(_: ErrorBoundaryProps, prevState: ErrorBoundaryState) {
  if (this.state.hasError && !prevState.hasError) {
    this.errorHeadingRef.current?.focus();
  }
}

// On the h2 at line 358:
<h2
  ref={this.errorHeadingRef}
  tabIndex={-1}
  className="text-xl font-semibold text-gray-900 mb-2 outline-none"
>
  {config.title}
</h2>
```

---

### C5 — ResilienceHub: Icon-only button has no accessible name

- **File:** `ResilienceHub.tsx:65-73`
- **WCAG:** 4.1.2 (Name, Role, Value)
- **Problem:** The refresh button contains only a `<RefreshCw>` icon. No `aria-label`, no visible text. Screen readers announce it as an empty button.
- **Fix at line 65:**

```tsx
<button
  onClick={() => refetch()}
  disabled={isRefetching}
  aria-label={isRefetching ? 'Refreshing data…' : 'Refresh data'}
  className="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white transition-colors disabled:opacity-50 focus-visible:ring-2 focus-visible:ring-blue-400 focus-visible:outline-none"
>
  <RefreshCw
    className={`w-5 h-5 ${isRefetching ? 'animate-spin' : ''}`}
    aria-hidden="true"
  />
</button>
```

---

### C6 — VoxelScheduleView: 3D WebGL inaccessible (file not uploaded — requirement spec)

- **File:** `VoxelScheduleView.tsx` (not in upload)
- **WCAG:** 1.1.1 (Non-text Content), 2.1.1 (Keyboard)
- **Problem:** WebGL `<canvas>` is opaque to assistive technology. No text alternative, no keyboard controls for camera.
- **Required implementation:**
  1. Add a `<button>` toggle: "Switch to Table View" / "Switch to 3D View".
  2. The table view must contain ALL data shown in the 3D visualization as an accessible `<table>` with proper `<th scope>` headers.
  3. Table view should be the default when `prefers-reduced-motion: reduce` is active.
  4. Add `aria-label="3D schedule visualization. Use the table view button for accessible data."` to the canvas container.
  5. If 3D is interactive: Arrow keys for orbit, `+`/`-` for zoom, `R` to reset, documented in an `aria-describedby` help text.

---

### C7 — BurnoutDashboard: Color-only severity indicator

- **File:** `BurnoutDashboard.tsx:144-149, 162-169`
- **WCAG:** 1.4.1 (Use of Color)
- **Problem:** The Burnout Rt value container background (red/yellow/green) and the TrendingUp/TrendingDown icons are the only indicators of severity. No text label for the severity level.
- **Fix at line 152-173** — add a text severity label:

```tsx
<div className="flex items-center justify-between mb-2">
  <span className="text-sm font-medium text-white">
    Reproduction Number (Rt)
  </span>
  <div className="flex items-center gap-1">
    {burnoutData.rt > 1 ? (
      <TrendingUp className="w-4 h-4 text-red-400" aria-hidden="true" />
    ) : (
      <TrendingDown className="w-4 h-4 text-green-400" aria-hidden="true" />
    )}
    <span
      className={`text-lg font-bold ${
        burnoutData.rt > 1
          ? 'text-red-400'
          : burnoutData.rt > 0.8
          ? 'text-yellow-400'
          : 'text-green-400'
      }`}
    >
      {burnoutData.rt.toFixed(2)}
    </span>
    {/* ADD THIS — visible severity label */}
    <span className={`text-xs font-medium ml-1 ${
      burnoutData.rt > 1 ? 'text-red-300' : burnoutData.rt > 0.8 ? 'text-yellow-300' : 'text-green-300'
    }`}>
      {burnoutData.rt > 1 ? '(Critical)' : burnoutData.rt > 0.8 ? '(Warning)' : '(Stable)'}
    </span>
  </div>
</div>
```

---

### C8 — BurnoutDashboard: Multiple text contrast failures

- **File:** `BurnoutDashboard.tsx:83, 106`
- **WCAG:** 1.4.3 (Contrast Minimum)
- **Problem and fixes:**

| Line | Current classes | Computed ratio | Fix |
|------|---------------|----------------|-----|
| 83 | `text-red-200` on `bg-red-500/10` container | ~1.3:1 | Change to `text-red-100` or restructure: `bg-red-900/40 text-red-200 border-red-500/30` for dark theme |
| 106 | `text-yellow-200` on `bg-yellow-500/5` container | ~1.3:1 | Change to `text-yellow-100` or restructure: `bg-yellow-900/30 text-yellow-200 border-yellow-500/20` |

**Fix at line 83:**

```tsx
// Change:
className="p-3 bg-red-500/10 border border-red-500/20 rounded-lg text-sm text-red-200"
// To:
className="p-3 bg-red-950/60 border border-red-500/30 rounded-lg text-sm text-red-200"
```

**Fix at line 106:**

```tsx
// Change:
className="p-3 bg-yellow-500/5 border border-yellow-500/10 rounded-lg text-sm text-yellow-200"
// To:
className="p-3 bg-yellow-950/40 border border-yellow-500/20 rounded-lg text-sm text-yellow-200"
```

These use darker backgrounds to achieve ≥4.5:1 contrast while preserving the dark theme aesthetic.

---

## HIGH Findings

### H1 — Toast: No Escape key to dismiss

- **File:** `Toast.tsx:70-178`
- **WCAG:** 2.1.1 (Keyboard)
- **Fix:** Add to the Toast component:

```tsx
// Inside Toast component, add useEffect:
useEffect(() => {
  const handleEscape = (e: KeyboardEvent) => {
    if (e.key === 'Escape') {
      handleDismiss();
    }
  };
  document.addEventListener('keydown', handleEscape);
  return () => document.removeEventListener('keydown', handleEscape);
}, [handleDismiss]);
```

---

### H2 — EditableCell: Focus lost after save/cancel

- **File:** `EditableCell.tsx:97, 128`
- **WCAG:** 2.4.3 (Focus Order)
- **Problem:** After `handleCancel` (line 92-95) and `handleSave` (line 97-129) call `setIsEditing(false)`, focus is not returned to the display-state container.
- **Fix — update both handlers:**

```tsx
const handleCancel = useCallback(() => {
  setIsEditing(false);
  setEditValue(value?.toString() ?? '');
  // Return focus to container
  requestAnimationFrame(() => containerRef.current?.focus());
}, [value]);

const handleSave = useCallback(() => {
  // ... existing save logic ...
  setIsEditing(false);
  // Return focus to container
  requestAnimationFrame(() => containerRef.current?.focus());
}, [/* existing deps */]);
```

---

### H3 — Toast: role="alert" with aria-live="polite" is contradictory

- **File:** `Toast.tsx:183-184`
- **WCAG:** 4.1.3 (Status Messages)
- **Problem:** `role="alert"` implicitly maps to `aria-live="assertive"`. Combining it with explicit `aria-live="polite"` creates conflicting semantics. Error toasts should be assertive; info/success should be polite.
- **Fix at line 182-184:**

```tsx
<div
  role={type === 'error' ? 'alert' : 'status'}
  aria-live={type === 'error' ? 'assertive' : 'polite'}
  // ... rest unchanged
>
```

---

### H4 — Toast: Auto-dismiss timer doesn't pause on keyboard focus

- **File:** `Toast.tsx:150-171`
- **WCAG:** 2.2.1 (Timing Adjustable)
- **Problem:** Timer pauses on `mouseEnter`/`mouseLeave` (line 150-171) but not on `focus`/`blur`. Screen reader users tabbing to the toast will have it disappear while reading.
- **Fix at line 182** — add onFocus/onBlur alongside onMouseEnter/onMouseLeave:

```tsx
<div
  role={type === 'error' ? 'alert' : 'status'}
  aria-live={type === 'error' ? 'assertive' : 'polite'}
  onMouseEnter={handleMouseEnter}
  onMouseLeave={handleMouseLeave}
  onFocus={handleMouseEnter}
  onBlur={handleMouseLeave}
  // ... rest unchanged
>
```

---

### H5 — EditableCell: Edit mode transition not announced

- **File:** `EditableCell.tsx:166-229`
- **WCAG:** 4.1.3 (Status Messages)
- **Problem:** When user activates the cell (Enter/Space), it silently transitions from display to edit. Screen readers don't know the cell is now editable.
- **Fix:** Add a live region announcement:

```tsx
// Add state:
const [announcement, setAnnouncement] = useState('');

// In handleStartEdit:
const handleStartEdit = useCallback(() => {
  if (disabled || isSaving) return;
  setIsEditing(true);
  setAnnouncement('Editing mode. Press Enter to save, Escape to cancel.');
}, [disabled, isSaving]);

// After save:
setAnnouncement('Value saved.');

// After cancel:
setAnnouncement('Edit cancelled.');

// In JSX (outside the editing/display conditional, e.g. at end of component):
<div aria-live="polite" className="sr-only">{announcement}</div>
```

---

### H6 — Focus ring visibility inconsistent

- **WCAG:** 2.4.7 (Focus Visible)
- **Problem:** Some components use `focus:ring-2` (which shows on click too) and some have no focus styles. Standardize on `focus-visible:` prefix across the codebase.
- **Fix:** Global Tailwind approach — add to `tailwind.config.ts`:

```ts
// tailwind.config.ts — add to theme.extend or as a plugin
// This ensures focus-visible is the default interaction for custom components.
// Alternatively, create a utility class in globals.css:
```

```css
/* globals.css */
.focus-ring {
  @apply focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2 focus-visible:outline-none;
}
.focus-ring-dark {
  @apply focus-visible:ring-2 focus-visible:ring-blue-400 focus-visible:ring-offset-1 focus-visible:ring-offset-slate-900 focus-visible:outline-none;
}
```

Apply `focus-ring` or `focus-ring-dark` to every interactive element.

---

### H7 — WeeklyGridEditor: SlotDetailsPanel labels not linked to inputs

- **File:** `WeeklyGridEditor.tsx:247-275`
- **WCAG:** 1.3.1 (Info and Relationships), 4.1.2 (Name, Role, Value)
- **Problem:** `<label>` elements at lines 247-248 and 265-266 have text content but no `htmlFor` attribute. `<select>` at line 250 and `<input>` at line 268 have no `id`. Screen readers cannot link label to input.
- **Fix:**

```tsx
// Line 247-260:
<div>
  <label htmlFor="slot-activity-type" className="block text-xs font-medium text-slate-600 mb-1">
    Activity Type Override
  </label>
  <select
    id="slot-activity-type"
    value={slot.activityType || ''}
    onChange={(e) => onUpdateDetails({ activityType: e.target.value || null })}
    className="w-full text-sm border rounded px-2 py-1.5 focus:ring-blue-500 focus:border-blue-500"
  >
    {/* options unchanged */}
  </select>
</div>

// Line 265-275:
<div>
  <label htmlFor="slot-notes" className="block text-xs font-medium text-slate-600 mb-1">
    Notes
  </label>
  <input
    id="slot-notes"
    type="text"
    value={slot.notes || ''}
    onChange={(e) => onUpdateDetails({ notes: e.target.value || null })}
    placeholder="e.g., Building B, Room 201"
    className="w-full text-sm border rounded px-2 py-1.5 focus:ring-blue-500 focus:border-blue-500"
  />
</div>
```

---

### H8 — CallAssignmentTable: Icon-only action buttons lack aria-label

- **File:** `CallAssignmentTable.tsx:351-367`
- **WCAG:** 4.1.2 (Name, Role, Value)
- **Problem:** Edit button (line 352) and Delete button (line 361) use `title` but no `aria-label`. `title` is not reliably announced by screen readers.
- **Fix:**

```tsx
// Line 351-358:
{onEdit && (
  <button
    onClick={() => onEdit(assignment)}
    className="p-1.5 text-slate-400 hover:text-white transition-colors focus-visible:ring-2 focus-visible:ring-violet-400 focus-visible:outline-none rounded"
    aria-label={`Edit assignment for ${assignment.personName} on ${assignment.date}`}
  >
    <Edit2 className="w-4 h-4" aria-hidden="true" />
  </button>
)}

// Line 359-367:
{onDelete && (
  <button
    onClick={() => onDelete(assignment)}
    className="p-1.5 text-slate-400 hover:text-red-400 transition-colors focus-visible:ring-2 focus-visible:ring-red-400 focus-visible:outline-none rounded"
    aria-label={`Delete assignment for ${assignment.personName} on ${assignment.date}`}
  >
    <Trash2 className="w-4 h-4" aria-hidden="true" />
  </button>
)}
```

---

### H9 — Both tables: `<th>` elements missing `scope="col"`

- **File:** `CallAssignmentTable.tsx:262-303`, `PeopleTable.tsx:183-227`
- **WCAG:** 1.3.1 (Info and Relationships)
- **Fix:** Add `scope="col"` to every `<th>` in both tables. Example for CallAssignmentTable:

```tsx
// Line 262:
<th scope="col" className="w-12 py-3 px-4">

// Line 270:
<th scope="col" className="text-left py-3 px-4 text-slate-400">

// ... repeat for all <th> elements in both files
```

---

## MEDIUM Findings

### M1 — Skip link target missing

- **File:** `layout.tsx:45`, `Navigation.tsx:95`
- **WCAG:** 2.4.1 (Bypass Blocks)
- **Problem:** Skip link targets `href="#main-content"` but `<main>` at layout.tsx:45 has no `id`.
- **Fix at layout.tsx:45:**

```tsx
<main id="main-content" className="flex-1 w-full">
```

---

### M2 — Heading hierarchy skips levels

- **Files:** `BurnoutDashboard.tsx:56` (h3 should be h2), `BurnoutDashboard.tsx:72` (h4 should be h3), `CallAssignmentTable.tsx:247` (h3 should be h2)
- **WCAG:** 1.3.1 (Info and Relationships)
- **Fix:** Change `<h3>` to `<h2>` in BurnoutDashboard.tsx:56 and CallAssignmentTable.tsx:247. Change `<h4>` to `<h3>` in BurnoutDashboard.tsx:72, 95, 130.

---

### M3 — Tables missing `<caption>` or `aria-label`

- **Files:** `CallAssignmentTable.tsx:259`, `PeopleTable.tsx:181`
- **WCAG:** 1.3.1 (Info and Relationships)
- **Fix:**

```tsx
// CallAssignmentTable.tsx:259:
<table className="w-full text-sm" aria-label="Call assignments">

// PeopleTable.tsx:181:
<table className="w-full" aria-label="People directory">
```

---

### M4 — CallAssignmentTable: Missing aria-sort on sortable columns

- **File:** `CallAssignmentTable.tsx:270-301`
- **WCAG:** 1.3.1 (Info and Relationships)
- **Problem:** PeopleTable has `aria-sort` on `<th>` elements (line 192+), but CallAssignmentTable does not.
- **Fix:** Add `aria-sort` to each sortable `<th>`:

```tsx
<th
  scope="col"
  className="text-left py-3 px-4 text-slate-400"
  aria-sort={sort.field === 'date' ? (sort.direction === 'asc' ? 'ascending' : 'descending') : 'none'}
>
```

Repeat for `personName` and `callType` columns.

---

### M5 — BurnoutDashboard: Loading skeleton not announced

- **File:** `BurnoutDashboard.tsx:28-32`
- **WCAG:** 4.1.3 (Status Messages)
- **Fix:**

```tsx
if (isLoading) {
  return (
    <div className="h-full w-full bg-slate-800/30 rounded-xl animate-pulse" role="status" aria-busy="true">
      <span className="sr-only">Loading burnout analysis…</span>
    </div>
  );
}
```

---

### M6 — BurnoutDashboard: Error state not announced

- **File:** `BurnoutDashboard.tsx:34-43`
- **WCAG:** 4.1.3 (Status Messages)
- **Fix:**

```tsx
if (error) {
  return (
    <div
      className="h-full p-6 bg-slate-900/50 border border-red-500/20 rounded-xl flex items-center justify-center"
      role="alert"
    >
      <div className="text-center">
        <AlertCircle className="w-6 h-6 text-red-400 mx-auto mb-2" aria-hidden="true" />
        <p className="text-red-300 text-sm">Unable to load data</p>
      </div>
    </div>
  );
}
```

---

### M7 — ResilienceHub: Emergency toggle has no role="switch" or aria-pressed

- **File:** `ResilienceHub.tsx:75-84`
- **WCAG:** 4.1.2 (Name, Role, Value)
- **Fix:**

```tsx
<button
  onClick={() => setEmergencyMode(!emergencyMode)}
  role="switch"
  aria-checked={emergencyMode}
  aria-label="Emergency simulation mode"
  className={`px-4 py-2 rounded-lg text-sm font-medium transition-all focus-visible:ring-2 focus-visible:ring-red-400 focus-visible:outline-none ${
    emergencyMode
      ? 'bg-red-500/20 text-red-200 border border-red-500/30'
      : 'bg-slate-800 hover:bg-slate-700 text-slate-300'
  }`}
>
  {emergencyMode ? 'Deactivate Sims' : 'Simulate Crisis'}
</button>
```

---

## LOW Findings

### L1 — Verify all page routes export unique metadata titles

- **File:** Every `page.tsx` under `app/`
- **Check:** Each must `export const metadata = { title: 'Descriptive Page Name' }` to fill the `'%s | Residency Scheduler'` template in `layout.tsx:14-17`.

### L2 — Add `<header>` and `<footer>` landmarks

- **File:** `layout.tsx:43-50`
- **Fix:** Wrap `<Navigation />` in `<header>`. Add a `<footer>` before closing the flex container.

```tsx
<div className="flex flex-col min-h-screen">
  <header>
    <Navigation />
  </header>
  <main id="main-content" className="flex-1 w-full">
    <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-4 sm:py-6">
      {children}
    </div>
  </main>
  <footer className="text-center text-xs text-gray-500 py-4">
    {/* Version, classification banner, etc. */}
  </footer>
</div>
```

### L3 — Add aria-hidden="true" to decorative icons in BurnoutDashboard

- **File:** `BurnoutDashboard.tsx:73, 96, 131, 158-161`
- **Fix:** Add `aria-hidden="true"` to `<AlertCircle>` at line 73, `<Info>` at line 96, `<Activity>` at line 131, `<TrendingUp>`/`<TrendingDown>` at lines 158-161. These are decorative — the adjacent text conveys the same meaning.

### L4 — Add aria-describedby help text for WeeklyGridEditor keyboard shortcuts

- Add visually hidden help text describing: "Use arrow keys to navigate cells. Enter or Space to apply template. Escape to cancel. Shift+Enter to toggle protection. Delete to clear."

### L5 — Add aria-label to WeeklyGridEditor table

- **File:** `WeeklyGridEditor.tsx:537`
- **Fix:** `<table className="w-full border-collapse" role="grid" aria-label="Weekly rotation pattern editor">`

---

## Contrast Violations Summary

| Current classes | File:Line | Computed ratio | Required | Fix |
|---|---|---|---|---|
| `text-slate-400` on `bg-slate-800/50` | Multiple (tables, dashboards) | ~3.7:1 | 4.5:1 | Use `text-slate-300` |
| `text-slate-500` on dark bg | ResilienceHub.tsx:121 | ~3.2:1 | 4.5:1 | Use `text-slate-400` |
| `text-gray-300` on `bg-gray-50` | WeeklyGridEditor.tsx:165 | ~1.5:1 | 4.5:1 | Use `text-gray-500` |
| `text-red-200` on `bg-red-500/10` | BurnoutDashboard.tsx:83 | ~1.3:1 | 4.5:1 | Use `bg-red-950/60` (darken bg) |
| `text-yellow-200` on `bg-yellow-500/5` | BurnoutDashboard.tsx:106 | ~1.3:1 | 4.5:1 | Use `bg-yellow-950/40` (darken bg) |
| `text-green-500` on `bg-white` | BurnoutDashboard.tsx:119 | ~2.8:1 | 3:1 (non-text) | Use `text-green-600` |

---

## Automated Testing Setup

### 1. jest-axe (unit tests)

```bash
npm install --save-dev jest-axe @types/jest-axe
```

```tsx
// __tests__/accessibility.test.tsx
import { render } from '@testing-library/react';
import { axe, toHaveNoViolations } from 'jest-axe';

expect.extend(toHaveNoViolations);

describe('Component accessibility', () => {
  it('Modal has no axe violations', async () => {
    const { container } = render(
      <Modal isOpen={true} onClose={jest.fn()} title="Test">
        Content
      </Modal>
    );
    expect(await axe(container)).toHaveNoViolations();
  });

  it('Toast has no axe violations', async () => {
    const { container } = render(
      <Toast id="1" type="success" message="Done" onDismiss={jest.fn()} />
    );
    expect(await axe(container)).toHaveNoViolations();
  });

  // Repeat for every component
});
```

### 2. Playwright E2E

```bash
npm install --save-dev @axe-core/playwright
```

```tsx
// e2e/accessibility.spec.ts
import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

const pages = ['/', '/schedule', '/people', '/call-hub', '/admin/resilience-hub'];

for (const path of pages) {
  test(`${path} has no a11y violations`, async ({ page }) => {
    await page.goto(path);
    const results = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag2aa', 'section508'])
      .analyze();
    expect(results.violations).toEqual([]);
  });
}
```

### 3. Storybook addon

```bash
npm install --save-dev @storybook/addon-a11y
```

```ts
// .storybook/main.ts
export default {
  addons: ['@storybook/addon-a11y'],
};
```

### 4. CI gate

Add to your CI pipeline (GitHub Actions example):

```yaml
# .github/workflows/a11y.yml
- name: Run accessibility tests
  run: npx jest --testPathPattern=accessibility
- name: Run Playwright a11y
  run: npx playwright test e2e/accessibility.spec.ts
```

---

## Manual Testing Checklist (VoiceOver + Keyboard-only)

| # | Scenario | Steps | Pass criteria |
|---|----------|-------|---------------|
| T1 | Login flow | Tab to Login link → Enter → Fill form → Submit | All labels read, errors linked to fields |
| T2 | Navigate to schedule | Tab through nav → Enter on Schedule | Page title announced, aria-current read |
| T3 | Read schedule data | VO+arrows through table | Column headers announced with each cell |
| T4 | Edit an assignment | Enter on EditableCell → type → Enter | Mode change announced, focus returns |
| T5 | Grid keyboard nav | Arrow keys in WeeklyGridEditor → Enter to apply | Focus moves, placement announced |
| T6 | Read a notification | Trigger toast → Tab to dismiss → Enter | Toast auto-announced, timer pauses on focus |
| T7 | Open/close modal | Trigger modal → Tab through → Escape | Focus trapped, returns to trigger |
| T8 | Navigate data table | Tab to row → Enter to select → Sort column | Selection announced, sort direction read |
| T9 | Resilience dashboard | Navigate to metrics → Read Rt value | Severity in text, not just color |
| T10 | Error state | Trigger error → Verify announcement | Error role="alert" announced, focus on heading |

---

## Files Changed Checklist

When all fixes are applied, these files will have been modified:

- [ ] `layout.tsx` — Add `id="main-content"` to `<main>`, wrap nav in `<header>`, add `<footer>`
- [ ] `Navigation.tsx` — Add `focus-visible:` styles to all links
- [ ] `Modal.tsx` — No changes needed (already compliant)
- [ ] `Toast.tsx` — Fix role/aria-live per type, add Escape handler, add onFocus/onBlur pause
- [ ] `EditableCell.tsx` — Return focus on save/cancel, add aria-live announcement, add focus-visible ring
- [ ] `ErrorBoundary.tsx` — Add `role="alert"`, focus error heading on render
- [ ] `WeeklyGridEditor.tsx` — Implement grid navigation hook, add role="grid", fix label associations, add aria-live region, add focus-visible rings
- [ ] `CallAssignmentTable.tsx` — Add scope="col", aria-sort, aria-label on table, keyboard on rows, aria-label on action buttons, focus-visible rings
- [ ] `PeopleTable.tsx` — Add scope="col", keyboard on rows, aria-selected, aria-label on table
- [ ] `ResilienceHub.tsx` — Add aria-label to refresh button, role="switch" to toggle, focus-visible rings, add aria-live for emergency status
- [ ] `BurnoutDashboard.tsx` — Fix contrast classes, add severity text labels, add aria-hidden to decorative icons, add role="status"/"alert" to loading/error states, fix heading levels
- [ ] **NEW** `hooks/useGridNavigation.ts` — Grid keyboard navigation hook
- [ ] **NEW** `globals.css` — `.focus-ring` / `.focus-ring-dark` utility classes
