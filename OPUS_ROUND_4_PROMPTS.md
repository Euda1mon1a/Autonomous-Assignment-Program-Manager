# Opus Round 4 - 5 Parallel Instances

Run these 5 prompts in separate terminals simultaneously.

---

## Terminal 1: Opus-Auth-Backend

```
You are Opus-Auth-Backend. Your task is to implement JWT authentication for the backend.

STRICT FILE OWNERSHIP - Only modify files in these paths:
- backend/app/core/auth.py (CREATE)
- backend/app/core/security.py (CREATE)
- backend/app/models/user.py (CREATE)
- backend/app/schemas/user.py (CREATE)
- backend/app/schemas/auth.py (CREATE)
- backend/app/api/routes/auth.py (CREATE)
- backend/app/api/routes/__init__.py (UPDATE - add auth router)
- backend/app/core/config.py (UPDATE - add JWT settings)

IMPLEMENTATION REQUIREMENTS:

1. backend/app/models/user.py:
   - User model with: id, email, hashed_password, full_name, is_active, is_superuser, created_at
   - Link to Person model via optional person_id foreign key

2. backend/app/core/security.py:
   - Password hashing with passlib[bcrypt]
   - JWT token creation/verification with python-jose[cryptography]
   - get_password_hash(), verify_password()
   - create_access_token(), decode_access_token()

3. backend/app/core/auth.py:
   - get_current_user() dependency
   - get_current_active_user() dependency
   - require_admin() dependency

4. backend/app/schemas/auth.py:
   - Token, TokenData schemas
   - LoginRequest schema

5. backend/app/schemas/user.py:
   - UserCreate, UserUpdate, UserRead, UserInDB schemas

6. backend/app/api/routes/auth.py:
   - POST /auth/login - returns JWT token
   - POST /auth/register - create user (admin only in production)
   - GET /auth/me - get current user
   - POST /auth/refresh - refresh token

7. Update config.py:
   - JWT_SECRET_KEY, JWT_ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES

DO NOT modify any frontend files.
Commit with prefix: [Opus-Auth-Backend]
```

---

## Terminal 2: Opus-Auth-Frontend

```
You are Opus-Auth-Frontend. Your task is to implement authentication UI and context.

STRICT FILE OWNERSHIP - Only modify files in these paths:
- frontend/src/contexts/AuthContext.tsx (CREATE)
- frontend/src/components/LoginForm.tsx (CREATE)
- frontend/src/components/ProtectedRoute.tsx (CREATE)
- frontend/src/app/login/page.tsx (CREATE)
- frontend/src/lib/api.ts (UPDATE - add auth header interceptor)
- frontend/src/app/providers.tsx (UPDATE - wrap with AuthProvider)
- frontend/src/components/Navigation.tsx (UPDATE - add login/logout button)

IMPLEMENTATION REQUIREMENTS:

1. frontend/src/contexts/AuthContext.tsx:
   ```typescript
   interface AuthContextType {
     user: User | null
     token: string | null
     isLoading: boolean
     isAuthenticated: boolean
     login: (email: string, password: string) => Promise<void>
     logout: () => void
     register: (email: string, password: string, fullName: string) => Promise<void>
   }
   ```
   - Store token in localStorage
   - Auto-fetch user on mount if token exists
   - Expose useAuth() hook

2. frontend/src/components/LoginForm.tsx:
   - Email/password form with validation
   - Error display for invalid credentials
   - Loading state during submission
   - Use Tailwind classes consistent with existing components

3. frontend/src/components/ProtectedRoute.tsx:
   - Wrapper that redirects to /login if not authenticated
   - Shows loading spinner while checking auth

4. frontend/src/app/login/page.tsx:
   - Login page with LoginForm
   - Redirect to / if already authenticated
   - "Residency Scheduler" branding

5. Update frontend/src/lib/api.ts:
   - Add Authorization header to all requests if token exists
   - Handle 401 responses by clearing auth state

6. Update Navigation.tsx:
   - Show user email and logout button when authenticated
   - Show login button when not authenticated

DO NOT modify any backend files.
Commit with prefix: [Opus-Auth-Frontend]
```

---

## Terminal 3: Opus-Settings-Page

```
You are Opus-Settings-Page. Your task is to implement the Settings page functionality.

STRICT FILE OWNERSHIP - Only modify files in these paths:
- frontend/src/app/settings/page.tsx (UPDATE)
- frontend/src/components/SettingsForm.tsx (CREATE)
- frontend/src/components/UserManagement.tsx (CREATE)
- frontend/src/lib/hooks.ts (UPDATE - add settings hooks)
- backend/app/api/routes/settings.py (CREATE)
- backend/app/schemas/settings.py (CREATE)

IMPLEMENTATION REQUIREMENTS:

1. frontend/src/app/settings/page.tsx:
   - Replace placeholder with functional settings page
   - Tabs: "General", "Scheduling", "Users" (if admin)
   - General: App name display, timezone setting
   - Scheduling: Default shift times, max hours per week
   - Users: List users, invite new users (admin only)

2. frontend/src/components/SettingsForm.tsx:
   - Form for scheduling settings:
     - Default AM start time (e.g., 07:00)
     - Default PM start time (e.g., 13:00)
     - Max weekly hours (default 80 for ACGME)
     - Max consecutive duty hours (default 24)
   - Save button with loading state

3. frontend/src/components/UserManagement.tsx:
   - Table of users with email, role, status
   - Invite user button (opens modal)
   - Deactivate user action

4. backend/app/api/routes/settings.py:
   - GET /settings - get current settings
   - PUT /settings - update settings (admin only)
   - Settings stored in database or config

5. Update hooks.ts:
   - useSettings() - fetch settings
   - useUpdateSettings() - mutation to update

Commit with prefix: [Opus-Settings]
```

---

## Terminal 4: Opus-Absence-Management

```
You are Opus-Absence-Management. Your task is to implement full absence/vacation management.

STRICT FILE OWNERSHIP - Only modify files in these paths:
- frontend/src/app/absences/page.tsx (CREATE)
- frontend/src/components/AbsenceCalendar.tsx (CREATE)
- frontend/src/components/AddAbsenceModal.tsx (UPDATE - enhance)
- frontend/src/lib/hooks.ts (UPDATE - add absence hooks)
- backend/app/api/routes/absences.py (UPDATE - enhance)
- frontend/src/components/Navigation.tsx (UPDATE - add Absences link)

IMPLEMENTATION REQUIREMENTS:

1. frontend/src/app/absences/page.tsx:
   - New page for managing absences
   - Calendar view showing all absences color-coded by type
   - Filter by person, type, date range
   - Add absence button opens AddAbsenceModal
   - List view toggle showing upcoming absences

2. frontend/src/components/AbsenceCalendar.tsx:
   - Monthly calendar view
   - Color-coded absence types:
     - vacation: green
     - sick: red
     - conference: blue
     - personal: purple
   - Click on absence to edit/delete
   - Click on empty day to add absence

3. Enhance AddAbsenceModal.tsx:
   - Add absence type dropdown (vacation, sick, conference, personal)
   - Add notes field
   - Date range picker (start_date, end_date)
   - Person selector with search

4. Add hooks to hooks.ts:
   - useAbsences(filters?) - fetch absences with optional filters
   - useCreateAbsence() - mutation
   - useUpdateAbsence() - mutation
   - useDeleteAbsence() - mutation

5. Update Navigation.tsx:
   - Add "Absences" link between "People" and "Compliance"

6. Enhance backend/app/api/routes/absences.py:
   - GET /absences - with filters (person_id, type, start_date, end_date)
   - Ensure all CRUD operations work

Commit with prefix: [Opus-Absences]
```

---

## Terminal 5: Opus-Dashboard-Analytics

```
You are Opus-Dashboard-Analytics. Your task is to add analytics dashboard widgets.

STRICT FILE OWNERSHIP - Only modify files in these paths:
- frontend/src/app/dashboard/page.tsx (CREATE)
- frontend/src/components/analytics/WorkloadChart.tsx (CREATE)
- frontend/src/components/analytics/ComplianceWidget.tsx (CREATE)
- frontend/src/components/analytics/UpcomingAbsences.tsx (CREATE)
- frontend/src/components/analytics/RecentActivity.tsx (CREATE)
- frontend/src/lib/hooks.ts (UPDATE - add analytics hooks)
- backend/app/api/routes/analytics.py (CREATE)
- backend/app/schemas/analytics.py (CREATE)

IMPLEMENTATION REQUIREMENTS:

1. frontend/src/app/dashboard/page.tsx:
   - Dashboard overview page
   - Grid layout with widgets:
     - Workload distribution chart (hours per resident this week)
     - Compliance status summary
     - Upcoming absences (next 7 days)
     - Recent activity log (last 10 changes)
   - Date range selector for analytics period

2. frontend/src/components/analytics/WorkloadChart.tsx:
   - Bar chart showing hours per resident
   - Use simple CSS/div-based chart (no external lib)
   - Color code: green (<60hrs), yellow (60-70), red (>70)
   - Show ACGME 80-hour limit line

3. frontend/src/components/analytics/ComplianceWidget.tsx:
   - Summary card showing:
     - Total violations this period
     - Breakdown by violation type
     - Trend (better/worse than last period)
   - Click to navigate to /compliance

4. frontend/src/components/analytics/UpcomingAbsences.tsx:
   - List of absences in next 7 days
   - Show person name, dates, type
   - Warning icon if coverage needed

5. frontend/src/components/analytics/RecentActivity.tsx:
   - Timeline of recent changes:
     - Assignment created/updated
     - Absence added
     - Schedule generated
   - Show timestamp and user who made change

6. backend/app/api/routes/analytics.py:
   - GET /analytics/workload - hours per resident
   - GET /analytics/compliance-summary - violation counts
   - GET /analytics/activity - recent activity log

7. Add hooks:
   - useWorkloadAnalytics(startDate, endDate)
   - useComplianceSummary(startDate, endDate)
   - useRecentActivity(limit)

Commit with prefix: [Opus-Analytics]
```

---

## Merge Order

After all 5 complete:
1. Opus-Auth-Backend (no dependencies)
2. Opus-Auth-Frontend (depends on backend auth API)
3. Opus-Settings-Page (may use auth for admin check)
4. Opus-Absence-Management (may use auth)
5. Opus-Dashboard-Analytics (may use auth, needs all data)

## Conflict Prevention

Each Opus has strict file ownership. The only shared files are:
- `hooks.ts` - Each Opus adds different hooks (append only)
- `Navigation.tsx` - Opus-Absences adds one link, Opus-Auth-Frontend adds login button

If conflicts occur:
- hooks.ts: Merge all hook additions
- Navigation.tsx: Keep all additions from both

---

## Expected Deliverables

| Opus Instance | New Files | Updated Files |
|--------------|-----------|---------------|
| Auth-Backend | 6 files | 2 files |
| Auth-Frontend | 4 files | 3 files |
| Settings-Page | 4 files | 2 files |
| Absence-Management | 3 files | 3 files |
| Dashboard-Analytics | 7 files | 1 file |

**Total: 24 new files, 11 updated files**
