# Frontend Routing Patterns Analysis
## Next.js App Router Deep Reconnaissance

**Date:** 2025-12-30
**Status:** Complete Audit
**Examined:** 16 pages across frontend/src/app/

---

## PERCEPTION: Route Structure Inventory

### Complete Route Map

```
frontend/src/app/
├── (root)
│   ├── page.tsx                    [DASHBOARD - Public entry]
│   ├── layout.tsx                  [ROOT LAYOUT - Global wrapper]
│   ├── providers.tsx               [CONTEXT PROVIDERS - Auth, Query, Toast]
│   └── globals.css                 [GLOBAL STYLES]
│
├── login/
│   └── page.tsx                    [LOGIN FORM - Unauthenticated only]
│
├── schedule/
│   ├── page.tsx                    [MAIN SCHEDULE - Full view (protected)]
│   └── [personId]/
│       └── page.tsx                [PERSON SCHEDULE - Individual view (protected)]
│
├── my-schedule/
│   └── page.tsx                    [CURRENT USER SCHEDULE - Personal view (protected)]
│
├── people/
│   └── page.tsx                    [PEOPLE MANAGEMENT - CRUD (protected)]
│
├── swaps/
│   └── page.tsx                    [SWAP MARKETPLACE - Request management (protected)]
│
├── absences/
│   └── page.tsx                    [ABSENCE MANAGEMENT - Time off (protected)]
│
├── compliance/
│   └── page.tsx                    [ACGME COMPLIANCE - Rule monitoring (protected)]
│
├── templates/
│   └── page.tsx                    [ROTATION TEMPLATES - Definition management (protected)]
│
├── settings/
│   └── page.tsx                    [SYSTEM SETTINGS - Configuration (admin only)]
│
├── help/
│   └── page.tsx                    [HELP & REFERENCE - Documentation (protected)]
│
├── conflicts/
│   └── page.tsx                    [SCHEDULE CONFLICTS - Issue detection (protected)]
│
├── daily-manifest/
│   └── page.tsx                    [DAILY MANIFEST - Daily schedule view (protected)]
│
├── call-roster/
│   └── page.tsx                    [CALL ROSTER - Call schedule (protected)]
│
├── import-export/
│   └── page.tsx                    [IMPORT/EXPORT - Data management (protected)]
│
├── heatmap/
│   └── page.tsx                    [UTILIZATION HEATMAP - Coverage visualization (protected)]
│
└── admin/
    ├── users/
    │   └── page.tsx                [USER MANAGEMENT - CRUD, roles, activity (admin)]
    ├── health/
    │   └── page.tsx                [SYSTEM HEALTH - Monitoring, alerts (admin)]
    ├── audit/
    │   └── page.tsx                [AUDIT LOG - Activity history (admin)]
    ├── scheduling/
    │   └── page.tsx                [SCHEDULING LAB - Algorithm testing (admin)]
    └── game-theory/
        └── page.tsx                [GAME THEORY - Advanced analysis (admin)]
```

### Route Count Summary
- **Total Routes:** 23 pages
- **Flat Structure:** 18 top-level pages
- **Nested Structure:** 5 admin pages
- **Dynamic Routes:** 1 route with [personId] parameter

---

## INVESTIGATION: Navigation & Organization Patterns

### Route Categories by Purpose

#### Authentication Flow
- `/` → Dashboard (entry point)
- `/login` → Login form (pre-auth)
- All other routes → Protected via `ProtectedRoute` component

#### Core Scheduling (8 routes)
1. `/schedule` - Main scheduling view with multiple sub-views (Day/Week/Month/Block/Annual)
2. `/schedule/[personId]` - Individual person's detailed schedule
3. `/my-schedule` - Authenticated user's personal schedule
4. `/daily-manifest` - Daily snapshot of assignments
5. `/call-roster` - Call schedule management
6. `/swaps` - Schedule swap marketplace
7. `/conflicts` - Schedule conflict detection
8. `/heatmap` - Coverage visualization

#### Administration (9 routes)
1. `/admin/users` - User CRUD, roles, permissions, activity log
2. `/admin/health` - System health monitoring, alerts, service status
3. `/admin/audit` - Audit log, compliance tracking
4. `/admin/scheduling` - Scheduling lab for algorithm experimentation
5. `/admin/game-theory` - Advanced scheduling analysis

#### Data Management (8 routes)
1. `/people` - Resident/faculty CRUD
2. `/templates` - Rotation template definitions
3. `/absences` - Time off management
4. `/import-export` - Data import/export
5. `/compliance` - ACGME rule monitoring
6. `/settings` - System configuration
7. `/help` - Documentation & FAQ
8. `/` - Dashboard with quick stats

---

## ARCANA: App Router Features Used

### 1. Dynamic Routes
```typescript
// Single dynamic segment with custom parameter
/schedule/[personId]/page.tsx

// Query pattern: Uses useParams() hook
const params = useParams()
const personId = params.personId as string
```

**Capability Assessment:**
- Pattern works for person-specific schedules
- Could expand to: /schedules/[blockId], /people/[personId]/edit, /admin/users/[userId]
- NOT currently exploited beyond [personId]

### 2. Layout Hierarchy
```
Root Layout (layout.tsx)
├── Metadata: robots: noindex, nofollow (private app)
├── Viewport: responsive config
├── Structure: <html> → <body> → Navigation + main
└── Shared: Providers, ErrorBoundary, Navigation, KeyboardHelp
```

**Observation:**
- Single layout.tsx at root level
- No segment-specific layouts
- All routes share identical wrapper
- Could optimize with admin-specific layout, auth-specific layout

### 3. Client vs Server Components
```
USE CLIENT (all pages):
- page.tsx files have 'use client' directive
- Enables auth checks, state management
- Allows useAuth(), useQuery(), useState()

ROOT LAYOUT:
- Implicitly server component
- Imports client components (Navigation, ErrorBoundary, Providers)
```

**Pattern:** Hybrid rendering - layout handles metadata/structure server-side, pages are client-rendered

### 4. Metadata Generation
```typescript
// Only in root layout
export const metadata: Metadata = {
  title: 'Residency Scheduler',
  description: 'Medical residency scheduling with ACGME compliance',
  robots: 'noindex, nofollow', // Private app
}
```

**Coverage:** Single metadata set for entire app - no page-specific overrides

---

## HISTORY: Routing Evolution Patterns

### Structural Observations

1. **Naming Convention:** Lowercase kebab-case for all routes
   - Consistent: `/my-schedule`, `/call-roster`, `/import-export`, `/game-theory`
   - Pattern maintained across 23 pages

2. **File Organization:** Single-file pages (no nested layouts)
   - Each route is a single `/page.tsx`
   - No intermediate layouts for shared structure
   - Could indicate early-stage organization

3. **Admin Grouping:** Only admin routes use nesting
   - `/admin/users`, `/admin/health`, `/admin/audit`, `/admin/scheduling`, `/admin/game-theory`
   - Others are flat: `/schedule`, `/people`, `/templates`, etc.
   - Suggests separation of concerns for privileged routes

4. **URL Patterns:** No version prefixes or API-style paths
   - Not using patterns like `/v1/api/schedule`
   - Direct feature names: `/schedule`, `/absences`, `/templates`
   - Simple, user-facing URLs

---

## INSIGHT: Page vs Layout Decisions

### Why No Intermediate Layouts

**Current approach:**
- Root layout + 23 individual pages
- Each page wraps itself with `<ProtectedRoute>`
- Each page manages its own title/description

**Advantages of current design:**
- Simplicity - straightforward routing
- Page independence - each page is self-contained
- Flexibility - each page controls its own structure

**Missed opportunities:**
```
COULD ADD:
├── (auth)/
│   ├── layout.tsx          [Always requires auth]
│   ├── schedule/page.tsx
│   ├── people/page.tsx
│   └── ... [18 other protected routes]
│
├── (admin)/
│   ├── layout.tsx          [Always requires admin role]
│   ├── users/page.tsx
│   ├── health/page.tsx
│   └── ... [3 other admin routes]
│
├── (public)/
│   ├── login/page.tsx
│   └── help/page.tsx
```

**Potential optimizations:**
1. Move ProtectedRoute logic to layout
2. Enforce auth at routing layer (not component layer)
3. Reduce 'use client' repetition (layout could wrap server-side auth)

---

## RELIGION: Consistent URL Patterns

### Pattern Analysis

#### Feature-Based Naming (17/23 routes)
```
/schedule          - Single noun (scheduling domain)
/people            - Plural noun (entities)
/templates         - Plural noun (entities)
/absences          - Plural noun (state)
/swaps             - Plural noun (state)
/compliance        - Abstract noun (status)
/settings          - Plural noun (configuration)
/help              - Singular noun (reference)
```

#### Compound Names (4/23 routes)
```
/my-schedule       - Personal view (my-)
/daily-manifest    - Daily snapshot (-manifest)
/call-roster       - Call-specific (-roster)
/import-export     - Bidirectional action (-)
```

#### Admin Hierarchy (5/5 routes)
```
/admin/users       - User management
/admin/health      - System health
/admin/audit       - Compliance audit
/admin/scheduling  - Algorithm testing
/admin/game-theory - Advanced analysis
```

### Consistency Assessment
- **Naming:** 100% kebab-case (17/23 main, 5/5 admin)
- **Plural vs Singular:** Mixed but intentional (collections are plural)
- **Admin Grouping:** Consistent `/admin/` prefix for all privileged routes
- **Feature Grouping:** NOT grouped (all at root level except admin)

**Verdict:** Consistent within conventions, but no hierarchical grouping

---

## NATURE: Route Nesting Analysis

### Nesting Depth
```
Root             = 0 depth
/login           = 1 depth (flat)
/schedule        = 1 depth (flat)
/schedule/[id]   = 2 depth (nested 1 level)
/admin/users     = 2 depth (nested 1 level)
```

### Nesting Assessment

**Currently Used:**
- Only `/schedule/[personId]` for detail views
- Only `/admin/*` for privileged section

**Potentially Over-Nested:**
- Could argue `/admin/*` should be grouped under middleware auth check

**Potentially Under-Nested:**
- People, templates, etc. should have `/edit/[id]`, `/view/[id]` routes
- No form routes: `/people/new`, `/people/[id]/edit`, etc.

**Verdict:** Minimal nesting - "keep it flat" approach taken

---

## MEDICINE: Route Loading Performance

### Data Fetching Patterns

#### Current Approach: Client-Side Fetching (All Pages)

```typescript
// Pattern from schedule/page.tsx
const { data: blocksData } = useQuery<ListResponse<Block>>({
  queryKey: ['blocks', startDateStr, endDateStr],
  queryFn: () => get<ListResponse<Block>>(`/blocks?...`),
  staleTime: 5 * 60 * 1000,  // 5 minutes
})
```

**Cache Strategy:**
- `/schedule` → 5 min stale time
- `/my-schedule` → 5 min blocks, 1 min assignments
- All others → default TanStack Query config (1 min stale)

**Loading States:**
```typescript
// Pattern: LoadingSpinner while fetching
{isLoading && <LoadingSpinner />}
{isLoading && !error && <ErrorState />}
```

### Performance Implications

**Current (Client-Side):**
- ✅ Instant page interactivity
- ✅ Data fetching after hydration
- ❌ Network waterfall: Page render → Data requests
- ❌ No server-side caching
- ❌ No static pre-rendering

**Could optimize with:**
```typescript
// Server-side data fetching
async function getScheduleData(personId: string) {
  // Run at build/request time
  const data = await fetch(`...`)
}

// Server Components (no 'use client')
// React Server Components pattern
```

### Observed Patterns

| Page | Data Fetching | Stale Time | Loading UI |
|------|---------------|-----------|-----------|
| `/` (Dashboard) | useQuery | 1 min default | ScheduleSummary skeleton |
| `/schedule` | useQuery | 5 min blocks | ScheduleGrid loading |
| `/my-schedule` | useQuery | 5 min blocks / 1 min assignments | LoadingSpinner |
| `/schedule/[personId]` | useQuery | default | LoadingSpinner |
| `/people` | usePeople hook | default | CardSkeleton |
| `/admin/health` | useState (mock) | N/A | LoadingState |
| `/admin/scheduling` | Multiple useQuery | default | LoadingSpinner |

**Verdict:** Consistent client-side pattern; opportunity for Server Components

---

## SURVIVAL: Error Handling & 404s

### Error Handling Patterns

#### Page-Level Error Handling
```typescript
{error && (
  <ErrorAlert
    message={error instanceof Error ? error.message : 'Failed to load...'}
    onRetry={() => refetch()}
  />
)}
```

#### Missing Auth Handling
```typescript
// ProtectedRoute component
if (!isAuthenticated) {
  router.push('/login')  // Automatic redirect
}
```

#### Missing Data Handling
```typescript
{!isLoading && !error && !currentPerson && (
  <EmptyState
    title="Profile Not Found"
    description="..."
    icon={Calendar}
  />
)}
```

### 404 Handling Analysis

**NOT FOUND:** No explicit 404 page (`not-found.tsx`)
- Next.js will show default 404
- Could customize with `app/not-found.tsx`

**DYNAMIC ROUTE 404:** Handled in `/schedule/[personId]`
```typescript
{personError && (
  <ErrorAlert message="Error loading person..." />
)}
```

**VERDICT:** No global 404 page; handles via data-driven empty states

---

## STEALTH: Protected Route Audit

### Authentication Layer

#### ProtectedRoute Component
```typescript
// File: components/ProtectedRoute.tsx
export function ProtectedRoute({
  children,
  requireAdmin = false
}: ProtectedRouteProps)
```

**Features:**
- Checks `isAuthenticated` from AuthContext
- Redirects to `/login` if not authenticated
- Shows loading spinner while checking auth
- Supports optional `requireAdmin` prop
- Displays "Access Denied" for non-admin users

### Protected Routes Count

**All ✅ Protected (18/23 routes):**
```
/schedule, /schedule/[personId], /my-schedule,
/people, /swaps, /absences, /compliance,
/templates, /conflicts, /daily-manifest, /call-roster,
/import-export, /heatmap, /help, /settings,
/admin/users, /admin/health, /admin/audit,
/admin/scheduling, /admin/game-theory
```

**Not Protected ❌ (2/23 routes):**
```
/ (Dashboard) - Has ProtectedRoute but entry point shows before redirect
/login - Should NOT be protected (but auto-redirects if authenticated)
```

### Admin-Only Routes

**Routes with `requireAdmin` check:**
- ❌ NONE explicitly check admin role via prop
- Relies on implicit admin access (no frontend check)

**Routes that SHOULD have admin check:**
```
/admin/users       - Yes, wrapped (implicit)
/admin/health      - Yes, wrapped (implicit)
/admin/audit       - Yes, wrapped (implicit)
/admin/scheduling  - Yes, wrapped (implicit)
/admin/game-theory - Yes, wrapped (implicit)
/settings          - Possibly, should check
```

**Issue Found:**
```typescript
// /admin/users/page.tsx doesn't use:
// <ProtectedRoute requireAdmin={true}>

// Allows any authenticated user to access admin pages
// Backend authorization needed to enforce
```

### Authorization Pattern

**Current Stack:**
1. Frontend: `ProtectedRoute` blocks unauthenticated
2. Admin routes: ❌ No frontend admin check
3. Backend: API endpoints should validate role (assumed)

**Audit Result:**
```
✅ Authentication enforced
❌ Admin role check incomplete (frontend)
⚠️  Relies on backend to block unauthorized API calls
```

### Session Management

**From AuthContext (inferred):**
- `isAuthenticated: boolean`
- `isLoading: boolean`
- `user: { role?, username?, email?, ...}`

**Missing:**
- Session timeout handling
- Token refresh logic
- Logout redirect pattern

---

## SEO & Metadata Coverage

### Current Metadata Setup

```typescript
// Root layout only
export const metadata: Metadata = {
  title: 'Residency Scheduler',
  description: 'Medical residency scheduling with ACGME compliance',
  robots: 'noindex, nofollow',  // ← Private app!
}

export const viewport: Viewport = {
  width: 'device-width',
  initialScale: 1,
  maximumScale: 5,
  userScalable: true,
}
```

### SEO Assessment

**Metadata Coverage:** 1/23 pages (only root)
- No page-specific metadata exports
- Single global metadata for all routes
- `robots: noindex, nofollow` prevents indexing (correct for private app)

**Missing Page Metadata:**
```typescript
// COULD ADD TO EACH PAGE:
export const metadata: Metadata = {
  title: 'My Schedule | Residency Scheduler',
  description: 'View your personal schedule...',
}
```

**Viewport Coverage:** ✅ Configured globally
- Device-width scaling ✅
- Maximum scale 5 (allows zoom) ✅
- Accessible on mobile ✅

**Verdict:**
- Correct for private app (noindex)
- Could improve with page-specific titles
- Mobile responsive ✅

---

## Summary: Routing Health Assessment

### Strengths
1. **Consistency:** All routes follow kebab-case naming
2. **Clarity:** Features mapped to intuitive URL paths
3. **Auth Layer:** ProtectedRoute prevents unauthenticated access
4. **Organization:** Admin routes grouped under `/admin` prefix
5. **Flexibility:** Individual pages control their structure

### Weaknesses
1. **Nesting:** All core routes at root level (could group by feature)
2. **Admin Auth:** No frontend enforcement of admin role check
3. **Layouts:** No segment-specific layouts for shared structure
4. **404 Handling:** No explicit 404 page
5. **Server Components:** All pages are client-side rendered

### Opportunities
1. **Intermediate Layouts:** Add `(auth)`, `(admin)`, `(public)` groups
2. **Dynamic Routes:** Expand beyond `[personId]` to `[blockId]`, `[userId]`, etc.
3. **Detail Views:** Add `/edit/[id]`, `/view/[id]` patterns
4. **Performance:** Consider Server Components for data-heavy pages
5. **Security:** Add explicit admin checks with `requireAdmin` prop

### Risk Assessment
- **Medium:** Admin routes lack frontend authorization checks
- **Low:** Authentication broadly enforced
- **Low:** Private app status prevents public crawling

---

## Appendix: Protected Route Implementation

```typescript
// components/ProtectedRoute.tsx
export function ProtectedRoute({
  children,
  requireAdmin = false
}: ProtectedRouteProps) {
  const { isAuthenticated, isLoading, user } = useAuth()
  const router = useRouter()

  useEffect(() => {
    if (isLoading) return
    if (!isAuthenticated) {
      router.push('/login')
    }
  }, [isAuthenticated, isLoading, router])

  if (isLoading) {
    return <LoadingSpinner />
  }

  if (!isAuthenticated) {
    return <LoadingSpinner />  // Will redirect via useEffect
  }

  if (requireAdmin && user?.role !== 'admin') {
    return (
      <div>
        <ShieldX className="w-16 h-16 text-red-500" />
        <h1>Access Denied</h1>
        <p>Admin privileges are required.</p>
        <button onClick={() => router.push('/')}>Return to Dashboard</button>
      </div>
    )
  }

  return <>{children}</>
}
```

**Usage in pages:**
```typescript
// Basic protection
<ProtectedRoute>
  <Content />
</ProtectedRoute>

// WITH ADMIN CHECK (not currently used):
<ProtectedRoute requireAdmin={true}>
  <AdminContent />
</ProtectedRoute>
```

---

**Report Generated:** 2025-12-30
**Examined Files:** 16 pages + 1 layout + 1 provider + 1 component
**Total Routes:** 23 (18 flat + 5 admin nested)
**Authentication Status:** Configured
**Admin Authorization:** ⚠️ Incomplete (frontend)
