/**
 * Import Staging API Types
 * Mirrors backend/app/schemas/import_staging.py
 */

export enum ImportBatchStatus {
  STAGED = "staged",
  APPROVED = "approved",
  REJECTED = "rejected",
  APPLIED = "applied",
  ROLLED_BACK = "rolled_back",
  FAILED = "failed",
}

export enum ConflictResolutionMode {
  REPLACE = "replace",
  MERGE = "merge",
  UPSERT = "upsert",
}

export enum StagedAssignmentStatus {
  PENDING = "pending",
  APPROVED = "approved",
  SKIPPED = "skipped",
  APPLIED = "applied",
  FAILED = "failed",
}

export interface ImportBatchCounts {
  total: number;
  pending: number;
  approved: number;
  skipped: number;
  applied: number;
  failed: number;
}

export interface ImportBatchResponse {
  id: string; // UUID
  created_at: string; // ISO Date
  created_by_id?: string;
  filename?: string;
  file_hash?: string;
  file_size_bytes?: number;
  status: ImportBatchStatus;
  conflict_resolution: ConflictResolutionMode;
  target_block?: number;
  target_start_date?: string;
  target_end_date?: string;
  notes?: string;
  row_count?: number;
  error_count: number;
  warning_count: number;
  applied_at?: string;
  applied_by_id?: string;
  rollback_available: boolean;
  rollback_expires_at?: string;
  rolled_back_at?: string;
  rolled_back_by_id?: string;
  counts: ImportBatchCounts;
}

export interface ImportBatchListItem {
  id: string;
  created_at: string;
  filename?: string;
  status: ImportBatchStatus;
  target_block?: number;
  target_start_date?: string;
  target_end_date?: string;
  row_count?: number;
  error_count: number;
  counts: ImportBatchCounts;
}

export interface ImportBatchListResponse {
  items: ImportBatchListItem[];
  total: number;
  page: number;
  page_size: number;
  has_next: boolean;
  has_previous: boolean;
}

export interface StagedAssignmentResponse {
  id: string;
  batch_id: string;
  row_number?: number;
  sheet_name?: string;
  person_name: string;
  assignment_date: string; // YYYY-MM-DD
  slot?: string;
  rotation_name?: string;
  raw_cell_value?: string;

  matched_person_id?: string;
  matched_person_name?: string;
  person_match_confidence?: number;

  matched_rotation_id?: string;
  matched_rotation_name?: string;
  rotation_match_confidence?: number;

  conflict_type?: "none" | "duplicate" | "overwrite";
  existing_assignment_id?: string;

  status: StagedAssignmentStatus;

  validation_errors?: any[]; // Simplified for now
  validation_warnings?: any[]; // Simplified for now

  created_assignment_id?: string;
}

export interface ImportConflictDetail {
  staged_assignment_id: string;
  existing_assignment_id: string;
  person_name: string;
  assignment_date: string;
  slot?: string;
  staged_rotation?: string;
  existing_rotation?: string;
  conflict_type: "duplicate" | "overwrite";
}

export interface ImportPreviewResponse {
  batch_id: string;
  new_count: number;
  update_count: number;
  conflict_count: number;
  skip_count: number;
  acgme_violations: string[];
  staged_assignments: StagedAssignmentResponse[];
  conflicts: ImportConflictDetail[];
  total_staged: number;
  page: number;
  page_size: number;
}

export interface ImportApplyResponse {
  batch_id: string;
  status: ImportBatchStatus;
  applied_count: number;
  skipped_count: number;
  error_count: number;
  started_at: string;
  completed_at?: string;
  errors: any[];
  acgme_warnings: string[];
  rollback_available: boolean;
  rollback_expires_at?: string;
  dry_run: boolean;
}

export interface ImportRollbackResponse {
  batch_id: string;
  status: ImportBatchStatus;
  rolled_back_count: number;
  failed_count: number;
  rolled_back_at: string;
  errors: string[];
}
