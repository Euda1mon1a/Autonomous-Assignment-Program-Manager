/**
 * Half-Day Import API Client (Block Template2)
 */
import { api, get, post } from "@/lib/api";
import type {
  HalfDayDiffType,
  HalfDayImportDraftRequest,
  HalfDayImportDraftResponse,
  HalfDayImportPreviewResponse,
  HalfDayImportStageResponse,
  HalfDayPreviewFilters,
} from "@/types/half-day-import";

const BASE_URL = "/import/half-day";

export async function stageHalfDayImport(params: {
  file: File;
  blockNumber: number;
  academicYear: number;
  notes?: string;
}): Promise<HalfDayImportStageResponse> {
  const formData = new FormData();
  formData.append("file", params.file);
  formData.append("block_number", params.blockNumber.toString());
  formData.append("academic_year", params.academicYear.toString());
  if (params.notes) {
    formData.append("notes", params.notes);
  }

  const response = await api.post<HalfDayImportStageResponse>(
    `${BASE_URL}/stage`,
    formData,
    {
      headers: {
        "Content-Type": "multipart/form-data",
      },
    }
  );
  return response.data;
}

export async function previewHalfDayImport(
  batchId: string,
  params: {
    page?: number;
    pageSize?: number;
    diffType?: HalfDayDiffType;
    activityCode?: string;
    hasErrors?: boolean;
    personId?: string;
  }
): Promise<HalfDayImportPreviewResponse> {
  const searchParams = new URLSearchParams();
  if (params.page) searchParams.append("page", params.page.toString());
  if (params.pageSize) {
    searchParams.append("page_size", params.pageSize.toString());
  }
  if (params.diffType) searchParams.append("diff_type", params.diffType);
  if (params.activityCode) {
    searchParams.append("activity_code", params.activityCode);
  }
  if (params.hasErrors !== undefined) {
    searchParams.append("has_errors", String(params.hasErrors));
  }
  if (params.personId) searchParams.append("person_id", params.personId);

  const query = searchParams.toString();
  const suffix = query ? `?${query}` : "";
  return get<HalfDayImportPreviewResponse>(
    `${BASE_URL}/batches/${batchId}/preview${suffix}`
  );
}

export async function createHalfDayDraft(
  batchId: string,
  payload: HalfDayImportDraftRequest
): Promise<HalfDayImportDraftResponse> {
  return post<HalfDayImportDraftResponse>(
    `${BASE_URL}/batches/${batchId}/draft`,
    payload
  );
}

export type { HalfDayDiffType, HalfDayPreviewFilters };
