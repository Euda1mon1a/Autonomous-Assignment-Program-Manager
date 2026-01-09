/**
 * Block Assignment Import/Export API Types
 * Mirrors backend/app/schemas/block_assignment_import.py
 */

export enum ImportFormat {
  CSV = "csv",
  XLSX = "xlsx",
}

export enum MatchStatus {
  MATCHED = "matched",
  UNKNOWN_ROTATION = "unknown_rotation",
  UNKNOWN_RESIDENT = "unknown_resident",
  DUPLICATE = "duplicate",
  INVALID = "invalid",
}

export enum DuplicateAction {
  SKIP = "skip",
  UPDATE = "update",
}

export enum ExportFormat {
  CSV = "csv",
  XLSX = "xlsx",
}

// ============================================================================
// Preview Types
// ============================================================================

export interface BlockAssignmentPreviewItem {
  rowNumber: number;
  blockNumber: number;
  rotationInput: string;
  residentDisplay: string; // Anonymized

  matchStatus: MatchStatus;
  matchedRotationId?: string;
  matchedRotationName?: string;
  rotationConfidence: number;
  matchedResidentId?: string;
  residentConfidence: number;

  isDuplicate: boolean;
  existingAssignmentId?: string;
  duplicateAction: DuplicateAction;

  errors: string[];
  warnings: string[];
}

export interface UnknownRotationItem {
  abbreviation: string;
  occurrences: number;
  suggestedName?: string;
}

export interface BlockAssignmentPreviewResponse {
  previewId: string;
  academicYear: number;
  formatDetected: ImportFormat;

  items: BlockAssignmentPreviewItem[];

  totalRows: number;
  matchedCount: number;
  unknownRotationCount: number;
  unknownResidentCount: number;
  duplicateCount: number;
  invalidCount: number;

  unknownRotations: UnknownRotationItem[];
  warnings: string[];
}

// ============================================================================
// Import Request/Result Types
// ============================================================================

export interface BlockAssignmentImportRequest {
  previewId: string;
  academicYear: number;
  skipDuplicates?: boolean;
  updateDuplicates?: boolean;
  importUnmatched?: boolean;
  rowOverrides?: Record<number, DuplicateAction>;
}

export interface BlockAssignmentImportResult {
  success: boolean;
  academicYear: number;

  totalRows: number;
  importedCount: number;
  updatedCount: number;
  skippedCount: number;
  failedCount: number;

  failedRows: number[];
  errorMessages: string[];

  startedAt: string;
  completedAt: string;
}

// ============================================================================
// Quick Template Types
// ============================================================================

export interface QuickTemplateCreateRequest {
  abbreviation: string;
  name: string;
  activityType: string;
  leaveEligible: boolean;
}

export interface QuickTemplateCreateResponse {
  id: string;
  abbreviation: string;
  name: string;
  activityType: string;
}

// ============================================================================
// Export Types
// ============================================================================

export interface BlockAssignmentExportRequest {
  format: ExportFormat;
  academicYear: number;
  blockNumbers?: number[];
  rotationIds?: string[];
  residentIds?: string[];
  includePgyLevel?: boolean;
  includeLeaveStatus?: boolean;
  groupBy?: "block" | "resident" | "rotation";
}

export interface BlockAssignmentExportResult {
  success: boolean;
  format: ExportFormat;
  filename: string;
  rowCount: number;
  downloadUrl?: string;
  data?: string; // Base64 for small exports
  generatedAt: string;
}

// ============================================================================
// Upload Request Type (for direct content upload)
// ============================================================================

export interface BlockAssignmentUploadRequest {
  content: string;
  academicYear?: number;
  format?: ImportFormat;
  blockNumber?: number;
  rotationId?: string;
}

// ============================================================================
// Helper type for row status colors
// ============================================================================

export const MATCH_STATUS_COLORS: Record<MatchStatus, string> = {
  [MatchStatus.MATCHED]: "bg-green-100 text-green-800",
  [MatchStatus.UNKNOWN_ROTATION]: "bg-yellow-100 text-yellow-800",
  [MatchStatus.UNKNOWN_RESIDENT]: "bg-red-100 text-red-800",
  [MatchStatus.DUPLICATE]: "bg-gray-100 text-gray-800",
  [MatchStatus.INVALID]: "bg-red-200 text-red-900",
};

export const MATCH_STATUS_LABELS: Record<MatchStatus, string> = {
  [MatchStatus.MATCHED]: "Matched",
  [MatchStatus.UNKNOWN_ROTATION]: "Unknown Rotation",
  [MatchStatus.UNKNOWN_RESIDENT]: "Unknown Resident",
  [MatchStatus.DUPLICATE]: "Duplicate",
  [MatchStatus.INVALID]: "Invalid",
};
