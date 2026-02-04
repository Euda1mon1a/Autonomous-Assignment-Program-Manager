/**
 * Schedule Drafts API Client
 */
import { del, get, post } from "@/lib/api";
import type {
  DraftPreviewResponse,
  PublishRequest,
  PublishResponse,
  RollbackResponse,
  ScheduleDraftStatus,
  ScheduleDraftListResponse,
  ScheduleDraftResponse,
} from "@/types/schedule-draft";

const BASE_URL = "/schedules/drafts";

export async function listScheduleDrafts(params?: {
  page?: number;
  pageSize?: number;
  status?: ScheduleDraftStatus;
}): Promise<ScheduleDraftListResponse> {
  const searchParams = new URLSearchParams();
  if (params?.page) searchParams.append("page", params.page.toString());
  if (params?.pageSize) searchParams.append("page_size", params.pageSize.toString());
  if (params?.status) searchParams.append("status", params.status);

  const suffix = searchParams.toString();
  return get<ScheduleDraftListResponse>(
    `${BASE_URL}${suffix ? `?${suffix}` : ""}`
  );
}

export async function getScheduleDraft(
  draftId: string
): Promise<ScheduleDraftResponse> {
  return get<ScheduleDraftResponse>(`${BASE_URL}/${draftId}`);
}

export async function previewScheduleDraft(
  draftId: string
): Promise<DraftPreviewResponse> {
  return get<DraftPreviewResponse>(`${BASE_URL}/${draftId}/preview`);
}

export async function publishScheduleDraft(
  draftId: string,
  payload?: PublishRequest
): Promise<PublishResponse> {
  return post<PublishResponse>(`${BASE_URL}/${draftId}/publish`, payload);
}

export async function rollbackScheduleDraft(
  draftId: string,
  payload?: { reason?: string }
): Promise<RollbackResponse> {
  return post<RollbackResponse>(`${BASE_URL}/${draftId}/rollback`, payload);
}

export async function discardScheduleDraft(draftId: string): Promise<void> {
  return del<void>(`${BASE_URL}/${draftId}`);
}

export interface DraftFlagAcknowledgeResponse {
  success: boolean;
  flagId: string;
  message: string;
}

export interface DraftFlagBulkAcknowledgeResponse {
  success: boolean;
  acknowledgedCount: number;
  failedCount: number;
  failedIds: string[];
}

export async function acknowledgeDraftFlag(
  draftId: string,
  flagId: string,
  resolutionNote?: string
): Promise<DraftFlagAcknowledgeResponse> {
  return post<DraftFlagAcknowledgeResponse>(
    `${BASE_URL}/${draftId}/flags/${flagId}/acknowledge`,
    resolutionNote ? { resolutionNote } : undefined
  );
}

export async function bulkAcknowledgeDraftFlags(
  draftId: string,
  flagIds: string[],
  resolutionNote?: string
): Promise<DraftFlagBulkAcknowledgeResponse> {
  return post<DraftFlagBulkAcknowledgeResponse>(
    `${BASE_URL}/${draftId}/flags/acknowledge`,
    {
      flagIds,
      resolutionNote,
    }
  );
}
