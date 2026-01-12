'use client';

/**
 * Admin Fairness Audit Page
 *
 * Full-detail workload fairness view for Program Directors.
 * Features:
 * - Date range selection
 * - Jain's fairness index gauge
 * - Category statistics (call, FMIT, clinic, admin, academic)
 * - Per-faculty workload table (sortable)
 * - Outlier highlighting
 * - Include titled faculty toggle
 */

import { useState, useMemo } from 'react';
import { Scale, RefreshCw, AlertTriangle, CheckCircle2, Users } from 'lucide-react';
import { useQueryClient } from '@tanstack/react-query';
import { DatePicker } from '@/components/ui/DatePicker';
import { Switch } from '@/components/ui/Switch';
import { Badge } from '@/components/ui/Badge';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { DataTable, Column } from '@/components/ui/DataTable';
import { getFirstOfMonthLocal, getLastOfMonthLocal } from '@/lib/date-utils';
import {
  useFairnessAudit,
  fairnessQueryKeys,
  getFairnessStatus,
  getFairnessLabel,
  getWorkloadDeviation,
  type FacultyWorkload,
} from '@/hooks/useFairness';

// ============================================================================
// Helper Components
// ============================================================================

function FairnessGauge({ value }: { value: number }) {
  const status = getFairnessStatus(value);
  const label = getFairnessLabel(value);
  const percentage = value * 100;

  const colorClass = {
    excellent: 'text-green-500',
    good: 'text-emerald-500',
    warning: 'text-amber-500',
    critical: 'text-red-500',
  }[status];

  const bgColorClass = {
    excellent: 'bg-green-500',
    good: 'bg-emerald-500',
    warning: 'bg-amber-500',
    critical: 'bg-red-500',
  }[status];

  return (
    <div className="flex flex-col items-center">
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
            strokeDasharray={`${percentage * 2.51} 251`}
            strokeLinecap="round"
            className={colorClass}
          />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className={`text-2xl font-bold ${colorClass}`}>
            {(value * 100).toFixed(1)}%
          </span>
        </div>
      </div>
      <Badge
        variant={status === 'excellent' ? 'success' : status === 'good' ? 'primary' : status === 'warning' ? 'warning' : 'danger'}
        className="mt-2"
      >
        {label}
      </Badge>
    </div>
  );
}

function StatCard({
  title,
  min,
  max,
  mean,
  spread,
  weight,
}: {
  title: string;
  min: number;
  max: number;
  mean: number;
  spread: number;
  weight: number;
}) {
  return (
    <Card className="bg-slate-800 border-slate-700">
      <CardContent>
        <div className="flex justify-between items-start mb-2">
          <span className="text-sm font-medium text-slate-300">{title}</span>
          <Badge variant="default" size="sm">
            w={weight}
          </Badge>
        </div>
        <div className="grid grid-cols-2 gap-2 text-sm">
          <div>
            <span className="text-slate-400">Min:</span>{' '}
            <span className="text-white font-medium">{min.toFixed(1)}</span>
          </div>
          <div>
            <span className="text-slate-400">Max:</span>{' '}
            <span className="text-white font-medium">{max.toFixed(1)}</span>
          </div>
          <div>
            <span className="text-slate-400">Mean:</span>{' '}
            <span className="text-white font-medium">{mean.toFixed(1)}</span>
          </div>
          <div>
            <span className="text-slate-400">Spread:</span>{' '}
            <span className="text-white font-medium">{spread.toFixed(1)}</span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

// ============================================================================
// Main Page Component
// ============================================================================

export default function AdminFairnessPage() {
  const queryClient = useQueryClient();

  // Default to current month (using local timezone)
  const [startDate, setStartDate] = useState<string>(getFirstOfMonthLocal);
  const [endDate, setEndDate] = useState<string>(getLastOfMonthLocal);
  const [includeTitled, setIncludeTitled] = useState(false);

  // Fetch data
  const { data, isLoading, error, isFetching } = useFairnessAudit(
    startDate,
    endDate,
    includeTitled
  );

  // Table columns
  const columns: Column<FacultyWorkload>[] = useMemo(
    () => [
      {
        key: 'personName',
        header: 'Faculty',
        accessor: (row) => row.personName,
        sortable: true,
      },
      {
        key: 'callCount',
        header: 'Call',
        accessor: (row) => row.callCount,
        sortable: true,
      },
      {
        key: 'fmitWeeks',
        header: 'FMIT',
        accessor: (row) => row.fmitWeeks,
        sortable: true,
      },
      {
        key: 'clinicHalfdays',
        header: 'Clinic',
        accessor: (row) => row.clinicHalfdays,
        sortable: true,
      },
      {
        key: 'adminHalfdays',
        header: 'Admin',
        accessor: (row) => row.adminHalfdays,
        sortable: true,
      },
      {
        key: 'academicHalfdays',
        header: 'Academic',
        accessor: (row) => row.academicHalfdays,
        sortable: true,
      },
      {
        key: 'totalScore',
        header: 'Score',
        accessor: (row) => row.totalScore,
        sortable: true,
        render: (value, row) => {
          const score = value as number;
          const deviation = data ? getWorkloadDeviation(row, data.workloadStats.mean) : 0;
          const isHigh = deviation > 25;
          const isLow = deviation < -25;

          return (
            <div className="flex items-center gap-2">
              <span className="font-medium">{score.toFixed(1)}</span>
              {isHigh && (
                <Badge variant="danger" size="sm">
                  +{deviation.toFixed(0)}%
                </Badge>
              )}
              {isLow && (
                <Badge variant="warning" size="sm">
                  {deviation.toFixed(0)}%
                </Badge>
              )}
            </div>
          );
        },
      },
    ],
    [data]
  );

  const handleRefresh = () => {
    queryClient.invalidateQueries({
      queryKey: fairnessQueryKeys.all,
    });
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
      {/* Header */}
      <header className="border-b border-slate-700/50 bg-slate-900/80 backdrop-blur-sm sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-gradient-to-br from-emerald-500 to-teal-600 rounded-lg">
                <Scale className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-white">
                  Workload Fairness Audit
                </h1>
                <p className="text-sm text-slate-300">
                  Analyze faculty workload distribution across categories
                </p>
              </div>
            </div>

            <button
              onClick={handleRefresh}
              disabled={isFetching}
              className="p-2 text-slate-300 hover:text-white transition-colors disabled:opacity-50"
              title="Refresh data"
              aria-label="Refresh fairness data"
            >
              <RefreshCw className={`w-5 h-5 ${isFetching ? 'animate-spin' : ''}`} />
            </button>
          </div>
        </div>
      </header>

      {/* Controls */}
      <div className="max-w-7xl mx-auto px-4 py-4">
        <div className="flex flex-wrap items-center gap-4 p-4 bg-slate-800/50 border border-slate-700 rounded-lg">
          <div className="flex items-center gap-2">
            <label className="text-sm text-slate-300">From:</label>
            <DatePicker
              value={startDate}
              onChange={setStartDate}
              max={endDate}
              className="w-48"
            />
          </div>
          <div className="flex items-center gap-2">
            <label className="text-sm text-slate-300">To:</label>
            <DatePicker
              value={endDate}
              onChange={setEndDate}
              min={startDate}
              className="w-48"
            />
          </div>
          <div className="flex items-center gap-2 ml-auto">
            <Switch
              checked={includeTitled}
              onChange={setIncludeTitled}
              label="Include titled faculty (PD, APD, OIC, Chief)"
            />
          </div>
        </div>
      </div>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 py-6 space-y-6">
        {/* Loading State */}
        {isLoading && (
          <div className="flex items-center justify-center py-12">
            <div className="flex items-center gap-3 text-slate-300">
              <RefreshCw className="w-5 h-5 animate-spin" />
              <span>Loading fairness data...</span>
            </div>
          </div>
        )}

        {/* Error State */}
        {error && (
          <div className="p-4 bg-red-500/10 border border-red-500/50 rounded-lg flex items-center gap-3">
            <AlertTriangle className="w-5 h-5 text-red-500" />
            <span className="text-red-400">
              Failed to load fairness data: {error.message}
            </span>
          </div>
        )}

        {/* Data Display */}
        {data && (
          <>
            {/* Summary Row */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {/* Fairness Index */}
              <Card className="bg-slate-800 border-slate-700">
                <CardHeader>
                  <CardTitle className="text-white">Fairness Index</CardTitle>
                </CardHeader>
                <CardContent className="flex justify-center">
                  <FairnessGauge value={data.fairnessIndex} />
                </CardContent>
              </Card>

              {/* Workload Summary */}
              <Card className="bg-slate-800 border-slate-700">
                <CardHeader>
                  <CardTitle className="text-white">Workload Summary</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    <div className="flex justify-between">
                      <span className="text-slate-400">Faculty Count:</span>
                      <span className="text-white font-medium">{data.facultyCount}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-400">Min Score:</span>
                      <span className="text-white font-medium">
                        {data.workloadStats.min.toFixed(1)}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-400">Max Score:</span>
                      <span className="text-white font-medium">
                        {data.workloadStats.max.toFixed(1)}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-400">Mean Score:</span>
                      <span className="text-white font-medium">
                        {data.workloadStats.mean.toFixed(1)}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-400">Spread:</span>
                      <span className="text-white font-medium">
                        {data.workloadStats.spread.toFixed(1)}
                      </span>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Outliers */}
              <Card className="bg-slate-800 border-slate-700">
                <CardHeader>
                  <CardTitle className="text-white">Outliers</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div>
                      <div className="flex items-center gap-2 mb-2">
                        <AlertTriangle className="w-4 h-4 text-red-500" />
                        <span className="text-sm text-slate-300">
                          High Workload ({data.outliers.high.length})
                        </span>
                      </div>
                      {data.outliers.high.length > 0 ? (
                        <div className="flex flex-wrap gap-1">
                          {data.outliers.high.map((name) => (
                            <Badge key={name} variant="danger" size="sm">
                              {name}
                            </Badge>
                          ))}
                        </div>
                      ) : (
                        <span className="text-slate-400 text-sm">None</span>
                      )}
                    </div>
                    <div>
                      <div className="flex items-center gap-2 mb-2">
                        <CheckCircle2 className="w-4 h-4 text-amber-500" />
                        <span className="text-sm text-slate-300">
                          Low Workload ({data.outliers.low.length})
                        </span>
                      </div>
                      {data.outliers.low.length > 0 ? (
                        <div className="flex flex-wrap gap-1">
                          {data.outliers.low.map((name) => (
                            <Badge key={name} variant="warning" size="sm">
                              {name}
                            </Badge>
                          ))}
                        </div>
                      ) : (
                        <span className="text-slate-400 text-sm">None</span>
                      )}
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Category Stats */}
            <div>
              <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                <Users className="w-5 h-5" />
                Category Statistics
              </h2>
              <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                <StatCard
                  title="Call (Overnight)"
                  {...data.categoryStats.call}
                  weight={data.weights.call}
                />
                <StatCard
                  title="FMIT Weeks"
                  {...data.categoryStats.fmit}
                  weight={data.weights.fmit}
                />
                <StatCard
                  title="Clinic Half-Days"
                  {...data.categoryStats.clinic}
                  weight={data.weights.clinic}
                />
                <StatCard
                  title="Admin (GME/DFM)"
                  {...data.categoryStats.admin}
                  weight={data.weights.admin}
                />
                <StatCard
                  title="Academic (LEC/ADV)"
                  {...data.categoryStats.academic}
                  weight={data.weights.academic}
                />
              </div>
            </div>

            {/* Faculty Table */}
            <div>
              <h2 className="text-lg font-semibold text-white mb-4">
                Faculty Workloads
              </h2>
              <DataTable
                data={data.workloads}
                columns={columns}
                rowKey={(row) => row.personId}
                pageSize={15}
                searchable
                className="[&_table]:bg-slate-800 [&_thead]:bg-slate-700 [&_th]:text-slate-300 [&_td]:text-slate-200 [&_input]:bg-slate-700 [&_input]:border-slate-600 [&_input]:text-white"
              />
            </div>

            {/* Period Info */}
            <div className="text-sm text-slate-400 text-center">
              Data for period: {data.period.start} to {data.period.end}
            </div>
          </>
        )}
      </main>
    </div>
  );
}
