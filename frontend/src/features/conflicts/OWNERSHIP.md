# File Ownership Matrix - Conflict Resolution Feature

## Territory: `frontend/src/features/conflicts/`

This document outlines the file ownership and responsibilities for the conflict resolution UI feature.

---

## File Ownership Matrix

| File | Owner | Purpose | Dependencies |
|------|-------|---------|--------------|
| `types.ts` | conflicts-team | Type definitions for conflicts, resolutions, and history | None |
| `hooks.ts` | conflicts-team | React Query hooks for conflict API interactions | `@/lib/api`, `types.ts` |
| `ConflictCard.tsx` | conflicts-team | Individual conflict display with severity highlighting | `types.ts`, `lucide-react`, `date-fns` |
| `ConflictList.tsx` | conflicts-team | Filterable, sortable list of conflicts | `ConflictCard.tsx`, `hooks.ts`, `types.ts` |
| `ConflictResolutionSuggestions.tsx` | conflicts-team | AI-powered resolution suggestions display | `hooks.ts`, `types.ts` |
| `ManualOverrideModal.tsx` | conflicts-team | Modal for creating manual overrides with ACGME tracking | `hooks.ts`, `types.ts` |
| `ConflictHistory.tsx` | conflicts-team | Conflict timeline and pattern analysis | `hooks.ts`, `types.ts`, `ConflictCard.tsx` |
| `BatchResolution.tsx` | conflicts-team | Batch processing of multiple conflicts | `hooks.ts`, `types.ts`, `ConflictCard.tsx` |
| `ConflictDashboard.tsx` | conflicts-team | Main dashboard integrating all conflict components | All above components |
| `index.ts` | conflicts-team | Module exports | All above files |

---

## Component Responsibilities

### Core Types (`types.ts`)
- `Conflict` - Main conflict data structure
- `ConflictSeverity` - Severity levels (critical, high, medium, low)
- `ConflictType` - Types of conflicts (scheduling, ACGME, supervision, etc.)
- `ResolutionSuggestion` - AI-generated resolution options
- `ManualOverride` - Override data with ACGME audit fields
- `ConflictPattern` - Recurring conflict pattern analysis

### Hooks (`hooks.ts`)
- `useConflicts` - Fetch and filter conflicts list
- `useConflict` - Fetch single conflict details
- `useResolutionSuggestions` - Get AI suggestions for a conflict
- `useApplyResolution` - Apply a resolution suggestion
- `useCreateOverride` - Create manual override
- `useBatchResolve` - Resolve multiple conflicts
- `useConflictHistory` - Fetch conflict history timeline
- `useConflictPatterns` - Fetch recurring patterns
- `useConflictStatistics` - Dashboard statistics

### Components

#### ConflictCard
- Visual conflict display with severity-based styling
- Expandable details view
- Quick action buttons (resolve, override, history)
- Compact mode for list displays

#### ConflictList
- Search and filter functionality
- Multi-select for batch operations
- Sort by severity, date, type, status
- Real-time conflict detection trigger

#### ConflictResolutionSuggestions
- Display AI-generated resolution options
- Impact and confidence scores
- Detailed change preview
- Side effects warning

#### ManualOverrideModal
- Override type selection (acknowledge, temporary, permanent)
- ACGME exception documentation
- Supervisor approval workflow
- Audit trail compliance

#### ConflictHistory
- Timeline view of conflict lifecycle
- Pattern detection and analysis
- Affected people tracking
- Prevention suggestions

#### BatchResolution
- Multi-conflict selection
- Bulk resolution methods
- Progress tracking
- Results summary

#### ConflictDashboard
- Statistics overview cards
- Integrated conflict management
- Split-panel layout for list + details
- Tab navigation between views

---

## API Integration

This feature expects the following API endpoints:

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/conflicts` | GET | List conflicts with filtering |
| `/conflicts/:id` | GET | Get single conflict |
| `/conflicts/:id/suggestions` | GET | Get resolution suggestions |
| `/conflicts/:id/resolve` | POST | Apply resolution |
| `/conflicts/:id/override` | POST | Create override |
| `/conflicts/:id/status` | PUT | Update status |
| `/conflicts/:id/history` | GET | Get history timeline |
| `/conflicts/batch-resolve` | POST | Batch resolution |
| `/conflicts/batch-ignore` | POST | Batch ignore |
| `/conflicts/patterns` | GET | Get recurring patterns |
| `/conflicts/statistics` | GET | Get dashboard stats |
| `/conflicts/detect` | POST | Trigger detection |

---

## ACGME Compliance

The conflict resolution UI includes specific features for ACGME compliance:

1. **Override Documentation**
   - Exception type selection
   - Detailed justification required
   - Supervisor approval workflow

2. **Audit Trail**
   - All actions timestamped
   - User attribution
   - Change history tracking

3. **Pattern Analysis**
   - Recurring violation detection
   - Affected person tracking
   - Prevention recommendations

---

## Testing Recommendations

1. **Unit Tests**
   - Type validation for all interfaces
   - Hook behavior with mock API
   - Component rendering with various conflict states

2. **Integration Tests**
   - Filter and sort combinations
   - Batch resolution workflows
   - Override creation flow

3. **E2E Tests**
   - Complete conflict resolution flow
   - Batch processing scenarios
   - ACGME compliance documentation

---

## Related Territories

- `frontend/src/features/audit/` - Audit log integration
- `frontend/src/features/templates/` - Template conflict checking
- `frontend/src/components/schedule/` - Schedule conflict highlighting
