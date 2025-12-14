# Opus Round 4 - 5 Parallel Instances (UPDATED)

Auth is COMPLETE (PRs #22, #23, #24)! Here are 5 new tasks focusing on remaining features.

Run these 5 prompts in separate terminals simultaneously.

---

## Terminal 1: Opus-Protected-Routes

```
You are Opus-Protected-Routes. Your task is to add route protection and authorization throughout the app.

STRICT FILE OWNERSHIP - Only modify files in these paths:
- frontend/src/components/ProtectedRoute.tsx (CREATE)
- frontend/src/app/page.tsx (UPDATE - wrap with protection)
- frontend/src/app/people/page.tsx (UPDATE - wrap with protection)
- frontend/src/app/templates/page.tsx (UPDATE - wrap with protection)
- frontend/src/app/compliance/page.tsx (UPDATE - wrap with protection)
- frontend/src/app/settings/page.tsx (UPDATE - add admin check)
- backend/app/api/routes/people.py (UPDATE - add auth dependencies)
- backend/app/api/routes/schedule.py (UPDATE - add auth dependencies)

IMPLEMENTATION REQUIREMENTS:

1. frontend/src/components/ProtectedRoute.tsx:
   ```typescript
   interface ProtectedRouteProps {
     children: React.ReactNode
     requireAdmin?: boolean
   }
   ```
   - Check isAuthenticated from useAuth()
   - If not authenticated, redirect to /login
   - If requireAdmin and user.role !== 'admin', show forbidden message
   - Show loading spinner while checking

2. Update all main pages to use ProtectedRoute:
   - Wrap page content in <ProtectedRoute>
   - Settings page should use <ProtectedRoute requireAdmin>

3. Backend: Add auth to sensitive endpoints:
   - POST/PUT/DELETE routes should require get_current_active_user
   - GET routes can remain public for now (read-only)
   - Import from app.core.security

Example backend update:
```python
from app.core.security import get_current_active_user
from app.models.user import User

@router.post("/", response_model=PersonRead)
async def create_person(
    person_in: PersonCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
```

DO NOT modify auth files or create new pages.
Commit with prefix: [Opus-Protected]
```

---

## Terminal 2: Opus-Absence-Page

```
You are Opus-Absence-Page. Your task is to create the Absences management page.

STRICT FILE OWNERSHIP - Only modify files in these paths:
- frontend/src/app/absences/page.tsx (CREATE)
- frontend/src/components/AbsenceCalendar.tsx (CREATE)
- frontend/src/components/AbsenceList.tsx (CREATE)
- frontend/src/lib/hooks.ts (UPDATE - add absence hooks ONLY)

IMPLEMENTATION REQUIREMENTS:

1. frontend/src/app/absences/page.tsx:
   - Page header "Absence Management"
   - Toggle between Calendar and List view
   - Filter dropdown: All, Vacation, Sick, Conference, Personal
   - "Add Absence" button (uses existing AddAbsenceModal)
   - Use React Query for data fetching

2. frontend/src/components/AbsenceCalendar.tsx:
   - Monthly calendar grid view
   - Color-coded absence types:
     - vacation: bg-green-100 border-green-500
     - sick: bg-red-100 border-red-500
     - conference: bg-blue-100 border-blue-500
     - personal: bg-purple-100 border-purple-500
   - Show person initials on absence day
   - Click absence to open edit modal
   - Navigation: < Month Year >

3. frontend/src/components/AbsenceList.tsx:
   - Table view with columns: Person, Type, Start Date, End Date, Notes, Actions
   - Sort by start date (upcoming first)
   - Edit and Delete action buttons
   - Use existing table styling from People page

4. Add to hooks.ts (append only, don't modify existing hooks):
   ```typescript
   export function useAbsences(filters?: { type?: string; personId?: number }) {
     return useQuery({
       queryKey: ['absences', filters],
       queryFn: () => api.get('/absences', { params: filters }).then(r => r.data),
     })
   }

   export function useDeleteAbsence() {
     const queryClient = useQueryClient()
     return useMutation({
       mutationFn: (id: number) => api.delete(`/absences/${id}`),
       onSuccess: () => queryClient.invalidateQueries({ queryKey: ['absences'] }),
     })
   }
   ```

DO NOT modify Navigation.tsx or backend files.
Commit with prefix: [Opus-Absences]
```

---

## Terminal 3: Opus-Dashboard

```
You are Opus-Dashboard. Your task is to create an analytics dashboard as the home page.

STRICT FILE OWNERSHIP - Only modify files in these paths:
- frontend/src/app/page.tsx (UPDATE - replace current home with dashboard)
- frontend/src/components/dashboard/ScheduleSummary.tsx (CREATE)
- frontend/src/components/dashboard/ComplianceAlert.tsx (CREATE)
- frontend/src/components/dashboard/UpcomingAbsences.tsx (CREATE)
- frontend/src/components/dashboard/QuickActions.tsx (CREATE)

IMPLEMENTATION REQUIREMENTS:

1. Update frontend/src/app/page.tsx:
   - Replace schedule calendar with dashboard layout
   - Grid layout: 2 columns on desktop, 1 on mobile
   - Header: "Dashboard" with current date
   - Import and arrange the 4 dashboard widgets

2. frontend/src/components/dashboard/ScheduleSummary.tsx:
   - Card showing "This Week's Schedule"
   - Count: X residents scheduled, Y attendings
   - Link to generate schedule if none exists
   - Show coverage status (fully staffed / gaps)

3. frontend/src/components/dashboard/ComplianceAlert.tsx:
   - Card showing "Compliance Status"
   - If violations: Red alert with count
   - If clean: Green "All Clear" message
   - Link to /compliance page
   - Use existing compliance API

4. frontend/src/components/dashboard/UpcomingAbsences.tsx:
   - Card showing "Upcoming Absences (7 days)"
   - List up to 5 upcoming absences
   - Show person name, dates, type badge
   - "View All" link to /absences

5. frontend/src/components/dashboard/QuickActions.tsx:
   - Card with action buttons:
     - "Generate Schedule" (opens GenerateScheduleDialog)
     - "Add Person" (links to /people)
     - "View Templates" (links to /templates)
   - 2x2 grid of buttons with icons

Use Tailwind card styling:
```typescript
<div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
```

DO NOT create new API endpoints or modify backend.
Commit with prefix: [Opus-Dashboard]
```

---

## Terminal 4: Opus-Navigation-Update

```
You are Opus-Navigation-Update. Your task is to enhance navigation and add the Absences link.

STRICT FILE OWNERSHIP - Only modify files in these paths:
- frontend/src/components/Navigation.tsx (UPDATE)
- frontend/src/components/MobileNav.tsx (CREATE)
- frontend/src/components/UserMenu.tsx (CREATE)

IMPLEMENTATION REQUIREMENTS:

1. Update frontend/src/components/Navigation.tsx:
   - Add "Absences" link between "People" and "Compliance"
   - Extract user menu to separate component
   - Add mobile hamburger menu
   - Highlight current route
   - Import and use MobileNav and UserMenu components

2. frontend/src/components/MobileNav.tsx:
   - Hamburger menu icon (shown on mobile only)
   - Slide-out drawer with nav links
   - Close on link click or overlay click
   - Same links as desktop nav
   - Use Tailwind responsive: hidden md:flex / flex md:hidden

3. frontend/src/components/UserMenu.tsx:
   - User avatar/initial circle
   - Dropdown menu on click:
     - User email display
     - Role badge (Admin/User)
     - Settings link
     - Logout button
   - Use useAuth() for user data and logout

Navigation links should be:
- Dashboard (/)
- People (/people)
- Templates (/templates)
- Absences (/absences)  <-- NEW
- Compliance (/compliance)
- Settings (/settings) - only if admin

Use active link styling:
```typescript
className={pathname === href ? 'text-blue-600 font-medium' : 'text-gray-600 hover:text-gray-900'}
```

DO NOT modify any page files or backend.
Commit with prefix: [Opus-Navigation]
```

---

## Terminal 5: Opus-API-Error-Handling

```
You are Opus-API-Error-Handling. Your task is to add comprehensive error handling and loading states.

STRICT FILE OWNERSHIP - Only modify files in these paths:
- frontend/src/components/ErrorBoundary.tsx (CREATE)
- frontend/src/components/ErrorAlert.tsx (CREATE)
- frontend/src/components/LoadingSpinner.tsx (CREATE)
- frontend/src/lib/api.ts (UPDATE - add error interceptor)
- frontend/src/app/layout.tsx (UPDATE - wrap with ErrorBoundary)

IMPLEMENTATION REQUIREMENTS:

1. frontend/src/components/ErrorBoundary.tsx:
   - React Error Boundary component
   - Catch render errors
   - Display friendly error message
   - "Try Again" button to reset
   - Log errors to console

2. frontend/src/components/ErrorAlert.tsx:
   - Reusable error display component
   - Props: message, onRetry?, onDismiss?
   - Red alert styling with X icon
   - Optional retry button

3. frontend/src/components/LoadingSpinner.tsx:
   - Reusable spinner component
   - Props: size ('sm' | 'md' | 'lg'), text?
   - Centered spinning animation
   - Optional loading text below

4. Update frontend/src/lib/api.ts:
   - Add response interceptor for errors
   - Handle 401: Clear auth, redirect to login
   - Handle 403: Show forbidden message
   - Handle 500: Show server error message
   - Transform error responses to consistent format

```typescript
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Clear token and redirect
      localStorage.removeItem('token')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)
```

5. Update layout.tsx:
   - Wrap children with ErrorBoundary
   - Keep existing Providers wrapper

DO NOT modify page components or backend.
Commit with prefix: [Opus-Errors]
```

---

## Merge Order

After all 5 complete:
1. Opus-API-Error-Handling (no dependencies, foundational)
2. Opus-Navigation-Update (independent)
3. Opus-Absence-Page (needs navigation link but can merge independently)
4. Opus-Dashboard (replaces home page)
5. Opus-Protected-Routes (add protection last to avoid blocking testing)

## Conflict Prevention

Each Opus has strict file ownership. Shared files:
- `hooks.ts` - Only Opus-Absences adds hooks (append only)
- `api.ts` - Only Opus-Errors modifies
- `layout.tsx` - Only Opus-Errors wraps with ErrorBoundary
- `page.tsx` (home) - Only Opus-Dashboard modifies
- `Navigation.tsx` - Only Opus-Navigation modifies

If conflicts in hooks.ts: Merge all hook additions.

---

## Expected Deliverables

| Opus Instance | New Files | Updated Files |
|--------------|-----------|---------------|
| Protected-Routes | 1 file | 6 files |
| Absence-Page | 3 files | 1 file |
| Dashboard | 4 files | 1 file |
| Navigation-Update | 2 files | 1 file |
| API-Error-Handling | 3 files | 2 files |

**Total: 13 new files, 11 updated files**

After this round, project should be at ~95% complete!
