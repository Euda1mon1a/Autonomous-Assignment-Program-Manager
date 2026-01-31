/**
 * Half-Day Import API Types
 * Mirrors backend/app/schemas/half_day_import.py
 */

export type HalfDayDiffType = "added" | "removed" | "modified";

export interface HalfDayDiffEntry {
  stagedId?: string | null;
  personId?: string | null;
  personName: string;
  assignmentDate: string;
  timeOfDay: string;
  diffType: HalfDayDiffType;
  excelValue?: string | null;
  currentValue?: string | null;
  warnings: string[];
  errors: string[];
}

export interface HalfDayDiffMetrics {
  totalSlots: number;
  changedSlots: number;
  added: number;
  removed: number;
  modified: number;
  percentChanged: number;
  manualHalfDays: number;
  manualHours: number;
  byActivity: Record<string, number>;
}

export interface HalfDayImportStageResponse {
  success: boolean;
  batchId?: string | null;
  createdAt?: string | null;
  message: string;
  warnings: string[];
  diffMetrics?: HalfDayDiffMetrics | null;
}

export interface HalfDayImportPreviewResponse {
  batchId: string;
  metrics: HalfDayDiffMetrics;
  diffs: HalfDayDiffEntry[];
  totalDiffs: number;
  page: number;
  pageSize: number;
}

export interface HalfDayImportDraftRequest {
  stagedIds?: string[] | null;
  notes?: string | null;
}

export interface HalfDayImportDraftResponse {
  success: boolean;
  batchId: string;
  draftId?: string | null;
  message: string;
  totalSelected: number;
  added: number;
  modified: number;
  removed: number;
  skipped: number;
  failed: number;
  failedIds: string[];
}

export interface HalfDayDraftErrorDetail {
  message: string;
  errorCode?: string;
  failedIds?: string[];
}

export interface HalfDayPreviewFilters {
  diffType?: HalfDayDiffType;
  activityCode?: string;
  hasErrors?: boolean;
  personId?: string;
}
