'use client';

/**
 * AnalyticsDashboard Component
 *
 * Main analytics dashboard with overview cards, trend charts,
 * quick stats summary, and alert cards for metric thresholds.
 */

import { useState } from 'react';
import {
  BarChart3,
  TrendingUp,
  Activity,
  AlertCircle,
  RefreshCw,
  Download,
  X,
  Eye,
  EyeOff,
  ChevronDown,
  ChevronUp,
} from 'lucide-react';
import { MetricsCard, MetricsCardSkeleton } from './MetricsCard';
import { FairnessTrend } from './FairnessTrend';
import { VersionComparison } from './VersionComparison';
import { WhatIfAnalysis } from './WhatIfAnalysis';
import {
  useCurrentMetrics,
  useMetricAlerts,
  useRefreshMetrics,
  useAcknowledgeAlert,
  useDismissAlert,
  useExportAnalytics,
} from './hooks';
import type { MetricCategory, TimePeriod, AlertPriority } from './types';
import { TIME_PERIOD_LABELS, ALERT_PRIORITY_COLORS, DEFAULT_TIME_PERIOD } from './types';

// ============================================================================
// Types
// ============================================================================

interface AnalyticsDashboardProps {
  className?: string;
}

type DashboardView = 'overview' | 'trends' | 'comparison' | 'whatif';

// ============================================================================
// Sub-Components
// ============================================================================

/**
 * View navigation tabs
 */
function ViewTabs({
  currentView,
  onViewChange,
}: {
  currentView: DashboardView;
  onViewChange: (view: DashboardView) => void;
}) {
  const tabs: Array<{ value: DashboardView; label: string; icon: React.ReactNode }> = [
    { value: 'overview', label: 'Overview', icon: <BarChart3 className="w-4 h-4" /> },
    { value: 'trends', label: 'Trends', icon: <TrendingUp className="w-4 h-4" /> },
    { value: 'comparison', label: 'Compare Versions', icon: <Activity className="w-4 h-4" /> },
    { value: 'whatif', label: 'What-If Analysis', icon: <AlertCircle className="w-4 h-4" /> },
  ];

  return (
    <div className="flex items-center gap-1 bg-gray-100 rounded-lg p-1 overflow-x-auto">
      {tabs.map((tab) => (
        <button
          key={tab.value}
          type="button"
          onClick={() => onViewChange(tab.value)}
          className={`
            flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-colors whitespace-nowrap
            ${
              currentView === tab.value
                ? 'bg-white text-blue-600 shadow-sm'
                : 'text-gray-600 hover:text-gray-900'
            }
          `}
        >
          {tab.icon}
          <span className="hidden sm:inline">{tab.label}</span>
        </button>
      ))}
    </div>
  );
}

/**
 * Quick stats summary
 */
function QuickStats({
  totalMetrics,
  excellentCount,
  warningCount,
  criticalCount,
}: {
  totalMetrics: number;
  excellentCount: number;
  warningCount: number;
  criticalCount: number;
}) {
  return (
    <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
      <div className="p-4 bg-white border border-gray-200 rounded-lg">
        <p className="text-xs text-gray-600 mb-1">Total Metrics</p>
        <p className="text-2xl font-bold text-gray-900">{totalMetrics}</p>
      </div>
      <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
        <p className="text-xs text-green-700 mb-1">Excellent</p>
        <p className="text-2xl font-bold text-green-900">{excellentCount}</p>
      </div>
      <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
        <p className="text-xs text-yellow-700 mb-1">Warnings</p>
        <p className="text-2xl font-bold text-yellow-900">{warningCount}</p>
      </div>
      <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
        <p className="text-xs text-red-700 mb-1">Critical</p>
        <p className="text-2xl font-bold text-red-900">{criticalCount}</p>
      </div>
    </div>
  );
}

/**
 * Alert card
 */
function AlertCard({
  alert,
  onAcknowledge,
  onDismiss,
}: {
  alert: {
    id: string;
    metricName: string;
    currentValue: number;
    thresholdValue: number;
    priority: AlertPriority;
    message: string;
    triggeredAt: string;
    acknowledged: boolean;
  };
  onAcknowledge: (id: string) => void;
  onDismiss: (id: string) => void;
}) {
  const [expanded, setExpanded] = useState(false);

  const priorityConfig = {
    low: { bg: 'bg-blue-50 border-blue-200', text: 'text-blue-900' },
    medium: { bg: 'bg-yellow-50 border-yellow-200', text: 'text-yellow-900' },
    high: { bg: 'bg-orange-50 border-orange-200', text: 'text-orange-900' },
    critical: { bg: 'bg-red-50 border-red-200', text: 'text-red-900' },
  };

  const config = priorityConfig[alert.priority];

  return (
    <div className={`border-2 rounded-lg ${config.bg}`}>
      <div className="p-4">
        <div className="flex items-start justify-between mb-2">
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-1">
              <span
                className={`px-2 py-1 text-xs font-bold uppercase rounded ${
                  ALERT_PRIORITY_COLORS[alert.priority] === 'blue'
                    ? 'bg-blue-100 text-blue-700'
                    : ALERT_PRIORITY_COLORS[alert.priority] === 'yellow'
                    ? 'bg-yellow-100 text-yellow-700'
                    : ALERT_PRIORITY_COLORS[alert.priority] === 'orange'
                    ? 'bg-orange-100 text-orange-700'
                    : 'bg-red-100 text-red-700'
                }`}
              >
                {alert.priority}
              </span>
              {alert.acknowledged && (
                <span className="px-2 py-1 text-xs font-medium bg-gray-200 text-gray-700 rounded">
                  Acknowledged
                </span>
              )}
            </div>
            <h4 className={`text-sm font-semibold ${config.text}`}>{alert.metricName}</h4>
            <p className="text-sm text-gray-700 mt-1">{alert.message}</p>
          </div>
          <button
            type="button"
            onClick={() => setExpanded(!expanded)}
            className="p-1 hover:bg-white rounded transition-colors"
          >
            {expanded ? <ChevronUp className="w-5 h-5" /> : <ChevronDown className="w-5 h-5" />}
          </button>
        </div>

        {expanded && (
          <div className="mt-4 pt-4 border-t border-gray-300 space-y-3">
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <p className="text-gray-600">Current Value</p>
                <p className="font-semibold text-gray-900">{alert.currentValue.toFixed(2)}</p>
              </div>
              <div>
                <p className="text-gray-600">Threshold</p>
                <p className="font-semibold text-gray-900">{alert.thresholdValue.toFixed(2)}</p>
              </div>
            </div>
            <div className="text-sm">
              <p className="text-gray-600">Triggered</p>
              <p className="font-semibold text-gray-900">
                {new Date(alert.triggeredAt).toLocaleString()}
              </p>
            </div>
            <div className="flex gap-2">
              {!alert.acknowledged && (
                <button
                  type="button"
                  onClick={() => onAcknowledge(alert.id)}
                  className="flex-1 px-3 py-2 bg-white border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors text-sm font-medium"
                >
                  Acknowledge
                </button>
              )}
              <button
                type="button"
                onClick={() => onDismiss(alert.id)}
                className="flex-1 px-3 py-2 bg-white border border-gray-300 text-red-600 rounded-lg hover:bg-red-50 transition-colors text-sm font-medium"
              >
                Dismiss
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

/**
 * Alerts section
 */
function AlertsSection({ className = '' }: { className?: string }) {
  const [showAcknowledged, setShowAcknowledged] = useState(false);
  const { data: alerts, isLoading } = useMetricAlerts(showAcknowledged ? undefined : false);
  const { mutate: acknowledgeAlert } = useAcknowledgeAlert();
  const { mutate: dismissAlert } = useDismissAlert();

  if (isLoading) {
    return (
      <div className={`bg-white border border-gray-200 rounded-lg p-6 ${className}`}>
        <div className="animate-pulse">
          <div className="h-6 bg-gray-300 rounded w-32 mb-4" />
          <div className="space-y-3">
            <div className="h-24 bg-gray-200 rounded" />
            <div className="h-24 bg-gray-200 rounded" />
          </div>
        </div>
      </div>
    );
  }

  const activeAlerts = alerts?.filter((a) => !a.acknowledged) || [];
  const acknowledgedAlerts = alerts?.filter((a) => a.acknowledged) || [];

  return (
    <div className={`bg-white border border-gray-200 rounded-lg p-6 ${className}`}>
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">Metric Alerts</h3>
          <p className="text-sm text-gray-600">
            {activeAlerts.length} active alert{activeAlerts.length !== 1 ? 's' : ''}
          </p>
        </div>
        <button
          type="button"
          onClick={() => setShowAcknowledged(!showAcknowledged)}
          className="flex items-center gap-2 px-3 py-1.5 text-sm text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
        >
          {showAcknowledged ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
          {showAcknowledged ? 'Hide' : 'Show'} Acknowledged
        </button>
      </div>

      {alerts && alerts.length > 0 ? (
        <div className="space-y-3">
          {activeAlerts.map((alert) => (
            <AlertCard
              key={alert.id}
              alert={alert}
              onAcknowledge={acknowledgeAlert}
              onDismiss={dismissAlert}
            />
          ))}
          {showAcknowledged &&
            acknowledgedAlerts.map((alert) => (
              <AlertCard
                key={alert.id}
                alert={alert}
                onAcknowledge={acknowledgeAlert}
                onDismiss={dismissAlert}
              />
            ))}
        </div>
      ) : (
        <div className="text-center py-8 text-gray-500">
          <AlertCircle className="w-12 h-12 mx-auto mb-3 text-gray-400" />
          <p>No alerts at this time</p>
        </div>
      )}
    </div>
  );
}

// ============================================================================
// Main Component
// ============================================================================

export function AnalyticsDashboard({ className = '' }: AnalyticsDashboardProps) {
  const [currentView, setCurrentView] = useState<DashboardView>('overview');

  const { data: metrics, isLoading: metricsLoading, error: metricsError } = useCurrentMetrics();
  const { mutate: refreshMetrics, isPending: isRefreshing } = useRefreshMetrics();
  const { mutate: exportAnalytics, isPending: isExporting } = useExportAnalytics();

  const handleRefresh = () => {
    refreshMetrics();
  };

  const handleExport = () => {
    exportAnalytics({
      format: 'pdf',
      includeCharts: true,
    });
  };

  // Calculate quick stats
  const metricsArray = metrics
    ? [
        metrics.fairnessScore,
        metrics.giniCoefficient,
        metrics.workloadVariance,
        metrics.pgyEquityScore,
        metrics.coverageScore,
        metrics.complianceScore,
        metrics.acgmeViolations,
      ]
    : [];

  const excellentCount = metricsArray.filter((m) => m.status === 'excellent').length;
  const warningCount = metricsArray.filter((m) => m.status === 'warning').length;
  const criticalCount = metricsArray.filter((m) => m.status === 'critical').length;

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Header */}
      <div className="bg-white border border-gray-200 rounded-lg p-6">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 mb-6">
          <div>
            <h1 className="text-2xl font-bold text-gray-900 mb-1">Analytics Dashboard</h1>
            <p className="text-sm text-gray-600">
              Monitor schedule fairness, coverage, and compliance metrics
            </p>
          </div>
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={handleRefresh}
              disabled={isRefreshing}
              className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:bg-gray-300"
            >
              <RefreshCw className={`w-4 h-4 ${isRefreshing ? 'animate-spin' : ''}`} />
              <span className="hidden sm:inline">Refresh</span>
            </button>
            <button
              type="button"
              onClick={handleExport}
              disabled={isExporting}
              className="flex items-center gap-2 px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors"
            >
              <Download className="w-4 h-4" />
              <span className="hidden sm:inline">Export</span>
            </button>
          </div>
        </div>

        {/* View Navigation */}
        <ViewTabs currentView={currentView} onViewChange={setCurrentView} />
      </div>

      {/* Content based on view */}
      {currentView === 'overview' && (
        <>
          {/* Quick Stats */}
          {metrics && (
            <QuickStats
              totalMetrics={metricsArray.length}
              excellentCount={excellentCount}
              warningCount={warningCount}
              criticalCount={criticalCount}
            />
          )}

          {/* Metrics Grid */}
          <div>
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Key Metrics</h2>
            {metricsLoading ? (
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
                {[...Array(7)].map((_, i) => (
                  <MetricsCardSkeleton key={i} />
                ))}
              </div>
            ) : metricsError ? (
              <div className="bg-red-50 border border-red-200 rounded-lg p-6">
                <p className="text-sm text-red-600">Failed to load metrics</p>
              </div>
            ) : metrics ? (
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
                <MetricsCard metric={metrics.fairnessScore} />
                <MetricsCard metric={metrics.giniCoefficient} />
                <MetricsCard metric={metrics.workloadVariance} />
                <MetricsCard metric={metrics.pgyEquityScore} />
                <MetricsCard metric={metrics.coverageScore} />
                <MetricsCard metric={metrics.complianceScore} />
                <MetricsCard metric={metrics.acgmeViolations} />
              </div>
            ) : null}
          </div>

          {/* Alerts Section */}
          <AlertsSection />

          {/* Quick Trend Preview */}
          <div>
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Fairness Trends</h2>
            <FairnessTrend months={1} showPgyComparison={false} />
          </div>
        </>
      )}

      {currentView === 'trends' && (
        <div>
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Detailed Trends</h2>
          <FairnessTrend months={3} showPgyComparison={true} />
        </div>
      )}

      {currentView === 'comparison' && (
        <div>
          <VersionComparison />
        </div>
      )}

      {currentView === 'whatif' && (
        <div>
          <WhatIfAnalysis />
        </div>
      )}
    </div>
  );
}
