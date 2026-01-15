'use client';

/**
 * Compliance Hub
 *
 * Unified compliance dashboard combining:
 * - ACGME Compliance: Work hour rules, supervision ratios, rest periods
 * - Away-From-Program Compliance: 28-day annual absence limit tracking
 *
 * Both tabs are read-only (Tier 0), making this a green-risk page.
 */
import { useState, useMemo } from 'react';
import { useSearchParams } from 'next/navigation';
import { format, startOfMonth, endOfMonth, addMonths, subMonths } from 'date-fns';
import {
  CheckCircle,
  XCircle,
  AlertTriangle,
  ChevronLeft,
  ChevronRight,
  RefreshCw,
  Shield,
  Plane,
  CheckCircle2,
  AlertCircle,
  ChevronDown,
  ChevronUp,
  CalendarDays,
  Clock,
  Eye,
  Users,
} from 'lucide-react';
import { useValidateSchedule } from '@/hooks/useSchedule';
import { useAwayComplianceDashboard } from '@/hooks/useAbsences';
import { usePeople } from '@/hooks/usePeople';
import { ProtectedRoute } from '@/components/ProtectedRoute';
import { RiskBar } from '@/components/ui/RiskBar';
import { Tabs } from '@/components/ui/Tabs';
import type { Violation, ThresholdStatus, AwayFromProgramSummary } from '@/types/api';

// ============================================================================
// Types
// ============================================================================

type TabId = 'acgme' | 'away-from-program';

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
    color: 'text-green-600',
    bgColor: 'bg-green-100',
    borderColor: 'border-green-300',
    icon: CheckCircle2,
  },
  warning: {
    label: 'Warning',
    color: 'text-yellow-600',
    bgColor: 'bg-yellow-100',
    borderColor: 'border-yellow-300',
    icon: AlertTriangle,
  },
  critical: {
    label: 'Critical',
    color: 'text-orange-600',
    bgColor: 'bg-orange-100',
    borderColor: 'border-orange-300',
    icon: AlertCircle,
  },
  exceeded: {
    label: 'Exceeded',
    color: 'text-red-600',
    bgColor: 'bg-red-100',
    borderColor: 'border-red-300',
    icon: XCircle,
  },
};

// ============================================================================
// ACGME Compliance Tab Components
// ============================================================================

function ACGMEComplianceTab() {
  const [selectedMonth, setSelectedMonth] = useState(new Date());
  const startDate = format(startOfMonth(selectedMonth), 'yyyy-MM-dd');
  const endDate = format(endOfMonth(selectedMonth), 'yyyy-MM-dd');

  const { data: validation, isLoading, isError, error, refetch } = useValidateSchedule(startDate, endDate);

  const goToPreviousMonth = () => setSelectedMonth(subMonths(selectedMonth, 1));
  const goToNextMonth = () => setSelectedMonth(addMonths(selectedMonth, 1));
  const goToCurrentMonth = () => setSelectedMonth(new Date());

  return (
    <div className="space-y-6">
      {/* Info Banner */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <div className="flex items-start gap-3">
          <Shield className="w-5 h-5 text-blue-600 mt-0.5 flex-shrink-0" aria-hidden="true" />
          <div>
            <p className="text-sm text-blue-800">
              <strong>ACGME Work Hour Requirements:</strong> Validates schedule compliance with
              Accreditation Council for Graduate Medical Education duty hour regulations.
            </p>
            <p className="text-xs text-blue-600 mt-1">
              Includes 80-hour weekly limit, 1-in-7 day off rule, and supervision ratio requirements.
            </p>
          </div>
        </div>
      </div>

      {/* Month Navigation */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <button
            onClick={goToPreviousMonth}
            className="p-2 hover:bg-gray-100 rounded-md transition-colors"
            aria-label="Previous month"
          >
            <ChevronLeft className="w-5 h-5" />
          </button>
          <button
            onClick={goToCurrentMonth}
            className="btn-secondary text-sm min-w-[140px]"
          >
            {format(selectedMonth, 'MMMM yyyy')}
          </button>
          <button
            onClick={goToNextMonth}
            className="p-2 hover:bg-gray-100 rounded-md transition-colors"
            aria-label="Next month"
          >
            <ChevronRight className="w-5 h-5" />
          </button>
        </div>
        <button
          onClick={() => refetch()}
          disabled={isLoading}
          className="flex items-center gap-2 px-3 py-2 text-sm text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-md transition-colors disabled:opacity-50"
          aria-label="Refresh validation"
        >
          <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
          Refresh
        </button>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <ACGMEComplianceCard
          title="80-Hour Rule"
          description="Max 80 hours/week (4-week average)"
          status={validation?.violations?.filter((v: Violation) => v.type === '80_HOUR_VIOLATION').length === 0 ? 'pass' : 'fail'}
          count={validation?.violations?.filter((v: Violation) => v.type === '80_HOUR_VIOLATION').length || 0}
          isLoading={isLoading}
        />
        <ACGMEComplianceCard
          title="1-in-7 Rule"
          description="One day off every 7 days"
          status={validation?.violations?.filter((v: Violation) => v.type === '1_IN_7_VIOLATION').length === 0 ? 'pass' : 'fail'}
          count={validation?.violations?.filter((v: Violation) => v.type === '1_IN_7_VIOLATION').length || 0}
          isLoading={isLoading}
        />
        <ACGMEComplianceCard
          title="Supervision Ratios"
          description="PGY-1: 1:2, PGY-2/3: 1:4"
          status={validation?.violations?.filter((v: Violation) => v.type === 'SUPERVISION_RATIO_VIOLATION').length === 0 ? 'pass' : 'fail'}
          count={validation?.violations?.filter((v: Violation) => v.type === 'SUPERVISION_RATIO_VIOLATION').length || 0}
          isLoading={isLoading}
        />
      </div>

      {/* Violations List */}
      <div className="card">
        <div className="border-b pb-4 mb-4">
          <h2 className="font-semibold text-lg">
            {validation?.valid ? 'No Violations' : 'Violations Requiring Attention'}
          </h2>
          <p className="text-sm text-gray-500">
            Coverage Rate: {((validation?.coverageRate ?? 0) * 100).toFixed(1)}%
          </p>
        </div>

        {isLoading ? (
          <div className="flex items-center justify-center h-32" role="status" aria-live="polite">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" aria-hidden="true"></div>
            <span className="sr-only">Loading compliance data...</span>
          </div>
        ) : isError ? (
          <div className="flex flex-col items-center justify-center h-32 text-center" role="alert">
            <p className="text-gray-600 mb-4">
              {error?.message || 'Failed to load compliance data'}
            </p>
            <button
              onClick={() => refetch()}
              className="btn-primary flex items-center gap-2"
            >
              <RefreshCw className="w-4 h-4" />
              Retry
            </button>
          </div>
        ) : validation?.violations?.length === 0 ? (
          <div className="text-center py-8 text-green-600">
            <CheckCircle className="w-12 h-12 mx-auto mb-2" aria-hidden="true" />
            <p className="font-medium">All ACGME requirements met!</p>
          </div>
        ) : (
          <div className="divide-y" role="list" aria-label="Compliance violations">
            {validation?.violations?.map((violation: Violation, idx: number) => (
              <ACGMEViolationRow key={idx} violation={violation} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function ACGMEComplianceCard({
  title,
  description,
  status,
  count,
  isLoading,
}: {
  title: string;
  description: string;
  status: 'pass' | 'fail';
  count: number;
  isLoading: boolean;
}) {
  return (
    <div className="card">
      <div className="flex items-start justify-between">
        <div>
          <h3 className="font-semibold text-gray-900">{title}</h3>
          <p className="text-sm text-gray-500">{description}</p>
        </div>
        {isLoading ? (
          <div className="animate-pulse w-8 h-8 bg-gray-200 rounded-full" aria-hidden="true"></div>
        ) : status === 'pass' ? (
          <CheckCircle className="w-8 h-8 text-green-500" aria-label="Passing" />
        ) : (
          <XCircle className="w-8 h-8 text-red-500" aria-label="Violations found" />
        )}
      </div>
      {!isLoading && count > 0 && (
        <p className="mt-2 text-sm text-red-600">
          {count} violation{count > 1 ? 's' : ''} found
        </p>
      )}
    </div>
  );
}

function ACGMEViolationRow({ violation }: { violation: Violation }) {
  const severityColors: Record<string, string> = {
    CRITICAL: 'bg-red-100 text-red-800',
    HIGH: 'bg-orange-100 text-orange-800',
    MEDIUM: 'bg-yellow-100 text-yellow-800',
    LOW: 'bg-gray-100 text-gray-800',
  };

  return (
    <div className="py-4 flex items-start gap-4" role="listitem">
      <AlertTriangle className="w-5 h-5 text-amber-500 flex-shrink-0 mt-0.5" aria-hidden="true" />
      <div className="flex-1">
        <div className="flex items-center gap-2">
          <span className={`px-2 py-0.5 rounded text-xs font-medium ${severityColors[violation.severity] || severityColors.LOW}`}>
            {violation.severity}
          </span>
          <span className="text-sm font-medium text-gray-900">
            {violation.type.replace(/_/g, ' ')}
          </span>
        </div>
        <p className="mt-1 text-sm text-gray-600">{violation.message}</p>
        {violation.personName && (
          <p className="text-xs text-gray-500 mt-1">Person: {violation.personName}</p>
        )}
      </div>
    </div>
  );
}

// ============================================================================
// Away-From-Program Tab Components
// ============================================================================

type SortField = 'name' | 'days_used' | 'status';
type SortDirection = 'asc' | 'desc';

function AwayFromProgramTab() {
  const [expandedIds, setExpandedIds] = useState<Set<string>>(new Set());
  const [sortField, setSortField] = useState<SortField>('status');
  const [sortDirection, setSortDirection] = useState<SortDirection>('desc');
  const [statusFilter, setStatusFilter] = useState<ThresholdStatus | ''>('');

  const { data, isLoading, error, refetch, isFetching } = useAwayComplianceDashboard();
  const { data: peopleData } = usePeople();

  // Create person lookup map
  const personMap = useMemo(() => {
    const map = new Map<string, { name: string; pgyLevel?: number }>();
    peopleData?.items?.forEach((p) => {
      map.set(p.id, { name: p.name, pgyLevel: p.pgyLevel ?? undefined });
    });
    return map;
  }, [peopleData]);

  // Filter and sort residents
  const sortedResidents = useMemo(() => {
    if (!data?.residents) return [];

    let filtered = [...data.residents];

    // Apply status filter
    if (statusFilter) {
      filtered = filtered.filter((r) => r.thresholdStatus === statusFilter);
    }

    // Sort
    filtered.sort((a, b) => {
      let comparison = 0;
      switch (sortField) {
        case 'name': {
          const nameA = personMap.get(a.personId)?.name || '';
          const nameB = personMap.get(b.personId)?.name || '';
          comparison = nameA.localeCompare(nameB);
          break;
        }
        case 'days_used':
          comparison = a.daysUsed - b.daysUsed;
          break;
        case 'status': {
          const statusOrder: Record<ThresholdStatus, number> = {
            exceeded: 4,
            critical: 3,
            warning: 2,
            ok: 1,
          };
          comparison = statusOrder[a.thresholdStatus] - statusOrder[b.thresholdStatus];
          break;
        }
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
      <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700" role="alert">
        Error loading compliance data: {error.message}
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Info Banner */}
      <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
        <div className="flex items-start gap-3">
          <Clock className="w-5 h-5 text-purple-600 mt-0.5 flex-shrink-0" aria-hidden="true" />
          <div>
            <p className="text-sm text-purple-800">
              <strong>28-Day Rule:</strong> Residents who exceed 28 days away from
              program per academic year (July 1 - June 30) must extend their training.
            </p>
            <p className="text-xs text-purple-600 mt-1">
              Warning threshold at 21 days (75%). All absence types count toward this limit.
            </p>
          </div>
        </div>
      </div>

      {/* Summary Cards */}
      {isLoading ? (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="h-24 bg-gray-100 animate-pulse rounded-xl" aria-hidden="true" />
          ))}
        </div>
      ) : (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <AwayFromProgramSummaryCard title="Total Residents" value={data?.summary?.totalResidents || 0} icon={Users} color="text-gray-600" bgColor="bg-gray-50" />
          <AwayFromProgramSummaryCard title="OK" value={data?.summary?.byStatus?.ok || 0} icon={CheckCircle2} color="text-green-600" bgColor="bg-green-50" />
          <AwayFromProgramSummaryCard title="Warning" value={data?.summary?.byStatus?.warning || 0} icon={AlertTriangle} color="text-yellow-600" bgColor="bg-yellow-50" />
          <AwayFromProgramSummaryCard title="Critical / Exceeded" value={(data?.summary?.byStatus?.critical || 0) + (data?.summary?.byStatus?.exceeded || 0)} icon={AlertCircle} color="text-red-600" bgColor="bg-red-50" />
        </div>
      )}

      {/* Filters */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <label htmlFor="status-filter" className="sr-only">Filter by status</label>
          <select
            id="status-filter"
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value as ThresholdStatus | '')}
            className="px-3 py-2 bg-white border border-gray-300 rounded-lg text-gray-700 text-sm focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
          >
            <option value="">All Statuses</option>
            <option value="ok">OK</option>
            <option value="warning">Warning</option>
            <option value="critical">Critical</option>
            <option value="exceeded">Exceeded</option>
          </select>
          <span className="text-sm text-gray-500">Showing {sortedResidents.length} resident{sortedResidents.length !== 1 ? 's' : ''}</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-sm text-gray-500">{data?.academicYear || 'Loading...'} Academic Year</span>
          <button
            onClick={() => refetch()}
            disabled={isFetching}
            className="flex items-center gap-2 px-3 py-2 text-sm text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-md transition-colors disabled:opacity-50"
            aria-label="Refresh data"
          >
            <RefreshCw className={`w-4 h-4 ${isFetching ? 'animate-spin' : ''}`} />
            Refresh
          </button>
        </div>
      </div>

      {/* Table */}
      {isLoading ? (
        <div className="card" role="status" aria-live="polite">
          <div className="p-8 flex items-center justify-center">
            <RefreshCw className="w-8 h-8 text-gray-400 animate-spin" aria-hidden="true" />
            <span className="sr-only">Loading resident data...</span>
          </div>
        </div>
      ) : (
        <div className="card overflow-hidden p-0">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:text-gray-700" onClick={() => handleSort('name')}>
                    <div className="flex items-center gap-1">Resident{sortField === 'name' && (sortDirection === 'asc' ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />)}</div>
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Progress</th>
                  <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:text-gray-700" onClick={() => handleSort('days_used')}>
                    <div className="flex items-center justify-center gap-1">Days Used{sortField === 'days_used' && (sortDirection === 'asc' ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />)}</div>
                  </th>
                  <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">Remaining</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:text-gray-700" onClick={() => handleSort('status')}>
                    <div className="flex items-center gap-1">Status{sortField === 'status' && (sortDirection === 'asc' ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />)}</div>
                  </th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {sortedResidents.length === 0 ? (
                  <tr><td colSpan={6} className="px-4 py-12 text-center text-gray-500">No residents found matching the selected filter.</td></tr>
                ) : (
                  sortedResidents.map((summary) => {
                    const person = personMap.get(summary.personId);
                    return (
                      <AwayFromProgramResidentRow
                        key={summary.personId}
                        summary={summary}
                        personName={person?.name || 'Unknown'}
                        pgyLevel={person?.pgyLevel}
                        isExpanded={expandedIds.has(summary.personId)}
                        onToggle={() => toggleExpanded(summary.personId)}
                      />
                    );
                  })
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}

function AwayFromProgramSummaryCard({ title, value, icon: Icon, color, bgColor }: { title: string; value: number; icon: typeof Users; color: string; bgColor: string }) {
  return (
    <div className={`rounded-xl border border-gray-200 ${bgColor} p-4`}>
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm text-gray-500">{title}</p>
          <p className={`text-2xl font-bold ${color}`}>{value}</p>
        </div>
        <Icon className={`w-8 h-8 ${color} opacity-50`} aria-hidden="true" />
      </div>
    </div>
  );
}

function AwayFromProgramProgressBar({ daysUsed, maxDays, warningDays, status }: { daysUsed: number; maxDays: number; warningDays: number; status: ThresholdStatus }) {
  const percentage = Math.min((daysUsed / maxDays) * 100, 100);
  const warningPercentage = (warningDays / maxDays) * 100;
  const barColor = status === 'ok' ? 'bg-green-500' : status === 'warning' ? 'bg-yellow-500' : status === 'critical' ? 'bg-orange-500' : 'bg-red-500';

  return (
    <div className="w-full">
      <div className="relative h-2 bg-gray-200 rounded-full overflow-hidden">
        <div className="absolute top-0 bottom-0 w-0.5 bg-yellow-400 z-10" style={{ left: `${warningPercentage}%` }} aria-hidden="true" />
        <div className="absolute top-0 bottom-0 w-0.5 bg-red-400 z-10" style={{ left: '100%', transform: 'translateX(-100%)' }} aria-hidden="true" />
        <div className={`h-full ${barColor} transition-all duration-300`} style={{ width: `${percentage}%` }} role="progressbar" aria-valuenow={daysUsed} aria-valuemin={0} aria-valuemax={maxDays} aria-label={`${daysUsed} of ${maxDays} days used`} />
      </div>
      <div className="flex justify-between mt-1 text-xs text-gray-400">
        <span>0</span>
        <span className="text-yellow-600">{warningDays}</span>
        <span className="text-red-600">{maxDays}</span>
      </div>
    </div>
  );
}

function AwayFromProgramStatusBadge({ status, size = 'md' }: { status: ThresholdStatus; size?: 'sm' | 'md' }) {
  const config = STATUS_CONFIG[status];
  const Icon = config.icon;
  const sizeClass = size === 'sm' ? 'px-2 py-0.5 text-xs' : 'px-3 py-1 text-sm';

  return (
    <span className={`inline-flex items-center gap-1 rounded-full font-medium border ${config.bgColor} ${config.color} ${config.borderColor} ${sizeClass}`}>
      <Icon className={size === 'sm' ? 'w-3 h-3' : 'w-4 h-4'} aria-hidden="true" />
      {config.label}
    </span>
  );
}

function AwayFromProgramResidentRow({ summary, personName, pgyLevel, isExpanded, onToggle }: { summary: AwayFromProgramSummary; personName: string; pgyLevel?: number; isExpanded: boolean; onToggle: () => void }) {
  const config = STATUS_CONFIG[summary.thresholdStatus];

  return (
    <>
      <tr className={`hover:bg-gray-50 cursor-pointer transition-colors ${isExpanded ? 'bg-gray-50' : ''}`} onClick={onToggle}>
        <td className="px-4 py-3 whitespace-nowrap">
          <div className="flex items-center gap-2">
            {isExpanded ? <ChevronUp className="w-4 h-4 text-gray-400" aria-hidden="true" /> : <ChevronDown className="w-4 h-4 text-gray-400" aria-hidden="true" />}
            <div>
              <div className="text-sm font-medium text-gray-900">{personName}</div>
              {pgyLevel && <div className="text-xs text-gray-500">PGY-{pgyLevel}</div>}
            </div>
          </div>
        </td>
        <td className="px-4 py-3 whitespace-nowrap">
          <div className="w-32">
            <AwayFromProgramProgressBar daysUsed={summary.daysUsed} maxDays={summary.maxDays} warningDays={summary.warningDays} status={summary.thresholdStatus} />
          </div>
        </td>
        <td className="px-4 py-3 whitespace-nowrap text-center">
          <span className={`text-lg font-semibold ${config.color}`}>{summary.daysUsed}</span>
          <span className="text-gray-400"> / {summary.maxDays}</span>
        </td>
        <td className="px-4 py-3 whitespace-nowrap text-center">
          <span className={`text-sm ${summary.daysRemaining <= 0 ? 'text-red-600' : summary.daysRemaining <= 7 ? 'text-yellow-600' : 'text-gray-500'}`}>{summary.daysRemaining}</span>
        </td>
        <td className="px-4 py-3 whitespace-nowrap">
          <AwayFromProgramStatusBadge status={summary.thresholdStatus} size="sm" />
        </td>
        <td className="px-4 py-3 whitespace-nowrap text-right">
          <button onClick={(e) => { e.stopPropagation(); }} className="text-purple-600 hover:text-purple-800 p-1 hover:bg-purple-50 rounded transition-colors" title="View details" aria-label={`View details for ${personName}`}>
            <Eye className="w-4 h-4" />
          </button>
        </td>
      </tr>
      {isExpanded && summary.absences.length > 0 && (
        <tr>
          <td colSpan={6} className="px-4 py-2 bg-gray-50">
            <div className="pl-8">
              <p className="text-xs text-gray-500 mb-2">Contributing Absences:</p>
              <div className="space-y-1">
                {summary.absences.map((absence) => (
                  <div key={absence.id} className="flex items-center gap-4 text-xs text-gray-600">
                    <CalendarDays className="w-3 h-3 text-gray-400" aria-hidden="true" />
                    <span>{new Date(absence.startDate).toLocaleDateString()} - {new Date(absence.endDate).toLocaleDateString()}</span>
                    <span className="px-2 py-0.5 bg-gray-200 rounded text-gray-700 capitalize">{absence.absenceType.replace('_', ' ')}</span>
                    <span className="text-gray-500">{absence.days} days</span>
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
// Main Component
// ============================================================================

export default function ComplianceHubPage() {
  const searchParams = useSearchParams();
  const tabParam = searchParams.get('tab');
  const defaultTab: TabId = tabParam === 'away-from-program' ? 'away-from-program' : 'acgme';

  const tabs = [
    { id: 'acgme' as TabId, label: 'ACGME Compliance', icon: <Shield className="w-4 h-4" aria-hidden="true" />, content: <ACGMEComplianceTab /> },
    { id: 'away-from-program' as TabId, label: 'Away-From-Program', icon: <Plane className="w-4 h-4" aria-hidden="true" />, content: <AwayFromProgramTab /> },
  ];

  return (
    <ProtectedRoute>
      <RiskBar tier={0} label="Read-only" tooltip="Compliance data is view-only. No modifications can be made from this page." />
      <div className="max-w-7xl mx-auto px-4 py-8">
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-gray-900">Compliance Hub</h1>
          <p className="text-gray-600">Monitor ACGME work hour compliance and away-from-program status</p>
        </div>
        <Tabs tabs={tabs} defaultTab={defaultTab} />
      </div>
    </ProtectedRoute>
  );
}
