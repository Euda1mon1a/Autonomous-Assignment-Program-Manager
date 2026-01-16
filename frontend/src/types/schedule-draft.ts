/**
 * Schedule Draft API Types
 * Mirrors backend/app/schemas/schedule_draft.py
 *
 * NOTE: Uses camelCase (axios interceptor converts from snake_case)
 */

export enum ScheduleDraftStatus {
  DRAFT = "draft",
  PUBLISHED = "published",
  ROLLED_BACK = "rolled_back",
  DISCARDED = "discarded",
}

export enum DraftSourceType {
  SOLVER = "solver",
  MANUAL = "manual",
  SWAP = "swap",
  IMPORT = "import",
}

export enum DraftAssignmentChangeType {
  ADD = "add",
  MODIFY = "modify",
  DELETE = "delete",
}

export enum DraftFlagType {
  CONFLICT = "conflict",
  ACGME_VIOLATION = "acgme_violation",
  COVERAGE_GAP = "coverage_gap",
  MANUAL_REVIEW = "manual_review",
}

export enum DraftFlagSeverity {
  ERROR = "error",
  WARNING = "warning",
  INFO = "info",
}

// =============================================================================
// ScheduleDraft Types
// =============================================================================

export interface ScheduleDraftCounts {
  assignmentsTotal: number;
  added: number;
  modified: number;
  deleted: number;
  flagsTotal: number;
  flagsAcknowledged: number;
  flagsUnacknowledged: number;
}

export interface ScheduleDraftResponse {
  id: string; // UUID
  createdAt: string; // ISO Date
  createdById?: string;

  // Scope
  targetBlock?: number;
  targetStartDate: string; // YYYY-MM-DD
  targetEndDate: string; // YYYY-MM-DD

  // Status
  status: ScheduleDraftStatus;
  sourceType: DraftSourceType;

  // Source tracking
  sourceScheduleRunId?: string;

  // Publish tracking
  publishedAt?: string;
  publishedById?: string;

  // Rollback info
  rollbackAvailable: boolean;
  rollbackExpiresAt?: string;
  rolledBackAt?: string;
  rolledBackById?: string;

  // Metadata
  notes?: string;
  changeSummary?: Record<string, number>;

  // Flags
  flagsTotal: number;
  flagsAcknowledged: number;
  overrideComment?: string;
  overrideById?: string;

  // Aggregated counts
  counts: ScheduleDraftCounts;
}

export interface ScheduleDraftListItem {
  id: string;
  createdAt: string;
  status: ScheduleDraftStatus;
  sourceType: DraftSourceType;
  targetBlock?: number;
  targetStartDate: string;
  targetEndDate: string;
  flagsTotal: number;
  flagsAcknowledged: number;
  counts: ScheduleDraftCounts;
}

export interface ScheduleDraftListResponse {
  items: ScheduleDraftListItem[];
  total: number;
  page: number;
  pageSize: number;
  hasNext: boolean;
  hasPrevious: boolean;
}

// =============================================================================
// DraftAssignment Types
// =============================================================================

export interface DraftAssignmentResponse {
  id: string;
  draftId: string;

  // Assignment data
  personId: string;
  personName?: string;
  assignmentDate: string; // YYYY-MM-DD
  timeOfDay?: string; // AM/PM
  activityCode?: string;
  rotationId?: string;
  rotationName?: string;

  // Change tracking
  changeType: DraftAssignmentChangeType;
  existingAssignmentId?: string;

  // After publish
  createdAssignmentId?: string;
}

export interface DraftAssignmentCreate {
  personId: string;
  assignmentDate: string; // YYYY-MM-DD
  timeOfDay?: string; // AM/PM
  activityCode?: string;
  rotationId?: string;
  changeType?: DraftAssignmentChangeType;
  existingAssignmentId?: string;
}

// =============================================================================
// DraftFlag Types
// =============================================================================

export interface DraftFlagResponse {
  id: string;
  draftId: string;

  // Flag details
  flagType: DraftFlagType;
  severity: DraftFlagSeverity;
  message: string;

  // Related entities
  assignmentId?: string;
  personId?: string;
  personName?: string;
  affectedDate?: string;

  // Resolution
  acknowledgedAt?: string;
  acknowledgedById?: string;
  resolutionNote?: string;

  createdAt: string;
}

// =============================================================================
// Preview Types
// =============================================================================

export interface DraftPreviewResponse {
  draftId: string;

  // Summary counts
  addCount: number;
  modifyCount: number;
  deleteCount: number;

  // Flags
  flagsTotal: number;
  flagsAcknowledged: number;

  // ACGME compliance preview
  acgmeViolations: string[];

  // Detailed assignments
  assignments: DraftAssignmentResponse[];

  // Detailed flags
  flags: DraftFlagResponse[];
}

// =============================================================================
// Create/Publish/Rollback Types
// =============================================================================

export interface ScheduleDraftCreate {
  sourceType: DraftSourceType;
  targetBlock?: number;
  targetStartDate: string; // YYYY-MM-DD
  targetEndDate: string; // YYYY-MM-DD
  scheduleRunId?: string;
  notes?: string;
}

export interface PublishRequest {
  overrideComment?: string;
  validateAcgme?: boolean;
}

export interface PublishError {
  draftAssignmentId: string;
  personId: string;
  assignmentDate: string;
  errorMessage: string;
}

export interface PublishResponse {
  draftId: string;
  status: ScheduleDraftStatus;
  publishedCount: number;
  errorCount: number;
  errors: PublishError[];
  acgmeWarnings: string[];
  rollbackAvailable: boolean;
  rollbackExpiresAt?: string;
  message: string;
}

export interface RollbackResponse {
  draftId: string;
  status: ScheduleDraftStatus;
  rolledBackCount: number;
  failedCount: number;
  rolledBackAt: string;
  rolledBackById?: string;
  errors: string[];
  message: string;
}
