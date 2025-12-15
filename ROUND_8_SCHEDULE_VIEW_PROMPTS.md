# Round 8: Schedule View & Editing

**Status**: Project at ~70% - THE CORE FEATURE (viewing/editing the schedule) is missing.

---

## Opus-ScheduleGrid

**Priority**: CRITICAL - This is THE most important page in the application.

### YOUR EXCLUSIVE FILES (only you may modify):
- `frontend/src/app/schedule/page.tsx` (CREATE)
- `frontend/src/components/schedule/ScheduleGrid.tsx` (CREATE)
- `frontend/src/components/schedule/ScheduleCell.tsx` (CREATE)
- `frontend/src/components/schedule/ScheduleHeader.tsx` (CREATE)
- `frontend/src/components/schedule/BlockNavigation.tsx` (CREATE)

### CONTEXT:
Users currently CANNOT view the schedule they generate. This page shows the entire block schedule - who is assigned where on a half-day (AM/PM) basis.

### REQUIREMENTS:

#### Grid Structure:
- Rows = People (grouped: PGY-1, gap, PGY-2, gap, PGY-3, gap, Faculty)
- Columns = Days (with AM/PM sub-columns for each day)
- Each cell shows rotation abbreviation from template
- Default view: 4-week block (28 days)

#### Data Fetching:
```typescript
// Use existing hooks
import { useAssignments, usePeople, useRotationTemplates } from '@/lib/hooks'

// Fetch assignments for date range
const { data: assignments } = useAssignments({
  start_date: startDate,
  end_date: endDate
})

// Map person_id -> person, template_id -> template for display
```

#### Color Coding (CRITICAL - humans work on heuristics):
```typescript
const rotationColors: Record<string, string> = {
  clinic: 'bg-blue-100 text-blue-800 border-blue-300',
  inpatient: 'bg-purple-100 text-purple-800 border-purple-300',
  procedure: 'bg-red-100 text-red-800 border-red-300',
  conference: 'bg-gray-100 text-gray-800 border-gray-300',
  elective: 'bg-green-100 text-green-800 border-green-300',
  call: 'bg-orange-100 text-orange-800 border-orange-300',
  off: 'bg-white text-gray-400 border-gray-200',
}
```

#### Layout:
- Sticky left column (person names with PGY badge)
- Sticky top header (dates with day-of-week)
- Horizontal scroll for days
- Visual separator rows between PGY levels
- Weekend columns slightly shaded

#### Navigation:
- Date range picker (start/end date)
- Previous Block / Next Block buttons
- "Today" quick button
- "This Block" quick button (jump to current 4-week block)

#### Page Structure:
```tsx
export default function SchedulePage() {
  return (
    <ProtectedRoute>
      <div className="h-screen flex flex-col">
        {/* Header with title and navigation */}
        <div className="flex-shrink-0 p-4 border-b">
          <h1>Schedule</h1>
          <BlockNavigation />
        </div>

        {/* Grid takes remaining space */}
        <div className="flex-1 overflow-auto">
          <ScheduleGrid />
        </div>
      </div>
    </ProtectedRoute>
  )
}
```

### DO NOT MODIFY:
- Any files outside your exclusive list
- Navigation components (Opus-NavAndDocs handles that)

---

## Opus-ScheduleEdit

**Priority**: CRITICAL - Admins must be able to edit assignments directly.

### YOUR EXCLUSIVE FILES (only you may modify):
- `frontend/src/components/schedule/EditAssignmentModal.tsx` (CREATE)
- `frontend/src/components/schedule/AssignmentWarnings.tsx` (CREATE)
- `frontend/src/components/schedule/QuickAssignMenu.tsx` (CREATE)
- `frontend/src/components/schedule/CellActions.tsx` (CREATE)

### CONTEXT:
Admins and Coordinators need to edit assignments directly on the schedule. Special circumstances come up all the time - the system should WARN but NOT BLOCK. Sometimes what needs to be done needs to be done.

### REQUIREMENTS:

#### Click-to-Edit:
- ScheduleCell (from Opus-ScheduleGrid) should accept `onCellClick` prop
- Clicking opens EditAssignmentModal
- Only works for Admin/Coordinator roles (check useAuth)
- Faculty see view-only cells

#### Edit Modal:
```tsx
interface EditAssignmentModalProps {
  isOpen: boolean
  onClose: () => void
  assignment: Assignment | null  // null = creating new
  personId: string
  date: string
  session: 'AM' | 'PM'
}
```

Contents:
- Person name (read-only display)
- Date and session (read-only display)
- Rotation dropdown (all templates from useRotationTemplates)
- Notes field for override reason
- Save / Cancel / Delete buttons

#### Warning System (WARN, NOT BLOCK):
```typescript
interface AssignmentWarning {
  type: 'hours' | 'supervision' | 'conflict' | 'absence' | 'capacity'
  severity: 'info' | 'warning' | 'critical'
  message: string
}

// Example warnings:
const warnings: AssignmentWarning[] = [
  { type: 'hours', severity: 'warning', message: 'This will put Dr. Smith at 82 hours this week (exceeds 80-hour limit)' },
  { type: 'absence', severity: 'critical', message: 'Dr. Smith is marked as on vacation this day' },
  { type: 'supervision', severity: 'info', message: 'No faculty supervisor assigned to this rotation' },
]
```

- Display warnings in modal but ALLOW save
- For critical warnings, require checkbox confirmation: "I understand this override"
- Log the override reason in notes

#### Quick Assign Menu:
- Right-click (desktop) or long-press (mobile) on cell
- Shows dropdown with:
  - Recently used rotations (top 5)
  - Separator
  - "Mark as Off"
  - "Clear Assignment"
  - "Edit Details..." (opens full modal)

#### Permissions:
```typescript
const { user } = useAuth()
const canEdit = user?.role === 'admin' || user?.role === 'coordinator'
```

### Hooks to use:
- `useUpdateAssignment` - for editing
- `useCreateAssignment` - for new assignments
- `useDeleteAssignment` - for clearing
- `useAuth` - for permission check

### DO NOT MODIFY:
- ScheduleGrid.tsx (Opus-ScheduleGrid owns that)
- Just export your components for ScheduleGrid to import

---

## Opus-PersonalView

**Priority**: HIGH - Each person needs to see their own schedule easily.

### YOUR EXCLUSIVE FILES (only you may modify):
- `frontend/src/components/schedule/PersonFilter.tsx` (CREATE)
- `frontend/src/components/schedule/PersonalScheduleCard.tsx` (CREATE)
- `frontend/src/components/schedule/MyScheduleWidget.tsx` (CREATE)
- `frontend/src/app/schedule/[personId]/page.tsx` (CREATE)

### CONTEXT:
Each resident and faculty member needs to see their OWN schedule easily. But everyone can see everyone's schedule for transparency.

### REQUIREMENTS:

#### Person Filter Dropdown (for schedule page header):
```tsx
interface PersonFilterProps {
  selectedPersonId: string | null  // null = show all
  onSelect: (personId: string | null) => void
}
```

Options:
- "All People" (default - full grid view)
- "My Schedule" (if logged-in user is in people list)
- Separator
- Residents grouped by PGY level
- Faculty section

Include search/filter input for large lists.

#### URL Support:
- `/schedule` - full grid, all people
- `/schedule?person=abc123` - filtered to specific person
- `/schedule/abc123` - dedicated personal schedule page

#### Personal Schedule Card:
When viewing single person, show card format instead of grid:
```tsx
<PersonalScheduleCard personId={personId} dateRange={...} />
```
- List of assignments for date range
- Each row: Date | Day | AM Rotation | PM Rotation
- Color-coded rotation badges
- Highlight today's row
- Show absences inline (e.g., "VACATION" instead of rotation)

#### My Schedule Widget (for Dashboard):
```tsx
<MyScheduleWidget />
```
- Shows next 5 upcoming assignments for logged-in user
- "No upcoming assignments" if none
- "View Full Schedule" link to `/schedule?person={myId}`
- Only shows if logged-in user exists in people list

#### Integration:
- Export PersonFilter for Opus-ScheduleGrid to use in header
- Export MyScheduleWidget for Dashboard to use

### DO NOT MODIFY:
- Dashboard page.tsx (just export the widget)
- ScheduleGrid.tsx (just export PersonFilter)

---

## Opus-CalendarViews

**Priority**: MEDIUM - Multiple view options for different use cases.

### YOUR EXCLUSIVE FILES (only you may modify):
- `frontend/src/components/schedule/ViewToggle.tsx` (CREATE)
- `frontend/src/components/schedule/DayView.tsx` (CREATE)
- `frontend/src/components/schedule/WeekView.tsx` (CREATE)
- `frontend/src/components/schedule/MonthView.tsx` (CREATE)

### CONTEXT:
Users need different views depending on their task:
- Block: Full 4-week view (default, from ScheduleGrid)
- Week: 7-day planning view
- Day: Single day detailed view
- Month: Calendar overview

### REQUIREMENTS:

#### View Toggle:
```tsx
type ScheduleView = 'day' | 'week' | 'month' | 'block'

interface ViewToggleProps {
  currentView: ScheduleView
  onChange: (view: ScheduleView) => void
}
```
- Segmented control or tabs
- Icons: CalendarDays, Calendar, CalendarRange, LayoutGrid
- Persist preference in localStorage
- URL param support: `/schedule?view=week`

#### Day View:
- Single day, all people
- Two sections: Morning (AM) and Afternoon (PM)
- Larger cells with full rotation name
- Previous/Next day arrows
- Jump to date picker

#### Week View:
- Monday-Sunday (or Sunday-Saturday, configurable)
- Condensed rows, all people visible
- Week number display
- Quick navigation to adjacent weeks

#### Month View:
- Traditional calendar grid
- Each day cell shows:
  - Count badge: "12 assignments"
  - Color indicators if any issues
- Click day to drill into Day View
- Federal holidays highlighted

#### Shared Requirements:
- All views use same color coding as ScheduleGrid
- All views respect person filter
- All views support cell click for editing (if permitted)
- Consistent date navigation header

#### Integration:
- Export ViewToggle for schedule page header
- Export view components for schedule page to render based on selection

### DO NOT MODIFY:
- ScheduleGrid.tsx (that's the Block view, already handled)

---

## Opus-NavAndDocs

**Priority**: MEDIUM - Navigation and documentation updates.

### YOUR EXCLUSIVE FILES (only you may modify):
- `frontend/src/components/Navigation.tsx` (MODIFY)
- `frontend/src/components/MobileNav.tsx` (MODIFY)
- `USER_GUIDE.md` (MODIFY)
- `frontend/src/app/help/page.tsx` (MODIFY)

### CONTEXT:
The Schedule page is THE core feature. Navigation must reflect this. Documentation must explain how to use it.

### REQUIREMENTS:

#### Navigation Changes:

Update navItems array in BOTH Navigation.tsx and MobileNav.tsx:

```typescript
import { CalendarDays } from 'lucide-react'

const navItems: NavItem[] = [
  { href: '/', label: 'Dashboard', icon: Calendar },
  { href: '/schedule', label: 'Schedule', icon: CalendarDays },  // NEW - position 2
  { href: '/people', label: 'People', icon: Users },
  { href: '/templates', label: 'Templates', icon: FileText },
  { href: '/absences', label: 'Absences', icon: CalendarOff },
  { href: '/compliance', label: 'Compliance', icon: AlertTriangle },
  { href: '/help', label: 'Help', icon: HelpCircle },
  { href: '/settings', label: 'Settings', icon: Settings, adminOnly: true },
]
```

#### USER_GUIDE.md Updates:

Add new section after "Dashboard" section:

```markdown
## Schedule View

The Schedule page is the heart of the application - where you view and manage all assignments.

### Viewing the Schedule

1. Click **Schedule** in the navigation bar
2. The grid shows all people (rows) and days (columns)
3. Each cell shows the rotation abbreviation for AM or PM

### Understanding the Grid

- **Rows**: Grouped by PGY level (PGY-1, PGY-2, PGY-3, then Faculty)
- **Columns**: Each day has two columns (AM and PM)
- **Colors**: Each rotation type has a distinct color
  - Blue: Clinic
  - Purple: Inpatient
  - Red: Procedure
  - Gray: Conference
  - Green: Elective
  - Orange: Call

### Navigating Dates

- Use **Previous Block** / **Next Block** to move 4 weeks
- Click **Today** to jump to current date
- Use the date picker for specific dates

### Viewing Personal Schedules

- Use the **Person** dropdown to filter to one person
- Or click **My Schedule** to see your own assignments
- Share personal schedule links with residents

### Editing Assignments (Admin/Coordinator only)

1. Click any cell to open the edit dialog
2. Select a different rotation from the dropdown
3. Review any warnings (hours limit, absences, etc.)
4. Add a note explaining the change (optional)
5. Click **Save**

**Note**: Warnings are advisory - you can save despite warnings when special circumstances require it.

### View Options

Switch between views using the toggle:
- **Block**: Full 4-week grid (default)
- **Week**: 7-day view
- **Day**: Single day detail
- **Month**: Calendar overview
```

Update Table of Contents to include Schedule View.

Update Navigation table to include Schedule.

#### Help Page Updates:

Add to Quick Reference section:
```
| View schedule | Schedule page |
| Edit assignment | Schedule → Click cell |
| See my schedule | Schedule → Person dropdown → My Schedule |
```

Add to FAQ section:
```tsx
<FAQItem
  question="How do I see my personal schedule?"
  answer="Go to Schedule page, click the Person dropdown, and select 'My Schedule'. You can also bookmark the direct link."
/>
<FAQItem
  question="How do I change an assignment?"
  answer="Click on any cell in the schedule grid. This opens the edit dialog where you can change the rotation. Only Admins and Coordinators can edit."
/>
<FAQItem
  question="What do the colors mean on the schedule?"
  answer="Each rotation type has a color: Blue=Clinic, Purple=Inpatient, Red=Procedure, Gray=Conference, Green=Elective, Orange=Call. This makes it easy to see patterns at a glance."
/>
<FAQItem
  question="Why am I getting a warning when I edit an assignment?"
  answer="Warnings alert you to potential issues like exceeding hour limits or scheduling during an absence. You can still save - warnings are advisory for when special circumstances require overrides."
/>
```

### DO NOT MODIFY:
- Any schedule components (other Opus instances handle those)
- Other pages

---

## Coordination Notes

### Import/Export Between Opus Instances:

**Opus-ScheduleGrid** exports:
- `ScheduleGrid` - main grid component
- `ScheduleCell` - cell component (accepts onCellClick)

**Opus-ScheduleEdit** exports:
- `EditAssignmentModal`
- `QuickAssignMenu`
- `AssignmentWarnings`

**Opus-PersonalView** exports:
- `PersonFilter`
- `PersonalScheduleCard`
- `MyScheduleWidget`

**Opus-CalendarViews** exports:
- `ViewToggle`
- `DayView`, `WeekView`, `MonthView`

### Final Assembly (schedule/page.tsx by Opus-ScheduleGrid):
```tsx
import { ScheduleGrid } from '@/components/schedule/ScheduleGrid'
import { EditAssignmentModal } from '@/components/schedule/EditAssignmentModal'
import { PersonFilter } from '@/components/schedule/PersonFilter'
import { ViewToggle } from '@/components/schedule/ViewToggle'
import { DayView, WeekView, MonthView } from '@/components/schedule/...'
```

---

## After Round 8

Expected completion: **~85%**

Remaining for future rounds:
- Dashboard integration (MyScheduleWidget)
- E2E tests for schedule features
- Performance optimization for large schedules
- Mobile-specific schedule UX
- Bulk assignment operations
