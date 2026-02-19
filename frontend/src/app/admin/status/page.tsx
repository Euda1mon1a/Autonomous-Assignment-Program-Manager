'use client';

/**
 * Admin Service Status Dashboard
 *
 * Focused status page showing native service health for core infrastructure:
 * Postgres, Redis, Backend API, and Frontend. Uses the `/api/health/deep`
 * endpoint for real-time connectivity checks with auto-refresh.
 */
import { useMemo } from 'react';
import {
  Activity,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  Database,
  Server,
  Globe,
  RefreshCw,
  Clock,
  Zap,
} from 'lucide-react';
import { useHealthDeep } from '@/hooks/useHealth';
import type { HealthDeepCheck } from '@/hooks/useHealth';

// ============================================================================
// Types
// ============================================================================

type StatusLevel = 'healthy' | 'degraded' | 'unhealthy' | 'unknown';

interface ServiceCardData {
  id: string;
  name: string;
  icon: React.ElementType;
  status: StatusLevel;
  connected: boolean;
  responseTimeMs: number | null;
  lastCheck: string | null;
  error: string | null;
  warning: string | null;
  details: Record<string, unknown> | null;
}

// ============================================================================
// Constants
// ============================================================================

const STATUS_CONFIG: Record<StatusLevel, { color: string; bgColor: string; icon: React.ElementType; label: string }> = {
  healthy: { color: 'text-green-400', bgColor: 'bg-green-900/30 border-green-700/50', icon: CheckCircle2, label: 'Healthy' },
  degraded: { color: 'text-yellow-400', bgColor: 'bg-yellow-900/30 border-yellow-700/50', icon: AlertTriangle, label: 'Degraded' },
  unhealthy: { color: 'text-red-400', bgColor: 'bg-red-900/30 border-red-700/50', icon: XCircle, label: 'Unhealthy' },
  unknown: { color: 'text-slate-400', bgColor: 'bg-slate-800/50 border-slate-700/50', icon: Clock, label: 'Unknown' },
};

// ============================================================================
// Helpers
// ============================================================================

function normalizeStatus(status: string | undefined): StatusLevel {
  if (status === 'healthy' || status === 'degraded' || status === 'unhealthy') {
    return status;
  }
  return 'unknown';
}

function formatResponseTime(ms: number | null): string {
  if (ms === null || ms === undefined) return '--';
  if (ms < 1) return '<1ms';
  if (ms < 1000) return `${Math.round(ms)}ms`;
  return `${(ms / 1000).toFixed(1)}s`;
}

function formatTimestamp(ts: string | null): string {
  if (!ts) return '--';
  try {
    return new Date(ts).toLocaleTimeString();
  } catch {
    return '--';
  }
}

function buildServiceCards(
  data: { status: string; timestamp: string; version: string; checks: { database: HealthDeepCheck; redis: HealthDeepCheck } } | undefined,
  backendReachable: boolean,
): ServiceCardData[] {
  const db = data?.checks?.database;
  const redis = data?.checks?.redis;

  return [
    {
      id: 'postgres',
      name: 'PostgreSQL',
      icon: Database,
      status: db ? normalizeStatus(db.status) : 'unknown',
      connected: db?.connected ?? false,
      responseTimeMs: db?.responseTimeMs ?? null,
      lastCheck: db?.timestamp ?? null,
      error: db?.error ?? null,
      warning: db?.warning ?? null,
      details: db?.details ?? null,
    },
    {
      id: 'redis',
      name: 'Redis',
      icon: Zap,
      status: redis ? normalizeStatus(redis.status) : 'unknown',
      connected: redis?.connected ?? false,
      responseTimeMs: redis?.responseTimeMs ?? null,
      lastCheck: redis?.timestamp ?? null,
      error: redis?.error ?? null,
      warning: redis?.warning ?? null,
      details: redis?.details ?? null,
    },
    {
      id: 'backend',
      name: 'Backend API',
      icon: Server,
      status: backendReachable ? normalizeStatus(data?.status) : 'unhealthy',
      connected: backendReachable,
      responseTimeMs: null,
      lastCheck: data?.timestamp ?? null,
      error: backendReachable ? null : 'Backend API is not reachable',
      warning: null,
      details: data ? { version: data.version } : null,
    },
    {
      id: 'frontend',
      name: 'Frontend',
      icon: Globe,
      status: 'healthy',
      connected: true,
      responseTimeMs: null,
      lastCheck: new Date().toISOString(),
      error: null,
      warning: null,
      details: null,
    },
  ];
}

// ============================================================================
// Components
// ============================================================================

function OverallStatusBanner({ status, timestamp, version }: { status: StatusLevel; timestamp: string | null; version: string | null }) {
  const config = STATUS_CONFIG[status];
  const Icon = config.icon;

  return (
    <div className={`rounded-lg border p-5 ${config.bgColor}`}>
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className={`p-2.5 rounded-lg bg-slate-900/50`}>
            <Icon className={`w-7 h-7 ${config.color}`} />
          </div>
          <div>
            <h2 className="text-lg font-semibold text-white">
              System Status: {config.label}
            </h2>
            <p className="text-sm text-slate-300">
              {version && `v${version} · `}
              {timestamp ? `Last checked ${formatTimestamp(timestamp)}` : 'Waiting for first check...'}
            </p>
          </div>
        </div>
        <span className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-sm font-medium ${config.bgColor} ${config.color}`}>
          <span className={`w-2 h-2 rounded-full ${status === 'healthy' ? 'bg-green-400' : status === 'degraded' ? 'bg-yellow-400' : status === 'unhealthy' ? 'bg-red-400' : 'bg-slate-400'} ${status !== 'unknown' ? 'animate-pulse' : ''}`} />
          {config.label}
        </span>
      </div>
    </div>
  );
}

function ServiceCard({ service }: { service: ServiceCardData }) {
  const config = STATUS_CONFIG[service.status];
  const StatusIcon = config.icon;
  const ServiceIcon = service.icon;

  return (
    <div className={`rounded-lg border p-5 transition-colors ${config.bgColor}`}>
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-slate-900/50 rounded-lg">
            <ServiceIcon className="w-5 h-5 text-slate-300" />
          </div>
          <div>
            <h3 className="text-base font-medium text-white">{service.name}</h3>
            <p className="text-xs text-slate-400 mt-0.5">
              {service.connected ? 'Connected' : 'Disconnected'}
            </p>
          </div>
        </div>
        <StatusIcon className={`w-5 h-5 ${config.color}`} />
      </div>

      <div className="grid grid-cols-2 gap-3 text-sm">
        <div>
          <span className="text-slate-400">Status</span>
          <p className={`font-medium ${config.color}`}>{config.label}</p>
        </div>
        <div>
          <span className="text-slate-400">Response Time</span>
          <p className="text-white font-medium">{formatResponseTime(service.responseTimeMs)}</p>
        </div>
        <div className="col-span-2">
          <span className="text-slate-400">Last Check</span>
          <p className="text-white">{formatTimestamp(service.lastCheck)}</p>
        </div>
      </div>

      {service.error && (
        <div className="mt-3 p-2.5 bg-red-900/30 border border-red-800/50 rounded text-xs text-red-300">
          {service.error}
        </div>
      )}

      {service.warning && (
        <div className="mt-3 p-2.5 bg-yellow-900/30 border border-yellow-800/50 rounded text-xs text-yellow-300">
          {service.warning}
        </div>
      )}

      {service.details && Object.keys(service.details).length > 0 && (
        <div className="mt-3 pt-3 border-t border-slate-700/50">
          <div className="text-xs text-slate-400 space-y-1">
            {Object.entries(service.details).map(([key, value]) => (
              <div key={key} className="flex justify-between">
                <span>{key}</span>
                <span className="text-slate-300">{String(value ?? '--')}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function LoadingSkeleton() {
  return (
    <div className="animate-pulse space-y-6">
      <div className="h-20 bg-slate-800/50 rounded-lg border border-slate-700" />
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="h-48 bg-slate-800/50 rounded-lg border border-slate-700" />
        ))}
      </div>
    </div>
  );
}

function ErrorState({ message, onRetry }: { message: string; onRetry: () => void }) {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-center">
      <XCircle className="w-12 h-12 text-red-400 mb-4" />
      <h3 className="text-lg font-medium text-white mb-2">Unable to fetch service status</h3>
      <p className="text-sm text-slate-400 mb-4 max-w-md">{message}</p>
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
// Main Page
// ============================================================================

export default function AdminStatusPage() {
  const {
    data,
    isLoading,
    isError,
    isFetching,
    error,
    refetch,
    dataUpdatedAt,
  } = useHealthDeep({ refetchInterval: 30_000 });

  const backendReachable = !!data && !isError;

  const services = useMemo(
    () => buildServiceCards(data, backendReachable),
    [data, backendReachable],
  );

  const overallStatus: StatusLevel = useMemo(() => {
    if (!backendReachable) return 'unhealthy';
    if (data?.status === 'healthy') return 'healthy';
    if (data?.status === 'unhealthy') return 'unhealthy';
    return 'degraded';
  }, [data, backendReachable]);

  const healthyCount = services.filter((s) => s.status === 'healthy').length;
  const totalCount = services.length;

  if (isLoading) {
    return (
      <div className="p-6">
        <h1 className="text-2xl font-bold text-white mb-6">Service Status</h1>
        <LoadingSkeleton />
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <Activity className="w-6 h-6 text-violet-400" />
            Service Status
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            {healthyCount}/{totalCount} services healthy
            {dataUpdatedAt ? ` · Updated ${new Date(dataUpdatedAt).toLocaleTimeString()}` : ''}
          </p>
        </div>
        <button
          onClick={() => refetch()}
          disabled={isFetching}
          className="flex items-center gap-2 px-3 py-2 bg-slate-700 hover:bg-slate-600 rounded-lg text-sm text-white transition-colors disabled:opacity-50"
        >
          <RefreshCw className={`w-4 h-4 ${isFetching ? 'animate-spin' : ''}`} />
          Refresh
        </button>
      </div>

      {/* Error banner (non-blocking — still show last cached data if available) */}
      {isError && !data && (
        <ErrorState
          message={error?.message ?? 'Could not reach backend API'}
          onRetry={() => refetch()}
        />
      )}

      {isError && data && (
        <div className="p-3 bg-yellow-900/30 border border-yellow-700/50 rounded-lg flex items-center gap-2 text-sm text-yellow-300">
          <AlertTriangle className="w-4 h-4 flex-shrink-0" />
          Live health check failed. Showing last successful result.
        </div>
      )}

      {/* Overall Status */}
      {(data || !isError) && (
        <>
          <OverallStatusBanner
            status={overallStatus}
            timestamp={data?.timestamp ?? null}
            version={data?.version ?? null}
          />

          {/* Service Cards Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {services.map((service) => (
              <ServiceCard key={service.id} service={service} />
            ))}
          </div>
        </>
      )}
    </div>
  );
}
