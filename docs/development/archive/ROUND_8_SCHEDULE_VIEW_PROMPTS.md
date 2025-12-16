# Round 8: Schedule View & Editing (6 Parallel Opus Instances)

**Project Status**: ~70% complete - THE CORE FEATURE (viewing/editing schedule) is missing.

**After Round 8**: ~90% complete

---

## 1. Opus-ScheduleGrid

**Priority**: CRITICAL - This is THE most important page in the application.

### YOUR EXCLUSIVE FILES (only you may modify):
- `frontend/src/app/schedule/page.tsx` (CREATE)
- `frontend/src/components/schedule/ScheduleGrid.tsx` (CREATE)
- `frontend/src/components/schedule/ScheduleCell.tsx` (CREATE)
- `frontend/src/components/schedule/ScheduleHeader.tsx` (CREATE)
- `frontend/src/components/schedule/BlockNavigation.tsx` (CREATE)
- `frontend/src/components/schedule/index.ts` (CREATE - barrel export)

### CONTEXT:
Users currently CANNOT view the schedule they generate. This page shows the entire block schedule - who is assigned where on a half-day (AM/PM) basis. This is like a banking app without an account balance page.

### REQUIREMENTS:

#### Grid Structure:
- Rows = People (grouped: PGY-1, then gap row, PGY-2, gap row, PGY-3, gap row, Faculty)
- Columns = Days (with AM/PM sub-columns for each day)
- Each cell shows rotation abbreviation from template
- Default view: 4-week block (28 days = 56 columns for AM/PM)

#### Data Fetching:
```typescript
import { useAssignments, usePeople, useRotationTemplates } from '@/lib/hooks'
import { useMemo } from 'react'

// In component:
const { data: assignmentsData, isLoading: assignmentsLoading } = useAssignments({
  start_date: startDate,
  end_date: endDate
})
const { data: peopleData } = usePeople()
const { data: templatesData } = useRotationTemplates()

// Build lookup maps
const assignments = assignmentsData?.items || []
const people = peopleData?.items || []
const templates = templatesData?.items || []

const templateMap = useMemo(() =>
  new Map(templates.map(t => [t.id, t])), [templates])

const assignmentMap = useMemo(() => {
  const map = new Map<string, Assignment>() // key: `${personId}-${date}-${session}`
  assignments.forEach(a => {
    map.set(`${a.person_id}-${a.date}-${a.session}`, a)
  })
  return map
}, [assignments])
```

#### Color Coding (CRITICAL - humans work on heuristics):
```typescript
export const rotationColors: Record<string, string> = {
  clinic: 'bg-blue-100 text-blue-800 border-blue-200',
  inpatient: 'bg-purple-100 text-purple-800 border-purple-200',
  procedure: 'bg-red-100 text-red-800 border-red-200',
  conference: 'bg-gray-100 text-gray-800 border-gray-200',
  elective: 'bg-green-100 text-green-800 border-green-200',
  call: 'bg-orange-100 text-orange-800 border-orange-200',
  off: 'bg-white text-gray-400 border-gray-100',
  absence: 'bg-yellow-100 text-yellow-800 border-yellow-200',
}
```

#### Layout Structure:
```tsx
<div className="h-[calc(100vh-200px)] flex flex-col">
  {/* Sticky header with dates */}
  <div className="flex-shrink-0 overflow-x-auto">
    <ScheduleHeader dates={dates} />
  </div>

  {/* Scrollable grid body */}
  <div className="flex-1 overflow-auto">
    <div className="min-w-max">
      {/* PGY-1 section */}
      <div className="bg-blue-50 px-4 py-1 font-semibold text-sm sticky left-0">
        PGY-1 Residents
      </div>
      {pgy1Residents.map(person => (
        <ScheduleRow key={person.id} person={person} dates={dates} />
      ))}

      {/* Gap row */}
      <div className="h-4 bg-gray-50" />

      {/* PGY-2, PGY-3, Faculty sections... */}
    </div>
  </div>
</div>
```

#### ScheduleCell Component:
```tsx
interface ScheduleCellProps {
  assignment: Assignment | null
  template: RotationTemplate | null
  absence: Absence | null
  personId: string
  date: string
  session: 'AM' | 'PM'
  onClick?: () => void
  canEdit: boolean
}

export function ScheduleCell({
  assignment, template, absence, onClick, canEdit
}: ScheduleCellProps) {
  // If absent, show absence type
  if (absence) {
    return (
      <div className={`${rotationColors.absence} px-1 py-0.5 text-xs truncate`}>
        {absence.absence_type.toUpperCase().slice(0, 3)}
      </div>
    )
  }

  // If no assignment, empty cell
  if (!assignment || !template) {
    return (
      <div
        className={`h-6 border-r border-gray-100 ${canEdit ? 'cursor-pointer hover:bg-gray-50' : ''}`}
        onClick={canEdit ? onClick : undefined}
      />
    )
  }

  const colorClass = rotationColors[template.activity_type] || rotationColors.off

  return (
    <div
      className={`${colorClass} px-1 py-0.5 text-xs truncate border-r ${canEdit ? 'cursor-pointer hover:opacity-80' : ''}`}
      onClick={canEdit ? onClick : undefined}
      title={template.name}
    >
      {template.abbreviation || template.name.slice(0, 3)}
    </div>
  )
}
```

#### Block Navigation:
```tsx
interface BlockNavigationProps {
  startDate: string
  endDate: string
  onDateChange: (start: string, end: string) => void
}

// Buttons: "← Prev Block" | "Today" | "This Block" | "Next Block →"
// Date range display: "Dec 2 - Dec 29, 2024"
```

#### Page Structure:
```tsx
'use client'

import { useState } from 'react'
import { startOfWeek, addDays, format } from 'date-fns'
import { ProtectedRoute } from '@/components/ProtectedRoute'
import { ScheduleGrid } from '@/components/schedule/ScheduleGrid'
import { BlockNavigation } from '@/components/schedule/BlockNavigation'
// Import other components from other Opus instances as they become available

export default function SchedulePage() {
  const today = new Date()
  const defaultStart = startOfWeek(today, { weekStartsOn: 1 })
  const defaultEnd = addDays(defaultStart, 27) // 4 weeks

  const [startDate, setStartDate] = useState(format(defaultStart, 'yyyy-MM-dd'))
  const [endDate, setEndDate] = useState(format(defaultEnd, 'yyyy-MM-dd'))

  return (
    <ProtectedRoute>
      <div className="flex flex-col h-[calc(100vh-64px)]">
        {/* Header */}
        <div className="flex-shrink-0 px-4 py-3 border-b bg-white">
          <div className="flex items-center justify-between">
            <h1 className="text-xl font-bold text-gray-900">Schedule</h1>
            <BlockNavigation
              startDate={startDate}
              endDate={endDate}
              onDateChange={(start, end) => {
                setStartDate(start)
                setEndDate(end)
              }}
            />
          </div>
        </div>

        {/* Grid */}
        <div className="flex-1 overflow-hidden">
          <ScheduleGrid startDate={startDate} endDate={endDate} />
        </div>
      </div>
    </ProtectedRoute>
  )
}
```

### DO NOT MODIFY:
- Navigation components (Opus-NavAndDocs handles that)
- Any existing pages or components

---

## 2. Opus-ScheduleEdit

**Priority**: CRITICAL - Admins must be able to edit assignments directly.

### YOUR EXCLUSIVE FILES (only you may modify):
- `frontend/src/components/schedule/EditAssignmentModal.tsx` (CREATE)
- `frontend/src/components/schedule/AssignmentWarnings.tsx` (CREATE)
- `frontend/src/components/schedule/QuickAssignMenu.tsx` (CREATE)

### CONTEXT:
Admins and Coordinators need to edit assignments directly on the schedule. Special circumstances come up all the time - the system should WARN but NOT BLOCK. Sometimes what needs to be done needs to be done.

### REQUIREMENTS:

#### EditAssignmentModal:
```tsx
interface EditAssignmentModalProps {
  isOpen: boolean
  onClose: () => void
  assignment: Assignment | null  // null = creating new
  personId: string
  personName: string
  date: string
  session: 'AM' | 'PM'
}

// Modal contents:
// - Header: "Edit Assignment" or "New Assignment"
// - Person name (read-only)
// - Date and session display (read-only)
// - Rotation dropdown (all templates)
// - Notes field for override reason
// - Warnings section (AssignmentWarnings component)
// - Buttons: Cancel | Delete (if editing) | Save
```

#### Warning System (WARN, NOT BLOCK):
```typescript
interface AssignmentWarning {
  type: 'hours' | 'supervision' | 'conflict' | 'absence' | 'capacity'
  severity: 'info' | 'warning' | 'critical'
  message: string
}

// Display logic:
// - info: blue info icon, small text
// - warning: yellow warning icon, normal text
// - critical: red alert icon, bold text, requires confirmation checkbox

// Example warnings to check:
function checkWarnings(
  personId: string,
  date: string,
  templateId: string,
  absences: Absence[],
  existingAssignments: Assignment[]
): AssignmentWarning[] {
  const warnings: AssignmentWarning[] = []

  // Check if person is absent
  const isAbsent = absences.some(a =>
    a.person_id === personId &&
    date >= a.start_date &&
    date <= a.end_date
  )
  if (isAbsent) {
    warnings.push({
      type: 'absence',
      severity: 'critical',
      message: 'This person is marked as absent on this date'
    })
  }

  // Check weekly hours (simplified - real logic would sum hours)
  // ... etc

  return warnings
}
```

#### AssignmentWarnings Component:
```tsx
interface AssignmentWarningsProps {
  warnings: AssignmentWarning[]
  onCriticalAcknowledge?: (acknowledged: boolean) => void
}

export function AssignmentWarnings({ warnings, onCriticalAcknowledge }: AssignmentWarningsProps) {
  const hasCritical = warnings.some(w => w.severity === 'critical')
  const [acknowledged, setAcknowledged] = useState(false)

  if (warnings.length === 0) return null

  return (
    <div className="space-y-2 p-3 bg-amber-50 rounded-lg border border-amber-200">
      <div className="text-sm font-medium text-amber-800">Warnings</div>
      {warnings.map((warning, i) => (
        <div key={i} className={`flex items-start gap-2 text-sm ${
          warning.severity === 'critical' ? 'text-red-700' :
          warning.severity === 'warning' ? 'text-amber-700' : 'text-blue-700'
        }`}>
          {/* Icon based on severity */}
          <span>{warning.message}</span>
        </div>
      ))}

      {hasCritical && (
        <label className="flex items-center gap-2 mt-3 text-sm">
          <input
            type="checkbox"
            checked={acknowledged}
            onChange={(e) => {
              setAcknowledged(e.target.checked)
              onCriticalAcknowledge?.(e.target.checked)
            }}
            className="rounded border-gray-300"
          />
          <span className="text-red-700 font-medium">
            I understand and want to proceed anyway
          </span>
        </label>
      )}
    </div>
  )
}
```

#### QuickAssignMenu (right-click context menu):
```tsx
interface QuickAssignMenuProps {
  isOpen: boolean
  position: { x: number; y: number }
  onClose: () => void
  onSelectTemplate: (templateId: string) => void
  onClear: () => void
  onEditDetails: () => void
  recentTemplates: RotationTemplate[]
  allTemplates: RotationTemplate[]
}

// Menu items:
// - Recent (top 5 used)
// - ---separator---
// - All templates in submenu or scrollable list
// - ---separator---
// - "Mark as Off"
// - "Clear Assignment"
// - ---separator---
// - "Edit Details..."
```

#### Hooks to use:
- `useCreateAssignment` for new
- `useUpdateAssignment` for edit
- `useDeleteAssignment` for clear/delete
- `useAbsences` for warning checks

### DO NOT MODIFY:
- ScheduleGrid.tsx (Opus-ScheduleGrid owns that - just export your components)

---

## 3. Opus-PersonalView

**Priority**: HIGH - Each person needs to see their own schedule easily.

### YOUR EXCLUSIVE FILES (only you may modify):
- `frontend/src/components/schedule/PersonFilter.tsx` (CREATE)
- `frontend/src/components/schedule/PersonalScheduleCard.tsx` (CREATE)
- `frontend/src/components/schedule/MyScheduleWidget.tsx` (CREATE)

### CONTEXT:
Each resident and faculty member needs to see their OWN schedule easily. But everyone can see everyone's schedule for transparency.

### REQUIREMENTS:

#### PersonFilter Dropdown:
```tsx
interface PersonFilterProps {
  selectedPersonId: string | null  // null = show all
  onSelect: (personId: string | null) => void
  people: Person[]
  currentUserId?: string  // for "My Schedule" option
}

export function PersonFilter({ selectedPersonId, onSelect, people, currentUserId }: PersonFilterProps) {
  // Group people by type and PGY level
  const grouped = useMemo(() => {
    const pgy1 = people.filter(p => p.type === 'resident' && p.pgy_level === 1)
    const pgy2 = people.filter(p => p.type === 'resident' && p.pgy_level === 2)
    const pgy3 = people.filter(p => p.type === 'resident' && p.pgy_level === 3)
    const faculty = people.filter(p => p.type === 'faculty')
    return { pgy1, pgy2, pgy3, faculty }
  }, [people])

  return (
    <select
      value={selectedPersonId || ''}
      onChange={(e) => onSelect(e.target.value || null)}
      className="input-field"
    >
      <option value="">All People</option>
      {currentUserId && (
        <option value={currentUserId}>📋 My Schedule</option>
      )}
      <optgroup label="PGY-1">
        {grouped.pgy1.map(p => <option key={p.id} value={p.id}>{p.name}</option>)}
      </optgroup>
      <optgroup label="PGY-2">
        {grouped.pgy2.map(p => <option key={p.id} value={p.id}>{p.name}</option>)}
      </optgroup>
      <optgroup label="PGY-3">
        {grouped.pgy3.map(p => <option key={p.id} value={p.id}>{p.name}</option>)}
      </optgroup>
      <optgroup label="Faculty">
        {grouped.faculty.map(p => <option key={p.id} value={p.id}>{p.name}</option>)}
      </optgroup>
    </select>
  )
}
```

#### PersonalScheduleCard (for filtered/personal view):
```tsx
interface PersonalScheduleCardProps {
  person: Person
  assignments: Assignment[]
  templates: RotationTemplate[]
  absences: Absence[]
  startDate: string
  endDate: string
}

// Display format:
// ┌─────────────────────────────────────┐
// │ Dr. Jane Smith - PGY-2              │
// ├─────────────────────────────────────┤
// │ Mon, Dec 2    AM: Clinic  PM: Clinic│
// │ Tue, Dec 3    AM: Ward    PM: Ward  │
// │ Wed, Dec 4    *** VACATION ***      │
// │ ...                                 │
// └─────────────────────────────────────┘

export function PersonalScheduleCard({ person, assignments, templates, absences, startDate, endDate }: PersonalScheduleCardProps) {
  // Generate date range
  const dates = useMemo(() => {
    const result: string[] = []
    let current = new Date(startDate)
    const end = new Date(endDate)
    while (current <= end) {
      result.push(format(current, 'yyyy-MM-dd'))
      current = addDays(current, 1)
    }
    return result
  }, [startDate, endDate])

  // ... render card with each date row
}
```

#### MyScheduleWidget (for Dashboard):
```tsx
export function MyScheduleWidget() {
  const { user } = useAuth()
  const { data: peopleData } = usePeople()

  // Find current user in people list
  const currentPerson = useMemo(() => {
    if (!user || !peopleData?.items) return null
    // Match by email or name - adjust based on your user/person linking
    return peopleData.items.find(p =>
      p.email === user.email || p.name === user.username
    )
  }, [user, peopleData])

  // If user isn't in people list, don't show widget
  if (!currentPerson) return null

  // Fetch next 2 weeks of assignments for this person
  const today = format(new Date(), 'yyyy-MM-dd')
  const twoWeeks = format(addDays(new Date(), 14), 'yyyy-MM-dd')

  const { data: assignmentsData } = useAssignments({
    person_id: currentPerson.id,
    start_date: today,
    end_date: twoWeeks
  })

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900">My Schedule</h3>
        <Link href={`/schedule?person=${currentPerson.id}`} className="text-blue-600 text-sm hover:underline">
          View Full →
        </Link>
      </div>

      {/* List next 5 assignments */}
      <div className="space-y-2">
        {assignmentsData?.items?.slice(0, 5).map(assignment => (
          // Render assignment row
        ))}
      </div>
    </div>
  )
}
```

### Integration Points:
- Export `PersonFilter` for schedule page header
- Export `MyScheduleWidget` for Dashboard to import

### DO NOT MODIFY:
- Dashboard page.tsx (Opus-DashboardIntegration handles that)
- ScheduleGrid.tsx

---

## 4. Opus-CalendarViews

**Priority**: MEDIUM - Multiple view options for different use cases.

### YOUR EXCLUSIVE FILES (only you may modify):
- `frontend/src/components/schedule/ViewToggle.tsx` (CREATE)
- `frontend/src/components/schedule/DayView.tsx` (CREATE)
- `frontend/src/components/schedule/WeekView.tsx` (CREATE)
- `frontend/src/components/schedule/MonthView.tsx` (CREATE)

### CONTEXT:
Users need different views:
- Block: Full 4-week view (default - ScheduleGrid handles this)
- Week: 7-day planning view
- Day: Single day detailed view
- Month: Calendar overview

### REQUIREMENTS:

#### ViewToggle:
```tsx
export type ScheduleView = 'day' | 'week' | 'month' | 'block'

interface ViewToggleProps {
  currentView: ScheduleView
  onChange: (view: ScheduleView) => void
}

export function ViewToggle({ currentView, onChange }: ViewToggleProps) {
  return (
    <div className="flex gap-1 bg-gray-100 p-1 rounded-lg">
      {[
        { value: 'day', icon: CalendarDays, label: 'Day' },
        { value: 'week', icon: Calendar, label: 'Week' },
        { value: 'month', icon: CalendarRange, label: 'Month' },
        { value: 'block', icon: LayoutGrid, label: 'Block' },
      ].map(({ value, icon: Icon, label }) => (
        <button
          key={value}
          onClick={() => onChange(value as ScheduleView)}
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded text-sm font-medium transition-colors ${
            currentView === value
              ? 'bg-white text-gray-900 shadow-sm'
              : 'text-gray-600 hover:text-gray-900'
          }`}
        >
          <Icon className="w-4 h-4" />
          <span className="hidden sm:inline">{label}</span>
        </button>
      ))}
    </div>
  )
}
```

#### DayView:
```tsx
interface DayViewProps {
  date: string
  people: Person[]
  assignments: Assignment[]
  templates: RotationTemplate[]
  absences: Absence[]
  onCellClick?: (personId: string, date: string, session: 'AM' | 'PM') => void
  canEdit: boolean
}

// Layout:
// ┌────────────────────────────────────────────┐
// │         Monday, December 2, 2024           │
// │        ◄ Prev          Next ►              │
// ├────────────────────────────────────────────┤
// │          │    MORNING    │   AFTERNOON     │
// ├──────────┼───────────────┼─────────────────┤
// │ PGY-1    │               │                 │
// │ Dr. Smith│   Clinic      │    Ward         │
// │ Dr. Jones│   Ward        │    Clinic       │
// ├──────────┼───────────────┼─────────────────┤
// │ PGY-2    │               │                 │
// │ ...      │               │                 │
// └────────────────────────────────────────────┘
```

#### WeekView:
```tsx
interface WeekViewProps {
  startDate: string  // Monday of the week
  people: Person[]
  assignments: Assignment[]
  templates: RotationTemplate[]
  absences: Absence[]
  onCellClick?: (personId: string, date: string, session: 'AM' | 'PM') => void
  canEdit: boolean
}

// 7 columns (Mon-Sun), rows grouped by PGY/Faculty
// Condensed cells showing abbreviation only
// Color coded by rotation type
```

#### MonthView:
```tsx
interface MonthViewProps {
  month: Date  // any date in the target month
  assignments: Assignment[]
  absences: Absence[]
  onDayClick: (date: string) => void  // drill down to day view
}

// Traditional calendar grid
// Each day cell shows:
// - Day number
// - Color dots or count badge for assignments
// - Holiday indicator if applicable
```

### Integration:
- Export ViewToggle for schedule page
- Export view components for conditional rendering

---

## 5. Opus-NavAndDocs

**Priority**: MEDIUM - Navigation and documentation updates.

### YOUR EXCLUSIVE FILES (only you may modify):
- `frontend/src/components/Navigation.tsx` (MODIFY)
- `frontend/src/components/MobileNav.tsx` (MODIFY)
- `USER_GUIDE.md` (MODIFY)
- `frontend/src/app/help/page.tsx` (MODIFY)

### REQUIREMENTS:

#### Navigation Update:

Add Schedule as the SECOND item (after Dashboard):

```typescript
import { CalendarDays } from 'lucide-react'

const navItems: NavItem[] = [
  { href: '/', label: 'Dashboard', icon: Calendar },
  { href: '/schedule', label: 'Schedule', icon: CalendarDays },  // ADD THIS
  { href: '/people', label: 'People', icon: Users },
  { href: '/templates', label: 'Templates', icon: FileText },
  { href: '/absences', label: 'Absences', icon: CalendarOff },
  { href: '/compliance', label: 'Compliance', icon: AlertTriangle },
  { href: '/help', label: 'Help', icon: HelpCircle },
  { href: '/settings', label: 'Settings', icon: Settings, adminOnly: true },
]
```

Update BOTH Navigation.tsx AND MobileNav.tsx.

#### USER_GUIDE.md Updates:

Add new section "## Schedule View" after Dashboard section with:
- Viewing the schedule grid
- Understanding AM/PM columns
- Color coding explanation (with color key)
- Navigating dates (blocks, weeks)
- Filtering by person
- Switching views (day/week/month/block)
- Editing assignments (admin/coordinator)
- Warnings and overrides

Update Table of Contents.
Update Navigation table.

#### Help Page Updates:

Add to Quick Reference:
```
| View schedule | Schedule page |
| Edit assignment | Schedule → Click cell |
| See my schedule | Schedule → Person dropdown |
```

Add FAQ items:
- "How do I see my personal schedule?"
- "How do I change an assignment?"
- "What do the colors mean on the schedule?"
- "Why am I getting a warning when I edit an assignment?"

---

## 6. Opus-DashboardIntegration

**Priority**: HIGH - Connect schedule features to dashboard.

### YOUR EXCLUSIVE FILES (only you may modify):
- `frontend/src/app/page.tsx` (MODIFY - Dashboard)
- `frontend/src/components/dashboard/ScheduleSummary.tsx` (MODIFY if exists, or note for integration)

### CONTEXT:
The Dashboard should show schedule-related information and link to the schedule page. The MyScheduleWidget from Opus-PersonalView should be added here.

### REQUIREMENTS:

#### Add MyScheduleWidget to Dashboard:
```tsx
// In page.tsx (Dashboard)
import { MyScheduleWidget } from '@/components/schedule/MyScheduleWidget'

// Add to the grid layout alongside existing widgets:
<div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
  <ScheduleSummary />
  <ComplianceAlert />
  <UpcomingAbsences />
  <QuickActions />
  <MyScheduleWidget />  {/* ADD THIS */}
</div>
```

#### Update QuickActions:
- "View Schedule" button linking to /schedule
- Ensure "Generate Schedule" still works

#### Update ScheduleSummary:
- Add "View Full Schedule →" link to /schedule
- Show current block date range
- Count of total assignments this block

#### Conditional Widget Display:
```tsx
// MyScheduleWidget should handle its own visibility
// (returns null if user not in people list)
// But wrap in Suspense for loading state:

<Suspense fallback={<div className="card animate-pulse h-48" />}>
  <MyScheduleWidget />
</Suspense>
```

### DO NOT MODIFY:
- Other dashboard widgets (unless adding links to schedule)
- Schedule components (other Opus instances own those)

---

## Coordination Summary

### Component Dependencies:

```
Opus-ScheduleGrid creates:
├── /schedule page
├── ScheduleGrid (main grid)
├── ScheduleCell (individual cells)
├── ScheduleHeader (date headers)
└── BlockNavigation (prev/next/today)

Opus-ScheduleEdit creates:
├── EditAssignmentModal (click-to-edit)
├── AssignmentWarnings (warning display)
└── QuickAssignMenu (right-click menu)

Opus-PersonalView creates:
├── PersonFilter (dropdown filter)
├── PersonalScheduleCard (single person view)
└── MyScheduleWidget (dashboard widget)

Opus-CalendarViews creates:
├── ViewToggle (day/week/month/block tabs)
├── DayView
├── WeekView
└── MonthView

Opus-NavAndDocs modifies:
├── Navigation.tsx (add Schedule link)
├── MobileNav.tsx (add Schedule link)
├── USER_GUIDE.md (add Schedule section)
└── help/page.tsx (add Schedule FAQ)

Opus-DashboardIntegration modifies:
├── page.tsx (add MyScheduleWidget)
└── QuickActions.tsx (add View Schedule link)
```

### After Round 8 Completion:

The schedule page will:
1. Show full block view with AM/PM columns
2. Color-code by rotation type
3. Support click-to-edit for admin/coordinator
4. Show warnings but allow overrides
5. Filter by person (personal schedule)
6. Switch between day/week/month/block views
7. Integrate with dashboard

**Expected completion after Round 8: ~90%**

### Remaining for future rounds (~10%):
- E2E tests for schedule
- Mobile-specific optimizations
- Bulk operations
- Performance tuning for large schedules
- Print-friendly schedule view
