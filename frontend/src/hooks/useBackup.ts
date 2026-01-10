/**
 * Backup Hooks
 *
 * TanStack Query hooks for database backup operations.
 * Used before bulk operations to create restore points.
 */
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { get, post } from '@/lib/api';
import type { ApiError } from '@/lib/api';

// ============================================================================
// Types
// ============================================================================

export interface SnapshotRequest {
  table: string;
  reason: string;
}

export interface SnapshotResponse {
  snapshot_id: string;
  table: string;
  row_count: number;
  file_path: string;
  createdAt: string;
  createdBy: string;
  reason: string;
}

export interface SnapshotListResponse {
  snapshots: SnapshotResponse[];
  total: number;
}

export interface RestoreRequest {
  snapshot_id: string;
  dryRun?: boolean;
}

export interface RestoreResponse {
  snapshot_id: string;
  table: string;
  rows_restored: number;
  dryRun: boolean;
  message: string;
}

// ============================================================================
// Query Keys
// ============================================================================

export const backupQueryKeys = {
  all: ['backup'] as const,
  snapshots: (table?: string) => ['backup', 'snapshots', table] as const,
};

// ============================================================================
// Hooks
// ============================================================================

/**
 * List available snapshots for a table.
 */
export function useSnapshots(table?: string, enabled = false) {
  return useQuery<SnapshotListResponse, ApiError>({
    queryKey: backupQueryKeys.snapshots(table),
    queryFn: async () => {
      const params = new URLSearchParams();
      if (table) params.append('table', table);
      const query = params.toString();
      return get<SnapshotListResponse>(`/backup/snapshots${query ? `?${query}` : ''}`);
    },
    enabled,
    staleTime: 60 * 1000, // 1 minute
  });
}

/**
 * Create a snapshot before bulk operations.
 *
 * @example
 * ```tsx
 * const createSnapshot = useCreateSnapshot();
 *
 * // Before bulk delete
 * await createSnapshot.mutateAsync({
 *   table: 'rotationTemplates',
 *   reason: 'Before bulk delete of 5 templates'
 * });
 * ```
 */
export function useCreateSnapshot() {
  const queryClient = useQueryClient();

  return useMutation<SnapshotResponse, ApiError, SnapshotRequest>({
    mutationFn: async (request) => {
      return post<SnapshotResponse>('/backup/snapshot', request);
    },
    onSuccess: (_, { table }) => {
      queryClient.invalidateQueries({
        queryKey: backupQueryKeys.snapshots(table),
      });
    },
  });
}

/**
 * Restore from a snapshot.
 *
 * @example
 * ```tsx
 * const restoreSnapshot = useRestoreSnapshot();
 *
 * // Preview restore (dry run)
 * const preview = await restoreSnapshot.mutateAsync({
 *   snapshot_id: 'rotationTemplates_20260107_120000',
 *   dryRun: true
 * });
 *
 * // Actually restore
 * await restoreSnapshot.mutateAsync({
 *   snapshot_id: 'rotationTemplates_20260107_120000',
 *   dryRun: false
 * });
 * ```
 */
export function useRestoreSnapshot() {
  const queryClient = useQueryClient();

  return useMutation<RestoreResponse, ApiError, RestoreRequest>({
    mutationFn: async (request) => {
      return post<RestoreResponse>('/backup/restore', request);
    },
    onSuccess: () => {
      // Invalidate all queries since table data changed
      queryClient.invalidateQueries();
    },
  });
}

/**
 * Helper hook that creates a snapshot before executing a callback.
 * Useful for wrapping bulk operations with automatic backup.
 *
 * @example
 * ```tsx
 * const { execute, isCreatingSnapshot } = useWithBackup();
 *
 * const handleBulkDelete = async (ids: string[]) => {
 *   await execute(
 *     { table: 'rotationTemplates', reason: `Delete ${ids.length} templates` },
 *     async () => {
 *       await bulkDelete.mutateAsync(ids);
 *     }
 *   );
 * };
 * ```
 */
export function useWithBackup() {
  const createSnapshot = useCreateSnapshot();

  const execute = async <T>(
    snapshotRequest: SnapshotRequest,
    operation: () => Promise<T>
  ): Promise<{ snapshot: SnapshotResponse; result: T }> => {
    // Create snapshot first
    const snapshot = await createSnapshot.mutateAsync(snapshotRequest);

    // Execute the operation
    const result = await operation();

    return { snapshot, result };
  };

  return {
    execute,
    isCreatingSnapshot: createSnapshot.isPending,
    snapshotError: createSnapshot.error,
  };
}
