/**
 * Tests for import staging hooks.
 */
import { act, renderHook, waitFor } from '@/test-utils';
import { QueryClient } from '@tanstack/react-query';
import { TestProviders } from '@/test-utils';
import {
  importStagingKeys,
  useImportPreview,
  useStageImport,
} from '@/hooks/useImportStaging';
import * as api from '@/lib/api';
import { ReactNode } from 'react';

jest.mock('@/lib/api');

const mockedApi = api as jest.Mocked<typeof api>;

function createWrapper(queryClient?: QueryClient) {
  return function Wrapper({ children }: { children: ReactNode }) {
    return <TestProviders queryClient={queryClient}>{children}</TestProviders>;
  };
}

describe('useStageImport', () => {
  const originalFetch = global.fetch;

  beforeEach(() => {
    jest.clearAllMocks();
    global.fetch = jest.fn();
  });

  afterEach(() => {
    global.fetch = originalFetch;
  });

  it('maps batch_id to batchId and invalidates batches', async () => {
    const queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false, gcTime: 0, staleTime: 0 },
        mutations: { retry: false },
      },
    });
    const invalidateSpy = jest.spyOn(queryClient, 'invalidateQueries');

    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => ({ batchId: 'batch-1' }),
    });

    const { result } = renderHook(() => useStageImport(), {
      wrapper: createWrapper(queryClient),
    });

    await act(async () => {
      await result.current.mutateAsync({
        file: new File(['data'], 'schedule.xlsx'),
      });
    });

    expect(invalidateSpy).toHaveBeenCalledWith({
      queryKey: importStagingKeys.batches(),
    });
  });
});

describe('useImportPreview', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('requests preview with page and page size', async () => {
    mockedApi.get.mockResolvedValueOnce({
      batchId: 'batch-1',
      total: 0,
      items: [],
      page: 2,
      pageSize: 25,
    });

    const { result } = renderHook(
      () => useImportPreview('batch-1', 2, 25),
      { wrapper: createWrapper() }
    );

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(mockedApi.get).toHaveBeenCalledWith(
      '/import/batches/batch-1/preview?page=2&page_size=25'
    );
  });
});
