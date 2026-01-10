/**
 * Tests for Resilience Framework Hooks
 *
 * Tests emergency coverage handling for deployments and absences
 * with automatic replacement finding and ACGME compliance validation.
 */
import { renderHook, act, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactNode } from 'react';
import { useEmergencyCoverage } from './useResilience';
import * as api from '@/lib/api';

// Mock the API module
jest.mock('@/lib/api');

const mockedApi = api as jest.Mocked<typeof api>;

// Test data
const mockEmergencyCoverageRequest = {
  personId: 'person-123',
  startDate: '2024-01-15',
  endDate: '2024-01-22',
  reason: 'TDY deployment',
  isDeployment: true,
};

const mockSuccessResponse = {
  status: 'success' as const,
  replacementsFound: 7,
  coverageGaps: 0,
  requiresManualReview: false,
  details: [
    {
      date: '2024-01-15',
      originalAssignment: 'assignment-1',
      replacement: 'person-456',
      status: 'replaced',
    },
    {
      date: '2024-01-16',
      originalAssignment: 'assignment-2',
      replacement: 'person-789',
      status: 'replaced',
    },
  ],
};

const mockPartialResponse = {
  status: 'partial' as const,
  replacementsFound: 5,
  coverageGaps: 2,
  requiresManualReview: true,
  details: [
    {
      date: '2024-01-15',
      originalAssignment: 'assignment-1',
      replacement: 'person-456',
      status: 'replaced',
    },
    {
      date: '2024-01-16',
      originalAssignment: 'assignment-2',
      replacement: undefined,
      status: 'gap',
    },
  ],
};

const mockFailedResponse = {
  status: 'failed' as const,
  replacementsFound: 0,
  coverageGaps: 7,
  requiresManualReview: true,
  details: [
    {
      date: '2024-01-15',
      originalAssignment: 'assignment-1',
      replacement: undefined,
      status: 'gap',
    },
  ],
};

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

describe('useEmergencyCoverage', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('handles successful emergency coverage', async () => {
    mockedApi.post.mockResolvedValueOnce(mockSuccessResponse);

    const { result } = renderHook(() => useEmergencyCoverage(), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      result.current.mutate(mockEmergencyCoverageRequest);
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(result.current.data).toEqual(mockSuccessResponse);
    expect(result.current.data?.status).toBe('success');
    expect(result.current.data?.replacementsFound).toBe(7);
    expect(result.current.data?.coverageGaps).toBe(0);
    expect(result.current.data?.requiresManualReview).toBe(false);
    expect(mockedApi.post).toHaveBeenCalledWith(
      '/schedule/emergency-coverage',
      mockEmergencyCoverageRequest
    );
  });

  it('handles partial coverage with gaps', async () => {
    mockedApi.post.mockResolvedValueOnce(mockPartialResponse);

    const { result } = renderHook(() => useEmergencyCoverage(), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      result.current.mutate(mockEmergencyCoverageRequest);
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(result.current.data?.status).toBe('partial');
    expect(result.current.data?.coverageGaps).toBe(2);
    expect(result.current.data?.requiresManualReview).toBe(true);
  });

  it('handles failed coverage attempts', async () => {
    mockedApi.post.mockResolvedValueOnce(mockFailedResponse);

    const { result } = renderHook(() => useEmergencyCoverage(), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      result.current.mutate(mockEmergencyCoverageRequest);
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(result.current.data?.status).toBe('failed');
    expect(result.current.data?.replacementsFound).toBe(0);
    expect(result.current.data?.requiresManualReview).toBe(true);
  });

  it('provides detailed replacement information', async () => {
    mockedApi.post.mockResolvedValueOnce(mockSuccessResponse);

    const { result } = renderHook(() => useEmergencyCoverage(), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      result.current.mutate(mockEmergencyCoverageRequest);
    });

    await waitFor(() => {
      expect(result.current.data?.details).toHaveLength(2);
    });

    const firstDetail = result.current.data?.details[0];
    expect(firstDetail?.date).toBe('2024-01-15');
    expect(firstDetail?.originalAssignment).toBe('assignment-1');
    expect(firstDetail?.replacement).toBe('person-456');
    expect(firstDetail?.status).toBe('replaced');
  });

  it('handles non-deployment absences', async () => {
    const absenceRequest = {
      personId: 'person-123',
      startDate: '2024-01-15',
      endDate: '2024-01-17',
      reason: 'Medical emergency',
      isDeployment: false,
    };

    mockedApi.post.mockResolvedValueOnce(mockSuccessResponse);

    const { result } = renderHook(() => useEmergencyCoverage(), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      result.current.mutate(absenceRequest);
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(mockedApi.post).toHaveBeenCalledWith(
      '/schedule/emergency-coverage',
      absenceRequest
    );
  });

  it('handles single-day coverage requests', async () => {
    const singleDayRequest = {
      ...mockEmergencyCoverageRequest,
      startDate: '2024-01-15',
      endDate: '2024-01-15',
    };

    const singleDayResponse = {
      ...mockSuccessResponse,
      replacementsFound: 1,
      details: [
        {
          date: '2024-01-15',
          originalAssignment: 'assignment-1',
          replacement: 'person-456',
          status: 'replaced',
        },
      ],
    };

    mockedApi.post.mockResolvedValueOnce(singleDayResponse);

    const { result } = renderHook(() => useEmergencyCoverage(), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      result.current.mutate(singleDayRequest);
    });

    await waitFor(() => {
      expect(result.current.data?.replacementsFound).toBe(1);
    });
  });

  it('handles extended deployment periods', async () => {
    const extendedRequest = {
      ...mockEmergencyCoverageRequest,
      startDate: '2024-01-01',
      endDate: '2024-03-31',
      reason: '90-day TDY',
    };

    const extendedResponse = {
      ...mockSuccessResponse,
      replacementsFound: 90,
    };

    mockedApi.post.mockResolvedValueOnce(extendedResponse);

    const { result } = renderHook(() => useEmergencyCoverage(), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      result.current.mutate(extendedRequest);
    });

    await waitFor(() => {
      expect(result.current.data?.replacementsFound).toBe(90);
    });
  });

  it('handles API errors', async () => {
    const error = {
      status: 409,
      message: 'ACGME compliance violation: Cannot find valid replacements',
    };
    mockedApi.post.mockRejectedValueOnce(error);

    const { result } = renderHook(() => useEmergencyCoverage(), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      result.current.mutate(mockEmergencyCoverageRequest);
    });

    await waitFor(() => {
      expect(result.current.isError).toBe(true);
    });

    expect(result.current.error).toBeTruthy();
  });

  it('invalidates related queries on success', async () => {
    const queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
        mutations: { retry: false },
      },
    });

    const invalidateSpy = jest.spyOn(queryClient, 'invalidateQueries');

    mockedApi.post.mockResolvedValueOnce(mockSuccessResponse);

    const wrapper = ({ children }: { children: ReactNode }) => (
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    );

    const { result } = renderHook(() => useEmergencyCoverage(), { wrapper });

    await act(async () => {
      result.current.mutate(mockEmergencyCoverageRequest);
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    // Should invalidate schedule, assignments, absences, and validation queries
    expect(invalidateSpy).toHaveBeenCalledWith({ queryKey: ['schedule'] });
    expect(invalidateSpy).toHaveBeenCalledWith({ queryKey: ['assignments'] });
    expect(invalidateSpy).toHaveBeenCalledWith({ queryKey: ['absences'] });
    expect(invalidateSpy).toHaveBeenCalledWith({ queryKey: ['validation'] });
  });

  it('handles pending state during request', async () => {
    mockedApi.post.mockImplementation(
      () =>
        new Promise((resolve) =>
          setTimeout(() => resolve(mockSuccessResponse), 100)
        )
    );

    const { result } = renderHook(() => useEmergencyCoverage(), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      result.current.mutate(mockEmergencyCoverageRequest);
    });

    // Should be pending initially
    expect(result.current.isPending).toBe(true);

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });
  });

  it('provides coverage gap details for manual review', async () => {
    mockedApi.post.mockResolvedValueOnce(mockPartialResponse);

    const { result } = renderHook(() => useEmergencyCoverage(), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      result.current.mutate(mockEmergencyCoverageRequest);
    });

    await waitFor(() => {
      expect(result.current.data?.requiresManualReview).toBe(true);
    });

    // Check that gap details are provided
    const gapDetail = result.current.data?.details.find(
      (d) => d.status === 'gap'
    );
    expect(gapDetail).toBeDefined();
    expect(gapDetail?.replacement).toBeUndefined();
  });
});
