/**
 * Admin Audit Log Types
 *
 * Types for the admin audit log viewer including
 * log entries, filtering, and export functionality.
 */

// ============================================================================
// Audit Event Types
// ============================================================================

export type AuditCategory =
  | 'authentication'
  | 'authorization'
  | 'schedule'
  | 'user'
  | 'swap'
  | 'absence'
  | 'system'
  | 'data';

export type AuditSeverity = 'info' | 'warning' | 'error' | 'critical';

export type AuditAction =
  // Authentication
  | 'login'
  | 'logout'
  | 'login_failed'
  | 'password_reset'
  | 'mfa_enabled'
  | 'mfa_disabled'
  // Schedule
  | 'schedule_generated'
  | 'schedule_approved'
  | 'schedule_rejected'
  | 'assignment_created'
  | 'assignment_updated'
  | 'assignment_deleted'
  | 'assignment_locked'
  | 'assignment_unlocked'
  // User management
  | 'user_created'
  | 'user_updated'
  | 'user_deleted'
  | 'user_activated'
  | 'user_deactivated'
  | 'role_changed'
  // Swaps
  | 'swap_requested'
  | 'swap_approved'
  | 'swap_rejected'
  | 'swap_executed'
  | 'swap_cancelled'
  // Absences
  | 'absence_requested'
  | 'absence_approved'
  | 'absence_rejected'
  | 'absence_cancelled'
  // System
  | 'settings_updated'
  | 'backup_created'
  | 'backup_restored'
  | 'data_imported'
  | 'data_exported'
  | 'maintenance_started'
  | 'maintenance_ended';

// ============================================================================
// Audit Entry Types
// ============================================================================

export interface AuditEntry {
  id: string;
  timestamp: string;
  category: AuditCategory;
  action: AuditAction;
  severity: AuditSeverity;
  userId?: string;
  userName?: string;
  targetId?: string;
  targetType?: string;
  targetName?: string;
  ipAddress?: string;
  userAgent?: string;
  details?: Record<string, unknown>;
  oldValue?: unknown;
  newValue?: unknown;
  success: boolean;
  errorMessage?: string;
}

export interface AuditEntryDetail extends AuditEntry {
  stackTrace?: string;
  requestBody?: Record<string, unknown>;
  responseBody?: Record<string, unknown>;
  correlationId?: string;
  sessionId?: string;
}

// ============================================================================
// Filter Types
// ============================================================================

export interface AuditFilters {
  search?: string;
  categories?: AuditCategory[];
  actions?: AuditAction[];
  severities?: AuditSeverity[];
  userIds?: string[];
  dateRange?: {
    start: string;
    end: string;
  };
  success?: boolean;
}

export interface AuditSortOptions {
  field: 'timestamp' | 'category' | 'action' | 'severity' | 'user';
  direction: 'asc' | 'desc';
}

// ============================================================================
// Aggregation Types
// ============================================================================

export interface AuditStats {
  totalEntries: number;
  entriesByCategory: Record<AuditCategory, number>;
  entriesBySeverity: Record<AuditSeverity, number>;
  recentFailures: number;
  activeUsers24h: number;
  topActions: { action: AuditAction; count: number }[];
}

export interface AuditTimeline {
  timestamp: string;
  count: number;
  categories: Record<AuditCategory, number>;
}

// ============================================================================
// Export Types
// ============================================================================

export type AuditExportFormat = 'csv' | 'json' | 'pdf';

export interface AuditExportRequest {
  format: AuditExportFormat;
  filters: AuditFilters;
  includeDetails: boolean;
  dateRange: {
    start: string;
    end: string;
  };
}

// ============================================================================
// API Response Types
// ============================================================================

export interface AuditLogsResponse {
  entries: AuditEntry[];
  total: number;
  page: number;
  pageSize: number;
  stats: AuditStats;
}

// ============================================================================
// State Types
// ============================================================================

export type AuditViewMode = 'list' | 'timeline' | 'stats';

export interface AuditLogState {
  viewMode: AuditViewMode;
  filters: AuditFilters;
  sort: AuditSortOptions;
  selectedEntry?: AuditEntry;
  isExporting: boolean;
}

// ============================================================================
// Display Constants
// ============================================================================

export const AUDIT_CATEGORY_LABELS: Record<AuditCategory, string> = {
  authentication: 'Authentication',
  authorization: 'Authorization',
  schedule: 'Schedule',
  user: 'User Management',
  swap: 'Swaps',
  absence: 'Absences',
  system: 'System',
  data: 'Data',
};

export const AUDIT_CATEGORY_COLORS: Record<AuditCategory, string> = {
  authentication: 'bg-blue-100 text-blue-800',
  authorization: 'bg-purple-100 text-purple-800',
  schedule: 'bg-green-100 text-green-800',
  user: 'bg-yellow-100 text-yellow-800',
  swap: 'bg-orange-100 text-orange-800',
  absence: 'bg-red-100 text-red-800',
  system: 'bg-gray-100 text-gray-800',
  data: 'bg-teal-100 text-teal-800',
};

export const AUDIT_SEVERITY_COLORS: Record<AuditSeverity, string> = {
  info: 'bg-blue-100 text-blue-800',
  warning: 'bg-yellow-100 text-yellow-800',
  error: 'bg-red-100 text-red-800',
  critical: 'bg-red-200 text-red-900',
};
