/**
 * Tests for Admin Scheduling Laboratory Hooks
 *
 * Tests schedule generation experimentation, run history,
 * validation, and manual overrides.
 */
import { renderHook, act, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactNode } from 'react';
import {
  useScheduleRuns,
  useScheduleRun,
  useConstraintConfigs,
  useValidateConfiguration,
  useGenerateScheduleRun,
  useQueueExperiments,
  useRunQueue,
  useLockedAssignments,
  useLockAssignment,
  useUnlockAssignment,
} from './useAdminScheduling';
import * as api from '@/lib/api';

// Mock the API module
jest.mock('@/lib/api');

const mockedApi = api as jest.Mocked<typeof api>;

// Test data
const mockRunLogEntry = {
  id: 'run-123',
  algorithm: 'genetic',
  status: 'completed',
  metrics: {
    coverage: 0.95,
    utilization: 0.75,
    violations: 0,
  },
  started_at: '2024-01-01T00:00:00Z',
  completed_at: '2024-01-01T00:05:00Z',
  created_at: '2024-01-01T00:00:00Z',
};

// Create wrapper
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

describe('useScheduleRuns', () => {
  it('fetches schedule runs successfully', async () => {
    const mockResponse = {
      runs: [mockRunLogEntry],
      total: 1,
    };
    mockedApi.get.mockResolvedValueOnce(mockResponse);

    const { result } = renderHook(() => useScheduleRuns(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.data).toEqual(mockResponse);
  });

  it('applies filters', async () => {
    const mockResponse = {
      runs: [mockRunLogEntry],
      total: 1,
    };
    mockedApi.get.mockResolvedValueOnce(mockResponse);

    const { result } = renderHook(
      () =>
        useScheduleRuns({
          algorithms: ['genetic'],
          status: ['completed'],
        }),
      { wrapper: createWrapper() }
    );

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(mockedApi.get).toHaveBeenCalled();
  });
});

describe('useGenerateScheduleRun', () => {
  it('generates schedule successfully', async () => {
    const mockResult = {
      run_id: 'run-456',
      status: 'completed',
      metrics: { coverage: 0.95 },
    };
    mockedApi.post.mockResolvedValueOnce(mockResult);

    const { result } = renderHook(() => useGenerateScheduleRun(), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      result.current.mutate({
        blockRange: { start: 1, end: 365 },
        academicYear: '2024-2025',
        algorithm: 'genetic',
        timeoutSeconds: 300,
        dryRun: false,
        constraints: [],
        preserveFMIT: true,
        nfPostCallEnabled: true,
      });
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });
  });
});

describe('useLockedAssignments', () => {
  it('fetches locked assignments successfully', async () => {
    const mockLocks = [
      {
        id: 'lock-123',
        assignment_id: 'assignment-456',
        reason: 'VIP schedule',
        locked_at: '2024-01-01T00:00:00Z',
      },
    ];
    mockedApi.get.mockResolvedValueOnce(mockLocks);

    const { result } = renderHook(() => useLockedAssignments(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.data).toEqual(mockLocks);
  });
});

describe('useLockAssignment', () => {
  it('locks assignment successfully', async () => {
    const mockLock = {
      id: 'lock-123',
      assignment_id: 'assignment-456',
      reason: 'VIP schedule',
      locked_at: '2024-01-01T00:00:00Z',
    };
    mockedApi.post.mockResolvedValueOnce(mockLock);

    const { result } = renderHook(() => useLockAssignment(), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      result.current.mutate({
        assignmentId: 'assignment-456',
        reason: 'VIP schedule',
      });
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });
  });
});

describe('useUnlockAssignment', () => {
  it('unlocks assignment successfully', async () => {
    mockedApi.del.mockResolvedValueOnce(undefined);

    const { result } = renderHook(() => useUnlockAssignment(), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      result.current.mutate('lock-123');
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(mockedApi.del).toHaveBeenCalledWith('/schedule/locks/lock-123');
  });
});
