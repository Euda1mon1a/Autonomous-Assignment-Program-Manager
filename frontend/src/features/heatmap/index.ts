/**
 * Heatmap Visualization Feature Module
 *
 * Provides comprehensive heatmap visualization UI components for viewing
 * schedule coverage, workload distribution, and rotation assignments.
 *
 * Components:
 * - HeatmapView: Main Plotly-based heatmap visualization component
 * - HeatmapControls: Filtering and control UI (date range, filters, export)
 * - HeatmapLegend: Color scale and activity type legend display
 *
 * Hooks:
 * - useHeatmapData: Fetch generic heatmap data with filters
 * - useCoverageHeatmap: Fetch coverage heatmap
 * - useWorkloadHeatmap: Fetch workload heatmap
 * - useRotationCoverageComparison: Fetch rotation comparison data
 * - useExportHeatmap: Export heatmap as image/data
 * - useDownloadHeatmap: Download heatmap file
 * - useAvailableRotations: Fetch rotations for filtering
 */

// Components
export { HeatmapView, HeatmapViewSkeleton } from './HeatmapView';
export { HeatmapControls } from './HeatmapControls';
export { HeatmapLegend, CompactHeatmapLegend } from './HeatmapLegend';

// Hooks
export {
  useHeatmapData,
  useCoverageHeatmap,
  useWorkloadHeatmap,
  useRotationCoverageComparison,
  useExportHeatmap,
  useDownloadHeatmap,
  useAvailableRotations,
  usePrefetchHeatmap,
  useInvalidateHeatmaps,
  heatmapQueryKeys,
} from './hooks';

// Types
export type {
  ColorScale,
  HeatmapAnnotation,
  HeatmapData,
  ActivityType,
  HeatmapGroupBy,
  HeatmapFilters,
  CoverageMetrics,
  WorkloadMetrics,
  CoverageHeatmapResponse,
  WorkloadHeatmapResponse,
  HeatmapResponse,
  HeatmapExportFormat,
  HeatmapExportConfig,
  HeatmapViewMode,
  DateRange,
  HeatmapPageState,
  HeatmapCellClickData,
} from './types';

// Constants
export {
  VIEW_MODE_LABELS,
  GROUP_BY_LABELS,
  DEFAULT_COLOR_SCALES,
  ACTIVITY_TYPE_COLORS,
  COVERAGE_INDICATOR_COLORS,
  DEFAULT_EXPORT_DIMENSIONS,
  getDefaultDateRange,
} from './types';
