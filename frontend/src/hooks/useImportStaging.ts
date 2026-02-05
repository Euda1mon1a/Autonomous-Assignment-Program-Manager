/**
 * Import Staging Hooks
 *
 * React Query hooks for the Excel import staging workflow:
 * - Stage import (upload file, create batch)
 * - Preview staged vs existing assignments
 * - Apply or rollback batches
 */

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { get, post, del, ApiError } from '@/lib/api';
import type {
  ImportBatchResponse,
  ImportBatchListResponse,
  ImportPreviewResponse,
  ImportApplyResponse,
  ImportRollbackResponse,
  ConflictResolutionMode,
} from '@/types/import';

// ============================================================================
// Query Keys
// ============================================================================

export const importStagingKeys = {
  all: ['import-staging'] as const,
  batches: () => [...importStagingKeys.all, 'batches'] as const,
  batchList: (params?: { page?: number; pageSize?: number; status?: string }) =>
    [...importStagingKeys.batches(), params] as const,
  batch: (batchId: string) => [...importStagingKeys.batches(), batchId] as const,
  preview: (batchId: string) => [...importStagingKeys.all, 'preview', batchId] as const,
};

// ============================================================================
// Query Hooks
// ============================================================================

/**
 * List import batches with pagination and filtering.
 */
export function useImportBatches(
  page = 1,
  pageSize = 20,
  status?: string
) {
  return useQuery<ImportBatchListResponse, ApiError>({
    queryKey: importStagingKeys.batchList({ page, pageSize, status }),
    queryFn: () => {
      const params = new URLSearchParams();
      params.set('page', String(page));
      params.set('page_size', String(pageSize));
      if (status) params.set('status', status);
      return get<ImportBatchListResponse>(`/import/batches?${params.toString()}`);
    },
  });
}

/**
 * Get a single import batch by ID.
 */
export function useImportBatch(batchId: string | null) {
  return useQuery<ImportBatchResponse, ApiError>({
    queryKey: batchId ? importStagingKeys.batch(batchId) : importStagingKeys.all,
    queryFn: () => get<ImportBatchResponse>(`/import/batches/${batchId}`),
    enabled: !!batchId,
  });
}

/**
 * Preview staged assignments vs existing for a batch.
 */
export function useImportPreview(batchId: string | null, page = 1, pageSize = 50) {
  return useQuery<ImportPreviewResponse, ApiError>({
    queryKey: batchId ? importStagingKeys.preview(batchId) : importStagingKeys.all,
    queryFn: () => {
      const params = new URLSearchParams();
      params.set('page', String(page));
      params.set('page_size', String(pageSize));
      return get<ImportPreviewResponse>(
        `/import/batches/${batchId}/preview?${params.toString()}`
      );
    },
    enabled: !!batchId,
  });
}

// ============================================================================
// Mutation Hooks
// ============================================================================

export interface StageImportParams {
  file: File;
  targetBlock?: number;
  targetStartDate?: string;
  targetEndDate?: string;
  conflictResolution?: ConflictResolutionMode;
  notes?: string;
  sheetName?: string;
}

/**
 * Stage an Excel file for import.
 */
export function useStageImport() {
  const queryClient = useQueryClient();

  return useMutation<{ batchId: string }, ApiError, StageImportParams>({
    mutationFn: async (params) => {
      const formData = new FormData();
      formData.append('file', params.file);

      if (params.targetBlock) {
        formData.append('target_block', String(params.targetBlock));
      }
      if (params.targetStartDate) {
        formData.append('target_start_date', params.targetStartDate);
      }
      if (params.targetEndDate) {
        formData.append('target_end_date', params.targetEndDate);
      }
      if (params.conflictResolution) {
        formData.append('conflict_resolution', params.conflictResolution);
      }
      if (params.notes) {
        formData.append('notes', params.notes);
      }
      if (params.sheetName) {
        formData.append('sheet_name', params.sheetName);
      }

      // Use fetch directly for FormData (axios needs special handling)
      const response = await fetch('/api/v1/import/stage', {
        method: 'POST',
        body: formData,
        credentials: 'include',
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail?.error || 'Failed to stage import');
      }

      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: importStagingKeys.batches() });
    },
  });
}

export interface ApplyImportParams {
  batchId: string;
  validateAcgme?: boolean;
  dryRun?: boolean;
}

/**
 * Apply a staged import batch.
 */
export function useApplyImport() {
  const queryClient = useQueryClient();

  return useMutation<ImportApplyResponse, ApiError, ApplyImportParams>({
    mutationFn: async ({ batchId, validateAcgme = true, dryRun = false }) => {
      return post<ImportApplyResponse>(`/import/batches/${batchId}/apply`, {
        validate_acgme: validateAcgme,
        dry_run: dryRun,
      });
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({
        queryKey: importStagingKeys.batch(data.batchId),
      });
      queryClient.invalidateQueries({ queryKey: importStagingKeys.batches() });
      queryClient.invalidateQueries({
        queryKey: importStagingKeys.preview(data.batchId),
      });
    },
  });
}

/**
 * Rollback an applied import batch.
 */
export function useRollbackImport() {
  const queryClient = useQueryClient();

  return useMutation<
    ImportRollbackResponse,
    ApiError,
    { batchId: string; reason?: string }
  >({
    mutationFn: async ({ batchId, reason }) => {
      return post<ImportRollbackResponse>(`/import/batches/${batchId}/rollback`, {
        reason,
      });
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({
        queryKey: importStagingKeys.batch(data.batchId),
      });
      queryClient.invalidateQueries({ queryKey: importStagingKeys.batches() });
    },
  });
}

/**
 * Delete/reject a staged import batch.
 */
export function useDeleteImportBatch() {
  const queryClient = useQueryClient();

  return useMutation<void, ApiError, string>({
    mutationFn: async (batchId) => {
      return del(`/import/batches/${batchId}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: importStagingKeys.batches() });
    },
  });
}
