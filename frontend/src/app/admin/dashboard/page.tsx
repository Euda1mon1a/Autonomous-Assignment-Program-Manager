'use client';

/**
 * Admin Dashboard Summary
 *
 * Overview page displaying key system metrics:
 * - User counts (total, active)
 * - People counts (residents, faculty)
 * - Absence tracking (active, upcoming)
 * - Swap status (pending, approved, executed)
 * - Conflict status (new, acknowledged, resolved)
 */
import {
  Users,
  UserCheck,
  Calendar,
  ArrowLeftRight,
  AlertTriangle,
  RefreshCw,
  CheckCircle2,
  Clock,
  XCircle,
  Undo2,
} from 'lucide-react';
import { useAdminDashboardSummary } from '@/hooks/useAdminDashboard';
import { SectionErrorBoundary } from '@/components/SectionErrorBoundary';

// ============================================================================
// Helper Components
// ============================================================================

function MetricCard({
  label,
  value,
  subLabel,
  subValue,
  icon: Icon,
  variant = 'default',
}: {
  label: string;
  value: number;
  subLabel?: string;
  subValue?: number;
  icon: React.ElementType;
  variant?: 'default' | 'success' | 'warning' | 'danger';
}) {
  const variantStyles = {
    default: 'bg-slate-800/50 border-slate-700',
    success: 'bg-green-900/20 border-green-700/50',
    warning: 'bg-yellow-900/20 border-yellow-700/50',
    danger: 'bg-red-900/20 border-red-700/50',
  };

  const iconStyles = {
    default: 'text-slate-400',
    success: 'text-green-400',
    warning: 'text-yellow-400',
    danger: 'text-red-400',
  };

  return (
    <div className={`rounded-lg border p-4 ${variantStyles[variant]}`}>
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm text-slate-400">{label}</p>
          <p className="text-2xl font-semibold text-white">{value.toLocaleString()}</p>
          {subLabel && subValue !== undefined && (
            <p className="text-xs text-slate-500 mt-1">
              {subLabel}: {subValue.toLocaleString()}
            </p>
          )}
        </div>
        <Icon className={`w-8 h-8 ${iconStyles[variant]}`} />
      </div>
    </div>
  );
}

function MetricGroup({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <div className="space-y-3">
      <h3 className="text-sm font-medium text-slate-300 uppercase tracking-wider">
        {title}
      </h3>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {children}
      </div>
    </div>
  );
}

function LoadingSkeleton() {
  return (
    <div className="animate-pulse space-y-6">
      {[1, 2, 3].map((group) => (
        <div key={group} className="space-y-3">
          <div className="h-4 w-24 bg-slate-700 rounded" />
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {[1, 2, 3].map((card) => (
              <div key={card} className="h-24 bg-slate-800/50 rounded-lg border border-slate-700" />
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}

function ErrorState({ message, onRetry }: { message: string; onRetry: () => void }) {
  return (
    <div className="flex flex-col items-center justify-center py-12 text-center">
      <AlertTriangle className="w-12 h-12 text-red-400 mb-4" />
      <h3 className="text-lg font-medium text-white mb-2">Failed to load dashboard</h3>
      <p className="text-sm text-slate-400 mb-4">{message}</p>
      <button
        onClick={onRetry}
        className="flex items-center gap-2 px-4 py-2 bg-slate-700 hover:bg-slate-600 rounded-lg text-sm text-white transition-colors"
      >
        <RefreshCw className="w-4 h-4" />
        Retry
      </button>
    </div>
  );
}

// ============================================================================
// Main Component
// ============================================================================

export default function AdminDashboardPage() {
  const { data, isLoading, isError, error, refetch } = useAdminDashboardSummary({
    refetchInterval: 60 * 1000, // Refresh every minute
  });

  if (isLoading) {
    return (
      <div className="p-6">
        <h1 className="text-2xl font-bold text-white mb-6">Dashboard</h1>
        <LoadingSkeleton />
      </div>
    );
  }

  if (isError) {
    return (
      <div className="p-6">
        <h1 className="text-2xl font-bold text-white mb-6">Dashboard</h1>
        <ErrorState
          message={error?.message ?? 'Unknown error'}
          onRetry={() => refetch()}
        />
      </div>
    );
  }

  if (!data) {
    return (
      <div className="p-6">
        <h1 className="text-2xl font-bold text-white mb-6">Dashboard</h1>
        <p className="text-slate-400">No data available</p>
      </div>
    );
  }

  const { users, people, absences, swaps, conflicts } = data;

  return (
    <div className="p-6 space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Dashboard</h1>
          <p className="text-sm text-slate-400 mt-1">
            Last updated: {new Date(data.timestamp).toLocaleString()}
          </p>
        </div>
        <button
          onClick={() => refetch()}
          className="flex items-center gap-2 px-3 py-2 bg-slate-700 hover:bg-slate-600 rounded-lg text-sm text-white transition-colors"
        >
          <RefreshCw className="w-4 h-4" />
          Refresh
        </button>
      </div>

      {/* Users & People */}
      <SectionErrorBoundary sectionName="Users & Personnel">
        <MetricGroup title="Users & Personnel">
          <MetricCard
            label="Total Users"
            value={users.total}
            subLabel="Active"
            subValue={users.active}
            icon={Users}
          />
          <MetricCard
            label="Residents"
            value={people.residents}
            icon={UserCheck}
          />
          <MetricCard
            label="Faculty"
            value={people.faculty}
            subLabel="Total People"
            subValue={people.total}
            icon={UserCheck}
          />
        </MetricGroup>
      </SectionErrorBoundary>

      {/* Absences */}
      <SectionErrorBoundary sectionName="Absences">
        <MetricGroup title="Absences">
          <MetricCard
            label="Active Absences"
            value={absences.active}
            icon={Calendar}
            variant={absences.active > 5 ? 'warning' : 'default'}
          />
          <MetricCard
            label="Upcoming"
            value={absences.upcoming}
            icon={Clock}
          />
        </MetricGroup>
      </SectionErrorBoundary>

      {/* Swaps */}
      <SectionErrorBoundary sectionName="Swap Requests">
        <MetricGroup title="Swap Requests">
          <MetricCard
            label="Pending"
            value={swaps.pending}
            icon={ArrowLeftRight}
            variant={swaps.pending > 0 ? 'warning' : 'default'}
          />
          <MetricCard
            label="Approved"
            value={swaps.approved}
            icon={CheckCircle2}
            variant="success"
          />
          <MetricCard
            label="Executed"
            value={swaps.executed}
            icon={CheckCircle2}
          />
          <MetricCard
            label="Rejected"
            value={swaps.rejected}
            icon={XCircle}
          />
          <MetricCard
            label="Rolled Back"
            value={swaps.rolledBack}
            icon={Undo2}
            variant={swaps.rolledBack > 0 ? 'warning' : 'default'}
          />
        </MetricGroup>
      </SectionErrorBoundary>

      {/* Conflicts */}
      <SectionErrorBoundary sectionName="Schedule Conflicts">
        <MetricGroup title="Schedule Conflicts">
          <MetricCard
            label="New Conflicts"
            value={conflicts.new}
            icon={AlertTriangle}
            variant={conflicts.new > 0 ? 'danger' : 'default'}
          />
          <MetricCard
            label="Acknowledged"
            value={conflicts.acknowledged}
            icon={CheckCircle2}
          />
          <MetricCard
            label="Resolved"
            value={conflicts.resolved}
            icon={CheckCircle2}
            variant="success"
          />
          <MetricCard
            label="Ignored"
            value={conflicts.ignored}
            icon={XCircle}
          />
        </MetricGroup>
      </SectionErrorBoundary>
    </div>
  );
}
