/**
 * Tests for admin dashboard hooks.
 */
import { renderHook, waitFor } from '@/test-utils';
import { QueryClient } from '@tanstack/react-query';
import { TestProviders } from '@/test-utils';
import {
  useAdminDashboardSummary,
  useBreakGlassUsage,
} from '@/hooks/useAdminDashboard';
import * as api from '@/lib/api';
import { ReactNode } from 'react';

jest.mock('@/lib/api');

const mockedApi = api as jest.Mocked<typeof api>;

function createWrapper(queryClient?: QueryClient) {
  return function Wrapper({ children }: { children: ReactNode }) {
    return <TestProviders queryClient={queryClient}>{children}</TestProviders>;
  };
}

describe('useAdminDashboardSummary', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('fetches summary metrics', async () => {
    mockedApi.get.mockResolvedValueOnce({
      totalUsers: 5,
      totalPeople: 10,
      totalAbsences: 2,
      totalSwaps: 1,
      totalConflicts: 0,
    });

    const { result } = renderHook(() => useAdminDashboardSummary(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(mockedApi.get).toHaveBeenCalledWith('/admin/dashboard/summary');
  });
});

describe('useBreakGlassUsage', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('fetches break-glass usage data', async () => {
    mockedApi.get.mockResolvedValueOnce({
      windowStart: '2025-01-01',
      windowEnd: '2025-01-31',
      count: 2,
      lastUsedAt: '2025-01-15T00:00:00Z',
    });

    const { result } = renderHook(() => useBreakGlassUsage(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(mockedApi.get).toHaveBeenCalledWith('/admin/dashboard/break-glass');
  });
});
