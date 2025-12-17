/**
 * Analytics Feature Module
 *
 * Provides comprehensive analytics dashboard for monitoring schedule
 * fairness, coverage, compliance metrics, and predictive analysis.
 *
 * Components:
 * - AnalyticsDashboard: Main dashboard with overview, trends, comparison, and what-if views
 * - MetricsCard: Reusable card for displaying metrics with status and trends
 * - FairnessTrend: Line chart visualization for fairness metrics over time
 * - VersionComparison: Side-by-side comparison of schedule versions
 * - WhatIfAnalysis: Predictive impact analysis for proposed changes
 *
 * Hooks:
 * - useCurrentMetrics: Fetch current schedule metrics snapshot
 * - useFairnessTrend: Fetch fairness trend data over time
 * - usePgyEquity: Fetch PGY level equity comparison data
 * - useVersionComparison: Compare two schedule versions
 * - useScheduleVersions: Fetch available schedule versions
 * - useMetricAlerts: Fetch metric threshold alerts
 * - useWhatIfAnalysis: Submit what-if analysis request
 * - useAcknowledgeAlert: Acknowledge a metric alert
 * - useDismissAlert: Dismiss a metric alert
 * - useExportAnalytics: Export analytics data
 * - useRefreshMetrics: Force refresh metrics calculation
 */

// Components
export { AnalyticsDashboard } from './AnalyticsDashboard';
export { MetricsCard, MetricsCardSkeleton } from './MetricsCard';
export { FairnessTrend } from './FairnessTrend';
export { VersionComparison } from './VersionComparison';
export { WhatIfAnalysis } from './WhatIfAnalysis';

// Hooks
export {
  useCurrentMetrics,
  useFairnessTrend,
  usePgyEquity,
  useVersionComparison,
  useScheduleVersions,
  useMetricAlerts,
  useWhatIfAnalysisResult,
  useWhatIfAnalysis,
  useAcknowledgeAlert,
  useDismissAlert,
  useExportAnalytics,
  useRefreshMetrics,
  usePrefetchFairnessTrend,
  usePrefetchVersionComparison,
  analyticsQueryKeys,
} from './hooks';

// Types
export type {
  MetricStatus,
  TrendDirection,
  MetricCategory,
  TimePeriod,
  Metric,
  ScheduleMetrics,
  FairnessTrendPoint,
  FairnessTrendData,
  PgyEquityData,
  ScheduleVersion,
  VersionComparison as VersionComparisonType,
  MetricDelta,
  ImpactAssessment,
  ChangeType,
  ProposedChange,
  WhatIfAnalysisRequest,
  PredictedImpact,
  Warning,
  ConstraintImpact,
  WhatIfAnalysisResult,
  AlertPriority,
  MetricAlert,
  DateRange,
  AnalyticsFilters,
  AnalyticsDashboardState,
} from './types';

// Constants
export {
  METRIC_STATUS_COLORS,
  METRIC_CATEGORY_LABELS,
  TIME_PERIOD_LABELS,
  ALERT_PRIORITY_COLORS,
  CHANGE_TYPE_LABELS,
  DEFAULT_TIME_PERIOD,
  DEFAULT_FILTERS,
} from './types';
