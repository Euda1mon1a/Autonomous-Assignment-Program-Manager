***REMOVED*** File Ownership Matrix: frontend/src/features/swap-marketplace/

***REMOVED******REMOVED*** Territory: Swap Marketplace
**Owner**: COMET Round M - Terminal 9 (Swap-Marketplace)
**Created**: 2024-12-17
**Branch**: claude/assess-project-status-Ia9J6

***REMOVED******REMOVED*** Files and Responsibilities

| File | Purpose | Dependencies | Exports |
|------|---------|--------------|---------|
| `types.ts` | Type definitions, interfaces, enums, constants | None | All swap marketplace types, enums, constants |
| `hooks.ts` | React Query hooks for API integration | `@tanstack/react-query`, `@/lib/api`, `./types` | Query hooks, mutation hooks |
| `SwapFilters.tsx` | Filtering UI for swap marketplace | `date-fns`, `lucide-react`, `./types` | `SwapFilters` |
| `SwapRequestCard.tsx` | Display card for individual swap requests | `date-fns`, `lucide-react`, `./types`, `./hooks` | `SwapRequestCard` |
| `SwapRequestForm.tsx` | Form to create new swap requests | `date-fns`, `lucide-react`, `./hooks`, `./types` | `SwapRequestForm` |
| `MySwapRequests.tsx` | User's swap request management view | `lucide-react`, `./hooks`, `./types`, `./SwapRequestCard` | `MySwapRequests` |
| `SwapMarketplace.tsx` | Main page integrating all components | All above components, `./hooks`, `./types`, `lucide-react` | `SwapMarketplace` |
| `index.ts` | Barrel exports | All above files | All public exports |

***REMOVED******REMOVED*** Feature Summary

***REMOVED******REMOVED******REMOVED*** Components

1. **SwapMarketplace** - Main container component
   - Three-tab interface: Browse / My Requests / Create
   - Integrates all sub-components
   - Shows marketplace statistics
   - Help section with usage instructions

2. **SwapFilters** - Advanced filtering
   - Date range selection with quick presets
   - Status filter (pending, approved, rejected, executed, cancelled)
   - Swap type filter (one-to-one, absorb)
   - Quick toggles (My Postings Only, Compatible Only)
   - Search by faculty name or reason
   - Active filter indicators and reset

3. **SwapRequestCard** - Swap request display
   - Shows swap details (faculty, weeks, status)
   - Badge for status with color coding
   - Action buttons (Accept, Reject, Cancel) based on permissions
   - Notes input for accept/reject
   - Reason display
   - Marketplace entry variant for browsing

4. **SwapRequestForm** - Create swap request
   - Week selection from assigned weeks
   - Swap mode: auto-find candidates or specific faculty
   - Target faculty selection (for specific mode)
   - Reason/notes textarea
   - Form validation
   - Success/error messaging
   - Help text and instructions

5. **MySwapRequests** - Request management
   - Three tabs: Incoming / Outgoing / Recent
   - Incoming: Requests to accept/reject
   - Outgoing: Pending requests with cancel option
   - Recent: Completed, rejected, or cancelled swaps
   - Empty states for each tab
   - Summary statistics

***REMOVED******REMOVED******REMOVED*** Hooks

- `useSwapMarketplace(filters)` - Fetch marketplace entries
- `useMySwapRequests()` - Fetch user's swap requests (incoming/outgoing/recent)
- `useCreateSwapRequest()` - Create new swap request mutation
- `useAcceptSwap(id)` - Accept incoming swap request mutation
- `useRejectSwap(id)` - Reject incoming swap request mutation
- `useCancelSwap(id)` - Cancel outgoing swap request mutation
- `useFacultyPreferences()` - Fetch faculty scheduling preferences

***REMOVED******REMOVED******REMOVED*** Types

- `SwapRequest` - Complete swap request structure
- `MarketplaceEntry` - Simplified entry for marketplace browsing
- `SwapStatus` - Enum for swap statuses
- `SwapType` - Enum for swap types
- `SwapFilters` - Filter configuration
- `CreateSwapRequest` - Request payload for creating swaps
- `SwapRespondRequest` - Request payload for accept/reject
- `MySwapsResponse` - Response with incoming/outgoing/recent swaps
- `MarketplaceResponse` - Response with marketplace entries
- `FacultyPreference` - Faculty scheduling preferences

***REMOVED******REMOVED*** Integration Points

***REMOVED******REMOVED******REMOVED*** API Endpoints Expected
- `GET /api/portal/marketplace` - Get marketplace entries
- `GET /api/portal/my/swaps` - Get user's swap requests
- `POST /api/portal/my/swaps` - Create new swap request
- `POST /api/portal/my/swaps/:id/respond` - Accept/reject swap request
- `GET /api/portal/my/preferences` - Get faculty preferences

***REMOVED******REMOVED******REMOVED*** Shared Dependencies
- `@/lib/api` - API client utilities (get, post)
- `@tanstack/react-query` - Data fetching and caching
- `date-fns` - Date formatting and manipulation
- `lucide-react` - Icons

***REMOVED******REMOVED******REMOVED*** Backend Schema Alignment
- Transforms snake_case backend responses to camelCase frontend types
- Maps backend `SwapRecord` model to frontend `SwapRequest` interface
- Aligns with backend portal schemas (`MarketplaceEntry`, `SwapRequestSummary`, etc.)

***REMOVED******REMOVED*** Non-Overlapping Boundaries

This module is exclusively responsible for:
- Swap marketplace browsing and filtering
- Creating swap requests
- Managing incoming swap requests (accept/reject)
- Managing outgoing swap requests (cancel)
- Displaying swap request details and status

This module does NOT handle:
- Actual swap execution logic (backend responsibility)
- Schedule generation or validation
- FMIT assignment creation/deletion
- Faculty profile management
- Absence tracking
- Conflict resolution (handled by conflicts feature)
- Audit logging (handled by audit feature)

***REMOVED******REMOVED*** Usage Example

```typescript
import { SwapMarketplace } from '@/features/swap-marketplace';

function SwapPage() {
  return <SwapMarketplace />;
}
```

***REMOVED******REMOVED*** Data Flow

1. **Browse Flow**:
   - User applies filters
   - `useSwapMarketplace(filters)` fetches marketplace entries
   - Entries displayed in grid with `SwapRequestCard`
   - Compatible swaps highlighted

2. **Create Flow**:
   - User fills out `SwapRequestForm`
   - `useCreateSwapRequest()` submits to backend
   - On success, redirects to My Requests tab
   - Queries invalidated to refresh data

3. **Accept/Reject Flow**:
   - User views incoming request in `MySwapRequests`
   - Clicks Accept/Reject on `SwapRequestCard`
   - Optional notes added
   - `useAcceptSwap(id)` or `useRejectSwap(id)` called
   - Queries invalidated to refresh lists

4. **Cancel Flow**:
   - User views outgoing request in `MySwapRequests`
   - Clicks Cancel on `SwapRequestCard`
   - Confirmation dialog shown
   - `useCancelSwap(id)` called
   - Queries invalidated to refresh lists

***REMOVED******REMOVED*** Future Enhancements

Potential future additions (not in current scope):
- Real-time notifications for new swap opportunities
- Counter-offer functionality
- Batch swap operations
- Swap request templates
- Analytics dashboard for swap patterns
- Email notifications integration
- Calendar integration for week visualization
