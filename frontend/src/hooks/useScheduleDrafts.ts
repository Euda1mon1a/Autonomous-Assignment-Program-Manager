/**
 * Schedule Draft Hooks
 */
import {
  acknowledgeDraftFlag,
  approveBreakGlass,
  bulkAcknowledgeDraftFlags,
  discardScheduleDraft,
  getScheduleDraft,
  listScheduleDrafts,
  previewScheduleDraft,
  publishScheduleDraft,
  rollbackScheduleDraft,
} from "@/api/schedule-drafts";
import type { ApiError } from "@/lib/api";
import type {
  BreakGlassApprovalResponse,
  DraftPreviewResponse,
  PublishRequest,
  PublishResponse,
  RollbackResponse,
  ScheduleDraftStatus,
  ScheduleDraftListResponse,
  ScheduleDraftResponse,
} from "@/types/schedule-draft";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

export const scheduleDraftKeys = {
  all: ["schedule-drafts"] as const,
  lists: () => [...scheduleDraftKeys.all, "list"] as const,
  list: (params?: { page?: number; pageSize?: number; status?: ScheduleDraftStatus }) =>
    [...scheduleDraftKeys.lists(), params] as const,
  details: () => [...scheduleDraftKeys.all, "detail"] as const,
  detail: (draftId: string) => [...scheduleDraftKeys.details(), draftId] as const,
  preview: (draftId: string) =>
    [...scheduleDraftKeys.all, "preview", draftId] as const,
};

export function useScheduleDrafts(
  page = 1,
  status?: ScheduleDraftStatus,
  pageSize = 20
) {
  return useQuery<ScheduleDraftListResponse, ApiError>({
    queryKey: scheduleDraftKeys.list({ page, pageSize, status }),
    queryFn: () => listScheduleDrafts({ page, pageSize, status }),
  });
}

export function useScheduleDraft(draftId: string | null) {
  return useQuery<ScheduleDraftResponse, ApiError>({
    queryKey: draftId
      ? scheduleDraftKeys.detail(draftId)
      : scheduleDraftKeys.all,
    queryFn: () => getScheduleDraft(draftId as string),
    enabled: !!draftId,
  });
}

export function useScheduleDraftPreview(draftId: string | null) {
  return useQuery<DraftPreviewResponse, ApiError>({
    queryKey: draftId
      ? scheduleDraftKeys.preview(draftId)
      : scheduleDraftKeys.all,
    queryFn: () => previewScheduleDraft(draftId as string),
    enabled: !!draftId,
  });
}

export function useApproveBreakGlass() {
  const queryClient = useQueryClient();
  return useMutation<
    BreakGlassApprovalResponse,
    ApiError,
    { draftId: string; reason: string }
  >({
    mutationFn: ({ draftId, reason }) =>
      approveBreakGlass(draftId, { reason }),
    onSuccess: (data) => {
      queryClient.invalidateQueries({
        queryKey: scheduleDraftKeys.detail(data.draftId),
      });
      queryClient.invalidateQueries({
        queryKey: scheduleDraftKeys.preview(data.draftId),
      });
    },
  });
}

export function usePublishScheduleDraft() {
  const queryClient = useQueryClient();
  return useMutation<
    PublishResponse,
    ApiError,
    { draftId: string; payload?: PublishRequest }
  >({
    mutationFn: ({ draftId, payload }) => publishScheduleDraft(draftId, payload),
    onSuccess: (data) => {
      queryClient.invalidateQueries({
        queryKey: scheduleDraftKeys.detail(data.draftId),
      });
      queryClient.invalidateQueries({ queryKey: scheduleDraftKeys.lists() });
      queryClient.invalidateQueries({
        queryKey: scheduleDraftKeys.preview(data.draftId),
      });
    },
  });
}

export function useRollbackScheduleDraft() {
  const queryClient = useQueryClient();
  return useMutation<
    RollbackResponse,
    ApiError,
    { draftId: string; reason?: string }
  >({
    mutationFn: ({ draftId, reason }) =>
      rollbackScheduleDraft(draftId, reason ? { reason } : undefined),
    onSuccess: (data) => {
      queryClient.invalidateQueries({
        queryKey: scheduleDraftKeys.detail(data.draftId),
      });
      queryClient.invalidateQueries({ queryKey: scheduleDraftKeys.lists() });
      queryClient.invalidateQueries({
        queryKey: scheduleDraftKeys.preview(data.draftId),
      });
    },
  });
}

export function useDiscardScheduleDraft() {
  const queryClient = useQueryClient();
  return useMutation<void, ApiError, string>({
    mutationFn: (draftId) => discardScheduleDraft(draftId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: scheduleDraftKeys.lists() });
    },
  });
}

export function useAcknowledgeFlag() {
  const queryClient = useQueryClient();
  return useMutation<
    Awaited<ReturnType<typeof acknowledgeDraftFlag>>,
    ApiError,
    { draftId: string; flagId: string; resolutionNote?: string }
  >({
    mutationFn: ({ draftId, flagId, resolutionNote }) =>
      acknowledgeDraftFlag(draftId, flagId, resolutionNote),
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({
        queryKey: scheduleDraftKeys.preview(variables.draftId),
      });
      queryClient.invalidateQueries({
        queryKey: scheduleDraftKeys.detail(variables.draftId),
      });
    },
  });
}

export function useBulkAcknowledgeFlags() {
  const queryClient = useQueryClient();
  return useMutation<
    Awaited<ReturnType<typeof bulkAcknowledgeDraftFlags>>,
    ApiError,
    { draftId: string; flagIds: string[]; resolutionNote?: string }
  >({
    mutationFn: ({ draftId, flagIds, resolutionNote }) =>
      bulkAcknowledgeDraftFlags(draftId, flagIds, resolutionNote),
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({
        queryKey: scheduleDraftKeys.preview(variables.draftId),
      });
      queryClient.invalidateQueries({
        queryKey: scheduleDraftKeys.detail(variables.draftId),
      });
    },
  });
}

// Compatibility aliases for UI components
export const usePublishDraft = usePublishScheduleDraft;
export const useRollbackDraft = useRollbackScheduleDraft;
export const useDiscardDraft = useDiscardScheduleDraft;
