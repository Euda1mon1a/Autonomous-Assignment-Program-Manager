/**
 * React hook for FMIT block schedule import
 *
 * Provides mutation for uploading Excel files to parse FMIT schedules
 * via the POST /api/v1/schedule/import/block endpoint.
 */

import { useMutation } from '@tanstack/react-query';
import type {
  BlockParseRequest,
  BlockParseResponse,
} from '@/types/fmit-import';

// ============================================================================
// API Function
// ============================================================================

/**
 * Upload and parse a block schedule Excel file
 *
 * @param file - Excel file to upload
 * @param options - Parse options including block number
 * @returns Parsed block schedule data
 */
async function parseBlockSchedule(
  file: File,
  options: BlockParseRequest
): Promise<BlockParseResponse> {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('block_number', options.blockNumber.toString());

  if (options.knownPeople && options.knownPeople.length > 0) {
    formData.append('known_people', JSON.stringify(options.knownPeople));
  }

  formData.append('include_fmit', String(options.includeFmit ?? true));

  const apiBase =
    process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

  const response = await fetch(`${apiBase}/schedule/import/block`, {
    method: 'POST',
    body: formData,
    credentials: 'include',
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({
      detail: 'Unknown error occurred',
    }));
    throw new Error(
      errorData.detail || `Upload failed with status ${response.status}`
    );
  }

  return response.json();
}

// ============================================================================
// Hook Types
// ============================================================================

interface UseFmitImportOptions {
  /** Callback when parsing succeeds */
  onSuccess?: (data: BlockParseResponse) => void;
  /** Callback when parsing fails */
  onError?: (error: Error) => void;
}

interface ParseBlockMutationVariables {
  file: File;
  blockNumber: number;
  knownPeople?: string[];
  includeFmit?: boolean;
}

// ============================================================================
// Hook Implementation
// ============================================================================

/**
 * Hook for parsing FMIT block schedules from Excel files
 *
 * @example
 * ```tsx
 * const { parseBlock, isLoading, error } = useFmitImport({
 *   onSuccess: (data) => console.log('Parsed', data.total_residents, 'residents'),
 *   onError: (error) => console.error('Parse failed:', error.message),
 * });
 *
 * // Trigger parse
 * parseBlock({ file: excelFile, blockNumber: 10 });
 * ```
 */
export function useFmitImport(options: UseFmitImportOptions = {}) {
  const mutation = useMutation<
    BlockParseResponse,
    Error,
    ParseBlockMutationVariables
  >({
    mutationFn: ({ file, blockNumber, knownPeople, includeFmit }) =>
      parseBlockSchedule(file, {
        blockNumber,
        knownPeople,
        includeFmit,
      }),
    onSuccess: options.onSuccess,
    onError: options.onError,
  });

  return {
    /** Trigger block schedule parsing */
    parseBlock: mutation.mutate,
    /** Trigger block schedule parsing (async version) */
    parseBlockAsync: mutation.mutateAsync,
    /** Whether parsing is in progress */
    isLoading: mutation.isPending,
    /** Whether parsing succeeded */
    isSuccess: mutation.isSuccess,
    /** Whether parsing failed */
    isError: mutation.isError,
    /** Error from last parsing attempt */
    error: mutation.error,
    /** Parsed data from last successful parse */
    data: mutation.data,
    /** Reset mutation state */
    reset: mutation.reset,
  };
}

export type UseFmitImportReturn = ReturnType<typeof useFmitImport>;
