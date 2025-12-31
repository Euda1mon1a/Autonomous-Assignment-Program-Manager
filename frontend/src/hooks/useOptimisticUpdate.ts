/**
 * Optimistic update hook for instant UI feedback.
 *
 * Updates UI immediately while API call is in progress,
 * then reconciles with server response.
 */

import { useMutation, useQueryClient } from '@tanstack/react-query';
import { useCallback, useState } from 'react';

export interface OptimisticUpdateOptions<T, V> {
  /** Query key to update */
  queryKey: string[];
  /** Mutation function */
  mutationFn: (variables: V) => Promise<T>;
  /** Optimistic update function */
  optimisticUpdate: (currentData: T | undefined, variables: V) => T;
  /** Rollback function on error */
  onError?: (error: Error, variables: V, context: any) => void;
  /** Success callback */
  onSuccess?: (data: T, variables: V) => void;
}

export function useOptimisticUpdate<T, V>({
  queryKey,
  mutationFn,
  optimisticUpdate,
  onError,
  onSuccess,
}: OptimisticUpdateOptions<T, V>) {
  const queryClient = useQueryClient();

  const mutation = useMutation({
    mutationFn,
    onMutate: async (variables: V) => {
      // Cancel outgoing refetches
      await queryClient.cancelQueries({ queryKey });

      // Snapshot previous value
      const previousData = queryClient.getQueryData<T>(queryKey);

      // Optimistically update
      queryClient.setQueryData<T>(queryKey, (old) =>
        optimisticUpdate(old, variables)
      );

      // Return snapshot for rollback
      return { previousData };
    },
    onError: (error: Error, variables: V, context: any) => {
      // Rollback to previous value
      if (context?.previousData) {
        queryClient.setQueryData(queryKey, context.previousData);
      }

      onError?.(error, variables, context);
    },
    onSuccess: (data: T, variables: V) => {
      // Update with actual server response
      queryClient.setQueryData(queryKey, data);
      onSuccess?.(data, variables);
    },
    onSettled: () => {
      // Always refetch after mutation
      queryClient.invalidateQueries({ queryKey });
    },
  });

  return mutation;
}

/**
 * Optimistic list operations (add, update, delete).
 */
export interface OptimisticListOptions<T> {
  queryKey: string[];
  getId: (item: T) => string | number;
}

export function useOptimisticList<T>({
  queryKey,
  getId,
}: OptimisticListOptions<T>) {
  const queryClient = useQueryClient();

  const addItem = useCallback(
    (item: T) => {
      queryClient.setQueryData<T[]>(queryKey, (old = []) => [...old, item]);
    },
    [queryClient, queryKey]
  );

  const updateItem = useCallback(
    (id: string | number, updates: Partial<T>) => {
      queryClient.setQueryData<T[]>(queryKey, (old = []) =>
        old.map((item) =>
          getId(item) === id ? { ...item, ...updates } : item
        )
      );
    },
    [queryClient, queryKey, getId]
  );

  const deleteItem = useCallback(
    (id: string | number) => {
      queryClient.setQueryData<T[]>(queryKey, (old = []) =>
        old.filter((item) => getId(item) !== id)
      );
    },
    [queryClient, queryKey, getId]
  );

  const replaceItem = useCallback(
    (id: string | number, newItem: T) => {
      queryClient.setQueryData<T[]>(queryKey, (old = []) =>
        old.map((item) => (getId(item) === id ? newItem : item))
      );
    },
    [queryClient, queryKey, getId]
  );

  return {
    addItem,
    updateItem,
    deleteItem,
    replaceItem,
  };
}

/**
 * Optimistic update with conflict resolution.
 */
export interface ConflictResolutionStrategy<T> {
  /** Check if server data conflicts with local changes */
  hasConflict: (local: T, server: T) => boolean;
  /** Resolve conflict between local and server data */
  resolve: (local: T, server: T) => T;
}

export function useOptimisticUpdateWithConflictResolution<T, V>({
  queryKey,
  mutationFn,
  optimisticUpdate,
  conflictResolution,
  onConflict,
}: OptimisticUpdateOptions<T, V> & {
  conflictResolution: ConflictResolutionStrategy<T>;
  onConflict?: (local: T, server: T, resolved: T) => void;
}) {
  const [conflicts, setConflicts] = useState<Array<{
    local: T;
    server: T;
    resolved: T;
    timestamp: number;
  }>>([]);

  const queryClient = useQueryClient();

  const mutation = useMutation({
    mutationFn,
    onMutate: async (variables: V) => {
      await queryClient.cancelQueries({ queryKey });

      const previousData = queryClient.getQueryData<T>(queryKey);

      queryClient.setQueryData<T>(queryKey, (old) =>
        optimisticUpdate(old, variables)
      );

      return { previousData };
    },
    onSuccess: (serverData: T, variables: V, context: any) => {
      const localData = queryClient.getQueryData<T>(queryKey);

      // Check for conflicts
      if (
        localData &&
        conflictResolution.hasConflict(localData, serverData)
      ) {
        // Resolve conflict
        const resolved = conflictResolution.resolve(localData, serverData);

        // Record conflict
        setConflicts((prev) => [
          ...prev,
          {
            local: localData,
            server: serverData,
            resolved,
            timestamp: Date.now(),
          },
        ]);

        // Apply resolved data
        queryClient.setQueryData(queryKey, resolved);

        onConflict?.(localData, serverData, resolved);
      } else {
        // No conflict, use server data
        queryClient.setQueryData(queryKey, serverData);
      }
    },
  });

  const clearConflicts = useCallback(() => {
    setConflicts([]);
  }, []);

  return {
    ...mutation,
    conflicts,
    clearConflicts,
  };
}

/**
 * Performance monitoring for optimistic updates.
 */
export class OptimisticUpdateMonitor {
  private stats = {
    totalUpdates: 0,
    successfulUpdates: 0,
    failedUpdates: 0,
    rollbacks: 0,
    averageRoundTripTime: 0,
  };

  private roundTripTimes: number[] = [];

  recordUpdate(success: boolean, roundTripTime: number, rolledBack: boolean): void {
    this.stats.totalUpdates++;

    if (success) {
      this.stats.successfulUpdates++;
    } else {
      this.stats.failedUpdates++;
    }

    if (rolledBack) {
      this.stats.rollbacks++;
    }

    this.roundTripTimes.push(roundTripTime);

    // Keep only last 100 measurements
    if (this.roundTripTimes.length > 100) {
      this.roundTripTimes.shift();
    }

    // Update average
    this.stats.averageRoundTripTime =
      this.roundTripTimes.reduce((a, b) => a + b, 0) /
      this.roundTripTimes.length;
  }

  getSuccessRate(): number {
    return this.stats.totalUpdates > 0
      ? (this.stats.successfulUpdates / this.stats.totalUpdates) * 100
      : 0;
  }

  getRollbackRate(): number {
    return this.stats.totalUpdates > 0
      ? (this.stats.rollbacks / this.stats.totalUpdates) * 100
      : 0;
  }

  getStats() {
    return {
      ...this.stats,
      successRate: this.getSuccessRate(),
      rollbackRate: this.getRollbackRate(),
    };
  }

  reset(): void {
    this.stats = {
      totalUpdates: 0,
      successfulUpdates: 0,
      failedUpdates: 0,
      rollbacks: 0,
      averageRoundTripTime: 0,
    };
    this.roundTripTimes = [];
  }
}
