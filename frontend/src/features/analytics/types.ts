/**
 * Analytics Dashboard Types and Interfaces
 *
 * Defines the data structures for the analytics dashboard,
 * including metrics, trends, and version comparisons.
 */

// ============================================================================
// Core Metrics Types
// ============================================================================

/**
 * Status indicator for metrics
 */
export type MetricStatus = 'excellent' | 'good' | 'warning' | 'critical';

/**
 * Trend direction for metrics
 */
export type TrendDirection = 'up' | 'down' | 'stable';

/**
 * Metric category
 */
export type MetricCategory = 'fairness' | 'coverage' | 'compliance' | 'workload';

/**
 * Time period for trend analysis
 */
export type TimePeriod = '7d' | '30d' | '90d' | '180d' | '1y';

/**
 * Single metric value with metadata
 */
export interface Metric {
  name: string;
  value: number;
  unit: string;
  status: MetricStatus;
  trend: TrendDirection;
  trendValue: number; // Percentage change
  description: string;
  category: MetricCategory;
  threshold?: {
    warning: number;
    critical: number;
  };
}

/**
 * Current schedule metrics snapshot
 */
export interface ScheduleMetrics {
  fairnessScore: Metric;
  giniCoefficient: Metric;
  workloadVariance: Metric;
  pgyEquityScore: Metric;
  coverageScore: Metric;
  complianceScore: Metric;
  acgmeViolations: Metric;
  lastUpdated: string; // ISO datetime
}

// ============================================================================
// Fairness Trend Types
// ============================================================================

/**
 * Single data point for fairness trend
 */
export interface FairnessTrendPoint {
  date: string; // ISO date
  giniCoefficient: number;
  workloadVariance: number;
  pgyEquityScore: number;
  fairnessScore: number;
}

/**
 * Fairness trend data over time
 */
export interface FairnessTrendData {
  period: TimePeriod;
  dataPoints: FairnessTrendPoint[];
  statistics: {
    avgGini: number;
    avgVariance: number;
    avgPgyEquity: number;
    trend: TrendDirection;
    improvementRate: number; // Percentage
  };
}

/**
 * PGY level equity data
 */
export interface PgyEquityData {
  pgyLevel: number;
  averageShifts: number;
  nightShifts: number;
  weekendShifts: number;
  holidayShifts: number;
  workloadScore: number;
  fairnessScore: number;
}

// ============================================================================
// Version Comparison Types
// ============================================================================

/**
 * Schedule version metadata
 */
export interface ScheduleVersion {
  id: string;
  name: string;
  createdAt: string; // ISO datetime
  createdBy: string;
  description?: string;
  metrics: ScheduleMetrics;
  status: 'draft' | 'active' | 'archived';
}

/**
 * Comparison between two versions
 */
export interface VersionComparison {
  versionA: ScheduleVersion;
  versionB: ScheduleVersion;
  deltas: MetricDelta[];
  impactAssessment: ImpactAssessment;
  recommendation?: string;
}

/**
 * Delta between metric values
 */
export interface MetricDelta {
  metricName: string;
  category: MetricCategory;
  valueA: number;
  valueB: number;
  delta: number; // Difference
  deltaPercentage: number; // Percentage change
  improved: boolean;
  significance: 'major' | 'moderate' | 'minor';
}

/**
 * Impact assessment for version comparison
 */
export interface ImpactAssessment {
  overallImpact: 'positive' | 'negative' | 'neutral';
  fairnessImpact: number; // -100 to 100
  coverageImpact: number; // -100 to 100
  complianceImpact: number; // -100 to 100
  affectedResidents: number;
  riskLevel: 'low' | 'medium' | 'high';
  recommendations: string[];
}

// ============================================================================
// What-If Analysis Types
// ============================================================================

/**
 * Change type for what-if analysis
 */
export type ChangeType =
  | 'addShift'
  | 'removeShift'
  | 'swapShifts'
  | 'addConstraint'
  | 'modifyRotation'
  | 'adjustStaffing';

/**
 * Proposed change for what-if analysis
 */
export interface ProposedChange {
  type: ChangeType;
  description: string;
  parameters: Record<string, unknown>;
}

/**
 * What-if analysis request
 */
export interface WhatIfAnalysisRequest {
  baseVersionId: string;
  changes: ProposedChange[];
  analysisScope: 'immediate' | 'week' | 'month' | 'quarter';
}

/**
 * Predicted impact from what-if analysis
 */
export interface PredictedImpact {
  metrics: Partial<ScheduleMetrics>;
  comparisonToBaseline: MetricDelta[];
  warnings: Warning[];
  constraints: ConstraintImpact[];
  confidence: number; // 0-100
}

/**
 * Warning from what-if analysis
 */
export interface Warning {
  severity: 'info' | 'warning' | 'error';
  message: string;
  affectedEntity: string;
  suggestion?: string;
}

/**
 * Constraint impact
 */
export interface ConstraintImpact {
  constraintType: string;
  constraintName: string;
  currentValue: number;
  projectedValue: number;
  violated: boolean;
  violationSeverity?: 'minor' | 'major' | 'critical';
}

/**
 * Complete what-if analysis response
 */
export interface WhatIfAnalysisResult {
  requestId: string;
  request: WhatIfAnalysisRequest;
  predictedImpact: PredictedImpact;
  recommendation: {
    approved: boolean;
    reasoning: string;
    alternatives?: string[];
  };
  generatedAt: string; // ISO datetime
}

// ============================================================================
// Alert Types
// ============================================================================

/**
 * Alert priority
 */
export type AlertPriority = 'low' | 'medium' | 'high' | 'critical';

/**
 * Metric threshold alert
 */
export interface MetricAlert {
  id: string;
  metricName: string;
  category: MetricCategory;
  currentValue: number;
  thresholdValue: number;
  priority: AlertPriority;
  message: string;
  triggeredAt: string; // ISO datetime
  acknowledged: boolean;
}

// ============================================================================
// Dashboard State Types
// ============================================================================

/**
 * Date range for analytics
 */
export interface DateRange {
  start: string; // ISO date
  end: string; // ISO date
}

/**
 * Analytics dashboard filters
 */
export interface AnalyticsFilters {
  dateRange?: DateRange;
  timePeriod: TimePeriod;
  metricCategories: MetricCategory[];
  pgyLevels?: number[];
}

/**
 * Analytics dashboard state
 */
export interface AnalyticsDashboardState {
  filters: AnalyticsFilters;
  selectedMetrics: string[];
  viewMode: 'overview' | 'detailed' | 'comparison';
  comparisonVersions?: [string, string]; // Version IDs
}

// ============================================================================
// Constants
// ============================================================================

/**
 * Metric status colors
 */
export const METRIC_STATUS_COLORS: Record<MetricStatus, string> = {
  excellent: 'green',
  good: 'blue',
  warning: 'yellow',
  critical: 'red',
};

/**
 * Metric category labels
 */
export const METRIC_CATEGORY_LABELS: Record<MetricCategory, string> = {
  fairness: 'Fairness',
  coverage: 'Coverage',
  compliance: 'Compliance',
  workload: 'Workload',
};

/**
 * Time period labels
 */
export const TIME_PERIOD_LABELS: Record<TimePeriod, string> = {
  '7d': 'Last 7 Days',
  '30d': 'Last 30 Days',
  '90d': 'Last 90 Days',
  '180d': 'Last 6 Months',
  '1y': 'Last Year',
};

/**
 * Alert priority colors
 */
export const ALERT_PRIORITY_COLORS: Record<AlertPriority, string> = {
  low: 'blue',
  medium: 'yellow',
  high: 'orange',
  critical: 'red',
};

/**
 * Change type labels
 */
export const CHANGE_TYPE_LABELS: Record<ChangeType, string> = {
  addShift: 'Add Shift',
  removeShift: 'Remove Shift',
  swapShifts: 'Swap Shifts',
  addConstraint: 'Add Constraint',
  modifyRotation: 'Modify Rotation',
  adjustStaffing: 'Adjust Staffing',
};

/**
 * Default time period
 */
export const DEFAULT_TIME_PERIOD: TimePeriod = '30d';

/**
 * Default filters
 */
export const DEFAULT_FILTERS: AnalyticsFilters = {
  timePeriod: DEFAULT_TIME_PERIOD,
  metricCategories: ['fairness', 'coverage', 'compliance', 'workload'],
};
