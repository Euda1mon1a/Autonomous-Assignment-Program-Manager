import { useState, useMemo } from 'react';
import { useRouter } from 'next/navigation';
import { CheckCircle2, AlertTriangle, AlertCircle, XCircle, ChevronDown, ChevronUp, CalendarDays, Clock, Eye, Users, RefreshCw } from 'lucide-react';
import { useAwayComplianceDashboard } from '@/hooks/useAbsences';
import { usePeople } from '@/hooks/usePeople';
import type { ThresholdStatus, AwayFromProgramSummary } from '@/types/api';

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

type SortField = 'name' | 'days_used' | 'status';
type SortDirection = 'asc' | 'desc';

export function AwayFromProgramTab() {
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
  const router = useRouter();

  const handleViewDetails = (e: React.MouseEvent) => {
    e.stopPropagation();
    // Navigate to person's schedule page which shows their full schedule including absences
    router.push(`/my-schedule?person=${summary.personId}`);
  };

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
          <button onClick={handleViewDetails} className="text-purple-600 hover:text-purple-800 p-1 hover:bg-purple-50 rounded transition-colors" title="View schedule" aria-label={`View schedule for ${personName}`}>
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
