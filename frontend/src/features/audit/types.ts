/**
 * Audit Log Types and Interfaces
 *
 * Defines the data structures for audit logging functionality,
 * including log entries, filters, and change tracking.
 */

// ============================================================================
// Core Audit Types
// ============================================================================

/**
 * Supported entity types that can be audited
 */
export type AuditEntityType =
  | 'assignment'
  | 'person'
  | 'absence'
  | 'rotation_template'
  | 'schedule_run'
  | 'block'
  | 'system';

/**
 * Types of actions that can be logged
 */
export type AuditActionType =
  | 'create'
  | 'update'
  | 'delete'
  | 'override'
  | 'restore'
  | 'bulk_import'
  | 'bulk_delete'
  | 'schedule_generate'
  | 'schedule_validate'
  | 'login'
  | 'logout'
  | 'export';

/**
 * Severity levels for audit events
 */
export type AuditSeverity = 'info' | 'warning' | 'critical';

/**
 * Single field change tracking
 */
export interface FieldChange {
  field: string;
  oldValue: unknown;
  newValue: unknown;
  displayName?: string;
}

/**
 * User who performed the action
 */
export interface AuditUser {
  id: string;
  name: string;
  email?: string;
  role?: string;
}

/**
 * Core audit log entry
 */
export interface AuditLogEntry {
  id: string;
  timestamp: string;
  entityType: AuditEntityType;
  entityId: string;
  entityName?: string;
  action: AuditActionType;
  severity: AuditSeverity;
  user: AuditUser;
  changes?: FieldChange[];
  metadata?: Record<string, unknown>;
  ipAddress?: string;
  userAgent?: string;
  sessionId?: string;
  reason?: string;
  acgmeOverride?: boolean;
  acgmeJustification?: string;
}

// ============================================================================
// Filter and Search Types
// ============================================================================

/**
 * Date range for filtering
 */
export interface DateRange {
  start: string;
  end: string;
}

/**
 * Audit log filters
 */
export interface AuditLogFilters {
  dateRange?: DateRange;
  entityTypes?: AuditEntityType[];
  actions?: AuditActionType[];
  userIds?: string[];
  severity?: AuditSeverity[];
  searchQuery?: string;
  entityId?: string;
  acgmeOverridesOnly?: boolean;
}

/**
 * Sort configuration
 */
export interface AuditLogSort {
  field: 'timestamp' | 'entityType' | 'action' | 'user' | 'severity';
  direction: 'asc' | 'desc';
}

/**
 * Pagination configuration
 */
export interface AuditLogPagination {
  page: number;
  pageSize: number;
}

/**
 * Complete query parameters for fetching audit logs
 */
export interface AuditLogQueryParams {
  filters?: AuditLogFilters;
  sort?: AuditLogSort;
  pagination?: AuditLogPagination;
}

// ============================================================================
// API Response Types
// ============================================================================

/**
 * Paginated audit log response
 */
export interface AuditLogResponse {
  items: AuditLogEntry[];
  total: number;
  page: number;
  pageSize: number;
  totalPages: number;
}

/**
 * Audit statistics for dashboard
 */
export interface AuditStatistics {
  totalEntries: number;
  entriesByAction: Record<AuditActionType, number>;
  entriesByEntityType: Record<AuditEntityType, number>;
  entriesBySeverity: Record<AuditSeverity, number>;
  acgmeOverrideCount: number;
  uniqueUsers: number;
  dateRange: DateRange;
}

/**
 * Timeline event for visual display
 */
export interface TimelineEvent {
  id: string;
  timestamp: string;
  title: string;
  description: string;
  entityType: AuditEntityType;
  action: AuditActionType;
  severity: AuditSeverity;
  user: AuditUser;
  icon?: string;
  color?: string;
}

// ============================================================================
// Export Types
// ============================================================================

/**
 * Export format options
 */
export type ExportFormat = 'csv' | 'json' | 'pdf';

/**
 * Export configuration
 */
export interface AuditExportConfig {
  format: ExportFormat;
  filters?: AuditLogFilters;
  includeMetadata?: boolean;
  includeChanges?: boolean;
  dateFormat?: string;
}

// ============================================================================
// UI State Types
// ============================================================================

/**
 * View mode for audit log display
 */
export type AuditViewMode = 'table' | 'timeline' | 'comparison';

/**
 * Selected entries for comparison
 */
export interface ComparisonSelection {
  before?: AuditLogEntry;
  after?: AuditLogEntry;
}

/**
 * Audit page state
 */
export interface AuditPageState {
  viewMode: AuditViewMode;
  filters: AuditLogFilters;
  sort: AuditLogSort;
  pagination: AuditLogPagination;
  selectedEntry?: AuditLogEntry;
  comparisonSelection: ComparisonSelection;
  isExportModalOpen: boolean;
  isFilterPanelOpen: boolean;
}

// ============================================================================
// Constants
// ============================================================================

/**
 * Display labels for entity types
 */
export const ENTITY_TYPE_LABELS: Record<AuditEntityType, string> = {
  assignment: 'Assignment',
  person: 'Person',
  absence: 'Absence',
  rotation_template: 'Rotation Template',
  schedule_run: 'Schedule Run',
  block: 'Block',
  system: 'System',
};

/**
 * Display labels for action types
 */
export const ACTION_TYPE_LABELS: Record<AuditActionType, string> = {
  create: 'Created',
  update: 'Updated',
  delete: 'Deleted',
  override: 'Override',
  restore: 'Restored',
  bulk_import: 'Bulk Import',
  bulk_delete: 'Bulk Delete',
  schedule_generate: 'Schedule Generated',
  schedule_validate: 'Schedule Validated',
  login: 'Login',
  logout: 'Logout',
  export: 'Export',
};

/**
 * Colors for severity levels
 */
export const SEVERITY_COLORS: Record<AuditSeverity, string> = {
  info: 'blue',
  warning: 'yellow',
  critical: 'red',
};

/**
 * Icons for action types (lucide-react icon names)
 */
export const ACTION_ICONS: Record<AuditActionType, string> = {
  create: 'Plus',
  update: 'Pencil',
  delete: 'Trash2',
  override: 'AlertTriangle',
  restore: 'RotateCcw',
  bulk_import: 'Upload',
  bulk_delete: 'Trash',
  schedule_generate: 'Calendar',
  schedule_validate: 'CheckCircle',
  login: 'LogIn',
  logout: 'LogOut',
  export: 'Download',
};

/**
 * Default pagination settings
 */
export const DEFAULT_PAGE_SIZE = 25;
export const PAGE_SIZE_OPTIONS = [10, 25, 50, 100];

/**
 * Default sort configuration
 */
export const DEFAULT_SORT: AuditLogSort = {
  field: 'timestamp',
  direction: 'desc',
};
