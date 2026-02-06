/**
 * Tests for schedule draft hooks.
 */
import { act, renderHook, waitFor } from '@/test-utils';
import { QueryClient } from '@tanstack/react-query';
import { TestProviders } from '@/test-utils';
import {
  scheduleDraftKeys,
  usePublishScheduleDraft,
  useScheduleDrafts,
} from '@/hooks/useScheduleDrafts';
import * as api from '@/api/schedule-drafts';
import { ReactNode } from 'react';
import { ScheduleDraftStatus } from '@/types/schedule-draft';

jest.mock('@/api/schedule-drafts');

const mockedApi = api as jest.Mocked<typeof api>;

function createWrapper(queryClient?: QueryClient) {
  return function Wrapper({ children }: { children: ReactNode }) {
    return <TestProviders queryClient={queryClient}>{children}</TestProviders>;
  };
}

describe('useScheduleDrafts', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('fetches drafts with pagination and status', async () => {
    mockedApi.listScheduleDrafts.mockResolvedValueOnce({
      items: [],
      total: 0,
      page: 2,
      pageSize: 50,
      hasNext: false,
      hasPrevious: false,
    });

    const { result } = renderHook(
      () => useScheduleDrafts(2, ScheduleDraftStatus.DRAFT, 50),
      { wrapper: createWrapper() }
    );

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(mockedApi.listScheduleDrafts).toHaveBeenCalledWith({
      page: 2,
      pageSize: 50,
      status: ScheduleDraftStatus.DRAFT,
    });
  });
});

describe('usePublishScheduleDraft', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('invalidates detail, list, and preview queries', async () => {
    const queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false, gcTime: 0, staleTime: 0 },
        mutations: { retry: false },
      },
    });
    const invalidateSpy = jest.spyOn(queryClient, 'invalidateQueries');

    mockedApi.publishScheduleDraft.mockResolvedValueOnce({
      draftId: 'draft-1',
      status: ScheduleDraftStatus.PUBLISHED,
      publishedCount: 1,
      errorCount: 0,
      errors: [],
      acgmeWarnings: [],
      rollbackAvailable: false,
      message: 'ok',
    });

    const { result } = renderHook(() => usePublishScheduleDraft(), {
      wrapper: createWrapper(queryClient),
    });

    await act(async () => {
      await result.current.mutateAsync({ draftId: 'draft-1' });
    });

    expect(invalidateSpy).toHaveBeenCalledWith({
      queryKey: scheduleDraftKeys.detail('draft-1'),
    });
    expect(invalidateSpy).toHaveBeenCalledWith({
      queryKey: scheduleDraftKeys.lists(),
    });
    expect(invalidateSpy).toHaveBeenCalledWith({
      queryKey: scheduleDraftKeys.preview('draft-1'),
    });
  });
});
