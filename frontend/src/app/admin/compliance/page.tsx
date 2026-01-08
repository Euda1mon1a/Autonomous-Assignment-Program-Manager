'use client';

/**
 * Away-From-Program Compliance Dashboard
 *
 * Tracks resident away-from-program days toward the 28-day annual limit.
 * Residents exceeding 28 days must extend their training.
 *
 * Status thresholds:
 * - OK (green): 0-20 days
 * - Warning (yellow): 21-27 days
 * - Critical (orange): 28 days (at limit)
 * - Exceeded (red): 29+ days (extension required)
 */
import { useState, useMemo } from 'react';
import {
  RefreshCw,
  Users,
  AlertTriangle,
  AlertCircle,
  CheckCircle2,
  XCircle,
  ChevronDown,
  ChevronUp,
  CalendarDays,
  Clock,
  Eye,
} from 'lucide-react';
import { useAwayComplianceDashboard } from '@/hooks/useAbsences';
import { usePeople } from '@/hooks/usePeople';
import type { ThresholdStatus, AwayFromProgramSummary } from '@/types/api';

// ============================================================================
// Constants
// ============================================================================

const STATUS_CONFIG: Record<
  ThresholdStatus,
  {
    label: string;
    color: string;
    bgColor: string;
    borderColor: string;
    icon: typeof CheckCircle2;
  }
> = {
  ok: {
    label: 'OK',
    color: 'text-green-400',
    bgColor: 'bg-green-500/20',
    borderColor: 'border-green-500/50',
    icon: CheckCircle2,
  },
  warning: {
    label: 'Warning',
    color: 'text-yellow-400',
    bgColor: 'bg-yellow-500/20',
    borderColor: 'border-yellow-500/50',
    icon: AlertTriangle,
  },
  critical: {
    label: 'Critical',
    color: 'text-orange-400',
    bgColor: 'bg-orange-500/20',
    borderColor: 'border-orange-500/50',
    icon: AlertCircle,
  },
  exceeded: {
    label: 'Exceeded',
    color: 'text-red-400',
    bgColor: 'bg-red-500/20',
    borderColor: 'border-red-500/50',
    icon: XCircle,
  },
};

// ============================================================================
// Progress Bar Component
// ============================================================================

interface AwayComplianceProgressBarProps {
  daysUsed: number;
  maxDays: number;
  warningDays: number;
  status: ThresholdStatus;
}

function AwayComplianceProgressBar({
  daysUsed,
  maxDays,
  warningDays,
  status,
}: AwayComplianceProgressBarProps) {
  const percentage = Math.min((daysUsed / maxDays) * 100, 100);
  const warningPercentage = (warningDays / maxDays) * 100;

  // Color based on status
  const barColor =
    status === 'ok'
      ? 'bg-green-500'
      : status === 'warning'
        ? 'bg-yellow-500'
        : status === 'critical'
          ? 'bg-orange-500'
          : 'bg-red-500';

  return (
    <div className="w-full">
      <div className="relative h-2 bg-slate-700 rounded-full overflow-hidden">
        {/* Warning threshold marker */}
        <div
          className="absolute top-0 bottom-0 w-0.5 bg-yellow-500/50 z-10"
          style={{ left: `${warningPercentage}%` }}
        />
        {/* Max threshold marker */}
        <div
          className="absolute top-0 bottom-0 w-0.5 bg-red-500/50 z-10"
          style={{ left: '100%', transform: 'translateX(-100%)' }}
        />
        {/* Progress bar */}
        <div
          className={`h-full ${barColor} transition-all duration-300`}
          style={{ width: `${percentage}%` }}
        />
      </div>
      <div className="flex justify-between mt-1 text-xs text-slate-500">
        <span>0</span>
        <span className="text-yellow-500">{warningDays}</span>
        <span className="text-red-500">{maxDays}</span>
      </div>
    </div>
  );
}

// ============================================================================
// Status Badge Component
// ============================================================================

interface StatusBadgeProps {
  status: ThresholdStatus;
  size?: 'sm' | 'md';
}

function StatusBadge({ status, size = 'md' }: StatusBadgeProps) {
  const config = STATUS_CONFIG[status];
  const Icon = config.icon;
  const sizeClass = size === 'sm' ? 'px-2 py-0.5 text-xs' : 'px-3 py-1 text-sm';

  return (
    <span
      className={`inline-flex items-center gap-1 rounded-full font-medium border ${config.bgColor} ${config.color} ${config.borderColor} ${sizeClass}`}
    >
      <Icon className={size === 'sm' ? 'w-3 h-3' : 'w-4 h-4'} />
      {config.label}
    </span>
  );
}

// ============================================================================
// Summary Card Component
// ============================================================================

interface SummaryCardProps {
  title: string;
  value: number;
  icon: typeof Users;
  color: string;
  bgColor: string;
}

function SummaryCard({ title, value, icon: Icon, color, bgColor }: SummaryCardProps) {
  return (
    <div className={`rounded-xl border border-slate-700 ${bgColor} p-4`}>
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm text-slate-400">{title}</p>
          <p className={`text-2xl font-bold ${color}`}>{value}</p>
        </div>
        <Icon className={`w-8 h-8 ${color} opacity-50`} />
      </div>
    </div>
  );
}

// ============================================================================
// Resident Row Component
// ============================================================================

interface ResidentRowProps {
  summary: AwayFromProgramSummary;
  personName: string;
  pgyLevel?: number;
  isExpanded: boolean;
  onToggle: () => void;
}

function ResidentRow({
  summary,
  personName,
  pgyLevel,
  isExpanded,
  onToggle,
}: ResidentRowProps) {
  const config = STATUS_CONFIG[summary.threshold_status];

  return (
    <>
      <tr
        className={`hover:bg-slate-800/50 cursor-pointer transition-colors ${
          isExpanded ? 'bg-slate-800/30' : ''
        }`}
        onClick={onToggle}
      >
        <td className="px-4 py-3 whitespace-nowrap">
          <div className="flex items-center gap-2">
            {isExpanded ? (
              <ChevronUp className="w-4 h-4 text-slate-400" />
            ) : (
              <ChevronDown className="w-4 h-4 text-slate-400" />
            )}
            <div>
              <div className="text-sm font-medium text-white">{personName}</div>
              {pgyLevel && (
                <div className="text-xs text-slate-400">PGY-{pgyLevel}</div>
              )}
            </div>
          </div>
        </td>
        <td className="px-4 py-3 whitespace-nowrap">
          <div className="w-32">
            <AwayComplianceProgressBar
              daysUsed={summary.days_used}
              maxDays={summary.max_days}
              warningDays={summary.warning_days}
              status={summary.threshold_status}
            />
          </div>
        </td>
        <td className="px-4 py-3 whitespace-nowrap text-center">
          <span className={`text-lg font-semibold ${config.color}`}>
            {summary.days_used}
          </span>
          <span className="text-slate-500"> / {summary.max_days}</span>
        </td>
        <td className="px-4 py-3 whitespace-nowrap text-center">
          <span
            className={`text-sm ${
              summary.days_remaining <= 0
                ? 'text-red-400'
                : summary.days_remaining <= 7
                  ? 'text-yellow-400'
                  : 'text-slate-300'
            }`}
          >
            {summary.days_remaining}
          </span>
        </td>
        <td className="px-4 py-3 whitespace-nowrap">
          <StatusBadge status={summary.threshold_status} size="sm" />
        </td>
        <td className="px-4 py-3 whitespace-nowrap text-right">
          <button
            onClick={(e) => {
              e.stopPropagation();
              // Future: navigate to detailed view
            }}
            className="text-violet-400 hover:text-violet-300 p-1 hover:bg-violet-500/20 rounded"
            title="View details"
          >
            <Eye className="w-4 h-4" />
          </button>
        </td>
      </tr>
      {isExpanded && summary.absences.length > 0 && (
        <tr>
          <td colSpan={6} className="px-4 py-2 bg-slate-800/50">
            <div className="pl-8">
              <p className="text-xs text-slate-400 mb-2">Contributing Absences:</p>
              <div className="space-y-1">
                {summary.absences.map((absence) => (
                  <div
                    key={absence.id}
                    className="flex items-center gap-4 text-xs text-slate-300"
                  >
                    <CalendarDays className="w-3 h-3 text-slate-500" />
                    <span>
                      {new Date(absence.start_date).toLocaleDateString()} -{' '}
                      {new Date(absence.end_date).toLocaleDateString()}
                    </span>
                    <span className="px-2 py-0.5 bg-slate-700 rounded text-slate-400 capitalize">
                      {absence.absence_type.replace('_', ' ')}
                    </span>
                    <span className="text-slate-500">{absence.days} days</span>
                  </div>
                ))}
              </div>
            </div>
          </td>
        </tr>
      )}
    </>
  );
}

// ============================================================================
// Main Dashboard Component
// ============================================================================

type SortField = 'name' | 'days_used' | 'status';
type SortDirection = 'asc' | 'desc';

export default function ComplianceDashboardPage() {
  const [expandedIds, setExpandedIds] = useState<Set<string>>(new Set());
  const [sortField, setSortField] = useState<SortField>('status');
  const [sortDirection, setSortDirection] = useState<SortDirection>('desc');
  const [statusFilter, setStatusFilter] = useState<ThresholdStatus | ''>('');

  const { data, isLoading, error, refetch, isFetching } = useAwayComplianceDashboard();
  const { data: peopleData } = usePeople();

  // Create person lookup map
  const personMap = useMemo(() => {
    const map = new Map<string, { name: string; pgy_level?: number }>();
    peopleData?.items?.forEach((p) => {
      map.set(p.id, { name: p.name, pgy_level: p.pgy_level ?? undefined });
    });
    return map;
  }, [peopleData]);

  // Filter and sort residents
  const sortedResidents = useMemo(() => {
    if (!data?.residents) return [];

    let filtered = [...data.residents];

    // Apply status filter
    if (statusFilter) {
      filtered = filtered.filter((r) => r.threshold_status === statusFilter);
    }

    // Sort
    filtered.sort((a, b) => {
      let comparison = 0;
      switch (sortField) {
        case 'name':
          const nameA = personMap.get(a.person_id)?.name || '';
          const nameB = personMap.get(b.person_id)?.name || '';
          comparison = nameA.localeCompare(nameB);
          break;
        case 'days_used':
          comparison = a.days_used - b.days_used;
          break;
        case 'status':
          // Sort by severity: exceeded > critical > warning > ok
          const statusOrder: Record<ThresholdStatus, number> = {
            exceeded: 4,
            critical: 3,
            warning: 2,
            ok: 1,
          };
          comparison = statusOrder[a.threshold_status] - statusOrder[b.threshold_status];
          break;
      }
      return sortDirection === 'asc' ? comparison : -comparison;
    });

    return filtered;
  }, [data?.residents, statusFilter, sortField, sortDirection, personMap]);

  const toggleExpanded = (personId: string) => {
    setExpandedIds((prev) => {
      const next = new Set(prev);
      if (next.has(personId)) {
        next.delete(personId);
      } else {
        next.add(personId);
      }
      return next;
    });
  };

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortDirection((prev) => (prev === 'asc' ? 'desc' : 'asc'));
    } else {
      setSortField(field);
      setSortDirection('desc');
    }
  };

  if (error) {
    return (
      <div className="min-h-screen bg-slate-900 text-white p-8">
        <div className="max-w-6xl mx-auto">
          <div className="bg-red-500/20 border border-red-500/50 rounded-lg p-4 text-red-400">
            Error loading compliance data: {error.message}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-900 text-white">
      {/* Header */}
      <header className="border-b border-slate-800 bg-slate-900/95 backdrop-blur sticky top-0 z-10">
        <div className="max-w-6xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold">Away-From-Program Compliance</h1>
              <p className="text-sm text-slate-400 mt-1">
                {data?.academic_year || 'Loading...'} Academic Year
              </p>
            </div>
            <button
              onClick={() => refetch()}
              disabled={isFetching}
              className="flex items-center gap-2 px-4 py-2 bg-violet-600 hover:bg-violet-700 disabled:opacity-50 rounded-lg transition-colors"
            >
              <RefreshCw className={`w-4 h-4 ${isFetching ? 'animate-spin' : ''}`} />
              Refresh
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-6 py-6 space-y-6">
        {/* Summary Cards */}
        {isLoading ? (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {[1, 2, 3, 4].map((i) => (
              <div
                key={i}
                className="h-24 bg-slate-800 animate-pulse rounded-xl"
              />
            ))}
          </div>
        ) : (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <SummaryCard
              title="Total Residents"
              value={data?.summary?.total_residents || 0}
              icon={Users}
              color="text-slate-300"
              bgColor="bg-slate-800/50"
            />
            <SummaryCard
              title="OK"
              value={data?.summary?.by_status?.ok || 0}
              icon={CheckCircle2}
              color="text-green-400"
              bgColor="bg-green-500/10"
            />
            <SummaryCard
              title="Warning"
              value={data?.summary?.by_status?.warning || 0}
              icon={AlertTriangle}
              color="text-yellow-400"
              bgColor="bg-yellow-500/10"
            />
            <SummaryCard
              title="Critical / Exceeded"
              value={(data?.summary?.by_status?.critical || 0) + (data?.summary?.by_status?.exceeded || 0)}
              icon={AlertCircle}
              color="text-red-400"
              bgColor="bg-red-500/10"
            />
          </div>
        )}

        {/* Info Banner */}
        <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-4">
          <div className="flex items-start gap-3">
            <Clock className="w-5 h-5 text-violet-400 mt-0.5" />
            <div>
              <p className="text-sm text-slate-300">
                <strong>28-Day Rule:</strong> Residents who exceed 28 days away from
                program per academic year (July 1 - June 30) must extend their training.
              </p>
              <p className="text-xs text-slate-500 mt-1">
                Warning threshold at 21 days (75%). All absence types count toward this limit.
              </p>
            </div>
          </div>
        </div>

        {/* Filters */}
        <div className="flex items-center gap-4">
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value as ThresholdStatus | '')}
            className="px-3 py-2 bg-slate-800/50 border border-slate-700 rounded-lg text-white text-sm"
          >
            <option value="">All Statuses</option>
            <option value="ok">OK</option>
            <option value="warning">Warning</option>
            <option value="critical">Critical</option>
            <option value="exceeded">Exceeded</option>
          </select>
          <span className="text-sm text-slate-400">
            Showing {sortedResidents.length} resident
            {sortedResidents.length !== 1 ? 's' : ''}
          </span>
        </div>

        {/* Table */}
        {isLoading ? (
          <div className="bg-slate-800/30 border border-slate-700 rounded-xl">
            <div className="p-8 flex items-center justify-center">
              <RefreshCw className="w-8 h-8 text-slate-400 animate-spin" />
            </div>
          </div>
        ) : (
          <div className="bg-slate-800/30 border border-slate-700 rounded-xl overflow-hidden">
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-slate-700">
                <thead className="bg-slate-800/50">
                  <tr>
                    <th
                      className="px-4 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider cursor-pointer hover:text-white"
                      onClick={() => handleSort('name')}
                    >
                      <div className="flex items-center gap-1">
                        Resident
                        {sortField === 'name' && (
                          sortDirection === 'asc' ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />
                        )}
                      </div>
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">
                      Progress
                    </th>
                    <th
                      className="px-4 py-3 text-center text-xs font-medium text-slate-400 uppercase tracking-wider cursor-pointer hover:text-white"
                      onClick={() => handleSort('days_used')}
                    >
                      <div className="flex items-center justify-center gap-1">
                        Days Used
                        {sortField === 'days_used' && (
                          sortDirection === 'asc' ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />
                        )}
                      </div>
                    </th>
                    <th className="px-4 py-3 text-center text-xs font-medium text-slate-400 uppercase tracking-wider">
                      Remaining
                    </th>
                    <th
                      className="px-4 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider cursor-pointer hover:text-white"
                      onClick={() => handleSort('status')}
                    >
                      <div className="flex items-center gap-1">
                        Status
                        {sortField === 'status' && (
                          sortDirection === 'asc' ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />
                        )}
                      </div>
                    </th>
                    <th className="px-4 py-3 text-right text-xs font-medium text-slate-400 uppercase tracking-wider">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-700/50">
                  {sortedResidents.length === 0 ? (
                    <tr>
                      <td colSpan={6} className="px-4 py-12 text-center text-slate-400">
                        No residents found matching the selected filter.
                      </td>
                    </tr>
                  ) : (
                    sortedResidents.map((summary) => {
                      const person = personMap.get(summary.person_id);
                      return (
                        <ResidentRow
                          key={summary.person_id}
                          summary={summary}
                          personName={person?.name || 'Unknown'}
                          pgyLevel={person?.pgy_level}
                          isExpanded={expandedIds.has(summary.person_id)}
                          onToggle={() => toggleExpanded(summary.person_id)}
                        />
                      );
                    })
                  )}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
