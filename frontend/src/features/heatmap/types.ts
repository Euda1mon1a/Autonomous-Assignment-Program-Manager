/**
 * Heatmap Visualization Types and Interfaces
 *
 * Defines the data structures for heatmap visualization functionality,
 * including heatmap data, filters, and export configuration.
 */

// ============================================================================
// Core Heatmap Types
// ============================================================================

/**
 * Color scale definition
 */
export interface ColorScale {
  min: number;
  max: number;
  colors: string[];
  labels?: string[];
}

/**
 * Annotation for heatmap cells
 */
export interface HeatmapAnnotation {
  x: number;
  y: number;
  text: string;
  font?: {
    color?: string;
    size?: number;
  };
}

/**
 * Core heatmap data structure
 */
export interface HeatmapData {
  x_labels: string[];
  y_labels: string[];
  z_values: number[][];
  color_scale?: ColorScale;
  annotations?: HeatmapAnnotation[];
  title?: string;
  x_axis_label?: string;
  y_axis_label?: string;
}

/**
 * Activity type for filtering
 */
export type ActivityType = 'residency' | 'fmit' | 'both';

/**
 * Group by options for heatmap
 */
export type HeatmapGroupBy = 'day' | 'week' | 'person' | 'rotation';

/**
 * Heatmap filters
 */
export interface HeatmapFilters {
  start_date?: string;
  end_date?: string;
  person_ids?: string[];
  rotation_ids?: string[];
  include_fmit?: boolean;
  group_by?: HeatmapGroupBy;
}

/**
 * Coverage metrics for heatmap
 */
export interface CoverageMetrics {
  total_slots: number;
  filled_slots: number;
  coverage_percentage: number;
  gaps: Array<{
    date: string;
    rotation: string;
    required: number;
    assigned: number;
  }>;
}

/**
 * Workload metrics for heatmap
 */
export interface WorkloadMetrics {
  person_id: string;
  person_name: string;
  total_assignments: number;
  total_hours: number;
  blocks_by_rotation: Record<string, number>;
  average_weekly_hours: number;
}

// ============================================================================
// API Response Types
// ============================================================================

/**
 * Coverage heatmap response
 */
export interface CoverageHeatmapResponse {
  heatmap: HeatmapData;
  metrics: CoverageMetrics;
}

/**
 * Workload heatmap response
 */
export interface WorkloadHeatmapResponse {
  heatmap: HeatmapData;
  metrics: WorkloadMetrics[];
}

/**
 * Generic heatmap response
 */
export interface HeatmapResponse {
  heatmap: HeatmapData;
  metadata?: Record<string, unknown>;
}

// ============================================================================
// Export Types
// ============================================================================

/**
 * Export format options
 */
export type HeatmapExportFormat = 'png' | 'svg' | 'pdf' | 'json';

/**
 * Export configuration
 */
export interface HeatmapExportConfig {
  format: HeatmapExportFormat;
  width?: number;
  height?: number;
  title?: string;
  include_legend?: boolean;
  filters?: HeatmapFilters;
}

// ============================================================================
// UI State Types
// ============================================================================

/**
 * Heatmap view mode
 */
export type HeatmapViewMode = 'coverage' | 'workload' | 'custom';

/**
 * Date range for filtering
 */
export interface DateRange {
  start: string;
  end: string;
}

/**
 * Heatmap page state
 */
export interface HeatmapPageState {
  viewMode: HeatmapViewMode;
  filters: HeatmapFilters;
  dateRange: DateRange;
  selectedPersonIds: string[];
  selectedRotationIds: string[];
  isExportModalOpen: boolean;
  isFilterPanelOpen: boolean;
}

/**
 * Cell click event data
 */
export interface HeatmapCellClickData {
  x: string;
  y: string;
  value: number;
  pointIndex: [number, number];
}

// ============================================================================
// Constants
// ============================================================================

/**
 * Display labels for view modes
 */
export const VIEW_MODE_LABELS: Record<HeatmapViewMode, string> = {
  coverage: 'Coverage View',
  workload: 'Workload View',
  custom: 'Custom View',
};

/**
 * Display labels for group by options
 */
export const GROUP_BY_LABELS: Record<HeatmapGroupBy, string> = {
  day: 'Daily',
  week: 'Weekly',
  person: 'By Person',
  rotation: 'By Rotation',
};

/**
 * Default color scales
 * Uses consistent intensity scale: cool (low) → warm (high) → black (critical)
 * Aligns with resilience framework: GREEN → YELLOW → ORANGE → RED → BLACK
 */
export const DEFAULT_COLOR_SCALES = {
  coverage: {
    min: 0,
    max: 100,
    colors: ['#1e1b4b', '#ef4444', '#fbbf24', '#22c55e'], // black(0%) -> red -> yellow -> green(100%)
    labels: ['Gap', 'Low', 'Partial', 'Full'],
  },
  workload: {
    min: 0,
    max: 80,
    colors: ['#3b82f6', '#fbbf24', '#ef4444', '#1e1b4b'], // blue(0) -> yellow -> red -> black(80+)
    labels: ['Light', 'Moderate', 'Heavy', 'Critical'],
  },
  custom: {
    min: 0,
    max: 100,
    colors: ['#3b82f6', '#fbbf24', '#ef4444', '#1e1b4b'], // blue -> yellow -> red -> black
    labels: ['Low', 'Medium', 'High', 'Critical'],
  },
};

/**
 * Activity type colors
 */
export const ACTIVITY_TYPE_COLORS: Record<string, string> = {
  residency: '#3b82f6', // blue
  fmit: '#10b981', // green
  both: '#8b5cf6', // purple
  clinical: '#f59e0b', // amber
  research: '#06b6d4', // cyan
  education: '#ec4899', // pink
};

/**
 * Coverage indicator colors
 */
export const COVERAGE_INDICATOR_COLORS = {
  full: '#22c55e', // green
  partial: '#fbbf24', // yellow
  gap: '#ef4444', // red
  overcovered: '#06b6d4', // cyan
};

/**
 * Default export dimensions
 */
export const DEFAULT_EXPORT_DIMENSIONS = {
  width: 1200,
  height: 800,
};

/**
 * Default date range (last 30 days)
 */
export function getDefaultDateRange(): DateRange {
  const end = new Date();
  const start = new Date();
  start.setDate(start.getDate() - 30);

  return {
    start: start.toISOString().split('T')[0],
    end: end.toISOString().split('T')[0],
  };
}
