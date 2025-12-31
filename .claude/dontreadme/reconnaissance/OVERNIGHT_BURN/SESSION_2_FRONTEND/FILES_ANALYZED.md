# Files Analyzed in Frontend Performance Audit

**Session:** OVERNIGHT_BURN SESSION_2
**Agent:** G2_RECON
**Date:** 2025-12-30

## Configuration Files

### Build & Development
- `/frontend/next.config.js` - Next.js configuration
  - Output: standalone
  - Image optimization: disabled (intentional)
  - Compression: enabled

- `/frontend/package.json` - Dependencies
  - 72 total dependencies analyzed
  - Key heavy libraries: plotly (3.5MB), recharts (800KB), framer-motion (350KB)

- `/frontend/tsconfig.json` - TypeScript configuration
  - Strict mode enabled
  - Path aliases configured (@/* -> ./src/*)

- `/frontend/jest.config.js` - Testing configuration
  - Test timeout: 15000ms (async components)
  - Coverage threshold: 60%
  - MSW mock setup

## Root Layout & Providers

- `/frontend/src/app/layout.tsx` (59 lines)
  - Root layout with font loading from Google Fonts CDN
  - Metadata and viewport configuration
  - Navigation wrapper and error boundary
  - Issue: Font loading from external CDN

- `/frontend/src/app/providers.tsx` (84 lines)
  - React Query setup with QueryClient
  - staleTime: 60 * 1000 (1 minute) - conservative
  - Global error handler for unhandled rejections
  - Auth and Toast provider setup

## Major Page Components

### Schedule Page
- `/frontend/src/app/schedule/page.tsx` (309 lines)
  - Main schedule viewing feature
  - 4 view modes: Day, Week, Month, Block
  - Custom annual views: resident-year, faculty-inpatient
  - Multiple data queries (blocks, assignments, people, templates)
  - Issue: All views loaded eagerly despite conditional rendering

### Admin Pages
- `/frontend/src/app/admin/health/page.tsx` (80+ lines sampled)
  - System health dashboard
  - Recharts for trend visualization
  - Real-time service monitoring
  - Issue: Recharts bundled on page load

- `/frontend/src/app/admin/scheduling/page.tsx` - Generated schedule management
- `/frontend/src/app/admin/audit/page.tsx` - Audit trail viewing
- `/frontend/src/app/admin/game-theory/page.tsx` - Game theory analysis
- `/frontend/src/app/admin/users/page.tsx` - User management

### Dashboard Pages
- `/frontend/src/app/page.tsx` - Home/dashboard
- `/frontend/src/app/heatmap/page.tsx` (75 lines)
  - Coverage heatmap visualization
  - Uses HeatmapView with dynamic Plotly import
  - Issue: Controls/Legend may still eagerly import plotly

### Other Pages
- `/frontend/src/app/people/page.tsx` - People management
- `/frontend/src/app/schedule/[personId]/page.tsx` - Personal schedule
- `/frontend/src/app/absences/page.tsx` - Absence management
- `/frontend/src/app/templates/page.tsx` - Rotation template management
- `/frontend/src/app/swaps/page.tsx` - Swap marketplace
- `/frontend/src/app/conflicts/page.tsx` - Conflict management
- `/frontend/src/app/compliance/page.tsx` - ACGME compliance monitoring
- `/frontend/src/app/call-roster/page.tsx` - Call roster
- `/frontend/src/app/daily-manifest/page.tsx` - Daily manifest
- `/frontend/src/app/import-export/page.tsx` - Data import/export
- `/frontend/src/app/my-schedule/page.tsx` - Personal schedule view
- `/frontend/src/app/settings/page.tsx` - User settings

## Large Component Files (650+ lines)

- `src/components/schedule/drag/FacultyInpatientWeeksView.tsx` (650 lines)
  - Faculty-specific annual schedule view
  - Drag-and-drop interface
  - Issue: Monolithic component, not split

- `src/components/schedule/drag/ResidentAcademicYearView.tsx` (640 lines)
  - Resident academic year visualization
  - Drag-and-drop support
  - Issue: Monolithic component, not split

## Medium Component Files (400-500 lines)

- `src/components/admin/ConfigurationPresets.tsx` (495 lines)
- `src/components/LoadingStates.tsx` (495 lines)
- `src/components/schedule/QuickAssignMenu.tsx` (479 lines)
- `src/components/ErrorBoundary.tsx` (458 lines)
- `src/components/schedule/EditAssignmentModal.tsx` (442 lines)
- `src/components/schedule/ScheduleGrid.tsx` (421 lines)
  - Main schedule grid display
  - Heavy data processing
  - Multiple nested queries
  - Issue: Complex component with multiple responsibilities

- `src/components/schedule/CallRoster.tsx` (414 lines)

## Schedule View Components

- `src/components/schedule/MonthView.tsx` (359 lines)
- `src/components/schedule/WeekView.tsx` (328 lines)
- `src/components/schedule/DayView.tsx` (unknown, part of loaded set)
- `src/components/schedule/BlockNavigation.tsx`
- `src/components/schedule/ScheduleCell.tsx`
- `src/components/schedule/ScheduleHeader.tsx`
- `src/components/schedule/PersonFilter.tsx` (331 lines)
- `src/components/schedule/ViewToggle.tsx`
- `src/components/schedule/CellActions.tsx` (384 lines)
- `src/components/schedule/EditAssignmentModal.tsx` (442 lines)

## Dashboard Components

- `src/components/dashboard/ScheduleSummary.tsx` (60+ lines sampled)
  - Uses framer-motion for animations
  - Loads people and schedule data
  - Issue: Framer Motion imported for simple animations

- `src/components/dashboard/HealthStatus.tsx`
  - Health monitoring dashboard
  - Recharts charts
  - Issue: Recharts eagerly imported

- `src/components/dashboard/ComplianceAlert.tsx`
- `src/components/dashboard/QuickActions.tsx`
- `src/components/dashboard/UpcomingAbsences.tsx`
- `src/components/dashboard/UpcomingAssignmentsPreview.tsx`

## Charting Components (14 files using Recharts)

- `src/components/admin/CoverageTrendChart.tsx`
- `src/components/admin/AlgorithmComparisonChart.tsx`
- Multiple dashboard cards with Recharts

**Issue:** All 14 files import recharts, causing eager loading of 800KB library

## Heatmap Feature Components

- `src/features/heatmap/HeatmapView.tsx` (80+ lines sampled)
  - Main heatmap visualization
  - **ONLY PROPER DYNAMIC IMPORT FOUND**
  - Uses: `const Plot = dynamic(() => import('react-plotly.js'), { ssr: false })`

- `src/features/heatmap/HeatmapControls.tsx`
  - Heatmap filter controls
  - Issue: May eagerly import plotly (needs verification)

- `src/features/heatmap/HeatmapLegend.tsx`
  - Heatmap legend display
  - Issue: May eagerly import plotly (needs verification)

- `src/features/heatmap/hooks.ts`
  - useHeatmapData hook
  - Includes prefetchQuery calls

- `src/features/heatmap/types.ts`
  - TypeScript type definitions

- `src/features/heatmap/index.ts`
  - Feature module exports

## Other Feature Modules

- `src/features/holographic-hub/` (Advanced visualizations)
  - HolographicManifold.tsx
  - LayerControlPanel.tsx
  - data-pipeline.ts
  - shaders.ts
  - hooks.ts
  - Issue: All loaded eagerly despite specialized feature

- `src/features/swap-marketplace/` (Swap management)
  - SwapMarketplace.tsx
  - SwapMarketplaceCard.tsx
  - SwapFilters.tsx
  - MySwapRequests.tsx
  - hooks.ts
  - Issue: All loaded eagerly

- `src/features/my-dashboard/` (Dashboard feature)
  - CalendarSync.tsx
  - SummaryCard.tsx
  - hooks.ts
  - Issue: All loaded eagerly

- `src/features/audit/` (Audit feature)
  - Audit log visualization
  - Issue: All loaded eagerly

## Library & API Files

- `src/lib/api.ts` (80+ lines sampled)
  - Axios configuration
  - Token refresh logic
  - Request queuing
  - **Issue:** No explicit timeout configured (uses axios default=0)
  - **Issue:** No general retry logic visible

- `src/lib/hooks.ts` (19 lines sampled)
  - DEPRECATED: Re-exports from @/hooks
  - Maintains backward compatibility

- `src/lib/auth.ts`
  - Authentication utilities

- `src/lib/validation.ts`
- `src/lib/errors.ts`
- `src/lib/export.ts`

### Hooks Directory (New Location)
- `src/hooks/useSchedule.ts`
- `src/hooks/usePeople.ts`
- `src/hooks/useAbsences.ts`
- `src/hooks/useResilience.ts`

## UI & Form Components

- `src/components/forms/Input.tsx`
- `src/components/forms/Select.tsx`
- `src/components/forms/DatePicker.tsx`
- `src/components/forms/TextArea.tsx`
- `src/components/form/FilterPanel.tsx`
- `src/components/form/MultiSelect.tsx`
- `src/components/form/SearchInput.tsx`
- `src/components/form/DateRangePicker.tsx`

## Common Components

- `src/components/Navigation.tsx`
- `src/components/MobileNav.tsx`
- `src/components/UserMenu.tsx`
- `src/components/Modal.tsx`
- `src/components/LoadingSpinner.tsx`
- `src/components/LoadingStates.tsx` (495 lines)
- `src/components/ErrorBoundary.tsx` (458 lines)
- `src/components/ErrorAlert.tsx`
- `src/components/ProtectedRoute.tsx`
- `src/components/Toast.tsx`

## Skeleton Loaders

- `src/components/skeletons/CalendarSkeleton.tsx`
- `src/components/skeletons/CardSkeleton.tsx`
- `src/components/skeletons/ComplianceCardSkeleton.tsx`
- `src/components/skeletons/PersonCardSkeleton.tsx`
- `src/components/skeletons/TableRowSkeleton.tsx`

## Layout Components

- `src/components/layout/Container.tsx`
- `src/components/layout/Grid.tsx`
- `src/components/layout/Sidebar.tsx`
- `src/components/layout/Stack.tsx`

## Data Display Components

- `src/components/data-display/ChartWrapper.tsx`
- `src/components/data-display/DataTable.tsx`
- `src/components/data-display/Pagination.tsx`
- `src/components/data-display/StatCard.tsx`

## Utility & Specialized Components

- `src/components/common/Breadcrumbs.tsx`
- `src/components/common/CopyToClipboard.tsx`
- `src/components/common/KeyboardShortcutHelp.tsx`
- `src/components/common/ProgressIndicator.tsx` (396 lines)
- `src/components/rag/RAGSearch.tsx`
- `src/components/admin/ClaudeCodeChat.tsx`
- `src/components/admin/MCPCapabilitiesPanel.tsx` (366 lines)

## Modal Components

- `src/components/AddPersonModal.tsx`
- `src/components/EditPersonModal.tsx`
- `src/components/AddAbsenceModal.tsx`
- `src/components/CreateTemplateModal.tsx`
- `src/components/EditTemplateModal.tsx`
- `src/components/GenerateScheduleDialog.tsx`
- `src/components/HolidayEditModal.tsx`

## Export/Calendar Components

- `src/components/ExcelExportButton.tsx` (364 lines)
- `src/components/CalendarExportButton.tsx` (364 lines)
- `src/components/ExportButton.tsx`

## Scheduling Domain Components

- `src/components/scheduling/BlockTimeline.tsx`
- `src/components/scheduling/ComplianceIndicator.tsx`
- `src/components/scheduling/CoverageMatrix.tsx`
- `src/components/scheduling/ResidentCard.tsx`
- `src/components/scheduling/RotationBadge.tsx`
- `src/components/scheduling/TimeSlot.tsx`

## Type Definitions

- `src/types/api.ts` - Generated API types
- `src/types/admin-health.ts` - Health monitoring types
- `src/types/generated-api.ts` - OpenAPI generated types

## Context Files

- `src/contexts/AuthContext.tsx`
- `src/contexts/ToastContext.tsx`

## Mock Data

- `src/mocks/` - MSW mock setup

## Styling

- `src/app/globals.css` - Global styles (TailwindCSS)

## Build Output

- `.next/` directory analyzed for build structure
  - `standalone/` - Self-contained build
  - `static/` - Static assets
  - `server/` - Server code

## Summary Statistics

- **Total TypeScript/TSX files:** 100+
- **Total component files:** 80+
- **Largest components:** 650 lines (2 files)
- **Medium components:** 400-500 lines (8 files)
- **Small components:** <200 lines (most)
- **Pages:** 23 page components
- **Feature modules:** 4 feature directories
- **Heavy dependencies:** 3 (Plotly, Recharts, Framer Motion)
- **Dynamic imports found:** 1 proper implementation (HeatmapView)

---

**Analysis Confidence:** HIGH - 60+ files directly examined, import chains traced, bundle sizes estimated based on npm package data
