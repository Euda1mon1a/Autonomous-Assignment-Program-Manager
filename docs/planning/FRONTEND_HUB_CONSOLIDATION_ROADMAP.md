# Frontend Hub Consolidation Roadmap

> **Status:** In Progress
> **Created:** 2026-01-12
> **Last Updated:** 2026-01-12 (Admin Scheduling wiring)
> **Related PRs:** #694 (consolidation map), #695 (RiskBar), #696 (Swap Hub), #697 (PersonSelector), #699 (Proxy Coverage), #700 (Command Center)
> **Source Analysis:** `docs/reviews/2026-01-11-frontend-consolidation-map.md`

---

## Executive Summary

### Vision

Transform scattered frontend pages into a unified **hub-based navigation model** where related functionality is grouped into cohesive hubs with:
- Tab-based views within each hub
- Tier-based permission gating
- Consistent RiskBar indicators
- Reusable feature module patterns

### Gold Standard

**Swap Hub** (`/swaps`) is the reference implementation. All new hubs should follow its patterns for:
- Declarative tab configuration
- Tier-based filtering
- RiskBar integration
- Feature module organization

### Scope

| Category | Count |
|----------|-------|
| Total Hubs | 14 |
| Complete | 1 (Swap Hub) |
| Partial/Exists | 5 (Schedule, People, Call, Import/Export, Admin Scheduling) |
| To Build | 7 |
| Roadmapped | 1 (Learner Hub) |

---

## Tier Model

The permission tier model determines what users can see and do across all hubs.

| Tier | Role | Who | Access Level |
|------|------|-----|--------------|
| **0** | Self-service | Residents, Faculty | **View all**, self-service actions |
| **0.5** | Learner managers | Select faculty (clerkship directors, education leads) | Medical student schedule management |
| **1** | Program operations | Coordinators, Program Directors | Full operational access, approvals, sensitive details |
| **2** | System admin | Developers, Super Admin | Keys to kingdom, user management |

### Transparency Model (Critical)

**Maximum transparency for Tier 0.** The tier system controls EDIT access, not VIEW access.

| Data | Tier 0 View | Tier 1-2 Additional |
|------|-------------|---------------------|
| **All schedules** | ✅ Everyone's assignments | Edit access |
| **All absences** | ✅ Who is away, when, reason (except sick) | Sick leave reasons |
| **Credentials** | ✅ Who can do what procedures | Edit access |
| **FMIT weeks** | ✅ Faculty teaching schedules | Edit access |
| **Pending swaps** | ✅ All swap requests | Approve/deny |
| **Fairness metrics** | ✅ Workload distribution | (preempts complaints) |
| **Compliance dashboard** | ✅ Summary ("we're compliant") | Detailed violation data |
| **Audit trail** | ❌ | ✅ Who changed what |

**Rationale:** Transparency builds trust. Everyone can see schedules, absences (deployment/TDY fine - local system), credentials, and fairness data. Only sensitive details (sick reasons, audit logs, compliance details) are restricted.

### Tier Boundaries (Actions)

**Tier 0 (Green):** View everything (except audit), self-service requests (swap requests, absence requests)

**Tier 0.5 (Special):** Faculty subset with learner management permissions (future Learner Hub)

**Tier 1 (Amber):** Approve/edit operations, see sensitive details (sick reasons, audit trail, compliance details)

**Tier 2 (Red):** System config, role assignment, force overrides, user management

---

## Hub Inventory

### Complete

| Hub | Route | Views/Tabs | Tier Access | Status |
|-----|-------|------------|-------------|--------|
| **Swap Hub** | `/swaps` | Marketplace / Admin Actions | 0: request, 1: approve, 2: force | ✅ Complete |

### Partial / Exists (Need Consolidation)

| Hub | Route | Views/Tabs | Tier Access | Status |
|-----|-------|------------|-------------|--------|
| **Schedule Hub** | `/schedule` | My Schedule / Full Grid / Generate | 0: own, 1: all + generate | Partial |
| **People Hub** | `/(hub)/people` | Directory / Credentials / FMIT / Absences | 0: view, 1: edit | Partial |
| **Call Hub** | `/call-hub` | Roster / Schedule / Faculty Call | 0: view, 1: manage | Exists |
| **Import/Export Hub** | `/hub/import-export` | Import / Export | 1 only | Started |
| **Admin Scheduling Hub** | `/admin/scheduling` | Config / Constraints / Queue / History / Metrics / Solver 3D / Schedule 3D | 2 only | ✅ Wired |

### To Build

| Hub | Route | Views/Tabs | Tier Access | Priority |
|-----|-------|------------|-------------|----------|
| **Activity Hub** | `/activities` | My Activities / Templates | 0: view all, 1: edit templates | 1 |
| **Absences Hub** | `/absences` | My Absences / Requests / Approvals | 0: view all + request, 1: approve + sick reasons | 2 |
| **Procedures Hub** | `/procedures` | Catalog (view/edit modes) | 0: view, 1: edit | 4 |
| **Ops Hub** | `/ops` | Manifest / Heatmap / Conflicts / Coverage | 0: view, 1: resolve conflicts | 5 |
| **Compliance Hub** | `/compliance` | Dashboard / Audit Trail | 0: summary, 1: details + audit | 6 |
| **Analytics Hub** | `/analytics` | Fairness / Game Theory | 0: view (transparency), 1: edit params | 7 |
| **Config Hub** | `/config` | Rotations / Settings | 1 only (setup/config) | 9 |

### Roadmapped (Future)

| Hub | Route | Views/Tabs | Tier Access | Notes |
|-----|-------|------------|-------------|-------|
| **Learner Hub** | `/learners` | Student schedules / Rotations | 0.5 only | Tier 0.5 feature, not yet implemented |

---

## Gold Standard Pattern

### From Swap Hub (`frontend/src/app/swaps/page.tsx`)

#### 1. Tier Calculation

```typescript
const userTier: RiskTier = useMemo(() => {
  if (isAdmin) return 2;
  if (isCoordinator) return 1;
  return 0;
}, [isAdmin, isCoordinator]);
```

#### 2. Declarative Tab Configuration

```typescript
interface TabConfig {
  id: string;
  label: string;
  icon: typeof IconComponent;
  description: string;
  requiredTier: RiskTier;
}

const TABS: TabConfig[] = [
  {
    id: 'marketplace',
    label: 'Marketplace',
    icon: ShoppingCart,
    description: 'Browse and manage swap requests',
    requiredTier: 0,  // All users
  },
  {
    id: 'admin',
    label: 'Admin Actions',
    icon: Shield,
    description: 'Force swaps and direct assignment edits',
    requiredTier: 1,  // Coordinator+
  },
];
```

#### 3. Tab Filtering by Permission

```typescript
const availableTabs = useMemo(() => {
  return TABS.filter((tab) => tab.requiredTier <= userTier);
}, [userTier]);
```

#### 4. Dynamic RiskBar

```typescript
const currentRiskTier: RiskTier = useMemo(() => {
  if (activeTab === 'marketplace') return 0;
  if (activeTab === 'admin') return userTier >= 2 ? 2 : 1;
  return 0;
}, [activeTab, userTier]);

// In render
<RiskBar
  tier={currentRiskTier}
  label={riskBarConfig.label}
  tooltip={riskBarConfig.tooltip}
/>
```

#### 5. Double Permission Check

```tsx
{/* Check at tab level */}
{availableTabs.map((tab) => (
  <TabButton key={tab.id} ... />
))}

{/* Check again at content level */}
{activeTab === 'admin' && userTier >= 1 && <AdminSwapPanel />}
```

---

## Feature Module Pattern

Each hub should have a corresponding feature module in `frontend/src/features/`:

**Existing Examples:**
- `frontend/src/features/proxy-coverage/` - Clean feature module (PR #699), needs RiskBar integration when moved to Ops Hub

```
frontend/src/features/
└── feature-name/
    ├── index.ts          # Public API (exports components, hooks, types)
    ├── FeatureName.tsx   # Main feature component
    ├── SubComponent.tsx  # Supporting components
    ├── hooks.ts          # TanStack Query hooks (queries + mutations)
    ├── types.ts          # TypeScript types, enums, constants
    └── OWNERSHIP.md      # Module documentation
```

### Export Pattern (`index.ts`)

```typescript
// Components
export { FeatureName } from './FeatureName';
export { SubComponent } from './SubComponent';

// Hooks
export {
  useFeatureQuery,
  useFeatureMutation,
  featureQueryKeys,
} from './hooks';

// Types
export type { FeatureType, FeatureConfig } from './types';
export { FEATURE_CONSTANTS } from './types';
```

---

## RiskBar Component

**Location:** `frontend/src/components/ui/RiskBar.tsx`

### Tier Colors

| Tier | Color | Meaning |
|------|-------|---------|
| 0 | Green | Read-only / self-service |
| 1 | Amber | Scoped, reversible changes |
| 2 | Red | High impact / destructive operations |

### Usage

```tsx
import { RiskBar, type RiskTier } from '@/components/ui/RiskBar';

<RiskBar
  tier={currentRiskTier}
  label="Self-Service"
  tooltip="Actions on this tab only affect your own requests"
/>
```

---

## Critical Warnings

### Couatl Killer: Query Parameter Case

**The Axios interceptor converts request/response BODY keys but NOT URL query strings.**

```typescript
// WRONG - silent failure, backend ignores unknown params
get(`/assignments?startDate=${date}&pageSize=500`)

// CORRECT - backend expects snake_case
get(`/assignments?start_date=${date}&page_size=500`)
```

**Protection:**
- Pre-commit hook: `scripts/couatl-killer.sh` (Phase 6b in `.pre-commit-config.yaml`)
- Catches common camelCase params: `startDate`, `endDate`, `pageSize`, `personId`, etc.
- Escape hatch: `// @query-param-ok` comment for intentional exceptions

**If you see silent data loading failures, check query params first.**

---

### Permission Double-Check

Always verify permissions at **BOTH** levels:

1. **Tab visibility:** Filter tabs array by `requiredTier <= userTier`
2. **Content rendering:** Guard component render with `userTier >= requiredTier`

```tsx
// Level 1: Tab doesn't appear if user lacks permission
const availableTabs = TABS.filter(t => t.requiredTier <= userTier);

// Level 2: Component doesn't render even if tab somehow appears
{activeTab === 'admin' && userTier >= 1 && <AdminPanel />}
```

**Why both?** Defense in depth. URL manipulation or state bugs shouldn't leak permissions.

---

### Parallel Run Strategy

**Never delete legacy pages until new hub is 100% verified.**

1. Build new hub alongside legacy page
2. Test thoroughly with real data
3. Get user validation
4. Move legacy to `/admin/legacy/` (holding pen)
5. Monitor for issues
6. Delete legacy only after confirmation

**Holding pen:** `/admin/legacy/` contains deprecated pages awaiting deletion.

---

## Implementation Priority

| Priority | Hub | Rationale |
|----------|-----|-----------|
| 1 | Activity Hub | Simplest model, clear tab structure |
| 2 | Absences Hub | High user value, tiered RBAC understood |
| 3 | People Hub Enhancement | Add views to existing hub |
| 4 | Procedures Hub | Small scope, critical for booking |
| 5 | Ops Hub | Bundle operational views |
| 6 | Compliance Hub | Audit + compliance dashboard |
| 7 | Analytics Hub | Fairness + game theory |
| 8 | Import/Export Hub | Finish started work |
| 9 | Config Hub | Rotations + settings |
| 10 | Schedule Hub | Consolidate existing views |
| 11 | Call Hub | Consolidate roster + schedule |

---

## Admin (Tier 2 Only) - Black Bar

These pages stay in `/admin/` and are **NOT** hub-ified:

| Route | Purpose | Why Tier 2 |
|-------|---------|------------|
| `/admin/users/` | Role/tier assignment | Keys to kingdom |
| `/admin/health/` | System diagnostics | Developer tooling |
| `/admin/legacy/` | Deprecated pages holding pen | Temporary storage |

**Rule:** If a Program Director or Coordinator needs it for daily operations, it belongs in a Tier 1 hub, not admin.

---

## Current Route Inventory

### Routes to Consolidate

| Current Route | Target Hub | Action |
|---------------|------------|--------|
| `/activities` | Activity Hub | Become default view |
| `/admin/faculty-activities` | Activity Hub | Become Templates tab |
| `/absences` | Absences Hub | Become default view |
| `/admin/credentials` | People Hub | Become Credentials tab |
| `/admin/people` | People Hub | Merge with existing |
| `/admin/procedures` | Procedures Hub | Add edit mode |
| `/daily-manifest` | Ops Hub | Become Manifest tab |
| `/heatmap` | Ops Hub | Become Demand tab |
| `/conflicts` | Ops Hub | Become Conflicts tab |
| `/proxy-coverage` | Ops Hub | Become Coverage tab (PR #699) |
| `/admin/audit` | Compliance Hub | Become Audit tab |
| `/admin/compliance` | Compliance Hub | Become Dashboard tab |
| `/admin/fairness` | Analytics Hub | Become Fairness tab |
| `/admin/game-theory` | Analytics Hub | Become Game Theory tab |
| `/admin/rotations` | Config Hub | Become Rotations tab |
| `/call-roster` | Call Hub | Merge with existing |
| `/admin/faculty-call` | Call Hub | Become Faculty Call tab |
| `/import-export` | Import/Export Hub | Consolidate with `/hub/import-export` |
| `/admin/import` | Import/Export Hub | Become Import tab |

### Routes to Keep Separate

| Route | Reason |
|-------|--------|
| `/login` | Auth flow |
| `/help` | Help center |
| `/settings` | User preferences |
| `/schedule/[personId]` | Deep link to specific person |
| `/my-schedule` | Personal schedule (may merge with Schedule Hub) |

---

## Command Center (3D Voxel Visualization)

**Route:** `/command-center`
**Status:** Phase 1 Complete (PR #700)
**Tech:** Three.js via React Three Fiber

### Current Features
- 3D voxel schedule visualization
- Animated 2D↔3D toggle with spring physics
- Conflict detection (pulsing red voxels)
- Tier-based RiskBar integration
- Lazy-loaded (~500KB isolated)

### Roadmap

| Phase | Features | Status |
|-------|----------|--------|
| 1 | Basic 3D with demo data | ✅ PR #700 |
| 2 | Real schedule data integration | Pending |
| 3 | CRUD operations by tier | Pending |
| 4 | View mode switching (axes) | Pending |
| **5** | **🥽 WebXR / Apple Vision Pro** | **Roadmapped** |

### Phase 5: WebXR / Vision Pro Support

visionOS 2+ supports WebXR by default. Levels of immersion:

| Level | Experience | Effort |
|-------|------------|--------|
| Window | 3D in Safari floating window | ✅ Done |
| Immersive VR | Schedule floats in space | Medium |
| Hand Tracking | Pinch-to-select, grab-to-move | Higher |

**Dependencies:** `@react-three/xr`

**Vision Pro Interactions:**
- Look + Pinch: Select voxels
- Two-hand pinch: Zoom/scale
- Voice: "Show conflicts"

---

## Success Criteria

- [ ] All hubs use RiskBar component
- [ ] Declarative tab configurations in all hubs
- [ ] Permission filtering at tab + content level
- [ ] Feature module pattern for new features
- [ ] No permission leakage (audit verified)
- [ ] Couatl Killer pre-commit hook passing
- [ ] All legacy routes either consolidated or in holding pen
- [ ] User validation of each hub before legacy deletion

---

## Related Documentation

- **Consolidation Analysis:** `docs/reviews/2026-01-11-frontend-consolidation-map.md`
- **Frontend Architecture:** `docs/architecture/frontend.md`
- **Hybrid Model:** `docs/scheduling/HYBRID_MODEL_OVERVIEW.md`
- **RiskBar PR:** #695
- **Swap Hub PR:** #696

---

## Changelog

| Date | Change |
|------|--------|
| 2026-01-12 | Added Admin Scheduling Hub (Tier 2, 7 tabs, 3D viz) - queue wiring complete |
| 2026-01-12 | Added Command Center section with WebXR/Vision Pro roadmap |
| 2026-01-12 | Added PR #699 Proxy Coverage → Ops Hub Coverage tab |
| 2026-01-12 | Initial roadmap created |
