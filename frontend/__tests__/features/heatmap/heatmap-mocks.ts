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
    xLabels: ['2024-01-01', '2024-01-02', '2024-01-03', '2024-01-04', '2024-01-05'],
    yLabels: ['Clinic', 'Inpatient', 'Procedures', 'Conference'],
    zValues: [
      [100, 80, 90, 100, 95],
      [90, 100, 85, 90, 100],
      [75, 60, 80, 70, 85],
      [100, 100, 100, 100, 100],
    ],
    colorScale: heatmapMockFactories.colorScale(),
    annotations: [],
    title: 'Coverage Heatmap',
    xAxisLabel: 'Date',
    yAxisLabel: 'Rotation',
    ...overrides,
  }),

  dateRange: (overrides: Partial<DateRange> = {}): DateRange => ({
    start: '2024-01-01',
    end: '2024-01-31',
    ...overrides,
  }),

  filters: (overrides: Partial<HeatmapFilters> = {}): HeatmapFilters => ({
    startDate: '2024-01-01',
    endDate: '2024-01-31',
    personIds: [],
    rotationIds: [],
    includeFmit: true,
    groupBy: 'person',
    ...overrides,
  }),

  coverageMetrics: (overrides: Partial<CoverageMetrics> = {}): CoverageMetrics => ({
    totalSlots: 100,
    filledSlots: 95,
    coveragePercentage: 95.0,
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
    personId: 'person-1',
    personName: 'Dr. John Smith',
    totalAssignments: 20,
    totalHours: 75.0,
    blocksByRotation: {
      'Clinic': 8,
      'Inpatient': 12,
    },
    averageWeeklyHours: 37.5,
    ...overrides,
  }),

  heatmapResponse: (overrides: Partial<HeatmapResponse> = {}): HeatmapResponse => ({
    heatmap: heatmapMockFactories.heatmapData(),
    metadata: {
      generatedAt: '2024-02-15T10:30:00Z',
      filtersApplied: true,
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
      yLabels: ['Dr. John Smith', 'Dr. Jane Doe', 'Dr. Bob Wilson'],
      zValues: [
        [40, 45, 38, 42, 40],
        [38, 40, 42, 39, 41],
        [42, 43, 41, 40, 39],
      ],
    }),
    metrics: [
      heatmapMockFactories.workloadMetrics(),
      heatmapMockFactories.workloadMetrics({
        personId: 'person-2',
        personName: 'Dr. Jane Doe',
        totalAssignments: 18,
        totalHours: 72.0,
      }),
    ],
    ...overrides,
  }),

  exportConfig: (overrides: Partial<HeatmapExportConfig> = {}): HeatmapExportConfig => ({
    format: 'png',
    width: 1200,
    height: 800,
    title: 'Heatmap Export',
    includeLegend: true,
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
      xLabels: [],
      yLabels: [],
      zValues: [],
    }),
  }),
  availableRotations: heatmapMockFactories.availableRotations(),
};
