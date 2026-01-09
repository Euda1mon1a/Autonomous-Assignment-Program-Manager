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
  createdAt: string; // ISO Date
  createdById?: string;
  filename?: string;
  fileHash?: string;
  fileSizeBytes?: number;
  status: ImportBatchStatus;
  conflictResolution: ConflictResolutionMode;
  targetBlock?: number;
  targetStartDate?: string;
  targetEndDate?: string;
  notes?: string;
  rowCount?: number;
  errorCount: number;
  warningCount: number;
  appliedAt?: string;
  appliedById?: string;
  rollbackAvailable: boolean;
  rollbackExpiresAt?: string;
  rolledBackAt?: string;
  rolledBackById?: string;
  counts: ImportBatchCounts;
}

export interface ImportBatchListItem {
  id: string;
  createdAt: string;
  filename?: string;
  status: ImportBatchStatus;
  targetBlock?: number;
  targetStartDate?: string;
  targetEndDate?: string;
  rowCount?: number;
  errorCount: number;
  counts: ImportBatchCounts;
}

export interface ImportBatchListResponse {
  items: ImportBatchListItem[];
  total: number;
  page: number;
  pageSize: number;
  hasNext: boolean;
  hasPrevious: boolean;
}

export interface StagedAssignmentResponse {
  id: string;
  batchId: string;
  rowNumber?: number;
  sheetName?: string;
  personName: string;
  assignmentDate: string; // YYYY-MM-DD
  slot?: string;
  rotationName?: string;
  rawCellValue?: string;

  matchedPersonId?: string;
  matchedPersonName?: string;
  personMatchConfidence?: number;

  matchedRotationId?: string;
  matchedRotationName?: string;
  rotationMatchConfidence?: number;

  conflictType?: "none" | "duplicate" | "overwrite";
  existingAssignmentId?: string;

  status: StagedAssignmentStatus;

  validationErrors?: any[]; // Simplified for now
  validationWarnings?: any[]; // Simplified for now

  createdAssignmentId?: string;
}

export interface ImportConflictDetail {
  stagedAssignmentId: string;
  existingAssignmentId: string;
  personName: string;
  assignmentDate: string;
  slot?: string;
  stagedRotation?: string;
  existingRotation?: string;
  conflictType: "duplicate" | "overwrite";
}

export interface ImportPreviewResponse {
  batchId: string;
  newCount: number;
  updateCount: number;
  conflictCount: number;
  skipCount: number;
  acgmeViolations: string[];
  stagedAssignments: StagedAssignmentResponse[];
  conflicts: ImportConflictDetail[];
  totalStaged: number;
  page: number;
  pageSize: number;
}

export interface ImportApplyResponse {
  batchId: string;
  status: ImportBatchStatus;
  appliedCount: number;
  skippedCount: number;
  errorCount: number;
  startedAt: string;
  completedAt?: string;
  errors: any[];
  acgmeWarnings: string[];
  rollbackAvailable: boolean;
  rollbackExpiresAt?: string;
  dryRun: boolean;
}

export interface ImportRollbackResponse {
  batchId: string;
  status: ImportBatchStatus;
  rolledBackCount: number;
  failedCount: number;
  rolledBackAt: string;
  errors: string[];
}
