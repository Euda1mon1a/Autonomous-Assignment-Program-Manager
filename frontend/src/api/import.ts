/**
 * Import Staging API Client
 */
import { api } from "@/lib/api";
import { del, get, post } from "@/lib/api";
import type {
  ConflictResolutionMode,
  ImportApplyResponse,
  ImportBatchListResponse,
  ImportBatchResponse,
  ImportPreviewResponse,
  ImportRollbackResponse,
} from "@/types/import";

const BASE_URL = "/import";

export async function stageImport(
  data: FormData
): Promise<{ batch_id: string }> {
  // Use raw api instance with explicit multipart config.
  // The default axios client sets Content-Type: application/json which prevents
  // FormData auto-detection. Setting to 'multipart/form-data' lets axios
  // correctly append the boundary parameter for the FormData payload.
  const response = await api.post<{ batch_id: string }>(`${BASE_URL}/stage`, data, {
    headers: {
      "Content-Type": "multipart/form-data",
    },
  });
  return response.data;
}

export async function listBatches(
  page = 1,
  page_size = 50,
  status?: string
): Promise<ImportBatchListResponse> {
  const params = new URLSearchParams({
    page: page.toString(),
    page_size: page_size.toString(),
  });
  if (status) params.append("status", status);

  return get<ImportBatchListResponse>(
    `${BASE_URL}/batches?${params.toString()}`
  );
}

export async function getBatch(batchId: string): Promise<ImportBatchResponse> {
  return get<ImportBatchResponse>(`${BASE_URL}/batches/${batchId}`);
}

export async function getBatchPreview(
  batchId: string,
  page = 1,
  page_size = 50
): Promise<ImportPreviewResponse> {
  const params = new URLSearchParams({
    page: page.toString(),
    page_size: page_size.toString(),
  });
  return get<ImportPreviewResponse>(
    `${BASE_URL}/batches/${batchId}/preview?${params.toString()}`
  );
}

export async function applyBatch(
  batchId: string,
  options?: {
    conflict_resolution?: ConflictResolutionMode;
    dry_run?: boolean;
    validate_acgme?: boolean;
  }
): Promise<ImportApplyResponse> {
  return post<ImportApplyResponse>(
    `${BASE_URL}/batches/${batchId}/apply`,
    options
  );
}

export async function rollbackBatch(
  batchId: string,
  reason?: string
): Promise<ImportRollbackResponse> {
  return post<ImportRollbackResponse>(
    `${BASE_URL}/batches/${batchId}/rollback`,
    { reason }
  );
}

export async function deleteBatch(batchId: string): Promise<void> {
  return del(`${BASE_URL}/batches/${batchId}`);
}
