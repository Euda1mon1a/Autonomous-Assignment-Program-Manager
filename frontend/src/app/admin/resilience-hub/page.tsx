'use client';

/**
 * Resilience Hub - Consolidated System Health & Compliance Dashboard
 *
 * Combines 3 previously fragmented pages into a single command center:
 * - Tab 1: Overview - System health, defense level, N-1/N-2 status
 * - Tab 2: Circuit Breakers - Netflix Hystrix pattern monitoring
 * - Tab 3: Fairness - Workload equity analysis (Jain's index, Gini)
 * - Tab 4: Compliance - MTF compliance, risk patterns, critical faculty
 *
 * @module admin/resilience-hub
 */
import { useState, useCallback } from 'react';
import {
  Activity,
  Shield,
  Scale,
  FileCheck,
  RefreshCw,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  Zap,
  TrendingUp,
  TrendingDown,
  Users,
  Clock,
} from 'lucide-react';

// Hooks
import {
  useSystemHealth,
  useVulnerabilityReport,
  useCircuitBreakers,
  useBreakerHealth,
  useMTFCompliance,
  useUnifiedCriticalIndex,
} from '@/hooks';
import { useFairnessAudit } from '@/hooks/useFairness';

// Existing resilience components
import { DefenseLevel } from '@/components/resilience/DefenseLevel';
import { UtilizationGauge } from '@/components/resilience/UtilizationGauge';
import { BurnoutRtDisplay } from '@/components/resilience/BurnoutRtDisplay';
import { N1ContingencyMap } from '@/components/resilience/N1ContingencyMap';

// Types
import type { CircuitState } from '@/types/resilience';

// ============================================================================
// Types
// ============================================================================

// Use string literal union instead of enum for simpler type checking
type StatusString = 'healthy' | 'warning' | 'degraded' | 'critical' | 'emergency';

type ResilienceTab = 'overview' | 'circuit-breakers' | 'fairness' | 'compliance';

interface TabConfig {
  id: ResilienceTab;
  label: string;
  icon: React.ElementType;
  description: string;
}

// ============================================================================
// Constants
// ============================================================================

const TABS: TabConfig[] = [
  {
    id: 'overview',
    label: 'Overview',
    icon: Activity,
    description: 'System health and defense status',
  },
  {
    id: 'circuit-breakers',
    label: 'Circuit Breakers',
    icon: Zap,
    description: 'Service health and failure isolation',
  },
  {
    id: 'fairness',
    label: 'Fairness',
    icon: Scale,
    description: 'Workload equity analysis',
  },
  {
    id: 'compliance',
    label: 'Compliance',
    icon: FileCheck,
    description: 'MTF compliance and risk assessment',
  },
];

const STATUS_COLORS: Record<StatusString, string> = {
  healthy: 'text-green-500 bg-green-500/10 border-green-500/30',
  warning: 'text-amber-500 bg-amber-500/10 border-amber-500/30',
  degraded: 'text-orange-500 bg-orange-500/10 border-orange-500/30',
  critical: 'text-red-500 bg-red-500/10 border-red-500/30',
  emergency: 'text-red-600 bg-red-600/20 border-red-600/50',
};

const CIRCUIT_STATE_COLORS: Record<CircuitState, string> = {
  closed: 'text-green-500 bg-green-500/10',
  open: 'text-red-500 bg-red-500/10',
  half_open: 'text-amber-500 bg-amber-500/10',
};

// ============================================================================
// Helper Components
// ============================================================================

function StatusBadge({ status, size = 'md' }: { status: StatusString; size?: 'sm' | 'md' | 'lg' }) {
  const sizeClasses = {
    sm: 'px-2 py-0.5 text-xs',
    md: 'px-3 py-1 text-sm',
    lg: 'px-4 py-1.5 text-base',
  };

  const Icon = status === 'healthy' ? CheckCircle2 : status === 'warning' ? AlertTriangle : XCircle;

  return (
    <span className={`inline-flex items-center gap-1.5 rounded-full border font-medium ${sizeClasses[size]} ${STATUS_COLORS[status]}`}>
      <Icon className="w-4 h-4" />
      {status.charAt(0).toUpperCase() + status.slice(1)}
    </span>
  );
}

function MetricCard({
  label,
  value,
  subValue,
  icon: Icon,
  trend,
  status,
}: {
  label: string;
  value: string | number;
  subValue?: string;
  icon: React.ElementType;
  trend?: 'up' | 'down' | 'stable';
  status?: StatusString;
}) {
  const trendColor = trend === 'up' ? 'text-green-400' : trend === 'down' ? 'text-red-400' : 'text-gray-400';
  const TrendIcon = trend === 'up' ? TrendingUp : trend === 'down' ? TrendingDown : null;

  return (
    <div className="bg-slate-800/50 border border-slate-700/50 rounded-lg p-4">
      <div className="flex items-center justify-between mb-2">
        <div className={`p-2 rounded-lg ${status ? STATUS_COLORS[status].split(' ')[1] : 'bg-slate-700/50'}`}>
          <Icon className={`w-5 h-5 ${status ? STATUS_COLORS[status].split(' ')[0] : 'text-slate-300'}`} />
        </div>
        {TrendIcon && <TrendIcon className={`w-4 h-4 ${trendColor}`} />}
      </div>
      <div className="text-2xl font-bold text-white">{value}</div>
      <div className="text-sm text-slate-300">{label}</div>
      {subValue && <div className="text-xs text-slate-400 mt-1">{subValue}</div>}
    </div>
  );
}

function LoadingSpinner() {
  return (
    <div className="flex items-center justify-center p-8">
      <RefreshCw className="w-8 h-8 text-blue-500 animate-spin" />
    </div>
  );
}

function ErrorMessage({ message }: { message: string }) {
  return (
    <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-4 text-red-400">
      <div className="flex items-center gap-2">
        <XCircle className="w-5 h-5" />
        <span>{message}</span>
      </div>
    </div>
  );
}

// ============================================================================
// Tab Content: Overview
// ============================================================================

function OverviewTab() {
  const { data: health, isLoading: healthLoading, error: healthError } = useSystemHealth();
  const { data: vulnerability } = useVulnerabilityReport({ include_n2: true });

  if (healthLoading) return <LoadingSpinner />;
  if (healthError) return <ErrorMessage message="Failed to load system health" />;

  return (
    <div className="space-y-6">
      {/* Quick Stats Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <MetricCard
          label="Overall Status"
          value={health?.overallStatus ? health.overallStatus.charAt(0).toUpperCase() + health.overallStatus.slice(1) : 'Unknown'}
          icon={Activity}
          status={health?.overallStatus}
        />
        <MetricCard
          label="Defense Level"
          value={health?.defenseLevel || 'Unknown'}
          icon={Shield}
          status={health?.crisisMode ? 'emergency' : 'healthy'}
        />
        <MetricCard
          label="N-1 Status"
          value={health?.n1Pass ? 'PASS' : 'FAIL'}
          icon={Users}
          status={health?.n1Pass ? 'healthy' : 'critical'}
        />
        <MetricCard
          label="N-2 Status"
          value={health?.n2Pass ? 'PASS' : 'FAIL'}
          icon={Users}
          status={health?.n2Pass ? 'healthy' : 'warning'}
        />
      </div>

      {/* Existing Components Row */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {health && (
          <>
            <div className="bg-slate-800/50 border border-slate-700/50 rounded-lg p-6">
              <h3 className="text-lg font-medium text-white mb-4">Defense Level</h3>
              <DefenseLevel level={health.defenseLevel} />
            </div>
            <div className="bg-slate-800/50 border border-slate-700/50 rounded-lg p-6">
              <h3 className="text-lg font-medium text-white mb-4">Utilization</h3>
              <UtilizationGauge
                utilizationRate={health.utilization?.utilizationRate || 0}
                level={health.utilization?.level || 'GREEN'}
              />
            </div>
          </>
        )}
        <div className="bg-slate-800/50 border border-slate-700/50 rounded-lg p-6">
          <h3 className="text-lg font-medium text-white mb-4">Burnout Risk</h3>
          <BurnoutRtDisplay />
        </div>
      </div>

      {/* N-1 Vulnerability Map */}
      {vulnerability && (
        <div className="bg-slate-800/50 border border-slate-700/50 rounded-lg p-6">
          <h3 className="text-lg font-medium text-white mb-4">N-1 Vulnerability Map</h3>
          <N1ContingencyMap vulnerabilities={vulnerability.n1Vulnerabilities} />
        </div>
      )}

      {/* Recommended Actions */}
      {health?.immediateActions && health.immediateActions.length > 0 && (
        <div className="bg-slate-800/50 border border-slate-700/50 rounded-lg p-6">
          <h3 className="text-lg font-medium text-white mb-4">Immediate Actions</h3>
          <ul className="space-y-2">
            {health.immediateActions.map((action, idx) => (
              <li key={idx} className="flex items-start gap-2 text-slate-300">
                <AlertTriangle className="w-5 h-5 text-amber-500 shrink-0 mt-0.5" />
                <span>{action}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

// ============================================================================
// Tab Content: Circuit Breakers
// ============================================================================

function CircuitBreakersTab() {
  const { data: breakers, isLoading, error } = useCircuitBreakers();
  const { data: health } = useBreakerHealth();

  if (isLoading) return <LoadingSpinner />;
  if (error) return <ErrorMessage message="Failed to load circuit breakers. API endpoint may not be available." />;

  return (
    <div className="space-y-6">
      {/* Summary Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <MetricCard
          label="Total Breakers"
          value={breakers?.totalBreakers || 0}
          icon={Zap}
        />
        <MetricCard
          label="Closed (Healthy)"
          value={breakers?.closedBreakers || 0}
          icon={CheckCircle2}
          status="healthy"
        />
        <MetricCard
          label="Open (Tripped)"
          value={breakers?.openBreakers || 0}
          icon={XCircle}
          status={breakers?.openBreakers ? 'critical' : 'healthy'}
        />
        <MetricCard
          label="Half-Open (Testing)"
          value={breakers?.halfOpenBreakers || 0}
          icon={AlertTriangle}
          status={breakers?.halfOpenBreakers ? 'warning' : 'healthy'}
        />
      </div>

      {/* Health Metrics */}
      {health && (
        <div className="bg-slate-800/50 border border-slate-700/50 rounded-lg p-6">
          <h3 className="text-lg font-medium text-white mb-4">Health Metrics</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div>
              <div className="text-sm text-slate-400">Overall Failure Rate</div>
              <div className="text-xl font-bold text-white">
                {((health.metrics?.overallFailureRate || 0) * 100).toFixed(1)}%
              </div>
            </div>
            <div>
              <div className="text-sm text-slate-400">Trend</div>
              <div className="text-xl font-bold text-white">{health.trendAnalysis || 'N/A'}</div>
            </div>
            <div>
              <div className="text-sm text-slate-400">Severity</div>
              <StatusBadge status={(health.severity as StatusString) || 'healthy'} size="sm" />
            </div>
            <div>
              <div className="text-sm text-slate-400">Needs Attention</div>
              <div className="text-xl font-bold text-white">
                {health.breakersNeedingAttention?.length || 0}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Individual Breakers */}
      {breakers?.breakers && breakers.breakers.length > 0 && (
        <div className="bg-slate-800/50 border border-slate-700/50 rounded-lg p-6">
          <h3 className="text-lg font-medium text-white mb-4">Individual Breakers</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {breakers.breakers.map((breaker) => (
              <div
                key={breaker.name}
                className={`p-4 rounded-lg border ${CIRCUIT_STATE_COLORS[breaker.state]}`}
              >
                <div className="flex items-center justify-between mb-2">
                  <span className="font-medium text-white">{breaker.name}</span>
                  <span className="text-xs uppercase font-bold">
                    {breaker.state.replace('_', ' ')}
                  </span>
                </div>
                <div className="grid grid-cols-2 gap-2 text-sm">
                  <div>
                    <span className="text-slate-400">Failure Rate:</span>
                    <span className="ml-2 text-white">{(breaker.failureRate * 100).toFixed(1)}%</span>
                  </div>
                  <div>
                    <span className="text-slate-400">Requests:</span>
                    <span className="ml-2 text-white">{breaker.totalRequests}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Recommendations */}
      {breakers?.recommendations && breakers.recommendations.length > 0 && (
        <div className="bg-slate-800/50 border border-slate-700/50 rounded-lg p-6">
          <h3 className="text-lg font-medium text-white mb-4">Recommendations</h3>
          <ul className="space-y-2">
            {breakers.recommendations.map((rec, idx) => (
              <li key={idx} className="flex items-start gap-2 text-slate-300">
                <CheckCircle2 className="w-5 h-5 text-blue-500 shrink-0 mt-0.5" />
                <span>{rec}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

// ============================================================================
// Tab Content: Fairness
// ============================================================================

function FairnessTab() {
  const startDate = new Date();
  startDate.setMonth(startDate.getMonth() - 1);
  const endDate = new Date();

  const { data: fairness, isLoading, error } = useFairnessAudit(
    startDate.toISOString().split('T')[0],
    endDate.toISOString().split('T')[0],
    false
  );

  if (isLoading) return <LoadingSpinner />;
  if (error) return <ErrorMessage message="Failed to load fairness data" />;

  return (
    <div className="space-y-6">
      {/* Jain's Fairness Index */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-slate-800/50 border border-slate-700/50 rounded-lg p-6 flex flex-col items-center">
          <h3 className="text-lg font-medium text-white mb-4">Jain&apos;s Fairness Index</h3>
          <div className="relative w-32 h-32">
            <svg className="w-full h-full transform -rotate-90" viewBox="0 0 100 100">
              <circle
                cx="50"
                cy="50"
                r="40"
                fill="none"
                stroke="currentColor"
                strokeWidth="10"
                className="text-slate-700"
              />
              <circle
                cx="50"
                cy="50"
                r="40"
                fill="none"
                stroke="currentColor"
                strokeWidth="10"
                strokeDasharray={`${(fairness?.jainIndex || 0) * 251} 251`}
                strokeLinecap="round"
                className={
                  (fairness?.jainIndex || 0) >= 0.9
                    ? 'text-green-500'
                    : (fairness?.jainIndex || 0) >= 0.8
                    ? 'text-emerald-500'
                    : (fairness?.jainIndex || 0) >= 0.7
                    ? 'text-amber-500'
                    : 'text-red-500'
                }
              />
            </svg>
            <div className="absolute inset-0 flex flex-col items-center justify-center">
              <span className="text-2xl font-bold text-white">
                {((fairness?.jainIndex || 0) * 100).toFixed(1)}%
              </span>
            </div>
          </div>
        </div>

        <div className="bg-slate-800/50 border border-slate-700/50 rounded-lg p-6">
          <h3 className="text-lg font-medium text-white mb-4">Gini Coefficient</h3>
          <div className="text-3xl font-bold text-white">
            {(fairness?.giniCoefficient || 0).toFixed(3)}
          </div>
          <div className="text-sm text-slate-400 mt-2">
            {(fairness?.giniCoefficient || 0) < 0.2
              ? 'Highly equitable'
              : (fairness?.giniCoefficient || 0) < 0.3
              ? 'Equitable'
              : (fairness?.giniCoefficient || 0) < 0.4
              ? 'Moderate inequality'
              : 'Significant inequality'}
          </div>
        </div>

        <div className="bg-slate-800/50 border border-slate-700/50 rounded-lg p-6">
          <h3 className="text-lg font-medium text-white mb-4">Faculty Analyzed</h3>
          <div className="text-3xl font-bold text-white">
            {fairness?.facultyWorkloads?.length || 0}
          </div>
          <div className="text-sm text-slate-400 mt-2">
            {fairness?.outliers?.length || 0} outliers detected
          </div>
        </div>
      </div>

      {/* Category Statistics */}
      {fairness?.categoryStats && (
        <div className="bg-slate-800/50 border border-slate-700/50 rounded-lg p-6">
          <h3 className="text-lg font-medium text-white mb-4">Category Statistics</h3>
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
            {Object.entries(fairness.categoryStats).map(([category, stats]) => (
              <div key={category} className="text-center">
                <div className="text-sm text-slate-400 capitalize">{category}</div>
                <div className="text-xl font-bold text-white">
                  {typeof stats === 'object' && 'mean' in stats
                    ? (stats as { mean: number }).mean.toFixed(1)
                    : '-'}
                </div>
                <div className="text-xs text-slate-500">avg half-days</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Workload Table - Simplified */}
      {fairness?.facultyWorkloads && fairness.facultyWorkloads.length > 0 && (
        <div className="bg-slate-800/50 border border-slate-700/50 rounded-lg p-6">
          <h3 className="text-lg font-medium text-white mb-4">Faculty Workloads</h3>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-slate-400 border-b border-slate-700">
                  <th className="pb-2">Faculty</th>
                  <th className="pb-2 text-right">Total</th>
                  <th className="pb-2 text-right">Call</th>
                  <th className="pb-2 text-right">FMIT</th>
                  <th className="pb-2 text-right">Clinic</th>
                  <th className="pb-2 text-right">Admin</th>
                </tr>
              </thead>
              <tbody>
                {fairness.facultyWorkloads.slice(0, 10).map((faculty) => (
                  <tr key={faculty.personId} className="border-b border-slate-700/50">
                    <td className="py-2 text-white">{faculty.name}</td>
                    <td className="py-2 text-right text-white">{faculty.totalHalfDays}</td>
                    <td className="py-2 text-right text-slate-300">{faculty.callHalfDays}</td>
                    <td className="py-2 text-right text-slate-300">{faculty.fmitHalfDays}</td>
                    <td className="py-2 text-right text-slate-300">{faculty.clinicHalfDays}</td>
                    <td className="py-2 text-right text-slate-300">{faculty.adminHalfDays}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}

// ============================================================================
// Tab Content: Compliance
// ============================================================================

function ComplianceTab() {
  const { data: mtf, isLoading: mtfLoading, error: mtfError } = useMTFCompliance(true);
  const { data: criticalIndex, isLoading: criticalLoading } = useUnifiedCriticalIndex(5);

  if (mtfLoading || criticalLoading) return <LoadingSpinner />;

  return (
    <div className="space-y-6">
      {/* MTF Compliance Summary */}
      {mtfError ? (
        <ErrorMessage message="MTF Compliance API not available" />
      ) : mtf && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <MetricCard
            label="DRRS Category"
            value={mtf.drrsCategory || 'N/A'}
            icon={FileCheck}
            status={
              mtf.drrsCategory === 'C1'
                ? 'healthy'
                : mtf.drrsCategory === 'C2'
                ? 'warning'
                : 'critical'
            }
          />
          <MetricCard
            label="Mission Capability"
            value={mtf.missionCapability || 'N/A'}
            icon={Shield}
          />
          <MetricCard
            label="Personnel Rating"
            value={mtf.personnelRating || 'N/A'}
            icon={Users}
          />
          <MetricCard
            label="Iron Dome Status"
            value={mtf.ironDomeStatus?.toUpperCase() || 'N/A'}
            icon={Shield}
            status={
              mtf.ironDomeStatus === 'green'
                ? 'healthy'
                : mtf.ironDomeStatus === 'yellow'
                ? 'warning'
                : 'critical'
            }
          />
        </div>
      )}

      {/* Executive Summary */}
      {mtf?.executiveSummary && (
        <div className="bg-slate-800/50 border border-slate-700/50 rounded-lg p-6">
          <h3 className="text-lg font-medium text-white mb-4">Executive Summary</h3>
          <p className="text-slate-300">{mtf.executiveSummary}</p>
        </div>
      )}

      {/* Deficiencies */}
      {mtf?.deficiencies && mtf.deficiencies.length > 0 && (
        <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-6">
          <h3 className="text-lg font-medium text-red-400 mb-4">Deficiencies</h3>
          <ul className="space-y-2">
            {mtf.deficiencies.map((def, idx) => (
              <li key={idx} className="flex items-start gap-2 text-red-300">
                <XCircle className="w-5 h-5 shrink-0 mt-0.5" />
                <span>{def}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Unified Critical Index */}
      {criticalIndex && (
        <>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <MetricCard
              label="Overall Risk Index"
              value={criticalIndex.overallIndex?.toFixed(2) || 'N/A'}
              icon={AlertTriangle}
              status={
                criticalIndex.riskLevel === 'low'
                  ? 'healthy'
                  : criticalIndex.riskLevel === 'medium'
                  ? 'warning'
                  : 'critical'
              }
            />
            <MetricCard
              label="Critical Faculty"
              value={criticalIndex.criticalCount || 0}
              subValue={`of ${criticalIndex.totalFaculty || 0} total`}
              icon={Users}
            />
            <MetricCard
              label="Universal Critical"
              value={criticalIndex.universalCriticalCount || 0}
              subValue="Maximum risk concentration"
              icon={XCircle}
              status={criticalIndex.universalCriticalCount ? 'critical' : 'healthy'}
            />
          </div>

          {/* Top Critical Faculty */}
          {criticalIndex.topCriticalFaculty && criticalIndex.topCriticalFaculty.length > 0 && (
            <div className="bg-slate-800/50 border border-slate-700/50 rounded-lg p-6">
              <h3 className="text-lg font-medium text-white mb-4">Top Critical Faculty</h3>
              <div className="space-y-3">
                {criticalIndex.topCriticalFaculty.map((faculty) => (
                  <div
                    key={faculty.facultyId}
                    className="flex items-center justify-between p-3 bg-slate-700/30 rounded-lg"
                  >
                    <div>
                      <div className="font-medium text-white">{faculty.facultyName}</div>
                      <div className="text-sm text-slate-400">
                        Pattern: {faculty.riskPattern?.replace(/_/g, ' ') || 'Unknown'}
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-lg font-bold text-white">
                        {(faculty.compositeIndex * 100).toFixed(0)}%
                      </div>
                      <div className="text-xs text-slate-400">Risk Score</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Recommendations */}
          {criticalIndex.recommendations && criticalIndex.recommendations.length > 0 && (
            <div className="bg-slate-800/50 border border-slate-700/50 rounded-lg p-6">
              <h3 className="text-lg font-medium text-white mb-4">Recommendations</h3>
              <ul className="space-y-2">
                {criticalIndex.recommendations.map((rec, idx) => (
                  <li key={idx} className="flex items-start gap-2 text-slate-300">
                    <CheckCircle2 className="w-5 h-5 text-blue-500 shrink-0 mt-0.5" />
                    <span>{rec}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </>
      )}
    </div>
  );
}

// ============================================================================
// Main Page Component
// ============================================================================

export default function ResilienceHubPage() {
  const [activeTab, setActiveTab] = useState<ResilienceTab>('overview');
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [lastRefresh, setLastRefresh] = useState(new Date());

  // Get overall status for header
  const { data: health } = useSystemHealth();

  const handleRefresh = useCallback(() => {
    setIsRefreshing(true);
    // Let React Query handle the actual refresh via refetch intervals
    setTimeout(() => {
      setIsRefreshing(false);
      setLastRefresh(new Date());
    }, 1000);
  }, []);

  return (
    <div className="min-h-screen bg-slate-900">
      {/* Header */}
      <header className="bg-slate-800/80 border-b border-slate-700/50 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
            {/* Title and Status */}
            <div className="flex items-center gap-4">
              <div className="p-2 bg-blue-500/10 rounded-lg">
                <Shield className="w-8 h-8 text-blue-500" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-white">Resilience Hub</h1>
                <p className="text-sm text-slate-400">System health, compliance & risk monitoring</p>
              </div>
              {health && (
                <StatusBadge status={health.overallStatus} size="lg" />
              )}
            </div>

            {/* Controls */}
            <div className="flex items-center gap-4">
              <div className="text-sm text-slate-400">
                <Clock className="w-4 h-4 inline mr-1" />
                Last refresh: {lastRefresh.toLocaleTimeString()}
              </div>
              <button
                onClick={handleRefresh}
                disabled={isRefreshing}
                className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-500 disabled:bg-blue-600/50 text-white rounded-lg transition-colors"
              >
                <RefreshCw className={`w-4 h-4 ${isRefreshing ? 'animate-spin' : ''}`} />
                Refresh
              </button>
            </div>
          </div>

          {/* Tabs */}
          <nav className="flex gap-1 mt-4 -mb-px overflow-x-auto">
            {TABS.map((tab) => {
              const Icon = tab.icon;
              const isActive = activeTab === tab.id;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`
                    flex items-center gap-2 px-4 py-2.5 text-sm font-medium rounded-t-lg
                    transition-all duration-200 whitespace-nowrap
                    ${isActive
                      ? 'bg-slate-900 text-white border-t border-x border-slate-700'
                      : 'text-slate-400 hover:text-white hover:bg-slate-700/50'
                    }
                  `}
                  title={tab.description}
                >
                  <Icon className="w-4 h-4" />
                  {tab.label}
                </button>
              );
            })}
          </nav>
        </div>
      </header>

      {/* Crisis Mode Alert */}
      {health?.crisisMode && (
        <div className="bg-red-600 text-white px-4 py-2 text-center font-medium">
          <AlertTriangle className="w-5 h-5 inline mr-2" />
          CRISIS MODE ACTIVE - System operating in emergency capacity
        </div>
      )}

      {/* Content */}
      <main className="max-w-7xl mx-auto px-4 py-6">
        {activeTab === 'overview' && <OverviewTab />}
        {activeTab === 'circuit-breakers' && <CircuitBreakersTab />}
        {activeTab === 'fairness' && <FairnessTab />}
        {activeTab === 'compliance' && <ComplianceTab />}
      </main>
    </div>
  );
}
