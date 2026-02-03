/**
 * Tests for half-day import hooks.
 */
import { renderHook, act, waitFor } from '@/test-utils';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactNode } from 'react';
import {
  useStageHalfDayImport,
  useHalfDayImportPreview,
  useCreateHalfDayDraft,
  halfDayImportKeys,
} from '@/hooks/useHalfDayImport';
import * as api from '@/api/half-day-import';

jest.mock('@/api/half-day-import');

const mockedApi = api as jest.Mocked<typeof api>;

function createWrapper(queryClient?: QueryClient) {
  const client =
    queryClient ||
    new QueryClient({
      defaultOptions: {
        queries: { retry: false, gcTime: 0, staleTime: 0 },
        mutations: { retry: false },
      },
    });

  return function Wrapper({ children }: { children: ReactNode }) {
    return <QueryClientProvider client={client}>{children}</QueryClientProvider>;
  };
}

describe('useStageHalfDayImport', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('invalidates preview queries on success', async () => {
    const queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false, gcTime: 0, staleTime: 0 },
        mutations: { retry: false },
      },
    });
    const invalidateSpy = jest.spyOn(queryClient, 'invalidateQueries');

    mockedApi.stageHalfDayImport.mockResolvedValueOnce({
      success: true,
      batchId: 'batch-1',
      createdAt: '2025-01-01T00:00:00Z',
      message: 'ok',
      warnings: [],
      diffMetrics: null,
    });

    const { result } = renderHook(() => useStageHalfDayImport(), {
      wrapper: createWrapper(queryClient),
    });

    await act(async () => {
      await result.current.mutateAsync({
        file: new File(['data'], 'schedule.xlsx'),
        blockNumber: 1,
        academicYear: 2025,
      });
    });

    expect(invalidateSpy).toHaveBeenCalledWith({
      queryKey: halfDayImportKeys.all,
    });
  });
});

describe('useHalfDayImportPreview', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('fetches preview data with filters', async () => {
    mockedApi.previewHalfDayImport.mockResolvedValueOnce({
      batchId: 'batch-1',
      metrics: {
        totalSlots: 10,
        changedSlots: 2,
        added: 1,
        removed: 0,
        modified: 1,
        percentChanged: 20,
        manualHalfDays: 0,
        manualHours: 0,
        byActivity: {},
      },
      diffs: [],
      totalDiffs: 0,
      page: 1,
      pageSize: 50,
    });

    const filters = {
      diffType: 'added' as const,
      activityCode: 'C',
      hasErrors: false,
      personId: 'person-1',
    };

    const { result } = renderHook(
      () => useHalfDayImportPreview('batch-1', 1, 50, filters),
      { wrapper: createWrapper() }
    );

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(mockedApi.previewHalfDayImport).toHaveBeenCalledWith('batch-1', {
      page: 1,
      pageSize: 50,
      diffType: filters.diffType,
      activityCode: filters.activityCode,
      hasErrors: filters.hasErrors,
      personId: filters.personId,
    });
  });
});

describe('useCreateHalfDayDraft', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('creates draft with payload', async () => {
    mockedApi.createHalfDayDraft.mockResolvedValueOnce({
      success: true,
      batchId: 'batch-1',
      draftId: 'draft-1',
      message: 'draft created',
      totalSelected: 1,
      added: 1,
      modified: 0,
      removed: 0,
      skipped: 0,
      failed: 0,
      failedIds: [],
    });

    const { result } = renderHook(() => useCreateHalfDayDraft(), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      await result.current.mutateAsync({
        batchId: 'batch-1',
        payload: { stagedIds: ['staged-1'], notes: 'ok' },
      });
    });

    expect(mockedApi.createHalfDayDraft).toHaveBeenCalledWith('batch-1', {
      stagedIds: ['staged-1'],
      notes: 'ok',
    });
  });
});
