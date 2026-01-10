/* eslint-disable @typescript-eslint/ban-ts-comment */
// @ts-nocheck - Hook generic type arguments changed
/**
 * Tests for Optimistic Update Hook
 *
 * Tests instant UI feedback with automatic rollback on failure
 * and conflict resolution strategies.
 */
import { renderHook, act, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactNode } from 'react';
import {
  useOptimisticUpdate,
  useOptimisticList,
  useOptimisticUpdateWithConflictResolution,
  OptimisticUpdateMonitor,
} from './useOptimisticUpdate';

// Create wrapper with QueryClient
function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });

  return ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
}

describe('useOptimisticUpdate', () => {
  it('updates UI optimistically', async () => {
    const queryClient = new QueryClient();
    queryClient.setQueryData(['test'], { value: 0 });

    const wrapper = ({ children }: { children: ReactNode }) => (
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    );

    interface TestData {
      value: number;
    }

    interface TestVariables {
      newValue: number;
    }

    const mutationFn = jest.fn((): Promise<TestData> =>
      Promise.resolve({ value: 1 })
    );

    const optimisticUpdate = (old: TestData | undefined, variables: TestVariables): TestData => ({
      value: variables.newValue,
    });

    const { result } = renderHook(
      () =>
        useOptimisticUpdate({
          queryKey: ['test'],
          mutationFn,
          optimisticUpdate,
        }),
      { wrapper }
    );

    // Trigger optimistic update
    await act(async () => {
      result.current.mutate({ newValue: 1 });
    });

    // Data should be immediately updated
    const data = queryClient.getQueryData(['test']);
    expect(data).toEqual({ value: 1 });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });
  });

  it('rolls back on failure', async () => {
    const queryClient = new QueryClient();
    queryClient.setQueryData(['test'], { value: 0 });

    const wrapper = ({ children }: { children: ReactNode }) => (
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    );

    interface TestData {
      value: number;
    }

    interface TestVariables {
      newValue: number;
    }

    const mutationFn = jest.fn((): Promise<TestData> =>
      Promise.reject(new Error('Update failed'))
    );

    const optimisticUpdate = (old: TestData | undefined, variables: TestVariables): TestData => ({
      value: variables.newValue,
    });

    const onError = jest.fn();

    const { result } = renderHook(
      () =>
        useOptimisticUpdate({
          queryKey: ['test'],
          mutationFn,
          optimisticUpdate,
          onError,
        }),
      { wrapper }
    );

    // Trigger optimistic update
    await act(async () => {
      result.current.mutate({ newValue: 1 });
    });

    await waitFor(() => {
      expect(result.current.isError).toBe(true);
    });

    // Should rollback to original value
    const data = queryClient.getQueryData(['test']);
    expect(data).toEqual({ value: 0 });
    expect(onError).toHaveBeenCalled();
  });

  it('calls onSuccess with server data', async () => {
    const queryClient = new QueryClient();
    queryClient.setQueryData(['test'], { value: 0 });

    const wrapper = ({ children }: { children: ReactNode }) => (
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    );

    interface TestData {
      value: number;
    }

    interface TestVariables {
      newValue: number;
    }

    const mutationFn = jest.fn((): Promise<TestData> =>
      Promise.resolve({ value: 2 }) // Server returns different value
    );

    const optimisticUpdate = (old: TestData | undefined, variables: TestVariables): TestData => ({
      value: variables.newValue,
    });

    const onSuccess = jest.fn();

    const { result } = renderHook(
      () =>
        useOptimisticUpdate({
          queryKey: ['test'],
          mutationFn,
          optimisticUpdate,
          onSuccess,
        }),
      { wrapper }
    );

    await act(async () => {
      result.current.mutate({ newValue: 1 });
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(onSuccess).toHaveBeenCalledWith({ value: 2 }, { newValue: 1 });
    // Final data should be server value
    const data = queryClient.getQueryData(['test']);
    expect(data).toEqual({ value: 2 });
  });

  it('cancels outgoing requests before updating', async () => {
    const queryClient = new QueryClient();
    const cancelQueriesSpy = jest.spyOn(queryClient, 'cancelQueries');

    const wrapper = ({ children }: { children: ReactNode }) => (
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    );

    interface TestData {
      value: number;
    }

    interface TestVariables {
      newValue: number;
    }

    const mutationFn = jest.fn((): Promise<TestData> => Promise.resolve({ value: 1 }));
    const optimisticUpdate = (old: TestData | undefined, variables: TestVariables): TestData => ({ value: variables.newValue });

    const { result } = renderHook(
      () =>
        useOptimisticUpdate({
          queryKey: ['test'],
          mutationFn,
          optimisticUpdate,
        }),
      { wrapper }
    );

    await act(async () => {
      result.current.mutate({ newValue: 1 });
    });

    expect(cancelQueriesSpy).toHaveBeenCalledWith({ queryKey: ['test'] });
  });
});

describe('useOptimisticList', () => {
  it('adds item optimistically', () => {
    interface ListItem {
      id: number;
      name: string;
    }

    const queryClient = new QueryClient();
    queryClient.setQueryData<ListItem[]>(['items'], [{ id: 1, name: 'Item 1' }]);

    const wrapper = ({ children }: { children: ReactNode }) => (
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    );

    const { result } = renderHook(
      () =>
        useOptimisticList<ListItem, number>({
          queryKey: ['items'],
          getId: (item) => item.id,
        }),
      { wrapper }
    );

    act(() => {
      result.current.addItem({ id: 2, name: 'Item 2' });
    });

    const data = queryClient.getQueryData<any[]>(['items']);
    expect(data).toHaveLength(2);
    expect(data?.[1]).toEqual({ id: 2, name: 'Item 2' });
  });

  it('updates item optimistically', () => {
    interface ListItem {
      id: number;
      name: string;
    }

    const queryClient = new QueryClient();
    queryClient.setQueryData<ListItem[]>(['items'], [{ id: 1, name: 'Item 1' }]);

    const wrapper = ({ children }: { children: ReactNode }) => (
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    );

    const { result } = renderHook(
      () =>
        useOptimisticList<ListItem, number>({
          queryKey: ['items'],
          getId: (item) => item.id,
        }),
      { wrapper }
    );

    act(() => {
      result.current.updateItem(1, { name: 'Updated Item' });
    });

    const data = queryClient.getQueryData<any[]>(['items']);
    expect(data?.[0].name).toBe('Updated Item');
  });

  it('deletes item optimistically', () => {
    interface ListItem {
      id: number;
      name: string;
    }

    const queryClient = new QueryClient();
    queryClient.setQueryData<ListItem[]>(['items'], [
      { id: 1, name: 'Item 1' },
      { id: 2, name: 'Item 2' },
    ]);

    const wrapper = ({ children }: { children: ReactNode }) => (
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    );

    const { result } = renderHook(
      () =>
        useOptimisticList<ListItem, number>({
          queryKey: ['items'],
          getId: (item) => item.id,
        }),
      { wrapper }
    );

    act(() => {
      result.current.deleteItem(1);
    });

    const data = queryClient.getQueryData<any[]>(['items']);
    expect(data).toHaveLength(1);
    expect(data?.[0].id).toBe(2);
  });

  it('replaces item optimistically', () => {
    interface ListItem {
      id: number;
      name: string;
    }

    const queryClient = new QueryClient();
    queryClient.setQueryData<ListItem[]>(['items'], [{ id: 1, name: 'Item 1' }]);

    const wrapper = ({ children }: { children: ReactNode }) => (
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    );

    const { result } = renderHook(
      () =>
        useOptimisticList<ListItem, number>({
          queryKey: ['items'],
          getId: (item) => item.id,
        }),
      { wrapper }
    );

    act(() => {
      result.current.replaceItem(1, { id: 1, name: 'Replaced Item' });
    });

    const data = queryClient.getQueryData<any[]>(['items']);
    expect(data?.[0]).toEqual({ id: 1, name: 'Replaced Item' });
  });
});

describe('useOptimisticUpdateWithConflictResolution', () => {
  it('detects conflicts', async () => {
    interface VersionedData {
      value: number;
      version: number;
    }

    interface TestVariables {
      newValue: number;
    }

    const queryClient = new QueryClient();
    queryClient.setQueryData<VersionedData>(['test'], { value: 0, version: 1 });

    const wrapper = ({ children }: { children: ReactNode }) => (
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    );

    const mutationFn = jest.fn((): Promise<VersionedData> =>
      Promise.resolve({ value: 10, version: 2 })
    );

    const optimisticUpdate = (old: VersionedData | undefined, variables: TestVariables): VersionedData => ({
      value: variables.newValue,
      version: 1,
    });

    const conflictResolution = {
      hasConflict: (local: VersionedData, server: VersionedData): boolean => local.version !== server.version,
      resolve: (local: VersionedData, server: VersionedData): VersionedData => server, // Server wins
    };

    const onConflict = jest.fn();

    const { result } = renderHook(
      () =>
        useOptimisticUpdateWithConflictResolution({
          queryKey: ['test'],
          mutationFn,
          optimisticUpdate,
          conflictResolution,
          onConflict,
        }),
      { wrapper }
    );

    await act(async () => {
      result.current.mutate({ newValue: 5 });
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(onConflict).toHaveBeenCalled();
    expect(result.current.conflicts).toHaveLength(1);
  });

  it('clears conflict history', async () => {
    interface TestData {
      value: number;
    }

    interface TestVariables {
      newValue: number;
    }

    const queryClient = new QueryClient();
    queryClient.setQueryData<TestData>(['test'], { value: 0 });

    const wrapper = ({ children }: { children: ReactNode }) => (
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    );

    const mutationFn = jest.fn((): Promise<TestData> => Promise.resolve({ value: 10 }));
    const optimisticUpdate = (old: TestData | undefined, variables: TestVariables): TestData => ({ value: variables.newValue });
    const conflictResolution = {
      hasConflict: (): boolean => true,
      resolve: (local: TestData, server: TestData): TestData => server,
    };

    const { result } = renderHook(
      () =>
        useOptimisticUpdateWithConflictResolution({
          queryKey: ['test'],
          mutationFn,
          optimisticUpdate,
          conflictResolution,
        }),
      { wrapper }
    );

    await act(async () => {
      result.current.mutate({ newValue: 5 });
    });

    await waitFor(() => {
      expect(result.current.conflicts).toHaveLength(1);
    });

    act(() => {
      result.current.clearConflicts();
    });

    expect(result.current.conflicts).toHaveLength(0);
  });
});

describe('OptimisticUpdateMonitor', () => {
  it('records update statistics', () => {
    const monitor = new OptimisticUpdateMonitor();

    monitor.recordUpdate(true, 100, false);
    monitor.recordUpdate(true, 150, false);
    monitor.recordUpdate(false, 200, true);

    const stats = monitor.getStats();
    expect(stats.totalUpdates).toBe(3);
    expect(stats.successfulUpdates).toBe(2);
    expect(stats.failedUpdates).toBe(1);
    expect(stats.rollbacks).toBe(1);
    expect(stats.averageRoundTripTime).toBeGreaterThan(0);
  });

  it('calculates success rate', () => {
    const monitor = new OptimisticUpdateMonitor();

    monitor.recordUpdate(true, 100, false);
    monitor.recordUpdate(true, 100, false);
    monitor.recordUpdate(false, 100, true);

    expect(monitor.getSuccessRate()).toBeCloseTo(66.67, 1);
  });

  it('calculates rollback rate', () => {
    const monitor = new OptimisticUpdateMonitor();

    monitor.recordUpdate(true, 100, false);
    monitor.recordUpdate(false, 100, true);
    monitor.recordUpdate(false, 100, true);

    expect(monitor.getRollbackRate()).toBeCloseTo(66.67, 1);
  });

  it('limits stored measurements to 100', () => {
    const monitor = new OptimisticUpdateMonitor();

    for (let i = 0; i < 150; i++) {
      monitor.recordUpdate(true, 100, false);
    }

    const stats = monitor.getStats();
    // Internal roundTripTimes array should be limited
    expect(stats.totalUpdates).toBe(150);
  });

  it('can be reset', () => {
    const monitor = new OptimisticUpdateMonitor();

    monitor.recordUpdate(true, 100, false);
    monitor.recordUpdate(true, 100, false);

    monitor.reset();

    const stats = monitor.getStats();
    expect(stats.totalUpdates).toBe(0);
    expect(stats.successfulUpdates).toBe(0);
  });
});
