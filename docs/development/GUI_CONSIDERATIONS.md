# GUI Considerations for Residency Scheduler

> **Last Updated:** 2026-01-17 | **Purpose:** Frontend library decisions and UI patterns

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

## Existing Custom Implementations

The codebase already includes custom implementations for common UI needs. **Consider these before adding new libraries.**

### Data Tables
**Component:** `frontend/src/components/ui/DataTable.tsx`

Features:
- Sorting, filtering, pagination
- Search functionality
- Custom column rendering
- Used by: `CallAssignmentTable`, `TemplateTable`, `PeopleTable`

```tsx
import { DataTable } from '@/components/ui/DataTable';

<DataTable
  data={residents}
  columns={columns}
  searchable
  sortable
  pagination
/>
```

### Calendar/Scheduler Views
**Components:**
- `AbsenceCalendar.tsx` - Full month view with date-fns
- `ScheduleCalendar.tsx` - Week-based schedule view
- `ScheduleGrid.tsx` - Grid-based block schedule

All use date-fns for date logic (already installed).

### Toast Notifications
**Component:** `frontend/src/components/Toast.tsx`

Features:
- Success, error, warning, info types
- Auto-dismiss with pause on hover
- Progress bar indicator
- Action buttons
- Persistent mode option
- Slide-in/out animations

```tsx
import { toast, ToastContainer } from '@/components/Toast';

// In layout
<ToastContainer />

// Usage
toast.success('Schedule saved');
toast.error('Validation failed');
toast.warning('Approaching limit');
```

### Accessible Modals
**Component:** `frontend/src/components/ConfirmDialog.tsx`

Features:
- WAI-ARIA compliant (alertdialog role)
- Keyboard navigation (Tab, Escape)
- Focus trapping and return
- Customizable actions

### UI Primitives
- `Dropdown.tsx` - Accessible dropdown menu
- `Alert.tsx` - Alert/banner component
- Various form inputs with Tailwind styling

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

### Military Medical Symbology

No React library exists for MIL-STD-2525 (NATO Joint Military Symbology). Options:
1. Custom SVG components based on [MIL-STD-2525D spec](https://www.jcs.mil/Portals/36/Documents/Doctrine/Other_Pubs/ms_2525d.pdf)
2. Use generic medical + military icons from Lucide/Phosphor
3. Create custom icon set for: medical unit, ambulance, hospital ship, CASEVAC, etc.

---

## Enhancement Opportunities

These are **optional improvements**, not critical gaps. Custom implementations already handle core functionality.

### 1. Form Validation Library (MEDIUM PRIORITY)

**Current:** Native React form handling with useState
**Enhancement:** react-hook-form + zod resolver

```bash
npm install react-hook-form @hookform/resolvers
```

Benefits:
- Reduced boilerplate for complex forms
- Native zod integration (zod already installed)
- Minimal re-renders

Best for: Swap request forms, admin settings, complex multi-step forms.

### 2. Table Virtualization (LOW PRIORITY)

**Current:** Custom DataTable handles typical datasets well
**Enhancement:** @tanstack/react-virtual for 1000+ row datasets

```bash
npm install @tanstack/react-table @tanstack/react-virtual
```

Only needed if performance issues arise with very large datasets.

### 3. Command Palette (LOW PRIORITY)

**Current:** No equivalent exists
**Enhancement:** cmdk for quick navigation

```bash
npm install cmdk
```

Use cases:
- Jump to resident: `⌘K` → "John Smith"
- Jump to block: `⌘K` → "Block 10"
- Quick actions: `⌘K` → "Generate schedule"

### 4. Additional Accessible Primitives (LOW PRIORITY)

**Current:** ConfirmDialog.tsx is ARIA-compliant
**Enhancement:** Radix UI for additional primitives (tooltips, popovers)

```bash
npm install @radix-ui/react-tooltip @radix-ui/react-popover
```

Only add as needed for new UI patterns.

### 5. Date Picker UI (LOW PRIORITY)

**Current:** Native date inputs with date-fns logic
**Enhancement:** react-day-picker for richer UX

```bash
npm install react-day-picker
```

Only add if users request better date selection UX.

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
const complianceColors = {
  compliant: 'bg-green-100 text-green-800 border-green-200',
  warning: 'bg-yellow-100 text-yellow-800 border-yellow-200',
  violation: 'bg-red-100 text-red-800 border-red-200',
};
```

### Rotation Type Colors

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
| Tables | < 30KB | Custom DataTable is lightweight |

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

- `frontend/src/components/ui/` - UI component library
- `frontend/src/components/Toast.tsx` - Notification system
- `frontend/src/lib/api.ts` - API client with camelCase conversion
- `CLAUDE.md` - TypeScript naming conventions (camelCase required)

---

## Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-01-17 | Document existing implementations | Custom Toast, DataTable, Calendar already built |
| 2026-01-17 | Reframe gaps as enhancements | Most functionality exists via custom components |
| 2026-01-15 | Lucide as primary icons | Already integrated, good medical coverage |
| 2026-01-15 | No military symbology library | Custom SVGs needed for MIL-STD-2525 |
