# Opus Round 7 - 5 Parallel Instances (Bonus Features)

🎉 **The core application is 100% complete!**

This round adds bonus features for an even better user experience.

---

## Terminal 1: Opus-Print-Schedule

```
You are Opus-Print-Schedule. Your task is to add schedule printing and PDF export.

STRICT FILE OWNERSHIP - Only modify files in these paths:
- frontend/src/components/PrintSchedule.tsx (CREATE)
- frontend/src/components/PrintButton.tsx (CREATE)
- frontend/src/app/schedule/page.tsx (CREATE)
- frontend/src/app/schedule/print/page.tsx (CREATE)
- frontend/src/lib/print.ts (CREATE)

IMPLEMENTATION REQUIREMENTS:

1. frontend/src/app/schedule/page.tsx:
   - New dedicated schedule view page
   - Week selector with navigation
   - Full calendar grid showing all assignments
   - Filter by person, rotation type
   - Print button in header

2. frontend/src/app/schedule/print/page.tsx:
   - Print-optimized layout (no navigation)
   - Week range in header
   - Compact table format
   - @media print CSS for proper printing
   - Auto-trigger print dialog on load (optional)

3. frontend/src/components/PrintSchedule.tsx:
   - Printable schedule component
   - Props: weekStart, weekEnd, assignments
   - Clean table layout for printing
   - Includes legend for rotation types

4. frontend/src/components/PrintButton.tsx:
   - Button that opens print view in new tab
   - Or triggers window.print() for current page
   - Loading state while preparing

5. frontend/src/lib/print.ts:
   ```typescript
   export function openPrintView(weekStart: Date): void
   export function formatScheduleForPrint(assignments: Assignment[]): PrintData
   ```

Print styles:
```css
@media print {
  .no-print { display: none; }
  .print-only { display: block; }
  body { font-size: 10pt; }
}
```

DO NOT modify existing pages except to add navigation links.
Commit with prefix: [Opus-Print]
```

---

## Terminal 2: Opus-Notifications

```
You are Opus-Notifications. Your task is to add an in-app notification system.

STRICT FILE OWNERSHIP - Only modify files in these paths:
- frontend/src/components/NotificationBell.tsx (CREATE)
- frontend/src/components/NotificationPanel.tsx (CREATE)
- frontend/src/contexts/NotificationContext.tsx (CREATE)
- frontend/src/lib/notifications.ts (CREATE)
- frontend/src/components/Navigation.tsx (UPDATE - add bell icon)
- backend/app/api/routes/notifications.py (CREATE)
- backend/app/models/notification.py (CREATE)

IMPLEMENTATION REQUIREMENTS:

1. backend/app/models/notification.py:
   ```python
   class Notification(Base):
       id: int
       user_id: int
       type: str  # 'schedule_change', 'absence_approved', 'compliance_alert'
       title: str
       message: str
       read: bool = False
       created_at: datetime
   ```

2. backend/app/api/routes/notifications.py:
   - GET /notifications - get user's notifications
   - PUT /notifications/{id}/read - mark as read
   - PUT /notifications/read-all - mark all as read
   - DELETE /notifications/{id} - delete notification

3. frontend/src/contexts/NotificationContext.tsx:
   - Fetch notifications on mount
   - Poll for new notifications every 30 seconds
   - Provide unread count
   - Methods: markAsRead, markAllRead, deleteNotification

4. frontend/src/components/NotificationBell.tsx:
   - Bell icon with unread badge count
   - Click opens NotificationPanel
   - Animated badge when new notifications

5. frontend/src/components/NotificationPanel.tsx:
   - Dropdown panel with notification list
   - Mark as read on click
   - "Mark all read" button
   - Empty state when no notifications
   - Timestamp formatting (e.g., "2 hours ago")

6. Update Navigation.tsx:
   - Add NotificationBell next to UserMenu

DO NOT modify other components or pages.
Commit with prefix: [Opus-Notifications]
```

---

## Terminal 3: Opus-Calendar-Sync

```
You are Opus-Calendar-Sync. Your task is to add calendar export (iCal) functionality.

STRICT FILE OWNERSHIP - Only modify files in these paths:
- frontend/src/lib/ical.ts (CREATE)
- frontend/src/components/CalendarExport.tsx (CREATE)
- frontend/src/app/settings/page.tsx (UPDATE - add calendar section)
- backend/app/api/routes/calendar.py (CREATE)

IMPLEMENTATION REQUIREMENTS:

1. frontend/src/lib/ical.ts:
   ```typescript
   export function generateICalEvent(assignment: Assignment): string
   export function generateICalFeed(assignments: Assignment[]): string
   export function downloadICalFile(assignments: Assignment[], filename: string): void
   ```

   iCal format:
   ```
   BEGIN:VCALENDAR
   VERSION:2.0
   PRODID:-//Residency Scheduler//EN
   BEGIN:VEVENT
   UID:assignment-123@residency-scheduler
   DTSTART:20240115T070000
   DTEND:20240115T190000
   SUMMARY:Clinic - Dr. Smith
   DESCRIPTION:Rotation: Morning Clinic
   END:VEVENT
   END:VCALENDAR
   ```

2. frontend/src/components/CalendarExport.tsx:
   - Export button with options:
     - "Export This Week" - current week's schedule
     - "Export This Month" - current month
     - "Subscribe URL" - show copyable calendar feed URL
   - Downloads .ics file

3. backend/app/api/routes/calendar.py:
   - GET /calendar/feed/{user_id} - returns iCal feed for user
   - GET /calendar/export - returns iCal for date range
   - Accept query params: start_date, end_date, person_id

4. Update settings/page.tsx:
   - Add "Calendar Integration" section
   - Show personal calendar feed URL
   - Copy to clipboard button
   - Instructions for adding to Google Calendar, Outlook, etc.

DO NOT modify scheduling logic or other pages.
Commit with prefix: [Opus-Calendar]
```

---

## Terminal 4: Opus-Dark-Mode

```
You are Opus-Dark-Mode. Your task is to add dark mode theme support.

STRICT FILE OWNERSHIP - Only modify files in these paths:
- frontend/src/contexts/ThemeContext.tsx (CREATE)
- frontend/src/components/ThemeToggle.tsx (CREATE)
- frontend/src/app/globals.css (UPDATE - add dark mode styles)
- frontend/src/app/layout.tsx (UPDATE - add ThemeProvider)
- frontend/src/components/Navigation.tsx (UPDATE - add theme toggle)
- frontend/tailwind.config.js (UPDATE - enable dark mode)

IMPLEMENTATION REQUIREMENTS:

1. frontend/tailwind.config.js:
   ```javascript
   module.exports = {
     darkMode: 'class',
     // ... rest of config
   }
   ```

2. frontend/src/contexts/ThemeContext.tsx:
   ```typescript
   interface ThemeContextType {
     theme: 'light' | 'dark' | 'system'
     setTheme: (theme: 'light' | 'dark' | 'system') => void
     resolvedTheme: 'light' | 'dark'
   }
   ```
   - Persist preference to localStorage
   - Respect system preference when 'system' selected
   - Apply 'dark' class to html element

3. frontend/src/components/ThemeToggle.tsx:
   - Sun/Moon icon button
   - Dropdown with Light/Dark/System options
   - Smooth icon transition animation

4. Update globals.css:
   ```css
   :root {
     --background: #ffffff;
     --foreground: #111827;
     /* ... light mode variables */
   }

   .dark {
     --background: #111827;
     --foreground: #f9fafb;
     /* ... dark mode variables */
   }
   ```

5. Update layout.tsx:
   - Wrap with ThemeProvider
   - Add suppressHydrationWarning to html tag

6. Update Navigation.tsx:
   - Add ThemeToggle next to NotificationBell/UserMenu

Key color mappings for dark mode:
- bg-white → dark:bg-gray-800
- bg-gray-50 → dark:bg-gray-900
- text-gray-900 → dark:text-white
- border-gray-200 → dark:border-gray-700

DO NOT modify component logic, only styling.
Commit with prefix: [Opus-DarkMode]
```

---

## Terminal 5: Opus-Keyboard-Shortcuts

```
You are Opus-Keyboard-Shortcuts. Your task is to add keyboard navigation and shortcuts.

STRICT FILE OWNERSHIP - Only modify files in these paths:
- frontend/src/hooks/useKeyboardShortcuts.ts (CREATE)
- frontend/src/components/KeyboardShortcutsModal.tsx (CREATE)
- frontend/src/components/CommandPalette.tsx (CREATE)
- frontend/src/app/layout.tsx (UPDATE - add global shortcuts)

IMPLEMENTATION REQUIREMENTS:

1. frontend/src/hooks/useKeyboardShortcuts.ts:
   ```typescript
   interface Shortcut {
     key: string
     ctrl?: boolean
     shift?: boolean
     alt?: boolean
     description: string
     action: () => void
   }

   export function useKeyboardShortcuts(shortcuts: Shortcut[]): void
   export function useGlobalShortcuts(): void
   ```

2. Global shortcuts to implement:
   - `?` or `Ctrl+/` - Show keyboard shortcuts help
   - `Ctrl+K` or `Cmd+K` - Open command palette
   - `g then h` - Go to home/dashboard
   - `g then p` - Go to people
   - `g then t` - Go to templates
   - `g then a` - Go to absences
   - `g then c` - Go to compliance
   - `g then s` - Go to settings
   - `Escape` - Close any open modal

3. frontend/src/components/CommandPalette.tsx:
   - Search input at top
   - List of available commands/navigation
   - Filter as you type
   - Arrow keys to navigate, Enter to select
   - Recent commands section
   - Fuzzy search matching

4. frontend/src/components/KeyboardShortcutsModal.tsx:
   - Modal showing all available shortcuts
   - Grouped by category (Navigation, Actions, etc.)
   - Clean table layout
   - Shows key combinations with styled kbd elements

5. Update layout.tsx:
   - Add useGlobalShortcuts hook
   - Render CommandPalette and KeyboardShortcutsModal

Styled kbd element:
```tsx
<kbd className="px-2 py-1 bg-gray-100 dark:bg-gray-700 rounded text-sm font-mono">
  Ctrl
</kbd>
```

DO NOT modify page components or backend.
Commit with prefix: [Opus-Keyboard]
```

---

## Merge Order

After all 5 complete:
1. Opus-Dark-Mode (foundational styling)
2. Opus-Keyboard-Shortcuts (global hooks)
3. Opus-Notifications (adds to nav)
4. Opus-Calendar-Sync (uses existing data)
5. Opus-Print-Schedule (new page)

## Conflict Prevention

Each Opus has strict file ownership. Shared files:
- `Navigation.tsx` - Multiple update it:
  - Dark-Mode: adds ThemeToggle
  - Notifications: adds NotificationBell
  - Resolution: Keep both additions, place in order: ThemeToggle, NotificationBell, UserMenu
- `layout.tsx` - Multiple update it:
  - Dark-Mode: adds ThemeProvider
  - Keyboard: adds useGlobalShortcuts
  - Resolution: Keep both, ThemeProvider wraps outer, shortcuts inside

---

## Expected Deliverables

| Opus Instance | New Files | Updated Files |
|--------------|-----------|---------------|
| Print-Schedule | 5 files | 0 files |
| Notifications | 5 files | 2 files |
| Calendar-Sync | 3 files | 2 files |
| Dark-Mode | 2 files | 4 files |
| Keyboard-Shortcuts | 3 files | 1 file |

**Total: 18 new files, 9 updated files**

These are bonus features - the app is already production ready!
