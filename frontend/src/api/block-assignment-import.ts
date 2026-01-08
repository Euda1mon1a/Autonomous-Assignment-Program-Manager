/**
 * Block Assignment Import/Export API Client
 */
import { api } from "@/lib/api";
import { post } from "@/lib/api";
import type {
  BlockAssignmentPreviewResponse,
  BlockAssignmentImportRequest,
  BlockAssignmentImportResult,
  QuickTemplateCreateRequest,
  QuickTemplateCreateResponse,
  BlockAssignmentExportRequest,
  BlockAssignmentExportResult,
} from "@/types/block-assignment-import";

const BASE_URL = "/admin/block-assignments";

/**
 * Preview block assignment import from CSV content.
 * Uses FormData for multipart upload support.
 */
export async function previewBlockAssignmentImport(
  csvContent: string,
  academicYear?: number
): Promise<BlockAssignmentPreviewResponse> {
  const formData = new FormData();
  formData.append("csv_content", csvContent);
  if (academicYear) {
    formData.append("academic_year", academicYear.toString());
  }

  const response = await api.post<BlockAssignmentPreviewResponse>(
    `${BASE_URL}/preview`,
    formData,
    {
      headers: {
        "Content-Type": "multipart/form-data",
      },
    }
  );
  return response.data;
}

/**
 * Preview block assignment import from file upload.
 */
export async function previewBlockAssignmentImportFile(
  file: File,
  academicYear?: number
): Promise<BlockAssignmentPreviewResponse> {
  const formData = new FormData();
  formData.append("file", file);
  if (academicYear) {
    formData.append("academic_year", academicYear.toString());
  }

  const response = await api.post<BlockAssignmentPreviewResponse>(
    `${BASE_URL}/preview`,
    formData,
    {
      headers: {
        "Content-Type": "multipart/form-data",
      },
    }
  );
  return response.data;
}

/**
 * Execute block assignment import based on preview.
 */
export async function executeBlockAssignmentImport(
  request: BlockAssignmentImportRequest
): Promise<BlockAssignmentImportResult> {
  return post<BlockAssignmentImportResult>(`${BASE_URL}/import`, request);
}

/**
 * Quick-create a rotation template during import.
 */
export async function quickCreateRotationTemplate(
  request: QuickTemplateCreateRequest
): Promise<QuickTemplateCreateResponse> {
  return post<QuickTemplateCreateResponse>(
    `${BASE_URL}/templates/quick-create`,
    request
  );
}

/**
 * Download the CSV import template.
 */
export async function downloadImportTemplate(): Promise<Blob> {
  const response = await api.get(`${BASE_URL}/template`, {
    responseType: "blob",
  });
  return response.data;
}

/**
 * Export block assignments.
 */
export async function exportBlockAssignments(
  request: BlockAssignmentExportRequest
): Promise<BlockAssignmentExportResult | Blob> {
  // For downloads, request blob response
  if (request.format === "xlsx" || request.format === "csv") {
    const response = await api.post(`${BASE_URL}/export`, request, {
      responseType: "blob",
    });
    return response.data;
  }
  return post<BlockAssignmentExportResult>(`${BASE_URL}/export`, request);
}

/**
 * Helper to trigger file download from blob.
 */
export function downloadBlob(blob: Blob, filename: string): void {
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  window.URL.revokeObjectURL(url);
}
