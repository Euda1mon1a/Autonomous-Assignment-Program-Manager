/**
 * Mock data factories for heatmap tests
 * Provides reusable mock data for heatmap-related tests
 */

import type {
  HeatmapData,
  HeatmapFilters,
  HeatmapResponse,
  CoverageHeatmapResponse,
  WorkloadHeatmapResponse,
  HeatmapExportConfig,
  DateRange,
  ColorScale,
  HeatmapAnnotation,
  CoverageMetrics,
  WorkloadMetrics,
  HeatmapCellClickData,
} from '@/features/heatmap/types';

/**
 * Mock data factories
 */
export const heatmapMockFactories = {
  colorScale: (overrides: Partial<ColorScale> = {}): ColorScale => ({
    min: 0,
    max: 100,
    colors: ['#ef4444', '#fbbf24', '#22c55e'],
    labels: ['Low', 'Medium', 'High'],
    ...overrides,
  }),

  annotation: (overrides: Partial<HeatmapAnnotation> = {}): HeatmapAnnotation => ({
    x: 0,
    y: 0,
    text: 'Gap',
    font: {
      color: '#000000',
      size: 10,
    },
    ...overrides,
  }),

  heatmapData: (overrides: Partial<HeatmapData> = {}): HeatmapData => ({
    x_labels: ['2024-01-01', '2024-01-02', '2024-01-03', '2024-01-04', '2024-01-05'],
    y_labels: ['Clinic', 'Inpatient', 'Procedures', 'Conference'],
    z_values: [
      [100, 80, 90, 100, 95],
      [90, 100, 85, 90, 100],
      [75, 60, 80, 70, 85],
      [100, 100, 100, 100, 100],
    ],
    color_scale: heatmapMockFactories.colorScale(),
    annotations: [],
    title: 'Coverage Heatmap',
    x_axis_label: 'Date',
    y_axis_label: 'Rotation',
    ...overrides,
  }),

  dateRange: (overrides: Partial<DateRange> = {}): DateRange => ({
    start: '2024-01-01',
    end: '2024-01-31',
    ...overrides,
  }),

  filters: (overrides: Partial<HeatmapFilters> = {}): HeatmapFilters => ({
    start_date: '2024-01-01',
    end_date: '2024-01-31',
    person_ids: [],
    rotation_ids: [],
    include_fmit: true,
    group_by: 'day',
    ...overrides,
  }),

  coverageMetrics: (overrides: Partial<CoverageMetrics> = {}): CoverageMetrics => ({
    total_slots: 100,
    filled_slots: 95,
    coverage_percentage: 95.0,
    gaps: [
      {
        date: '2024-01-05',
        rotation: 'Procedures',
        required: 2,
        assigned: 1,
      },
    ],
    ...overrides,
  }),

  workloadMetrics: (overrides: Partial<WorkloadMetrics> = {}): WorkloadMetrics => ({
    person_id: 'person-1',
    person_name: 'Dr. John Smith',
    total_assignments: 20,
    total_hours: 75.0,
    blocks_by_rotation: {
      'Clinic': 8,
      'Inpatient': 12,
    },
    average_weekly_hours: 37.5,
    ...overrides,
  }),

  heatmapResponse: (overrides: Partial<HeatmapResponse> = {}): HeatmapResponse => ({
    heatmap: heatmapMockFactories.heatmapData(),
    metadata: {
      generated_at: '2024-02-15T10:30:00Z',
      filters_applied: true,
    },
    ...overrides,
  }),

  coverageHeatmapResponse: (
    overrides: Partial<CoverageHeatmapResponse> = {}
  ): CoverageHeatmapResponse => ({
    heatmap: heatmapMockFactories.heatmapData(),
    metrics: heatmapMockFactories.coverageMetrics(),
    ...overrides,
  }),

  workloadHeatmapResponse: (
    overrides: Partial<WorkloadHeatmapResponse> = {}
  ): WorkloadHeatmapResponse => ({
    heatmap: heatmapMockFactories.heatmapData({
      y_labels: ['Dr. John Smith', 'Dr. Jane Doe', 'Dr. Bob Wilson'],
      z_values: [
        [40, 45, 38, 42, 40],
        [38, 40, 42, 39, 41],
        [42, 43, 41, 40, 39],
      ],
    }),
    metrics: [
      heatmapMockFactories.workloadMetrics(),
      heatmapMockFactories.workloadMetrics({
        person_id: 'person-2',
        person_name: 'Dr. Jane Doe',
        total_assignments: 18,
        total_hours: 72.0,
      }),
    ],
    ...overrides,
  }),

  exportConfig: (overrides: Partial<HeatmapExportConfig> = {}): HeatmapExportConfig => ({
    format: 'png',
    width: 1200,
    height: 800,
    title: 'Heatmap Export',
    include_legend: true,
    filters: heatmapMockFactories.filters(),
    ...overrides,
  }),

  cellClickData: (overrides: Partial<HeatmapCellClickData> = {}): HeatmapCellClickData => ({
    x: '2024-01-01',
    y: 'Clinic',
    value: 100,
    pointIndex: [0, 0],
    ...overrides,
  }),

  availablePersons: () => [
    { id: 'person-1', name: 'Dr. John Smith' },
    { id: 'person-2', name: 'Dr. Jane Doe' },
    { id: 'person-3', name: 'Dr. Bob Wilson' },
  ],

  availableRotations: () => [
    { id: 'rotation-1', name: 'Clinic' },
    { id: 'rotation-2', name: 'Inpatient' },
    { id: 'rotation-3', name: 'Procedures' },
    { id: 'rotation-4', name: 'Conference' },
  ],
};

/**
 * Mock API responses
 */
export const heatmapMockResponses = {
  heatmapData: heatmapMockFactories.heatmapResponse(),
  coverageHeatmap: heatmapMockFactories.coverageHeatmapResponse(),
  workloadHeatmap: heatmapMockFactories.workloadHeatmapResponse(),
  emptyHeatmap: heatmapMockFactories.heatmapResponse({
    heatmap: heatmapMockFactories.heatmapData({
      x_labels: [],
      y_labels: [],
      z_values: [],
    }),
  }),
  availableRotations: heatmapMockFactories.availableRotations(),
};
