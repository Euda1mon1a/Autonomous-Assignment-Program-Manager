/**
 * Audit Log Feature Module
 *
 * Provides comprehensive audit logging UI components for tracking
 * and reviewing system changes, user activities, and ACGME compliance.
 *
 * Components:
 * - AuditLogPage: Main page component integrating all audit features
 * - AuditLogTable: Table view with sorting, pagination, and expandable rows
 * - AuditLogFilters: Advanced filtering and search capabilities
 * - AuditLogExport: Export functionality (CSV, JSON, PDF)
 * - AuditTimeline: Visual timeline view of audit events
 * - ChangeComparison: Side-by-side change comparison view
 *
 * Hooks:
 * - useAuditLogs: Fetch paginated audit logs with filters
 * - useAuditLogEntry: Fetch single audit log entry
 * - useAuditStatistics: Fetch audit statistics
 * - useAuditTimeline: Fetch timeline events
 * - useEntityAuditHistory: Fetch audit history for specific entity
 * - useUserAuditActivity: Fetch user's audit activity
 * - useExportAuditLogs: Export audit logs mutation
 * - useMarkAuditReviewed: Mark entries as reviewed mutation
 */

// Components
export { AuditLogPage } from './AuditLogPage';
export { AuditLogTable } from './AuditLogTable';
export { AuditLogFilters } from './AuditLogFilters';
export { AuditLogExport } from './AuditLogExport';
export { AuditTimeline } from './AuditTimeline';
export { ChangeComparison } from './ChangeComparison';

// Hooks
export {
  useAuditLogs,
  useAuditLogEntry,
  useAuditStatistics,
  useAuditTimeline,
  useEntityAuditHistory,
  useUserAuditActivity,
  useExportAuditLogs,
  useMarkAuditReviewed,
  useAuditUsers,
  usePrefetchAuditLogs,
  auditQueryKeys,
} from './hooks';

// Types
export type {
  AuditEntityType,
  AuditActionType,
  AuditSeverity,
  FieldChange,
  AuditUser,
  AuditLogEntry,
  DateRange,
  AuditLogFilters,
  AuditLogSort,
  AuditLogPagination,
  AuditLogQueryParams,
  AuditLogResponse,
  AuditStatistics,
  TimelineEvent,
  ExportFormat,
  AuditExportConfig,
  AuditViewMode,
  ComparisonSelection,
  AuditPageState,
} from './types';

// Constants
export {
  ENTITY_TYPE_LABELS,
  ACTION_TYPE_LABELS,
  SEVERITY_COLORS,
  ACTION_ICONS,
  DEFAULT_PAGE_SIZE,
  PAGE_SIZE_OPTIONS,
  DEFAULT_SORT,
} from './types';
