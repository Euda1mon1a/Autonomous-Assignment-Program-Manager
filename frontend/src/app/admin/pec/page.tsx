'use client';

/**
 * PEC (Program Evaluation Committee) Dashboard
 *
 * ACGME-compliant program oversight dashboard with meeting tracking,
 * decision audit trails, and action item lifecycle management.
 *
 * @see docs/design/PEC_OPERATIONS_DESIGN.md
 */

import { useState, useMemo } from 'react';
import {
  Calendar,
  Users,
  CheckCircle2,
  Clock,
  AlertTriangle,
  TrendingUp,
  ClipboardList,
  FileText,
  RefreshCw,
  ChevronRight,
  Shield,
} from 'lucide-react';
import { format, parseISO, isAfter } from 'date-fns';

import {
  usePecDashboard,
  usePecMeetings,
  usePecActionItems,
  getMeetingStatusColor,
  getMeetingTypeLabel,
  getActionPriorityColor,
  getActionStatusColor,
} from '@/hooks/usePec';
import type {
  PecMeeting,
  PecActionItem,
  PecMeetingStatus,
  PecActionPriority,
} from '@/types/pec';

// ============ Types ============

type PecTab = 'overview' | 'meetings' | 'actions' | 'analytics';

interface TabConfig {
  id: PecTab;
  label: string;
  icon: React.ElementType;
  description: string;
}

// ============ Constants ============

const TABS: TabConfig[] = [
  { id: 'overview', label: 'Overview', icon: TrendingUp, description: 'Dashboard metrics and alerts' },
  { id: 'meetings', label: 'Meetings', icon: Calendar, description: 'PEC meeting history' },
  { id: 'actions', label: 'Action Items', icon: ClipboardList, description: 'Task tracking' },
  { id: 'analytics', label: 'Analytics', icon: FileText, description: 'Performance data (Phase 3)' },
];

const ACADEMIC_YEARS = ['AY25-26', 'AY24-25', 'AY23-24'];

const MEETING_STATUS_OPTIONS: { value: PecMeetingStatus | ''; label: string }[] = [
  { value: '', label: 'All Statuses' },
  { value: 'scheduled', label: 'Scheduled' },
  { value: 'in_progress', label: 'In Progress' },
  { value: 'completed', label: 'Completed' },
  { value: 'cancelled', label: 'Cancelled' },
];

const ACTION_PRIORITY_OPTIONS: { value: PecActionPriority | ''; label: string }[] = [
  { value: '', label: 'All Priorities' },
  { value: 'critical', label: 'Critical' },
  { value: 'high', label: 'High' },
  { value: 'medium', label: 'Medium' },
  { value: 'low', label: 'Low' },
];

// ============ Sub-Components ============

function MetricCard({
  label,
  value,
  icon: Icon,
  trend,
  alert,
}: {
  label: string;
  value: string | number;
  icon: React.ElementType;
  trend?: 'up' | 'down' | 'neutral';
  alert?: boolean;
}) {
  return (
    <div
      className={`bg-slate-800/50 border rounded-lg p-4 ${
        alert ? 'border-amber-500/50' : 'border-slate-700/50'
      }`}
    >
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div
            className={`p-2 rounded-lg ${
              alert ? 'bg-amber-500/10' : 'bg-indigo-500/10'
            }`}
          >
            <Icon
              className={`w-5 h-5 ${alert ? 'text-amber-400' : 'text-indigo-400'}`}
            />
          </div>
          <div>
            <p className="text-sm text-slate-400">{label}</p>
            <p className="text-2xl font-bold text-white">{value}</p>
          </div>
        </div>
        {trend && (
          <div
            className={`text-sm ${
              trend === 'up'
                ? 'text-green-400'
                : trend === 'down'
                  ? 'text-red-400'
                  : 'text-slate-400'
            }`}
          >
            {trend === 'up' ? '+' : trend === 'down' ? '-' : ''}
          </div>
        )}
      </div>
    </div>
  );
}

function MeetingRow({ meeting }: { meeting: PecMeeting }) {
  const statusColor = getMeetingStatusColor(meeting.status);
  const typeLabel = getMeetingTypeLabel(meeting.meetingType);

  return (
    <tr className="border-b border-slate-700/50 hover:bg-slate-800/30">
      <td className="px-4 py-3">
        <div className="flex items-center gap-2">
          <Calendar className="w-4 h-4 text-slate-400" />
          <span className="text-white font-medium">
            {format(parseISO(meeting.meetingDate), 'MMM d, yyyy')}
          </span>
        </div>
      </td>
      <td className="px-4 py-3">
        <span className="text-slate-300">{typeLabel}</span>
      </td>
      <td className="px-4 py-3">
        <div className="flex flex-wrap gap-1">
          {meeting.focusAreas.slice(0, 2).map((area, i) => (
            <span
              key={i}
              className="px-2 py-0.5 text-xs bg-slate-700/50 text-slate-300 rounded"
            >
              {area}
            </span>
          ))}
          {meeting.focusAreas.length > 2 && (
            <span className="text-xs text-slate-400">
              +{meeting.focusAreas.length - 2}
            </span>
          )}
        </div>
      </td>
      <td className="px-4 py-3">
        <span
          className={`px-2 py-1 text-xs font-medium rounded border ${statusColor}`}
        >
          {meeting.status.replace('_', ' ')}
        </span>
      </td>
      <td className="px-4 py-3 text-right">
        <div className="flex items-center justify-end gap-4 text-sm text-slate-400">
          <span title="Decisions">{meeting.decisionCount} decisions</span>
          <span title="Open Actions">{meeting.openActionCount} open</span>
          <ChevronRight className="w-4 h-4" />
        </div>
      </td>
    </tr>
  );
}

function ActionRow({ action }: { action: PecActionItem }) {
  const priorityColor = getActionPriorityColor(action.priority);
  const statusColor = getActionStatusColor(action.status);

  return (
    <tr
      className={`border-b border-slate-700/50 hover:bg-slate-800/30 ${
        action.isOverdue ? 'bg-red-500/5' : ''
      }`}
    >
      <td className="px-4 py-3">
        <div className="flex items-center gap-2">
          {action.isOverdue && (
            <AlertTriangle className="w-4 h-4 text-red-400 flex-shrink-0" />
          )}
          <span className="text-white">{action.description}</span>
        </div>
      </td>
      <td className="px-4 py-3">
        <span className="text-slate-300">{action.ownerName}</span>
      </td>
      <td className="px-4 py-3">
        {action.dueDate ? (
          <span
            className={`text-sm ${action.isOverdue ? 'text-red-400' : 'text-slate-300'}`}
          >
            {format(parseISO(action.dueDate), 'MMM d, yyyy')}
          </span>
        ) : (
          <span className="text-slate-500">No due date</span>
        )}
      </td>
      <td className="px-4 py-3">
        <span
          className={`px-2 py-1 text-xs font-medium rounded border ${priorityColor}`}
        >
          {action.priority}
        </span>
      </td>
      <td className="px-4 py-3">
        <span className={`px-2 py-1 text-xs font-medium rounded ${statusColor}`}>
          {action.status.replace('_', ' ')}
        </span>
      </td>
    </tr>
  );
}

// ============ Tab Panels ============

function OverviewTab({
  academicYear,
  isLoading,
}: {
  academicYear: string;
  isLoading: boolean;
}) {
  const { data: dashboard } = usePecDashboard(academicYear);
  const { data: meetings } = usePecMeetings({ academicYear });
  const { data: actions } = usePecActionItems();

  const upcomingMeeting = useMemo(() => {
    if (!meetings) return null;
    const now = new Date();
    return meetings.find(
      (m) => m.status === 'scheduled' && isAfter(parseISO(m.meetingDate), now)
    );
  }, [meetings]);

  const overdueActions = useMemo(() => {
    if (!actions) return [];
    return actions.filter((a) => a.isOverdue);
  }, [actions]);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="w-8 h-8 text-slate-400 animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          label="Total Residents"
          value={dashboard?.totalResidents ?? 0}
          icon={Users}
        />
        <MetricCard
          label="Meetings This Year"
          value={dashboard?.metrics.meetingsThisYear ?? 0}
          icon={Calendar}
        />
        <MetricCard
          label="Open Action Items"
          value={dashboard?.metrics.openActions ?? 0}
          icon={ClipboardList}
        />
        <MetricCard
          label="Overdue Actions"
          value={dashboard?.metrics.overdueActions ?? 0}
          icon={AlertTriangle}
          alert={(dashboard?.metrics.overdueActions ?? 0) > 0}
        />
      </div>

      {/* Command Approval Alert */}
      {(dashboard?.metrics.commandPendingCount ?? 0) > 0 && (
        <div className="bg-amber-500/10 border border-amber-500/30 rounded-lg p-4">
          <div className="flex items-center gap-3">
            <Shield className="w-5 h-5 text-amber-400" />
            <div>
              <p className="text-amber-300 font-medium">
                {dashboard?.metrics.commandPendingCount} Decision(s) Pending Command
                Approval
              </p>
              <p className="text-sm text-amber-400/70">
                Military chain of command review required before implementation
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Two Column Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Next Meeting */}
        <div className="bg-slate-800/50 border border-slate-700/50 rounded-lg p-4">
          <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
            <Calendar className="w-5 h-5 text-indigo-400" />
            Next Meeting
          </h3>
          {upcomingMeeting ? (
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-slate-300">
                  {format(parseISO(upcomingMeeting.meetingDate), 'EEEE, MMMM d, yyyy')}
                </span>
                <span
                  className={`px-2 py-1 text-xs rounded border ${getMeetingStatusColor(upcomingMeeting.status)}`}
                >
                  {getMeetingTypeLabel(upcomingMeeting.meetingType)}
                </span>
              </div>
              <div>
                <p className="text-sm text-slate-400 mb-2">Focus Areas:</p>
                <div className="flex flex-wrap gap-2">
                  {upcomingMeeting.focusAreas.map((area, i) => (
                    <span
                      key={i}
                      className="px-2 py-1 text-sm bg-indigo-500/10 text-indigo-300 rounded"
                    >
                      {area}
                    </span>
                  ))}
                </div>
              </div>
              {upcomingMeeting.location && (
                <p className="text-sm text-slate-400">
                  Location: {upcomingMeeting.location}
                </p>
              )}
            </div>
          ) : (
            <p className="text-slate-400">No upcoming meetings scheduled</p>
          )}
        </div>

        {/* Overdue Actions */}
        <div className="bg-slate-800/50 border border-slate-700/50 rounded-lg p-4">
          <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
            <AlertTriangle className="w-5 h-5 text-red-400" />
            Overdue Actions ({overdueActions.length})
          </h3>
          {overdueActions.length > 0 ? (
            <div className="space-y-3 max-h-48 overflow-y-auto">
              {overdueActions.slice(0, 5).map((action) => (
                <div
                  key={action.id}
                  className="flex items-start gap-3 p-2 bg-red-500/5 rounded"
                >
                  <Clock className="w-4 h-4 text-red-400 mt-0.5 flex-shrink-0" />
                  <div>
                    <p className="text-sm text-white">{action.description}</p>
                    <p className="text-xs text-slate-400">
                      {action.ownerName} &middot; Due{' '}
                      {action.dueDate && format(parseISO(action.dueDate), 'MMM d')}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="flex items-center gap-2 text-green-400">
              <CheckCircle2 className="w-5 h-5" />
              <span>No overdue action items</span>
            </div>
          )}
        </div>
      </div>

      {/* Recent Decisions */}
      <div className="bg-slate-800/50 border border-slate-700/50 rounded-lg p-4">
        <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
          <FileText className="w-5 h-5 text-indigo-400" />
          Recent Decisions
        </h3>
        {dashboard?.recentDecisions && dashboard.recentDecisions.length > 0 ? (
          <div className="space-y-3">
            {dashboard.recentDecisions.map((decision) => (
              <div
                key={decision.id}
                className="flex items-start justify-between p-3 bg-slate-700/30 rounded"
              >
                <div>
                  <p className="text-white">{decision.summary}</p>
                  <p className="text-sm text-slate-400 mt-1">
                    {decision.decisionType} &middot;{' '}
                    {format(parseISO(decision.createdAt), 'MMM d, yyyy')}
                  </p>
                </div>
                {decision.requiresCommandApproval && (
                  <span
                    className={`px-2 py-1 text-xs rounded ${
                      decision.commandDisposition === 'Approved'
                        ? 'bg-green-500/10 text-green-400'
                        : decision.commandDisposition === 'Pending'
                          ? 'bg-amber-500/10 text-amber-400'
                          : 'bg-slate-500/10 text-slate-400'
                    }`}
                  >
                    {decision.commandDisposition ?? 'Pending'}
                  </span>
                )}
              </div>
            ))}
          </div>
        ) : (
          <p className="text-slate-400">No recent decisions</p>
        )}
      </div>
    </div>
  );
}

function MeetingsTab({
  academicYear,
  isLoading,
}: {
  academicYear: string;
  isLoading: boolean;
}) {
  const [statusFilter, setStatusFilter] = useState<PecMeetingStatus | ''>('');

  const { data: meetings } = usePecMeetings({
    academicYear,
    status: statusFilter || undefined,
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="w-8 h-8 text-slate-400 animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Filters */}
      <div className="flex items-center gap-4">
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value as PecMeetingStatus | '')}
          className="px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white text-sm"
        >
          {MEETING_STATUS_OPTIONS.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>
        <span className="text-sm text-slate-400">
          {meetings?.length ?? 0} meeting(s)
        </span>
      </div>

      {/* Table */}
      <div className="bg-slate-800/50 border border-slate-700/50 rounded-lg overflow-hidden">
        <table className="w-full">
          <thead className="bg-slate-700/30">
            <tr>
              <th className="px-4 py-3 text-left text-sm font-medium text-slate-300">
                Date
              </th>
              <th className="px-4 py-3 text-left text-sm font-medium text-slate-300">
                Type
              </th>
              <th className="px-4 py-3 text-left text-sm font-medium text-slate-300">
                Focus Areas
              </th>
              <th className="px-4 py-3 text-left text-sm font-medium text-slate-300">
                Status
              </th>
              <th className="px-4 py-3 text-right text-sm font-medium text-slate-300">
                Summary
              </th>
            </tr>
          </thead>
          <tbody>
            {meetings && meetings.length > 0 ? (
              meetings.map((meeting) => (
                <MeetingRow key={meeting.id} meeting={meeting} />
              ))
            ) : (
              <tr>
                <td colSpan={5} className="px-4 py-8 text-center text-slate-400">
                  No meetings found
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function ActionsTab({ isLoading }: { isLoading: boolean }) {
  const [priorityFilter, setPriorityFilter] = useState<PecActionPriority | ''>('');
  const [showOverdueOnly, setShowOverdueOnly] = useState(false);

  const { data: actions } = usePecActionItems({
    priority: priorityFilter || undefined,
    overdue: showOverdueOnly || undefined,
  });

  const filteredActions = useMemo(() => {
    if (!actions) return [];
    let result = [...actions];
    if (showOverdueOnly) {
      result = result.filter((a) => a.isOverdue);
    }
    // Sort: overdue first, then by priority, then by due date
    const priorityOrder = { critical: 0, high: 1, medium: 2, low: 3 };
    result.sort((a, b) => {
      if (a.isOverdue !== b.isOverdue) return a.isOverdue ? -1 : 1;
      if (a.priority !== b.priority) {
        return priorityOrder[a.priority] - priorityOrder[b.priority];
      }
      if (a.dueDate && b.dueDate) {
        return new Date(a.dueDate).getTime() - new Date(b.dueDate).getTime();
      }
      return 0;
    });
    return result;
  }, [actions, showOverdueOnly]);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="w-8 h-8 text-slate-400 animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Filters */}
      <div className="flex items-center gap-4 flex-wrap">
        <select
          value={priorityFilter}
          onChange={(e) => setPriorityFilter(e.target.value as PecActionPriority | '')}
          className="px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white text-sm"
        >
          {ACTION_PRIORITY_OPTIONS.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>
        <label className="flex items-center gap-2 text-sm text-slate-300 cursor-pointer">
          <input
            type="checkbox"
            checked={showOverdueOnly}
            onChange={(e) => setShowOverdueOnly(e.target.checked)}
            className="rounded bg-slate-700 border-slate-600"
          />
          Overdue only
        </label>
        <span className="text-sm text-slate-400">
          {filteredActions.length} action(s)
        </span>
      </div>

      {/* Table */}
      <div className="bg-slate-800/50 border border-slate-700/50 rounded-lg overflow-hidden">
        <table className="w-full">
          <thead className="bg-slate-700/30">
            <tr>
              <th className="px-4 py-3 text-left text-sm font-medium text-slate-300">
                Description
              </th>
              <th className="px-4 py-3 text-left text-sm font-medium text-slate-300">
                Owner
              </th>
              <th className="px-4 py-3 text-left text-sm font-medium text-slate-300">
                Due Date
              </th>
              <th className="px-4 py-3 text-left text-sm font-medium text-slate-300">
                Priority
              </th>
              <th className="px-4 py-3 text-left text-sm font-medium text-slate-300">
                Status
              </th>
            </tr>
          </thead>
          <tbody>
            {filteredActions.length > 0 ? (
              filteredActions.map((action) => (
                <ActionRow key={action.id} action={action} />
              ))
            ) : (
              <tr>
                <td colSpan={5} className="px-4 py-8 text-center text-slate-400">
                  No action items found
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function AnalyticsTab() {
  return (
    <div className="bg-slate-800/50 border border-slate-700/50 rounded-lg p-8 text-center">
      <FileText className="w-12 h-12 text-slate-500 mx-auto mb-4" />
      <h3 className="text-xl font-semibold text-white mb-2">Analytics Coming Soon</h3>
      <p className="text-slate-400 max-w-md mx-auto">
        Phase 3 will add resident performance slices, rotation quality metrics, and
        program outcomes visualization. Backend integration required.
      </p>
    </div>
  );
}

// ============ Main Component ============

export default function PecDashboardPage() {
  const [activeTab, setActiveTab] = useState<PecTab>('overview');
  const [academicYear, setAcademicYear] = useState('AY25-26');
  const [isRefreshing, setIsRefreshing] = useState(false);

  const { isLoading: dashboardLoading } = usePecDashboard(academicYear);
  const { isLoading: meetingsLoading } = usePecMeetings({ academicYear });
  const { isLoading: actionsLoading } = usePecActionItems();

  const isLoading = dashboardLoading || meetingsLoading || actionsLoading;

  const handleRefresh = () => {
    setIsRefreshing(true);
    setTimeout(() => setIsRefreshing(false), 1000);
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-900 via-slate-800 to-slate-900">
      {/* Header */}
      <header className="bg-slate-800/80 border-b border-slate-700/50 backdrop-blur-sm sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div className="flex items-center gap-4">
              <div className="p-2 bg-indigo-500/10 rounded-lg">
                <Users className="w-8 h-8 text-indigo-400" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-white">
                  Program Evaluation Committee
                </h1>
                <p className="text-sm text-slate-400">
                  ACGME-compliant program oversight
                </p>
              </div>
            </div>

            <div className="flex items-center gap-4">
              {/* Academic Year Selector */}
              <select
                value={academicYear}
                onChange={(e) => setAcademicYear(e.target.value)}
                className="px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white"
                aria-label="Select academic year"
              >
                {ACADEMIC_YEARS.map((year) => (
                  <option key={year} value={year}>
                    {year}
                  </option>
                ))}
              </select>

              <button
                onClick={handleRefresh}
                disabled={isRefreshing}
                className="flex items-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-500 disabled:bg-indigo-600/50 text-white rounded-lg transition-colors"
                aria-label="Refresh data"
              >
                <RefreshCw
                  className={`w-4 h-4 ${isRefreshing ? 'animate-spin' : ''}`}
                />
                Refresh
              </button>
            </div>
          </div>

          {/* Tabs */}
          <nav className="flex gap-1 mt-4 -mb-px overflow-x-auto" role="tablist">
            {TABS.map((tab) => {
              const Icon = tab.icon;
              const isActive = activeTab === tab.id;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  role="tab"
                  aria-selected={isActive}
                  aria-controls={`${tab.id}-panel`}
                  className={`flex items-center gap-2 px-4 py-2.5 text-sm font-medium rounded-t-lg transition-all whitespace-nowrap ${
                    isActive
                      ? 'bg-slate-900 text-white border-t border-x border-slate-700'
                      : 'text-slate-400 hover:text-white hover:bg-slate-700/50'
                  }`}
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

      {/* Content */}
      <main className="max-w-7xl mx-auto px-4 py-6">
        <div role="tabpanel" id={`${activeTab}-panel`}>
          {activeTab === 'overview' && (
            <OverviewTab academicYear={academicYear} isLoading={isLoading} />
          )}
          {activeTab === 'meetings' && (
            <MeetingsTab academicYear={academicYear} isLoading={isLoading} />
          )}
          {activeTab === 'actions' && <ActionsTab isLoading={isLoading} />}
          {activeTab === 'analytics' && <AnalyticsTab />}
        </div>
      </main>

      {/* Mock Data Banner */}
      <div className="fixed bottom-4 right-4 px-4 py-2 bg-amber-600/90 text-white rounded-lg text-sm shadow-lg">
        Demo Mode - Using Mock Data
      </div>
    </div>
  );
}
