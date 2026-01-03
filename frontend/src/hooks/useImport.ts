/**
 * Import Staging Hooks
 */
import {
  applyBatch,
  deleteBatch,
  getBatch,
  getBatchPreview,
  listBatches,
  rollbackBatch,
  stageImport,
} from "@/api/import";
import { ApiError } from "@/lib/api";
import type {
  ImportBatchListResponse,
  ImportBatchResponse,
  ImportPreviewResponse,
} from "@/types/import";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

export const importQueryKeys = {
  all: ["import"] as const,
  lists: () => ["import", "list"] as const,
  list: (page: number, status?: string) =>
    ["import", "list", page, status] as const,
  details: () => ["import", "detail"] as const,
  detail: (id: string) => ["import", "detail", id] as const,
  previews: () => ["import", "preview"] as const,
  preview: (id: string, page: number) =>
    ["import", "preview", id, page] as const,
};

export function useImportBatches(page = 1, status?: string) {
  return useQuery<ImportBatchListResponse, ApiError>({
    queryKey: importQueryKeys.list(page, status),
    queryFn: () => listBatches(page, 50, status),
    placeholderData: (previousData) => previousData,
  });
}

export function useImportBatch(batchId: string) {
  return useQuery<ImportBatchResponse, ApiError>({
    queryKey: importQueryKeys.detail(batchId),
    queryFn: () => getBatch(batchId),
    enabled: !!batchId,
  });
}

export function useImportPreview(batchId: string, page = 1) {
  return useQuery<ImportPreviewResponse, ApiError>({
    queryKey: importQueryKeys.preview(batchId, page),
    queryFn: () => getBatchPreview(batchId, page),
    enabled: !!batchId,
    placeholderData: (previousData) => previousData,
  });
}

export function useStageImport() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: stageImport,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: importQueryKeys.lists() });
    },
  });
}

export function useApplyBatch() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, options }: { id: string; options?: Record<string, unknown> }) =>
      applyBatch(id, options),
    onSuccess: (data, variables) => {
      queryClient.invalidateQueries({
        queryKey: importQueryKeys.detail(variables.id),
      });
      queryClient.invalidateQueries({ queryKey: importQueryKeys.lists() });
    },
  });
}

export function useRollbackBatch() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, reason }: { id: string; reason?: string }) =>
      rollbackBatch(id, reason),
    onSuccess: (data, variables) => {
      queryClient.invalidateQueries({
        queryKey: importQueryKeys.detail(variables.id),
      });
      queryClient.invalidateQueries({ queryKey: importQueryKeys.lists() });
    },
  });
}

export function useDeleteBatch() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: deleteBatch,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: importQueryKeys.lists() });
    },
  });
}
