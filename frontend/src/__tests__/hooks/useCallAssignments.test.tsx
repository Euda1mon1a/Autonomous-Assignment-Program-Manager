/**
 * useCallAssignments Hook Tests
 *
 * Tests for call assignment hooks including list, detail, CRUD mutations,
 * coverage reports, and equity reports.
 */
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactNode } from 'react';
import * as api from '@/lib/api';
import {
  useCallAssignments,
  useCallAssignment,
  useCreateCallAssignment,
  useUpdateCallAssignment,
  useDeleteCallAssignment,
  useCoverageReport,
  useEquityReport,
} from '@/hooks/useCallAssignments';

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

// Mock data
const mockCallAssignment = {
  id: 'call-1',
  personId: 'person-1',
  personName: 'Dr. Smith',
  date: '2024-01-15',
  callType: 'night',
  isWeekend: false,
  postCallStatus: 'scheduled',
  createdAt: '2024-01-01T00:00:00Z',
  updatedAt: '2024-01-01T00:00:00Z',
};

const mockCallAssignments = [
  mockCallAssignment,
  {
    id: 'call-2',
    personId: 'person-2',
    personName: 'Dr. Jones',
    date: '2024-01-16',
    callType: 'night',
    isWeekend: false,
    postCallStatus: 'available',
    createdAt: '2024-01-01T00:00:00Z',
    updatedAt: '2024-01-01T00:00:00Z',
  },
];

describe('useCallAssignments', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should fetch call assignments successfully', async () => {
    mockedApi.get.mockResolvedValueOnce({
      items: mockCallAssignments,
      total: 2,
    });

    const { result } = renderHook(() => useCallAssignments(), {
      wrapper: createWrapper(),
    });

    // Initially loading
    expect(result.current.isLoading).toBe(true);
    expect(result.current.data).toBeUndefined();

    // Wait for data to load
    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    // Check data
    expect(result.current.data?.items).toHaveLength(2);
    expect(result.current.data?.total).toBe(2);
    expect(mockedApi.get).toHaveBeenCalledWith('/call-assignments');
  });

  it('should apply filters to query string', async () => {
    mockedApi.get.mockResolvedValueOnce({
      items: [mockCallAssignment],
      total: 1,
    });

    const filters = {
      startDate: '2024-01-01',
      endDate: '2024-01-31',
      personId: 'person-1',
      callType: 'night',
    };

    const { result } = renderHook(() => useCallAssignments(filters), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    // URL query params must use snake_case
    expect(mockedApi.get).toHaveBeenCalledWith(
      expect.stringContaining('start_date=2024-01-01')
    );
    expect(mockedApi.get).toHaveBeenCalledWith(
      expect.stringContaining('end_date=2024-01-31')
    );
    expect(mockedApi.get).toHaveBeenCalledWith(
      expect.stringContaining('person_id=person-1')
    );
    expect(mockedApi.get).toHaveBeenCalledWith(
      expect.stringContaining('call_type=night')
    );
  });

  it('should handle empty results', async () => {
    mockedApi.get.mockResolvedValueOnce({
      items: [],
      total: 0,
    });

    const { result } = renderHook(() => useCallAssignments(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(result.current.data?.items).toHaveLength(0);
    expect(result.current.data?.total).toBe(0);
  });

  it('should handle API errors gracefully', async () => {
    const apiError = { message: 'Network error', status: 500 };
    mockedApi.get.mockRejectedValueOnce(apiError);

    const { result } = renderHook(() => useCallAssignments(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isError).toBe(true);
    });

    expect(result.current.error).toEqual(apiError);
  });
});

describe('useCallAssignment', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should fetch single call assignment', async () => {
    mockedApi.get.mockResolvedValueOnce(mockCallAssignment);

    const { result } = renderHook(() => useCallAssignment('call-1'), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(result.current.data).toEqual(mockCallAssignment);
    expect(mockedApi.get).toHaveBeenCalledWith('/call-assignments/call-1');
  });

  it('should be disabled when id is not provided', () => {
    const { result } = renderHook(() => useCallAssignment(''), {
      wrapper: createWrapper(),
    });

    expect(result.current.isLoading).toBe(false);
    expect(result.current.isFetching).toBe(false);
  });

  it('should handle not found error', async () => {
    const notFoundError = { message: 'Call assignment not found', status: 404 };
    mockedApi.get.mockRejectedValueOnce(notFoundError);

    const { result } = renderHook(() => useCallAssignment('call-999'), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isError).toBe(true);
    });

    expect(result.current.error).toEqual(notFoundError);
  });
});

describe('useCreateCallAssignment', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should create call assignment and invalidate cache', async () => {
    mockedApi.post.mockResolvedValueOnce(mockCallAssignment);

    const queryClient = createTestQueryClient();
    const invalidateSpy = jest.spyOn(queryClient, 'invalidateQueries');

    const wrapper = ({ children }: { children: ReactNode }) => (
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    );

    const { result } = renderHook(() => useCreateCallAssignment(), { wrapper });

    const createData = {
      personId: 'person-1',
      date: '2024-01-15',
      callType: 'night',
    };

    await result.current.mutateAsync(createData);

    expect(mockedApi.post).toHaveBeenCalledWith('/call-assignments', createData);
    expect(invalidateSpy).toHaveBeenCalledWith({
      queryKey: ['call-assignments'],
    });
  });
});

describe('useUpdateCallAssignment', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should update call assignment and invalidate caches', async () => {
    const updatedAssignment = { ...mockCallAssignment, callType: 'day' };
    mockedApi.put.mockResolvedValueOnce(updatedAssignment);

    const queryClient = createTestQueryClient();
    const invalidateSpy = jest.spyOn(queryClient, 'invalidateQueries');

    const wrapper = ({ children }: { children: ReactNode }) => (
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    );

    const { result } = renderHook(() => useUpdateCallAssignment(), { wrapper });

    const updateData = {
      callType: 'day',
    };

    await result.current.mutateAsync({ id: 'call-1', data: updateData });

    expect(mockedApi.put).toHaveBeenCalledWith(
      '/call-assignments/call-1',
      updateData
    );
    expect(invalidateSpy).toHaveBeenCalledWith({
      queryKey: ['call-assignments'],
    });
    expect(invalidateSpy).toHaveBeenCalledWith({
      queryKey: ['call-assignments', 'detail', 'call-1'],
    });
  });
});

describe('useDeleteCallAssignment', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should delete call assignment and invalidate cache', async () => {
    mockedApi.del.mockResolvedValueOnce(undefined);

    const queryClient = createTestQueryClient();
    const invalidateSpy = jest.spyOn(queryClient, 'invalidateQueries');

    const wrapper = ({ children }: { children: ReactNode }) => (
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    );

    const { result } = renderHook(() => useDeleteCallAssignment(), { wrapper });

    await result.current.mutateAsync('call-1');

    expect(mockedApi.del).toHaveBeenCalledWith('/call-assignments/call-1');
    expect(invalidateSpy).toHaveBeenCalledWith({
      queryKey: ['call-assignments'],
    });
  });
});

describe('useCoverageReport', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should fetch coverage report for date range', async () => {
    const mockCoverageReport = {
      startDate: '2024-01-01',
      endDate: '2024-01-31',
      totalDays: 31,
      coveredDays: 30,
      uncoveredDays: 1,
      coverageRate: 0.968,
      gaps: [
        {
          date: '2024-01-15',
          reason: 'No assignment',
        },
      ],
    };

    mockedApi.get.mockResolvedValueOnce(mockCoverageReport);

    const { result } = renderHook(
      () => useCoverageReport('2024-01-01', '2024-01-31'),
      {
        wrapper: createWrapper(),
      }
    );

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(result.current.data).toEqual(mockCoverageReport);
    expect(mockedApi.get).toHaveBeenCalledWith(
      expect.stringContaining('/call-assignments/reports/coverage')
    );
    expect(mockedApi.get).toHaveBeenCalledWith(
      expect.stringContaining('startDate=2024-01-01')
    );
    expect(mockedApi.get).toHaveBeenCalledWith(
      expect.stringContaining('endDate=2024-01-31')
    );
  });

  it('should be disabled when dates are not provided', () => {
    const { result } = renderHook(() => useCoverageReport('', ''), {
      wrapper: createWrapper(),
    });

    expect(result.current.isLoading).toBe(false);
    expect(result.current.isFetching).toBe(false);
  });
});

describe('useEquityReport', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should fetch equity report for date range', async () => {
    const mockEquityReport = {
      startDate: '2024-01-01',
      endDate: '2024-01-31',
      giniCoefficient: 0.12,
      isEquitable: true,
      personStats: [
        {
          personId: 'person-1',
          personName: 'Dr. Smith',
          callCount: 5,
          weekendCallCount: 1,
          totalHours: 120,
        },
        {
          personId: 'person-2',
          personName: 'Dr. Jones',
          callCount: 4,
          weekendCallCount: 2,
          totalHours: 110,
        },
      ],
    };

    mockedApi.get.mockResolvedValueOnce(mockEquityReport);

    const { result } = renderHook(
      () => useEquityReport('2024-01-01', '2024-01-31'),
      {
        wrapper: createWrapper(),
      }
    );

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(result.current.data).toEqual(mockEquityReport);
    expect(mockedApi.get).toHaveBeenCalledWith(
      expect.stringContaining('/call-assignments/reports/equity')
    );
    expect(mockedApi.get).toHaveBeenCalledWith(
      expect.stringContaining('startDate=2024-01-01')
    );
    expect(mockedApi.get).toHaveBeenCalledWith(
      expect.stringContaining('endDate=2024-01-31')
    );
  });

  it('should be disabled when dates are not provided', () => {
    const { result } = renderHook(() => useEquityReport('', ''), {
      wrapper: createWrapper(),
    });

    expect(result.current.isLoading).toBe(false);
    expect(result.current.isFetching).toBe(false);
  });

  it('should handle equity report with high Gini coefficient', async () => {
    const mockEquityReport = {
      startDate: '2024-01-01',
      endDate: '2024-01-31',
      giniCoefficient: 0.35,
      isEquitable: false,
      personStats: [
        {
          personId: 'person-1',
          personName: 'Dr. Smith',
          callCount: 10,
          weekendCallCount: 5,
          totalHours: 240,
        },
        {
          personId: 'person-2',
          personName: 'Dr. Jones',
          callCount: 2,
          weekendCallCount: 0,
          totalHours: 48,
        },
      ],
    };

    mockedApi.get.mockResolvedValueOnce(mockEquityReport);

    const { result } = renderHook(
      () => useEquityReport('2024-01-01', '2024-01-31'),
      {
        wrapper: createWrapper(),
      }
    );

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(result.current.data?.isEquitable).toBe(false);
    expect(result.current.data?.giniCoefficient).toBeGreaterThan(0.3);
  });
});
