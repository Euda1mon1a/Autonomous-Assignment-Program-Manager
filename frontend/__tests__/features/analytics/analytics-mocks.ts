/**
 * Mock data factories for analytics tests
 * Provides reusable mock data for analytics-related tests
 */

import type {
  Metric,
  ScheduleMetrics,
  FairnessTrendData,
  FairnessTrendPoint,
  PgyEquityData,
  ScheduleVersion,
  VersionComparison,
  MetricDelta,
  ImpactAssessment,
  WhatIfAnalysisRequest,
  WhatIfAnalysisResult,
  PredictedImpact,
  ProposedChange,
  Warning,
  ConstraintImpact,
  MetricAlert,
  MetricStatus,
  TrendDirection,
  MetricCategory,
} from '@/features/analytics/types';

/**
 * Mock data factories
 */
export const analyticsMockFactories = {
  metric: (overrides: Partial<Metric> = {}): Metric => ({
    name: 'Fairness Score',
    value: 85.5,
    unit: 'score',
    status: 'good' as MetricStatus,
    trend: 'up' as TrendDirection,
    trendValue: 2.3,
    description: 'Overall schedule fairness metric',
    category: 'fairness' as MetricCategory,
    threshold: {
      warning: 70,
      critical: 50,
    },
    ...overrides,
  }),

  scheduleMetrics: (overrides: Partial<ScheduleMetrics> = {}): ScheduleMetrics => ({
    fairnessScore: analyticsMockFactories.metric({
      name: 'Fairness Score',
      value: 85.5,
      category: 'fairness',
      status: 'good',
    }),
    giniCoefficient: analyticsMockFactories.metric({
      name: 'Gini Coefficient',
      value: 0.25,
      category: 'fairness',
      status: 'excellent',
      trend: 'down',
      trendValue: -1.5,
    }),
    workloadVariance: analyticsMockFactories.metric({
      name: 'Workload Variance',
      value: 12.5,
      category: 'workload',
      status: 'good',
    }),
    pgyEquityScore: analyticsMockFactories.metric({
      name: 'PGY Equity Score',
      value: 78.2,
      category: 'fairness',
      status: 'good',
    }),
    coverageScore: analyticsMockFactories.metric({
      name: 'Coverage Score',
      value: 95.8,
      unit: '%',
      category: 'coverage',
      status: 'excellent',
    }),
    complianceScore: analyticsMockFactories.metric({
      name: 'Compliance Score',
      value: 92.3,
      unit: '%',
      category: 'compliance',
      status: 'excellent',
    }),
    acgmeViolations: analyticsMockFactories.metric({
      name: 'ACGME Violations',
      value: 2,
      unit: 'violations',
      category: 'compliance',
      status: 'warning',
      trend: 'down',
      trendValue: -33.3,
    }),
    lastUpdated: '2024-02-15T10:30:00Z',
    ...overrides,
  }),

  fairnessTrendPoint: (overrides: Partial<FairnessTrendPoint> = {}): FairnessTrendPoint => ({
    date: '2024-02-01',
    giniCoefficient: 0.25,
    workloadVariance: 12.5,
    pgyEquityScore: 78.2,
    fairnessScore: 85.5,
    ...overrides,
  }),

  fairnessTrendData: (overrides: Partial<FairnessTrendData> = {}): FairnessTrendData => ({
    period: '30d',
    dataPoints: [
      analyticsMockFactories.fairnessTrendPoint({ date: '2024-02-01' }),
      analyticsMockFactories.fairnessTrendPoint({
        date: '2024-02-08',
        giniCoefficient: 0.24,
        fairnessScore: 86.2,
      }),
      analyticsMockFactories.fairnessTrendPoint({
        date: '2024-02-15',
        giniCoefficient: 0.23,
        fairnessScore: 87.0,
      }),
    ],
    statistics: {
      avgGini: 0.24,
      avgVariance: 12.3,
      avgPgyEquity: 78.5,
      trend: 'up',
      improvementRate: 1.8,
    },
    ...overrides,
  }),

  pgyEquityData: (overrides: Partial<PgyEquityData> = {}): PgyEquityData => ({
    pgyLevel: 1,
    averageShifts: 20,
    nightShifts: 5,
    weekendShifts: 4,
    holidayShifts: 1,
    workloadScore: 85.0,
    fairnessScore: 88.5,
    ...overrides,
  }),

  scheduleVersion: (overrides: Partial<ScheduleVersion> = {}): ScheduleVersion => ({
    id: 'version-1',
    name: 'February Schedule v1',
    createdAt: '2024-02-01T09:00:00Z',
    createdBy: 'admin@hospital.org',
    description: 'Initial February schedule',
    metrics: analyticsMockFactories.scheduleMetrics(),
    status: 'active',
    ...overrides,
  }),

  metricDelta: (overrides: Partial<MetricDelta> = {}): MetricDelta => ({
    metricName: 'Fairness Score',
    category: 'fairness',
    valueA: 85.5,
    valueB: 88.2,
    delta: 2.7,
    deltaPercentage: 3.16,
    improved: true,
    significance: 'moderate',
    ...overrides,
  }),

  impactAssessment: (overrides: Partial<ImpactAssessment> = {}): ImpactAssessment => ({
    overallImpact: 'positive',
    fairnessImpact: 15,
    coverageImpact: 10,
    complianceImpact: 5,
    affectedResidents: 12,
    riskLevel: 'low',
    recommendations: [
      'This change improves overall fairness',
      'Monitor PGY-1 workload distribution',
    ],
    ...overrides,
  }),

  versionComparison: (overrides: Partial<VersionComparison> = {}): VersionComparison => ({
    versionA: analyticsMockFactories.scheduleVersion({ id: 'v1', name: 'Version A' }),
    versionB: analyticsMockFactories.scheduleVersion({ id: 'v2', name: 'Version B' }),
    deltas: [
      analyticsMockFactories.metricDelta(),
      analyticsMockFactories.metricDelta({
        metricName: 'Gini Coefficient',
        valueA: 0.25,
        valueB: 0.22,
        delta: -0.03,
        deltaPercentage: -12.0,
        improved: true,
      }),
    ],
    impactAssessment: analyticsMockFactories.impactAssessment(),
    recommendation: 'Version B shows improved fairness metrics',
    ...overrides,
  }),

  proposedChange: (overrides: Partial<ProposedChange> = {}): ProposedChange => ({
    type: 'add_shift',
    description: 'Add extra night shift coverage',
    parameters: {
      resident_id: 'resident-123',
      date: '2024-02-15',
      shift_type: 'night',
    },
    ...overrides,
  }),

  warning: (overrides: Partial<Warning> = {}): Warning => ({
    severity: 'warning',
    message: 'This change may increase workload variance',
    affectedEntity: 'PGY-1 Residents',
    suggestion: 'Consider redistributing shifts across PGY levels',
    ...overrides,
  }),

  constraintImpact: (overrides: Partial<ConstraintImpact> = {}): ConstraintImpact => ({
    constraintType: 'ACGME',
    constraintName: '80-hour weekly limit',
    currentValue: 75.0,
    projectedValue: 78.5,
    violated: false,
    ...overrides,
  }),

  predictedImpact: (overrides: Partial<PredictedImpact> = {}): PredictedImpact => ({
    metrics: {
      fairnessScore: analyticsMockFactories.metric({ value: 86.0 }),
    },
    comparisonToBaseline: [
      analyticsMockFactories.metricDelta({
        metricName: 'Fairness Score',
        valueA: 85.5,
        valueB: 86.0,
        delta: 0.5,
        deltaPercentage: 0.58,
        improved: true,
        significance: 'minor',
      }),
    ],
    warnings: [analyticsMockFactories.warning()],
    constraints: [analyticsMockFactories.constraintImpact()],
    confidence: 85,
    ...overrides,
  }),

  whatIfAnalysisRequest: (overrides: Partial<WhatIfAnalysisRequest> = {}): WhatIfAnalysisRequest => ({
    baseVersionId: 'version-1',
    changes: [analyticsMockFactories.proposedChange()],
    analysisScope: 'week',
    ...overrides,
  }),

  whatIfAnalysisResult: (overrides: Partial<WhatIfAnalysisResult> = {}): WhatIfAnalysisResult => ({
    requestId: 'request-123',
    request: analyticsMockFactories.whatIfAnalysisRequest(),
    predictedImpact: analyticsMockFactories.predictedImpact(),
    recommendation: {
      approved: true,
      reasoning: 'Change improves fairness with minimal risk',
      alternatives: ['Consider adding shift on different date'],
    },
    generatedAt: '2024-02-15T11:00:00Z',
    ...overrides,
  }),

  metricAlert: (overrides: Partial<MetricAlert> = {}): MetricAlert => ({
    id: 'alert-1',
    metricName: 'Fairness Score',
    category: 'fairness',
    currentValue: 65.5,
    thresholdValue: 70.0,
    priority: 'medium',
    message: 'Fairness score has dropped below warning threshold',
    triggeredAt: '2024-02-15T09:30:00Z',
    acknowledged: false,
    ...overrides,
  }),
};

/**
 * Mock API responses
 */
export const analyticsMockResponses = {
  currentMetrics: analyticsMockFactories.scheduleMetrics(),

  fairnessTrend: analyticsMockFactories.fairnessTrendData(),

  pgyEquity: [
    analyticsMockFactories.pgyEquityData({ pgyLevel: 1, averageShifts: 20 }),
    analyticsMockFactories.pgyEquityData({ pgyLevel: 2, averageShifts: 22 }),
    analyticsMockFactories.pgyEquityData({ pgyLevel: 3, averageShifts: 21 }),
  ],

  versions: [
    { id: 'v1', name: 'Version 1', createdAt: '2024-02-01T09:00:00Z', status: 'active' },
    { id: 'v2', name: 'Version 2', createdAt: '2024-02-08T10:00:00Z', status: 'draft' },
    { id: 'v3', name: 'Version 3', createdAt: '2024-02-15T11:00:00Z', status: 'archived' },
  ],

  versionComparison: analyticsMockFactories.versionComparison(),

  alerts: [
    analyticsMockFactories.metricAlert(),
    analyticsMockFactories.metricAlert({
      id: 'alert-2',
      metricName: 'ACGME Violations',
      category: 'compliance',
      priority: 'high',
      currentValue: 5,
      thresholdValue: 3,
      acknowledged: false,
    }),
  ],

  whatIfAnalysis: analyticsMockFactories.whatIfAnalysisResult(),
};
