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
  row_number: number;
  block_number: number;
  rotation_input: string;
  resident_display: string; // Anonymized

  match_status: MatchStatus;
  matched_rotation_id?: string;
  matched_rotation_name?: string;
  rotation_confidence: number;
  matched_resident_id?: string;
  resident_confidence: number;

  is_duplicate: boolean;
  existing_assignment_id?: string;
  duplicate_action: DuplicateAction;

  errors: string[];
  warnings: string[];
}

export interface UnknownRotationItem {
  abbreviation: string;
  occurrences: number;
  suggested_name?: string;
}

export interface BlockAssignmentPreviewResponse {
  preview_id: string;
  academic_year: number;
  format_detected: ImportFormat;

  items: BlockAssignmentPreviewItem[];

  total_rows: number;
  matched_count: number;
  unknown_rotation_count: number;
  unknown_resident_count: number;
  duplicate_count: number;
  invalid_count: number;

  unknown_rotations: UnknownRotationItem[];
  warnings: string[];
}

// ============================================================================
// Import Request/Result Types
// ============================================================================

export interface BlockAssignmentImportRequest {
  preview_id: string;
  academic_year: number;
  skip_duplicates?: boolean;
  update_duplicates?: boolean;
  import_unmatched?: boolean;
  row_overrides?: Record<number, DuplicateAction>;
}

export interface BlockAssignmentImportResult {
  success: boolean;
  academic_year: number;

  total_rows: number;
  imported_count: number;
  updated_count: number;
  skipped_count: number;
  failed_count: number;

  failed_rows: number[];
  error_messages: string[];

  started_at: string;
  completed_at: string;
}

// ============================================================================
// Quick Template Types
// ============================================================================

export interface QuickTemplateCreateRequest {
  abbreviation: string;
  name: string;
  activity_type: string;
  leave_eligible: boolean;
}

export interface QuickTemplateCreateResponse {
  id: string;
  abbreviation: string;
  name: string;
  activity_type: string;
}

// ============================================================================
// Export Types
// ============================================================================

export interface BlockAssignmentExportRequest {
  format: ExportFormat;
  academic_year: number;
  block_numbers?: number[];
  rotation_ids?: string[];
  resident_ids?: string[];
  include_pgy_level?: boolean;
  include_leave_status?: boolean;
  group_by?: "block" | "resident" | "rotation";
}

export interface BlockAssignmentExportResult {
  success: boolean;
  format: ExportFormat;
  filename: string;
  row_count: number;
  download_url?: string;
  data?: string; // Base64 for small exports
  generated_at: string;
}

// ============================================================================
// Upload Request Type (for direct content upload)
// ============================================================================

export interface BlockAssignmentUploadRequest {
  content: string;
  academic_year?: number;
  format?: ImportFormat;
  block_number?: number;
  rotation_id?: string;
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
