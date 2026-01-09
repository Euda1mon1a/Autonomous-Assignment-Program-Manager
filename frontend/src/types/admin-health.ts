/**
 * Admin System Health Types
 *
 * Types for the system health dashboard including
 * service status, metrics, and alerting.
 */

// ============================================================================
// Service Status Types
// ============================================================================

export type ServiceStatus = 'healthy' | 'degraded' | 'unhealthy' | 'unknown';

export interface ServiceHealth {
  name: string;
  status: ServiceStatus;
  latencyMs?: number;
  uptime?: number;
  lastCheck: string;
  message?: string;
  details?: Record<string, unknown>;
}

export interface ServiceComponent {
  id: string;
  name: string;
  type: 'api' | 'database' | 'cache' | 'queue' | 'external';
  health: ServiceHealth;
  dependencies?: string[];
}

// ============================================================================
// Database Health Types
// ============================================================================

export interface DatabaseHealth {
  status: ServiceStatus;
  connectionPoolSize: number;
  activeConnections: number;
  waitingConnections: number;
  maxConnections: number;
  avgQueryTimeMs: number;
  slowQueries24h: number;
  lastMigration?: string;
  diskUsagePercent: number;
  tableStats?: {
    name: string;
    rowCount: number;
    sizeBytes: number;
  }[];
}

// ============================================================================
// Cache Health Types
// ============================================================================

export interface CacheHealth {
  status: ServiceStatus;
  connectedClients: number;
  usedMemoryBytes: number;
  maxMemoryBytes: number;
  hitRate: number;
  missRate: number;
  evictedKeys24h: number;
  keyCount: number;
}

// ============================================================================
// Queue Health Types
// ============================================================================

export interface QueueHealth {
  status: ServiceStatus;
  workers: {
    active: number;
    total: number;
    idle: number;
  };
  queues: {
    name: string;
    pending: number;
    processing: number;
    completed24h: number;
    failed24h: number;
    avgProcessingTimeMs: number;
  }[];
  scheduledTasks: number;
}

// ============================================================================
// API Health Types
// ============================================================================

export interface ApiHealth {
  status: ServiceStatus;
  requestsPerMinute: number;
  avgResponseTimeMs: number;
  errorRate: number;
  activeRequests: number;
  rateLimitedRequests24h: number;
  topEndpoints: {
    path: string;
    method: string;
    count: number;
    avgTimeMs: number;
  }[];
}

// ============================================================================
// Resource Metrics Types
// ============================================================================

export interface ResourceMetrics {
  cpu: {
    usagePercent: number;
    coreCount: number;
    loadAverage: [number, number, number];
  };
  memory: {
    usedBytes: number;
    totalBytes: number;
    usagePercent: number;
  };
  disk: {
    usedBytes: number;
    totalBytes: number;
    usagePercent: number;
    readBytesPerSec: number;
    writeBytesPerSec: number;
  };
  network: {
    inBytesPerSec: number;
    outBytesPerSec: number;
    activeConnections: number;
  };
}

// ============================================================================
// Alert Types
// ============================================================================

export type AlertSeverity = 'info' | 'warning' | 'error' | 'critical';
export type AlertStatus = 'active' | 'acknowledged' | 'resolved';

export interface HealthAlert {
  id: string;
  severity: AlertSeverity;
  status: AlertStatus;
  title: string;
  message: string;
  service: string;
  triggeredAt: string;
  acknowledgedAt?: string;
  acknowledgedBy?: string;
  resolvedAt?: string;
  resolvedBy?: string;
  details?: Record<string, unknown>;
}

// ============================================================================
// Metric History Types
// ============================================================================

export interface MetricDataPoint {
  timestamp: string;
  value: number;
}

export interface MetricSeries {
  name: string;
  unit: string;
  data: MetricDataPoint[];
  current: number;
  min: number;
  max: number;
  avg: number;
}

// ============================================================================
// Overall Health Types
// ============================================================================

export interface SystemHealthSummary {
  overallStatus: ServiceStatus;
  lastUpdated: string;
  services: ServiceComponent[];
  database: DatabaseHealth;
  cache: CacheHealth;
  queue: QueueHealth;
  api: ApiHealth;
  resources: ResourceMetrics;
  activeAlerts: HealthAlert[];
  uptime: number;
  version: string;
  environment: string;
}

// ============================================================================
// API Response Types
// ============================================================================

export interface HealthCheckResponse {
  status: ServiceStatus;
  timestamp: string;
  durationMs: number;
  checks: {
    name: string;
    status: ServiceStatus;
    message?: string;
  }[];
}

export interface MetricsHistoryResponse {
  metric: string;
  period: '1h' | '6h' | '24h' | '7d' | '30d';
  data: MetricDataPoint[];
  aggregation: 'avg' | 'sum' | 'max' | 'min';
}

export interface AlertsResponse {
  alerts: HealthAlert[];
  total: number;
  active: number;
  acknowledged: number;
}

// ============================================================================
// State Types
// ============================================================================

export type HealthDashboardTab = 'overview' | 'services' | 'metrics' | 'alerts';

export interface HealthDashboardState {
  activeTab: HealthDashboardTab;
  refreshInterval: number;
  selectedService?: string;
  metricsTimeRange: '1h' | '6h' | '24h' | '7d' | '30d';
  alertFilters: {
    severities?: AlertSeverity[];
    statuses?: AlertStatus[];
    services?: string[];
  };
}

// ============================================================================
// Display Constants
// ============================================================================

export const SERVICE_STATUS_COLORS: Record<ServiceStatus, string> = {
  healthy: 'bg-green-100 text-green-800',
  degraded: 'bg-yellow-100 text-yellow-800',
  unhealthy: 'bg-red-100 text-red-800',
  unknown: 'bg-gray-100 text-gray-800',
};

export const SERVICE_STATUS_ICONS: Record<ServiceStatus, string> = {
  healthy: 'CheckCircle2',
  degraded: 'AlertTriangle',
  unhealthy: 'XCircle',
  unknown: 'HelpCircle',
};

export const ALERT_SEVERITY_COLORS: Record<AlertSeverity, string> = {
  info: 'bg-blue-100 text-blue-800 border-blue-200',
  warning: 'bg-yellow-100 text-yellow-800 border-yellow-200',
  error: 'bg-red-100 text-red-800 border-red-200',
  critical: 'bg-red-200 text-red-900 border-red-300',
};
