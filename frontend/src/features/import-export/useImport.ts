/**
 * React hook for handling bulk imports
 *
 * Supports CSV, JSON, and Excel (.xlsx) file imports.
 * Excel files are parsed via backend API first, with client-side
 * fallback using SheetJS if the backend is unavailable.
 */

import { ApiError, post } from "@/lib/api";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useCallback, useRef, useState } from "react";
import * as XLSX from "xlsx";
import type {
  ImportDataType,
  ImportFileFormat,
  ImportOptions,
  ImportPreviewResult,
  ImportProgress,
  ImportResult,
  ImportValidationError,
} from "./types";
import {
  detectDataType,
  detectFileFormat,
  normalizeColumns,
  parseCSV,
  parseJSON,
  readFileAsArrayBuffer,
  readFileAsText,
} from "./utils";
import {
  findDuplicates,
  findOverlappingAbsences,
  validateImportData,
} from "./validation";

// ============================================================================
// Backend XLSX Parse Response Type
// ============================================================================

interface BackendXlsxResponse {
  success: boolean;
  rows: Record<string, unknown>[];
  columns: string[];
  total_rows: number;
  sheet_name: string;
  warnings: string[];
}

interface BackendXlsxError {
  success: boolean;
  error: string;
  error_code: string;
}

// ============================================================================
// Default Options
// ============================================================================

const DEFAULT_IMPORT_OPTIONS: ImportOptions = {
  skipDuplicates: true,
  updateExisting: false,
  skipInvalidRows: true,
  dateFormat: "YYYY-MM-DD",
  trimWhitespace: true,
};

// ============================================================================
// API Endpoints
// ============================================================================

const IMPORT_ENDPOINTS: Record<ImportDataType, string> = {
  people: "/people/bulk",
  assignments: "/assignments/bulk",
  absences: "/absences/bulk",
  schedules: "/schedule/import",
};

// ============================================================================
// Types
// ============================================================================

interface UseImportOptions {
  dataType?: ImportDataType;
  onProgress?: (progress: ImportProgress) => void;
  onComplete?: (result: ImportResult) => void;
  onError?: (error: Error) => void;
}

interface ImportState {
  file: File | null;
  format: ImportFileFormat;
  dataType: ImportDataType;
  dataTypeSource: "auto" | "manual";
  preview: ImportPreviewResult | null;
  progress: ImportProgress;
  options: ImportOptions;
  /** True if xlsx was parsed client-side instead of via backend */
  xlsxFallbackUsed: boolean;
  /** Warnings from xlsx parsing (backend or client) */
  xlsxWarnings: string[];
}

// ============================================================================
// Hook Implementation
// ============================================================================

export function useImport(hookOptions: UseImportOptions = {}) {
  const queryClient = useQueryClient();
  const abortControllerRef = useRef<AbortController | null>(null);

  const [state, setState] = useState<ImportState>({
    file: null,
    format: "csv",
    dataType: hookOptions.dataType || "schedules",
    dataTypeSource: hookOptions.dataType ? "manual" : "auto",
    preview: null,
    progress: {
      status: "idle",
      currentRow: 0,
      totalRows: 0,
      processedRows: 0,
      successCount: 0,
      errorCount: 0,
      warningCount: 0,
      message: "",
      errors: [],
    },
    options: DEFAULT_IMPORT_OPTIONS,
    xlsxFallbackUsed: false,
    xlsxWarnings: [],
  });

  // ============================================================================
  // Update Progress
  // ============================================================================

  const updateProgress = useCallback(
    (updates: Partial<ImportProgress>) => {
      setState((prev) => {
        const newProgress = { ...prev.progress, ...updates };
        hookOptions.onProgress?.(newProgress);
        return { ...prev, progress: newProgress };
      });
    },
    [hookOptions]
  );

  // ============================================================================
  // Parse XLSX via Backend API
  // ============================================================================

  const parseXlsxViaBackend = useCallback(
    async (
      file: File
    ): Promise<{
      rows: Record<string, unknown>[];
      warnings: string[];
    }> => {
      const formData = new FormData();
      formData.append("file", file);

      // Use fetch directly for FormData upload
      const apiBase =
        process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";
      const response = await fetch(`${apiBase}/imports/parse-xlsx`, {
        method: "POST",
        body: formData,
        credentials: "include",
      });

      if (!response.ok) {
        const errorData = (await response
          .json()
          .catch(() => ({ error: "Unknown error" }))) as BackendXlsxError;
        throw new Error(errorData.error || `Backend error: ${response.status}`);
      }

      const data = (await response.json()) as BackendXlsxResponse;

      if (!data.success) {
        throw new Error(
          (data as unknown as BackendXlsxError).error ||
            "Backend parsing failed"
        );
      }

      return {
        rows: data.rows,
        warnings: data.warnings || [],
      };
    },
    []
  );

  // ============================================================================
  // Parse XLSX Client-Side (Fallback)
  // ============================================================================

  const parseXlsxClientSide = useCallback(
    async (
      file: File
    ): Promise<{
      rows: Record<string, unknown>[];
      warnings: string[];
    }> => {
      const warnings: string[] = [
        "Using client-side Excel parsing (backend unavailable). Some features like color detection may not work.",
      ];

      const arrayBuffer = await readFileAsArrayBuffer(file);
      const workbook = XLSX.read(arrayBuffer, {
        type: "array",
        cellDates: true,
      });

      // Use first sheet
      const sheetName = workbook.SheetNames[0];
      if (!sheetName) {
        throw new Error("No sheets found in Excel file");
      }

      const worksheet = workbook.Sheets[sheetName];
      if (!worksheet) {
        throw new Error(`Failed to read sheet: ${sheetName}`);
      }

      // Convert to JSON with headers from first row
      const rows = XLSX.utils.sheet_to_json<Record<string, unknown>>(
        worksheet,
        {
          header: undefined, // Use first row as headers
          defval: null, // Default value for empty cells
          raw: false, // Convert dates to strings
        }
      );

      if (rows.length === 0) {
        warnings.push("No data rows found in Excel file");
      }

      return { rows, warnings };
    },
    []
  );

  // ============================================================================
  // Parse File (Main Entry Point)
  // ============================================================================

  const parseFile = useCallback(
    async (file: File): Promise<Record<string, unknown>[]> => {
      const format = detectFileFormat(file);

      setState((prev) => ({
        ...prev,
        file,
        format,
        xlsxFallbackUsed: false,
        xlsxWarnings: [],
      }));

      if (format === "csv") {
        const content = await readFileAsText(file);
        return parseCSV(content);
      }

      if (format === "json") {
        const content = await readFileAsText(file);
        return parseJSON(content);
      }

      if (format === "xlsx") {
        // Try backend first, fall back to client-side
        let rows: Record<string, unknown>[];
        let warnings: string[] = [];
        let usedFallback = false;

        try {
          const result = await parseXlsxViaBackend(file);
          rows = result.rows;
          warnings = result.warnings;
        } catch (backendError) {
          // Backend failed, try client-side fallback
          console.warn(
            "Backend xlsx parsing failed, using client-side fallback:",
            backendError instanceof Error ? backendError.message : backendError
          );

          usedFallback = true;
          const result = await parseXlsxClientSide(file);
          rows = result.rows;
          warnings = result.warnings;
        }

        // Update state with fallback info
        setState((prev) => ({
          ...prev,
          xlsxFallbackUsed: usedFallback,
          xlsxWarnings: warnings,
        }));

        return rows;
      }

      throw new Error(`Unsupported file format: ${format}`);
    },
    [parseXlsxViaBackend, parseXlsxClientSide]
  );

  // ============================================================================
  // Preview Import
  // ============================================================================

  const previewImport = useCallback(
    async (file: File): Promise<ImportPreviewResult> => {
      updateProgress({
        status: "parsing",
        message: "Parsing file...",
        currentRow: 0,
        totalRows: 0,
      });

      try {
        // Parse the file
        const rawData = await parseFile(file);

        if (rawData.length === 0) {
          throw new Error("No data found in file");
        }

        // Normalize column names
        const normalizedData = normalizeColumns(rawData);
        const columns = Object.keys(normalizedData[0] || {});

        // Use manual selection if user explicitly chose, otherwise auto-detect
        const detectedType =
          state.dataTypeSource === "manual"
            ? state.dataType
            : detectDataType(columns);

        updateProgress({
          status: "validating",
          message: "Validating data...",
          totalRows: normalizedData.length,
        });

        // Validate the data
        const preview = validateImportData(
          normalizedData,
          detectedType,
          columns
        );
        preview.detectedFormat = detectFileFormat(file);

        // Add duplicate warnings
        const duplicateWarnings = findDuplicates(normalizedData, detectedType);
        if (duplicateWarnings.length > 0) {
          for (const warning of duplicateWarnings) {
            const row = preview.rows.find((r) => r.rowNumber === warning.row);
            if (row) {
              row.warnings.push(warning);
              if (row.status === "valid") {
                row.status = "warning";
                preview.warningRows++;
              }
            }
          }
        }

        // Add overlapping absence warnings
        if (detectedType === "absences") {
          const overlapWarnings = findOverlappingAbsences(normalizedData);
          for (const warning of overlapWarnings) {
            const row = preview.rows.find((r) => r.rowNumber === warning.row);
            if (row) {
              row.warnings.push(warning);
              if (row.status === "valid") {
                row.status = "warning";
                preview.warningRows++;
              }
            }
          }
        }

        setState((prev) => ({
          ...prev,
          dataType: detectedType,
          preview,
        }));

        updateProgress({
          status: "idle",
          message: "Preview ready",
          processedRows: normalizedData.length,
        });

        return preview;
      } catch (error) {
        updateProgress({
          status: "error",
          message:
            error instanceof Error ? error.message : "Failed to parse file",
        });
        throw error;
      }
    },
    [state.dataType, state.dataTypeSource, parseFile, updateProgress]
  );

  // ============================================================================
  // Execute Import Mutation
  // ============================================================================

  const importMutation = useMutation<
    ImportResult,
    ApiError,
    Record<string, unknown>[]
  >({
    mutationFn: async (data) => {
      const endpoint = IMPORT_ENDPOINTS[state.dataType];
      return post<ImportResult>(endpoint, {
        items: data,
        options: state.options,
      });
    },
    onSuccess: (result) => {
      // Invalidate relevant queries
      queryClient.invalidateQueries({ queryKey: ["people"] });
      queryClient.invalidateQueries({ queryKey: ["assignments"] });
      queryClient.invalidateQueries({ queryKey: ["absences"] });
      queryClient.invalidateQueries({ queryKey: ["schedule"] });
      queryClient.invalidateQueries({ queryKey: ["validation"] });

      hookOptions.onComplete?.(result);
    },
    onError: (error) => {
      hookOptions.onError?.(new Error(error.message));
    },
  });

  // ============================================================================
  // Execute Import
  // ============================================================================

  const executeImport = useCallback(async (): Promise<ImportResult> => {
    if (!state.preview) {
      throw new Error("No preview available. Please preview the import first.");
    }

    // Create abort controller for cancellation
    abortControllerRef.current = new AbortController();

    const validRows = state.preview.rows.filter(
      (row) =>
        row.status === "valid" ||
        (row.status === "warning" && state.options.skipInvalidRows)
    );

    if (validRows.length === 0) {
      throw new Error("No valid rows to import");
    }

    updateProgress({
      status: "importing",
      message: "Importing data...",
      totalRows: validRows.length,
      currentRow: 0,
      processedRows: 0,
      successCount: 0,
      errorCount: 0,
      warningCount: state.preview.warningRows,
    });

    const dataToImport = validRows.map((row) => row.data);
    const batchSize = 100;
    const totalBatches = Math.ceil(dataToImport.length / batchSize);

    let successCount = 0;
    let errorCount = 0;
    const errors: ImportValidationError[] = [];
    const importedIds: string[] = [];

    try {
      for (let batchIndex = 0; batchIndex < totalBatches; batchIndex++) {
        // Check for cancellation
        if (abortControllerRef.current?.signal.aborted) {
          throw new Error("Import cancelled");
        }

        const start = batchIndex * batchSize;
        const end = Math.min(start + batchSize, dataToImport.length);
        const batch = dataToImport.slice(start, end);

        try {
          const result = await importMutation.mutateAsync(batch);
          successCount += result.successCount;
          errorCount += result.errorCount;
          errors.push(...result.errors);
          importedIds.push(...result.importedIds);
        } catch (batchError) {
          // Handle batch error
          errorCount += batch.length;
          errors.push({
            row: start + 2,
            column: "batch",
            value: null,
            message:
              batchError instanceof Error
                ? batchError.message
                : "Batch import failed",
            severity: "error",
          });
        }

        updateProgress({
          currentRow: end,
          processedRows: end,
          successCount,
          errorCount,
          errors,
          message: `Imported ${end} of ${dataToImport.length} rows...`,
        });
      }

      const result: ImportResult = {
        success: errorCount === 0,
        totalProcessed: dataToImport.length,
        successCount,
        errorCount,
        skippedCount: state.preview.skippedRows + state.preview.errorRows,
        errors,
        importedIds,
      };

      updateProgress({
        status: "complete",
        message: `Import complete: ${successCount} succeeded, ${errorCount} failed`,
        errors,
      });

      return result;
    } catch (error) {
      updateProgress({
        status: "error",
        message: error instanceof Error ? error.message : "Import failed",
      });
      throw error;
    }
  }, [
    state.preview,
    state.options,
    // state.dataType intentionally omitted to prevent re-creation on type change if not needed
    updateProgress,
    importMutation,
  ]);

  // ============================================================================
  // Cancel Import
  // ============================================================================

  const cancelImport = useCallback(() => {
    abortControllerRef.current?.abort();
    updateProgress({
      status: "idle",
      message: "Import cancelled",
    });
  }, [updateProgress]);

  // ============================================================================
  // Reset State
  // ============================================================================

  const reset = useCallback(() => {
    abortControllerRef.current?.abort();
    setState({
      file: null,
      format: "csv",
      dataType: hookOptions.dataType || "schedules",
      dataTypeSource: hookOptions.dataType ? "manual" : "auto",
      preview: null,
      progress: {
        status: "idle",
        currentRow: 0,
        totalRows: 0,
        processedRows: 0,
        successCount: 0,
        errorCount: 0,
        warningCount: 0,
        message: "",
        errors: [],
      },
      options: DEFAULT_IMPORT_OPTIONS,
      xlsxFallbackUsed: false,
      xlsxWarnings: [],
    });
  }, [hookOptions.dataType]);

  // ============================================================================
  // Update Options
  // ============================================================================

  const updateOptions = useCallback((options: Partial<ImportOptions>) => {
    setState((prev) => ({
      ...prev,
      options: { ...prev.options, ...options },
    }));
  }, []);

  // ============================================================================
  // Set Data Type
  // ============================================================================

  const setDataType = useCallback((dataType: ImportDataType) => {
    setState((prev) => ({ ...prev, dataType, dataTypeSource: "manual" }));
  }, []);

  // ============================================================================
  // Return Hook API
  // ============================================================================

  return {
    // State
    file: state.file,
    format: state.format,
    dataType: state.dataType,
    preview: state.preview,
    progress: state.progress,
    options: state.options,
    isLoading:
      importMutation.isPending ||
      ["parsing", "validating", "importing"].includes(state.progress.status),
    isError: state.progress.status === "error",
    /** True if xlsx was parsed client-side (backend was unavailable) */
    xlsxFallbackUsed: state.xlsxFallbackUsed,
    /** Warnings from xlsx parsing */
    xlsxWarnings: state.xlsxWarnings,

    // Actions
    previewImport,
    executeImport,
    cancelImport,
    reset,
    updateOptions,
    setDataType,
  };
}

export type UseImportReturn = ReturnType<typeof useImport>;
