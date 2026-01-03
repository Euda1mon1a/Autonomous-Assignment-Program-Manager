'use client';

/**
 * Admin System Health Dashboard
 *
 * Real-time monitoring of system health, services, and performance metrics.
 * Provides alerts management and historical metric visualization.
 */
import { useState, useEffect } from 'react';
import {
  Activity,
  Server,
  Database,
  Cpu,
  HardDrive,
  Wifi,
  Clock,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  HelpCircle,
  RefreshCw,
  Bell,
  BellOff,
  ChevronDown,
  ChevronUp,
  Zap,
  MemoryStick,
  ArrowUpDown,
  Timer,
  TrendingUp,
  TrendingDown,
  BarChart3,
} from 'lucide-react';
import type {
  ServiceStatus,
  SystemHealthSummary,
  HealthDashboardTab,
} from '@/types/admin-health';
import {
  SERVICE_STATUS_COLORS,
  ALERT_SEVERITY_COLORS,
} from '@/types/admin-health';

// ============================================================================
// Mock Data
// ============================================================================

const MOCK_HEALTH: SystemHealthSummary = {
  overallStatus: 'healthy',
  lastUpdated: new Date().toISOString(),
  uptime: 2592000, // 30 days in seconds
  version: '1.2.3',
  environment: 'production',
  services: [
    {
      id: 'api',
      name: 'API Server',
      type: 'api',
      health: {
        name: 'API Server',
        status: 'healthy',
        latencyMs: 45,
        uptime: 99.99,
        lastCheck: new Date().toISOString(),
      },
    },
    {
      id: 'db',
      name: 'PostgreSQL',
      type: 'database',
      health: {
        name: 'PostgreSQL',
        status: 'healthy',
        latencyMs: 12,
        uptime: 99.99,
        lastCheck: new Date().toISOString(),
      },
      dependencies: ['api'],
    },
    {
      id: 'redis',
      name: 'Redis Cache',
      type: 'cache',
      health: {
        name: 'Redis Cache',
        status: 'healthy',
        latencyMs: 2,
        uptime: 99.99,
        lastCheck: new Date().toISOString(),
      },
    },
    {
      id: 'celery',
      name: 'Celery Workers',
      type: 'queue',
      health: {
        name: 'Celery Workers',
        status: 'degraded',
        latencyMs: 150,
        uptime: 98.5,
        lastCheck: new Date().toISOString(),
        message: '1 worker offline',
      },
      dependencies: ['redis'],
    },
  ],
  database: {
    status: 'healthy',
    connectionPoolSize: 20,
    activeConnections: 8,
    waitingConnections: 0,
    maxConnections: 100,
    avgQueryTimeMs: 15,
    slowQueries24h: 3,
    lastMigration: 'abc123 - Add indexes',
    diskUsagePercent: 42,
  },
  cache: {
    status: 'healthy',
    connectedClients: 12,
    usedMemoryBytes: 256 * 1024 * 1024,
    maxMemoryBytes: 1024 * 1024 * 1024,
    hitRate: 0.94,
    missRate: 0.06,
    evictedKeys24h: 150,
    keyCount: 12500,
  },
  queue: {
    status: 'degraded',
    workers: {
      active: 3,
      total: 4,
      idle: 1,
    },
    queues: [
      { name: 'default', pending: 5, processing: 2, completed24h: 1250, failed24h: 3, avgProcessingTimeMs: 450 },
      { name: 'schedules', pending: 0, processing: 0, completed24h: 45, failed24h: 0, avgProcessingTimeMs: 12500 },
      { name: 'notifications', pending: 12, processing: 1, completed24h: 890, failed24h: 2, avgProcessingTimeMs: 120 },
    ],
    scheduledTasks: 8,
  },
  api: {
    status: 'healthy',
    requestsPerMinute: 125,
    avgResponseTimeMs: 45,
    errorRate: 0.002,
    activeRequests: 8,
    rateLimitedRequests24h: 15,
    topEndpoints: [
      { path: '/api/schedule', method: 'GET', count: 2500, avgTimeMs: 35 },
      { path: '/api/assignments', method: 'GET', count: 1800, avgTimeMs: 28 },
      { path: '/api/auth/login', method: 'POST', count: 450, avgTimeMs: 120 },
    ],
  },
  resources: {
    cpu: {
      usagePercent: 35,
      coreCount: 8,
      loadAverage: [1.2, 1.5, 1.3],
    },
    memory: {
      usedBytes: 6 * 1024 * 1024 * 1024,
      totalBytes: 16 * 1024 * 1024 * 1024,
      usagePercent: 37.5,
    },
    disk: {
      usedBytes: 42 * 1024 * 1024 * 1024,
      totalBytes: 100 * 1024 * 1024 * 1024,
      usagePercent: 42,
      readBytesPerSec: 1024 * 1024,
      writeBytesPerSec: 512 * 1024,
    },
    network: {
      inBytesPerSec: 2 * 1024 * 1024,
      outBytesPerSec: 1.5 * 1024 * 1024,
      activeConnections: 156,
    },
  },
  activeAlerts: [
    {
      id: 'alert-1',
      severity: 'warning',
      status: 'active',
      title: 'Celery Worker Offline',
      message: 'Worker celery-4 has been offline for 15 minutes',
      service: 'Celery Workers',
      triggeredAt: new Date(Date.now() - 15 * 60 * 1000).toISOString(),
    },
    {
      id: 'alert-2',
      severity: 'info',
      status: 'acknowledged',
      title: 'High Memory Usage',
      message: 'Memory usage exceeded 80% threshold briefly',
      service: 'API Server',
      triggeredAt: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
      acknowledgedAt: new Date(Date.now() - 1.5 * 60 * 60 * 1000).toISOString(),
      acknowledgedBy: 'Admin',
    },
  ],
};

// ============================================================================
// Constants
// ============================================================================

const TABS: { id: HealthDashboardTab; label: string; icon: React.ElementType }[] = [
  { id: 'overview', label: 'Overview', icon: Activity },
  { id: 'services', label: 'Services', icon: Server },
  { id: 'metrics', label: 'Metrics', icon: BarChart3 },
  { id: 'alerts', label: 'Alerts', icon: Bell },
];

const STATUS_ICONS: Record<ServiceStatus, React.ElementType> = {
  healthy: CheckCircle2,
  degraded: AlertTriangle,
  unhealthy: XCircle,
  unknown: HelpCircle,
};

// ============================================================================
// Helper Functions
// ============================================================================

function formatBytes(bytes: number): string {
  const units = ['B', 'KB', 'MB', 'GB', 'TB'];
  let unitIndex = 0;
  let value = bytes;
  while (value >= 1024 && unitIndex < units.length - 1) {
    value /= 1024;
    unitIndex++;
  }
  return `${value.toFixed(1)} ${units[unitIndex]}`;
}

function formatUptime(seconds: number): string {
  const days = Math.floor(seconds / 86400);
  const hours = Math.floor((seconds % 86400) / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  if (days > 0) return `${days}d ${hours}h`;
  if (hours > 0) return `${hours}h ${minutes}m`;
  return `${minutes}m`;
}

function formatDuration(ms: number): string {
  if (ms < 1000) return `${ms}ms`;
  return `${(ms / 1000).toFixed(1)}s`;
}

// ============================================================================
// Helper Components
// ============================================================================

function StatusIndicator({ status, size = 'md' }: { status: ServiceStatus; size?: 'sm' | 'md' | 'lg' }) {
  const Icon = STATUS_ICONS[status];
  const sizeClasses = {
    sm: 'w-4 h-4',
    md: 'w-5 h-5',
    lg: 'w-6 h-6',
  };
  const colorClasses: Record<ServiceStatus, string> = {
    healthy: 'text-green-400',
    degraded: 'text-yellow-400',
    unhealthy: 'text-red-400',
    unknown: 'text-gray-400',
  };

  return <Icon className={`${sizeClasses[size]} ${colorClasses[status]}`} />;
}

function StatusBadge({ status }: { status: ServiceStatus }) {
  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium ${SERVICE_STATUS_COLORS[status]}`}>
      <StatusIndicator status={status} size="sm" />
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
  status?: ServiceStatus;
}) {
  const trendColor = trend === 'up' ? 'text-green-400' : trend === 'down' ? 'text-red-400' : 'text-gray-400';
  const TrendIcon = trend === 'up' ? TrendingUp : trend === 'down' ? TrendingDown : null;

  return (
    <div className="bg-slate-800/50 border border-slate-700/50 rounded-lg p-4">
      <div className="flex items-center justify-between mb-2">
        <div className={`p-2 rounded-lg ${status ? SERVICE_STATUS_COLORS[status].replace('text-', 'bg-').replace('-800', '-900/50') : 'bg-slate-700/50'}`}>
          <Icon className={`w-5 h-5 ${status ? SERVICE_STATUS_COLORS[status].split(' ')[1] : 'text-slate-400'}`} />
        </div>
        {TrendIcon && (
          <TrendIcon className={`w-4 h-4 ${trendColor}`} />
        )}
      </div>
      <div className="text-2xl font-bold text-white">{value}</div>
      <div className="text-sm text-slate-400">{label}</div>
      {subValue && <div className="text-xs text-slate-500 mt-1">{subValue}</div>}
    </div>
  );
}

function ProgressBar({
  value,
  max,
  label,
  showValue = true,
  colorThresholds = { warning: 70, critical: 90 },
}: {
  value: number;
  max: number;
  label: string;
  showValue?: boolean;
  colorThresholds?: { warning: number; critical: number };
}) {
  const percentage = (value / max) * 100;
  const color =
    percentage >= colorThresholds.critical
      ? 'bg-red-500'
      : percentage >= colorThresholds.warning
      ? 'bg-yellow-500'
      : 'bg-green-500';

  return (
    <div>
      <div className="flex items-center justify-between text-sm mb-1">
        <span className="text-slate-300">{label}</span>
        {showValue && (
          <span className="text-slate-400">{percentage.toFixed(1)}%</span>
        )}
      </div>
      <div className="h-2 bg-slate-700 rounded-full overflow-hidden">
        <div
          className={`h-full ${color} rounded-full transition-all duration-300`}
          style={{ width: `${Math.min(percentage, 100)}%` }}
        />
      </div>
    </div>
  );
}

// ============================================================================
// Overview Panel
// ============================================================================

function OverviewPanel({ health }: { health: SystemHealthSummary }) {
  return (
    <div className="space-y-6">
      {/* Status Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <MetricCard
          label="Overall Status"
          value={health.overallStatus.charAt(0).toUpperCase() + health.overallStatus.slice(1)}
          icon={Activity}
          status={health.overallStatus}
        />
        <MetricCard
          label="Uptime"
          value={formatUptime(health.uptime)}
          subValue="Since last restart"
          icon={Clock}
          trend="stable"
        />
        <MetricCard
          label="Active Alerts"
          value={health.activeAlerts.length}
          icon={Bell}
          status={health.activeAlerts.length > 0 ? 'degraded' : 'healthy'}
        />
        <MetricCard
          label="API Requests/min"
          value={health.api.requestsPerMinute}
          subValue={`${formatDuration(health.api.avgResponseTimeMs)} avg`}
          icon={Zap}
          trend="up"
        />
      </div>

      {/* Services Overview */}
      <div className="bg-slate-800/50 border border-slate-700/50 rounded-lg p-6">
        <h3 className="text-lg font-medium text-white mb-4">Services</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {health.services.map((service) => (
            <div
              key={service.id}
              className="flex items-center gap-3 p-3 bg-slate-700/30 rounded-lg"
            >
              <StatusIndicator status={service.health.status} />
              <div>
                <div className="text-sm font-medium text-white">{service.name}</div>
                <div className="text-xs text-slate-400">
                  {service.health.latencyMs}ms
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Resource Usage */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-slate-800/50 border border-slate-700/50 rounded-lg p-6">
          <h3 className="text-lg font-medium text-white mb-4 flex items-center gap-2">
            <Cpu className="w-5 h-5 text-slate-400" />
            System Resources
          </h3>
          <div className="space-y-4">
            <ProgressBar
              value={health.resources.cpu.usagePercent}
              max={100}
              label="CPU Usage"
            />
            <ProgressBar
              value={health.resources.memory.usagePercent}
              max={100}
              label="Memory Usage"
            />
            <ProgressBar
              value={health.resources.disk.usagePercent}
              max={100}
              label="Disk Usage"
            />
          </div>
        </div>

        <div className="bg-slate-800/50 border border-slate-700/50 rounded-lg p-6">
          <h3 className="text-lg font-medium text-white mb-4 flex items-center gap-2">
            <Database className="w-5 h-5 text-slate-400" />
            Database
          </h3>
          <div className="space-y-4">
            <ProgressBar
              value={health.database.activeConnections}
              max={health.database.maxConnections}
              label={`Connections (${health.database.activeConnections}/${health.database.maxConnections})`}
            />
            <ProgressBar
              value={health.database.diskUsagePercent}
              max={100}
              label="Disk Usage"
            />
            <div className="flex items-center justify-between text-sm">
              <span className="text-slate-400">Avg Query Time</span>
              <span className="text-white">{health.database.avgQueryTimeMs}ms</span>
            </div>
            <div className="flex items-center justify-between text-sm">
              <span className="text-slate-400">Slow Queries (24h)</span>
              <span className={health.database.slowQueries24h > 10 ? 'text-yellow-400' : 'text-white'}>
                {health.database.slowQueries24h}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Active Alerts */}
      {health.activeAlerts.length > 0 && (
        <div className="bg-slate-800/50 border border-slate-700/50 rounded-lg p-6">
          <h3 className="text-lg font-medium text-white mb-4 flex items-center gap-2">
            <AlertTriangle className="w-5 h-5 text-yellow-400" />
            Active Alerts
          </h3>
          <div className="space-y-3">
            {health.activeAlerts.map((alert) => (
              <div
                key={alert.id}
                className={`p-4 rounded-lg border ${ALERT_SEVERITY_COLORS[alert.severity]}`}
              >
                <div className="flex items-center justify-between">
                  <div className="font-medium">{alert.title}</div>
                  <span className={`text-xs px-2 py-0.5 rounded ${
                    alert.status === 'acknowledged' ? 'bg-blue-100 text-blue-800' : 'bg-yellow-100 text-yellow-800'
                  }`}>
                    {alert.status}
                  </span>
                </div>
                <div className="text-sm mt-1 opacity-80">{alert.message}</div>
                <div className="text-xs mt-2 opacity-60">
                  {new Date(alert.triggeredAt).toLocaleString()}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

// ============================================================================
// Services Panel
// ============================================================================

function ServicesPanel({ health }: { health: SystemHealthSummary }) {
  const [expandedService, setExpandedService] = useState<string | null>(null);

  return (
    <div className="space-y-6">
      {/* Service Cards */}
      <div className="space-y-4">
        {health.services.map((service) => (
          <div
            key={service.id}
            className="bg-slate-800/50 border border-slate-700/50 rounded-lg overflow-hidden"
          >
            <button
              onClick={() => setExpandedService(expandedService === service.id ? null : service.id)}
              className="w-full flex items-center justify-between p-4 hover:bg-slate-700/30 transition-colors"
            >
              <div className="flex items-center gap-4">
                <StatusIndicator status={service.health.status} size="lg" />
                <div className="text-left">
                  <div className="text-lg font-medium text-white">{service.name}</div>
                  <div className="text-sm text-slate-400">
                    {service.type.charAt(0).toUpperCase() + service.type.slice(1)} •{' '}
                    {formatDuration(service.health.latencyMs || 0)} latency •{' '}
                    {service.health.uptime?.toFixed(2)}% uptime
                  </div>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <StatusBadge status={service.health.status} />
                {expandedService === service.id ? (
                  <ChevronUp className="w-5 h-5 text-slate-400" />
                ) : (
                  <ChevronDown className="w-5 h-5 text-slate-400" />
                )}
              </div>
            </button>

            {expandedService === service.id && (
              <div className="px-4 pb-4 pt-2 border-t border-slate-700/50">
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div>
                    <div className="text-xs text-slate-400 mb-1">Status</div>
                    <div className="text-sm text-white capitalize">{service.health.status}</div>
                  </div>
                  <div>
                    <div className="text-xs text-slate-400 mb-1">Latency</div>
                    <div className="text-sm text-white">{formatDuration(service.health.latencyMs || 0)}</div>
                  </div>
                  <div>
                    <div className="text-xs text-slate-400 mb-1">Uptime</div>
                    <div className="text-sm text-white">{service.health.uptime?.toFixed(2)}%</div>
                  </div>
                  <div>
                    <div className="text-xs text-slate-400 mb-1">Last Check</div>
                    <div className="text-sm text-white">
                      {new Date(service.health.lastCheck).toLocaleTimeString()}
                    </div>
                  </div>
                </div>
                {service.health.message && (
                  <div className="mt-3 p-3 bg-yellow-900/30 border border-yellow-800/50 rounded-lg text-sm text-yellow-200">
                    {service.health.message}
                  </div>
                )}
                {service.dependencies && service.dependencies.length > 0 && (
                  <div className="mt-3">
                    <div className="text-xs text-slate-400 mb-1">Dependencies</div>
                    <div className="flex gap-2">
                      {service.dependencies.map((dep) => (
                        <span key={dep} className="px-2 py-0.5 bg-slate-700 text-slate-300 text-xs rounded">
                          {dep}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Queue Details */}
      <div className="bg-slate-800/50 border border-slate-700/50 rounded-lg p-6">
        <h3 className="text-lg font-medium text-white mb-4 flex items-center gap-2">
          <ArrowUpDown className="w-5 h-5 text-slate-400" />
          Task Queues
        </h3>
        <div className="space-y-4">
          {health.queue.queues.map((queue) => (
            <div key={queue.name} className="p-3 bg-slate-700/30 rounded-lg">
              <div className="flex items-center justify-between mb-2">
                <span className="font-medium text-white">{queue.name}</span>
                <span className="text-sm text-slate-400">
                  {queue.completed24h} completed / {queue.failed24h} failed
                </span>
              </div>
              <div className="grid grid-cols-3 gap-4 text-sm">
                <div>
                  <span className="text-slate-400">Pending:</span>{' '}
                  <span className={queue.pending > 50 ? 'text-yellow-400' : 'text-white'}>{queue.pending}</span>
                </div>
                <div>
                  <span className="text-slate-400">Processing:</span>{' '}
                  <span className="text-white">{queue.processing}</span>
                </div>
                <div>
                  <span className="text-slate-400">Avg Time:</span>{' '}
                  <span className="text-white">{formatDuration(queue.avgProcessingTimeMs)}</span>
                </div>
              </div>
            </div>
          ))}
        </div>
        <div className="mt-4 flex items-center justify-between text-sm">
          <span className="text-slate-400">Workers: {health.queue.workers.active}/{health.queue.workers.total} active</span>
          <span className="text-slate-400">Scheduled Tasks: {health.queue.scheduledTasks}</span>
        </div>
      </div>
    </div>
  );
}

// ============================================================================
// Metrics Panel
// ============================================================================

function MetricsPanel({ health }: { health: SystemHealthSummary }) {
  return (
    <div className="space-y-6">
      {/* Resource Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          label="CPU Usage"
          value={`${health.resources.cpu.usagePercent.toFixed(1)}%`}
          subValue={`${health.resources.cpu.coreCount} cores`}
          icon={Cpu}
          status={health.resources.cpu.usagePercent > 80 ? 'degraded' : 'healthy'}
        />
        <MetricCard
          label="Memory Usage"
          value={formatBytes(health.resources.memory.usedBytes)}
          subValue={`of ${formatBytes(health.resources.memory.totalBytes)}`}
          icon={MemoryStick}
          status={health.resources.memory.usagePercent > 80 ? 'degraded' : 'healthy'}
        />
        <MetricCard
          label="Disk Usage"
          value={formatBytes(health.resources.disk.usedBytes)}
          subValue={`of ${formatBytes(health.resources.disk.totalBytes)}`}
          icon={HardDrive}
          status={health.resources.disk.usagePercent > 80 ? 'degraded' : 'healthy'}
        />
        <MetricCard
          label="Network"
          value={`${health.resources.network.activeConnections}`}
          subValue="Active connections"
          icon={Wifi}
        />
      </div>

      {/* API Metrics */}
      <div className="bg-slate-800/50 border border-slate-700/50 rounded-lg p-6">
        <h3 className="text-lg font-medium text-white mb-4 flex items-center gap-2">
          <Zap className="w-5 h-5 text-slate-400" />
          API Performance
        </h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          <div className="p-3 bg-slate-700/30 rounded-lg">
            <div className="text-2xl font-bold text-white">{health.api.requestsPerMinute}</div>
            <div className="text-sm text-slate-400">Requests/min</div>
          </div>
          <div className="p-3 bg-slate-700/30 rounded-lg">
            <div className="text-2xl font-bold text-white">{health.api.avgResponseTimeMs}ms</div>
            <div className="text-sm text-slate-400">Avg Response</div>
          </div>
          <div className="p-3 bg-slate-700/30 rounded-lg">
            <div className="text-2xl font-bold text-white">{(health.api.errorRate * 100).toFixed(2)}%</div>
            <div className="text-sm text-slate-400">Error Rate</div>
          </div>
          <div className="p-3 bg-slate-700/30 rounded-lg">
            <div className="text-2xl font-bold text-white">{health.api.rateLimitedRequests24h}</div>
            <div className="text-sm text-slate-400">Rate Limited (24h)</div>
          </div>
        </div>

        <h4 className="text-sm font-medium text-slate-300 mb-3">Top Endpoints</h4>
        <div className="space-y-2">
          {health.api.topEndpoints.map((endpoint, index) => (
            <div key={index} className="flex items-center justify-between p-2 bg-slate-700/30 rounded">
              <div className="flex items-center gap-3">
                <span className={`px-2 py-0.5 text-xs font-medium rounded ${
                  endpoint.method === 'GET' ? 'bg-green-900/50 text-green-300' :
                  endpoint.method === 'POST' ? 'bg-blue-900/50 text-blue-300' :
                  endpoint.method === 'PUT' ? 'bg-yellow-900/50 text-yellow-300' :
                  'bg-red-900/50 text-red-300'
                }`}>
                  {endpoint.method}
                </span>
                <span className="text-sm text-white font-mono">{endpoint.path}</span>
              </div>
              <div className="text-sm text-slate-400">
                {endpoint.count} calls • {endpoint.avgTimeMs}ms avg
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Cache Metrics */}
      <div className="bg-slate-800/50 border border-slate-700/50 rounded-lg p-6">
        <h3 className="text-lg font-medium text-white mb-4 flex items-center gap-2">
          <Timer className="w-5 h-5 text-slate-400" />
          Cache Performance
        </h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="p-3 bg-slate-700/30 rounded-lg">
            <div className="text-2xl font-bold text-white">{(health.cache.hitRate * 100).toFixed(1)}%</div>
            <div className="text-sm text-slate-400">Hit Rate</div>
          </div>
          <div className="p-3 bg-slate-700/30 rounded-lg">
            <div className="text-2xl font-bold text-white">{formatBytes(health.cache.usedMemoryBytes)}</div>
            <div className="text-sm text-slate-400">Memory Used</div>
          </div>
          <div className="p-3 bg-slate-700/30 rounded-lg">
            <div className="text-2xl font-bold text-white">{health.cache.keyCount.toLocaleString()}</div>
            <div className="text-sm text-slate-400">Keys</div>
          </div>
          <div className="p-3 bg-slate-700/30 rounded-lg">
            <div className="text-2xl font-bold text-white">{health.cache.evictedKeys24h}</div>
            <div className="text-sm text-slate-400">Evictions (24h)</div>
          </div>
        </div>
      </div>
    </div>
  );
}

// ============================================================================
// Alerts Panel
// ============================================================================

function AlertsPanel({ health }: { health: SystemHealthSummary }) {
  const [filter, setFilter] = useState<'all' | 'active' | 'acknowledged'>('all');

  const filteredAlerts = health.activeAlerts.filter((alert) => {
    if (filter === 'all') return true;
    return alert.status === filter;
  });

  return (
    <div className="space-y-6">
      {/* Filter Tabs */}
      <div className="flex gap-2">
        {(['all', 'active', 'acknowledged'] as const).map((f) => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            className={`px-4 py-2 text-sm font-medium rounded-lg transition-colors ${
              filter === f
                ? 'bg-violet-600 text-white'
                : 'bg-slate-800 text-slate-400 hover:text-white'
            }`}
          >
            {f.charAt(0).toUpperCase() + f.slice(1)}
          </button>
        ))}
      </div>

      {/* Alert List */}
      {filteredAlerts.length === 0 ? (
        <div className="text-center py-12">
          <BellOff className="w-12 h-12 text-slate-500 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-slate-300 mb-2">No Alerts</h3>
          <p className="text-slate-400">
            {filter === 'all' ? 'All systems operating normally' : `No ${filter} alerts`}
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {filteredAlerts.map((alert) => (
            <div
              key={alert.id}
              className={`p-4 rounded-lg border ${ALERT_SEVERITY_COLORS[alert.severity]}`}
            >
              <div className="flex items-start justify-between">
                <div className="flex items-start gap-3">
                  <AlertTriangle className="w-5 h-5 mt-0.5" />
                  <div>
                    <div className="font-medium">{alert.title}</div>
                    <div className="text-sm mt-1 opacity-80">{alert.message}</div>
                    <div className="text-xs mt-2 opacity-60">
                      Service: {alert.service} • Triggered: {new Date(alert.triggeredAt).toLocaleString()}
                    </div>
                    {alert.acknowledgedAt && (
                      <div className="text-xs mt-1 opacity-60">
                        Acknowledged by {alert.acknowledgedBy} at {new Date(alert.acknowledgedAt).toLocaleString()}
                      </div>
                    )}
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <span className={`text-xs px-2 py-0.5 rounded ${
                    alert.status === 'acknowledged' ? 'bg-blue-100 text-blue-800' : 'bg-yellow-100 text-yellow-800'
                  }`}>
                    {alert.status}
                  </span>
                  {alert.status === 'active' && (
                    <button className="px-3 py-1 text-xs font-medium bg-slate-700 hover:bg-slate-600 text-white rounded transition-colors">
                      Acknowledge
                    </button>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// ============================================================================
// Main Page Component
// ============================================================================

export default function AdminHealthPage() {
  const [activeTab, setActiveTab] = useState<HealthDashboardTab>('overview');
  const [health] = useState<SystemHealthSummary>(MOCK_HEALTH);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [lastRefresh, setLastRefresh] = useState(new Date());

  const handleRefresh = async () => {
    setIsRefreshing(true);
    // Simulate API call
    await new Promise((resolve) => setTimeout(resolve, 1000));
    setLastRefresh(new Date());
    setIsRefreshing(false);
  };

  // Auto-refresh every 30 seconds
  useEffect(() => {
    const interval = setInterval(() => {
      setLastRefresh(new Date());
    }, 30000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
      {/* Header */}
      <header className="border-b border-slate-700/50 bg-slate-900/80 backdrop-blur-sm sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-gradient-to-br from-violet-500 to-purple-600 rounded-lg">
                <Activity className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-white flex items-center gap-2">
                  System Health
                  <StatusIndicator status={health.overallStatus} />
                </h1>
                <p className="text-sm text-slate-400">
                  v{health.version} • {health.environment} • Updated {lastRefresh.toLocaleTimeString()}
                </p>
              </div>
            </div>

            <button
              onClick={handleRefresh}
              disabled={isRefreshing}
              className="flex items-center gap-2 px-4 py-2 bg-slate-800 hover:bg-slate-700 text-white rounded-lg transition-colors disabled:opacity-50"
            >
              <RefreshCw className={`w-4 h-4 ${isRefreshing ? 'animate-spin' : ''}`} />
              Refresh
            </button>
          </div>

          {/* Tabs */}
          <nav className="flex gap-1 mt-4 -mb-px">
            {TABS.map((tab) => {
              const Icon = tab.icon;
              const isActive = activeTab === tab.id;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`
                    flex items-center gap-2 px-4 py-2.5 text-sm font-medium rounded-t-lg
                    transition-all duration-200
                    ${isActive
                      ? 'bg-slate-800 text-white border-t border-x border-slate-700'
                      : 'text-slate-400 hover:text-white hover:bg-slate-800/50'
                    }
                  `}
                >
                  <Icon className="w-4 h-4" />
                  {tab.label}
                  {tab.id === 'alerts' && health.activeAlerts.length > 0 && (
                    <span className="ml-1 px-1.5 py-0.5 text-xs bg-red-500 text-white rounded-full">
                      {health.activeAlerts.length}
                    </span>
                  )}
                </button>
              );
            })}
          </nav>
        </div>
      </header>

      {/* Content */}
      <main className="max-w-7xl mx-auto px-4 py-6">
        {activeTab === 'overview' && <OverviewPanel health={health} />}
        {activeTab === 'services' && <ServicesPanel health={health} />}
        {activeTab === 'metrics' && <MetricsPanel health={health} />}
        {activeTab === 'alerts' && <AlertsPanel health={health} />}
      </main>
    </div>
  );
}
