# GUI Considerations for Residency Scheduler

> **Last Updated:** 2026-01-15 | **Purpose:** Frontend library decisions and UI patterns for Claude Code CLI

---

## Current Frontend Stack

| Category | Library | Version | Status |
|----------|---------|---------|--------|
| Framework | Next.js (App Router) | 14.2.35 | Installed |
| UI | React | 18.2.0 | Installed |
| Styling | TailwindCSS | 3.4.1 | Installed |
| Icons | lucide-react | 0.561.0 | Installed |
| 3D | three, @react-three/fiber, @react-three/drei | 0.164.1 / 8.18.0 / 9.122.0 | Installed |
| Animation | framer-motion | 12.23.26 | Installed |
| Animation (3D) | @react-spring/three | 9.7.3 | Installed |
| Drag & Drop | @dnd-kit/* | 6.3.1+ | Installed |
| Charts | recharts, plotly.js, react-plotly.js | 3.6.0 / 3.3.1 | Installed |
| Data Fetching | @tanstack/react-query | 5.90.14 | Installed |
| Dates | date-fns | 4.1.0 | Installed |
| Excel | xlsx | 0.20.2 | Installed |
| Validation | zod | 4.3.2 | Installed |

---

## Icon Libraries

### Primary: Lucide React (Installed)

Lucide is the primary icon library. It includes:
- 1,500+ icons with consistent 24x24 grid
- Healthcare icons: `Hospital`, `Stethoscope`, `HeartPulse`, `Pill`, `Syringe`, `Activity`
- Calendar/scheduling: `Calendar`, `CalendarDays`, `Clock`, `Timer`, `AlarmClock`
- User/role icons: `User`, `Users`, `UserCog`, `Shield`, `ShieldCheck`

```tsx
import { Calendar, Users, Shield, Activity } from 'lucide-react';
```

### Complementary Options (Not Installed)

| Library | Use Case | Install |
|---------|----------|---------|
| [Phosphor Icons](https://phosphoricons.com) | 6 weight variants for visual hierarchy | `npm i @phosphor-icons/react` |
| [Heroicons](https://heroicons.com) | Tailwind-native, outline/solid pairs | `npm i @heroicons/react` |
| [Iconify](https://iconify.design) | Meta-library (275k+ icons, on-demand) | `npm i @iconify/react` |
| [Health Icons](https://healthicons.org) | Open-source medical-specific | Manual SVG import |

### Three.js / 3D Icons

Already installed: `three`, `@react-three/fiber`, `@react-three/drei`

For 3D extruded icons:
```bash
npm install react-3d-icons  # Uses simpleicons.org catalogue
```

Features:
- Extrude any SVG into 3D
- Customizable depth, rotation, spin animation
- Requires peer deps already installed (three, @react-three/fiber)

### Military Medical Symbology

No React library exists for MIL-STD-2525 (NATO Joint Military Symbology). Options:
1. Custom SVG components based on [MIL-STD-2525D spec](https://www.jcs.mil/Portals/36/Documents/Doctrine/Other_Pubs/ms_2525d.pdf)
2. Use generic medical + military icons from Lucide/Phosphor
3. Create custom icon set for: medical unit, ambulance, hospital ship, CASEVAC, etc.

---

## GUI Gaps & Recommendations

### 1. Data Tables (HIGH PRIORITY)

**Gap:** No table library for resident rosters, schedule grids, compliance reports.

**Recommendation:** TanStack Table (headless, pairs with Tailwind)

```bash
npm install @tanstack/react-table @tanstack/react-virtual
```

Why:
- Headless = full styling control with Tailwind
- Virtualization for large datasets (17 residents x 13 blocks x years)
- Sorting, filtering, grouping built-in
- Same ecosystem as @tanstack/react-query (already installed)

### 2. Calendar/Scheduler Component (HIGH PRIORITY)

**Gap:** No dedicated calendar UI for schedule visualization.

| Option | Cost | Best For |
|--------|------|----------|
| [react-big-calendar](https://github.com/jquense/react-big-calendar) | Free | Monthly/weekly views, Google Calendar-style |
| [FullCalendar](https://fullcalendar.io/docs/react) | Free + Premium | Resource views, timeline, more features |
| [DHTMLX Scheduler](https://dhtmlx.com/docs/products/dhtmlxScheduler/) | Commercial | Medical-specific, multi-resource views |
| [Planby](https://planby.app/) | Commercial | TV guide-style timeline |

**Recommendation:** Start with `react-big-calendar`, upgrade to FullCalendar Premium if resource views needed.

```bash
npm install react-big-calendar
```

### 3. Form Handling (MEDIUM PRIORITY)

**Gap:** No form library for swap requests, user preferences, admin forms.

**Recommendation:** react-hook-form + zod resolver (zod already installed)

```bash
npm install react-hook-form @hookform/resolvers
```

Benefits:
- Minimal re-renders (performance)
- Native zod integration for validation
- Uncontrolled inputs = less state management

### 4. Toast/Notifications (MEDIUM PRIORITY)

**Gap:** No notification system for:
- Swap confirmations
- ACGME compliance alerts
- Import success/failure
- Async operation feedback

**Options:**

| Library | Style | Size |
|---------|-------|------|
| [sonner](https://sonner.emilkowal.ski/) | Modern, stacked | 5KB |
| [react-hot-toast](https://react-hot-toast.com/) | Minimal | 5KB |
| [react-toastify](https://fkhadra.github.io/react-toastify/) | Feature-rich | 12KB |

**Recommendation:** `sonner` - cleanest API, best animations

```bash
npm install sonner
```

### 5. Date/Time Pickers (MEDIUM PRIORITY)

**Gap:** date-fns handles logic but no picker UI.

**Options:**

| Library | Style | Notes |
|---------|-------|-------|
| [react-day-picker](https://react-day-picker.js.org/) | Minimal | Powers shadcn calendar |
| [react-datepicker](https://reactdatepicker.com/) | Full-featured | Time picker included |

**Recommendation:** `react-day-picker` - lightweight, pairs with Tailwind

```bash
npm install react-day-picker
```

### 6. Command Palette (LOW PRIORITY)

**Gap:** No quick navigation for complex UIs.

**Recommendation:** cmdk - Vercel-style command menu

```bash
npm install cmdk
```

Use cases:
- Jump to resident: `⌘K` → "John Smith"
- Jump to block: `⌘K` → "Block 10"
- Quick actions: `⌘K` → "Generate schedule"

### 7. Accessible Primitives (LOW PRIORITY)

**Gap:** No headless UI primitives for modals, dropdowns, popovers.

**Recommendation:** Radix UI (or shadcn/ui which wraps Radix)

```bash
npm install @radix-ui/react-dialog @radix-ui/react-dropdown-menu @radix-ui/react-popover @radix-ui/react-tooltip
```

Benefits:
- WAI-ARIA compliant out of box
- Keyboard navigation
- Focus management
- Works with Tailwind

---

## Priority Installation Order

### Phase 1: Core Functionality
```bash
# Tables for schedule grids
npm install @tanstack/react-table @tanstack/react-virtual

# Forms for user input
npm install react-hook-form @hookform/resolvers

# Notifications for feedback
npm install sonner
```

### Phase 2: Enhanced UX
```bash
# Calendar visualization
npm install react-big-calendar

# Date pickers
npm install react-day-picker

# Accessible primitives
npm install @radix-ui/react-dialog @radix-ui/react-dropdown-menu
```

### Phase 3: Power Features
```bash
# Command palette
npm install cmdk

# Additional icon weights
npm install @phosphor-icons/react

# 3D icons (if using)
npm install react-3d-icons
```

---

## Component Patterns

### Schedule Grid (TanStack Table + Tailwind)

```tsx
// Headless table with Tailwind styling
import { useReactTable, getCoreRowModel, flexRender } from '@tanstack/react-table';

const columns = [
  { accessorKey: 'residentName', header: 'Resident' },
  { accessorKey: 'block1', header: 'Block 1' },
  { accessorKey: 'block2', header: 'Block 2' },
  // ... blocks 3-13
];

// Virtual scrolling for large datasets
import { useVirtualizer } from '@tanstack/react-virtual';
```

### Toast Notifications (Sonner)

```tsx
import { toast, Toaster } from 'sonner';

// In layout
<Toaster position="top-right" richColors />

// Usage
toast.success('Schedule saved');
toast.error('ACGME violation detected');
toast.warning('Approaching 80-hour limit');
toast.promise(saveSchedule(), {
  loading: 'Saving...',
  success: 'Schedule saved',
  error: 'Failed to save'
});
```

### Form with Zod Validation

```tsx
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';

const swapSchema = z.object({
  fromResidentId: z.string().uuid(),
  toResidentId: z.string().uuid(),
  blockNumber: z.number().min(1).max(13),
  reason: z.string().min(10, 'Please provide a reason')
});

const { register, handleSubmit, formState: { errors } } = useForm({
  resolver: zodResolver(swapSchema)
});
```

---

## Design System Notes

### Color Usage (Medical Context)

| Color | Usage | Tailwind |
|-------|-------|----------|
| Green | Compliant, available, approved | `text-green-600` |
| Yellow | Warning, approaching limit | `text-yellow-600` |
| Red | Violation, conflict, denied | `text-red-600` |
| Blue | Information, neutral actions | `text-blue-600` |
| Gray | Disabled, historical, read-only | `text-gray-400` |

### ACGME Compliance Indicators

```tsx
// Visual hierarchy for compliance status
const complianceColors = {
  compliant: 'bg-green-100 text-green-800 border-green-200',
  warning: 'bg-yellow-100 text-yellow-800 border-yellow-200',
  violation: 'bg-red-100 text-red-800 border-red-200',
};
```

### Rotation Type Colors

Standardize across UI:
| Type | Color | Example Rotations |
|------|-------|-------------------|
| Inpatient | Red/Orange | IM, Peds, L&D, Night Float |
| Outpatient | Blue | FM Clinic, Cardio, Derm |
| Education | Purple | Didactics, Faculty Dev |
| Off | Gray | Leave, Military Duty |
| Procedures | Teal | Procedures block |

---

## Accessibility Checklist

- [ ] All interactive elements keyboard accessible
- [ ] Focus visible on all focusable elements
- [ ] Color not sole indicator (use icons + text)
- [ ] ARIA labels on icon-only buttons
- [ ] Skip links for schedule grids
- [ ] High contrast mode support
- [ ] Screen reader testing with NVDA/VoiceOver

---

## Performance Considerations

### Bundle Size Targets

| Category | Budget | Notes |
|----------|--------|-------|
| Icons | < 50KB | Tree-shake, import individual icons |
| Charts | < 100KB | Plotly is heavy, consider recharts-only |
| 3D | Lazy load | Only load Three.js when 3D view active |
| Tables | < 30KB | TanStack Table is lightweight |

### Lazy Loading Pattern

```tsx
// Lazy load heavy components
const ScheduleVisualization3D = dynamic(
  () => import('@/components/ScheduleVisualization3D'),
  { loading: () => <LoadingSkeleton /> }
);

// Only render when tab active
{activeTab === '3d' && <ScheduleVisualization3D />}
```

---

## Related Documentation

- `docs/planning/GUI_IMPORT_LESSONS.md` - Import workflow UX patterns
- `docs/guides/3d-schedule-visualization.md` - Three.js visualization guide
- `frontend/src/lib/api.ts` - API client with camelCase conversion
- `CLAUDE.md` - TypeScript naming conventions (camelCase required)

---

## Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-01-15 | Lucide as primary icons | Already integrated, good medical coverage |
| 2026-01-15 | TanStack Table recommended | Headless, same ecosystem as Query |
| 2026-01-15 | sonner for toasts | Smallest bundle, best DX |
| 2026-01-15 | No military symbology library | Custom SVGs needed for MIL-STD-2525 |
