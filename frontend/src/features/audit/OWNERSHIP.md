# File Ownership Matrix: frontend/src/features/audit/

## Territory: Audit Log Viewer
**Owner**: COMET Round E - Terminal 4 (Audit)
**Created**: 2024-12-15
**Branch**: claude/audit-log-viewer-7x9Km

## Files and Responsibilities

| File | Purpose | Dependencies | Exports |
|------|---------|--------------|---------|
| `types.ts` | Type definitions, interfaces, constants | None | All audit types, constants |
| `hooks.ts` | React Query hooks for API integration | `@tanstack/react-query`, `@/lib/api`, `./types` | Query hooks, mutation hooks |
| `AuditLogTable.tsx` | Main table view with expandable rows | `date-fns`, `lucide-react`, `./types` | `AuditLogTable` |
| `AuditLogFilters.tsx` | Filtering and search UI | `date-fns`, `lucide-react`, `./types` | `AuditLogFilters` |
| `AuditLogExport.tsx` | Export functionality (CSV, JSON, PDF) | `date-fns`, `lucide-react`, `@/lib/export`, `./types` | `AuditLogExport` |
| `AuditTimeline.tsx` | Visual timeline view | `date-fns`, `lucide-react`, `./types` | `AuditTimeline` |
| `ChangeComparison.tsx` | Side-by-side change comparison | `date-fns`, `lucide-react`, `./types` | `ChangeComparison` |
| `AuditLogPage.tsx` | Main page integrating all components | All above components, `./hooks`, `./types` | `AuditLogPage` |
| `index.ts` | Barrel exports | All above files | All public exports |

## Feature Summary

### Components
1. **AuditLogPage** - Main container component
   - Integrates all sub-components
   - Manages state (filters, sort, pagination, view mode)
   - Statistics dashboard cards

2. **AuditLogTable** - Comprehensive data table
   - Sortable columns
   - Expandable rows for change details
   - Pagination controls
   - ACGME override highlighting

3. **AuditLogFilters** - Advanced filtering
   - Date range picker with quick presets
   - Multi-select dropdowns (entity type, action, user, severity)
   - Full-text search with debounce
   - Active filter tags

4. **AuditLogExport** - Export functionality
   - CSV format (spreadsheet compatible)
   - JSON format (full data)
   - PDF format (print-ready report)
   - Export all matching records via API

5. **AuditTimeline** - Visual timeline
   - Events grouped by date
   - Collapsible date sections
   - Color-coded action types
   - Legend for action types

6. **ChangeComparison** - Comparison view
   - Single entry detail view
   - Side-by-side entry comparison
   - Diff visualization (before/after)
   - ACGME override details

### Hooks
- `useAuditLogs` - Fetch paginated logs
- `useAuditLogEntry` - Fetch single entry
- `useAuditStatistics` - Fetch dashboard stats
- `useAuditTimeline` - Fetch timeline events
- `useEntityAuditHistory` - Entity-specific history
- `useUserAuditActivity` - User activity logs
- `useExportAuditLogs` - Export mutation
- `useMarkAuditReviewed` - Mark reviewed mutation
- `useAuditUsers` - Fetch users for filters

### Types
- `AuditLogEntry` - Core audit entry structure
- `AuditLogFilters` - Filter configuration
- `AuditLogSort` - Sort configuration
- `AuditViewMode` - View mode enum
- `FieldChange` - Individual field change
- `TimelineEvent` - Timeline display event
- `AuditExportConfig` - Export options

## Integration Points

### API Endpoints Expected
- `GET /api/audit/logs` - Paginated audit logs
- `GET /api/audit/logs/:id` - Single audit entry
- `GET /api/audit/statistics` - Statistics
- `GET /api/audit/users` - Users for filtering
- `POST /api/audit/export` - Export all records
- `POST /api/audit/mark-reviewed` - Mark as reviewed

### Shared Dependencies
- `@/lib/api` - API client utilities
- `@/lib/export` - Export utilities
- `@tanstack/react-query` - Data fetching
- `date-fns` - Date formatting
- `lucide-react` - Icons

## Non-Overlapping Boundaries

This module is exclusively responsible for:
- Audit log viewing and searching
- Audit log filtering
- Audit log exporting
- Audit event timeline visualization
- Change comparison and diff viewing

This module does NOT handle:
- Bulk import/export (handled by import-export feature)
- Template management (handled by templates feature)
- Conflict resolution (handled by conflicts feature)
- Actual audit log creation (backend responsibility)
