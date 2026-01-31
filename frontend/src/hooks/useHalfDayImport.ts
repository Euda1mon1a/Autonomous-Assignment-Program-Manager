/**
 * Half-Day Import Hooks
 */
import {
  createHalfDayDraft,
  previewHalfDayImport,
  stageHalfDayImport,
} from "@/api/half-day-import";
import type { ApiError } from "@/lib/api";
import type {
  HalfDayImportDraftRequest,
  HalfDayImportDraftResponse,
  HalfDayImportPreviewResponse,
  HalfDayImportStageResponse,
  HalfDayPreviewFilters,
} from "@/types/half-day-import";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

export const halfDayImportKeys = {
  all: ["half-day-import"] as const,
  preview: (
    batchId: string,
    page: number,
    pageSize: number,
    filters: HalfDayPreviewFilters
  ) => ["half-day-import", "preview", batchId, page, pageSize, filters] as const,
};

export function useStageHalfDayImport() {
  const queryClient = useQueryClient();
  return useMutation<HalfDayImportStageResponse, ApiError, {
    file: File;
    blockNumber: number;
    academicYear: number;
    notes?: string;
  }>(
    {
      mutationFn: stageHalfDayImport,
      onSuccess: (data) => {
        if (data.batchId) {
          queryClient.invalidateQueries({ queryKey: halfDayImportKeys.all });
        }
      },
    }
  );
}

export function useHalfDayImportPreview(
  batchId: string | null,
  page: number,
  pageSize: number,
  filters: HalfDayPreviewFilters
) {
  return useQuery<HalfDayImportPreviewResponse, ApiError>({
    queryKey: batchId
      ? halfDayImportKeys.preview(batchId, page, pageSize, filters)
      : halfDayImportKeys.all,
    queryFn: () =>
      previewHalfDayImport(batchId as string, {
        page,
        pageSize,
        diffType: filters.diffType,
        activityCode: filters.activityCode,
        hasErrors: filters.hasErrors,
        personId: filters.personId,
      }),
    enabled: !!batchId,
    placeholderData: (previousData) => previousData,
  });
}

export function useCreateHalfDayDraft() {
  return useMutation<
    HalfDayImportDraftResponse,
    ApiError,
    { batchId: string; payload: HalfDayImportDraftRequest }
  >({
    mutationFn: ({ batchId, payload }) => createHalfDayDraft(batchId, payload),
  });
}
