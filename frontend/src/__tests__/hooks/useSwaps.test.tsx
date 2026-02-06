/**
 * useSwaps Hook Tests
 *
 * Tests for swap management hooks including list, detail, create,
 * approve, reject, candidates, and auto-match.
 */
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactNode } from 'react';
import * as api from '@/lib/api';
import {
  useSwapRequest,
  useSwapList,
  useSwapCandidates,
  useSwapCreate,
  useSwapApprove,
  useSwapReject,
  useAutoMatch,
  SwapStatus,
  SwapType,
} from '@/hooks/useSwaps';

// Mock the api module
jest.mock('@/lib/api');

const mockedApi = api as jest.Mocked<typeof api>;

// Create a fresh QueryClient for each test
function createTestQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        gcTime: 0,
        staleTime: 0,
      },
      mutations: {
        retry: false,
      },
    },
  });
}

// Wrapper component with QueryClientProvider
function createWrapper() {
  const queryClient = createTestQueryClient();
  return function Wrapper({ children }: { children: ReactNode }) {
    return (
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    );
  };
}

// Mock data - note enum values are snake_case (Gorgon's Gaze rule)
const mockSwapRequest = {
  id: 'swap-1',
  sourceFacultyId: 'faculty-1',
  sourceFacultyName: 'Dr. Smith',
  sourceWeek: '2024-01-15',
  targetFacultyId: 'faculty-2',
  targetFacultyName: 'Dr. Jones',
  targetWeek: '2024-01-22',
  swapType: 'one_to_one' as const, // snake_case enum value
  status: 'pending' as const, // snake_case enum value
  requestedAt: '2024-01-01T00:00:00Z',
  reason: 'Family emergency',
};

const mockSwapRequests = [
  mockSwapRequest,
  {
    id: 'swap-2',
    sourceFacultyId: 'faculty-3',
    sourceFacultyName: 'Dr. Brown',
    sourceWeek: '2024-02-01',
    swapType: 'absorb' as const, // snake_case enum value
    status: 'approved' as const, // snake_case enum value
    requestedAt: '2024-01-02T00:00:00Z',
  },
];

describe('useSwapRequest', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should fetch single swap request successfully', async () => {
    mockedApi.get.mockResolvedValueOnce(mockSwapRequest);

    const { result } = renderHook(() => useSwapRequest('swap-1'), {
      wrapper: createWrapper(),
    });

    expect(result.current.isLoading).toBe(true);

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(result.current.data).toEqual(mockSwapRequest);
    expect(result.current.data?.swapType).toBe('one_to_one'); // Verify snake_case
    expect(mockedApi.get).toHaveBeenCalledWith('/swaps/swap-1');
  });

  it('should be disabled when id is not provided', () => {
    const { result } = renderHook(() => useSwapRequest(''), {
      wrapper: createWrapper(),
    });

    expect(result.current.isLoading).toBe(false);
    expect(result.current.isFetching).toBe(false);
  });

  it('should handle not found error', async () => {
    const notFoundError = { message: 'Swap request not found', status: 404 };
    mockedApi.get.mockRejectedValueOnce(notFoundError);

    const { result } = renderHook(() => useSwapRequest('swap-999'), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isError).toBe(true);
    });

    expect(result.current.error).toEqual(notFoundError);
  });
});

describe('useSwapList', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should fetch swap list successfully', async () => {
    mockedApi.get.mockResolvedValueOnce({
      items: mockSwapRequests,
      total: 2,
    });

    const { result } = renderHook(() => useSwapList(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(result.current.data?.items).toHaveLength(2);
    expect(result.current.data?.total).toBe(2);
    expect(mockedApi.get).toHaveBeenCalledWith('/swaps');
  });

  it('should apply status filter with snake_case query param', async () => {
    mockedApi.get.mockResolvedValueOnce({
      items: [mockSwapRequest],
      total: 1,
    });

    const { result } = renderHook(
      () =>
        useSwapList({
          status: [SwapStatus.PENDING],
        }),
      {
        wrapper: createWrapper(),
      }
    );

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    // URL param should be snake_case
    expect(mockedApi.get).toHaveBeenCalledWith(
      expect.stringContaining('status=pending')
    );
  });

  it('should apply swap type filter with snake_case query param', async () => {
    mockedApi.get.mockResolvedValueOnce({
      items: [mockSwapRequest],
      total: 1,
    });

    const { result } = renderHook(
      () =>
        useSwapList({
          swapType: [SwapType.ONE_TO_ONE],
        }),
      {
        wrapper: createWrapper(),
      }
    );

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    // URL param should be snake_case
    expect(mockedApi.get).toHaveBeenCalledWith(
      expect.stringContaining('swap_type=oneToOne')
    );
  });

  it('should apply faculty and date filters', async () => {
    mockedApi.get.mockResolvedValueOnce({
      items: [mockSwapRequest],
      total: 1,
    });

    const filters = {
      sourceFacultyId: 'faculty-1',
      targetFacultyId: 'faculty-2',
      startDate: '2024-01-01',
      endDate: '2024-01-31',
    };

    const { result } = renderHook(() => useSwapList(filters), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    // URL params must use snake_case
    expect(mockedApi.get).toHaveBeenCalledWith(
      expect.stringContaining('source_faculty_id=faculty-1')
    );
    expect(mockedApi.get).toHaveBeenCalledWith(
      expect.stringContaining('target_faculty_id=faculty-2')
    );
    expect(mockedApi.get).toHaveBeenCalledWith(
      expect.stringContaining('start_date=2024-01-01')
    );
    expect(mockedApi.get).toHaveBeenCalledWith(
      expect.stringContaining('end_date=2024-01-31')
    );
  });

  it('should handle empty results', async () => {
    mockedApi.get.mockResolvedValueOnce({
      items: [],
      total: 0,
    });

    const { result } = renderHook(() => useSwapList(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(result.current.data?.items).toHaveLength(0);
  });
});

describe('useSwapCandidates', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should fetch swap candidates successfully', async () => {
    const mockCandidates = [
      {
        facultyId: 'faculty-2',
        facultyName: 'Dr. Jones',
        available_weeks: ['2024-01-22', '2024-01-29'],
        compatibility_score: 0.95,
        constraints_met: true,
      },
      {
        facultyId: 'faculty-3',
        facultyName: 'Dr. Brown',
        available_weeks: ['2024-01-22'],
        compatibility_score: 0.85,
        constraints_met: true,
      },
    ];

    mockedApi.get.mockResolvedValueOnce({
      items: mockCandidates,
      total: 2,
    });

    const { result } = renderHook(
      () => useSwapCandidates('faculty-1', '2024-01-15'),
      {
        wrapper: createWrapper(),
      }
    );

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(result.current.data?.items).toHaveLength(2);
    expect(result.current.data?.items[0].facultyName).toBe('Dr. Jones');
    // URL params must use snake_case
    expect(mockedApi.get).toHaveBeenCalledWith(
      expect.stringContaining('source_faculty_id=faculty-1')
    );
    expect(mockedApi.get).toHaveBeenCalledWith(
      expect.stringContaining('source_week=2024-01-15')
    );
  });

  it('should be disabled when params are missing', () => {
    const { result } = renderHook(() => useSwapCandidates('', ''), {
      wrapper: createWrapper(),
    });

    expect(result.current.isLoading).toBe(false);
    expect(result.current.isFetching).toBe(false);
  });
});

describe('useSwapCreate', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should create swap request and invalidate cache', async () => {
    const mockResponse = {
      success: true,
      requestId: 'swap-1',
      message: 'Swap request created',
      candidatesNotified: 3,
    };

    mockedApi.post.mockResolvedValueOnce(mockResponse);

    const queryClient = createTestQueryClient();
    const invalidateSpy = jest.spyOn(queryClient, 'invalidateQueries');

    const wrapper = ({ children }: { children: ReactNode }) => (
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    );

    const { result } = renderHook(() => useSwapCreate(), { wrapper });

    const createData = {
      sourceFacultyId: 'faculty-1',
      sourceWeek: '2024-01-15',
      targetFacultyId: 'faculty-2',
      targetWeek: '2024-01-22',
      swapType: SwapType.ONE_TO_ONE,
      reason: 'Family emergency',
    };

    await result.current.mutateAsync(createData);

    expect(mockedApi.post).toHaveBeenCalledWith('/swaps', createData);
    expect(invalidateSpy).toHaveBeenCalledWith({
      queryKey: ['swaps', 'list'],
    });
  });
});

describe('useSwapApprove', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should approve swap and invalidate related caches', async () => {
    const mockResponse = {
      success: true,
      message: 'Swap approved',
      swapId: 'swap-1',
    };

    mockedApi.post.mockResolvedValueOnce(mockResponse);

    const queryClient = createTestQueryClient();
    const invalidateSpy = jest.spyOn(queryClient, 'invalidateQueries');

    const wrapper = ({ children }: { children: ReactNode }) => (
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    );

    const { result } = renderHook(() => useSwapApprove(), { wrapper });

    await result.current.mutateAsync({
      swapId: 'swap-1',
      notes: 'Coverage confirmed',
    });

    expect(mockedApi.post).toHaveBeenCalledWith('/swaps/swap-1/approve', {
      notes: 'Coverage confirmed',
    });

    // Should invalidate detail, list, and schedule queries
    expect(invalidateSpy).toHaveBeenCalledWith({
      queryKey: ['swaps', 'detail', 'swap-1'],
    });
    expect(invalidateSpy).toHaveBeenCalledWith({
      queryKey: ['swaps', 'list'],
    });
    expect(invalidateSpy).toHaveBeenCalledWith({
      queryKey: ['schedule'],
    });
    expect(invalidateSpy).toHaveBeenCalledWith({
      queryKey: ['assignments'],
    });
  });
});

describe('useSwapReject', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should reject swap and invalidate caches', async () => {
    const mockResponse = {
      success: true,
      message: 'Swap rejected',
      swapId: 'swap-1',
    };

    mockedApi.post.mockResolvedValueOnce(mockResponse);

    const queryClient = createTestQueryClient();
    const invalidateSpy = jest.spyOn(queryClient, 'invalidateQueries');

    const wrapper = ({ children }: { children: ReactNode }) => (
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    );

    const { result } = renderHook(() => useSwapReject(), { wrapper });

    await result.current.mutateAsync({
      swapId: 'swap-1',
      reason: 'Coverage not available',
      notes: 'Cannot cover this shift',
    });

    expect(mockedApi.post).toHaveBeenCalledWith('/swaps/swap-1/reject', {
      notes: 'Cannot cover this shift',
      reason: 'Coverage not available',
    });

    expect(invalidateSpy).toHaveBeenCalledWith({
      queryKey: ['swaps', 'detail', 'swap-1'],
    });
    expect(invalidateSpy).toHaveBeenCalledWith({
      queryKey: ['swaps', 'list'],
    });
  });
});

describe('useAutoMatch', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should find compatible candidates with auto-match', async () => {
    const mockResponse = {
      success: true,
      candidates: [
        {
          facultyId: 'faculty-2',
          facultyName: 'Dr. Jones',
          available_weeks: ['2024-01-22'],
          compatibility_score: 0.95,
          constraints_met: true,
        },
      ],
      total_candidates: 1,
      message: 'Found 1 compatible candidate',
    };

    mockedApi.post.mockResolvedValueOnce(mockResponse);

    const queryClient = createTestQueryClient();
    const invalidateSpy = jest.spyOn(queryClient, 'invalidateQueries');

    const wrapper = ({ children }: { children: ReactNode }) => (
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    );

    const { result } = renderHook(() => useAutoMatch(), { wrapper });

    const matchRequest = {
      sourceFacultyId: 'faculty-1',
      sourceWeek: '2024-01-15',
      max_candidates: 10,
      prefer_oneToOne: true,
    };

    await result.current.mutateAsync(matchRequest);

    expect(mockedApi.post).toHaveBeenCalledWith(
      '/swaps/auto-match',
      matchRequest
    );

    // Should invalidate candidates query
    expect(invalidateSpy).toHaveBeenCalledWith({
      queryKey: ['swaps', 'candidates', 'faculty-1', '2024-01-15'],
    });
  });

  it('should handle no candidates found', async () => {
    const mockResponse = {
      success: true,
      candidates: [],
      total_candidates: 0,
      message: 'No compatible candidates found',
    };

    mockedApi.post.mockResolvedValueOnce(mockResponse);

    const wrapper = createWrapper();
    const { result } = renderHook(() => useAutoMatch(), { wrapper });

    const matchRequest = {
      sourceFacultyId: 'faculty-1',
      sourceWeek: '2024-01-15',
    };

    const response = await result.current.mutateAsync(matchRequest);

    expect(response.total_candidates).toBe(0);
    expect(response.candidates).toHaveLength(0);
  });
});
