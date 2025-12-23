/**
 * React hook for handling bulk imports
 */

import { useState, useCallback, useRef } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { post, ApiError } from '@/lib/api';
import type {
  ImportDataType,
  ImportFileFormat,
  ImportOptions,
  ImportProgress,
  ImportPreviewResult,
  ImportResult,
  ImportValidationError,
} from './types';
import {
  detectFileFormat,
  detectDataType,
  parseCSV,
  parseJSON,
  readFileAsText,
  normalizeColumns,
} from './utils';
import {
  validateImportData,
  findDuplicates,
  findOverlappingAbsences,
} from './validation';

// ============================================================================
// Default Options
// ============================================================================

const DEFAULT_IMPORT_OPTIONS: ImportOptions = {
  skipDuplicates: true,
  updateExisting: false,
  skipInvalidRows: true,
  dateFormat: 'YYYY-MM-DD',
  trimWhitespace: true,
};

// ============================================================================
// API Endpoints
// ============================================================================

const IMPORT_ENDPOINTS: Record<ImportDataType, string> = {
  people: '/people/bulk',
  assignments: '/assignments/bulk',
  absences: '/absences/bulk',
  schedules: '/schedule/import',
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
  dataTypeSource: 'auto' | 'manual';
  preview: ImportPreviewResult | null;
  progress: ImportProgress;
  options: ImportOptions;
}

// ============================================================================
// Hook Implementation
// ============================================================================

export function useImport(hookOptions: UseImportOptions = {}) {
  const queryClient = useQueryClient();
  const abortControllerRef = useRef<AbortController | null>(null);

  const [state, setState] = useState<ImportState>({
    file: null,
    format: 'csv',
    dataType: hookOptions.dataType || 'schedules',
    dataTypeSource: hookOptions.dataType ? 'manual' : 'auto',
    preview: null,
    progress: {
      status: 'idle',
      currentRow: 0,
      totalRows: 0,
      processedRows: 0,
      successCount: 0,
      errorCount: 0,
      warningCount: 0,
      message: '',
      errors: [],
    },
    options: DEFAULT_IMPORT_OPTIONS,
  });

  // ============================================================================
  // Update Progress
  // ============================================================================

  const updateProgress = useCallback((updates: Partial<ImportProgress>) => {
    setState(prev => {
      const newProgress = { ...prev.progress, ...updates };
      hookOptions.onProgress?.(newProgress);
      return { ...prev, progress: newProgress };
    });
  }, [hookOptions]);

  // ============================================================================
  // Parse File
  // ============================================================================

  const parseFile = useCallback(async (file: File): Promise<Record<string, unknown>[]> => {
    const format = detectFileFormat(file);
    const content = await readFileAsText(file);

    setState(prev => ({ ...prev, file, format }));

    if (format === 'csv') {
      return parseCSV(content);
    }

    if (format === 'json') {
      return parseJSON(content);
    }

    if (format === 'xlsx') {
      // For Excel files, we need to use a library like xlsx
      // For now, we'll show a message to convert to CSV
      throw new Error('Excel files (.xlsx) are not yet fully supported. Please convert to CSV format.');
    }

    throw new Error(`Unsupported file format: ${format}`);
  }, []);

  // ============================================================================
  // Preview Import
  // ============================================================================

  const previewImport = useCallback(async (file: File): Promise<ImportPreviewResult> => {
    updateProgress({
      status: 'parsing',
      message: 'Parsing file...',
      currentRow: 0,
      totalRows: 0,
    });

    try {
      // Parse the file
      const rawData = await parseFile(file);

      if (rawData.length === 0) {
        throw new Error('No data found in file');
      }

      // Normalize column names
      const normalizedData = normalizeColumns(rawData);
      const columns = Object.keys(normalizedData[0] || {});

      // Use manual selection if user explicitly chose, otherwise auto-detect
      const detectedType =
        state.dataTypeSource === 'manual' ? state.dataType : detectDataType(columns);

      updateProgress({
        status: 'validating',
        message: 'Validating data...',
        totalRows: normalizedData.length,
      });

      // Validate the data
      let preview = validateImportData(normalizedData, detectedType, columns);
      preview.detectedFormat = detectFileFormat(file);

      // Add duplicate warnings
      const duplicateWarnings = findDuplicates(normalizedData, detectedType);
      if (duplicateWarnings.length > 0) {
        for (const warning of duplicateWarnings) {
          const row = preview.rows.find(r => r.rowNumber === warning.row);
          if (row) {
            row.warnings.push(warning);
            if (row.status === 'valid') {
              row.status = 'warning';
              preview.warningRows++;
            }
          }
        }
      }

      // Add overlapping absence warnings
      if (detectedType === 'absences') {
        const overlapWarnings = findOverlappingAbsences(normalizedData);
        for (const warning of overlapWarnings) {
          const row = preview.rows.find(r => r.rowNumber === warning.row);
          if (row) {
            row.warnings.push(warning);
            if (row.status === 'valid') {
              row.status = 'warning';
              preview.warningRows++;
            }
          }
        }
      }

      setState(prev => ({
        ...prev,
        dataType: detectedType,
        preview,
      }));

      updateProgress({
        status: 'idle',
        message: 'Preview ready',
        processedRows: normalizedData.length,
      });

      return preview;
    } catch (error) {
      updateProgress({
        status: 'error',
        message: error instanceof Error ? error.message : 'Failed to parse file',
      });
      throw error;
    }
  }, [state.dataType, state.dataTypeSource, parseFile, updateProgress]);

  // ============================================================================
  // Execute Import Mutation
  // ============================================================================

  const importMutation = useMutation<ImportResult, ApiError, Record<string, unknown>[]>({
    mutationFn: async (data) => {
      const endpoint = IMPORT_ENDPOINTS[state.dataType];
      return post<ImportResult>(endpoint, {
        items: data,
        options: state.options,
      });
    },
    onSuccess: (result) => {
      // Invalidate relevant queries
      queryClient.invalidateQueries({ queryKey: ['people'] });
      queryClient.invalidateQueries({ queryKey: ['assignments'] });
      queryClient.invalidateQueries({ queryKey: ['absences'] });
      queryClient.invalidateQueries({ queryKey: ['schedule'] });
      queryClient.invalidateQueries({ queryKey: ['validation'] });

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
      throw new Error('No preview available. Please preview the import first.');
    }

    // Create abort controller for cancellation
    abortControllerRef.current = new AbortController();

    const validRows = state.preview.rows.filter(row =>
      row.status === 'valid' ||
      (row.status === 'warning' && state.options.skipInvalidRows)
    );

    if (validRows.length === 0) {
      throw new Error('No valid rows to import');
    }

    updateProgress({
      status: 'importing',
      message: 'Importing data...',
      totalRows: validRows.length,
      currentRow: 0,
      processedRows: 0,
      successCount: 0,
      errorCount: 0,
      warningCount: state.preview.warningRows,
    });

    const dataToImport = validRows.map(row => row.data);
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
          throw new Error('Import cancelled');
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
            column: 'batch',
            value: null,
            message: batchError instanceof Error ? batchError.message : 'Batch import failed',
            severity: 'error',
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
        status: 'complete',
        message: `Import complete: ${successCount} succeeded, ${errorCount} failed`,
        errors,
      });

      return result;
    } catch (error) {
      updateProgress({
        status: 'error',
        message: error instanceof Error ? error.message : 'Import failed',
      });
      throw error;
    }
  }, [state.preview, state.options, state.dataType, updateProgress, importMutation]);

  // ============================================================================
  // Cancel Import
  // ============================================================================

  const cancelImport = useCallback(() => {
    abortControllerRef.current?.abort();
    updateProgress({
      status: 'idle',
      message: 'Import cancelled',
    });
  }, [updateProgress]);

  // ============================================================================
  // Reset State
  // ============================================================================

  const reset = useCallback(() => {
    abortControllerRef.current?.abort();
    setState({
      file: null,
      format: 'csv',
      dataType: hookOptions.dataType || 'schedules',
      dataTypeSource: hookOptions.dataType ? 'manual' : 'auto',
      preview: null,
      progress: {
        status: 'idle',
        currentRow: 0,
        totalRows: 0,
        processedRows: 0,
        successCount: 0,
        errorCount: 0,
        warningCount: 0,
        message: '',
        errors: [],
      },
      options: DEFAULT_IMPORT_OPTIONS,
    });
  }, [hookOptions.dataType]);

  // ============================================================================
  // Update Options
  // ============================================================================

  const updateOptions = useCallback((options: Partial<ImportOptions>) => {
    setState(prev => ({
      ...prev,
      options: { ...prev.options, ...options },
    }));
  }, []);

  // ============================================================================
  // Set Data Type
  // ============================================================================

  const setDataType = useCallback((dataType: ImportDataType) => {
    setState(prev => ({ ...prev, dataType, dataTypeSource: 'manual' }));
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
    isLoading: importMutation.isPending || ['parsing', 'validating', 'importing'].includes(state.progress.status),
    isError: state.progress.status === 'error',

    // Actions
    previewImport,
    executeImport,
    cancelImport,
    reset,
    updateOptions,
    setDataType,
  };
}

// ============================================================================
// Export hook type
// ============================================================================

export type UseImportReturn = ReturnType<typeof useImport>;
